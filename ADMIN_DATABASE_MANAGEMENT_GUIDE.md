# Database Management - Admin Guide

This guide explains how to use the admin interface to manage universities, professors, and countries data with real-time updates reflected on the website.

## Overview

The Database Management system provides comprehensive tools for administrators to:
- **Manage Universities**: Add, edit, and delete university records
- **Manage Professors**: Add, edit, and delete faculty/professor profiles
- **Monitor Countries**: View country statistics derived from university data
- **Real-time Updates**: Changes are immediately reflected on the public website
- **Data Integrity**: Built-in validation and referential integrity checks

## Access

### Admin Database Management
- **URL**: `http://yourdomain.com/admin/database`
- **Navigation**: Admin Dashboard → Database

### Required Permissions
- Admin access to the FacultyFinder system
- Database write permissions for universities and professors tables

## Interface Overview

### 📊 **Statistics Dashboard**

The top section displays real-time database metrics:

#### **Universities Count**
- Total number of universities in the database
- Includes all university types (Public, Private, Community)

#### **Professors Count** 
- Total number of faculty/professor profiles
- Includes both full-time and adjunct positions

#### **Countries Count**
- Number of unique countries represented
- Derived from university locations

#### **Recent Additions (30d)**
- Combined count of universities and professors added in the last 30 days
- Helps track data growth and recent activity

### 🏗️ **Tab-Based Management**

The interface provides three main management sections:

#### **1. Universities Tab**
- View, create, edit, and delete university records
- Advanced filtering by country, province/state, and search
- Comprehensive university information management

#### **2. Professors Tab**
- Manage faculty and professor profiles
- Filter by university, department, and search criteria
- Complete academic profile management

#### **3. Countries Tab**
- Read-only view of country statistics
- Quick navigation to filter universities by country
- Overview of geographic distribution

## Universities Management

### 🏛️ **University Information Fields**

#### **Required Fields**
- **University Code**: Unique identifier (e.g., CA-ON-001)
- **University Name**: Full official name
- **Country**: Country where university is located

#### **Optional Fields**
- **Province/State**: Regional location
- **City**: Specific city location
- **Address**: Complete postal address
- **Website**: Official university website URL
- **University Type**: Public, Private, or Community
- **Languages**: Languages of instruction
- **Year Established**: Founding year

### 🔍 **University Filtering & Search**

#### **Country Filter**
- Dropdown populated with all countries in the database
- Instantly filters universities by selected country

#### **Province/State Filter**
- Text input with real-time search
- Matches partial province/state names

#### **Search Filter**
- Searches across university names and codes
- Real-time results with 500ms debounce

### ✏️ **University Operations**

#### **Add University**
1. Click "Add University" button
2. Fill in required fields (marked with *)
3. Complete optional fields as needed
4. Click "Save University"
5. Changes immediately reflect on the website

#### **Edit University**
1. Click the edit icon (✏️) next to any university
2. Modify fields in the popup form
3. Click "Save University"
4. Updates are immediately live

#### **Delete University**
1. Click the delete icon (🗑️) next to the university
2. Confirm deletion in the popup dialog
3. **Safety Check**: Cannot delete if professors are associated
4. If deleted, removal is immediate and irreversible

### 🚨 **University Safety Features**

#### **Referential Integrity**
- Cannot delete universities with associated professors
- System shows count of associated professors before deletion
- Prevents data orphaning and maintains consistency

#### **Validation**
- University code uniqueness enforcement
- URL format validation for websites
- Year range validation (1000-2030)

## Professors Management

### 👨‍🏫 **Professor Information Fields**

#### **Required Fields**
- **Faculty ID**: Unique identifier (e.g., CA-ON-002-00125)
- **First Name**: Professor's first name
- **Last Name**: Professor's last name  
- **University**: Associated university (dropdown selection)

#### **Optional Fields**
- **Middle Names**: Middle name(s) or initials
- **Faculty**: Faculty/school name
- **Department**: Department or division
- **Position**: Academic position/title
- **Full Time**: Employment status checkbox
- **Adjunct**: Adjunct faculty checkbox
- **University Email**: Official institutional email
- **Website**: Personal or department website
- **Degrees**: Academic qualifications
- **Research Areas**: Research interests and specializations
- **Google Scholar**: Google Scholar profile URL
- **ORCID**: ORCID identifier
- **LinkedIn**: LinkedIn profile URL

### 🔍 **Professor Filtering & Search**

#### **University Filter**
- Dropdown populated with all universities
- Shows only professors from selected university

#### **Department Filter**
- Text input for department-based filtering
- Partial matching with real-time updates

#### **Search Filter**
- Searches across names, faculty IDs, and research areas
- Comprehensive text matching

### ✏️ **Professor Operations**

#### **Add Professor**
1. Click "Add Professor" button
2. Fill in required fields
3. Select university from dropdown
4. Add optional academic and contact information
5. Click "Save Professor"
6. Profile immediately appears on the website

#### **Edit Professor**
1. Click the edit icon (✏️) next to any professor
2. Modify information in the comprehensive form
3. Click "Save Professor"
4. Changes are immediately visible on professor profile pages

#### **Delete Professor**
1. Click the delete icon (🗑️) next to the professor
2. Confirm deletion in the popup dialog
3. Deletion is immediate and removes the professor profile from the website

### 🎓 **Professor Profile Features**

#### **Automatic Name Building**
- Full name automatically constructed from first, middle, and last names
- Handles various name formats and cultural variations

#### **Academic Links**
- Integration with major academic platforms
- Direct links to Google Scholar, ORCID, and LinkedIn profiles
- Supports research discoverability

#### **Research Areas**
- Semicolon-separated research interests
- Enables sophisticated search and matching algorithms
- Supports interdisciplinary research discovery

## Countries Management

### 🌍 **Country Statistics**

The Countries tab provides a read-only overview of geographic distribution:

#### **Country Information**
- **Country Name**: Full country name
- **Universities Count**: Number of universities in that country
- **Provinces/States Count**: Number of unique provinces/states

#### **Quick Navigation**
- "View Universities" button for each country
- Automatically switches to Universities tab with country filter applied
- Streamlined workflow for country-specific management

### 📊 **Geographic Insights**

#### **Distribution Analysis**
- Identify countries with the most universities
- Monitor geographic expansion of the database
- Plan targeted data collection efforts

#### **Data Completeness**
- Spot countries with incomplete province/state data
- Identify opportunities for data enhancement
- Support strategic database growth

## Real-Time Website Updates

### ⚡ **Immediate Reflection**

All changes made through the admin interface are immediately reflected on the public website:

#### **University Changes**
- New universities appear in university listings
- Updated information shows on university profile pages
- Deleted universities are removed from all public views

#### **Professor Changes**
- New professors appear in faculty listings
- Updated profiles reflect changes on individual professor pages
- Research area changes affect search results immediately
- Deleted professors are removed from all public listings

#### **Search & Discovery**
- Updated research areas immediately affect search algorithms
- New universities appear in location filters
- Enhanced discoverability through real-time indexing

### 🔄 **Data Consistency**

#### **Cross-Platform Synchronization**
- API endpoints immediately reflect database changes
- Search functionality updates in real-time
- No caching delays or sync issues

#### **User Experience**
- Visitors see the most current information
- No delays between admin updates and public visibility
- Consistent data across all platform features

## Advanced Features

### 🚀 **Bulk Operations**

#### **Filtering for Efficiency**
- Use filters to isolate specific data sets
- Perform targeted reviews and updates
- Streamline large-scale data management

#### **Pagination**
- Handle large datasets with efficient pagination
- 50 records per page for optimal performance
- Quick navigation through extensive lists

### 📋 **Data Import Considerations**

#### **CSV Integration**
- Admin interface complements existing CSV import workflows
- Manual verification and correction of imported data
- Quality control for automated data ingestion

#### **Faculty ID Management**
- Consistent faculty ID formatting
- Unique identifier enforcement
- Cross-reference with existing data systems

### 🔐 **Data Validation**

#### **University Validation**
- University code uniqueness
- Website URL format verification
- Year established range checking

#### **Professor Validation**
- Faculty ID uniqueness enforcement
- Email format validation
- University association verification

## Best Practices

### 📝 **Data Entry Guidelines**

#### **University Data**
- Use official university names and codes
- Verify website URLs before saving
- Include complete address information when available
- Standardize country and province/state names

#### **Professor Data**
- Use complete, official names
- Verify university associations
- Include comprehensive research area descriptions
- Maintain consistent academic link formats

### 🔍 **Quality Control**

#### **Regular Reviews**
- Periodically review country statistics for data gaps
- Verify university-professor associations
- Check for duplicate or inconsistent entries
- Monitor data completeness across fields

#### **Data Integrity Checks**
- Verify external links periodically
- Confirm university affiliations
- Update research areas as they evolve
- Maintain current contact information

### 🚨 **Safety Measures**

#### **Before Deletion**
- Always verify the impact of deletions
- Check for associated records
- Consider data archiving instead of deletion
- Document reasons for major changes

#### **Backup Considerations**
- Changes are immediate and irreversible
- Ensure proper database backup procedures
- Maintain change logs for audit purposes
- Test changes in development environment when possible

## Troubleshooting

### 🔧 **Common Issues**

#### **Cannot Delete University**
- **Symptom**: Error message about associated professors
- **Solution**: Either reassign professors to other universities or delete professors first
- **Prevention**: Check professor associations before university deletion

#### **Faculty ID Conflicts**
- **Symptom**: Error when creating professor with existing Faculty ID
- **Solution**: Use unique Faculty ID or update existing professor
- **Prevention**: Check existing IDs before creating new professors

#### **University Code Conflicts**
- **Symptom**: Error when creating university with existing code
- **Solution**: Use unique university code or update existing university
- **Prevention**: Follow standardized university code format

### 📊 **Performance Considerations**

#### **Large Dataset Handling**
- Use filters to reduce data load
- Pagination prevents browser performance issues
- Search functionality optimized for quick results

#### **Real-Time Updates**
- Changes may take a few seconds to propagate across all systems
- Refresh browser if changes don't appear immediately
- Check network connectivity for any delays

## API Reference

### 🔌 **University Endpoints**

#### **Get Universities**
```
GET /api/v1/admin/universities
```
Parameters:
- `country`: Filter by country
- `province_state`: Filter by province/state
- `search`: Search universities
- `limit`: Results per page (default: 100)
- `offset`: Page offset

#### **Create University**
```
POST /api/v1/admin/universities
```
Body: University data object

#### **Update University**
```
PUT /api/v1/admin/universities/{id}
```
Body: Updated university data

#### **Delete University**
```
DELETE /api/v1/admin/universities/{id}
```

### 👨‍🏫 **Professor Endpoints**

#### **Get Professors**
```
GET /api/v1/admin/professors
```
Parameters:
- `university_code`: Filter by university
- `department`: Filter by department
- `search`: Search professors
- `limit`: Results per page (default: 100)
- `offset`: Page offset

#### **Create Professor**
```
POST /api/v1/admin/professors
```
Body: Professor data object

#### **Update Professor**
```
PUT /api/v1/admin/professors/{id}
```
Body: Updated professor data

#### **Delete Professor**
```
DELETE /api/v1/admin/professors/{id}
```

### 🌍 **Country & Statistics**

#### **Get Countries**
```
GET /api/v1/admin/countries
```

#### **Get Database Statistics**
```
GET /api/v1/admin/database/stats
```

## Security Considerations

### 🔐 **Access Control**
- Admin-only access to database management
- Secure authentication required
- Regular access permission reviews

### 🛡️ **Data Protection**
- All changes logged for audit purposes
- Secure handling of personal information
- Compliance with data protection regulations

### 🔍 **Monitoring**
- Track all database modifications
- Monitor for unusual activity patterns
- Maintain comprehensive change logs

---

## Quick Reference

### 🎯 **Essential Workflows**

#### **Adding New University**
1. Universities Tab → Add University
2. Fill required fields (Code, Name, Country)
3. Add optional details
4. Save → Immediately live on website

#### **Adding New Professor**
1. Professors Tab → Add Professor
2. Fill required fields (Faculty ID, Names, University)
3. Add academic and contact details
4. Save → Profile immediately accessible

#### **Data Cleanup**
1. Use filters to identify problematic records
2. Edit records to correct issues
3. Delete only when necessary and safe
4. Monitor impact on website functionality

### ⚡ **Key Features**
- **Real-time updates**: Changes immediately reflected on website
- **Data integrity**: Built-in validation and safety checks
- **Comprehensive search**: Advanced filtering across all fields
- **User-friendly**: Intuitive interface with professional design
- **Scalable**: Handles large datasets with efficient pagination

This database management interface provides complete control over the FacultyFinder database while ensuring data integrity and immediate website updates. Use it to maintain accurate, current information that serves researchers and academics worldwide. 