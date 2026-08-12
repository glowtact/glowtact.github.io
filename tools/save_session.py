"""Save Claude Code session transcripts so they survive a machine move.

Claude Code keeps transcripts outside the repository, under
~/.claude/projects/<slug>/<session-id>.jsonl, where <slug> is derived from
the working directory. They therefore do not travel with a git clone, and
they do not travel with materials/ either unless something puts them there.

This copies them into materials/_session/ -- which is untracked, so nothing
lands in this public repository, and which is already carried by
materials_sync.py -- and renders a readable Markdown version alongside the
raw JSONL.

    python tools/save_session.py            # the most recent session
    python tools/save_session.py --all      # every session for this project
    python tools/save_session.py --list     # show what is available

The raw .jsonl is what `claude --resume` reads; the .md is for humans and
for reading the history without any tooling at all.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil

ROOT = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
)
DEST = os.path.join(ROOT, "materials", "_session")


def slug(path: str) -> str:
    """Claude Code's project directory name for a given working directory."""
    for char in ":\\/.":
        path = path.replace(char, "-")
    return path


def matches_root(transcript: str) -> bool:
    """True if a transcript's records were recorded in this repository."""
    try:
        with open(transcript, encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                cwd = json.loads(line).get("cwd")
                if cwd:
                    return os.path.normpath(cwd) == ROOT
    except (OSError, json.JSONDecodeError):
        return False
    return False


def project_dir() -> str:
    """Locate this repository's transcript directory.

    The name is derived from the working directory, but rather than trust
    that derivation, fall back to reading the `cwd` recorded inside the
    transcripts themselves.
    """
    base = os.path.join(os.path.expanduser("~"), ".claude", "projects")
    guess = os.path.join(base, slug(ROOT))
    if os.path.isdir(guess):
        return guess
    if os.path.isdir(base):
        for name in sorted(os.listdir(base)):
            candidate = os.path.join(base, name)
            if not os.path.isdir(candidate):
                continue
            for entry in os.listdir(candidate):
                if entry.endswith(".jsonl") and matches_root(
                    os.path.join(candidate, entry)
                ):
                    return candidate
    return guess


def sessions() -> list[tuple[str, str, float, int]]:
    """(session_id, path, mtime, size) newest first."""
    source = project_dir()
    if not os.path.isdir(source):
        raise SystemExit(f"no transcripts found at {source}")
    found = []
    for name in os.listdir(source):
        if not name.endswith(".jsonl"):
            continue
        full = os.path.join(source, name)
        found.append((name[:-6], full, os.path.getmtime(full),
                      os.path.getsize(full)))
    if not found:
        raise SystemExit(f"no .jsonl transcripts in {source}")
    return sorted(found, key=lambda item: item[2], reverse=True)


def text_of(content: object) -> list[str]:
    """Assistant/user text blocks, with tool calls reduced to a marker."""
    if isinstance(content, str):
        return [content]
    if not isinstance(content, list):
        return []
    out = []
    for block in content:
        if not isinstance(block, dict):
            continue
        kind = block.get("type")
        if kind == "text" and block.get("text", "").strip():
            out.append(block["text"])
        elif kind == "tool_use":
            out.append(f"_[ran {block.get('name', 'tool')}]_")
    return out


def render(path: str, session_id: str) -> str:
    """Readable transcript: prompts and replies, without tool payloads."""
    sections: list[tuple[str, str, list[str]]] = []
    started = None
    skipped_tool_results = 0

    for raw in open(path, encoding="utf-8"):
        raw = raw.strip()
        if not raw:
            continue
        try:
            record = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if record.get("type") not in ("user", "assistant"):
            continue
        if record.get("isSidechain"):
            continue

        message = record.get("message")
        if not isinstance(message, dict):
            continue
        content = message.get("content")

        # A user record whose content is tool_result blocks is the harness
        # feeding output back, not the person typing.
        if record["type"] == "user" and isinstance(content, list):
            if any(isinstance(b, dict) and b.get("type") == "tool_result"
                   for b in content):
                skipped_tool_results += 1
                continue

        blocks = [b for b in text_of(content) if b.strip()]
        if not blocks:
            continue

        stamp = (record.get("timestamp") or "")[:19].replace("T", " ")
        started = started or stamp
        who = "You" if record["type"] == "user" else "Claude"
        # Consecutive records from the same speaker are one turn; a reply
        # interleaved with tool calls should not become ten headings.
        if sections and sections[-1][0] == who:
            sections[-1][2].extend(blocks)
        else:
            sections.append((who, stamp, list(blocks)))

    lines = [f"# Session {session_id}", ""]
    if started:
        lines.append(f"Started {started}.")
    lines += [
        f"Tool output omitted ({skipped_tool_results} exchanges); the raw "
        f"`{session_id}.jsonl` beside this file has everything.",
        "",
    ]
    for who, stamp, blocks in sections:
        lines.append(f"## {who}" + (f"  <sub>{stamp}</sub>" if stamp else ""))
        lines.append("")
        # Collapse a run of tool markers into a single line.
        merged: list[str] = []
        for block in blocks:
            is_marker = block.startswith("_[ran ") and block.endswith("]_")
            if (is_marker and merged and merged[-1].startswith("_[ran ")
                    and merged[-1].endswith("]_")):
                merged[-1] = merged[-1][:-2] + ", " + block[6:]
            else:
                merged.append(block)
        lines += ["\n\n".join(merged), ""]
    return "\n".join(lines) + "\n"


def save(session_id: str, path: str) -> None:
    os.makedirs(DEST, exist_ok=True)
    shutil.copy2(path, os.path.join(DEST, f"{session_id}.jsonl"))
    markdown = render(path, session_id)
    with open(os.path.join(DEST, f"{session_id}.md"), "w",
              encoding="utf-8", newline="\n") as handle:
        handle.write(markdown)
    size = os.path.getsize(path) / 1048576
    print(f"saved {session_id}  ({size:.1f} MiB raw, "
          f"{len(markdown) / 1024:.0f} KiB readable)")


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--all", action="store_true")
    group.add_argument("--list", action="store_true")
    group.add_argument("--session", help="a specific session id")
    args = parser.parse_args()

    available = sessions()
    if args.list:
        print(f"transcripts in {project_dir()}:")
        for session_id, _, _, size in available:
            print(f"  {session_id}  {size / 1048576:6.1f} MiB")
        return

    if args.session:
        chosen = [s for s in available if s[0] == args.session]
        if not chosen:
            raise SystemExit(f"no such session: {args.session}")
    elif args.all:
        chosen = available
    else:
        chosen = available[:1]

    for session_id, path, _, _ in chosen:
        save(session_id, path)
    print(f"-> {DEST}")


if __name__ == "__main__":
    main()
