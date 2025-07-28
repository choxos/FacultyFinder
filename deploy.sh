#!/bin/bash

# FacultyFinder VPS Deployment Script
# Usage: ./deploy.sh [production|staging]

set -e  # Exit on any error

# Configuration
SERVER_IP="91.99.161.136"
SERVER_USER="xeradb"
PROJECT_PATH="/var/www/ff"
SERVICE_NAME="facultyfinder"
ENVIRONMENT=${1:-production}

echo "🚀 Starting FacultyFinder deployment to $ENVIRONMENT environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're deploying from the correct directory
if [[ ! -f "webapp/app.py" ]]; then
    print_error "Please run this script from the FacultyFinder root directory"
    exit 1
fi

# Check if SSH key is available
if ! ssh -o ConnectTimeout=5 -o BatchMode=yes $SERVER_USER@$SERVER_IP exit 2>/dev/null; then
    print_error "Cannot connect to server. Please ensure SSH key authentication is set up."
    exit 1
fi

print_status "Connected to server successfully"

# Backup current deployment
print_status "Creating backup of current deployment..."
ssh $SERVER_USER@$SERVER_IP "
    if [ -d $PROJECT_PATH ]; then
        sudo cp -r $PROJECT_PATH ${PROJECT_PATH}_backup_\$(date +%Y%m%d_%H%M%S)
        echo 'Backup created successfully'
    else
        echo 'No existing deployment to backup'
    fi
"

# Sync files to server (excluding sensitive files)
print_status "Syncing files to server..."
rsync -avz --delete \
    --exclude '.git' \
    --exclude '.env' \
    --exclude 'database/facultyfinder_dev.db' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude 'logs/' \
    --exclude 'backups/' \
    --exclude 'venv/' \
    . $SERVER_USER@$SERVER_IP:$PROJECT_PATH/

# Execute deployment commands on server
print_status "Executing deployment commands on server..."
ssh $SERVER_USER@$SERVER_IP "
    set -e
    cd $PROJECT_PATH
    
    # Create necessary directories
    mkdir -p logs backups
    
    # Set up virtual environment
    if [ ! -d 'venv' ]; then
        echo 'Creating virtual environment...'
        python3 -m venv venv
    fi
    
    # Activate virtual environment and install dependencies
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install psycopg2-binary gunicorn python-dotenv
    
    # Check if .env file exists
    if [ ! -f '.env' ]; then
        echo '⚠️  Warning: .env file not found. Please create it manually.'
        echo 'Template:'
        cat << 'EOF'
FLASK_ENV=production
SECRET_KEY=your_secret_key_here
DB_HOST=localhost
DB_PORT=5432
DB_USER=ff_user
DB_PASSWORD=Choxos10203040
DB_NAME=ff_production
APP_PORT=8008
APP_HOST=0.0.0.0
STRIPE_PUBLISHABLE_KEY=pk_live_your_key
STRIPE_SECRET_KEY=sk_live_your_key
STRIPE_WEBHOOK_SECRET=whsec_your_secret
EOF
    fi
    
    # Set proper permissions
    chown -R xeradb:xeradb $PROJECT_PATH
    chmod 600 .env 2>/dev/null || echo '.env file not found'
    chmod +x scripts/*.sh 2>/dev/null || echo 'No executable scripts found'
    
    # Test database connection
    echo 'Testing database connection...'
    python3 -c \"
import psycopg2
try:
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        user='ff_user',
        password='Choxos10203040',
        database='ff_production'
    )
    print('✅ Database connection successful')
    conn.close()
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
\"
    
    # Initialize/update database if needed
    echo 'Updating database schema...'
    python3 -c \"
import sys
sys.path.append('$PROJECT_PATH')
from scripts.data_loader import DataLoader
from webapp.config import ProductionConfig

try:
    loader = DataLoader()
    loader.dev_mode = False
    loader.config = ProductionConfig.DB_CONFIG
    
    # Check if tables exist, if not initialize
    result = loader.execute_query('SELECT COUNT(*) FROM information_schema.tables WHERE table_name = \\\"professors\\\"')
    if not result or result[0][0] == 0:
        print('Initializing database...')
        loader.initialize_database()
        loader.load_universities()
        loader.load_faculty()
        loader.extract_research_areas()
    else:
        print('Database already initialized')
    
    loader.close()
    print('✅ Database update completed')
except Exception as e:
    print(f'❌ Database update failed: {e}')
    exit(1)
\"
"

# Update systemd service
print_status "Updating systemd service..."
ssh $SERVER_USER@$SERVER_IP "
    # Create/update systemd service file
    sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null << 'EOF'
[Unit]
Description=FacultyFinder Flask Application
After=network.target postgresql.service

[Service]
Type=simple
User=xeradb
Group=xeradb
WorkingDirectory=$PROJECT_PATH
Environment=PATH=$PROJECT_PATH/venv/bin
EnvironmentFile=$PROJECT_PATH/.env
ExecStart=$PROJECT_PATH/venv/bin/gunicorn --bind 127.0.0.1:8008 --workers 3 --timeout 60 --max-requests 1000 --max-requests-jitter 100 --access-logfile $PROJECT_PATH/logs/access.log --error-logfile $PROJECT_PATH/logs/error.log webapp.wsgi:application
ExecReload=/bin/kill -HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
    
    # Create WSGI entry point if it doesn't exist
    if [ ! -f webapp/wsgi.py ]; then
        cat > webapp/wsgi.py << 'EOF'
#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv('$PROJECT_PATH/.env')

# Add project to path
sys.path.insert(0, '$PROJECT_PATH')
sys.path.insert(0, '$PROJECT_PATH/webapp')

# Import application
from app import app as application

if __name__ == '__main__':
    application.run()
EOF
    fi
    
    # Reload systemd and restart service
    sudo systemctl daemon-reload
    sudo systemctl enable $SERVICE_NAME
    
    # Stop service gracefully
    sudo systemctl stop $SERVICE_NAME || true
    sleep 2
    
    # Start service
    sudo systemctl start $SERVICE_NAME
    
    # Check service status
    if sudo systemctl is-active --quiet $SERVICE_NAME; then
        echo '✅ Service started successfully'
    else
        echo '❌ Service failed to start'
        sudo systemctl status $SERVICE_NAME
        exit 1
    fi
"

# Update Nginx configuration if needed
print_status "Checking Nginx configuration..."
ssh $SERVER_USER@$SERVER_IP "
    # Check if our site is enabled
    if [ ! -f /etc/nginx/sites-enabled/facultyfinder ]; then
        echo 'ℹ️  Nginx site not configured. Please run the Nginx setup from DEPLOYMENT_GUIDE.md'
    else
        # Test nginx configuration
        sudo nginx -t && sudo systemctl reload nginx
        echo '✅ Nginx configuration updated'
    fi
"

# Health check
print_status "Performing health check..."
sleep 5  # Give the service time to start

ssh $SERVER_USER@$SERVER_IP "
    # Check if application is responding
    for i in {1..5}; do
        if curl -f -s http://127.0.0.1:8008/ > /dev/null; then
            echo '✅ Application is responding'
            break
        else
            echo \"Attempt \$i: Application not responding yet...\"
            sleep 2
        fi
        
        if [ \$i -eq 5 ]; then
            echo '❌ Application health check failed'
            echo 'Service status:'
            sudo systemctl status $SERVICE_NAME
            echo 'Recent logs:'
            sudo journalctl -u $SERVICE_NAME -n 20 --no-pager
            exit 1
        fi
    done
"

# Final verification
print_status "Final verification..."
if curl -f -s -I http://$SERVER_IP/ | grep -q "200 OK\|301\|302"; then
    print_status "✅ Deployment completed successfully!"
    print_status "🌐 Application is accessible at: http://$SERVER_IP/"
    
    # Display useful commands
    echo ""
    echo "📝 Useful commands for management:"
    echo "   View logs: ssh $SERVER_USER@$SERVER_IP 'sudo journalctl -u $SERVICE_NAME -f'"
    echo "   Restart:   ssh $SERVER_USER@$SERVER_IP 'sudo systemctl restart $SERVICE_NAME'"
    echo "   Status:    ssh $SERVER_USER@$SERVER_IP 'sudo systemctl status $SERVICE_NAME'"
    echo "   Stop:      ssh $SERVER_USER@$SERVER_IP 'sudo systemctl stop $SERVICE_NAME'"
    echo ""
else
    print_error "❌ Deployment verification failed"
    print_error "The application may not be accessible externally"
    print_warning "Check Nginx configuration and firewall settings"
    exit 1
fi

print_status "🎉 Deployment complete!" 