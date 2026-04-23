# Elgoog Roadmap

This roadmap is derived from recent public Gemini developer demand:

- `100` recent `google-gemini/gemini-cli` issue threads
- `1079` aggregate comments

Those comments clustered around:

1. auth and permissions confusion
2. quota and capacity ambiguity
3. latency and hanging
4. repo/file context that feels unreliable
5. outputs developers can actually keep and reuse

Elgoog v1 is scoped to that demand. Anything else is v2.

## V1

Ship only what directly answers the current harness gap:

- CLI-first workflow
- auth/key save flow
- doctor/readiness checks
- explicit failure classification:
  - `auth`
  - `quota`
  - `transient`
  - `busy`
  - `error`
- repo/file/GitHub intake
- task-native commands:
  - `recover`
  - `understand`
  - `todos`
  - `plan`
- context budget policy
- file-backed artifacts and manifests
- interactive CLI session mode
- transparent compaction and resumable session state

## V2

Build later only if v1 proves useful:

- richer output ranking and replay
- stronger export bundles
- better optional web inspector
- GitHub Actions
- desktop shell
- IDE integrations
- local runtime service / daemon
- gateway / app-server layer
- multi-agent or orchestration surfaces

## Non-goals

These are not part of the current product boundary:

- mission control
- speculative autonomy
- provider-agnostic orchestration plane
- “AI cockpit” UI theater
- terms-of-service bypass positioning
