# 👩‍🔬 OpenAlex Author Information Fetcher Guide

## 🎯 **Overview**

The **OpenAlex Author Information Fetcher** (`openalex_author_info_fetcher.py`) is a comprehensive system that extracts detailed author profiles from the OpenAlex API and saves them to structured CSV files. This tool captures **all available author fields** without selectivity, providing complete academic profiles for faculty members.

## 📁 **Output Structure**

```
data/faculties/[country]/[province_state]/[university_code + _ + website]/
└── [university_code + _ + website]_faculty_info_OpenAlex.csv
```

**Example:**
```
data/faculties/CA/ON/CA-ON-002_mcmaster.ca/
└── CA-ON-002_mcmaster.ca_faculty_info_OpenAlex.csv
```

## 📊 **Complete Data Fields Captured**

### **Faculty Information (Original CSV Data)**
- `faculty_id` - Internal faculty identifier
- `faculty_name` - Full name constructed from first_name + last_name
- `faculty_first_name` - First name from CSV
- `faculty_last_name` - Last name from CSV
- `faculty_department` - Department affiliation
- `faculty_position` - Academic position/title
- `faculty_email` - Email address
- `faculty_research_areas` - Research interests from CSV
- `faculty_full_time` - Full-time status
- `faculty_adjunct` - Adjunct status
- `faculty_university_name` - University name
- `faculty_university_code` - University code
- `faculty_country` - Country code
- `faculty_province` - Province/state code

### **OpenAlex Core Information**
- `openalex_id` - Unique OpenAlex author identifier
- `orcid` - ORCID identifier (if available)
- `display_name` - Primary author name in OpenAlex
- `display_name_alternatives` - Alternative name spellings (pipe-separated)

### **Publication & Citation Metrics**
- `works_count` - Total number of published works
- `cited_by_count` - Total citation count
- `2yr_mean_citedness` - Mean citations per work (last 2 years)
- `h_index` - H-index score
- `i10_index` - Number of works with ≥10 citations

### **External Identifiers**
- `openalex_canonical_id` - Canonical OpenAlex ID
- `mag_id` - Microsoft Academic Graph ID
- `scopus_id` - Scopus author ID
- `twitter_id` - Twitter handle
- `wikipedia_id` - Wikipedia page ID

### **Current Institutional Affiliation**
- `last_known_institution_id` - OpenAlex institution ID
- `last_known_institution_name` - Institution name
- `last_known_institution_ror` - ROR identifier
- `last_known_institution_country` - Institution country
- `last_known_institution_type` - Institution type (education, company, etc.)

### **Affiliation History**
- `affiliations_names` - All institution names (pipe-separated)
- `affiliations_years` - Year ranges for each affiliation (pipe-separated)

### **Research Focus & Topics**
- `top_topics_names` - Top 10 research topics (pipe-separated)
- `top_topics_counts` - Publication counts per topic (pipe-separated)
- `top_topics_fields` - Academic fields for each topic (pipe-separated)
- `top_topics_domains` - Academic domains for each topic (pipe-separated)

### **Research Distribution**
- `topic_share_names` - Top 5 research areas by percentage (pipe-separated)
- `topic_share_values` - Percentage values for each area (pipe-separated)

### **Legacy Classification**
- `x_concepts_names` - Legacy concept names (pipe-separated)
- `x_concepts_scores` - Concept relevance scores (pipe-separated)

### **Publication Trends (Last 5 Years)**
- `recent_years` - Year values (pipe-separated)
- `recent_works_counts` - Works published per year (pipe-separated)
- `recent_citations_counts` - Citations received per year (pipe-separated)

### **API & Meta Information**
- `works_api_url` - Direct API URL to fetch author's publications
- `updated_date` - Last update in OpenAlex database
- `created_date` - First appearance in OpenAlex database
- `data_fetched_at` - Timestamp when data was retrieved

## 🚀 **Usage**

### **Basic Usage**
```bash
python3 openalex_author_info_fetcher.py data/faculties/CA/ON/CA-ON-002_mcmaster.ca/mcmaster_hei_faculty.csv
```

### **With Custom Settings**
```bash
python3 openalex_author_info_fetcher.py data/faculties/CA/ON/CA-ON-002_mcmaster.ca/mcmaster_hei_faculty.csv \
    --email your.email@university.edu \
    --delay 1.5 \
    --max 10
```

### **Command-Line Options**
- `--email` - Your email (improves API rate limits)
- `--delay` - Delay between API calls in seconds (default: 1.0)
- `--max` - Maximum faculty to process (for testing)

## 📈 **Sample Output Data**

```csv
"faculty_id","faculty_name","faculty_first_name","faculty_last_name","openalex_id","works_count","cited_by_count","h_index","top_topics_names"
"CA-ON-002-00001","Julia Abelson","Julia","Abelson","https://openalex.org/A5043118077","156","8089","44","Health Policy Implementation Science|Mental Health and Patient Involvement|Primary Care and Health Outcomes"
```

**Key Features:**
- **All fields quoted** - Handles commas in data (e.g., department names)
- **Separate name fields** - `faculty_first_name` and `faculty_last_name` from CSV
- **Comprehensive data** - 50+ fields per faculty member
- **Clean structure** - Proper CSV formatting for reliable parsing

## 🔍 **Advanced Features**

### **Smart Name Matching**
The system uses intelligent name matching to find the correct OpenAlex author profile:
- Exact name matching preferred
- Partial name matching with scoring
- Institution-based disambiguation
- Multiple search strategies

### **Comprehensive Data Extraction**
- **No selective filtering** - captures all available fields
- **Structured hierarchical data** flattened for CSV format
- **Pipe-separated arrays** for multi-value fields
- **Temporal data** with year-by-year breakdowns

### **University Folder Mapping**
Automatically maps university codes to correct folder names using the `UniversityFolderMapper`:
- Reads university data from `data/universities/CA/CA_universities.csv`
- Maps `university_code` to `university_code_website` format
- Ensures consistent naming across all systems

## 📊 **Output Statistics**

The system provides detailed statistics:
```
🎉 Final Statistics:
==================================================
Faculty processed: 281
Authors found: 267
Authors not found: 14
API requests made: 342
Rate limit hits: 0
Errors: 0
==================================================
✅ Author discovery rate: 95.0%
```

## 🔧 **Integration with Existing Systems**

### **Compatibility with Publication Systems**
The author information complements publication data from:
- PubMed searches (`*_PubMed.csv`)
- OpenAlex publication searches (`*_OpenAlex.csv`)
- Future Scopus integration

### **Data Analysis Capabilities**
The comprehensive author profiles enable:
- **Research collaboration analysis** via co-authorship networks
- **Academic impact assessment** through citation metrics
- **Research trend identification** via topic evolution
- **Institutional mobility tracking** through affiliation history
- **Interdisciplinary research mapping** via topic distributions

## 🗂️ **File Organization**

```
data/faculties/CA/ON/CA-ON-002_mcmaster.ca/
├── mcmaster_hei_faculty.csv                    # Source faculty data
├── CA-ON-002_mcmaster.ca_faculty_info_OpenAlex.csv   # Author profiles (NEW!)
└── publications/
    ├── CA-ON-002-00001_OpenAlex.csv           # Publication tracking
    ├── CA-ON-002-00001_PubMed.csv             # Publication tracking
    └── ...
```

## 🔍 **Data Analysis Examples**

### **Research Impact Analysis**
```python
import pandas as pd

# Load author information
authors_df = pd.read_csv('data/faculties/CA/ON/CA-ON-002_mcmaster.ca/CA-ON-002_mcmaster.ca_faculty_info_OpenAlex.csv')

# Top researchers by H-index
top_researchers = authors_df.nlargest(10, 'h_index')[['faculty_name', 'h_index', 'works_count', 'cited_by_count']]

# Research field distribution
field_analysis = authors_df['top_topics_fields'].str.split('|').explode().value_counts()

# Recent productivity trends
recent_productivity = authors_df['recent_works_counts'].str.split('|').apply(lambda x: sum(int(i) for i in x if i.isdigit()))
```

### **Collaboration Network Analysis**
```python
# Identify potential collaborators by research topic overlap
def find_collaborators(faculty_id, topics_column='top_topics_names'):
    faculty_topics = set(authors_df[authors_df['faculty_id'] == faculty_id][topics_column].iloc[0].split('|'))
    
    collaborators = []
    for _, row in authors_df.iterrows():
        if row['faculty_id'] != faculty_id:
            their_topics = set(row[topics_column].split('|'))
            overlap = len(faculty_topics.intersection(their_topics))
            if overlap > 2:  # Significant topic overlap
                collaborators.append((row['faculty_name'], overlap))
    
    return sorted(collaborators, key=lambda x: x[1], reverse=True)
```

## 🔧 **CSV Data Handling**

### **Robust CSV Formatting**
- **All fields quoted** - Every field is enclosed in double quotes to handle commas, quotes, and special characters in the data
- **Comma-safe** - Department names like "Department of Health Research Methods, Evidence, and Impact (HEI)" are properly handled
- **UTF-8 encoding** - Supports international characters and special symbols

### **Name Processing**
- **Source fields** - Uses `first_name` and `last_name` from the HEI faculty CSV file
- **Combined search** - Constructs full name for OpenAlex searches: `first_name + " " + last_name`
- **Separate storage** - Maintains both individual name components and full name in output CSV

### **Data Integrity**
- **Field preservation** - All original CSV fields are maintained in output
- **No data loss** - Comprehensive capture without selective filtering
- **Consistent formatting** - Standardized field naming and structure

## ⚠️ **Important Notes**

### **API Rate Limits**
- OpenAlex: 100,000 requests/day (free)
- No authentication required
- Email parameter improves rate limits
- Automatic rate limit handling included

### **Data Quality Considerations**
- **Author disambiguation**: OpenAlex uses algorithmic matching, may have false positives/negatives
- **Affiliation accuracy**: Historical affiliations may be incomplete
- **Citation lag**: Recent publications may have low citation counts
- **Field classification**: Research topics assigned algorithmically

### **Privacy & Ethics**
- All data from OpenAlex is publicly available
- No personal information beyond academic profiles
- Respects OpenAlex usage terms
- Consider faculty consent for institutional use

## 🔄 **Regular Updates**

### **Recommended Update Frequency**
- **Monthly**: For active research monitoring
- **Quarterly**: For institutional reporting
- **Annually**: For comprehensive faculty reviews

### **Incremental Updates**
```bash
# Update specific faculty members
python3 openalex_author_info_fetcher.py data/faculties/CA/ON/CA-ON-002_mcmaster.ca/mcmaster_hei_faculty.csv --max 50

# Focus on recently hired faculty
python3 openalex_author_info_fetcher.py new_faculty_2024.csv
```

## 🎯 **Next Steps**

1. **Test the system** with a small faculty subset (`--max 5`)
2. **Verify data quality** by checking a few known faculty profiles
3. **Run full extraction** for complete institutional coverage
4. **Integrate with publication data** for comprehensive faculty profiles
5. **Set up regular updates** for ongoing faculty monitoring

## 🆕 **Recent Improvements**

- **Enhanced name handling** - Uses `first_name` and `last_name` from CSV for better accuracy
- **Robust CSV formatting** - All fields quoted to handle commas and special characters
- **Expanded data capture** - Now captures 50 comprehensive fields per faculty
- **Improved data integrity** - Better field separation and preservation

This comprehensive author information system provides the foundation for advanced faculty analytics, research collaboration mapping, and institutional research intelligence! 🌟 