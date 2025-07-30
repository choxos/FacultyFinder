#!/usr/bin/env python3
"""
Parse structured Medline files from university folder organization
Works with: data/publications/pubmed/[country]/[province]/[university]/
"""

import os
import json
import csv
import sys
import re
from datetime import datetime
from typing import Dict, List, Optional

class StructuredMedlineParser:
    """Parser for structured NCBI Medline format files"""
    
    def __init__(self):
        self.current_record = {}
        self.publications = []
    
    def parse_file(self, file_path: str, faculty_name: str = None, university_info: Dict = None) -> List[Dict]:
        """Parse a single medline file with university context"""
        
        print(f"📄 Parsing {file_path}...")
        
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return []
        
        # Extract faculty name from filename if not provided
        if not faculty_name:
            filename = os.path.basename(file_path)
            faculty_name = filename.replace("_publications.txt", "").replace("_", " ")
        
        # Extract university info from path if not provided
        if not university_info:
            university_info = self._extract_university_info_from_path(file_path)
        
        publications = []
        current_record = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    
                    if not line:
                        # Empty line - end of record
                        if current_record:
                            pub_data = self._process_record(current_record, faculty_name, university_info)
                            if pub_data:
                                publications.append(pub_data)
                            current_record = {}
                        continue
                    
                    # Parse field
                    if '- ' in line:
                        field, value = line.split('- ', 1)
                        field = field.strip()
                        value = value.strip()
                        
                        if field in current_record:
                            # Multiple values for same field
                            if isinstance(current_record[field], list):
                                current_record[field].append(value)
                            else:
                                current_record[field] = [current_record[field], value]
                        else:
                            current_record[field] = value
                
                # Process final record
                if current_record:
                    pub_data = self._process_record(current_record, faculty_name, university_info)
                    if pub_data:
                        publications.append(pub_data)
        
        except Exception as e:
            print(f"❌ Error parsing {file_path}: {str(e)}")
            return []
        
        print(f"   ✅ Parsed {len(publications)} publications for {faculty_name}")
        return publications
    
    def _extract_university_info_from_path(self, file_path: str) -> Dict:
        """Extract university information from file path"""
        
        path_parts = file_path.split(os.sep)
        
        university_info = {
            'country': 'Unknown',
            'province': 'Unknown', 
            'university_code': 'Unknown',
            'university_name': 'Unknown'
        }
        
        try:
            # Look for the pubmed folder and extract info
            if 'pubmed' in path_parts:
                pubmed_index = path_parts.index('pubmed')
                
                if len(path_parts) > pubmed_index + 3:
                    university_info['country'] = path_parts[pubmed_index + 1]
                    university_info['province'] = path_parts[pubmed_index + 2]
                    university_info['university_code'] = path_parts[pubmed_index + 3]
                    
                    # Extract university name from code
                    if '_' in university_info['university_code']:
                        university_info['university_name'] = university_info['university_code'].split('_', 1)[1].replace('.ca', '')
        
        except Exception as e:
            print(f"   Warning: Could not extract university info from path: {str(e)}")
        
        return university_info
    
    def _process_record(self, record: Dict, faculty_name: str, university_info: Dict) -> Optional[Dict]:
        """Process a single publication record with university context"""
        
        try:
            # Extract PMID
            pmid = record.get('PMID', '')
            if not pmid:
                return None
            
            # Extract title
            title = record.get('TI', '')
            if isinstance(title, list):
                title = ' '.join(title)
            
            # Extract abstract
            abstract = record.get('AB', '')
            if isinstance(abstract, list):
                abstract = ' '.join(abstract)
            
            # Extract authors
            authors = []
            au_fields = record.get('AU', [])
            if isinstance(au_fields, str):
                au_fields = [au_fields]
            elif au_fields:
                authors = au_fields
            
            authors_str = "; ".join(authors) if authors else ""
            
            # Extract journal
            journal_name = record.get('JT', '') or record.get('TA', '')
            
            # Extract publication date
            pub_date = None
            pub_year = None
            
            # Try different date fields
            date_fields = ['DP', 'DA', 'DEP']
            for date_field in date_fields:
                if date_field in record:
                    date_str = record[date_field]
                    if isinstance(date_str, list):
                        date_str = date_str[0]
                    
                    # Extract year
                    year_match = re.search(r'(\d{4})', date_str)
                    if year_match:
                        pub_year = int(year_match.group(1))
                        
                        # Try to extract full date
                        date_match = re.search(r'(\d{4})/(\d{1,2})/(\d{1,2})', date_str)
                        if date_match:
                            year, month, day = date_match.groups()
                            pub_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                        elif re.search(r'(\d{4})/(\d{1,2})', date_str):
                            date_match = re.search(r'(\d{4})/(\d{1,2})', date_str)
                            year, month = date_match.groups()
                            pub_date = f"{year}-{month.zfill(2)}-01"
                        else:
                            pub_date = f"{pub_year}-01-01"
                    break
            
            # Extract DOI
            doi = ""
            doi_fields = ['LID', 'AID']
            for doi_field in doi_fields:
                if doi_field in record:
                    doi_values = record[doi_field]
                    if isinstance(doi_values, str):
                        doi_values = [doi_values]
                    
                    for doi_value in doi_values:
                        if 'doi' in doi_value.lower():
                            # Extract DOI from string like "10.1234/example [doi]"
                            doi_match = re.search(r'(10\.\d+/[^\s\[\]]+)', doi_value)
                            if doi_match:
                                doi = doi_match.group(1)
                                break
                    if doi:
                        break
            
            # Extract volume, issue, pages
            volume = record.get('VI', '')
            issue = record.get('IP', '')
            pages = record.get('PG', '')
            
            # Create publication data with university context
            publication_data = {
                'pmid': pmid,
                'doi': doi,
                'title': title,
                'abstract': abstract,
                'authors': authors_str,
                'journal_name': journal_name,
                'publication_date': pub_date,
                'publication_year': pub_year,
                'volume': volume,
                'issue': issue,
                'pages': pages,
                'faculty_name': faculty_name,
                'university_code': university_info.get('university_code', ''),
                'university_name': university_info.get('university_name', ''),
                'country': university_info.get('country', ''),
                'province': university_info.get('province', ''),
                'created_at': datetime.now().isoformat()
            }
            
            return publication_data
            
        except Exception as e:
            print(f"      Warning: Failed to process record: {str(e)}")
            return None
    
    def parse_structured_directory(self, base_path: str, output_dir: str = "parsed_publications_structured") -> Dict:
        """Parse all structured medline files"""
        
        print(f"📁 Parsing structured medline files from: {base_path}")
        
        if not os.path.exists(base_path):
            print(f"❌ Directory not found: {base_path}")
            return {}
        
        os.makedirs(output_dir, exist_ok=True)
        
        all_publications = []
        university_results = {}
        faculty_results = []
        
        # Walk through the structured directory
        for root, dirs, files in os.walk(base_path):
            txt_files = [f for f in files if f.endswith('.txt')]
            
            if not txt_files:
                continue
            
            # Extract university info from path
            university_info = self._extract_university_info_from_path(root)
            university_key = university_info['university_code']
            
            if university_key not in university_results:
                university_results[university_key] = {
                    'university_info': university_info,
                    'faculty_count': 0,
                    'total_publications': 0,
                    'faculty_list': []
                }
            
            print(f"\n🏫 Processing {university_info['university_name']} ({university_key})")
            print(f"   📁 Path: {root}")
            print(f"   📄 Files: {len(txt_files)}")
            
            for filename in txt_files:
                file_path = os.path.join(root, filename)
                
                # Extract faculty name from filename
                faculty_name = filename.replace("_publications.txt", "").replace("_", " ")
                
                # Parse file
                publications = self.parse_file(file_path, faculty_name, university_info)
                
                if publications:
                    # Save individual faculty file
                    faculty_output = os.path.join(output_dir, f"{university_key}_{faculty_name.replace(' ', '_')}_parsed.json")
                    with open(faculty_output, 'w') as f:
                        json.dump({
                            'faculty_name': faculty_name,
                            'university_info': university_info,
                            'publication_count': len(publications),
                            'publications': publications
                        }, f, indent=2)
                    
                    # Add to combined results
                    all_publications.extend(publications)
                    
                    # Update university stats
                    university_results[university_key]['faculty_count'] += 1
                    university_results[university_key]['total_publications'] += len(publications)
                    university_results[university_key]['faculty_list'].append({
                        'name': faculty_name,
                        'publication_count': len(publications)
                    })
                    
                    # Add to faculty results
                    faculty_results.append({
                        'name': faculty_name,
                        'university_code': university_key,
                        'university_name': university_info['university_name'],
                        'publication_count': len(publications),
                        'source_file': filename
                    })
                    
                    print(f"      ✅ {faculty_name}: {len(publications)} publications")
        
        # Save combined results
        combined_json = os.path.join(output_dir, "all_publications_structured.json")
        with open(combined_json, 'w') as f:
            json.dump(all_publications, f, indent=2)
        
        # Save CSV
        combined_csv = os.path.join(output_dir, "all_publications_structured.csv")
        if all_publications:
            with open(combined_csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=all_publications[0].keys())
                writer.writeheader()
                writer.writerows(all_publications)
        
        # Save university summary
        university_summary = os.path.join(output_dir, "university_summary.json")
        with open(university_summary, 'w') as f:
            json.dump(university_results, f, indent=2)
        
        # Save overall summary
        summary = {
            'parse_date': datetime.now().isoformat(),
            'source_directory': base_path,
            'total_universities': len(university_results),
            'total_faculty': len(faculty_results),
            'faculty_with_publications': len([r for r in faculty_results if r['publication_count'] > 0]),
            'total_publications': len(all_publications),
            'university_breakdown': university_results,
            'faculty_results': faculty_results
        }
        
        summary_file = os.path.join(output_dir, "parse_summary_structured.json")
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n🎉 Structured Parsing Complete!")
        print("=" * 50)
        print(f"   🏫 Universities: {summary['total_universities']}")
        print(f"   👨‍🔬 Faculty with publications: {summary['faculty_with_publications']}/{summary['total_faculty']}")
        print(f"   📚 Total publications: {summary['total_publications']}")
        print(f"   📁 Output directory: {output_dir}/")
        
        # Show university breakdown
        print(f"\n📊 University Breakdown:")
        for uni_code, uni_data in university_results.items():
            if uni_data['total_publications'] > 0:
                print(f"   {uni_data['university_info']['university_name']}: {uni_data['total_publications']} publications ({uni_data['faculty_count']} faculty)")
        
        print(f"\n📋 Output Files:")
        print(f"   📄 Combined JSON: {combined_json}")
        print(f"   📄 Combined CSV: {combined_csv}")
        print(f"   📄 University Summary: {university_summary}")
        print(f"   📄 Parse Summary: {summary_file}")
        
        return summary

def main():
    """Main function for parsing structured medline files"""
    
    print("📂 Structured Medline File Parser")
    print("=" * 50)
    print("Parses files from university folder structure:")
    print("data/publications/pubmed/[country]/[province]/[university]/\n")
    
    if len(sys.argv) < 2:
        print("Usage: python3 parse_medline_structured.py <base_directory>")
        print("\nExamples:")
        print("  python3 parse_medline_structured.py data/publications/pubmed/")
        print("  python3 parse_medline_structured.py data/publications/pubmed/CA/ON/")
        sys.exit(1)
    
    base_path = sys.argv[1]
    parser = StructuredMedlineParser()
    
    if os.path.isdir(base_path):
        # Parse structured directory
        summary = parser.parse_structured_directory(base_path)
        
        if summary.get('total_publications', 0) > 0:
            print("\n🚀 Next Steps:")
            print("1. Transfer to VPS: scp -r parsed_publications_structured/ user@vps:/var/www/ff/")
            print("2. Import to database: python3 import_pubmed_data.py parsed_publications_structured/")
        
    else:
        print(f"❌ Directory not found: {base_path}")

if __name__ == "__main__":
    main() 