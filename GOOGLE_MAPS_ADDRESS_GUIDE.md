# Google Maps Address Integration Guide

## 🎯 **Overview**

This guide shows you how to deploy and manage the enhanced Google Maps integration for FacultyFinder universities, using structured address data from your CSV files.

---

## 🗺️ **What's New**

### **Enhanced Address Structure**
Your `data/university_codes.csv` already contains parsed address components:
- `building_number` - Street number (e.g., "1407")
- `street` - Street name (e.g., "14 Ave NW")  
- `postal_code` - Postal/ZIP code (e.g., "T2N 4R3")

### **Before vs. After**

**Before:**
```
🏛️ University of Toronto
📍 Toronto, Ontario, Canada
```

**After:**
```
🏛️ University of Toronto  
📍 Toronto, Ontario, Canada
🗺️ [Maps] ← Enhanced Google Maps button
🏠 27 King's College Circle, M5S 1A1
```

---

## 🚀 **Quick Deployment**

### **One-Command Setup:**
```bash
./deploy_google_maps_address_system.sh
```

This will:
- ✅ Update database schema with new address columns
- ✅ Import address data from CSV
- ✅ Update FastAPI endpoints  
- ✅ Deploy enhanced frontend
- ✅ Restart service and verify functionality

---

## 📋 **Step-by-Step Manual Setup**

### **Step 1: Update Database Schema**
```bash
python3 update_university_address_schema.py
```

**What this does:**
- Adds `building_number`, `street`, `postal_code` columns to universities table
- Creates database indexes for performance
- Creates helper functions for address formatting

### **Step 2: Import Address Data**
```bash
./update_db.sh universities
```

**What this does:**
- Reads `data/university_codes.csv`
- Updates existing universities with address data
- Adds new universities if found in CSV

### **Step 3: Restart Service**
```bash
sudo systemctl restart facultyfinder.service
```

---

## 🏗️ **Technical Implementation**

### **Database Schema Changes**

**New Columns Added:**
```sql
ALTER TABLE universities 
ADD COLUMN building_number VARCHAR(50),
ADD COLUMN street VARCHAR(200),
ADD COLUMN postal_code VARCHAR(20);
```

**Address Helper Function:**
```sql
CREATE OR REPLACE FUNCTION get_full_address(
    university_name TEXT,
    building_number TEXT,
    street TEXT,
    city TEXT,
    province_state TEXT,
    postal_code TEXT,
    country TEXT
) RETURNS TEXT
```

### **FastAPI Endpoint Updates**

**University Model Enhanced:**
```python
class University(BaseModel):
    # ... existing fields ...
    building_number: Optional[str] = None
    street: Optional[str] = None
    postal_code: Optional[str] = None
    full_address: Optional[str] = None  # Computed field
```

**API Response Example:**
```json
{
  "name": "McMaster University",
  "city": "Hamilton",
  "country": "Canada",
  "building_number": "1280",
  "street": "Main Street West",
  "postal_code": "L8S 4L8",
  "full_address": "McMaster University, 1280 Main Street West, Hamilton, Ontario L8S 4L8, Canada"
}
```

### **Frontend Enhancements**

**New Google Maps Button:**
```html
<a href="https://www.google.com/maps/search/[encoded_full_address]" 
   target="_blank" class="btn btn-sm btn-outline-primary google-maps-btn">
    <i class="fas fa-map-marked-alt me-1"></i>Maps
</a>
```

**Address Display Card:**
```html
<div class="address-details">
    <i class="fas fa-home me-2"></i>
    <strong>1280 Main Street West, L8S 4L8</strong>
</div>
```

---

## 📊 **Database Updates**

### **When You Update university_codes.csv:**

**Option 1: Quick Update**
```bash
./update_db.sh universities
```

**Option 2: Manual Update**
```bash
python3 update_database_from_csv.py --mode universities --restart
```

**Option 3: Custom CSV File**
```bash
python3 update_database_from_csv.py --mode universities --csv path/to/your/file.csv --restart
```

### **Address Data Format in CSV:**

Your CSV should have these columns:
```
university_code,university_name,country,province_state,city,building_number,street,postal_code
CA-ON-002,McMaster University,Canada,Ontario,Hamilton,1280,Main Street West,L8S 4L8
```

**Address Reconstruction:**
```
university_name, building_number street, city, province_state postal_code, country
McMaster University, 1280 Main Street West, Hamilton, Ontario L8S 4L8, Canada
```

---

## 🎨 **Frontend Features**

### **Card View (Grid Layout)**
- **Enhanced Maps Button:** Blue styled button with icon
- **Address Details Card:** Shows building number + street + postal code
- **Hover Effects:** Smooth animations and shadows

### **Table View (List Layout)**  
- **Compact Maps Button:** Smaller button in table cell
- **Address Preview:** Street address shown below city name
- **Responsive Design:** Works on mobile devices

### **CSS Styling**
```css
.google-maps-btn {
    font-size: 0.875rem;
    padding: 0.25rem 0.5rem;
    border-radius: 0.375rem;
    transition: all 0.2s ease;
}

.address-details {
    background-color: rgba(108, 117, 125, 0.1);
    padding: 0.375rem 0.5rem;
    border-radius: 0.25rem;
    border-left: 3px solid #6c757d;
}
```

---

## 🔧 **Troubleshooting**

### **Common Issues**

**❌ "Database connection failed"**
```bash
# Check .env file
cat .env
# Verify database credentials
```

**❌ "Column does not exist"**
```bash
# Run schema update first
python3 update_university_address_schema.py
```

**❌ "Address data not showing"**
```bash
# Update university data
./update_db.sh universities
# Check API response
curl "http://localhost:8008/api/v1/universities?per_page=1"
```

**❌ "Maps button not working"**
```bash
# Restart service
sudo systemctl restart facultyfinder.service
# Check service status
sudo systemctl status facultyfinder.service
```

### **Verification Steps**

**1. Check Database Schema:**
```sql
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'universities' 
AND column_name IN ('building_number', 'street', 'postal_code');
```

**2. Test API Response:**
```bash
curl "http://localhost:8008/api/v1/universities?per_page=1" | python3 -m json.tool
```

**3. Check Frontend:**
- Visit `/universities` page
- Look for blue "Maps" buttons
- Verify address details are displayed

---

## 📱 **Mobile Responsiveness**

### **Responsive Features:**
- **Smaller buttons** on mobile devices
- **Compact address display** with appropriate font sizes
- **Touch-friendly** Maps buttons with adequate spacing
- **Responsive grid** that adapts to screen size

### **CSS Media Queries:**
```css
@media (max-width: 576px) {
    .google-maps-btn {
        font-size: 0.75rem;
        padding: 0.2rem 0.4rem;
    }
    
    .address-details {
        font-size: 0.8rem;
        padding: 0.25rem 0.4rem;
    }
}
```

---

## 🎯 **Best Practices**

### **For CSV Data:**
- ✅ Keep address components separate (building_number, street, postal_code)
- ✅ Use consistent formatting for postal codes
- ✅ Include complete street names
- ✅ Verify address accuracy with Google Maps

### **For Database Updates:**
- ✅ Always backup before major updates
- ✅ Test on staging environment first
- ✅ Use incremental updates for regular changes
- ✅ Monitor service status after deployments

### **For Production:**
- ✅ Deploy during low-traffic periods
- ✅ Test all Maps buttons after deployment
- ✅ Verify responsive design on mobile
- ✅ Monitor for any broken Maps links

---

## 📚 **File Reference**

### **New Files Created:**
- `update_university_address_schema.py` - Database schema updater
- `deploy_google_maps_address_system.sh` - Complete deployment script
- `GOOGLE_MAPS_ADDRESS_GUIDE.md` - This documentation

### **Modified Files:**
- `webapp/main.py` - Updated University model and API endpoint
- `webapp/static/universities.html` - Enhanced frontend with Maps buttons
- `webapp/static/css/facultyfinder.css` - New CSS styles for Maps integration
- `update_database_from_csv.py` - Added university update functionality
- `update_db.sh` - Added universities mode

---

## 🌐 **Testing Your Deployment**

### **Quick Verification:**
1. **Visit Universities Page:** `https://facultyfinder.io/universities`
2. **Look for Maps Buttons:** Blue buttons with map icon
3. **Click a Maps Button:** Should open Google Maps with precise location
4. **Check Address Display:** Should show building number + street + postal code
5. **Test Mobile View:** Ensure responsive design works

### **API Testing:**
```bash
# Test universities endpoint
curl "https://facultyfinder.io/api/v1/universities?per_page=1"

# Should include new fields:
# "building_number": "1280"
# "street": "Main Street West"  
# "postal_code": "L8S 4L8"
# "full_address": "McMaster University, 1280 Main Street West, Hamilton, Ontario L8S 4L8, Canada"
```

---

## ✅ **Summary**

### **What You Get:**
- 🗺️ **Enhanced Google Maps integration** with precise addresses
- 🏠 **Detailed address display** showing building number + street
- 🎨 **Professional UI improvements** with styled Maps buttons
- 📱 **Mobile-responsive design** that works on all devices
- 🔧 **Easy database updates** with new CSV structure
- 📊 **Comprehensive API enhancements** with new address fields

### **Address Format:**
```
Input CSV: building_number="1280", street="Main Street West", postal_code="L8S 4L8"
Output: "McMaster University, 1280 Main Street West, Hamilton, Ontario L8S 4L8, Canada"
Google Maps: Opens precise location with full address
```

### **Quick Commands:**
```bash
# Deploy everything
./deploy_google_maps_address_system.sh

# Update universities only  
./update_db.sh universities

# Regular faculty updates (unchanged)
./update_db.sh
```

**Your Google Maps integration is now professional-grade and ready for production! 🚀**
