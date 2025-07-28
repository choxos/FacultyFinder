# Citation Analysis & Network Integration Guide

## 🔗 Overview

FacultyFinder now includes comprehensive citation analysis and academic network mapping powered by the **OpenCitations API**. This integration provides deep insights into academic collaboration patterns, research impact, and citation relationships between faculty members.

## ✨ Features

### 📊 Citation Metrics
- **H-Index**: Standard measure of research productivity and impact
- **i10-Index**: Number of publications with at least 10 citations
- **Total Citations**: Aggregate citation count across all publications
- **Average Citations**: Mean citations per publication
- **Citation Velocity**: Citations per year metric
- **Top Cited Papers**: Most impactful publications with citation counts

### 🌐 Citation Networks
- **Collaboration Networks**: Visual mapping of co-authorship relationships
- **Citation Networks**: Visualization of who cites whom among faculty
- **Network Metrics**: Collaboration strength and academic influence analysis
- **Interactive Visualization**: Dynamic network graphs (visualization library integration ready)

### 🔄 Data Management
- **Automated Updates**: Scheduled citation data refreshing
- **Batch Processing**: Efficient handling of large faculty datasets
- **Rate Limiting**: Respectful API usage with built-in delays
- **Error Recovery**: Robust error handling and retry mechanisms

## 🗃️ Database Schema

### New Tables

#### `citations`
```sql
CREATE TABLE citations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    citing_pmid TEXT NOT NULL,        -- Paper that cites
    cited_pmid TEXT NOT NULL,         -- Paper being cited
    citing_doi TEXT,
    cited_doi TEXT,
    citation_date TEXT,
    source VARCHAR(50) DEFAULT 'opencitations',
    confidence_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(citing_pmid, cited_pmid)
);
```

#### `citation_networks`
```sql
CREATE TABLE citation_networks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    citing_professor_id INTEGER,      -- Professor who cites
    cited_professor_id INTEGER,       -- Professor being cited
    citing_pmid TEXT,
    cited_pmid TEXT,
    citation_count INTEGER DEFAULT 1,
    first_citation_year INTEGER,
    last_citation_year INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (citing_professor_id) REFERENCES professors (id),
    FOREIGN KEY (cited_professor_id) REFERENCES professors (id)
);
```

#### `publication_metrics`
```sql
CREATE TABLE publication_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pmid TEXT UNIQUE NOT NULL,
    doi TEXT,
    total_citations INTEGER DEFAULT 0,
    h_index_contribution INTEGER DEFAULT 0,
    citation_velocity REAL DEFAULT 0.0,
    peak_citation_year INTEGER,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pmid) REFERENCES publications (pmid)
);
```

## 🚀 API Integration

### OpenCitations API
- **Base URL**: `https://api.opencitations.net/index/v2`
- **Endpoints Used**:
  - `/citations/{identifiers}` - Get papers that cite given papers
  - `/references/{identifiers}` - Get papers cited by given papers
  - `/citation-count/{identifiers}` - Get citation counts
- **Rate Limiting**: 100ms delay between requests, batch processing
- **Authentication**: Optional access token for higher rate limits

### Internal API Endpoints

#### Update Citations
```
GET /api/citations/update/<professor_id>
```
Updates citation data for a specific professor's publications.

**Response:**
```json
{
    "success": true,
    "citations_stored": 45,
    "metrics_updated": 12,
    "network_relationships": 8,
    "pmids_processed": 12
}
```

#### Get Citation Network
```
GET /api/citations/network/<professor_id>
```
Retrieves collaboration and citation network data.

**Response:**
```json
{
    "success": true,
    "network": {
        "nodes": [
            {
                "id": 123,
                "name": "Dr. Smith",
                "university_id": 1,
                "type": "central",
                "size": 25
            }
        ],
        "edges": [
            {
                "source": 123,
                "target": 456,
                "weight": 5,
                "type": "collaboration"
            }
        ]
    },
    "total_nodes": 15,
    "total_edges": 28
}
```

## 🔧 Usage Guide

### 1. Manual Citation Updates

#### Update Single Professor
```bash
cd scripts
python3 citation_update_scheduler.py single 123
```

#### Update Batch of Professors
```bash
python3 citation_update_scheduler.py batch 5
```

#### Full System Update
```bash
python3 citation_update_scheduler.py full 50
```

### 2. Integration in Application

#### In Python Code
```python
from webapp.citation_analysis import CitationAnalyzer, CitationVisualizer
from webapp.opencitations_api import CitationManager

# Initialize components
analyzer = CitationAnalyzer(db_path)
manager = CitationManager(db_path)

# Calculate metrics
metrics = analyzer.calculate_citation_metrics(professor_id)
top_papers = analyzer.get_top_cited_papers(professor_id, 10)

# Update citation data
manager.fetch_and_store_citations(pmids)
manager.build_citation_network()
```

#### In Templates
```html
<!-- Citation metrics display -->
{% if citation_metrics %}
    <div class="metric-card">
        <div class="metric-number">{{ citation_metrics.h_index }}</div>
        <div class="metric-label">H-Index</div>
    </div>
{% endif %}

<!-- Network visualization -->
<div id="citation-network" style="height: 400px;"></div>
<script>
    // Network data passed from backend
    const networkData = {{ network_json|safe }};
    renderCitationNetwork(networkData);
</script>
```

### 3. Automated Scheduling

#### Cron Job Setup
```bash
# Update citations daily at 2 AM
0 2 * * * cd /var/www/ff/scripts && python3 citation_update_scheduler.py batch 10 >> ../logs/citations.log 2>&1

# Full update weekly on Sundays at 3 AM
0 3 * * 0 cd /var/www/ff/scripts && python3 citation_update_scheduler.py full 100 >> ../logs/citations.log 2>&1
```

## 📊 Metrics Explained

### H-Index
The H-Index is calculated as the largest number h such that the author has h papers with at least h citations each.

**Example**: If a professor has 10 papers with citation counts [50, 30, 25, 20, 15, 12, 8, 5, 3, 1], their H-Index is 8 (8 papers with ≥8 citations each).

### i10-Index
The number of publications with at least 10 citations.

### Citation Velocity
Average citations received per year of research activity:
```
Citation Velocity = Total Citations / Years Active
```

### Network Metrics
- **Collaboration Strength**: Number of joint publications
- **Citation Influence**: How often colleagues cite the professor's work
- **Network Centrality**: Position importance in collaboration network

## 🎨 Visualization Integration

### Supported Libraries
The system provides data in formats compatible with:
- **D3.js**: For custom interactive networks
- **vis.js**: For easy network visualization
- **Cytoscape.js**: For complex graph layouts
- **Sigma.js**: For large network performance

### Example Network Data Structure
```javascript
{
    "nodes": [
        {
            "id": 123,
            "name": "Dr. Jane Smith",
            "type": "central",        // central, coauthor, cited
            "color": "#e74c3c",      // Node color
            "size": 25,              // Node size
            "university_id": 1
        }
    ],
    "edges": [
        {
            "source": 123,
            "target": 456,
            "type": "collaboration", // collaboration, citation
            "weight": 5,             // Relationship strength
            "color": "#3498db",      // Edge color
            "width": 3               // Edge width
        }
    ]
}
```

## 🔒 Privacy & Ethics

### Data Sources
- **OpenCitations**: Open access citation database
- **Public Publications**: Only publicly available research data
- **Aggregated Metrics**: No personal information beyond public academic records

### Rate Limiting
- **API Respect**: Built-in delays to respect OpenCitations rate limits
- **Batch Processing**: Efficient data collection minimizing API load
- **Caching**: Local storage to reduce repeated API calls

### Data Retention
- **Citation Data**: Stored locally for performance
- **Update Frequency**: Weekly updates to balance freshness and efficiency
- **Cleanup**: Automatic removal of outdated citation records

## 🚀 Future Enhancements

### Planned Features
1. **Real-time Collaboration Recommendations**: Suggest potential collaborators
2. **Impact Prediction**: ML models for predicting paper impact
3. **Trend Analysis**: Identification of emerging research areas
4. **Cross-institutional Networks**: University-level collaboration mapping
5. **Temporal Analysis**: Evolution of citation patterns over time

### Visualization Improvements
1. **3D Network Graphs**: Interactive 3D collaboration networks
2. **Timeline Visualization**: Citation growth over time
3. **Geographic Mapping**: Institution location-based networks
4. **Filtering Controls**: Dynamic network filtering by metrics
5. **Export Features**: Network data export for external analysis

### Performance Optimizations
1. **Incremental Updates**: Only update changed data
2. **Background Processing**: Async citation updates
3. **Caching Layers**: Multi-level caching for network data
4. **Database Optimization**: Query performance improvements
5. **API Parallelization**: Concurrent OpenCitations requests

## 📚 Resources

### OpenCitations
- **Website**: https://opencitations.net/
- **API Documentation**: https://opencitations.net/index/api/v2
- **Access Token**: https://opencitations.net/accesstoken

### Academic Metrics
- **H-Index**: https://en.wikipedia.org/wiki/H-index
- **Citation Analysis**: https://en.wikipedia.org/wiki/Citation_analysis
- **Network Analysis**: https://en.wikipedia.org/wiki/Social_network_analysis

### Visualization Libraries
- **D3.js**: https://d3js.org/
- **vis.js**: https://visjs.org/
- **Cytoscape.js**: https://cytoscape.org/
- **Sigma.js**: https://sigmajs.org/

## 🐛 Troubleshooting

### Common Issues

#### No Citation Data
- **Cause**: Publications not in OpenCitations database
- **Solution**: Verify PMIDs exist in PubMed and OpenCitations

#### API Rate Limits
- **Cause**: Too many requests to OpenCitations
- **Solution**: Increase delays in `opencitations_api.py`

#### Network Visualization Not Loading
- **Cause**: No collaboration or citation relationships found
- **Solution**: Update more professors or check database connectivity

#### Slow Performance
- **Cause**: Large datasets or inefficient queries
- **Solution**: Add database indexes, implement pagination

### Debug Commands
```bash
# Check citation data
sqlite3 database/facultyfinder_dev.db "SELECT COUNT(*) FROM citations;"

# Verify professor networks
sqlite3 database/facultyfinder_dev.db "SELECT COUNT(*) FROM citation_networks;"

# Test OpenCitations API
cd webapp && python3 opencitations_api.py

# Update logs
tail -f logs/citation_updates.log
```

---

**Citation Analysis Integration**: Transforming academic data into actionable research insights and collaboration opportunities! 🎓📊🔗 