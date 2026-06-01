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
Tests for core Pydantic type models, verifying:
- ISO-8601 datetime parsing (with milliseconds and timezone)
- Timezone-aware datetime handling
- Stop types (NONE, TECHNICAL, PASSENGER)
- Event types (ARRIVAL, DEPARTURE)
- Realtime time types (SCHEDULE, PREDICTION, REAL)
- DateTime formatting with strftime
- Journey model creation with nested events

### `test_extended_types.py`
Tests for extended Journey model fields from OpenAPI spec:
- JourneyStopInfo (platform and track information)
- GeoPosition (latitude and longitude)
- JourneyLiveData with optional driver and nextSignal fields
- JourneyEvent with optional scheduledPassengerStop and realtimePassengerStop
- Journey model with optional liveData

### `test_transport.py`
Tests for complete JourneyTransport model:
- All required and optional fields (category, categoryExternal, number, line, label, type, maxSpeed)
- All 12 transport types (express, regional, cargo, maintenance, etc.)
- Real-world examples (EuroCity, cargo trains, maintenance trains)

### `test_vehicles.py`
Tests for vehicle composition models:
- Railcar model with physical properties and DLC requirements
- Vehicle model with optional cargo loads
- VehicleSequence for complete train compositions
- All 19 cargo load types (coal, petrol, containers, wood, etc.)
- Vehicle indexing and ordering in compositions
- Printable string representation with locomotive info and statistics

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

Current test count: **47 tests**
- 8 tests for delay calculation
- 9 tests for extended Journey/Event types  
- 6 tests for core type models
- 6 tests for JourneyTransport
- 14 tests for vehicle composition models (including printable representation)
- 4 tests for DelayInfo and Journey creation

All tests verify that:
1. Pydantic correctly parses API datetime strings (both timezone-aware with `Z` and timezone-naive without)
2. Delay calculations handle all edge cases (on-time, delayed, early)
3. Stop types are properly distinguished (pass-through vs actual stops)
4. All event metadata is preserved through transformations
5. DateTime formatting works correctly for both timezone-aware and timezone-naive datetimes
