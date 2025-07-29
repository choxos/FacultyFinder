#!/usr/bin/env python3
"""
Automated Publication Update System for FacultyFinder
====================================================

This script automatically:
1. Searches PubMed for faculty publications using Entrez API
2. Tracks citations using OpenCitations API
3. Processes Scimago journal metrics
4. Updates SQLite database with new publications and metrics
5. Runs on a schedule to keep data fresh

Usage:
    python automated_publication_updater.py [options]

Options:
    --setup          : Setup database schema and initial data
    --run-once       : Run update cycle once and exit
    --schedule       : Run continuously with scheduled updates
    --faculty-only   : Update only specific faculty member(s)
    --verbose        : Enable detailed logging

Requirements:
    pip install biopython requests schedule sqlite3 pandas lxml beautifulsoup4
"""

import sqlite3
import requests
import time
import logging
import json
import csv
import re
import schedule
import argparse
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('publication_updater.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration
DATABASE_PATH = "database/facultyfinder_dev.db"
SCIMAGO_DATA_DIR = "data/scimagojr"
ENTREZ_EMAIL = "your.email@example.com"  # Required for NCBI API
ENTREZ_API_KEY = None  # Optional but recommended for higher rate limits

# Rate limiting settings
PUBMED_DELAY = 1.0  # Seconds between PubMed requests
OPENCITATIONS_DELAY = 1.0  # Seconds between OpenCitations requests
MAX_RETRIES = 3

@dataclass
class Publication:
    """Publication data structure"""
    pmid: str
    title: str
    authors: str
    journal: str
    year: int
    volume: str = ""
    issue: str = ""
    pages: str = ""
    doi: str = ""
    pmcid: str = ""
    abstract: str = ""
    keywords: str = ""
    journal_issn: str = ""
    citation_count: int = 0
    last_citation_update: datetime = None

@dataclass
class JournalMetrics:
    """Journal metrics from Scimago"""
    issn: str
    title: str
    sjr: float
    h_index: int
    total_docs: int
    quartile: str
    category: str
    year: int

class DatabaseManager:
    """Handles database operations"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.ensure_database_exists()
    
    def ensure_database_exists(self):
        """Create database and tables if they don't exist"""
        if not os.path.exists(os.path.dirname(self.db_path)):
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def setup_schema(self):
        """Setup enhanced database schema for publications and metrics"""
        conn = self.get_connection()
        try:
            # Enhanced publications table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS publications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    professor_id INTEGER,
                    pmid TEXT UNIQUE,
                    title TEXT NOT NULL,
                    authors TEXT,
                    journal TEXT,
                    year INTEGER,
                    volume TEXT,
                    issue TEXT,
                    pages TEXT,
                    doi TEXT,
                    pmcid TEXT,
                    abstract TEXT,
                    keywords TEXT,
                    journal_issn TEXT,
                    citation_count INTEGER DEFAULT 0,
                    last_citation_update DATETIME,
                    journal_rank INTEGER,
                    journal_sjr REAL,
                    journal_quartile TEXT,
                    journal_h_index INTEGER,
                    scimago_year INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (professor_id) REFERENCES professors (id)
                )
            """)
            
            # Journal metrics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS journal_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    issn TEXT,
                    title TEXT,
                    sjr REAL,
                    h_index INTEGER,
                    total_docs INTEGER,
                    quartile TEXT,
                    category TEXT,
                    year INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(issn, year)
                )
            """)
            
            # Citations tracking table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS citations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    publication_id INTEGER,
                    citing_pmid TEXT,
                    citing_doi TEXT,
                    citation_year INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (publication_id) REFERENCES publications (id)
                )
            """)
            
            # Update log table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS publication_update_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    update_type TEXT, -- 'pubmed', 'citations', 'scimago'
                    professor_id INTEGER,
                    publications_added INTEGER DEFAULT 0,
                    publications_updated INTEGER DEFAULT 0,
                    citations_added INTEGER DEFAULT 0,
                    errors_count INTEGER DEFAULT 0,
                    execution_time REAL,
                    started_at DATETIME,
                    completed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'completed', -- 'completed', 'failed', 'partial'
                    error_message TEXT
                )
            """)
            
            # Collaboration networks
            conn.execute("""
                CREATE TABLE IF NOT EXISTS collaboration_networks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    professor1_id INTEGER,
                    professor2_id INTEGER,
                    collaboration_count INTEGER DEFAULT 1,
                    first_collaboration_year INTEGER,
                    last_collaboration_year INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (professor1_id) REFERENCES professors (id),
                    FOREIGN KEY (professor2_id) REFERENCES professors (id),
                    UNIQUE(professor1_id, professor2_id)
                )
            """)
            
            # Create indexes for performance
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_publications_pmid ON publications(pmid)",
                "CREATE INDEX IF NOT EXISTS idx_publications_professor ON publications(professor_id)",
                "CREATE INDEX IF NOT EXISTS idx_publications_year ON publications(year)",
                "CREATE INDEX IF NOT EXISTS idx_publications_journal ON publications(journal)",
                "CREATE INDEX IF NOT EXISTS idx_publications_issn ON publications(journal_issn)",
                "CREATE INDEX IF NOT EXISTS idx_journal_metrics_issn ON journal_metrics(issn)",
                "CREATE INDEX IF NOT EXISTS idx_journal_metrics_year ON journal_metrics(year)",
                "CREATE INDEX IF NOT EXISTS idx_citations_publication ON citations(publication_id)",
                "CREATE INDEX IF NOT EXISTS idx_citations_pmid ON citations(citing_pmid)"
            ]
            
            for index_sql in indexes:
                conn.execute(index_sql)
            
            conn.commit()
            logger.info("Database schema setup completed")
            
        except Exception as e:
            logger.error(f"Error setting up database schema: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_faculty_list(self) -> List[Dict]:
        """Get list of faculty members for publication updates"""
        conn = self.get_connection()
        try:
            cursor = conn.execute("""
                SELECT id, name, research_areas, last_publication_update
                FROM professors 
                WHERE name IS NOT NULL AND name != ''
                ORDER BY 
                    CASE WHEN last_publication_update IS NULL THEN 0 ELSE 1 END,
                    last_publication_update ASC
            """)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def save_publications(self, professor_id: int, publications: List[Publication]) -> Tuple[int, int]:
        """Save publications to database, return (added, updated) counts"""
        conn = self.get_connection()
        added_count = 0
        updated_count = 0
        
        try:
            for pub in publications:
                # Check if publication exists
                cursor = conn.execute(
                    "SELECT id, updated_at FROM publications WHERE pmid = ?",
                    (pub.pmid,)
                )
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing publication
                    conn.execute("""
                        UPDATE publications SET 
                            title = ?, authors = ?, journal = ?, year = ?,
                            volume = ?, issue = ?, pages = ?, doi = ?, pmcid = ?,
                            abstract = ?, keywords = ?, journal_issn = ?,
                            citation_count = ?, last_citation_update = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE pmid = ?
                    """, (
                        pub.title, pub.authors, pub.journal, pub.year,
                        pub.volume, pub.issue, pub.pages, pub.doi, pub.pmcid,
                        pub.abstract, pub.keywords, pub.journal_issn,
                        pub.citation_count, pub.last_citation_update, pub.pmid
                    ))
                    updated_count += 1
                else:
                    # Insert new publication
                    conn.execute("""
                        INSERT INTO publications (
                            professor_id, pmid, title, authors, journal, year,
                            volume, issue, pages, doi, pmcid, abstract, keywords,
                            journal_issn, citation_count, last_citation_update
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        professor_id, pub.pmid, pub.title, pub.authors, pub.journal, pub.year,
                        pub.volume, pub.issue, pub.pages, pub.doi, pub.pmcid,
                        pub.abstract, pub.keywords, pub.journal_issn,
                        pub.citation_count, pub.last_citation_update
                    ))
                    added_count += 1
            
            # Update faculty member's last update timestamp
            conn.execute(
                "UPDATE professors SET last_publication_update = CURRENT_TIMESTAMP WHERE id = ?",
                (professor_id,)
            )
            
            conn.commit()
            return added_count, updated_count
            
        except Exception as e:
            logger.error(f"Error saving publications: {e}")
            conn.rollback()
            return 0, 0
        finally:
            conn.close()

class PubMedSearcher:
    """Handles PubMed API interactions using Entrez"""
    
    def __init__(self, email: str, api_key: Optional[str] = None):
        try:
            from Bio import Entrez
            self.Entrez = Entrez
            self.Entrez.email = email
            if api_key:
                self.Entrez.api_key = api_key
        except ImportError:
            logger.error("Biopython not installed. Run: pip install biopython")
            sys.exit(1)
    
    def search_faculty_publications(self, faculty_name: str, research_areas: str = "") -> List[Publication]:
        """Search PubMed for faculty publications"""
        publications = []
        
        try:
            # Build search query
            search_terms = self._build_search_query(faculty_name, research_areas)
            
            # Search PubMed
            handle = self.Entrez.esearch(
                db="pubmed",
                term=search_terms,
                retmax=200,  # Maximum results
                sort="pub_date",
                datetype="pdat",
                mindate="2020",  # Last 5 years
                maxdate=datetime.now().year
            )
            search_results = self.Entrez.read(handle)
            handle.close()
            
            pmids = search_results["IdList"]
            if not pmids:
                logger.info(f"No publications found for {faculty_name}")
                return publications
            
            logger.info(f"Found {len(pmids)} potential publications for {faculty_name}")
            
            # Fetch detailed information
            for i in range(0, len(pmids), 20):  # Process in batches of 20
                batch_pmids = pmids[i:i+20]
                batch_publications = self._fetch_publication_details(batch_pmids)
                
                # Filter publications by author name match
                for pub in batch_publications:
                    if self._is_author_match(faculty_name, pub.authors):
                        publications.append(pub)
                
                # Rate limiting
                time.sleep(PUBMED_DELAY)
            
            logger.info(f"Filtered to {len(publications)} confirmed publications for {faculty_name}")
            return publications
            
        except Exception as e:
            logger.error(f"Error searching PubMed for {faculty_name}: {e}")
            return publications
    
    def _build_search_query(self, faculty_name: str, research_areas: str) -> str:
        """Build optimized PubMed search query"""
        # Extract last name and first initial
        name_parts = faculty_name.strip().split()
        if len(name_parts) >= 2:
            last_name = name_parts[-1]
            first_initial = name_parts[0][0]
            author_query = f'"{last_name} {first_initial}"[Author]'
        else:
            author_query = f'"{faculty_name}"[Author]'
        
        # Add research area keywords if available
        research_keywords = []
        if research_areas:
            # Extract keywords from research areas
            areas = re.split(r'[;,]', research_areas)
            for area in areas[:3]:  # Limit to 3 main areas
                area = area.strip()
                if area and len(area) > 3:
                    research_keywords.append(f'"{area}"[MeSH Terms] OR "{area}"[Title/Abstract]')
        
        # Combine queries
        if research_keywords:
            query = f"({author_query}) AND ({' OR '.join(research_keywords)})"
        else:
            query = author_query
        
        return query
    
    def _fetch_publication_details(self, pmids: List[str]) -> List[Publication]:
        """Fetch detailed publication information"""
        publications = []
        
        try:
            handle = self.Entrez.efetch(
                db="pubmed",
                id=",".join(pmids),
                rettype="xml",
                retmode="text"
            )
            records = self.Entrez.read(handle)
            handle.close()
            
            for record in records['PubmedArticle']:
                try:
                    pub = self._parse_pubmed_record(record)
                    if pub:
                        publications.append(pub)
                except Exception as e:
                    logger.warning(f"Error parsing PubMed record: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error fetching publication details: {e}")
        
        return publications
    
    def _parse_pubmed_record(self, record) -> Optional[Publication]:
        """Parse PubMed XML record into Publication object"""
        try:
            article = record['MedlineCitation']['Article']
            medline = record['MedlineCitation']
            
            # Basic information
            pmid = str(medline['PMID'])
            title = article.get('ArticleTitle', '')
            
            # Authors
            authors = []
            if 'AuthorList' in article:
                for author in article['AuthorList']:
                    if 'LastName' in author and 'Initials' in author:
                        authors.append(f"{author['LastName']} {author['Initials']}")
            authors_str = "; ".join(authors)
            
            # Journal information
            journal = article.get('Journal', {}).get('Title', '')
            
            # Publication date
            pub_date = article.get('Journal', {}).get('JournalIssue', {}).get('PubDate', {})
            year = int(pub_date.get('Year', 0)) if pub_date.get('Year') else 0
            
            # Volume, Issue, Pages
            journal_issue = article.get('Journal', {}).get('JournalIssue', {})
            volume = journal_issue.get('Volume', '')
            issue = journal_issue.get('Issue', '')
            
            pagination = article.get('Pagination', {})
            pages = pagination.get('MedlinePgn', '')
            
            # DOI
            doi = ""
            if 'ELocationID' in article:
                for elocation in article['ELocationID']:
                    if elocation.attributes.get('EIdType') == 'doi':
                        doi = str(elocation)
                        break
            
            # PMC ID
            pmcid = ""
            if 'OtherID' in medline:
                for other_id in medline['OtherID']:
                    if str(other_id).startswith('PMC'):
                        pmcid = str(other_id)
                        break
            
            # Abstract
            abstract = ""
            if 'Abstract' in article and 'AbstractText' in article['Abstract']:
                abstract_parts = article['Abstract']['AbstractText']
                if isinstance(abstract_parts, list):
                    abstract = " ".join(str(part) for part in abstract_parts)
                else:
                    abstract = str(abstract_parts)
            
            # Keywords
            keywords = ""
            if 'KeywordList' in medline:
                keyword_list = medline['KeywordList'][0] if medline['KeywordList'] else []
                keywords = "; ".join(str(kw) for kw in keyword_list)
            
            # Journal ISSN
            journal_issn = article.get('Journal', {}).get('ISSN', '')
            if journal_issn:
                journal_issn = str(journal_issn)
            
            return Publication(
                pmid=pmid,
                title=title,
                authors=authors_str,
                journal=journal,
                year=year,
                volume=volume,
                issue=issue,
                pages=pages,
                doi=doi,
                pmcid=pmcid,
                abstract=abstract,
                keywords=keywords,
                journal_issn=journal_issn
            )
            
        except Exception as e:
            logger.error(f"Error parsing PubMed record: {e}")
            return None
    
    def _is_author_match(self, faculty_name: str, authors_str: str) -> bool:
        """Check if faculty name matches any author in the publication"""
        if not authors_str:
            return False
        
        # Normalize names
        faculty_parts = faculty_name.lower().split()
        faculty_last = faculty_parts[-1] if faculty_parts else ""
        faculty_first = faculty_parts[0] if faculty_parts else ""
        
        authors = authors_str.lower()
        
        # Check for last name and first initial
        if len(faculty_first) > 0:
            pattern1 = f"{faculty_last} {faculty_first[0]}"
            pattern2 = f"{faculty_first[0]} {faculty_last}"
            if pattern1 in authors or pattern2 in authors:
                return True
        
        # Check for full last name
        if faculty_last in authors:
            return True
        
        return False

class OpenCitationsAPI:
    """Handles OpenCitations API for citation tracking"""
    
    def __init__(self):
        self.base_url = "https://opencitations.net/index/api/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'FacultyFinder Publication Updater (Contact: your.email@example.com)'
        })
    
    def get_citation_count(self, doi: str = "", pmid: str = "") -> int:
        """Get citation count for a publication"""
        try:
            # Prefer DOI over PMID
            if doi:
                identifier = f"doi:{doi}"
            elif pmid:
                identifier = f"pmid:{pmid}"
            else:
                return 0
            
            url = f"{self.base_url}/citations/{identifier}"
            
            response = self.session.get(url, timeout=30)
            if response.status_code == 200:
                citations = response.json()
                return len(citations) if citations else 0
            elif response.status_code == 404:
                # No citations found
                return 0
            else:
                logger.warning(f"OpenCitations API error {response.status_code} for {identifier}")
                return 0
                
        except Exception as e:
            logger.error(f"Error getting citations for {doi or pmid}: {e}")
            return 0
    
    def update_citations_batch(self, publications: List[Tuple[int, str, str]]) -> Dict[int, int]:
        """Update citations for a batch of publications"""
        citation_counts = {}
        
        for pub_id, doi, pmid in publications:
            citation_count = self.get_citation_count(doi, pmid)
            citation_counts[pub_id] = citation_count
            
            # Rate limiting
            time.sleep(OPENCITATIONS_DELAY)
        
        return citation_counts

class ScimagoProcessor:
    """Processes Scimago journal rankings data"""
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.current_year = datetime.now().year
    
    def load_scimago_data(self) -> Dict[str, JournalMetrics]:
        """Load Scimago data from CSV files"""
        journal_metrics = {}
        
        if not self.data_dir.exists():
            logger.warning(f"Scimago data directory not found: {self.data_dir}")
            return journal_metrics
        
        # Process CSV files from most recent year backward
        for year in range(self.current_year, 1999, -1):
            csv_file = self.data_dir / f"scimagojr {year}.csv"
            
            if csv_file.exists():
                try:
                    metrics = self._parse_scimago_csv(csv_file, year)
                    journal_metrics.update(metrics)
                    logger.info(f"Loaded {len(metrics)} journal metrics from {year}")
                except Exception as e:
                    logger.error(f"Error loading Scimago data for {year}: {e}")
        
        return journal_metrics
    
    def _parse_scimago_csv(self, csv_file: Path, year: int) -> Dict[str, JournalMetrics]:
        """Parse individual Scimago CSV file"""
        metrics = {}
        
        try:
            import pandas as pd
            
            # Read CSV with proper encoding
            df = pd.read_csv(csv_file, encoding='utf-8', sep=';')
            
            for _, row in df.iterrows():
                try:
                    # Extract ISSN (handle multiple ISSNs)
                    issn = str(row.get('Issn', '')).strip()
                    if not issn or issn == 'nan':
                        continue
                    
                    # Take first ISSN if multiple
                    issn = issn.split(',')[0].strip()
                    
                    # Create metrics object
                    metric = JournalMetrics(
                        issn=issn,
                        title=str(row.get('Title', '')).strip(),
                        sjr=float(row.get('SJR', 0)) if pd.notna(row.get('SJR')) else 0.0,
                        h_index=int(row.get('H index', 0)) if pd.notna(row.get('H index')) else 0,
                        total_docs=int(row.get('Total Docs.', 0)) if pd.notna(row.get('Total Docs.')) else 0,
                        quartile=str(row.get('SJR Best Quartile', '')).strip(),
                        category=str(row.get('Categories', '')).strip(),
                        year=year
                    )
                    
                    metrics[issn] = metric
                    
                except Exception as e:
                    logger.warning(f"Error parsing row in {csv_file}: {e}")
                    continue
        
        except ImportError:
            logger.error("Pandas not installed. Run: pip install pandas")
        except Exception as e:
            logger.error(f"Error reading {csv_file}: {e}")
        
        return metrics
    
    def update_publication_metrics(self, db_manager: DatabaseManager, journal_metrics: Dict[str, JournalMetrics]):
        """Update publication records with journal metrics"""
        conn = db_manager.get_connection()
        updated_count = 0
        
        try:
            # Get publications that need metrics updates
            cursor = conn.execute("""
                SELECT id, journal_issn, year 
                FROM publications 
                WHERE journal_issn IS NOT NULL AND journal_issn != ''
                AND (journal_sjr IS NULL OR scimago_year != ?)
            """, (self.current_year,))
            
            publications = cursor.fetchall()
            
            for pub in publications:
                pub_id, issn, year = pub['id'], pub['journal_issn'], pub['year']
                
                # Find best matching metrics (prefer same year, fallback to closest)
                best_metric = self._find_best_metric(issn, year, journal_metrics)
                
                if best_metric:
                    conn.execute("""
                        UPDATE publications SET
                            journal_sjr = ?,
                            journal_h_index = ?,
                            journal_quartile = ?,
                            scimago_year = ?
                        WHERE id = ?
                    """, (
                        best_metric.sjr,
                        best_metric.h_index,
                        best_metric.quartile,
                        best_metric.year,
                        pub_id
                    ))
                    updated_count += 1
            
            conn.commit()
            logger.info(f"Updated {updated_count} publications with Scimago metrics")
            
        except Exception as e:
            logger.error(f"Error updating publication metrics: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def _find_best_metric(self, issn: str, year: int, journal_metrics: Dict[str, JournalMetrics]) -> Optional[JournalMetrics]:
        """Find best matching journal metric for given ISSN and year"""
        if not issn:
            return None
        
        # Try exact ISSN match for same year
        key = f"{issn}_{year}"
        if key in journal_metrics:
            return journal_metrics[key]
        
        # Try ISSN match for closest year
        matches = [m for m in journal_metrics.values() if m.issn == issn]
        if matches:
            # Sort by year distance and return closest
            matches.sort(key=lambda m: abs(m.year - year))
            return matches[0]
        
        return None

class AutomatedPublicationUpdater:
    """Main orchestrator class"""
    
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_manager = DatabaseManager(db_path)
        self.pubmed = PubMedSearcher(ENTREZ_EMAIL, ENTREZ_API_KEY)
        self.opencitations = OpenCitationsAPI()
        self.scimago = ScimagoProcessor(SCIMAGO_DATA_DIR)
        
    def setup_system(self):
        """Setup database schema and initial data"""
        logger.info("Setting up automated publication update system...")
        
        # Setup database schema
        self.db_manager.setup_schema()
        
        # Load and process Scimago data
        logger.info("Loading Scimago journal metrics...")
        journal_metrics = self.scimago.load_scimago_data()
        
        if journal_metrics:
            # Save journal metrics to database
            self._save_journal_metrics(journal_metrics)
            logger.info(f"Loaded {len(journal_metrics)} journal metrics")
        
        logger.info("System setup completed successfully!")
    
    def run_full_update(self):
        """Run complete publication update cycle"""
        start_time = time.time()
        logger.info("Starting full publication update cycle...")
        
        try:
            # Get faculty list
            faculty_list = self.db_manager.get_faculty_list()
            logger.info(f"Found {len(faculty_list)} faculty members to update")
            
            total_added = 0
            total_updated = 0
            total_errors = 0
            
            for faculty in faculty_list:
                try:
                    logger.info(f"Processing publications for {faculty['name']}")
                    
                    # Search PubMed for publications
                    publications = self.pubmed.search_faculty_publications(
                        faculty['name'], 
                        faculty.get('research_areas', '')
                    )
                    
                    if publications:
                        # Update citation counts
                        self._update_citation_counts(publications)
                        
                        # Save to database
                        added, updated = self.db_manager.save_publications(
                            faculty['id'], publications
                        )
                        
                        total_added += added
                        total_updated += updated
                        
                        logger.info(f"Processed {faculty['name']}: {added} new, {updated} updated")
                    
                except Exception as e:
                    logger.error(f"Error processing {faculty['name']}: {e}")
                    total_errors += 1
            
            # Update journal metrics
            self._update_journal_metrics()
            
            # Log summary
            execution_time = time.time() - start_time
            self._log_update_cycle('full_update', total_added, total_updated, total_errors, execution_time)
            
            logger.info(f"Update cycle completed: {total_added} added, {total_updated} updated, {total_errors} errors")
            
        except Exception as e:
            logger.error(f"Error in full update cycle: {e}")
    
    def run_incremental_update(self):
        """Run incremental update for recently updated publications"""
        logger.info("Starting incremental update...")
        
        # Update citation counts for recent publications
        self._update_recent_citations()
        
        # Update any new journal metrics
        self._update_journal_metrics()
        
        logger.info("Incremental update completed")
    
    def run_scheduled_updates(self):
        """Run continuous scheduled updates"""
        logger.info("Starting scheduled publication updates...")
        
        # Schedule different types of updates
        schedule.every().monday.at("02:00").do(self.run_full_update)
        schedule.every().day.at("06:00").do(self.run_incremental_update)
        schedule.every(6).hours.do(self._update_recent_citations)
        
        logger.info("Scheduled tasks configured:")
        logger.info("- Full update: Every Monday at 2:00 AM")
        logger.info("- Incremental update: Daily at 6:00 AM")
        logger.info("- Citation updates: Every 6 hours")
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                logger.info("Scheduled updates stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in scheduler: {e}")
                time.sleep(300)  # Wait 5 minutes before retrying
    
    def _update_citation_counts(self, publications: List[Publication]):
        """Update citation counts for publications"""
        logger.info(f"Updating citation counts for {len(publications)} publications...")
        
        for pub in publications:
            try:
                citation_count = self.opencitations.get_citation_count(pub.doi, pub.pmid)
                pub.citation_count = citation_count
                pub.last_citation_update = datetime.now()
                
                time.sleep(OPENCITATIONS_DELAY)
                
            except Exception as e:
                logger.warning(f"Error updating citations for {pub.pmid}: {e}")
    
    def _update_recent_citations(self):
        """Update citations for publications updated in last week"""
        conn = self.db_manager.get_connection()
        
        try:
            # Get publications that need citation updates
            one_week_ago = datetime.now() - timedelta(days=7)
            cursor = conn.execute("""
                SELECT id, doi, pmid 
                FROM publications 
                WHERE last_citation_update IS NULL 
                   OR last_citation_update < ?
                LIMIT 100
            """, (one_week_ago,))
            
            publications = cursor.fetchall()
            
            if publications:
                logger.info(f"Updating citations for {len(publications)} publications")
                
                for pub in publications:
                    citation_count = self.opencitations.get_citation_count(
                        pub['doi'], pub['pmid']
                    )
                    
                    conn.execute("""
                        UPDATE publications 
                        SET citation_count = ?, last_citation_update = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (citation_count, pub['id']))
                    
                    time.sleep(OPENCITATIONS_DELAY)
                
                conn.commit()
                logger.info("Citation updates completed")
        
        except Exception as e:
            logger.error(f"Error updating recent citations: {e}")
        finally:
            conn.close()
    
    def _update_journal_metrics(self):
        """Update journal metrics from Scimago data"""
        logger.info("Updating journal metrics...")
        
        journal_metrics = self.scimago.load_scimago_data()
        if journal_metrics:
            self.scimago.update_publication_metrics(self.db_manager, journal_metrics)
    
    def _save_journal_metrics(self, journal_metrics: Dict[str, JournalMetrics]):
        """Save journal metrics to database"""
        conn = self.db_manager.get_connection()
        
        try:
            for metric in journal_metrics.values():
                conn.execute("""
                    INSERT OR REPLACE INTO journal_metrics 
                    (issn, title, sjr, h_index, total_docs, quartile, category, year)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metric.issn, metric.title, metric.sjr, metric.h_index,
                    metric.total_docs, metric.quartile, metric.category, metric.year
                ))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error saving journal metrics: {e}")
        finally:
            conn.close()
    
    def _log_update_cycle(self, update_type: str, added: int, updated: int, errors: int, execution_time: float):
        """Log update cycle to database"""
        conn = self.db_manager.get_connection()
        
        try:
            conn.execute("""
                INSERT INTO publication_update_log 
                (update_type, publications_added, publications_updated, errors_count, execution_time, started_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (update_type, added, updated, errors, execution_time, datetime.now()))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error logging update cycle: {e}")
        finally:
            conn.close()

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Automated Publication Update System')
    parser.add_argument('--setup', action='store_true', help='Setup database schema and initial data')
    parser.add_argument('--run-once', action='store_true', help='Run update cycle once and exit')
    parser.add_argument('--schedule', action='store_true', help='Run continuously with scheduled updates')
    parser.add_argument('--incremental', action='store_true', help='Run incremental update only')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create updater instance
    updater = AutomatedPublicationUpdater()
    
    if args.setup:
        updater.setup_system()
    elif args.run_once:
        updater.run_full_update()
    elif args.incremental:
        updater.run_incremental_update()
    elif args.schedule:
        updater.run_scheduled_updates()
    else:
        # Default: show help
        parser.print_help()
        print("\nExample usage:")
        print("  python automated_publication_updater.py --setup")
        print("  python automated_publication_updater.py --run-once")
        print("  python automated_publication_updater.py --schedule")

if __name__ == "__main__":
    main() 