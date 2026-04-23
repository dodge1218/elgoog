from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import elgoog


class ClassifyErrorTests(unittest.TestCase):
    def test_quota_errors_are_classified(self) -> None:
        self.assertEqual(elgoog.classify_error("HTTP 429 resource_exhausted"), "quota")

    def test_transient_errors_are_classified(self) -> None:
        self.assertEqual(elgoog.classify_error("504 deadline exceeded"), "transient")

    def test_503_unavailable_is_classified_as_transient(self) -> None:
        self.assertEqual(elgoog.classify_error("503 UNAVAILABLE"), "transient")

    def test_auth_errors_are_classified(self) -> None:
        self.assertEqual(elgoog.classify_error("permission denied"), "auth")

    def test_unknown_errors_fall_back_to_error(self) -> None:
        self.assertEqual(elgoog.classify_error("something odd happened"), "error")

    def test_status_next_action_for_transient(self) -> None:
        self.assertIn("retry", elgoog.status_next_action("transient"))

    def test_format_status_block_includes_next_action(self) -> None:
        payload = json.loads(elgoog.format_status_block(status="auth", slot="work", detail="permission denied"))
        self.assertEqual(payload["status"], "auth")
        self.assertEqual(payload["slot"], "work")
        self.assertIn("doctor", payload["next_action"])


class LoadSlotsTests(unittest.TestCase):
    def test_inline_string_slot_is_normalized(self) -> None:
        slots = elgoog.load_slots(slots_json='["abc12345"]')
        self.assertEqual(len(slots), 1)
        self.assertEqual(slots[0]["slot"], "slot_1")
        self.assertEqual(slots[0]["api_key"], "abc12345")
        self.assertEqual(slots[0]["source"], "inline")

    def test_slots_path_is_loaded(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "slots.json"
            path.write_text(json.dumps([{"slot": "work", "api_key": "xyz98765"}]), encoding="utf-8")
            slots = elgoog.load_slots(slots_path=path)
        self.assertEqual(slots, [{"slot": "work", "api_key": "xyz98765", "source": str(path)}])


class ParserTests(unittest.TestCase):
    def test_run_parser_accepts_task_class(self) -> None:
        parser = elgoog.build_parser()
        args = parser.parse_args(["run", "--text", "hello", "--task-class", "planning", "--dry-run"])
        self.assertEqual(args.command, "run")
        self.assertEqual(args.task_class, "planning")
        self.assertTrue(args.dry_run)

    def test_onboard_parser_exists(self) -> None:
        parser = elgoog.build_parser()
        args = parser.parse_args(["onboard", "--no-browser"])
        self.assertEqual(args.command, "onboard")
        self.assertTrue(args.no_browser)

    def test_auth_login_parser_exists(self) -> None:
        parser = elgoog.build_parser()
        args = parser.parse_args(["auth", "login", "--no-browser"])
        self.assertEqual(args.command, "auth")
        self.assertEqual(args.auth_command, "login")
        self.assertTrue(args.no_browser)

    def test_auth_add_parser_exists(self) -> None:
        parser = elgoog.build_parser()
        args = parser.parse_args(["auth", "add", "--slot", "gemini_slot_1", "--api-key", "abc123"])
        self.assertEqual(args.command, "auth")
        self.assertEqual(args.auth_command, "add")
        self.assertEqual(args.slot, "gemini_slot_1")
        self.assertEqual(args.api_key, "abc123")

    def test_help_parser_exists(self) -> None:
        parser = elgoog.build_parser()
        args = parser.parse_args(["help"])
        self.assertEqual(args.command, "help")

    def test_web_parser_exists(self) -> None:
        parser = elgoog.build_parser()
        args = parser.parse_args(["web", "--open-browser"])
        self.assertEqual(args.command, "web")
        self.assertTrue(args.open_browser)

    def test_recover_parser_exists(self) -> None:
        parser = elgoog.build_parser()
        args = parser.parse_args(["recover", "--text", "notes", "--slot", "work", "--dry-run"])
        self.assertEqual(args.command, "recover")
        self.assertEqual(args.slot, "work")
        self.assertTrue(args.dry_run)

    def test_todos_parser_exists(self) -> None:
        parser = elgoog.build_parser()
        args = parser.parse_args(["todos", "--file", "./notes.md", "--json"])
        self.assertEqual(args.command, "todos")
        self.assertEqual(args.file, "./notes.md")
        self.assertTrue(args.json)

    def test_understand_parser_accepts_repo(self) -> None:
        parser = elgoog.build_parser()
        args = parser.parse_args(["understand", "--repo", ".", "--slot", "work", "--context-budget", "small"])
        self.assertEqual(args.command, "understand")
        self.assertEqual(args.repo, ".")
        self.assertEqual(args.slot, "work")
        self.assertEqual(args.context_budget, "small")

    def test_run_parser_accepts_github(self) -> None:
        parser = elgoog.build_parser()
        args = parser.parse_args(["run", "--github", "https://github.com/google-gemini/gemini-cli", "--task-class", "classification", "--dry-run"])
        self.assertEqual(args.command, "run")
        self.assertEqual(args.github, "https://github.com/google-gemini/gemini-cli")

    def test_plan_parser_accepts_large_context_budget(self) -> None:
        parser = elgoog.build_parser()
        args = parser.parse_args(["plan", "--text", "release notes", "--context-budget", "large"])
        self.assertEqual(args.command, "plan")
        self.assertEqual(args.context_budget, "large")

    def test_session_parser_accepts_repo(self) -> None:
        parser = elgoog.build_parser()
        args = parser.parse_args(["session", "--repo", ".", "--slot", "work", "--name", "demo"])
        self.assertEqual(args.command, "session")
        self.assertEqual(args.repo, ".")
        self.assertEqual(args.slot, "work")
        self.assertEqual(args.name, "demo")

    def test_resume_parser_exists(self) -> None:
        parser = elgoog.build_parser()
        args = parser.parse_args(["resume", "--name", "demo", "--slot", "work"])
        self.assertEqual(args.command, "resume")
        self.assertEqual(args.name, "demo")
        self.assertEqual(args.slot, "work")

    def test_export_parser_exists(self) -> None:
        parser = elgoog.build_parser()
        args = parser.parse_args(["export", "--name", "demo", "--json"])
        self.assertEqual(args.command, "export")
        self.assertEqual(args.name, "demo")
        self.assertTrue(args.json)


class SessionTests(unittest.TestCase):
    def test_build_compaction_summary_keeps_recent_turns(self) -> None:
        turns = [
            {"user": "a", "assistant": "one"},
            {"user": "b", "assistant": "two"},
            {"user": "c", "assistant": "three"},
        ]
        summary, recent = elgoog._build_compaction_summary(turns, keep_last=2)
        self.assertIn("Session summary from earlier turns:", summary)
        self.assertEqual(len(recent), 2)
        self.assertEqual(recent[0]["user"], "b")

    def test_session_prompt_includes_new_input(self) -> None:
        prompt = elgoog._session_prompt(
            source_context="repo context",
            source_mode="repo",
            context_budget="medium",
            summary="prior summary",
            turns=[{"user": "what does this do", "assistant": "it does x"}],
            user_text="what should I inspect next?",
        )
        self.assertIn("## Source context", prompt)
        self.assertIn("## Session summary", prompt)
        self.assertIn("## Recent turns", prompt)
        self.assertIn("## New user input", prompt)

    def test_mark_and_resolve_last_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            original_index = elgoog.SESSIONS_INDEX_PATH
            try:
                elgoog.SESSIONS_INDEX_PATH = Path(tmpdir) / "_index.json"
                session_path = Path(tmpdir) / "demo.json"
                elgoog._mark_last_session("demo", session_path)
                self.assertEqual(elgoog._resolve_resume_name(""), "demo")
            finally:
                elgoog.SESSIONS_INDEX_PATH = original_index

    def test_resolve_resume_name_prefers_explicit_name(self) -> None:
        self.assertEqual(elgoog._resolve_resume_name("custom"), "custom")

    def test_render_session_export_markdown(self) -> None:
        state = {
            "name": "demo",
            "updated_at": "2026-04-22T20:00:00-04:00",
            "source_mode": "repo",
            "context_budget": "medium",
            "input_repo_path": ".",
            "summary": "prior summary",
            "turns": [{"user": "what now", "assistant": "inspect elgoog.py"}],
        }
        md = elgoog._render_session_export_markdown(state)
        self.assertIn("# Elgoog Session Export", md)
        self.assertIn("## Summary", md)
        self.assertIn("## Transcript", md)
        self.assertIn("inspect elgoog.py", md)


if __name__ == "__main__":
    unittest.main()
