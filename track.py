#!/usr/bin/env python3
"""Quick launcher for SimRail tracking with mode selection."""

import os
import sys

if __name__ == "__main__":
    import argparse

    from dotenv import load_dotenv

    load_dotenv()

    parser = argparse.ArgumentParser(description="SimRail Session Tracker")
    parser.add_argument(
        "--mode",
        choices=["tui", "cli"],
        default="tui",
        help="Tracker mode: 'tui' for dashboard (default), 'cli' for logging output",
    )
    parser.add_argument(
        "--steam-id",
        help="Steam ID to track (overrides .env)",
    )
    parser.add_argument(
        "--db",
        default="data/player_tracker.db",
        help="Database path (default: data/player_tracker.db)",
    )

    args = parser.parse_args()

    steam_id: str | None = args.steam_id or os.getenv("STEAM_ID")
    if not steam_id:
        print("❌ Steam ID required. Set STEAM_ID in .env or use --steam-id flag")
        sys.exit(1)

    # At this point, steam_id is guaranteed to be a non-empty string
    steam_id_str: str = steam_id

    # Configure UTF-8 output for Windows
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

    if args.mode == "tui":
        # Launch TUI dashboard
        import asyncio

        from player_tracker.tui import TrackerDashboard

        from player_tracker.lock import TrackerLock

        lock = TrackerLock(steam_id_str)
        try:
            lock.acquire()
        except RuntimeError as e:
            print(f"\n❌ {e}\n")
            sys.exit(1)

        try:
            app = TrackerDashboard(steam_id=steam_id_str, db_path=args.db)
            asyncio.run(app.run_async())
        finally:
            lock.release()

    else:
        # Launch CLI tracker
        import asyncio
        import logging

        from player_tracker import PlayerTracker
        from player_tracker.lock import TrackerLock
        from player_tracker.summary import print_summary

        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"
        )

        lock = TrackerLock(steam_id_str)
        try:
            lock.acquire()
        except RuntimeError as e:
            print(f"\n❌ {e}\n")
            sys.exit(1)

        tracker = PlayerTracker(steam_id=steam_id_str, db_path=args.db, poll_interval=30)

        print("=" * 60)
        print(f"PLAYER TRACKER - Steam ID: {steam_id_str}")
        print("=" * 60)
        print(f"Polling interval: {tracker.poll_interval} seconds")
        print("Press Ctrl+C to stop and view stats")
        print("=" * 60)
        print()

        async def run_tracker():
            tracker_task = None
            try:
                tracker_task = asyncio.create_task(tracker.start())
                await tracker_task
            except (KeyboardInterrupt, asyncio.CancelledError):
                pass
            finally:
                print("\n\n" + "=" * 60)
                print("SHUTTING DOWN...")
                print("=" * 60)

                if tracker.running:
                    tracker.stop()

                if tracker_task and not tracker_task.done():
                    tracker_task.cancel()
                    try:
                        await asyncio.wait_for(tracker_task, timeout=2.0)
                    except (asyncio.TimeoutError, asyncio.CancelledError):
                        pass

                await asyncio.sleep(0.5)

                try:
                    print_summary(tracker.db, steam_id_str, session_limit=5)
                except Exception as e:
                    print(f"Could not display summary: {e}")

                try:
                    await tracker.close()
                except Exception as e:
                    print(f"Error during cleanup: {e}")

                lock.release()
                print("\n✅ Tracker stopped successfully\n")

        try:
            asyncio.run(run_tracker())
        except KeyboardInterrupt:
            pass
