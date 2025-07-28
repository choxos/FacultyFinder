#!/usr/bin/env python3
"""
Citation Update Scheduler
Periodically updates citation data for all professors using OpenCitations API
"""

import os
import sys
import sqlite3
import time
import logging
from datetime import datetime, timedelta
from typing import List, Tuple

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from webapp.opencitations_api import CitationManager
from webapp.citation_analysis import CitationAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../logs/citation_updates.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CitationUpdateScheduler:
    """Manages scheduled citation data updates"""
    
    def __init__(self, db_path: str):
        """Initialize the scheduler"""
        self.db_path = db_path
        self.citation_manager = CitationManager(db_path)
        self.analyzer = CitationAnalyzer(db_path)
        
        # Ensure logs directory exists
        os.makedirs('../logs', exist_ok=True)
        
    def get_professors_for_update(self, limit: int = 10) -> List[Tuple[int, str, List[str]]]:
        """
        Get professors who need citation updates
        
        Args:
            limit (int): Maximum number of professors to update
            
        Returns:
            List[Tuple[int, str, List[str]]]: List of (professor_id, name, pmids)
        """
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get professors with publications but outdated citation data
            cursor.execute("""
                SELECT DISTINCT 
                    p.id,
                    p.name,
                    GROUP_CONCAT(pub.pmid) as pmids
                FROM professors p
                JOIN author_publications ap ON p.id = ap.professor_id
                JOIN publications pub ON ap.publication_pmid = pub.pmid
                LEFT JOIN publication_metrics pm ON pub.pmid = pm.pmid
                WHERE pm.last_updated IS NULL 
                   OR pm.last_updated < datetime('now', '-7 days')
                GROUP BY p.id, p.name
                ORDER BY 
                    CASE WHEN pm.last_updated IS NULL THEN 0 ELSE 1 END,
                    pm.last_updated ASC
                LIMIT ?
            """, (limit,))
            
            results = []
            for row in cursor.fetchall():
                professor_id, name, pmids_str = row
                pmids = pmids_str.split(',') if pmids_str else []
                results.append((professor_id, name, pmids))
            
            conn.close()
            return results
            
        except Exception as e:
            logger.error(f"Error getting professors for update: {str(e)}")
            return []
    
    def update_professor_citations(self, professor_id: int, name: str, pmids: List[str]) -> dict:
        """
        Update citation data for a specific professor
        
        Args:
            professor_id (int): Professor ID
            name (str): Professor name
            pmids (List[str]): List of publication PMIDs
            
        Returns:
            dict: Update results
        """
        
        logger.info(f"Updating citations for {name} (ID: {professor_id})")
        
        try:
            # Limit to first 20 publications to avoid API rate limits
            limited_pmids = pmids[:20]
            
            # Fetch and store citation data
            citations_stored = self.citation_manager.fetch_and_store_citations(limited_pmids)
            
            # Update publication metrics
            metrics_updated = self.citation_manager.update_publication_metrics(limited_pmids)
            
            # Build citation network (this processes all data in DB)
            network_updated = self.citation_manager.build_citation_network()
            
            # Calculate updated metrics
            citation_metrics = self.analyzer.calculate_citation_metrics(professor_id)
            
            logger.info(f"Updated {name}: {citations_stored} citations, {metrics_updated} metrics, {network_updated} network links")
            
            return {
                'success': True,
                'citations_stored': citations_stored,
                'metrics_updated': metrics_updated,
                'network_updated': network_updated,
                'h_index': citation_metrics.get('h_index', 0),
                'total_citations': citation_metrics.get('total_citations', 0)
            }
            
        except Exception as e:
            logger.error(f"Error updating {name}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def run_update_batch(self, batch_size: int = 5) -> dict:
        """
        Run a batch update of citation data
        
        Args:
            batch_size (int): Number of professors to update in this batch
            
        Returns:
            dict: Batch update results
        """
        
        logger.info(f"Starting citation update batch (size: {batch_size})")
        start_time = datetime.now()
        
        # Get professors to update
        professors = self.get_professors_for_update(batch_size)
        
        if not professors:
            logger.info("No professors found needing citation updates")
            return {
                'total_processed': 0,
                'successful': 0,
                'failed': 0,
                'duration': 0
            }
        
        # Process each professor
        results = {
            'total_processed': len(professors),
            'successful': 0,
            'failed': 0,
            'details': []
        }
        
        for professor_id, name, pmids in professors:
            try:
                # Add delay between professors to respect API rate limits
                time.sleep(2)
                
                result = self.update_professor_citations(professor_id, name, pmids)
                
                if result['success']:
                    results['successful'] += 1
                else:
                    results['failed'] += 1
                
                results['details'].append({
                    'professor_id': professor_id,
                    'name': name,
                    'pmids_count': len(pmids),
                    'result': result
                })
                
            except Exception as e:
                logger.error(f"Error processing {name}: {str(e)}")
                results['failed'] += 1
                
                results['details'].append({
                    'professor_id': professor_id,
                    'name': name,
                    'pmids_count': len(pmids),
                    'result': {'success': False, 'error': str(e)}
                })
        
        # Calculate duration
        end_time = datetime.now()
        results['duration'] = (end_time - start_time).total_seconds()
        
        logger.info(f"Batch update completed: {results['successful']} successful, {results['failed']} failed, {results['duration']:.1f}s")
        
        return results
    
    def run_full_update(self, max_professors: int = 50) -> dict:
        """
        Run a full citation update for multiple professors
        
        Args:
            max_professors (int): Maximum number of professors to update
            
        Returns:
            dict: Full update results
        """
        
        logger.info(f"Starting full citation update (max: {max_professors} professors)")
        
        total_results = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'batches': []
        }
        
        batch_size = 5
        batches_needed = (max_professors + batch_size - 1) // batch_size
        
        for batch_num in range(batches_needed):
            logger.info(f"Processing batch {batch_num + 1}/{batches_needed}")
            
            batch_results = self.run_update_batch(batch_size)
            
            total_results['total_processed'] += batch_results['total_processed']
            total_results['successful'] += batch_results['successful']
            total_results['failed'] += batch_results['failed']
            total_results['batches'].append(batch_results)
            
            # Break if no more professors to process
            if batch_results['total_processed'] == 0:
                break
            
            # Add delay between batches
            if batch_num < batches_needed - 1:
                logger.info("Waiting 10 seconds between batches...")
                time.sleep(10)
        
        logger.info(f"Full update completed: {total_results['successful']} successful, {total_results['failed']} failed")
        
        return total_results

def main():
    """Main function for running citation updates"""
    
    if len(sys.argv) < 2:
        print("Usage: python3 citation_update_scheduler.py <command> [options]")
        print("Commands:")
        print("  batch [size]    - Run a single batch update (default size: 5)")
        print("  full [max]      - Run full update (default max: 50)")
        print("  single <id>     - Update single professor by ID")
        return
    
    command = sys.argv[1]
    db_path = '../database/facultyfinder_dev.db'
    
    scheduler = CitationUpdateScheduler(db_path)
    
    if command == 'batch':
        batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        results = scheduler.run_update_batch(batch_size)
        print(f"Batch update results: {results}")
        
    elif command == 'full':
        max_professors = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        results = scheduler.run_full_update(max_professors)
        print(f"Full update results: {results}")
        
    elif command == 'single':
        if len(sys.argv) < 3:
            print("Error: Professor ID required for single update")
            return
        
        professor_id = int(sys.argv[2])
        
        # Get professor info
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.name, GROUP_CONCAT(pub.pmid) as pmids
            FROM professors p
            JOIN author_publications ap ON p.id = ap.professor_id
            JOIN publications pub ON ap.publication_pmid = pub.pmid
            WHERE p.id = ?
            GROUP BY p.id, p.name
        """, (professor_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            print(f"Professor with ID {professor_id} not found")
            return
        
        name, pmids_str = result
        pmids = pmids_str.split(',') if pmids_str else []
        
        update_result = scheduler.update_professor_citations(professor_id, name, pmids)
        print(f"Single update result for {name}: {update_result}")
        
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main() 