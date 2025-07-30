#!/usr/bin/env python3
"""
Generate EDirect (esearch/efetch) scripts for faculty publication searches
Uses the user's preferred bash approach with esearch and efetch
"""

import os
import sys
from datetime import datetime

class EDirectScriptGenerator:
    """Generate bash scripts using NCBI EDirect tools"""
    
    def __init__(self):
        self.faculty_list = [
            "Gordon Guyatt",
            "Salim Yusuf", 
            "Hertzel Gerstein",
            "Mohit Bhandari",
            "Mark Crowther",
            "Deborah Cook",
            "Andrew Mente",
            "Bram Rochwerg",
            "Holger Schünemann",
            "Jan Brozek"
        ]
    
    def generate_individual_scripts(self, output_dir="edirect_scripts"):
        """Generate individual bash scripts for each faculty member"""
        
        os.makedirs(output_dir, exist_ok=True)
        
        script_files = []
        
        for faculty_name in self.faculty_list:
            # Clean name for filename
            clean_name = faculty_name.replace(" ", "_").replace("ü", "u").replace("ö", "o")
            script_file = f"{output_dir}/search_{clean_name}.sh"
            
            # Create search query
            query = f'"{faculty_name}"[Author]'
            output_file = f"pubmed_data/{clean_name}_publications.txt"
            
            script_content = f'''#!/bin/bash
# EDirect search script for {faculty_name}
# Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

echo "🔍 Searching PubMed for {faculty_name}..."

# Create output directory
mkdir -p pubmed_data

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
        
        return script_files
    
    def generate_batch_script(self, output_dir="edirect_scripts"):
        """Generate a single script that searches all faculty"""
        
        os.makedirs(output_dir, exist_ok=True)
        
        batch_script = f"{output_dir}/search_all_faculty.sh"
        
        script_content = f'''#!/bin/bash
# Batch EDirect search script for all faculty
# Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

echo "🚀 Starting batch PubMed search for {len(self.faculty_list)} faculty members..."
echo "================================================"

# Create output directory
mkdir -p pubmed_data

# Track statistics
total_faculty={len(self.faculty_list)}
completed=0
failed=0

'''
        
        for i, faculty_name in enumerate(self.faculty_list, 1):
            clean_name = faculty_name.replace(" ", "_").replace("ü", "u").replace("ö", "o")
            query = f'"{faculty_name}"[Author]'
            output_file = f"pubmed_data/{clean_name}_publications.txt"
            
            script_content += f'''
# [{i}/{len(self.faculty_list)}] {faculty_name}
echo "🔍 [{i}/{len(self.faculty_list)}] Searching for {faculty_name}..."

esearch -db pubmed -query '{query}' | efetch -format medline > {output_file}

if [ -s {output_file} ]; then
    pub_count=$(grep -c "^PMID-" {output_file})
    echo "   ✅ Found $pub_count publications"
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
echo "🎉 Batch search completed!"
echo "================================================"
echo "✅ Successful searches: $completed"
echo "❌ Failed searches: $failed"
echo "📁 Output directory: pubmed_data/"

# Count total publications
total_pubs=$(find pubmed_data/ -name "*.txt" -exec grep -c "^PMID-" {{}} + 2>/dev/null | awk '{{sum+=$1}} END {{print sum}}')
echo "📚 Total publications found: $total_pubs"

echo ""
echo "📋 Next steps:"
echo "1. Parse data: python3 parse_medline_files.py pubmed_data/"
echo "2. Import to VPS: python3 import_pubmed_data.py parsed_publications.json"
'''
        
        # Write batch script
        with open(batch_script, 'w') as f:
            f.write(script_content)
        
        # Make executable
        os.chmod(batch_script, 0o755)
        
        print(f"✅ Created batch script: {batch_script}")
        return batch_script
    
    def generate_custom_search_script(self, output_dir="edirect_scripts"):
        """Generate a script for custom searches"""
        
        os.makedirs(output_dir, exist_ok=True)
        
        custom_script = f"{output_dir}/custom_search.sh"
        
        script_content = '''#!/bin/bash
# Custom EDirect search script
# Usage: ./custom_search.sh "Author Name" [output_filename]

if [ -z "$1" ]; then
    echo "Usage: $0 \"Author Name\" [output_filename]"
    echo "Example: $0 \"Gordon Guyatt\" gordon_guyatt.txt"
    exit 1
fi

AUTHOR_NAME="$1"
OUTPUT_FILE="${2:-$(echo "$1" | tr ' ' '_' | tr '[:upper:]' '[:lower:]').txt}"

echo "🔍 Searching PubMed for: $AUTHOR_NAME"
echo "📄 Output file: pubmed_data/$OUTPUT_FILE"

# Create output directory
mkdir -p pubmed_data

# Search and fetch
esearch -db pubmed -query "\"$AUTHOR_NAME\"[Author]" | efetch -format medline > "pubmed_data/$OUTPUT_FILE"

if [ -s "pubmed_data/$OUTPUT_FILE" ]; then
    pub_count=$(grep -c "^PMID-" "pubmed_data/$OUTPUT_FILE")
    echo "✅ Search completed: $pub_count publications found"
    echo "📁 File: pubmed_data/$OUTPUT_FILE"
else
    echo "❌ No results found or search failed"
fi
'''
        
        # Write custom script
        with open(custom_script, 'w') as f:
            f.write(script_content)
        
        # Make executable
        os.chmod(custom_script, 0o755)
        
        print(f"✅ Created custom search script: {custom_script}")
        return custom_script
    
    def show_usage_instructions(self):
        """Show usage instructions for generated scripts"""
        
        print(f"\n📋 EDirect Scripts Generated!")
        print("=" * 50)
        
        print("\n🔧 Prerequisites:")
        print("   • Install EDirect tools: https://www.ncbi.nlm.nih.gov/books/NBK179288/")
        print("   • Or use conda: conda install -c bioconda entrez-direct")
        
        print("\n🚀 Usage Options:")
        print("   1. Batch search all faculty:")
        print("      ./edirect_scripts/search_all_faculty.sh")
        
        print("\n   2. Search individual faculty:")
        print("      ./edirect_scripts/search_Gordon_Guyatt.sh")
        print("      ./edirect_scripts/search_Salim_Yusuf.sh")
        
        print("\n   3. Custom search:")
        print("      ./edirect_scripts/custom_search.sh \"Faculty Name\"")
        
        print("\n📄 Output:")
        print("   • Files saved to: pubmed_data/")
        print("   • Format: Medline text format")
        print("   • One file per faculty member")
        
        print("\n🔄 Next Steps:")
        print("   1. Run the search scripts")
        print("   2. Parse results: python3 parse_medline_files.py")
        print("   3. Import to VPS: python3 import_pubmed_data.py")

def main():
    """Main function to generate EDirect scripts"""
    
    print("📜 EDirect Script Generator")
    print("=" * 40)
    print("Generates bash scripts using esearch/efetch commands")
    print("(Your preferred method that avoids SSL issues)\n")
    
    generator = EDirectScriptGenerator()
    
    # Generate all script types
    individual_scripts = generator.generate_individual_scripts()
    batch_script = generator.generate_batch_script()
    custom_script = generator.generate_custom_search_script()
    
    print(f"\n✅ Generated {len(individual_scripts)} individual scripts")
    print(f"✅ Generated 1 batch script")
    print(f"✅ Generated 1 custom search script")
    
    # Show usage instructions
    generator.show_usage_instructions()

if __name__ == "__main__":
    main() 