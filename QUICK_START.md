# ⚡ QUICK START GUIDE

**Use this file when you need instant answers without reading the full roadmap.**

---

## 🎯 WHERE AM I?

**Check your current phase:**
1. Open GitHub Copilot chat
2. Type: `Show me the todo list`
3. Look for tasks marked "in-progress" or first uncompleted task

**Or check git:**
```powershell
git log --oneline -1
```
Your last commit message tells you what you completed.

---

## 🚀 STARTING A NEW CHAT SESSION

**Copy and paste this template:**

```
I'm working on the enterprise subscription platform (white-label SaaS).

PROJECT: Django 5.2 + PostgreSQL + Redis + Celery + Next.js
BRANCH: enterprise-platform-v1
ROADMAP: 150 hours, 11 phases

PLEASE READ:
1. ENTERPRISE_PLATFORM_ROADMAP.md
2. CONTEXT_FOR_NEW_CHAT.md

CURRENT STATUS:
- Phase: [Check todo list]
- Last completed: [Check git log]
- Working on: [First uncompleted task]

What should I do next?
```

---

## 📋 PHASE QUICK REFERENCE

### **Phase 0: Preparation** (~4 hours)
**Goal:** Set up infrastructure  
**Deliverables:** PostgreSQL, Redis, branch, dependencies installed  
**Key Files:** None  
**Next Phase:** 0.5  

---

### **Phase 0.5: Dynamic Plans** (~20 hours)
**Goal:** Create subscription system with admin config  
**Deliverables:** 11 models, admin APIs, admin UI, seed commands  
**Key Files:**
- `backend/subscriptions/models.py` (add 11 models)
- `backend/subscriptions/encryption.py` (create)
- `backend/subscriptions/views/admin_views.py` (update)
- `frontend/src/app/admin/plans/page.tsx` (create)

**Models to Create:**
1. Feature
2. SubscriptionPlan
3. Subscription (update)
4. Coupon
5. CouponUsage
6. ReferralCode
7. Referral
8. TelegramConfiguration
9. TelegramGroup
10. PaymentConfiguration
11. EmailConfiguration

**Next Phase:** 0.6  

---

### **Phase 0.6: API Keys & Webhooks** (~10 hours)
**Goal:** Enable client integrations  
**Deliverables:** API key auth, webhook delivery system, admin UI  
**Key Files:**
- `backend/subscriptions/models.py` (add 3 models)
- `backend/subscriptions/middleware.py` (create)
- `backend/subscriptions/webhooks.py` (create)
- `frontend/src/app/admin/api-keys/page.tsx` (create)

**Models to Create:**
1. APIKey
2. WebhookEndpoint
3. WebhookDelivery

**Next Phase:** 0.7  

---

### **Phase 0.7: Analytics** (~12 hours)
**Goal:** Data-driven insights for admins  
**Deliverables:** Analytics dashboard, export functionality  
**Key Files:**
- `backend/subscriptions/models.py` (add DailyAnalytics)
- `backend/subscriptions/tasks.py` (add aggregation task)
- `frontend/src/app/admin/analytics/page.tsx` (create)

**Next Phase:** 0.8  

---

### **Phase 0.8: Email Campaigns & Audit** (~14 hours)
**Goal:** Marketing automation + compliance  
**Deliverables:** Campaign system, audit logging  
**Key Files:**
- `backend/subscriptions/models.py` (add 3 models)
- `backend/subscriptions/middleware.py` (update)
- `frontend/src/app/admin/campaigns/page.tsx` (create)
- `frontend/src/app/admin/audit-logs/page.tsx` (create)

**Next Phase:** 0.9  

---

### **Phase 0.9: Dunning** (~8 hours)
**Goal:** Recover failed payments  
**Deliverables:** Retry system, admin dashboard  
**Key Files:**
- `backend/subscriptions/models.py` (add PaymentAttempt)
- `backend/subscriptions/tasks.py` (add retry task)
- `frontend/src/app/admin/dunning/page.tsx` (create)

**Next Phase:** 1  

---

### **Phase 1: Celery Foundation** (~4 hours)
**Goal:** Set up async processing  
**Deliverables:** Celery app, test task, worker running  
**Key Files:**
- `backend/oxidane/celery.py` (create)
- `backend/oxidane/__init__.py` (update)
- `backend/oxidane/settings.py` (update)
- `backend/subscriptions/tasks.py` (create)

**Test Command:**
```powershell
celery -A oxidane worker -l info --pool=solo
```

**Next Phase:** 2  

---

### **Phase 2: Schema Updates** (~2 hours)
**Goal:** Add telegram_user_id to BillingProfile  
**Deliverables:** Migration, serializer update  
**Key Files:**
- `backend/subscriptions/models.py` (update BillingProfile)
- `backend/subscriptions/serializers.py` (update)

**Next Phase:** 3  

---

### **Phase 3: Telegram Package** (~6 hours)
**Goal:** Database-driven Telegram integration  
**Deliverables:** TelegramManager, config system  
**Key Files:**
- `backend/subscriptions/telegram/config.py` (create)
- `backend/subscriptions/telegram/manager.py` (create)
- `backend/subscriptions/telegram/utils.py` (create)

**Next Phase:** 4  

---

### **Phase 4: Celery Tasks** (~8 hours)
**Goal:** Implement all automation tasks  
**Deliverables:** 7 tasks, beat schedule  
**Key Files:**
- `backend/subscriptions/tasks.py` (update)
- `backend/oxidane/celery.py` (update beat_schedule)

**Tasks to Create:**
1. add_user_to_telegram
2. remove_user_from_telegram
3. check_expired_subscriptions
4. send_expiry_warning
5. process_expiry_warnings
6. aggregate_daily_analytics
7. retry_failed_payments

**Next Phase:** 5  

---

### **Phase 5: Webhook Integration** (~4 hours)
**Goal:** Auto-trigger tasks on payment  
**Deliverables:** Updated webhook handler  
**Key Files:**
- `backend/subscriptions/views/payment_views.py` (update)

**Next Phase:** 6  

---

### **Phase 6: Bot Updates** (~4 hours)
**Goal:** Update bot for DB config  
**Deliverables:** /verify and /status commands, bot service  
**Key Files:**
- Bot file (wherever it is)

**Next Phase:** 7  

---

### **Phase 7: Frontend Updates** (~6 hours)
**Goal:** User-facing verification UI  
**Deliverables:** Verification modal, referral section, upgrade UI  
**Key Files:**
- `frontend/src/components/TelegramVerificationModal.tsx` (create)
- `frontend/src/app/dashboard/page.tsx` (update)
- `frontend/src/app/pricing/page.tsx` (update)

**Next Phase:** 8  

---

### **Phase 8: Testing** (~10 hours)
**Goal:** Test everything  
**Deliverables:** 15 test scenarios passed  
**Key Files:**
- Test files (create as needed)

**Next Phase:** 9  

---

### **Phase 9: Monitoring** (~4 hours)
**Goal:** Production monitoring  
**Deliverables:** Sentry, Flower, health check  
**Key Files:**
- `backend/oxidane/settings.py` (update)
- `backend/subscriptions/views/health_views.py` (create)

**Next Phase:** 10  

---

### **Phase 10: Cleanup** (~6 hours)
**Goal:** Remove old code, create docs  
**Deliverables:** 3 guide docs, deployment scripts  
**Key Files:**
- `DEPLOYMENT_GUIDE.md` (create)
- `RESALE_GUIDE.md` (create)
- `INTEGRATION_GUIDE.md` (create)
- `deploy.ps1` (create)

**Next Phase:** 11  

---

### **Phase 11: Deployment** (~8 hours)
**Goal:** Go live  
**Deliverables:** Production deployment, real payment tested  
**Key Files:**
- `.env` (update for production)

**Next Phase:** 🎉 DONE!  

---

## 🆘 COMMON PROBLEMS & FIXES

### **Problem: Celery worker won't start**
**Error:** `[Errno 10061] No connection could be made`  
**Fix:**
1. Check if Redis is running: `redis-cli ping`
2. Check Redis URL in `.env`: `CELERY_BROKER_URL=redis://...`
3. Try with `--pool=solo` flag (Windows)

---

### **Problem: Migration fails**
**Error:** `django.db.utils.OperationalError`  
**Fix:**
1. Check PostgreSQL is running
2. Check database exists: `psql -U postgres -c "\l"`
3. Check user permissions: `GRANT ALL PRIVILEGES ON DATABASE oxidane TO oxidane;`

---

### **Problem: Import errors**
**Error:** `ModuleNotFoundError: No module named 'celery'`  
**Fix:**
1. Activate virtual environment
2. Run: `pip install -r requirements.txt`
3. Verify: `pip list | grep celery`

---

### **Problem: Telegram bot not responding**
**Error:** Bot doesn't reply to commands  
**Fix:**
1. Check bot is running: Look for Python process
2. Check bot token is correct in database
3. Check bot username with @BotFather
4. Test connection: `curl https://api.telegram.org/bot<TOKEN>/getMe`

---

### **Problem: Frontend won't build**
**Error:** Type errors in TypeScript  
**Fix:**
1. Check Node version: `node --version` (need 18+)
2. Delete node_modules: `rm -rf node_modules`
3. Reinstall: `npm install`
4. Clear cache: `npm cache clean --force`

---

### **Problem: Lost context in new chat**
**Fix:**
1. Read: `ENTERPRISE_PLATFORM_ROADMAP.md`
2. Read: `CONTEXT_FOR_NEW_CHAT.md`
3. Check: `git log --oneline -5`
4. Ask Copilot: "Read ENTERPRISE_PLATFORM_ROADMAP.md and tell me what phase I'm on based on my git history"

---

## 📞 EMERGENCY COMMANDS

### **Reset Everything:**
```powershell
# DANGER: This deletes all data!
git reset --hard HEAD
git clean -fd
python manage.py flush
```

### **Start Fresh (Keep Git History):**
```powershell
# Stash current work
git stash

# Go back to last good commit
git log --oneline
git reset --hard <commit-hash>

# Restore if needed
git stash pop
```

### **Check What's Running:**
```powershell
# PostgreSQL
psql -U postgres -c "SELECT version();"

# Redis
redis-cli ping

# Django
curl http://localhost:8000

# Celery
celery -A oxidane inspect active
```

---

## 🎯 TODAY'S FOCUS

**Before you start coding, answer these:**

1. **What phase am I on?** _____________
2. **What's the current task ID?** _____________
3. **What am I building?** _____________
4. **What file am I editing?** _____________
5. **How will I test it?** _____________

**If you can't answer all 5, read `ENTERPRISE_PLATFORM_ROADMAP.md` first!**

---

## 💾 END OF SESSION CHECKLIST

Before closing:

- [ ] Git commit: `git add . && git commit -m "Phase X: Task Y"`
- [ ] Git push: `git push origin enterprise-platform-v1`
- [ ] Update `PROGRESS_TRACKER.md` with today's work
- [ ] Mark completed tasks in todo list
- [ ] Note any blockers in `PROGRESS_TRACKER.md`
- [ ] Write tomorrow's plan in `PROGRESS_TRACKER.md`

---

## 📚 FILE REFERENCE

**Read these for context:**
- `ENTERPRISE_PLATFORM_ROADMAP.md` - Complete roadmap (master reference)
- `CONTEXT_FOR_NEW_CHAT.md` - How to maintain context across chats
- `PROGRESS_TRACKER.md` - Track daily progress
- `QUICK_START.md` - This file (instant reference)

**Create these as you go:**
- `KNOWN_ISSUES.md` - Document bugs/blockers
- `PROGRESS_NOTES.md` - Daily notes
- `.env` - Environment variables (DON'T commit!)

---

## 🔥 PRODUCTIVITY TIPS

1. **Work in 2-hour blocks** - Take breaks!
2. **Test after each task** - Don't write 100 lines without testing
3. **Commit after each task** - Easy rollback if needed
4. **Read error messages fully** - Don't guess, read the traceback
5. **Ask specific questions** - Give Copilot full context
6. **Keep roadmap open** - Reference it constantly
7. **Update progress daily** - Track your velocity
8. **Celebrate small wins** - You're building something amazing!

---

**Remember: 150 hours = 20 days. You're building a $20k+ platform. Take it one task at a time!**

**You got this! 🚀**
