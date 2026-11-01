"""Focused safety tests for the task-sync helper."""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "tools" / "github_task_sync.py"
spec = importlib.util.spec_from_file_location("github_task_sync", MODULE_PATH)
sync = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(sync)


class SyncSafetyTests(unittest.TestCase):
    def test_sensitive_names_are_flagged(self) -> None:
        for path in (".env", ".env.test", "config/prod.pem", "secrets.json",
                     "api-token.txt", ".ssh/config", "private/notes.txt"):
            with self.subTest(path=path):
                self.assertTrue(sync.path_is_sensitive(path))

    def test_ordinary_source_files_are_not_flagged(self) -> None:
        self.assertFalse(sync.path_is_sensitive("src/feature.py"))
        self.assertFalse(sync.path_is_sensitive("docs/WORKFLOW.md"))

    def test_repository_relative_path_validation(self) -> None:
        self.assertEqual(sync.validate_path("README.md"), "README.md")
        for path in ("../outside", "C:/outside", "/outside"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                sync.validate_path(path)

    def test_reviews_are_mandatory_for_sensitive_and_deleted_files(self) -> None:
        from unittest.mock import patch
        with patch.object(sync, "is_deletion", return_value=False), \
             patch.object(sync.sys.stdin, "isatty", return_value=False):
            with self.assertRaisesRegex(RuntimeError, "Interactive review"):
                sync.require_review([".env"], "HEAD")
        with patch.object(sync, "is_deletion", return_value=True), \
             patch.object(sync.sys.stdin, "isatty", return_value=False):
            with self.assertRaisesRegex(RuntimeError, "Interactive review"):
                sync.require_review(["README.md"], "HEAD")

    def test_slug_validation_rejects_invalid_characters(self) -> None:
        for slug in ("../main", "with/slash"):
            with self.subTest(slug=slug), self.assertRaises(SystemExit):
                with __import__("contextlib").redirect_stderr(__import__("io").StringIO()):
                    sync.main(["--branch-slug", slug, "--check", "exit 0", "README.md"])
        self.assertEqual(sync.normalize_slug("Fix Example_2"), "fix-example_2")


if __name__ == "__main__":
    unittest.main()