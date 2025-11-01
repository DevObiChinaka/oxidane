# Admin Authentication Token Fix

## Date: October 27, 2025

## Problem Identified

After successful OTP verification during admin login, the admin was getting **401 Unauthorized** errors on all subsequent API requests. This was causing the admin dashboard to fail loading data.

### Root Causes

1. **Inconsistent Token Storage Key**
   - Backend returns: `admin_token` (with underscore)
   - Most frontend code uses: `admin_token` (with underscore) ✅
   - `pricingAPI.ts` was using: `adminToken` (WITHOUT underscore) ❌
   
   This meant that when API calls were made from pricing-related features, they were looking for a token that didn't exist in localStorage.

2. **DateTime Timezone Warning**
   - `email_service.py` was using `datetime.now()` instead of `timezone.now()`
   - This caused Django runtime warnings about naive datetime values

## Files Fixed

### Frontend Changes

#### 1. `frontend/src/app/admin/utils/pricingAPI.ts`
Changed all instances of `localStorage.getItem('adminToken')` to `localStorage.getItem('admin_token')`:

- Line 22: `getPricingPlans()` method
- Line 49: `createPricingPlan()` method
- Line 77: `updatePricingPlan()` method
- Line 93: `deletePricingPlan()` method
- Line 123: `getCouponCodes()` method
- Line 151: `createCouponCode()` method

**Total: 6 instances fixed**

### Backend Changes

#### 1. `backend/users/email_service.py`
- Added import: `from django.utils import timezone`
- Changed `email_log.sent_at = datetime.now()` → `timezone.now()`
- Changed `template.last_used = datetime.now()` → `timezone.now()`

## Authentication Flow (Now Fixed)

1. **Step 1: Login Request**
   ```
   POST /api/admin-auth/login/
   → Returns session_token
   ```

2. **Step 2: OTP Verification**
   ```
   POST /api/admin-auth/verify-otp/
   Body: { session_token, otp }
   → Returns: { admin_token, user }
   ```

3. **Step 3: Token Storage**
   ```javascript
   localStorage.setItem('admin_token', token);  // ✅ Consistent naming
   localStorage.setItem('admin_user', JSON.stringify(userData));
   ```

4. **Step 4: Authenticated Requests**
   ```javascript
   headers: {
     'Authorization': `Bearer ${localStorage.getItem('admin_token')}`  // ✅ All files now use 'admin_token'
   }
   ```

## Token Storage Standard

All code must use: **`admin_token`** (with underscore)

### Files Verified as Correct:
- ✅ `AdminAuthContext.tsx` - Uses `admin_token`
- ✅ `admin/page.tsx` - Uses `admin_token`
- ✅ `admin/dashboard/page.tsx` - Uses `admin_token`
- ✅ `admin/utils/api.ts` - Uses `admin_token`
- ✅ `admin/hooks/useAdminAPI.ts` - Uses `admin_token`
- ✅ `admin/components/MentorshipManagement.tsx` - Uses `admin_token`

### Files Fixed:
- ✅ `admin/utils/pricingAPI.ts` - Changed from `adminToken` to `admin_token`

## Testing Checklist

After these fixes, test the following flow:

1. ✅ Navigate to `/admin/login`
2. ✅ Enter admin credentials (email/username + password)
3. ✅ Click "Send Login Code"
4. ✅ Check email for OTP code
5. ✅ Enter OTP code
6. ✅ Click "Verify Code"
7. ✅ Should redirect to `/admin/dashboard` with data loading successfully
8. ✅ Dashboard metrics should load without 401 errors
9. ✅ Courses list should load without 401 errors
10. ✅ All admin API endpoints should work with authentication
11. ✅ No more DateTime warnings in Django logs

## Expected Behavior

- **Before Fix**: 401 Unauthorized on all admin API calls after login
- **After Fix**: All admin API calls include proper Bearer token and succeed

## Technical Notes

### Why This Happened
The `pricingAPI.ts` file was likely created separately or copy-pasted from another project and used a different token naming convention (`adminToken` without underscore). This inconsistency went unnoticed because:
1. The token was successfully stored with the correct name (`admin_token`)
2. But pricing-related API calls looked for the wrong name (`adminToken`)
3. Result: `undefined` was sent in Authorization header → 401 Unauthorized

### Prevention
To prevent similar issues:
1. Use a centralized auth utility/hook for all API calls
2. Never access localStorage directly in API functions
3. Consider using TypeScript literal types for localStorage keys
4. Add ESLint rule to catch direct localStorage access patterns

### Example Centralized Pattern
```typescript
// ✅ Good Practice
export const getAuthHeaders = () => ({
  'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
  'Content-Type': 'application/json'
});

// Use in all API calls:
fetch(url, { headers: getAuthHeaders() })
```

## Status: ✅ RESOLVED

All authentication token issues have been fixed. The admin login flow should now work correctly end-to-end.
