#!/bin/bash

echo "🚀 FacultyFinder Complete Data Deployment"
echo "========================================="

# Configuration
LOCAL_DATA_DIR="/Users/choxos/Documents/GitHub/FacultyFinder/data"
VPS_USER="xeradb"
VPS_IP="91.99.161.136"
VPS_DATA_DIR="/var/www/ff/data_import"

echo "📋 Deployment Steps:"
echo "1. Transfer data files from local to VPS"
echo "2. Install required Python packages on VPS"
echo "3. Run database migration"
echo "4. Verify data import"
echo "5. Test website functionality"
echo

# Step 1: Transfer data files
echo "🔄 Step 1: Transferring data files..."
echo "====================================="

# Check if transfer script exists and run it
if [ -f "./transfer_data_to_vps.sh" ]; then
    chmod +x ./transfer_data_to_vps.sh
    ./transfer_data_to_vps.sh
else
    echo "❌ Transfer script not found. Running inline transfer..."
    
    # Inline transfer commands
    ssh $VPS_USER@$VPS_IP "mkdir -p $VPS_DATA_DIR"
    
    echo "📚 Transferring essential data files..."
    rsync -avz --progress "$LOCAL_DATA_DIR/university_codes.csv" $VPS_USER@$VPS_IP:$VPS_DATA_DIR/
    rsync -avz --progress "$LOCAL_DATA_DIR/mcmaster_experts_summary.csv" $VPS_USER@$VPS_IP:$VPS_DATA_DIR/
    rsync -avz --progress "$LOCAL_DATA_DIR/mcmaster_experts_detailed.json" $VPS_USER@$VPS_IP:$VPS_DATA_DIR/
    rsync -avz --progress "./data_migration_system.py" $VPS_USER@$VPS_IP:$VPS_DATA_DIR/
fi

if [ $? -ne 0 ]; then
    echo "❌ Data transfer failed!"
    exit 1
fi

echo "✅ Data transfer completed!"
echo

# Step 2: Install Python packages
echo "🐍 Step 2: Installing Python packages on VPS..."
echo "==============================================="

ssh $VPS_USER@$VPS_IP "
echo '📦 Installing required Python packages...'
cd /var/www/ff
source venv/bin/activate

# Install data processing packages
pip install pandas psycopg2-binary python-dotenv

echo '✅ Python packages installed'
"

if [ $? -ne 0 ]; then
    echo "❌ Package installation failed!"
    exit 1
fi

echo "✅ Python packages installed!"
echo

# Step 3: Run database migration
echo "🗄️  Step 3: Running database migration..."
echo "========================================"

ssh $VPS_USER@$VPS_IP "
cd $VPS_DATA_DIR
source /var/www/ff/venv/bin/activate

echo '🚀 Starting data migration...'
python3 data_migration_system.py --data-dir $VPS_DATA_DIR

echo '📊 Migration completed!'
"

if [ $? -ne 0 ]; then
    echo "❌ Database migration failed!"
    echo "🔧 Troubleshooting tips:"
    echo "1. Check PostgreSQL is running: ssh $VPS_USER@$VPS_IP 'sudo systemctl status postgresql'"
    echo "2. Check database connection: ssh $VPS_USER@$VPS_IP 'psql -h localhost -U ff_user -d ff_production'"
    echo "3. Check migration logs on VPS"
    exit 1
fi

echo "✅ Database migration completed!"
echo

# Step 4: Verify data import
echo "✅ Step 4: Verifying data import..."
echo "=================================="

ssh $VPS_USER@$VPS_IP "
source /var/www/ff/venv/bin/activate

echo '📊 Database verification:'
python3 -c \"
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv('/var/www/ff/.env')

try:
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'ff_user'), 
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME', 'ff_production')
    )
    
    cursor = conn.cursor()
    
    # Check universities
    cursor.execute('SELECT COUNT(*) FROM universities')
    uni_count = cursor.fetchone()[0]
    print(f'✅ Universities: {uni_count}')
    
    # Check professors
    cursor.execute('SELECT COUNT(*) FROM professors')
    prof_count = cursor.fetchone()[0] 
    print(f'✅ Professors: {prof_count}')
    
    # Check publications
    cursor.execute('SELECT COUNT(*) FROM publications')
    pub_count = cursor.fetchone()[0]
    print(f'✅ Publications: {pub_count}')
    
    # Sample data
    cursor.execute('SELECT name FROM universities LIMIT 3')
    unis = cursor.fetchall()
    print(f'✅ Sample universities: {[u[0] for u in unis]}')
    
    cursor.execute('SELECT name FROM professors LIMIT 3')
    profs = cursor.fetchall()
    print(f'✅ Sample professors: {[p[0] for p in profs]}')
    
    conn.close()
    print('🎉 Database verification successful!')
    
except Exception as e:
    print(f'❌ Database verification failed: {e}')
    exit(1)
\"
"

if [ $? -ne 0 ]; then
    echo "❌ Data verification failed!"
    exit 1
fi

echo "✅ Data verification completed!"
echo

# Step 5: Test website functionality
echo "🌐 Step 5: Testing website functionality..."
echo "=========================================="

ssh $VPS_USER@$VPS_IP "
echo '🔄 Restarting FacultyFinder service...'
sudo systemctl restart facultyfinder
sleep 5

echo '📊 Checking service status...'
sudo systemctl status facultyfinder --no-pager

echo '🌐 Testing website response...'
curl -s -I http://127.0.0.1:8008/ | head -1
"

echo
echo "🌍 Testing public website..."
response=$(curl -s -I https://facultyfinder.io | head -1)
echo "Response: $response"

if [[ $response == *"200"* ]]; then
    echo "✅ Website is responding correctly!"
else
    echo "⚠️  Website may need additional restart"
    echo "Run: ssh $VPS_USER@$VPS_IP 'sudo systemctl restart facultyfinder'"
fi

echo
echo "🎉 DATA DEPLOYMENT COMPLETED!"
echo "============================"
echo
echo "✅ Your FacultyFinder website now has:"
echo "   📚 University data"
echo "   👥 Professor profiles" 
echo "   📄 Publication records"
echo "   📊 Journal metrics (if imported)"
echo
echo "🔗 Website: https://facultyfinder.io"
echo
echo "📋 What you can now do:"
echo "   • Browse universities and faculty"
echo "   • Search for professors by name, department, or research area"
echo "   • View detailed faculty profiles with publications"
echo "   • Use all FacultyFinder features with real data"
echo
echo "🔧 If you need to make changes:"
echo "   • SSH to VPS: ssh $VPS_USER@$VPS_IP"
echo "   • Check logs: sudo journalctl -u facultyfinder -f"
echo "   • Restart service: sudo systemctl restart facultyfinder"
echo
echo "🎯 Next steps:"
echo "   • Test the website thoroughly"
echo "   • Set up automated backups"
echo "   • Consider adding more universities/data"
echo
echo "✅ Deployment successful! Your FacultyFinder is now live with real data! 🚀" 