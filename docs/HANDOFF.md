# Handoff — 2026-08-11

Written to resume this project on a different machine. Covers where things
stand, what was decided and why, and what is still open. For the material
tree and how to bring it across, see [`../MATERIALS.md`](../MATERIALS.md).

## Where things stand

**The website is live.** `https://glowtact.github.io/` serves concept-03
("Signal Chamber") and returns 200. Before this session it returned 404:
GitHub Pages builds from `main:/`, but every page lived under `design/`, so
only `/design/concept-03/` resolved.

**The sources are consolidated.** 449 files / 464.3 MiB of figures, slides,
captures, meshes, and video now live in one untracked `materials/` tree with
a checksum manifest, instead of four top-level folders with doubled nesting.

Commits from this session, oldest first:

| Commit | What |
|---|---|
| `bec6f00` | `feat(site)`: publish concept-03 at the repository root |
| `fce691e` | `docs(materials)`: consolidate raw sources into `materials/` |
| `07622a0` | `feat(materials)`: one-command sync to automate the migration |

## Resuming on the new machine

```powershell
git clone git@github.com:glowtact/glowtact.github.io.git
cd glowtact.github.io
python tools/materials_sync.py pull <location>   # or copy materials/ by hand
python tools/materials_check.py --verify         # do this either way
python -m http.server 4173
```

Then open `http://127.0.0.1:4173/`. Serve from the **repository root**, not
from `design/` — the published root page resolves `design/assets/...`, and
serving from `design/` will 404 those.

You will also want Python 3 with `playwright` (`pip install playwright &&
playwright install chromium`) for `design/browser_check.py` and
`design/tools/release.py`. `design/verify.py` and both `tools/` scripts need
only the standard library. `origin` uses SSH, so either register a key or
re-point it with `git remote set-url`.

## How the site is built

The published root is **generated, not hand-written**. `design/tools/publish.py`
reads `design/concept-03/index.html` and rewrites its relative references to
resolve from the repository root; only `index.html` is generated, while CSS,
JS, images, and video are referenced where they already live under `design/`.
Nothing is duplicated, so the published page cannot drift from the reviewed
one. The generated file carries a DO-NOT-EDIT banner.

**To change the site, edit `design/concept-03/` and re-run the tool** — or
just use `design/tools/release.py`, which stamps, verifies, runs the browser
checks, publishes, commits, and pushes in one step.

`publish.py` link-checks every local reference and refuses to write a root
page that would ship a broken link.

## Decisions worth not re-litigating

**`materials/` stays out of git.** This repo is served by GitHub Pages.
Committing 464 MiB of sources would make every clone pull 464 MiB for a
17 MiB site, trip GitHub's 50 MiB per-file warning on the 76 MiB talk video,
count against the Pages 1 GiB limit, and need a history rewrite to undo. The
derivatives the site actually serves are tracked under `design/assets/`. If
these ever need versioning, use a separate repo or Git LFS — not this one.

**Because git cannot verify what it does not track**, `materials/` carries a
SHA-256 manifest instead. `tools/materials_check.py --verify` re-hashes every
file and exits non-zero on anything missing, changed, or extra. This was
confirmed by test — a single flipped byte in the 464 MiB fails the run — not
assumed. Run it after *any* transfer, tool-assisted or manual.

**Mirroring guards against deletion.** `materials_sync.py` stops and lists
what it would remove unless `--force` is passed, and refuses to mirror onto a
non-empty folder that does not look like a materials tree, so a mistyped path
cannot wipe an unrelated directory.

**The mesh zips are redundant; the session zip is not.**
`_archives/single_meshes_{gt,h}.zip` are byte-identical to `meshes/flat/` and
`meshes/humanoid/`. `_archives/session_20260728_010530.zip` also contains an
`episode_000003` that is absent from the extracted tree — do not delete it
assuming symmetry.

## Open items

1. **Review-build chrome is public.** The published root still shows the
   `CONCEPT 03` badge, the tab title "GlowTact — Signal Chamber", and footer
   links into `/design/`. That is internal review vocabulary now facing the
   public. Fixing it is a rewrite-rule change in `publish.py`, not a content
   edit.
2. **Local `.git` was 461 MB on the old machine**, from ~290
   `refs/omnara-checkpoints/*` refs that snapshotted the materials. The
   pushed history is a healthy 17.5 MiB, so a fresh clone is unaffected —
   this only mattered if the project folder were copied wholesale. Prune the
   refs and `git gc` if it reappears.
3. **1.9 MB of redundant mesh zips** can be dropped from `_archives/` (see
   above for the one to keep).
4. **Premiere relinking.** `materials/video/Glowtact.prproj` references media
   by absolute path and will ask to relink after any move.

## Session transcript

The full Claude Code transcript for the session that produced the above is
saved at `materials/_session/` and travels with the material tree. It is
deliberately **not** committed: this repository is public, and the transcript
contains local paths and environment detail. See the README in that folder
for how to resume the session itself.
