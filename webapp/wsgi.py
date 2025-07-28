#!/usr/bin/env python3
"""
WSGI entry point for FacultyFinder production deployment
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/var/www/ff/.env')

# Add project directory to Python path
sys.path.insert(0, '/var/www/ff')
sys.path.insert(0, '/var/www/ff/webapp')

# Set production environment
os.environ.setdefault('FLASK_ENV', 'production')

# Import application
from app import app as application

if __name__ == "__main__":
    application.run(
        host=os.environ.get('APP_HOST', '0.0.0.0'),
        port=int(os.environ.get('APP_PORT', 8008)),
        debug=False
    ) 