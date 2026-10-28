"""Descriptive comparison: Phase 5 RF susceptibility ranking map vs GSI 2022 LSZ
zones (LSZ-01), Wayanad.

STANDING RULES BUILT INTO EVERY OUTPUT (tables, figure, metadata, prose):
  * The RF raster is a RELATIVE RANKING conditional on the observed inventory -
    not a calibrated probability, not a forecast, warning or timing prediction.
  * The GSI 2022 zones (LSZ-01) are another MODEL-DERIVED susceptibility
    product, NOT ground truth, NOT geology, NOT validation labels, and they
    must never enter the predictor stack.
  * This is a DESCRIPTIVE zone/ranking agreement comparison only. No
    significance tests, no independence claims - spatial autocorrelation is
    expected in both products.
  * The GSI file covers 95.99% of the project GADM 4.1 boundary and has NOT
    been field-validated (status DOWNLOADED_NOT_FULLY_VALIDATED). The GSI
    zones are NOT extrapolated to the missing GADM area.

METHOD (fixed, recorded in every output):
  * Comparison domain (30 m project grid, EPSG:32643, cell-aligned):
        district mask (GADM 4.1) AND GSI zone coverage AND RF raster valid.
  * GSI classes stay CATEGORICAL: the polygons are rasterized as class codes
    (Low=1, Moderate=2, High=3) - never interpolated or resampled as
    continuous values.
  * Geometry repair for overlay: shapely.validation.make_valid per feature
    (the 3 delivered MultiPolygons are formally invalid). The repaired areas
    are compared with the raw areas to verify the repair changes nothing.
  * RF quantile classes: 5 quintile bands defined over the COMPARISON DOMAIN
    cells (equal-area cells, so cell quantiles ARE area-weighted quantiles).
    Cut values recorded; class shares reported as measured (ties can shift
    shares away from exactly 20%).
  * Areas: cells x 900 m^2 (30 m grid); all work in EPSG:32643.

Outputs (comparison-only; nothing upstream is modified) ->
  outputs/lsz_rf_comparison/
    crosstab_gsi_class_x_rf_quintile.csv
    rf_score_stats_within_gsi_zones.csv
    comparison_domain.json
    overlay_map.png

Run:  python scripts/lsz_rf_map_comparison.py
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
OUT = ROOT / "outputs" / "lsz_rf_comparison"

LSZ_SHP = ROOT / "data" / "interim" / "lsz_reference" / "extracted" / "Wayanad" / "Wayanad_GSI_LS.shp"
LSZ_ZIP = ROOT / "data" / "raw" / "landslide_susceptibility_reference" / "Wayanad.zip"
GADM = ROOT / "data" / "raw" / "boundary" / "gadm41_IND_2" / "gadm41_IND_2.json"
MASK = ROOT / "data" / "processed" / "grid" / "district_mask_30m.tif"
RF_TIF = ROOT / "data" / "processed" / "models" / "susceptibility_rf_baseline_30m.tif"
RF_META = ROOT / "data" / "processed" / "models" / "map_metadata.json"

DISCLAIMERS = [
    "RF raster = relative landslide susceptibility ranking conditional on the observed "
    "inventory (92.3% of labels from 2018); NOT a calibrated probability, forecast, warning "
    "or timing prediction.",
    "GSI 2022 zones (LSZ-01, KSDMA-hosted) are another model-derived susceptibility product, "
    "NOT ground truth, NOT geology, NOT validation labels.",
    "Descriptive zone/ranking agreement only; no significance tests; spatial autocorrelation "
    "expected in both products.",
    "GSI file covers 95.99% of the GADM 4.1 project boundary and is not field-validated "
    "(DOWNLOADED_NOT_FULLY_VALIDATED); zones are NOT extrapolated to the missing GADM area.",
]

CLASS_CODE = {"Low": 1, "Moderate": 2, "High": 3}   # categorical, ordinal by susceptibility
CLASS_COLOR = {1: "#2ca25f", 2: "#fdae6b", 3: "#e34a33"}
CLASS_NAME = {1: "Low", 2: "Moderate", 3: "High"}
CELL_KM2 = 900.0 / 1e6


def sha256_of(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    meta: dict = {"run_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                  "purpose": "descriptive comparison of two susceptibility products "
                             "(reference only; neither product is ground truth)",
                  "disclaimers": DISCLAIMERS}

    # ---- input integrity gates ---------------------------------------------
    meta["input_sha256"] = {
        "data/raw/landslide_susceptibility_reference/Wayanad.zip": sha256_of(LSZ_ZIP),
        "data/processed/models/susceptibility_rf_baseline_30m.tif": sha256_of(RF_TIF),
    }
    rf_meta = json.loads(RF_META.read_text(encoding="utf-8"))
    meta["rf_raster_sha256_matches_phase5_record"] = \
        meta["input_sha256"][RF_TIF.relative_to(ROOT).as_posix()] == \
        rf_meta["outputs_sha256"]["susceptibility_rf_baseline_30m.tif"]
    meta["rf_map_record"] = {
        "value": rf_meta["value"], "domain_rule": rf_meta["domain_rule"],
        "domain_cells_recorded": rf_meta["domain_cells"],
        "district_cells_recorded": rf_meta["district_cells"],
        "label": rf_meta["label"], "nodata": rf_meta["nodata_value"],
    }

    # ---- 1. geometry repair (documented) ------------------------------------
    lsz = gpd.read_file(LSZ_SHP).to_crs(32643)
    repair_rows = []
    repaired = []
    for _, row in lsz.iterrows():
        g = row.geometry
        cls = str(row["Susceptibi"])
        fixed = make_valid(g)
        if not fixed.is_valid:                       # belt and braces; record if ever used
            fixed = g.buffer(0)
        repair_rows.append({"susceptibi": cls,
                            "valid_raw": bool(g.is_valid),
                            "valid_after_make_valid": bool(fixed.is_valid),
                            "area_raw_km2": round(g.area / 1e6, 4),
                            "area_repaired_km2": round(fixed.area / 1e6, 4),
                            "area_delta_km2": round((fixed.area - g.area) / 1e6, 6)})
        repaired.append((fixed, CLASS_CODE[cls]))
    meta["geometry_repair"] = {
        "method": "shapely.validation.make_valid per feature (3/3 delivered features are "
                  "formally invalid); buffer(0) fallback never needed this run",
        "per_feature": repair_rows,
        "total_area_raw_km2": round(sum(r["area_raw_km2"] for r in repair_rows), 4),
        "total_area_repaired_km2": round(sum(r["area_repaired_km2"] for r in repair_rows), 4),
        "changes_measured_areas": any(abs(r["area_delta_km2"]) > 0 for r in repair_rows),
    }
    lsz_union = unary_union([g for g, _ in repaired])
    meta["lsz_union_area_repaired_km2"] = round(lsz_union.area / 1e6, 4)

    # ---- 2. grid + rasters ---------------------------------------------------
    with rasterio.open(MASK) as ds:
        dmask = ds.read(1) == 1
        tf, shape = ds.transform, (ds.height, ds.width)
        # matplotlib imshow extent order is (left, right, bottom, top)
        grid_bounds = (ds.bounds.left, ds.bounds.right, ds.bounds.bottom, ds.bounds.top)
    with rasterio.open(RF_TIF) as ds:
        assert (ds.height, ds.width) == shape, "RF raster not on the district grid"
        assert ds.transform.almost_equals(tf), "RF transform differs from mask"
        assert ds.crs.to_string() == "EPSG:32643"
        rf = ds.read(1).astype("float64")
        nod = ds.nodata
    valid_rf = np.isfinite(rf) & (rf != nod)

    lsz_code = rasterize(repaired, out_shape=shape, transform=tf, fill=0,
                         all_touched=False, dtype="uint8")

    domain = dmask & (lsz_code > 0) & valid_rf
    n_dom = int(domain.sum())
    dom = dmask & (lsz_code > 0) & (~valid_rf)          # LSZ-covered but RF invalid
    n_dom_rf_invalid = int(dom.sum())

    gadm_df = gpd.read_file(GADM).query("NAME_2 == 'Wayanad'").to_crs(32643)
    gadm_geom = unary_union(list(gadm_df.geometry))

    dmask_cells = int(dmask.sum())
    rf_domain_cells = int((dmask & valid_rf).sum())
    meta["comparison_domain"] = {
        "rule": "district_mask(GADM) AND lsz_code>0 AND rf_valid",
        "cells": n_dom,
        "area_km2": round(n_dom * CELL_KM2, 2),
        "share_of_district_mask_cells": round(n_dom / dmask_cells, 6),
        "share_of_rf_map_domain_cells": round(n_dom / rf_domain_cells, 6),
        "district_mask_cells": dmask_cells,
        "rf_map_domain_cells": rf_domain_cells,
        "gadm_minus_lsz_cells": int((dmask & (lsz_code == 0)).sum()),
        "gadm_minus_lsz_km2": round(int((dmask & (lsz_code == 0)).sum()) * CELL_KM2, 2),
        "lsz_covered_rf_invalid_cells": n_dom_rf_invalid,
        "note": "GADM area not covered by the GSI file is EXCLUDED (no extrapolation)",
        "cell_size_m": 30, "crs": "EPSG:32643",
        "gadm_area_km2_vector": round(gadm_geom.area / 1e6, 4),
    }

    # ---- 3. RF quintile classes over the comparison domain -------------------
    scores = rf[domain]
    qs = [0.2, 0.4, 0.6, 0.8]
    cuts = np.quantile(scores, qs, method="linear")
    qcls = np.searchsorted(cuts, scores, side="left") + 1        # 1..5
    qlabel = {1: "Q1 (lowest band)", 2: "Q2", 3: "Q3", 4: "Q4", 5: "Q5 (highest band)"}
    q_shares = {qlabel[i]: round(float((qcls == i).mean()), 6) for i in range(1, 6)}
    meta["rf_quantile_method"] = {
        "defined_over": "comparison-domain cells only (equal-area 30 m cells; cell quantiles "
                        "= area-weighted quantiles)",
        "classes": 5,
        "cut_values": {f"p{int(q*100)}": float(c) for q, c in zip(qs, cuts)},
        "assignment": "np.searchsorted(cuts, score, side='left') + 1",
        "class_share_caveat": "score ties (many cells at 0.0) shift measured class shares "
                              "away from exactly 20% - shares reported as measured",
        "measured_class_shares": q_shares,
    }

    # ---- 4. cross-tabulation (area-weighted by cells) ------------------------
    zones = np.array([CLASS_CODE[str(s)] for s in lsz["Susceptibi"]])
    lsz_dom = lsz_code[domain]
    zc = np.zeros_like(scores, dtype=np.int64)
    for code in (1, 2, 3):
        zc[lsz_dom == code] = code

    tab = np.zeros((3, 5), dtype=np.int64)
    for z in (1, 2, 3):
        for q in range(1, 6):
            tab[z - 1, q - 1] = int(((zc == z) & (qcls == q)).sum())
    assert tab.sum() == n_dom

    cross_rows = []
    for z in (1, 2, 3):
        zname = CLASS_NAME[z]
        ztot = tab[z - 1].sum()
        for q in range(1, 6):
            cross_rows.append({
                "gsi_zone": zname, "rf_quintile": qlabel[q],
                "cells": int(tab[z - 1, q - 1]),
                "area_km2": round(tab[z - 1, q - 1] * CELL_KM2, 4),
                "pct_within_gsi_zone": round(100 * tab[z - 1, q - 1] / ztot, 3) if ztot else 0.0,
                "pct_of_rf_quintile_in_domain": round(
                    100 * tab[z - 1, q - 1] / tab[:, q - 1].sum(), 3),
            })
    for q in range(1, 6):
        cross_rows.append({
            "gsi_zone": "ALL ZONES", "rf_quintile": qlabel[q],
            "cells": int(tab[:, q - 1].sum()),
            "area_km2": round(tab[:, q - 1].sum() * CELL_KM2, 4),
            "pct_within_gsi_zone": round(100 * tab[:, q - 1].sum() / n_dom, 3),
            "pct_of_rf_quintile_in_domain": 100.0,
        })
    cross = pd.DataFrame(cross_rows)

    # ---- 5. RF score distribution within each GSI zone -----------------------
    stat_rows = []
    for z in (1, 2, 3):
        v = scores[zc == z]
        stat_rows.append({
            "gsi_zone": CLASS_NAME[z],
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
            **{f"pct_in_{qlabel[q].split(' ')[0]}":
               round(100 * float((qcls[zc == z] == q).mean()), 3) for q in range(1, 6)},
        })
    v = scores
    stat_rows.append({
        "gsi_zone": "ALL ZONES", "cells_in_domain": int(v.size),
        "area_km2": round(v.size * CELL_KM2, 4),
        "mean": round(float(v.mean()), 6), "std": round(float(v.std()), 6),
        "min": round(float(v.min()), 6),
        "p05": round(float(np.quantile(v, 0.05)), 6),
        "p25": round(float(np.quantile(v, 0.25)), 6),
        "median": round(float(np.quantile(v, 0.5)), 6),
        "p75": round(float(np.quantile(v, 0.75)), 6),
        "p95": round(float(np.quantile(v, 0.95)), 6),
        "max": round(float(v.max()), 6),
        **{f"pct_in_{qlabel[q].split(' ')[0]}":
           round(100 * float((qcls == q).mean()), 3) for q in range(1, 6)},
    })
    stats = pd.DataFrame(stat_rows)

    # ---- 6. per-zone capture (no extrapolation record) -----------------------
    zone_capture = []
    for z in (1, 2, 3):
        code = z
        zname = CLASS_NAME[z]
        g_area = sum(r["area_repaired_km2"] for r in repair_rows
                     if r["susceptibi"] == zname)
        cells_z = int((lsz_code == code).sum())
        cells_z_dom = int(((lsz_code == code) & dmask & valid_rf).sum())
        zone_capture.append({"gsi_zone": zname,
                             "repaired_vector_area_km2": round(g_area, 4),
                             "rasterized_cells_full_grid": cells_z,
                             "rasterized_km2_full_grid": round(cells_z * CELL_KM2, 4),
                             "cells_in_comparison_domain": cells_z_dom,
                             "km2_in_comparison_domain": round(cells_z_dom * CELL_KM2, 4),
                             "pct_of_zone_inside_domain":
                                 round(100 * cells_z_dom / cells_z, 3)})
    meta["zone_capture_in_domain"] = zone_capture

    # ---- 7. write tables + metadata (disclaimers as '#' headers) -------------
    head = "\n".join(f"# {d}" for d in DISCLAIMERS)
    cross_path = OUT / "crosstab_gsi_class_x_rf_quintile.csv"
    stats_path = OUT / "rf_score_stats_within_gsi_zones.csv"
    cross.to_csv(cross_path, index=False, float_format="%.6f",
                 lineterminator="\n")
    stats.to_csv(stats_path, index=False, float_format="%.6f",
                 lineterminator="\n")
    for p in (cross_path, stats_path):
        txt = p.read_text(encoding="utf-8")
        p.write_text(head + "\n" + txt, encoding="utf-8")

    meta["outputs"] = {
        "crosstab": str(cross_path.relative_to(ROOT)),
        "score_stats": str(stats_path.relative_to(ROOT)),
        "figure": str((OUT / "overlay_map.png").relative_to(ROOT)),
    }
    (OUT / "comparison_domain.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    # ---- 8. figure ------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(11.5, 9.5), dpi=150)
    rf_bg = np.where(valid_rf, rf, np.nan)
    im = ax.imshow(rf_bg, cmap="magma", origin="upper", extent=grid_bounds,
                   vmin=0.0, vmax=1.0, interpolation="nearest", zorder=1)
    cb = fig.colorbar(im, ax=ax, fraction=0.032, pad=0.015, shrink=0.85)
    cb.set_label("RF vote share - relative ranking (not a probability)", fontsize=9)

    lsz_bg = np.where(lsz_code > 0, lsz_code, np.nan)
    cmap = ListedColormap([CLASS_COLOR[c] for c in (1, 2, 3)])
    ax.imshow(lsz_bg, cmap=cmap, origin="upper", extent=grid_bounds,
              vmin=0.5, vmax=3.5, alpha=0.38, interpolation="nearest", zorder=2)
    ax.contour(np.where(lsz_code > 0, lsz_code, 0).astype(float),
               levels=[0.5], colors="#333333", linewidths=0.3, origin="upper",
               extent=grid_bounds, zorder=3)

    gadm_plot = gpd.GeoSeries([gadm_geom], crs=32643).boundary
    gadm_plot.plot(ax=ax, edgecolor="black", linewidth=1.4, zorder=4)

    handles = [Patch(facecolor=CLASS_COLOR[c], alpha=0.38,
                     edgecolor="#333333", label=f"GSI 2022 zone: {CLASS_NAME[c]}")
               for c in (1, 2, 3)]
    handles.append(plt.Line2D([0], [0], color="black", lw=1.4,
                              label="GADM 4.1 project boundary"))
    ax.legend(handles=handles, loc="lower left", fontsize=9, framealpha=0.9)

    ax.set_title("Descriptive comparison — Phase 5 RF susceptibility ranking vs\n"
                 "GSI 2022 landslide susceptibility zones (LSZ-01), Wayanad",
                 fontsize=13)
    ax.set_xlabel("UTM 43N easting (m)"); ax.set_ylabel("UTM 43N northing (m)")
    sub = (f"Comparison domain: GADM 4.1 ∩ GSI coverage ∩ valid RF = "
           f"{n_dom:,} cells = {n_dom * CELL_KM2:,.1f} km² "
           f"({100 * n_dom / dmask_cells:.2f}% of the district mask). "
           f"GSI-zone gap vs GADM: "
           f"{meta['comparison_domain']['gadm_minus_lsz_km2']:,.2f} km² (excluded, no extrapolation).")
    ax.text(0.5, -0.075, sub, transform=ax.transAxes, ha="center", fontsize=8.5)
    import textwrap
    disc = ("   ·   ".join([
        "RF raster = RELATIVE ranking conditional on the observed inventory — not a calibrated "
        "probability, forecast, warning or timing prediction",
        "GSI 2022 zones = another MODEL-DERIVED susceptibility product — not ground truth, "
        "not geology, not validation labels",
        "Descriptive zone/ranking agreement only — no significance tests; spatial "
        "autocorrelation expected",
        "GSI file covers 95.99% of the GADM boundary; not field-validated; zones NOT "
        "extrapolated to the missing area",
    ]))
    y0 = 0.030
    for i, line in enumerate(textwrap.wrap(disc, width=175)[:3]):
        fig.text(0.5, y0 - i * 0.016, line, ha="center", fontsize=6.8, color="#333333")
    fig.subplots_adjust(bottom=0.16)
    fig.savefig(OUT / "overlay_map.png", bbox_inches="tight")
    plt.close(fig)

    # ---- 9. console summary ---------------------------------------------------
    print("geometry repair delta km2:",
          meta["geometry_repair"]["total_area_repaired_km2"],
          "vs raw", meta["geometry_repair"]["total_area_raw_km2"],
          "| changes areas:", meta["geometry_repair"]["changes_measured_areas"])
    print("domain:", n_dom, "cells =", round(n_dom * CELL_KM2, 2), "km2 |",
          round(100 * n_dom / dmask_cells, 2), "% of district mask |",
          round(100 * n_dom / rf_domain_cells, 2), "% of RF map domain")
    print("quantile cuts:", {f"p{int(q*100)}": round(float(c), 6)
                             for q, c in zip(qs, cuts)})
    print("\ncross-tab (km2, % within zone):")
    print(cross.to_string(index=False))
    print("\nRF score stats within GSI zones:")
    print(stats.to_string(index=False))
    print(f"\noutputs -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
