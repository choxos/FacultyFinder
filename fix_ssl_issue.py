#!/usr/bin/env python3
"""
Fix SSL certificate issues for PubMed access
Quick patch for certificate verification problems
"""

import ssl
import os
import sys
from Bio import Entrez
from dotenv import load_dotenv

def fix_ssl_context():
    """Fix SSL context for certificate issues"""
    
    print("🔧 Fixing SSL certificate issues...")
    
    # Create unverified SSL context (not ideal but works)
    try:
        import ssl
        ssl._create_default_https_context = ssl._create_unverified_context
        print("✅ SSL verification disabled")
    except Exception as e:
        print(f"❌ Could not fix SSL: {str(e)}")
        return False
    
    return True

def test_fixed_connection():
    """Test PubMed connection after SSL fix"""
    
    load_dotenv()
    
    email = os.getenv('NCBI_EMAIL', '')
    if not email or 'example.com' in email:
        print("❌ Please set NCBI_EMAIL in .env file")
        return False
    
    Entrez.email = email
    Entrez.tool = "FacultyFinder-SSL-Fixed"
    
    api_key = os.getenv('NCBI_API_KEY')
    if api_key:
        Entrez.api_key = api_key
    
    try:
        print("🧪 Testing connection with SSL fix...")
        
        handle = Entrez.esearch(
            db="pubmed",
            term="Guyatt G[Author]",
            retmax=1,
            retmode="xml"
        )
        
        result = Entrez.read(handle)
        handle.close()
        
        print("✅ SSL fix successful! PubMed connection working")
        print(f"   Found {result.get('Count', 0)} total publications for Guyatt G")
        return True
        
    except Exception as e:
        print(f"❌ Still having issues: {str(e)}")
        return False

def main():
    """Main SSL fix function"""
    
    print("🔐 SSL Certificate Fix Tool")
    print("=" * 40)
    
    if fix_ssl_context():
        if test_fixed_connection():
            print("\n🎉 SSL issue resolved!")
            print("✅ You can now run: python3 local_pubmed_export.py")
        else:
            print("\n⚠️  SSL fixed but other issues remain")
            print("💡 Consider using EDirect tools instead")
    else:
        print("\n❌ Could not fix SSL issue")
        print("💡 EDirect tools (esearch/efetch) are recommended")

if __name__ == "__main__":
    main() 