# Elgoog

Elgoog is a Gemini-native developer workbench.

It exists to solve a narrow problem: Gemini models are strong, but the surrounding developer harness is still weaker than it should be. Elgoog adds the missing operator layer for local developer work.

## Purpose

Elgoog is for developers who need Gemini to behave like reliable tooling instead of a fragile chat surface.

The product focus is:

- repo understanding
- unfinished-work recovery
- bounded TODO generation
- artifact-first execution
- explicit auth, quota, and failure semantics

The product is not trying to be a general AI cockpit.

## What it is

- a local Gemini runtime wrapper
- a local web app on top of that runtime
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
git clone <repo-url>
cd elgoog
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### `pipx` install from GitHub

```bash
pipx install git+https://github.com/<owner>/elgoog.git
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
elgoog onboard
elgoog auth login
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

## Running the app

Fastest first-run path:

```bash
elgoog
```

That starts onboarding, checks slot readiness, and launches the local app.

If you only want the key flow:

```bash
elgoog auth login
```

If you want to skip automatic browser launch:

```bash
elgoog onboard --no-browser
```

Start the local app server:

```bash
elgoog-server
```

Then open:

```text
http://127.0.0.1:8765
```

The app provides:

- setup/doctor surface
- slot management
- local file input
- local repo input
- public GitHub repo URL input
- artifact rendering
- run history
- provenance display

## First-run path

If you want the shortest path to a working local setup:

1. create a Gemini API key:
   - https://aistudio.google.com/apikey
2. start the app:
   - `make server`
3. open:
   - `http://127.0.0.1:8765`
4. save one or more slots in the app
5. run `Recover Work` or `Understand Repo` against a local repo or public GitHub repo

## CLI examples

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

Open the key page:

```bash
elgoog key-url
```

Check local readiness:

```bash
elgoog doctor --json
```

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

- dedicated clean GitHub repo/remotes
- CI running on a real remote
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
