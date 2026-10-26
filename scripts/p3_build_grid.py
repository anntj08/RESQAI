"""Phase 3 Stage 2 - establish the metric CRS and the common study grid.

Decision (documented in docs/PREPROCESSING_REPORT.md):
  * Working CRS  : EPSG:32643 (WGS 84 / UTM zone 43N), central meridian 75E.
                   Wayanad spans 75.77-76.44E, i.e. inside zone 43 (72E-78E).
  * Cell size    : 30 m - the native resolution of the primary terrain source.
  * Origin       : snapped outward to an exact multiple of 30 m in EPSG:32643
                   coordinates, so the grid is reproducible without carrying a
                   magic number and every layer built on it is pixel-identical.
  * Extent       : GADM Wayanad buffered by 1,000 m, so that slope/aspect/
                   curvature and any focal statistic have valid neighbours at the
                   district edge. Final products are clipped to the district mask.

The metric buffer is applied in EPSG:32643, never in degrees.

Outputs (data/processed/grid/):
  wayanad_gadm_32643.gpkg   primary working boundary, metric
  wayanad_osm_32643.gpkg    independent cross-check boundary, metric
  grid_spec.json            full grid definition + validation figures
  district_mask_30m.tif    uint8, 1 = pixel centre inside GADM polygon

Run: python scripts/p3_build_grid.py
"""
from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import rasterize

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed" / "grid"
OUT.mkdir(parents=True, exist_ok=True)

WORK_CRS = "EPSG:32643"
CELL = 30.0
BUFFER_M = 1000.0


def main() -> None:
    gadm_all = gpd.read_file(RAW / "boundary/gadm41_IND_2/gadm41_IND_2.json")
    gadm = gadm_all[gadm_all["NAME_2"] == "Wayanad"].copy()
    assert len(gadm) == 1, f"expected 1 GADM Wayanad feature, got {len(gadm)}"
    osm = gpd.read_file(RAW / "boundary/osm_nominatim_wayanad.geojson")
    assert len(osm) == 1

    gadm_m = gadm.to_crs(WORK_CRS)
    osm_m = osm.to_crs(WORK_CRS)

    gadm_area = float(gadm_m.geometry.area.sum() / 1e6)
    osm_area = float(osm_m.geometry.area.sum() / 1e6)
    gadm_union = gadm_m.geometry.union_all()
    osm_union = osm_m.geometry.union_all()
    inter = float(gadm_union.intersection(osm_union).area / 1e6)
    union = float(gadm_union.union(osm_union).area / 1e6)

    # Grid extent: buffered district, snapped outward to a multiple of CELL.
    minx, miny, maxx, maxy = gadm_m.total_bounds
    x0 = np.floor((minx - BUFFER_M) / CELL) * CELL
    y0 = np.floor((miny - BUFFER_M) / CELL) * CELL
    x1 = np.ceil((maxx + BUFFER_M) / CELL) * CELL
    y1 = np.ceil((maxy + BUFFER_M) / CELL) * CELL
    width = int(round((x1 - x0) / CELL))
    height = int(round((y1 - y0) / CELL))
    transform = rasterio.transform.from_origin(x0, y1, CELL, CELL)

    mask = rasterize(
        [(geom, 1) for geom in gadm_m.geometry],
        out_shape=(height, width),
        transform=transform,
        fill=0,
        all_touched=False,
        dtype="uint8",
    )
    n_district = int(mask.sum())
    mask_area = n_district * CELL * CELL / 1e6

    # Same mask at 10 m, to quantify how much district area a 30 m mask loses.
    cell10 = 10.0
    t10 = rasterio.transform.from_origin(x0, y1, cell10, cell10)
    w10 = int(round((x1 - x0) / cell10))
    h10 = int(round((y1 - y0) / cell10))
    mask10 = rasterize([(g, 1) for g in gadm_m.geometry], out_shape=(h10, w10),
                       transform=t10, fill=0, all_touched=False, dtype="uint8")
    mask10_area = int(mask10.sum()) * cell10 * cell10 / 1e6

    spec = {
        "work_crs": WORK_CRS,
        "work_crs_note": "UTM 43N; central meridian 75E; Wayanad 75.77-76.44E lies inside the zone",
        "cell_size_m": CELL,
        "buffer_m": BUFFER_M,
        "origin_x": float(x0),
        "origin_y": float(y0),
        "origin_rule": "floor/ceil of (district bounds -/+ buffer) to a multiple of 30 m, EPSG:32643",
        "width": width,
        "height": height,
        "transform": list(transform)[:6],
        "bounds": [float(x0), float(y0), float(x1), float(y1)],
        "n_pixels": width * height,
        "n_district_pixels": n_district,
        "district_mask_area_km2": round(mask_area, 1),
        "district_mask_area_10m_km2": round(mask10_area, 1),
        "gadm_area_km2": round(gadm_area, 1),
        "osm_area_km2": round(osm_area, 1),
        "intersection_km2": round(inter, 1),
        "union_km2": round(union, 1),
        "iou": round(inter / union, 5),
        "area_diff_pct": round((osm_area - gadm_area) / gadm_area * 100, 3),
        "mask_vs_polygon_pct": round((mask_area - gadm_area) / gadm_area * 100, 3),
        "bbox_4326": [round(v, 6) for v in gadm.total_bounds],
    }

    gadm_m.to_file(OUT / "wayanad_gadm_32643.gpkg", driver="GPKG")
    osm_m.to_file(OUT / "wayanad_osm_32643.gpkg", driver="GPKG")
    with rasterio.open(
        OUT / "district_mask_30m.tif", "w", driver="GTiff", width=width, height=height,
        count=1, dtype="uint8", crs=WORK_CRS, transform=transform, nodata=255,
        compress="deflate", tiled=True, blockxsize=256, blockysize=256,
    ) as ds:
        ds.write(mask, 1)
        ds.set_band_description(1, "1 = pixel centre inside GADM 4.1 Wayanad")
        ds.update_tags(**{
            "source": "data/raw/boundary/gadm41_IND_2/gadm41_IND_2.json (NAME_2=Wayanad)",
            "script": "scripts/p3_build_grid.py",
            "rule": "rasterio.features.rasterize, all_touched=False (pixel-centre rule)",
        })
    (OUT / "grid_spec.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")

    print(json.dumps(spec, indent=2))
    print(f"\nwritten -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
