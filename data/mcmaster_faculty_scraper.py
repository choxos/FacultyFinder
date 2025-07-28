import csv
import re
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urlparse

def extract_faculty_info(html_content):
    """
    Extract faculty information from McMaster HEI department HTML
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    faculty_data = []
    
    # Find all modal dialogs that contain faculty information
    modals = soup.find_all('div', class_='modal fade')
    
    for modal in modals:
        faculty_info = {}
        
        # Extract basic information from modal header
        modal_header = modal.find('div', class_='modal-header')
        if modal_header:
            # Name
            name_elem = modal_header.find('h3', class_='card-title')
            faculty_info['name'] = name_elem.get_text(strip=True) if name_elem else ''
            
            # Degree
            degree_elem = modal_header.find('p', class_='h6 mb-2')
            faculty_info['degree'] = degree_elem.get_text(strip=True) if degree_elem else ''
            
            # Position/Title
            position_elem = modal_header.find('div', class_='card-text mb-0')
            if position_elem:
                position_p = position_elem.find('p')
                faculty_info['position'] = position_p.get_text(strip=True) if position_p else ''
            
            # Faculty Type (e.g., "Faculty")
            faculty_type_elem = modal_header.find('div', class_='card-text small mt-2 mb-0')
            if faculty_type_elem:
                type_p = faculty_type_elem.find('p')
                faculty_info['faculty_type'] = type_p.get_text(strip=True) if type_p else ''
        
        # Extract contact information and links from modal body
        modal_body = modal.find('div', class_='modal-body')
        if modal_body:
            # Initialize contact fields
            faculty_info['email'] = ''
            faculty_info['website'] = ''
            faculty_info['twitter'] = ''
            faculty_info['additional_links'] = []
            
            # Find all links in the modal body
            links = modal_body.find_all('a', class_='dropdown-item')
            
            for link in links:
                href = link.get('href', '')
                link_text = link.get_text(strip=True)
                icon = link.find('i')
                
                if href.startswith('mailto:'):
                    # Extract email
                    faculty_info['email'] = href.replace('mailto:', '')
                elif icon and 'fa-twitter' in icon.get('class', []):
                    # Extract Twitter handle
                    faculty_info['twitter'] = href
                elif icon and 'fa-info-circle' in icon.get('class', []):
                    # Website/additional info
                    faculty_info['website'] = href
                else:
                    # Additional links
                    faculty_info['additional_links'].append(f"{link_text}: {href}")
        
        # Create McMaster Experts URL from email
        if faculty_info.get('email'):
            email_username = faculty_info['email'].split('@')[0]
            faculty_info['mcmaster_experts_url'] = f"https://experts.mcmaster.ca/individual/{email_username}"
        else:
            faculty_info['mcmaster_experts_url'] = ''
        
        # Convert additional links list to string
        faculty_info['additional_links'] = ' | '.join(faculty_info['additional_links'])
        
        # Only add if we have at least a name
        if faculty_info.get('name'):
            faculty_data.append(faculty_info)
    
    # If no modals found, try alternative extraction method
    if not faculty_data:
        faculty_data = extract_alternative_structure(soup)
    
    return faculty_data

def extract_alternative_structure(soup):
    """
    Alternative extraction method for different HTML structures
    """
    faculty_data = []
    
    # Look for other possible structures
    # This is a fallback in case the modal structure changes
    people_cards = soup.find_all('div', class_='col-md-6')
    
    for card in people_cards:
        faculty_info = {}
        
        # Try to extract any available information
        name_elem = card.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if name_elem:
            faculty_info['name'] = name_elem.get_text(strip=True)
            
            # Look for email in any links
            email_link = card.find('a', href=re.compile(r'mailto:'))
            if email_link:
                faculty_info['email'] = email_link.get('href').replace('mailto:', '')
                email_username = faculty_info['email'].split('@')[0]
                faculty_info['mcmaster_experts_url'] = f"https://experts.mcmaster.ca/individual/{email_username}"
            
            faculty_data.append(faculty_info)
    
    return faculty_data

def save_to_csv(faculty_data, filename='mcmaster_hei_faculty.csv'):
    """
    Save faculty data to CSV file
    """
    if not faculty_data:
        print("No faculty data found to save.")
        return
    
    # Define all possible columns
    columns = [
        'name', 'degree', 'position', 'faculty_type', 'email', 
        'mcmaster_experts_url', 'website', 'twitter', 'additional_links'
    ]
    
    # Create DataFrame
    df = pd.DataFrame(faculty_data)
    
    # Reorder columns and ensure all columns exist
    for col in columns:
        if col not in df.columns:
            df[col] = ''
    
    df = df[columns]
    
    # Save to CSV
    df.to_csv(filename, index=False, encoding='utf-8')
    print(f"Faculty data saved to {filename}")
    print(f"Total faculty members: {len(faculty_data)}")
    
    return df

def main():
    """
    Main function to process HTML and create CSV
    """
    # Read HTML file
    try:
        with open('Faculty/Epi_PH/McMaster_HEI.html', 'r', encoding='utf-8') as file:
            html_content = file.read()
    except FileNotFoundError:
        print("Please save your HTML content as 'faculty_page.html' in the same directory")
        # For demonstration, using the provided HTML snippet
        html_content = """<!DOCTYPE html>
        <!-- Your HTML content here -->
        """
        
    # Extract faculty information
    faculty_data = extract_faculty_info(html_content)
    
    # Display extracted data
    print("Extracted Faculty Information:")
    print("-" * 50)
    for i, faculty in enumerate(faculty_data, 1):
        print(f"{i}. {faculty.get('name', 'Unknown')}")
        print(f"   Degree: {faculty.get('degree', 'N/A')}")
        print(f"   Position: {faculty.get('position', 'N/A')}")
        print(f"   Email: {faculty.get('email', 'N/A')}")
        print(f"   McMaster Experts: {faculty.get('mcmaster_experts_url', 'N/A')}")
        print(f"   Website: {faculty.get('website', 'N/A')}")
        print(f"   Twitter: {faculty.get('twitter', 'N/A')}")
        if faculty.get('additional_links'):
            print(f"   Additional Links: {faculty.get('additional_links')}")
        print()
    
    # Save to CSV
    df = save_to_csv(faculty_data)
    
    return df

# Alternative function if you want to process HTML content directly
def process_html_string(html_string, output_filename='faculty_data.csv'):
    """
    Process HTML content directly from string
    """
    faculty_data = extract_faculty_info(html_string)
    df = save_to_csv(faculty_data, output_filename)
    return df

if __name__ == "__main__":
    # Example usage with the provided HTML snippet
    html_snippet = '''
    <!-- Your HTML content here -->
    '''
    
    # Process the HTML
    df = main()
    
    # Display the DataFrame
    if not df.empty:
        print("\nDataFrame Preview:")
        print(df.head())
