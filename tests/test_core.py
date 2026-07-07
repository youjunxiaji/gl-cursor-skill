from __future__ import annotations

from pathlib import Path

import pytest

from gl_cursor_skill.agents import normalize_agent
from gl_cursor_skill.core import (
    SkillError,
    build_install_plan,
    ensure_skill_dir,
    install_skill,
    normalize_scope,
    resolve_source_candidates,
)


def make_skill(path: Path) -> Path:
    path.mkdir(parents=True)
    (path / "SKILL.md").write_text("---\nname: demo\n---\n# Demo\n", encoding="utf-8")
    return path


def test_normalize_agent_aliases() -> None:
    assert normalize_agent("codex").key == "codex"
    assert normalize_agent("claudecode").key == "claude-code"
    assert normalize_agent("claude").key == "claude-code"
    assert normalize_agent("opencode").key == "opencode"
    assert normalize_agent("open-code").key == "opencode"


def test_opencode_uses_xdg_config_global_dir() -> None:
    opencode = normalize_agent("opencode")
    assert opencode.global_dir.parts[-3:] == (".config", "opencode", "skills")
    assert opencode.project_dir.as_posix() == ".opencode/skills"


def test_normalize_scope() -> None:
    assert normalize_scope("global") == "global"
    assert normalize_scope("project") == "project"
    with pytest.raises(ValueError):
        normalize_scope("workspace")


def test_ensure_skill_dir_accepts_directory_and_skill_file(tmp_path: Path) -> None:
    skill = make_skill(tmp_path / "cursor-agent")
    assert ensure_skill_dir(skill) == skill
    assert ensure_skill_dir(skill / "SKILL.md") == skill


def test_install_skill_to_explicit_destination(tmp_path: Path) -> None:
    source = make_skill(tmp_path / "source" / "cursor-agent")
    dest = tmp_path / "dest"
    plan = build_install_plan(source, normalize_agent("codex"), "global", explicit_dest=dest)

    install_skill(plan)

    assert (dest / "cursor-agent" / "SKILL.md").is_file()


def test_install_skill_requires_force_for_existing_target(tmp_path: Path) -> None:
    source = make_skill(tmp_path / "source" / "cursor-agent")
    dest = tmp_path / "dest"
    plan = build_install_plan(source, normalize_agent("codex"), "global", explicit_dest=dest)
    install_skill(plan)

    with pytest.raises(SkillError):
        install_skill(plan)

    install_skill(plan, force=True)
    assert (dest / "cursor-agent" / "SKILL.md").is_file()


def test_dry_run_does_not_require_force_for_existing_target(tmp_path: Path) -> None:
    source = make_skill(tmp_path / "source" / "cursor-agent")
    dest = tmp_path / "dest"
    plan = build_install_plan(source, normalize_agent("codex"), "global", explicit_dest=dest)
    install_skill(plan)

    install_skill(plan, dry_run=True)

    assert (dest / "cursor-agent" / "SKILL.md").is_file()


def test_resolve_source_candidates_from_explicit_path(tmp_path: Path) -> None:
    source = make_skill(tmp_path / "source" / "cursor-agent")

    candidates = resolve_source_candidates(str(source))

    assert len(candidates) == 1
    assert candidates[0].path == source


def test_resolve_source_candidates_from_exact_from_path(tmp_path: Path) -> None:
    source = make_skill(tmp_path / "source" / "cursor-agent")

    candidates = resolve_source_candidates("cursor-agent", source=str(source))

    assert len(candidates) == 1
    assert candidates[0].path == source


def test_resolve_source_candidates_from_parent_from_path(tmp_path: Path) -> None:
    source = make_skill(tmp_path / "source" / "cursor-agent")

    candidates = resolve_source_candidates("cursor-agent", source=str(source.parent))

    assert len(candidates) == 1
    assert candidates[0].path == source


def test_resolve_source_candidates_from_bundled() -> None:
    candidates = resolve_source_candidates("cursor-agent", source="bundled")

    assert len(candidates) == 1
    assert candidates[0].path.name == "cursor-agent"
    assert (candidates[0].path / "SKILL.md").is_file()
