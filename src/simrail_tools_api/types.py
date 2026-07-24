from datetime import datetime
from typing import Literal

from pydantic import BaseModel

# Type aliases for reused Literals
EventType = Literal["ARRIVAL", "DEPARTURE"]
StopType = Literal["NONE", "TECHNICAL", "PASSENGER"]
RealtimeTimeType = Literal["SCHEDULE", "PREDICTION", "REAL"]
DelayStatus = Literal["on_time", "delayed", "early"]
TransportType = Literal[
    "NATIONAL_EXPRESS_TRAIN",
    "INTER_NATIONAL_EXPRESS_TRAIN",
    "INTER_REGIONAL_EXPRESS_TRAIN",
    "INTER_REGIONAL_TRAIN",
    "REGIONAL_FAST_TRAIN",
    "REGIONAL_TRAIN",
    "ADDITIONAL_TRAIN",
    "MANEUVER_TRAIN",
    "EMPTY_TRANSFER_TRAIN",
    "INTER_NATIONAL_CARGO_TRAIN",
    "NATIONAL_CARGO_TRAIN",
    "MAINTENANCE_TRAIN",
]


class JourneyTransport(BaseModel):
    category: str
    categoryExternal: str | None = None
    number: str
    line: str | None = None
    label: str | None = None
    type: TransportType
    maxSpeed: int


class JourneyStopPlace(BaseModel):
    id: str
    name: str


class JourneyStopInfo(BaseModel):
    """Information about a passenger stop (platform and track)."""

    platform: int
    track: int


class GeoPosition(BaseModel):
    """Geographic position with latitude and longitude."""

    latitude: float
    longitude: float


class JourneyEvent(BaseModel):
    id: str
    type: EventType
    cancelled: bool
    additional: bool
    stopPlace: JourneyStopPlace
    scheduledTime: datetime
    realtimeTime: datetime
    realtimeTimeType: RealtimeTimeType
    stopType: StopType
    scheduledPassengerStop: JourneyStopInfo | None = None
    realtimePassengerStop: JourneyStopInfo | None = None
    transport: JourneyTransport


class JourneyLiveData(BaseModel):
    speed: int
    position: GeoPosition
    driver: dict | None = None  # Driver information when available
    nextSignal: dict | None = None  # Next signal information when available


class Journey(BaseModel):
    journeyId: str
    serverId: str
    lastUpdated: str
    firstSeenTime: str | None = None
    lastSeenTime: str | None = None
    journeyCancelled: bool
    liveData: JourneyLiveData | None = None
    events: list[JourneyEvent]


class DelayInfo(BaseModel):
    station_name: str
    event_type: EventType
    scheduled_time: datetime
    realtime_time: datetime
    delay_seconds: int
    delay_minutes: float
    status: DelayStatus
    time_type: RealtimeTimeType
    stop_type: StopType
