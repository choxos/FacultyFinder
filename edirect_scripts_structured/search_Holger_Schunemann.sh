#!/bin/bash
# EDirect search script for Holger Schünemann
# University: CA-ON-002_mcmaster.ca
# Generated on 2025-07-30 09:05:46

echo "🔍 Searching PubMed for Holger Schünemann..."
echo "🏫 University: CA-ON-002_mcmaster.ca"

# Create university directory structure
mkdir -p data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca

# Search and fetch publications
esearch -db pubmed -query '"Holger Schünemann"[Author]' | efetch -format medline > data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Holger_Schunemann_publications.txt

if [ -s data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Holger_Schunemann_publications.txt ]; then
    echo "✅ Search completed: data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Holger_Schunemann_publications.txt"
    echo "📊 Publications found: $(grep -c "^PMID-" data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Holger_Schunemann_publications.txt)"
else
    echo "❌ No results or search failed: data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Holger_Schunemann_publications.txt"
fi
