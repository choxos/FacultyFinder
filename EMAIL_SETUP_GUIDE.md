# Email Setup Guide for FacultyFinder

This guide provides comprehensive instructions for setting up professional email accounts for FacultyFinder at `facultyfinder.io`.

## 📧 Required Email Addresses

### Primary Addresses
- `support@facultyfinder.io` - Main support and contact
- `admin@facultyfinder.io` - Administrative communications
- `noreply@facultyfinder.io` - Automated emails (notifications, confirmations)
- `api@facultyfinder.io` - API-related communications
- `partnerships@facultyfinder.io` - University partnerships

### Optional Addresses
- `hello@facultyfinder.io` - General inquiries
- `security@facultyfinder.io` - Security-related reports
- `dev@facultyfinder.io` - Development team communications

## 🌐 Email Provider Options

### Option 1: Google Workspace (Recommended)
**Best for**: Professional features, reliability, integration

**Pricing**: $6/user/month (Business Starter)

**Features**:
- Custom domain email
- 30GB storage per user
- Google Drive, Docs, Sheets integration
- Professional calendar and video conferencing
- Advanced security features

**Setup Steps**:
1. Go to [Google Workspace](https://workspace.google.com/)
2. Sign up with your `facultyfinder.io` domain
3. Verify domain ownership via DNS records
4. Create user accounts for each email address
5. Configure MX records (see DNS section below)

### Option 2: Microsoft 365 Business
**Best for**: Microsoft ecosystem integration

**Pricing**: $6/user/month (Business Basic)

**Features**:
- Custom domain email
- 50GB mailbox storage
- Microsoft Office apps
- Teams integration
- Advanced threat protection

### Option 3: Custom Email Hosting
**Best for**: Cost-effective, full control

**Providers**:
- **Namecheap Email**: $1.49/month per mailbox
- **Zoho Mail**: $1/month per user
- **ProtonMail**: $4/month per user (privacy-focused)

## 🔧 DNS Configuration

### MX Records (Mail Exchange)
Configure these DNS records in your domain registrar:

**For Google Workspace:**
```
Type: MX    Name: @    Value: ASPMX.L.GOOGLE.COM.         Priority: 1
Type: MX    Name: @    Value: ALT1.ASPMX.L.GOOGLE.COM.    Priority: 5
Type: MX    Name: @    Value: ALT2.ASPMX.L.GOOGLE.COM.    Priority: 5
Type: MX    Name: @    Value: ALT3.ASPMX.L.GOOGLE.COM.    Priority: 10
Type: MX    Name: @    Value: ALT4.ASPMX.L.GOOGLE.COM.    Priority: 10
```

**For Microsoft 365:**
```
Type: MX    Name: @    Value: facultyfinder-io.mail.protection.outlook.com    Priority: 0
```

### SPF Record (Sender Policy Framework)
```
Type: TXT   Name: @    Value: v=spf1 include:_spf.google.com ~all
```

### DKIM Record (DomainKeys Identified Mail)
Google Workspace will provide a specific DKIM key to add as a TXT record.

### DMARC Record (Domain-based Message Authentication)
```
Type: TXT   Name: _dmarc    Value: v=DMARC1; p=quarantine; rua=mailto:admin@facultyfinder.io
```

## 📱 Application Email Configuration

### SMTP Settings for Flask Application

**For Google Workspace:**
```python
# Email Configuration
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USE_SSL = False
MAIL_USERNAME = 'noreply@facultyfinder.io'
MAIL_PASSWORD = 'your_app_password'  # Use App Password, not regular password
MAIL_DEFAULT_SENDER = 'noreply@facultyfinder.io'
```

**For Microsoft 365:**
```python
# Email Configuration
MAIL_SERVER = 'smtp.office365.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USE_SSL = False
MAIL_USERNAME = 'noreply@facultyfinder.io'
MAIL_PASSWORD = 'your_password'
MAIL_DEFAULT_SENDER = 'noreply@facultyfinder.io'
```

### Environment Variables (.env)
```bash
# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=noreply@facultyfinder.io
MAIL_PASSWORD=your_app_specific_password
MAIL_DEFAULT_SENDER=noreply@facultyfinder.io

# Email Addresses
SUPPORT_EMAIL=support@facultyfinder.io
ADMIN_EMAIL=admin@facultyfinder.io
PARTNERSHIPS_EMAIL=partnerships@facultyfinder.io
```

## 🔐 Security Setup

### Google Workspace App Passwords
1. Enable 2-factor authentication on the admin account
2. Go to [App Passwords](https://myaccount.google.com/apppasswords)
3. Generate app-specific password for "Mail"
4. Use this password in your application configuration

### Microsoft 365 Modern Authentication
1. Register your application in Azure AD
2. Configure OAuth2 authentication
3. Use access tokens for SMTP authentication

## 📋 Email Templates

### Contact Form Response Template
```html
Subject: Thank you for contacting FacultyFinder

Dear {{name}},

Thank you for reaching out to FacultyFinder! We have received your message regarding "{{subject}}" and will respond within 24 hours.

Your message:
{{message}}

If you have urgent questions, please don't hesitate to contact us directly at support@facultyfinder.io.

Best regards,
The FacultyFinder Team

---
FacultyFinder - Connecting researchers worldwide
https://facultyfinder.io
```

### API Key Notification Template
```html
Subject: Your FacultyFinder API Key

Dear {{user_name}},

Welcome to the FacultyFinder API! Your API key details:

API Key: {{api_key}}
Rate Limit: {{rate_limit}} requests per hour
Documentation: https://facultyfinder.io/api

Important: Keep your API key secure and never share it publicly.

Best regards,
The FacultyFinder API Team
```

### University Partnership Template
```html
Subject: University Partnership Opportunity - FacultyFinder

Dear {{university_name}} Team,

Thank you for your interest in partnering with FacultyFinder!

We'd love to discuss how we can help showcase your faculty members and attract top researchers to your institution.

Partnership benefits:
- Enhanced faculty visibility
- Global researcher network access
- Advanced analytics and insights
- Custom university profile page

Let's schedule a call to discuss your specific needs.

Best regards,
The FacultyFinder Partnerships Team
partnerships@facultyfinder.io
```

## 🧪 Testing Email Configuration

### Test Script
```python
#!/usr/bin/env python3
"""
Email configuration test script
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_email_config():
    # Configuration
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    username = "noreply@facultyfinder.io"
    password = "your_app_password"
    
    # Create message
    msg = MIMEMultipart()
    msg['From'] = username
    msg['To'] = "admin@facultyfinder.io"
    msg['Subject'] = "FacultyFinder Email Configuration Test"
    
    body = """
    This is a test email to verify the FacultyFinder email configuration.
    
    If you receive this email, the SMTP settings are working correctly.
    
    Best regards,
    FacultyFinder System
    """
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        # Connect to server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(username, password)
        
        # Send email
        text = msg.as_string()
        server.sendmail(username, "admin@facultyfinder.io", text)
        server.quit()
        
        print("✅ Email sent successfully!")
        
    except Exception as e:
        print(f"❌ Error sending email: {e}")

if __name__ == "__main__":
    test_email_config()
```

## 📊 Email Analytics and Monitoring

### Recommended Tools
- **Google Workspace Admin Console**: Built-in analytics
- **SendGrid**: Transactional email service with analytics
- **Mailgun**: Email API with detailed tracking
- **Postmark**: Reliable transactional email delivery

### Key Metrics to Track
- Email delivery rate
- Open rates (for marketing emails)
- Bounce rates
- Spam complaints
- Response times to support emails

## 🔄 Email Automation Workflows

### Contact Form Workflow
1. User submits contact form
2. Instant confirmation email to user
3. Notification email to support team
4. Auto-response with ticket number
5. Follow-up email if no response in 24 hours

### User Registration Workflow
1. User signs up for account
2. Welcome email with getting started guide
3. Email verification required
4. Weekly newsletter subscription option
5. Feature announcement emails

### API Usage Workflow
1. User requests API access
2. API key generated and emailed
3. Usage threshold notifications (80%, 90%, 100%)
4. Monthly usage reports
5. Renewal reminders

## 🛠️ Integration with FacultyFinder

### Flask-Mail Integration
```python
from flask_mail import Mail, Message

# Initialize Flask-Mail
mail = Mail(app)

def send_contact_confirmation(user_email, user_name, subject, message):
    """Send confirmation email when contact form is submitted"""
    msg = Message(
        subject="Thank you for contacting FacultyFinder",
        sender=app.config['MAIL_DEFAULT_SENDER'],
        recipients=[user_email]
    )
    
    msg.html = render_template('emails/contact_confirmation.html',
                              name=user_name,
                              subject=subject,
                              message=message)
    
    mail.send(msg)

def notify_support_team(user_email, user_name, subject, message):
    """Notify support team of new contact form submission"""
    msg = Message(
        subject=f"New Contact Form: {subject}",
        sender=app.config['MAIL_DEFAULT_SENDER'],
        recipients=[app.config['SUPPORT_EMAIL']]
    )
    
    msg.html = render_template('emails/support_notification.html',
                              user_email=user_email,
                              user_name=user_name,
                              subject=subject,
                              message=message)
    
    mail.send(msg)
```

## 🚨 Troubleshooting

### Common Issues

**1. "Authentication failed" error**
- Solution: Enable 2FA and use app-specific passwords
- Check username/password are correct
- Verify SMTP server and port settings

**2. Emails going to spam**
- Solution: Configure SPF, DKIM, and DMARC records
- Use professional email templates
- Avoid spam trigger words

**3. "Connection refused" error**
- Solution: Check firewall settings on VPS
- Verify SMTP port (587 or 465) is allowed
- Test from different network

**4. Emails not delivering**
- Solution: Check MX records are properly configured
- Verify domain ownership
- Monitor email provider's status page

### Debug Commands
```bash
# Test MX records
dig MX facultyfinder.io

# Test SMTP connection
telnet smtp.gmail.com 587

# Check SPF record
dig TXT facultyfinder.io

# Verify email headers
tail -f /var/log/mail.log
```

## 📞 Support

For email setup assistance:
- Google Workspace: [Support Center](https://support.google.com/a/)
- Microsoft 365: [Admin Help](https://docs.microsoft.com/en-us/microsoft-365/)
- Domain DNS: Contact your domain registrar support

---

**Next Steps**: After setting up email, update the deployment guide with email configuration and test all email workflows thoroughly. 