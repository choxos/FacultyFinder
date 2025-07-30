# VPS PubMed Entrez Integration Guide

## 🚀 Complete Setup for Faculty Publications Database

This guide shows you how to deploy and run PubMed Entrez searches on your VPS server to automatically populate your faculty publications database.

## 📋 Prerequisites Checklist

### 1. VPS Requirements
- ✅ **Python 3.8+** installed
- ✅ **PostgreSQL** running (your current setup)
- ✅ **Internet access** for API calls
- ✅ **Sufficient storage** (~500MB for dependencies)

### 2. NCBI Requirements  
- ✅ **Valid email address** (required by NCBI)
- 🔄 **NCBI API Key** (optional but recommended for higher limits)

## 🔧 Step-by-Step VPS Deployment

### Step 1: Install Dependencies

```bash
# Connect to your VPS
ssh user@your-vps-ip

# Navigate to your FacultyFinder directory
cd /var/www/ff

# Install Python dependencies for PubMed integration
pip install biopython requests schedule pandas lxml beautifulsoup4

# Or use the requirements file (if not already installed)
pip install -r requirements_publications.txt
```

### Step 2: Set Up Environment Variables

```bash
# Edit your .env file to add PubMed configuration
nano .env

# Add these lines to your .env file:
NCBI_EMAIL=your.email@domain.com           # ⚠️ REQUIRED: Your real email
NCBI_API_KEY=your_api_key_here             # Optional: Get from NCBI
PUBMED_MAX_RESULTS=100                     # Default: 100 per search
PUBMED_RATE_LIMIT=3                        # Requests per second (max 10 with API key)
```

### Step 3: Get NCBI API Key (Recommended)

```bash
# Visit: https://ncbiinsights.ncbi.nlm.nih.gov/2017/11/02/new-api-keys-for-the-e-utilities/
# 1. Create NCBI account if you don't have one
# 2. Log in to your NCBI account
# 3. Go to Settings > API Key Management
# 4. Generate new API key
# 5. Add it to your .env file as NCBI_API_KEY
```

### Step 4: Update Database Schema (PostgreSQL)

```bash
# Update your PostgreSQL database to ensure all tables exist
cd /var/www/ff

# Run schema updates
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -d $DB_NAME -U $DB_USER -f database/schema.sql
```

### Step 5: Test PubMed Integration

```bash
# Create a test script to verify everything works
cat > test_pubmed.py << 'EOF'
#!/usr/bin/env python3
import sys
import os
sys.path.append('/var/www/ff/webapp')

from pubmed_integration import PubMedSearcher

# Test with your actual environment
searcher = PubMedSearcher()

# Test search for a known McMaster professor
print("Testing PubMed search...")
results = searcher.search_author_publications("Gordon Guyatt", max_results=5)

print(f"Found {len(results)} publications")
for pub in results[:3]:
    print(f"- {pub.get('title', 'No title')}")
    print(f"  PMID: {pub.get('pmid', 'N/A')}")
    print(f"  Year: {pub.get('year', 'N/A')}")
    print()

print("✅ PubMed integration test successful!")
EOF

# Run the test
python3 test_pubmed.py
```

## 🔄 Population Strategies

### Strategy 1: Bulk Population (Recommended for Initial Setup)

```bash
# Create bulk population script
cat > populate_publications.py << 'EOF'
#!/usr/bin/env python3
import sys
import time
import os
sys.path.append('/var/www/ff/webapp')

from pubmed_integration import PubMedSearcher
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        port=os.getenv('DB_PORT')
    )

def get_all_faculty():
    """Get all faculty from database"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT id, name, university_code, department, research_interests 
        FROM professors 
        WHERE name IS NOT NULL AND name != ''
        ORDER BY id
    """)
    
    faculty = cur.fetchall()
    cur.close()
    conn.close()
    return faculty

def populate_faculty_publications():
    searcher = PubMedSearcher()
    faculty = get_all_faculty()
    
    print(f"🔍 Starting publication search for {len(faculty)} faculty members...")
    
    for i, (prof_id, name, uni_code, dept, research) in enumerate(faculty):
        try:
            print(f"\n[{i+1}/{len(faculty)}] Searching for: {name}")
            
            # Search for publications
            publications = searcher.search_author_publications(name, max_results=50)
            
            if publications:
                # Store in database
                stored = searcher.store_publications(prof_id, publications)
                print(f"  ✅ Found {len(publications)} publications, stored {stored}")
            else:
                print(f"  ⚪ No publications found")
            
            # Rate limiting - be nice to NCBI
            time.sleep(1)
            
        except Exception as e:
            print(f"  ❌ Error for {name}: {str(e)}")
            continue
    
    print("\n🎉 Publication population complete!")

if __name__ == "__main__":
    populate_faculty_publications()
EOF

# Run bulk population (this will take time!)
python3 populate_publications.py
```

### Strategy 2: Incremental Updates (Daily/Weekly)

```bash
# Create incremental update script
cat > update_publications.py << 'EOF'
#!/usr/bin/env python3
import sys
import os
from datetime import datetime, timedelta
sys.path.append('/var/www/ff/webapp')

from pubmed_integration import PubMedSearcher
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def update_recent_publications():
    """Update publications for faculty with recent activity"""
    searcher = PubMedSearcher()
    
    # Get faculty who need updates (no publications in last 30 days)
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        port=os.getenv('DB_PORT')
    )
    
    cur = conn.cursor()
    cur.execute("""
        SELECT p.id, p.name 
        FROM professors p
        LEFT JOIN author_publications ap ON p.id = ap.professor_id
        LEFT JOIN publications pub ON ap.publication_id = pub.id
        WHERE pub.created_at IS NULL 
           OR pub.created_at < NOW() - INTERVAL '30 days'
        GROUP BY p.id, p.name
        LIMIT 20
    """)
    
    faculty = cur.fetchall()
    cur.close()
    conn.close()
    
    print(f"🔄 Updating publications for {len(faculty)} faculty members...")
    
    for prof_id, name in faculty:
        try:
            print(f"Updating: {name}")
            publications = searcher.search_author_publications(name, max_results=20)
            
            if publications:
                stored = searcher.store_publications(prof_id, publications)
                print(f"  ✅ Stored {stored} new publications")
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")

if __name__ == "__main__":
    update_recent_publications()
EOF
```

### Strategy 3: Targeted Search by Research Area

```bash
# Create research-area focused search
cat > search_by_research.py << 'EOF'
#!/usr/bin/env python3
import sys
import os
sys.path.append('/var/www/ff/webapp')

from pubmed_integration import PubMedSearcher

def search_by_research_area(research_area, affiliation="McMaster University"):
    """Search for publications by research area and affiliation"""
    searcher = PubMedSearcher()
    
    # Create more specific search query
    search_query = f"({research_area}[Title/Abstract]) AND {affiliation}[Affiliation]"
    
    print(f"🔍 Searching for: {search_query}")
    
    # This would require extending the PubMedSearcher class
    # For now, search by common research areas in your database
    
    common_areas = [
        "epidemiology", "cardiology", "clinical trials", 
        "evidence-based medicine", "systematic review",
        "meta-analysis", "public health"
    ]
    
    for area in common_areas:
        print(f"\nSearching for research area: {area}")
        # You could implement specific search logic here

if __name__ == "__main__":
    search_by_research_area("epidemiology")
EOF
```

## 🔄 Automation Setup

### Option 1: Cron Job (Simple)

```bash
# Add to crontab for automatic updates
crontab -e

# Add these lines:
# Daily incremental update at 2 AM
0 2 * * * cd /var/www/ff && /usr/bin/python3 update_publications.py >> /var/log/pubmed_updates.log 2>&1

# Weekly full update on Sundays at 3 AM  
0 3 * * 0 cd /var/www/ff && /usr/bin/python3 populate_publications.py >> /var/log/pubmed_full.log 2>&1
```

### Option 2: Systemd Service (Advanced)

```bash
# Create systemd service for publication updates
sudo tee /etc/systemd/system/pubmed-updater.service << 'EOF'
[Unit]
Description=FacultyFinder PubMed Publication Updater
After=network.target postgresql.service

[Service]
Type=oneshot
User=www-data
WorkingDirectory=/var/www/ff
Environment=PATH=/var/www/ff/venv/bin
ExecStart=/var/www/ff/venv/bin/python3 update_publications.py
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Create timer for regular updates
sudo tee /etc/systemd/system/pubmed-updater.timer << 'EOF'
[Unit]
Description=Run PubMed updater daily
Requires=pubmed-updater.service

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
EOF

# Enable and start the timer
sudo systemctl daemon-reload
sudo systemctl enable pubmed-updater.timer
sudo systemctl start pubmed-updater.timer
```

## 📊 Monitoring & Optimization

### 1. Check Publication Count

```bash
# Quick check of publication data
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -d $DB_NAME -U $DB_USER -c "
SELECT 
    COUNT(*) as total_publications,
    COUNT(DISTINCT pmid) as unique_pmids,
    MIN(publication_year) as earliest_year,
    MAX(publication_year) as latest_year
FROM publications;
"
```

### 2. Faculty with Publications

```bash
# Check which faculty have publications
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -d $DB_NAME -U $DB_USER -c "
SELECT 
    p.name,
    COUNT(ap.publication_id) as pub_count
FROM professors p
LEFT JOIN author_publications ap ON p.id = ap.professor_id
GROUP BY p.id, p.name
HAVING COUNT(ap.publication_id) > 0
ORDER BY pub_count DESC
LIMIT 10;
"
```

### 3. Monitor API Usage

```bash
# Create monitoring script
cat > monitor_pubmed.py << 'EOF'
#!/usr/bin/env python3
import os
import psycopg2
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

def publication_stats():
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        port=os.getenv('DB_PORT')
    )
    
    cur = conn.cursor()
    
    # Total publications
    cur.execute("SELECT COUNT(*) FROM publications")
    total = cur.fetchone()[0]
    
    # Publications added today
    cur.execute("SELECT COUNT(*) FROM publications WHERE created_at >= CURRENT_DATE")
    today = cur.fetchone()[0]
    
    # Faculty with publications
    cur.execute("""
        SELECT COUNT(DISTINCT professor_id) 
        FROM author_publications
    """)
    faculty_with_pubs = cur.fetchone()[0]
    
    print(f"📊 Publication Statistics")
    print(f"   Total Publications: {total}")
    print(f"   Added Today: {today}")  
    print(f"   Faculty with Publications: {faculty_with_pubs}")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    publication_stats()
EOF

# Run monitoring
python3 monitor_pubmed.py
```

## 🚨 Troubleshooting

### Common Issues & Solutions

#### 1. Rate Limiting Errors
```bash
# If you get rate limiting errors:
# Solution: Get NCBI API key and increase delays
echo "NCBI_RATE_LIMIT=1" >> .env  # Slow down to 1 request/second
```

#### 2. Database Connection Errors
```bash
# Check PostgreSQL connection
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -d $DB_NAME -U $DB_USER -c "SELECT version();"
```

#### 3. Missing Dependencies
```bash
# Install missing packages
pip install --upgrade biopython requests psycopg2-binary
```

#### 4. Memory Issues on VPS
```bash
# Monitor memory usage during large operations
htop

# If needed, process in smaller batches
# Edit populate_publications.py and add LIMIT to queries
```

## 🎯 Best Practices

### 1. **Start Small**: Test with 5-10 faculty first
### 2. **Rate Limiting**: Respect NCBI limits (3-10 requests/second)  
### 3. **Error Handling**: Log failures and retry later
### 4. **Deduplication**: Check for existing PMIDs before storing
### 5. **Backup**: Regular database backups before bulk operations

## 📈 Expected Results

After successful deployment:
- **Initial Population**: 50-200 publications per faculty (depending on research activity)
- **Daily Updates**: 1-10 new publications across all faculty
- **API Usage**: ~100-500 requests per day (well within limits)
- **Database Growth**: ~1-5MB per week

## 🎉 Verification

```bash
# Final verification script
cat > verify_setup.py << 'EOF'
#!/usr/bin/env python3
import sys
sys.path.append('/var/www/ff/webapp')

print("🧪 Verifying PubMed Integration Setup...")

try:
    from pubmed_integration import PubMedSearcher
    print("✅ PubMed module imported successfully")
    
    searcher = PubMedSearcher()
    print("✅ PubMed searcher initialized")
    
    # Test search
    results = searcher.search_author_publications("test", max_results=1)
    print("✅ PubMed API connection working")
    
    print("\n🎉 All checks passed! Ready for publication population.")
    
except Exception as e:
    print(f"❌ Setup error: {str(e)}")
    print("\n🔧 Please check your configuration and try again.")
EOF

python3 verify_setup.py
```

## 📞 Support

If you encounter issues:
1. Check the logs: `/var/log/pubmed_*.log`
2. Verify your NCBI email is valid
3. Ensure all dependencies are installed
4. Test with a small batch first

Your PubMed integration is now ready for production use! 🚀 