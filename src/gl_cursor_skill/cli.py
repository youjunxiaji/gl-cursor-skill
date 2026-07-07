from __future__ import annotations

from pathlib import Path
import sys
from typing import Optional

import questionary
from rich.console import Console
from rich.table import Table
import typer

from . import __version__
from .agents import AGENTS, agent_choices, normalize_agent
from .core import (
    SkillCandidate,
    SkillError,
    build_install_plan,
    install_skill,
    known_source_dirs,
    normalize_scope,
    resolve_source_candidates,
)


app = typer.Typer(
    add_completion=False,
    help="Install AI-agent skills between Claude, Codex, Cursor, and project scopes.",
    no_args_is_help=True,
)
console = Console()


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"gl-cursor-skill {__version__}")
        raise typer.Exit()


@app.callback()
def callback(
    version: bool = typer.Option(
        False,
        "--version",
        help="Show the installed gl-cursor-skill version.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    pass


@app.command()
def agents() -> None:
    """Show known agent skill directories."""
    table = Table(title="Known agent skill directories")
    table.add_column("Agent")
    table.add_column("Global")
    table.add_column("Project")

    for agent in AGENTS:
        table.add_row(agent.label, str(agent.global_dir), str(agent.project_dir))

    console.print(table)


@app.command(name="list")
def list_skills(
    project_dir: Optional[Path] = typer.Option(
        None,
        "--project-dir",
        "-p",
        help="Project root used when listing project skill folders.",
    ),
) -> None:
    """List discovered local skills."""
    table = Table(title="Discovered skills")
    table.add_column("Source")
    table.add_column("Skill")
    table.add_column("Path")

    found_any = False
    for base in known_source_dirs(project_dir):
        if not base.path.is_dir():
            continue
        for child in sorted(base.path.iterdir(), key=lambda item: item.name.lower()):
            if child.is_dir() and (child / "SKILL.md").is_file():
                found_any = True
                table.add_row(base.label, child.name, str(child))

    if found_any:
        console.print(table)
    else:
        console.print("[yellow]No skills found in known directories.[/yellow]")


@app.command()
def add(
    skill: Optional[str] = typer.Argument(
        None,
        help="Skill name or path to a skill directory containing SKILL.md.",
    ),
    agent: Optional[str] = typer.Option(
        None,
        "--agent",
        "-a",
        help="Target agent: codex, cursor, or claude-code.",
    ),
    scope: Optional[str] = typer.Option(
        None,
        "--scope",
        "-s",
        help="Install scope: global or project.",
    ),
    source: Optional[str] = typer.Option(
        None,
        "--from",
        "-f",
        help="Source agent or path. Examples: bundled, claude, codex, cursor, /path/to/skill.",
    ),
    project_dir: Optional[Path] = typer.Option(
        None,
        "--project-dir",
        "-p",
        help="Project root used for project scope and project-source discovery.",
    ),
    dest: Optional[Path] = typer.Option(
        None,
        "--dest",
        help="Override the destination skills directory.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Overwrite the target skill if it already exists.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Print the planned install without copying files.",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Do not prompt; use defaults where possible.",
    ),
) -> None:
    """Install a skill into an agent's global or project skill directory."""
    interactive = _can_prompt(yes)
    project_root = project_dir.expanduser() if project_dir is not None else Path.cwd()

    try:
        skill_name = _resolve_skill_arg(skill, interactive)
        target_agent = normalize_agent(agent) if agent else _choose_agent(interactive, yes)
        target_scope = normalize_scope(scope) if scope else _choose_scope(interactive, yes)
        source_dir = _choose_source(skill_name, source, project_root, interactive, yes)
        plan = build_install_plan(source_dir, target_agent, target_scope, project_root, dest)
        _print_plan(plan, dry_run, force)
        install_skill(plan, force=force, dry_run=dry_run)
    except (SkillError, ValueError) as error:
        console.print(f"[red]Error:[/red] {error}")
        raise typer.Exit(code=1) from error

    if dry_run:
        console.print("[cyan]Dry run complete. No files were changed.[/cyan]")
    else:
        console.print(f"[green]Installed[/green] {plan.skill_name} -> {plan.target_dir}")
        console.print("Restart the target agent if it does not pick up new skills automatically.")


def _can_prompt(yes: bool) -> bool:
    return not yes and sys.stdin.isatty() and sys.stdout.isatty()


def _resolve_skill_arg(skill: Optional[str], interactive: bool) -> str:
    if skill:
        return skill
    if not interactive:
        raise SkillError("Skill is required in non-interactive mode.")
    answer = questionary.text("Skill name or path:").ask()
    if not answer:
        raise SkillError("Skill is required.")
    return answer


def _choose_agent(interactive: bool, yes: bool):
    if yes:
        return normalize_agent("codex")
    if not interactive:
        raise SkillError("Missing --agent in non-interactive mode.")

    choices = [questionary.Choice(title=label, value=value) for label, value in agent_choices()]
    answer = questionary.select("Install for which agent?", choices=choices).ask()
    if not answer:
        raise SkillError("Target agent is required.")
    return normalize_agent(answer)


def _choose_scope(interactive: bool, yes: bool) -> str:
    if yes:
        return "global"
    if not interactive:
        raise SkillError("Missing --scope in non-interactive mode.")

    answer = questionary.select(
        "Install scope?",
        choices=[
            questionary.Choice(title="Global", value="global"),
            questionary.Choice(title="Project", value="project"),
        ],
    ).ask()
    if not answer:
        raise SkillError("Scope is required.")
    return normalize_scope(answer)


def _choose_source(
    skill: str,
    source: Optional[str],
    project_root: Path,
    interactive: bool,
    yes: bool,
) -> Path:
    candidates = resolve_source_candidates(skill, source, project_root)
    if not candidates:
        hint = f" from '{source}'" if source else ""
        raise SkillError(f"Could not find skill '{skill}'{hint}.")

    if len(candidates) == 1:
        return candidates[0].path

    if yes:
        return candidates[0].path

    if not interactive:
        lines = "\n".join(f"- {candidate.label}: {candidate.path}" for candidate in candidates)
        raise SkillError(f"Multiple source skills found; pass --from or run interactively.\n{lines}")

    choices = [
        questionary.Choice(title=f"{candidate.label}: {candidate.path}", value=str(index))
        for index, candidate in enumerate(candidates)
    ]
    answer = questionary.select("Install from which source?", choices=choices).ask()
    if answer is None:
        raise SkillError("Source selection is required.")
    return candidates[int(answer)].path


def _print_plan(plan, dry_run: bool, force: bool) -> None:
    table = Table(title="Install plan")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("Skill", plan.skill_name)
    table.add_row("Target agent", plan.target_agent.label)
    table.add_row("Scope", plan.scope)
    table.add_row("Source", str(plan.source_dir))
    table.add_row("Destination", str(plan.target_dir))
    table.add_row("Target exists", "yes" if plan.target_dir.exists() else "no")
    table.add_row("Mode", "dry-run" if dry_run else "copy")
    table.add_row("Overwrite", "yes" if force else "no")
    console.print(table)
    if dry_run and plan.target_dir.exists() and not force:
        console.print("[yellow]Target already exists; actual install would need --force.[/yellow]")


def main() -> None:
    app()
