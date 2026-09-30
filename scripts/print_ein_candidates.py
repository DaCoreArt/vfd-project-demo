import csv
from collections import defaultdict
from pathlib import Path

rows = list(
    csv.DictReader(
        (Path(__file__).resolve().parents[1] / "data" / "ein_candidates.csv").open(
            encoding="utf-8"
        )
    )
)
by: dict[str, list] = defaultdict(list)
for r in rows:
    by[r["department"]].append(r)


def fireish(r: dict) -> bool:
    blob = (r["candidate_legal_name"] + " " + (r["ntee_code"] or "")).upper()
    return any(
        x in blob
        for x in (
            "FIRE",
            "HOSE",
            "ENGINE",
            "LADDER",
            "HOOK",
            "VOLUNTEER",
            "AMBULANCE",
            "EMERGENCY",
            "M24",
            "M23",
            "E62",
        )
    )


print("TOP CANDIDATES (fire/emergency-leaning first)")
print("=" * 100)
for dept, items in by.items():
    items_sorted = sorted(items, key=lambda r: (-fireish(r), -float(r["match_score"])))
    print()
    print(dept)
    print("-" * len(dept))
    for r in items_sorted[:6]:
        print(f"  score={float(r['match_score']):.3f}  EIN={r['ein']}  {r['candidate_legal_name']}")
        print(
            f"    city={r['city'] or '-'}  ntee={r['ntee_code'] or '-'}  "
            f"ruling={r['ruling_date'] or '-'}  form={r['latest_form_type'] or '-'}  "
            f"rev={r['latest_total_revenue'] or '-'}"
        )
        print(f"    source={r['source']}  flag={r['flag'] or '-'}")
