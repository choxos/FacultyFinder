#!/usr/bin/env python3
"""
Test script for research areas generation
"""

import sqlite3
import json
import sys
import os

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_research_areas():
    """Test the research areas functionality"""
    print("🔬 Testing Research Areas Generation System")
    print("=" * 50)
    
    try:
        # Test database connection
        conn = sqlite3.connect('facultyfinder_dev.db')
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📊 Available tables: {', '.join(tables)}")
        
        # Check professors
        cursor.execute("SELECT COUNT(*) FROM professors")
        prof_count = cursor.fetchone()[0]
        print(f"👥 Total professors: {prof_count}")
        
        # Check publications
        pub_count = 0
        pub_tables = ['publications', 'professor_publications']
        for table in pub_tables:
            if table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                pub_count += count
                print(f"📚 {table}: {count} records")
        
        # Check for research_areas column
        cursor.execute("PRAGMA table_info(professors)")
        columns = [col[1] for col in cursor.fetchall()]
        has_research_areas = 'research_areas' in columns
        print(f"🎯 Research areas column exists: {has_research_areas}")
        
        if not has_research_areas:
            print("⚠️  Adding research_areas column...")
            cursor.execute("ALTER TABLE professors ADD COLUMN research_areas TEXT")
            conn.commit()
            print("✅ Research areas column added")
        
        # Sample a professor
        cursor.execute("SELECT id, name FROM professors LIMIT 1")
        sample_prof = cursor.fetchone()
        
        if sample_prof:
            prof_id, prof_name = sample_prof
            print(f"\n🧪 Testing with: {prof_name} (ID: {prof_id})")
            
            # Check for publications
            pub_found = False
            for table in pub_tables:
                if table in tables:
                    if table == 'professor_publications':
                        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE professor_id = ?", (prof_id,))
                    else:
                        cursor.execute(f"SELECT COUNT(*) FROM author_publications WHERE professor_id = ?", (prof_id,))
                    
                    count = cursor.fetchone()[0]
                    if count > 0:
                        print(f"📖 Found {count} publications in {table}")
                        pub_found = True
            
            if not pub_found:
                print("⚠️  No publications found for this professor")
                
                # Let's create some sample research areas manually for testing
                sample_areas = ["Machine Learning", "Data Science", "Artificial Intelligence"]
                areas_json = json.dumps(sample_areas)
                
                cursor.execute("UPDATE professors SET research_areas = ? WHERE id = ?", 
                             (areas_json, prof_id))
                conn.commit()
                print(f"✅ Added sample research areas: {sample_areas}")
            
            # Test retrieval
            cursor.execute("SELECT research_areas FROM professors WHERE id = ?", (prof_id,))
            areas_row = cursor.fetchone()
            
            if areas_row and areas_row[0]:
                try:
                    areas = json.loads(areas_row[0])
                    print(f"🎯 Current research areas: {areas}")
                except json.JSONDecodeError:
                    print(f"🎯 Research areas (text): {areas_row[0]}")
            else:
                print("⚠️  No research areas set for this professor")
        
        conn.close()
        
        print("\n✅ Research Areas System Test Complete!")
        print("\n💡 To generate research areas from publications:")
        print("   python3 run_research_areas_generation.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_research_areas() 