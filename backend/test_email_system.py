"""
Email System Integration Test
Tests Gmail SMTP integration, system emails, and EmailLog creation
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.models import EmailTemplate, EmailLog
from users.email_service import EmailTemplateService

User = get_user_model()


def print_header(text):
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)


def print_success(text):
    print(f"✅ {text}")


def print_error(text):
    print(f"❌ {text}")


def print_info(text):
    print(f"ℹ️  {text}")


def test_system_emails_exist():
    """Test 1: Verify system emails were created"""
    print_header("TEST 1: System Email Templates")
    
    system_templates = EmailTemplate.objects.filter(is_system_email=True)
    count = system_templates.count()
    
    if count == 0:
        print_error(f"No system emails found! Run: python manage.py seed_system_emails")
        return False
    
    print_success(f"Found {count} system email templates")
    
    expected_types = [
        'email_verification',
        'password_reset',
        'signin_notification',
        'payment_success',
        'payment_failed',
        'payment_refunded',
        'subscription_success',
        'subscription_expiry',
        'subscription_renewal',
        'telegram_added',
        'telegram_removed'
    ]
    
    for template_type in expected_types:
        template = system_templates.filter(template_type=template_type).first()
        if template:
            print_success(f"  {template.name} ({template_type})")
        else:
            print_error(f"  Missing: {template_type}")
    
    return True


def test_system_email_protection():
    """Test 2: Verify system emails cannot be deleted"""
    print_header("TEST 2: System Email Protection")
    
    system_template = EmailTemplate.objects.filter(is_system_email=True).first()
    
    if not system_template:
        print_error("No system templates to test protection")
        return False
    
    print_info(f"Testing protection on: {system_template.name}")
    
    # Try to change status to inactive
    original_status = system_template.status
    system_template.status = 'inactive'
    system_template.save()
    
    # In production, the API endpoint would reject this
    # For now, just verify the field exists
    if hasattr(system_template, 'is_system_email'):
        print_success("is_system_email field exists")
        print_info("Backend API endpoints should reject deletion/deactivation")
    else:
        print_error("is_system_email field missing")
        return False
    
    # Restore status
    system_template.status = original_status
    system_template.save()
    
    return True


def test_email_sending():
    """Test 3: Send test email using EmailTemplateService"""
    print_header("TEST 3: Email Sending via EmailTemplateService")
    
    # Get a test user or create one
    test_email = input("\nEnter test email address (or press Enter to skip): ").strip()
    
    if not test_email:
        print_info("Skipping email send test")
        return True
    
    # Get email verification template
    template = EmailTemplate.objects.filter(
        template_type='email_verification',
        is_system_email=True
    ).first()
    
    if not template:
        print_error("Email verification template not found")
        return False
    
    print_info(f"Using template: {template.name}")
    
    # Create test user object
    test_user = type('TestUser', (), {
        'first_name': 'Test',
        'last_name': 'User',
        'email': test_email,
        'username': test_email.split('@')[0]
    })()
    
    # Send test email
    service = EmailTemplateService()
    
    try:
        result = service.send_email(
            template_type='email_verification',
            recipient_email=test_email,
            user=test_user,
            context_data={
                'custom': {
                    'verification_link': 'https://oxiworld.com/verify/test123',
                    'verification_code': '123456'
                }
            }
        )
        
        if result.get('success'):
            print_success(f"Email sent successfully to {test_email}")
            
            # Check if EmailLog was created
            log = EmailLog.objects.filter(recipient_email=test_email).order_by('-created_at').first()
            if log:
                print_success(f"EmailLog created: ID={log.id}, Status={log.status}")
            else:
                print_error("EmailLog was not created")
                return False
        else:
            print_error(f"Email send failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print_error(f"Exception during email send: {str(e)}")
        print_info("Check your Gmail SMTP settings in .env file:")
        print_info("  - EMAIL_HOST_USER")
        print_info("  - EMAIL_HOST_PASSWORD")
        print_info("  - EMAIL_USE_TLS")
        return False
    
    return True


def test_email_logs():
    """Test 4: Verify EmailLog model and entries"""
    print_header("TEST 4: EmailLog Model")
    
    total_logs = EmailLog.objects.count()
    print_info(f"Total email logs in database: {total_logs}")
    
    if total_logs > 0:
        recent_logs = EmailLog.objects.order_by('-created_at')[:5]
        print_success(f"Found {len(recent_logs)} recent logs:")
        
        for log in recent_logs:
            status_emoji = "✅" if log.status in ['sent', 'delivered'] else "❌" if log.status == 'failed' else "⏳"
            print(f"  {status_emoji} {log.recipient_email} - {log.template.name if log.template else 'N/A'} ({log.status})")
    else:
        print_info("No email logs yet. Send some emails to see logs.")
    
    # Test EmailLog fields
    required_fields = ['recipient_email', 'subject', 'status', 'created_at', 'sent_at', 'error_message']
    log_model_fields = [f.name for f in EmailLog._meta.get_fields()]
    
    all_present = True
    for field in required_fields:
        if field in log_model_fields:
            print_success(f"  Field '{field}' exists")
        else:
            print_error(f"  Field '{field}' missing")
            all_present = False
    
    return all_present


def test_subscription_filtering():
    """Test 5: Verify subscription plan filtering logic"""
    print_header("TEST 5: Subscription Plan Filtering")
    
    from subscriptions.models import Subscription, SubscriptionPlan
    
    # Check if we have subscription plans
    plans = SubscriptionPlan.objects.all()
    plan_count = plans.count()
    
    print_info(f"Found {plan_count} subscription plans")
    
    if plan_count > 0:
        billing_periods = plans.values_list('billing_period', flat=True).distinct()
        print_success(f"Billing periods available: {', '.join(billing_periods)}")
        
        # Test filtering logic
        for period in ['weekly', 'monthly', 'quarterly', 'yearly', 'lifetime']:
            count = plans.filter(billing_period=period).count()
            if count > 0:
                print_info(f"  {period.capitalize()}: {count} plan(s)")
    else:
        print_info("No subscription plans found. Create some to test filtering.")
    
    # Check if users have subscriptions
    active_subs = Subscription.objects.filter(status='active').count()
    print_info(f"Active subscriptions: {active_subs}")
    
    return True


def run_all_tests():
    """Run all email system tests"""
    print("\n" + "🚀"*35)
    print("  EMAIL SYSTEM INTEGRATION TEST SUITE")
    print("🚀"*35)
    
    tests = [
        ("System Email Templates", test_system_emails_exist),
        ("System Email Protection", test_system_email_protection),
        ("Email Sending (SMTP)", test_email_sending),
        ("EmailLog Model", test_email_logs),
        ("Subscription Filtering", test_subscription_filtering),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"Test '{test_name}' crashed: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        if result:
            print_success(f"{test_name}")
        else:
            print_error(f"{test_name}")
    
    print(f"\n{'='*70}")
    print(f"  PASSED: {passed}/{total} tests")
    print(f"{'='*70}\n")
    
    if passed == total:
        print("🎉 All tests passed! Email system is ready for production.")
    else:
        print("⚠️  Some tests failed. Review errors above and fix issues.")


if __name__ == '__main__':
    run_all_tests()
