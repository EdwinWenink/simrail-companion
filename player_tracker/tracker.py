import asyncio
import logging
from typing import Optional
from datetime import datetime

from simrail_api import SimRailClient
from simrail_steam import SteamClient
from simrail_tools_api import SimRailToolsClient
from .database import TrackerDatabase

logger = logging.getLogger(__name__)


class PlayerTracker:
    def __init__(
        self,
        steam_id: str,
        db_path: str = "player_tracker.db",
        poll_interval: int = 30,
    ):
        self.steam_id = steam_id
        self.poll_interval = poll_interval
        self.simrail_client = SimRailClient()
        self.steam_client = SteamClient()
        self.simrail_tools_client = SimRailToolsClient()
        self.db = TrackerDatabase(db_path)
        self.running = False

        # Track current state
        self.current_train_session_id: Optional[str] = None
        self.current_station_session_id: Optional[str] = None
        self.start_steam_distance: Optional[int] = None
        self.start_steam_points: Optional[int] = None
        self.current_journey_id: Optional[str] = None
        self.last_next_station: Optional[str] = None  # Track last shown next station

    async def start(self):
        """Start tracking the player continuously."""
        # Sync Steam stats before starting
        await self.sync_steam_stats()

        self.running = True
        logger.info(f"Started tracking player {self.steam_id}")

        try:
            while self.running:
                try:
                    await self._check_player_activity()
                except asyncio.CancelledError:
                    # Task was cancelled, exit gracefully
                    logger.info("Tracker task cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error during tracking: {e}")

                # Sleep with cancellation check
                try:
                    await asyncio.sleep(self.poll_interval)
                except asyncio.CancelledError:
                    logger.info("Tracker sleep cancelled")
                    break
        finally:
            # Ensure any active sessions are closed
            logger.info("Cleaning up active sessions...")
            await self._end_active_sessions()

    def stop(self):
        """Stop tracking the player."""
        self.running = False
        logger.info("Stopped tracking")

    async def _check_player_activity(self):
        """Check current player activity and update sessions."""
        logger.debug(f"Checking activity for player {self.steam_id}")
        activity = await self.simrail_client.find_player(self.steam_id)

        if not activity:
            # Player is offline, end any active sessions
            logger.info(f"Player {self.steam_id} is offline")
            await self._end_active_sessions()
            return

        if activity["activity_type"] == "train":
            logger.debug(f"Player on train {activity['train_number']} ({activity['train_name']}) on server {activity['server_code']}")
            await self._handle_train_activity(activity)
        else:
            logger.debug(f"Player at station {activity['station_name']} on server {activity['server_code']}")
            await self._handle_station_activity(activity)

    async def _handle_train_activity(self, activity: dict):
        """Handle player driving a train."""
        # End any active station session
        if self.current_station_session_id:
            self.db.end_station_session(self.current_station_session_id)
            logger.info(f"Player switched from station to train - ended station session")
            self.current_station_session_id = None

        # Check if this is a new train session
        active_session = self.db.get_active_train_session(self.steam_id)

        if active_session and active_session["train_number"] == activity["train_number"]:
            # Same train, still active - check for delay updates periodically
            # (we check every poll, but the detailed output only shows when there are changes)
            logger.debug(f"Player still on train {activity['train_number']}")
            await self._check_delay_status(activity)
            return

        # End old train session if exists
        if active_session:
            logger.info(f"Player switched trains: {active_session['train_number']} -> {activity['train_number']}")
            await self._end_train_session(active_session["id"])

        # Start new train session
        await self._start_train_session(activity)

        # Show initial delay status and upcoming stations
        await self._check_delay_status(activity)

    async def _handle_station_activity(self, activity: dict):
        """Handle player dispatching at a station."""
        # End any active train session
        if self.current_train_session_id:
            logger.info(f"Player switched from train to station")
            await self._end_train_session(self.current_train_session_id)

        # Check if this is a new station session
        active_session = self.db.get_active_station_session(self.steam_id)

        if active_session and active_session["station_name"] == activity["station_name"]:
            # Same station, still active
            logger.debug(f"Player still at station {activity['station_name']}")
            return

        # End old station session if exists
        if active_session:
            logger.info(f"Player switched stations: {active_session['station_name']} -> {activity['station_name']}")
            self.db.end_station_session(active_session["id"])

        # Start new station session
        session_id = self.db.create_station_session(
            steam_id=self.steam_id,
            server_code=activity["server_code"],
            server_name=activity["server_name"],
            station_name=activity["station_name"],
            station_prefix=activity["station_prefix"],
        )
        self.current_station_session_id = session_id
        logger.info(
            f"📍 Started dispatching at {activity['station_name']} ({activity['station_prefix']}) on {activity['server_name']}"
        )

    async def _start_train_session(self, activity: dict):
        """Start a new train session and record starting Steam stats."""
        # Get current Steam stats
        logger.debug("Fetching Steam stats for session baseline")
        steam_stats = await self.steam_client.get_simrail_stats(self.steam_id)

        if steam_stats:
            self.start_steam_distance = steam_stats["DISTANCE_M"]
            self.start_steam_points = steam_stats["SCORE"]
            logger.debug(f"Baseline stats: {self.start_steam_distance}m, {self.start_steam_points} points")
        else:
            self.start_steam_distance = None
            self.start_steam_points = None
            logger.warning("Could not fetch Steam stats for baseline")

        # Get vehicle name (first vehicle in the list)
        vehicle = activity["vehicles"][0] if activity["vehicles"] else "Unknown"

        session_id = self.db.create_train_session(
            steam_id=self.steam_id,
            server_code=activity["server_code"],
            server_name=activity["server_name"],
            train_number=activity["train_number"],
            train_name=activity["train_name"],
            start_station=activity["start_station"],
            end_station=activity["end_station"],
            vehicle=vehicle,
        )
        self.current_train_session_id = session_id
        logger.info(
            f"🚂 Started driving train {activity['train_number']} ({activity['train_name']}) - {vehicle}"
        )
        logger.info(
            f"   Route: {activity['start_station']} → {activity['end_station']} on {activity['server_name']}"
        )

    async def _end_train_session(self, session_id: str):
        """End a train session and calculate distance/points."""
        logger.debug("Ending train session, calculating stats")

        # Clear the cached journey ID and last next station since we're leaving this train
        self.current_journey_id = None
        self.last_next_station = None

        if not self.start_steam_distance or not self.start_steam_points:
            # No starting stats, can't calculate difference
            self.db.end_train_session(session_id, 0, 0)
            logger.warning(
                f"⚠️  Ended train session with no distance/points (missing start stats)"
            )
            self.current_train_session_id = None
            return

        # Get current Steam stats
        logger.debug("Fetching Steam stats for session end")
        steam_stats = await self.steam_client.get_simrail_stats(self.steam_id)

        if not steam_stats:
            # Can't get current stats
            self.db.end_train_session(session_id, 0, 0)
            logger.warning(
                f"⚠️  Ended train session with no distance/points (missing end stats)"
            )
            self.current_train_session_id = None
            return

        # Calculate difference
        distance = max(0, steam_stats["DISTANCE_M"] - self.start_steam_distance)
        points = max(0, steam_stats["SCORE"] - self.start_steam_points)

        self.db.end_train_session(session_id, distance, points)
        logger.info(
            f"✅ Completed train session: {distance:,}m ({distance/1000:.2f}km), {points:,} points"
        )

        self.current_train_session_id = None
        self.start_steam_distance = None
        self.start_steam_points = None

    async def _end_active_sessions(self):
        """End any active sessions when player goes offline or tracker stops."""
        if self.current_train_session_id:
            logger.info("Ending active train session")
            await self._end_train_session(self.current_train_session_id)

        if self.current_station_session_id:
            self.db.end_station_session(self.current_station_session_id)
            logger.info("Ended active station session")
            self.current_station_session_id = None

    def get_stats(self) -> dict:
        """Get aggregated player statistics."""
        return self.db.get_stats(self.steam_id)

    def get_recent_train_sessions(self, limit: int = 10) -> list[dict]:
        """Get recent train sessions."""
        return self.db.get_train_sessions(self.steam_id, limit)

    def get_recent_station_sessions(self, limit: int = 10) -> list[dict]:
        """Get recent station sessions."""
        return self.db.get_station_sessions(self.steam_id, limit)

    async def _check_delay_status(self, activity: dict):
        """Check and log delay status for current train."""
        try:
            server_code = activity["server_code"]
            journey_id = self.current_journey_id

            # If we don't have the journey ID cached, find it
            if not journey_id:
                logger.info(f"Looking up timetable for train {activity['train_number']}...")
                journey_id = await self.simrail_tools_client.find_journey_by_train_number(
                    server_code, activity["train_number"]
                )
                if journey_id:
                    self.current_journey_id = journey_id
                    logger.info(f"✓ Found timetable (journey {journey_id[:8]}...)")
                else:
                    logger.info(
                        f"⚠️  No timetable data available for train {activity['train_number']} "
                        f"(may be a bot train or timetable not yet available)"
                    )
                    return

            # Get upcoming delays (filters out past events using realtimeTimeType)
            delays = await self.simrail_tools_client.get_journey_delays(journey_id, upcoming_only=True)

            if not delays:
                logger.info("⚠️  No upcoming stations in timetable (journey may have ended)")
                return

            # Check if next station changed since last poll
            next_station = delays[0].station_name
            if self.last_next_station == next_station:
                # Next station hasn't changed, don't spam the log
                logger.debug(f"Next station still {next_station}, skipping display")
                return

            # Update last shown station
            self.last_next_station = next_station

            # Show next 3-5 stations with their info
            upcoming_count = min(5, len(delays))
            logger.info(f"\n{'─' * 80}")
            logger.info(f"🚂 UPCOMING STATION EVENTS (next {upcoming_count} of {len(delays)}):")
            logger.info(f"{'─' * 80}")

            for i, delay in enumerate(delays[:upcoming_count], 1):
                station_name = delay.station_name
                event_type = delay.event_type
                stop_type = delay.stop_type
                delay_min = delay.delay_minutes
                time_type = delay.time_type

                # Debug: log the values to understand what we're getting
                logger.debug(f"Station: {station_name}, event_type: {event_type}, stop_type: {stop_type}")

                # Format datetime objects to HH:MM (server local time)
                try:
                    scheduled = delay.scheduled_time.strftime("%H:%M")
                    realtime = delay.realtime_time.strftime("%H:%M")
                except Exception as e:
                    logger.debug(f"Error formatting times: {e}")
                    scheduled = "??:??"
                    realtime = "??:??"

                # Determine if it's a stop based on stop_type
                if stop_type == "NONE":
                    # Pass-through station (no stop)
                    stop_indicator = "━━━"
                    action = "Pass"
                elif event_type == "ARRIVAL":
                    stop_indicator = "[A]"
                    action = "Arrive"
                elif event_type == "DEPARTURE":
                    stop_indicator = "[D]"
                    action = "Depart"
                else:
                    stop_indicator = "   "
                    action = event_type[:7]

                # Format delay with color
                if abs(delay_min) > 1:
                    if delay_min > 0:
                        delay_str = f"+{delay_min:.0f}m"
                        delay_icon = "🔴"
                    else:
                        delay_str = f"{delay_min:.0f}m"
                        delay_icon = "🟢"
                else:
                    delay_str = "on time"
                    delay_icon = "⚪"

                # Add time type indicator
                if time_type.upper() == "SCHEDULE":
                    time_indicator = "📅"  # Scheduled (no real-time data)
                elif time_type.upper() == "PREDICTION":
                    time_indicator = "🔮"  # Predicted
                elif time_type.upper() == "REAL":
                    time_indicator = "✓"  # Actual (shouldn't appear in upcoming)
                else:
                    time_indicator = ""

                # Check dispatcher only for next stop
                dispatcher_info = ""
                if i == 1 and event_type.lower() != "pass":
                    dispatcher_info = await self._check_dispatcher(server_code, station_name)
                    if dispatcher_info:
                        dispatcher_info = f" {dispatcher_info}"

                # Format line
                logger.info(
                    f"  {i}. {stop_indicator} {station_name:<32} "
                    f"{scheduled}→{realtime} "
                    f"{delay_icon}{delay_str:<8} "
                    f"{time_indicator}{dispatcher_info}"
                )

            logger.info(f"{'─' * 80}\n")

        except Exception as e:
            logger.error(f"Error fetching delay info: {type(e).__name__} - {e}")
            import traceback
            logger.debug(traceback.format_exc())

    async def _check_dispatcher(self, server_code: str, station_name: str) -> str:
        """Check if a station has a human dispatcher."""
        try:
            stations = await self.simrail_client.get_stations(server_code)

            for station in stations:
                if station["Name"] == station_name:
                    dispatchers = station.get("DispatchedBy", [])
                    if dispatchers and dispatchers[0].get("SteamId"):
                        return "👤"  # Human dispatcher
                    else:
                        return "🤖"  # AI dispatcher

            return "🤖"  # Default to AI if station not found
        except Exception as e:
            logger.debug(f"Could not check dispatcher: {e}")
            return ""

    async def sync_steam_stats(self):
        """Sync current Steam stats to database."""
        logger.info("Syncing Steam stats...")

        steam_stats = await self.steam_client.get_simrail_stats(self.steam_id)

        if not steam_stats:
            logger.warning("Could not fetch Steam stats for sync")
            return

        self.db.save_steam_stats(
            steam_id=self.steam_id,
            score=steam_stats["SCORE"],
            distance_meters=steam_stats["DISTANCE_M"],
            dispatcher_time_minutes=steam_stats["DISPATCHER_TIME"],
        )

        logger.info(
            f"✅ Steam stats synced: {steam_stats['DISTANCE_M']:,}m, "
            f"{steam_stats['SCORE']:,} points, "
            f"{steam_stats['DISPATCHER_TIME']} min dispatcher time"
        )

    async def close(self):
        """Close all connections."""
        await self.simrail_client.close()
        await self.steam_client.close()
        await self.simrail_tools_client.close()
