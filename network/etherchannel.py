"""
EtherChannel (Port-Channel) collection.
Parses 'show etherchannel summary'.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import List

from network.ssh_client import SSHClient

logger = logging.getLogger(__name__)


@dataclass
class EtherChannel:
    """Single EtherChannel / Port-Channel entry."""
    port_channel: str = ""
    protocol: str = ""
    status: str = ""
    member_ports: List[str] = field(default_factory=list)


def collect_etherchannel(client: SSHClient) -> List[EtherChannel]:
    """
    Collect EtherChannel data.

    Returns empty list if no port-channels configured or on failure.
    """
    try:
        raw = client.send_command("show etherchannel summary")
    except Exception as exc:
        logger.warning("[%s] EtherChannel command failed: %s", client.ip, exc)
        return []

    if not raw:
        return []

    # Genie first
    result = _parse_with_genie(client.ip, raw)
    if result:
        return result

    return _parse_with_regex(raw)


def _parse_with_genie(ip: str, raw: str) -> List[EtherChannel]:
    """Use Genie ShowEtherchannelSummary."""
    try:
        from genie.libs.parser.iosxe.show_etherchannel import ShowEtherchannelSummary
        from unittest.mock import MagicMock

        device = MagicMock()
        device.os = "iosxe"
        device.custom = {"abstraction": {"order": ["os"]}}

        parser = ShowEtherchannelSummary(device=device)
        parsed = parser.parse(output=raw)

        channels = []
        for po_name, po_data in parsed.get("interfaces", {}).items():
            members = list(po_data.get("members", {}).keys())
            protocol = po_data.get("protocol", "")
            if isinstance(protocol, str):
                protocol = protocol.upper().strip("-") or "NONE"
            flags = po_data.get("oper_status", "")

            channels.append(EtherChannel(
                port_channel=po_name,
                protocol=str(protocol),
                status=str(flags),
                member_ports=members,
            ))

        logger.debug("[%s] Genie parsed %d EtherChannels.", ip, len(channels))
        return channels

    except Exception as exc:
        logger.debug("[%s] Genie EtherChannel parse failed (%s), using regex.", ip, exc)
        return []


def _parse_with_regex(raw: str) -> List[EtherChannel]:
    """
    Regex fallback.

    Example line:
        1      Po1(SU)         LACP      Gi1/0/1(P)  Gi1/0/2(P)
    """
    channels: List[EtherChannel] = []

    # Pattern: group_num  Po<n>(<flags>)  [protocol]  members...
    line_re = re.compile(
        r"^\s*\d+\s+(Po\d+)\((\w+)\)\s+(\S+)\s+(.*)",
        re.IGNORECASE,
    )
    member_re = re.compile(r"([A-Za-z]{2,}[\d/]+)\(\w+\)")

    for line in raw.splitlines():
        m = line_re.match(line)
        if not m:
            continue

        po_name = m.group(1)
        flags = m.group(2)
        protocol = m.group(3).upper()
        members_raw = m.group(4)

        members = member_re.findall(members_raw)
        channels.append(EtherChannel(
            port_channel=po_name,
            protocol=protocol if protocol not in ("-", "") else "NONE",
            status=flags,
            member_ports=members,
        ))

    return channels
