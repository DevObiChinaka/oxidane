# Django management command to create initial pricing plans
from django.core.management.base import BaseCommand
from django.db import transaction
from subscriptions.models import PricingPlan
from decimal import Decimal

class Command(BaseCommand):
    help = 'Create initial pricing plans for OxiWorld'
    
    def handle(self, *args, **options):
        """Create the initial pricing plans"""
        
        pricing_plans = [
            # Mentorship Plans
            {
                'plan_type': 'mentorship_basic',
                'plan_category': 'mentorship',
                'billing_cycle': 'one_time',
                'name': 'Basic Mentorship',
                'description': 'Complete forex education and mentorship program. One-time access to all educational content, trading psychology, market analysis, and community discussions.',
                'price': Decimal('135.00'),
                'currency': 'USD',
                'telegram_groups': ['mentorship'],
                'features_list': [
                    'Complete forex education curriculum',
                    'Trading psychology guidance',
                    'Market analysis and insights',
                    'Access to mentorship community',
                    'Q&A sessions with experts',
                    'Lifetime access to content',
                    'Study materials and resources'
                ],
                'call_to_action': 'Start Learning',
                'is_active': True,
                'is_featured': False,
                'sort_order': 10
            },
            
            # Signals Plans
            {
                'plan_type': 'signals_weekly',
                'plan_category': 'signals',
                'billing_cycle': 'weekly',
                'name': 'Weekly Signals',
                'description': 'Get live trading signals for one week. Perfect for testing our signal quality and accuracy before committing to longer plans.',
                'price': Decimal('20.00'),
                'currency': 'USD',
                'telegram_groups': ['signals'],
                'features_list': [
                    'Live trading signals',
                    'Entry and exit points',
                    'Risk management guidance',
                    'Real-time market updates',
                    '7-day signal access',
                    'Performance tracking'
                ],
                'call_to_action': 'Try Signals',
                'is_active': True,
                'is_featured': False,
                'sort_order': 20
            },
            {
                'plan_type': 'signals_monthly',
                'plan_category': 'signals',
                'billing_cycle': 'monthly',
                'name': 'Monthly Signals',
                'description': 'Full month of premium trading signals. Most popular choice for consistent trading performance and steady profits.',
                'price': Decimal('50.00'),
                'currency': 'USD',
                'telegram_groups': ['signals'],
                'features_list': [
                    'Live trading signals',
                    'Entry and exit points',
                    'Risk management guidance',
                    'Real-time market updates',
                    '30-day signal access',
                    'Performance tracking',
                    'Priority support'
                ],
                'call_to_action': 'Get Signals',
                'is_active': True,
                'is_featured': True,  # Most popular
                'sort_order': 21
            },
            {
                'plan_type': 'signals_yearly',
                'plan_category': 'signals',
                'billing_cycle': 'yearly',
                'name': 'Yearly Signals',
                'description': 'Full year of premium trading signals. Best value - save $100 compared to monthly payments. Perfect for serious traders.',
                'price': Decimal('500.00'),
                'currency': 'USD',
                'telegram_groups': ['signals'],
                'features_list': [
                    'Live trading signals',
                    'Entry and exit points',
                    'Risk management guidance',
                    'Real-time market updates',
                    '365-day signal access',
                    'Performance tracking',
                    'Priority support',
                    'Save $100 vs monthly',
                    'Exclusive yearly bonuses'
                ],
                'call_to_action': 'Save Big',
                'is_active': True,
                'is_featured': False,
                'sort_order': 22
            },
            
            # VIP Plans
            {
                'plan_type': 'vip_weekly',
                'plan_category': 'vip',
                'billing_cycle': 'weekly',
                'name': 'Weekly VIP',
                'description': 'Premium VIP experience for one week. Access to everything - signals, education, and exclusive VIP community with direct analyst access.',
                'price': Decimal('35.00'),
                'currency': 'USD',
                'telegram_groups': ['mentorship', 'signals', 'vip'],
                'features_list': [
                    'All signal features',
                    'Complete mentorship access',
                    'VIP community access',
                    'Direct analyst communication',
                    'Premium strategies',
                    'Advanced market analysis',
                    'Priority support',
                    '7-day full access'
                ],
                'call_to_action': 'Go VIP',
                'is_active': True,
                'is_featured': False,
                'sort_order': 30
            },
            {
                'plan_type': 'vip_monthly',
                'plan_category': 'vip',
                'billing_cycle': 'monthly',
                'name': 'Monthly VIP',
                'description': 'Full VIP experience for one month. Everything included - the ultimate trading package for serious forex traders who want it all.',
                'price': Decimal('100.00'),
                'currency': 'USD',
                'telegram_groups': ['mentorship', 'signals', 'vip'],
                'features_list': [
                    'All signal features',
                    'Complete mentorship access',
                    'VIP community access',
                    'Direct analyst communication',
                    'Premium strategies',
                    'Advanced market analysis',
                    'Exclusive webinars',
                    '1-on-1 support sessions',
                    '30-day full access'
                ],
                'call_to_action': 'Full Access',
                'is_active': True,
                'is_featured': True,  # Premium option
                'sort_order': 31
            },
            {
                'plan_type': 'vip_yearly',
                'plan_category': 'vip',
                'billing_cycle': 'yearly',
                'name': 'Yearly VIP',
                'description': 'Ultimate VIP package for a full year. Everything included plus exclusive yearly bonuses. Save $300 - the best deal for committed traders.',
                'price': Decimal('900.00'),
                'currency': 'USD',
                'telegram_groups': ['mentorship', 'signals', 'vip'],
                'features_list': [
                    'All signal features',
                    'Complete mentorship access',
                    'VIP community access',
                    'Direct analyst communication',
                    'Premium strategies',
                    'Advanced market analysis',
                    'Exclusive webinars',
                    '1-on-1 support sessions',
                    '365-day full access',
                    'Save $300 vs monthly',
                    'Exclusive yearly bonuses',
                    'Personal account manager'
                ],
                'call_to_action': 'Ultimate Deal',
                'is_active': True,
                'is_featured': False,
                'sort_order': 32
            }
        ]
        
        try:
            with transaction.atomic():
                # Clear existing plans (be careful in production!)
                if self.confirm_reset():
                    PricingPlan.objects.all().delete()
                    self.stdout.write(self.style.WARNING('Deleted existing pricing plans'))
                
                # Create new plans
                created_count = 0
                for plan_data in pricing_plans:
                    plan, created = PricingPlan.objects.get_or_create(
                        plan_type=plan_data['plan_type'],
                        defaults=plan_data
                    )
                    
                    if created:
                        created_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'✓ Created: {plan.name} - ${plan.price}')
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'⚠ Already exists: {plan.name}')
                        )
                
                self.stdout.write(
                    self.style.SUCCESS(f'\n🎉 Successfully created {created_count} pricing plans!')
                )
                
                # Show summary
                self.show_summary()
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error creating pricing plans: {e}')
            )
            raise
    
    def confirm_reset(self):
        """Ask for confirmation before deleting existing plans"""
        existing_count = PricingPlan.objects.count()
        if existing_count > 0:
            confirm = input(f'\n⚠️  Found {existing_count} existing pricing plans. Delete them? (y/N): ')
            return confirm.lower() == 'y'
        return True
    
    def show_summary(self):
        """Show summary of created plans"""
        self.stdout.write(self.style.SUCCESS('\n📊 Pricing Plan Summary:'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
        
        categories = PricingPlan.objects.values_list('plan_category', flat=True).distinct()
        
        for category in categories:
            plans = PricingPlan.objects.filter(plan_category=category).order_by('sort_order')
            self.stdout.write(f'\n🎯 {category.upper()} Plans:')
            
            for plan in plans:
                status = '🟢' if plan.is_active else '🔴'
                featured = '⭐' if plan.is_featured else '  '
                
                self.stdout.write(
                    f'  {status}{featured} {plan.name:<20} ${plan.price:>6} ({plan.billing_cycle})'
                )
        
        # Show totals
        total_plans = PricingPlan.objects.count()
        active_plans = PricingPlan.objects.filter(is_active=True).count()
        featured_plans = PricingPlan.objects.filter(is_featured=True).count()
        
        self.stdout.write(f'\n📈 Statistics:')
        self.stdout.write(f'   Total Plans: {total_plans}')
        self.stdout.write(f'   Active Plans: {active_plans}')
        self.stdout.write(f'   Featured Plans: {featured_plans}')
        
        self.stdout.write(self.style.SUCCESS('\n✅ Pricing plans ready for use!'))
        self.stdout.write('💡 Next steps:')
        self.stdout.write('   1. Check admin panel: /admin/subscriptions/pricingplan/')
        self.stdout.write('   2. Create coupon codes if needed')
        self.stdout.write('   3. Update bot pricing detection')
        self.stdout.write('   4. Test checkout process')