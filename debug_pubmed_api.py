#!/usr/bin/env python3
"""
Debug script for PubMed API issues
Helps diagnose XML parsing and API connection problems
"""

import os
import sys
import requests
from Bio import Entrez
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_ncbi_connection():
    """Test basic connection to NCBI"""
    print("🧪 Testing NCBI API Connection...")
    
    # Use a real email address (required by NCBI)
    real_email = os.getenv('NCBI_EMAIL', 'your.real.email@domain.com')
    
    if 'example.com' in real_email:
        print("❌ WARNING: You're using an example email address!")
        print("   NCBI requires a real email address for API access.")
        print("   Please set NCBI_EMAIL in your .env file to your real email.")
        return False
    
    print(f"📧 Using email: {real_email}")
    
    # Configure Entrez
    Entrez.email = real_email
    Entrez.tool = "FacultyFinder"
    
    if os.getenv('NCBI_API_KEY'):
        Entrez.api_key = os.getenv('NCBI_API_KEY')
        print("🔑 Using NCBI API key")
    else:
        print("⚠️  No API key - using default rate limits")
    
    try:
        # Test with a simple search
        print("\n🔍 Testing simple search...")
        handle = Entrez.esearch(
            db="pubmed",
            term="cancer[Title]",
            retmax=1,
            retmode="xml"
        )
        
        # Read the response
        result = Entrez.read(handle)
        handle.close()
        
        print(f"✅ Search successful! Found {result.get('Count', 0)} total results")
        return True
        
    except Exception as e:
        print(f"❌ Search failed: {str(e)}")
        
        # Try to get the raw response to debug
        try:
            print("\n🔍 Trying raw HTTP request to debug...")
            url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
            params = {
                'db': 'pubmed',
                'term': 'cancer[Title]',
                'retmax': '1',
                'retmode': 'xml',
                'email': real_email,
                'tool': 'FacultyFinder'
            }
            
            response = requests.get(url, params=params)
            print(f"HTTP Status: {response.status_code}")
            print(f"Content-Type: {response.headers.get('content-type', 'unknown')}")
            
            if response.status_code == 200:
                content = response.text[:500]  # First 500 chars
                print(f"Response preview: {content}")
                
                if not content.startswith('<?xml'):
                    print("❌ Response is not XML! Likely an error page.")
                else:
                    print("✅ Response appears to be valid XML")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"Response: {response.text[:200]}")
                
        except Exception as debug_e:
            print(f"❌ Debug request failed: {str(debug_e)}")
        
        return False

def test_author_search():
    """Test searching for a specific author"""
    print("\n👨‍🔬 Testing author search...")
    
    real_email = os.getenv('NCBI_EMAIL', 'your.real.email@domain.com')
    
    if 'example.com' in real_email:
        print("❌ Cannot test author search with example email")
        return False
    
    Entrez.email = real_email
    Entrez.tool = "FacultyFinder"
    
    if os.getenv('NCBI_API_KEY'):
        Entrez.api_key = os.getenv('NCBI_API_KEY')
    
    try:
        # Search for Gordon Guyatt (a real McMaster professor)
        print("🔍 Searching for Gordon Guyatt...")
        handle = Entrez.esearch(
            db="pubmed",
            term="Guyatt G[Author]",
            retmax=5,
            retmode="xml"
        )
        
        result = Entrez.read(handle)
        handle.close()
        
        pmids = result.get("IdList", [])
        print(f"✅ Found {len(pmids)} publications")
        
        if pmids:
            print(f"   Sample PMIDs: {pmids[:3]}")
            
            # Test fetching details for one publication
            print("📄 Testing publication details fetch...")
            detail_handle = Entrez.efetch(
                db="pubmed",
                id=pmids[0],
                rettype="medline",
                retmode="xml"
            )
            
            details = Entrez.read(detail_handle)
            detail_handle.close()
            
            if details and 'PubmedArticle' in details:
                article = details['PubmedArticle'][0]
                title = article['MedlineCitation']['Article'].get('ArticleTitle', 'No title')
                print(f"✅ Successfully fetched details for: {title[:60]}...")
            else:
                print("❌ Failed to parse publication details")
        
        return True
        
    except Exception as e:
        print(f"❌ Author search failed: {str(e)}")
        return False

def main():
    """Main debug function"""
    print("🔬 PubMed API Debug Tool")
    print("=" * 50)
    
    # Check environment
    print("📋 Environment Check:")
    email = os.getenv('NCBI_EMAIL', 'NOT_SET')
    api_key = os.getenv('NCBI_API_KEY', 'NOT_SET')
    
    print(f"   NCBI_EMAIL: {email}")
    print(f"   NCBI_API_KEY: {'SET' if api_key != 'NOT_SET' else 'NOT_SET'}")
    
    if email == 'NOT_SET' or 'example.com' in email:
        print("\n❌ CRITICAL: Invalid email address!")
        print("   Please set a real email in your .env file:")
        print("   echo 'NCBI_EMAIL=your.real.email@domain.com' >> .env")
        return
    
    # Test basic connection
    if not test_ncbi_connection():
        return
    
    # Test author search
    if not test_author_search():
        return
    
    print("\n🎉 All tests passed!")
    print("✅ PubMed API is working correctly")
    print("🚀 You can now use the PubMed integration")

if __name__ == "__main__":
    main() 