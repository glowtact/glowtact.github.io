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
materials/                        451 files, 467 MiB
├── paper/
│   ├── paper.pdf                 the manuscript
│   ├── GlowTact-2026-08-14.pdf   a later revision; differs from paper.pdf,
│   │                             so both are kept
│   └── GlowTact-2026-09-27.pdf   the authored revision (2026-09-26 build),
│                                 served as /GlowTact.pdf since 2026-09-27
├── figures/                       15 files,  34 MiB
│   ├── teaser.png / .pdf          hero figure
│   ├── fingerprints.png / .pdf    fingerprint pressure series
│   ├── 3d_recon.png / .pdf        reconstruction overview
│   ├── glowtact_h.png             humanoid contact geometry
│   ├── data collection.png
│   ├── mechanism-contact-states.png   optical coupling, no-contact vs in-contact
│   ├── SNR.png                    Fig. 10, the sensitivity panels. The site
│                                  chart is digitized from this file by
│                                  design/tools/digitize_snr.py, which
│                                  therefore needs the materials tree to re-run
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
│                                  (there is no _session/ -- see below)
└── _archives/                      3 files,  38 MiB
    ├── single_meshes_gt.zip       redundant: identical to meshes/flat/
    ├── single_meshes_h.zip        redundant: identical to meshes/humanoid/
    └── session_20260728_010530.zip NOT redundant: also contains episode_000003,
                                    which is absent from the extracted tree
```

`MANIFEST.sha256` sits at the top of `materials/` and lists a SHA-256 for
every file. It is generated, and travels with the data.

**The Claude Code transcripts did not make the move.** Earlier revisions of
this document describe a `_session/` folder holding them; it is absent from
this copy, and absent from `materials.zip`, which was built before
`save_session.py` ran. Nothing else is missing -- `materials_check.py
--verify` passes on all 451 files -- but if you want the session history from
the old machine, it is still only on the old machine.

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
| `design/assets/images/fingerprints/press-1..5.jpg` | `~/tactile_data/glowtact/analysis/fingerprints/cropped/` tactile frames 000001, 000002, 000003, 000004, 000008 (the paper's three plus the lightest and hardest press of the same placement) |
| `design/assets/video/shear/*.mp4`, `design/assets/images/shear/*-poster.jpg` | `~/Desktop/glowtact_materials/shear_field/videos/original/` re-encoded H.264 CRF 20; posters cut at each object's `peak_frame` in `shear_field/params.json` (the colour-tuned set was retired 2026-09-27) |
| `design/assets/video/recon/*.mp4`, `design/assets/images/reconstruction/*` | `~/Desktop/glowtact_materials/gallery/gallery/<object>/` turntable GIFs and tactile frames, the paper's reconstruction parameters; `*-object.jpg` are the object photographs cropped from `materials/figures/3d_recon.png` (top row) and, for the Oreo, `slides/3d_recon.pptx` media image25 |
| `design/assets/images/reconstruction-overview.jpg` | `materials/figures/3d_recon.png` |
| `design/assets/images/contact-geometry.jpg` | `materials/figures/glowtact_h.png` |
| `design/assets/images/thread-mesh.png` | `materials/meshes/flat/glowtact_1_steep_01_screw_threads_mesh.png` |
| `design/assets/images/phillips-mesh.png` | `materials/meshes/flat/glowtact_1_steep_04_philips_head_mesh.png` |
| `design/assets/images/ball-array-mesh.png` | `materials/meshes/flat/glowtact_1_steep_03_cali_balls_mesh.png` |
| `design/assets/video/mms-contact.mp4` | `materials/video/mms_gt.mp4` |
| `design/assets/images/mms-contact-poster.jpg` | midpoint frame of the video above |

## Why it is not in git

This repository is `glowtact.github.io` — GitHub Pages builds and serves it
from `main:/`. Committing 467 MiB of sources would mean:

- every clone downloads 467 MiB to get a 17 MiB website;
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
site, and `tools/materials_sync.py` carries the sources.

**On the old machine**, first capture anything that lives outside the repo
and outside `materials/` — chiefly the Claude Code session history, which
Claude Code stores in your user profile:

```powershell
python tools/save_session.py
```

That writes the transcripts into `materials/_session/` so they travel with
everything else; see `materials/_session/README.md`. The project's decisions
and open items are in [`docs/HANDOFF.md`](docs/HANDOFF.md), which git already
carries.

Then send `materials/` to somewhere both machines can reach — an external
drive, a network share, or a cloud-synced folder. All three are just paths,
so they work the same way:

```powershell
python tools/materials_sync.py push E:\glowtact-materials
```

**On the new machine**, two commands and you are working:

```powershell
git clone git@github.com:glowtact/glowtact.github.io.git
cd glowtact.github.io
python tools/materials_sync.py pull E:\glowtact-materials
```

The clone brings the site, `design/`, and the tooling — about 17 MiB. The
pull brings the 467 MiB of sources.

The location is saved to `.materials-remote` (untracked, per-machine) on
first use, so from then on it is just `push` or `pull` with no argument.
`GLOWTACT_MATERIALS_REMOTE` works too if you would rather set it in the
environment.

### What the sync does for you

- **Refreshes the manifest** before pushing, so the checksums always match
  what is being sent.
- **Mirrors** with `robocopy /MIR` on Windows (`rsync -a --delete`
  elsewhere), which retries and resumes — worth having for a 76 MiB video
  over a flaky link. Re-running only moves what changed; a no-op sync takes
  seconds.
- **Verifies the receiving end** by re-hashing every file against the
  manifest, and exits non-zero if anything is missing, changed, or extra. A
  single flipped byte anywhere in the 467 MiB fails the run. Silent transfer
  corruption is exactly what you want to hear about now rather than the day
  you need the file.
- **Refuses to destroy things.** Mirroring deletes files at the receiving
  end that are absent from the sending end. Any run that would delete
  something stops and lists what, unless you pass `--force`; and it will not
  mirror onto a non-empty folder that does not already look like a materials
  tree, so a mistyped path cannot wipe your documents.

Check either side at any time:

```powershell
python tools/materials_sync.py status
```

### Keeping both machines current

`push` is safe to repeat, so it can run on a schedule and keep the shared
copy fresh; the other machine then only ever needs `pull`. To have Windows
do it nightly at 19:00:

```powershell
schtasks /create /tn "GlowTact materials push" /sc daily /st 19:00 /tr "python C:\path\to\glowtact.github.io\tools\materials_sync.py push"
```

The scheduled run takes no location argument, so it uses the one saved in
`.materials-remote`; run `push` by hand once first to establish it. The
tools resolve paths from their own location, so the task works whatever
directory it starts in. Drop it again with
`schtasks /delete /tn "GlowTact materials push" /f`.

### Confirm the site still builds

```powershell
python design/verify.py
python design/tools/publish.py
python -m http.server 4173
```

Then open `http://127.0.0.1:4173/`. Note the server runs from the
repository root, not from `design/`, so that the published root page
resolves its `design/assets/...` references the way GitHub Pages does.

### If the two machines cannot share a path

Mirror to a drive or share and move that, or replace the mirror step with
`rclone`/`scp` and keep the verification:

```powershell
rclone sync materials remote:glowtact-materials
# then, on the new machine, after rclone sync back:
python tools/materials_check.py --verify
```

`materials_check.py` takes `--root PATH` to check any copy of the tree, so
the verification works regardless of how the bytes got there.

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

## Shear clips (re-sourced 2026-09-26)

The five DAT/03 clips and their posters under `design/assets/video/shear/`
and `design/assets/images/shear/` are derived from a **second, newer material
tree** that this document does not yet describe: `~/glowtact_stuff`, packed
2026-09-25 (894 files, 763 MiB, with a README per folder). Its
`05_shear_field/` is the current marker-free shear package (session
`20260809_022437`, Farnebäck flow with LCN + CLAHE); the clips previously in
the site came from the superseded pre-2026-08-19 package and showed a
different tracker's field. Reconciling `~/glowtact_stuff` with `materials/`
is an open item.

| Committed asset | Source | How |
|---|---|---|
| `design/assets/video/shear/<name>.mp4` (5) | `~/glowtact_stuff/05_shear_field/videos/color_tuned/<name>.mp4` | `ffmpeg -an -c:v libx264 -profile:v high -pix_fmt yuv420p -crf 20 -preset slow -movflags +faststart` (three of the five masters were MPEG-4 Simple Profile) |
| `design/assets/images/shear/<name>-poster.jpg` (5) | the re-encoded clip above | one frame at `peak_frame / fps` from `05_shear_field/params.json` (peak contact), `-q:v 3` |

The numbers the module quotes come from `05_shear_field/params.json`
(`preprocess_stats`, `objects[].peak_contact_area`) and its `README.md`;
`design/data/results.json` records the exact key for each. The folder's
`eval/metrics.json` is an earlier tracker-comparison run and is not quoted.

## Own-sensor pass (2026-09-26)

| Committed asset | Source | Recipe |
|---|---|---|
| `design/assets/video/sensitivity/screw-m2.mp4` | `~/glowtact_stuff/03_sensitivity/videos/screw_1.mp4` (the M2×6 screw, 0.2 g / 1.96 mN; main deck slide 6) | `ffmpeg -an -c:v libx264 -profile:v high -pix_fmt yuv420p -crf 20 -preset slow -movflags +faststart` |
| `design/assets/images/sensitivity/screw-m2-poster.jpg` | frame at 3.5 s of the clip above | `-frames:v 1 -q:v 3` |
| `design/assets/images/sensitivity/fig9-{mm,m6-nut,m5-screw}-{raw,diff,diff3}.jpg` (9) | `~/glowtact_stuff/01_decks/light_objects.pptx` slide 2, GlowTact half: rows y≈1.6 / 3.7 / 5.0 = M&M (image3/2/4), M6 nut (image31/30/32), M5×6 (image5/6/7); identified by content against `02_figures/light_objects.pdf` | Pillow, JPEG q88, ≤ 760 px |
| `design/assets/images/forms/flat-exploded.jpg` | `GlowTact_main_deck.pptx` slide 5 `image16.png` (Flat exploded CAD) | Pillow, JPEG q88, ≤ 1200 px |
| `design/assets/images/forms/tip-exploded.jpg` | slide 5 `image14.png` (dome fingertip exploded CAD) | same |
| `design/assets/images/forms/tips-in-hand.jpg` | slide 5 `image10.png` (two fingertip sensors held) | same |
| removed | `design/assets/images/sensitivity/{mm,m8-nut,m5-screw}-{glowtact,gelsight}.jpg` | superseded by the Fig. 9 triplets; the site no longer shows GelSight |
| unused, kept | `design/data/snr-curves.json`, `design/tools/digitize_snr.py` | the SNR chart left the page on 2026-09-26; the digitisation stays as a documented derivation |
