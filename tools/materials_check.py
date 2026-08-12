"""Checksum manifest for the untracked materials/ tree.

materials/ holds ~464 MB of raw source material that is deliberately not in
git, so git cannot tell you whether a copy of it is complete. This writes and
verifies a SHA-256 manifest instead, which is what makes moving the tree to
another machine trustworthy.

    python tools/materials_check.py --write     # before transferring
    python tools/materials_check.py --verify    # on the new machine

The manifest lives at materials/MANIFEST.sha256 so it travels with the data.
It is excluded from its own checksums.

`--root PATH` points either operation at some other copy of the tree -- the
one on the external drive, the share, or the new machine -- which is how
materials_sync.py checks both ends of a transfer.
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
MANIFEST_NAME = "MANIFEST.sha256"


def digest(path: str) -> str:
    sha = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            sha.update(chunk)
    return sha.hexdigest()


def walk(root: str) -> list[str]:
    """Every file under root, as sorted forward-slash relative paths."""
    found = []
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            if rel == MANIFEST_NAME:
                continue
            found.append(rel)
    return sorted(found)


def read_manifest(root: str) -> dict[str, str]:
    entries = {}
    with open(os.path.join(root, MANIFEST_NAME), encoding="utf-8") as handle:
        for line in handle:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            checksum, _, rel = line.partition("  ")
            entries[rel] = checksum
    return entries


def write(root: str, quiet: bool = False) -> None:
    files = walk(root)
    total = 0
    lines = []
    for index, rel in enumerate(files, 1):
        full = os.path.join(root, rel.replace("/", os.sep))
        total += os.path.getsize(full)
        lines.append(f"{digest(full)}  {rel}")
        if not quiet and (index % 50 == 0 or index == len(files)):
            print(f"  hashed {index}/{len(files)}", end="\r", flush=True)
    if not quiet:
        print()
    with open(os.path.join(root, MANIFEST_NAME), "w",
              encoding="utf-8", newline="\n") as handle:
        handle.write(
            f"# GlowTact materials manifest\n"
            f"# {len(files)} files, {total / 1048576:.1f} MiB\n"
            f"# Regenerate with: python tools/materials_check.py --write\n"
        )
        handle.write("\n".join(lines) + "\n")
    print(f"wrote {MANIFEST_NAME}: {len(files)} files, "
          f"{total / 1048576:.1f} MiB")


def verify(root: str, quiet: bool = False) -> None:
    if not os.path.exists(os.path.join(root, MANIFEST_NAME)):
        raise SystemExit(
            f"no {MANIFEST_NAME} in {root}; run --write on the source first"
        )
    expected = read_manifest(root)
    actual = set(walk(root))

    missing = sorted(set(expected) - actual)
    extra = sorted(actual - set(expected))
    shared = sorted(set(expected) & actual)
    changed = []
    for index, rel in enumerate(shared, 1):
        full = os.path.join(root, rel.replace("/", os.sep))
        if digest(full) != expected[rel]:
            changed.append(rel)
        if not quiet and (index % 50 == 0 or index == len(shared)):
            print(f"  checked {index}/{len(expected)}", end="\r", flush=True)
    if not quiet:
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
    parser.add_argument(
        "--root", default=MATERIALS,
        help="materials tree to operate on (default: ./materials)",
    )
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        raise SystemExit(f"no such directory: {root}; see MATERIALS.md")
    if args.write:
        write(root, args.quiet)
    else:
        verify(root, args.quiet)


if __name__ == "__main__":
    main()
