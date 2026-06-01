"""Tests for delay calculation logic."""
import pytest
from simrail_tools_api.client import SimRailToolsClient
from simrail_tools_api.types import JourneyEvent


class TestDelayCalculation:
    """Tests for the calculate_delay method."""

    @pytest.fixture
    def client(self):
        """Create a SimRailToolsClient instance."""
        return SimRailToolsClient()

    def test_on_time_arrival(self, client):
        """Test delay calculation for on-time arrival."""
        event_data = {
            'id': 'test-123',
            'type': 'ARRIVAL',
            'cancelled': False,
            'additional': False,
            'stopPlace': {'id': 'station-1', 'name': 'Test Station'},
            'scheduledTime': '2024-01-01T12:00:00.000Z',
            'realtimeTime': '2024-01-01T12:00:00.000Z',
            'realtimeTimeType': 'PREDICTION',
            'stopType': 'PASSENGER',
            'transport': {'category': 'IC', 'number': '1234', 'line': None}
        }

        event = JourneyEvent(**event_data)
        delay_info = client.calculate_delay(event)

        assert delay_info.delay_seconds == 0
        assert delay_info.delay_minutes == 0.0
        assert delay_info.status == 'on_time'
        assert delay_info.station_name == 'Test Station'
        assert delay_info.event_type == 'ARRIVAL'
        assert delay_info.stop_type == 'PASSENGER'

    def test_delayed_arrival(self, client):
        """Test delay calculation for delayed arrival (>1 minute late)."""
        event_data = {
            'id': 'test-123',
            'type': 'ARRIVAL',
            'cancelled': False,
            'additional': False,
            'stopPlace': {'id': 'station-1', 'name': 'Test Station'},
            'scheduledTime': '2024-01-01T12:00:00.000Z',
            'realtimeTime': '2024-01-01T12:03:30.000Z',
            'realtimeTimeType': 'PREDICTION',
            'stopType': 'PASSENGER',
            'transport': {'category': 'IC', 'number': '1234', 'line': None}
        }

        event = JourneyEvent(**event_data)
        delay_info = client.calculate_delay(event)

        assert delay_info.delay_seconds == 210
        assert delay_info.delay_minutes == 3.5
        assert delay_info.status == 'delayed'

    def test_early_arrival(self, client):
        """Test delay calculation for early arrival (>1 minute early)."""
        event_data = {
            'id': 'test-123',
            'type': 'ARRIVAL',
            'cancelled': False,
            'additional': False,
            'stopPlace': {'id': 'station-1', 'name': 'Test Station'},
            'scheduledTime': '2024-01-01T12:05:00.000Z',
            'realtimeTime': '2024-01-01T12:03:00.000Z',
            'realtimeTimeType': 'PREDICTION',
            'stopType': 'PASSENGER',
            'transport': {'category': 'IC', 'number': '1234', 'line': None}
        }

        event = JourneyEvent(**event_data)
        delay_info = client.calculate_delay(event)

        assert delay_info.delay_seconds == -120
        assert delay_info.delay_minutes == -2.0
        assert delay_info.status == 'early'

    def test_small_delay_counts_as_on_time(self, client):
        """Test that delays <1 minute are considered on_time."""
        event_data = {
            'id': 'test-123',
            'type': 'ARRIVAL',
            'cancelled': False,
            'additional': False,
            'stopPlace': {'id': 'station-1', 'name': 'Test Station'},
            'scheduledTime': '2024-01-01T12:00:00.000Z',
            'realtimeTime': '2024-01-01T12:00:45.000Z',
            'realtimeTimeType': 'PREDICTION',
            'stopType': 'PASSENGER',
            'transport': {'category': 'IC', 'number': '1234', 'line': None}
        }

        event = JourneyEvent(**event_data)
        delay_info = client.calculate_delay(event)

        assert delay_info.delay_seconds == 45
        assert delay_info.delay_minutes == 0.75
        assert delay_info.status == 'on_time'

    def test_pass_through_station(self, client):
        """Test delay calculation for pass-through station (stopType=NONE)."""
        event_data = {
            'id': 'test-123',
            'type': 'ARRIVAL',
            'cancelled': False,
            'additional': False,
            'stopPlace': {'id': 'station-1', 'name': 'Pass Through Station'},
            'scheduledTime': '2024-01-01T12:00:00.000Z',
            'realtimeTime': '2024-01-01T12:00:00.000Z',
            'realtimeTimeType': 'PREDICTION',
            'stopType': 'NONE',
            'transport': {'category': 'IC', 'number': '1234', 'line': None}
        }

        event = JourneyEvent(**event_data)
        delay_info = client.calculate_delay(event)

        assert delay_info.stop_type == 'NONE'
        assert delay_info.station_name == 'Pass Through Station'

    def test_technical_stop(self, client):
        """Test delay calculation for technical stop."""
        event_data = {
            'id': 'test-123',
            'type': 'DEPARTURE',
            'cancelled': False,
            'additional': False,
            'stopPlace': {'id': 'station-1', 'name': 'Technical Stop'},
            'scheduledTime': '2024-01-01T12:00:00.000Z',
            'realtimeTime': '2024-01-01T12:01:30.000Z',
            'realtimeTimeType': 'PREDICTION',
            'stopType': 'TECHNICAL',
            'transport': {'category': 'IC', 'number': '1234', 'line': None}
        }

        event = JourneyEvent(**event_data)
        delay_info = client.calculate_delay(event)

        assert delay_info.stop_type == 'TECHNICAL'
        assert delay_info.event_type == 'DEPARTURE'
        assert delay_info.delay_seconds == 90
        assert delay_info.status == 'delayed'

    def test_delay_preserves_all_fields(self, client):
        """Test that calculate_delay preserves all event fields."""
        event_data = {
            'id': 'test-123',
            'type': 'DEPARTURE',
            'cancelled': False,
            'additional': False,
            'stopPlace': {'id': 'station-1', 'name': 'Test Station'},
            'scheduledTime': '2024-01-01T12:00:00.000Z',
            'realtimeTime': '2024-01-01T12:02:00.000Z',
            'realtimeTimeType': 'REAL',
            'stopType': 'PASSENGER',
            'transport': {'category': 'IC', 'number': '1234', 'line': None}
        }

        event = JourneyEvent(**event_data)
        delay_info = client.calculate_delay(event)

        assert delay_info.station_name == 'Test Station'
        assert delay_info.event_type == 'DEPARTURE'
        assert delay_info.time_type == 'REAL'
        assert delay_info.stop_type == 'PASSENGER'
        # Check that datetime objects are preserved
        assert delay_info.scheduled_time == event.scheduledTime
        assert delay_info.realtime_time == event.realtimeTime

    def test_large_delay(self, client):
        """Test delay calculation for very large delay (>1 hour)."""
        event_data = {
            'id': 'test-123',
            'type': 'ARRIVAL',
            'cancelled': False,
            'additional': False,
            'stopPlace': {'id': 'station-1', 'name': 'Test Station'},
            'scheduledTime': '2024-01-01T12:00:00.000Z',
            'realtimeTime': '2024-01-01T13:30:00.000Z',
            'realtimeTimeType': 'PREDICTION',
            'stopType': 'PASSENGER',
            'transport': {'category': 'IC', 'number': '1234', 'line': None}
        }

        event = JourneyEvent(**event_data)
        delay_info = client.calculate_delay(event)

        assert delay_info.delay_seconds == 5400
        assert delay_info.delay_minutes == 90.0
        assert delay_info.status == 'delayed'
