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
  Cursor
  Claude Code

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
| Cursor | `~/.cursor/skills` | `.cursor/skills` |

`claude` and `claudecode` are accepted aliases for `claude-code`.

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

## Release From GitHub

The repository includes GitHub Actions workflows:

- `.github/workflows/ci.yml` runs tests and builds the package on push and pull requests.
- `.github/workflows/publish.yml` publishes to PyPI when a GitHub Release is published.

Recommended setup:

1. Create a GitHub repository and push this project.
2. On PyPI, configure a Trusted Publisher for project `gl-cursor-skill`.
3. Use these PyPI Trusted Publisher values:

```text
Owner: <your GitHub username or org>
Repository name: <your repo name>
Workflow name: publish.yml
Environment name: pypi
```

4. For each release, bump the version in `pyproject.toml`, tag the commit as `vX.Y.Z`, and publish a GitHub Release from that tag.

The workflow checks that the release tag matches the package version. For example, version `0.1.0` must be released with tag `v0.1.0`.

Manual local publish also works:

```bash
UV_PUBLISH_TOKEN="pypi-..." uv publish
```

If you configure PyPI Trusted Publishing in CI, `uv publish` can run without a token.
