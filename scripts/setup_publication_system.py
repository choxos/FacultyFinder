#!/usr/bin/env python3
"""
Setup script for FacultyFinder Automated Publication System
Run this to initialize the enhanced database schema and check requirements
"""

import os
import sys
import sqlite3
import subprocess
from pathlib import Path

def check_requirements():
    """Check if required packages are installed"""
    required_packages = [
        'biopython',
        'pandas', 
        'requests',
        'schedule'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} is missing")
    
    if missing_packages:
        print(f"\nTo install missing packages, run:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def setup_database(db_path):
    """Setup database with new schema"""
    try:
        # Check if database exists
        if not os.path.exists(db_path):
            print(f"❌ Database not found: {db_path}")
            print("Please ensure the main database exists first")
            return False
        
        # Apply schema updates
        schema_file = "database/journal_metrics_schema.sql"
        
        if not os.path.exists(schema_file):
            print(f"❌ Schema file not found: {schema_file}")
            return False
        
        print(f"📊 Applying database schema updates...")
        
        conn = sqlite3.connect(db_path)
        
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
        
        # Execute schema updates
        conn.executescript(schema_sql)
        conn.commit()
        conn.close()
        
        print("✅ Database schema updated successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        return False

def check_data_files():
    """Check if required data files exist"""
    required_files = [
        "data/mcmaster_hei_faculty.csv",
        "data/scimago_journals_comprehensive.csv"
    ]
    
    all_exist = True
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} not found")
            all_exist = False
    
    return all_exist

def create_config_template():
    """Create configuration template"""
    config_content = """# FacultyFinder Publication Update Configuration
# Copy this to config.py and update with your values

# PubMed API Configuration
PUBMED_EMAIL = "your-email@domain.com"  # Required for Entrez API
PUBMED_API_KEY = None  # Optional but recommended - get from NCBI

# Database Configuration
DATABASE_PATH = "database/facultyfinder_dev.db"

# Data File Paths
FACULTY_CSV_PATH = "data/mcmaster_hei_faculty.csv"
SCIMAGO_CSV_PATH = "data/scimago_journals_comprehensive.csv"

# Update Schedule Configuration
ENABLE_SCHEDULER = True
FULL_UPDATE_SCHEDULE = "sunday.at('02:00')"  # Weekly full update
CITATION_UPDATE_SCHEDULE = "day.at('03:00')"  # Daily citation updates
INCREMENTAL_UPDATE_HOURS = 6  # Hours between incremental updates

# Email Notification Configuration (Optional)
EMAIL_NOTIFICATIONS = {
    'enabled': False,
    'smtp_server': 'smtp.gmail.com',
    'port': 587,
    'username': 'your-email@gmail.com',
    'password': 'your-app-password',  # Use app password for Gmail
    'from': 'your-email@gmail.com',
    'to': 'admin@facultyfinder.io'
}

# Rate Limiting
PUBMED_RATE_LIMIT = 0.34  # Seconds between requests (3/sec)
OPENCITATIONS_RATE_LIMIT = 1.0  # Seconds between requests

# Batch Sizes
PUBMED_BATCH_SIZE = 200  # Publications per batch
CITATION_UPDATE_BATCH_SIZE = 50  # Publications to update citations for

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FILE = "publication_updates.log"
"""
    
    config_file = "scripts/config_template.py"
    
    with open(config_file, 'w') as f:
        f.write(config_content)
    
    print(f"✅ Created configuration template: {config_file}")
    print("   Please copy to config.py and update with your settings")

def run_test_search():
    """Run a test PubMed search to verify API access"""
    try:
        from Bio import Entrez
        
        # Use a placeholder email for testing
        Entrez.email = "test@example.com"
        
        print("🔬 Testing PubMed API access...")
        
        # Simple test search
        search_handle = Entrez.esearch(
            db="pubmed",
            term="McMaster University[Affiliation]",
            retmax=5
        )
        
        search_results = Entrez.read(search_handle)
        search_handle.close()
        
        pmids = search_results["IdList"]
        
        if pmids:
            print(f"✅ PubMed API test successful - found {len(pmids)} results")
            return True
        else:
            print("⚠️  PubMed API accessible but no results found")
            return True
            
    except Exception as e:
        print(f"❌ PubMed API test failed: {e}")
        print("   Please check your internet connection and Biopython installation")
        return False

def main():
    """Main setup function"""
    print("🚀 FacultyFinder Publication System Setup")
    print("=" * 50)
    
    # Check current directory
    if not os.path.exists("webapp/app.py"):
        print("❌ Please run this script from the FacultyFinder root directory")
        sys.exit(1)
    
    success = True
    
    # 1. Check requirements
    print("\n1. Checking Python package requirements...")
    if not check_requirements():
        success = False
    
    # 2. Check data files
    print("\n2. Checking required data files...")
    if not check_data_files():
        print("   Some data files are missing. The system will still work")
        print("   but you'll need these files for full functionality")
    
    # 3. Setup database
    print("\n3. Setting up database schema...")
    db_path = "database/facultyfinder_dev.db"
    if not setup_database(db_path):
        success = False
    
    # 4. Create configuration template
    print("\n4. Creating configuration template...")
    create_config_template()
    
    # 5. Test PubMed API
    print("\n5. Testing PubMed API access...")
    if not run_test_search():
        print("   API test failed but setup can continue")
    
    # Summary
    print("\n" + "=" * 50)
    if success:
        print("✅ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Copy scripts/config_template.py to scripts/config.py")
        print("2. Update config.py with your email and API key")
        print("3. Run: python scripts/publication_update_system.py")
        print("4. For automated updates: python scripts/update_scheduler.py")
    else:
        print("❌ Setup completed with errors")
        print("Please resolve the issues above before proceeding")
    
    print("\n📚 Documentation:")
    print("- Full guide: AUTOMATED_PUBLICATION_UPDATE_GUIDE.md")
    print("- Database schema: database/journal_metrics_schema.sql")

if __name__ == "__main__":
    main() 