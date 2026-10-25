"""Exercise the audit CLI with disposable vaults and no third-party packages."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills/obsidian-local-vault/scripts/audit_vault.py"
)


class AuditVaultTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "vault"
        self.root.mkdir()
        (self.root / ".obsidian").mkdir()

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def run_audit(self, *args, vault=None, environment=None):
        command = [sys.executable, str(SCRIPT)]
        if vault is not False:
            command += ["--vault", str(self.root if vault is None else vault)]
        return subprocess.run(
            [*command, *args], capture_output=True, text=True, env=environment
        )

    def report(self, *args):
        result = self.run_audit(*args)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        return json.loads(result.stdout)

    def assert_controlled_error(self, result):
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("Traceback", result.stderr)
        self.assertFalse(json.loads(result.stderr)["ok"])

    def test_empty_vault_keeps_report_fields(self):
        report = self.report()
        self.assertTrue(report["ok"])
        self.assertEqual(report["md_count"], 0)
        self.assertEqual(report["workspace_refs"], [])
        self.assertEqual(report["sensitive_candidates"], [])

    def test_workspace_paths_are_decoded_deduplicated_and_sorted(self):
        names = ['中文.md', 'a"quote.md', 'back\\slash.md']
        for name in names:
            self.write(name, "# Heading\n")
        workspace = {"children": [{"file": name} for name in names * 2]}
        self.write(".obsidian/workspace.json", json.dumps(workspace))
        report = self.report()
        self.assertEqual(report["workspace_refs"], sorted(names))
        self.assertEqual(report["missing_workspace_files"], [])

    def test_missing_workspace_paths_remain_reported(self):
        self.write(".obsidian/workspace.json", '{"file":"absent.md"}')
        self.assertEqual(self.report()["missing_workspace_files"], ["absent.md"])

    def test_workspace_refs_cannot_resolve_outside_vault(self):
        outside = Path(self.temporary.name) / "outside.md"
        outside.write_text("# Outside\n", encoding="utf-8")
        refs = ["../outside.md", str(outside)]
        self.write(".obsidian/workspace.json", json.dumps([{"file": ref} for ref in refs]))
        self.assertEqual(self.report()["missing_workspace_files"], sorted(refs))

    def test_directory_with_markdown_suffix_is_not_a_note(self):
        (self.root / "folder.md").mkdir()
        self.write("folder.md/note.md", "# Heading\n")
        report = self.report()
        self.assertEqual(report["md_count"], 1)
        self.assertEqual(report["top_level_md"], [])

    def test_deleted_notes_do_not_affect_live_vault_audit(self):
        self.write("active.md", "# Active\n")
        self.write(".trash/未命名.md", "password: SYNTHETIC_DELETED_VALUE\n")
        self.write(".trash/nested/deleted.md", "Deleted note\n")
        self.write(".obsidian/internal.md", "Internal data\n")
        report = self.report()
        self.assertEqual(report["md_count"], 1)
        self.assertEqual(report["top_level_dirs"], [])
        self.assertEqual(report["unnamed_notes"], [])
        self.assertEqual(report["notes_without_heading_total"], 0)
        self.assertEqual(report["sensitive_candidate_total"], 0)

    def test_user_hidden_folders_and_nested_trash_remain_live_notes(self):
        self.write(".md", "# Hidden note filename\n")
        self.write(".notes/hidden.md", "# Hidden note\n")
        self.write("projects/.trash/reference.md", "# User folder\n")
        self.write("projects/.obsidian/internal.md", "Internal data\n")
        report = self.report()
        self.assertEqual(report["md_count"], 3)
        self.assertEqual(report["top_level_md"], [".md"])
        self.assertEqual(report["top_level_dirs"], [".notes", "projects"])

    def test_workspace_reference_to_deleted_file_is_still_checked_for_existence(self):
        self.write(".trash/deleted.md", "Deleted note\n")
        refs = [".trash/deleted.md", ".trash/missing.md"]
        self.write(".obsidian/workspace.json", json.dumps([{"file": ref} for ref in refs]))
        report = self.report()
        self.assertEqual(report["md_count"], 0)
        self.assertEqual(report["workspace_refs"], refs)
        self.assertEqual(report["missing_workspace_files"], [".trash/missing.md"])

    def test_existing_file_is_not_a_vault(self):
        file_path = self.write("note.md", "# Heading\n")
        self.assert_controlled_error(self.run_audit(vault=file_path))

    def test_invalid_app_json_has_controlled_error(self):
        self.write(".obsidian/app.json", "{broken")
        self.assert_controlled_error(self.run_audit())

    def test_app_json_must_be_an_object(self):
        for value in ([], [1], "text", True, 1):
            with self.subTest(value=value):
                self.write(".obsidian/app.json", json.dumps(value))
                self.assert_controlled_error(self.run_audit())

    def test_invalid_workspace_json_has_controlled_error(self):
        self.write(".obsidian/workspace.json", "{broken")
        self.assert_controlled_error(self.run_audit())

    def make_symlink(self, link, target):
        try:
            link.symlink_to(target)
        except (OSError, NotImplementedError) as error:
            self.skipTest(f"Symlinks unavailable: {error}")

    def test_external_note_symlink_is_not_read_or_listed(self):
        outside = Path(self.temporary.name) / "outside.md"
        outside.write_text("password: DO_NOT_PRINT_SYNTHETIC_SECRET\n", encoding="utf-8")
        self.make_symlink(self.root / "linked.md", outside)
        report = self.report()
        self.assertEqual(report["md_count"], 0)
        self.assertEqual(report["top_level_md"], [])
        self.assertEqual(report["sensitive_candidates"], [])

    def test_internal_note_symlink_can_be_a_note(self):
        note = self.write("nested/note.md", "# Heading\n")
        self.make_symlink(self.root / "linked.md", note)
        self.assertEqual(self.report()["md_count"], 2)

    def test_directory_symlinks_do_not_reintroduce_internal_or_external_notes(self):
        self.write(".obsidian/internal.md", "Internal data\n")
        self.write(".trash/deleted.md", "Deleted note\n")
        outside = Path(self.temporary.name) / "outside"
        outside.mkdir()
        (outside / "external.md").write_text("External note\n", encoding="utf-8")
        for name, target in (
            ("config-copy", self.root / ".obsidian"),
            ("trash-copy", self.root / ".trash"),
            ("external-copy", outside),
        ):
            self.make_symlink(self.root / name, target)
        self.assertEqual(self.report()["md_count"], 0)

    def test_external_settings_symlink_is_rejected_without_reading(self):
        outside = Path(self.temporary.name) / "outside.json"
        outside.write_text('{"newFileFolderPath":"DO_NOT_PRINT_SYNTHETIC_SECRET"}', encoding="utf-8")
        for filename in ("app.json", "workspace.json"):
            with self.subTest(filename=filename):
                link = self.root / ".obsidian" / filename
                self.make_symlink(link, outside)
                result = self.run_audit()
                self.assert_controlled_error(result)
                self.assertNotIn("DO_NOT_PRINT_SYNTHETIC_SECRET", result.stderr + result.stdout)
                link.unlink()

    def test_frontmatter_with_h1_is_not_headingless(self):
        self.write("note.md", "---\ntitle: Example\n---\n\n# Heading\n")
        self.assertEqual(self.report()["notes_without_heading"], [])

    def test_h2_without_h1_is_headingless(self):
        self.write("note.md", "## Subtitle\n")
        self.assertEqual(self.report()["notes_without_heading"], ["note.md"])

    def test_h1_after_intro_is_detected(self):
        self.write("note.md", "Introduction\n\n# Heading\n")
        self.assertEqual(self.report()["notes_without_heading"], [])

    def test_code_block_heading_is_not_a_note_heading(self):
        self.write("note.md", "```sh\n# A comment\n```\n")
        self.assertEqual(self.report()["notes_without_heading"], ["note.md"])

    def test_sensitive_values_are_never_printed(self):
        self.write("note.md", "password: DO_NOT_PRINT_SYNTHETIC_SECRET\n")
        result = self.run_audit()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("DO_NOT_PRINT_SYNTHETIC_SECRET", result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["sensitive_candidate_total"], 1)

    def test_configured_vault_is_used_without_explicit_flag(self):
        environment = dict(os.environ, OBSIDIAN_VAULT=str(self.root))
        result = self.run_audit(vault=False, environment=environment)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["vault"], str(self.root))

    def test_limits_preserve_totals(self):
        for index in range(3):
            self.write(f"note-{index}.md", "password: synthetic\n")
        report = self.report("--headingless-limit", "1", "--sensitive-limit", "0")
        self.assertEqual(len(report["notes_without_heading"]), 1)
        self.assertEqual(report["notes_without_heading_total"], 3)
        self.assertEqual(report["sensitive_candidates"], [])
        self.assertEqual(report["sensitive_candidate_total"], 3)


if __name__ == "__main__":
    unittest.main()
