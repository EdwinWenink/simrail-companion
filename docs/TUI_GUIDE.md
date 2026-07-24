# TUI Dashboard Guide

## Overview

The TUI (Terminal User Interface) Dashboard provides a real-time, interactive view of your SimRail session tracking. Built with [Textual](https://textual.textualize.io/), it offers a rich terminal experience without leaving your console.

## Quick Start

```bash
# Make sure dependencies are installed
uv sync

# Set your Steam ID in .env file
echo "STEAM_ID=your_steam_id_here" > .env

# Launch the dashboard
uv run tui_tracker.py
```

## Dashboard Layout

### Left Column

#### 🚂 Session Panel (Top)
Shows your current active session in real-time:

**When driving a train:**
- Train number and name
- Route (start → end station)
- Server name
- Vehicle/locomotive details
- Elapsed time
- Live distance estimate (updated from Steam API)

**When dispatching:**
- Station name and prefix
- Server name
- Elapsed time

**When offline:**
- Shows "NO ACTIVE SESSION" status

#### 📊 Stats Panel (Middle)
Lifetime aggregate statistics:
- Total train sessions completed
- Total distance traveled (km)
- Total points earned
- Total driving time
- Total dispatching time

#### 🚂 Vehicle Composition Panel (Bottom)
Detailed consist information for current train:
- List of all locomotives (handles double-headed configs)
- List of EMU units
- Total vehicle count
- Number of wagons
- Total consist length (meters)
- Total consist weight (tonnes)

### Right Column

#### 📍 Recent Station Passages (Top)
Shows the last 10 stations passed in your current train session:
- Station name
- Stop type (PASSENGER, TECHNICAL, NONE)
- Time of passage

Perfect for tracking your progress along the route!

#### 🚂 Recent Sessions (Bottom)
Shows your last 10 completed train sessions:
- Train number
- Route (abbreviated)
- Distance traveled
- Points earned
- Session duration

## Controls

### Keyboard Shortcuts
- `R` - Manually refresh all panels
- `Q` - Quit the dashboard (cleanly ends active session)
- `Ctrl+C` - Emergency exit

### Buttons
- **Refresh [R]** - Same as `R` key
- **Quit [Q]** - Same as `Q` key

## Features

### Auto-Refresh
The dashboard automatically updates every **5 seconds** by:
1. Checking for active sessions
2. Querying the database for historical data
3. Updating all panels with new information

The tracker itself polls the SimRail API every **30 seconds** in the background.

### Live Distance Tracking
When you're driving a train, the dashboard shows a **live distance estimate** based on:
- Baseline Steam stats captured when you started
- Current Steam stats from periodic API calls
- Real-time calculation of distance delta

**Note:** Steam stats may be delayed by 5-10 seconds, so the displayed distance might lag slightly behind your actual position.

### Single-Instance Protection
The dashboard uses the same PID lock as the CLI tracker, preventing multiple instances from running simultaneously for the same Steam ID. This prevents:
- Race conditions in session tracking
- Duplicate distance/points recording
- Database conflicts

### Clean Shutdown
When you press `Q` or `Ctrl+C`, the dashboard:
1. Cancels the update loop
2. Stops the tracker gracefully
3. Finalizes any active sessions
4. Closes all API connections
5. Releases the PID lock

## Technical Details

### Architecture
```
TrackerDashboard (Textual App)
├── Header (clock + title)
├── Main Container
│   ├── Left Column
│   │   ├── SessionPanel (reactive)
│   │   ├── StatsPanel (reactive)
│   │   └── CompositionPanel (reactive)
│   └── Right Column
│       ├── StationsPanel (DataTable)
│       └── SessionsPanel (DataTable)
└── Footer (keybindings)
```

### Data Flow
1. **Tracker Task**: Runs `PlayerTracker.start()` in background asyncio task
2. **Update Loop**: Every 5s, queries database and updates UI
3. **Reactive Properties**: Panels automatically re-render when data changes
4. **Database Queries**: Direct SQLite reads for historical/aggregate data

### Performance
- Minimal CPU usage (~1-2% on modern hardware)
- Database queries are indexed and fast
- UI updates are efficient (only changed widgets re-render)
- No network calls from UI code (tracker handles all API interactions)

## Troubleshooting

### "Another tracker instance is already running"
Only one tracker can run per Steam ID at a time. Either:
- Stop the other instance (CLI or TUI)
- Check for stale PID file: `data/tracker_{steam_id}.lock`
- If stale, manually delete the lock file

### "STEAM_ID environment variable is required"
Create a `.env` file in the project root:
```bash
STEAM_ID=76561198XXXXXXXXX
```

### Stats show "—" or zero
- Your Steam profile might be private (set it to public)
- Steam API might be temporarily unavailable
- Session might have just started (wait for first API poll)

### Composition panel shows "No composition data available"
- Train might not have timetable data (some bot trains don't)
- SimRail Tools API might not have composition for this train
- This is expected for some services

### Terminal looks weird / broken layout
- Make sure your terminal supports Unicode and colors
- Try resizing the terminal (minimum 80x24 recommended)
- On Windows, use Windows Terminal or modern console

## Comparison: TUI vs CLI

| Feature | TUI Dashboard | CLI Tracker |
|---------|---------------|-------------|
| **Visual Appeal** | ✅ Rich panels & tables | ❌ Plain logs |
| **Real-time Updates** | ✅ Auto-refresh UI | ❌ Scroll logs |
| **Historical View** | ✅ Recent sessions table | ❌ Must query separately |
| **Composition Display** | ✅ Dedicated panel | ⚠️ Logs on change |
| **Debugging** | ❌ No detailed logs | ✅ Verbose logging |
| **Background Running** | ⚠️ Requires terminal open | ✅ Can redirect logs |
| **Scriptable** | ❌ Interactive only | ✅ Pipe/redirect friendly |

**Recommendation:** Use TUI for **active monitoring**, CLI for **debugging** or **background tracking**.

## Future Enhancements

Potential features for future versions:
- [ ] ASCII route map showing train position
- [ ] Sparkline charts for distance/points over time
- [ ] Real-time delay status in stations panel
- [ ] Dispatcher info (human/AI) for next station
- [ ] Color-coded delay indicators
- [ ] Session comparison view
- [ ] Export session to JSON/CSV from UI
- [ ] Sound notifications on session milestones
- [ ] Dark/light theme toggle
- [ ] Configurable refresh intervals
- [ ] Multi-player tracking (tabs)

## Credits

Built with:
- [Textual](https://textual.textualize.io/) - Terminal UI framework
- [Rich](https://rich.readthedocs.io/) - Rich text formatting
- SimRail APIs (multiplayer, Steam, Tools)
