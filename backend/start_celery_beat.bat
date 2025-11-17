@echo off
REM Celery Beat Startup Script for Oxidane
REM This script starts the Celery beat scheduler for periodic tasks

cd /d "%~dp0"
echo Starting Celery Beat...
celery -A oxidane beat --loglevel=info --logfile=logs\celery_beat.log
