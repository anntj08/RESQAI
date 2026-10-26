"""Phase 3 Stage 1 - inspect raw and derived inputs, record metadata verbatim.

Read-only. Writes a JSON snapshot to data/interim/p3/inputs_metadata.json so that
later stages can prove they did not alter the raw sources.

Run: python scripts/p3_inspect_inputs.py
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
OUT = ROOT / "data" / "interim" / "p3"
OUT.mkdir(parents=True, exist_ok=True)

RASTERS = {
    "dem_copernicus_E075": RAW / "dem/copernicus_glo30/Copernicus_DSM_COG_10_N11_00_E075_00_DEM.tif",
    "dem_copernicus_E076": RAW / "dem/copernicus_glo30/Copernicus_DSM_COG_10_N11_00_E076_00_DEM.tif",
    "landcover_worldcover_2021": RAW / "landcover/ESA_WorldCover_10m_2021_v200_N09E075_Map.tif",
}

for p in sorted((RAW / "soil/soilgrids250m").glob("*.tif")):
    RASTERS[f"soil_{p.stem.replace('soilgrids_', '')}"] = p

VECTORS = {
    "boundary_gadm": RAW / "boundary/gadm41_IND_2/gadm41_IND_2.json",
    "boundary_osm": RAW / "boundary/osm_nominatim_wayanad.geojson",
    "roads_osm_raw": RAW / "additional/osm_roads_wayanad.geojson",
    "hydrorivers_raw": RAW / "additional/hydrorivers/HydroRIVERS_v10_as_shp/HydroRIVERS_v10_as.shp",
    "geology_clip": PROC / "geology/glim_wayanad_clip.gpkg",
    "roads_clip": PROC / "additional/osm_roads_wayanad_clip.gpkg",
    "hydrorivers_clip": PROC / "additional/hydrorivers_wayanad_clip.gpkg",
}
VECTOR_LAYERS = {"geology_clip": None, "roads_clip": None, "hydrorivers_clip": None}


def describe_raster(key: str, path: Path) -> dict:
    rec: dict = {"key": key, "path": str(path.relative_to(ROOT)), "exists": path.exists()}
    if not path.exists():
        return rec
    rec["size_bytes"] = path.stat().st_size
    with rasterio.open(path) as ds:
        rec.update(
            driver=ds.driver,
            width=ds.width,
            height=ds.height,
            count=ds.count,
            dtype=ds.dtypes[0],
            crs=str(ds.crs),
            crs_wkt=ds.crs.to_wkt() if ds.crs else None,
            transform=list(ds.transform)[:6],
            bounds=list(ds.bounds),
            nodata=ds.nodata,
            nodatavals=list(ds.nodatavals),
            res=list(ds.res),
            block_shapes=list(ds.block_shapes),
            compression=str(ds.compression),
            tags={k: v for k, v in ds.tags().items()},
            descriptions=list(ds.descriptions),
            colorinterp=[c.name for c in ds.colorinterp],
        )
        # Sample statistics on a decimated read (full reads happen in stage scripts).
        scale = max(1, max(ds.width, ds.height) // 2000)
        arr = ds.read(1, out_shape=(max(1, ds.height // scale), max(1, ds.width // scale)),
                      resampling=rasterio.enums.Resampling.nearest)
        rec["sample_scale"] = scale
        rec["sample_shape"] = list(arr.shape)
        rec["sample_dtype"] = str(arr.dtype)
        if arr.size:
            finite = arr[np.isfinite(arr)]
            rec["sample_min"] = float(finite.min()) if finite.size else None
            rec["sample_max"] = float(finite.max()) if finite.size else None
            uniq = np.unique(finite)
            rec["sample_n_unique"] = int(uniq.size)
            if uniq.size <= 30:
                vals, cnts = np.unique(finite, return_counts=True)
                rec["sample_values"] = {str(int(v)) if float(v).is_integer() else str(v): int(c)
                                        for v, c in zip(vals, cnts)}
            nd = ds.nodata
            if nd is not None:
                rec["sample_nodata_pixels"] = int((arr == nd).sum())
            rec["sample_negative_9999"] = int((arr == -9999).sum())
    return rec


def describe_vector(key: str, path: Path, layer=None) -> dict:
    rec: dict = {"key": key, "path": str(path.relative_to(ROOT)), "exists": path.exists()}
    if not path.exists():
        return rec
    rec["size_bytes"] = path.stat().st_size
    gdf = gpd.read_file(path, layer=layer)
    rec.update(
        n_features=int(len(gdf)),
        crs=str(gdf.crs),
        geom_types=sorted(gdf.geom_type.dropna().unique().tolist()),
        columns=list(gdf.columns),
        dtypes={c: str(t) for c, t in gdf.dtypes.items()},
        total_bounds=list(gdf.total_bounds),
        invalid_geoms=int((~gdf.geometry.is_valid).sum()),
        empty_geoms=int(gdf.geometry.is_empty.sum()),
        null_geoms=int(gdf.geometry.isna().sum()),
    )
    if gdf.crs is not None and not gdf.crs.is_geographic:
        rec["area_km2"] = float(gdf.geometry.area.sum() / 1e6)
        rec["length_km"] = float(gdf.geometry.length.sum() / 1e3)
    rec["non_null_counts"] = {c: int(gdf[c].notna().sum()) for c in gdf.columns if c != "geometry"}
    return rec


def main() -> None:
    meta = {
        "rasters": {k: describe_raster(k, p) for k, p in RASTERS.items()},
        "vectors": {k: describe_vector(k, p, VECTOR_LAYERS.get(k)) for k, p in VECTORS.items()},
    }
    meta["chirps_file_count"] = len(list((RAW / "rainfall/chirps_v2_monthly").glob("*.tif.gz")))
    out = OUT / "inputs_metadata.json"
    out.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print("== RASTERS ==")
    for k, r in meta["rasters"].items():
        if not r["exists"]:
            print(f"{k:34s} MISSING")
            continue
        print(f"{k:34s} {r['width']}x{r['height']} {r['dtype']:8s} {r['crs']:12s} "
              f"res={r['res'][0]:.8f}x{r['res'][1]:.8f} nd={r['nodata']} "
              f"min={r['sample_min']} max={r['sample_max']} tags={list(r['tags'])[:3]}")
    print("\n== VECTORS ==")
    for k, v in meta["vectors"].items():
        if not v["exists"]:
            print(f"{k:22s} MISSING")
            continue
        print(f"{k:22s} n={v['n_features']:7d} crs={v['crs']} "
              f"types={v['geom_types']} invalid={v['invalid_geoms']} "
              f"cols={len(v['columns'])}")
    print(f"\nCHIRPS .tif.gz files: {meta['chirps_file_count']}")
    print(f"written -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
