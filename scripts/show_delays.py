#!/usr/bin/env python3
"""
Show delay information for a train.
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from player_tracker.formatting import format_time
from player_tracker.station_utils import check_dispatcher_status
from simrail_api import SimRailClient
from simrail_tools_api import SimRailToolsClient


async def main():
    parser = argparse.ArgumentParser(description="Show train delay information")
    parser.add_argument("server_id", help="Server ID (e.g., 'int1')")
    parser.add_argument("train_number", help="Train number (e.g., '6162')")
    parser.add_argument(
        "--all-events", action="store_true", help="Show all events, not just upcoming"
    )

    args = parser.parse_args()

    tools_client = SimRailToolsClient()
    simrail_client = SimRailClient()

    print(
        f"Fetching delay information for train {args.train_number} on server {args.server_id}...\n"
    )

    delay_info = await tools_client.get_current_delay(
        args.server_id, args.train_number, include_station_name=True
    )

    if not delay_info:
        print(f"❌ Could not find train {args.train_number} on server {args.server_id}")
        print("   Train may not be active or server ID may be incorrect")
        await tools_client.close()
        await simrail_client.close()
        return

    # Function to get dispatcher status for a station
    async def get_dispatcher_display(station_name: str) -> str:
        """Get dispatcher display string for a station."""
        status = await check_dispatcher_status(simrail_client, args.server_id, station_name)
        if status == "👤":
            return "👤 Human"
        elif status == "🤖":
            return "🤖 AI"
        return "Unknown"

    print("=" * 80)
    print(f"DELAY INFORMATION - Train {args.train_number}")
    print("=" * 80)

    if delay_info["current_delay"]:
        current = delay_info["current_delay"]
        delay_min = current["delay_minutes"]

        print("\n🚂 Current Status:")
        if abs(delay_min) <= 1:
            print("   ✅ ON TIME")
        elif delay_min > 0:
            print(f"   ⚠️  DELAYED by {delay_min:.1f} minutes")
        else:
            print(f"   ⏩ EARLY by {abs(delay_min):.1f} minutes")

        print("\nNext Stop:")
        print(f"   Station: {current['station_name']}")
        dispatcher = await get_dispatcher_display(current["station_name"])
        print(f"   Dispatcher: {dispatcher}")
        print(f"   Event: {current['event_type'].title()}")
        print(f"   Scheduled: {format_time(current['scheduled_time'])}")
        print(f"   Expected: {format_time(current['realtime_time'])}")
        print(f"   Time Type: {current['time_type']}")

    print("\n📅 Upcoming Events:")
    print("-" * 95)
    print(
        f"{'Station':<30} {'Disp':<8} {'Type':<10} {'Scheduled':<10} {'Expected':<10} {'Delay':<15}"
    )
    print("-" * 95)

    for event in delay_info["upcoming_events"]:
        delay_min = event["delay_minutes"]

        if abs(delay_min) <= 1:
            delay_str = "On time"
        elif delay_min > 0:
            delay_str = f"+{delay_min:.1f} min"
        else:
            delay_str = f"{delay_min:.1f} min"

        # Truncate long station names
        station = (
            event["station_name"][:28] + ".."
            if len(event["station_name"]) > 30
            else event["station_name"]
        )

        # Get dispatcher type
        dispatcher = await get_dispatcher_display(event["station_name"])

        print(
            f"{station:<30} "
            f"{dispatcher:<8} "
            f"{event['event_type'][:8]:<10} "
            f"{format_time(event['scheduled_time']):<10} "
            f"{format_time(event['realtime_time']):<10} "
            f"{delay_str:<15}"
        )

    print(f"\nJourney ID: {delay_info['journey_id']}")
    print(f"Total Events: {delay_info['total_events']}")

    await tools_client.close()
    await simrail_client.close()


if __name__ == "__main__":
    # Configure UTF-8 output for Windows
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    asyncio.run(main())
