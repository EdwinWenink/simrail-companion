#!/usr/bin/env python3
"""Test script to check stop types in journey data."""
import asyncio
import sys
from dotenv import load_dotenv
from simrail_tools_api import SimRailToolsClient

async def main():
    load_dotenv()

    if len(sys.argv) < 3:
        print("Usage: python test_stop_types.py <server_code> <train_number>")
        print("Example: python test_stop_types.py int1 4144")
        return

    server_code = sys.argv[1]
    train_number = sys.argv[2]

    client = SimRailToolsClient()

    print(f"Looking up train {train_number} on {server_code}...")
    journey_id = await client.find_journey_by_train_number(server_code, train_number)

    if not journey_id:
        print(f"❌ Train {train_number} not found on {server_code}")
        await client.close()
        return

    print(f"✓ Found journey: {journey_id}\n")

    # Get full journey
    journey = await client.get_journey(journey_id)
    if not journey:
        print("❌ Could not fetch journey details")
        await client.close()
        return

    events = journey.events
    print(f"Journey has {len(events)} events\n")
    print("=" * 120)
    print(f"{'Station':<35} {'Type':<12} {'Stop Type':<12} {'Scheduled':<20} {'Realtime':<20} {'Time Type':<12}")
    print("=" * 120)

    for event in events[:15]:  # Show first 15
        station = event.stopPlace.name
        event_type = event.type
        stop_type = event.stopType
        scheduled = event.scheduledTime
        realtime = event.realtimeTime
        time_type = event.realtimeTimeType

        print(f"{station:<35} {event_type:<12} {stop_type:<12} {scheduled:<20} {realtime:<20} {time_type:<12}")

    print("=" * 120)

    # Test delay calculation
    print("\n\nTesting delay calculation (upcoming only):")
    delays = await client.get_journey_delays(journey_id, upcoming_only=True)

    print(f"\nFound {len(delays)} upcoming events\n")
    print("=" * 100)
    print(f"{'Station':<35} {'Type':<12} {'Stop Type':<12} {'Delay':<10}")
    print("=" * 100)

    for delay in delays[:10]:
        station = delay.station_name
        event_type = delay.event_type
        stop_type = delay.stop_type
        delay_min = delay.delay_minutes

        print(f"{station:<35} {event_type:<12} {stop_type:<12} {delay_min:>6.1f}m")

    print("=" * 100)

    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
