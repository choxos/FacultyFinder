# University Data Collection Guide 🎓

## Legal Methods for Gathering University Information

This guide provides comprehensive advice on legally collecting university data including student numbers, department information, rankings, and statistics for your FacultyFinder platform.

---

## 📋 **Table of Contents**

1. [Legal Considerations](#legal-considerations)
2. [Official University Sources](#official-university-sources)
3. [Government & Public APIs](#government--public-apis)
4. [Educational Ranking Services](#educational-ranking-services)
5. [Open Data Sources](#open-data-sources)
6. [Commercial APIs](#commercial-apis)
7. [Web Scraping Guidelines](#web-scraping-guidelines)
8. [Data Storage & Attribution](#data-storage--attribution)
9. [Implementation Strategy](#implementation-strategy)

---

## 🔒 **Legal Considerations**

### ✅ **What's Generally Legal**

- **Public Information**: Officially published statistics and facts
- **Government Data**: Open government datasets and APIs
- **Published Rankings**: Using ranking data with proper attribution
- **University Websites**: Publicly available information (with proper scraping ethics)
- **API Data**: Data accessed through official APIs with terms compliance

### ⚠️ **What to Avoid**

- **Copyrighted Content**: Reproducing copyrighted text, images, or proprietary analysis
- **Personal Data**: Student/faculty personal information without consent
- **Behind Paywalls**: Content requiring subscription or payment
- **Terms of Service Violations**: Scraping when explicitly prohibited
- **Excessive Requests**: Overloading servers with rapid requests

### 📄 **Copyright & Fair Use**

**Times Higher Education (THE) Rankings:**
- ✅ **Legal**: Referencing THE ranking positions (e.g., "Ranked #45 by THE")
- ✅ **Legal**: Using factual data (enrollment numbers, founding year)
- ❌ **Avoid**: Copying THE's analysis, methodology descriptions, or branded content
- ✅ **Best Practice**: Attribute rankings and link to original source

---

## 🏛️ **Official University Sources**

### **1. University Official Websites**

**What to Collect:**
```
✅ Basic Information:
- Official name and address
- Year established
- Student enrollment numbers (if published)
- Number of faculties/schools
- Contact information
- Official website URLs

✅ Academic Structure:
- Faculty/school names
- Department listings
- Program offerings
- Campus locations

✅ Public Statistics:
- Enrollment numbers (if published)
- Faculty-to-student ratios
- International student percentages
- Research expenditures (if published)
```

**Legal Implementation:**
```python
# Example scraping with proper ethics
import requests
from bs4 import BeautifulSoup
import time

def scrape_university_data(url):
    # Always include User-Agent and respect robots.txt
    headers = {
        'User-Agent': 'FacultyFinder/1.0 (contact@facultyfinder.io)',
        'Accept': 'text/html,application/xhtml+xml'
    }
    
    # Add delays between requests
    time.sleep(2)
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None
```

### **2. University Fact Sheets & Annual Reports**

**Sources:**
- Official fact sheets (usually in "About" sections)
- Annual reports and financial statements
- Student handbooks and calendars
- Research reports and statistics

---

## 🌐 **Government & Public APIs**

### **1. United States**

**IPEDS (Integrated Postsecondary Education Data System)**
- **API**: https://nces.ed.gov/ipeds/use-the-data
- **Data**: Enrollment, graduation rates, finances, faculty
- **Legal Status**: ✅ Public domain
- **Implementation**:
```python
import requests

def get_ipeds_data(unitid):
    """
    Get university data from IPEDS API
    """
    base_url = "https://educationdata.urban.org/api/v1/schools/ipeds"
    
    # Get basic institutional data
    institutional_url = f"{base_url}/directory/{unitid}/"
    enrollment_url = f"{base_url}/enrollment-full-time-equivalent/{unitid}/"
    
    try:
        inst_response = requests.get(institutional_url)
        enroll_response = requests.get(enrollment_url)
        
        return {
            'institutional': inst_response.json(),
            'enrollment': enroll_response.json()
        }
    except Exception as e:
        print(f"Error fetching IPEDS data: {e}")
        return None
```

### **2. Canada**

**Statistics Canada University Information**
- **Source**: https://www.statcan.gc.ca/en/subjects/education
- **Data**: Enrollment, degrees granted, faculty numbers
- **Legal Status**: ✅ Open Government License

### **3. United Kingdom**

**HESA (Higher Education Statistics Agency)**
- **Source**: https://www.hesa.ac.uk/data-and-analysis
- **Data**: Student numbers, staff statistics, finances
- **Legal Status**: ✅ Some data freely available, some requires license

### **4. Australia**

**Department of Education Data**
- **Source**: https://www.education.gov.au/higher-education-statistics
- **Data**: University statistics and performance data
- **Legal Status**: ✅ Creative Commons license

---

## 📊 **Educational Ranking Services**

### **1. Times Higher Education (THE)**

**✅ Legal Usage:**
```python
# Example of proper THE data usage
university_data = {
    'name': 'University of Toronto',
    'the_world_ranking_2025': 21,  # ✅ Factual information
    'the_ranking_source': 'Times Higher Education World University Rankings 2025',
    'the_ranking_url': 'https://www.timeshighereducation.com/world-university-rankings/2025',
    'ranking_attribution': '© Times Higher Education'
}
```

**❌ Avoid:**
- Copying THE's methodology descriptions
- Using THE's copyrighted images or branding
- Reproducing THE's analysis text

### **2. QS World University Rankings**

**Legal Approach:**
```python
# Proper QS ranking usage
def add_qs_ranking(university_id, rank, year):
    return {
        'university_id': university_id,
        'qs_ranking': rank,
        'ranking_year': year,
        'source': 'QS World University Rankings',
        'attribution': '© QS Quacquarelli Symonds Limited'
    }
```

### **3. Academic Ranking of World Universities (ARWU)**

**Shanghai Rankings - Legal Usage:**
- ✅ Reference ranking positions
- ✅ Attribute to "Shanghai Ranking's Academic Ranking of World Universities"
- ❌ Copy their analysis or methodology

---

## 📂 **Open Data Sources**

### **1. Wikidata**

**University Data Available:**
```sparql
# SPARQL query for university data
SELECT ?university ?universityLabel ?inception ?student_count ?country WHERE {
  ?university wdt:P31/wdt:P279* wd:Q3918 .  # Instance of university
  ?university wdt:P571 ?inception .          # Inception date
  OPTIONAL { ?university wdt:P2196 ?student_count . }  # Student count
  ?university wdt:P17 ?country .             # Country
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
}
```

**Implementation:**
```python
import requests

def get_wikidata_university_info(university_name):
    """
    Get university information from Wikidata
    """
    sparql_endpoint = "https://query.wikidata.org/sparql"
    
    query = f"""
    SELECT ?university ?universityLabel ?inception ?student_count ?country ?countryLabel WHERE {{
      ?university rdfs:label "{university_name}"@en .
      ?university wdt:P31/wdt:P279* wd:Q3918 .
      OPTIONAL {{ ?university wdt:P571 ?inception . }}
      OPTIONAL {{ ?university wdt:P2196 ?student_count . }}
      OPTIONAL {{ ?university wdt:P17 ?country . }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }}
    """
    
    try:
        response = requests.get(sparql_endpoint, params={'query': query, 'format': 'json'})
        return response.json()
    except Exception as e:
        print(f"Wikidata query error: {e}")
        return None
```

### **2. OpenStreetMap**

**University Location Data:**
```python
import overpy

def get_university_osm_data(university_name, city):
    """
    Get university data from OpenStreetMap
    """
    api = overpy.Overpass()
    
    query = f"""
    [out:json];
    (
      way["amenity"="university"]["name"~"{university_name}",i];
      relation["amenity"="university"]["name"~"{university_name}",i];
    );
    out center;
    """
    
    try:
        result = api.query(query)
        return result
    except Exception as e:
        print(f"OSM query error: {e}")
        return None
```

---

## 💼 **Commercial APIs**

### **1. Clearbit Company API**

**University Information:**
```python
import requests

def get_clearbit_university_data(domain):
    """
    Get university data from Clearbit (requires API key)
    """
    headers = {'Authorization': f'Bearer {CLEARBIT_API_KEY}'}
    url = f"https://company.clearbit.com/v2/companies/find?domain={domain}"
    
    try:
        response = requests.get(url, headers=headers)
        return response.json()
    except Exception as e:
        print(f"Clearbit API error: {e}")
        return None
```

### **2. SemRush University Data**

**For Website Analytics:**
```python
def get_semrush_data(domain):
    """
    Get website analytics for university domains
    """
    url = f"https://api.semrush.com/"
    params = {
        'type': 'domain_overview',
        'domain': domain,
        'database': 'us',
        'key': SEMRUSH_API_KEY
    }
    
    try:
        response = requests.get(url, params=params)
        return response.text
    except Exception as e:
        print(f"SemRush API error: {e}")
        return None
```

---

## 🤖 **Web Scraping Guidelines**

### **Legal & Ethical Scraping**

**1. Check robots.txt:**
```python
import urllib.robotparser

def check_robots_txt(base_url):
    """
    Check if scraping is allowed according to robots.txt
    """
    robots_url = f"{base_url}/robots.txt"
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)
    rp.read()
    
    return rp.can_fetch('*', base_url)
```

**2. Respectful Rate Limiting:**
```python
import time
from functools import wraps

def rate_limit(delay_seconds=2):
    """
    Decorator to add delays between requests
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            time.sleep(delay_seconds)
            return func(*args, **kwargs)
        return wrapper
    return decorator

@rate_limit(2.0)  # 2-second delay between requests
def scrape_page(url):
    # Your scraping logic here
    pass
```

**3. User-Agent Best Practices:**
```python
headers = {
    'User-Agent': 'FacultyFinder-Bot/1.0 (+https://facultyfinder.io/about; contact@facultyfinder.io)',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
}
```

### **Target Data Points for Scraping**

**University Websites - Safe to Scrape:**
```python
university_data_points = {
    'basic_info': [
        'official_name',
        'establishment_year',
        'address',
        'phone_number',
        'official_email',
        'website_url'
    ],
    'academic_structure': [
        'faculty_names',
        'school_names', 
        'department_list',
        'campus_locations'
    ],
    'published_statistics': [
        'total_enrollment',  # Only if publicly stated
        'international_students_percentage',
        'faculty_count',  # If published
        'campus_size'
    ]
}
```

---

## 📝 **Data Storage & Attribution**

### **Database Schema for University Data**

```sql
-- Add these columns to your universities table
ALTER TABLE universities ADD COLUMN student_population INTEGER;
ALTER TABLE universities ADD COLUMN faculty_count INTEGER;
ALTER TABLE universities ADD COLUMN international_students_percentage DECIMAL(5,2);
ALTER TABLE universities ADD COLUMN campus_size_acres INTEGER;
ALTER TABLE universities ADD COLUMN research_expenditure BIGINT;
ALTER TABLE universities ADD COLUMN the_ranking INTEGER;
ALTER TABLE universities ADD COLUMN qs_ranking INTEGER;
ALTER TABLE universities ADD COLUMN arwu_ranking INTEGER;
ALTER TABLE universities ADD COLUMN ranking_year INTEGER;
ALTER TABLE universities ADD COLUMN data_source VARCHAR(255);
ALTER TABLE universities ADD COLUMN last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Create separate table for multiple rankings
CREATE TABLE university_rankings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    university_id INTEGER,
    ranking_system VARCHAR(50),
    ranking_position INTEGER,
    ranking_year INTEGER,
    source_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (university_id) REFERENCES universities(id)
);

-- Create table for departments/schools
CREATE TABLE university_departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    university_id INTEGER,
    department_name VARCHAR(255),
    department_type VARCHAR(50), -- 'faculty', 'school', 'college', 'department'
    faculty_count INTEGER,
    student_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (university_id) REFERENCES universities(id)
);
```

### **Proper Attribution**

```python
# Example attribution for different sources
attributions = {
    'ipeds': {
        'source': 'IPEDS (Integrated Postsecondary Education Data System)',
        'url': 'https://nces.ed.gov/ipeds/',
        'license': 'Public Domain',
        'attribution': 'Data from IPEDS, U.S. Department of Education'
    },
    'the_rankings': {
        'source': 'Times Higher Education World University Rankings',
        'url': 'https://www.timeshighereducation.com/',
        'attribution': '© Times Higher Education. Rankings used with attribution.',
        'license': 'Fair Use - Factual Data'
    },
    'wikidata': {
        'source': 'Wikidata',
        'url': 'https://www.wikidata.org/',
        'license': 'CC0 1.0 Universal Public Domain Dedication',
        'attribution': 'Data from Wikidata, CC0 License'
    },
    'official_website': {
        'source': 'University Official Website',
        'attribution': 'Data from official university sources',
        'license': 'Publicly Available Information'
    }
}
```

---

## 🛠️ **Implementation Strategy**

### **Phase 1: Government & Open Data**

```python
def collect_university_data_phase1():
    """
    Start with the safest, most legal sources
    """
    
    # 1. Get US universities from IPEDS
    us_universities = fetch_ipeds_data()
    
    # 2. Get Canadian universities from Statistics Canada
    ca_universities = fetch_statcan_data()
    
    # 3. Supplement with Wikidata
    for university in universities:
        wikidata_info = get_wikidata_university_info(university['name'])
        if wikidata_info:
            university.update(wikidata_info)
    
    # 4. Add rankings with proper attribution
    add_ranking_data(universities)
    
    return universities
```

### **Phase 2: Official University Websites**

```python
def collect_university_data_phase2(universities):
    """
    Carefully scrape official university websites
    """
    
    for university in universities:
        if check_robots_txt(university['website']):
            # Scrape allowed data points
            scraped_data = scrape_university_safely(university['website'])
            university.update(scraped_data)
            
            # Always add proper attribution
            university['data_sources'].append({
                'source': 'official_website',
                'url': university['website'],
                'scraped_at': datetime.now().isoformat()
            })
        
        # Rate limiting
        time.sleep(3)
    
    return universities
```

### **Phase 3: Commercial APIs (Optional)**

```python
def collect_university_data_phase3(universities):
    """
    Use commercial APIs for additional data
    """
    
    for university in universities:
        # Get additional data from commercial sources
        if has_clearbit_access():
            clearbit_data = get_clearbit_university_data(university['domain'])
            if clearbit_data:
                university.update(clearbit_data)
    
    return universities
```

---

## ⚖️ **Legal Compliance Checklist**

### **Before Implementing**

- [ ] **Review Terms of Service** for each data source
- [ ] **Check robots.txt** for scraping permissions
- [ ] **Implement rate limiting** (minimum 1-2 seconds between requests)
- [ ] **Add proper User-Agent** with contact information
- [ ] **Plan attribution strategy** for all data sources
- [ ] **Document data sources** for transparency

### **During Collection**

- [ ] **Respect robots.txt** directives
- [ ] **Monitor request rates** to avoid overloading servers
- [ ] **Log all data sources** for proper attribution
- [ ] **Store original URLs** for reference
- [ ] **Handle errors gracefully** (don't retry aggressively)

### **After Collection**

- [ ] **Add source attribution** to your website
- [ ] **Provide data source links** where appropriate
- [ ] **Update data regularly** to maintain accuracy
- [ ] **Respond to takedown requests** promptly if received

---

## 📊 **Recommended Implementation Order**

### **Priority 1: Government Data (100% Legal)**
1. IPEDS for US universities
2. Statistics Canada for Canadian universities  
3. HESA for UK universities
4. Wikidata for all countries

### **Priority 2: Official Rankings (With Attribution)**
1. Times Higher Education (factual rankings only)
2. QS World University Rankings (factual rankings only)
3. ARWU Shanghai Rankings (factual rankings only)

### **Priority 3: Official University Websites (Careful Scraping)**
1. Basic contact information
2. Published statistics
3. Department/faculty listings
4. Publicly available enrollment numbers

### **Priority 4: Commercial APIs (If Budget Allows)**
1. Clearbit for additional company data
2. SemRush for website analytics
3. LinkedIn Company API for company information

---

## 🚨 **Red Flags to Avoid**

- **Never scrape**: Student directories, faculty personal information, or login-protected content
- **Never copy**: Large amounts of text, images, or proprietary analysis
- **Never ignore**: robots.txt, terms of service, or rate limiting
- **Never claim**: Data ownership when using third-party sources

---

## 📞 **Support & Resources**

### **Legal Resources**
- **EFF (Electronic Frontier Foundation)**: https://www.eff.org/issues/coders/reverse-engineering-faq
- **US Copyright Fair Use**: https://www.copyright.gov/fair-use/
- **Creative Commons**: https://creativecommons.org/about/

### **Technical Resources**
- **Scrapy Framework**: https://scrapy.org/ (for ethical scraping)
- **Requests-HTML**: https://github.com/psf/requests-html
- **Beautiful Soup**: https://www.crummy.com/software/BeautifulSoup/

### **API Documentation**
- **IPEDS API**: https://educationdata.urban.org/documentation/
- **Wikidata SPARQL**: https://query.wikidata.org/
- **OpenStreetMap Overpass**: https://wiki.openstreetmap.org/wiki/Overpass_API

---

**Remember**: When in doubt, err on the side of caution and seek legal advice for specific use cases. Always prioritize official, open, and government data sources over scraping when possible.

*Last updated: January 2025*  
*Version: 1.0.0*  
*FacultyFinder University Data Collection Guide* 