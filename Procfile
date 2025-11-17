web: cd backend && gunicorn oxidane.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
worker: cd backend && celery -A oxidane worker --loglevel=info --concurrency=2
beat: cd backend && celery -A oxidane beat --loglevel=info
