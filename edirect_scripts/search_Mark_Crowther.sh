#!/bin/bash
# EDirect search script for Mark Crowther
# Generated on 2025-07-30 08:57:15

echo "🔍 Searching PubMed for Mark Crowther..."

# Create output directory
mkdir -p pubmed_data

# Search and fetch publications
esearch -db pubmed -query '"Mark Crowther"[Author]' | efetch -format medline > pubmed_data/Mark_Crowther_publications.txt

if [ -s pubmed_data/Mark_Crowther_publications.txt ]; then
    echo "✅ Search completed: pubmed_data/Mark_Crowther_publications.txt"
    echo "📊 Publications found: $(grep -c "^PMID-" pubmed_data/Mark_Crowther_publications.txt)"
else
    echo "❌ No results or search failed: pubmed_data/Mark_Crowther_publications.txt"
fi
