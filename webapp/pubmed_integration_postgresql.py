"""
PubMed Integration Module for FacultyFinder (PostgreSQL Version)
Handles publication search and storage for faculty members on VPS with PostgreSQL
"""

import os
import json
import time
import logging
import psycopg2
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from Bio import Entrez
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PubMedSearcherPostgreSQL:
    """Handles PubMed searches and publication data management for PostgreSQL"""
    
    def __init__(self, email: str = None, tool: str = "FacultyFinder"):
        """
        Initialize PubMed searcher for PostgreSQL
        
        Args:
            email (str): Email for NCBI API (required)
            tool (str): Tool name for API identification
        """
        self.email = email or os.getenv('NCBI_EMAIL', 'facultyfinder@example.com')
        self.tool = tool
        self.api_key = os.getenv('NCBI_API_KEY', None)
        
        # Configure Entrez
        Entrez.email = self.email
        Entrez.tool = self.tool
        if self.api_key:
            Entrez.api_key = self.api_key
        
        # Rate limiting (higher with API key)
        self.last_request_time = 0
        rate_limit = int(os.getenv('PUBMED_RATE_LIMIT', '3'))
        self.min_request_interval = 1.0 / rate_limit
        
        logger.info(f"PubMed searcher initialized with email: {self.email}")
        if self.api_key:
            logger.info("✅ Using NCBI API key for higher rate limits")
    
    def get_db_connection(self):
        """Get PostgreSQL database connection"""
        try:
            conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                database=os.getenv('DB_NAME', 'ff_production'),
                user=os.getenv('DB_USER', 'ff_user'),
                password=os.getenv('DB_PASSWORD'),
                port=os.getenv('DB_PORT', '5432')
            )
            return conn
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            raise
    
    def _rate_limit(self):
        """Implement rate limiting for NCBI API"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def search_author_publications(self, author_name: str, max_results: int = 50, 
                                 affiliation: str = None, years: str = "2020:2025") -> List[Dict]:
        """
        Search for publications by author name
        
        Args:
            author_name (str): Author name to search for
            max_results (int): Maximum number of results
            affiliation (str): University/institution name to filter by
            years (str): Publication years range (e.g., "2020:2025")
            
        Returns:
            List[Dict]: List of publication records
        """
        
        try:
            self._rate_limit()
            
            # Create search query
            search_terms = [f"{author_name}[Author]"]
            
            if affiliation:
                search_terms.append(f"{affiliation}[Affiliation]")
            
            if years:
                search_terms.append(f"{years}[Publication Date]")
            
            search_query = " AND ".join(search_terms)
            
            logger.info(f"Searching PubMed for: {search_query}")
            
            # Perform search
            handle = Entrez.esearch(
                db="pubmed",
                term=search_query,
                retmax=max_results,
                sort="pub_date",
                retmode="xml"
            )
            
            search_results = Entrez.read(handle)
            handle.close()
            
            pmids = search_results.get("IdList", [])
            
            if not pmids:
                logger.info(f"No publications found for {author_name}")
                return []
            
            logger.info(f"Found {len(pmids)} publications for {author_name}")
            
            # Fetch detailed information
            publications = self._fetch_publication_details(pmids)
            
            return publications
            
        except Exception as e:
            logger.error(f"Error searching PubMed for {author_name}: {str(e)}")
            return []
    
    def _fetch_publication_details(self, pmids: List[str]) -> List[Dict]:
        """
        Fetch detailed publication information for given PMIDs
        
        Args:
            pmids (List[str]): List of PubMed IDs
            
        Returns:
            List[Dict]: List of publication records with details
        """
        
        if not pmids:
            return []
        
        try:
            self._rate_limit()
            
            # Fetch details in batches to avoid overwhelming API
            batch_size = 20
            all_publications = []
            
            for i in range(0, len(pmids), batch_size):
                batch_pmids = pmids[i:i + batch_size]
                batch_publications = self._fetch_batch_details(batch_pmids)
                all_publications.extend(batch_publications)
                
                # Rate limiting between batches
                if i + batch_size < len(pmids):
                    time.sleep(0.5)
            
            return all_publications
            
        except Exception as e:
            logger.error(f"Error fetching publication details: {str(e)}")
            return []
    
    def _fetch_batch_details(self, pmids: List[str]) -> List[Dict]:
        """Fetch details for a batch of PMIDs"""
        
        try:
            # Fetch publication details
            handle = Entrez.efetch(
                db="pubmed",
                id=",".join(pmids),
                rettype="medline",
                retmode="xml"
            )
            
            records = Entrez.read(handle)
            handle.close()
            
            publications = []
            
            for record in records['PubmedArticle']:
                try:
                    pub_data = self._parse_publication_record(record)
                    if pub_data:
                        publications.append(pub_data)
                except Exception as e:
                    logger.warning(f"Error parsing publication record: {str(e)}")
                    continue
            
            return publications
            
        except Exception as e:
            logger.error(f"Error fetching batch details: {str(e)}")
            return []
    
    def _parse_publication_record(self, record) -> Optional[Dict]:
        """
        Parse a PubMed publication record
        
        Args:
            record: PubMed record from Entrez
            
        Returns:
            Dict: Parsed publication data
        """
        
        try:
            medline_citation = record['MedlineCitation']
            article = medline_citation['Article']
            
            # Basic information
            pmid = str(medline_citation['PMID'])
            title = article.get('ArticleTitle', '')
            
            # Handle abstract
            abstract = ""
            if 'Abstract' in article and 'AbstractText' in article['Abstract']:
                abstract_parts = article['Abstract']['AbstractText']
                if isinstance(abstract_parts, list):
                    abstract = " ".join([str(part) for part in abstract_parts])
                else:
                    abstract = str(abstract_parts)
            
            # Authors
            authors = []
            if 'AuthorList' in article:
                for author in article['AuthorList']:
                    if 'LastName' in author and 'ForeName' in author:
                        full_name = f"{author['ForeName']} {author['LastName']}"
                        authors.append(full_name)
            
            authors_str = "; ".join(authors)
            
            # Journal information
            journal = article.get('Journal', {})
            journal_title = journal.get('Title', '') or journal.get('ISOAbbreviation', '')
            
            # Publication date
            pub_date = None
            pub_year = None
            
            if 'DateCompleted' in medline_citation:
                date_completed = medline_citation['DateCompleted']
                try:
                    pub_year = int(date_completed.get('Year', 0))
                    month = int(date_completed.get('Month', 1))
                    day = int(date_completed.get('Day', 1))
                    pub_date = datetime(pub_year, month, day).date()
                except (ValueError, TypeError):
                    pass
            
            # If no DateCompleted, try PubDate
            if not pub_date and 'JournalIssue' in journal and 'PubDate' in journal['JournalIssue']:
                pub_date_info = journal['JournalIssue']['PubDate']
                try:
                    if 'Year' in pub_date_info:
                        pub_year = int(pub_date_info['Year'])
                        month = int(pub_date_info.get('Month', 1)) if pub_date_info.get('Month', '').isdigit() else 1
                        day = int(pub_date_info.get('Day', 1)) if pub_date_info.get('Day', '').isdigit() else 1
                        pub_date = datetime(pub_year, month, day).date()
                except (ValueError, TypeError):
                    pass
            
            # DOI
            doi = ""
            if 'ELocationID' in article:
                for elocation in article['ELocationID']:
                    if elocation.attributes.get('EIdType') == 'doi':
                        doi = str(elocation)
                        break
            
            # PMC ID
            pmcid = ""
            if 'PubmedData' in record and 'ArticleIdList' in record['PubmedData']:
                for article_id in record['PubmedData']['ArticleIdList']:
                    if article_id.attributes.get('IdType') == 'pmc':
                        pmcid = str(article_id)
                        break
            
            # Journal issue details
            volume = ""
            issue = ""
            pages = ""
            
            if 'JournalIssue' in journal:
                volume = journal['JournalIssue'].get('Volume', '')
                issue = journal['JournalIssue'].get('Issue', '')
            
            if 'Pagination' in article and 'MedlinePgn' in article['Pagination']:
                pages = article['Pagination']['MedlinePgn']
            
            # Keywords and MeSH terms
            keywords = []
            mesh_terms = []
            
            if 'KeywordList' in medline_citation:
                for keyword_list in medline_citation['KeywordList']:
                    keywords.extend([str(kw) for kw in keyword_list])
            
            if 'MeshHeadingList' in medline_citation:
                for mesh_heading in medline_citation['MeshHeadingList']:
                    if 'DescriptorName' in mesh_heading:
                        mesh_terms.append(str(mesh_heading['DescriptorName']))
            
            # Publication types
            pub_types = []
            if 'PublicationTypeList' in article:
                pub_types = [str(pt) for pt in article['PublicationTypeList']]
            
            # Country and affiliation
            country = ""
            affiliations = []
            
            if 'AuthorList' in article:
                for author in article['AuthorList']:
                    if 'AffiliationInfo' in author:
                        for affiliation in author['AffiliationInfo']:
                            if 'Affiliation' in affiliation:
                                aff_text = str(affiliation['Affiliation'])
                                affiliations.append(aff_text)
                                
                                # Try to extract country
                                if not country:
                                    aff_lower = aff_text.lower()
                                    if 'canada' in aff_lower or 'ontario' in aff_lower:
                                        country = "Canada"
                                    elif 'usa' in aff_lower or 'united states' in aff_lower:
                                        country = "United States"
            
            publication_data = {
                'pmid': pmid,
                'pmcid': pmcid,
                'doi': doi,
                'title': title,
                'abstract': abstract,
                'authors': authors_str,
                'journal_name': journal_title,
                'publication_date': pub_date,
                'publication_year': pub_year,
                'volume': volume,
                'issue': issue,
                'pages': pages,
                'keywords': "; ".join(keywords),
                'mesh_terms': "; ".join(mesh_terms),
                'publication_types': "; ".join(pub_types),
                'language': 'eng',
                'country': country,
                'affiliations': "; ".join(affiliations)
            }
            
            return publication_data
            
        except Exception as e:
            logger.error(f"Error parsing publication record: {str(e)}")
            return None
    
    def store_publications(self, professor_id: int, publications: List[Dict]) -> int:
        """
        Store publications in PostgreSQL database
        
        Args:
            professor_id (int): ID of the professor
            publications (List[Dict]): List of publication data
            
        Returns:
            int: Number of publications stored
        """
        
        if not publications:
            return 0
        
        conn = None
        try:
            conn = self.get_db_connection()
            cur = conn.cursor()
            
            stored_count = 0
            
            for pub in publications:
                try:
                    # Check if publication already exists
                    cur.execute("SELECT id FROM publications WHERE pmid = %s", (pub['pmid'],))
                    existing = cur.fetchone()
                    
                    if existing:
                        publication_id = existing[0]
                        logger.debug(f"Publication {pub['pmid']} already exists")
                    else:
                        # Insert new publication
                        insert_query = """
                        INSERT INTO publications (
                            pmid, pmcid, doi, title, abstract, authors, journal_name,
                            publication_date, publication_year, volume, issue, pages,
                            keywords, mesh_terms, publication_types, language, country, affiliations
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        ) RETURNING id
                        """
                        
                        cur.execute(insert_query, (
                            pub['pmid'], pub['pmcid'], pub['doi'], pub['title'],
                            pub['abstract'], pub['authors'], pub['journal_name'],
                            pub['publication_date'], pub['publication_year'],
                            pub['volume'], pub['issue'], pub['pages'],
                            pub['keywords'], pub['mesh_terms'], pub['publication_types'],
                            pub['language'], pub['country'], pub['affiliations']
                        ))
                        
                        publication_id = cur.fetchone()[0]
                        logger.debug(f"Inserted publication {pub['pmid']} with ID {publication_id}")
                    
                    # Link to professor (check if relationship already exists)
                    cur.execute(
                        "SELECT id FROM author_publications WHERE professor_id = %s AND publication_id = %s",
                        (professor_id, publication_id)
                    )
                    
                    if not cur.fetchone():
                        cur.execute("""
                            INSERT INTO author_publications (professor_id, publication_id, author_order)
                            VALUES (%s, %s, %s)
                        """, (professor_id, publication_id, 1))
                        
                        stored_count += 1
                        logger.debug(f"Linked publication {pub['pmid']} to professor {professor_id}")
                
                except psycopg2.IntegrityError as e:
                    logger.warning(f"Integrity error for publication {pub.get('pmid', 'unknown')}: {str(e)}")
                    conn.rollback()
                    continue
                except Exception as e:
                    logger.error(f"Error storing publication {pub.get('pmid', 'unknown')}: {str(e)}")
                    conn.rollback()
                    continue
            
            conn.commit()
            logger.info(f"Successfully stored {stored_count} publications for professor {professor_id}")
            return stored_count
            
        except Exception as e:
            logger.error(f"Database error storing publications: {str(e)}")
            if conn:
                conn.rollback()
            return 0
        finally:
            if conn:
                cur.close()
                conn.close()
    
    def get_publication_stats(self) -> Dict:
        """Get publication statistics from database"""
        
        try:
            conn = self.get_db_connection()
            cur = conn.cursor()
            
            # Total publications
            cur.execute("SELECT COUNT(*) FROM publications")
            total_publications = cur.fetchone()[0]
            
            # Publications with PMIDs
            cur.execute("SELECT COUNT(*) FROM publications WHERE pmid IS NOT NULL")
            with_pmids = cur.fetchone()[0]
            
            # Faculty with publications
            cur.execute("SELECT COUNT(DISTINCT professor_id) FROM author_publications")
            faculty_with_pubs = cur.fetchone()[0]
            
            # Recent publications (last 30 days)
            cur.execute("""
                SELECT COUNT(*) FROM publications 
                WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
            """)
            recent_pubs = cur.fetchone()[0]
            
            stats = {
                'total_publications': total_publications,
                'publications_with_pmids': with_pmids,
                'faculty_with_publications': faculty_with_pubs,
                'recent_publications': recent_pubs
            }
            
            cur.close()
            conn.close()
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting publication stats: {str(e)}")
            return {}

def main():
    """Test function for the PubMed searcher"""
    
    print("🧪 Testing PubMed PostgreSQL Integration...")
    
    try:
        # Initialize searcher
        searcher = PubMedSearcherPostgreSQL()
        
        # Test search
        print("Testing search for Gordon Guyatt...")
        publications = searcher.search_author_publications(
            "Gordon Guyatt", 
            max_results=5, 
            affiliation="McMaster University"
        )
        
        print(f"Found {len(publications)} publications")
        
        for i, pub in enumerate(publications[:3], 1):
            print(f"\n{i}. {pub.get('title', 'No title')}")
            print(f"   PMID: {pub.get('pmid', 'N/A')}")
            print(f"   Year: {pub.get('publication_year', 'N/A')}")
            print(f"   Journal: {pub.get('journal_name', 'N/A')}")
        
        # Get stats
        stats = searcher.get_publication_stats()
        print(f"\n📊 Current Database Stats:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        print("\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")

if __name__ == "__main__":
    main() 