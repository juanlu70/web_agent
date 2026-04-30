import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)

DEFAULT_HEARTBEAT_EVERY = "30m"
HEARTBEAT_OK = "HEARTBEAT_OK"

DURATION_RE = re.compile(r"^(\d+)(m|h|d|s)$")


def parse_duration(d: str) -> int:
    m = DURATION_RE.match(d.strip().lower())
    if not m:
        raise ValueError(f"Invalid duration: {d!r}")
    val = int(m.group(1))
    unit = m.group(2)
    if unit == "s":
        return val
    if unit == "m":
        return val * 60
    if unit == "h":
        return val * 3600
    if unit == "d":
        return val * 86400
    raise ValueError(f"Invalid duration unit: {unit!r}")


class HeartbeatTask:
    def __init__(self, name: str, interval: str, prompt: str):
        self.name = name
        self.interval = interval
        self.interval_seconds = parse_duration(interval)
        self.prompt = prompt
        self.last_run: Optional[datetime] = None

    def is_due(self) -> bool:
        if self.last_run is None:
            return True
        elapsed = (datetime.now() - self.last_run).total_seconds()
        return elapsed >= self.interval_seconds

    def mark_run(self) -> None:
        self.last_run = datetime.now()

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "interval": self.interval,
            "prompt": self.prompt,
            "last_run": self.last_run.isoformat() if self.last_run else None,
        }


class HeartbeatRunner:
    def __init__(
        self,
        heartbeat_file: Optional[str] = None,
        every: str = DEFAULT_HEARTBEAT_EVERY,
        prompt: Optional[str] = None,
    ):
        if heartbeat_file:
            self.heartbeat_file = Path(heartbeat_file)
        else:
            self.heartbeat_file = Path.home() / ".web_agent" / "HEARTBEAT.md"
        self.default_every = every
        self.default_prompt = prompt
        self.tasks: list[HeartbeatTask] = []
        self._load_tasks()

    def _load_tasks(self) -> None:
        self.tasks.clear()
        if not self.heartbeat_file.exists():
            logger.debug("No HEARTBEAT.md found at %s", self.heartbeat_file)
            return
        try:
            content = self.heartbeat_file.read_text()
            self._parse_tasks(content)
        except Exception as e:
            logger.warning("Failed to load HEARTBEAT.md: %s", e)

    def reload(self) -> None:
        self._load_tasks()

    def _parse_tasks(self, content: str) -> None:
        yaml_match = re.search(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        if yaml_match:
            try:
                frontmatter = yaml.safe_load(yaml_match.group(1))
                if frontmatter and "tasks" in frontmatter:
                    for t in frontmatter["tasks"]:
                        self.tasks.append(HeartbeatTask(
                            name=t.get("name", "unnamed"),
                            interval=t.get("interval", self.default_every),
                            prompt=t.get("prompt", ""),
                        ))
                    logger.info("Loaded %d heartbeat tasks", len(self.tasks))
            except yaml.YAMLError as e:
                logger.warning("Failed to parse HEARTBEAT.md frontmatter: %s", e)

    def get_due_tasks(self) -> list[HeartbeatTask]:
        return [t for t in self.tasks if t.is_due()]

    def build_heartbeat_prompt(self) -> str:
        base = self.default_prompt or (
            "Read HEARTBEAT.md if it exists. Follow its instructions strictly. "
            "If nothing needs attention, reply HEARTBEAT_OK."
        )
        due = self.get_due_tasks()
        if not due:
            return base
        parts = [base, "\n\nDue tasks:"]
        for t in due:
            parts.append(f"- [{t.name}] (every {t.interval}): {t.prompt}")
        return "\n".join(parts)

    @staticmethod
    def is_heartbeat_ok(response: str) -> bool:
        return HEARTBEAT_OK in response.strip()

    def mark_tasks_run(self, task_names: list[str]) -> None:
        for t in self.tasks:
            if t.name in task_names:
                t.mark_run()

    def save_state(self, state_file: Optional[Path] = None) -> None:
        path = state_file or Path.home() / ".web_agent" / "heartbeat_state.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        import json
        data = {t.name: t.to_dict() for t in self.tasks}
        try:
            path.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.warning("Failed to save heartbeat state: %s", e)

    def load_state(self, state_file: Optional[Path] = None) -> None:
        path = state_file or Path.home() / ".web_agent" / "heartbeat_state.json"
        if not path.exists():
            return
        import json
        try:
            data = json.loads(path.read_text())
            for t in self.tasks:
                if t.name in data:
                    last = data[t.name].get("last_run")
                    if last:
                        t.last_run = datetime.fromisoformat(last)
        except Exception as e:
            logger.warning("Failed to load heartbeat state: %s", e)