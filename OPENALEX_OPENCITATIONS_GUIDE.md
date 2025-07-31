# OpenAlex & OpenCitations Publication System Guide

This guide covers the new **OpenAlex & OpenCitations publication discovery and enhancement system** - a powerful, free alternative to Scopus that provides comprehensive academic publication data across all research fields.

## 🎯 **System Overview**

### **Two-Tier Architecture**

1. **🔍 OpenAlex (Primary Discovery)**
   - **Free & Comprehensive**: 100,000 requests/day, no authentication required
   - **Author-based Search**: Direct search by faculty name + institution
   - **Dual Search Strategy**: Author-only vs Author+Institution for affiliation tracking
   - **Rich Data**: Abstracts, authors, institutions, citations, topics, open access status

2. **🔗 OpenCitations (Citation Enhancement)**
   - **Free Citation Data**: Enhances OpenAlex findings with detailed citation relationships
   - **Citation Networks**: Incoming citations, outgoing references, citation counts
   - **Bibliometric Analysis**: Citation patterns, self-citations, journal impact

### **Data Architecture**

```
data/
├── publications/
│   ├── openalex/           # Primary publication data
│   │   ├── W2123456789.json
│   │   └── W2987654321.json
│   └── opencitations/      # Citation enhancement data
│       ├── 10_1038_nature_12345.json
│       └── 10_1126_science_67890.json
└── faculties/
    └── [country]/[province]/[university_code_website]/
        └── publications/
            ├── CA-ON-002-00001_OpenAlex.csv    # Faculty tracking (OpenAlex)
            ├── CA-ON-002-00001_PubMed.csv      # Faculty tracking (PubMed)
            └── CA-ON-002-00002_OpenAlex.csv
```

## 🚀 **Quick Start**

### **1. OpenAlex Faculty Search**

```bash
# Search for all faculty (recommended for production)
python openalex_faculty_searcher.py data/faculties/CA/ON/CA-ON-002_mcmaster.ca/mcmaster_hei_faculty.csv

# Test with limited faculty and custom settings
python openalex_faculty_searcher.py data/faculties/CA/ON/CA-ON-002_mcmaster.ca/mcmaster_hei_faculty.csv --max 5 --delay 1 --email your.email@university.edu

# High-throughput search (use carefully)
python openalex_faculty_searcher.py data/faculties/CA/ON/CA-ON-002_mcmaster.ca/mcmaster_hei_faculty.csv --delay 0.2 --max-results 200
```

### **2. OpenCitations Enhancement**

```bash
# Enhance all OpenAlex publications with citation data
python opencitations_enhancer.py

# Limited enhancement for testing
python opencitations_enhancer.py --max 50 --delay 2

# With OpenCitations access token (recommended)
python opencitations_enhancer.py --token YOUR_ACCESS_TOKEN --delay 1
```

## 📊 **OpenAlex System**

### **Features**

- **🔍 Dual Search Strategy**
  - **Author-only**: `"Abelson, J." OR "Abelson, Julia" OR "Julia Abelson"`
  - **Author+Institution**: `("Abelson, J." OR "Abelson, Julia") AND "McMaster"`

- **📄 Rich Publication Data**
  - Full abstracts and bibliographic details
  - Complete author lists with ORCID IDs
  - Institution affiliations and addresses
  - Subject classifications and topics
  - Citation counts and open access status
  - Publication venues and journal information

- **🏛️ Institution Matching**
  - Automatic institution name cleaning
  - Flexible matching for university variations
  - Affiliation-based publication filtering

### **Command Line Options**

```bash
python openalex_faculty_searcher.py <csv_file> [options]

Required:
  csv_file              Faculty CSV file path

Optional:
  --max N              Maximum faculty to process (default: all)
  --delay SECONDS      Delay between requests (default: 0.5)
  --email EMAIL        Email for polite pool (default: facultyfinder@research.org)
  --max-results N      Maximum results per search (default: 100)
```

### **Output Files**

#### **1. Individual Publication Files**
`data/publications/openalex/W2123456789.json`
```json
{
  "openalex_id": "W2123456789",
  "doi": "10.1038/nature.2023.12345",
  "title": "Revolutionary Discovery in Quantum Computing",
  "abstract": "This study presents groundbreaking findings...",
  "authors": [
    {
      "display_name": "Julia Abelson",
      "id": "A1234567890",
      "orcid": "https://orcid.org/0000-0001-2345-6789",
      "institutions": [
        {
          "display_name": "McMaster University",
          "country_code": "CA",
          "type": "education"
        }
      ],
      "is_corresponding": true
    }
  ],
  "publication_year": 2023,
  "publication_date": "2023-06-15",
  "type": "article",
  "cited_by_count": 45,
  "source": {
    "display_name": "Nature",
    "issn_l": "0028-0836",
    "type": "journal"
  },
  "concepts": [
    {
      "display_name": "Quantum computing",
      "level": 3,
      "score": 0.89
    }
  ],
  "open_access": {
    "is_oa": true,
    "oa_date": "2023-06-15",
    "oa_url": "https://www.nature.com/articles/..."
  },
  "retrieved_date": "2024-01-15T10:30:00Z",
  "source_database": "OpenAlex"
}
```

#### **2. Faculty Tracking CSVs**
`data/faculties/CA/ON/CA-ON-002_mcmaster.ca/publications/CA-ON-002-00001_OpenAlex.csv`
```csv
openalex_id,current_affiliation
W2123456789,TRUE
W2987654321,FALSE
W3456789012,TRUE
```

**Current Affiliation Logic:**
- `TRUE`: Publication found in both author-only AND author+institution searches
- `FALSE`: Publication found ONLY in author-only search (different affiliation)

**System-Specific Naming:**
- `_OpenAlex.csv`: Publications from OpenAlex searches
- `_PubMed.csv`: Publications from PubMed searches (existing system)
- `_Scopus.csv`: Publications from Scopus searches (if implemented)

## 🔗 **OpenCitations Enhancement**

### **Features**

- **📊 Citation Metrics**
  - Citation counts from multiple sources
  - Incoming citations (papers citing this work)
  - Outgoing references (papers cited by this work)

- **🔍 Citation Analysis**
  - Author self-citations identification
  - Journal self-citations tracking
  - Citation network relationships

- **📋 Enhanced Metadata**
  - Comprehensive bibliographic data
  - Alternative publication identifiers
  - Open access link verification

### **Command Line Options**

```bash
python opencitations_enhancer.py [options]

Optional:
  --max N              Maximum publications to process (default: all)
  --delay SECONDS      Delay between requests (default: 1.0)
  --token TOKEN        OpenCitations access token (recommended)
```

### **Output Files**

#### **Citation Enhancement Files**
`data/publications/opencitations/10_1038_nature_12345.json`
```json
{
  "openalex_id": "W2123456789",
  "doi": "10.1038/nature.2023.12345",
  "title": "Revolutionary Discovery in Quantum Computing",
  "citation_count": 45,
  "citations": [
    {
      "oci": "06101801781-06180334099",
      "citing": "omid:br/06101801781 doi:10.7717/peerj-cs.421",
      "cited": "omid:br/06180334099 doi:10.1038/nature.2023.12345",
      "creation": "2023-08-15",
      "timespan": "P2M0D",
      "journal_sc": "no",
      "author_sc": "no"
    }
  ],
  "references": [
    {
      "oci": "06180334099-06101802023",
      "citing": "omid:br/06180334099 doi:10.1038/nature.2023.12345",
      "cited": "omid:br/06101802023 doi:10.1126/science.2022.67890",
      "creation": "2023-06-15",
      "timespan": "P11M0D",
      "journal_sc": "no",
      "author_sc": "yes"
    }
  ],
  "metadata": {
    "author": "Abelson, Julia; Smith, John; Johnson, Mary",
    "year": "2023",
    "source_title": "Nature",
    "volume": "618",
    "issue": "7965",
    "page": "123-130",
    "oa_link": "https://www.nature.com/articles/nature12345"
  },
  "retrieved_date": "2024-01-15T11:00:00Z",
  "source_database": "OpenCitations"
}
```

## 📈 **Performance & Rate Limits**

### **OpenAlex**
- **Rate Limit**: 100,000 requests/day (per email)
- **Recommended Delay**: 0.5 seconds (polite pool)
- **Throughput**: ~7,200 requests/hour with polite pool
- **Best Practice**: Include email in requests for better performance

### **OpenCitations**
- **Rate Limit**: No official limit, but be respectful
- **Recommended Delay**: 1.0 seconds
- **Access Token**: Recommended for better service
- **Throughput**: ~3,600 requests/hour

### **Estimated Processing Times**

| Faculty Count | OpenAlex (Primary) | OpenCitations (Enhancement) | Total Time |
|---------------|-------------------|----------------------------|------------|
| 10 faculty    | 2-5 minutes       | 5-10 minutes               | 7-15 min   |
| 100 faculty   | 20-50 minutes     | 1-2 hours                  | 1.5-2.5 hrs |
| 281 faculty   | 1-2 hours         | 3-5 hours                  | 4-7 hours  |

## 🔧 **Advanced Configuration**

### **Search Optimization**

```bash
# For high-precision, low-volume searches
python openalex_faculty_searcher.py faculty.csv --delay 1 --max-results 50

# For high-throughput, comprehensive searches  
python openalex_faculty_searcher.py faculty.csv --delay 0.3 --max-results 200

# For testing and development
python openalex_faculty_searcher.py faculty.csv --max 5 --delay 0.5
```

### **Email Configuration**

```bash
# Use your institutional email for better rate limits
python openalex_faculty_searcher.py faculty.csv --email researcher@mcmaster.ca

# Use the same email consistently for tracking
export OPENALEX_EMAIL="your.email@university.edu"
python openalex_faculty_searcher.py faculty.csv --email $OPENALEX_EMAIL
```

### **Resume Capability**

Both systems automatically skip already-processed items:
- **OpenAlex**: Skips existing `.json` files in `data/publications/openalex/`
- **OpenCitations**: Skips DOIs already in `data/publications/opencitations/`

## 🎯 **Integration Workflow**

### **Complete Publication Discovery Workflow**

```bash
#!/bin/bash
# Complete publication discovery and enhancement

echo "🔍 Step 1: OpenAlex Faculty Search"
python openalex_faculty_searcher.py \
    data/faculties/CA/ON/CA-ON-002_mcmaster.ca/mcmaster_hei_faculty.csv \
    --email researcher@mcmaster.ca \
    --delay 0.5

echo "🔗 Step 2: OpenCitations Enhancement"
python opencitations_enhancer.py \
    --token YOUR_ACCESS_TOKEN \
    --delay 1

echo "📊 Step 3: Generate Statistics"
python analyze_publications.py --source openalex --enhancement opencitations

echo "✅ Complete publication discovery finished!"
```

### **Targeted Faculty Search**

```bash
# Search specific faculty subset
python openalex_faculty_searcher.py faculty.csv --max 10

# Enhance only recent publications
python opencitations_enhancer.py --max 100

# Analyze results
ls -la data/publications/openalex/ | wc -l
ls -la data/publications/opencitations/ | wc -l
```

### **Faculty Performance Tracking**

```python
# Example analysis script
import json
import pandas as pd

# Load faculty tracking data from OpenAlex
faculty_df = pd.read_csv('data/faculties/.../publications/CA-ON-002-00001_OpenAlex.csv')

# Calculate affiliation retention rate
current_affiliation_rate = faculty_df['current_affiliation'].value_counts()['TRUE'] / len(faculty_df)

print(f"Current affiliation rate: {current_affiliation_rate:.2%}")

# Compare across different publication systems
pubmed_df = pd.read_csv('data/faculties/.../publications/CA-ON-002-00001_PubMed.csv')
print(f"PubMed publications: {len(pubmed_df)}")
print(f"OpenAlex publications: {len(faculty_df)}")
```