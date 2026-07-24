#!/usr/bin/env python3
"""
Display a summary of tracked player data from the database.
"""

import sys
import argparse
from player_tracker.database import TrackerDatabase
from player_tracker.summary import print_summary, print_active_sessions


def main():
    parser = argparse.ArgumentParser(description="Display tracked player data summary")
    parser.add_argument("steam_id", help="Steam ID to show summary for")
    parser.add_argument(
        "--db",
        default="data/player_tracker.db",
        help="Path to database file (default: data/player_tracker.db)",
    )
    parser.add_argument(
        "--sessions",
        type=int,
        default=10,
        help="Number of recent sessions to display (default: 10)",
    )
    parser.add_argument(
        "--active-only", action="store_true", help="Show only active sessions"
    )

    args = parser.parse_args()

    db = TrackerDatabase(args.db)

    if args.active_only:
        print_active_sessions(db, args.steam_id)
    else:
        print_summary(db, args.steam_id, session_limit=args.sessions)


if __name__ == "__main__":
    main()
