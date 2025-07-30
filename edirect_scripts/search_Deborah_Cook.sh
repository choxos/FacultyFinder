#!/bin/bash
# EDirect search script for Deborah Cook
# Generated on 2025-07-30 08:57:15

echo "🔍 Searching PubMed for Deborah Cook..."

# Create output directory
mkdir -p pubmed_data

# Search and fetch publications
esearch -db pubmed -query '"Deborah Cook"[Author]' | efetch -format medline > pubmed_data/Deborah_Cook_publications.txt

if [ -s pubmed_data/Deborah_Cook_publications.txt ]; then
    echo "✅ Search completed: pubmed_data/Deborah_Cook_publications.txt"
    echo "📊 Publications found: $(grep -c "^PMID-" pubmed_data/Deborah_Cook_publications.txt)"
else
    echo "❌ No results or search failed: pubmed_data/Deborah_Cook_publications.txt"
fi
