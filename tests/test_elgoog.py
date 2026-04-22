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
        args = parser.parse_args(["understand", "--repo", ".", "--slot", "work"])
        self.assertEqual(args.command, "understand")
        self.assertEqual(args.repo, ".")
        self.assertEqual(args.slot, "work")

    def test_run_parser_accepts_github(self) -> None:
        parser = elgoog.build_parser()
        args = parser.parse_args(["run", "--github", "https://github.com/google-gemini/gemini-cli", "--task-class", "classification", "--dry-run"])
        self.assertEqual(args.command, "run")
        self.assertEqual(args.github, "https://github.com/google-gemini/gemini-cli")


if __name__ == "__main__":
    unittest.main()
