# Scopus Faculty Search System Guide

## Overview

The Scopus Faculty Search System provides comprehensive publication data collection from Scopus, the world's largest abstract and citation database. Unlike PubMed which focuses on medical and life sciences, Scopus covers all research fields including:

- **Physical Sciences & Engineering**: Physics, Chemistry, Computer Science, Engineering
- **Life Sciences**: Medicine, Neuroscience, Biochemistry, Agriculture  
- **Health Sciences**: Medicine, Nursing, Dentistry, Health Professions
- **Social Sciences & Humanities**: Psychology, Economics, Business, Arts

## Key Features

### 🔍 **Dual Search Strategy**
- **Author-only searches**: `AUTHOR-NAME("Smith, J.")`
- **Author + Affiliation searches**: `AUTHOR-NAME("Smith, J.") AND AFFIL(McMaster)`
- Automatic name format variations (initials, full names)

### 📊 **Comprehensive Data Extraction**
- **Abstracts**: Full abstract text when available
- **Author Details**: Names, ORCID IDs, Scopus Author IDs, affiliations
- **Journal Information**: Name, ISSN, volume, issue, pages, publication date
- **Metrics**: Citation counts, publication types
- **Keywords**: Author-provided keywords
- **Subject Areas**: Scopus subject classifications
- **DOIs**: Digital Object Identifiers for linking

### 💾 **Structured Data Storage**
- Individual JSON files: `data/publications/scopus/[scopus_id].json`
- Faculty tracking CSVs: `data/faculties/[country]/[province]/[university]/publications/[faculty_id].csv`
- Current affiliation flags (TRUE/FALSE based on dual search results)

### ⚡ **Smart Features**
- Rate limiting to respect Scopus API quotas
- Resumable searches with `--start-from` option
- Progress tracking and statistics
- Automatic duplicate handling
- Error recovery and retry logic

## Installation & Setup

### Prerequisites
```bash
pip install requests pathlib
```

### API Key Configuration
Your Scopus API key is already configured: `a40794bde2315194803ca0422b5fe851`

## Usage Examples

### Basic Usage
```bash
# Search for 5 faculty members with 2-second delays
python3 scopus_faculty_searcher.py data/faculties/CA/ON/CA-ON-002_mcmaster.ca/mcmaster_hei_faculty.csv --max 5 --delay 2
```

### Advanced Options
```bash
# Resume from a specific faculty member
python3 scopus_faculty_searcher.py data/faculties/CA/ON/CA-ON-002_mcmaster.ca/mcmaster_hei_faculty.csv --start-from "Gordon Guyatt" --delay 1.5

# Process all faculty with custom API key
python3 scopus_faculty_searcher.py data/faculties/CA/ON/CA-ON-002_mcmaster.ca/mcmaster_hei_faculty.csv --api-key YOUR_KEY --delay 1.0

# Test with one faculty member
python3 scopus_faculty_searcher.py data/faculties/CA/ON/CA-ON-002_mcmaster.ca/mcmaster_hei_faculty.csv --max 1 --delay 0.5
```

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `csv_file` | Path to faculty CSV file | Required |
| `--api-key` | Scopus API key | Pre-configured |
| `--max` | Maximum faculty to process | All |
| `--delay` | Delay between requests (seconds) | 1.0 |
| `--start-from` | Faculty name to resume from | None |

## Output Structure

### Publication JSON Files
Location: `data/publications/scopus/[scopus_id].json`

```json
{
  "scopus_id": "85123456789",
  "eid": "2-s2.0-85123456789",
  "title": "Advanced Machine Learning Techniques",
  "abstract": "This study presents novel approaches to...",
  "authors": [
    {
      "authid": "56789012345",
      "orcid": "0000-0002-1234-5678",
      "surname": "Smith",
      "given_name": "John",
      "initials": "J.",
      "indexed_name": "Smith, J.",
      "affiliations": [
        {
          "afid": "60022195",
          "name": "McMaster University",
          "city": "Hamilton",
          "country": "Canada"
        }
      ]
    }
  ],
  "journal": {
    "name": "Nature Machine Intelligence",
    "issn": "2522-5839",
    "volume": "4",
    "issue": "3",
    "pages": "245-258",
    "cover_date": "2023-03-15",
    "aggregation_type": "Journal"
  },
  "publication_type": {
    "type": "ar",
    "description": "Article"
  },
  "keywords": ["machine learning", "neural networks", "AI"],
  "subject_areas": [
    {
      "code": "1702",
      "abbreviation": "COMP",
      "name": "Artificial Intelligence"
    }
  ],
  "doi": "10.1038/s42256-023-00123-4",
  "publication_year": 2023,
  "citation_count": 42,
  "source": "scopus"
}
```

### Faculty Tracking CSVs
Location: `data/faculties/[country]/[province]/[university_code_website]/publications/[faculty_id].csv`

**Important**: The folder naming follows the pattern `university_code_website` (e.g., `CA-ON-002_mcmaster.ca`), where:
- `university_code`: From the universities CSV (e.g., CA-ON-002)
- `website`: From the universities CSV (e.g., mcmaster.ca)

Example path: `data/faculties/CA/ON/CA-ON-002_mcmaster.ca/publications/CA-ON-002-00001.csv`

```csv
scopus_id,current_affiliation
85123456789,TRUE
85234567890,FALSE
85345678901,TRUE
```

**Affiliation Flags:**
- `TRUE`: Publication found in both author-only AND author+affiliation searches
- `FALSE`: Publication found only in author-only search (likely previous affiliation)

## Search Query Examples

The system automatically constructs optimized Scopus queries:

### Author Searches
```
AUTHOR-NAME("Guyatt, G.") OR AUTHOR-NAME("Guyatt, Gordon")
```

### Affiliation Searches  
```
(AUTHOR-NAME("Guyatt, G.") OR AUTHOR-NAME("Guyatt, Gordon")) AND AFFIL(McMaster)
```

## Rate Limiting & API Quotas

### Scopus API Limits
- **Development Level**: 9 requests/second
- **Weekly Quota**: 20,000 requests
- **Results per Request**: 25 (default) to 200 (maximum)

### Built-in Protections
- Automatic rate limit detection (HTTP 429)
- 30-second backoff on rate limit hits
- Configurable delays between requests
- Request counting and monitoring

## Data Analysis Capabilities

The comprehensive JSON structure enables powerful analysis:

### Bibliometric Analysis
- Citation impact assessment
- Collaboration network mapping
- Research trend identification
- International cooperation analysis

### Subject Area Analysis  
- Interdisciplinary research patterns
- Field evolution over time
- Cross-domain collaboration

### Author Profiling
- Career trajectory analysis
- Institutional mobility tracking
- ORCID-based disambiguation

### Journal Analysis
- Publication venue preferences
- Impact factor correlation
- Open access patterns

## Integration with Existing Systems

### Database Integration
The JSON structure can be easily imported into:
- PostgreSQL (using JSON/JSONB columns)
- MongoDB (native JSON storage)  
- Elasticsearch (for full-text search)

### PubMed Comparison
```python
# Compare PubMed vs Scopus coverage
pubmed_files = list(Path('data/publications/pubmed').glob('*.json'))
scopus_files = list(Path('data/publications/scopus').glob('*.json'))

print(f"PubMed publications: {len(pubmed_files)}")
print(f"Scopus publications: {len(scopus_files)}")
```

## Advanced Usage Patterns

### Batch Processing
```bash
# Process multiple universities
for university in CA-ON-002 CA-ON-003 CA-BC-001; do
    python3 scopus_faculty_searcher.py data/faculties/CA/ON/$university/faculty.csv --delay 2
done
```

### Error Recovery
```bash
# Resume after interruption
python3 scopus_faculty_searcher.py data/faculties/CA/ON/CA-ON-002_mcmaster.ca/mcmaster_hei_faculty.csv --start-from "Last Processed Name"
```

### Performance Optimization
```bash
# Fast processing with higher rate limits
python3 scopus_faculty_searcher.py data/faculties/CA/ON/CA-ON-002_mcmaster.ca/mcmaster_hei_faculty.csv --delay 0.2 --max 10
```

## Troubleshooting

### Common Issues

**1. Rate Limit Exceeded**
```
⏳ Rate limit hit, waiting 30 seconds...
```
*Solution*: Increase `--delay` parameter or wait for quota reset

**2. Invalid API Key**
```
❌ Scopus search error: 401 Unauthorized
```
*Solution*: Verify API key or request new one from Elsevier

**3. No Results Found**
```
📚 No publications found (author-only)
```
*Solution*: Check name spelling or try alternative name formats

**4. Network Issues**
```
❌ Scopus search error: Connection timeout
```
*Solution*: Check internet connection and retry

### Performance Monitoring

The system provides detailed statistics:
```
📊 Progress Statistics:
   Faculty processed: 45/281
   Successful author searches: 42
   Successful affiliation searches: 38
   Total publications found: 1,247
   Unique publications saved: 1,185
   API requests made: 156
   Rate limit hits: 2
```

## API Reference

### Search Query Fields
- `AUTHOR-NAME()`: Author name search
- `AFFIL()`: Affiliation search  
- `TITLE()`: Title keyword search
- `KEY()`: Keyword search
- `PUBYEAR()`: Publication year
- `DOCTYPE()`: Document type filter

### Response Fields
- `dc:identifier`: Scopus ID
- `dc:title`: Publication title
- `dc:description`: Abstract text
- `prism:doi`: DOI
- `citedby-count`: Citation count
- `authkeywords`: Author keywords
- `subject-area`: Subject classifications

## Future Enhancements

### Planned Features
1. **Author Profile Integration**: Link to Scopus author profiles
2. **Affiliation Mapping**: Enhanced institution name matching
3. **Temporal Analysis**: Publication timeline visualization
4. **Collaboration Networks**: Co-authorship analysis
5. **Impact Metrics**: h-index and other bibliometric indicators

### Integration Opportunities
1. **Web of Science**: Cross-database comparison
2. **Google Scholar**: Complementary coverage analysis
3. **ORCID**: Enhanced author disambiguation
4. **Institutional Repositories**: Local publication verification

---

*Last Updated: December 2024*
*For support, check the error messages and statistics output, or review the comprehensive logging built into the system.* 