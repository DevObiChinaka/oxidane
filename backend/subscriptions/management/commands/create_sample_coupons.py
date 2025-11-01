# Django management command to create sample coupon codes
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from subscriptions.models import Coupon, SubscriptionPlan
from decimal import Decimal

class Command(BaseCommand):
    help = 'Create sample coupon codes for testing the coupon system'
    
    def handle(self, *args, **options):
        """Create sample coupon codes"""
        
        coupon_codes = [
            # Welcome discount for new users
            {
                'code': 'WELCOME10',
                'description': 'Special 10% discount for first-time users',
                'discount_type': 'percentage',
                'discount_value': Decimal('10.00'),
                'max_uses': 100,
                'max_uses_per_user': 1,
                'valid_from': timezone.now(),
                'valid_until': timezone.now() + timedelta(days=30),
                'is_active': True,
            },
            
            # VIP specific discount
            {
                'code': 'VIP25',
                'description': '25% off all VIP plans - Limited time!',
                'discount_type': 'percentage',
                'discount_value': Decimal('25.00'),
                'max_uses': 50,
                'max_uses_per_user': 1,
                'valid_from': timezone.now(),
                'valid_until': timezone.now() + timedelta(days=7),
                'is_active': True,
            },
            
            # Signals discount
            {
                'code': 'SIGNALS15',
                'description': '15% off all signal plans',
                'discount_type': 'percentage',
                'discount_value': Decimal('15.00'),
                'max_uses': None,  # Unlimited
                'max_uses_per_user': 1,
                'valid_from': timezone.now(),
                'valid_until': timezone.now() + timedelta(days=14),
                'is_active': True,
            },
            
            # Fixed amount discount
            {
                'code': 'SAVE50',
                'description': 'Get $50 off any yearly plan',
                'discount_type': 'fixed',
                'discount_value': Decimal('50.00'),
                'max_uses': 25,
                'max_uses_per_user': 1,
                'valid_from': timezone.now(),
                'valid_until': timezone.now() + timedelta(days=21),
                'is_active': True,
            },
            
            # Black Friday style discount
            {
                'code': 'BLACKFRIDAY',
                'description': 'Huge 40% discount on everything! Limited time only.',
                'discount_type': 'percentage',
                'discount_value': Decimal('40.00'),
                'max_uses': 200,
                'max_uses_per_user': 1,
                'valid_from': timezone.now(),
                'valid_until': timezone.now() + timedelta(days=3),
                'is_active': False,  # Disabled by default
            },
            
            # Student discount
            {
                'code': 'STUDENT20',
                'description': '20% student discount with valid ID',
                'discount_type': 'percentage',
                'discount_value': Decimal('20.00'),
                'max_uses': None,  # Unlimited
                'max_uses_per_user': 3,  # Can use multiple times
                'valid_from': timezone.now(),
                'valid_until': timezone.now() + timedelta(days=365),  # Valid for 1 year
                'is_active': True,
            }
        ]
        
        try:
            with transaction.atomic():
                created_count = 0
                
                for coupon_data in coupon_codes:
                    coupon, created = Coupon.objects.get_or_create(
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
        
        coupons = Coupon.objects.all().order_by('-created_at')
        
        for coupon in coupons:
            status = '🟢 ACTIVE' if coupon.is_active else '🔴 INACTIVE'
            
            # Usage info
            if coupon.max_uses:
                usage_info = f'{coupon.current_uses}/{coupon.max_uses} used'
            else:
                usage_info = f'{coupon.current_uses} used (unlimited)'
            
            # Validity
            if coupon.valid_until:
                days_left = (coupon.valid_until - timezone.now()).days
                if days_left > 0:
                    validity = f'⏰ {days_left} days left'
                else:
                    validity = '⏰ EXPIRED'
            else:
                validity = '⏰ No expiration'
            
            self.stdout.write(f'\n📋 {coupon.code}')
            self.stdout.write(f'   💰 {coupon.get_discount_display()}')
            self.stdout.write(f'   📊 {status}')
            self.stdout.write(f'   📈 {usage_info}')
            self.stdout.write(f'   ⏰ {validity}')
            
            # Show applicable plans
            plan_count = coupon.plans.count()
            if plan_count > 0:
                self.stdout.write(f'   🎯 Applies to {plan_count} specific plan(s)')
            else:
                self.stdout.write(f'   🎯 Applies to all plans')
        
        # Show totals
        total_coupons = Coupon.objects.count()
        active_coupons = Coupon.objects.filter(is_active=True).count()
        
        self.stdout.write(f'\n📈 Statistics:')
        self.stdout.write(f'   Total Coupons: {total_coupons}')
        self.stdout.write(f'   Active Coupons: {active_coupons}')
        
        self.stdout.write(self.style.SUCCESS('\n✅ Coupon codes ready for use!'))
        self.stdout.write('💡 Usage examples:')
        self.stdout.write('   • WELCOME10: 10% off for new users')
        self.stdout.write('   • VIP25: 25% off VIP plans (7 days)')
        self.stdout.write('   • SAVE50: $50 off yearly plans')
        self.stdout.write('   • STUDENT20: 20% student discount')
        self.stdout.write('\n🔧 Admin panel: /admin/subscriptions/Coupon/')
