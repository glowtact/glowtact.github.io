"""Checksum manifest for the untracked materials/ tree.

materials/ holds ~464 MB of raw source material that is deliberately not in
git, so git cannot tell you whether a copy of it is complete. This writes and
verifies a SHA-256 manifest instead, which is what makes moving the tree to
another machine trustworthy.

    python tools/materials_check.py --write     # before transferring
    python tools/materials_check.py --verify    # on the new machine

The manifest lives at materials/MANIFEST.sha256 so it travels with the data.
It is excluded from its own checksums.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys

ROOT = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
)
MATERIALS = os.path.join(ROOT, "materials")
MANIFEST = os.path.join(MATERIALS, "MANIFEST.sha256")
MANIFEST_NAME = "MANIFEST.sha256"


def digest(path: str) -> str:
    sha = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            sha.update(chunk)
    return sha.hexdigest()


def walk() -> list[str]:
    """Every file under materials/, as sorted forward-slash relative paths."""
    found = []
    for dirpath, _, filenames in os.walk(MATERIALS):
        for name in filenames:
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, MATERIALS).replace(os.sep, "/")
            if rel == MANIFEST_NAME:
                continue
            found.append(rel)
    return sorted(found)


def read_manifest() -> dict[str, str]:
    entries = {}
    with open(MANIFEST, encoding="utf-8") as handle:
        for line in handle:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            checksum, _, rel = line.partition("  ")
            entries[rel] = checksum
    return entries


def write() -> None:
    files = walk()
    total = 0
    lines = []
    for index, rel in enumerate(files, 1):
        full = os.path.join(MATERIALS, rel.replace("/", os.sep))
        total += os.path.getsize(full)
        lines.append(f"{digest(full)}  {rel}")
        if index % 50 == 0 or index == len(files):
            print(f"  hashed {index}/{len(files)}", end="\r", flush=True)
    print()
    with open(MANIFEST, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(
            f"# GlowTact materials manifest\n"
            f"# {len(files)} files, {total / 1048576:.1f} MiB\n"
            f"# Regenerate with: python tools/materials_check.py --write\n"
        )
        handle.write("\n".join(lines) + "\n")
    print(f"wrote {MANIFEST_NAME}: {len(files)} files, "
          f"{total / 1048576:.1f} MiB")


def verify() -> None:
    if not os.path.exists(MANIFEST):
        raise SystemExit(
            f"no {MANIFEST_NAME}; run --write on the source machine first"
        )
    expected = read_manifest()
    actual = set(walk())

    missing = sorted(set(expected) - actual)
    extra = sorted(actual - set(expected))
    shared = sorted(set(expected) & actual)
    changed = []
    for index, rel in enumerate(shared, 1):
        full = os.path.join(MATERIALS, rel.replace("/", os.sep))
        if digest(full) != expected[rel]:
            changed.append(rel)
        if index % 50 == 0 or index == len(shared):
            print(f"  checked {index}/{len(expected)}", end="\r", flush=True)
    print()

    for label, items in (("MISSING", missing), ("CHANGED", changed),
                         ("UNTRACKED", extra)):
        for item in items:
            print(f"{label}: {item}", file=sys.stderr)

    if missing or changed:
        raise SystemExit(
            f"materials incomplete: {len(missing)} missing, "
            f"{len(changed)} changed"
        )
    note = f", {len(extra)} extra file(s) not in manifest" if extra else ""
    print(f"materials OK: {len(expected)} files verified{note}")


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--verify", action="store_true")
    args = parser.parse_args()

    if not os.path.isdir(MATERIALS):
        raise SystemExit("no materials/ directory here; see MATERIALS.md")
    write() if args.write else verify()


if __name__ == "__main__":
    main()
