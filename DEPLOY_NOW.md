# Frontend Deployment - Quick Start

## ⚡ Fastest Path: Deploy to Vercel Now

### 1. Go to Vercel
👉 https://vercel.com/new

### 2. Import Your Repo
- Click "Continue with GitHub"
- Select: **DevObiChinaka/oxidane**
- Root Directory: **frontend**

### 3. Add Environment Variables
Copy-paste these into Vercel's environment variables section:

```bash
NEXTAUTH_URL=https://your-app-name.vercel.app
NEXTAUTH_SECRET=LkMlpdXl9HM8zym4oBRBaJT4ykRgvLh/HyNTSE78tOw=
GOOGLE_CLIENT_ID=272603953255-kj2klbtrbbe59cmm6tvif7ddjhjs8q1l.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=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
NEXT_PUBLIC_API_URL=https://oxiworldforexacademy.com/api
```

**Important:** After deployment, Vercel gives you a URL (e.g., `oxidane-abc123.vercel.app`). 
Come back and update `NEXTAUTH_URL` with your actual Vercel URL.

### 4. Deploy
Click **"Deploy"** and wait ~2 minutes

### 5. After Deployment

**Update Google OAuth:**
1. Go to: https://console.cloud.google.com/apis/credentials
2. Edit OAuth Client ID
3. Add redirect URI: `https://your-actual-vercel-url.vercel.app/api/auth/callback/google`

**Update Backend CORS:**
```bash
ssh root@169.255.57.172

# Edit .env
cat >> /var/www/oxidane/backend/.env << 'EOF'
CORS_ALLOWED_ORIGINS=https://oxiworldforexacademy.com,https://www.oxiworldforexacademy.com,https://your-actual-vercel-url.vercel.app
EOF

# Restart
systemctl restart oxidane-gunicorn
```

**Update Backend SECRET_KEY (CRITICAL):**
```bash
# Still in SSH session
cat > /var/www/oxidane/backend/.env << 'EOF'
DATABASE_URL=postgresql://oxidane:Oxidane25@localhost:5432/oxidane_prod
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
DEBUG=False
ENVIRONMENT=production
SECRET_KEY=dim^ovv=a(+2#d$pdky3kr8)980pq%#0vvi6!t05o)k1ehpxt8
ALLOWED_HOSTS=oxiworldforexacademy.com,www.oxiworldforexacademy.com,169.255.57.172,localhost
CORS_ALLOWED_ORIGINS=https://oxiworldforexacademy.com,https://www.oxiworldforexacademy.com,https://your-actual-vercel-url.vercel.app
FRONTEND_URL=https://oxiworldforexacademy.com
STATIC_ROOT=/var/www/oxidane/staticfiles
STATIC_URL=/static/
MEDIA_ROOT=/var/www/oxidane/media
MEDIA_URL=/media/
EOF

systemctl restart oxidane-gunicorn
exit
```

---

## 🎯 Your URLs After Deployment

- **Backend API:** https://oxiworldforexacademy.com/api
- **Backend Admin:** https://oxiworldforexacademy.com/django-admin
- **Frontend:** https://your-app.vercel.app (will be assigned after deploy)

---

## ✅ SSL Issue - Try This

Your backend has valid SSL. If Chrome still shows "not secure":

1. **Hard refresh:** Press `Ctrl + Shift + R`
2. **Clear SSL state:**
   - Go to: `chrome://net-internals/#hsts`
   - Enter: `oxiworldforexacademy.com`
   - Click "Delete domain security policies"
   - Try again in **Incognito mode**

3. **Check mixed content:**
   - Open site in Chrome
   - Press `F12` (DevTools)
   - Look for HTTP requests (should all be HTTPS)

---

## 📋 Deployment Checklist

Before deploying:
- [ ] Backend SECRET_KEY updated (see command above)
- [ ] Backend running: https://oxiworldforexacademy.com/api/
- [ ] SSL certificate valid (expires Feb 25, 2026 ✅)

During deployment:
- [ ] Vercel account created
- [ ] Repository imported
- [ ] Environment variables added
- [ ] Deploy button clicked

After deployment:
- [ ] Note your Vercel URL
- [ ] Update NEXTAUTH_URL in Vercel env vars
- [ ] Update Google OAuth redirect URI
- [ ] Update backend CORS_ALLOWED_ORIGINS
- [ ] Test login on frontend
- [ ] Test API connection
- [ ] Test payment flow

---

**Time to deploy: ~10 minutes**
**See VERCEL_DEPLOYMENT_GUIDE.md for detailed instructions**
