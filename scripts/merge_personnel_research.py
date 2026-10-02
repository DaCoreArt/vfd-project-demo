"""Merge data/vfd-personnel-research.json into data/departments.json.

VERIFY-marked chiefs/personnel are not published as fact.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEPTS = ROOT / "data" / "departments.json"
PERSONNEL = ROOT / "data" / "vfd-personnel-research.json"
MAP_CSV = ROOT / "data" / "my-maps-import.csv"

SLUG_TO_SHORT = {
    "broad-channel": "Broad Channel",
    "edgewater-park": "Edgewater Park",
    "gerritsen-beach": "Gerritsen Beach",
    "point-breeze": "Point Breeze",
    "richmond-engine": "Richmond Engine",
    "rockaway-point": "Rockaway Point",
    "roxbury": "Roxbury",
    "west-hamilton-beach": "West Hamilton Beach",
}

RICHMOND_VFANYC = "https://vfanyc.org/richmond-engine-company-1/"
CHIEF_UNCONFIRMED = "to be confirmed"


def normalize_ein(raw: str | None) -> str:
    digits = "".join(ch for ch in str(raw or "") if ch.isdigit())
    return digits if len(digits) >= 8 else "TODO"


def is_verify(value: str | None) -> bool:
    return "VERIFY" in str(value or "").upper()


def publishable_personnel(people: list[dict], chief_status: str) -> list[dict]:
    out: list[dict] = []
    chief_is_verify = is_verify(chief_status)
    for person in people or []:
        name = str(person.get("name") or "").strip()
        title = str(person.get("title") or "").strip()
        if not name:
            continue
        if is_verify(title) or is_verify(name):
            continue
        # Do not publish an unverified chief under another title/role either
        if chief_is_verify and re.search(r"\bchief\b", title, re.I):
            continue
        out.append({"name": name, "title": title})
    return out


def publishable_source(source: str | None) -> str:
    text = (source or "").strip()
    if not text:
        return "TODO"
    if is_verify(text):
        # Keep only the non-VERIFY factual framing when possible
        if "2015" in text and "990-EZ" in text:
            return (
                "Latest detailed filing on ProPublica is Form 990-EZ (2015); "
                "current officers not confirmed for publication."
            )
        if "990-N" in text or "e-Postcard" in text:
            return "Board not listed on available Form 990-N (e-Postcard) filings."
        return "Source pending department confirmation."
    return text


def display_chief_line(dept: dict) -> str:
    if is_verify(dept.get("chief_status")):
        return "Chief: to be confirmed"
    name = dept.get("chief_name") or "TODO"
    if str(name).strip().upper() in {"TODO", CHIEF_UNCONFIRMED.upper()}:
        return "Chief: to be confirmed"
    return f"Chief: {name}"


def load_ruling_years() -> dict[str, str]:
    path = ROOT / "data" / "ein_candidates.csv"
    if not path.exists():
        return {}
    best: dict[str, str] = {}
    with path.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            ein = normalize_ein(row.get("ein"))
            ruling = (row.get("ruling_date") or "").strip()
            if ein != "TODO" and ruling[:4].isdigit() and ein not in best:
                best[ein] = ruling[:4]
    return best


def regenerate_maps_csv(depts: list[dict]) -> None:
    fieldnames = ["Name", "Address", "Latitude", "Longitude", "Description"]
    rows = []
    for dept in depts:
        lines = [display_chief_line(dept)]
        lines.append("Key Personnel:")
        people = dept.get("key_personnel") or []
        if people:
            for p in people:
                lines.append(f"- {p.get('name')}, {p.get('title')}")
        else:
            lines.append("- to be confirmed")
        source = dept.get("key_personnel_source") or "TODO"
        lines.append(f"Source: {source}")
        rows.append(
            {
                "Name": dept["name"],
                "Address": dept.get("address", ""),
                "Latitude": dept.get("lat", ""),
                "Longitude": dept.get("lng", ""),
                "Description": "\n".join(lines),
            }
        )
    with MAP_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    research = json.loads(PERSONNEL.read_text(encoding="utf-8"))
    depts = json.loads(DEPTS.read_text(encoding="utf-8"))
    by_short = {d["short_name"]: d for d in depts}
    rulings = load_ruling_years()

    for item in research["departments"]:
        short = SLUG_TO_SHORT[item["short_name"]]
        dept = by_short[short]

        ein = normalize_ein(item.get("ein"))
        dept["ein"] = ein
        if ein != "TODO":
            dept["ein_source"] = (
                f"vfd-personnel-research.json; "
                f"https://projects.propublica.org/nonprofits/organizations/{ein}"
            )
        if item.get("legal_name"):
            dept["legal_name"] = item["legal_name"]

        fy = item.get("founded_year")
        dept["founded_year"] = fy if fy not in (None, "", "TODO") else "TODO"
        if item.get("founded_year_source"):
            dept["founded_year_source"] = item["founded_year_source"]

        status = item.get("chief_status") or ""
        dept["chief_status"] = status
        if item.get("chief_title"):
            dept["chief_title"] = item["chief_title"]
        if item.get("chief_source"):
            dept["chief_source"] = item["chief_source"]

        # Publishable chief only — VERIFY chiefs are not published as named fact
        if is_verify(status):
            dept["chief_name"] = CHIEF_UNCONFIRMED
        else:
            chief = (item.get("chief_name") or "").strip()
            dept["chief_name"] = chief if chief and chief.upper() != "TODO" else CHIEF_UNCONFIRMED

        dept["key_personnel"] = publishable_personnel(
            item.get("key_personnel") or [], status
        )
        dept["key_personnel_source"] = publishable_source(item.get("key_personnel_source"))

        if item.get("notes"):
            dept["notes"] = item["notes"]
        if item.get("related_ein"):
            dept["related_ein"] = item["related_ein"]
        if ein != "TODO" and ein in rulings:
            dept["irs_ruling_year"] = rulings[ein]

        if short == "Richmond Engine":
            dept["website"] = RICHMOND_VFANYC

    DEPTS.write_text(json.dumps(depts, indent=2) + "\n", encoding="utf-8")
    regenerate_maps_csv(depts)

    print(f"Updated {DEPTS}")
    print(f"Regenerated {MAP_CSV}")
    for d in depts:
        print(
            f"  {d['short_name']}: chief={d.get('chief_name')!r} "
            f"status={d.get('chief_status')!r} people={len(d.get('key_personnel') or [])} "
            f"site={d.get('website')}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
