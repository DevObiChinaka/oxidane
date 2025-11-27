#!/bin/bash
# MyHostAfrica C1 Optimized Deployment Script
# For 1 vCPU, 2GB RAM, 30GB SSD VPS
# ==========================================

set -e
trap 'echo "❌ Deployment failed at line $LINENO"' ERR

echo "🚀 MyHostAfrica C1 Deployment Starting"
echo "======================================"

# Check system resources
echo "📊 Checking C1 system resources..."
echo "Memory: $(free -h | grep Mem | awk '{print $3"/"$2}')"
echo "Disk: $(df -h / | tail -1 | awk '{print $3"/"$2" ("$5" used)"}')"
echo ""

# Activate virtual environment
echo "🐍 Activating Python environment..."
cd /var/www/oxidane
source venv/bin/activate

# Install dependencies with C1 optimizations
echo "📦 Installing dependencies (C1 optimized)..."
pip install --no-cache-dir -r backend/requirements.txt

# Set up environment variables
echo "⚙️ Configuring environment..."
if [ ! -f backend/.env ]; then
    cp myhostafrica_c1_production.env backend/.env
    echo "✅ Created .env from C1 template"
else
    echo "⚠️  .env already exists, please verify settings"
fi

# Collect static files
echo "📁 Collecting static files..."
cd backend
python manage.py collectstatic --noinput --clear

# Run database migrations
echo "🗄️ Running database migrations..."
python manage.py migrate

# Create superuser if needed
echo "👤 Creating admin user..."
python manage.py shell << 'EOF'
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@oxiworldforexacademy.com', 'secure_admin_password_2024')
    print("✅ Admin user created")
else:
    print("ℹ️  Admin user already exists")
EOF

# Set up Gunicorn service (C1 optimized)
echo "🔧 Setting up Gunicorn service..."
sudo tee /etc/systemd/system/oxidane-gunicorn.service > /dev/null << EOF
[Unit]
Description=Oxidane Gunicorn (C1 Optimized)
After=network.target

[Service]
User=oxidane
Group=oxidane
WorkingDirectory=/var/www/oxidane/backend
Environment="PATH=/var/www/oxidane/venv/bin"
ExecStart=/var/www/oxidane/venv/bin/gunicorn \\
    --workers 2 \\
    --threads 2 \\
    --timeout 30 \\
    --keep-alive 5 \\
    --max-requests 500 \\
    --max-requests-jitter 50 \\
    --preload \\
    --bind 127.0.0.1:8000 \\
    --log-level info \\
    --log-file /var/log/oxidane/gunicorn.log \\
    --access-logfile /var/log/oxidane/gunicorn-access.log \\
    oxidane.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

# C1 resource limits
MemoryMax=512M
CPUQuota=50%

[Install]
WantedBy=multi-user.target
EOF

# Set up Celery worker service (C1 optimized)
echo "⚙️ Setting up Celery worker..."
sudo tee /etc/systemd/system/oxidane-celery.service > /dev/null << EOF
[Unit]
Description=Oxidane Celery Worker (C1 Optimized)
After=network.target redis.service

[Service]
Type=exec
User=oxidane
Group=oxidane
WorkingDirectory=/var/www/oxidane/backend
Environment="PATH=/var/www/oxidane/venv/bin"
ExecStart=/var/www/oxidane/venv/bin/celery -A oxidane worker \\
    --concurrency=2 \\
    --prefetch-multiplier=1 \\
    --max-tasks-per-child=100 \\
    --time-limit=600 \\
    --soft-time-limit=300 \\
    --loglevel=info \\
    --logfile=/var/log/oxidane/celery-worker.log
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
Restart=always
RestartSec=10

# C1 resource limits
MemoryMax=256M
CPUQuota=25%

[Install]
WantedBy=multi-user.target
EOF

# Set up Celery Beat service
echo "⏰ Setting up Celery Beat..."
sudo tee /etc/systemd/system/oxidane-celery-beat.service > /dev/null << EOF
[Unit]
Description=Oxidane Celery Beat Scheduler
After=network.target redis.service

[Service]
Type=exec
User=oxidane
Group=oxidane
WorkingDirectory=/var/www/oxidane/backend
Environment="PATH=/var/www/oxidane/venv/bin"
ExecStart=/var/www/oxidane/venv/bin/celery -A oxidane beat \\
    --loglevel=info \\
    --logfile=/var/log/oxidane/celery-beat.log \\
    --pidfile=/var/run/celery/beat.pid
ExecReload=/bin/kill -s HUP \$MAINPID
RuntimeDirectory=celery
RuntimeDirectoryMode=0755
Restart=always
RestartSec=10

# Minimal resources for scheduler
MemoryMax=128M
CPUQuota=10%

[Install]
WantedBy=multi-user.target
EOF

# Set up Nginx configuration
echo "🌐 Setting up Nginx..."
sudo cp ../nginx_myhostafrica_c1.conf /etc/nginx/sites-available/oxidane
sudo ln -sf /etc/nginx/sites-available/oxidane /etc/nginx/sites-enabled/oxidane
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Set up log rotation
echo "📋 Setting up log rotation..."
sudo tee /etc/logrotate.d/oxidane > /dev/null << EOF
/var/log/oxidane/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    copytruncate
    maxsize 20M
    postrotate
        systemctl reload oxidane-gunicorn oxidane-celery
    endscript
}
EOF

# Create monitoring script for C1
echo "📊 Creating C1 monitoring script..."
sudo tee /usr/local/bin/oxidane-c1-monitor.sh > /dev/null << 'EOF'
#!/bin/bash
# MyHostAfrica C1 Resource Monitor

echo "🖥️  MyHostAfrica C1 Resource Monitor"
echo "===================================="
echo "$(date)"
echo ""

# Memory usage
echo "💾 Memory Usage:"
free -h | grep -E "Mem|Swap"
echo ""

# Disk usage
echo "💽 Disk Usage:"
df -h / | tail -1
echo ""

# CPU load
echo "⚡ CPU Load:"
uptime
echo ""

# Service status
echo "🔧 Service Status:"
systemctl is-active oxidane-gunicorn || echo "❌ Gunicorn stopped"
systemctl is-active oxidane-celery || echo "❌ Celery stopped"  
systemctl is-active nginx || echo "❌ Nginx stopped"
systemctl is-active postgresql || echo "❌ PostgreSQL stopped"
systemctl is-active redis-server || echo "❌ Redis stopped"
echo ""

# Check if resources are over thresholds
MEMORY_USED=$(free | awk 'NR==2{printf "%.0f", $3*100/$2 }')
DISK_USED=$(df / | awk 'NR==2{print $(NF-1)}' | sed 's/%//')

if [ "$MEMORY_USED" -gt 80 ]; then
    echo "⚠️  WARNING: Memory usage is ${MEMORY_USED}% (>80%)"
fi

if [ "$DISK_USED" -gt 80 ]; then
    echo "⚠️  WARNING: Disk usage is ${DISK_USED}% (>80%)"
fi
EOF

sudo chmod +x /usr/local/bin/oxidane-c1-monitor.sh

# Reload systemd and start services
echo "🔄 Starting optimized services..."
sudo systemctl daemon-reload
sudo systemctl enable oxidane-gunicorn
sudo systemctl enable oxidane-celery
sudo systemctl enable oxidane-celery-beat
sudo systemctl start oxidane-gunicorn
sudo systemctl start oxidane-celery
sudo systemctl start oxidane-celery-beat
sudo systemctl reload nginx

# Final system check
echo ""
echo "🔍 Final system check..."
sleep 5

# Check service status
echo "📊 Service Status:"
services=("oxidane-gunicorn" "oxidane-celery" "oxidane-celery-beat" "nginx" "postgresql" "redis-server")
for service in "${services[@]}"; do
    if systemctl is-active --quiet "$service"; then
        echo "✅ $service: running"
    else
        echo "❌ $service: stopped"
    fi
done

echo ""
echo "💾 Final Resource Check:"
/usr/local/bin/oxidane-c1-monitor.sh

echo ""
echo "✅ MyHostAfrica C1 Deployment Complete!"
echo "======================================="
echo ""
echo "🎯 C1 Optimizations Applied:"
echo "• Gunicorn: 2 workers, 2 threads"
echo "• Celery: 2 concurrent workers"
echo "• Memory limits: Gunicorn 512MB, Celery 256MB"
echo "• CPU quotas: Conservative allocation"
echo "• Log rotation: 7 days, 20MB max"
echo ""
echo "🌐 Next Steps:"
echo "1. Configure SSL: sudo certbot --nginx -d oxiworldforexacademy.com"
echo "2. Update DNS A records to point to this VPS IP"
echo "3. Configure payment keys in .env file"
echo "4. Set up Telegram bot webhook"
echo "5. Monitor resources: /usr/local/bin/oxidane-c1-monitor.sh"
echo ""
echo "⚠️  C1 Monitoring Commands:"
echo "• Resource monitor: /usr/local/bin/oxidane-c1-monitor.sh"
echo "• Service status: systemctl status oxidane-gunicorn"
echo "• View logs: journalctl -fu oxidane-gunicorn"
echo "• Memory usage: free -h"
echo "• Disk usage: df -h"
echo ""
echo "📈 Upgrade to C2 if:"
echo "• Memory consistently >80%"
echo "• High swap usage"
echo "• Slow response times"