#!/usr/bin/env python3
"""
Scopus Faculty Publication Searcher

This script searches Scopus for faculty publications using the Scopus Search API.
It reads faculty data from CSV files and performs comprehensive searches with both
author-only and author+affiliation queries, similar to our PubMed system.

Updated to use proper university_code_website folder naming convention.

Features:
- Reads faculty data from structured CSV files
- Performs dual search strategies (author-only vs author+affiliation)
- Saves individual publication files as [scopus_id].json
- Creates faculty tracking CSVs with current_affiliation flags
- Supports resumable searches with progress tracking
- Extracts comprehensive metadata including abstracts, author details, affiliations
- Rate limiting to respect Scopus API quotas

Usage:
    python3 scopus_faculty_searcher.py <csv_file> [options]
    
Example:
    python3 scopus_faculty_searcher.py data/faculties/CA/ON/CA-ON-002_mcmaster.ca/mcmaster_hei_faculty.csv --max 5 --delay 2
"""

import json
import csv
import requests
import time
import argparse
import os
import sys
import re
from pathlib import Path
from urllib.parse import quote_plus
from typing import Dict, List, Optional, Tuple
from university_folder_mapper import get_faculty_publications_path

class ScopusFacultySearcher:
    def __init__(self, api_key: str, delay: float = 1.0):
        """
        Initialize the Scopus searcher
        
        Args:
            api_key: Scopus API key
            delay: Delay between requests in seconds
        """
        self.api_key = api_key
        self.delay = delay
        self.base_url = "https://api.elsevier.com/content/search/scopus"
        self.abstract_url = "https://api.elsevier.com/content/abstract"
        self.session = requests.Session()
        self.session.headers.update({
            'X-ELS-APIKey': api_key,
            'Accept': 'application/json',
            'User-Agent': 'FacultyFinder-ScopusSearcher/1.0'
        })
        
        # Statistics tracking
        self.stats = {
            'total_faculty': 0,
            'processed_faculty': 0,
            'successful_author_searches': 0,
            'successful_affiliation_searches': 0,
            'failed_searches': 0,
            'total_publications_found': 0,
            'unique_publications_saved': 0,
            'api_requests_made': 0,
            'rate_limit_hits': 0
        }
    
    def load_faculty_data(self, csv_file: str) -> List[Dict]:
        """Load faculty data from CSV file"""
        faculty_data = []
        
        try:
            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    faculty_data.append({
                        'faculty_id': row.get('faculty_id', '').strip(),
                        'name': row.get('name', '').strip(),
                        'first_name': row.get('first_name', '').strip(),
                        'last_name': row.get('last_name', '').strip(),
                        'university_code': row.get('university_code', '').strip(),
                        'university': row.get('university', '').strip(),
                        'university_name': row.get('university', 'Unknown University').strip(),  # Use 'university' field
                        'country': row.get('country', '').strip(),
                        'province': row.get('province_state', '').strip(),
                        'department': row.get('department', '').strip()
                    })
        except Exception as e:
            print(f"❌ Error loading CSV file: {str(e)}")
            return []
        
        print(f"📊 Loaded {len(faculty_data)} faculty members from {csv_file}")
        return faculty_data
    
    def construct_search_queries(self, faculty: Dict) -> Tuple[str, str]:
        """
        Construct Scopus search queries for author-only and author+affiliation
        
        Returns:
            Tuple of (author_query, affiliation_query)
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
        
        # Get first initial
        first_initial = author_first[0] if author_first else ""
        
        # Construct author search query (multiple name formats)
        # Scopus uses AUTH() syntax, not AUTHOR-NAME()
        author_queries = []
        
        if first_initial and author_last:
            # Format: "Last, F."
            author_queries.append(f'AUTH("{author_last}, {first_initial}.")')
            # Format: "Last, First"  
            if len(author_first) > 1:
                author_queries.append(f'AUTH("{author_last}, {author_first}")')
            # Alternative format without comma
            author_queries.append(f'AUTH("{author_first} {author_last}")')
        
        # Join with OR
        author_query = ' OR '.join(author_queries) if author_queries else ""
        
        # Construct affiliation query
        affiliation_query = ""
        if author_query and university_name and university_name != "Unknown University":
            # Clean university name for search - Scopus uses AFFIL() syntax
            # Keep the full university name for better matching
            univ_search = university_name.replace("University of ", "").strip()
            # Remove trailing "University" only if it makes the name too short
            if univ_search.endswith(" University") and len(univ_search) > 15:
                univ_search = univ_search.replace(" University", "")
            affiliation_query = f"({author_query}) AND AFFIL({univ_search})"
        
        return author_query, affiliation_query
    
    def search_scopus(self, query: str, max_results: int = 200) -> List[Dict]:
        """
        Search Scopus using the Search API
        
        Args:
            query: Scopus search query
            max_results: Maximum results to retrieve
            
        Returns:
            List of publication dictionaries
        """
        if not query:
            return []
        
        publications = []
        start = 0
        count = min(25, max_results)  # Scopus API default/max per request
        
        while start < max_results:
            try:
                params = {
                    'query': query,
                    'start': start,
                    'count': count,
                    'view': 'COMPLETE',  # Get comprehensive metadata
                    'field': 'dc:identifier,eid,dc:title,dc:description,dc:creator,author,affiliation,prism:publicationName,prism:coverDate,prism:volume,prism:issueIdentifier,prism:pageRange,prism:doi,citedby-count,prism:aggregationType,subtype,subtypeDescription,authkeywords,subject-area'
                }
                
                response = self.session.get(self.base_url, params=params)
                self.stats['api_requests_made'] += 1
                
                if response.status_code == 429:
                    self.stats['rate_limit_hits'] += 1
                    print(f"⏳ Rate limit hit, waiting 30 seconds...")
                    time.sleep(30)
                    continue
                
                response.raise_for_status()
                data = response.json()
                
                search_results = data.get('search-results', {})
                entries = search_results.get('entry', [])
                
                if not entries:
                    break
                
                publications.extend(entries)
                
                # Check if we have more results
                total_results = int(search_results.get('opensearch:totalResults', 0))
                start += count
                
                if start >= total_results or len(entries) < count:
                    break
                
                # Respect rate limits
                time.sleep(self.delay)
                
            except requests.exceptions.RequestException as e:
                # Check for specific error types
                if hasattr(e, 'response') and e.response is not None:
                    status_code = e.response.status_code
                    if status_code == 403:
                        print(f"❌ Scopus API Access Denied (403 Forbidden)")
                        print(f"   💡 This is likely due to IP-based access restrictions")
                        print(f"   🔧 Solutions:")
                        print(f"      1. Contact your institution's library to register this IP")
                        print(f"      2. Use the local export script from an institutional network")
                        print(f"      3. Check if your API key has proper permissions")
                        print(f"   📧 Contact: apisupport@elsevier.com with your API key")
                    elif status_code == 401:
                        print(f"❌ Scopus API Authentication Error (401)")
                        print(f"   🔑 Check if your API key is valid and active")
                    elif status_code == 429:
                        print(f"❌ Scopus API Rate Limit Exceeded (429)")
                        print(f"   ⏳ Wait for quota reset or increase delay")
                    else:
                        print(f"❌ Scopus search error (HTTP {status_code}): {str(e)}")
                else:
                    print(f"❌ Scopus search error: {str(e)}")
                break
            except Exception as e:
                print(f"❌ Unexpected error in search: {str(e)}")
                break
        
        return publications
    
    def get_abstract_details(self, scopus_id: str) -> Dict:
        """
        Get detailed abstract information using Abstract Retrieval API
        
        Args:
            scopus_id: Scopus identifier
            
        Returns:
            Detailed publication dictionary
        """
        try:
            url = f"{self.abstract_url}/scopus_id/{scopus_id}"
            params = {
                'view': 'FULL',
                'field': 'dc:identifier,eid,dc:title,dc:description,dc:creator,authors,affiliation,prism:publicationName,prism:coverDate,prism:volume,prism:issueIdentifier,prism:pageRange,prism:doi,citedby-count,prism:aggregationType,subtype,subtypeDescription,authkeywords,subject-areas,item'
            }
            
            response = self.session.get(url, params=params)
            self.stats['api_requests_made'] += 1
            
            if response.status_code == 429:
                self.stats['rate_limit_hits'] += 1
                print(f"⏳ Rate limit hit, waiting 30 seconds...")
                time.sleep(30)
                return {}
            
            response.raise_for_status()
            data = response.json()
            
            # Extract the abstract response
            abstract_response = data.get('abstracts-retrieval-response', {})
            return abstract_response
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error getting abstract details for {scopus_id}: {str(e)}")
            return {}
        except Exception as e:
            print(f"❌ Unexpected error getting abstract for {scopus_id}: {str(e)}")
            return {}
    
    def parse_scopus_publication(self, entry: Dict, detailed_abstract: Dict = None) -> Dict:
        """
        Parse a Scopus publication entry into a comprehensive JSON structure
        
        Args:
            entry: Basic entry from search results
            detailed_abstract: Detailed data from Abstract Retrieval API
            
        Returns:
            Comprehensive publication dictionary
        """
        # Use detailed abstract if available, otherwise use search entry
        source_data = detailed_abstract if detailed_abstract else entry
        
        # Extract basic identifiers
        scopus_id = entry.get('dc:identifier', '').replace('SCOPUS_ID:', '')
        eid = entry.get('eid', '')
        
        # Extract title and abstract
        title = source_data.get('dc:title', entry.get('dc:title', ''))
        abstract = source_data.get('dc:description', entry.get('dc:description', ''))
        
        # Parse authors
        authors = []
        if detailed_abstract:
            # Use detailed author information
            author_group = detailed_abstract.get('authors', {}).get('author', [])
            if not isinstance(author_group, list):
                author_group = [author_group]
        else:
            # Use search result author information
            author_group = entry.get('author', [])
            if not isinstance(author_group, list):
                author_group = [author_group]
        
        for author in author_group:
            if isinstance(author, dict):
                author_info = {
                    'authid': author.get('@auid', author.get('authid', '')),
                    'orcid': author.get('@orcid', author.get('orcid', '')),
                    'surname': author.get('ce:surname', author.get('surname', '')),
                    'given_name': author.get('ce:given-name', author.get('given-name', '')),
                    'initials': author.get('ce:initials', author.get('initials', '')),
                    'indexed_name': author.get('ce:indexed-name', author.get('authname', '')),
                    'affiliations': []
                }
                
                # Parse affiliations for this author
                author_affils = author.get('affiliation', [])
                if not isinstance(author_affils, list):
                    author_affils = [author_affils]
                
                for affil in author_affils:
                    if isinstance(affil, dict):
                        affil_info = {
                            'afid': affil.get('@id', affil.get('afid', '')),
                            'name': affil.get('affilname', affil.get('@affilname', '')),
                            'city': affil.get('affiliation-city', ''),
                            'country': affil.get('affiliation-country', '')
                        }
                        author_info['affiliations'].append(affil_info)
                
                authors.append(author_info)
        
        # Extract journal information
        journal_info = {
            'name': source_data.get('prism:publicationName', entry.get('prism:publicationName', '')),
            'issn': source_data.get('prism:issn', entry.get('prism:issn', '')),
            'volume': source_data.get('prism:volume', entry.get('prism:volume', '')),
            'issue': source_data.get('prism:issueIdentifier', entry.get('prism:issueIdentifier', '')),
            'pages': source_data.get('prism:pageRange', entry.get('prism:pageRange', '')),
            'cover_date': source_data.get('prism:coverDate', entry.get('prism:coverDate', '')),
            'aggregation_type': source_data.get('prism:aggregationType', entry.get('prism:aggregationType', ''))
        }
        
        # Extract publication type
        pub_type = {
            'type': source_data.get('subtype', entry.get('subtype', '')),
            'description': source_data.get('subtypeDescription', entry.get('subtypeDescription', ''))
        }
        
        # Extract keywords
        keywords = []
        authkeywords = source_data.get('authkeywords', entry.get('authkeywords', ''))
        if authkeywords:
            if isinstance(authkeywords, str):
                keywords = [kw.strip() for kw in authkeywords.split('|') if kw.strip()]
            elif isinstance(authkeywords, list):
                keywords = authkeywords
        
        # Extract subject areas
        subject_areas = []
        subj_areas = source_data.get('subject-area', entry.get('subject-area', []))
        if not isinstance(subj_areas, list):
            subj_areas = [subj_areas]
        
        for subj in subj_areas:
            if isinstance(subj, dict):
                subject_areas.append({
                    'code': subj.get('@code', ''),
                    'abbreviation': subj.get('@abbrev', ''),
                    'name': subj.get('$', '')
                })
        
        # Extract citation count
        citation_count = 0
        citedby = source_data.get('citedby-count', entry.get('citedby-count', '0'))
        try:
            citation_count = int(citedby) if citedby else 0
        except (ValueError, TypeError):
            citation_count = 0
        
        # Extract DOI
        doi = source_data.get('prism:doi', entry.get('prism:doi', ''))
        
        # Parse publication year
        pub_year = None
        cover_date = journal_info['cover_date']
        if cover_date:
            try:
                pub_year = int(cover_date.split('-')[0])
            except (ValueError, IndexError):
                pass
        
        # Build comprehensive publication dictionary
        publication = {
            'scopus_id': scopus_id,
            'eid': eid,
            'title': title,
            'abstract': abstract,
            'authors': authors,
            'journal': journal_info,
            'publication_type': pub_type,
            'keywords': keywords,
            'subject_areas': subject_areas,
            'doi': doi,
            'publication_year': pub_year,
            'citation_count': citation_count,
            'source': 'scopus'
        }
        
        return publication
    
    def save_publication(self, publication: Dict) -> bool:
        """
        Save a publication as a JSON file
        
        Args:
            publication: Publication dictionary
            
        Returns:
            True if saved successfully, False otherwise
        """
        scopus_id = publication.get('scopus_id', '')
        if not scopus_id:
            return False
        
        # Create publications directory
        pub_dir = Path('data/publications/scopus')
        pub_dir.mkdir(parents=True, exist_ok=True)
        
        # Save as [scopus_id].json
        filename = f"{scopus_id}.json"
        filepath = pub_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(publication, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"❌ Error saving publication {scopus_id}: {str(e)}")
            return False
    
    def save_faculty_tracking_csv(self, faculty: Dict, author_pmids: List[str], affiliation_pmids: List[str]):
        """
        Save faculty tracking CSV with publication IDs and affiliation flags
        
        Args:
            faculty: Faculty information
            author_pmids: Scopus IDs from author-only search
            affiliation_pmids: Scopus IDs from author+affiliation search
        """
        faculty_id = faculty.get('faculty_id', '')
        
        if not faculty_id:
            print(f"⚠️  Missing faculty_id for faculty tracking CSV: {faculty}")
            return
        
        # Use the university folder mapper for correct folder naming
        faculty_dir = Path(get_faculty_publications_path(faculty))
        faculty_dir.mkdir(parents=True, exist_ok=True)
        
        # Combine all unique Scopus IDs
        all_scopus_ids = set(author_pmids + affiliation_pmids)
        
        # Create tracking data
        tracking_data = []
        for scopus_id in all_scopus_ids:
            current_affiliation = scopus_id in affiliation_pmids
            tracking_data.append({
                'scopus_id': scopus_id,
                'current_affiliation': 'TRUE' if current_affiliation else 'FALSE'
            })
        
        # Sort by Scopus ID
        tracking_data.sort(key=lambda x: x['scopus_id'])
        
        # Save CSV
        csv_file = faculty_dir / f"{faculty_id}.csv"
        try:
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['scopus_id', 'current_affiliation'])
                writer.writeheader()
                writer.writerows(tracking_data)
            
            print(f"📊 Saved {len(tracking_data)} publications for {faculty.get('name', 'Unknown')} ({faculty_id})")
        except Exception as e:
            print(f"❌ Error saving faculty tracking CSV for {faculty_id}: {str(e)}")
    
    def search_faculty_publications(self, faculty: Dict) -> Tuple[List[str], List[str]]:
        """
        Search for a faculty member's publications
        
        Args:
            faculty: Faculty information dictionary
            
        Returns:
            Tuple of (author_only_scopus_ids, affiliation_scopus_ids)
        """
        faculty_name = faculty.get('name', 'Unknown')
        university = faculty.get('university_name', 'Unknown University')
        
        print(f"\n🔍 Searching for {faculty_name} ({university})")
        
        # Construct search queries
        author_query, affiliation_query = self.construct_search_queries(faculty)
        
        if not author_query:
            print(f"⚠️  Could not construct search query for {faculty_name}")
            self.stats['failed_searches'] += 1
            return [], []
        
        print(f"🔎 Author query: {author_query}")
        if affiliation_query:
            print(f"🔎 Affiliation query: {affiliation_query}")
        
        # Search author-only
        author_publications = self.search_scopus(author_query)
        author_scopus_ids = []
        
        if author_publications:
            self.stats['successful_author_searches'] += 1
            print(f"📚 Found {len(author_publications)} publications (author-only)")
            
            for pub_entry in author_publications:
                scopus_id = pub_entry.get('dc:identifier', '').replace('SCOPUS_ID:', '')
                if scopus_id:
                    author_scopus_ids.append(scopus_id)
                    
                    # Get detailed abstract if available
                    detailed_abstract = {}
                    if scopus_id:
                        detailed_abstract = self.get_abstract_details(scopus_id)
                        time.sleep(self.delay)  # Rate limiting
                    
                    # Parse and save publication
                    publication = self.parse_scopus_publication(pub_entry, detailed_abstract)
                    if self.save_publication(publication):
                        self.stats['unique_publications_saved'] += 1
        else:
            print(f"📚 No publications found (author-only)")
        
        # Search with affiliation
        affiliation_scopus_ids = []
        if affiliation_query:
            time.sleep(self.delay)  # Rate limiting between searches
            
            affiliation_publications = self.search_scopus(affiliation_query)
            
            if affiliation_publications:
                self.stats['successful_affiliation_searches'] += 1
                print(f"🏛️  Found {len(affiliation_publications)} publications (with affiliation)")
                
                for pub_entry in affiliation_publications:
                    scopus_id = pub_entry.get('dc:identifier', '').replace('SCOPUS_ID:', '')
                    if scopus_id:
                        affiliation_scopus_ids.append(scopus_id)
                        
                        # Only get details and save if we haven't already processed this publication
                        if scopus_id not in author_scopus_ids:
                            # Get detailed abstract if available
                            detailed_abstract = {}
                            if scopus_id:
                                detailed_abstract = self.get_abstract_details(scopus_id)
                                time.sleep(self.delay)  # Rate limiting
                            
                            # Parse and save publication
                            publication = self.parse_scopus_publication(pub_entry, detailed_abstract)
                            if self.save_publication(publication):
                                self.stats['unique_publications_saved'] += 1
            else:
                print(f"🏛️  No publications found (with affiliation)")
        
        # Update statistics
        self.stats['total_publications_found'] += len(author_scopus_ids) + len([sid for sid in affiliation_scopus_ids if sid not in author_scopus_ids])
        
        return author_scopus_ids, affiliation_scopus_ids
    
    def process_faculty_list(self, faculty_list: List[Dict], max_faculty: Optional[int] = None, 
                           start_from: Optional[str] = None):
        """
        Process a list of faculty members
        
        Args:
            faculty_list: List of faculty dictionaries
            max_faculty: Maximum number of faculty to process
            start_from: Faculty name to start from (for resuming)
        """
        self.stats['total_faculty'] = len(faculty_list)
        
        # Find starting position if specified
        start_idx = 0
        if start_from:
            for i, faculty in enumerate(faculty_list):
                if faculty.get('name', '').lower() == start_from.lower():
                    start_idx = i
                    break
            print(f"🔄 Resuming from faculty #{start_idx + 1}: {start_from}")
        
        # Limit faculty count if specified
        end_idx = len(faculty_list)
        if max_faculty:
            end_idx = min(start_idx + max_faculty, len(faculty_list))
            print(f"📊 Processing {end_idx - start_idx} faculty members (of {len(faculty_list)} total)")
        
        # Process each faculty member
        for i in range(start_idx, end_idx):
            faculty = faculty_list[i]
            faculty_name = faculty.get('name', f'Faculty_{i}')
            
            try:
                print(f"\n{'='*60}")
                print(f"Processing faculty {i + 1}/{len(faculty_list)}: {faculty_name}")
                print(f"{'='*60}")
                
                # Search for publications
                author_scopus_ids, affiliation_scopus_ids = self.search_faculty_publications(faculty)
                
                # Save faculty tracking CSV
                self.save_faculty_tracking_csv(faculty, author_scopus_ids, affiliation_scopus_ids)
                
                self.stats['processed_faculty'] += 1
                
                # Progress update
                if (i + 1) % 5 == 0:
                    self.print_progress_stats()
                
                # Rate limiting between faculty
                time.sleep(self.delay)
                
            except KeyboardInterrupt:
                print(f"\n⏹️  Search interrupted by user. Processed {self.stats['processed_faculty']} faculty members.")
                break
            except Exception as e:
                print(f"❌ Error processing {faculty_name}: {str(e)}")
                self.stats['failed_searches'] += 1
                continue
    
    def print_progress_stats(self):
        """Print current progress statistics"""
        print(f"\n📊 Progress Statistics:")
        print(f"   Faculty processed: {self.stats['processed_faculty']}/{self.stats['total_faculty']}")
        print(f"   Successful author searches: {self.stats['successful_author_searches']}")
        print(f"   Successful affiliation searches: {self.stats['successful_affiliation_searches']}")
        print(f"   Total publications found: {self.stats['total_publications_found']}")
        print(f"   Unique publications saved: {self.stats['unique_publications_saved']}")
        print(f"   API requests made: {self.stats['api_requests_made']}")
        print(f"   Rate limit hits: {self.stats['rate_limit_hits']}")
    
    def print_final_stats(self):
        """Print final statistics"""
        print(f"\n🎉 Final Statistics:")
        print(f"{'='*50}")
        print(f"Faculty processed: {self.stats['processed_faculty']}/{self.stats['total_faculty']}")
        print(f"Successful author searches: {self.stats['successful_author_searches']}")
        print(f"Successful affiliation searches: {self.stats['successful_affiliation_searches']}")
        print(f"Failed searches: {self.stats['failed_searches']}")
        print(f"Total publications found: {self.stats['total_publications_found']}")
        print(f"Unique publications saved: {self.stats['unique_publications_saved']}")
        print(f"API requests made: {self.stats['api_requests_made']}")
        print(f"Rate limit hits: {self.stats['rate_limit_hits']}")
        print(f"{'='*50}")


def main():
    parser = argparse.ArgumentParser(description='Search Scopus for faculty publications')
    parser.add_argument('csv_file', help='Path to faculty CSV file')
    parser.add_argument('--api-key', default='a40794bde2315194803ca0422b5fe851', 
                       help='Scopus API key')
    parser.add_argument('--max', type=int, help='Maximum number of faculty to process')
    parser.add_argument('--delay', type=float, default=1.0, 
                       help='Delay between requests in seconds (default: 1.0)')
    parser.add_argument('--start-from', help='Faculty name to start from (for resuming)')
    
    args = parser.parse_args()
    
    # Validate CSV file
    if not os.path.exists(args.csv_file):
        print(f"❌ CSV file not found: {args.csv_file}")
        sys.exit(1)
    
    print("🔬 Scopus Faculty Publication Searcher")
    print("=" * 50)
    print(f"📁 CSV file: {args.csv_file}")
    print(f"🔑 API key: {args.api_key[:10]}...")
    print(f"⏱️  Delay: {args.delay}s")
    if args.max:
        print(f"📊 Max faculty: {args.max}")
    if args.start_from:
        print(f"🔄 Starting from: {args.start_from}")
    print()
    
    # Initialize searcher
    searcher = ScopusFacultySearcher(args.api_key, args.delay)
    
    # Load faculty data
    faculty_data = searcher.load_faculty_data(args.csv_file)
    if not faculty_data:
        print("❌ No faculty data loaded. Exiting.")
        sys.exit(1)
    
    # Process faculty
    try:
        searcher.process_faculty_list(faculty_data, args.max, args.start_from)
    except KeyboardInterrupt:
        print("\n⏹️  Search interrupted by user.")
    finally:
        searcher.print_final_stats()


if __name__ == "__main__":
    main() 