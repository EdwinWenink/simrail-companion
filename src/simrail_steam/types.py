from typing import Literal, TypedDict


class PlayerSummary(TypedDict):
    steamid: str
    communityvisibilitystate: int
    profilestate: int
    personaname: str
    commentpermission: int
    profileurl: str
    avatar: str
    avatarmedium: str
    avatarfull: str
    avatarhash: str
    personastate: int
    primaryclanid: str
    timecreated: int
    personastateflags: int
    gameextrainfo: str
    gameid: str
    loccountrycode: str
    locstatecode: str


class StatValue(TypedDict):
    name: str
    value: int


class Achievement(TypedDict):
    name: str
    achieved: Literal[0, 1]


class PlayerStats(TypedDict):
    steamID: str
    gameName: str
    stats: list[StatValue]
    achievements: list[Achievement]


class SimRailStats(TypedDict):
    SCORE: int
    DISPATCHER_TIME: int
    DISTANCE_M: int
