#!/usr/bin/env python3
"""
Publications System Test Script

Tests the publications database integration and API endpoints
to verify everything is working correctly.

Usage:
    python3 test_publications_system.py [options]
"""

import os
import sys
import requests
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
import json
from pathlib import Path


def test_database_connection():
    """Test PostgreSQL database connection and schema"""
    print("🔍 Testing database connection...")
    
    try:
        load_dotenv()
        
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', '5432')),
            'database': os.getenv('DB_NAME', 'facultyfinder'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD')
        }
        
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        print("✅ Database connection successful")
        
        # Test tables exist
        print("📊 Checking publications tables...")
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('publications', 'faculty_publications', 'author_profiles', 'publication_metrics_cache')
            ORDER BY table_name
        """)
        
        tables = [row['table_name'] for row in cursor.fetchall()]
        required_tables = ['author_profiles', 'faculty_publications', 'publication_metrics_cache', 'publications']
        
        for table in required_tables:
            if table in tables:
                print(f"   ✅ {table}")
            else:
                print(f"   ❌ {table} - MISSING")
                return False
        
        # Test sample data
        print("\n📈 Checking data counts...")
        
        cursor.execute("SELECT COUNT(*) as count FROM publications")
        pub_count = cursor.fetchone()['count']
        print(f"   Publications: {pub_count}")
        
        cursor.execute("SELECT COUNT(*) as count FROM author_profiles")
        author_count = cursor.fetchone()['count']
        print(f"   Author profiles: {author_count}")
        
        cursor.execute("SELECT COUNT(*) as count FROM faculty_publications")
        fp_count = cursor.fetchone()['count']
        print(f"   Faculty-publication links: {fp_count}")
        
        # Test functions
        print("\n🔧 Testing database functions...")
        try:
            cursor.execute("SELECT refresh_faculty_metrics('TEST-ID')")
            print("   ✅ refresh_faculty_metrics() function works")
        except Exception as e:
            print(f"   ❌ refresh_faculty_metrics() function failed: {str(e)}")
        
        # Test views
        print("\n👁️  Testing database views...")
        try:
            cursor.execute("SELECT COUNT(*) FROM faculty_publication_summary LIMIT 1")
            print("   ✅ faculty_publication_summary view works")
        except Exception as e:
            print(f"   ❌ faculty_publication_summary view failed: {str(e)}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {str(e)}")
        return False


def test_api_endpoints(base_url="http://localhost:8000"):
    """Test FastAPI endpoints"""
    print(f"\n🌐 Testing API endpoints at {base_url}...")
    
    try:
        # Test basic connectivity
        response = requests.get(f"{base_url}/api/v1/stats", timeout=10)
        if response.status_code == 200:
            print("   ✅ Basic API connectivity")
        else:
            print(f"   ⚠️  API connectivity issue: {response.status_code}")
    
    except requests.exceptions.RequestException as e:
        print(f"   ❌ API connectivity failed: {str(e)}")
        print(f"   💡 Make sure FastAPI server is running at {base_url}")
        return False
    
    # Test publication endpoints
    endpoints_to_test = [
        ("/api/v1/publications/stats", "Publication statistics"),
        ("/api/v1/publications/search?q=health", "Publication search"),
    ]
    
    for endpoint, description in endpoints_to_test:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            if response.status_code == 200:
                print(f"   ✅ {description}")
                
                # Show sample data
                if "stats" in endpoint:
                    data = response.json()
                    if 'total_publications' in data:
                        print(f"      📊 Total publications: {data['total_publications']}")
                    
            else:
                print(f"   ⚠️  {description}: HTTP {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ {description}: {str(e)}")
    
    # Test faculty endpoint (if we have sample data)
    print("\n👥 Testing faculty endpoints...")
    try:
        # Try to get a sample faculty ID
        load_dotenv()
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', '5432')),
            'database': os.getenv('DB_NAME', 'facultyfinder'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD')
        }
        
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor.execute("SELECT faculty_id FROM author_profiles LIMIT 1")
        result = cursor.fetchone()
        
        if result:
            faculty_id = result['faculty_id']
            
            response = requests.get(f"{base_url}/api/v1/faculty/{faculty_id}/publications", timeout=10)
            if response.status_code == 200:
                print(f"   ✅ Faculty publications endpoint")
                data = response.json()
                if 'publications' in data:
                    print(f"      📚 Found {len(data['publications'])} publications for {faculty_id}")
            else:
                print(f"   ⚠️  Faculty publications endpoint: HTTP {response.status_code}")
        else:
            print("   ⚠️  No faculty profiles found to test with")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"   ⚠️  Faculty endpoint test: {str(e)}")
    
    return True


def test_data_integrity():
    """Test data integrity and relationships"""
    print("\n🔍 Testing data integrity...")
    
    try:
        load_dotenv()
        
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', '5432')),
            'database': os.getenv('DB_NAME', 'facultyfinder'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD')
        }
        
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Test faculty-publication relationships
        cursor.execute("""
            SELECT COUNT(*) as orphaned_links
            FROM faculty_publications fp
            LEFT JOIN publications p ON fp.publication_id = p.publication_id 
                                     AND fp.source_system = p.source_system
            WHERE p.id IS NULL
        """)
        
        orphaned = cursor.fetchone()['orphaned_links']
        if orphaned == 0:
            print("   ✅ All faculty-publication links have valid publications")
        else:
            print(f"   ⚠️  Found {orphaned} orphaned faculty-publication links")
        
        # Test author profiles vs faculty data
        cursor.execute("""
            SELECT COUNT(*) as profiles_with_pubs
            FROM author_profiles ap
            JOIN faculty_publications fp ON ap.faculty_id = fp.faculty_id
        """)
        
        profiles_with_pubs = cursor.fetchone()['profiles_with_pubs']
        
        cursor.execute("SELECT COUNT(*) as total_profiles FROM author_profiles")
        total_profiles = cursor.fetchone()['total_profiles']
        
        if total_profiles > 0:
            coverage = (profiles_with_pubs / total_profiles) * 100
            print(f"   📊 {coverage:.1f}% of author profiles have publications")
        
        # Test JSON data integrity
        cursor.execute("""
            SELECT COUNT(*) as invalid_json
            FROM publications 
            WHERE raw_data IS NULL OR raw_data = 'null'::jsonb
        """)
        
        invalid_json = cursor.fetchone()['invalid_json']
        if invalid_json == 0:
            print("   ✅ All publications have valid JSON data")
        else:
            print(f"   ⚠️  Found {invalid_json} publications with invalid JSON")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Data integrity test failed: {str(e)}")
        return False


def test_sample_queries():
    """Test sample analytical queries"""
    print("\n📊 Testing sample analytical queries...")
    
    try:
        load_dotenv()
        
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', '5432')),
            'database': os.getenv('DB_NAME', 'facultyfinder'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD')
        }
        
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Top cited publications
        cursor.execute("""
            SELECT title, citation_count, source_system
            FROM publications
            WHERE citation_count > 0
            ORDER BY citation_count DESC
            LIMIT 3
        """)
        
        top_cited = cursor.fetchall()
        if top_cited:
            print("   📈 Top cited publications:")
            for pub in top_cited:
                title = pub['title'][:50] + "..." if len(pub['title']) > 50 else pub['title']
                print(f"      {pub['citation_count']} citations: {title}")
        
        # Faculty with highest H-index
        cursor.execute("""
            SELECT display_name, h_index, works_count
            FROM author_profiles
            WHERE h_index > 0
            ORDER BY h_index DESC
            LIMIT 3
        """)
        
        top_faculty = cursor.fetchall()
        if top_faculty:
            print("   🏆 Faculty with highest H-index:")
            for faculty in top_faculty:
                print(f"      {faculty['display_name']}: H-index {faculty['h_index']} ({faculty['works_count']} works)")
        
        # Publication trends
        cursor.execute("""
            SELECT publication_year, COUNT(*) as count
            FROM publications
            WHERE publication_year >= 2020
            GROUP BY publication_year
            ORDER BY publication_year DESC
        """)
        
        trends = cursor.fetchall()
        if trends:
            print("   📅 Recent publication trends:")
            for trend in trends:
                print(f"      {trend['publication_year']}: {trend['count']} publications")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Sample queries test failed: {str(e)}")
        return False


def main():
    print("🧪 Publications System Test Suite")
    print("=" * 50)
    
    all_tests_passed = True
    
    # Test 1: Database connection and schema
    if not test_database_connection():
        all_tests_passed = False
    
    # Test 2: API endpoints
    if not test_api_endpoints():
        all_tests_passed = False
    
    # Test 3: Data integrity
    if not test_data_integrity():
        all_tests_passed = False
    
    # Test 4: Sample queries
    if not test_sample_queries():
        all_tests_passed = False
    
    print("\n" + "=" * 50)
    if all_tests_passed:
        print("✅ All tests passed! Publications system is working correctly.")
        print("\n🎯 Next steps:")
        print("   1. Update your FastAPI application with publication endpoints")
        print("   2. Update frontend templates to display publication data")
        print("   3. Deploy to production")
    else:
        print("❌ Some tests failed. Please check the issues above.")
        print("\n🔧 Troubleshooting:")
        print("   1. Ensure database schema is deployed: ./deploy_publications_schema.sh")
        print("   2. Import data: python3 publications_importer.py")
        print("   3. Restart FastAPI server")
        sys.exit(1)


if __name__ == "__main__":
    main() 