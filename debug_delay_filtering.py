#!/usr/bin/env python3
"""
Debug script to inspect journey event filtering.
Shows realtimeTimeType values and how filtering works.
"""
import asyncio
import sys
from dotenv import load_dotenv
from simrail_api import SimRailClient
from simrail_tools_api import SimRailToolsClient


async def main():
    load_dotenv()

    if len(sys.argv) < 2:
        print("Usage: python debug_delay_filtering.py <steam_id>")
        print("Example: python debug_delay_filtering.py 76561198033647260")
        sys.exit(1)

    steam_id = sys.argv[1]

    simrail_client = SimRailClient()
    tools_client = SimRailToolsClient()

    print("=" * 100)
    print(f"JOURNEY EVENT FILTERING DEBUG - Steam ID: {steam_id}")
    print("=" * 100)
    print()

    # Find where the player is
    print("Looking for player activity...")
    activity = await simrail_client.find_player(steam_id)

    if not activity:
        print("❌ Player not found or offline")
        await simrail_client.close()
        await tools_client.close()
        return

    if activity["activity_type"] != "train":
        print(f"❌ Player is not on a train (activity: {activity['activity_type']})")
        await simrail_client.close()
        await tools_client.close()
        return

    server_code = activity["server_code"]
    train_number = activity["train_number"]

    print(f"✓ Found player on train {train_number} on server {server_code}")
    print()

    # Find the journey
    print("Looking up journey timetable...")
    journey_id = await tools_client.find_journey_by_train_number(server_code, train_number)

    if not journey_id:
        print(f"❌ No journey found for train {train_number}")
        await simrail_client.close()
        await tools_client.close()
        return

    print(f"✓ Found journey: {journey_id}")
    print()

    # Get full journey
    journey = await tools_client.get_journey(journey_id)

    if not journey or not journey.get("events"):
        print("❌ No events in journey")
        await simrail_client.close()
        await tools_client.close()
        return

    events = journey["events"]
    print(f"Journey has {len(events)} total events")
    print()

    # Analyze events
    print("=" * 100)
    print(f"{'#':<4} {'Station':<35} {'Type':<12} {'Sched':<8} {'Real':<8} {'TimeType':<12}")
    print("=" * 100)

    real_count = 0
    prediction_count = 0
    schedule_count = 0

    for i, event in enumerate(events, 1):
        station = event["stopPlace"]["name"]
        event_type = event["type"]
        time_type = event.get("realtimeTimeType", "MISSING")

        # Extract times
        sched_time = event.get("scheduledTime", "")
        real_time = event.get("realtimeTime", "")

        if "T" in sched_time:
            sched = sched_time.split("T")[1][:5]
        else:
            sched = sched_time[:5] if sched_time else "??:??"

        if "T" in real_time:
            real = real_time.split("T")[1][:5]
        else:
            real = real_time[:5] if real_time else "??:??"

        # Count types
        if time_type == "REAL":
            real_count += 1
            marker = "✓ (past)"
        elif time_type == "PREDICTION":
            prediction_count += 1
            marker = "🔮 (future)"
        elif time_type == "SCHEDULE":
            schedule_count += 1
            marker = "📅 (future)"
        else:
            marker = "❓"

        print(f"{i:<4} {station:<35} {event_type:<12} {sched:<8} {real:<8} {time_type:<12} {marker}")

    print("=" * 100)
    print()
    print(f"Summary:")
    print(f"  REAL (past events):        {real_count}")
    print(f"  PREDICTION (future):       {prediction_count}")
    print(f"  SCHEDULE (future):         {schedule_count}")
    print(f"  Total events:              {len(events)}")
    print()

    # Find last REAL event
    last_real_index = -1
    for i, event in enumerate(events):
        if event.get("realtimeTimeType") == "REAL":
            last_real_index = i

    expected_upcoming = len(events) - last_real_index - 1

    # Test filtering
    print("Testing filter (upcoming_only=True)...")
    print(f"  Last REAL event: #{last_real_index + 1} {events[last_real_index]['stopPlace']['name'] if last_real_index >= 0 else 'N/A'}")
    print(f"  Expected upcoming events: {expected_upcoming}")
    delays = await tools_client.get_journey_delays(journey_id, upcoming_only=True)
    print(f"  Actual events returned: {len(delays)}")
    print()

    if len(delays) != expected_upcoming:
        print(f"⚠️  WARNING: Expected {expected_upcoming} events but got {len(delays)}")
        print("   This means the filtering is not working correctly!")
    else:
        print("✅ Filtering is working correctly!")
        print()
        print("First 5 upcoming events:")
        for i, delay in enumerate(delays[:5], 1):
            print(f"  {i}. {delay['station_name']} ({delay['time_type']})")

    print()

    await simrail_client.close()
    await tools_client.close()


if __name__ == "__main__":
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    asyncio.run(main())
