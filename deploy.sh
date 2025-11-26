#!/bin/bash
# Complete deployment script - run this after server setup
# Run as root

set -e

echo "🚀 Deploying Oxidane to production..."

# Copy service files
cp oxidane-gunicorn.service /etc/systemd/system/
cp oxidane-celery.service /etc/systemd/system/
cp oxidane-celery-beat.service /etc/systemd/system/

# Copy nginx configuration
cp nginx_oxidane.conf /etc/nginx/sites-available/oxidane
ln -sf /etc/nginx/sites-available/oxidane /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
nginx -t

# Reload systemd and start services
systemctl daemon-reload
systemctl enable oxidane-gunicorn oxidane-celery oxidane-celery-beat nginx
systemctl start oxidane-gunicorn
systemctl start oxidane-celery  
systemctl start oxidane-celery-beat
systemctl restart nginx

# Setup SSL certificate
certbot --nginx -d oxiworld.app -d www.oxiworld.app --non-interactive --agree-tos --email your-email@example.com

echo "✅ Deployment complete!"
echo ""
echo "🔍 Check service status:"
echo "systemctl status oxidane-gunicorn"
echo "systemctl status oxidane-celery"
echo "systemctl status nginx"
echo ""
echo "📊 Monitor logs:"
echo "journalctl -fu oxidane-gunicorn"
echo "tail -f /var/log/celery/worker.log"
echo ""
echo "🌐 Your site should be live at: https://oxiworld.app"