#!/usr/bin/env python3
"""
OpenAlex Author Information Fetcher

This script fetches comprehensive author information from the OpenAlex API
and saves it to structured CSV files as requested:
data/faculties/[country]/[province_state]/[university_code + _ + website]/[university_code + _ + website]_faculty_info_OpenAlex.csv

Usage:
    python3 openalex_author_info_fetcher.py <faculty_csv_file> [options]

Example:
    python3 openalex_author_info_fetcher.py data/faculties/CA/ON/CA-ON-002_mcmaster.ca/mcmaster_hei_faculty.csv --delay 1 --max 10
"""

import os
import sys
import csv
import json
import time
import requests
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from university_folder_mapper import UniversityFolderMapper


class OpenAlexAuthorInfoFetcher:
    def __init__(self, email: str = "facultyfinder@research.org", delay: float = 1.0):
        """
        Initialize the OpenAlex Author Info Fetcher
        
        Args:
            email: Email for OpenAlex API (improves rate limiting)
            delay: Delay between API calls in seconds
        """
        self.email = email
        self.delay = delay
        self.base_url = "https://api.openalex.org/authors"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'FacultyFinder-AuthorInfoFetcher/1.0'
        })
        
        # Initialize the university folder mapper
        self.mapper = UniversityFolderMapper()
        
        # Statistics
        self.stats = {
            'faculty_processed': 0,
            'authors_found': 0,
            'authors_not_found': 0,
            'api_requests': 0,
            'rate_limit_hits': 0,
            'errors': 0
        }

    def load_faculty_data(self, csv_file: str) -> List[Dict]:
        """Load faculty data from CSV file"""
        faculty_data = []
        
        try:
            # Extract country and province from file path if not in CSV
            file_path = Path(csv_file)
            path_parts = file_path.parts
            
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
            
            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Use first_name and last_name instead of name
                    first_name = row.get('first_name', '').strip()
                    last_name = row.get('last_name', '').strip()
                    
                    # Construct full name from first_name and last_name
                    name = f"{first_name} {last_name}".strip()
                    if not name:
                        continue
                    
                    faculty_id = row.get('faculty_id', '').strip()
                    university_name = row.get('university', '').strip()
                    university_code = row.get('university_code', '').strip()
                    
                    # Extract location info from CSV or path
                    country = row.get('country', '').strip() or default_country
                    province = row.get('province_state', '').strip() or default_province
                    
                    faculty_data.append({
                        'name': name,
                        'first_name': first_name,
                        'last_name': last_name,
                        'faculty_id': faculty_id,
                        'university_name': university_name,
                        'university_code': university_code,
                        'country': country,
                        'province': province,
                        'department': row.get('department', '').strip(),
                        'position': row.get('position', '').strip(),
                        'email': row.get('uni_email', row.get('other_email', '')).strip(),
                        'research_areas': row.get('research_areas', '').strip(),
                        'full_time': row.get('full_time', '').strip(),
                        'adjunct': row.get('adjunct', '').strip()
                    })
            
            print(f"📊 Loaded {len(faculty_data)} faculty members from {csv_file}")
            if default_country and default_province:
                print(f"📍 Using path-derived location: {default_country}/{default_province}")
            
            return faculty_data
            
        except Exception as e:
            print(f"❌ Error loading faculty data: {str(e)}")
            return []

    def search_author(self, faculty: Dict) -> Optional[Dict]:
        """
        Search for an author in OpenAlex by name and institution
        
        Args:
            faculty: Faculty information dictionary
            
        Returns:
            Author data if found, None otherwise
        """
        name = faculty['name']
        university_name = faculty['university_name']
        
        try:
            # Construct search queries
            queries = [
                f"{name}",  # Author name only
                f"{name} AND {university_name}" if university_name else f"{name}"  # Author + institution
            ]
            
            for query in queries:
                print(f"🔍 Searching: {query}")
                
                # Make API request
                params = {
                    'search': query,
                    'mailto': self.email,
                    'per-page': 25  # Get more results to find best match
                }
                
                response = self.session.get(self.base_url, params=params)
                self.stats['api_requests'] += 1
                
                if response.status_code == 429:
                    print("⚠️  Rate limit hit, waiting...")
                    self.stats['rate_limit_hits'] += 1
                    time.sleep(30)
                    continue
                elif response.status_code != 200:
                    print(f"⚠️  API error {response.status_code}: {response.text}")
                    continue
                
                data = response.json()
                
                if data.get('results'):
                    # Look for best match (exact name match preferred)
                    for author in data['results']:
                        author_name = author.get('display_name', '')
                        if self._is_name_match(name, author_name):
                            print(f"✅ Found author: {author_name}")
                            return author
                    
                    # If no exact match, return first result
                    first_author = data['results'][0]
                    print(f"🔍 Best match: {first_author.get('display_name', '')}")
                    return first_author
                
                # Delay between requests
                time.sleep(self.delay)
            
            print(f"❌ No author found for: {name}")
            return None
            
        except Exception as e:
            print(f"⚠️  Error searching for {name}: {str(e)}")
            self.stats['errors'] += 1
            return None

    def _is_name_match(self, query_name: str, author_name: str) -> bool:
        """Check if two names are a close match"""
        query_parts = query_name.lower().split()
        author_parts = author_name.lower().split()
        
        # Check if significant parts of the names match
        matches = 0
        for part in query_parts:
            if len(part) > 2:  # Skip very short parts
                for author_part in author_parts:
                    if part in author_part or author_part in part:
                        matches += 1
                        break
        
        # Consider it a match if most name parts are found
        return matches >= max(1, len(query_parts) * 0.6)

    def flatten_author_data(self, author: Dict, faculty: Dict) -> Dict:
        """
        Flatten author data into a single-level dictionary for CSV export
        
        Args:
            author: Author data from OpenAlex API
            faculty: Original faculty data
            
        Returns:
            Flattened dictionary ready for CSV export
        """
        try:
            flattened = {}
            
            # Original faculty information
            flattened['faculty_id'] = faculty.get('faculty_id', '')
            flattened['faculty_name'] = faculty.get('name', '')
            flattened['faculty_first_name'] = faculty.get('first_name', '')
            flattened['faculty_last_name'] = faculty.get('last_name', '')
            flattened['faculty_department'] = faculty.get('department', '')
            flattened['faculty_position'] = faculty.get('position', '')
            flattened['faculty_email'] = faculty.get('email', '')
            flattened['faculty_research_areas'] = faculty.get('research_areas', '')
            flattened['faculty_full_time'] = faculty.get('full_time', '')
            flattened['faculty_adjunct'] = faculty.get('adjunct', '')
            flattened['faculty_university_name'] = faculty.get('university_name', '')
            flattened['faculty_university_code'] = faculty.get('university_code', '')
            flattened['faculty_country'] = faculty.get('country', '')
            flattened['faculty_province'] = faculty.get('province', '')
            
            # Basic author information
            flattened['openalex_id'] = author.get('id', '')
            flattened['orcid'] = author.get('orcid', '')
            flattened['display_name'] = author.get('display_name', '')
            flattened['display_name_alternatives'] = '|'.join(author.get('display_name_alternatives', []))
            
            # Statistics
            flattened['works_count'] = author.get('works_count', 0)
            flattened['cited_by_count'] = author.get('cited_by_count', 0)
            
            # Summary statistics
            summary_stats = author.get('summary_stats', {})
            flattened['2yr_mean_citedness'] = summary_stats.get('2yr_mean_citedness', 0)
            flattened['h_index'] = summary_stats.get('h_index', 0)
            flattened['i10_index'] = summary_stats.get('i10_index', 0)
            
            # External IDs
            ids = author.get('ids', {})
            flattened['openalex_canonical_id'] = ids.get('openalex', '')
            flattened['mag_id'] = ids.get('mag', '')
            flattened['scopus_id'] = ids.get('scopus', '')
            flattened['twitter_id'] = ids.get('twitter', '')
            flattened['wikipedia_id'] = ids.get('wikipedia', '')
            
            # Current/last known affiliations
            last_institutions = author.get('last_known_institutions', [])
            if last_institutions:
                inst = last_institutions[0]
                flattened['last_known_institution_id'] = inst.get('id', '')
                flattened['last_known_institution_name'] = inst.get('display_name', '')
                flattened['last_known_institution_ror'] = inst.get('ror', '')
                flattened['last_known_institution_country'] = inst.get('country_code', '')
                flattened['last_known_institution_type'] = inst.get('type', '')
            else:
                flattened['last_known_institution_id'] = ''
                flattened['last_known_institution_name'] = ''
                flattened['last_known_institution_ror'] = ''
                flattened['last_known_institution_country'] = ''
                flattened['last_known_institution_type'] = ''
            
            # All affiliations (compressed)
            affiliations = author.get('affiliations', [])
            affiliation_names = []
            affiliation_years = []
            for aff in affiliations[:5]:  # Limit to first 5 affiliations
                inst = aff.get('institution', {})
                affiliation_names.append(inst.get('display_name', ''))
                years = aff.get('years', [])
                affiliation_years.append(f"{min(years) if years else ''}-{max(years) if years else ''}")
            
            flattened['affiliations_names'] = '|'.join(affiliation_names)
            flattened['affiliations_years'] = '|'.join(affiliation_years)
            
            # Top research topics
            topics = author.get('topics', [])
            topic_names = []
            topic_counts = []
            topic_fields = []
            topic_domains = []
            
            for topic in topics[:10]:  # Top 10 topics
                topic_names.append(topic.get('display_name', ''))
                topic_counts.append(str(topic.get('count', 0)))
                
                field = topic.get('field', {})
                topic_fields.append(field.get('display_name', ''))
                
                domain = topic.get('domain', {})
                topic_domains.append(domain.get('display_name', ''))
            
            flattened['top_topics_names'] = '|'.join(topic_names)
            flattened['top_topics_counts'] = '|'.join(topic_counts)
            flattened['top_topics_fields'] = '|'.join(topic_fields)
            flattened['top_topics_domains'] = '|'.join(topic_domains)
            
            # Topic shares (research focus distribution)
            topic_shares = author.get('topic_share', [])
            share_topics = []
            share_values = []
            for share in topic_shares[:5]:  # Top 5 topic shares
                share_topics.append(share.get('display_name', ''))
                share_values.append(str(round(share.get('value', 0), 4)))
            
            flattened['topic_share_names'] = '|'.join(share_topics)
            flattened['topic_share_values'] = '|'.join(share_values)
            
            # Legacy concepts (top 5)
            x_concepts = author.get('x_concepts', [])
            concept_names = []
            concept_scores = []
            for concept in x_concepts[:5]:
                concept_names.append(concept.get('display_name', ''))
                concept_scores.append(str(round(concept.get('score', 0), 2)))
            
            flattened['x_concepts_names'] = '|'.join(concept_names)
            flattened['x_concepts_scores'] = '|'.join(concept_scores)
            
            # Publication and citation trends (last 5 years)
            counts_by_year = author.get('counts_by_year', [])
            recent_years = []
            recent_works = []
            recent_citations = []
            
            for year_data in counts_by_year[:5]:  # Last 5 years
                recent_years.append(str(year_data.get('year', '')))
                recent_works.append(str(year_data.get('works_count', 0)))
                recent_citations.append(str(year_data.get('cited_by_count', 0)))
            
            flattened['recent_years'] = '|'.join(recent_years)
            flattened['recent_works_counts'] = '|'.join(recent_works)
            flattened['recent_citations_counts'] = '|'.join(recent_citations)
            
            # API and meta information
            flattened['works_api_url'] = author.get('works_api_url', '')
            flattened['updated_date'] = author.get('updated_date', '')
            flattened['created_date'] = author.get('created_date', '')
            
            # Fetch timestamp
            flattened['data_fetched_at'] = datetime.now().isoformat()
            
            return flattened
            
        except Exception as e:
            print(f"⚠️  Error flattening author data: {str(e)}")
            return {}

    def save_author_info_csv(self, faculty_data: List[Dict], university_code: str, country: str, province: str):
        """
        Save author information to CSV file
        
        Args:
            faculty_data: List of faculty with their author information
            university_code: University code for folder naming
            country: Country code
            province: Province/state code
        """
        try:
            # Use the mapper to get the correct folder name
            university_folder_name = self.mapper.get_university_folder(university_code)
            if not university_folder_name:
                print(f"⚠️  Could not determine folder name for university code: {university_code}")
                return
            
            # Create directory path
            faculty_dir = Path(f'data/faculties/{country}/{province}/{university_folder_name}')
            faculty_dir.mkdir(parents=True, exist_ok=True)
            
            # Create CSV filename
            csv_file = faculty_dir / f"{university_folder_name}_faculty_info_OpenAlex.csv"
            
            if not faculty_data:
                print(f"⚠️  No faculty data to save")
                return
            
            # Get all possible field names from the data
            all_fields = set()
            for faculty in faculty_data:
                if 'author_info' in faculty:
                    all_fields.update(faculty['author_info'].keys())
            
            # Define field order (put most important fields first)
            priority_fields = [
                'faculty_id', 'faculty_name', 'faculty_first_name', 'faculty_last_name', 
                'faculty_department', 'faculty_position',
                'openalex_id', 'orcid', 'display_name', 'works_count', 'cited_by_count',
                'h_index', 'i10_index', '2yr_mean_citedness',
                'last_known_institution_name', 'last_known_institution_country',
                'top_topics_names', 'top_topics_fields', 'affiliations_names'
            ]
            
            # Create final field list
            fieldnames = []
            # Add priority fields first
            for field in priority_fields:
                if field in all_fields:
                    fieldnames.append(field)
                    all_fields.remove(field)
            # Add remaining fields
            fieldnames.extend(sorted(all_fields))
            
            # Write CSV file
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
                writer.writeheader()
                
                for faculty in faculty_data:
                    if 'author_info' in faculty:
                        writer.writerow(faculty['author_info'])
            
            print(f"💾 Saved author information: {csv_file}")
            print(f"📊 Fields included: {len(fieldnames)}")
            
        except Exception as e:
            print(f"⚠️  Error saving author info CSV: {str(e)}")

    def process_faculty_list(self, faculty_data: List[Dict], max_faculty: Optional[int] = None):
        """
        Process a list of faculty members to fetch their OpenAlex author information
        
        Args:
            faculty_data: List of faculty dictionaries
            max_faculty: Maximum number of faculty to process (for testing)
        """
        if not faculty_data:
            print("❌ No faculty data to process")
            return
        
        # Limit number of faculty if specified
        if max_faculty:
            faculty_data = faculty_data[:max_faculty]
            print(f"📊 Processing {len(faculty_data)} faculty members (of {max_faculty} total)")
        else:
            print(f"📊 Processing {len(faculty_data)} faculty members")
        
        start_time = datetime.now()
        
        for i, faculty in enumerate(faculty_data, 1):
            print(f"\n{'='*60}")
            print(f"Processing faculty {i}/{len(faculty_data)}: {faculty['name']}")
            print(f"{'='*60}")
            
            # Search for author in OpenAlex
            author_data = self.search_author(faculty)
            
            if author_data:
                # Flatten author data for CSV export
                flattened_data = self.flatten_author_data(author_data, faculty)
                faculty['author_info'] = flattened_data
                self.stats['authors_found'] += 1
                print(f"📊 Author info extracted: {len(flattened_data)} fields")
            else:
                # Create empty record for faculty not found
                faculty['author_info'] = self.flatten_author_data({}, faculty)
                self.stats['authors_not_found'] += 1
            
            self.stats['faculty_processed'] += 1
            
            # Progress update
            elapsed = datetime.now() - start_time
            print(f"⏱️  Elapsed: {elapsed}")
        
        # Save results to CSV
        if faculty_data:
            # Extract university info for file naming
            first_faculty = faculty_data[0]
            university_code = first_faculty.get('university_code', '')
            country = first_faculty.get('country', '')
            province = first_faculty.get('province', '')
            
            if university_code and country and province:
                self.save_author_info_csv(faculty_data, university_code, country, province)
            else:
                print("⚠️  Missing university/location information for file naming")

    def print_final_stats(self):
        """Print final statistics"""
        print(f"\n🎉 Final Statistics:")
        print(f"{'='*50}")
        print(f"Faculty processed: {self.stats['faculty_processed']}")
        print(f"Authors found: {self.stats['authors_found']}")
        print(f"Authors not found: {self.stats['authors_not_found']}")
        print(f"API requests made: {self.stats['api_requests']}")
        print(f"Rate limit hits: {self.stats['rate_limit_hits']}")
        print(f"Errors: {self.stats['errors']}")
        print(f"{'='*50}")
        
        if self.stats['faculty_processed'] > 0:
            success_rate = (self.stats['authors_found'] / self.stats['faculty_processed']) * 100
            print(f"✅ Author discovery rate: {success_rate:.1f}%")


def main():
    parser = argparse.ArgumentParser(description='Fetch comprehensive author information from OpenAlex')
    parser.add_argument('csv_file', help='Path to faculty CSV file')
    parser.add_argument('--email', default='facultyfinder@research.org', help='Email for API requests')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay between API calls (seconds)')
    parser.add_argument('--max', type=int, help='Maximum number of faculty to process (for testing)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.csv_file):
        print(f"❌ CSV file not found: {args.csv_file}")
        sys.exit(1)
    
    print(f"🔬 OpenAlex Author Information Fetcher")
    print(f"{'='*50}")
    print(f"📁 CSV file: {args.csv_file}")
    print(f"📧 Email: {args.email}")
    print(f"⏱️  Delay: {args.delay}s")
    if args.max:
        print(f"📊 Max faculty: {args.max}")
    
    # Initialize fetcher
    fetcher = OpenAlexAuthorInfoFetcher(email=args.email, delay=args.delay)
    
    try:
        # Load faculty data
        faculty_data = fetcher.load_faculty_data(args.csv_file)
        
        if not faculty_data:
            print("❌ No faculty data loaded")
            sys.exit(1)
        
        # Process faculty list
        fetcher.process_faculty_list(faculty_data, args.max)
        
        # Print final statistics
        fetcher.print_final_stats()
        
        print(f"\n✅ OpenAlex author information fetching completed successfully!")
        
    except KeyboardInterrupt:
        print(f"\n⚠️  Process interrupted by user")
        fetcher.print_final_stats()
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        fetcher.print_final_stats()
        sys.exit(1)


if __name__ == "__main__":
    main() 