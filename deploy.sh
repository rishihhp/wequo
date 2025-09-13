#!/bin/bash
# WeQuo Deployment Script for Render

echo "🚀 WeQuo Deployment Script"
echo "=========================="

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found. Please run this script from the wequo directory."
    exit 1
fi

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📦 Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit for WeQuo deployment"
fi

# Check if render.yaml exists
if [ ! -f "render.yaml" ]; then
    echo "❌ Error: render.yaml not found. Please ensure deployment files are present."
    exit 1
fi

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: requirements.txt not found."
    exit 1
fi

echo "✅ All deployment files found"

# Display next steps
echo ""
echo "📋 Next Steps:"
echo "1. Push your code to GitHub:"
echo "   git add ."
echo "   git commit -m 'Prepare for Render deployment'"
echo "   git push origin main"
echo ""
echo "2. Deploy to Render:"
echo "   - Go to https://render.com"
echo "   - Click 'New +' → 'Web Service'"
echo "   - Connect your GitHub repository"
echo "   - Use these settings:"
echo "     * Build Command: pip install --upgrade pip && pip install -r requirements.txt && python scripts/init_data.py"
echo "     * Start Command: python app.py"
echo "     * Environment: Python 3"
echo ""
echo "3. Add Environment Variables in Render:"
echo "   - FRED_API_KEY (required)"
echo "   - SECRET_KEY (let Render generate this)"
echo "   - Other API keys as needed (see DEPLOYMENT.md)"
echo ""
echo "4. Deploy and access your app at: https://your-app-name.onrender.com"
echo ""
echo "📚 For detailed instructions, see docs/DEPLOYMENT.md"
echo ""
echo "🎉 Ready to deploy!"
