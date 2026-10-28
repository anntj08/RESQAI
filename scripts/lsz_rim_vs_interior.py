"""Distinguish boundary-rim effects from interior holes in the LSZ coverage
mismatch, and add the OSM boundary-alignment analogue.

Companion to diagnose_lsz_boundary_fit.py (run after validate_ksdma_lsz_wayanad.py).
For each GADM-minus-LSZ part and LSZ-minus-GADM part this records whether the
part touches the GADM boundary (< 1 m): a part that touches the boundary is a
boundary-line strip (two boundary sources disagreeing); an interior part would
be a genuine hole in the susceptibility zoning.

Evidence -> data/interim/lsz_reference/rim_vs_interior.json

Run:  python scripts/lsz_rim_vs_interior.py
"""
from __future__ import annotations

import json
import pathlib
import sys

import geopandas as gpd
from shapely import prepare
from shapely.ops import unary_union

ROOT = pathlib.Path(__file__).resolve().parents[1]
LAYER = ROOT / "data" / "interim" / "lsz_reference" / "extracted" / "Wayanad" / "Wayanad_GSI_LS.shp"
GADM = ROOT / "data" / "raw" / "boundary" / "gadm41_IND_2" / "gadm41_IND_2.json"
OSM = ROOT / "data" / "raw" / "boundary" / "osm_nominatim_wayanad.geojson"
OUT = ROOT / "data" / "interim" / "lsz_reference" / "rim_vs_interior.json"
K2 = 1e6


def main() -> int:
    lsz = unary_union(list(gpd.read_file(LAYER).to_crs(32643).geometry))
    gadm_gdf = gpd.read_file(GADM).query("NAME_2 == 'Wayanad'").to_crs(32643)
    gadm = unary_union(list(gadm_gdf.geometry))
    osm = unary_union(list(gpd.read_file(OSM).to_crs(32643).geometry))

    rec: dict = {}
    for label, diff in (("gadm_minus_lsz", gadm.difference(lsz)),
                        ("lsz_minus_gadm", lsz.difference(gadm))):
        parts = list(diff.geoms)
        gadm_b = gadm.boundary
        prepare(gadm_b)
        rows = []
        interior = 0
        for g in sorted(parts, key=lambda x: -x.area):
            d = gadm_b.distance(g)
            touches = d < 1.0
            interior += (not touches)
            c = g.centroid
            rows.append({"area_km2": round(g.area / K2, 4),
                         "touches_gadm_boundary": bool(touches),
                         "distance_to_gadm_boundary_m": round(float(d), 1),
                         "centroid_wgs84_lon": round(float(c.x), 4),
                         "centroid_wgs84_lat": round(float(c.y), 4)})
        rec[label] = {"n_parts": len(parts),
                      "n_parts_touching_boundary": len(parts) - interior,
                      "n_interior_parts": interior,
                      "total_km2": round(diff.area / K2, 4),
                      "parts": rows}

    # OSM analogue: alignment of the LSZ boundary against OSM boundary
    from shapely import wkt
    import numpy as np
    osm_b = osm.boundary
    prepare(osm_b)
    pts = []
    for g in (list(lsz.geoms) if lsz.geom_type.startswith("Multi") else [lsz]):
        pts += list(g.exterior.coords)
    step = max(1, len(pts) // 1500)
    d = np.array([osm_b.distance(wkt.loads(f"POINT ({x} {y})")) for x, y in pts[::step]])
    rec["boundary_alignment_vs_osm"] = {
        "sampled_lsz_boundary_vertices": int(len(d)),
        "median_m": round(float(np.median(d)), 1),
        "p95_m": round(float(np.percentile(d, 95)), 1),
        "max_m": round(float(d.max()), 1),
        "share_within_100m": round(float((d <= 100).mean()), 4),
        "share_within_250m": round(float((d <= 250).mean()), 4),
    }

    OUT.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: ({kk: vv for kk, vv in v.items() if kk != "parts"}
                          if isinstance(v, dict) else v) for k, v in rec.items()},
                     indent=2))
    print(f"evidence -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
