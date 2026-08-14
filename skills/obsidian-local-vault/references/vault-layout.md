# Obsidian Local Vault Defaults

## Default Path

- Primary local vault path: `~/Documents/Obsidian Vault` (override with the `OBSIDIAN_VAULT` environment variable).
- If the user explicitly provides another path, prefer the user-provided path.

## Recommended First-Pass Structure

Use this structure when the vault is sparse, flat, or obviously ad hoc:

- `00-首页`: home note, navigation, index notes
- `10-收集箱`: new uncategorized notes
- `11-附件`: images, screenshots, exported files
- `20-配置与工具`: config snippets, shell commands, CLI notes
- `30-资料摘录`: long copied notes, tutorials, excerpts
- `40-渠道记录`: links, sources, vendor/channel notes
- `90-敏感记录`: passwords, tokens, account notes, recovery info

## Cleanup Priorities

1. Replace `未命名*.md` with semantic names based on content.
2. Move obvious sensitive notes away from the root.
3. Add a home note when there is no stable entry point.
4. Keep the layout shallow unless the vault grows enough to justify more depth.

## `.obsidian` Defaults

These settings are strong defaults for a personal vault that is still being organized:

- `alwaysUpdateLinks = true`
- `newFileLocation = "folder"`
- `newFileFolderPath = "10-收集箱"`
- `attachmentFolderPath = "11-附件"`

## Sensitive Content Rules

- Detect and isolate notes that contain passwords, tokens, `sk-` keys, API credentials, or account recovery details.
- Do not print or summarize secret values in chat unless the user explicitly requests those values.
- Prefer reporting note paths and risk categories instead of secret contents.
