-- FacultyFinder Database Schema
-- SQLite version for development, PostgreSQL compatible for production

-- Universities table
CREATE TABLE universities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    university_code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(500) NOT NULL,
    country VARCHAR(100) NOT NULL,
    province_state VARCHAR(100),
    city VARCHAR(200),
    address TEXT,
    university_type VARCHAR(50),
    languages VARCHAR(200),
    year_established INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Faculty/Professors table
CREATE TABLE professors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(500) NOT NULL,
    first_name VARCHAR(200),
    last_name VARCHAR(200),
    middle_names VARCHAR(300),
    other_name VARCHAR(300),
    degrees TEXT,
    all_degrees_and_inst TEXT,
    all_degrees_only TEXT,
    research_areas TEXT,
    university_id INTEGER,
    faculty VARCHAR(300),
    department VARCHAR(500),
    other_departments TEXT,
    primary_affiliation VARCHAR(500),
    memberships TEXT,
    canada_research_chair VARCHAR(500),
    director TEXT,
    position VARCHAR(200),
    full_time BOOLEAN DEFAULT FALSE,
    adjunct BOOLEAN DEFAULT FALSE,
    uni_email VARCHAR(200),
    other_email TEXT,
    uni_page TEXT,
    website TEXT,
    misc TEXT,
    twitter VARCHAR(100),
    linkedin VARCHAR(100),
    phone VARCHAR(50),
    fax VARCHAR(50),
    google_scholar VARCHAR(100),
    scopus VARCHAR(100),
    web_of_science VARCHAR(100),
    orcid VARCHAR(50),
    researchgate VARCHAR(100),
    academicedu VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (university_id) REFERENCES universities(id)
);

-- Journals table (from Scimago data)
CREATE TABLE journals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id VARCHAR(50),
    title VARCHAR(1000) NOT NULL,
    type VARCHAR(50),
    issn VARCHAR(100),
    publisher VARCHAR(500),
    categories TEXT,
    areas TEXT,
    country VARCHAR(100),
    region VARCHAR(100),
    coverage VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Journal rankings by year (from Scimago)
CREATE TABLE journal_rankings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    journal_id INTEGER,
    year INTEGER,
    rank INTEGER,
    sjr REAL,
    sjr_best_quartile VARCHAR(5),
    h_index INTEGER,
    total_docs INTEGER,
    total_citations INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (journal_id) REFERENCES journals(id),
    UNIQUE(journal_id, year)
);

-- Publications table
CREATE TABLE publications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pmid VARCHAR(20) UNIQUE,
    pmcid VARCHAR(20),
    doi VARCHAR(200),
    title TEXT NOT NULL,
    abstract TEXT,
    authors TEXT,
    journal_name VARCHAR(1000),
    journal_id INTEGER,
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
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (journal_id) REFERENCES journals(id)
);

-- Author-Publication relationship table
CREATE TABLE author_publications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    professor_id INTEGER,
    publication_id INTEGER,
    author_order INTEGER,
    is_corresponding BOOLEAN DEFAULT FALSE,
    is_first_author BOOLEAN DEFAULT FALSE,
    is_last_author BOOLEAN DEFAULT FALSE,
    affiliation_at_time TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (professor_id) REFERENCES professors(id),
    FOREIGN KEY (publication_id) REFERENCES publications(id),
    UNIQUE(professor_id, publication_id)
);

-- Collaborations table (derived from co-authorships)
CREATE TABLE collaborations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    professor1_id INTEGER,
    professor2_id INTEGER,
    collaboration_count INTEGER DEFAULT 1,
    first_collaboration_year INTEGER,
    latest_collaboration_year INTEGER,
    collaboration_type VARCHAR(50), -- 'internal', 'national', 'international'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (professor1_id) REFERENCES professors(id),
    FOREIGN KEY (professor2_id) REFERENCES professors(id),
    UNIQUE(professor1_id, professor2_id)
);

-- Research areas lookup table
CREATE TABLE research_areas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(300) UNIQUE NOT NULL,
    category VARCHAR(100),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Professor-Research Area relationship table
CREATE TABLE professor_research_areas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    professor_id INTEGER,
    research_area_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (professor_id) REFERENCES professors(id),
    FOREIGN KEY (research_area_id) REFERENCES research_areas(id),
    UNIQUE(professor_id, research_area_id)
);

-- Degrees lookup table
CREATE TABLE degrees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    degree_type VARCHAR(50) UNIQUE NOT NULL,  -- PhD, MSc, MD, etc.
    full_name VARCHAR(200),                   -- Doctor of Philosophy, Master of Science, etc.
    category VARCHAR(50),                     -- Graduate, Undergraduate, Professional, etc.
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Professor-Degree relationship table
CREATE TABLE professor_degrees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    professor_id INTEGER,
    degree_id INTEGER,
    specialization TEXT,                      -- e.g., "Clinical Epidemiology and Biostatistics"
    institution VARCHAR(500),                 -- Where degree was obtained
    year_obtained INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (professor_id) REFERENCES professors(id),
    FOREIGN KEY (degree_id) REFERENCES degrees(id)
);

-- API usage tracking
CREATE TABLE api_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_ip VARCHAR(50),
    endpoint VARCHAR(200),
    parameters TEXT,
    response_time REAL,
    status_code INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI Assistant sessions
CREATE TABLE ai_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    user_ip VARCHAR(50),
    cv_text TEXT,
    ai_provider VARCHAR(50),
    api_key_provided BOOLEAN DEFAULT FALSE,
    payment_session_id VARCHAR(200),
    payment_status VARCHAR(50),
    recommendations TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User Management Tables
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(200) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'user',  -- 'user', 'admin', 'moderator'
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    profile_picture TEXT,
    institution VARCHAR(200),
    field_of_study VARCHAR(200),
    academic_level VARCHAR(50),  -- 'undergraduate', 'graduate', 'postdoc', 'faculty', 'other'
    bio TEXT,
    website VARCHAR(300),
    orcid VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    login_count INTEGER DEFAULT 0,
    preferences TEXT  -- JSON field for user preferences
);

-- User Sessions for authentication
CREATE TABLE user_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- User favorites (faculty and universities)
CREATE TABLE user_favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    item_type VARCHAR(20) NOT NULL,  -- 'professor', 'university'
    item_id INTEGER NOT NULL,
    notes TEXT,
    tags TEXT,  -- JSON array of user-defined tags
    is_private BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    UNIQUE(user_id, item_type, item_id)
);

-- User search history
CREATE TABLE user_search_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    search_type VARCHAR(20) NOT NULL,  -- 'faculty', 'university', 'general'
    search_query TEXT,
    search_filters TEXT,  -- JSON object with filters applied
    results_count INTEGER,
    clicked_results TEXT,  -- JSON array of clicked result IDs
    session_id VARCHAR(100),
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
);

-- User activity log
CREATE TABLE user_activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    activity_type VARCHAR(50) NOT NULL,  -- 'login', 'search', 'favorite_add', 'profile_view', 'payment', etc.
    activity_data TEXT,  -- JSON object with activity details
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
);

-- Payment history (enhanced from existing)
CREATE TABLE user_payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    payment_intent_id VARCHAR(255),
    stripe_payment_id VARCHAR(255),
    amount INTEGER NOT NULL,  -- in cents
    currency VARCHAR(3) DEFAULT 'CAD',
    payment_method VARCHAR(50),
    service_type VARCHAR(50),  -- 'ai_analysis', 'manual_review', 'subscription'
    service_details TEXT,  -- JSON with service-specific data
    status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'completed', 'failed', 'refunded'
    receipt_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
);

-- User saved searches
CREATE TABLE user_saved_searches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    search_name VARCHAR(100) NOT NULL,
    search_type VARCHAR(20) NOT NULL,
    search_parameters TEXT NOT NULL,  -- JSON object with search params
    notification_enabled BOOLEAN DEFAULT FALSE,
    last_run TIMESTAMP,
    results_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- User collections (groups of favorites)
CREATE TABLE user_collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    color VARCHAR(7),  -- hex color code
    icon VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- Collection items (linking favorites to collections)
CREATE TABLE user_collection_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection_id INTEGER NOT NULL,
    favorite_id INTEGER NOT NULL,
    sort_order INTEGER DEFAULT 0,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (collection_id) REFERENCES user_collections (id) ON DELETE CASCADE,
    FOREIGN KEY (favorite_id) REFERENCES user_favorites (id) ON DELETE CASCADE,
    UNIQUE(collection_id, favorite_id)
);

-- Admin dashboard metrics cache
CREATE TABLE admin_metrics_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name VARCHAR(100) NOT NULL,
    metric_value TEXT NOT NULL,  -- JSON value
    cache_key VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System notifications for admin
CREATE TABLE system_notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    notification_type VARCHAR(50) NOT NULL,  -- 'warning', 'error', 'info', 'success'
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    is_dismissed BOOLEAN DEFAULT FALSE,
    created_by INTEGER,  -- system = NULL, user_id for user-generated
    metadata TEXT,  -- JSON object with additional data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE SET NULL
);

-- Enhanced API usage tracking
CREATE TABLE api_usage_detailed (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    endpoint VARCHAR(200) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER,
    response_time INTEGER,  -- in milliseconds
    request_size INTEGER,
    response_size INTEGER,
    ip_address VARCHAR(45),
    user_agent TEXT,
    api_key_used VARCHAR(100),
    rate_limited BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
);

-- Create indexes for better performance
CREATE INDEX idx_professors_university ON professors(university_id);
CREATE INDEX idx_professors_name ON professors(name);
CREATE INDEX idx_professors_research_areas ON professors(research_areas);
CREATE INDEX idx_publications_pmid ON publications(pmid);
CREATE INDEX idx_publications_year ON publications(publication_year);
CREATE INDEX idx_publications_journal ON publications(journal_id);
CREATE INDEX idx_author_publications_professor ON author_publications(professor_id);
CREATE INDEX idx_author_publications_publication ON author_publications(publication_id);
CREATE INDEX idx_collaborations_prof1 ON collaborations(professor1_id);
CREATE INDEX idx_collaborations_prof2 ON collaborations(professor2_id);
CREATE INDEX idx_journal_rankings_year ON journal_rankings(year);
CREATE INDEX idx_journal_rankings_journal ON journal_rankings(journal_id);
CREATE INDEX idx_professor_degrees_professor ON professor_degrees(professor_id);
CREATE INDEX idx_professor_degrees_degree ON professor_degrees(degree_id);
CREATE INDEX idx_degrees_type ON degrees(degree_type);

-- Create views for common queries
CREATE VIEW professor_summary AS
SELECT 
    p.id,
    p.name,
    p.first_name,
    p.last_name,
    p.position,
    p.department,
    u.name as university_name,
    u.city,
    u.province_state,
    p.research_areas,
    COUNT(ap.publication_id) as publication_count,
    MAX(pub.publication_year) as latest_publication_year
FROM professors p
LEFT JOIN universities u ON p.university_id = u.id
LEFT JOIN author_publications ap ON p.id = ap.professor_id
LEFT JOIN publications pub ON ap.publication_id = pub.id
GROUP BY p.id, p.name, p.first_name, p.last_name, p.position, p.department, u.name, u.city, u.province_state, p.research_areas;

CREATE VIEW university_summary AS
SELECT 
    u.id,
    u.name,
    u.city,
    u.province_state,
    u.country,
    COUNT(p.id) as professor_count,
    COUNT(DISTINCT p.department) as department_count
FROM universities u
LEFT JOIN professors p ON u.id = p.university_id
GROUP BY u.id, u.name, u.city, u.province_state, u.country;

-- Sample data for development
INSERT INTO universities (university_code, name, country, province_state, city) VALUES
('CA-ON-002', 'McMaster University', 'Canada', 'Ontario', 'Hamilton'),
('CA-ON-001', 'University of Toronto', 'Canada', 'Ontario', 'Toronto'),
('CA-BC-001', 'University of British Columbia', 'Canada', 'British Columbia', 'Vancouver'); 

-- Additional performance indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_professors_name_research ON professors(name, research_areas);
CREATE INDEX IF NOT EXISTS idx_professors_department_uni ON professors(department, university_id);
CREATE INDEX IF NOT EXISTS idx_universities_country_province ON universities(country, province_state);
CREATE INDEX IF NOT EXISTS idx_universities_type_language ON universities(university_type, languages);
CREATE INDEX IF NOT EXISTS idx_publications_year_journal ON publications(publication_year DESC, journal_id);
CREATE INDEX IF NOT EXISTS idx_author_publications_composite ON author_publications(professor_id, publication_pmid);
CREATE INDEX IF NOT EXISTS idx_citation_networks_citing ON citation_networks(citing_professor_id, citation_count DESC);
CREATE INDEX IF NOT EXISTS idx_citation_networks_cited ON citation_networks(cited_professor_id, citation_count DESC);
CREATE INDEX IF NOT EXISTS idx_publication_metrics_citations ON publication_metrics(total_citations DESC);
CREATE INDEX IF NOT EXISTS idx_professor_degrees_composite ON professor_degrees(professor_id, degree_id);

-- Partial indexes for better performance on filtered queries
CREATE INDEX IF NOT EXISTS idx_professors_active ON professors(id) WHERE name IS NOT NULL AND university_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_publications_recent ON publications(publication_year DESC, pmid) WHERE publication_year >= 2010;
CREATE INDEX IF NOT EXISTS idx_universities_with_faculty ON universities(id, name) WHERE id IN (SELECT DISTINCT university_id FROM professors);

-- Covering indexes for frequently accessed columns
CREATE INDEX IF NOT EXISTS idx_professors_list_view ON professors(id, name, department, university_id, research_areas, position);
CREATE INDEX IF NOT EXISTS idx_universities_list_view ON universities(id, name, city, province_state, country, university_type);

-- Full-text search indexes (PostgreSQL specific - will be ignored in SQLite)
-- CREATE INDEX IF NOT EXISTS idx_professors_fts ON professors USING gin(to_tsvector('english', name || ' ' || COALESCE(research_areas, '')));
-- CREATE INDEX IF NOT EXISTS idx_universities_fts ON universities USING gin(to_tsvector('english', name));

-- Optimize existing indexes by adding missing columns for covering
DROP INDEX IF EXISTS idx_professors_university;
CREATE INDEX idx_professors_university_enhanced ON professors(university_id, name, department, id);

DROP INDEX IF EXISTS idx_author_publications_professor;
CREATE INDEX idx_author_publications_professor_enhanced ON author_publications(professor_id, publication_pmid, author_order);

-- Statistics update for query planner (PostgreSQL)
-- ANALYZE professors;
-- ANALYZE universities;
-- ANALYZE publications;
-- ANALYZE author_publications; 

-- Insert default admin user (password should be changed on first login)
INSERT INTO users (username, email, password_hash, first_name, last_name, role, is_active, email_verified) 
VALUES ('admin', 'admin@facultyfinder.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeANI1.9M8B8H0K1.', 'Admin', 'User', 'admin', TRUE, TRUE); 