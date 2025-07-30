#!/bin/bash
# EDirect search script for Holger Schünemann
# Generated on 2025-07-30 08:57:15

echo "🔍 Searching PubMed for Holger Schünemann..."

# Create output directory
mkdir -p pubmed_data

# Search and fetch publications
esearch -db pubmed -query '"Holger Schünemann"[Author]' | efetch -format medline > pubmed_data/Holger_Schunemann_publications.txt

if [ -s pubmed_data/Holger_Schunemann_publications.txt ]; then
    echo "✅ Search completed: pubmed_data/Holger_Schunemann_publications.txt"
    echo "📊 Publications found: $(grep -c "^PMID-" pubmed_data/Holger_Schunemann_publications.txt)"
else
    echo "❌ No results or search failed: pubmed_data/Holger_Schunemann_publications.txt"
fi
