# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SimRail Companion is a Python toolkit for SimRail train simulation that provides:
- Steam API client for player profiles and statistics
- SimRail multiplayer API client for live server/train/station tracking
- SimRail Tools API client for journey details and vehicle composition
- Real-time TUI dashboard for tracking player sessions with live updates

The primary use case is running the TUI dashboard (`tui_tracker.py`) to continuously track and display a player's sessions in real-time (trains driven, stations dispatched, distance traveled, points earned, delays, vehicle composition, etc.).

## Commands

### Setup
```bash
# Install dependencies
uv sync

# Install dev dependencies
uv sync --dev
```

### Running
```bash
# TUI Dashboard - Real-time interactive tracker (DEFAULT INTERFACE)
uv run main.py

# View tracking summary
uv run scripts/show_summary.py <steam_id>

# Sync Steam stats manually
uv run scripts/sync_steam.py <steam_id>

# Show delay information
uv run scripts/show_delays.py <server_code> <train_number>

# Sync dispatch stations to database
uv run scripts/sync_dispatch_stations.py
```

### Testing
```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_double_headed.py -v

# Run with coverage
uv run pytest --cov=src
```

### Linting
```bash
# Format code
uv run ruff format .

# Lint
uv run ruff check .

# Type check
uv run pyright
```

## User Interface

### TUI Dashboard (`main.py`)

The main interface is a real-time terminal UI built with [Textual](https://textual.textualize.io/) that provides:

**Left Column:**
- **Session Panel**: Current active train/station with live stats (train number, route, vehicle, elapsed time, distance estimate)
- **Lifetime Stats Panel**: Aggregate statistics (sessions, distance, points, time)
- **Vehicle Composition Panel**: Detailed consist information (locomotives, EMUs, wagons, length, weight)

**Right Column:**
- **Recent Stations**: Last 10 station passages from current session with stop types
- **Next Station Board**: Arrivals and departures at the next upcoming station
- **Recent Sessions**: Last 10 completed train sessions with distance/points/duration

**Features:**
- Auto-refreshes every 5 seconds
- Keyboard shortcuts: `R` to refresh, `Q` to quit
- Color-coded panels with zebra-striped tables
- Handles single-instance locking (same as CLI tracker)
- Clean shutdown with session finalization

**Technical Notes:**
- Runs tracker in background asyncio task
- Uses reactive properties for efficient UI updates
- Queries SQLite database directly for historical data
- Enforces single-instance locking via PID file

## Architecture

### Source Layout (src/)

The codebase uses a `src/` layout with four main packages:

1. **`simrail_api/`** - SimRail multiplayer API client
   - Fetches live server data, trains, stations, player activity
   - Used to detect when player joins/leaves trains or stations

2. **`simrail_steam/`** - Steam API client
   - Retrieves player profiles and SimRail game statistics
   - Used to calculate distance/points earned per session via baseline comparison
   - Supports multiple API keys with automatic rotation

3. **`simrail_tools_api/`** - SimRail Tools API client
   - Provides journey details, timetables, vehicle composition
   - Fetches arrivals/departures boards for stations
   - Used for delay tracking and displaying train consist
   - **Important**: Supports double-headed locomotives and coupled EMUs

4. **`player_tracker/`** - Core session tracking
   - `tracker.py` - Main `PlayerTracker` class with polling loop
   - `database.py` - SQLite schema and queries
   - `composition_types.py` - Pydantic models for vehicle composition validation
   - `summary.py` - Display formatting
   - `formatting.py` - Shared formatting utilities (duration, distance, time, signals)
   - `station_utils.py` - Station-related utilities (dispatcher checking)
   - `lock.py` - Single-instance PID lock to prevent concurrent trackers
   - `tui.py` - Real-time Textual TUI dashboard with live updates
   - `sync_stations.py` - Helper to sync dispatch stations on first run

### Key Patterns

**Session Tracking Flow**:
1. Tracker polls SimRail API every N seconds to find player
2. When player joins a train:
   - Fetch current Steam stats as baseline
   - Fetch vehicle composition (includes locomotives, EMUs, wagons, weight, length)
   - Create train session in database with composition JSON
3. When player leaves train:
   - Fetch current Steam stats
   - Calculate `distance = current - baseline`
   - Store final distance/points in session

**Vehicle Composition Storage**:
- `composition_json` field stores complete vehicle data including:
  - `locomotives`: List of locomotive details (for quick access)
  - `emus`: List of EMU unit details (shorthand)
  - `vehicles`: Full list of ALL vehicles with types, weights, loads
  - Summary fields: `num_wagons`, `total_length`, `total_weight`
- Denormalized fields for SQL queries: `vehicle_summary`, `traction_name`, `num_locomotives`, `traction_type`

**Single-Instance Lock**:
- `TrackerLock` class uses PID file (`data/tracker_{steam_id}.lock`)
- Prevents multiple tracker instances from racing and ending each other's sessions
- Checks if PID is still running before claiming stale lock
- Windows-compatible via `tasklist` command

**State Management**:
- Tracker maintains in-memory state: `current_train_session_id`, `start_steam_distance`, etc.
- Helper `_clear_session_state_if_current(session_id)` only clears state if ending the current session
- Prevents clearing state when ending stale/interrupted sessions from previous runs

### Database Schema

**train_sessions** table:
- Basic: steam_id, server, train_number, train_name, route, timestamps
- Performance: distance_meters, points, baseline_distance, baseline_points
- Vehicle composition: vehicle_summary, traction_type, transport_type, traction_name, num_locomotives, num_wagons, total_vehicles, total_length, total_weight, composition_json
- `composition_json` includes transport details (category, line, label, max_speed, type) from journey API
- `transport_type` extracted from journey transport information (e.g., "PASSENGER", "FREIGHT")

**station_sessions** table:
- Dispatcher sessions: steam_id, station_name, station_prefix, point_id, timestamps
- `point_id` links to `dispatch_stations` table for reliable station identification

**train_station_passages** table:
- Stations passed during train sessions with stop_type (PASSENGER, TECHNICAL, NONE)
- Unique constraint on (train_session_id, station_name) to prevent duplicates

**steam_stats** table:
- Historical Steam stats snapshots

**dispatch_stations** table:
- Reference data for dispatch stations from SimRail Tools API
- Fields: id, name, point_id, last_updated, position_lat, position_lon, difficulty
- Automatically populated on first run of TUI or CLI tracker
- Can be manually synced with `uv run scripts/sync_dispatch_stations.py`
- Used to look up `point_id` when creating station sessions

## Important Constraints

1. **Steam API Limitations**:
   - Only provides aggregate stats (total distance, total score, total dispatcher time)
   - No per-session breakdown from Steam API itself
   - **Stats may be delayed and do not update in real-time**
   - Tracker retries 3 times with 2s delays to wait for Steam stats to update
   - If stats don't update within ~6 seconds, session records 0 distance/points
   - Profile must be public for stats to be accessible

2. **Double-Headed Locomotives**:
   - Use `vehicles.locomotives` property (not `vehicles[0]`)
   - Check `is_double_headed` before assuming single locomotive
   - Display all locomotives when multiple exist

3. **Race Conditions**:
   - Always use `TrackerLock` when running tracker
   - Only one tracker instance per steam_id allowed
   - Stale sessions from interrupted runs are automatically detected and closed

4. **Delay Tracking**:
   - Only works for trains with timetable data (not all trains have it)
   - Requires valid journey_id from SimRail Tools API
   - Shows next 3-5 stations with delay status

## Configuration

**Environment Variables** (`.env` file):
- `STEAM_ID` - Required for main tracker
- `STEAM_API_KEY` - Single key or JSON array `["key1", "key2"]` for rotation

**Database Location**:
- Default: `data/player_tracker.db`
- Configurable via `db_path` parameter

## Common Pitfalls

1. **Don't assume single locomotive** - Always use `vehicles.locomotives` list
2. **Don't run multiple tracker instances** - Use the PID lock
3. **Don't trust Steam stats for real-time tracking** - They may be delayed
4. **Don't use `vehicle` column** - It's been migrated to `vehicle_summary`
5. **Don't skip baseline stats** - Can't calculate distance without them
