# Environment File Management

## Single Source of Truth

**`production.env`** is the ONLY environment configuration file for this project.

## File Locations

- **Local**: `backend/.env` (copy of production.env)
- **Server**: `/var/www/oxidane/backend/.env` (deployed from production.env)

## Updating Environment Variables

### 1. Edit production.env
Make all changes in `production.env` file

### 2. Sync to local backend
```powershell
Copy-Item production.env backend\.env
```

### 3. Deploy to server
```powershell
scp production.env root@169.255.57.172:/var/www/oxidane/backend/.env
ssh root@169.255.57.172 "systemctl restart oxidane-gunicorn"
```

## Important Notes

- ❌ DO NOT create new env files (hostinger_production.env, myhostafrica_production.env, etc.)
- ✅ ALWAYS edit production.env and sync it
- ✅ Backend/.env is auto-generated from production.env
- ✅ Server .env is deployed from production.env

## Current Configuration

- Database: PostgreSQL (oxidane_prod, password: Oxidane25)
- Redis: Cloud Redis Labs
- CORS: oxiworldforexacademy.com + www subdomain
- Email: Managed via Admin UI (fallback: chiderachinaka06@gmail.com)
- Telegram: Configured in settings
- DEBUG: False (production mode)
