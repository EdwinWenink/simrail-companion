import asyncio
import logging
import os
from dotenv import load_dotenv
from simrail_steam import SteamClient

logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def main():
    # Load environment variables from .env file
    load_dotenv()

    # Initialize the Steam client
    client = SteamClient()

    # Get Steam ID from environment variable
    steam_id = os.getenv("STEAM_ID")
    if not steam_id:
        raise ValueError("STEAM_ID environment variable is required")

    print(f"Fetching data for Steam ID: {steam_id}\n")

    # Get player profile summary
    print("=== Player Summary ===")
    player = await client.get_player_summary(steam_id)
    if player:
        print(f"Username: {player['personaname']}")
        print(f"Profile URL: {player['profileurl']}")
        print(f"Avatar: {player['avatarfull']}")
        print(f"Country: {player.get('loccountrycode', 'N/A')}")
    else:
        print("Player not found or profile is private")

    print("\n=== SimRail Game Stats ===")
    # Get full player stats
    stats = await client.get_player_stats(steam_id)
    if stats:
        print(f"Game: {stats['gameName']}")
        print("\nStats:")
        for stat in stats['stats']:
            print(f"  {stat['name']}: {stat['value']}")

        print("\nAchievements:")
        for achievement in stats.get('achievements', []):
            status = "[X]" if achievement['achieved'] else "[ ]"
            print(f"  {status} {achievement['name']}")
    else:
        print("Stats not available (profile may be private or player hasn't played SimRail)")

    print("\n=== SimRail Stats (Simplified) ===")
    # Get simplified SimRail-specific stats
    simrail_stats = await client.get_simrail_stats(steam_id)
    if simrail_stats:
        print(f"Total Distance: {simrail_stats['DISTANCE_M']:,} meters ({simrail_stats['DISTANCE_M'] / 1000:.2f} km)")
        print(f"Total Score: {simrail_stats['SCORE']:,}")
        print(f"Dispatcher Time: {simrail_stats['DISPATCHER_TIME']:,} minutes ({simrail_stats['DISPATCHER_TIME'] / 60:.2f} hours)")
    else:
        print("SimRail stats not available")

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())