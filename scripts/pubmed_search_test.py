#!/usr/bin/env python3
"""
PubMed Search Test Script
Demonstrates integration with NCBI PubMed API for faculty publication search
"""

import os
import sys
import json
import time
from datetime import datetime
import requests
from Bio import Entrez

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def setup_entrez():
    """Configure Entrez settings for PubMed access"""
    # Set email for NCBI (required for API access)
    Entrez.email = "facultyfinder@example.com"  # Replace with your email
    Entrez.tool = "FacultyFinder"
    
    print("✅ Entrez configured for PubMed access")

def search_pubmed_publications(author_name, max_results=10):
    """
    Search PubMed for publications by a specific author
    
    Args:
        author_name (str): Full name of the author (e.g., "Smith J")
        max_results (int): Maximum number of results to return
    
    Returns:
        list: List of publication dictionaries
    """
    
    print(f"🔍 Searching PubMed for publications by: {author_name}")
    
    try:
        # Search for publications
        search_query = f"{author_name}[Author]"
        
        # Perform the search
        handle = Entrez.esearch(
            db="pubmed",
            term=search_query,
            retmax=max_results,
            sort="pub_date",
            retmode="xml"
        )
        
        search_results = Entrez.read(handle)
        handle.close()
        
        pmids = search_results["IdList"]
        
        if not pmids:
            print(f"❌ No publications found for {author_name}")
            return []
        
        print(f"📄 Found {len(pmids)} publications")
        
        # Fetch detailed information for each publication
        publications = fetch_publication_details(pmids)
        
        return publications
        
    except Exception as e:
        print(f"❌ Error searching PubMed: {str(e)}")
        return []

def fetch_publication_details(pmids):
    """
    Fetch detailed information for a list of PubMed IDs
    
    Args:
        pmids (list): List of PubMed IDs
    
    Returns:
        list: List of detailed publication information
    """
    
    if not pmids:
        return []
    
    try:
        # Fetch detailed records
        handle = Entrez.efetch(
            db="pubmed",
            id=",".join(pmids),
            rettype="medline",
            retmode="xml"
        )
        
        records = Entrez.read(handle)
        handle.close()
        
        publications = []
        
        for record in records['PubmedArticle']:
            try:
                article = record['MedlineCitation']['Article']
                
                # Extract basic information
                title = article.get('ArticleTitle', 'No title available')
                
                # Extract authors
                authors = []
                if 'AuthorList' in article:
                    for author in article['AuthorList']:
                        if 'LastName' in author and 'ForeName' in author:
                            full_name = f"{author['ForeName']} {author['LastName']}"
                            authors.append(full_name)
                        elif 'CollectiveName' in author:
                            authors.append(author['CollectiveName'])
                
                # Extract journal information
                journal = article.get('Journal', {})
                journal_title = journal.get('Title', 'Unknown Journal')
                
                # Extract publication date
                pub_date = "Unknown Date"
                if 'Journal' in article and 'JournalIssue' in article['Journal']:
                    issue = article['Journal']['JournalIssue']
                    if 'PubDate' in issue:
                        date_info = issue['PubDate']
                        year = date_info.get('Year', '')
                        month = date_info.get('Month', '')
                        pub_date = f"{month} {year}".strip()
                
                # Extract abstract
                abstract = ""
                if 'Abstract' in article and 'AbstractText' in article['Abstract']:
                    abstract_parts = article['Abstract']['AbstractText']
                    if isinstance(abstract_parts, list):
                        abstract = " ".join([str(part) for part in abstract_parts])
                    else:
                        abstract = str(abstract_parts)
                
                # Get PMID
                pmid = record['MedlineCitation']['PMID']
                
                # Create publication record
                publication = {
                    'pmid': str(pmid),
                    'title': title,
                    'authors': authors,
                    'journal': journal_title,
                    'publication_date': pub_date,
                    'abstract': abstract[:500] + "..." if len(abstract) > 500 else abstract,
                    'pubmed_url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                }
                
                publications.append(publication)
                
            except Exception as e:
                print(f"⚠️  Error processing publication record: {str(e)}")
                continue
        
        return publications
        
    except Exception as e:
        print(f"❌ Error fetching publication details: {str(e)}")
        return []

def display_publications(publications, author_name):
    """Display publications in a formatted way"""
    
    if not publications:
        print(f"❌ No publications found for {author_name}")
        return
    
    print(f"\n📚 Publications for {author_name}")
    print("=" * 80)
    
    for i, pub in enumerate(publications, 1):
        print(f"\n{i}. {pub['title']}")
        print(f"   Authors: {', '.join(pub['authors'][:3])}{'...' if len(pub['authors']) > 3 else ''}")
        print(f"   Journal: {pub['journal']}")
        print(f"   Date: {pub['publication_date']}")
        print(f"   PMID: {pub['pmid']}")
        print(f"   URL: {pub['pubmed_url']}")
        
        if pub['abstract']:
            print(f"   Abstract: {pub['abstract']}")
        
        print("-" * 80)

def save_results_to_file(publications, author_name):
    """Save search results to a JSON file"""
    
    if not publications:
        return
    
    # Create results directory if it doesn't exist
    results_dir = "pubmed_search_results"
    os.makedirs(results_dir, exist_ok=True)
    
    # Save to JSON file
    filename = f"{results_dir}/{author_name.replace(' ', '_')}_publications.json"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'author': author_name,
                'search_date': datetime.now().isoformat(),
                'total_publications': len(publications),
                'publications': publications
            }, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Results saved to: {filename}")
        
    except Exception as e:
        print(f"❌ Error saving results: {str(e)}")

def test_faculty_searches():
    """Test PubMed searches for sample faculty members"""
    
    # Sample faculty names from our database
    test_faculty = [
        "Gordon Guyatt",  # McMaster HEI faculty
        "Salim Yusuf",    # Well-known researcher
        "Mohit Bhandari", # Orthopedic surgeon researcher
        "Hertzel Gerstein" # Diabetes researcher
    ]
    
    print("🧪 Testing PubMed searches for sample faculty members")
    print("=" * 60)
    
    all_results = {}
    
    for faculty_name in test_faculty:
        print(f"\n🔬 Testing search for: {faculty_name}")
        
        # Search for publications
        publications = search_pubmed_publications(faculty_name, max_results=5)
        
        if publications:
            display_publications(publications, faculty_name)
            save_results_to_file(publications, faculty_name)
            all_results[faculty_name] = publications
        
        # Be respectful to NCBI servers
        time.sleep(1)
    
    # Save summary
    summary_file = "pubmed_search_results/search_summary.json"
    try:
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump({
                'test_date': datetime.now().isoformat(),
                'faculty_tested': list(all_results.keys()),
                'total_faculty': len(all_results),
                'total_publications': sum(len(pubs) for pubs in all_results.values()),
                'results': all_results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n📊 Summary saved to: {summary_file}")
        
    except Exception as e:
        print(f"❌ Error saving summary: {str(e)}")

def main():
    """Main function to run PubMed search tests"""
    
    print("🚀 FacultyFinder PubMed Search Test")
    print("=" * 50)
    
    # Check if Biopython is available
    try:
        from Bio import Entrez
        print("✅ Biopython is available")
    except ImportError:
        print("❌ Biopython not found. Please install with: pip install biopython")
        return
    
    # Setup Entrez
    setup_entrez()
    
    # Test searches
    test_faculty_searches()
    
    print("\n🎉 PubMed search test completed!")
    print("\n📝 Next steps:")
    print("   1. Review search results in pubmed_search_results/")
    print("   2. Integrate with main FacultyFinder database")
    print("   3. Implement caching for repeated searches")
    print("   4. Add publication metrics and journal rankings")

if __name__ == "__main__":
    main() 