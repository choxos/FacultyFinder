# Academic Profile Discovery System

A comprehensive system for automatically discovering and validating academic profiles across multiple platforms using faculty name variations.

## 🎯 Overview

The Profile Discovery System searches across academic and professional platforms to find faculty profiles using:
- **Two name variations**: `first_name + last_name` and `first_name + middle_name + last_name`
- **Multiple platforms**: Google Scholar, ORCID, OpenAlex, ResearchGate, Academia.edu, LinkedIn, Scopus, Web of Science
- **Confidence scoring**: Each result gets a confidence score (0-1) based on name similarity
- **Easy validation**: Results are presented for manual verification before updating profiles

## 🔧 System Components

### 1. Core Scripts

| Script | Purpose |
|--------|---------|
| `profile_discoverer.py` | Main discovery engine - searches all platforms |
| `update_profiles_from_discovery.py` | Updates JSON files with discovered profiles |
| `PROFILE_DISCOVERY_GUIDE.md` | This comprehensive guide |

### 2. Supported Platforms

✅ **Currently Supported:**
- **Google Scholar** - Academic publications and citations
- **ORCID** - Researcher identifier registry  
- **OpenAlex** - Open academic graph
- **ResearchGate** - Academic social network
- **Academia.edu** - Academic papers and profiles

🔄 **Planned Support:**
- **Scopus** - Citation database (requires API access)
- **Web of Science** - Citation database (requires API access)
- **LinkedIn** - Professional networking (requires API access)

## 🚀 Quick Start

### Step 1: Install Dependencies

```bash
pip install beautifulsoup4 aiohttp requests
```

### Step 2: Run Profile Discovery

```bash
# Discover profiles for all faculty
python3 profile_discoverer.py

# Discover profiles for specific faculty
python3 profile_discoverer.py --faculty-id "CA-ON-002-00001"

# Custom JSON directory
python3 profile_discoverer.py --json-dir "path/to/your/json/files"
```

### Step 3: Update Faculty Profiles

```bash
# Automatic update (high confidence only)
python3 update_profiles_from_discovery.py --mode auto

# Interactive update (manual validation)
python3 update_profiles_from_discovery.py --mode interactive

# Generate validation report
python3 update_profiles_from_discovery.py --mode validate
```

## 📋 Detailed Usage

### Discovery Process

1. **Name Variation Generation**
   ```
   Faculty: "John Michael Smith"
   Variations:
   - "John Smith"
   - "John Michael Smith"
   ```

2. **Platform Searching**
   - Each variation is searched on each platform
   - Results are scored for confidence
   - Top 3 results per platform are kept

3. **Confidence Scoring**
   - 🟢 **High (0.8-1.0)**: Exact or very close name match
   - 🟡 **Medium (0.5-0.8)**: Partial name match
   - 🔴 **Low (0.0-0.5)**: Weak name match

### Command Line Options

#### Profile Discovery (`profile_discoverer.py`)

```bash
python3 profile_discoverer.py [OPTIONS]

Options:
  --json-dir          Directory with faculty JSON files
  --output           Output file for discovery report
  --faculty-id       Process only specific faculty ID
```

#### Profile Updates (`update_profiles_from_discovery.py`)

```bash
python3 update_profiles_from_discovery.py [OPTIONS]

Options:
  --json-dir         Directory with faculty JSON files
  --report          Discovery report file to use
  --mode            Update mode: auto, interactive, validate
  --confidence      Confidence threshold for auto mode (0.0-1.0)
```

### Update Modes

#### 1. Auto Mode (Recommended for Initial Run)
```bash
python3 update_profiles_from_discovery.py --mode auto --confidence 0.8
```
- Automatically updates profiles with high confidence (≥0.8)
- Safe for bulk processing
- No manual intervention required

#### 2. Interactive Mode (Recommended for Verification)
```bash
python3 update_profiles_from_discovery.py --mode interactive
```
- Shows all discovered profiles for manual selection
- Allows skipping uncertain matches
- Best for accuracy and validation

#### 3. Validation Mode (Generate Reports)
```bash
python3 update_profiles_from_discovery.py --mode validate
```
- Generates HTML report of current profiles
- No updates made to data
- Good for reviewing current state

## 📊 Example Workflow

### Complete Discovery and Update Process

```bash
# Step 1: Discover profiles for all faculty
echo "🔍 Discovering profiles..."
python3 profile_discoverer.py

# Step 2: Auto-update high confidence matches
echo "🤖 Auto-updating high confidence profiles..."
python3 update_profiles_from_discovery.py --mode auto --confidence 0.8

# Step 3: Interactive review of remaining profiles
echo "🖱️ Interactive review of medium confidence profiles..."
python3 update_profiles_from_discovery.py --mode interactive

# Step 4: Generate validation report
echo "📄 Generating validation report..."
python3 update_profiles_from_discovery.py --mode validate

echo "✅ Profile discovery completed!"
```

### Single Faculty Testing

```bash
# Test with one faculty member
python3 profile_discoverer.py --faculty-id "CA-ON-002-00001"

# Review and update their profiles
python3 update_profiles_from_discovery.py --mode interactive
```

## 📄 Output Files

### Discovery Report (`profile_discovery_report.json`)

```json
{
  "timestamp": "2025-01-09 20:00:00",
  "total_faculty": 7,
  "discovery_results": [
    {
      "faculty_id": "CA-ON-002-00001",
      "name": "Julia Abelson",
      "name_variations": ["Julia Abelson"],
      "existing_profiles": {
        "gscholar": "",
        "orcid": "",
        "openalex": "",
        ...
      },
      "discovered_profiles": {
        "google_scholar": [
          {
            "url": "https://scholar.google.com/citations?user=xyz",
            "title": "Julia Abelson",
            "description": "McMaster University",
            "confidence": 0.95,
            "name_variation": "Julia Abelson"
          }
        ]
      },
      "recommendations": {
        "google_scholar": {
          "url": "https://scholar.google.com/citations?user=xyz",
          "confidence": 0.95,
          "reason": "High confidence match"
        }
      }
    }
  ]
}
```

### Validation Report (`profile_validation_report.html`)

Interactive HTML report showing:
- Current profile status for each faculty
- Links to existing profiles
- Missing profile indicators
- Easy validation and verification

## 🛠️ Advanced Configuration

### Rate Limiting

The system includes built-in rate limiting to respect platform policies:

```python
rate_limits = {
    'google_scholar': 2,  # seconds between requests
    'orcid': 1,
    'researchgate': 3,
    'academia': 2,
    'openalex': 1
}
```

### Custom Search Parameters

You can modify the search behavior by editing `profile_discoverer.py`:

1. **Affiliation-based search**: Include university name in searches
2. **Extended name variations**: Add nicknames or alternative names
3. **Custom confidence thresholds**: Adjust scoring algorithms

### Batch Processing

For large faculty datasets:

```bash
# Process in smaller batches
python3 profile_discoverer.py --json-dir "batch1/"
python3 profile_discoverer.py --json-dir "batch2/"

# Combine results
cat profile_discovery_report_*.json > combined_report.json
```

## 🔍 Troubleshooting

### Common Issues

1. **Rate Limiting**
   ```
   Error: Too many requests
   Solution: Increase delays in rate_limits configuration
   ```

2. **No Results Found**
   ```
   Check:
   - Name spelling variations
   - Platform availability
   - Network connectivity
   ```

3. **Low Confidence Scores**
   ```
   Solutions:
   - Try additional name variations
   - Include middle initials
   - Check for name changes or aliases
   ```

### Debug Mode

Enable detailed logging:

```bash
export PROFILE_DISCOVERY_LOG_LEVEL=DEBUG
python3 profile_discoverer.py --faculty-id "CA-ON-002-00001"
```

## 📈 Performance Optimization

### For Large Datasets

1. **Parallel Processing**: Run multiple instances with different faculty subsets
2. **Caching**: Store successful searches to avoid re-querying
3. **Incremental Updates**: Only search for faculty with missing profiles

### Example Parallel Processing

```bash
# Split faculty list and run in parallel
python3 profile_discoverer.py --faculty-id "CA-ON-002-00001" &
python3 profile_discoverer.py --faculty-id "CA-ON-002-00002" &
python3 profile_discoverer.py --faculty-id "CA-ON-002-00003" &
wait
```

## 🔄 Integration with Main Workflow

### Add to Faculty Update Pipeline

Update your `update_faculty_pipeline.sh`:

```bash
# ... existing stages ...

# Stage 6: Discover academic profiles
echo "🔍 Stage 6: Discovering academic profiles..."
python3 profile_discoverer.py
if [ $? -eq 0 ]; then
    echo "✅ Profile discovery completed"
    
    # Auto-update high confidence profiles
    python3 update_profiles_from_discovery.py --mode auto --confidence 0.8
    echo "✅ High confidence profiles updated"
else
    echo "⚠️ Profile discovery had issues"
fi

# Stage 7: Generate validation report
echo "📄 Stage 7: Generating profile validation report..."
python3 update_profiles_from_discovery.py --mode validate

echo "🎉 Complete Faculty Pipeline with Profile Discovery Completed!"
```

## 📋 Manual Validation Best Practices

### When Using Interactive Mode

1. **Check Affiliation**: Verify the person works at the correct institution
2. **Check Research Areas**: Ensure research topics match
3. **Check Publication Dates**: Look for recent activity
4. **Cross-Reference**: Compare with existing known information

### Confidence Guidelines

- **0.9-1.0**: Almost certainly correct - safe to auto-update
- **0.7-0.9**: Likely correct - review manually
- **0.5-0.7**: Possibly correct - verify carefully  
- **0.0-0.5**: Unlikely correct - probably skip

## 🎯 Expected Results

### Success Rates by Platform

Based on typical academic faculty:

- **Google Scholar**: 60-80% (many academics have profiles)
- **ORCID**: 40-70% (growing adoption)
- **OpenAlex**: 70-90% (comprehensive coverage)
- **ResearchGate**: 30-60% (varies by field)
- **Academia.edu**: 20-40% (declining usage)

### Time Estimates

- **Small dataset (7 faculty)**: 2-3 minutes
- **Medium dataset (50 faculty)**: 15-20 minutes  
- **Large dataset (500 faculty)**: 2-3 hours

This system significantly speeds up the profile discovery process while maintaining accuracy through confidence scoring and manual validation options! 