import asyncio
import logging

import aiohttp

from .types import DelayInfo, Journey, JourneyEvent
from .vehicle_types import VehicleSequence

logger = logging.getLogger(__name__)


class SimRailToolsClient:
    BASE_URL = "https://apis.simrail.tools"
    DEFAULT_TIMEOUT = 10

    def __init__(self, timeout: int = DEFAULT_TIMEOUT):
        self.timeout = timeout
        self._server_cache = {}  # Cache server code -> ID mapping

    async def _fetch(self, endpoint: str) -> dict:
        url = f"{self.BASE_URL}/{endpoint}"
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with (
                aiohttp.ClientSession(timeout=timeout) as session,
                session.get(url) as response,
            ):
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientResponseError as e:
            logger.error("SimRail Tools API HTTP %s: %s - %s", e.status, e.message, url)
            raise
        except asyncio.TimeoutError:
            logger.error("SimRail Tools API timeout: %s", url)
            raise
        except Exception as e:
            logger.error(
                "SimRail Tools API request failed: %s - %s - %s",
                type(e).__name__,
                e,
                url,
            )
            raise

    async def get_server_id_by_code(self, server_code: str) -> str | None:
        """Convert server code (e.g., 'int1') to server UUID."""
        # Check cache first
        if server_code in self._server_cache:
            return self._server_cache[server_code]

        try:
            # Fetch all servers
            servers = await self._fetch("sit-servers/v2/")

            # Find matching server by code
            for server in servers:
                if server.get("code", "").lower() == server_code.lower():
                    server_id = server.get("id")
                    # Cache for future use
                    self._server_cache[server_code] = server_id
                    logger.debug("Resolved server code %s -> %s", server_code, server_id)
                    return server_id

            logger.warning("Server code '%s' not found", server_code)
            return None
        except Exception as e:
            logger.error("Error resolving server code: %s", e)
            return None

    async def find_journey_by_train_number(
        self, server_code_or_id: str, train_number: str
    ) -> str | None:
        """Find journey ID by train number on a specific server.

        Args:
            server_code_or_id: Server code (e.g., 'int1') or UUID
            train_number: Train number to search for
        """
        try:
            # Convert server code to UUID if needed
            if not server_code_or_id.count("-") >= 4:  # Simple UUID check
                server_id = await self.get_server_id_by_code(server_code_or_id)
                if not server_id:
                    logger.error("Could not resolve server code: %s", server_code_or_id)
                    return None
            else:
                server_id = server_code_or_id

            # Normalize train number (remove leading zeros, whitespace)
            normalized_search = train_number.strip().lstrip("0") or train_number

            # Search for active journeys
            data = await self._fetch(f"sit-journeys/v2/active?serverId={server_id}")

            logger.debug(
                "Searching for train %s among %s active journeys",
                train_number,
                len(data),
            )

            # Find matching train number
            for journey in data:
                journey_id = journey.get("journeyId") or journey.get("id")
                if not journey_id:
                    continue

                # Check if the summary already has the train number
                # (more efficient than fetching full details)
                if "transport" in journey:
                    number = journey["transport"].get("number", "")
                    normalized_number = number.strip().lstrip("0") or number

                    if normalized_number == normalized_search or number == train_number:
                        logger.debug("Found match in summary: %s -> %s", number, journey_id)
                        return journey_id

                # Fallback: fetch full journey and check all events
                # (skip if fetch fails - journey may have just ended)
                try:
                    full_journey = await self.get_journey(journey_id)
                    if full_journey and full_journey.events:
                        # Check if ANY event has this train number (not just the first)
                        for event in full_journey.events:
                            number = event.transport.number
                            normalized_number = number.strip().lstrip("0") or number

                            if normalized_number == normalized_search or number == train_number:
                                logger.debug("Found match in event: %s -> %s", number, journey_id)
                                return journey_id
                except Exception as e:
                    # Journey fetch failed, skip this one
                    logger.debug("Skipping journey %s: %s", journey_id, e)
                    continue

            logger.warning("No journey found for train number %s", train_number)
            return None
        except Exception as e:
            logger.error("Error finding journey by train number: %s", e)
            return None

    async def get_journey(self, journey_id: str) -> Journey | None:
        """Get full journey details including timetable."""
        try:
            data = await self._fetch(f"sit-journeys/v2/by-id/{journey_id}")
            return Journey(**data)
        except aiohttp.ClientResponseError as e:
            if e.status == 404:
                logger.warning("Journey %s not found (404) - may have ended", journey_id)
            else:
                logger.error("HTTP %s fetching journey %s: %s", e.status, journey_id, e.message)
            return None
        except Exception as e:
            logger.error("Error fetching journey %s: %s - %s", journey_id, type(e).__name__, e)
            return None

    def calculate_delay(self, event: JourneyEvent) -> DelayInfo:
        """Calculate delay for a journey event.

        Note: Times are in the server's local timezone (UTC+1 or UTC+2).
        We only calculate delay (difference between scheduled and realtime),
        not absolute time comparisons.
        """
        # Calculate delay - datetimes are already parsed by Pydantic
        delay_seconds = int((event.realtimeTime - event.scheduledTime).total_seconds())
        delay_minutes = delay_seconds / 60

        if delay_seconds > 60:  # More than 1 minute late
            status = "delayed"
        elif delay_seconds < -60:  # More than 1 minute early
            status = "early"
        else:
            status = "on_time"

        return DelayInfo(
            station_name=event.stopPlace.name,
            event_type=event.type,
            scheduled_time=event.scheduledTime,
            realtime_time=event.realtimeTime,
            delay_seconds=delay_seconds,
            delay_minutes=delay_minutes,
            status=status,
            time_type=event.realtimeTimeType,
            stop_type=event.stopType,
        )

    async def get_journey_delays(
        self, journey_id: str, upcoming_only: bool = True
    ) -> list[DelayInfo]:
        """Get delay information for all events in a journey.

        Note: Times from the API are in the server's local timezone (UTC+1 or UTC+2).
        We filter by finding the last REAL event and showing everything after that.
        - SCHEDULE = no realtime info available (could be past or future)
        - PREDICTION = future event (estimated based on current delay)
        - REAL = past event (already happened, recorded actual time)
        """
        journey = await self.get_journey(journey_id)
        if not journey:
            return []

        events = journey.events
        delays = []

        if upcoming_only:
            # Find the index of the last REAL event
            last_real_index = -1
            for i, event in enumerate(events):
                time_type = event.realtimeTimeType.upper()
                if time_type == "REAL":
                    last_real_index = i

            # Include all events after the last REAL event
            start_index = last_real_index + 1

            logger.debug(
                "Journey has %s events, last REAL at index %s, showing %s upcoming",
                len(events),
                last_real_index,
                len(events) - start_index,
            )

            for event in events[start_index:]:
                delays.append(self.calculate_delay(event))
        else:
            # Include all events
            for event in events:
                delays.append(self.calculate_delay(event))

        return delays

    async def get_current_delay(
        self,
        server_code_or_id: str,
        train_number: str,
        include_station_name: bool = False,
    ) -> dict | None:
        """Get current delay status for a train.

        Args:
            server_code_or_id: Server code (e.g., 'int1') or UUID
            train_number: Train number to search for
        """
        journey_id = await self.find_journey_by_train_number(server_code_or_id, train_number)
        if not journey_id:
            return None

        journey = await self.get_journey(journey_id)
        if not journey:
            return None

        delays = await self.get_journey_delays(journey_id, upcoming_only=True)

        if not delays:
            return None

        # Without knowing the server timezone, just use the first event as "next"
        next_event = delays[0] if delays else None
        next_station_name = next_event.station_name if next_event else None

        result = {
            "journey_id": journey_id,
            "current_delay": next_event,
            "upcoming_events": delays[:5],  # Next 5 events
            "total_events": len(journey.events),
        }

        if include_station_name and next_station_name:
            result["next_station_name"] = next_station_name

        return result

    async def get_vehicle_composition(self, journey_id: str) -> VehicleSequence | None:
        """Get the vehicle composition for a journey.

        Args:
            journey_id: Journey ID to get vehicles for

        Returns:
            VehicleSequence with all vehicles in the composition, or None if not found
        """
        try:
            data = await self._fetch(f"sit-vehicles/v2/by-journey/{journey_id}")
            return VehicleSequence(**data)
        except aiohttp.ClientResponseError as e:
            if e.status == 404:
                logger.warning("Vehicle composition for journey %s not found (404)", journey_id)
            else:
                logger.error(
                    "HTTP %s fetching vehicle composition for journey %s: %s",
                    e.status,
                    journey_id,
                    e.message,
                )
            return None
        except Exception as e:
            logger.error(
                "Error fetching vehicle composition for journey %s: %s - %s",
                journey_id,
                type(e).__name__,
                e,
            )
            return None

    async def close(self):
        pass
