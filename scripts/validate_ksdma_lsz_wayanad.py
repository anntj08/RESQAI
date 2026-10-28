"""Validate the KSDMA-hosted GSI 2022 Wayanad landslide susceptibility zones archive.

Validates the ACTUAL FILE downloaded by scripts/fetch_ksdma_lsz_wayanad.py
(data/raw/landslide_susceptibility_reference/Wayanad.zip, original preserved
unchanged). This is a REFERENCE / COMPARISON dataset only — GSI 2022 landslide
susceptibility zones (not geology, not a predictor, not a model input, never a
forecast or timing claim).

Checks, per AGENTS.md verification vocabulary (VERIFIED requires file integrity,
format, CRS, resolution/scale, full district coverage and value plausibility —
all confirmed on the actual file):

  1. sha256 of the preserved zip re-computed vs the fetch evidence record.
  2. Zip integrity: CRC test of every member (zipfile.testzip), member listing.
  3. Extracted working copy under data/interim/lsz_reference/extracted/ (raw
     zip is NEVER modified or replaced by this script).
  4. Layer inspection with geopandas: CRS, geometry types, feature counts,
     validity, bounds (native + WGS84), attribute schema, class-column
     distributions (feature counts AND measured areas in EPSG:32643).
  5. Coverage against the Wayanad district boundary, measured three ways:
       a) rasterized overlap against the authoritative 30 m district mask
          (data/processed/grid/district_mask_30m.tif, EPSG:32643);
       b) vector intersection against the GADM 4.1 Wayanad polygon
          (data/raw/boundary/gadm41_IND_2/gadm41_IND_2.json);
       c) supplementary vector cross-check against the OSM/Nominatim boundary
          (data/raw/boundary/osm_nominatim_wayanad.geojson).
     No full-coverage claim is made unless the file itself demonstrates it.
  6. Value plausibility: class names/counts/areas recorded as measured.

Evidence -> data/interim/lsz_reference/validation.json

Run:  python scripts/validate_ksdma_lsz_wayanad.py
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import pathlib
import shutil
import sys
import zipfile

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import rasterize
from shapely.ops import unary_union

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW_ZIP = ROOT / "data" / "raw" / "landslide_susceptibility_reference" / "Wayanad.zip"
FETCH_EV = ROOT / "data" / "interim" / "lsz_reference" / "fetch_evidence.json"
WORKDIR = ROOT / "data" / "interim" / "lsz_reference" / "extracted"
OUT = ROOT / "data" / "interim" / "lsz_reference" / "validation.json"

DISTRICT_MASK = ROOT / "data" / "processed" / "grid" / "district_mask_30m.tif"
GADM = ROOT / "data" / "raw" / "boundary" / "gadm41_IND_2" / "gadm41_IND_2.json"
OSM = ROOT / "data" / "raw" / "boundary" / "osm_nominatim_wayanad.geojson"

# Wayanad spans 75.7722-76.4356 E / 11.4427-11.9706 N (AGENTS.md, do not re-derive wrongly)
WAYANAD_BBOX_WGS84 = (75.7722, 11.4427, 76.4356, 11.9706)

# categorical rasters are never interpolated (AGENTS.md rule 1) - rasterizing
# zone polygons onto the project grid is a classification, not interpolation.

K2 = 1e6  # m^2 -> km^2


def sha256_of(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def jsonable(v):
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return float(v)
    return v


def bbox_of(gdf: gpd.GeoDataFrame) -> list[float]:
    b = gdf.total_bounds
    return [jsonable(x) for x in b]


def bbox_wgs84(gdf: gpd.GeoDataFrame) -> list[float]:
    g = gdf if (gdf.crs and gdf.crs.is_geographic) else gdf.to_crs(4326)
    return bbox_of(g)


def class_column_distributions(gdf: gpd.GeoDataFrame, utm: gpd.GeoDataFrame
                               ) -> list[dict]:
    """For short-cardinality text/numeric columns, count features and measure area."""
    out = []
    if gdf.empty:
        return out
    areas = utm.geometry.area / K2
    for col in gdf.columns:
        if col == gdf.geometry.name:
            continue
        s = gdf[col]
        is_text = (s.dtype == object or pd.api.types.is_string_dtype(s))
        is_num = (pd.api.types.is_numeric_dtype(s)
                  and not pd.api.types.is_bool_dtype(s))
        if not (is_text or is_num):
            continue
        nun = int(s.nunique(dropna=False))
        if not (0 < nun <= 12):
            continue
        vals = []
        vc = s.value_counts(dropna=False)
        if is_num:
            vc = vc.sort_index()
        for val, cnt in vc.items():
            if pd.isna(val):
                mask = s.isna().to_numpy()
            else:
                mask = (s == val).to_numpy()
            vals.append({"value": None if pd.isna(val) else jsonable(val),
                         "n_features": int(cnt),
                         "area_km2": round(float(areas[mask].sum()), 4)})
        out.append({"column": col, "n_unique": nun, "values": vals})
    return out


def read_layer(path: pathlib.Path) -> gpd.GeoDataFrame:
    return gpd.read_file(path)


def main() -> int:
    if not RAW_ZIP.exists() or not FETCH_EV.exists():
        print("FATAL: run scripts/fetch_ksdma_lsz_wayanad.py first")
        return 1

    rec: dict = {"checked_at_utc":
                 dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}

    # ---- 1. integrity vs fetch evidence -----------------------------------
    fetch = json.loads(FETCH_EV.read_text(encoding="utf-8"))
    sha = sha256_of(RAW_ZIP)
    rec["zip"] = {"path": str(RAW_ZIP.relative_to(ROOT)),
                  "size_bytes": RAW_ZIP.stat().st_size,
                  "sha256": sha,
                  "sha256_matches_fetch_evidence": sha == fetch["sha256"]}

    # ---- 2. zip listing + CRC integrity ------------------------------------
    with zipfile.ZipFile(RAW_ZIP) as zf:
        bad = zf.testzip()
        members = zf.infolist()
        rec["zip"]["crc_test_all_ok"] = bad is None
        rec["zip"]["crc_first_bad_member"] = bad
        rec["zip"]["n_members"] = len(members)
        rec["zip"]["members"] = [
            {"name": m.filename, "size": m.file_size, "compressed": m.compress_size,
             "date_time": list(m.date_time)} for m in members]
        # ---- 3. working-copy extraction (raw untouched) --------------------
        if WORKDIR.exists():
            shutil.rmtree(WORKDIR)
        zf.extractall(WORKDIR)

    names = [m.filename for m in members]
    shps = [p for p in WORKDIR.rglob("*.shp")]
    gbds = [p.parent for p in WORKDIR.rglob("*.gdb")]
    rec["zip"]["shapefiles_found"] = [str(p.relative_to(WORKDIR)) for p in shps]
    rec["zip"]["gdb_dirs_found"] = [str(p.relative_to(WORKDIR)) for p in gbds]

    # ---- 4. layer inspection ----------------------------------------------
    layers = []
    gdfs: list[tuple[str, gpd.GeoDataFrame]] = []
    for p in shps:
        try:
            gdf = read_layer(p)
        except Exception as e:                     # record, don't hide
            layers.append({"file": str(p.relative_to(WORKDIR)),
                           "error": f"{type(e).__name__}: {e}"})
            continue
        gdf_utm = gdf.to_crs(32643) if gdf.crs else gdf
        inval = int((~gdf.geometry.is_valid).sum())
        nulls = int(gdf.geometry.isna().sum())
        lyr = {
            "file": str(p.relative_to(WORKDIR)),
            "features": int(len(gdf)),
            "crs": str(gdf.crs) if gdf.crs else "(MISSING - no .prj / no CRS)",
            "crs_is_geographic": bool(gdf.crs.is_geographic) if gdf.crs else None,
            "geometry_types": sorted({t for t in gdf.geometry.geom_type.unique()}),
            "invalid_geometries": inval,
            "null_geometries": nulls,
            "bounds_native": bbox_of(gdf),
            "bounds_wgs84": bbox_wgs84(gdf),
            "columns": [{"name": c, "dtype": str(gdf[c].dtype)}
                        for c in gdf.columns if c != gdf.geometry.name],
            "sample_attributes": gdf.drop(columns=[gdf.geometry.name])
                                    .head(3).to_dict(orient="records"),
        }
        lyr["class_distributions"] = class_column_distributions(gdf, gdf_utm)
        layers.append(lyr)
        gdfs.append((p.name, gdf))
        print(f"layer {p.name}: {len(gdf)} features, crs={gdf.crs}, "
              f"invalid={inval}, nulls={nulls}")
    for gp in gbds:
        try:
            gdf = gpd.read_file(gp)
        except Exception as e:
            layers.append({"file": str(gp.relative_to(WORKDIR)),
                           "error": f"{type(e).__name__}: {e}"})
            continue
        layers.append({"file": str(gp.relative_to(WORKDIR)) + " (FileGDB)",
                       "note": "gdb layer read"} |
                      {"features": int(len(gdf)), "crs": str(gdf.crs),
                       "bounds_native": bbox_of(gdf),
                       "columns": [c for c in gdf.columns if c != gdf.geometry.name]})
        gdfs.append((gp.name, gdf))
    rec["layers"] = layers

    if not gdfs:
        print("FATAL: no readable spatial layer found in the archive")
        OUT.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
        return 1

    # combined union of ALL layers, in UTM 43N (metric; AGENTS.md rule 5)
    utm_parts = []
    for _, gdf in gdfs:
        u = gdf.to_crs(32643)
        if u.crs is not None:
            utm_parts += list(u.geometry)
    utm_parts = [g for g in utm_parts if g is not None and not g.is_empty]
    try:
        lsz_union = unary_union(utm_parts)
        union_note = "raw geometries"
    except Exception as e:
        # invalid members can break union; fix copies for MEASUREMENT only
        fixed = [g.buffer(0) if not g.is_valid else g for g in utm_parts]
        lsz_union = unary_union(fixed)
        union_note = (f"union required buffer(0) on invalid members "
                      f"({type(e).__name__}); measurement-only fix, raw unchanged")
    rec["union"] = {"area_km2": round(lsz_union.area / K2, 4),
                    "parts_unioned": len(utm_parts),
                    "note": union_note}

    # ---- 5. coverage --------------------------------------------------------
    cov: dict = {}

    # reference boundaries
    gadm = gpd.read_file(GADM)
    gadm_w = gadm[gadm["NAME_2"] == "Wayanad"].to_crs(32643)
    gadm_geom = unary_union(list(gadm_w.geometry))
    cov["gadm_wayanad"] = {"features": int(len(gadm_w)),
                           "area_km2": round(gadm_geom.area / K2, 4)}

    osm_gdf = gpd.read_file(OSM).to_crs(32643)
    osm_geom = unary_union(list(osm_gdf.geometry))
    cov["osm_wayanad"] = {"features": int(len(osm_gdf)),
                          "area_km2": round(osm_geom.area / K2, 4)}

    inter_g = lsz_union.intersection(gadm_geom)
    diff_g = lsz_union.difference(gadm_geom)
    cov["method_b_vector_gadm"] = {
        "lsz_intersection_km2": round(inter_g.area / K2, 4),
        "fraction_of_district": round((inter_g.area / gadm_geom.area), 6),
        "lsz_outside_gadm_km2": round(diff_g.area / K2, 4),
    }
    inter_o = lsz_union.intersection(osm_geom)
    cov["method_c_vector_osm_supplementary"] = {
        "lsz_intersection_km2": round(inter_o.area / K2, 4),
        "fraction_of_district": round((inter_o.area / osm_geom.area), 6),
    }

    # method (a): authoritative 30 m district mask
    with rasterio.open(DISTRICT_MASK) as src:
        mask = src.read(1)
        mtransform, mshape = src.transform, (src.height, src.width)
        cov["district_mask"] = {
            "path": str(DISTRICT_MASK.relative_to(ROOT)),
            "crs": str(src.crs), "shape": [src.height, src.width],
            "cell_values": sorted(jsonable(v) for v in np.unique(mask)),
            "district_cells": int((mask == 1).sum()),
            "district_area_km2": round(float((mask == 1).sum() * 900 / K2), 2),
        }
        n_mask = int((mask == 1).sum())
        for at in (False, True):
            rz = rasterize([(g, 1) for g in utm_parts], out_shape=mshape,
                           transform=mtransform, fill=0, all_touched=at,
                           dtype="uint8")
            overlap = int(((mask == 1) & (rz == 1)).sum())
            cov[f"method_a_raster_mask_30m_alltouched_{str(at).lower()}"] = {
                "lsz_cells_inside_district": overlap,
                "fraction_of_district_cells": round(overlap / n_mask, 6),
            }
    rec["coverage"] = cov

    # ---- 6. plausibility ----------------------------------------------------
    wgs = None
    for lyr in rec["layers"]:
        if "bounds_wgs84" in lyr:
            wgs = lyr["bounds_wgs84"]
            break
    in_w = (wgs is not None and
            wgs[0] < WAYANAD_BBOX_WGS84[2] and wgs[2] > WAYANAD_BBOX_WGS84[0] and
            wgs[1] < WAYANAD_BBOX_WGS84[3] and wgs[3] > WAYANAD_BBOX_WGS84[1])
    rec["value_plausibility"] = {
        "wayanad_reference_bbox_wgs84": list(WAYANAD_BBOX_WGS84),
        "lsz_bounds_wgs84": wgs,
        "lsz_overlaps_district_bbox": bool(in_w),
        "note": "susceptibility zoning estimates where conditions favour failure; "
                "not a forecast, warning or timing prediction",
    }

    OUT.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    print(f"\nsummary:")
    print(f"  sha256 match : {rec['zip']['sha256_matches_fetch_evidence']} | "
          f"CRC ok: {rec['zip']['crc_test_all_ok']}")
    print(f"  layers       : {[g for g, _ in gdfs]}")
    print(f"  union area   : {rec['union']['area_km2']} km2")
    print(f"  GADM district: {cov['gadm_wayanad']['area_km2']} km2")
    print(f"  coverage GADM: {cov['method_b_vector_gadm']['fraction_of_district']*100:.2f} % "
          f"({cov['method_b_vector_gadm']['lsz_intersection_km2']} km2)")
    print(f"  coverage OSM : {cov['method_c_vector_osm_supplementary']['fraction_of_district']*100:.2f} %")
    print(f"  coverage mask: "
          f"{cov['method_a_raster_mask_30m_alltouched_false']['fraction_of_district_cells']*100:.2f} % "
          f"(cells), all_touched="
          f"{cov['method_a_raster_mask_30m_alltouched_true']['fraction_of_district_cells']*100:.2f} %")
    print(f"evidence -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
