#!/usr/bin/env python3
"""
Research Areas Generation Script
Run this to generate research areas for all faculty members based on their publication keywords
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from research_areas_generator import ResearchAreasGenerator
import logging

def main():
    """Main function to run research areas generation"""
    print("🔬 FacultyFinder Research Areas Generator")
    print("=" * 50)
    print()
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Initialize generator
        generator = ResearchAreasGenerator()
        
        print("🚀 Starting research areas generation for all faculty members...")
        print("   This will analyze publication keywords and extract top 5 research areas")
        print("   for each faculty member based on frequency analysis.")
        print()
        
        # Run generation
        stats = generator.update_all_professors_research_areas()
        
        print()
        print("✅ Research Areas Generation Complete!")
        print("=" * 50)
        print(f"📊 Results Summary:")
        print(f"   ✅ Successfully updated: {stats['updated']} professors")
        print(f"   ❌ Failed to update: {stats['failed']} professors")
        print(f"   ⚠️  No publication data: {stats['no_data']} professors")
        print()
        
        total_processed = sum(stats.values())
        if total_processed > 0:
            success_rate = (stats['updated'] / total_processed) * 100
            print(f"📈 Success Rate: {success_rate:.1f}%")
        
        print()
        print("🎯 Research areas are now available in:")
        print("   • Faculty profiles (/professor/<id>)")
        print("   • Faculty search and listings (/faculties)")
        print("   • Database column: professors.research_areas")
        print()
        print("💡 To regenerate for specific professors, use:")
        print("   python3 -c \"from research_areas_generator import generate_research_areas_for_professor; generate_research_areas_for_professor(PROFESSOR_ID)\"")
        
    except Exception as e:
        print(f"❌ Error during research areas generation: {e}")
        print("   Please check the database connection and try again.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 