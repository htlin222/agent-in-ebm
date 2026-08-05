#!/usr/bin/env python3
"""章節發布的確定性建置入口。只用標準函式庫，沒有 pip 相依。

  python3 build/build.py check   --report dist/_build/check.json
  python3 build/build.py prepare --outdir dist/_build --tag TAG --date YYYY-MM-DD
  python3 build/build.py figures --outdir dist/figures --epoch 1234567890
  python3 build/build.py bib     --outdir dist --cache .cache/crossref \\
                                 --tag TAG --date YYYY-MM-DD --commit SHA
  python3 build/build.py notes   --outdir dist --commit SHA --epoch N \\
                                 --previous-tag TAG --report ... --toolchain ...

同一個 commit 重跑，每個步驟都應得到相同輸出。唯二的網路來源是 doi.org
與正文裡的遠端圖片；兩者都會重試，失敗就讓 build 停住而不是默默發出殘缺的檔案。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import steps_build  # noqa: E402
import steps_check  # noqa: E402
import steps_notes  # noqa: E402
from common import REPO  # noqa: E402

DEFAULT_MD = str(REPO / "docs/manuscript/chapter-full.md")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--md", default=DEFAULT_MD, help="正文路徑")

    check = subparsers.add_parser("check", parents=[common], help="驗證正文")
    check.add_argument("--report", default="", help="軟缺口與統計的輸出 JSON")
    check.set_defaults(function=steps_check.run)

    prepare = subparsers.add_parser("prepare", parents=[common], help="產生 pandoc 來源與 metadata")
    prepare.add_argument("--outdir", required=True)
    prepare.add_argument("--tag", required=True)
    prepare.add_argument("--date", required=True)
    prepare.set_defaults(function=steps_build.prepare)

    figures = subparsers.add_parser("figures", parents=[common], help="匯出帶標號的獨立圖檔")
    figures.add_argument("--outdir", required=True)
    figures.add_argument("--epoch", type=int, required=True, help="SOURCE_DATE_EPOCH，用來固定 mtime")
    figures.set_defaults(function=steps_build.figures)

    bib = subparsers.add_parser("bib", parents=[common], help="產生 citation.bib 與 references.bib")
    bib.add_argument("--outdir", required=True)
    bib.add_argument("--cache", required=True)
    bib.add_argument("--tag", required=True)
    bib.add_argument("--date", required=True)
    bib.add_argument("--commit", required=True)
    bib.set_defaults(function=steps_build.bib)

    notes = subparsers.add_parser("notes", parents=[common], help="產生 release 內文")
    notes.add_argument("--outdir", required=True)
    notes.add_argument("--commit", required=True)
    notes.add_argument("--epoch", required=True)
    notes.add_argument("--previous-tag", default="")
    notes.add_argument("--report", default="")
    notes.add_argument("--toolchain", default="")
    notes.set_defaults(function=steps_notes.run)

    args = parser.parse_args()
    args.function(args)


if __name__ == "__main__":
    main()
