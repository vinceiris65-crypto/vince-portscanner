# Advanced Port Scanner (CLI)

Lightweight educational TCP port scanner written in Python.

## Disclaimer (Ethics)

Only scan systems you **own** or where you have **explicit permission** to test. Unauthorized scanning may be illegal and disruptive.

## Features

- Scan a single IP or domain
- Default port range `1–1024`
- Custom ranges and explicit port lists
- Multi-threaded scanning for speed
- Timeout control
- Simple service name mapping (port → common TCP service)
- Optional export to JSON/TXT

## Download

### Linux (Git)

```bash
git clone https://github.com/vinceiris65-crypto/vince-portscanner.git port-scanner
cd port-scanner
```

### Linux (ZIP)

```bash
# Default branch ZIP download (change `main` if your default branch is different)
curl -L -o port-scanner.zip "https://github.com/vinceiris65-crypto/vince-portscanner/archive/refs/heads/main.zip"
unzip port-scanner.zip
cd port-scanner*
```

## Installation

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
```

## Usage

Default scan (`1–1024`):

```bash
python3 main.py 192.168.1.1
```

Custom range:

```bash
python3 main.py 192.168.1.1 1 2000
```

Specific ports/ranges:

```bash
python3 main.py example.com -p "22,80,443,8000-8100"
```

Tune performance:

```bash
python3 main.py 192.168.1.1 1 1024 -w 300 --timeout 0.3
```

Export:

```bash
python3 main.py 192.168.1.1 -p "22,80,443" --json results.json --txt results.txt
```
