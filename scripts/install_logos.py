"""Install confirmed logo finals from candidates / user-supplied files."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DEPTS = ROOT / "data" / "departments.json"
CAND = ROOT / "images" / "logos" / "_candidates"
OUT_DIR = ROOT / "images" / "logos"

# name -> (source path, logo_source_url, out stem matching existing logo_path convention)
INSTALL = [
    (
        "Broad Channel VFD & Ambulance Corp.",
        CAND / "broad-channel" / "logo-img.png",
        "https://broadchannelvfd.org/wp-content/uploads/2022/02/Broad-Channel-patch.png",
        "broad-channel-vfd",
    ),
    (
        "Edgewater Park Volunteer Hose Co. #1",
        CAND / "edgewater-park" / "logo-img-2.png",
        "https://vfanyc.org/wp-content/uploads/2022/09/Edgewater-Park-patch-232x300.png",
        "edgewater-park-hose-co",
    ),
    (
        "Gerritsen Beach VFD",
        CAND / "gerritsen-beach" / "favicon-2.png",
        "https://gbfd.net/wp-content/uploads/2022/02/Gerrittsen-Beach-100-Years.png",
        "gerritsen-beach-vfd",
    ),
    (
        "Point Breeze VFD",
        Path(r"C:\Users\cpett\Downloads\Point Breeze.jpg"),
        "user-supplied:Point Breeze.jpg",
        "point-breeze-vfd",
    ),
    (
        "Richmond Engine Co. #1",
        CAND / "richmond-engine" / "logo-img.png",
        "https://richmondengine.org/wp-content/uploads/2023/04/Richmond-Engine-Co-NYC-patch.png",
        "richmond-engine-co",
    ),
    (
        "Rockaway Point VFD",
        CAND / "rockaway-point" / "favicon-2.png",
        "https://rpfdny.org/wp-content/uploads/2022/02/Rockaway-Point-Patch.png",
        "rockaway-point-vfd",
    ),
    (
        "Roxbury VFD",
        Path(r"C:\Users\cpett\Downloads\Roxbury.jpg"),
        "user-supplied:Roxbury.jpg",
        "roxbury-vfd",
    ),
    (
        "West Hamilton Beach VFD",
        Path(r"C:\Users\cpett\Downloads\West Hamilton Beach.png"),
        "user-supplied:West Hamilton Beach.png",
        "west-hamilton-beach-vfd",
    ),
]


def color_close(a: tuple[int, ...], b: tuple[int, ...], tol: int = 18) -> bool:
    return all(abs(x - y) <= tol for x, y in zip(a[:3], b[:3]))


def flood_clear_background(im: Image.Image, tol: int = 18) -> Image.Image:
    """Make connected corner-matching background transparent, then crop."""
    im = im.convert("RGBA")
    pixels = im.load()
    w, h = im.size
    if w == 0 or h == 0:
        return im

    # Sample corners — only clear if corners agree (uniform canvas)
    corners = [
        pixels[0, 0][:3],
        pixels[w - 1, 0][:3],
        pixels[0, h - 1][:3],
        pixels[w - 1, h - 1][:3],
    ]
    # Prefer black/white-ish canvases
    def is_canvas(rgb: tuple[int, int, int]) -> bool:
        r, g, b = rgb
        dark = r < 40 and g < 40 and b < 40
        light = r > 245 and g > 245 and b > 245
        return dark or light

    if not all(is_canvas(c) for c in corners):
        # Still trim existing alpha if present
        bbox = im.split()[-1].getbbox()
        return im.crop(bbox) if bbox else im

    target = corners[0]
    if not all(color_close(c, target, tol) for c in corners):
        bbox = im.split()[-1].getbbox()
        return im.crop(bbox) if bbox else im

    # Flood from all edge pixels matching target
    stack = []
    for x in range(w):
        stack.append((x, 0))
        stack.append((x, h - 1))
    for y in range(h):
        stack.append((0, y))
        stack.append((w - 1, y))

    seen = set()
    while stack:
        x, y = stack.pop()
        if (x, y) in seen or x < 0 or y < 0 or x >= w or y >= h:
            continue
        seen.add((x, y))
        r, g, b, a = pixels[x, y]
        if a == 0:
            continue
        if not color_close((r, g, b), target, tol):
            continue
        pixels[x, y] = (r, g, b, 0)
        stack.extend([(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)])

    bbox = im.split()[-1].getbbox()
    return im.crop(bbox) if bbox else im


def process(src: Path, dest: Path) -> None:
    im = Image.open(src)
    # Animated / palette
    if getattr(im, "n_frames", 1) > 1:
        im.seek(0)
    im = flood_clear_background(im)
    dest.parent.mkdir(parents=True, exist_ok=True)
    # Always save final as PNG (prefer PNG over JPG; no SVG among picks)
    im.save(dest, format="PNG", optimize=True)
    print(f"  {src.name} -> {dest.relative_to(ROOT)}  {im.size} mode={im.mode}")


def main() -> int:
    depts = json.loads(DEPTS.read_text(encoding="utf-8"))
    by_name = {d["name"]: d for d in depts}

    for name, src, source_url, stem in INSTALL:
        print(f"=== {name} ===")
        if not src.exists():
            raise SystemExit(f"Missing source: {src}")
        dest = OUT_DIR / f"{stem}.png"
        process(src, dest)
        dept = by_name[name]
        dept["logo_path"] = f"images/logos/{stem}.png"
        dept["logo_source_url"] = source_url

    DEPTS.write_text(json.dumps(depts, indent=2) + "\n", encoding="utf-8")
    print(f"Updated {DEPTS}")

    if CAND.exists():
        shutil.rmtree(CAND)
        print(f"Deleted {CAND}")

    review = ROOT / "logo-review.html"
    if review.exists():
        review.unlink()
        print(f"Deleted {review}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
