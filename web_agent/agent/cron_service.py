import asyncio
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)

DEFAULT_CRON_DIR = Path.home() / ".web_agent" / "cron"


def parse_cron_expr(expr: str) -> dict:
    parts = expr.strip().split()
    if len(parts) != 5:
        raise ValueError(f"Invalid cron expression (need 5 fields): {expr!r}")
    return {
        "minute": parts[0],
        "hour": parts[1],
        "dayOfMonth": parts[2],
        "month": parts[3],
        "dayOfWeek": parts[4],
    }


def cron_expr_matches(expr: str, dt: Optional[datetime] = None) -> bool:
    dt = dt or datetime.now()
    parts = expr.strip().split()
    if len(parts) != 5:
        return False
    checks = [
        (parts[0], dt.minute),
        (parts[1], dt.hour),
        (parts[2], dt.day),
        (parts[3], dt.month),
        (parts[4], dt.isoweekday() % 7),
    ]
    for field, value in checks:
        if field == "*":
            continue
        if field.startswith("*/"):
            step = int(field[2:])
            if step == 0 or value % step != 0:
                return False
        elif "," in field:
            if str(value) not in field.split(","):
                return False
        elif "-" in field:
            lo, hi = field.split("-")
            if not (int(lo) <= value <= int(hi)):
                return False
        else:
            if int(field) != value:
                return False
    return True


class CronJob:
    def __init__(
        self,
        name: str,
        prompt: str,
        schedule_kind: str = "cron",
        schedule_expr: str = "*/30 * * * *",
        schedule_interval_seconds: int = 0,
        schedule_at: Optional[str] = None,
        enabled: bool = True,
        job_id: Optional[str] = None,
    ):
        self.id = job_id or uuid.uuid4().hex[:8]
        self.name = name
        self.prompt = prompt
        self.schedule_kind = schedule_kind
        self.schedule_expr = schedule_expr
        self.schedule_interval_seconds = schedule_interval_seconds
        self.schedule_at = schedule_at
        self.enabled = enabled
        self.last_run: Optional[datetime] = None
        self.next_run: Optional[datetime] = None
        self.consecutive_errors = 0
        self.created_at = datetime.now().isoformat()

    def is_due(self, dt: Optional[datetime] = None) -> bool:
        if not self.enabled:
            return False
        dt = dt or datetime.now()
        if self.schedule_kind == "at":
            if self.last_run is not None:
                return False
            at_dt = datetime.fromisoformat(self.schedule_at) if self.schedule_at else None
            return at_dt is not None and dt >= at_dt
        if self.schedule_kind == "every":
            if self.last_run is None:
                return True
            elapsed = (dt - self.last_run).total_seconds()
            return elapsed >= self.schedule_interval_seconds
        if self.schedule_kind == "cron":
            if self.last_run is not None:
                minutes_since = (dt - self.last_run).total_seconds() / 60
                if minutes_since < 1:
                    return False
            return cron_expr_matches(self.schedule_expr, dt)
        return False

    def mark_run(self, success: bool = True) -> None:
        self.last_run = datetime.now()
        if success:
            self.consecutive_errors = 0
        else:
            self.consecutive_errors += 1

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "prompt": self.prompt,
            "schedule_kind": self.schedule_kind,
            "schedule_expr": self.schedule_expr,
            "schedule_interval_seconds": self.schedule_interval_seconds,
            "schedule_at": self.schedule_at,
            "enabled": self.enabled,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "consecutive_errors": self.consecutive_errors,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CronJob":
        job = cls(
            name=data.get("name", "unnamed"),
            prompt=data.get("prompt", ""),
            schedule_kind=data.get("schedule_kind", "cron"),
            schedule_expr=data.get("schedule_expr", "*/30 * * * *"),
            schedule_interval_seconds=data.get("schedule_interval_seconds", 0),
            schedule_at=data.get("schedule_at"),
            enabled=data.get("enabled", True),
            job_id=data.get("id"),
        )
        job.created_at = data.get("created_at", datetime.now().isoformat())
        job.consecutive_errors = data.get("consecutive_errors", 0)
        lr = data.get("last_run")
        if lr:
            job.last_run = datetime.fromisoformat(lr)
        return job


class CronService:
    def __init__(self, cron_dir: Optional[str] = None, orchestrator=None):
        self.cron_dir = Path(cron_dir) if cron_dir else DEFAULT_CRON_DIR
        self.cron_dir.mkdir(parents=True, exist_ok=True)
        self.jobs_file = self.cron_dir / "jobs.json"
        self.orchestrator = orchestrator
        self.jobs: list[CronJob] = []
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._load_jobs()

    def _load_jobs(self) -> None:
        if not self.jobs_file.exists():
            self.jobs = []
            return
        try:
            data = json.loads(self.jobs_file.read_text())
            version = data.get("version", 1)
            raw_jobs = data.get("jobs", [])
            self.jobs = [CronJob.from_dict(j) for j in raw_jobs]
            logger.info("Loaded %d cron jobs", len(self.jobs))
        except Exception as e:
            logger.warning("Failed to load cron jobs: %s", e)
            self.jobs = []

    def _save_jobs(self) -> None:
        data = {
            "version": 1,
            "jobs": [j.to_dict() for j in self.jobs],
            "updated_at": datetime.now().isoformat(),
        }
        try:
            tmp = self.jobs_file.with_suffix(".tmp")
            tmp.write_text(json.dumps(data, indent=2))
            tmp.rename(self.jobs_file)
        except Exception as e:
            logger.error("Failed to save cron jobs: %s", e)

    def add_job(
        self,
        name: str,
        prompt: str,
        schedule_kind: str = "cron",
        schedule_expr: str = "*/30 * * * *",
        schedule_interval_seconds: int = 0,
        schedule_at: Optional[str] = None,
    ) -> CronJob:
        job = CronJob(
            name=name,
            prompt=prompt,
            schedule_kind=schedule_kind,
            schedule_expr=schedule_expr,
            schedule_interval_seconds=schedule_interval_seconds,
            schedule_at=schedule_at,
        )
        self.jobs.append(job)
        self._save_jobs()
        logger.info("Added cron job: %s (%s)", job.name, job.id)
        return job

    def remove_job(self, job_id: str) -> bool:
        before = len(self.jobs)
        self.jobs = [j for j in self.jobs if j.id != job_id]
        if len(self.jobs) < before:
            self._save_jobs()
            logger.info("Removed cron job: %s", job_id)
            return True
        return False

    def toggle_job(self, job_id: str, enabled: bool) -> bool:
        for j in self.jobs:
            if j.id == job_id:
                j.enabled = enabled
                self._save_jobs()
                return True
        return False

    def list_jobs(self) -> list[dict]:
        return [j.to_dict() for j in self.jobs]

    async def _run_job(self, job: CronJob) -> None:
        logger.info("Running cron job: %s (%s)", job.name, job.id)
        try:
            if self.orchestrator:
                result = await self.orchestrator.handle_request(job.prompt)
                logger.info("Cron job %s completed: %s", job.name, result[:100])
            else:
                logger.warning("No orchestrator set, skipping job execution")
            job.mark_run(success=True)
        except Exception as e:
            logger.error("Cron job %s failed: %s", job.name, e)
            job.mark_run(success=False)
        self._save_jobs()

    async def _tick(self) -> None:
        now = datetime.now()
        for job in self.jobs:
            if job.is_due(now):
                asyncio.create_task(self._run_job(job))

    async def _run_loop(self) -> None:
        logger.info("Cron service started, checking every 60s")
        while self._running:
            await self._tick()
            await asyncio.sleep(60)

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())

    def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None