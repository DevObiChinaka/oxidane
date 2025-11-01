# 🤖 OXIWORD BOT - REFINED SETUP PLAN

**Bot Name**: OxiWord Bot  
**Primary Function**: User Management & Access Control  
**Launch Strategy**: Hard Launch (Full deployment)  
**Date**: October 5, 2025  

---

## 🎯 **BOT SPECIFICATIONS**

### **Bot Identity:**
- **Name**: `OxiWord Bot`
- **Username**: `@oxiword_bot` (recommended) or `@oxiworldbot`
- **Profile**: Your logo (ready ✅)
- **Purpose**: Automated user management for subscription-based Telegram groups

### **Core Functions:**
1. 🔐 **User Access Management** - Add/remove users based on subscription status
2. 👋 **Automated Welcome Messages** - Greet new members with group-specific content
3. ⚡ **Subscription Enforcement** - Strict subscription verification
4. 📧 **Expiration Warnings** - 3-day advance warning via email (not Telegram)
5. 🚫 **Auto-Removal** - Remove users when subscriptions expire

---

## 📱 **GROUP STRUCTURE & BOT ACCESS**

### **Groups with Bot Access:**

#### **1. 🏆 Mentorship Group**
- **Access Level**: Premium+ subscribers
- **Bot Role**: User management, welcome messages
- **Content**: Manual by site owner
- **Bot Permissions**: Add/Remove users, Send messages, Delete spam

#### **2. 📊 Signals Group** 
- **Access Level**: Basic+ subscribers  
- **Bot Role**: User management, welcome messages
- **Content**: Manual signals by site owner
- **Bot Permissions**: Add/Remove users, Send messages, Pin important signals

#### **3. 💎 VIP Signals Group**
- **Access Level**: VIP subscribers only
- **Bot Role**: User management, welcome messages  
- **Content**: Exclusive manual signals by site owner
- **Bot Permissions**: Add/Remove users, Send messages, Delete spam

#### **4. 🌍 Community Group**
- **Access Level**: All subscribers (Basic+)
- **Bot Role**: User management, moderation, welcome messages
- **Content**: Community discussions (minimal bot involvement)
- **Bot Permissions**: Add/Remove users, Moderate discussions, Welcome new members

### **Groups WITHOUT Bot Access:**

#### **5. 🔒 Admin Group**
- **Access Level**: Admin team only
- **Bot Role**: None (off-limits as requested)
- **Content**: Internal admin coordination
- **Bot Permissions**: No access

---

## ⚙️ **SUBSCRIPTION MANAGEMENT SYSTEM**

### **Subscription Tiers → Group Access:**

```python
SUBSCRIPTION_GROUP_ACCESS = {
    'basic': [
        'signals_group',          # Basic trading signals
        'community_group'         # General community discussions
    ],
    'premium': [
        'signals_group',          # Basic trading signals  
        'mentorship_group',       # Educational mentorship
        'community_group'         # General community discussions
    ],
    'vip': [
        'signals_group',          # Basic trading signals
        'vip_signals_group',      # Exclusive VIP signals
        'mentorship_group',       # Educational mentorship  
        'community_group'         # General community discussions
    ]
}
```

### **Strict Subscription Enforcement:**
- ✅ **Real-time verification** before group access
- ✅ **Payment status checking** (verified payments only)
- ✅ **Subscription date validation** (not expired)
- ✅ **Automatic removal** on expiration
- ❌ **No grace period** (except 3-day warning)

---

## 📧 **3-DAY EXPIRATION WARNING SYSTEM**

### **Email Warning Flow:**
```
Day -3: 📧 "Subscription Expires in 3 Days" email
Day -1: 📧 "Subscription Expires Tomorrow" email  
Day 0:  🚫 Auto-removal from Telegram groups + 📧 "Subscription Expired" email
```

### **Enhanced Email Templates Needed:**

#### **1. 3-Day Warning Email** (New Template)
```python
template_type = 'renewal_reminder'
subject = '⚠️ Your OxiWorld Subscription Expires in 3 Days!'
content = """
Dear {user.first_name},

Your OxiWorld subscription is set to expire in 3 days on {subscription_end_date}.

To maintain access to:
• Trading signals groups
• Mentorship sessions  
• VIP community features
• Educational content

Please renew your subscription before expiration.

[RENEW NOW BUTTON]

If you don't renew, you'll be automatically removed from Telegram groups on {subscription_end_date}.

Best regards,
OxiWorld Team
"""
```

#### **2. 1-Day Final Warning** (New Template)
```python
template_type = 'renewal_reminder'
subject = '🚨 Final Warning: Subscription Expires Tomorrow!'
```

#### **3. Post-Expiration Email** (New Template)  
```python
template_type = 'subscription_expired'
subject = '❌ Your OxiWorld Subscription Has Expired'
content = """
Your subscription expired today and you've been removed from premium Telegram groups.

To regain access, please renew your subscription:
[RENEW NOW BUTTON]
"""
```

---

## 🤖 **BOT COMMANDS & AUTOMATION**

### **User Commands:**
```
/start - Welcome message + subscription status check
/status - Check current subscription and group access  
/help - Show available commands and support info
/support - Get support contact information
/groups - Show which groups user has access to
```

### **Admin Commands (for site owner):**
```
/admin_add {username} {group} - Manually add user to group
/admin_remove {username} {group} - Manually remove user  
/admin_status {username} - Check user's subscription status
/admin_broadcast {group} {message} - Send announcement to group
/admin_stats - Show bot statistics and group member counts
```

### **Automated Functions:**
1. **Welcome Messages** - Custom message per group
2. **Subscription Verification** - Before adding to groups
3. **Daily Expiration Check** - Remove expired users
4. **Email Trigger Integration** - Send warning emails via Django
5. **Spam Detection** - Basic anti-spam measures

---

## 📝 **WELCOME MESSAGES PER GROUP**

### **Mentorship Group Welcome:**
```
🎓 Welcome to OxiWorld Mentorship, {first_name}!

You now have access to:
• Exclusive educational content
• Personal mentorship sessions
• Advanced trading strategies
• Direct Q&A with instructors

Please read our group rules and introduce yourself!

Happy learning! 📚
```

### **Signals Group Welcome:**
```
📊 Welcome to OxiWorld Trading Signals, {first_name}!

You now have access to:
• Daily trading signals
• Entry and exit points
• Risk management guidance
• Market analysis updates

Please enable notifications for important signals! 🔔
```

### **VIP Signals Welcome:**
```
💎 Welcome to OxiWorld VIP Signals, {first_name}!

You're now part of our exclusive VIP community:
• Premium trading signals
• Advanced market insights
• Priority support
• Exclusive trading strategies

Welcome to the elite trading circle! 🏆
```

### **Community Group Welcome:**
```
🌍 Welcome to the OxiWorld Community, {first_name}!

Connect with fellow traders:
• Share trading experiences
• Ask questions and get help
• Network with other members
• Stay updated on announcements

Let's grow together! 🚀
```

---

## 🔧 **TECHNICAL IMPLEMENTATION PLAN**

### **Phase 1: BotFather Setup (Today)**
1. Create `OxiWord Bot` with BotFather
2. Set description and commands
3. Upload your logo
4. Get bot token

### **Phase 2: Group Creation (Today)**
1. Create 4 Telegram groups (Mentorship, Signals, VIP Signals, Community)
2. Add bot as administrator with required permissions
3. Collect Chat IDs for each group
4. Test basic bot functionality

### **Phase 3: Django Integration (Day 1-2)**
1. Update `settings.py` with bot token and group IDs
2. Create new email templates for expiration warnings
3. Implement 3-day warning cron job
4. Test subscription → group access automation

### **Phase 4: Bot Programming (Day 2-3)**
1. Implement user management commands
2. Set up welcome message automation
3. Create subscription verification logic
4. Test all bot functions thoroughly

### **Phase 5: Hard Launch (Day 3-4)**
1. Import existing subscribers to appropriate groups
2. Send launch announcement
3. Monitor bot performance
4. Handle initial user feedback

---

## 🚨 **SUBSCRIPTION EXPIRATION AUTOMATION**

### **Daily Cron Job Logic:**
```python
# Daily task (runs at 9:00 AM UTC)
def check_subscription_expiries():
    today = timezone.now().date()
    
    # 3-day warning emails
    expiring_in_3_days = SignalSubscription.objects.filter(
        subscription_end__date=today + timedelta(days=3),
        is_active=True
    )
    for subscription in expiring_in_3_days:
        send_3_day_warning_email(subscription.user)
    
    # 1-day final warning emails  
    expiring_tomorrow = SignalSubscription.objects.filter(
        subscription_end__date=today + timedelta(days=1),
        is_active=True
    )
    for subscription in expiring_tomorrow:
        send_final_warning_email(subscription.user)
    
    # Remove expired users from Telegram groups
    expired_today = SignalSubscription.objects.filter(
        subscription_end__date=today,
        is_active=True
    )
    for subscription in expired_today:
        remove_user_from_all_groups(subscription.user)
        send_expiration_email(subscription.user)
        subscription.is_active = False
        subscription.save()
```

---

## 📊 **BOT ANALYTICS & MONITORING**

### **Key Metrics to Track:**
- 📈 **Daily group member counts**
- 🔄 **User additions/removals per day**
- 📧 **Warning emails sent**
- 💳 **Subscription renewals triggered by warnings**
- ⚡ **Bot command usage statistics**
- 🚫 **Failed operations (for debugging)**

### **Admin Dashboard Integration:**
Your existing Django admin can show:
- Real-time bot status
- Group member statistics  
- Recent bot activities
- Failed operations log
- Warning email delivery status

---

## 🎯 **HARD LAUNCH STRATEGY**

### **Pre-Launch Checklist:**
- [ ] Bot created and configured
- [ ] All 4 groups set up with proper permissions
- [ ] Welcome messages tested
- [ ] Subscription verification working
- [ ] Email warning system functional
- [ ] Admin commands tested
- [ ] Emergency stop procedures ready

### **Launch Day Execution:**
1. **09:00** - Final systems check
2. **10:00** - Import existing subscribers to groups
3. **11:00** - Send launch announcement email
4. **12:00** - Post on social media about new Telegram access
5. **Ongoing** - Monitor bot performance and user feedback

### **Post-Launch Monitoring (First 48 Hours):**
- Bot response times
- User addition success rate
- Welcome message delivery
- Group activity levels
- Support ticket volume
- System error logs

---

## 💬 **DISCUSSION POINTS**

### **Questions for You:**

1. **Bot Username Preference:**
   - `@oxiword_bot` ✅ (clean and simple)
   - `@oxiworldbot` (alternative)
   - Other preference?

2. **Group Privacy Settings:**
   - Should all groups be **private** (no public username)?
   - Or public usernames for easier discovery?

3. **Content Posting:**
   - Will you post directly in groups or through the bot?
   - Should bot pin your important messages automatically?

4. **Emergency Procedures:**
   - Should there be a manual override for subscription checks?
   - Emergency contact method if bot malfunctions?

5. **User Support:**
   - Should bot handle basic support queries?
   - Redirect all support to email/website?

---

## 🚀 **READY TO START?**

Your vision is crystal clear and your existing Django system is perfectly positioned for this integration! The hard launch approach will create immediate impact and show the full value of your premium Telegram community.

**Next immediate steps:**
1. **Create the bot** with BotFather using the name "OxiWord Bot"
2. **Set up the 4 groups** (Mentorship, Signals, VIP Signals, Community)
3. **Get the bot token and group Chat IDs**
4. **I'll help you integrate** everything with your Django system

**Ready to create the bot with BotFather? I can walk you through each step!** 🤖✨