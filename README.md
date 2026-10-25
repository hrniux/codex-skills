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

Run the repository catalog and contributor self-check with Python 3.9+:

```bash
python3 -B scripts/validate_skills.py
python3 -B scripts/validate_skills.py --format json
```

The command discovers every immediate directory under `skills/`, prints a deterministic catalog, and exits with status 1 when metadata or local files fail validation. `--root /path/to/repository` checks another checkout. JSON output has `schema_version`, `ok`, `skills` (names, descriptions, display names, resource files), and actionable `errors`. CI runs the real collection check as well as the regression suite.

### Repository metadata contract

The self-check supports this repository's deliberately small YAML-compatible format; it is not a general YAML parser. Unsupported syntax is a validation error. Use UTF-8, spaces, blank lines or whole-line comments, and the following fields:

- `SKILL.md` starts and ends its frontmatter with `---` and has exactly `name` and `description` as nonempty single-line strings. Names use lowercase letters, digits and single hyphens and match the directory.
- `agents/openai.yaml` has `interface:` and `policy:` mappings. Child keys have two spaces. Required interface strings are `display_name`, `short_description`, `icon_small`, and `icon_large`; optional strings are `brand_color` (quoted `#RRGGBB`) and `default_prompt`.
- Required policy fields are `products` (a nonempty block list of distinct string items, with a consistent two or four spaces before every `-`) and `allow_implicit_invocation` (literal `true` or `false`). Duplicate and unknown fields fail.
- String values can be JSON double-quoted strings, YAML single-quoted strings with doubled apostrophes, or plain text. Quote values starting with YAML punctuation or a number, ending in `:`, containing `: ` or an inline ` #`, or equal to YAML boolean/null words. Values must contain valid Unicode; unpaired surrogate escapes fail validation. Multiline values, flow collections, aliases, tags, tabs and inline comments are unsupported.

Both icons must resolve to files inside their skill. Files under `assets/`, `references/`, and `scripts/` appear in the catalog; escaping symlinks and symlink resource directories fail. The checker examines `SKILL.md` and Markdown reference documents for inline Markdown links with whitespace-free destinations (optionally enclosed in `<...>`; encode spaces as `%20`) and backtick paths beginning with `assets/`, `references/`, or `scripts/`, outside fenced examples. Inline links resolve from their document, and backtick resource paths resolve from the skill root. URL-encoded paths are decoded; fragments are ignored. Local targets must be existing files inside the skill. External URLs and fragment-only links are skipped. Reference-style links, raw HTML, and fragment/anchor existence are outside this check.

Run the dependency-free CLI and diagnostic-recipe regression tests with Python 3.9+ and Git:

```bash
python3 -B -m unittest discover -s tests -v
```
