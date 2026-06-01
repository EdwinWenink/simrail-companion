# Tests

This directory contains the test suite for the SimRail Companion project.

## Running Tests

```bash
# Run all tests
uv run pytest tests/

# Run with verbose output
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_types.py -v

# Run specific test class or method
uv run pytest tests/test_delay_calculation.py::TestDelayCalculation::test_delayed_arrival -v
```

## Test Structure

### `test_types.py`
Tests for Pydantic type models, verifying:
- ISO-8601 datetime parsing (with milliseconds and timezone)
- Timezone-aware datetime handling
- Stop types (NONE, TECHNICAL, PASSENGER)
- Event types (ARRIVAL, DEPARTURE)
- Realtime time types (SCHEDULE, PREDICTION, REAL)
- DateTime formatting with strftime
- Journey model creation with nested events

### `test_delay_calculation.py`
Tests for delay calculation logic, covering:
- On-time arrivals (0 delay)
- Delayed arrivals (>1 minute late)
- Early arrivals (>1 minute early)
- Small delays (<1 minute counted as on-time)
- Pass-through stations (stopType=NONE)
- Technical stops
- Large delays (>1 hour)
- Field preservation during calculation

## Test Coverage

Current test count: **18 tests**

All tests verify that:
1. Pydantic correctly parses API datetime strings (both timezone-aware with `Z` and timezone-naive without)
2. Delay calculations handle all edge cases (on-time, delayed, early)
3. Stop types are properly distinguished (pass-through vs actual stops)
4. All event metadata is preserved through transformations
5. DateTime formatting works correctly for both timezone-aware and timezone-naive datetimes
