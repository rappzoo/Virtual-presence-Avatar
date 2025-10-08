#!/bin/bash
# Avatar Tank Disk Usage Checker
# Shows disk usage and helps identify large files

echo "💾 Avatar Tank Disk Usage Report"
echo "================================"

# Get current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Show overall disk usage
echo "📊 Overall Disk Usage:"
df -h . | tail -1 | awk '{print "   Used: " $3 " / " $2 " (" $5 ")"}'

# Show directory sizes
echo ""
echo "📁 Directory Sizes:"
du -sh * 2>/dev/null | sort -hr | head -10 | while read size name; do
    echo "   $size  $name"
done

# Show log file sizes
echo ""
echo "📋 Log File Sizes:"
if ls *.log 1> /dev/null 2>&1; then
    ls -lah *.log | awk '{print "   " $5 "  " $9}' | sort -hr
else
    echo "   No log files found"
fi

# Show largest files
echo ""
echo "📄 Largest Files:"
find . -type f -exec ls -lah {} + 2>/dev/null | sort -k5 -hr | head -5 | awk '{print "   " $5 "  " $9}'

# Show Python cache size
echo ""
echo "🐍 Python Cache:"
if [[ -d "modules/__pycache__" ]]; then
    CACHE_SIZE=$(du -sh modules/__pycache__ 2>/dev/null | cut -f1)
    echo "   modules/__pycache__: $CACHE_SIZE"
else
    echo "   No Python cache found"
fi

# Show snapshots directory
echo ""
echo "📸 Snapshots:"
if [[ -d "snapshots" ]]; then
    SNAPSHOT_COUNT=$(find snapshots -name "*.jpg" -type f 2>/dev/null | wc -l)
    SNAPSHOT_SIZE=$(du -sh snapshots 2>/dev/null | cut -f1)
    echo "   Count: $SNAPSHOT_COUNT files"
    echo "   Size: $SNAPSHOT_SIZE"
else
    echo "   No snapshots directory found"
fi

# Show config directory
echo ""
echo "⚙️  Configuration:"
if [[ -d "config" ]]; then
    CONFIG_SIZE=$(du -sh config 2>/dev/null | cut -f1)
    echo "   config/: $CONFIG_SIZE"
    ls -lah config/ 2>/dev/null | tail -n +2 | while read line; do
        echo "     $line"
    done
else
    echo "   No config directory found"
fi

echo ""
echo "✅ Disk usage report completed!"
echo ""
echo "💡 Tips:"
echo "   - Run ./cleanup_logs.sh to clean old log files"
echo "   - Delete old snapshots if disk space is low"
echo "   - Python cache files can be safely deleted (they'll regenerate)"

