# TUI Update - Steam Baseline Stats

## Changes Made

Enhanced the **Lifetime Statistics** panel to show Steam baseline stats and tracking coverage percentage, matching the CLI tracker's output.

### Before

```
📊 LIFETIME STATISTICS

Train Sessions: 42
Total Distance: 1,234.5 km
Total Points: 456,789
Driving Time: 23h 45m
Dispatching Time: 5h 12m
```

### After

```
📊 LIFETIME STATISTICS

Steam Total: 2,500.0 km, 850,000 pts

Train Sessions: 42
Tracked Distance: 1,234.5 km
Tracked Points: 456,789
Driving Time: 23h 45m
Dispatching: 5h 12m

Coverage: 49.4% tracked
```

## What's Displayed

### Steam Baseline (if available)
- **Steam Total Distance** (km) - from Steam API
- **Steam Total Points** - from Steam API

Shows the "ground truth" from Steam's official stats.

### Tracked Stats
- **Train Sessions** - number of sessions tracked by this tool
- **Tracked Distance** - distance calculated from this tool's tracking
- **Tracked Points** - points calculated from this tool's tracking
- **Driving Time** - total time driving trains (from tracker)
- **Dispatching Time** - total time at stations (from tracker)

### Coverage Percentage
- **Coverage %** - `(tracked_distance / steam_distance) × 100`
- Shows what percentage of your Steam distance has been tracked by this tool
- Useful for understanding how complete your tracking history is

## Why This Matters

The coverage percentage answers:
- **"How much of my SimRail career have I tracked?"**
- **"Did I miss tracking any sessions?"**
- **"Is my tracking data representative of my overall play?"**

### Example Scenarios

**High Coverage (90%+):**
```
Steam Total: 1,500.0 km, 400,000 pts
Tracked Distance: 1,350.0 km
Coverage: 90.0% tracked
```
→ You've been tracking consistently, data is very representative.

**Medium Coverage (50-90%):**
```
Steam Total: 2,500.0 km, 850,000 pts
Tracked Distance: 1,234.5 km
Coverage: 49.4% tracked
```
→ You started tracking after playing for a while, or missed some sessions.

**Low Coverage (<50%):**
```
Steam Total: 5,000.0 km, 1,500,000 pts
Tracked Distance: 500.0 km
Coverage: 10.0% tracked
```
→ Recently started tracking, most of your career is untracked.

## Technical Implementation

### Data Source
```python
# Get latest Steam stats from database
latest_steam = self.db.get_latest_steam_stats(self.steam_id)

# Calculate coverage
if latest_steam and latest_steam["total_distance_meters"] > 0:
    coverage = (stats["total_distance_meters"] / 
                latest_steam["total_distance_meters"]) * 100
```

### Fallback Behavior
- If no Steam stats synced yet: Shows only tracked stats (no baseline or coverage)
- If Steam distance is 0: No coverage percentage shown
- If Steam profile is private: Steam stats will be unavailable

### Sync Frequency
Steam stats are synced:
- When tracker starts
- Can be manually synced with: `uv run scripts/sync_steam.py <steam_id>`
- Stored in `steam_stats` table with timestamps

## UI Adjustments

### Panel Height
Increased Stats Panel height from `10` to `14` lines to accommodate:
- Steam baseline (2 lines)
- Tracked stats (5 lines)
- Coverage percentage (2 lines)
- Spacing

### Text Formatting
- **Steam Total:** Bold/emphasized line at top
- **Tracked stats:** Clear labels with values
- **Coverage:** Bottom summary line with percentage

## Comparison with CLI

The TUI now shows the **exact same information** as the CLI summary:

| Information | CLI | TUI v2 | TUI v3 |
|-------------|-----|--------|--------|
| Steam baseline distance | ✅ | ❌ | ✅ |
| Steam baseline points | ✅ | ❌ | ✅ |
| Tracked distance | ✅ | ✅ | ✅ |
| Tracked points | ✅ | ✅ | ✅ |
| Coverage percentage | ✅ | ❌ | ✅ |
| Driving time | ✅ | ✅ | ✅ |
| Dispatching time | ✅ | ✅ | ✅ |

**Result:** ✅ **Complete parity** with CLI stats display

## Related Files

- `src/player_tracker/tui.py` - Stats panel update logic
- `src/player_tracker/database.py` - `get_latest_steam_stats()` method
- `src/player_tracker/summary.py` - CLI version for reference

## Future Enhancements

Potential additions:
- [ ] Show Steam dispatcher time baseline
- [ ] Show gain since last sync
- [ ] Display last sync timestamp
- [ ] Color-code coverage (red <50%, yellow 50-80%, green >80%)
- [ ] Graph coverage trend over time
- [ ] Compare points-per-km efficiency vs. Steam average

## Testing Checklist

- [x] Stats panel shows Steam baseline when available
- [x] Stats panel shows tracked stats
- [x] Coverage percentage calculated correctly
- [x] Handles missing Steam stats gracefully
- [x] Handles zero Steam distance gracefully
- [x] Panel height accommodates all lines
- [x] Formatting is clear and readable
- [x] Matches CLI output format
