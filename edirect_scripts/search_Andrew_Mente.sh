#!/bin/bash
# EDirect search script for Andrew Mente
# Generated on 2025-07-30 08:57:15

echo "🔍 Searching PubMed for Andrew Mente..."

# Create output directory
mkdir -p pubmed_data

# Search and fetch publications
esearch -db pubmed -query '"Andrew Mente"[Author]' | efetch -format medline > pubmed_data/Andrew_Mente_publications.txt

if [ -s pubmed_data/Andrew_Mente_publications.txt ]; then
    echo "✅ Search completed: pubmed_data/Andrew_Mente_publications.txt"
    echo "📊 Publications found: $(grep -c "^PMID-" pubmed_data/Andrew_Mente_publications.txt)"
else
    echo "❌ No results or search failed: pubmed_data/Andrew_Mente_publications.txt"
fi
