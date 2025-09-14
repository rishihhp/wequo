#!/bin/bash
# WeQuo Local Build and Test Script

echo "🚀 WeQuo Local Build and Test"
echo "============================="

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found. Please run this script from the wequo directory."
    exit 1
fi

# Function to run command and check result
run_command() {
    local cmd="$1"
    local description="$2"
    
    echo "🔧 $description..."
    if eval "$cmd"; then
        echo "✅ $description - Success"
        return 0
    else
        echo "❌ $description - Failed"
        return 1
    fi
}

# Track test results
TESTS_PASSED=0
TOTAL_TESTS=0

# Test 1: Check Python version
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if run_command "python --version | grep -E 'Python 3\.(10|11|12)'" "Checking Python version (3.10+)"; then
    TESTS_PASSED=$((TESTS_PASSED + 1))
fi

# Test 2: Install dependencies
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if run_command "pip install --upgrade pip" "Upgrading pip"; then
    if run_command "pip install -r requirements.txt" "Installing dependencies"; then
        TESTS_PASSED=$((TESTS_PASSED + 1))
    fi
fi

# Test 3: Run data initialization
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if run_command "python scripts/init_data.py" "Initializing data directories"; then
    TESTS_PASSED=$((TESTS_PASSED + 1))
fi

# Test 4: Run local tests
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if run_command "python test_local.py" "Running local tests"; then
    TESTS_PASSED=$((TESTS_PASSED + 1))
fi

# Test 5: Test app startup (quick test)
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo "🔧 Testing app startup..."
timeout 10s python -c "
import sys
sys.path.insert(0, 'src')
from app import create_main_app
app = create_main_app()
print('App created successfully')
" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ App startup test - Success"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo "❌ App startup test - Failed"
fi

# Test 6: Check for common issues
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo "🔧 Checking for common issues..."

ISSUES_FOUND=0

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found. Creating from template..."
    if [ -f "env.example" ]; then
        cp env.example .env
        echo "✅ Created .env from env.example"
    else
        echo "❌ env.example not found"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
    fi
fi

# Check if data directories exist
if [ ! -d "data" ]; then
    echo "❌ Data directory not found"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
else
    echo "✅ Data directory exists"
fi

# Check if config.yml exists
if [ ! -f "src/wequo/config.yml" ]; then
    echo "❌ config.yml not found"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
else
    echo "✅ config.yml exists"
fi

if [ $ISSUES_FOUND -eq 0 ]; then
    echo "✅ Common issues check - Success"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo "❌ Common issues check - Failed ($ISSUES_FOUND issues found)"
fi

# Summary
echo ""
echo "============================="
echo "📊 Build Results: $TESTS_PASSED/$TOTAL_TESTS tests passed"

if [ $TESTS_PASSED -eq $TOTAL_TESTS ]; then
    echo "🎉 All tests passed! Ready for production deployment."
    echo ""
    echo "🚀 Next steps:"
    echo "1. Set your API keys in .env file"
    echo "2. Test locally: python app.py"
    echo "3. Deploy to Render: ./deploy.sh"
    exit 0
else
    echo "❌ Some tests failed. Please fix issues before deploying."
    echo ""
    echo "🔧 Common fixes:"
    echo "- Install missing dependencies: pip install -r requirements.txt"
    echo "- Check Python version: python --version"
    echo "- Verify all files are present"
    echo "- Check error messages above"
    exit 1
fi
