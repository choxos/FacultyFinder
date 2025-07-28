#!/usr/bin/env python3
"""
FacultyFinder Publication Update System
Automated PubMed search, OpenCitations, and Scimago integration
"""

import sys
import os
import sqlite3
import logging
import pandas as pd
from datetime import datetime, timedelta
import requests
import xml.etree.ElementTree as ET
from Bio import Entrez
import time
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class PubMedSearcher:
    def __init__(self, email, api_key=None):
        """Initialize PubMed searcher with rate limiting"""
        Entrez.email = email
        if api_key:
            Entrez.api_key = api_key
        
        self.logger = logging.getLogger(__name__)
        self.rate_limit_delay = 0.34  # ~3 requests per second
        
    def search_professor_publications(self, first_name, last_name, university_name=None, max_results=1000):
        """Search for professor's publications with both search patterns"""
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
        """Parse individual publication record from PubMed XML"""
        try:
            citation = record["MedlineCitation"]
            article = citation["Article"]
            
            # Basic publication info
            pmid = str(citation["PMID"])
            title = article.get("ArticleTitle", "")
            
            # Journal info
            journal = article["Journal"]
            journal_name = journal.get("Title", "")
            journal_issn = ""
            
            if "ISSN" in journal:
                journal_issn = str(journal["ISSN"])
            
            # Publication date
            pub_date = self._extract_publication_date(article, journal)
            
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
            
            if "PubmedData" in record and "ArticleIdList" in record["PubmedData"]:
                for article_id in record["PubmedData"]["ArticleIdList"]:
                    if hasattr(article_id, 'attributes'):
                        id_type = article_id.attributes.get("IdType", "")
                        if id_type == "doi":
                            doi = str(article_id)
                        elif id_type == "pmc":
                            pmcid = str(article_id)
            
            # Volume, Issue, Pages
            volume = ""
            issue = ""
            if "JournalIssue" in journal:
                volume = journal["JournalIssue"].get("Volume", "")
                issue = journal["JournalIssue"].get("Issue", "")
            
            pages = ""
            if "Pagination" in article and "MedlinePgn" in article["Pagination"]:
                pages = article["Pagination"]["MedlinePgn"]
            
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
    
    def _extract_publication_date(self, article, journal):
        """Extract publication date and year"""
        try:
            year = None
            month = None
            day = None
            
            # Try different date fields
            if "JournalIssue" in journal and "PubDate" in journal["JournalIssue"]:
                pub_date = journal["JournalIssue"]["PubDate"]
                year = pub_date.get("Year", "")
                month = pub_date.get("Month", "")
                day = pub_date.get("Day", "")
            
            # Try ArticleDate if PubDate not found
            if not year and "ArticleDate" in article:
                for date_info in article["ArticleDate"]:
                    year = date_info.get("Year", "")
                    month = date_info.get("Month", "")
                    day = date_info.get("Day", "")
                    if year:
                        break
            
            # Format date
            date_str = None
            if year:
                if month and day:
                    try:
                        # Handle month names
                        if month.isalpha():
                            month_num = {
                                'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
                                'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
                                'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
                            }.get(month, month)
                        else:
                            month_num = month.zfill(2)
                        
                        date_str = f"{year}-{month_num}-{day.zfill(2)}"
                    except:
                        date_str = f"{year}-{month}"
                elif month:
                    date_str = f"{year}-{month}"
                else:
                    date_str = year
            
            return {
                "date": date_str,
                "year": int(year) if year and year.isdigit() else None
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


class OpenCitationsAPI:
    def __init__(self):
        self.base_url = "https://opencitations.net/index/api/v1"
        self.logger = logging.getLogger(__name__)
        self.rate_limit_delay = 1.0  # 1 second between requests
    
    def get_citations(self, doi):
        """Get citations for a publication by DOI"""
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


class ScimagoProcessor:
    def __init__(self, db_connection):
        self.conn = db_connection
        self.logger = logging.getLogger(__name__)
        
    def load_scimago_data(self, scimago_file_path):
        """Load Scimago journal data into database"""
        try:
            if not os.path.exists(scimago_file_path):
                self.logger.error(f"Scimago file not found: {scimago_file_path}")
                return
            
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
        """Match publication to Scimago journal metrics"""
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
        """Run complete publication update for all faculty"""
        start_time = datetime.now()
        self.logger.info("Starting full publication update")
        
        try:
            # Load and process Scimago data first
            self._update_scimago_data(scimago_csv_path)
            
            # Load faculty data
            if not os.path.exists(faculty_csv_path):
                self.logger.error(f"Faculty CSV file not found: {faculty_csv_path}")
                return
            
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
            
            # Update citations for recent publications
            self._update_citations_batch()
            
            duration = datetime.now() - start_time
            self.logger.info(f"Full update completed. Processed: {processed}, Errors: {errors}, Duration: {duration}")
            
        except Exception as e:
            self.logger.error(f"Fatal error in full update: {e}")
    
    def _update_scimago_data(self, scimago_csv_path):
        """Update Scimago journal data in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            scimago = ScimagoProcessor(conn)
            scimago.load_scimago_data(scimago_csv_path)
            conn.close()
            self.logger.info("Scimago data update completed")
        except Exception as e:
            self.logger.error(f"Error updating Scimago data: {e}")
    
    def _process_faculty_publications(self, faculty):
        """Process publications for a single faculty member"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            first_name = faculty['first_name']
            last_name = faculty['last_name']
            university_name = faculty.get('university_name', 'McMaster University')
            
            # Get professor ID
            cursor = conn.execute(
                "SELECT id FROM professors WHERE first_name = ? AND last_name = ?",
                (first_name, last_name)
            )
            professor_result = cursor.fetchone()
            
            if not professor_result:
                self.logger.warning(f"Professor not found: {first_name} {last_name}")
                conn.close()
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
    
    def _deduplicate_publications(self, publications):
        """Remove duplicate publications based on PMID"""
        seen_pmids = set()
        unique_pubs = []
        
        for pub in publications:
            pmid = pub.get('pmid')
            if pmid and pmid not in seen_pmids:
                seen_pmids.add(pmid)
                unique_pubs.append(pub)
        
        return unique_pubs
    
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
                conn.commit()
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
    
    def _log_update(self, conn, professor_id, total_pubs, new_pubs):
        """Log the update results"""
        try:
            conn.execute("""
                INSERT INTO publication_update_log 
                (professor_id, search_type, publications_found, new_publications, 
                 citations_updated, update_duration, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                professor_id, 'full', total_pubs, new_pubs, 0, 0, 'success'
            ))
            conn.commit()
        except Exception as e:
            self.logger.error(f"Error logging update: {e}")
    
    def _update_citations_batch(self, limit=50):
        """Update citations for publications with DOIs"""
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
                LIMIT ?
            """, (limit,))
            
            publications = cursor.fetchall()
            
            for pub in publications:
                try:
                    citations = self.opencitations.get_citations(pub['doi'])
                    
                    # Update citation count
                    conn.execute("""
                        UPDATE publications 
                        SET citation_count = ?, last_citation_update = ?
                        WHERE id = ?
                    """, (len(citations), datetime.now(), pub['id']))
                    
                    # Rate limiting for OpenCitations
                    time.sleep(self.opencitations.rate_limit_delay)
                    
                except Exception as e:
                    self.logger.error(f"Error updating citations for publication {pub['id']}: {e}")
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Updated citations for {len(publications)} publications")
            
        except Exception as e:
            self.logger.error(f"Error updating citations: {e}")


if __name__ == "__main__":
    # Configuration
    EMAIL = "your-email@domain.com"  # Required for PubMed API
    API_KEY = None  # Optional NCBI API key
    
    # Paths
    DATABASE_PATH = "database/facultyfinder_dev.db"
    FACULTY_CSV = "data/mcmaster_hei_faculty.csv"
    SCIMAGO_CSV = "data/scimago_journals_comprehensive.csv"
    
    # Initialize system
    system = PublicationUpdateSystem(DATABASE_PATH, EMAIL, API_KEY)
    
    # Run full update
    system.run_full_update(FACULTY_CSV, SCIMAGO_CSV)
    
    print("Publication update completed! Check publication_updates.log for details.") 