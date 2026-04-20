import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_MAX_HISTORY_ENTRIES = 15


class ConversationHistory:
    def __init__(self, history_dir: Optional[str] = None, max_entries: int = DEFAULT_MAX_HISTORY_ENTRIES):
        if history_dir:
            self.history_dir = Path(history_dir)
        else:
            self.history_dir = Path.home() / ".web_agent"
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.history_dir / "conversation_history.md"
        self.max_entries = max_entries

    def load(self) -> str:
        if not self.history_file.exists():
            return ""
        try:
            return self.history_file.read_text()
        except Exception as e:
            logger.warning("Failed to load conversation history: %s", e)
            return ""

    def load_recent(self) -> str:
        content = self.load()
        if not content:
            return ""
        entries = content.split("\n\n---\n\n")
        recent = entries[-self.max_entries:]
        if len(recent) < len(entries):
            header = "# Conversation History\n\n"
            remaining = content.find("---")
            if remaining > 0:
                header = content[:remaining].strip() + "\n\n"
            return header + "\n\n---\n\n".join(recent)
        return content

    def add_entry(self, request: str, result: str, web_search_used: bool = False) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        source = "web search" if web_search_used else "AI knowledge"
        entry = f"""## [{timestamp}] (source: {source})

**Request:** {request}

**Result:** {result}"""

        existing = self.load()
        entries = existing.split("\n\n---\n\n") if existing else []

        if not entries or not existing:
            header = "# Conversation History\n"
            entries = [entry]
        else:
            header_part = existing[:existing.find("---")].strip() if "---" in existing else existing.split("\n\n")[0]
            header = header_part + "\n"
            entries.append(entry)

        entries = entries[-self.max_entries:]

        new_content = header + "\n\n---\n\n".join(entries) + "\n"

        try:
            self.history_file.write_text(new_content)
            logger.debug("Saved conversation entry (total: %d)", len(entries))
        except Exception as e:
            logger.error("Failed to save conversation history: %s", e)

    def get_context_for_prompt(self) -> str:
        content = self.load_recent()
        if not content.strip():
            return ""
        return f"""## Previous Conversation History

This is the history of recent interactions with this user. Use this context to learn the user's preferences and behavior patterns:

{content}"""

    def clear(self) -> None:
        if self.history_file.exists():
            self.history_file.unlink()
            logger.info("Cleared conversation history")