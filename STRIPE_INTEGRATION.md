# Stripe Integration Guide for FacultyFinder

Complete guide for integrating Stripe payment processing into FacultyFinder at facultyfinder.io.

## 📋 Table of Contents

1. [Stripe Account Setup](#stripe-account-setup)
2. [Product Configuration](#product-configuration)
3. [Webhook Configuration](#webhook-configuration)
4. [Environment Configuration](#environment-configuration)
5. [Testing Integration](#testing-integration)
6. [Production Deployment](#production-deployment)
7. [Advanced Features](#advanced-features)
8. [Troubleshooting](#troubleshooting)

## Stripe Account Setup

### 1. Create Stripe Account
1. Visit [stripe.com](https://stripe.com)
2. Click "Start now" and create your account
3. Use your business email: `admin@facultyfinder.io`
4. Complete business verification:
   - Business type: Online software/SaaS
   - Industry: Education Technology
   - Website: `https://facultyfinder.io`
   - Description: "AI-powered faculty discovery platform for academic researchers"

### 2. Account Verification
Required documents for live payments:
- Business registration (if applicable)
- Bank account information
- Tax identification number
- Identity verification for account holders

### 3. Enable Live Payments
1. Complete all verification steps
2. Add bank account for payouts
3. Set payout schedule (daily/weekly)
4. Enable live mode in dashboard

## Product Configuration

### 1. Create Products in Stripe Dashboard

Navigate to **Products** in your Stripe dashboard and create the following:

#### Product 1: AI Faculty Analysis
```
Name: AI Faculty Analysis
Description: Get personalized faculty recommendations using advanced AI analysis of your CV and research interests. Powered by Claude, GPT-4, Gemini, or Grok AI.

Pricing:
- Price: $5.00 CAD
- Billing: One-time payment
- Currency: CAD
```

#### Product 2: Expert Faculty Review
```
Name: Expert Faculty Review  
Description: Manual review and personalized recommendations by our team of academic advisors with PhD-level expertise across multiple disciplines.

Pricing:
- Price: $50.00 CAD
- Billing: One-time payment
- Currency: CAD
```

#### Product 3: Monthly Unlimited Access (Optional)
```
Name: FacultyFinder Pro Monthly
Description: Unlimited AI analyses, priority support, early access to new features, and advanced search filters.

Pricing:
- Price: $29.99 CAD
- Billing: Monthly subscription
- Currency: CAD
- Trial: 7-day free trial
```

#### Product 4: Annual Unlimited Access (Optional)
```
Name: FacultyFinder Pro Annual
Description: Annual subscription with 2 months free. Includes unlimited AI analyses, priority support, and premium features.

Pricing:
- Price: $299.99 CAD (save $59.89)
- Billing: Annual subscription
- Currency: CAD
```

### 2. Configure Price IDs
After creating products, copy the Price IDs (they start with `price_`):
```
AI Analysis: price_1234567890abcdef
Expert Review: price_abcdef1234567890
Monthly Pro: price_monthly123456789
Annual Pro: price_annual123456789
```

### 3. Set Up Payment Methods
Enable the following payment methods:
- **Credit/Debit Cards**: Visa, Mastercard, American Express
- **Digital Wallets**: Apple Pay, Google Pay
- **Bank Transfers**: For larger payments (expert reviews)
- **Buy Now, Pay Later**: Klarna, Afterpay (optional)

## Webhook Configuration

### 1. Create Webhook Endpoint

In Stripe Dashboard → **Developers** → **Webhooks**:

```
Endpoint URL: https://facultyfinder.io/stripe/webhook
Description: FacultyFinder payment processing webhook
Events to send: (see below)
```

### 2. Required Webhook Events

Select these events to send to your endpoint:

**Payment Events:**
```
payment_intent.succeeded
payment_intent.payment_failed
payment_intent.canceled
payment_intent.requires_action
```

**Subscription Events (if using subscriptions):**
```
customer.subscription.created
customer.subscription.updated
customer.subscription.deleted
customer.subscription.trial_will_end
invoice.payment_succeeded
invoice.payment_failed
```

**Customer Events:**
```
customer.created
customer.updated
customer.deleted
```

### 3. Webhook Security
- Copy the **Webhook Signing Secret** (starts with `whsec_`)
- This will be used to verify webhook authenticity
- Store securely in your environment variables

## Environment Configuration

### 1. Development Environment (.env.development)
```bash
# Stripe Test Configuration
STRIPE_PUBLISHABLE_KEY=pk_test_51234567890abcdef...
STRIPE_SECRET_KEY=sk_test_51234567890abcdef...
STRIPE_WEBHOOK_SECRET=whsec_test_1234567890abcdef...

# Test Product Price IDs
STRIPE_AI_ANALYSIS_PRICE_ID=price_test_ai_analysis
STRIPE_EXPERT_REVIEW_PRICE_ID=price_test_expert_review
STRIPE_MONTHLY_PRO_PRICE_ID=price_test_monthly_pro
STRIPE_ANNUAL_PRO_PRICE_ID=price_test_annual_pro

# Test Environment Settings
STRIPE_ENVIRONMENT=test
DOMAIN_NAME=localhost:8080
BASE_URL=http://localhost:8080
```

### 2. Production Environment (.env)
```bash
# Stripe Live Configuration
STRIPE_PUBLISHABLE_KEY=pk_live_51234567890abcdef...
STRIPE_SECRET_KEY=sk_live_51234567890abcdef...
STRIPE_WEBHOOK_SECRET=whsec_1234567890abcdef...

# Live Product Price IDs
STRIPE_AI_ANALYSIS_PRICE_ID=price_live_ai_analysis
STRIPE_EXPERT_REVIEW_PRICE_ID=price_live_expert_review
STRIPE_MONTHLY_PRO_PRICE_ID=price_live_monthly_pro
STRIPE_ANNUAL_PRO_PRICE_ID=price_live_annual_pro

# Production Settings
STRIPE_ENVIRONMENT=live
DOMAIN_NAME=facultyfinder.io
BASE_URL=https://facultyfinder.io
```

### 3. Security Configuration
```bash
# Payment Security
STRIPE_WEBHOOK_TOLERANCE=300  # 5 minutes
PAYMENT_RETRY_ATTEMPTS=3
PAYMENT_TIMEOUT=30  # seconds

# Currency Settings
DEFAULT_CURRENCY=CAD
SUPPORTED_CURRENCIES=CAD,USD

# Tax Configuration (if applicable)
STRIPE_TAX_RATE_ID=txr_1234567890abcdef  # Canadian tax rate
```

## Testing Integration

### 1. Test Cards for Development

Use these test card numbers in development:

**Successful Payments:**
```
4242 4242 4242 4242  # Visa
4000 0056 0000 0008  # Visa (debit)
5555 5555 5555 4444  # Mastercard
3782 822463 10005    # American Express
```

**Failed Payments:**
```
4000 0000 0000 0002  # Generic decline
4000 0000 0000 9995  # Insufficient funds
4000 0000 0000 9987  # Lost card
4000 0000 0000 9979  # Stolen card
```

**Special Cases:**
```
4000 0025 0000 3155  # Requires 3D Secure authentication
4000 0000 0000 3220  # 3D Secure authentication failure
4242 4242 4242 4241  # Invalid CVC
4000 0000 0000 0069  # Expired card
```

### 2. Test Webhook Delivery

#### Using Stripe CLI:
```bash
# Install Stripe CLI
# Download from: https://github.com/stripe/stripe-cli

# Login to Stripe
stripe login

# Forward events to local development server
stripe listen --forward-to http://localhost:8080/stripe/webhook

# Trigger test events
stripe trigger payment_intent.succeeded
stripe trigger customer.subscription.created
```

#### Manual Testing:
1. Use test mode in Stripe dashboard
2. Create test payments
3. Verify webhook delivery in dashboard
4. Check application logs for processing

### 3. Test User Flows

**AI Analysis Purchase:**
1. User visits AI assistant page
2. Uploads CV and selects AI service
3. Chooses "Quick Analysis ($5)"
4. Completes payment with test card
5. Receives analysis results

**Expert Review Purchase:**
1. User selects "Expert Review ($50)"
2. Provides additional information
3. Completes payment
4. Receives confirmation email
5. Gets review within 3-5 business days

**Subscription Flow:**
1. User selects monthly/annual plan
2. Completes payment setup
3. Gains access to premium features
4. Can cancel anytime

## Production Deployment

### 1. Pre-Launch Checklist

**Stripe Configuration:**
- [ ] Live API keys configured
- [ ] Webhook endpoint tested
- [ ] Products and prices created
- [ ] Payment methods enabled
- [ ] Tax rates configured (if applicable)

**Application Configuration:**
- [ ] Environment variables set
- [ ] SSL certificate active
- [ ] Domain configured properly
- [ ] Error handling implemented
- [ ] Logging configured

**Testing:**
- [ ] End-to-end payment flow tested
- [ ] Webhook delivery verified
- [ ] Refund process tested
- [ ] Subscription management tested
- [ ] Error scenarios tested

### 2. Go-Live Process

1. **Switch to Live Mode:**
   ```bash
   # Update .env with live keys
   STRIPE_PUBLISHABLE_KEY=pk_live_...
   STRIPE_SECRET_KEY=sk_live_...
   STRIPE_ENVIRONMENT=live
   ```

2. **Deploy Application:**
   ```bash
   cd /var/www/ff
   git pull origin main
   sudo systemctl restart facultyfinder
   ```

3. **Verify Live Configuration:**
   ```bash
   # Test webhook endpoint
   curl -X POST https://facultyfinder.io/stripe/webhook
   
   # Test payment page
   curl https://facultyfinder.io/ai-assistant
   ```

### 3. Post-Launch Monitoring

**Key Metrics to Monitor:**
- Payment success rate
- Failed payment reasons
- Webhook delivery success
- Customer signup conversion
- Subscription churn rate

**Monitoring Tools:**
```bash
# Check payment logs
tail -f /var/log/facultyfinder/payment.log

# Monitor Stripe dashboard
# - Payment volume
# - Success/failure rates
# - Dispute notifications
# - Webhook delivery status
```

## Advanced Features

### 1. Subscription Management

**Customer Portal:**
- Self-service subscription management
- Payment method updates
- Invoice downloads
- Usage tracking

**Configuration in Stripe:**
```javascript
// Customer portal settings
{
  "business_profile": {
    "headline": "Manage your FacultyFinder subscription",
    "privacy_policy_url": "https://facultyfinder.io/privacy",
    "terms_of_service_url": "https://facultyfinder.io/terms"
  },
  "features": {
    "payment_method_update": {
      "enabled": true
    },
    "subscription_cancel": {
      "enabled": true,
      "mode": "at_period_end"
    },
    "subscription_pause": {
      "enabled": false
    },
    "invoice_history": {
      "enabled": true
    }
  }
}
```

### 2. Usage-Based Billing

**Metered Billing for API Calls:**
```javascript
// Report usage to Stripe
{
  "subscription_item": "si_1234567890",
  "quantity": 10,  // Number of AI analyses used
  "timestamp": 1640995200,
  "action": "increment"
}
```

### 3. Multi-Currency Support

**Supported Currencies:**
```bash
# Primary currencies
CAD  # Canadian Dollar (primary)
USD  # US Dollar
EUR  # Euro
GBP  # British Pound

# Configuration
SUPPORTED_CURRENCIES=CAD,USD,EUR,GBP
DEFAULT_CURRENCY=CAD
```

### 4. Tax Calculation

**Stripe Tax Integration:**
```javascript
// Automatic tax calculation
{
  "automatic_tax": {
    "enabled": true
  },
  "customer_details": {
    "tax_exempt": "none",
    "tax_ids": []
  }
}
```

### 5. Marketplace Features (Future)

**Connect for University Partnerships:**
- Universities can create accounts
- Revenue sharing for referrals
- Branded payment pages
- Separate payout schedules

## Troubleshooting

### 1. Common Payment Issues

**Payment Declined:**
```javascript
// Check decline codes
{
  "decline_code": "insufficient_funds",
  "message": "Your card has insufficient funds."
}

// Common decline codes:
// - insufficient_funds
// - card_declined
// - expired_card
// - incorrect_cvc
// - processing_error
```

**Solutions:**
1. Display user-friendly error messages
2. Suggest alternative payment methods
3. Retry with different card
4. Contact customer support

### 2. Webhook Debugging

**Webhook Not Received:**
```bash
# Check webhook logs in Stripe dashboard
# Verify endpoint URL: https://facultyfinder.io/stripe/webhook
# Check SSL certificate validity
# Verify webhook signature validation

# Debug webhook processing
tail -f /var/log/facultyfinder/webhook.log
```

**Webhook Signature Verification:**
```python
import stripe
import hashlib
import hmac

def verify_webhook_signature(payload, sig_header, endpoint_secret):
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
        return True, event
    except ValueError:
        return False, "Invalid payload"
    except stripe.error.SignatureVerificationError:
        return False, "Invalid signature"
```

### 3. Subscription Issues

**Failed Subscription Renewal:**
- Check payment method validity
- Update billing address
- Retry payment with Smart Retries
- Send dunning emails

**Subscription Cancellation:**
- Process at period end
- Provide retention offers
- Export data before deletion
- Send confirmation email

### 4. Dispute Management

**Chargeback Prevention:**
- Clear billing descriptor: "FACULTYFINDER.IO"
- Detailed receipts
- Customer communication logs
- Clear refund policy

**Dispute Response:**
- Gather evidence quickly
- Submit compelling evidence
- Use Stripe Radar for fraud prevention
- Monitor dispute rates

## Security Best Practices

### 1. API Key Security
```bash
# Never commit API keys to version control
# Use environment variables only
# Rotate keys regularly
# Monitor API key usage

# Key rotation process:
1. Generate new API keys in Stripe dashboard
2. Update environment variables
3. Deploy application
4. Delete old keys
5. Monitor for any issues
```

### 2. Webhook Security
```python
# Always verify webhook signatures
# Use HTTPS only
# Implement idempotency
# Log all webhook events
# Set up webhook retry logic
```

### 3. PCI Compliance
- Never store card data
- Use Stripe.js for card collection
- Implement 3D Secure when required
- Regular security audits
- Monitor for suspicious activity

## Support and Resources

### 1. Stripe Resources
- **Documentation**: https://stripe.com/docs
- **API Reference**: https://stripe.com/docs/api
- **Testing Guide**: https://stripe.com/docs/testing
- **Webhook Guide**: https://stripe.com/docs/webhooks

### 2. Community Support
- **Discord**: Stripe Developers
- **Stack Overflow**: stripe-payments tag
- **GitHub**: stripe/stripe-node

### 3. Emergency Contacts
- **Stripe Support**: https://support.stripe.com
- **Critical Issues**: Available 24/7 for live accounts
- **Phone Support**: Available for higher-volume accounts

---

## Quick Reference Commands

```bash
# Test webhook endpoint
curl -X POST https://facultyfinder.io/stripe/webhook \
  -H "Content-Type: application/json" \
  -d '{"test": true}'

# Check payment logs
tail -f /var/log/facultyfinder/payment.log

# Verify Stripe configuration
grep STRIPE /var/www/ff/.env

# Test payment flow
curl https://facultyfinder.io/ai-assistant

# Monitor webhook delivery
stripe listen --forward-to https://facultyfinder.io/stripe/webhook
```

---

🚀 **Your Stripe integration is now ready for production!** Monitor the dashboard closely during the first few days to ensure everything is working smoothly. 