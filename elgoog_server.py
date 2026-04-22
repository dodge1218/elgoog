#!/usr/bin/env python3
from __future__ import annotations

import json
import hashlib
import subprocess
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
UI_DIR = ROOT / "ui"
CLI = ROOT / "elgoog.py"
SLOTS_PATH = ROOT / "state" / "slots.json"
RUNS_DIR = ROOT / "state" / "runs"
MANIFESTS_DIR = ROOT / "state" / "manifests"
HOST = "127.0.0.1"
PORT = 8765

TASK_MAP = {
    "understand_repo": "classification",
    "recover_work": "planning",
    "create_todos": "cheap_extract",
    "plan_next_steps": "planning",
    "scan_context": "wide_scan",
}

TASK_INSTRUCTIONS = {
    "recover_work": """You are reconstructing in-flight developer work.

Return:
- current state summary
- likely stale or half-finished work
- blockers or missing context
- next 3 bounded tasks

Be concrete. Do not give generic advice.""",
    "create_todos": """Turn the provided context into a bounded developer TODO list.

Return:
- a short summary
- prioritized TODOs
- each TODO must be specific and shippable
- note missing information separately

Avoid vague backlog language.""",
    "understand_repo": """Understand this repo for a developer who needs a fast briefing.

Return:
- what this repo appears to do
- likely moving parts
- likely entrypoints
- current risk or confusion areas
- what to inspect next

Prefer concrete repo interpretation over speculation.""",
    "plan_next_steps": """Plan the next steps from the provided developer context.

Return:
- short current-state summary
- next 3 actions
- blockers
- handoff notes if relevant

Keep the plan actionable and bounded.""",
    "scan_context": """Scan this context and extract the most decision-relevant signals.

Return:
- high-signal findings
- repeated themes
- concrete next actions

Do not pad.""",
}

MAX_FILE_CHARS = 12000
MAX_README_CHARS = 6000
MAX_FILE_LIST = 120
MAX_MANIFEST_CHARS = 3000
MAX_TODO_LINES = 40
MAX_COMMIT_LINES = 8
MAX_DIFFSTAT_CHARS = 2500
MAX_ENTRYPOINTS = 20
MAX_GITHUB_README_CHARS = 8000
MAX_GITHUB_FILE_LINES = 40

CONTEXT_BUDGETS = {
    "small": {
        "readme_chars": 2500,
        "manifest_chars": 1500,
        "todo_lines": 15,
        "commit_lines": 4,
        "diffstat_chars": 1000,
        "entrypoints": 10,
        "file_list": 40,
        "github_readme_chars": 3000,
        "github_file_lines": 15,
    },
    "medium": {
        "readme_chars": MAX_README_CHARS,
        "manifest_chars": MAX_MANIFEST_CHARS,
        "todo_lines": MAX_TODO_LINES,
        "commit_lines": MAX_COMMIT_LINES,
        "diffstat_chars": MAX_DIFFSTAT_CHARS,
        "entrypoints": MAX_ENTRYPOINTS,
        "file_list": MAX_FILE_LIST,
        "github_readme_chars": MAX_GITHUB_README_CHARS,
        "github_file_lines": MAX_GITHUB_FILE_LINES,
    },
    "large": {
        "readme_chars": 12000,
        "manifest_chars": 6000,
        "todo_lines": 80,
        "commit_lines": 16,
        "diffstat_chars": 5000,
        "entrypoints": 40,
        "file_list": 240,
        "github_readme_chars": 16000,
        "github_file_lines": 80,
    },
}


def json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict) -> None:
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def file_response(handler: BaseHTTPRequestHandler, path: Path, content_type: str) -> None:
    body = path.read_bytes()
    handler.send_response(200)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _read_file_excerpt(path: Path, limit: int = MAX_FILE_CHARS) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return f"[Could not read file: {exc}]"
    return text[:limit].strip()


def _fetch_json(url: str) -> dict | list | None:
    try:
        req = Request(url, headers={"User-Agent": "Elgoog/1.0"})
        with urlopen(req, timeout=20) as response:
            return json.load(response)
    except Exception:
        return None


def _fetch_text(url: str, limit: int) -> str:
    try:
        req = Request(url, headers={"User-Agent": "Elgoog/1.0"})
        with urlopen(req, timeout=20) as response:
            return response.read().decode("utf-8", errors="ignore")[:limit].strip()
    except Exception:
        return ""


def _run_capture(cmd: list[str], cwd: Path) -> str:
    try:
        result = subprocess.run(
            cmd,
            cwd=str(cwd),
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
        return ""
    return result.stdout.strip()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _budget(name: str) -> dict:
    return CONTEXT_BUDGETS.get(name, CONTEXT_BUDGETS["medium"])


def _repo_manifest_excerpt(repo_path: Path, budget_name: str) -> str:
    budget = _budget(budget_name)
    candidates = (
        "package.json",
        "pyproject.toml",
        "requirements.txt",
        "go.mod",
        "Cargo.toml",
        "Gemfile",
    )
    parts: list[str] = []
    for name in candidates:
        path = repo_path / name
        if path.exists():
            parts.append(f"{name}:\n{_read_file_excerpt(path, budget['manifest_chars'])}")
    return "\n\n".join(parts).strip()


def _repo_todo_excerpt(repo_path: Path, budget_name: str) -> str:
    budget = _budget(budget_name)
    output = _run_capture(
        [
            "rg",
            "-n",
            "-m",
            str(budget["todo_lines"]),
            "(TODO|FIXME|HACK|XXX|BUG)",
            str(repo_path),
        ],
        repo_path,
    )
    if not output:
        return ""
    return "\n".join(output.splitlines()[: budget["todo_lines"]]).strip()


def _repo_recent_commits(repo_path: Path, budget_name: str) -> str:
    budget = _budget(budget_name)
    output = _run_capture(
        [
            "git",
            "log",
            f"-{budget['commit_lines']}",
            "--pretty=format:%h %ad %s",
            "--date=short",
        ],
        repo_path,
    )
    if not output:
        return ""
    return "\n".join(output.splitlines()[: budget["commit_lines"]]).strip()


def _repo_diffstat(repo_path: Path, budget_name: str) -> str:
    budget = _budget(budget_name)
    output = _run_capture(["git", "diff", "--stat"], repo_path)
    if not output:
        return ""
    return output[: budget["diffstat_chars"]].strip()


def _repo_entrypoints(repo_path: Path, budget_name: str) -> str:
    budget = _budget(budget_name)
    candidates = [
        "src/index.ts",
        "src/main.ts",
        "src/App.tsx",
        "src/main.py",
        "app.py",
        "main.py",
        "manage.py",
        "server.py",
        "index.js",
        "main.go",
        "cmd",
        "internal",
        "app",
        "src",
    ]
    found: list[str] = []
    for relative in candidates:
        path = repo_path / relative
        if path.exists():
            found.append(relative)
    if len(found) < budget["entrypoints"]:
        files_output = _run_capture(
            [
                "rg",
                "--files",
                str(repo_path),
                "-g",
                "package.json",
                "-g",
                "pyproject.toml",
                "-g",
                "tsconfig.json",
                "-g",
                "*.tsx",
                "-g",
                "*.ts",
                "-g",
                "*.py",
            ],
            repo_path,
        )
        for line in files_output.splitlines():
            line = line.strip()
            if line and line not in found:
                found.append(line)
            if len(found) >= budget["entrypoints"]:
                break
    if not found:
        return ""
    return "\n".join(found[: budget["entrypoints"]]).strip()


def _repo_context(repo_path: Path, budget_name: str = "medium") -> str:
    budget = _budget(budget_name)
    if not repo_path.exists() or not repo_path.is_dir():
        return f"[Repo path missing: {repo_path}]"
    parts: list[str] = [f"Repo path: {repo_path}"]
    git_root = (repo_path / ".git").exists()
    if git_root:
        branch = _run_capture(["git", "rev-parse", "--abbrev-ref", "HEAD"], repo_path)
        status = _run_capture(["git", "status", "--short"], repo_path)
        commits = _repo_recent_commits(repo_path, budget_name)
        diffstat = _repo_diffstat(repo_path, budget_name)
        if branch:
            parts.append(f"\nGit branch:\n{branch}")
        if status:
            parts.append(f"\nGit status:\n{status[:4000]}")
        if diffstat:
            parts.append(f"\nWorking diff summary:\n{diffstat}")
        if commits:
            parts.append(f"\nRecent commits:\n{commits}")
    readme = None
    for name in ("README.md", "README", "readme.md"):
        candidate = repo_path / name
        if candidate.exists():
            readme = candidate
            break
    if readme:
        parts.append(f"\nREADME excerpt:\n{_read_file_excerpt(readme, budget['readme_chars'])}")
    manifest_excerpt = _repo_manifest_excerpt(repo_path, budget_name)
    if manifest_excerpt:
        parts.append(f"\nProject manifests:\n{manifest_excerpt}")
    entrypoints = _repo_entrypoints(repo_path, budget_name)
    if entrypoints:
        parts.append(f"\nLikely entrypoints and key files:\n{entrypoints}")
    todo_excerpt = _repo_todo_excerpt(repo_path, budget_name)
    if todo_excerpt:
        parts.append(f"\nOpen markers:\n{todo_excerpt}")
    files_output = _run_capture(["rg", "--files", str(repo_path)], repo_path)
    files = [line.strip() for line in files_output.splitlines() if line.strip()][: budget["file_list"]]
    if files:
        parts.append("\nRepo file sample:\n" + "\n".join(files))
    return "\n".join(parts).strip()


def _parse_github_repo_url(repo_url: str) -> tuple[str, str] | None:
    parsed = urlparse(repo_url.strip())
    if parsed.netloc not in {"github.com", "www.github.com"}:
        return None
    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) < 2:
        return None
    owner, repo = parts[0], parts[1]
    if repo.endswith(".git"):
        repo = repo[:-4]
    return owner, repo


def _github_repo_context(repo_url: str, budget_name: str = "medium") -> str:
    budget = _budget(budget_name)
    parsed = _parse_github_repo_url(repo_url)
    if not parsed:
        return f"[Invalid GitHub repo URL: {repo_url}]"
    owner, repo = parsed
    repo_api = f"https://api.github.com/repos/{owner}/{repo}"
    repo_data = _fetch_json(repo_api)
    if not isinstance(repo_data, dict):
        return f"[Could not fetch GitHub repo: {owner}/{repo}]"
    default_branch = repo_data.get("default_branch") or "main"
    language = repo_data.get("language") or "Unknown"
    description = repo_data.get("description") or ""
    parts = [f"GitHub repo: {owner}/{repo}", f"Default branch: {default_branch}", f"Primary language: {language}"]
    if description:
        parts.append(f"Description: {description}")
    readme_api = f"{repo_api}/readme"
    readme_data = _fetch_json(readme_api)
    if isinstance(readme_data, dict):
        download_url = readme_data.get("download_url")
        if download_url:
            readme_text = _fetch_text(download_url, budget["github_readme_chars"])
            if readme_text:
                parts.append(f"\nREADME excerpt:\n{readme_text}")
    contents_api = f"{repo_api}/contents"
    contents = _fetch_json(contents_api)
    if isinstance(contents, list):
        sample = []
        for item in contents[: budget["github_file_lines"]]:
            item_type = item.get("type", "file")
            name = item.get("name", "")
            if name:
                sample.append(f"{item_type}: {name}")
        if sample:
            parts.append("\nTop-level files:\n" + "\n".join(sample))
    return "\n".join(parts).strip()


def _source_manifest(user_task: str, file_path: str, repo_path: str, github_repo_url: str, prompt_text: str, resolved_text: str, context_budget: str = "medium") -> dict:
    sources = []
    if file_path.strip():
        sources.append({"kind": "file", "path": file_path.strip()})
    if repo_path.strip():
        sources.append({"kind": "repo_path", "path": repo_path.strip()})
    if github_repo_url.strip():
        sources.append({"kind": "github_repo", "url": github_repo_url.strip()})
    if prompt_text.strip():
        sources.append({"kind": "prompt_text", "chars": len(prompt_text.strip())})
    if not sources:
        sources.append({"kind": "empty"})
    if any(source["kind"] in {"file", "repo_path", "github_repo"} for source in sources):
        source_mode = "files_first"
    elif any(source["kind"] == "prompt_text" for source in sources):
        source_mode = "prompt_only"
    else:
        source_mode = "empty"
    return {
        "timestamp": now_iso(),
        "task": user_task,
        "context_budget": context_budget,
        "source_mode": source_mode,
        "sources": sources,
        "prompt_chars": len(prompt_text.strip()),
        "resolved_input_chars": len(resolved_text),
        "resolved_input_sha256": _sha256_text(resolved_text),
    }


def _write_manifest(stem: str, manifest: dict) -> Path:
    MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)
    path = MANIFESTS_DIR / f"{stem}.json"
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _write_run_record(stem: str, payload: dict) -> Path:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    path = RUNS_DIR / f"{stem}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def build_run_text(task: str, text: str, file_path: str, repo_path: str, github_repo_url: str, context_budget: str = "medium") -> str:
    parts: list[str] = []
    instruction = TASK_INSTRUCTIONS.get(task)
    if instruction:
        parts.append(instruction)
    if text.strip():
        parts.append(text.strip())
    if file_path.strip():
        path = Path(file_path).expanduser()
        parts.append(f"Imported file: {path}\n{_read_file_excerpt(path)}")
    if repo_path.strip():
        path = Path(repo_path).expanduser()
        parts.append(_repo_context(path, context_budget))
    if github_repo_url.strip():
        parts.append(_github_repo_context(github_repo_url, context_budget))
    return "\n\n".join(part for part in parts if part).strip()


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def recent_runs(limit: int = 12) -> list[dict]:
    if not RUNS_DIR.exists():
        return []
    rows: list[dict] = []
    for path in sorted(RUNS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        payload["artifact"] = str(path)
        rows.append(payload)
    return rows


class ElgoogHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/slots":
            if SLOTS_PATH.exists():
                try:
                    slots = json.loads(SLOTS_PATH.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    json_response(self, 500, {"status": "error", "message": "invalid slots file"})
                    return
            else:
                slots = []
            json_response(self, 200, {"slots": slots, "slots_path": str(SLOTS_PATH)})
            return
        if parsed.path == "/api/runs":
            json_response(self, 200, {"runs": recent_runs()})
            return
        if parsed.path == "/api/doctor":
            result = subprocess.run(
                [sys.executable, str(CLI), "doctor", "--json"],
                cwd=str(ROOT),
                text=True,
                capture_output=True,
                check=False,
            )
            if result.returncode != 0:
                json_response(self, 500, {"status": "error", "stderr": result.stderr.strip(), "stdout": result.stdout.strip()})
                return
            json_response(self, 200, json.loads(result.stdout))
            return
        if parsed.path == "/api/key-url":
            result = subprocess.run(
                [sys.executable, str(CLI), "key-url"],
                cwd=str(ROOT),
                text=True,
                capture_output=True,
                check=False,
            )
            if result.returncode != 0:
                json_response(self, 500, {"status": "error", "stderr": result.stderr.strip()})
                return
            json_response(self, 200, {"key_url": result.stdout.strip()})
            return
        if parsed.path in ("/", "/index.html"):
            file_response(self, UI_DIR / "index.html", "text/html; charset=utf-8")
            return
        if parsed.path == "/styles.css":
            file_response(self, UI_DIR / "styles.css", "text/css; charset=utf-8")
            return
        if parsed.path == "/app.js":
            file_response(self, UI_DIR / "app.js", "application/javascript; charset=utf-8")
            return
        self.send_error(404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/slots":
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length) if length else b"{}"
            try:
                payload = json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError:
                json_response(self, 400, {"status": "error", "message": "invalid json"})
                return
            slots = payload.get("slots")
            if not isinstance(slots, list):
                json_response(self, 400, {"status": "error", "message": "slots must be a list"})
                return
            clean_slots = []
            for idx, item in enumerate(slots, start=1):
                if not isinstance(item, dict):
                    json_response(self, 400, {"status": "error", "message": f"invalid slot entry at {idx}"})
                    return
                slot_name = str(item.get("slot") or f"slot_{idx}").strip()
                api_key = str(item.get("api_key") or "").strip()
                if not api_key:
                    continue
                clean_slots.append({"slot": slot_name, "api_key": api_key})
            SLOTS_PATH.parent.mkdir(parents=True, exist_ok=True)
            SLOTS_PATH.write_text(json.dumps(clean_slots, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            json_response(self, 200, {"status": "saved", "count": len(clean_slots), "slots_path": str(SLOTS_PATH)})
            return
        if parsed.path != "/api/run":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            json_response(self, 400, {"status": "error", "message": "invalid json"})
            return
        user_task = str(payload.get("task") or "plan_next_steps")
        task_class = TASK_MAP.get(user_task, "planning")
        text = str(payload.get("text") or "").strip()
        file_path = str(payload.get("file_path") or "").strip()
        repo_path = str(payload.get("repo_path") or "").strip()
        github_repo_url = str(payload.get("github_repo_url") or "").strip()
        context_budget = str(payload.get("context_budget") or "medium").strip()
        run_text = build_run_text(user_task, text, file_path, repo_path, github_repo_url, context_budget)
        source_manifest = _source_manifest(user_task, file_path, repo_path, github_repo_url, text, run_text, context_budget)
        slot = str(payload.get("slot") or "gemini_slot_1")
        dry_run = bool(payload.get("dry_run", True))
        cmd = [
            sys.executable,
            str(CLI),
            "run",
            "--task-class",
            task_class,
            "--slot",
            slot,
            "--json",
        ]
        if dry_run:
            cmd.append("--dry-run")
        if run_text:
            cmd.extend(["--text", run_text])
        result = subprocess.run(cmd, cwd=str(ROOT), text=True, capture_output=True, check=False)
        if result.returncode not in (0, 2, 73, 75):
            json_response(self, 500, {"status": "error", "stderr": result.stderr.strip(), "stdout": result.stdout.strip(), "returncode": result.returncode})
            return
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            data = {"status": "error", "stdout": result.stdout.strip(), "stderr": result.stderr.strip(), "returncode": result.returncode}
        data["task"] = user_task
        data["task_class"] = task_class
        data["input_file_path"] = file_path or None
        data["input_repo_path"] = repo_path or None
        data["input_github_repo_url"] = github_repo_url or None
        data["context_budget"] = context_budget
        data["source_mode"] = source_manifest["source_mode"]
        data["resolved_input_sha256"] = source_manifest["resolved_input_sha256"]
        data["resolved_input_chars"] = len(run_text)
        stem = Path(str(data.get("artifact", "artifact"))).stem
        manifest_path = _write_manifest(stem, source_manifest)
        data["source_manifest"] = str(manifest_path)
        run_record = {
            "timestamp": now_iso(),
            "task": user_task,
            "task_class": task_class,
            "status": data.get("status"),
            "slot": slot,
            "model": data.get("model"),
            "artifact": data.get("artifact"),
            "output_path": data.get("output_path"),
            "source_manifest": str(manifest_path),
            "source_mode": source_manifest["source_mode"],
            "input_file_path": file_path or None,
            "input_repo_path": repo_path or None,
            "input_github_repo_url": github_repo_url or None,
            "context_budget": context_budget,
            "resolved_input_sha256": source_manifest["resolved_input_sha256"],
            "resolved_input_chars": len(run_text),
        }
        run_record_path = _write_run_record(stem, run_record)
        data["run_record"] = str(run_record_path)
        if data.get("status") == "dry_run":
            data["artifact"] = str(run_record_path)
        output_path = data.get("output_path")
        if output_path:
            out_path = Path(output_path)
            if out_path.exists():
                data["output_text"] = out_path.read_text(encoding="utf-8", errors="ignore")
        json_response(self, 200, data)


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), ElgoogHandler)
    print(f"Elgoog app running at http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
