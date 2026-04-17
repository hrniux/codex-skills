---
name: obsidian-local-vault
description: Use when working in the local Obsidian vault on macOS, especially to audit or reorganize notes, rename untitled files, maintain .obsidian settings, manage templates/frontmatter/links, or operate on the default vault at /Users/bingbing/Documents/Obsidian Vault.
---

# Obsidian Local Vault

## Overview

Use this skill for filesystem-level management of a local Obsidian vault. It is for notes, folders, markdown files, and `.obsidian/*.json` settings, not for clicking the Obsidian GUI.

Default vault path: `/Users/bingbing/Documents/Obsidian Vault`

If the user gives another vault path, use that instead. If no path is given, assume the default path above and verify it exists before editing.

## Quick Start

1. Work inside the vault root, not inside `.obsidian/`, unless the task is specifically about settings.
2. Run `scripts/audit_vault.py --vault "/Users/bingbing/Documents/Obsidian Vault"` first to get a JSON summary of:
   - note counts
   - top-level folders
   - unnamed notes
   - missing workspace references
   - config highlights from `.obsidian/app.json`
   - sensitive-note candidates without printing secret values
3. Read only the notes and config files needed for the requested cleanup.
4. Make low-risk structural changes directly when the user asks to organize the vault; preserve content and avoid destructive cleanup.
5. Re-run the audit after edits and validate modified `.json` files before claiming completion.

## Default Rules

- Prefer filesystem edits over GUI instructions. Obsidian UI clicks are not the primary surface.
- Treat `90-敏感记录/` and any note containing tokens, passwords, API keys, or account credentials as sensitive.
- Do not echo secret values back to the user unless they explicitly ask for those exact values.
- If you rename notes, also update `.obsidian/workspace.json` and any internal links that still point to old names.
- If the vault is sparse or messy, prefer a simple structure over elaborate taxonomy.

## Recommended Layout

When the user asks for a first-pass cleanup and there is no stronger existing taxonomy, prefer:

- `00-首页`
- `10-收集箱`
- `11-附件`
- `20-配置与工具`
- `30-资料摘录`
- `40-渠道记录`
- `90-敏感记录`

Use [references/vault-layout.md](references/vault-layout.md) for the rationale and exact defaults.

## High-Value Operations

### Audit and triage

- Identify unnamed notes such as `未命名.md` or `未命名 1.md`.
- Identify notes without a first-level heading.
- Check whether `.obsidian/workspace.json` references files that no longer exist.
- Check whether `alwaysUpdateLinks`, `newFileFolderPath`, and `attachmentFolderPath` are aligned with the intended workflow.

### Safe structural cleanup

- Rename untitled notes to semantic names based on actual content.
- Move notes into a small number of clearly named folders.
- Add a lightweight home note with links when the vault has no obvious entry point.
- Keep attachments out of the root when the user wants a cleaner vault.

### Settings cleanup

- For organized vault workflows, prefer:
  - `alwaysUpdateLinks = true`
  - `newFileLocation = "folder"`
  - `newFileFolderPath = "10-收集箱"`
  - `attachmentFolderPath = "11-附件"`
- Validate edited JSON files after any change.

### Sensitive content handling

- Keep passwords, tokens, and credentials isolated from ordinary notes.
- Do not move sensitive notes into public repositories unless the user explicitly asks.
- If a note is a mixed dump of commands plus secrets, prefer separating it into smaller notes only when the user wants deeper cleanup.

## Verification

- Re-run `scripts/audit_vault.py` after edits.
- Parse modified `.obsidian/*.json` files with a real JSON parser.
- Search for stale old note names in markdown links and `workspace.json`.
- Report the final folder layout and changed notes clearly.

## Examples

- "Organize my Obsidian vault at `/Users/bingbing/Documents/Obsidian Vault`."
- "Rename untitled notes and update the workspace."
- "Audit my `.obsidian` settings and make them cleaner."
- "Separate sensitive notes from general notes in my local vault."

## Resources

- `scripts/audit_vault.py`: JSON audit of the local vault without printing secret values.
- `references/vault-layout.md`: Recommended structure, default path, and cleanup defaults for this specific vault.
