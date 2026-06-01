from typing import Optional, Literal
from datetime import datetime
from pydantic import BaseModel


class JourneyTransport(BaseModel):
    category: str
    number: str
    line: Optional[str] = None


class JourneyStopPlace(BaseModel):
    id: str
    name: str


class JourneyEvent(BaseModel):
    id: str
    type: Literal["ARRIVAL", "DEPARTURE"]
    cancelled: bool
    additional: bool
    stopPlace: JourneyStopPlace
    scheduledTime: datetime
    realtimeTime: datetime
    realtimeTimeType: Literal["SCHEDULE", "PREDICTION", "REAL"]
    stopType: Literal["NONE", "TECHNICAL", "PASSENGER"]
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
    event_type: Literal["ARRIVAL", "DEPARTURE"]
    scheduled_time: datetime
    realtime_time: datetime
    delay_seconds: int
    delay_minutes: float
    status: Literal["on_time", "delayed", "early"]
    time_type: Literal["SCHEDULE", "PREDICTION", "REAL"]
    stop_type: Literal["NONE", "TECHNICAL", "PASSENGER"]
