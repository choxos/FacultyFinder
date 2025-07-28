"""
Open Citations API Integration for FacultyFinder
Handles citation data retrieval and citation network analysis
"""

import requests
import time
import json
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import sqlite3
from urllib.parse import quote

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenCitationsAPI:
    """Interface for Open Citations API services"""
    
    def __init__(self, rate_limit_delay: float = 0.1):
        """
        Initialize OpenCitations API client
        
        Args:
            rate_limit_delay (float): Delay between API requests in seconds
        """
        self.base_url = "https://api.opencitations.net/index/v2"
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0
        
        # API endpoints
        self.endpoints = {
            'citations': '/citations',
            'references': '/references', 
            'metadata': '/metadata',
            'citation_count': '/citation-count'
        }
        
        logger.info("OpenCitations API client initialized")
    
    def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, identifiers: List[str], 
                     id_type: str = 'pmid') -> Optional[List[Dict]]:
        """
        Make API request to OpenCitations
        
        Args:
            endpoint (str): API endpoint to call
            identifiers (List[str]): List of paper identifiers (PMIDs or DOIs)
            id_type (str): Type of identifier ('pmid' or 'doi')
            
        Returns:
            Optional[List[Dict]]: API response data or None if failed
        """
        
        if not identifiers:
            return []
        
        # Rate limiting
        self._rate_limit()
        
        # Prepare identifiers for API
        if id_type == 'pmid':
            formatted_ids = [f"pmid:{pmid}" for pmid in identifiers]
        else:
            formatted_ids = identifiers
        
        # Join identifiers with double underscore as per API spec
        ids_param = '__'.join(formatted_ids)
        
        url = f"{self.base_url}{endpoint}/{ids_param}"
        
        try:
            headers = {
                'User-Agent': 'FacultyFinder Citation Analyzer (https://github.com/your-repo)',
                'Accept': 'application/json'
            }
            
            logger.debug(f"Making request to: {url}")
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            logger.debug(f"Received {len(data) if data else 0} results")
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            return None
    
    def get_citations(self, pmids: List[str]) -> List[Dict]:
        """
        Get citations for given PMIDs (papers that cite these papers)
        
        Args:
            pmids (List[str]): List of PubMed IDs
            
        Returns:
            List[Dict]: List of citing papers
        """
        
        logger.info(f"Fetching citations for {len(pmids)} papers")
        
        # Process in batches to avoid URL length limits
        batch_size = 10
        all_citations = []
        
        for i in range(0, len(pmids), batch_size):
            batch = pmids[i:i + batch_size]
            citations = self._make_request(self.endpoints['citations'], batch, 'pmid')
            
            if citations:
                all_citations.extend(citations)
            
            # Add delay between batches
            if i + batch_size < len(pmids):
                time.sleep(0.5)
        
        logger.info(f"Retrieved {len(all_citations)} citation records")
        return all_citations
    
    def get_references(self, pmids: List[str]) -> List[Dict]:
        """
        Get references for given PMIDs (papers cited by these papers)
        
        Args:
            pmids (List[str]): List of PubMed IDs
            
        Returns:
            List[Dict]: List of referenced papers
        """
        
        logger.info(f"Fetching references for {len(pmids)} papers")
        
        batch_size = 10
        all_references = []
        
        for i in range(0, len(pmids), batch_size):
            batch = pmids[i:i + batch_size]
            references = self._make_request(self.endpoints['references'], batch, 'pmid')
            
            if references:
                all_references.extend(references)
            
            if i + batch_size < len(pmids):
                time.sleep(0.5)
        
        logger.info(f"Retrieved {len(all_references)} reference records")
        return all_references
    
    def get_citation_count(self, pmids: List[str]) -> Dict[str, int]:
        """
        Get citation counts for given PMIDs
        
        Args:
            pmids (List[str]): List of PubMed IDs
            
        Returns:
            Dict[str, int]: Mapping of PMID to citation count
        """
        
        logger.info(f"Fetching citation counts for {len(pmids)} papers")
        
        batch_size = 10
        citation_counts = {}
        
        for i in range(0, len(pmids), batch_size):
            batch = pmids[i:i + batch_size]
            counts = self._make_request(self.endpoints['citation_count'], batch, 'pmid')
            
            if counts:
                for item in counts:
                    pmid = item.get('cited', '').replace('pmid:', '')
                    count = int(item.get('count', 0))
                    if pmid:
                        citation_counts[pmid] = count
            
            if i + batch_size < len(pmids):
                time.sleep(0.5)
        
        logger.info(f"Retrieved citation counts for {len(citation_counts)} papers")
        return citation_counts

class CitationManager:
    """Manages citation data storage and analysis"""
    
    def __init__(self, db_path: str):
        """Initialize citation manager"""
        self.db_path = db_path
        self.api = OpenCitationsAPI()
        
    def fetch_and_store_citations(self, pmids: List[str]) -> int:
        """
        Fetch citations from OpenCitations and store in database
        
        Args:
            pmids (List[str]): List of PubMed IDs to fetch citations for
            
        Returns:
            int: Number of citation records stored
        """
        
        if not pmids:
            return 0
        
        try:
            # Get citations (papers that cite our papers)
            citations = self.api.get_citations(pmids)
            
            # Get references (papers cited by our papers)  
            references = self.api.get_references(pmids)
            
            # Store citation data
            stored_count = 0
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Store citations
            for citation in citations:
                try:
                    citing_id = citation.get('citing', '').replace('pmid:', '')
                    cited_id = citation.get('cited', '').replace('pmid:', '')
                    
                    if citing_id and cited_id:
                        cursor.execute("""
                            INSERT OR IGNORE INTO citations 
                            (citing_pmid, cited_pmid, citing_doi, cited_doi, source)
                            VALUES (?, ?, ?, ?, ?)
                        """, (
                            citing_id,
                            cited_id,
                            citation.get('citing_doi', ''),
                            citation.get('cited_doi', ''),
                            'opencitations'
                        ))
                        stored_count += 1
                except Exception as e:
                    logger.warning(f"Error storing citation: {str(e)}")
            
            # Store references
            for reference in references:
                try:
                    citing_id = reference.get('citing', '').replace('pmid:', '')
                    cited_id = reference.get('cited', '').replace('pmid:', '')
                    
                    if citing_id and cited_id:
                        cursor.execute("""
                            INSERT OR IGNORE INTO citations 
                            (citing_pmid, cited_pmid, citing_doi, cited_doi, source)
                            VALUES (?, ?, ?, ?, ?)
                        """, (
                            citing_id,
                            cited_id,
                            reference.get('citing_doi', ''),
                            reference.get('cited_doi', ''),
                            'opencitations'
                        ))
                        stored_count += 1
                except Exception as e:
                    logger.warning(f"Error storing reference: {str(e)}")
            
            conn.commit()
            conn.close()
            
            logger.info(f"Stored {stored_count} citation records")
            return stored_count
            
        except Exception as e:
            logger.error(f"Error fetching/storing citations: {str(e)}")
            return 0
    
    def update_publication_metrics(self, pmids: List[str]) -> int:
        """
        Update publication metrics including citation counts
        
        Args:
            pmids (List[str]): List of PubMed IDs to update metrics for
            
        Returns:
            int: Number of publications updated
        """
        
        if not pmids:
            return 0
        
        try:
            # Get citation counts from API
            citation_counts = self.api.get_citation_count(pmids)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            updated_count = 0
            
            for pmid, count in citation_counts.items():
                cursor.execute("""
                    INSERT OR REPLACE INTO publication_metrics 
                    (pmid, total_citations, last_updated)
                    VALUES (?, ?, ?)
                """, (pmid, count, datetime.now().isoformat()))
                updated_count += 1
            
            conn.commit()
            conn.close()
            
            logger.info(f"Updated metrics for {updated_count} publications")
            return updated_count
            
        except Exception as e:
            logger.error(f"Error updating publication metrics: {str(e)}")
            return 0
    
    def build_citation_network(self) -> int:
        """
        Build citation network between professors based on citation data
        
        Returns:
            int: Number of professor-to-professor citation relationships created
        """
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Find citations between professors in our database
            query = """
                SELECT DISTINCT
                    citing_prof.id as citing_professor_id,
                    cited_prof.id as cited_professor_id,
                    c.citing_pmid,
                    c.cited_pmid,
                    citing_pub.publication_year as citing_year,
                    cited_pub.publication_year as cited_year
                FROM citations c
                JOIN author_publications citing_ap ON c.citing_pmid = citing_ap.publication_pmid
                JOIN author_publications cited_ap ON c.cited_pmid = cited_ap.publication_pmid
                JOIN professors citing_prof ON citing_ap.professor_id = citing_prof.id
                JOIN professors cited_prof ON cited_ap.professor_id = cited_prof.id
                LEFT JOIN publications citing_pub ON c.citing_pmid = citing_pub.pmid
                LEFT JOIN publications cited_pub ON c.cited_pmid = cited_pub.pmid
                WHERE citing_prof.id != cited_prof.id
            """
            
            cursor.execute(query)
            citation_relationships = cursor.fetchall()
            
            network_count = 0
            
            for row in citation_relationships:
                try:
                    citing_year = row[4] if row[4] else datetime.now().year
                    cited_year = row[5] if row[5] else datetime.now().year
                    
                    cursor.execute("""
                        INSERT OR REPLACE INTO citation_networks
                        (citing_professor_id, cited_professor_id, citing_pmid, cited_pmid,
                         citation_count, first_citation_year, last_citation_year, updated_at)
                        VALUES (?, ?, ?, ?, 1, ?, ?, ?)
                    """, (
                        row[0], row[1], row[2], row[3],
                        int(citing_year), int(citing_year),
                        datetime.now().isoformat()
                    ))
                    network_count += 1
                    
                except Exception as e:
                    logger.warning(f"Error creating citation network entry: {str(e)}")
            
            conn.commit()
            conn.close()
            
            logger.info(f"Created {network_count} citation network relationships")
            return network_count
            
        except Exception as e:
            logger.error(f"Error building citation network: {str(e)}")
            return 0
    
    def get_professor_citation_network(self, professor_id: int, depth: int = 2) -> Dict:
        """
        Get citation network for a specific professor
        
        Args:
            professor_id (int): Professor ID
            depth (int): Network depth (1 = direct citations, 2 = second-degree)
            
        Returns:
            Dict: Citation network data with nodes and edges
        """
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get direct citations (both directions)
            cursor.execute("""
                SELECT 
                    cn.citing_professor_id,
                    cn.cited_professor_id,
                    cn.citation_count,
                    citing_prof.name as citing_name,
                    cited_prof.name as cited_name,
                    citing_prof.university_id as citing_uni,
                    cited_prof.university_id as cited_uni
                FROM citation_networks cn
                JOIN professors citing_prof ON cn.citing_professor_id = citing_prof.id
                JOIN professors cited_prof ON cn.cited_professor_id = cited_prof.id
                WHERE cn.citing_professor_id = ? OR cn.cited_professor_id = ?
            """, (professor_id, professor_id))
            
            direct_citations = cursor.fetchall()
            
            # Build network structure
            nodes = set()
            edges = []
            
            # Add central professor
            cursor.execute("SELECT name, university_id FROM professors WHERE id = ?", (professor_id,))
            central_prof = cursor.fetchone()
            if central_prof:
                nodes.add((professor_id, central_prof[0], central_prof[1], 'central'))
            
            # Process direct citations
            for citation in direct_citations:
                citing_id, cited_id = citation[0], citation[1]
                citation_count = citation[2]
                
                # Add nodes
                nodes.add((citing_id, citation[3], citation[5], 'citing' if citing_id != professor_id else 'cited'))
                nodes.add((cited_id, citation[4], citation[6], 'cited' if cited_id != professor_id else 'citing'))
                
                # Add edge
                edges.append({
                    'source': citing_id,
                    'target': cited_id,
                    'weight': citation_count,
                    'type': 'citation'
                })
            
            conn.close()
            
            # Convert nodes to list format
            nodes_list = [
                {
                    'id': node[0],
                    'name': node[1],
                    'university_id': node[2],
                    'type': node[3]
                }
                for node in nodes
            ]
            
            return {
                'nodes': nodes_list,
                'edges': edges,
                'central_professor': professor_id,
                'total_nodes': len(nodes_list),
                'total_edges': len(edges)
            }
            
        except Exception as e:
            logger.error(f"Error getting citation network: {str(e)}")
            return {'nodes': [], 'edges': [], 'total_nodes': 0, 'total_edges': 0}

def demo_opencitations():
    """Demonstrate OpenCitations integration"""
    
    print("🔬 OpenCitations Integration Demo")
    print("=" * 50)
    
    # Initialize API
    api = OpenCitationsAPI()
    
    # Test with sample PMIDs
    test_pmids = ['33087917', '32778518', '31578536']  # Sample biomedical papers
    
    print(f"Testing with PMIDs: {test_pmids}")
    
    # Get citation counts
    citation_counts = api.get_citation_count(test_pmids)
    
    if citation_counts:
        print("\n📊 Citation Counts:")
        for pmid, count in citation_counts.items():
            print(f"  PMID {pmid}: {count} citations")
    
    # Get some citations
    citations = api.get_citations(test_pmids[:1])  # Test with just one paper
    
    if citations:
        print(f"\n📄 Sample Citations (first 3):")
        for i, citation in enumerate(citations[:3]):
            citing = citation.get('citing', '').replace('pmid:', '')
            cited = citation.get('cited', '').replace('pmid:', '')
            print(f"  {i+1}. Paper {citing} cites Paper {cited}")

if __name__ == "__main__":
    demo_opencitations() 