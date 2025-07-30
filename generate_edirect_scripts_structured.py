#!/usr/bin/env python3
"""
Generate EDirect scripts with proper university folder structure
Saves .txt files to: data/publications/pubmed/[country]/[province]/[university]/
"""

import os
import sys
from datetime import datetime

class StructuredEDirectGenerator:
    """Generate EDirect scripts using proper university folder structure"""
    
    def __init__(self):
        # Faculty with their university information
        self.faculty_data = [
            {
                "name": "Gordon Guyatt",
                "university": "CA-ON-002_mcmaster.ca",
                "country": "CA",
                "province": "ON"
            },
            {
                "name": "Salim Yusuf",
                "university": "CA-ON-002_mcmaster.ca", 
                "country": "CA",
                "province": "ON"
            },
            {
                "name": "Hertzel Gerstein",
                "university": "CA-ON-002_mcmaster.ca",
                "country": "CA", 
                "province": "ON"
            },
            {
                "name": "Mohit Bhandari",
                "university": "CA-ON-002_mcmaster.ca",
                "country": "CA",
                "province": "ON"
            },
            {
                "name": "Mark Crowther", 
                "university": "CA-ON-002_mcmaster.ca",
                "country": "CA",
                "province": "ON"
            },
            {
                "name": "Deborah Cook",
                "university": "CA-ON-002_mcmaster.ca",
                "country": "CA",
                "province": "ON"
            },
            {
                "name": "Andrew Mente",
                "university": "CA-ON-002_mcmaster.ca", 
                "country": "CA",
                "province": "ON"
            },
            {
                "name": "Bram Rochwerg",
                "university": "CA-ON-002_mcmaster.ca",
                "country": "CA",
                "province": "ON"
            },
            {
                "name": "Holger Schünemann",
                "university": "CA-ON-002_mcmaster.ca",
                "country": "CA", 
                "province": "ON"
            },
            {
                "name": "Jan Brozek",
                "university": "CA-ON-002_mcmaster.ca",
                "country": "CA",
                "province": "ON"
            }
        ]
    
    def get_university_path(self, faculty):
        """Get the full path for a faculty member's university"""
        return f"data/publications/pubmed/{faculty['country']}/{faculty['province']}/{faculty['university']}"
    
    def generate_individual_scripts(self, output_dir="edirect_scripts_structured"):
        """Generate individual scripts with proper folder structure"""
        
        os.makedirs(output_dir, exist_ok=True)
        script_files = []
        
        for faculty in self.faculty_data:
            # Clean name for filename
            clean_name = faculty["name"].replace(" ", "_").replace("ü", "u").replace("ö", "o")
            script_file = f"{output_dir}/search_{clean_name}.sh"
            
            # Get university path
            university_path = self.get_university_path(faculty)
            
            # Create search query
            query = f'"{faculty["name"]}"[Author]'
            output_file = f"{university_path}/{clean_name}_publications.txt"
            
            script_content = f'''#!/bin/bash
# EDirect search script for {faculty["name"]}
# University: {faculty["university"]}
# Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

echo "🔍 Searching PubMed for {faculty["name"]}..."
echo "🏫 University: {faculty["university"]}"

# Create university directory structure
mkdir -p {university_path}

# Search and fetch publications
esearch -db pubmed -query '{query}' | efetch -format medline > {output_file}

if [ -s {output_file} ]; then
    echo "✅ Search completed: {output_file}"
    echo "📊 Publications found: $(grep -c "^PMID-" {output_file})"
else
    echo "❌ No results or search failed: {output_file}"
fi
'''
            
            # Write script file
            with open(script_file, 'w') as f:
                f.write(script_content)
            
            # Make executable
            os.chmod(script_file, 0o755)
            
            script_files.append(script_file)
            print(f"✅ Created: {script_file}")
            print(f"   📁 Output: {output_file}")
        
        return script_files
    
    def generate_batch_script(self, output_dir="edirect_scripts_structured"):
        """Generate batch script with proper folder structure"""
        
        os.makedirs(output_dir, exist_ok=True)
        batch_script = f"{output_dir}/search_all_faculty_structured.sh"
        
        script_content = f'''#!/bin/bash
# Structured EDirect search script for all faculty
# Uses proper university folder structure
# Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

echo "🚀 Starting structured PubMed search for {len(self.faculty_data)} faculty members..."
echo "📁 Using folder structure: data/publications/pubmed/[country]/[province]/[university]/"
echo "================================================"

# Track statistics
total_faculty={len(self.faculty_data)}
completed=0
failed=0

'''
        
        for i, faculty in enumerate(self.faculty_data, 1):
            clean_name = faculty["name"].replace(" ", "_").replace("ü", "u").replace("ö", "o")
            university_path = self.get_university_path(faculty)
            query = f'"{faculty["name"]}"[Author]'
            output_file = f"{university_path}/{clean_name}_publications.txt"
            
            script_content += f'''
# [{i}/{len(self.faculty_data)}] {faculty["name"]} - {faculty["university"]}
echo "🔍 [{i}/{len(self.faculty_data)}] Searching for {faculty["name"]}..."
echo "   🏫 University: {faculty["university"]}"

# Create university directory
mkdir -p {university_path}

# Search and fetch
esearch -db pubmed -query '{query}' | efetch -format medline > {output_file}

if [ -s {output_file} ]; then
    pub_count=$(grep -c "^PMID-" {output_file})
    echo "   ✅ Found $pub_count publications"
    echo "   📁 Saved to: {output_file}"
    ((completed++))
else
    echo "   ❌ No results found"
    ((failed++))
fi

# Small delay between searches
sleep 2
'''
        
        script_content += f'''
echo ""
echo "🎉 Structured batch search completed!"
echo "================================================"
echo "✅ Successful searches: $completed"
echo "❌ Failed searches: $failed"
echo "📁 Base directory: data/publications/pubmed/"

# Count total publications by university
echo ""
echo "📊 Publications by University:"
for uni_dir in data/publications/pubmed/*/*/*/; do
    if [ -d "$uni_dir" ]; then
        uni_name=$(basename "$uni_dir")
        txt_count=$(find "$uni_dir" -name "*.txt" | wc -l)
        if [ "$txt_count" -gt 0 ]; then
            total_pubs=$(find "$uni_dir" -name "*.txt" -exec grep -c "^PMID-" {{}} + 2>/dev/null | awk '{{sum+=$1}} END {{print sum}}')
            echo "   $uni_name: $total_pubs publications ($txt_count files)"
        fi
    fi
done

echo ""
echo "📋 Next steps:"
echo "1. Parse data: python3 parse_medline_structured.py data/publications/pubmed/"
echo "2. Import to VPS: python3 import_pubmed_data.py parsed_publications/"
'''
        
        # Write batch script
        with open(batch_script, 'w') as f:
            f.write(script_content)
        
        # Make executable
        os.chmod(batch_script, 0o755)
        
        print(f"✅ Created structured batch script: {batch_script}")
        return batch_script
    
    def generate_custom_search_script(self, output_dir="edirect_scripts_structured"):
        """Generate custom search script with university selection"""
        
        os.makedirs(output_dir, exist_ok=True)
        custom_script = f"{output_dir}/custom_search_structured.sh"
        
        script_content = '''#!/bin/bash
# Custom structured EDirect search script
# Usage: ./custom_search_structured.sh "Author Name" "University Code" [Country] [Province]

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: $0 \"Author Name\" \"University Code\" [Country] [Province]"
    echo "Example: $0 \"Gordon Guyatt\" \"CA-ON-002_mcmaster.ca\" \"CA\" \"ON\""
    echo ""
    echo "Available Universities:"
    echo "  McMaster: CA-ON-002_mcmaster.ca"
    echo "  Toronto: CA-ON-001_utoronto.ca"
    echo "  Waterloo: CA-ON-003_uwaterloo.ca"
    exit 1
fi

AUTHOR_NAME="$1"
UNIVERSITY_CODE="$2"
COUNTRY="${3:-CA}"
PROVINCE="${4:-ON}"

# Clean name for filename
CLEAN_NAME=$(echo "$AUTHOR_NAME" | tr ' ' '_' | tr '[:upper:]' '[:lower:]')
UNIVERSITY_PATH="data/publications/pubmed/$COUNTRY/$PROVINCE/$UNIVERSITY_CODE"
OUTPUT_FILE="$UNIVERSITY_PATH/${CLEAN_NAME}_publications.txt"

echo "🔍 Searching PubMed for: $AUTHOR_NAME"
echo "🏫 University: $UNIVERSITY_CODE"
echo "📁 Output: $OUTPUT_FILE"

# Create university directory
mkdir -p "$UNIVERSITY_PATH"

# Search and fetch
esearch -db pubmed -query "\"$AUTHOR_NAME\"[Author]" | efetch -format medline > "$OUTPUT_FILE"

if [ -s "$OUTPUT_FILE" ]; then
    pub_count=$(grep -c "^PMID-" "$OUTPUT_FILE")
    echo "✅ Search completed: $pub_count publications found"
    echo "📁 File: $OUTPUT_FILE"
else
    echo "❌ No results found or search failed"
fi
'''
        
        # Write custom script
        with open(custom_script, 'w') as f:
            f.write(script_content)
        
        # Make executable
        os.chmod(custom_script, 0o755)
        
        print(f"✅ Created structured custom search script: {custom_script}")
        return custom_script
    
    def show_usage_instructions(self):
        """Show usage instructions for structured scripts"""
        
        print(f"\n📋 Structured EDirect Scripts Generated!")
        print("=" * 60)
        
        print("\n📁 Folder Structure:")
        print("   data/publications/pubmed/")
        print("   ├── CA/")
        print("   │   └── ON/")
        print("   │       └── CA-ON-002_mcmaster.ca/")
        print("   │           ├── Gordon_Guyatt_publications.txt")
        print("   │           ├── Salim_Yusuf_publications.txt")
        print("   │           └── ...")
        
        print("\n🚀 Usage Options:")
        print("   1. Batch search all faculty:")
        print("      ./edirect_scripts_structured/search_all_faculty_structured.sh")
        
        print("\n   2. Search individual faculty:")
        print("      ./edirect_scripts_structured/search_Gordon_Guyatt.sh")
        print("      ./edirect_scripts_structured/search_Salim_Yusuf.sh")
        
        print("\n   3. Custom search:")
        print("      ./edirect_scripts_structured/custom_search_structured.sh \"Faculty Name\" \"CA-ON-002_mcmaster.ca\"")
        
        print("\n📊 Organization Benefits:")
        print("   • Files organized by university")
        print("   • Easy to find specific faculty")
        print("   • Scalable to multiple universities")
        print("   • Compatible with existing structure")
        
        print("\n🔄 Next Steps:")
        print("   1. Run the structured search scripts")
        print("   2. Parse results: python3 parse_medline_structured.py")
        print("   3. Import to VPS: python3 import_pubmed_data.py")

def main():
    """Main function to generate structured EDirect scripts"""
    
    print("📂 Structured EDirect Script Generator")
    print("=" * 50)
    print("Generates scripts using your university folder structure:")
    print("data/publications/pubmed/[country]/[province]/[university]/\n")
    
    generator = StructuredEDirectGenerator()
    
    # Generate all script types
    individual_scripts = generator.generate_individual_scripts()
    batch_script = generator.generate_batch_script()
    custom_script = generator.generate_custom_search_script()
    
    print(f"\n✅ Generated {len(individual_scripts)} individual scripts")
    print(f"✅ Generated 1 structured batch script")
    print(f"✅ Generated 1 structured custom search script")
    
    # Show usage instructions
    generator.show_usage_instructions()

if __name__ == "__main__":
    main() 