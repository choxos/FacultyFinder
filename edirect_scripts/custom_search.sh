#!/bin/bash
# Custom EDirect search script
# Usage: ./custom_search.sh "Author Name" [output_filename]

if [ -z "$1" ]; then
    echo "Usage: $0 "Author Name" [output_filename]"
    echo "Example: $0 "Gordon Guyatt" gordon_guyatt.txt"
    exit 1
fi

AUTHOR_NAME="$1"
OUTPUT_FILE="${2:-$(echo "$1" | tr ' ' '_' | tr '[:upper:]' '[:lower:]').txt}"

echo "🔍 Searching PubMed for: $AUTHOR_NAME"
echo "📄 Output file: pubmed_data/$OUTPUT_FILE"

# Create output directory
mkdir -p pubmed_data

# Search and fetch
esearch -db pubmed -query ""$AUTHOR_NAME"[Author]" | efetch -format medline > "pubmed_data/$OUTPUT_FILE"

if [ -s "pubmed_data/$OUTPUT_FILE" ]; then
    pub_count=$(grep -c "^PMID-" "pubmed_data/$OUTPUT_FILE")
    echo "✅ Search completed: $pub_count publications found"
    echo "📁 File: pubmed_data/$OUTPUT_FILE"
else
    echo "❌ No results found or search failed"
fi
