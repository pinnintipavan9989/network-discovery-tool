"""
PyQt6 Worker — runs network discovery in a background thread,
emitting signals so the GUI stays responsive.
"""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from pathlib import Path
from typing import List

from PyQt6.QtCore import QThread, pyqtSignal

from network.discovery import DeviceDiscovery, DiscoveryResult
from excel.report_generator import ReportGenerator
from config import AppConfig

logger = logging.getLogger(__name__)


class DiscoveryWorker(QThread):
    """
    QThread that orchestrates multi-threaded device discovery.

    Signals
    -------
    sig_log(str, str)           : (message, level)
    sig_progress(int, int)      : (completed, total)
    sig_device_done(str, bool)  : (ip, success)
    sig_counters(int,int,int,int): (total, completed, failed, running)
    sig_finished(str)           : output file path
    sig_error(str)              : fatal error message
    """

    sig_log = pyqtSignal(str, str)
    sig_progress = pyqtSignal(int, int)
    sig_device_done = pyqtSignal(str, bool)
    sig_counters = pyqtSignal(int, int, int, int)
    sig_finished = pyqtSignal(str)
    sig_error = pyqtSignal(str)

    def __init__(
        self,
        devices: List[dict],
        output_dir: str,
        thread_count: int,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._devices = devices
        self._output_dir = Path(output_dir)
        self._thread_count = thread_count
        self._stop_flag = False
        self._results: List[DiscoveryResult] = []

        # Counters — guarded by the GIL for int ops (safe enough here)
        self._total = len(devices)
        self._completed = 0
        self._failed = 0
        self._running = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def stop(self) -> None:
        """Request graceful cancellation."""
        self._stop_flag = True
        self.sig_log.emit("Stop requested — finishing in-flight tasks…", "WARNING")
        logger.warning("Discovery stop requested by user.")

    # ------------------------------------------------------------------
    # Thread entry point
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Main execution — called by QThread.start()."""
        start_time = time.monotonic()
        self.sig_log.emit(
            f"Starting discovery for {self._total} device(s) "
            f"using {self._thread_count} thread(s).",
            "INFO",
        )
        self._emit_counters()

        try:
            self._run_discovery()
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Fatal error in discovery worker: %s", exc)
            self.sig_error.emit(str(exc))
            return

        # Write report
        try:
            output_path = self._write_report()
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Report generation failed: %s", exc)
            self.sig_error.emit(f"Report generation failed: {exc}")
            return

        elapsed = time.monotonic() - start_time
        self.sig_log.emit(
            f"Discovery complete in {elapsed:.1f}s — "
            f"{self._completed} succeeded, {self._failed} failed.",
            "SUCCESS",
        )
        self.sig_finished.emit(str(output_path))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _run_discovery(self) -> None:
        """Submit all devices to the thread pool and collect results."""
        with ThreadPoolExecutor(
            max_workers=self._thread_count,
            thread_name_prefix="nd_worker",
        ) as executor:
            future_map: dict[Future, dict] = {
                executor.submit(self._discover_one, dev): dev
                for dev in self._devices
            }

            self._running = len(future_map)
            self._emit_counters()

            for future in as_completed(future_map):
                if self._stop_flag:
                    # Cancel pending futures (best-effort)
                    for f in future_map:
                        f.cancel()
                    self.sig_log.emit("Discovery stopped by user.", "WARNING")
                    break

                device = future_map[future]
                self._running = max(0, self._running - 1)

                try:
                    result: DiscoveryResult = future.result()
                    self._results.append(result)
                    success = result.status == "SUCCESS"

                    if success:
                        self._completed += 1
                        self.sig_log.emit(
                            f"[SUCCESS] {device['IP']} — {result.hostname}", "SUCCESS"
                        )
                    else:
                        self._failed += 1
                        self.sig_log.emit(
                            f"[FAILED]  {device['IP']} — {result.failure_reason}", "ERROR"
                        )

                    self.sig_device_done.emit(device["IP"], success)

                except Exception as exc:  # pylint: disable=broad-except
                    self._failed += 1
                    logger.exception("Unexpected future error for %s: %s", device["IP"], exc)
                    self.sig_log.emit(
                        f"[ERROR]   {device['IP']} — Unexpected: {exc}", "ERROR"
                    )

                self.sig_progress.emit(self._completed + self._failed, self._total)
                self._emit_counters()

    def _discover_one(self, device: dict) -> DiscoveryResult:
        """Execute full discovery for a single device (runs in worker thread)."""
        self.sig_log.emit(f"[CONNECT] {device['IP']} — connecting…", "CONNECTING")
        discovery = DeviceDiscovery(device)
        return discovery.run()

    def _write_report(self) -> Path:
        """Generate the Excel report from collected results."""
        self._output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_path = self._output_dir / f"network_discovery_{timestamp}.xlsx"

        self.sig_log.emit(f"Generating report: {output_path.name}", "INFO")
        generator = ReportGenerator(self._results, output_path)
        generator.generate()
        self.sig_log.emit(f"Report saved: {output_path}", "SUCCESS")
        return output_path

    def _emit_counters(self) -> None:
        self.sig_counters.emit(
            self._total,
            self._completed,
            self._failed,
            self._running,
        )
