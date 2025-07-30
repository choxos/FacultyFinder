#!/bin/bash
# Batch EDirect search script for all faculty
# Generated on 2025-07-30 08:57:15

echo "🚀 Starting batch PubMed search for 10 faculty members..."
echo "================================================"

# Create output directory
mkdir -p pubmed_data

# Track statistics
total_faculty=10
completed=0
failed=0


# [1/10] Gordon Guyatt
echo "🔍 [1/10] Searching for Gordon Guyatt..."

esearch -db pubmed -query '"Gordon Guyatt"[Author]' | efetch -format medline > pubmed_data/Gordon_Guyatt_publications.txt

if [ -s pubmed_data/Gordon_Guyatt_publications.txt ]; then
    pub_count=$(grep -c "^PMID-" pubmed_data/Gordon_Guyatt_publications.txt)
    echo "   ✅ Found $pub_count publications"
    ((completed++))
else
    echo "   ❌ No results found"
    ((failed++))
fi

# Small delay between searches
sleep 2

# [2/10] Salim Yusuf
echo "🔍 [2/10] Searching for Salim Yusuf..."

esearch -db pubmed -query '"Salim Yusuf"[Author]' | efetch -format medline > pubmed_data/Salim_Yusuf_publications.txt

if [ -s pubmed_data/Salim_Yusuf_publications.txt ]; then
    pub_count=$(grep -c "^PMID-" pubmed_data/Salim_Yusuf_publications.txt)
    echo "   ✅ Found $pub_count publications"
    ((completed++))
else
    echo "   ❌ No results found"
    ((failed++))
fi

# Small delay between searches
sleep 2

# [3/10] Hertzel Gerstein
echo "🔍 [3/10] Searching for Hertzel Gerstein..."

esearch -db pubmed -query '"Hertzel Gerstein"[Author]' | efetch -format medline > pubmed_data/Hertzel_Gerstein_publications.txt

if [ -s pubmed_data/Hertzel_Gerstein_publications.txt ]; then
    pub_count=$(grep -c "^PMID-" pubmed_data/Hertzel_Gerstein_publications.txt)
    echo "   ✅ Found $pub_count publications"
    ((completed++))
else
    echo "   ❌ No results found"
    ((failed++))
fi

# Small delay between searches
sleep 2

# [4/10] Mohit Bhandari
echo "🔍 [4/10] Searching for Mohit Bhandari..."

esearch -db pubmed -query '"Mohit Bhandari"[Author]' | efetch -format medline > pubmed_data/Mohit_Bhandari_publications.txt

if [ -s pubmed_data/Mohit_Bhandari_publications.txt ]; then
    pub_count=$(grep -c "^PMID-" pubmed_data/Mohit_Bhandari_publications.txt)
    echo "   ✅ Found $pub_count publications"
    ((completed++))
else
    echo "   ❌ No results found"
    ((failed++))
fi

# Small delay between searches
sleep 2

# [5/10] Mark Crowther
echo "🔍 [5/10] Searching for Mark Crowther..."

esearch -db pubmed -query '"Mark Crowther"[Author]' | efetch -format medline > pubmed_data/Mark_Crowther_publications.txt

if [ -s pubmed_data/Mark_Crowther_publications.txt ]; then
    pub_count=$(grep -c "^PMID-" pubmed_data/Mark_Crowther_publications.txt)
    echo "   ✅ Found $pub_count publications"
    ((completed++))
else
    echo "   ❌ No results found"
    ((failed++))
fi

# Small delay between searches
sleep 2

# [6/10] Deborah Cook
echo "🔍 [6/10] Searching for Deborah Cook..."

esearch -db pubmed -query '"Deborah Cook"[Author]' | efetch -format medline > pubmed_data/Deborah_Cook_publications.txt

if [ -s pubmed_data/Deborah_Cook_publications.txt ]; then
    pub_count=$(grep -c "^PMID-" pubmed_data/Deborah_Cook_publications.txt)
    echo "   ✅ Found $pub_count publications"
    ((completed++))
else
    echo "   ❌ No results found"
    ((failed++))
fi

# Small delay between searches
sleep 2

# [7/10] Andrew Mente
echo "🔍 [7/10] Searching for Andrew Mente..."

esearch -db pubmed -query '"Andrew Mente"[Author]' | efetch -format medline > pubmed_data/Andrew_Mente_publications.txt

if [ -s pubmed_data/Andrew_Mente_publications.txt ]; then
    pub_count=$(grep -c "^PMID-" pubmed_data/Andrew_Mente_publications.txt)
    echo "   ✅ Found $pub_count publications"
    ((completed++))
else
    echo "   ❌ No results found"
    ((failed++))
fi

# Small delay between searches
sleep 2

# [8/10] Bram Rochwerg
echo "🔍 [8/10] Searching for Bram Rochwerg..."

esearch -db pubmed -query '"Bram Rochwerg"[Author]' | efetch -format medline > pubmed_data/Bram_Rochwerg_publications.txt

if [ -s pubmed_data/Bram_Rochwerg_publications.txt ]; then
    pub_count=$(grep -c "^PMID-" pubmed_data/Bram_Rochwerg_publications.txt)
    echo "   ✅ Found $pub_count publications"
    ((completed++))
else
    echo "   ❌ No results found"
    ((failed++))
fi

# Small delay between searches
sleep 2

# [9/10] Holger Schünemann
echo "🔍 [9/10] Searching for Holger Schünemann..."

esearch -db pubmed -query '"Holger Schünemann"[Author]' | efetch -format medline > pubmed_data/Holger_Schunemann_publications.txt

if [ -s pubmed_data/Holger_Schunemann_publications.txt ]; then
    pub_count=$(grep -c "^PMID-" pubmed_data/Holger_Schunemann_publications.txt)
    echo "   ✅ Found $pub_count publications"
    ((completed++))
else
    echo "   ❌ No results found"
    ((failed++))
fi

# Small delay between searches
sleep 2

# [10/10] Jan Brozek
echo "🔍 [10/10] Searching for Jan Brozek..."

esearch -db pubmed -query '"Jan Brozek"[Author]' | efetch -format medline > pubmed_data/Jan_Brozek_publications.txt

if [ -s pubmed_data/Jan_Brozek_publications.txt ]; then
    pub_count=$(grep -c "^PMID-" pubmed_data/Jan_Brozek_publications.txt)
    echo "   ✅ Found $pub_count publications"
    ((completed++))
else
    echo "   ❌ No results found"
    ((failed++))
fi

# Small delay between searches
sleep 2

echo ""
echo "🎉 Batch search completed!"
echo "================================================"
echo "✅ Successful searches: $completed"
echo "❌ Failed searches: $failed"
echo "📁 Output directory: pubmed_data/"

# Count total publications
total_pubs=$(find pubmed_data/ -name "*.txt" -exec grep -c "^PMID-" {} + 2>/dev/null | awk '{sum+=$1} END {print sum}')
echo "📚 Total publications found: $total_pubs"

echo ""
echo "📋 Next steps:"
echo "1. Parse data: python3 parse_medline_files.py pubmed_data/"
echo "2. Import to VPS: python3 import_pubmed_data.py parsed_publications.json"
