# 📊 FacultyFinder Data Migration Guide

**Complete guide to transfer and import your local data to the production FacultyFinder website.**

---

## 🎯 **Overview**

You have valuable data in your local `data/` folder that needs to be:
1. **Transferred** from your local computer to the VPS
2. **Imported** into the PostgreSQL production database
3. **Verified** to ensure everything works correctly

---

## 📋 **Available Data Files**

### **Your Local Data (`/Users/choxos/Documents/GitHub/FacultyFinder/data/`):**

| File | Size | Description |
|------|------|-------------|
| **university_codes.csv** | 15KB | University information (101 universities) |
| **mcmaster_experts_summary.csv** | 357KB | Faculty overview with publication stats (275 faculty) |
| **mcmaster_experts_detailed.json** | 19MB | Complete faculty data with publications |
| **mcmaster_hei_faculty.csv** | 98KB | Additional faculty data |
| **scimago_journals_comprehensive.csv** | 45MB | Journal metrics database |
| **mcmaster_experts_individual_csv/** | Directory | Individual CSV files for each faculty |
| **mcmaster_experts_individual_json/** | Directory | Individual JSON profiles |

---

## ⚡ **Quick Migration (Recommended)**

### **Option 1: Automated Complete Migration**

```bash
# Run the complete deployment script
chmod +x deploy_data_to_production.sh
./deploy_data_to_production.sh
```

This script will:
- ✅ Transfer all data files to VPS
- ✅ Install required Python packages
- ✅ Run database migration
- ✅ Verify import success
- ✅ Test website functionality

---

## 🔧 **Manual Step-by-Step Migration**

### **Step 1: Transfer Data to VPS**

```bash
# Run the transfer script
chmod +x transfer_data_to_vps.sh
./transfer_data_to_vps.sh
```

**What this does:**
- Creates `/var/www/ff/data_import/` directory on VPS
- Transfers all CSV and JSON files
- Transfers migration scripts
- Verifies file transfer

### **Step 2: SSH to VPS and Install Dependencies**

```bash
# SSH to your VPS
ssh xeradb@91.99.161.136

# Navigate to project
cd /var/www/ff
source venv/bin/activate

# Install required packages
pip install pandas psycopg2-binary python-dotenv
```

### **Step 3: Run Database Migration**

**Option A: Full Migration System**
```bash
cd /var/www/ff/data_import
python3 data_migration_system.py --data-dir /var/www/ff/data_import
```

**Option B: Simple Import (Faster)**
```bash
cd /var/www/ff/data_import
python3 simple_data_import.py
```

### **Step 4: Restart Website**

```bash
sudo systemctl restart facultyfinder
sudo systemctl status facultyfinder
```

### **Step 5: Verify Website**

```bash
# Test local connection
curl -I http://127.0.0.1:8008

# Check public website
curl -I https://facultyfinder.io
```

---

## 📊 **What Gets Imported**

### **Universities Table:**
- **101 universities** from `university_codes.csv`
- University codes, names, locations, websites
- Foundation for the university directory

### **Professors Table:**
- **275+ faculty members** from McMaster University
- Names, departments, positions, contact info
- Publication statistics (counts, citations, h-index)
- Research interests and profile URLs

### **Publications Table:**
- **Thousands of publications** from detailed JSON
- Titles, authors, journals, years, DOIs
- Linked to individual professors

### **Optional: Journals Table:**
- **Journal metrics** from Scimago database
- Impact factors, rankings, publisher info
- Enables journal quality analysis

---

## ✅ **Expected Results**

After successful migration, your website will have:

### **🌐 Universities Page:**
- Browse 101 universities worldwide
- Filter by country, type, language
- Real university data with websites

### **👥 Faculty Page:**
- Search 275+ McMaster faculty members
- Filter by department, position, research area
- Real publication counts and statistics

### **📄 Professor Profiles:**
- Detailed faculty information
- Complete publication lists
- Research interests and contact info
- Links to Google Scholar, ORCID profiles

### **🔍 Search Functionality:**
- Search professors by name
- Filter by department or research area
- Real data powers all searches

---

## 🚨 **Troubleshooting**

### **Transfer Issues:**
```bash
# Check SSH connection
ssh xeradb@91.99.161.136 'echo "Connection works"'

# Check disk space on VPS
ssh xeradb@91.99.161.136 'df -h'

# Retry failed transfers manually
rsync -avz --progress /path/to/file xeradb@91.99.161.136:/var/www/ff/data_import/
```

### **Database Issues:**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test database connection
python3 -c "
import psycopg2
from dotenv import load_dotenv
import os
load_dotenv('/var/www/ff/.env')
conn = psycopg2.connect(
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME')
)
print('✅ Database connection works!')
conn.close()
"
```

### **Import Errors:**
```bash
# Check for missing files
ls -la /var/www/ff/data_import/

# Run simple import for essential data only
python3 simple_data_import.py

# Check database tables
psql -h localhost -U ff_user -d ff_production -c "\dt"
```

### **Website Issues:**
```bash
# Restart services
sudo systemctl restart facultyfinder
sudo systemctl restart nginx

# Check logs
sudo journalctl -u facultyfinder -n 20
```

---

## 📈 **Data Statistics**

After import, you should see approximately:

| Table | Expected Count | Source |
|-------|---------------|---------|
| **universities** | 101 | university_codes.csv |
| **professors** | 275+ | mcmaster_experts_summary.csv |
| **publications** | 5,000+ | mcmaster_experts_detailed.json |
| **professor_publications** | 5,000+ | Relationships |
| **journals** | 50,000+ | scimago_journals_comprehensive.csv (optional) |

---

## 🎯 **Next Steps After Migration**

### **1. Test Your Website:**
- Visit https://facultyfinder.io
- Test university browsing
- Search for faculty members
- Check professor profiles

### **2. Add More Data:**
- Add other universities beyond McMaster
- Import additional publication sources
- Update research areas and keywords

### **3. Backup Your Data:**
- Set up automated PostgreSQL backups
- Export data periodically
- Document your data sources

### **4. Monitor Performance:**
- Check website speed with real data
- Monitor database performance
- Optimize queries if needed

---

## 🚀 **Ready to Migrate?**

### **Choose Your Migration Method:**

#### **🏃 Quick & Easy (Recommended):**
```bash
chmod +x deploy_data_to_production.sh
./deploy_data_to_production.sh
```

#### **🔧 Step-by-Step Control:**
1. Run `transfer_data_to_vps.sh`
2. SSH to VPS and install packages
3. Run `simple_data_import.py`
4. Restart services and test

#### **🔬 Full Featured:**
1. Run `transfer_data_to_vps.sh`
2. SSH to VPS and install packages
3. Run `data_migration_system.py`
4. Import journal data and advanced features

---

**✅ After migration, your FacultyFinder will have real university and faculty data powering all features! 🎉** 