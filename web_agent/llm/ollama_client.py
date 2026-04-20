import aiohttp
import json
import logging
from typing import AsyncIterator, Optional

from web_agent.config.settings import Config

logger = logging.getLogger(__name__)

MAX_RETRIES = 2
RETRY_DELAY_SECONDS = 1


class OllamaClient:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.base_url = self.config.ollama_base_url.rstrip("/")
        self.model = self.config.ollama_model

    async def chat(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        stream: bool = False,
    ) -> dict:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }
        if tools:
            payload["tools"] = tools

        last_error = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_url}/api/chat",
                        json=payload,
                    ) as resp:
                        if resp.status == 404:
                            raise aiohttp.ClientResponseError(
                                request_info=resp.request_info,
                                history=resp.history,
                                status=resp.status,
                                message=f"Model '{self.model}' not found or /api/chat endpoint unavailable",
                            )
                        resp.raise_for_status()
                        data = await resp.json()
                        return data
            except (aiohttp.ClientResponseError, aiohttp.ClientConnectorError) as e:
                last_error = e
                if attempt < MAX_RETRIES:
                    logger.warning("Ollama chat attempt %d failed: %s, retrying...", attempt + 1, e)
                    import asyncio
                    await asyncio.sleep(RETRY_DELAY_SECONDS * (attempt + 1))
        raise last_error

    async def chat_stream(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
    ) -> AsyncIterator[dict]:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
        }
        if tools:
            payload["tools"] = tools

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/chat",
                json=payload,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.content:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        yield chunk
                    except json.JSONDecodeError:
                        logger.warning("Failed to decode chunk: %s", line)

    async def is_available(self) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags") as resp:
                    return resp.status == 200
        except Exception:
            return False

    async def list_models(self) -> list[str]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags") as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            logger.error("Failed to list models: %s", e)
            return []

