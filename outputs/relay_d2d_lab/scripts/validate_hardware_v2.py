"""Compatibility entry point for the two-direction ESP32 bench check."""
import runpy
from pathlib import Path

if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).with_name("hardware_smoke.py")), run_name="__main__")
