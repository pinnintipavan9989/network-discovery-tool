"""
VLAN collection using 'show vlan brief'.
Genie parser preferred; regex fallback.
"""

from __future__ import annotations

import logging
import re
from typing import List

from network.ssh_client import SSHClient

logger = logging.getLogger(__name__)


def collect_vlans(client: SSHClient) -> List[str]:
    """
    Return list of VLAN IDs present on the device.

    Skips reserved VLANs (1002-1005).
    Returns empty list on failure.
    """
    try:
        raw = client.send_command("show vlan brief")
    except Exception as exc:
        logger.warning("[%s] VLAN command failed: %s", client.ip, exc)
        return []

    if not raw:
        return []

    # Try Genie
    vlans = _parse_with_genie(client.ip, raw)
    if vlans:
        return vlans

    return _parse_with_regex(raw)


def _parse_with_genie(ip: str, raw: str) -> List[str]:
    """Parse with Genie ShowVlanBrief parser."""
    try:
        from genie.libs.parser.iosxe.show_vlan import ShowVlanBrief
        from unittest.mock import MagicMock

        device = MagicMock()
        device.os = "iosxe"
        device.custom = {"abstraction": {"order": ["os"]}}

        parser = ShowVlanBrief(device=device)
        parsed = parser.parse(output=raw)

        reserved = {1002, 1003, 1004, 1005}
        vlans = []
        for vlan_id_str in parsed.get("vlans", {}):
            try:
                vid = int(vlan_id_str)
                if vid not in reserved:
                    vlans.append(str(vid))
            except ValueError:
                pass

        logger.debug("[%s] Genie parsed %d VLANs.", ip, len(vlans))
        return sorted(vlans, key=lambda x: int(x))

    except Exception as exc:
        logger.debug("[%s] Genie VLAN parse failed (%s), using regex.", ip, exc)
        return []


def _parse_with_regex(raw: str) -> List[str]:
    """Regex fallback: parse VLAN IDs from 'show vlan brief' output."""
    reserved = {1002, 1003, 1004, 1005}
    vlans = []

    for line in raw.splitlines():
        m = re.match(r"^\s*(\d+)\s+\S+\s+(active|suspended)", line, re.IGNORECASE)
        if m:
            vid = int(m.group(1))
            if vid not in reserved:
                vlans.append(str(vid))

    return sorted(vlans, key=lambda x: int(x))
