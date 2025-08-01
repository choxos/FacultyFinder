#!/usr/bin/env python3
"""
JSON to PostgreSQL Faculty Importer
Updates PostgreSQL database with faculty data from JSON files
"""

import json
import os
import asyncio
import asyncpg
from pathlib import Path
from typing import List, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FacultyDatabaseUpdater:
    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        self.connection = None
    
    async def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.connection = await asyncpg.connect(**self.db_config)
            logger.info("✅ Connected to PostgreSQL database")
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            raise
    
    async def close(self):
        """Close database connection"""
        if self.connection:
            await self.connection.close()
            logger.info("🔌 Database connection closed")
    
    def parse_json_faculty(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse JSON faculty data for database insertion"""
        
        # Convert lists back to semicolon-separated strings for database storage
        def list_to_semicolon(data):
            if isinstance(data, list):
                return '; '.join(data) if data else None
            return data if data else None
        
        faculty_record = {
            'faculty_id': json_data.get('faculty_id'),
            'name': json_data.get('name'),
            'first_name': json_data.get('first_name'),
            'last_name': json_data.get('last_name'),
            'middle_names': json_data.get('middle_names') or None,
            'other_name': json_data.get('other_name') or None,
            'degrees': list_to_semicolon(json_data.get('degree')),
            'all_degrees_and_inst': list_to_semicolon(json_data.get('all_degrees_and_inst')),
            'research_areas': list_to_semicolon(json_data.get('research_areas')),
            'university_code': json_data.get('university_code'),
            'university_name': json_data.get('university'),
            'department': json_data.get('department'),
            'other_departments': list_to_semicolon(json_data.get('other_depts')),
            'position': json_data.get('position'),
            'full_time': json_data.get('full_time'),
            'adjunct': json_data.get('adjunct'),
            'uni_email': json_data.get('uni_email'),
            'other_email': list_to_semicolon(json_data.get('other_email')),
            'uni_page': json_data.get('uni_page'),
            'website': json_data.get('website'),
            'phone': json_data.get('phone'),
            'fax': json_data.get('fax'),
            'twitter': json_data.get('twitter'),
            'linkedin': json_data.get('linkedin'),
            'google_scholar': json_data.get('gscholar'),
            'scopus': json_data.get('scopus'),
            'orcid': json_data.get('orcid'),
            'researchgate': json_data.get('researchgate'),
            'academicedu': json_data.get('academicedu'),
            'openalex': json_data.get('openalex'),
            'memberships': list_to_semicolon(json_data.get('membership')),
            'canada_research_chair': json_data.get('canada_research_chair') or None,
            'director': json_data.get('director') or None,
        }
        
        return faculty_record
    
    async def upsert_faculty(self, faculty_data: Dict[str, Any]) -> bool:
        """Insert or update faculty record in database"""
        try:
            query = """
                INSERT INTO professors (
                    professor_id, name, first_name, last_name, middle_names, other_name,
                    degrees, all_degrees_and_inst, research_areas, university_code,
                    department, other_departments, position, full_time, adjunct,
                    uni_email, other_email, uni_page, website, phone, fax,
                    twitter, linkedin, google_scholar, scopus, orcid, researchgate,
                    academicedu, openalex, memberships, canada_research_chair, director,
                    created_at, updated_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                    $11, $12, $13, $14, $15, $16, $17, $18, $19, $20,
                    $21, $22, $23, $24, $25, $26, $27, $28, $29, $30,
                    $31, $32, NOW(), NOW()
                )
                ON CONFLICT (professor_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    middle_names = EXCLUDED.middle_names,
                    other_name = EXCLUDED.other_name,
                    degrees = EXCLUDED.degrees,
                    all_degrees_and_inst = EXCLUDED.all_degrees_and_inst,
                    research_areas = EXCLUDED.research_areas,
                    university_code = EXCLUDED.university_code,
                    department = EXCLUDED.department,
                    other_departments = EXCLUDED.other_departments,
                    position = EXCLUDED.position,
                    full_time = EXCLUDED.full_time,
                    adjunct = EXCLUDED.adjunct,
                    uni_email = EXCLUDED.uni_email,
                    other_email = EXCLUDED.other_email,
                    uni_page = EXCLUDED.uni_page,
                    website = EXCLUDED.website,
                    phone = EXCLUDED.phone,
                    fax = EXCLUDED.fax,
                    twitter = EXCLUDED.twitter,
                    linkedin = EXCLUDED.linkedin,
                    google_scholar = EXCLUDED.google_scholar,
                    scopus = EXCLUDED.scopus,
                    orcid = EXCLUDED.orcid,
                    researchgate = EXCLUDED.researchgate,
                    academicedu = EXCLUDED.academicedu,
                    openalex = EXCLUDED.openalex,
                    memberships = EXCLUDED.memberships,
                    canada_research_chair = EXCLUDED.canada_research_chair,
                    director = EXCLUDED.director,
                    updated_at = NOW()
            """
            
            await self.connection.execute(query, *faculty_data.values())
            logger.info(f"✅ Upserted faculty: {faculty_data['faculty_id']} - {faculty_data['name']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to upsert faculty {faculty_data.get('faculty_id')}: {e}")
            return False
    
    async def process_json_files(self, json_directory: str) -> Dict[str, int]:
        """Process all JSON files in directory and update database"""
        json_dir = Path(json_directory)
        
        if not json_dir.exists():
            logger.error(f"❌ Directory not found: {json_directory}")
            return {'processed': 0, 'successful': 0, 'failed': 0}
        
        json_files = list(json_dir.glob("*.json"))
        logger.info(f"📁 Found {len(json_files)} JSON files to process")
        
        stats = {'processed': 0, 'successful': 0, 'failed': 0}
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                
                faculty_data = self.parse_json_faculty(json_data)
                success = await self.upsert_faculty(faculty_data)
                
                stats['processed'] += 1
                if success:
                    stats['successful'] += 1
                else:
                    stats['failed'] += 1
                    
            except Exception as e:
                logger.error(f"❌ Failed to process {json_file}: {e}")
                stats['processed'] += 1
                stats['failed'] += 1
        
        return stats

async def main():
    # Database configuration - update with your settings
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'facultyfinder_dev',
        'user': 'your_username',
        'password': 'your_password'
    }
    
    # JSON files directory
    json_directory = "data/faculties/CA/ON/CA-ON-002_mcmaster.ca/HEI/CA-ON-002_mcmaster.ca_HEI_jsons"
    
    updater = FacultyDatabaseUpdater(db_config)
    
    try:
        await updater.connect()
        stats = await updater.process_json_files(json_directory)
        
        logger.info(f"""
🎉 Database update completed!
📊 Statistics:
   - Files processed: {stats['processed']}
   - Successful updates: {stats['successful']}
   - Failed updates: {stats['failed']}
        """)
        
    except Exception as e:
        logger.error(f"❌ Database update failed: {e}")
    finally:
        await updater.close()

if __name__ == "__main__":
    asyncio.run(main()) 