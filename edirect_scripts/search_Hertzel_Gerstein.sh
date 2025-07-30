#!/bin/bash
# EDirect search script for Hertzel Gerstein
# Generated on 2025-07-30 08:57:15

echo "🔍 Searching PubMed for Hertzel Gerstein..."

# Create output directory
mkdir -p pubmed_data

# Search and fetch publications
esearch -db pubmed -query '"Hertzel Gerstein"[Author]' | efetch -format medline > pubmed_data/Hertzel_Gerstein_publications.txt

if [ -s pubmed_data/Hertzel_Gerstein_publications.txt ]; then
    echo "✅ Search completed: pubmed_data/Hertzel_Gerstein_publications.txt"
    echo "📊 Publications found: $(grep -c "^PMID-" pubmed_data/Hertzel_Gerstein_publications.txt)"
else
    echo "❌ No results or search failed: pubmed_data/Hertzel_Gerstein_publications.txt"
fi
