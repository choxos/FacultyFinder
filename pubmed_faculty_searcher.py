#!/usr/bin/env python3
"""
PubMed Faculty Searcher
Reads faculty CSV files and runs EDirect searches dynamically
Much better than individual bash scripts for each faculty
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
            'successful_searches': 0,
            'failed_searches': 0,
            'total_publications': 0
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
    
    def get_faculty_filename(self, faculty: Dict) -> str:
        """Generate filename for faculty publications"""
        
        # Clean name for filename
        clean_name = faculty['name'].replace(' ', '_').replace(',', '').replace('.', '')
        # Remove any problematic characters
        clean_name = ''.join(c for c in clean_name if c.isalnum() or c in ['_', '-'])
        
        return f"{clean_name}_publications.txt"
    
    def run_edirect_search(self, faculty: Dict, delay: float = 2.0) -> bool:
        """Run EDirect search for a single faculty member"""
        
        try:
            # Get output path and filename
            output_dir = self.get_faculty_output_path(faculty)
            output_file = os.path.join(output_dir, self.get_faculty_filename(faculty))
            
            # Create directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Prepare search query - try different name formats
            search_queries = [
                f'"{faculty["name"]}"[Author]',
                f'"{faculty["last_name"]} {faculty["first_name"][:1]}"[Author]',  # "Guyatt G"
                f'"{faculty["first_name"]} {faculty["last_name"]}"[Author]'  # "Gordon Guyatt"
            ]
            
            print(f"🔍 Searching for {faculty['name']}...")
            print(f"   🏫 {faculty['university']} - {faculty['department']}")
            print(f"   📁 Output: {output_file}")
            
            # Try each search query until we get results
            best_result = None
            best_count = 0
            
            for i, query in enumerate(search_queries):
                temp_file = f"{output_file}.tmp{i}"
                
                try:
                    # Run esearch | efetch
                    cmd = f'esearch -db pubmed -query \'{query}\' | efetch -format medline > "{temp_file}"'
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
                    
                    if result.returncode == 0 and os.path.exists(temp_file):
                        # Count publications
                        with open(temp_file, 'r') as f:
                            content = f.read()
                            pub_count = content.count('PMID-')
                        
                        print(f"      Query {i+1}: {query} → {pub_count} publications")
                        
                        if pub_count > best_count:
                            best_count = pub_count
                            best_result = temp_file
                    
                except subprocess.TimeoutExpired:
                    print(f"      Query {i+1}: Timeout")
                except Exception as e:
                    print(f"      Query {i+1}: Error - {str(e)}")
                
                # Small delay between queries
                time.sleep(1)
            
            # Use the best result
            if best_result and best_count > 0:
                # Move best result to final location
                os.rename(best_result, output_file)
                
                # Clean up other temp files
                for i in range(len(search_queries)):
                    temp_file = f"{output_file}.tmp{i}"
                    if os.path.exists(temp_file) and temp_file != best_result:
                        os.remove(temp_file)
                
                print(f"   ✅ Found {best_count} publications")
                self.search_stats['successful_searches'] += 1
                self.search_stats['total_publications'] += best_count
                
                # Add delay between faculty searches
                if delay > 0:
                    time.sleep(delay)
                
                return True
            
            else:
                # No results found with any query
                print(f"   ❌ No publications found")
                
                # Clean up temp files
                for i in range(len(search_queries)):
                    temp_file = f"{output_file}.tmp{i}"
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                
                self.search_stats['failed_searches'] += 1
                return False
            
        except Exception as e:
            print(f"   ❌ Search failed: {str(e)}")
            self.search_stats['failed_searches'] += 1
            return False
    
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
        print("=" * 60)
        
        self.search_stats['total_faculty'] = len(batch)
        start_time = datetime.now()
        
        for i, faculty in enumerate(batch):
            print(f"\n[{i+1}/{len(batch)}] Processing {faculty['name']}")
            
            success = self.run_edirect_search(faculty, delay)
            
            # Show progress
            if (i + 1) % 10 == 0:
                elapsed = datetime.now() - start_time
                avg_time = elapsed.total_seconds() / (i + 1)
                remaining = avg_time * (len(batch) - i - 1)
                
                print(f"\n📈 Progress: {i+1}/{len(batch)} completed")
                print(f"   ⏱️  Average time per faculty: {avg_time:.1f}s")
                print(f"   🕐 Estimated remaining: {remaining/60:.1f} minutes")
                print(f"   ✅ Success rate: {self.search_stats['successful_searches']}/{i+1} ({100*self.search_stats['successful_searches']/(i+1):.1f}%)")
        
        # Final statistics
        end_time = datetime.now()
        total_time = end_time - start_time
        
        print(f"\n🎉 Batch search completed!")
        print("=" * 60)
        print(f"📊 Final Statistics:")
        print(f"   👨‍🔬 Total faculty processed: {self.search_stats['total_faculty']}")
        print(f"   ✅ Successful searches: {self.search_stats['successful_searches']}")
        print(f"   ❌ Failed searches: {self.search_stats['failed_searches']}")
        print(f"   📚 Total publications found: {self.search_stats['total_publications']}")
        print(f"   ⏱️  Total time: {total_time}")
        print(f"   📈 Success rate: {100*self.search_stats['successful_searches']/self.search_stats['total_faculty']:.1f}%")
        
        if self.search_stats['successful_searches'] > 0:
            avg_pubs = self.search_stats['total_publications'] / self.search_stats['successful_searches']
            print(f"   📊 Average publications per faculty: {avg_pubs:.1f}")
        
        return self.search_stats
    
    def show_directory_structure(self, faculty_list: List[Dict]):
        """Show what the directory structure will look like"""
        
        print(f"\n📁 Directory Structure Preview:")
        print("=" * 50)
        
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
            print(f"   📄 Files will be saved as: [Faculty_Name]_publications.txt")

def main():
    """Main function with command line interface"""
    
    parser = argparse.ArgumentParser(description="PubMed Faculty Searcher")
    parser.add_argument('csv_file', help='Path to faculty CSV file')
    parser.add_argument('--start', type=int, default=0, help='Starting faculty index (0-based)')
    parser.add_argument('--max', type=int, help='Maximum number of faculty to search')
    parser.add_argument('--delay', type=float, default=2.0, help='Delay between searches (seconds)')
    parser.add_argument('--preview', action='store_true', help='Preview directory structure only')
    parser.add_argument('--output-base', default='data/publications/pubmed', help='Base output directory')
    
    args = parser.parse_args()
    
    print("🔬 PubMed Faculty Searcher")
    print("=" * 50)
    print(f"CSV File: {args.csv_file}")
    print(f"Output Base: {args.output_base}")
    
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
        response = input(f"\n⚠️  About to search {len(faculty_list)} faculty members. This may take several hours. Continue? (y/n): ")
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
        print(f"   ✅ Successful: {searcher.search_stats['successful_searches']}")
        print(f"   ❌ Failed: {searcher.search_stats['failed_searches']}")
        print(f"\n💡 To resume, run:")
        print(f"   python3 pubmed_faculty_searcher.py {args.csv_file} --start={args.start + searcher.search_stats['successful_searches'] + searcher.search_stats['failed_searches']}")

if __name__ == "__main__":
    main() 