#!/usr/bin/env python3
"""
Academic Profile Discoverer
Searches across academic and professional platforms to find faculty profiles
using name variations for easier validation and profile linking
"""

import json
import requests
import time
import re
from pathlib import Path
from urllib.parse import quote, urlencode
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
from bs4 import BeautifulSoup
import asyncio
import aiohttp

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    platform: str
    name_variation: str
    url: str
    title: str
    description: str
    confidence: float  # 0-1 scale

@dataclass
class FacultyProfile:
    faculty_id: str
    name: str
    first_name: str
    last_name: str
    middle_names: str
    affiliation: str
    existing_profiles: Dict[str, str]

class ProfileSearcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.rate_limits = {
            'google_scholar': 2,  # seconds between requests
            'orcid': 1,
            'researchgate': 3,
            'academia': 2,
            'linkedin': 2,
            'openalex': 1,
            'scopus': 2,
            'wos': 3
        }
    
    def generate_name_variations(self, faculty: FacultyProfile) -> List[str]:
        """Generate name variations for searching"""
        variations = []
        
        # Variation 1: First + Last
        if faculty.first_name and faculty.last_name:
            variations.append(f"{faculty.first_name} {faculty.last_name}")
        
        # Variation 2: First + Middle + Last
        if faculty.first_name and faculty.last_name:
            if faculty.middle_names:
                variations.append(f"{faculty.first_name} {faculty.middle_names} {faculty.last_name}")
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(variations))
    
    def search_google_scholar(self, name: str, affiliation: str = "") -> List[SearchResult]:
        """Search Google Scholar for profiles"""
        try:
            time.sleep(self.rate_limits['google_scholar'])
            
            # Google Scholar search URL
            base_url = "https://scholar.google.com/citations"
            params = {
                'view_op': 'search_authors',
                'mauthors': f"{name} {affiliation}".strip(),
                'hl': 'en'
            }
            
            url = f"{base_url}?{urlencode(params)}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                results = []
                
                # Parse Google Scholar results
                for result in soup.find_all('div', class_='gsc_1usr')[:3]:  # Top 3 results
                    try:
                        name_elem = result.find('h3', class_='gsc_1usr_name')
                        if name_elem and name_elem.find('a'):
                            profile_url = "https://scholar.google.com" + name_elem.find('a')['href']
                            profile_name = name_elem.get_text().strip()
                            
                            affil_elem = result.find('div', class_='gsc_1usr_aff')
                            affiliation_text = affil_elem.get_text().strip() if affil_elem else ""
                            
                            # Calculate confidence based on name similarity
                            confidence = self.calculate_name_confidence(name, profile_name)
                            
                            results.append(SearchResult(
                                platform='google_scholar',
                                name_variation=name,
                                url=profile_url,
                                title=profile_name,
                                description=affiliation_text,
                                confidence=confidence
                            ))
                    except Exception as e:
                        logger.warning(f"Error parsing Google Scholar result: {e}")
                
                return results
                
        except Exception as e:
            logger.error(f"Google Scholar search failed for '{name}': {e}")
            return []
    
    def search_orcid(self, name: str) -> List[SearchResult]:
        """Search ORCID for profiles"""
        try:
            time.sleep(self.rate_limits['orcid'])
            
            # ORCID API search
            api_url = "https://pub.orcid.org/v3.0/search"
            params = {
                'q': f'given-names:{name.split()[0]} AND family-name:{name.split()[-1]}',
                'format': 'json'
            }
            
            response = self.session.get(api_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for result in data.get('result', [])[:3]:  # Top 3 results
                    try:
                        orcid_id = result.get('orcid-identifier', {}).get('path', '')
                        profile_url = f"https://orcid.org/{orcid_id}"
                        
                        # Get display name
                        person_details = result.get('person-details', {})
                        display_name = ""
                        if person_details:
                            given_names = person_details.get('given-names', {}).get('value', '')
                            family_names = person_details.get('family-names', {}).get('value', '')
                            display_name = f"{given_names} {family_names}".strip()
                        
                        confidence = self.calculate_name_confidence(name, display_name)
                        
                        results.append(SearchResult(
                            platform='orcid',
                            name_variation=name,
                            url=profile_url,
                            title=display_name or orcid_id,
                            description=f"ORCID ID: {orcid_id}",
                            confidence=confidence
                        ))
                    except Exception as e:
                        logger.warning(f"Error parsing ORCID result: {e}")
                
                return results
                
        except Exception as e:
            logger.error(f"ORCID search failed for '{name}': {e}")
            return []
    
    def search_openalex(self, name: str, affiliation: str = "") -> List[SearchResult]:
        """Search OpenAlex for author profiles"""
        try:
            time.sleep(self.rate_limits['openalex'])
            
            # OpenAlex API search
            api_url = "https://api.openalex.org/authors"
            params = {
                'search': name,
                'per-page': 3
            }
            
            if affiliation:
                params['search'] += f" {affiliation}"
            
            response = self.session.get(api_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for author in data.get('results', []):
                    try:
                        author_id = author.get('id', '').replace('https://openalex.org/', '')
                        display_name = author.get('display_name', '')
                        profile_url = f"https://openalex.org/{author_id}"
                        
                        # Get affiliation
                        affiliations = author.get('affiliations', [])
                        affil_names = [affil.get('institution', {}).get('display_name', '') 
                                     for affil in affiliations[:2]]
                        affil_text = '; '.join(filter(None, affil_names))
                        
                        confidence = self.calculate_name_confidence(name, display_name)
                        
                        results.append(SearchResult(
                            platform='openalex',
                            name_variation=name,
                            url=profile_url,
                            title=display_name,
                            description=affil_text,
                            confidence=confidence
                        ))
                    except Exception as e:
                        logger.warning(f"Error parsing OpenAlex result: {e}")
                
                return results
                
        except Exception as e:
            logger.error(f"OpenAlex search failed for '{name}': {e}")
            return []
    
    def search_web_platforms(self, name: str, platform: str) -> List[SearchResult]:
        """Search web-based platforms (ResearchGate, Academia.edu, LinkedIn)"""
        try:
            time.sleep(self.rate_limits.get(platform, 2))
            
            search_urls = {
                'researchgate': f"https://www.researchgate.net/search/researcher?q={quote(name)}",
                'academia': f"https://www.academia.edu/search?q={quote(name)}",
                'linkedin': f"https://www.linkedin.com/search/results/people/?keywords={quote(name)}"
            }
            
            if platform not in search_urls:
                return []
            
            url = search_urls[platform]
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                results = []
                
                # Platform-specific parsing
                if platform == 'researchgate':
                    for result in soup.find_all('div', class_='nova-legacy-e-text')[:3]:
                        try:
                            link = result.find('a')
                            if link:
                                profile_url = "https://www.researchgate.net" + link['href']
                                profile_name = link.get_text().strip()
                                
                                confidence = self.calculate_name_confidence(name, profile_name)
                                
                                results.append(SearchResult(
                                    platform='researchgate',
                                    name_variation=name,
                                    url=profile_url,
                                    title=profile_name,
                                    description="ResearchGate Profile",
                                    confidence=confidence
                                ))
                        except Exception as e:
                            logger.warning(f"Error parsing ResearchGate result: {e}")
                
                elif platform == 'academia':
                    for result in soup.find_all('div', class_='work-card')[:3]:
                        try:
                            link = result.find('a')
                            if link and link.get('href'):
                                profile_url = link['href']
                                profile_name = link.get_text().strip()
                                
                                confidence = self.calculate_name_confidence(name, profile_name)
                                
                                results.append(SearchResult(
                                    platform='academia',
                                    name_variation=name,
                                    url=profile_url,
                                    title=profile_name,
                                    description="Academia.edu Profile",
                                    confidence=confidence
                                ))
                        except Exception as e:
                            logger.warning(f"Error parsing Academia result: {e}")
                
                return results
                
        except Exception as e:
            logger.error(f"{platform} search failed for '{name}': {e}")
            return []
    
    def calculate_name_confidence(self, search_name: str, found_name: str) -> float:
        """Calculate confidence score based on name similarity"""
        if not search_name or not found_name:
            return 0.0
        
        # Normalize names (lowercase, remove extra spaces)
        search_parts = search_name.lower().split()
        found_parts = found_name.lower().split()
        
        # Check for exact match
        if search_name.lower() == found_name.lower():
            return 1.0
        
        # Check if all search name parts are in found name
        search_in_found = all(part in ' '.join(found_parts) for part in search_parts)
        found_in_search = all(part in ' '.join(search_parts) for part in found_parts)
        
        if search_in_found and found_in_search:
            return 0.9
        elif search_in_found or found_in_search:
            return 0.7
        
        # Check for partial matches
        matches = sum(1 for part in search_parts if part in found_parts)
        total_parts = len(search_parts)
        
        return matches / total_parts if total_parts > 0 else 0.0
    
    def search_all_platforms(self, faculty: FacultyProfile) -> Dict[str, List[SearchResult]]:
        """Search all platforms for a faculty member"""
        logger.info(f"🔍 Searching profiles for: {faculty.name}")
        
        all_results = {}
        name_variations = self.generate_name_variations(faculty)
        
        logger.info(f"📝 Name variations: {name_variations}")
        
        for name_var in name_variations:
            logger.info(f"🔎 Searching with name: '{name_var}'")
            
            # Search each platform
            platforms = [
                ('google_scholar', lambda: self.search_google_scholar(name_var, faculty.affiliation)),
                ('orcid', lambda: self.search_orcid(name_var)),
                ('openalex', lambda: self.search_openalex(name_var, faculty.affiliation)),
                ('researchgate', lambda: self.search_web_platforms(name_var, 'researchgate')),
                ('academia', lambda: self.search_web_platforms(name_var, 'academia')),
            ]
            
            for platform_name, search_func in platforms:
                try:
                    results = search_func()
                    if results:
                        if platform_name not in all_results:
                            all_results[platform_name] = []
                        all_results[platform_name].extend(results)
                        logger.info(f"✅ Found {len(results)} results on {platform_name}")
                    else:
                        logger.info(f"❌ No results on {platform_name}")
                except Exception as e:
                    logger.error(f"❌ Error searching {platform_name}: {e}")
        
        return all_results

class ProfileDiscoveryManager:
    def __init__(self, json_directory: str):
        self.json_directory = Path(json_directory)
        self.searcher = ProfileSearcher()
    
    def load_faculty_data(self) -> List[FacultyProfile]:
        """Load faculty data from JSON files"""
        faculty_list = []
        
        if not self.json_directory.exists():
            logger.error(f"Directory not found: {self.json_directory}")
            return faculty_list
        
        for json_file in self.json_directory.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                faculty = FacultyProfile(
                    faculty_id=data.get('faculty_id', ''),
                    name=data.get('name', ''),
                    first_name=data.get('first_name', ''),
                    last_name=data.get('last_name', ''),
                    middle_names=data.get('middle_names', ''),
                    affiliation=data.get('university', ''),
                    existing_profiles={
                        'gscholar': data.get('gscholar', ''),
                        'orcid': data.get('orcid', ''),
                        'openalex': data.get('openalex', ''),
                        'researchgate': data.get('researchgate', ''),
                        'academicedu': data.get('academicedu', ''),
                        'linkedin': data.get('linkedin', ''),
                        'scopus': data.get('scopus', ''),
                        'wos': data.get('wos', '')
                    }
                )
                faculty_list.append(faculty)
                
            except Exception as e:
                logger.error(f"Error loading {json_file}: {e}")
        
        return faculty_list
    
    def generate_discovery_report(self, faculty_list: List[FacultyProfile], output_file: str = "profile_discovery_report.json"):
        """Generate comprehensive discovery report"""
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_faculty': len(faculty_list),
            'discovery_results': []
        }
        
        for faculty in faculty_list:
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing: {faculty.name} ({faculty.faculty_id})")
            logger.info(f"{'='*60}")
            
            # Search all platforms
            search_results = self.searcher.search_all_platforms(faculty)
            
            faculty_report = {
                'faculty_id': faculty.faculty_id,
                'name': faculty.name,
                'name_variations': self.searcher.generate_name_variations(faculty),
                'existing_profiles': faculty.existing_profiles,
                'discovered_profiles': {},
                'recommendations': {}
            }
            
            # Process results for each platform
            for platform, results in search_results.items():
                if results:
                    # Sort by confidence score
                    sorted_results = sorted(results, key=lambda x: x.confidence, reverse=True)
                    
                    faculty_report['discovered_profiles'][platform] = [
                        {
                            'url': result.url,
                            'title': result.title,
                            'description': result.description,
                            'confidence': result.confidence,
                            'name_variation': result.name_variation
                        }
                        for result in sorted_results
                    ]
                    
                    # Recommend highest confidence result
                    best_result = sorted_results[0]
                    if best_result.confidence >= 0.7:  # High confidence threshold
                        faculty_report['recommendations'][platform] = {
                            'url': best_result.url,
                            'confidence': best_result.confidence,
                            'reason': 'High confidence match'
                        }
            
            report['discovery_results'].append(faculty_report)
            
            # Display summary for this faculty
            self.display_faculty_summary(faculty, search_results)
        
        # Save report
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n🎉 Discovery report saved to: {output_file}")
        return report
    
    def display_faculty_summary(self, faculty: FacultyProfile, results: Dict[str, List[SearchResult]]):
        """Display summary for a faculty member"""
        print(f"\n📋 SUMMARY for {faculty.name}")
        print("-" * 50)
        
        for platform in ['google_scholar', 'orcid', 'openalex', 'researchgate', 'academia']:
            print(f"\n🔍 {platform.upper()}:")
            
            if platform in results and results[platform]:
                sorted_results = sorted(results[platform], key=lambda x: x.confidence, reverse=True)
                
                for i, result in enumerate(sorted_results[:2], 1):
                    confidence_emoji = "🟢" if result.confidence >= 0.8 else "🟡" if result.confidence >= 0.5 else "🔴"
                    print(f"  {i}. {confidence_emoji} {result.title}")
                    print(f"     URL: {result.url}")
                    print(f"     Confidence: {result.confidence:.2f}")
                    print(f"     Description: {result.description}")
                    print(f"     Name used: {result.name_variation}")
            else:
                print("  ❌ No results found")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Discover academic profiles for faculty members')
    parser.add_argument('--json-dir', 
                       default='data/faculties/CA/ON/CA-ON-002_mcmaster.ca/HEI/CA-ON-002_mcmaster.ca_HEI_jsons',
                       help='Directory containing faculty JSON files')
    parser.add_argument('--output', 
                       default='profile_discovery_report.json',
                       help='Output file for discovery report')
    parser.add_argument('--faculty-id', 
                       help='Process only specific faculty ID')
    
    args = parser.parse_args()
    
    # Initialize discovery manager
    manager = ProfileDiscoveryManager(args.json_dir)
    
    # Load faculty data
    faculty_list = manager.load_faculty_data()
    
    if not faculty_list:
        logger.error("No faculty data found!")
        return
    
    # Filter by faculty ID if specified
    if args.faculty_id:
        faculty_list = [f for f in faculty_list if f.faculty_id == args.faculty_id]
        if not faculty_list:
            logger.error(f"Faculty ID {args.faculty_id} not found!")
            return
    
    logger.info(f"🚀 Starting profile discovery for {len(faculty_list)} faculty members")
    
    # Generate discovery report
    report = manager.generate_discovery_report(faculty_list, args.output)
    
    # Display final statistics
    total_discovered = sum(len(faculty['discovered_profiles']) for faculty in report['discovery_results'])
    total_recommendations = sum(len(faculty['recommendations']) for faculty in report['discovery_results'])
    
    logger.info(f"\n📊 FINAL STATISTICS:")
    logger.info(f"   Faculty processed: {len(faculty_list)}")
    logger.info(f"   Profiles discovered: {total_discovered}")
    logger.info(f"   High-confidence recommendations: {total_recommendations}")
    logger.info(f"   Report saved: {args.output}")

if __name__ == "__main__":
    main() 