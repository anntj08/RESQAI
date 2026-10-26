"""Assert every Phase 3 number quoted in the documentation against the actual outputs.

The point is not to re-test the pipeline (the p3_* scripts already assert internally).
The point is to make documentation drift a build failure: if a raster is regenerated
and a figure moves, this script fails instead of shipping prose that no longer
matches the file it cites.

Run:  python scripts/p3_check_consistency.py
Exit: 0 = docs and data agree; 1 = at least one mismatch (printed).
"""
from __future__ import annotations

import csv
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
P = ROOT / "data" / "processed"
DOCS = ROOT / "docs"

failures: list[str] = []
n_checks = 0


def num(label: str, got, want, tol: float = 0.0) -> None:
    global n_checks
    n_checks += 1
    try:
        ok = abs(float(got) - float(want)) <= tol
    except (TypeError, ValueError):
        ok = False
    if not ok:
        failures.append(f"{label}: got {got!r}, expected {want!r} (tol {tol})")


def eq(label: str, got, want) -> None:
    global n_checks
    n_checks += 1
    if got != want:
        failures.append(f"{label}: got {got!r}, expected {want!r}")


def true(label: str, cond, detail: str = "") -> None:
    global n_checks
    n_checks += 1
    if not cond:
        failures.append(f"{label}: expected true {detail}".strip())


def load(rel: str) -> dict:
    with open(P / rel, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------- grid -------
grid = load("grid/grid_spec.json")
eq("grid.crs", grid["work_crs"], "EPSG:32643")
num("grid.cell", grid["cell_size_m"], 30.0)
eq("grid.width", grid["width"], 2480)
eq("grid.height", grid["height"], 2013)
num("grid.origin_x", grid["origin_x"], 583110.0)
num("grid.origin_y", grid["origin_y"], 1264170.0)
eq("grid.transform", [round(v, 6) for v in grid["transform"]],
   [30.0, 0.0, 583110.0, 0.0, -30.0, 1324560.0])
eq("grid.n_pixels", grid["n_pixels"], grid["width"] * grid["height"])
eq("grid.n_district_pixels", grid["n_district_pixels"], 2356538)
num("grid.district_area_km2", grid["district_mask_area_km2"], 2120.9, 0.05)
num("grid.gadm_area_km2", grid["gadm_area_km2"], 2121.0, 0.05)
num("grid.mask_vs_polygon_pct", grid["mask_vs_polygon_pct"], -0.005, 0.0005)
num("grid.area_10m_km2", grid["district_mask_area_10m_km2"], 2121.0, 0.05)
# the district straddles 76E: both DEM tiles are required
true("grid.straddles_76E", grid["bbox_4326"][0] < 76.0 < grid["bbox_4326"][2])

# ------------------------------------------------------------ boundary -------
bnd = load("grid/boundary_diagnostics.json")
num("boundary.gadm_to_osm.median_m", bnd["gadm_vertices_to_osm"]["median_m"], 744.1, 0.05)
num("boundary.osm_to_gadm.median_m", bnd["osm_vertices_to_gadm"]["median_m"], 770.7, 0.05)
num("boundary.gadm_to_osm.p90_m", bnd["gadm_vertices_to_osm"]["p90_m"], 1078.2, 0.05)
num("boundary.osm_to_gadm.p90_m", bnd["osm_vertices_to_gadm"]["p90_m"], 1148.2, 0.05)
num("boundary.gadm_to_osm.max_m", bnd["gadm_vertices_to_osm"]["max_m"], 1462.3, 0.05)
num("boundary.osm_to_gadm.max_m", bnd["osm_vertices_to_gadm"]["max_m"], 1578.6, 0.05)
num("boundary.symmetric_diff_pct", bnd["asymmetric_diff_pct_of_gadm"], 8.75, 0.005)
num("boundary.only_gadm_km2", bnd["area_only_gadm_km2"], 89.05, 0.005)
num("boundary.only_osm_km2", bnd["area_only_osm_km2"], 96.6, 0.05)
eq("boundary.records_outside_gadm", bnd["inventory_outside_gadm"], 23)
eq("boundary.records_outside_gadm_inside_osm", bnd["inventory_outside_gadm_but_inside_osm"], 4)
eq("boundary.flipped_record_count", len(bnd["flipped_records"]), 4)
num("boundary.largest_gadm_only_patch_km2", bnd["patches_only_gadm_ge1km2"][0]["area_km2"], 42.18, 0.005)
num("boundary.largest_osm_only_patch_km2", bnd["patches_only_osm_ge1km2"][0]["area_km2"], 56.56, 0.005)
# area agreement is not outline agreement
true("boundary.area_vs_outline_disagreement",
     bnd["gadm_vertices_to_osm"]["median_m"] > 700 and grid["area_diff_pct"] < 0.5)

# ----------------------------------------------------------------- DEM -------
dem = load("dem/dem_validation.json")
true("dem.same_node_grid", dem["same_node_grid"])
eq("dem.extra_edge_columns", dem["srtm_extra_edge_nodes"]["extra_columns_before_trim"], 1)
eq("dem.extra_edge_rows", dem["srtm_extra_edge_nodes"]["extra_rows_before_trim"], 1)
num("dem.copernicus_nan", dem["copernicus_tiles"]["nan_pixels"], 0)
num("dem.mosaic_width", dem["copernicus_tiles"]["mosaic_shape"][1], 7200)
num("dem.mosaic_height", dem["copernicus_tiles"]["mosaic_shape"][0], 3600)

cross = dem["cross_dem"]
eq("dem.cross.n", cross["n_nodes_in_district"], 2280319)
num("dem.cross.mean_diff", cross["mean_diff_m"], -1.27, 0.005)
num("dem.cross.mad", cross["mad_m"], 3.42, 0.005)
num("dem.cross.p95", cross["p95_absdiff_m"], 8.74, 0.005)
num("dem.cross.max", cross["max_absdiff_m"], 147.03, 0.005)
eq("dem.cross.n_gt_50", cross["n_gt_50m"], 447)
num("dem.cross.r", cross["pearson_r"], 0.9997, 0.00005)
true("dem.cross.tail_is_rare", cross["n_gt_50m"] / cross["n_nodes_in_district"] < 0.001)

shift = dem["registration_shift_test"]
eq("dem.shift.best_dx", shift["best"]["dx_px"], 0.0)
eq("dem.shift.best_dy", shift["best"]["dy_px"], 0.0)
num("dem.shift.mad_at_zero", shift["mad_at_zero_shift_m"], 3.42, 0.005)
num("dem.shift.gain", shift["mad_gain_at_best_m"], 0.0, 1e-9)
cand = {(c["dx_px"], c["dy_px"]): c["mad_m"] for c in shift["candidates"]}
for dx in (-0.5, 0.5):
    true(f"dem.shift.x_{dx}_worse_than_zero", cand[(dx, 0.0)] > cand[(0.0, 0.0)])
for dy in (-0.5, 0.5):
    true(f"dem.shift.y_{dy}_worse_than_zero", cand[(0.0, dy)] > cand[(0.0, 0.0)])
num("dem.shift.pixel_m", shift["pixel_m_approx"], 30.3, 0.1)

eq("dem.reproj.nodata_buffered", dem["reprojection"]["nodata_pixels_buffered"], 0)
eq("dem.reproj.valid_district", dem["reprojection"]["valid_pixels_district"], 2356538)
num("dem.elev_district_min", dem["reprojection"]["elev_range_district_m"][0], 116.96, 0.005)
num("dem.elev_district_max", dem["reprojection"]["elev_range_district_m"][1], 2230.27, 0.005)
num("dem.stats.mean", dem["dem_district_stats"]["mean"], 854.59, 0.005)
num("dem.stats.median", dem["dem_district_stats"]["median"], 803.83, 0.005)
num("dem.stats.std", dem["dem_district_stats"]["std"], 179.89, 0.005)
num("dem.pct_below_300m", dem["elevation_range_note"]["pct_below_300m"], 0.196, 0.0005)
num("dem.pct_above_2000m", dem["elevation_range_note"]["pct_above_2000m"], 0.065, 0.0005)
# the phase-1 range must not reappear as current
eq("dem.phase1_range_superseded",
   dem["elevation_range_note"]["phase1_quoted_district_range_m"], [165, 1849])
true("dem.range_actually_differs",
     dem["reprojection"]["elev_range_district_m"][0] < 165
     and dem["reprojection"]["elev_range_district_m"][1] > 1849)

der = dem["derivatives"]
num("dem.slope.mean", der["slope"]["mean"], 11.53, 0.005)
num("dem.slope.max", der["slope"]["max"], 67.77, 0.005)
num("dem.slope.p99", der["slope"]["p99"], 39.15, 0.005)
num("dem.aspect.median", der["aspect"]["median"], 177.48, 0.005)
eq("dem.aspect.flat_pixels", der["aspect"]["flat_pixels_district"], 11380)
num("dem.aspect.nodata_pct", der["nodata_inside_district"]["aspect"]
    / 2356538 * 100, 0.483, 0.0005)
eq("dem.curv.nodata", der["nodata_inside_district"]["profile_curvature"], 0)
num("dem.profile.min", der["profile_curvature"]["min"], -0.0459, 0.00005)
num("dem.profile.max", der["profile_curvature"]["max"], 0.0625, 0.00005)
num("dem.plan.min", der["plan_curvature"]["min"], -0.0511, 0.00005)
num("dem.plan.max", der["plan_curvature"]["max"], 0.0422, 0.00005)
num("dem.sanity.slope_gt_60_pct", dem["sanity"]["slope_gt_60_pct"], 0.011, 0.0005)
num("dem.sanity.slope_lt_2_pct", dem["sanity"]["slope_lt_2deg_pct"], 6.656, 0.0005)
true("dem.sanity.slope_le_90", dem["sanity"]["slope_le_90"])
num("dem.sanity.curv_violations", dem["sanity"]["curv_abs_gt_1_per_m_pct"], 0.0)

buf = dem["buffer_test"]
eq("dem.buffer.ring_pixels", buf["ring_pixels"], 15514)
eq("dem.buffer.lost", buf["ring_pixels_lost_without_buffer"], 10873)
num("dem.buffer.lost_pct", buf["ring_pct_lost_without_buffer"], 70.09, 0.005)
num("dem.buffer.max_diff", buf["ring_max_abs_slope_diff_deg"], 0.0)
num("dem.buffer.interior_diff", buf["interior_max_abs_slope_diff_deg"], 0.0)

rt = dem["roundtrip_native_utm_native"]
num("dem.roundtrip.mad", rt["mad_m"], 0.883, 0.0005)
num("dem.roundtrip.p99", rt["p99_abs_m"], 4.027, 0.0005)
num("dem.roundtrip.max", rt["max_abs_m"], 15.984, 0.0005)

ground = dem["georeferencing_ground_checks"]
eq("dem.ground.n_towns", len(ground), 4)
for town, vals in ground.items():
    true(f"dem.ground.{town}_within_50m", abs(vals["delta_m"]) < 50)
num("dem.ground.kalpetta", ground["Kalpetta"]["glo30_m"], 750.1, 0.05)

cs = dem["cross_dem_slope"]
num("dem.cross_slope.mad", cs["mad_deg"], 2.24, 0.005)
num("dem.cross_slope.p95", cs["p95_abs_diff_deg"], 5.96, 0.005)
num("dem.cross_slope.r", cs["pearson_r"], 0.943, 0.0005)
num("dem.cross_slope.srtm_mean", cs["srtm_mean_deg"], 10.69, 0.005)

# ----------------------------------------------------------- land cover ------
lc = load("landcover/landcover_validation.json")
nw = lc["native_window"]
eq("lc.window.district_pixels", nw["district_pixels"], 25337122)
num("lc.window.area_km2", nw["district_area_km2"], 2121.9, 0.05)
num("lc.window.pixel_area_m2", nw["pixel_area_m2_at_centre_lat"], 83.75, 0.005)
num("lc.window.naive_area_km2", nw["naive_100m2_area_km2"], 2533.7, 0.05)
true("lc.naive_area_is_19pct_too_big",
     nw["naive_100m2_area_km2"] / nw["district_area_km2"] > 1.19)

nc = lc["native_classes"]
num("lc.tree.share", nc["10"]["share_pct"], 89.629, 0.0005)
num("lc.grass.share", nc["30"]["share_pct"], 5.899, 0.0005)
num("lc.crop.share", nc["40"]["share_pct"], 2.953, 0.0005)
num("lc.built.share", nc["50"]["share_pct"], 0.913, 0.0005)
num("lc.bare.share", nc["60"]["share_pct"], 0.019, 0.0005)
num("lc.water.share", nc["80"]["share_pct"], 0.581, 0.0005)
num("lc.wetland.share", nc["90"]["share_pct"], 0.004, 0.0005)
eq("lc.shrubland.pixels", nc["20"]["pixels"], 1)

agg = lc["aggregation"]
eq("lc.grid.district_pixels", agg["district_pixels"], 2356538)
eq("lc.grid.nodata", agg["nodata_inside_district"], 0)
num("lc.max_share_change_pp", agg["max_abs_share_change_pp"], 0.495, 0.0005)
num("lc.disagreement_vs_nearest_pct", agg["disagreement_vs_nearest_pct"], 1.21, 0.005)
eq("lc.classes_retained", agg["classes_retained"], [10, 30, 40, 50, 60, 80, 90])
eq("lc.unexpected_codes", agg["unexpected_codes"], [])
num("lc.nonpure_blocks_pct", lc["native_heterogeneity_3x3"]["pct_with_any_differing_neighbour"],
    8.62, 0.005)

# ------------------------------------------------------------- rainfall ------
rf = load("rainfall/rainfall_validation.json")
eq("rf.n_files", rf["n_files"], 312)
eq("rf.first_month", rf["date_sequence"]["first"], "2000-01")
eq("rf.last_month", rf["date_sequence"]["last"], "2025-12")
true("rf.no_2026", "2026" not in rf["date_sequence"]["last"])
eq("rf.missing", rf["date_sequence"]["missing"], [])
eq("rf.duplicates", rf["date_sequence"]["duplicates"], 0)
true("rf.sequence_assertion", rf["date_sequence"]["assertion_passed"])
eq("rf.files_read_ok", rf["file_reads"]["n_read_ok"], 312)
eq("rf.sentinel_in_district_cells",
   rf["file_reads"]["files_with_sentinel_inside_district_cells"], 0)
eq("rf.sentinel_in_padded_window",
   rf["file_reads"]["files_with_sentinel_in_padded_window"], 312)
true("rf.nodata_not_declared", rf["grid"]["nodata_declared"] is None)
eq("rf.grid.area_or_point", rf["grid"]["area_or_point"], "Area")
eq("rf.window.n_cells", rf["window"]["n_cells"], rf["window"]["width"] * rf["window"]["height"])
eq("rf.overlap_cells", rf["weights"]["cells_with_any_district_overlap"], 97)
num("rf.equivalent_full_cells", rf["weights"]["equivalent_full_cells"], 68.985, 0.0005)

ds = rf["district_series"]
eq("rf.n_months", ds["n_months"], 312)
num("rf.monthly_min", ds["monthly_min"], 5.82, 0.005)
num("rf.monthly_mean", ds["monthly_mean"], 203.26, 0.005)
num("rf.monthly_max", ds["monthly_max"], 976.56, 0.005)
num("rf.annual_mean", ds["annual_mean_mm"], 2439.1, 0.05)
num("rf.annual_std", ds["annual_std_mm"], 351.0, 0.05)
num("rf.annual_min", ds["annual_min_mm"], 1571.0, 0.05)
eq("rf.annual_min_year", ds["annual_min_year"], 2016)
num("rf.annual_max", ds["annual_max_mm"], 3128.0, 0.05)
eq("rf.annual_max_year", ds["annual_max_year"], 2007)
num("rf.jjas_mean", ds["jjas_mean_mm"], 1601.1, 0.05)
num("rf.jjas_share", ds["jjas_share_of_annual_pct"], 65.6, 0.05)
num("rf.wettest_month", ds["wettest_month_mean_mm"], 554.0, 0.05)
eq("rf.wettest_month_number", ds["wettest_month"], 7)
num("rf.dry_month_mean", ds["dry_month_mean_mm"], 19.4, 0.05)
num("rf.2024_07_check", rf["local_consistency_check"]["chirps_2024_07_district_mean_mm"], 698.8, 0.05)

rgr = rf["study_grid_rasters"]
num("rf.raster.annual_min", rgr["rainfall_annual_mean_30m_district.tif"]["min"], 1529.7, 0.05)
num("rf.raster.annual_max", rgr["rainfall_annual_mean_30m_district.tif"]["max"], 3468.6, 0.05)
num("rf.raster.jjas_min", rgr["rainfall_jjas_mean_30m_district.tif"]["min"], 792.0, 0.05)
num("rf.raster.jjas_max", rgr["rainfall_jjas_mean_30m_district.tif"]["max"], 2457.7, 0.05)
eq("rf.raster.climatology_bands",
   rgr["rainfall_monthly_climatology_30m_district.tif"]["bands"], 12)
for k, v in rgr.items():
    eq(f"rf.raster.{k}.nodata", v.get("nodata_inside_district", 0), 0)

# ----------------------------------------------------------------- soil ------
soil = load("soil/soil_validation.json")
eq("soil.n_files", soil["n_files"], 14)
chk = soil["checks"]
true("soil.zero_footprint_identical", chk["zero_footprint_identical_across_all_14"])
eq("soil.zero_cells", chk["zero_cells_per_file"], 8312)
eq("soil.zero_cells_min", chk["zero_cells_per_file_min"], 8312)
eq("soil.zero_cells_max", chk["zero_cells_per_file_max"], 8312)
eq("soil.zero_any", chk["n_cells_where_any_file_is_zero"], 8312)
eq("soil.zero_all", chk["n_cells_where_all_files_are_zero"], 8312)
num("soil.grid_nodata_pct", chk["grid_nodata_inside_district_pct"], 0.155, 0.0005)
eq("soil.plausibility_violations", chk["plausibility_violations"], {})
true("soil.all_outputs_have_data", chk["all_outputs_have_data_inside_district"])
for depth, t in soil["texture_closure"].items():
    num(f"soil.texture.{depth}.mean", t["mean_sum_pct"], 100.0, 0.005)
    num(f"soil.texture.{depth}.p05", t["p05_pct"], 99.94, 0.005)
    num(f"soil.texture.{depth}.p95", t["p95_pct"], 100.06, 0.005)
    num(f"soil.texture.{depth}.share", t["share_within_1pp_of_100"], 100.0, 0.005)
eq("soil.nodata_rule", soil["nodata_decision"]["rule"], "raw value 0 -> nodata for all 14 rasters")

soil_csv = list(csv.DictReader(open(P / "soil/soil_properties.csv", encoding="utf-8")))
eq("soil.csv.rows", len(soil_csv), 14)
true("soil.csv.native_valid",
     all(int(r["valid_cells_native_in_district"]) == 32514 for r in soil_csv))
true("soil.csv.native_nodata",
     all(int(r["nodata_cells_native_in_district"]) == 50 for r in soil_csv))
true("soil.csv.grid_valid",
     all(int(r["grid_valid_pixels"]) == 2352881 for r in soil_csv))
true("soil.csv.grid_nodata",
     all(int(r["grid_nodata_pixels"]) == 3657 for r in soil_csv))

# -------------------------------------------------------------- geology ------
geo = load("geology/geology_validation.json")
true("geo.native_crs_is_esri", geo["native_crs"]["is_esri_54012"])
true("geo.epsg_54012_does_not_resolve", "CRSError" in geo["native_crs"]["epsg_54012_resolves"])
eq("geo.phase1.bbox_clip_polygons", geo["phase1_product"]["n_polygons"], 29)
eq("geo.phase1.intersecting", geo["phase1_product"]["n_intersecting_district"], 16)
dl = geo["district_layer"]
eq("geo.district.polygons", dl["n_polygons"], 16)
eq("geo.district.classes", dl["n_classes"], 5)
num("geo.district.area_km2", dl["area_sum_km2"], 2121.0, 0.05)
num("geo.district.coverage_pct", dl["coverage_of_district_pct"], 100.0, 0.005)
eq("geo.district.invalid", dl["invalid_geometries"], 0)
eq("geo.raster.classes", geo["raster"]["classes_present"], [1, 2, 3, 4, 5])
eq("geo.raster.nodata", geo["raster"]["nodata_inside_district"], 0)
shares = geo["raster"]["share_by_class_pct"]
num("geo.share.1", shares["1"], 57.81, 0.005)
num("geo.share.2", shares["2"], 26.45, 0.005)
num("geo.share.3", shares["3"], 12.57, 0.005)
num("geo.share.4", shares["4"], 3.14, 0.005)
num("geo.share.5", shares["5"], 0.03, 0.005)
sl = geo["site_lithology_check"]
eq("geo.sites.with_lithology", sl["n_records_with_gsi_lithology"], 45)
eq("geo.sites.in_district", sl["n_used_inside_district"], 45)
eq("geo.sites.with_polygon", sl["n_with_glim_polygon"], 43)
eq("geo.sites.crosstab_total", sum(sl["crosstab"].values()), 45)
eq("geo.sites.charnockite_gneiss_pa", sl["crosstab"]["charnockite-gneiss / GLiM pa"], 22)
eq("geo.sites.charnockite_gneiss_mt", sl["crosstab"]["charnockite-gneiss / GLiM mt"], 14)
eq("geo.sites.charnockite_gneiss_pb", sl["crosstab"]["charnockite-gneiss / GLiM pb"], 1)
eq("geo.sites.charnockite_gneiss_outside", sl["crosstab"]["charnockite-gneiss / GLiM outside"], 2)
num("geo.scale.median_m", geo["scale_check"]["median_distance_to_class_boundary_m"], 1063.0, 0.05)
num("geo.scale.p90_m", geo["scale_check"]["p90_distance_to_class_boundary_m"], 4623.0, 0.05)
num("geo.scale.mean_polygon_km2", geo["scale_check"]["mean_polygon_area_km2"], 132.6, 0.05)

# ----------------------------------------------------------- additional ------
add = load("additional/additional_layers_validation.json")
rd = add["roads"]
eq("roads.raw.n", rd["raw"]["n_features"], 24063)
eq("roads.clip.n", rd["clip"]["n_features"], 13169)
num("roads.raw.km", rd["raw"]["metric_length_km"], 11758.5, 0.05)
num("roads.clip.km", rd["clip"]["metric_length_km"], 5968.2, 0.05)
eq("roads.clip.features_lost", rd["clip_completeness"]["features_lost_entirely"], 0)
num("roads.clip.length_retained_pct", rd["clip_completeness"]["length_retained_pct"], 100.0, 0.005)
for field in ("invalid", "empty", "null", "zero_length", "duplicate_wkb"):
    eq(f"roads.clip.{field}", rd["clip"][field], 0)
eq("roads.primary_count", rd["highway_classes"]["primary"], 126)
eq("roads.trunk_count", rd["highway_classes"]["trunk"], 83)
num("roads.attr.highway_pct", rd["attribute_completeness_pct"]["highway"], 100.0, 0.005)
num("roads.attr.surface_pct", rd["attribute_completeness_pct"]["surface"], 10.8, 0.05)
num("roads.attr.ref_pct", rd["attribute_completeness_pct"]["ref"], 3.9, 0.05)
num("roads.attr.name_pct", rd["attribute_completeness_pct"]["name"], 8.3, 0.05)

rv = add["rivers"]
eq("rivers.clip.n", rv["clip"]["n_features"], 1298)
num("rivers.clip.km", rv["clip"]["metric_length_km"], 3195.5, 0.05)
num("rivers.attr_km", rv["length_sum_km_vs_attribute"]["LENGTH_KM_attribute_total"], 3384.4, 0.05)
eq("rivers.duplicate_id", rv["duplicate_hyriv_id"], 0)
eq("rivers.truncated", rv["connectivity"]["segments_truncated_at_the_district_edge"], 40)
num("rivers.truncated_pct", rv["connectivity"]["truncation_pct"], 3.08, 0.005)
eq("rivers.orders", rv["stream_order_distribution"],
   {"1": 673, "2": 322, "3": 178, "4": 84, "5": 41})

# ------------------------------------------------------------ inventory ------
inv_sum = load("inventory/inventory_suitability_summary.json")
eq("inv.input.records", inv_sum["input"]["records"], 468)
eq("inv.phase2_tables_modified", inv_sum["phase2_tables_modified"], False)
eq("inv.label_roles", inv_sum["counts_by_label_role"],
   {"EVENT_POINT_IN_WINDOW": 372, "SITE_EVIDENCE_UNDATED": 78,
    "EXCLUDED_NOT_IN_DISTRICT": 12, "HISTORICAL_PRE_2000": 6})
eq("inv.spatial_use", inv_sum["counts_by_spatial_use"],
   {"point_label_ok": 408, "review_widen_label": 36, "review_boundary_uncertain": 10,
    "exclude_not_in_district": 12, "exclude_district_centroid": 1,
    "exclude_until_corrected": 1})
eq("inv.precision_classes", inv_sum["counts_by_precision_class"],
   {"A_PRECISE_LE_100M": 424, "C_COARSE_300_800M": 44})
eq("inv.in_window", inv_sum["in_window_records"], 372)
eq("inv.in_window_by_class", inv_sum["in_window_by_precision_class"],
   {"A_PRECISE_LE_100M": 370, "C_COARSE_300_800M": 2})

td = inv_sum["two_decimal_records"]
eq("inv.two_dp.n", td["n"], 44)
eq("inv.two_dp.by_source", td["by_source"], {"GSI14337": 35, "NASA_GLC": 9})
eq("inv.two_dp.dated_in_window", td["n_dated_in_window"], 2)
eq("inv.two_dp.unique_coords", td["unique_coordinates_among_the_35_gsi14337"], 28)
eq("inv.two_dp.sharing", td["gsi14337_records_sharing_a_coordinate"], 12)
eq("inv.two_dp.dated_ids",
   sorted(r["source_record_id"] for r in td["dated_in_window_records"]),
   ["GLC/10011", "GLC/101"])

cw = inv_sum["crosswalk_resolution"]
eq("inv.crosswalk.considered", cw["pairs_considered"], 35)
eq("inv.crosswalk.accepted", cw["accepted_le_1.5km"], 33)
eq("inv.crosswalk.rejected", cw["rejected_gt_1.5km"], 2)
eq("inv.crosswalk.targets", cw["distinct_14115_targets"], 26)
num("inv.crosswalk.reject_1_m", cw["rejected_detail"][0]["distance_m"], 7428.8, 0.05)
num("inv.crosswalk.reject_2_m", cw["rejected_detail"][1]["distance_m"], 16579.0, 0.05)

eg = inv_sum["event_groups"]
eq("inv.groups.n", eg["n_groups"], 371)
eq("inv.groups.with_label", eg["groups_with_at_least_one_point_label"], 363)
eq("inv.groups.without_label", eg["groups_without_a_point_label"], 8)
eq("inv.groups.2018", eg["groups_2018"], 339)
eq("inv.groups.non_2018", eg["groups_non_2018"], 32)

pc = inv_sum["precision_corrections"]
eq("inv.precision_corrections.n", len(pc), 1)
num("inv.correction.value", pc[0]["corrected_to_deg"], 0.000278, 0.0000005)

# the correction must actually be present in the CSV, not just the summary
rows = list(csv.DictReader(open(P / "inventory/inventory_spatial_suitability.csv", encoding="utf-8")))
eq("inv.csv.rows", len(rows), 468)
fixed = [r for r in rows if r["source_record_id"] == pc[0]["source_record_id"]]
eq("inv.csv.corrected_row_found", len(fixed), 1)
num("inv.csv.corrected_precision", float(fixed[0]["coord_precision_deg_verified"]), 0.000278, 0.0000005)
num("inv.csv.corrected_uncertainty", float(fixed[0]["positional_uncertainty_m"]), 15.5, 0.05)
true("inv.csv.correction_note", len(fixed[0]["precision_correction_note"]) > 0)
true("inv.csv.stored_precision_unchanged",
     abs(float(fixed[0]["coord_precision_deg_stored"]) - 2.778e-06) < 1e-9)

two_dp = [r for r in rows
          if float(r["coord_precision_deg_stored"]) >= 0.009]
eq("inv.csv.two_dp.rows", len(two_dp), 44)
eq("inv.csv.two_dp.point_labels", sum(r["spatial_suitability_use"] == "point_label_ok" for r in two_dp), 0)
eq("inv.csv.two_dp.widen", sum(r["spatial_suitability_use"] == "review_widen_label" for r in two_dp), 36)
eq("inv.csv.two_dp.not_in_district",
   sum(r["spatial_suitability_use"] == "exclude_not_in_district" for r in two_dp), 7)
eq("inv.csv.two_dp.centroid",
   sum(r["spatial_suitability_use"] == "exclude_district_centroid" for r in two_dp), 1)

ok = [r for r in rows if r["spatial_suitability_use"] == "point_label_ok"]
eq("inv.csv.point_labels", len(ok), 408)
eq("inv.csv.point_labels.in_window",
   sum(r["label_role"] == "EVENT_POINT_IN_WINDOW" for r in ok), 364)
eq("inv.csv.point_labels.undated",
   sum(r["label_role"] == "SITE_EVIDENCE_UNDATED" for r in ok), 38)
eq("inv.csv.point_labels.pre2000",
   sum(r["label_role"] == "HISTORICAL_PRE_2000" for r in ok), 6)

bnd_rows = [r for r in rows if r["spatial_suitability_use"] == "review_boundary_uncertain"]
eq("inv.csv.boundary_uncertain.n", len(bnd_rows), 10)
num("inv.csv.boundary_uncertain.min_m",
    min(float(r["dist_outside_boundary_m"]) for r in bnd_rows), 212.3, 0.05)
num("inv.csv.boundary_uncertain.max_m",
    max(float(r["dist_outside_boundary_m"]) for r in bnd_rows), 2836.1, 0.05)
eq("inv.csv.boundary_uncertain.outside_envelope",
   sum(1 for r in bnd_rows if float(r["dist_outside_boundary_m"]) > 1580), 1)

# These three records are easy to conflate and their statuses must never be merged:
#   A. the one record whose printed precision was corrected,
#   B. the one record excluded because its printed longitude is ~77 km east (Tamil Nadu),
#   C. the one boundary-review record beyond the GADM/OSM disagreement envelope.
by_id = {r["source_record_id"]: r for r in rows}
A = "KER/WYD/58A03/2024/01"
B = "14115/p141/row17 (printed Sl.17)"
C = "14115/p140/row15 (printed Sl.15)"
for rid in (A, B, C):
    true(f"inv.record_present.{rid}", rid in by_id, rid)
true("inv.records_are_distinct", len({A, B, C}) == 3)

eq("inv.A.use_is_point_label", by_id[A]["spatial_suitability_use"], "point_label_ok")
num("inv.A.stored_precision", float(by_id[A]["coord_precision_deg_stored"]), 2.778e-06, 1e-12)
num("inv.A.verified_precision", float(by_id[A]["coord_precision_deg_verified"]), 0.000278, 5e-7)
num("inv.A.uncertainty_m", float(by_id[A]["positional_uncertainty_m"]), 15.5, 0.05)
true("inv.A.has_floor_z", by_id[A]["spatial_suitability_use"] != "exclude_until_corrected")

eq("inv.B.use_is_exclude_until_corrected", by_id[B]["spatial_suitability_use"],
   "exclude_until_corrected")
eq("inv.B.is_the_only_exclusion",
   sum(r["spatial_suitability_use"] == "exclude_until_corrected" for r in rows), 1)
true("inv.B.reason_mentions_tamil_nadu", "Tamil Nadu" in by_id[B]["reason"])
true("inv.B.is_not_a_boundary_review",
     by_id[B]["spatial_suitability_use"] != "review_boundary_uncertain")

eq("inv.C.use_is_boundary_review", by_id[C]["spatial_suitability_use"],
   "review_boundary_uncertain")
num("inv.C.dist_outside_m", float(by_id[C]["dist_outside_boundary_m"]), 2836.1, 0.05)
true("inv.C.exceeds_osm_envelope", float(by_id[C]["dist_outside_boundary_m"]) > 1578.6)
true("inv.C.is_not_the_corrected_record", C != A)

grp = list(csv.DictReader(open(P / "inventory/event_group_point_status.csv", encoding="utf-8")))
eq("inv.groups.csv.rows", len(grp), 371)
eq("inv.groups.csv.with_label",
   sum(r["has_usable_point_label"] == "True" for r in grp), 363)

# ------------------------------------------------------------------- QA ------
qa = load("qa/readiness_metrics.json")
align = load("qa/grid_alignment_report.json")
eq("qa.n_label_points", qa["point_label_records_tested"], 408)
eq("qa.n_in_window_points", qa["in_window_point_records"], 364)
eq("qa.n_groups", qa["distinct_event_groups"], 363)
nn = qa["nearest_neighbour_distance_m"]
eq("qa.nn.median", nn["median"], 335.0)
num("qa.nn.p10", nn["p10"], 77.9, 0.05)
num("qa.nn.min", nn["min"], 1.0, 0.005)
eq("qa.nn.within_250", nn["n_within_250m"], 141)
eq("qa.nn.within_1000", nn["n_within_1000m"], 318)
eq("qa.clusters", qa["single_linkage_clusters"],
   {"250_m": 278, "500_m": 186, "1000_m": 76, "2000_m": 26, "5000_m": 2})
eq("qa.records_per_year", qa["records_per_year"],
   {"2006": 2, "2007": 15, "2008": 1, "2009": 7, "2018": 335,
    "2019": 1, "2024": 3})
eq("qa.date_precision", qa["date_precision"],
   {"year": 328, "day": 26, "month": 8, "multi-event": 2})
num("qa.share_2018", qa["share_2018_pct"], 92.0, 0.05)
eq("qa.layers_checked", len(qa["coverage_by_layer"]), 24)
for layer, cov in qa["coverage_by_layer"].items():
    eq(f"qa.coverage.{layer}.valid", cov["valid"], 408)
    num(f"qa.coverage.{layer}.pct", cov["coverage_pct"], 100.0, 0.005)
eq("qa.all_on_grid", align["all_on_grid"], True)
eq("qa.alignment_problems", align["problems"], [])
eq("qa.n_layers_on_grid", align["n_layers"], 25)

layers = list(csv.DictReader(open(P / "qa/layer_inventory.csv", encoding="utf-8")))
eq("qa.layer_inventory.rows", len(layers), 25)
true("qa.layer_inventory.all_same_grid", all(r["same_grid"] == "True" for r in layers))
eq("qa.layer_inventory.mask_valid", int(float(layers[0]["valid_in_district"])), 2356538)
num("qa.layer_inventory.dem_min", float(layers[1]["min"]), 116.96, 0.005)
num("qa.layer_inventory.dem_max", float(layers[1]["max"]), 2230.27, 0.005)

# ------------------------------------------------------------- manifest ------
manifest = list(csv.DictReader(open(DOCS / "data_manifest.csv", encoding="utf-8")))
eq("manifest.rows", len(manifest), 37)
eq("manifest.cols", len(manifest[0]), 16)
ids = [r["dataset_id"] for r in manifest]
eq("manifest.unique_ids", len(ids), len(set(ids)))
for i in range(1, 10):
    true(f"manifest.has_p3_{i:02d}", f"P3-{i:02d}" in ids)
p3_rows = [r for r in manifest if r["dataset_id"].startswith("P3-")]
eq("manifest.p3_rows", len(p3_rows), 9)
for r in p3_rows:
    lp = r["local_path"]
    true(f"manifest.{r['dataset_id']}.path_exists", (ROOT / lp).exists(), lp)
    true(f"manifest.{r['dataset_id']}.has_status", r["validation_status"] == "VERIFIED")
    true(f"manifest.{r['dataset_id']}.has_limitations", len(r["limitations"]) > 40)

# ------------------------------------------------------- documentation ------
DOCS_TEXT = {name: (DOCS / name).read_text(encoding="utf-8")
             for name in ("PREPROCESSING_REPORT.md", "DATA_READINESS_REPORT.md",
                          "data_quality_report.md", "PHASE3_PROGRESS.md")}
README = (ROOT / "README.md").read_text(encoding="utf-8")


def quoted(doc: str, needle: str) -> None:
    true(f"doc.{doc}.contains.{needle!r}", needle in DOCS_TEXT[doc])


# Per-document lists: a number must appear in the document that actually quotes it.
DOC_QUOTES = {
    "PREPROCESSING_REPORT.md": [
        f"{grid['n_district_pixels']:,}",
        f"{grid['district_mask_area_km2']:,.1f} km²",
        f"{grid['width']} × {grid['height']}",
        f"{cross['mad_m']:.2f}",
        f"{cross['n_nodes_in_district']:,}",
        f"{cross['max_absdiff_m']:.2f}",
        f"{cross['n_gt_50m']}",
        f"{dem['reprojection']['elev_range_district_m'][1]:,.2f}",
        f"{dem['reprojection']['elev_range_district_m'][0]:.2f}",
        f"{der['slope']['mean']:.2f}°",
        f"{der['slope']['max']:.2f}°",
        f"{bnd['gadm_vertices_to_osm']['median_m']:.1f}",
        f"{bnd['osm_vertices_to_gadm']['median_m']:.1f}",
        f"{bnd['asymmetric_diff_pct_of_gadm']:.2f}",
        f"{soil['checks']['grid_nodata_inside_district_pct']:.3f}",
        f"{chk['zero_cells_per_file']:,}",
        f"{ds['annual_mean_mm']:,.1f}",
        f"{ds['jjas_mean_mm']:,.1f}",
        f"{geo['raster']['share_by_class_pct']['1']:.2f}",
        f"{geo['scale_check']['median_distance_to_class_boundary_m']:,.0f}",
        f"{nw['pixel_area_m2_at_centre_lat']:.2f}",
        f"{nw['naive_100m2_area_km2']:,.1f}",
        f"{qa['point_label_records_tested']}",
        f"{cw['distinct_14115_targets']}",
        f"{rd['clip']['metric_length_km']:,.1f}",
        f"{rv['clip']['metric_length_km']:,.1f}",
        "2.778",
        "factor of 100",
    ],
    "DATA_READINESS_REPORT.md": [
        f"{grid['n_district_pixels']:,}",
        f"{grid['district_mask_area_km2']:,.1f} km²",
        f"{cross['mad_m']:.2f}",
        f"{soil['checks']['grid_nodata_inside_district_pct']:.3f}",
        f"{chk['zero_cells_per_file']:,}",
        f"{ds['annual_mean_mm']:,.1f}",
        f"{geo['raster']['share_by_class_pct']['1']:.2f}",
        f"{qa['point_label_records_tested']}",
        f"{qa['share_2018_pct']:.1f}",
        f"{qa['single_linkage_clusters']['1000_m']}",
        f"{cw['distinct_14115_targets']}",
        f"{rd['clip']['metric_length_km']:,.1f}",
        f"{rv['clip']['metric_length_km']:,.1f}",
        f"{bnd['asymmetric_diff_pct_of_gadm']:.2f}",
        "2.778",
    ],
    "data_quality_report.md": [
        f"{grid['n_district_pixels']:,}",
        f"{grid['district_mask_area_km2']:,.1f} km²",
        f"{cross['mad_m']:.2f}",
        f"{cross['n_nodes_in_district']:,}",
        f"{cross['max_absdiff_m']:.2f}",
        f"{cross['n_gt_50m']}",
        f"{dem['reprojection']['elev_range_district_m'][1]:,.2f}",
        f"{dem['reprojection']['elev_range_district_m'][0]:.2f}",
        f"{bnd['gadm_vertices_to_osm']['median_m']:.1f}",
        f"{bnd['osm_vertices_to_gadm']['median_m']:.1f}",
        f"{bnd['asymmetric_diff_pct_of_gadm']:.2f}",
        f"{chk['zero_cells_per_file']:,}",
        f"{soil['checks']['grid_nodata_inside_district_pct']:.3f}",
        f"{nw['pixel_area_m2_at_centre_lat']:.2f}",
        f"{nw['naive_100m2_area_km2']:,.1f}",
        f"{geo['raster']['share_by_class_pct']['1']:.2f}",
        f"{geo['scale_check']['median_distance_to_class_boundary_m']:,.0f}",
        f"{td['n']}",
        f"{pc[0]['corrected_to_deg']:.6f}",
        "2,836.1",
        "2.778",
    ],
}
for doc, needles in DOC_QUOTES.items():
    for needle in needles:
        quoted(doc, needle)

true("readme.contains_processed_labels", f"{len(ok)}" in README)
true("readme.contains_grid_height", f"{grid['height']}" in README)
true("readme.contains_no_model_claim", "No accuracy figure exists" in README)

# --------------------------------------------------------------- report ------
print(f"{n_checks} checks run")
if failures:
    print(f"\nFAILED {len(failures)}:")
    for f in failures:
        print("  -", f)
    sys.exit(1)
print("ALL PASSED — documentation matches the Phase 3 outputs")
