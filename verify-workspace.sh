#!/bin/bash

# TorchMail Workspace Verification Script
# Use this script to verify you're working in the correct location

set -e

# Expected configuration
EXPECTED_PATH="/home/j_ishihara1997/.openclaw/shared-workspace/projects/torchmail"
EXPECTED_REMOTE="https://github.com/JerryIshihara/torchmail.git"
EXPECTED_FILES=("README.md" "package.json" "docs/product-management/iteration-workflow.md" "WORKSPACE_CONFIG.md")

echo "🔍 Verifying TorchMail workspace configuration..."
echo "=============================================="

# Check current directory
CURRENT_PATH=$(pwd)
echo "Current directory: $CURRENT_PATH"

if [ "$CURRENT_PATH" != "$EXPECTED_PATH" ]; then
    echo "❌ ERROR: Wrong workspace location!"
    echo "   Expected: $EXPECTED_PATH"
    echo "   Current:  $CURRENT_PATH"
    echo ""
    echo "💡 Solution: Run: cd $EXPECTED_PATH"
    exit 1
else
    echo "✅ Correct workspace location"
fi

# Check git remote (works for both regular repos and submodules)
if [ -f ".git" ] || [ -d ".git" ]; then
    REMOTE_URL=$(git remote get-url origin 2>/dev/null || echo "No git remote")
    echo "Git remote: $REMOTE_URL"
    
    if [ "$REMOTE_URL" != "$EXPECTED_REMOTE" ]; then
        echo "❌ ERROR: Wrong git repository!"
        echo "   Expected: $EXPECTED_REMOTE"
        echo "   Current:  $REMOTE_URL"
        exit 1
    else
        echo "✅ Correct git repository"
    fi
else
    echo "❌ ERROR: Not a git repository!"
    exit 1
fi

# Check required files
echo ""
echo "📁 Checking required files..."
ALL_FILES_EXIST=true
for file in "${EXPECTED_FILES[@]}"; do
    if [ -f "$file" ] || [ -d "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file (missing)"
        ALL_FILES_EXIST=false
    fi
done

if [ "$ALL_FILES_EXIST" = false ]; then
    echo "❌ ERROR: Missing required files!"
    exit 1
else
    echo "✅ All required files present"
fi

# Check git status
echo ""
echo "📊 Git status:"
git status --short

# Check if we're on main branch
CURRENT_BRANCH=$(git branch --show-current)
echo "Current branch: $CURRENT_BRANCH"

if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "⚠️  Warning: Not on main branch. Consider: git checkout main"
fi

echo ""
echo "=============================================="
echo "✅ Workspace verification complete!"
echo ""
echo "Next steps:"
echo "1. Run: npm install  (to install dependencies)"
echo "2. Run: npm run dev   (to start development)"
echo "3. Check WORKSPACE_CONFIG.md for detailed instructions"
echo ""
echo "Happy coding! 🚀"