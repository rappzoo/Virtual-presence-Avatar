import os
import json
import threading
import time
import subprocess
from pathlib import Path


class WifiManager:
    """Simple Wi-Fi manager using nmcli when available, with preference handling and auto-selection.

    Notes:
    - Preferences are stored in config/wifi.json.
    - If nmcli is not available, scanning falls back to iw utilities where possible.
    - Connecting requires nmcli; otherwise a helpful error is returned.
    """

    def __init__(self, config_dir: str):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_path = self.config_dir / 'wifi.json'
        self._lock = threading.Lock()
        self._load_state()
        self._stop_event = threading.Event()
        self._thread = None

    # ---------- Persistence ----------
    def _load_state(self) -> None:
        default_state = {
            'auto_manage': True,
            'preferred_order': [],  # list of SSIDs, first is highest priority
            'known_networks': {}     # SSID -> {"psk": "..."}
        }
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    self.state = json.load(f)
            else:
                self.state = default_state
                self._save_state()
        except Exception:
            self.state = default_state

    def _save_state(self) -> None:
        tmp = self.config_path.with_suffix('.tmp')
        with open(tmp, 'w') as f:
            json.dump(self.state, f, indent=2)
        os.replace(tmp, self.config_path)

    # ---------- Utilities ----------
    @staticmethod
    def _has_nmcli() -> bool:
        return subprocess.run(['which', 'nmcli'], capture_output=True).returncode == 0

    @staticmethod
    def _run(cmd: list[str], timeout: int = 5) -> subprocess.CompletedProcess:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

    def _wifi_iface(self) -> str | None:
        try:
            res = self._run(['nmcli', '-t', '-f', 'DEVICE,TYPE,STATE', 'device', 'status'])
            if res.returncode == 0:
                for line in res.stdout.splitlines():
                    parts = (line or '').split(':')
                    if len(parts) >= 3 and parts[1] == 'wifi':
                        return parts[0]
        except Exception:
            pass
        return None

    # ---------- Public API ----------
    def status(self) -> dict:
        with self._lock:
            connected_ssid = None
            signal = None
            ip4 = None
            backend = 'nmcli' if self._has_nmcli() else 'iw'
            try:
                if self._has_nmcli():
                    # Current connection
                    res = self._run(['nmcli', '-t', '-f', 'active,ssid,signal,device', 'dev', 'wifi'])
                    if res.returncode == 0:
                        for line in res.stdout.splitlines():
                            parts = line.split(':')
                            if len(parts) >= 4 and parts[0] == 'yes':
                                connected_ssid = parts[1] or None
                                try:
                                    signal = int(parts[2]) if parts[2] else None
                                except Exception:
                                    signal = None
                                break
                    ipres = self._run(['nmcli', '-t', '-f', 'ip4.address', 'device', 'show'])
                    if ipres.returncode == 0:
                        for line in ipres.stdout.splitlines():
                            if line.strip().startswith('IP4.ADDRESS') or line.strip().startswith('IP4.ADDRESS[1]'):
                                ip4 = line.split(':', 1)[1].split('/')[0].strip()
                                break
                else:
                    # Fallback: iwgetid for SSID
                    ssid_res = self._run(['iwgetid', '-r'])
                    if ssid_res.returncode == 0:
                        connected_ssid = (ssid_res.stdout or '').strip() or None
            except Exception:
                pass

            return {
                'connected_ssid': connected_ssid,
                'signal': signal,
                'ip4': ip4,
                'backend': backend,
                'auto_manage': self.state.get('auto_manage', True),
                'preferred_order': list(self.state.get('preferred_order', [])),
                'known_networks': {k: {'has_psk': bool(v.get('psk'))} for k, v in self.state.get('known_networks', {}).items()}
            }

    def scan(self) -> list[dict]:
        networks: list[dict] = []
        try:
            if self._has_nmcli():
                # Trigger a fresh rescan on the Wi‑Fi interface if available for fuller results
                iface = self._wifi_iface()
                if iface:
                    self._run(['nmcli', 'device', 'wifi', 'rescan', 'ifname', iface], timeout=10)
                else:
                    self._run(['nmcli', 'device', 'wifi', 'rescan'], timeout=10)
                time.sleep(1.0)
                res = self._run(['nmcli', '-t', '-f', 'ssid,signal,security', 'dev', 'wifi', 'list'], timeout=10)
                if res.returncode == 0:
                    seen = set()
                    for line in res.stdout.splitlines():
                        parts = line.split(':')
                        if len(parts) >= 3:
                            ssid = parts[0]
                            if not ssid or ssid in seen:
                                continue
                            seen.add(ssid)
                            try:
                                sig = int(parts[1]) if parts[1] else None
                            except Exception:
                                sig = None
                            security = parts[2] or ''
                            networks.append({'ssid': ssid, 'signal': sig, 'security': security})
            else:
                # Try iwlist scan
                res = self._run(['bash', '-lc', "iwlist $(iw dev | awk '/Interface/ {print $2; exit}') scan 2>/dev/null | egrep 'ESSID|Signal level'"], timeout=10)
                if res.returncode == 0:
                    ssid = None
                    for line in res.stdout.splitlines():
                        line = line.strip()
                        if 'ESSID' in line:
                            ssid = line.split(':', 1)[1].strip().strip('"')
                        elif 'Signal level' in line and ssid:
                            networks.append({'ssid': ssid, 'signal': None, 'security': ''})
                            ssid = None
        except Exception:
            pass
        # Sort by signal descending where available
        networks.sort(key=lambda x: (x['signal'] is None, -(x['signal'] or 0)))
        return networks

    def scan_full(self) -> list[dict]:
        """Perform a full scan by briefly disconnecting and rescanning, then restoring connection."""
        if not self._has_nmcli():
            return self.scan()
        iface = self._wifi_iface()
        active_name = None
        try:
            cres = self._run(['nmcli', '-t', '-f', 'NAME,TYPE,DEVICE,ACTIVE', 'connection', 'show', '--active'], timeout=10)
            if cres.returncode == 0:
                for line in cres.stdout.splitlines():
                    name, ctype, dev, active = (line.split(':') + ['','','',''])[:4]
                    if ctype == 'wifi' and active == 'yes':
                        active_name = name
                        break
            if active_name:
                self._run(['nmcli', 'connection', 'down', active_name], timeout=10)
                time.sleep(2)
            if iface:
                self._run(['nmcli', 'device', 'wifi', 'rescan', 'ifname', iface], timeout=10)
            else:
                self._run(['nmcli', 'device', 'wifi', 'rescan'], timeout=10)
            time.sleep(2)
            nets = self.scan()
        finally:
            if active_name:
                self._run(['nmcli', 'connection', 'up', active_name], timeout=15)
        return nets

    def set_auto(self, enabled: bool) -> dict:
        with self._lock:
            self.state['auto_manage'] = bool(enabled)
            self._save_state()
            return {'ok': True, 'auto_manage': self.state['auto_manage']}

    def prefer(self, ssid: str) -> dict:
        if not ssid:
            return {'ok': False, 'msg': 'Missing ssid'}
        with self._lock:
            order = [s for s in self.state.get('preferred_order', []) if s != ssid]
            order.insert(0, ssid)
            self.state['preferred_order'] = order
            self._save_state()
            return {'ok': True, 'preferred_order': order}

    def set_priorities(self, ssids: list[str]) -> dict:
        with self._lock:
            # Keep only unique, non-empty
            clean = []
            for s in ssids:
                if s and s not in clean:
                    clean.append(s)
            self.state['preferred_order'] = clean
            self._save_state()
            return {'ok': True, 'preferred_order': clean}

    def save_known(self, ssid: str, psk: str | None) -> None:
        with self._lock:
            self.state.setdefault('known_networks', {})[ssid] = {'psk': psk or ''}
            if ssid not in self.state.setdefault('preferred_order', []):
                self.state['preferred_order'].append(ssid)
            self._save_state()

    def connect(self, ssid: str, psk: str | None = None) -> dict:
        if not self._has_nmcli():
            return {'ok': False, 'msg': 'nmcli not available; cannot connect programmatically'}
        if not ssid:
            return {'ok': False, 'msg': 'Missing ssid'}
        try:
            # If there is already a connection profile, try to up it
            con_list = self._run(['nmcli', '-t', '-f', 'NAME,TYPE', 'connection', 'show'])
            has_profile = False
            if con_list.returncode == 0:
                for line in con_list.stdout.splitlines():
                    name, _, = (line.split(':') + [''])[:2]
                    if name == ssid:
                        has_profile = True
                        break
            if has_profile:
                up = self._run(['nmcli', 'connection', 'up', ssid], timeout=20)
                if up.returncode == 0:
                    return {'ok': True, 'msg': f'Activated existing profile {ssid}'}
            # Else, try a direct connection
            if psk:
                cmd = ['nmcli', 'dev', 'wifi', 'connect', ssid, 'password', psk]
            else:
                cmd = ['nmcli', 'dev', 'wifi', 'connect', ssid]
            res = self._run(cmd, timeout=30)
            if res.returncode == 0:
                # Save credentials locally for auto-manage
                self.save_known(ssid, psk)
                return {'ok': True, 'msg': res.stdout.strip() or 'Connected'}
            return {'ok': False, 'msg': res.stderr.strip() or res.stdout.strip() or 'Connection failed'}
        except Exception as e:
            return {'ok': False, 'msg': str(e)}

    # ---------- Background Auto-Manager ----------
    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._auto_loop, name='WifiAutoManager', daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _best_available(self) -> str | None:
        scan = self.scan()
        if not scan:
            return None
        available_by_ssid = {n['ssid']: n for n in scan if n.get('ssid')}
        # Choose first preferred that is available; otherwise strongest open
        for ssid in self.state.get('preferred_order', []):
            if ssid in available_by_ssid:
                return ssid
        # No preferred available: return strongest by signal
        best = None
        best_sig = -10**9
        for n in scan:
            sig = n.get('signal')
            if sig is not None and sig > best_sig:
                best = n.get('ssid')
                best_sig = sig
        return best

    def _current_ssid(self) -> str | None:
        try:
            if self._has_nmcli():
                res = self._run(['nmcli', '-t', '-f', 'active,ssid', 'dev', 'wifi'])
                if res.returncode == 0:
                    for line in res.stdout.splitlines():
                        parts = line.split(':')
                        if len(parts) >= 2 and parts[0] == 'yes':
                            return parts[1] or None
            else:
                res = self._run(['iwgetid', '-r'])
                if res.returncode == 0:
                    return (res.stdout or '').strip() or None
        except Exception:
            pass
        return None

    def _auto_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                with self._lock:
                    auto = self.state.get('auto_manage', True)
                if not auto:
                    time.sleep(5)
                    continue
                # Only attempt programmatic connect with nmcli
                if not self._has_nmcli():
                    time.sleep(10)
                    continue
                current = self._current_ssid()
                target = self._best_available()
                if target and target != current:
                    creds = self.state.get('known_networks', {}).get(target, {})
                    psk = creds.get('psk') or None
                    self.connect(target, psk)
                time.sleep(10)
            except Exception:
                time.sleep(10)


# Singleton helper
_wifi_manager_singleton: WifiManager | None = None


def get_wifi_manager(config_dir: str) -> WifiManager:
    global _wifi_manager_singleton
    if _wifi_manager_singleton is None:
        _wifi_manager_singleton = WifiManager(config_dir)
        _wifi_manager_singleton.start()
    return _wifi_manager_singleton


