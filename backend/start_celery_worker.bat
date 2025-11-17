@echo off
REM Celery Worker Startup Script for Oxidane
REM This script starts the Celery worker for processing async tasks

cd /d "%~dp0"
echo Starting Celery Worker...
celery -A oxidane worker --loglevel=info --pool=solo --logfile=logs\celery_worker.log
