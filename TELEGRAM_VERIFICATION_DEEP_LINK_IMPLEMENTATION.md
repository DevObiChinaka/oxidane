# Telegram Verification: Deep Link + Username Entry Implementation

**Date:** November 12, 2025  
**Implementation Status:** ✅ Complete (Ready for Testing)

---

## 🎯 Project Decision

**Problem:** The old Telegram verification system used `/verify CODE` commands that required:
- Webhook setup (ngrok for development)
- Manual BotFather command configuration
- Hardcoded bot references (`@OxiWorldBot`)
- Didn't work with the new singleton TelegramConfiguration system

**Solution Chosen:** **Deep Link + Username Entry Verification**

### Why This Approach?

✅ **No Webhook Required** - Works in development without ngrok  
✅ **No BotFather Setup** - `/start` command works by default on all bots  
✅ **Admin-Configurable Bot** - Uses TelegramConfiguration singleton model  
✅ **Better UX** - Clear 3-step process with visual feedback  
✅ **Direct API Calls** - Backend makes outbound requests to Telegram API  
✅ **Development-Friendly** - No public URL needed for local testing

---

## 🏗️ Architecture Overview

### User Flow (3 Steps)

```
Step 1: Generate Verification Code
  ↓ User clicks "Verify Telegram" on checkout
  ↓ Backend generates: OXI-A1B2
  ↓ Creates deep link: t.me/YourBot?start=VERIFY_OXI-A1B2
  ↓ Returns to frontend

Step 2: Enter Telegram Username
  ↓ User clicks deep link → Opens Telegram
  ↓ User clicks START in bot chat
  ↓ User returns to website
  ↓ Enters Telegram username: @johndoe
  ↓ Backend validates username via Telegram API
  ↓ Generates 6-digit code: 123456
  ↓ Sends code to user via Telegram message

Step 3: Confirm Code
  ↓ User checks Telegram for code
  ↓ Enters 6-digit code on website
  ↓ Backend verifies code matches
  ✅ Account verified and linked!
```

---

## 📁 Files Created/Modified

### Backend Files

#### 1. **`backend/subscriptions/billing_views.py`** (Modified)

**Line 21-71: Updated `generate_telegram_verification_code`**
```python
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_telegram_verification_code(request):
    """
    Generate verification code and deep link for Telegram verification.
    Now uses TelegramConfiguration singleton instead of hardcoded bot.
    
    Returns:
    {
        'verification_code': 'OXI-A1B2',
        'deep_link': 'https://t.me/YourBot?start=VERIFY_OXI-A1B2',
        'bot_username': '@YourBot',
        'expires_at': '2025-11-12T10:30:00Z'
    }
    """
    # Get admin-configured bot
    telegram_config = TelegramConfiguration.objects.first()
    if not telegram_config or not telegram_config.bot_username:
        return Response({
            'error': 'Telegram bot not configured. Please contact support.',
            'code': 'BOT_NOT_CONFIGURED'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    # Generate verification code
    billing_profile, _ = BillingProfile.objects.get_or_create(user=request.user)
    code = billing_profile.generate_verification_code()
    
    # Create deep link
    bot_username_clean = telegram_config.bot_username.replace('@', '')
    deep_link = f'https://t.me/{bot_username_clean}?start=VERIFY_{code}'
    bot_username = telegram_config.bot_username if telegram_config.bot_username.startswith('@') else f'@{telegram_config.bot_username}'
    
    return Response({
        'verification_code': code,
        'deep_link': deep_link,
        'bot_username': bot_username,
        'expires_at': billing_profile.verification_code_expires_at,
    }, status=status.HTTP_200_OK)
```

**Lines 242-284: New `verify_telegram_username` endpoint**
```python
@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_telegram_username(request):
    """
    Step 2: Verify user's Telegram username and send confirmation code.
    
    Body:
    {
        "verification_code": "OXI-A1B2",
        "telegram_username": "@johndoe"
    }
    
    Process:
    1. Validate verification code is valid
    2. Check username via Telegram API
    3. Generate 6-digit confirmation code
    4. Send code to user via Telegram
    5. Store code temporarily for confirmation
    
    Response:
    {
        "success": true,
        "message": "Confirmation code sent to your Telegram"
    }
    """
    verification_code = request.data.get('verification_code', '').upper().strip()
    telegram_username = request.data.get('telegram_username', '').strip()
    
    # Remove @ if present
    if telegram_username.startswith('@'):
        telegram_username = telegram_username[1:]
    
    try:
        # Get billing profile
        billing_profile = BillingProfile.objects.get(
            user=request.user,
            verification_code=verification_code
        )
        
        # Check code validity
        if not billing_profile.is_verification_code_valid():
            return Response({
                'success': False,
                'error': 'Verification code expired. Please generate a new one.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get bot configuration
        config = TelegramConfiguration.objects.first()
        if not config or not config.bot_token:
            return Response({
                'success': False,
                'error': 'Telegram bot not configured'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        # Verify username exists via Telegram API
        import requests
        response = requests.get(
            f'https://api.telegram.org/bot{config.bot_token}/getChat',
            params={'chat_id': f'@{telegram_username}'},
            timeout=10
        )
        
        if not response.ok:
            return Response({
                'success': False,
                'error': 'Username not found. Please check and try again.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user_data = response.json()['result']
        telegram_user_id = str(user_data['id'])
        
        # Generate 6-digit confirmation code
        import random
        confirmation_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        
        # Store code temporarily (5 minutes)
        from django.core.cache import cache
        cache_key = f'telegram_confirm_{verification_code}'
        cache.set(cache_key, {
            'confirmation_code': confirmation_code,
            'telegram_user_id': telegram_user_id,
            'telegram_username': telegram_username
        }, 300)  # 5 minutes
        
        # Send code via Telegram
        send_response = requests.post(
            f'https://api.telegram.org/bot{config.bot_token}/sendMessage',
            json={
                'chat_id': telegram_user_id,
                'text': f'🔐 Your Oxidane verification code: {confirmation_code}\n\nEnter this code on the website to complete verification.',
                'parse_mode': 'HTML'
            },
            timeout=10
        )
        
        if not send_response.ok:
            return Response({
                'success': False,
                'error': 'Failed to send code. Please make sure you started the bot.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': True,
            'message': 'Confirmation code sent to your Telegram'
        }, status=status.HTTP_200_OK)
        
    except BillingProfile.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Invalid verification code'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error verifying Telegram username: {str(e)}")
        return Response({
            'success': False,
            'error': 'Verification failed. Please try again.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

**Lines 286-344: New `confirm_telegram_code` endpoint**
```python
@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_telegram_code(request):
    """
    Step 3: Confirm the 6-digit code sent to user's Telegram.
    
    Body:
    {
        "verification_code": "OXI-A1B2",
        "confirmation_code": "123456"
    }
    
    Process:
    1. Retrieve cached confirmation data
    2. Validate 6-digit code matches
    3. Link Telegram account to user
    4. Mark as verified
    
    Response:
    {
        "success": true,
        "message": "Telegram account verified successfully!",
        "telegram_username": "@johndoe",
        "verified_at": "2025-11-12T10:35:00Z"
    }
    """
    verification_code = request.data.get('verification_code', '').upper().strip()
    confirmation_code = request.data.get('confirmation_code', '').strip()
    
    try:
        # Get cached confirmation data
        from django.core.cache import cache
        cache_key = f'telegram_confirm_{verification_code}'
        cached_data = cache.get(cache_key)
        
        if not cached_data:
            return Response({
                'success': False,
                'message': 'Confirmation code expired. Please restart verification.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify code matches
        if cached_data['confirmation_code'] != confirmation_code:
            return Response({
                'success': False,
                'message': 'Invalid confirmation code. Please try again.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get billing profile
        billing_profile = BillingProfile.objects.get(
            user=request.user,
            verification_code=verification_code
        )
        
        # Link Telegram account
        billing_profile.telegram_user_id = cached_data['telegram_user_id']
        billing_profile.telegram_username = f"@{cached_data['telegram_username']}"
        billing_profile.telegram_verified = True
        billing_profile.telegram_verified_at = timezone.now()
        billing_profile.verification_code = ''  # Clear code
        billing_profile.save()
        
        # Clear cache
        cache.delete(cache_key)
        
        return Response({
            'success': True,
            'message': 'Telegram account verified successfully!',
            'telegram_username': billing_profile.telegram_username,
            'verified_at': billing_profile.telegram_verified_at
        }, status=status.HTTP_200_OK)
        
    except BillingProfile.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Invalid verification code'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error confirming Telegram code: {str(e)}")
        return Response({
            'success': False,
            'message': 'Verification failed. Please try again.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

#### 2. **`backend/subscriptions/urls.py`** (Modified)

Added new URL routes:
```python
# Telegram Verification (Deep Link + Username Entry)
path('billing/telegram/generate-code/', generate_telegram_verification_code, name='generate_telegram_code'),
path('billing/telegram/verify-username/', verify_telegram_username, name='verify_telegram_username'),
path('billing/telegram/confirm/', confirm_telegram_code, name='confirm_telegram_code'),
path('billing/telegram/status/', check_telegram_verification_status, name='check_telegram_status'),
```

---

### Frontend Files

#### 3. **`frontend/src/lib/api/payment.ts`** (Modified)

**Lines 363-395: Updated `generateTelegramCode`**
```typescript
export async function generateTelegramCode(): Promise<{
  verification_code: string;
  deep_link: string;
  bot_username: string;
  expires_at: string;
}> {
  const response = await fetch(
    `${API_BASE_URL}/billing/telegram/generate-code/`,
    {
      method: 'POST',
      headers: getAuthHeaders(),
    }
  );

  if (!response.ok) {
    await handleApiError(response);
  }

  return response.json();
}
```

**Lines 397-419: New `verifyTelegramUsername`**
```typescript
export async function verifyTelegramUsername(
  verificationCode: string,
  telegramUsername: string
): Promise<{
  success: boolean;
  message: string;
}> {
  const response = await fetch(
    `${API_BASE_URL}/billing/telegram/verify-username/`,
    {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        verification_code: verificationCode,
        telegram_username: telegramUsername,
      }),
    }
  );

  if (!response.ok) {
    await handleApiError(response);
  }

  return response.json();
}
```

**Lines 421-448: New `confirmTelegramVerification`**
```typescript
export async function confirmTelegramVerification(
  verificationCode: string,
  confirmationCode: string
): Promise<{
  success: boolean;
  message: string;
  telegram_username: string;
  verified_at: string;
}> {
  const response = await fetch(
    `${API_BASE_URL}/billing/telegram/confirm/`,
    {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        verification_code: verificationCode,
        confirmation_code: confirmationCode,
      }),
    }
  );

  if (!response.ok) {
    await handleApiError(response);
  }

  return response.json();
}
```

#### 4. **`frontend/src/components/TelegramVerification.tsx`** (Modified)

**Key Changes:**
- Added new state variables: `telegramUsername`, `confirmationCode`, `currentStep`
- Added verification step type: `'bot' | 'username' | 'confirm'`
- Updated imports to use new API functions
- Complete UI overhaul with 3-step flow

**New State Management:**
```typescript
const [currentStep, setCurrentStep] = useState<VerificationStep>('bot');
const [telegramUsername, setTelegramUsername] = useState<string>('');
const [confirmationCode, setConfirmationCode] = useState<string>('');
const [codeSent, setCodeSent] = useState(false);
```

**Step 1: Open Bot (Lines 380-418)**
```tsx
<div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
  <p className="text-sm font-semibold text-blue-900 dark:text-blue-100 mb-2">
    📱 Step 1 of 3: Open Telegram Bot
  </p>
  <p className="text-sm text-blue-800 dark:text-blue-200 mb-3">
    Click the button below to open our Telegram bot in a new tab or window.
  </p>
  <ul className="text-xs text-blue-700 dark:text-blue-300 space-y-1.5 ml-4 list-disc">
    <li>The bot will open automatically in Telegram (app or web)</li>
    <li>You'll see a <strong>START</strong> button - click it to begin</li>
    <li>After clicking START, return to this page to continue</li>
  </ul>
  
  <button onClick={openTelegramBot} className="...">
    Open {botUsername || 'Telegram Bot'}
  </button>
  
  <div className="mt-3 p-2 bg-blue-100 dark:bg-blue-800/30 rounded text-center">
    <p className="text-xs text-blue-800 dark:text-blue-200 font-medium">
      💡 Tip: Keep this page open while you verify in Telegram
    </p>
  </div>
</div>
```

**Step 2: Enter Username (Lines 422-489)**
```tsx
<div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
  <p className="text-sm font-semibold text-blue-900 dark:text-blue-100 mb-2">
    👤 Step 2 of 3: Enter Your Telegram Username
  </p>
  
  <div className="bg-blue-100 dark:bg-blue-800/30 rounded p-3 mb-3">
    <p className="text-xs text-blue-900 dark:text-blue-100 font-medium mb-2">
      📍 How to find your username:
    </p>
    <ol className="text-xs text-blue-800 dark:text-blue-200 space-y-1 ml-4 list-decimal">
      <li>Open Telegram and go to <strong>Settings</strong></li>
      <li>Look for your username (starts with @)</li>
      <li>If you don't have one, tap <strong>"Username"</strong> to create it</li>
    </ol>
  </div>
  
  <input
    type="text"
    value={telegramUsername}
    onChange={(e) => setTelegramUsername(e.target.value)}
    placeholder="@yourusername or yourusername"
    className="..."
  />
  
  <button onClick={handleUsernameSubmit} className="...">
    Continue to Confirmation
  </button>
</div>
```

**Step 3: Confirm Code (Lines 493-570)**
```tsx
<div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
  <div className="flex items-start gap-2 mb-3">
    <svg className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5">...</svg>
    <div className="flex-1">
      <p className="text-sm text-green-800 dark:text-green-200 font-medium mb-1">
        ✅ Code sent to Telegram!
      </p>
      <p className="text-xs text-green-700 dark:text-green-300">
        Check your Telegram chat with {botUsername} for your 6-digit confirmation code
      </p>
    </div>
  </div>
</div>

<div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
  <p className="text-sm font-semibold text-blue-900 dark:text-blue-100 mb-2">
    🔐 Step 3 of 3: Enter Confirmation Code
  </p>
  
  <input
    type="text"
    value={confirmationCode}
    onChange={(e) => setConfirmationCode(e.target.value.toUpperCase())}
    placeholder="123456"
    className="...text-xl font-mono tracking-widest..."
    maxLength={6}
  />
  
  <button onClick={handleConfirmCode} className="...">
    Complete Verification
  </button>
</div>
```

#### 5. **`frontend/src/app/contexts/UserAuthContext.tsx`** (Modified)

**Fixed endpoint from `/api/user/profile/` to `/auth/profile/`:**
```typescript
// Line 151
const data = await apiRequest('/auth/profile/');  // Was: /api/user/profile/
```

#### 6. **`frontend/src/app/utils/userAPI.ts`** (Modified)

**Fixed endpoint:**
```typescript
// Line 21
export const getUserProfile = async (): Promise<UserProfile> => {
  const response = await fetch(`${API_URL}/auth/profile/`, {  // Was: /api/user/profile/
    method: 'GET',
    headers: getHeaders(),
  });
  // ...
};
```

---

## 🔧 Technical Details

### Bot Configuration

The system now uses the **TelegramConfiguration singleton model** instead of hardcoded values:

```python
# backend/subscriptions/models.py (Lines 1792-1850)
class TelegramConfiguration(models.Model):
    """Singleton model for Telegram bot configuration"""
    
    bot_token = models.CharField(max_length=500, blank=True)
    bot_username = models.CharField(max_length=100, blank=True)
    is_enabled = models.BooleanField(default=True)
    is_connected = models.BooleanField(default=False)
    auto_add_enabled = models.BooleanField(default=True)
    welcome_message = models.TextField(blank=True)
    # ... other fields
```

### Deep Link Format

```
https://t.me/{bot_username}?start=VERIFY_{verification_code}

Example:
https://t.me/OxidaneBot?start=VERIFY_OXI-A1B2
```

When user clicks the deep link:
1. Telegram opens (app or web)
2. Bot chat opens with pre-filled `/start VERIFY_OXI-A1B2`
3. User clicks START button
4. Bot receives the command (handled via webhook in production)

### Code Flow

```
Frontend                    Backend                     Telegram API
   |                           |                              |
   |--generateTelegramCode---->|                              |
   |                           |--get bot from DB             |
   |                           |--generate OXI-A1B2           |
   |<----return deep link------|                              |
   |                           |                              |
   |--user opens deep link---->|                              |
   |                           |                              |
   |--verifyTelegramUsername-->|                              |
   |                           |--validate code               |
   |                           |----getChat(@username)------->|
   |                           |<----user data----------------|
   |                           |--generate 123456             |
   |                           |--cache code                  |
   |                           |----sendMessage(123456)------>|
   |<----success message-------|                              |
   |                           |                              |
   |--confirmTelegramCode----->|                              |
   |                           |--get cached data             |
   |                           |--verify 123456               |
   |                           |--link account                |
   |<----verified!-------------|                              |
```

---

## ✅ Benefits Over Old System

| Feature | Old System (Webhook) | New System (Deep Link) |
|---------|---------------------|------------------------|
| **Development** | Requires ngrok | Works locally |
| **Setup** | Manual BotFather commands | Zero setup needed |
| **Bot Changes** | Hardcoded `@OxiWorldBot` | Admin-configurable |
| **Dependencies** | Webhook endpoint required | Direct API calls only |
| **UX** | Text commands | Visual 3-step flow |
| **Debugging** | Complex webhook logs | Simple request/response |
| **Deployment** | Public URL required | No special requirements |

---

## 🧪 Testing Checklist

- [ ] Test code generation with valid auth token
- [ ] Test deep link opens correct bot
- [ ] Test username validation with valid username
- [ ] Test username validation with invalid username
- [ ] Test username without @ symbol works
- [ ] Test code is sent to Telegram
- [ ] Test code confirmation with correct code
- [ ] Test code confirmation with wrong code
- [ ] Test code expiration (5 minutes)
- [ ] Test verification status is saved
- [ ] Test error handling at each step
- [ ] Test "Back" button navigation
- [ ] Test loading states display correctly
- [ ] Test success state shows benefits

---

## 📝 Next Steps

1. **Test end-to-end flow** on checkout page
2. **Verify bot configuration** in admin panel
3. **Test with multiple users** concurrently
4. **Monitor Telegram API rate limits**
5. **Add analytics** for verification success rate
6. **Consider adding:** Email notification when Telegram verified

---

## 🐛 Known Issues / Edge Cases

1. **No Telegram Username:** Some users don't have usernames - need fallback
2. **Bot Not Started:** If user doesn't click START, code sending fails
3. **Rate Limiting:** Telegram API has limits - need to handle gracefully
4. **Code Expiration:** 5-minute window might be too short for some users
5. **Multiple Devices:** User might have Telegram on multiple devices

---

## 🔐 Security Considerations

✅ **Secure:**
- Uses JWT authentication for all endpoints
- 6-digit codes are random and time-limited
- Codes stored in cache (not database) for security
- Verification codes expire after usage
- User must prove ownership of both website account AND Telegram account

⚠️ **Future Enhancements:**
- Add rate limiting on verification attempts
- Add CAPTCHA for code generation
- Encrypt bot token (Phase 0.5.12)
- Add IP-based fraud detection

---

## 📚 References

- **Telegram Bot API:** https://core.telegram.org/bots/api
- **Deep Links:** https://core.telegram.org/bots#deep-linking
- **TelegramConfiguration Model:** `backend/subscriptions/models.py:1792-1850`
- **Billing Views:** `backend/subscriptions/billing_views.py`
- **Payment API:** `frontend/src/lib/api/payment.ts`
- **Verification Component:** `frontend/src/components/TelegramVerification.tsx`

---

## 👥 Team Notes

**For Next Developer:**

This implementation is **complete and ready for testing**. The old webhook-based system is still in the codebase but can be removed after testing confirms the new system works.

**Key Files to Review:**
1. `billing_views.py` - Backend verification logic
2. `TelegramVerification.tsx` - Frontend UI component
3. `payment.ts` - API integration layer

**To Enable:**
1. Ensure TelegramConfiguration has valid bot_token and bot_username
2. Frontend will automatically use the new flow
3. No webhook setup required for development

Good luck! 🚀
