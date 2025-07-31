#!/usr/bin/env python3
"""
OpenAlex Faculty Publication Searcher

This script searches OpenAlex for publications by faculty members, implements
dual search strategy (author-only vs author+institution), saves individual
publication JSON files, and creates faculty tracking CSVs.

Features:
- CSV-driven faculty processing
- Dual search: author-only and author+institution
- Individual publication files: [openalex_id].json
- Faculty tracking CSVs: [faculty_id].csv with current_affiliation flags
- Comprehensive publication data extraction
- Rate limiting and progress tracking
- Resume capability

Usage:
    python openalex_faculty_searcher.py <csv_file> [options]
    
Examples:
    python openalex_faculty_searcher.py data/faculties/CA/ON/CA-ON-002_mcmaster.ca/mcmaster_hei_faculty.csv
    python openalex_faculty_searcher.py data/faculties/CA/ON/CA-ON-002_mcmaster.ca/mcmaster_hei_faculty.csv --max 10 --delay 1
"""

import csv
import json
import requests
import time
import argparse
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Optional, Tuple
from university_folder_mapper import UniversityFolderMapper

class OpenAlexFacultySearcher:
    def __init__(self, email: str = "facultyfinder@research.org", delay: float = 0.5):
        """
        Initialize OpenAlex Faculty Searcher
        
        Args:
            email: Email for polite pool (recommended by OpenAlex)
            delay: Delay between requests in seconds
        """
        self.email = email
        self.delay = delay
        self.base_url = "https://api.openalex.org"
        self.session = requests.Session()
        
        # Set headers for polite pool
        self.session.headers.update({
            'User-Agent': f'FacultyFinder-OpenAlexSearcher/1.0 (mailto:{email})',
            'Accept': 'application/json',
        })
        
        # Add email parameter for polite pool
        self.email_param = f"mailto:{email}"
        
        # Initialize university folder mapper
        self.mapper = UniversityFolderMapper()
        
        # Statistics tracking
        self.stats = {
            'faculty_processed': 0,
            'successful_author_searches': 0,
            'successful_institution_searches': 0,
            'failed_searches': 0,
            'total_publications_found': 0,
            'unique_publications_saved': 0,
            'api_requests_made': 0,
            'rate_limit_hits': 0
        }
        
        # Track processed publications to avoid duplicates
        self.processed_publications: Set[str] = set()
    
    def load_faculty_data(self, csv_file: str) -> List[Dict]:
        """Load faculty data from CSV file"""
        faculty_data = []
        
        # Extract country and province from file path if not in CSV
        file_path = Path(csv_file)
        path_parts = file_path.parts
        
        # Look for pattern like data/faculties/CA/ON/university/file.csv
        default_country = ""
        default_province = ""
        
        try:
            if 'faculties' in path_parts:
                faculties_idx = path_parts.index('faculties')
                if len(path_parts) > faculties_idx + 2:
                    default_country = path_parts[faculties_idx + 1]  # CA
                    default_province = path_parts[faculties_idx + 2]  # ON
        except:
            pass
        
        try:
            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Use default values from path if CSV columns are empty
                    country = row.get('country', '').strip() or default_country
                    province = row.get('province_state', '').strip() or default_province
                    
                    faculty_data.append({
                        'faculty_id': row.get('faculty_id', '').strip(),
                        'name': row.get('name', '').strip(),
                        'first_name': row.get('first_name', '').strip(),
                        'last_name': row.get('last_name', '').strip(),
                        'university_code': row.get('university_code', '').strip(),
                        'university': row.get('university', '').strip(),
                        'university_name': row.get('university', '').strip(),  # Use 'university' field
                        'country': country,
                        'province': province,
                        'department': row.get('department', '').strip()
                    })
                    
            print(f"📊 Loaded {len(faculty_data)} faculty members from {csv_file}")
            if default_country and default_province:
                print(f"📍 Using path-derived location: {default_country}/{default_province}")
            return faculty_data
            
        except Exception as e:
            print(f"❌ Error loading faculty data: {str(e)}")
            return []
    
    def construct_search_queries(self, faculty: Dict) -> Tuple[str, str]:
        """
        Construct OpenAlex search queries for author-only and author+institution
        
        Returns:
            Tuple of (author_query, institution_query)
        """
        # Clean name components
        name = faculty.get('name', '').strip()
        first_name = faculty.get('first_name', '').strip()
        last_name = faculty.get('last_name', '').strip()
        university_name = faculty.get('university_name', '').strip()
        
        # Use individual names if available, otherwise split full name
        if first_name and last_name:
            author_first = first_name
            author_last = last_name
        elif name:
            name_parts = name.split()
            if len(name_parts) >= 2:
                author_first = name_parts[0]
                author_last = ' '.join(name_parts[1:])
            else:
                author_first = ""
                author_last = name
        else:
            print(f"⚠️  No valid name found for faculty: {faculty}")
            return "", ""
        
        # Construct simplified author search query
        # OpenAlex works better with simpler queries
        if author_first and author_last:
            # Use the most likely format: "First Last"
            author_query = f"{author_first} {author_last}"
        else:
            author_query = author_last
        
        # Construct institution query
        institution_query = ""
        if author_query and university_name and university_name != "Unknown University":
            # Clean university name for search
            univ_search = university_name
            # Remove common words that might interfere and keep main identifier
            if "McMaster" in university_name:
                univ_search = "McMaster University"
            elif "University" in university_name:
                # Keep the full name but clean it
                univ_search = university_name.strip()
            
            institution_query = f"{author_query} AND {univ_search}"
        
        return author_query, institution_query
    
    def search_openalex(self, query: str, query_type: str = "author", max_results: int = 200) -> List[Dict]:
        """
        Search OpenAlex for publications
        
        Args:
            query: Search query string
            query_type: Type of query ("author" or "institution")
            max_results: Maximum results to return
            
        Returns:
            List of publication dictionaries
        """
        publications = []
        per_page = 25  # OpenAlex default
        cursor = "*"  # Use cursor pagination for reliability
        
        while len(publications) < max_results:
            try:
                # Use simple search parameter instead of complex filters
                params = {
                    'search': query,
                    'per-page': per_page,
                    'cursor': cursor,
                    'select': 'id,doi,title,display_name,publication_year,publication_date,type,cited_by_count,authorships,primary_location,abstract_inverted_index,concepts,topics,open_access,biblio,language,is_retracted,is_paratext',
                    'email': self.email_param
                }
                
                response = self.session.get(f"{self.base_url}/works", params=params)
                self.stats['api_requests_made'] += 1
                
                if response.status_code == 429:
                    self.stats['rate_limit_hits'] += 1
                    print(f"⏳ Rate limit hit, waiting 30 seconds...")
                    time.sleep(30)
                    continue
                
                response.raise_for_status()
                data = response.json()
                
                results = data.get('results', [])
                if not results:
                    break
                
                # Filter results by author name for more precise matching
                filtered_results = []
                query_lower = query.lower()
                
                for result in results:
                    authorships = result.get('authorships', [])
                    for authorship in authorships:
                        author = authorship.get('author', {})
                        author_name = author.get('display_name', '').lower()
                        
                        # Check if author name contains query terms
                        if any(term in author_name for term in query_lower.split()):
                            filtered_results.append(result)
                            break
                
                publications.extend(filtered_results)
                
                # Check for next cursor
                meta = data.get('meta', {})
                next_cursor = meta.get('next_cursor')
                if not next_cursor:
                    break
                
                cursor = next_cursor
                
                # Respect rate limits
                time.sleep(self.delay)
                
            except requests.exceptions.RequestException as e:
                print(f"❌ OpenAlex search error: {str(e)}")
                break
            except Exception as e:
                print(f"❌ Unexpected error in search: {str(e)}")
                break
        
        return publications[:max_results]
    
    def parse_openalex_publication(self, publication: Dict) -> Dict:
        """
        Parse OpenAlex publication data into comprehensive format
        
        Args:
            publication: Raw OpenAlex publication object
            
        Returns:
            Parsed publication dictionary
        """
        try:
            # Extract basic information
            openalex_id = publication.get('id', '').replace('https://openalex.org/', '')
            
            # Extract title
            title = publication.get('display_name', '') or publication.get('title', '')
            
            # Extract abstract from inverted index
            abstract = ""
            abstract_inverted = publication.get('abstract_inverted_index', {})
            if abstract_inverted:
                # Reconstruct abstract from inverted index
                words_with_positions = []
                for word, positions in abstract_inverted.items():
                    for pos in positions:
                        words_with_positions.append((pos, word))
                
                if words_with_positions:
                    words_with_positions.sort(key=lambda x: x[0])
                    abstract = ' '.join([word for _, word in words_with_positions])
            
            # Extract authors
            authors = []
            authorships = publication.get('authorships', [])
            for authorship in authorships:
                author = authorship.get('author', {})
                if author:
                    author_name = author.get('display_name', '')
                    author_id = author.get('id', '').replace('https://openalex.org/', '')
                    orcid = author.get('orcid', '')
                    
                    # Extract institutions for this author
                    institutions = []
                    for inst in authorship.get('institutions', []):
                        institutions.append({
                            'id': inst.get('id', '').replace('https://openalex.org/', ''),
                            'display_name': inst.get('display_name', ''),
                            'country_code': inst.get('country_code', ''),
                            'type': inst.get('type', '')
                        })
                    
                    authors.append({
                        'display_name': author_name,
                        'id': author_id,
                        'orcid': orcid,
                        'institutions': institutions,
                        'is_corresponding': authorship.get('is_corresponding', False),
                        'raw_author_name': authorship.get('raw_author_name', '')
                    })
            
            # Extract publication venue
            primary_location = publication.get('primary_location', {})
            source = primary_location.get('source', {}) if primary_location else {}
            
            # Extract concepts/topics
            concepts = []
            for concept in publication.get('concepts', []):
                concepts.append({
                    'id': concept.get('id', '').replace('https://openalex.org/', ''),
                    'display_name': concept.get('display_name', ''),
                    'level': concept.get('level', 0),
                    'score': concept.get('score', 0.0)
                })
            
            # Extract topics
            topics = []
            for topic in publication.get('topics', []):
                topics.append({
                    'id': topic.get('id', '').replace('https://openalex.org/', ''),
                    'display_name': topic.get('display_name', ''),
                    'score': topic.get('score', 0.0)
                })
            
            # Extract bibliographic information
            biblio = publication.get('biblio', {})
            
            # Compile comprehensive publication data
            parsed_publication = {
                'openalex_id': openalex_id,
                'doi': publication.get('doi', ''),
                'title': title,
                'abstract': abstract,
                'authors': authors,
                'publication_year': publication.get('publication_year'),
                'publication_date': publication.get('publication_date'),
                'type': publication.get('type'),
                'cited_by_count': publication.get('cited_by_count', 0),
                'is_retracted': publication.get('is_retracted', False),
                'is_paratext': publication.get('is_paratext', False),
                'language': publication.get('language'),
                
                # Venue information
                'source': {
                    'id': source.get('id', '').replace('https://openalex.org/', '') if source else '',
                    'display_name': source.get('display_name', '') if source else '',
                    'issn_l': source.get('issn_l', '') if source else '',
                    'issn': source.get('issn', []) if source else [],
                    'type': source.get('type', '') if source else '',
                    'host_organization': source.get('host_organization', '') if source else ''
                },
                
                # Bibliographic details
                'volume': biblio.get('volume', ''),
                'issue': biblio.get('issue', ''),
                'first_page': biblio.get('first_page', ''),
                'last_page': biblio.get('last_page', ''),
                
                # Open access information
                'open_access': publication.get('open_access', {}),
                
                # Subject areas
                'concepts': concepts,
                'topics': topics,
                
                # Additional metadata
                'created_date': publication.get('created_date'),
                'updated_date': publication.get('updated_date'),
                'indexed_in': publication.get('indexed_in', []),
                
                # URL and links
                'landing_page_url': primary_location.get('landing_page_url', '') if primary_location else '',
                'pdf_url': primary_location.get('pdf_url', '') if primary_location else '',
                
                # Search metadata
                'retrieved_date': datetime.now().isoformat(),
                'source_database': 'OpenAlex'
            }
            
            return parsed_publication
            
        except Exception as e:
            print(f"⚠️  Error parsing publication: {str(e)}")
            return {}
    
    def save_publication(self, publication: Dict, publication_id: str) -> bool:
        """
        Save individual publication to JSON file
        
        Args:
            publication: Parsed publication data
            publication_id: OpenAlex ID for filename
            
        Returns:
            True if saved successfully
        """
        try:
            # Create output directory
            output_dir = Path('data/publications/openalex')
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save individual publication file
            output_file = output_dir / f"{publication_id}.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(publication, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"⚠️  Error saving publication {publication_id}: {str(e)}")
            return False
    
    def save_faculty_tracking_csv(self, faculty: Dict, author_ids: List[str], institution_ids: List[str]):
        """
        Save faculty tracking CSV with current_affiliation flags
        
        Args:
            faculty: Faculty information dictionary
            author_ids: OpenAlex IDs from author-only search
            institution_ids: OpenAlex IDs from author+institution search
        """
        try:
            faculty_id = faculty.get('faculty_id', '')
            university_code = faculty.get('university_code', '')
            
            # Use the mapper to get the correct folder name
            university_folder_name = self.mapper.get_university_folder(university_code)
            if not university_folder_name:
                print(f"⚠️  Could not determine folder name for university code: {university_code}")
                return
            
            country = faculty.get('country', '')
            province = faculty.get('province', '')
            
            if not all([faculty_id, country, province]):
                print(f"⚠️  Missing required fields for faculty tracking CSV: {faculty}")
                return
            
            # Construct the path using the mapped folder name
            faculty_dir = Path(f'data/faculties/{country}/{province}/{university_folder_name}/publications')
            faculty_dir.mkdir(parents=True, exist_ok=True)
            
            # Create faculty tracking CSV with system name in filename
            csv_file = faculty_dir / f"{faculty_id}_OpenAlex.csv"
            
            # Combine all publication IDs and determine affiliation status
            all_ids = set(author_ids + institution_ids)
            institution_ids_set = set(institution_ids)
            
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['openalex_id', 'current_affiliation'])
                
                for pub_id in sorted(all_ids):
                    current_affiliation = 'TRUE' if pub_id in institution_ids_set else 'FALSE'
                    writer.writerow([pub_id, current_affiliation])
            
            print(f"📄 Saved faculty tracking: {csv_file}")
            
        except Exception as e:
            print(f"⚠️  Error saving faculty tracking CSV: {str(e)}")
    
    def process_faculty_member(self, faculty: Dict, max_results_per_search: int = 100) -> Tuple[int, int]:
        """
        Process a single faculty member with dual search strategy
        
        Args:
            faculty: Faculty information dictionary
            max_results_per_search: Maximum results per search type
            
        Returns:
            Tuple of (total_publications_found, unique_publications_saved)
        """
        name = faculty.get('name', 'Unknown')
        university_name = faculty.get('university_name', 'Unknown University')
        
        print(f"🔍 Searching for {name} ({university_name})")
        
        # Construct search queries
        author_query, institution_query = self.construct_search_queries(faculty)
        
        if not author_query:
            print(f"⚠️  Could not construct valid search query for {name}")
            return 0, 0
        
        print(f"🔎 Author query: {author_query}")
        if institution_query:
            print(f"🏛️  Institution query: {institution_query}")
        
        total_found = 0
        unique_saved = 0
        author_ids = []
        institution_ids = []
        
        # 1. Author-only search
        try:
            print(f"📚 Searching author-only...")
            author_publications = self.search_openalex(author_query, "author", max_results_per_search)
            
            if author_publications:
                self.stats['successful_author_searches'] += 1
                print(f"✅ Found {len(author_publications)} publications (author-only)")
                total_found += len(author_publications)
                
                # Process and save publications
                for pub in author_publications:
                    openalex_id = pub.get('id', '').replace('https://openalex.org/', '')
                    if openalex_id and openalex_id not in self.processed_publications:
                        parsed_pub = self.parse_openalex_publication(pub)
                        if parsed_pub and self.save_publication(parsed_pub, openalex_id):
                            self.processed_publications.add(openalex_id)
                            unique_saved += 1
                    
                    if openalex_id:
                        author_ids.append(openalex_id)
            else:
                print(f"📭 No publications found (author-only)")
                
        except Exception as e:
            print(f"❌ Error in author search: {str(e)}")
            self.stats['failed_searches'] += 1
        
        # 2. Author + Institution search
        if institution_query:
            try:
                print(f"🏛️  Searching author + institution...")
                institution_publications = self.search_openalex(institution_query, "institution", max_results_per_search)
                
                if institution_publications:
                    self.stats['successful_institution_searches'] += 1
                    print(f"✅ Found {len(institution_publications)} publications (author + institution)")
                    total_found += len(institution_publications)
                    
                    # Process and save publications
                    for pub in institution_publications:
                        openalex_id = pub.get('id', '').replace('https://openalex.org/', '')
                        if openalex_id and openalex_id not in self.processed_publications:
                            parsed_pub = self.parse_openalex_publication(pub)
                            if parsed_pub and self.save_publication(parsed_pub, openalex_id):
                                self.processed_publications.add(openalex_id)
                                unique_saved += 1
                        
                        if openalex_id:
                            institution_ids.append(openalex_id)
                else:
                    print(f"📭 No publications found (author + institution)")
                    
            except Exception as e:
                print(f"❌ Error in institution search: {str(e)}")
                self.stats['failed_searches'] += 1
        
        # Save faculty tracking CSV
        self.save_faculty_tracking_csv(faculty, author_ids, institution_ids)
        
        print(f"📊 Saved {unique_saved} unique publications for {name}")
        return total_found, unique_saved
    
    def run(self, csv_file: str, max_faculty: Optional[int] = None, max_results_per_search: int = 100) -> bool:
        """
        Main execution method
        
        Args:
            csv_file: Path to faculty CSV file
            max_faculty: Maximum number of faculty to process (None for all)
            max_results_per_search: Maximum results per search type
            
        Returns:
            True if completed successfully
        """
        print(f"🔬 OpenAlex Faculty Publication Searcher")
        print(f"=" * 50)
        print(f"📁 CSV file: {csv_file}")
        print(f"📧 Email: {self.email}")
        print(f"⏱️  Delay: {self.delay}s")
        if max_faculty:
            print(f"📊 Max faculty: {max_faculty}")
        
        # Load faculty data
        faculty_data = self.load_faculty_data(csv_file)
        if not faculty_data:
            return False
        
        # Limit faculty if specified
        if max_faculty:
            faculty_data = faculty_data[:max_faculty]
            print(f"📊 Processing {len(faculty_data)} faculty members (of {len(self.load_faculty_data(csv_file))} total)")
        else:
            print(f"📊 Processing all {len(faculty_data)} faculty members")
        
        # Process each faculty member
        start_time = datetime.now()
        
        for i, faculty in enumerate(faculty_data, 1):
            print(f"\n{'=' * 60}")
            print(f"Processing faculty {i}/{len(faculty_data)}: {faculty.get('name', 'Unknown')}")
            print(f"{'=' * 60}")
            
            try:
                total_found, unique_saved = self.process_faculty_member(faculty, max_results_per_search)
                
                self.stats['faculty_processed'] += 1
                self.stats['total_publications_found'] += total_found
                self.stats['unique_publications_saved'] += unique_saved
                
                # Progress update
                elapsed = datetime.now() - start_time
                print(f"⏱️  Elapsed: {elapsed}")
                
                # Respect rate limits between faculty
                time.sleep(self.delay)
                
            except KeyboardInterrupt:
                print(f"\n⏹️  Search interrupted by user. Processed {i-1} faculty members.")
                break
            except Exception as e:
                print(f"❌ Error processing faculty {faculty.get('name', 'Unknown')}: {str(e)}")
                continue
        
        # Final statistics
        self.print_final_statistics()
        return True
    
    def print_final_statistics(self):
        """Print final search statistics"""
        print(f"\n🎉 Final Statistics:")
        print(f"=" * 50)
        print(f"Faculty processed: {self.stats['faculty_processed']}")
        print(f"Successful author searches: {self.stats['successful_author_searches']}")
        print(f"Successful institution searches: {self.stats['successful_institution_searches']}")
        print(f"Failed searches: {self.stats['failed_searches']}")
        print(f"Total publications found: {self.stats['total_publications_found']}")
        print(f"Unique publications saved: {self.stats['unique_publications_saved']}")
        print(f"API requests made: {self.stats['api_requests_made']}")
        print(f"Rate limit hits: {self.stats['rate_limit_hits']}")
        print(f"=" * 50)

def main():
    parser = argparse.ArgumentParser(description='Search OpenAlex for faculty publications')
    parser.add_argument('csv_file', help='Path to faculty CSV file')
    parser.add_argument('--max', type=int, help='Maximum number of faculty to process')
    parser.add_argument('--delay', type=float, default=0.5, help='Delay between requests (seconds)')
    parser.add_argument('--email', default='facultyfinder@research.org', help='Email for polite pool')
    parser.add_argument('--max-results', type=int, default=100, help='Maximum results per search type')
    
    args = parser.parse_args()
    
    # Initialize searcher
    searcher = OpenAlexFacultySearcher(email=args.email, delay=args.delay)
    
    # Run the search
    success = searcher.run(
        csv_file=args.csv_file,
        max_faculty=args.max,
        max_results_per_search=args.max_results
    )
    
    if success:
        print("✅ OpenAlex search completed successfully!")
    else:
        print("❌ OpenAlex search failed!")

if __name__ == "__main__":
    main() 