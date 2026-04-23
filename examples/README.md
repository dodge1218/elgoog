# Elgoog Examples

These examples are proof artifacts from real Elgoog runs.

They are meant to show:

- CLI-first command shape
- repo-native input handling
- context-budget behavior
- readable artifact output
- interactive CLI session flow

## Included examples

### Understand a local repo, small context budget

Source command:

```bash
elgoog understand --repo . --slot myb --context-budget small --json
```

Artifact:

- `example-understand-local-repo-small.md`

Why it matters:

- shows repo-native understanding without max-token spam
- demonstrates the small budget path

### Recover work from a local repo, medium context budget

Source command:

```bash
elgoog recover --repo . --slot myb --context-budget medium --json
```

Artifact:

- `example-recover-local-repo-medium.md`

Why it matters:

- shows bounded execution-oriented output
- demonstrates a wider context budget when the task needs it

### Interactive repo session

Source commands:

```bash
elgoog session --repo . --slot myb
elgoog resume
elgoog export --json
```

Artifact:

- `example-session-repo-flow.md`

Why it matters:

- shows the real terminal-first path
- shows explicit compaction and resume behavior
- shows exportable session artifacts instead of hidden memory

## Notes

These are real outputs, not hand-written examples.

Provider-side transient errors are also part of the proof story. Elgoog records them explicitly in run artifacts instead of collapsing them into vague failure noise.

Local screenshots are intentionally not tracked in the repo yet. The product surface is still changing, and stale screenshots create confusion faster than they help.
