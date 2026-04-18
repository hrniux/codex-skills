# Focused Problem Solving Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a platform-neutral skill that keeps Codex accurate while reducing waste from broad search, unnecessary file reads, and verbose responses, then install it locally and publish it to `origin/main`.

**Architecture:** The implementation stays lightweight: a self-contained `SKILL.md`, a small OpenAI manifest, a simple SVG icon, and a README entry. Verification combines a pre-skill baseline, post-change structural checks, a fresh-session smoke test, and GitHub-backed installation through the system skill installer.

**Tech Stack:** Markdown, YAML, SVG, Git, Codex CLI, system `skill-installer`

---

### Task 1: Capture The Baseline

**Files:**
- Read: `/tmp/focused_problem_solving_baseline.txt`

- [ ] **Step 1: Run the baseline prompt before the skill exists**

```bash
codex exec --skip-git-repo-check --sandbox read-only -C /Users/bingbing/codex-skills -o /tmp/focused_problem_solving_baseline.txt "用户说：帮我在一个陌生仓库里定位‘开始游戏’按钮文案在哪个文件，同时尽量节省 token。请直接给出你的默认工作流，不要执行命令。"
```

Expected: a fresh Codex answer with no `$focused-problem-solving` skill available yet.

- [ ] **Step 2: Inspect the baseline output**

```bash
sed -n '1,200p' /tmp/focused_problem_solving_baseline.txt
```

Expected: enough detail to identify waste patterns that the new skill should suppress.

### Task 2: Add The Skill Package

**Files:**
- Create: `skills/focused-problem-solving/SKILL.md`
- Create: `skills/focused-problem-solving/agents/openai.yaml`
- Create: `skills/focused-problem-solving/assets/icon.svg`
- Modify: `README.md`

- [ ] **Step 1: Write the skill document**

```markdown
---
name: focused-problem-solving
description: Use when solving coding, debugging, review, or repository tasks where correctness matters but unnecessary repository exploration, file reads, and verbose output should be minimized.
---

# Focused Problem Solving

Use this skill to solve technical tasks with a narrow evidence path. Optimize for correctness first, then cut waste from broad searches, unnecessary file reads, repeated explanations, and oversized plans.

## Default Loop

1. Classify the task: explain, locate, change, review, or verify.
2. Start from one likely entry point only: a user-named path, an exact text or error match, or the repo entry file.
3. Search narrowly. Prefer one keyword, symbol, or error at a time. Read the smallest relevant slice first.
4. Stop exploring once you can state what to change, why this is the right place, and how to verify it.
5. Act directly unless the next step is destructive, expensive, or high-risk ambiguous.
6. Verify with the smallest complete check that matches the claim.

## Hard Rules

- Do not scan the whole repo "just in case."
- Do not read several adjacent files unless the first read leaves a real evidence gap.
- Lead with the conclusion and next action; add only the support the user needs.
- Keep updates short and non-repetitive.
- Do not replace verification with confidence.
- If the user explicitly asks for a broad audit, deep research, or exhaustive testing, do that instead.

## Red Flags

Narrow scope immediately if you catch yourself:

- opening many files before one concrete lead exists
- searching multiple unrelated terms in parallel
- repeating repository context the user already gave
- asking clarifying questions a safe assumption would avoid
- claiming success before the matching check runs
```

- [ ] **Step 2: Write the OpenAI skill manifest**

```yaml
interface:
  display_name: "Focused Problem Solving"
  short_description: "Solve technical tasks with a narrower search path and smaller context."
  icon_small: "./assets/icon.svg"
  icon_large: "./assets/icon.svg"
  brand_color: "#FF7A30"
  default_prompt: "Use $focused-problem-solving to solve this technical task accurately with minimal unnecessary exploration."
policy:
  products:
    - "chatgpt"
    - "codex"
    - "api"
    - "atlas"
  allow_implicit_invocation: true
```

- [ ] **Step 3: Add the icon asset**

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" role="img" aria-labelledby="title">
  <title>Focused Problem Solving</title>
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FFF4E8" />
      <stop offset="100%" stop-color="#FFD4B3" />
    </linearGradient>
  </defs>
  <rect width="128" height="128" rx="28" fill="url(#bg)" />
  <circle cx="64" cy="64" r="34" fill="none" stroke="#1D1D1F" stroke-width="8" />
  <circle cx="64" cy="64" r="13" fill="#FF7A30" />
  <path d="M64 18v18M64 92v18M18 64h18M92 64h18" stroke="#1D1D1F" stroke-width="8" stroke-linecap="round" />
</svg>
```

- [ ] **Step 4: Update the README skill list**

```markdown
- `focused-problem-solving`: keeps Codex on a narrow, correctness-first workflow that reduces broad repository exploration, unnecessary file reads, and verbose responses.
```

- [ ] **Step 5: Commit the implementation**

```bash
git add README.md skills/focused-problem-solving
git commit -m "feat: add focused problem solving skill"
```

### Task 3: Verify Package Quality

**Files:**
- Read: `skills/focused-problem-solving/SKILL.md`
- Read: `skills/focused-problem-solving/agents/openai.yaml`

- [ ] **Step 1: Check the skill word count**

```bash
wc -w skills/focused-problem-solving/SKILL.md
```

Expected: the skill stays in the intended lightweight range and avoids becoming a heavy always-loaded document.

- [ ] **Step 2: Validate the manifest parses as YAML**

```bash
python3 - <<'PY'
import pathlib
import yaml
path = pathlib.Path("skills/focused-problem-solving/agents/openai.yaml")
print(yaml.safe_load(path.read_text()))
PY
```

Expected: parsed YAML object prints with no exception.

- [ ] **Step 3: Check the README entry and file layout**

```bash
rg -n "focused-problem-solving" README.md skills/focused-problem-solving
```

Expected: README and skill files both reference the new skill.

### Task 4: Publish, Install, And Smoke Test

**Files:**
- Read: `/tmp/focused_problem_solving_after.txt`
- Install target: `~/.codex/skills/focused-problem-solving`

- [ ] **Step 1: Push the repo over HTTPS**

```bash
git push origin main
```

Expected: push completes without switching away from the existing HTTPS remote.

- [ ] **Step 2: Install the published skill into local Codex**

```bash
python3 /Users/bingbing/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py --url https://github.com/hrniux/codex-skills/tree/main/skills/focused-problem-solving
```

Expected: install succeeds into `~/.codex/skills/focused-problem-solving` and reminds that restarting Codex may be needed.

- [ ] **Step 3: Run a fresh-session smoke test with the installed skill**

```bash
codex exec --skip-git-repo-check --sandbox read-only -C /Users/bingbing/codex-skills -o /tmp/focused_problem_solving_after.txt '$focused-problem-solving 用户说：帮我在一个陌生仓库里定位“开始游戏”按钮文案在哪个文件，同时尽量节省 token。请直接给出你的默认工作流，不要执行命令。'
```

Expected: the fresh Codex session accepts the explicit skill invocation and returns a narrower workflow than the baseline.

- [ ] **Step 4: Inspect the smoke-test output**

```bash
sed -n '1,200p' /tmp/focused_problem_solving_after.txt
```

Expected: the answer emphasizes one entry point, narrow search, stop conditions, concise output, and matching verification.
