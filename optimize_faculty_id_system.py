#!/usr/bin/env python3
"""
Optimize Faculty ID System
Remove faculty_id column and reconstruct it programmatically from professor_id + university_code
"""

import os
import logging
import pandas as pd
import asyncpg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

def generate_professor_id(university_code: str, sequence_id: int) -> str:
    """Generate professor_id from university_code and sequence_id"""
    return f"{university_code}-{sequence_id:05d}"

def parse_professor_id(professor_id: str) -> tuple:
    """Parse professor_id to extract university_code and sequence_id"""
    # CA-ON-002-00001 → ("CA-ON-002", 1)
    parts = professor_id.split('-')
    if len(parts) >= 4:
        university_code = '-'.join(parts[:-1])  # CA-ON-002
        sequence_id = int(parts[-1])  # 1 (from 00001)
        return university_code, sequence_id
    else:
        raise ValueError(f"Invalid professor_id format: {professor_id}")

async def optimize_faculty_id_system():
    """Remove faculty_id column and optimize the system"""
    
    logger.info("🚀 Optimizing Faculty ID System")
    logger.info("=" * 50)
    
    # Connect to database
    conn = await asyncpg.connect(DATABASE_URL)
    logger.info("✅ Connected to PostgreSQL database")
    
    try:
        # Step 1: Check current schema
        logger.info("📊 Analyzing current database structure...")
        
        # Check if faculty_id column exists
        faculty_id_exists = await conn.fetchval("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'professors' AND column_name = 'faculty_id'
        """)
        
        if not faculty_id_exists:
            logger.info("ℹ️  faculty_id column doesn't exist in database - system already optimized!")
            return
        
        # Step 2: Extract current data to understand professor_id distribution
        logger.info("📋 Extracting current faculty data...")
        
        current_data = await conn.fetch("""
            SELECT id, faculty_id, university_code, name 
            FROM professors 
            ORDER BY university_code, faculty_id
        """)
        
        if not current_data:
            logger.info("⚠️  No professor data found")
            return
            
        logger.info(f"📊 Found {len(current_data)} professors")
        
        # Step 3: Create professor_id mapping per university
        logger.info("🔄 Creating professor_id mapping per university...")
        
        university_counters = {}
        professor_mappings = []
        
        for row in current_data:
            university_code = row['university_code']
            faculty_id = row['faculty_id']
            
            # Initialize counter for this university
            if university_code not in university_counters:
                university_counters[university_code] = 0
            
            # Increment professor_id for this university
            university_counters[university_code] += 1
            new_professor_id = university_counters[university_code]
            
            # Generate professor_id to verify it matches
            reconstructed_professor_id = generate_professor_id(university_code, new_professor_id)
            
            professor_mappings.append({
                'database_id': row['id'],
                'old_faculty_id': faculty_id,
                'university_code': university_code,
                'new_professor_id': new_professor_id,
                'reconstructed_professor_id': reconstructed_professor_id,
                'name': row['name']
            })
        
        # Log the mapping
        logger.info("📋 Professor ID mapping preview:")
        for i, mapping in enumerate(professor_mappings[:5]):
            logger.info(f"  {mapping['name']}: {mapping['old_faculty_id']} → sequence_id={mapping['new_professor_id']} ({mapping['reconstructed_professor_id']})")
        
        if len(professor_mappings) > 5:
            logger.info(f"  ... and {len(professor_mappings) - 5} more")
        
        # Step 4: Add professor_id column and populate it
        logger.info("🔧 Adding professor_id column...")
        
        await conn.execute("""
            ALTER TABLE professors 
            ADD COLUMN IF NOT EXISTS professor_id INTEGER
        """)
        
        # Step 5: Update professor_id values
        logger.info("📝 Updating professor_id values...")
        
        for mapping in professor_mappings:
            await conn.execute("""
                UPDATE professors 
                SET professor_id = $1 
                WHERE id = $2
            """, mapping['new_professor_id'], mapping['database_id'])
        
        # Step 6: Add constraints to ensure professor_id is unique per university
        logger.info("🔒 Adding constraints...")
        
        await conn.execute("""
            ALTER TABLE professors 
            ADD CONSTRAINT unique_professor_id_per_university 
            UNIQUE (university_code, professor_id)
        """)
        
        # Step 7: Create index for performance
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_professors_university_professor_id 
            ON professors(university_code, professor_id)
        """)
        
        # Step 8: Remove faculty_id column
        logger.info("🗑️  Removing faculty_id column...")
        
        await conn.execute("ALTER TABLE professors DROP COLUMN faculty_id")
        
        # Step 9: Verify the optimization
        logger.info("✅ Verification...")
        
        verification_data = await conn.fetch("""
            SELECT university_code, professor_id, name 
            FROM professors 
            ORDER BY university_code, professor_id 
            LIMIT 5
        """)
        
        logger.info("📊 Sample optimized data:")
        for row in verification_data:
            reconstructed = generate_professor_id(row['university_code'], row['professor_id'])
            logger.info(f"  {row['name']}: sequence_id={row['professor_id']} → {reconstructed}")
        
        # Step 10: Create helper function test
        logger.info("🧪 Testing helper functions...")
        
        test_university_code = "CA-ON-002"
        test_sequence_id = 1
        test_professor_id = generate_professor_id(test_university_code, test_sequence_id)
        parsed_university, parsed_id = parse_professor_id(test_professor_id)
        
        logger.info(f"✅ Helper function test:")
        logger.info(f"  generate_professor_id('{test_university_code}', {test_sequence_id}) = '{test_professor_id}'")
        logger.info(f"  parse_professor_id('{test_professor_id}') = ('{parsed_university}', {parsed_id})")
        
        # Summary
        total_professors = len(professor_mappings)
        total_universities = len(university_counters)
        
        logger.info("🎉 Faculty ID system optimization complete!")
        logger.info(f"📊 Summary:")
        logger.info(f"   - Optimized {total_professors} professors across {total_universities} universities")
        logger.info(f"   - Removed faculty_id string column")
        logger.info(f"   - Added efficient professor_id integer column")
        logger.info(f"   - Added unique constraint per university")
        logger.info(f"   - Created performance index")
        
        for university_code, count in university_counters.items():
            logger.info(f"   - {university_code}: {count} professors")
            
    except Exception as e:
        logger.error(f"❌ Error during optimization: {e}")
        raise
        
    finally:
        await conn.close()
        logger.info("🔌 Database connection closed")

if __name__ == "__main__":
    import asyncio
    asyncio.run(optimize_faculty_id_system()) 