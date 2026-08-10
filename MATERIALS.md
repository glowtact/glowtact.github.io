# GlowTact Source Materials

Raw source material for the paper and the website lives in `materials/` at
the repository root. It is **not tracked by git** — see [Why it is not in
git](#why-it-is-not-in-git) — so cloning this repository gives you the site
but not the sources. [Moving to another machine](#moving-to-another-machine)
covers how to bring them across.

Everything the published website needs is already committed under
`design/assets/`. You only need `materials/` to re-derive those assets, to
edit figures and slides, or to work on the paper.

## Layout

```text
materials/                        449 files, 464 MiB
├── paper/
│   └── paper.pdf                 the manuscript
├── figures/                       14 files,  33 MiB
│   ├── teaser.png / .pdf          hero figure
│   ├── fingerprints.png / .pdf    fingerprint pressure series
│   ├── 3d_recon.png / .pdf        reconstruction overview
│   ├── glowtact_h.png             humanoid contact geometry
│   ├── data collection.png
│   ├── mechanism-contact-states.png   optical coupling, no-contact vs in-contact
│   └── ... (side view, exploded view, gelsight_and_9dtact, humanoid finger)
├── slides/                        14 files, 233 MiB
│   └── *.pptx sources plus GlowTact_video.mp4 (76 MiB, the rendered talk video)
├── meshes/                        48 files, 2.5 MiB
│   ├── flat/                      24 reconstructed meshes, flat sensor
│   └── humanoid/                  24 reconstructed meshes, humanoid finger
│                                  (4 viewing angles x 6 objects each)
├── captures/                     321 files, 105 MiB
│   ├── 3d-recon-pad/              tactile/diff/enhanced frames + cropped/ + index.csv
│   └── sensitive-pad/             same structure, sensitivity experiments
├── video/                         48 files,  51 MiB
│   ├── mms_gt.mp4                 M&M contact clip (source of the site's video)
│   ├── gt_mms.mp4                 a different, shorter cut of the same subject
│   ├── Glowtact.prproj            Premiere project
│   ├── premiere-autosave/         Premiere auto-save copies
│   └── session_20260728_010530/   6 recorded episodes; per episode:
│                                  streams/gelsight, gelsight_diff, hx711_force
└── _archives/                      3 files,  38 MiB
    ├── single_meshes_gt.zip       redundant: identical to meshes/flat/
    ├── single_meshes_h.zip        redundant: identical to meshes/humanoid/
    └── session_20260728_010530.zip NOT redundant: also contains episode_000003,
                                    which is absent from the extracted tree
```

`MANIFEST.sha256` sits at the top of `materials/` and lists a SHA-256 for
every file. It is generated, and travels with the data.

### What changed from the older layout

The material used to sit in four separate top-level folders with some
awkward nesting. Nothing was renamed except where noted:

| Was | Now |
|---|---|
| `glowtact_images/glowtact_images/3d_recon_pad/` | `materials/captures/3d-recon-pad/` |
| `glowtact_images/glowtact_images/sensitive_pad/` | `materials/captures/sensitive-pad/` |
| `glowtact_materials/figures/` | `materials/figures/` |
| `glowtact_materials/slides/` | `materials/slides/` |
| `glowtact_materials/single_meshes_gt/single_meshes/` | `materials/meshes/flat/` |
| `glowtact_materials/single_meshes_h/single_meshes/` | `materials/meshes/humanoid/` |
| `glowtact_materials/glowtact_video/session_.../session_.../` | `materials/video/session_20260728_010530/` |
| `glowtact_materials/glowtact_video/Adobe Premiere Pro Auto-Save/` | `materials/video/premiere-autosave/` |
| `glowtact_mechanism/image.png` | `materials/figures/mechanism-contact-states.png` |
| `mms_gt.mp4`, `paper.pdf` (repo root) | `materials/video/`, `materials/paper/` |
| `*.zip` scattered among their extracted copies | `materials/_archives/` |

Five Microsoft Office lock files (`~$*.pptx`, 165 bytes each) were deleted;
they are temp files left by an open PowerPoint, not content. No other file
was removed, and no image, slide, mesh, capture, or video was modified.

## Derived website assets

The committed assets under `design/assets/` are derivatives of the files
above. JPEG derivatives use quality 88 and a maximum dimension of 2200 px;
the mesh PNGs and the video are byte-for-byte copies.

| Committed asset | Source |
|---|---|
| `design/assets/images/hero-teaser.jpg` | `materials/figures/teaser.png` |
| `design/assets/images/fingerprint-pressure.jpg` | `materials/figures/fingerprints.png` |
| `design/assets/images/reconstruction-overview.jpg` | `materials/figures/3d_recon.png` |
| `design/assets/images/contact-geometry.jpg` | `materials/figures/glowtact_h.png` |
| `design/assets/images/thread-mesh.png` | `materials/meshes/flat/glowtact_1_steep_01_screw_threads_mesh.png` |
| `design/assets/images/phillips-mesh.png` | `materials/meshes/flat/glowtact_1_steep_04_philips_head_mesh.png` |
| `design/assets/images/ball-array-mesh.png` | `materials/meshes/flat/glowtact_1_steep_03_cali_balls_mesh.png` |
| `design/assets/video/mms-contact.mp4` | `materials/video/mms_gt.mp4` |
| `design/assets/images/mms-contact-poster.jpg` | midpoint frame of the video above |

## Why it is not in git

This repository is `glowtact.github.io` — GitHub Pages builds and serves it
from `main:/`. Committing 464 MiB of sources would mean:

- every clone downloads 464 MiB to get a 17 MiB website;
- GitHub warns above 50 MiB per file, and `slides/GlowTact_video.mp4` is
  76 MiB;
- the sources would count against the Pages 1 GiB site limit;
- removing them later requires rewriting history, not just a delete commit.

The sources are inputs, not deliverables. `design/assets/` holds the small
set of derivatives the site actually serves, and those *are* tracked.

If you later decide the sources should be versioned, put them in a separate
repository or use Git LFS — do not add them to this one.

## Moving to another machine

The website and the materials travel by different routes: git carries the
site, and a copy carries the sources.

**1. On the new machine, clone the repository.**

```powershell
git clone git@github.com:glowtact/glowtact.github.io.git
cd glowtact.github.io
```

That gives you the full site, `design/`, and the tooling — about 17 MiB.

**2. On the old machine, refresh the manifest.**

```powershell
python tools/materials_check.py --write
```

This rewrites `materials/MANIFEST.sha256` so it matches what you are about
to copy.

**3. Copy `materials/` across.** Any of these work; pick by what you have.

*External drive or network share* — `robocopy` mirrors and retries, which
matters for a 76 MiB video over a flaky link:

```powershell
robocopy materials E:\glowtact-materials /MIR /R:3 /W:5
```

Then on the new machine, into the freshly cloned repository:

```powershell
robocopy E:\glowtact-materials materials /MIR /R:3 /W:5
```

*Single archive* — one file is easier to hand off through cloud storage.
Store-only (`-mx0`) is worth it: the bulk is already-compressed PNG, MP4,
PPTX, and ZIP, so compression buys little and costs a lot of time:

```powershell
7z a -mx0 glowtact-materials.7z materials
```

Unpack it inside the cloned repository so the tree lands at `materials/`.

*Directly between machines on one network:*

```powershell
scp -r materials user@newmachine:/path/to/glowtact.github.io/
```

**4. On the new machine, verify the copy.**

```powershell
python tools/materials_check.py --verify
```

It re-hashes all 449 files and names anything missing, changed, or extra,
exiting non-zero if the tree is incomplete. A silent transfer failure on a
464 MiB copy is exactly the kind of thing you want to catch before you need
the file, not after.

**5. Confirm the site still builds.**

```powershell
python design/verify.py
python design/tools/publish.py
python -m http.server 4173
```

Then open `http://127.0.0.1:4173/`. Note the server runs from the
repository root, not from `design/`, so that the published root page
resolves its `design/assets/...` references the way GitHub Pages does.

### What you also need on the new machine

- **Python 3** with `playwright` if you intend to run `design/browser_check.py`
  or `design/tools/release.py` (`pip install playwright && playwright install
  chromium`). `design/verify.py` and `tools/materials_check.py` need only the
  standard library.
- **An SSH key registered with GitHub**, since `origin` uses `git@github.com`.
  Otherwise re-point it at HTTPS with `git remote set-url`.
- **PowerPoint and Premiere Pro** to open `slides/` and `video/Glowtact.prproj`.
  The Premiere project references media by path and will ask you to relink
  after the move.
