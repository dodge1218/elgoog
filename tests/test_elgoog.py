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


if __name__ == "__main__":
    unittest.main()
