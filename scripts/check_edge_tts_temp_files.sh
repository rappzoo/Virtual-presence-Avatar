#!/bin/bash
# Script to check for and clean up Edge-TTS temp files

echo "=== Edge-TTS Temp File Checker ==="
echo ""

# Check for Edge-TTS temp files
echo "Checking /tmp/edge_tts_ro/ ..."
if [ -d "/tmp/edge_tts_ro/" ]; then
    echo "Directory exists!"
    ls -lh /tmp/edge_tts_ro/ | wc -l
    du -sh /tmp/edge_tts_ro/
else
    echo "Directory does not exist (good)"
fi

echo ""
echo "Checking for edge_tts_sound_* files in /tmp ..."
find /tmp -name "edge_tts_sound_*" -ls 2>/dev/null | head -20

echo ""
echo "Checking for edge_tts*.mp3 files in /tmp ..."
find /tmp -name "edge_tts*.mp3" -ls 2>/dev/null | head -20

echo ""
echo "=== Cleanup ==="
# Clean up old temp files (older than 1 hour)
find /tmp -name "edge_tts_sound_*" -mmin +60 -delete 2>/dev/null
find /tmp -name "edge_tts*.mp3" -mmin +60 -delete 2>/dev/null

echo "Cleanup complete!"
