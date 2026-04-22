## Current state
Elgoog is a Python CLI-first developer workbench for Gemini models, focused on improving developer tooling around auth, quota, status, and repo context. It provides `elgoog` and `elgoog-server` commands, with core user-facing jobs: `Recover Work`, `Understand Repo`, `Create TODOs`, and `Plan Next Steps`. The project supports repo, file, and public GitHub inputs, an optional local web UI, and outputs structured artifacts (JSON run record, source manifest, markdown, provider log). Recent commits indicate robust development in CLI inputs, task-native commands, onboarding, authentication flows, and context budget policies.

## Likely stale or half-finished work
The `Create TODOs` functionality appears to be the primary area of ongoing refinement.
- Several internal markers in `elgoog.py` and `elgoog_server.py` directly address the quality and structure of generated TODOs:
    - `elgoog.py:126`, `elgoog.py:130`, `elgoog.py:134` emphasize the need for "bounded developer TODOs," "Priority TODOs," and that "each TODO should be specific and shippable."
    - `elgoog_server.py:42`, `elgoog_server.py:46`, `elgoog_server.py:47` similarly define the `create_todos` task prompt to include "prioritized TODOs" that are "specific and shippable."
- The constant `elgoog_server.py:84:MAX_TODO_LINES = 40` suggests a current hard limit on the number of generated TODOs, which might be a temporary measure or an area for future configuration.
- The regex `elgoog_server.py:220: "(TODO|FIXME|HACK|XXX|BUG)"` indicates a potential internal mechanism for identifying these markers, possibly for internal `TODO` generation or analysis.

## Blockers or missing context
The primary "blocker" or area needing further context is the subjective quality of the `Create TODOs` output, as indicated by the explicit internal requirements for "specific," "shippable," and "prioritized" TODOs. While the feature exists, the internal notes suggest that the current implementation might not fully meet these quality criteria yet. There's no explicit external blocker mentioned, but the success of the `Create TODOs` feature hinges on delivering high-quality, actionable outputs.

## Next 3 bounded tasks
1.  **Refine `create_todos` prompt for specificity**: Update the `create_todos` task definition within `elgoog_server.py:42` to enhance prompt instructions, guiding the Gemini model to consistently generate TODOs that are "specific and shippable" as required by `elgoog.py:134`.
2.  **Implement TODO prioritization logic**: Add logic to the `elgoog todos` command (either via prompt engineering in `elgoog_server.py` or post-processing in `elgoog.py`) to ensure the generated TODOs are clearly "prioritized," aligning with `elgoog.py:130` and `elgoog_server.py:46`.
3.  **Evaluate `MAX_TODO_LINES` constraint**: Review `MAX_TODO_LINES = 40` in `elgoog_server.py:84`. Determine if this limit should be removed, made configurable via a `--max-todos` CLI flag for `elgoog todos`, or if the output handling needs more sophisticated truncation based on semantic boundaries rather than line count.
