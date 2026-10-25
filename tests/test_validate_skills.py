"""Exercise the contributor command with isolated skill directories."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


COMMAND = Path(__file__).resolve().parents[1] / "scripts/validate_skills.py"
FRONTMATTER = "---\nname: example\ndescription: A useful example skill.\n---\n\n# Example\n"
MANIFEST = '''interface:
  display_name: "Example"
  short_description: A useful example.
  icon_small: assets/icon.svg
  icon_large: "./assets/icon.svg"
policy:
  products:
  - codex
  - "chatgpt"
  allow_implicit_invocation: true
'''


class ValidateSkillsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.skill = self.root / "skills/example"
        (self.skill / "agents").mkdir(parents=True)
        (self.skill / "assets").mkdir()
        (self.skill / "assets/icon.svg").write_text("<svg/>", encoding="utf-8")
        self.write("SKILL.md", FRONTMATTER)
        self.write("agents/openai.yaml", MANIFEST)

    def write(self, name, value):
        path = self.skill / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")

    def run_command(self, root=None, format="json"):
        return subprocess.run(
            [sys.executable, "-B", str(COMMAND), "--root", str(root or self.root), "--format", format],
            text=True, capture_output=True,
        )

    def assert_invalid(self, expected):
        result = self.run_command()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertFalse(report["ok"])
        self.assertIn(expected, "\n".join(report["errors"]))
        self.assertEqual(result.stderr, "")

    def test_catalog_contains_metadata_and_resources_in_stable_order(self):
        self.write("references/guide.md", "# Guide\n")
        self.write("scripts/helper.py", "print('hello')\n")
        self.write("SKILL.md", FRONTMATTER + "\n[Guide](references/guide.md#guide) and `scripts/helper.py`.\n")
        result = self.run_command()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["schema_version"], 1)
        self.assertTrue(report["ok"])
        self.assertEqual(report["errors"], [])
        self.assertEqual([s["name"] for s in report["skills"]], ["example"])
        self.assertEqual(report["skills"][0]["description"], "A useful example skill.")
        self.assertEqual(report["skills"][0]["display_name"], "Example")
        self.assertEqual(report["skills"][0]["resources"], ["assets/icon.svg", "references/guide.md", "scripts/helper.py"])
        self.assertEqual(self.run_command().stdout, result.stdout)

    def test_text_catalog_names_skills(self):
        result = self.run_command(format="text")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("example", result.stdout)
        self.assertIn("1 skill", result.stdout)

    def test_name_must_match_directory(self):
        self.write("SKILL.md", FRONTMATTER.replace("name: example", "name: other"))
        self.assert_invalid("name must match directory")

    def test_required_frontmatter_and_manifest_fields(self):
        for path, original, removed in (
            ("SKILL.md", FRONTMATTER, "description: A useful example skill.\n"),
            ("agents/openai.yaml", MANIFEST, '  display_name: "Example"\n'),
            ("agents/openai.yaml", MANIFEST, "  allow_implicit_invocation: true\n"),
        ):
            with self.subTest(path=path, removed=removed):
                self.write(path, original.replace(removed, ""))
                self.assert_invalid("required")
                self.write(path, original)

    def test_duplicate_metadata_is_rejected(self):
        self.write("SKILL.md", FRONTMATTER.replace("description:", "name: duplicate\ndescription:"))
        self.assert_invalid("duplicate")

    def test_unsupported_yaml_fails_clearly(self):
        for value in ("|\n  multiline", "&alias value", "[one, two]", "value # comment", "value: nested", '"unterminated', "# comment", ".inf", ".nan"):
            with self.subTest(value=value):
                self.write("SKILL.md", FRONTMATTER.replace("A useful example skill.", value))
                self.assert_invalid("supported metadata format")

    def test_manifest_rejects_invalid_bool_unknown_fields_and_duplicate_products(self):
        for manifest in (
            MANIFEST.replace("true", "yes"),
            MANIFEST + "unexpected: value\n",
            MANIFEST.replace('  - "chatgpt"', "  - codex"),
            MANIFEST.replace("  short_description:", "  display_name: Again\n  short_description:"),
        ):
            with self.subTest(manifest=manifest):
                self.write("agents/openai.yaml", manifest)
                self.assert_invalid("agents/openai.yaml")

    def test_trailing_plain_colon_requires_quoting(self):
        self.write("SKILL.md", FRONTMATTER.replace("A useful example skill.", "example:"))
        self.assert_invalid("supported metadata format")
        self.write("SKILL.md", FRONTMATTER.replace("A useful example skill.", '"example:"'))
        result = self.run_command()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["skills"][0]["description"], "example:")

    def test_product_list_items_require_consistent_indentation(self):
        for first, second in ((2, 4), (4, 2)):
            with self.subTest(first=first, second=second):
                modified = MANIFEST.replace("  - codex", " " * first + "- codex")
                modified = modified.replace('  - "chatgpt"', " " * second + '- "chatgpt"')
                self.write("agents/openai.yaml", modified)
                self.assert_invalid("consistent indentation")
        for spaces in (2, 4):
            with self.subTest(valid_spaces=spaces):
                self.write("agents/openai.yaml", MANIFEST.replace("  - ", " " * spaces + "- "))
                result = self.run_command()
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_unpaired_unicode_surrogates_have_structured_json_and_text_errors(self):
        for field in ("description", "display_name", "icon_small"):
            for surrogate in (chr(0xD800), chr(0xDFFF)):
                for output_format in ("json", "text"):
                    with self.subTest(field=field, surrogate=repr(surrogate), format=output_format):
                        self.write("SKILL.md", FRONTMATTER)
                        self.write("agents/openai.yaml", MANIFEST)
                        quoted = json.dumps(surrogate)
                        if field == "description":
                            self.write("SKILL.md", FRONTMATTER.replace("A useful example skill.", quoted))
                        else:
                            original = '\"Example\"' if field == "display_name" else "assets/icon.svg"
                            self.write("agents/openai.yaml", MANIFEST.replace(original, quoted, 1))
                        result = self.run_command(format=output_format)
                        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                        self.assertEqual(result.stderr, "", result.stderr)
                        self.assertTrue(result.stdout.strip(), "missing structured response")
                        if output_format == "json":
                            report = json.loads(result.stdout)
                            self.assertFalse(report["ok"])
                            self.assertIn("valid Unicode", " ".join(report["errors"]))
                        else:
                            self.assertIn("ERROR:", result.stdout)
                            self.assertIn("valid Unicode", result.stdout)

    def test_valid_escaped_unicode_pairs_remain_supported(self):
        self.write("SKILL.md", FRONTMATTER.replace("A useful example skill.", json.dumps("Useful 🚀 skill.")))
        result = self.run_command()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["skills"][0]["description"], "Useful 🚀 skill.")

    def test_quoted_scalars_preserve_string_content(self):
        self.write("SKILL.md", FRONTMATTER.replace("A useful example skill.", "'It''s useful: # truly.'"))
        self.write("agents/openai.yaml", MANIFEST.replace('"Example"', json.dumps('Example "quoted"')))
        result = self.run_command()
        self.assertEqual(result.returncode, 0, result.stdout)
        catalog = json.loads(result.stdout)["skills"][0]
        self.assertEqual(catalog["description"], "It's useful: # truly.")
        self.assertEqual(catalog["display_name"], 'Example "quoted"')

    def test_missing_manifest_and_asset_are_reported(self):
        (self.skill / "agents/openai.yaml").unlink()
        self.assert_invalid("agents/openai.yaml")
        self.write("agents/openai.yaml", MANIFEST)
        (self.skill / "assets/icon.svg").unlink()
        self.assert_invalid("assets/icon.svg")

    def test_missing_local_markdown_and_code_references_are_reported(self):
        self.write("SKILL.md", FRONTMATTER + "\n[Missing](references/missing.md) and `scripts/missing.py`.\n")
        self.assert_invalid("references/missing.md")
        self.assert_invalid("scripts/missing.py")

    def test_reference_documents_are_checked_with_relative_links(self):
        self.write("references/guide.md", "[Icon](../assets/icon.svg)\n[Missing](missing.md)\n")
        self.assert_invalid("missing.md")
        self.write("references/guide.md", "[Icon](../assets/icon.svg)\n")
        result = self.run_command()
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_links_outside_skill_and_symlink_assets_are_rejected(self):
        outside = self.root / "outside.svg"
        outside.write_text("outside", encoding="utf-8")
        self.write("SKILL.md", FRONTMATTER + "\n[Outside](../../outside.svg)\n")
        self.assert_invalid("outside skill")
        self.write("SKILL.md", FRONTMATTER)
        (self.skill / "assets/icon.svg").unlink()
        (self.skill / "assets/icon.svg").symlink_to(outside)
        self.assert_invalid("outside skill")

    def test_fenced_examples_and_external_urls_are_ignored(self):
        self.write("SKILL.md", FRONTMATTER + '''
```markdown
[Example](missing.md) and `scripts/missing.py`
```
~~~markdown
[Example](another.md)
~~~
[Web](https://example.invalid/path) [Mail](mailto:test@example.invalid) [Here](#example)
''')
        result = self.run_command()
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_missing_and_empty_roots_have_structured_errors(self):
        for root in (self.root / "missing", self.root / "empty"):
            with self.subTest(root=root):
                if root.name == "empty":
                    (root / "skills").mkdir(parents=True)
                result = self.run_command(root=root)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertFalse(json.loads(result.stdout)["ok"])
                self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
