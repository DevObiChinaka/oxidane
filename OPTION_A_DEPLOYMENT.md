# Option A Implementation Guide
## Frontend: oxiworldforexacademy.com | Backend: api.oxiworldforexacademy.com

Professional standard architecture with frontend on root domain and backend on API subdomain.

---

## Phase 1: Backend Migration to API Subdomain

### Step 1: Add DNS Record for API Subdomain

In **MyHostAfrica DNS Management**, add:
```
Type: A
Name: api
Value: 169.255.57.172
TTL: 3600
```

**Verify DNS propagation (wait 5-10 minutes):**
```powershell
nslookup api.oxiworldforexacademy.com
```

### Step 2: Update VPS Configuration

#### 2.1: Upload Scripts to VPS

```powershell
cd C:\Users\user\OneDrive\Desktop\Oxidane\backend
scp update_nginx_api_subdomain.sh root@169.255.57.172:/root/
scp update_django_settings.sh root@169.255.57.172:/root/
```

#### 2.2: SSH into VPS

```bash
ssh root@169.255.57.172
```

#### 2.3: Run Nginx Update

```bash
chmod +x /root/update_nginx_api_subdomain.sh
/root/update_nginx_api_subdomain.sh
```

#### 2.4: Get SSL Certificate for API Subdomain

```bash
sudo certbot --nginx -d api.oxiworldforexacademy.com
```

Select option to redirect HTTP to HTTPS.

#### 2.5: Update Django Settings

```bash
chmod +x /root/update_django_settings.sh
/root/update_django_settings.sh
```

#### 2.6: Update SECRET_KEY (CRITICAL!)

```bash
cd /var/www/oxidane
nano .env
```

Find and replace:
```bash
SECRET_KEY=dim^ovv=a(+2#d$pdky3kr8)980pq%#0vvi6!t05o)k1ehpxt8
```

Save (Ctrl+X, Y, Enter), then restart:
```bash
sudo systemctl restart oxidane-gunicorn
sudo systemctl status oxidane-gunicorn
```

#### 2.7: Verify Backend

```bash
curl https://api.oxiworldforexacademy.com/health
curl https://api.oxiworldforexacademy.com/api/
```

✅ You can now exit SSH.

---

## Phase 2: Frontend Deployment to Vercel

### Step 3: Commit Updated Environment Variables

```powershell
cd C:\Users\user\OneDrive\Desktop\Oxidane
git add frontend/.env.production
git commit -m "Update API URL to api.oxiworldforexacademy.com subdomain"
git push
```

### Step 4: Deploy to Vercel

#### 4.1: Import Project

1. Go to https://vercel.com/new
2. Click "Import Git Repository"
3. Select `DevObiChinaka/oxidane`
4. Configure:
   - **Framework:** Next.js
   - **Root Directory:** `frontend`
   - **Branch:** `mySaaS`

#### 4.2: Set Environment Variables

Click "Environment Variables" and add:

| Name | Value |
|------|-------|
| NEXTAUTH_URL | https://oxiworldforexacademy.com |
| NEXTAUTH_SECRET | LkMlpdXl9HM8zym4oBRBaJT4ykRgvLh/HyNTSE78tOw= |
| GOOGLE_CLIENT_ID | 272603953255-kj2klbtrbbe59cmm6tvif7ddjhjs8q1l.apps.googleusercontent.com |
| GOOGLE_CLIENT_SECRET | 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 |
| NEXT_PUBLIC_API_URL | https://api.oxiworldforexacademy.com/api |
| NEXT_PUBLIC_PAYSTACK_PUBLIC_KEY | pk_live_your_live_key_here |

**Note:** Get Paystack LIVE key from https://dashboard.paystack.com/#/settings/developers

#### 4.3: Deploy

Click "Deploy" - takes about 2-3 minutes.

Vercel will assign a temporary URL like: `oxidane-abc123.vercel.app`

### Step 5: Add Custom Domain

#### 5.1: In Vercel Dashboard

1. Go to Project → Settings → Domains
2. Add domain: `oxiworldforexacademy.com`
3. Vercel shows required DNS records

#### 5.2: Update DNS in MyHostAfrica

**Current DNS (Before):**
```
Type: A
Name: @
Value: 169.255.57.172  ← Points to VPS
```

**New DNS (After):**
```
Type: A
Name: @
Value: 76.76.21.21  ← Vercel's IP (check Vercel dashboard for exact IP)

Type: A
Name: api
Value: 169.255.57.172  ← Backend stays on VPS
```

**Important:** Vercel will tell you the exact IP address in the dashboard. Use that instead of 76.76.21.21 if different.

#### 5.3: Wait for DNS Propagation

Usually takes 5-30 minutes. Check with:
```powershell
nslookup oxiworldforexacademy.com
nslookup api.oxiworldforexacademy.com
```

#### 5.4: Vercel Auto-SSL

Once DNS propagates, Vercel automatically provisions SSL certificate. Wait for "SSL Certificate Ready" message.

---

## Phase 3: Post-Deployment Configuration

### Step 6: Update Google OAuth

Go to https://console.cloud.google.com/apis/credentials

Update **Authorized redirect URIs**:
```
https://oxiworldforexacademy.com/api/auth/callback/google
https://api.oxiworldforexacademy.com/auth/google/callback/
```

### Step 7: Test Everything

#### 7.1: Frontend
- Visit https://oxiworldforexacademy.com
- Should load homepage
- Check browser console for errors

#### 7.2: API Connection
- Try signing up/logging in
- Check Network tab - API calls should go to `api.oxiworldforexacademy.com`

#### 7.3: Google OAuth
- Click "Continue with Google"
- Should redirect properly and log you in

#### 7.4: Payment Flow
- Navigate to pricing page
- Select a plan
- Verify Paystack modal opens
- Complete test transaction

---

## Final Architecture

```
┌─────────────────────────────────────────┐
│  oxiworldforexacademy.com               │
│  ├─ Frontend (Next.js on Vercel)        │
│  ├─ Auto-deployed from mySaaS branch    │
│  └─ Global CDN (fast worldwide)         │
└─────────────────────────────────────────┘
                   ↓ API calls
┌─────────────────────────────────────────┐
│  api.oxiworldforexacademy.com           │
│  ├─ Django Backend (VPS)                │
│  ├─ PostgreSQL + Redis + Celery         │
│  └─ IP: 169.255.57.172                  │
└─────────────────────────────────────────┘
```

---

## Rollback Plan

If something goes wrong:

### Revert DNS:
```
Type: A
Name: @
Value: 169.255.57.172
```

### Revert Nginx:
```bash
ssh root@169.255.57.172
sudo cp /etc/nginx/sites-available/oxidane.backup /etc/nginx/sites-available/oxidane
sudo systemctl reload nginx
```

### Revert Django .env:
```bash
cp /var/www/oxidane/.env.backup /var/www/oxidane/.env
sudo systemctl restart oxidane-gunicorn
```

---

## Success Checklist

- [ ] DNS propagated for api.oxiworldforexacademy.com
- [ ] SSL certificate for api subdomain (Let's Encrypt)
- [ ] Backend responding at https://api.oxiworldforexacademy.com/health
- [ ] Django SECRET_KEY updated (not placeholder)
- [ ] Frontend deployed to Vercel
- [ ] Custom domain configured on Vercel
- [ ] DNS pointing root domain to Vercel
- [ ] Vercel SSL certificate active
- [ ] Google OAuth redirect URIs updated
- [ ] Frontend loads at https://oxiworldforexacademy.com
- [ ] API calls working (check Network tab)
- [ ] Login/signup working
- [ ] Google OAuth login working
- [ ] Payment flow working

---

**Ready to start?** Begin with Phase 1, Step 1 (add DNS record for api subdomain).
