# Elgoog Contract

Elgoog is a Gemini-specific runtime surface.

## Input contract

- raw text or file path
- task class
- preferred slot id
- optional explicit model

## Output contract

Every run writes:
- JSON artifact
- markdown output on success
- provider log entry

Status values:
- `success`
- `quota`
- `transient`
- `auth`
- `error`
- `busy`
- `dry_run`

## External orchestrator integration

Another orchestrator should call Elgoog as an external worker when:
- task is wide
- task is repetitive
- task benefits from cheap Gemini extraction
- slot rotation matters
- the output should be an artifact, not an in-band chat answer

The external orchestrator should retain:
- routing
- context/memory discipline
- workflow state
- final judgment

Elgoog should own:
- Gemini auth flow
- slot failover
- Gemini-specific task prompts
- Gemini run artifacts
- Gemini quota/error handling
