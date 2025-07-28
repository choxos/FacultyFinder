"""
PubMed Integration Module for FacultyFinder
Handles publication search and storage for faculty members
"""

import os
import json
import time
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from Bio import Entrez

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PubMedSearcher:
    """Handles PubMed searches and publication data management"""
    
    def __init__(self, email: str = None, tool: str = "FacultyFinder"):
        """
        Initialize PubMed searcher
        
        Args:
            email (str): Email for NCBI API (required)
            tool (str): Tool name for API identification
        """
        self.email = email or os.getenv('NCBI_EMAIL', 'facultyfinder@example.com')
        self.tool = tool
        
        # Configure Entrez
        Entrez.email = self.email
        Entrez.tool = self.tool
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.34  # ~3 requests per second (NCBI limit)
        
        logger.info(f"PubMed searcher initialized with email: {self.email}")
    
    def _rate_limit(self):
        """Implement rate limiting for NCBI API"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def search_author_publications(self, author_name: str, max_results: int = 50) -> List[Dict]:
        """
        Search for publications by author name
        
        Args:
            author_name (str): Author name to search for
            max_results (int): Maximum number of results
            
        Returns:
            List[Dict]: List of publication records
        """
        
        try:
            self._rate_limit()
            
            # Create search query
            search_query = f"{author_name}[Author]"
            
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
        Fetch detailed publication information
        
        Args:
            pmids (List[str]): List of PubMed IDs
            
        Returns:
            List[Dict]: Detailed publication records
        """
        
        if not pmids:
            return []
        
        try:
            self._rate_limit()
            
            # Fetch records in batches to avoid timeout
            batch_size = 100
            all_publications = []
            
            for i in range(0, len(pmids), batch_size):
                batch_pmids = pmids[i:i + batch_size]
                
                handle = Entrez.efetch(
                    db="pubmed",
                    id=",".join(batch_pmids),
                    rettype="medline",
                    retmode="xml"
                )
                
                records = Entrez.read(handle)
                handle.close()
                
                batch_publications = self._parse_publication_records(records)
                all_publications.extend(batch_publications)
                
                # Rate limit between batches
                if i + batch_size < len(pmids):
                    time.sleep(0.5)
            
            return all_publications
            
        except Exception as e:
            logger.error(f"Error fetching publication details: {str(e)}")
            return []
    
    def _parse_publication_records(self, records) -> List[Dict]:
        """Parse PubMed XML records into structured data"""
        
        publications = []
        
        for record in records.get('PubmedArticle', []):
            try:
                article = record['MedlineCitation']['Article']
                medline = record['MedlineCitation']
                
                # Basic information
                pmid = str(medline['PMID'])
                title = article.get('ArticleTitle', '').strip()
                
                # Authors
                authors = self._extract_authors(article.get('AuthorList', []))
                
                # Journal information
                journal_info = self._extract_journal_info(article.get('Journal', {}))
                
                # Publication date
                pub_date = self._extract_publication_date(article.get('Journal', {}))
                
                # Abstract
                abstract = self._extract_abstract(article.get('Abstract', {}))
                
                # Keywords/MeSH terms
                keywords = self._extract_keywords(medline.get('MeshHeadingList', []))
                
                # DOI
                doi = self._extract_doi(article.get('ELocationID', []))
                
                publication = {
                    'pmid': pmid,
                    'title': title,
                    'authors': authors,
                    'journal_name': journal_info['title'],
                    'journal_abbrev': journal_info['abbrev'],
                    'volume': journal_info.get('volume', ''),
                    'issue': journal_info.get('issue', ''),
                    'pages': journal_info.get('pages', ''),
                    'publication_date': pub_date,
                    'publication_year': pub_date.split('-')[0] if pub_date else '',
                    'abstract': abstract,
                    'keywords': keywords,
                    'doi': doi,
                    'pubmed_url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    'citation_count': 0,  # To be filled by external API
                    'created_at': datetime.now().isoformat()
                }
                
                publications.append(publication)
                
            except Exception as e:
                logger.warning(f"Error parsing publication record: {str(e)}")
                continue
        
        return publications
    
    def _extract_authors(self, author_list) -> List[str]:
        """Extract author names from PubMed record"""
        authors = []
        
        for author in author_list:
            if 'LastName' in author and 'ForeName' in author:
                full_name = f"{author['ForeName']} {author['LastName']}"
                authors.append(full_name)
            elif 'CollectiveName' in author:
                authors.append(author['CollectiveName'])
        
        return authors
    
    def _extract_journal_info(self, journal) -> Dict:
        """Extract journal information"""
        return {
            'title': journal.get('Title', 'Unknown Journal'),
            'abbrev': journal.get('ISOAbbreviation', ''),
            'volume': journal.get('JournalIssue', {}).get('Volume', ''),
            'issue': journal.get('JournalIssue', {}).get('Issue', ''),
            'pages': journal.get('Pagination', {}).get('MedlinePgn', '')
        }
    
    def _extract_publication_date(self, journal) -> str:
        """Extract publication date in ISO format"""
        try:
            issue = journal.get('JournalIssue', {})
            pub_date = issue.get('PubDate', {})
            
            year = pub_date.get('Year', '')
            month = pub_date.get('Month', '01')
            day = pub_date.get('Day', '01')
            
            # Handle month names
            month_map = {
                'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
                'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
                'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
            }
            
            if month in month_map:
                month = month_map[month]
            elif not month.isdigit():
                month = '01'
            
            # Ensure proper formatting
            if len(month) == 1:
                month = '0' + month
            if len(day) == 1:
                day = '0' + day
            
            return f"{year}-{month}-{day}" if year else ''
            
        except Exception:
            return ''
    
    def _extract_abstract(self, abstract_info) -> str:
        """Extract abstract text"""
        try:
            abstract_texts = abstract_info.get('AbstractText', [])
            
            if isinstance(abstract_texts, list):
                return ' '.join([str(text) for text in abstract_texts])
            else:
                return str(abstract_texts)
                
        except Exception:
            return ''
    
    def _extract_keywords(self, mesh_list) -> List[str]:
        """Extract MeSH keywords"""
        keywords = []
        
        try:
            for mesh in mesh_list:
                descriptor = mesh.get('DescriptorName', {})
                if isinstance(descriptor, dict):
                    keyword = descriptor.get('@UI', '') or str(descriptor)
                else:
                    keyword = str(descriptor)
                
                if keyword:
                    keywords.append(keyword)
        except Exception:
            pass
        
        return keywords
    
    def _extract_doi(self, elocation_list) -> str:
        """Extract DOI from publication record"""
        try:
            for elocation in elocation_list:
                if elocation.get('@EIdType') == 'doi':
                    return elocation.get('text', '')
        except Exception:
            pass
        
        return ''

class PublicationDatabase:
    """Manages publication storage and retrieval"""
    
    def __init__(self, db_path: str):
        """Initialize publication database"""
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize publication tables if they don't exist"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create publications table if not exists (extending existing schema)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS professor_publications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    professor_id INTEGER,
                    pmid TEXT UNIQUE,
                    title TEXT,
                    authors TEXT,
                    journal_name TEXT,
                    journal_abbrev TEXT,
                    volume TEXT,
                    issue TEXT,
                    pages TEXT,
                    publication_date TEXT,
                    publication_year TEXT,
                    abstract TEXT,
                    keywords TEXT,
                    doi TEXT,
                    pubmed_url TEXT,
                    citation_count INTEGER DEFAULT 0,
                    created_at TEXT,
                    updated_at TEXT,
                    FOREIGN KEY (professor_id) REFERENCES professors (id)
                )
            """)
            
            # Create index for faster searches
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_professor_publications_professor
                ON professor_publications (professor_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_professor_publications_pmid
                ON professor_publications (pmid)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_professor_publications_year
                ON professor_publications (publication_year)
            """)
            
            conn.commit()
            conn.close()
            
            logger.info("Publication database initialized")
            
        except Exception as e:
            logger.error(f"Error initializing publication database: {str(e)}")
    
    def store_publications(self, professor_id: int, publications: List[Dict]) -> int:
        """
        Store publications for a professor
        
        Args:
            professor_id (int): Professor ID
            publications (List[Dict]): List of publication records
            
        Returns:
            int: Number of publications stored
        """
        
        if not publications:
            return 0
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            stored_count = 0
            
            for pub in publications:
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO professor_publications 
                        (professor_id, pmid, title, authors, journal_name, journal_abbrev,
                         volume, issue, pages, publication_date, publication_year,
                         abstract, keywords, doi, pubmed_url, citation_count,
                         created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        professor_id,
                        pub['pmid'],
                        pub['title'],
                        json.dumps(pub['authors']),
                        pub['journal_name'],
                        pub['journal_abbrev'],
                        pub['volume'],
                        pub['issue'],
                        pub['pages'],
                        pub['publication_date'],
                        pub['publication_year'],
                        pub['abstract'],
                        json.dumps(pub['keywords']),
                        pub['doi'],
                        pub['pubmed_url'],
                        pub['citation_count'],
                        pub['created_at'],
                        datetime.now().isoformat()
                    ))
                    
                    stored_count += 1
                    
                except sqlite3.IntegrityError:
                    # Publication already exists, update it
                    cursor.execute("""
                        UPDATE professor_publications 
                        SET title=?, authors=?, journal_name=?, abstract=?, 
                            updated_at=?
                        WHERE pmid=?
                    """, (
                        pub['title'],
                        json.dumps(pub['authors']),
                        pub['journal_name'],
                        pub['abstract'],
                        datetime.now().isoformat(),
                        pub['pmid']
                    ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Stored {stored_count} publications for professor {professor_id}")
            return stored_count
            
        except Exception as e:
            logger.error(f"Error storing publications: {str(e)}")
            return 0
    
    def get_professor_publications(self, professor_id: int) -> List[Dict]:
        """Get all publications for a professor"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM professor_publications 
                WHERE professor_id = ?
                ORDER BY publication_year DESC, publication_date DESC
            """, (professor_id,))
            
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            publications = []
            for row in rows:
                pub = dict(zip(columns, row))
                # Parse JSON fields
                pub['authors'] = json.loads(pub['authors']) if pub['authors'] else []
                pub['keywords'] = json.loads(pub['keywords']) if pub['keywords'] else []
                publications.append(pub)
            
            conn.close()
            return publications
            
        except Exception as e:
            logger.error(f"Error getting publications for professor {professor_id}: {str(e)}")
            return []

def demo_pubmed_search():
    """Demonstrate PubMed search functionality"""
    
    print("🔬 PubMed Integration Demo")
    print("=" * 50)
    
    # Initialize searcher
    searcher = PubMedSearcher()
    
    # Test search
    test_author = "Gordon Guyatt"
    print(f"Searching for publications by: {test_author}")
    
    publications = searcher.search_author_publications(test_author, max_results=5)
    
    if publications:
        print(f"\n📚 Found {len(publications)} publications:")
        
        for i, pub in enumerate(publications, 1):
            print(f"\n{i}. {pub['title'][:100]}...")
            print(f"   Journal: {pub['journal_name']}")
            print(f"   Year: {pub['publication_year']}")
            print(f"   Authors: {len(pub['authors'])} authors")
            print(f"   PMID: {pub['pmid']}")
    else:
        print("No publications found")

if __name__ == "__main__":
    demo_pubmed_search() 