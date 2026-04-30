import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_MEMORY_DIR = Path.home() / ".web_agent"


class UserMemory:
    def __init__(self, memory_dir: Optional[str] = None):
        self.memory_dir = Path(memory_dir) if memory_dir else DEFAULT_MEMORY_DIR
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.memory_file = self.memory_dir / "MEMORY.md"
        self.entries_dir = self.memory_dir / "memory"
        self.entries_dir.mkdir(parents=True, exist_ok=True)
        self._short_term: list[dict] = []
        self._max_short_term = 10

    def load(self) -> str:
        if not self.memory_file.exists():
            return ""
        try:
            return self.memory_file.read_text()
        except Exception as e:
            logger.warning("Failed to load MEMORY.md: %s", e)
            return ""

    def save(self, content: str) -> None:
        try:
            self.memory_file.write_text(content)
            logger.debug("Saved MEMORY.md")
        except Exception as e:
            logger.error("Failed to save MEMORY.md: %s", e)

    def append(self, section: str) -> None:
        existing = self.load()
        if existing and not existing.endswith("\n"):
            existing += "\n"
        self.save(existing + section + "\n")

    def get_context_for_prompt(self) -> str:
        content = self.load()
        if not content.strip():
            return ""
        return f"""## User Memory

This is the user's personal memory file. It contains their preferences, personal context, and accumulated knowledge about how they like things done. Always respect and follow these preferences when responding:

{content}"""

    def get_short_term_context(self) -> str:
        if not self._short_term:
            return ""
        lines = ["## Short-Term Memory\n", "Recent observations and context from this session:"]
        for entry in self._short_term:
            ts = entry.get("timestamp", "?")
            text = entry.get("text", "")
            lines.append(f"- [{ts}] {text}")
        return "\n".join(lines)

    def add_short_term(self, text: str) -> None:
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "text": text,
        }
        self._short_term.append(entry)
        if len(self._short_term) > self._max_short_term:
            self._short_term = self._short_term[-self._max_short_term:]

    def flush_short_term(self, summary: str) -> None:
        if summary.strip():
            ts = datetime.now().strftime("%Y-%m-%d")
            dated_entry = f"\n## [{ts}] Session Notes\n\n{summary}\n"
            self.append(dated_entry)
            dated_file = self.entries_dir / f"{ts}.md"
            try:
                existing = dated_file.read_text() if dated_file.exists() else ""
                dated_file.write_text(existing + summary + "\n")
            except Exception as e:
                logger.warning("Failed to write dated memory entry: %s", e)
        self._short_term.clear()

    def list_entries(self) -> list[dict]:
        entries = []
        if self.memory_file.exists():
            entries.append({
                "path": str(self.memory_file),
                "name": "MEMORY.md",
                "modified": datetime.fromtimestamp(self.memory_file.stat().st_mtime).isoformat(),
            })
        for f in sorted(self.entries_dir.glob("*.md")):
            entries.append({
                "path": str(f),
                "name": f.name,
                "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
            })
        return entries