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