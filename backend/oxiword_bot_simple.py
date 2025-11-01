#!/usr/bin/env python3
"""
OxiWord Bot - Simplified User Management Bot for OxiWorld Forex Academy
Version 2.0 - Focuses on invite link generation and user tracking
"""

import os
import sys
import django
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Setup Django
sys.path.append('C:/Users/user/OneDrive/Desktop/Oxidane/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import Forbidden, BadRequest

from django.conf import settings
from django.utils import timezone
from subscriptions.models import SignalSubscription, TelegramGroupManagement

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class OxiWordBotSimple:
    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.groups = settings.TELEGRAM_GROUPS
        self.bot = Bot(token=self.bot_token)
        self.application = None
        
        # Group access mapping based on subscription levels
        self.group_access = {
            'basic': ['mentorship'],  # Mentorship/Education only
            'signals': ['signals'],  # Signals only (new dedicated level)
            'premium': ['mentorship', 'signals'],  # Mentorship + Signals
            'vip': ['mentorship', 'signals', 'vip']  # All groups
        }
        
    async def initialize(self):
        """Initialize the bot application"""
        self.application = Application.builder().token(self.bot_token).build()
        
        # Add command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("support", self.support_command))
        
        # Admin commands
        self.application.add_handler(CommandHandler("admin_stats", self.admin_stats))
        self.application.add_handler(CommandHandler("admin_invite", self.admin_create_invite))
        
        logger.info("OxiWord Bot initialized successfully")
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command and register user"""
        user = update.effective_user
        
        # Store/update user's Telegram ID in database
        if user.username:
            try:
                from asgiref.sync import sync_to_async
                from django.contrib.auth import get_user_model
                User = get_user_model()
                
                @sync_to_async
                def save_telegram_id():
                    try:
                        # Find user by telegram username in subscription
                        subscription = SignalSubscription.objects.filter(
                            telegram_username=user.username,
                            payment_status='verified'
                        ).first()
                        
                        if subscription:
                            django_user = subscription.user
                            django_user.telegram_user_id = user.id
                            django_user.save()
                            logger.info(f"Stored Telegram ID {user.id} for user {django_user.email}")
                            return django_user.email, django_user.id
                    except Exception as e:
                        logger.error(f"Error saving telegram ID: {e}")
                    return None, None
                
                user_email, django_user_id = await save_telegram_id()
                
                welcome_message = f"""
🤖 **Welcome to OxiWord Bot!**

Hello {user.first_name}, I'm your OxiWorld Forex Academy assistant.

✅ **Registration Complete!** Your Telegram account is now linked.

**Available Commands:**
• /status - Check your subscription and group access
• /help - Show all commands  
• /support - Get support information

I'll automatically add you to appropriate groups based on your active subscription.

Happy trading! 📈
                """
                
                if user_email and django_user_id:
                    welcome_message += f"\n\n🔗 **Linked Account**: {user_email}"
                    
                    # Trigger immediate subscription check for this user
                    result = await self.check_and_add_user_to_groups(django_user_id, user.id)
                    
                    # If user was added to groups, let them know
                    if "✅" in result:
                        await update.message.reply_text(
                            f"🎉 **Group Access Granted!**\n\n{result}",
                            parse_mode='Markdown'
                        )
                    
            except Exception as e:
                logger.error(f"Error in start command: {e}")
                welcome_message = f"""
🤖 **Welcome to OxiWord Bot!**

Hello {user.first_name}, I'm your OxiWorld Forex Academy assistant.

**Available Commands:**
• /status - Check your subscription and group access
• /help - Show all commands  
• /support - Get support information

To access premium groups, make sure you have an active subscription at oxiworld.com and that your Telegram username matches your subscription profile.

Happy trading! 📈
                """
        else:
            welcome_message = """
🤖 **Welcome to OxiWord Bot!**

⚠️ **Please set a Telegram username first!**

To use this bot, you need to:
1. Go to Telegram Settings
2. Set a username (like @yourname)
3. Make sure it matches your OxiWorld subscription
4. Come back and use /start again

This helps us securely link your account.
            """
        
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
        
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
            from asgiref.sync import sync_to_async
            
            @sync_to_async
            def get_subscription():
                return SignalSubscription.objects.filter(
                    telegram_username=telegram_username,
                    payment_status='verified'
                ).first()
                
            subscription = await get_subscription()
            
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
🤖 **OxiWord Bot Commands**

**User Commands:**
• /start - Welcome message and registration
• /status - Check your subscription and group access  
• /help - Show this help message
• /support - Get support contact information

**How It Works:**
1. Subscribe at oxiworld.com
2. Enter your Telegram username in your profile
3. Use /start to register with this bot
4. You'll receive invite links to appropriate groups
5. Access is managed automatically based on subscription

**Subscription Levels:**
• **Basic** → Mentorship Group access
• **Premium** → Mentorship + Signals Groups  
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
• **Username issues?** Make sure your Telegram username is set and matches your profile

**Business Hours**: Monday - Friday, 9 AM - 6 PM UTC

We're here to help! 🚀
        """
        await update.message.reply_text(support_text, parse_mode='Markdown')
        
    # Admin Commands
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
            
    async def admin_create_invite(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Create invite link for a user"""
        if not await self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized. Admin access required.")
            return
            
        try:
            args = context.args
            if len(args) < 2:
                await update.message.reply_text(
                    "Usage: /admin_invite <telegram_username> <group_key>\n"
                    "Groups: education_group, premium_signals, vip_community"
                )
                return
                
            username = args[0].replace('@', '')
            group_key = args[1]
            
            result = await self.create_invite_for_user(username, group_key)
            await update.message.reply_text(result)
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    # Core Functions
    async def add_user_directly_to_group(self, telegram_user_id: int, telegram_username: str, group_key: str) -> str:
        """Add user directly to specific group"""
        try:
            group_info = self.groups.get(group_key)
            if not group_info:
                return f"❌ Group '{group_key}' not found"
                
            chat_id = group_info['chat_id']
            group_name = group_info['name']
            
            try:
                # Add user directly to the group
                await self.bot.add_chat_member(
                    chat_id=chat_id,
                    user_id=telegram_user_id
                )
                
                # Send welcome message to the group
                welcome_msg = f"""
{self.get_welcome_message(group_key)}

🎉 **Welcome @{telegram_username}!**
                """
                
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=welcome_msg,
                    parse_mode='Markdown'
                )
                
                logger.info(f"Successfully added user {telegram_user_id} (@{telegram_username}) to {group_name}")
                
                return f"✅ Successfully added @{telegram_username} to {group_name}"
                
            except Forbidden:
                return f"❌ Bot lacks permission to add users to {group_name}"
            except BadRequest as e:
                if "user is already a participant" in str(e).lower():
                    return f"✅ @{telegram_username} is already in {group_name}"
                return f"❌ Failed to add user to {group_name}: {e}"
                
        except Exception as e:
            logger.error(f"Error adding user {telegram_user_id} (@{telegram_username}) to {group_key}: {e}")
            return f"❌ Error: {e}"
    
    async def remove_user_from_group(self, telegram_user_id: int, telegram_username: str, group_key: str) -> str:
        """Remove user from specific group"""
        try:
            group_info = self.groups.get(group_key)
            if not group_info:
                return f"❌ Group '{group_key}' not found"
                
            chat_id = group_info['chat_id']
            group_name = group_info['name']
            
            try:
                # Remove user from the group
                await self.bot.ban_chat_member(
                    chat_id=chat_id,
                    user_id=telegram_user_id
                )
                
                # Immediately unban to allow future re-joining
                await self.bot.unban_chat_member(
                    chat_id=chat_id,
                    user_id=telegram_user_id
                )
                
                logger.info(f"Successfully removed user {telegram_user_id} (@{telegram_username}) from {group_name}")
                
                return f"✅ Successfully removed @{telegram_username} from {group_name}"
                
            except Forbidden:
                return f"❌ Bot lacks permission to remove users from {group_name}"
            except BadRequest as e:
                if "user not found" in str(e).lower():
                    return f"✅ @{telegram_username} was not in {group_name}"
                return f"❌ Failed to remove user from {group_name}: {e}"
                
        except Exception as e:
            logger.error(f"Error removing user {telegram_user_id} (@{telegram_username}) from {group_key}: {e}")
            return f"❌ Error: {e}"
    
    async def check_and_add_user_to_groups(self, user_id: int, telegram_user_id: int = None) -> str:
        """Check user subscription status and add to appropriate groups"""
        try:
            from django.contrib.auth.models import User
            from subscriptions.models import SignalSubscription
            from asgiref.sync import sync_to_async
            
            # Get user from database
            user = await sync_to_async(User.objects.get)(id=user_id)
            
            # Check if user has telegram_user_id
            if not telegram_user_id and hasattr(user, 'telegram_user_id'):
                telegram_user_id = user.telegram_user_id
                
            if not telegram_user_id:
                return f"❌ No Telegram user ID available for {user.username}. User must start the bot first with /start"
            
            # Get user's subscriptions
            subscriptions = await sync_to_async(list)(
                SignalSubscription.objects.filter(user=user, is_active=True)
            )
            
            if not subscriptions:
                return f"❌ User {user.username} has no active subscriptions"
            
            results = []
            telegram_username = user.username if hasattr(user, 'username') else f"user_{user_id}"
            
            for subscription in subscriptions:
                plan_type = subscription.subscription_plan.plan_type.upper()
                
                # Map subscription types to access levels
                access_level_mapping = {
                    'BASIC': 'basic',
                    'MENTORSHIP': 'basic',  # Mentorship-only maps to basic access
                    'SIGNAL': 'signals',    # Signals-only (new dedicated level)
                    'SIGNALS': 'signals',   # Alternative naming
                    'PREMIUM': 'premium',   # Mentorship + Signals
                    'VIP': 'vip'           # All groups
                }
                
                access_level = access_level_mapping.get(plan_type, 'basic')
                accessible_groups = self.group_access.get(access_level, [])
                
                # Add user to all accessible groups for this subscription
                for group_key in accessible_groups:
                    result = await self.add_user_directly_to_group(
                        telegram_user_id, 
                        telegram_username, 
                        group_key
                    )
                    results.append(f"**{plan_type} → {group_key.upper()}**: {result}")
            
            return "\n".join(results)
            
        except Exception as e:
            logger.error(f"Error checking user {user_id}: {e}")
            return f"❌ Error: {e}"
    
    async def remove_user_from_all_groups(self, user_id: int, telegram_user_id: int = None) -> str:
        """Remove user from all groups (for expired/cancelled subscriptions)"""
        try:
            from django.contrib.auth.models import User
            from asgiref.sync import sync_to_async
            
            # Get user from database
            user = await sync_to_async(User.objects.get)(id=user_id)
            
            # Check if user has telegram_user_id
            if not telegram_user_id and hasattr(user, 'telegram_user_id'):
                telegram_user_id = user.telegram_user_id
                
            if not telegram_user_id:
                return f"❌ No Telegram user ID available for {user.username}"
            
            results = []
            telegram_username = user.username if hasattr(user, 'username') else f"user_{user_id}"
            
            # Remove from all groups
            for group_key in ['vip', 'signals', 'mentorship']:
                result = await self.remove_user_from_group(
                    telegram_user_id, 
                    telegram_username, 
                    group_key
                )
                results.append(f"**{group_key.upper()}**: {result}")
            
            return "\n".join(results)
            
        except Exception as e:
            logger.error(f"Error removing user {user_id} from groups: {e}")
            return f"❌ Error: {e}"
    
    # Subscription Management Integration
    async def process_subscription_updates(self):
        """Process pending subscription updates from Django queue"""
        try:
            from asgiref.sync import sync_to_async
            
            # Get pending additions using sync_to_async
            @sync_to_async
            def get_pending_additions():
                return list(TelegramGroupManagement.objects.filter(
                    action_type='add',
                    status='pending'
                )[:5])  # Process 5 at a time
                
            pending_additions = await get_pending_additions()
            
            for task in pending_additions:
                try:
                    subscription = task.signal_subscription
                    plan_type = self.get_plan_type(subscription)
                    accessible_groups = self.group_access.get(plan_type, [])
                    
                    # Add user directly to all accessible groups
                    added_groups = []
                    
                    # Get user's telegram_user_id from the subscription or linked Django user
                    telegram_user_id = None
                    if hasattr(subscription, 'user') and hasattr(subscription.user, 'telegram_user_id'):
                        telegram_user_id = subscription.user.telegram_user_id
                    
                    if telegram_user_id:
                        for group_key in accessible_groups:
                            result = await self.add_user_directly_to_group(
                                telegram_user_id,
                                subscription.telegram_username, 
                                group_key
                            )
                            if "✅" in result:
                                added_groups.append(group_key)
                                
                        # Update task status
                        if added_groups:
                            task.status = 'completed'
                            task.admin_notes = f"Added to groups: {', '.join(added_groups)}"
                            subscription.telegram_status = 'added'
                        else:
                            task.status = 'failed'
                            task.admin_notes = "Failed to add to groups - check bot permissions"
                    else:
                        task.status = 'failed'
                        task.admin_notes = "User must start bot first to get Telegram ID"
                        
                    task.processed_at = timezone.now()
                    await sync_to_async(task.save)()
                    await sync_to_async(subscription.save)()
                    
                except Exception as e:
                    task.status = 'failed'
                    task.admin_notes = str(e)
                    task.processed_at = timezone.now()
                    await sync_to_async(task.save)()
                    logger.error(f"Error processing addition task {task.id}: {e}")
            
            # Process removal tasks - now we can auto-remove users
            @sync_to_async
            def get_pending_removals():
                return list(TelegramGroupManagement.objects.filter(
                    action_type='remove',
                    status='pending'
                )[:5])
                
            pending_removals = await get_pending_removals()
            
            for task in pending_removals:
                try:
                    subscription = task.signal_subscription
                    
                    # Get user's telegram_user_id from the subscription or linked Django user
                    telegram_user_id = None
                    if hasattr(subscription, 'user') and hasattr(subscription.user, 'telegram_user_id'):
                        telegram_user_id = subscription.user.telegram_user_id
                    
                    if telegram_user_id:
                        # Remove from all groups
                        result = await self.remove_user_from_all_groups(
                            subscription.user.id,
                            telegram_user_id
                        )
                        
                        task.status = 'completed'
                        task.admin_notes = "User removed from all groups"
                        subscription.telegram_status = 'removed'
                    else:
                        task.status = 'completed'
                        task.admin_notes = "No Telegram ID found - manual removal may be needed"
                        subscription.telegram_status = 'removed'
                    
                    task.processed_at = timezone.now()
                    await sync_to_async(task.save)()
                    await sync_to_async(subscription.save)()
                    
                except Exception as e:
                    task.status = 'failed'
                    task.admin_notes = f"Removal error: {str(e)}"
                    task.processed_at = timezone.now()
                    await sync_to_async(task.save)()
                    logger.error(f"Error processing removal task {task.id}: {e}")
                    
        except Exception as e:
            logger.error(f"Error processing subscription updates: {e}")
    
    # Helper Functions
    def get_plan_type(self, subscription: SignalSubscription) -> str:
        """Determine plan type from subscription"""
        if hasattr(subscription, 'plan_type'):
            return subscription.plan_type.lower()
        elif hasattr(subscription, 'amount_paid'):
            amount = float(subscription.amount_paid)
            if amount >= 199:  # VIP threshold - highest tier (all groups)
                return 'vip'
            elif amount >= 99:   # Premium threshold - mentorship + signals
                return 'premium'  
            elif amount >= 29:   # Signals-only threshold - new dedicated level
                return 'signals'
            else:
                return 'basic'   # Basic/mentorship only
        else:
            return 'basic'  # Default fallback
    
    def get_welcome_message(self, group_key: str) -> str:
        """Get appropriate welcome message for each group"""
        messages = {
            'mentorship': """
🎓 **Welcome to OxiWorld Mentorship!**

Here you'll get:
• Educational content and tutorials
• Market analysis and insights  
• Trading psychology guidance
• Q&A sessions with experts
• Community discussions

Let's learn and grow together! 📚
            """,
            'signals': """
📈 **Welcome to OxiWorld Signals!**

Here you'll receive:
• Live trading signals
• Entry and exit points
• Risk management tips
• Market updates
• Performance tracking

Ready to trade with confidence! 🚀
            """,
            'vip': """
💎 **Welcome to OxiWorld VIP Community!**

Exclusive access to:
• Premium strategies and insights
• Direct access to senior analysts
• Advanced market analysis
• Priority support
• Special events and webinars

Welcome to the elite circle! ⭐
            """
        }
        return messages.get(group_key, "Welcome to OxiWorld! 🌍")
    
    async def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        # Add your admin user IDs here - get your ID by messaging the bot
        admin_ids = [123456789]  # Replace with actual admin Telegram IDs
        return user_id in admin_ids
    
    async def get_bot_stats(self) -> str:
        """Get bot statistics"""
        try:
            from asgiref.sync import sync_to_async
            
            # Get stats from Django models
            @sync_to_async
            def get_stats():
                return {
                    'total': SignalSubscription.objects.filter(payment_status='verified').count(),
                    'active': SignalSubscription.objects.filter(
                        payment_status='verified',
                        subscription_end__gt=timezone.now()
                    ).count(),
                    'pending': TelegramGroupManagement.objects.filter(status='pending').count(),
                    'completed': TelegramGroupManagement.objects.filter(
                        status='completed',
                        processed_at__gte=timezone.now().date()
                    ).count()
                }
            
            stats = await get_stats()
            total_subscriptions = stats['total']
            active_subscriptions = stats['active'] 
            pending_tasks = stats['pending']
            completed_today = stats['completed']
            
            stats_msg = f"""
📊 **OxiWord Bot Statistics**

**Subscriptions:**
• Total Verified: {total_subscriptions}
• Currently Active: {active_subscriptions}

**Queue Status:**
• Pending Tasks: {pending_tasks}
• Completed Today: {completed_today}

**Bot Info:**
• Groups Managed: {len(self.groups)}
• Users Registered: {len(self.user_ids)}

**Groups:**
            """
            
            for group_key, group_info in self.groups.items():
                stats_msg += f"\n• {group_info['name']}: {group_info['chat_id']}"
            
            return stats_msg
            
        except Exception as e:
            return f"❌ Error getting statistics: {e}"
    
    async def run_bot(self):
        """Main bot runner"""
        try:
            await self.initialize()
            
            logger.info("OxiWord Bot starting...")
            
            # Start the bot
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            logger.info("OxiWord Bot started successfully! Processing queue every 30 seconds...")
            
            # Keep running and process subscription updates periodically
            while True:
                await asyncio.sleep(30)  # Check every 30 seconds
                await self.process_subscription_updates()
                
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Error running bot: {e}")
        finally:
            # Safely stop the application
            try:
                if self.application:
                    await self.application.updater.stop()
                    await self.application.stop()
                    logger.info("Bot stopped cleanly")
            except Exception as stop_error:
                logger.warning(f"Error during shutdown: {stop_error}")

# Main execution
async def main():
    """Main function to run the bot"""
    oxiword_bot = OxiWordBotSimple()
    await oxiword_bot.run_bot()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")