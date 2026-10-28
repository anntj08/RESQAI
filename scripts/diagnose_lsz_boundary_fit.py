"""Diagnose the LSZ-vs-boundary mismatch and geometry validity of the GSI 2022
Wayanad susceptibility zones layer (down RUN-2026-10-28-05).

The first validation pass measured coverage of 95.99% (GADM), 96.11% (30 m mask,
all_touched) and 99.07% (OSM) — with ALL 3 layer geometries invalid. Before any
manifest verdict, this script answers, with numbers:

  1. buffer(0) sensitivity: do the invalid (self-intersecting) rings change
     measured class areas? (raw shoelace area vs make-buffer(0) area, per class)
  2. shape of the uncovered district area (GADM minus LSZ): one thin boundary
     rim, or interior holes? (part count, part areas, largest parts with bboxes)
  3. shape of the LSZ area outside the district (LSZ minus GADM): edge spill
     along the boundary line, or detached blocks?
  4. boundary alignment: distance from sampled LSZ boundary vertices to the
     GADM boundary (median / p95 / max, metres) — quantifies the boundary-line
     difference behind the ~4% mismatch.
  5. the .shp.xml ArcGIS metadata shipped INSIDE the archive: extract title /
     credits / purpose tags (official in-file provenance evidence).

Evidence -> data/interim/lsz_reference/boundary_fit_diagnostics.json
(raw files are read-only here; nothing is modified.)

Run:  python scripts/diagnose_lsz_boundary_fit.py
"""
from __future__ import annotations

import json
import pathlib
import sys
import xml.etree.ElementTree as ET

import geopandas as gpd
import numpy as np
from shapely import wkt
from shapely.ops import unary_union

ROOT = pathlib.Path(__file__).resolve().parents[1]
LAYER = ROOT / "data" / "interim" / "lsz_reference" / "extracted" / "Wayanad" / "Wayanad_GSI_LS.shp"
SHPXML = LAYER.with_suffix(".shp.xml")
GADM = ROOT / "data" / "raw" / "boundary" / "gadm41_IND_2" / "gadm41_IND_2.json"
OSM = ROOT / "data" / "raw" / "boundary" / "osm_nominatim_wayanad.geojson"
OUT = ROOT / "data" / "interim" / "lsz_reference" / "boundary_fit_diagnostics.json"
K2 = 1e6


def part_summary(geom, keep=6):
    parts = list(geom.geoms) if geom.geom_type.startswith("Multi") else [geom]
    parts = sorted(parts, key=lambda g: g.area, reverse=True)
    out = []
    for g in parts[:keep]:
        c = g.centroid
        out.append({"area_km2": round(g.area / K2, 4),
                    "bbox_wgs84": [round(c.x, 4), round(c.y, 4),
                                   round(g.bounds[0], 4), round(g.bounds[1], 4),
                                   round(g.bounds[2], 4), round(g.bounds[3], 4)],
                    "centroid_wgs84_note": "first two values are centroid lon/lat",
                    "n_vertices": len(list(g.exterior.coords)) if hasattr(g, "exterior") else None})
    return {"n_parts": len(parts), "total_km2": round(geom.area / K2, 4),
            "largest_parts": out}


def main() -> int:
    lsz = gpd.read_file(LAYER).to_crs(32643)
    gadm = unary_union(list(gpd.read_file(GADM).query("NAME_2 == 'Wayanad'").to_crs(32643).geometry))
    osm = unary_union(list(gpd.read_file(OSM).to_crs(32643).geometry))

    rec: dict = {"layer": str(LAYER.relative_to(ROOT))}

    # ---- 1. validity + buffer(0) sensitivity -------------------------------
    per_class = []
    for _, row in lsz.iterrows():
        g = row.geometry
        fixed = g.buffer(0)
        per_class.append({
            "susceptibi": row["Susceptibi"],
            "is_valid_raw": bool(g.is_valid),
            "explanation": getattr(g, "explain_validity", lambda: None)(),
            "area_raw_km2": round(g.area / K2, 4),
            "area_buffer0_km2": round(fixed.area / K2, 4),
            "n_parts_raw": len(g.geoms) if g.geom_type.startswith("Multi") else 1,
            "n_parts_buffer0": len(fixed.geoms) if fixed.geom_type.startswith("Multi") else 1,
        })
    rec["validity_and_area_sensitivity"] = per_class
    raw_sum = sum(p["area_raw_km2"] for p in per_class)
    fix_sum = sum(p["area_buffer0_km2"] for p in per_class)
    rec["area_totals"] = {"raw_sum_km2": round(raw_sum, 4),
                          "buffer0_sum_km2": round(fix_sum, 4),
                          "delta_km2": round(raw_sum - fix_sum, 4)}

    # ---- 2/3. difference shapes --------------------------------------------
    lsz_u = unary_union(list(lsz.geometry))
    rec["gadm_minus_lsz"] = part_summary(gadm.difference(lsz_u))
    rec["lsz_minus_gadm"] = part_summary(lsz_u.difference(gadm))
    rec["osm_minus_lsz"] = {"n_parts_total_km2":
                            round(osm.difference(lsz_u).area / K2, 4)}

    # ---- 4. boundary alignment ---------------------------------------------
    from shapely import prepare
    gadm_b = gadm.boundary
    prepare(gadm_b)
    pts = []
    for g in (list(lsz_u.geoms) if lsz_u.geom_type.startswith("Multi") else [lsz_u]):
        pts += list(g.exterior.coords)
    step = max(1, len(pts) // 1500)
    sample = [wkt.loads(f"POINT ({x} {y})") for x, y in pts[::step]]
    d = np.array([gadm_b.distance(p) for p in sample])
    rec["boundary_alignment_vs_gadm"] = {
        "sampled_lsz_boundary_vertices": int(len(d)),
        "median_m": round(float(np.median(d)), 1),
        "p95_m": round(float(np.percentile(d, 95)), 1),
        "max_m": round(float(d.max()), 1),
        "share_within_100m": round(float((d <= 100).mean()), 4),
        "share_within_250m": round(float((d <= 250).mean()), 4),
    }

    # ---- 5. in-archive ArcGIS metadata --------------------------------------
    if SHPXML.exists():
        xml_text = SHPXML.read_text(encoding="utf-8", errors="replace")
        rec["shp_xml_bytes"] = len(xml_text)
        try:
            root = ET.fromstring(xml_text)
            texts = {}
            for tag in ("title", "abstract", "purpose", "credit", "status",
                        "pubdate", "pubinfo", "custod", "datacred"):
                for el in root.iter():
                    if el.tag.split("}")[-1] == tag and el.text and el.text.strip():
                        texts.setdefault(tag, el.text.strip()[:400])
            rec["shp_xml_key_fields"] = texts
        except ET.ParseError as e:
            rec["shp_xml_key_fields"] = {"parse_error": str(e)}

    OUT.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(rec, indent=2)[:3500])
    print(f"...\nevidence -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
