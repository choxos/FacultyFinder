# Stripe Integration Guide for FacultyFinder

This guide covers implementing Stripe payments for the AI Assistant feature, allowing users to pay for CV analysis when they don't have their own API keys.

## Overview

FacultyFinder's AI Assistant offers two options:
1. **Free**: Users provide their own API keys (Claude, Gemini, ChatGPT, Grok)
2. **Paid**: Users pay for AI analysis using our API keys

## Stripe Account Setup

### 1. Create Stripe Account
1. Go to [stripe.com](https://stripe.com) and create an account
2. Complete account verification
3. Navigate to the Dashboard

### 2. Get API Keys
1. Go to **Developers** → **API keys**
2. Copy your **Publishable key** (starts with `pk_`)
3. Copy your **Secret key** (starts with `sk_`)
4. For webhooks, create an endpoint and get the **Webhook secret** (starts with `whsec_`)

### 3. Set Up Products and Prices
```bash
# Create products in Stripe Dashboard or via API:

# Product 1: Single CV Analysis
Name: Single CV Analysis
Description: AI-powered analysis of your CV to match with faculty members
Price: $9.99 USD (one-time payment)

# Product 2: CV Analysis Package
Name: CV Analysis Package (5 analyses)
Description: 5 AI-powered CV analyses with detailed faculty recommendations  
Price: $39.99 USD (one-time payment)

# Product 3: Premium Monthly
Name: Premium Monthly Access
Description: Unlimited CV analyses and priority support
Price: $19.99 USD/month (recurring)
```

## Environment Configuration

### 1. Update .env File
```bash
# Add to /var/www/ff/.env
STRIPE_PUBLISHABLE_KEY=pk_live_your_publishable_key_here
STRIPE_SECRET_KEY=sk_live_your_secret_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# Stripe Product IDs (get these from Stripe Dashboard)
STRIPE_SINGLE_ANALYSIS_PRICE_ID=price_single_analysis_id
STRIPE_PACKAGE_PRICE_ID=price_package_analysis_id
STRIPE_PREMIUM_PRICE_ID=price_premium_monthly_id

# AI API Keys (for paid users)
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GOOGLE_AI_API_KEY=your_google_ai_key
GROK_API_KEY=your_grok_key
```

## Backend Implementation

### 1. Update Requirements
```bash
# Add to requirements.txt
stripe==7.8.0
openai==1.3.7
anthropic==0.7.8
google-generativeai==0.3.2
```

### 2. Create Stripe Service
```python
# Create webapp/services/stripe_service.py
import stripe
import os
from flask import current_app

class StripeService:
    def __init__(self):
        stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
    
    def create_checkout_session(self, price_id, success_url, cancel_url, user_email=None):
        """Create a Stripe checkout session"""
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='payment',  # Use 'subscription' for recurring payments
                success_url=success_url,
                cancel_url=cancel_url,
                customer_email=user_email,
                metadata={
                    'service': 'cv_analysis',
                    'price_id': price_id
                }
            )
            return session
        except Exception as e:
            current_app.logger.error(f"Stripe checkout session creation failed: {e}")
            return None
    
    def verify_webhook(self, payload, signature):
        """Verify Stripe webhook signature"""
        try:
            webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
            event = stripe.Webhook.construct_event(payload, signature, webhook_secret)
            return event
        except ValueError:
            current_app.logger.error("Invalid payload in webhook")
            return None
        except stripe.error.SignatureVerificationError:
            current_app.logger.error("Invalid signature in webhook")
            return None
    
    def handle_payment_success(self, session):
        """Handle successful payment"""
        customer_email = session.get('customer_email')
        price_id = session['metadata'].get('price_id')
        payment_intent = session.get('payment_intent')
        
        # Determine credits based on price_id
        credits = self.get_credits_for_price(price_id)
        
        return {
            'customer_email': customer_email,
            'credits': credits,
            'payment_intent': payment_intent,
            'session_id': session['id']
        }
    
    def get_credits_for_price(self, price_id):
        """Map price ID to credits"""
        price_mappings = {
            os.environ.get('STRIPE_SINGLE_ANALYSIS_PRICE_ID'): 1,
            os.environ.get('STRIPE_PACKAGE_PRICE_ID'): 5,
            os.environ.get('STRIPE_PREMIUM_PRICE_ID'): 999  # Unlimited for subscription
        }
        return price_mappings.get(price_id, 0)
```

### 3. Update Database Schema
```sql
-- Add to database/schema.sql

-- User credits table
CREATE TABLE user_credits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(200) NOT NULL,
    credits_remaining INTEGER DEFAULT 0,
    credits_total INTEGER DEFAULT 0,
    subscription_active BOOLEAN DEFAULT FALSE,
    stripe_customer_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    UNIQUE(email)
);

-- Payment transactions table
CREATE TABLE payment_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(200),
    stripe_session_id VARCHAR(200),
    stripe_payment_intent VARCHAR(200),
    amount_cents INTEGER,
    currency VARCHAR(3) DEFAULT 'USD',
    credits_purchased INTEGER,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI analysis usage tracking
CREATE TABLE ai_analysis_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(200),
    ai_provider VARCHAR(50),
    tokens_used INTEGER,
    cost_cents INTEGER,
    analysis_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_user_credits_email ON user_credits(email);
CREATE INDEX idx_payment_transactions_email ON payment_transactions(email);
CREATE INDEX idx_ai_usage_email ON ai_analysis_usage(email);
```

### 4. Update Flask App Routes
```python
# Add to webapp/app.py

from services.stripe_service import StripeService
from services.ai_service import AIService
import stripe

stripe_service = StripeService()
ai_service = AIService()

@app.route('/payment/create-checkout-session', methods=['POST'])
def create_checkout_session():
    """Create Stripe checkout session"""
    data = request.get_json()
    price_id = data.get('price_id')
    user_email = data.get('email')
    
    if not price_id:
        return jsonify({'error': 'Price ID required'}), 400
    
    success_url = request.url_root + 'payment/success?session_id={CHECKOUT_SESSION_ID}'
    cancel_url = request.url_root + 'ai-assistant?cancelled=true'
    
    session = stripe_service.create_checkout_session(
        price_id=price_id,
        success_url=success_url,
        cancel_url=cancel_url,
        user_email=user_email
    )
    
    if session:
        return jsonify({'checkout_url': session.url})
    else:
        return jsonify({'error': 'Failed to create checkout session'}), 500

@app.route('/payment/success')
def payment_success():
    """Handle successful payment"""
    session_id = request.args.get('session_id')
    
    if not session_id:
        return redirect('/ai-assistant?error=no_session')
    
    try:
        # Retrieve the session
        session = stripe.checkout.Session.retrieve(session_id)
        
        if session.payment_status == 'paid':
            # Process the successful payment
            payment_data = stripe_service.handle_payment_success(session)
            
            # Add credits to user account
            add_user_credits(
                email=payment_data['customer_email'],
                credits=payment_data['credits'],
                transaction_data=payment_data
            )
            
            return render_template('payment_success.html', 
                                 credits=payment_data['credits'],
                                 email=payment_data['customer_email'])
        else:
            return redirect('/ai-assistant?error=payment_failed')
            
    except Exception as e:
        logger.error(f"Payment success handling failed: {e}")
        return redirect('/ai-assistant?error=processing_failed')

@app.route('/webhooks/stripe', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks"""
    payload = request.get_data()
    signature = request.headers.get('Stripe-Signature')
    
    event = stripe_service.verify_webhook(payload, signature)
    
    if not event:
        return '', 400
    
    # Handle different event types
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        payment_data = stripe_service.handle_payment_success(session)
        add_user_credits(
            email=payment_data['customer_email'],
            credits=payment_data['credits'],
            transaction_data=payment_data
        )
    
    elif event['type'] == 'invoice.payment_succeeded':
        # Handle subscription renewals
        invoice = event['data']['object']
        handle_subscription_renewal(invoice)
    
    elif event['type'] == 'customer.subscription.deleted':
        # Handle subscription cancellation
        subscription = event['data']['object']
        handle_subscription_cancellation(subscription)
    
    return '', 200

@app.route('/ai-assistant/analyze', methods=['POST'])
def ai_analyze_cv():
    """Analyze CV with AI (requires credits or API key)"""
    data = request.get_json()
    cv_text = data.get('cv_text')
    user_email = data.get('email')
    ai_provider = data.get('ai_provider', 'openai')
    user_api_key = data.get('api_key')
    
    if not cv_text:
        return jsonify({'error': 'CV text required'}), 400
    
    # Check if user provided their own API key
    if user_api_key:
        # Use user's API key (free)
        result = ai_service.analyze_cv_with_user_key(
            cv_text=cv_text,
            ai_provider=ai_provider,
            api_key=user_api_key
        )
    else:
        # Use our API key (requires credits)
        if not user_email:
            return jsonify({'error': 'Email required for paid analysis'}), 400
        
        # Check user credits
        credits = get_user_credits(user_email)
        if credits < 1:
            return jsonify({'error': 'Insufficient credits', 'credits_needed': 1}), 402
        
        # Perform analysis
        result = ai_service.analyze_cv_with_our_key(
            cv_text=cv_text,
            ai_provider=ai_provider
        )
        
        if result.get('success'):
            # Deduct credit
            deduct_user_credit(user_email, 1)
            
            # Track usage
            track_ai_usage(
                email=user_email,
                ai_provider=ai_provider,
                tokens_used=result.get('tokens_used', 0),
                cost_cents=result.get('cost_cents', 0)
            )
    
    return jsonify(result)

# Helper functions
def add_user_credits(email, credits, transaction_data):
    """Add credits to user account"""
    try:
        # Insert or update user credits
        db.execute_query("""
            INSERT INTO user_credits (email, credits_remaining, credits_total, stripe_customer_id)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(email) DO UPDATE SET
                credits_remaining = credits_remaining + ?,
                credits_total = credits_total + ?,
                updated_at = CURRENT_TIMESTAMP
        """, [
            email, credits, credits, transaction_data.get('customer_id'),
            credits, credits
        ])
        
        # Record transaction
        db.execute_query("""
            INSERT INTO payment_transactions 
            (email, stripe_session_id, stripe_payment_intent, credits_purchased, status)
            VALUES (?, ?, ?, ?, 'completed')
        """, [
            email, 
            transaction_data.get('session_id'),
            transaction_data.get('payment_intent'),
            credits
        ])
        
    except Exception as e:
        logger.error(f"Failed to add user credits: {e}")

def get_user_credits(email):
    """Get user's remaining credits"""
    result = db.execute_query("""
        SELECT credits_remaining FROM user_credits WHERE email = ?
    """, [email])
    
    return result[0]['credits_remaining'] if result else 0

def deduct_user_credit(email, credits=1):
    """Deduct credits from user account"""
    db.execute_query("""
        UPDATE user_credits 
        SET credits_remaining = credits_remaining - ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE email = ? AND credits_remaining >= ?
    """, [credits, email, credits])
```

## Frontend Implementation

### 1. Update AI Assistant Template
```html
<!-- Add to webapp/templates/ai_assistant.html -->
{% extends "base.html" %}

{% block title %}AI Assistant - FacultyFinder{% endblock %}

{% block extra_css %}
<script src="https://js.stripe.com/v3/"></script>
{% endblock %}

{% block content %}
<div class="container">
    <div class="ai-assistant-container">
        <h1 class="text-center mb-4">
            <i class="fas fa-robot text-primary me-3"></i>
            AI Faculty Matching Assistant
        </h1>
        
        <!-- CV Upload Section -->
        <div class="facultyfinder-card p-4 mb-4">
            <h3>Upload Your CV</h3>
            <div class="cv-upload-area" id="cv-upload-area">
                <i class="fas fa-cloud-upload-alt fa-3x text-muted mb-3"></i>
                <h4>Drop your CV here or click to select</h4>
                <p class="text-muted">Supports PDF, DOC, DOCX files up to 10MB</p>
                <input type="file" id="cv-file-input" accept=".pdf,.doc,.docx" style="display: none;">
            </div>
            <textarea id="cv-text" class="form-control mt-3" rows="10" 
                      placeholder="Or paste your CV text here..."></textarea>
        </div>
        
        <!-- AI Provider Selection -->
        <div class="facultyfinder-card p-4 mb-4">
            <h3>Choose AI Provider</h3>
            <div class="row">
                <!-- Free Option: User's API Key -->
                <div class="col-md-6 mb-3">
                    <div class="api-provider-card" data-provider="user-key">
                        <h5><i class="fas fa-key me-2"></i>Use Your API Key (Free)</h5>
                        <p class="text-muted">Provide your own API key from OpenAI, Anthropic, Google, or Grok</p>
                        
                        <div class="provider-options mt-3" style="display: none;">
                            <select class="form-select mb-3" id="ai-provider-select">
                                <option value="openai">OpenAI (ChatGPT)</option>
                                <option value="anthropic">Anthropic (Claude)</option>
                                <option value="google">Google (Gemini)</option>
                                <option value="grok">Grok</option>
                            </select>
                            
                            <input type="password" class="form-control" id="user-api-key" 
                                   placeholder="Enter your API key">
                            
                            <small class="text-muted">
                                Your API key is used only for this analysis and is not stored.
                            </small>
                        </div>
                    </div>
                </div>
                
                <!-- Paid Option: Our API Keys -->
                <div class="col-md-6 mb-3">
                    <div class="api-provider-card" data-provider="paid">
                        <h5><i class="fas fa-credit-card me-2"></i>Use Our API Keys</h5>
                        <p class="text-muted">Pay per analysis or subscribe for unlimited access</p>
                        
                        <div class="pricing-options mt-3" style="display: none;">
                            <div class="row">
                                <div class="col-12 mb-2">
                                    <button class="btn btn-outline-primary w-100 pricing-btn" 
                                            data-price-id="{{ stripe_single_price_id }}" data-credits="1">
                                        Single Analysis - $9.99
                                    </button>
                                </div>
                                <div class="col-12 mb-2">
                                    <button class="btn btn-outline-success w-100 pricing-btn" 
                                            data-price-id="{{ stripe_package_price_id }}" data-credits="5">
                                        5 Analyses - $39.99 <span class="badge bg-success">Best Value</span>
                                    </button>
                                </div>
                                <div class="col-12 mb-2">
                                    <button class="btn btn-outline-warning w-100 pricing-btn" 
                                            data-price-id="{{ stripe_premium_price_id }}" data-credits="unlimited">
                                        Unlimited Monthly - $19.99/month
                                    </button>
                                </div>
                            </div>
                            
                            <input type="email" class="form-control mt-3" id="user-email" 
                                   placeholder="Your email address" required>
                            
                            <div id="credits-display" class="mt-2" style="display: none;">
                                <small class="text-success">
                                    <i class="fas fa-coins me-1"></i>
                                    You have <span id="credits-count">0</span> credits remaining
                                </small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Analysis Button -->
        <div class="text-center mb-4">
            <button id="analyze-btn" class="btn btn-primary btn-lg" disabled>
                <i class="fas fa-magic me-2"></i>Analyze My CV
            </button>
        </div>
        
        <!-- Results Section -->
        <div id="results-section" class="facultyfinder-card p-4" style="display: none;">
            <h3>Faculty Recommendations</h3>
            <div id="analysis-results"></div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
// Initialize Stripe
const stripe = Stripe('{{ stripe_publishable_key }}');

document.addEventListener('DOMContentLoaded', function() {
    initializeAIAssistant();
});

function initializeAIAssistant() {
    // Provider selection
    document.querySelectorAll('.api-provider-card').forEach(card => {
        card.addEventListener('click', function() {
            selectProvider(this.dataset.provider);
        });
    });
    
    // Pricing buttons
    document.querySelectorAll('.pricing-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            purchaseCredits(this.dataset.priceId);
        });
    });
    
    // CV file upload
    document.getElementById('cv-file-input').addEventListener('change', handleFileUpload);
    document.getElementById('cv-upload-area').addEventListener('click', () => {
        document.getElementById('cv-file-input').click();
    });
    
    // Analyze button
    document.getElementById('analyze-btn').addEventListener('click', analyzeCV);
    
    // Check existing credits
    checkUserCredits();
}

function selectProvider(provider) {
    // Clear previous selections
    document.querySelectorAll('.api-provider-card').forEach(card => {
        card.classList.remove('selected');
        card.querySelector('.provider-options, .pricing-options').style.display = 'none';
    });
    
    // Select current provider
    const selectedCard = document.querySelector(`[data-provider="${provider}"]`);
    selectedCard.classList.add('selected');
    
    if (provider === 'user-key') {
        selectedCard.querySelector('.provider-options').style.display = 'block';
    } else {
        selectedCard.querySelector('.pricing-options').style.display = 'block';
    }
    
    updateAnalyzeButton();
}

function purchaseCredits(priceId) {
    const email = document.getElementById('user-email').value;
    
    if (!email) {
        alert('Please enter your email address');
        return;
    }
    
    // Create checkout session
    fetch('/payment/create-checkout-session', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            price_id: priceId,
            email: email
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.checkout_url) {
            window.location.href = data.checkout_url;
        } else {
            alert('Error creating checkout session');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error processing payment');
    });
}

function analyzeCV() {
    const cvText = document.getElementById('cv-text').value;
    const selectedProvider = document.querySelector('.api-provider-card.selected');
    
    if (!cvText.trim()) {
        alert('Please provide your CV text');
        return;
    }
    
    if (!selectedProvider) {
        alert('Please select an AI provider option');
        return;
    }
    
    const isUserKey = selectedProvider.dataset.provider === 'user-key';
    let requestData = { cv_text: cvText };
    
    if (isUserKey) {
        const apiKey = document.getElementById('user-api-key').value;
        const provider = document.getElementById('ai-provider-select').value;
        
        if (!apiKey) {
            alert('Please enter your API key');
            return;
        }
        
        requestData.api_key = apiKey;
        requestData.ai_provider = provider;
    } else {
        const email = document.getElementById('user-email').value;
        
        if (!email) {
            alert('Please enter your email address');
            return;
        }
        
        requestData.email = email;
        requestData.ai_provider = 'openai'; // Default for paid
    }
    
    // Show loading
    const analyzeBtn = document.getElementById('analyze-btn');
    analyzeBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Analyzing...';
    analyzeBtn.disabled = true;
    
    // Send analysis request
    fetch('/ai-assistant/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displayResults(data.recommendations);
            updateCreditsDisplay();
        } else if (data.error === 'Insufficient credits') {
            alert('You need more credits to perform this analysis. Please purchase credits.');
        } else {
            alert('Analysis failed: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error during analysis');
    })
    .finally(() => {
        // Reset button
        analyzeBtn.innerHTML = '<i class="fas fa-magic me-2"></i>Analyze My CV';
        analyzeBtn.disabled = false;
    });
}

function displayResults(recommendations) {
    const resultsSection = document.getElementById('results-section');
    const resultsContainer = document.getElementById('analysis-results');
    
    let html = `
        <div class="analysis-summary mb-4">
            <h4>Analysis Summary</h4>
            <p>${recommendations.summary || 'Based on your CV analysis, here are personalized faculty recommendations.'}</p>
        </div>
        
        <div class="faculty-recommendations">
            <h4>Recommended Faculty Members</h4>
            <div class="row">
    `;
    
    recommendations.faculty.forEach(faculty => {
        html += `
            <div class="col-md-6 mb-3">
                <div class="faculty-recommendation-card p-3 border rounded">
                    <h6><a href="/professor/${faculty.id}">${faculty.name}</a></h6>
                    <p class="text-muted">${faculty.department}</p>
                    <p class="small">${faculty.match_reason}</p>
                    <div class="match-score">
                        <span class="badge bg-success">Match: ${faculty.match_score}%</span>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += `
            </div>
        </div>
        
        <div class="recommendations-actions mt-4">
            <button class="btn btn-primary me-2" onclick="downloadRecommendations()">
                <i class="fas fa-download me-1"></i>Download Report
            </button>
            <button class="btn btn-outline-secondary" onclick="shareRecommendations()">
                <i class="fas fa-share me-1"></i>Share Results
            </button>
        </div>
    `;
    
    resultsContainer.innerHTML = html;
    resultsSection.style.display = 'block';
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

function checkUserCredits() {
    const email = document.getElementById('user-email')?.value;
    if (!email) return;
    
    fetch(`/api/user-credits?email=${encodeURIComponent(email)}`)
        .then(response => response.json())
        .then(data => {
            if (data.credits !== undefined) {
                document.getElementById('credits-count').textContent = data.credits;
                document.getElementById('credits-display').style.display = 'block';
            }
        })
        .catch(error => console.error('Error checking credits:', error));
}

function updateCreditsDisplay() {
    setTimeout(checkUserCredits, 1000);
}

function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    // Implement file upload and text extraction
    // This would require additional libraries like PDF.js for PDF parsing
    alert('File upload feature coming soon! Please paste your CV text for now.');
}

function updateAnalyzeButton() {
    const selected = document.querySelector('.api-provider-card.selected');
    const cvText = document.getElementById('cv-text').value;
    const analyzeBtn = document.getElementById('analyze-btn');
    
    analyzeBtn.disabled = !selected || !cvText.trim();
}

// Update button state when CV text changes
document.getElementById('cv-text').addEventListener('input', updateAnalyzeButton);
</script>
{% endblock %}
```

## Testing Stripe Integration

### 1. Test Mode Setup
```bash
# Use test API keys in development
STRIPE_PUBLISHABLE_KEY=pk_test_your_test_key
STRIPE_SECRET_KEY=sk_test_your_test_key

# Test credit card numbers (from Stripe docs)
# Success: 4242424242424242
# Decline: 4000000000000002
# Insufficient funds: 4000000000009995
```

### 2. Webhook Testing
```bash
# Install Stripe CLI for local testing
wget https://github.com/stripe/stripe-cli/releases/download/v1.19.1/stripe_1.19.1_linux_x86_64.tar.gz
tar -xzf stripe_1.19.1_linux_x86_64.tar.gz
sudo mv stripe /usr/local/bin/

# Login and forward webhooks
stripe login
stripe listen --forward-to localhost:8008/webhooks/stripe
```

## Production Deployment

### 1. Update Production Configuration
```bash
# Set live Stripe keys in production .env
STRIPE_PUBLISHABLE_KEY=pk_live_your_live_key
STRIPE_SECRET_KEY=sk_live_your_live_key
STRIPE_WEBHOOK_SECRET=whsec_your_live_webhook_secret
```

### 2. Configure Production Webhooks
1. Go to Stripe Dashboard → Developers → Webhooks
2. Add endpoint: `https://your-domain.com/webhooks/stripe`
3. Select events:
   - `checkout.session.completed`
   - `invoice.payment_succeeded`
   - `customer.subscription.deleted`

### 3. Security Considerations
- Always verify webhook signatures
- Use HTTPS for all payment-related pages
- Store sensitive data encrypted
- Implement rate limiting on payment endpoints
- Log all payment activities
- Regular security audits

This completes the Stripe integration setup. Users can now purchase credits for AI analysis or use their own API keys for free analysis. 