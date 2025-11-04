"""
Management command to update exchange rates from external API.

Usage:
    python manage.py update_exchange_rates
    python manage.py update_exchange_rates --base EUR
    python manage.py update_exchange_rates --force
    python manage.py update_exchange_rates --use-fixer --api-key YOUR_KEY
    python manage.py update_exchange_rates --stats
"""

from django.core.management.base import BaseCommand, CommandError
from subscriptions.services import ExchangeRateService


class Command(BaseCommand):
    help = 'Update exchange rates from external API'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--base',
            type=str,
            default='USD',
            help='Base currency for fetching rates (default: USD)'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update even if rates are not stale'
        )
        
        parser.add_argument(
            '--use-fixer',
            action='store_true',
            help='Use fixer.io API instead of exchangerate-api.io'
        )
        
        parser.add_argument(
            '--api-key',
            type=str,
            help='API key for fixer.io (required if using fixer)'
        )
        
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Display statistics about stored exchange rates'
        )
    
    def handle(self, *args, **options):
        base_currency = options['base'].upper()
        force_update = options['force']
        use_fixer = options['use_fixer']
        api_key = options.get('api_key')
        show_stats = options['stats']
        
        service = ExchangeRateService(base_currency=base_currency)
        
        # Display statistics if requested
        if show_stats:
            self.display_statistics(service)
            return
        
        # Validate API key if using fixer
        if use_fixer and not api_key:
            raise CommandError(
                "API key is required when using fixer.io. "
                "Use --api-key YOUR_KEY or set FIXER_API_KEY in settings."
            )
        
        # Check if update is needed
        if not force_update and not service.needs_update():
            self.stdout.write(
                self.style.SUCCESS(
                    f'Exchange rates for {base_currency} are up to date. '
                    f'Use --force to update anyway.'
                )
            )
            self.display_statistics(service)
            return
        
        # Fetch and update rates
        self.stdout.write(
            f'Fetching exchange rates for {base_currency} from '
            f'{"fixer.io" if use_fixer else "exchangerate-api.io"}...'
        )
        
        try:
            success = service.fetch_and_update_rates(
                base_currency=base_currency,
                use_fixer=use_fixer,
                api_key=api_key,
                force_update=force_update
            )
            
            if success:
                rates = service.get_current_rates(base_currency)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Successfully updated {len(rates)} exchange rates for {base_currency}'
                    )
                )
                
                # Display sample rates
                self.stdout.write('\nSample rates:')
                sample_currencies = ['EUR', 'GBP', 'JPY', 'CAD', 'NGN']
                for currency in sample_currencies:
                    if currency in rates:
                        self.stdout.write(
                            f'  {base_currency}/{currency}: {rates[currency]}'
                        )
                
                self.display_statistics(service)
            else:
                raise CommandError('Failed to update exchange rates')
        
        except Exception as e:
            raise CommandError(f'Error updating exchange rates: {e}')
    
    def display_statistics(self, service):
        """Display statistics about stored exchange rates"""
        stats = service.get_statistics()
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write('EXCHANGE RATE STATISTICS')
        self.stdout.write('='*60)
        
        self.stdout.write(f'Total rates stored: {stats["total_rates"]}')
        
        if stats['total_rates'] > 0:
            self.stdout.write(
                f'Base currencies: {", ".join(stats["base_currencies"])}'
            )
            self.stdout.write(
                f'Target currencies: {len(stats["target_currencies"])} currencies'
            )
            self.stdout.write(
                f'Total supported currencies: {len(stats["supported_currencies"])}'
            )
            
            if stats['oldest_rate']:
                age_hours = stats['oldest_rate']['age'].total_seconds() / 3600
                self.stdout.write(
                    f'Oldest rate: {stats["oldest_rate"]["pair"]} '
                    f'({age_hours:.1f} hours old)'
                )
            
            if stats['newest_rate']:
                age_hours = stats['newest_rate']['age'].total_seconds() / 3600
                self.stdout.write(
                    f'Newest rate: {stats["newest_rate"]["pair"]} '
                    f'({age_hours:.1f} hours old)'
                )
            
            stale_count = stats['stale_rates_count']
            if stale_count > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f'\n⚠ {stale_count} stale rate(s) detected (>24 hours old)'
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('\n✓ All rates are fresh (<24 hours old)')
                )
        
        self.stdout.write('='*60 + '\n')
