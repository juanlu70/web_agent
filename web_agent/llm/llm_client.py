import aiohttp
import json
import logging
from typing import AsyncIterator, Optional

from web_agent.config.settings import Config

logger = logging.getLogger(__name__)

MAX_RETRIES = 2
RETRY_DELAY_SECONDS = 1


class OllamaClient:
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def chat(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
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
                        return await resp.json()
            except (aiohttp.ClientResponseError, aiohttp.ClientConnectorError) as e:
                last_error = e
                if attempt < MAX_RETRIES:
                    logger.warning("Ollama chat attempt %d failed: %s, retrying...", attempt + 1, e)
                    import asyncio
                    await asyncio.sleep(RETRY_DELAY_SECONDS * (attempt + 1))
        raise last_error

    async def is_available(self) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags") as resp:
                    return resp.status == 200
        except Exception:
            return False

    async def list_models(self) -> list[dict]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags") as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    return [
                        {"name": m["name"], "provider": "ollama", "size": m.get("size", 0)}
                        for m in data.get("models", [])
                    ]
        except Exception as e:
            logger.error("Failed to list Ollama models: %s", e)
            return []


PROVIDERS = {
    "ollama": {
        "name": "Ollama (local)",
        "default_url": "http://localhost:11434",
        "needs_api_key": False,
    },
    "openai": {
        "name": "OpenAI",
        "default_url": "https://api.openai.com/v1",
        "needs_api_key": True,
        "default_model": "gpt-4o",
        "models": [
            {"name": "gpt-4o", "provider": "openai"},
            {"name": "gpt-4o-mini", "provider": "openai"},
            {"name": "gpt-4-turbo", "provider": "openai"},
            {"name": "gpt-3.5-turbo", "provider": "openai"},
            {"name": "o1", "provider": "openai"},
            {"name": "o1-mini", "provider": "openai"},
            {"name": "o3-mini", "provider": "openai"},
        ],
    },
    "anthropic": {
        "name": "Anthropic",
        "default_url": "https://api.anthropic.com",
        "needs_api_key": True,
        "default_model": "claude-sonnet-4-20250514",
        "models": [
            {"name": "claude-sonnet-4-20250514", "provider": "anthropic"},
            {"name": "claude-3-5-sonnet-20241022", "provider": "anthropic"},
            {"name": "claude-3-5-haiku-20241022", "provider": "anthropic"},
            {"name": "claude-3-opus-20240229", "provider": "anthropic"},
        ],
    },
    "openrouter": {
        "name": "OpenRouter",
        "default_url": "https://openrouter.ai/api/v1",
        "needs_api_key": True,
        "default_model": "openai/gpt-4o",
        "models": [
            {"name": "openai/gpt-4o", "provider": "openrouter"},
            {"name": "anthropic/claude-3.5-sonnet", "provider": "openrouter"},
            {"name": "google/gemini-2.0-flash-001", "provider": "openrouter"},
            {"name": "meta-llama/llama-3.3-70b-instruct", "provider": "openrouter"},
            {"name": "deepseek/deepseek-r1", "provider": "openrouter"},
        ],
    },
}


class LLMClient:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self._ollama: Optional[OllamaClient] = None

    @property
    def ollama(self) -> OllamaClient:
        if self._ollama is None:
            self._ollama = OllamaClient(
                base_url=self.config.ollama_base_url,
                model=self.config.ollama_model,
            )
        return self._ollama

    async def chat(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
    ) -> dict:
        provider = self.config.llm_provider

        if provider == "ollama":
            return await self.ollama.chat(messages=messages, tools=tools)
        elif provider == "openai":
            return await self._openai_chat(messages, tools=tools)
        elif provider == "anthropic":
            return await self._anthropic_chat(messages, tools=tools)
        elif provider == "openrouter":
            return await self._openrouter_chat(messages, tools=tools)
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")

    async def _openai_chat(self, messages: list[dict], tools: Optional[list[dict]] = None) -> dict:
        url = f"{self.config.llm_api_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.llm_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.config.llm_model,
            "messages": messages,
            "stream": False,
        }
        if tools:
            payload["tools"] = tools

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                resp.raise_for_status()
                data = await resp.json()
                choice = data.get("choices", [{}])[0]
                msg = choice.get("message", {})
                return {
                    "message": msg,
                    "done": True,
                    "done_reason": choice.get("finish_reason", "stop"),
                }

    async def _anthropic_chat(self, messages: list[dict], tools: Optional[list[dict]] = None) -> dict:
        url = f"{self.config.llm_api_url.rstrip('/')}/v1/messages"
        headers = {
            "x-api-key": self.config.llm_api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        system_text = ""
        user_messages = []
        for m in messages:
            if m.get("role") == "system":
                system_text += m.get("content", "") + "\n"
            else:
                user_messages.append(m)

        payload = {
            "model": self.config.llm_model,
            "max_tokens": 4096,
            "messages": user_messages,
        }
        if system_text:
            payload["system"] = system_text.strip()
        if tools:
            payload["tools"] = [
                {
                    "name": t["function"]["name"],
                    "description": t["function"].get("description", ""),
                    "input_schema": t["function"].get("parameters", {}),
                }
                for t in tools
            ]

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                resp.raise_for_status()
                data = await resp.json()
                content_blocks = data.get("content", [])
                text = ""
                tool_calls = []
                for block in content_blocks:
                    if block.get("type") == "text":
                        text += block.get("text", "")
                    elif block.get("type") == "tool_use":
                        tool_calls.append({
                            "function": {
                                "name": block.get("name", ""),
                                "arguments": block.get("input", {}),
                            }
                        })

                message = {"role": "assistant", "content": text}
                if tool_calls:
                    message["tool_calls"] = tool_calls
                return {
                    "message": message,
                    "done": True,
                    "done_reason": data.get("stop_reason", "end_turn"),
                }

    async def _openrouter_chat(self, messages: list[dict], tools: Optional[list[dict]] = None) -> dict:
        url = f"{self.config.llm_api_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.llm_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/web-agent",
        }
        payload = {
            "model": self.config.llm_model,
            "messages": messages,
            "stream": False,
        }
        if tools:
            payload["tools"] = tools

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                resp.raise_for_status()
                data = await resp.json()
                choice = data.get("choices", [{}])[0]
                msg = choice.get("message", {})
                return {
                    "message": msg,
                    "done": True,
                    "done_reason": choice.get("finish_reason", "stop"),
                }

    async def list_models(self) -> list[dict]:
        provider = self.config.llm_provider
        if provider == "ollama":
            return await self.ollama.list_models()
        else:
            return PROVIDERS.get(provider, {}).get("models", [])

    async def is_available(self) -> bool:
        provider = self.config.llm_provider
        if provider == "ollama":
            return await self.ollama.is_available()
        return bool(self.config.llm_api_key)


def get_provider_info(provider: str) -> dict:
    return PROVIDERS.get(provider, {})


def list_providers() -> list[dict]:
    result = []
    for key, info in PROVIDERS.items():
        result.append({
            "id": key,
            "name": info["name"],
            "needs_api_key": info["needs_api_key"],
            "default_url": info.get("default_url", ""),
            "default_model": info.get("default_model", ""),
        })
    return result