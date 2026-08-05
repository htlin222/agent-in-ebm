#!/usr/bin/env python3
"""notes：產生 release 內文。"""

from __future__ import annotations

import argparse
import difflib
import json
from pathlib import Path

from common import (
    RELEASE,
    git,
    load_json,
    parse_manuscript,
    read_manuscript,
    sha256_file,
    statistics,
)

SKIP_ASSETS = {"release-notes.md", "checksums.txt"}


def _changed_sections(
    md_relative: str, previous_tag: str, current: list[str], sections: list[dict]
) -> list[str] | None:
    """回傳改動所在的節；讀不到前一版時回傳 None，不能跟「沒有改動」混為一談。"""
    old = git("show", f"{previous_tag}:{md_relative}")
    if not old:
        return None
    matcher = difflib.SequenceMatcher(a=old.splitlines(), b=current, autojunk=False)
    changed: list[int] = []
    for tag, _, _, start, end in matcher.get_opcodes():
        if tag != "equal":
            changed.extend(range(start + 1, max(end, start + 1) + 1))

    titles: list[str] = []
    for line_number in changed:
        enclosing = [section for section in sections if section["line"] <= line_number]
        title = enclosing[-1]["title"] if enclosing else "（標題與前言）"
        if title not in titles:
            titles.append(title)
    return titles


def run(args: argparse.Namespace) -> None:
    md_path = Path(args.md).resolve()
    outdir = Path(args.outdir).resolve()
    lines = read_manuscript(md_path)
    parsed = parse_manuscript(lines)
    meta = load_json(RELEASE / "meta.json")
    stats = statistics(lines, parsed)

    report = {"soft": []}
    if args.report and Path(args.report).exists():
        report = json.loads(Path(args.report).read_text(encoding="utf-8"))
    toolchain = {}
    if args.toolchain and Path(args.toolchain).exists():
        toolchain = json.loads(Path(args.toolchain).read_text(encoding="utf-8"))

    out = [
        parsed["title"],
        "",
        f"由 `{meta['manuscript']}` 在 commit "
        f"[`{args.commit[:7]}`]({meta['repo_url']}/commit/{args.commit}) 的狀態建置。",
        "",
        "## 本次變更",
        "",
    ]

    if args.previous_tag:
        link = f"[`{args.previous_tag}`]({meta['repo_url']}/releases/tag/{args.previous_tag})"
        titles = _changed_sections(meta["manuscript"], args.previous_tag, lines, parsed["sections"])
        numstat = git("diff", "--numstat", f"{args.previous_tag}..{args.commit}", "--", meta["manuscript"])
        if titles is None or "\t" not in numstat:
            # 取不到前一版就照實說取不到。這裡絕不能退回「沒有改動」——
            # 那會讓一次失敗的比較讀起來像一次成功的比較。
            out.append(f"無法與 {link} 比較：這個 tag 在建置環境裡取不到正文。")
        else:
            added, removed = numstat.split("\t")[0], numstat.split("\t")[1]
            out.append(f"相對於 {link}：正文 +{added} / −{removed} 行。")
            out.append("")
            if titles:
                out.append("改動落在這些節：")
                out.append("")
                out += [f"- {title}" for title in titles]
            else:
                out.append("正文內容與上一版逐行相同；本次發布來自圖檔或建置流程的變更。")
    else:
        out.append("這是第一個版本，沒有可以比較的前一版。")

    out += [
        "",
        "## 內容統計",
        "",
        "| 項目 | 數量 |",
        "| --- | --- |",
        f"| 中文字數 | {stats['cjk_characters']:,} |",
        f"| 節（`##` 層級） | {stats['sections']} |",
        f"| 圖 | {stats['figures']} |",
        f"| 註腳 | {stats['footnotes']} |",
        "",
        "## 檔案",
        "",
        "| 檔案 | 大小 | sha256 |",
        "| --- | --- | --- |",
    ]
    for path in sorted(outdir.rglob("*")):
        relative = path.relative_to(outdir)
        if not path.is_file() or path.name in SKIP_ASSETS or relative.parts[0].startswith("_"):
            continue
        out.append(f"| `{relative}` | {path.stat().st_size:,} B | `{sha256_file(path)[:16]}…` |")

    out += [
        "",
        "完整雜湊見 `checksums.txt`。",
        "",
        "## 引用方式",
        "",
        "```bibtex",
        (outdir / "citation.bib").read_text(encoding="utf-8").strip(),
        "```",
        "",
        "`references.bib` 是本章引用的文獻，全部由 DOI 經 doi.org 取回官方 BibTeX，"
        "可直接匯入 Zotero 或 EndNote。",
        "",
        "## 建置環境",
        "",
        "| 項目 | 值 |",
        "| --- | --- |",
        f"| commit | `{args.commit}` |",
        f"| SOURCE_DATE_EPOCH | `{args.epoch}` |",
    ]
    out += [f"| {key} | `{value}` |" for key, value in sorted(toolchain.items())]
    out += [
        "",
        "PDF 以固定的 `SOURCE_DATE_EPOCH` 建置，同一個 commit 重跑應得到相同的檔案。"
        "`.docx` 是 zip 容器，位元層級一致不保證，這裡不宣稱做得到。",
        "",
        "## 已知缺口",
        "",
    ]
    soft = report.get("soft", [])
    if soft:
        out.append("檢查器抓到、但不足以擋下發布的問題。列出來是為了不讓它們消失在紀錄之外：")
        out.append("")
        out += [f"- {item}" for item in soft]
    else:
        out.append("本次檢查沒有留下未解決的軟缺口。")

    out += ["", "---", "", f"線上編輯版：{meta['hackmd_url']}　·　授權：{meta['license']}"]

    (outdir / "release-notes.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"release notes：{len(out)} 行")
