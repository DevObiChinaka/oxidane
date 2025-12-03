# Test Admin Login Flow on Production VPS
# This script will test the complete admin OTP login flow

$VPS_IP = "169.255.57.172"
$BASE_URL = "http://${VPS_IP}/api"

Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "TESTING ADMIN LOGIN FLOW ON PRODUCTION VPS" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan

# Step 1: Request Admin OTP
Write-Host "`n[STEP 1] Requesting Admin OTP..." -ForegroundColor Yellow
$loginRequestBody = @{
    username = "admin"
    password = "admin123"
} | ConvertTo-Json

try {
    $otpResponse = Invoke-RestMethod -Uri "$BASE_URL/admin-auth/login/" `
        -Method POST `
        -Body $loginRequestBody `
        -ContentType "application/json; charset=utf-8" `
        -UseBasicParsing `
        -ErrorAction Stop
    
    Write-Host "✅ OTP Request Successful!" -ForegroundColor Green
    Write-Host "Session Token: $($otpResponse.session_token)" -ForegroundColor Gray
    $sessionToken = $otpResponse.session_token
} catch {
    Write-Host "❌ OTP Request Failed!" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails) {
        Write-Host "Details: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
    exit 1
}

# Step 2: Prompt for OTP
Write-Host "`n[STEP 2] Enter the OTP sent to your email:" -ForegroundColor Yellow
$otp = Read-Host "OTP"

# Step 3: Verify OTP and get JWT token
Write-Host "`n[STEP 3] Verifying OTP and getting JWT token..." -ForegroundColor Yellow
$verifyBody = @{
    session_token = $sessionToken
    otp = $otp
} | ConvertTo-Json

try {
    $tokenResponse = Invoke-RestMethod -Uri "$BASE_URL/admin-auth/verify-otp/" `
        -Method POST `
        -Body $verifyBody `
        -ContentType "application/json" `
        -ErrorAction Stop
    
    Write-Host "✅ OTP Verification Successful!" -ForegroundColor Green
    Write-Host "`nUser Data:" -ForegroundColor Cyan
    $tokenResponse.user | ConvertTo-Json | Write-Host -ForegroundColor Gray
    
    $accessToken = $tokenResponse.access
    Write-Host "`nAccess Token (first 80 chars): $($accessToken.Substring(0, 80))..." -ForegroundColor Gray
    
} catch {
    Write-Host "❌ OTP Verification Failed!" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails) {
        Write-Host "Details: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
    exit 1
}

# Step 4: Test authenticated request to setup status
Write-Host "`n[STEP 4] Testing authenticated request to /api/admin/setup/status/..." -ForegroundColor Yellow
try {
    $setupResponse = Invoke-RestMethod -Uri "$BASE_URL/admin/setup/status/" `
        -Method GET `
        -Headers @{
            Authorization = "Bearer $accessToken"
            "Content-Type" = "application/json"
        } `
        -ErrorAction Stop
    
    Write-Host "✅ Setup Status Request Successful!" -ForegroundColor Green
    Write-Host "`nSetup Status:" -ForegroundColor Cyan
    $setupResponse | ConvertTo-Json -Depth 5 | Write-Host -ForegroundColor Gray
    
} catch {
    Write-Host "❌ Setup Status Request Failed!" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Status Code: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
    if ($_.ErrorDetails) {
        Write-Host "Details: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
}

# Step 5: Test dashboard metrics
Write-Host "`n[STEP 5] Testing authenticated request to /api/admin/dashboard/..." -ForegroundColor Yellow
try {
    $dashboardResponse = Invoke-RestMethod -Uri "$BASE_URL/admin/dashboard/" `
        -Method GET `
        -Headers @{
            Authorization = "Bearer $accessToken"
            "Content-Type" = "application/json"
        } `
        -ErrorAction Stop
    
    Write-Host "✅ Dashboard Request Successful!" -ForegroundColor Green
    Write-Host "`nDashboard Data:" -ForegroundColor Cyan
    $dashboardResponse | ConvertTo-Json -Depth 3 | Write-Host -ForegroundColor Gray
    
} catch {
    Write-Host "❌ Dashboard Request Failed!" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Status Code: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
    if ($_.ErrorDetails) {
        Write-Host "Details: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
}

Write-Host "`n" + ("=" * 70) -ForegroundColor Cyan
Write-Host "TEST COMPLETE" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
