#!/bin/bash
# Django application setup script
# Run as oxidane user: ./app_setup.sh

set -e

echo "🐍 Setting up Django application..."

cd /var/www/oxidane

# Clone repository (you'll need to update this URL)
# git clone https://github.com/DevObiChinaka/oxidane.git .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install --upgrade pip
pip install -r backend/requirements.txt
pip install gunicorn psycopg2-binary

# Create environment file
cat > .env << EOL
DEBUG=False
SECRET_KEY=your_super_secret_key_here_make_it_long_and_random
ALLOWED_HOSTS=oxiworld.app,www.oxiworld.app
DATABASE_URL=postgresql://oxidane:your_secure_password_here@localhost:5432/oxidane_production
REDIS_URL=redis://:your_redis_password_here@localhost:6379/0

# Email settings (update with your SMTP)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
EMAIL_USE_TLS=True

# Paystack settings
PAYSTACK_SECRET_KEY=your_paystack_secret_key
PAYSTACK_PUBLIC_KEY=your_paystack_public_key

# Security
CSRF_TRUSTED_ORIGINS=https://oxiworld.app,https://www.oxiworld.app
CORS_ALLOWED_ORIGINS=https://oxiworld.app,https://www.oxiworld.app

# Celery
CELERY_BROKER_URL=redis://:your_redis_password_here@localhost:6379/0
CELERY_RESULT_BACKEND=redis://:your_redis_password_here@localhost:6379/0
EOL

# Run Django setup
cd backend
python manage.py collectstatic --noinput
python manage.py migrate

echo "✅ Django application setup complete!"
echo "Update the .env file with your actual credentials before starting services!"