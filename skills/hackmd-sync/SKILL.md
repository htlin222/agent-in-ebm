---
name: hackmd-sync
description: "Deterministic HackMD note synchronization for editing Markdown: pull the cloud note before any edit, normalize GitHub raw image links to local paths, push the finished file back, and verify the remote content exactly. Use whenever a HackMD note is being edited or published."
---

# HackMD synchronization

Use this skill whenever a Markdown file is edited from, or published to, HackMD.

## Mandatory workflow

1. Pull the current note before reading or editing the local manuscript:

   ```bash
   python3 /path/to/hackmd-sync/scripts/hackmd_sync.py pull \
     --note-id NOTE_ID \
     --file docs/manuscript/chapter-full.md
   ```

   This writes a cloud snapshot beside the file as `.cloud.md`. Compare it with the working file and reconcile any difference before editing. Do not silently overwrite local work.

2. Edit the local Markdown source. Keep image references as repository-relative paths such as `../../figures/fig03-freedom-map.png`.

3. Push only after validation:

   ```bash
   python3 /path/to/hackmd-sync/scripts/hackmd_sync.py push \
     --note-id NOTE_ID \
     --file docs/manuscript/chapter-full.md
   ```

   The command converts repository-relative figure paths to GitHub raw URLs, updates the note, exports it again, and fails unless the exported content exactly matches the upload.

## Credentials and image links

- Load `HACKMD_API` from `.env` in this skill directory. The script also accepts `HMD_API_ACCESS_TOKEN` from the environment as a fallback.
- Keep the skill `.env` permission-restricted (`chmod 600`) and never print its contents or token.
- The repository `.gitignore` must ignore `/skills/hackmd-sync/.env`.
- The default image base is `https://raw.githubusercontent.com/htlin222/agent-in-ebm/main/figures/`. Override it only when the repository and branch differ.
- Pull converts that raw base back to `../../figures/` for local editing; push performs the inverse conversion.

## Script location

Use `scripts/hackmd_sync.py` from the installed skill directory. The repository copy is `skills/hackmd-sync`; the global installed copy is normally `/Users/htlin/.agents/skills/hackmd-sync`.
