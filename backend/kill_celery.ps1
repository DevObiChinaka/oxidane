# Kill all Celery processes to free Redis connections
Write-Host "Killing all Celery workers..." -ForegroundColor Yellow

$celeryProcesses = Get-Process | Where-Object {$_.ProcessName -like "*celery*"}

if ($celeryProcesses) {
    $celeryProcesses | ForEach-Object {
        Write-Host "  Killing Celery process $($_.Id)..." -ForegroundColor Cyan
        Stop-Process -Id $_.Id -Force
    }
    Write-Host "Done - All Celery processes killed" -ForegroundColor Green
} else {
    Write-Host "No Celery processes found" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Remaining Python processes:" -ForegroundColor Yellow
Get-Process | Where-Object {$_.ProcessName -like "*python*"} | Select-Object ProcessName, Id | Format-Table
