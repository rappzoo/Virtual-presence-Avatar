#!/bin/bash
# Avatar Tank Simple Startup

cd /home/havatar/Avatar-robot

# Kill any existing app process quickly
pkill -9 -f mediamtx_main.py 2>/dev/null || true
sleep 1

# MediaMTX is now managed by systemd (avatar-media.service)
# Ensure it's active before starting the app
if ! systemctl is-active --quiet avatar-media.service; then
	systemctl start avatar-media.service || true
	sleep 2
fi

# Start Flask in foreground (becomes main process for systemd)
exec python3 -u modules/mediamtx_main.py

