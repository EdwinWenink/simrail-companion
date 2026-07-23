#!/usr/bin/env python3
"""
Debug script to show all active trains and their journey info.
"""
import asyncio
import sys
import argparse
import json
from simrail_tools_api import SimRailToolsClient


async def main():
    parser = argparse.ArgumentParser(description="Debug journey matching")
    parser.add_argument(
        "server_id",
        help="Server ID (e.g., 'int1')"
    )
    parser.add_argument(
        "--train",
        help="Optional: specific train number to search for",
        default=None
    )

    args = parser.parse_args()

    client = SimRailToolsClient()

    print(f"Fetching active journeys on {args.server_id}...\n")

    try:
        # Resolve server code to UUID
        server_id = await client.get_server_id_by_code(args.server_id)
        if not server_id:
            print(f"❌ Could not find server with code: {args.server_id}")
            await client.close()
            return

        print(f"Resolved server code '{args.server_id}' to ID: {server_id}\n")

        data = await client._fetch(f"sit-journeys/v2/active?serverId={server_id}")

        print(f"Found {len(data)} active journeys:\n")
        print("=" * 100)
        print(f"{'Journey ID':<40} {'Train Number':<15} {'Category':<10} {'Line':<10} {'Driver':<15}")
        print("=" * 100)

        for journey in data:
            journey_id = journey.get("journeyId", journey.get("id", "N/A"))

            # Get transport info
            transport = journey.get("transport", {})
            number = transport.get("number", "N/A")
            category = transport.get("category", "N/A")
            line = transport.get("line", "N/A")

            # Get driver info
            driver = journey.get("liveData", {}).get("driver")
            driver_str = "Human" if driver else "AI/Bot"

            print(f"{journey_id:<40} {number:<15} {category:<10} {line:<10} {driver_str:<15}")

            # If searching for specific train, show more details
            if args.train and (args.train == number or args.train.lstrip('0') == number.lstrip('0')):
                print(f"\n{'*' * 100}")
                print(f"MATCH FOUND for train {args.train}:")
                print(json.dumps(journey, indent=2))
                print(f"{'*' * 100}\n")

        if args.train:
            print(f"\nSearching for train number: {args.train}")
            journey_id = await client.find_journey_by_train_number(args.server_id, args.train)
            if journey_id:
                print(f"✅ Found journey ID: {journey_id}")

                # Get full journey details
                full = await client.get_journey(journey_id)
                if full:
                    print(f"\nJourney has {len(full.get('events', []))} events")
                    print(f"\nFirst 5 events:")
                    for i, event in enumerate(full.get('events', [])[:5]):
                        print(f"  {i+1}. {event['stopPlace']['name']} - "
                              f"{event['transport']['category']} {event['transport']['number']} "
                              f"({event['type']})")
            else:
                print(f"❌ No journey found for train {args.train}")

    except Exception as e:
        print(f"Error: {e}")

    await client.close()


if __name__ == "__main__":
    # Configure UTF-8 output for Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    asyncio.run(main())
