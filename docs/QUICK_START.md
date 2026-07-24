# Quick Start Guide

## 🚀 Get Started in 3 Steps

### 1. Install Dependencies
```bash
uv sync
```

### 2. Configure Steam ID
Create a `.env` file:
```bash
STEAM_ID=76561198XXXXXXXXX
```

### 3. Launch the Dashboard
```bash
# Option A: TUI Dashboard (recommended)
uv run tui_tracker.py

# Option B: Unified launcher with mode selection
uv run track.py                    # defaults to TUI
uv run track.py --mode cli         # CLI mode
uv run track.py --mode tui         # explicit TUI mode

# Option C: Traditional CLI
uv run main.py
```

## 🎨 Dashboard Features

The TUI dashboard gives you a real-time view of your SimRail sessions:

### What You See

**Current Session (Live)**
- Train number, route, vehicle
- Elapsed time
- Distance estimate (updates from Steam API)

**Lifetime Statistics**
- Total sessions
- Total distance (km)
- Total points
- Driving time
- Dispatching time

**Vehicle Composition**
- All locomotives (handles double-headed)
- EMU units
- Wagon count
- Total length & weight

**Recent Activity**
- Last 10 station passages (current session)
- Last 10 completed sessions with stats

### Controls
- `R` - Refresh
- `Q` - Quit (saves session)
- Auto-updates every 5 seconds

## 📊 Viewing Historical Data

```bash
# View summary anytime (doesn't require tracker running)
uv run scripts/show_summary.py <steam_id>

# Show only active sessions
uv run scripts/show_summary.py <steam_id> --active-only

# Show more recent sessions
uv run scripts/show_summary.py <steam_id> --sessions 20
```

## 🔧 Standalone Tools

```bash
# Delay information for a specific train
uv run scripts/show_delays.py en1 4523

# List all servers
uv run scripts/list_servers.py

# Sync Steam stats manually
uv run scripts/sync_steam.py <steam_id>
```

## ⚠️ Important Notes

### Steam Stats Delay
Steam stats may update with a 5-10 second delay. The tracker:
- Waits up to 6 seconds for stats to update
- Retries 3 times with 2-second delays
- Records 0 distance/points if Steam API doesn't respond

### Single Instance
Only one tracker can run per Steam ID at a time:
- TUI and CLI use the same PID lock
- If you see "already running", check for:
  - Another tracker instance
  - Stale lock file: `data/tracker_{steam_id}.lock`

### Session Finalization
For accurate stats:
- Let the tracker detect when you leave the train
- Steam only updates stats on clean session end
- If your game crashes, stats won't update

### Steam Profile
Your Steam profile must be **public** for stats tracking to work.

## 🆘 Troubleshooting

### "STEAM_ID environment variable is required"
Create a `.env` file in the project root with your Steam ID.

### Stats show zeros
- Check that your Steam profile is public
- Make sure you completed the session normally
- Steam API might be temporarily unavailable

### TUI looks broken
- Minimum terminal size: 80x24
- Use a modern terminal (Windows Terminal recommended on Windows)
- Make sure your terminal supports Unicode

### Database locked
Only one tracker per Steam ID. Stop other instances or delete stale PID lock.

## 📚 More Information

- [TUI Guide](TUI_GUIDE.md) - Complete TUI documentation
- [TUI Layout](TUI_LAYOUT.txt) - Visual layout reference
- [AGENTS.md](../AGENTS.md) - Architecture & technical details
- [README.md](../README.md) - Full project documentation
