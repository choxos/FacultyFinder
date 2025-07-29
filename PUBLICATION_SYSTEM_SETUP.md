# Automated Publication Update System - Setup Guide

## 🚀 Quick Start

This system automatically updates faculty publications from PubMed, tracks citations via OpenCitations, and processes Scimago journal metrics for your FacultyFinder database.

## 📋 Prerequisites

1. **Python 3.8+** installed on your system
2. **SQLite database** (already included with Python)
3. **Internet connection** for API access
4. **NCBI Entrez email** (required for PubMed API)

## 🔧 Installation

### 1. Install Dependencies

```bash
# Install required packages
pip install -r requirements_publications.txt

# Or install individually:
pip install biopython requests schedule pandas lxml beautifulsoup4
```

### 2. Configuration

Edit the configuration section in `automated_publication_updater.py`:

```python
# Required: Your email for NCBI Entrez API
ENTREZ_EMAIL = "your.email@example.com"  # ⚠️ CHANGE THIS!

# Optional: NCBI API key for higher rate limits
ENTREZ_API_KEY = "your_api_key_here"  # Get from: https://ncbiinsights.ncbi.nlm.nih.gov/2017/11/02/new-api-keys-for-the-e-utilities/

# Database path
DATABASE_PATH = "database/facultyfinder_dev.db"

# Scimago data directory  
SCIMAGO_DATA_DIR = "data/scimagojr"
```

### 3. Download Scimago Data (Optional but Recommended)

The system can work without Scimago data, but journal metrics will be missing.

1. Visit: https://www.scimagojr.com/journalrank.php
2. Download CSV files for different years (2020-2024 recommended)
3. Place them in `data/scimagojr/` directory:
   ```
   data/scimagojr/
   ├── scimagojr 2024.csv
   ├── scimagojr 2023.csv
   ├── scimagojr 2022.csv
   └── ...
   ```

## 🎯 Usage

### Initial Setup

```bash
# Setup database schema and load initial data
python automated_publication_updater.py --setup
```

### Running Updates

```bash
# Run a complete update cycle once
python automated_publication_updater.py --run-once

# Run incremental updates only
python automated_publication_updater.py --incremental  

# Run with verbose logging
python automated_publication_updater.py --run-once --verbose

# Start scheduled automatic updates (runs continuously)
python automated_publication_updater.py --schedule
```

### Scheduled Updates (Automatic Mode)

When running with `--schedule`, the system will:

- **Full Update**: Every Monday at 2:00 AM
- **Incremental Update**: Daily at 6:00 AM  
- **Citation Updates**: Every 6 hours

## 📊 What It Does

### 1. PubMed Publication Search
- Searches for faculty publications using author names and research areas
- Fetches detailed metadata (title, authors, journal, DOI, abstract, etc.)
- Smart author name matching to reduce false positives
- Processes publications from 2020 onwards

### 2. Citation Tracking
- Uses OpenCitations API to get citation counts
- Updates citation data periodically
- Tracks citation trends over time

### 3. Journal Metrics
- Processes Scimago journal rankings
- Adds SJR (SCImago Journal Rank), H-index, quartiles
- Matches journals by ISSN across multiple years

### 4. Database Updates
- Creates enhanced publication tables
- Tracks collaboration networks between faculty
- Logs all update activities for monitoring

## 📈 Monitoring

### Check Logs

```bash
# View recent log entries
tail -f publication_updater.log

# Check for errors
grep ERROR publication_updater.log
```

### Database Queries

```sql
-- Check recent publications
SELECT COUNT(*) FROM publications WHERE created_at > datetime('now', '-7 days');

-- Check citation updates
SELECT COUNT(*) FROM publications WHERE last_citation_update IS NOT NULL;

-- View update log
SELECT * FROM publication_update_log ORDER BY completed_at DESC LIMIT 10;

-- Faculty with most publications
SELECT p.name, COUNT(pub.id) as pub_count 
FROM professors p 
LEFT JOIN publications pub ON p.id = pub.professor_id 
GROUP BY p.id 
ORDER BY pub_count DESC;
```

## 🚨 Common Issues & Solutions

### 1. "No module named 'Bio'" Error
```bash
pip install biopython
```

### 2. "Permission denied" for Database
```bash
# Check file permissions
ls -la database/
chmod 644 database/facultyfinder_dev.db
```

### 3. PubMed API Rate Limiting
- Get an NCBI API key: https://ncbiinsights.ncbi.nlm.nih.gov/2017/11/02/new-api-keys-for-the-e-utilities/
- Add it to `ENTREZ_API_KEY` in the configuration

### 4. No Publications Found
- Check faculty names in database (must match PubMed author format)
- Verify research areas are filled in
- Check internet connection
- Review search query logic in logs

### 5. Scimago Data Issues
- Ensure CSV files are properly formatted (semicolon-separated)
- Check file encoding (should be UTF-8)
- Verify column names match expected format

## 🔧 Advanced Configuration

### Custom Search Patterns

Modify `_build_search_query()` method to customize PubMed search logic:

```python
def _build_search_query(self, faculty_name: str, research_areas: str) -> str:
    # Add institution-specific search terms
    query = f'("{faculty_name}"[Author]) AND ("McMaster University"[Affiliation])'
    return query
```

### Rate Limiting

Adjust delays in configuration:

```python
PUBMED_DELAY = 1.0      # Seconds between PubMed requests
OPENCITATIONS_DELAY = 1.0  # Seconds between citation requests
```

### Batch Processing

Modify batch sizes for large datasets:

```python
# In _fetch_publication_details()
for i in range(0, len(pmids), 50):  # Increase from 20 to 50
```

## 📋 Production Deployment

### 1. Service Setup (Linux)

Create systemd service file `/etc/systemd/system/publication-updater.service`:

```ini
[Unit]
Description=FacultyFinder Publication Updater
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/FacultyFinder
ExecStart=/usr/bin/python3 automated_publication_updater.py --schedule
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable publication-updater
sudo systemctl start publication-updater
```

### 2. Monitoring Script

Create a monitoring script to check system health:

```bash
#!/bin/bash
# check_publications.sh

# Check if process is running
if ! pgrep -f "automated_publication_updater.py" > /dev/null; then
    echo "Publication updater is not running!"
    # Restart service or send alert
fi

# Check recent updates
recent_updates=$(sqlite3 database/facultyfinder_dev.db "SELECT COUNT(*) FROM publication_update_log WHERE completed_at > datetime('now', '-24 hours');")

if [ "$recent_updates" -eq 0 ]; then
    echo "No updates in last 24 hours - check system!"
fi
```

## 📚 API Documentation

### PubMed/Entrez
- Documentation: https://www.ncbi.nlm.nih.gov/books/NBK25499/
- Python Bio.Entrez: https://biopython.org/docs/1.81/api/Bio.Entrez.html

### OpenCitations
- API Docs: https://opencitations.net/index/api/v1
- Rate Limits: No official limit, but be respectful (1 req/sec)

### Scimago Journal Rankings
- Website: https://www.scimagojr.com/
- CSV Download: https://www.scimagojr.com/journalrank.php

## 🆘 Support

If you encounter issues:

1. Check the log file: `publication_updater.log`
2. Verify all dependencies are installed
3. Ensure database permissions are correct
4. Test internet connectivity to APIs
5. Review configuration settings

## 🎉 Success Indicators

System is working correctly when you see:

- ✅ Publications appearing in database
- ✅ Citation counts being updated  
- ✅ Journal metrics populated
- ✅ Regular log entries without errors
- ✅ Homepage statistics increasing over time

---

**Happy Publication Tracking! 📊🔬** 