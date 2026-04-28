"""Thermal monitor — watches CPU temperature and adjusts PyTorch threads.

Temperature bands (all °C):
  < THROTTLE_TEMP_C  → restore normal operation (NUM_THREADS)
  ≥ THROTTLE_TEMP_C  → soft throttle (THROTTLE_THREADS)
  ≥ MAX_SAFE_TEMP_C  → emergency throttle (EMERGENCY_THREADS)

Thread counts are kept ≤ physical cores to prevent hyperthreading heat spikes.
Inter-op threads are always set to half of intra-op threads to reduce
OS scheduling contention.

The monitor runs as a daemon thread (10 s poll interval) so it is
automatically killed when the main process exits.
"""

import threading
import time
import logging

import torch

from server.config import (
    MAX_SAFE_TEMP_C,
    THROTTLE_TEMP_C,
    THROTTLE_THREADS,
    EMERGENCY_THREADS,
    NUM_THREADS,
)

log = logging.getLogger(__name__)

_running = False
_lock = threading.Lock()


# ── Temperature reading ───────────────────────────────────────────────────────

def _get_cpu_temp() -> float:
    """Return the highest CPU core temperature in °C, or 0.0 if unreadable."""
    # 1. psutil (Linux / macOS)
    try:
        import psutil  # type: ignore
        temps = psutil.sensors_temperatures()
        if temps:
            for name in ("coretemp", "cpu_thermal", "k10temp", "zenpower"):
                if name in temps:
                    return max(t.current for t in temps[name])
            all_temps = [t.current for entries in temps.values() for t in entries]
            if all_temps:
                return max(all_temps)
    except Exception:
        pass

    # 2. WMIC fallback (Windows) — parses Kelvin → Celsius
    try:
        import subprocess
        result = subprocess.run(
            [
                "wmic", "path",
                "Win32_PerfFormattedData_Counters_ThermalZoneInformation",
                "get", "Temperature",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        for line in result.stdout.strip().split("\n")[1:]:
            val = line.strip()
            if val and val.isdigit():
                temp_c = int(val) - 273.15
                if 20 < temp_c < 110:
                    return temp_c
    except Exception:
        pass

    return 0.0


# ── Thread-count helper ───────────────────────────────────────────────────────

def _apply_threads(n_intra: int, label: str) -> None:
    """Set intra-op and inter-op thread counts with a structured log line."""
    n_inter = max(1, n_intra // 2)
    torch.set_num_threads(n_intra)
    try:
        torch.set_num_interop_threads(n_inter)
    except RuntimeError:
        pass
    log.info("[THERMAL] %s → intra=%d  inter=%d threads", label, n_intra, n_inter)


# ── Monitor loop ──────────────────────────────────────────────────────────────

def _monitor_loop() -> None:
    last_band: str | None = None          # track band to avoid log spam

    while _running:
        temp = _get_cpu_temp()

        if temp >= MAX_SAFE_TEMP_C:
            band = "CRITICAL"
            if band != last_band:
                log.warning(
                    "[THERMAL] [CRITICAL] CPU %.0f°C — emergency throttle (%d threads)",
                    temp, EMERGENCY_THREADS,
                )
                _apply_threads(EMERGENCY_THREADS, "EMERGENCY")
                last_band = band

        elif temp >= THROTTLE_TEMP_C:
            band = "WARNING"
            if band != last_band:
                log.warning(
                    "[THERMAL] [WARNING] CPU %.0f°C — throttling to %d threads",
                    temp, THROTTLE_THREADS,
                )
                _apply_threads(THROTTLE_THREADS, "THROTTLE")
                last_band = band

        elif temp > 0:                    # temperature readable but in safe range
            band = "OK"
            if band != last_band:
                log.info("[THERMAL] CPU %.0f°C — nominal (%d threads)", temp, NUM_THREADS)
                _apply_threads(NUM_THREADS, "NOMINAL")
                last_band = band
        # else: temp == 0.0  → unreadable sensor, leave threads as-is

        time.sleep(10)


# ── Public API ────────────────────────────────────────────────────────────────

def start_thermal_monitor() -> None:
    global _running
    with _lock:
        if _running:
            return
        _running = True

    # Apply conservative thread baseline immediately on startup
    _apply_threads(NUM_THREADS, "STARTUP")

    t = threading.Thread(target=_monitor_loop, daemon=True, name="thermal-monitor")
    t.start()
    log.info("[THERMAL] Monitor started (daemon, 10 s interval)")


def stop_thermal_monitor() -> None:
    global _running
    with _lock:
        _running = False
