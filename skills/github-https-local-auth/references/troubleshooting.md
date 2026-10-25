# troubleshooting guide

Use this reference only after a GitHub-related command fails and only when the user wants a diagnosis.

## allowed checks

Run these read-only checks without shell tracing. Replace `origin` if the relevant remote has another name. Raw URLs and helper values remain internal to the checks; only fixed classifications are printed:

```bash
remote_url=$(git remote get-url origin 2>/dev/null) || remote_url=
case "$remote_url" in
  https://*) printf 'origin protocol=https\n' ;;
  ssh://*|git@*) printf 'origin protocol=ssh\n' ;;
  '') printf 'origin protocol=unavailable\n' ;;
  *) printf 'origin protocol=other\n' ;;
esac
unset remote_url
if git config --get-urlmatch credential.helper https://github.com 2>/dev/null | grep -Fx osxkeychain >/dev/null; then
  printf 'osxkeychain configured=yes\n'
else
  printf 'osxkeychain configured=no or unavailable\n'
fi
```

Do not print complete Git configuration, remote URLs, authorization headers, or credential-helper command values. Redact credential values in any error reported to the user.

## classify the failure

### case 1: remote uses https

If the protocol check prints `origin protocol=https`, keep HTTPS in place.

Do not suggest switching to SSH unless the user explicitly asks.

### case 2: credential helper present

If the helper check prints `osxkeychain configured=yes`, state that Git selects the macOS keychain helper for GitHub.

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
