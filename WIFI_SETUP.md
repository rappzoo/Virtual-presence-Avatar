# WiFi Configuration - Avatar Tank

## Current WiFi Networks

The Avatar Tank is configured to automatically connect to available WiFi networks based on priority:

### Priority Order (Highest to Lowest)

1. **SID_GUEST** - Priority 100 (Primary)
   - SSID: `SID_GUEST`
   - Password: `BunVenit!`
   - Use: Primary network when in range

2. **preconfigured** - Priority 50 (Secondary)
   - Existing network configuration
   - Use: Backup when SID_GUEST not available

3. **havatar-mobile** - Priority 10 (Fallback)
   - SSID: `havatar`
   - Password: `pk2wdspN6sty`
   - Use: Mobile router - used when others not available

## How It Works

NetworkManager automatically:
- Scans for available networks
- Connects to the highest priority network in range
- Switches to higher priority network when available
- Falls back to lower priority if connection is lost

## Managing WiFi Connections

### View All Connections
```bash
nmcli connection show
```

### View WiFi Priorities
```bash
nmcli -f NAME,AUTOCONNECT,AUTOCONNECT-PRIORITY,TYPE connection show | grep wifi
```

### Connect to Specific Network
```bash
sudo nmcli connection up "SID_GUEST"
sudo nmcli connection up "havatar-mobile"
sudo nmcli connection up "preconfigured"
```

### Disconnect from Network
```bash
sudo nmcli connection down "SID_GUEST"
```

### Check Current Connection
```bash
nmcli device status
nmcli connection show --active
```

### Add New WiFi Network
```bash
sudo nmcli connection add type wifi ifname wlan0 \
  con-name "NETWORK_NAME" \
  ssid "SSID" \
  wifi-sec.key-mgmt wpa-psk \
  wifi-sec.psk "PASSWORD" \
  connection.autoconnect yes \
  connection.autoconnect-priority PRIORITY
```

### Modify Priority
```bash
sudo nmcli connection modify "NETWORK_NAME" connection.autoconnect-priority PRIORITY
```

### Delete Network
```bash
sudo nmcli connection delete "NETWORK_NAME"
```

## Priority Guidelines

- **100+**: Primary networks (home, office)
- **50-99**: Secondary networks (backup locations)
- **10-49**: Fallback networks (mobile hotspots)
- **0-9**: Low priority networks (public WiFi)
- **Negative**: Disabled auto-connect (manual only)

## Network Details

### SID_GUEST
- **Type**: Fixed location network
- **Security**: WPA-PSK
- **Auto-connect**: Yes
- **Priority**: 100 (Highest)

### preconfigured
- **Type**: Existing network
- **Auto-connect**: Yes
- **Priority**: 50 (Medium)

### havatar-mobile
- **Type**: Mobile router
- **Security**: WPA-PSK
- **Auto-connect**: Yes
- **Priority**: 10 (Lowest - fallback only)

## Troubleshooting

### Network Not Connecting
```bash
# Rescan networks
sudo nmcli device wifi rescan

# List available networks
nmcli device wifi list

# Check connection status
nmcli connection show "NETWORK_NAME"

# Restart NetworkManager
sudo systemctl restart NetworkManager
```

### Force Connection to Specific Network
```bash
# Disconnect current
sudo nmcli connection down $(nmcli -t -f NAME connection show --active | head -1)

# Connect to desired
sudo nmcli connection up "NETWORK_NAME"
```

### View Connection Details
```bash
nmcli connection show "NETWORK_NAME"
```

### Test Network Speed
```bash
# Download test
curl -o /dev/null http://speedtest.wdc01.softlayer.com/downloads/test10.zip

# Ping test
ping -c 10 8.8.8.8
```

## Security Notes

- Passwords are stored encrypted in NetworkManager
- Connection profiles: `/etc/NetworkManager/system-connections/`
- Only root can read connection files
- Passwords visible with: `sudo nmcli connection show "NAME" --show-secrets`

## Backup Configuration

### Export Connections
```bash
sudo cp -r /etc/NetworkManager/system-connections/ ~/wifi-backup/
```

### Restore Connections
```bash
sudo cp ~/wifi-backup/* /etc/NetworkManager/system-connections/
sudo chmod 600 /etc/NetworkManager/system-connections/*
sudo systemctl restart NetworkManager
```

## Remote Access

When connected to any of these networks, the Avatar Tank is accessible at:
- **WebRTC/HLS**: Port 8889, 8888
- **Flask API**: Port 5000
- **SSH**: Port 22

IP addresses are displayed in service logs:
```bash
sudo journalctl -u avatar-tank.service -n 50 | grep "RPi IP"
```

## Mobile Router Notes

The `havatar-mobile` connection is specifically for mobile/portable use:
- **Data Usage**: Monitor 4G data when using mobile router
- **Priority**: Set lowest to avoid accidental connection when home networks available
- **Stream Control**: Service automatically stops stream when webpage closed to save data

## Current Status

View current network status:
```bash
echo "=== Current Connection ==="
nmcli connection show --active | grep wifi
echo ""
echo "=== WiFi Device Status ==="
nmcli device status | grep wifi
echo ""
echo "=== Signal Strength ==="
nmcli device wifi list | head -5
```

---

**Last Updated**: After adding SID_GUEST and havatar-mobile networks
**Configuration Method**: NetworkManager (nmcli)
