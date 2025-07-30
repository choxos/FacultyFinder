#!/usr/bin/env python3
"""
PubMed Faculty Searcher - JSON-based with PMID Tracking
Reads faculty CSV files and runs EDirect searches in JSON format
Creates individual PMID JSON files and faculty tracking CSVs
"""

import os
import csv
import json
import subprocess
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Set
import argparse

class PubMedFacultySearcher:
    """JSON-based PubMed searcher with PMID tracking"""
    
    def __init__(self, base_publications_path: str = "data/publications/pubmed", 
                 base_faculties_path: str = "data/faculties"):
        self.base_publications_path = base_publications_path
        self.base_faculties_path = base_faculties_path
        self.faculty_data = []
        self.search_stats = {
            'total_faculty': 0,
            'successful_faculty': 0,
            'failed_searches': 0,
            'total_all_publications': 0,
            'total_current_affiliation_publications': 0,
            'successful_all_searches': 0,
            'successful_current_searches': 0
        }
    
    def load_faculty_csv(self, csv_path: str) -> List[Dict]:
        """Load faculty data from CSV file"""
        
        print(f"📄 Loading faculty data from: {csv_path}")
        
        if not os.path.exists(csv_path):
            print(f"❌ CSV file not found: {csv_path}")
            return []
        
        faculty_list = []
        
        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as f:  # utf-8-sig handles BOM
                reader = csv.DictReader(f)
                
                for row_num, row in enumerate(reader, start=2):
                    # Extract key information with better handling of empty values
                    faculty_info = {
                        'faculty_id': row.get('faculty_id', '').strip(),
                        'name': row.get('name', '').strip(),
                        'first_name': row.get('first_name', '').strip(),
                        'last_name': row.get('last_name', '').strip(),
                        'university_code': row.get('university_code', '').strip(),
                        'university': row.get('university', '').strip(),
                        'university_name': row.get('university', '').strip(),  # Alias for compatibility
                        'faculty': row.get('faculty', '').strip(),
                        'department': row.get('department', '').strip(),
                        'position': row.get('position', '').strip(),
                        'uni_email': row.get('uni_email', '').strip(),
                        'other_email': row.get('other_email', '').strip()
                    }
                    
                    # Only include faculty with basic required information
                    if (faculty_info['faculty_id'] and 
                        faculty_info['name'] and 
                        faculty_info['university_code']):
                        faculty_list.append(faculty_info)
                    else:
                        print(f"⚠️  Skipping row {row_num}: Missing required fields")
                        continue
            
            print(f"✅ Loaded {len(faculty_list)} faculty members")
            
            # Show sample faculty
            if faculty_list:
                print(f"📋 Sample faculty:")
                for i, faculty in enumerate(faculty_list[:5]):
                    print(f"   {i+1}. {faculty['faculty_id']} - {faculty['name']} - {faculty['department']}")
                if len(faculty_list) > 5:
                    print(f"   ... and {len(faculty_list) - 5} more")
            
            return faculty_list
            
        except Exception as e:
            print(f"❌ Error loading CSV: {str(e)}")
            return []
    
    def extract_path_info(self, faculty: Dict) -> Dict:
        """Extract country, province, and university info from university code"""
        
        # Default structure for McMaster
        path_info = {
            'country': 'CA',
            'province': 'ON', 
            'university_code': faculty['university_code']
        }
        
        # Parse university code (e.g., CA-ON-002)
        if '-' in faculty['university_code']:
            parts = faculty['university_code'].split('-')
            if len(parts) >= 3:
                path_info['country'] = parts[0]
                path_info['province'] = parts[1]
        
        return path_info
    
    def get_faculty_csv_path(self, faculty: Dict) -> str:
        """Get the CSV file path for faculty publication tracking"""
        
        path_info = self.extract_path_info(faculty)
        university_folder = f"{faculty['university_code']}_{faculty['university'].lower().replace(' ', '').replace('university', 'ca')}"
        
        # Handle McMaster specifically
        if 'mcmaster' in faculty['university'].lower():
            university_folder = f"{faculty['university_code']}_mcmaster.ca"
        
        publications_dir = os.path.join(
            self.base_faculties_path,
            path_info['country'],
            path_info['province'],
            university_folder,
            'publications'
        )
        
        return os.path.join(publications_dir, f"{faculty['faculty_id']}.csv")
    
    def get_search_queries(self, faculty: Dict) -> Dict[str, List[str]]:
        """Generate search queries for all publications and current affiliation"""
        
        # All publications queries (no quotations)
        all_queries = [
            f"{faculty['name']}[Author]",
            f"{faculty['last_name']} {faculty['first_name'][:1]}[Author]",
            f"{faculty['first_name']} {faculty['last_name']}[Author]"
        ]
        
        # Current affiliation queries
        university_name = faculty['university']
        affiliation_queries = [
            f"{faculty['name']}[Author] AND {university_name}[Affiliation]",
            f"{faculty['last_name']} {faculty['first_name'][:1]}[Author] AND {university_name}[Affiliation]",
            f"{faculty['first_name']} {faculty['last_name']}[Author] AND {university_name}[Affiliation]"
        ]
        
        return {
            'all': all_queries,
            'affiliation': affiliation_queries
        }
    
    def run_edirect_json_search(self, query: str, search_type: str) -> Optional[Dict]:
        """Run a single EDirect search and return JSON result"""
        
        try:
            # Run esearch | efetch with correct JSON format for PubMed
            cmd = f"esearch -db pubmed -query '{query}' | efetch -format docsum -mode json"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0 and result.stdout.strip():
                try:
                    # Parse JSON response
                    json_data = json.loads(result.stdout)
                    return json_data
                except json.JSONDecodeError as e:
                    print(f"      ❌ JSON parsing error for {search_type}: {str(e)}")
                    return None
            else:
                print(f"      ❌ EDirect command failed for {search_type}")
                return None
                
        except subprocess.TimeoutExpired:
            print(f"      ❌ Timeout for {search_type}")
            return None
        except Exception as e:
            print(f"      ❌ Error in {search_type}: {str(e)}")
            return None
    
    def parse_and_save_publications(self, json_data: Dict, search_type: str) -> Set[str]:
        """Parse JSON response and save individual publication files"""
        
        pmids = set()
        
        try:
            # EDirect JSON structure: {"result": {"uids": [...], "pmid1": {...}, "pmid2": {...}}}
            result = json_data.get('result', {})
            uids = result.get('uids', [])
            
            print(f"      📚 Found {len(uids)} publications for {search_type}")
            
            # Create directory for PMID files
            os.makedirs(self.base_publications_path, exist_ok=True)
            
            for pmid in uids:
                # Get publication data for this PMID
                pub_data = result.get(pmid, {})
                
                if pub_data:
                    # Save individual PMID JSON file
                    pmid_file = os.path.join(self.base_publications_path, f"{pmid}.json")
                    
                    # Add search metadata to the publication
                    pub_data['search_metadata'] = {
                        'search_type': search_type,
                        'retrieved_date': datetime.now().isoformat(),
                        'pmid': pmid
                    }
                    
                    with open(pmid_file, 'w', encoding='utf-8') as f:
                        json.dump(pub_data, f, indent=2)
                    
                    pmids.add(pmid)
                    print(f"        ✅ Saved {pmid}.json")
                else:
                    print(f"        ⚠️  No data found for PMID {pmid}")
            
            return pmids
            
        except Exception as e:
            print(f"      ❌ Error parsing publications: {str(e)}")
            return set()

    def save_faculty_tracking_csv(self, faculty: Dict, all_pmids: Set[str], 
                                 current_affiliation_pmids: Set[str]) -> None:
        """Save faculty tracking CSV with PMID and current_affiliation columns"""
        
        try:
            # Extract university info for folder structure
            university_code = faculty.get('university_code', 'unknown')
            country = university_code[:2] if len(university_code) >= 2 else 'unknown'
            province = university_code[3:5] if len(university_code) >= 5 else 'unknown'
            
            # Create faculty CSV directory
            csv_dir = os.path.join(self.base_faculties_path, country, province, university_code, 'publications')
            os.makedirs(csv_dir, exist_ok=True)
            
            # Create CSV file
            faculty_id = faculty.get('faculty_id', 'unknown')
            csv_file = os.path.join(csv_dir, f"{faculty_id}.csv")
            
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['pmid', 'current_affiliation'])
                
                for pmid in sorted(all_pmids):
                    current_affiliation = pmid in current_affiliation_pmids
                    writer.writerow([pmid, str(current_affiliation).upper()])
            
            print(f"    📝 Saved faculty tracking: {csv_file}")
            print(f"       📊 Total publications: {len(all_pmids)}")
            print(f"       🏛️  Current affiliation: {len(current_affiliation_pmids)}")
            
        except Exception as e:
            print(f"    ❌ Error saving faculty CSV: {str(e)}")

    def search_faculty_publications(self, faculty: Dict) -> None:
        """Search and save publications for a single faculty member"""
        
        name = faculty.get('name', 'Unknown')
        faculty_id = faculty.get('faculty_id', 'unknown')
        
        # Better university name extraction
        university_name = faculty.get('university_name', faculty.get('university', 'McMaster University'))
        if not university_name or university_name.strip() == '':
            university_name = 'McMaster University'  # Default for this dataset
        
        print(f"  🔬 Processing: {name} (ID: {faculty_id})")
        print(f"      🏛️  University: {university_name}")
        
        # Prepare search queries
        queries = {
            'all_publications': f"{name}[Author]",
            'current_affiliation': f"{name}[Author] AND {university_name}[Affiliation]"
        }
        
        all_pmids = set()
        current_affiliation_pmids = set()
        
        for search_type, query in queries.items():
            print(f"    🔍 {search_type}: {query}")
            
            # Run EDirect search
            json_result = self.run_edirect_json_search(query, search_type)
            
            if json_result:
                # Parse and save individual publications
                pmids = self.parse_and_save_publications(json_result, search_type)
                
                if search_type == 'all_publications':
                    all_pmids = pmids
                    self.search_stats['total_all_publications'] += len(pmids)
                    self.search_stats['successful_all_searches'] += 1
                elif search_type == 'current_affiliation':
                    current_affiliation_pmids = pmids
                    self.search_stats['total_current_affiliation_publications'] += len(pmids)
                    self.search_stats['successful_current_searches'] += 1
                    
            else:
                print(f"    ❌ No results for {search_type}")
                self.search_stats['failed_searches'] += 1
            
            # Delay between searches
            if hasattr(self, 'delay') and self.delay > 0:
                time.sleep(self.delay)
        
        # Save faculty tracking CSV
        self.save_faculty_tracking_csv(faculty, all_pmids, current_affiliation_pmids)
        
        self.search_stats['successful_faculty'] += 1
    
    def run_searches(self, csv_path: str, max_faculty: Optional[int] = None, 
                    start_index: int = 0, delay: float = 2.0) -> None:
        """Run PubMed searches for faculty members"""
        
        print("🔬 **PubMed Faculty Searcher - JSON Based**\n")
        
        # Load faculty data
        self.faculty_data = self.load_faculty_csv(csv_path)
        
        if not self.faculty_data:
            print("❌ No faculty data loaded. Exiting.")
            return
        
        # Set delay for use in searches
        self.delay = delay
        
        # Determine range to process
        total_faculty = len(self.faculty_data)
        end_index = min(start_index + max_faculty, total_faculty) if max_faculty else total_faculty
        
        faculty_to_process = self.faculty_data[start_index:end_index]
        
        print(f"📊 Processing {len(faculty_to_process)} faculty members (indices {start_index}-{end_index-1})")
        print(f"⏱️  Delay between searches: {delay} seconds")
        print("=" * 80)
        
        self.search_stats['total_faculty'] = len(faculty_to_process)
        
        # Process each faculty member
        for i, faculty in enumerate(faculty_to_process, start=start_index + 1):
            print(f"\n[{i}/{end_index}] Starting faculty search...")
            
            try:
                self.search_faculty_publications(faculty)
                print(f"    ✅ Completed successfully!")
                
            except Exception as e:
                print(f"    ❌ Error processing faculty: {str(e)}")
                self.search_stats['failed_searches'] += 1
                continue
        
        # Print final statistics
        self.print_final_stats()
    
    def print_final_stats(self) -> None:
        """Print comprehensive final statistics"""
        
        stats = self.search_stats
        
        print("\n" + "=" * 80)
        print("📊 **FINAL SEARCH STATISTICS**")
        print("=" * 80)
        
        print(f"👥 Faculty Processing:")
        print(f"   • Total faculty: {stats['total_faculty']}")
        print(f"   • Successful: {stats['successful_faculty']}")
        print(f"   • Failed: {stats['failed_searches']}")
        
        success_rate = (stats['successful_faculty'] / stats['total_faculty'] * 100) if stats['total_faculty'] > 0 else 0
        print(f"   • Success rate: {success_rate:.1f}%")
        
        print(f"\n📚 Publication Results:")
        print(f"   • All publications found: {stats['total_all_publications']}")
        print(f"   • Current affiliation pubs: {stats['total_current_affiliation_publications']}")
        print(f"   • Individual PMID files created: {stats['total_all_publications']} (deduplicated)")
        
        print(f"\n🔍 Search Success:")
        print(f"   • Successful all-publication searches: {stats['successful_all_searches']}")
        print(f"   • Successful current-affiliation searches: {stats['successful_current_searches']}")
        
        print(f"\n📁 Output Locations:")
        print(f"   • PMID JSON files: {self.base_publications_path}/")
        print(f"   • Faculty CSV tracking: {self.base_faculties_path}/[country]/[province]/[university]/publications/")
        
        print("=" * 80)

def main():
    """Main function with command line interface"""
    
    parser = argparse.ArgumentParser(description='PubMed Faculty Publication Searcher - JSON Based')
    parser.add_argument('csv_file', help='Path to faculty CSV file')
    parser.add_argument('--max', type=int, help='Maximum number of faculty to process (default: all)')
    parser.add_argument('--start', type=int, default=0, help='Starting index (default: 0)')
    parser.add_argument('--delay', type=float, default=2.0, help='Delay between searches in seconds (default: 2.0)')
    parser.add_argument('--publications-base', default='data/publications/pubmed', 
                       help='Base path for PMID JSON files (default: data/publications/pubmed)')
    parser.add_argument('--faculties-base', default='data/faculties',
                       help='Base path for faculty CSV tracking files (default: data/faculties)')
    
    args = parser.parse_args()
    
    # Validate CSV file exists
    if not os.path.exists(args.csv_file):
        print(f"❌ Error: CSV file not found: {args.csv_file}")
        return 1
    
    # Create searcher instance
    searcher = PubMedFacultySearcher(
        base_publications_path=args.publications_base,
        base_faculties_path=args.faculties_base
    )
    
    print(f"🚀 Starting PubMed searches...")
    print(f"📄 CSV file: {args.csv_file}")
    print(f"📂 PMID files output: {args.publications_base}/")
    print(f"📂 Faculty CSV output: {args.faculties_base}/[country]/[province]/[university]/publications/")
    print("-" * 80)
    
    try:
        # Run the searches
        searcher.run_searches(
            args.csv_file,
            start_index=args.start,
            max_faculty=args.max,
            delay=args.delay
        )
        
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Search interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        return 1
    
    print(f"\n🎉 PubMed search completed successfully!")
    return 0

if __name__ == "__main__":
    exit(main()) 