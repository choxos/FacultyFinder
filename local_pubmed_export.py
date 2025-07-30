#!/usr/bin/env python3
"""
Local PubMed Export Tool
Run this on your local machine to bypass VPS IP blocking
Exports publication data for import to VPS
"""

import os
import json
import csv
import sys
from datetime import datetime
from Bio import Entrez
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LocalPubMedExporter:
    """Export PubMed data from local machine"""
    
    def __init__(self):
        self.email = os.getenv('NCBI_EMAIL', '')
        self.api_key = os.getenv('NCBI_API_KEY', '')
        
        if not self.email or 'example.com' in self.email:
            print("❌ Please set NCBI_EMAIL in .env file")
            sys.exit(1)
        
        # Configure Entrez
        Entrez.email = self.email
        Entrez.tool = "FacultyFinder-Local"
        
        if self.api_key:
            Entrez.api_key = self.api_key
            print(f"✅ Using API key for {self.email}")
        else:
            print(f"⚠️  No API key - using basic rate limits for {self.email}")
    
    def search_author_publications(self, author_name, max_results=50):
        """Search for author publications"""
        
        try:
            print(f"🔍 Searching for {author_name}...")
            
            # Search for publications
            handle = Entrez.esearch(
                db="pubmed",
                term=f"{author_name}[Author]",
                retmax=max_results,
                sort="pub_date",
                retmode="xml"
            )
            
            search_results = Entrez.read(handle)
            handle.close()
            
            pmids = search_results.get("IdList", [])
            
            if not pmids:
                print(f"   No publications found")
                return []
            
            print(f"   Found {len(pmids)} publications")
            
            # Fetch detailed information
            publications = self._fetch_publication_details(pmids)
            
            return publications
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return []
    
    def _fetch_publication_details(self, pmids):
        """Fetch detailed publication information"""
        
        if not pmids:
            return []
        
        try:
            # Fetch details in batches
            batch_size = 20
            all_publications = []
            
            for i in range(0, len(pmids), batch_size):
                batch_pmids = pmids[i:i + batch_size]
                
                handle = Entrez.efetch(
                    db="pubmed",
                    id=",".join(batch_pmids),
                    rettype="medline",
                    retmode="xml"
                )
                
                records = Entrez.read(handle)
                handle.close()
                
                for record in records['PubmedArticle']:
                    try:
                        pub_data = self._parse_publication_record(record)
                        if pub_data:
                            all_publications.append(pub_data)
                    except Exception as e:
                        print(f"      Warning: Failed to parse publication: {str(e)}")
                        continue
            
            return all_publications
            
        except Exception as e:
            print(f"   ❌ Error fetching details: {str(e)}")
            return []
    
    def _parse_publication_record(self, record):
        """Parse a PubMed publication record"""
        
        try:
            medline_citation = record['MedlineCitation']
            article = medline_citation['Article']
            
            # Basic information
            pmid = str(medline_citation['PMID'])
            title = article.get('ArticleTitle', '')
            
            # Handle abstract
            abstract = ""
            if 'Abstract' in article and 'AbstractText' in article['Abstract']:
                abstract_parts = article['Abstract']['AbstractText']
                if isinstance(abstract_parts, list):
                    abstract = " ".join([str(part) for part in abstract_parts])
                else:
                    abstract = str(abstract_parts)
            
            # Authors
            authors = []
            if 'AuthorList' in article:
                for author in article['AuthorList']:
                    if 'LastName' in author and 'ForeName' in author:
                        full_name = f"{author['ForeName']} {author['LastName']}"
                        authors.append(full_name)
            
            authors_str = "; ".join(authors)
            
            # Journal information
            journal = article.get('Journal', {})
            journal_title = journal.get('Title', '') or journal.get('ISOAbbreviation', '')
            
            # Publication date
            pub_date = None
            pub_year = None
            
            if 'DateCompleted' in medline_citation:
                date_completed = medline_citation['DateCompleted']
                try:
                    pub_year = int(date_completed.get('Year', 0))
                    month = int(date_completed.get('Month', 1))
                    day = int(date_completed.get('Day', 1))
                    pub_date = f"{pub_year}-{month:02d}-{day:02d}"
                except (ValueError, TypeError):
                    pass
            
            # DOI
            doi = ""
            if 'ELocationID' in article:
                for elocation in article['ELocationID']:
                    if elocation.attributes.get('EIdType') == 'doi':
                        doi = str(elocation)
                        break
            
            # Volume, issue, pages
            volume = ""
            issue = ""
            pages = ""
            
            if 'JournalIssue' in journal:
                volume = journal['JournalIssue'].get('Volume', '')
                issue = journal['JournalIssue'].get('Issue', '')
            
            if 'Pagination' in article and 'MedlinePgn' in article['Pagination']:
                pages = article['Pagination']['MedlinePgn']
            
            publication_data = {
                'pmid': pmid,
                'doi': doi,
                'title': title,
                'abstract': abstract,
                'authors': authors_str,
                'journal_name': journal_title,
                'publication_date': pub_date,
                'publication_year': pub_year,
                'volume': volume,
                'issue': issue,
                'pages': pages,
                'created_at': datetime.now().isoformat()
            }
            
            return publication_data
            
        except Exception as e:
            print(f"      Parse error: {str(e)}")
            return None
    
    def export_faculty_publications(self, faculty_list, output_dir="pubmed_exports"):
        """Export publications for a list of faculty"""
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Summary data
        summary = {
            'export_date': datetime.now().isoformat(),
            'total_faculty': len(faculty_list),
            'faculty_with_publications': 0,
            'total_publications': 0,
            'faculty_results': []
        }
        
        all_publications = []
        
        for i, faculty_name in enumerate(faculty_list):
            print(f"\n[{i+1}/{len(faculty_list)}] Processing {faculty_name}")
            
            # Search for publications
            publications = self.search_author_publications(faculty_name, max_results=100)
            
            if publications:
                summary['faculty_with_publications'] += 1
                summary['total_publications'] += len(publications)
                
                # Save individual faculty file
                faculty_file = f"{output_dir}/{faculty_name.replace(' ', '_').replace(',', '')}_publications.json"
                with open(faculty_file, 'w') as f:
                    json.dump({
                        'faculty_name': faculty_name,
                        'publication_count': len(publications),
                        'publications': publications
                    }, f, indent=2)
                
                # Add to all publications
                for pub in publications:
                    pub['faculty_name'] = faculty_name
                    all_publications.append(pub)
                
                print(f"   ✅ Exported {len(publications)} publications to {faculty_file}")
            
            summary['faculty_results'].append({
                'name': faculty_name,
                'publication_count': len(publications)
            })
        
        # Save combined files
        combined_json = f"{output_dir}/all_publications.json"
        with open(combined_json, 'w') as f:
            json.dump(all_publications, f, indent=2)
        
        # Save CSV for easy import
        combined_csv = f"{output_dir}/all_publications.csv"
        if all_publications:
            with open(combined_csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=all_publications[0].keys())
                writer.writeheader()
                writer.writerows(all_publications)
        
        # Save summary
        summary_file = f"{output_dir}/export_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n🎉 Export Complete!")
        print(f"   📊 Summary: {summary['faculty_with_publications']}/{summary['total_faculty']} faculty with publications")
        print(f"   📚 Total publications: {summary['total_publications']}")
        print(f"   📁 Files saved to: {output_dir}/")
        print(f"   📋 Combined JSON: {combined_json}")
        print(f"   📋 Combined CSV: {combined_csv}")
        
        return summary

def main():
    """Main function for local export"""
    
    print("🏠 Local PubMed Export Tool")
    print("=" * 40)
    print("This tool runs PubMed searches from your local machine")
    print("to bypass VPS IP blocking issues.\n")
    
    # Sample McMaster faculty list
    mcmaster_faculty = [
        "Gordon Guyatt",
        "Salim Yusuf", 
        "Hertzel Gerstein",
        "Mohit Bhandari",
        "Mark Crowther",
        "Deborah Cook",
        "Andrew Mente",
        "Bram Rochwerg"
    ]
    
    print("📋 Sample faculty list loaded:")
    for i, name in enumerate(mcmaster_faculty, 1):
        print(f"   {i}. {name}")
    
    print(f"\n🚀 Starting export for {len(mcmaster_faculty)} faculty...")
    
    exporter = LocalPubMedExporter()
    summary = exporter.export_faculty_publications(mcmaster_faculty)
    
    print("\n📤 Transfer to VPS:")
    print("1. Copy the pubmed_exports/ folder to your VPS")
    print("2. Run: scp -r pubmed_exports/ user@your-vps:/var/www/ff/")
    print("3. Import the data using the provided import script")

if __name__ == "__main__":
    main() 