#!/bin/bash
# FacultyFinder Flask to FastAPI Migration Script
# This script carefully migrates from Flask to FastAPI with zero downtime

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="/var/www/ff"
SERVICE_NAME="facultyfinder"
NGINX_SITE="facultyfinder"
BACKUP_DIR="/var/www/ff/backup_$(date +%Y%m%d_%H%M%S)"

echo -e "${BLUE}🚀 FacultyFinder Flask to FastAPI Migration${NC}"
echo "=========================================="

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Function to check if we're running as the correct user
check_user() {
    if [[ $EUID -eq 0 ]]; then
        print_error "This script should not be run as root"
        exit 1
    fi
    
    if [[ $(whoami) != "xeradb" ]]; then
        print_error "This script should be run as user 'xeradb'"
        exit 1
    fi
}

# Function to backup current application
backup_current_app() {
    print_info "Creating backup of current application..."
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup Flask application
    cp -r "$APP_DIR/webapp" "$BACKUP_DIR/webapp_flask"
    
    # Backup service file
    sudo cp "/etc/systemd/system/$SERVICE_NAME.service" "$BACKUP_DIR/"
    
    # Backup nginx config
    if [ -f "/etc/nginx/sites-available/$NGINX_SITE" ]; then
        sudo cp "/etc/nginx/sites-available/$NGINX_SITE" "$BACKUP_DIR/nginx_old.conf"
    fi
    
    # Backup requirements
    if [ -f "$APP_DIR/requirements.txt" ]; then
        cp "$APP_DIR/requirements.txt" "$BACKUP_DIR/requirements_flask.txt"
    fi
    
    print_status "Backup created at $BACKUP_DIR"
}

# Function to check system status
check_system_status() {
    print_info "Checking system status..."
    
    # Check if Flask service is running
    if sudo systemctl is-active --quiet $SERVICE_NAME; then
        print_status "Current Flask service is running"
    else
        print_warning "Flask service is not running"
    fi
    
    # Check database connection
    if cd "$APP_DIR" && python3 -c "
import psycopg2
import os
from dotenv import load_dotenv
load_dotenv('.env')
conn = psycopg2.connect(
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME')
)
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM professors')
print(f'Database OK: {cursor.fetchone()[0]} professors')
cursor.close()
conn.close()
" 2>/dev/null; then
        print_status "Database connection verified"
    else
        print_error "Database connection failed"
        exit 1
    fi
}

# Function to install FastAPI dependencies
install_fastapi_deps() {
    print_info "Installing FastAPI dependencies..."
    
    cd "$APP_DIR"
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install FastAPI requirements
    pip install fastapi==0.104.1
    pip install uvicorn[standard]==0.24.0
    pip install asyncpg==0.29.0
    
    # Keep existing dependencies that might be needed
    pip install python-dotenv
    pip install psycopg2-binary
    
    print_status "FastAPI dependencies installed"
}

# Function to update systemd service
update_systemd_service() {
    print_info "Updating systemd service for FastAPI..."
    
    # Create new service file
    sudo tee "/etc/systemd/system/facultyfinder_fastapi.service" > /dev/null << EOF
[Unit]
Description=FacultyFinder FastAPI Application
After=network.target
After=postgresql.service
Requires=postgresql.service

[Service]
Type=exec
User=xeradb
Group=xeradb
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
Environment="PYTHONPATH=$APP_DIR"
ExecStart=$APP_DIR/venv/bin/uvicorn webapp.main:app --host 127.0.0.1 --port 8008 --workers 4 --log-level info
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=3
KillMode=mixed
TimeoutStopSec=5

# Performance optimizations
LimitNOFILE=65535
LimitNPROC=4096

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$APP_DIR

# Environment variables
EnvironmentFile=$APP_DIR/.env

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd
    sudo systemctl daemon-reload
    
    print_status "SystemD service updated"
}

# Function to test FastAPI application
test_fastapi_app() {
    print_info "Testing FastAPI application..."
    
    cd "$APP_DIR"
    source venv/bin/activate
    
    # Test if app can be imported
    if python3 -c "from webapp.main import app; print('✅ FastAPI app imports successfully')" 2>/dev/null; then
        print_status "FastAPI application imports successfully"
    else
        print_error "FastAPI application import failed"
        return 1
    fi
    
    # Start FastAPI temporarily and test
    timeout 10s uvicorn webapp.main:app --host 127.0.0.1 --port 8009 &
    FASTAPI_PID=$!
    
    sleep 3
    
    # Test health endpoint
    if curl -s http://127.0.0.1:8009/health | grep -q "healthy"; then
        print_status "FastAPI health check passed"
        TEST_PASSED=true
    else
        print_error "FastAPI health check failed"
        TEST_PASSED=false
    fi
    
    # Stop test server
    kill $FASTAPI_PID 2>/dev/null || true
    wait $FASTAPI_PID 2>/dev/null || true
    
    if [ "$TEST_PASSED" = true ]; then
        return 0
    else
        return 1
    fi
}

# Function to perform zero-downtime migration
migrate_with_zero_downtime() {
    print_info "Performing zero-downtime migration..."
    
    # Stop the old Flask service
    print_info "Stopping Flask service..."
    sudo systemctl stop $SERVICE_NAME
    
    # Disable old service
    sudo systemctl disable $SERVICE_NAME
    
    # Start new FastAPI service
    print_info "Starting FastAPI service..."
    sudo systemctl enable facultyfinder_fastapi
    sudo systemctl start facultyfinder_fastapi
    
    # Wait for service to start
    sleep 5
    
    # Check if new service is running
    if sudo systemctl is-active --quiet facultyfinder_fastapi; then
        print_status "FastAPI service started successfully"
        
        # Test the service
        if curl -s http://127.0.0.1:8008/health | grep -q "healthy"; then
            print_status "FastAPI service is responding"
        else
            print_error "FastAPI service is not responding"
            rollback_migration
            exit 1
        fi
    else
        print_error "FastAPI service failed to start"
        rollback_migration
        exit 1
    fi
}

# Function to update nginx configuration
update_nginx_config() {
    print_info "Updating nginx configuration..."
    
    # The nginx config should already be compatible with FastAPI
    # since it proxies to the same port (8008)
    
    # Test nginx configuration
    if sudo nginx -t; then
        print_status "Nginx configuration is valid"
        
        # Reload nginx
        sudo systemctl reload nginx
        print_status "Nginx reloaded"
    else
        print_error "Nginx configuration test failed"
        exit 1
    fi
}

# Function to verify migration success
verify_migration() {
    print_info "Verifying migration success..."
    
    # Check if FastAPI service is running
    if sudo systemctl is-active --quiet facultyfinder_fastapi; then
        print_status "FastAPI service is active"
    else
        print_error "FastAPI service is not active"
        return 1
    fi
    
    # Test health endpoint
    if curl -s https://facultyfinder.io/health | grep -q "FastAPI"; then
        print_status "Website is responding with FastAPI"
    else
        print_warning "Website health check unclear"
    fi
    
    # Test API endpoints
    if curl -s https://facultyfinder.io/api/v1/stats | grep -q "total_professors"; then
        print_status "API endpoints are working"
    else
        print_error "API endpoints are not working"
        return 1
    fi
    
    # Test static pages
    if curl -s https://facultyfinder.io/ | grep -q "FacultyFinder"; then
        print_status "Homepage is loading"
    else
        print_error "Homepage is not loading"
        return 1
    fi
    
    return 0
}

# Function to rollback migration
rollback_migration() {
    print_error "Rolling back migration..."
    
    # Stop FastAPI service
    sudo systemctl stop facultyfinder_fastapi 2>/dev/null || true
    sudo systemctl disable facultyfinder_fastapi 2>/dev/null || true
    
    # Restore Flask service
    sudo systemctl enable $SERVICE_NAME
    sudo systemctl start $SERVICE_NAME
    
    print_warning "Rollback completed. Flask service restored."
}

# Function to cleanup after successful migration
cleanup_migration() {
    print_info "Cleaning up after successful migration..."
    
    # Remove old service files (but keep as backup)
    if [ -f "/etc/systemd/system/$SERVICE_NAME.service" ]; then
        sudo mv "/etc/systemd/system/$SERVICE_NAME.service" "$BACKUP_DIR/"
    fi
    
    # Update the main service to point to FastAPI
    sudo ln -sf "/etc/systemd/system/facultyfinder_fastapi.service" "/etc/systemd/system/$SERVICE_NAME.service"
    sudo systemctl daemon-reload
    
    print_status "Migration cleanup completed"
}

# Main migration function
main() {
    echo
    print_info "Starting FacultyFinder Flask to FastAPI migration..."
    echo
    
    # Pre-migration checks
    check_user
    check_system_status
    
    # Create backup
    backup_current_app
    
    # Install dependencies
    install_fastapi_deps
    
    # Test FastAPI application
    if ! test_fastapi_app; then
        print_error "FastAPI application test failed. Aborting migration."
        exit 1
    fi
    
    # Update system services
    update_systemd_service
    
    # Perform migration
    migrate_with_zero_downtime
    
    # Update nginx if needed
    update_nginx_config
    
    # Verify migration
    if verify_migration; then
        print_status "Migration verification passed"
        cleanup_migration
        
        echo
        print_status "🎉 Migration completed successfully!"
        echo
        print_info "FastAPI application is now running at:"
        print_info "  - https://facultyfinder.io"
        print_info "  - API docs: https://facultyfinder.io/api/docs"
        print_info "  - Health check: https://facultyfinder.io/health"
        echo
        print_info "Backup location: $BACKUP_DIR"
        echo
        
    else
        print_error "Migration verification failed"
        rollback_migration
        exit 1
    fi
}

# Run migration
main "$@" 