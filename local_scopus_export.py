#!/usr/bin/env python3
"""
Local Scopus Export Script

Run this on a machine with institutional Scopus access to export data
for later import to your VPS.
"""

import sys
import os

# Add the current directory to path to import our searcher
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scopus_faculty_searcher import ScopusFacultySearcher
import argparse

def main():
    parser = argparse.ArgumentParser(description='Export Scopus data locally')
    parser.add_argument('csv_file', help='Path to faculty CSV file')
    parser.add_argument('--api-key', default='a40794bde2315194803ca0422b5fe851', 
                       help='Scopus API key')
    parser.add_argument('--max', type=int, default=10, help='Maximum faculty to process')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay between requests')
    parser.add_argument('--export-dir', default='scopus_export', 
                       help='Directory to save exported data')
    
    args = parser.parse_args()
    
    print("🏠 Local Scopus Data Export")
    print("=" * 40)
    print("💡 Run this script on a machine with institutional Scopus access")
    print("💡 Then transfer the export directory to your VPS")
    print()
    
    # Use the existing searcher but save to export directory
    searcher = ScopusFacultySearcher(args.api_key, args.delay)
    
    # Override output paths for export
    import os
    original_cwd = os.getcwd()
    
    try:
        # Create export directory
        os.makedirs(args.export_dir, exist_ok=True)
        os.chdir(args.export_dir)
        
        # Load and process faculty
        faculty_data = searcher.load_faculty_data(args.csv_file)
        if faculty_data:
            searcher.process_faculty_list(faculty_data, args.max)
            
        print(f"\n📦 Export completed in: {os.path.join(original_cwd, args.export_dir)}")
        print(f"💡 Transfer this directory to your VPS at: data/")
        
    finally:
        os.chdir(original_cwd)

if __name__ == "__main__":
    main()
