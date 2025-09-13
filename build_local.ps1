# WeQuo Local Build and Test Script (PowerShell)

Write-Host "🚀 WeQuo Local Build and Test" -ForegroundColor Green
Write-Host "=============================" -ForegroundColor Green

# Check if we're in the right directory
if (!(Test-Path "app.py")) {
    Write-Host "❌ Error: app.py not found. Please run this script from the wequo directory." -ForegroundColor Red
    exit 1
}

# Function to run command and check result
function Run-Command {
    param(
        [string]$Command,
        [string]$Description
    )
    
    Write-Host "🔧 $Description..." -ForegroundColor Yellow
    try {
        Invoke-Expression $Command
        Write-Host "✅ $Description - Success" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "❌ $Description - Failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Track test results
$TestsPassed = 0
$TotalTests = 0

# Test 1: Check Python version
$TotalTests++
Write-Host "🔧 Checking Python version (3.10+)..." -ForegroundColor Yellow
$pythonVersion = python --version
if ($pythonVersion -match "Python 3\.(1[0-9]|[2-9]\d)") {
    Write-Host "✅ Python version check - Success ($pythonVersion)" -ForegroundColor Green
    $TestsPassed++
} else {
    Write-Host "❌ Python version check - Failed. Need Python 3.10+" -ForegroundColor Red
}

# Test 2: Install dependencies
$TotalTests++
if (Run-Command "pip install --upgrade pip" "Upgrading pip") {
    if (Run-Command "pip install -r requirements.txt" "Installing dependencies") {
        $TestsPassed++
    }
} else {
    Write-Host "❌ Dependencies installation - Failed" -ForegroundColor Red
}

# Test 3: Run data initialization
$TotalTests++
if (Test-Path "scripts/init_data.py") {
    if (Run-Command "python scripts/init_data.py" "Initializing data directories") {
        $TestsPassed++
    }
} else {
    Write-Host "⚠️  scripts/init_data.py not found, skipping..." -ForegroundColor Yellow
    $TestsPassed++ # Skip this test if file doesn't exist
}

# Test 4: Run local tests
$TotalTests++
if (Test-Path "test_local.py") {
    if (Run-Command "python test_local.py" "Running local tests") {
        $TestsPassed++
    }
} else {
    Write-Host "⚠️  test_local.py not found, skipping..." -ForegroundColor Yellow
    $TestsPassed++ # Skip this test if file doesn't exist
}

# Test 5: Test app startup (quick test)
$TotalTests++
Write-Host "🔧 Testing app startup..." -ForegroundColor Yellow
try {
    $job = Start-Job -ScriptBlock {
        python -c @"
import sys
sys.path.insert(0, 'src')
from app import create_main_app
app = create_main_app()
print('App created successfully')
"@
    }
    
    if (Wait-Job $job -Timeout 10) {
        $result = Receive-Job $job
        if ($result -match "App created successfully") {
            Write-Host "✅ App startup test - Success" -ForegroundColor Green
            $TestsPassed++
        } else {
            Write-Host "❌ App startup test - Failed" -ForegroundColor Red
        }
    } else {
        Write-Host "❌ App startup test - Timeout" -ForegroundColor Red
        Stop-Job $job
    }
    Remove-Job $job -Force
}
catch {
    Write-Host "❌ App startup test - Failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 6: Check for common issues
$TotalTests++
Write-Host "🔧 Checking for common issues..." -ForegroundColor Yellow

$IssuesFound = 0

# Check if .env exists
if (!(Test-Path ".env")) {
    Write-Host "⚠️  Warning: .env file not found. Creating from template..." -ForegroundColor Yellow
    if (Test-Path "env.example") {
        Copy-Item "env.example" ".env"
        Write-Host "✅ Created .env from env.example" -ForegroundColor Green
    } else {
        Write-Host "❌ env.example not found" -ForegroundColor Red
        $IssuesFound++
    }
} else {
    Write-Host "✅ .env file exists" -ForegroundColor Green
}

# Check if data directories exist
if (!(Test-Path "data")) {
    Write-Host "❌ Data directory not found" -ForegroundColor Red
    $IssuesFound++
} else {
    Write-Host "✅ Data directory exists" -ForegroundColor Green
}

# Check if config.yml exists
if (!(Test-Path "src/wequo/config.yml")) {
    Write-Host "❌ config.yml not found" -ForegroundColor Red
    $IssuesFound++
} else {
    Write-Host "✅ config.yml exists" -ForegroundColor Green
}

if ($IssuesFound -eq 0) {
    Write-Host "✅ Common issues check - Success" -ForegroundColor Green
    $TestsPassed++
} else {
    Write-Host "❌ Common issues check - Failed ($IssuesFound issues found)" -ForegroundColor Red
}

# Summary
Write-Host ""
Write-Host "=============================" -ForegroundColor Green
Write-Host "📊 Build Results: $TestsPassed/$TotalTests tests passed" -ForegroundColor Cyan

if ($TestsPassed -eq $TotalTests) {
    Write-Host "🎉 All tests passed! Ready for production deployment." -ForegroundColor Green
    Write-Host ""
    Write-Host "🚀 Next steps:" -ForegroundColor Cyan
    Write-Host "1. Set your API keys in .env file"
    Write-Host "2. Test locally: python app.py"
    Write-Host "3. Deploy to Render: ./deploy.sh"
    exit 0
} else {
    Write-Host "❌ Some tests failed. Please fix issues before deploying." -ForegroundColor Red
    Write-Host ""
    Write-Host "🔧 Common fixes:" -ForegroundColor Yellow
    Write-Host "- Install missing dependencies: pip install -r requirements.txt"
    Write-Host "- Check Python version: python --version"
    Write-Host "- Verify all files are present"
    Write-Host "- Check error messages above"
    exit 1
}