# NCBI Blocking Solution Guide

## 🚨 **Problem Identified**

Your VPS is being **blocked by NCBI** with the error:
```
NCBI - WWW Error Blocked Diagnostic
```

This is a common issue with **VPS/cloud server IPs** being flagged as suspicious traffic by NCBI's security system.

## 🔍 **Root Cause Analysis**

NCBI blocks requests when they detect:
- ✅ **Cloud/VPS IP addresses** (AWS, Google Cloud, DigitalOcean, etc.)
- ✅ **Automated scripts** without proper headers
- ✅ **High request rates** from unknown sources
- ✅ **Suspicious user-agent strings**

Your VPS IP is likely **flagged in NCBI's security database**.

## 🚀 **Complete Solution Workflow**

I've created a **3-step solution** to bypass this blocking:

### **Step 1: Diagnose the Issue** 
```bash
# Run on your VPS
python3 fix_ncbi_blocking.py
```

**What it does:**
- ✅ Tests different connection methods
- ✅ Checks IP reputation
- ✅ Tries improved headers and timing
- ✅ Provides alternative suggestions

### **Step 2: Export Data Locally**
```bash
# Run on your LOCAL machine (not VPS)
python3 local_pubmed_export.py
```

**What it does:**
- ✅ Bypasses VPS IP blocking completely
- ✅ Searches PubMed from your local IP
- ✅ Exports data as JSON and CSV files
- ✅ Processes multiple faculty members
- ✅ Creates ready-to-import files

### **Step 3: Import to VPS Database**
```bash
# Transfer files to VPS
scp -r pubmed_exports/ user@your-vps:/var/www/ff/

# Import on VPS
python3 import_pubmed_data.py pubmed_exports/
```

**What it does:**
- ✅ Imports all exported publication data
- ✅ Creates professor records if needed
- ✅ Links publications to faculty
- ✅ Updates PostgreSQL database
- ✅ Provides import statistics

## 📋 **Detailed Instructions**

### **Option A: Local Export + VPS Import (Recommended)**

#### **1. Set Up Local Environment**
```bash
# On your local machine
git clone your-repo
cd FacultyFinder
pip install biopython requests python-dotenv

# Create .env with your real email
echo "NCBI_EMAIL=your.real.email@domain.com" > .env
echo "NCBI_API_KEY=your_api_key" >> .env  # Optional but recommended
```

#### **2. Export PubMed Data Locally**
```bash
# Run the export (takes 10-30 minutes for sample faculty)
python3 local_pubmed_export.py
```

**Expected Output:**
```
🏠 Local PubMed Export Tool
========================================
✅ Using API key for your.email@domain.com
🔍 Searching for Gordon Guyatt...
   Found 89 publications
📄 Testing publication details...
✅ Exported 89 publications to pubmed_exports/Gordon_Guyatt_publications.json

🎉 Export Complete!
   📊 Summary: 8/8 faculty with publications
   📚 Total publications: 456
   📁 Files saved to: pubmed_exports/
```

#### **3. Transfer to VPS**
```bash
# Copy exported data to VPS
scp -r pubmed_exports/ user@your-vps:/var/www/ff/
```

#### **4. Import on VPS**
```bash
# On your VPS
cd /var/www/ff
python3 import_pubmed_data.py pubmed_exports/
```

**Expected Output:**
```
📥 PubMed Data Importer for VPS
========================================
✅ Connected to PostgreSQL database
👨‍🔬 Processing Gordon Guyatt (89 publications)
   Found existing professor: Gordon Guyatt (ID: 123)
      Imported publication 12345678
      Linked to professor

🎉 Total imported from directory: 456 publications
📊 Database Statistics:
   Total Publications: 456
   Faculty with Publications: 8
```

### **Option B: Try VPS Fixes First**

#### **1. Diagnostic and Fix Attempts**
```bash
# Try to fix VPS blocking
python3 fix_ncbi_blocking.py
```

#### **2. Retry with Delays**
```bash
# If diagnostic suggests retry
python3 retry_ncbi_access.py
```

#### **3. Manual Configuration**
```bash
# Update PubMed integration with better settings
./fix_pubmed_config.sh
```

## 🔧 **Alternative Data Sources**

If NCBI continues to block your VPS:

### **Europe PMC API**
```python
# Alternative to PubMed
import requests

def search_europe_pmc(author_name):
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    params = {
        'query': f'AUTH:"{author_name}"',
        'format': 'json',
        'resultType': 'core'
    }
    response = requests.get(url, params=params)
    return response.json()
```

### **CrossRef API**
```python
# For DOI-based searches
import requests

def search_crossref(author_name):
    url = "https://api.crossref.org/works"
    params = {
        'query.author': author_name,
        'rows': 100
    }
    response = requests.get(url, params=params)
    return response.json()
```

## 📊 **Expected Results**

After successful implementation:

### **Local Export Results**
- ✅ **8 sample faculty** → ~456 publications
- ✅ **Export time**: 10-30 minutes
- ✅ **File formats**: JSON + CSV
- ✅ **Data quality**: Complete metadata

### **VPS Import Results**
- ✅ **Database populated** with publications
- ✅ **Faculty-publication links** created
- ✅ **Homepage displays** publication counts
- ✅ **Professor profiles** show research data
- ✅ **Search includes** publication data

## 🎯 **Production Deployment**

### **Scale to All Faculty**
```python
# In local_pubmed_export.py, expand faculty list:
faculty_list = [
    # All 281 McMaster faculty
    "Gordon Guyatt", "Salim Yusuf", "Hertzel Gerstein",
    # ... add all your faculty names
]
```

### **Automation**
```bash
# Set up weekly local exports
# Cron job on local machine:
0 2 * * 0 cd /path/to/FacultyFinder && python3 local_pubmed_export.py
```

### **Monitoring**
```bash
# Check import status
python3 -c "
import psycopg2
conn = psycopg2.connect(host='$DB_HOST', database='$DB_NAME', user='$DB_USER', password='$DB_PASSWORD')
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM publications')
print(f'Total publications: {cur.fetchone()[0]}')
"
```

## 🚨 **Troubleshooting**

### **Common Issues**

#### **1. Local Export Fails**
```bash
# Check email configuration
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
print(f'NCBI_EMAIL: {os.getenv(\"NCBI_EMAIL\")}')
"
```

#### **2. VPS Import Fails**
```bash
# Check database connection
python3 -c "
import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()
conn = psycopg2.connect(host=os.getenv('DB_HOST'), database=os.getenv('DB_NAME'), user=os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD'))
print('✅ Database connection OK')
"
```

#### **3. Missing Publications**
```bash
# Check author name variations
python3 -c "
# Try different name formats:
# 'Gordon Guyatt'
# 'Guyatt G'
# 'Guyatt GH'
"
```

## 📞 **Support Options**

### **1. Contact NCBI**
- **Email**: info@ncbi.nlm.nih.gov
- **Subject**: "Academic Research IP Whitelist Request"
- **Include**: VPS IP, institution, research purpose

### **2. VPS Provider**
- Request **different IP range**
- Use **dedicated IP** if available
- Consider **different provider**

### **3. Network Solutions**
- **VPN service** for VPS
- **Proxy service** for API calls
- **Local development** → VPS deployment

## 🎉 **Success Metrics**

Your solution is working when:
- ✅ **Local export completes** without errors
- ✅ **VPS import succeeds** with all publications
- ✅ **Homepage shows** publication metrics
- ✅ **Faculty profiles** display research data
- ✅ **Search includes** publication information

## 🚀 **Next Steps**

1. **Run local export** for sample faculty
2. **Test VPS import** with small dataset
3. **Verify database** integration works
4. **Scale to full faculty** list (281 members)
5. **Set up automation** for regular updates

**Your FacultyFinder will now have comprehensive publication data despite the NCBI blocking!** 🎓📚 