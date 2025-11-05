"""
Permission classes for subscription management API endpoints.

These permissions enforce row-level access control, feature-based authorization,
and proper separation between admin and user capabilities.
"""
from rest_framework.permissions import BasePermission, SAFE_METHODS
from subscriptions.models import Subscription, BillingProfile, Feature
from subscriptions.utils import has_feature_access


class IsAdmin(BasePermission):
    """
    Permission class that allows only admin users (is_staff=True).
    Use this for admin-only endpoints.
    
    Usage:
        @permission_classes([IsAuthenticated, IsAdmin])
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_staff
        )


class IsSuperAdmin(BasePermission):
    """
    Permission class that allows only superadmin users (is_superuser=True).
    Use this for sensitive operations like user management.
    
    Usage:
        @permission_classes([IsAuthenticated, IsSuperAdmin])
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_superuser
        )


class IsSubscribed(BasePermission):
    """
    Permission class that verifies user has an active subscription.
    
    Checks if user has any active subscription, regardless of plan.
    Use this to gate premium features that require any paid plan.
    
    Usage:
        @permission_classes([IsAuthenticated, IsSubscribed])
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admins always have access
        if request.user.is_staff:
            return True
        
        try:
            # Check if user has billing profile with active subscription
            billing_profile = BillingProfile.objects.get(user=request.user)
            active_subscriptions = billing_profile.subscriptions.filter(
                status='active'
            )
            return active_subscriptions.exists()
        except BillingProfile.DoesNotExist:
            return False


class HasFeatureAccess(BasePermission):
    """
    Permission class that verifies user has access to a specific feature.
    
    The feature key must be provided in the view via the 'required_feature' attribute.
    
    Usage:
        class MyView(APIView):
            permission_classes = [IsAuthenticated, HasFeatureAccess]
            required_feature = 'view_premium_signals'
    
    Or use the decorator:
        @permission_classes([IsAuthenticated, HasFeatureAccess])
        @required_feature('view_premium_signals')
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admins always have access
        if request.user.is_staff:
            return True
        
        # Get required feature from view
        required_feature = getattr(view, 'required_feature', None)
        if not required_feature:
            # If no feature specified, deny access (fail-safe)
            return False
        
        # Check if user has access to the feature
        return has_feature_access(request.user, required_feature)


class CanManageSubscription(BasePermission):
    """
    Row-level permission for subscription management.
    
    - Users can only manage their own subscriptions
    - Admins can manage all subscriptions
    - Only allows safe methods (GET) by default
    - Dangerous methods (PUT, PATCH, DELETE) restricted to admins
    
    Usage:
        @permission_classes([IsAuthenticated, CanManageSubscription])
    """
    
    def has_permission(self, request, view):
        """Check if user has general permission to access subscriptions"""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Check if user can access specific subscription"""
        # Admins can do anything
        if request.user.is_staff:
            return True
        
        # Ensure obj is a Subscription
        if not isinstance(obj, Subscription):
            return False
        
        # Users can only access their own subscriptions
        try:
            if not obj.billing_profile or obj.billing_profile.user != request.user:
                return False
        except Exception:
            # Handle edge case where billing_profile doesn't exist or raises exception
            return False
        
        # Check action type for fine-grained permissions
        action = getattr(view, 'action', None)
        
        # Allow safe methods (GET, HEAD, OPTIONS)
        if request.method in SAFE_METHODS:
            return True
        
        # Allow specific custom actions for subscription owners
        # These are safe POST actions that modify the user's own subscription
        if action in ['cancel', 'reactivate']:
            return True
        
        # Block all other write operations (create, update, partial_update, destroy)
        # Only admins can perform these operations
        return False


class CanManageReferrals(BasePermission):
    """
    Permission class for referral management.
    
    - Users can view and create their own referral codes
    - Users can view their referral statistics
    - Admins can manage all referrals
    - Users cannot modify others' referral codes
    
    Usage:
        @permission_classes([IsAuthenticated, CanManageReferrals])
    """
    
    def has_permission(self, request, view):
        """Check if user has general permission to access referrals"""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Check if user can access specific referral code"""
        # Admins can do anything
        if request.user.is_staff:
            return True
        
        # Check if object has referrer attribute (ReferralCode model)
        if hasattr(obj, 'referrer'):
            # Users can only manage their own referral codes
            if obj.referrer != request.user:
                return False
            
            # Users can view and create, but not delete
            if request.method == 'DELETE':
                return False
            
            return True
        
        # Check if object has referral_code attribute (Referral model)
        if hasattr(obj, 'referral_code'):
            # Users can view referrals they made or received
            is_referrer = obj.referrer == request.user
            is_referee = obj.referee == request.user
            
            if not (is_referrer or is_referee):
                return False
            
            # Only safe methods allowed for regular users
            if request.method not in SAFE_METHODS:
                return False
            
            return True
        
        return False


class CanAccessAnalytics(BasePermission):
    """
    Permission class for analytics access.
    
    - Only admins can access platform-wide analytics
    - Users can access their own analytics (subscriptions, referrals)
    - Enforces data segregation
    
    Usage:
        @permission_classes([IsAuthenticated, CanAccessAnalytics])
    """
    
    def has_permission(self, request, view):
        """Check if user has general permission to access analytics"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admins have full analytics access
        if request.user.is_staff:
            return True
        
        # Regular users can access their own analytics
        # View should filter by user in get_queryset()
        return True
    
    def has_object_permission(self, request, view, obj):
        """Check if user can access specific analytics object"""
        # Admins can access all analytics
        if request.user.is_staff:
            return True
        
        # Users can only access their own analytics data
        # Check various possible relationships to user
        if hasattr(obj, 'user') and obj.user == request.user:
            return True
        
        if hasattr(obj, 'billing_profile'):
            return obj.billing_profile.user == request.user
        
        if hasattr(obj, 'subscription'):
            return (obj.subscription.billing_profile and 
                   obj.subscription.billing_profile.user == request.user)
        
        return False


class IsOwnerOrAdmin(BasePermission):
    """
    Generic permission that allows object owners or admin users.
    
    Works with any object that has a 'user' attribute or is itself a user.
    Useful for generic endpoints where users access their own data.
    
    Usage:
        @permission_classes([IsAuthenticated, IsOwnerOrAdmin])
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin users have full access
        if request.user.is_staff:
            return True
        
        # Check if object has 'user' attribute and matches request user
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # Check if object itself is a user
        if hasattr(obj, 'id') and hasattr(request.user, 'id'):
            return obj.id == request.user.id
        
        return False


class ReadOnly(BasePermission):
    """
    Permission class that only allows read operations (GET, HEAD, OPTIONS).
    
    Useful for endpoints that should be view-only.
    
    Usage:
        @permission_classes([IsAuthenticated, ReadOnly])
    """
    
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS


# Utility decorator for specifying required feature
def required_feature(feature_key):
    """
    Decorator to specify required feature for a view.
    
    Usage:
        @api_view(['GET'])
        @permission_classes([IsAuthenticated, HasFeatureAccess])
        @required_feature('view_premium_signals')
        def premium_signals(request):
            pass
    """
    def decorator(view_func):
        view_func.required_feature = feature_key
        return view_func
    return decorator
