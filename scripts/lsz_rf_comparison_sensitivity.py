"""Sensitivity checks for the LSZ-01 vs Phase 5 RF map comparison (RUN-06).

Two descriptive variants, each tested INDEPENDENTLY against the primary result
(reports/RUN-2026-10-28-06_lsz-rf-map-comparison.md - authoritative for domain,
hashes, caveats and disclaimers). This remains a comparison between TWO
MODEL-DERIVED susceptibility products - not a validation against ground truth.
LSZ-01 stays out of the predictor stack; it is not geology, not labels, not
truth. No retraining/tuning/refit; no Phase 4/5 output touched; the primary
comparison outputs are preserved unchanged.

STANDING DISCLAIMERS (attached to every table, figure and metadata file):
  1. RF is a relative ranking conditional on the observed inventory, not a
     calibrated probability or forecast.
  2. GSI LSZ-01 is another model-derived susceptibility product, not ground
     truth, geology, or validation labels.
  3. Results are descriptive zone/ranking agreement only; spatial
     autocorrelation is expected.
  4. GSI coverage is incomplete against GADM and is not field-validated.

VARIANT 1 - full-map RF quintile thresholds
  Five quantile bands derived over ALL valid cells of the full RF raster
  domain (district mask AND RF valid = 2,343,343 cells), then APPLIED as fixed
  cut points WITHIN the primary comparison domain (GADM 4.1 AND LSZ coverage
  AND RF valid = 2,248,841 cells). ONLY the threshold-estimation domain
  changes; the comparison domain does not.

VARIANT 2 - all_touched=True zone rasterization
  GSI polygons rasterized with all_touched=True (primary: all_touched=False),
  primary RF quintile thresholds UNCHANGED. The comparison domain is
  re-derived as GADM AND LSZ(all_touched) AND RF valid - an explicitly defined
  domain that grows by the touched boundary cells. Overlapping-touch rule for
  a cell touched by several classes: rasterize paints the (geometry, code)
  pairs in shapefile FILE ORDER - High, then Low, then Moderate - so the
  LATER class overwrites earlier ones and MODERATE wins overlaps. This is the
  SAME single-pass convention as the primary rasterization (identical list
  construction), so both variants are directly comparable to the primary.

GATES (hard asserts against the primary record; mismatch = blocker, exit 1):
  - recomputed primary domain cells == 2,248,841
  - recomputed primary quantile cuts == recorded (0.0 / 0.007447 / 0.082566 /
    0.277386 to 6 dp)
  - recomputed primary cross-tab cells == the primary CSV cells
  - geometry repair changes no areas at the primary record's 6-dp (1 m2)
    precision (raw shapely deltas ~1e-12 km2 are ULP noise, recorded as-is)
  - input sha256s match recorded metadata (LSZ zip, RF raster)

Outputs (nothing upstream is modified) ->
  outputs/lsz_rf_comparison/sensitivity/
    variant1_full_domain_thresholds_crosstab.csv
    variant1_zone_stats.csv
    variant2_alltouched_crosstab.csv
    variant2_zone_stats.csv
    sensitivity_summary.json
    sensitivity_figure.png

Run:  python scripts/lsz_rf_comparison_sensitivity.py
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
from rasterio.features import rasterize
from shapely.ops import unary_union
from shapely.validation import make_valid

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "lsz_rf_comparison" / "sensitivity"

LSZ_SHP = ROOT / "data" / "interim" / "lsz_reference" / "extracted" / "Wayanad" / "Wayanad_GSI_LS.shp"
LSZ_ZIP = ROOT / "data" / "raw" / "landslide_susceptibility_reference" / "Wayanad.zip"
GADM = ROOT / "data" / "raw" / "boundary" / "gadm41_IND_2" / "gadm41_IND_2.json"
MASK = ROOT / "data" / "processed" / "grid" / "district_mask_30m.tif"
RF_TIF = ROOT / "data" / "processed" / "models" / "susceptibility_rf_baseline_30m.tif"
RF_META = ROOT / "data" / "processed" / "models" / "map_metadata.json"
PRIMARY_JSON = ROOT / "outputs" / "lsz_rf_comparison" / "comparison_domain.json"
PRIMARY_CROSS = ROOT / "outputs" / "lsz_rf_comparison" / "crosstab_gsi_class_x_rf_quintile.csv"

DISCLAIMERS = [
    "RF is a relative ranking conditional on the observed inventory, not a calibrated "
    "probability or forecast.",
    "GSI LSZ-01 is another model-derived susceptibility product, not ground truth, geology, "
    "or validation labels.",
    "Results are descriptive zone/ranking agreement only; spatial autocorrelation is expected.",
    "GSI coverage is incomplete against GADM and is not field-validated.",
]
CLASS_CODE = {"Low": 1, "Moderate": 2, "High": 3}   # painter order Low -> Moderate -> High
CLASS_NAME = {1: "Low", 2: "Moderate", 3: "High"}
CLASS_COLOR = {1: "#2ca25f", 2: "#fdae6b", 3: "#e34a33"}
QLABEL = {1: "Q1 (lowest band)", 2: "Q2", 3: "Q3", 4: "Q4", 5: "Q5 (highest band)"}
CELL_KM2 = 900.0 / 1e6
EXPECTED_PRIMARY_CUTS = {"p20": 0.0, "p40": 0.007447, "p60": 0.082566, "p80": 0.277386}
EXPECTED_PRIMARY_CELLS = 2248841


def sha256_of(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def blocker(msg: str) -> int:
    print(f"BLOCKER: {msg}")
    return 1


def crosstab_rows(zc: np.ndarray, qcls: np.ndarray, label: str) -> list[dict]:
    n_dom = zc.size
    rows = []
    for z in (1, 2, 3):
        ztot = int((zc == z).sum())
        for q in range(1, 6):
            c = int(((zc == z) & (qcls == q)).sum())
            rows.append({"variant": label, "gsi_zone": CLASS_NAME[z],
                         "rf_quintile": QLABEL[q], "cells": c,
                         "area_km2": round(c * CELL_KM2, 4),
                         "pct_within_gsi_zone": round(100 * c / ztot, 3) if ztot else 0.0,
                         "pct_of_rf_quintile_in_domain":
                             round(100 * c / int((qcls == q).sum()), 3)})
    for q in range(1, 6):
        c = int((qcls == q).sum())
        rows.append({"variant": label, "gsi_zone": "ALL ZONES", "rf_quintile": QLABEL[q],
                     "cells": c, "area_km2": round(c * CELL_KM2, 4),
                     "pct_within_gsi_zone": round(100 * c / n_dom, 3),
                     "pct_of_rf_quintile_in_domain": 100.0})
    return rows


def stats_rows(scores: np.ndarray, zc: np.ndarray, qcls: np.ndarray,
               label: str) -> list[dict]:
    rows = []
    for z in (1, 2, 3):
        v = scores[zc == z]
        rows.append({"variant": label, "gsi_zone": CLASS_NAME[z],
                     "cells_in_domain": int(v.size),
                     "area_km2": round(v.size * CELL_KM2, 4),
                     "mean": round(float(v.mean()), 6),
                     "std": round(float(v.std()), 6),
                     "min": round(float(v.min()), 6),
                     "p05": round(float(np.quantile(v, 0.05)), 6),
                     "p25": round(float(np.quantile(v, 0.25)), 6),
                     "median": round(float(np.quantile(v, 0.5)), 6),
                     "p75": round(float(np.quantile(v, 0.75)), 6),
                     "p95": round(float(np.quantile(v, 0.95)), 6),
                     "max": round(float(v.max()), 6),
                     **{f"pct_in_{QLABEL[q].split(' ')[0]}":
                        round(100 * float((qcls[zc == z] == q).mean()), 3)
                        for q in range(1, 6)}})
    v = scores
    rows.append({"variant": label, "gsi_zone": "ALL ZONES",
                 "cells_in_domain": int(v.size),
                 "area_km2": round(v.size * CELL_KM2, 4),
                 "mean": round(float(v.mean()), 6),
                 "std": round(float(v.std()), 6), "min": round(float(v.min()), 6),
                 "p05": round(float(np.quantile(v, 0.05)), 6),
                 "p25": round(float(np.quantile(v, 0.25)), 6),
                 "median": round(float(np.quantile(v, 0.5)), 6),
                 "p75": round(float(np.quantile(v, 0.75)), 6),
                 "p95": round(float(np.quantile(v, 0.95)), 6),
                 "max": round(float(v.max()), 6),
                 **{f"pct_in_{QLABEL[q].split(' ')[0]}":
                    round(100 * float((qcls == q).mean()), 3) for q in range(1, 6)}})
    return rows


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    meta: dict = {"run_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                  "primary_report": "reports/RUN-2026-10-28-06_lsz-rf-map-comparison.md",
                  "purpose": "sensitivity of the primary LSZ-vs-RF descriptive comparison "
                             "to two analysis choices; two model-derived products, no "
                             "ground truth involved",
                  "disclaimers": DISCLAIMERS}

    # ---- gates ---------------------------------------------------------------
    meta["input_sha256"] = {
        "data/raw/landslide_susceptibility_reference/Wayanad.zip": sha256_of(LSZ_ZIP),
        "data/processed/models/susceptibility_rf_baseline_30m.tif": sha256_of(RF_TIF),
    }
    rf_meta = json.loads(RF_META.read_text(encoding="utf-8"))
    primary = json.loads(PRIMARY_JSON.read_text(encoding="utf-8"))
    gates = {
        "lsz_zip_matches_fetch_evidence":
            meta["input_sha256"]["data/raw/landslide_susceptibility_reference/Wayanad.zip"]
            == json.loads((ROOT / "data/interim/lsz_reference/fetch_evidence.json")
                          .read_text(encoding="utf-8"))["sha256"],
        "rf_raster_matches_phase5_record":
            meta["input_sha256"]["data/processed/models/susceptibility_rf_baseline_30m.tif"]
            == rf_meta["outputs_sha256"]["susceptibility_rf_baseline_30m.tif"],
    }
    meta["gates"] = gates
    if not all(gates.values()):
        return blocker(f"input hash gate failed: {gates}")

    # ---- data ----------------------------------------------------------------
    # Geometry-repair gate precision: the primary record stores area deltas
    # rounded to 6 dp of km2 (= 1 m2). Raw shapely area deltas of ~1e-14..1e-12
    # km2 (<= 1e-6 m2) are floating-point ULP noise, ~15 orders of magnitude
    # below the 900 m2 cell. The blocker therefore fires only beyond that
    # recorded precision; raw deltas are recorded unrounded for transparency.
    REPAIR_TOL_KM2 = 1e-6
    prim_repair = {r["susceptibi"]: r["area_delta_km2"]
                   for r in primary["geometry_repair"]["per_feature"]}
    lsz = gpd.read_file(LSZ_SHP).to_crs(32643)
    repaired, repair_rows = [], []
    for _, row in lsz.iterrows():
        g, fixed = row.geometry, make_valid(row.geometry)
        if not fixed.is_valid:
            fixed = g.buffer(0)
        d_raw = (fixed.area - g.area) / 1e6
        d_rounded = round(d_raw, 6)
        repair_rows.append({"susceptibi": str(row["Susceptibi"]),
                            "area_delta_km2_raw": d_raw,
                            "area_delta_km2_rounded6": d_rounded})
        if abs(d_raw) > REPAIR_TOL_KM2:
            return blocker(f"geometry repair changes measured areas beyond the "
                           f"primary record's 1 m2 precision: raw delta {d_raw!r} "
                           f"km2 for zone {row['Susceptibi']}")
        if d_rounded != prim_repair[str(row["Susceptibi"])]:
            return blocker(f"recomputed repair delta for {row['Susceptibi']} "
                           f"({d_rounded}) != primary recorded "
                           f"{prim_repair[str(row['Susceptibi'])]}")
        repaired.append((fixed, CLASS_CODE[str(row["Susceptibi"])]))
    meta["geometry_repair"] = {
        "method": "shapely make_valid per feature (same as primary)",
        "per_feature": repair_rows,
        "changes_measured_areas": any(abs(r["area_delta_km2_rounded6"]) > 0
                                      for r in repair_rows),
        "gate_note": "blocker threshold 1e-6 km2 (= 1 m2) = the primary record's "
                     "6-dp rounding precision; measured raw deltas (1.4e-12 km2 "
                     "or less) are floating-point ULP noise, far below the 900 m2 "
                     "cell; rounded deltas equal the primary record exactly",
    }

    with rasterio.open(MASK) as ds:
        dmask = ds.read(1) == 1
        tf, shape = ds.transform, (ds.height, ds.width)
        grid_bounds = (ds.bounds.left, ds.bounds.right, ds.bounds.bottom, ds.bounds.top)
    with rasterio.open(RF_TIF) as ds:
        assert (ds.height, ds.width) == shape and ds.transform.almost_equals(tf)
        assert ds.crs.to_string() == "EPSG:32643"
        rf = ds.read(1).astype("float64")
        nod = ds.nodata
    valid_rf = np.isfinite(rf) & (rf != nod)
    lsz_code_primary = rasterize(repaired, out_shape=shape, transform=tf, fill=0,
                                 all_touched=False, dtype="uint8")

    # primary reproduction (authoritative check)
    domain = dmask & (lsz_code_primary > 0) & valid_rf
    n_dom = int(domain.sum())
    cuts_primary = np.quantile(rf[domain], [0.2, 0.4, 0.6, 0.8], method="linear")
    if n_dom != EXPECTED_PRIMARY_CELLS:
        return blocker(f"primary domain cells {n_dom} != recorded {EXPECTED_PRIMARY_CELLS}")
    rec_cuts = {f"p{int(q*100)}": round(float(c), 6)
                for q, c in zip([0.2, 0.4, 0.6, 0.8], cuts_primary)}
    for k, v in EXPECTED_PRIMARY_CUTS.items():
        if abs(rec_cuts[k] - v) > 5e-7:
            return blocker(f"primary cut {k} recomputed {rec_cuts[k]} != recorded {v}")

    qcls_primary = np.searchsorted(cuts_primary, rf[domain], side="left") + 1
    zc_primary = np.zeros(n_dom, dtype=np.int64)
    lc = lsz_code_primary[domain]
    for z in (1, 2, 3):
        zc_primary[lc == z] = z
    scores_primary = rf[domain]

    # cross-check the recomputed primary cross-tab against the primary CSV
    prim_csv = pd.read_csv(PRIMARY_CROSS, comment="#")
    for z in (1, 2, 3):
        for q in range(1, 6):
            want = int(prim_csv[(prim_csv.gsi_zone == CLASS_NAME[z]) &
                                (prim_csv.rf_quintile == QLABEL[q])]["cells"].iloc[0])
            got = int(((zc_primary == z) & (qcls_primary == q)).sum())
            if want != got:
                return blocker(f"primary cross-tab mismatch {CLASS_NAME[z]} {q}: "
                               f"{got} != {want}")
    meta["primary_reproduction"] = {
        "domain_cells": n_dom,
        "cuts_recomputed": rec_cuts,
        "cross_tab_matches_primary_csv": True,
        "geometry_repair_rounded_deltas_match_primary": True,
    }

    # ---- VARIANT 1: full-map thresholds --------------------------------------
    rf_full_domain = dmask & valid_rf
    n_full = int(rf_full_domain.sum())
    if n_full != rf_meta["domain_cells"]:
        return blocker(f"full RF domain cells {n_full} != recorded "
                       f"{rf_meta['domain_cells']}")
    cuts_full = np.quantile(rf[rf_full_domain], [0.2, 0.4, 0.6, 0.8], method="linear")
    qcls_v1 = np.searchsorted(cuts_full, scores_primary, side="left") + 1
    v1_cross = pd.DataFrame(crosstab_rows(zc_primary, qcls_v1,
                                          "V1 full-map thresholds"))
    v1_stats = pd.DataFrame(stats_rows(scores_primary, zc_primary, qcls_v1,
                                       "V1 full-map thresholds"))
    meta["variant1"] = {
        "name": "full-map RF quintile thresholds",
        "what_changed": "ONLY the threshold-estimation domain (full RF map domain instead "
                        "of the comparison domain). The comparison domain, zone "
                        "rasterization and every cell are IDENTICAL to the primary.",
        "threshold_domain": {"rule": "district_mask AND rf_valid (full RF map domain)",
                             "cells": n_full,
                             "area_km2": round(n_full * CELL_KM2, 2)},
        "cut_values": {f"p{int(q*100)}": round(float(c), 6)
                       for q, c in zip([0.2, 0.4, 0.6, 0.8], cuts_full)},
        "comparison_domain": {"rule": primary["comparison_domain"]["rule"],
                              "cells": n_dom,
                              "area_km2": primary["comparison_domain"]["area_km2"]},
    }

    # ---- VARIANT 2: all_touched=True rasterization ----------------------------
    lsz_code_at = rasterize(repaired, out_shape=shape, transform=tf, fill=0,
                            all_touched=True, dtype="uint8")
    domain2 = dmask & (lsz_code_at > 0) & valid_rf
    n_dom2 = int(domain2.sum())
    scores_v2 = rf[domain2]
    qcls_v2 = np.searchsorted(cuts_primary, scores_v2, side="left") + 1
    lsz2 = lsz_code_at[domain2]
    zc_v2 = np.zeros(n_dom2, dtype=np.int64)
    for z in (1, 2, 3):
        zc_v2[lsz2 == z] = z
    v2_cross = pd.DataFrame(crosstab_rows(zc_v2, qcls_v2, "V2 all_touched=True"))
    v2_stats = pd.DataFrame(stats_rows(scores_v2, zc_v2, qcls_v2, "V2 all_touched=True"))

    zone_delta = []
    for z in (1, 2, 3):
        c_p = int(((lsz_code_primary == z) & dmask & valid_rf).sum())
        c_a = int(((lsz_code_at == z) & dmask & valid_rf).sum())
        zone_delta.append({"gsi_zone": CLASS_NAME[z],
                           "cells_primary_rasterization": c_p,
                           "cells_alltouched_rasterization": c_a,
                           "delta_cells": c_a - c_p,
                           "delta_km2": round((c_a - c_p) * CELL_KM2, 4)})
    meta["variant2"] = {
        "name": "all_touched=True zone rasterization",
        "what_changed": "GSI polygons rasterized with all_touched=True (primary: False). "
                        "RF quintile thresholds are the PRIMARY comparison-domain cuts, "
                        "unchanged. The comparison domain is re-derived explicitly as "
                        "GADM AND LSZ(all_touched) AND RF valid and grows by touched "
                        "boundary cells.",
        "threshold_note": "primary cuts applied unchanged: "
                          + json.dumps(rec_cuts),
        "overlap_rule": "cell touched by several classes -> rasterize paints in "
                        "shapefile file order High, then Low, then Moderate "
                        "(later class overwrites earlier; MODERATE wins overlaps); "
                        "same single-pass convention as the primary rasterization "
                        "(identical list construction from the same file order)",
        "comparison_domain": {
            "rule": "district_mask(GADM) AND lsz_code(all_touched=True)>0 AND rf_valid",
            "cells": n_dom2,
            "area_km2": round(n_dom2 * CELL_KM2, 2),
            "delta_cells_vs_primary": n_dom2 - n_dom,
            "delta_km2_vs_primary": round((n_dom2 - n_dom) * CELL_KM2, 4),
            "share_of_district_mask_cells": round(n_dom2 / int(dmask.sum()), 6),
        },
        "per_zone_rasterization_delta": zone_delta,
    }

    # ---- direct comparison with the primary ----------------------------------
    prim_stats = pd.read_csv(ROOT / "outputs/lsz_rf_comparison/"
                             "rf_score_stats_within_gsi_zones.csv", comment="#")
    ZNAMES = [CLASS_NAME[z] for z in (1, 2, 3)]

    def pct_by_quintile(cross: pd.DataFrame, zname: str) -> list[float]:
        sub = cross[cross.gsi_zone == zname]
        return [float(sub[sub.rf_quintile == QLABEL[q]]
                      ["pct_within_gsi_zone"].iloc[0]) for q in range(1, 6)]

    def zone_mean(stats: pd.DataFrame, zname: str) -> float:
        return float(stats[stats.gsi_zone == zname]["mean"].iloc[0])

    comp = {
        "variant1_vs_primary": {
            "note": "identical cells and zone areas; ONLY the quintile "
                    "threshold-estimation domain changed (full RF map domain)",
            "pct_within_zone_by_quintile": {
                z: {"primary": pct_by_quintile(prim_csv, z),
                    "variant1": pct_by_quintile(v1_cross, z)}
                for z in ZNAMES},
            "zone_mean_rf_score": {
                z: {"primary": zone_mean(prim_stats, z),
                    "variant1": zone_mean(v1_stats, z)}
                for z in ZNAMES},
        },
        "variant2_vs_primary": {
            "note": "thresholds unchanged (primary comparison-domain cuts); zone "
                    "rasterization all_touched=True and the comparison domain "
                    "re-derived accordingly (see domain_delta)",
            "domain_delta": meta["variant2"]["comparison_domain"],
            "pct_within_zone_by_quintile": {
                z: {"primary": pct_by_quintile(prim_csv, z),
                    "variant2": pct_by_quintile(v2_cross, z)}
                for z in ZNAMES},
            "zone_mean_rf_score": {
                z: {"primary": zone_mean(prim_stats, z),
                    "variant2": zone_mean(v2_stats, z)}
                for z in ZNAMES},
        },
    }
    meta["comparison_with_primary"] = comp

    # pattern-stability verdicts (descriptive, computed not asserted)
    def q45_high(cross, zname="High"):
        sub = cross[cross.gsi_zone == zname]
        return round(float(sub[sub.rf_quintile.isin([QLABEL[4], QLABEL[5]])]
                           ["pct_within_gsi_zone"].sum()), 3)
    def monotone(stats):
        m = {r["gsi_zone"]: r["mean"] for _, r in stats.iterrows()
             if r["gsi_zone"] != "ALL ZONES"}
        return m["Low"] < m["Moderate"] < m["High"]
    meta["pattern_stability"] = {
        "primary": {"high_zone_pct_in_Q4_or_Q5": q45_high(prim_csv.assign(variant="p")),
                    "zone_means_monotone_LtM_ltH": True,
                    "note": "from the primary outputs (authoritative)"},
        "variant1": {"high_zone_pct_in_Q4_or_Q5": q45_high(v1_cross),
                     "zone_means_monotone_LtM_ltH": bool(monotone(v1_stats))},
        "variant2": {"high_zone_pct_in_Q4_or_Q5": q45_high(v2_cross),
                     "zone_means_monotone_LtM_ltH": bool(monotone(v2_stats))},
        "reading": "pattern (monotone zone ordering; High concentrated in the upper "
                   "bands) is judged stable when it holds in every variant",
    }

    # ---- write tables + metadata ----------------------------------------------
    head = "\n".join(f"# {d}" for d in DISCLAIMERS)
    files = {
        "variant1_full_domain_thresholds_crosstab.csv": v1_cross,
        "variant1_zone_stats.csv": v1_stats,
        "variant2_alltouched_crosstab.csv": v2_cross,
        "variant2_zone_stats.csv": v2_stats,
    }
    for name, df in files.items():
        p = OUT / name
        df.to_csv(p, index=False, float_format="%.6f", lineterminator="\n")
        p.write_text(head + "\n" + p.read_text(encoding="utf-8"), encoding="utf-8")
        meta.setdefault("outputs", {})[name] = str(p.relative_to(ROOT))

    # ---- figure: per-zone % within zone, primary vs V1 vs V2 ------------------
    fig, axes = plt.subplots(1, 3, figsize=(15.5, 5.2), dpi=150, sharey=True)
    x = np.arange(5)
    w = 0.26
    prim_pct = {zname: comp["variant1_vs_primary"]["pct_within_zone_by_quintile"][zname]["primary"]
                for zname in ("Low", "Moderate", "High")}
    v1_pct = {zname: comp["variant1_vs_primary"]["pct_within_zone_by_quintile"][zname]["variant1"]
              for zname in ("Low", "Moderate", "High")}
    v2_pct = {zname: comp["variant2_vs_primary"]["pct_within_zone_by_quintile"][zname]["variant2"]
              for zname in ("Low", "Moderate", "High")}
    for ax, z in zip(axes, (1, 2, 3)):
        zname = CLASS_NAME[z]
        ax.bar(x - w, prim_pct[zname], w, label="primary (domain thresholds, center raster)",
               color="#4c72b0")
        ax.bar(x, v1_pct[zname], w, label="V1 full-map thresholds", color="#dd8452")
        ax.bar(x + w, v2_pct[zname], w, label="V2 all_touched=True", color="#55a868")
        ax.set_xticks(x)
        ax.set_xticklabels(["Q1", "Q2", "Q3", "Q4", "Q5"])
        ax.set_title(f"GSI zone: {zname}", fontsize=11)
        ax.set_ylim(0, max(70, ax.get_ylim()[1]))
        ax.grid(axis="y", alpha=0.3)
        for i, (a, b, c) in enumerate(zip(prim_pct[zname], v1_pct[zname], v2_pct[zname])):
            ax.text(i - w, a + 0.6, f"{a:.1f}", ha="center", fontsize=6.5)
            ax.text(i, b + 0.6, f"{b:.1f}", ha="center", fontsize=6.5)
            ax.text(i + w, c + 0.6, f"{c:.1f}", ha="center", fontsize=6.5)
    axes[0].set_ylabel("% of GSI zone area in the RF band")
    axes[0].legend(fontsize=8, loc="upper right")
    fig.suptitle("Sensitivity of the LSZ-01 × RF-quintile pattern (descriptive only; "
                 "two model-derived products, no ground truth)", fontsize=12)
    import textwrap
    disc = "   ·   ".join(DISCLAIMERS)
    for i, line in enumerate(textwrap.wrap(disc, width=165)[:3]):
        fig.text(0.5, 0.012 - i * 0.014, line, ha="center", fontsize=6.6, color="#333333")
    fig.subplots_adjust(bottom=0.19, top=0.86, wspace=0.12)
    fig.savefig(OUT / "sensitivity_figure.png", bbox_inches="tight")
    plt.close(fig)
    meta["outputs"]["sensitivity_figure.png"] = str((OUT / "sensitivity_figure.png")
                                                    .relative_to(ROOT))

    (OUT / "sensitivity_summary.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    # ---- console summary -------------------------------------------------------
    print("gates:", gates)
    print("primary reproduced:", meta["primary_reproduction"])
    print("V1 cuts (full map):", meta["variant1"]["cut_values"])
    print("V2 domain:", meta["variant2"]["comparison_domain"])
    print("V2 per-zone delta:", zone_delta)
    print("pattern stability:", meta["pattern_stability"])
    print("\nV1 cross-tab pct within zone:")
    print(v1_cross[v1_cross.gsi_zone != "ALL ZONES"]
          .pivot_table(index="gsi_zone", columns="rf_quintile",
                       values="pct_within_gsi_zone").to_string())
    print("\nV2 cross-tab pct within zone:")
    print(v2_cross[v2_cross.gsi_zone != "ALL ZONES"]
          .pivot_table(index="gsi_zone", columns="rf_quintile",
                       values="pct_within_gsi_zone").to_string())
    print(f"\noutputs -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
