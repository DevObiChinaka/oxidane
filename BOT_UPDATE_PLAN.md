# Telegram Bot Update Plan

## Current State Analysis:
- Bot currently uses hardcoded price thresholds in `get_plan_type()` method
- Uses fixed group access mapping
- Plans are determined by amount paid rather than actual plan selection

## Required Updates:

### 1. Update Bot to Use PricingPlan Model

Update the bot to fetch plan information from the database instead of hardcoded values.

### Current Code (oxiword_bot_simple.py lines 613+):
```python
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
```

### New Dynamic Code:
```python
def get_plan_access(self, subscription: SignalSubscription) -> dict:
    """Get plan access information from PricingPlan model"""
    try:
        from subscriptions.models import PricingPlan
        
        # If subscription has a linked pricing plan, use that
        if hasattr(subscription, 'pricing_plan') and subscription.pricing_plan:
            plan = subscription.pricing_plan
            return {
                'plan_name': plan.name,
                'plan_category': plan.plan_category,
                'telegram_groups': plan.telegram_groups,
                'access_level': self.determine_access_level(plan)
            }
        
        # Fallback: try to find plan by plan_type field
        if hasattr(subscription, 'plan_type') and subscription.plan_type:
            try:
                plan = PricingPlan.objects.get(
                    plan_type=subscription.plan_type,
                    is_active=True
                )
                return {
                    'plan_name': plan.name,
                    'plan_category': plan.plan_category,
                    'telegram_groups': plan.telegram_groups,
                    'access_level': self.determine_access_level(plan)
                }
            except PricingPlan.DoesNotExist:
                pass
        
        # Ultimate fallback: use amount-based detection
        return self.get_legacy_plan_access(subscription)
        
    except Exception as e:
        logger.error(f"Error getting plan access: {e}")
        return self.get_legacy_plan_access(subscription)

def determine_access_level(self, plan: 'PricingPlan') -> str:
    """Determine access level from plan category and groups"""
    if plan.plan_category == 'vip':
        return 'vip'
    elif plan.plan_category == 'signals':
        return 'signals'
    elif plan.plan_category == 'mentorship':
        return 'basic'
    else:
        # Determine by telegram groups
        groups = plan.telegram_groups or []
        if 'vip' in groups:
            return 'vip'
        elif 'signals' in groups:
            return 'signals'
        else:
            return 'basic'

def get_legacy_plan_access(self, subscription: SignalSubscription) -> dict:
    """Legacy fallback method using amount-based detection"""
    if hasattr(subscription, 'amount_paid'):
        amount = float(subscription.amount_paid)
        if amount >= 199:
            return {
                'plan_name': 'VIP (Legacy)',
                'plan_category': 'vip',
                'telegram_groups': ['mentorship', 'signals', 'vip'],
                'access_level': 'vip'
            }
        elif amount >= 99:
            return {
                'plan_name': 'Premium (Legacy)',
                'plan_category': 'signals',
                'telegram_groups': ['mentorship', 'signals'],
                'access_level': 'premium'
            }
        elif amount >= 29:
            return {
                'plan_name': 'Signals (Legacy)',
                'plan_category': 'signals',
                'telegram_groups': ['signals'],
                'access_level': 'signals'
            }
    
    return {
        'plan_name': 'Basic (Legacy)',
        'plan_category': 'mentorship',
        'telegram_groups': ['mentorship'],
        'access_level': 'basic'
    }
```

### 2. Update Group Access Logic

Replace the hardcoded group_access mapping with dynamic lookups:

```python
# Current hardcoded mapping:
self.group_access = {
    'basic': ['mentorship'],
    'signals': ['signals'],
    'premium': ['mentorship', 'signals'],
    'vip': ['mentorship', 'signals', 'vip']
}

# New dynamic method:
def get_user_groups(self, subscription: SignalSubscription) -> list:
    """Get telegram groups user should have access to"""
    plan_access = self.get_plan_access(subscription)
    return plan_access['telegram_groups']
```

### 3. Update Status Command

Enhance the status command to show dynamic plan information:

```python
async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... existing code ...
    
    plan_access = self.get_plan_access(subscription)
    user_groups = plan_access['telegram_groups']
    
    status_msg = f"""
📊 **Your Subscription Status**

**Plan**: {plan_access['plan_name']}
**Category**: {plan_access['plan_category'].title()}
**Status**: {'✅ Active' if is_active else '❌ Expired'}
**Expires**: {subscription.subscription_end.strftime('%B %d, %Y')}

**Access Groups**: {', '.join(user_groups) if user_groups else 'None'}
**Telegram Status**: {subscription.telegram_status}
**Payment Status**: {subscription.payment_status}
    """
```

### 4. Update Help Command

Make the help command show current pricing from the database:

```python
async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help information with current pricing"""
    try:
        from subscriptions.models import PricingPlan
        
        # Get featured plans for display
        featured_plans = PricingPlan.objects.filter(
            is_active=True,
            is_featured=True
        ).order_by('sort_order')[:3]
        
        plans_text = ""
        for plan in featured_plans:
            plans_text += f"• **{plan.name}** - ${plan.price}/{plan.billing_cycle}\n"
        
        help_text = f"""
🤖 **OxiWord Bot Commands**

**User Commands:**
• /start - Welcome message and registration
• /status - Check your subscription and group access  
• /help - Show this help message
• /support - Get support contact information

**Current Featured Plans:**
{plans_text}

**How It Works:**
1. Subscribe at oxiworld.com
2. Enter your Telegram username in your profile
3. Use /start to register with this bot
4. You'll receive invite links to appropriate groups
5. Access is managed automatically based on subscription

**Need Help?**
Use /support for contact information or visit oxiworld.com
        """
        
    except Exception as e:
        # Fallback to static message
        help_text = """
🤖 **OxiWord Bot Commands**
[... existing static help text ...]
        """
    
    await update.message.reply_text(help_text, parse_mode='Markdown')
```

## Implementation Priority:
1. ✅ Backend API endpoints (already done)
2. 🟡 Update bot to use PricingPlan model
3. 🟡 Update frontend to use dynamic API
4. 🟡 Test end-to-end flow

## Testing Steps:
1. Create test subscriptions with different plans
2. Verify bot correctly identifies plan access
3. Verify group assignments work correctly
4. Test fallback for legacy subscriptions