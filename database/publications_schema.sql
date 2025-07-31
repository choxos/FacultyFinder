-- Publications Database Schema
-- Comprehensive schema for storing publication data from multiple sources

-- Enhanced Publications Table
CREATE TABLE IF NOT EXISTS publications (
    id SERIAL PRIMARY KEY,
    publication_id VARCHAR(255) NOT NULL,
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
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(publication_id, source_system)
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
    UNIQUE(faculty_id, publication_id, source_system)
);

-- Enhanced Author Profiles Table (from OpenAlex author info)
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
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Research Collaborations Table
CREATE TABLE IF NOT EXISTS research_collaborations (
    id SERIAL PRIMARY KEY,
    faculty1_id VARCHAR(50) NOT NULL,
    faculty2_id VARCHAR(50) NOT NULL,
    publication_id VARCHAR(255) NOT NULL,
    source_system VARCHAR(50) NOT NULL,
    collaboration_year INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Publication Metrics Cache Table (for performance)
CREATE TABLE IF NOT EXISTS publication_metrics_cache (
    id SERIAL PRIMARY KEY,
    faculty_id VARCHAR(50) UNIQUE NOT NULL,
    total_publications INTEGER DEFAULT 0,
    total_citations INTEGER DEFAULT 0,
    h_index INTEGER DEFAULT 0,
    recent_publications INTEGER DEFAULT 0,      -- Last 5 years
    collaboration_count INTEGER DEFAULT 0,
    current_affiliation_rate FLOAT DEFAULT 0,
    last_calculated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_publications_source_system ON publications(source_system);
CREATE INDEX IF NOT EXISTS idx_publications_year ON publications(publication_year);
CREATE INDEX IF NOT EXISTS idx_publications_citation_count ON publications(citation_count);
CREATE INDEX IF NOT EXISTS idx_publications_doi ON publications(doi);
CREATE INDEX IF NOT EXISTS idx_publications_pmid ON publications(pmid);

CREATE INDEX IF NOT EXISTS idx_faculty_publications_faculty_id ON faculty_publications(faculty_id);
CREATE INDEX IF NOT EXISTS idx_faculty_publications_publication_id ON faculty_publications(publication_id);
CREATE INDEX IF NOT EXISTS idx_faculty_publications_source ON faculty_publications(source_system);
CREATE INDEX IF NOT EXISTS idx_faculty_publications_current_aff ON faculty_publications(current_affiliation);

CREATE INDEX IF NOT EXISTS idx_author_profiles_openalex_id ON author_profiles(openalex_id);
CREATE INDEX IF NOT EXISTS idx_author_profiles_orcid ON author_profiles(orcid);
CREATE INDEX IF NOT EXISTS idx_author_profiles_h_index ON author_profiles(h_index);
CREATE INDEX IF NOT EXISTS idx_author_profiles_works_count ON author_profiles(works_count);

CREATE INDEX IF NOT EXISTS idx_collaborations_faculty1 ON research_collaborations(faculty1_id);
CREATE INDEX IF NOT EXISTS idx_collaborations_faculty2 ON research_collaborations(faculty2_id);
CREATE INDEX IF NOT EXISTS idx_collaborations_year ON research_collaborations(collaboration_year);

-- Full-text search indexes
CREATE INDEX IF NOT EXISTS idx_publications_title_fts ON publications USING gin(to_tsvector('english', title));
CREATE INDEX IF NOT EXISTS idx_publications_abstract_fts ON publications USING gin(to_tsvector('english', abstract));

-- JSONB indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_publications_authors_gin ON publications USING gin(authors);
CREATE INDEX IF NOT EXISTS idx_publications_topics_gin ON publications USING gin(topics);
CREATE INDEX IF NOT EXISTS idx_author_profiles_research_topics_gin ON author_profiles USING gin(research_topics);

-- Functions and triggers for automatic updates
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for publications table
DROP TRIGGER IF EXISTS update_publications_modtime ON publications;
CREATE TRIGGER update_publications_modtime 
    BEFORE UPDATE ON publications 
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

-- Function to calculate and cache faculty metrics
CREATE OR REPLACE FUNCTION refresh_faculty_metrics(faculty_id_param VARCHAR(50))
RETURNS void AS $$
DECLARE
    total_pubs INTEGER;
    total_cites INTEGER;
    h_idx INTEGER;
    recent_pubs INTEGER;
    collab_count INTEGER;
    current_aff_rate FLOAT;
BEGIN
    -- Calculate total publications
    SELECT COUNT(*) INTO total_pubs
    FROM faculty_publications
    WHERE faculty_id = faculty_id_param;
    
    -- Calculate total citations
    SELECT COALESCE(SUM(p.citation_count), 0) INTO total_cites
    FROM publications p
    JOIN faculty_publications fp ON p.publication_id = fp.publication_id 
                                 AND p.source_system = fp.source_system
    WHERE fp.faculty_id = faculty_id_param;
    
    -- Get H-index from author profile
    SELECT COALESCE(h_index, 0) INTO h_idx
    FROM author_profiles
    WHERE faculty_id = faculty_id_param;
    
    -- Calculate recent publications (last 5 years)
    SELECT COUNT(*) INTO recent_pubs
    FROM publications p
    JOIN faculty_publications fp ON p.publication_id = fp.publication_id
    WHERE fp.faculty_id = faculty_id_param 
    AND p.publication_year >= EXTRACT(YEAR FROM CURRENT_DATE) - 5;
    
    -- Calculate collaboration count
    SELECT COUNT(DISTINCT fp2.faculty_id) INTO collab_count
    FROM faculty_publications fp1
    JOIN faculty_publications fp2 ON fp1.publication_id = fp2.publication_id 
                                  AND fp1.source_system = fp2.source_system
    WHERE fp1.faculty_id = faculty_id_param 
    AND fp2.faculty_id != faculty_id_param;
    
    -- Calculate current affiliation rate
    SELECT CASE 
        WHEN COUNT(*) > 0 THEN 
            (SUM(CASE WHEN current_affiliation THEN 1 ELSE 0 END)::FLOAT / COUNT(*)) * 100
        ELSE 0 
    END INTO current_aff_rate
    FROM faculty_publications
    WHERE faculty_id = faculty_id_param;
    
    -- Insert or update metrics cache
    INSERT INTO publication_metrics_cache (
        faculty_id, total_publications, total_citations, h_index,
        recent_publications, collaboration_count, current_affiliation_rate,
        last_calculated
    ) VALUES (
        faculty_id_param, total_pubs, total_cites, h_idx,
        recent_pubs, collab_count, current_aff_rate, CURRENT_TIMESTAMP
    ) ON CONFLICT (faculty_id) DO UPDATE SET
        total_publications = EXCLUDED.total_publications,
        total_citations = EXCLUDED.total_citations,
        h_index = EXCLUDED.h_index,
        recent_publications = EXCLUDED.recent_publications,
        collaboration_count = EXCLUDED.collaboration_count,
        current_affiliation_rate = EXCLUDED.current_affiliation_rate,
        last_calculated = EXCLUDED.last_calculated;
        
END;
$$ LANGUAGE plpgsql;

-- Views for common queries
CREATE OR REPLACE VIEW faculty_publication_summary AS
SELECT 
    ap.faculty_id,
    ap.display_name,
    ap.first_name,
    ap.last_name,
    ap.h_index,
    ap.works_count,
    ap.cited_by_count,
    pmc.total_publications,
    pmc.total_citations,
    pmc.recent_publications,
    pmc.collaboration_count,
    pmc.current_affiliation_rate
FROM author_profiles ap
LEFT JOIN publication_metrics_cache pmc ON ap.faculty_id = pmc.faculty_id;

CREATE OR REPLACE VIEW top_cited_publications AS
SELECT 
    p.title,
    p.citation_count,
    p.publication_year,
    p.journal_name,
    p.doi,
    p.source_system,
    string_agg(DISTINCT ap.display_name, ', ') as faculty_authors
FROM publications p
JOIN faculty_publications fp ON p.publication_id = fp.publication_id 
                             AND p.source_system = fp.source_system
JOIN author_profiles ap ON fp.faculty_id = ap.faculty_id
WHERE p.citation_count > 0
GROUP BY p.id, p.title, p.citation_count, p.publication_year, p.journal_name, p.doi, p.source_system
ORDER BY p.citation_count DESC;

CREATE OR REPLACE VIEW collaboration_network AS
SELECT 
    ap1.display_name as faculty1_name,
    ap1.faculty_id as faculty1_id,
    ap2.display_name as faculty2_name,
    ap2.faculty_id as faculty2_id,
    COUNT(*) as collaboration_count,
    MAX(p.publication_year) as latest_collaboration,
    MIN(p.publication_year) as first_collaboration
FROM faculty_publications fp1
JOIN faculty_publications fp2 ON fp1.publication_id = fp2.publication_id 
                              AND fp1.source_system = fp2.source_system
JOIN publications p ON fp1.publication_id = p.publication_id
JOIN author_profiles ap1 ON fp1.faculty_id = ap1.faculty_id
JOIN author_profiles ap2 ON fp2.faculty_id = ap2.faculty_id
WHERE fp1.faculty_id < fp2.faculty_id  -- Avoid duplicates
GROUP BY ap1.faculty_id, ap1.display_name, ap2.faculty_id, ap2.display_name
HAVING COUNT(*) >= 2  -- Only show collaborations with 2+ papers
ORDER BY collaboration_count DESC;

-- Sample data verification queries
-- Uncomment these after importing data to verify the system

-- SELECT 'Publications by source' as metric, source_system, COUNT(*) as count
-- FROM publications 
-- GROUP BY source_system
-- UNION ALL
-- SELECT 'Faculty with publications', 'total', COUNT(DISTINCT faculty_id)
-- FROM faculty_publications
-- UNION ALL  
-- SELECT 'Author profiles', 'total', COUNT(*)
-- FROM author_profiles;

COMMENT ON TABLE publications IS 'Core publications table storing all publication data from multiple sources';
COMMENT ON TABLE faculty_publications IS 'Junction table linking faculty to their publications with affiliation tracking';
COMMENT ON TABLE author_profiles IS 'Comprehensive author profiles from OpenAlex with metrics and research topics';
COMMENT ON TABLE research_collaborations IS 'Research collaboration relationships between faculty members';
COMMENT ON TABLE publication_metrics_cache IS 'Cached metrics for performance optimization';

COMMENT ON COLUMN publications.raw_data IS 'Complete original JSON data from source system for future reference';
COMMENT ON COLUMN faculty_publications.current_affiliation IS 'Whether publication was created while at current institution';
COMMENT ON COLUMN author_profiles.research_topics IS 'Structured research topics with counts and classifications';
COMMENT ON COLUMN publication_metrics_cache.current_affiliation_rate IS 'Percentage of publications with current institutional affiliation';

-- Grant necessary permissions
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO your_app_user; 