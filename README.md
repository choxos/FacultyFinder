# FacultyFinder 🎓

**Discover Your Ideal Academic Collaborators Worldwide**

FacultyFinder is an advanced platform designed to help prospective graduate students, researchers, and institutions connect with faculty members who align with their academic goals and research interests across universities worldwide.

## ✨ Features

### 🔍 **Smart Faculty Discovery**
- **Advanced Search & Filtering**: Find faculty by research areas, universities, departments, publications, and more
- **AI-Powered Matching**: Upload your CV for personalized faculty recommendations using cutting-edge AI
- **Global Coverage**: Access faculty information from top universities worldwide
- **Professional Interface**: Modern, responsive design optimized for academic research

### 📊 **Comprehensive Faculty Profiles**
- **Academic Background**: Detailed information on degrees, positions, and career progression
- **Research Areas**: Categorized research interests with clickable filtering
- **Publication Metrics**: Citation counts, H-index, i10-index, and publication records
- **Collaboration Networks**: Visual representation of academic partnerships
- **Contact Information**: Direct access to faculty email, office locations, and websites

### 🏛️ **University Information**
- **Global Database**: Universities from 25+ countries with detailed profiles
- **Department Insights**: Faculty counts, research strengths, and academic programs
- **Location Integration**: Interactive maps and geographic filtering
- **Institutional Details**: University types, languages of instruction, establishment dates

### 🤖 **AI Assistant**
- **CV Analysis**: Upload PDF/DOCX files for intelligent faculty matching
- **Multiple AI Models**: Choose between Claude, Gemini, ChatGPT, and Grok
- **Flexible Pricing**: Use your own API keys or pay-per-use options
- **Expert Review**: Optional manual CV review by academic professionals

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- SQLite3 (development) or PostgreSQL (production)
- Modern web browser

### Installation

```bash
# Clone the repository
git clone https://github.com/facultyfinder/FacultyFinder.git
cd FacultyFinder

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
cd scripts
python data_loader.py

# Run the application
cd ../webapp
python app.py
```

Visit `http://localhost:8080` to access FacultyFinder!

## 📁 Project Structure

```
FacultyFinder/
├── webapp/                 # Flask web application
│   ├── app.py             # Main application file
│   ├── templates/         # Jinja2 templates
│   ├── static/           # CSS, JS, and assets
│   └── wsgi.py           # WSGI entry point
├── database/              # Database schema and setup
├── scripts/              # Data loading and maintenance
├── data/                 # Raw data files and exports
└── docs/                 # Documentation and guides
```

## 🎨 Technology Stack

- **Backend**: Flask (Python), SQLite/PostgreSQL
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **AI Integration**: OpenAI, Anthropic Claude, Google Gemini, xAI Grok
- **Data Sources**: PubMed, ORCID, Scimago Journal Rankings
- **Deployment**: Gunicorn, Nginx, Systemd
- **Theming**: Custom CSS with dark mode support

## 🌐 API Access

FacultyFinder provides a comprehensive REST API for developers:

```python
import requests

# Search faculty
response = requests.get(
    "https://api.facultyfinder.io/v1/faculties",
    params={"search": "machine learning", "country": "Canada"}
)

faculty = response.json()
```

Visit `/api` for complete documentation.

## 🚀 Deployment

FacultyFinder offers multiple deployment approaches based on your needs:

### 📋 **Choose Your Deployment Path:**

| Goal | Guide | Time | Best For |
|------|-------|------|----------|
| **Quick Demo** | `QUICK_START_DEPLOYMENT.md` | 15 min | Testing, demos |
| **Production Site** | `DEPLOYMENT_GUIDE_RESTRUCTURED.md` | 3-6 hours | Live websites |
| **Technical Reference** | `DEPLOYMENT_INDEX.md` | - | Choose your path |

### ⚡ **Quick Start (15 Minutes)**
Get a working website running immediately:
```bash
sudo apt update && apt install -y python3 python3-venv git
git clone https://github.com/yourusername/FacultyFinder.git /var/www/ff
cd /var/www/ff && python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# Follow QUICK_START_DEPLOYMENT.md for complete steps
```

### 🏗️ **Production Deployment (Progressive Phases)**
Build a complete production system:
- **Phase 1**: Basic working website (30 min)
- **Phase 2**: PostgreSQL + authentication (60 min)  
- **Phase 3**: Domain + SSL + production setup (90 min)
- **Phase 4**: Advanced features (payments, AI, etc.)

### 🔧 **Technology Stack:**
- **Backend**: Flask with Gunicorn WSGI server
- **Database**: SQLite (development) / PostgreSQL (production)
- **Frontend**: Bootstrap 5 with responsive design
- **Reverse Proxy**: Nginx for production
- **SSL**: Let's Encrypt (free certificates)
- **Process Management**: Systemd service

*Note: Detailed deployment guides with server configurations are available separately for security reasons.*

## 📊 Data & Privacy

### Data Sources
- **Universities**: Official institutional websites and directories
- **Publications**: PubMed, ORCID, and other academic databases
- **Journal Rankings**: Scimago Journal & Country Rank

### Privacy Commitment
- Only publicly available academic information is displayed
- Faculty can request profile updates or removal
- No personal data collection without consent
- GDPR and academic privacy standards compliance

## 🤝 Contributing

We welcome contributions from the academic and developer communities!

### Ways to Contribute
- **University Data**: Help expand our global coverage
- **Feature Development**: Implement new functionality
- **Bug Reports**: Identify and report issues
- **Documentation**: Improve guides and tutorials

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📞 Support & Contact

- **Documentation**: [Visit our docs](https://facultyfinder.io/docs)
- **Issues**: [GitHub Issues](https://github.com/facultyfinder/FacultyFinder/issues)
- **Discussions**: [GitHub Discussions](https://github.com/facultyfinder/FacultyFinder/discussions)
- **Email**: support@facultyfinder.io

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🌟 Acknowledgments

- **Academic Community**: For providing open access to research data
- **University Partners**: For supporting global academic collaboration
- **Open Source Libraries**: For enabling rapid development
- **Contributors**: For their valuable contributions and feedback

---

<div align="center">
<p><strong>Connecting researchers worldwide through intelligent faculty discovery</strong></p>
<p>
  <a href="https://facultyfinder.io">Website</a> •
  <a href="https://facultyfinder.io/api">API</a> •
  <a href="https://facultyfinder.io/about">About</a> •
  <a href="https://facultyfinder.io/contact">Contact</a>
</p>
</div>