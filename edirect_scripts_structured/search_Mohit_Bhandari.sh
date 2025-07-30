#!/bin/bash
# EDirect search script for Mohit Bhandari
# University: CA-ON-002_mcmaster.ca
# Generated on 2025-07-30 09:05:46

echo "🔍 Searching PubMed for Mohit Bhandari..."
echo "🏫 University: CA-ON-002_mcmaster.ca"

# Create university directory structure
mkdir -p data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca

# Search and fetch publications
esearch -db pubmed -query '"Mohit Bhandari"[Author]' | efetch -format medline > data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Mohit_Bhandari_publications.txt

if [ -s data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Mohit_Bhandari_publications.txt ]; then
    echo "✅ Search completed: data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Mohit_Bhandari_publications.txt"
    echo "📊 Publications found: $(grep -c "^PMID-" data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Mohit_Bhandari_publications.txt)"
else
    echo "❌ No results or search failed: data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Mohit_Bhandari_publications.txt"
fi
