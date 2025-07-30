#!/bin/bash
# EDirect search script for Salim Yusuf
# Generated on 2025-07-30 08:57:15

echo "🔍 Searching PubMed for Salim Yusuf..."

# Create output directory
mkdir -p pubmed_data

# Search and fetch publications
esearch -db pubmed -query '"Salim Yusuf"[Author]' | efetch -format medline > pubmed_data/Salim_Yusuf_publications.txt

if [ -s pubmed_data/Salim_Yusuf_publications.txt ]; then
    echo "✅ Search completed: pubmed_data/Salim_Yusuf_publications.txt"
    echo "📊 Publications found: $(grep -c "^PMID-" pubmed_data/Salim_Yusuf_publications.txt)"
else
    echo "❌ No results or search failed: pubmed_data/Salim_Yusuf_publications.txt"
fi
