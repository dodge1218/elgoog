# Release Checklist

Use this checklist before treating Elgoog as more than a public alpha.

## CLI quality

- `elgoog` prints the short command map cleanly
- `elgoog help` is accurate
- `elgoog session --repo . --slot ...` works on a real repo
- `elgoog resume` restores the expected session
- `elgoog export` writes JSON and markdown bundles

## Auth and status

- `elgoog auth login` points to the correct key URL
- `elgoog auth add` wording is clear about slot name vs API key
- `elgoog doctor --json` reports usable slot state
- in-session `/doctor` gives a concrete next action

## Repo and file behavior

- `understand --repo .` works with `small`
- `recover --repo .` works with `medium`
- `understand --github ...` classifies transient failures honestly
- source manifests show what was included and why

## Artifacts

- run records are written
- manifests are written
- successful runs produce markdown outputs
- session export bundles are readable

## Public repo

- README matches the current CLI behavior
- examples are current
- `git status` is clean
- no local screenshots or junk files are staged
- no private paths, names, or sidequest residue leaked

## Outbound bar

Do not pitch Elgoog as finished until:

- one clean real session flow has been tested end to end
- one clean repo-understand example exists
- one clean recover-work example exists
- the README and examples still match the current code
