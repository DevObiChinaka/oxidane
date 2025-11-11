# 🧪 Phase 1.5: Testing & Integration Guide

**Date:** November 8, 2025  
**Status:** In Progress  
**Goal:** Test existing user flows, identify bugs, integrate Phase 0.5 with user system

---

## 🎯 TESTING STRATEGY

We'll test the complete user journey in this order:
1. Registration flows (Email + OAuth)
2. Email verification
3. Login flows (Password + OTP)
4. Dashboard & profile
5. Settings & preferences
6. Course browsing & enrollment
7. Password reset

**Report all bugs immediately so I can fix them in real-time!**

---

## 🚀 SETUP INSTRUCTIONS

### Step 1: Start Backend Server
```powershell
cd backend
python manage.py runserver
```
**Expected:** Server running on `http://127.0.0.1:8000/`

### Step 2: Start Frontend Server
```powershell
cd frontend
npm run dev
```
**Expected:** Server running on `http://localhost:3000/`

### Step 3: Open Browser
Navigate to: `http://localhost:3000/`

---

## 📋 TEST SCENARIOS

### ✅ Test 1: User Registration (Email + Password)

**URL:** `http://localhost:3000/auth`

**Steps:**
1. Click on "Sign Up" tab (if not already there)
2. Fill in registration form:
   - **First Name:** Test
   - **Last Name:** User
   - **Email:** testuser@example.com (use a real email if possible)
   - **Password:** Test123!@#
   - **Confirm Password:** Test123!@#
3. Click "Create Account"

**Expected Behavior:**
- ✅ Form validates password requirements (8+ chars, uppercase, lowercase, number, special char)
- ✅ Email validation shows "Email available" message
- ✅ Success message appears
- ✅ Redirect to OTP verification page OR show OTP input field
- ✅ Email sent to inbox with 6-digit OTP

**What to Check:**
- [ ] Does the form validate properly?
- [ ] Are password requirements shown?
- [ ] Does email availability check work?
- [ ] Is the OTP sent to email?
- [ ] Any console errors?

**Report Issues Here:**
```
Issue #1.1: [Describe what went wrong]
Error message: [Copy any error messages]
Console errors: [Check browser console - F12]
```

---

### ✅ Test 2: Email Verification (OTP)

**Steps:**
1. Check email inbox for OTP (6-digit code)
2. Enter OTP in verification form
3. Click "Verify Email"

**Expected Behavior:**
- ✅ OTP countdown timer shows (10 minutes)
- ✅ Valid OTP verifies successfully
- ✅ Account activated
- ✅ Redirect to login or dashboard
- ✅ Success message shown

**What to Check:**
- [ ] Did you receive the OTP email?
- [ ] Does the OTP work when entered?
- [ ] Does "Resend OTP" button work?
- [ ] Does the countdown timer work?
- [ ] Where does it redirect after verification?

**Report Issues Here:**
```
Issue #2.1: [Describe what went wrong]
```

---

### ✅ Test 3: Login (Email + Password)

**URL:** `http://localhost:3000/auth`

**Steps:**
1. Click "Sign In" tab
2. Enter credentials:
   - **Email:** testuser@example.com
   - **Password:** Test123!@#
3. Click "Sign In"

**Expected Behavior:**
- ✅ Login successful with valid credentials
- ✅ JWT tokens stored in localStorage
- ✅ Redirect to `/dashboard`
- ✅ Dashboard loads with user data

**What to Check:**
- [ ] Does login work?
- [ ] Are you redirected to dashboard?
- [ ] Is user data displayed correctly?
- [ ] Check localStorage for `access_token` and `refresh_token`

**Report Issues Here:**
```
Issue #3.1: [Describe what went wrong]
```

---

### ✅ Test 4: Login with OTP (Passwordless)

**Steps:**
1. On login page, click "Sign in with OTP" (if available)
2. Enter email address
3. Click "Send OTP"
4. Check email for OTP
5. Enter OTP and submit

**Expected Behavior:**
- ✅ OTP sent to email
- ✅ OTP verification works
- ✅ Login successful
- ✅ Redirect to dashboard

**What to Check:**
- [ ] Is there an OTP login option?
- [ ] Does the flow work end-to-end?

**Report Issues Here:**
```
Issue #4.1: [Describe what went wrong]
```

---

### ✅ Test 5: Google OAuth Registration/Login

**Steps:**
1. On auth page, click "Sign in with Google" button
2. Follow Google OAuth flow
3. Authorize the app
4. Return to app

**Expected Behavior:**
- ✅ Redirect to Google OAuth page
- ✅ User can authorize
- ✅ Redirect back to app with token
- ✅ Account created/logged in
- ✅ Redirect to dashboard

**What to Check:**
- [ ] Does OAuth button exist?
- [ ] Does it redirect to Google?
- [ ] Does callback work properly?
- [ ] Is user logged in after OAuth?

**Report Issues Here:**
```
Issue #5.1: [Describe what went wrong]
```

---

### ✅ Test 6: Dashboard

**URL:** `http://localhost:3000/dashboard`

**What to Check:**
- [ ] User name displayed correctly
- [ ] Email displayed
- [ ] Subscription stats shown (if any)
- [ ] Course count displayed
- [ ] Navigation sidebar works
- [ ] No console errors

**Expected Data:**
```json
{
  "user": {
    "name": "Test User",
    "email": "testuser@example.com",
    "is_email_verified": true
  },
  "subscriptions": {
    "active_count": 0,
    "total_monthly_cost": 0,
    "has_active_subscription": false
  }
}
```

**Report Issues Here:**
```
Issue #6.1: [Describe what went wrong]
API endpoint issues: [Note any 404s or errors]
```

---

### ✅ Test 7: Profile Management

**URL:** `http://localhost:3000/profile`

**Steps:**
1. Navigate to Profile page
2. Click "Edit Profile"
3. Change first name to "Updated"
4. Change last name to "Name"
5. Click "Save Changes"

**Expected Behavior:**
- ✅ Form pre-fills with current data
- ✅ Changes save successfully
- ✅ Success message shown
- ✅ Profile updates reflected

**What to Check:**
- [ ] Can you edit profile?
- [ ] Do changes persist?
- [ ] Avatar upload works? (if applicable)

**Report Issues Here:**
```
Issue #7.1: [Describe what went wrong]
```

---

### ✅ Test 8: Settings - Password Change

**URL:** `http://localhost:3000/settings`

**Steps:**
1. Navigate to Settings page
2. Go to "Password" tab
3. Fill in:
   - **Current Password:** Test123!@#
   - **New Password:** NewPass123!@#
   - **Confirm Password:** NewPass123!@#
4. Click "Change Password"

**Expected Behavior:**
- ✅ Password changes successfully
- ✅ Success message shown
- ✅ Can login with new password

**What to Check:**
- [ ] Does password change work?
- [ ] Is validation proper?
- [ ] Can you login with new password after?

**Report Issues Here:**
```
Issue #8.1: [Describe what went wrong]
```

---

### ✅ Test 9: Settings - Notification Preferences

**URL:** `http://localhost:3000/settings`

**Steps:**
1. Go to "Notifications" tab
2. Toggle various notification preferences
3. Click "Save Preferences"

**Expected Behavior:**
- ✅ Toggles work
- ✅ Preferences save
- ✅ Settings persist on reload

**What to Check:**
- [ ] Do notification toggles work?
- [ ] Do preferences save?

**Report Issues Here:**
```
Issue #9.1: [Describe what went wrong]
```

---

### ✅ Test 10: Course Browsing

**URL:** `http://localhost:3000/courses`

**Steps:**
1. Navigate to Courses page
2. Browse available courses
3. Use search bar
4. Filter by difficulty
5. Filter by type (free/premium)

**Expected Behavior:**
- ✅ Courses load from API
- ✅ Filters work correctly
- ✅ Search functionality works
- ✅ Course cards display properly

**What to Check:**
- [ ] Do courses display?
- [ ] Does filtering work?
- [ ] Does search work?
- [ ] Can you click into course details?

**Report Issues Here:**
```
Issue #10.1: [Describe what went wrong]
```

---

### ✅ Test 11: Course Enrollment

**Steps:**
1. Click on a free course
2. Click "Enroll" button
3. Verify enrollment successful
4. Navigate to "My Courses"
5. Verify course appears there

**Expected Behavior:**
- ✅ Enrollment works
- ✅ Course appears in "My Courses"
- ✅ Progress tracking initialized

**What to Check:**
- [ ] Can you enroll in courses?
- [ ] Does it show in My Courses?

**Report Issues Here:**
```
Issue #11.1: [Describe what went wrong]
```

---

### ✅ Test 12: Password Reset Flow

**URL:** `http://localhost:3000/forgot-password`

**Steps:**
1. Navigate to Forgot Password page
2. Enter email address
3. Click "Send Reset Code"
4. Check email for OTP
5. Enter OTP and new password
6. Submit reset form

**Expected Behavior:**
- ✅ OTP sent to email
- ✅ OTP verification works
- ✅ Password resets successfully
- ✅ Can login with new password

**What to Check:**
- [ ] Does forgot password work?
- [ ] Is OTP received?
- [ ] Does password reset successfully?

**Report Issues Here:**
```
Issue #12.1: [Describe what went wrong]
```

---

### ✅ Test 13: Billing & Telegram Integration

**URL:** `http://localhost:3000/billing`

**Steps:**
1. Navigate to Billing page
2. Check Telegram verification status
3. Try generating verification code
4. Check subscription display

**Expected Behavior:**
- ✅ Page loads
- ✅ Telegram status shown
- ✅ Subscription info displays (if any)

**What to Check:**
- [ ] Does billing page load?
- [ ] Are subscriptions displayed?
- [ ] Does Telegram verification show?

**Report Issues Here:**
```
Issue #13.1: [Describe what went wrong]
```

---

## 🐛 BUG TRACKING

As you test, document ALL issues here:

### Critical Bugs 🔴
```
1. [Bug description]
2. [Bug description]
```

### Medium Priority Bugs 🟡
```
1. [Bug description]
2. [Bug description]
```

### Minor Issues 🟢
```
1. [Bug description]
2. [Bug description]
```

### Missing Features ⚪
```
1. [Feature description]
2. [Feature description]
```

---

## 📊 TEST RESULTS SUMMARY

| Test | Status | Notes |
|------|--------|-------|
| Registration (Email) | ⏳ Pending | |
| Email Verification | ⏳ Pending | |
| Login (Password) | ⏳ Pending | |
| Login (OTP) | ⏳ Pending | |
| Google OAuth | ⏳ Pending | |
| Dashboard | ⏳ Pending | |
| Profile Management | ⏳ Pending | |
| Password Change | ⏳ Pending | |
| Notifications | ⏳ Pending | |
| Course Browsing | ⏳ Pending | |
| Course Enrollment | ⏳ Pending | |
| Password Reset | ⏳ Pending | |
| Billing/Telegram | ⏳ Pending | |

**Legend:** ✅ Pass | ❌ Fail | ⏳ Pending | ⚠️ Has Issues

---

## 🔧 NEXT STEPS AFTER TESTING

Once testing is complete, we'll:
1. **Fix all identified bugs**
2. **Build missing API endpoints** (e.g., `/api/subscriptions/my-subscriptions/`)
3. **Integrate Phase 0.5 models** with user system
4. **Update documentation** to reflect actual state
5. **Plan Phase 2.0** (Payment Gateway Integration)

---

**Ready to start testing!** 🚀

Open your browser and let's begin with Test 1: User Registration.
Report any issues you encounter, and I'll fix them immediately!
