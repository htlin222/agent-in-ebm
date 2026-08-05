#!/usr/bin/env python3
"""check：發布前的確定性驗證。

硬錯誤讓 build 停住（缺圖、註腳對不上、引用未登記）；軟缺口只記錄，
最後會原樣寫進 release notes 的「已知缺口」——本章的主張是無法證明的事要具名，
所以這裡不讓它們靜靜消失。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import (
    RELEASE,
    REPO,
    RE_FIG_ALT,
    die,
    is_remote,
    load_json,
    parse_manuscript,
    read_manuscript,
    resolve_image,
    sort_key,
    statistics,
    warn,
)


def run(args: argparse.Namespace) -> None:
    md_path = Path(args.md).resolve()
    lines = read_manuscript(md_path)
    parsed = parse_manuscript(lines)
    refs = load_json(RELEASE / "refs.json")["refs"]

    hard: list[str] = []
    soft: list[str] = []

    if not parsed["title"]:
        hard.append("正文第一行不是 `# 標題`，無法決定文件標題")

    defined = parsed["footnote_definitions"]
    duplicates = sorted({key for key in defined if defined.count(key) > 1}, key=sort_key)
    if duplicates:
        hard.append(f"註腳定義重複：{'、'.join(duplicates)}")

    defined_set = set(defined)
    referenced_set = set(parsed["footnote_references"])
    for key in sorted(referenced_set - defined_set, key=sort_key):
        hard.append(f"正文引用了 [^{key}] 但沒有對應的註腳定義")
    for key in sorted(defined_set - referenced_set, key=sort_key):
        soft.append(f"註腳 [^{key}] 有定義但正文沒有引用")

    refs_set = set(refs)
    for key in sorted(defined_set - refs_set, key=sort_key):
        hard.append(f"註腳 [^{key}] 不在 release/refs.json 裡，引用來源未登記")
    for key in sorted(refs_set - defined_set, key=sort_key):
        hard.append(f"release/refs.json 有 [^{key}] 但正文已無此註腳，請一併移除")

    for key in sorted(refs, key=sort_key):
        entry = refs[key]
        if not entry.get("doi") and not entry.get("literal"):
            hard.append(f"refs.json 的 [^{key}] 既沒有 doi 也沒有 literal")
        if entry.get("duplicate_of"):
            soft.append(f"註腳 [^{key}] 與 [^{entry['duplicate_of']}] 指向同一筆文獻，references.bib 會去重")

    numbered = {row["number"] for row in parsed["appendix_figures"]}
    for image in parsed["images"]:
        target = image["target"]
        if is_remote(target):
            soft.append(f"第 {image['line']} 行的圖是遠端連結、沒有圖號，也不在版控裡：{target}")
            continue
        if not resolve_image(md_path, target).exists():
            hard.append(f"第 {image['line']} 行的圖找不到：{target}")
            continue
        alt_match = RE_FIG_ALT.match(image["alt"].strip())
        if not alt_match:
            soft.append(f"第 {image['line']} 行的圖沒有「圖N」形式的標號，alt 是「{image['alt']}」")
        elif alt_match.group(1) not in numbered:
            hard.append(f"圖 {alt_match.group(1)} 沒有登記在附錄 D 的圖表原始碼表")

    for row in parsed["appendix_figures"]:
        if not (REPO / row["source"]).exists():
            hard.append(f"附錄 D 的圖 {row['number']} 原始碼不存在：{row['source']}")

    stats = statistics(lines, parsed)
    print(f"標題：{parsed['title']}")
    print(
        f"統計：{stats['cjk_characters']} 中文字／{stats['sections']} 節／"
        f"{stats['figures']} 圖／{stats['footnotes']} 註腳"
    )

    for line in soft:
        warn(line)

    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps({"soft": soft, "stats": stats}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    if hard:
        die(f"正文檢查未通過（{len(hard)} 項）", hard)
    print(f"檢查通過；{len(soft)} 項軟缺口已記錄，會出現在 release notes")
