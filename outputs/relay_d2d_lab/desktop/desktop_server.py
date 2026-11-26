"""Keep the native Windows window and its own controller on the same lifetime."""
import argparse
import asyncio
import os
import sys
import threading
from pathlib import Path

import uvicorn


async def run(practice):
    os.environ["RELAY_LAB_PRACTICE"] = "1" if practice else "0"
    room_root = Path(__file__).resolve().parent.parent
    os.chdir(room_root)
    sys.path.insert(0, str(room_root))
    from lab.server import app, engine

    config = uvicorn.Config(app, host="127.0.0.1" if practice else "0.0.0.0",
                            port=8877 if practice else 8765, access_log=False)
    server = uvicorn.Server(config)
    owner_closed = threading.Event()

    def watch_window():
        try:
            sys.stdin.buffer.read(1)
        finally:
            owner_closed.set()

    threading.Thread(target=watch_window, daemon=True).start()

    async def stop_with_window():
        while not owner_closed.is_set():
            await asyncio.sleep(0.15)
        # A crashed window should still leave a complete run record.
        while engine.task and not engine.task.done():
            await asyncio.sleep(0.2)
        server.should_exit = True

    monitor = asyncio.create_task(stop_with_window())
    try:
        await server.serve()
    finally:
        monitor.cancel()
        await asyncio.gather(monitor, return_exceptions=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--practice", action="store_true")
    asyncio.run(run(parser.parse_args().practice))

