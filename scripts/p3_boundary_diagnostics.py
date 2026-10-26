"""Phase 3 Stage 2 - boundary diagnostics: GADM 4.1 vs OSM/Nominatim.

Equal area does not mean equal outline. This script measures where the two
boundaries disagree in metres, how far the disagreement extends, and whether any
inventory record classified as "outside GADM" is inside OSM - which would make
the exclusion a boundary-generalisation artefact rather than a district error.

Run: python scripts/p3_boundary_diagnostics.py
"""
from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed" / "grid"
INV = ROOT / "data" / "processed" / "inventory" / "inventory_source_records.csv"
WORK_CRS = "EPSG:32643"


def edge_samples(geom, step_m: float = 50.0) -> np.ndarray:
    """Points every `step_m` along a LinearRing / LineString / MultiLineString."""
    if geom.geom_type in ("LineString", "LinearRing"):
        lines = [geom]
    elif geom.geom_type == "Polygon":
        lines = [geom.exterior]
    elif geom.geom_type == "MultiPolygon":
        lines = [g.exterior for g in geom.geoms]
    else:  # MultiLineString
        lines = list(geom.geoms)
    pts = []
    for ln in lines:
        n = max(2, int(ln.length // step_m))
        for i in range(n):
            p = ln.interpolate(i * ln.length / n)
            pts.append((p.x, p.y))
    return np.array(pts)


def main() -> None:
    gadm = gpd.read_file(RAW / "boundary/gadm41_IND_2/gadm41_IND_2.json")
    gadm = gadm[gadm["NAME_2"] == "Wayanad"].to_crs(WORK_CRS)
    osm = gpd.read_file(RAW / "boundary/osm_nominatim_wayanad.geojson").to_crs(WORK_CRS)
    g_union = gadm.geometry.union_all()
    o_union = osm.geometry.union_all()

    gb = g_union.boundary
    ob = o_union.boundary

    res: dict = {}
    for name, src, dst in (("gadm_vertices_to_osm", gb, o_union), ("osm_vertices_to_gadm", ob, g_union)):
        pts = edge_samples(src, 50.0)
        dist = np.array([dst.boundary.distance(Point(x, y)) for x, y in pts])
        res[name] = {
            "n_samples": int(dist.size),
            "median_m": round(float(np.median(dist)), 1),
            "p90_m": round(float(np.percentile(dist, 90)), 1),
            "p99_m": round(float(np.percentile(dist, 99)), 1),
            "max_m": round(float(dist.max()), 1),
            "share_within_100m_pct": round(float((dist <= 100).mean() * 100), 2),
            "share_within_500m_pct": round(float((dist <= 500).mean() * 100), 2),
        }

    # Asymmetric difference, split by side and located by centroid.
    only_gadm = g_union.difference(o_union)
    only_osm = o_union.difference(g_union)
    res["area_only_gadm_km2"] = round(only_gadm.area / 1e6, 2)
    res["area_only_osm_km2"] = round(only_osm.area / 1e6, 2)
    res["asymmetric_diff_pct_of_gadm"] = round((only_gadm.area + only_osm.area) / g_union.area * 100, 2)

    def patches(geom, min_km2=1.0):
        parts = list(geom.geoms) if geom.geom_type == "MultiPolygon" else [geom]
        rows = []
        for p in parts:
            if p.area / 1e6 >= min_km2:
                c = p.representative_point()
                lon, lat = gpd.GeoSeries([c], crs=WORK_CRS).to_crs("EPSG:4326").iloc[0].coords[0]
                rows.append({"area_km2": round(p.area / 1e6, 2), "lon": round(lon, 4),
                             "lat": round(lat, 4)})
        return sorted(rows, key=lambda r: -r["area_km2"])

    res["patches_only_gadm_ge1km2"] = patches(only_gadm)
    res["patches_only_osm_ge1km2"] = patches(only_osm)

    # Cross-check: do the 23 "outside GADM" inventory records fall inside OSM?
    inv = pd.read_csv(INV)
    outside = inv[inv["inclusion"].isin(
        ["INCLUDED_BOUNDARY_REVIEW", "EXCLUDED_OUT_OF_DISTRICT", "INCLUDED_FLAGGED"])].copy()
    pts = gpd.GeoDataFrame(
        outside,
        geometry=gpd.points_from_xy(outside["lon_dd_original"], outside["lat_dd_original"]),
        crs="EPSG:4326",
    ).to_crs(WORK_CRS)
    pts["inside_gadm"] = pts.geometry.within(g_union)
    pts["inside_osm"] = pts.geometry.within(o_union)
    pts["dist_gadm_m"] = pts.geometry.apply(lambda p: gb.distance(p)).round(0)
    pts["dist_osm_m"] = pts.geometry.apply(lambda p: ob.distance(p)).round(0)
    flipped = pts[(~pts["inside_gadm"]) & pts["inside_osm"]]
    res["inventory_outside_gadm"] = int((~pts["inside_gadm"]).sum())
    res["inventory_outside_gadm_but_inside_osm"] = int(len(flipped))
    res["flipped_records"] = flipped[[
        "source_record_id", "source_id", "locality", "lat_dd_original", "lon_dd_original",
        "inclusion", "coord_precision_deg", "dist_outside_boundary_m",
        "dist_osm_m"]].to_dict("records")

    (OUT / "boundary_diagnostics.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
