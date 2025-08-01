#!/usr/bin/env python3
"""
Profile Update Utility
Updates faculty JSON files with discovered academic profiles
"""

import json
import os
from pathlib import Path
from typing import Dict, List

def load_discovery_report(report_file: str) -> Dict:
    """Load the discovery report JSON file"""
    try:
        with open(report_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading discovery report: {e}")
        return {}

def update_faculty_json(json_file: Path, profile_updates: Dict[str, str]) -> bool:
    """Update a faculty JSON file with new profile information"""
    try:
        # Load existing data
        with open(json_file, 'r', encoding='utf-8') as f:
            faculty_data = json.load(f)
        
        # Track changes
        changes_made = False
        
        # Update profiles
        for platform, url in profile_updates.items():
            if url and url != faculty_data.get(platform, ''):
                faculty_data[platform] = url
                changes_made = True
                print(f"    ✅ Updated {platform}: {url}")
        
        # Save updated data
        if changes_made:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(faculty_data, f, indent=2, ensure_ascii=False)
            return True
        else:
            print(f"    ℹ️ No changes needed")
            return False
            
    except Exception as e:
        print(f"    ❌ Error updating {json_file}: {e}")
        return False

def interactive_profile_selection(faculty_name: str, platform: str, discovered_profiles: List[Dict]) -> str:
    """Interactive selection of profiles"""
    if not discovered_profiles:
        return ""
    
    print(f"\n🔍 {platform.upper()} profiles for {faculty_name}:")
    print("-" * 60)
    
    for i, profile in enumerate(discovered_profiles, 1):
        confidence_emoji = "🟢" if profile['confidence'] >= 0.8 else "🟡" if profile['confidence'] >= 0.5 else "🔴"
        print(f"{i}. {confidence_emoji} {profile['title']}")
        print(f"   URL: {profile['url']}")
        print(f"   Confidence: {profile['confidence']:.2f}")
        print(f"   Description: {profile['description']}")
        print(f"   Name used: {profile['name_variation']}")
        print()
    
    while True:
        try:
            choice = input(f"Select profile (1-{len(discovered_profiles)}, 0 for none, 's' to skip): ").strip().lower()
            
            if choice == 's':
                return "SKIP"
            elif choice == '0':
                return ""
            else:
                choice_num = int(choice)
                if 1 <= choice_num <= len(discovered_profiles):
                    return discovered_profiles[choice_num - 1]['url']
                else:
                    print(f"❌ Please enter a number between 1 and {len(discovered_profiles)}")
        except ValueError:
            print("❌ Please enter a valid number, 0, or 's'")

def auto_update_high_confidence(json_directory: str, discovery_report: Dict, confidence_threshold: float = 0.8) -> Dict:
    """Automatically update profiles with high confidence matches"""
    json_dir = Path(json_directory)
    stats = {'updated_files': 0, 'updated_profiles': 0, 'total_files': 0}
    
    print(f"🤖 Auto-updating profiles with confidence >= {confidence_threshold}")
    print("=" * 60)
    
    for faculty_result in discovery_report.get('discovery_results', []):
        faculty_id = faculty_result['faculty_id']
        faculty_name = faculty_result['name']
        
        # Find corresponding JSON file
        json_files = list(json_dir.glob(f"{faculty_id}_*.json"))
        if not json_files:
            print(f"⚠️ JSON file not found for {faculty_id}")
            continue
        
        json_file = json_files[0]
        stats['total_files'] += 1
        
        print(f"\n📝 Processing: {faculty_name}")
        
        # Collect high-confidence updates
        profile_updates = {}
        
        for platform, profiles in faculty_result.get('discovered_profiles', {}).items():
            if profiles:
                # Get highest confidence profile
                best_profile = max(profiles, key=lambda x: x['confidence'])
                if best_profile['confidence'] >= confidence_threshold:
                    profile_updates[platform] = best_profile['url']
                    print(f"    🎯 High confidence {platform}: {best_profile['confidence']:.2f}")
        
        # Update the JSON file
        if profile_updates:
            if update_faculty_json(json_file, profile_updates):
                stats['updated_files'] += 1
                stats['updated_profiles'] += len(profile_updates)
        else:
            print(f"    ℹ️ No high-confidence profiles found")
    
    return stats

def interactive_update(json_directory: str, discovery_report: Dict) -> Dict:
    """Interactive profile update process"""
    json_dir = Path(json_directory)
    stats = {'updated_files': 0, 'updated_profiles': 0, 'total_files': 0, 'skipped': 0}
    
    print("🖱️ Interactive Profile Update Mode")
    print("=" * 60)
    print("You'll be shown discovered profiles for each faculty member.")
    print("Select the correct profile or skip if unsure.\n")
    
    for faculty_result in discovery_report.get('discovery_results', []):
        faculty_id = faculty_result['faculty_id']
        faculty_name = faculty_result['name']
        
        # Find corresponding JSON file
        json_files = list(json_dir.glob(f"{faculty_id}_*.json"))
        if not json_files:
            print(f"⚠️ JSON file not found for {faculty_id}")
            continue
        
        json_file = json_files[0]
        stats['total_files'] += 1
        
        print(f"\n{'='*60}")
        print(f"👤 Faculty: {faculty_name} ({faculty_id})")
        print(f"{'='*60}")
        
        # Show existing profiles
        existing_profiles = faculty_result.get('existing_profiles', {})
        has_existing = any(profile for profile in existing_profiles.values())
        
        if has_existing:
            print("\n📋 Existing profiles:")
            for platform, url in existing_profiles.items():
                if url:
                    print(f"  • {platform}: {url}")
        
        # Process each platform
        profile_updates = {}
        discovered_profiles = faculty_result.get('discovered_profiles', {})
        
        for platform in ['gscholar', 'orcid', 'openalex', 'researchgate', 'academicedu']:
            # Skip if already has profile and user doesn't want to update
            if existing_profiles.get(platform):
                update_existing = input(f"\n{platform} already has profile. Update? (y/n): ").strip().lower()
                if update_existing != 'y':
                    continue
            
            if platform in discovered_profiles:
                selected_url = interactive_profile_selection(
                    faculty_name, platform, discovered_profiles[platform]
                )
                
                if selected_url == "SKIP":
                    stats['skipped'] += 1
                    continue
                elif selected_url:
                    profile_updates[platform] = selected_url
        
        # Update the JSON file
        if profile_updates:
            if update_faculty_json(json_file, profile_updates):
                stats['updated_files'] += 1
                stats['updated_profiles'] += len(profile_updates)
        
        # Ask if user wants to continue
        if stats['total_files'] > 1:  # Don't ask for the last one
            continue_choice = input(f"\nContinue to next faculty? (y/n/q to quit): ").strip().lower()
            if continue_choice == 'q':
                break
    
    return stats

def generate_validation_report(json_directory: str, output_file: str = "profile_validation_report.html"):
    """Generate an HTML report for profile validation"""
    json_dir = Path(json_directory)
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Faculty Profile Validation Report</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .faculty { border: 1px solid #ddd; margin: 20px 0; padding: 15px; }
            .platform { margin: 10px 0; }
            .profile-link { color: #0066cc; text-decoration: none; }
            .confidence-high { color: #28a745; font-weight: bold; }
            .confidence-medium { color: #ffc107; font-weight: bold; }
            .confidence-low { color: #dc3545; font-weight: bold; }
            .existing-profile { background-color: #e8f5e8; padding: 5px; }
        </style>
    </head>
    <body>
        <h1>Faculty Profile Validation Report</h1>
        <p>Generated on: """ + str(Path.cwd()) + """</p>
    """
    
    faculty_count = 0
    for json_file in json_dir.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            faculty_count += 1
            html_content += f"""
            <div class="faculty">
                <h3>{data.get('name', 'Unknown')} ({data.get('faculty_id', 'Unknown')})</h3>
                <p><strong>Department:</strong> {data.get('department', 'Unknown')}</p>
                <p><strong>University:</strong> {data.get('university', 'Unknown')}</p>
                
                <h4>Current Profiles:</h4>
            """
            
            platforms = ['gscholar', 'orcid', 'openalex', 'researchgate', 'academicedu', 'linkedin', 'scopus', 'wos']
            for platform in platforms:
                url = data.get(platform, '')
                if url:
                    html_content += f"""
                    <div class="platform existing-profile">
                        <strong>{platform.title()}:</strong> 
                        <a href="{url}" target="_blank" class="profile-link">{url}</a>
                    </div>
                    """
                else:
                    html_content += f"""
                    <div class="platform">
                        <strong>{platform.title()}:</strong> <em>Not available</em>
                    </div>
                    """
            
            html_content += "</div>"
            
        except Exception as e:
            print(f"Error processing {json_file}: {e}")
    
    html_content += f"""
        <p><strong>Total Faculty Processed:</strong> {faculty_count}</p>
    </body>
    </html>
    """
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"📄 Validation report saved: {output_file}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Update faculty profiles from discovery report')
    parser.add_argument('--json-dir', 
                       default='data/faculties/CA/ON/CA-ON-002_mcmaster.ca/HEI/CA-ON-002_mcmaster.ca_HEI_jsons',
                       help='Directory containing faculty JSON files')
    parser.add_argument('--report', 
                       default='profile_discovery_report.json',
                       help='Discovery report file')
    parser.add_argument('--mode', 
                       choices=['auto', 'interactive', 'validate'],
                       default='auto',
                       help='Update mode: auto (high confidence), interactive, or validate (generate report)')
    parser.add_argument('--confidence', 
                       type=float, 
                       default=0.8,
                       help='Confidence threshold for auto mode (0.0-1.0)')
    
    args = parser.parse_args()
    
    if args.mode == 'validate':
        generate_validation_report(args.json_dir)
        return
    
    # Load discovery report
    discovery_report = load_discovery_report(args.report)
    if not discovery_report:
        return
    
    print(f"📊 Discovery report loaded: {len(discovery_report.get('discovery_results', []))} faculty")
    
    # Update profiles based on mode
    if args.mode == 'auto':
        stats = auto_update_high_confidence(args.json_dir, discovery_report, args.confidence)
    else:  # interactive
        stats = interactive_update(args.json_dir, discovery_report)
    
    # Display final statistics
    print(f"\n🎉 Update completed!")
    print(f"📊 Statistics:")
    print(f"   Files processed: {stats['total_files']}")
    print(f"   Files updated: {stats['updated_files']}")
    print(f"   Profiles updated: {stats['updated_profiles']}")
    if 'skipped' in stats:
        print(f"   Profiles skipped: {stats['skipped']}")

if __name__ == "__main__":
    main() 