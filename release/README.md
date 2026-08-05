# 章節發布流程

`docs/manuscript/chapter-full.md` 推上 `main` 就會觸發
[`.github/workflows/release-chapter.yml`](../.github/workflows/release-chapter.yml)，
建置並發一版 GitHub Release。

## 發布內容

| 資產 | 說明 |
| --- | --- |
| `chapter-full.md` | 正文原檔，逐位元組與 repo 相同 |
| `chapter-full.pdf` | XeLaTeX + xeCJK 排版，Noto Serif CJK TC |
| `chapter-full.docx` | 校對語言為 zh-TW |
| `citation.bib` | 引用這一版的 `@misc`，含 tag 與 commit |
| `references.bib` | 本章 33 筆文獻，由 DOI 經 doi.org 取回官方 BibTeX |
| `figures/*.png` `.pdf` `.svg` | 獨立圖檔，檔名沿用附錄 D 的原始碼 basename |
| `figures/FIGURES.md` | 圖號、圖說、原始碼、重建指令、sha256 |
| `figures/figures.json` | 同上，機器可讀 |
| `figures.zip` | 上述圖檔打包 |
| `checksums.txt` | 所有資產的 sha256 |

## 版本命名

`chapter-<UTC 日期>-<7 碼 commit>`，例如 `chapter-2026.08.06-35f15fe`。
完全由 commit 決定，不需要維護版本檔；同一天推多次也不會撞 tag。

tag 已存在時 build 會直接失敗。要重發同一個 commit，用 workflow_dispatch
並勾選 `force`，流程會刪掉舊 release 與 tag 再重建。

## 確定性

- 版本、日期、`SOURCE_DATE_EPOCH` 全部由 commit 推導，不看 build 當下的時間。
- 圖檔 mtime 與 zip（`-X`）都釘在 `SOURCE_DATE_EPOCH`。
- pandoc 版本寫死在 workflow 的 `PANDOC_VERSION`。`.deb` 的 sha256 每次都會印出來並寫進
  release notes；雜湊已釘在 `PANDOC_SHA256`，不符就擋下來；換 pandoc 版本時要一起更新。
- 引用只從 `refs.json` 登記的 DOI 取，不從正文解析、不由模型生成。DOI 查詢結果按
  `refs.json` 的雜湊快取。
- PDF 在同一個 commit 下應可重現；`.docx` 是 zip 容器，位元層級一致不保證，
  release notes 裡也照實這麼寫。

## 檢查器

`build.py check` 分兩級。**硬錯誤**讓 build 停住：

- 正文第一行不是 `# 標題`
- 註腳定義重複，或引用了不存在的註腳
- 註腳與 `release/refs.json` 對不上（任一邊多或少都算）
- `refs.json` 的條目既沒有 `doi` 也沒有 `literal`
- 正文的圖檔不存在，或圖號沒登記在附錄 D
- 附錄 D 登記的原始碼檔案不存在

**軟缺口**只記錄，並原樣寫進 release notes 的「已知缺口」：

- 註腳有定義但正文沒引用
- 兩個註腳指向同一筆文獻
- 圖是遠端連結、沒有圖號，或不在版控裡

產物端另有一道驗收：PDF 頁數、DOCX 的 zip 結構、圖檔數量與正文對不對得上。

## 本機重跑

不需要任何 pip 套件，Python 標準函式庫就夠。PDF 那一步要 pandoc + XeLaTeX + Noto CJK。

```bash
EPOCH=$(git log -1 --format=%ct)
COMMIT=$(git rev-parse HEAD)
DATE=$(TZ=UTC date -u -d "@$EPOCH" +%Y-%m-%d)   # macOS: date -u -r "$EPOCH" +%Y-%m-%d
TAG="chapter-$(TZ=UTC date -u -d "@$EPOCH" +%Y.%m.%d)-$(git rev-parse --short=7 HEAD)"

python3 release/build.py check   --report dist/_build/check.json
python3 release/build.py prepare --outdir dist/_build --tag "$TAG" --date "$DATE"
python3 release/build.py figures --outdir dist/figures --epoch "$EPOCH"
python3 release/build.py bib     --outdir dist --cache .cache/crossref \
                               --tag "$TAG" --date "$DATE" --commit "$COMMIT"
python3 release/build.py notes   --outdir dist --commit "$COMMIT" --epoch "$EPOCH" \
                               --report dist/_build/check.json
```

## 改正文之後要記得的事

新增或刪掉一個註腳，就要同步改 `release/refs.json`，否則 `check` 會擋下來。
這是刻意的：引用的真相來源是 `refs.json`，不是正文，也不是模型補出來的作者名。

新增一張圖，要同時做三件事：把圖檔提交進 `figures/`、在正文用 `![圖N](...)` 引用、
在附錄 D 的表格加一列登記原始碼與重建指令。少任何一項，`check` 都會失敗。

## 檔案

| 檔案 | 用途 |
| --- | --- |
| `build.py` | CLI 入口 |
| `common.py` | 正文解析與共用工具 |
| `steps_check.py` | `check` |
| `steps_build.py` | `prepare` / `figures` / `bib` |
| `steps_notes.py` | `notes` |
| `meta.json` | 作者、授權、字型等固定 metadata（標題除外，標題唯一來源是正文 H1） |
| `refs.json` | 引用真相來源：註腳號 → citekey + DOI |
