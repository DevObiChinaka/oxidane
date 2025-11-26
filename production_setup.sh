#!/bin/bash
# Complete Hetzner VPS setup for Django + PostgreSQL + Redis + Celery
# Run as root: curl -sSL https://raw.githubusercontent.com/yourusername/oxidane/main/production_setup.sh | bash

set -e

echo "🚀 Setting up Oxidane production server..."

# Update system
apt update && apt upgrade -y

# Create app user
useradd -m -s /bin/bash oxidane
usermod -aG sudo oxidane

# Install essential packages
apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib redis-server nginx git curl software-properties-common

# Install Node.js (for frontend builds if needed)
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

# Create project directory
mkdir -p /var/www/oxidane
chown oxidane:oxidane /var/www/oxidane

# Setup PostgreSQL
sudo -u postgres createuser --createdb oxidane
sudo -u postgres psql -c "ALTER USER oxidane WITH PASSWORD 'your_secure_password_here';"
sudo -u postgres createdb oxidane_production -O oxidane

# Configure PostgreSQL
echo "host    all             all             127.0.0.1/32            md5" >> /etc/postgresql/*/main/pg_hba.conf
systemctl restart postgresql
systemctl enable postgresql

# Configure Redis
sed -i 's/^# requireauth/requireauth your_redis_password_here/' /etc/redis/redis.conf
sed -i 's/^save/#save/' /etc/redis/redis.conf
echo "save 900 1" >> /etc/redis/redis.conf
echo "save 300 10" >> /etc/redis/redis.conf  
echo "save 60 10000" >> /etc/redis/redis.conf
systemctl restart redis-server
systemctl enable redis-server

# Setup firewall
ufw --force enable
ufw allow ssh
ufw allow 80
ufw allow 443

# Install fail2ban for security
apt install -y fail2ban
systemctl enable fail2ban

# Setup SSL with Certbot
apt install -y certbot python3-certbot-nginx

echo "✅ Server setup complete!"
echo ""
echo "Next steps:"
echo "1. Clone your repository to /var/www/oxidane"
echo "2. Set up Python virtual environment"
echo "3. Configure Django settings"
echo "4. Setup Nginx configuration"
echo "5. Create systemd services for Gunicorn and Celery"
echo "6. Setup SSL certificate"
echo ""
echo "Run the app setup script next!"