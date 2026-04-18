# codex-skills

Public repository for Codex skills.

This repository keeps reusable skills in a simple collection layout:

```text
skills/
  github-https-local-auth/
  obsidian-local-vault/
```

Current skills:

- `github-https-local-auth`: keeps GitHub repository operations on HTTPS and reuses existing macOS local Git credentials instead of switching to SSH or starting `gh auth login` flows.
- `focused-problem-solving`: keeps Codex on a narrow, correctness-first workflow that reduces broad repository exploration, unnecessary file reads, and verbose responses.
- `obsidian-local-vault`: manages the local Obsidian vault on macOS, including note organization, `.obsidian` settings cleanup, unnamed-note renaming, and safe handling of sensitive notes at the default path `/Users/bingbing/Documents/Obsidian Vault`.

Each skill is self-contained and follows the standard Codex skill structure with `SKILL.md` plus optional `agents/`, `references/`, and `assets/`.
