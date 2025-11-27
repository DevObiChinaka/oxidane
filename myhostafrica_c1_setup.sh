#!/bin/bash
# MyHostAfrica C1 Plan VPS Setup Script
# Optimized for 1 vCPU, 2GB RAM, 30GB SSD
# Ubuntu 22.04 LTS

set -e
trap 'echo "❌ Setup failed at line $LINENO"' ERR

echo "🚀 Starting MyHostAfrica C1 VPS Setup"
echo "======================================"
echo "📊 System Resources: 1 vCPU, 2GB RAM, 30GB SSD"
echo ""

# Update system
echo "🔄 Updating system packages..."
apt update && apt upgrade -y

# Install essential packages with C1 optimizations
echo "📦 Installing optimized packages for C1..."
apt install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    postgresql-14 \
    redis-server \
    nginx \
    git \
    curl \
    htop \
    ufw \
    fail2ban \
    supervisor

# Optimize PostgreSQL for 2GB RAM
echo "🗄️ Optimizing PostgreSQL for C1 (2GB RAM)..."
cp /etc/postgresql/14/main/postgresql.conf /etc/postgresql/14/main/postgresql.conf.backup

cat >> /etc/postgresql/14/main/postgresql.conf << 'EOF'

# C1 Plan Optimizations (2GB RAM)
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 128MB
checkpoint_completion_target = 0.9
wal_buffers = 8MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 8MB
min_wal_size = 1GB
max_wal_size = 4GB
max_connections = 50
EOF

# Optimize Redis for C1
echo "📝 Optimizing Redis for C1..."
cp /etc/redis/redis.conf /etc/redis/redis.conf.backup

# Set Redis max memory to 256MB (reasonable for 2GB system)
echo "maxmemory 256mb" >> /etc/redis/redis.conf
echo "maxmemory-policy allkeys-lru" >> /etc/redis/redis.conf

# Start services
echo "▶️ Starting optimized services..."
systemctl enable postgresql
systemctl enable redis-server
systemctl enable nginx
systemctl start postgresql
systemctl start redis-server
systemctl start nginx

# Create application user
echo "👤 Creating application user..."
useradd -m -s /bin/bash oxidane
usermod -aG sudo oxidane

# Create application directory
echo "📁 Setting up application directories..."
mkdir -p /var/www/oxidane
mkdir -p /var/log/oxidane
chown -R oxidane:oxidane /var/www/oxidane
chown -R oxidane:oxidane /var/log/oxidane

# Create database and user
echo "🗄️ Setting up database..."
sudo -u postgres psql << 'EOF'
CREATE DATABASE oxidane_prod;
CREATE USER oxidane WITH PASSWORD 'secure_db_password_2024';
ALTER ROLE oxidane SET client_encoding TO 'utf8';
ALTER ROLE oxidane SET default_transaction_isolation TO 'read committed';
ALTER ROLE oxidane SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE oxidane_prod TO oxidane;
\q
EOF

# Configure firewall for C1
echo "🛡️ Configuring firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 'Nginx Full'
ufw --force enable

# Configure fail2ban
echo "🚫 Setting up fail2ban..."
cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log

[nginx-http-auth]
enabled = true
port = http,https
filter = nginx-http-auth
logpath = /var/log/nginx/error.log

[nginx-limit-req]
enabled = true
port = http,https
filter = nginx-limit-req
logpath = /var/log/nginx/error.log
EOF

systemctl enable fail2ban
systemctl start fail2ban

# Configure Nginx with C1 optimizations
echo "⚙️ Configuring Nginx for C1..."
cat > /etc/nginx/nginx.conf << 'EOF'
user www-data;
worker_processes 1;  # Single CPU optimization
pid /run/nginx.pid;

events {
    worker_connections 1024;  # Reduced for C1
    use epoll;
    multi_accept on;
}

http {
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 30;  # Reduced for memory efficiency
    types_hash_max_size 2048;
    client_max_body_size 10M;  # Reasonable limit
    
    # Memory optimization
    client_body_buffer_size 128k;
    client_header_buffer_size 1k;
    large_client_header_buffers 4 4k;
    output_buffers 1 32k;
    postpone_output 1460;

    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml text/javascript;

    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;
}
EOF

# Set up log rotation for space efficiency
echo "📋 Setting up log rotation..."
cat > /etc/logrotate.d/oxidane << 'EOF'
/var/log/oxidane/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    copytruncate
    maxsize 50M
}
EOF

# Create swap file for memory assistance (important for 2GB system)
echo "💾 Creating swap file for C1..."
if [ ! -f /swapfile ]; then
    fallocate -l 1G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    echo 'vm.swappiness=10' >> /etc/sysctl.conf
fi

# Set up system monitoring
echo "📊 Installing monitoring tools..."
apt install -y nload iotop

# Create C1-optimized Python environment
echo "🐍 Setting up Python environment..."
sudo -u oxidane bash << 'EOF'
cd /var/www/oxidane
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip wheel
EOF

# Display system info
echo ""
echo "💽 System Information:"
echo "======================"
free -h
df -h
echo ""

echo "✅ MyHostAfrica C1 VPS Setup Complete!"
echo "======================================="
echo ""
echo "🎯 C1 Optimizations Applied:"
echo "• PostgreSQL configured for 2GB RAM"
echo "• Redis limited to 256MB"
echo "• Nginx optimized for single CPU"
echo "• 1GB swap file created"
echo "• Log rotation configured"
echo "• Firewall and security hardened"
echo ""
echo "📊 Resource Usage Monitoring:"
echo "• htop - system processes"
echo "• nload - network usage"
echo "• iotop - disk I/O"
echo "• free -h - memory usage"
echo "• df -h - disk usage"
echo ""
echo "🔄 Next Steps:"
echo "1. Switch to oxidane user: su - oxidane"
echo "2. Clone repository: git clone https://github.com/DevObiChinaka/oxidane.git ."
echo "3. Run deployment: bash deploy.sh"
echo "4. Configure SSL certificates"
echo ""
echo "⚠️  Memory Management Tips for C1:"
echo "• Monitor memory with 'free -h'"
echo "• Use 'systemctl status' to check service health"
echo "• Consider upgrading if consistently using >80% RAM"