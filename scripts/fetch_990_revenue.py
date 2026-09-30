"""Fetch program service revenue from ProPublica Nonprofit Explorer API.

Reads EINs from data/departments.json and writes data/program_revenue.csv.
Does not invent or interpolate missing values.
"""
from __future__ import annotations

import csv
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEPTS_PATH = ROOT / "data" / "departments.json"
OUT_PATH = ROOT / "data" / "program_revenue.csv"
TOTALS_PATH = ROOT / "data" / "operating_totals.csv"
API = "https://projects.propublica.org/nonprofits/api/v2/organizations/{ein}.json"

FORM_LABELS = {
    0: "990",
    1: "990-EZ",
    2: "990-PF",
}

# Candidate field names for program service revenue across form extracts
PROGRAM_REVENUE_KEYS = (
    "totprgmrevnue",
    "totprgmrev",
    "programservicerevenue",
    "prgmservrev",
    "totprgmrevnuecy",
)

TOTAL_REVENUE_KEYS = (
    "totrevenue",
    "totalrevenue",
    "totrevnue",
    "totrevenuecy",
)

TOTAL_EXPENSE_KEYS = (
    "totfuncexpns",
    "totalfunctionalexpenses",
    "totexpns",
    "totalexpenses",
    "totfuncexpense",
)


def normalize_ein(raw: str) -> str | None:
    if raw is None:
        return None
    s = str(raw).strip()
    if not s or s.upper() == "TODO":
        return None
    digits = "".join(ch for ch in s if ch.isdigit())
    if len(digits) < 8:
        return None
    return digits


def extract_int_field(filing: dict, keys: tuple[str, ...]) -> int | None:
    for key in keys:
        if key in filing and filing[key] is not None:
            try:
                return int(filing[key])
            except (TypeError, ValueError):
                continue
    return None


def extract_program_revenue(filing: dict) -> int | None:
    return extract_int_field(filing, PROGRAM_REVENUE_KEYS)


def form_label(filing: dict) -> str:
    ft = filing.get("formtype")
    if ft in FORM_LABELS:
        return FORM_LABELS[ft]
    # Some payloads use string labels
    raw = filing.get("form_type") or filing.get("formtype")
    return str(raw) if raw is not None else "unknown"


def fetch_org(ein: str) -> dict:
    url = API.format(ein=ein)
    req = urllib.request.Request(url, headers={"User-Agent": "vfd-project-demo/1.0 (educational)"})
    with urllib.request.urlopen(req, timeout=45) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    depts = json.loads(DEPTS_PATH.read_text(encoding="utf-8"))
    rows: list[dict] = []
    total_rows: list[dict] = []
    coverage: list[str] = []

    print("ProPublica 990 program-revenue coverage report")
    print("=" * 60)

    for dept in depts:
        name = dept.get("name", "Unknown")
        ein_raw = dept.get("ein", "TODO")
        ein = normalize_ein(ein_raw)
        if not ein:
            coverage.append(f"[SKIP] {name}: EIN is TODO / invalid ({ein_raw!r})")
            print(coverage[-1])
            continue

        try:
            payload = fetch_org(ein)
        except urllib.error.HTTPError as exc:
            coverage.append(f"[ERROR] {name} (EIN {ein}): HTTP {exc.code}")
            print(coverage[-1])
            continue
        except Exception as exc:  # noqa: BLE001
            coverage.append(f"[ERROR] {name} (EIN {ein}): {exc}")
            print(coverage[-1])
            continue

        filings = payload.get("filings_with_data") or []
        filings_wo = payload.get("filings_without_data") or []
        years_with: list[str] = []
        years_without: list[str] = []
        form_types_seen: set[str] = set()

        for filing in filings:
            year = filing.get("tax_prd_yr") or str(filing.get("tax_prd", ""))[:4]
            label = form_label(filing)
            form_types_seen.add(label)
            revenue = extract_program_revenue(filing)
            tot_rev = extract_int_field(filing, TOTAL_REVENUE_KEYS)
            tot_exp = extract_int_field(filing, TOTAL_EXPENSE_KEYS)
            if tot_rev is not None or tot_exp is not None:
                total_rows.append(
                    {
                        "ein": ein,
                        "department": name,
                        "tax_year": year,
                        "total_revenue": tot_rev if tot_rev is not None else "",
                        "total_expenses": tot_exp if tot_exp is not None else "",
                        "form_type": label,
                    }
                )
            if revenue is None:
                years_without.append(f"{year} ({label}, no program revenue field)")
                continue
            years_with.append(f"{year} ({label})")
            rows.append(
                {
                    "ein": ein,
                    "department": name,
                    "tax_year": year,
                    "program_revenue": revenue,
                    "form_type": label,
                }
            )

        for filing in filings_wo:
            year = filing.get("tax_prd_yr") or str(filing.get("tax_prd", ""))[:4]
            label = form_label(filing)
            form_types_seen.add(label)
            years_without.append(f"{year} ({label}, filing without extracted data)")

        forms = ", ".join(sorted(form_types_seen)) if form_types_seen else "none"
        coverage.append(
            f"[OK] {name} (EIN {ein}): forms={forms}; "
            f"with program revenue: {', '.join(years_with) or 'none'}; "
            f"without: {', '.join(years_without) or 'none'}"
        )
        print(coverage[-1])

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["ein", "department", "tax_year", "program_revenue", "form_type"],
        )
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda r: (r["department"], str(r["tax_year"]))))

    with TOTALS_PATH.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "ein",
                "department",
                "tax_year",
                "total_revenue",
                "total_expenses",
                "form_type",
            ],
        )
        writer.writeheader()
        writer.writerows(
            sorted(total_rows, key=lambda r: (r["department"], str(r["tax_year"])))
        )

    print("=" * 60)
    print(f"Wrote {len(rows)} revenue rows -> {OUT_PATH}")
    print(f"Wrote {len(total_rows)} operating-total rows -> {TOTALS_PATH}")
    report_path = ROOT / "data" / "program_revenue_coverage.txt"
    report_path.write_text("\n".join(coverage) + "\n", encoding="utf-8")
    print(f"Wrote coverage report -> {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
