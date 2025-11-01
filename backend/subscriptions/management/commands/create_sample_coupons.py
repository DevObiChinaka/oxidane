# Django management command to create sample coupon codes
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from subscriptions.models import CouponCode, PricingPlan
from decimal import Decimal

class Command(BaseCommand):
    help = 'Create sample coupon codes for testing the coupon system'
    
    def handle(self, *args, **options):
        """Create sample coupon codes"""
        
        coupon_codes = [
            # Welcome discount for new users
            {
                'code': 'WELCOME10',
                'name': 'Welcome Discount',
                'description': 'Special 10% discount for first-time users',
                'discount_type': 'percentage',
                'discount_value': Decimal('10.00'),
                'minimum_amount': Decimal('0.00'),
                'usage_limit': 100,
                'usage_limit_per_user': 1,
                'valid_from': timezone.now(),
                'valid_until': timezone.now() + timedelta(days=30),
                'applicable_categories': ['mentorship', 'signals', 'vip'],
                'is_active': True,
                'first_time_users_only': True
            },
            
            # VIP specific discount
            {
                'code': 'VIP25',
                'name': 'VIP Flash Sale',
                'description': '25% off all VIP plans - Limited time!',
                'discount_type': 'percentage',
                'discount_value': Decimal('25.00'),
                'minimum_amount': Decimal('50.00'),
                'maximum_discount': Decimal('250.00'),
                'usage_limit': 50,
                'usage_limit_per_user': 1,
                'valid_from': timezone.now(),
                'valid_until': timezone.now() + timedelta(days=7),
                'applicable_categories': ['vip'],
                'is_active': True,
                'first_time_users_only': False
            },
            
            # Signals discount
            {
                'code': 'SIGNALS15',
                'name': 'Signals Special',
                'description': '15% off all signal plans',
                'discount_type': 'percentage',
                'discount_value': Decimal('15.00'),
                'minimum_amount': Decimal('20.00'),
                'usage_limit': None,  # Unlimited
                'usage_limit_per_user': 1,
                'valid_from': timezone.now(),
                'valid_until': timezone.now() + timedelta(days=14),
                'applicable_categories': ['signals'],
                'is_active': True,
                'first_time_users_only': False
            },
            
            # Fixed amount discount
            {
                'code': 'SAVE50',
                'name': 'Save $50',
                'description': 'Get $50 off any yearly plan',
                'discount_type': 'fixed_amount',
                'discount_value': Decimal('50.00'),
                'minimum_amount': Decimal('200.00'),
                'usage_limit': 25,
                'usage_limit_per_user': 1,
                'valid_from': timezone.now(),
                'valid_until': timezone.now() + timedelta(days=21),
                'applicable_categories': ['signals', 'vip'],
                'is_active': True,
                'first_time_users_only': False
            },
            
            # Black Friday style discount
            {
                'code': 'BLACKFRIDAY',
                'name': 'Black Friday Mega Sale',
                'description': 'Huge 40% discount on everything! Limited time only.',
                'discount_type': 'percentage',
                'discount_value': Decimal('40.00'),
                'minimum_amount': Decimal('20.00'),
                'maximum_discount': Decimal('400.00'),
                'usage_limit': 200,
                'usage_limit_per_user': 1,
                'valid_from': timezone.now(),
                'valid_until': timezone.now() + timedelta(days=3),
                'applicable_categories': ['mentorship', 'signals', 'vip'],
                'is_active': False,  # Disabled by default
                'first_time_users_only': False
            },
            
            # Student discount
            {
                'code': 'STUDENT20',
                'name': 'Student Discount',
                'description': '20% student discount with valid ID',
                'discount_type': 'percentage',
                'discount_value': Decimal('20.00'),
                'minimum_amount': Decimal('0.00'),
                'usage_limit': None,  # Unlimited
                'usage_limit_per_user': 3,  # Can use multiple times
                'valid_from': timezone.now(),
                'valid_until': timezone.now() + timedelta(days=365),  # Valid for 1 year
                'applicable_categories': ['mentorship', 'signals'],  # Exclude VIP
                'is_active': True,
                'first_time_users_only': False
            }
        ]
        
        try:
            with transaction.atomic():
                created_count = 0
                
                for coupon_data in coupon_codes:
                    coupon, created = CouponCode.objects.get_or_create(
                        code=coupon_data['code'],
                        defaults=coupon_data
                    )
                    
                    if created:
                        created_count += 1
                        status = '🟢' if coupon.is_active else '🔴'
                        self.stdout.write(
                            self.style.SUCCESS(f'{status} Created: {coupon.code} - {coupon.get_discount_display()}')
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'⚠ Already exists: {coupon.code}')
                        )
                
                self.stdout.write(
                    self.style.SUCCESS(f'\n🎉 Successfully created {created_count} coupon codes!')
                )
                
                # Show summary
                self.show_summary()
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error creating coupon codes: {e}')
            )
            raise
    
    def show_summary(self):
        """Show summary of created coupons"""
        self.stdout.write(self.style.SUCCESS('\n🎫 Coupon Code Summary:'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        coupons = CouponCode.objects.all().order_by('-created_at')
        
        for coupon in coupons:
            status = '🟢 ACTIVE' if coupon.is_active else '🔴 INACTIVE'
            first_time = '👶 New Users Only' if coupon.first_time_users_only else '👥 All Users'
            
            # Usage info
            if coupon.usage_limit:
                usage_info = f'{coupon.usage_count}/{coupon.usage_limit} used'
            else:
                usage_info = f'{coupon.usage_count} used (unlimited)'
            
            # Validity
            days_left = (coupon.valid_until - timezone.now()).days
            if days_left > 0:
                validity = f'⏰ {days_left} days left'
            else:
                validity = '⏰ EXPIRED'
            
            self.stdout.write(f'\n📋 {coupon.code}')
            self.stdout.write(f'   💰 {coupon.get_discount_display()}')
            self.stdout.write(f'   📊 {status}')
            self.stdout.write(f'   👥 {first_time}')
            self.stdout.write(f'   📈 {usage_info}')
            self.stdout.write(f'   ⏰ {validity}')
            
            if coupon.applicable_categories:
                categories = ', '.join(coupon.applicable_categories)
                self.stdout.write(f'   🎯 Categories: {categories}')
        
        # Show totals
        total_coupons = CouponCode.objects.count()
        active_coupons = CouponCode.objects.filter(is_active=True).count()
        
        self.stdout.write(f'\n📈 Statistics:')
        self.stdout.write(f'   Total Coupons: {total_coupons}')
        self.stdout.write(f'   Active Coupons: {active_coupons}')
        
        self.stdout.write(self.style.SUCCESS('\n✅ Coupon codes ready for use!'))
        self.stdout.write('💡 Usage examples:')
        self.stdout.write('   • WELCOME10: 10% off for new users')
        self.stdout.write('   • VIP25: 25% off VIP plans (7 days)')
        self.stdout.write('   • SAVE50: $50 off yearly plans')
        self.stdout.write('   • STUDENT20: 20% student discount')
        self.stdout.write('\n🔧 Admin panel: /admin/subscriptions/couponcode/')