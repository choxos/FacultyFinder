#!/bin/bash
# EDirect search script for Hertzel Gerstein
# University: CA-ON-002_mcmaster.ca
# Generated on 2025-07-30 09:05:46

echo "🔍 Searching PubMed for Hertzel Gerstein..."
echo "🏫 University: CA-ON-002_mcmaster.ca"

# Create university directory structure
mkdir -p data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca

# Search and fetch publications
esearch -db pubmed -query '"Hertzel Gerstein"[Author]' | efetch -format medline > data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Hertzel_Gerstein_publications.txt

if [ -s data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Hertzel_Gerstein_publications.txt ]; then
    echo "✅ Search completed: data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Hertzel_Gerstein_publications.txt"
    echo "📊 Publications found: $(grep -c "^PMID-" data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Hertzel_Gerstein_publications.txt)"
else
    echo "❌ No results or search failed: data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Hertzel_Gerstein_publications.txt"
fi
