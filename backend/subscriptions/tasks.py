"""
Celery Tasks for Subscription Management
Handles async operations for payments, subscriptions, Telegram, and emails

Created: November 10, 2025
"""

import logging
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from celery import shared_task
import requests

from .models import (
    Payment, Subscription, SubscriptionPlan, User,
    TelegramGroup, TelegramConfiguration, EmailConfiguration,
    ExchangeRate, BillingProfile
)

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def activate_subscription(self, payment_id):
    """
    Activate subscription after successful payment
    
    Args:
        payment_id: ID of the successful payment
        
    Actions:
        1. Get payment and plan details
        2. Create or update subscription
        3. Update user subscription fields
        4. Set subscription dates based on billing period
        5. Log activation
        
    Retries: 3 times with 60-second delay
    """
    try:
        logger.info(f"Activating subscription for payment {payment_id}")
        
        # Get payment
        try:
            payment = Payment.objects.select_related(
                'billing_profile__user',
                'subscription__plan'
            ).get(id=payment_id)
        except Payment.DoesNotExist:
            logger.error(f"Payment {payment_id} not found")
            return {'success': False, 'error': 'Payment not found'}
        
        # Verify payment is successful
        if payment.status != 'success':
            logger.warning(f"Payment {payment_id} status is {payment.status}, not 'success'")
            return {'success': False, 'error': f'Payment status is {payment.status}'}
        
        # Get plan from metadata or subscription
        if payment.subscription and payment.subscription.plan:
            plan = payment.subscription.plan
        else:
            # Try to get from gateway_response (direct or nested in metadata)
            plan_id = payment.gateway_response.get('plan_id')
            if not plan_id:
                metadata = payment.gateway_response.get('metadata', {})
                plan_id = metadata.get('plan_id')
            
            if not plan_id:
                logger.error(f"No plan_id found for payment {payment_id}")
                return {'success': False, 'error': 'No plan associated with payment'}
            
            try:
                plan = SubscriptionPlan.objects.get(id=plan_id)
            except SubscriptionPlan.DoesNotExist:
                logger.error(f"Plan {plan_id} not found")
                return {'success': False, 'error': 'Plan not found'}
        
        user = payment.billing_profile.user
        
        # Calculate subscription dates based on billing period
        start_date = timezone.now()
        
        if plan.billing_period == 'weekly':
            end_date = start_date + timedelta(days=7)
        elif plan.billing_period == 'monthly':
            end_date = start_date + timedelta(days=30)
        elif plan.billing_period == 'quarterly':
            end_date = start_date + timedelta(days=90)
        elif plan.billing_period == 'yearly':
            end_date = start_date + timedelta(days=365)
        elif plan.billing_period == 'lifetime':
            end_date = start_date + timedelta(days=365 * 100)  # 100 years
        else:
            end_date = start_date + timedelta(days=30)  # Default to monthly
        
        # Create or update subscription (get the active one or create new)
        subscription, created = Subscription.objects.update_or_create(
            billing_profile=payment.billing_profile,
            status='active',  # Only update active subscriptions
            defaults={
                'plan': plan,
                'start_date': start_date,
                'end_date': end_date,
                'amount_paid': payment.amount,
                'currency': payment.currency,
            }
        )
        
        # Link payment to subscription if not already linked
        if not payment.subscription:
            payment.subscription = subscription
            payment.save()
        
        # Update user subscription fields
        user.current_plan = plan
        user.subscription_status = 'active'
        user.subscription_start_date = start_date
        user.subscription_end_date = end_date
        user.save()
        
        action = 'Created' if created else 'Updated'
        logger.info(f"{action} subscription {subscription.id} for user {user.id} with plan {plan.name}")
        
        return {
            'success': True,
            'subscription_id': str(subscription.id),
            'user_id': user.id,
            'plan_name': plan.name,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
        }
    
    except Exception as e:
        logger.error(f"Error activating subscription for payment {payment_id}: {str(e)}", exc_info=True)
        
        # Retry the task
        try:
            raise self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for activate_subscription (payment {payment_id})")
            return {'success': False, 'error': str(e)}


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def add_user_to_telegram_groups(self, user_id, plan_id):
    """
    Add user to Telegram groups based on subscription plan
    
    Args:
        user_id: ID of the user
        plan_id: ID of the subscription plan
        
    Actions:
        1. Get user's Telegram user ID from billing profile
        2. Get Telegram groups associated with the plan
        3. Add user to groups (method depends on group type)
        4. Send welcome message
        
    Note: User must have telegram_user_id in their billing profile
    
    Retries: 3 times with 60-second delay
    """
    try:
        logger.info(f"Adding user {user_id} to Telegram groups for plan {plan_id}")
        
        # Get user and plan
        try:
            user = User.objects.select_related('billing_profile').get(id=user_id)
            plan = SubscriptionPlan.objects.prefetch_related('telegram_groups').get(id=plan_id)
        except (User.DoesNotExist, SubscriptionPlan.DoesNotExist) as e:
            logger.error(f"User or plan not found: {str(e)}")
            return {'success': False, 'error': str(e)}
        
        # Check if user has Telegram connected
        billing_profile = user.billing_profile
        if not billing_profile.telegram_user_id:
            logger.warning(f"User {user.email} has no Telegram user ID. Username: {billing_profile.telegram_username or 'Not set'}")
            return {
                'success': False, 
                'error': 'No Telegram account linked',
                'message': 'Please link your Telegram account in your profile before subscribing'
            }
        
        # Get Telegram configuration
        try:
            telegram_config = TelegramConfiguration.get_instance()
            
            if not telegram_config.has_valid_token():
                logger.warning("Telegram bot token not configured or invalid")
                return {'success': False, 'error': 'Telegram not configured'}
            
            bot_token = telegram_config.bot_token
            
        except Exception as e:
            logger.error(f"Error getting Telegram configuration: {str(e)}")
            return {'success': False, 'error': 'Telegram configuration error'}
        
        # Get Telegram groups for this plan
        telegram_groups = plan.telegram_groups.filter(is_active=True)
        
        if not telegram_groups.exists():
            logger.info(f"No Telegram groups associated with plan {plan.name}")
            return {'success': True, 'message': 'No groups to add', 'groups_added': 0}
        
        # Add user to each group using appropriate method
        groups_added = []
        groups_failed = []
        
        for group in telegram_groups:
            try:
                # Try direct addition first (works for regular groups under 200 members)
                url = f"https://api.telegram.org/bot{bot_token}/addChatMember"
                payload = {
                    'chat_id': group.chat_id,
                    'user_id': int(billing_profile.telegram_user_id)
                }
                
                response = requests.post(url, json=payload, timeout=30)
                data = response.json()
                
                if data.get('ok'):
                    # Successfully added user directly to regular group!
                    groups_added.append(group.name)
                    logger.info(f"✅ DIRECT-ADD: User @{billing_profile.telegram_username} added to {group.name}")
                    
                    # Send confirmation message
                    message = f"🎉 You've been automatically added to *{group.name}*!\n\n"
                    message += f"Open Telegram to see your new group."
                    
                    send_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                    send_payload = {
                        'chat_id': int(billing_profile.telegram_user_id),
                        'text': message,
                        'parse_mode': 'Markdown'
                    }
                    
                    requests.post(send_url, json=send_payload, timeout=30)
                    logger.info(f"Sent confirmation for {group.name}")
                
                else:
                    error_desc = data.get('description', 'Unknown error')
                    
                    # Handle specific error cases
                    if 'USER_ALREADY_PARTICIPANT' in error_desc:
                        groups_added.append(group.name)
                        logger.info(f"User already in {group.name}")
                    
                    elif 'Not Found' in error_desc or 'CHAT_NOT_FOUND' in error_desc:
                        # This is a supergroup/channel - create secure single-use invite link
                        logger.info(f"{group.name} is a supergroup - creating single-use invite link")
                        
                        # Create a single-use invite link (expires in 1 hour, max 1 member)
                        # This link can only be used ONCE by ONE person, preventing sharing
                        import time
                        expire_timestamp = int(time.time()) + 3600  # 1 hour from now
                        
                        create_link_url = f"https://api.telegram.org/bot{bot_token}/createChatInviteLink"
                        create_link_payload = {
                            'chat_id': group.chat_id,
                            'member_limit': 1,  # Only 1 person can use this link (SECURITY)
                            'expire_date': expire_timestamp,  # Expires in 1 hour
                            'name': f"Access for @{billing_profile.telegram_username}"  # Track who it's for
                        }
                        
                        link_response = requests.post(create_link_url, json=create_link_payload, timeout=30)
                        link_data = link_response.json()
                        
                        if link_data.get('ok'):
                            group_link = link_data['result']['invite_link']
                            
                            # Send user a message with inline button to join directly
                            # Note: Escape special Markdown characters
                            username = billing_profile.telegram_username.replace('_', '\\_')
                            
                            message = f"🎉 *Welcome to {group.name}\\!*\n\n"
                            message += f"✅ Your exclusive access link is ready\\.\n\n"
                            message += f"Click the button below to join:\n\n"
                            message += f"🔒 *Security:* This link:\n"
                            message += f"   • Works only ONCE\n"
                            message += f"   • Only for YOU \\(@{username}\\)\n"
                            message += f"   • Expires in 1 hour\n"
                            message += f"   • Cannot be shared or reused"
                            
                            send_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                            send_payload = {
                                'chat_id': int(billing_profile.telegram_user_id),
                                'text': message,
                                'parse_mode': 'Markdown',
                                'reply_markup': {
                                    'inline_keyboard': [[
                                        {
                                            'text': '🚀 Join Group Now',
                                            'url': group_link
                                        }
                                    ]]
                                }
                            }
                            
                            send_response = requests.post(send_url, json=send_payload, timeout=30)
                            
                            if send_response.json().get('ok'):
                                groups_added.append(group.name)
                                logger.info(f"✅ Sent single-use invite link for {group.name} to @{billing_profile.telegram_username}")
                            else:
                                logger.error(f"Failed to send join link: {send_response.json().get('description')}")
                                groups_failed.append({
                                    'group': group.name,
                                    'error': 'Failed to send join request link'
                                })
                        else:
                            error_msg = link_data.get('description', 'Unknown error')
                            logger.error(f"Failed to create invite link for {group.name}: {error_msg}")
                            groups_failed.append({
                                'group': group.name,
                                'error': error_msg
                            })
                    
                    elif 'CHAT_ADMIN_REQUIRED' in error_desc:
                        groups_failed.append({
                            'group': group.name,
                            'error': 'Bot is not an administrator. Please make bot admin with "Add Members" permission.'
                        })
                        logger.error(f"❌ Bot not admin in {group.name}")
                    
                    elif 'USER_PRIVACY_RESTRICTED' in error_desc:
                        groups_failed.append({
                            'group': group.name,
                            'error': 'User privacy settings prevent auto-add. User must adjust privacy settings.'
                        })
                        logger.error(f"❌ Privacy restricted for {group.name}")
                    
                    else:
                        groups_failed.append({
                            'group': group.name,
                            'error': error_desc
                        })
                        logger.error(f"Failed to add user to {group.name}: {error_desc}")
            
            except Exception as e:
                groups_failed.append({
                    'group': group.name,
                    'error': str(e)
                })
                logger.error(f"Error adding user to {group.name}: {str(e)}")
                continue
        
        # Send welcome message if any groups were processed
        if groups_added:
            try:
                welcome_message = f"🎉 *Welcome to {plan.name}!*\n\n"
                welcome_message += f"You now have access to {len(groups_added)} Telegram group(s):\n\n"
                
                for group_name in groups_added:
                    welcome_message += f"✅ {group_name}\n"
                
                welcome_message += f"\n💡 _Check the messages above for join buttons._"
                
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                payload = {
                    'chat_id': int(billing_profile.telegram_user_id),
                    'text': welcome_message,
                    'parse_mode': 'Markdown'
                }
                
                requests.post(url, json=payload, timeout=30)
                logger.info(f"Sent welcome message to @{billing_profile.telegram_username}")
            
            except Exception as e:
                logger.error(f"Error sending welcome message: {str(e)}")
        
        return {
            'success': True,
            'user_id': user_id,
            'plan_name': plan.name,
            'groups_added': len(groups_added),
            'groups_failed': len(groups_failed),
            'group_names': groups_added,
            'telegram_username': billing_profile.telegram_username,
            'telegram_user_id': billing_profile.telegram_user_id,
            'failures': groups_failed if groups_failed else None
        }
    
    except Exception as e:
        logger.error(f"Error adding user {user_id} to Telegram groups: {str(e)}", exc_info=True)
        
        # Retry the task
        try:
            raise self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for add_user_to_telegram_groups (user {user_id})")
            return {'success': False, 'error': str(e)}


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_payment_receipt_email(self, payment_id):
    """
    Send payment receipt email to user
    
    Args:
        payment_id: ID of the successful payment
        
    Actions:
        1. Get payment details
        2. Render email template (payment_success.html)
        3. Send email via EmailConfiguration SMTP
        
    Retries: 3 times with 60-second delay
    """
    try:
        logger.info(f"Sending payment receipt email for payment {payment_id}")
        
        # Get payment
        try:
            payment = Payment.objects.select_related(
                'billing_profile__user',
                'subscription__plan'
            ).get(id=payment_id)
        except Payment.DoesNotExist:
            logger.error(f"Payment {payment_id} not found")
            return {'success': False, 'error': 'Payment not found'}
        
        # Verify payment is successful
        if payment.status != 'success':
            logger.warning(f"Payment {payment_id} status is {payment.status}, not 'success'")
            return {'success': False, 'error': f'Payment status is {payment.status}'}
        
        user = payment.billing_profile.user
        
        # Get email configuration
        try:
            email_config = EmailConfiguration.get_instance()
            
            if not email_config.is_configured():
                logger.warning("Email not configured, using Django default")
                from_email = settings.DEFAULT_FROM_EMAIL
            else:
                from_email = email_config.from_email
        
        except Exception as e:
            logger.warning(f"Error getting email configuration: {str(e)}, using default")
            from_email = settings.DEFAULT_FROM_EMAIL
        
        # Prepare email context
        context = {
            'user': user,
            'payment': payment,
            'plan': payment.subscription.plan if payment.subscription else None,
            'subscription': payment.subscription,
            'amount': payment.amount,
            'processing_fee': payment.processing_fee,
            'total_amount': payment.total_amount,
            'currency': payment.currency,
            'payment_date': payment.paid_at or payment.created_at,
            'reference': payment.gateway_reference,
            'invoice_number': f"INV-{str(payment.id)[:8].upper()}",  # Use first 8 chars of UUID
            'site_name': 'OxiWorld',
            'site_url': settings.FRONTEND_URL,
        }
        
        # Render email templates
        try:
            html_content = render_to_string('emails/payment_receipt.html', context)
            text_content = render_to_string('emails/payment_receipt.txt', context)
        except Exception as e:
            logger.warning(f"Email templates not found, using simple text: {str(e)}")
            
            # Fallback plain text email
            text_content = f"""
Payment Receipt - OxiWorld

Hi {user.first_name or user.email},

Thank you for your payment!

Payment Details:
- Amount: {payment.currency} {payment.amount}
- Processing Fee: {payment.currency} {payment.processing_fee}
- Total Paid: {payment.currency} {payment.total_amount}
- Reference: {payment.gateway_reference}
- Date: {payment.paid_at or payment.created_at}

Your subscription is now active. You can access your account at {settings.FRONTEND_URL}/dashboard

Thank you,
OxiWorld Team
            """.strip()
            html_content = None
        
        # Send email
        subject = f"Payment Receipt - {payment.currency} {payment.total_amount}"
        to_email = user.email
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=[to_email]
        )
        
        if html_content:
            email.attach_alternative(html_content, "text/html")
        
        email.send(fail_silently=False)
        
        logger.info(f"Payment receipt email sent to {to_email} for payment {payment_id}")
        
        return {
            'success': True,
            'payment_id': payment_id,
            'recipient': to_email,
            'subject': subject
        }
    
    except Exception as e:
        logger.error(f"Error sending payment receipt email for payment {payment_id}: {str(e)}", exc_info=True)
        
        # Retry the task
        try:
            raise self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for send_payment_receipt_email (payment {payment_id})")
            return {'success': False, 'error': str(e)}


# ============================================================================
# PERIODIC TASKS (Celery Beat)
# ============================================================================

@shared_task
def check_expired_subscriptions():
    """
    Check for expired subscriptions and deactivate them
    
    Runs: Daily at midnight (configured in celery.py)
    """
    logger.info("Checking for expired subscriptions")
    
    # Get subscriptions that expired
    expired_subscriptions = Subscription.objects.filter(
        status='active',
        end_date__lt=timezone.now()
    )
    
    count = 0
    for subscription in expired_subscriptions:
        subscription.status = 'expired'
        subscription.is_active = False
        subscription.save()
        
        # Update user
        user = subscription.user
        user.subscription_status = 'expired'
        user.save()
        
        count += 1
        logger.info(f"Deactivated expired subscription {subscription.id} for user {user.id}")
    
    logger.info(f"Deactivated {count} expired subscriptions")
    
    return {'success': True, 'expired_count': count}


@shared_task
def send_renewal_reminders():
    """
    Send renewal reminder emails to users whose subscriptions expire soon
    
    Runs: Daily at 9 AM (configured in celery.py)
    """
    logger.info("Sending subscription renewal reminders")
    
    # Get subscriptions expiring in 3 days
    reminder_date = timezone.now() + timedelta(days=3)
    
    expiring_subscriptions = Subscription.objects.filter(
        status='active',
        end_date__date=reminder_date.date()
    ).select_related('user', 'plan')
    
    count = 0
    for subscription in expiring_subscriptions:
        # TODO: Send renewal reminder email
        logger.info(f"Renewal reminder needed for user {subscription.user.id}")
        count += 1
    
    logger.info(f"Sent {count} renewal reminders")
    
    return {'success': True, 'reminders_sent': count}


@shared_task
def update_exchange_rates():
    """
    Update exchange rates from external API
    
    Runs: Every 6 hours (configured in celery.py)
    
    TODO: Implement actual exchange rate API integration
    """
    logger.info("Updating exchange rates (placeholder)")
    
    # TODO: Fetch from external API (e.g., exchangerate-api.com)
    
    return {'success': True, 'note': 'Exchange rate update not implemented'}


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def approve_telegram_join_request(self, chat_id, user_id):
    """
    Auto-approve a user's join request to a Telegram group
    
    This task is called when a paid user requests to join a group.
    It automatically approves their request if they have an active subscription.
    
    Args:
        chat_id: Telegram chat/group ID
        user_id: Telegram user ID requesting to join
        
    Returns:
        dict: Success status and details
    """
    try:
        logger.info(f"Auto-approving join request for user {user_id} to chat {chat_id}")
        
        # Get Telegram configuration
        try:
            telegram_config = TelegramConfiguration.get_instance()
            
            if not telegram_config.has_valid_token():
                logger.error("Telegram bot token not configured")
                return {'success': False, 'error': 'Telegram not configured'}
            
            bot_token = telegram_config.bot_token
            
        except Exception as e:
            logger.error(f"Error getting Telegram config: {str(e)}")
            return {'success': False, 'error': 'Configuration error'}
        
        # Check if user has active subscription
        try:
            billing_profile = BillingProfile.objects.filter(
                telegram_user_id=str(user_id),
                telegram_verified=True
            ).first()
            
            if not billing_profile:
                logger.warning(f"No verified billing profile found for telegram_user_id {user_id}")
                return {'success': False, 'error': 'User not verified'}
            
            # Check if user has active subscription
            user = billing_profile.user
            if user.subscription_status != 'active':
                logger.warning(f"User {user.email} does not have active subscription")
                return {'success': False, 'error': 'No active subscription'}
            
        except Exception as e:
            logger.error(f"Error checking user subscription: {str(e)}")
            return {'success': False, 'error': 'Database error'}
        
        # Approve the join request
        url = f"https://api.telegram.org/bot{bot_token}/approveChatJoinRequest"
        payload = {
            'chat_id': chat_id,
            'user_id': int(user_id)
        }
        
        response = requests.post(url, json=payload, timeout=30)
        data = response.json()
        
        if data.get('ok'):
            logger.info(f"✅ AUTO-APPROVED join request: @{billing_profile.telegram_username} → chat {chat_id}")
            
            # Send confirmation to user
            message = f"✅ *Join Request Approved!*\n\n"
            message += f"You've been added to the group. Welcome! 🎉"
            
            send_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            send_payload = {
                'chat_id': int(user_id),
                'text': message,
                'parse_mode': 'Markdown'
            }
            
            requests.post(send_url, json=send_payload, timeout=30)
            
            return {
                'success': True,
                'user_id': user_id,
                'chat_id': chat_id,
                'username': billing_profile.telegram_username
            }
        else:
            error = data.get('description', 'Unknown error')
            logger.error(f"Failed to approve join request: {error}")
            
            # Handle specific errors
            if 'USER_ALREADY_PARTICIPANT' in error:
                return {'success': True, 'note': 'User already in group'}
            elif 'HIDE_REQUESTER_MISSING' in error:
                return {'success': False, 'error': 'Group does not have join requests enabled'}
            
            return {'success': False, 'error': error}
    
    except Exception as e:
        logger.error(f"Error approving join request: {str(e)}", exc_info=True)
        
        # Retry
        try:
            raise self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for approve_telegram_join_request")
            return {'success': False, 'error': str(e)}


@shared_task(bind=True)
def process_telegram_updates(self):
    """
    Poll Telegram for new messages and handle verification codes.
    
    This task should be run periodically (e.g., every 5-10 seconds) via Celery Beat.
    It processes /start commands with verification codes and regular text messages.
    
    Flow:
    1. Call getUpdates to fetch new messages
    2. For each message, check if it's a /start command or verification code
    3. Match code with pending verification in database
    4. Mark user as verified and send confirmation
    5. Update offset to acknowledge processed messages
    
    No webhooks needed - works behind firewalls/NAT.
    """
    try:
        from django.core.cache import cache
        
        config = TelegramConfiguration.get_instance()
        
        if not config.has_valid_token():
            logger.debug("Telegram bot not configured, skipping update processing")
            return {'success': False, 'message': 'Bot not configured'}
        
        bot_token = config.decrypt_field('bot_token')
        
        # Get last processed update ID from cache
        offset_key = 'telegram_bot_update_offset'
        last_offset = cache.get(offset_key, 0)
        
        # Fetch updates from Telegram
        url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
        params = {
            'offset': last_offset + 1,  # Only get updates after last processed
            'timeout': 5,  # Long polling timeout
            'allowed_updates': ['message']  # Only interested in messages
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"Telegram getUpdates failed: {response.status_code}")
            return {'success': False, 'message': 'API request failed'}
        
        data = response.json()
        
        if not data.get('ok'):
            error = data.get('description', 'Unknown error')
            logger.error(f"Telegram API error: {error}")
            return {'success': False, 'message': error}
        
        updates = data.get('result', [])
        
        if not updates:
            logger.debug("No new Telegram updates")
            return {'success': True, 'processed': 0}
        
        processed_count = 0
        new_offset = last_offset
        
        for update in updates:
            update_id = update.get('update_id')
            new_offset = max(new_offset, update_id)
            
            # Only process messages
            if 'message' not in update:
                continue
            
            message = update['message']
            text = message.get('text', '').strip()
            user = message['from']
            user_id = str(user['id'])
            username = user.get('username', '')
            chat_id = message['chat']['id']
            
            # Handle /start command with deep link parameter
            if text.startswith('/start'):
                parts = text.split()
                
                # Check for deep link: /start VERIFY_A3F8K2
                if len(parts) == 2 and parts[1].startswith('VERIFY_'):
                    verification_code = parts[1].replace('VERIFY_', '').upper()
                    username_display = f"@{username}" if username else f"user_{user_id}"
                    logger.info(f"Deep link verification from {username_display}: {verification_code}")
                    
                    # Process verification
                    result = _process_verification_code(
                        verification_code, user_id, username, chat_id, bot_token
                    )
                    processed_count += 1
                    continue
                
                # Regular /start command - send welcome message
                _send_welcome_message(chat_id, username, bot_token)
                processed_count += 1
                continue
            
            # Handle direct code entry (6 alphanumeric characters)
            if text.upper().replace(' ', '') and len(text.replace(' ', '')) == 6:
                code = text.upper().replace(' ', '')
                
                # Validate code format: 6 alphanumeric
                import re
                if re.match(r'^[A-Z0-9]{6}$', code):
                    username_display = f"@{username}" if username else f"user_{user_id}"
                    logger.info(f"Direct code entry from {username_display}: {code}")
                    
                    result = _process_verification_code(
                        code, user_id, username, chat_id, bot_token
                    )
                    processed_count += 1
                    continue
        
        # Save new offset to cache
        if new_offset > last_offset:
            cache.set(offset_key, new_offset, timeout=None)  # Never expire
        
        logger.info(f"Processed {processed_count} Telegram updates")
        return {'success': True, 'processed': processed_count}
    
    except requests.exceptions.Timeout:
        logger.warning("Telegram API timeout")
        return {'success': False, 'message': 'Timeout'}
    
    except Exception as e:
        logger.error(f"Error processing Telegram updates: {str(e)}", exc_info=True)
        return {'success': False, 'error': str(e)}


def _process_verification_code(verification_code, telegram_user_id, telegram_username, chat_id, bot_token):
    """
    Helper function to process a verification code.
    
    Args:
        verification_code: 6-character code (e.g., "A3F8K2")
        telegram_user_id: Telegram user ID (str)
        telegram_username: Telegram username (optional)
        chat_id: Chat ID to send response to
        bot_token: Decrypted bot token
        
    Returns:
        Dict with success status and message
    """
    try:
        # Find billing profile with matching code
        from django.utils import timezone
        
        billing_profile = BillingProfile.objects.filter(
            verification_code=verification_code,
            verification_code_expires_at__gt=timezone.now(),
            telegram_verified=False
        ).first()
        
        if not billing_profile:
            # Code not found or expired
            _send_telegram_message(
                chat_id,
                "❌ Invalid or expired verification code.\n\n"
                "Please generate a new code from the website and try again.",
                bot_token
            )
            return {'success': False, 'message': 'Invalid code'}
        
        # Mark as verified
        billing_profile.telegram_user_id = telegram_user_id
        billing_profile.telegram_username = telegram_username if telegram_username else f"user_{telegram_user_id}"
        billing_profile.telegram_verified = True
        billing_profile.verification_code = None  # Clear code
        billing_profile.verification_code_expires_at = None
        billing_profile.save(update_fields=[
            'telegram_user_id', 'telegram_username', 'telegram_verified',
            'verification_code', 'verification_code_expires_at'
        ])
        
        # Send success message
        username_display = f"@{telegram_username}" if telegram_username else f"user_{telegram_user_id}"
        _send_telegram_message(
            chat_id,
            f"✅ Verification successful!\n\n"
            f"Your Telegram account is now linked to your subscription.\n"
            f"User ID: {telegram_user_id}",
            bot_token
        )
        
        logger.info(f"✅ Verified: {billing_profile.user.email} → {username_display}")
        return {'success': True, 'message': 'Verified successfully'}
    
    except Exception as e:
        logger.error(f"Error in _process_verification_code: {str(e)}", exc_info=True)
        _send_telegram_message(
            chat_id,
            "❌ An error occurred during verification. Please try again or contact support.",
            bot_token
        )
        return {'success': False, 'error': str(e)}


def _send_welcome_message(chat_id, username, bot_token):
    """Send welcome message when user clicks /start."""
    message = (
        f"👋 Welcome to the bot{', @' + username if username else ''}!\n\n"
        "To verify your Telegram account:\n"
        "1. Generate a verification code on the website\n"
        "2. Send the 6-character code here\n\n"
        "Example: If your code is A3F8K2, just type:\n"
        "A3F8K2"
    )
    _send_telegram_message(chat_id, message, bot_token)


def _send_telegram_message(chat_id, text, bot_token):
    """
    Helper function to send a message via Telegram API.
    
    Args:
        chat_id: Telegram chat ID
        text: Message text
        bot_token: Decrypted bot token
    """
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        requests.post(
            url,
            json={'chat_id': chat_id, 'text': text},
            timeout=10
        )
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {str(e)}")


# ============================================================================
# AUTO-RENEWAL TASKS (Trial tasks removed - trials disabled)
# ============================================================================
# Note: process_trial_endings() and process_trial_conversion() tasks have been
# removed as the platform no longer supports free trials. All subscriptions
# are now paid upfront (with optional coupon discounts).
# 
# The removed tasks were:
#   - process_trial_endings(): Detected trials ending today, queued conversions
#   - process_trial_conversion(): Charged payment method to convert trial to paid
# 
# Removal date: 2025
# Reason: Platform switched to Udemy-style coupon model, trials disabled
# ============================================================================


@shared_task
def process_auto_renewals():
    """
    Process auto-renewals for subscriptions ending today.
    
    Runs: Daily at 2 AM (configured in celery.py)
    
    Flow:
        1. Find all paid subscriptions ending today with auto_renew=True
        2. For each subscription, charge saved payment method
        3. On success: Extend subscription
        4. On failure: Retry, then disable auto_renew
    
    Returns:
        dict: Summary of renewals processed
    """
    try:
        logger.info("Processing auto-renewals for subscriptions ending today")
        
        from django.utils import timezone
        
        # Get subscriptions ending today with auto-renewal enabled
        today = timezone.now().date()
        
        renewing_subscriptions = Subscription.objects.filter(
            status='active',
            is_trial=False,  # Only paid subscriptions
            auto_renew=True,
            next_billing_date__date=today
        ).select_related('billing_profile__user', 'plan', 'payment_method')
        
        total_count = renewing_subscriptions.count()
        
        if total_count == 0:
            logger.info("No subscriptions to auto-renew today")
            return {'success': True, 'renewals': 0}
        
        logger.info(f"Found {total_count} subscriptions to auto-renew")
        
        # Process each renewal
        processed = 0
        for subscription in renewing_subscriptions:
            try:
                # Queue individual renewal task (async)
                process_single_renewal.delay(str(subscription.id))
                processed += 1
                logger.info(f"Queued auto-renewal for subscription {subscription.id}")
            except Exception as e:
                logger.error(f"Failed to queue renewal for {subscription.id}: {str(e)}")
        
        logger.info(f"Queued {processed}/{total_count} auto-renewals")
        
        return {
            'success': True,
            'renewals': total_count,
            'queued': processed
        }
    
    except Exception as e:
        logger.error(f"Error in process_auto_renewals: {str(e)}", exc_info=True)
        return {'success': False, 'error': str(e)}


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def process_single_renewal(self, subscription_id):
    """
    Process a single subscription renewal by charging saved payment method.
    
    Args:
        subscription_id: UUID string of subscription to renew
        
    Similar to trial conversion but for regular renewals.
    
    Retries: 3 times with 5-minute delay
    """
    try:
        from django.utils import timezone
        from datetime import timedelta
        from subscriptions.payment_service import PaystackService
        
        logger.info(f"Processing auto-renewal for subscription {subscription_id}")
        
        # Get subscription
        try:
            subscription = Subscription.objects.select_related(
                'billing_profile__user',
                'plan',
                'payment_method'
            ).get(id=subscription_id)
        except Subscription.DoesNotExist:
            logger.error(f"Subscription {subscription_id} not found")
            return {'success': False, 'error': 'Subscription not found'}
        
        # Verify auto_renew is enabled
        if not subscription.auto_renew:
            logger.warning(f"Auto-renew disabled for subscription {subscription_id}")
            return {'success': False, 'error': 'Auto-renew not enabled'}
        
        # Check for payment method
        if not subscription.payment_method or not subscription.payment_method.is_active:
            logger.error(f"No active payment method for subscription {subscription_id}")
            
            # Disable auto-renew
            subscription.auto_renew = False
            subscription.save(update_fields=['auto_renew'])
            
            # TODO: Send email notification about disabled auto-renewal
            
            return {
                'success': False,
                'error': 'No active payment method',
                'action': 'auto_renew_disabled'
            }
        
        payment_method = subscription.payment_method
        user = subscription.billing_profile.user
        auth_code = payment_method.gateway_authorization_code
        
        if not auth_code:
            logger.error(f"Payment method {payment_method.id} has no authorization code")
            subscription.auto_renew = False
            subscription.save(update_fields=['auto_renew'])
            return {
                'success': False,
                'error': 'No authorization code',
                'action': 'auto_renew_disabled'
            }
        
        # Calculate amount
        amount = subscription.plan.base_price
        currency = subscription.currency or 'USD'
        
        # Charge payment method
        logger.info(f"Charging {currency} {amount} for renewal of {subscription_id}")
        
        paystack_service = PaystackService()
        
        charge_result = paystack_service.charge_authorization(
            authorization_code=auth_code,
            email=user.email,
            amount=amount,
            currency=currency,
            metadata={
                'subscription_id': str(subscription.id),
                'plan_id': str(subscription.plan.id),
                'renewal': True,
                'user_email': user.email
            }
        )
        
        if charge_result.get('success'):
            # Renewal successful
            logger.info(f"✅ Auto-renewal successful for {subscription_id}")
            
            # Extend subscription
            if subscription.plan.billing_period == 'weekly':
                subscription.next_billing_date = timezone.now() + timedelta(days=7)
                subscription.end_date = timezone.now() + timedelta(days=7)
            elif subscription.plan.billing_period == 'monthly':
                subscription.next_billing_date = timezone.now() + timedelta(days=30)
                subscription.end_date = timezone.now() + timedelta(days=30)
            elif subscription.plan.billing_period == 'quarterly':
                subscription.next_billing_date = timezone.now() + timedelta(days=90)
                subscription.end_date = timezone.now() + timedelta(days=90)
            elif subscription.plan.billing_period == 'yearly':
                subscription.next_billing_date = timezone.now() + timedelta(days=365)
                subscription.end_date = timezone.now() + timedelta(days=365)
            else:
                subscription.next_billing_date = timezone.now() + timedelta(days=30)
                subscription.end_date = timezone.now() + timedelta(days=30)
            
            subscription.save()
            
            # Create payment record
            Payment.objects.create(
                billing_profile=subscription.billing_profile,
                subscription=subscription,
                payment_method=payment_method,
                amount=amount,
                currency=currency,
                processing_fee=Decimal('0.00'),
                total_amount=amount,
                status='success',
                gateway='paystack',
                gateway_reference=charge_result.get('reference'),
                gateway_response=charge_result,
                paid_at=timezone.now()
            )
            
            # TODO: Send renewal confirmation email
            
            return {
                'success': True,
                'subscription_id': str(subscription.id),
                'amount_charged': float(amount),
                'currency': currency,
                'reference': charge_result.get('reference'),
                'next_billing_date': subscription.next_billing_date.isoformat()
            }
        
        else:
            # Renewal payment failed
            error_message = charge_result.get('message', 'Unknown error')
            logger.error(f"Renewal payment failed for {subscription_id}: {error_message}")
            
            # Retry
            if self.request.retries < self.max_retries:
                logger.info(f"Retrying renewal for {subscription_id} (attempt {self.request.retries + 1}/{self.max_retries})")
                raise self.retry(exc=Exception(error_message))
            else:
                # Max retries - disable auto-renewal
                logger.error(f"Max retries exceeded for {subscription_id}, disabling auto-renew")
                
                subscription.auto_renew = False
                subscription.save(update_fields=['auto_renew'])
                
                # TODO: Send email about failed renewal
                
                return {
                    'success': False,
                    'error': error_message,
                    'action': 'auto_renew_disabled',
                    'retries_exhausted': True
                }
    
    except Exception as e:
        logger.error(f"Error in process_single_renewal for {subscription_id}: {str(e)}", exc_info=True)
        
        try:
            raise self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for renewal {subscription_id}")
            
            try:
                subscription = Subscription.objects.get(id=subscription_id)
                subscription.auto_renew = False
                subscription.save(update_fields=['auto_renew'])
            except Exception as save_error:
                logger.error(f"Failed to disable auto_renew: {str(save_error)}")
            
            return {'success': False, 'error': str(e), 'action': 'auto_renew_disabled'}
