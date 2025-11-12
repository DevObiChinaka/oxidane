# Start Celery Services Script
# =============================
# This script helps you start all required services for production-mode Celery testing

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  CELERY PRODUCTION MODE SETUP" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Redis is needed
Write-Host "Step 1: Start Redis" -ForegroundColor Yellow
Write-Host "----------------------------------------"
Write-Host ""
Write-Host "Choose your Redis setup:" -ForegroundColor White
Write-Host "  1. WSL Redis (Recommended)" -ForegroundColor Green
Write-Host "  2. Docker Redis" -ForegroundColor Green
Write-Host "  3. Windows Redis" -ForegroundColor Green
Write-Host "  4. Skip (Redis already running)" -ForegroundColor Gray
Write-Host ""

$redisChoice = Read-Host "Enter choice (1-4)"

switch ($redisChoice) {
    "1" {
        Write-Host "Starting Redis in WSL..." -ForegroundColor Green
        wsl sudo service redis-server start
        Write-Host "✓ Redis started in WSL" -ForegroundColor Green
    }
    "2" {
        Write-Host "Starting Redis in Docker..." -ForegroundColor Green
        docker run -d -p 6379:6379 --name oxidane-redis redis:alpine
        Write-Host "✓ Redis container started" -ForegroundColor Green
    }
    "3" {
        Write-Host "Please start redis-server.exe manually in another window" -ForegroundColor Yellow
        pause
    }
    "4" {
        Write-Host "Skipping Redis startup..." -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "Testing Redis connection..." -ForegroundColor Yellow

# Test Redis
$redisTest = python -c "import redis; r = redis.Redis(host='localhost', port=6379); print('OK' if r.ping() else 'FAIL')" 2>$null

if ($redisTest -eq "OK") {
    Write-Host "✓ Redis is running!" -ForegroundColor Green
} else {
    Write-Host "✗ Cannot connect to Redis" -ForegroundColor Red
    Write-Host "  Make sure Redis is running on localhost:6379" -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host ""
Write-Host "Step 2: Configure Environment" -ForegroundColor Yellow
Write-Host "----------------------------------------"
Write-Host ""

# Check .env file
$envPath = "C:\Users\user\OneDrive\Desktop\Oxidane\backend\.env"

if (Test-Path $envPath) {
    $envContent = Get-Content $envPath -Raw
    
    if ($envContent -match "USE_CELERY_EAGER\s*=\s*True") {
        Write-Host "⚠️  Found USE_CELERY_EAGER=True in .env" -ForegroundColor Yellow
        Write-Host ""
        $disable = Read-Host "Disable eager mode for production testing? (Y/n)"
        
        if ($disable -ne "n") {
            # Comment out the line
            $newContent = $envContent -replace "USE_CELERY_EAGER\s*=\s*True", "# USE_CELERY_EAGER=True"
            Set-Content -Path $envPath -Value $newContent
            Write-Host "✓ Disabled eager mode in .env" -ForegroundColor Green
        }
    } else {
        Write-Host "✓ Eager mode is disabled" -ForegroundColor Green
    }
} else {
    Write-Host "⚠️  .env file not found" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Step 3: Starting Services" -ForegroundColor Yellow
Write-Host "----------------------------------------"
Write-Host ""
Write-Host "Opening terminals for:" -ForegroundColor White
Write-Host "  - Django development server" -ForegroundColor Cyan
Write-Host "  - Celery worker" -ForegroundColor Cyan
Write-Host "  - Celery beat (scheduler)" -ForegroundColor Cyan
Write-Host ""

# Start Django server in new terminal
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'C:\Users\user\OneDrive\Desktop\Oxidane\backend'; Write-Host 'DJANGO DEVELOPMENT SERVER' -ForegroundColor Green; python manage.py runserver"

Start-Sleep -Seconds 2

# Start Celery worker in new terminal
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'C:\Users\user\OneDrive\Desktop\Oxidane\backend'; Write-Host 'CELERY WORKER' -ForegroundColor Yellow; celery -A oxidane worker --pool=solo -l info"

Start-Sleep -Seconds 2

# Start Celery beat in new terminal
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'C:\Users\user\OneDrive\Desktop\Oxidane\backend'; Write-Host 'CELERY BEAT (Scheduler)' -ForegroundColor Magenta; celery -A oxidane beat -l info"

Write-Host "✓ Services started in new terminals" -ForegroundColor Green
Write-Host ""

Write-Host "Step 4: Optional - Flower Monitoring" -ForegroundColor Yellow
Write-Host "----------------------------------------"
Write-Host ""
Write-Host "Flower provides a web UI to monitor Celery tasks" -ForegroundColor White
$installFlower = Read-Host "Install and start Flower? (Y/n)"

if ($installFlower -ne "n") {
    Write-Host "Installing Flower..." -ForegroundColor Green
    pip install flower
    
    Start-Sleep -Seconds 2
    
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'C:\Users\user\OneDrive\Desktop\Oxidane\backend'; Write-Host 'FLOWER - Celery Monitoring' -ForegroundColor Cyan; celery -A oxidane flower --port=5555; Write-Host 'Visit: http://localhost:5555' -ForegroundColor Green"
    
    Write-Host "✓ Flower started at http://localhost:5555" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SETUP COMPLETE!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Services running:" -ForegroundColor White
Write-Host "  ✓ Redis - localhost:6379" -ForegroundColor Green
Write-Host "  ✓ Django - http://localhost:8000" -ForegroundColor Green
Write-Host "  ✓ Celery Worker - Processing tasks" -ForegroundColor Green
Write-Host "  ✓ Celery Beat - Scheduled tasks" -ForegroundColor Green

if ($installFlower -ne "n") {
    Write-Host "  ✓ Flower - http://localhost:5555" -ForegroundColor Green
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Run test script: python test_celery_production_mode.py" -ForegroundColor White
Write-Host "  2. Make a payment through your app" -ForegroundColor White
Write-Host "  3. Watch the Celery Worker terminal for task execution" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to run the test script now..." -ForegroundColor Cyan
pause

# Run test script
cd C:\Users\user\OneDrive\Desktop\Oxidane\backend
python test_celery_production_mode.py
