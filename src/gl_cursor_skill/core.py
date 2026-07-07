from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
import shutil

from .agents import AGENTS, AgentProfile, normalize_agent


class SkillError(RuntimeError):
    pass


@dataclass(frozen=True)
class SkillCandidate:
    path: Path
    label: str


@dataclass(frozen=True)
class InstallPlan:
    source_dir: Path
    target_dir: Path
    skill_name: str
    target_agent: AgentProfile
    scope: str


def find_skill_file(path: Path) -> Path | None:
    if path.is_file() and path.name.lower() == "skill.md":
        return path
    if not path.is_dir():
        return None
    for name in ("SKILL.md", "skill.md"):
        candidate = path / name
        if candidate.is_file():
            return candidate
    return None


def ensure_skill_dir(path: Path) -> Path:
    expanded = path.expanduser()
    if expanded.is_file() and expanded.name.lower() == "skill.md":
        expanded = expanded.parent
    skill_file = find_skill_file(expanded)
    if skill_file is None:
        raise SkillError(f"Not a skill directory: {expanded}")
    return expanded


def target_base_dir(
    agent: AgentProfile,
    scope: str,
    project_root: Path | None = None,
    explicit_dest: Path | None = None,
) -> Path:
    if explicit_dest is not None:
        return explicit_dest.expanduser()

    normalized_scope = normalize_scope(scope)
    if normalized_scope == "global":
        return agent.global_dir

    root = project_root.expanduser() if project_root is not None else Path.cwd()
    return root / agent.project_dir


def normalize_scope(value: str) -> str:
    normalized = value.strip().lower()
    if normalized not in {"global", "project"}:
        raise ValueError("Scope must be either 'global' or 'project'")
    return normalized


def known_source_dirs(project_root: Path | None = None) -> list[SkillCandidate]:
    root = project_root.expanduser() if project_root is not None else Path.cwd()
    candidates: list[SkillCandidate] = bundled_source_dirs()

    for agent in AGENTS:
        candidates.append(SkillCandidate(agent.global_dir, f"{agent.label} global"))
        candidates.append(SkillCandidate(root / agent.project_dir, f"{agent.label} project"))

    return candidates


def bundled_source_dirs() -> list[SkillCandidate]:
    bundled = files("gl_cursor_skill").joinpath("bundled_skills")
    if not bundled.is_dir():
        return []
    return [SkillCandidate(Path(str(bundled)), "Bundled")]


def resolve_source_candidates(
    skill: str,
    source: str | None = None,
    project_root: Path | None = None,
) -> list[SkillCandidate]:
    skill_path = Path(skill).expanduser()
    if skill_path.exists():
        source_dir = ensure_skill_dir(skill_path)
        return [SkillCandidate(source_dir, "explicit path")]

    source_path = Path(source).expanduser() if source else None
    if source_path is not None and source_path.exists():
        if find_skill_file(source_path) is not None:
            source_dir = ensure_skill_dir(source_path)
        elif source_path.is_dir():
            source_dir = ensure_skill_dir(source_path / skill)
        else:
            source_dir = ensure_skill_dir(source_path)
        return [SkillCandidate(source_dir, "explicit --from path")]

    search_dirs = _source_search_dirs(source, project_root)
    found: list[SkillCandidate] = []
    seen: set[Path] = set()
    for base in search_dirs:
        candidate_dir = base.path / skill
        if find_skill_file(candidate_dir) is None:
            continue
        resolved = candidate_dir.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        found.append(SkillCandidate(candidate_dir, base.label))

    return found


def _source_search_dirs(source: str | None, project_root: Path | None) -> list[SkillCandidate]:
    if source is None:
        return known_source_dirs(project_root)

    if source.strip().lower() == "bundled":
        return bundled_source_dirs()

    try:
        agent = normalize_agent(source)
    except ValueError as error:
        raise SkillError(f"{error}. You can also pass --from bundled or --from /path/to/skills.") from error

    root = project_root.expanduser() if project_root is not None else Path.cwd()
    return [
        SkillCandidate(agent.global_dir, f"{agent.label} global"),
        SkillCandidate(root / agent.project_dir, f"{agent.label} project"),
    ]


def build_install_plan(
    source_dir: Path,
    target_agent: AgentProfile,
    scope: str,
    project_root: Path | None = None,
    explicit_dest: Path | None = None,
) -> InstallPlan:
    source = ensure_skill_dir(source_dir)
    base = target_base_dir(target_agent, scope, project_root, explicit_dest)
    return InstallPlan(
        source_dir=source,
        target_dir=base / source.name,
        skill_name=source.name,
        target_agent=target_agent,
        scope=normalize_scope(scope),
    )


def install_skill(plan: InstallPlan, force: bool = False, dry_run: bool = False) -> None:
    if plan.target_dir.exists():
        if dry_run:
            return
        if not force:
            raise SkillError(f"Target already exists: {plan.target_dir}")
        if plan.target_dir.is_dir():
            shutil.rmtree(plan.target_dir)
        else:
            plan.target_dir.unlink()

    if dry_run:
        return

    plan.target_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(plan.source_dir, plan.target_dir)
