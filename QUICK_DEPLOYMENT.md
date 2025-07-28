# Quick Deployment Reference

## 🚀 Immediate Steps to Deploy FacultyFinder

### 1. Prepare Your VPS (One-time setup)

**SSH into your server:**
```bash
ssh xeradb@91.99.161.136
```

**Install dependencies:**
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git nginx postgresql postgresql-contrib supervisor
```

**Setup PostgreSQL:**
```bash
sudo -u postgres psql
```
```sql
CREATE DATABASE ff_production;
CREATE USER ff_user WITH PASSWORD 'Choxos10203040';
GRANT ALL PRIVILEGES ON DATABASE ff_production TO ff_user;
ALTER USER ff_user CREATEDB;
\q
```

**Configure PostgreSQL access:**
```bash
sudo nano /etc/postgresql/*/main/pg_hba.conf
# Add this line: local   ff_production   ff_user                md5
sudo systemctl restart postgresql
```

### 2. Deploy Application (Automated)

**From your local machine:**
```bash
# In your FacultyFinder directory
./deploy.sh production
```

**Or manually sync and deploy:**
```bash
# Sync files
rsync -avz --exclude '.git' --exclude '.env' --exclude 'database/' --exclude '__pycache__' --exclude 'venv/' . xeradb@91.99.161.136:/var/www/ff/

# SSH and setup
ssh xeradb@91.99.161.136
cd /var/www/ff
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt psycopg2-binary gunicorn python-dotenv
```

### 3. Configure Environment

**Create .env file on server:**
```bash
cat > /var/www/ff/.env << EOF
FLASK_ENV=production
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
DB_HOST=localhost
DB_PORT=5432
DB_USER=ff_user
DB_PASSWORD=Choxos10203040
DB_NAME=ff_production
APP_PORT=8008
APP_HOST=0.0.0.0

# Add your Stripe keys here:
STRIPE_PUBLISHABLE_KEY=pk_live_your_key_here
STRIPE_SECRET_KEY=sk_live_your_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
EOF

chmod 600 .env
```

### 4. Setup Systemd Service

**Create service file:**
```bash
sudo tee /etc/systemd/system/facultyfinder.service > /dev/null << EOF
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
ExecStart=/var/www/ff/venv/bin/gunicorn --bind 127.0.0.1:8008 --workers 3 webapp.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable facultyfinder
sudo systemctl start facultyfinder
```

### 5. Configure Nginx (Simple HTTP first)

**Create Nginx config:**
```bash
sudo tee /etc/nginx/sites-available/facultyfinder > /dev/null << EOF
server {
    listen 80;
    server_name 91.99.161.136;
    
    location /static {
        alias /var/www/ff/webapp/static;
        expires 1y;
    }
    
    location / {
        proxy_pass http://127.0.0.1:8008;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/facultyfinder /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 6. Test Everything

```bash
# Test application
curl -I http://127.0.0.1:8008/

# Test through Nginx
curl -I http://91.99.161.136/

# Check service status
sudo systemctl status facultyfinder
sudo systemctl status nginx
```

## 🔧 Common Commands

**Application Management:**
```bash
# Restart application
sudo systemctl restart facultyfinder

# View logs
sudo journalctl -u facultyfinder -f

# Check status
sudo systemctl status facultyfinder
```

**Database Management:**
```bash
# Connect to database
psql -h localhost -U ff_user -d ff_production

# Backup database
pg_dump -h localhost -U ff_user ff_production > backup.sql

# Restore database
psql -h localhost -U ff_user -d ff_production < backup.sql
```

**Nginx Management:**
```bash
# Test configuration
sudo nginx -t

# Reload configuration
sudo systemctl reload nginx

# View access logs
sudo tail -f /var/log/nginx/access.log
```

## 💳 Stripe Setup Checklist

1. **Create Stripe Account** at [stripe.com](https://stripe.com)
2. **Get API Keys** from Dashboard → Developers → API keys
3. **Create Products:**
   - Single CV Analysis: $9.99
   - 5-Pack Analysis: $39.99
   - Monthly Unlimited: $19.99/month
4. **Setup Webhooks** pointing to `https://your-domain.com/webhooks/stripe`
5. **Update .env file** with your Stripe keys
6. **Test with test cards** before going live

## 🔒 Security Checklist

- [ ] Change default PostgreSQL password
- [ ] Setup SSH key authentication (disable password auth)
- [ ] Configure UFW firewall
- [ ] Setup SSL certificate with Let's Encrypt
- [ ] Regular security updates
- [ ] Monitor application logs
- [ ] Setup database backups

## 🚨 If Something Goes Wrong

**Application won't start:**
```bash
sudo journalctl -u facultyfinder -n 50
```

**Database connection issues:**
```bash
psql -h localhost -U ff_user -d ff_production
# Check if you can connect manually
```

**Nginx issues:**
```bash
sudo nginx -t
sudo tail -f /var/log/nginx/error.log
```

**Port conflicts:**
```bash
sudo netstat -tlnp | grep 8008
```

## 📞 Quick Access URLs

- **Application**: http://91.99.161.136/
- **Health Check**: http://91.99.161.136/health
- **API Docs**: http://91.99.161.136/api

---

**Need help?** Check the full guides:
- `DEPLOYMENT_GUIDE.md` - Complete deployment instructions
- `STRIPE_INTEGRATION.md` - Stripe payment setup 