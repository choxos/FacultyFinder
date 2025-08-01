# AI Assistant Requests Management - Admin Guide

This guide explains how to use the admin interface to manage AI Assistant requests and monitor the system performance.

## Overview

The AI Assistant Requests Management system provides comprehensive tools for administrators to:
- Monitor all AI assistant analysis requests
- Track payment statuses (both credit card and cryptocurrency)
- View user engagement and system statistics
- Manage request statuses and resolve issues
- Analyze revenue and usage patterns

## Access

### Admin Dashboard
- **URL**: `http://yourdomain.com/admin`
- **Direct AI Requests**: `http://yourdomain.com/admin/ai-requests`

### Navigation
The admin interface includes:
- **Dashboard**: Overall system statistics and overview
- **AI Requests**: Detailed management of AI assistant requests

## AI Requests Management Features

### 📊 **Statistics Dashboard**

The top of the AI requests page displays key metrics:

#### **Total Sessions**
- Total number of AI assistant sessions created
- Includes all requests regardless of payment status

#### **Total Revenue (CAD)**
- Combined revenue from credit card and cryptocurrency payments
- Shows completed payments only
- Automatically converts crypto payments to CAD

#### **Recent Sessions (30d)**
- Number of sessions created in the last 30 days
- Helps track recent user activity

#### **Completion Rate**
- Percentage of sessions that reached "completed" status
- Key metric for system success rate

### 🔍 **Filtering System**

#### **Status Filter**
- **All Statuses**: Show all requests
- **Pending**: Payment initiated but not completed
- **Completed**: Successfully processed requests
- **Failed**: Failed payments or processing errors
- **Processing**: Currently being processed

#### **Service Type Filter**
- **All Services**: Show all service types
- **AI Analysis**: Basic AI analysis packages ($7, $10, $15, $49)
- **Manual Review**: Expert review packages ($99, $299, $999)
- **Subscription**: Monthly unlimited plans

#### **AI Provider Filter**
- **All Providers**: Show all AI providers
- **Claude**: Anthropic's Claude AI
- **ChatGPT**: OpenAI's GPT models
- **Gemini**: Google's Gemini AI
- **Grok**: xAI's Grok AI

### 📋 **Request Details Table**

Each request displays:

#### **Session ID**
- Unique identifier for the AI session
- Used for tracking and debugging

#### **User Information**
- User name (if registered) or "Anonymous"
- Email address or IP address
- Helps identify and contact users

#### **AI Provider**
- Which AI service was selected
- Color-coded badges for easy identification

#### **Service Type**
- Type of analysis requested
- Links to pricing tier selected

#### **Payment Information**
- **Regular Payments**: Credit card via Stripe
  - Amount in CAD
  - Payment method
- **Cryptocurrency Payments**: 
  - Crypto amount and type
  - Equivalent CAD amount
  - Payment provider (CoinPayments, NOWPayments)

#### **Status**
- Current processing status
- Color-coded for quick identification

#### **Created At**
- When the request was initiated
- Relative time display (e.g., "2h ago")

## 🛠 **Admin Actions**

### **View Details**
- Click the eye icon (👁️) to view full request details
- Shows comprehensive information about the session
- Includes user details, payment information, and timestamps

### **Mark Completed**
- Click the checkmark icon (✅) to mark a request as completed
- Use when manually processing requests
- Updates system statistics

### **Mark Failed**
- Click the X icon (❌) to mark a request as failed
- Use for failed payments or processing errors
- Helps track issues for improvement

### **Status Updates**
- All status changes are logged
- Updates are reflected in real-time statistics
- Confirmation dialog prevents accidental changes

## 📈 **Monitoring Best Practices**

### **Daily Tasks**
1. **Check Recent Activity**: Review sessions from last 24 hours
2. **Monitor Failed Requests**: Investigate and resolve failed payments
3. **Verify Completions**: Ensure successful requests are marked completed

### **Weekly Tasks**
1. **Analyze Trends**: Review completion rates and popular services
2. **Revenue Review**: Check payment processing and totals
3. **Provider Performance**: Monitor which AI providers are most popular

### **Monthly Tasks**
1. **Generate Reports**: Export statistics for business analysis
2. **System Optimization**: Identify bottlenecks and improvements
3. **User Feedback**: Review patterns to improve user experience

## 🔧 **Troubleshooting**

### **Common Issues**

#### **Stuck Pending Payments**
- **Symptom**: Payments remain "pending" for extended periods
- **Solutions**:
  - Check payment provider dashboards
  - Verify webhook configurations
  - Manually mark as completed if payment confirmed

#### **Failed Cryptocurrency Payments**
- **Symptom**: Crypto payments showing as failed
- **Solutions**:
  - Verify blockchain confirmations
  - Check payment provider logs
  - Contact crypto payment provider support

#### **Missing User Information**
- **Symptom**: Requests showing as "Anonymous"
- **Explanation**: Guest users or users who didn't complete registration
- **Action**: Use IP address for tracking if needed

### **API Endpoints for Advanced Management**

#### **Get Requests**
```
GET /api/v1/admin/ai-requests
```
Parameters:
- `status`: Filter by status
- `service_type`: Filter by service type
- `provider`: Filter by AI provider
- `limit`: Results per page (default: 50)
- `offset`: Page offset

#### **Update Status**
```
POST /api/v1/admin/ai-requests/{request_id}/update-status
```
Body: `{"status": "completed"}`

#### **Get Statistics**
```
GET /api/v1/admin/ai-requests/stats
```
Returns comprehensive statistics for dashboard

## 💡 **Tips for Efficient Management**

### **Quick Actions**
- Use keyboard shortcuts where available
- Set up bookmarks for common filters
- Monitor the "Recent Sessions" metric for activity spikes

### **Bulk Operations**
- Apply filters to work with specific request types
- Use pagination for large datasets
- Export data if needed for external analysis

### **Proactive Monitoring**
- Set up alerts for failed payment rates above 5%
- Monitor completion rates - should be above 85%
- Track revenue trends for business insights

## 🔐 **Security Considerations**

### **Access Control**
- Admin access should be restricted to authorized personnel
- Consider implementing role-based access for larger teams
- Regular access reviews and permission audits

### **Data Privacy**
- User information should be handled according to privacy policies
- Consider data retention policies for old requests
- Ensure secure handling of payment information

### **Audit Trail**
- All admin actions are logged
- Status changes are tracked with timestamps
- Maintain records for compliance and analysis

## 📞 **Support and Escalation**

### **When to Escalate**
- Unusual payment failure patterns
- System-wide issues affecting multiple requests
- User complaints about missing services

### **Contact Information**
- Technical issues: Check system logs first
- Payment provider issues: Contact Stripe or crypto providers
- User inquiries: Use request details to investigate

---

## Quick Reference

### **Package Types and Pricing**
- **Single Analysis**: $7 CAD
- **3-Analysis Pack**: $10 CAD (Save 52%)
- **5-Analysis Pack**: $15 CAD (Save 40%)
- **Monthly Unlimited**: $49 CAD/month
- **Basic Expert Review**: $99 CAD
- **Premium Expert Review**: $299 CAD
- **VIP Package**: $999 CAD

### **Status Definitions**
- **Pending**: Payment initiated, waiting for completion
- **Completed**: Successfully processed and delivered
- **Failed**: Payment or processing failed
- **Processing**: Currently being analyzed
- **Confirming**: Cryptocurrency payment confirming on blockchain

### **AI Providers**
- **Claude**: Anthropic's advanced reasoning AI
- **ChatGPT**: OpenAI's conversational AI
- **Gemini**: Google's multimodal AI
- **Grok**: xAI's real-time AI

This admin interface provides comprehensive tools for managing the AI Assistant service efficiently and ensuring excellent user experience. 