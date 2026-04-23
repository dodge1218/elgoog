# Release Status

Date: 2026-04-22

Current status: public alpha, internally release-checked

## Verified now

### CLI quality

- `elgoog` prints the short command map cleanly
- `elgoog help` is accurate
- `elgoog session --repo . --slot myb` works on a real repo
- `elgoog resume` restores the saved session
- `elgoog export` writes JSON and markdown bundles

### Auth and status

- `elgoog auth login` points to the correct key URL
- `elgoog auth add` wording is clear about slot name vs API key
- `elgoog doctor --json` reports usable slot state
- in-session `/doctor` reports slot health with a next action

### Repo and file behavior

- `understand --repo . --context-budget small` works
- `recover --repo . --context-budget medium` works
- `understand --github ...` classifies transient failures honestly
- source manifests record what was included and why

### Artifacts

- run records are written
- manifests are written
- successful runs produce markdown outputs
- session export bundles are readable

### Install

- editable install in a fresh virtualenv works
- installed `elgoog` entrypoint runs successfully from that clean environment

## Still below a wider public release bar

- no polished desktop shell
- no IDE integration
- no stronger long-running progress UI
- output quality is good enough, not best-in-class
- screenshots are still local-only and intentionally not tracked

## Honest label

Elgoog is not finished.

It is a credible, tested, CLI-first public alpha with a clean product boundary and a working terminal workflow.
