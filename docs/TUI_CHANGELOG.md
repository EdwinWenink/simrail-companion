# TUI Enhancement Changelog

## Version 2.0 - Feature Parity with CLI Tracker

### New Panels Added

#### 1. **Upcoming Stations Panel** (Middle Column, Top)
Shows the next 5 upcoming stations with comprehensive delay information:

- **Station name** with event indicator:
  - `[A]` - Arrival
  - `[D]` - Departure  
  - `━━━` - Pass-through (no stop)
- **Scheduled → Realtime times** (HH:MM format)
- **Delay status** with color-coded icons:
  - 🔴 Delayed (+Xm)
  - 🟢 Early (-Xm)
  - ⚪ On time
- **Time type indicators**:
  - 📅 Schedule (no real-time data)
  - 🔮 Prediction (estimated)
- **Dispatcher status** (for next station only):
  - 👤 Human dispatcher
  - 🤖 AI dispatcher

**Example:**
```
Next 5 Stations:

1. [A] Sosnowiec Główny
   14:30→14:32 +2m 🔴 🔮 👤

2. ━━━ Będzin
   14:45→14:45 on time ⚪ 📅

3. [D] Dąbrowa Górnicza
   14:52→14:50 -2m 🟢 🔮
```

#### 2. **Passed Stations Panel** (Middle Column, Middle)
Shows stations already passed in current session:
- Station name
- Stop type (PASSENGER, TECHNICAL, NONE)
- Time of passage (HH:MM:SS)

Replaces the previous "Recent Station Passages" panel.

#### 3. **Event Log Panel** (Right Column, Full Height)
Real-time event stream showing:
- Session start/end events
- Baseline stats captured
- Distance/points calculations
- API events
- Session switches
- Errors and warnings

**Format:** `[HH:MM:SS] message`

**Example:**
```
[14:25:12] ✅ Tracker started
[14:25:45] 🚂 Started driving train 4523 (IC 4523 Przemysl)
[14:25:45] 📊 Baseline captured: 123,456 m, 45,678 points
[14:26:15] 📍 Recorded passage: Sosnowiec (PASSENGER)
[14:27:30] Player switched trains: 4523 -> 6162
[14:27:30] ✅ Completed train session: 12,345 m (12.35 km), 1,234 points
```

### Layout Changes

**Before (2-column):**
- Left: Session, Stats, Composition
- Right: Stations (50%), Sessions (50%)

**After (3-column):**
- Left (40%): Session, Stats, Composition
- Middle (35%): Upcoming Stations, Passed Stations, Recent Sessions
- Right (25%): Event Log (full height)

### Technical Implementation

#### Event Logging System
- Custom `logging.Handler` intercepts tracker logs
- Filters out verbose debug messages
- Pipes relevant events to TUI event panel
- Thread-safe with try/except guards

#### Async API Integration
- Fetches delay data from SimRail Tools API
- Queries dispatcher status from SimRail API  
- Non-blocking updates (doesn't freeze UI)
- Graceful error handling with fallbacks

#### Data Flow
```
PlayerTracker (background)
    ↓ logs to
TUILogHandler
    ↓ pipes to
EventLogPanel.add_log()
    ↓ displays in
Event Log Widget
```

```
SimRail Tools API
    ↓ delays data
UpcomingStationsPanel
    ↓ formats
Delay display with icons
```

### Information Completeness

The TUI now displays **everything** the CLI tracker shows:

| Information | CLI (main.py) | TUI v1 | TUI v2 |
|-------------|---------------|--------|--------|
| Current session | ✅ | ✅ | ✅ |
| Lifetime stats | ✅ | ✅ | ✅ |
| Vehicle composition | ✅ | ✅ | ✅ |
| Upcoming stations | ✅ | ❌ | ✅ |
| Delay information | ✅ | ❌ | ✅ |
| Dispatcher status | ✅ | ❌ | ✅ |
| Passed stations | ✅ | ✅ | ✅ |
| Recent sessions | ✅ | ✅ | ✅ |
| Event log | ✅ | ❌ | ✅ |
| Session transitions | ✅ | ❌ | ✅ |
| Stats calculations | ✅ | ❌ | ✅ |

**Result:** ✅ **100% feature parity** with CLI tracker

### Performance Impact

- Event log: ~50 lines max (auto-trimmed)
- Delay API calls: 1 per 5s update cycle (only when train active)
- Dispatcher API calls: 1 per 5s (only for next station)
- Memory increase: ~5-10 MB (event log buffer)

### User Experience Improvements

#### Information Density
- More data visible without scrolling
- Grouped by relevance (current, upcoming, historical)
- Event stream for context/debugging

#### Visual Hierarchy
- Left: "What I'm doing now"
- Middle: "Where I'm going"
- Right: "What just happened"

#### Real-time Feedback
- Event log shows tracker is working
- Delay updates every 5 seconds
- No need to check console logs

### Future Enhancements

Now that we have feature parity, potential additions:

- [ ] Route map visualization (linear or braille)
- [ ] Color themes for delay indicators
- [ ] Sound notifications for events
- [ ] Export event log to file
- [ ] Filter event log by category
- [ ] Fullscreen mode for specific panels
- [ ] Keyboard shortcuts for navigation
- [ ] Session comparison view

### Migration Notes

**Backwards Compatible:** The TUI v2 works with existing databases and configs.

**Breaking Changes:** None.

**New Dependencies:** None (uses existing Textual + APIs).

### Testing Checklist

- [x] Session panel shows current train/station
- [x] Stats panel shows lifetime aggregates
- [x] Composition panel shows vehicle details
- [x] Upcoming stations shows delay info
- [x] Passed stations shows historical passages
- [x] Recent sessions shows last 10 sessions
- [x] Event log captures tracker events
- [x] Delay indicators work (🔴 🟢 ⚪)
- [x] Dispatcher status works (👤 🤖)
- [x] Time type indicators work (📅 🔮)
- [x] Auto-scroll works in event log
- [x] Handles no-journey-data gracefully
- [x] Handles offline state gracefully
- [x] Refresh button works
- [x] Quit button works
- [x] Keyboard shortcuts work (R, Q)

### Known Issues

None at this time. The S110 linting warnings (try-except-pass) are intentional for non-critical UI updates.

### Credits

- Event logging pattern inspired by Textual logging examples
- Delay formatting matches CLI tracker exactly
- Layout optimized for 80x24+ terminals
