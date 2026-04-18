# Focused Problem Solving Skill Design

## Goal

Create a platform-neutral Codex skill that improves correctness per token for general coding, debugging, repository, and review tasks. The skill should reduce waste from broad repo exploration, unnecessary file reads, and verbose replies without weakening verification.

## User-Approved Constraints

- Scope: general Codex problem solving
- Priority: correctness first, token savings second
- Waste priority: over-search > over-explain > under-verify
- Environment: platform-neutral
- Skill weight: balanced, roughly 200 to 450 words
- Uncertainty handling: make reasonable low-risk assumptions and act

## Problem

Generic problem-solving behavior often spends too much context on exploratory reading before a concrete lead exists. It also tends to over-explain before the next action is clear. Both issues waste token budget and slow down execution even when the underlying task is small.

## Non-Goals

- Replacing domain-specific skills such as GitHub auth or Obsidian vault handling
- Forcing exhaustive repo audits when the user only asked for a focused task
- Skipping verification to save tokens
- Depending on a specific operating system, shell, or framework

## Deliverables

- `skills/focused-problem-solving/SKILL.md`
- `skills/focused-problem-solving/agents/openai.yaml`
- `skills/focused-problem-solving/assets/icon.svg`
- `README.md` update listing the new skill

## Skill Design

### Triggering Conditions

The skill should trigger for coding, debugging, repo navigation, review, and CLI development tasks where the user benefits from a narrow evidence path and concise replies.

### Core Workflow

1. Classify the task: explain, locate, change, review, or verify.
2. Start from one likely entry point only.
3. Search one keyword, symbol, or error at a time.
4. Read the smallest relevant slice first.
5. Stop exploring once there is enough evidence to state:
   - what to change
   - why this is the right place
   - how to verify it
6. Act directly unless the next step is destructive, expensive, or high-risk ambiguous.
7. Run the smallest complete verification that matches the claim.

### Hard Rules

- No broad repo scans "just in case"
- No multi-file reading without a concrete evidence gap
- No long preambles before the action or conclusion
- No repeated context the user already supplied
- No completion claims without matching verification
- Explicit user requests for deep audit, broad research, or exhaustive testing still override the default narrow behavior

### Red Flags

The skill should explicitly tell the agent to narrow scope if it catches itself:

- opening many files before finding one concrete lead
- searching unrelated keywords in parallel
- writing a long explanation before deciding the next action
- asking clarifying questions that a low-risk assumption would avoid
- claiming success before running the matching check

## Verification Plan

- Capture a fresh no-skill baseline using `codex exec`
- Keep `SKILL.md` self-contained and check its word count
- Validate the repo structure and YAML parsing after edits
- Push to `origin/main` over HTTPS using existing local Git credentials
- Install the skill into local Codex with the GitHub-backed system installer
- Run a fresh `codex exec` session with `$focused-problem-solving` as a smoke test

## Risks And Mitigations

- Too short and vague: include concrete stop conditions and red flags
- Too long and heavy: keep the skill self-contained and avoid auxiliary references
- Too aggressive about narrowing: explicitly allow expansion when there is a real evidence gap
- Installation appears missing in the current session: use a fresh Codex process and remind that restart may be required for long-lived sessions
