#!/usr/bin/env python3
"""Launch the TUI tracker dashboard."""

import asyncio
import os
import sys

from dotenv import load_dotenv
from player_tracker.tui import TrackerDashboard

from player_tracker.lock import TrackerLock

# Configure UTF-8 output for Windows console
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]


async def main() -> None:
    load_dotenv()

    # Get Steam ID from environment variable
    steam_id = os.getenv("STEAM_ID")
    if not steam_id:
        print("❌ STEAM_ID environment variable is required")
        print("Set it in your .env file or export it in your shell")
        sys.exit(1)

    # Acquire single-instance lock
    lock = TrackerLock(steam_id)
    try:
        lock.acquire()
    except RuntimeError as e:
        print(f"\n❌ {e}\n")
        sys.exit(1)

    try:
        # Run the TUI app
        app = TrackerDashboard(steam_id=steam_id, db_path="data/player_tracker.db")
        await app.run_async()
    finally:
        # Always release the lock
        lock.release()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
