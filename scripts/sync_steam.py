#!/usr/bin/env python3
"""
Sync Steam stats to the local database without starting the tracker.
"""

import asyncio
import argparse
from dotenv import load_dotenv
from player_tracker import PlayerTracker


async def main():
    parser = argparse.ArgumentParser(description="Sync Steam stats to local database")
    parser.add_argument("steam_id", help="Steam ID to sync stats for")
    parser.add_argument(
        "--db",
        default="data/player_tracker.db",
        help="Path to database file (default: data/player_tracker.db)",
    )

    args = parser.parse_args()

    load_dotenv()

    tracker = PlayerTracker(
        steam_id=args.steam_id,
        db_path=args.db,
    )

    print(f"Syncing Steam stats for {args.steam_id}...")
    await tracker.sync_steam_stats()
    print("Done!")

    await tracker.close()


if __name__ == "__main__":
    asyncio.run(main())
