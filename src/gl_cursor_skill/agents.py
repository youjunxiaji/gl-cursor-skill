from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AgentProfile:
    key: str
    label: str
    global_dir: Path
    project_dir: Path
    aliases: tuple[str, ...] = ()


def home() -> Path:
    return Path.home()


AGENTS: tuple[AgentProfile, ...] = (
    AgentProfile(
        key="codex",
        label="Codex",
        global_dir=home() / ".codex" / "skills",
        project_dir=Path(".codex") / "skills",
    ),
    AgentProfile(
        key="claude-code",
        label="Claude Code",
        global_dir=home() / ".claude" / "skills",
        project_dir=Path(".claude") / "skills",
        aliases=("claude", "claudecode", "claude_code"),
    ),
    AgentProfile(
        key="cursor",
        label="Cursor",
        global_dir=home() / ".cursor" / "skills",
        project_dir=Path(".cursor") / "skills",
    ),
)


def normalize_agent(value: str) -> AgentProfile:
    wanted = value.strip().lower().replace(" ", "-")
    for agent in AGENTS:
        names = (agent.key, *agent.aliases)
        if wanted in names:
            return agent
    valid = ", ".join(agent.key for agent in AGENTS)
    raise ValueError(f"Unknown agent '{value}'. Expected one of: {valid}")


def agent_choices() -> list[tuple[str, str]]:
    return [(agent.label, agent.key) for agent in AGENTS]
