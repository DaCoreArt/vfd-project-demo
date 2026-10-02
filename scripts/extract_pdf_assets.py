"""Extract logos, hero image, hyperlinks, and text slices from the VFD guide PDF."""
from __future__ import annotations

import json
import re
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "source" / "vfd-step-by-step-guide-2026-01-17.pdf"
OUT_DIR = ROOT / "data" / "pdf-extract"
LOGO_DIR = ROOT / "images" / "logos"
IMAGES_DIR = ROOT / "images"

# Expected short_name stems matching departments.json logo_path conventions
LOGO_ORDER_HINTS = [
    ("broad-channel-vfd", ("broad", "channel")),
    ("edgewater-park-hose-co", ("edgewater",)),
    ("gerritsen-beach-vfd", ("gerrit",)),
    ("point-breeze-vfd", ("point", "breeze")),
    ("richmond-engine-co", ("richmond",)),
    ("rockaway-point-vfd", ("rockaway",)),
    ("roxbury-vfd", ("roxbury",)),
    ("west-hamilton-beach-vfd", ("hamilton", "west")),
]


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOGO_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(PDF)
    print(f"PDF pages: {len(doc)}")

    # --- Page 1 images ---
    page0 = doc[0]
    images = page0.get_images(full=True)
    print(f"Page 1 embedded images: {len(images)}")
    meta = []
    for i, img in enumerate(images):
        xref = img[0]
        pix = fitz.Pixmap(doc, xref)
        if pix.n >= 5:  # CMYK
            pix = fitz.Pixmap(fitz.csRGB, pix)
        w, h = pix.width, pix.height
        area = w * h
        meta.append({"i": i, "xref": xref, "w": w, "h": h, "area": area, "pix": pix})
        print(f"  img[{i}] xref={xref} {w}x{h} area={area}")

    # Largest wide image ~= apparatus banner; smaller square-ish ~= logos
    by_area = sorted(meta, key=lambda m: m["area"], reverse=True)
    hero = by_area[0]
    hero_path = IMAGES_DIR / "hero-apparatus.jpg"
    # Save as JPEG
    if hero["pix"].alpha:
        rgb = fitz.Pixmap(fitz.csRGB, hero["pix"])
        rgb.save(hero_path.as_posix())
    else:
        hero["pix"].save(hero_path.as_posix())
    print(f"Saved hero -> {hero_path} ({hero['w']}x{hero['h']})")

    # Remaining images as logo candidates sorted left-to-right by bbox if available
    logo_imgs = [m for m in meta if m["i"] != hero["i"]]
    # Try to get positions via image blocks
    positioned = []
    for m in logo_imgs:
        # fallback order by index
        positioned.append(m)

    # Use page.get_image_info for positions
    try:
        infos = page0.get_image_info(xrefs=True)
    except Exception:
        infos = []
    xref_to_bbox = {}
    for info in infos:
        xref_to_bbox[info.get("xref")] = info.get("bbox")

    for m in logo_imgs:
        m["bbox"] = xref_to_bbox.get(m["xref"])
    logo_imgs.sort(key=lambda m: (m["bbox"][1] if m["bbox"] else 0, m["bbox"][0] if m["bbox"] else m["i"]))

    # Save all non-hero images; map by size/heuristic to 8 logos
    saved_logos = []
    for idx, m in enumerate(logo_imgs):
        path = OUT_DIR / f"page1-img-{idx}.png"
        pix = m["pix"]
        if pix.alpha:
            pix = fitz.Pixmap(fitz.csRGB, pix)
        pix.save(path.as_posix())
        saved_logos.append({"path": path, "w": m["w"], "h": m["h"], "bbox": m["bbox"], "xref": m["xref"]})

    # Prefer ~square logos in a reasonable size band
    candidates = [s for s in saved_logos if s["w"] >= 80 and s["h"] >= 80]
    # If more than 8, take 8 closest to square among mid-sized
    def square_score(s):
        ratio = s["w"] / max(s["h"], 1)
        return abs(1 - ratio) + (0 if 100 <= s["w"] <= 900 else 2)

    candidates = sorted(candidates, key=square_score)[:8]
    # Re-sort left-to-right / top-to-bottom for assignment
    candidates.sort(key=lambda s: (s["bbox"][1] if s["bbox"] else 0, s["bbox"][0] if s["bbox"] else 0))

    # If we don't have exactly 8, fall back to first 8 saved
    if len(candidates) < 8:
        candidates = saved_logos[:8]

    assigned = []
    for (stem, _hints), src in zip(LOGO_ORDER_HINTS, candidates):
        dest = LOGO_DIR / f"{stem}.png"
        dest.write_bytes(src["path"].read_bytes())
        assigned.append({"stem": stem, "from": src["path"].name, "w": src["w"], "h": src["h"]})
        print(f"Logo {stem} <- {src['path'].name} ({src['w']}x{src['h']})")

    (OUT_DIR / "logo_assignment.json").write_text(json.dumps(assigned, indent=2), encoding="utf-8")

    # --- Hyperlinks ---
    links_out = []
    for pno in range(len(doc)):
        page = doc[pno]
        words = page.get_text("words")  # x0,y0,x1,y1,word,block,line,word_no
        for link in page.get_links():
            uri = link.get("uri") or ""
            if not uri:
                continue
            rect = fitz.Rect(link.get("from"))
            # gather words intersecting rect
            anchor_words = []
            for w in words:
                wr = fitz.Rect(w[0], w[1], w[2], w[3])
                if wr.intersects(rect):
                    anchor_words.append(w[4])
            anchor = " ".join(anchor_words).strip()
            links_out.append(
                {
                    "page": pno + 1,  # 1-based
                    "uri": uri,
                    "anchor_text": anchor,
                    "rect": [rect.x0, rect.y0, rect.x1, rect.y1],
                }
            )

    links_path = OUT_DIR / "hyperlinks.json"
    links_path.write_text(json.dumps(links_out, indent=2), encoding="utf-8")
    print(f"Wrote {len(links_out)} hyperlinks -> {links_path}")

    # --- Full text per page for content restore ---
    pages_text = []
    for pno in range(len(doc)):
        text = doc[pno].get_text("text")
        pages_text.append({"page": pno + 1, "text": text})
    (OUT_DIR / "pages_text.json").write_text(
        json.dumps(pages_text, indent=2), encoding="utf-8"
    )
    # Also plaintext dump
    (OUT_DIR / "full_text.txt").write_text(
        "\n\n===== PAGE BREAK =====\n\n".join(p["text"] for p in pages_text),
        encoding="utf-8",
    )
    print(f"Wrote page text -> {OUT_DIR / 'full_text.txt'}")

    # Rubric pages 27-38 (1-based) -> indices 26-37
    rubric_text = []
    for pno in range(26, min(38, len(doc))):
        rubric_text.append(f"\n\n===== PAGE {pno+1} =====\n\n{doc[pno].get_text('text')}")
    (OUT_DIR / "rubrics_pp27-38.txt").write_text("".join(rubric_text), encoding="utf-8")

    # D4 pages 21-22
    d4 = []
    for pno in range(20, min(22, len(doc))):
        d4.append(f"\n\n===== PAGE {pno+1} =====\n\n{doc[pno].get_text('text')}")
    (OUT_DIR / "d4_pp21-22.txt").write_text("".join(d4), encoding="utf-8")

    doc.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
