#!/usr/bin/env python3
"""
Fix NCBI blocking issues for VPS/cloud servers
Implements proper headers, delays, and alternative approaches
"""

import os
import time
import requests
from Bio import Entrez
from dotenv import load_dotenv
import urllib.parse

load_dotenv()

def test_with_better_headers():
    """Test NCBI access with improved headers and timing"""
    
    email = os.getenv('NCBI_EMAIL')
    api_key = os.getenv('NCBI_API_KEY')
    
    print("🛠️  Testing with improved headers and timing...")
    
    # Configure Entrez with better settings
    Entrez.email = email
    Entrez.tool = "FacultyFinder-Academic-Research"  # More descriptive tool name
    
    if api_key:
        Entrez.api_key = api_key
    
    # Add longer delays to avoid triggering security
    time.sleep(2)
    
    try:
        print("⏱️  Adding delay before request...")
        time.sleep(3)  # 3-second delay
        
        # Use a simpler search term
        handle = Entrez.esearch(
            db="pubmed",
            term="cancer",  # Simple, common term
            retmax=1,
            retmode="xml",
            usehistory="n"  # Don't use history server
        )
        
        result = Entrez.read(handle)
        handle.close()
        
        print("✅ Success with improved headers!")
        return True
        
    except Exception as e:
        print(f"❌ Still blocked: {str(e)}")
        return False

def test_direct_http_with_headers():
    """Test direct HTTP requests with proper headers"""
    
    print("\n🌐 Testing direct HTTP with proper headers...")
    
    email = os.getenv('NCBI_EMAIL')
    api_key = os.getenv('NCBI_API_KEY')
    
    # Construct URL manually
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    
    params = {
        'db': 'pubmed',
        'term': 'cancer',
        'retmax': '1',
        'retmode': 'xml',
        'email': email,
        'tool': 'FacultyFinder-Academic-Research'
    }
    
    if api_key:
        params['api_key'] = api_key
    
    # Add proper headers to appear more legitimate
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 FacultyFinder/1.0',
        'Accept': 'application/xml, text/xml, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        print("⏱️  Adding delay before HTTP request...")
        time.sleep(5)  # 5-second delay
        
        response = requests.get(base_url, params=params, headers=headers, timeout=30)
        
        print(f"HTTP Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'unknown')}")
        
        if response.status_code == 200:
            content = response.text[:200]
            print(f"Response preview: {content}")
            
            if content.startswith('<?xml'):
                print("✅ Success! Getting XML response")
                return True
            elif 'error' in content.lower() or 'blocked' in content.lower():
                print("❌ Still getting error page")
                return False
            else:
                print("⚠️  Unexpected response format")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ HTTP request failed: {str(e)}")
        return False

def check_ip_reputation():
    """Check if the current IP might be problematic"""
    
    print("\n🔍 Checking IP reputation...")
    
    try:
        # Get current IP
        ip_response = requests.get('https://httpbin.org/ip', timeout=10)
        current_ip = ip_response.json().get('origin', 'unknown')
        print(f"Current IP: {current_ip}")
        
        # Check if it's a known cloud provider
        if any(provider in current_ip for provider in ['amazonaws', 'google', 'azure', 'digital']):
            print("⚠️  Detected cloud/VPS IP - this may be flagged by NCBI")
        
        # Try a different service to test connectivity
        test_response = requests.get('https://www.ncbi.nlm.nih.gov/', timeout=10)
        if test_response.status_code == 200:
            print("✅ Can reach NCBI main website")
        else:
            print("❌ Cannot reach NCBI main website")
            
    except Exception as e:
        print(f"❌ IP check failed: {str(e)}")

def suggest_alternatives():
    """Suggest alternative approaches"""
    
    print("\n💡 Alternative Solutions:")
    print("=" * 50)
    
    print("1. 🔄 **Retry Later**")
    print("   • NCBI blocking may be temporary")
    print("   • Try again in 1-2 hours")
    print("   • Use during off-peak hours (US nighttime)")
    
    print("\n2. 🌐 **Use Different Network**")
    print("   • Try from your local machine first")
    print("   • Consider VPN if available")
    print("   • Use different VPS provider")
    
    print("\n3. 📧 **Contact NCBI**")
    print("   • Email: info@ncbi.nlm.nih.gov")
    print("   • Explain academic research use")
    print("   • Request IP whitelist for your VPS")
    
    print("\n4. 🔄 **Alternative Data Sources**")
    print("   • Europe PMC API (https://europepmc.org/RestfulWebService)")
    print("   • CrossRef API for DOI metadata")
    print("   • Manual data import from existing sources")
    
    print("\n5. 🎯 **Optimized Approach**")
    print("   • Run PubMed searches from local machine")
    print("   • Export data and import to VPS")
    print("   • Use VPS only for web application")

def create_retry_script():
    """Create a script that retries with different approaches"""
    
    print("\n📝 Creating retry script...")
    
    script_content = '''#!/usr/bin/env python3
"""
NCBI Retry Script with Multiple Approaches
Tries different methods to access PubMed API
"""

import time
import random
from Bio import Entrez
import os
from dotenv import load_dotenv

load_dotenv()

def retry_with_delays():
    """Retry PubMed access with random delays"""
    
    email = os.getenv('NCBI_EMAIL')
    api_key = os.getenv('NCBI_API_KEY')
    
    Entrez.email = email
    Entrez.tool = "FacultyFinder-Research"
    
    if api_key:
        Entrez.api_key = api_key
    
    max_retries = 5
    base_delay = 10  # Start with 10 seconds
    
    for attempt in range(max_retries):
        try:
            # Random delay between attempts
            delay = base_delay + random.randint(0, 30)
            print(f"Attempt {attempt + 1}/{max_retries} - waiting {delay} seconds...")
            time.sleep(delay)
            
            handle = Entrez.esearch(
                db="pubmed",
                term="Guyatt G[Author]",
                retmax=1,
                retmode="xml"
            )
            
            result = Entrez.read(handle)
            handle.close()
            
            print(f"✅ Success on attempt {attempt + 1}!")
            return True
            
        except Exception as e:
            print(f"❌ Attempt {attempt + 1} failed: {str(e)}")
            base_delay *= 2  # Exponential backoff
    
    print("❌ All retry attempts failed")
    return False

if __name__ == "__main__":
    retry_with_delays()
'''
    
    with open('retry_ncbi_access.py', 'w') as f:
        f.write(script_content)
    
    os.chmod('retry_ncbi_access.py', 0o755)
    print("✅ Created retry_ncbi_access.py")

def main():
    """Main function to diagnose and fix NCBI blocking"""
    
    print("🚨 NCBI Blocking Diagnostic & Fix Tool")
    print("=" * 50)
    
    # Check IP reputation
    check_ip_reputation()
    
    # Test with better headers
    if test_with_better_headers():
        print("\n🎉 Fixed! NCBI access working with improved settings")
        return
    
    # Test direct HTTP
    if test_direct_http_with_headers():
        print("\n🎉 Fixed! NCBI access working with direct HTTP")
        return
    
    # Create retry script
    create_retry_script()
    
    # Suggest alternatives
    suggest_alternatives()
    
    print("\n🔧 Immediate Actions:")
    print("1. Try: python3 retry_ncbi_access.py")
    print("2. Wait 1-2 hours and retry")
    print("3. Test from local machine first")
    print("4. Consider contacting NCBI for IP whitelist")

if __name__ == "__main__":
    main() 