#!/bin/bash
# Custom structured EDirect search script
# Usage: ./custom_search_structured.sh "Author Name" "University Code" [Country] [Province]

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: $0 "Author Name" "University Code" [Country] [Province]"
    echo "Example: $0 "Gordon Guyatt" "CA-ON-002_mcmaster.ca" "CA" "ON""
    echo ""
    echo "Available Universities:"
    echo "  McMaster: CA-ON-002_mcmaster.ca"
    echo "  Toronto: CA-ON-001_utoronto.ca"
    echo "  Waterloo: CA-ON-003_uwaterloo.ca"
    exit 1
fi

AUTHOR_NAME="$1"
UNIVERSITY_CODE="$2"
COUNTRY="${3:-CA}"
PROVINCE="${4:-ON}"

# Clean name for filename
CLEAN_NAME=$(echo "$AUTHOR_NAME" | tr ' ' '_' | tr '[:upper:]' '[:lower:]')
UNIVERSITY_PATH="data/publications/pubmed/$COUNTRY/$PROVINCE/$UNIVERSITY_CODE"
OUTPUT_FILE="$UNIVERSITY_PATH/${CLEAN_NAME}_publications.txt"

echo "🔍 Searching PubMed for: $AUTHOR_NAME"
echo "🏫 University: $UNIVERSITY_CODE"
echo "📁 Output: $OUTPUT_FILE"

# Create university directory
mkdir -p "$UNIVERSITY_PATH"

# Search and fetch
esearch -db pubmed -query ""$AUTHOR_NAME"[Author]" | efetch -format medline > "$OUTPUT_FILE"

if [ -s "$OUTPUT_FILE" ]; then
    pub_count=$(grep -c "^PMID-" "$OUTPUT_FILE")
    echo "✅ Search completed: $pub_count publications found"
    echo "📁 File: $OUTPUT_FILE"
else
    echo "❌ No results found or search failed"
fi
