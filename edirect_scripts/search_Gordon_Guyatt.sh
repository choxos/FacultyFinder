#!/bin/bash
# EDirect search script for Gordon Guyatt
# Generated on 2025-07-30 08:57:15

echo "🔍 Searching PubMed for Gordon Guyatt..."

# Create output directory
mkdir -p pubmed_data

# Search and fetch publications
esearch -db pubmed -query '"Gordon Guyatt"[Author]' | efetch -format medline > pubmed_data/Gordon_Guyatt_publications.txt

if [ -s pubmed_data/Gordon_Guyatt_publications.txt ]; then
    echo "✅ Search completed: pubmed_data/Gordon_Guyatt_publications.txt"
    echo "📊 Publications found: $(grep -c "^PMID-" pubmed_data/Gordon_Guyatt_publications.txt)"
else
    echo "❌ No results or search failed: pubmed_data/Gordon_Guyatt_publications.txt"
fi
