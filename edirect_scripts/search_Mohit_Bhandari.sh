#!/bin/bash
# EDirect search script for Mohit Bhandari
# Generated on 2025-07-30 08:57:15

echo "🔍 Searching PubMed for Mohit Bhandari..."

# Create output directory
mkdir -p pubmed_data

# Search and fetch publications
esearch -db pubmed -query '"Mohit Bhandari"[Author]' | efetch -format medline > pubmed_data/Mohit_Bhandari_publications.txt

if [ -s pubmed_data/Mohit_Bhandari_publications.txt ]; then
    echo "✅ Search completed: pubmed_data/Mohit_Bhandari_publications.txt"
    echo "📊 Publications found: $(grep -c "^PMID-" pubmed_data/Mohit_Bhandari_publications.txt)"
else
    echo "❌ No results or search failed: pubmed_data/Mohit_Bhandari_publications.txt"
fi
