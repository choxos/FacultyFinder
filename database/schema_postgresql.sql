-- FacultyFinder Database Schema - PostgreSQL Version
-- Compatible with PostgreSQL 12+ for VPS deployment

-- Universities table
CREATE TABLE IF NOT EXISTS universities (
    id SERIAL PRIMARY KEY,
    university_code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(500) NOT NULL,
    country VARCHAR(100) NOT NULL,
    province_state VARCHAR(100),
    city VARCHAR(200),
    address TEXT,
    building_number VARCHAR(50),
    street VARCHAR(200),
    postal_code VARCHAR(20),
    website VARCHAR(500),
    university_type VARCHAR(50),
    languages VARCHAR(200),
    year_established INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Faculty/Professors table
CREATE TABLE IF NOT EXISTS professors (
    id SERIAL PRIMARY KEY,
    professor_id VARCHAR(50), -- Generated ID like CA-ON-002-00001
    name VARCHAR(500) NOT NULL,
    first_name VARCHAR(200),
    last_name VARCHAR(200),
    middle_names VARCHAR(300),
    other_name VARCHAR(300),
    degrees TEXT,
    all_degrees_and_inst TEXT,
    all_degrees_only TEXT,
    research_areas TEXT,
    university_code VARCHAR(20), -- Reference to universities.university_code
    university VARCHAR(300), -- University name (legacy field)
    faculty VARCHAR(300),
    department VARCHAR(500),
    other_departments TEXT,
    primary_affiliation VARCHAR(500),
    memberships TEXT,
    canada_research_chair VARCHAR(500),
    director TEXT,
    position VARCHAR(200),
    primary_position VARCHAR(200),
    full_time BOOLEAN DEFAULT TRUE,  -- TRUE = full-time, FALSE = part-time
    adjunct BOOLEAN DEFAULT FALSE,   -- TRUE = adjunct faculty, FALSE = regular faculty
    uni_email VARCHAR(200),
    other_email TEXT,
    uni_page TEXT,
    website TEXT,
    misc TEXT,
    twitter VARCHAR(100),
    linkedin VARCHAR(100),
    orcid VARCHAR(100),
    googlescholar VARCHAR(200),
    researchgate VARCHAR(200),
    academicedu VARCHAR(200),
    publons VARCHAR(200),
    scopus VARCHAR(200),
    webofscience VARCHAR(200),
    phone VARCHAR(50),
    fax VARCHAR(50),
    office_location TEXT,
    cv_file_path TEXT,
    research_statement TEXT,
    teaching_statement TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Journals table for publication metrics
CREATE TABLE IF NOT EXISTS journals (
    id SERIAL PRIMARY KEY,
    name VARCHAR(1000) NOT NULL,
    issn VARCHAR(20),
    eissn VARCHAR(20),
    publisher VARCHAR(500),
    impact_factor DECIMAL(10,3),
    sjr_score DECIMAL(10,3),
    h_index INTEGER,
    country VARCHAR(100),
    subject_area TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Publications table
CREATE TABLE IF NOT EXISTS publications (
    id SERIAL PRIMARY KEY,
    pmid VARCHAR(20) UNIQUE,
    pmcid VARCHAR(20),
    doi VARCHAR(200),
    title TEXT NOT NULL,
    abstract TEXT,
    authors TEXT,
    journal_name VARCHAR(1000),
    journal_id INTEGER REFERENCES journals(id),
    publication_date DATE,
    publication_year INTEGER,
    volume VARCHAR(50),
    issue VARCHAR(50),
    pages VARCHAR(100),
    keywords TEXT,
    mesh_terms TEXT,
    publication_types TEXT,
    language VARCHAR(10) DEFAULT 'eng',
    country VARCHAR(100),
    affiliations TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Author-Publication relationship table
CREATE TABLE IF NOT EXISTS author_publications (
    id SERIAL PRIMARY KEY,
    professor_id INTEGER REFERENCES professors(id),
    publication_id INTEGER REFERENCES publications(id),
    author_order INTEGER,
    is_corresponding BOOLEAN DEFAULT FALSE,
    is_first_author BOOLEAN DEFAULT FALSE,
    is_last_author BOOLEAN DEFAULT FALSE,
    affiliation_at_time TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(professor_id, publication_id)
);

-- Collaborations table (derived from co-authorships)
CREATE TABLE IF NOT EXISTS collaborations (
    id SERIAL PRIMARY KEY,
    professor1_id INTEGER REFERENCES professors(id),
    professor2_id INTEGER REFERENCES professors(id),
    collaboration_count INTEGER DEFAULT 1,
    first_collaboration_year INTEGER,
    latest_collaboration_year INTEGER,
    shared_publications TEXT, -- JSON array of publication IDs
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(professor1_id, professor2_id)
);

-- Journal Rankings (Scimago/JCR data)
CREATE TABLE IF NOT EXISTS journal_rankings (
    id SERIAL PRIMARY KEY,
    journal_id INTEGER REFERENCES journals(id),
    year INTEGER NOT NULL,
    rank_in_category INTEGER,
    category VARCHAR(200),
    quartile VARCHAR(5), -- Q1, Q2, Q3, Q4
    percentile DECIMAL(5,2),
    impact_factor DECIMAL(10,3),
    sjr_score DECIMAL(10,3),
    cite_score DECIMAL(10,3),
    h_index INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(journal_id, year, category)
);

-- Professor degrees (normalized)
CREATE TABLE IF NOT EXISTS professor_degrees (
    id SERIAL PRIMARY KEY,
    professor_id INTEGER REFERENCES professors(id),
    degree_type VARCHAR(50) NOT NULL, -- PhD, MSc, BSc, etc.
    specialization VARCHAR(300),
    institution VARCHAR(500),
    country VARCHAR(100),
    year_obtained INTEGER,
    is_highest_degree BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Degrees reference table
CREATE TABLE IF NOT EXISTS degrees (
    id SERIAL PRIMARY KEY,
    degree_code VARCHAR(20) UNIQUE NOT NULL,
    degree_name VARCHAR(200) NOT NULL,
    degree_type VARCHAR(50), -- undergraduate, graduate, doctoral, professional
    field_of_study VARCHAR(300),
    typical_duration_years INTEGER,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Citation Networks
CREATE TABLE IF NOT EXISTS citation_networks (
    id SERIAL PRIMARY KEY,
    citing_publication_id INTEGER REFERENCES publications(id),
    cited_publication_id INTEGER REFERENCES publications(id),
    citation_context TEXT,
    citation_year INTEGER,
    is_self_citation BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(citing_publication_id, cited_publication_id)
);

-- Publication Metrics
CREATE TABLE IF NOT EXISTS publication_metrics (
    id SERIAL PRIMARY KEY,
    publication_id INTEGER REFERENCES publications(id) UNIQUE,
    citation_count INTEGER DEFAULT 0,
    download_count INTEGER DEFAULT 0,
    altmetric_score DECIMAL(10,2),
    social_media_mentions INTEGER DEFAULT 0,
    news_mentions INTEGER DEFAULT 0,
    blog_mentions INTEGER DEFAULT 0,
    policy_mentions INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Research Areas taxonomy
CREATE TABLE IF NOT EXISTS research_areas (
    id SERIAL PRIMARY KEY,
    area_code VARCHAR(20) UNIQUE NOT NULL,
    area_name VARCHAR(300) NOT NULL,
    parent_area_id INTEGER REFERENCES research_areas(id),
    level INTEGER DEFAULT 1, -- 1=broad field, 2=discipline, 3=subdiscipline
    description TEXT,
    keywords TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Professor-Research Area relationships
CREATE TABLE IF NOT EXISTS professor_research_areas (
    id SERIAL PRIMARY KEY,
    professor_id INTEGER REFERENCES professors(id),
    research_area_id INTEGER REFERENCES research_areas(id),
    expertise_level VARCHAR(20) DEFAULT 'intermediate', -- novice, intermediate, expert
    years_experience INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(professor_id, research_area_id)
);

-- Users table for authentication
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    is_verified BOOLEAN DEFAULT FALSE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    verification_token VARCHAR(255),
    reset_token VARCHAR(255),
    reset_token_expires TIMESTAMP
);

-- Crypto Payment System Tables
CREATE TABLE IF NOT EXISTS crypto_currencies (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(50) NOT NULL,
    network VARCHAR(50) NOT NULL,
    decimals INTEGER DEFAULT 18,
    contract_address VARCHAR(100),
    icon_url VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS crypto_payment_providers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    api_endpoint VARCHAR(255),
    supported_currencies TEXT, -- JSON array
    fee_percentage DECIMAL(5,2) DEFAULT 0.00,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS crypto_payments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    provider_id INTEGER REFERENCES crypto_payment_providers(id),
    currency_id INTEGER REFERENCES crypto_currencies(id),
    amount DECIMAL(20,8) NOT NULL,
    usd_amount DECIMAL(10,2),
    wallet_address VARCHAR(100) NOT NULL,
    transaction_hash VARCHAR(100) UNIQUE,
    status VARCHAR(20) DEFAULT 'pending', -- pending, confirmed, failed, expired
    purpose VARCHAR(100), -- subscription, analysis, etc.
    metadata TEXT, -- JSON for additional data
    expires_at TIMESTAMP,
    confirmed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_universities_code ON universities(university_code);
CREATE INDEX IF NOT EXISTS idx_universities_country ON universities(country);
CREATE INDEX IF NOT EXISTS idx_universities_name ON universities(name);

CREATE INDEX IF NOT EXISTS idx_professors_name ON professors(name);
CREATE INDEX IF NOT EXISTS idx_professors_university_code ON professors(university_code);
CREATE INDEX IF NOT EXISTS idx_professors_department ON professors(department);
CREATE INDEX IF NOT EXISTS idx_professors_research_areas ON professors USING GIN (to_tsvector('english', research_areas));

CREATE INDEX IF NOT EXISTS idx_publications_pmid ON publications(pmid);
CREATE INDEX IF NOT EXISTS idx_publications_doi ON publications(doi);
CREATE INDEX IF NOT EXISTS idx_publications_year ON publications(publication_year);
CREATE INDEX IF NOT EXISTS idx_publications_journal ON publications(journal_name);

CREATE INDEX IF NOT EXISTS idx_author_publications_professor ON author_publications(professor_id);
CREATE INDEX IF NOT EXISTS idx_author_publications_publication ON author_publications(publication_id);

CREATE INDEX IF NOT EXISTS idx_citation_networks_citing ON citation_networks(citing_publication_id);
CREATE INDEX IF NOT EXISTS idx_citation_networks_cited ON citation_networks(cited_publication_id);

CREATE INDEX IF NOT EXISTS idx_journal_rankings_year ON journal_rankings(year);
CREATE INDEX IF NOT EXISTS idx_journal_rankings_journal ON journal_rankings(journal_id);

CREATE INDEX IF NOT EXISTS idx_professor_degrees_professor ON professor_degrees(professor_id);
CREATE INDEX IF NOT EXISTS idx_professor_degrees_type ON professor_degrees(degree_type);

-- Full-text search indexes
CREATE INDEX IF NOT EXISTS idx_professors_fulltext ON professors USING GIN (
    to_tsvector('english', COALESCE(name, '') || ' ' || COALESCE(research_areas, '') || ' ' || COALESCE(department, ''))
);

CREATE INDEX IF NOT EXISTS idx_publications_fulltext ON publications USING GIN (
    to_tsvector('english', COALESCE(title, '') || ' ' || COALESCE(abstract, '') || ' ' || COALESCE(keywords, ''))
);

-- Partial indexes for active records
CREATE INDEX IF NOT EXISTS idx_professors_active ON professors(id) WHERE name IS NOT NULL AND university_code IS NOT NULL;

-- Insert sample data
INSERT INTO universities (university_code, name, country, province_state, city, address, website, university_type, year_established) 
VALUES 
    ('CA-ON-002', 'McMaster University', 'Canada', 'Ontario', 'Hamilton', '1280 Main Street West', 'https://www.mcmaster.ca', 'Public Research University', 1887),
    ('CA-QC-001', 'McGill University', 'Canada', 'Quebec', 'Montreal', '845 Sherbrooke Street West', 'https://www.mcgill.ca', 'Public Research University', 1821),
    ('CA-ON-001', 'University of Toronto', 'Canada', 'Ontario', 'Toronto', '27 King''s College Circle', 'https://www.utoronto.ca', 'Public Research University', 1827)
ON CONFLICT (university_code) DO NOTHING;

-- Sample crypto currencies
INSERT INTO crypto_currencies (symbol, name, network, decimals, is_active) VALUES
    ('BTC', 'Bitcoin', 'Bitcoin', 8, true),
    ('ETH', 'Ethereum', 'Ethereum', 18, true),
    ('USDC', 'USD Coin', 'Ethereum', 6, true),
    ('USDT', 'Tether', 'Ethereum', 6, true)
ON CONFLICT (symbol) DO NOTHING;

-- Sample payment providers
INSERT INTO crypto_payment_providers (name, display_name, fee_percentage, is_active) VALUES
    ('coinbase', 'Coinbase Commerce', 1.00, true),
    ('nowpayments', 'NOWPayments', 0.50, true)
ON CONFLICT (name) DO NOTHING; 