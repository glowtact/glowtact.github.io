"""Derive the live clip from the handheld source: a locked view of the tablet.

Source: materials/video/GlowTact-BW-fingerprint.MOV (phone, HEVC 10-bit,
1280x720, 30 fps, 29.9 s, with audio). A GlowTact sensor on a desk, a tablet
showing the raw feed; a fingertip, then a coin pressed through denim.

Every frame is registered to frame 0 with a homography estimated from SIFT
matches on the static scene (desk, tablet bezel, cables; the screen content
and the zone the hand moves through are masked out) and RANSAC, so
translation, rotation, zoom and perspective wobble are all removed: the
tablet corners move by about half a pixel afterwards (vidstab's tripod mode,
tried first, left 3.5 px and no zoom compensation). The output window is the
largest rectangle covered by every registered frame that still holds the
tablet and the sensor; it is resampled to 1280 px wide (lanczos, light
unsharp). No super-resolution model is involved. The clip is trimmed to the
interaction: the hand enters at 1.0 s and leaves at 28.0 s.

Needs OpenCV, NumPy and ffmpeg. Run from the repository root.
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

import cv2
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "materials" / "video" / "GlowTact-BW-fingerprint.MOV"
OUT = ROOT / "design" / "assets" / "video" / "live" / "live-stabilized.mp4"
POSTER = ROOT / "design" / "assets" / "images" / "live" / "live-stabilized-poster.jpg"
W, H, FPS = 1280, 720, 30
TRIM = (0.9, 28.1)          # seconds of the source to keep
POSTER_AT = 20.6            # source time of the coin pressed through denim
OUT_WIDTH = 1280

# Static-scene mask in reference coordinates: no screen content, no hand.
MASK = np.full((H, W), 255, np.uint8)
MASK[130:580, 180:940] = 0
MASK[380:720, 780:1280] = 0

# The window must keep the tablet (x from 130) and the sensor (x to 1235).
WINDOW_X0_MAX, WINDOW_X1_MIN, WINDOW_Y0_MAX = 128, 1236, 105


def homographies() -> tuple[list[np.ndarray], np.ndarray]:
    sift = cv2.SIFT_create(nfeatures=6000)
    matcher = cv2.BFMatcher(cv2.NORM_L2)
    cap = cv2.VideoCapture(str(SRC))
    ok, ref = cap.read()
    assert ok, SRC
    kp0, des0 = sift.detectAndCompute(cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY), MASK)
    hs = [np.eye(3)]
    coverage = np.ones((H, W), bool)
    previous = np.eye(3)
    fallbacks = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        search = cv2.warpPerspective(MASK, np.linalg.inv(previous), (W, H))
        kp, des = sift.detectAndCompute(gray, search)
        h, inliers = None, 0
        if des is not None and len(kp) > 20:
            pairs = matcher.knnMatch(des, des0, k=2)
            good = [a for a, b in (p for p in pairs if len(p) == 2) if a.distance < 0.75 * b.distance]
            if len(good) >= 12:
                src = np.float32([kp[m.queryIdx].pt for m in good])
                dst = np.float32([kp0[m.trainIdx].pt for m in good])
                h, mask = cv2.findHomography(src, dst, cv2.RANSAC, 3.0)
                inliers = int(mask.sum()) if mask is not None else 0
        if h is None or inliers < 25:
            h, fallbacks = previous, fallbacks + 1
        previous = h
        hs.append(h)
        coverage &= cv2.warpPerspective(np.full((H, W), 255, np.uint8), h, (W, H)) > 0
    cap.release()
    print(f"registered {len(hs)} frames, {fallbacks} fallback(s)")
    return hs, coverage


def window(coverage: np.ndarray) -> tuple[int, int, int, int]:
    """Largest fully covered rectangle holding the tablet and the sensor."""
    best = None
    for y0 in range(60, WINDOW_Y0_MAX + 1, 1):
        for x0 in range(100, WINDOW_X0_MAX + 1, 2):
            for x1 in range(1252, WINDOW_X1_MIN - 1, -2):
                rows = coverage[:, x0:x1].all(axis=1)
                if not rows[y0]:
                    continue
                y1 = y0 + int(np.argmin(rows[y0:])) if not rows[y0:].all() else H
                area = (x1 - x0) * (y1 - y0)
                if best is None or area > best[0]:
                    best = (area, x0, y0, x1, y1)
                break
    assert best, "no covered window holds the tablet and the sensor"
    _, x0, y0, x1, y1 = best
    w, h = (x1 - x0) & ~1, (y1 - y0) & ~1
    return x0, y0, w, h


def main() -> int:
    if not SRC.exists():
        print(f"missing source: {SRC}", file=sys.stderr)
        return 1
    hs, coverage = homographies()
    x0, y0, w, h = window(coverage)
    out_h = int(round(OUT_WIDTH * h / w)) & ~1
    print(f"window {w}x{h} at ({x0}, {y0}) -> {OUT_WIDTH}x{out_h}")

    first, last = int(round(TRIM[0] * FPS)), int(round(TRIM[1] * FPS))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    POSTER.parent.mkdir(parents=True, exist_ok=True)
    encoder = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24",
         "-s", f"{OUT_WIDTH}x{out_h}", "-r", str(FPS), "-i", "-",
         "-vf", "unsharp=5:5:0.5:5:5:0.0", "-c:v", "libx264", "-preset", "slow",
         "-crf", "23", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(OUT)],
        stdin=subprocess.PIPE,
    )
    cap = cv2.VideoCapture(str(SRC))
    index = 0
    while True:
        ok, frame = cap.read()
        if not ok or index >= last:
            break
        if index >= first:
            locked = cv2.warpPerspective(frame, hs[index], (W, H), flags=cv2.INTER_LANCZOS4)
            crop = locked[y0:y0 + h, x0:x0 + w]
            encoder.stdin.write(cv2.resize(crop, (OUT_WIDTH, out_h), interpolation=cv2.INTER_LANCZOS4).tobytes())
        index += 1
    cap.release()
    encoder.stdin.close()
    assert encoder.wait() == 0, "ffmpeg failed"

    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{POSTER_AT - TRIM[0]:.2f}", "-i", str(OUT),
                    "-frames:v", "1", "-q:v", "4", str(POSTER)], check=True)
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=codec_name,pix_fmt,width,height,nb_frames", "-of", "csv=p=0", str(OUT)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    print(f"{OUT.relative_to(ROOT)}: {probe}, {OUT.stat().st_size / 1e6:.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
