"""Find EIN candidates for NYC VFDs from IRS EO BMF + ProPublica search.

Does NOT write EINs into departments.json. Writes data/ein_candidates.csv only.
"""
from __future__ import annotations

import csv
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEPTS_PATH = ROOT / "data" / "departments.json"
OUT_PATH = ROOT / "data" / "ein_candidates.csv"
CACHE_DIR = ROOT / "data" / "cache"
EO_NY_PATH = CACHE_DIR / "eo_ny.csv"
EO_NY_URL = "https://www.irs.gov/pub/irs-soi/eo_ny.csv"
PROP_SEARCH = "https://projects.propublica.org/nonprofits/api/v2/search.json"
PROP_ORG = "https://projects.propublica.org/nonprofits/api/v2/organizations/{ein}.json"

UA = "vfd-project-ein-finder/1.0 (educational; local research)"

NAME_KEYWORDS = ("FIRE", "HOSE", "ENGINE", "LADDER", "HOOK")
NON_OPERATING_MARKERS = (
    "BENEVOLENT",
    "AUXILIARY",
    "RELIEF",
    "EXEMPT FIREMEN",
    "EXEMPT FIREMAN",
)

FORM_LABELS = {0: "990", 1: "990-EZ", 2: "990-PF", 3: "990-N"}


@dataclass
class Candidate:
    department: str
    candidate_legal_name: str
    ein: str
    city: str
    ntee_code: str
    ruling_date: str
    latest_form_type: str
    latest_total_revenue: str
    source: str
    match_score: float
    flag: str


def http_get(url: str, timeout: int = 120) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def http_get_json(url: str, timeout: int = 45) -> dict:
    return json.loads(http_get(url, timeout=timeout).decode("utf-8"))


def download_eo_ny(force: bool = False) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    if EO_NY_PATH.exists() and not force and EO_NY_PATH.stat().st_size > 1_000_000:
        print(f"Using cached EO BMF: {EO_NY_PATH}")
        return EO_NY_PATH
    print(f"Downloading IRS EO BMF NY -> {EO_NY_PATH}")
    print(f"  source page: https://www.irs.gov/charities-non-profits/exempt-organizations-business-master-file-extract-eo-bmf")
    print(f"  file URL: {EO_NY_URL}")
    data = http_get(EO_NY_URL, timeout=300)
    EO_NY_PATH.write_bytes(data)
    print(f"  wrote {len(data):,} bytes")
    return EO_NY_PATH


def normalize_text(value: str) -> str:
    s = (value or "").upper()
    s = s.replace("&", " AND ")
    s = re.sub(r"[^A-Z0-9\s]", " ", s)
    replacements = {
        "VOLUNTEER FIRE DEPARTMENT": "VFD",
        "VOLUNTEER FIRE DEPT": "VFD",
        "VOL FIRE DEPT": "VFD",
        "FIRE DEPARTMENT": "VFD",
        "FIRE DEPT": "VFD",
        "COMPANY": "CO",
        "NUMBER": "NO",
        "CORPORATION": "CORP",
        "INCORPORATED": "INC",
    }
    for a, b in replacements.items():
        s = s.replace(a, b)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def tokenize(value: str) -> set[str]:
    stop = {"THE", "OF", "AND", "INC", "CORP", "CO", "NO", "NYC", "NEW", "YORK"}
    return {t for t in normalize_text(value).split() if t and t not in stop}


def extract_city(address: str) -> str:
    # "15 Noel Road, Broad Channel, NY 11693" -> Broad Channel
    parts = [p.strip() for p in (address or "").split(",")]
    if len(parts) >= 2:
        # penultimate before state/zip often the city/neighborhood
        for part in reversed(parts[:-1]):
            if re.search(r"\bNY\b", part, re.I):
                continue
            if re.search(r"\d{5}", part):
                continue
            return part
    return ""


def city_aliases(city: str, dept_name: str) -> set[str]:
    aliases = {normalize_text(city)} if city else set()
    name_n = normalize_text(dept_name)
    # Neighborhood cues from department names / known NYC VFD areas
    cues = [
        "BROAD CHANNEL",
        "EDGEWATER PARK",
        "GERRITSEN BEACH",
        "GERRITTSEN BEACH",
        "POINT BREEZE",
        "BREEZY POINT",
        "ROCKAWAY POINT",
        "ROXBURY",
        "WEST HAMILTON BEACH",
        "HAMILTON BEACH",
        "HOWARD BEACH",
        "RICHMOND",
        "STATEN ISLAND",
        "BRONX",
        "BROOKLYN",
        "QUEENS",
        "FAR ROCKAWAY",
        "ROCKAWAY",
    ]
    for cue in cues:
        if cue in name_n or cue in normalize_text(city):
            aliases.add(cue)
    # Common BMF city spellings
    if "GERRITSEN" in name_n:
        aliases.add("GERRITTSEN BEACH")
        aliases.add("BROOKLYN")
    if "EDGEWATER" in name_n:
        aliases.add("BRONX")
    if "RICHMOND ENGINE" in name_n:
        aliases.add("STATEN ISLAND")
        aliases.add("RICHMOND")
    if "POINT BREEZE" in name_n or "ROCKAWAY POINT" in name_n or "ROXBURY" in name_n:
        aliases.add("BREEZY POINT")
        aliases.add("ROCKAWAY POINT")
        aliases.add("FAR ROCKAWAY")
    if "WEST HAMILTON" in name_n:
        aliases.add("HOWARD BEACH")
        aliases.add("HAMILTON BEACH")
    if "BROAD CHANNEL" in name_n:
        aliases.add("BROAD CHANNEL")
        aliases.add("FAR ROCKAWAY")
    return {a for a in aliases if a}


def name_similarity(a: str, b: str) -> float:
    na, nb = normalize_text(a), normalize_text(b)
    if not na or not nb:
        return 0.0
    seq = SequenceMatcher(None, na, nb).ratio()
    ta, tb = tokenize(a), tokenize(b)
    if not ta or not tb:
        jacc = 0.0
    else:
        jacc = len(ta & tb) / len(ta | tb)
    # Prefer shared distinctive tokens
    return round(0.55 * seq + 0.45 * jacc, 4)


def city_bonus(dept_city: str, dept_name: str, cand_city: str) -> float:
    aliases = city_aliases(dept_city, dept_name)
    cand = normalize_text(cand_city)
    if not cand:
        return 0.0
    if cand in aliases:
        return 0.25
    for alias in aliases:
        if alias and (alias in cand or cand in alias):
            return 0.2
        if SequenceMatcher(None, alias, cand).ratio() >= 0.85:
            return 0.15
    return 0.0


PLACE_TOKENS = (
    "BROAD CHANNEL",
    "EDGEWATER PARK",
    "GERRITSEN BEACH",
    "GERRITTSEN BEACH",
    "POINT BREEZE",
    "ROCKAWAY POINT",
    "ROCKAWAY PT",
    "ROXBURY VOLUNTEER",
    "WEST HAMILTON BEACH",
    "HAMILTON BEACH",
    "RICHMOND ENGINE",
)


def is_fire_related_bmf(row: dict) -> bool:
    ntee = (row.get("NTEE_CD") or "").upper()
    if ntee.startswith("M24"):
        return True
    name = (row.get("NAME") or "").upper()
    if any(k in name for k in NAME_KEYWORDS):
        return True
    # NYC VFD legal names sometimes use VOLUNTEERS / EMERGENCY SERVICES under M23/E62
    return any(tok in name for tok in PLACE_TOKENS)


def non_operating_flag(name: str) -> str:
    up = (name or "").upper()
    hits = [m for m in NON_OPERATING_MARKERS if m in up]
    if hits:
        return "likely_non_operating:" + "|".join(hits)
    return ""


def format_ein(raw: str) -> str:
    digits = re.sub(r"\D", "", str(raw or ""))
    if len(digits) == 9:
        return digits
    return digits


def load_bmf_fire_rows(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="latin-1", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if (row.get("STATE") or "").upper() != "NY":
                continue
            if is_fire_related_bmf(row):
                rows.append(row)
    print(f"EO BMF NY fire-related rows: {len(rows)}")
    return rows


def bmf_candidates_for_dept(dept: dict, bmf_rows: list[dict], min_score: float = 0.35) -> list[Candidate]:
    dept_name = dept["name"]
    dept_city = extract_city(dept.get("address", ""))
    out: list[Candidate] = []
    for row in bmf_rows:
        legal = row.get("NAME") or ""
        city = row.get("CITY") or ""
        score = name_similarity(dept_name, legal) + city_bonus(dept_city, dept_name, city)
        # Also compare against short_name
        short = dept.get("short_name", "")
        score = max(score, name_similarity(short, legal) + city_bonus(dept_city, dept_name, city) * 0.8)
        place = normalize_text(short)
        if place and place in normalize_text(legal):
            score = max(score, 0.8 + city_bonus(dept_city, dept_name, city))
        if score < min_score:
            continue
        ruling = row.get("RULING") or ""
        # RULING is YYYYMM
        ruling_date = ""
        if re.fullmatch(r"\d{6}", ruling):
            ruling_date = f"{ruling[:4]}-{ruling[4:6]}-01"
        elif re.fullmatch(r"\d{4}", ruling):
            ruling_date = f"{ruling}-01-01"
        rev = row.get("REVENUE_AMT") or ""
        out.append(
            Candidate(
                department=dept_name,
                candidate_legal_name=legal,
                ein=format_ein(row.get("EIN", "")),
                city=city.title() if city else "",
                ntee_code=row.get("NTEE_CD") or "",
                ruling_date=ruling_date,
                latest_form_type="",  # not in BMF; may fill from ProPublica later
                latest_total_revenue=str(rev) if rev not in ("", None) else "",
                source="irs_eo_bmf_ny",
                match_score=round(min(score, 1.0), 4),
                flag=non_operating_flag(legal),
            )
        )
    out.sort(key=lambda c: c.match_score, reverse=True)
    return out[:12]


def propublica_search(query: str) -> list[dict]:
    params = urllib.parse.urlencode({"q": query})
    url = f"{PROP_SEARCH}?{params}"
    try:
        data = http_get_json(url)
    except urllib.error.HTTPError as exc:
        print(f"  [ProPublica search error] {query!r}: HTTP {exc.code}")
        return []
    except Exception as exc:  # noqa: BLE001
        print(f"  [ProPublica search error] {query!r}: {exc}")
        return []
    orgs = data.get("organizations") or []
    return [o for o in orgs if (o.get("state") or "").upper() == "NY"]


def enrich_from_propublica(ein: str, cache: dict[str, dict]) -> dict:
    if ein in cache:
        return cache[ein]
    url = PROP_ORG.format(ein=ein)
    try:
        payload = http_get_json(url)
        time.sleep(0.25)
    except Exception as exc:  # noqa: BLE001
        cache[ein] = {"error": str(exc)}
        return cache[ein]
    org = payload.get("organization") or {}
    filings = payload.get("filings_with_data") or []
    latest = None
    if filings:
        latest = sorted(
            filings,
            key=lambda f: int(f.get("tax_prd_yr") or 0),
            reverse=True,
        )[0]
    form_type = ""
    revenue = ""
    if latest:
        ft = latest.get("formtype")
        form_type = FORM_LABELS.get(ft, str(ft) if ft is not None else "")
        if latest.get("totrevenue") is not None:
            revenue = str(latest.get("totrevenue"))
    cache[ein] = {
        "name": org.get("name") or "",
        "city": org.get("city") or "",
        "ntee_code": org.get("ntee_code") or "",
        "ruling_date": org.get("ruling_date") or "",
        "latest_form_type": form_type,
        "latest_total_revenue": revenue,
    }
    return cache[ein]


def propublica_queries_for_dept(dept: dict) -> list[str]:
    """Build ProPublica queries. Avoid tokens that 404 on their API (e.g. lone 'VFD')."""
    short = (dept.get("short_name") or "").strip()
    name = dept["name"]
    queries: list[str] = []
    if short:
        queries.append(short)
        queries.append(f"{short} Volunteers")
        queries.append(f"{short} Volunteer")
    # Place-focused variants without '#' / '&'
    cleaned = re.sub(r"[#&]+", " ", name)
    cleaned = re.sub(r"\bVFD\b", " ", cleaned, flags=re.I)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    queries.append(cleaned)
    if "Gerritsen" in name:
        queries.append("Gerrittsen Beach Fire Volunteers")
        queries.append("Gerrittsen Beach")
    if "Roxbury" in name:
        queries.append("Roxbury Volunteer Emergency")
    if "Rockaway Point" in name:
        queries.append("Rockaway Point Volunteer")
        queries.append("Rockaway Point Volunteer Emergency")
    if "Broad Channel" in name:
        queries.append("Broad Channel Volunteers")
    if "West Hamilton" in name:
        queries.append("West Hamilton Beach Volunteers")
        queries.append("Hamilton Beach Volunteers")
    if "Richmond Engine" in name:
        queries.append("Richmond Engine Co")
    if "Edgewater" in name:
        queries.append("Edgewater Park Volunteer Hose")
    if "Point Breeze" in name:
        queries.append("Point Breeze Volunteer Fire")
    # De-dupe preserving order
    seen: set[str] = set()
    out: list[str] = []
    for q in queries:
        q = re.sub(r"\s+", " ", q).strip()
        key = q.lower()
        if len(q) < 3 or key in seen:
            continue
        seen.add(key)
        out.append(q)
    return out


def propublica_candidates_for_dept(dept: dict, enrich_cache: dict[str, dict]) -> list[Candidate]:
    dept_name = dept["name"]
    dept_city = extract_city(dept.get("address", ""))
    short = dept.get("short_name") or ""

    seen_ein: set[str] = set()
    out: list[Candidate] = []
    for q in propublica_queries_for_dept(dept):
        print(f"  ProPublica search: {q!r}")
        for org in propublica_search(q):
            ein = format_ein(str(org.get("ein") or ""))
            if not ein or ein in seen_ein:
                continue
            seen_ein.add(ein)
            legal = org.get("name") or ""
            city = org.get("city") or ""
            score = name_similarity(dept_name, legal) + city_bonus(dept_city, dept_name, city)
            score = max(
                score,
                name_similarity(short, legal) + city_bonus(dept_city, dept_name, city) * 0.8,
            )
            # Boost exact place-name organizations even if legal name omits FIRE
            place = normalize_text(short)
            if place and place in normalize_text(legal):
                score = max(score, 0.75 + city_bonus(dept_city, dept_name, city))
            if score < 0.28:
                continue
            details = enrich_from_propublica(ein, enrich_cache)
            out.append(
                Candidate(
                    department=dept_name,
                    candidate_legal_name=details.get("name") or legal,
                    ein=ein,
                    city=(details.get("city") or city).title(),
                    ntee_code=details.get("ntee_code") or org.get("ntee_code") or "",
                    ruling_date=details.get("ruling_date") or "",
                    latest_form_type=details.get("latest_form_type") or "",
                    latest_total_revenue=details.get("latest_total_revenue") or "",
                    source="propublica_search",
                    match_score=round(min(score, 1.0), 4),
                    flag=non_operating_flag(details.get("name") or legal),
                )
            )
        time.sleep(0.2)
    out.sort(key=lambda c: c.match_score, reverse=True)
    return out[:15]


def merge_candidates(groups: list[list[Candidate]]) -> list[Candidate]:
    best: dict[str, Candidate] = {}
    for group in groups:
        for cand in group:
            key = cand.ein
            if key not in best:
                best[key] = cand
                continue
            prev = best[key]
            # Prefer higher score; merge sources and fill blanks
            sources = sorted({prev.source, cand.source})
            winner = cand if cand.match_score > prev.match_score else prev
            other = prev if winner is cand else cand
            merged = Candidate(
                department=winner.department,
                candidate_legal_name=winner.candidate_legal_name or other.candidate_legal_name,
                ein=winner.ein,
                city=winner.city or other.city,
                ntee_code=winner.ntee_code or other.ntee_code,
                ruling_date=winner.ruling_date or other.ruling_date,
                latest_form_type=winner.latest_form_type or other.latest_form_type,
                latest_total_revenue=winner.latest_total_revenue or other.latest_total_revenue,
                source="+".join(sources),
                match_score=max(winner.match_score, other.match_score),
                flag=winner.flag or other.flag,
            )
            best[key] = merged
    return sorted(best.values(), key=lambda c: (-c.match_score, c.candidate_legal_name))


def main() -> int:
    depts = json.loads(DEPTS_PATH.read_text(encoding="utf-8"))
    eo_path = download_eo_ny()
    bmf_rows = load_bmf_fire_rows(eo_path)
    enrich_cache: dict[str, dict] = {}

    all_rows: list[Candidate] = []
    for dept in depts:
        print(f"\n=== {dept['name']} ===")
        bmf = bmf_candidates_for_dept(dept, bmf_rows)
        print(f"  BMF candidates kept: {len(bmf)}")
        prop = propublica_candidates_for_dept(dept, enrich_cache)
        print(f"  ProPublica candidates kept: {len(prop)}")
        merged = merge_candidates([bmf, prop])
        # Fill missing form/revenue from ProPublica for BMF-only hits
        for cand in merged:
            if cand.ein and (not cand.latest_form_type or not cand.ruling_date):
                details = enrich_from_propublica(cand.ein, enrich_cache)
                if not cand.latest_form_type:
                    cand.latest_form_type = details.get("latest_form_type") or ""
                if not cand.latest_total_revenue and details.get("latest_total_revenue"):
                    cand.latest_total_revenue = details["latest_total_revenue"]
                if not cand.ruling_date and details.get("ruling_date"):
                    cand.ruling_date = details["ruling_date"]
                if not cand.ntee_code and details.get("ntee_code"):
                    cand.ntee_code = details["ntee_code"]
        all_rows.extend(merged)
        for c in merged[:8]:
            flag = f"  FLAG={c.flag}" if c.flag else ""
            print(
                f"  {c.match_score:.3f}  {c.ein}  {c.candidate_legal_name}  "
                f"({c.city}, {c.ntee_code}) [{c.source}]{flag}"
            )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "department",
        "candidate_legal_name",
        "ein",
        "city",
        "ntee_code",
        "ruling_date",
        "latest_form_type",
        "latest_total_revenue",
        "source",
        "match_score",
        "flag",
    ]
    with OUT_PATH.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in all_rows:
            writer.writerow(asdict(row))

    print(f"\nWrote {len(all_rows)} candidate rows -> {OUT_PATH}")
    print("NOTE: No EINs were written to departments.json.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
