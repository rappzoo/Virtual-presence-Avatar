#!/bin/bash
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() { echo -e "${GREEN}[INFO]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()  { echo -e "${RED}[ERROR]${NC} $*"; }

ESP_CHIP="esp32"
DEFAULT_PORT="/dev/ttyUSB0"
BUILD_DIR="$(cd "$(dirname "$0")" && pwd)/build/esp32.esp32.esp32"
MERGED_BIN="$BUILD_DIR/crawler_motor_control.ino.merged.bin"
BOOT_BIN="$BUILD_DIR/crawler_motor_control.ino.bootloader.bin"
PART_BIN="$BUILD_DIR/crawler_motor_control.ino.partitions.bin"
APP_BIN="$BUILD_DIR/crawler_motor_control.ino.bin"

ensure_tools() {
  info "Installing required tools (python3-pip, esptool)..."
  sudo apt-get update -y
  sudo apt-get install -y python3 python3-pip python3-serial
  if ! command -v esptool.py >/dev/null 2>&1; then
    pip3 install --user esptool
  fi
  if ! command -v esptool.py >/dev/null 2>&1; then
    export PATH="$HOME/.local/bin:$PATH"
  fi
  if ! command -v esptool.py >/dev/null 2>&1; then
    err "esptool.py not found after install. Try: export PATH=\"$HOME/.local/bin:$PATH\""
    exit 1
  fi
}

set_permissions() {
  info "Setting serial permissions..."
  sudo usermod -a -G dialout "$USER" || true
  local port
  port=$(detect_port || true)
  if [[ -n "${port:-}" && -e "$port" ]]; then
    sudo chmod 666 "$port" || true
  else
    warn "ESP32 port not detected yet; permissions will apply on next plug-in"
  fi
}

detect_port() {
  local p
  for p in /dev/ttyUSB* /dev/ttyACM*; do
    [[ -e "$p" ]] && { echo "$p"; return 0; }
  done
  return 1
}

flash() {
  local port
  port=${1:-}
  if [[ -z "$port" ]]; then
    port=$(detect_port || true)
  fi
  if [[ -z "$port" ]]; then
    err "No serial port found. Plug the ESP32 via USB and retry."
    exit 1
  fi
  info "Using port: $port"

  if [[ -f "$MERGED_BIN" ]]; then
    info "Flashing merged image: $MERGED_BIN"
    esptool.py --chip "$ESP_CHIP" --port "$port" --baud 460800 write_flash -z 0x0 "$MERGED_BIN"
    return
  fi

  if [[ -f "$BOOT_BIN" && -f "$PART_BIN" && -f "$APP_BIN" ]]; then
    info "Flashing bootloader/partitions/app images"
    esptool.py --chip "$ESP_CHIP" --port "$port" --baud 460800 write_flash -z \
      0x1000 "$BOOT_BIN" \
      0x8000 "$PART_BIN" \
      0x10000 "$APP_BIN"
    return
  fi

  err "No firmware images found in $BUILD_DIR"
  exit 1
}

post_check() {
  local port
  port=$(detect_port || echo "$DEFAULT_PORT")
  info "Reading chip ID..."
  esptool.py --chip "$ESP_CHIP" --port "$port" chip_id || warn "Chip ID read failed (device may have rebooted)."
  info "Done. If permissions were just added, log out/in for them to take effect."
}

usage() {
  cat <<USAGE
Usage: $0 [--port /dev/ttyUSBx] [--no-install] [--no-perms]

Flashes the ESP32 firmware built by Arduino IDE into: 
  $BUILD_DIR

Prefers merged binary; falls back to bootloader/partitions/app images.
USAGE
}

PORT=""
DO_INSTALL=1
DO_PERMS=1
while [[ $# -gt 0 ]]; do
  case "$1" in
    --port) PORT="$2"; shift 2;;
    --no-install) DO_INSTALL=0; shift;;
    --no-perms) DO_PERMS=0; shift;;
    -h|--help) usage; exit 0;;
    *) warn "Unknown arg: $1"; usage; exit 1;;
  esac
done

[[ $DO_INSTALL -eq 1 ]] && ensure_tools
[[ $DO_PERMS -eq 1 ]] && set_permissions
flash "$PORT"
post_check





