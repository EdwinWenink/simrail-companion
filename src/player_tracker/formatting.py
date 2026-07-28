"""Shared formatting utilities for display formatting across the application."""

from datetime import datetime


def format_duration(seconds: float | None) -> str:
    """Format duration in seconds to human readable string.

    Args:
        seconds: Duration in seconds, or None

    Returns:
        Human-readable duration string (e.g., "2h 15m", "45m 30s", "—")
    """
    if seconds is None:
        return "—"
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}h {minutes}m"
    if minutes > 0:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def format_distance(meters: int | None) -> str:
    """Format distance in meters to kilometers.

    Args:
        meters: Distance in meters, or None

    Returns:
        Distance in km with 2 decimal places (e.g., "12.34 km", "—")
    """
    if meters is None:
        return "—"
    return f"{meters / 1000:.2f} km"


def format_time(iso_time: str | None) -> str:
    """Format ISO timestamp to HH:MM:SS.

    Args:
        iso_time: ISO 8601 timestamp string, or None

    Returns:
        Formatted time string (e.g., "14:23:45", "—")
    """
    if not iso_time:
        return "—"
    try:
        dt = datetime.fromisoformat(iso_time)
        return dt.strftime("%H:%M:%S")
    except Exception:
        return "—"


def format_datetime(dt_str: str) -> str:
    """Format ISO datetime string to readable format.

    Args:
        dt_str: ISO 8601 datetime string

    Returns:
        Formatted datetime (e.g., "2026-07-28 14:23:45")
    """
    dt = datetime.fromisoformat(dt_str)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


# Signal-related formatting utilities


def get_signal_aspect(speed_limit: float | None) -> str:
    """Determine signal aspect based on speed limit.

    Args:
        speed_limit: Speed limit in km/h, or None

    Returns:
        Signal aspect emoji string (e.g., "🟢 vmax", "🔴 Stop")
    """
    if speed_limit is None:
        return "⚪ No data"
    if speed_limit == 0:
        return "🔴 Stop"
    if speed_limit in [40, 60]:
        return "🟠🟠 Slow"
    if speed_limit in [80, 100]:
        return "🟢🟠 Clear"
    if speed_limit >= 32767 or speed_limit > 100:
        return "🟢 vmax"
    return "⚪ Unknown"


def format_signal_distance(distance: float | None) -> str:
    """Format signal distance.

    Args:
        distance: Distance in meters, or None

    Returns:
        Formatted distance (e.g., "1.23 km", "456 m", "—")
    """
    if distance is None:
        return "—"
    if distance >= 1000:
        return f"{distance / 1000:.2f} km"
    return f"{distance:.0f} m"


def format_signal_limit(speed_limit: float | None) -> str:
    """Format signal speed limit.

    Args:
        speed_limit: Speed limit in km/h, or None

    Returns:
        Formatted speed limit (e.g., "120 km/h", "vmax", "—")
    """
    if speed_limit is None:
        return "—"
    if speed_limit == 32767:
        return "vmax"
    return f"{speed_limit:.0f} km/h"


def format_vehicle_info(session: dict) -> str:
    """Format vehicle information with optional weight and length.

    Args:
        session: Session dictionary containing vehicle data

    Returns:
        Formatted vehicle string with weight/length if available
    """
    vehicle_info = session.get("vehicle_summary", "Unknown")
    if session.get("total_weight"):
        vehicle_info += f" ({session['total_weight']:.0f}t)"
    if session.get("total_length"):
        vehicle_info += f" • {session['total_length']:.1f}m"
    return vehicle_info
