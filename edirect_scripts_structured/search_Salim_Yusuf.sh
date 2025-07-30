#!/bin/bash
# EDirect search script for Salim Yusuf
# University: CA-ON-002_mcmaster.ca
# Generated on 2025-07-30 09:05:46

echo "🔍 Searching PubMed for Salim Yusuf..."
echo "🏫 University: CA-ON-002_mcmaster.ca"

# Create university directory structure
mkdir -p data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca

# Search and fetch publications
esearch -db pubmed -query '"Salim Yusuf"[Author]' | efetch -format medline > data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Salim_Yusuf_publications.txt

if [ -s data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Salim_Yusuf_publications.txt ]; then
    echo "✅ Search completed: data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Salim_Yusuf_publications.txt"
    echo "📊 Publications found: $(grep -c "^PMID-" data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Salim_Yusuf_publications.txt)"
else
    echo "❌ No results or search failed: data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Salim_Yusuf_publications.txt"
fi
