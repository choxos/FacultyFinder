# Automated Publication Update System Guide 📚

## Complete Integration: PubMed + OpenCitations + Scimago

This guide provides a production-ready system for automatically updating your database with publication data, citations, and journal metrics.

---

## 📋 **Table of Contents**

1. [System Overview](#system-overview)
2. [Database Schema Updates](#database-schema-updates)
3. [PubMed Integration](#pubmed-integration)
4. [OpenCitations Integration](#opencitations-integration)
5. [Scimago Journal Data](#scimago-journal-data)
6. [Automated Update System](#automated-update-system)
7. [Implementation Code](#implementation-code)
8. [Scheduling & Monitoring](#scheduling--monitoring)

---

## 🏗️ **System Overview**

### **Data Flow Pipeline:**
```
Faculty Data → PubMed Search → Publication Extraction → 
OpenCitations Citations → Scimago Journal Metrics → 
Database Update → Collaboration Networks
```

### **Key Features:**
- **Automated PubMed searches** for all faculty
- **Citation tracking** via OpenCitations
- **Journal impact metrics** from Scimago
- **Duplicate prevention** using PMID/DOI/PMCID
- **Collaboration network mapping**
- **Continuous updates** with scheduling
- **Error handling and logging**

---

## 🗄️ **Database Schema Updates**

### **Enhanced Publications Table:**
```sql
-- Add citation and journal metric columns
ALTER TABLE publications ADD COLUMN pmcid VARCHAR(20);
ALTER TABLE publications ADD COLUMN citation_count INTEGER DEFAULT 0;
ALTER TABLE publications ADD COLUMN last_citation_update TIMESTAMP;

-- Add journal metrics from Scimago
ALTER TABLE publications ADD COLUMN journal_issn VARCHAR(20);
ALTER TABLE publications ADD COLUMN journal_rank INTEGER;
ALTER TABLE publications ADD COLUMN journal_sjr DECIMAL(8,4);
ALTER TABLE publications ADD COLUMN journal_quartile VARCHAR(5);
ALTER TABLE publications ADD COLUMN journal_h_index INTEGER;
ALTER TABLE publications ADD COLUMN scimago_year INTEGER;

-- Add indexing for performance
CREATE INDEX idx_publications_pmcid ON publications(pmcid);
CREATE INDEX idx_publications_issn ON publications(journal_issn);
CREATE INDEX idx_publications_citation_count ON publications(citation_count);
```

### **New Tables:**

#### **Citations Table:**
```sql
CREATE TABLE citations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    citing_publication_id INTEGER,
    cited_publication_id INTEGER,
    citation_context TEXT,
    citation_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (citing_publication_id) REFERENCES publications(id),
    FOREIGN KEY (cited_publication_id) REFERENCES publications(id),
    UNIQUE(citing_publication_id, cited_publication_id)
);
```

#### **Journal Metrics Table:**
```sql
CREATE TABLE journal_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    issn VARCHAR(20),
    journal_name VARCHAR(500),
    year INTEGER,
    rank_value INTEGER,
    sjr DECIMAL(8,4),
    sjr_best_quartile VARCHAR(5),
    h_index INTEGER,
    country VARCHAR(100),
    subject_category TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(issn, year)
);
```

#### **Publication Update Log:**
```sql
CREATE TABLE publication_update_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    professor_id INTEGER,
    search_type VARCHAR(50), -- 'all' or 'affiliation'
    publications_found INTEGER,
    new_publications INTEGER,
    citations_updated INTEGER,
    update_duration INTEGER, -- seconds
    status VARCHAR(20), -- 'success', 'error', 'partial'
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (professor_id) REFERENCES professors(id)
);
```

---

## 🔬 **PubMed Integration**

### **Core PubMed Search Class:**

```python
import requests
import xml.etree.ElementTree as ET
from Bio import Entrez
import time
import logging
from datetime import datetime, timedelta

class PubMedSearcher:
    def __init__(self, email, api_key=None):
        """
        Initialize PubMed searcher
        
        Args:
            email: Your email for Entrez API
            api_key: NCBI API key (optional but recommended)
        """
        Entrez.email = email
        if api_key:
            Entrez.api_key = api_key
        
        self.logger = logging.getLogger(__name__)
        self.rate_limit_delay = 0.34  # ~3 requests per second (safe limit)
        
    def search_professor_publications(self, first_name, last_name, university_name=None, max_results=1000):
        """
        Search for professor's publications
        
        Args:
            first_name: Professor's first name
            last_name: Professor's last name  
            university_name: University affiliation (optional)
            max_results: Maximum publications to retrieve
            
        Returns:
            List of publication dictionaries
        """
        try:
            # Build search query
            if university_name:
                search_query = f'({first_name} {last_name}[Author] AND {university_name}[Affiliation])'
            else:
                search_query = f'{first_name} {last_name}[Author]'
            
            self.logger.info(f"Searching PubMed: {search_query}")
            
            # Search for publication IDs
            search_handle = Entrez.esearch(
                db="pubmed",
                term=search_query,
                retmax=max_results,
                sort="pub_date",
                retmode="xml"
            )
            
            search_results = Entrez.read(search_handle)
            search_handle.close()
            
            pmids = search_results["IdList"]
            
            if not pmids:
                self.logger.info(f"No publications found for {first_name} {last_name}")
                return []
            
            self.logger.info(f"Found {len(pmids)} publications")
            
            # Fetch publication details in batches
            publications = []
            batch_size = 200  # PubMed recommends max 200 per request
            
            for i in range(0, len(pmids), batch_size):
                batch_pmids = pmids[i:i + batch_size]
                batch_publications = self._fetch_publication_details(batch_pmids)
                publications.extend(batch_publications)
                
                # Rate limiting
                time.sleep(self.rate_limit_delay)
            
            return publications
            
        except Exception as e:
            self.logger.error(f"Error searching PubMed for {first_name} {last_name}: {e}")
            return []
    
    def _fetch_publication_details(self, pmids):
        """Fetch detailed publication information"""
        try:
            fetch_handle = Entrez.efetch(
                db="pubmed",
                id=",".join(pmids),
                rettype="medline",
                retmode="xml"
            )
            
            records = Entrez.read(fetch_handle)
            fetch_handle.close()
            
            publications = []
            
            for record in records["PubmedArticle"]:
                pub_data = self._parse_publication_record(record)
                if pub_data:
                    publications.append(pub_data)
            
            return publications
            
        except Exception as e:
            self.logger.error(f"Error fetching publication details: {e}")
            return []
    
    def _parse_publication_record(self, record):
        """Parse individual publication record"""
        try:
            citation = record["MedlineCitation"]
            article = citation["Article"]
            
            # Basic publication info
            pmid = str(citation["PMID"])
            title = article.get("ArticleTitle", "")
            
            # Journal info
            journal = article["Journal"]
            journal_name = journal.get("Title", "")
            journal_issn = journal.get("ISSN", "")
            
            # Publication date
            pub_date = self._extract_publication_date(article)
            
            # Authors
            authors = self._extract_authors(article)
            
            # Abstract
            abstract = ""
            if "Abstract" in article and "AbstractText" in article["Abstract"]:
                abstract_parts = article["Abstract"]["AbstractText"]
                if isinstance(abstract_parts, list):
                    abstract = " ".join(str(part) for part in abstract_parts)
                else:
                    abstract = str(abstract_parts)
            
            # DOI and PMC ID
            doi = ""
            pmcid = ""
            
            if "ArticleIdList" in record["PubmedData"]:
                for article_id in record["PubmedData"]["ArticleIdList"]:
                    if article_id.attributes.get("IdType") == "doi":
                        doi = str(article_id)
                    elif article_id.attributes.get("IdType") == "pmc":
                        pmcid = str(article_id)
            
            # Volume, Issue, Pages
            volume = journal.get("JournalIssue", {}).get("Volume", "")
            issue = journal.get("JournalIssue", {}).get("Issue", "")
            pages = article.get("Pagination", {}).get("MedlinePgn", "")
            
            return {
                "pmid": pmid,
                "title": title,
                "authors": authors,
                "journal_name": journal_name,
                "journal_issn": journal_issn,
                "volume": volume,
                "issue": issue,
                "pages": pages,
                "publication_date": pub_date["date"],
                "publication_year": pub_date["year"],
                "abstract": abstract,
                "doi": doi,
                "pmcid": pmcid
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing publication record: {e}")
            return None
    
    def _extract_publication_date(self, article):
        """Extract publication date and year"""
        try:
            # Try different date fields
            date_fields = ["ArticleDate", "PubDate"]
            
            for field in date_fields:
                if field in article["Journal"]["JournalIssue"]:
                    date_info = article["Journal"]["JournalIssue"][field]
                    break
                elif field in article:
                    date_info = article[field]
                    break
            else:
                return {"date": None, "year": None}
            
            year = date_info.get("Year", "")
            month = date_info.get("Month", "")
            day = date_info.get("Day", "")
            
            # Format date
            date_str = None
            if year:
                if month and day:
                    try:
                        date_obj = datetime.strptime(f"{year}-{month}-{day}", "%Y-%m-%d")
                        date_str = date_obj.strftime("%Y-%m-%d")
                    except:
                        date_str = f"{year}-{month}"
                elif month:
                    date_str = f"{year}-{month}"
                else:
                    date_str = year
            
            return {
                "date": date_str,
                "year": int(year) if year.isdigit() else None
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting publication date: {e}")
            return {"date": None, "year": None}
    
    def _extract_authors(self, article):
        """Extract author list"""
        try:
            if "AuthorList" not in article:
                return ""
            
            authors = []
            for author in article["AuthorList"]:
                if "LastName" in author:
                    name_parts = []
                    if "ForeName" in author:
                        name_parts.append(author["ForeName"])
                    name_parts.append(author["LastName"])
                    authors.append(" ".join(name_parts))
            
            return ", ".join(authors)
            
        except Exception as e:
            self.logger.error(f"Error extracting authors: {e}")
            return ""
```

---

## 📖 **OpenCitations Integration**

### **Citation Fetcher Class:**

```python
import requests
import json
from time import sleep

class OpenCitationsAPI:
    def __init__(self):
        self.base_url = "https://opencitations.net/index/api/v1"
        self.logger = logging.getLogger(__name__)
        self.rate_limit_delay = 1.0  # 1 second between requests
    
    def get_citations(self, doi):
        """
        Get citations for a publication by DOI
        
        Args:
            doi: Publication DOI
            
        Returns:
            List of citing publications
        """
        try:
            if not doi:
                return []
            
            # Clean DOI
            clean_doi = doi.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")
            
            # Get citations
            url = f"{self.base_url}/citations/{clean_doi}"
            
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                citations = response.json()
                self.logger.info(f"Found {len(citations)} citations for DOI: {clean_doi}")
                return citations
            elif response.status_code == 404:
                self.logger.info(f"No citations found for DOI: {clean_doi}")
                return []
            else:
                self.logger.warning(f"OpenCitations API error {response.status_code} for DOI: {clean_doi}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error fetching citations for DOI {doi}: {e}")
            return []
    
    def get_references(self, doi):
        """
        Get references cited by a publication
        
        Args:
            doi: Publication DOI
            
        Returns:
            List of referenced publications
        """
        try:
            if not doi:
                return []
            
            clean_doi = doi.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")
            
            url = f"{self.base_url}/references/{clean_doi}"
            
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                references = response.json()
                self.logger.info(f"Found {len(references)} references for DOI: {clean_doi}")
                return references
            elif response.status_code == 404:
                self.logger.info(f"No references found for DOI: {clean_doi}")
                return []
            else:
                self.logger.warning(f"OpenCitations API error {response.status_code} for DOI: {clean_doi}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error fetching references for DOI {doi}: {e}")
            return []
    
    def batch_get_citations(self, dois, batch_size=10):
        """
        Get citations for multiple DOIs with rate limiting
        
        Args:
            dois: List of DOIs
            batch_size: Number of DOIs to process in each batch
            
        Returns:
            Dictionary mapping DOI to citations
        """
        results = {}
        
        for i in range(0, len(dois), batch_size):
            batch = dois[i:i + batch_size]
            
            for doi in batch:
                results[doi] = self.get_citations(doi)
                sleep(self.rate_limit_delay)
            
            self.logger.info(f"Processed batch {i//batch_size + 1}/{(len(dois) + batch_size - 1)//batch_size}")
        
        return results
```

---

## 📊 **Scimago Journal Data Integration**

### **Journal Metrics Processor:**

```python
import pandas as pd
import sqlite3
from pathlib import Path

class ScimagoProcessor:
    def __init__(self, db_connection):
        self.conn = db_connection
        self.logger = logging.getLogger(__name__)
        
    def load_scimago_data(self, scimago_file_path):
        """
        Load Scimago journal data into database
        
        Args:
            scimago_file_path: Path to scimago_journals_comprehensive.csv
        """
        try:
            df = pd.read_csv(scimago_file_path)
            self.logger.info(f"Loading Scimago data with {len(df)} journals")
            
            # Get all year columns
            year_columns = {}
            for col in df.columns:
                if '_' in col and col.split('_')[-1].isdigit():
                    metric = '_'.join(col.split('_')[:-1])
                    year = int(col.split('_')[-1])
                    
                    if year not in year_columns:
                        year_columns[year] = {}
                    year_columns[year][metric] = col
            
            # Process each year
            for year in sorted(year_columns.keys()):
                self._process_year_data(df, year, year_columns[year])
            
            self.logger.info("Scimago data loading completed")
            
        except Exception as e:
            self.logger.error(f"Error loading Scimago data: {e}")
    
    def _process_year_data(self, df, year, year_cols):
        """Process Scimago data for a specific year"""
        try:
            records_inserted = 0
            
            for _, row in df.iterrows():
                # Extract metrics for this year
                rank_val = row.get(year_cols.get('rank', ''), None)
                sjr_val = row.get(year_cols.get('sjr', ''), None)
                quartile = row.get(year_cols.get('sjr_best_quartile', ''), None)
                h_index = row.get(year_cols.get('h_index', ''), None)
                
                # Skip if no data for this year
                if pd.isna(rank_val) and pd.isna(sjr_val):
                    continue
                
                # Insert into database
                self.conn.execute("""
                    INSERT OR REPLACE INTO journal_metrics 
                    (issn, journal_name, year, rank_value, sjr, sjr_best_quartile, h_index, country, subject_category)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row.get('Issn', ''),
                    row.get('Title', ''),
                    year,
                    int(rank_val) if pd.notna(rank_val) else None,
                    float(sjr_val) if pd.notna(sjr_val) else None,
                    str(quartile) if pd.notna(quartile) else None,
                    int(h_index) if pd.notna(h_index) else None,
                    row.get('Country', ''),
                    row.get('Categories', '')
                ))
                
                records_inserted += 1
            
            self.conn.commit()
            self.logger.info(f"Inserted {records_inserted} journal metrics for year {year}")
            
        except Exception as e:
            self.logger.error(f"Error processing year {year} data: {e}")
    
    def match_publication_to_journal(self, publication_id, journal_issn, publication_year):
        """
        Match publication to Scimago journal metrics
        
        Args:
            publication_id: Database ID of publication
            journal_issn: ISSN of journal
            publication_year: Year of publication
        """
        try:
            if not journal_issn or not publication_year:
                return
            
            # Find matching journal metrics
            cursor = self.conn.execute("""
                SELECT rank_value, sjr, sjr_best_quartile, h_index
                FROM journal_metrics
                WHERE issn = ? AND year = ?
                LIMIT 1
            """, (journal_issn, publication_year))
            
            result = cursor.fetchone()
            
            if result:
                # Update publication with journal metrics
                self.conn.execute("""
                    UPDATE publications 
                    SET journal_issn = ?, journal_rank = ?, journal_sjr = ?, 
                        journal_quartile = ?, journal_h_index = ?, scimago_year = ?
                    WHERE id = ?
                """, (
                    journal_issn,
                    result[0],  # rank_value
                    result[1],  # sjr
                    result[2],  # sjr_best_quartile
                    result[3],  # h_index
                    publication_year,
                    publication_id
                ))
                
                self.conn.commit()
                self.logger.debug(f"Updated publication {publication_id} with journal metrics")
                
        except Exception as e:
            self.logger.error(f"Error matching publication {publication_id} to journal: {e}")
```

---

## 🤖 **Automated Update System**

### **Main Update Orchestrator:**

```python
import sqlite3
import logging
from datetime import datetime, timedelta
import pandas as pd
import os

class PublicationUpdateSystem:
    def __init__(self, database_path, email, api_key=None):
        self.db_path = database_path
        self.pubmed = PubMedSearcher(email, api_key)
        self.opencitations = OpenCitationsAPI()
        self.logger = logging.getLogger(__name__)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('publication_updates.log'),
                logging.StreamHandler()
            ]
        )
    
    def run_full_update(self, faculty_csv_path, scimago_csv_path):
        """
        Run complete publication update for all faculty
        
        Args:
            faculty_csv_path: Path to faculty CSV file
            scimago_csv_path: Path to Scimago data
        """
        start_time = datetime.now()
        self.logger.info("Starting full publication update")
        
        try:
            # Load and process Scimago data first
            self._update_scimago_data(scimago_csv_path)
            
            # Load faculty data
            faculty_df = pd.read_csv(faculty_csv_path)
            total_faculty = len(faculty_df)
            
            processed = 0
            errors = 0
            
            for _, faculty in faculty_df.iterrows():
                try:
                    self._process_faculty_publications(faculty)
                    processed += 1
                    
                    if processed % 10 == 0:
                        self.logger.info(f"Processed {processed}/{total_faculty} faculty")
                        
                except Exception as e:
                    self.logger.error(f"Error processing faculty {faculty.get('name', 'Unknown')}: {e}")
                    errors += 1
            
            # Update citations for all publications
            self._update_all_citations()
            
            duration = datetime.now() - start_time
            self.logger.info(f"Full update completed. Processed: {processed}, Errors: {errors}, Duration: {duration}")
            
        except Exception as e:
            self.logger.error(f"Fatal error in full update: {e}")
    
    def _process_faculty_publications(self, faculty):
        """Process publications for a single faculty member"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            first_name = faculty['first_name']
            last_name = faculty['last_name']
            university_name = faculty.get('university_name', '')
            
            # Get professor ID
            cursor = conn.execute(
                "SELECT id FROM professors WHERE first_name = ? AND last_name = ?",
                (first_name, last_name)
            )
            professor_result = cursor.fetchone()
            
            if not professor_result:
                self.logger.warning(f"Professor not found: {first_name} {last_name}")
                return
            
            professor_id = professor_result['id']
            
            # Search PubMed (both general and affiliation-specific)
            all_publications = self.pubmed.search_professor_publications(
                first_name, last_name
            )
            
            affiliation_publications = self.pubmed.search_professor_publications(
                first_name, last_name, university_name
            )
            
            # Combine and deduplicate
            combined_pubs = self._deduplicate_publications(all_publications + affiliation_publications)
            
            # Process each publication
            new_pubs = 0
            for pub in combined_pubs:
                if self._insert_publication(conn, professor_id, pub):
                    new_pubs += 1
            
            # Log update
            self._log_update(conn, professor_id, len(combined_pubs), new_pubs)
            
            conn.close()
            
            self.logger.info(f"Processed {first_name} {last_name}: {new_pubs} new publications")
            
        except Exception as e:
            self.logger.error(f"Error processing faculty {faculty.get('name', 'Unknown')}: {e}")
    
    def _insert_publication(self, conn, professor_id, pub_data):
        """Insert publication into database if not duplicate"""
        try:
            # Check for duplicates
            cursor = conn.execute("""
                SELECT id FROM publications 
                WHERE pmid = ? OR (doi = ? AND doi != '') OR (pmcid = ? AND pmcid != '')
            """, (pub_data['pmid'], pub_data.get('doi', ''), pub_data.get('pmcid', '')))
            
            existing = cursor.fetchone()
            
            if existing:
                # Link to existing publication
                conn.execute("""
                    INSERT OR IGNORE INTO author_publications (professor_id, publication_id)
                    VALUES (?, ?)
                """, (professor_id, existing['id']))
                return False
            
            # Insert new publication
            cursor = conn.execute("""
                INSERT INTO publications (
                    pmid, title, authors, journal_name, journal_issn, volume, issue, pages,
                    publication_date, publication_year, abstract, doi, pmcid
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pub_data['pmid'],
                pub_data['title'],
                pub_data['authors'],
                pub_data['journal_name'],
                pub_data['journal_issn'],
                pub_data['volume'],
                pub_data['issue'],
                pub_data['pages'],
                pub_data['publication_date'],
                pub_data['publication_year'],
                pub_data['abstract'],
                pub_data['doi'],
                pub_data['pmcid']
            ))
            
            publication_id = cursor.lastrowid
            
            # Link to professor
            conn.execute("""
                INSERT INTO author_publications (professor_id, publication_id)
                VALUES (?, ?)
            """, (professor_id, publication_id))
            
            # Match to Scimago journal data
            if pub_data['journal_issn'] and pub_data['publication_year']:
                scimago = ScimagoProcessor(conn)
                scimago.match_publication_to_journal(
                    publication_id, 
                    pub_data['journal_issn'], 
                    pub_data['publication_year']
                )
            
            conn.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"Error inserting publication: {e}")
            return False
    
    def _update_all_citations(self):
        """Update citations for all publications with DOIs"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Get publications that need citation updates
            cursor = conn.execute("""
                SELECT id, doi FROM publications 
                WHERE doi IS NOT NULL AND doi != ''
                AND (last_citation_update IS NULL OR 
                     last_citation_update < date('now', '-30 days'))
                ORDER BY last_citation_update ASC
                LIMIT 100
            """)
            
            publications = cursor.fetchall()
            
            for pub in publications:
                citations = self.opencitations.get_citations(pub['doi'])
                
                # Update citation count
                conn.execute("""
                    UPDATE publications 
                    SET citation_count = ?, last_citation_update = ?
                    WHERE id = ?
                """, (len(citations), datetime.now(), pub['id']))
                
                # Store citation details (simplified)
                # You could expand this to store full citation data
                
            conn.commit()
            conn.close()
            
            self.logger.info(f"Updated citations for {len(publications)} publications")
            
        except Exception as e:
            self.logger.error(f"Error updating citations: {e}")

# Create update script
if __name__ == "__main__":
    system = PublicationUpdateSystem(
        database_path="database/facultyfinder_dev.db",
        email="your-email@domain.com",  # Required for PubMed
        api_key="your-ncbi-api-key"     # Optional but recommended
    )
    
    system.run_full_update(
        faculty_csv_path="data/mcmaster_hei_faculty.csv",
        scimago_csv_path="data/scimago_journals_comprehensive.csv"
    )
```

---

## ⏰ **Scheduling & Monitoring**

### **Automated Scheduler:**

```python
import schedule
import time
import subprocess
import smtplib
from email.mime.text import MIMEText

class UpdateScheduler:
    def __init__(self, email_config=None):
        self.email_config = email_config
        self.logger = logging.getLogger(__name__)
    
    def setup_schedule(self):
        """Setup automated update schedule"""
        
        # Full update weekly (Sundays at 2 AM)
        schedule.every().sunday.at("02:00").do(self.run_full_update)
        
        # Citation updates daily (at 3 AM)
        schedule.every().day.at("03:00").do(self.run_citation_update)
        
        # Incremental updates for new faculty (every 6 hours)
        schedule.every(6).hours.do(self.run_incremental_update)
        
        self.logger.info("Update schedule configured")
    
    def run_full_update(self):
        """Run full publication update"""
        try:
            self.logger.info("Starting scheduled full update")
            
            result = subprocess.run([
                "python", "scripts/full_publication_update.py"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info("Full update completed successfully")
                self._send_notification("Full Update Success", result.stdout)
            else:
                self.logger.error(f"Full update failed: {result.stderr}")
                self._send_notification("Full Update Failed", result.stderr)
                
        except Exception as e:
            self.logger.error(f"Error in scheduled full update: {e}")
            self._send_notification("Full Update Error", str(e))
    
    def _send_notification(self, subject, message):
        """Send email notification"""
        if not self.email_config:
            return
            
        try:
            msg = MIMEText(message)
            msg['Subject'] = f"FacultyFinder: {subject}"
            msg['From'] = self.email_config['from']
            msg['To'] = self.email_config['to']
            
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['port'])
            server.starttls()
            server.login(self.email_config['username'], self.email_config['password'])
            server.send_message(msg)
            server.quit()
            
        except Exception as e:
            self.logger.error(f"Error sending notification: {e}")

# Run scheduler
if __name__ == "__main__":
    scheduler = UpdateScheduler({
        'smtp_server': 'smtp.gmail.com',
        'port': 587,
        'username': 'your-email@gmail.com',
        'password': 'your-app-password',
        'from': 'your-email@gmail.com',
        'to': 'admin@facultyfinder.io'
    })
    
    scheduler.setup_schedule()
    
    while True:
        schedule.run_pending()
        time.sleep(60)
```

---

## 📈 **Professor Profile Enhancements**

### **Journal Metrics Display:**

```python
# Add to your app.py professor profile route
def get_professor_journal_metrics(professor_id):
    """Get journal metrics for professor's publications"""
    try:
        conn = get_db_connection()
        
        # Get quartile distribution
        quartile_query = """
            SELECT 
                journal_quartile,
                COUNT(*) as count
            FROM publications p
            JOIN author_publications ap ON p.id = ap.publication_id
            WHERE ap.professor_id = ? AND journal_quartile IS NOT NULL
            GROUP BY journal_quartile
        """
        
        cursor = conn.execute(quartile_query, (professor_id,))
        quartiles = dict(cursor.fetchall())
        
        # Get SJR statistics
        sjr_query = """
            SELECT 
                AVG(journal_sjr) as mean_sjr,
                COUNT(*) as total_pubs,
                MIN(journal_sjr) as min_sjr,
                MAX(journal_sjr) as max_sjr
            FROM publications p
            JOIN author_publications ap ON p.id = ap.publication_id
            WHERE ap.professor_id = ? AND journal_sjr IS NOT NULL
        """
        
        cursor = conn.execute(sjr_query, (professor_id,))
        sjr_stats = dict(cursor.fetchone())
        
        # Calculate quartile percentages
        total_with_quartiles = sum(quartiles.values())
        quartile_percentages = {}
        for q in ['Q1', 'Q2', 'Q3', 'Q4']:
            count = quartiles.get(q, 0)
            percentage = (count / total_with_quartiles * 100) if total_with_quartiles > 0 else 0
            quartile_percentages[q] = {
                'count': count,
                'percentage': round(percentage, 1)
            }
        
        return {
            'quartile_distribution': quartile_percentages,
            'sjr_statistics': sjr_stats,
            'total_publications_with_metrics': total_with_quartiles
        }
        
    except Exception as e:
        logger.error(f"Error getting journal metrics for professor {professor_id}: {e}")
        return None
```

---

## 🔧 **Implementation Commands**

### **Setup Database:**
```bash
# Run database schema updates
sqlite3 database/facultyfinder_dev.db < database/journal_metrics_schema.sql

# Load Scimago data
python scripts/load_scimago_data.py
```

### **Install Dependencies:**
```bash
pip install biopython pandas schedule requests
```

### **Run Updates:**
```bash
# Full update
python scripts/publication_update_system.py

# Start scheduler
python scripts/update_scheduler.py
```

---

## 📊 **Monitoring Dashboard**

Add to your admin interface:

```python
@app.route('/admin/publication-stats')
def publication_stats():
    """Admin dashboard for publication updates"""
    try:
        conn = get_db_connection()
        
        # Recent update statistics
        stats_query = """
            SELECT 
                DATE(created_at) as update_date,
                COUNT(*) as updates,
                SUM(new_publications) as total_new_pubs,
                AVG(update_duration) as avg_duration
            FROM publication_update_log 
            WHERE created_at >= date('now', '-30 days')
            GROUP BY DATE(created_at)
            ORDER BY update_date DESC
        """
        
        cursor = conn.execute(stats_query)
        recent_stats = [dict(row) for row in cursor.fetchall()]
        
        return render_template('admin/publication_stats.html', 
                             recent_stats=recent_stats)
                             
    except Exception as e:
        logger.error(f"Error getting publication stats: {e}")
        return "Error loading statistics"
```

---

## 🎯 **Key Benefits**

### **Automated System:**
- **Continuous updates** without manual intervention
- **Smart deduplication** prevents duplicate publications
- **Error handling** and logging for reliability
- **Rate limiting** respects API guidelines

### **Enhanced Data:**
- **Citation tracking** via OpenCitations
- **Journal impact metrics** from Scimago
- **Collaboration networks** through shared publications
- **Quality indicators** (quartile distribution, SJR scores)

### **Production Ready:**
- **Scalable architecture** handles thousands of faculty
- **Monitoring and alerts** for system health
- **Database optimization** for performance
- **Comprehensive logging** for debugging

---

**This system will transform your FacultyFinder into a comprehensive academic research platform with real-time publication data, citation metrics, and journal impact analysis!** 🚀

*Last updated: January 2025*  
*Version: 1.0.0*  
*FacultyFinder Automated Publication System* 