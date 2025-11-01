# Telegram API Test Suite - PowerShell Runner
# This script provides Windows-compatible test execution

param(
    [switch]$Verbose,
    [switch]$Frontend,
    [switch]$API,
    [switch]$Backend,
    [switch]$Browser,
    [switch]$Help
)

# Color definitions for PowerShell
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    
    switch ($Color.ToLower()) {
        "red" { Write-Host $Message -ForegroundColor Red }
        "green" { Write-Host $Message -ForegroundColor Green }
        "yellow" { Write-Host $Message -ForegroundColor Yellow }
        "blue" { Write-Host $Message -ForegroundColor Blue }
        "magenta" { Write-Host $Message -ForegroundColor Magenta }
        "cyan" { Write-Host $Message -ForegroundColor Cyan }
        default { Write-Host $Message -ForegroundColor White }
    }
}

function Write-Section {
    param([string]$Title)
    
    Write-Host ""
    Write-Host ("=" * 60) -ForegroundColor Cyan
    Write-Host $Title -ForegroundColor Cyan -NoNewline
    Write-Host ""
    Write-Host ("=" * 60) -ForegroundColor Cyan
    Write-Host ""
}

# Help function
function Show-Help {
    Write-Host @"

Telegram API Test Suite - PowerShell Edition

Usage: .\run-tests.ps1 [options]

Options:
  -Help              Show this help message
  -Verbose           Show verbose output
  -Frontend          Run only frontend tests
  -API               Run only API tests  
  -Backend           Run only backend tests
  -Browser           Run only browser tests

Examples:
  .\run-tests.ps1                          # Run all tests
  .\run-tests.ps1 -Verbose                 # Run all tests with verbose output
  .\run-tests.ps1 -Frontend -API           # Run only frontend and API tests
  .\run-tests.ps1 -Backend -Verbose        # Run only backend tests with verbose output

"@ -ForegroundColor White
    
    Write-ColorOutput "Note: If no specific test suite is specified, all tests will be run." "Yellow"
}

# Check if help was requested
if ($Help) {
    Show-Help
    exit 0
}

# Initialize results tracking
$Results = @{
    Frontend = @{ Status = "Pending"; Duration = 0; Details = $null }
    API = @{ Status = "Pending"; Duration = 0; Details = $null }
    Backend = @{ Status = "Pending"; Duration = 0; Details = $null }
    Browser = @{ Status = "Pending"; Duration = 0; Details = $null }
}

$StartTime = Get-Date

# Determine which tests to run
$RunAll = -not ($Frontend -or $API -or $Backend -or $Browser)

Write-ColorOutput "Telegram API Test Suite - PowerShell Edition" "Magenta"

# Check prerequisites
Write-Section "Checking Prerequisites"

$Prerequisites = @(
    @{ Name = "Node.js"; Command = "node"; Args = @("--version") },
    @{ Name = "NPM"; Command = "npm"; Args = @("--version") },
    @{ Name = "Python"; Command = "python"; Args = @("--version") }
)

foreach ($prereq in $Prerequisites) {
    try {
        $result = & $prereq.Command $prereq.Args 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✓ $($prereq.Name): Available" "Green"
            if ($Verbose -and $result) {
                Write-ColorOutput "  Version: $result" "Blue"
            }
        } else {
            throw "Command failed"
        }
    } catch {
        Write-ColorOutput "✗ $($prereq.Name): Not available" "Red"
        if ($Verbose) {
            Write-ColorOutput "  Error: $($_.Exception.Message)" "Red"
        }
    }
}

# Check required test files
Write-ColorOutput "`nChecking test files:" "Yellow"
$RequiredFiles = @(
    "test-telegram-api.js",
    "telegram-api-tests.js",
    "test_telegram_backend.py"
)

foreach ($file in $RequiredFiles) {
    if (Test-Path $file) {
        Write-ColorOutput "✓ $file: Found" "Green"
    } else {
        Write-ColorOutput "✗ $file: Missing" "Red"
    }
}

# Function to run a test suite
function Invoke-TestSuite {
    param(
        [string]$Name,
        [string]$Command,
        [string[]]$Arguments = @(),
        [string]$WorkingDirectory = $null
    )
    
    $testStartTime = Get-Date
    
    try {
        if ($Verbose) {
            Write-ColorOutput "Running: $Command $($Arguments -join ' ')" "Blue"
        }
        
        $processArgs = @{
            FilePath = $Command
            ArgumentList = $Arguments
            Wait = $true
            NoNewWindow = $true
            PassThru = $true
        }
        
        if ($WorkingDirectory) {
            $processArgs.WorkingDirectory = $WorkingDirectory
        }
        
        if (-not $Verbose) {
            $processArgs.RedirectStandardOutput = $true
            $processArgs.RedirectStandardError = $true
        }
        
        $process = Start-Process @processArgs
        
        $duration = (Get-Date) - $testStartTime
        
        if ($process.ExitCode -eq 0) {
            $Results[$Name].Status = "Passed"
            $Results[$Name].Duration = [int]$duration.TotalMilliseconds
            Write-ColorOutput "✓ $Name tests passed" "Green"
        } else {
            $Results[$Name].Status = "Failed"  
            $Results[$Name].Duration = [int]$duration.TotalMilliseconds
            Write-ColorOutput "✗ $Name tests failed" "Red"
        }
        
    } catch {
        $duration = (Get-Date) - $testStartTime
        $Results[$Name].Status = "Failed"
        $Results[$Name].Duration = [int]$duration.TotalMilliseconds
        $Results[$Name].Details = $_.Exception.Message
        
        Write-ColorOutput "✗ $Name tests failed" "Red"
        if ($Verbose) {
            Write-ColorOutput "  Error: $($_.Exception.Message)" "Red"
        }
    }
}

# Run Frontend Tests
if ($RunAll -or $Frontend) {
    Write-Section "Running Frontend Tests"
    
    $frontendDir = if (Test-Path ".\src") { "." } else { ".\frontend" }
    
    if (Test-Path (Join-Path $frontendDir "package.json")) {
        # Install dependencies if needed
        if (-not (Test-Path (Join-Path $frontendDir "node_modules"))) {
            Write-ColorOutput "Installing frontend dependencies..." "Yellow"
            Invoke-TestSuite "Frontend-Install" "npm" @("install") $frontendDir
        }
        
        # Run tests
        Invoke-TestSuite "Frontend" "npm" @("test", "--", "--watchAll=false") $frontendDir
    } else {
        Write-ColorOutput "✗ Frontend package.json not found" "Red"
        $Results.Frontend.Status = "Failed"
        $Results.Frontend.Details = "package.json not found"
    }
}

# Run API Tests
if ($RunAll -or $API) {
    Write-Section "Running API Tests"
    Invoke-TestSuite "API" "node" @("test-telegram-api.js")
}

# Run Backend Tests  
if ($RunAll -or $Backend) {
    Write-Section "Running Backend Tests"
    Invoke-TestSuite "Backend" "python" @("test_telegram_backend.py")
}

# Run Browser Tests
if ($RunAll -or $Browser) {
    Write-Section "Running Browser Tests"
    Invoke-TestSuite "Browser" "node" @("telegram-api-tests.js")
}

# Generate final report
Write-Section "Test Results Summary"

$totalDuration = (Get-Date) - $StartTime
$total = 0
$passed = 0
$failed = 0

foreach ($result in $Results.Values) {
    if ($result.Status -ne "Pending") {
        $total++
        if ($result.Status -eq "Passed") { $passed++ }
        if ($result.Status -eq "Failed") { $failed++ }
    }
}

Write-Host "Test Suite Results:" -ForegroundColor White
Write-Host "Total Duration: $([math]::Round($totalDuration.TotalSeconds))s`n"

foreach ($suite in $Results.Keys) {
    $result = $Results[$suite]
    if ($result.Status -eq "Pending") { continue }
    
    $status = if ($result.Status -eq "Passed") {
        Write-Host "✓ PASSED" -ForegroundColor Green -NoNewline
    } else {
        Write-Host "✗ FAILED" -ForegroundColor Red -NoNewline
    }
    
    $duration = "$([math]::Round($result.Duration / 1000))s"
    
    Write-Host "$($suite.ToUpper().PadRight(12)) " -NoNewline
    $status
    Write-Host " ($duration)"
    
    if ($Verbose -and $result.Details) {
        Write-ColorOutput "Details:" "Blue"
        $result.Details -split "`n" | ForEach-Object { Write-Host "  $_" }
        Write-Host ""
    }
}

Write-Host "`nSummary:" -ForegroundColor White
Write-ColorOutput "Passed: $passed" "Green"
Write-ColorOutput "Failed: $failed" "Red"
Write-Host "Total: $total"

if ($passed -eq $total -and $total -gt 0) {
    Write-ColorOutput "`n🎉 All tests passed!" "Green"
    exit 0
} elseif ($failed -gt 0) {
    Write-ColorOutput "`n❌ Some tests failed" "Red"
    exit 1
} else {
    Write-ColorOutput "`n⚠️  No tests were run" "Yellow"
    exit 1
}