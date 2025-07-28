# FacultyFinder VPS Deployment Guide

This guide provides step-by-step instructions for deploying FacultyFinder to your VPS with PostgreSQL, Nginx, and SSL.

## Server Information
- **IP**: 91.99.161.136
- **Username**: xeradb
- **Project Path**: /var/www/ff
- **Database**: ff_production
- **DB User**: ff_user
- **Port**: 8008

## Prerequisites

### 1. Update System
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git nginx postgresql postgresql-contrib supervisor
```

### 2. Create Project Directory
```bash
sudo mkdir -p /var/www/ff
sudo chown xeradb:xeradb /var/www/ff
cd /var/www/ff
```

## Database Setup

### 1. Configure PostgreSQL
```bash
# Switch to postgres user
sudo -u postgres psql

-- Create database and user
CREATE DATABASE ff_production;
CREATE USER ff_user WITH PASSWORD 'Choxos10203040';
GRANT ALL PRIVILEGES ON DATABASE ff_production TO ff_user;
ALTER USER ff_user CREATEDB;
\q
```

### 2. Configure PostgreSQL Access
```bash
# Edit PostgreSQL configuration
sudo nano /etc/postgresql/*/main/pg_hba.conf

# Add this line before other rules:
local   ff_production   ff_user                md5

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### 3. Test Database Connection
```bash
psql -h localhost -U ff_user -d ff_production
# Enter password: Choxos10203040
```

## Application Deployment

### 1. Clone and Setup Project
```bash
cd /var/www/ff
git clone https://github.com/xeradb/FacultyFinder.git .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install psycopg2-binary gunicorn
```

### 2. Environment Configuration
```bash
# Create environment file
cat > /var/www/ff/.env << EOF
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_USER=ff_user
DB_PASSWORD=Choxos10203040
DB_NAME=ff_production

# Application Configuration
APP_PORT=8008
APP_HOST=0.0.0.0

# Stripe Configuration (add your keys)
STRIPE_PUBLISHABLE_KEY=pk_live_your_key_here
STRIPE_SECRET_KEY=sk_live_your_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
EOF

# Secure the environment file
chmod 600 /var/www/ff/.env
```

### 3. Update Application for Production
```bash
# Create production configuration
cat > /var/www/ff/webapp/config.py << EOF
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/var/www/ff/.env')

class ProductionConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # Database Configuration
    DB_CONFIG = {
        'host': os.environ.get('DB_HOST', 'localhost'),
        'port': int(os.environ.get('DB_PORT', 5432)),
        'user': os.environ.get('DB_USER'),
        'password': os.environ.get('DB_PASSWORD'),
        'database': os.environ.get('DB_NAME')
    }
    
    # Stripe Configuration
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    # Application Configuration
    DEBUG = False
    TESTING = False
    PORT = int(os.environ.get('APP_PORT', 8008))
    HOST = os.environ.get('APP_HOST', '0.0.0.0')
EOF
```

### 4. Initialize Production Database
```bash
cd /var/www/ff
source venv/bin/activate

# Modify data loader for PostgreSQL
python3 -c "
from scripts.data_loader import DataLoader
from webapp.config import ProductionConfig

# Initialize with production config
loader = DataLoader()
loader.dev_mode = False
loader.config = ProductionConfig.DB_CONFIG

# Load data
loader.initialize_database()
loader.load_universities()
loader.load_faculty()
loader.extract_research_areas()
loader.load_scimago_journals(sample_size=5000)  # More journals for production

stats = loader.get_database_stats()
print(f'Production database initialized: {stats}')
loader.close()
"
```

## Nginx Configuration

### 1. Create Nginx Site Configuration
```bash
sudo cat > /etc/nginx/sites-available/facultyfinder << EOF
server {
    listen 80;
    server_name 91.99.161.136;  # Replace with your domain when available
    
    # Redirect to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name 91.99.161.136;  # Replace with your domain
    
    # SSL Configuration (replace with your certificates)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # SSL Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    
    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # Static files
    location /static {
        alias /var/www/ff/webapp/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Main application
    location / {
        proxy_pass http://127.0.0.1:8008;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8008/health;
        access_log off;
    }
}
EOF

# Enable the site
sudo ln -sf /etc/nginx/sites-available/facultyfinder /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Systemd Service Configuration

### 1. Create Systemd Service
```bash
sudo cat > /etc/systemd/system/facultyfinder.service << EOF
[Unit]
Description=FacultyFinder Flask Application
After=network.target postgresql.service

[Service]
Type=simple
User=xeradb
Group=xeradb
WorkingDirectory=/var/www/ff
Environment=PATH=/var/www/ff/venv/bin
EnvironmentFile=/var/www/ff/.env
ExecStart=/var/www/ff/venv/bin/gunicorn --bind 127.0.0.1:8008 --workers 3 --timeout 60 --max-requests 1000 --max-requests-jitter 100 webapp.wsgi:application
ExecReload=/bin/kill -HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable facultyfinder
sudo systemctl start facultyfinder
sudo systemctl status facultyfinder
```

### 2. Create WSGI Entry Point
```bash
cat > /var/www/ff/webapp/wsgi.py << EOF
#!/usr/bin/env python3
"""WSGI entry point for FacultyFinder production deployment"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/var/www/ff/.env')

# Add project directory to Python path
sys.path.insert(0, '/var/www/ff')
sys.path.insert(0, '/var/www/ff/webapp')

from app import app as application

if __name__ == "__main__":
    application.run()
EOF
```

## SSL Certificate Setup

### 1. Install Certbot
```bash
sudo apt install -y certbot python3-certbot-nginx
```

### 2. Obtain SSL Certificate
```bash
# Replace with your actual domain
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# For IP-only setup (not recommended for production)
# You'll need to configure SSL manually or use a self-signed certificate
```

### 3. Auto-renewal Setup
```bash
# Test renewal
sudo certbot renew --dry-run

# Check cron job
sudo crontab -l | grep certbot
```

## Monitoring and Logging

### 1. Setup Log Rotation
```bash
sudo cat > /etc/logrotate.d/facultyfinder << EOF
/var/www/ff/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    notifempty
    create 644 xeradb xeradb
    postrotate
        systemctl reload facultyfinder
    endscript
}
EOF

# Create logs directory
mkdir -p /var/www/ff/logs
```

### 2. Setup Monitoring
```bash
# Create monitoring script
cat > /var/www/ff/scripts/health_check.sh << EOF
#!/bin/bash
# Health check script for FacultyFinder

URL="http://127.0.0.1:8008/health"
RESPONSE=\$(curl -s -o /dev/null -w "%{http_code}" \$URL)

if [ \$RESPONSE -eq 200 ]; then
    echo "FacultyFinder is healthy"
    exit 0
else
    echo "FacultyFinder is unhealthy (HTTP \$RESPONSE)"
    # Restart service if unhealthy
    sudo systemctl restart facultyfinder
    exit 1
fi
EOF

chmod +x /var/www/ff/scripts/health_check.sh

# Add to crontab
(crontab -l 2>/dev/null; echo "*/5 * * * * /var/www/ff/scripts/health_check.sh >> /var/www/ff/logs/health_check.log 2>&1") | crontab -
```

## Firewall Configuration

### 1. Configure UFW
```bash
# Allow SSH, HTTP, HTTPS, and custom port
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 8008
sudo ufw --force enable
sudo ufw status
```

## Backup Configuration

### 1. Database Backup Script
```bash
cat > /var/www/ff/scripts/backup_db.sh << EOF
#!/bin/bash
# Database backup script

DATE=\$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/www/ff/backups"
DB_NAME="ff_production"
DB_USER="ff_user"

mkdir -p \$BACKUP_DIR

# Create database backup
PGPASSWORD="Choxos10203040" pg_dump -h localhost -U \$DB_USER \$DB_NAME > \$BACKUP_DIR/ff_backup_\$DATE.sql

# Keep only last 7 days of backups
find \$BACKUP_DIR -name "ff_backup_*.sql" -mtime +7 -delete

echo "Backup completed: ff_backup_\$DATE.sql"
EOF

chmod +x /var/www/ff/scripts/backup_db.sh

# Schedule daily backups
(crontab -l 2>/dev/null; echo "0 2 * * * /var/www/ff/scripts/backup_db.sh >> /var/www/ff/logs/backup.log 2>&1") | crontab -
```

## Verification Steps

### 1. Check All Services
```bash
# Check PostgreSQL
sudo systemctl status postgresql

# Check Nginx
sudo systemctl status nginx
sudo nginx -t

# Check FacultyFinder
sudo systemctl status facultyfinder

# Check logs
sudo journalctl -u facultyfinder -f
tail -f /var/www/ff/logs/gunicorn.log
```

### 2. Test Application
```bash
# Test local connection
curl -I http://127.0.0.1:8008/

# Test through Nginx
curl -I http://91.99.161.136/

# Test HTTPS (if configured)
curl -I https://91.99.161.136/
```

## Maintenance Commands

### Update Application
```bash
cd /var/www/ff
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart facultyfinder
```

### View Logs
```bash
# Application logs
sudo journalctl -u facultyfinder -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Database logs
sudo tail -f /var/log/postgresql/postgresql-*-main.log
```

### Performance Monitoring
```bash
# Check system resources
htop
df -h
free -h

# Check database connections
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity WHERE datname='ff_production';"

# Check application performance
curl -w "@curl-format.txt" -o /dev/null -s http://127.0.0.1:8008/
```

## Security Recommendations

1. **Change default passwords** immediately after setup
2. **Restrict SSH access** to key-based authentication only
3. **Regular updates**: Keep system and dependencies updated
4. **Monitor logs** for suspicious activity
5. **Backup regularly** and test restore procedures
6. **Use a proper domain** instead of IP address for SSL
7. **Implement rate limiting** in Nginx for API endpoints
8. **Database security**: Regular vacuum and analyze operations

## Troubleshooting

### Common Issues

1. **Service won't start**:
   ```bash
   sudo journalctl -u facultyfinder -n 50
   ```

2. **Database connection issues**:
   ```bash
   psql -h localhost -U ff_user -d ff_production
   ```

3. **Permission issues**:
   ```bash
   sudo chown -R xeradb:xeradb /var/www/ff
   ```

4. **Port conflicts**:
   ```bash
   sudo netstat -tlnp | grep 8008
   ```

This completes the deployment setup. The application should now be accessible at `http://91.99.161.136/` or `https://91.99.161.136/` if SSL is configured. 