# Deploy and run investigation script on VPS

$VPS_IP = "169.255.57.172"
$VPS_USER = "root"
$REMOTE_PATH = "/root/Oxidane/backend"

Write-Host "📤 Uploading investigation script..." -ForegroundColor Cyan
scp investigate_autorenewal.py "${VPS_USER}@${VPS_IP}:${REMOTE_PATH}/"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Upload successful!" -ForegroundColor Green
    Write-Host "`n🔍 Running investigation on server..." -ForegroundColor Cyan
    ssh "${VPS_USER}@${VPS_IP}" "cd ${REMOTE_PATH} && source venv/bin/activate && python investigate_autorenewal.py"
} else {
    Write-Host "❌ Upload failed!" -ForegroundColor Red
}
