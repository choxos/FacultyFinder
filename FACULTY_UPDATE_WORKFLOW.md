# Faculty Data Management Workflow

This document outlines the complete workflow for managing faculty data from CSV updates through publication retrieval and database integration.

## 📋 Overview

The workflow consists of several stages:
1. **CSV Update** → **JSON Generation** → **Database Update**
2. **Publication Retrieval** (PubMed + OpenAlex)
3. **Metrics Enhancement** (OpenAlex metrics integration)

## 🔄 Complete Workflow

### Stage 1: Faculty Data Processing

#### 1.1 When CSV is Updated

```bash
# Run the JSON generator for updated faculty data
python3 create_faculty_jsons.py

# This will create individual JSON files in:
# data/faculties/CA/ON/CA-ON-002_mcmaster.ca/HEI/CA-ON-002_mcmaster.ca_HEI_jsons/
```

#### 1.2 Update PostgreSQL Database

```bash
# Update database configuration in json_to_postgres.py
# Then run the database updater
python3 json_to_postgres.py
```

**Database Configuration Setup:**
```python
db_config = {
    'host': 'localhost',  # or your database host
    'port': 5432,
    'database': 'facultyfinder_dev',  # your database name
    'user': 'your_username',
    'password': 'your_password'
}
```

### Stage 2: Publication Data Retrieval

#### 2.1 PubMed Integration

**Automated PubMed Search:**
```bash
# Search PubMed for each faculty member's publications
python3 scripts/pubmed_faculty_searcher.py --faculty-json-dir="data/faculties/CA/ON/CA-ON-002_mcmaster.ca/HEI/CA-ON-002_mcmaster.ca_HEI_jsons"
```

**What this does:**
- Searches PubMed using faculty name variations
- Retrieves publication metadata (PMID, title, abstract, authors, journal, etc.)
- Stores results in JSON format in `data/publications/pubmed/`
- Links publications to faculty members in database

#### 2.2 OpenAlex Integration

**Automated OpenAlex Search:**
```bash
# Search OpenAlex for comprehensive publication data
python3 scripts/openalex_faculty_searcher.py --faculty-json-dir="data/faculties/CA/ON/CA-ON-002_mcmaster.ca/HEI/CA-ON-002_mcmaster.ca_HEI_jsons"
```

**What this does:**
- Uses faculty ORCID, OpenAlex ID, or name matching
- Retrieves comprehensive publication metadata
- Gets citation counts, collaboration networks
- Stores results in `data/publications/openalex/`

### Stage 3: Enhanced Metrics from OpenAlex

#### 3.1 Faculty Metrics Enhancement

**Retrieve Additional Metrics:**
```bash
# Enhance faculty profiles with OpenAlex metrics
python3 scripts/openalex_metrics_enhancer.py
```

**Metrics Retrieved:**
- **H-index**: Citation-based productivity measure
- **i10-index**: Number of publications with ≥10 citations
- **Total citations**: Cumulative citation count
- **Open access percentage**: % of publications that are open access
- **Publication count by year**: Temporal publication patterns
- **Collaboration metrics**: Co-authorship statistics

#### 3.2 Database Schema for Metrics

**Additional database columns for faculty metrics:**
```sql
ALTER TABLE professors ADD COLUMN IF NOT EXISTS h_index INTEGER DEFAULT 0;
ALTER TABLE professors ADD COLUMN IF NOT EXISTS i10_index INTEGER DEFAULT 0;
ALTER TABLE professors ADD COLUMN IF NOT EXISTS total_citations INTEGER DEFAULT 0;
ALTER TABLE professors ADD COLUMN IF NOT EXISTS open_access_percentage DECIMAL(5,2) DEFAULT 0.0;
ALTER TABLE professors ADD COLUMN IF NOT EXISTS publication_count INTEGER DEFAULT 0;
ALTER TABLE professors ADD COLUMN IF NOT EXISTS last_metrics_update TIMESTAMP;
```

## 🛠️ Scripts and Tools

### Core Scripts

1. **`create_faculty_jsons.py`** - Converts CSV to individual JSON files
2. **`json_to_postgres.py`** - Updates PostgreSQL from JSON files
3. **`pubmed_faculty_searcher.py`** - PubMed publication retrieval
4. **`openalex_faculty_searcher.py`** - OpenAlex publication retrieval
5. **`openalex_metrics_enhancer.py`** - Enhanced metrics from OpenAlex

### Configuration Files

```bash
# Database configuration
cp config/database.env.example config/database.env
# Edit with your database credentials

# API configuration for external services
cp config/apis.env.example config/apis.env
# Add API keys for PubMed, OpenAlex if needed
```

## 📊 Publication Data Pipeline

### Data Flow Architecture

```
CSV Faculty Data
       ↓
   JSON Files
       ↓
PostgreSQL Database
       ↓
Publication Retrieval
   ↓         ↓
PubMed    OpenAlex
   ↓         ↓
Publication Database
       ↓
Enhanced Metrics
       ↓
Updated Faculty Profiles
```

### Publication Storage Structure

```
data/publications/
├── pubmed/
│   ├── {pmid}.json
│   └── faculty_publications/
│       └── {faculty_id}_publications.json
├── openalex/
│   ├── {work_id}.json
│   └── faculty_publications/
│       └── {faculty_id}_publications.json
└── combined/
    └── {faculty_id}_all_publications.json
```

## 🔧 Automated Workflow Script

### Complete Automation

Create `update_faculty_pipeline.sh`:

```bash
#!/bin/bash
# Complete Faculty Data Update Pipeline

echo "🚀 Starting Faculty Data Update Pipeline"

# Stage 1: Generate JSON files from CSV
echo "📝 Stage 1: Converting CSV to JSON files..."
python3 create_faculty_jsons.py
if [ $? -eq 0 ]; then
    echo "✅ JSON files created successfully"
else
    echo "❌ Failed to create JSON files"
    exit 1
fi

# Stage 2: Update PostgreSQL database
echo "💾 Stage 2: Updating PostgreSQL database..."
python3 json_to_postgres.py
if [ $? -eq 0 ]; then
    echo "✅ Database updated successfully"
else
    echo "❌ Failed to update database"
    exit 1
fi

# Stage 3: Retrieve publications from PubMed
echo "📚 Stage 3: Retrieving PubMed publications..."
python3 scripts/pubmed_faculty_searcher.py --batch-mode
if [ $? -eq 0 ]; then
    echo "✅ PubMed publications retrieved"
else
    echo "⚠️ PubMed retrieval had issues (continuing...)"
fi

# Stage 4: Retrieve publications from OpenAlex
echo "🔬 Stage 4: Retrieving OpenAlex publications..."
python3 scripts/openalex_faculty_searcher.py --batch-mode
if [ $? -eq 0 ]; then
    echo "✅ OpenAlex publications retrieved"
else
    echo "⚠️ OpenAlex retrieval had issues (continuing...)"
fi

# Stage 5: Enhance with OpenAlex metrics
echo "📈 Stage 5: Enhancing with OpenAlex metrics..."
python3 scripts/openalex_metrics_enhancer.py
if [ $? -eq 0 ]; then
    echo "✅ Metrics enhancement completed"
else
    echo "⚠️ Metrics enhancement had issues"
fi

echo "🎉 Faculty Data Update Pipeline Completed!"
```

## 📋 Manual Workflow Steps

### When You Update a CSV File:

1. **Backup Current Data** (recommended)
   ```bash
   # Backup current JSON files
   cp -r data/faculties/CA/ON/CA-ON-002_mcmaster.ca/HEI/CA-ON-002_mcmaster.ca_HEI_jsons/ \
         data/faculties/CA/ON/CA-ON-002_mcmaster.ca/HEI/CA-ON-002_mcmaster.ca_HEI_jsons_backup_$(date +%Y%m%d)
   ```

2. **Generate New JSON Files**
   ```bash
   python3 create_faculty_jsons.py
   ```

3. **Update Database**
   ```bash
   python3 json_to_postgres.py
   ```

4. **Retrieve Publications** (for new faculty or updated profiles)
   ```bash
   # PubMed search
   python3 scripts/pubmed_faculty_searcher.py
   
   # OpenAlex search
   python3 scripts/openalex_faculty_searcher.py
   ```

5. **Update Metrics**
   ```bash
   python3 scripts/openalex_metrics_enhancer.py
   ```

6. **Verify Updates**
   ```bash
   # Check database for new records
   python3 scripts/verify_faculty_updates.py
   ```

## 🔍 OpenAlex Metrics Integration

### Key Metrics Retrieved

1. **Productivity Metrics:**
   - Total publications
   - Publications by year
   - Average publications per year

2. **Impact Metrics:**
   - H-index
   - i10-index
   - Total citations
   - Average citations per paper

3. **Accessibility Metrics:**
   - Open access percentage
   - Gold/Green/Bronze OA breakdown

4. **Collaboration Metrics:**
   - Number of unique co-authors
   - International collaboration percentage
   - Institution collaboration networks

### Data Enhancement Process

```python
# Example metrics structure stored in database
{
    "faculty_id": "CA-ON-002-00001",
    "metrics": {
        "h_index": 23,
        "i10_index": 45,
        "total_citations": 1245,
        "publication_count": 89,
        "open_access_percentage": 67.4,
        "collaboration_metrics": {
            "unique_coauthors": 156,
            "international_collab_pct": 34.5
        },
        "temporal_metrics": {
            "publications_by_year": {...},
            "citations_by_year": {...}
        },
        "last_updated": "2025-01-09T20:00:00Z"
    }
}
```

## 🛡️ Error Handling and Monitoring

### Common Issues and Solutions

1. **CSV Encoding Issues**
   - Ensure CSV files are UTF-8 encoded
   - Script handles BOM characters automatically

2. **Database Connection Issues**
   - Verify PostgreSQL is running
   - Check database credentials in config

3. **API Rate Limits**
   - PubMed: 3 requests/second limit
   - OpenAlex: No strict limits, but be respectful

4. **Missing Publications**
   - Try name variations for faculty searches
   - Manual verification for important faculty

### Monitoring and Logs

```bash
# Enable detailed logging
export FACULTY_UPDATE_LOG_LEVEL=DEBUG

# Run with logging
python3 json_to_postgres.py 2>&1 | tee logs/faculty_update_$(date +%Y%m%d_%H%M%S).log
```

## 📅 Recommended Update Schedule

- **Faculty Data**: Monthly or as needed when CSV changes
- **Publications**: Weekly automated retrieval
- **Metrics**: Monthly for comprehensive updates
- **Database Backup**: Before any major updates

This workflow ensures your faculty database stays current with comprehensive publication data and accurate metrics from authoritative sources. 