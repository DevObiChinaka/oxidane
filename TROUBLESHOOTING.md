# 🔧 Google Sign-In Troubleshooting Guide

## Most Common Issues & Solutions:

### 1. **Firebase Console Configuration**

Check these in your Firebase Console (https://console.firebase.google.com/project/oxidane-dd474):

**Authentication → Sign-in method:**

- ✅ Google provider must be **ENABLED**
- ✅ Web SDK configuration should show your domain

**Authentication → Settings → Authorized domains:**

- ✅ `localhost` must be listed
- ✅ `oxidane-dd474.firebaseapp.com` must be listed
- ✅ If using custom domain, add that too

### 2. **Common Error Codes & Fixes**

**`auth/unauthorized-domain`**

- Add `localhost` to authorized domains in Firebase Console
- Add your production domain if deploying

**`auth/operation-not-allowed`**

- Enable Google provider in Firebase Console → Authentication → Sign-in method

**`auth/popup-blocked`**

- Browser blocked popup - this is handled with redirect fallback
- Allow popups for localhost in browser settings

**`auth/network-request-failed`**

- Check internet connection
- Verify Firebase domain is accessible
- Check for firewall/antivirus blocking

**`auth/invalid-api-key`**

- Verify API key in .env.local matches Firebase Console
- Check for extra spaces or missing characters

### 3. **Browser-Specific Issues**

**Chrome:**

- Allow popups for localhost
- Clear cache/cookies for localhost
- Disable extensions that might block auth

**Firefox:**

- Check popup blocker settings
- Ensure tracking protection allows authentication

### 4. **Environment Variables Check**

Verify your `.env.local` file has all required values:

```
NEXT_PUBLIC_FIREBASE_API_KEY=AIzaSyCEQNx8yJWgmfEeelZrtmG6cagoFNoO1BM
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=oxidane-dd474.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=oxidane-dd474
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=oxidane-dd474.firebasestorage.app
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=797182841637
NEXT_PUBLIC_FIREBASE_APP_ID=1:797182841637:web:d03efbfbcdc7d7f5c6c0cc
```

### 5. **Testing Steps**

1. Open http://localhost:3001/auth
2. Open Developer Tools (F12) → Console tab
3. Click "Sign in with Google"
4. Check console for detailed error messages
5. Report the specific error code/message

---

**Next Steps:** Please share the exact error message from your browser console so I can provide a targeted fix! 🎯
