"""Sync dispatch stations from SimRail Tools API to local database."""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from player_tracker.database import TrackerDatabase
from simrail_tools_api.client import SimRailToolsClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def sync_dispatch_stations(db_path: str = "data/player_tracker.db"):
    """Fetch all dispatch stations and store them in the database."""
    db = TrackerDatabase(db_path)
    client = SimRailToolsClient()

    try:
        logger.info("Fetching dispatch stations from SimRail Tools API...")
        stations = await client.fetch_all_dispatch_stations()

        logger.info("Storing %s station instances in database...", len(stations))
        for station in stations:
            db.upsert_dispatch_station(
                station_id=station["id"],
                name=station["name"],
                point_id=station["pointId"],
                last_updated=station["lastUpdated"],
                position_lat=station["position"]["latitude"],
                position_lon=station["position"]["longitude"],
                difficulty=station["difficulty"],
            )

        logger.info("✓ Sync complete!")

        # Show summary
        unique_stations = {s["name"] for s in stations}
        logger.info("Summary:")
        logger.info("  - Total station instances: %s", len(stations))
        logger.info("  - Unique stations: %s", len(unique_stations))

        # Show sample of unique stations with difficulty
        stations_by_name = {}
        for s in stations:
            name = s["name"]
            if name not in stations_by_name:
                stations_by_name[name] = s["difficulty"]

        logger.info("  - Sample (name: difficulty):")
        for name, diff in sorted(stations_by_name.items())[:10]:
            logger.info("    • %s: %s", name, diff)

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(sync_dispatch_stations())
