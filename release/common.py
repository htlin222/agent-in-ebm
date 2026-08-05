#!/usr/bin/env python3
"""正文解析與共用工具。只用標準函式庫，不裝任何 pip 套件。"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RELEASE = REPO / "release"

RE_IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)\)")
RE_FN_DEF = re.compile(r"^\[\^([^\]]+)\]:")
RE_FN_REF = re.compile(r"\[\^([^\]]+)\]")
RE_CAPTION = re.compile(r"〔圖\s*(\d+)[：:]\s*(.+?)〕")
RE_H1 = re.compile(r"^#\s+(.+?)\s*$")
RE_H2 = re.compile(r"^##\s+(.+?)\s*$")
RE_FIG_ALT = re.compile(r"^圖\s*(\d+)$")
RE_CJK = re.compile(r"[㐀-䶿一-鿿豈-﫿]")

USER_AGENT = "agent-in-ebm-build/1 (+https://github.com/htlin222/agent-in-ebm)"


def die(message: str, details: list[str] | None = None) -> None:
    print(f"::error::{message}", file=sys.stderr)
    for line in details or []:
        print(f"  - {line}", file=sys.stderr)
    raise SystemExit(1)


def warn(message: str) -> None:
    print(f"::warning::{message}", file=sys.stderr)


def sort_key(key: str):
    return (0, int(key)) if key.isdigit() else (1, key)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_manuscript(path: Path) -> list[str]:
    if not path.exists():
        die(f"找不到正文：{path}")
    return path.read_text(encoding="utf-8").splitlines()


def resolve_image(md_path: Path, target: str) -> Path:
    return (md_path.parent / target).resolve()


def is_remote(target: str) -> bool:
    return target.startswith(("http://", "https://"))


def fetch(url: str, accept: str | None, attempts: int = 4) -> bytes:
    """帶指數退避的 GET。全部失敗就拋出，由呼叫端決定是否讓 build 停住。"""
    last: Exception | None = None
    for attempt in range(attempts):
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        if accept:
            request.add_header("Accept", accept)
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                return response.read()
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            last = error
            if attempt < attempts - 1:
                time.sleep(2**attempt)
    raise RuntimeError(f"{url} 取不到：{last}")


def git(*args: str) -> str:
    result = subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else ""


def parse_manuscript(lines: list[str]) -> dict:
    """把正文拆成後續每個子命令共用的結構。"""
    title = ""
    if lines and RE_H1.match(lines[0]):
        title = RE_H1.match(lines[0]).group(1)

    footnote_definitions: list[str] = []
    footnote_references: list[str] = []
    images: list[dict] = []
    sections: list[dict] = []
    captions: dict[str, str] = {}
    appendix_figures: list[dict] = []
    in_appendix_d = False

    for number, raw in enumerate(lines, start=1):
        heading = RE_H2.match(raw)
        if heading:
            sections.append({"line": number, "title": heading.group(1)})

        if raw.startswith("### 附錄 D"):
            in_appendix_d = True
        elif in_appendix_d and (raw.startswith("## ") or raw.startswith("### ") or raw.strip() == "---"):
            in_appendix_d = False

        definition = RE_FN_DEF.match(raw)
        if definition:
            footnote_definitions.append(definition.group(1))
        else:
            footnote_references.extend(RE_FN_REF.findall(raw))

        for alt, target in RE_IMAGE.findall(raw):
            images.append({"line": number, "alt": alt, "target": target})

        for figure_number, text in RE_CAPTION.findall(raw):
            captions[figure_number] = text.strip()

        if in_appendix_d and raw.startswith("|"):
            cells = [cell.strip() for cell in raw.strip().strip("|").split("|")]
            if len(cells) >= 4 and cells[0][:1].isdigit():
                figure_number, _, name = cells[0].partition(" ")
                appendix_figures.append(
                    {
                        "number": figure_number.strip(),
                        "name": name.strip(),
                        "section": cells[1].strip(),
                        "source": cells[2].strip().strip("`"),
                        "rebuild": cells[3].strip().strip("`"),
                    }
                )

    return {
        "title": title,
        "footnote_definitions": footnote_definitions,
        "footnote_references": footnote_references,
        "images": images,
        "sections": sections,
        "captions": captions,
        "appendix_figures": appendix_figures,
    }


def statistics(lines: list[str], parsed: dict) -> dict:
    body = "\n".join(lines)
    return {
        "cjk_characters": len(RE_CJK.findall(body)),
        "characters": len(body),
        "lines": len(lines),
        "sections": len(parsed["sections"]),
        "footnotes": len(parsed["footnote_definitions"]),
        "figures": len(parsed["images"]),
    }
