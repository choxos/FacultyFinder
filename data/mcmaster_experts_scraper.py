import csv
import re
import json
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin, urlparse
import requests
from datetime import datetime

class McMasterExpertsScraper:
    def __init__(self, base_url="https://experts.mcmaster.ca"):
        self.base_url = base_url
        
    def extract_expert_profile(self, html_content, profile_url=None):
        """
        Extract comprehensive information from a McMaster Experts profile page
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        profile_data = {}
        
        # Basic Information
        profile_data.update(self._extract_basic_info(soup))
        
        # Contact Information
        profile_data.update(self._extract_contact_info(soup))
        
        # Overview/Biography
        profile_data.update(self._extract_overview(soup))
        
        # Affiliations
        profile_data.update(self._extract_affiliations(soup))
        
        # Research Areas
        profile_data.update(self._extract_research_areas(soup))
        
        # Education & Background
        profile_data.update(self._extract_education(soup))
        
        # Publications
        profile_data.update(self._extract_publications(soup))
        
        # Teaching Activities
        profile_data.update(self._extract_teaching(soup))
        
        # Network/Collaboration Links
        profile_data.update(self._extract_network_links(soup))
        
        # Meta information
        profile_data['profile_url'] = profile_url
        profile_data['scraped_date'] = datetime.now().isoformat()
        
        return profile_data
    
    def _extract_basic_info(self, soup):
        """Extract name, title, photo, etc."""
        data = {}
        
        # Name - Clean up whitespace and newlines
        name_elem = soup.find('span', {'itemprop': 'name', 'class': 'fn'})
        if name_elem:
            # Get text and clean up whitespace/newlines
            raw_name = name_elem.get_text()
            # Replace multiple whitespace characters (including newlines) with single space
            clean_name = ' '.join(raw_name.split())
            data['name'] = clean_name
            
            # Extract first and last names
            name_parts = clean_name.split()
            if len(name_parts) >= 2:
                data['first_name'] = name_parts[0]
                data['last_name'] = name_parts[-1]
                if len(name_parts) > 2:
                    data['middle_names'] = ' '.join(name_parts[1:-1])
                else:
                    data['middle_names'] = ''
            elif len(name_parts) == 1:
                data['first_name'] = name_parts[0]
                data['last_name'] = ''
                data['middle_names'] = ''
            else:
                data['first_name'] = ''
                data['last_name'] = ''
                data['middle_names'] = ''
        else:
            data['name'] = ''
            data['first_name'] = ''
            data['last_name'] = ''
            data['middle_names'] = ''
        
        # Title/Position
        title_elem = soup.find('span', {'itemprop': 'jobTitle'})
        data['title'] = title_elem.get_text(strip=True) if title_elem else ''
        
        # Photo URL
        photo_elem = soup.find('img', class_='individual-photo')
        if photo_elem:
            data['photo_url'] = urljoin(self.base_url, photo_elem.get('src', ''))
        else:
            data['photo_url'] = ''
            
        return data
    
    def _extract_contact_info(self, soup):
        """Extract email, websites, social media"""
        data = {}
        
        # Email (handle obfuscation)
        email_elem = soup.find('a', class_='email')
        if email_elem:
            email_href = email_elem.get('href', '')
            # Handle McMaster's email obfuscation
            if 'vivo7vivo' in email_href:
                email = email_href.replace('mailto:', '').replace('vivo7vivo', '@')
            else:
                email = email_href.replace('mailto:', '')
            data['email'] = email
        else:
            data['email'] = ''
        
        # Websites and social media
        data['websites'] = []
        data['linkedin'] = ''
        data['twitter'] = ''
        
        # Extract from social links div
        social_links = soup.find('div', id='individualsociallinks')
        if social_links:
            linkedin_pattern = r'linkedin\.com/in/([^"\']+)'
            linkedin_match = re.search(linkedin_pattern, str(social_links))
            if linkedin_match:
                data['linkedin'] = f"https://linkedin.com/in/{linkedin_match.group(1)}"
        
        # Extract from non-social links div
        nonsocial_links = soup.find('div', id='individualnonsociallinks')
        if nonsocial_links:
            links = nonsocial_links.find_all('a')
            for link in links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                if href:
                    data['websites'].append({'url': href, 'title': text})
        
        # Convert websites list to string for CSV compatibility
        data['websites_json'] = json.dumps(data['websites'])
        data['primary_website'] = data['websites'][0]['url'] if data['websites'] else ''
        
        return data
    
    def _extract_overview(self, soup):
        """Extract biography/overview"""
        data = {}
        
        overview_elem = soup.find('div', class_='overview-value')
        data['overview'] = overview_elem.get_text(strip=True) if overview_elem else ''
        
        return data
    
    def _extract_affiliations(self, soup):
        """Extract institutional affiliations"""
        data = {}
        affiliations = []
        
        affiliation_list = soup.find('ul', id='individual-personInPosition')
        if affiliation_list:
            items = affiliation_list.find_all('li', role='listitem')
            for item in items:
                affiliation = {}
                
                # Position/title
                job_title = item.find('span', {'itemprop': 'jobTitle'})
                if job_title:
                    affiliation['position'] = job_title.get_text(strip=True).rstrip(',')
                
                # Organization
                org_links = item.find_all('a')
                orgs = []
                for org_link in org_links:
                    org_name = org_link.find('span', {'itemprop': 'name'})
                    if org_name:
                        orgs.append(org_name.get_text(strip=True))
                
                affiliation['organizations'] = ' > '.join(orgs)
                
                if affiliation.get('organizations'):
                    affiliations.append(affiliation)
        
        # Store detailed affiliations data
        data['affiliations_json'] = json.dumps(affiliations)
        
        # Create concatenated strings for CSV (ALL affiliations)
        if affiliations:
            # All affiliations with positions (for detailed view)
            full_affiliations = []
            for aff in affiliations:
                position = aff.get('position', '')
                org = aff.get('organizations', '')
                if position and org:
                    full_affiliations.append(f"{position}, {org}")
                elif org:
                    full_affiliations.append(org)
            
            data['all_affiliations'] = ' ; '.join(full_affiliations)
            
            # All organizations only (for simpler view)
            all_orgs = [aff['organizations'] for aff in affiliations if aff.get('organizations')]
            data['all_organizations'] = ' ; '.join(all_orgs)
            
            # Primary affiliation (first one for backward compatibility)
            data['primary_affiliation'] = affiliations[0]['organizations'] 
            data['primary_position'] = affiliations[0].get('position', '')
        else:
            data['all_affiliations'] = ''
            data['all_organizations'] = ''
            data['primary_affiliation'] = ''
            data['primary_position'] = ''
        
        return data
    
    def _extract_research_areas(self, soup):
        """Extract research areas/interests"""
        data = {}
        research_areas = []
        
        research_list = soup.find('ul', id='individual-hasResearchArea')
        if research_list:
            items = research_list.find_all('li', role='listitem')
            for item in items:
                link = item.find('a')
                if link:
                    area = link.get_text(strip=True)
                    # Remove the "(RA)" suffix if present
                    area = re.sub(r'\s*\(RA\)$', '', area)
                    research_areas.append(area)
        
        data['research_areas'] = ' | '.join(research_areas)
        data['research_areas_json'] = json.dumps(research_areas)
        
        return data
    
    def _extract_education(self, soup):
        """Extract education and training"""
        data = {}
        education = []
        
        education_list = soup.find('ul', id='RO_0000056-EducationalProcess-List')
        if education_list:
            items = education_list.find_all('li', role='listitem')
            for item in items:
                edu_text = item.get_text(strip=True)
                # Parse degree and institution
                if ',' in edu_text:
                    parts = edu_text.split(',', 1)
                    degree = parts[0].strip()
                    institution = parts[1].strip()
                    education.append({'degree': degree, 'institution': institution})
                else:
                    education.append({'degree': edu_text, 'institution': ''})
        
        # Store detailed education data
        data['education_json'] = json.dumps(education)
        
        # Create concatenated strings for CSV (ALL degrees)
        if education:
            # All degrees with institutions (for detailed view)
            full_education = []
            for edu in education:
                degree = edu.get('degree', '')
                institution = edu.get('institution', '')
                if degree and institution:
                    full_education.append(f"{degree}, {institution}")
                elif degree:
                    full_education.append(degree)
            
            data['all_degrees'] = ' ; '.join(full_education)
            
            # All degrees only (for simpler view)  
            all_degrees_only = [edu['degree'] for edu in education if edu.get('degree')]
            data['all_degrees_only'] = ' ; '.join(all_degrees_only)
            
            # All institutions only
            all_institutions = [edu['institution'] for edu in education if edu.get('institution')]
            data['all_institutions'] = ' ; '.join(all_institutions)
            
            # Primary degree (first/highest one for backward compatibility)
            data['highest_degree'] = education[0]['degree']
            data['degree_institution'] = education[0]['institution']
        else:
            data['all_degrees'] = ''
            data['all_degrees_only'] = ''
            data['all_institutions'] = ''
            data['highest_degree'] = ''
            data['degree_institution'] = ''
        
        return data
    
    def _extract_publications(self, soup):
        """Extract publications information"""
        data = {}
        publications = {
            'journal_articles': [],
            'chapters': [],
            'conferences': [],
            'other': [],
            'preprints': []
        }
        
        # Find publications section
        pub_section = soup.find('ul', id='relatedBy-Authorship-List')
        if pub_section:
            subcategories = pub_section.find_all('li', class_='subclass')
            
            for subcat in subcategories:
                category_header = subcat.find('h3')
                if not category_header:
                    continue
                    
                category = category_header.get_text(strip=True)
                category_key = self._map_publication_category(category)
                
                pub_list = subcat.find('ul', class_='subclass-property-list')
                if pub_list:
                    items = pub_list.find_all('li', role='listitem')
                    for item in items:
                        pub_data = self._parse_publication_item(item)
                        if pub_data:
                            publications[category_key].append(pub_data)
        
        # Calculate publication counts
        data['total_publications'] = sum(len(pubs) for pubs in publications.values())
        data['journal_articles_count'] = len(publications['journal_articles'])
        data['book_chapters_count'] = len(publications['chapters'])
        data['conference_papers_count'] = len(publications['conferences'])
        
        # Store recent publications (last 5 years)
        current_year = datetime.now().year
        recent_pubs = []
        for pub_list in publications.values():
            for pub in pub_list:
                if pub.get('year') and int(pub['year']) >= current_year - 5:
                    recent_pubs.append(pub)
        
        data['recent_publications_count'] = len(recent_pubs)
        data['publications_json'] = json.dumps(publications)
        
        return data
    
    def _map_publication_category(self, category):
        """Map publication category names to standardized keys"""
        category_map = {
            'journal articles': 'journal_articles',
            'chapters': 'chapters',
            'conferences': 'conferences',
            'preprints': 'preprints',
            'other': 'other'
        }
        return category_map.get(category.lower(), 'other')
    
    def _parse_publication_item(self, item):
        """Parse individual publication item"""
        pub_data = {}
        
        # Title and link
        title_link = item.find('a')
        if title_link:
            pub_data['title'] = title_link.get_text(strip=True)
            pub_data['url'] = urljoin(self.base_url, title_link.get('href', ''))
        
        # Journal/venue (in <em> tags)
        journal_elem = item.find('em')
        if journal_elem:
            pub_data['journal'] = journal_elem.get_text(strip=True)
        
        # Year
        year_elem = item.find('span', class_='listDateTime')
        if year_elem:
            pub_data['year'] = year_elem.get_text(strip=True)
        
        # DOI (from altmetric div)
        doi_elem = item.find('div', {'data-doi': True})
        if doi_elem:
            pub_data['doi'] = doi_elem.get('data-doi')
        
        return pub_data
    
    def _extract_teaching(self, soup):
        """Extract teaching activities"""
        data = {}
        teaching_activities = []
        
        teaching_list = soup.find('ul', id='RO_0000053-TeacherRole-List')
        if teaching_list:
            items = teaching_list.find_all('li', role='listitem')
            for item in items:
                activity = {}
                
                # Course name and link
                course_link = item.find('a')
                if course_link:
                    activity['course'] = course_link.get_text(strip=True)
                
                # Role (usually "Instructor")
                text = item.get_text(strip=True)
                if ',' in text:
                    parts = text.split(',')
                    if len(parts) >= 2:
                        activity['role'] = parts[1].strip().split()[0]  # Get first word after comma
                
                # Year
                year_elem = item.find('span', class_='listDateTime')
                if year_elem:
                    activity['year'] = year_elem.get_text(strip=True)
                
                teaching_activities.append(activity)
        
        data['teaching_activities_json'] = json.dumps(teaching_activities)
        data['teaching_courses_count'] = len(set(act.get('course', '') for act in teaching_activities))
        
        return data
    
    def _extract_network_links(self, soup):
        """Extract collaboration network links"""
        data = {}
        
        # Co-author network
        coauthor_link = soup.find('a', href=re.compile(r'/vis/author-network/'))
        data['coauthor_network_url'] = urljoin(self.base_url, coauthor_link.get('href')) if coauthor_link else ''
        
        # Map of science
        science_map_link = soup.find('a', href=re.compile(r'/vis/map-of-science/'))
        data['science_map_url'] = urljoin(self.base_url, science_map_link.get('href')) if science_map_link else ''
        
        return data

def scrape_expert_profile_from_url(url):
    """
    Scrape a single expert profile from URL
    """
    scraper = McMasterExpertsScraper()
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        profile_data = scraper.extract_expert_profile(response.text, url)
        return profile_data
        
    except Exception as e:
        print(f"Error scraping {url}: {str(e)}")
        return None

def scrape_expert_profile_from_file(html_file_path):
    """
    Scrape expert profile from local HTML file with UTF-8 encoding
    """
    scraper = McMasterExpertsScraper()
    
    try:
        with open(html_file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
        
        profile_data = scraper.extract_expert_profile(html_content)
        return profile_data
        
    except Exception as e:
        print(f"Error reading file {html_file_path}: {str(e)}")
        return None

def save_profiles_to_csv(profiles_data, filename='mcmaster_experts_profiles.csv'):
    """
    Save scraped profiles to CSV with UTF-8 encoding (SUMMARY DATA ONLY)
    Individual publication details are saved in separate files
    """
    if not profiles_data:
        print("No profile data to save.")
        return
    
    # Enhanced profile data with detailed publication stats
    enhanced_profiles = []
    
    for profile in profiles_data:
        enhanced_profile = profile.copy()
        
        # Add detailed publication statistics
        pub_stats = create_publication_summary_stats(profile.get('publications_json', ''))
        enhanced_profile.update(pub_stats)
        
        enhanced_profiles.append(enhanced_profile)
    
    # Define columns for CSV (SUMMARY DATA ONLY - no raw JSON data)
    columns = [
        # Basic Info
        'name', 'first_name', 'last_name', 'middle_names', 'title', 'email', 
        'primary_website', 'linkedin', 'twitter', 
        
        # Academic Info
        'overview', 
        
        # ALL Affiliations (new comprehensive fields)
        'all_affiliations',  # All positions and organizations
        'all_organizations', # All organizations only
        'primary_affiliation', 'primary_position',  # Keep for compatibility
        
        # Research Areas
        'research_areas', 
        
        # ALL Degrees (new comprehensive fields)
        'all_degrees',       # All degrees with institutions
        'all_degrees_only',  # All degrees only
        'all_institutions',  # All institutions only
        'highest_degree', 'degree_institution',  # Keep for compatibility
        
        # Publication Summary Statistics
        'total_publications', 'journal_articles_count', 'book_chapters_count', 
        'conference_papers_count', 'preprints_count', 'other_publications_count',
        'recent_publications_count', 'publications_last_5_years', 
        'latest_publication_year', 'oldest_publication_year',
        
        # Teaching & Other
        'teaching_courses_count', 'photo_url', 'coauthor_network_url', 
        'science_map_url', 'profile_url', 'scraped_date'
    ]
    
    # Create DataFrame
    df = pd.DataFrame(enhanced_profiles)
    
    # Ensure all columns exist
    for col in columns:
        if col not in df.columns:
            df[col] = ''
    
    # Reorder columns
    df = df[columns]
    
    # Save to CSV with UTF-8 encoding
    df.to_csv(filename, index=False, encoding='utf-8')
    print(f"Saved {len(profiles_data)} faculty profiles (summary) to {filename}")
    
    return df

def save_detailed_profiles_to_json(profiles_data, filename='mcmaster_experts_detailed.json'):
    """
    Save complete profile data (including JSON fields) to JSON file with UTF-8 encoding
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(profiles_data, f, indent=2, ensure_ascii=False)
    print(f"Saved detailed data for {len(profiles_data)} profiles to {filename}")

def create_safe_filename(name, profile_id=None):
    """
    Create a safe filename from a person's name
    """
    if not name:
        name = f"unknown_profile_{profile_id or 'unnamed'}"
    
    # Replace problematic characters
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', name)
    # Replace multiple spaces/dots with underscores
    safe_name = re.sub(r'[\s.]+', '_', safe_name)
    # Remove leading/trailing underscores
    safe_name = safe_name.strip('_')
    # Limit length
    safe_name = safe_name[:100]
    
    return safe_name

def save_individual_json_files(profiles_data, output_dir='faculty_profiles'):
    """
    Save each faculty profile as a separate JSON file with ALL publications
    
    Args:
        profiles_data (list): List of profile dictionaries
        output_dir (str): Directory to save individual files
    """
    import os
    
    if not profiles_data:
        print("No profile data to save.")
        return
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    saved_files = []
    name_counts = {}  # Track duplicate names
    
    for i, profile in enumerate(profiles_data):
        # Get name for filename
        name = profile.get('name', '').strip()
        first_name = profile.get('first_name', '').strip()
        last_name = profile.get('last_name', '').strip()
        
        # Create base filename
        if name:
            base_filename = create_safe_filename(name)
        elif first_name or last_name:
            base_filename = create_safe_filename(f"{first_name}_{last_name}")
        else:
            base_filename = f"profile_{i+1}"
        
        # Handle duplicate names
        if base_filename in name_counts:
            name_counts[base_filename] += 1
            filename = f"{base_filename}_{name_counts[base_filename]}.json"
        else:
            name_counts[base_filename] = 0
            filename = f"{base_filename}.json"
        
        # Full file path
        file_path = os.path.join(output_dir, filename)
        
        # Prepare profile data with full publications
        profile_with_full_data = profile.copy()
        
        # Parse publications JSON if it exists
        if 'publications_json' in profile:
            try:
                publications = json.loads(profile['publications_json'])
                profile_with_full_data['publications'] = publications
            except (json.JSONDecodeError, TypeError):
                profile_with_full_data['publications'] = {}
        
        # Add metadata
        profile_with_full_data['filename'] = filename
        profile_with_full_data['file_created'] = datetime.now().isoformat()
        
        # Save individual JSON file with UTF-8 encoding
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(profile_with_full_data, f, indent=2, ensure_ascii=False)
            
            saved_files.append(file_path)
            print(f"Saved JSON: {filename} - {profile.get('name', 'Unknown Name')}")
            
        except Exception as e:
            print(f"Error saving {filename}: {str(e)}")
    
    print(f"\n✓ Saved {len(saved_files)} individual JSON files to '{output_dir}/' directory")
    return saved_files

def save_individual_csv_files(profiles_data, output_dir='faculty_csv_profiles'):
    """
    Save each faculty member's publications as separate CSV files
    
    Args:
        profiles_data (list): List of profile dictionaries
        output_dir (str): Directory to save individual CSV files
    """
    import os
    
    if not profiles_data:
        print("No profile data to save.")
        return
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    saved_files = []
    name_counts = {}  # Track duplicate names
    
    for i, profile in enumerate(profiles_data):
        # Get name for filename
        name = profile.get('name', '').strip()
        first_name = profile.get('first_name', '').strip()
        last_name = profile.get('last_name', '').strip()
        
        # Create base filename
        if name:
            base_filename = create_safe_filename(name)
        elif first_name or last_name:
            base_filename = create_safe_filename(f"{first_name}_{last_name}")
        else:
            base_filename = f"profile_{i+1}"
        
        # Handle duplicate names
        if base_filename in name_counts:
            name_counts[base_filename] += 1
            filename = f"{base_filename}_{name_counts[base_filename]}_publications.csv"
        else:
            name_counts[base_filename] = 0
            filename = f"{base_filename}_publications.csv"
        
        # Full file path
        file_path = os.path.join(output_dir, filename)
        
        # Parse publications and create CSV
        try:
            publications_data = []
            
            if 'publications_json' in profile:
                try:
                    publications = json.loads(profile['publications_json'])
                    
                    # Flatten all publication types into one list
                    for pub_type, pub_list in publications.items():
                        for pub in pub_list:
                            pub_row = {
                                'faculty_name': profile.get('name', ''),
                                'faculty_email': profile.get('email', ''),
                                'publication_type': pub_type,
                                'title': pub.get('title', ''),
                                'journal': pub.get('journal', ''),
                                'year': pub.get('year', ''),
                                'doi': pub.get('doi', ''),
                                'url': pub.get('url', ''),
                                'file_created': datetime.now().isoformat()
                            }
                            publications_data.append(pub_row)
                    
                except (json.JSONDecodeError, TypeError):
                    # If no publications or error parsing, create empty row
                    publications_data = [{
                        'faculty_name': profile.get('name', ''),
                        'faculty_email': profile.get('email', ''),
                        'publication_type': 'none',
                        'title': 'No publications found',
                        'journal': '',
                        'year': '',
                        'doi': '',
                        'url': '',
                        'file_created': datetime.now().isoformat()
                    }]
            else:
                # No publications data
                publications_data = [{
                    'faculty_name': profile.get('name', ''),
                    'faculty_email': profile.get('email', ''),
                    'publication_type': 'none',
                    'title': 'No publications data available',
                    'journal': '',
                    'year': '',
                    'doi': '',
                    'url': '',
                    'file_created': datetime.now().isoformat()
                }]
            
            # Save to CSV
            if publications_data:
                df = pd.DataFrame(publications_data)
                df.to_csv(file_path, index=False, encoding='utf-8')
                saved_files.append(file_path)
                print(f"Saved CSV: {filename} - {len(publications_data)} publications")
            
        except Exception as e:
            print(f"Error creating CSV for {filename}: {str(e)}")
    
    print(f"\n✓ Saved {len(saved_files)} individual CSV files to '{output_dir}/' directory")
    return saved_files

def check_existing_files(json_dir, csv_dir):
    """
    Check how many individual files already exist in the directories
    
    Args:
        json_dir (str): Directory for JSON files
        csv_dir (str): Directory for CSV files
    
    Returns:
        tuple: (json_count, csv_count, existing_names)
    """
    import os
    
    json_count = 0
    csv_count = 0
    existing_names = set()
    
    # Count existing JSON files
    if os.path.exists(json_dir):
        json_files = [f for f in os.listdir(json_dir) if f.endswith('.json')]
        json_count = len(json_files)
        # Extract names from filenames
        for f in json_files:
            name = f.replace('.json', '').replace('_1', '').replace('_2', '')  # Handle duplicates
            existing_names.add(name)
    
    # Count existing CSV files
    if os.path.exists(csv_dir):
        csv_files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]
        csv_count = len(csv_files)
        # Extract names from filenames
        for f in csv_files:
            name = f.replace('_publications.csv', '').replace('_1_publications.csv', '').replace('_2_publications.csv', '')
            existing_names.add(name)
    
    return json_count, csv_count, existing_names

def scrape_from_csv_urls(csv_file_path, url_column='uni_page', delay=2, max_profiles=None,
                        save_individual_files=True, output_prefix='scraped_experts'):
    """
    Read CSV file and scrape expert profiles from URLs in specified column
    Creates individual files immediately after each successful scrape
    Skips files that already exist
    
    Args:
        csv_file_path (str): Path to CSV file containing URLs
        url_column (str): Name of column containing URLs (default: 'uni_page')
        delay (int): Delay between requests in seconds (default: 2)
        max_profiles (int): Maximum number of profiles to scrape (None for all)
        save_individual_files (bool): Whether to save individual files immediately
        output_prefix (str): Prefix for output directories and files
    
    Returns:
        tuple: (scraped_profiles, failed_urls)
    """
    import time
    import os
    
    print(f"Reading URLs from {csv_file_path}...")
    
    try:
        # Read CSV file
        df = pd.read_csv(csv_file_path)
        
        if url_column not in df.columns:
            print(f"Error: Column '{url_column}' not found in CSV file.")
            print(f"Available columns: {list(df.columns)}")
            return [], []
        
        # Get URLs and filter out empty ones
        urls = df[url_column].dropna().tolist()
        urls = [url for url in urls if url.strip()]  # Remove empty strings
        
        if max_profiles:
            urls = urls[:max_profiles]
        
        print(f"Found {len(urls)} URLs to scrape")
        
        # Create output directories if saving individual files
        individual_json_dir = None
        individual_csv_dir = None
        name_counts = {}  # Track duplicate names across all profiles
        
        if save_individual_files:
            individual_json_dir = f"{output_prefix}_individual_json"
            individual_csv_dir = f"{output_prefix}_individual_csv"
            
            os.makedirs(individual_json_dir, exist_ok=True)
            os.makedirs(individual_csv_dir, exist_ok=True)
            
            print(f"📁 Created directories:")
            print(f"  📂 {individual_json_dir}/")
            print(f"  📂 {individual_csv_dir}/")
            
            # Check for existing files
            json_count, csv_count, existing_names = check_existing_files(individual_json_dir, individual_csv_dir)
            if json_count > 0 or csv_count > 0:
                print(f"\n📋 Found existing files:")
                print(f"  📄 {json_count} JSON files")
                print(f"  📄 {csv_count} CSV files")
                print(f"  👤 {len(existing_names)} unique profiles already processed")
                print(f"  ⏭️  Will skip existing files to save time")
            print()
        
        scraped_profiles = []
        failed_urls = []
        skipped_count = 0
        
        for i, url in enumerate(urls, 1):
            print(f"Scraping {i}/{len(urls)}: {url}")
            
            profile_data = scrape_expert_profile_from_url(url)
            
            if profile_data:
                # Add original CSV row data if available
                matching_rows = df[df[url_column] == url]
                if not matching_rows.empty:
                    csv_data = matching_rows.iloc[0].to_dict()
                    # Add CSV data to profile with prefix to avoid conflicts
                    for key, value in csv_data.items():
                        if key != url_column:  # Don't duplicate the URL
                            profile_data[f'csv_{key}'] = value
                
                scraped_profiles.append(profile_data)
                name = profile_data.get('name', 'Unknown')
                print(f"  ✓ Successfully scraped: {name}")
                
                # Save individual files immediately (will skip if they exist)
                if save_individual_files:
                    save_single_profile_files(
                        profile_data, 
                        individual_json_dir, 
                        individual_csv_dir, 
                        name_counts,
                        i  # profile index for unique naming
                    )
                
            else:
                failed_urls.append(url)
                print(f"  ✗ Failed to scrape: {url}")
            
            # Be respectful with request timing
            if i < len(urls):  # Don't delay after the last request
                time.sleep(delay)
        
        print(f"\nScraping completed!")
        print(f"Successfully scraped: {len(scraped_profiles)} profiles")
        print(f"Failed: {len(failed_urls)} URLs")
        
        if save_individual_files:
            # Count final files
            final_json_count, final_csv_count, _ = check_existing_files(individual_json_dir, individual_csv_dir)
            print(f"📁 Final individual files:")
            print(f"  📂 {individual_json_dir}/ ({final_json_count} files)")
            print(f"  📂 {individual_csv_dir}/ ({final_csv_count} files)")
        
        return scraped_profiles, failed_urls
        
    except Exception as e:
        print(f"Error reading CSV file: {str(e)}")
        return [], []

def save_single_profile_files(profile_data, json_dir, csv_dir, name_counts, profile_index):
    """
    Save individual JSON and CSV files for a single profile immediately
    
    Args:
        profile_data (dict): Profile data dictionary
        json_dir (str): Directory for JSON files
        csv_dir (str): Directory for CSV files  
        name_counts (dict): Dictionary tracking duplicate names
        profile_index (int): Index of current profile for unique naming
    """
    import os
    
    # Get name for filename
    name = profile_data.get('name', '').strip()
    first_name = profile_data.get('first_name', '').strip()
    last_name = profile_data.get('last_name', '').strip()
    
    # Create base filename
    if name:
        base_filename = create_safe_filename(name)
    elif first_name or last_name:
        base_filename = create_safe_filename(f"{first_name}_{last_name}")
    else:
        base_filename = f"profile_{profile_index}"
    
    # Handle duplicate names
    if base_filename in name_counts:
        name_counts[base_filename] += 1
        json_filename = f"{base_filename}_{name_counts[base_filename]}.json"
        csv_filename = f"{base_filename}_{name_counts[base_filename]}_publications.csv"
    else:
        name_counts[base_filename] = 0
        json_filename = f"{base_filename}.json"
        csv_filename = f"{base_filename}_publications.csv"
    
    # Save JSON file
    try:
        json_path = os.path.join(json_dir, json_filename)
        
        # Prepare profile data with full publications
        profile_with_full_data = profile_data.copy()
        
        # Parse publications JSON if it exists
        if 'publications_json' in profile_data:
            try:
                publications = json.loads(profile_data['publications_json'])
                profile_with_full_data['publications'] = publications
            except (json.JSONDecodeError, TypeError):
                profile_with_full_data['publications'] = {}
        
        # Add metadata
        profile_with_full_data['filename'] = json_filename
        profile_with_full_data['file_created'] = datetime.now().isoformat()
        
        # Save JSON
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(profile_with_full_data, f, indent=2, ensure_ascii=False)
        
        print(f"    📄 Saved JSON: {json_filename}")
        
    except Exception as e:
        print(f"    ❌ Error saving JSON {json_filename}: {str(e)}")
    
    # Save CSV file
    try:
        csv_path = os.path.join(csv_dir, csv_filename)
        publications_data = []
        
        if 'publications_json' in profile_data:
            try:
                publications = json.loads(profile_data['publications_json'])
                
                # Flatten all publication types into one list
                for pub_type, pub_list in publications.items():
                    for pub in pub_list:
                        pub_row = {
                            'faculty_name': profile_data.get('name', ''),
                            'faculty_email': profile_data.get('email', ''),
                            'publication_type': pub_type,
                            'title': pub.get('title', ''),
                            'journal': pub.get('journal', ''),
                            'year': pub.get('year', ''),
                            'doi': pub.get('doi', ''),
                            'url': pub.get('url', ''),
                            'file_created': datetime.now().isoformat()
                        }
                        publications_data.append(pub_row)
                
            except (json.JSONDecodeError, TypeError):
                # If no publications or error parsing, create empty row
                publications_data = [{
                    'faculty_name': profile_data.get('name', ''),
                    'faculty_email': profile_data.get('email', ''),
                    'publication_type': 'none',
                    'title': 'No publications found',
                    'journal': '',
                    'year': '',
                    'doi': '',
                    'url': '',
                    'file_created': datetime.now().isoformat()
                }]
        else:
            # No publications data
            publications_data = [{
                'faculty_name': profile_data.get('name', ''),
                'faculty_email': profile_data.get('email', ''),
                'publication_type': 'none',
                'title': 'No publications data available',
                'journal': '',
                'year': '',
                'doi': '',
                'url': '',
                'file_created': datetime.now().isoformat()
            }]
        
        # Save to CSV
        if publications_data:
            df = pd.DataFrame(publications_data)
            df.to_csv(csv_path, index=False, encoding='utf-8')
            print(f"    📄 Saved CSV: {csv_filename} ({len(publications_data)} publications)")
        
    except Exception as e:
        print(f"    ❌ Error saving CSV {csv_filename}: {str(e)}")

def process_csv_and_save_results(csv_file_path, url_column='uni_page', 
                                output_prefix='scraped_experts', 
                                delay=2, max_profiles=None,
                                save_individual_files=True):
    """
    Complete workflow: read CSV, scrape profiles, save results
    Individual files are created immediately as profiles are scraped
    
    Args:
        csv_file_path (str): Path to input CSV file
        url_column (str): Column name containing URLs
        output_prefix (str): Prefix for output files and directories
        delay (int): Delay between requests in seconds
        max_profiles (int): Maximum profiles to scrape (None for all)
        save_individual_files (bool): Whether to save individual JSON and CSV files immediately
    """
    print(f"🚀 Starting FacultyFinder scraping process...")
    print(f"📊 Configuration:")
    print(f"  📄 Input CSV: {csv_file_path}")
    print(f"  🔗 URL Column: {url_column}")
    print(f"  ⏱️  Delay: {delay} seconds")
    print(f"  📁 Output Prefix: {output_prefix}")
    print(f"  💾 Individual Files: {'Yes' if save_individual_files else 'No'}")
    if max_profiles:
        print(f"  🔢 Max Profiles: {max_profiles}")
    print()
    
    # Scrape profiles from CSV URLs (individual files created during scraping)
    scraped_profiles, failed_urls = scrape_from_csv_urls(
        csv_file_path, url_column, delay, max_profiles, 
        save_individual_files, output_prefix
    )
    
    if scraped_profiles:
        print(f"\n=== Saving Summary Files ===")
        
        # Save main summary files
        csv_filename = f"{output_prefix}_summary.csv"
        json_filename = f"{output_prefix}_detailed.json"
        
        save_profiles_to_csv(scraped_profiles, csv_filename)
        save_detailed_profiles_to_json(scraped_profiles, json_filename)
        
        # Save failed URLs for retry
        if failed_urls:
            failed_df = pd.DataFrame({'failed_urls': failed_urls})
            failed_filename = f"{output_prefix}_failed_urls.csv"
            failed_df.to_csv(failed_filename, index=False, encoding='utf-8')
            print(f"\n⚠️  Saved {len(failed_urls)} failed URLs to {failed_filename}")
        
        # Print summary statistics
        print_scraping_summary(scraped_profiles)
        
        # Print file structure summary
        print_file_structure_summary(output_prefix, len(scraped_profiles), save_individual_files)
        
    else:
        print("❌ No profiles were successfully scraped.")

def print_file_structure_summary(output_prefix, profile_count, individual_files_saved):
    """Print summary of created files and directory structure"""
    print(f"\n=== 📁 FILE STRUCTURE SUMMARY ===")
    print(f"✅ All files saved successfully!")
    print()
    print(f"📄 Summary Files:")
    print(f"  📊 {output_prefix}_summary.csv - Faculty overview with publication stats")
    print(f"  📋 {output_prefix}_detailed.json - Complete data for all faculty")
    
    if individual_files_saved:
        print(f"\n📂 Individual Profile Files:")
        print(f"  📁 {output_prefix}_individual_json/ - {profile_count} complete JSON profiles")
        print(f"  📁 {output_prefix}_individual_csv/ - {profile_count} publication CSV files")
        
        print(f"\n📝 Example Individual Files:")
        print(f"  📄 Julia_Abelson.json - Complete profile with all data")
        print(f"  📄 Julia_Abelson_publications.csv - All publications in spreadsheet")
        print(f"  📄 Muhammad_Afzal.json - Complete profile with all data")
        print(f"  📄 Muhammad_Afzal_publications.csv - All publications in spreadsheet")
    
    print(f"\n🎯 Ready for FacultyFinder integration!")
    print(f"   • Use summary CSV for main database")
    print(f"   • Use individual files for detailed faculty pages")
    print(f"   • Use publication CSVs for search functionality")

def print_file_structure_summary(output_prefix, profile_count, individual_files_saved):
    """Print summary of created files and directory structure"""
    print(f"\n=== FILE STRUCTURE SUMMARY ===")
    print(f"📁 Main files:")
    print(f"  📄 {output_prefix}_summary.csv - Summary stats for all faculty")
    print(f"  📄 {output_prefix}_detailed.json - Complete data for all faculty")
    
    if individual_files_saved:
        print(f"\n📁 Individual files:")
        print(f"  📂 {output_prefix}_individual_json/ - {profile_count} JSON files with full data")
        print(f"  📂 {output_prefix}_individual_csv/ - {profile_count} CSV files with all publications")
        
        print(f"\n📝 Individual file examples:")
        print(f"  📄 Julia_Abelson.json - Complete profile with all publications")
        print(f"  📄 Julia_Abelson_publications.csv - All publications in spreadsheet format")
    
    print(f"\n✅ Ready for FacultyFinder database integration!")

def create_publication_summary_stats(publications_json_str):
    """
    Create detailed publication statistics from publications JSON
    """
    if not publications_json_str:
        return {
            'total_publications': 0,
            'journal_articles_count': 0,
            'book_chapters_count': 0,
            'conference_papers_count': 0,
            'preprints_count': 0,
            'other_publications_count': 0,
            'recent_publications_count': 0,
            'publications_last_5_years': 0,
            'latest_publication_year': '',
            'oldest_publication_year': ''
        }
    
    try:
        publications = json.loads(publications_json_str)
        
        # Count by type
        journal_count = len(publications.get('journal_articles', []))
        chapters_count = len(publications.get('chapters', []))
        conference_count = len(publications.get('conferences', []))
        preprints_count = len(publications.get('preprints', []))
        other_count = len(publications.get('other', []))
        
        total_count = journal_count + chapters_count + conference_count + preprints_count + other_count
        
        # Calculate year-based stats
        current_year = datetime.now().year
        all_years = []
        recent_count = 0
        
        for pub_list in publications.values():
            for pub in pub_list:
                year_str = pub.get('year', '')
                if year_str:
                    try:
                        year = int(year_str)
                        all_years.append(year)
                        if year >= current_year - 5:
                            recent_count += 1
                    except ValueError:
                        pass
        
        latest_year = str(max(all_years)) if all_years else ''
        oldest_year = str(min(all_years)) if all_years else ''
        
        return {
            'total_publications': total_count,
            'journal_articles_count': journal_count,
            'book_chapters_count': chapters_count,
            'conference_papers_count': conference_count,
            'preprints_count': preprints_count,
            'other_publications_count': other_count,
            'recent_publications_count': recent_count,
            'publications_last_5_years': recent_count,  # Same as recent for now
            'latest_publication_year': latest_year,
            'oldest_publication_year': oldest_year
        }
        
    except (json.JSONDecodeError, TypeError):
        return {
            'total_publications': 0,
            'journal_articles_count': 0,
            'book_chapters_count': 0,
            'conference_papers_count': 0,
            'preprints_count': 0,
            'other_publications_count': 0,
            'recent_publications_count': 0,
            'publications_last_5_years': 0,
            'latest_publication_year': '',
            'oldest_publication_year': ''
        }

def print_scraping_summary(profiles_data):
    """Print summary statistics of scraped data"""
    if not profiles_data:
        return
        
    print(f"\n=== SCRAPING SUMMARY ===")
    print(f"Total profiles scraped: {len(profiles_data)}")
    
    # Count by institution
    institutions = {}
    for profile in profiles_data:
        inst = profile.get('primary_affiliation', 'Unknown')
        institutions[inst] = institutions.get(inst, 0) + 1
    
    print(f"\nProfiles by institution:")
    for inst, count in sorted(institutions.items(), key=lambda x: x[1], reverse=True):
        print(f"  {inst}: {count}")
    
    # Research areas
    all_areas = []
    for profile in profiles_data:
        areas = profile.get('research_areas', '')
        if areas:
            all_areas.extend([area.strip() for area in areas.split('|')])
    
    if all_areas:
        from collections import Counter
        top_areas = Counter(all_areas).most_common(10)
        print(f"\nTop research areas:")
        for area, count in top_areas:
            print(f"  {area}: {count}")
    
    # Publication stats
    total_pubs = sum(profile.get('total_publications', 0) for profile in profiles_data)
    avg_pubs = total_pubs / len(profiles_data) if profiles_data else 0
    print(f"\nPublication statistics:")
    print(f"  Total publications: {total_pubs}")
    print(f"  Average per researcher: {avg_pubs:.1f}")

# Example usage
if __name__ == "__main__":
    # Method 1: Process CSV file with URLs (RECOMMENDED - Smart file creation)
    csv_file = "mcmaster_hei_faculty.csv"  # Replace with your CSV file path
    
    print("=== FacultyFinder Scraping - Smart File Creation ===")
    process_csv_and_save_results(
        csv_file_path=csv_file,
        url_column='uni_page',  # Your column name
        output_prefix='mcmaster_experts',
        delay=2,  # 2 seconds between requests (be respectful)
        save_individual_files=True  # Creates files immediately, skips existing ones
    )
    
