#!/usr/bin/env python3
"""prepare / figures / bib 三個產出步驟。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
from pathlib import Path

from common import (
    RELEASE,
    RE_FIG_ALT,
    RE_H1,
    die,
    fetch,
    is_remote,
    load_json,
    parse_manuscript,
    read_manuscript,
    resolve_image,
    sha256_file,
    sort_key,
)


# -------------------------------------------------------------- prepare


def prepare(args: argparse.Namespace) -> None:
    md_path = Path(args.md).resolve()
    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    lines = read_manuscript(md_path)
    parsed = parse_manuscript(lines)
    meta = load_json(RELEASE / "meta.json")

    # 遠端圖片先抓下來，pandoc 那一步就完全離線，也才有 sha256 可以記。
    remote_map: dict[str, str] = {}
    for image in parsed["images"]:
        target = image["target"]
        if not is_remote(target) or target in remote_map:
            continue
        assets = outdir / "_remote"
        assets.mkdir(parents=True, exist_ok=True)
        try:
            payload = fetch(target, accept=None)
        except RuntimeError as error:
            die(f"遠端圖片抓不下來，拒絕發布缺圖的文件：{error}")
        local = assets / f"remote-{hashlib.sha256(target.encode()).hexdigest()[:12]}{Path(target).suffix or '.png'}"
        local.write_bytes(payload)
        remote_map[target] = str(local)
        print(f"遠端圖片已內嵌：{target} → {local.name} sha256={sha256_file(local)}")

    # 拿掉 H1 與緊接的分隔線；標題改由 metadata 帶，PDF/DOCX 才不會出現兩次。
    body = list(lines)
    if body and RE_H1.match(body[0]):
        body = body[1:]
        while body and not body[0].strip():
            body = body[1:]
        if body and body[0].strip() == "---":
            body = body[1:]

    rewritten = []
    for raw in body:
        line = raw
        for url, local in remote_map.items():
            line = line.replace(f"]({url})", f"]({local})")
        rewritten.append(line)

    (outdir / "chapter.pandoc.md").write_text("\n".join(rewritten) + "\n", encoding="utf-8")

    # 這裡刻意不寫 lang：pandoc 一看到 lang 就會替 XeLaTeX 掛上 polyglossia，
    # 而 polyglossia 的中文支援在不同 TeX Live 版本間並不一致。lang 只在 docx 那一步補上。
    metadata = {
        "title": parsed["title"],
        "author": meta["authors"],
        "date": args.date,
        "subject": f"{meta['repo']} @ {args.tag}",
        "toc-title": "目次",
        **meta["pdf"],
    }
    (outdir / "metadata.yaml").write_text(
        "---\n" + "".join(_yaml_line(key, value) for key, value in metadata.items()) + "---\n",
        encoding="utf-8",
    )
    print(f"pandoc 來源：{outdir / 'chapter.pandoc.md'}（{len(rewritten)} 行，{len(remote_map)} 張遠端圖已內嵌）")


def _yaml_line(key: str, value) -> str:
    if isinstance(value, list):
        return f"{key}:\n" + "".join(f"  - {json.dumps(item, ensure_ascii=False)}\n" for item in value)
    return f"{key}: {json.dumps(value, ensure_ascii=False)}\n"


# -------------------------------------------------------------- figures


def figures(args: argparse.Namespace) -> None:
    md_path = Path(args.md).resolve()
    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    parsed = parse_manuscript(read_manuscript(md_path))
    appendix = {row["number"]: row for row in parsed["appendix_figures"]}

    manifest: list[dict] = []
    for image in parsed["images"]:
        alt_match = RE_FIG_ALT.match(image["alt"].strip())
        if not alt_match or is_remote(image["target"]):
            continue
        number = alt_match.group(1)
        row = appendix.get(number)
        if row is None:
            die(f"圖 {number} 沒有附錄 D 的登記，無法決定匯出檔名")

        # 檔名沿用原始碼的 basename（底線一律正規化成連字號），
        # 讀者從資產檔名就找得回附錄 D 的重建指令。
        stem = Path(row["source"]).stem.replace("_", "-")
        referenced = resolve_image(md_path, image["target"])
        exports = []
        for sibling in sorted(referenced.parent.glob(f"{referenced.stem}.*")):
            if sibling.suffix.lower() not in {".png", ".pdf", ".svg"}:
                continue
            destination = outdir / f"{stem}{sibling.suffix.lower()}"
            shutil.copy2(sibling, destination)
            os.utime(destination, (args.epoch, args.epoch))
            exports.append(
                {"file": destination.name, "sha256": sha256_file(destination), "bytes": destination.stat().st_size}
            )

        manifest.append(
            {
                "number": number,
                "name": row["name"],
                "caption": parsed["captions"].get(number, ""),
                "section": row["section"],
                "source": row["source"],
                "rebuild": row["rebuild"],
                "used_in_text": image["target"],
                "exports": exports,
            }
        )

    rows = [
        "# 圖表清單",
        "",
        f"共 {len(manifest)} 張圖。檔名沿用原始碼的 basename，可以直接對回「重建指令」那一欄自行重畫。",
        "",
    ]
    for entry in manifest:
        rows += [f"## 圖 {entry['number']}　{entry['name']}", "", f"- 出現於：{entry['section']}"]
        if entry["caption"]:
            rows.append(f"- 圖說：{entry['caption']}")
        rows += [f"- 原始碼：`{entry['source']}`", f"- 重建指令：`{entry['rebuild']}`"]
        rows += [f"- `{e['file']}`　{e['bytes']:,} bytes　sha256 `{e['sha256']}`" for e in entry["exports"]]
        rows.append("")

    (outdir / "FIGURES.md").write_text("\n".join(rows), encoding="utf-8")
    (outdir / "figures.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"匯出 {len(manifest)} 張圖，共 {sum(len(e['exports']) for e in manifest)} 個檔案")


# ------------------------------------------------------------------ bib


def bib(args: argparse.Namespace) -> None:
    md_path = Path(args.md).resolve()
    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    cache = Path(args.cache).resolve()
    cache.mkdir(parents=True, exist_ok=True)

    parsed = parse_manuscript(read_manuscript(md_path))
    meta = load_json(RELEASE / "meta.json")
    refs = load_json(RELEASE / "refs.json")["refs"]

    entries: dict[str, str] = {}
    order: list[str] = []
    failures: list[str] = []

    for key in sorted(refs, key=sort_key):
        entry = refs[key]
        citekey = entry["citekey"]
        if citekey in entries:
            continue
        order.append(citekey)

        if entry.get("literal"):
            entries[citekey] = entry["literal"].strip()
            continue

        doi = entry["doi"]
        cached = cache / f"{hashlib.sha256(doi.encode()).hexdigest()}.bib"
        if cached.exists():
            raw = cached.read_text(encoding="utf-8")
        else:
            try:
                raw = fetch(f"https://doi.org/{doi}", accept="application/x-bibtex; charset=utf-8").decode("utf-8")
            except RuntimeError as error:
                failures.append(f"[^{key}] {doi}：{error}")
                order.pop()
                continue
            cached.write_text(raw, encoding="utf-8")
        entries[citekey] = _rewrite_citekey(raw.strip(), citekey)
        print(f"[^{key}] {doi} → {citekey}")

    if failures:
        die(f"{len(failures)} 筆 DOI 取不到 BibTeX，拒絕發布不完整的參考文獻庫", failures)

    header = [
        "% references.bib — 本章引用的文獻",
        "% 來源：release/refs.json 登記的 DOI，經 https://doi.org content negotiation 取得官方 BibTeX",
        "% 不由正文解析、不由模型生成；DOI 取不到就讓 build 失敗",
        f"% {meta['repo']} @ {args.commit}",
        f"% 正文 {len(parsed['footnote_definitions'])} 個註腳，去重後 {len(order)} 筆文獻",
        "",
    ]
    (outdir / "references.bib").write_text(
        "\n".join(header) + "\n" + "\n\n".join(entries[key] for key in order) + "\n", encoding="utf-8"
    )

    citation = [
        f"@misc{{{meta['citekey']},",
        f"  author       = {{{meta['author_bibtex']}}},",
        f"  title        = {{{{{parsed['title']}}}}},",
        f"  year         = {{{args.date[:4]}}},",
        f"  month        = {{{args.date[5:7]}}},",
        f"  version      = {{{args.tag}}},",
        f"  howpublished = {{{meta['repo_url']}/releases/tag/{args.tag}}},",
        f"  url          = {{{meta['repo_url']}}},",
        f"  note         = {{commit {args.commit}；線上版 {meta['hackmd_url']}；授權 {meta['license']}}}",
        "}",
    ]
    (outdir / "citation.bib").write_text("\n".join(citation) + "\n", encoding="utf-8")
    print(f"references.bib：{len(order)} 筆；citation.bib：1 筆")


def _rewrite_citekey(bibtex: str, citekey: str) -> str:
    """換掉出版社給的 citekey，讓引用鍵在各版之間保持穩定。"""
    return re.sub(r"^(@\w+\s*\{)[^,]*,", lambda match: f"{match.group(1)}{citekey},", bibtex, count=1)
