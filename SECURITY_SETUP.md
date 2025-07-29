# 🔒 FacultyFinder Security Setup

## What Was Done for Security

To protect sensitive deployment information, the following files have been **EXCLUDED** from the public GitHub repository:

### 🚫 Excluded Files (Private/Local Only)

#### Deployment Guides with Credentials
- `DEPLOYMENT_GUIDE.md` - Contains server passwords, API keys, database credentials
- `QUICK_DEPLOYMENT.md` - Contains production configuration secrets
- `EMAIL_SETUP_GUIDE.md` - Contains SMTP passwords and email credentials
- `AI_INTEGRATION_GUIDE.md` - Contains AI API keys (OpenAI, Anthropic, etc.)
- `CRYPTOCURRENCY_PAYMENT_GUIDE.md` - Contains crypto payment API keys
- `GOOGLE_OAUTH_SETUP_GUIDE.md` - Contains OAuth client secrets
- `STRIPE_INTEGRATION.md` - Contains Stripe API keys and webhooks
- All other `*GUIDE*.md` files

#### VPS & Production Scripts
- `deploy.sh` - Contains production server commands and paths
- `fix_python312_vps.sh` - Contains VPS-specific commands
- `vps_emergency_install.md` - Contains server access information
- All `vps_*.sh` and `vps_*.md` files

#### Production Configuration
- `requirements_python312.txt` - VPS-specific package versions
- `requirements_vps.txt` - Production requirements
- `requirements_publications.txt` - Contains API endpoint configurations

#### Automated Scripts & Migration Tools
- `automated_publication_updater.py` - Contains API keys and database paths
- `migrate_*.py` - Contains database migration scripts
- `test_cv_analysis.py` - Contains test API keys

### ✅ What's Safe in Public Repository

#### Core Application Code
- `webapp/` directory - All Flask application code
- `templates/` and `static/` - Frontend code and assets
- `requirements.txt` - Core dependencies (no versions/credentials)

#### Public Documentation
- `README.md` - Public project overview (references to private guides removed)
- `LICENSE` - Open source license
- `FacultyFinder_guide.md` - Public user guide

#### Data Files
- `data/` directory - Public research data (PubMed, university info)
- `Faculty/` directory - Scraped public faculty data

### 🔧 For Deployment

Keep your private deployment files in a separate, secure location:

```
/path/to/private/facultyfinder-deployment/
├── DEPLOYMENT_GUIDE.md
├── deploy.sh
├── .env.production
├── vps_scripts/
└── credentials/
```

### 🛡️ Security Benefits

1. **API Keys Protected** - No accidental exposure of OpenAI, Stripe, etc. keys
2. **Server Credentials Safe** - Database passwords, SSH keys remain private
3. **Production Configs Secure** - VPS paths, domains, certificates not exposed
4. **Clean Open Source** - Public repo contains only the application code

### 📝 For Developers

When working with FacultyFinder:
1. **Public repo**: Clone for the application code
2. **Private setup**: Get deployment guides separately
3. **Environment**: Create your own `.env` with your API keys
4. **Production**: Use separate, private deployment repository

This separation ensures the open-source application remains clean while keeping sensitive deployment information secure. 