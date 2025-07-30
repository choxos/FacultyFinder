#!/usr/bin/env python3
"""
University Folder Structure Generator
Reads CA_universities.csv and creates folder structure:
province_abbreviation/university_code_website/
"""

import pandas as pd
import os
from pathlib import Path
from collections import defaultdict

# Province name to abbreviation mapping for Canadian provinces/territories
PROVINCE_MAPPING = {
    'Alberta': 'AB',
    'British Columbia': 'BC',
    'Manitoba': 'MB',
    'New Brunswick': 'NB',
    'Newfoundland and Labrador': 'NL',
    'Northwest Territories': 'NT',
    'Nova Scotia': 'NS',
    'Nunavut': 'NU',
    'Ontario': 'ON',
    'Prince Edward Island': 'PE',
    'Quebec': 'QC',
    'Saskatchewan': 'SK',
    'Yukon': 'YT'
}

def read_universities_csv(filename):
    """Read and parse the universities CSV file."""
    try:
        df = pd.read_csv(filename)
        print(f"📊 Successfully loaded {len(df)} universities from {filename}")
        return df
    except FileNotFoundError:
        print(f"❌ Error: File '{filename}' not found.")
        print("Please check the file path and ensure the CSV file exists.")
        return None
    except Exception as e:
        print(f"❌ Error reading CSV file: {e}")
        return None

def get_province_abbreviation(province_name):
    """Convert province name to abbreviation."""
    if pd.isna(province_name):
        return None
    
    province_clean = str(province_name).strip()
    return PROVINCE_MAPPING.get(province_clean)

def create_folder_structure(df, base_path='.', create_folders=True):
    """
    Create folder structure from university data.
    
    Args:
        df: DataFrame with university data
        base_path: Base directory to create folders in
        create_folders: If True, actually create the folders; if False, just show structure
    """
    folder_structure = defaultdict(list)
    unknown_provinces = set()
    
    for index, row in df.iterrows():
        # Get province abbreviation
        province_abbrev = get_province_abbreviation(row['province_state'])
        
        if not province_abbrev:
            unknown_provinces.add(str(row['province_state']))
            print(f"⚠️  Unknown province: {row['province_state']} for {row['university_name']}")
            continue
        
        # Create university folder name: university_code_website
        university_folder = f"{row['university_code']}_{row['website']}"
        
        folder_structure[province_abbrev].append({
            'folder': university_folder,
            'name': row['university_name'],
            'city': row['city']
        })
    
    # Display folder structure
    print('\n📁 FOLDER STRUCTURE:')
    print('=' * 60)
    
    total_universities = 0
    for province in sorted(folder_structure.keys()):
        universities = folder_structure[province]
        total_universities += len(universities)
        
        print(f"\n📁 {province}/ ({len(universities)} universities)")
        
        for uni in sorted(universities, key=lambda x: x['folder']):
            print(f"  📁 {uni['folder']}/")
            print(f"     └── {uni['name']} ({uni['city']})")
    
    if create_folders:
        # Create actual folders
        print(f"\n🏗️  Creating folders in: {os.path.abspath(base_path)}")
        
        for province, universities in folder_structure.items():
            # Create province folder
            province_path = Path(base_path) / province
            province_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created: {province}/")
            
            # Create university folders
            for uni in universities:
                uni_path = province_path / uni['folder']
                uni_path.mkdir(parents=True, exist_ok=True)
                print(f"✅ Created: {province}/{uni['folder']}/")
    
    # Print summary
    print('\n📈 SUMMARY:')
    print('=' * 60)
    print(f"Total provinces: {len(folder_structure)}")
    print(f"Total universities: {total_universities}")
    
    if unknown_provinces:
        print(f"Unknown provinces found: {len(unknown_provinces)}")
        for province in sorted(unknown_provinces):
            print(f"  - {province}")
    
    print("\nUniversities by province:")
    for province in sorted(folder_structure.keys()):
        print(f"  {province}: {len(folder_structure[province])} universities")
    
    return folder_structure

def generate_batch_script(folder_structure, filename='create_folders.bat', parent_folder='.'):
    """Generate Windows batch script to create folders."""
    script_content = '@echo off\n'
    script_content += 'echo Creating university folder structure...\n'
    
    # Change to parent directory if specified
    if parent_folder != '.':
        script_content += f'cd /d "{os.path.abspath(parent_folder)}"\n'
    script_content += '\n'
    
    for province in sorted(folder_structure.keys()):
        script_content += f'REM Create {province} province folder\n'
        script_content += f'mkdir "{province}" 2>nul\n'
        
        for uni in folder_structure[province]:
            script_content += f'mkdir "{province}\\{uni["folder"]}" 2>nul\n'
        script_content += '\n'
    
    script_content += 'echo Folder structure created successfully!\npause\n'
    
    with open(filename, 'w') as f:
        f.write(script_content)
    
    print(f"💾 Windows batch script saved as: {filename}")

def generate_shell_script(folder_structure, filename='create_folders.sh', parent_folder='.'):
    """Generate Unix/Linux shell script to create folders."""
    script_content = '#!/bin/bash\n'
    script_content += 'echo "Creating university folder structure..."\n'
    
    # Change to parent directory if specified
    if parent_folder != '.':
        script_content += f'cd "{os.path.abspath(parent_folder)}"\n'
    script_content += '\n'
    
    for province in sorted(folder_structure.keys()):
        script_content += f'# Create {province} province folder\n'
        script_content += f'mkdir -p "{province}"\n'
        
        for uni in folder_structure[province]:
            script_content += f'mkdir -p "{province}/{uni["folder"]}"\n'
        script_content += '\n'
    
    script_content += 'echo "Folder structure created successfully!"\n'
    
    with open(filename, 'w') as f:
        f.write(script_content)
    
    # Make script executable
    os.chmod(filename, 0o755)
    print(f"💾 Shell script saved as: {filename}")

def main():
    """Main function to orchestrate the folder creation process."""
    print("🏫 University Folder Structure Generator")
    print("=" * 60)
    
    # Get CSV file location
    csv_file = input("Enter CSV file path (or press Enter for 'CA_universities.csv'): ").strip()
    if not csv_file:
        csv_file = 'CA_universities.csv'
    
    # Read CSV file
    df = read_universities_csv(csv_file)
    if df is None:
        return
    
    # Show first few rows
    print(f"\n📋 Sample data (first 3 rows):")
    print(df[['university_code', 'university_name', 'province_state', 'website']].head(3).to_string(index=False))
    
    # Get parent folder location
    parent_folder = input("\nEnter parent folder path (or press Enter for current directory): ").strip()
    if not parent_folder:
        parent_folder = '.'
    
    # Verify parent folder exists or can be created
    try:
        Path(parent_folder).mkdir(parents=True, exist_ok=True)
        print(f"📂 Using parent directory: {os.path.abspath(parent_folder)}")
    except Exception as e:
        print(f"❌ Error with parent directory: {e}")
        return
    
    # Ask user if they want to actually create folders or just preview
    print(f"\nOptions:")
    print("1. Preview folder structure only")
    print("2. Create actual folders")
    print("3. Generate batch/shell scripts")
    
    try:
        choice = input("\nEnter your choice (1-3): ").strip()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled.")
        return
    
    if choice == '1':
        # Preview only
        create_folder_structure(df, parent_folder, create_folders=False)
    
    elif choice == '2':
        # Create actual folders
        folder_structure = create_folder_structure(df, parent_folder, create_folders=True)
        print(f"\n✅ Folders created successfully in: {os.path.abspath(parent_folder)}")
    
    elif choice == '3':
        # Generate scripts
        folder_structure = create_folder_structure(df, parent_folder, create_folders=False)
        
        # Ask for script location
        script_location = input(f"\nEnter location to save scripts (or press Enter for current directory): ").strip()
        if not script_location:
            script_location = '.'
        
        batch_file = os.path.join(script_location, 'create_folders.bat')
        shell_file = os.path.join(script_location, 'create_folders.sh')
        
        generate_batch_script(folder_structure, batch_file, parent_folder)
        generate_shell_script(folder_structure, shell_file, parent_folder)
        print(f"\n✅ Scripts generated in: {os.path.abspath(script_location)}")
    
    else:
        print("Invalid choice. Please run the script again.")

if __name__ == "__main__":
    main()
