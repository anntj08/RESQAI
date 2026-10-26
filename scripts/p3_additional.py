"""Phase 3 Stage 8 - HydroRIVERS and OSM roads: validate, metric reprojection.

Neither layer gets a distance raster in this phase. Distance-to-river and
distance-to-road are modelling decisions that need a stated rationale about
whether the feature is a proxy for the process (road = cut slope / disturbance;
river = basal erosion / undercutting) and about which stream-order threshold is
defensible. Producing them now would prejudge that.

What is checked here:
  * CRS, geometry types, validity, zero-length geometries, duplicates;
  * whether the district clip dropped whole features (it must be an intersection,
    not a "within" filter) and how much length lies outside the polygon;
  * HydroRIVERS topological truncation: a clipped network necessarily loses the
    downstream links that leave the district. This is counted, not glossed over.

Outputs (data/processed/additional/):
  roads_wayanad_district_32643.gpkg
  hydrorivers_wayanad_district_32643.gpkg
  additional_layers_validation.json

Run: python scripts/p3_additional.py
"""
from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "additional"
PROC = ROOT / "data" / "processed" / "additional"
GRID = ROOT / "data" / "processed" / "grid"
OUT = PROC
CRS = "EPSG:32643"


def geom_checks(gdf: gpd.GeoDataFrame, name: str) -> dict:
    g = gdf.geometry
    flat = np.concatenate([np.asarray(x.coords) for x in
                           (g if g.geom_type.iloc[0] == "LineString" else
                            [p for ml in g for p in ml.geoms])]) if len(g) else np.empty((0, 2))
    return {
        "n_features": int(len(gdf)),
        "geom_types": sorted(g.geom_type.unique().tolist()),
        "invalid": int((~g.is_valid).sum()),
        "empty": int(g.is_empty.sum()),
        "null": int(g.isna().sum()),
        "zero_length": int((g.length == 0).sum()),
        "duplicate_wkb": int(gdf.assign(wkb=g.to_wkb()).duplicated("wkb").sum()),
        "duplicate_geometry_ignoring_direction": int(
            gdf.assign(wkb=g.apply(lambda x: x.wkb_hex if x.geom_type == "LineString"
                                   else x.wkb_hex)).duplicated("wkb").sum()),
        "vertex_count": int(len(flat)),
        "metric_length_km": round(float(gdf.to_crs(CRS).length.sum() / 1e3), 1),
    }


def main() -> None:
    gadm = gpd.read_file(GRID / "wayanad_gadm_32643.gpkg")
    district = gadm.geometry.union_all()
    rep: dict = {}

    # ---------------- roads --------------------------------------------------
    raw = gpd.read_file(RAW / "osm_roads_wayanad.geojson")
    clip = gpd.read_file(PROC / "osm_roads_wayanad_clip.gpkg")
    raw_m = raw.to_crs(CRS)
    clip_m = clip.to_crs(CRS)

    raw_in = raw_m[raw_m.intersects(district)]
    rep["roads"] = {
        "raw": {"path": "data/raw/additional/osm_roads_wayanad.geojson",
                "crs": str(raw.crs), "columns": raw.columns.tolist(), **geom_checks(raw, "raw")},
        "clip": {"path": "data/processed/additional/osm_roads_wayanad_clip.gpkg",
                 "crs": str(clip.crs), "columns": clip.columns.tolist(),
                 **geom_checks(clip, "clip")},
        "clip_completeness": {
            "raw_features_intersecting_district": int(len(raw_in)),
            "clip_features": int(len(clip_m)),
            "features_lost_entirely": int(len(raw_in) - len(clip_m)),
            "raw_length_inside_district_km": round(
                float(raw_in.geometry.intersection(district).length.sum() / 1e3), 1),
            "clip_length_km": round(float(clip_m.length.sum() / 1e3), 1),
        },
        "attribute_completeness_pct": {
            str(c): round(float(clip[c].notna().mean() * 100), 1)
            for c in clip.columns if c != "geometry"},
        "highway_classes": clip["highway"].value_counts().head(12).to_dict(),
    }
    rep["roads"]["clip_completeness"]["length_retained_pct"] = round(
        rep["roads"]["clip_completeness"]["clip_length_km"]
        / rep["roads"]["clip_completeness"]["raw_length_inside_district_km"] * 100, 2)
    rep["roads"]["caveats"] = [
        "OSM completeness is uneven in rural Wayanad; an unmapped track is not an absent track.",
        "Snapshot dated 2026-10-25: roads built or abandoned since 2000 are not represented "
        "historically, so the layer is a present-day proxy, not a condition at the time of each "
        "landslide.",
        "A mapped road does not imply a cut slope; the predictor would be a proxy for "
        "anthropogenic disturbance, not a physical trigger.",
    ]

    # ---------------- rivers -------------------------------------------------
    hclip = gpd.read_file(PROC / "hydrorivers_wayanad_clip.gpkg")
    hclip_m = hclip.to_crs(CRS)
    ids = set(hclip["HYRIV_ID"].astype("int64"))
    down_in = hclip["NEXT_DOWN"].astype("int64")
    up_in = hclip["NEXT_UP"] if "NEXT_UP" in hclip.columns else None
    trunc = int((~down_in.isin(ids) & (down_in != 0)).sum())
    rep["rivers"] = {
        "clip": {"path": "data/processed/additional/hydrorivers_wayanad_clip.gpkg",
                 "crs": str(hclip.crs), "columns": hclip.columns.tolist(),
                 **geom_checks(hclip, "clip")},
        "connectivity": {
            "segments": int(len(hclip)),
            "segments_whose_next_down_is_also_in_the_clip": int(len(hclip) - trunc),
            "segments_truncated_at_the_district_edge": trunc,
            "truncation_pct": round(trunc / len(hclip) * 100, 2),
            "note": "expected: the district clip cuts the network, so downstream links leave "
                    "the study area. Flow routing must therefore be done on the unclipped Asia "
                    "network if it is ever needed; the clipped layer is for spatial context only.",
        },
        "duplicate_hyriv_id": int(hclip["HYRIV_ID"].duplicated().sum()),
        "length_sum_km_vs_attribute": {
            "geometry_km": round(float(hclip_m.length.sum() / 1e3), 1),
            "LENGTH_KM_attribute_total": round(float(hclip["LENGTH_KM"].sum()), 1),
            "note": "geometry < attribute total because each segment is cut at the district edge",
        },
        "stream_order_distribution": hclip["ORD_STRA"].value_counts().sort_index().to_dict(),
        "total_upstream_area_km2": round(float(hclip["UPLAND_SKM"].sum()), 1),
        "caveats": [
            "HydroRIVERS is a modelled network derived from a DEM, not a surveyed channel map; "
            "headwater streams below the source threshold are absent. At 30 m DEM resolution the "
            "channels that undercut a specific slope may simply not be represented.",
            "Segments crossing the district boundary are cut, so first/last links are not "
            "hydrologically complete.",
        ],
    }

    # ---------------- metric copies -----------------------------------------
    roads_out = OUT / "roads_wayanad_district_32643.gpkg"
    rivers_out = OUT / "hydrorivers_wayanad_district_32643.gpkg"
    clip_m.to_file(roads_out, driver="GPKG")
    hclip_m.to_file(rivers_out, driver="GPKG")
    rep["metric_copies"] = {"roads": str(roads_out.relative_to(ROOT)),
                            "rivers": str(rivers_out.relative_to(ROOT)),
                            "crs": CRS,
                            "note": "same features and attributes as the Phase-1 clips, only "
                                    "reprojected; the source clips are left untouched"}

    rep["distance_rasters"] = {
        "produced": False,
        "reason": "not required in this phase; deriving them is a modelling decision that needs "
                  "a stated proxy rationale and, for rivers, a defensible stream-order threshold",
    }

    (OUT / "additional_layers_validation.json").write_text(json.dumps(rep, indent=2),
                                                          encoding="utf-8")
    print(json.dumps(rep, indent=2))


if __name__ == "__main__":
    main()
