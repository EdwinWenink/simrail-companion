import asyncio
import logging
import os
import sys
from dotenv import load_dotenv
from simrail_api import SimRailClient

# Configure UTF-8 output for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def main():
    load_dotenv()

    client = SimRailClient()

    # Get Steam ID from environment variable
    steam_id = os.getenv("STEAM_ID")
    if not steam_id:
        raise ValueError("STEAM_ID environment variable is required")

    print(f"Searching for player {steam_id} across all SimRail servers...\n")

    # Find player activity
    activity = await client.find_player(steam_id)

    if activity:
        print("=== Player Found ===")
        print(f"Server: {activity['server_name']} ({activity['server_code']})")
        print(f"Activity: {activity['activity_type'].upper()}")

        if activity['activity_type'] == 'train':
            print(f"\nTrain Information:")
            print(f"  Train Number: {activity['train_number']}")
            print(f"  Train Name: {activity['train_name']}")
            print(f"  Route: {activity['start_station']} -> {activity['end_station']}")
            print(f"  Run ID: {activity['run_id']}")

            print(f"\nRolling Stock ({len(activity['vehicles'])} vehicle(s)):")
            for idx, vehicle in enumerate(activity['vehicles'] or [], 1):
                print(f"  {idx}. {vehicle}")

            print(f"\nCurrent Status:")
            if activity['velocity'] is not None:
                print(f"  Speed: {activity['velocity']:.1f} km/h")

            if activity['signal_in_front']:
                print(f"\nNext Signal:")
                print(f"  Signal ID: {activity['signal_in_front']}")
                if activity['distance_to_signal'] is not None:
                    print(f"  Distance: {activity['distance_to_signal']:.0f} m")
                if activity['signal_speed_limit'] is not None:
                    print(f"  Speed Limit: {activity['signal_speed_limit']:.0f} km/h")
                else:
                    print(f"  Speed Limit: No limit")
        else:
            print(f"\nStation Information:")
            print(f"  Station: {activity['station_name']} ({activity['station_prefix']})")
    else:
        print("Player is not currently active on any server")

    print("\n=== All Active Servers ===")
    servers = await client.get_servers()
    for server in servers:
        status = "Active" if server.get("IsActive") else "Inactive"
        print(f"  [{status}] {server['ServerName']} ({server['ServerCode']}) - {server['ServerRegion']}")

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
