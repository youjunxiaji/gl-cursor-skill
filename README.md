# gl-cursor-skill

`gl-cursor-skill` installs AI-agent skills between common local skill folders.

Primary usage:

```bash
uvx gl-cursor-skill add cursor-agent
```

The `cursor-agent` skill is bundled with this package, so the command works even when the source skill does not already exist on the machine.

When options are omitted in an interactive terminal, the CLI asks where to install:

```text
? Install for which agent?
  Codex
  Claude Code
  OpenCode

? Install scope?
  Global
  Project
```

For scripts, pass the choices explicitly:

```bash
uvx gl-cursor-skill add cursor-agent --agent codex --scope global --from bundled --yes
```

## Supported Targets

| Agent | Global target | Project target |
| --- | --- | --- |
| Codex | `~/.codex/skills` | `.codex/skills` |
| Claude Code | `~/.claude/skills` | `.claude/skills` |
| OpenCode | `~/.config/opencode/skills` | `.opencode/skills` |

`claude` and `claudecode` are accepted aliases for `claude-code`. `open-code` is an alias for `opencode`.

## Commands

```bash
gl-cursor-skill add <skill>
gl-cursor-skill agents
gl-cursor-skill list
```

Examples:

```bash
# Interactive install
uvx gl-cursor-skill add cursor-agent

# Non-interactive install from Claude global skills into Codex global skills
uvx gl-cursor-skill add cursor-agent --agent codex --scope global --from claude --yes

# Non-interactive install from the bundled cursor-agent skill
uvx gl-cursor-skill add cursor-agent --agent codex --scope global --from bundled --yes

# Install from an explicit local path
uvx gl-cursor-skill add /path/to/cursor-agent --agent codex --scope global --yes

# Preview without copying files
uvx gl-cursor-skill add cursor-agent --agent codex --scope global --from claude --dry-run --yes

# Overwrite an existing target skill
uvx gl-cursor-skill add cursor-agent --agent codex --scope global --from claude --force --yes
```

## Development

```bash
uv sync
uv run pytest
uv run gl-cursor-skill --help
uv build
```

## Releasing

CI (`.github/workflows/ci.yml`) tests and builds on every push and PR. Publishing to PyPI (`.github/workflows/publish.yml`) runs automatically when a GitHub Release is published — PyPI Trusted Publishing is already configured, so no token is needed.

To cut a release: bump the version in `pyproject.toml` and `src/gl_cursor_skill/__init__.py`, then publish a GitHub Release tagged `vX.Y.Z`. The tag must match the package version (e.g. `0.2.0` → `v0.2.0`), or the publish workflow fails its check.
