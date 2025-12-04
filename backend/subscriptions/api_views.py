"""
Subscription API ViewSets (Phase 0.5 - Tasks 0.5.20-0.5.21)

RESTful API endpoints for subscription management with:
- Full CRUD operations (list, retrieve, create, update, delete)
- Row-level permissions (users see own, admins see all)
- Filtering by status, plan, date ranges
- Pagination (10 per page for subscriptions, 20 for plans)
- Custom actions (cancel, reactivate, activate, deactivate, clone)
- Signal integration for automation
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q, Count, Sum
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from decimal import Decimal, InvalidOperation

User = get_user_model()

from .models import Subscription, SubscriptionPlan, BillingProfile, Feature, Coupon, TelegramConfiguration, TelegramGroup, PaymentConfiguration, EmailConfiguration, Payment
from .serializers import SubscriptionSerializer, PricingPlanSerializer, FeatureSerializer, CouponSerializer, TelegramConfigurationSerializer, TelegramGroupSerializer, PaymentConfigurationSerializer, EmailConfigurationSerializer, PublicPricingPlanSerializer
from .permissions import CanManageSubscription, IsAdmin


class SubscriptionPagination(PageNumberPagination):
    """Custom pagination for subscriptions (10 per page)"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class SubscriptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for subscription management (Phase 0.5 - Task 0.5.20)
    
    Provides:
    - list: GET /subscriptions/ - List subscriptions (users see own, admins see all)
    - retrieve: GET /subscriptions/{id}/ - Get subscription details
    - create: POST /subscriptions/ - Create new subscription
    - update: PUT/PATCH /subscriptions/{id}/ - Update subscription (admin only)
    - destroy: DELETE /subscriptions/{id}/ - Delete subscription (admin only)
    - cancel: POST /subscriptions/{id}/cancel/ - Cancel subscription
    - reactivate: POST /subscriptions/{id}/reactivate/ - Reactivate cancelled subscription
    
    Permissions:
    - IsAuthenticated: All users must be logged in
    - CanManageSubscription: Row-level permissions (users read own, admins full CRUD)
    
    Filtering:
    - status: Filter by subscription status (active, cancelled, expired, etc.)
    - plan: Filter by subscription plan ID
    - start_date__gte: Filter by start date (greater than or equal)
    - end_date__lte: Filter by end date (less than or equal)
    
    Search:
    - Search by user email, plan name
    
    Pagination:
    - 10 subscriptions per page (configurable via page_size parameter)
    """
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated, CanManageSubscription]
    pagination_class = SubscriptionPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'plan', 'billing_profile']
    search_fields = ['billing_profile__user__email', 'plan__name']
    ordering_fields = ['created_at', 'start_date', 'end_date', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Return subscriptions based on user permissions:
        - Regular users: Only their own subscriptions
        - Admin/staff: All subscriptions
        """
        user = self.request.user
        
        if user.is_staff or user.is_superuser:
            # Admins see all subscriptions
            queryset = Subscription.objects.all()
        else:
            # Users see only their own subscriptions
            queryset = Subscription.objects.filter(
                billing_profile__user=user
            )
        
        # Select related to optimize queries
        queryset = queryset.select_related(
            'billing_profile',
            'billing_profile__user',
            'plan',
            'referral',
            'referral__referrer',
            'referral__referral_code',
            'payment_method'
        ).prefetch_related(
            'plan__features'
        )
        
        return queryset
    
    def perform_create(self, serializer):
        """
        Create subscription with proper user context.
        Users can only create subscriptions for their own billing profile.
        Admins can create for any billing profile.
        """
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel a subscription (POST /subscriptions/{id}/cancel/)
        
        Request body:
        {
            "reason": "Optional cancellation reason"
        }
        
        Response:
        {
            "success": true,
            "message": "Subscription cancelled successfully",
            "subscription": {...subscription data...}
        }
        
        Notes:
        - Sets auto_renew to False
        - Sets status to 'cancelled'
        - Records cancellation timestamp and reason
        - Access continues until end_date
        - Triggers subscription_cancelled signal
        """
        subscription = self.get_object()
        
        # Check if already cancelled
        if subscription.status == 'cancelled':
            return Response(
                {
                    'success': False,
                    'message': 'Subscription is already cancelled',
                    'subscription': self.get_serializer(subscription).data
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if already expired
        if subscription.status == 'expired':
            return Response(
                {
                    'success': False,
                    'message': 'Cannot cancel an expired subscription',
                    'subscription': self.get_serializer(subscription).data
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get cancellation reason from request
        reason = request.data.get('reason', '')
        
        # Cancel subscription using model method (triggers signal)
        subscription.cancel(reason=reason)
        
        return Response(
            {
                'success': True,
                'message': 'Subscription cancelled successfully. Access continues until end date.',
                'subscription': self.get_serializer(subscription).data
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def reactivate(self, request, pk=None):
        """
        Reactivate a cancelled subscription (POST /subscriptions/{id}/reactivate/)
        
        Response:
        {
            "success": true,
            "message": "Subscription reactivated successfully",
            "subscription": {...subscription data...}
        }
        
        Notes:
        - Only works for cancelled subscriptions
        - Re-enables auto_renew
        - Sets status back to 'active'
        - Clears cancellation timestamp and reason
        - Subscription must not be expired (end_date > now)
        """
        subscription = self.get_object()
        
        # Check if subscription is cancelled
        if subscription.status != 'cancelled':
            return Response(
                {
                    'success': False,
                    'message': 'Only cancelled subscriptions can be reactivated',
                    'subscription': self.get_serializer(subscription).data
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if subscription is expired
        if timezone.now() > subscription.end_date:
            return Response(
                {
                    'success': False,
                    'message': 'Cannot reactivate an expired subscription. Please create a new subscription.',
                    'subscription': self.get_serializer(subscription).data
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Reactivate subscription
        subscription.status = 'active'
        subscription.auto_renew = True
        subscription.cancelled_at = None
        subscription.cancellation_reason = ''
        subscription.save()
        
        return Response(
            {
                'success': True,
                'message': 'Subscription reactivated successfully',
                'subscription': self.get_serializer(subscription).data
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def expiring_soon(self, request):
        """
        Get subscriptions expiring within specified days (GET /subscriptions/expiring_soon/?days=7)
        
        Query params:
        - days: Number of days to look ahead (default: 7)
        
        Returns list of subscriptions expiring within the specified timeframe.
        Users see only their own, admins see all.
        """
        days = int(request.query_params.get('days', 7))
        
        from datetime import timedelta
        expiry_threshold = timezone.now() + timedelta(days=days)
        
        queryset = self.get_queryset().filter(
            status='active',
            end_date__lte=expiry_threshold,
            end_date__gte=timezone.now()
        )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsAdmin])
    def statistics(self, request):
        """
        Get subscription statistics (GET /subscriptions/statistics/) - Admin only
        
        Returns:
        {
            "total_subscriptions": 150,
            "active_subscriptions": 120,
            "cancelled_subscriptions": 20,
            "expired_subscriptions": 10,
            "pending_subscriptions": 5,
            "subscriptions_this_month": 15,
            "expiring_this_week": 8
        }
        """
        from datetime import timedelta
        from django.db.models import Count
        
        now = timezone.now()
        week_from_now = now + timedelta(days=7)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        queryset = Subscription.objects.all()
        
        stats = {
            'total_subscriptions': queryset.count(),
            'active_subscriptions': queryset.filter(status='active').count(),
            'cancelled_subscriptions': queryset.filter(status='cancelled').count(),
            'expired_subscriptions': queryset.filter(status='expired').count(),
            'pending_subscriptions': queryset.filter(status='pending').count(),
            'suspended_subscriptions': queryset.filter(status='suspended').count(),
            'subscriptions_this_month': queryset.filter(created_at__gte=month_start).count(),
            'expiring_this_week': queryset.filter(
                status='active',
                end_date__gte=now,
                end_date__lte=week_from_now
            ).count()
        }
        
        return Response(stats, status=status.HTTP_200_OK)


# ============================================================================
# Phase 0.5 - Task 0.5.21: SubscriptionPlan API Endpoints
# ============================================================================


class SubscriptionPlanPagination(PageNumberPagination):
    """Custom pagination for subscription plans (20 per page)"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class SubscriptionPlanViewSet(viewsets.ModelViewSet):
    """
    ViewSet for subscription plan management (Phase 0.5 - Task 0.5.21)
    
    Provides:
    - list: GET /plans/ - List all active plans (public access)
    - retrieve: GET /plans/{id}/ - Get plan details (public access)
    - create: POST /plans/ - Create new plan (admin only)
    - update: PUT/PATCH /plans/{id}/ - Update plan (admin only)
    - destroy: DELETE /plans/{id}/ - Delete plan (admin only)
    - activate: POST /plans/{id}/activate/ - Activate plan (admin only)
    - deactivate: POST /plans/{id}/deactivate/ - Deactivate plan (admin only)
    - clone: POST /plans/{id}/clone/ - Clone plan (admin only)
    
    Permissions:
    - AllowAny: List and retrieve (public endpoints)
    - IsAdmin: Create, update, delete, and custom actions
    
    Filtering: billing_period, is_active, is_featured
    Search: name, description
    Ordering: base_price, name, created_at, -base_price, -created_at
    """
    
    serializer_class = PricingPlanSerializer
    pagination_class = SubscriptionPlanPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['billing_period', 'is_active', 'is_featured']
    search_fields = ['name', 'description']
    ordering_fields = ['base_price', 'name', 'created_at']
    ordering = ['sort_order', 'base_price']  # Default ordering
    
    def get_permissions(self):
        """
        Set permissions based on action:
        - list, retrieve: AllowAny (public access)
        - All others: IsAdmin (write operations)
        """
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdmin()]
    
    def get_queryset(self):
        """
        Return subscription plans with optimized queries.
        Public users see only active plans.
        Admins see all plans.
        """
        queryset = SubscriptionPlan.objects.prefetch_related('features')
        
        # Public users only see active plans
        if not self.request.user.is_authenticated or not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        
        return queryset
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def activate(self, request, pk=None):
        """
        Activate a subscription plan (admin only)
        POST /api/plans/{id}/activate/
        """
        plan = self.get_object()
        
        if plan.is_active:
            return Response(
                {'error': 'Plan is already active'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        plan.is_active = True
        plan.save(update_fields=['is_active', 'updated_at'])
        
        serializer = self.get_serializer(plan)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def deactivate(self, request, pk=None):
        """
        Deactivate a subscription plan (admin only)
        POST /api/plans/{id}/deactivate/
        """
        plan = self.get_object()
        
        if not plan.is_active:
            return Response(
                {'error': 'Plan is already inactive'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        plan.is_active = False
        plan.save(update_fields=['is_active', 'updated_at'])
        
        serializer = self.get_serializer(plan)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def clone(self, request, pk=None):
        """
        Clone a subscription plan with a new name (admin only)
        POST /api/plans/{id}/clone/
        Body: {
            "name": "New Plan Name",
            "slug": "new-plan-slug" (optional, will auto-generate if not provided)
        }
        """
        source_plan = self.get_object()
        new_name = request.data.get('name')
        new_slug = request.data.get('slug', None)
        
        if not new_name:
            return Response(
                {'error': 'Name is required for cloned plan'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create new plan as a copy
        cloned_plan = SubscriptionPlan.objects.create(
            name=new_name,
            slug=new_slug if new_slug else None,  # Will auto-generate from name
            description=f"{source_plan.description} (Cloned)",
            base_price=source_plan.base_price,
            billing_period=source_plan.billing_period,
            limits=source_plan.limits.copy() if source_plan.limits else {},
            paystack_plan_code='',  # Clear Paystack integration (must be set manually)
            is_active=False,  # Cloned plans start inactive
            is_featured=False,  # Not featured by default
            sort_order=source_plan.sort_order + 1
        )
        
        # Copy features M2M relationship
        cloned_plan.features.set(source_plan.features.all())
        
        serializer = self.get_serializer(cloned_plan)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# Phase 0.5 - Task 0.5.22: Feature API Endpoints
# ==================================================

class FeaturePagination(PageNumberPagination):
    """Pagination for Feature list endpoint"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class FeatureViewSet(viewsets.ModelViewSet):
    """
    ViewSet for feature management (Phase 0.5 - Task 0.5.22)
    
    Public endpoints (AllowAny):
    - list: GET /api/features/ - List all active features (non-admins see only active)
    - retrieve: GET /api/features/{id}/ - Get feature details
    
    Admin-only endpoints (IsAdmin):
    - create: POST /api/features/ - Create new feature
    - update: PUT/PATCH /api/features/{id}/ - Update feature (key is immutable)
    - destroy: DELETE /api/features/{id}/ - Delete feature
    - bulk_activate: POST /api/features/bulk_activate/ - Activate multiple features
    - bulk_deactivate: POST /api/features/bulk_deactivate/ - Deactivate multiple features
    
    Filtering:
    - ?category=signals - Filter by category
    - ?is_active=true - Filter by active status
    
    Search:
    - ?search=premium - Search in name, description, key
    
    Ordering:
    - ?ordering=sort_order - Order by sort_order (default)
    - ?ordering=name - Order by name
    - ?ordering=category - Order by category
    - ?ordering=-created_at - Order by creation date (newest first)
    
    Pagination:
    - Default: 20 per page
    - Custom: ?page_size=50 (max 100)
    """
    queryset = Feature.objects.all()
    serializer_class = FeatureSerializer
    pagination_class = FeaturePagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['name', 'description', 'key']
    ordering_fields = ['sort_order', 'name', 'category', 'created_at']
    ordering = ['sort_order', 'name']  # Default ordering
    
    def get_permissions(self):
        """
        Public access for list/retrieve.
        Admin-only for create/update/delete/custom actions.
        """
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdmin()]
    
    def get_queryset(self):
        """
        Filter features based on user permissions.
        Public/non-staff users: only active features
        Admins: all features (active + inactive)
        """
        queryset = super().get_queryset()
        
        # Non-admin users only see active features
        if not (self.request.user and self.request.user.is_authenticated and self.request.user.is_staff):
            queryset = queryset.filter(is_active=True)
        
        return queryset
    
    @action(detail=False, methods=['post'], permission_classes=[IsAdmin])
    def bulk_activate(self, request):
        """
        Bulk activate features by IDs
        
        POST /api/features/bulk_activate/
        Body: {"ids": ["uuid1", "uuid2", ...]}
        """
        ids = request.data.get('ids', [])
        
        if not ids:
            return Response(
                {'error': 'No feature IDs provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not isinstance(ids, list):
            return Response(
                {'error': 'IDs must be a list'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update features
        updated_count = Feature.objects.filter(id__in=ids).update(is_active=True)
        
        return Response({
            'message': f'Successfully activated {updated_count} feature(s)',
            'count': updated_count
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAdmin])
    def bulk_deactivate(self, request):
        """
        Bulk deactivate features by IDs
        
        POST /api/features/bulk_deactivate/
        Body: {"ids": ["uuid1", "uuid2", ...]}
        """
        ids = request.data.get('ids', [])
        
        if not ids:
            return Response(
                {'error': 'No feature IDs provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not isinstance(ids, list):
            return Response(
                {'error': 'IDs must be a list'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update features
        updated_count = Feature.objects.filter(id__in=ids).update(is_active=False)
        
        return Response({
            'message': f'Successfully deactivated {updated_count} feature(s)',
            'count': updated_count
        }, status=status.HTTP_200_OK)


class CouponPagination(PageNumberPagination):
    """Custom pagination for coupons (20 per page)"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class CouponViewSet(viewsets.ModelViewSet):
    """
    Coupon management API (Phase 0.5 - Task 0.5.23)
    
    Endpoints:
    - GET /api/coupons/ - List all coupons (admin-only)
    - GET /api/coupons/{id}/ - Retrieve coupon details (admin-only)
    - POST /api/coupons/ - Create coupon (admin-only)
    - PUT/PATCH /api/coupons/{id}/ - Update coupon (admin-only)
    - DELETE /api/coupons/{id}/ - Delete coupon (admin-only)
    - POST /api/coupons/validate/ - Validate coupon code (admin-only)
    - GET /api/coupons/{id}/usage_stats/ - Get usage statistics (admin-only)
    - POST /api/coupons/bulk_activate/ - Bulk activate coupons (admin-only)
    - POST /api/coupons/bulk_deactivate/ - Bulk deactivate coupons (admin-only)
    
    Permissions:
    - Admin-only access (IsAdmin permission)
    
    Features:
    - Filtering: discount_type, is_active, valid_from, valid_until
    - Search: code, description
    - Ordering: created_at, current_uses, discount_value
    - Pagination: 20 per page (configurable to 100)
    - Code immutability (cannot change after creation)
    """
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    permission_classes = [IsAdmin]
    pagination_class = CouponPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['discount_type', 'is_active']
    search_fields = ['code', 'description']
    ordering_fields = ['created_at', 'current_uses', 'discount_value', 'valid_from', 'valid_until']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        """Set created_by to current user"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['post'])
    def validate(self, request):
        """
        Validate a coupon code without applying it.
        
        POST /api/coupons/validate/
        Body: {
            "code": "SAVE20",
            "plan_id": "uuid",  # optional
            "amount": 100.00    # optional, for fixed discounts
        }
        
        Returns: {
            "valid": true/false,
            "message": "...",
            "coupon": {...},         # if valid
            "discount_details": {...} # if valid and amount provided
        }
        """
        code = request.data.get('code', '').upper().strip()
        plan_id = request.data.get('plan_id')
        amount = request.data.get('amount')
        
        if not code:
            return Response({
                'valid': False,
                'message': 'Coupon code is required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            coupon = Coupon.objects.get(code=code)
        except Coupon.DoesNotExist:
            return Response({
                'valid': False,
                'message': f'Coupon "{code}" does not exist.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if coupon can be used
        if not coupon.can_be_used():
            reasons = []
            if not coupon.is_active:
                reasons.append("inactive")
            if not coupon.is_valid():
                reasons.append("expired or not yet valid")
            if not coupon.is_usage_available():
                reasons.append("usage limit reached")
            
            return Response({
                'valid': False,
                'message': f'Coupon "{code}" cannot be used: {", ".join(reasons)}.',
                'coupon': CouponSerializer(coupon).data
            }, status=status.HTTP_200_OK)
        
        # Check plan applicability if plan_id provided
        if plan_id:
            try:
                from django.core.exceptions import ValidationError as DjangoValidationError
                from uuid import UUID
                try:
                    plan_uuid = UUID(plan_id)
                    plan = SubscriptionPlan.objects.get(id=plan_uuid)
                except (ValueError, DjangoValidationError):
                    return Response({
                        'valid': False,
                        'message': 'Invalid plan ID format.'
                    }, status=status.HTTP_400_BAD_REQUEST)
                except SubscriptionPlan.DoesNotExist:
                    return Response({
                        'valid': False,
                        'message': f'Plan with ID {plan_id} does not exist.'
                    }, status=status.HTTP_404_NOT_FOUND)
                
                if not coupon.applies_to_plan(plan):
                    return Response({
                        'valid': False,
                        'message': f'Coupon "{code}" does not apply to the selected plan.',
                        'coupon': CouponSerializer(coupon).data
                    }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({
                    'valid': False,
                    'message': f'Error validating plan: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        response_data = {
            'valid': True,
            'message': f'Coupon "{code}" is valid.',
            'coupon': CouponSerializer(coupon).data
        }
        
        # Calculate discount if amount provided
        if amount is not None:
            try:
                from decimal import Decimal
                amount_decimal = Decimal(str(amount))
                discount_details = coupon.calculate_discount(amount_decimal)
                response_data['discount_details'] = {
                    'original_price': float(discount_details['original_price']),
                    'discount_amount': float(discount_details['discount_amount']),
                    'final_price': float(discount_details['final_price']),
                    'savings_percentage': float(discount_details['savings_percentage'])
                }
            except Exception as e:
                response_data['discount_details_error'] = str(e)
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'])
    def usage_stats(self, request, pk=None):
        """
        Get detailed usage statistics for a coupon.
        
        GET /api/coupons/{id}/usage_stats/
        
        Returns: {
            "coupon": {...},
            "stats": {
                "total_uses": 10,
                "remaining_uses": 40,
                "usage_percentage": 20.0,
                "is_exhausted": false,
                "is_expired": false,
                "is_valid": true,
                "plans_count": 3
            }
        }
        """
        coupon = self.get_object()
        
        stats = {
            'total_uses': coupon.current_uses,
            'remaining_uses': coupon.get_remaining_uses(),
            'usage_percentage': float(
                (coupon.current_uses / coupon.max_uses * 100) if coupon.max_uses else 0
            ),
            'is_exhausted': not coupon.is_usage_available(),
            'is_expired': not coupon.is_valid(),
            'is_valid': coupon.is_valid(),
            'can_be_used': coupon.can_be_used(),
            'plans_count': coupon.plans.count()
        }
        
        return Response({
            'coupon': CouponSerializer(coupon).data,
            'stats': stats
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'], url_path='usage', url_name='usage-alias')
    def usage(self, request, pk=None):
        """
        Alias for usage_stats to match Task 0.5.24 endpoint specification.
        
        GET /api/coupons/{id}/usage/
        
        This is an alias that returns the same data as usage_stats.
        """
        return self.usage_stats(request, pk)
    
    @action(detail=False, methods=['post'])
    def bulk_activate(self, request):
        """
        Bulk activate coupons by IDs.
        
        POST /api/coupons/bulk_activate/
        Body: {"ids": ["uuid1", "uuid2", ...]}
        
        Returns: {"message": "...", "count": N}
        """
        ids = request.data.get('ids', [])
        
        if not ids:
            return Response({
                'error': 'No coupon IDs provided.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(ids, list):
            return Response({
                'error': 'IDs must be a list.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update coupons
        updated_count = Coupon.objects.filter(id__in=ids).update(is_active=True)
        
        return Response({
            'message': f'Successfully activated {updated_count} coupon(s)',
            'count': updated_count
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def bulk_deactivate(self, request):
        """
        Bulk deactivate coupons by IDs.
        
        POST /api/coupons/bulk_deactivate/
        Body: {"ids": ["uuid1", "uuid2", ...]}
        
        Returns: {"message": "...", "count": N}
        """
        ids = request.data.get('ids', [])
        
        if not ids:
            return Response({
                'error': 'No coupon IDs provided.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(ids, list):
            return Response({
                'error': 'IDs must be a list.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update coupons
        updated_count = Coupon.objects.filter(id__in=ids).update(is_active=False)
        
        return Response({
            'message': f'Successfully deactivated {updated_count} coupon(s)',
            'count': updated_count
        }, status=status.HTTP_200_OK)


# ============================================================================
# TELEGRAM CONFIGURATION API (Task 0.5.27)
# ============================================================================

class TelegramConfigurationViewSet(viewsets.ViewSet):
    """
    ViewSet for Telegram bot configuration (Phase 0.5 - Task 0.5.27)
    
    Singleton model - only one configuration exists.
    
    Endpoints:
    - GET /api/admin/telegram/config/ - Get current configuration
    - POST /api/admin/telegram/config/ - Update configuration (creates if doesn't exist)
    - PUT/PATCH /api/admin/telegram/config/<id>/ - Update specific fields
    - POST /api/admin/telegram/config/test_connection/ - Test bot connection
    
    Permissions:
    - IsAuthenticated + IsAdmin: Admin-only access
    
    Features:
    - Singleton pattern (always returns one instance)
    - Encrypted bot_token storage
    - Masked token display (never expose raw token)
    - Connection health testing
    - Settings bulk update
    """
    
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = TelegramConfigurationSerializer
    
    def list(self, request):
        """
        GET /api/admin/telegram/config/
        
        Returns the singleton TelegramConfiguration instance.
        Always returns a list with one item for DRF consistency.
        """
        instance = TelegramConfiguration.get_instance()
        serializer = TelegramConfigurationSerializer(instance)
        return Response([serializer.data], status=status.HTTP_200_OK)
    
    def retrieve(self, request, pk=None):
        """
        GET /api/admin/telegram/config/<id>/
        
        Get configuration details. ID is ignored (singleton).
        """
        instance = TelegramConfiguration.get_instance()
        serializer = TelegramConfigurationSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def create(self, request):
        """
        POST /api/admin/telegram/config/
        
        Create or update configuration (singleton pattern).
        """
        instance = TelegramConfiguration.get_instance()
        serializer = TelegramConfigurationSerializer(
            instance,
            data=request.data,
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, pk=None):
        """
        PUT /api/admin/telegram/config/<id>/
        
        Full update of configuration. ID is ignored (singleton).
        """
        instance = TelegramConfiguration.get_instance()
        serializer = TelegramConfigurationSerializer(
            instance,
            data=request.data,
            partial=False
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def partial_update(self, request, pk=None):
        """
        PATCH /api/admin/telegram/config/<id>/
        
        Partial update of configuration. ID is ignored (singleton).
        """
        instance = TelegramConfiguration.get_instance()
        serializer = TelegramConfigurationSerializer(
            instance,
            data=request.data,
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='test-connection')
    def test_connection(self, request):
        """
        POST /api/admin/telegram/config/test-connection/
        
        Test Telegram bot connection by calling the Telegram API.
        
        Returns:
        - 200: Connection successful (updates is_connected=True)
        - 400: Connection failed (updates is_connected=False with error)
        
        Response format:
        {
            "success": true/false,
            "message": "Connection successful" or error message,
            "bot_info": {
                "id": 123456789,
                "username": "OxidaneBot",
                "first_name": "Oxidane",
                "can_join_groups": true,
                "can_read_all_group_messages": false
            }
        }
        """
        instance = TelegramConfiguration.get_instance()
        
        # Check if bot token is set
        if not instance.bot_token:
            return Response({
                'success': False,
                'message': 'Bot token is not configured. Please set a bot token first.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Test connection to Telegram API
        try:
            import requests
            
            # Decrypt bot token before using
            try:
                raw_token = instance.bot_token
                decrypted_token = instance.decrypt_field('bot_token')
                
                # Debug logging
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Raw token (first 20 chars): {raw_token[:20] if raw_token else 'None'}")
                logger.info(f"Raw token starts with gAAAAA: {raw_token.startswith('gAAAAA') if raw_token else False}")
                logger.info(f"Decrypted token (first 20 chars): {decrypted_token[:20] if decrypted_token else 'None'}")
                logger.info(f"Decrypted token contains colon: {':' in decrypted_token if decrypted_token else False}")
                
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Decryption error: {str(e)}")
                return Response({
                    'success': False,
                    'message': f'Failed to decrypt bot token: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Validate decrypted token format
            if not decrypted_token or ':' not in decrypted_token:
                return Response({
                    'success': False,
                    'message': f'Bot token has invalid format. Expected: numbers:characters (got: {decrypted_token[:30] if decrypted_token else "empty"}...)'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            parts = decrypted_token.split(':')
            if len(parts) != 2 or not parts[0].isdigit() or len(parts[1]) < 30:
                return Response({
                    'success': False,
                    'message': 'Bot token has invalid format. Expected: numbers:characters'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Call Telegram getMe API
            api_url = f'https://api.telegram.org/bot{decrypted_token}/getMe'
            response = requests.get(api_url, timeout=10)
            data = response.json()
            
            if response.status_code == 200 and data.get('ok'):
                # Connection successful
                bot_info = data.get('result', {})
                bot_username = f"@{bot_info.get('username', '')}"
                
                # Update configuration
                instance.mark_as_connected(bot_username=bot_username)
                
                return Response({
                    'success': True,
                    'message': 'Connection successful! Bot is configured and ready to use.',
                    'bot_info': {
                        'id': bot_info.get('id'),
                        'username': bot_info.get('username'),
                        'first_name': bot_info.get('first_name'),
                        'can_join_groups': bot_info.get('can_join_groups', False),
                        'can_read_all_group_messages': bot_info.get('can_read_all_group_messages', False),
                    }
                }, status=status.HTTP_200_OK)
            else:
                # Connection failed
                error_message = data.get('description', 'Unknown error')
                instance.mark_as_disconnected(error_message=error_message)
                
                return Response({
                    'success': False,
                    'message': f'Connection failed: {error_message}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        except requests.exceptions.Timeout:
            error_message = 'Connection timeout. Please check your internet connection.'
            instance.mark_as_disconnected(error_message=error_message)
            
            return Response({
                'success': False,
                'message': error_message
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except requests.exceptions.RequestException as e:
            error_message = f'Network error: {str(e)}'
            instance.mark_as_disconnected(error_message=error_message)
            
            return Response({
                'success': False,
                'message': error_message
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            error_message = f'Unexpected error: {str(e)}'
            instance.mark_as_disconnected(error_message=error_message)
            
            return Response({
                'success': False,
                'message': error_message
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], url_path='discover-chats')
    def discover_chats(self, request):
        """
        Discover available groups/channels the bot has access to.
        
        Fetches recent bot updates to find all groups, supergroups, and channels
        the bot is a member of. This helps users find the correct chat ID when
        adding a new group.
        
        Returns:
            200: Success with list of discovered chats
            400: Bot token not configured or API error
            408: Connection timeout
            500: Unexpected error
        """
        config = TelegramConfiguration.get_instance()
        
        # Validation
        if not config.bot_token:
            return Response({
                'success': False,
                'message': 'Bot token not configured. Please configure the Telegram bot first.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            import requests
            
            # Get decrypted bot token
            bot_token = config.decrypt_field('bot_token')
            
            # Get recent updates from bot
            url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    updates = data.get('result', [])
                    
                    # Extract unique chats
                    chats_dict = {}
                    for update in updates:
                        # Check different message types
                        for msg_type in ['message', 'edited_message', 'channel_post', 'my_chat_member']:
                            if msg_type in update:
                                msg = update[msg_type]
                                if 'chat' in msg:
                                    chat = msg['chat']
                                    chat_id = chat.get('id')
                                    
                                    # Only include groups, supergroups, and channels (negative IDs)
                                    if chat_id and chat_id < 0:
                                        chat_key = str(chat_id)
                                        if chat_key not in chats_dict:
                                            chats_dict[chat_key] = {
                                                'chat_id': str(chat_id),
                                                'title': chat.get('title', 'Unknown'),
                                                'type': chat.get('type', 'unknown'),
                                                'username': chat.get('username', ''),
                                                'member_count': None  # Will be filled if possible
                                            }
                    
                    # Try to get member counts for each chat
                    for chat_key, chat_info in chats_dict.items():
                        try:
                            count_url = f"https://api.telegram.org/bot{bot_token}/getChatMemberCount"
                            count_response = requests.post(
                                count_url,
                                json={'chat_id': chat_info['chat_id']},
                                timeout=5
                            )
                            if count_response.status_code == 200:
                                count_data = count_response.json()
                                if count_data.get('ok'):
                                    chat_info['member_count'] = count_data['result']
                        except:
                            pass  # Skip if we can't get member count
                    
                    chats_list = sorted(
                        chats_dict.values(), 
                        key=lambda x: (x['type'], x['title'])
                    )
                    
                    return Response({
                        'success': True,
                        'message': f'Found {len(chats_list)} groups/channels',
                        'chats': chats_list,
                        'hint': 'Send a message in your group to make it appear here if it\'s missing.'
                    }, status=status.HTTP_200_OK)
                else:
                    error_msg = data.get('description', 'Unknown error')
                    return Response({
                        'success': False,
                        'message': f'Telegram API error: {error_msg}'
                    }, status=status.HTTP_400_BAD_REQUEST)
            elif response.status_code == 409:
                # Webhook is active - can't use getUpdates
                # Return existing groups from database instead
                from subscriptions.models import TelegramGroup
                existing_groups = TelegramGroup.objects.all().values(
                    'id', 'chat_id', 'name', 'member_count'
                )
                
                chats_list = [
                    {
                        'chat_id': str(group['chat_id']),
                        'title': group['name'],
                        'type': 'group',  # Default type since we don't store it
                        'username': '',
                        'member_count': group['member_count']
                    }
                    for group in existing_groups if group['chat_id']
                ]
                
                if len(chats_list) == 0:
                    # No groups found - provide helpful instructions
                    return Response({
                        'success': False,
                        'message': 'Webhook is active - automatic discovery unavailable',
                        'chats': [],
                        'webhook_active': True,
                        'instructions': {
                            'title': 'Add Groups Manually',
                            'steps': [
                                '1. Add your bot to the Telegram group',
                                '2. Send any message in the group',
                                '3. Visit: https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates',
                                '4. Find the "chat" object and copy the "id" (negative number)',
                                '5. Go to Telegram Groups page and click "Add Group"',
                                '6. Enter the Chat ID and group details'
                            ],
                            'note': 'The webhook is configured for real-time updates. To use auto-discovery, you would need to temporarily disable the webhook.'
                        }
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'success': True,
                        'message': f'Webhook is active. Showing {len(chats_list)} configured groups',
                        'chats': chats_list,
                        'hint': 'Add more groups manually using the chat ID. Auto-discovery requires webhook to be disabled.',
                        'webhook_active': True
                    }, status=status.HTTP_200_OK)
            elif response.status_code == 401:
                return Response({
                    'success': False,
                    'message': 'Unauthorized: Invalid bot token'
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    'success': False,
                    'message': f'Failed to get updates: HTTP {response.status_code}'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except requests.exceptions.Timeout:
            return Response({
                'success': False,
                'message': 'Connection timeout. Please try again.'
            }, status=status.HTTP_408_REQUEST_TIMEOUT)
        except requests.exceptions.RequestException as e:
            return Response({
                'success': False,
                'message': f'Network error: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Unexpected error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TelegramGroupViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Telegram Group management (Phase 0.5 - Task 0.5.28)
    
    Provides:
    - list: GET /admin/telegram/groups/ - List all groups
    - retrieve: GET /admin/telegram/groups/{id}/ - Get group details
    - create: POST /admin/telegram/groups/ - Create new group
    - update: PUT/PATCH /admin/telegram/groups/{id}/ - Update group
    - destroy: DELETE /admin/telegram/groups/{id}/ - Delete group
    - sync_members: POST /admin/telegram/groups/{id}/sync-members/ - Sync member count from Telegram
    - test_access: POST /admin/telegram/groups/{id}/test-access/ - Test bot access and permissions
    
    Permissions:
    - IsAuthenticated + IsAdmin: Admin-only access
    
    Features:
    - M2M relationship with SubscriptionPlan
    - Member count tracking via Telegram API
    - Bot permission verification
    - Capacity management
    - Computed health status
    """
    queryset = TelegramGroup.objects.all()
    serializer_class = TelegramGroupSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'is_private', 'auto_add_enabled', 'auto_remove_enabled']
    search_fields = ['name', 'description', 'group_key']
    ordering_fields = ['sort_order', 'name', 'member_count', 'created_at']
    ordering = ['sort_order', 'name']
    pagination_class = PageNumberPagination
    
    @action(detail=True, methods=['post'], url_path='sync-members')
    def sync_members(self, request, pk=None):
        """
        Sync member count from Telegram API.
        
        Calls Telegram Bot API getChatMemberCount endpoint to get current member count,
        then updates the group's member_count and last_sync_at fields.
        
        Returns:
            200: Success with old/new counts
            400: Bot token not configured, invalid chat_id, or Telegram API error
            408: Connection timeout
            500: Unexpected error
        """
        group = self.get_object()
        config = TelegramConfiguration.get_instance()
        
        # Validation
        if not config.bot_token:
            return Response({
                'success': False,
                'message': 'Bot token not configured. Please configure the Telegram bot first.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not group.chat_id:
            return Response({
                'success': False,
                'message': 'Group chat ID not set'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            import requests
            
            # Get decrypted bot token
            bot_token = config.decrypt_field('bot_token')
            
            # Call Telegram API
            url = f"https://api.telegram.org/bot{bot_token}/getChatMemberCount"
            response = requests.post(
                url,
                json={'chat_id': group.chat_id},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    new_count = data['result']
                    old_count = group.member_count
                    
                    # Update group
                    group.update_member_count(new_count)
                    
                    return Response({
                        'success': True,
                        'message': 'Member count synced successfully',
                        'old_count': old_count,
                        'new_count': new_count,
                        'difference': new_count - old_count,
                        'last_sync_at': group.last_sync_at.isoformat()
                    }, status=status.HTTP_200_OK)
                else:
                    error_msg = data.get('description', 'Unknown error')
                    return Response({
                        'success': False,
                        'message': f'Telegram API error: {error_msg}'
                    }, status=status.HTTP_400_BAD_REQUEST)
            elif response.status_code == 401:
                return Response({
                    'success': False,
                    'message': 'Unauthorized: Invalid bot token'
                }, status=status.HTTP_400_BAD_REQUEST)
            elif response.status_code == 403:
                return Response({
                    'success': False,
                    'message': 'Forbidden: Bot may have been removed from group or lacks permissions'
                }, status=status.HTTP_403_FORBIDDEN)
            else:
                return Response({
                    'success': False,
                    'message': f'Failed to connect to Telegram: HTTP {response.status_code}'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except requests.exceptions.Timeout:
            return Response({
                'success': False,
                'message': 'Connection timeout. Please check your internet connection and try again.'
            }, status=status.HTTP_408_REQUEST_TIMEOUT)
        except requests.exceptions.RequestException as e:
            return Response({
                'success': False,
                'message': f'Network error: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Unexpected error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'], url_path='test-access')
    def test_access(self, request, pk=None):
        """
        Test bot access and permissions in the group.
        
        Calls Telegram Bot API getChat endpoint to verify bot can access the group
        and retrieve its permissions.
        
        Returns:
            200: Success with group info and bot permissions
            400: Bot token not configured, invalid chat_id, or Telegram API error
            403: Bot doesn't have access to group
            408: Connection timeout
            500: Unexpected error
        """
        group = self.get_object()
        config = TelegramConfiguration.get_instance()
        
        # Validation
        if not config.bot_token:
            return Response({
                'success': False,
                'message': 'Bot token not configured. Please configure the Telegram bot first.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not group.chat_id:
            return Response({
                'success': False,
                'message': 'Group chat ID not set'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            import requests
            
            # Get decrypted bot token
            bot_token = config.decrypt_field('bot_token')
            
            # Call Telegram API to get chat info
            url = f"https://api.telegram.org/bot{bot_token}/getChat"
            response = requests.post(
                url,
                json={'chat_id': group.chat_id},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    chat_info = data['result']
                    
                    # Get bot's member info to check permissions
                    bot_url = f"https://api.telegram.org/bot{bot_token}/getChatMember"
                    bot_response = requests.post(
                        bot_url,
                        json={
                            'chat_id': group.chat_id,
                            'user_id': config.bot_token.split(':')[0]  # Bot ID is before the colon
                        },
                        timeout=10
                    )
                    
                    permissions = {}
                    is_admin = False
                    
                    if bot_response.status_code == 200:
                        bot_data = bot_response.json()
                        if bot_data.get('ok'):
                            member = bot_data['result']
                            is_admin = member.get('status') in ['creator', 'administrator']
                            
                            if is_admin:
                                # Extract permissions
                                permissions = {
                                    'can_send_messages': member.get('can_send_messages', True),
                                    'can_invite_users': member.get('can_invite_users', False),
                                    'can_restrict_members': member.get('can_restrict_members', False),
                                    'can_pin_messages': member.get('can_pin_messages', False),
                                    'can_delete_messages': member.get('can_delete_messages', False),
                                    'can_manage_chat': member.get('can_manage_chat', False)
                                }
                    
                    return Response({
                        'success': True,
                        'message': 'Bot has access to the group',
                        'group_info': {
                            'title': chat_info.get('title'),
                            'type': chat_info.get('type'),
                            'username': chat_info.get('username'),
                            'description': chat_info.get('description')
                        },
                        'bot_status': {
                            'is_admin': is_admin,
                            'permissions': permissions
                        }
                    }, status=status.HTTP_200_OK)
                else:
                    error_msg = data.get('description', 'Unknown error')
                    return Response({
                        'success': False,
                        'message': f'Telegram API error: {error_msg}'
                    }, status=status.HTTP_400_BAD_REQUEST)
            elif response.status_code == 401:
                return Response({
                    'success': False,
                    'message': 'Unauthorized: Invalid bot token'
                }, status=status.HTTP_400_BAD_REQUEST)
            elif response.status_code == 403:
                return Response({
                    'success': False,
                    'message': 'Forbidden: Bot doesn\'t have access to this group'
                }, status=status.HTTP_403_FORBIDDEN)
            else:
                return Response({
                    'success': False,
                    'message': f'Failed to connect to Telegram: HTTP {response.status_code}'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except requests.exceptions.Timeout:
            return Response({
                'success': False,
                'message': 'Connection timeout. Please check your internet connection and try again.'
            }, status=status.HTTP_408_REQUEST_TIMEOUT)
        except requests.exceptions.RequestException as e:
            return Response({
                'success': False,
                'message': f'Network error: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Unexpected error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# PAYMENT CONFIGURATION API (Task 0.5.29)
# ============================================================================

class PaymentConfigurationViewSet(viewsets.ModelViewSet):
    """
    Admin-only API for managing Payment Configuration (singleton).
    
    Supports Paystack and Stripe payment providers with encrypted API keys.
    
    **Endpoints:**
    - GET /api/admin/payment/config/ - List (returns singleton as list)
    - GET /api/admin/payment/config/{id}/ - Retrieve config details
    - POST /api/admin/payment/config/ - Create/update config
    - PUT /api/admin/payment/config/{id}/ - Full update
    - PATCH /api/admin/payment/config/{id}/ - Partial update
    - POST /api/admin/payment/config/{id}/test-paystack/ - Test Paystack connection
    - POST /api/admin/payment/config/{id}/test-stripe/ - Test Stripe connection
    
    **Permissions:** Admin only (IsAuthenticated + IsAdmin)
    
    **Features:**
    - Singleton pattern (only one instance exists)
    - Encrypted sensitive keys (secret keys, webhook secrets)
    - Masked key display (never expose raw keys)
    - Provider configuration (Paystack/Stripe)
    - Multi-currency support
    - Test connection actions for both providers
    
    Phase 0.5, Task 0.5.29
    """
    serializer_class = PaymentConfigurationSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    queryset = PaymentConfiguration.objects.all()
    http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options']  # No DELETE for singleton
    
    def get_queryset(self):
        """Return singleton instance as queryset."""
        # Always return the singleton instance
        instance = PaymentConfiguration.get_instance()
        return PaymentConfiguration.objects.filter(pk=instance.pk)
    
    def list(self, request, *args, **kwargs):
        """List returns the singleton instance as a single-item list."""
        instance = PaymentConfiguration.get_instance()
        serializer = self.get_serializer(instance)
        return Response([serializer.data])
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve the singleton instance."""
        instance = PaymentConfiguration.get_instance()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """
        Create/update the singleton instance.
        Acts like update since only one instance can exist.
        """
        instance = PaymentConfiguration.get_instance()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def update(self, request, *args, **kwargs):
        """Full update of the singleton instance."""
        instance = PaymentConfiguration.get_instance()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    def partial_update(self, request, *args, **kwargs):
        """Partial update of the singleton instance."""
        instance = PaymentConfiguration.get_instance()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], url_path='test-paystack')
    def test_paystack(self, request):
        """
        Test Paystack API connection by verifying the secret key.
        
        **Request:** POST /api/admin/payment/config/test-paystack/
        
        **Response:**
        ```json
        {
            "success": true,
            "message": "Paystack connection successful",
            "details": "API key is valid and working"
        }
        ```
        
        **Errors:**
        - 400: No secret key configured or invalid key
        - 401: Invalid secret key
        - 408: Request timeout
        - 500: Unexpected error
        """
        import requests
        from requests.exceptions import Timeout, RequestException
        
        instance = PaymentConfiguration.get_instance()
        
        # Check if Paystack is configured
        if not instance.paystack_secret_key:
            return Response({
                'success': False,
                'message': 'Paystack secret key not configured'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Decrypt the secret key
            secret_key = instance.decrypt_field('paystack_secret_key')
            
            # Test API call to Paystack
            url = 'https://api.paystack.co/transaction/initialize'
            headers = {
                'Authorization': f'Bearer {secret_key}',
                'Content-Type': 'application/json'
            }
            
            # Simple test: Try to initialize a transaction with minimal data
            # This will fail but will tell us if the key is valid
            test_data = {
                'email': 'test@example.com',
                'amount': '10000'  # 100 NGN in kobo
            }
            
            response = requests.post(
                url,
                json=test_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                # Success - key is valid
                return Response({
                    'success': True,
                    'message': 'Paystack connection successful',
                    'details': 'API key is valid and working'
                })
            elif response.status_code == 401:
                # Invalid key
                return Response({
                    'success': False,
                    'message': 'Invalid Paystack secret key'
                }, status=status.HTTP_401_UNAUTHORIZED)
            else:
                # Other error
                error_data = response.json() if response.content else {}
                return Response({
                    'success': False,
                    'message': f'Paystack API error: {error_data.get("message", "Unknown error")}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        except Timeout:
            return Response({
                'success': False,
                'message': 'Connection timeout - Paystack API not reachable'
            }, status=status.HTTP_408_REQUEST_TIMEOUT)
        except RequestException as e:
            return Response({
                'success': False,
                'message': f'Network error: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Unexpected error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], url_path='test-stripe')
    def test_stripe(self, request):
        """
        Test Stripe API connection by retrieving account info.
        
        **Request:** POST /api/admin/payment/config/test-stripe/
        
        **Response:**
        ```json
        {
            "success": true,
            "message": "Stripe connection successful",
            "account_info": {
                "id": "acct_123",
                "email": "business@example.com",
                "country": "US"
            }
        }
        ```
        
        **Errors:**
        - 400: No secret key configured or invalid key
        - 401: Invalid secret key
        - 408: Request timeout
        - 500: Unexpected error
        """
        import requests
        from requests.exceptions import Timeout, RequestException
        
        instance = PaymentConfiguration.get_instance()
        
        # Check if Stripe is configured
        if not instance.stripe_secret_key:
            return Response({
                'success': False,
                'message': 'Stripe secret key not configured'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Decrypt the secret key
            secret_key = instance.decrypt_field('stripe_secret_key')
            
            # Test API call to Stripe - get account info
            url = 'https://api.stripe.com/v1/account'
            headers = {
                'Authorization': f'Bearer {secret_key}'
            }
            
            response = requests.get(
                url,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                # Success - key is valid
                account_data = response.json()
                return Response({
                    'success': True,
                    'message': 'Stripe connection successful',
                    'account_info': {
                        'id': account_data.get('id'),
                        'email': account_data.get('email'),
                        'country': account_data.get('country'),
                        'charges_enabled': account_data.get('charges_enabled'),
                        'payouts_enabled': account_data.get('payouts_enabled'),
                    }
                })
            elif response.status_code == 401:
                # Invalid key
                return Response({
                    'success': False,
                    'message': 'Invalid Stripe secret key'
                }, status=status.HTTP_401_UNAUTHORIZED)
            else:
                # Other error
                error_data = response.json() if response.content else {}
                return Response({
                    'success': False,
                    'message': f'Stripe API error: {error_data.get("error", {}).get("message", "Unknown error")}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        except Timeout:
            return Response({
                'success': False,
                'message': 'Connection timeout - Stripe API not reachable'
            }, status=status.HTTP_408_REQUEST_TIMEOUT)
        except RequestException as e:
            return Response({
                'success': False,
                'message': f'Network error: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Unexpected error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# EMAIL CONFIGURATION API (Task 0.5.30)
# ============================================================================

class EmailConfigurationViewSet(viewsets.ModelViewSet):
    """
    Admin-only API for managing Email Configuration (singleton).
    
    Supports SMTP server configuration with encrypted password storage.
    
    **Endpoints:**
    - GET /api/admin/email/config/ - List (returns singleton as list)
    - GET /api/admin/email/config/{id}/ - Retrieve config details
    - POST /api/admin/email/config/ - Create/update config
    - PUT /api/admin/email/config/{id}/ - Full update
    - PATCH /api/admin/email/config/{id}/ - Partial update
    - POST /api/admin/email/config/{id}/test-connection/ - Test SMTP connection
    
    **Permissions:** Admin only (IsAuthenticated + IsAdmin)
    
    **Features:**
    - Singleton pattern (only one instance exists)
    - Encrypted SMTP password (never expose raw password)
    - Masked password display
    - SMTP connection testing
    - TLS/SSL validation
    - Port validation
    
    Phase 0.5, Task 0.5.30
    """
    serializer_class = EmailConfigurationSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    queryset = EmailConfiguration.objects.all()
    http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options']  # No DELETE for singleton
    
    def get_queryset(self):
        """Return singleton instance as queryset."""
        # Always return the singleton instance
        instance = EmailConfiguration.get_instance()
        return EmailConfiguration.objects.filter(pk=instance.pk)
    
    def list(self, request, *args, **kwargs):
        """List returns the singleton instance as a single-item list."""
        instance = EmailConfiguration.get_instance()
        serializer = self.get_serializer(instance)
        return Response([serializer.data])
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve the singleton instance."""
        instance = EmailConfiguration.get_instance()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """Create or update the singleton instance."""
        instance = EmailConfiguration.get_instance()
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def update(self, request, *args, **kwargs):
        """Full update of the singleton instance."""
        instance = EmailConfiguration.get_instance()
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    def partial_update(self, request, *args, **kwargs):
        """Partial update of the singleton instance."""
        instance = EmailConfiguration.get_instance()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='test-connection')
    def test_connection(self, request, pk=None):
        """
        Test SMTP connection with current configuration.
        
        **Request:** POST /api/admin/email/config/{id}/test-connection/
        
        **Success Response (200):**
        ```json
        {
            "success": true,
            "message": "Successfully connected to smtp.gmail.com:587",
            "host": "smtp.gmail.com",
            "port": 587,
            "encryption": "TLS"
        }
        ```
        
        **Error Responses:**
        - 400: Missing required settings
        - 401: Authentication failed
        - 408: Connection timeout
        - 500: Unexpected error
        """
        config = self.get_object()
        
        # Validate that configuration has required fields
        if not config.smtp_host:
            return Response({
                'success': False,
                'message': 'SMTP host is not configured'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not config.smtp_username or not config.smtp_password:
            return Response({
                'success': False,
                'message': 'SMTP credentials (username and password) are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Test connection using model method
        try:
            result = config.test_connection()
            
            if result['success']:
                # Return success with connection details
                encryption_type = 'SSL' if config.use_ssl else 'TLS'
                return Response({
                    'success': True,
                    'message': result['message'],
                    'host': config.smtp_host,
                    'port': config.smtp_port,
                    'encryption': encryption_type
                }, status=status.HTTP_200_OK)
            else:
                # Return error from test_connection
                # Determine appropriate status code based on error message
                error_msg = result['message'].lower()
                
                if 'authentication' in error_msg or 'login' in error_msg:
                    status_code = status.HTTP_401_UNAUTHORIZED
                elif 'timeout' in error_msg:
                    status_code = status.HTTP_408_REQUEST_TIMEOUT
                elif 'credentials' in error_msg or 'required' in error_msg:
                    status_code = status.HTTP_400_BAD_REQUEST
                else:
                    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
                
                return Response({
                    'success': False,
                    'message': result['message']
                }, status=status_code)
                
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Unexpected error during connection test: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'], url_path='send-test')
    def send_test_email(self, request, pk=None):
        """
        Send a test email to verify SMTP configuration.
        
        POST /api/admin/email/config/{id}/send-test/
        
        Request Body:
        {
            "recipient": "test@example.com"  // Required
        }
        
        Returns:
            200: Email sent successfully
            400: Missing recipient or configuration incomplete
            401: Authentication failed
            408: Connection timeout
            500: Unexpected error
        """
        instance = self.get_object()
        
        # Get recipient from request
        recipient = request.data.get('recipient')
        
        if not recipient:
            return Response({
                'success': False,
                'message': 'Recipient email address is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate recipient email format
        from django.core.validators import EmailValidator
        from django.core.exceptions import ValidationError as DjangoValidationError
        
        validator = EmailValidator()
        try:
            validator(recipient)
        except DjangoValidationError:
            return Response({
                'success': False,
                'message': f'Invalid email address: {recipient}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if SMTP is configured
        if not instance.is_configured():
            return Response({
                'success': False,
                'message': 'Email configuration is incomplete. Please configure SMTP settings first.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Send test email using Django's email backend
            from django.core.mail import send_mail
            from django.conf import settings
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Decrypt SMTP password before using
            try:
                decrypted_password = instance.decrypt_field('smtp_password')
            except Exception as e:
                return Response({
                    'success': False,
                    'message': f'Failed to decrypt SMTP password: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Create connection with current settings
            from django.core.mail import get_connection
            
            # Build connection kwargs
            connection_kwargs = {
                'host': instance.smtp_host,
                'port': instance.smtp_port,
                'username': instance.smtp_username,
                'password': decrypted_password,  # Use decrypted password
                'use_tls': instance.use_tls,
                'use_ssl': instance.use_ssl,
                'timeout': 10,
            }
            
            connection = get_connection(
                backend='django.core.mail.backends.smtp.EmailBackend',
                **connection_kwargs
            )
            
            # Prepare test email
            subject = 'Test Email from Oxidane Platform'
            from_email = f'{instance.from_name} <{instance.from_email}>' if instance.from_name else instance.from_email
            
            message_body = f"""
Hello,

This is a test email from the Oxidane Platform to verify your SMTP configuration.

Configuration Details:
- SMTP Host: {instance.smtp_host}
- SMTP Port: {instance.smtp_port}
- Encryption: {'TLS' if instance.use_tls else 'SSL' if instance.use_ssl else 'None'}
- From: {from_email}

If you received this email, your email configuration is working correctly!

Best regards,
Oxidane Platform
            """.strip()
            
            # Send the email
            send_mail(
                subject=subject,
                message=message_body,
                from_email=from_email,
                recipient_list=[recipient],
                connection=connection,
                fail_silently=False,
            )
            
            return Response({
                'success': True,
                'message': f'Test email sent successfully to {recipient}',
                'recipient': recipient,
                'from_email': from_email
            }, status=status.HTTP_200_OK)
            
        except smtplib.SMTPAuthenticationError as e:
            return Response({
                'success': False,
                'message': f'Authentication failed: {str(e)}'
            }, status=status.HTTP_401_UNAUTHORIZED)
            
        except smtplib.SMTPException as e:
            return Response({
                'success': False,
                'message': f'SMTP error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except TimeoutError:
            return Response({
                'success': False,
                'message': 'Connection timeout. Please check your SMTP host and port.'
            }, status=status.HTTP_408_REQUEST_TIMEOUT)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Failed to send test email: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# SETUP STATUS API (Task 0.5.32)
# ============================================================================

class SetupStatusViewSet(viewsets.ViewSet):
    """
    Admin-only API for checking platform setup/configuration status.
    
    **Endpoints:**
    - GET /api/admin/setup/status/ - Get comprehensive setup status
    
    **Permissions:** Admin only (IsAuthenticated + IsAdmin)
    
    **Response includes:**
    - Overall setup completion percentage
    - Individual component status (Telegram, Payment, Email)
    - Database status (plans, features, groups)
    - Recommendations for incomplete setup
    
    Phase 0.5, Task 0.5.32
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def list(self, request):
        """
        Get comprehensive platform setup status.
        
        GET /api/admin/setup/status/
        
        Returns:
        {
            "setup_complete": bool,
            "completion_percentage": int,  // 0-100
            "components": {
                "telegram": {...},
                "payment": {...},
                "email": {...},
                "database": {...}
            },
            "recommendations": [...]
        }
        """
        from subscriptions.models import (
            TelegramConfiguration, PaymentConfiguration, EmailConfiguration,
            SubscriptionPlan, Feature, TelegramGroup
        )
        
        recommendations = []
        
        # ===== TELEGRAM CONFIGURATION =====
        telegram_config = TelegramConfiguration.get_instance()
        telegram_status = {
            'configured': False,
            'healthy': telegram_config.is_healthy(),
            'has_token': bool(telegram_config.bot_token),
            'has_username': bool(telegram_config.bot_username),
            'last_check': telegram_config.last_health_check,
            'connection_status': 'connected' if telegram_config.is_connected else 'disconnected'
        }
        
        # Check if Telegram is configured
        if telegram_config.bot_token and telegram_config.is_enabled:
            telegram_status['configured'] = True
        else:
            recommendations.append({
                'component': 'telegram',
                'message': 'Configure Telegram bot to enable automated group management',
                'action': 'Add bot token in Telegram Configuration'
            })
        
        # ===== PAYMENT CONFIGURATION =====
        payment_config = PaymentConfiguration.get_instance()
        payment_status = {
            'configured': False,
            'paystack_configured': bool(payment_config.paystack_secret_key),
            'stripe_configured': bool(payment_config.stripe_secret_key),
            'test_mode': payment_config.is_test_mode
        }
        
        # Check if at least one payment gateway is configured
        if payment_config.paystack_secret_key or payment_config.stripe_secret_key:
            payment_status['configured'] = True
        else:
            recommendations.append({
                'component': 'payment',
                'message': 'Configure at least one payment gateway (Paystack or Stripe)',
                'action': 'Add payment gateway credentials in Payment Configuration'
            })
        
        # ===== EMAIL CONFIGURATION =====
        email_config = EmailConfiguration.get_instance()
        email_status = {
            'configured': email_config.is_configured(),
            'enabled': email_config.is_enabled,
            'has_host': bool(email_config.smtp_host),
            'has_credentials': bool(email_config.smtp_username and email_config.smtp_password),
            'connection_status': 'connected' if email_config.is_connected else 'not_tested',
            'last_test': email_config.last_test_at
        }
        
        if not email_config.is_configured():
            recommendations.append({
                'component': 'email',
                'message': 'Configure SMTP settings to enable email notifications',
                'action': 'Add SMTP credentials in Email Configuration'
            })
        
        # ===== DATABASE CONTENT =====
        plans_count = SubscriptionPlan.objects.filter(is_active=True).count()
        features_count = Feature.objects.count()
        groups_count = TelegramGroup.objects.filter(is_active=True).count()
        
        database_status = {
            'has_active_plans': plans_count > 0,
            'plans_count': plans_count,
            'features_count': features_count,
            'active_groups_count': groups_count,
            'ready': plans_count > 0  # At least one plan is required
        }
        
        if plans_count == 0:
            recommendations.append({
                'component': 'database',
                'message': 'Create at least one subscription plan',
                'action': 'Add subscription plans via Plans API'
            })
        
        if features_count == 0:
            recommendations.append({
                'component': 'database',
                'message': 'Define platform features for subscription plans',
                'action': 'Add features via Features API'
            })
        
        # ===== CALCULATE COMPLETION =====
        # Count 5 separate checks to match frontend display:
        # 1. Telegram, 2. Payment, 3. Email, 4. Plans, 5. Features
        checks = [
            telegram_status['configured'],
            payment_status['configured'],
            email_status['configured'],
            database_status['has_active_plans'],  # Plans step
            features_count > 0  # Features step
        ]
        
        completed_checks = sum(checks)
        total_checks = len(checks)
        completion_percentage = int((completed_checks / total_checks) * 100)
        setup_complete = completion_percentage == 100
        
        return Response({
            'setup_complete': setup_complete,
            'completion_percentage': completion_percentage,
            'components': {
                'telegram': telegram_status,
                'payment': payment_status,
                'email': email_status,
                'database': database_status
            },
            'recommendations': recommendations,
            'summary': {
                'total_checks': total_checks,
                'completed_checks': completed_checks,
                'pending_checks': total_checks - completed_checks
            }
        })


# ============================================================================
# PUBLIC PRICING API (Task 0.5.33)
# ============================================================================

class PublicPricingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public API for subscription plans with multi-currency support.
    
    **Endpoints:**
    - GET /api/v1/subscriptions/plans/ - List all active plans
    - GET /api/v1/subscriptions/plans/{id}/ - Get plan details
    
    **Query Parameters:**
    - currency: Currency code (USD, NGN, GBP, EUR, etc.) - defaults to USD
    - billing_period: Filter by billing period (weekly, monthly, quarterly, yearly, lifetime)
    - featured: Filter featured plans (true/false)
    
    **Features:**
    - Automatic currency conversion using live exchange rates
    - Includes plan features in response
    - Public access (no authentication required)
    - Returns only active plans
    
    **Response Format:**
    {
        "id": "uuid",
        "name": "Premium Plan",
        "description": "...",
        "price": 99.00,
        "currency": "USD",
        "base_price_usd": 99.00,
        "billing_period": "monthly",
        "billing_period_display": "Monthly",
        "trial_days": 7,
        "is_featured": true,
        "features": [
            {
                "id": "uuid",
                "name": "Feature Name",
                "description": "...",
                "icon": "✨",
                "category": "signals"
            }
        ],
        "limits": {...}
    }
    
    Phase 0.5, Task 0.5.33
    """
    permission_classes = [AllowAny]
    serializer_class = PublicPricingPlanSerializer
    pagination_class = SubscriptionPlanPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['billing_period', 'is_featured']
    search_fields = ['name', 'description']
    ordering_fields = ['base_price', 'name']
    ordering = ['sort_order', 'base_price']
    
    def get_queryset(self):
        """
        Return only active subscription plans with features prefetched.
        Public API always shows only active plans.
        """
        return SubscriptionPlan.objects.filter(
            is_active=True
        ).prefetch_related('features').order_by('sort_order', 'base_price')
    
    def list(self, request, *args, **kwargs):
        """
        List all active plans with optional currency conversion.
        
        GET /api/v1/subscriptions/plans/?currency=NGN
        """
        # Get requested currency (default: USD)
        currency = request.query_params.get('currency', 'USD').upper()
        
        # Get queryset and apply filters
        queryset = self.filter_queryset(self.get_queryset())
        
        # Paginate
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            # Convert prices to requested currency
            data = self._convert_prices(serializer.data, currency)
            return self.get_paginated_response(data)
        
        serializer = self.get_serializer(queryset, many=True)
        data = self._convert_prices(serializer.data, currency)
        return Response(data)
    
    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a single plan with optional currency conversion.
        
        GET /api/v1/subscriptions/plans/{id}/?currency=NGN
        """
        # Get requested currency (default: USD)
        currency = request.query_params.get('currency', 'USD').upper()
        
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        # Convert price to requested currency
        data = self._convert_prices([serializer.data], currency)[0]
        return Response(data)
    
    def _convert_prices(self, plans_data, target_currency):
        """
        Convert plan prices from USD to target currency.
        
        Args:
            plans_data (list): List of plan dictionaries
            target_currency (str): Target currency code
            
        Returns:
            list: Plans data with converted prices
        """
        from subscriptions.models import ExchangeRate
        from decimal import Decimal
        
        # If target currency is USD, no conversion needed
        if target_currency == 'USD':
            for plan in plans_data:
                # price already set by serializer as float
                plan['currency'] = 'USD'
                plan['base_price_usd'] = plan['price']
            return plans_data
        
        # Convert each plan's price
        for plan in plans_data:
            base_price = Decimal(str(plan['price']))
            
            # Attempt currency conversion
            converted_price = ExchangeRate.convert_amount(
                amount=base_price,
                from_currency='USD',
                to_currency=target_currency,
                round_result=True
            )
            
            if converted_price is not None:
                # Conversion successful
                plan['price'] = float(converted_price)
                plan['currency'] = target_currency
                plan['base_price_usd'] = float(base_price)
            else:
                # Conversion failed - fallback to USD
                plan['price'] = float(base_price)
                plan['currency'] = 'USD'
                plan['base_price_usd'] = float(base_price)
                # Note: In production, you might want to log this
        
        return plans_data


# ============================================================================
# VALIDATE COUPON API (Task 0.5.34)
# ============================================================================

class ValidateCouponViewSet(viewsets.ViewSet):
    """
    Public API endpoint for validating coupon codes during checkout.
    
    **Endpoint:**
    - POST /api/v1/subscriptions/validate-coupon/ - Validate a coupon code
    
    **Request Body:**
    {
        "code": "SAVE20",
        "plan_id": "uuid-string",  // optional - validate for specific plan
        "amount": 99.00,            // optional - original price for discount calculation
        "user_id": "uuid-string"    // optional - check user-specific usage limits
    }
    
    **Response Format (Success):**
    {
        "valid": true,
        "code": "SAVE20",
        "discount_type": "percentage",
        "discount_value": 20.0,
        "discount_display": "20% off",
        "original_price": 99.00,
        "discount_amount": 19.80,
        "final_price": 79.20,
        "savings_percentage": 20.0,
        "message": "Coupon applied successfully!"
    }
    
    **Response Format (Invalid):**
    {
        "valid": false,
        "code": "INVALID",
        "error": "Coupon code not found or inactive",
        "error_code": "COUPON_NOT_FOUND"
    }
    
    **Error Codes:**
    - COUPON_NOT_FOUND: Code doesn't exist or is inactive
    - COUPON_EXPIRED: Coupon has expired
    - COUPON_NOT_STARTED: Coupon is not yet valid
    - USAGE_LIMIT_REACHED: Total usage limit exceeded
    - USER_LIMIT_REACHED: User has already used this coupon max times
    - PLAN_NOT_APPLICABLE: Coupon doesn't apply to the specified plan
    - MISSING_PLAN_ID: Plan ID required for plan-specific coupons
    
    Phase 0.5, Task 0.5.34
    """
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'], url_path='validate')
    def validate(self, request):
        """
        Validate a coupon code and calculate discount.
        
        POST /api/v1/subscriptions/validate-coupon/validate/
        """
        code = request.data.get('code', '').strip().upper()
        plan_id = request.data.get('plan_id')
        amount = request.data.get('amount')
        user_id = request.data.get('user_id')
        
        # Validate required fields
        if not code:
            return Response({
                'valid': False,
                'error': 'Coupon code is required',
                'error_code': 'MISSING_CODE'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Try to find the coupon
        try:
            coupon = Coupon.objects.get(code=code)
        except Coupon.DoesNotExist:
            return Response({
                'valid': False,
                'code': code,
                'error': 'Coupon code not found or inactive',
                'error_code': 'COUPON_NOT_FOUND'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if coupon is active
        if not coupon.is_active:
            return Response({
                'valid': False,
                'code': code,
                'error': 'This coupon is no longer active',
                'error_code': 'COUPON_INACTIVE'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check time validity
        now = timezone.now()
        
        if coupon.valid_from and now < coupon.valid_from:
            return Response({
                'valid': False,
                'code': code,
                'error': f'Coupon is not valid until {coupon.valid_from.strftime("%Y-%m-%d")}',
                'error_code': 'COUPON_NOT_STARTED',
                'valid_from': coupon.valid_from.isoformat()
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if coupon.valid_until and now > coupon.valid_until:
            return Response({
                'valid': False,
                'code': code,
                'error': f'Coupon expired on {coupon.valid_until.strftime("%Y-%m-%d")}',
                'error_code': 'COUPON_EXPIRED',
                'valid_until': coupon.valid_until.isoformat()
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check total usage limit
        if not coupon.is_usage_available():
            return Response({
                'valid': False,
                'code': code,
                'error': 'This coupon has reached its usage limit',
                'error_code': 'USAGE_LIMIT_REACHED',
                'current_uses': coupon.current_uses,
                'max_uses': coupon.max_uses
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check user-specific usage limit (if user_id provided)
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                # Get billing profile for the user
                from subscriptions.models import BillingProfile
                billing_profile = BillingProfile.objects.filter(user=user).first()
                
                if billing_profile:
                    # Count how many times this user has used this coupon
                    # Check gateway_response metadata since that's where coupon_code is stored
                    user_usage_count = Payment.objects.filter(
                        billing_profile=billing_profile,
                        status__in=['completed', 'success'],
                        gateway_response__metadata__coupon_code=code
                    ).count()
                    
                    if user_usage_count >= coupon.max_uses_per_user:
                        return Response({
                            'valid': False,
                            'code': code,
                            'error': f'You have already used this coupon {coupon.max_uses_per_user} time(s)',
                            'error_code': 'USER_LIMIT_REACHED',
                            'user_usage': user_usage_count,
                            'max_uses_per_user': coupon.max_uses_per_user
                        }, status=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist:
                pass  # Invalid user_id, but don't fail validation
        
        # Check plan applicability (if plan_id provided)
        plan = None
        if plan_id:
            try:
                plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
                
                if not coupon.applies_to_plan(plan):
                    # Get applicable plan names for better error message
                    applicable_plans = coupon.plans.filter(is_active=True)
                    if applicable_plans.exists():
                        plan_names = ', '.join([p.name for p in applicable_plans[:3]])
                        error_msg = f'This coupon is only valid for: {plan_names}'
                    else:
                        error_msg = 'This coupon is not applicable to the selected plan'
                    
                    return Response({
                        'valid': False,
                        'code': code,
                        'error': error_msg,
                        'error_code': 'PLAN_NOT_APPLICABLE'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
            except SubscriptionPlan.DoesNotExist:
                return Response({
                    'valid': False,
                    'error': 'Invalid plan ID',
                    'error_code': 'INVALID_PLAN_ID'
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            # If coupon has plan restrictions but no plan_id provided
            if coupon.plans.exists():
                return Response({
                    'valid': False,
                    'code': code,
                    'error': 'This coupon requires a plan to be selected',
                    'error_code': 'MISSING_PLAN_ID'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate discount if amount provided
        discount_info = None
        if amount:
            try:
                amount = Decimal(str(amount))
                discount_info = coupon.calculate_discount(amount)
            except (ValueError, TypeError, InvalidOperation):
                return Response({
                    'valid': False,
                    'error': 'Invalid amount provided',
                    'error_code': 'INVALID_AMOUNT'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Build success response
        response_data = {
            'valid': True,
            'code': coupon.code,
            'discount_type': coupon.discount_type,
            'discount_value': float(coupon.discount_value),
            'discount_display': coupon.get_discount_display(),
            'description': coupon.description,
            'message': 'Coupon applied successfully!'
        }
        
        # Add discount calculation if amount was provided
        if discount_info:
            response_data.update({
                'original_price': float(discount_info['original_price']),
                'discount_amount': float(discount_info['discount_amount']),
                'final_price': float(discount_info['final_price']),
                'savings_percentage': float(discount_info['savings_percentage'])
            })
        
        # Add plan info if applicable
        if plan:
            response_data['applicable_plan'] = {
                'id': str(plan.id),
                'name': plan.name,
                'slug': plan.slug
            }
        
        # Add usage stats
        response_data['usage'] = {
            'current_uses': coupon.current_uses,
            'max_uses': coupon.max_uses,
            'remaining_uses': (coupon.max_uses - coupon.current_uses) if coupon.max_uses else None
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


class SubscriptionUpgradeViewSet(viewsets.ViewSet):
    """
    ViewSet for upgrading subscription plans (Phase 0.5 - Task 0.5.36)
    
    Handles immediate plan upgrades with prorated billing.
    User receives credit for unused portion of current plan.
    
    Endpoints:
    - POST /api/v1/subscriptions/{id}/upgrade/
    
    Request Body:
    - new_plan_id (required): UUID of the plan to upgrade to
    - payment_reference (optional): Payment reference for the upgrade transaction
    
    Returns:
    - Cost breakdown with prorated credit
    - New plan details and end date
    - Amount due for upgrade
    
    Error Codes:
    - SUBSCRIPTION_NOT_FOUND: Subscription doesn't exist
    - SUBSCRIPTION_INACTIVE: Cannot upgrade inactive subscription
    - MISSING_PLAN_ID: No new plan ID provided
    - PLAN_NOT_FOUND: New plan doesn't exist
    - PLAN_INACTIVE: New plan is not active
    - SAME_PLAN: Trying to upgrade to current plan
    - INVALID_UPGRADE: New plan is not an upgrade (lower or same price)
    """
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['post'], url_path='upgrade')
    def upgrade_subscription(self, request, pk=None):
        """
        Upgrade subscription to a higher-tier plan with prorated credit.
        
        POST /api/v1/subscriptions/{id}/upgrade/
        Body: {"new_plan_id": "uuid", "payment_reference": "optional"}
        """
        
        # Get subscription
        try:
            subscription = Subscription.objects.select_related('plan', 'billing_profile__user').get(pk=pk)
        except Subscription.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Subscription not found',
                'error_code': 'SUBSCRIPTION_NOT_FOUND'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user owns this subscription
        if subscription.billing_profile.user != request.user and not request.user.is_staff:
            return Response({
                'success': False,
                'error': 'You do not have permission to upgrade this subscription',
                'error_code': 'PERMISSION_DENIED'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if subscription is active
        if not subscription.is_active:
            return Response({
                'success': False,
                'error': 'Cannot upgrade an inactive subscription',
                'error_code': 'SUBSCRIPTION_INACTIVE',
                'current_status': subscription.status
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get new plan ID
        new_plan_id = request.data.get('new_plan_id')
        payment_reference = request.data.get('payment_reference')
        
        if not new_plan_id:
            return Response({
                'success': False,
                'error': 'New plan ID is required',
                'error_code': 'MISSING_PLAN_ID'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get new plan
        try:
            new_plan = SubscriptionPlan.objects.get(pk=new_plan_id)
        except (SubscriptionPlan.DoesNotExist, ValueError, DjangoValidationError):
            return Response({
                'success': False,
                'error': 'Plan not found',
                'error_code': 'PLAN_NOT_FOUND'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if new plan is active
        if not new_plan.is_active:
            return Response({
                'success': False,
                'error': 'The selected plan is not currently available',
                'error_code': 'PLAN_INACTIVE'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if trying to upgrade to same plan
        if subscription.plan and subscription.plan.id == new_plan.id:
            return Response({
                'success': False,
                'error': 'You are already subscribed to this plan',
                'error_code': 'SAME_PLAN'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate upgrade (new plan should be higher price)
        if subscription.plan:
            current_monthly_price = subscription.plan.get_monthly_equivalent()
            new_monthly_price = new_plan.get_monthly_equivalent()
            
            if new_monthly_price <= current_monthly_price:
                return Response({
                    'success': False,
                    'error': 'Cannot upgrade to a plan with lower or equal value. Use downgrade instead.',
                    'error_code': 'INVALID_UPGRADE',
                    'current_plan_monthly': float(current_monthly_price),
                    'new_plan_monthly': float(new_monthly_price)
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate upgrade cost
        try:
            cost_breakdown = subscription.calculate_upgrade_cost(new_plan)
        except ValueError as e:
            return Response({
                'success': False,
                'error': str(e),
                'error_code': 'CALCULATION_ERROR'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Perform upgrade
        try:
            upgrade_details = subscription.upgrade_plan(new_plan, payment_reference)
            
            # Build success response
            response_data = {
                'success': True,
                'message': f'Successfully upgraded to {new_plan.name}',
                'subscription_id': str(subscription.id),
                'upgrade_details': {
                    'old_plan': upgrade_details['current_plan_name'],
                    'new_plan': upgrade_details['new_plan_name'],
                    'old_plan_price': float(upgrade_details['current_plan_price']),
                    'new_plan_price': float(upgrade_details['new_plan_price']),
                    'prorated_credit': float(upgrade_details['prorated_credit']),
                    'amount_due': float(upgrade_details['amount_due']),
                    'days_remaining_old_plan': upgrade_details['days_remaining'],
                    'old_end_date': upgrade_details['current_end_date'].isoformat(),
                    'new_end_date': upgrade_details['new_end_date'].isoformat(),
                    'upgraded_at': timezone.now().isoformat()
                }
            }
            
            if payment_reference:
                response_data['payment_reference'] = payment_reference
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response({
                'success': False,
                'error': str(e),
                'error_code': 'UPGRADE_FAILED'
            }, status=status.HTTP_400_BAD_REQUEST)


class SubscriptionDowngradeViewSet(viewsets.ViewSet):
    """
    ViewSet for downgrading subscription plans (Phase 0.5 - Task 0.5.36)
    
    Handles plan downgrades with two modes:
    - Scheduled: Downgrade takes effect at end of current billing period (default)
    - Immediate: Downgrade immediately without refund (no prorated credit)
    
    Endpoints:
    - POST /api/v1/subscriptions/{id}/downgrade/
    
    Request Body:
    - new_plan_id (required): UUID of the plan to downgrade to
    - immediate (optional): Boolean, if True downgrade immediately
    
    Returns:
    - Downgrade details
    - Effective date (when change takes effect)
    - End date of current subscription
    
    Error Codes:
    - SUBSCRIPTION_NOT_FOUND: Subscription doesn't exist
    - SUBSCRIPTION_INACTIVE: Cannot downgrade inactive subscription
    - MISSING_PLAN_ID: No new plan ID provided
    - PLAN_NOT_FOUND: New plan doesn't exist
    - PLAN_INACTIVE: New plan is not active
    - SAME_PLAN: Trying to downgrade to current plan
    - INVALID_DOWNGRADE: New plan is not a downgrade (higher or same price)
    """
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['post'], url_path='downgrade')
    def downgrade_subscription(self, request, pk=None):
        """
        Downgrade subscription to a lower-tier plan.
        
        POST /api/v1/subscriptions/{id}/downgrade/
        Body: {"new_plan_id": "uuid", "immediate": false}
        """
        
        # Get subscription
        try:
            subscription = Subscription.objects.select_related('plan', 'billing_profile__user').get(pk=pk)
        except Subscription.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Subscription not found',
                'error_code': 'SUBSCRIPTION_NOT_FOUND'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user owns this subscription
        if subscription.billing_profile.user != request.user and not request.user.is_staff:
            return Response({
                'success': False,
                'error': 'You do not have permission to downgrade this subscription',
                'error_code': 'PERMISSION_DENIED'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if subscription is active
        if not subscription.is_active:
            return Response({
                'success': False,
                'error': 'Cannot downgrade an inactive subscription',
                'error_code': 'SUBSCRIPTION_INACTIVE',
                'current_status': subscription.status
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get new plan ID and immediate flag
        new_plan_id = request.data.get('new_plan_id')
        immediate = request.data.get('immediate', False)
        
        if not new_plan_id:
            return Response({
                'success': False,
                'error': 'New plan ID is required',
                'error_code': 'MISSING_PLAN_ID'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get new plan
        try:
            new_plan = SubscriptionPlan.objects.get(pk=new_plan_id)
        except (SubscriptionPlan.DoesNotExist, ValueError, DjangoValidationError):
            return Response({
                'success': False,
                'error': 'Plan not found',
                'error_code': 'PLAN_NOT_FOUND'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if new plan is active
        if not new_plan.is_active:
            return Response({
                'success': False,
                'error': 'The selected plan is not currently available',
                'error_code': 'PLAN_INACTIVE'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if trying to downgrade to same plan
        if subscription.plan and subscription.plan.id == new_plan.id:
            return Response({
                'success': False,
                'error': 'You are already subscribed to this plan',
                'error_code': 'SAME_PLAN'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate downgrade (new plan should be lower price)
        if subscription.plan:
            current_monthly_price = subscription.plan.get_monthly_equivalent()
            new_monthly_price = new_plan.get_monthly_equivalent()
            
            if new_monthly_price >= current_monthly_price:
                return Response({
                    'success': False,
                    'error': 'Cannot downgrade to a plan with higher or equal value. Use upgrade instead.',
                    'error_code': 'INVALID_DOWNGRADE',
                    'current_plan_monthly': float(current_monthly_price),
                    'new_plan_monthly': float(new_monthly_price)
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Perform downgrade
        try:
            downgrade_details = subscription.downgrade_plan(new_plan, immediate=immediate)
            
            # Build success response
            response_data = {
                'success': True,
                'message': downgrade_details.get('message', f'Successfully downgraded to {new_plan.name}'),
                'subscription_id': str(subscription.id),
                'downgrade_details': {
                    'old_plan': downgrade_details['old_plan_name'],
                    'new_plan': downgrade_details['new_plan_name'],
                    'new_plan_price': float(downgrade_details['new_plan_price']),
                    'effective_date': downgrade_details['effective_date'].isoformat(),
                    'end_date': downgrade_details['end_date'].isoformat(),
                    'immediate': downgrade_details['immediate'],
                    'downgraded_at': timezone.now().isoformat()
                }
            }
            
            if not immediate:
                response_data['note'] = 'Downgrade scheduled for end of current billing period. You will retain access to current plan features until then.'
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response({
                'success': False,
                'error': str(e),
                'error_code': 'DOWNGRADE_FAILED'
            }, status=status.HTTP_400_BAD_REQUEST)


class CurrencyConversionViewSet(viewsets.ViewSet):
    """
    ViewSet for live currency conversion
    
    Provides:
    - convert: GET /currency/convert/?from=USD&to=NGN&amount=30
    - rates: GET /currency/rates/?base=USD
    
    Uses smart caching with 1-hour expiry via ExchangeRateService
    """
    permission_classes = [AllowAny]
    
    def list(self, request):
        """
        Default list action - redirect to convert
        """
        return self.convert(request)
    
    @action(detail=False, methods=['get'], url_path='convert')
    def convert(self, request):
        """
        Convert amount between currencies with live rates
        
        Query params:
        - from: Source currency code (default: USD)
        - to: Target currency code (default: NGN)
        - amount: Amount to convert (default: 1)
        
        Returns:
        {
            "success": true,
            "from_currency": "USD",
            "to_currency": "NGN",
            "from_amount": 30.0,
            "to_amount": 43112.33,
            "exchange_rate": 1437.0777,
            "last_updated": "2025-11-11T14:58:28Z",
            "cached": true
        }
        """
        from .services import ExchangeRateService
        from datetime import datetime
        
        # Get query parameters
        from_currency = request.query_params.get('from', 'USD').upper()
        to_currency = request.query_params.get('to', 'NGN').upper()
        
        try:
            amount = Decimal(request.query_params.get('amount', '1'))
        except (ValueError, InvalidOperation):
            return Response({
                'success': False,
                'error': 'Invalid amount value',
                'error_code': 'INVALID_AMOUNT'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate currencies
        if len(from_currency) != 3 or len(to_currency) != 3:
            return Response({
                'success': False,
                'error': 'Currency codes must be 3 characters (e.g., USD, NGN)',
                'error_code': 'INVALID_CURRENCY_CODE'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Same currency
        if from_currency == to_currency:
            return Response({
                'success': True,
                'from_currency': from_currency,
                'to_currency': to_currency,
                'from_amount': float(amount),
                'to_amount': float(amount),
                'exchange_rate': 1.0,
                'last_updated': datetime.utcnow().isoformat() + 'Z',
                'cached': False
            })
        
        try:
            # Use ExchangeRateService for conversion
            service = ExchangeRateService()
            converted_amount = service.convert_amount(
                amount=amount,
                from_currency=from_currency,
                to_currency=to_currency
            )
            
            if converted_amount is None:
                return Response({
                    'success': False,
                    'error': f'Exchange rate not available for {from_currency} → {to_currency}',
                    'error_code': 'RATE_NOT_AVAILABLE',
                    'fallback': 'Please use USD for pricing'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
            # Get the rate for response
            rate = service.get_rate(from_currency, to_currency)
            
            # Get the ExchangeRate model to check cache age
            from .models import ExchangeRate
            rate_obj = ExchangeRate.objects.filter(
                base_currency=from_currency,
                target_currency=to_currency
            ).first()
            
            last_updated = rate_obj.last_updated if rate_obj else datetime.utcnow()
            
            return Response({
                'success': True,
                'from_currency': from_currency,
                'to_currency': to_currency,
                'from_amount': float(amount),
                'to_amount': float(converted_amount),
                'exchange_rate': float(rate) if rate else None,
                'last_updated': last_updated.isoformat(),
                'cached': rate_obj is not None
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Conversion failed: {str(e)}',
                'error_code': 'CONVERSION_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='rates')
    def rates(self, request):
        """
        Get all available exchange rates for a base currency
        
        Query params:
        - base: Base currency code (default: USD)
        
        Returns:
        {
            "success": true,
            "base_currency": "USD",
            "rates": {
                "NGN": 1437.0777,
                "EUR": 0.8649,
                "GBP": 0.7592,
                ...
            },
            "count": 164,
            "last_updated": "2025-11-11T14:58:28Z"
        }
        """
        from .services import ExchangeRateService
        from .models import ExchangeRate
        from datetime import datetime
        
        base_currency = request.query_params.get('base', 'USD').upper()
        
        # Validate base currency
        if len(base_currency) != 3:
            return Response({
                'success': False,
                'error': 'Currency code must be 3 characters (e.g., USD)',
                'error_code': 'INVALID_CURRENCY_CODE'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get rates from database
            rate_objects = ExchangeRate.objects.filter(base_currency=base_currency)
            
            if not rate_objects.exists():
                # No rates in cache, fetch from API
                service = ExchangeRateService()
                rates_dict = service.fetch_rates_from_exchangerate_api(base_currency)
                
                # Update database
                service.bulk_update_rates(base_currency, rates_dict)
                
                # Re-fetch from database
                rate_objects = ExchangeRate.objects.filter(base_currency=base_currency)
            
            # Build rates dictionary
            rates = {}
            latest_update = None
            for rate_obj in rate_objects:
                rates[rate_obj.target_currency] = float(rate_obj.rate)
                if latest_update is None or rate_obj.last_updated > latest_update:
                    latest_update = rate_obj.last_updated
            
            return Response({
                'success': True,
                'base_currency': base_currency,
                'rates': rates,
                'count': len(rates),
                'last_updated': latest_update.isoformat() if latest_update else datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Failed to fetch rates: {str(e)}',
                'error_code': 'FETCH_RATES_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
