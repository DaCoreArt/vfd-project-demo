"""Collect logo candidate images from department websites.

Does NOT copy finals into images/logos/ for the book — candidates only.
"""
from __future__ import annotations

import csv
import hashlib
import html as html_lib
import io
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEPTS_PATH = ROOT / "data" / "departments.json"
OUT_CSV = ROOT / "data" / "logo_candidates.csv"
CAND_ROOT = ROOT / "images" / "logos" / "_candidates"
REVIEW_HTML = ROOT / "logo-review.html"

UA = (
    "VFDProjectLogoFetcher/1.0 (+https://github.com/; educational research; "
    "contact: joseph.foy@cuny.edu)"
)
REQUEST_DELAY_SEC = 2.0
LOGO_HINTS = ("logo", "patch", "seal", "badge")


@dataclass
class CandidateRef:
    url: str
    source_type: str
    inline_svg: str | None = None


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.base_href: str | None = None
        self.og_images: list[str] = []
        self.twitter_images: list[str] = []
        self.icons: list[tuple[str, str]] = []  # (rel, href)
        self.logo_imgs: list[str] = []
        self.header_imgs: list[str] = []
        self.header_svgs: list[str] = []
        self._in_headerish = 0
        self._in_svg = 0
        self._svg_buf: list[str] = []
        self._svg_depth_start = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        ad = {k.lower(): (v or "") for k, v in attrs}
        tag = tag.lower()

        if tag == "base" and ad.get("href"):
            self.base_href = ad["href"]

        if tag in {"header", "nav"}:
            self._in_headerish += 1

        if tag == "meta":
            prop = (ad.get("property") or ad.get("name") or "").lower()
            content = ad.get("content") or ""
            if content and prop in {"og:image", "og:image:url"}:
                self.og_images.append(content)
            if content and prop in {"twitter:image", "twitter:image:src"}:
                self.twitter_images.append(content)

        if tag == "link":
            rel = (ad.get("rel") or "").lower()
            href = ad.get("href") or ""
            if href and any(
                token in rel
                for token in ("icon", "apple-touch-icon", "shortcut icon")
            ):
                self.icons.append((rel, href))

        if tag == "img":
            src = ad.get("src") or ad.get("data-src") or ad.get("data-lazy-src") or ""
            if not src:
                srcset = ad.get("srcset") or ""
                if srcset:
                    src = srcset.split(",")[0].strip().split(" ")[0]
            blob = " ".join(
                [
                    src,
                    ad.get("alt") or "",
                    ad.get("class") or "",
                    ad.get("id") or "",
                ]
            ).lower()
            if src and any(h in blob for h in LOGO_HINTS):
                self.logo_imgs.append(src)
            elif src and self._in_headerish > 0:
                self.header_imgs.append(src)

        if tag == "svg":
            if self._in_svg == 0:
                self._svg_depth_start = 0
                self._svg_buf = [self._reconstruct_start("svg", attrs)]
            else:
                self._svg_buf.append(self._reconstruct_start("svg", attrs))
            self._in_svg += 1

        elif self._in_svg > 0:
            self._svg_buf.append(self._reconstruct_start(tag, attrs))

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self._in_svg > 0:
            self._svg_buf.append(f"</{tag}>")
            if tag == "svg":
                self._in_svg -= 1
                if self._in_svg == 0:
                    svg = "".join(self._svg_buf)
                    if self._in_headerish > 0:
                        self.header_svgs.append(svg)
                    self._svg_buf = []

        if tag in {"header", "nav"} and self._in_headerish > 0:
            self._in_headerish -= 1

    def handle_data(self, data: str) -> None:
        if self._in_svg > 0:
            self._svg_buf.append(html_lib.escape(data))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        # void / self-closing
        ad = {k.lower(): (v or "") for k, v in attrs}
        tag = tag.lower()
        if tag == "base" and ad.get("href"):
            self.base_href = ad["href"]
        if tag == "meta":
            self.handle_starttag(tag, attrs)
        if tag == "link":
            self.handle_starttag(tag, attrs)
        if tag == "img":
            self.handle_starttag(tag, attrs)
        if self._in_svg > 0:
            self._svg_buf.append(self._reconstruct_start(tag, attrs).rstrip(">") + " />")

    @staticmethod
    def _reconstruct_start(tag: str, attrs: list[tuple[str, str | None]]) -> str:
        parts = [f"<{tag}"]
        for k, v in attrs:
            if v is None:
                parts.append(f" {k}")
            else:
                parts.append(f' {k}="{html_lib.escape(v, quote=True)}"')
        parts.append(">")
        return "".join(parts)


def slugify(short_name: str) -> str:
    s = short_name.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-") or "dept"


def http_get(url: str, timeout: int = 45) -> tuple[bytes, str]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml,image/*,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        ctype = resp.headers.get("Content-Type", "")
        return resp.read(), ctype


def allowed_by_robots(page_url: str, rp_cache: dict[str, urllib.robotparser.RobotFileParser]) -> bool:
    parts = urllib.parse.urlsplit(page_url)
    origin = f"{parts.scheme}://{parts.netloc}"
    if origin not in rp_cache:
        rp = urllib.robotparser.RobotFileParser()
        robots_url = urllib.parse.urljoin(origin + "/", "robots.txt")
        try:
            raw, _ = http_get(robots_url, timeout=20)
            rp.parse(raw.decode("utf-8", errors="replace").splitlines())
        except Exception:
            # If robots.txt missing/unreachable, be permissive but still delay.
            rp.parse("User-agent: *\nAllow: /\n".splitlines())
        rp_cache[origin] = rp
        time.sleep(REQUEST_DELAY_SEC)
    return rp_cache[origin].can_fetch(UA, page_url)


def absolutize(base: str, href: str) -> str:
    return urllib.parse.urljoin(base, href)


def ext_from_url_or_ctype(url: str, ctype: str, data: bytes) -> str:
    path = urllib.parse.urlsplit(url).path.lower()
    for ext in (".svg", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico", ".bmp"):
        if path.endswith(ext):
            return ".jpg" if ext == ".jpeg" else ext
    ctype = (ctype or "").lower()
    if "svg" in ctype:
        return ".svg"
    if "png" in ctype:
        return ".png"
    if "jpeg" in ctype or "jpg" in ctype:
        return ".jpg"
    if "webp" in ctype:
        return ".webp"
    if "gif" in ctype:
        return ".gif"
    if "icon" in ctype:
        return ".ico"
    # sniff
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    if data[:3] == b"\xff\xd8\xff":
        return ".jpg"
    if data[:4] == b"GIF8":
        return ".gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    if data.lstrip().startswith(b"<svg") or b"<svg" in data[:500].lower():
        return ".svg"
    if data[:4] == b"\x00\x00\x01\x00":
        return ".ico"
    return ".bin"


def image_size(data: bytes, ext: str) -> tuple[int | None, int | None]:
    try:
        from PIL import Image  # type: ignore

        with Image.open(io.BytesIO(data)) as im:
            return im.size[0], im.size[1]
    except Exception:
        pass

    if ext == ".svg" or b"<svg" in data[:800].lower():
        text = data.decode("utf-8", errors="ignore")
        m = re.search(
            r'viewBox\s*=\s*["\']\s*([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)',
            text,
            re.I,
        )
        if m:
            return int(float(m.group(3))), int(float(m.group(4)))
        wm = re.search(r'\bwidth\s*=\s*["\']?([0-9.]+)', text, re.I)
        hm = re.search(r'\bheight\s*=\s*["\']?([0-9.]+)', text, re.I)
        if wm and hm:
            return int(float(wm.group(1))), int(float(hm.group(1)))
        return None, None

    if data[:8] == b"\x89PNG\r\n\x1a\n" and len(data) >= 24:
        w = int.from_bytes(data[16:20], "big")
        h = int.from_bytes(data[20:24], "big")
        return w, h
    if data[:3] == b"\xff\xd8\xff":
        # minimal SOF scan
        i = 2
        while i < len(data) - 9:
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if marker in {0xC0, 0xC1, 0xC2}:
                h = int.from_bytes(data[i + 5 : i + 7], "big")
                w = int.from_bytes(data[i + 7 : i + 9], "big")
                return w, h
            if marker == 0xD9:
                break
            if marker == 0x00 or marker == 0x01 or (0xD0 <= marker <= 0xD9):
                i += 2
                continue
            seglen = int.from_bytes(data[i + 2 : i + 4], "big")
            i += 2 + seglen
        return None, None
    if data[:4] == b"GIF8" and len(data) >= 10:
        w = int.from_bytes(data[6:8], "little")
        h = int.from_bytes(data[8:10], "little")
        return w, h
    return None, None


def collect_refs(page_url: str, html: str) -> list[CandidateRef]:
    parser = PageParser()
    try:
        parser.feed(html)
        parser.close()
    except Exception:
        pass

    base = parser.base_href or page_url
    refs: list[CandidateRef] = []
    seen: set[str] = set()

    def add(url_or_empty: str, source_type: str, inline: str | None = None) -> None:
        if inline is not None:
            key = "svg:" + hashlib.sha1(inline.encode("utf-8", errors="ignore")).hexdigest()[:12]
            if key in seen:
                return
            seen.add(key)
            refs.append(CandidateRef(url=page_url + "#" + key, source_type=source_type, inline_svg=inline))
            return
        if not url_or_empty or url_or_empty.startswith("data:"):
            return
        abs_url = absolutize(base, url_or_empty.strip())
        if abs_url in seen:
            return
        seen.add(abs_url)
        refs.append(CandidateRef(url=abs_url, source_type=source_type))

    for src in parser.logo_imgs:
        add(src, "logo-img")
    for i, src in enumerate(parser.header_imgs[:8], start=1):
        add(src, f"header-img-{i}")
    for url in parser.og_images:
        add(url, "og-image")
    for url in parser.twitter_images:
        add(url, "twitter-image")
    for rel, href in parser.icons:
        st = "apple-touch-icon" if "apple-touch-icon" in rel else "favicon"
        add(href, st)
    for i, svg in enumerate(parser.header_svgs[:5], start=1):
        add("", f"header-svg-{i}", inline=svg)

    return refs


def write_review(rows: list[dict], manual: list[dict]) -> None:
    # Group by department
    by_dept: dict[str, list[dict]] = {}
    for r in rows:
        by_dept.setdefault(r["department"], []).append(r)

    parts = [
        "<!DOCTYPE html>",
        '<html lang="en"><head><meta charset="utf-8" />',
        '<meta name="viewport" content="width=device-width, initial-scale=1" />',
        "<title>Logo candidates review</title>",
        "<style>",
        "body{font-family:system-ui,sans-serif;margin:24px;background:#f5f5f5;color:#111}",
        "h1{font-size:1.4rem} h2{font-size:1.1rem;margin:1.5rem 0 .5rem}",
        ".row{background:#fff;border:1px solid #ddd;border-radius:8px;padding:12px;margin-bottom:16px}",
        ".cands{display:flex;flex-wrap:wrap;gap:12px}",
        ".card{width:220px;border:1px solid #e5e5e5;border-radius:6px;padding:8px;background:#fafafa}",
        ".card img,.card object{max-width:100%;max-height:140px;display:block;margin:0 auto 8px;object-fit:contain;background:#fff}",
        ".meta{font-size:.75rem;color:#444;line-height:1.35;word-break:break-word}",
        ".low{color:#a30;font-weight:700}",
        ".manual{color:#666;font-style:italic}",
        "a{color:#0b57d0}",
        "</style></head><body>",
        "<h1>Logo candidates review</h1>",
        "<p>Not part of the Jupyter Book. Choose one file per department; finals are not installed yet.</p>",
    ]

    # Preserve department order from JSON if possible
    depts = json.loads(DEPTS_PATH.read_text(encoding="utf-8"))
    order = [d["name"] for d in depts]
    for name in order:
        parts.append(f'<section class="row"><h2>{html_lib.escape(name)}</h2>')
        manual_hit = next((m for m in manual if m["department"] == name), None)
        if manual_hit:
            reason = html_lib.escape(manual_hit.get("reason", "MANUAL"))
            site = html_lib.escape(manual_hit.get("website", ""))
            parts.append(f'<p class="manual">MANUAL — {reason}. Website: {site or "none"}</p>')
            parts.append("</section>")
            continue
        cands = by_dept.get(name, [])
        if not cands:
            parts.append('<p class="manual">No candidates downloaded.</p></section>')
            continue
        parts.append('<div class="cands">')
        for c in cands:
            rel = c["file"].replace("\\", "/")
            href = html_lib.escape(rel)
            w, h = c.get("width") or "", c.get("height") or ""
            low = ""
            try:
                if c.get("width") and int(c["width"]) < 300:
                    low = '<div class="low">low-res (&lt;300px wide)</div>'
            except Exception:
                pass
            is_svg = rel.lower().endswith(".svg")
            if is_svg:
                media = f'<object data="{href}" type="image/svg+xml" width="200" height="140">SVG</object>'
            else:
                media = f'<img src="{href}" alt="" loading="lazy" />'
            parts.append(
                "<div class=\"card\">"
                f"{media}"
                f"{low}"
                f"<div class=\"meta\"><strong>{html_lib.escape(c['source_type'])}</strong><br>"
                f"{w or '?'}×{h or '?'} · {html_lib.escape(c['format'])}<br>"
                f"<code>{html_lib.escape(Path(rel).name)}</code><br>"
                f"<a href=\"{html_lib.escape(c['source_url'])}\">source</a></div>"
                "</div>"
            )
        parts.append("</div></section>")

    parts.append("</body></html>")
    REVIEW_HTML.write_text("\n".join(parts), encoding="utf-8")


def main() -> int:
    depts = json.loads(DEPTS_PATH.read_text(encoding="utf-8"))
    CAND_ROOT.mkdir(parents=True, exist_ok=True)
    rp_cache: dict[str, urllib.robotparser.RobotFileParser] = {}
    rows: list[dict] = []
    manual: list[dict] = []
    summary = {"found": 0, "low_res_only": 0, "manual": 0, "no_candidates": 0}

    for dept in depts:
        name = dept["name"]
        short = dept.get("short_name") or name
        slug = slugify(short)
        website = (dept.get("website") or "").strip()
        print(f"\n=== {name} ===")

        if not website:
            print("  MANUAL: no website")
            manual.append({"department": name, "website": "", "reason": "no website"})
            summary["manual"] += 1
            continue
        if "facebook.com" in website.lower():
            print(f"  MANUAL: Facebook URL ({website})")
            manual.append({"department": name, "website": website, "reason": "facebook.com URL"})
            summary["manual"] += 1
            continue

        if not allowed_by_robots(website, rp_cache):
            print(f"  MANUAL: disallowed by robots.txt ({website})")
            manual.append({"department": name, "website": website, "reason": "disallowed by robots.txt"})
            summary["manual"] += 1
            continue

        try:
            print(f"  Fetching homepage: {website}")
            html_bytes, ctype = http_get(website)
            time.sleep(REQUEST_DELAY_SEC)
        except Exception as exc:  # noqa: BLE001
            print(f"  MANUAL: homepage fetch failed ({exc})")
            manual.append({"department": name, "website": website, "reason": f"fetch failed: {exc}"})
            summary["manual"] += 1
            continue

        # Follow simple HTML assumption
        charset = "utf-8"
        m = re.search(r"charset=([\w-]+)", ctype or "", re.I)
        if m:
            charset = m.group(1)
        html = html_bytes.decode(charset, errors="replace")
        # Prefer final URL path base — urllib doesn't expose after redirect easily;
        # reconstruct from Content-Location if present is rare; use original website.
        page_url = website
        refs = collect_refs(page_url, html)
        print(f"  Candidate refs: {len(refs)}")

        out_dir = CAND_ROOT / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        dept_rows: list[dict] = []
        type_counts: dict[str, int] = {}

        for ref in refs:
            type_counts[ref.source_type] = type_counts.get(ref.source_type, 0) + 1
            seq = type_counts[ref.source_type]
            try:
                if ref.inline_svg is not None:
                    data = ref.inline_svg.encode("utf-8")
                    ext = ".svg"
                    ctype_img = "image/svg+xml"
                    source_url = ref.url
                else:
                    if not allowed_by_robots(ref.url, rp_cache):
                        print(f"  skip (robots): {ref.url}")
                        continue
                    data, ctype_img = http_get(ref.url)
                    time.sleep(REQUEST_DELAY_SEC)
                    ext = ext_from_url_or_ctype(ref.url, ctype_img, data)
                    source_url = ref.url
            except Exception as exc:  # noqa: BLE001
                print(f"  download failed ({ref.source_type}): {exc}")
                continue

            fname = f"{ref.source_type}{ext}"
            # If duplicate source_type names, append index
            if seq > 1 and not ref.source_type.startswith("header-img-") and not ref.source_type.startswith("header-svg-"):
                fname = f"{ref.source_type}-{seq}{ext}"
            dest = out_dir / fname
            # Avoid overwrite collisions
            if dest.exists():
                dest = out_dir / f"{ref.source_type}-{seq}{ext}"
            dest.write_bytes(data)
            w, h = image_size(data, ext)
            rel = dest.relative_to(ROOT).as_posix()
            row = {
                "department": name,
                "file": rel,
                "source_url": source_url,
                "source_type": ref.source_type,
                "width": w if w is not None else "",
                "height": h if h is not None else "",
                "format": ext.lstrip("."),
            }
            dept_rows.append(row)
            print(f"  saved {rel} ({w}x{h} {ext})")

        rows.extend(dept_rows)
        if not dept_rows:
            summary["no_candidates"] += 1
            print("  No candidates downloaded")
        else:
            widths = []
            for r in dept_rows:
                try:
                    if r["width"] != "":
                        widths.append(int(r["width"]))
                except Exception:
                    pass
            if widths and max(widths) < 300:
                summary["low_res_only"] += 1
            else:
                summary["found"] += 1

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "department",
                "file",
                "source_url",
                "source_type",
                "width",
                "height",
                "format",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    # Also append MANUAL rows into review helper sidecar
    manual_path = ROOT / "data" / "logo_candidates_manual.json"
    manual_path.write_text(json.dumps(manual, indent=2), encoding="utf-8")

    write_review(rows, manual)

    print("\n" + "=" * 60)
    print(f"Wrote {len(rows)} candidate files catalog -> {OUT_CSV}")
    print(f"Review sheet -> {REVIEW_HTML}")
    print(
        "Summary: "
        f"found={summary['found']}  "
        f"low-res only={summary['low_res_only']}  "
        f"manual={summary['manual']}  "
        f"no candidates={summary['no_candidates']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
