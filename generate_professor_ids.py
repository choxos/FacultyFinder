#!/usr/bin/env python3
"""
Generate Professor IDs in the new format: UNIVERSITY_CODE-SEQUENCE
Example: CA-ON-002-00001, CA-ON-002-00002, etc.
"""

import os
import asyncpg
from dotenv import load_dotenv

# Load environment variables
env_files = ['/var/www/ff/.env', '.env', '.env.test']
for env_file in env_files:
    if os.path.exists(env_file):
        load_dotenv(env_file)
        break

def get_database_url():
    """Construct database URL from environment variables"""
    host = os.getenv('DATABASE_HOST', 'localhost')
    port = os.getenv('DATABASE_PORT', '5432')
    name = os.getenv('DATABASE_NAME', 'facultyfinder')
    user = os.getenv('DATABASE_USER', 'postgres')
    password = os.getenv('DATABASE_PASSWORD', '')
    
    return f"postgresql://{user}:{password}@{host}:{port}/{name}"

async def generate_professor_ids():
    """Generate professor IDs in the new format"""
    database_url = get_database_url()
    print(f"🔗 Connecting to database...")
    
    try:
        conn = await asyncpg.connect(database_url)
        print("✅ Database connected successfully")
        
        # Get all professors grouped by university
        query = """
            SELECT p.id, p.name, p.university_code, u.name as university_name,
                   ROW_NUMBER() OVER (PARTITION BY p.university_code ORDER BY p.id) as sequence
            FROM professors p
            LEFT JOIN universities u ON p.university_code = u.university_code
            ORDER BY p.university_code, p.id
        """
        
        professors = await conn.fetch(query)
        print(f"📊 Found {len(professors)} professors")
        
        # Generate mapping of old ID to new ID
        professor_id_mapping = {}
        university_sequences = {}
        
        for prof in professors:
            university_code = prof['university_code']
            sequence = prof['sequence']
            old_id = prof['id']
            
            if university_code:
                # Format: CA-ON-002-00001
                new_id = f"{university_code}-{sequence:05d}"
                professor_id_mapping[old_id] = new_id
                
                if university_code not in university_sequences:
                    university_sequences[university_code] = 0
                university_sequences[university_code] += 1
                
                print(f"  {prof['name']}: {old_id} → {new_id} ({prof['university_name']})")
            else:
                print(f"  ⚠️  {prof['name']}: No university code - keeping ID {old_id}")
        
        print(f"\n📈 University Sequences:")
        for uni_code, count in university_sequences.items():
            print(f"  {uni_code}: {count} professors")
        
        # Optionally add professor_id_new column to database
        print(f"\n🔧 Adding professor_id_new column to database...")
        try:
            await conn.execute("ALTER TABLE professors ADD COLUMN professor_id_new VARCHAR(50)")
            print("✅ Added professor_id_new column")
        except asyncpg.exceptions.DuplicateColumnError:
            print("ℹ️  professor_id_new column already exists")
        except Exception as e:
            print(f"⚠️  Could not add column: {e}")
        
        # Update professors with new IDs
        print(f"\n💾 Updating professors with new IDs...")
        update_count = 0
        for old_id, new_id in professor_id_mapping.items():
            await conn.execute(
                "UPDATE professors SET professor_id_new = $1 WHERE id = $2",
                new_id, old_id
            )
            update_count += 1
        
        print(f"✅ Updated {update_count} professors with new IDs")
        
        # Create index on new ID column
        try:
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_professors_new_id ON professors(professor_id_new)")
            print("✅ Created index on professor_id_new")
        except Exception as e:
            print(f"⚠️  Could not create index: {e}")
        
        await conn.close()
        print(f"\n🎉 Professor ID generation complete!")
        print(f"📋 Summary:")
        print(f"  - Total professors: {len(professors)}")
        print(f"  - Universities: {len(university_sequences)}")
        print(f"  - New IDs generated: {update_count}")
        
        return professor_id_mapping
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return {}

def save_mapping_to_file(mapping):
    """Save ID mapping to a file for reference"""
    with open('professor_id_mapping.txt', 'w') as f:
        f.write("# Professor ID Mapping (Old ID → New ID)\n")
        f.write("# Format: OLD_ID,NEW_ID\n\n")
        for old_id, new_id in mapping.items():
            f.write(f"{old_id},{new_id}\n")
    print("💾 Saved ID mapping to professor_id_mapping.txt")

async def main():
    print("🆔 Professor ID Generator")
    print("=" * 50)
    print("Generating professor IDs in format: UNIVERSITY_CODE-SEQUENCE")
    print("Example: CA-ON-002-00001, CA-ON-002-00002, etc.")
    print("=" * 50)
    
    mapping = await generate_professor_ids()
    
    if mapping:
        save_mapping_to_file(mapping)
        print(f"\n✅ Professor ID generation completed successfully!")
        print(f"📄 Check professor_id_mapping.txt for the complete mapping")
    else:
        print(f"\n❌ Professor ID generation failed")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 