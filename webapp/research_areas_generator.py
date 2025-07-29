"""
Research Areas Generator
Extracts top 5 keywords from faculty publications to populate research areas
"""

import sqlite3
import json
import logging
from collections import Counter
from typing import List, Dict, Tuple
import re
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResearchAreasGenerator:
    """Generates research areas for faculty based on their publication keywords"""
    
    def __init__(self, db_path: str = "facultyfinder_dev.db"):
        """Initialize with database path"""
        self.db_path = db_path
        self._ensure_research_areas_column()
    
    def _ensure_research_areas_column(self):
        """Add research_areas column to professors table if it doesn't exist"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if research_areas column exists
            cursor.execute("PRAGMA table_info(professors)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'research_areas' not in columns:
                cursor.execute("ALTER TABLE professors ADD COLUMN research_areas TEXT")
                conn.commit()
                logger.info("Added research_areas column to professors table")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error ensuring research_areas column: {e}")
    
    def _clean_keyword(self, keyword: str) -> str:
        """Clean and normalize a keyword"""
        if not keyword or not isinstance(keyword, str):
            return ""
        
        # Remove common noise words and patterns
        noise_patterns = [
            r'\b(and|or|the|of|in|for|with|to|from|by|at|on)\b',
            r'\b(study|studies|analysis|research|investigation)\b',
            r'\b(data|results|conclusion|background|methods)\b',
            r'\b(patient|patients|human|humans|male|female)\b',
            r'\b(year|years|month|months|day|days)\b',
            r'\([^)]*\)',  # Remove parenthetical content
            r'\[[^\]]*\]', # Remove bracketed content
        ]
        
        cleaned = keyword.lower().strip()
        
        # Apply noise pattern removal
        for pattern in noise_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Clean up extra whitespace and punctuation
        cleaned = re.sub(r'[^\w\s-]', '', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Filter out very short or very long keywords
        if len(cleaned) < 3 or len(cleaned) > 50:
            return ""
        
        # Filter out purely numeric strings
        if cleaned.isdigit():
            return ""
        
        return cleaned
    
    def _extract_keywords_from_text(self, text: str) -> List[str]:
        """Extract potential keywords from title/abstract text"""
        if not text:
            return []
        
        # Medical/academic keyword patterns
        patterns = [
            r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',  # Title case phrases
            r'\b[a-z]+-[a-z]+\b',             # Hyphenated terms
            r'\b\w{5,}\b',                    # Longer single words
        ]
        
        keywords = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            keywords.extend(matches)
        
        # Clean and filter
        cleaned_keywords = []
        for kw in keywords:
            cleaned = self._clean_keyword(kw)
            if cleaned:
                cleaned_keywords.append(cleaned)
        
        return cleaned_keywords
    
    def _get_professor_publications_keywords(self, professor_id: int) -> List[str]:
        """Get all keywords for a professor from their publications"""
        all_keywords = []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check both publication systems
            tables_to_check = [
                ("professor_publications", "professor_id"),
                ("author_publications ap JOIN publications p ON ap.publication_id = p.id", "ap.professor_id")
            ]
            
            for table_join, id_field in tables_to_check:
                try:
                    if "JOIN" in table_join:
                        query = f"""
                        SELECT p.title, p.abstract, p.keywords 
                        FROM {table_join}
                        WHERE {id_field} = ?
                        """
                    else:
                        query = f"""
                        SELECT title, abstract, keywords 
                        FROM {table_join}
                        WHERE {id_field} = ?
                        """
                    
                    cursor.execute(query, (professor_id,))
                    rows = cursor.fetchall()
                    
                    for row in rows:
                        title, abstract, keywords_json = row
                        
                        # Extract from keywords field
                        if keywords_json:
                            try:
                                keywords_list = json.loads(keywords_json)
                                if isinstance(keywords_list, list):
                                    for kw in keywords_list:
                                        cleaned = self._clean_keyword(str(kw))
                                        if cleaned:
                                            all_keywords.append(cleaned)
                            except (json.JSONDecodeError, TypeError):
                                # Try as comma-separated string
                                if isinstance(keywords_json, str):
                                    for kw in keywords_json.split(','):
                                        cleaned = self._clean_keyword(kw.strip())
                                        if cleaned:
                                            all_keywords.append(cleaned)
                        
                        # Extract from title and abstract
                        if title:
                            title_keywords = self._extract_keywords_from_text(title)
                            all_keywords.extend(title_keywords)
                        
                        if abstract:
                            abstract_keywords = self._extract_keywords_from_text(abstract)
                            all_keywords.extend(abstract_keywords)
                
                except sqlite3.OperationalError as e:
                    # Table doesn't exist or column doesn't exist
                    logger.debug(f"Skipping {table_join}: {e}")
                    continue
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error getting keywords for professor {professor_id}: {e}")
        
        return all_keywords
    
    def get_top_research_areas(self, professor_id: int, limit: int = 5) -> List[str]:
        """Get top N research areas for a professor based on keyword frequency"""
        keywords = self._get_professor_publications_keywords(professor_id)
        
        if not keywords:
            return []
        
        # Count keyword frequency
        keyword_counter = Counter(keywords)
        
        # Get top keywords
        top_keywords = keyword_counter.most_common(limit)
        
        # Return just the keywords (not the counts)
        research_areas = [kw for kw, count in top_keywords if count >= 2]  # Minimum 2 occurrences
        
        return research_areas[:limit]
    
    def update_professor_research_areas(self, professor_id: int) -> bool:
        """Update research areas for a specific professor"""
        try:
            research_areas = self.get_top_research_areas(professor_id)
            
            if not research_areas:
                logger.info(f"No research areas found for professor {professor_id}")
                return False
            
            # Store as JSON array
            research_areas_json = json.dumps(research_areas)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE professors 
                SET research_areas = ?, updated_at = ?
                WHERE id = ?
            """, (research_areas_json, datetime.now().isoformat(), professor_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Updated research areas for professor {professor_id}: {research_areas}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating research areas for professor {professor_id}: {e}")
            return False
    
    def update_all_professors_research_areas(self, batch_size: int = 50) -> Dict[str, int]:
        """Update research areas for all professors"""
        stats = {"updated": 0, "failed": 0, "no_data": 0}
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all professor IDs
            cursor.execute("SELECT id, name FROM professors")
            professors = cursor.fetchall()
            conn.close()
            
            logger.info(f"Processing research areas for {len(professors)} professors...")
            
            for i, (prof_id, prof_name) in enumerate(professors):
                try:
                    research_areas = self.get_top_research_areas(prof_id)
                    
                    if research_areas:
                        if self.update_professor_research_areas(prof_id):
                            stats["updated"] += 1
                            logger.info(f"✅ {prof_name}: {', '.join(research_areas)}")
                        else:
                            stats["failed"] += 1
                    else:
                        stats["no_data"] += 1
                        logger.info(f"⚠️  {prof_name}: No research areas found")
                    
                    # Progress update
                    if (i + 1) % batch_size == 0:
                        logger.info(f"Processed {i + 1}/{len(professors)} professors")
                
                except Exception as e:
                    stats["failed"] += 1
                    logger.error(f"Failed to process professor {prof_id} ({prof_name}): {e}")
            
            logger.info(f"Research areas update complete: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error updating all professor research areas: {e}")
            return stats
    
    def get_professor_research_areas(self, professor_id: int) -> List[str]:
        """Get stored research areas for a professor"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT research_areas FROM professors WHERE id = ?", (professor_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row and row[0]:
                try:
                    return json.loads(row[0])
                except json.JSONDecodeError:
                    return []
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting research areas for professor {professor_id}: {e}")
            return []


# Utility functions for easy access
def generate_research_areas_for_all():
    """Convenience function to update research areas for all professors"""
    generator = ResearchAreasGenerator()
    return generator.update_all_professors_research_areas()


def generate_research_areas_for_professor(professor_id: int):
    """Convenience function to update research areas for a specific professor"""
    generator = ResearchAreasGenerator()
    return generator.update_professor_research_areas(professor_id)


if __name__ == "__main__":
    # Run research areas generation
    print("🔬 Generating research areas for all faculty members...")
    stats = generate_research_areas_for_all()
    print(f"\n✅ Research areas generation complete!")
    print(f"   Updated: {stats['updated']}")
    print(f"   Failed: {stats['failed']}")
    print(f"   No data: {stats['no_data']}") 