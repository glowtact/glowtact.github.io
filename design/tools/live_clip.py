"""Derive the two live-clip versions from the handheld source.

Source: materials/video/GlowTact-BW-fingerprint.MOV (phone, HEVC 10-bit,
1280x720, 30 fps, 29.9 s, with audio). A GlowTact sensor on a desk, a tablet
showing the raw feed; a fingertip, then a coin pressed through denim.

  as-shot     the clip as recorded, audio stripped, 1280x720.
  stabilized  vidstab in tripod mode locked to frame 1 (a static scene, a
              moving camera), no zoom, then a fixed 1168x657 window at
              (96, 63) that stays inside every frame's black border
              (measured maxima: left 20, right 13, top 34, bottom 0 px),
              lanczos to 1280x720 and a light unsharp. Tablet-corner
              tracking: +-16/22 px before, +-3.5/2 px after. No
              super-resolution model is involved; "enhanced" is a 1.1x
              lanczos resample with sharpening.

Both are H.264 yuv420p, CRF 23, faststart, posters at the coin moment.
Run from the repository root; needs ffmpeg with libvidstab.
"""
from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "materials" / "video" / "GlowTact-BW-fingerprint.MOV"
VIDEO_DIR = ROOT / "design" / "assets" / "video" / "live"
POSTER_DIR = ROOT / "design" / "assets" / "images" / "live"
POSTER_TIME = "20.6"
CROP = "1168:657:96:63"
ENCODE = ["-c:v", "libx264", "-preset", "slow", "-crf", "23", "-pix_fmt", "yuv420p",
          "-movflags", "+faststart", "-an"]


def run(args: list[str]) -> None:
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


def poster(video: pathlib.Path, out: pathlib.Path) -> None:
    run(["-ss", POSTER_TIME, "-i", str(video), "-frames:v", "1", "-q:v", "4", str(out)])


def main() -> int:
    if not SRC.exists():
        print(f"missing source: {SRC}", file=sys.stderr)
        return 1
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    POSTER_DIR.mkdir(parents=True, exist_ok=True)

    as_shot = VIDEO_DIR / "live-as-shot.mp4"
    run(["-i", str(SRC), *ENCODE, str(as_shot)])
    poster(as_shot, POSTER_DIR / "live-as-shot-poster.jpg")

    stabilized = VIDEO_DIR / "live-stabilized.mp4"
    with tempfile.TemporaryDirectory() as tmp:
        transforms = pathlib.Path(tmp) / "live.trf"
        run(["-i", str(SRC), "-vf",
             f"vidstabdetect=shakiness=8:accuracy=15:tripod=1:result={transforms}",
             "-an", "-f", "null", "-"])
        run(["-i", str(SRC), "-vf",
             f"vidstabtransform=input={transforms}:tripod=1:optzoom=0:zoom=0:crop=black:interpol=bicubic,"
             f"crop={CROP},scale=1280:720:flags=lanczos,unsharp=5:5:0.5:5:5:0.0",
             *ENCODE, str(stabilized)])
    poster(stabilized, POSTER_DIR / "live-stabilized-poster.jpg")

    for path in (as_shot, stabilized):
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
             "stream=codec_name,pix_fmt,width,height,nb_frames", "-of", "csv=p=0", str(path)],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        print(f"{path.relative_to(ROOT)}: {probe}, {path.stat().st_size / 1e6:.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
