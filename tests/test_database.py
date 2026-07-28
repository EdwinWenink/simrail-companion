"""Tests for database operations."""

import pytest

from player_tracker.database import TrackerDatabase


@pytest.fixture
def test_db(tmp_path):
    """Create a test database."""
    db_path = tmp_path / "test.db"
    return TrackerDatabase(str(db_path))


class TestTrainSessions:
    """Tests for train session operations."""

    def test_create_train_session(self, test_db):
        """Test creating a train session."""
        session_id = test_db.create_train_session(
            steam_id="76561198012345678",
            server_code="en1",
            server_name="EN1",
            train_number="6162",
            train_name="TLK 6162",
            start_station="Warszawa Wschodnia",
            end_station="Katowice",
            vehicle="EU07 096",
            baseline_distance=150000,
            baseline_points=12500,
        )

        assert session_id is not None
        assert isinstance(session_id, str)

    def test_get_active_train_session(self, test_db):
        """Test retrieving active train session."""
        # Create a session
        session_id = test_db.create_train_session(
            steam_id="76561198012345678",
            server_code="en1",
            server_name="EN1",
            train_number="6162",
            train_name="TLK 6162",
            start_station="Warszawa Wschodnia",
            end_station="Katowice",
            vehicle="EU07 096",
        )

        # Retrieve it
        active = test_db.get_active_train_session("76561198012345678")

        assert active is not None
        assert active["id"] == session_id
        assert active["train_number"] == "6162"
        assert active["left_at"] is None  # Still active

    def test_end_train_session(self, test_db):
        """Test ending a train session."""
        # Create a session
        session_id = test_db.create_train_session(
            steam_id="76561198012345678",
            server_code="en1",
            server_name="EN1",
            train_number="6162",
            train_name="TLK 6162",
            start_station="Warszawa Wschodnia",
            end_station="Katowice",
            vehicle="EU07 096",
        )

        # End it
        test_db.end_train_session(session_id, distance_meters=15000, points=1250)

        # Verify it's ended
        session = test_db.get_train_session_by_id(session_id)
        assert session["left_at"] is not None
        assert session["distance_meters"] == 15000
        assert session["points"] == 1250

    def test_get_train_sessions(self, test_db):
        """Test retrieving train session list."""
        # Create multiple sessions
        for i in range(3):
            test_db.create_train_session(
                steam_id="76561198012345678",
                server_code="en1",
                server_name="EN1",
                train_number=f"616{i}",
                train_name=f"TLK 616{i}",
                start_station="Warszawa Wschodnia",
                end_station="Katowice",
                vehicle="EU07 096",
            )

        # Retrieve sessions
        sessions = test_db.get_train_sessions("76561198012345678", limit=10)

        assert len(sessions) == 3
        # Most recent first
        assert sessions[0]["train_number"] == "6162"


class TestStationSessions:
    """Tests for station session operations."""

    def test_create_station_session(self, test_db):
        """Test creating a station session."""
        session_id = test_db.create_station_session(
            steam_id="76561198012345678",
            server_code="en1",
            server_name="EN1",
            station_name="Warszawa Wschodnia",
            station_prefix="WsE",
            point_id="ws-east-point-123",
        )

        assert session_id is not None
        assert isinstance(session_id, str)

    def test_get_active_station_session(self, test_db):
        """Test retrieving active station session."""
        session_id = test_db.create_station_session(
            steam_id="76561198012345678",
            server_code="en1",
            server_name="EN1",
            station_name="Warszawa Wschodnia",
            station_prefix="WsE",
        )

        active = test_db.get_active_station_session("76561198012345678")

        assert active is not None
        assert active["id"] == session_id
        assert active["station_name"] == "Warszawa Wschodnia"

    def test_end_station_session(self, test_db):
        """Test ending a station session."""
        session_id = test_db.create_station_session(
            steam_id="76561198012345678",
            server_code="en1",
            server_name="EN1",
            station_name="Warszawa Wschodnia",
            station_prefix="WsE",
        )

        test_db.end_station_session(session_id)

        # Verify it's ended
        active = test_db.get_active_station_session("76561198012345678")
        assert active is None  # No active session


class TestStats:
    """Tests for statistics aggregation."""

    def test_empty_stats(self, test_db):
        """Test stats for user with no sessions."""
        stats = test_db.get_stats("76561198012345678")

        assert stats["total_distance_meters"] == 0
        assert stats["total_points"] == 0
        assert stats["train_sessions"] == 0
        assert stats["station_sessions"] == 0

    def test_stats_with_sessions(self, test_db):
        """Test stats calculation with completed sessions."""
        # Create and complete a train session
        session_id = test_db.create_train_session(
            steam_id="76561198012345678",
            server_code="en1",
            server_name="EN1",
            train_number="6162",
            train_name="TLK 6162",
            start_station="Warszawa Wschodnia",
            end_station="Katowice",
            vehicle="EU07 096",
        )
        test_db.end_train_session(session_id, distance_meters=15000, points=1250)

        # Get stats
        stats = test_db.get_stats("76561198012345678")

        assert stats["total_distance_meters"] == 15000
        assert stats["total_points"] == 1250
        assert stats["train_sessions"] == 1


class TestSteamStats:
    """Tests for Steam stats operations."""

    def test_save_steam_stats(self, test_db):
        """Test saving Steam stats."""
        test_db.save_steam_stats(
            steam_id="76561198012345678",
            score=12500,
            distance_meters=150000,
            dispatcher_time_minutes=120,
        )

        latest = test_db.get_latest_steam_stats("76561198012345678")

        assert latest is not None
        assert latest["total_score"] == 12500
        assert latest["total_distance_meters"] == 150000

    def test_steam_stats_history(self, test_db):
        """Test retrieving Steam stats history."""
        # Save multiple snapshots
        for i in range(3):
            test_db.save_steam_stats(
                steam_id="76561198012345678",
                score=10000 + i * 1000,
                distance_meters=100000 + i * 10000,
                dispatcher_time_minutes=100 + i * 10,
            )

        history = test_db.get_steam_stats_history("76561198012345678", limit=10)

        assert len(history) == 3
        # Most recent first
        assert history[0]["total_score"] == 12000


class TestVehicleComposition:
    """Tests for vehicle composition storage."""

    def test_store_composition(self, test_db):
        """Test storing vehicle composition data."""
        composition = {
            "traction_type": "LOCOMOTIVE",
            "locomotives": [{"displayName": "EU07 096", "typeIdentifier": "eu07"}],
            "emus": [],
            "vehicles": [
                {
                    "indexInGroup": 0,
                    "displayName": "EU07 096",
                    "type": "LOCOMOTIVE",
                    "weight": 80.0,
                    "length": 15.9,
                }
            ],
            "num_wagons": 0,
            "total_vehicles": 1,
            "total_length": 15.9,
            "total_weight": 80.0,
        }

        session_id = test_db.create_train_session(
            steam_id="76561198012345678",
            server_code="en1",
            server_name="EN1",
            train_number="6162",
            train_name="TLK 6162",
            start_station="Warszawa Wschodnia",
            end_station="Katowice",
            vehicle="EU07 096",
            vehicle_composition=composition,
        )

        # Retrieve and verify
        session = test_db.get_train_session_by_id(session_id)

        assert session["vehicle_summary"] == "EU07 096"
        assert session["traction_type"] == "LOCOMOTIVE"
        assert session["num_locomotives"] == 1
        assert session["total_weight"] == 80.0
        assert session["composition_json"] is not None
