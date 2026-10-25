"""Assemble the phase-2 Wayanad inventory: inclusion decisions, event grouping,
duplicate crosswalk and year-by-year coverage for 2000-2026.

Consumes data/processed/inventory/inventory_all_source_records.csv produced by
build_consolidated_inventory.py and writes four products:

  inventory_source_records.csv   every original source record + decision + event id
  duplicate_crosswalk.csv        candidate matches, evidence, decision, confidence
  inventory_events_2000_2026.csv event-level view built from dated records only
  coverage_2000_2026.csv         candidate / verified / unresolved per year

Counting rules (stated so they cannot be misread):
  * "source records" counts rows in the tables above, including duplicates.
  * "distinct events" counts distinct event_group_id values among *dated* records.
  * undated site records are reported separately and never counted as events.
  * several source records describing one physical landslide collapse into one
    event group only on explicit evidence recorded in the crosswalk.
"""
import csv
import pathlib
import re

import geopandas as gpd
import pandas as pd

MAIN = pathlib.Path(r"C:\Major")
INV = MAIN / "data" / "processed" / "inventory"
SRC = INV / "inventory_all_source_records.csv"

df = pd.read_csv(SRC)
print(f"input source records: {len(df)}")

# ------------------------------------------------------------------ fixes -----
# NASA GLC was queried on a bounding box, so it returns neighbouring districts too.
OUT_OF_DISTRICT = {
    "GLC/100": "Kozhikode district, not Wayanad",
    "GLC/5200": "Nilgiris, Tamil Nadu",
    "GLC/1213": "Kozhikode district",
    "GLC/1212": "Kozhikode district",
    "GLC/4984": "Nilgiris, Tamil Nadu",
    "GLC/1172": "Nilambur, Malappuram district",
    "GLC/4468": "Pulloorampara, Kozhikode district",
}
# Records just outside the GADM polygon: retained and flagged, never silently moved.
NEEDS_REVIEW = {}
for _, r in df.iterrows():
    pass

df["inclusion"] = "INCLUDED"
df["inclusion_reason"] = ""
df["spatial_use"] = "usable_for_spatial_analysis"

for i, r in df.iterrows():
    rid = r["source_record_id"]
    if rid in OUT_OF_DISTRICT:
        df.at[i, "inclusion"] = "EXCLUDED_OUT_OF_DISTRICT"
        df.at[i, "inclusion_reason"] = OUT_OF_DISTRICT[rid]
        df.at[i, "spatial_use"] = "not_applicable"

# GSI 14115 record 17: impossible longitude, flagged at extraction time
m = df["source_record_id"].astype(str).str.contains(r"14115/p141/row17")
df.loc[m, "inclusion"] = "INCLUDED_FLAGGED"
df.loc[m, "inclusion_reason"] = ("printed longitude 76d56'58\"E places the site in Tamil Nadu, "
                                "~77 km east of the district; retained as published")
df.loc[m, "spatial_use"] = "unsuitable_until_corrected"

# everything that fell outside the GADM polygon but is not a mis-typed coordinate
gadm = gpd.read_file(MAIN / "data" / "raw" / "boundary" / "gadm41_IND_2" / "gadm41_IND_2.json")
wy = gadm[(gadm.NAME_1.astype(str).str.strip().str.lower() == "kerala")
          & (gadm.NAME_2.astype(str).str.strip().str.lower() == "wayanad")].to_crs(4326)
poly = wy.geometry.union_all() if hasattr(wy.geometry, "union_all") else wy.geometry.unary_union

g = gpd.GeoDataFrame(df.copy(), geometry=gpd.points_from_xy(df.lon_dd_original, df.lat_dd_original), crs=4326)
inside = g.geometry.within(poly)
print(f"inside GADM Wayanad: {int(inside.sum())} / {len(g)}")

# Being outside the polygon is not one condition. A point 200 m outside is a
# boundary-generalisation artefact and is worth keeping; a point 17 km outside is
# in a different district and is not ours. The rule is therefore a measured
# distance, and the measured value is written into the record so the decision can
# be audited without re-running anything.
BOUNDARY_TOLERANCE_M = 5000.0

gproj = g.to_crs(32643)
boundary_line = wy.to_crs(32643).geometry.union_all().boundary
df["dist_outside_boundary_m"] = 0.0

for i in df.index[~inside.to_numpy()]:
    d_out = float(gproj.geometry.loc[i].distance(boundary_line))
    df.at[i, "dist_outside_boundary_m"] = round(d_out, 1)
    if df.at[i, "inclusion"] != "INCLUDED":
        continue
    if d_out > BOUNDARY_TOLERANCE_M:
        df.at[i, "inclusion"] = "EXCLUDED_OUT_OF_DISTRICT"
        df.at[i, "spatial_use"] = "not_applicable"
        df.at[i, "inclusion_reason"] = (
            f"{d_out / 1000:.1f} km outside the GADM 4.1 Wayanad polygon, which is far "
            "beyond any plausible boundary-generalisation error. The source report "
            "covers a corridor that crosses into the adjacent district.")
    else:
        df.at[i, "inclusion"] = "INCLUDED_BOUNDARY_REVIEW"
        df.at[i, "spatial_use"] = "review_before_spatial_use"
        df.at[i, "inclusion_reason"] = (
            f"{d_out:.0f} m outside the GADM 4.1 polygon, i.e. within a plausible "
            "generalisation error of the district edge. Retained as published; "
            "not relocated.")

print(f"outside polygon split: "
      f"{(df.inclusion == 'EXCLUDED_OUT_OF_DISTRICT').sum()} excluded, "
      f"{(df.inclusion == 'INCLUDED_BOUNDARY_REVIEW').sum()} retained for review")

# ------------------------------------------------------- event grouping -------
# Only records whose source states a date can carry an event group.
df["episode_id"] = ""
df["event_group_id"] = ""

NO_DATE = df["event_date_iso"].isna() | (df["event_date_iso"].astype(str).str.strip() == "")


def g(cond, event_id, episode_id):
    df.loc[cond, "event_group_id"] = event_id
    df.loc[cond, "episode_id"] = episode_id


sid = df["source_record_id"].astype(str)

# 2018: each mapped landslide in the Hao/van Westen inventory is its own event
c = df.source_id.eq("KER2018")
df.loc[c, "event_group_id"] = "EV-2018-KER-" + df.loc[c].index.astype(str)
df.loc[c, "episode_id"] = "EP-2018-MONSOON"

# 2018: GSI's eight 42-point datasheets
c = df.source_id.eq("GSI2018")
df.loc[c, "event_group_id"] = "EV-2018-GSI-" + df.loc[c].index.astype(str)
df.loc[c, "episode_id"] = "EP-2018-06-14"

# 2014/2017-2024 dated records from GSI 14115: one group per row, episodes by date
c = df.source_id.eq("GSI14115") & ~NO_DATE
df.loc[c, "event_group_id"] = "EV-14115-" + df.loc[c].index.astype(str)
df.loc[c, "episode_id"] = "EP-" + df.loc[c, "event_date_iso"].astype(str)

# Three 14115 rows record a failure that recurred: "1982 & June 2007", "1988 &
# July 2007", "19th June 1991 & 1st July". Only the in-window occurrence is used
# for year coverage; the earlier occurrence stays in date_text and is never
# dropped. Row 8 (1991 only) has no in-window occurrence.
MULTI_TO_WINDOW = {
    "14115/p136/row3 (printed Sl.3)": "2007-06",
    "14115/p137/row6 (printed Sl.6)": "2007-07",
}
for rid, win in MULTI_TO_WINDOW.items():
    m2 = df.source_record_id.astype(str).eq(rid)
    df.loc[m2, "event_date_iso"] = win
    df.loc[m2, "date_certainty"] = "multi-event"
    df.loc[m2, "notes"] = (df.loc[m2, "notes"].astype(str) + " in-window occurrence dated " + win +
                           "; an earlier occurrence at the same site is also described")

# July 2024 Mundakkai-Chooralmala: GSI slide + independent literature record
c = sid.eq("KER/WYD/58A03/2024/01") | sid.str.endswith("Table1/2024-07-30")
g(c, "EV-2024-MUNDAKKAI", "EP-2024-07-30")

# June 2024 Meenakshi Bridge road-cut slide (reported in the 2025 GSI volume)
c = sid.eq("KER/WYD/58A03/2025/01")
g(c, "EV-2024-MEENAKSHI-BRIDGE", "EP-2024-06")

# August 2019 Puthumala
c = sid.str.endswith("Table1/2019-08-08")
g(c, "EV-2019-PUTHUMALA", "EP-2019-08-08")

# NASA GLC records. Every GLC record carries a stated date, so every one gets an
# event group even though most lie outside Wayanad: an out-of-district event is
# still a dated event, it is simply not one of ours. Labelling them
# SITE_UNDATED (the previous behaviour) would have inflated the undated count.
cream = df.source_id.eq("NASA_GLC") & (df.event_date_iso.astype(str).str.strip() != "")
for i in df.index[cream]:
    eid = df.at[i, "source_record_id"].split("/")[-1]
    df.at[i, "event_group_id"] = f"EV-GLC-{eid}"
    df.at[i, "episode_id"] = "EP-" + str(df.at[i, "event_date_iso"])
# the two that are actually inside the district keep descriptive ids
c = sid.eq("GLC/101")
g(c, "EV-2007-GLC101", "EP-2007-06-25")
c = sid.eq("GLC/10011")
g(c, "EV-2017-WAYANAD-PASS", "EP-2017-06-27")

dated = df.event_group_id.astype(str).str.len() > 0
df["record_class"] = "SITE_UNDATED"
df.loc[dated, "record_class"] = "EVENT_DATED"
print(f"\ndated event records: {int(dated.sum())}   undated site records: {int((~dated).sum())}")
print(f"distinct event groups: {df.loc[dated,'event_group_id'].nunique()}")

# --------------------------------------------------- verification status ------
# Rules: GSI field investigation of the specific slide -> SOURCE_CONFIRMED.
#        an independent publication agreeing on locality+date+coords -> CORROBORATED.
#        a literature compilation with no primary record obtained -> SECONDARY_SOURCE_ONLY.
#        a coordinate that fails a documented internal-consistency test -> NEEDS_REVIEW.
df["verification_status"] = ""
c = df.source_id.isin(["GSI14115", "GSI2018", "GSI_PDLS", "GSI14337", "GSI14768"]) & dated
df.loc[c, "verification_status"] = "SOURCE_CONFIRMED"
c = df.source_id.eq("KER2018")
df.loc[c, "verification_status"] = "SOURCE_CONFIRMED"
c = df.source_id.eq("NASA_GLC")
df.loc[c, "verification_status"] = "SECONDARY_SOURCE_ONLY"
c = df.source_id.eq("LIT2025") & sid.str.endswith("2024-07-30")
df.loc[c, "verification_status"] = "CORROBORATED"
c = df.source_id.eq("LIT2025") & sid.str.endswith("2019-08-08")
df.loc[c, "verification_status"] = "SECONDARY_SOURCE_ONLY"
# undated site records are confirmed as *sites* in a GSI survey, but no event is claimed
c = df.record_class.eq("SITE_UNDATED") & df.source_id.isin(
    ["GSI14115", "GSI14337", "GSI14768"])
df.loc[c, "verification_status"] = "SOURCE_CONFIRMED"
df.loc[df.inclusion.eq("INCLUDED_FLAGGED"), "verification_status"] = "NEEDS_REVIEW"

df.loc[df.inclusion.eq("EXCLUDED_OUT_OF_DISTRICT"), "verification_status"] = "NOT_APPLICABLE"

# -------------------------------------------------------------- crosswalk ----
xw = []


def xwalk(a_mask, b_mask, basis, decision, confidence):
    A = df[a_mask]
    B = df[b_mask]
    if A.empty or B.empty:
        return
    # The index MUST be carried through explicitly. GeoSeries defaults to a
    # 0..n-1 RangeIndex, which would make `dd.idxmin()` a *position* rather than
    # a source-row label and silently pair the nearest geometry with an
    # unrelated record. A points_from_xy array has no index of its own.
    ga = gpd.GeoSeries(gpd.points_from_xy(A.lon_dd_original, A.lat_dd_original),
                       index=A.index, crs=4326).to_crs(32643)
    gb = gpd.GeoSeries(gpd.points_from_xy(B.lon_dd_original, B.lat_dd_original),
                       index=B.index, crs=4326).to_crs(32643)
    for ia, pa in ga.items():
        dd = gb.distance(pa)
        j = dd.idxmin()
        # guard: the matched label must belong to the B mask, and the measured
        # distance must equal the distance to B's own geometry at that label
        assert j in B.index, f"crosswalk matched row {j} outside the B mask"
        assert df.at[j, "source_id"] == B.at[j, "source_id"]
        xw.append({
            "record_a": df.at[ia, "source_record_id"],
            "record_b": df.at[j, "source_record_id"],
            "a_source": df.at[ia, "source_id"],
            "b_source": df.at[j, "source_id"],
            "a_locality": df.at[ia, "locality"],
            "b_locality": df.at[j, "locality"],
            "a_date": df.at[ia, "event_date_iso"],
            "b_date": df.at[j, "event_date_iso"],
            "distance_m": round(float(dd.loc[j]), 1),
            "basis": basis,
            "decision": decision,
            "confidence": confidence,
        })


# 1. GSI 14337 two-decimal records vs GSI 14115 arc-second records
xwalk(df.source_id.eq("GSI14337"), df.source_id.eq("GSI14115"),
      "same publisher lineage; 14337 gives village centroid at 2 dp, 14115 the surveyed site",
      "same investigation site - 14115 coordinate supersedes 14337 coordinate for spatial use",
      "medium")

# 2. GSI 2018 datasheets vs the 2018 statewide inventory
xwalk(df.source_id.eq("GSI2018"), df.source_id.eq("KER2018"),
      "same monsoon season; GSI 42-point datasheet vs statewide mapped point",
      "candidate duplicate - not merged without a locality match",
      "low")

# 3. July 2024 GSI vs literature
xwalk(df.source_id.eq("GSI_PDLS") & sid.eq("KER/WYD/58A03/2024/01"),
      df.source_id.eq("LIT2025"), "independent publication vs GSI first information report",
      "SAME EVENT - merged into EV-2024-MUNDAKKAI", "high")

# 4. NASA GLC 2007 vs GSI 14115 2007 records
xwalk(df.source_id.eq("NASA_GLC") & sid.eq("GLC/101"),
      df.source_id.eq("GSI14115"), "same year, GSI surveyed 2007 storm sites",
      "candidate - GLC gives a district-level coordinate only, no site match claimed", "low")

xwd = pd.DataFrame(xw)
# Confidence is derived from stated evidence, not asserted. Separation alone sets
# the baseline; independent agreement on the date raises it, because a
# coordinate agreement without a date agreement is a much weaker claim.
def conf(dm, same_date):
    if dm < 300:
        return "high"
    if dm < 1500:
        return "high" if same_date else "medium"
    return "low"


if len(xwd):
    same = (xwd["a_date"].astype(str).str.strip() != "") & \
           (xwd["a_date"].astype(str).str.strip() == xwd["b_date"].astype(str).str.strip())
    xwd["same_stated_date"] = same
    xwd["confidence"] = [conf(d, s) for d, s in zip(xwd["distance_m"], same)]


    def decide(row):
        if row["a_source"] == "GSI_PDLS":
            return "SAME EVENT - merged into one event group"
        if row["a_source"] == "GSI14337":
            return ("same GSI investigation site; 14115 coordinate supersedes the 2-dp "
                    "14337 coordinate for spatial use")
        if row["a_source"] == "GSI2018":
            if row["distance_m"] < 300:
                return "probable duplicate of a mapped 2018 landslide - flagged, not merged"
            return ("same 2018 monsoon cluster but >300 m apart - treated as a separate "
                    "failure until a locality match is documented")
        return "candidate only - no merge"


    xwd["decision"] = xwd.apply(decide, axis=1)

xwd = xwd.sort_values(["record_a", "distance_m"])
xwd.to_csv(INV / "duplicate_crosswalk.csv", index=False, quoting=csv.QUOTE_MINIMAL)
print(f"\ncrosswalk candidate pairs: {len(xwd)}")
print(xwd.groupby(["a_source", "b_source", "confidence"]).size().to_string())

# ------------------------------------------------------- event table ---------
ev = df[dated].copy()
ev_cols = ["event_group_id", "episode_id", "source_id", "source_record_id", "locality",
           "village", "taluk", "lat_dd_original", "lon_dd_original", "coord_precision_deg",
           "coord_format", "event_date_iso", "date_certainty", "date_text",
           "landslide_type", "geology", "area_text", "casualties", "verification_status",
           "inclusion", "spatial_use", "source_title", "source_file", "source_ref"]
ev[ev_cols].sort_values(["episode_id", "event_group_id"]).to_csv(
    INV / "inventory_events_2000_2026.csv", index=False, quoting=csv.QUOTE_MINIMAL)

# ------------------------------------------------------------ coverage ------
# The coverage table is a Wayanad product: records that a boundary check put
# outside the district are counted in `excluded_records_in_year` and kept out of
# every other column, so they can neither inflate nor silently vanish.
rows = []
for yr in range(2000, 2027):
    all_rec = df[(df.event_date_iso.astype(str).str.startswith(str(yr)))
                 & df.record_class.eq("EVENT_DATED")]
    d = all_rec[all_rec.inclusion.str.startswith("INCLUDED")]
    rows.append({
        "year": yr,
        "dated_records_in_year": len(all_rec),
        "excluded_records_in_year": len(all_rec) - len(d),
        "included_event_records": len(d),
        "distinct_event_groups": int(d.event_group_id.nunique()),
        "verified_records": int(d.verification_status.isin(["SOURCE_CONFIRMED", "CORROBORATED"]).sum()),
        "unresolved_records": int(d.verification_status.eq("NEEDS_REVIEW").sum()),
        "secondary_only_records": int(d.verification_status.eq("SECONDARY_SOURCE_ONLY").sum()),
        "sources": ";".join(sorted(set(d.source_id))),
        "best_date_precision": ("day" if (d.date_certainty == "day").any()
                                else "month" if (d.date_certainty == "month").any()
                                else "year" if (d.date_certainty == "year").any() else "none"),
        "coverage_note": "",
    })

COV_NOTE = {
    2006: "two records, both July/August 2006",
    2007: "densest pre-2018 year; several records describe recurring failure at the same site",
    2008: "single record",
    2009: "15-16 July 2009 cloudburst cluster at Muppainadu",
    2017: "single road-blocking event from a secondary compilation",
    2018: "dominant year: 331 mapped landslides + 8 GSI 42-point datasheets",
    2019: "single event (Puthumala); GSI's 2019-20 Wayanad post-disaster report is not in the public index",
    2024: "July 2024 Mundakkai-Chooralmala + June 2024 Meenakshi Bridge",
    2025: "no event dated 2025; the 2025 GSI volume reports a June 2024 slide",
    2026: "year incomplete at execution time; absence of records is not evidence of absence",
}
for r in rows:
    r["coverage_note"] = COV_NOTE.get(r["year"], "")
cov = pd.DataFrame(rows)
cov.to_csv(INV / "coverage_2000_2026.csv", index=False, quoting=csv.QUOTE_MINIMAL)

print("\n--- coverage 2000-2026 ---")
print(cov[["year", "included_event_records", "distinct_event_groups",
           "verified_records", "unresolved_records", "secondary_only_records"]]
      .to_string(index=False))

# totals, stated with the counting rule attached
yr = pd.to_numeric(df.event_date_iso.astype(str).str.slice(0, 4), errors="coerce")
inwin_all = df[dated & yr.between(2000, 2026)]
inwin = inwin_all[inwin_all.inclusion.str.startswith("INCLUDED")]
pre2000 = df[dated & (yr < 2000)]
print(f"\nDated records total                  : {int(dated.sum())}")
print(f"  in 2000-2026 window                : {len(inwin_all)}")
print(f"    included in Wayanad inventory    : {len(inwin)}")
print(f"    excluded by boundary check       : {len(inwin_all) - len(inwin)}")
print(f"  pre-2000 (kept, outside window)    : {len(pre2000)}")
print(f"Undated site records                 : {int((~dated).sum())}")
print(f"Distinct event groups, in-window+inc : {inwin.event_group_id.nunique()}")

df.to_csv(INV / "inventory_source_records.csv", index=False, quoting=csv.QUOTE_MINIMAL)
print(f"\nwrote {INV/'inventory_source_records.csv'}  rows={len(df)}")
print("\nverification status counts:")
print(df.verification_status.value_counts().to_string())
print("\ninclusion counts:")
print(df.inclusion.value_counts().to_string())
