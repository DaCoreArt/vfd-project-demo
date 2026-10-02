import fitz
from pathlib import Path

doc = fitz.open("source/vfd-step-by-step-guide-2026-01-17.pdf")
page = doc[0]
infos = page.get_image_info(xrefs=True)

LOGO_STEMS = [
    "broad-channel-vfd",
    "edgewater-park-hose-co",
    "gerritsen-beach-vfd",
    "point-breeze-vfd",
    "richmond-engine-co",
    "rockaway-point-vfd",
    "roxbury-vfd",
    "west-hamilton-beach-vfd",
]

logo_infos = []
for info in infos:
    xref = info["xref"]
    w = info.get("width") or 0
    h = info.get("height") or 0
    # Skip hero banners and page-wide images
    if xref in {20, 23, 0}:
        continue
    if w < 200 or h < 200:
        continue
    logo_infos.append(info)

logo_infos.sort(key=lambda i: (round(i["bbox"][1] / 40), i["bbox"][0]))
print("Logo order:")
for i, info in enumerate(logo_infos):
    print(i, info["xref"], info.get("width"), info.get("height"), [round(x) for x in info["bbox"]])

assert len(logo_infos) >= 8, len(logo_infos)
out = Path("images/logos")
for stem, info in zip(LOGO_STEMS, logo_infos[:8]):
    pix = fitz.Pixmap(doc, info["xref"])
    if pix.n >= 5:
        pix = fitz.Pixmap(fitz.csRGB, pix)
    if pix.alpha:
        pix = fitz.Pixmap(fitz.csRGB, pix)
    dest = out / f"{stem}.png"
    pix.save(dest.as_posix())
    print("saved", dest.name, pix.width, pix.height)

# hero
for info in infos:
    if info["xref"] == 20:
        pix = fitz.Pixmap(doc, 20)
        if pix.n >= 5 or pix.alpha:
            pix = fitz.Pixmap(fitz.csRGB, pix)
        dest = Path("images/hero-apparatus.jpg")
        pix.save(dest.as_posix())
        print("hero", dest, pix.width, pix.height)
doc.close()
