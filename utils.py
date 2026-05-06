from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class Target:
    raw: str
    ip: str
    hostname: Optional[str]


def resolve_target(value: str) -> Target:
    value = value.strip()
    if not value:
        raise ValueError("Target is empty.")

    # Fast-path: already an IP.
    try:
        ipaddress.ip_address(value)
        return Target(raw=value, ip=value, hostname=None)
    except ValueError:
        pass

    try:
        ip = socket.gethostbyname(value)
    except OSError as exc:
        raise ValueError(f"Could not resolve '{value}' to an IP address: {exc}") from exc

    return Target(raw=value, ip=ip, hostname=value)


def parse_port_range(start: Optional[int], end: Optional[int]) -> Tuple[int, int]:
    if start is None and end is None:
        raise ValueError("Start/end ports are missing.")
    if start is None or end is None:
        raise ValueError("Both start and end ports must be provided for a range.")
    if start < 1 or end < 1 or start > 65535 or end > 65535:
        raise ValueError("Ports must be in range 1..65535.")
    if end < start:
        raise ValueError("End port must be >= start port.")
    return start, end


def parse_ports_list(value: str) -> List[int]:
    """
    Accepts:
      - Comma separated ports: "22,80,443"
      - Ranges: "1-1024"
      - Mixed: "22,80-90,443"
    """
    raw = value.strip()
    if not raw:
        raise ValueError("Port list is empty.")

    ports: List[int] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            a_i = int(a.strip())
            b_i = int(b.strip())
            if a_i < 1 or b_i < 1 or a_i > 65535 or b_i > 65535 or b_i < a_i:
                raise ValueError(f"Invalid port range '{part}'.")
            ports.extend(range(a_i, b_i + 1))
        else:
            p = int(part)
            if p < 1 or p > 65535:
                raise ValueError(f"Invalid port '{p}'.")
            ports.append(p)

    # Unique + sorted.
    return sorted(set(ports))


def chunked(seq: Sequence[int], size: int) -> Iterable[Sequence[int]]:
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


def service_name(port: int) -> Optional[str]:
    try:
        name = socket.getservbyport(port, "tcp")
        return name
    except OSError:
        return None

