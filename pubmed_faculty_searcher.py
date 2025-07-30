#!/usr/bin/env python3
"""
PubMed Faculty Searcher
Reads faculty CSV files and runs EDirect searches dynamically
Searches both all publications and current affiliation publications
"""

import os
import csv
import subprocess
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional
import argparse

class PubMedFacultySearcher:
    """Dynamic PubMed searcher based on faculty CSV data"""
    
    def __init__(self, base_path: str = "data/publications/pubmed"):
        self.base_path = base_path
        self.faculty_data = []
        self.search_stats = {
            'total_faculty': 0,
            'successful_all_searches': 0,
            'successful_affiliation_searches': 0,
            'failed_searches': 0,
            'total_all_publications': 0,
            'total_affiliation_publications': 0
        }
    
    def load_faculty_csv(self, csv_path: str) -> List[Dict]:
        """Load faculty data from CSV file"""
        
        print(f"📄 Loading faculty data from: {csv_path}")
        
        if not os.path.exists(csv_path):
            print(f"❌ CSV file not found: {csv_path}")
            return []
        
        faculty_list = []
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    # Extract key information
                    faculty_info = {
                        'faculty_id': row.get('faculty_id', ''),
                        'name': row.get('name', ''),
                        'first_name': row.get('first_name', ''),
                        'last_name': row.get('last_name', ''),
                        'university_code': row.get('university_code', ''),
                        'university': row.get('university', ''),
                        'faculty': row.get('faculty', ''),
                        'department': row.get('department', ''),
                        'position': row.get('position', ''),
                        'full_time': row.get('full_time', ''),
                        'adjunct': row.get('adjunct', ''),
                        'uni_email': row.get('uni_email', ''),
                        'research_areas': row.get('research_areas', ''),
                        'gscholar': row.get('gscholar', ''),
                        'orcid': row.get('orcid', ''),
                        'scopus': row.get('scopus', '')
                    }
                    
                    # Only add if we have a valid name
                    if faculty_info['name'].strip():
                        faculty_list.append(faculty_info)
            
            print(f"✅ Loaded {len(faculty_list)} faculty members")
            
            # Show sample faculty
            if faculty_list:
                print(f"📋 Sample faculty:")
                for i, faculty in enumerate(faculty_list[:5]):
                    print(f"   {i+1}. {faculty['name']} - {faculty['department']}")
                if len(faculty_list) > 5:
                    print(f"   ... and {len(faculty_list) - 5} more")
            
            return faculty_list
            
        except Exception as e:
            print(f"❌ Error loading CSV: {str(e)}")
            return []
    
    def extract_university_path_info(self, university_code: str) -> Dict:
        """Extract country, province, and university info from university code"""
        
        # Default structure for McMaster
        path_info = {
            'country': 'CA',
            'province': 'ON', 
            'university_code': university_code
        }
        
        # Parse university code (e.g., CA-ON-002)
        if '-' in university_code:
            parts = university_code.split('-')
            if len(parts) >= 3:
                path_info['country'] = parts[0]
                path_info['province'] = parts[1]
        
        return path_info
    
    def get_faculty_output_path(self, faculty: Dict) -> str:
        """Get the full output path for a faculty member's publications"""
        
        path_info = self.extract_university_path_info(faculty['university_code'])
        university_folder = f"{faculty['university_code']}_{faculty['university'].lower().replace(' ', '').replace('university', 'ca')}"
        
        # Handle McMaster specifically
        if 'mcmaster' in faculty['university'].lower():
            university_folder = f"{faculty['university_code']}_mcmaster.ca"
        
        return os.path.join(
            self.base_path,
            path_info['country'],
            path_info['province'],
            university_folder
        )
    
    def get_faculty_filenames(self, faculty: Dict) -> Dict[str, str]:
        """Generate filenames for faculty publications (all and affiliation-specific)"""
        
        # Clean name for filename
        clean_name = faculty['name'].replace(' ', '_').replace(',', '').replace('.', '')
        # Remove any problematic characters
        clean_name = ''.join(c for c in clean_name if c.isalnum() or c in ['_', '-'])
        
        return {
            'all': f"{clean_name}_all_publications.txt",
            'affiliation': f"{clean_name}_current_affiliation.txt"
        }
    
    def get_search_queries(self, faculty: Dict) -> Dict[str, List[str]]:
        """Generate search queries for all publications and current affiliation"""
        
        # All publications queries (no quotations as requested)
        all_queries = [
            f"{faculty['name']}[Author]",
            f"{faculty['last_name']} {faculty['first_name'][:1]}[Author]",  # "Guyatt G[Author]"
            f"{faculty['first_name']} {faculty['last_name']}[Author]"  # "Gordon Guyatt[Author]"
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
    
    def run_search_queries(self, queries: List[str], output_file: str, search_type: str) -> int:
        """Run a set of queries and return the best result count"""
        
        best_result = None
        best_count = 0
        
        for i, query in enumerate(queries):
            temp_file = f"{output_file}.tmp{i}"
            
            try:
                # Run esearch | efetch (no quotes around the entire query)
                cmd = f"esearch -db pubmed -query '{query}' | efetch -format medline > \"{temp_file}\""
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0 and os.path.exists(temp_file):
                    # Count publications
                    with open(temp_file, 'r') as f:
                        content = f.read()
                        pub_count = content.count('PMID-')
                    
                    print(f"      {search_type} Query {i+1}: {query} → {pub_count} publications")
                    
                    if pub_count > best_count:
                        best_count = pub_count
                        best_result = temp_file
                
            except subprocess.TimeoutExpired:
                print(f"      {search_type} Query {i+1}: Timeout")
            except Exception as e:
                print(f"      {search_type} Query {i+1}: Error - {str(e)}")
            
            # Small delay between queries
            time.sleep(1)
        
        # Use the best result
        if best_result and best_count > 0:
            # Move best result to final location
            os.rename(best_result, output_file)
            
            # Clean up other temp files
            for i in range(len(queries)):
                temp_file = f"{output_file}.tmp{i}"
                if os.path.exists(temp_file) and temp_file != best_result:
                    os.remove(temp_file)
            
            return best_count
        
        else:
            # Clean up temp files
            for i in range(len(queries)):
                temp_file = f"{output_file}.tmp{i}"
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            
            return 0
    
    def run_edirect_search(self, faculty: Dict, delay: float = 2.0) -> Dict[str, int]:
        """Run EDirect search for a single faculty member (both all and affiliation)"""
        
        try:
            # Get output path and filenames
            output_dir = self.get_faculty_output_path(faculty)
            filenames = self.get_faculty_filenames(faculty)
            queries = self.get_search_queries(faculty)
            
            # Create directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            print(f"🔍 Searching for {faculty['name']}...")
            print(f"   🏫 {faculty['university']} - {faculty['department']}")
            print(f"   📁 Output dir: {output_dir}")
            
            results = {'all': 0, 'affiliation': 0}
            
            # Search all publications
            print(f"   📚 Searching all publications...")
            all_output_file = os.path.join(output_dir, filenames['all'])
            all_count = self.run_search_queries(queries['all'], all_output_file, "All")
            results['all'] = all_count
            
            if all_count > 0:
                print(f"   ✅ All publications: {all_count}")
                self.search_stats['successful_all_searches'] += 1
                self.search_stats['total_all_publications'] += all_count
            else:
                print(f"   ❌ No publications found (all)")
            
            # Search current affiliation publications
            print(f"   🏛️  Searching current affiliation publications...")
            affiliation_output_file = os.path.join(output_dir, filenames['affiliation'])
            affiliation_count = self.run_search_queries(queries['affiliation'], affiliation_output_file, "Affiliation")
            results['affiliation'] = affiliation_count
            
            if affiliation_count > 0:
                print(f"   ✅ Current affiliation: {affiliation_count}")
                self.search_stats['successful_affiliation_searches'] += 1
                self.search_stats['total_affiliation_publications'] += affiliation_count
            else:
                print(f"   ❌ No publications found (current affiliation)")
            
            # Summary for this faculty
            if all_count > 0 or affiliation_count > 0:
                print(f"   📊 Summary: {all_count} total, {affiliation_count} at {faculty['university']}")
                
                # Add delay between faculty searches
                if delay > 0:
                    time.sleep(delay)
                
                return results
            else:
                print(f"   ❌ No publications found with any search strategy")
                self.search_stats['failed_searches'] += 1
                return results
            
        except Exception as e:
            print(f"   ❌ Search failed: {str(e)}")
            self.search_stats['failed_searches'] += 1
            return {'all': 0, 'affiliation': 0}
    
    def search_faculty_batch(self, faculty_list: List[Dict], 
                           start_index: int = 0, 
                           max_faculty: Optional[int] = None,
                           delay: float = 2.0) -> Dict:
        """Run searches for a batch of faculty members"""
        
        if max_faculty:
            end_index = min(start_index + max_faculty, len(faculty_list))
            batch = faculty_list[start_index:end_index]
        else:
            batch = faculty_list[start_index:]
        
        print(f"🚀 Starting batch search for {len(batch)} faculty members...")
        print(f"📊 Range: {start_index + 1} to {start_index + len(batch)} of {len(faculty_list)}")
        print(f"📋 Search types: All publications + Current affiliation")
        print("=" * 70)
        
        self.search_stats['total_faculty'] = len(batch)
        start_time = datetime.now()
        
        for i, faculty in enumerate(batch):
            print(f"\n[{i+1}/{len(batch)}] Processing {faculty['name']}")
            
            results = self.run_edirect_search(faculty, delay)
            
            # Show progress
            if (i + 1) % 10 == 0:
                elapsed = datetime.now() - start_time
                avg_time = elapsed.total_seconds() / (i + 1)
                remaining = avg_time * (len(batch) - i - 1)
                
                successful_faculty = self.search_stats['successful_all_searches']
                
                print(f"\n📈 Progress: {i+1}/{len(batch)} completed")
                print(f"   ⏱️  Average time per faculty: {avg_time:.1f}s")
                print(f"   🕐 Estimated remaining: {remaining/60:.1f} minutes")
                print(f"   ✅ Success rate: {successful_faculty}/{i+1} ({100*successful_faculty/(i+1):.1f}%)")
                print(f"   📚 Publications found: {self.search_stats['total_all_publications']} total, {self.search_stats['total_affiliation_publications']} current affiliation")
        
        # Final statistics
        end_time = datetime.now()
        total_time = end_time - start_time
        
        print(f"\n🎉 Batch search completed!")
        print("=" * 70)
        print(f"📊 Final Statistics:")
        print(f"   👨‍🔬 Total faculty processed: {self.search_stats['total_faculty']}")
        print(f"   ✅ Successful all searches: {self.search_stats['successful_all_searches']}")
        print(f"   ✅ Successful affiliation searches: {self.search_stats['successful_affiliation_searches']}")
        print(f"   ❌ Failed searches: {self.search_stats['failed_searches']}")
        print(f"   📚 Total publications (all): {self.search_stats['total_all_publications']}")
        print(f"   🏛️  Total publications (current affiliation): {self.search_stats['total_affiliation_publications']}")
        print(f"   ⏱️  Total time: {total_time}")
        print(f"   📈 Success rate: {100*self.search_stats['successful_all_searches']/self.search_stats['total_faculty']:.1f}%")
        
        if self.search_stats['successful_all_searches'] > 0:
            avg_all_pubs = self.search_stats['total_all_publications'] / self.search_stats['successful_all_searches']
            print(f"   📊 Average publications per faculty (all): {avg_all_pubs:.1f}")
        
        if self.search_stats['successful_affiliation_searches'] > 0:
            avg_aff_pubs = self.search_stats['total_affiliation_publications'] / self.search_stats['successful_affiliation_searches']
            print(f"   📊 Average publications per faculty (current affiliation): {avg_aff_pubs:.1f}")
        
        return self.search_stats
    
    def show_directory_structure(self, faculty_list: List[Dict]):
        """Show what the directory structure will look like"""
        
        print(f"\n📁 Directory Structure Preview:")
        print("=" * 60)
        
        # Group by university
        universities = {}
        for faculty in faculty_list:
            uni_code = faculty['university_code']
            if uni_code not in universities:
                universities[uni_code] = {
                    'info': faculty,
                    'faculty_count': 0
                }
            universities[uni_code]['faculty_count'] += 1
        
        for uni_code, uni_data in universities.items():
            path_info = self.extract_university_path_info(uni_code)
            output_path = self.get_faculty_output_path(uni_data['info'])
            
            print(f"\n🏫 {uni_data['info']['university']}")
            print(f"   📁 Path: {output_path}")
            print(f"   👨‍🔬 Faculty: {uni_data['faculty_count']}")
            print(f"   📄 Files per faculty:")
            print(f"      • [Name]_all_publications.txt (all career publications)")
            print(f"      • [Name]_current_affiliation.txt (publications at {uni_data['info']['university']})")

def main():
    """Main function with command line interface"""
    
    parser = argparse.ArgumentParser(description="PubMed Faculty Searcher - Dual Search Strategy")
    parser.add_argument('csv_file', help='Path to faculty CSV file')
    parser.add_argument('--start', type=int, default=0, help='Starting faculty index (0-based)')
    parser.add_argument('--max', type=int, help='Maximum number of faculty to search')
    parser.add_argument('--delay', type=float, default=2.0, help='Delay between searches (seconds)')
    parser.add_argument('--preview', action='store_true', help='Preview directory structure only')
    parser.add_argument('--output-base', default='data/publications/pubmed', help='Base output directory')
    
    args = parser.parse_args()
    
    print("🔬 PubMed Faculty Searcher - Dual Search Strategy")
    print("=" * 60)
    print(f"CSV File: {args.csv_file}")
    print(f"Output Base: {args.output_base}")
    print(f"📋 Search Strategy:")
    print(f"   1. All publications: [Author] searches")
    print(f"   2. Current affiliation: [Author] AND [University][Affiliation]")
    print(f"   📄 Creates 2 files per faculty member")
    
    # Initialize searcher
    searcher = PubMedFacultySearcher(args.output_base)
    
    # Load faculty data
    faculty_list = searcher.load_faculty_csv(args.csv_file)
    
    if not faculty_list:
        print("❌ No faculty data loaded. Exiting.")
        sys.exit(1)
    
    # Show directory structure preview
    searcher.show_directory_structure(faculty_list)
    
    if args.preview:
        print("\n👀 Preview mode - no searches will be run")
        return
    
    # Confirm before starting
    if not args.max or args.max > 50:
        print(f"\n⚠️  About to search {len(faculty_list)} faculty members (2 searches each).")
        print(f"   This will create {len(faculty_list) * 2} files and may take several hours.")
        response = input("Continue? (y/n): ")
        if response.lower() != 'y':
            print("❌ Search cancelled")
            return
    
    print(f"\n🚀 Starting EDirect searches...")
    print(f"💡 Tip: You can stop anytime with Ctrl+C and resume later with --start={args.start}")
    
    try:
        # Run the searches
        stats = searcher.search_faculty_batch(
            faculty_list,
            start_index=args.start,
            max_faculty=args.max,
            delay=args.delay
        )
        
        print(f"\n📋 Next Steps:")
        print(f"1. Parse results: python3 parse_medline_structured.py {args.output_base}")
        print(f"2. Transfer to VPS: scp -r parsed_publications_structured/ user@vps:/var/www/ff/")
        print(f"3. Import to database: python3 import_pubmed_data.py parsed_publications_structured/")
        
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Search interrupted by user")
        print(f"📊 Progress so far:")
        print(f"   ✅ Successful (all): {searcher.search_stats['successful_all_searches']}")
        print(f"   ✅ Successful (affiliation): {searcher.search_stats['successful_affiliation_searches']}")
        print(f"   ❌ Failed: {searcher.search_stats['failed_searches']}")
        print(f"\n💡 To resume, run:")
        print(f"   python3 pubmed_faculty_searcher.py {args.csv_file} --start={args.start + searcher.search_stats['total_faculty']}")

if __name__ == "__main__":
    main() 