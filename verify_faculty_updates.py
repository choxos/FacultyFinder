#!/usr/bin/env python3
"""
Faculty Database Verification Script
Verifies faculty data integrity and database updates
"""

import asyncio
import asyncpg
import json
from pathlib import Path
from datetime import datetime

class FacultyVerifier:
    def __init__(self, db_config):
        self.db_config = db_config
        self.connection = None
    
    async def connect(self):
        """Connect to database"""
        try:
            self.connection = await asyncpg.connect(**self.db_config)
            print("✅ Connected to database")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            raise
    
    async def close(self):
        """Close database connection"""
        if self.connection:
            await self.connection.close()
    
    async def verify_faculty_count(self, json_dir):
        """Verify faculty count matches between JSON files and database"""
        print("\n🔢 Verifying Faculty Count...")
        
        # Count JSON files
        json_path = Path(json_dir)
        json_files = list(json_path.glob("*.json")) if json_path.exists() else []
        json_count = len(json_files)
        
        # Count database records
        db_count = await self.connection.fetchval(
            "SELECT COUNT(*) FROM professors WHERE university_code = 'CA-ON-002'"
        )
        
        print(f"📁 JSON files: {json_count}")
        print(f"💾 Database records: {db_count}")
        
        if json_count == db_count:
            print("✅ Counts match!")
        else:
            print("⚠️ Count mismatch - some records may not have been imported")
        
        return json_count, db_count
    
    async def verify_recent_updates(self):
        """Check for recent updates in database"""
        print("\n🕒 Checking Recent Updates...")
        
        # Check for records updated in last 24 hours
        recent_updates = await self.connection.fetch("""
            SELECT professor_id, name, updated_at 
            FROM professors 
            WHERE updated_at > NOW() - INTERVAL '24 hours'
            ORDER BY updated_at DESC
            LIMIT 10
        """)
        
        if recent_updates:
            print(f"📅 Found {len(recent_updates)} recent updates:")
            for record in recent_updates:
                print(f"   • {record['professor_id']} - {record['name']} "
                      f"(updated: {record['updated_at'].strftime('%Y-%m-%d %H:%M:%S')})")
        else:
            print("⚠️ No recent updates found")
        
        return len(recent_updates)
    
    async def verify_data_integrity(self):
        """Check data integrity and completeness"""
        print("\n🔍 Checking Data Integrity...")
        
        checks = []
        
        # Check for missing required fields
        missing_names = await self.connection.fetchval(
            "SELECT COUNT(*) FROM professors WHERE name IS NULL OR name = ''"
        )
        checks.append(("Missing names", missing_names, 0))
        
        missing_emails = await self.connection.fetchval(
            "SELECT COUNT(*) FROM professors WHERE uni_email IS NULL OR uni_email = ''"
        )
        total_faculty = await self.connection.fetchval("SELECT COUNT(*) FROM professors")
        checks.append(("Missing emails", missing_emails, total_faculty * 0.1))  # Allow 10% missing
        
        missing_departments = await self.connection.fetchval(
            "SELECT COUNT(*) FROM professors WHERE department IS NULL OR department = ''"
        )
        checks.append(("Missing departments", missing_departments, total_faculty * 0.05))  # Allow 5% missing
        
        # Check for duplicate professor IDs
        duplicates = await self.connection.fetchval("""
            SELECT COUNT(*) FROM (
                SELECT professor_id, COUNT(*) 
                FROM professors 
                GROUP BY professor_id 
                HAVING COUNT(*) > 1
            ) duplicates
        """)
        checks.append(("Duplicate professor IDs", duplicates, 0))
        
        # Display results
        all_passed = True
        for check_name, actual, threshold in checks:
            if actual <= threshold:
                print(f"✅ {check_name}: {actual} (threshold: {threshold})")
            else:
                print(f"❌ {check_name}: {actual} (exceeds threshold: {threshold})")
                all_passed = False
        
        return all_passed
    
    async def verify_publication_links(self):
        """Check publication data links"""
        print("\n📚 Checking Publication Data...")
        
        # Check if publication tables exist
        pub_tables = await self.connection.fetch("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE '%publication%'
        """)
        
        if pub_tables:
            print(f"📊 Found {len(pub_tables)} publication-related tables:")
            for table in pub_tables:
                count = await self.connection.fetchval(f"SELECT COUNT(*) FROM {table['table_name']}")
                print(f"   • {table['table_name']}: {count} records")
        else:
            print("⚠️ No publication tables found")
        
        return len(pub_tables)
    
    async def generate_summary_report(self):
        """Generate comprehensive summary report"""
        print("\n📋 Faculty Database Summary Report")
        print("=" * 50)
        
        # Basic statistics
        total_faculty = await self.connection.fetchval("SELECT COUNT(*) FROM professors")
        total_universities = await self.connection.fetchval("SELECT COUNT(DISTINCT university_code) FROM professors")
        total_departments = await self.connection.fetchval("SELECT COUNT(DISTINCT department) FROM professors WHERE department IS NOT NULL")
        
        print(f"👥 Total Faculty: {total_faculty}")
        print(f"🏫 Universities: {total_universities}")
        print(f"🏢 Departments: {total_departments}")
        
        # Position breakdown
        positions = await self.connection.fetch("""
            SELECT position, COUNT(*) as count 
            FROM professors 
            WHERE position IS NOT NULL 
            GROUP BY position 
            ORDER BY count DESC
        """)
        
        if positions:
            print(f"\n📊 Faculty by Position:")
            for pos in positions[:5]:  # Top 5 positions
                print(f"   • {pos['position']}: {pos['count']}")
        
        # Recent activity
        recent_count = await self.connection.fetchval("""
            SELECT COUNT(*) FROM professors 
            WHERE updated_at > NOW() - INTERVAL '7 days'
        """)
        print(f"\n🕒 Updated in last 7 days: {recent_count}")
        
        # Data completeness
        with_emails = await self.connection.fetchval("SELECT COUNT(*) FROM professors WHERE uni_email IS NOT NULL AND uni_email != ''")
        with_orcid = await self.connection.fetchval("SELECT COUNT(*) FROM professors WHERE orcid IS NOT NULL AND orcid != ''")
        with_gscholar = await self.connection.fetchval("SELECT COUNT(*) FROM professors WHERE google_scholar IS NOT NULL AND google_scholar != ''")
        
        print(f"\n📊 Data Completeness:")
        print(f"   • With email: {with_emails}/{total_faculty} ({(with_emails/total_faculty*100):.1f}%)")
        print(f"   • With ORCID: {with_orcid}/{total_faculty} ({(with_orcid/total_faculty*100):.1f}%)")
        print(f"   • With Google Scholar: {with_gscholar}/{total_faculty} ({(with_gscholar/total_faculty*100):.1f}%)")

async def main():
    # Database configuration
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'facultyfinder_dev',
        'user': 'your_username',  # Update with your credentials
        'password': 'your_password'
    }
    
    json_directory = "data/faculties/CA/ON/CA-ON-002_mcmaster.ca/HEI/CA-ON-002_mcmaster.ca_HEI_jsons"
    
    verifier = FacultyVerifier(db_config)
    
    try:
        await verifier.connect()
        
        print("🔍 Faculty Database Verification")
        print("=" * 40)
        
        # Run verification checks
        json_count, db_count = await verifier.verify_faculty_count(json_directory)
        recent_updates = await verifier.verify_recent_updates()
        integrity_passed = await verifier.verify_data_integrity()
        pub_tables = await verifier.verify_publication_links()
        
        # Generate summary
        await verifier.generate_summary_report()
        
        # Overall status
        print("\n" + "=" * 50)
        if integrity_passed and json_count == db_count:
            print("🎉 All verification checks PASSED!")
        else:
            print("⚠️ Some verification checks FAILED - review above details")
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
    finally:
        await verifier.close()

if __name__ == "__main__":
    asyncio.run(main()) 