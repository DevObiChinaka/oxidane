# VPS Backend Status Check Script
# Checks if backend is running and accessible

$VPS_IP = "169.255.57.172"

Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "VPS BACKEND STATUS CHECK" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan

# Test HTTP connection to VPS (assuming Nginx is proxy)
Write-Host "`n[1] Testing HTTP connection to VPS..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://${VPS_IP}/" -Method GET -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✅ VPS is reachable via HTTP (Status: $($response.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "❌ Cannot reach VPS via HTTP" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test API health endpoint
Write-Host "`n[2] Testing API health endpoint..." -ForegroundColor Yellow
try {
    $healthResponse = Invoke-RestMethod -Uri "http://${VPS_IP}/api/health/" -Method GET -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✅ API Health Check Successful!" -ForegroundColor Green
    $healthResponse | ConvertTo-Json | Write-Host -ForegroundColor Gray
} catch {
    Write-Host "❌ API Health Check Failed" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test admin auth endpoint
Write-Host "`n[3] Testing admin auth endpoint availability..." -ForegroundColor Yellow
try {
    $authTest = Invoke-WebRequest -Uri "http://${VPS_IP}/api/admin-auth/login/" `
        -Method POST `
        -Body '{}' `
        -ContentType "application/json" `
        -TimeoutSec 5 `
        -ErrorAction Stop
    
    Write-Host "✅ Admin auth endpoint is accessible (Status: $($authTest.StatusCode))" -ForegroundColor Green
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    if ($statusCode -eq 400) {
        Write-Host "✅ Admin auth endpoint is accessible (400 is expected for empty body)" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Admin auth endpoint returned: $statusCode" -ForegroundColor Yellow
    }
}

# Test setup status endpoint (should fail with 401 without auth)
Write-Host "`n[4] Testing setup status endpoint (should return 401)..." -ForegroundColor Yellow
try {
    $setupTest = Invoke-WebRequest -Uri "http://${VPS_IP}/api/admin/setup/status/" `
        -Method GET `
        -TimeoutSec 5 `
        -ErrorAction Stop
    
    Write-Host "⚠️  Setup endpoint returned $($setupTest.StatusCode) (expected 401)" -ForegroundColor Yellow
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    if ($statusCode -eq 401) {
        Write-Host "✅ Setup endpoint correctly returns 401 Unauthorized" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Setup endpoint returned: $statusCode" -ForegroundColor Yellow
    }
}

Write-Host "`n" + ("=" * 70) -ForegroundColor Cyan
Write-Host "STATUS CHECK COMPLETE" -ForegroundColor Cyan  
Write-Host "=" * 70 -ForegroundColor Cyan

Write-Host "`nNext Step: If all checks passed, run test_production_admin_login.ps1" -ForegroundColor Cyan
