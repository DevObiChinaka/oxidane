#!/bin/bash
# Script to update Nginx configuration for api.oxiworldforexacademy.com

echo "Updating Nginx configuration for API subdomain..."

# Backup current config
sudo cp /etc/nginx/sites-available/oxidane /etc/nginx/sites-available/oxidane.backup

# Update Nginx config
sudo tee /etc/nginx/sites-available/oxidane > /dev/null <<'EOF'
server {
    listen 80;
    server_name api.oxiworldforexacademy.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.oxiworldforexacademy.com;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/oxiworldforexacademy.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/oxiworldforexacademy.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    client_max_body_size 100M;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # API endpoints
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Django admin
    location /django-admin/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files
    location /static/ {
        alias /var/www/oxidane/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /var/www/oxidane/media/;
        expires 30d;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Root redirect
    location = / {
        return 200 '{"status": "API is running", "docs": "/api/docs/"}';
        add_header Content-Type application/json;
    }
}
EOF

# Test Nginx configuration
echo "Testing Nginx configuration..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "Nginx configuration is valid"
    echo "Reloading Nginx..."
    sudo systemctl reload nginx
    echo "✅ Nginx updated successfully for api.oxiworldforexacademy.com"
else
    echo "❌ Nginx configuration error. Restoring backup..."
    sudo cp /etc/nginx/sites-available/oxidane.backup /etc/nginx/sites-available/oxidane
    exit 1
fi

# Get new SSL certificate for api subdomain
echo ""
echo "Now get SSL certificate for api subdomain:"
echo "sudo certbot --nginx -d api.oxiworldforexacademy.com"
