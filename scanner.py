from __future__ import annotations

import socket
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence

from config import MAX_PORTS, MAX_WORKERS
from utils import service_name


@dataclass(frozen=True)
class PortResult:
    port: int
    open: bool
    service: Optional[str]
    error: Optional[str] = None


def scan_port(ip: str, port: int, timeout_s: float) -> PortResult:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout_s)
    try:
        rc = sock.connect_ex((ip, port))
        is_open = rc == 0
        return PortResult(port=port, open=is_open, service=service_name(port) if is_open else None)
    except OSError as exc:
        return PortResult(port=port, open=False, service=None, error=str(exc))
    finally:
        try:
            sock.close()
        except OSError:
            pass


def scan_ports(
    ip: str,
    ports: Sequence[int],
    *,
    workers: int,
    timeout_s: float,
    progress_cb=None,
) -> List[PortResult]:
    if len(ports) > MAX_PORTS:
        raise ValueError(f"Refusing to scan {len(ports)} ports (max {MAX_PORTS}).")
    if workers < 1:
        raise ValueError("Workers must be >= 1.")
    if workers > MAX_WORKERS:
        raise ValueError(f"Workers too high (max {MAX_WORKERS}).")
    if timeout_s <= 0:
        raise ValueError("Timeout must be > 0 seconds.")

    start = time.perf_counter()
    results: List[PortResult] = []

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(scan_port, ip, port, timeout_s): port for port in ports}
        completed = 0
        for fut in as_completed(futures):
            results.append(fut.result())
            completed += 1
            if progress_cb is not None:
                progress_cb(completed, len(ports))

    results.sort(key=lambda r: r.port)
    elapsed_s = time.perf_counter() - start
    if progress_cb is not None:
        progress_cb(len(ports), len(ports), done=True, elapsed_s=elapsed_s)
    return results

