#!/bin/bash
# EDirect search script for Bram Rochwerg
# Generated on 2025-07-30 08:57:15

echo "🔍 Searching PubMed for Bram Rochwerg..."

# Create output directory
mkdir -p pubmed_data

# Search and fetch publications
esearch -db pubmed -query '"Bram Rochwerg"[Author]' | efetch -format medline > pubmed_data/Bram_Rochwerg_publications.txt

if [ -s pubmed_data/Bram_Rochwerg_publications.txt ]; then
    echo "✅ Search completed: pubmed_data/Bram_Rochwerg_publications.txt"
    echo "📊 Publications found: $(grep -c "^PMID-" pubmed_data/Bram_Rochwerg_publications.txt)"
else
    echo "❌ No results or search failed: pubmed_data/Bram_Rochwerg_publications.txt"
fi
