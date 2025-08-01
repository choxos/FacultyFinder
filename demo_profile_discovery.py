#!/usr/bin/env python3
"""
Profile Discovery Demonstration
Shows how the system works with real examples and sample searches
"""

import json
import time
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class MockSearchResult:
    platform: str
    name_variation: str
    url: str
    title: str
    description: str
    confidence: float

def demo_name_variations():
    """Demonstrate name variation generation"""
    print("🔤 Name Variation Generation Demo")
    print("=" * 50)
    
    faculty_examples = [
        ("Julia", "", "Abelson"),
        ("Gina", "", "Agarwal"),
        ("Thomas", "", "Agoritsas"),
        ("Noori", "", "Akhtar-Danesh"),
        ("Elie", "A", "Akl")
    ]
    
    for first, middle, last in faculty_examples:
        print(f"\n👤 Faculty: {first} {middle} {last}".strip())
        
        # Variation 1: First + Last
        var1 = f"{first} {last}"
        print(f"   📝 Variation 1: '{var1}'")
        
        # Variation 2: First + Middle + Last (if middle exists)
        if middle:
            var2 = f"{first} {middle} {last}"
            print(f"   📝 Variation 2: '{var2}'")
        else:
            print(f"   📝 Variation 2: (same as variation 1)")

def demo_confidence_scoring():
    """Demonstrate confidence scoring algorithm"""
    print("\n🎯 Confidence Scoring Demo")
    print("=" * 50)
    
    search_name = "Julia Abelson"
    
    found_names = [
        ("Julia Abelson", 1.0, "Exact match"),
        ("Julia M. Abelson", 0.9, "Close match with middle initial"),
        ("Dr. Julia Abelson", 0.9, "Match with title"),
        ("Julia Abelson-Smith", 0.7, "Partial match with hyphenated name"),
        ("J. Abelson", 0.6, "Initial + last name"),
        ("Julia Anderson", 0.3, "Different last name"),
        ("Julie Abelson", 0.3, "Similar first name"),
        ("John Abelson", 0.2, "Same last name, different first")
    ]
    
    print(f"🔍 Searching for: '{search_name}'")
    print()
    
    for found_name, confidence, reason in found_names:
        emoji = "🟢" if confidence >= 0.8 else "🟡" if confidence >= 0.5 else "🔴"
        print(f"{emoji} {confidence:.1f} - '{found_name}' ({reason})")

def demo_platform_search_results():
    """Demonstrate sample search results from different platforms"""
    print("\n🌐 Platform Search Results Demo")
    print("=" * 50)
    
    # Mock results for "Julia Abelson"
    mock_results = {
        'google_scholar': [
            MockSearchResult(
                platform='google_scholar',
                name_variation='Julia Abelson',
                url='https://scholar.google.com/citations?user=JyveCpEAAAAJ',
                title='Julia Abelson',
                description='Professor at McMaster University - Health Policy',
                confidence=0.95
            ),
            MockSearchResult(
                platform='google_scholar',
                name_variation='Julia Abelson',
                url='https://scholar.google.com/citations?user=xyz123',
                title='Julia M. Abelson',
                description='University of Toronto',
                confidence=0.75
            )
        ],
        'orcid': [
            MockSearchResult(
                platform='orcid',
                name_variation='Julia Abelson',
                url='https://orcid.org/0000-0002-2907-2783',
                title='Julia Abelson',
                description='ORCID ID: 0000-0002-2907-2783',
                confidence=0.90
            )
        ],
        'openalex': [
            MockSearchResult(
                platform='openalex',
                name_variation='Julia Abelson',
                url='https://openalex.org/A5043118077',
                title='Julia Abelson',
                description='McMaster University; Health Policy',
                confidence=0.92
            )
        ],
        'researchgate': [
            MockSearchResult(
                platform='researchgate',
                name_variation='Julia Abelson',
                url='https://www.researchgate.net/profile/Julia-Abelson',
                title='Julia Abelson',
                description='McMaster University - Health Research Methods',
                confidence=0.88
            )
        ]
    }
    
    for platform, results in mock_results.items():
        print(f"\n🔍 {platform.upper()} Results:")
        print("-" * 40)
        
        for i, result in enumerate(results, 1):
            confidence_emoji = "🟢" if result.confidence >= 0.8 else "🟡" if result.confidence >= 0.5 else "🔴"
            print(f"  {i}. {confidence_emoji} {result.title}")
            print(f"     URL: {result.url}")
            print(f"     Confidence: {result.confidence:.2f}")
            print(f"     Description: {result.description}")
            print()

def demo_discovery_report():
    """Demonstrate the discovery report structure"""
    print("📄 Discovery Report Demo")
    print("=" * 50)
    
    sample_report = {
        "timestamp": "2025-01-09 20:30:00",
        "total_faculty": 1,
        "discovery_results": [
            {
                "faculty_id": "CA-ON-002-00001",
                "name": "Julia Abelson",
                "name_variations": ["Julia Abelson"],
                "existing_profiles": {
                    "gscholar": "JyveCpEAAAAJ",
                    "orcid": "0000-0002-2907-2783",
                    "openalex": "A5043118077",
                    "researchgate": "",
                    "academicedu": "",
                    "linkedin": "julia-abelson-8999a319",
                    "scopus": "7102191638",
                    "wos": ""
                },
                "discovered_profiles": {
                    "google_scholar": [
                        {
                            "url": "https://scholar.google.com/citations?user=JyveCpEAAAAJ",
                            "title": "Julia Abelson",
                            "description": "McMaster University - Health Policy",
                            "confidence": 0.95,
                            "name_variation": "Julia Abelson"
                        }
                    ],
                    "researchgate": [
                        {
                            "url": "https://www.researchgate.net/profile/Julia-Abelson",
                            "title": "Julia Abelson",
                            "description": "McMaster University",
                            "confidence": 0.88,
                            "name_variation": "Julia Abelson"
                        }
                    ]
                },
                "recommendations": {
                    "google_scholar": {
                        "url": "https://scholar.google.com/citations?user=JyveCpEAAAAJ",
                        "confidence": 0.95,
                        "reason": "High confidence match"
                    },
                    "researchgate": {
                        "url": "https://www.researchgate.net/profile/Julia-Abelson",
                        "confidence": 0.88,
                        "reason": "High confidence match"
                    }
                }
            }
        ]
    }
    
    print("📋 Sample Discovery Report Structure:")
    print(json.dumps(sample_report, indent=2))

def demo_update_modes():
    """Demonstrate different update modes"""
    print("\n🔄 Update Modes Demo")
    print("=" * 50)
    
    print("1️⃣ AUTO MODE (--mode auto --confidence 0.8)")
    print("   • Automatically updates profiles with confidence ≥ 0.8")
    print("   • Safe for bulk processing")
    print("   • Example: Updates Google Scholar (0.95) and ResearchGate (0.88)")
    print()
    
    print("2️⃣ INTERACTIVE MODE (--mode interactive)")
    print("   • Shows all discovered profiles for manual selection")
    print("   • User chooses which profiles to update")
    print("   • Example interaction:")
    print("     🔍 GOOGLE_SCHOLAR profiles for Julia Abelson:")
    print("     1. 🟢 Julia Abelson")
    print("        URL: https://scholar.google.com/citations?user=JyveCpEAAAAJ")
    print("        Confidence: 0.95")
    print("     Select profile (1-1, 0 for none, 's' to skip): 1")
    print()
    
    print("3️⃣ VALIDATION MODE (--mode validate)")
    print("   • Generates HTML report of current profiles")
    print("   • No updates made to data")
    print("   • Shows what profiles exist and what's missing")

def demo_workflow_example():
    """Demonstrate complete workflow"""
    print("\n🚀 Complete Workflow Example")
    print("=" * 50)
    
    workflow_steps = [
        ("🔍 Discovery", "python3 profile_discoverer.py", "Search all platforms for faculty profiles"),
        ("🤖 Auto Update", "python3 update_profiles_from_discovery.py --mode auto", "Update high-confidence matches"),
        ("🖱️ Interactive", "python3 update_profiles_from_discovery.py --mode interactive", "Review and validate remaining profiles"),
        ("📄 Validation", "python3 update_profiles_from_discovery.py --mode validate", "Generate HTML report for review"),
        ("💾 Database Sync", "python3 json_to_postgres.py", "Update PostgreSQL database")
    ]
    
    print("Complete workflow for faculty profile discovery:")
    print()
    
    for i, (stage, command, description) in enumerate(workflow_steps, 1):
        print(f"{i}. {stage}")
        print(f"   Command: {command}")
        print(f"   Purpose: {description}")
        print()

def demo_real_world_scenarios():
    """Demonstrate real-world scenarios and challenges"""
    print("🌍 Real-World Scenarios Demo")
    print("=" * 50)
    
    scenarios = [
        {
            "name": "Common Success Case",
            "faculty": "Julia Abelson",
            "challenge": "Faculty with well-established online presence",
            "expected": "High confidence matches on multiple platforms",
            "action": "Auto-update safe, manual verification recommended"
        },
        {
            "name": "Name Variation Challenge",
            "faculty": "Elie A Akl",
            "challenge": "Middle initial that may or may not be used",
            "expected": "Need to search 'Elie Akl' and 'Elie A Akl'",
            "action": "Compare results from both variations"
        },
        {
            "name": "Hyphenated Names",
            "faculty": "Noori Akhtar-Danesh",
            "challenge": "Hyphenated name might be split or combined",
            "expected": "Search for 'Noori Akhtar-Danesh' and 'Noori Akhtar Danesh'",
            "action": "Manual verification important for accuracy"
        },
        {
            "name": "Common Name Issue",
            "faculty": "John Smith",
            "challenge": "Very common name with many false positives",
            "expected": "Many low-confidence matches",
            "action": "Require affiliation matching for validation"
        },
        {
            "name": "New Faculty",
            "faculty": "Early Career Researcher",
            "challenge": "Limited online presence",
            "expected": "Few or no matches found",
            "action": "Manual profile creation may be needed"
        }
    ]
    
    for scenario in scenarios:
        print(f"📋 {scenario['name']}")
        print(f"   Faculty: {scenario['faculty']}")
        print(f"   Challenge: {scenario['challenge']}")
        print(f"   Expected: {scenario['expected']}")
        print(f"   Action: {scenario['action']}")
        print()

def main():
    """Run all demonstrations"""
    print("🎭 Profile Discovery System Demonstration")
    print("=" * 60)
    print("This demo shows how the academic profile discovery system works")
    print("with real examples and practical scenarios.\n")
    
    # Run all demos
    demo_name_variations()
    demo_confidence_scoring()
    demo_platform_search_results()
    demo_discovery_report()
    demo_update_modes()
    demo_workflow_example()
    demo_real_world_scenarios()
    
    print("\n" + "=" * 60)
    print("✅ Profile Discovery System Demo Complete!")
    print("\nTo get started with real data:")
    print("1. Install dependencies: pip install beautifulsoup4 aiohttp")
    print("2. Run discovery: python3 profile_discoverer.py")
    print("3. Update profiles: python3 update_profiles_from_discovery.py --mode auto")
    print("4. Read the guide: PROFILE_DISCOVERY_GUIDE.md")

if __name__ == "__main__":
    main() 