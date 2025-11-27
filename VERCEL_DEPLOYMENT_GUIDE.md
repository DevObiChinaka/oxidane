# Frontend Deployment Guide - Vercel

## Overview
Deploy your Next.js frontend to Vercel (free tier, optimized for Next.js)

## Prerequisites
✅ Backend deployed at: https://oxiworldforexacademy.com
✅ GitHub repository: DevObiChinaka/oxidane
✅ Branch: mySaaS

---

## Option 1: Deploy via Vercel Dashboard (Recommended - Easiest)

### Step 1: Create Vercel Account
1. Go to https://vercel.com
2. Click **"Sign Up"**
3. Choose **"Continue with GitHub"**
4. Authorize Vercel to access your GitHub account

### Step 2: Import Your Repository
1. Click **"Add New..."** → **"Project"**
2. Find and select **"DevObiChinaka/oxidane"** repository
3. If not visible, click **"Adjust GitHub App Permissions"** to grant access

### Step 3: Configure Project Settings
```
Framework Preset: Next.js
Root Directory: frontend
Build Command: npm run build (auto-detected)
Output Directory: .next (auto-detected)
Install Command: npm install (auto-detected)
```

### Step 4: Add Environment Variables
In the Vercel project settings, add these environment variables:

**Required:**
```bash
NEXTAUTH_URL=https://your-app-name.vercel.app
NEXTAUTH_SECRET=generate-new-secret-see-below
GOOGLE_CLIENT_ID=272603953255-kj2klbtrbbe59cmm6tvif7ddjhjs8q1l.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=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
NEXT_PUBLIC_API_URL=https://oxiworldforexacademy.com/api
NEXT_PUBLIC_PAYSTACK_PUBLIC_KEY=pk_test_4c1e965ff610e87ab67614df6e24300ef3470fa7
```

**Generate NEXTAUTH_SECRET:**
```bash
# Run this in PowerShell:
node -e "console.log(require('crypto').randomBytes(32).toString('base64'))"
```

### Step 5: Deploy
1. Click **"Deploy"**
2. Wait 2-3 minutes for build to complete
3. You'll get a URL like: `https://oxidane-xyz123.vercel.app`

### Step 6: Update Google OAuth Redirect URI
1. Go to: https://console.cloud.google.com/apis/credentials
2. Edit your OAuth 2.0 Client ID
3. Add to **Authorized redirect URIs**:
   ```
   https://your-app-name.vercel.app/api/auth/callback/google
   ```
4. Save

### Step 7: Update Backend CORS
SSH into your VPS and update the .env file:

```bash
ssh root@169.255.57.172

# Edit .env to add Vercel URL to CORS_ALLOWED_ORIGINS
nano /var/www/oxidane/backend/.env

# Add your Vercel URL:
CORS_ALLOWED_ORIGINS=https://oxiworldforexacademy.com,https://www.oxiworldforexacademy.com,https://your-app-name.vercel.app

# Restart Gunicorn
systemctl restart oxidane-gunicorn
```

---

## Option 2: Custom Domain on Vercel (Optional)

### Use oxiworldforexacademy.com for Frontend

1. In Vercel project settings → **Domains**
2. Click **"Add Domain"**
3. Enter: `app.oxiworldforexacademy.com` or just `oxiworldforexacademy.com`
4. Vercel will show DNS records to add

**If using subdomain (app.oxiworldforexacademy.com):**
- Go to Namecheap DNS settings
- Add CNAME record:
  ```
  Type: CNAME
  Host: app
  Value: cname.vercel-dns.com
  ```

**If using root domain (oxiworldforexacademy.com):**
- This conflicts with your backend. Better to use subdomain or separate domain
- Recommended: Use `app.oxiworldforexacademy.com` for frontend

### After Adding Custom Domain
Update environment variables in Vercel:
```bash
NEXTAUTH_URL=https://app.oxiworldforexacademy.com
```

Update Google OAuth redirect URI:
```
https://app.oxiworldforexacademy.com/api/auth/callback/google
```

---

## Option 3: Deploy via Vercel CLI

### Install Vercel CLI
```powershell
npm install -g vercel
```

### Login to Vercel
```powershell
vercel login
```

### Deploy from Frontend Directory
```powershell
cd c:\Users\user\OneDrive\Desktop\Oxidane\frontend
vercel
```

Follow the prompts:
- Set up and deploy? **Yes**
- Which scope? Select your account
- Link to existing project? **No**
- Project name? **oxidane** or **oxiworld**
- Directory? **. (current directory)**
- Override settings? **No**

---

## Post-Deployment Checklist

✅ Frontend deployed and accessible
✅ Environment variables configured
✅ Google OAuth redirect URI updated
✅ Backend CORS updated with frontend URL
✅ Test login flow
✅ Test API connection
✅ Test payment flow (if using live Paystack keys)

---

## Troubleshooting

### "API connection failed"
- Check `NEXT_PUBLIC_API_URL` points to `https://oxiworldforexacademy.com/api`
- Verify backend CORS includes frontend URL
- Check backend is running: `ssh root@169.255.57.172 "systemctl status oxidane-gunicorn"`

### "OAuth Error: redirect_uri_mismatch"
- Verify Google OAuth redirect URI includes Vercel URL
- Format: `https://your-app.vercel.app/api/auth/callback/google`

### "NextAuth secret not found"
- Verify `NEXTAUTH_SECRET` is set in Vercel environment variables
- Generate new one: `node -e "console.log(require('crypto').randomBytes(32).toString('base64'))"`

### Build fails on Vercel
- Check build logs in Vercel dashboard
- Verify `package.json` has all dependencies
- Try local build first: `npm run build`

---

## Alternative: Netlify Deployment

If you prefer Netlify:

1. Go to https://netlify.com
2. Click **"Add new site"** → **"Import an existing project"**
3. Connect to GitHub
4. Select repository: `DevObiChinaka/oxidane`
5. Configure:
   ```
   Base directory: frontend
   Build command: npm run build
   Publish directory: .next
   ```
6. Add same environment variables as Vercel
7. Deploy

---

## Production Recommendations

1. **Use Vercel Pro** ($20/month) for:
   - Custom domain SSL
   - Better performance
   - Analytics
   - Priority support

2. **Switch to Live Paystack Keys**
   - Get from: https://dashboard.paystack.com/#/settings/developers
   - Replace `pk_test_*` with `pk_live_*`

3. **Monitor Performance**
   - Vercel Analytics (free tier included)
   - Backend logs: `ssh root@169.255.57.172 "journalctl -u oxidane-gunicorn -f"`

4. **Enable HTTPS Everywhere**
   - All URLs should use HTTPS
   - No mixed content warnings

---

## Next Steps After Deployment

1. Test complete user flow:
   - Sign up with Google
   - Purchase subscription
   - Access course content
   - Join Telegram group

2. Configure email notifications (if not in singleton):
   - Test email verification
   - Test password reset

3. Set up monitoring:
   - Vercel deployment notifications
   - Backend uptime monitoring
   - Error tracking (Sentry)

4. Update documentation with live URLs

---

**Ready to deploy? Start with Option 1 (Vercel Dashboard) - it's the easiest!**
