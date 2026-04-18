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
- Do not enumerate fallback branches before evidence requires them.
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
