#!/bin/bash
# Script to update Django settings for API subdomain

echo "Updating Django settings for api.oxiworldforexacademy.com..."

# Backup current .env
cp /var/www/oxidane/.env /var/www/oxidane/.env.backup

# Update ALLOWED_HOSTS and CORS_ALLOWED_ORIGINS
cat > /tmp/django_update.py << 'PYTHON_SCRIPT'
import os
from pathlib import Path

env_file = Path("/var/www/oxidane/.env")
content = env_file.read_text()

# Update ALLOWED_HOSTS
if "ALLOWED_HOSTS=" in content:
    # Replace existing ALLOWED_HOSTS
    lines = content.split('\n')
    new_lines = []
    for line in lines:
        if line.startswith("ALLOWED_HOSTS="):
            new_lines.append('ALLOWED_HOSTS=api.oxiworldforexacademy.com,oxiworldforexacademy.com,169.255.57.172,localhost,127.0.0.1')
        else:
            new_lines.append(line)
    content = '\n'.join(new_lines)
else:
    # Add ALLOWED_HOSTS
    content += '\nALLOWED_HOSTS=api.oxiworldforexacademy.com,oxiworldforexacademy.com,169.255.57.172,localhost,127.0.0.1\n'

# Update CORS_ALLOWED_ORIGINS
if "CORS_ALLOWED_ORIGINS=" in content:
    lines = content.split('\n')
    new_lines = []
    for line in lines:
        if line.startswith("CORS_ALLOWED_ORIGINS="):
            new_lines.append('CORS_ALLOWED_ORIGINS=https://oxiworldforexacademy.com,https://api.oxiworldforexacademy.com,http://localhost:3000')
        else:
            new_lines.append(line)
    content = '\n'.join(new_lines)
else:
    content += '\nCORS_ALLOWED_ORIGINS=https://oxiworldforexacademy.com,https://api.oxiworldforexacademy.com,http://localhost:3000\n'

# Update CSRF_TRUSTED_ORIGINS
if "CSRF_TRUSTED_ORIGINS=" in content:
    lines = content.split('\n')
    new_lines = []
    for line in lines:
        if line.startswith("CSRF_TRUSTED_ORIGINS="):
            new_lines.append('CSRF_TRUSTED_ORIGINS=https://oxiworldforexacademy.com,https://api.oxiworldforexacademy.com')
        else:
            new_lines.append(line)
    content = '\n'.join(new_lines)
else:
    content += '\nCSRF_TRUSTED_ORIGINS=https://oxiworldforexacademy.com,https://api.oxiworldforexacademy.com\n'

env_file.write_text(content)
print("✅ Updated .env file successfully")
PYTHON_SCRIPT

# Run the Python update script
python3 /tmp/django_update.py

# Restart Gunicorn to apply changes
echo "Restarting Gunicorn..."
sudo systemctl restart oxidane-gunicorn

echo ""
echo "✅ Django settings updated for API subdomain"
echo "Backend will now accept requests from:"
echo "  - https://oxiworldforexacademy.com (frontend)"
echo "  - https://api.oxiworldforexacademy.com (API)"
