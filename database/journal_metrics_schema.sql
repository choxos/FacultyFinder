-- FacultyFinder Journal Metrics and Citation Tracking Schema
-- Run this to add publication enhancement tables

-- Add new columns to existing publications table
ALTER TABLE publications ADD COLUMN pmcid VARCHAR(20);
ALTER TABLE publications ADD COLUMN citation_count INTEGER DEFAULT 0;
ALTER TABLE publications ADD COLUMN last_citation_update TIMESTAMP;
ALTER TABLE publications ADD COLUMN journal_issn VARCHAR(20);
ALTER TABLE publications ADD COLUMN journal_rank INTEGER;
ALTER TABLE publications ADD COLUMN journal_sjr DECIMAL(8,4);
ALTER TABLE publications ADD COLUMN journal_quartile VARCHAR(5);
ALTER TABLE publications ADD COLUMN journal_h_index INTEGER;
ALTER TABLE publications ADD COLUMN scimago_year INTEGER;

-- Create journal metrics table for Scimago data
CREATE TABLE IF NOT EXISTS journal_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    issn VARCHAR(20),
    journal_name VARCHAR(500),
    year INTEGER,
    rank_value INTEGER,
    sjr DECIMAL(8,4),
    sjr_best_quartile VARCHAR(5),
    h_index INTEGER,
    country VARCHAR(100),
    subject_category TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(issn, year)
);

-- Create citations tracking table
CREATE TABLE IF NOT EXISTS citations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    citing_publication_id INTEGER,
    cited_publication_id INTEGER,
    citation_context TEXT,
    citation_type VARCHAR(50),
    opencitations_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (citing_publication_id) REFERENCES publications(id),
    FOREIGN KEY (cited_publication_id) REFERENCES publications(id),
    UNIQUE(citing_publication_id, cited_publication_id)
);

-- Create publication update log table
CREATE TABLE IF NOT EXISTS publication_update_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    professor_id INTEGER,
    search_type VARCHAR(50), -- 'all', 'affiliation', 'citations'
    publications_found INTEGER DEFAULT 0,
    new_publications INTEGER DEFAULT 0,
    citations_updated INTEGER DEFAULT 0,
    update_duration INTEGER DEFAULT 0, -- seconds
    status VARCHAR(20) DEFAULT 'success', -- 'success', 'error', 'partial'
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (professor_id) REFERENCES professors(id)
);

-- Create collaboration networks table
CREATE TABLE IF NOT EXISTS collaboration_networks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    professor1_id INTEGER,
    professor2_id INTEGER,
    collaboration_count INTEGER DEFAULT 1,
    shared_publications INTEGER DEFAULT 0,
    collaboration_type VARCHAR(50), -- 'internal', 'national', 'international'
    first_collaboration_date DATE,
    last_collaboration_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (professor1_id) REFERENCES professors(id),
    FOREIGN KEY (professor2_id) REFERENCES professors(id),
    UNIQUE(professor1_id, professor2_id)
);

-- Create journal impact metrics summary table
CREATE TABLE IF NOT EXISTS professor_journal_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    professor_id INTEGER,
    total_publications INTEGER DEFAULT 0,
    q1_publications INTEGER DEFAULT 0,
    q2_publications INTEGER DEFAULT 0,
    q3_publications INTEGER DEFAULT 0,
    q4_publications INTEGER DEFAULT 0,
    mean_sjr DECIMAL(8,4),
    median_sjr DECIMAL(8,4),
    mean_rank DECIMAL(8,2),
    median_rank INTEGER,
    h_index_weighted DECIMAL(8,2), -- weighted average of journal h-indices
    total_citations INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (professor_id) REFERENCES professors(id),
    UNIQUE(professor_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_publications_pmcid ON publications(pmcid);
CREATE INDEX IF NOT EXISTS idx_publications_issn ON publications(journal_issn);
CREATE INDEX IF NOT EXISTS idx_publications_citation_count ON publications(citation_count);
CREATE INDEX IF NOT EXISTS idx_publications_quartile ON publications(journal_quartile);
CREATE INDEX IF NOT EXISTS idx_publications_year ON publications(publication_year);

CREATE INDEX IF NOT EXISTS idx_journal_metrics_issn ON journal_metrics(issn);
CREATE INDEX IF NOT EXISTS idx_journal_metrics_year ON journal_metrics(year);
CREATE INDEX IF NOT EXISTS idx_journal_metrics_issn_year ON journal_metrics(issn, year);

CREATE INDEX IF NOT EXISTS idx_citations_citing ON citations(citing_publication_id);
CREATE INDEX IF NOT EXISTS idx_citations_cited ON citations(cited_publication_id);

CREATE INDEX IF NOT EXISTS idx_update_log_professor ON publication_update_log(professor_id);
CREATE INDEX IF NOT EXISTS idx_update_log_date ON publication_update_log(created_at);

CREATE INDEX IF NOT EXISTS idx_collaboration_prof1 ON collaboration_networks(professor1_id);
CREATE INDEX IF NOT EXISTS idx_collaboration_prof2 ON collaboration_networks(professor2_id);
CREATE INDEX IF NOT EXISTS idx_collaboration_type ON collaboration_networks(collaboration_type);

-- Create view for professor statistics with journal metrics
CREATE VIEW IF NOT EXISTS professor_publication_stats AS
SELECT 
    p.id as professor_id,
    p.name as professor_name,
    p.university_id,
    u.name as university_name,
    COUNT(DISTINCT pub.id) as total_publications,
    COUNT(CASE WHEN pub.journal_quartile = 'Q1' THEN 1 END) as q1_publications,
    COUNT(CASE WHEN pub.journal_quartile = 'Q2' THEN 1 END) as q2_publications,
    COUNT(CASE WHEN pub.journal_quartile = 'Q3' THEN 1 END) as q3_publications,
    COUNT(CASE WHEN pub.journal_quartile = 'Q4' THEN 1 END) as q4_publications,
    ROUND(AVG(pub.journal_sjr), 4) as mean_sjr,
    ROUND(AVG(pub.journal_rank), 2) as mean_rank,
    SUM(pub.citation_count) as total_citations,
    MAX(pub.publication_year) as latest_publication_year,
    MIN(pub.publication_year) as earliest_publication_year
FROM professors p
LEFT JOIN universities u ON p.university_id = u.id
LEFT JOIN author_publications ap ON p.id = ap.professor_id
LEFT JOIN publications pub ON ap.publication_id = pub.id
GROUP BY p.id, p.name, p.university_id, u.name;

-- Create view for collaboration networks
CREATE VIEW IF NOT EXISTS professor_collaborations AS
SELECT 
    p1.name as professor1_name,
    p2.name as professor2_name,
    cn.collaboration_count,
    cn.collaboration_type,
    cn.first_collaboration_date,
    cn.last_collaboration_date,
    u1.name as university1,
    u2.name as university2,
    CASE 
        WHEN u1.id = u2.id THEN 'Internal'
        WHEN u1.country = u2.country THEN 'National' 
        ELSE 'International'
    END as collaboration_scope
FROM collaboration_networks cn
JOIN professors p1 ON cn.professor1_id = p1.id
JOIN professors p2 ON cn.professor2_id = p2.id
LEFT JOIN universities u1 ON p1.university_id = u1.id
LEFT JOIN universities u2 ON p2.university_id = u2.id;

-- Create trigger to update professor metrics when publications change
CREATE TRIGGER IF NOT EXISTS update_professor_metrics_trigger
    AFTER INSERT ON author_publications
    FOR EACH ROW
BEGIN
    INSERT OR REPLACE INTO professor_journal_metrics (
        professor_id, 
        total_publications,
        q1_publications,
        q2_publications, 
        q3_publications,
        q4_publications,
        mean_sjr,
        mean_rank,
        total_citations,
        last_updated
    )
    SELECT 
        NEW.professor_id,
        COUNT(DISTINCT p.id),
        SUM(CASE WHEN p.journal_quartile = 'Q1' THEN 1 ELSE 0 END),
        SUM(CASE WHEN p.journal_quartile = 'Q2' THEN 1 ELSE 0 END),
        SUM(CASE WHEN p.journal_quartile = 'Q3' THEN 1 ELSE 0 END),
        SUM(CASE WHEN p.journal_quartile = 'Q4' THEN 1 ELSE 0 END),
        AVG(p.journal_sjr),
        AVG(p.journal_rank),
        SUM(p.citation_count),
        CURRENT_TIMESTAMP
    FROM author_publications ap
    JOIN publications p ON ap.publication_id = p.id
    WHERE ap.professor_id = NEW.professor_id;
END;

-- Insert initial data validation queries
-- These can be run to check data integrity

-- Check for publications without journal metrics that should have them
-- SELECT p.id, p.title, p.journal_name, p.journal_issn, p.publication_year
-- FROM publications p
-- WHERE p.journal_issn IS NOT NULL 
-- AND p.publication_year IS NOT NULL
-- AND p.journal_quartile IS NULL
-- LIMIT 10;

-- Check journal metrics data
-- SELECT year, COUNT(*) as journal_count
-- FROM journal_metrics
-- GROUP BY year
-- ORDER BY year DESC;

-- Check professor publication counts
-- SELECT p.name, COUNT(ap.publication_id) as pub_count
-- FROM professors p
-- LEFT JOIN author_publications ap ON p.id = ap.professor_id
-- GROUP BY p.id, p.name
-- ORDER BY pub_count DESC
-- LIMIT 20; 