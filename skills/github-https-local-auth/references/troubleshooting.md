# troubleshooting guide

Use this reference only after a GitHub-related command fails and only when the user wants a diagnosis.

## allowed checks

Run only these read-only commands:

```bash
git remote -v
git config --list --show-origin --show-scope
```

## classify the failure

### case 1: remote uses https

If `git remote -v` shows `https://github.com/...`, keep HTTPS in place.

Do not suggest switching to SSH unless the user explicitly asks.

### case 2: credential helper present

If Git config shows `credential.helper=osxkeychain`, state that local macOS Git credentials appear to be configured.

Do not infer that the stored credential is valid. Only state that the helper is configured.

### case 3: git auth failure

Typical indicators:

- authentication failed
- could not read username for 'https://github.com'
- invalid username or token

State that the problem appears to be Git-over-HTTPS authentication.

### case 4: repository authorization failure

Typical indicators:

- permission denied to repository
- repository not found
- 403 on push while authentication otherwise appears configured

State that the problem may be repository or organization authorization rather than missing local Git config.

### case 5: gh-only failure

If `gh` fails but plain `git` is not required for the task, state that `gh` authentication is separate from Git transport authentication.

Do not treat a `gh` login issue as proof that the local Git HTTPS path is broken.

## response shape

Keep the diagnosis short:

1. current remote protocol
2. whether `credential.helper=osxkeychain` is present
3. likely failure class
4. next manual step, without executing it
