#!/usr/bin/env bash
# 本地 chapter-full.md → HackMD（單向推送）。圖片改寫成 GitHub raw URL。
# 用法：./sync-hackmd.sh
set -euo pipefail
cd "$(dirname "$0")"
export HMD_API_ACCESS_TOKEN="$(grep -E '^HACKMD_API=' .env | head -1 | cut -d= -f2- | tr -d '"'"'"' ')"
NOTE_ID="8cqZK3E6Sqy7U92Pl2aIpg"
RAW="https://raw.githubusercontent.com/htlin222/agent-in-ebm/main/figures/"
TMP="$(mktemp)"
sed "s#\.\./\.\./figures/#${RAW}#g" docs/manuscript/chapter-full.md > "$TMP"
hackmd-cli notes update --noteId "$NOTE_ID" --content "$(cat "$TMP")"
rm -f "$TMP"
echo "已推送到 https://hackmd.io/${NOTE_ID}"
