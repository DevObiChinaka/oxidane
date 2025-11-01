# Dual Subscription System Architecture
# OxiWorld Forex Academy - Mentorship + Signals

## 🎯 PROPOSED DUAL SUBSCRIPTION MODEL

### Current Status Analysis:
- ✅ Signal Subscriptions: FULLY IMPLEMENTED
- ❌ Mentorship Subscriptions: NOT IMPLEMENTED YET
- ✅ Telegram Bot Integration: WORKING
- ✅ Payment System: PAYSTACK INTEGRATED

## 🚀 MENTORSHIP SUBSCRIPTION IMPLEMENTATION PLAN

### Phase 5A: Add Mentorship Subscription Type

#### 1. Database Schema Extension
```python
class SubscriptionType(models.Model):
    SIGNAL = 'signal'
    MENTORSHIP = 'mentorship'
    COMBO = 'combo'  # Both signals + mentorship
    
    TYPE_CHOICES = [
        (SIGNAL, 'Trading Signals'),
        (MENTORSHIP, '1-on-1 Mentorship'),
        (COMBO, 'Signals + Mentorship'),
    ]

class Subscription(models.Model):
    # Extend existing model
    subscription_type = models.CharField(max_length=20, choices=SubscriptionType.TYPE_CHOICES, default='signal')
    
    # Mentorship specific fields
    mentor_assigned = models.ForeignKey('User', null=True, blank=True, related_name='mentees')
    mentorship_level = models.CharField(max_length=20, choices=[
        ('basic', 'Basic Mentorship - 2 sessions/month'),
        ('premium', 'Premium Mentorship - 4 sessions/month'),
        ('vip', 'VIP Mentorship - 8 sessions/month + WhatsApp'),
    ])
    
    # Session tracking
    monthly_sessions_limit = models.IntegerField(default=0)
    sessions_used_this_month = models.IntegerField(default=0)
    
    # Mentorship Telegram groups (different from signal groups)
    mentorship_telegram_group = models.CharField(max_length=100, blank=True)
```

#### 2. Subscription Plans Matrix
```python
SUBSCRIPTION_PLANS = {
    # Signal-Only Plans
    'signal_weekly': {
        'type': 'signal',
        'duration_days': 7,
        'price_ngn': 5000,
        'telegram_groups': ['signals_basic'],
        'features': ['Basic signals', 'Market analysis', 'Entry/Exit alerts']
    },
    'signal_monthly': {
        'type': 'signal', 
        'duration_days': 30,
        'price_ngn': 15000,
        'telegram_groups': ['signals_premium'],
        'features': ['Premium signals', 'Market analysis', 'Risk management tips']
    },
    'signal_vip': {
        'type': 'signal',
        'duration_days': 30, 
        'price_ngn': 30000,
        'telegram_groups': ['signals_vip', 'vip_analysis'],
        'features': ['VIP signals', 'Live market sessions', 'Priority support']
    },
    
    # Mentorship-Only Plans
    'mentorship_basic': {
        'type': 'mentorship',
        'duration_days': 30,
        'price_ngn': 25000,
        'sessions_per_month': 2,
        'telegram_groups': ['mentorship_basic'],
        'features': ['2 1-on-1 sessions', 'Trading plan review', 'Basic mentorship group']
    },
    'mentorship_premium': {
        'type': 'mentorship',
        'duration_days': 30,
        'price_ngn': 45000, 
        'sessions_per_month': 4,
        'telegram_groups': ['mentorship_premium', 'mentor_chat'],
        'features': ['4 1-on-1 sessions', 'Portfolio analysis', 'Premium mentorship group']
    },
    'mentorship_vip': {
        'type': 'mentorship',
        'duration_days': 30,
        'price_ngn': 75000,
        'sessions_per_month': 8,
        'telegram_groups': ['mentorship_vip', 'mentor_direct'],
        'whatsapp_access': True,
        'features': ['8 1-on-1 sessions', 'WhatsApp access', 'VIP mentorship group', 'Trading psychology coaching']
    },
    
    # Combo Plans (Signals + Mentorship)
    'combo_premium': {
        'type': 'combo',
        'duration_days': 30,
        'price_ngn': 55000,
        'sessions_per_month': 2,
        'telegram_groups': ['signals_premium', 'mentorship_basic', 'combo_premium'],
        'features': ['Premium signals', '2 mentorship sessions', 'Combo exclusive group']
    },
    'combo_vip': {
        'type': 'combo',
        'duration_days': 30,
        'price_ngn': 95000,
        'sessions_per_month': 4,
        'telegram_groups': ['signals_vip', 'mentorship_vip', 'combo_vip'],
        'whatsapp_access': True,
        'features': ['VIP signals', '4 mentorship sessions', 'WhatsApp access', 'All exclusive groups']
    }
}
```

#### 3. Telegram Group Assignment Logic
```python
class TelegramBotService:
    TELEGRAM_GROUPS = {
        # Signal Groups
        'signals_basic': {'id': '@oxiworld_signals_basic', 'type': 'signal'},
        'signals_premium': {'id': '@oxiworld_signals_premium', 'type': 'signal'},
        'signals_vip': {'id': '@oxiworld_signals_vip', 'type': 'signal'},
        'vip_analysis': {'id': '@oxiworld_vip_analysis', 'type': 'signal'},
        
        # Mentorship Groups  
        'mentorship_basic': {'id': '@oxiworld_mentorship_basic', 'type': 'mentorship'},
        'mentorship_premium': {'id': '@oxiworld_mentorship_premium', 'type': 'mentorship'},
        'mentorship_vip': {'id': '@oxiworld_mentorship_vip', 'type': 'mentorship'},
        'mentor_chat': {'id': '@oxiworld_mentor_chat', 'type': 'mentorship'},
        'mentor_direct': {'id': '@oxiworld_mentor_direct', 'type': 'mentorship'},
        
        # Combo Groups
        'combo_premium': {'id': '@oxiworld_combo_premium', 'type': 'combo'},
        'combo_vip': {'id': '@oxiworld_combo_vip', 'type': 'combo'},
    }
    
    def add_user_to_subscription_groups(self, user, subscription):
        """Add user to appropriate Telegram groups based on subscription type"""
        plan = SUBSCRIPTION_PLANS[subscription.plan_type]
        
        for group_name in plan['telegram_groups']:
            try:
                group_info = self.TELEGRAM_GROUPS[group_name]
                result = self.bot.add_chat_member(
                    chat_id=group_info['id'],
                    user_id=user.telegram_id
                )
                
                # Log successful addition
                subscription.telegram_groups_added.append(group_name)
                
            except Exception as e:
                # Log failed addition
                subscription.telegram_groups_failed.append({
                    'group': group_name,
                    'error': str(e),
                    'timestamp': timezone.now()
                })
        
        subscription.save()
```

## 🎯 IMPLEMENTATION QUESTIONS FOR YOU:

### 1. **Subscription Types Priority**
- Should we implement **Mentorship subscriptions** alongside the existing Signal subscriptions?
- Do you want **Combo plans** (Signals + Mentorship) as well?

### 2. **Telegram Group Structure**  
- How many **different Telegram groups** do you want?
  - Separate groups for: Basic Signals, Premium Signals, VIP Signals
  - Separate groups for: Basic Mentorship, Premium Mentorship, VIP Mentorship  
  - Combo groups for users with both subscriptions?

### 3. **Mentorship Features**
- **Session booking system**: Do users need to book mentorship sessions?
- **Mentor assignment**: Automatic or manual assignment of mentors?
- **Session limits**: Should we track sessions used per month?
- **WhatsApp integration**: VIP users get direct WhatsApp access?

### 4. **Pricing Strategy**
- What are your **pricing tiers** for mentorship vs signals?
- Should mentorship be more expensive than signals?
- Any **bundle discounts** for combo subscriptions?

## 🚀 NEXT STEPS OPTIONS:

### Option A: **Extend Current System** 
- Add mentorship subscription types to existing models
- Implement multi-group Telegram assignment  
- Create mentorship-specific admin tools
- Add session tracking and booking system

### Option B: **Focus on Signal Enhancement**
- Improve existing signal subscription features
- Add more signal group tiers
- Enhance Telegram bot functionality 
- Add signal analytics and performance tracking

### Option C: **Complete Dual System**
- Implement both mentorship and enhanced signals
- Create sophisticated group assignment logic
- Build comprehensive admin dashboard
- Add session management and mentor tools

## ❓ WHAT'S YOUR PREFERENCE?

Which direction should we take for **Phase 5**? 

1. **Dual System** (Signals + Mentorship)?
2. **Focus on Signals** enhancement?
3. **Mentorship-first** approach?
4. **Complete redesign** of subscription architecture?

Let me know your vision and I'll implement accordingly! 🎯