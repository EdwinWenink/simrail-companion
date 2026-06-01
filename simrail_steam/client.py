import asyncio
import json
import logging
import os
import random
from typing import Optional

import aiohttp

from .types import PlayerSummary, PlayerStats, SimRailStats

logger = logging.getLogger(__name__)


class SteamClient:
    SIMRAIL_APP_ID = 1422130
    BASE_URL = "https://api.steampowered.com"
    DEFAULT_TIMEOUT = 10

    def __init__(self, api_keys: Optional[list[str]] = None, timeout: int = DEFAULT_TIMEOUT):
        if api_keys is None:
            api_keys = self._load_api_keys_from_env()

        if not api_keys:
            raise ValueError(
                "No Steam API keys provided. Set STEAM_API_KEY environment variable "
                "or pass api_keys parameter."
            )

        self.api_keys = api_keys
        self.timeout = timeout

    @staticmethod
    def _load_api_keys_from_env() -> list[str]:
        api_key_env = os.getenv("STEAM_API_KEY", "")

        if not api_key_env:
            return []

        # Try to parse as JSON array first
        if api_key_env.startswith("["):
            try:
                keys = json.loads(api_key_env)
                return keys if isinstance(keys, list) else [api_key_env]
            except json.JSONDecodeError:
                pass

        # Single key
        return [api_key_env]

    def _get_random_key(self) -> str:
        return random.choice(self.api_keys)

    async def _fetch_with_retry(
        self,
        url: str,
        max_retries: int = 3
    ) -> dict:
        retries = 0

        while retries < max_retries:
            api_key = self._get_random_key()
            full_url = url.replace("[STEAMKEY]", api_key)

            try:
                timeout = aiohttp.ClientTimeout(total=self.timeout)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(full_url) as response:
                        response.raise_for_status()
                        return await response.json()
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                retries += 1
                logger.warning(f"Steam request failed: {e}, retry {retries}/{max_retries}")

                if retries < max_retries:
                    await asyncio.sleep(retries)
                else:
                    raise

        raise Exception(f"Failed to fetch from Steam API after {max_retries} retries")

    async def get_player_summary(self, steam_id: str) -> Optional[PlayerSummary]:
        url = (
            f"{self.BASE_URL}/ISteamUser/GetPlayerSummaries/v2/"
            f"?key=[STEAMKEY]&format=json&steamids={steam_id}"
        )

        try:
            data = await self._fetch_with_retry(url)
            players = data.get("response", {}).get("players", [])

            if not players:
                return None

            return players[0]
        except Exception as e:
            logger.error(f"Error fetching player summary for {steam_id}: {e}")
            return None

    async def get_player_stats(self, steam_id: str) -> Optional[PlayerStats]:
        url = (
            f"{self.BASE_URL}/ISteamUserStats/GetUserStatsForGame/v0002/"
            f"?appid={self.SIMRAIL_APP_ID}&key=[STEAMKEY]&steamid={steam_id}"
        )

        try:
            data = await self._fetch_with_retry(url)
            player_stats = data.get("playerstats")

            if not player_stats or "stats" not in player_stats:
                return None

            return player_stats
        except Exception as e:
            logger.error(f"Error fetching player stats for {steam_id}: {e}")
            return None

    async def get_simrail_stats(self, steam_id: str) -> Optional[SimRailStats]:
        stats = await self.get_player_stats(steam_id)

        if not stats:
            return None

        stats_dict = {stat["name"]: stat["value"] for stat in stats["stats"]}

        return SimRailStats(
            SCORE=stats_dict.get("SCORE", 0),
            DISPATCHER_TIME=stats_dict.get("DISPATCHER_TIME", 0),
            DISTANCE_M=stats_dict.get("DISTANCE_M", 0),
        )

    async def close(self):
        pass
