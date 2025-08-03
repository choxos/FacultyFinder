# FacultyFinder

**Discover Your Ideal Academic Collaborators Worldwide**

FacultyFinder is a comprehensive platform that helps researchers discover and connect with faculty members across universities globally. Our AI-powered matching system and extensive academic database make finding the perfect research collaborators easier than ever.

## 🌟 Features

- **Global Faculty Database**: Access profiles from universities worldwide
- **Advanced Search & Filtering**: Find faculty by expertise, location, and research areas
- **University Profiles**: Comprehensive information about academic institutions
- **Publication Tracking**: Integration with academic databases (PubMed, OpenAlex)
- **Analytics Dashboard**: Track engagement and platform usage
- **Modern UI**: Responsive design with dark/light theme support
- **Admin Panel**: Comprehensive management tools

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL (or SQLite for development)
- Node.js (for front-end assets)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/FacultyFinder.git
   cd FacultyFinder
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run the application**
   ```bash
   python -m uvicorn webapp.main:app --reload --host 0.0.0.0 --port 8000
   ```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=facultyfinder

# Security
SECRET_KEY=your-secret-key-here

# Google OAuth (Optional)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback

# Google Analytics (Optional)
GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX
GOOGLE_ANALYTICS_ENABLED=true

# Email Configuration (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### Google Analytics Setup

FacultyFinder includes comprehensive Google Analytics (GA4) tracking:

1. **Create a GA4 Property**
   - Go to [Google Analytics](https://analytics.google.com/)
   - Create a new GA4 property
   - Get your `G-XXXXXXXXXX` tracking ID

2. **Configure Tracking**
   ```env
   GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX
   GOOGLE_ANALYTICS_ENABLED=true
   ```

3. **Tracked Events**
   - Page views by type (homepage, faculty profiles, university profiles)
   - Faculty profile views
   - University profile views
   - Search queries and results
   - User engagement metrics

4. **Custom Events**
   ```javascript
   // Track custom events
   window.FacultyFinderAnalytics.trackFacultyView('CA-ON-002-00001', 'CA-ON-002');
   window.FacultyFinderAnalytics.trackSearch('machine learning', 'faculty', 25);
   ```

## 📊 Database Schema

The application uses PostgreSQL with the following main tables:

- `universities`: University information
- `faculties`: Faculty member profiles
- `publications`: Academic publications
- `users`: User accounts and authentication
- `admin_permissions`: Role-based access control

## 🔧 Development

### Project Structure

```
FacultyFinder/
├── webapp/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── oauth.py             # Authentication
│   ├── static/              # Static files (CSS, JS, HTML)
│   └── templates/           # Jinja2 templates
├── data/                    # Data files and imports
├── scripts/                 # Utility scripts
└── database/                # Database schemas
```

### Key Components

- **FastAPI Backend**: High-performance async API
- **Jinja2 Templates**: Server-side rendering for admin pages
- **Static HTML + JS**: Client-side rendering for main pages
- **Bootstrap 5**: Modern responsive UI framework
- **Custom CSS Themes**: Light/dark mode support

### Adding New Features

1. **API Endpoints**: Add to `webapp/main.py`
2. **Database Changes**: Update schema files in `database/`
3. **Frontend Pages**: Add to `webapp/static/`
4. **Admin Features**: Add templates to `webapp/templates/admin/`

## 🔒 Security

The application includes several security features:

- **Environment-based configuration**: Sensitive data in environment variables
- **OAuth integration**: Google OAuth for authentication
- **Role-based permissions**: Granular admin access control
- **Input validation**: Pydantic models for API validation
- **CORS protection**: Configurable cross-origin requests

## 📈 Analytics & Monitoring

### Google Analytics Integration

- **Automatic tracking**: Page views, user interactions
- **Custom events**: Faculty views, searches, downloads
- **Performance metrics**: Page load times, user engagement
- **Privacy-compliant**: IP anonymization, no personal data

### Admin Dashboard

- **System statistics**: Users, faculty, publications
- **Database management**: Direct database operations
- **User management**: Role assignment and permissions
- **Analytics overview**: Usage metrics and trends

## 🚀 Deployment

### Production Deployment

1. **Environment Setup**
   ```bash
   # Set production environment variables
   export DB_HOST=your-production-db
   export GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX
   export SECRET_KEY=your-production-secret
   ```

2. **Database Migration**
   ```bash
   # Run database setup scripts
   python scripts/setup_database.py
   ```

3. **Start Application**
   ```bash
   # Production server with multiple workers
   uvicorn webapp.main:app --host 0.0.0.0 --port 8000 --workers 4
   ```

### Docker Deployment

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "webapp.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📄 API Documentation

Once running, visit:
- **Interactive API Docs**: `http://localhost:8000/api/docs`
- **ReDoc Documentation**: `http://localhost:8000/api/redoc`

### Key API Endpoints

```
GET  /api/v1/faculties              # Search faculty
GET  /api/v1/universities           # List universities
GET  /api/v1/professor/{id}         # Faculty profile
GET  /api/v1/university/{code}      # University profile
POST /api/v1/search                 # Advanced search
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support, questions, or suggestions:

- **Email**: support@facultyfinder.io
- **GitHub Issues**: [Create an issue](https://github.com/yourusername/FacultyFinder/issues)
- **Documentation**: [Full documentation](https://docs.facultyfinder.io)

## 🙏 Acknowledgments

- Faculty data sourced from university websites and academic databases
- Publication data from PubMed, OpenAlex, and OpenCitations
- Built with FastAPI, Bootstrap, and modern web technologies

---

**FacultyFinder** - Connecting researchers worldwide 🌍