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

## Installation

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

Default scan (`1–1024`):

```bash
python main.py 192.168.1.1
```

Custom range:

```bash
python main.py 192.168.1.1 1 2000
```

Specific ports/ranges:

```bash
python main.py example.com -p "22,80,443,8000-8100"
```

Tune performance:

```bash
python main.py 192.168.1.1 1 1024 -w 300 --timeout 0.3
```

Export:

```bash
python main.py 192.168.1.1 -p "22,80,443" --json results.json --txt results.txt
```

