from typing import TypedDict, Optional, Literal


class Server(TypedDict):
    id: str
    IsActive: bool
    ServerCode: str
    ServerName: str
    ServerRegion: str


class TrainData(TypedDict):
    InBorderStationArea: bool
    Latititute: float
    Longitute: float
    VDDelayedTimetableIndex: int
    ControlledBySteamID: Optional[str]
    ControlledByXboxID: Optional[str]
    Velocity: float
    DistanceToSignalInFront: float
    SignalInFront: Optional[str]
    SignalInFrontSpeed: float
    RequiredMapDLCs: Optional[list[str]]


class Train(TypedDict):
    id: str
    TrainNoLocal: str
    TrainName: str
    StartStation: str
    EndStation: str
    Vehicles: list[str]
    ServerCode: str
    TrainData: TrainData
    RunId: str
    Type: Literal["user", "bot"]


class DispatchedBy(TypedDict):
    ServerCode: str
    SteamId: str


class Station(TypedDict):
    id: str
    Name: str
    Prefix: str
    MainImageURL: str
    AdditionalImage1URL: str
    AdditionalImage2URL: str
    Latititude: float
    Longitude: float
    DifficultyLevel: int
    DispatchedBy: list[DispatchedBy]


class PlayerActivity(TypedDict):
    steam_id: str
    activity_type: Literal["train", "station"]
    server_code: str
    server_name: str
    # For trains
    train_number: Optional[str]
    train_name: Optional[str]
    start_station: Optional[str]
    end_station: Optional[str]
    vehicles: Optional[list[str]]
    velocity: Optional[float]
    signal_in_front: Optional[str]
    distance_to_signal: Optional[float]
    signal_speed_limit: Optional[float]
    run_id: Optional[str]
    # For stations
    station_name: Optional[str]
    station_prefix: Optional[str]
