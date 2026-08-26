"""Geocode NYC volunteer fire department addresses and update vfd-map.html.

Uses OpenStreetMap Nominatim (1 request/sec). No API key required.
"""
from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ASSETS = Path(__file__).resolve().parent
HTML_PATH = ASSETS / "interactive" / "vfd-map.html"
GEOJSON_PATH = ASSETS / "departments.geojson"
USER_AGENT = "vfd-project-demo/1.0 (educational map; local geocoding)"


def geocode(address: str) -> tuple[float, float] | None:
    query = urllib.parse.urlencode(
        {
            "q": address,
            "format": "json",
            "limit": 1,
            "countrycodes": "us",
        }
    )
    url = f"https://nominatim.openstreetmap.org/search?{query}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if not data:
        return None
    return float(data[0]["lat"]), float(data[0]["lon"])


def extract_departments(html: str) -> list[dict]:
    """Parse DEPARTMENTS array entries from the map HTML."""
    block = re.search(r"const DEPARTMENTS = \[(.*?)\];", html, re.S)
    if not block:
        raise SystemExit("Could not find DEPARTMENTS array in vfd-map.html")
    body = block.group(1)
    entries = []
    for m in re.finditer(
        r"\{\s*letter:\"(?P<letter>[^\"]+)\",\s*name:\"(?P<name>[^\"]+)\",\s*"
        r"address:\"(?P<address>[^\"]+)\",\s*lat:(?P<lat>null|-?\d+(?:\.\d+)?),\s*"
        r"lng:(?P<lng>null|-?\d+(?:\.\d+)?),",
        body,
        re.S,
    ):
        lat = None if m.group("lat") == "null" else float(m.group("lat"))
        lng = None if m.group("lng") == "null" else float(m.group("lng"))
        entries.append(
            {
                "letter": m.group("letter"),
                "name": m.group("name"),
                "address": m.group("address"),
                "lat": lat,
                "lng": lng,
            }
        )
    return entries


def patch_html(html: str, coords: dict[str, tuple[float, float]]) -> str:
    def repl(match: re.Match) -> str:
        letter = match.group("letter")
        if letter not in coords:
            return match.group(0)
        lat, lng = coords[letter]
        return (
            f'{{ letter:"{letter}", name:"{match.group("name")}",\n'
            f'    address:"{match.group("address")}",\n'
            f"    lat:{lat:.6f}, lng:{lng:.6f},"
        )

    return re.sub(
        r"\{\s*letter:\"(?P<letter>[^\"]+)\",\s*name:\"(?P<name>[^\"]+)\",\s*"
        r"address:\"(?P<address>[^\"]+)\",\s*lat:(?:null|-?\d+(?:\.\d+)?),\s*"
        r"lng:(?:null|-?\d+(?:\.\d+)?),",
        repl,
        html,
        flags=re.S,
    )


def main() -> None:
    html = HTML_PATH.read_text(encoding="utf-8")
    departments = extract_departments(html)
    print(f"Found {len(departments)} departments in {HTML_PATH.name}")

    coords: dict[str, tuple[float, float]] = {}
    features = []
    for i, dept in enumerate(departments):
        letter = dept["letter"]
        if dept["lat"] is not None and dept["lng"] is not None:
            print(f"  {letter} already geocoded: {dept['lat']}, {dept['lng']}")
            lat, lng = dept["lat"], dept["lng"]
        else:
            print(f"  Geocoding {letter}: {dept['address']}")
            result = geocode(dept["address"])
            if not result:
                print(f"    FAILED — no result for {dept['address']}")
                continue
            lat, lng = result
            print(f"    -> {lat:.6f}, {lng:.6f}")
            # Nominatim usage policy: max 1 request/sec
            if i < len(departments) - 1:
                time.sleep(1.1)
        coords[letter] = (lat, lng)
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "letter": letter,
                    "name": dept["name"],
                    "address": dept["address"],
                },
                "geometry": {"type": "Point", "coordinates": [lng, lat]},
            }
        )

    if not coords:
        raise SystemExit("No coordinates obtained.")

    updated = patch_html(html, coords)
    HTML_PATH.write_text(updated, encoding="utf-8", newline="\n")
    GEOJSON_PATH.write_text(
        json.dumps({"type": "FeatureCollection", "features": features}, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"Updated {HTML_PATH}")
    print(f"Wrote {GEOJSON_PATH}")
    print(f"Geocoded {len(coords)}/{len(departments)} departments.")


if __name__ == "__main__":
    main()
