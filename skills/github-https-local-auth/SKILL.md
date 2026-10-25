---
name: github-https-local-auth
description: preserve stable github access in codex cli on macos by preferring git over https with existing local credentials. use when working in github repositories where git authentication is already configured locally, typically with credential.helper=osxkeychain, and the user wants to avoid switching to ssh, rewriting remotes, or starting gh login flows unless explicitly requested.
---

# github https local auth

## overview

Assume a macos workstation where GitHub repository access is already configured locally for Git over HTTPS, usually through `credential.helper=osxkeychain`.

Reuse the existing authentication path. Do not change protocols, rewrite remotes, generate SSH keys, or start `gh` authentication unless the user explicitly asks.

Consult [references/troubleshooting.md](references/troubleshooting.md) only when a command fails and the user wants a diagnosis.

## default operating rules

- Prefer plain `git` for repository transport operations such as `clone`, `fetch`, `pull`, `push`, `status`, `remote`, and branch workflows.
- Treat an existing HTTPS remote and the local credential helper as the source of truth.
- Assume credentials are managed outside the conversation by the local macOS keychain-backed Git setup.
- Do not embed tokens in clone URLs, scripts, shell history, or config files.
- Do not switch the remote from HTTPS to SSH unless the user explicitly requests that exact change.
- Do not run `ssh-keygen`, `ssh -T git@github.com`, `git remote set-url`, `gh auth login`, or `gh auth setup-git` unless the user explicitly requests one of those actions.
- Do not treat an unauthenticated `gh` session as a Git failure. If plain `git` is sufficient for the task, continue without `gh`.
- Default to not using `gh` at all.

## task routing

### repository transport and local repo work

Use `git` directly for:

- cloning repositories over HTTPS
- fetching, pulling, and pushing
- inspecting remotes and branches
- reading local Git config
- preparing commits and normal branch workflows

When cloning, prefer URLs of the form:

```bash
https://github.com/OWNER/REPO.git
```

### github platform actions

Do not use `gh` unless the user explicitly requests GitHub platform operations such as:

- pull request creation or review
- issue creation or triage
- release management
- repository metadata queries that are specifically GitHub-platform scoped

Even in those cases, do not run `gh auth login` unless the user explicitly asks to log in with `gh`.

## failure handling

When a GitHub-related command fails:

1. Stop after the failing command.
2. Report the command and error with credential values redacted.
3. Do not attempt fallback authentication.
4. Do not switch to SSH.
5. Do not rewrite remotes.
6. Do not start any login flow.

If the user wants diagnosis, limit inspection to read-only checks. Run without shell tracing; keep raw URLs and credential configuration out of output. For the relevant remote (replace `origin` if needed), print only these fixed classifications:

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

The configuration check reports only whether Git selects `osxkeychain` for GitHub. It does not validate the stored credential. Do not dump complete Git config, remote URLs, authorization headers, or helper command values.

After those checks, report only:

- whether the remote is HTTPS or SSH
- whether the GitHub credential-helper check finds `osxkeychain`
- whether the failure looks like Git HTTPS authentication, GitHub repository authorization, or a separate `gh` authentication issue

Then recommend the next manual step without executing it unless the user explicitly asks.

## preferred wording

When stating the current assumption, use language close to:

- "use the existing local https git credentials on macos"
- "do not switch this repo to ssh"
- "do not run gh auth login unless explicitly requested"
- "treat git transport auth and gh auth as separate states"

## examples

### example: normal repository work

User request:

> Pull the latest changes from GitHub and show me the current branch.

Expected behavior:

- use `git pull`
- use `git branch --show-current` or equivalent local Git inspection
- do not call `gh`
- do not inspect or modify auth unless a command actually fails

### example: user asks for a GitHub platform task

User request:

> Create a pull request with gh.

Expected behavior:

- use `gh` because the user explicitly requested it
- if `gh` is unauthenticated, report that state
- do not run `gh auth login` unless the user explicitly asks for that login flow

### example: authentication failure during push

User request:

> Push my branch.

Observed failure:

> `git push` returns an authentication or permission error.

Expected behavior:

- report the failed `git push` command and error text
- do not try PAT-in-URL, SSH, or `gh auth`
- only if the user wants diagnosis, run the read-only inspection commands above
- recommend the next manual action instead of changing configuration automatically
