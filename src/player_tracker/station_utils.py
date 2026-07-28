"""Station-related utility functions."""

import logging

logger = logging.getLogger(__name__)


async def check_dispatcher_status(simrail_client, server_code: str, station_name: str) -> str:
    """Check if a station has a human or AI dispatcher.

    Args:
        simrail_client: SimRailClient instance for fetching station data
        server_code: Server code (e.g., "en1")
        station_name: Name of the station to check

    Returns:
        "👤" for human dispatcher
        "🤖" for AI dispatcher
        "" on error or if station not found
    """
    try:
        stations = await simrail_client.get_stations(server_code)

        for station in stations:
            if station["Name"] == station_name:
                dispatchers = station.get("DispatchedBy", [])
                if dispatchers and dispatchers[0].get("SteamId"):
                    return "👤"  # Human dispatcher
                return "🤖"  # AI dispatcher

        return "🤖"  # Default to AI if station not found
    except Exception as e:
        logger.debug("Could not check dispatcher status: %s", e)
        return ""
