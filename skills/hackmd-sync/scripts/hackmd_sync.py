#!/usr/bin/env python3
"""Pull and push HackMD notes with deterministic image-link conversion."""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
from pathlib import Path


DEFAULT_RAW_BASE = "https://raw.githubusercontent.com/htlin222/agent-in-ebm/main/figures/"
DEFAULT_RELATIVE_PREFIX = "../../figures/"


def read_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip('"').strip("'")
        values[key.strip()] = value
    return values


def cli_environment() -> dict[str, str]:
    skill_root = Path(__file__).resolve().parents[1]
    values = read_dotenv(skill_root / ".env")
    token = values.get("HACKMD_API") or os.environ.get("HMD_API_ACCESS_TOKEN")
    if not token:
        raise SystemExit("HACKMD_API is missing from the skill .env and HMD_API_ACCESS_TOKEN is unset")
    environment = os.environ.copy()
    environment["HMD_API_ACCESS_TOKEN"] = token
    return environment


def note_id(args: argparse.Namespace) -> str:
    value = args.note_id or os.environ.get("HACKMD_NOTE_ID")
    if not value:
        raise SystemExit("provide --note-id or set HACKMD_NOTE_ID")
    return value


def run_cli(arguments: list[str], environment: dict[str, str]) -> str:
    result = subprocess.run(
        ["hackmd-cli", *arguments],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown hackmd-cli error"
        raise SystemExit(f"hackmd-cli failed: {detail}")
    return result.stdout


def normalize_pull(content: str, raw_base: str, relative_prefix: str) -> str:
    return content.replace(raw_base.rstrip("/") + "/", relative_prefix)


def normalize_push(content: str, raw_base: str, relative_prefix: str) -> str:
    return content.replace(relative_prefix, raw_base.rstrip("/") + "/")


def sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def pull(args: argparse.Namespace) -> None:
    environment = cli_environment()
    remote = run_cli(["export", "--noteId", note_id(args)], environment)
    output = Path(args.snapshot or f"{args.file}.cloud.md")
    if output.exists() and not args.force:
        raise SystemExit(f"refusing to overwrite existing snapshot: {output}; use --force after inspecting it")
    normalized = normalize_pull(remote, args.raw_base, args.relative_prefix)
    output.write_text(normalized, encoding="utf-8")
    print(f"pulled cloud note to {output}")
    print(f"cloud sha256: {sha256(remote)}")


def push(args: argparse.Namespace) -> None:
    environment = cli_environment()
    source = Path(args.file)
    content = source.read_text(encoding="utf-8")
    upload = normalize_push(content, args.raw_base, args.relative_prefix).rstrip("\n")
    expected_remote = upload + "\n"
    run_cli(
        ["notes", "update", "--noteId", note_id(args), "--content", upload],
        environment,
    )
    remote = run_cli(["export", "--noteId", note_id(args)], environment)
    if remote != expected_remote:
        raise SystemExit(
            "remote content differs from upload "
            f"(upload {sha256(expected_remote)}, remote {sha256(remote)})"
        )
    print(f"pushed and verified {source}")
    print(f"remote sha256: {sha256(remote)}")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    subparsers = result.add_subparsers(dest="command", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--note-id")
    common.add_argument("--file", required=True)
    common.add_argument("--raw-base", default=DEFAULT_RAW_BASE)
    common.add_argument("--relative-prefix", default=DEFAULT_RELATIVE_PREFIX)

    pull_parser = subparsers.add_parser("pull", parents=[common])
    pull_parser.add_argument("--snapshot")
    pull_parser.add_argument("--force", action="store_true")
    pull_parser.set_defaults(function=pull)

    push_parser = subparsers.add_parser("push", parents=[common])
    push_parser.set_defaults(function=push)
    return result


if __name__ == "__main__":
    arguments = parser().parse_args()
    arguments.function(arguments)
