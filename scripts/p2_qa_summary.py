"""Print every number cited in docs/INVENTORY_VERIFICATION_REPORT.md.

Run this immediately before writing or updating that report so no figure is
carried over from memory. Nothing is computed here that the inventory scripts do
not already produce; this script only summarises their outputs.
"""
import pathlib

import pandas as pd

INV = pathlib.Path(r"C:\Major\data\processed\inventory")


def hdr(t):
    print("\n" + "=" * 72)
    print(t)
    print("=" * 72)


src = pd.read_csv(INV / "inventory_source_records.csv", keep_default_na=False)
xw = pd.read_csv(INV / "duplicate_crosswalk.csv", keep_default_na=False)
cov = pd.read_csv(INV / "coverage_2000_2026.csv", keep_default_na=False)
ev = pd.read_csv(INV / "inventory_events_2000_2026.csv", keep_default_na=False)

hdr("A. COUNTS")
print(f"source records total          : {len(src)}")
print(f"sources (distinct)            : {src.source_id.nunique()}")
print(f"source list                   : {', '.join(sorted(src.source_id.unique()))}")
print(f"record_class EVENT_DATED      : {int((src.record_class == 'EVENT_DATED').sum())}")
print(f"record_class SITE_UNDATED     : {int((src.record_class == 'SITE_UNDATED').sum())}")
print(f"distinct event_group_id (all) : {src.loc[src.event_group_id != '', 'event_group_id'].nunique()}")
print(f"inventory_events_2000_2026 rows: {len(ev)}")

print("\nrecords per source:")
for s, n in src.source_id.value_counts().items():
    d = src[(src.source_id == s) & (src.record_class == "EVENT_DATED")]
    print(f"  {s:12s} {n:4d} total   {len(d):4d} dated   "
          f"{int((src.source_id == s).sum() and ((src.source_id == s) & (src.record_class == 'SITE_UNDATED')).sum()):4d} undated")

hdr("B. INCLUSION")
print(src.inclusion.value_counts().to_string())

hdr("C. VERIFICATION STATUS")
print(src.verification_status.value_counts().to_string())

hdr("D. IN-WINDOW TOTALS")
yr = pd.to_numeric(src.event_date_iso.astype(str).str.slice(0, 4), errors="coerce")
dated = src.record_class == "EVENT_DATED"
inwin_all = src[dated & yr.between(2000, 2026)]
inwin = inwin_all[inwin_all.inclusion.str.startswith("INCLUDED")]
pre2000 = src[dated & (yr < 2000)]
print(f"dated records 2000-2026       : {len(inwin_all)}")
print(f"  included                    : {len(inwin)}")
print(f"  excluded                    : {len(inwin_all) - len(inwin)}")
print(f"  distinct event groups (inc) : {inwin.event_group_id.nunique()}")
print(f"pre-2000 dated records        : {len(pre2000)}  years: "
      f"{sorted(set(pre2000.event_date_iso.astype(str).str.slice(0,4)))}")
print(f"undated site records          : {int((~dated).sum())}")

hdr("E. COVERAGE TABLE")
print(cov[["year", "included_event_records", "distinct_event_groups", "verified_records",
           "unresolved_records", "secondary_only_records", "best_date_precision"]]
      .to_string(index=False))

hdr("F. DATE PRECISION among in-window dated records")
print(inwin.date_certainty.value_counts().to_string())

hdr("G. COORDINATE PRECISION")
print("coord_precision_deg value counts (all records):")
print(src.coord_precision_deg.value_counts().to_string())
print("\ncoord format by source:")
for s in sorted(src.source_id.unique()):
    d = src[src.source_id == s]
    print(f"  {s:12s} {d.coord_precision_deg.min():.9f} - {d.coord_precision_deg.max():.9f}"
          f"   e.g. {d.coord_format.iloc[0][:70]}")

hdr("H. DUPLICATE CROSSWALK")
print(f"candidate pairs: {len(xw)}")
print(xw.groupby(["a_source", "b_source", "confidence"]).size().to_string())
for a, b in [("GSI14337", "GSI14115"), ("GSI2018", "KER2018"),
             ("GSI_PDLS", "GSI14115"), ("NASA_GLC", "GSI14115")]:
    d = xw[(xw.a_source == a) & (xw.b_source == b)]
    if len(d):
        print(f"\n{a} -> {b}: n={len(d)}  min={d.distance_m.min():.0f} m  "
              f"median={d.distance_m.median():.0f} m  max={d.distance_m.max():.0f} m")
        print(f"   within 300 m: {int((d.distance_m < 300).sum())}   "
              f"within 1500 m: {int((d.distance_m < 1500).sum())}   "
              f"within 3000 m: {int((d.distance_m <= 3000).sum())}")

hdr("I. 2024 COORDINATE EVIDENCE")
print((INV / "2024_corroboration.json").read_text(encoding="utf-8"))

hdr("J. THE TWO 2024 EVENT GROUPS")
print(src[src.event_group_id.str.startswith("EV-2024")][
    ["event_group_id", "source_id", "source_record_id", "locality",
     "lat_dd_original", "lon_dd_original", "event_date_iso", "verification_status"]]
    .to_string(max_colwidth=40, index=False))

hdr("K. BOUNDARY / FLAGGED RECORDS")
print(src[~src.inclusion.isin(["INCLUDED", "EXCLUDED_OUT_OF_DISTRICT"])][
    ["source_id", "source_record_id", "locality", "lat_dd_original", "lon_dd_original",
     "inclusion", "inclusion_reason"]].to_string(max_colwidth=44, index=False))
print("\nexcluded out of district:")
print(src[src.inclusion == "EXCLUDED_OUT_OF_DISTRICT"][
    ["source_id", "source_record_id", "locality", "inclusion_reason"]]
    .to_string(max_colwidth=52, index=False))

hdr("L. GEOLOGY FIELD COVERAGE")
dated_gsi = src[src.source_id.isin(["GSI14115", "GSI2018", "GSI_PDLS"])]
print(f"GSI records with geology text : {int((dated_gsi.geology.astype(str).str.strip() != '').sum())}"
      f" / {len(dated_gsi)}")
print(dict(dated_gsi.geology.astype(str).str.strip().value_counts()))
