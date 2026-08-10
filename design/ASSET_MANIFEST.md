# GlowTact Website Asset Manifest

## Rules
- Prefer original high-resolution exports over PDF screenshots.
- Preserve axes, labels, colors, and scientific meaning.
- Keep GlowTact amber and GelSight Mini blue.
- Use SVG for diagrams when practical.
- Use WebP/AVIF/PNG for images.
- Do not generate fake experimental images or data.

## Folders
```text
public/
├── images/
│   ├── hero/
│   ├── mechanism/
│   ├── form-factors/
│   ├── lightweight/
│   ├── sensitivity/
│   ├── reconstruction/
│   └── force-estimation/
├── videos/
├── data/
└── paper/
```

## Hero
```text
public/images/hero/leap-hand-screw.webp
public/images/hero/tactile-screw-top.webp
public/images/hero/tactile-screw-bottom.webp
public/images/hero/social-preview.png
```

Optional:
```text
public/videos/leap-hand-grasp.mp4
public/videos/leap-hand-grasp.webm
```

## Mechanism
```text
public/images/mechanism/paper-mechanism-reference.png
```

Optional SVG pieces:
```text
membrane.svg
textured-gel.svg
acrylic.svg
camera.svg
light-source.svg
indenter.svg
```

## Form Factors

Flat:
```text
flat-assembled.webp
flat-exploded.webp
flat-fingerprint-03N.webp
flat-fingerprint-10N.webp
flat-fingerprint-20N.webp
```

Omnidirectional:
```text
omni-assembled.webp
omni-exploded.webp
omni-tactile-example.webp
```

Humanoid:
```text
humanoid-components.webp
humanoid-assembled.webp
humanoid-quarter-tactile.webp
```

## Lightweight Objects
Folders:
```text
public/images/lightweight/mm/
public/images/lightweight/m6-nut/
public/images/lightweight/m5x6/
```

Each folder:
```text
object.webp
glowtact-raw.webp
glowtact-diff.webp
glowtact-enhanced.webp
gelsight-raw.webp
gelsight-diff.webp
gelsight-enhanced.webp
```

Metadata:
```text
public/data/lightweight-objects.json
```

## Sensitivity
```text
public/data/sensitivity.json
```

Suggested schema:
```json
{
  "metadata": {
    "numProbes": 10,
    "forceRangeN": [0, 20],
    "samplesPerSensor": 13116,
    "snrThreshold": 3
  },
  "responseCurves": {},
  "snrCurves": {},
  "probeCurves": [],
  "minimumDetectableForceN": {
    "glowtact": [],
    "gelsight": []
  }
}
```

## Reconstruction
Folders:
```text
phillips/
m3/
m2_5/
m2/
m1_5/
m1/
ball-array/
```

Each:
```text
object.webp
raw-tactile.webp
reconstruction.webp
```

Metadata:
```text
public/data/reconstruction.json
```

## Force Estimation
```text
public/data/force-estimation.json
```

Populate from the final source table, not by reading values from an image.

## Paper
```text
public/paper/glowtact.pdf
public/data/bibtex.txt
```

## Missing Assets
When an asset is missing:
- show a labeled placeholder
- add a TODO
- do not invent a scientific replacement

## Implemented Review Assets

The three-concept review build uses the following deliberate derivatives. Source
files remain unchanged.

Source paths are relative to the repository root and live in the untracked
`materials/` tree; see `../MATERIALS.md` for its layout and for how to obtain
it on a new machine.

| Review asset | Source |
|---|---|
| `assets/images/hero-teaser.jpg` | `materials/figures/teaser.png` |
| `assets/images/fingerprint-pressure.jpg` | `materials/figures/fingerprints.png` |
| `assets/images/reconstruction-overview.jpg` | `materials/figures/3d_recon.png` |
| `assets/images/contact-geometry.jpg` | `materials/figures/glowtact_h.png` |
| `assets/images/thread-mesh.png` | `materials/meshes/flat/glowtact_1_steep_01_screw_threads_mesh.png` |
| `assets/images/phillips-mesh.png` | `materials/meshes/flat/glowtact_1_steep_04_philips_head_mesh.png` |
| `assets/images/ball-array-mesh.png` | `materials/meshes/flat/glowtact_1_steep_03_cali_balls_mesh.png` |
| `assets/images/mms-contact-poster.jpg` | Midpoint frame extracted from `assets/video/mms-contact.mp4` |
| `assets/video/mms-contact.mp4` | `materials/video/mms_gt.mp4` |

The JPEG derivatives use quality 88 and a maximum dimension of 2200 pixels.
The video and mesh PNGs are byte-for-byte copies of the supplied source files.

Concept 03 uses `assets/images/hero-teaser.jpg` as its first-screen paper teaser.
The figure is displayed without cropping, and its original scientific
annotations are preserved.
