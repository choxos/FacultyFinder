#!/bin/bash
# Structured EDirect search script for all faculty
# Uses proper university folder structure
# Generated on 2025-07-30 09:05:46

echo "🚀 Starting structured PubMed search for 10 faculty members..."
echo "📁 Using folder structure: data/publications/pubmed/[country]/[province]/[university]/"
echo "================================================"

# Track statistics
total_faculty=10
completed=0
failed=0


# [1/10] Gordon Guyatt - CA-ON-002_mcmaster.ca
echo "🔍 [1/10] Searching for Gordon Guyatt..."
echo "   🏫 University: CA-ON-002_mcmaster.ca"

# Create university directory
mkdir -p data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca

# Search and fetch
esearch -db pubmed -query '"Gordon Guyatt"[Author]' | efetch -format medline > data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Gordon_Guyatt_publications.txt

if [ -s data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Gordon_Guyatt_publications.txt ]; then
    pub_count=$(grep -c "^PMID-" data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Gordon_Guyatt_publications.txt)
    echo "   ✅ Found $pub_count publications"
    echo "   📁 Saved to: data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Gordon_Guyatt_publications.txt"
    ((completed++))
else
    echo "   ❌ No results found"
    ((failed++))
fi

# Small delay between searches
sleep 2

# [2/10] Salim Yusuf - CA-ON-002_mcmaster.ca
echo "🔍 [2/10] Searching for Salim Yusuf..."
echo "   🏫 University: CA-ON-002_mcmaster.ca"

# Create university directory
mkdir -p data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca

# Search and fetch
esearch -db pubmed -query '"Salim Yusuf"[Author]' | efetch -format medline > data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Salim_Yusuf_publications.txt

if [ -s data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Salim_Yusuf_publications.txt ]; then
    pub_count=$(grep -c "^PMID-" data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Salim_Yusuf_publications.txt)
    echo "   ✅ Found $pub_count publications"
    echo "   📁 Saved to: data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Salim_Yusuf_publications.txt"
    ((completed++))
else
    echo "   ❌ No results found"
    ((failed++))
fi

# Small delay between searches
sleep 2

# [3/10] Hertzel Gerstein - CA-ON-002_mcmaster.ca
echo "🔍 [3/10] Searching for Hertzel Gerstein..."
echo "   🏫 University: CA-ON-002_mcmaster.ca"

# Create university directory
mkdir -p data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca

# Search and fetch
esearch -db pubmed -query '"Hertzel Gerstein"[Author]' | efetch -format medline > data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Hertzel_Gerstein_publications.txt

if [ -s data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Hertzel_Gerstein_publications.txt ]; then
    pub_count=$(grep -c "^PMID-" data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Hertzel_Gerstein_publications.txt)
    echo "   ✅ Found $pub_count publications"
    echo "   📁 Saved to: data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Hertzel_Gerstein_publications.txt"
    ((completed++))
else
    echo "   ❌ No results found"
    ((failed++))
fi

# Small delay between searches
sleep 2

# [4/10] Mohit Bhandari - CA-ON-002_mcmaster.ca
echo "🔍 [4/10] Searching for Mohit Bhandari..."
echo "   🏫 University: CA-ON-002_mcmaster.ca"

# Create university directory
mkdir -p data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca

# Search and fetch
esearch -db pubmed -query '"Mohit Bhandari"[Author]' | efetch -format medline > data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Mohit_Bhandari_publications.txt

if [ -s data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Mohit_Bhandari_publications.txt ]; then
    pub_count=$(grep -c "^PMID-" data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Mohit_Bhandari_publications.txt)
    echo "   ✅ Found $pub_count publications"
    echo "   📁 Saved to: data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Mohit_Bhandari_publications.txt"
    ((completed++))
else
    echo "   ❌ No results found"
    ((failed++))
fi

# Small delay between searches
sleep 2

# [5/10] Mark Crowther - CA-ON-002_mcmaster.ca
echo "🔍 [5/10] Searching for Mark Crowther..."
echo "   🏫 University: CA-ON-002_mcmaster.ca"

# Create university directory
mkdir -p data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca

# Search and fetch
esearch -db pubmed -query '"Mark Crowther"[Author]' | efetch -format medline > data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Mark_Crowther_publications.txt

if [ -s data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Mark_Crowther_publications.txt ]; then
    pub_count=$(grep -c "^PMID-" data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Mark_Crowther_publications.txt)
    echo "   ✅ Found $pub_count publications"
    echo "   📁 Saved to: data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Mark_Crowther_publications.txt"
    ((completed++))
else
    echo "   ❌ No results found"
    ((failed++))
fi

# Small delay between searches
sleep 2

# [6/10] Deborah Cook - CA-ON-002_mcmaster.ca
echo "🔍 [6/10] Searching for Deborah Cook..."
echo "   🏫 University: CA-ON-002_mcmaster.ca"

# Create university directory
mkdir -p data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca

# Search and fetch
esearch -db pubmed -query '"Deborah Cook"[Author]' | efetch -format medline > data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Deborah_Cook_publications.txt

if [ -s data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Deborah_Cook_publications.txt ]; then
    pub_count=$(grep -c "^PMID-" data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Deborah_Cook_publications.txt)
    echo "   ✅ Found $pub_count publications"
    echo "   📁 Saved to: data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Deborah_Cook_publications.txt"
    ((completed++))
else
    echo "   ❌ No results found"
    ((failed++))
fi

# Small delay between searches
sleep 2

# [7/10] Andrew Mente - CA-ON-002_mcmaster.ca
echo "🔍 [7/10] Searching for Andrew Mente..."
echo "   🏫 University: CA-ON-002_mcmaster.ca"

# Create university directory
mkdir -p data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca

# Search and fetch
esearch -db pubmed -query '"Andrew Mente"[Author]' | efetch -format medline > data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Andrew_Mente_publications.txt

if [ -s data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Andrew_Mente_publications.txt ]; then
    pub_count=$(grep -c "^PMID-" data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Andrew_Mente_publications.txt)
    echo "   ✅ Found $pub_count publications"
    echo "   📁 Saved to: data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Andrew_Mente_publications.txt"
    ((completed++))
else
    echo "   ❌ No results found"
    ((failed++))
fi

# Small delay between searches
sleep 2

# [8/10] Bram Rochwerg - CA-ON-002_mcmaster.ca
echo "🔍 [8/10] Searching for Bram Rochwerg..."
echo "   🏫 University: CA-ON-002_mcmaster.ca"

# Create university directory
mkdir -p data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca

# Search and fetch
esearch -db pubmed -query '"Bram Rochwerg"[Author]' | efetch -format medline > data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Bram_Rochwerg_publications.txt

if [ -s data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Bram_Rochwerg_publications.txt ]; then
    pub_count=$(grep -c "^PMID-" data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Bram_Rochwerg_publications.txt)
    echo "   ✅ Found $pub_count publications"
    echo "   📁 Saved to: data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Bram_Rochwerg_publications.txt"
    ((completed++))
else
    echo "   ❌ No results found"
    ((failed++))
fi

# Small delay between searches
sleep 2

# [9/10] Holger Schünemann - CA-ON-002_mcmaster.ca
echo "🔍 [9/10] Searching for Holger Schünemann..."
echo "   🏫 University: CA-ON-002_mcmaster.ca"

# Create university directory
mkdir -p data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca

# Search and fetch
esearch -db pubmed -query '"Holger Schünemann"[Author]' | efetch -format medline > data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Holger_Schunemann_publications.txt

if [ -s data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Holger_Schunemann_publications.txt ]; then
    pub_count=$(grep -c "^PMID-" data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Holger_Schunemann_publications.txt)
    echo "   ✅ Found $pub_count publications"
    echo "   📁 Saved to: data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Holger_Schunemann_publications.txt"
    ((completed++))
else
    echo "   ❌ No results found"
    ((failed++))
fi

# Small delay between searches
sleep 2

# [10/10] Jan Brozek - CA-ON-002_mcmaster.ca
echo "🔍 [10/10] Searching for Jan Brozek..."
echo "   🏫 University: CA-ON-002_mcmaster.ca"

# Create university directory
mkdir -p data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca

# Search and fetch
esearch -db pubmed -query '"Jan Brozek"[Author]' | efetch -format medline > data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Jan_Brozek_publications.txt

if [ -s data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Jan_Brozek_publications.txt ]; then
    pub_count=$(grep -c "^PMID-" data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Jan_Brozek_publications.txt)
    echo "   ✅ Found $pub_count publications"
    echo "   📁 Saved to: data/publications/pubmed/CA/ON/CA-ON-002_mcmaster.ca/Jan_Brozek_publications.txt"
    ((completed++))
else
    echo "   ❌ No results found"
    ((failed++))
fi

# Small delay between searches
sleep 2

echo ""
echo "🎉 Structured batch search completed!"
echo "================================================"
echo "✅ Successful searches: $completed"
echo "❌ Failed searches: $failed"
echo "📁 Base directory: data/publications/pubmed/"

# Count total publications by university
echo ""
echo "📊 Publications by University:"
for uni_dir in data/publications/pubmed/*/*/*/; do
    if [ -d "$uni_dir" ]; then
        uni_name=$(basename "$uni_dir")
        txt_count=$(find "$uni_dir" -name "*.txt" | wc -l)
        if [ "$txt_count" -gt 0 ]; then
            total_pubs=$(find "$uni_dir" -name "*.txt" -exec grep -c "^PMID-" {} + 2>/dev/null | awk '{sum+=$1} END {print sum}')
            echo "   $uni_name: $total_pubs publications ($txt_count files)"
        fi
    fi
done

echo ""
echo "📋 Next steps:"
echo "1. Parse data: python3 parse_medline_structured.py data/publications/pubmed/"
echo "2. Import to VPS: python3 import_pubmed_data.py parsed_publications/"
