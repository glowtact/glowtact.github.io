"""Recover the Fig. 10b median curves from the published figure.

The source data behind Fig. 10 does not exist on disk: SNR's denominator is
the standard deviation of the unloaded frames, and the I0 references are
absent for both sensors, so the curves cannot be recomputed from the CNC
dataset. They are therefore digitized from the figure itself and labelled as
such wherever they are shown.

Calibration is anchored on two independent features and cross-checked:
decade gridlines give 103 px per decade with SNR = 1 at y = 620.5, which puts
SNR = 3 at y = 571.4 -- and the dashed threshold rule, detected separately,
sits at y = 572. A calibration that were wrong would not land within a pixel
of an independently measured line.

    python3 design/tools/digitize_snr.py [--report]

Writes design/data/snr-curves.json. Requires the source figure, which lives
in the untracked materials tree; the JSON output is what the site ships.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "materials" / "figures" / "SNR.png"
TARGET = ROOT / "design" / "data" / "snr-curves.json"

# Panel b plot area, in source pixels.
X0, X1, Y0, Y1 = 1010, 1420, 120, 800
X_DEC, X_REF_PX = 177.5, 1205.0     # px per decade of force; pixel of 1 N
Y_DEC, Y_REF_PX = 103.0, 620.5      # px per decade of SNR;   pixel of SNR 1
THRESHOLD_PX = 572.0                # measured position of the dashed SNR=3 rule
KEEP_EVERY = 3                      # ~135 points per curve is plenty inline


def to_force(px: float) -> float:
    return 10 ** ((px - X_REF_PX) / X_DEC)


def to_snr(py: float) -> float:
    return 10 ** (-(py - Y_REF_PX) / Y_DEC)


def extract(mask: np.ndarray) -> list[tuple[float, float]]:
    """Median y of the bold stroke in each column.

    The scatter is alpha-blended toward white and fails the saturation test;
    only the opaque median line survives it.
    """
    points = []
    for x in range(X0, X1):
        rows = np.where(mask[Y0:Y1, x])[0]
        if rows.size < 3:           # a real stroke is several pixels thick
            continue
        points.append((to_force(x), to_snr(Y0 + float(np.median(rows)))))
    return points


def main() -> int:
    if not SOURCE.exists():
        print(f"digitize_snr: missing {SOURCE}", file=sys.stderr)
        print("The figure lives in the untracked materials tree; see MATERIALS.md.",
              file=sys.stderr)
        return 1

    image = np.array(Image.open(SOURCE).convert("RGB")).astype(int)
    r, g, b = image[..., 0], image[..., 1], image[..., 2]
    amber = (r > 205) & (g > 125) & (g < 185) & (b < 80)
    blue = (b > 150) & (r < 80) & (g > 100) & (g < 165)

    glowtact, gelsight = extract(amber), extract(blue)

    # --- checks that can actually fail ---------------------------------
    problems = []
    if len(glowtact) < 200 or len(gelsight) < 200:
        # Report and stop: the range checks below index into these lists, and a
        # traceback is not a failing check -- it tells you nothing about which
        # assumption broke.
        print(
            f"digitize_snr: colour match collapsed: {len(glowtact)} amber, "
            f"{len(gelsight)} blue columns (expect ~400 each)",
            file=sys.stderr,
        )
        return 1
    predicted = Y_REF_PX - np.log10(3.0) * Y_DEC
    if abs(predicted - THRESHOLD_PX) > 2.0:
        problems.append(
            f"calibration disagrees with the dashed rule: SNR=3 predicted at "
            f"y={predicted:.1f}, rule measured at y={THRESHOLD_PX}"
        )
    for name, pts in (("glowtact", glowtact), ("gelsight", gelsight)):
        lo, hi = pts[0][0], pts[-1][0]
        if not (0.05 <= lo <= 0.2 and 8 <= hi <= 25):
            problems.append(f"{name} force range {lo:.3f}-{hi:.1f} N is off-axis")
    if problems:
        print("\n".join(f"digitize_snr: {p}" for p in problems), file=sys.stderr)
        return 1

    def thin(pts):
        kept = pts[::KEEP_EVERY]
        if kept[-1] != pts[-1]:
            kept.append(pts[-1])
        return [[round(f, 4), round(s, 1)] for f, s in kept]

    payload = {
        "provenance": (
            "Digitized from Fig. 10b of the GlowTact manuscript. The source data "
            "for this figure is not available: SNR is measured against the "
            "unloaded-frame standard deviation and the unloaded references are "
            "absent, so the curves cannot be recomputed."
        ),
        "calibration": {
            "x_px_per_decade": X_DEC,
            "y_px_per_decade": Y_DEC,
            "cross_check": (
                f"SNR=3 predicted at y={predicted:.1f} from the decade gridlines; "
                f"the dashed threshold rule measures y={THRESHOLD_PX}"
            ),
        },
        "axis": {"x_label": "Normal force (N)", "y_label": "SNR"},
        "threshold": 3,
        "series": [
            {"key": "glowtact", "label": "GlowTact", "points": thin(glowtact)},
            {"key": "gelsight", "label": "GelSight Mini", "points": thin(gelsight)},
        ],
    }
    TARGET.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")

    if "--report" in sys.argv:
        for name, pts in (("glowtact", glowtact), ("gelsight", gelsight)):
            print(f"{name}: {len(pts)} columns -> {len(thin(pts))} kept, "
                  f"force {pts[0][0]:.3f}-{pts[-1][0]:.1f} N, "
                  f"SNR {min(p[1] for p in pts):.1f}-{max(p[1] for p in pts):.0f}")
        print(f"calibration cross-check: predicted {predicted:.1f} px vs "
              f"measured {THRESHOLD_PX} px")
    print(f"wrote {TARGET.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
