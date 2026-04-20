import os
import yaml
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.yaml"
SKILLS_DIR = PROJECT_ROOT / "skills"
DEFAULT_GUARDRAILS_PATH = PROJECT_ROOT / "guardrails.md"
DEFAULT_OLLAMA_MODEL = "glm-5.1:cloud"
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_SERVER_HOST = "127.0.0.1"
DEFAULT_SERVER_PORT = 8400


@dataclass
class Config:
    server_host: str = DEFAULT_SERVER_HOST
    server_port: int = DEFAULT_SERVER_PORT
    ollama_base_url: str = DEFAULT_OLLAMA_BASE_URL
    ollama_model: str = DEFAULT_OLLAMA_MODEL
    skills_dir: str = str(SKILLS_DIR)
    guardrails_file: str = str(DEFAULT_GUARDRAILS_PATH)
    normal_search_results: int = 10
    deep_search_results: int = 50
    headless: bool = True
    browser_timeout_ms: int = 30000
    max_subagents: int = 3
    subagent_depth_limit: int = 3
    max_agent_iterations: int = 10
    max_history_entries: int = 15

    @classmethod
    def load(cls, path: Optional[str] = None) -> "Config":
        config_path = Path(path) if path else DEFAULT_CONFIG_PATH
        if config_path.exists():
            with open(config_path) as f:
                data = yaml.safe_load(f) or {}
            known_fields = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
            skills_dir = known_fields.get("skills_dir", "")
            if skills_dir == "":
                known_fields["skills_dir"] = str(SKILLS_DIR)
            guardrails = known_fields.get("guardrails_file", "")
            if guardrails == "":
                known_fields["guardrails_file"] = str(DEFAULT_GUARDRAILS_PATH)
            return cls(**known_fields)
        cfg = cls()
        cfg.save(str(config_path))
        return cfg

    def save(self, path: Optional[str] = None) -> None:
        config_path = Path(path) if path else DEFAULT_CONFIG_PATH
        config_path.parent.mkdir(parents=True, exist_ok=True)
        data = {}
        for k, v in self.__dict__.items():
            if k in ("skills_dir", "guardrails_file"):
                if v == str(SKILLS_DIR):
                    data[k] = ""
                elif v == str(DEFAULT_GUARDRAILS_PATH):
                    data[k] = ""
                else:
                    data[k] = v
            else:
                data[k] = v
        with open(config_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    @property
    def effective_skills_dir(self) -> str:
        if self.skills_dir and self.skills_dir.strip():
            return self.skills_dir
        return str(SKILLS_DIR)

    @property
    def effective_guardrails_file(self) -> str:
        if self.guardrails_file and self.guardrails_file.strip():
            return self.guardrails_file
        return str(DEFAULT_GUARDRAILS_PATH)

    def load_guardrails(self) -> str:
        guardrails_path = Path(self.effective_guardrails_file)
        if guardrails_path.exists():
            return guardrails_path.read_text()
        return ""

    @property
    def server_url(self) -> str:
        return f"http://{self.server_host}:{self.server_port}"

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            server_host=os.environ.get("WEB_AGENT_HOST", DEFAULT_SERVER_HOST),
            server_port=int(os.environ.get("WEB_AGENT_PORT", str(DEFAULT_SERVER_PORT))),
            ollama_base_url=os.environ.get("OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL),
            ollama_model=os.environ.get("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL),
            skills_dir=os.environ.get("WEB_AGENT_SKILLS_DIR", str(SKILLS_DIR)),
            guardrails_file=os.environ.get("WEB_AGENT_GUARDRAILS_FILE", str(DEFAULT_GUARDRAILS_PATH)),
            headless=os.environ.get("WEB_AGENT_HEADLESS", "true").lower() == "true",
            normal_search_results=int(os.environ.get("WEB_AGENT_NORMAL_SEARCH_RESULTS", "10")),
            deep_search_results=int(os.environ.get("WEB_AGENT_DEEP_SEARCH_RESULTS", "50")),
            max_subagents=int(os.environ.get("WEB_AGENT_MAX_SUBAGENTS", "3")),
        )