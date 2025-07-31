#!/usr/bin/env python3
"""
OpenCitations Citation Enhancer

This script enhances publications found by OpenAlex with citation data from OpenCitations.
It reads OpenAlex publication JSON files, extracts DOIs, and retrieves citation information.

Features:
- Reads OpenAlex publication files from data/publications/openalex/
- Extracts DOIs from publications
- Retrieves citation data from OpenCitations API
- Saves enhanced citation data to data/publications/opencitations/
- Creates citation tracking files with OpenCitations identifiers
- Handles rate limiting and error recovery

Usage:
    python opencitations_enhancer.py [options]
    
Examples:
    python opencitations_enhancer.py
    python opencitations_enhancer.py --delay 1 --max 100
"""

import json
import requests
import time
import argparse
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Optional
from urllib.parse import quote

class OpenCitationsEnhancer:
    def __init__(self, access_token: Optional[str] = None, delay: float = 1.0):
        """
        Initialize OpenCitations Enhancer
        
        Args:
            access_token: Optional OpenCitations access token
            delay: Delay between requests in seconds
        """
        self.access_token = access_token
        self.delay = delay
        self.base_url = "https://api.opencitations.net/index/v2"
        self.session = requests.Session()
        
        # Set headers
        headers = {
            'User-Agent': 'FacultyFinder-OpenCitationsEnhancer/1.0',
            'Accept': 'application/json',
        }
        
        if access_token:
            headers['Authorization'] = access_token
            
        self.session.headers.update(headers)
        
        # Statistics tracking
        self.stats = {
            'publications_processed': 0,
            'publications_with_dois': 0,
            'successful_citations': 0,
            'successful_references': 0,
            'successful_metadata': 0,
            'failed_requests': 0,
            'api_requests_made': 0,
            'rate_limit_hits': 0,
            'citation_data_saved': 0
        }
        
        # Track processed DOIs to avoid duplicates
        self.processed_dois: Set[str] = set()
    
    def load_openalex_publications(self, max_files: Optional[int] = None) -> List[Dict]:
        """
        Load OpenAlex publication files
        
        Args:
            max_files: Maximum number of files to process (None for all)
            
        Returns:
            List of publication dictionaries with metadata
        """
        publications = []
        openalex_dir = Path('data/publications/openalex')
        
        if not openalex_dir.exists():
            print(f"❌ OpenAlex directory not found: {openalex_dir}")
            return []
        
        json_files = list(openalex_dir.glob('*.json'))
        
        if max_files:
            json_files = json_files[:max_files]
        
        print(f"📁 Found {len(json_files)} OpenAlex publication files")
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    publication = json.load(f)
                    publication['_source_file'] = str(json_file)
                    publication['_openalex_id'] = json_file.stem
                    publications.append(publication)
            except Exception as e:
                print(f"⚠️  Error loading {json_file}: {str(e)}")
                continue
        
        return publications
    
    def extract_doi(self, publication: Dict) -> Optional[str]:
        """
        Extract DOI from OpenAlex publication
        
        Args:
            publication: OpenAlex publication dictionary
            
        Returns:
            DOI string or None if not found
        """
        doi = publication.get('doi', '')
        if doi:
            # Clean DOI format
            if doi.startswith('https://doi.org/'):
                doi = doi.replace('https://doi.org/', '')
            elif doi.startswith('http://dx.doi.org/'):
                doi = doi.replace('http://dx.doi.org/', '')
            return doi
        return None
    
    def get_citation_count(self, doi: str) -> Optional[int]:
        """
        Get citation count for a DOI from OpenCitations
        
        Args:
            doi: DOI string
            
        Returns:
            Citation count or None if failed
        """
        try:
            url = f"{self.base_url}/citation-count/doi:{doi}"
            response = self.session.get(url)
            self.stats['api_requests_made'] += 1
            
            if response.status_code == 429:
                self.stats['rate_limit_hits'] += 1
                print(f"⏳ Rate limit hit, waiting 30 seconds...")
                time.sleep(30)
                return self.get_citation_count(doi)  # Retry
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    return int(data[0].get('count', 0))
            
            return None
            
        except Exception as e:
            print(f"⚠️  Error getting citation count for {doi}: {str(e)}")
            return None
    
    def get_citations(self, doi: str) -> List[Dict]:
        """
        Get incoming citations for a DOI from OpenCitations
        
        Args:
            doi: DOI string
            
        Returns:
            List of citation dictionaries
        """
        try:
            url = f"{self.base_url}/citations/doi:{doi}"
            response = self.session.get(url)
            self.stats['api_requests_made'] += 1
            
            if response.status_code == 429:
                self.stats['rate_limit_hits'] += 1
                print(f"⏳ Rate limit hit, waiting 30 seconds...")
                time.sleep(30)
                return self.get_citations(doi)  # Retry
            
            if response.status_code == 200:
                data = response.json()
                return data if isinstance(data, list) else []
            
            return []
            
        except Exception as e:
            print(f"⚠️  Error getting citations for {doi}: {str(e)}")
            return []
    
    def get_references(self, doi: str) -> List[Dict]:
        """
        Get outgoing references for a DOI from OpenCitations
        
        Args:
            doi: DOI string
            
        Returns:
            List of reference dictionaries
        """
        try:
            url = f"{self.base_url}/references/doi:{doi}"
            response = self.session.get(url)
            self.stats['api_requests_made'] += 1
            
            if response.status_code == 429:
                self.stats['rate_limit_hits'] += 1
                print(f"⏳ Rate limit hit, waiting 30 seconds...")
                time.sleep(30)
                return self.get_references(doi)  # Retry
            
            if response.status_code == 200:
                data = response.json()
                return data if isinstance(data, list) else []
            
            return []
            
        except Exception as e:
            print(f"⚠️  Error getting references for {doi}: {str(e)}")
            return []
    
    def get_metadata(self, doi: str) -> Optional[Dict]:
        """
        Get metadata for a DOI from OpenCitations
        
        Args:
            doi: DOI string
            
        Returns:
            Metadata dictionary or None if failed
        """
        try:
            # Use the legacy v1 API for metadata as it's more comprehensive
            url = f"https://api.opencitations.net/index/v1/metadata/{doi}"
            response = self.session.get(url)
            self.stats['api_requests_made'] += 1
            
            if response.status_code == 429:
                self.stats['rate_limit_hits'] += 1
                print(f"⏳ Rate limit hit, waiting 30 seconds...")
                time.sleep(30)
                return self.get_metadata(doi)  # Retry
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    return data[0]
            
            return None
            
        except Exception as e:
            print(f"⚠️  Error getting metadata for {doi}: {str(e)}")
            return None
    
    def create_citation_identifier(self, citation_data: Dict) -> str:
        """
        Create a unique identifier for citation data file
        
        Args:
            citation_data: Citation data dictionary
            
        Returns:
            Unique identifier string
        """
        # Use OCI if available, otherwise create from DOI and timestamp
        oci = citation_data.get('oci', '')
        if oci:
            return oci.replace(':', '_').replace('-', '_')
        
        # Fallback: create from citing and cited DOIs
        citing = citation_data.get('citing', '').replace(':', '_').replace('/', '_').replace('.', '_')
        cited = citation_data.get('cited', '').replace(':', '_').replace('/', '_').replace('.', '_')
        
        if citing and cited:
            return f"{citing}_cites_{cited}"
        
        # Last resort: use timestamp
        return f"citation_{int(datetime.now().timestamp())}"
    
    def save_citation_data(self, doi: str, citation_data: Dict) -> bool:
        """
        Save citation data to JSON file
        
        Args:
            doi: DOI of the publication
            citation_data: Combined citation data
            
        Returns:
            True if saved successfully
        """
        try:
            # Create output directory
            output_dir = Path('data/publications/opencitations')
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Create filename from DOI
            safe_doi = doi.replace('/', '_').replace('.', '_').replace(':', '_')
            output_file = output_dir / f"{safe_doi}.json"
            
            # Add metadata
            citation_data['doi'] = doi
            citation_data['retrieved_date'] = datetime.now().isoformat()
            citation_data['source_database'] = 'OpenCitations'
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(citation_data, f, indent=2, ensure_ascii=False)
            
            self.stats['citation_data_saved'] += 1
            return True
            
        except Exception as e:
            print(f"⚠️  Error saving citation data for {doi}: {str(e)}")
            return False
    
    def enhance_publication(self, publication: Dict) -> bool:
        """
        Enhance a single publication with OpenCitations data
        
        Args:
            publication: OpenAlex publication dictionary
            
        Returns:
            True if enhancement was successful
        """
        openalex_id = publication.get('_openalex_id', 'Unknown')
        title = publication.get('title', 'Unknown Title')
        
        # Extract DOI
        doi = self.extract_doi(publication)
        if not doi:
            print(f"⚠️  No DOI found for {openalex_id}: {title}")
            return False
        
        if doi in self.processed_dois:
            print(f"⏭️  DOI already processed: {doi}")
            return True
        
        print(f"🔍 Enhancing with OpenCitations: {doi}")
        
        # Initialize citation data
        citation_data = {
            'openalex_id': openalex_id,
            'doi': doi,
            'title': title,
            'citation_count': 0,
            'citations': [],
            'references': [],
            'metadata': {}
        }
        
        enhanced = False
        
        # Get citation count
        citation_count = self.get_citation_count(doi)
        if citation_count is not None:
            citation_data['citation_count'] = citation_count
            enhanced = True
            print(f"📊 Citation count: {citation_count}")
        
        # Get incoming citations
        citations = self.get_citations(doi)
        if citations:
            citation_data['citations'] = citations
            self.stats['successful_citations'] += 1
            enhanced = True
            print(f"📥 Found {len(citations)} citing papers")
        
        # Get outgoing references
        references = self.get_references(doi)
        if references:
            citation_data['references'] = references
            self.stats['successful_references'] += 1
            enhanced = True
            print(f"📤 Found {len(references)} references")
        
        # Get metadata
        metadata = self.get_metadata(doi)
        if metadata:
            citation_data['metadata'] = metadata
            self.stats['successful_metadata'] += 1
            enhanced = True
            print(f"📋 Retrieved metadata")
        
        # Save if any data was retrieved
        if enhanced:
            if self.save_citation_data(doi, citation_data):
                self.processed_dois.add(doi)
                print(f"✅ Enhanced publication saved")
                return True
        else:
            print(f"📭 No citation data found in OpenCitations")
        
        return False
    
    def run(self, max_publications: Optional[int] = None) -> bool:
        """
        Main execution method
        
        Args:
            max_publications: Maximum number of publications to process (None for all)
            
        Returns:
            True if completed successfully
        """
        print(f"🔗 OpenCitations Citation Enhancer")
        print(f"=" * 50)
        print(f"⏱️  Delay: {self.delay}s")
        if self.access_token:
            print(f"🔑 Using access token: {self.access_token[:10]}...")
        if max_publications:
            print(f"📊 Max publications: {max_publications}")
        
        # Load OpenAlex publications
        publications = self.load_openalex_publications(max_publications)
        if not publications:
            print(f"❌ No OpenAlex publications found")
            return False
        
        print(f"📊 Processing {len(publications)} publications")
        
        # Process each publication
        start_time = datetime.now()
        
        for i, publication in enumerate(publications, 1):
            print(f"\n{'=' * 60}")
            print(f"Processing publication {i}/{len(publications)}")
            print(f"{'=' * 60}")
            
            try:
                self.enhance_publication(publication)
                self.stats['publications_processed'] += 1
                
                # Count publications with DOIs
                if self.extract_doi(publication):
                    self.stats['publications_with_dois'] += 1
                
                # Progress update
                if i % 10 == 0:
                    elapsed = datetime.now() - start_time
                    print(f"⏱️  Progress: {i}/{len(publications)} ({elapsed})")
                
                # Respect rate limits
                time.sleep(self.delay)
                
            except KeyboardInterrupt:
                print(f"\n⏹️  Enhancement interrupted by user. Processed {i-1} publications.")
                break
            except Exception as e:
                print(f"❌ Error processing publication {i}: {str(e)}")
                self.stats['failed_requests'] += 1
                continue
        
        # Final statistics
        self.print_final_statistics()
        return True
    
    def print_final_statistics(self):
        """Print final enhancement statistics"""
        print(f"\n🎉 Final Statistics:")
        print(f"=" * 50)
        print(f"Publications processed: {self.stats['publications_processed']}")
        print(f"Publications with DOIs: {self.stats['publications_with_dois']}")
        print(f"Successful citation retrievals: {self.stats['successful_citations']}")
        print(f"Successful reference retrievals: {self.stats['successful_references']}")
        print(f"Successful metadata retrievals: {self.stats['successful_metadata']}")
        print(f"Failed requests: {self.stats['failed_requests']}")
        print(f"Citation data files saved: {self.stats['citation_data_saved']}")
        print(f"API requests made: {self.stats['api_requests_made']}")
        print(f"Rate limit hits: {self.stats['rate_limit_hits']}")
        print(f"=" * 50)

def main():
    parser = argparse.ArgumentParser(description='Enhance OpenAlex publications with OpenCitations data')
    parser.add_argument('--max', type=int, help='Maximum number of publications to process')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay between requests (seconds)')
    parser.add_argument('--token', help='OpenCitations access token (optional)')
    
    args = parser.parse_args()
    
    # Initialize enhancer
    enhancer = OpenCitationsEnhancer(access_token=args.token, delay=args.delay)
    
    # Run the enhancement
    success = enhancer.run(max_publications=args.max)
    
    if success:
        print("✅ OpenCitations enhancement completed successfully!")
    else:
        print("❌ OpenCitations enhancement failed!")

if __name__ == "__main__":
    main() 