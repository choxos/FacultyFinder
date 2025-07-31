#!/usr/bin/env python3
"""
Test OpenAlex & OpenCitations Systems

This script tests both the OpenAlex faculty searcher and OpenCitations enhancer
to ensure they work correctly together.

Usage:
    python test_openalex_opencitations.py
"""

import json
import requests
import os
from pathlib import Path

def test_openalex_api():
    """Test basic OpenAlex API connectivity and search"""
    print("🧪 Testing OpenAlex API...")
    
    try:
        # Test basic API connection
        url = "https://api.openalex.org/works"
        params = {
            'search': 'quantum computing',
            'per-page': 1,
            'email': 'test@facultyfinder.org'
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            
            if results:
                print(f"✅ OpenAlex API working - found {len(results)} result(s)")
                
                # Show sample result structure
                sample = results[0]
                print(f"   Sample publication: {sample.get('display_name', 'No title')[:50]}...")
                print(f"   Authors: {len(sample.get('authorships', []))}")
                print(f"   Citations: {sample.get('cited_by_count', 0)}")
                print(f"   Year: {sample.get('publication_year', 'Unknown')}")
                
                return True
            else:
                print("⚠️  OpenAlex API working but no results found")
                return True
        else:
            print(f"❌ OpenAlex API error: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ OpenAlex API test failed: {str(e)}")
        return False

def test_opencitations_api():
    """Test basic OpenCitations API connectivity"""
    print("\n🧪 Testing OpenCitations API...")
    
    try:
        # Test with a well-known DOI
        test_doi = "10.1371/journal.pone.0266781"
        url = f"https://api.opencitations.net/index/v2/citation-count/doi:{test_doi}"
        
        headers = {
            'User-Agent': 'FacultyFinder-Test/1.0',
            'Accept': 'application/json'
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                count = data[0].get('count', 0)
                print(f"✅ OpenCitations API working - found {count} citations for test DOI")
                return True
            else:
                print("⚠️  OpenCitations API working but no data for test DOI")
                return True
        else:
            print(f"❌ OpenCitations API error: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ OpenCitations API test failed: {str(e)}")
        return False

def test_faculty_csv_loading():
    """Test faculty CSV loading"""
    print("\n🧪 Testing Faculty CSV Loading...")
    
    csv_file = "data/faculties/CA/ON/CA-ON-002_mcmaster.ca/mcmaster_hei_faculty.csv"
    
    if not os.path.exists(csv_file):
        print(f"⚠️  Faculty CSV not found: {csv_file}")
        print("   This is expected if you haven't set up the data structure yet")
        return False
    
    try:
        from openalex_faculty_searcher import OpenAlexFacultySearcher
        
        searcher = OpenAlexFacultySearcher()
        faculty_data = searcher.load_faculty_data(csv_file)
        
        if faculty_data:
            print(f"✅ Faculty CSV loaded successfully - {len(faculty_data)} faculty members")
            
            # Show sample faculty
            sample = faculty_data[0]
            print(f"   Sample faculty: {sample.get('name', 'Unknown')}")
            print(f"   University: {sample.get('university', 'Unknown')}")
            print(f"   Faculty ID: {sample.get('faculty_id', 'Unknown')}")
            
            return True
        else:
            print("❌ Faculty CSV loaded but no data found")
            return False
            
    except Exception as e:
        print(f"❌ Faculty CSV loading test failed: {str(e)}")
        return False

def test_university_folder_mapper():
    """Test university folder mapping system"""
    print("\n🧪 Testing University Folder Mapper...")
    
    try:
        from university_folder_mapper import UniversityFolderMapper
        
        mapper = UniversityFolderMapper()
        
        # Test with McMaster University code
        test_code = "CA-ON-002"
        folder_name = mapper.get_university_folder(test_code)
        
        if folder_name:
            print(f"✅ University folder mapper working")
            print(f"   {test_code} -> {folder_name}")
            return True
        else:
            print(f"⚠️  University folder mapper working but no mapping for {test_code}")
            return True
            
    except Exception as e:
        print(f"❌ University folder mapper test failed: {str(e)}")
        return False

def test_directory_structure():
    """Test that required directories can be created"""
    print("\n🧪 Testing Directory Structure...")
    
    try:
        # Test creating publication directories
        openalex_dir = Path('data/publications/openalex')
        opencitations_dir = Path('data/publications/opencitations')
        faculty_dir = Path('data/faculties/CA/ON/CA-ON-002_mcmaster.ca/publications')
        
        openalex_dir.mkdir(parents=True, exist_ok=True)
        opencitations_dir.mkdir(parents=True, exist_ok=True)
        faculty_dir.mkdir(parents=True, exist_ok=True)
        
        print("✅ Directory structure test passed")
        print(f"   Created: {openalex_dir}")
        print(f"   Created: {opencitations_dir}")
        print(f"   Created: {faculty_dir}")
        
        return True
        
    except Exception as e:
        print(f"❌ Directory structure test failed: {str(e)}")
        return False

def test_json_operations():
    """Test JSON file operations"""
    print("\n🧪 Testing JSON Operations...")
    
    try:
        # Test sample publication data
        sample_publication = {
            "openalex_id": "W1234567890",
            "doi": "10.1000/test.2024.123",
            "title": "Test Publication for FacultyFinder",
            "abstract": "This is a test publication for system verification.",
            "authors": [
                {
                    "display_name": "Test Author",
                    "id": "A1234567890",
                    "institutions": [
                        {
                            "display_name": "Test University",
                            "country_code": "CA"
                        }
                    ]
                }
            ],
            "publication_year": 2024,
            "cited_by_count": 0,
            "source": {
                "display_name": "Test Journal",
                "type": "journal"
            },
            "retrieved_date": "2024-01-15T10:00:00Z",
            "source_database": "OpenAlex"
        }
        
        # Test OpenAlex file
        openalex_dir = Path('data/publications/openalex')
        openalex_dir.mkdir(parents=True, exist_ok=True)
        
        test_file = openalex_dir / "W1234567890.json"
        
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(sample_publication, f, indent=2, ensure_ascii=False)
        
        # Verify we can read it back
        with open(test_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        if loaded_data['openalex_id'] == 'W1234567890':
            print("✅ JSON operations test passed")
            print(f"   Created and verified: {test_file}")
            
            # Clean up test file
            test_file.unlink()
            
            return True
        else:
            print("❌ JSON data verification failed")
            return False
        
    except Exception as e:
        print(f"❌ JSON operations test failed: {str(e)}")
        return False

def test_search_query_construction():
    """Test search query construction logic"""
    print("\n🧪 Testing Search Query Construction...")
    
    try:
        from openalex_faculty_searcher import OpenAlexFacultySearcher
        
        searcher = OpenAlexFacultySearcher()
        
        # Test faculty data
        test_faculty = {
            'name': 'Julia Abelson',
            'first_name': 'Julia',
            'last_name': 'Abelson', 
            'university_name': 'McMaster University',
            'country': 'CA',
            'province': 'ON'
        }
        
        author_query, institution_query = searcher.construct_search_queries(test_faculty)
        
        if author_query and institution_query:
            print("✅ Search query construction test passed")
            print(f"   Author query: {author_query}")
            print(f"   Institution query: {institution_query}")
            return True
        else:
            print("❌ Search query construction failed")
            return False
        
    except Exception as e:
        print(f"❌ Search query construction test failed: {str(e)}")
        return False

def run_all_tests():
    """Run all system tests"""
    print("🧪 FacultyFinder OpenAlex & OpenCitations System Tests")
    print("=" * 60)
    
    tests = [
        ("OpenAlex API", test_openalex_api),
        ("OpenCitations API", test_opencitations_api),
        ("Faculty CSV Loading", test_faculty_csv_loading),
        ("University Folder Mapper", test_university_folder_mapper),
        ("Directory Structure", test_directory_structure),
        ("JSON Operations", test_json_operations),
        ("Search Query Construction", test_search_query_construction),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n🎯 Test Results Summary:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:10} {test_name}")
        if result:
            passed += 1
    
    print(f"\n📊 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! System is ready for use.")
    elif passed >= total * 0.8:
        print("⚠️  Most tests passed. System should work with minor issues.")
    else:
        print("❌ Multiple test failures. Please review system setup.")
    
    print("\n💡 Next Steps:")
    if passed >= total * 0.8:
        print("1. Run a small test search:")
        print("   python openalex_faculty_searcher.py <csv_file> --max 2")
        print("2. If successful, run OpenCitations enhancement:")
        print("   python opencitations_enhancer.py --max 10")
        print("3. Scale up to full production use")
    else:
        print("1. Check API connectivity and credentials")
        print("2. Verify CSV file format and location")
        print("3. Review error messages above for specific issues")
    
    return passed == total

if __name__ == "__main__":
    run_all_tests() 