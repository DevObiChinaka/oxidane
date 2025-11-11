# Phase 1: Core Models Integration Plan

**Status:** 🚀 READY TO START  
**Estimated Time:** 8-10 hours  
**Dependencies:** Phase 0.5 Complete ✅  
**Date:** November 9, 2025

---

## 🎯 Objective

Integrate the new subscription models (created in Phase 0.5) with existing core models (User, Course, Enrollment) to create a unified subscription management system.

---

## 📋 Task Breakdown

### **Task 1.1: User Model Integration** (2 hours)
**File:** `backend/accounts/models.py`

**Current State:**
- User model exists with basic profile fields
- Has relationships to old subscription models
- Needs integration with new SubscriptionPlan model

**Changes Needed:**
1. Add foreign key to `SubscriptionPlan` (current_plan)
2. Add subscription status fields:
   - `subscription_status` (active/past_due/cancelled/trialing)
   - `subscription_start_date`
   - `subscription_end_date`
   - `trial_end_date`
3. Add helper methods:
   - `has_feature(feature_key)` - Check if user's plan has a feature
   - `can_access_course(course)` - Check course access based on plan
   - `get_plan_limits()` - Get usage limits from plan
   - `is_subscription_active()` - Check if subscription is active
4. Add usage tracking fields:
   - `usage_stats` (JSONField) - Track feature usage
5. Write comprehensive tests (30+ tests)
6. Create migration

**Test Coverage:**
- Subscription status transitions
- Feature access checks
- Plan limit validation
- Trial period handling
- Usage tracking

---

### **Task 1.2: Course Model Integration** (2 hours)
**File:** `backend/courses/models.py`

**Current State:**
- Course model with basic fields (title, description, instructor)
- Has `course_type` (free/premium) field
- No relationship to SubscriptionPlan

**Changes Needed:**
1. Add ManyToMany to `SubscriptionPlan` (required_plans)
   - Empty M2M = available to all plans
   - Non-empty = restricted to specific plans
2. Add fields:
   - `access_type` (free/plan_based/direct_purchase)
   - `direct_purchase_price` (DecimalField, nullable)
3. Update helper methods:
   - `is_accessible_by_user(user)` - Check if user can access
   - `get_required_plan_names()` - Get list of plan names
4. Backward compatibility:
   - Keep `course_type` for now, mark as deprecated
   - Add migration to map old data to new structure
5. Write comprehensive tests (25+ tests)
6. Create migration

**Test Coverage:**
- Plan-based access control
- Free course access
- Direct purchase logic
- Required plan validation
- User access checks

---

### **Task 1.3: Enrollment Model Updates** (1.5 hours)
**File:** `backend/courses/models.py`

**Current State:**
- Basic enrollment tracking (user, course, enrolled_at)
- No subscription awareness

**Changes Needed:**
1. Add fields:
   - `access_granted_by` (plan/purchase/admin/free)
   - `subscription_plan` (FK to SubscriptionPlan, nullable)
   - `payment_reference` (CharField, for direct purchases)
   - `access_expires_at` (DateTimeField, nullable)
2. Add methods:
   - `is_access_valid()` - Check if access is still valid
   - `renew_from_subscription()` - Update access based on subscription
3. Add signals:
   - Update enrollment access when user's subscription changes
4. Write tests (20+ tests)
5. Create migration

**Test Coverage:**
- Enrollment creation from different sources
- Access expiration handling
- Subscription renewal impact
- Admin-granted access

---

### **Task 1.4: Data Migration Script** (1.5 hours)
**File:** `backend/subscriptions/management/commands/migrate_old_subscriptions.py`

**Purpose:** Migrate existing data to new structure

**Steps:**
1. Create default "Free" plan if doesn't exist
2. Create "Premium" plan matching old system
3. Map all users with old subscriptions to new plans
4. Update all courses:
   - `course_type='free'` → `access_type='free'`
   - `course_type='premium'` → `access_type='plan_based'` + link to Premium plan
5. Update all enrollments with proper access tracking
6. Generate report of migration results
7. Add rollback capability

**Validation:**
- Count users before/after
- Verify all enrollments preserved
- Check plan assignments
- Test access for sample users

---

### **Task 1.5: Admin Interface Updates** (1 hour)
**Files:** 
- `backend/accounts/admin.py`
- `backend/courses/admin.py`

**Changes:**
1. **User Admin:**
   - Add subscription status to list display
   - Add plan filter
   - Add inline for subscription history
   - Add action: "Grant trial access"
   - Add action: "Reset trial"
   
2. **Course Admin:**
   - Add required_plans to form
   - Add access_type to list display
   - Add filter by access type
   - Show enrollment count
   - Add action: "Clone course"

3. **Enrollment Admin:**
   - Add access_granted_by to list display
   - Add filter by access type
   - Add filter by subscription plan
   - Show expiration date
   - Add action: "Extend access"

---

### **Task 1.6: API Endpoints Updates** (1.5 hours)
**Files:**
- `backend/courses/views.py`
- `backend/courses/serializers.py`
- `backend/accounts/views.py`

**New/Updated Endpoints:**

1. **GET /api/courses/** (Update)
   - Add `can_access` field based on user's plan
   - Add `required_plans` in response
   - Add `access_type` field
   - Filter visible courses based on user's plan

2. **GET /api/courses/{slug}/** (Update)
   - Add detailed access information
   - Show which plans grant access
   - Show user's current access status
   - Add enrollment instructions

3. **POST /api/courses/{slug}/enroll/** (Update)
   - Check plan access before enrolling
   - Create enrollment with proper tracking
   - Handle different access types
   - Return clear error messages

4. **GET /api/users/me/subscription/** (New)
   - Return user's current plan details
   - Show active features
   - Show usage stats
   - Show subscription dates

5. **GET /api/users/me/access/** (New)
   - List all accessible courses
   - Show access source (plan/purchase/admin)
   - Show expiration dates
   - Group by access type

**Test Coverage:**
- API response format validation
- Access control tests
- Error handling
- Permission checks

---

### **Task 1.7: Integration Testing** (1 hour)
**File:** `backend/tests/integration/test_subscription_flow.py`

**Test Scenarios:**
1. **Free User Flow:**
   - User can access free courses
   - User cannot access premium courses
   - User can see upgrade prompts

2. **Premium User Flow:**
   - User with plan can access plan courses
   - User can see all accessible courses
   - Usage tracking works correctly

3. **Trial User Flow:**
   - Trial access granted correctly
   - Trial expiration handled
   - Conversion to paid works

4. **Subscription Changes:**
   - Upgrade plan → access increases
   - Downgrade plan → access decreases
   - Cancel subscription → access revoked properly

5. **Edge Cases:**
   - Expired subscriptions
   - Multiple plan assignments
   - Admin override access
   - Direct purchase + subscription

---

## 🗄️ Database Schema Changes

### **New Fields:**

**accounts.User:**
```python
current_plan = FK(SubscriptionPlan, null=True)
subscription_status = CharField(choices=[...])
subscription_start_date = DateTimeField(null=True)
subscription_end_date = DateTimeField(null=True)
trial_end_date = DateTimeField(null=True)
usage_stats = JSONField(default=dict)
```

**courses.Course:**
```python
required_plans = M2M(SubscriptionPlan)
access_type = CharField(choices=['free', 'plan_based', 'direct_purchase'])
direct_purchase_price = DecimalField(null=True)
# Keep for backward compatibility:
course_type = CharField(deprecated=True)  # Will remove in Phase 2
```

**courses.Enrollment:**
```python
access_granted_by = CharField(choices=['plan', 'purchase', 'admin', 'free'])
subscription_plan = FK(SubscriptionPlan, null=True)
payment_reference = CharField(null=True)
access_expires_at = DateTimeField(null=True)
```

---

## 📊 Migration Strategy

### **Phase A: Additive Changes** (Safe)
1. Add new fields to all models (nullable/default values)
2. Add new helper methods
3. Create new API endpoints
4. Run migrations

### **Phase B: Data Migration** (Careful)
1. Run migration script in dry-run mode
2. Review migration plan
3. Execute migration
4. Validate results
5. Keep old fields temporarily

### **Phase C: Deprecation** (Later - Phase 2)
1. Update all code to use new fields
2. Add deprecation warnings to old fields
3. Schedule removal date
4. Remove old fields in Phase 2

---

## ✅ Success Criteria

- [ ] All new fields added and migrated
- [ ] All helper methods working correctly
- [ ] All existing enrollments preserved
- [ ] All courses properly categorized
- [ ] All users assigned to correct plans
- [ ] 100% test coverage for new code
- [ ] All API endpoints updated and tested
- [ ] Admin interfaces fully functional
- [ ] Integration tests passing
- [ ] No data loss during migration
- [ ] Backward compatibility maintained
- [ ] Documentation updated

---

## 🚨 Risk Mitigation

**Risk 1: Data Loss During Migration**
- Mitigation: Create full database backup before migration
- Mitigation: Test migration on copy of production data
- Mitigation: Add rollback script

**Risk 2: Breaking Existing Functionality**
- Mitigation: Keep old fields during transition
- Mitigation: Comprehensive integration tests
- Mitigation: Gradual rollout with feature flags

**Risk 3: Performance Issues**
- Mitigation: Add database indexes on new FK fields
- Mitigation: Optimize queries with select_related/prefetch_related
- Mitigation: Monitor query performance

---

## 📝 Next Steps After Phase 1

After completing this integration:
1. **Phase 0.6:** API Keys & Webhooks
2. **Phase 0.7:** Analytics & Reporting
3. **Phase 1.0:** Celery Foundation (original roadmap)

---

**Last Updated:** November 9, 2025  
**Status:** Ready to begin 🚀
