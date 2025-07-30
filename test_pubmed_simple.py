#!/usr/bin/env python3
"""
Simple PubMed test script with proper error handling
Replaces the original test_pubmed.py with better diagnostics
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_pubmed_basic():
    """Test basic PubMed functionality with proper error handling"""
    
    try:
        from Bio import Entrez
        print("✅ Biopython imported successfully")
    except ImportError:
        print("❌ Biopython not installed. Run: pip install biopython")
        return False
    
    # Check email configuration
    email = os.getenv('NCBI_EMAIL', '')
    if not email or 'example.com' in email:
        print("❌ Invalid NCBI_EMAIL. Please set a real email address in .env:")
        print("   echo 'NCBI_EMAIL=your.real.email@domain.com' >> .env")
        return False
    
    print(f"📧 Using email: {email}")
    
    # Configure Entrez
    Entrez.email = email
    Entrez.tool = "FacultyFinder"
    
    # Set API key if available
    api_key = os.getenv('NCBI_API_KEY')
    if api_key:
        Entrez.api_key = api_key
        print("🔑 Using NCBI API key")
    
    try:
        print("🔍 Testing PubMed search...")
        
        # Simple test search
        handle = Entrez.esearch(
            db="pubmed",
            term="Guyatt G[Author]",
            retmax=3,
            retmode="xml"
        )
        
        results = Entrez.read(handle)
        handle.close()
        
        pmids = results.get("IdList", [])
        count = results.get("Count", "0")
        
        print(f"✅ Search successful!")
        print(f"   Total results found: {count}")
        print(f"   Retrieved PMIDs: {len(pmids)}")
        
        if pmids:
            print(f"   Sample PMIDs: {pmids[:3]}")
            
            # Test fetching details for one publication
            print("📄 Testing publication details...")
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
                print(f"✅ Successfully fetched: {title[:60]}...")
            else:
                print("⚠️  Could not parse publication details")
        
        return True
        
    except Exception as e:
        print(f"❌ PubMed search failed: {str(e)}")
        
        # Provide helpful error messages
        error_str = str(e).lower()
        if "xml" in error_str:
            print("💡 This is likely due to:")
            print("   • Invalid email address (use your real email)")
            print("   • NCBI API returning error instead of XML")
            print("   • Network connectivity issues")
        elif "http" in error_str:
            print("💡 This appears to be a network/HTTP error")
        elif "rate" in error_str or "limit" in error_str:
            print("💡 Rate limiting detected - consider getting an API key")
        
        return False

def main():
    """Main test function"""
    print("🧪 Simple PubMed Integration Test")
    print("=" * 40)
    
    if test_pubmed_basic():
        print("\n🎉 PubMed integration is working!")
        print("✅ You can now use the publication system")
    else:
        print("\n❌ PubMed integration failed")
        print("🔧 Run ./fix_pubmed_config.sh to fix configuration")
        sys.exit(1)

if __name__ == "__main__":
    main() 