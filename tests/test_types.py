"""Tests for Pydantic type models."""
from datetime import datetime
from simrail_tools_api.types import (
    JourneyEvent,
    DelayInfo,
    Journey,
)


class TestJourneyEvent:
    """Tests for JourneyEvent model."""

    def test_parse_iso_datetime_with_milliseconds_and_z(self):
        """Test parsing ISO-8601 datetime with milliseconds and Z timezone."""
        event_data = {
            'id': 'test-123',
            'type': 'ARRIVAL',
            'cancelled': False,
            'additional': False,
            'stopPlace': {'id': 'station-1', 'name': 'Test Station'},
            'scheduledTime': '1970-01-01T00:00:00.000Z',
            'realtimeTime': '1970-01-01T00:02:00.000Z',
            'realtimeTimeType': 'PREDICTION',
            'stopType': 'PASSENGER',
            'transport': {'category': 'EIP', 'number': '1234', 'line': None}
        }

        event = JourneyEvent(**event_data)

        assert isinstance(event.scheduledTime, datetime)
        assert isinstance(event.realtimeTime, datetime)
        assert event.scheduledTime.tzinfo is not None
        assert event.realtimeTime.tzinfo is not None

    def test_datetime_is_timezone_aware(self):
        """Test that parsed datetimes with Z are timezone-aware (UTC)."""
        event_data = {
            'id': 'test-123',
            'type': 'DEPARTURE',
            'cancelled': False,
            'additional': False,
            'stopPlace': {'id': 'station-1', 'name': 'Test Station'},
            'scheduledTime': '2024-01-01T12:00:00.000Z',
            'realtimeTime': '2024-01-01T12:02:00.000Z',
            'realtimeTimeType': 'REAL',
            'stopType': 'TECHNICAL',
            'transport': {'category': 'IC', 'number': '5678', 'line': 'S1'}
        }

        event = JourneyEvent(**event_data)

        # Check that timezone is present (Pydantic uses its own TzInfo(UTC))
        assert event.scheduledTime.tzinfo is not None
        assert event.realtimeTime.tzinfo is not None
        assert str(event.scheduledTime.tzinfo) == 'UTC'
        assert str(event.realtimeTime.tzinfo) == 'UTC'

    def test_datetime_without_timezone(self):
        """Test that parsed datetimes without timezone info work (timezone-naive)."""
        event_data = {
            'id': 'test-456',
            'type': 'ARRIVAL',
            'cancelled': False,
            'additional': False,
            'stopPlace': {'id': 'station-2', 'name': 'Test Station 2'},
            'scheduledTime': '2026-06-01T11:44:00',
            'realtimeTime': '2026-06-01T11:46:00',
            'realtimeTimeType': 'PREDICTION',
            'stopType': 'PASSENGER',
            'transport': {'category': 'IC', 'number': '1234', 'line': None}
        }

        event = JourneyEvent(**event_data)

        # Check that datetimes are parsed (even without timezone)
        assert isinstance(event.scheduledTime, datetime)
        assert isinstance(event.realtimeTime, datetime)
        # These should be timezone-naive
        assert event.scheduledTime.tzinfo is None
        assert event.realtimeTime.tzinfo is None

    def test_stop_types(self):
        """Test all three stop types: NONE, TECHNICAL, PASSENGER."""
        base_data = {
            'id': 'test-123',
            'type': 'ARRIVAL',
            'cancelled': False,
            'additional': False,
            'stopPlace': {'id': 'station-1', 'name': 'Test Station'},
            'scheduledTime': '2024-01-01T12:00:00.000Z',
            'realtimeTime': '2024-01-01T12:00:00.000Z',
            'realtimeTimeType': 'SCHEDULE',
            'transport': {'category': 'IC', 'number': '1234', 'line': None}
        }

        for stop_type in ['NONE', 'TECHNICAL', 'PASSENGER']:
            event = JourneyEvent(**{**base_data, 'stopType': stop_type})
            assert event.stopType == stop_type

    def test_event_types(self):
        """Test both event types: ARRIVAL and DEPARTURE."""
        base_data = {
            'id': 'test-123',
            'cancelled': False,
            'additional': False,
            'stopPlace': {'id': 'station-1', 'name': 'Test Station'},
            'scheduledTime': '2024-01-01T12:00:00.000Z',
            'realtimeTime': '2024-01-01T12:00:00.000Z',
            'realtimeTimeType': 'SCHEDULE',
            'stopType': 'PASSENGER',
            'transport': {'category': 'IC', 'number': '1234', 'line': None}
        }

        for event_type in ['ARRIVAL', 'DEPARTURE']:
            event = JourneyEvent(**{**base_data, 'type': event_type})
            assert event.type == event_type

    def test_realtime_time_types(self):
        """Test all three realtime time types: SCHEDULE, PREDICTION, REAL."""
        base_data = {
            'id': 'test-123',
            'type': 'ARRIVAL',
            'cancelled': False,
            'additional': False,
            'stopPlace': {'id': 'station-1', 'name': 'Test Station'},
            'scheduledTime': '2024-01-01T12:00:00.000Z',
            'realtimeTime': '2024-01-01T12:00:00.000Z',
            'stopType': 'PASSENGER',
            'transport': {'category': 'IC', 'number': '1234', 'line': None}
        }

        for time_type in ['SCHEDULE', 'PREDICTION', 'REAL']:
            event = JourneyEvent(**{**base_data, 'realtimeTimeType': time_type})
            assert event.realtimeTimeType == time_type


class TestDelayInfo:
    """Tests for DelayInfo model."""

    def test_create_delay_info(self):
        """Test creating a DelayInfo instance."""
        delay = DelayInfo(
            station_name='Test Station',
            event_type='ARRIVAL',
            scheduled_time='2024-01-01T12:00:00.000Z',
            realtime_time='2024-01-01T12:02:00.000Z',
            delay_seconds=120,
            delay_minutes=2.0,
            status='delayed',
            time_type='PREDICTION',
            stop_type='PASSENGER'
        )

        assert delay.station_name == 'Test Station'
        assert delay.event_type == 'ARRIVAL'
        assert delay.delay_seconds == 120
        assert delay.delay_minutes == 2.0
        assert delay.status == 'delayed'
        assert delay.stop_type == 'PASSENGER'

    def test_delay_status_types(self):
        """Test all delay status types: on_time, delayed, early."""
        base_data = {
            'station_name': 'Test Station',
            'event_type': 'ARRIVAL',
            'scheduled_time': '2024-01-01T12:00:00.000Z',
            'realtime_time': '2024-01-01T12:00:00.000Z',
            'delay_seconds': 0,
            'delay_minutes': 0.0,
            'time_type': 'PREDICTION',
            'stop_type': 'PASSENGER'
        }

        for status in ['on_time', 'delayed', 'early']:
            delay = DelayInfo(**{**base_data, 'status': status})
            assert delay.status == status

    def test_datetime_formatting(self):
        """Test that datetime fields can be formatted with strftime."""
        delay = DelayInfo(
            station_name='Test Station',
            event_type='ARRIVAL',
            scheduled_time='2024-01-01T12:30:00.000Z',
            realtime_time='2024-01-01T12:35:00.000Z',
            delay_seconds=300,
            delay_minutes=5.0,
            status='delayed',
            time_type='PREDICTION',
            stop_type='PASSENGER'
        )

        scheduled_str = delay.scheduled_time.strftime("%H:%M")
        realtime_str = delay.realtime_time.strftime("%H:%M")

        assert scheduled_str == "12:30"
        assert realtime_str == "12:35"


class TestJourney:
    """Tests for Journey model."""

    def test_create_journey(self):
        """Test creating a Journey with events."""
        journey_data = {
            'journeyId': 'journey-123',
            'serverId': 'server-456',
            'lastUpdated': '2024-01-01T12:00:00.000Z',
            'journeyCancelled': False,
            'events': [
                {
                    'id': 'event-1',
                    'type': 'ARRIVAL',
                    'cancelled': False,
                    'additional': False,
                    'stopPlace': {'id': 'station-1', 'name': 'Station A'},
                    'scheduledTime': '2024-01-01T12:00:00.000Z',
                    'realtimeTime': '2024-01-01T12:00:00.000Z',
                    'realtimeTimeType': 'SCHEDULE',
                    'stopType': 'PASSENGER',
                    'transport': {'category': 'IC', 'number': '1234', 'line': None}
                },
                {
                    'id': 'event-2',
                    'type': 'DEPARTURE',
                    'cancelled': False,
                    'additional': False,
                    'stopPlace': {'id': 'station-1', 'name': 'Station A'},
                    'scheduledTime': '2024-01-01T12:05:00.000Z',
                    'realtimeTime': '2024-01-01T12:05:00.000Z',
                    'realtimeTimeType': 'SCHEDULE',
                    'stopType': 'PASSENGER',
                    'transport': {'category': 'IC', 'number': '1234', 'line': None}
                }
            ]
        }

        journey = Journey(**journey_data)

        assert journey.journeyId == 'journey-123'
        assert journey.serverId == 'server-456'
        assert len(journey.events) == 2
        assert journey.events[0].type == 'ARRIVAL'
        assert journey.events[1].type == 'DEPARTURE'
