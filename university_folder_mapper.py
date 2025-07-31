#!/usr/bin/env python3
"""
University Folder Mapper

This utility maps university codes to the correct folder naming convention:
university_code + website (e.g., CA-ON-002_mcmaster.ca)

Used by both PubMed and Scopus faculty search systems.
"""

import csv
from pathlib import Path
from typing import Dict, Optional

class UniversityFolderMapper:
    def __init__(self):
        """Initialize the mapper with university data"""
        self.university_map = {}
        self.load_university_data()
    
    def load_university_data(self):
        """Load university code to website mapping from CSV files"""
        # Load Canadian universities
        ca_universities_file = Path('data/universities/CA/CA_universities.csv')
        if ca_universities_file.exists():
            self._load_universities_csv(ca_universities_file)
        
        # Add other countries as needed
        # us_universities_file = Path('data/universities/US/US_universities.csv')
        # if us_universities_file.exists():
        #     self._load_universities_csv(us_universities_file)
    
    def _load_universities_csv(self, csv_file: Path):
        """Load universities from a CSV file"""
        try:
            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    # Handle potential BOM in column names
                    university_code = (row.get('university_code') or row.get('\ufeffuniversity_code', '')).strip()
                    website = row.get('website', '').strip()
                    
                    if university_code and website:
                        # Create the folder name format: university_code_website
                        folder_name = f"{university_code}_{website}"
                        self.university_map[university_code] = folder_name
                        count += 1
                
                # Only print if in debug mode (when called directly)
                if __name__ == "__main__":
                    print(f"Loaded {count} universities from {csv_file}")
        except Exception as e:
            print(f"Warning: Could not load university data from {csv_file}: {str(e)}")
    
    def get_university_folder(self, university_code: str) -> str:
        """
        Get the correct folder name for a university code
        
        Args:
            university_code: The university code (e.g., 'CA-ON-002')
            
        Returns:
            The folder name (e.g., 'CA-ON-002_mcmaster.ca') or the original code if not found
        """
        return self.university_map.get(university_code, university_code)
    
    def get_faculty_path(self, faculty: Dict, base_path: str = "data/faculties") -> str:
        """
        Get the complete faculty directory path using correct university folder naming
        
        Args:
            faculty: Faculty dictionary containing university_code, country, province
            base_path: Base path for faculty directories
            
        Returns:
            Complete path to faculty directory
        """
        university_code = faculty.get('university_code', 'unknown')
        country = faculty.get('country', university_code[:2] if len(university_code) >= 2 else 'unknown')
        province = faculty.get('province', university_code[3:5] if len(university_code) >= 5 else 'unknown')
        
        # Get the correct university folder name
        university_folder = self.get_university_folder(university_code)
        
        return f"{base_path}/{country}/{province}/{university_folder}"
    
    def get_faculty_publications_path(self, faculty: Dict, base_path: str = "data/faculties") -> str:
        """
        Get the complete faculty publications directory path
        
        Args:
            faculty: Faculty dictionary containing university_code, country, province
            base_path: Base path for faculty directories
            
        Returns:
            Complete path to faculty publications directory
        """
        return f"{self.get_faculty_path(faculty, base_path)}/publications"
    
    def list_available_universities(self) -> Dict[str, str]:
        """Get all available university code to folder mappings"""
        return self.university_map.copy()

# Global instance for easy import
university_mapper = UniversityFolderMapper()

def get_university_folder(university_code: str) -> str:
    """Convenience function to get university folder name"""
    return university_mapper.get_university_folder(university_code)

def get_faculty_publications_path(faculty: Dict, base_path: str = "data/faculties") -> str:
    """Convenience function to get faculty publications path"""
    return university_mapper.get_faculty_publications_path(faculty, base_path)

if __name__ == "__main__":
    # Test the mapper
    mapper = UniversityFolderMapper()
    
    print("University Folder Mapper Test")
    print("=" * 40)
    
    # Test cases
    test_cases = [
        "CA-ON-002",  # McMaster
        "CA-ON-001",  # University of Toronto
        "CA-BC-001"   # UBC
    ]
    
    for code in test_cases:
        folder = mapper.get_university_folder(code)
        print(f"University Code: {code}")
        print(f"Folder Name: {folder}")
        print()
    
    # Test faculty path
    test_faculty = {
        'university_code': 'CA-ON-002',
        'country': 'CA',
        'province': 'ON',
        'faculty_id': 'CA-ON-002-00001'
    }
    
    path = mapper.get_faculty_publications_path(test_faculty)
    print(f"Faculty Publications Path: {path}")
    
    print(f"\nTotal universities mapped: {len(mapper.university_map)}") 