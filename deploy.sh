#!/bin/bash
# Deploy to GitHub and Render

echo "🚀 ICEGODS Platform Deployment"

# Check files exist
for file in main.py requirements.txt Procfile; do
    if [ ! -f "$file" ]; then
        echo "❌ Missing: $file"
        exit 1
    fi
done

echo "✅ All files present"

# Git operations
if [ ! -d ".git" ]; then
    git init
    echo "✅ Git initialized"
fi

git add .
git commit -m "Deploy: ICEGODS SaaS Platform v1.0 - Working"

# Check remote
if ! git remote | grep -q "origin"; then
    git remote add origin https://github.com/IceReign-MEXT/MEX-WarSystem.git
    echo "✅ Remote added"
fi

echo ""
echo "📤 Pushing to GitHub..."
git push origin main --force

echo ""
echo "✅ PUSHED TO GITHUB!"
echo ""
echo "NEXT STEPS:"
echo "1. Go to https://dashboard.render.com"
echo "2. New Web Service → Connect GitHub repo"
echo "3. Settings:"
echo "   - Name: mex-warsystem-saas"
echo "   - Runtime: Python 3"
echo "   - Build Command: pip install -r requirements.txt"
echo "   - Start Command: python main.py"
echo "4. Add Environment Variables (copy from .env)"
echo "5. Deploy!"
echo ""
echo "Your bot will be LIVE at:"
echo "https://mex-warsystem-xxx.onrender.com"
echo ""

