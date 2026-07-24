import asyncio
import logging

import aiohttp

from .types import PlayerActivity, Server, Station, Train

logger = logging.getLogger(__name__)


class SimRailClient:
    BASE_URL = "https://panel.simrail.eu:8084"
    DEFAULT_TIMEOUT = 10

    def __init__(self, timeout: int = DEFAULT_TIMEOUT):
        self.timeout = timeout

    async def _fetch(self, endpoint: str) -> dict:
        url = f"{self.BASE_URL}/{endpoint}"
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    return await response.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error("SimRail API request failed: %s", e)
            raise

    async def get_servers(self) -> list[Server]:
        data = await self._fetch("servers-open")
        if data.get("result") and "data" in data:
            return data["data"]
        return []

    async def get_trains(self, server_code: str) -> list[Train]:
        data = await self._fetch(f"trains-open?serverCode={server_code}")
        if data.get("result") and "data" in data:
            return data["data"]
        return []

    async def get_stations(self, server_code: str) -> list[Station]:
        data = await self._fetch(f"stations-open?serverCode={server_code}")
        if data.get("result") and "data" in data:
            return data["data"]
        return []

    async def find_player(self, steam_id: str) -> PlayerActivity | None:
        servers = await self.get_servers()

        for server in servers:
            if not server.get("IsActive"):
                continue

            server_code = server["ServerCode"]

            # Check trains
            trains = await self.get_trains(server_code)
            for train in trains:
                controlled_by = train.get("TrainData", {}).get("ControlledBySteamID")
                if controlled_by == steam_id:
                    train_data = train["TrainData"]
                    # Speed limit: 32767 means no limit
                    speed_limit = train_data.get("SignalInFrontSpeed")
                    if speed_limit == 32767:
                        speed_limit = None

                    return PlayerActivity(
                        steam_id=steam_id,
                        activity_type="train",
                        server_code=server_code,
                        server_name=server["ServerName"],
                        train_number=train["TrainNoLocal"],
                        train_name=train["TrainName"],
                        start_station=train["StartStation"],
                        end_station=train["EndStation"],
                        vehicles=train["Vehicles"],
                        velocity=train_data.get("Velocity"),
                        signal_in_front=train_data.get("SignalInFront"),
                        distance_to_signal=train_data.get("DistanceToSignalInFront"),
                        signal_speed_limit=speed_limit,
                        run_id=train.get("RunId"),
                        station_name=None,
                        station_prefix=None,
                    )

            # Check stations
            stations = await self.get_stations(server_code)
            for station in stations:
                dispatchers = station.get("DispatchedBy", [])
                if dispatchers and dispatchers[0].get("SteamId") == steam_id:
                    return PlayerActivity(
                        steam_id=steam_id,
                        activity_type="station",
                        server_code=server_code,
                        server_name=server["ServerName"],
                        train_number=None,
                        train_name=None,
                        start_station=None,
                        end_station=None,
                        vehicles=None,
                        velocity=None,
                        signal_in_front=None,
                        distance_to_signal=None,
                        signal_speed_limit=None,
                        run_id=None,
                        station_name=station["Name"],
                        station_prefix=station["Prefix"],
                    )

        return None

    async def close(self):
        pass
