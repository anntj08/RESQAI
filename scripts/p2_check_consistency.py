"""Assert that the headline figures quoted in the phase-2 documentation match the
CSV products on disk.

This exists because a number in a report is a claim. If a script changes the data
and the report is not updated, this fails loudly instead of letting the two drift.
Run it after any change to the inventory scripts.
"""
import csv
import pathlib
import sys

import pandas as pd

MAIN = pathlib.Path(r"C:\Major")
INV = MAIN / "data" / "processed" / "inventory"

fails = []


def check(label, actual, expected):
    ok = actual == expected
    print(f"{'PASS' if ok else 'FAIL'}  {label:58s} {actual!r:>10} (expected {expected!r})")
    if not ok:
        fails.append(label)


src = pd.read_csv(INV / "inventory_source_records.csv", keep_default_na=False)
xw = pd.read_csv(INV / "duplicate_crosswalk.csv", keep_default_na=False)
cov = pd.read_csv(INV / "coverage_2000_2026.csv", keep_default_na=False)
ev = pd.read_csv(INV / "inventory_events_2000_2026.csv", keep_default_na=False)

yr = pd.to_numeric(src.event_date_iso.astype(str).str.slice(0, 4), errors="coerce")
dated = src.record_class == "EVENT_DATED"
inwin_all = src[dated & yr.between(2000, 2026)]
inwin = inwin_all[inwin_all.inclusion.str.startswith("INCLUDED")]

print("--- source records ---")
check("total source records", len(src), 468)
check("distinct sources", src.source_id.nunique(), 8)
check("EVENT_DATED records", int(dated.sum()), 385)
check("SITE_UNDATED records", int((~dated).sum()), 83)
check("pre-2000 dated records", int((dated & (yr < 2000)).sum()), 6)

print("\n--- in-window ---")
check("dated records 2000-2026", len(inwin_all), 379)
check("included in-window records", len(inwin), 372)
check("excluded in-window records", len(inwin_all) - len(inwin), 7)
check("distinct event groups (in-window, included)", inwin.event_group_id.nunique(), 371)

print("\n--- inclusion decisions ---")
inc = src.inclusion.value_counts()
check("INCLUDED", int(inc.get("INCLUDED", 0)), 445)
check("INCLUDED_BOUNDARY_REVIEW", int(inc.get("INCLUDED_BOUNDARY_REVIEW", 0)), 10)
check("EXCLUDED_OUT_OF_DISTRICT", int(inc.get("EXCLUDED_OUT_OF_DISTRICT", 0)), 12)
check("INCLUDED_FLAGGED", int(inc.get("INCLUDED_FLAGGED", 0)), 1)

print("\n--- verification status ---")
vs = src.verification_status.value_counts()
check("SOURCE_CONFIRMED", int(vs.get("SOURCE_CONFIRMED", 0)), 451)
check("NOT_APPLICABLE", int(vs.get("NOT_APPLICABLE", 0)), 12)
check("SECONDARY_SOURCE_ONLY", int(vs.get("SECONDARY_SOURCE_ONLY", 0)), 3)
check("NEEDS_REVIEW", int(vs.get("NEEDS_REVIEW", 0)), 1)
check("CORROBORATED", int(vs.get("CORROBORATED", 0)), 1)
check("every record has exactly one status",
      int(src.verification_status.astype(str).str.strip().eq("").sum()), 0)

print("\n--- per-source records ---")
per = {s: int((src.source_id == s).sum()) for s in
       ["KER2018", "GSI14768", "GSI14115", "GSI14337", "NASA_GLC",
        "GSI2018", "GSI_PDLS", "LIT2025"]}
check("KER2018", per["KER2018"], 331)
check("GSI14768", per["GSI14768"], 46)
check("GSI14115", per["GSI14115"], 35)
check("GSI14337", per["GSI14337"], 35)
check("NASA_GLC", per["NASA_GLC"], 9)
check("GSI2018", per["GSI2018"], 8)
check("GSI_PDLS", per["GSI_PDLS"], 2)
check("LIT2025", per["LIT2025"], 2)
check("per-source sum equals total", sum(per.values()), 468)

print("\n--- coverage table ---")
COV = {2006: (2, 2), 2007: (18, 18), 2008: (1, 1), 2009: (7, 7),
       2017: (1, 1), 2018: (339, 339), 2019: (1, 1), 2024: (3, 2)}
for y, (recs, groups) in COV.items():
    row = cov[cov.year == y].iloc[0]
    check(f"{y} records", int(row.included_event_records), recs)
    check(f"{y} event groups", int(row.distinct_event_groups), groups)
zeros = [int(r.year) for _, r in cov.iterrows()
         if int(r.included_event_records) == 0]
check("years with zero records", len(zeros), 19)
check("coverage rows", len(cov), 27)
check("coverage record total", int(cov.included_event_records.sum()), 372)
check("coverage group total", int(cov.distinct_event_groups.sum()), 371)

print("\n--- date precision (in-window included) ---")
dc = inwin.date_certainty.value_counts()
check("year precision", int(dc.get("year", 0)), 332)
check("day precision", int(dc.get("day", 0)), 30)
check("month precision", int(dc.get("month", 0)), 8)
check("multi-event", int(dc.get("multi-event", 0)), 2)

print("\n--- crosswalk ---")
check("candidate pairs", len(xw), 45)
g14337 = xw[xw.a_source == "GSI14337"]
check("14337->14115 pairs", len(g14337), 35)
check("14337 pairs within 1500 m", int((g14337.distance_m <= 1500).sum()), 33)
check("14337 pairs within 300 m", int((g14337.distance_m < 300).sum()), 7)
check("14337 median separation (m)", int(round(g14337.distance_m.median())), 471)
g2018 = xw[xw.a_source == "GSI2018"]
check("2018 pairs", len(g2018), 8)
check("2018 pairs under 300 m (duplicates)", int((g2018.distance_m < 300).sum()), 0)
gp = xw[xw.a_source == "GSI_PDLS"]
check("PDLS->LIT2025 pair", len(gp), 1)
check("PDLS separation (m)", int(round(gp.distance_m.iloc[0])), 495)
check("PDLS confidence", gp.confidence.iloc[0], "high")
check("crosswalk has no out-of-mask source label",
      int((~xw.b_source.isin(src.source_id.unique())).sum()), 0)

print("\n--- event table ---")
check("inventory_events rows", len(ev), 385)
check("event table has one row per dated record",
      len(ev), int(dated.sum()))

print("\n--- manifest ---")
with open(MAIN / "docs" / "data_manifest.csv", encoding="utf-8") as f:
    man = list(csv.DictReader(f))
# Phase 2 registered 28 datasets; Phase 3 appends derived products. What must hold
# is that every Phase 2 dataset is still present and no id is duplicated -- not
# that the file never grows.
P2_IDS = {f"DEM-0{i}" for i in (1, 2, 3)} | {"LC-01", "RF-01", "GEO-01", "GEO-02",
                                             "BND-01", "BND-02", "BND-03",
                                             "ADD-01", "ADD-02"} | {f"INV-{i:02d}" for i in range(1, 17)}
ids = {r["dataset_id"] for r in man}
check("manifest keeps all 28 Phase 2 datasets", len(P2_IDS - ids), 0)
check("manifest columns", len(man[0]), 16)
check("manifest unique ids", len(ids), len(man))

print("\n" + "=" * 70)
if fails:
    print(f"{len(fails)} FAILED:")
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("all consistency checks passed")
