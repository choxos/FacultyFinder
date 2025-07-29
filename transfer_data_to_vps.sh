#!/bin/bash

echo "🚀 FacultyFinder Data Transfer to VPS"
echo "====================================="

# Configuration
LOCAL_DATA_DIR="/Users/choxos/Documents/GitHub/FacultyFinder/data"
VPS_USER="xeradb"
VPS_IP="91.99.161.136"
VPS_DATA_DIR="/var/www/ff/data_import"

# Check if local data directory exists
if [ ! -d "$LOCAL_DATA_DIR" ]; then
    echo "❌ Local data directory not found: $LOCAL_DATA_DIR"
    echo "   Please ensure you're running this from the correct location"
    exit 1
fi

echo "📁 Local data directory: $LOCAL_DATA_DIR"
echo "🌐 VPS: $VPS_USER@$VPS_IP"
echo "📂 VPS destination: $VPS_DATA_DIR"
echo

# Create VPS data directory
echo "📁 Creating VPS data directory..."
ssh $VPS_USER@$VPS_IP "mkdir -p $VPS_DATA_DIR"

if [ $? -ne 0 ]; then
    echo "❌ Failed to create VPS directory. Check SSH connection."
    exit 1
fi

echo "✅ VPS directory created"
echo

# List what will be transferred
echo "📋 Files to be transferred:"
ls -lh "$LOCAL_DATA_DIR"/*.csv "$LOCAL_DATA_DIR"/*.json 2>/dev/null | while read line; do
    echo "   $line"
done
echo

# Transfer essential data files
echo "🔄 Transferring data files..."

# Transfer university data
echo "📚 Transferring university data..."
rsync -avz --progress "$LOCAL_DATA_DIR/university_codes.csv" $VPS_USER@$VPS_IP:$VPS_DATA_DIR/

# Transfer McMaster faculty data
echo "👥 Transferring McMaster faculty data..."
rsync -avz --progress "$LOCAL_DATA_DIR/mcmaster_experts_summary.csv" $VPS_USER@$VPS_IP:$VPS_DATA_DIR/
rsync -avz --progress "$LOCAL_DATA_DIR/mcmaster_experts_detailed.json" $VPS_USER@$VPS_IP:$VPS_DATA_DIR/
rsync -avz --progress "$LOCAL_DATA_DIR/mcmaster_hei_faculty.csv" $VPS_USER@$VPS_IP:$VPS_DATA_DIR/

# Transfer Scimago journal data (large files)
echo "📊 Transferring Scimago journal data (this may take a while)..."
rsync -avz --progress "$LOCAL_DATA_DIR/scimago_journals_comprehensive.csv" $VPS_USER@$VPS_IP:$VPS_DATA_DIR/ || echo "⚠️  Scimago comprehensive file transfer failed"
rsync -avz --progress "$LOCAL_DATA_DIR/scimago_journals_semicolon_format.csv" $VPS_USER@$VPS_IP:$VPS_DATA_DIR/ || echo "⚠️  Scimago semicolon file transfer failed"

# Transfer individual data directories
echo "📂 Transferring individual faculty data directories..."
rsync -avz --progress "$LOCAL_DATA_DIR/mcmaster_experts_individual_csv/" $VPS_USER@$VPS_IP:$VPS_DATA_DIR/mcmaster_experts_individual_csv/ || echo "⚠️  Individual CSV transfer failed"
rsync -avz --progress "$LOCAL_DATA_DIR/mcmaster_experts_individual_json/" $VPS_USER@$VPS_IP:$VPS_DATA_DIR/mcmaster_experts_individual_json/ || echo "⚠️  Individual JSON transfer failed"

# Transfer scimagojr directory
echo "📈 Transferring Scimago yearly data..."
rsync -avz --progress "$LOCAL_DATA_DIR/scimagojr/" $VPS_USER@$VPS_IP:$VPS_DATA_DIR/scimagojr/ || echo "⚠️  Scimago yearly data transfer failed"

# Transfer migration script
echo "🔧 Transferring migration scripts..."
rsync -avz --progress "./data_migration_system.py" $VPS_USER@$VPS_IP:$VPS_DATA_DIR/

# Verify transfer
echo
echo "✅ Transfer completed! Verifying files on VPS..."
ssh $VPS_USER@$VPS_IP "
echo '📋 Files on VPS:'
ls -lh $VPS_DATA_DIR/*.csv $VPS_DATA_DIR/*.json $VPS_DATA_DIR/*.py 2>/dev/null

echo
echo '📊 Directory sizes:'
du -sh $VPS_DATA_DIR/*/ 2>/dev/null

echo
echo '💾 Total space used:'
du -sh $VPS_DATA_DIR
"

echo
echo "🎯 Next steps:"
echo "1. SSH into your VPS: ssh $VPS_USER@$VPS_IP"
echo "2. Navigate to data directory: cd $VPS_DATA_DIR"
echo "3. Run the migration: python3 data_migration_system.py --data-dir $VPS_DATA_DIR"
echo
echo "✅ Data transfer completed successfully!" 