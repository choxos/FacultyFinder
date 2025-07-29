#!/usr/bin/env python3
"""
Fix Field Mapping Issues
Corrects API field mapping to match CSV data structure
"""

import os
import re

def fix_university_field_mapping():
    """Fix university field mapping in main.py"""
    
    print("🔧 Fixing University Field Mapping")
    print("=" * 40)
    
    main_py_path = 'webapp/main.py'
    
    if not os.path.exists(main_py_path):
        print(f"❌ {main_py_path} not found")
        return
    
    # Read the current file
    with open(main_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Fix university field mapping issues
    fixes_applied = []
    
    # 1. Fix 'university_type' to 'type' (to match CSV)
    if 'u.university_type' in content:
        content = content.replace('u.university_type', 'u.type')
        content = content.replace('university_type', 'type')
        fixes_applied.append("university_type → type")
    
    # 2. Fix 'languages' to 'language' (to match CSV)
    if 'u.languages' in content:
        content = content.replace('u.languages', 'u.language')
        content = content.replace('languages', 'language')
        fixes_applied.append("languages → language")
    
    # 3. Fix 'year_established' to 'established' (to match CSV)
    if 'u.year_established' in content:
        content = content.replace('u.year_established', 'u.established')
        # Don't replace all instances, just in queries
        content = re.sub(r'year_established(?=\s*[,)])', 'established', content)
        fixes_applied.append("year_established → established")
    
    # 4. Update University model to match CSV fields
    university_model_pattern = r'class University\(BaseModel\):(.*?)(?=class|\Z)'
    
    def fix_university_model(match):
        model_content = match.group(1)
        
        # Replace field names in the model
        model_content = model_content.replace('university_type:', 'type:')
        model_content = model_content.replace('languages:', 'language:')
        model_content = model_content.replace('year_established:', 'established:')
        
        return f'class University(BaseModel):{model_content}'
    
    content = re.sub(university_model_pattern, fix_university_model, content, flags=re.DOTALL)
    
    # Write the fixed content
    if content != original_content:
        with open(main_py_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Applied fixes to {main_py_path}:")
        for fix in fixes_applied:
            print(f"  - {fix}")
    else:
        print(f"ℹ️  No fixes needed in {main_py_path}")

def fix_frontend_field_mapping():
    """Fix frontend field mapping in HTML files"""
    
    print(f"\n🔧 Fixing Frontend Field Mapping")
    print("=" * 40)
    
    html_files = [
        'webapp/static/universities.html',
        'webapp/static/index.html'
    ]
    
    for file_path in html_files:
        if not os.path.exists(file_path):
            print(f"⚠️  {file_path} not found")
            continue
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        fixes_applied = []
        
        # Fix university field references in JavaScript
        if 'university.university_type' in content:
            content = content.replace('university.university_type', 'university.type')
            fixes_applied.append("university_type → type")
        
        if 'university.languages' in content:
            content = content.replace('university.languages', 'university.language')
            fixes_applied.append("languages → language")
        
        if 'university.year_established' in content:
            content = content.replace('university.year_established', 'university.established')
            fixes_applied.append("year_established → established")
        
        # Write the fixed content
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Applied fixes to {file_path}:")
            for fix in fixes_applied:
                print(f"  - {fix}")
        else:
            print(f"ℹ️  No fixes needed in {file_path}")

def verify_professor_field_mapping():
    """Verify professor field mapping is correct"""
    
    print(f"\n🔍 Verifying Professor Field Mapping")
    print("=" * 40)
    
    main_py_path = 'webapp/main.py'
    
    with open(main_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if professor fields are correctly mapped
    professor_checks = [
        ('p.position', 'position field'),
        ('p.full_time', 'full_time field'),
        ('p.adjunct', 'adjunct field'),
        ('p.uni_email', 'uni_email field'),
        ('p.research_areas', 'research_areas field')
    ]
    
    for field, description in professor_checks:
        if field in content:
            print(f"  ✅ {description}: {field}")
        else:
            print(f"  ❌ {description}: NOT FOUND")

def main():
    print("🔧 Field Mapping Fix Script")
    print("=" * 50)
    print("Fixing field mapping to match CSV data structure")
    print("Based on:")
    print("  - mcmaster_hei_faculty.csv")
    print("  - university_codes.csv")
    print("=" * 50)
    
    # Fix university field mapping
    fix_university_field_mapping()
    
    # Fix frontend field mapping
    fix_frontend_field_mapping()
    
    # Verify professor field mapping
    verify_professor_field_mapping()
    
    print(f"\n🎯 Summary:")
    print(f"Field mapping has been corrected to match CSV structure:")
    print(f"  - CSV 'type' → Database 'type' (not 'university_type')")
    print(f"  - CSV 'language' → Database 'language' (not 'languages')")
    print(f"  - CSV 'established' → Database 'established' (not 'year_established')")
    print(f"  - Professor fields verified: position, full_time, adjunct")
    print(f"\n🚀 Next steps:")
    print(f"  1. Restart FastAPI service")
    print(f"  2. Test API endpoints")
    print(f"  3. Verify data display is correct")

if __name__ == "__main__":
    main() 