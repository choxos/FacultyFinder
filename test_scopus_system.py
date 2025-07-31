#!/usr/bin/env python3
"""
Test script for Scopus Faculty Search System

This script tests the Scopus search functionality with a small sample
to verify everything is working correctly before processing large datasets.
"""

import json
import requests
from pathlib import Path

def test_scopus_api():
    """Test basic Scopus API connectivity"""
    print("🔬 Testing Scopus API Connectivity")
    print("=" * 40)
    
    api_key = "a40794bde2315194803ca0422b5fe851"
    base_url = "https://api.elsevier.com/content/search/scopus"
    
    # Test query for a well-known researcher
    test_query = 'AUTHOR-NAME("Smith, J.")'
    
    headers = {
        'X-ELS-APIKey': api_key,
        'Accept': 'application/json'
    }
    
    params = {
        'query': test_query,
        'count': 5,
        'view': 'STANDARD'
    }
    
    try:
        response = requests.get(base_url, headers=headers, params=params, timeout=30)
        
        print(f"📡 Request URL: {response.url}")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            search_results = data.get('search-results', {})
            total_results = search_results.get('opensearch:totalResults', 0)
            entries = search_results.get('entry', [])
            
            print(f"✅ API Connection Successful!")
            print(f"📚 Total Results: {total_results}")
            print(f"📄 Results Retrieved: {len(entries)}")
            
            # Show first result details
            if entries:
                first_result = entries[0]
                print(f"\n📖 Sample Result:")
                print(f"   Title: {first_result.get('dc:title', 'No title')[:100]}...")
                print(f"   Scopus ID: {first_result.get('dc:identifier', 'No ID')}")
                print(f"   Journal: {first_result.get('prism:publicationName', 'No journal')}")
                print(f"   Year: {first_result.get('prism:coverDate', 'No date')[:4]}")
                
                # Test Abstract Retrieval API
                scopus_id = first_result.get('dc:identifier', '').replace('SCOPUS_ID:', '')
                if scopus_id:
                    print(f"\n🔍 Testing Abstract Retrieval for {scopus_id}")
                    abstract_url = f"https://api.elsevier.com/content/abstract/scopus_id/{scopus_id}"
                    abstract_params = {'view': 'FULL'}
                    
                    try:
                        abstract_response = requests.get(abstract_url, headers=headers, params=abstract_params, timeout=30)
                        if abstract_response.status_code == 200:
                            print(f"✅ Abstract Retrieval Successful!")
                            abstract_data = abstract_response.json()
                            # Check if we got enhanced data
                            abstract_resp = abstract_data.get('abstracts-retrieval-response', {})
                            if abstract_resp:
                                print(f"📋 Enhanced abstract data available")
                        else:
                            print(f"⚠️  Abstract Retrieval returned: {abstract_response.status_code}")
                    except Exception as e:
                        print(f"⚠️  Abstract Retrieval error: {str(e)}")
            
            return True
            
        elif response.status_code == 401:
            print(f"❌ Authentication Error: Invalid API Key")
            return False
        elif response.status_code == 429:
            print(f"⏳ Rate Limit Exceeded - API key is valid but quota reached")
            return True
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return False
            
    except requests.exceptions.Timeout:
        print(f"⏱️  Request timed out - check internet connection")
        return False
    except requests.exceptions.ConnectionError:
        print(f"🌐 Connection error - check internet connection")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def test_directory_structure():
    """Test that output directories can be created"""
    print(f"\n📁 Testing Directory Structure")
    print("=" * 40)
    
    # Test publication directory
    pub_dir = Path('data/publications/scopus')
    pub_dir.mkdir(parents=True, exist_ok=True)
    
    if pub_dir.exists():
        print(f"✅ Publications directory created: {pub_dir}")
    else:
        print(f"❌ Failed to create publications directory")
        return False
    
    # Test faculty directory  
    faculty_dir = Path('data/faculties/CA/ON/CA-ON-002_mcmaster.ca/publications')
    faculty_dir.mkdir(parents=True, exist_ok=True)
    
    if faculty_dir.exists():
        print(f"✅ Faculty directory created: {faculty_dir}")
    else:
        print(f"❌ Failed to create faculty directory")
        return False
    
    return True

def test_json_creation():
    """Test JSON file creation"""
    print(f"\n📄 Testing JSON File Creation")
    print("=" * 40)
    
    # Create test publication
    test_publication = {
        "scopus_id": "test123456789",
        "title": "Test Publication",
        "abstract": "This is a test abstract for verification purposes.",
        "authors": [
            {
                "surname": "Test",
                "given_name": "User",
                "affiliations": [{"name": "Test University"}]
            }
        ],
        "journal": {
            "name": "Test Journal",
            "volume": "1",
            "issue": "1"
        },
        "source": "scopus"
    }
    
    # Save test file
    pub_dir = Path('data/publications/scopus')
    test_file = pub_dir / "test123456789.json"
    
    try:
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_publication, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Test JSON file created: {test_file}")
        
        # Verify file content
        with open(test_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        if loaded_data['scopus_id'] == test_publication['scopus_id']:
            print(f"✅ JSON content verified correctly")
        else:
            print(f"❌ JSON content verification failed")
            return False
        
        # Clean up test file
        test_file.unlink()
        print(f"🗑️  Test file cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ JSON creation error: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🧪 Scopus Faculty Search System - Test Suite")
    print("=" * 50)
    
    tests = [
        ("API Connectivity", test_scopus_api),
        ("Directory Structure", test_directory_structure), 
        ("JSON File Creation", test_json_creation)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' failed with exception: {str(e)}")
            results.append((test_name, False))
    
    # Print summary
    print(f"\n🎯 Test Summary")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print(f"\n🎉 All tests passed! Scopus system is ready to use.")
        print(f"\nNext steps:")
        print(f"1. Run a small test: python3 scopus_faculty_searcher.py data/faculties/CA/ON/CA-ON-002_mcmaster.ca/mcmaster_hei_faculty.csv --max 1")
        print(f"2. Check results in data/publications/scopus/")
        print(f"3. Review the SCOPUS_SEARCH_GUIDE.md for detailed usage")
    else:
        print(f"\n⚠️  Some tests failed. Please resolve issues before using the system.")
    
    return passed == total

if __name__ == "__main__":
    main() 