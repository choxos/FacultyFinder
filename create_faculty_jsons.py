#!/usr/bin/env python3
"""
Faculty JSON Generator
Converts CSV faculty data to individual JSON files for each faculty member
"""

import csv
import json
import os
import re
from pathlib import Path

def clean_filename(text):
    """Clean text for use in filename"""
    if not text:
        return ""
    # Remove special characters and replace spaces with underscores
    text = re.sub(r'[<>:"/\\|?*]', '', text)
    text = re.sub(r'\s+', '_', text.strip())
    return text

def parse_semicolon_separated(value):
    """Parse semicolon-separated values into a list"""
    if not value or value.strip() == "":
        return []
    # Split by semicolon and clean up each item
    items = [item.strip() for item in value.split(';') if item.strip()]
    return items if len(items) > 1 else [value.strip()] if value.strip() else []

def convert_boolean(value):
    """Convert string boolean values to actual booleans"""
    if isinstance(value, str):
        if value.upper() == 'TRUE':
            return True
        elif value.upper() == 'FALSE':
            return False
    return value

def clean_field_name(field_name):
    """Clean field names by removing BOM and other unwanted characters"""
    # Remove BOM character if present
    if field_name.startswith('\ufeff'):
        field_name = field_name[1:]
    return field_name.strip()

def process_faculty_row(row):
    """Process a single faculty row and convert to structured JSON data"""
    
    # Fields that should be parsed as semicolon-separated lists
    list_fields = [
        'degree', 'all_degrees_and_inst', 'all_degrees_only', 'research_areas',
        'other_depts', 'membership', 'other_email'
    ]
    
    # Fields that should be converted to boolean
    boolean_fields = ['full_time', 'adjunct']
    
    faculty_data = {}
    
    for key, value in row.items():
        # Clean the field name (remove BOM, etc.)
        clean_key = clean_field_name(key)
        
        if clean_key in list_fields:
            faculty_data[clean_key] = parse_semicolon_separated(value)
        elif clean_key in boolean_fields:
            faculty_data[clean_key] = convert_boolean(value)
        else:
            # Keep as string, but clean empty values
            faculty_data[clean_key] = value.strip() if value else ""
    
    return faculty_data

def generate_filename(faculty_data):
    """Generate filename based on faculty_id + names"""
    faculty_id = clean_filename(faculty_data.get('faculty_id', ''))
    first_name = clean_filename(faculty_data.get('first_name', ''))
    middle_names = clean_filename(faculty_data.get('middle_names', ''))
    last_name = clean_filename(faculty_data.get('last_name', ''))
    
    # Build filename components
    filename_parts = []
    if faculty_id:
        filename_parts.append(faculty_id)
    if first_name:
        filename_parts.append(first_name)
    if middle_names:
        filename_parts.append(middle_names)
    if last_name:
        filename_parts.append(last_name)
    
    filename = '_'.join(filename_parts) + '.json'
    return filename

def create_faculty_jsons(csv_file_path, num_faculty=7):
    """Create JSON files for faculty members from CSV data"""
    
    # Determine output directory
    csv_path = Path(csv_file_path)
    csv_filename = csv_path.stem  # Filename without extension
    output_dir = csv_path.parent / f"{csv_filename}_jsons"
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    print(f"📁 Created directory: {output_dir}")
    
    # Read CSV and process faculty
    created_files = []
    with open(csv_file_path, 'r', encoding='utf-8-sig') as csvfile:  # utf-8-sig handles BOM
        reader = csv.DictReader(csvfile)
        
        for i, row in enumerate(reader):
            if i >= num_faculty:  # Stop after processing the specified number
                break
                
            # Process faculty data
            faculty_data = process_faculty_row(row)
            
            # Generate filename
            filename = generate_filename(faculty_data)
            file_path = output_dir / filename
            
            # Write JSON file
            with open(file_path, 'w', encoding='utf-8') as jsonfile:
                json.dump(faculty_data, jsonfile, indent=2, ensure_ascii=False)
            
            created_files.append(filename)
            print(f"✅ Created: {filename}")
    
    print(f"\n🎉 Successfully created {len(created_files)} JSON files in {output_dir}")
    return output_dir, created_files

def main():
    csv_file = "data/faculties/CA/ON/CA-ON-002_mcmaster.ca/HEI/CA-ON-002_mcmaster.ca_HEI.csv"
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        return
    
    print(f"📖 Processing faculty data from: {csv_file}")
    print(f"🎯 Creating JSON files for first 7 faculty members...")
    
    output_dir, created_files = create_faculty_jsons(csv_file, num_faculty=7)
    
    print(f"\n📋 Created files:")
    for filename in created_files:
        print(f"   - {filename}")

if __name__ == "__main__":
    main() 