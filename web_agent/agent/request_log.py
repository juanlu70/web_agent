import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
import uuid

logger = logging.getLogger(__name__)

DEFAULT_LOG_PATH = Path.home() / ".web_agent" / "request_log.json"


class RequestLog:
    def __init__(self, log_path: Optional[str] = None):
        self.log_path = Path(log_path) if log_path else DEFAULT_LOG_PATH
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def add_entry(
        self,
        query: str,
        result: str,
        file_paths: Optional[list[str]] = None,
        source: str = "AI knowledge",
        deep: bool = False,
    ) -> dict:
        entry = {
            "id": uuid.uuid4().hex[:8],
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "file_paths": file_paths or [],
            "result": result,
            "source": source,
            "deep": deep,
        }

        entries = self._load_all()
        entries.append(entry)
        self._write_all(entries)
        logger.debug("Logged request %s", entry["id"])
        return entry

    def get_entries(self, limit: Optional[int] = None) -> list[dict]:
        entries = self._load_all()
        if limit:
            return entries[-limit:]
        return entries

    def get_entry(self, entry_id: str) -> Optional[dict]:
        for entry in self._load_all():
            if entry.get("id") == entry_id:
                return entry
        return None

    def clear(self) -> None:
        if self.log_path.exists():
            self.log_path.unlink()
            logger.info("Cleared request log")

    def _load_all(self) -> list[dict]:
        if not self.log_path.exists():
            return []
        try:
            data = self.log_path.read_text()
            if not data.strip():
                return []
            return json.loads(data)
        except (json.JSONDecodeError, Exception) as e:
            logger.warning("Failed to read request log: %s", e)
            return []

    def _write_all(self, entries: list[dict]) -> None:
        try:
            self.log_path.write_text(json.dumps(entries, indent=2, ensure_ascii=False))
        except Exception as e:
            logger.error("Failed to write request log: %s", e)