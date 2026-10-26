"""Phase 3 Stage 7 - GLiM / LiMW 2015 geology: CRS, clip, shares, usefulness test.

Points that are easy to get wrong here:

  * The native CRS identifier is ``ESRI:54012`` (World Eckert IV). ``EPSG:54012``
    does not exist and pyproj will raise if it is used; the CRS must be read from
    the file, not typed from memory.
  * The Phase 1 product (`glim_wayanad_clip.gpkg`) is a **bounding-box** clip with
    29 polygons, only 16 of which intersect the district. It is kept as-is and a
    proper district intersection is written alongside it.
  * GLiM's average source scale is 1:3.75 million. The layer is a coarse
    contextual covariate, not a local lithology map. Instead of asserting that,
    this script measures it: the 45 inventory records that carry GSI field
    lithology are compared against the GLiM polygon under each point.

Outputs (data/processed/geology/):
  glim_wayanad_district_32643.gpkg   district intersection, metric CRS, area fields
  glim_lithology_shares.csv          class shares of the district
  geology_class_legend.csv           class index <-> GLiM code <-> description
  geology_class_30m_district.tif     class index on the study grid (coarse covariate)
  geology_validation.json

Run: python scripts/p3_geology.py
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pyproj
import rasterio
from rasterio.features import rasterize

ROOT = Path(__file__).resolve().parents[1]
GDB = ROOT / "data" / "raw" / "geology" / "glim" / "LiMW_GIS 2015.gdb"
PREV = ROOT / "data" / "processed" / "geology" / "glim_wayanad_clip.gpkg"
GRID = ROOT / "data" / "processed" / "grid"
INV = ROOT / "data" / "processed" / "inventory" / "inventory_source_records.csv"
OUT = ROOT / "data" / "processed" / "geology"
OUT.mkdir(parents=True, exist_ok=True)

# GLiM first-order + second-order codes, as published (Hartmann & Moosdorf 2012)
FIRST = {"mt": "Metamorphic rocks", "pa": "Plutonic rocks, acidic", "pb": "Plutonic rocks, basic",
         "pi": "Plutonic rocks, intermediate", "va": "Volcanic rocks, acidic",
         "vb": "Volcanic rocks, basic", "vi": "Volcanic rocks, intermediate",
         "sm": "Sedimentary rocks, mixed", "ss": "Siliciclastic sedimentary",
         "sc": "Carbonate sedimentary", "su": "Sedimentary, unconsolidated",
         "wb": "Water bodies", "nd": "No data", "ig": "Ice and glaciers",
         "py": "Pyroclastic", "ev": "Evaporites", "mt": "Metamorphic rocks"}
SECOND = {
    "mtam__": "Metamorphic, amphibolite facies",
    "mt____": "Metamorphic, undifferentiated",
    "mtgr__": "Metamorphic, granulite facies",
    "mtbl__": "Metamorphic, blueschist facies",
    "mtgs__": "Metamorphic, greenschist facies",
    "pa____": "Plutonic, acidic (granitoid / charnockite family)",
    "pa__mt": "Plutonic acidic with metamorphic overprint",
    "pb____": "Plutonic, basic",
    "pi____": "Plutonic, intermediate",
}


def main() -> None:
    spec = json.loads((GRID / "grid_spec.json").read_text(encoding="utf-8"))
    tf_grid = rasterio.transform.Affine(*spec["transform"])
    H, W, crs = spec["height"], spec["width"], spec["work_crs"]
    with rasterio.open(GRID / "district_mask_30m.tif") as ds:
        dmask = ds.read(1) == 1
    gadm = gpd.read_file(GRID / "wayanad_gadm_32643.gpkg")
    gadm4326 = gadm.to_crs("EPSG:4326")
    rep: dict = {}

    # ---- native CRS verification -------------------------------------------
    native = gpd.read_file(GDB, layer="GLiM_export", rows=1)
    native_crs = native.crs
    rep["native_crs"] = {
        "as_read": str(native_crs),
        "is_esri_54012": bool(native_crs is not None and native_crs.to_epsg() in (None, 54012)
                              and "Eckert" in native_crs.name),
        "name": native_crs.name if native_crs else None,
        "epsg_54012_resolves": None,
    }
    try:
        pyproj.CRS.from_epsg(54012)
        rep["native_crs"]["epsg_54012_resolves"] = True
    except Exception as exc:  # noqa: BLE001
        rep["native_crs"]["epsg_54012_resolves"] = f"NO - {type(exc).__name__}"

    # ---- district intersection ---------------------------------------------
    prev = gpd.read_file(PREV)
    rep["phase1_product"] = {
        "path": str(PREV.relative_to(ROOT)),
        "n_polygons": int(len(prev)),
        "n_intersecting_district": int(prev.intersects(gadm4326.union_all()).sum()),
        "type": "bounding-box clip (district bbox + 0.05 deg pad), NOT a district clip",
    }

    inter = gpd.overlay(prev.to_crs(crs), gadm[["geometry"]], how="intersection",
                        keep_geom_type=True)
    inter["area_km2"] = inter.geometry.area / 1e6
    inter["first_order"] = inter["xx"].map(FIRST).fillna("unmapped")
    inter["lithology"] = inter["Litho"].map(SECOND).fillna(inter["Litho"])
    inter = inter[["IDENTITY_", "Litho", "xx", "first_order", "lithology", "area_km2",
                   "geometry"]].sort_values("area_km2", ascending=False)
    inter = inter.reset_index(drop=True)
    inter.to_file(OUT / "glim_wayanad_district_32643.gpkg", driver="GPKG")

    total = float(inter["area_km2"].sum())
    shares = (inter.groupby(["xx", "Litho", "first_order", "lithology"])["area_km2"]
              .sum().reset_index().sort_values("area_km2", ascending=False))
    shares["share_pct"] = (shares["area_km2"] / total * 100).round(2)
    shares["area_km2"] = shares["area_km2"].round(1)
    shares.to_csv(OUT / "glim_lithology_shares.csv", index=False)

    rep["district_layer"] = {
        "n_polygons": int(len(inter)),
        "n_classes": int(shares.shape[0]),
        "area_sum_km2": round(total, 1),
        "gadm_area_km2": 2121.0,
        "coverage_of_district_pct": round(total / 2121.0 * 100, 2),
        "dominant_class": str(shares.iloc[0]["lithology"]),
        "dominant_share_pct": float(shares.iloc[0]["share_pct"]),
        "invalid_geometries": int((~inter.geometry.is_valid).sum()),
        "empty_geometries": int(inter.geometry.is_empty.sum()),
        "crs": str(inter.crs),
    }

    # ---- class index raster on the study grid ------------------------------
    classes = shares.reset_index(drop=True)
    codes = {row["Litho"]: i + 1 for i, row in classes.iterrows()}
    legend = [{"index": int(codes[r["Litho"]]), "glim_code": r["Litho"], "xx": r["xx"],
               "description": r["lithology"], "first_order": r["first_order"],
               "share_pct": float(r["share_pct"])} for _, r in classes.iterrows()]
    with (OUT / "geology_class_legend.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(legend[0].keys()))
        w.writeheader()
        w.writerows(legend)

    shapes = [(geom, codes[code]) for geom, code in zip(inter.geometry, inter["Litho"])]
    gcls = rasterize(shapes, out_shape=(H, W), transform=tf_grid, fill=0, dtype="uint8",
                     all_touched=False)
    gcls[~dmask] = 0
    with rasterio.open(OUT / "geology_class_30m_district.tif", "w", driver="GTiff",
                       width=W, height=H, count=1, dtype="uint8", crs=crs,
                       transform=tf_grid, nodata=0, compress="deflate", tiled=True) as ds:
        ds.write(gcls, 1)
        ds.set_band_description(1, "GLiM 2015 lithology class index (see legend CSV)")
        ds.update_tags(source="glim_wayanad_district_32643.gpkg",
                       script="scripts/p3_geology.py",
                       scale="1:3,750,000 average source scale",
                       warning="coarse contextual covariate; the 30 m grid does NOT imply "
                               "30 m geological detail")
    vc = np.bincount(gcls[dmask].ravel(), minlength=len(classes) + 1)
    rep["raster"] = {
        "classes_present": [int(i) for i in np.nonzero(vc)[0] if i > 0],
        "nodata_inside_district": int((gcls[dmask] == 0).sum()),
        "share_by_class_pct": {int(i): round(float(vc[i] / vc[1:].sum() * 100), 2)
                               for i in np.nonzero(vc)[0] if i > 0},
    }

    # ---- is the layer actually local enough? -------------------------------
    # 45 inventory records carry GSI field lithology; compare with the GLiM polygon.
    inv = pd.read_csv(INV)
    lith = inv[inv["geology"].notna() & (inv["geology"].astype(str).str.strip() != "")].copy()
    pts = gpd.GeoDataFrame(
        lith, geometry=gpd.points_from_xy(lith["lon_dd_original"], lith["lat_dd_original"]),
        crs="EPSG:4326").to_crs(crs)
    pts = pts[pts["inclusion"].str.startswith("INCLUDED")]
    joined = gpd.sjoin(pts, inter[["Litho", "xx", "lithology", "geometry"]], how="left",
                       predicate="within")
    joined = joined[~joined.index.duplicated(keep="first")]

    def gsi_family(text: str) -> str:
        t = str(text).lower()
        if "charnockite" in t and "gneiss" not in t:
            return "charnockite"
        if "charnockite" in t and "gneiss" in t:
            return "charnockite-gneiss"
        if "gneiss" in t or "biotite" in t:
            return "gneiss"
        if "schist" in t or "phyllit" in t:
            return "schist/phyllite"
        return "other"

    joined["gsi_family"] = joined["geology"].map(gsi_family)
    xt = pd.crosstab(joined["gsi_family"], joined["xx"].fillna("outside"))
    per_point = joined[["source_record_id", "locality", "geology", "gsi_family",
                        "xx", "lithology"]].copy()
    per_point.to_csv(OUT / "site_lithology_vs_glim.csv", index=False)

    rep["site_lithology_check"] = {
        "n_records_with_gsi_lithology": int(len(lith)),
        "n_used_inside_district": int(len(joined)),
        "n_with_glim_polygon": int(joined["xx"].notna().sum()),
        "gsi_family_counts": joined["gsi_family"].value_counts().to_dict(),
        "glim_code_counts": joined["xx"].value_counts().to_dict(),
        "crosstab": {f"{k[0]} / GLiM {k[1]}": int(v) for k, v in xt.stack().items() if v},
        "interpretation": "GSI field records distinguish charnockite from gneiss at the "
                          "outcrop; GLiM assigns both to the same broad class. Agreement at "
                          "this level of detail is therefore low by construction, which is "
                          "why GLiM is a weak covariate.",
    }

    # Nearest-neighbour scale check: how far to the nearest class boundary?
    bounds = inter.boundary.union_all()
    d = pts.geometry.apply(lambda p: bounds.distance(p))
    rep["scale_check"] = {
        "median_distance_to_class_boundary_m": round(float(d.median()), 0),
        "p90_distance_to_class_boundary_m": round(float(d.quantile(0.9)), 0),
        "min_m": round(float(d.min()), 0),
        "mean_polygon_area_km2": round(float(inter["area_km2"].mean()), 1),
        "note": "at 1:3.75 M, map distance 1 mm is ~3.75 km on the ground; polygon-scale "
                "classes are the finest signal the source can carry",
    }

    (OUT / "geology_validation.json").write_text(json.dumps(rep, indent=2), encoding="utf-8")
    print(json.dumps(rep, indent=2))
    print("\n" + shares[["xx", "Litho", "lithology", "area_km2", "share_pct"]].to_string(index=False))
    print("\n" + xt.to_string())


if __name__ == "__main__":
    main()
