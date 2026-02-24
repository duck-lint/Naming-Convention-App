import tempfile
import unittest
import zipfile
from pathlib import Path

import bulk_extract_zips


class BulkExtractZipsTests(unittest.TestCase):
    def write_zip(self, zip_path: Path, members: dict[str, str]) -> None:
        zip_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, "w") as zf:
            for name, content in members.items():
                zf.writestr(name, content)

    def test_zip_slip_member_is_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            in_dir = root / "in"
            out_dir = root / "out"
            in_dir.mkdir()
            self.write_zip(
                in_dir / "one.zip",
                {
                    "../evil.txt": "EVIL",
                    "ok.txt": "OK",
                },
            )

            summary = bulk_extract_zips.run_bulk_extract(
                in_dir,
                out_dir,
                subfolders=False,
                overwrite=False,
                dry_run=False,
                verbose=False,
            )

            self.assertTrue((out_dir / "ok.txt").exists())
            self.assertEqual((out_dir / "ok.txt").read_text(encoding="utf-8"), "OK")
            outside_evil = out_dir.parent / "evil.txt"
            self.assertFalse(outside_evil.exists())
            self.assertEqual(summary.files_skipped_unsafe, 1)
            self.assertEqual(summary.files_extracted, 1)
            self.assertEqual(summary.zips_found, 1)
            self.assertEqual(summary.zips_processed, 1)

    def test_duplicate_skip_default_in_flat_mode(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            in_dir = root / "in"
            out_dir = root / "out"
            in_dir.mkdir()
            self.write_zip(in_dir / "a.zip", {"same.txt": "FIRST"})
            self.write_zip(in_dir / "b.zip", {"same.txt": "SECOND"})

            summary = bulk_extract_zips.run_bulk_extract(
                in_dir,
                out_dir,
                subfolders=False,
                overwrite=False,
                dry_run=False,
                verbose=False,
            )

            target = out_dir / "same.txt"
            self.assertTrue(target.exists())
            self.assertEqual(target.read_text(encoding="utf-8"), "FIRST")
            self.assertEqual(summary.files_extracted, 1)
            self.assertEqual(summary.files_skipped_duplicates, 1)
            self.assertEqual(summary.zips_found, 2)
            self.assertEqual(summary.zips_processed, 2)

    def test_dry_run_summary_matches_real_run_for_core_counters(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            in_dir = root / "in"
            out_dry = root / "out_dry"
            out_real = root / "out_real"
            in_dir.mkdir()
            self.write_zip(in_dir / "one.zip", {"alpha.txt": "A"})
            self.write_zip(in_dir / "two.zip", {"alpha.txt": "B", "beta.txt": "BETA"})

            dry_summary = bulk_extract_zips.run_bulk_extract(
                in_dir,
                out_dry,
                subfolders=False,
                overwrite=False,
                dry_run=True,
                verbose=False,
            )
            real_summary = bulk_extract_zips.run_bulk_extract(
                in_dir,
                out_real,
                subfolders=False,
                overwrite=False,
                dry_run=False,
                verbose=False,
            )

            self.assertEqual(dry_summary.zips_found, real_summary.zips_found)
            self.assertEqual(dry_summary.zips_processed, real_summary.zips_processed)
            self.assertEqual(
                dry_summary.files_skipped_duplicates, real_summary.files_skipped_duplicates
            )
            self.assertEqual(dry_summary.files_skipped_unsafe, real_summary.files_skipped_unsafe)
            self.assertEqual(dry_summary.bad_zips_skipped, real_summary.bad_zips_skipped)
            self.assertEqual(dry_summary.other_errors_count, real_summary.other_errors_count)
            self.assertEqual(dry_summary.files_extracted, real_summary.files_extracted)

            self.assertFalse((out_dry / "alpha.txt").exists())
            self.assertFalse((out_dry / "beta.txt").exists())
            self.assertTrue((out_real / "alpha.txt").exists())
            self.assertTrue((out_real / "beta.txt").exists())

    def test_cli_recursive_flag_discovers_nested_zips(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            in_dir = root / "in"
            nested_dir = in_dir / "nested"
            out_dir = root / "out"
            nested_dir.mkdir(parents=True)
            self.write_zip(nested_dir / "inner.zip", {"ok.txt": "OK"})

            argv_base = [
                "--in_dir",
                str(in_dir),
                "--out_dir",
                str(out_dir),
                "--dry_run",
            ]

            rc_no_recursive = bulk_extract_zips.main(argv_base)
            self.assertEqual(rc_no_recursive, 0)
            args_no_recursive = bulk_extract_zips.build_parser().parse_args(argv_base)
            summary_no_recursive = bulk_extract_zips.run_from_args(args_no_recursive)
            self.assertEqual(summary_no_recursive.zips_found, 0)
            self.assertEqual(summary_no_recursive.zips_processed, 0)

            argv_recursive = [*argv_base, "--recursive"]
            rc_recursive = bulk_extract_zips.main(argv_recursive)
            self.assertEqual(rc_recursive, 0)
            args_recursive = bulk_extract_zips.build_parser().parse_args(argv_recursive)
            summary_recursive = bulk_extract_zips.run_from_args(args_recursive)
            self.assertEqual(summary_recursive.zips_found, 1)
            self.assertEqual(summary_recursive.zips_processed, 1)
            self.assertEqual(summary_recursive.files_extracted, 1)


if __name__ == "__main__":
    unittest.main()
