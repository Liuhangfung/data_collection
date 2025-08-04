#!/bin/bash

# AI Trend Navigator - Daily Update Cron Script
# This script runs the daily update and handles logging

# Set paths (CHANGE THESE TO YOUR ACTUAL PATHS)
SCRIPT_DIR="/home/your-user/ai_trend"
PYTHON_PATH="/usr/bin/python3"
LOG_FILE="/var/log/ai_trend_update.log"

# Create log directory if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"

# Change to script directory
cd "$SCRIPT_DIR" || {
    echo "$(date): ERROR - Cannot change to directory: $SCRIPT_DIR" >> "$LOG_FILE"
    exit 1
}

# Log start time
echo "$(date): 🚀 Starting AI Trend Navigator daily update..." >> "$LOG_FILE"

# Export environment variables from .env file
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "$(date): ✅ Loaded environment variables" >> "$LOG_FILE"
else
    echo "$(date): ❌ ERROR - .env file not found" >> "$LOG_FILE"
    exit 1
fi

# Run the Python script
$PYTHON_PATH daily_supabase_update.py >> "$LOG_FILE" 2>&1
exit_code=$?

# Log completion
if [ $exit_code -eq 0 ]; then
    echo "$(date): ✅ Daily update completed successfully" >> "$LOG_FILE"
else
    echo "$(date): ❌ Daily update failed with exit code: $exit_code" >> "$LOG_FILE"
fi

echo "$(date): ================================================" >> "$LOG_FILE"
exit $exit_code 