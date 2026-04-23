import json
import logging
from typing import Optional

import aiohttp

from web_agent.config.settings import Config

logger = logging.getLogger(__name__)


class WebAgentClient:
    def __init__(self, server_url: Optional[str] = None, config: Optional[Config] = None):
        self.config = config or Config()
        self.server_url = (server_url or self.config.server_url).rstrip("/")

    async def request(self, query: str, deep: bool = False, file_paths: Optional[list[str]] = None, sync: bool = True) -> dict:
        payload = {
            "query": query,
            "deep": deep,
            "sync": sync,
        }
        if file_paths:
            payload["file_paths"] = file_paths

        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.server_url}/request", json=payload) as resp:
                resp.raise_for_status()
                return await resp.json()

    async def health(self) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.server_url}/health") as resp:
                resp.raise_for_status()
                return await resp.json()

    async def status(self, task_id: str) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.server_url}/status/{task_id}") as resp:
                resp.raise_for_status()
                return await resp.json()

    async def get_config(self) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.server_url}/config") as resp:
                resp.raise_for_status()
                return await resp.json()

    async def get_history(self, limit: Optional[int] = None) -> dict:
        params = {}
        if limit:
            params["limit"] = str(limit)
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.server_url}/history", params=params) as resp:
                resp.raise_for_status()
                return await resp.json()

    def sync_request(self, query: str, deep: bool = False, file_paths: Optional[list[str]] = None) -> dict:
        import asyncio
        return asyncio.run(self.request(query, deep=deep, file_paths=file_paths, sync=True))

    def sync_health(self) -> dict:
        import asyncio
        return asyncio.run(self.health())