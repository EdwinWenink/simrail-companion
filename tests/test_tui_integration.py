"""Integration tests for TUI dashboard with mocked data.

These tests demonstrate the testing approach but are disabled by default
because they need refinement for Textual's async lifecycle.

To enable, remove the @pytest.mark.skip decorators and run:
    uv run pytest tests/test_tui_integration.py -v
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from player_tracker.database import TrackerDatabase
from player_tracker.tui import TrackerDashboard


@pytest.fixture
def test_db(tmp_path):
    """Create a test database."""
    db_path = tmp_path / "test.db"
    db = TrackerDatabase(str(db_path))
    return db, str(db_path)


@pytest.fixture
def mock_tracker_offline(test_db):
    """Mock tracker with player offline."""
    _, db_path = test_db

    mock = MagicMock()
    mock.current_activity = None  # Player offline
    mock.current_journey_id = None
    mock.steam_id = "76561198012345678"
    mock.db_path = db_path
    mock.db = MagicMock()

    # Mock API clients
    mock.simrail_client = AsyncMock()
    mock.simrail_tools_client = AsyncMock()
    mock.steam_client = AsyncMock()

    return mock


@pytest.fixture
def mock_tracker_active_train(test_db):
    """Mock tracker with player on active train."""
    db, db_path = test_db

    # Create vehicle composition
    composition = {
        "traction_type": "LOCOMOTIVE",
        "transport": {
            "category": "TLK",
            "number": "6162",
            "type": "PASSENGER",
            "max_speed": 160,
        },
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

    # Create active train session in DB
    session_id = db.create_train_session(
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
        vehicle_composition=composition,
    )

    mock = MagicMock()
    mock.current_activity = {
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
    mock.current_journey_id = "test-journey-123"
    mock.steam_id = "76561198012345678"
    mock.db_path = db_path
    mock.running = True
    mock.db = db

    # Mock API clients
    mock.simrail_client = AsyncMock()
    mock.simrail_tools_client = AsyncMock()
    mock.steam_client = AsyncMock()

    return mock, session_id


@pytest.mark.skip(reason="TUI integration tests need refinement - see docs/TESTING_GUIDE.md")
@pytest.mark.asyncio
async def test_dashboard_loads_with_offline_player(mock_tracker_offline):
    """Test that dashboard loads when player is offline.

    NOTE: Skipped - needs proper mocking of on_mount to prevent PlayerTracker creation.
    """
    with patch("player_tracker.tui.PlayerTracker") as MockTracker:
        MockTracker.return_value = mock_tracker_offline

        app = TrackerDashboard(
            steam_id="76561198012345678",
            db_path=mock_tracker_offline.db_path,
        )

        async with app.run_test() as pilot:
            await pilot.pause()

            # Check that title is set
            assert app.title == "SimRail Tracker - 76561198012345678"

            # Check session panel shows offline message
            session_panel = app.query_one("#session-panel")
            assert "offline" in session_panel.session_info.lower()


@pytest.mark.skip(reason="TUI integration tests need refinement - see docs/TESTING_GUIDE.md")
@pytest.mark.asyncio
async def test_dashboard_shows_active_train(mock_tracker_active_train):
    """Test dashboard displays active train session correctly.

    NOTE: Skipped - needs proper async lifecycle handling.
    """
    mock_tracker, _ = mock_tracker_active_train

    with patch("player_tracker.tui.PlayerTracker") as MockTracker:
        MockTracker.return_value = mock_tracker

        app = TrackerDashboard(
            steam_id="76561198012345678",
            db_path=mock_tracker.db_path,
        )

        async with app.run_test() as pilot:
            await pilot.pause()

            # Check session panel shows train info
            session_panel = app.query_one("#session-panel")
            assert "6162" in session_panel.session_info
            assert "TLK 6162" in session_panel.session_info
