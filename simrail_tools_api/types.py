from typing import TypedDict, Optional, Literal


class JourneyTransport(TypedDict):
    category: str
    number: str
    line: Optional[str]


class JourneyStopPlace(TypedDict):
    id: str
    name: str


class JourneyEvent(TypedDict):
    id: str
    type: Literal["ARRIVAL", "DEPARTURE"]
    cancelled: bool
    additional: bool
    stopPlace: JourneyStopPlace
    scheduledTime: str  # ISO-8601
    realtimeTime: str  # ISO-8601
    realtimeTimeType: Literal["SCHEDULE", "PREDICTION", "REAL"]
    stopType: Literal["NONE", "TECHNICAL", "PASSENGER"]
    transport: JourneyTransport


class JourneyLiveData(TypedDict):
    speed: int
    position: dict  # GeoPosition


class Journey(TypedDict):
    journeyId: str
    serverId: str
    lastUpdated: str
    firstSeenTime: Optional[str]
    lastSeenTime: Optional[str]
    journeyCancelled: bool
    liveData: Optional[JourneyLiveData]
    events: list[JourneyEvent]


class DelayInfo(TypedDict):
    station_name: str
    event_type: Literal["ARRIVAL", "DEPARTURE"]
    scheduled_time: str
    realtime_time: str
    delay_seconds: int
    delay_minutes: float
    status: Literal["on_time", "delayed", "early"]
    time_type: Literal["SCHEDULE", "PREDICTION", "REAL"]
