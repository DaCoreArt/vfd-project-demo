"""Merge data/vfd-personnel-research.json into data/departments.json."""
from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEPTS = ROOT / "data" / "departments.json"
RESEARCH_SRC = Path(r"C:\Users\cpett\Downloads\vfd-personnel-research.json")
PERSONNEL_DST = ROOT / "data" / "vfd-personnel-research.json"
MAP_CSV = ROOT / "data" / "my-maps-import.csv"

# Map research short_name -> departments.json short_name
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


def load_ruling_years() -> dict[str, str]:
    path = ROOT / "data" / "ein_candidates.csv"
    if not path.exists():
        return {}
    best: dict[str, str] = {}
    with path.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            ein = "".join(ch for ch in (row.get("ein") or "") if ch.isdigit())
            ruling = (row.get("ruling_date") or "").strip()
            if ein and ruling and ruling[:4].isdigit():
                # Prefer rows that also have a form type / higher score later
                if ein not in best:
                    best[ein] = ruling[:4]
    return best


def main() -> int:
    shutil.copy2(RESEARCH_SRC, PERSONNEL_DST)
    research = json.loads(RESEARCH_SRC.read_text(encoding="utf-8"))
    depts = json.loads(DEPTS.read_text(encoding="utf-8"))
    by_short = {d["short_name"]: d for d in depts}
    rulings = load_ruling_years()

    for item in research["departments"]:
        short = SLUG_TO_SHORT[item["short_name"]]
        dept = by_short[short]
        ein_digits = "".join(ch for ch in str(item.get("ein") or "") if ch.isdigit())
        dept["ein"] = ein_digits if ein_digits else "TODO"
        if ein_digits:
            dept["ein_source"] = (
                f"vfd-personnel-research.json; "
                f"https://projects.propublica.org/nonprofits/organizations/{ein_digits}"
            )
        else:
            dept["ein_source"] = "TODO"
        if item.get("legal_name"):
            dept["legal_name"] = item["legal_name"]
        fy = item.get("founded_year")
        dept["founded_year"] = fy if fy not in (None, "", "TODO") else "TODO"
        if item.get("founded_year_source"):
            dept["founded_year_source"] = item["founded_year_source"]
        chief = item.get("chief_name") or "TODO"
        dept["chief_name"] = chief
        if item.get("chief_title"):
            dept["chief_title"] = item["chief_title"]
        if item.get("chief_source"):
            dept["chief_source"] = item["chief_source"]
        if item.get("chief_status"):
            dept["chief_status"] = item["chief_status"]
        dept["key_personnel"] = item.get("key_personnel") or []
        dept["key_personnel_source"] = item.get("key_personnel_source") or "TODO"
        if item.get("notes"):
            dept["notes"] = item["notes"]
        if item.get("related_ein"):
            dept["related_ein"] = item["related_ein"]
        if ein_digits and ein_digits in rulings:
            dept["irs_ruling_year"] = rulings[ein_digits]
        # Prefer research legal/display caution for Richmond website
        if short == "Richmond Engine" and "unrelated" in (item.get("notes") or "").lower():
            # Keep URL but do not invent a replacement; note already stored
            pass

    DEPTS.write_text(json.dumps(depts, indent=2) + "\n", encoding="utf-8")
    print(f"Updated {DEPTS}")
    print(f"Copied research -> {PERSONNEL_DST}")

    # Refresh My Maps CSV descriptions from departments.json
    if MAP_CSV.exists():
        rows = []
        with MAP_CSV.open(encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            fieldnames = reader.fieldnames or [
                "Name",
                "Address",
                "Latitude",
                "Longitude",
                "Description",
            ]
            existing = {r["Name"]: r for r in reader}

        for dept in depts:
            base = existing.get(dept["name"], {})
            people = dept.get("key_personnel") or []
            lines = [f"Chief: {dept.get('chief_name') or 'TODO'}"]
            status = dept.get("chief_status")
            if status and status != "confirmed":
                lines[0] += f" ({status})"
            lines.append("Key Personnel:")
            if people:
                for p in people:
                    lines.append(f"- {p.get('name')}, {p.get('title')}")
            else:
                lines.append("- TODO")
            lines.append(f"Source: {dept.get('key_personnel_source') or 'TODO'}")
            rows.append(
                {
                    "Name": dept["name"],
                    "Address": dept.get("address") or base.get("Address", ""),
                    "Latitude": dept.get("lat", base.get("Latitude", "")),
                    "Longitude": dept.get("lng", base.get("Longitude", "")),
                    "Description": "\n".join(lines),
                }
            )

        with MAP_CSV.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"Updated {MAP_CSV}")

    for d in depts:
        print(
            f"  {d['short_name']}: ein={d.get('ein')} founded={d.get('founded_year')} "
            f"chief={d.get('chief_name')} ({d.get('chief_status', '')}) "
            f"people={len(d.get('key_personnel') or [])}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
