#!/bin/bash
cd /var/www/oxidane/backend
../venv/bin/celery -A oxidane beat --loglevel=debug
