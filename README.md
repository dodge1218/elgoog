# Elgoog

Elgoog is a Gemini-native developer workbench.

It exists to solve a narrow problem: Gemini models are strong, but the surrounding developer harness is still weaker than it should be. Elgoog adds the missing operator layer for local developer work.

## Purpose

Elgoog is for developers who need Gemini to behave like reliable tooling instead of a fragile chat surface.

The product focus is:

- terminal-first developer workflow
- repo understanding
- unfinished-work recovery
- bounded TODO generation
- artifact-first execution
- explicit auth, quota, and failure semantics

The product is not trying to be a general AI cockpit.

## What it is

- a CLI-first Gemini runtime wrapper
- an optional local web app for setup and inspection
- file-backed and provenance-first
- optimized for understanding and advancing work

## What it is not

- not a multi-provider control plane
- not a mission-control dashboard
- not a background agent fleet manager
- not a prompt toy
- not a terms-of-service bypass layer

## Why it exists

Recent public developer demand around Gemini clusters around four recurring complaints:

1. auth and permissions confusion
2. quota and capacity ambiguity
3. hanging and weak status signaling
4. repo/file context that feels unreliable

Elgoog is built around those complaints, not around novelty features.

## Core jobs

The user-facing jobs are:

- `Recover Work`
- `Understand Repo`
- `Create TODOs`
- `Plan Next Steps`

These are the public surfaces. Internal task classes stay technical.

## Design constraints

The project is intentionally narrow.

MVP priorities:

1. auth and slot reliability
2. honest failure classification
3. file/repo/GitHub intake
4. recovery-oriented prompts
5. readable, copyable artifacts

Explicit non-goals for v1:

- mission control
- multi-agent choreography
- vague canvas UX
- speculative autonomy layers

## Install

Elgoog is currently a Python project. It is not an npm package.

### Local editable install

```bash
git clone https://github.com/dodge1218/elgoog.git
cd elgoog
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### `pipx` install from GitHub

```bash
pipx install git+https://github.com/dodge1218/elgoog.git
```

Installed commands:

```bash
elgoog
elgoog-server
```

Or use the local convenience targets:

```bash
make test
make doctor
make server
```

Primary CLI entrypoints:

```bash
elgoog
elgoog help
elgoog onboard
elgoog auth login
elgoog auth add
elgoog session
elgoog resume
elgoog recover
elgoog understand
elgoog todos
elgoog plan
elgoog run --help
```

## API key setup

Create a Gemini API key here:

- https://aistudio.google.com/apikey

Slot inputs currently support:

- `--api-key`
- `--slots-path`
- `--slots-json`
- `ELGOOG_API_KEYS`
- `GEMINI_API_KEY`

## CLI first run

Fastest first-run path:

```bash
elgoog
```

That prints the short first-use command map. It does not launch the browser.

If you only want the key flow:

```bash
elgoog auth login
```

That prints the Gemini key URL and the next local steps. Browser launch is manual by default.

To save a key locally:

```bash
elgoog auth add
```

Important:

- the first prompt is only a local slot label, for example `gemini_slot_1`
- the second prompt is the actual Gemini API key

## First-run path

If you want the shortest path to a working local setup:

1. create a Gemini API key:
   - https://aistudio.google.com/apikey
2. save one local slot:
   - `elgoog auth add`
3. verify readiness:
   - `elgoog doctor --json`
4. start an interactive repo session:
   - `elgoog session --repo . --slot gemini_slot_1`
5. resume later:
   - `elgoog resume`
5. optionally use the web surface later for setup and inspection:
   - `elgoog web`

## CLI examples

Show the short command map again:

```bash
elgoog help
```

Task-native commands:

```bash
elgoog session --repo . --slot gemini_slot_1

elgoog resume

elgoog recover --text "I have notes and a messy repo state. Recover the next bounded steps." --slot gemini_slot_1 --json

elgoog understand --repo . --slot gemini_slot_1 --json

elgoog todos --file /abs/path/notes.md --slot gemini_slot_1 --json

elgoog plan --text "Turn this release context into a bounded plan." --slot gemini_slot_1 --json
```

Repo and GitHub inputs:

```bash
elgoog understand --repo . --slot gemini_slot_1 --context-budget small --json

elgoog recover --repo . --slot gemini_slot_1 --context-budget medium --json

elgoog understand --github https://github.com/google-gemini/gemini-cli --slot gemini_slot_1 --context-budget large --json
```

Context budget:

- `small`: tight first pass, less repo/context included
- `medium`: default
- `large`: wider context when the task genuinely needs it

## Interactive session mode

`elgoog session` is the CLI path for ongoing work.

It is:

- file-backed
- source-aware
- explicit about compaction
- local and inspectable

Example:

```bash
elgoog session --repo . --slot gemini_slot_1
```

In-session commands:

```text
/help
/status
/doctor
/sources
/last
/compact
/clear
/exit
```

What `/compact` does:

- summarizes older turns into a visible session summary
- keeps the most recent turns intact
- writes updated state to `state/sessions/`

This is intentional. Elgoog does not hide memory behavior behind vague “AI workspace” language.

What `elgoog resume` does:

- restores the last saved session by default
- or restores a named session with `--name`
- reuses saved repo/file/GitHub source details unless you override them

What `/doctor` does in-session:

- probes the current slot directly
- reports `ready`, `auth`, `quota`, `transient`, or `error`
- gives the next action inline instead of forcing you back out to guess

Dry run:

```bash
elgoog run \
  --text "Recover the next three bounded tasks from this repo summary" \
  --task-class planning \
  --slot gemini_slot_1 \
  --dry-run \
  --json
```

Real run:

```bash
elgoog run \
  --file /abs/path/input.txt \
  --task-class planning \
  --slot gemini_slot_1 \
  --slots-path /abs/path/slots.json \
  --json
```

## Optional web surface

If you want the optional local UI for setup, artifact inspection, and repo/file input:

```bash
elgoog web
```

If you want browser launch automatically:

```bash
elgoog web --open-browser
```

The lower-level server entrypoint also exists:

```bash
elgoog-server
```

Then open:

```text
http://127.0.0.1:8765
```

Open the key page:

```bash
elgoog key-url
```

Check local readiness:

```bash
elgoog doctor --json
```

## Proof examples

Real example outputs live in:

- [examples/README.md](examples/README.md)
- [examples/example-understand-local-repo-small.md](examples/example-understand-local-repo-small.md)
- [examples/example-recover-local-repo-medium.md](examples/example-recover-local-repo-medium.md)

## Runtime model

Today, Elgoog works like this:

1. the app collects durable inputs
   - file
   - repo
   - public GitHub repo
   - optional prompt overlay
2. the runtime resolves those inputs into a single file-backed source manifest
3. the runtime selects a Gemini slot
4. the runtime executes or dry-runs the task
5. the runtime writes artifacts and returns classified status

Prompts are input overlays. They are not the system of record.

## Output contract

Each run writes:

- a JSON run record
- a JSON source manifest
- a markdown output on success
- a provider log entry

The important invariant is that each run is inspectable after the fact.

## Repository structure

Current top-level layout:

```text
elgoog.py            CLI runtime
elgoog_server.py     local web server
ui/                  web app
pyproject.toml       packaging
README.md            operator-facing docs
CONTRACT.md          local contract notes
```

Runtime-generated directories such as `state/`, `locks/`, `logs/`, and `outputs/` are operational data, not source.

## Current status

Elgoog is early, but it is not imaginary.

Working now:

- slot-aware runtime
- explicit failure semantics
- repo/file/public-GitHub intake
- recovery/repo/TODO task framing
- run history
- copy/export
- file-backed manifests
- basic local test coverage

Still missing before a serious public release:

- polished install story
- real desktop shell
- stronger progress and latency handling
- broader GitHub integration
- production hardening

## Integration posture

Elgoog is designed to stand on its own.

If another orchestrator wants to call it later, the boundary should stay simple:

- durable inputs in
- classified Gemini run out
- file-backed artifacts on disk
