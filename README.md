# Network Discovery Tool

Enterprise-grade Cisco network discovery platform built with Python 3.12+.

---

## Features

- Concurrent SSH discovery (5–100 threads)
- CDP neighbor topology mapping
- VLAN, SVI, EtherChannel, and default gateway collection
- Genie/pyATS parsers with regex fallback
- Three-sheet Excel report with full formatting
- Professional PyQt6 GUI — never freezes
- Rotating log file with redacted credentials
- Supports 500+ devices

---

## Installation

### 1. Prerequisites

- Python 3.12 or newer
- pip

### 2. Clone / Extract

```bash
cd network_discovery_app
```

### 3. Create Virtual Environment (Recommended)

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Running

```bash
python main.py
```

---

## Input File Format

**File:** `input/input.xlsx`  
**Sheet:** `Devices`

| IP          | Username | Password  | Device_Type |
|-------------|----------|-----------|-------------|
| 10.10.10.1  | admin    | Cisco123  | cisco_ios   |
| 10.10.10.2  | admin    | Cisco123  | cisco_xe    |

**Supported Device Types:** `cisco_ios`, `cisco_xe`, `cisco_nxos`, `cisco_xr`

---

## Output File Format

Generated file: `reports/network_discovery_YYYYMMDD_HHMMSS.xlsx`

### Sheet 1 — Network Discovery
| Column | Description |
|--------|-------------|
| IP | Device management IP |
| Hostname | Discovered hostname |
| VLANs | Comma-separated VLAN IDs |
| SVI VLANs | Comma-separated SVI interfaces |
| Neighbor | CDP neighbor hostname |
| Neighbor IP | CDP neighbor IP |
| Platform | Neighbor platform |
| Local Interface | Local port toward neighbor |
| Remote Interface | Neighbor's port |
| Gateway | Default gateway IP |
| Status | SUCCESS or FAILED |

### Sheet 2 — Ethernet Channels
Port-channel groups with member ports and linked CDP neighbor.

### Sheet 3 — Failed Devices
All devices that could not be reached, with failure reason and timestamp.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `Authentication Failed` | Check credentials in input.xlsx |
| `SSH Timeout` | Verify device is reachable; increase `SSH_TIMEOUT` in config.py |
| `Connection Refused` | Confirm SSH (port 22) is enabled on device |
| `DNS Failure` | Use IP addresses instead of hostnames |
| `CDP Disabled` | Enable with `cdp run` on device; row still added to report |
| `Genie parse error` | Regex fallback is used automatically |
| GUI freezes | Should not occur; file a bug if it does |

---

## Security Notes

- Passwords are **never** written to logs or the Excel report.
- Credentials exist only in memory during the SSH session.
- Log files are stored in `logs/network_discovery.log` (rotated at 10 MB).

---

## PyInstaller Packaging

### Build Single Executable

```bash
pip install pyinstaller

pyinstaller \
  --onefile \
  --windowed \
  --name "NetworkDiscoveryTool" \
  --add-data "config.py:." \
  --hidden-import "genie.libs.parser.iosxe.show_cdp" \
  --hidden-import "genie.libs.parser.iosxe.show_vlan" \
  --hidden-import "genie.libs.parser.iosxe.show_interface" \
  --hidden-import "genie.libs.parser.iosxe.show_etherchannel" \
  --hidden-import "genie.libs.parser.iosxe.show_platform" \
  --hidden-import "netmiko" \
  --hidden-import "PyQt6" \
  main.py
```

Executable will be in `dist/NetworkDiscoveryTool` (or `.exe` on Windows).

### Create Required Directories Alongside Executable

```
dist/
├── NetworkDiscoveryTool.exe
├── input/          ← place input.xlsx here
├── logs/           ← auto-created
└── reports/        ← auto-created
```

---

## Configuration

Edit `config.py` to adjust:

- `SSH_TIMEOUT` — seconds before SSH connection times out (default: 30)
- `MAX_RETRIES` — SSH connection retry attempts (default: 2)
- `DEFAULT_THREADS` — default thread count (default: 10)
- Excel color constants

---

## Architecture

```
main.py                  Entry point
config.py                Central configuration
gui/
  main_window.py         PyQt6 main window
  worker.py              QThread discovery orchestrator
  styles.py              Stylesheet
  dialogs.py             Modal dialogs
network/
  ssh_client.py          Netmiko SSH wrapper
  discovery.py           Per-device orchestrator + DiscoveryResult
  cdp.py                 CDP neighbor collection
  vlan.py                VLAN collection
  svi.py                 SVI collection
  etherchannel.py        EtherChannel collection
  gateway.py             Default gateway extraction
excel/
  report_generator.py    OpenPyXL report builder
logs/                    Rotating log files
reports/                 Generated Excel reports
input/                   Input Excel files
```
