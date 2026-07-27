"""Real-time TUI dashboard for player tracking using Textual."""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, ClassVar

from pydantic import ValidationError
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.widgets import (
    DataTable,
    Footer,
    Header,
    Static,
)

from player_tracker import PlayerTracker
from player_tracker.composition_types import VehicleComposition
from player_tracker.database import TrackerDatabase

# Suppress verbose logging in TUI mode
logging.getLogger("simrail_api").setLevel(logging.WARNING)
logging.getLogger("simrail_steam").setLevel(logging.WARNING)
logging.getLogger("simrail_tools_api").setLevel(logging.WARNING)
logging.getLogger("player_tracker").setLevel(logging.WARNING)


logger = logging.getLogger(__name__)


def format_duration(seconds: float | None) -> str:
    """Format duration in seconds to human readable string."""
    if seconds is None:
        return "—"
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m {secs}s"


def format_distance(meters: int | None) -> str:
    """Format distance in meters to km."""
    if meters is None:
        return "—"
    return f"{meters / 1000:.2f} km"


def format_time(iso_time: str | None) -> str:
    """Format ISO timestamp to HH:MM:SS."""
    if not iso_time:
        return "—"
    try:
        dt = datetime.fromisoformat(iso_time)
        return dt.strftime("%H:%M:%S")
    except Exception:
        return "—"


class SessionPanel(VerticalScroll):
    """Panel showing current active session."""

    session_info = reactive("No active session")

    def compose(self) -> ComposeResult:
        yield Static(id="session-content")

    def watch_session_info(self, new_text: str) -> None:
        """Update the static content when text changes."""
        try:
            content = self.query_one("#session-content", Static)
            content.update(new_text)
        except Exception as e:
            logger.debug("Could not update session panel: %s", e)


class StatsPanel(Static):
    """Panel showing real-time statistics."""

    stats_text = reactive("")

    def render(self) -> str:
        return self.stats_text


class CompositionPanel(VerticalScroll):
    """Panel showing vehicle composition with expandable wagons."""

    composition_text = reactive("No composition data")
    wagons_expanded = reactive(False)
    _comp_data = None  # Store composition JSON

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.content_static = Static("")

    def compose(self) -> ComposeResult:
        yield self.content_static

    def on_click(self) -> None:
        """Toggle wagon expansion on click."""
        if self._comp_data and self._comp_data.get("num_wagons", 0) > 0:
            self.wagons_expanded = not self.wagons_expanded
            self._rebuild_display()

    def update_data(self, comp_data: dict | None) -> None:
        """Store composition data and build display."""
        self._comp_data = comp_data
        self._rebuild_display()

    def watch_composition_text(self, new_text: str) -> None:
        """Update the static content when text changes."""
        self.content_static.update(new_text)

    def _rebuild_display(self) -> None:
        """Rebuild the composition display with current expansion state."""
        if not self._comp_data:
            self.composition_text = "No composition data available"
            return

        comp = self._comp_data
        comp_text = ""

        # TRACTION (top level)
        if comp.get("locomotives"):
            for loc in comp["locomotives"]:
                comp_text += f"🚂 {loc['displayName']}\n"
        elif comp.get("emus"):
            for emu in comp["emus"]:
                comp_text += f"⚡ {emu['displayName']}\n"

        # WAGONS/CARRIAGES (top level summary with expandable hint)
        num_wagons = comp.get("num_wagons", 0)
        if num_wagons > 0:
            # Get wagon details (filter out locomotives and EMUs)
            wagons = [
                v
                for v in comp.get("vehicles", [])
                if v.get("type") not in ["LOCOMOTIVE", "ELECTRIC_MULTIPLE_UNIT"]
            ]

            comp_text += f"\n🚃 Wagons ({num_wagons})"
            if not self.wagons_expanded:
                comp_text += " [click to expand]"
            comp_text += "\n"

            if self.wagons_expanded and wagons:
                comp_text += "\n"
                for i, wagon in enumerate(wagons, 1):
                    name = wagon.get("displayName", wagon.get("name", "Unknown"))
                    weight = wagon.get("weight", 0) or 0
                    load_weight = wagon.get("loadWeight") or 0
                    load_type = wagon.get("load")

                    comp_text += f"  {i}. {name}\n"
                    comp_text += f"     Railcar: {weight:.1f}t"
                    if load_weight > 0:
                        comp_text += f", Load: {load_weight}t"
                        if load_type:
                            comp_text += f" ({load_type})"
                    comp_text += "\n"

        # TOTAL STATS (top level)
        comp_text += "\n"
        comp_text += f"Total: {comp.get('total_vehicles', 0)} vehicles\n"
        if comp.get("total_length"):
            comp_text += f"Length: {comp['total_length']:.0f} m\n"
        if comp.get("total_weight"):
            comp_text += f"Weight: {comp['total_weight']:.1f} t"

        self.composition_text = comp_text


class SignalStatePanel(VerticalScroll):
    """Panel showing current signal state and speed limits."""

    signal_text = reactive("No signal data")

    def compose(self) -> ComposeResult:
        yield Static(id="signal-content")

    def watch_signal_text(self, new_text: str) -> None:
        """Update the static content when text changes."""
        try:
            content = self.query_one("#signal-content", Static)
            content.update(new_text)
        except Exception as e:
            logger.debug("Could not update signal panel: %s", e)


class DispatcherStationsPanel(Static):
    """Panel showing dispatcher station statistics."""

    stations_text = reactive("No dispatcher data")

    def render(self) -> str:
        return self.stations_text


class UpcomingStationsPanel(VerticalScroll):
    """Panel showing upcoming stations with delays."""

    upcoming_text = reactive("No upcoming station data")

    def compose(self) -> ComposeResult:
        yield Static(id="upcoming-content")

    def watch_upcoming_text(self, new_text: str) -> None:
        """Update the static content when text changes."""
        try:
            content = self.query_one("#upcoming-content", Static)
            content.update(new_text)
        except Exception as e:
            logger.debug("Could not update upcoming stations: %s", e)


class PassedStationsPanel(VerticalScroll):
    """Panel showing recently passed station passages."""

    stations_table: DataTable

    def compose(self) -> ComposeResult:
        self.stations_table = DataTable()
        self.stations_table.add_columns("Station", "Type", "Time")
        self.stations_table.zebra_stripes = True
        yield self.stations_table

    def update_stations(self, stations: list[dict[str, Any]]) -> None:
        """Update the stations table."""
        self.stations_table.clear()
        for station in stations[:10]:  # Show first 10 (already ordered DESC by query)
            self.stations_table.add_row(
                station["station_name"],
                station["stop_type"],
                format_time(station["passed_at"]),
            )


class NextStationBoardPanel(VerticalScroll):
    """Panel showing arrivals/departures board for next station."""

    board_text = reactive("No next station data")

    def compose(self) -> ComposeResult:
        yield Static(id="board-content")

    def watch_board_text(self, new_text: str) -> None:
        """Update the static content when text changes."""
        try:
            content = self.query_one("#board-content", Static)
            content.update(new_text)
        except Exception as e:
            logger.debug("Could not update board: %s", e)


class TopTrainsPanel(VerticalScroll):
    """Panel showing top trains by time driven."""

    trains_table: DataTable

    def compose(self) -> ComposeResult:
        self.trains_table = DataTable()
        self.trains_table.add_columns("Train/Vehicle", "Distance", "Points", "Time")
        self.trains_table.zebra_stripes = True
        yield self.trains_table

    def update_trains(self, trains_by_type: dict[str, dict[str, Any]]) -> None:
        """Update the top trains table."""
        self.trains_table.clear()

        # Sort by time (descending)
        sorted_trains = sorted(
            trains_by_type.items(),
            key=lambda x: x[1]["time"],
            reverse=True,
        )

        for vehicle, data in sorted_trains[:10]:  # Show top 10
            distance_km = data["distance"] / 1000
            time_str = format_duration(data["time"])
            # Truncate long vehicle names
            vehicle_display = vehicle[:28] if len(vehicle) <= 28 else vehicle[:25] + "..."

            self.trains_table.add_row(
                vehicle_display,
                f"{distance_km:.1f} km",
                f"{data['points']:,}",
                time_str,
            )


class SessionsPanel(VerticalScroll):
    """Panel showing recent completed sessions."""

    sessions_table: DataTable

    def compose(self) -> ComposeResult:
        self.sessions_table = DataTable()
        self.sessions_table.add_columns("Train", "Vehicle", "Distance", "Points", "Time")
        self.sessions_table.zebra_stripes = True
        yield self.sessions_table

    def update_sessions(self, sessions: list[dict[str, Any]]) -> None:
        """Update the sessions table."""
        self.sessions_table.clear()
        for session in sessions[:5]:  # Show last 5 sessions (space constrained)
            if session["left_at"]:  # Only show completed sessions
                duration = None
                if session["joined_at"] and session["left_at"]:
                    start = datetime.fromisoformat(session["joined_at"])
                    end = datetime.fromisoformat(session["left_at"])
                    duration = (end - start).total_seconds()

                # Get vehicle name, truncate if needed
                vehicle = session.get("vehicle_summary", "Unknown")
                vehicle_display = vehicle[:20] if len(vehicle) <= 20 else vehicle[:17] + "..."

                # Format points
                points = session.get("points", 0) or 0
                points_str = f"{points:,}" if points > 0 else "0"

                self.sessions_table.add_row(
                    session["train_number"],
                    vehicle_display,
                    format_distance(session.get("distance_meters")),
                    points_str,
                    format_duration(duration),
                )


class TrackerDashboard(App):
    """A Textual app for real-time SimRail session tracking."""

    CSS = """
    Screen {
        background: $surface;
    }

    #main-container {
        height: 1fr;
        width: 1fr;
        border: solid white;
    }

    #left-column {
        width: 50%;
        height: 100%;
    }

    #middle-column {
        width: 50%;
        height: 100%;
    }

    .panel {
        border: solid $primary;
        height: auto;
        padding: 1 1;
    }

    #session-panel {
        height: 16%;
        background: $boost;
    }

    #signal-panel {
        height: 12%;
        background: $panel;
    }

    #composition-panel {
        height: 20%;
        background: $panel;
    }

    #upcoming-stations-panel {
        height: 20%;
        background: $panel;
    }

    #passed-stations-panel {
        height: 15%;
        background: $panel;
    }

    #next-station-board-panel {
        height: 17%;
        background: $panel;
    }

    #stats-panel {
        height: 10%;
        background: $panel;
    }

    #top-trains-panel {
        height: 40%;
        background: $panel;
    }

    #dispatcher-stations-panel {
        height: 30%;
        background: $panel;
    }

    #sessions-panel {
        height: 20%;
        background: $panel;
    }

    DataTable {
        height: 100%;
    }
    """

    BINDINGS: ClassVar = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
    ]

    def __init__(self, steam_id: str, db_path: str = "data/player_tracker.db"):
        super().__init__()
        self.theme = "textual-light"
        self.steam_id = steam_id
        self.db_path = db_path
        self.tracker: PlayerTracker | None = None
        self.db: TrackerDatabase | None = None
        self.tracker_task: asyncio.Task | None = None
        self.update_task: asyncio.Task | None = None

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(show_clock=True)
        yield Footer()

        with Container(id="main-container"), Horizontal():
            # LEFT COLUMN: ACTIVE SESSION - "Right Now"
            with Vertical(id="left-column"):
                session_panel = SessionPanel(id="session-panel", classes="panel")
                session_panel.border_title = "🚂 Current Session"
                yield session_panel

                signal_panel = SignalStatePanel(id="signal-panel", classes="panel")
                signal_panel.border_title = "🚦 Signal & Speed"
                yield signal_panel

                composition_panel = CompositionPanel(id="composition-panel", classes="panel")
                composition_panel.border_title = "🧩 Vehicle Composition"
                yield composition_panel

                with Container(id="upcoming-stations-panel", classes="panel") as upcoming_container:
                    upcoming_container.border_title = "🚉 Upcoming Stations & Delays"
                    yield UpcomingStationsPanel()

                with Container(id="passed-stations-panel", classes="panel") as passed_container:
                    passed_container.border_title = "📍 Passed Stations"
                    yield PassedStationsPanel()

                with Container(id="next-station-board-panel", classes="panel") as board_container:
                    board_container.border_title = "🚉 Next Station Board"
                    yield NextStationBoardPanel()

            # MIDDLE COLUMN: HISTORICAL STATS - "All-Time"
            with Vertical(id="middle-column"):
                stats_panel = StatsPanel(id="stats-panel", classes="panel")
                stats_panel.border_title = "📊 Lifetime Statistics"
                yield stats_panel

                with Container(id="top-trains-panel", classes="panel") as top_trains_container:
                    top_trains_container.border_title = "🚂 Top Traction (All-Time)"
                    yield TopTrainsPanel()

                dispatcher_panel = DispatcherStationsPanel(
                    id="dispatcher-stations-panel", classes="panel"
                )
                dispatcher_panel.border_title = "📍 Top Dispatcher Stations"
                yield dispatcher_panel

                with Container(id="sessions-panel", classes="panel") as sessions_container:
                    sessions_container.border_title = "📜 Recent Sessions"
                    yield SessionsPanel()

    async def on_mount(self) -> None:
        """Start tracking when app starts."""
        self.title = f"SimRail Tracker - {self.steam_id}"
        self.sub_title = "Real-time Session Monitoring"

        # Initialize tracker and database
        self.tracker = PlayerTracker(steam_id=self.steam_id, db_path=self.db_path, poll_interval=10)
        self.db = TrackerDatabase(self.db_path)

        # Start tracker in background
        self.tracker_task = asyncio.create_task(self.tracker.start())

        # Start update loop
        self.update_task = asyncio.create_task(self.update_dashboard_loop())

        # Initial update
        await self.update_dashboard()

    async def update_dashboard_loop(self) -> None:
        """Continuously update dashboard."""
        while True:
            try:
                await asyncio.sleep(5)  # Update every 5 seconds
                await self.update_dashboard()
            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log but continue - don't crash dashboard on data errors
                logger.debug("Update error: %s", e)

    def _get_transport_info_text(self, composition_json: str | None) -> str:
        """Extract transport info from composition JSON."""
        if not composition_json:
            return ""

        try:
            composition = json.loads(composition_json)
            transport = composition.get("transport")
            if not transport:
                return ""

            info_parts = []
            if transport_type := transport.get("type"):
                info_parts.append(f"Type: {transport_type}")
            if category_ext := transport.get("category_external"):
                info_parts.append(f"Category (external): {category_ext}")
            if line := transport.get("line"):
                info_parts.append(f"Line: {line}")
            if label := transport.get("label"):
                info_parts.append(f"Label: {label}")
            if max_speed := transport.get("max_speed"):
                info_parts.append(f"Max Speed: {max_speed} km/h")

            return "\n" + "\n".join(info_parts) if info_parts else ""
        except Exception as e:
            logger.debug("Could not parse transport info: %s", e)
            return ""

    def _format_difficulty_text(self, difficulty: int) -> str:
        """Format difficulty level with visual indicator."""
        stars = "⭐" * difficulty
        levels = {1: "Easy", 2: "Medium", 3: "Hard", 4: "Expert", 5: "Master"}
        label = levels.get(difficulty, f"Level {difficulty}")
        return f"\nDifficulty: {stars} {label}"

    async def _get_station_difficulty(self, server_code: str, station_name: str) -> str:
        """Fetch and format station difficulty level."""
        try:
            assert self.tracker
            stations = await self.tracker.simrail_client.get_stations(server_code)
            for station in stations:
                if station["Name"] == station_name:
                    if difficulty := station.get("DifficultyLevel", 0):
                        return self._format_difficulty_text(difficulty)
                    break
        except Exception as e:
            logger.debug("Could not fetch station difficulty: %s", e)
        return ""

    async def _update_session_panel(
        self, session_panel: SessionPanel, active_train: dict | None, active_station: dict | None
    ) -> None:
        """Update the current session panel."""
        if active_train:
            joined = datetime.fromisoformat(active_train["joined_at"])
            elapsed = (datetime.now(timezone.utc) - joined).total_seconds()
            transport_info = self._get_transport_info_text(active_train.get("composition_json"))

            session_text = f"""Train: {active_train["train_name"]} {active_train["train_number"]}
Route: {active_train["start_station"]} → {active_train["end_station"]}
Server: {active_train["server_name"]}
Vehicle: {active_train.get("vehicle_summary", "Unknown")}{transport_info}

Elapsed: {format_duration(elapsed)}"""
            session_panel.session_info = session_text

        elif active_station:
            joined = datetime.fromisoformat(active_station["joined_at"])
            elapsed = (datetime.now(timezone.utc) - joined).total_seconds()
            difficulty_text = await self._get_station_difficulty(
                active_station["server_code"], active_station["station_name"]
            )

            session_text = f"""Station: {active_station["station_name"]} ({active_station["station_prefix"]})
Server: {active_station["server_name"]}{difficulty_text}

Elapsed: {format_duration(elapsed)}"""
            session_panel.session_info = session_text
        else:
            session_panel.session_info = """Player is offline or not in a train/station."""

    def _get_signal_aspect(self, speed_limit: float | None) -> str:
        """Determine signal aspect based on speed limit."""
        if speed_limit is None:
            return "⚪ No data"
        if speed_limit == 0:
            return "🔴 Stop"
        if speed_limit in [40, 60]:
            return "🟠🟠 Slow"
        if speed_limit in [80, 100]:
            return "🟢🟠 Clear"
        if speed_limit >= 32767 or speed_limit > 100:
            return "🟢 vmax"
        return "⚪ Unknown"

    def _format_signal_distance(self, distance: float | None) -> str:
        """Format signal distance."""
        if distance is None:
            return "—"
        if distance >= 1000:
            return f"{distance / 1000:.2f} km"
        return f"{distance:.0f} m"

    def _format_signal_limit(self, speed_limit: float | None) -> str:
        """Format signal speed limit."""
        if speed_limit is None:
            return "—"
        if speed_limit == 32767:
            return "vmax"
        return f"{speed_limit:.0f} km/h"

    def _update_signal_panel(
        self, signal_panel: SignalStatePanel, player_activity: dict | None
    ) -> None:
        """Update the signal state panel."""
        if not player_activity or player_activity.get("activity_type") != "train":
            signal_panel.signal_text = "No active train\n"
            return

        velocity = player_activity.get("velocity")
        signal_in_front = player_activity.get("signal_in_front")
        distance_to_signal = player_activity.get("distance_to_signal")
        signal_speed_limit = player_activity.get("signal_speed_limit")

        signal_text = ""

        # Current speed with compliance check
        if velocity is not None:
            signal_text += f"Speed: {velocity:.0f} km/h"
            if signal_speed_limit is not None:
                if velocity > signal_speed_limit + 5:
                    signal_text += " ⚠️ OVERSPEEDING"
                elif velocity > signal_speed_limit:
                    signal_text += " ⚠️"
            signal_text += "\n"
        else:
            signal_text += "Speed: — km/h\n"

        signal_text += "\n"

        if signal_in_front:
            aspect = self._get_signal_aspect(signal_speed_limit)
            signal_text += f"Signal: {aspect}\n"
            signal_text += f"ID: {signal_in_front}\n"
            signal_text += f"Distance: {self._format_signal_distance(distance_to_signal)}\n"
            signal_text += f"Limit: {self._format_signal_limit(signal_speed_limit)}"
        else:
            signal_text += "No signal data"

        signal_panel.signal_text = signal_text

    def _update_stats_panel(
        self, stats_panel: StatsPanel, stats: dict, latest_steam: dict | None
    ) -> None:
        """Update the lifetime statistics panel."""
        stats_text = ""

        if latest_steam:
            steam_distance_km = latest_steam["total_distance_meters"] / 1000
            steam_points = latest_steam["total_score"]
            stats_text += f"Steam Total: {steam_distance_km:,.1f} km, {steam_points:,} pts\n\n"

        coverage_str = ""
        if latest_steam and latest_steam["total_distance_meters"] > 0:
            coverage = (
                stats["total_distance_meters"] / latest_steam["total_distance_meters"]
            ) * 100
            coverage_str = f" ({coverage:.1f}% coverage)"

        stats_text += f"Train Sessions: {stats['train_sessions']}\n"
        stats_text += f"Tracked: {format_distance(stats['total_distance_meters'])}{coverage_str}\n"
        stats_text += f"Points: {stats['total_points']:,}\n"
        stats_text += f"Driving: {format_duration(stats['total_train_time_seconds'])}\n"
        stats_text += f"Dispatching: {format_duration(stats['total_dispatcher_time_seconds'])}"

        stats_panel.stats_text = stats_text

    def _update_composition_panel(
        self, composition_panel: CompositionPanel, active_train: dict | None
    ) -> None:
        """Update the vehicle composition panel."""
        if not active_train or not active_train.get("composition_json"):
            composition_panel.update_data(None)
            return

        try:
            comp_data = json.loads(active_train["composition_json"])
            comp_model = VehicleComposition(**comp_data)
            composition_panel.update_data(comp_model.model_dump())
        except (json.JSONDecodeError, ValidationError) as e:
            logger.error("Invalid composition data: %s", e)
            composition_panel.update_data(None)

    def _update_dispatcher_panel(
        self, dispatcher_panel: DispatcherStationsPanel, stats: dict
    ) -> None:
        """Update the dispatcher stations panel."""
        if not stats.get("stations_by_name"):
            dispatcher_panel.stations_text = "No dispatcher data yet"
            return

        sorted_stations = sorted(
            stats["stations_by_name"].items(), key=lambda x: x[1], reverse=True
        )

        dispatcher_text = ""
        for i, (station, time_seconds) in enumerate(sorted_stations[:8], 1):
            time_str = format_duration(time_seconds)
            station_display = station[:24] if len(station) <= 24 else station[:21] + "..."
            dispatcher_text += f"{i}. {station_display:<24} {time_str:>8}\n"

        dispatcher_panel.stations_text = dispatcher_text

    async def _get_next_station_dispatcher_status(self, server_code: str, station_name: str) -> str:
        """Get dispatcher status for next station (👤 human or 🤖 AI)."""
        try:
            stations = await self.tracker.simrail_client.get_stations(server_code)
            for station in stations:
                if station["Name"] == station_name:
                    dispatchers = station.get("DispatchedBy", [])
                    if dispatchers and dispatchers[0].get("SteamId"):
                        return " 👤"
                    return " 🤖"
        except Exception as e:
            logger.debug("Dispatcher check error: %s", e)
        return ""

    async def _update_upcoming_stations_panel(
        self, upcoming_panel: UpcomingStationsPanel, active_train: dict | None
    ) -> None:
        """Update the upcoming stations panel with delay info."""
        if not active_train or not self.tracker.current_journey_id:
            logger.debug(
                "No upcoming stations: active_train=%s, journey_id=%s",
                bool(active_train),
                self.tracker.current_journey_id[:16] if self.tracker.current_journey_id else None,
            )
            upcoming_panel.upcoming_text = "No active train or no journey data"
            return

        try:
            logger.debug("Fetching delays for journey %s", self.tracker.current_journey_id[:16])
            delays = await self.tracker.simrail_tools_client.get_journey_delays(
                self.tracker.current_journey_id, upcoming_only=True
            )

            upcoming_delays = delays[:5]
            if not upcoming_delays:
                upcoming_panel.upcoming_text = "No upcoming stations"
                return

            lines = []
            for i, delay in enumerate(upcoming_delays, 1):
                scheduled = delay.scheduled_time.strftime("%H:%M")
                realtime = delay.realtime_time.strftime("%H:%M")

                # Stop indicator
                if delay.stop_type == "NONE":
                    stop_ind = "━━━"
                elif delay.event_type == "ARRIVAL":
                    stop_ind = "[A]"
                elif delay.event_type == "DEPARTURE":
                    stop_ind = "[D]"
                else:
                    stop_ind = "   "

                # Delay indicator
                delay_min = delay.delay_minutes
                if abs(delay_min) > 1:
                    delay_str = f"+{delay_min:.0f}m 🔴" if delay_min > 0 else f"{delay_min:.0f}m 🟢"
                else:
                    delay_str = "on time ⚪"

                # Time type indicator
                time_ind = {"SCHEDULE": "📅", "PREDICTION": "🔮"}.get(delay.time_type.upper(), "")

                # Dispatcher status for first station
                dispatcher = ""
                if i == 1 and delay.event_type != "PASS":
                    dispatcher = await self._get_next_station_dispatcher_status(
                        active_train["server_code"], delay.station_name
                    )

                line = f"{i}. {stop_ind} {delay.station_name[:28]:<28}\n"
                line += f"   {scheduled}→{realtime} {delay_str} {time_ind}{dispatcher}"
                lines.append(line)

            upcoming_panel.upcoming_text = "\n\n".join(lines)
        except Exception as e:
            logger.exception("Error fetching upcoming stations")
            upcoming_panel.upcoming_text = f"Could not fetch delay info:\n{e}"

    def _update_passed_stations_panel(
        self, passed_panel: PassedStationsPanel, active_train: dict | None
    ) -> None:
        """Update the passed stations panel."""
        if not active_train:
            return

        import sqlite3

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
            cursor = conn.execute(
                """
                SELECT station_name, stop_type, passed_at
                FROM train_station_passages
                WHERE train_session_id = ?
                ORDER BY passed_at DESC
                """,
                (active_train["id"],),
            )
            stations = cursor.fetchall()
            passed_panel.update_stations(stations)

    def _format_board_entry(self, entry: Any, prefix: str) -> str:
        """Format a single board entry (arrival or departure)."""
        time_str = entry.realtimeTime.strftime("%H:%M")
        delay_min = (entry.realtimeTime - entry.scheduledTime).total_seconds() / 60

        delay_indicator = ""
        if abs(delay_min) > 1:
            delay_indicator = f" +{delay_min:.0f}m" if delay_min > 0 else f" {delay_min:.0f}m"

        platform_info = ""
        if entry.realtimePassengerStop:
            platform_info = f" Pl.{entry.realtimePassengerStop.platform}"

        return f"{time_str}{delay_indicator} {entry.transport.category} {entry.transport.number}{platform_info}\n"

    async def _get_next_station_from_journey(self) -> tuple[str | None, str | None]:
        """Find next station point ID and name from journey events."""
        try:
            journey = await self.tracker.simrail_tools_client.get_journey(
                self.tracker.current_journey_id
            )
            if not journey or not journey.events:
                return None, None

            # Find last REAL event
            last_real_index = -1
            for i, event in enumerate(journey.events):
                if event.realtimeTimeType == "REAL":
                    last_real_index = i

            # Find next upcoming station
            for event in journey.events[last_real_index + 1 :]:
                if event.realtimeTimeType in ("PREDICTION", "SCHEDULE"):
                    return event.stopPlace.id, event.stopPlace.name

        except Exception as e:
            logger.debug("Error finding next station: %s", e)

        return None, None

    async def _update_next_station_board_panel(
        self, board_panel: NextStationBoardPanel, active_train: dict | None
    ) -> None:
        """Update the next station board panel."""
        if not active_train or not self.tracker.current_journey_id:
            board_panel.board_text = "No active train or journey"
            return

        try:
            next_station_point_id, next_station_name = await self._get_next_station_from_journey()

            if not next_station_point_id or not next_station_name:
                board_panel.board_text = "No upcoming stations in journey"
                return

            # Get server ID
            server_id = active_train["server_code"]
            if not server_id.count("-") >= 4:
                server_id = await self.tracker.simrail_tools_client.get_server_id_by_code(server_id)

            if not server_id:
                board_panel.board_text = "Could not resolve server ID"
                return

            # Fetch arrivals and departures
            departures = await self.tracker.simrail_tools_client.get_departures(
                server_id, next_station_point_id
            )
            arrivals = await self.tracker.simrail_tools_client.get_arrivals(
                server_id, next_station_point_id
            )

            # Format display
            board_text = f"Station: {next_station_name}\n\n"

            if departures:
                board_text += "🚂 Departures:\n"
                for dep in departures[:5]:
                    board_text += self._format_board_entry(dep, "🚂")

            board_text += "\n"

            if arrivals:
                board_text += "🚃 Arrivals:\n"
                for arr in arrivals[:5]:
                    board_text += self._format_board_entry(arr, "🚃")

            board_panel.board_text = board_text

        except Exception as e:
            logger.debug("Could not fetch next station board: %s", e)
            board_panel.board_text = "Error fetching board data"

    async def update_dashboard(self) -> None:
        """Update all dashboard panels with current data."""
        if not self.tracker or not self.db:
            return

        # Get shared data
        player_activity = self.tracker.current_activity
        active_train = self.db.get_active_train_session(self.steam_id)
        active_station = self.db.get_active_station_session(self.steam_id)
        stats = self.db.get_stats(self.steam_id)
        latest_steam = self.db.get_latest_steam_stats(self.steam_id)

        # Update all panels
        await self._update_session_panel(
            self.query_one("#session-panel", SessionPanel), active_train, active_station
        )

        self._update_signal_panel(
            self.query_one("#signal-panel", SignalStatePanel), player_activity
        )

        self._update_stats_panel(self.query_one("#stats-panel", StatsPanel), stats, latest_steam)

        self._update_composition_panel(
            self.query_one("#composition-panel", CompositionPanel), active_train
        )

        self._update_dispatcher_panel(
            self.query_one("#dispatcher-stations-panel", DispatcherStationsPanel), stats
        )

        await self._update_upcoming_stations_panel(
            self.query_one(UpcomingStationsPanel), active_train
        )

        self._update_passed_stations_panel(self.query_one(PassedStationsPanel), active_train)

        await self._update_next_station_board_panel(
            self.query_one(NextStationBoardPanel), active_train
        )

        # Update top trains panel
        top_trains_panel = self.query_one(TopTrainsPanel)
        if stats.get("trains_by_type"):
            top_trains_panel.update_trains(stats["trains_by_type"])
        else:
            top_trains_panel.trains_table.clear()

        # Update recent sessions panel
        sessions_panel = self.query_one(SessionsPanel)
        recent_sessions = self.db.get_train_sessions(self.steam_id, limit=5)
        sessions_panel.update_sessions(recent_sessions)

    async def action_refresh(self) -> None:
        """Manually refresh the dashboard."""
        await self.update_dashboard()

    async def action_quit(self) -> None:
        """Quit the application."""
        await self.shutdown()

    async def shutdown(self) -> None:
        """Clean shutdown of tracker and tasks."""
        # Cancel update task
        if self.update_task:
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass

        # Stop tracker
        if self.tracker:
            self.tracker.stop()

            # Cancel tracker task
            if self.tracker_task:
                self.tracker_task.cancel()
                try:
                    await asyncio.wait_for(self.tracker_task, timeout=2.0)
                except (asyncio.TimeoutError, asyncio.CancelledError):
                    pass

            # Close connections
            try:
                await self.tracker.close()
            except Exception as e:
                # Log but don't fail shutdown
                logger.debug("Cleanup error: %s", e)

        # Exit app
        self.exit()

    async def on_unmount(self) -> None:
        """Cleanup when app unmounts."""
        await self.shutdown()
