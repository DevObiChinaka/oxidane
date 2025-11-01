# Admin Token Debugging Guide

## Current Status: Token Storage Issue

The OTP verification succeeds (200 response) but subsequent API calls return 401 Unauthorized, indicating the token is not being properly stored or retrieved.

## Debug Logs Added

### Files Modified with Debug Logging:

1. **`frontend/src/app/admin/login/page.tsx`**
   - OTP verification response logging
   - Token pass-through logging
   - localStorage verification after storage

2. **`frontend/src/app/admin/contexts/AdminAuthContext.tsx`**
   - Login function entry logging
   - Token storage confirmation
   - localStorage verification

3. **`frontend/src/app/admin/utils/api.ts`**
   - Token retrieval logging for each API request
   - Authorization header setting confirmation

## Testing Steps

### Step 1: Clear Everything
```javascript
// Open browser DevTools Console and run:
localStorage.clear();
location.reload();
```

### Step 2: Attempt Login
1. Go to `http://localhost:3000/admin/login`
2. Enter credentials
3. Get OTP from email
4. Enter OTP code
5. **Watch the console carefully**

### Step 3: Check Console Output

#### Expected Output (SUCCESS):
```
🔐 OTP Verification Response: { success: true, hasToken: true, ... }
🔐 OTP verified successfully!
🔐 Token from API: abc123...
🔐 User from API: { email: "...", ... }
🔐 OTP Success - Token received: YES
🔐 AdminAuthContext.login() called
🔐 Token received: YES (abc123...)
🔐 Storing token in localStorage...
🔐 Storing user data in localStorage...
✅ Token stored successfully: YES
✅ User stored successfully: YES
🔐 Redirecting to /admin/dashboard
🔐 API Request - Token check: Found (abc123...)
🔐 API Request - Authorization header set
```

#### Problem Indicators:
- ❌ "Token received: NO" → Backend not returning token
- ❌ "Token stored successfully: NO" → localStorage.setItem failing
- ❌ "Token check: NOT FOUND" → Token lost between storage and API call

## Common Issues & Solutions

### Issue 1: Token Not Returned from Backend
**Symptom:** `hasToken: false` in OTP response

**Solution:** Check backend response in Network tab:
```bash
# Check backend logs for:
'admin_token': admin_session_token
```

### Issue 2: localStorage Not Persisting
**Symptom:** Token stored but immediately lost

**Possible Causes:**
1. Browser privacy mode/incognito
2. localStorage disabled by browser settings
3. Page reload clearing storage (HMR issue in dev)

**Solution:**
```javascript
// Test localStorage:
localStorage.setItem('test', 'value');
console.log(localStorage.getItem('test')); // Should output 'value'
```

### Issue 3: Timing Issue with Router Push
**Symptom:** Token stored but lost during navigation

**Solution:** Added 100ms delay before redirect to ensure localStorage write completes

### Issue 4: Multiple localStorage Keys
**Symptom:** Wrong token key being used

**Verify:**
```javascript
// Check all keys:
console.log(Object.keys(localStorage));
// Should see: ['admin_token', 'admin_user']
```

## Manual Testing Commands

### Check Token in Browser Console:
```javascript
// Get token
const token = localStorage.getItem('admin_token');
console.log('Token:', token);

// Test API call manually
fetch('http://127.0.0.1:8000/api/admin/dashboard/metrics/', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
})
.then(r => r.json())
.then(d => console.log('API Response:', d))
.catch(e => console.error('API Error:', e));
```

### Clear Token and Re-test:
```javascript
localStorage.removeItem('admin_token');
localStorage.removeItem('admin_user');
// Then try login again
```

## Backend Verification

### Check Backend Logs:
Look for these patterns:
```
✅ GOOD:
[POST] /api/admin-auth/verify-otp/ 200 236
[GET] /api/admin/dashboard/metrics/ 200 ...

❌ BAD:
[POST] /api/admin-auth/verify-otp/ 200 236
Unauthorized: /api/admin/dashboard/metrics/
[GET] /api/admin/dashboard/metrics/ 401 183
```

### Test Token Generation:
```python
# In Django shell:
python manage.py shell

from django.core.cache import cache
import uuid

# Create test token
test_token = str(uuid.uuid4())
cache_key = f"admin_session_{test_token}"
cache.set(cache_key, {
    'user_id': 1,
    'email': 'test@example.com',
    'is_superuser': True
}, 3600)

print(f"Test token: {test_token}")
# Use this token in Authorization: Bearer <token>
```

## Next Steps After Testing

1. **If logs show token stored but not retrieved:**
   - Check for page reload/navigation clearing storage
   - Check browser localStorage permissions
   - Check for conflicting code clearing storage

2. **If logs show token not being stored:**
   - Check browser localStorage support
   - Check for localStorage quota errors
   - Check browser console for errors

3. **If logs show token not returned from backend:**
   - Check backend response structure
   - Check Django session creation
   - Check Redis/cache connectivity

## Files to Review Based on Issue

### Token Not Stored:
- `frontend/src/app/admin/contexts/AdminAuthContext.tsx`
- Browser localStorage permissions

### Token Not Retrieved:
- `frontend/src/app/admin/utils/api.ts`
- `frontend/src/app/admin/hooks/useAdminAPI.ts`

### Token Not Sent to Backend:
- `backend/users/admin_auth.py`
- Redis cache connection
- Django cache settings

## Quick Fix Checklist

- [x] Fixed token key inconsistency (`adminToken` → `admin_token`)
- [x] Fixed datetime timezone warnings
- [x] Added comprehensive debug logging
- [x] Added timing delay before redirect
- [ ] Verify localStorage is working in browser
- [ ] Verify token is in backend response
- [ ] Verify token persists after redirect
