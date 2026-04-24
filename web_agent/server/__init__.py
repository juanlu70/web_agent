import asyncio
import json
import logging
import uuid
from pathlib import Path
from typing import Optional

from aiohttp import web

from web_agent.agent.orchestrator import OrchestratorAgent
from web_agent.agent.request_log import RequestLog
from web_agent.config.settings import Config

logger = logging.getLogger(__name__)

CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]


@web.middleware
async def cors_middleware(request: web.Request, handler):
    origin = request.headers.get("Origin", "")
    if origin in CORS_ORIGINS:
        if request.method == "OPTIONS":
            response = web.Response(status=204)
        else:
            response = await handler(request)
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, DELETE"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Access-Control-Max-Age"] = "86400"
        return response
    return await handler(request)


class WebAgentServer:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.orchestrator = OrchestratorAgent(self.config)
        self.request_log = RequestLog()
        self.app = web.Application(middlewares=[cors_middleware])
        self._setup_routes()
        self._active_tasks: dict[str, asyncio.Task] = {}

    def _setup_routes(self):
        self.app.router.add_post("/request", self.handle_request)
        self.app.router.add_get("/health", self.handle_health)
        self.app.router.add_get("/status/{task_id}", self.handle_status)
        self.app.router.add_delete("/cancel/{task_id}", self.handle_cancel)
        self.app.router.add_get("/config", self.handle_get_config)
        self.app.router.add_get("/history", self.handle_history)
        self.app.router.add_get("/history/{entry_id}", self.handle_history_entry)

    async def handle_request(self, request: web.Request) -> web.Response:
        try:
            data = await request.json()
        except Exception:
            return web.json_response({"error": "Invalid JSON body"}, status=400)

        query = data.get("query", "").strip()
        if not query:
            return web.json_response({"error": "Missing 'query' field"}, status=400)

        deep = data.get("deep", False)
        file_paths = data.get("file_paths", [])
        if isinstance(file_paths, str):
            file_paths = [file_paths]
        file_paths = file_paths or None

        sync = data.get("sync", False)
        task_id = str(uuid.uuid4())[:8]

        async def _run():
            try:
                result = await self.orchestrator.handle_request(query, file_paths=file_paths)
                self.request_log.add_entry(
                    query=query,
                    result=result,
                    file_paths=file_paths or [],
                    source="web search" if "web" in str(result).lower() else "AI knowledge",
                    deep=deep,
                )
                return {"task_id": task_id, "status": "completed", "result": result}
            except asyncio.CancelledError:
                logger.info("Task %s was cancelled", task_id)
                self.request_log.add_entry(
                    query=query,
                    result="Search cancelled by user",
                    file_paths=file_paths or [],
                    source="cancelled",
                    deep=deep,
                )
                return {"task_id": task_id, "status": "cancelled", "result": "Search cancelled by user"}
            except Exception as e:
                logger.error("Task %s failed: %s", task_id, e)
                self.request_log.add_entry(
                    query=query,
                    result=f"Error: {str(e)}",
                    file_paths=file_paths or [],
                    source="error",
                    deep=deep,
                )
                return {"task_id": task_id, "status": "failed", "error": str(e)}

        task = asyncio.create_task(_run())
        self._active_tasks[task_id] = task

        if sync:
            result = await task
            self._active_tasks.pop(task_id, None)
            return web.json_response(result)
        else:
            return web.json_response({"task_id": task_id, "status": "running"})

    async def handle_status(self, request: web.Request) -> web.Response:
        task_id = request.match_info.get("task_id", "")
        task = self._active_tasks.get(task_id)
        if task is None:
            return web.json_response({"task_id": task_id, "status": "unknown"})
        if task.done():
            result = task.result()
            self._active_tasks.pop(task_id, None)
            return web.json_response(result)
        return web.json_response({"task_id": task_id, "status": "running"})

    async def handle_cancel(self, request: web.Request) -> web.Response:
        task_id = request.match_info.get("task_id", "")
        task = self._active_tasks.get(task_id)
        if task is None:
            return web.json_response({"task_id": task_id, "status": "unknown"})
        if task.done():
            self._active_tasks.pop(task_id, None)
            return web.json_response({"task_id": task_id, "status": "already_done"})
        task.cancel()
        logger.info("Cancelled task %s", task_id)
        return web.json_response({"task_id": task_id, "status": "cancelling"})

    async def handle_health(self, request: web.Request) -> web.Response:
        return web.json_response({
            "status": "ok",
            "model": self.config.ollama_model,
            "host": self.config.server_host,
            "port": self.config.server_port,
        })

    async def handle_get_config(self, request: web.Request) -> web.Response:
        return web.json_response({
            "server_host": self.config.server_host,
            "server_port": self.config.server_port,
            "ollama_model": self.config.ollama_model,
            "ollama_base_url": self.config.ollama_base_url,
            "normal_search_results": self.config.normal_search_results,
            "deep_search_results": self.config.deep_search_results,
            "max_subagents": self.config.max_subagents,
            "max_agent_iterations": self.config.max_agent_iterations,
            "max_history_entries": self.config.max_history_entries,
            "headless": self.config.headless,
            "skills_dir": self.config.effective_skills_dir,
            "guardrails_file": self.config.effective_guardrails_file,
        })

    async def handle_history(self, request: web.Request) -> web.Response:
        limit = int(request.query.get("limit", "0")) or None
        entries = self.request_log.get_entries(limit=limit)
        return web.json_response({"history": entries, "count": len(entries)})

    async def handle_history_entry(self, request: web.Request) -> web.Response:
        entry_id = request.match_info.get("entry_id", "")
        entry = self.request_log.get_entry(entry_id)
        if entry is None:
            return web.json_response({"error": f"Entry '{entry_id}' not found"}, status=404)
        return web.json_response(entry)

    def run(self, host: Optional[str] = None, port: Optional[int] = None):
        host = host or self.config.server_host
        port = port or self.config.server_port
        logger.info("Starting web_agent server on %s:%d", host, port)
        web.run_app(self.app, host=host, port=port, print=lambda msg: logger.info(msg))