from __future__ import annotations

import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from doc_prefix import apply_plan, plan_renames  # noqa: E402


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_basic_preview_and_apply() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _write(root / "alpha.txt", "A")
        _write(root / "beta.txt", "B")

        plan = plan_renames(
            root,
            first="Jane",
            last="Doe",
            recursive=False,
            force=False,
            conflict="suffix",
            date_yyyymm="202602",
            use_mtime=False,
        )

        rename_items = [it for it in plan if it.reason.startswith("rename")]
        skip_items = [it for it in plan if not it.reason.startswith("rename")]

        assert len(rename_items) == 2, f"Expected 2 renames, got {len(rename_items)}"
        assert len(skip_items) == 0, f"Expected 0 skips, got {len(skip_items)}"
        assert (root / "alpha.txt").exists()
        assert rename_items[0].dst.name.startswith("202602 - Doe, Jane - ")

        renamed, skipped = apply_plan(plan, conflict="suffix")
        assert renamed == 2, f"Expected renamed=2, got {renamed}"
        assert skipped == 0, f"Expected skipped=0, got {skipped}"
        assert not (root / "alpha.txt").exists()
        assert (root / "202602 - Doe, Jane - alpha.txt").read_text(encoding="utf-8") == "A"
        assert (root / "202602 - Doe, Jane - beta.txt").read_text(encoding="utf-8") == "B"


def test_overwrite_chain_safety() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _write(root / "x.txt", "0")
        _write(root / "202602 - Doe, Jane - x.txt", "1")
        _write(root / "202602 - Doe, Jane - 202602 - Doe, Jane - x.txt", "2")

        plan = plan_renames(
            root,
            first="Jane",
            last="Doe",
            recursive=False,
            force=True,
            conflict="overwrite",
            date_yyyymm="202602",
            use_mtime=False,
        )

        renamed, skipped = apply_plan(plan, conflict="overwrite")
        assert renamed == 3, f"Expected renamed=3, got {renamed}"
        assert skipped == 0, f"Expected skipped=0, got {skipped}"

        assert (root / "202602 - Doe, Jane - x.txt").read_text(encoding="utf-8") == "0"
        assert (
            root / "202602 - Doe, Jane - 202602 - Doe, Jane - x.txt"
        ).read_text(encoding="utf-8") == "1"
        assert (
            root / "202602 - Doe, Jane - 202602 - Doe, Jane - 202602 - Doe, Jane - x.txt"
        ).read_text(encoding="utf-8") == "2"


def main() -> int:
    tests = [
        ("basic preview/apply", test_basic_preview_and_apply),
        ("overwrite chain safety", test_overwrite_chain_safety),
    ]
    print("Running DocPrefix smoke tests...")
    for name, fn in tests:
        fn()
        print(f"  PASS: {name}")
    print("Smoke tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
