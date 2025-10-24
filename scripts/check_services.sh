#!/bin/bash
# Avatar Tank Service Audit Script
# Checks for duplicate services and conflicts
# Run regularly to prevent OOM crashes

echo "🔍 Avatar Tank Service Audit"
echo "============================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ISSUES_FOUND=0

# Check enabled services
echo "📋 Checking enabled services..."
echo ""

if systemctl is-enabled avatar-tank.service &>/dev/null; then
    echo -e "  ${GREEN}✓${NC} avatar-tank.service is ENABLED (correct)"
else
    echo -e "  ${RED}❌${NC} avatar-tank.service is DISABLED (SHOULD be enabled!)"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi

if systemctl is-enabled avatar-mediamtx.service &>/dev/null; then
    echo -e "  ${RED}❌${NC} avatar-mediamtx.service is ENABLED (SHOULD be disabled!)"
    echo -e "     ${YELLOW}→ Fix: sudo systemctl disable avatar-mediamtx.service${NC}"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
else
    echo -e "  ${GREEN}✓${NC} avatar-mediamtx.service is disabled (correct)"
fi

if systemctl is-enabled mediamtx.service &>/dev/null; then
    echo -e "  ${RED}❌${NC} mediamtx.service is ENABLED (SHOULD be disabled!)"
    echo -e "     ${YELLOW}→ Fix: sudo systemctl disable mediamtx.service${NC}"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
else
    echo -e "  ${GREEN}✓${NC} mediamtx.service is disabled (correct)"
fi

echo ""
echo "📊 Checking running services..."
echo ""

if systemctl is-active avatar-tank.service &>/dev/null; then
    echo -e "  ${GREEN}✓${NC} avatar-tank.service is running"
else
    echo -e "  ${RED}❌${NC} avatar-tank.service is NOT running (SHOULD be running!)"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi

if systemctl is-active avatar-mediamtx.service &>/dev/null; then
    echo -e "  ${RED}❌${NC} avatar-mediamtx.service is running (SHOULD be stopped!)"
    echo -e "     ${YELLOW}→ Fix: sudo systemctl stop avatar-mediamtx.service${NC}"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
else
    echo -e "  ${GREEN}✓${NC} avatar-mediamtx.service is not running (correct)"
fi

if systemctl is-active mediamtx.service &>/dev/null; then
    echo -e "  ${RED}❌${NC} mediamtx.service is running (SHOULD be stopped!)"
    echo -e "     ${YELLOW}→ Fix: sudo systemctl stop mediamtx.service${NC}"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
else
    echo -e "  ${GREEN}✓${NC} mediamtx.service is not running (correct)"
fi

echo ""
echo "🔢 Checking MediaMTX instance count..."
echo ""

# Count actual MediaMTX binary processes (not Python parent)
MEDIAMTX_COUNT=$(ps aux | grep "[/]usr/local/bin/mediamtx" | wc -l)
echo "  Found: $MEDIAMTX_COUNT MediaMTX binary process(es)"

if [ "$MEDIAMTX_COUNT" -eq 0 ]; then
    echo -e "  ${YELLOW}⚠${NC}  No MediaMTX instances running (stream not active or not started yet)"
elif [ "$MEDIAMTX_COUNT" -eq 1 ]; then
    echo -e "  ${GREEN}✓${NC} Correct! Only 1 MediaMTX instance"
    ps aux | grep "[/]usr/local/bin/mediamtx" | awk '{printf "     PID: %s, CPU: %s%%, MEM: %s%%\n", $2, $3, $4}'
    
    # Check if it's a child of avatar-tank
    MEDIAMTX_PID=$(pgrep -f "/usr/local/bin/mediamtx" | head -1)
    PYTHON_PID=$(pgrep -f "mediamtx_main" | head -1)
    if [ ! -z "$MEDIAMTX_PID" ] && [ ! -z "$PYTHON_PID" ]; then
        PARENT_PID=$(ps -o ppid= -p $MEDIAMTX_PID | tr -d ' ')
        if [ "$PARENT_PID" = "$PYTHON_PID" ]; then
            echo -e "  ${GREEN}✓${NC} MediaMTX is correctly launched by avatar-tank (parent PID: $PYTHON_PID)"
        else
            echo -e "  ${YELLOW}⚠${NC}  MediaMTX parent is PID $PARENT_PID (expected: $PYTHON_PID)"
        fi
    fi
else
    echo -e "  ${RED}❌${NC} WARNING: Multiple MediaMTX binary instances detected!"
    echo -e "  ${RED}❌${NC} This WILL cause crashes and OOM kills!"
    echo ""
    echo "  Processes:"
    ps aux | grep "[/]usr/local/bin/mediamtx" | awk '{printf "     PID: %s, PPID: %s, CPU: %s%%, MEM: %s%%\n", $2, $3, $3, $4}'
    echo ""
    echo -e "  ${YELLOW}→ Fix: Check for duplicate systemd services${NC}"
    echo -e "  ${YELLOW}→ Run: systemctl list-units | grep mediamtx${NC}"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi

echo ""
echo "🌐 Checking port usage..."
echo ""

if command -v netstat &> /dev/null; then
    PORTS=$(netstat -tulpn 2>/dev/null | grep -E ":5000|:8554|:8888|:8889|:9997")
    if [ -z "$PORTS" ]; then
        echo -e "  ${YELLOW}⚠${NC}  No services listening on expected ports (stream not active)"
    else
        echo "$PORTS" | while read line; do
            PORT=$(echo $line | awk '{print $4}' | cut -d: -f2)
            PID=$(echo $line | awk '{print $7}' | cut -d/ -f1)
            PROG=$(echo $line | awk '{print $7}' | cut -d/ -f2)
            
            if [ "$PORT" = "5000" ]; then
                echo -e "  ${GREEN}✓${NC} Port 5000 (Flask):  PID $PID ($PROG)"
            elif [ "$PORT" = "8554" ]; then
                echo -e "  ${GREEN}✓${NC} Port 8554 (RTSP):   PID $PID ($PROG)"
            elif [ "$PORT" = "8888" ]; then
                echo -e "  ${GREEN}✓${NC} Port 8888 (HLS):    PID $PID ($PROG)"
            elif [ "$PORT" = "8889" ]; then
                echo -e "  ${GREEN}✓${NC} Port 8889 (WebRTC): PID $PID ($PROG)"
            elif [ "$PORT" = "9997" ]; then
                echo -e "  ${GREEN}✓${NC} Port 9997 (API):    PID $PID ($PROG)"
            fi
        done
    fi
else
    echo -e "  ${YELLOW}⚠${NC}  netstat not available, skipping port check"
fi

echo ""
echo "💾 Checking memory usage..."
echo ""

TOTAL_MEM=$(free -m | awk '/^Mem:/{print $2}')
USED_MEM=$(free -m | awk '/^Mem:/{print $3}')
FREE_MEM=$(free -m | awk '/^Mem:/{print $4}')
AVAIL_MEM=$(free -m | awk '/^Mem:/{print $7}')
MEM_PERCENT=$((USED_MEM * 100 / TOTAL_MEM))

echo "  Total: ${TOTAL_MEM}MB, Used: ${USED_MEM}MB (${MEM_PERCENT}%), Available: ${AVAIL_MEM}MB"

if [ "$MEM_PERCENT" -lt 70 ]; then
    echo -e "  ${GREEN}✓${NC} Memory usage is healthy"
elif [ "$MEM_PERCENT" -lt 85 ]; then
    echo -e "  ${YELLOW}⚠${NC}  Memory usage is moderate (${MEM_PERCENT}%)"
else
    echo -e "  ${RED}❌${NC} Memory usage is HIGH (${MEM_PERCENT}%)! Risk of OOM!"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi

# Check Python process memory
PYTHON_PID=$(pgrep -f "mediamtx_main" | head -1)
if [ ! -z "$PYTHON_PID" ]; then
    PYTHON_MEM=$(ps -p $PYTHON_PID -o rss= 2>/dev/null)
    if [ ! -z "$PYTHON_MEM" ]; then
        PYTHON_MEM_MB=$((PYTHON_MEM / 1024))
        echo "  Python app (PID $PYTHON_PID): ${PYTHON_MEM_MB}MB"
        
        if [ "$PYTHON_MEM_MB" -gt 1000 ]; then
            echo -e "  ${RED}❌${NC} Python memory usage is very high! Possible memory leak!"
            ISSUES_FOUND=$((ISSUES_FOUND + 1))
        elif [ "$PYTHON_MEM_MB" -gt 500 ]; then
            echo -e "  ${YELLOW}⚠${NC}  Python memory usage is elevated"
        else
            echo -e "  ${GREEN}✓${NC} Python memory usage is normal"
        fi
    fi
fi

echo ""
echo "🔍 Checking for recent OOM kills..."
echo ""

OOM_KILLS=$(sudo journalctl --since "24 hours ago" 2>/dev/null | grep -c "killed.*status=9")
if [ "$OOM_KILLS" -gt 0 ]; then
    echo -e "  ${RED}❌${NC} Found $OOM_KILLS OOM kill(s) in the last 24 hours!"
    echo "  Recent kills:"
    sudo journalctl --since "24 hours ago" 2>/dev/null | grep "killed.*status=9" | tail -5 | sed 's/^/     /'
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
else
    echo -e "  ${GREEN}✓${NC} No OOM kills in the last 24 hours"
fi

echo ""
echo "============================"
echo ""

if [ "$ISSUES_FOUND" -eq 0 ]; then
    echo -e "${GREEN}✅ ALL CHECKS PASSED!${NC}"
    echo "System is healthy and configured correctly."
    exit 0
else
    echo -e "${RED}⚠️  FOUND $ISSUES_FOUND ISSUE(S)!${NC}"
    echo "Please fix the issues listed above to prevent crashes."
    exit 1
fi

