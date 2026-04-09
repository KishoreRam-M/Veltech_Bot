import threading
import time
import torch
from server.config import MAX_SAFE_TEMP_C, THROTTLE_TEMP_C, THROTTLE_THREADS, EMERGENCY_THREADS, NUM_THREADS

_running = False

def _get_cpu_temp() -> float:
    try:
        import psutil
        temps = psutil.sensors_temperatures()
        if temps:
            for name in ("coretemp", "cpu_thermal", "k10temp", "zenpower"):
                if name in temps:
                    return max(t.current for t in temps[name])
            all_temps = []
            for entries in temps.values():
                all_temps.extend(t.current for t in entries)
            if all_temps:
                return max(all_temps)
    except Exception:
        pass
    try:
        import subprocess
        result = subprocess.run(
            ["wmic", "path", "Win32_PerfFormattedData_Counters_ThermalZoneInformation", "get", "Temperature"],
            capture_output=True, text=True, timeout=5,
        )
        for line in result.stdout.strip().split("\n")[1:]:
            val = line.strip()
            if val and val.isdigit():
                temp_k = int(val)
                temp_c = temp_k - 273.15
                if 20 < temp_c < 110:
                    return temp_c
    except Exception:
        pass
    return 0.0

def _monitor_loop():
    while _running:
        temp = _get_cpu_temp()
        if temp >= MAX_SAFE_TEMP_C:
            torch.set_num_threads(EMERGENCY_THREADS)
            print(f"[THERMAL] ⚠️ CPU {temp:.0f}°C — emergency throttle to {EMERGENCY_THREADS} threads")
        elif temp >= THROTTLE_TEMP_C:
            torch.set_num_threads(THROTTLE_THREADS)
            print(f"[THERMAL] ⚡ CPU {temp:.0f}°C — throttling to {THROTTLE_THREADS} threads")
        elif temp > 0:
            torch.set_num_threads(NUM_THREADS)
        time.sleep(10)

def start_thermal_monitor():
    global _running
    if _running:
        return
    _running = True
    t = threading.Thread(target=_monitor_loop, daemon=True)
    t.start()
    print("[THERMAL] Monitor started (daemon thread, 10s interval)")

def stop_thermal_monitor():
    global _running
    _running = False
