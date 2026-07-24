"""Real-time TUI dashboard for player tracking using Textual."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, ClassVar

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Label,
    Static,
)

from player_tracker import PlayerTracker
from player_tracker.database import TrackerDatabase

# Suppress verbose logging in TUI mode
logging.getLogger("simrail_api").setLevel(logging.WARNING)
logging.getLogger("simrail_steam").setLevel(logging.WARNING)
logging.getLogger("simrail_tools_api").setLevel(logging.WARNING)
logging.getLogger("player_tracker").setLevel(logging.WARNING)


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


class SessionPanel(Static):
    """Panel showing current active session."""

    session_info = reactive("No active session")

    def render(self) -> str:
        return self.session_info


class StatsPanel(Static):
    """Panel showing real-time statistics."""

    stats_text = reactive("")

    def render(self) -> str:
        return self.stats_text


class CompositionPanel(Static):
    """Panel showing vehicle composition."""

    composition_text = reactive("No composition data")

    def render(self) -> str:
        return self.composition_text


class DispatcherStationsPanel(Static):
    """Panel showing dispatcher station statistics."""

    stations_text = reactive("No dispatcher data")

    def render(self) -> str:
        return self.stations_text


class UpcomingStationsPanel(Static):
    """Panel showing upcoming stations with delays."""

    upcoming_text = reactive("No upcoming station data")

    def render(self) -> str:
        return self.upcoming_text


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
        for station in stations[-10:]:  # Show last 10 stations
            self.stations_table.add_row(
                station["station_name"],
                station["stop_type"],
                format_time(station["passed_at"]),
            )


class EventLogPanel(VerticalScroll):
    """Panel showing event log messages."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.log_lines: list[str] = []
        self.log_static = Static("")

    def compose(self) -> ComposeResult:
        yield self.log_static

    def add_log(self, message: str) -> None:
        """Add a log message with timestamp."""
        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
        self.log_lines.append(f"[{timestamp}] {message}")
        # Keep last 50 lines
        if len(self.log_lines) > 50:
            self.log_lines = self.log_lines[-50:]
        self.log_static.update("\n".join(self.log_lines))
        # Auto-scroll to bottom
        self.scroll_end(animate=False)


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
        self.sessions_table.add_columns("Train", "Vehicle", "Distance", "Time")
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

                self.sessions_table.add_row(
                    session["train_number"],
                    vehicle_display,
                    format_distance(session.get("distance_meters")),
                    format_duration(duration),
                )


class TrackerDashboard(App):
    """A Textual app for real-time SimRail session tracking."""

    CSS = """
    Screen {
        background: $surface;
    }

    #main-container {
        height: 100%;
        width: 100%;
    }

    #left-column {
        width: 40%;
        height: 100%;
    }

    #middle-column {
        width: 35%;
        height: 100%;
    }

    #right-column {
        width: 25%;
        height: 100%;
    }

    .panel {
        border: solid $primary;
        height: auto;
        margin: 1;
        padding: 1;
    }

    #session-panel {
        height: 12;
        background: $boost;
    }

    #stats-panel {
        height: 14;
        background: $panel;
    }

    #composition-panel {
        height: auto;
        background: $panel;
    }

    #dispatcher-stations-panel {
        height: auto;
        background: $panel;
    }

    #upcoming-stations-panel {
        height: 50%;
        background: $panel;
    }

    #passed-stations-panel {
        height: 15%;
        background: $panel;
    }

    #top-trains-panel {
        height: 25%;
        background: $panel;
    }

    #sessions-panel {
        height: 10%;
        background: $panel;
    }

    #event-log-panel {
        height: 100%;
        background: $panel;
    }

    #controls {
        height: auto;
        dock: bottom;
        background: $surface;
        padding: 1;
    }

    Button {
        margin: 0 1;
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
            with Vertical(id="left-column"):
                yield SessionPanel(id="session-panel", classes="panel")
                yield StatsPanel(id="stats-panel", classes="panel")
                yield CompositionPanel(id="composition-panel", classes="panel")
                yield DispatcherStationsPanel(id="dispatcher-stations-panel", classes="panel")

            with Vertical(id="middle-column"):
                with Container(id="upcoming-stations-panel", classes="panel"):
                    yield Label("🚂 Upcoming Stations & Delays", id="upcoming-label")
                    yield UpcomingStationsPanel()

                with Container(id="passed-stations-panel", classes="panel"):
                    yield Label("📍 Passed Stations", id="passed-label")
                    yield PassedStationsPanel()

                with Container(id="top-trains-panel", classes="panel"):
                    yield Label("🚂 Top Trains (All-Time)", id="top-trains-label")
                    yield TopTrainsPanel()

                with Container(id="sessions-panel", classes="panel"):
                    yield Label("📜 Recent Sessions", id="sessions-label")
                    yield SessionsPanel()

            with Vertical(id="right-column"), Container(id="event-log-panel", classes="panel"):
                yield Label("📋 Event Log", id="log-label")
                yield EventLogPanel()

        with Horizontal(id="controls"):
            yield Button("Refresh [R]", id="refresh-btn", variant="primary")
            yield Button("Quit [Q]", id="quit-btn", variant="error")

    async def on_mount(self) -> None:
        """Start tracking when app starts."""
        self.title = f"SimRail Tracker - {self.steam_id}"
        self.sub_title = "Real-time Session Monitoring"

        # Initialize tracker and database
        self.tracker = PlayerTracker(steam_id=self.steam_id, db_path=self.db_path, poll_interval=30)
        self.db = TrackerDatabase(self.db_path)

        # Set up logging to event panel
        self._setup_event_logging()

        # Start tracker in background
        self.tracker_task = asyncio.create_task(self.tracker.start())

        # Start update loop
        self.update_task = asyncio.create_task(self.update_dashboard_loop())

        # Initial update
        await self.update_dashboard()
        self.log_event("✅ Tracker started")

    def _setup_event_logging(self) -> None:
        """Set up logging handler to pipe tracker logs to event panel."""

        class TUILogHandler(logging.Handler):
            def __init__(self, dashboard: TrackerDashboard):
                super().__init__()
                self.dashboard = dashboard

            def emit(self, record: logging.LogRecord) -> None:
                try:
                    msg = self.format(record)
                    # Filter out verbose messages
                    if "Checking activity" in msg or "still on train" in msg:
                        return
                    self.dashboard.log_event(msg)
                except Exception as e:
                    # Suppress - logging to UI is non-critical
                    logging.getLogger(__name__).debug("Log emit error: %s", e)

        # Add handler to player_tracker logger
        tracker_logger = logging.getLogger("player_tracker")
        tracker_logger.setLevel(logging.INFO)
        handler = TUILogHandler(self)
        handler.setFormatter(logging.Formatter("%(message)s"))
        tracker_logger.addHandler(handler)

    def log_event(self, message: str) -> None:
        """Add an event to the log panel."""
        try:
            event_log = self.query_one(EventLogPanel)
            event_log.add_log(message)
        except Exception as e:
            # Ignore if panel not ready yet
            logging.getLogger(__name__).debug("Log event error: %s", e)

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
                logging.getLogger(__name__).debug("Update error: %s", e)

    async def update_dashboard(self) -> None:
        """Update all dashboard panels with current data."""
        if not self.tracker or not self.db:
            return

        # Update session panel
        session_panel = self.query_one("#session-panel", SessionPanel)
        active_train = self.db.get_active_train_session(self.steam_id)
        active_station = self.db.get_active_station_session(self.steam_id)

        if active_train:
            joined = datetime.fromisoformat(active_train["joined_at"])
            elapsed = (datetime.now(timezone.utc) - joined).total_seconds()

            # Calculate real-time distance estimate
            current_distance = 0
            if (
                self.tracker.start_steam_distance
                and active_train.get("baseline_distance") is not None
            ):
                current_distance = (
                    self.tracker.start_steam_distance - active_train["baseline_distance"]
                )

            session_text = f"""🚂 DRIVING TRAIN {active_train["train_number"]}

Train: {active_train["train_name"]}
Route: {active_train["start_station"]} → {active_train["end_station"]}
Server: {active_train["server_name"]}
Vehicle: {active_train.get("vehicle_summary", "Unknown")}

Elapsed: {format_duration(elapsed)}
Distance: {format_distance(current_distance)} (live estimate)"""

            session_panel.session_info = session_text

        elif active_station:
            joined = datetime.fromisoformat(active_station["joined_at"])
            elapsed = (datetime.now(timezone.utc) - joined).total_seconds()

            session_text = f"""📍 DISPATCHING STATION

Station: {active_station["station_name"]} ({active_station["station_prefix"]})
Server: {active_station["server_name"]}

Elapsed: {format_duration(elapsed)}"""

            session_panel.session_info = session_text
        else:
            session_panel.session_info = """⚪ NO ACTIVE SESSION

Player is offline or not in a train/station."""

        # Update stats panel
        stats_panel = self.query_one("#stats-panel", StatsPanel)
        stats = self.db.get_stats(self.steam_id)

        # Get Steam baseline stats for comparison
        latest_steam = self.db.get_latest_steam_stats(self.steam_id)

        stats_text = "📊 LIFETIME STATISTICS\n\n"

        # Steam baseline (if available)
        if latest_steam:
            steam_distance_km = latest_steam["total_distance_meters"] / 1000
            steam_points = latest_steam["total_score"]
            stats_text += f"Steam Total: {steam_distance_km:,.1f} km, {steam_points:,} pts\n\n"

        # Calculate coverage percentage first
        coverage_str = ""
        if latest_steam and latest_steam["total_distance_meters"] > 0:
            coverage = (
                stats["total_distance_meters"] / latest_steam["total_distance_meters"]
            ) * 100
            coverage_str = f" ({coverage:.1f}% coverage)"

        # Tracked stats
        stats_text += f"Train Sessions: {stats['train_sessions']}\n"
        stats_text += f"Tracked: {format_distance(stats['total_distance_meters'])}{coverage_str}\n"
        stats_text += f"Points: {stats['total_points']:,}\n"
        stats_text += f"Driving: {format_duration(stats['total_train_time_seconds'])}\n"
        stats_text += f"Dispatching: {format_duration(stats['total_dispatcher_time_seconds'])}"

        stats_panel.stats_text = stats_text

        # Update composition panel
        composition_panel = self.query_one("#composition-panel", CompositionPanel)
        if active_train and active_train.get("composition_json"):
            import json

            comp = json.loads(active_train["composition_json"])

            comp_text = "🚂 VEHICLE COMPOSITION\n\n"

            # Locomotives
            if comp.get("locomotives"):
                comp_text += "Locomotives:\n"
                for loc in comp["locomotives"]:
                    comp_text += f"  • {loc['displayName']}\n"

            # EMUs
            if comp.get("emus"):
                comp_text += "EMU Units:\n"
                for emu in comp["emus"]:
                    comp_text += f"  • {emu['displayName']}\n"

            # Summary stats
            comp_text += f"\nTotal Vehicles: {comp.get('total_vehicles', 0)}\n"
            comp_text += f"Wagons: {comp.get('num_wagons', 0)}\n"
            if comp.get("total_length"):
                comp_text += f"Length: {comp['total_length']:.0f} m\n"
            if comp.get("total_weight"):
                comp_text += f"Weight: {comp['total_weight'] / 1000:.1f} t"

            composition_panel.composition_text = comp_text
        else:
            composition_panel.composition_text = "No composition data available"

        # Update dispatcher stations panel
        dispatcher_panel = self.query_one("#dispatcher-stations-panel", DispatcherStationsPanel)
        if stats.get("stations_by_name"):
            # Sort by time spent
            sorted_stations = sorted(
                stats["stations_by_name"].items(), key=lambda x: x[1], reverse=True
            )

            dispatcher_text = "📍 TOP DISPATCHER STATIONS\n\n"
            for i, (station, time_seconds) in enumerate(sorted_stations[:8], 1):
                time_str = format_duration(time_seconds)
                # Truncate long station names
                station_display = station[:24] if len(station) <= 24 else station[:21] + "..."
                dispatcher_text += f"{i}. {station_display:<24} {time_str:>8}\n"

            dispatcher_panel.stations_text = dispatcher_text
        else:
            dispatcher_panel.stations_text = "No dispatcher data yet"

        # Update upcoming stations panel with delay info
        upcoming_panel = self.query_one(UpcomingStationsPanel)
        if active_train and self.tracker.current_journey_id:
            try:
                # Get delays from SimRail Tools API
                delays = await self.tracker.simrail_tools_client.get_journey_delays(
                    self.tracker.current_journey_id, upcoming_only=False
                )

                # Filter for upcoming only
                upcoming_delays = [d for d in delays if d.time_type != "REAL"][:5]

                if upcoming_delays:
                    lines = ["Next 5 Stations:\n"]
                    for i, delay in enumerate(upcoming_delays, 1):
                        # Format times
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
                            if delay_min > 0:
                                delay_str = f"+{delay_min:.0f}m 🔴"
                            else:
                                delay_str = f"{delay_min:.0f}m 🟢"
                        else:
                            delay_str = "on time ⚪"

                        # Time type
                        if delay.time_type.upper() == "SCHEDULE":
                            time_ind = "📅"
                        elif delay.time_type.upper() == "PREDICTION":
                            time_ind = "🔮"
                        else:
                            time_ind = ""

                        # Dispatcher for next station
                        dispatcher = ""
                        if i == 1 and delay.event_type != "PASS":
                            try:
                                stations = await self.tracker.simrail_client.get_stations(
                                    active_train["server_code"]
                                )
                                for station in stations:
                                    if station["Name"] == delay.station_name:
                                        dispatchers = station.get("DispatchedBy", [])
                                        if dispatchers and dispatchers[0].get("SteamId"):
                                            dispatcher = " 👤"
                                        else:
                                            dispatcher = " 🤖"
                                        break
                            except Exception as e:
                                # Non-critical - dispatcher status is optional
                                logging.getLogger(__name__).debug("Dispatcher check error: %s", e)

                        line = f"{i}. {stop_ind} {delay.station_name[:28]:<28}\n"
                        line += f"   {scheduled}→{realtime} {delay_str} {time_ind}{dispatcher}"

                        lines.append(line)

                    upcoming_panel.upcoming_text = "\n\n".join(lines)
                else:
                    upcoming_panel.upcoming_text = "No upcoming stations"
            except Exception as e:
                upcoming_panel.upcoming_text = f"Could not fetch delay info:\n{e}"
        else:
            upcoming_panel.upcoming_text = "No active train or no journey data"

        # Update passed stations panel
        if active_train:
            passed_panel = self.query_one(PassedStationsPanel)
            # Get station passages for current session
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

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "refresh-btn":
            await self.action_refresh()
        elif event.button.id == "quit-btn":
            await self.action_quit()

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
                logging.getLogger(__name__).debug("Cleanup error: %s", e)

        # Exit app
        self.exit()

    async def on_unmount(self) -> None:
        """Cleanup when app unmounts."""
        await self.shutdown()
