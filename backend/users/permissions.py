"""Standard DRF permission classes for role-based access control"""
from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """
    Permission class that allows only admin users (is_staff=True).
    Use this for admin-only endpoints.
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
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_superuser
        )


class IsOwnerOrAdmin(BasePermission):
    """
    Permission class that allows object owners or admin users.
    Useful for endpoints where users can access their own data, or admins can access all.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin users have full access
        if request.user.is_staff:
            return True
        
        # Check if object has 'user' attribute and matches request user
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # Check if object itself is a user
        if hasattr(obj, 'id') and obj.id == request.user.id:
            return True
        
        return False
