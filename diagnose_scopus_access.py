#!/usr/bin/env python3
"""
Scopus API Access Diagnostics

This script helps diagnose Scopus API access issues and provides solutions.
"""

import requests
import json
from datetime import datetime

def test_scopus_api_access():
    """Comprehensive Scopus API diagnostics"""
    print("🔬 Scopus API Access Diagnostics")
    print("=" * 50)
    
    api_key = "a40794bde2315194803ca0422b5fe851"
    
    # Test different endpoints
    endpoints = [
        {
            'name': 'Scopus Search API',
            'url': 'https://api.elsevier.com/content/search/scopus',
            'params': {'query': 'TITLE("machine learning")', 'count': 1}
        },
        {
            'name': 'Author Search API', 
            'url': 'https://api.elsevier.com/content/search/author',
            'params': {'query': 'AUTHFIRST(john) AND AUTHLAST(smith)', 'count': 1}
        },
        {
            'name': 'Subject Classifications',
            'url': 'https://api.elsevier.com/content/subject/scopus',
            'params': {}
        }
    ]
    
    headers = {
        'X-ELS-APIKey': api_key,
        'Accept': 'application/json',
        'User-Agent': 'FacultyFinder-Diagnostics/1.0'
    }
    
    print(f"🔑 API Key: {api_key[:10]}...{api_key[-10:]}")
    print(f"🌐 Testing from IP: {get_public_ip()}")
    print(f"📅 Test Time: {datetime.now().isoformat()}\n")
    
    for endpoint in endpoints:
        print(f"🔍 Testing: {endpoint['name']}")
        print(f"   URL: {endpoint['url']}")
        
        try:
            response = requests.get(
                endpoint['url'], 
                headers=headers, 
                params=endpoint['params'],
                timeout=30
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ SUCCESS - API accessible")
                data = response.json()
                # Try to extract some basic info
                if 'search-results' in data:
                    total = data.get('search-results', {}).get('opensearch:totalResults', 0)
                    print(f"   📊 Results: {total}")
                elif 'subject-classifications' in data:
                    print(f"   📊 Subject classifications available")
                    
            elif response.status_code == 401:
                print(f"   ❌ AUTHENTICATION ERROR - Invalid API key")
                
            elif response.status_code == 403:
                print(f"   ❌ AUTHORIZATION ERROR - Access denied")
                error_data = response.json() if response.content else {}
                if 'service-error' in error_data:
                    status_text = error_data.get('service-error', {}).get('status', {}).get('statusText', '')
                    print(f"   Details: {status_text}")
                    
                print(f"   Possible causes:")
                print(f"   - IP address not registered with Elsevier")
                print(f"   - API key lacks required permissions")
                print(f"   - Institutional subscription required")
                
            elif response.status_code == 429:
                print(f"   ⏳ RATE LIMIT - Too many requests")
                
            else:
                print(f"   ❓ UNEXPECTED ERROR")
                print(f"   Response: {response.text[:200]}...")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ REQUEST ERROR: {str(e)}")
        except Exception as e:
            print(f"   ❌ UNEXPECTED ERROR: {str(e)}")
        
        print()

def get_public_ip():
    """Get the public IP address"""
    try:
        response = requests.get('https://httpbin.org/ip', timeout=5)
        if response.status_code == 200:
            return response.json().get('origin', 'Unknown')
    except:
        pass
    
    try:
        response = requests.get('https://api.ipify.org?format=json', timeout=5)
        if response.status_code == 200:
            return response.json().get('ip', 'Unknown')
    except:
        pass
    
    return 'Could not determine'

def suggest_solutions():
    """Provide solutions for common Scopus API issues"""
    print("💡 Suggested Solutions")
    print("=" * 50)
    
    print("1. 🏛️  INSTITUTIONAL ACCESS")
    print("   - Scopus often requires institutional subscriptions")
    print("   - Check if your VPS IP is registered with your institution")
    print("   - Contact your institution's library for IP registration")
    print()
    
    print("2. 🔑 API KEY ISSUES")
    print("   - Verify API key is correct and active")
    print("   - Check API key permissions at https://dev.elsevier.com")
    print("   - Request higher access level if needed")
    print()
    
    print("3. 🌐 IP-BASED AUTHENTICATION")
    print("   - Scopus uses IP-based authentication by default")
    print("   - Your current IP may not be registered")
    print("   - Consider using institutional token authentication")
    print()
    
    print("4. 🏠 LOCAL DEVELOPMENT ALTERNATIVE")
    print("   - Run searches from your institutional network")
    print("   - Export data and transfer to VPS")
    print("   - Use the same approach as with PubMed blocking")
    print()
    
    print("5. 📧 CONTACT ELSEVIER SUPPORT")
    print("   - Email: apisupport@elsevier.com")
    print("   - Include your API key and use case")
    print("   - Request IP registration or alternative access")
    print()

def create_local_export_script():
    """Create a script for local Scopus data export"""
    script_content = '''#!/usr/bin/env python3
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
            
        print(f"\\n📦 Export completed in: {os.path.join(original_cwd, args.export_dir)}")
        print(f"💡 Transfer this directory to your VPS at: data/")
        
    finally:
        os.chdir(original_cwd)

if __name__ == "__main__":
    main()
'''
    
    with open('local_scopus_export.py', 'w') as f:
        f.write(script_content)
    
    print("📝 Created: local_scopus_export.py")
    print("   Use this script on a machine with institutional Scopus access")

def main():
    """Run diagnostics and provide solutions"""
    test_scopus_api_access()
    suggest_solutions()
    create_local_export_script()
    
    print("🎯 Next Steps")
    print("=" * 50)
    print("1. Try running from your institutional network")
    print("2. Contact your institution's library about IP registration")
    print("3. Use local_scopus_export.py if you have institutional access")
    print("4. Consider alternative data sources if Scopus access unavailable")
    print()
    
    print("📚 The system is ready to use once API access is resolved!")

if __name__ == "__main__":
    main() 