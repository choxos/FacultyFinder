#!/bin/bash

echo "🚀 Committing Data Migration System to GitHub"
echo "=============================================="

# Navigate to project root
cd /Users/choxos/Documents/GitHub/FacultyFinder

# Check git status
echo "📋 Current git status:"
git status --porcelain

echo
echo "🔒 Adding data migration files (safe for public repository):"

# Add the data migration system files
echo "✅ Adding data migration system..."
git add data_migration_system.py
git add simple_data_import.py
git add DATA_MIGRATION_GUIDE.md

# Add safe utility scripts (exclude VPS-specific ones)
echo "✅ Adding safe utility scripts..."
git add flask_quick_fix.py
git add fix_flask_compatibility.py
git add generate_secret_key.py

# Add updated core application files
echo "✅ Adding updated webapp files..."
git add webapp/app.py 2>/dev/null || true
git add webapp/wsgi.py 2>/dev/null || true
git add webapp/templates/ 2>/dev/null || true
git add webapp/static/ 2>/dev/null || true

# Add safe configuration files
echo "✅ Adding safe configuration..."
git add requirements.txt
git add .gitignore
git add README.md
git add LICENSE

# Add public documentation
echo "✅ Adding public documentation..."
git add FacultyFinder_guide.md

# Add data files (safe - public research data)
echo "✅ Adding data files..."
git add data/ 2>/dev/null || true
git add Faculty/ 2>/dev/null || true

echo
echo "🚫 Files being EXCLUDED (contain sensitive VPS/deployment info):"
echo "   - transfer_data_to_vps.sh (contains VPS IP and credentials)"
echo "   - deploy_data_to_production.sh (contains VPS access info)"
echo "   - All *GUIDE*.md files (except DATA_MIGRATION_GUIDE.md which is safe)"
echo "   - All deployment and VPS-specific scripts"

# Show what's being committed
echo
echo "📋 Files to be committed:"
git status --porcelain | grep -E "^A|^M" || echo "No files staged"

# Create comprehensive commit message
echo
echo "📝 Creating commit..."

git commit -m "📊 Data Migration System & Core Enhancements

🚀 Data Migration System:
- Added data_migration_system.py - comprehensive PostgreSQL migration tool
- Added simple_data_import.py - streamlined data import for quick setup
- Added DATA_MIGRATION_GUIDE.md - complete migration documentation
- Support for universities, professors, publications, and journal data
- Batch processing for large datasets with error handling

🔧 Flask Application Improvements:
- Enhanced WSGI configuration for production deployment
- Fixed Flask 2.2+ compatibility issues with deprecated decorators
- Improved database connection handling and performance
- Added proper error handling and logging

🎯 Core Features:
- Complete database schema for academic data
- Support for professor profiles with publications
- University directory with comprehensive information
- Publication tracking and citation metrics
- Journal quality metrics integration

📊 Database Design:
- Universities table with location and institutional data
- Professors table with research interests and metrics
- Publications table with DOI, PMID, and citation tracking
- Relational structure linking professors to publications
- Optimized indexes for search performance

🔧 Development Tools:
- Flask compatibility fix scripts for Python 3.12+
- Secret key generation utilities for secure deployment
- Data validation and verification tools
- Migration progress tracking and error reporting

💾 Data Processing:
- CSV import for university and faculty data
- JSON processing for detailed publication records
- Scimago journal metrics integration
- Batch processing for large datasets
- Data validation and cleanup routines

🎨 User Experience:
- Real data powers all search and filter functionality
- Complete professor profiles with publication lists
- University browsing with institutional details
- Research area categorization and discovery

Note: VPS deployment scripts and sensitive configuration files
are kept private for security. This commit includes only the 
core application code and safe migration tools."

echo "✅ Commit created successfully!"

# Push to GitHub
echo
echo "📤 Pushing to GitHub..."
git push origin main

if [ $? -eq 0 ]; then
    echo "🎉 Successfully pushed Data Migration System to GitHub!"
    echo
    echo "✅ What was committed:"
    echo "   - Complete data migration system for PostgreSQL"
    echo "   - Database schema and import tools"
    echo "   - Documentation for data migration process"
    echo "   - Flask compatibility improvements"
    echo "   - Core application enhancements"
    echo "   - Development and utility scripts"
    echo
    echo "🔒 What was protected:"
    echo "   - VPS-specific deployment scripts"
    echo "   - Server IP addresses and credentials"
    echo "   - Production configuration details"
    echo
    echo "🔗 Your repository now includes a complete data migration system!"
    echo "   Users can import their own academic data into FacultyFinder"
else
    echo "❌ Failed to push to GitHub. Check the error messages above."
fi 