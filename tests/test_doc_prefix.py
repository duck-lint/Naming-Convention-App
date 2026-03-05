import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

import doc_prefix


class DocPrefixTests(unittest.TestCase):
    def write_file(self, root: Path, name: str, content: str) -> Path:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def test_overwrite_force_does_not_delete_in_plan_source(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.write_file(root, "a.txt", "A")
            self.write_file(root, "202602 - Doe, Jane - a.txt", "B")

            plan = doc_prefix.plan_renames(
                root,
                first="Jane",
                last="Doe",
                recursive=False,
                force=True,
                conflict="overwrite",
                date_yyyymm="202602",
                use_mtime=False,
            )

            doc_prefix.apply_plan(plan, conflict="overwrite")

            self.assertFalse((root / "a.txt").exists())
            self.assertEqual(
                (root / "202602 - Doe, Jane - a.txt").read_text(encoding="utf-8"), "A"
            )
            self.assertEqual(
                (root / "202602 - Doe, Jane - 202602 - Doe, Jane - a.txt").read_text(
                    encoding="utf-8"
                ),
                "B",
            )

    def test_overwrite_chain_rename_is_safe(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.write_file(root, "x.txt", "0")
            self.write_file(root, "202602 - Doe, Jane - x.txt", "1")
            self.write_file(root, "202602 - Doe, Jane - 202602 - Doe, Jane - x.txt", "2")

            plan = doc_prefix.plan_renames(
                root,
                first="Jane",
                last="Doe",
                recursive=False,
                force=True,
                conflict="overwrite",
                date_yyyymm="202602",
                use_mtime=False,
            )

            doc_prefix.apply_plan(plan, conflict="overwrite")

            self.assertEqual(
                (root / "202602 - Doe, Jane - x.txt").read_text(encoding="utf-8"), "0"
            )
            self.assertEqual(
                (root / "202602 - Doe, Jane - 202602 - Doe, Jane - x.txt").read_text(
                    encoding="utf-8"
                ),
                "1",
            )
            self.assertEqual(
                (
                    root
                    / "202602 - Doe, Jane - 202602 - Doe, Jane - 202602 - Doe, Jane - x.txt"
                ).read_text(encoding="utf-8"),
                "2",
            )

    def test_non_force_replaces_existing_prefix_when_person_differs(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = self.write_file(root, "202602 - Aubry, Madison - a.txt", "A")

            plan = doc_prefix.plan_renames(
                root,
                first="test",
                last="test",
                recursive=False,
                force=False,
                conflict="overwrite",
                date_yyyymm="202602",
                use_mtime=False,
            )

            self.assertEqual(len(plan), 1)
            self.assertEqual(plan[0].src, src)
            self.assertEqual(plan[0].reason, "rename")
            self.assertEqual(plan[0].dst.name, "202602 - test, test - a.txt")

    def test_non_force_skips_when_existing_prefix_matches_person(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = self.write_file(root, "202602 - DOE, JANE - a.txt", "A")

            plan = doc_prefix.plan_renames(
                root,
                first="jane",
                last="doe",
                recursive=False,
                force=False,
                conflict="overwrite",
                date_yyyymm="202602",
                use_mtime=False,
            )

            self.assertEqual(len(plan), 1)
            self.assertEqual(plan[0].src, src)
            self.assertEqual(plan[0].dst, src)
            self.assertEqual(plan[0].reason, "skip:already-prefixed")

    def test_non_force_replaces_existing_prefix_when_date_differs(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = self.write_file(root, "202602 - Aubry, Madison - a.txt", "A")

            plan = doc_prefix.plan_renames(
                root,
                first="Madison",
                last="Aubry",
                recursive=False,
                force=False,
                conflict="overwrite",
                date_yyyymm="202603",
                use_mtime=False,
            )

            self.assertEqual(len(plan), 1)
            self.assertEqual(plan[0].src, src)
            self.assertEqual(plan[0].reason, "rename")
            self.assertEqual(plan[0].dst.name, "202603 - Aubry, Madison - a.txt")

    def test_non_force_skips_when_existing_prefix_matches_person_and_date(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = self.write_file(root, "202603 - Aubry, Madison - a.txt", "A")

            plan = doc_prefix.plan_renames(
                root,
                first="Madison",
                last="Aubry",
                recursive=False,
                force=False,
                conflict="overwrite",
                date_yyyymm="202603",
                use_mtime=False,
            )

            self.assertEqual(len(plan), 1)
            self.assertEqual(plan[0].src, src)
            self.assertEqual(plan[0].dst, src)
            self.assertEqual(plan[0].reason, "skip:already-prefixed")

    def test_suffix_resolves_planned_destination_collision(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.write_file(root, "202602 - Doe, Jane - a.txt", "A")
            self.write_file(root, "202603 - Doe, Jane - a.txt", "B")

            plan = doc_prefix.plan_renames(
                root,
                first="Jane",
                last="Doe",
                recursive=False,
                force=False,
                conflict="suffix",
                date_yyyymm="202604",
                use_mtime=False,
            )

            rename_items = [it for it in plan if it.reason.startswith("rename")]
            self.assertEqual(len(rename_items), 2)
            dst_names = [it.dst.name for it in rename_items]
            self.assertEqual(len(set(dst_names)), 2)
            self.assertIn("202604 - Doe, Jane - a.txt", dst_names)
            self.assertIn("202604 - Doe, Jane - a (1).txt", dst_names)

    def test_skip_marks_planned_destination_collision(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.write_file(root, "202602 - Doe, Jane - a.txt", "A")
            self.write_file(root, "202603 - Doe, Jane - a.txt", "B")

            plan = doc_prefix.plan_renames(
                root,
                first="Jane",
                last="Doe",
                recursive=False,
                force=False,
                conflict="skip",
                date_yyyymm="202604",
                use_mtime=False,
            )

            rename_items = [it for it in plan if it.reason.startswith("rename")]
            self.assertEqual(len(rename_items), 1)
            self.assertEqual(sum(it.reason == "skip:conflict-planned" for it in plan), 1)

    def test_overwrite_rejects_duplicate_planned_destinations(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.write_file(root, "202602 - Doe, Jane - a.txt", "A")
            self.write_file(root, "202603 - Doe, Jane - a.txt", "B")

            with self.assertRaisesRegex(
                ValueError, r"Multiple sources.*same destination"
            ):
                doc_prefix.plan_renames(
                    root,
                    first="Jane",
                    last="Doe",
                    recursive=False,
                    force=False,
                    conflict="overwrite",
                    date_yyyymm="202604",
                    use_mtime=False,
                )

    def test_invalid_date_uses_argparse_error(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            stderr = io.StringIO()
            argv = [
                "doc_prefix.py",
                td,
                "--first",
                "Jane",
                "--last",
                "Doe",
                "--date",
                "2026-02",
            ]

            with mock.patch.object(sys, "argv", argv), redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as ctx:
                    doc_prefix.main()

            self.assertEqual(ctx.exception.code, 2)
            err = stderr.getvalue()
            self.assertIn("--date", err)
            self.assertIn("YYYYMM", err)

    def test_default_date_computed_once_per_run(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.write_file(root, "a.txt", "A")
            self.write_file(root, "b.txt", "B")

            stdout = io.StringIO()
            argv = ["doc_prefix.py", str(root), "--first", "Jane", "--last", "Doe"]

            with (
                mock.patch.object(sys, "argv", argv),
                mock.patch.object(
                    doc_prefix, "yyyymm_from_now", side_effect=["202601", "202602"]
                ) as mock_now,
                redirect_stdout(stdout),
            ):
                rc = doc_prefix.main()

            self.assertEqual(rc, 0)
            self.assertEqual(mock_now.call_count, 1)
            out = stdout.getvalue()
            self.assertIn("202601 - Doe, Jane - a.txt", out)
            self.assertIn("202601 - Doe, Jane - b.txt", out)

    def test_overwrite_cycle_swap_uses_temp_staging(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            a = self.write_file(root, "a.txt", "A")
            b = self.write_file(root, "b.txt", "B")

            plan = [
                doc_prefix.PlanItem(a, b, "rename:overwrite"),
                doc_prefix.PlanItem(b, a, "rename:overwrite"),
            ]

            renamed, skipped = doc_prefix.apply_plan(plan, conflict="overwrite")

            self.assertEqual((renamed, skipped), (2, 0))
            self.assertEqual((root / "a.txt").read_text(encoding="utf-8"), "B")
            self.assertEqual((root / "b.txt").read_text(encoding="utf-8"), "A")

    def test_apply_plan_wraps_non_overwrite_rename_errors(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "a.txt"
            dst = root / "b.txt"
            plan = [doc_prefix.PlanItem(src, dst, "rename")]

            with mock.patch.object(doc_prefix.os, "rename", side_effect=OSError("boom")):
                with self.assertRaisesRegex(
                    RuntimeError, r"Failed rename: .*a\.txt .*-> .*b\.txt: .*boom"
                ):
                    doc_prefix.apply_plan(plan, conflict="suffix")


if __name__ == "__main__":
    unittest.main()
