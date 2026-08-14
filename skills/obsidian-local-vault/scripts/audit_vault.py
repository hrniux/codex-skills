#!/usr/bin/env python3
"""Audit a local Obsidian vault and print a safe JSON summary."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

DEFAULT_VAULT = Path(
    os.environ.get("OBSIDIAN_VAULT", str(Path.home() / "Documents" / "Obsidian Vault"))
)
UNTITLED_RE = re.compile(r"^未命名(?: \d+)?\.md$")
WORKSPACE_FILE_RE = re.compile(r'"file"\s*:\s*"([^"]+)"')

SENSITIVE_PATTERNS = {
    "password-assignment": re.compile(r"(password|密码|主密码)\s*[:=]", re.IGNORECASE),
    "secret-assignment": re.compile(
        r"(?:export\s+)?[A-Z0-9_]*(?:TOKEN|KEY|SECRET|PASSWORD)[A-Z0-9_]*\s*=",
        re.IGNORECASE,
    ),
    "anthropic-env": re.compile(r"ANTHROPIC_AUTH_TOKEN\s*=", re.IGNORECASE),
    "openai-key": re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit an Obsidian vault.")
    parser.add_argument("--vault", default=str(DEFAULT_VAULT), help="Vault root path")
    parser.add_argument(
        "--headingless-limit",
        type=int,
        default=20,
        help="Maximum headingless notes to list",
    )
    parser.add_argument(
        "--sensitive-limit",
        type=int,
        default=20,
        help="Maximum sensitive candidates to list",
    )
    return parser.parse_args()


def rel_path(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def safe_read_text(path: Path) -> str:
    try:
      return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
      return path.read_text(encoding="utf-8", errors="replace")


def first_non_empty_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def detect_sensitive_reasons(text: str, path_text: str) -> list[str]:
    reasons: list[str] = []
    if "敏感" in path_text:
        reasons.append("sensitive-folder-name")
    for label, pattern in SENSITIVE_PATTERNS.items():
        if pattern.search(text):
            reasons.append(label)
    return sorted(set(reasons))


def load_json_if_exists(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(safe_read_text(path))


def collect_workspace_refs(root: Path) -> tuple[list[str], list[str]]:
    workspace_path = root / ".obsidian" / "workspace.json"
    if not workspace_path.exists():
        return [], []

    workspace_text = safe_read_text(workspace_path)
    refs = sorted(set(WORKSPACE_FILE_RE.findall(workspace_text)))
    missing = [ref for ref in refs if not (root / ref).exists()]
    return refs, missing


def main() -> None:
    args = parse_args()
    root = Path(args.vault).expanduser().resolve()

    if not root.exists():
        raise SystemExit(json.dumps({"ok": False, "error": f"vault not found: {root}"}))

    md_files = sorted(path for path in root.rglob("*.md") if ".obsidian" not in path.parts)
    unnamed_notes: list[str] = []
    notes_without_heading: list[str] = []
    sensitive_candidates: list[dict[str, object]] = []
    frontmatter_count = 0

    for path in md_files:
        path_text = rel_path(root, path)
        if UNTITLED_RE.match(path.name):
            unnamed_notes.append(path_text)

        text = safe_read_text(path)
        if text.startswith("---\n"):
            frontmatter_count += 1

        first_line = first_non_empty_line(text)
        if not first_line.startswith("#"):
            notes_without_heading.append(path_text)

        reasons = detect_sensitive_reasons(text, path_text)
        if reasons:
            sensitive_candidates.append({"path": path_text, "reasons": reasons})

    app_json = load_json_if_exists(root / ".obsidian" / "app.json") or {}
    workspace_refs, missing_workspace_files = collect_workspace_refs(root)

    top_dirs = sorted(
        rel_path(root, path)
        for path in root.iterdir()
        if path.is_dir() and path.name != ".obsidian"
    )
    obsidian_files = sorted(
        rel_path(root, path)
        for path in (root / ".obsidian").glob("*")
        if path.is_file()
    ) if (root / ".obsidian").exists() else []

    report = {
        "ok": True,
        "vault": str(root),
        "md_count": len(md_files),
        "top_level_dirs": top_dirs,
        "top_level_md": sorted(
            rel_path(root, path)
            for path in root.glob("*.md")
        ),
        "unnamed_notes": unnamed_notes,
        "frontmatter_count": frontmatter_count,
        "notes_without_heading": notes_without_heading[: args.headingless_limit],
        "notes_without_heading_total": len(notes_without_heading),
        "obsidian_files": obsidian_files,
        "app_config": {
            "alwaysUpdateLinks": app_json.get("alwaysUpdateLinks"),
            "newFileLocation": app_json.get("newFileLocation"),
            "newFileFolderPath": app_json.get("newFileFolderPath"),
            "attachmentFolderPath": app_json.get("attachmentFolderPath"),
        },
        "workspace_refs": workspace_refs,
        "missing_workspace_files": missing_workspace_files,
        "sensitive_candidates": sensitive_candidates[: args.sensitive_limit],
        "sensitive_candidate_total": len(sensitive_candidates),
    }

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
