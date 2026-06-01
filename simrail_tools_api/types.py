from typing import Optional, Literal
from datetime import datetime
from pydantic import BaseModel

# Type aliases for reused Literals
EventType = Literal["ARRIVAL", "DEPARTURE"]
StopType = Literal["NONE", "TECHNICAL", "PASSENGER"]
RealtimeTimeType = Literal["SCHEDULE", "PREDICTION", "REAL"]
DelayStatus = Literal["on_time", "delayed", "early"]


class JourneyTransport(BaseModel):
    category: str
    number: str
    line: Optional[str] = None


class JourneyStopPlace(BaseModel):
    id: str
    name: str


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
    transport: JourneyTransport


class JourneyLiveData(BaseModel):
    speed: int
    position: dict  # GeoPosition


class Journey(BaseModel):
    journeyId: str
    serverId: str
    lastUpdated: str
    firstSeenTime: Optional[str] = None
    lastSeenTime: Optional[str] = None
    journeyCancelled: bool
    liveData: Optional[JourneyLiveData] = None
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
