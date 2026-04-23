# Example: Interactive Repo Session

This example shows the intended terminal flow for ongoing work in Elgoog.

## Start

```bash
elgoog session --repo . --slot myb
```

## In-session flow

Check saved state and current source:

```text
/status
/sources
```

Probe the current slot without leaving the session:

```text
/doctor
```

Ask a repo-grounded question:

```text
what are the most likely entrypoints in this repo?
```

Compact older turns when the session gets noisy:

```text
/compact
```

Export a shareable bundle:

```text
/export
```

Exit cleanly:

```text
/exit
```

## Resume later

```bash
elgoog resume
```

## Export later

```bash
elgoog export --json
```

## Why it matters

- keeps work in one terminal session
- preserves explicit source context
- makes compaction visible instead of hidden
- gives developers a durable transcript and JSON bundle
