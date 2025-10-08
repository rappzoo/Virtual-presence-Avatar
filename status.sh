#!/bin/bash
# Avatar Tank Status Script

echo "=== Avatar Tank System Status ==="
echo

echo "Services:"
ps aux | grep -E "(mediamtx|python.*mediamtx_main)" | grep -v grep
echo

echo "Ports:"
netstat -tlnp | grep -E "(5000|8888|8889|8554)" | head -10
echo

echo "API Status:"
curl -s http://localhost:5000/api/status 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "API not responding"
echo

echo "HLS Stream:"
curl -s http://192.168.68.107:8888/stream/index.m3u8 2>/dev/null | head -3 || echo "HLS stream not available"
echo

echo "WebRTC Stream:"
curl -s http://192.168.68.107:8889/stream 2>/dev/null | head -1 || echo "WebRTC stream not available"
echo

echo "=== End Status ==="










