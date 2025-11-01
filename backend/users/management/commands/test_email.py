from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings

class Command(BaseCommand):
    help = 'Send a test email to verify email configuration'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email address to send test email to')

    def handle(self, *args, **options):
        email = options['email']
        
        try:
            send_mail(
                subject='Test Email from OxY Fx',
                message='''
Hello!

This is a test email from your OxY Fx Django backend.

If you received this email, your email configuration is working correctly!

Best regards,
The OxY Fx Team
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Test email sent successfully to {email}!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to send email: {str(e)}')
            )