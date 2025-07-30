#!/bin/bash
# EDirect search script for Jan Brozek
# Generated on 2025-07-30 08:57:15

echo "🔍 Searching PubMed for Jan Brozek..."

# Create output directory
mkdir -p pubmed_data

# Search and fetch publications
esearch -db pubmed -query '"Jan Brozek"[Author]' | efetch -format medline > pubmed_data/Jan_Brozek_publications.txt

if [ -s pubmed_data/Jan_Brozek_publications.txt ]; then
    echo "✅ Search completed: pubmed_data/Jan_Brozek_publications.txt"
    echo "📊 Publications found: $(grep -c "^PMID-" pubmed_data/Jan_Brozek_publications.txt)"
else
    echo "❌ No results or search failed: pubmed_data/Jan_Brozek_publications.txt"
fi
