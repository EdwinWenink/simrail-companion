from datetime import datetime
from typing import TypedDict


class TrainSession(TypedDict):
    id: str
    steam_id: str
    server_code: str
    server_name: str
    train_number: str
    train_name: str
    start_station: str
    end_station: str
    vehicle: str
    joined_at: datetime
    left_at: datetime | None
    distance_meters: int | None
    points: int | None


class StationSession(TypedDict):
    id: str
    steam_id: str
    server_code: str
    server_name: str
    station_name: str
    station_prefix: str
    joined_at: datetime
    left_at: datetime | None


class PlayerStats(TypedDict):
    total_distance_meters: int
    total_points: int
    total_train_time_seconds: int
    total_dispatcher_time_seconds: int
    train_sessions: int
    station_sessions: int
    trains_by_type: dict[str, dict[str, int]]  # vehicle -> {distance, points, time}
    stations_by_name: dict[str, int]  # station -> time_seconds
