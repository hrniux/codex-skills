"""Run the documented diagnostic recipes against synthetic credential settings."""

from pathlib import Path
import os
import re
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1] / "skills/github-https-local-auth"


class AuthDiagnosticTests(unittest.TestCase):
    def test_diagnostics_report_protocol_and_helper_without_credentials(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            environment = dict(os.environ, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
            subprocess.run(["git", "init", "-q", str(repo)], check=True, env=environment)
            for key, value in (
                ("remote.origin.url", "https://user:SYNTHETIC_REMOTE_SECRET@github.com/example/repo.git"),
                ("http.https://github.com/.extraheader", "Authorization: Basic SYNTHETIC_HEADER_SECRET"),
                ("credential.helper", "osxkeychain"),
            ):
                subprocess.run(["git", "-C", str(repo), "config", key, value], check=True, env=environment)
            for filename, section in (
                ("SKILL.md", "If the user wants diagnosis"),
                ("references/troubleshooting.md", "## allowed checks"),
            ):
                with self.subTest(filename=filename):
                    text = (ROOT / filename).read_text(encoding="utf-8").split(section, 1)[1]
                    recipe = re.search(r"```bash\n(.*?)\n```", text, re.DOTALL).group(1)
                    result = subprocess.run(
                        ["bash", "-c", recipe], cwd=repo, text=True, capture_output=True,
                        env=environment,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    output = result.stdout + result.stderr
                    self.assertNotIn("SYNTHETIC_REMOTE_SECRET", output)
                    self.assertNotIn("SYNTHETIC_HEADER_SECRET", output)
                    self.assertIn("origin protocol=https", output)
                    self.assertIn("osxkeychain configured=yes", output)


if __name__ == "__main__":
    unittest.main()
