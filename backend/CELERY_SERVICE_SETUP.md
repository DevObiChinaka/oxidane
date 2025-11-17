# Celery Service Setup for Windows

This guide explains how to set up Celery Worker and Beat as Windows services that start automatically.

## Quick Start (Development)

For development/testing, simply run:

```powershell
# Terminal 1 - Worker (processes tasks)
.\start_celery_worker.bat

# Terminal 2 - Beat (schedules periodic tasks)
.\start_celery_beat.bat
```

## Production Setup (Windows Service)

For production, install Celery as Windows services that start automatically on boot.

### Prerequisites

1. **NSSM (Non-Sucking Service Manager)**
   - Download: https://nssm.cc/download
   - Extract `nssm.exe` to a folder (e.g., `C:\nssm\`)
   - Add to PATH or note the full path

### Installation Steps

1. **Open PowerShell as Administrator**
   - Right-click PowerShell → "Run as Administrator"

2. **Navigate to backend directory**
   ```powershell
   cd C:\Users\user\OneDrive\Desktop\Oxidane\backend
   ```

3. **Run installer script**
   ```powershell
   # If NSSM is in PATH
   .\install_celery_service.ps1

   # If NSSM is not in PATH
   .\install_celery_service.ps1 -NssmPath "C:\nssm\nssm.exe"
   ```

4. **Verify services are running**
   ```powershell
   Get-Service Oxidane*
   ```

   You should see:
   - `OxidaneCeleryWorker` - Status: Running
   - `OxidaneCeleryBeat` - Status: Running

### Service Management

**View service status:**
```powershell
Get-Service Oxidane*
```

**Stop services:**
```powershell
Stop-Service OxidaneCeleryWorker
Stop-Service OxidaneCeleryBeat
```

**Start services:**
```powershell
Start-Service OxidaneCeleryWorker
Start-Service OxidaneCeleryBeat
```

**Restart services:**
```powershell
Restart-Service OxidaneCeleryWorker
Restart-Service OxidaneCeleryBeat
```

**View logs:**
```powershell
# Worker logs
Get-Content logs\celery_worker.log -Tail 50 -Wait

# Beat logs
Get-Content logs\celery_beat.log -Tail 50 -Wait
```

**Remove services (if needed):**
```powershell
nssm remove OxidaneCeleryWorker confirm
nssm remove OxidaneCeleryBeat confirm
```

## What Each Service Does

### Celery Worker (`OxidaneCeleryWorker`)
Processes asynchronous tasks:
- ✅ Add users to Telegram groups after subscription
- ✅ Send payment receipt emails
- ✅ Process auto-renewals
- ✅ Remove users from Telegram groups
- ✅ Send welcome messages
- ✅ Activate subscriptions

### Celery Beat (`OxidaneCeleryBeat`)
Schedules periodic tasks:
- 🔄 Check expired subscriptions (every hour)
- 🔄 Process auto-renewals (daily at midnight)
- 🔄 Send renewal reminders (daily)
- 🔄 Update exchange rates (every 6 hours)

## Troubleshooting

### Services won't start
1. Check logs in `backend\logs\` directory
2. Verify Redis is accessible
3. Check Django settings are correct

### Tasks not processing
1. Verify worker service is running: `Get-Service OxidaneCeleryWorker`
2. Check worker logs: `Get-Content logs\celery_worker.log -Tail 50`
3. Restart worker: `Restart-Service OxidaneCeleryWorker`

### Scheduled tasks not running
1. Verify beat service is running: `Get-Service OxidaneCeleryBeat`
2. Check beat logs: `Get-Content logs\celery_beat.log -Tail 50`
3. Restart beat: `Restart-Service OxidaneCeleryBeat`

### View real-time logs
```powershell
# Worker
Get-Content logs\celery_worker_stdout.log -Tail 50 -Wait

# Beat
Get-Content logs\celery_beat_stdout.log -Tail 50 -Wait
```

## Linux/Mac Production Setup

For Linux/Mac servers, use systemd or supervisor instead:

### Using systemd (Recommended for Linux)

Create `/etc/systemd/system/celery-worker.service`:
```ini
[Unit]
Description=Oxidane Celery Worker
After=network.target redis.target

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/path/to/oxidane/backend
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/celery -A oxidane worker --loglevel=info --logfile=/var/log/celery/worker.log --detach

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/celery-beat.service`:
```ini
[Unit]
Description=Oxidane Celery Beat
After=network.target redis.target

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/path/to/oxidane/backend
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/celery -A oxidane beat --loglevel=info --logfile=/var/log/celery/beat.log --detach

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable celery-worker celery-beat
sudo systemctl start celery-worker celery-beat
sudo systemctl status celery-worker celery-beat
```

## Testing After Setup

1. **Delete test subscriptions:**
   ```powershell
   python manage.py shell -c "from django.contrib.auth import get_user_model; from subscriptions.models import Subscription, BillingProfile; User = get_user_model(); user = User.objects.get(email='obbinachidera123@gmail.com'); bp = BillingProfile.objects.get(user=user); Subscription.objects.filter(billing_profile=bp).delete()"
   ```

2. **Make a test purchase** via the frontend

3. **Verify automation:**
   - Subscription created immediately
   - Telegram invite sent within 5 seconds
   - Payment receipt email sent within 10 seconds

4. **Check logs:**
   ```powershell
   Get-Content logs\celery_worker.log -Tail 20
   ```

   Should show:
   ```
   [INFO] Activating subscription for payment ...
   [INFO] Adding user ... to Telegram groups
   [INFO] ✅ Sent single-use invite link for TradeHub
   [INFO] Payment receipt email sent to ...
   ```

## Production Checklist

- [ ] NSSM installed
- [ ] Services installed and running
- [ ] Logs directory created
- [ ] Test purchase completes successfully
- [ ] Telegram invite sent automatically
- [ ] Email receipt sent automatically
- [ ] Services restart on server reboot (test)
- [ ] Monitor logs for errors daily

## Support

If you encounter issues:
1. Check logs in `backend\logs\`
2. Verify Redis connection
3. Ensure Django migrations are applied
4. Check Telegram bot token is valid
5. Verify Paystack API keys are correct
