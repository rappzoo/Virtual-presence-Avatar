#!/bin/bash
# Avatar Tank Log Cleanup Script
# Removes old log files and temporary files to keep the system clean

echo "🧹 Avatar Tank Log Cleanup"
echo "=========================="

# Get current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Count files before cleanup
LOG_COUNT_BEFORE=$(find . -name "*.log" -type f | wc -l)
TEMP_COUNT_BEFORE=$(find /tmp -name "avatar_*" -type f 2>/dev/null | wc -l)

echo "📊 Before cleanup:"
echo "   Log files: $LOG_COUNT_BEFORE"
echo "   Temp files: $TEMP_COUNT_BEFORE"

# Keep only essential log files
echo ""
echo "🗑️  Removing old log files..."

# List of log files to keep (essential ones)
KEEP_LOGS=(
    "flask.log"
    "mediamtx_fixed.log" 
    "stream_monitor.log"
    "stream_monitor_live.log"
)

# Remove all log files except the ones we want to keep
for log_file in *.log; do
    if [[ -f "$log_file" ]]; then
        keep_file=false
        for keep in "${KEEP_LOGS[@]}"; do
            if [[ "$log_file" == "$keep" ]]; then
                keep_file=true
                break
            fi
        done
        
        if [[ "$keep_file" == false ]]; then
            echo "   Removing: $log_file"
            rm -f "$log_file"
        else
            echo "   Keeping: $log_file"
        fi
    fi
done

# Clean up old temporary files
echo ""
echo "🗑️  Removing old temporary files..."
rm -f /tmp/avatar_camera_settings.json
rm -f /tmp/avatar_clean.lock
rm -f /tmp/avatar_*.tmp
rm -f /tmp/avatar_*.pid

# Clean up empty directories
echo ""
echo "🗑️  Removing empty directories..."
find . -type d -empty -delete 2>/dev/null

# Count files after cleanup
LOG_COUNT_AFTER=$(find . -name "*.log" -type f | wc -l)
TEMP_COUNT_AFTER=$(find /tmp -name "avatar_*" -type f 2>/dev/null | wc -l)

echo ""
echo "📊 After cleanup:"
echo "   Log files: $LOG_COUNT_AFTER (removed $((LOG_COUNT_BEFORE - LOG_COUNT_AFTER)))"
echo "   Temp files: $TEMP_COUNT_AFTER (removed $((TEMP_COUNT_BEFORE - TEMP_COUNT_AFTER)))"

# Show remaining log files
echo ""
echo "📋 Remaining log files:"
if [[ $LOG_COUNT_AFTER -gt 0 ]]; then
    ls -lah *.log 2>/dev/null | while read line; do
        echo "   $line"
    done
else
    echo "   No log files remaining"
fi

echo ""
echo "✅ Log cleanup completed!"
echo ""
echo "💡 Tip: Run this script periodically to keep your system clean"
echo "   Usage: ./cleanup_logs.sh"


