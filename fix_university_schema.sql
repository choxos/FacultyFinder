-- Fix University Schema for Google Maps Integration
-- Add missing address columns to universities table

-- Add building_number column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'universities' AND column_name = 'building_number') THEN
        ALTER TABLE universities ADD COLUMN building_number VARCHAR(50);
        RAISE NOTICE 'Added building_number column';
    ELSE
        RAISE NOTICE 'building_number column already exists';
    END IF;
END $$;

-- Add street column if it doesn't exist  
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'universities' AND column_name = 'street') THEN
        ALTER TABLE universities ADD COLUMN street VARCHAR(200);
        RAISE NOTICE 'Added street column';
    ELSE
        RAISE NOTICE 'street column already exists';
    END IF;
END $$;

-- Add postal_code column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'universities' AND column_name = 'postal_code') THEN
        ALTER TABLE universities ADD COLUMN postal_code VARCHAR(20);
        RAISE NOTICE 'Added postal_code column';
    ELSE
        RAISE NOTICE 'postal_code column already exists';
    END IF;
END $$;

-- Create index for better performance on address queries
CREATE INDEX IF NOT EXISTS idx_universities_address 
ON universities(building_number, street, postal_code);

-- Create helper function for full address generation
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

-- Show success message
SELECT 'University schema update completed successfully! ✅' AS result; 