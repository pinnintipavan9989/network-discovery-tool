"""
Default gateway extraction from 'show ip route'.
"""

from __future__ import annotations

import logging
import re

from network.ssh_client import SSHClient

logger = logging.getLogger(__name__)


def collect_default_gateway(client: SSHClient) -> str:
    """
    Extract gateway of last resort from 'show ip route'.

    Returns IP string or "" if not found / command fails.
    """
    try:
        raw = client.send_command("show ip route")
    except Exception as exc:
        logger.warning("[%s] Gateway command failed: %s", client.ip, exc)
        return ""

    if not raw:
        return ""

    # Line: "Gateway of last resort is 10.0.0.1 to network 0.0.0.0"
    m = re.search(r"Gateway of last resort is ([\d.]+)", raw, re.IGNORECASE)
    if m:
        gw = m.group(1)
        logger.debug("[%s] Gateway: %s", client.ip, gw)
        return gw

    # Not configured
    if "not set" in raw.lower():
        logger.debug("[%s] Gateway not set.", client.ip)
        return "Not Set"

    return ""
