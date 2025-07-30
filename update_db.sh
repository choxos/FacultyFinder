#!/bin/bash

# FacultyFinder Database Update Helper Script
echo "🚀 FacultyFinder Database Update Helper"
echo "======================================="

# Check if we're on the VPS or local machine
if [ -f "/var/www/ff/.env" ]; then
    echo "🖥️  Detected VPS environment"
    ENV_LOCATION="/var/www/ff/.env"
else
    echo "💻 Detected local environment"
    ENV_LOCATION=".env"
fi

# Function to show usage
show_usage() {
    echo ""
    echo "📖 Usage Options:"
    echo "  ./update_db.sh                    # Quick incremental update + restart service"
    echo "  ./update_db.sh check              # Check database status"
    echo "  ./update_db.sh incremental        # Incremental update only"
    echo "  ./update_db.sh full               # Full database rebuild"
    echo "  ./update_db.sh quick              # Quick update without restart"
    echo ""
    echo "💡 Most common usage: ./update_db.sh"
    echo ""
}

# Parse command line argument
MODE=${1:-"default"}

case $MODE in
    "check"|"status")
        echo "📊 Checking database status..."
        python3 update_database_from_csv.py --mode status
        ;;
    "incremental")
        echo "🔄 Performing incremental update..."
        python3 update_database_from_csv.py --mode incremental
        ;;
    "full"|"rebuild")
        echo "🗑️ Performing full database rebuild..."
        python3 update_database_from_csv.py --mode full --restart
        ;;
    "quick")
        echo "⚡ Quick incremental update (no restart)..."
        python3 update_database_from_csv.py --mode incremental
        ;;
    "default"|"")
        echo "🎯 Default: Incremental update + restart service"
        python3 update_database_from_csv.py --mode incremental --restart
        ;;
    "help"|"-h"|"--help")
        show_usage
        exit 0
        ;;
    *)
        echo "❌ Unknown option: $MODE"
        show_usage
        exit 1
        ;;
esac

echo ""
echo "🎉 Database update process completed!"
