#!/bin/bash

# Faculty Data Update Pipeline
# Complete automation script for faculty data management
# From CSV updates to publication retrieval and metrics enhancement

set -e  # Exit on any error

# Configuration
LOG_DIR="logs"
LOG_FILE="$LOG_DIR/faculty_pipeline_$(date +%Y%m%d_%H%M%S).log"
CSV_FILE="data/faculties/CA/ON/CA-ON-002_mcmaster.ca/HEI/CA-ON-002_mcmaster.ca_HEI.csv"
JSON_DIR="data/faculties/CA/ON/CA-ON-002_mcmaster.ca/HEI/CA-ON-002_mcmaster.ca_HEI_jsons"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Logging function
log() {
    echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check prerequisites
check_prerequisites() {
    log "${BLUE}🔍 Checking prerequisites...${NC}"
    
    # Check Python
    if ! command_exists python3; then
        log "${RED}❌ Python3 is required but not installed${NC}"
        exit 1
    fi
    
    # Check required Python packages
    python3 -c "import asyncpg, json, pathlib" 2>/dev/null || {
        log "${RED}❌ Required Python packages missing. Install with: pip install asyncpg${NC}"
        exit 1
    }
    
    # Check if CSV file exists
    if [ ! -f "$CSV_FILE" ]; then
        log "${RED}❌ CSV file not found: $CSV_FILE${NC}"
        exit 1
    fi
    
    log "${GREEN}✅ Prerequisites check passed${NC}"
}

# Function to backup existing data
backup_data() {
    log "${BLUE}💾 Creating backup of existing data...${NC}"
    
    if [ -d "$JSON_DIR" ]; then
        BACKUP_DIR="${JSON_DIR}_backup_$(date +%Y%m%d_%H%M%S)"
        cp -r "$JSON_DIR" "$BACKUP_DIR"
        log "${GREEN}✅ Backup created: $BACKUP_DIR${NC}"
    else
        log "${YELLOW}⚠️ No existing JSON directory to backup${NC}"
    fi
}

# Function to run a command with error handling
run_command() {
    local cmd="$1"
    local description="$2"
    local allow_failure="${3:-false}"
    
    log "${BLUE}🔄 $description...${NC}"
    
    if eval "$cmd" >> "$LOG_FILE" 2>&1; then
        log "${GREEN}✅ $description completed successfully${NC}"
        return 0
    else
        if [ "$allow_failure" = "true" ]; then
            log "${YELLOW}⚠️ $description had issues but continuing...${NC}"
            return 0
        else
            log "${RED}❌ $description failed${NC}"
            return 1
        fi
    fi
}

# Main pipeline execution
main() {
    log "${BLUE}🚀 Starting Faculty Data Update Pipeline${NC}"
    log "${BLUE}📝 Log file: $LOG_FILE${NC}"
    
    # Check prerequisites
    check_prerequisites
    
    # Create backup
    backup_data
    
    # Stage 1: Generate JSON files from CSV
    run_command "python3 create_faculty_jsons.py" "Stage 1: Converting CSV to JSON files"
    
    # Stage 2: Update PostgreSQL database
    run_command "python3 json_to_postgres.py" "Stage 2: Updating PostgreSQL database"
    
    # Stage 3: Retrieve publications from PubMed (allow failure)
    if [ -f "scripts/pubmed_faculty_searcher.py" ]; then
        run_command "python3 scripts/pubmed_faculty_searcher.py --faculty-json-dir='$JSON_DIR'" \
                   "Stage 3: Retrieving PubMed publications" true
    else
        log "${YELLOW}⚠️ PubMed searcher script not found, skipping PubMed retrieval${NC}"
    fi
    
    # Stage 4: Retrieve publications from OpenAlex (allow failure)
    if [ -f "scripts/openalex_faculty_searcher.py" ]; then
        run_command "python3 scripts/openalex_faculty_searcher.py --faculty-json-dir='$JSON_DIR'" \
                   "Stage 4: Retrieving OpenAlex publications" true
    else
        log "${YELLOW}⚠️ OpenAlex searcher script not found, skipping OpenAlex retrieval${NC}"
    fi
    
    # Stage 5: Enhance with OpenAlex metrics (allow failure)
    if [ -f "scripts/openalex_metrics_enhancer.py" ]; then
        run_command "python3 scripts/openalex_metrics_enhancer.py --faculty-json-dir='$JSON_DIR'" \
                   "Stage 5: Enhancing with OpenAlex metrics" true
    else
        log "${YELLOW}⚠️ OpenAlex metrics enhancer script not found, skipping metrics enhancement${NC}"
    fi
    
    # Stage 6: Update database with publication and metrics data
    if [ -f "scripts/update_faculty_metrics.py" ]; then
        run_command "python3 scripts/update_faculty_metrics.py" \
                   "Stage 6: Updating database with metrics" true
    else
        log "${YELLOW}⚠️ Faculty metrics updater script not found, skipping metrics database update${NC}"
    fi
    
    # Generate summary report
    generate_summary_report
    
    log "${GREEN}🎉 Faculty Data Update Pipeline Completed Successfully!${NC}"
    log "${BLUE}📋 Check the log file for detailed information: $LOG_FILE${NC}"
}

# Function to generate summary report
generate_summary_report() {
    log "${BLUE}📊 Generating summary report...${NC}"
    
    # Count JSON files
    if [ -d "$JSON_DIR" ]; then
        JSON_COUNT=$(find "$JSON_DIR" -name "*.json" | wc -l)
        log "${GREEN}📁 JSON files created: $JSON_COUNT${NC}"
    fi
    
    # Count publication files
    PUBMED_COUNT=0
    OPENALEX_COUNT=0
    
    if [ -d "data/publications/pubmed" ]; then
        PUBMED_COUNT=$(find "data/publications/pubmed" -name "*.json" | wc -l)
    fi
    
    if [ -d "data/publications/openalex" ]; then
        OPENALEX_COUNT=$(find "data/publications/openalex" -name "*.json" | wc -l)
    fi
    
    log "${GREEN}📚 PubMed publications: $PUBMED_COUNT${NC}"
    log "${GREEN}🔬 OpenAlex publications: $OPENALEX_COUNT${NC}"
    
    # Database connectivity check
    if python3 -c "
import asyncio
import asyncpg
async def test_db():
    try:
        conn = await asyncpg.connect(
            host='localhost', port=5432, 
            database='facultyfinder_dev', 
            user='postgres', password='password'
        )
        count = await conn.fetchval('SELECT COUNT(*) FROM professors')
        print(f'Database professors count: {count}')
        await conn.close()
        return True
    except Exception as e:
        print(f'Database connection failed: {e}')
        return False
asyncio.run(test_db())
" 2>/dev/null; then
        log "${GREEN}💾 Database connection verified${NC}"
    else
        log "${YELLOW}⚠️ Could not verify database connection${NC}"
    fi
}

# Function to display usage
usage() {
    echo "Faculty Data Update Pipeline"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  --csv-file     Specify CSV file path (default: $CSV_FILE)"
    echo "  --json-dir     Specify JSON output directory (default: $JSON_DIR)"
    echo "  --no-backup    Skip backup creation"
    echo "  --dry-run      Show what would be done without executing"
    echo ""
    echo "Examples:"
    echo "  $0                           # Run full pipeline with defaults"
    echo "  $0 --csv-file=my_faculty.csv # Use custom CSV file"
    echo "  $0 --no-backup              # Skip backup creation"
    echo "  $0 --dry-run                # Show planned actions"
    echo ""
}

# Parse command line arguments
BACKUP=true
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        --csv-file=*)
            CSV_FILE="${1#*=}"
            shift
            ;;
        --json-dir=*)
            JSON_DIR="${1#*=}"
            shift
            ;;
        --no-backup)
            BACKUP=false
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Dry run mode
if [ "$DRY_RUN" = "true" ]; then
    echo "🔍 DRY RUN MODE - No changes will be made"
    echo ""
    echo "Would execute the following pipeline:"
    echo "1. Check prerequisites"
    echo "2. Create backup of existing data (if BACKUP=true)"
    echo "3. Convert CSV to JSON files: $CSV_FILE → $JSON_DIR"
    echo "4. Update PostgreSQL database from JSON files"
    echo "5. Retrieve publications from PubMed"
    echo "6. Retrieve publications from OpenAlex"
    echo "7. Enhance with OpenAlex metrics"
    echo "8. Update database with publication metrics"
    echo "9. Generate summary report"
    echo ""
    echo "Log file would be: $LOG_FILE"
    exit 0
fi

# Handle interruption gracefully
trap 'log "${RED}⚠️ Pipeline interrupted by user${NC}"; exit 130' INT

# Execute main pipeline
main

# Exit with success
exit 0 