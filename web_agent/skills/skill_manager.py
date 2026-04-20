import logging
import re
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class Skill:
    name: str
    description: str
    when_to_use: str = ""
    when_not_to_use: str = ""
    instructions: str = ""
    website_url: str = ""
    commands: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    @classmethod
    def from_markdown(cls, content: str) -> "Skill":
        frontmatter, body = _parse_frontmatter(content)
        name = frontmatter.get("name", "unknown")
        description = frontmatter.get("description", "")
        metadata = {k: v for k, v in frontmatter.items() if k not in ("name", "description")}

        sections = _parse_sections(body)
        return cls(
            name=name,
            description=description,
            when_to_use=sections.get("when to use", ""),
            when_not_to_use=sections.get("when not to use", ""),
            instructions=sections.get("instructions", sections.get("how to use", "")),
            website_url=frontmatter.get("website_url", frontmatter.get("url", "")),
            commands=_parse_commands(body),
            metadata=metadata,
        )

    def to_markdown(self) -> str:
        frontmatter = {"name": self.name, "description": self.description}
        if self.website_url:
            frontmatter["website_url"] = self.website_url
        frontmatter.update(self.metadata)

        parts = [f"---\n{yaml.dump(frontmatter, default_flow_style=False).strip()}\n---\n"]
        if self.when_to_use:
            parts.append(f"\n## When to use\n\n{self.when_to_use}\n")
        if self.when_not_to_use:
            parts.append(f"\n## When not to use\n\n{self.when_not_to_use}\n")
        if self.instructions:
            parts.append(f"\n## Instructions\n\n{self.instructions}\n")
        if self.commands:
            parts.append("\n## Commands\n\n")
            for cmd in self.commands:
                parts.append(f"- `{cmd}`\n")
        return "\n".join(parts)

    def matches_query(self, query: str) -> float:
        query_lower = query.lower()
        score = 0.0
        if self.name.lower() in query_lower:
            score += 3.0
        if self.website_url and self.website_url.lower() in query_lower:
            score += 5.0
        if self.description.lower() in query_lower:
            score += 2.0
        for keyword in self.description.lower().split():
            if keyword in query_lower and len(keyword) > 3:
                score += 0.5
        return score


class SkillManager:
    def __init__(self, skills_dir: str):
        self.skills_dir = Path(skills_dir)
        self._skills: dict[str, Skill] = {}
        self._loaded = False

    def load_skills(self) -> None:
        self._skills.clear()
        if not self.skills_dir.exists():
            logger.warning("Skills directory does not exist: %s", self.skills_dir)
            self.skills_dir.mkdir(parents=True, exist_ok=True)
            return

        for skill_file in self.skills_dir.glob("**/SKILL.md"):
            try:
                content = skill_file.read_text()
                skill = Skill.from_markdown(content)
                self._skills[skill.name] = skill
                logger.debug("Loaded skill: %s from %s", skill.name, skill_file)
            except Exception as e:
                logger.error("Failed to load skill from %s: %s", skill_file, e)

        self._loaded = True
        logger.info("Loaded %d skills from %s", len(self._skills), self.skills_dir)

    def get_skill(self, name: str) -> Optional[Skill]:
        if not self._loaded:
            self.load_skills()
        return self._skills.get(name)

    def find_relevant_skills(self, query: str, top_k: int = 3) -> list[Skill]:
        if not self._loaded:
            self.load_skills()
        scored = [(skill.matches_query(query), skill) for skill in self._skills.values()]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [skill for score, skill in scored if score > 0][:top_k]

    def save_skill(self, skill: Skill) -> Path:
        if not self._loaded:
            self.load_skills()
        skill_dir = self.skills_dir / skill.name
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_path = skill_dir / "SKILL.md"
        skill_path.write_text(skill.to_markdown())
        self._skills[skill.name] = skill
        logger.info("Saved skill: %s to %s", skill.name, skill_path)
        return skill_path

    def list_skills(self) -> list[str]:
        if not self._loaded:
            self.load_skills()
        return list(self._skills.keys())

    def get_skill_instructions_for_prompt(self, query: str) -> str:
        relevant = self.find_relevant_skills(query)
        if not relevant:
            return ""
        parts = []
        for skill in relevant:
            parts.append(f"### Skill: {skill.name}\n{skill.description}")
            if skill.instructions:
                parts.append(f"Instructions:\n{skill.instructions}")
            if skill.website_url:
                parts.append(f"Website: {skill.website_url}")
        return "\n\n".join(parts)


def _parse_frontmatter(content: str) -> tuple[dict, str]:
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", content, re.DOTALL)
    if not match:
        return {}, content
    try:
        return yaml.safe_load(match.group(1)) or {}, match.group(2)
    except yaml.YAMLError:
        return {}, content


def _parse_sections(body: str) -> dict[str, str]:
    sections = {}
    current_header = ""
    current_content: list[str] = []
    for line in body.split("\n"):
        header_match = re.match(r"^##\s+(.+)", line)
        if header_match:
            if current_header:
                sections[current_header.lower()] = "\n".join(current_content).strip()
            current_header = header_match.group(1).strip()
            current_content = []
        else:
            current_content.append(line)
    if current_header:
        sections[current_header.lower()] = "\n".join(current_content).strip()
    return sections


def _parse_commands(body: str) -> list[str]:
    return re.findall(r"`([^`]+)`", body)

