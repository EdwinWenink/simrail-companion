from typing import Literal, TypedDict


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
    ControlledBySteamID: str | None
    ControlledByXboxID: str | None
    Velocity: float
    DistanceToSignalInFront: float
    SignalInFront: str | None
    SignalInFrontSpeed: float
    RequiredMapDLCs: list[str] | None


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
    train_number: str | None
    train_name: str | None
    start_station: str | None
    end_station: str | None
    vehicles: list[str] | None
    velocity: float | None
    signal_in_front: str | None
    distance_to_signal: float | None
    signal_speed_limit: float | None
    run_id: str | None
    # For stations
    station_name: str | None
    station_prefix: str | None
