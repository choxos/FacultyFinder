# FacultyFinder 🎓

> **Discover Your Ideal Faculty** - A comprehensive platform for finding faculty members across Canadian universities based on research interests and academic compatibility.

FacultyFinder is part of the [Xera DB](https://xeradb.com) research platform ecosystem, designed to help prospective graduate students and researchers connect with faculty members who align with their academic goals.

![FacultyFinder](https://img.shields.io/badge/Status-In%20Development-yellow)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Flask](https://img.shields.io/badge/Flask-3.0+-green)
![License](https://img.shields.io/badge/License-MIT-blue)

## 🚀 Features

### ✅ Implemented
- **Faculty Search & Discovery**: Advanced search and filtering by name, research areas, university, and department
- **University Explorer**: Browse and compare Canadian universities with faculty statistics
- **Detailed Professor Profiles**: Comprehensive profiles with academic information, contact details, and social media links
- **Professional Theme**: Academic-focused UI with consistent Xera DB branding
- **Responsive Design**: Mobile-friendly interface with Bootstrap 5
- **Database Integration**: SQLite for development with PostgreSQL support for production

### 🔄 In Progress
- **PubMed Integration**: Automatic publication discovery via Entrez API
- **Journal Impact Metrics**: Scimago journal ranking integration for publication quality assessment
- **AI-Powered Matching**: CV analysis for personalized faculty recommendations
- **Collaboration Networks**: Co-authorship analysis and visualization
- **REST API**: External access to faculty and publication data

### 📋 Planned
- **Multi-language Support**: French and English interfaces
- **Advanced Analytics**: Research impact visualization and trends
- **Notification System**: Updates on faculty research activities
- **Export Features**: PDF reports and data export capabilities

## 🛠️ Technology Stack

- **Backend**: Flask 3.0+ (Python)
- **Database**: SQLite (development) / PostgreSQL (production)
- **Frontend**: Bootstrap 5, Font Awesome, custom CSS themes
- **Data Processing**: Pandas, NumPy
- **APIs**: PubMed Entrez, AI providers (Claude, Gemini, ChatGPT, Grok)
- **Payments**: Stripe integration
- **Deployment**: Gunicorn, supervisor

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip package manager

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/xeradb/FacultyFinder.git
   cd FacultyFinder
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the database**
   ```bash
   python3 scripts/data_loader.py
   ```

4. **Start the application**
   ```bash
   python3 run_app.py
   ```

5. **Access the application**
   Open your browser and navigate to: `http://localhost:8080`

### Alternative Launch Methods

**Using the webapp directly:**
```bash
cd webapp
FLASK_ENV=development FLASK_DEBUG=1 python3 app.py
```

**Using the convenience launcher:**
```bash
chmod +x run_app.py
./run_app.py
```

## 📊 Database Schema

FacultyFinder uses a comprehensive database schema designed for academic data:

### Core Tables
- **Universities**: Canadian university information with codes and locations
- **Professors**: Faculty profiles with contact and academic details
- **Publications**: Research publications with DOI, PMID, and journal information
- **Journals**: Journal metadata with Scimago rankings by year
- **Collaborations**: Co-authorship networks and collaboration metrics

### Data Sources
- **University Codes**: Standardized Canadian university identifiers
- **Faculty Data**: McMaster HEI department (validated sample of 281 professors)
- **Scimago Rankings**: Journal impact metrics from 1999-2024
- **PubMed**: Publication metadata and citations (planned)

## 🎨 User Interface

FacultyFinder features a professional academic interface with:

- **Unified Theme System**: Consistent with other Xera DB projects
- **Academic Color Scheme**: Deep blues, academic gold, and research green
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile
- **Accessibility**: WCAG compliant with semantic HTML and proper ARIA labels

### Key Pages

1. **Home Page** (`/`)
   - Hero section with main search
   - Platform statistics dashboard
   - Top universities showcase
   - Feature highlights

2. **Faculty Search** (`/faculties`)
   - Advanced search and filtering
   - Grid/list view toggle
   - Professor cards with key information
   - Research area tags (clickable)

3. **University Explorer** (`/universities`)
   - University cards with statistics
   - Province/state filtering
   - Faculty count and department information

4. **Professor Profiles** (`/professor/<id>`)
   - Comprehensive academic information
   - Contact details and social media links
   - Research areas and collaborations
   - Publication lists (when available)
   - Academic profile links (Google Scholar, ORCID, etc.)

## 🔌 API Integration

### Current Integrations
- **Database**: SQLite/PostgreSQL with optimized queries
- **Static Assets**: Bootstrap 5 and Font Awesome CDNs

### Planned Integrations
- **PubMed Entrez API**: Automatic publication discovery
- **AI Services**: Claude, Gemini, ChatGPT, Grok for CV analysis
- **Stripe**: Payment processing for premium features
- **Academic APIs**: ORCID, Crossref, Google Scholar

## 📁 Project Structure

```
FacultyFinder/
├── webapp/                 # Flask application
│   ├── app.py             # Main application file
│   ├── templates/         # Jinja2 templates
│   └── static/            # CSS, JS, and assets
├── database/              # Database files and schema
│   ├── schema.sql         # Database schema
│   └── facultyfinder_dev.db  # SQLite database
├── scripts/               # Data processing scripts
│   └── data_loader.py     # Database initialization
├── data/                  # Source data files
│   ├── mcmaster_hei_faculty.csv
│   ├── university_codes.csv
│   └── scimago_journals_comprehensive.csv
├── css/themes/            # Theme CSS files
├── requirements.txt       # Python dependencies
└── run_app.py            # Application launcher
```

## 🌐 Environment Configuration

### Development
```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
export DEV_DB_PATH=database/facultyfinder_dev.db
```

### Production
```bash
export FLASK_ENV=production
export DB_HOST=localhost
export DB_USER=facultyfinder_user
export DB_PASSWORD=your_secure_password
export DB_NAME=facultyfinder_production
export SECRET_KEY=your_secret_key
```

## 🤝 Contributing

We welcome contributions to FacultyFinder! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Code Style
- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings for new functions
- Maintain consistent indentation (4 spaces)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Related Projects

- **[Xera DB](https://xeradb.com)**: Main research platform ecosystem
- **[EvidenceDB](https://github.com/xeradb/EvidenceDB)**: Evidence-based medicine network visualization
- **[OpenScienceTracker](https://github.com/xeradb/OpenScienceTracker)**: Open science publication tracking
- **[CitingRetracted](https://github.com/xeradb/CitingRetracted)**: Retracted paper citation analysis

## 📞 Support

- **Documentation**: [docs.xeradb.com/facultyfinder](https://docs.xeradb.com/facultyfinder)
- **Issues**: [GitHub Issues](https://github.com/xeradb/FacultyFinder/issues)
- **Discussions**: [GitHub Discussions](https://github.com/xeradb/FacultyFinder/discussions)
- **Email**: support@xeradb.com

## 🙏 Acknowledgments

- **McMaster University**: HEI department data
- **Scimago Lab**: Journal ranking data
- **PubMed/NCBI**: Publication metadata
- **Bootstrap Team**: UI framework
- **Flask Community**: Web framework

---

<div align="center">
  <p>Made with ❤️ for the academic community</p>
  <p>Part of the <a href="https://xeradb.com">Xera DB</a> research platform ecosystem</p>
</div>