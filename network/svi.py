"""
SVI (Layer-3 VLAN interface) collection.
Parses 'show ip interface brief' for Vlan* interfaces.
"""

from __future__ import annotations

import logging
import re
from typing import List

from network.ssh_client import SSHClient

logger = logging.getLogger(__name__)


def collect_svi_interfaces(client: SSHClient) -> List[str]:
    """
    Return list of VLAN SVI interface names (e.g. ['Vlan10', 'Vlan20']).

    Returns empty list on failure.
    """
    try:
        raw = client.send_command("show ip interface brief")
    except Exception as exc:
        logger.warning("[%s] SVI command failed: %s", client.ip, exc)
        return []

    if not raw:
        return []

    # Try Genie
    svis = _parse_with_genie(client.ip, raw)
    if svis:
        return svis

    return _parse_with_regex(raw)


def _parse_with_genie(ip: str, raw: str) -> List[str]:
    """Use Genie ShowIpInterfaceBrief."""
    try:
        from genie.libs.parser.iosxe.show_interface import ShowIpInterfaceBrief
        from unittest.mock import MagicMock

        device = MagicMock()
        device.os = "iosxe"
        device.custom = {"abstraction": {"order": ["os"]}}

        parser = ShowIpInterfaceBrief(device=device)
        parsed = parser.parse(output=raw)

        svis = [
            intf
            for intf in parsed.get("interface", {})
            if intf.lower().startswith("vlan")
        ]
        logger.debug("[%s] Genie parsed %d SVIs.", ip, len(svis))
        return sorted(svis, key=lambda x: int(re.sub(r"\D", "", x) or 0))

    except Exception as exc:
        logger.debug("[%s] Genie SVI parse failed (%s), using regex.", ip, exc)
        return []


def _parse_with_regex(raw: str) -> List[str]:
    """Regex fallback for SVI extraction."""
    svis = []
    for line in raw.splitlines():
        m = re.match(r"^\s*(Vlan\d+)\s+", line, re.IGNORECASE)
        if m:
            svis.append(m.group(1))
    return sorted(svis, key=lambda x: int(re.sub(r"\D", "", x) or 0))
