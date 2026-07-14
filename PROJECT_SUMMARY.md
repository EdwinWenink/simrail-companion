# SimRail Steam Python Tracker - Project Summary

## Overview

This is a **Python-based single-player tracking system** for the SimRail train simulator game. It monitors a player's activity in real-time, tracks their sessions (both driving trains and dispatching at stations), calculates statistics, and provides live journey information including delays and upcoming stations.

**Created:** May 2026  
**Language:** Python 3.11+  
**Package Manager:** uv  
**Database:** SQLite

## Project Purpose

Originally extracted from the main simrail.pro project (a multi-player tracking backend in TypeScript), this standalone Python module was created to:

1. Track a **single player's** activity instead of all players
2. Provide **simplified session tracking** without the complexity of the full backend
3. Add **real-time journey information** (delays, upcoming stations, dispatcher info)
4. Store **Steam stats history** to track progress over time
5. Offer a **comprehensive summary** of player statistics and activity

## Architecture

### Core Modules

```
simrail-steam-py/
├── simrail_steam/          # Steam Web API client
│   ├── client.py           # API calls, retry logic, key rotation
│   └── types.py            # Steam data types
├── simrail_api/            # SimRail Multiplayer API client
│   ├── client.py           # Live player/server/train/station data
│   └── types.py            # SimRail data types
├── simrail_tools_api/      # SimRail Tools API client
│   ├── client.py           # Journey timetables, delay calculation
│   └── types.py            # Journey/delay data types
├── player_tracker/         # Core tracking logic
│   ├── tracker.py          # Main tracking loop and session management
│   ├── database.py         # SQLite schema and queries
│   └── summary.py          # Comprehensive statistics display
├── example_tracker.py      # Main entry point for continuous tracking
├── show_summary.py         # View statistics without tracking
├── sync_steam.py           # Manually sync Steam stats
└── debug_*.py              # Debug utilities
```

### Data Flow

```
Every 30 seconds:
┌─────────────────────────────────────────────────────────────┐
│ 1. SimRail Multiplayer API                                  │
│    → Find player by Steam ID                                │
│    → Determine: on train / at station / offline             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Session Tracking                                         │
│    → If new train: Get Steam stats (baseline)               │
│    → If train ended: Calculate distance/points delta        │
│    → Store session in SQLite                                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Journey Information (if on train)                        │
│    → SimRail Tools API: Get journey timetable               │
│    → Calculate delays (scheduled vs realtime)               │
│    → Filter upcoming stations (REAL vs PREDICTION/SCHEDULE) │
│    → Check dispatcher type (human/AI) at next station       │
│    → Display only when next station changes                 │
└─────────────────────────────────────────────────────────────┘
```

### Database Schema

**train_sessions:**
- Session tracking for train driving
- Stores: train number, vehicle, route, distance, points, duration
- Distance/points calculated via Steam API delta (join stats - leave stats)

**station_sessions:**
- Session tracking for dispatching
- Stores: station name, duration
- No per-station Steam stats available (only aggregate DISPATCHER_TIME)

**steam_stats:**
- Historical Steam statistics snapshots
- Stores: total distance, points, dispatcher time
- Synced before tracking starts and manually via sync_steam.py

## Recent Development (Session Context)

### Major Features Implemented

1. **Delay Tracking** (May 31, 2026)
   - Integrated SimRail Tools API for journey timetables
   - Calculate delay: `realtimeTime - scheduledTime`
   - Show next 5 upcoming stations with delay status
   - Color-coded: 🔴 delayed, 🟢 early/on-time, ⚪ on-time

2. **Dispatcher Detection**
   - Check if next station has human (👤) or AI (🤖) dispatcher
   - Cross-reference journey station names with live station data

3. **Graceful Ctrl-C Handling**
   - Always shows summary when interrupted
   - Closes active sessions properly
   - Clean shutdown with no traceback

4. **Smart Display Logic**
   - Only show upcoming stations when next station changes
   - Prevents log spam (was showing every 30 seconds)
   - Still shows initial route when boarding

### Critical Fixes

#### 1. **Timezone Issues** (Multiple iterations)
**Problem:** API returns times in server local timezone (UTC+1 or UTC+2), but we were treating them as UTC, causing "2 hours ago" displays for current events.

**Solution:** 
- Don't compare absolute times across timezones
- Parse times as naive datetimes (no timezone)
- Delay calculation still works (both times in same timezone, delta is correct)

#### 2. **Incorrect Station Filtering** (Final fix)
**Problem:** Events marked `SCHEDULE` were assumed to be future, but `SCHEDULE` actually means "no realtime data yet" and could be past or future.

**Original approach:** Filter by `realtimeTimeType != "REAL"` (wrong!)
- Result: Showed all SCHEDULE + PREDICTION events, including past ones
- Example: Journey started at Małaszewicze (3 hours ago) but still showed as "upcoming"

**Actual API behavior:**
- `REAL` = Past event (already happened, recorded actual time)
- `PREDICTION` = Future event (estimated based on current delay)
- `SCHEDULE` = No realtime data (could be past OR future)

**Final solution:**
```python
# Find last event that actually happened
last_real_index = max(i for i, event in enumerate(events) 
                      if event["realtimeTimeType"] == "REAL")

# Show everything after that
upcoming_events = events[last_real_index + 1:]
```

This works regardless of whether future events are PREDICTION or SCHEDULE.

#### 3. **Train Number Matching**
**Problem:** API journey train numbers had leading zeros/whitespace, didn't match player train numbers.

**Solution:** Normalize both sides (strip whitespace and leading zeros) before comparison.

#### 4. **Server UUID Resolution**
**Problem:** SimRail Tools API requires server UUID, but we only have server code (e.g., "int1").

**Solution:** Add `get_server_id_by_code()` with caching to convert codes to UUIDs.

#### 5. **404 Journey Errors**
**Problem:** Journey fetch would fail with 404 when train reached destination.

**Solution:** Handle 404 gracefully, log warning, continue tracking (journey ended is normal).

### Debug Tools Created

- **debug_delay_filtering.py** - Inspect journey events and filtering logic
- **debug_journey.py** - List active journeys on a server
- **list_servers.py** - Show all available servers with codes/UUIDs
- **show_delays.py** - Display delays for specific train

## Current State

### What Works

✅ **Session Tracking**
- Automatically detects when player boards/leaves trains
- Calculates distance and points per session (Steam API delta)
- Tracks dispatching time at stations
- Stores all sessions in SQLite

✅ **Steam Stats History**
- Syncs Steam stats before tracking
- Historical snapshots stored in database
- Summary shows Steam stats comparison (start vs now)

✅ **Journey Information**
- Shows next 5 upcoming stations
- Delay status with color coding
- Stop indicator (stop vs pass through)
- Dispatcher type (human/AI) at next stop
- Time type indicator (🔮 predicted, 📅 scheduled)
- Only displays when next station changes (no spam)

✅ **Comprehensive Summary**
- Overall stats (total distance, points, dispatcher time)
- Per-vehicle breakdown (most driven trains)
- Per-station breakdown (time spent dispatching)
- Recent sessions (last N train/station sessions)
- Activity timeline (last sessions with context)
- Tracking coverage (% of Steam distance tracked)
- Steam stats comparison (before/after)

✅ **Error Handling**
- Graceful Ctrl-C (always shows summary)
- Handles journey 404s (train reached destination)
- Retries on Steam API failures
- Continues tracking even if timetable unavailable

### Known Limitations

⚠️ **Per-Station Dispatcher Stats Not Available**
- Steam API only provides aggregate `DISPATCHER_TIME`
- Per-station stats would require monitoring live API join/leave events

⚠️ **Server Timezone Unknown**
- Times displayed are in server local time (UTC+1 or UTC+2)
- Can't convert to user's local time without knowing server timezone
- Delay calculation works (same timezone for both times)

⚠️ **Bot Trains Have No Timetable**
- AI-driven trains don't appear in SimRail Tools API
- Tracking still works, but no delay/upcoming station info

⚠️ **Unused Variable Warnings**
- `action` variable set but not used in upcoming stations display
- Cosmetic issue, doesn't affect functionality

### Configuration

**Required Environment Variables:**
```bash
STEAM_API_KEY="your-steam-api-key"
# OR multiple keys:
STEAM_API_KEY='["key1", "key2", "key3"]'
```

**Key Files to Modify:**
- `example_tracker.py` - Change `steam_id` variable to track different player
- `player_tracker.db` - SQLite database (can be deleted to reset)

## Usage

### Start Tracking
```bash
cd simrail-steam-py
uv run example_tracker.py
```
- Syncs Steam stats
- Polls every 30 seconds
- Press Ctrl-C to stop and view summary

### View Summary (Without Tracking)
```bash
uv run show_summary.py <steam_id>
uv run show_summary.py <steam_id> --active-only
uv run show_summary.py <steam_id> --sessions 20
```

### Manually Sync Steam Stats
```bash
uv run sync_steam.py <steam_id>
```

### Debug Tools
```bash
# Inspect journey filtering
uv run debug_delay_filtering.py <steam_id>

# List servers
uv run list_servers.py

# List active journeys on a server
uv run debug_journey.py int1

# Search for specific train
uv run debug_journey.py int1 --train 6162

# Show delays for a train
uv run show_delays.py int1 6162
```

## Example Output

```
============================================================
PLAYER TRACKER - Steam ID: 76561198033647260
============================================================
Polling interval: 30 seconds
Press Ctrl+C to stop and view stats
============================================================

23:15:42 [INFO] Syncing Steam stats...
23:15:43 [INFO] ✅ Steam stats synced: 1,234,567m, 45,678 points, 89 min dispatcher time
23:15:43 [INFO] Started tracking player 76561198033647260
23:15:46 [INFO] 🚂 Started driving train 144031 (IC "Batory") - EU07-123
23:15:46 [INFO]    Route: Małaszewicze → Częstochowa Towarowa on International 1

────────────────────────────────────────────────────────────────────────────────
🚂 UPCOMING STATION EVENTS (next 5 of 22):
────────────────────────────────────────────────────────────────────────────────
  1. [X] Rokiciny                          22:51→22:45 🔴-6m     🔮 👤
  2. [X] Baby                              23:02→22:56 🔴-6m     🔮
  3. [X] Baby                              23:03→22:57 🔴-6m     🔮
  4. [X] Piotrków Trybunalski              23:14→23:08 🔴-6m     🔮
  5. [X] Piotrków Trybunalski              23:25→23:25 ⚪on time 🔮
────────────────────────────────────────────────────────────────────────────────

^C

============================================================
SHUTTING DOWN...
============================================================
23:20:15 [INFO] Ending active train session
23:20:16 [INFO] ✅ Completed train session: 12,543m (12.54km), 485 points

================================================================================
PLAYER TRACKING SUMMARY - Steam ID: 76561198033647260
================================================================================
[Full summary with stats, sessions, timeline...]

✅ Tracker stopped successfully
```

## Next Steps / Future Enhancements

### Potential Improvements

1. **Fix Unused Variable Warning**
   - Remove or use the `action` variable in upcoming stations display

2. **Configurable Display**
   - Add settings for how many upcoming stations to show
   - Toggle dispatcher info, time type indicators, etc.

3. **Better Time Display**
   - Show relative time ("in 5 minutes") in addition to absolute time
   - Optionally convert to user's local timezone (if server timezone known)

4. **Export Functionality**
   - Export statistics to CSV/JSON
   - Generate reports for specific date ranges

5. **Live Dashboard**
   - Web-based dashboard showing real-time tracking
   - Charts/graphs for statistics over time

6. **Multi-Player Support**
   - Track multiple Steam IDs simultaneously
   - Compare statistics between players

7. **Achievements Integration**
   - Track progress toward Steam achievements
   - Alert when close to completing achievements

### Questions to Resolve

- Should we show ARRIVAL and DEPARTURE as separate entries, or consolidate stops?
- Should delay color coding thresholds be configurable? (currently >1 min)
- Should we cache journey data longer to reduce API calls?

## Development Notes

### API Documentation

- **Steam Web API:** https://steamcommunity.com/dev
- **SimRail Multiplayer API:** panel.simrail.eu:8084 (undocumented)
- **SimRail Tools API:** https://apis.simrail.tools (OpenAPI spec included)

### Testing Checklist

When making changes, test these scenarios:

- [ ] Player boards a train (session created, Steam stats recorded)
- [ ] Player drives for a while (upcoming stations update correctly)
- [ ] Player completes journey (session ended, distance/points calculated)
- [ ] Player switches trains mid-journey (old session ended, new started)
- [ ] Player goes offline (active sessions closed)
- [ ] Ctrl-C during tracking (summary displays, sessions closed)
- [ ] Bot train (no timetable available, tracking continues)
- [ ] Journey ends while tracking (404 handled gracefully)
- [ ] Dispatching at station (station session created)

### Common Issues

**"No timetable data available"**
- Train is AI-driven (bot train)
- Train number mismatch (check normalization)
- Server UUID resolution failed (check server code)

**"Next station still showing old station"**
- `realtimeTimeType` hasn't updated to REAL yet
- API lag (wait for next poll)
- Journey may have ended (check for 404s)

**"Tracking coverage shows 0%"**
- No sessions tracked yet (distance_meters = 0 in sessions)
- Steam stats haven't updated (API lag)
- Sessions ended with missing Steam stats (check warnings)

## Project History Summary

This project was created during a conversation on **May 31, 2026**. Key milestones:

1. Initial Steam API client (get player stats)
2. Added SimRail Multiplayer API (find active player)
3. Implemented session tracking with SQLite
4. Added Steam stats history
5. Integrated delay tracking with SimRail Tools API
6. Added dispatcher detection
7. Fixed timezone issues (3-4 iterations)
8. Fixed station filtering (SCHEDULE vs PREDICTION vs REAL)
9. Added smart display logic (only show on station change)
10. Improved Ctrl-C handling

**Current Version:** Functional single-player tracker with real-time journey information.

