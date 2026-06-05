"""
Device discovery orchestrator.
Coordinates SSH connection and all data collection modules.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from netmiko import NetmikoAuthenticationException, NetmikoTimeoutException
from paramiko.ssh_exception import SSHException

from network.ssh_client import SSHClient
from network.cdp import CDPNeighbor, collect_cdp_neighbors
from network.vlan import collect_vlans
from network.svi import collect_svi_interfaces
from network.etherchannel import EtherChannel, collect_etherchannel
from network.gateway import collect_default_gateway

logger = logging.getLogger(__name__)


@dataclass
class DiscoveryResult:
    """Aggregated discovery data for a single device."""

    ip: str
    hostname: str = ""
    vlans: List[str] = field(default_factory=list)
    svi_interfaces: List[str] = field(default_factory=list)
    gateway: str = ""
    cdp_neighbors: List[CDPNeighbor] = field(default_factory=list)
    etherchannel: List[EtherChannel] = field(default_factory=list)
    status: str = "SUCCESS"
    failure_reason: str = ""
    timestamp: str = field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )


class DeviceDiscovery:
    """
    Runs the full discovery workflow for a single device.
    All exceptions are caught and recorded — never propagated.
    """

    def __init__(self, device: dict) -> None:
        self._device = device
        self._ip = device["IP"].strip()

    def run(self) -> DiscoveryResult:
        """Execute discovery and always return a DiscoveryResult."""
        result = DiscoveryResult(ip=self._ip)

        try:
            with SSHClient(self._device) as client:
                result.hostname = self._get_hostname(client)
                result.vlans = collect_vlans(client)
                result.svi_interfaces = collect_svi_interfaces(client)
                result.gateway = collect_default_gateway(client)
                result.cdp_neighbors = collect_cdp_neighbors(client)
                result.etherchannel = collect_etherchannel(client)

            logger.info(
                "[%s] Discovery SUCCESS — hostname=%s, VLANs=%d, CDPs=%d, POs=%d",
                self._ip,
                result.hostname,
                len(result.vlans),
                len(result.cdp_neighbors),
                len(result.etherchannel),
            )

        except NetmikoAuthenticationException:
            self._fail(result, "Authentication Failed")
        except NetmikoTimeoutException:
            self._fail(result, "SSH Timeout")
        except ConnectionRefusedError:
            self._fail(result, "Connection Refused")
        except SSHException as exc:
            self._fail(result, f"SSH Error: {exc}")
        except OSError as exc:
            # Covers DNS failures, unreachable hosts, etc.
            msg = str(exc)
            if "Name or service not known" in msg or "nodename nor servname" in msg:
                self._fail(result, "DNS Failure / Invalid Hostname")
            elif "timed out" in msg.lower():
                self._fail(result, "Connection Timeout")
            else:
                self._fail(result, f"Network Error: {msg}")
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("[%s] Unexpected discovery error: %s", self._ip, exc)
            self._fail(result, f"Unexpected Error: {type(exc).__name__}: {exc}")

        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_hostname(self, client: SSHClient) -> str:
        """
        Retrieve hostname.
        Tries Genie parser on 'show version', then falls back to
        'show running-config | include hostname'.
        """
        # Genie attempt
        try:
            raw = client.send_command("show version")
            hostname = self._genie_hostname(client.ip, raw)
            if hostname:
                return hostname
        except Exception:
            pass

        # Fallback
        try:
            raw = client.send_command("show running-config | include hostname")
            m = re.search(r"^hostname\s+(\S+)", raw, re.MULTILINE | re.IGNORECASE)
            if m:
                return m.group(1)
        except Exception as exc:
            logger.warning("[%s] Hostname fallback failed: %s", client.ip, exc)

        return client.ip  # Last resort

    def _genie_hostname(self, ip: str, raw: str) -> str:
        """Parse hostname from 'show version' via Genie."""
        try:
            from genie.libs.parser.iosxe.show_platform import ShowVersion
            from unittest.mock import MagicMock

            device = MagicMock()
            device.os = "iosxe"
            device.custom = {"abstraction": {"order": ["os"]}}

            parser = ShowVersion(device=device)
            parsed = parser.parse(output=raw)
            hostname = (
                parsed.get("version", {}).get("hostname", "")
                or parsed.get("hostname", "")
            )
            return str(hostname).strip()
        except Exception as exc:
            logger.debug("[%s] Genie hostname parse failed: %s", ip, exc)
            return ""

    @staticmethod
    def _fail(result: DiscoveryResult, reason: str) -> None:
        result.status = "FAILED"
        result.failure_reason = reason
        logger.warning("[%s] Discovery FAILED: %s", result.ip, reason)
