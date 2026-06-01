"""Tests for extended Journey model fields."""
from simrail_tools_api.types import (
    JourneyEvent,
    JourneyStopInfo,
    GeoPosition,
    JourneyLiveData,
    Journey,
)



def get_default_transport():
    """Get default transport data for tests."""
    return {
        'category': 'IC',
        'categoryExternal': None,
        'number': '1234',
        'line': None,
        'label': None,
        'type': 'INTER_REGIONAL_TRAIN',
        'maxSpeed': 160
    }


class TestJourneyStopInfo:
    """Tests for JourneyStopInfo model."""

    def test_create_stop_info(self):
        """Test creating a JourneyStopInfo instance."""
        stop_info = JourneyStopInfo(platform=2, track=3)

        assert stop_info.platform == 2
        assert stop_info.track == 3


class TestGeoPosition:
    """Tests for GeoPosition model."""

    def test_create_geo_position(self):
        """Test creating a GeoPosition instance."""
        position = GeoPosition(latitude=52.2297, longitude=21.0122)

        assert position.latitude == 52.2297
        assert position.longitude == 21.0122

    def test_geo_position_accepts_floats(self):
        """Test that GeoPosition accepts float values."""
        position = GeoPosition(latitude=50.5, longitude=19.25)

        assert isinstance(position.latitude, float)
        assert isinstance(position.longitude, float)


class TestJourneyLiveData:
    """Tests for JourneyLiveData model."""

    def test_create_live_data_minimal(self):
        """Test creating JourneyLiveData with minimal required fields."""
        live_data = JourneyLiveData(
            speed=100,
            position=GeoPosition(latitude=52.0, longitude=21.0)
        )

        assert live_data.speed == 100
        assert live_data.position.latitude == 52.0
        assert live_data.position.longitude == 21.0
        assert live_data.driver is None
        assert live_data.nextSignal is None

    def test_create_live_data_with_optional_fields(self):
        """Test creating JourneyLiveData with optional fields."""
        live_data = JourneyLiveData(
            speed=80,
            position=GeoPosition(latitude=51.0, longitude=20.0),
            driver={"steamId": "76561198012345678"},
            nextSignal={"id": "SBL_A", "distance": 500}
        )

        assert live_data.speed == 80
        assert live_data.driver["steamId"] == "76561198012345678"
        assert live_data.nextSignal["id"] == "SBL_A"


class TestJourneyEventExtended:
    """Tests for extended JourneyEvent fields."""

    def test_event_without_passenger_stops(self):
        """Test event for pass-through station (no passenger stops)."""
        event_data = {
            'id': 'event-1',
            'type': 'ARRIVAL',
            'cancelled': False,
            'additional': False,
            'stopPlace': {'id': 'station-1', 'name': 'Pass Through Station'},
            'scheduledTime': '2024-01-01T12:00:00.000Z',
            'realtimeTime': '2024-01-01T12:00:00.000Z',
            'realtimeTimeType': 'PREDICTION',
            'stopType': 'NONE',
            'transport': get_default_transport()
        }

        event = JourneyEvent(**event_data)

        assert event.scheduledPassengerStop is None
        assert event.realtimePassengerStop is None

    def test_event_with_passenger_stops(self):
        """Test event with scheduled and realtime passenger stop info."""
        event_data = {
            'id': 'event-2',
            'type': 'ARRIVAL',
            'cancelled': False,
            'additional': False,
            'stopPlace': {'id': 'station-2', 'name': 'Main Station'},
            'scheduledTime': '2024-01-01T12:00:00.000Z',
            'realtimeTime': '2024-01-01T12:02:00.000Z',
            'realtimeTimeType': 'PREDICTION',
            'stopType': 'PASSENGER',
            'scheduledPassengerStop': {'platform': 1, 'track': 2},
            'realtimePassengerStop': {'platform': 1, 'track': 3},
            'transport': get_default_transport()
        }

        event = JourneyEvent(**event_data)

        assert event.scheduledPassengerStop is not None
        assert event.scheduledPassengerStop.platform == 1
        assert event.scheduledPassengerStop.track == 2

        assert event.realtimePassengerStop is not None
        assert event.realtimePassengerStop.platform == 1
        assert event.realtimePassengerStop.track == 3


class TestJourneyExtended:
    """Tests for extended Journey model."""

    def test_journey_with_live_data(self):
        """Test Journey with live data included."""
        journey_data = {
            'journeyId': 'journey-123',
            'serverId': 'server-456',
            'lastUpdated': '2024-01-01T12:00:00.000Z',
            'journeyCancelled': False,
            'liveData': {
                'speed': 120,
                'position': {'latitude': 52.2297, 'longitude': 21.0122},
                'driver': {'steamId': '76561198012345678'},
                'nextSignal': None
            },
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
                    'transport': get_default_transport()
                }
            ]
        }

        journey = Journey(**journey_data)

        assert journey.liveData is not None
        assert journey.liveData.speed == 120
        assert journey.liveData.position.latitude == 52.2297
        assert journey.liveData.driver['steamId'] == '76561198012345678'

    def test_journey_without_live_data(self):
        """Test Journey without live data (inactive journey)."""
        journey_data = {
            'journeyId': 'journey-456',
            'serverId': 'server-789',
            'lastUpdated': '2024-01-01T12:00:00.000Z',
            'journeyCancelled': False,
            'events': []
        }

        journey = Journey(**journey_data)

        assert journey.liveData is None
