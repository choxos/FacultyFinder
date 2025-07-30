#!/bin/bash

echo "🔧 Fixing PubMed Configuration"
echo "============================"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Creating .env file..."
    touch .env
fi

# Check current NCBI_EMAIL setting
CURRENT_EMAIL=$(grep "NCBI_EMAIL" .env | cut -d'=' -f2 | tr -d '"' || echo "")

if [ -z "$CURRENT_EMAIL" ] || [[ "$CURRENT_EMAIL" == *"example.com"* ]]; then
    echo "❌ Invalid or missing NCBI_EMAIL found: $CURRENT_EMAIL"
    echo ""
    echo "NCBI requires a REAL email address for API access."
    echo "Please enter your real email address:"
    read -p "Email: " USER_EMAIL
    
    if [[ "$USER_EMAIL" == *"@"* ]] && [[ "$USER_EMAIL" != *"example.com"* ]]; then
        # Remove existing NCBI_EMAIL line if it exists
        grep -v "NCBI_EMAIL" .env > .env.tmp && mv .env.tmp .env
        
        # Add new NCBI_EMAIL
        echo "NCBI_EMAIL=$USER_EMAIL" >> .env
        echo "✅ Updated NCBI_EMAIL to: $USER_EMAIL"
    else
        echo "❌ Invalid email format. Please provide a real email address."
        exit 1
    fi
else
    echo "✅ Valid NCBI_EMAIL found: $CURRENT_EMAIL"
fi

# Check for API key
API_KEY=$(grep "NCBI_API_KEY" .env | cut -d'=' -f2 | tr -d '"' || echo "")

if [ -z "$API_KEY" ]; then
    echo ""
    echo "🔑 NCBI API Key (Optional but Recommended)"
    echo "   • Increases rate limits from 3 to 10 requests/second"
    echo "   • Get one free at: https://ncbiinsights.ncbi.nlm.nih.gov/2017/11/02/new-api-keys-for-the-e-utilities/"
    echo ""
    read -p "Do you have an NCBI API key? (y/n): " HAS_KEY
    
    if [ "$HAS_KEY" = "y" ] || [ "$HAS_KEY" = "Y" ]; then
        read -p "Enter your NCBI API key: " USER_API_KEY
        if [ ! -z "$USER_API_KEY" ]; then
            echo "NCBI_API_KEY=$USER_API_KEY" >> .env
            echo "✅ Added NCBI API key"
        fi
    else
        echo "⚠️  No API key added - using default rate limits (3 requests/second)"
    fi
else
    echo "✅ NCBI API key found"
fi

# Set other PubMed settings
echo ""
echo "📝 Setting PubMed configuration..."

# Remove existing PubMed settings
grep -v "PUBMED_MAX_RESULTS\|PUBMED_RATE_LIMIT" .env > .env.tmp && mv .env.tmp .env

# Add PubMed settings
echo "PUBMED_MAX_RESULTS=100" >> .env
echo "PUBMED_RATE_LIMIT=3" >> .env

echo "✅ Added PubMed configuration"

echo ""
echo "🧪 Testing PubMed connection..."

# Install required packages if needed
if ! python3 -c "import Bio" 2>/dev/null; then
    echo "📦 Installing biopython..."
    pip install biopython
fi

if ! python3 -c "import requests" 2>/dev/null; then
    echo "📦 Installing requests..."
    pip install requests
fi

# Run the debug script
if [ -f "debug_pubmed_api.py" ]; then
    echo "🔍 Running PubMed API test..."
    python3 debug_pubmed_api.py
else
    echo "⚠️  debug_pubmed_api.py not found, skipping test"
fi

echo ""
echo "🎉 PubMed Configuration Complete!"
echo "================================"

echo "✅ Your .env file now contains:"
echo "   • Valid NCBI_EMAIL address"
if [ ! -z "$USER_API_KEY" ]; then
    echo "   • NCBI API key for higher rate limits"
fi
echo "   • PubMed configuration settings"

echo ""
echo "🚀 Next steps:"
echo "   1. Test: python3 debug_pubmed_api.py"
echo "   2. Use: python3 populate_publications.py"
echo "   3. Deploy: Run the VPS PubMed deployment guide" 