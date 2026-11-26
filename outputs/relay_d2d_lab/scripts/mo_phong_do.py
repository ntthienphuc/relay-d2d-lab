"""Start the installed room and open its dashboard when ready."""
import argparse
import os
import json
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path
import uvicorn

def main():
    parser = argparse.ArgumentParser(description="Relay Lab 2.5")
    parser.add_argument("--practice", action="store_true")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    os.chdir(Path(__file__).resolve().parents[1])
    port = 8877 if args.practice else 8765
    url = f"http://127.0.0.1:{port}"
    def status():
        try:
            with urllib.request.urlopen(url + "/api/status", timeout=1) as res:
                return json.load(res)
        except (OSError, ValueError):
            return None
    def open_dashboard():
        for _ in range(80):
            result = status()
            if result and result.get("version") == "2.5.1" and bool(result.get("practice")) == args.practice:
                webbrowser.open(url)
                return
            time.sleep(0.25)
    existing = status()
    if existing is not None:
        if existing.get("version") != "2.5.1" or bool(existing.get("practice")) != args.practice:
            raise SystemExit(f"Close the previous server on port {port} and start Relay Lab again.")
        if not args.no_browser:
            webbrowser.open(url)
        return
    os.environ["RELAY_LAB_PRACTICE"] = "1" if args.practice else "0"
    if not args.no_browser:
        threading.Thread(target=open_dashboard, daemon=True).start()
    print(f"Relay Lab 2.5  |  {url}  |  Ctrl+C to stop", flush=True)
    uvicorn.run("lab.server:app", host="127.0.0.1" if args.practice else "0.0.0.0", port=port, access_log=False)

if __name__ == "__main__":
    main()

