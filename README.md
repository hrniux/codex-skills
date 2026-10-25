# codex-skills

Public repository for Codex skills.

This repository keeps reusable skills in a simple collection layout:

```text
skills/
  focused-problem-solving/
  github-https-local-auth/
  obsidian-local-vault/
```

## Skills

- `focused-problem-solving`: keeps Codex on a narrow, correctness-first workflow that reduces broad repository exploration, unnecessary file reads, and verbose responses.
- `github-https-local-auth`: keeps GitHub repository operations on HTTPS and reuses existing macOS local Git credentials instead of switching to SSH or starting `gh auth login` flows.
- `obsidian-local-vault`: manages the local Obsidian vault on macOS, including note organization, `.obsidian` settings cleanup, unnamed-note renaming, and safe handling of sensitive notes at the default path `~/Documents/Obsidian Vault`.

## Installation

Each skill is a self-contained directory under `skills/`. To install one, copy it into your Codex skills directory:

```bash
mkdir -p ~/.codex/skills
cp -R skills/focused-problem-solving ~/.codex/skills/
```

For Claude Code, copy into `~/.claude/skills/` instead.

Each skill follows the standard Codex skill structure with `SKILL.md` plus optional `agents/`, `references/`, and `assets/`.

## Validation

Run the dependency-free CLI and diagnostic-recipe regression tests with Python 3.9+ and Git:

```bash
python3 -B -m unittest discover -s tests -v
```
