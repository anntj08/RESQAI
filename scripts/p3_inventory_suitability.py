"""Phase 3 Stage 9 - inventory suitability for spatial analysis.

The Phase 2 inventory is the authoritative input and is NOT modified. This script
adds an explicit, auditable per-record judgement of whether a record may be used
as a point label, and why.

Two corrections/additions to the Phase 2 record, both written into new columns
rather than into the Phase 2 tables:

1. **Printed-precision defect.** GSI PDLS 2024 row 1 prints whole-second DMS
   (``11027'46"N / 76008'03"E``) but carries ``coord_precision_deg = 0.000003``
   (0.01 arc-second). The printed coordinate only supports 1 arc-second
   (0.000278). Corrected here in ``coord_precision_deg_verified``; the Phase 2
   value is left untouched so the published numbers stay intact.

2. **The "44 two-decimal records" are not 44 events.** They are 35 undated GSI
   14337 site rows plus 9 NASA GLC rows, 7 of which are outside the district.
   Only **2** dated in-window records carry a 2-decimal coordinate, and one of
   those two is a district-level centroid rather than a site. This script states
   that per record instead of leaving it as a headline.

Uncertainty model
-----------------
    precision_radius_m       = 0.5 * printed_step_deg * 111320      (half a last digit)
    precision_radius_diag_m  = precision_radius_m * sqrt(2)         (conservative)
    positional_uncertainty_m = max(precision_radius_m, source_accuracy_floor_m)

The floor is an ASSUMPTION about how accurate the source can be regardless of how
many digits it prints, and is labelled as such column by column. It is not a
measured accuracy.

Outputs (data/processed/inventory/):
  inventory_spatial_suitability.csv     468 rows, one per source record
  event_group_point_status.csv          one row per event group
  inventory_suitability_summary.json

Run: python scripts/p3_inventory_suitability.py
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INV = ROOT / "data" / "processed" / "inventory"
SRC = INV / "inventory_source_records.csv"
XW = INV / "duplicate_crosswalk.csv"
OUT = INV

M_PER_DEG_LAT = 111320.0

# Assumed minimum achievable accuracy per source (metres). These are ASSUMPTIONS
# about the source, used only where the printed precision would otherwise imply
# an implausibly small error.
SOURCE_FLOOR_M = {
    "GSI14115": 10.0,   # field investigation; toposheet / handheld GPS plotting
    "GSI_PDLS": 10.0,
    "LIT2025": 10.0,    # compiled from a paper, not surveyed by this project
    "GSI2018": 10.0,
    "KER2018": 30.0,    # mapped landslide centroids; 5 dp is file precision only
    "GSI14768": 50.0,   # coordinates read off 1:50,000 plates
    "GSI14337": 0.0,    # printed 2 dp dominates (787 m)
    "NASA_GLC": 0.0,    # printed 2 dp dominates (787 m)
}
FLOOR_RATIONALE = {
    "GSI14115": "ASSUMPTION: field-survey plotting accuracy, not a measured error",
    "GSI_PDLS": "ASSUMPTION: field-survey plotting accuracy, not a measured error",
    "LIT2025": "ASSUMPTION: compiled coordinate, not surveyed by this project",
    "GSI2018": "ASSUMPTION: field-survey plotting accuracy, not a measured error",
    "KER2018": "ASSUMPTION: 5-decimal storage is file precision; the Phase 2 report "
               "explicitly warns it is not survey accuracy for mapped centroids",
    "GSI14768": "ASSUMPTION: 1:50,000 plate reading, ~0.5 mm on paper = 25 m",
    "GSI14337": "printed precision already exceeds any plausible accuracy floor",
    "NASA_GLC": "printed precision already exceeds any plausible accuracy floor",
}

# Printed-precision corrections, with the verbatim source text as evidence.
# Keyed by the real `source_record_id` in the consolidated table. (The Phase 2
# working label for this record was "GSI_PDLS/p95"; keying the dict on that label
# silently matched nothing, so the correction was reported in the summary but
# never applied to any row.  Caught by scripts/p3_check_consistency.py.)
PRECISION_FIX = {
    "KER/WYD/58A03/2024/01": (
        0.000278,
        "Phase 2 label GSI_PDLS/p95; printed 11027'46\"N / 76008'03\"E = whole-second "
        "DMS, so 1 arc-second (0.000278 deg), not the stored 0.01 arc-second",
    ),
}


def classify(u: float) -> str:
    if u <= 100:
        return "A_PRECISE_LE_100M"
    if u <= 300:
        return "B_MODERATE_100_300M"
    if u <= 800:
        return "C_COARSE_300_800M"
    return "D_UNUSABLE_GT_800M"


def main() -> None:
    inv = pd.read_csv(SRC)
    xw = pd.read_csv(XW)
    n0 = len(inv)
    assert n0 == 468, f"expected 468 source records, got {n0}"

    # ---- 1. crosswalk-derived superseding coordinate ------------------------
    # Only accept a superseding 14115 coordinate where the measured separation is
    # within 1,500 m. Two pairs sit at 7,429 m and 16,579 m: a 2-dp village
    # centroid cannot be resolved to a specific site at those distances.
    g37 = xw[(xw["a_source"] == "GSI14337") & (xw["b_source"] == "GSI14115")]
    accept = g37[g37["distance_m"] <= 1500.0]
    reject = g37[g37["distance_m"] > 1500.0]
    supersede = dict(zip(accept["record_a"], accept["record_b"]))
    sup_dist = dict(zip(accept["record_a"], accept["distance_m"]))
    assert len(accept) == 33 and len(reject) == 2, (len(accept), len(reject))

    # ---- 2. precision verification -----------------------------------------
    rows = []
    for _, r in inv.iterrows():
        sid = r["source_id"]
        prec_stored = float(r["coord_precision_deg"])
        note = ""
        prec = prec_stored
        rid = r["source_record_id"]
        if rid in PRECISION_FIX:
            prec, note = PRECISION_FIX[rid]
        elif prec_stored != prec_stored:  # NaN
            prec, note = np.nan, "no coordinate precision recorded"

        if np.isfinite(prec):
            r_axis = 0.5 * prec * M_PER_DEG_LAT
            r_diag = r_axis * np.sqrt(2)
            floor = SOURCE_FLOOR_M.get(sid, 0.0)
            u = max(r_axis, floor)
        else:
            r_axis = r_diag = u = np.nan
        pclass = classify(u) if np.isfinite(u) else "E_NO_COORDINATE"

        # ---- 3. label role --------------------------------------------------
        dated = pd.notna(r["event_date_iso"])
        year = pd.to_datetime(r["event_date_iso"], errors="coerce").year if dated else None
        in_window = bool(dated and 2000 <= year <= 2026)
        inclusion = r["inclusion"]

        if inclusion == "EXCLUDED_OUT_OF_DISTRICT":
            role = "EXCLUDED_NOT_IN_DISTRICT"
        elif not dated:
            role = "SITE_EVIDENCE_UNDATED"
        elif not in_window:
            role = "HISTORICAL_PRE_2000"
        else:
            role = "EVENT_POINT_IN_WINDOW"

        # ---- 4. spatial use recommendation ----------------------------------
        is_centroid = str(r["locality"]).strip().lower() in {"wayanad", "wayanad district"}
        if role == "EXCLUDED_NOT_IN_DISTRICT":
            use = "exclude_not_in_district"
            reason = "outside the GADM polygon by the Phase 2 measured 5 km rule"
        elif r["verification_status"] == "NEEDS_REVIEW":
            use = "exclude_until_corrected"
            reason = "printed longitude puts the site ~77 km east, in Tamil Nadu; retained as published"
        elif str(r["spatial_use"]) == "review_before_spatial_use":
            use = "review_boundary_uncertain"
            reason = ("Phase 2 flagged this record: it lies outside the GADM polygon by "
                      "212-2,836 m. The GADM/OSM outlines disagree by ~750 m median, so "
                      "membership is a boundary-definition question, not a coordinate error")
        elif is_centroid:
            use = "exclude_district_centroid"
            reason = "locality is 'Wayanad': the coordinate is a district reference point, not a site"
        elif pclass.startswith("D") and rid in supersede:
            use = "use_superseding_coordinate"
            reason = (f"2-decimal village centroid; the matched GSI 14115 site is "
                      f"{sup_dist[rid]:.0f} m away and supplies a usable coordinate")
        elif pclass.startswith("D"):
            use = "retain_as_published_no_spatial_use"
            reason = ("2-decimal coordinate with no verified match to a better source; "
                      "kept for historical reporting only")
        elif pclass.startswith("C"):
            use = "review_widen_label"
            reason = ("300-800 m uncertainty: only usable if the label is widened to a "
                      "neighbourhood or the record is dropped")
        else:
            use = "point_label_ok"
            reason = (f"{pclass.split('_')[0]}-class precision "
                      f"({u:.0f} m modelled uncertainty)")

        rows.append({
            "source_record_id": rid,
            "source_id": sid,
            "locality": r["locality"],
            "village": r["village"],
            "lat_original": r["lat_dd_original"],
            "lon_original": r["lon_dd_original"],
            "coord_precision_deg_stored": prec_stored,
            "coord_precision_deg_verified": prec,
            "precision_correction_note": note,
            "precision_radius_m": None if not np.isfinite(r_axis) else round(float(r_axis), 2),
            "precision_radius_diag_m": None if not np.isfinite(r_diag) else round(float(r_diag), 2),
            "source_accuracy_floor_m": SOURCE_FLOOR_M.get(sid, 0.0),
            "accuracy_floor_basis": FLOOR_RATIONALE.get(sid, ""),
            "positional_uncertainty_m": None if not np.isfinite(u) else round(float(u), 1),
            "precision_class": pclass,
            "inclusion": inclusion,
            "inside_wayanad": r["inside_wayanad"],
            "dist_outside_boundary_m": r["dist_outside_boundary_m"],
            "verification_status": r["verification_status"],
            "event_date_iso": r["event_date_iso"],
            "date_certainty": r["date_certainty"],
            "event_year": year,
            "event_group_id": r["event_group_id"],
            "label_role": role,
            "spatial_suitability_use": use,
            "superseded_by": supersede.get(rid, ""),
            "superseding_distance_m": sup_dist.get(rid),
            "reason": reason,
        })

    out = pd.DataFrame(rows)

    # A correction whose key matches no row is a silent no-op, which is exactly how
    # the first version of this table shipped a correction it had not applied.
    missing = sorted(set(PRECISION_FIX) - set(out["source_record_id"]))
    assert not missing, f"precision-fix keys matched no record: {missing}"
    fixed = out[out["source_record_id"].isin(PRECISION_FIX)]
    assert (fixed["coord_precision_deg_verified"]
            == fixed["source_record_id"].map(lambda k: PRECISION_FIX[k][0])).all()
    assert fixed["precision_correction_note"].str.len().gt(0).all()

    # identical-coordinate groups (2-dp rounding collapses distinct records)
    key = out["lat_original"].round(6).astype(str) + "," + out["lon_original"].round(6).astype(str)
    sizes = key.map(key.value_counts())
    out["coord_duplicate_group_size"] = sizes.astype(int)
    out["shares_coordinate_with_other_record"] = sizes > 1

    # ---- 5. event-group view ------------------------------------------------
    ev = out[out["label_role"] == "EVENT_POINT_IN_WINDOW"]
    grp = ev.groupby("event_group_id").agg(
        n_records=("source_record_id", "size"),
        best_precision_class=("precision_class", "min"),
        best_uncertainty_m=("positional_uncertainty_m", "min"),
        n_usable_points=("spatial_suitability_use",
                         lambda s: int((s == "point_label_ok").sum())),
        uses_superseding=("spatial_suitability_use",
                          lambda s: int((s == "use_superseding_coordinate").sum())),
        event_year=("event_year", "first"),
        date_certainty=("date_certainty", "first"),
    ).reset_index()
    grp["has_usable_point_label"] = grp["n_usable_points"] > 0
    grp.to_csv(OUT / "event_group_point_status.csv", index=False)

    # ---- 6. summary ---------------------------------------------------------
    def counts(col):
        return {str(k): int(v) for k, v in out[col].value_counts().sort_index().items()}

    inw = out[out["label_role"] == "EVENT_POINT_IN_WINDOW"]
    rep = {
        "input": {"path": str(SRC.relative_to(ROOT)), "records": n0,
                  "sha256": hashlib.sha256(SRC.read_bytes()).hexdigest()},
        "phase2_tables_modified": False,
        "counts_by_precision_class": counts("precision_class"),
        "counts_by_spatial_use": counts("spatial_suitability_use"),
        "counts_by_label_role": counts("label_role"),
        "in_window_records": int(len(inw)),
        "in_window_by_precision_class": {
            str(k): int(v) for k, v in inw["precision_class"].value_counts().sort_index().items()},
        "two_decimal_records": {
            "n": int((out["coord_precision_deg_stored"] == 0.01).sum()),
            "by_source": {str(k): int(v) for k, v in
                          out[out["coord_precision_deg_stored"] == 0.01]
                          ["source_id"].value_counts().items()},
            "n_dated_in_window": int((inw["coord_precision_deg_stored"] == 0.01).sum()),
            "dated_in_window_records": inw[inw["coord_precision_deg_stored"] == 0.01]
            [["source_record_id", "locality", "spatial_suitability_use"]].to_dict("records"),
            "unique_coordinates_among_the_35_gsi14337":
                int(out[out["source_id"] == "GSI14337"]
                    [["lat_original", "lon_original"]].drop_duplicates().shape[0]),
            "gsi14337_records_sharing_a_coordinate":
                int((out[out["source_id"] == "GSI14337"]["shares_coordinate_with_other_record"]
                     ).sum()),
        },
        "crosswalk_resolution": {
            "pairs_considered": int(len(g37)),
            "accepted_le_1.5km": int(len(accept)),
            "rejected_gt_1.5km": int(len(reject)),
            "rejected_detail": reject[["record_a", "record_b", "distance_m", "confidence"]]
            .to_dict("records"),
            "distinct_14115_targets": int(accept["record_b"].nunique()),
            "note": "33 accepted rows map onto fewer than 33 distinct 14115 sites, because "
                    "several 2-dp rows share a rounded coordinate. Accepted rows are "
                    "therefore NOT 33 independent new locations.",
        },
        "precision_corrections": [
            {"source_record_id": k, "corrected_to_deg": v[0], "evidence": v[1]}
            for k, v in PRECISION_FIX.items()],
        "event_groups": {
            "n_groups": int(len(grp)),
            "groups_with_at_least_one_point_label": int(grp["has_usable_point_label"].sum()),
            "groups_without_a_point_label": int((~grp["has_usable_point_label"]).sum()),
            "groups_by_best_precision_class": {
                str(k): int(v) for k, v in grp["best_precision_class"].value_counts().items()},
            "groups_2018": int((grp["event_year"] == 2018).sum()),
            "groups_non_2018": int((grp["event_year"] != 2018).sum()),
        },
        "uncertainty_model": {
            "precision_radius_m": "0.5 * printed_step_deg * 111320",
            "diag": "radius * sqrt(2)",
            "positional_uncertainty_m": "max(precision_radius_m, source_accuracy_floor_m)",
            "floors_are_assumptions": True,
            "classes": {"A": "<=100 m", "B": "100-300 m", "C": "300-800 m",
                        "D": ">800 m", "E": "no coordinate"},
        },
        "not_done": [
            "no coordinate was snapped, relocated, rounded further or deleted",
            "no records were merged; event_group_id is preserved as Phase 2 set it",
            "no undated record was promoted to an event",
            "no date was imputed",
        ],
    }

    out.to_csv(OUT / "inventory_spatial_suitability.csv", index=False)
    (OUT / "inventory_suitability_summary.json").write_text(json.dumps(rep, indent=2),
                                                           encoding="utf-8")
    print(json.dumps(rep, indent=2))
    print("\n" + out.groupby(["label_role", "precision_class"]).size().to_string())


if __name__ == "__main__":
    main()
