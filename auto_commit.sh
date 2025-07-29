#!/bin/bash

echo "🔄 Auto-commit: Checking for changes..."

# Check if there are any changes
if git diff --quiet && git diff --cached --quiet && [ -z "$(git ls-files --others --exclude-standard)" ]; then
    echo "✅ No changes to commit"
    exit 0
fi

# Files to exclude (containing sensitive information)
EXCLUDED_FILES=(
    "DATA_MIGRATION_GUIDE.md"
    "EMAIL_SETUP_GUIDE.md"
    "GOOGLE_OAUTH_SETUP_GUIDE.md"
    "GOOGLE_OAUTH_SETUP.md"
    "SECRET_KEY_SETUP_GUIDE.md"
    "SECURITY_SETUP.md"
    "STRIPE_INTEGRATION.md"
    "CRYPTOCURRENCY_PAYMENT_GUIDE.md"
    "vps_emergency_install.md"
    "vps_quick_fix.md"
    "**/config.py"
    "**/.env*"
    "**/secrets*"
)

# Create exclude pattern for git add
EXCLUDE_PATTERN=""
for file in "${EXCLUDED_FILES[@]}"; do
    EXCLUDE_PATTERN="$EXCLUDE_PATTERN ':(exclude)$file'"
done

echo "📦 Staging changes (excluding sensitive files)..."

# Add all files except excluded ones
eval "git add . $EXCLUDE_PATTERN"

# Check if anything was staged
if git diff --cached --quiet; then
    echo "⚠️  No non-sensitive files to commit"
    exit 0
fi

# Generate commit message based on changed files
CHANGED_FILES=$(git diff --cached --name-only)
echo "📝 Changed files:"
echo "$CHANGED_FILES" | sed 's/^/  - /'

# Generate automatic commit message
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
COMMIT_MSG="Auto-commit: Updates on $TIMESTAMP

Modified files:
$(echo "$CHANGED_FILES" | sed 's/^/- /')"

echo "💾 Committing changes..."
git commit -m "$COMMIT_MSG"

if [ $? -eq 0 ]; then
    echo "✅ Committed successfully"
    
    echo "🚀 Pushing to GitHub..."
    git push origin main
    
    if [ $? -eq 0 ]; then
        echo "✅ Pushed to GitHub successfully"
    else
        echo "❌ Failed to push to GitHub"
        exit 1
    fi
else
    echo "❌ Commit failed"
    exit 1
fi

echo "🎉 Auto-commit complete!" 