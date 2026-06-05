"""
CDP neighbor collection using Genie parser with TextFSM fallback.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional

from network.ssh_client import SSHClient

logger = logging.getLogger(__name__)


@dataclass
class CDPNeighbor:
    """Single CDP neighbor entry."""
    neighbor_hostname: str = ""
    neighbor_ip: str = ""
    platform: str = ""
    local_interface: str = ""
    remote_interface: str = ""


def collect_cdp_neighbors(client: SSHClient) -> List[CDPNeighbor]:
    """
    Collect CDP neighbors from a device.

    Tries Genie parser first; falls back to regex if parsing fails.

    Returns an empty list if CDP is disabled or no neighbors found.
    """
    try:
        raw = client.send_command("show cdp neighbors detail")
    except Exception as exc:
        logger.warning("[%s] CDP command failed: %s", client.ip, exc)
        return []

    if not raw or any(msg in raw.lower() for msg in ["cdp is not enabled", "% cdp"]):
        logger.info("[%s] CDP disabled or no output.", client.ip)
        return []

    # Try Genie
    neighbors = _parse_with_genie(client.ip, raw)
    if neighbors:
        return neighbors

    # Fallback to regex
    return _parse_with_regex(raw)


def _parse_with_genie(ip: str, raw: str) -> List[CDPNeighbor]:
    """Parse CDP output using pyATS/Genie."""
    try:
        from genie.libs.parser.iosxe.show_cdp import ShowCdpNeighborsDetail
        from unittest.mock import MagicMock

        device = MagicMock()
        device.os = "iosxe"
        device.custom = {"abstraction": {"order": ["os"]}}

        parser = ShowCdpNeighborsDetail(device=device)
        parsed = parser.parse(output=raw)

        neighbors = []
        index_data = parsed.get("index", {})

        for _idx, entry in index_data.items():
            n = CDPNeighbor(
                neighbor_hostname=str(entry.get("device_id", "")).split(".")[0],
                neighbor_ip=_first_ip(entry.get("management_addresses", {})),
                platform=str(entry.get("platform", "")),
                local_interface=str(entry.get("local_interface", "")),
                remote_interface=str(entry.get("port_id", "")),
            )
            if n.neighbor_hostname:
                neighbors.append(n)

        logger.debug("[%s] Genie parsed %d CDP neighbors.", ip, len(neighbors))
        return neighbors

    except Exception as exc:
        logger.debug("[%s] Genie CDP parse failed (%s), using regex fallback.", ip, exc)
        return []


def _first_ip(addr_dict: dict) -> str:
    """Extract first IP address from Genie address dict."""
    if not isinstance(addr_dict, dict):
        return ""
    for v in addr_dict.values():
        if isinstance(v, dict):
            ip = v.get("ip", "")
            if ip:
                return str(ip)
        elif isinstance(v, str) and re.match(r"\d+\.\d+\.\d+\.\d+", v):
            return v
    return ""


def _parse_with_regex(raw: str) -> List[CDPNeighbor]:
    """Regex-based fallback CDP parser."""
    neighbors: List[CDPNeighbor] = []
    blocks = re.split(r"-{20,}", raw)

    for block in blocks:
        if not block.strip():
            continue

        hostname_m = re.search(r"Device ID:\s*(.+)", block, re.IGNORECASE)
        ip_m = re.search(r"IP(?:v4)? [Aa]ddress:\s*([\d.]+)", block)
        platform_m = re.search(r"Platform:\s*(.+?),", block, re.IGNORECASE)
        local_m = re.search(r"Interface:\s*(\S+),", block, re.IGNORECASE)
        remote_m = re.search(r"Port ID \(outgoing port\):\s*(\S+)", block, re.IGNORECASE)

        if hostname_m:
            neighbors.append(CDPNeighbor(
                neighbor_hostname=hostname_m.group(1).strip().split(".")[0],
                neighbor_ip=ip_m.group(1) if ip_m else "",
                platform=platform_m.group(1).strip() if platform_m else "",
                local_interface=local_m.group(1) if local_m else "",
                remote_interface=remote_m.group(1) if remote_m else "",
            ))

    return neighbors
