"""
SSH client abstraction using Netmiko.
Handles connection lifecycle, retries, and safe credential handling.
"""

from __future__ import annotations

import logging
from typing import Optional

from netmiko import ConnectHandler, NetmikoAuthenticationException, NetmikoTimeoutException
from netmiko.exceptions import NetmikoBaseException
from paramiko.ssh_exception import SSHException

from config import AppConfig

logger = logging.getLogger(__name__)


class SSHClient:
    """
    Manages a single SSH session to a Cisco device via Netmiko.

    Passwords are never logged.
    """

    def __init__(self, device: dict) -> None:
        self._ip: str = device["IP"].strip()
        self._username: str = device.get("Username", "").strip()
        self._password: str = device.get("Password", "")
        self._device_type: str = device.get("Device_Type", "cisco_ios").strip()
        self._connection: Optional[ConnectHandler] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def ip(self) -> str:
        return self._ip

    def connect(self) -> None:
        """
        Open SSH connection with retry logic.

        Raises
        ------
        NetmikoAuthenticationException  : bad credentials
        NetmikoTimeoutException          : connection timed out
        SSHException                     : SSH protocol error
        ConnectionRefusedError           : port 22 refused
        Exception                        : any other failure
        """
        conn_params = {
            "device_type": self._device_type,
            "host": self._ip,
            "username": self._username,
            "password": self._password,
            "timeout": AppConfig.SSH_TIMEOUT,
            "auth_timeout": AppConfig.SSH_AUTH_TIMEOUT,
            "banner_timeout": AppConfig.SSH_BANNER_TIMEOUT,
            "session_log": None,          # Never log sessions (contains creds)
            "fast_cli": False,
        }

        last_exc: Optional[Exception] = None
        for attempt in range(1, AppConfig.MAX_RETRIES + 1):
            try:
                logger.debug("SSH attempt %d/%d to %s", attempt, AppConfig.MAX_RETRIES, self._ip)
                self._connection = ConnectHandler(**conn_params)
                logger.info("SSH connected: %s", self._ip)
                return
            except NetmikoAuthenticationException as exc:
                logger.warning("Auth failed for %s: %s", self._ip, exc)
                raise  # No point retrying bad creds
            except (NetmikoTimeoutException, SSHException, OSError) as exc:
                logger.warning("Connection attempt %d failed for %s: %s", attempt, self._ip, exc)
                last_exc = exc

        raise last_exc or Exception(f"Connection failed after {AppConfig.MAX_RETRIES} attempts")

    def send_command(self, command: str, use_textfsm: bool = False) -> str:
        """
        Execute a show command and return the output string.

        Raises RuntimeError if not connected.
        """
        if not self._connection:
            raise RuntimeError(f"Not connected to {self._ip}")

        logger.debug("Running on %s: %s", self._ip, command)
        try:
            output = self._connection.send_command(
                command,
                read_timeout=AppConfig.COMMAND_TIMEOUT,
                use_textfsm=use_textfsm,
            )
            return output if isinstance(output, str) else str(output)
        except NetmikoBaseException as exc:
            logger.error("Command failed on %s [%s]: %s", self._ip, command, exc)
            raise

    def disconnect(self) -> None:
        """Safely close the SSH connection."""
        if self._connection:
            try:
                self._connection.disconnect()
                logger.debug("SSH disconnected: %s", self._ip)
            except Exception as exc:  # pylint: disable=broad-except
                logger.debug("Error during disconnect from %s: %s", self._ip, exc)
            finally:
                self._connection = None

    def __enter__(self) -> "SSHClient":
        self.connect()
        return self

    def __exit__(self, *_) -> None:
        self.disconnect()
