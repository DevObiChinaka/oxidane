from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from .models import PricingPlan, Coupon, SignalSubscription
from .pricing_serializers import (
    PricingPlanSerializer, CouponSerializer,
    PricingAnalyticsSerializer, CouponValidationSerializer
)
from users.permissions import IsAdmin


class PricingPlanViewSet(viewsets.ModelViewSet):
    """ViewSet for managing pricing plans"""
    serializer_class = PricingPlanSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def get_queryset(self):
        """Filter pricing plans based on query params"""
        queryset = PricingPlan.objects.all().order_by('sort_order', 'created_at')
        
        # Admin-only access for full CRUD - check if user is authenticated and admin
        if not (self.request.user and self.request.user.is_authenticated and self.request.user.is_staff):
            queryset = queryset.filter(is_active=True)
        
        # Filter by category
        category = self.request.query_params.get('plan_category')
        if category:
            queryset = queryset.filter(plan_category=category)
        
        # Filter by billing cycle
        billing_cycle = self.request.query_params.get('billing_cycle')
        if billing_cycle:
            queryset = queryset.filter(billing_cycle=billing_cycle)
        
        # Filter active only
        active_only = self.request.query_params.get('active_only')
        if active_only and active_only.lower() == 'true':
            queryset = queryset.filter(is_active=True)
            
        return queryset

    def perform_create(self, serializer):
        """Set created_by when creating a plan"""
        serializer.save()

    def perform_update(self, serializer):
        """Handle plan updates"""
        serializer.save()

    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get all plan categories with their plans"""
        categories = {}
        plans = self.get_queryset()
        
        for plan in plans:
            category = plan.plan_category
            if category not in categories:
                categories[category] = []
            categories[category].append(PricingPlanSerializer(plan, context={'request': request}).data)
        
        return Response(categories)

    @action(detail=False, methods=['get'], permission_classes=[])
    def public(self, request):
        """Public endpoint for pricing (no authentication required)"""
        
        queryset = PricingPlan.objects.filter(is_active=True).order_by('sort_order')
        
        # Filter by category if specified
        category = request.query_params.get('plan_category')
        if category:
            queryset = queryset.filter(plan_category=category)
        
        serializer = PricingPlanSerializer(queryset, many=True, context={'request': request})
        
        return Response({
            'plans': serializer.data,
            'categories': {
                'signals': [p for p in serializer.data if p['plan_category'] == 'signals'],
                'mentorship': [p for p in serializer.data if p['plan_category'] == 'mentorship'],
                'vip': [p for p in serializer.data if p['plan_category'] == 'vip'],
            }
        })

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle plan active status"""
        plan = self.get_object()
        plan.is_active = not plan.is_active
        plan.save()
        
        return Response({
            'success': True,
            'is_active': plan.is_active,
            'message': f'Plan {"activated" if plan.is_active else "deactivated"} successfully'
        })

    @action(detail=True, methods=['post'])
    def toggle_featured(self, request, pk=None):
        """Toggle plan featured status"""
        plan = self.get_object()
        plan.is_featured = not plan.is_featured
        plan.save()
        
        return Response({
            'success': True,
            'is_featured': plan.is_featured,
            'message': f'Plan {"featured" if plan.is_featured else "unfeatured"} successfully'
        })


class CouponViewSet(viewsets.ModelViewSet):
    """ViewSet for managing coupon codes"""
    serializer_class = CouponSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def get_queryset(self):
        """Filter coupon codes based on query params"""
        queryset = Coupon.objects.all().order_by('-created_at')
        
        # Admin-only access - check if user is authenticated and admin
        if not (self.request.user and self.request.user.is_authenticated and self.request.user.is_staff):
            return Coupon.objects.none()
        
        # Filter by active status
        active_only = self.request.query_params.get('active_only')
        if active_only and active_only.lower() == 'true':
            queryset = queryset.filter(is_active=True)
        
        # Filter by validity
        valid_only = self.request.query_params.get('valid_only')
        if valid_only and valid_only.lower() == 'true':
            now = timezone.now()
            queryset = queryset.filter(
                is_active=True,
                valid_from__lte=now,
                valid_until__gte=now
            )
        
        # Search by code
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) | Q(description__icontains=search)
            )
            
        return queryset

    @action(detail=False, methods=['post'])
    def validate_coupon(self, request):
        """Validate a coupon code for checkout"""
        serializer = CouponValidationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        code = serializer.validated_data['code']
        plan_id = serializer.validated_data['plan_id']
        amount = serializer.validated_data['amount']
        
        try:
            # Get the coupon
            coupon = Coupon.objects.get(code=code, is_active=True)
            
            # Check validity period
            now = timezone.now()
            if now < coupon.valid_from or now > coupon.valid_until:
                return Response({
                    'valid': False,
                    'error': 'Coupon has expired or is not yet active'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check usage limits
            if coupon.usage_limit and coupon.usage_count >= coupon.usage_limit:
                return Response({
                    'valid': False,
                    'error': 'Coupon usage limit reached'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check minimum amount
            if coupon.minimum_amount and amount < coupon.minimum_amount:
                return Response({
                    'valid': False,
                    'error': f'Minimum order amount is ${coupon.minimum_amount}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check applicable plans
            if coupon.applicable_plans:
                try:
                    plan = PricingPlan.objects.get(id=plan_id)
                    if plan.id not in coupon.applicable_plans:
                        return Response({
                            'valid': False,
                            'error': 'Coupon not applicable to this plan'
                        }, status=status.HTTP_400_BAD_REQUEST)
                except PricingPlan.DoesNotExist:
                    return Response({
                        'valid': False,
                        'error': 'Invalid plan'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Calculate discount
            if coupon.discount_type == 'percentage':
                discount_amount = (amount * coupon.discount_value) / 100
            else:  # fixed_amount
                discount_amount = min(coupon.discount_value, amount)
            
            final_amount = max(amount - discount_amount, 0)
            
            return Response({
                'valid': True,
                'discount_amount': discount_amount,
                'final_amount': final_amount,
                'original_amount': amount,
                'message': f'{coupon.discount_value}{"%" if coupon.discount_type == "percentage" else "$"} discount applied',
                'coupon': {
                    'code': coupon.code,
                    'description': coupon.description,
                    'discount_type': coupon.discount_type,
                    'discount_value': coupon.discount_value
                }
            })
            
        except Coupon.DoesNotExist:
            return Response({
                'valid': False,
                'error': 'Invalid coupon code'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle coupon active status"""
        coupon = self.get_object()
        coupon.is_active = not coupon.is_active
        coupon.save()
        
        return Response({
            'success': True,
            'is_active': coupon.is_active,
            'message': f'Coupon {"activated" if coupon.is_active else "deactivated"} successfully'
        })

    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """Get coupon analytics"""
        # Get date range
        days_back = int(request.query_params.get('days_back', 30))
        start_date = timezone.now() - timedelta(days=days_back)
        
        # Basic stats
        total_coupons = Coupon.objects.count()
        active_coupons = Coupon.objects.filter(is_active=True).count()
        
        # Get coupons created/used in date range
        recent_coupons = Coupon.objects.filter(created_at__gte=start_date)
        total_usage = sum(c.current_uses for c in recent_coupons)
        
        # Top performing coupons (by usage)
        top_coupons = Coupon.objects.filter(current_uses__gt=0).order_by('-current_uses')[:10]
        
        return Response({
            'total_coupons': total_coupons,
            'active_coupons': active_coupons,
            'total_usage': total_usage,
            'top_coupons': [{
                'code': coupon.code,
                'description': coupon.description or '',
                'usage_count': coupon.current_uses,
                'discount_type': coupon.discount_type,
                'discount_value': float(coupon.discount_value)
            } for coupon in top_coupons]
        })


