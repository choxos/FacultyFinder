#!/usr/bin/env python3
"""
Update University Address Schema
Adds new address columns to the universities table for Google Maps integration
"""

import os
import sys
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_db_config():
    """Load database configuration"""
    env_files = ['/var/www/ff/.env', '.env', '.env.production']
    for env_file in env_files:
        if os.path.exists(env_file):
            load_dotenv(env_file)
            break
    
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'database': os.getenv('DB_NAME')
    }

def connect_database():
    """Connect to PostgreSQL database"""
    config = load_db_config()
    try:
        conn = psycopg2.connect(**config)
        conn.autocommit = False
        logger.info("✅ Connected to PostgreSQL database")
        return conn
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return None

def update_university_schema(conn):
    """Update universities table schema with new address columns"""
    logger.info("🔧 Updating universities table schema...")
    
    try:
        cursor = conn.cursor()
        
        # Check if new columns already exist
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'universities' AND column_name IN ('building_number', 'street', 'postal_code')
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]
        
        columns_to_add = []
        if 'building_number' not in existing_columns:
            columns_to_add.append("ADD COLUMN building_number VARCHAR(50)")
        if 'street' not in existing_columns:
            columns_to_add.append("ADD COLUMN street VARCHAR(200)")
        if 'postal_code' not in existing_columns:
            columns_to_add.append("ADD COLUMN postal_code VARCHAR(20)")
        
        if columns_to_add:
            alter_sql = f"ALTER TABLE universities {', '.join(columns_to_add)}"
            cursor.execute(alter_sql)
            logger.info(f"✅ Added columns: {', '.join([col.split()[-1] for col in columns_to_add])}")
        else:
            logger.info("ℹ️ All address columns already exist")
        
        # Create index for better performance on address queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_universities_address 
            ON universities(building_number, street, postal_code)
        """)
        logger.info("✅ Created address index")
        
        conn.commit()
        return True
        
    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Schema update failed: {e}")
        return False

def import_address_data(conn):
    """Import address data from CSV into new columns"""
    logger.info("📥 Importing address data from CSV...")
    
    csv_file = 'data/university_codes.csv'
    if not os.path.exists(csv_file):
        logger.error(f"❌ CSV file not found: {csv_file}")
        return False
    
    try:
        cursor = conn.cursor()
        df = pd.read_csv(csv_file)
        
        updated_count = 0
        
        for index, row in df.iterrows():
            university_code = row.get('university_code')
            building_number = row.get('building_number')
            street = row.get('street')
            postal_code = row.get('postal_code')
            
            if pd.isna(university_code):
                continue
            
            # Update university with address data
            update_sql = """
                UPDATE universities 
                SET building_number = %s, street = %s, postal_code = %s
                WHERE university_code = %s
            """
            
            cursor.execute(update_sql, (
                building_number if not pd.isna(building_number) else None,
                street if not pd.isna(street) else None,
                postal_code if not pd.isna(postal_code) else None,
                university_code
            ))
            
            if cursor.rowcount > 0:
                updated_count += 1
                logger.info(f"🔄 Updated: {row.get('university_name', university_code)}")
        
        conn.commit()
        logger.info(f"✅ Updated {updated_count} universities with address data")
        return True
        
    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Address import failed: {e}")
        return False

def create_address_helper_function(conn):
    """Create PostgreSQL function to generate full address"""
    logger.info("🔧 Creating address helper function...")
    
    try:
        cursor = conn.cursor()
        
        # Create function to generate full address for Google Maps
        function_sql = """
        CREATE OR REPLACE FUNCTION get_full_address(
            university_name TEXT,
            building_number TEXT,
            street TEXT,
            city TEXT,
            province_state TEXT,
            postal_code TEXT,
            country TEXT
        ) RETURNS TEXT AS $$
        BEGIN
            RETURN CONCAT_WS(', ',
                university_name,
                NULLIF(CONCAT_WS(' ', building_number, street), ''),
                city,
                NULLIF(CONCAT_WS(' ', province_state, postal_code), ''),
                country
            );
        END;
        $$ LANGUAGE plpgsql;
        """
        
        cursor.execute(function_sql)
        conn.commit()
        logger.info("✅ Created address helper function")
        return True
        
    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Function creation failed: {e}")
        return False

def verify_address_update(conn):
    """Verify the address update was successful"""
    logger.info("🔍 Verifying address update...")
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check universities with complete address data
        cursor.execute("""
            SELECT 
                university_code, name, city, province_state, country,
                building_number, street, postal_code,
                get_full_address(name, building_number, street, city, province_state, postal_code, country) as full_address
            FROM universities 
            WHERE building_number IS NOT NULL AND street IS NOT NULL
            ORDER BY name
            LIMIT 5
        """)
        
        results = cursor.fetchall()
        
        logger.info("📋 Sample universities with address data:")
        for uni in results:
            logger.info(f"   • {uni['name']}")
            logger.info(f"     Address: {uni['full_address']}")
            logger.info(f"     Components: {uni['building_number']} {uni['street']}, {uni['postal_code']}")
        
        # Get total counts
        cursor.execute("SELECT COUNT(*) as total FROM universities")
        total = cursor.fetchone()['total']
        
        cursor.execute("""
            SELECT COUNT(*) as with_address 
            FROM universities 
            WHERE building_number IS NOT NULL AND street IS NOT NULL
        """)
        with_address = cursor.fetchone()['with_address']
        
        logger.info(f"📊 Address Data Summary:")
        logger.info(f"   Total Universities: {total}")
        logger.info(f"   With Address Data: {with_address}")
        logger.info(f"   Coverage: {(with_address/total*100):.1f}%")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False

def main():
    logger.info("🚀 University Address Schema Update")
    logger.info("====================================")
    
    conn = connect_database()
    if not conn:
        return False
    
    try:
        # Step 1: Update schema
        if not update_university_schema(conn):
            return False
        
        # Step 2: Import address data
        if not import_address_data(conn):
            return False
        
        # Step 3: Create helper function
        if not create_address_helper_function(conn):
            return False
        
        # Step 4: Verify update
        if not verify_address_update(conn):
            return False
        
        logger.info("🎉 University address schema update completed successfully!")
        logger.info("🗺️ Universities now have detailed address data for Google Maps integration")
        return True
        
    except Exception as e:
        logger.error(f"❌ Update failed: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
