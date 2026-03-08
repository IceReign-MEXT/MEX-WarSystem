#!/bin/bash
# Deployment script for ICEGODS Platform

echo "🚀 Starting deployment..."

# Check files exist
if [ ! -f "main.py" ]; then
    echo "❌ main.py not found"
    exit 1
fi

if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found"
    exit 1
fi

if [ ! -f "Procfile" ]; then
    echo "❌ Procfile not found"
    exit 1
fi

# Git setup
if [ ! -d ".git" ]; then
    git init
    git add .
    git commit -m "Initial SaaS platform deployment"
    echo "✅ Git initialized"
else
    git add .
    git commit -m "Update: $(date)"
    echo "✅ Git updated"
fi

echo ""
echo "📋 DEPLOYMENT CHECKLIST:"
echo "1. Push to GitHub: git push origin main"
echo "2. Connect Render.com to your repo"
echo "3. Set environment variables in Render dashboard"
echo "4. Deploy!"
echo ""
echo "🔧 Required Environment Variables:"
echo "- BOT_TOKEN"
echo "- ADMIN_ID"
echo "- DATABASE_URL"
echo "- MASTER_WALLET"
echo "- HELIUS_API_KEY"
echo "- WEBHOOK_URL"
echo ""

