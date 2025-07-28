# FacultyFinder Deployment Guide

Complete guide for deploying FacultyFinder to your VPS with domain management and payment integration.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [DNS Configuration (facultyfinder.io)](#dns-configuration)
3. [VPS Preparation](#vps-preparation)
4. [PostgreSQL Setup](#postgresql-setup)
5. [Application Deployment](#application-deployment)
6. [Nginx Configuration](#nginx-configuration)
7. [SSL Certificate Setup](#ssl-certificate-setup)
8. [Stripe Integration Setup](#stripe-integration-setup)
9. [Systemd Service](#systemd-service)
10. [Monitoring & Logs](#monitoring--logs)
11. [Security Configuration](#security-configuration)
12. [Database Backups](#database-backups)
13. [Testing & Verification](#testing--verification)
14. [Maintenance](#maintenance)

## Prerequisites

### Required Information
- **VPS Details**:
  - IP: `91.99.161.136`
  - Username: `xeradb`
  - Project folder: `/var/www/ff`
  - PostgreSQL database: `ff_production`
  - PostgreSQL user: `ff_user`
  - PostgreSQL password: `Choxos10203040`
  - Application port: `8008`

### Required Accounts
- Domain registrar access for `facultyfinder.io`
- Stripe account for payment processing
- SSL certificate (Let's Encrypt - free)

## DNS Configuration

### Setting up facultyfinder.io DNS

#### 1. Access Your Domain Registrar
Log into your domain registrar where you purchased `facultyfinder.io`.

#### 2. Configure DNS Records
Add the following DNS records:

```bash
# A Record (Main domain)
Type: A
Name: @
Value: 91.99.161.136
TTL: 300 (or Auto)

# A Record (www subdomain)
Type: A
Name: www
Value: 91.99.161.136
TTL: 300

# Optional: Admin subdomain
Type: A
Name: admin
Value: 91.99.161.136
TTL: 300

# Optional: API subdomain
Type: A
Name: api
Value: 91.99.161.136
TTL: 300
```

#### 3. Email Configuration (Optional)
For professional email addresses:

```bash
# MX Record (if using email hosting)
Type: MX
Name: @
Value: [Your email provider's MX record]
Priority: 10
TTL: 300

# CNAME for email (if using external email service)
Type: CNAME
Name: mail
Value: [Your email provider's domain]
TTL: 300
```

#### 4. Verify DNS Propagation
```bash
# Check from your local machine
nslookup facultyfinder.io
dig facultyfinder.io

# Check from multiple locations
# Use online tools like whatsmydns.net or dnschecker.org
```

**Note**: DNS propagation can take 24-48 hours worldwide, but usually completes within 2-4 hours.

## VPS Preparation

### 1. Connect to VPS
```bash
ssh xeradb@91.99.161.136
```

### 2. Update System
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git nginx postgresql postgresql-contrib python3 python3-pip python3-venv ufw certbot python3-certbot-nginx
```

### 3. Create Project Directory
```bash
sudo mkdir -p /var/www/ff
sudo chown xeradb:xeradb /var/www/ff
cd /var/www/ff
```

## PostgreSQL Setup

### 1. Configure PostgreSQL
```bash
sudo -u postgres psql
```

```sql
-- Create database and user
CREATE DATABASE ff_production;
CREATE USER ff_user WITH PASSWORD 'Choxos10203040';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE ff_production TO ff_user;
ALTER USER ff_user CREATEDB;

-- Exit PostgreSQL
\q
```

### 2. Configure PostgreSQL for Remote Access (if needed)
```bash
# Edit postgresql.conf
sudo nano /etc/postgresql/*/main/postgresql.conf

# Find and modify:
listen_addresses = 'localhost'

# Edit pg_hba.conf
sudo nano /etc/postgresql/*/main/pg_hba.conf

# Add line for local connections:
local   ff_production   ff_user                     md5
```

### 3. Restart PostgreSQL
```bash
sudo systemctl restart postgresql
sudo systemctl enable postgresql
```

### 4. Test Database Connection
```bash
psql -h localhost -U ff_user -d ff_production
# Enter password: Choxos10203040
\q
```

## Application Deployment

### 1. Clone Repository
```bash
cd /var/www/ff
git clone https://github.com/choxos/FacultyFinder.git .
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
pip install gunicorn psycopg2-binary
```

### 4. Create Environment Configuration
```bash
nano .env
```

```bash
# Production Environment Configuration
FLASK_ENV=production
SECRET_KEY=your-super-secure-secret-key-change-this-immediately
DEBUG=False

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_USER=ff_user
DB_PASSWORD=Choxos10203040
DB_NAME=ff_production

# Domain Configuration
DOMAIN_NAME=facultyfinder.io
BASE_URL=https://facultyfinder.io

# Stripe Configuration (Will be configured later)
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Stripe Product IDs (Will be configured later)
STRIPE_AI_ANALYSIS_PRICE_ID=price_...
STRIPE_EXPERT_REVIEW_PRICE_ID=price_...
STRIPE_MONTHLY_UNLIMITED_PRICE_ID=price_...

# AI API Keys (Add your API keys)
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
GOOGLE_API_KEY=your-google-ai-api-key
XAI_API_KEY=your-xai-grok-api-key

# Email Configuration (Optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@facultyfinder.io
MAIL_PASSWORD=your-email-password

# Security Settings
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
PERMANENT_SESSION_LIFETIME=3600

# Rate Limiting
RATELIMIT_STORAGE_URL=redis://localhost:6379
```

### 5. Generate Secret Key
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
# Copy the output and replace 'your-super-secure-secret-key-change-this-immediately' in .env
```

### 6. Initialize Database
```bash
source venv/bin/activate
cd scripts
python3 data_loader.py
```

### 7. Test Application
```bash
cd /var/www/ff
source venv/bin/activate
python3 run_app.py
# Test in another terminal: curl http://localhost:8008
# Stop with Ctrl+C
```

## Nginx Configuration

### 1. Create Nginx Configuration
```bash
sudo nano /etc/nginx/sites-available/facultyfinder
```

```nginx
# FacultyFinder Nginx Configuration
server {
    listen 80;
    server_name facultyfinder.io www.facultyfinder.io;
    
    # Redirect all HTTP traffic to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name facultyfinder.io www.facultyfinder.io;

    # SSL Configuration (will be set up by Certbot)
    ssl_certificate /etc/letsencrypt/live/facultyfinder.io/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/facultyfinder.io/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Root directory for static files
    root /var/www/ff;

    # Client upload size limit
    client_max_body_size 10M;

    # Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied expired no-cache no-store private auth;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/xml+rss
        application/json;

    # Static files
    location /static/ {
        alias /var/www/ff/webapp/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Favicon
    location /favicon.ico {
        alias /var/www/ff/webapp/static/favicon.ico;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Main application
    location / {
        proxy_pass http://127.0.0.1:8008;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8008/health;
        access_log off;
    }

    # Admin subdomain (optional)
    location /admin {
        proxy_pass http://127.0.0.1:8008/admin;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Additional security for admin
        # Uncomment to restrict admin access by IP
        # allow 91.99.161.136;
        # allow YOUR_HOME_IP;
        # deny all;
    }

    # Stripe webhook endpoint
    location /stripe/webhook {
        proxy_pass http://127.0.0.1:8008/stripe/webhook;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Block access to sensitive files
    location ~ /\. {
        deny all;
    }
    
    location ~ \.(env|py|pyc|pyo|log)$ {
        deny all;
    }
}

# Optional: API subdomain
server {
    listen 80;
    server_name api.facultyfinder.io;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.facultyfinder.io;

    ssl_certificate /etc/letsencrypt/live/facultyfinder.io/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/facultyfinder.io/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8008/api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 2. Enable Site
```bash
sudo ln -s /etc/nginx/sites-available/facultyfinder /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## SSL Certificate Setup

### 1. Install SSL Certificate
```bash
# Install certificate for main domain and www subdomain
sudo certbot --nginx -d facultyfinder.io -d www.facultyfinder.io

# If you want API subdomain SSL too:
sudo certbot --nginx -d api.facultyfinder.io
```

### 2. Test SSL Configuration
```bash
sudo certbot certificates
```

### 3. Set up Auto-renewal
```bash
# Test renewal
sudo certbot renew --dry-run

# Auto-renewal is typically set up automatically, but verify:
sudo systemctl status certbot.timer
```

### 4. Verify SSL
Visit `https://facultyfinder.io` and check for:
- ✅ Green padlock in browser
- ✅ Valid certificate
- ✅ HTTP redirects to HTTPS

## Stripe Integration Setup

### 1. Create Stripe Account
1. Go to [stripe.com](https://stripe.com) and create an account
2. Complete account verification process
3. Enable live payments (requires business verification)

### 2. Get API Keys
1. Go to Stripe Dashboard → Developers → API keys
2. Copy the following keys:
   - **Publishable key** (starts with `pk_live_` for production)
   - **Secret key** (starts with `sk_live_` for production)

### 3. Create Products and Prices

#### Create Products in Stripe Dashboard:

**Product 1: AI Faculty Analysis**
```
Name: AI Faculty Analysis
Description: Get personalized faculty recommendations using advanced AI analysis of your CV and research interests
```

**Product 2: Expert Review Service**
```
Name: Expert Faculty Review
Description: Manual review and personalized recommendations by our academic advisors
```

**Product 3: Monthly Unlimited (Optional)**
```
Name: Monthly Unlimited Access
Description: Unlimited AI analyses and priority support for one month
```

#### Create Prices for Each Product:

**AI Analysis Price:**
- Price: $5.00 CAD
- Billing: One-time
- Copy the Price ID (starts with `price_`)

**Expert Review Price:**
- Price: $50.00 CAD
- Billing: One-time
- Copy the Price ID (starts with `price_`)

**Monthly Unlimited Price (Optional):**
- Price: $29.99 CAD
- Billing: Monthly recurring
- Copy the Price ID (starts with `price_`)

### 4. Set up Webhooks

1. Go to Stripe Dashboard → Developers → Webhooks
2. Click "Add endpoint"
3. Endpoint URL: `https://facultyfinder.io/stripe/webhook`
4. Events to send:
   ```
   payment_intent.succeeded
   payment_intent.payment_failed
   invoice.payment_succeeded
   invoice.payment_failed
   customer.subscription.created
   customer.subscription.updated
   customer.subscription.deleted
   ```
5. Copy the webhook signing secret (starts with `whsec_`)

### 5. Update Environment Variables
```bash
nano /var/www/ff/.env
```

Add/update these lines:
```bash
# Stripe Configuration
STRIPE_PUBLISHABLE_KEY=pk_live_your_publishable_key
STRIPE_SECRET_KEY=sk_live_your_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Stripe Product IDs
STRIPE_AI_ANALYSIS_PRICE_ID=price_ai_analysis_id
STRIPE_EXPERT_REVIEW_PRICE_ID=price_expert_review_id
STRIPE_MONTHLY_UNLIMITED_PRICE_ID=price_monthly_unlimited_id
```

### 6. Test Stripe Integration
Use Stripe test keys first:
```bash
# Test keys for development
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
```

Test with Stripe test card numbers:
- **Success**: 4242 4242 4242 4242
- **Decline**: 4000 0000 0000 0002
- **Requires SCA**: 4000 0025 0000 3155

### 7. Configure Stripe Connect (Future Enhancement)
For marketplace functionality where universities can have their own accounts:
1. Enable Stripe Connect in your dashboard
2. Set up OAuth application
3. Implement Connect onboarding flow

## Systemd Service

### 1. Create Service File
```bash
sudo nano /etc/systemd/system/facultyfinder.service
```

```ini
[Unit]
Description=FacultyFinder Gunicorn Application
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=notify
User=xeradb
Group=xeradb
WorkingDirectory=/var/www/ff
Environment=PATH=/var/www/ff/venv/bin
EnvironmentFile=/var/www/ff/.env
ExecStart=/var/www/ff/venv/bin/gunicorn --bind 127.0.0.1:8008 --workers 4 --worker-class sync --timeout 120 --keep-alive 5 --max-requests 1000 --max-requests-jitter 100 --access-logfile /var/log/facultyfinder/access.log --error-logfile /var/log/facultyfinder/error.log webapp.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=10

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/www/ff/logs /var/log/facultyfinder

[Install]
WantedBy=multi-user.target
```

### 2. Create Log Directory
```bash
sudo mkdir -p /var/log/facultyfinder
sudo chown xeradb:xeradb /var/log/facultyfinder
mkdir -p /var/www/ff/logs
```

### 3. Enable and Start Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable facultyfinder
sudo systemctl start facultyfinder
sudo systemctl status facultyfinder
```

### 4. Create WSGI Entry Point
```bash
nano /var/www/ff/webapp/wsgi.py
```

```python
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

# Set Flask environment
os.environ.setdefault('FLASK_ENV', 'production')

# Import Flask application
from app import app as application

if __name__ == "__main__":
    application.run()
```

## Monitoring & Logs

### 1. Set up Log Rotation
```bash
sudo nano /etc/logrotate.d/facultyfinder
```

```
/var/log/facultyfinder/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 xeradb xeradb
    postrotate
        systemctl reload facultyfinder
    endscript
}
```

### 2. Monitoring Commands
```bash
# Check application status
sudo systemctl status facultyfinder

# View logs
sudo journalctl -u facultyfinder -f
tail -f /var/log/facultyfinder/error.log
tail -f /var/log/facultyfinder/access.log

# Check Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# Check resource usage
htop
df -h
free -h
```

### 3. Health Check Script
```bash
nano /var/www/ff/scripts/health_check.sh
```

```bash
#!/bin/bash
# FacultyFinder Health Check Script

echo "=== FacultyFinder Health Check ==="
echo "Timestamp: $(date)"
echo

# Check service status
echo "Service Status:"
systemctl is-active facultyfinder
echo

# Check if application responds
echo "Application Health:"
curl -s -o /dev/null -w "%{http_code}" http://localhost:8008/health
echo

# Check database connection
echo "Database Connection:"
PGPASSWORD=Choxos10203040 psql -h localhost -U ff_user -d ff_production -c "SELECT 1;" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Database connection successful"
else
    echo "❌ Database connection failed"
fi

# Check disk space
echo
echo "Disk Usage:"
df -h /var/www/ff

# Check memory usage
echo
echo "Memory Usage:"
free -h

echo
echo "=== Health Check Complete ==="
```

```bash
chmod +x /var/www/ff/scripts/health_check.sh
```

## Security Configuration

### 1. Configure UFW Firewall
```bash
# Reset firewall rules
sudo ufw --force reset

# Default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH
sudo ufw allow ssh

# Allow HTTP and HTTPS
sudo ufw allow 80
sudo ufw allow 443

# Allow specific ports if needed
# sudo ufw allow 8008  # Only if you need direct access

# Enable firewall
sudo ufw enable
sudo ufw status
```

### 2. Secure PostgreSQL
```bash
# Edit PostgreSQL configuration
sudo nano /etc/postgresql/*/main/postgresql.conf

# Ensure these settings:
listen_addresses = 'localhost'
ssl = on
password_encryption = scram-sha-256
```

### 3. Set up Fail2Ban
```bash
sudo apt install fail2ban

# Create jail configuration
sudo nano /etc/fail2ban/jail.d/facultyfinder.conf
```

```ini
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log

[nginx-dos]
enabled = true
filter = nginx-dos
port = http,https
logpath = /var/log/nginx/access.log
maxretry = 20
bantime = 600
```

```bash
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

## Database Backups

### 1. Create Backup Script
```bash
nano /var/www/ff/scripts/backup_db.sh
```

```bash
#!/bin/bash
# Database backup script for FacultyFinder

BACKUP_DIR="/var/backups/facultyfinder"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="ff_production"
DB_USER="ff_user"
BACKUP_FILE="$BACKUP_DIR/ff_backup_$DATE.sql"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create database backup
PGPASSWORD=Choxos10203040 pg_dump -h localhost -U $DB_USER -d $DB_NAME > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Remove backups older than 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

# Log backup completion
echo "$(date): Database backup completed: $BACKUP_FILE.gz" >> /var/log/facultyfinder/backup.log
```

### 2. Set up Automated Backups
```bash
chmod +x /var/www/ff/scripts/backup_db.sh

# Add to crontab
crontab -e

# Add this line for daily backups at 2 AM:
0 2 * * * /var/www/ff/scripts/backup_db.sh
```

### 3. Test Backup and Restore
```bash
# Test backup
/var/www/ff/scripts/backup_db.sh

# Test restore (use a test database)
PGPASSWORD=Choxos10203040 createdb -h localhost -U ff_user ff_test
gunzip -c /var/backups/facultyfinder/ff_backup_*.sql.gz | PGPASSWORD=Choxos10203040 psql -h localhost -U ff_user -d ff_test
```

## Testing & Verification

### 1. Domain and SSL Tests
```bash
# Test domain resolution
nslookup facultyfinder.io

# Test SSL certificate
openssl s_client -connect facultyfinder.io:443 -servername facultyfinder.io

# Test HTTP to HTTPS redirect
curl -I http://facultyfinder.io
```

### 2. Application Tests
```bash
# Test health endpoint
curl https://facultyfinder.io/health

# Test main page
curl -I https://facultyfinder.io

# Test API endpoints
curl -I https://facultyfinder.io/api

# Test admin access (should require authentication)
curl -I https://facultyfinder.io/admin
```

### 3. Stripe Tests
1. Use Stripe test mode first
2. Test payment flow with test cards
3. Verify webhook delivery in Stripe dashboard
4. Check application logs for payment processing

### 4. Performance Tests
```bash
# Install tools
sudo apt install apache2-utils

# Basic load test
ab -n 100 -c 10 https://facultyfinder.io/

# Test specific endpoints
ab -n 50 -c 5 https://facultyfinder.io/universities
ab -n 50 -c 5 https://facultyfinder.io/faculties
```

## Maintenance

### 1. Regular Updates
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Python packages
cd /var/www/ff
source venv/bin/activate
pip list --outdated
pip install --upgrade package_name

# Update application code
git pull origin main
sudo systemctl restart facultyfinder
```

### 2. Certificate Renewal
```bash
# Certificates auto-renew, but you can manually renew:
sudo certbot renew
sudo systemctl reload nginx
```

### 3. Log Management
```bash
# Archive old logs
sudo logrotate -f /etc/logrotate.d/facultyfinder

# Clean up large log files
sudo truncate -s 0 /var/log/nginx/access.log
```

### 4. Database Maintenance
```bash
# Analyze database performance
PGPASSWORD=Choxos10203040 psql -h localhost -U ff_user -d ff_production -c "ANALYZE;"

# Vacuum database
PGPASSWORD=Choxos10203040 psql -h localhost -U ff_user -d ff_production -c "VACUUM ANALYZE;"
```

### 5. Monitoring Checklist
- [ ] Check application status: `systemctl status facultyfinder`
- [ ] Check disk space: `df -h`
- [ ] Check memory usage: `free -h`
- [ ] Check error logs: `tail -50 /var/log/facultyfinder/error.log`
- [ ] Check SSL certificate expiry: `sudo certbot certificates`
- [ ] Test website accessibility: Visit `https://facultyfinder.io`
- [ ] Check backup completion: `ls -la /var/backups/facultyfinder/`

## Troubleshooting

### Common Issues and Solutions

#### 1. Application Won't Start
```bash
# Check service status
sudo systemctl status facultyfinder

# Check logs
sudo journalctl -u facultyfinder -n 50

# Common fixes:
sudo systemctl restart facultyfinder
```

#### 2. Database Connection Issues
```bash
# Test database connection
PGPASSWORD=Choxos10203040 psql -h localhost -U ff_user -d ff_production

# Check PostgreSQL status
sudo systemctl status postgresql

# Restart PostgreSQL
sudo systemctl restart postgresql
```

#### 3. SSL Certificate Issues
```bash
# Check certificate status
sudo certbot certificates

# Renew certificates
sudo certbot renew --force-renewal
sudo systemctl reload nginx
```

#### 4. Domain Not Resolving
```bash
# Check DNS propagation
nslookup facultyfinder.io
dig facultyfinder.io

# Check domain registrar settings
# Verify A records point to 91.99.161.136
```

#### 5. Stripe Payment Issues
- Check Stripe dashboard for webhook delivery
- Verify API keys in `.env` file
- Check application logs for Stripe errors
- Test with Stripe test environment first

### Emergency Procedures

#### 1. Application Rollback
```bash
cd /var/www/ff
git log --oneline -10  # Check recent commits
git reset --hard COMMIT_HASH  # Rollback to specific commit
sudo systemctl restart facultyfinder
```

#### 2. Database Restore
```bash
# Stop application
sudo systemctl stop facultyfinder

# Restore from backup
gunzip -c /var/backups/facultyfinder/ff_backup_YYYYMMDD_HHMMSS.sql.gz | PGPASSWORD=Choxos10203040 psql -h localhost -U ff_user -d ff_production

# Start application
sudo systemctl start facultyfinder
```

## Post-Deployment Configuration

### 1. Admin Account Setup
1. Visit `https://facultyfinder.io/auth/register`
2. Create your admin account
3. Manually update user role in database:
```sql
UPDATE users SET role = 'admin' WHERE email = 'your-email@domain.com';
```

### 2. First-Time Configuration
1. Test all major features
2. Upload initial faculty data
3. Configure AI API keys
4. Test payment processing
5. Set up monitoring alerts

### 3. Performance Optimization
1. Monitor application performance
2. Adjust Gunicorn worker count based on usage
3. Implement Redis caching if needed
4. Set up CDN for static files (optional)

---

## Quick Commands Reference

```bash
# Service management
sudo systemctl restart facultyfinder
sudo systemctl status facultyfinder
sudo systemctl reload nginx

# Logs
sudo journalctl -u facultyfinder -f
tail -f /var/log/facultyfinder/error.log

# Health check
curl https://facultyfinder.io/health

# Database backup
/var/www/ff/scripts/backup_db.sh

# Certificate renewal
sudo certbot renew

# Update application
cd /var/www/ff && git pull && sudo systemctl restart facultyfinder
```

---

🎉 **Congratulations!** Your FacultyFinder application should now be live at `https://facultyfinder.io` with SSL, Stripe payments, and full production setup!

For any issues, check the troubleshooting section or contact support. 