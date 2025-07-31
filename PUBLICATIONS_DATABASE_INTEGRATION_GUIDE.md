# 📚 Publications Database Integration Guide

## 🎯 **Overview**

This guide provides step-by-step instructions for transferring your comprehensive publication data (JSON files, faculty CSVs, and author information) to your PostgreSQL database on the VPS and updating your FastAPI website to display this rich academic information.

## 📁 **Current Data Structure**

Your publication data is organized as follows:

```
data/
├── publications/
│   ├── openalex/
│   │   ├── W1991178113.json          # Individual publication files
│   │   └── W1498485049.json
│   ├── pubmed/
│   │   ├── 11933791.json
│   │   └── 12113438.json
│   └── opencitations/
│       └── 10_1038_nature_12345.json
└── faculties/
    └── CA/ON/CA-ON-002_mcmaster.ca/
        ├── CA-ON-002_mcmaster.ca_faculty_info_OpenAlex.csv    # Author profiles
        └── publications/
            ├── CA-ON-002-00001_OpenAlex.csv              # Faculty publication tracking
            ├── CA-ON-002-00001_PubMed.csv                # Faculty publication tracking
            └── ...
```

## 🗄️ **Database Schema Design**

### **Step 1: Create Publication Tables**

Create a comprehensive database schema to store all publication data:

```sql
-- Enhanced Publications Table
CREATE TABLE IF NOT EXISTS publications (
    id SERIAL PRIMARY KEY,
    publication_id VARCHAR(255) UNIQUE NOT NULL,  -- OpenAlex ID, PMID, etc.
    source_system VARCHAR(50) NOT NULL,           -- 'openalex', 'pubmed', 'scopus'
    title TEXT,
    abstract TEXT,
    publication_year INTEGER,
    publication_date DATE,
    doi VARCHAR(255),
    pmid VARCHAR(50),
    pmcid VARCHAR(50),
    journal_name TEXT,
    journal_issn VARCHAR(50),
    volume VARCHAR(50),
    issue VARCHAR(50),
    pages VARCHAR(100),
    citation_count INTEGER DEFAULT 0,
    authors JSONB,                                -- Array of author objects
    affiliations JSONB,                          -- Array of affiliation objects
    topics JSONB,                                -- Research topics/subjects
    keywords JSONB,                              -- Keywords array
    mesh_terms JSONB,                            -- MeSH terms (PubMed)
    open_access JSONB,                           -- Open access information
    grants JSONB,                                -- Funding information
    raw_data JSONB,                              -- Complete original JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Faculty Publications Junction Table
CREATE TABLE IF NOT EXISTS faculty_publications (
    id SERIAL PRIMARY KEY,
    faculty_id VARCHAR(50) NOT NULL,
    publication_id VARCHAR(255) NOT NULL,
    source_system VARCHAR(50) NOT NULL,
    current_affiliation BOOLEAN DEFAULT FALSE,   -- From CSV tracking files
    author_position INTEGER,                     -- Position in author list
    is_corresponding BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (publication_id, source_system) REFERENCES publications(publication_id, source_system),
    UNIQUE(faculty_id, publication_id, source_system)
);

-- Enhanced Authors Table (from OpenAlex author info)
CREATE TABLE IF NOT EXISTS author_profiles (
    id SERIAL PRIMARY KEY,
    faculty_id VARCHAR(50) UNIQUE NOT NULL,
    openalex_id VARCHAR(255),
    orcid VARCHAR(255),
    display_name TEXT,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    works_count INTEGER DEFAULT 0,
    cited_by_count INTEGER DEFAULT 0,
    h_index INTEGER DEFAULT 0,
    i10_index INTEGER DEFAULT 0,
    mean_citedness FLOAT DEFAULT 0,
    affiliations JSONB,                          -- Affiliation history
    research_topics JSONB,                       -- Research areas and topics
    topic_distribution JSONB,                    -- Topic share percentages
    external_ids JSONB,                          -- Scopus, MAG, etc.
    publication_trends JSONB,                    -- Year-by-year publication data
    raw_profile JSONB,                           -- Complete OpenAlex profile
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (faculty_id) REFERENCES professors(professor_id)
);

-- Research Collaborations Table
CREATE TABLE IF NOT EXISTS research_collaborations (
    id SERIAL PRIMARY KEY,
    faculty1_id VARCHAR(50) NOT NULL,
    faculty2_id VARCHAR(50) NOT NULL,
    publication_id VARCHAR(255) NOT NULL,
    source_system VARCHAR(50) NOT NULL,
    collaboration_year INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (faculty1_id) REFERENCES professors(professor_id),
    FOREIGN KEY (faculty2_id) REFERENCES professors(professor_id),
    FOREIGN KEY (publication_id, source_system) REFERENCES publications(publication_id, source_system)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_publications_source_system ON publications(source_system);
CREATE INDEX IF NOT EXISTS idx_publications_year ON publications(publication_year);
CREATE INDEX IF NOT EXISTS idx_publications_citation_count ON publications(citation_count);
CREATE INDEX IF NOT EXISTS idx_faculty_publications_faculty_id ON faculty_publications(faculty_id);
CREATE INDEX IF NOT EXISTS idx_faculty_publications_source ON faculty_publications(source_system);
CREATE INDEX IF NOT EXISTS idx_author_profiles_openalex_id ON author_profiles(openalex_id);
CREATE INDEX IF NOT EXISTS idx_author_profiles_h_index ON author_profiles(h_index);

-- Full-text search indexes
CREATE INDEX IF NOT EXISTS idx_publications_title_fts ON publications USING gin(to_tsvector('english', title));
CREATE INDEX IF NOT EXISTS idx_publications_abstract_fts ON publications USING gin(to_tsvector('english', abstract));
```

### **Step 2: Deploy Schema to VPS**

Create a deployment script:

```bash
#!/bin/bash
# deploy_publications_schema.sh

echo "🗄️  Deploying Publications Database Schema..."

# Load environment variables
if [ -f .env ]; then
    source .env
else
    echo "❌ .env file not found"
    exit 1
fi

# Apply schema
echo "📊 Creating publications tables..."
psql "postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}" -f database/publications_schema.sql

if [ $? -eq 0 ]; then
    echo "✅ Publications schema deployed successfully!"
else
    echo "❌ Schema deployment failed"
    exit 1
fi

echo "🔍 Verifying tables..."
psql "postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}" -c "\dt publications*"
psql "postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}" -c "\dt faculty_publications"
psql "postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}" -c "\dt author_profiles"

echo "✅ Publications database ready!"
```

## 📥 **Data Import Scripts**

### **Step 3: Publication JSON Importer**

Create a comprehensive data importer:

```python
#!/usr/bin/env python3
"""
Publications Data Importer

Imports JSON publication files and CSV tracking files into PostgreSQL database.
Handles OpenAlex, PubMed, and other publication sources.
"""

import os
import json
import csv
import psycopg2
import psycopg2.extras
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import argparse


class PublicationsImporter:
    def __init__(self, db_config: Dict[str, str]):
        """Initialize database connection"""
        self.db_config = db_config
        self.conn = None
        self.cursor = None
        self.stats = {
            'publications_imported': 0,
            'faculty_publications_imported': 0,
            'author_profiles_imported': 0,
            'duplicates_skipped': 0,
            'errors': 0
        }

    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            print("✅ Connected to PostgreSQL database")
        except Exception as e:
            print(f"❌ Database connection failed: {str(e)}")
            raise

    def import_publication_json(self, json_file: Path, source_system: str):
        """Import a single publication JSON file"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract publication ID based on source system
            if source_system == 'openalex':
                pub_id = data.get('id', '').replace('https://openalex.org/', '')
                title = data.get('display_name', '')
                abstract = self._reconstruct_abstract(data.get('abstract_inverted_index', {}))
                doi = data.get('doi', '')
                citation_count = data.get('cited_by_count', 0)
                pub_year = data.get('publication_year')
                pub_date = data.get('publication_date')
                
            elif source_system == 'pubmed':
                pub_id = data.get('pmid', '')
                title = data.get('title', '')
                abstract = data.get('abstract', '')
                doi = data.get('doi', '')
                citation_count = 0  # PubMed doesn't provide citation counts
                pub_year = data.get('year')
                pub_date = data.get('date')
                
            else:
                print(f"⚠️  Unknown source system: {source_system}")
                return False

            if not pub_id:
                print(f"⚠️  No publication ID found in {json_file}")
                return False

            # Insert or update publication
            insert_query = """
                INSERT INTO publications (
                    publication_id, source_system, title, abstract, publication_year,
                    publication_date, doi, citation_count, authors, affiliations,
                    topics, keywords, raw_data, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) ON CONFLICT (publication_id, source_system) DO UPDATE SET
                    title = EXCLUDED.title,
                    abstract = EXCLUDED.abstract,
                    citation_count = EXCLUDED.citation_count,
                    raw_data = EXCLUDED.raw_data,
                    updated_at = EXCLUDED.updated_at
                RETURNING id;
            """
            
            # Prepare data for insertion
            authors_json = json.dumps(self._extract_authors(data, source_system))
            affiliations_json = json.dumps(self._extract_affiliations(data, source_system))
            topics_json = json.dumps(self._extract_topics(data, source_system))
            keywords_json = json.dumps(self._extract_keywords(data, source_system))
            
            self.cursor.execute(insert_query, (
                pub_id, source_system, title, abstract, pub_year,
                pub_date, doi, citation_count, authors_json, affiliations_json,
                topics_json, keywords_json, json.dumps(data), datetime.now()
            ))
            
            result = self.cursor.fetchone()
            if result:
                self.stats['publications_imported'] += 1
                return True
            else:
                self.stats['duplicates_skipped'] += 1
                return True
                
        except Exception as e:
            print(f"⚠️  Error importing {json_file}: {str(e)}")
            self.stats['errors'] += 1
            return False

    def import_faculty_publications_csv(self, csv_file: Path, source_system: str):
        """Import faculty-publication tracking CSV"""
        try:
            faculty_id = csv_file.stem.replace(f'_{source_system}', '')
            
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    # Get publication ID based on source system
                    if source_system.lower() == 'openalex':
                        pub_id = row.get('openalex_id', '').replace('https://openalex.org/', '')
                    elif source_system.lower() == 'pubmed':
                        pub_id = row.get('pmid', '')
                    else:
                        continue
                    
                    if not pub_id:
                        continue
                    
                    current_affiliation = row.get('current_affiliation', 'FALSE').upper() == 'TRUE'
                    
                    # Insert faculty-publication relationship
                    insert_query = """
                        INSERT INTO faculty_publications (
                            faculty_id, publication_id, source_system, current_affiliation
                        ) VALUES (%s, %s, %s, %s)
                        ON CONFLICT (faculty_id, publication_id, source_system) DO UPDATE SET
                            current_affiliation = EXCLUDED.current_affiliation;
                    """
                    
                    self.cursor.execute(insert_query, (faculty_id, pub_id, source_system, current_affiliation))
                    self.stats['faculty_publications_imported'] += 1
            
            return True
            
        except Exception as e:
            print(f"⚠️  Error importing faculty CSV {csv_file}: {str(e)}")
            self.stats['errors'] += 1
            return False

    def import_author_profiles_csv(self, csv_file: Path):
        """Import OpenAlex author profiles CSV"""
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    faculty_id = row.get('faculty_id', '')
                    openalex_id = row.get('openalex_id', '').replace('https://openalex.org/', '')
                    
                    if not faculty_id:
                        continue
                    
                    # Prepare structured data
                    affiliations = self._parse_pipe_separated_affiliations(row)
                    research_topics = self._parse_pipe_separated_topics(row)
                    topic_distribution = self._parse_topic_shares(row)
                    external_ids = self._parse_external_ids(row)
                    publication_trends = self._parse_publication_trends(row)
                    
                    insert_query = """
                        INSERT INTO author_profiles (
                            faculty_id, openalex_id, orcid, display_name, first_name, last_name,
                            works_count, cited_by_count, h_index, i10_index, mean_citedness,
                            affiliations, research_topics, topic_distribution, external_ids,
                            publication_trends, raw_profile, last_updated
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        ) ON CONFLICT (faculty_id) DO UPDATE SET
                            openalex_id = EXCLUDED.openalex_id,
                            works_count = EXCLUDED.works_count,
                            cited_by_count = EXCLUDED.cited_by_count,
                            h_index = EXCLUDED.h_index,
                            i10_index = EXCLUDED.i10_index,
                            affiliations = EXCLUDED.affiliations,
                            research_topics = EXCLUDED.research_topics,
                            topic_distribution = EXCLUDED.topic_distribution,
                            last_updated = EXCLUDED.last_updated;
                    """
                    
                    self.cursor.execute(insert_query, (
                        faculty_id, openalex_id, row.get('orcid', ''),
                        row.get('display_name', ''), row.get('faculty_first_name', ''),
                        row.get('faculty_last_name', ''), 
                        int(row.get('works_count', 0) or 0),
                        int(row.get('cited_by_count', 0) or 0),
                        int(row.get('h_index', 0) or 0),
                        int(row.get('i10_index', 0) or 0),
                        float(row.get('2yr_mean_citedness', 0) or 0),
                        json.dumps(affiliations), json.dumps(research_topics),
                        json.dumps(topic_distribution), json.dumps(external_ids),
                        json.dumps(publication_trends), json.dumps(dict(row)),
                        datetime.now()
                    ))
                    
                    self.stats['author_profiles_imported'] += 1
            
            return True
            
        except Exception as e:
            print(f"⚠️  Error importing author profiles {csv_file}: {str(e)}")
            self.stats['errors'] += 1
            return False

    def _reconstruct_abstract(self, inverted_index: Dict) -> str:
        """Reconstruct abstract from OpenAlex inverted index"""
        if not inverted_index:
            return ""
        
        # Create position-to-word mapping
        words = {}
        for word, positions in inverted_index.items():
            for pos in positions:
                words[pos] = word
        
        # Reconstruct in order
        max_pos = max(words.keys()) if words else 0
        return ' '.join(words.get(i, '') for i in range(max_pos + 1))

    def _extract_authors(self, data: Dict, source_system: str) -> List[Dict]:
        """Extract author information based on source system"""
        if source_system == 'openalex':
            return data.get('authorships', [])
        elif source_system == 'pubmed':
            return data.get('authors', [])
        return []

    def _extract_affiliations(self, data: Dict, source_system: str) -> List[Dict]:
        """Extract affiliation information"""
        if source_system == 'openalex':
            affiliations = []
            for authorship in data.get('authorships', []):
                affiliations.extend(authorship.get('institutions', []))
            return affiliations
        elif source_system == 'pubmed':
            return data.get('affiliations', [])
        return []

    def _extract_topics(self, data: Dict, source_system: str) -> List[Dict]:
        """Extract topic information"""
        if source_system == 'openalex':
            return data.get('topics', [])
        elif source_system == 'pubmed':
            return data.get('mesh_terms', [])
        return []

    def _extract_keywords(self, data: Dict, source_system: str) -> List[str]:
        """Extract keywords"""
        if source_system == 'openalex':
            return [kw.get('display_name', '') for kw in data.get('keywords', [])]
        elif source_system == 'pubmed':
            return data.get('keywords', [])
        return []

    def _parse_pipe_separated_affiliations(self, row: Dict) -> List[Dict]:
        """Parse pipe-separated affiliation data"""
        names = row.get('affiliations_names', '').split('|') if row.get('affiliations_names') else []
        years = row.get('affiliations_years', '').split('|') if row.get('affiliations_years') else []
        
        affiliations = []
        for i, name in enumerate(names):
            if name.strip():
                affiliation = {'name': name.strip()}
                if i < len(years) and years[i].strip():
                    affiliation['years'] = years[i].strip()
                affiliations.append(affiliation)
        
        return affiliations

    def _parse_pipe_separated_topics(self, row: Dict) -> List[Dict]:
        """Parse research topics from pipe-separated data"""
        names = row.get('top_topics_names', '').split('|') if row.get('top_topics_names') else []
        counts = row.get('top_topics_counts', '').split('|') if row.get('top_topics_counts') else []
        fields = row.get('top_topics_fields', '').split('|') if row.get('top_topics_fields') else []
        domains = row.get('top_topics_domains', '').split('|') if row.get('top_topics_domains') else []
        
        topics = []
        for i, name in enumerate(names):
            if name.strip():
                topic = {'name': name.strip()}
                if i < len(counts) and counts[i].strip():
                    topic['count'] = int(counts[i].strip() or 0)
                if i < len(fields) and fields[i].strip():
                    topic['field'] = fields[i].strip()
                if i < len(domains) and domains[i].strip():
                    topic['domain'] = domains[i].strip()
                topics.append(topic)
        
        return topics

    def _parse_topic_shares(self, row: Dict) -> List[Dict]:
        """Parse topic share distribution"""
        names = row.get('topic_share_names', '').split('|') if row.get('topic_share_names') else []
        values = row.get('topic_share_values', '').split('|') if row.get('topic_share_values') else []
        
        shares = []
        for i, name in enumerate(names):
            if name.strip():
                share = {'topic': name.strip()}
                if i < len(values) and values[i].strip():
                    share['value'] = float(values[i].strip() or 0)
                shares.append(share)
        
        return shares

    def _parse_external_ids(self, row: Dict) -> Dict:
        """Parse external identifiers"""
        return {
            'scopus_id': row.get('scopus_id', ''),
            'mag_id': row.get('mag_id', ''),
            'twitter_id': row.get('twitter_id', ''),
            'wikipedia_id': row.get('wikipedia_id', '')
        }

    def _parse_publication_trends(self, row: Dict) -> List[Dict]:
        """Parse year-by-year publication trends"""
        years = row.get('recent_years', '').split('|') if row.get('recent_years') else []
        works = row.get('recent_works_counts', '').split('|') if row.get('recent_works_counts') else []
        citations = row.get('recent_citations_counts', '').split('|') if row.get('recent_citations_counts') else []
        
        trends = []
        for i, year in enumerate(years):
            if year.strip():
                trend = {'year': int(year.strip())}
                if i < len(works) and works[i].strip():
                    trend['works_count'] = int(works[i].strip() or 0)
                if i < len(citations) and citations[i].strip():
                    trend['cited_by_count'] = int(citations[i].strip() or 0)
                trends.append(trend)
        
        return trends

    def process_all_data(self, data_dir: str = "data"):
        """Process all publication data"""
        data_path = Path(data_dir)
        
        print("🔄 Starting comprehensive data import...")
        
        # 1. Import JSON publication files
        print("\n📚 Importing JSON publication files...")
        
        # OpenAlex publications
        openalex_dir = data_path / "publications" / "openalex"
        if openalex_dir.exists():
            for json_file in openalex_dir.glob("*.json"):
                self.import_publication_json(json_file, "openalex")
        
        # PubMed publications
        pubmed_dir = data_path / "publications" / "pubmed"
        if pubmed_dir.exists():
            for json_file in pubmed_dir.glob("*.json"):
                self.import_publication_json(json_file, "pubmed")
        
        # 2. Import faculty-publication tracking CSVs
        print("\n👥 Importing faculty-publication relationships...")
        
        faculties_dir = data_path / "faculties"
        for csv_file in faculties_dir.rglob("*_OpenAlex.csv"):
            if "publications" in str(csv_file):  # Only tracking CSVs
                self.import_faculty_publications_csv(csv_file, "OpenAlex")
        
        for csv_file in faculties_dir.rglob("*_PubMed.csv"):
            if "publications" in str(csv_file):  # Only tracking CSVs
                self.import_faculty_publications_csv(csv_file, "PubMed")
        
        # 3. Import author profiles
        print("\n👨‍🎓 Importing author profiles...")
        
        for csv_file in faculties_dir.rglob("*_faculty_info_OpenAlex.csv"):
            self.import_author_profiles_csv(csv_file)
        
        # Commit all changes
        self.conn.commit()
        print("\n✅ All data imported successfully!")

    def print_stats(self):
        """Print import statistics"""
        print(f"\n📊 Import Statistics:")
        print(f"{'='*40}")
        print(f"Publications imported: {self.stats['publications_imported']}")
        print(f"Faculty-publication links: {self.stats['faculty_publications_imported']}")
        print(f"Author profiles imported: {self.stats['author_profiles_imported']}")
        print(f"Duplicates skipped: {self.stats['duplicates_skipped']}")
        print(f"Errors: {self.stats['errors']}")
        print(f"{'='*40}")

    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()


def main():
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Database configuration
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'facultyfinder'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD')
    }
    
    # Initialize and run importer
    importer = PublicationsImporter(db_config)
    
    try:
        importer.connect()
        importer.process_all_data()
        importer.print_stats()
    
    except Exception as e:
        print(f"❌ Import failed: {str(e)}")
    
    finally:
        importer.close()


if __name__ == "__main__":
    main()
```

## 🚀 **FastAPI Integration**

### **Step 4: Update FastAPI Models**

Add new Pydantic models for publication data:

```python
# In webapp/main.py, add these models

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class Publication(BaseModel):
    id: int
    publication_id: str
    source_system: str
    title: Optional[str] = None
    abstract: Optional[str] = None
    publication_year: Optional[int] = None
    publication_date: Optional[str] = None
    doi: Optional[str] = None
    journal_name: Optional[str] = None
    citation_count: int = 0
    authors: List[Dict[str, Any]] = []
    topics: List[Dict[str, Any]] = []

class AuthorProfile(BaseModel):
    faculty_id: str
    openalex_id: Optional[str] = None
    orcid: Optional[str] = None
    display_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    works_count: int = 0
    cited_by_count: int = 0
    h_index: int = 0
    i10_index: int = 0
    research_topics: List[Dict[str, Any]] = []
    affiliations: List[Dict[str, Any]] = []

class FacultyPublications(BaseModel):
    faculty_id: str
    publications: List[Publication] = []
    metrics: Dict[str, Any] = {}
    author_profile: Optional[AuthorProfile] = None

class PublicationStats(BaseModel):
    total_publications: int
    publications_by_year: Dict[int, int] = {}
    publications_by_source: Dict[str, int] = {}
    top_cited_publications: List[Publication] = []
    collaboration_stats: Dict[str, Any] = {}
```

### **Step 5: Create Publication API Endpoints**

Add comprehensive API endpoints:

```python
# Add these endpoints to webapp/main.py

@app.get("/api/v1/faculty/{faculty_id}/publications", response_model=FacultyPublications)
async def get_faculty_publications(faculty_id: str, source: Optional[str] = None, limit: int = 100):
    """Get all publications for a specific faculty member"""
    
    # Base query for faculty publications
    query = """
        SELECT p.*, fp.current_affiliation, fp.author_position
        FROM publications p
        JOIN faculty_publications fp ON p.publication_id = fp.publication_id 
                                     AND p.source_system = fp.source_system
        WHERE fp.faculty_id = %s
    """
    params = [faculty_id]
    
    # Add source filter if specified
    if source:
        query += " AND p.source_system = %s"
        params.append(source)
    
    query += " ORDER BY p.publication_year DESC, p.citation_count DESC LIMIT %s"
    params.append(limit)
    
    cursor.execute(query, params)
    publications_data = cursor.fetchall()
    
    # Get author profile
    cursor.execute("""
        SELECT * FROM author_profiles WHERE faculty_id = %s
    """, (faculty_id,))
    profile_data = cursor.fetchone()
    
    # Calculate metrics
    metrics = await calculate_faculty_metrics(faculty_id)
    
    return FacultyPublications(
        faculty_id=faculty_id,
        publications=[Publication(**dict(pub)) for pub in publications_data],
        metrics=metrics,
        author_profile=AuthorProfile(**dict(profile_data)) if profile_data else None
    )

@app.get("/api/v1/publications/search")
async def search_publications(
    q: str, 
    source: Optional[str] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    limit: int = 50
):
    """Search publications by title, abstract, or keywords"""
    
    query = """
        SELECT p.*, COUNT(*) OVER() as total_count
        FROM publications p
        WHERE (
            to_tsvector('english', p.title) @@ plainto_tsquery('english', %s)
            OR to_tsvector('english', p.abstract) @@ plainto_tsquery('english', %s)
        )
    """
    params = [q, q]
    
    if source:
        query += " AND p.source_system = %s"
        params.append(source)
    
    if year_from:
        query += " AND p.publication_year >= %s"
        params.append(year_from)
    
    if year_to:
        query += " AND p.publication_year <= %s"
        params.append(year_to)
    
    query += " ORDER BY p.citation_count DESC, p.publication_year DESC LIMIT %s"
    params.append(limit)
    
    cursor.execute(query, params)
    results = cursor.fetchall()
    
    return {
        "results": [Publication(**dict(pub)) for pub in results],
        "total_count": results[0]['total_count'] if results else 0,
        "query": q
    }

@app.get("/api/v1/publications/stats", response_model=PublicationStats)
async def get_publication_stats():
    """Get overall publication statistics"""
    
    # Total publications
    cursor.execute("SELECT COUNT(*) as total FROM publications")
    total = cursor.fetchone()['total']
    
    # Publications by year
    cursor.execute("""
        SELECT publication_year, COUNT(*) as count
        FROM publications 
        WHERE publication_year IS NOT NULL
        GROUP BY publication_year
        ORDER BY publication_year DESC
        LIMIT 10
    """)
    by_year = {row['publication_year']: row['count'] for row in cursor.fetchall()}
    
    # Publications by source
    cursor.execute("""
        SELECT source_system, COUNT(*) as count
        FROM publications
        GROUP BY source_system
    """)
    by_source = {row['source_system']: row['count'] for row in cursor.fetchall()}
    
    # Top cited publications
    cursor.execute("""
        SELECT * FROM publications
        ORDER BY citation_count DESC
        LIMIT 10
    """)
    top_cited = [Publication(**dict(pub)) for pub in cursor.fetchall()]
    
    return PublicationStats(
        total_publications=total,
        publications_by_year=by_year,
        publications_by_source=by_source,
        top_cited_publications=top_cited
    )

@app.get("/api/v1/faculty/{faculty_id}/collaborations")
async def get_faculty_collaborations(faculty_id: str, limit: int = 20):
    """Get research collaborations for a faculty member"""
    
    query = """
        SELECT 
            f2.name as collaborator_name,
            f2.professor_id as collaborator_id,
            f2.department as collaborator_department,
            COUNT(*) as collaboration_count,
            MAX(p.publication_year) as latest_collaboration
        FROM faculty_publications fp1
        JOIN faculty_publications fp2 ON fp1.publication_id = fp2.publication_id 
                                      AND fp1.source_system = fp2.source_system
        JOIN publications p ON fp1.publication_id = p.publication_id
        JOIN professors f2 ON fp2.faculty_id = f2.professor_id
        WHERE fp1.faculty_id = %s AND fp2.faculty_id != %s
        GROUP BY f2.professor_id, f2.name, f2.department
        ORDER BY collaboration_count DESC, latest_collaboration DESC
        LIMIT %s
    """
    
    cursor.execute(query, (faculty_id, faculty_id, limit))
    collaborations = cursor.fetchall()
    
    return {
        "faculty_id": faculty_id,
        "collaborations": [dict(collab) for collab in collaborations]
    }

async def calculate_faculty_metrics(faculty_id: str) -> Dict[str, Any]:
    """Calculate comprehensive metrics for a faculty member"""
    
    # Publication counts by source
    cursor.execute("""
        SELECT source_system, COUNT(*) as count
        FROM faculty_publications
        WHERE faculty_id = %s
        GROUP BY source_system
    """, (faculty_id,))
    by_source = {row['source_system']: row['count'] for row in cursor.fetchall()}
    
    # Current affiliation percentage
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN current_affiliation THEN 1 ELSE 0 END) as current
        FROM faculty_publications
        WHERE faculty_id = %s
    """, (faculty_id,))
    affiliation_data = cursor.fetchone()
    
    current_affiliation_rate = 0
    if affiliation_data['total'] > 0:
        current_affiliation_rate = (affiliation_data['current'] / affiliation_data['total']) * 100
    
    # Publication trends (last 5 years)
    cursor.execute("""
        SELECT p.publication_year, COUNT(*) as count
        FROM publications p
        JOIN faculty_publications fp ON p.publication_id = fp.publication_id
        WHERE fp.faculty_id = %s AND p.publication_year >= %s
        GROUP BY p.publication_year
        ORDER BY p.publication_year DESC
    """, (faculty_id, datetime.now().year - 5))
    
    recent_trends = {row['publication_year']: row['count'] for row in cursor.fetchall()}
    
    # Total citations
    cursor.execute("""
        SELECT SUM(p.citation_count) as total_citations
        FROM publications p
        JOIN faculty_publications fp ON p.publication_id = fp.publication_id
        WHERE fp.faculty_id = %s
    """, (faculty_id,))
    
    total_citations = cursor.fetchone()['total_citations'] or 0
    
    return {
        "publications_by_source": by_source,
        "total_publications": sum(by_source.values()),
        "current_affiliation_rate": round(current_affiliation_rate, 1),
        "recent_publication_trends": recent_trends,
        "total_citations": total_citations
    }
```

## 🎨 **Frontend Updates**

### **Step 6: Enhanced Faculty Profile Pages**

Update professor profile templates to display publication data:

```html
<!-- In webapp/templates/professor_profile.html -->

<!-- Add this section after existing content -->
<div class="row mt-4">
    <div class="col-12">
        <div class="card">
            <div class="card-header">
                <h4><i class="fas fa-chart-bar"></i> Research Metrics</h4>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-3">
                        <div class="metric-card text-center">
                            <h3 id="total-publications" class="text-primary">-</h3>
                            <p>Total Publications</p>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="metric-card text-center">
                            <h3 id="total-citations" class="text-success">-</h3>
                            <p>Total Citations</p>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="metric-card text-center">
                            <h3 id="h-index" class="text-warning">-</h3>
                            <p>H-Index</p>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="metric-card text-center">
                            <h3 id="collaboration-rate" class="text-info">-</h3>
                            <p>Current Affiliation %</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Publications List -->
<div class="row mt-4">
    <div class="col-12">
        <div class="card">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h4><i class="fas fa-file-alt"></i> Recent Publications</h4>
                <div>
                    <select id="source-filter" class="form-select form-select-sm">
                        <option value="">All Sources</option>
                        <option value="openalex">OpenAlex</option>
                        <option value="pubmed">PubMed</option>
                    </select>
                </div>
            </div>
            <div class="card-body">
                <div id="publications-list">
                    <!-- Publications will be loaded here -->
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Research Topics -->
<div class="row mt-4">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h4><i class="fas fa-tags"></i> Research Topics</h4>
            </div>
            <div class="card-body">
                <div id="research-topics">
                    <!-- Topics will be loaded here -->
                </div>
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h4><i class="fas fa-users"></i> Collaborations</h4>
            </div>
            <div class="card-body">
                <div id="collaborations-list">
                    <!-- Collaborations will be loaded here -->
                </div>
            </div>
        </div>
    </div>
</div>

<script>
// Faculty ID from template context
const facultyId = "{{ prof.sequence_id }}";

// Load faculty publication data
async function loadFacultyData() {
    try {
        // Load metrics and publications
        const response = await fetch(`/api/v1/faculty/${facultyId}/publications`);
        const data = await response.json();
        
        // Update metrics
        document.getElementById('total-publications').textContent = data.metrics.total_publications || 0;
        document.getElementById('total-citations').textContent = data.metrics.total_citations || 0;
        document.getElementById('collaboration-rate').textContent = data.metrics.current_affiliation_rate || 0;
        
        if (data.author_profile) {
            document.getElementById('h-index').textContent = data.author_profile.h_index || 0;
        }
        
        // Display publications
        displayPublications(data.publications);
        
        // Display research topics
        if (data.author_profile && data.author_profile.research_topics) {
            displayResearchTopics(data.author_profile.research_topics);
        }
        
        // Load collaborations
        loadCollaborations();
        
    } catch (error) {
        console.error('Error loading faculty data:', error);
    }
}

function displayPublications(publications) {
    const container = document.getElementById('publications-list');
    
    if (!publications || publications.length === 0) {
        container.innerHTML = '<p class="text-muted">No publications found.</p>';
        return;
    }
    
    const html = publications.slice(0, 10).map(pub => `
        <div class="publication-item border-bottom py-3">
            <h6 class="mb-2">
                ${pub.doi ? `<a href="https://doi.org/${pub.doi}" target="_blank" class="text-decoration-none">` : ''}
                ${pub.title || 'Untitled'}
                ${pub.doi ? '</a>' : ''}
                <span class="badge bg-secondary ms-2">${pub.source_system}</span>
            </h6>
            <p class="text-muted small mb-1">
                <i class="fas fa-calendar"></i> ${pub.publication_year || 'Unknown'} 
                ${pub.journal_name ? `| <i class="fas fa-book"></i> ${pub.journal_name}` : ''}
                ${pub.citation_count > 0 ? `| <i class="fas fa-quote-right"></i> ${pub.citation_count} citations` : ''}
            </p>
            ${pub.abstract ? `
                <p class="small text-secondary">${pub.abstract.substring(0, 200)}${pub.abstract.length > 200 ? '...' : ''}</p>
            ` : ''}
        </div>
    `).join('');
    
    container.innerHTML = html;
}

function displayResearchTopics(topics) {
    const container = document.getElementById('research-topics');
    
    if (!topics || topics.length === 0) {
        container.innerHTML = '<p class="text-muted">No research topics available.</p>';
        return;
    }
    
    const html = topics.slice(0, 10).map(topic => `
        <span class="badge bg-primary me-2 mb-2" title="${topic.field || ''} - ${topic.domain || ''}">
            ${topic.name} ${topic.count ? `(${topic.count})` : ''}
        </span>
    `).join('');
    
    container.innerHTML = html;
}

async function loadCollaborations() {
    try {
        const response = await fetch(`/api/v1/faculty/${facultyId}/collaborations`);
        const data = await response.json();
        
        const container = document.getElementById('collaborations-list');
        
        if (!data.collaborations || data.collaborations.length === 0) {
            container.innerHTML = '<p class="text-muted">No collaborations found.</p>';
            return;
        }
        
        const html = data.collaborations.slice(0, 5).map(collab => `
            <div class="d-flex justify-content-between align-items-center py-2 border-bottom">
                <div>
                    <strong>${collab.collaborator_name}</strong><br>
                    <small class="text-muted">${collab.collaborator_department || ''}</small>
                </div>
                <div class="text-end">
                    <span class="badge bg-info">${collab.collaboration_count} publications</span><br>
                    <small class="text-muted">Latest: ${collab.latest_collaboration || 'Unknown'}</small>
                </div>
            </div>
        `).join('');
        
        container.innerHTML = html;
        
    } catch (error) {
        console.error('Error loading collaborations:', error);
    }
}

// Source filter functionality
document.getElementById('source-filter').addEventListener('change', async function() {
    const source = this.value;
    const url = source ? `/api/v1/faculty/${facultyId}/publications?source=${source}` : `/api/v1/faculty/${facultyId}/publications`;
    
    try {
        const response = await fetch(url);
        const data = await response.json();
        displayPublications(data.publications);
    } catch (error) {
        console.error('Error filtering publications:', error);
    }
});

// Load data when page loads
document.addEventListener('DOMContentLoaded', loadFacultyData);
</script>
```

## 🚀 **Deployment Process**

### **Step 7: Complete Deployment Script**

Create a comprehensive deployment script:

```bash
#!/bin/bash
# deploy_publications_system.sh

echo "🚀 Deploying Publications System to VPS..."

# 1. Deploy database schema
echo "📊 Deploying database schema..."
./deploy_publications_schema.sh

# 2. Upload and run data import
echo "📥 Importing publication data..."
python3 publications_importer.py

# 3. Update FastAPI application
echo "🔄 Updating FastAPI application..."
# Copy updated files to VPS
scp webapp/main.py your-vps:/path/to/facultyfinder/webapp/
scp webapp/templates/professor_profile.html your-vps:/path/to/facultyfinder/webapp/templates/

# 4. Restart services
echo "♻️  Restarting services..."
ssh your-vps "sudo systemctl restart facultyfinder_fastapi"

# 5. Test the system
echo "🧪 Testing publication endpoints..."
curl -s "http://your-vps.com/api/v1/publications/stats" | python3 -m json.tool

echo "✅ Publications system deployment complete!"
```

## 📊 **Usage Examples**

### **API Endpoints**

```bash
# Get faculty publications
curl "https://your-website.com/api/v1/faculty/CA-ON-002-00001/publications"

# Search publications
curl "https://your-website.com/api/v1/publications/search?q=health+policy&year_from=2020"

# Get publication statistics
curl "https://your-website.com/api/v1/publications/stats"

# Get faculty collaborations
curl "https://your-website.com/api/v1/faculty/CA-ON-002-00001/collaborations"
```

### **Database Queries**

```sql
-- Top 10 most cited publications
SELECT title, citation_count, publication_year, source_system
FROM publications 
ORDER BY citation_count DESC 
LIMIT 10;

-- Faculty with highest H-index
SELECT display_name, h_index, works_count, cited_by_count
FROM author_profiles 
ORDER BY h_index DESC 
LIMIT 10;

-- Research collaboration network
SELECT f1.name, f2.name, COUNT(*) as collaborations
FROM faculty_publications fp1
JOIN faculty_publications fp2 ON fp1.publication_id = fp2.publication_id
JOIN professors f1 ON fp1.faculty_id = f1.professor_id
JOIN professors f2 ON fp2.faculty_id = f2.professor_id
WHERE fp1.faculty_id != fp2.faculty_id
GROUP BY f1.name, f2.name
ORDER BY collaborations DESC;
```

## 🎯 **Next Steps**

1. **Deploy database schema** using the provided SQL script
2. **Run data import** using the Python importer script  
3. **Update FastAPI application** with new endpoints and models
4. **Test the system** with a few faculty profiles
5. **Deploy to production** and update your website

This comprehensive system will transform your website into a powerful research intelligence platform with detailed publication analytics, collaboration networks, and academic impact metrics! 🌟 