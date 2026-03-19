# codex-skills

Public repository for Codex skills.

This repository keeps reusable skills in a simple collection layout:

```text
skills/
  github-https-local-auth/
```

Current skills:

- `github-https-local-auth`: keeps GitHub repository operations on HTTPS and reuses existing macOS local Git credentials instead of switching to SSH or starting `gh auth login` flows.

Each skill is self-contained and follows the standard Codex skill structure with `SKILL.md` plus optional `agents/`, `references/`, and `assets/`.
