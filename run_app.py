#!/usr/bin/env python3
"""
FacultyFinder Application Launcher
Simple script to run the Flask application with proper configuration
"""

import os
import sys
import subprocess

def main():
    """Main launcher function"""
    # Set environment variables
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_DEBUG'] = '1'
    
    # Change to webapp directory
    webapp_dir = os.path.join(os.path.dirname(__file__), 'webapp')
    os.chdir(webapp_dir)
    
    print("Starting FacultyFinder application...")
    print("Access the application at: http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    
    try:
        # Run the Flask application
        subprocess.run([sys.executable, 'app.py'])
    except KeyboardInterrupt:
        print("\nShutting down FacultyFinder...")
    except Exception as e:
        print(f"Error starting application: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main()) 