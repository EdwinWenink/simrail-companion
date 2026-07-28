"""Tests for formatting utilities."""

from player_tracker.formatting import (
    format_datetime,
    format_distance,
    format_duration,
    format_signal_distance,
    format_signal_limit,
    format_time,
    format_vehicle_info,
    get_signal_aspect,
)


class TestFormatDuration:
    """Tests for format_duration()."""

    def test_none_returns_dash(self):
        assert format_duration(None) == "—"

    def test_seconds_only(self):
        assert format_duration(45) == "45s"

    def test_minutes_and_seconds(self):
        assert format_duration(125) == "2m 5s"

    def test_hours_and_minutes(self):
        assert format_duration(3665) == "1h 1m"

    def test_zero_seconds(self):
        assert format_duration(0) == "0s"

    def test_exactly_one_hour(self):
        assert format_duration(3600) == "1h 0m"


class TestFormatDistance:
    """Tests for format_distance()."""

    def test_none_returns_dash(self):
        assert format_distance(None) == "—"

    def test_meters_to_kilometers(self):
        assert format_distance(1500) == "1.50 km"

    def test_large_distance(self):
        assert format_distance(123456) == "123.46 km"

    def test_zero_distance(self):
        assert format_distance(0) == "0.00 km"


class TestFormatTime:
    """Tests for format_time()."""

    def test_none_returns_dash(self):
        assert format_time(None) == "—"

    def test_empty_string_returns_dash(self):
        assert format_time("") == "—"

    def test_iso_timestamp(self):
        result = format_time("2026-07-28T14:30:45")
        assert result == "14:30:45"

    def test_iso_timestamp_with_timezone(self):
        result = format_time("2026-07-28T14:30:45+00:00")
        assert result == "14:30:45"

    def test_invalid_timestamp_returns_dash(self):
        assert format_time("invalid") == "—"


class TestFormatDatetime:
    """Tests for format_datetime()."""

    def test_iso_datetime(self):
        result = format_datetime("2026-07-28T14:30:45")
        assert result == "2026-07-28 14:30:45"

    def test_iso_datetime_with_timezone(self):
        result = format_datetime("2026-07-28T14:30:45+00:00")
        assert result == "2026-07-28 14:30:45"


class TestGetSignalAspect:
    """Tests for get_signal_aspect()."""

    def test_none_returns_no_data(self):
        assert get_signal_aspect(None) == "⚪ No data"

    def test_zero_speed_is_stop(self):
        assert get_signal_aspect(0) == "🔴 Stop"

    def test_slow_speeds(self):
        assert get_signal_aspect(40) == "🟠🟠 Slow"
        assert get_signal_aspect(60) == "🟠🟠 Slow"

    def test_clear_speeds(self):
        assert get_signal_aspect(80) == "🟢🟠 Clear"
        assert get_signal_aspect(100) == "🟢🟠 Clear"

    def test_vmax_speeds(self):
        assert get_signal_aspect(120) == "🟢 vmax"
        assert get_signal_aspect(32767) == "🟢 vmax"

    def test_unknown_speed(self):
        # Edge case: speed between categories
        assert get_signal_aspect(70) == "⚪ Unknown"


class TestFormatSignalDistance:
    """Tests for format_signal_distance()."""

    def test_none_returns_dash(self):
        assert format_signal_distance(None) == "—"

    def test_meters_under_1km(self):
        assert format_signal_distance(500) == "500 m"

    def test_meters_over_1km(self):
        assert format_signal_distance(1500) == "1.50 km"

    def test_zero_distance(self):
        assert format_signal_distance(0) == "0 m"


class TestFormatSignalLimit:
    """Tests for format_signal_limit()."""

    def test_none_returns_dash(self):
        assert format_signal_limit(None) == "—"

    def test_vmax_constant(self):
        assert format_signal_limit(32767) == "vmax"

    def test_normal_speed(self):
        assert format_signal_limit(120) == "120 km/h"

    def test_zero_speed(self):
        assert format_signal_limit(0) == "0 km/h"


class TestFormatVehicleInfo:
    """Tests for format_vehicle_info()."""

    def test_vehicle_summary_only(self):
        session = {"vehicle_summary": "EU07 096"}
        assert format_vehicle_info(session) == "EU07 096"

    def test_with_weight(self):
        session = {"vehicle_summary": "EU07 096", "total_weight": 450.5}
        assert format_vehicle_info(session) == "EU07 096 (450t)"

    def test_with_length(self):
        session = {"vehicle_summary": "EU07 096", "total_length": 200.7}
        assert format_vehicle_info(session) == "EU07 096 • 200.7m"

    def test_with_weight_and_length(self):
        session = {
            "vehicle_summary": "EU07 096",
            "total_weight": 450.5,
            "total_length": 200.7,
        }
        assert format_vehicle_info(session) == "EU07 096 (450t) • 200.7m"

    def test_missing_vehicle_summary(self):
        session = {}
        assert format_vehicle_info(session) == "Unknown"
