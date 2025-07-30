# Database Update Guide for FacultyFinder

## 🎯 **When You Update Your CSV Files**

When you modify `data/mcmaster_hei_faculty.csv` or other data files, you need to update the database to reflect these changes. This guide provides multiple approaches based on your needs.

---

## 🚀 **Quick Start (Most Common)**

### **Simple One-Command Update:**
```bash
./update_db.sh
```
This will:
- ✅ Perform incremental update from your CSV
- ✅ Restart the FacultyFinder service
- ✅ Show you the results

---

## 📖 **All Available Options**

### **1. 🔄 Incremental Update (Recommended)**
```bash
./update_db.sh                    # Update + restart service
./update_db.sh quick              # Update only (no restart)
```

**When to use:**
- ✅ Added new faculty members
- ✅ Updated existing faculty information  
- ✅ Minor changes to CSV file
- ✅ You want fast updates (keeps existing data)

**What it does:**
- Compares CSV with database
- Adds new professors
- Updates changed information
- Preserves existing data and IDs

---

### **2. 🗑️ Full Rebuild**
```bash
./update_db.sh full               # Complete rebuild + restart
```

**When to use:**
- ❗ Major structural changes to CSV
- ❗ Database corruption or inconsistencies
- ❗ You want a completely fresh start
- ❗ Added/removed universities

**What it does:**
- Completely wipes the database
- Recreates all tables and data from scratch
- Regenerates all professor IDs
- Takes longer but ensures consistency

---

### **3. 📊 Status Check**
```bash
./update_db.sh check              # Check database status
```

**Shows you:**
- Current number of professors
- Number of universities
- Recent database entries
- Overall database health

---

## 🛠️ **Advanced Usage**

### **Direct Python Script:**
```bash
# Incremental update
python3 update_database_from_csv.py --mode incremental --restart

# Full rebuild  
python3 update_database_from_csv.py --mode full --restart

# Status check
python3 update_database_from_csv.py --mode status

# Custom CSV file
python3 update_database_from_csv.py --csv path/to/your/file.csv --restart
```

### **Available Modes:**
- `incremental` - Smart update (default)
- `full` - Complete rebuild
- `status` - Check database status

### **Available Flags:**
- `--restart` - Restart service after update
- `--csv` - Specify custom CSV file path

---

## 📋 **Step-by-Step Workflow**

### **Typical Update Process:**

1. **Edit your CSV file:**
   ```bash
   nano data/mcmaster_hei_faculty.csv
   # Make your changes and save
   ```

2. **Check current status (optional):**
   ```bash
   ./update_db.sh check
   ```

3. **Update the database:**
   ```bash
   ./update_db.sh
   ```

4. **Verify the changes:**
   - Visit your website: `https://facultyfinder.io`
   - Check that new/updated faculty appear correctly

---

## 🔧 **What Happens During Updates**

### **Incremental Update Process:**
1. 📖 Reads your CSV file
2. 🔍 Compares with existing database records
3. ➕ Adds new faculty members (assigns new IDs)
4. 🔄 Updates changed information for existing faculty
5. 💾 Commits changes to database
6. 🔄 Restarts FacultyFinder service (if `--restart`)

### **Full Rebuild Process:**
1. 🗑️ Completely wipes database tables
2. 🏗️ Recreates database schema
3. 📥 Imports universities from `data/university_codes.csv`
4. 👥 Imports faculty from `data/mcmaster_hei_faculty.csv`  
5. 🔢 Generates new professor IDs
6. ✅ Verifies data integrity
7. 🔄 Restarts service

---

## ⚠️ **Important Notes**

### **CSV File Requirements:**
Your `data/mcmaster_hei_faculty.csv` should have these columns:
- `name` - Faculty member name (required)
- `university_code` - University identifier (required)
- `first_name`, `last_name` - Name components
- `department` - Department/faculty
- `position` - Academic position
- `full_time` - TRUE/FALSE for employment type
- `adjunct` - TRUE/FALSE for adjunct status
- `uni_email`, `other_email` - Contact information
- `research_areas` - Research interests
- `website`, `twitter`, `linkedin` - Social/web links

### **ID Management:**
- **Incremental updates**: Preserves existing professor IDs
- **Full rebuilds**: Regenerates all IDs from scratch
- Professor IDs format: `CA-ON-002-00001` (university-sequence)

### **Service Restart:**
- Required to see changes on the website
- Use `--restart` flag or `./update_db.sh` (includes restart)
- Manual restart: `sudo systemctl restart facultyfinder.service`

---

## 🚨 **Troubleshooting**

### **Common Issues:**

**❌ "Database connection failed"**
```bash
# Check your .env file exists and has correct credentials
ls -la .env
cat .env  # Verify DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
```

**❌ "CSV file not found"**
```bash
# Verify CSV file exists
ls -la data/mcmaster_hei_faculty.csv
```

**❌ "Service restart failed"**
```bash
# Manual service restart
sudo systemctl restart facultyfinder.service
sudo systemctl status facultyfinder.service
```

**❌ "Update failed with SQL error"**
```bash
# Try full rebuild instead
./update_db.sh full
```

### **Recovery Options:**

1. **Try incremental first:** `./update_db.sh`
2. **If that fails, try full rebuild:** `./update_db.sh full`
3. **Check service status:** `sudo systemctl status facultyfinder.service`
4. **View recent logs:** `sudo journalctl -u facultyfinder.service -n 20`

---

## 🎯 **Best Practices**

### **Before Updating:**
- ✅ Backup your CSV file: `cp data/mcmaster_hei_faculty.csv data/mcmaster_hei_faculty.csv.backup`
- ✅ Check current status: `./update_db.sh check`
- ✅ Test changes on a small subset first

### **For Regular Updates:**
- ✅ Use incremental updates for speed
- ✅ Use full rebuild only when necessary
- ✅ Always include `--restart` or use `./update_db.sh`
- ✅ Verify changes on the website afterward

### **For Production:**
- ✅ Test updates on staging/development first
- ✅ Update during low-traffic periods
- ✅ Monitor service status after updates
- ✅ Keep backups of working CSV files

---

## 📞 **Quick Reference**

| Task | Command | Time | Data Preservation |
|------|---------|------|-------------------|
| **Regular Update** | `./update_db.sh` | ~30s | ✅ Preserves IDs |
| **Quick Update** | `./update_db.sh quick` | ~20s | ✅ Preserves IDs |
| **Full Rebuild** | `./update_db.sh full` | ~2-3min | ❌ Recreates IDs |
| **Status Check** | `./update_db.sh check` | ~5s | ➖ Read-only |

**Most common:** `./update_db.sh` (incremental update + restart)

---

## ✅ **Summary**

When you update your CSV files:

1. **Quick and easy:** `./update_db.sh`
2. **Check it worked:** Visit your website and verify changes
3. **If issues:** Try `./update_db.sh full` for complete rebuild

Your database will be updated and your website will reflect the changes! 🎉
