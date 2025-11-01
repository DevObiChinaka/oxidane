#!/usr/bin/env python3
"""
OxiWorld Bot - User Management Bot for OxiWorld Forex Academy
Handles automated user additions and removals based on subscription status
"""

import os
import sys
import django
import logging
import asyncio
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Setup Django
sys.path.append('C:/Users/user/OneDrive/Desktop/Oxidane/backend')  # Updated path
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import TelegramError, Forbidden, BadRequest

from django.conf import settings
from django.utils import timezone
from subscriptions.models import SignalSubscription, TelegramGroupManagement

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class OxiWorldBot:
    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.groups = settings.TELEGRAM_GROUPS
        self.bot = Bot(token=self.bot_token)
        self.application = None
        
        # Group access mapping based on subscription levels
        self.group_access = {
            'basic': ['education_group'],  # Mentorship only
            'premium': ['education_group', 'premium_signals'],  # Mentorship + Signals
            'vip': ['education_group', 'premium_signals', 'vip_community']  # All groups
        }
        
    async def initialize(self):
        """Initialize the bot application"""
        self.application = Application.builder().token(self.bot_token).build()
        
        # Add command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("verify", self.verify_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("support", self.support_command))
        
        # Admin commands (you can restrict these by user ID)
        self.application.add_handler(CommandHandler("admin_add", self.admin_add_user))
        self.application.add_handler(CommandHandler("admin_remove", self.admin_remove_user))
        self.application.add_handler(CommandHandler("admin_status", self.admin_status))
        self.application.add_handler(CommandHandler("admin_stats", self.admin_stats))
        
        logger.info("OxiWorld Bot initialized successfully")
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        
        welcome_message = f"""
🤖 **Welcome to OxiWorld Bot!**

Hello {user.first_name}, I'm your OxiWorld Forex Academy assistant.

I manage access to our premium Telegram groups based on your subscription status.

**Available Commands:**
• /verify - Verify your Telegram account for subscriptions
• /status - Check your subscription and group access
• /help - Show all commands
• /support - Get support information

To access premium groups:
1. Subscribe at oxiworld.com/billing
2. Get your verification code
3. Send: /verify YOUR-CODE

Happy trading! 📈
        """
        
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
    
    async def verify_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /verify command - Link Telegram account to billing profile"""
        user = update.effective_user
        
        # Check if user provided verification code
        if not context.args:
            await update.message.reply_text(
                "❌ **Please provide your verification code**\n\n"
                "**Usage:** `/verify YOUR-CODE`\n\n"
                "**Example:** `/verify OXI-1234`\n\n"
                "**How to get your code:**\n"
                "1. Go to oxiworld.com/billing\n"
                "2. Click 'Verify Telegram'\n"
                "3. Copy your verification code\n"
                "4. Send it here with /verify",
                parse_mode='Markdown'
            )
            return
        
        verification_code = context.args[0].upper().strip()
        
        # Validate code format
        if not verification_code.startswith('OXI-'):
            await update.message.reply_text(
                "❌ Invalid code format. Code should look like: OXI-1234"
            )
            return
        
        # Show processing message
        processing_msg = await update.message.reply_text("⏳ Verifying your code...")
        
        try:
            # Make request to backend verification endpoint
            import requests
            
            backend_url = os.getenv('BACKEND_URL', 'http://localhost:8000')
            bot_secret = os.getenv('TELEGRAM_BOT_SECRET', 'your-secret-key')
            
            response = requests.post(
                f"{backend_url}/api/billing/telegram/verify-callback/",
                json={
                    'verification_code': verification_code,
                    'telegram_user_id': user.id,
                    'telegram_username': user.username or '',
                    'telegram_first_name': user.first_name,
                    'telegram_last_name': user.last_name or '',
                },
                headers={
                    'X-Bot-Secret': bot_secret,
                    'Content-Type': 'application/json'
                },
                timeout=10
            )
            
            # Delete processing message
            await processing_msg.delete()
            
            if response.status_code == 200:
                data = response.json()
                user_email = data.get('user_email', 'your account')
                
                success_message = f"""
✅ **Verification Successful!**

Your Telegram account has been linked to: {user_email}

**What's Next:**
• Subscribe to any plan at oxiworld.com/billing
• I'll automatically add you to the appropriate groups
• Use /status to check your access anytime

**Your Info:**
• Telegram ID: `{user.id}`
• Username: @{user.username or 'Not set'}

You're all set! 🎉
                """
                
                await update.message.reply_text(success_message, parse_mode='Markdown')
                logger.info(f"Verification successful for user {user.id} (@{user.username})")
                
            elif response.status_code == 400:
                error_data = response.json()
                error_msg = error_data.get('error', 'Invalid or expired code')
                
                if 'expired' in error_msg.lower():
                    await update.message.reply_text(
                        "❌ **Verification code expired**\n\n"
                        "Please generate a new code:\n"
                        "1. Go to oxiworld.com/billing\n"
                        "2. Click 'Verify Telegram'\n"
                        "3. Get a fresh verification code\n"
                        "4. Try again with: /verify NEW-CODE"
                    )
                else:
                    await update.message.reply_text(
                        f"❌ **Verification Failed**\n\n{error_msg}\n\n"
                        "Please make sure:\n"
                        "• Code is correct (copy-paste recommended)\n"
                        "• Code hasn't expired (valid for 24 hours)\n"
                        "• You got the code from oxiworld.com/billing"
                    )
                
                logger.warning(f"Verification failed for user {user.id}: {error_msg}")
                
            else:
                await update.message.reply_text(
                    "❌ **Server Error**\n\n"
                    "Something went wrong. Please try again in a moment.\n"
                    "If the problem persists, contact support: /support"
                )
                logger.error(f"Verification endpoint returned {response.status_code}")
                
        except requests.exceptions.Timeout:
            await processing_msg.delete()
            await update.message.reply_text(
                "❌ **Connection Timeout**\n\n"
                "The server took too long to respond. Please try again."
            )
            logger.error("Verification request timeout")
            
        except requests.exceptions.RequestException as e:
            await processing_msg.delete()
            await update.message.reply_text(
                "❌ **Connection Error**\n\n"
                "Could not connect to verification server.\n"
                "Please try again later or contact support."
            )
            logger.error(f"Verification request failed: {e}")
            
        except Exception as e:
            await processing_msg.delete()
            await update.message.reply_text(
                "❌ **Unexpected Error**\n\n"
                "Something went wrong during verification.\n"
                "Please contact support: /support"
            )
            logger.error(f"Unexpected error in verify command: {e}", exc_info=True)
        
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check user's subscription status and group access"""
        user = update.effective_user
        telegram_username = user.username
        
        if not telegram_username:
            await update.message.reply_text(
                "❌ Please set a Telegram username in your profile settings to use this bot."
            )
            return
            
        try:
            # Find user's subscription by telegram username
            subscription = SignalSubscription.objects.filter(
                telegram_username=telegram_username,
                payment_status='verified'
            ).first()
            
            if not subscription:
                await update.message.reply_text(
                    "❌ No active subscription found for your Telegram username.\n\n"
                    "Please make sure:\n"
                    "1. You have an active subscription at oxiworld.com\n"
                    "2. Your Telegram username matches your subscription\n"
                    "3. Your payment has been verified\n\n"
                    "Contact support if you need help: /support"
                )
                return
                
            # Check subscription validity
            now = timezone.now()
            is_active = subscription.subscription_end and subscription.subscription_end > now
            
            if not is_active:
                await update.message.reply_text(
                    f"⚠️ Your subscription expired on {subscription.subscription_end.strftime('%B %d, %Y')}\n\n"
                    "Please renew your subscription to regain access to premium groups.\n\n"
                    "Visit: oxiworld.com/subscribe"
                )
                return
                
            # Determine accessible groups
            plan_type = self.get_plan_type(subscription)
            accessible_groups = self.group_access.get(plan_type, [])
            
            status_message = f"""
✅ **Subscription Status: Active**

**Plan**: {plan_type.title()}
**Expires**: {subscription.subscription_end.strftime('%B %d, %Y')}

**Your Group Access:**
            """
            
            for group_key in accessible_groups:
                group_info = self.groups.get(group_key, {})
                group_name = group_info.get('name', 'Unknown Group')
                status_message += f"\n• {group_name} ✅"
                
            # Add renewal reminder if expiring soon
            days_left = (subscription.subscription_end - now).days
            if days_left <= 7:
                status_message += f"\n\n⚠️ **Renewal Reminder**: Your subscription expires in {days_left} days!"
                
            await update.message.reply_text(status_message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in status command: {e}")
            await update.message.reply_text(
                "❌ Error checking subscription status. Please try again later or contact support."
            )
            
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show help information"""
        help_text = """
🤖 **OxiWorld Bot Commands**

**User Commands:**
• /start - Welcome message and bot introduction
• /verify CODE - Verify your Telegram for subscriptions
• /status - Check your subscription and group access  
• /help - Show this help message
• /support - Get support contact information

**How To Get Started:**
1. Go to oxiworld.com/billing
2. Click "Verify Telegram" to get your code
3. Send me: /verify YOUR-CODE
4. Subscribe to any plan
5. I'll automatically add you to appropriate groups!

**Subscription Levels:**
• **Basic** → Mentorship Group access
• **Signals** → Signals Groups  
• **VIP** → All Groups (Mentorship + Signals + VIP)

**Need Help?**
Use /support for contact information or visit oxiworld.com
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
        
    async def support_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show support information"""
        support_text = """
📞 **OxiWorld Support**

**Website**: oxiworld.com
**Email**: support@oxiworld.com
**Subscription Issues**: billing@oxiworld.com

**Common Issues:**
• **Not added to groups?** Check your subscription status with /status
• **Wrong groups?** Verify your subscription plan level
• **Username issues?** Make sure your Telegram username is set

**Business Hours**: Monday - Friday, 9 AM - 6 PM UTC

We're here to help! 🚀
        """
        await update.message.reply_text(support_text, parse_mode='Markdown')
    
    async def verify_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /verify command for Telegram account verification"""
        user = update.effective_user
        
        # Check if verification code was provided
        if not context.args or len(context.args) == 0:
            await update.message.reply_text(
                "❌ **Verification Code Required**\n\n"
                "Please provide your verification code:\n"
                "`/verify OXI-1234`\n\n"
                "Get your code from the Billing page at oxiworld.com",
                parse_mode='Markdown'
            )
            return
        
        verification_code = context.args[0].upper().strip()
        telegram_user_id = user.id
        telegram_username = user.username or ''
        
        logger.info(f"Verification attempt - Code: {verification_code}, User ID: {telegram_user_id}, Username: @{telegram_username}")
        
        try:
            # Import here to avoid circular imports
            from subscriptions.billing_models import BillingProfile
            
            # Find billing profile with this verification code
            try:
                billing_profile = BillingProfile.objects.get(verification_code=verification_code)
            except BillingProfile.DoesNotExist:
                await update.message.reply_text(
                    "❌ **Invalid Verification Code**\n\n"
                    "The code you entered is not valid or has already been used.\n\n"
                    "Please:\n"
                    "1. Check the code and try again\n"
                    "2. Generate a new code at oxiworld.com/billing\n"
                    "3. Contact support if you need help: /support",
                    parse_mode='Markdown'
                )
                logger.warning(f"Invalid verification code: {verification_code}")
                return
            
            # Check if code is expired
            if not billing_profile.is_verification_code_valid(verification_code):
                await update.message.reply_text(
                    "⏰ **Verification Code Expired**\n\n"
                    "Your verification code has expired (24 hour limit).\n\n"
                    "Please generate a new code at oxiworld.com/billing",
                    parse_mode='Markdown'
                )
                logger.warning(f"Expired verification code: {verification_code}")
                return
            
            # Verify the Telegram account
            billing_profile.verify_telegram(telegram_user_id, telegram_username)
            
            # Success message
            success_message = f"""
✅ **Verification Successful!**

Your Telegram account has been linked to your OxiWorld account.

**Account Details:**
• Email: `{billing_profile.user.email}`
• Telegram ID: `{telegram_user_id}`
• Username: `@{telegram_username or 'Not set'}`

**What's Next?**
1. You can now subscribe to premium plans
2. Your group access will be managed automatically
3. Use /status to check your subscription

Welcome to OxiWorld! 🚀
            """
            
            await update.message.reply_text(success_message, parse_mode='Markdown')
            
            logger.info(f"Verification successful - User: {billing_profile.user.email}, Telegram ID: {telegram_user_id}")
            
        except Exception as e:
            logger.error(f"Error in verify command: {e}", exc_info=True)
            await update.message.reply_text(
                "❌ **Verification Error**\n\n"
                "An error occurred during verification. Please try again later or contact support.\n\n"
                "Use /support for contact information.",
                parse_mode='Markdown'
            )
        
    # Admin Commands (restrict these by user ID in production)
    async def admin_add_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command to manually add user to group"""
        if not await self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized. Admin access required.")
            return
            
        try:
            args = context.args
            if len(args) < 2:
                await update.message.reply_text(
                    "Usage: /admin_add <telegram_username> <group_key>\n"
                    "Groups: education_group, premium_signals, vip_community"
                )
                return
                
            username = args[0].replace('@', '')
            group_key = args[1]
            
            result = await self.add_user_to_group(username, group_key)
            await update.message.reply_text(f"✅ {result}")
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
            
    async def admin_remove_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command to manually remove user from group"""
        if not await self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized. Admin access required.")
            return
            
        try:
            args = context.args
            if len(args) < 2:
                await update.message.reply_text(
                    "Usage: /admin_remove <telegram_username> <group_key>\n"
                    "Groups: education_group, premium_signals, vip_community"
                )
                return
                
            username = args[0].replace('@', '')
            group_key = args[1]
            
            result = await self.remove_user_from_group(username, group_key)
            await update.message.reply_text(f"✅ {result}")
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
            
    async def admin_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command to check user's subscription status"""
        if not await self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized. Admin access required.")
            return
            
        try:
            args = context.args
            if len(args) < 1:
                await update.message.reply_text(
                    "Usage: /admin_status <telegram_username>\n"
                    "Example: /admin_status @johndoe"
                )
                return
                
            username = args[0].replace('@', '')
            
            # Find user's subscription
            subscription = SignalSubscription.objects.filter(
                telegram_username=username,
                payment_status='verified'
            ).first()
            
            if not subscription:
                await update.message.reply_text(f"❌ No subscription found for @{username}")
                return
                
            # Check subscription validity
            now = timezone.now()
            is_active = subscription.subscription_end and subscription.subscription_end > now
            plan_type = self.get_plan_type(subscription)
            
            status_msg = f"""
📊 **Admin Status Check: @{username}**

**User**: {subscription.user.email}
**Plan**: {plan_type.title()}
**Status**: {'✅ Active' if is_active else '❌ Expired'}
**Expires**: {subscription.subscription_end.strftime('%B %d, %Y')}
**Telegram Status**: {subscription.telegram_status}
**Payment Status**: {subscription.payment_status}
            """
            
            await update.message.reply_text(status_msg, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def admin_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show bot statistics"""
        if not await self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized. Admin access required.")
            return
            
        try:
            stats = await self.get_bot_stats()
            await update.message.reply_text(stats, parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text(f"❌ Error getting stats: {e}")
    
    # Core User Management Functions
    async def add_user_to_group(self, telegram_username: str, group_key: str) -> str:
        """Add user to specified Telegram group"""
        try:
            # Get group info
            group_info = self.groups.get(group_key)
            if not group_info:
                return f"❌ Group '{group_key}' not found"
                
            chat_id = group_info['chat_id']
            group_name = group_info['name']
            
            try:
                # Create an invite link for the user to join
                # This is more reliable than trying to add them directly
                invite_link = await self.bot.create_chat_invite_link(
                    chat_id,
                    member_limit=1,
                    expire_date=int((timezone.now() + timedelta(hours=24)).timestamp())
                )
                
                # Send welcome message with invite link
                welcome_msg = f"""
{self.get_welcome_message(group_key)}

🔗 **Join Link**: {invite_link.invite_link}
⏰ This link expires in 24 hours.

After joining, you'll have full access to the group!
                """
                
                # Try to send direct message to user (if they've started chat with bot)
                try:
                    # This would only work if user has started a chat with the bot
                    # For now, we'll return the invite link
                    pass
                except:
                    pass
                
                return f"✅ Created invite link for @{telegram_username} to {group_name}\nLink: {invite_link.invite_link}"
                
            except Forbidden:
                return f"❌ Bot lacks permission to create invite links for {group_name}"
            except BadRequest as e:
                return f"❌ Failed to create invite link: {e}"
                
        except Exception as e:
            logger.error(f"Error adding user {telegram_username} to {group_key}: {e}")
            return f"❌ Error: {e}"
    
    async def remove_user_from_group(self, telegram_username: str, group_key: str) -> str:
        """Remove user from specified Telegram group"""
        try:
            group_info = self.groups.get(group_key)
            if not group_info:
                return f"❌ Group '{group_key}' not found"
                
            chat_id = group_info['chat_id']
            group_name = group_info['name']
            
            try:
                # For removal, we need the user's numeric ID
                # This is a limitation - we'll need to store user IDs when they interact with the bot
                # For now, we'll return a message indicating manual removal is needed
                return f"⚠️ Manual removal needed for @{telegram_username} from {group_name} (User ID required)"
                
            except Forbidden:
                return f"❌ Bot lacks permission to remove users from {group_name}"
            except BadRequest as e:
                return f"❌ Failed to remove user: {e}"
                
        except Exception as e:
            logger.error(f"Error removing user {telegram_username} from {group_key}: {e}")
            return f"❌ Error: {e}"
    
    # Subscription Management Integration
    async def process_subscription_updates(self):
        """Process pending subscription updates from Django queue"""
        try:
            # Get pending additions
            pending_additions = TelegramGroupManagement.objects.filter(
                action_type='add',
                status='pending'
            )
            
            for task in pending_additions:
                try:
                    subscription = task.signal_subscription
                    plan_type = self.get_plan_type(subscription)
                    accessible_groups = self.group_access.get(plan_type, [])
                    
                    success_count = 0
                    for group_key in accessible_groups:
                        result = await self.add_user_to_group(
                            subscription.telegram_username, 
                            group_key
                        )
                        if "✅" in result:
                            success_count += 1
                            
                    # Update task status
                    if success_count > 0:
                        task.status = 'completed'
                        task.admin_notes = f"Added to {success_count} groups"
                        subscription.mark_telegram_added(task.telegram_group)
                    else:
                        task.status = 'failed'
                        task.admin_notes = "Failed to add to any groups"
                        
                    task.processed_at = timezone.now()
                    task.save()
                    
                except Exception as e:
                    task.status = 'failed'
                    task.admin_notes = str(e)
                    task.processed_at = timezone.now()
                    task.save()
                    logger.error(f"Error processing addition task {task.id}: {e}")
            
            # Get pending removals
            pending_removals = TelegramGroupManagement.objects.filter(
                action_type='remove',
                status='pending'
            )
            
            for task in pending_removals:
                try:
                    subscription = task.signal_subscription
                    
                    # Remove from all groups
                    success_count = 0
                    for group_key in self.groups.keys():
                        result = await self.remove_user_from_group(
                            subscription.telegram_username,
                            group_key
                        )
                        if "✅" in result:
                            success_count += 1
                    
                    # Update task status
                    task.status = 'completed' if success_count > 0 else 'failed'
                    task.admin_notes = f"Removed from {success_count} groups"
                    task.processed_at = timezone.now()
                    task.save()
                    
                except Exception as e:
                    task.status = 'failed'
                    task.admin_notes = str(e)
                    task.processed_at = timezone.now()
                    task.save()
                    logger.error(f"Error processing removal task {task.id}: {e}")
                    
        except Exception as e:
            logger.error(f"Error processing subscription updates: {e}")
    
    # Helper Functions
    def get_plan_type(self, subscription: SignalSubscription) -> str:
        """Determine plan type from subscription"""
        # You'll need to implement this based on your subscription model
        # This is a placeholder - adjust based on your actual fields
        if hasattr(subscription, 'plan_type'):
            return subscription.plan_type
        elif hasattr(subscription, 'amount_paid'):
            # Example based on payment amount
            amount = float(subscription.amount_paid)
            if amount >= 99:  # VIP threshold
                return 'vip'
            elif amount >= 29:  # Premium threshold  
                return 'premium'
            else:
                return 'basic'
        else:
            return 'basic'  # Default fallback
    
    def get_welcome_message(self, group_key: str) -> str:
        """Get welcome message for specific group"""
        messages = {
            'education_group': """
🎓 Welcome to OxiWorld Forex Mentorship!

You now have access to:
• Exclusive educational content
• Personal mentorship sessions  
• Advanced trading strategies
• Direct Q&A with instructors

Please read our group rules and introduce yourself!
Happy learning! 📚
            """,
            'premium_signals': """
📊 Welcome to OxiWorld Trading Signals!

You now have access to:
• Daily trading signals
• Entry and exit points
• Risk management guidance
• Market analysis updates

Please enable notifications for important signals! 🔔
            """,
            'vip_community': """
💎 Welcome to OxiWorld VIP Members!

You're now part of our exclusive VIP community:
• Premium trading signals
• Advanced market insights
• Priority support
• Exclusive trading strategies

Welcome to the elite trading circle! 🏆
            """
        }
        return messages.get(group_key, "Welcome to OxiWorld Forex Academy!")
    
    async def is_admin(self, user_id: int) -> bool:
        """Check if user is admin (implement your own logic)"""
        # Add your admin user IDs here
        admin_ids = [123456789]  # Replace with actual admin Telegram IDs
        return user_id in admin_ids
    
    async def get_bot_stats(self) -> str:
        """Get bot statistics"""
        try:
            # Get stats from Django models
            total_subscriptions = SignalSubscription.objects.filter(payment_status='verified').count()
            active_subscriptions = SignalSubscription.objects.filter(
                payment_status='verified',
                subscription_end__gt=timezone.now()
            ).count()
            
            pending_tasks = TelegramGroupManagement.objects.filter(status='pending').count()
            completed_today = TelegramGroupManagement.objects.filter(
                status='completed',
                processed_at__gte=timezone.now().date()
            ).count()
            
            stats_msg = f"""
📊 **OxiWorld Bot Statistics**

**Subscriptions:**
• Total Verified: {total_subscriptions}
• Currently Active: {active_subscriptions}

**Queue Status:**
• Pending Tasks: {pending_tasks}
• Completed Today: {completed_today}

**Groups Managed:**
• Total Groups: {len(self.groups)}
            """
            
            for group_key, group_info in self.groups.items():
                try:
                    chat = await self.bot.get_chat(group_info['chat_id'])
                    member_count = await self.bot.get_chat_member_count(group_info['chat_id'])
                    stats_msg += f"\n• {group_info['name']}: {member_count} members"
                except:
                    stats_msg += f"\n• {group_info['name']}: Error getting count"
            
            return stats_msg
            
        except Exception as e:
            return f"❌ Error getting statistics: {e}"
    
    # Daily Maintenance Tasks
    async def daily_subscription_check(self):
        """Daily check for expired subscriptions"""
        try:
            logger.info("Running daily subscription check...")
            
            # Find subscriptions expiring today
            today = timezone.now().date()
            expired_subscriptions = SignalSubscription.objects.filter(
                subscription_end__date=today,
                payment_status='verified'
            )
            
            for subscription in expired_subscriptions:
                # Create removal task
                for group_key in self.groups.keys():
                    TelegramGroupManagement.objects.create(
                        signal_subscription=subscription,
                        action_type='remove',
                        telegram_username=subscription.telegram_username,
                        telegram_group=group_key,
                        status='pending'
                    )
                
                # Mark subscription as inactive
                subscription.telegram_status = 'removed'
                subscription.save()
                
            logger.info(f"Created removal tasks for {expired_subscriptions.count()} expired subscriptions")
            
        except Exception as e:
            logger.error(f"Error in daily subscription check: {e}")
    
    async def run_bot(self):
        """Main bot runner"""
        try:
            await self.initialize()
            
            # Start the bot
            await self.application.initialize()
            await self.application.start()
            
            logger.info("OxiWorld Bot started successfully!")
            
            # Run the bot
            await self.application.updater.start_polling()
            
            # Keep running and process subscription updates periodically
            while True:
                await asyncio.sleep(30)  # Check every 30 seconds
                await self.process_subscription_updates()
                
        except Exception as e:
            logger.error(f"Error running bot: {e}")
        finally:
            # Safely stop the application
            try:
                if self.application:
                    await self.application.stop()
            except Exception as stop_error:
                logger.error(f"Error stopping application: {stop_error}")

# Main execution
async def main():
    """Main function to run the bot"""
    oxiworld_bot = OxiWorldBot()
    await oxiworld_bot.run_bot()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")