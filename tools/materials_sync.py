"""One-command mirroring of the untracked materials/ tree.

git carries the website; it cannot carry the 464 MiB of sources. This does,
to and from any path -- an external drive, a network share, or a
cloud-synced folder (OneDrive/Drive/Dropbox are just directories on disk, so
all three work the same way here).

    python tools/materials_sync.py push E:\\glowtact-materials
    python tools/materials_sync.py pull E:\\glowtact-materials
    python tools/materials_sync.py status

The location is remembered in .materials-remote after the first run, so
later syncs are just `push` or `pull`. It can also come from the
GLOWTACT_MATERIALS_REMOTE environment variable.

push refreshes the manifest, mirrors, then verifies the *destination* by
re-hashing it; pull mirrors, then verifies the local copy. Either way the
transfer is checked rather than assumed.

Mirroring deletes files at the receiving end that are absent from the
sending end -- that is what makes it a mirror. Any run that would delete
something stops and shows you what, unless you pass --force.

For a genuinely remote machine, mirror to a share or drive and sync that,
or swap the mirror step for rclone/scp; the verify step is transport-blind.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys

import materials_check as check

ROOT = check.ROOT
MATERIALS = check.MATERIALS
CONFIG = os.path.join(ROOT, ".materials-remote")
# A tree with none of these is probably not a materials/ copy, and
# mirroring onto it would delete whatever is actually there.
LANDMARKS = (check.MANIFEST_NAME, "figures", "captures", "meshes", "video")


def remembered() -> str | None:
    if os.path.exists(CONFIG):
        value = open(CONFIG, encoding="utf-8").read().strip()
        if value:
            return value
    return os.environ.get("GLOWTACT_MATERIALS_REMOTE") or None


def remember(path: str) -> None:
    with open(CONFIG, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(path + "\n")


def resolve(explicit: str | None) -> str:
    path = explicit or remembered()
    if not path:
        raise SystemExit(
            "no remote location given and none remembered.\n"
            "Pass one once and it is saved:\n"
            "  python tools/materials_sync.py push E:\\glowtact-materials"
        )
    return os.path.abspath(os.path.expandvars(os.path.expanduser(path)))


def looks_like_materials(path: str) -> bool:
    if not os.path.isdir(path):
        return False
    return any(os.path.exists(os.path.join(path, name)) for name in LANDMARKS)


def is_empty(path: str) -> bool:
    return not os.path.isdir(path) or not os.listdir(path)


def deletions(src: str, dst: str) -> list[str]:
    """Files present at dst but not at src, which a mirror would remove."""
    if not os.path.isdir(dst):
        return []
    src_files = set(check.walk(src))
    return sorted(set(check.walk(dst)) - src_files)


def mirror(src: str, dst: str) -> None:
    os.makedirs(dst, exist_ok=True)
    if os.name == "nt":
        # robocopy retries and resumes, which matters for a 76 MiB video
        # over a flaky link. Exit codes below 8 are success variants.
        result = subprocess.run([
            "robocopy", src, dst, "/MIR", "/R:3", "/W:5",
            "/NFL", "/NDL", "/NJH", "/NP",
        ])
        if result.returncode >= 8:
            raise SystemExit(f"robocopy failed (exit {result.returncode})")
        return
    if shutil.which("rsync"):
        result = subprocess.run(
            ["rsync", "-a", "--delete", f"{src}{os.sep}", dst]
        )
        if result.returncode != 0:
            raise SystemExit(f"rsync failed (exit {result.returncode})")
        return
    # Portable fallback: copy everything, then prune what the source lost.
    shutil.copytree(src, dst, dirs_exist_ok=True)
    for rel in deletions(src, dst):
        os.remove(os.path.join(dst, rel.replace("/", os.sep)))


def guard(src: str, dst: str, label: str, force: bool) -> None:
    if not looks_like_materials(src):
        raise SystemExit(
            f"{src} does not look like a materials tree "
            f"(expected one of: {', '.join(LANDMARKS)})"
        )
    if not is_empty(dst) and not looks_like_materials(dst):
        raise SystemExit(
            f"refusing to mirror onto {dst}: it is not empty and does not "
            f"look like a materials tree. Mirroring would delete its "
            f"contents. Point at a dedicated folder, or clear it first."
        )
    pending = deletions(src, dst)
    if pending and not force:
        print(f"{label} would delete {len(pending)} file(s) at {dst}:",
              file=sys.stderr)
        for rel in pending[:20]:
            print(f"  {rel}", file=sys.stderr)
        if len(pending) > 20:
            print(f"  ... and {len(pending) - 20} more", file=sys.stderr)
        raise SystemExit("stopped; re-run with --force if that is intended")


def summarize(root: str) -> str:
    if not os.path.isdir(root):
        return "absent"
    files = check.walk(root)
    total = sum(
        os.path.getsize(os.path.join(root, rel.replace("/", os.sep)))
        for rel in files
    )
    return f"{len(files)} files, {total / 1048576:.1f} MiB"


def push(args: argparse.Namespace) -> None:
    dst = resolve(args.location)
    if not os.path.isdir(MATERIALS):
        raise SystemExit("no local materials/ to push; see MATERIALS.md")
    print(f"push  {MATERIALS}\n   -> {dst}")
    print("refreshing manifest...")
    check.write(MATERIALS, quiet=True)
    guard(MATERIALS, dst, "push", args.force)
    mirror(MATERIALS, dst)
    if not args.no_verify:
        print("verifying destination...")
        check.verify(dst, quiet=True)
    # Only a location that worked is worth remembering.
    if args.location:
        remember(args.location)


def pull(args: argparse.Namespace) -> None:
    src = resolve(args.location)
    print(f"pull  {src}\n   -> {MATERIALS}")
    guard(src, MATERIALS, "pull", args.force)
    mirror(src, MATERIALS)
    if not args.no_verify:
        print("verifying local copy...")
        check.verify(MATERIALS, quiet=True)
    if args.location:
        remember(args.location)


def status(args: argparse.Namespace) -> None:
    remote = remembered()
    print(f"local   materials/  {summarize(MATERIALS)}")
    if not remote:
        print("remote  (none remembered)")
        return
    resolved = os.path.abspath(os.path.expandvars(os.path.expanduser(remote)))
    print(f"remote  {resolved}  {summarize(resolved)}")
    if os.path.isdir(resolved) and os.path.isdir(MATERIALS):
        out = deletions(MATERIALS, resolved)
        back = deletions(resolved, MATERIALS)
        print(f"        {len(back)} file(s) only on remote, "
              f"{len(out)} only local")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="mirror materials/ to or from a drive, share, or "
                    "cloud-synced folder",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    for name, handler, help_text in (
        ("push", push, "send local materials/ to the remote location"),
        ("pull", pull, "bring materials/ here from the remote location"),
    ):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("location", nargs="?",
                       help="path to mirror with; remembered after first use")
        p.add_argument("--force", action="store_true",
                       help="proceed even if files would be deleted")
        p.add_argument("--no-verify", action="store_true")
        p.set_defaults(handler=handler)
    p = sub.add_parser("status", help="show local and remote state")
    p.set_defaults(handler=status)

    args = parser.parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
