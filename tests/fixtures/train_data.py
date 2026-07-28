"""Test fixtures for train and station data."""

import pytest


@pytest.fixture
def train_activity():
    """Active train session data."""
    return {
        "activity_type": "train",
        "train_number": "6162",
        "train_name": "TLK 6162",
        "start_station": "Warszawa Wschodnia",
        "end_station": "Katowice",
        "server_code": "en1",
        "server_name": "EN1",
        "vehicles": ["EU07-096"],
        "velocity": 100.0,
        "signal_in_front": "WsE_Sg12",
        "distance_to_signal": 1200.0,
        "signal_speed_limit": 100.0,
    }


@pytest.fixture
def station_activity():
    """Active dispatcher session data."""
    return {
        "activity_type": "station",
        "station_name": "Warszawa Wschodnia",
        "station_prefix": "WsE",
        "server_code": "en1",
        "server_name": "EN1",
    }


@pytest.fixture
def vehicle_composition():
    """Complete vehicle composition data."""
    return {
        "traction_type": "LOCOMOTIVE",
        "transport": {
            "category": "TLK",
            "category_external": None,
            "number": "6162",
            "line": None,
            "label": "TLK 6162",
            "type": "PASSENGER",
            "max_speed": 160,
        },
        "locomotives": [
            {
                "displayName": "EU07 096",
                "typeIdentifier": "eu07",
            }
        ],
        "emus": [],
        "vehicles": [
            {
                "indexInGroup": 0,
                "id": "eu07-096",
                "displayName": "EU07 096",
                "name": None,
                "type": "LOCOMOTIVE",
                "typeIdentifier": "eu07",
                "designation": "EU07",
                "producer": "Pafawag Wrocław",
                "productionYears": "1964-1974",
                "weight": 80.0,
                "length": 15.9,
                "maxSpeed": 125,
                "loadWeight": None,
                "load": None,
            },
            {
                "indexInGroup": 1,
                "id": "wagon-1",
                "displayName": "Type 111A Coach",
                "name": None,
                "type": "WAGON",
                "typeIdentifier": "111a",
                "designation": "111A",
                "producer": None,
                "productionYears": None,
                "weight": 40.0,
                "length": 24.5,
                "maxSpeed": 160,
                "loadWeight": 0,
                "load": None,
            },
        ],
        "num_wagons": 1,
        "total_vehicles": 2,
        "total_length": 40.4,
        "total_weight": 120.0,
    }


@pytest.fixture
def double_headed_composition():
    """Double-headed locomotive composition."""
    return {
        "traction_type": "LOCOMOTIVE",
        "transport": {
            "category": "TLK",
            "category_external": None,
            "number": "3902",
            "line": None,
            "label": "TLK 3902",
            "type": "FREIGHT",
            "max_speed": 100,
        },
        "locomotives": [
            {
                "displayName": "EU07 096",
                "typeIdentifier": "eu07",
            },
            {
                "displayName": "EU07 193",
                "typeIdentifier": "eu07",
            },
        ],
        "emus": [],
        "vehicles": [
            {
                "indexInGroup": 0,
                "id": "eu07-096",
                "displayName": "EU07 096",
                "name": None,
                "type": "LOCOMOTIVE",
                "typeIdentifier": "eu07",
                "designation": "EU07",
                "producer": "Pafawag Wrocław",
                "productionYears": "1964-1974",
                "weight": 80.0,
                "length": 15.9,
                "maxSpeed": 125,
                "loadWeight": None,
                "load": None,
            },
            {
                "indexInGroup": 1,
                "id": "eu07-193",
                "displayName": "EU07 193",
                "name": None,
                "type": "LOCOMOTIVE",
                "typeIdentifier": "eu07",
                "designation": "EU07",
                "producer": "Pafawag Wrocław",
                "productionYears": "1964-1974",
                "weight": 80.0,
                "length": 15.9,
                "maxSpeed": 125,
                "loadWeight": None,
                "load": None,
            },
        ],
        "num_wagons": 0,
        "total_vehicles": 2,
        "total_length": 31.8,
        "total_weight": 160.0,
    }


@pytest.fixture
def steam_stats():
    """Mock Steam stats."""
    return {
        "DISTANCE_M": 150000,
        "SCORE": 12500,
        "DISPATCHER_TIME": 120,
    }


@pytest.fixture
def train_session_db_entry():
    """Database entry for a completed train session."""
    return {
        "id": "test-session-123",
        "steam_id": "76561198012345678",
        "server_code": "en1",
        "server_name": "EN1",
        "train_number": "6162",
        "train_name": "TLK 6162",
        "start_station": "Warszawa Wschodnia",
        "end_station": "Katowice",
        "joined_at": "2026-07-28T14:00:00+00:00",
        "left_at": "2026-07-28T16:30:00+00:00",
        "distance_meters": 15000,
        "points": 1250,
        "baseline_distance": 150000,
        "baseline_points": 12500,
        "vehicle_summary": "EU07 096",
        "traction_type": "LOCOMOTIVE",
        "transport_type": "PASSENGER",
        "traction_name": "EU07 096",
        "num_locomotives": 1,
        "num_wagons": 8,
        "total_vehicles": 9,
        "total_length": 200.0,
        "total_weight": 400.0,
        "composition_json": None,
    }
