## What this repo appears to do
Elgoog is a Python-based, CLI-first developer workbench designed to improve the Gemini model developer experience. It wraps Gemini's runtime to provide explicit tooling for tasks like repo understanding, recovering unfinished work, and generating TODOs, focusing on reliability for auth, quota, and status signaling. It includes an optional local web app for setup and inspection.

## Likely moving parts
- **CLI application**: The core `elgoog.py` provides the main command-line interface.
- **Server application**: `elgoog_server.py` implements the optional local web app, likely residing in `ui/` (e.g., `ui/index.html`, `ui/app.js`).
- **Gemini integration**: The `google-genai` Python library is a key dependency, indicating direct interaction with Gemini APIs.
- **Repository context**: Mechanisms for ingesting and managing local repository/file context, suggested by "repo understanding," "repo-native CLI inputs" (recent commit), and "context budget policy" (recent commit).
- **Authentication/Authorization**: Dedicated modules for `elgoog auth login` and `elgoog auth add`.
- **Testing**: `tests/test_elgoog.py` indicates a test suite for the main application logic.

## Likely entrypoints
- **CLI commands**:
    - `elgoog`: Main CLI interface.
    - `elgoog help`: Provides usage information.
    - `elgoog onboard`: Initial setup.
    - `elgoog auth login`, `elgoog auth add`: Authentication management.
    - `elgoog recover`, `elgoog understand`, `elgoog todos`, `elgoog plan`, `elgoog r`: Core developer task commands.
- **Server command**: `elgoog-server`: Starts the local web application.
- **Makefile targets**: `make test`, `make doctor`, `make server` provide convenience for common operations.
- **Python modules**: `elgoog.py` and `elgoog_server.py` are the primary source code entrypoints for their respective applications.

## Current risk or confusion areas
- **Auth and slot reliability**: Explicitly called out as an MVP priority and a recurring user complaint, suggesting ongoing work or potential fragility in this area.
- **Honest failure classification**: Another MVP priority, indicating that clear error handling and status signaling are critical and actively developed.
- **Repo/file context management**: The recent commit "Add context budget policy" points to challenges in reliably providing and managing context for Gemini models, a core problem Elgoog aims to solve.
- **API quota and capacity**: Mentioned as a recurring complaint and a design constraint, implying that managing and communicating these aspects is a key challenge.

## What to inspect next
1.  **`elgoog.py`**: Understand the main CLI command dispatch and core logic for user-facing jobs like `recover`, `understand`, `todos`, and `plan`.
2.  **`elgoog_server.py` and `ui/` directory**: Examine how the local web app is implemented and interacts with the core `elgoog` functionality, especially for setup and inspection.
3.  **Authentication code (implied by `elgoog auth`)**: Investigate how Gemini authentication and permissions are handled to address the "auth and permissions confusion" complaint.
4.  **`Makefile`**: Review available development and operational targets.
5.  **`CONTRACT.md`**: This file name suggests important project agreements or design principles that could inform further development.
