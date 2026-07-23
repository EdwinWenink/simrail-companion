import asyncio
import logging
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from player_tracker import PlayerTracker
from player_tracker.summary import print_summary

# Configure UTF-8 output for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)


async def main():
    load_dotenv()

    # Get Steam ID from environment variable
    steam_id = os.getenv("STEAM_ID")
    if not steam_id:
        raise ValueError("STEAM_ID environment variable is required")

    tracker = PlayerTracker(
        steam_id=steam_id,
        db_path="data/player_tracker.db",
        poll_interval=30  # Check every 30 seconds
    )

    print("=" * 60)
    print(f"PLAYER TRACKER - Steam ID: {steam_id}")
    print("=" * 60)
    print(f"Polling interval: {tracker.poll_interval} seconds")
    print("Press Ctrl+C to stop and view stats")
    print("=" * 60)
    print()

    tracker_task = None

    try:
        # Run tracker in background
        tracker_task = asyncio.create_task(tracker.start())

        # Wait for interrupt
        await tracker_task

    except (KeyboardInterrupt, asyncio.CancelledError):
        pass  # Normal exit, handle cleanup below

    finally:
        # Always run cleanup, even if interrupted
        print("\n\n" + "=" * 60)
        print("SHUTTING DOWN...")
        print("=" * 60)

        # Stop the tracker gracefully
        if tracker.running:
            tracker.stop()

        # Cancel the task if still running
        if tracker_task and not tracker_task.done():
            tracker_task.cancel()
            try:
                await asyncio.wait_for(tracker_task, timeout=2.0)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                pass  # Task cancelled or timed out, that's fine

        # Give time for any final operations to complete
        await asyncio.sleep(0.5)

        # Display summary
        try:
            print_summary(tracker.db, steam_id, session_limit=5)
        except Exception as e:
            print(f"Could not display summary: {e}")

        # Close connections
        try:
            await tracker.close()
        except Exception as e:
            print(f"Error during cleanup: {e}")

        print("\n✅ Tracker stopped successfully\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Catch any KeyboardInterrupt that escapes asyncio.run
        # (shouldn't happen with our improved handling, but just in case)
        pass
