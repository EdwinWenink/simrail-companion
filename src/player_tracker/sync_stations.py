"""Helper to sync dispatch stations on demand."""

import logging

from player_tracker.database import TrackerDatabase
from simrail_tools_api.client import SimRailToolsClient

logger = logging.getLogger(__name__)


async def sync_dispatch_stations_if_empty(db: TrackerDatabase) -> bool:
    """Sync dispatch stations from API if the table is empty.

    Args:
        db: TrackerDatabase instance

    Returns:
        True if sync was performed, False if table already had data
    """
    if not db.is_dispatch_stations_empty():
        logger.debug("Dispatch stations already populated, skipping sync")
        return False

    logger.info("Dispatch stations table is empty, syncing from API...")
    client = SimRailToolsClient()

    try:
        stations = await client.fetch_all_dispatch_stations()
        logger.info("Fetched %s dispatch stations, storing in database...", len(stations))

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

        logger.info("✓ Dispatch stations synced successfully (%s stations)", len(stations))
        return True
    finally:
        await client.close()
