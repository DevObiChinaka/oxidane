# PowerShell script to install Celery as a Windows Service using NSSM
# NSSM (Non-Sucking Service Manager) is required: https://nssm.cc/download

param(
    [string]$NssmPath = "nssm.exe"
)

Write-Host "=== Oxidane Celery Service Installer ===" -ForegroundColor Cyan

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

# Get current directory
$BackendDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$WorkerBat = Join-Path $BackendDir "start_celery_worker.bat"
$BeatBat = Join-Path $BackendDir "start_celery_beat.bat"
$LogDir = Join-Path $BackendDir "logs"

# Create logs directory if it doesn't exist
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
    Write-Host "✓ Created logs directory: $LogDir" -ForegroundColor Green
}

# Check if NSSM is available
$nssmExists = $null -ne (Get-Command $NssmPath -ErrorAction SilentlyContinue)
if (-not $nssmExists) {
    Write-Host ""
    Write-Host "NSSM not found! Please install NSSM first:" -ForegroundColor Yellow
    Write-Host "1. Download from: https://nssm.cc/download" -ForegroundColor White
    Write-Host "2. Extract nssm.exe to a folder (e.g., C:\nssm)" -ForegroundColor White
    Write-Host "3. Add folder to PATH or specify path with -NssmPath parameter" -ForegroundColor White
    Write-Host ""
    Write-Host "Example: .\install_celery_service.ps1 -NssmPath 'C:\nssm\nssm.exe'" -ForegroundColor Gray
    exit 1
}

Write-Host "✓ NSSM found: $NssmPath" -ForegroundColor Green

# Install Celery Worker Service
Write-Host ""
Write-Host "Installing Celery Worker Service..." -ForegroundColor Cyan
& $NssmPath install OxidaneCeleryWorker "$WorkerBat"
& $NssmPath set OxidaneCeleryWorker AppDirectory "$BackendDir"
& $NssmPath set OxidaneCeleryWorker DisplayName "Oxidane Celery Worker"
& $NssmPath set OxidaneCeleryWorker Description "Processes async tasks for Oxidane platform (Telegram, payments, emails)"
& $NssmPath set OxidaneCeleryWorker Start SERVICE_AUTO_START
& $NssmPath set OxidaneCeleryWorker ObjectName LocalSystem
& $NssmPath set OxidaneCeleryWorker AppStdout "$LogDir\celery_worker_stdout.log"
& $NssmPath set OxidaneCeleryWorker AppStderr "$LogDir\celery_worker_stderr.log"
& $NssmPath set OxidaneCeleryWorker AppRotateFiles 1
& $NssmPath set OxidaneCeleryWorker AppRotateBytes 10485760  # 10MB
Write-Host "✓ Celery Worker service installed" -ForegroundColor Green

# Install Celery Beat Service
Write-Host ""
Write-Host "Installing Celery Beat Service..." -ForegroundColor Cyan
& $NssmPath install OxidaneCeleryBeat "$BeatBat"
& $NssmPath set OxidaneCeleryBeat AppDirectory "$BackendDir"
& $NssmPath set OxidaneCeleryBeat DisplayName "Oxidane Celery Beat"
& $NssmPath set OxidaneCeleryBeat Description "Schedules periodic tasks for Oxidane platform (renewals, reminders, exchange rates)"
& $NssmPath set OxidaneCeleryBeat Start SERVICE_AUTO_START
& $NssmPath set OxidaneCeleryBeat ObjectName LocalSystem
& $NssmPath set OxidaneCeleryBeat AppStdout "$LogDir\celery_beat_stdout.log"
& $NssmPath set OxidaneCeleryBeat AppStderr "$LogDir\celery_beat_stderr.log"
& $NssmPath set OxidaneCeleryBeat AppRotateFiles 1
& $NssmPath set OxidaneCeleryBeat AppRotateBytes 10485760  # 10MB
Write-Host "✓ Celery Beat service installed" -ForegroundColor Green

# Start services
Write-Host ""
Write-Host "Starting services..." -ForegroundColor Cyan
Start-Service OxidaneCeleryWorker
Start-Service OxidaneCeleryBeat
Write-Host "✓ Services started" -ForegroundColor Green

Write-Host ""
Write-Host "=== Installation Complete! ===" -ForegroundColor Green
Write-Host ""
Write-Host "Services installed:" -ForegroundColor White
Write-Host "  - OxidaneCeleryWorker (processes async tasks)" -ForegroundColor Gray
Write-Host "  - OxidaneCeleryBeat (schedules periodic tasks)" -ForegroundColor Gray
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor White
Write-Host "  View status:   Get-Service Oxidane*" -ForegroundColor Gray
Write-Host "  Stop services: Stop-Service Oxidane*" -ForegroundColor Gray
Write-Host "  Start services: Start-Service Oxidane*" -ForegroundColor Gray
Write-Host "  Remove services: nssm remove OxidaneCeleryWorker confirm; nssm remove OxidaneCeleryBeat confirm" -ForegroundColor Gray
Write-Host ""
Write-Host "Logs location: $LogDir" -ForegroundColor Yellow
