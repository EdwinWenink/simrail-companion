# SimRail Companion

Python toolkit for SimRail: Steam API client, multiplayer API tracking, and comprehensive player session monitoring.

## Features

This tool has two main purposes:

- Track detailed information about your SimRail multiplayer sessions to soothe your inner train nerd and show stats to your friends that they probably won't care about
- Provide live information about your trip 

### Tracking stuff

The Steam API only provides aggregate stats: total score, total distance driven, total dispatcher time.
These stats are used as a baseline for tracking total stats, but they do not provide detailed information about individual sessions.
When you run this tool while playing SimRail multiplayer, it will provided more detailed information about your sessions.

Features:

- Steam stats tracking
    * Stats history (track progress over time)
    * Shows tracking coverage (% of Steam distance that's been tracked with this tool)
- Detailed information about train sessions:
    * Detailed information about the train you are driving (train number, train type, train composition)
    * Distance driven per session
    * Points scored per session
    * Stations passed during train sessions with stop_type (PASSENGER, TECHNICAL, NONE)
- Detailed information about station sessions (time spent at each station, handy for tracking the 2h achievements)
- Detailed information about your trip schedule:
    * Current delay status (on time, early, or delayed)
    * Next station with scheduled vs. expected times
    * Whether the dispatcher at an upcoming station is human (👤) or AI (🤖)
    * Upcoming events with delay information
    * Real-time vs. predicted times
- Data is stored locally only in a SQLite database, make backups!

### Companion

When running this tool, you get live information about your trip that may be particularly nice if you run without HUD.

When you close your multiplayer session, the tool will show a summary of your session, including distance driven, points scored, and time spent at stations.
On top of that the companion will show a summary of your total stats, more detailed overview of your latest train sessions and dispatcher sessions, stats on which stations you pass most, and a top 10 of your most driven trains.

## Installation

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Or install in development mode
uv sync --dev
```

## Configuration

Find your Steam ID and get your Steam API key from: https://steamcommunity.com/dev/apikey

Set your Steam API key(s) as an environment variable in the `.env` file (see `.env.example`):

```bash
STEAM_ID="your-steam-id"  # Your Steam 64-bit ID (e.g., 76561198012345678)

# Single key
STEAM_API_KEY="your-steam-api-key"

# Multiple keys (JSON array)
STEAM_API_KEY='["key1", "key2", "key3"]'
```

## Repository Structure

```
simrail-companion/
├── main.py                       # Main player tracker (run this!)
├── src/                          # Source code packages
│   ├── simrail_api/              # SimRail multiplayer API client
│   ├── simrail_steam/            # Steam API client
│   ├── simrail_tools_api/        # SimRail Tools API client
│   └── player_tracker/           # Player tracking core
├── scripts/                      # Utility CLI tools
├── tools/                        # Debug/development utilities
├── data/                         # Database files
└── tests/                        # Unit tests
```

## Usage

**Important**: accurate tracking of distance and points requires that your session finishes before you shut down the tracker.
This is because the tracker needs to compare your Steam stats before and after the session to calculate the distance driven and points scored.
If you are playing a long session and your game crashes, you similarly lose points because SimRail only updates steam if the session is closed normally.

If you run the main script, everything is automatically tracked for your session and reported back to you.

```bash
uv run main.py  # Start the player tracker

# Or activate the virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
python main.py
```


## Standalone scripts

There are some standalone scripts that use some of the functionality without tracking your session.

```bash
# Show delay information for a specific train
uv run scripts/show_delays.py int1 6162

# List all available servers
uv run scripts/list_servers.py


# List all active trains on a server
uv run tools/debug_journey.py int1

# Search for a specific train
uv run tools/debug_journey.py int1 --train 6162

# Debug delay filtering
uv run tools/debug_delay_filtering.py [steam_id]

# Test stop types
uv run tools/test_stop_types.py int1 6162

# Manually sync Steam stats without starting tracker
uv run scripts/sync_steam.py 76561198012345678

# View summary of tracked data anytime
uv run scripts/show_summary.py 76561198012345678

# Show only active sessions
uv run scripts/show_summary.py 76561198012345678 --active-only

# Customize number of recent sessions shown
uv run scripts/show_summary.py 76561198012345678 --sessions 20
```

## SimRail App ID

SimRail uses Steam App ID: `1422130`

## Idea box

- When player is still offline, use `GET /sit-journeys/v2/by-playable-departure` to list some upcoming possible journeys.
