#!/bin/bash
# Complete Hostinger VPS setup for Django + PostgreSQL + Redis + Celery
# Run as root on Ubuntu 22.04 LTS
# curl -sSL https://raw.githubusercontent.com/DevObiChinaka/oxidane/mySaaS/production_setup.sh | bash

set -e

echo "🚀 Setting up Oxidane on Hostinger VPS..."
echo "OS: $(lsb_release -d | cut -f2)"
echo "Server: $(hostname -I | awk '{print $1}')"

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

# Create log directories
mkdir -p /var/log/celery /var/log/gunicorn
chown oxidane:oxidane /var/log/celery /var/log/gunicorn

echo "✅ Hostinger VPS setup complete!"
echo ""
echo "🎯 HOSTINGER SPECIFIC OPTIMIZATIONS:"
echo "• Configured for Hostinger's network environment"
echo "• Optimized Redis for VPS resources" 
echo "• Security hardening with fail2ban"
echo "• Ready for oxiworldforexacademy.com deployment"
echo ""
echo "📋 NEXT STEPS:"
echo "1. Switch to oxidane user: su - oxidane"
echo "2. Clone repository: cd /var/www/oxidane && git clone https://github.com/DevObiChinaka/oxidane.git ."
echo "3. Copy environment file: cp hostinger_production.env .env"
echo "4. Edit .env with your actual credentials"
echo "5. Run deployment: bash deploy.sh"
echo ""
echo "🌐 Domain: Point DNS A records to $(hostname -I | awk '{print $1}')"
echo "6. Setup SSL certificate"
echo ""
echo "Run the app setup script next!"