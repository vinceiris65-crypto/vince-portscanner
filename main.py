from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import List, Optional

try:
    from colorama import Fore, Style, init as colorama_init
except ModuleNotFoundError:  # optional dependency
    class _NoColor:
        BLACK = RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = RESET = ""

    class _NoStyle:
        RESET_ALL = ""

    Fore = _NoColor()  # type: ignore
    Style = _NoStyle()  # type: ignore

    def colorama_init(*_args, **_kwargs) -> None:  # type: ignore
        return None

from config import (
    DEFAULT_END_PORT,
    DEFAULT_START_PORT,
    DEFAULT_TIMEOUT_S,
    DEFAULT_WORKERS,
)
from scanner import PortResult, scan_ports
from utils import parse_port_range, parse_ports_list, resolve_target


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="port-scanner",
        description="Educational TCP port scanner. Only scan targets you own or have explicit permission to test.",
    )
    p.add_argument("target", help="IP address or domain name (e.g., 192.168.1.10 or example.com)")

    range_group = p.add_argument_group("port selection")
    range_group.add_argument("start_port", nargs="?", type=int, default=None, help="Start port (default: 1)")
    range_group.add_argument("end_port", nargs="?", type=int, default=None, help="End port (default: 1024)")
    range_group.add_argument(
        "-p",
        "--ports",
        dest="ports_list",
        default=None,
        help='Comma list/ranges (e.g. "22,80,443" or "1-1024" or "22,80-90")',
    )

    perf = p.add_argument_group("performance")
    perf.add_argument("-w", "--workers", type=int, default=DEFAULT_WORKERS, help=f"Thread workers (default: {DEFAULT_WORKERS})")
    perf.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_S,
        help=f"Socket timeout in seconds (default: {DEFAULT_TIMEOUT_S})",
    )

    out = p.add_argument_group("output")
    out.add_argument("--no-color", action="store_true", help="Disable colored output")
    out.add_argument("--show-closed", action="store_true", help="Also print closed ports")
    out.add_argument("--json", dest="json_path", default=None, help="Write results to a JSON file")
    out.add_argument("--txt", dest="txt_path", default=None, help="Write results to a text file")

    return p


def _colorize(enabled: bool, text: str, color: str) -> str:
    if not enabled:
        return text
    return f"{color}{text}{Style.RESET_ALL}"


def _print_result(res: PortResult, *, color: bool) -> None:
    if res.open:
        tag = _colorize(color, "[OPEN]", Fore.GREEN)
        svc = f" → {res.service.upper()}" if res.service else ""
        print(f"{tag} {res.port:>5}{svc}")
    else:
        tag = _colorize(color, "[CLOSED]", Fore.RED)
        err = f" ({res.error})" if res.error else ""
        print(f"{tag} {res.port:>5}{err}")


def _write_json(path: str, *, target: str, ip: str, results: List[PortResult], elapsed_s: float) -> None:
    payload = {
        "target": target,
        "ip": ip,
        "elapsed_s": round(elapsed_s, 6),
        "results": [
            {"port": r.port, "open": r.open, "service": r.service, "error": r.error} for r in results
        ],
    }
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_txt(path: str, *, target: str, ip: str, results: List[PortResult], elapsed_s: float) -> None:
    lines: List[str] = []
    lines.append(f"Target: {target} ({ip})")
    lines.append(f"Elapsed: {elapsed_s:.3f}s")
    lines.append("")
    for r in results:
        if r.open:
            svc = f" -> {r.service}" if r.service else ""
            lines.append(f"[OPEN] {r.port}{svc}")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    color = not args.no_color
    if color:
        colorama_init()

    try:
        target = resolve_target(args.target)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    if args.ports_list:
        try:
            ports = parse_ports_list(args.ports_list)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 2
    else:
        start = args.start_port if args.start_port is not None else DEFAULT_START_PORT
        end = args.end_port if args.end_port is not None else DEFAULT_END_PORT
        try:
            start, end = parse_port_range(start, end)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 2
        ports = list(range(start, end + 1))

    print(f"Target: {target.raw} ({target.ip})")
    if target.hostname:
        print(f"Resolved: {target.hostname} -> {target.ip}")
    print(f"Ports: {ports[0]}..{ports[-1]} ({len(ports)} total)" if ports else "Ports: none")
    print(f"Workers: {args.workers} | Timeout: {args.timeout}s")
    print("")

    last_progress_ts = 0.0

    def progress_cb(completed: int, total: int, done: bool = False, elapsed_s: float = 0.0, **_):
        nonlocal last_progress_ts
        now = time.monotonic()
        if done:
            sys.stderr.write("\r" + " " * 60 + "\r")
            sys.stderr.flush()
            return
        if now - last_progress_ts < 0.1:
            return
        last_progress_ts = now
        sys.stderr.write(f"\rProgress: {completed}/{total}")
        sys.stderr.flush()

    start_ts = time.perf_counter()
    try:
        results = scan_ports(
            target.ip,
            ports,
            workers=args.workers,
            timeout_s=args.timeout,
            progress_cb=progress_cb,
        )
    except ValueError as exc:
        sys.stderr.write("\n")
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    elapsed_s = time.perf_counter() - start_ts
    sys.stderr.write("\n\n")

    open_results = [r for r in results if r.open]
    for r in results:
        if r.open or args.show_closed:
            _print_result(r, color=color)

    print("")
    print("Scan completed")
    print(f"Open ports: {len(open_results)}")
    print(f"Time taken: {elapsed_s:.3f} seconds")

    if args.json_path:
        _write_json(args.json_path, target=target.raw, ip=target.ip, results=results, elapsed_s=elapsed_s)
        print(f"Wrote JSON: {args.json_path}")
    if args.txt_path:
        _write_txt(args.txt_path, target=target.raw, ip=target.ip, results=results, elapsed_s=elapsed_s)
        print(f"Wrote TXT: {args.txt_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
