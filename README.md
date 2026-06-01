# SimRail Steam API Client

Python module for retrieving Steam player data and statistics for SimRail.

## Features

- Fetch player profile information (username, avatar, etc.)
- Retrieve SimRail game statistics (distance, score, dispatcher time)
- Support for multiple Steam API keys with automatic rotation
- Built-in retry logic for failed requests
- Type hints for better IDE support

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for fast, reliable Python package management.

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Or install in development mode
uv sync --dev
```

## Configuration

Set your Steam API key(s) as an environment variable:

```bash
# Single key
export STEAM_API_KEY="your-steam-api-key"

# Multiple keys (JSON array)
export STEAM_API_KEY='["key1", "key2", "key3"]'
```

Get your Steam API key from: https://steamcommunity.com/dev/apikey

## Usage

```bash
# Run the example
uv run example.py

# Or activate the virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
python example.py
```

```python
from simrail_steam import SteamClient

# Initialize client
client = SteamClient()

# Get player profile
player = await client.get_player_summary("76561198012345678")
print(f"Player: {player['personaname']}")

# Get SimRail stats
simrail_stats = await client.get_simrail_stats("76561198012345678")
print(f"Distance: {simrail_stats['DISTANCE_M']} meters")
print(f"Score: {simrail_stats['SCORE']}")
print(f"Dispatcher Time: {simrail_stats['DISPATCHER_TIME']} minutes")
```

## Limitations

**Per-station stats are not available** through the Steam API. The Steam API only provides aggregate dispatcher time (`DISPATCHER_TIME`), not per-station breakdowns. To track per-station statistics, you need to monitor live player sessions via the SimRail multiplayer API (like the main simrail.pro backend does).

## SimRail Multiplayer API

The `simrail_api` module provides access to the SimRail multiplayer API for tracking live player activity:

```python
from simrail_api import SimRailClient

client = SimRailClient()

# Find where a player is currently active
activity = await client.find_player("76561198012345678")
if activity:
    if activity['activity_type'] == 'train':
        print(f"Driving train {activity['train_number']}")
    else:
        print(f"Dispatching at {activity['station_name']}")

# Get all active servers
servers = await client.get_servers()

# Get all trains on a server
trains = await client.get_trains("en1")

# Get all stations on a server
stations = await client.get_stations("en1")
```

Run the SimRail API example:
```bash
uv run example_simrail_api.py
```

## Delay Tracking

Track whether you're running on time using the SimRail Tools API:

```bash
# Show delay information for a specific train
uv run show_delays.py int1 6162

# Debug: List all available servers
uv run list_servers.py

# Debug: List all active trains on a server
uv run debug_journey.py int1

# Debug: Search for a specific train
uv run debug_journey.py int1 --train 6162

# The tracker automatically checks delays while monitoring
uv run example_tracker.py
```

The delay tracker shows:
- Current delay status (on time, early, or delayed)
- Next station with scheduled vs. expected times
- Whether the dispatcher is human (👤) or AI (🤖)
- Upcoming events with delay information
- Real-time vs. predicted times

## Single Player Tracker

The `player_tracker` module provides automatic session tracking for a single player:

```python
from player_tracker import PlayerTracker

tracker = PlayerTracker(
    steam_id="76561198012345678",
    db_path="player_tracker.db",
    poll_interval=30  # Check every 30 seconds
)

# Start tracking (runs continuously)
await tracker.start()

# Get aggregated stats
stats = tracker.get_stats()
print(f"Total distance: {stats['total_distance_meters']} meters")
print(f"Time by station: {stats['stations_by_name']}")

# Get recent sessions
train_sessions = tracker.get_recent_train_sessions(10)
station_sessions = tracker.get_recent_station_sessions(10)
```

Run the tracker example:
```bash
# Start tracking (automatically syncs Steam stats first, then tracks continuously)
uv run example_tracker.py

# Manually sync Steam stats without starting tracker
uv run sync_steam.py 76561198012345678

# View summary of tracked data anytime
uv run show_summary.py 76561198012345678

# Show only active sessions
uv run show_summary.py 76561198012345678 --active-only

# Customize number of recent sessions shown
uv run show_summary.py 76561198012345678 --sessions 20
```

**Features:**
- Automatically syncs Steam stats before tracking starts
- Stores Steam stats history (track progress over time)
- Automatically detects when player joins/leaves trains or stations
- Calculates distance and points per train session using Steam API
- Stores all sessions in SQLite database
- Provides aggregated statistics (total distance, time per station, time per train type)
- Tracks session history
- Comprehensive summary display with recent activity timeline
- Shows tracking coverage (% of Steam distance that's been tracked)

## SimRail App ID

SimRail uses Steam App ID: `1422130`

## Idea box

- When player is still offline, use `GET /sit-journeys/v2/by-playable-departure` to list some upcoming possible journeys.

