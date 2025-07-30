#!/usr/bin/env python3
"""
PubMed Faculty Searcher - XML-based with Complete Fields
Reads faculty CSV files and runs EDirect searches in XML format
Creates individual PMID JSON files with ALL available fields including abstracts
"""

import os
import csv
import json
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Optional, Set
import argparse

class PubMedFacultySearcher:
    """XML-based PubMed searcher with complete field extraction"""
    
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
    
    def run_edirect_xml_search(self, query: str, search_type: str) -> Optional[str]:
        """Run a single EDirect search and return XML result"""
        
        try:
            # Run esearch | efetch with XML format for complete data
            cmd = f"esearch -db pubmed -query '{query}' | efetch -format xml"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout
            else:
                print(f"      ❌ EDirect command failed for {search_type}")
                if result.stderr:
                    print(f"         Error: {result.stderr.strip()}")
                return None
                
        except subprocess.TimeoutExpired:
            print(f"      ⏱️  Search timeout for {search_type}")
            return None
        except Exception as e:
            print(f"      ❌ Search error for {search_type}: {str(e)}")
            return None

    def parse_pubmed_xml_article(self, article_elem) -> Optional[Dict]:
        """Parse a single PubmedArticle XML element into comprehensive JSON"""
        
        try:
            pub_data = {}
            
            # Basic identifiers
            pmid_elem = article_elem.find('.//PMID')
            if pmid_elem is not None:
                pub_data['pmid'] = pmid_elem.text
                pub_data['uid'] = pmid_elem.text  # For compatibility
            
            # Article information
            article = article_elem.find('.//Article')
            if article is not None:
                # Title
                title_elem = article.find('ArticleTitle')
                if title_elem is not None:
                    pub_data['title'] = title_elem.text or ""
                
                # Abstract - COMPREHENSIVE EXTRACTION
                abstract_elem = article.find('Abstract')
                if abstract_elem is not None:
                    abstract_parts = []
                    for abstract_text in abstract_elem.findall('AbstractText'):
                        label = abstract_text.get('Label', '')
                        text = abstract_text.text or ""
                        if label:
                            abstract_parts.append(f"{label}: {text}")
                        else:
                            abstract_parts.append(text)
                    pub_data['abstract'] = " ".join(abstract_parts).strip()
                else:
                    pub_data['abstract'] = ""
                
                # Authors - COMPLETE INFORMATION
                authors = []
                author_list = article.find('AuthorList')
                if author_list is not None:
                    for author in author_list.findall('Author'):
                        author_data = {}
                        
                        # Name components
                        lastname = author.find('LastName')
                        forename = author.find('ForeName')
                        initials = author.find('Initials')
                        
                        if lastname is not None:
                            author_data['last_name'] = lastname.text or ""
                        if forename is not None:
                            author_data['fore_name'] = forename.text or ""
                        if initials is not None:
                            author_data['initials'] = initials.text or ""
                        
                        # Full name for compatibility
                        if lastname is not None and forename is not None:
                            author_data['name'] = f"{forename.text} {lastname.text}"
                        elif lastname is not None:
                            author_data['name'] = lastname.text
                        
                        # Affiliations
                        affiliations = []
                        for affiliation in author.findall('AffiliationInfo/Affiliation'):
                            if affiliation.text:
                                affiliations.append(affiliation.text)
                        author_data['affiliations'] = affiliations
                        
                        # ORCID if available
                        for identifier in author.findall('Identifier'):
                            if identifier.get('Source') == 'ORCID':
                                author_data['orcid'] = identifier.text
                        
                        authors.append(author_data)
                
                pub_data['authors'] = authors
                
                # Journal Information - COMPLETE
                journal = article.find('Journal')
                if journal is not None:
                    journal_data = {}
                    
                    # Journal title
                    title_elem = journal.find('Title')
                    if title_elem is not None:
                        journal_data['title'] = title_elem.text or ""
                    
                    # ISO abbreviation
                    iso_abbrev = journal.find('ISOAbbreviation')
                    if iso_abbrev is not None:
                        journal_data['iso_abbreviation'] = iso_abbrev.text or ""
                    
                    # ISSN
                    issn_elem = journal.find('ISSN')
                    if issn_elem is not None:
                        journal_data['issn'] = issn_elem.text or ""
                        journal_data['issn_type'] = issn_elem.get('IssnType', '')
                    
                    # Journal Issue
                    issue = journal.find('JournalIssue')
                    if issue is not None:
                        volume_elem = issue.find('Volume')
                        issue_elem = issue.find('Issue')
                        
                        if volume_elem is not None:
                            journal_data['volume'] = volume_elem.text or ""
                        if issue_elem is not None:
                            journal_data['issue'] = issue_elem.text or ""
                        
                        # Publication date
                        pub_date = issue.find('PubDate')
                        if pub_date is not None:
                            year_elem = pub_date.find('Year')
                            month_elem = pub_date.find('Month')
                            day_elem = pub_date.find('Day')
                            
                            if year_elem is not None:
                                journal_data['pub_year'] = year_elem.text or ""
                            if month_elem is not None:
                                journal_data['pub_month'] = month_elem.text or ""
                            if day_elem is not None:
                                journal_data['pub_day'] = day_elem.text or ""
                    
                    pub_data['journal'] = journal_data
                
                # Pagination
                pagination = article.find('Pagination')
                if pagination is not None:
                    start_page = pagination.find('StartPage')
                    end_page = pagination.find('EndPage')
                    medline_pgn = pagination.find('MedlinePgn')
                    
                    if start_page is not None:
                        pub_data['start_page'] = start_page.text or ""
                    if end_page is not None:
                        pub_data['end_page'] = end_page.text or ""
                    if medline_pgn is not None:
                        pub_data['pages'] = medline_pgn.text or ""
                
                # Language
                language_elem = article.find('Language')
                if language_elem is not None:
                    pub_data['language'] = language_elem.text or ""
                
                # Publication Types
                pub_types = []
                pub_type_list = article.find('PublicationTypeList')
                if pub_type_list is not None:
                    for pub_type in pub_type_list.findall('PublicationType'):
                        if pub_type.text:
                            pub_types.append(pub_type.text)
                pub_data['publication_types'] = pub_types
            
            # MeSH Keywords/Terms
            mesh_list = article_elem.find('.//MeshHeadingList')
            keywords = []
            if mesh_list is not None:
                for mesh_heading in mesh_list.findall('MeshHeading'):
                    descriptor = mesh_heading.find('DescriptorName')
                    if descriptor is not None and descriptor.text:
                        keywords.append(descriptor.text)
            pub_data['keywords'] = keywords
            
            # Article IDs (DOI, PMC, etc.)
            article_ids = {}
            article_id_list = article_elem.find('.//ArticleIdList')
            if article_id_list is not None:
                for article_id in article_id_list.findall('ArticleId'):
                    id_type = article_id.get('IdType', '')
                    if id_type and article_id.text:
                        article_ids[id_type] = article_id.text
            pub_data['article_ids'] = article_ids
            
            # DOI (for easy access)
            if 'doi' in article_ids:
                pub_data['doi'] = article_ids['doi']
            
            # PMC ID (for easy access)
            if 'pmc' in article_ids:
                pub_data['pmc_id'] = article_ids['pmc']
            
            # Dates - COMPREHENSIVE
            dates = {}
            
            # Date completed
            date_completed = article_elem.find('.//DateCompleted')
            if date_completed is not None:
                year = date_completed.find('Year')
                month = date_completed.find('Month')
                day = date_completed.find('Day')
                if year is not None:
                    dates['completed'] = f"{year.text or ''}-{month.text if month is not None else ''}-{day.text if day is not None else ''}"
            
            # Date revised
            date_revised = article_elem.find('.//DateRevised')
            if date_revised is not None:
                year = date_revised.find('Year')
                month = date_revised.find('Month')
                day = date_revised.find('Day')
                if year is not None:
                    dates['revised'] = f"{year.text or ''}-{month.text if month is not None else ''}-{day.text if day is not None else ''}"
            
            pub_data['dates'] = dates
            
            # Chemical List (if available)
            chemical_list = article_elem.find('.//ChemicalList')
            chemicals = []
            if chemical_list is not None:
                for chemical in chemical_list.findall('Chemical'):
                    substance = chemical.find('NameOfSubstance')
                    if substance is not None and substance.text:
                        chemicals.append(substance.text)
            pub_data['chemicals'] = chemicals
            
            # Grant information
            grants = []
            grant_list = article_elem.find('.//GrantList')
            if grant_list is not None:
                for grant in grant_list.findall('Grant'):
                    grant_data = {}
                    grant_id = grant.find('GrantID')
                    agency = grant.find('Agency')
                    country = grant.find('Country')
                    
                    if grant_id is not None:
                        grant_data['grant_id'] = grant_id.text or ""
                    if agency is not None:
                        grant_data['agency'] = agency.text or ""
                    if country is not None:
                        grant_data['country'] = country.text or ""
                    
                    if grant_data:
                        grants.append(grant_data)
            pub_data['grants'] = grants
            
            return pub_data
            
        except Exception as e:
            print(f"         ⚠️ Error parsing article XML: {str(e)}")
            return None
    
    def parse_and_save_publications(self, xml_data: str, search_type: str) -> Set[str]:
        """Parse XML response and save individual publication files"""
        
        pmids = set()
        
        try:
            # Parse XML response
            root = ET.fromstring(xml_data)
            
            # EDirect XML structure: PubmedArticleSet contains multiple PubmedArticle elements
            articles = root.findall('.//PubmedArticle')
            
            print(f"      📚 Found {len(articles)} publications for {search_type}")
            
            # Create directory for PMID files
            os.makedirs(self.base_publications_path, exist_ok=True)
            
            for article_elem in articles:
                # Parse this article into comprehensive JSON
                pub_data = self.parse_pubmed_xml_article(article_elem)
                
                if pub_data and 'pmid' in pub_data:
                    pmid = pub_data['pmid']
                    
                    # Save individual PMID JSON file
                    pmid_file = os.path.join(self.base_publications_path, f"{pmid}.json")
                    
                    # Add search metadata to the publication
                    pub_data['search_metadata'] = {
                        'search_type': search_type,
                        'retrieved_date': datetime.now().isoformat(),
                        'pmid': pmid
                    }
                    
                    with open(pmid_file, 'w', encoding='utf-8') as f:
                        json.dump(pub_data, f, indent=2, ensure_ascii=False)
                    
                    pmids.add(pmid)
                    print(f"        ✅ Saved {pmid}.json (with abstract)")
                else:
                    print(f"        ⚠️  Could not parse article XML")
            
            return pmids
            
        except ET.ParseError as e:
            print(f"      ❌ XML parsing error: {str(e)}")
            return set()
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
            xml_result = self.run_edirect_xml_search(query, search_type)
            
            if xml_result:
                # Parse and save individual publications
                pmids = self.parse_and_save_publications(xml_result, search_type)
                
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
        """Run PubMed searches for faculty members with complete field extraction"""
        
        print("🔬 **PubMed Faculty Searcher - XML-based with Complete Fields**\n")
        
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
        print(f"📋 Output: Individual JSON files with ALL fields including abstracts")
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
        print("📊 **FINAL SEARCH STATISTICS - XML with Complete Fields**")
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
        print(f"   • Individual PMID files created: {stats['total_all_publications']} (with complete data)")
        
        print(f"\n🔍 Search Success:")
        print(f"   • Successful all-publication searches: {stats['successful_all_searches']}")
        print(f"   • Successful current-affiliation searches: {stats['successful_current_searches']}")
        
        print(f"\n📁 Output Locations:")
        print(f"   • PMID JSON files: {self.base_publications_path}/")
        print(f"   • Faculty CSV tracking: {self.base_faculties_path}/[country]/[province]/[university]/publications/")
        
        print(f"\n🎯 Enhanced Data Includes:")
        print(f"   • ✅ Complete abstracts")
        print(f"   • ✅ Full author details with affiliations")
        print(f"   • ✅ Complete journal information")
        print(f"   • ✅ MeSH keywords/terms")
        print(f"   • ✅ DOI, PMC IDs, publication types")
        print(f"   • ✅ Grant information and funding")
        print(f"   • ✅ Chemical substances and dates")
        
        print("=" * 80)

def main():
    """Main function with command line interface"""
    
    parser = argparse.ArgumentParser(description='PubMed Faculty Searcher - XML-based with Complete Fields including Abstracts')
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
    
    print(f"🚀 Starting PubMed searches with complete field extraction...")
    print(f"📄 CSV file: {args.csv_file}")
    print(f"📂 PMID files output: {args.publications_base}/")
    print(f"📂 Faculty CSV output: {args.faculties_base}/[country]/[province]/[university]/publications/")
    print(f"🎯 Enhanced: Abstracts, affiliations, MeSH terms, grants, and more!")
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
    
    print(f"\n🎉 PubMed search with complete fields completed successfully!")
    return 0

if __name__ == "__main__":
    exit(main()) 