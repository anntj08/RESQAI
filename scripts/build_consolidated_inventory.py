"""Build the phase-2 consolidated Wayanad landslide inventory.

Design
------
Every original source record is retained as its own row. Nothing is merged
here; merging is expressed only through an explicit `event_group_id` assigned on
documented evidence. The output supports traceability from event group back to
individual source records.

Columns that must never be conflated:
  lat_dd_original / lon_dd_original      exactly as the source published it
  coord_precision_deg                    the resolution the source actually prints
  lat_dd_verified / lon_dd_verified      set only where an independent source
                                         supports a location; otherwise blank
  verified_coord_basis                   why, with the corroborating source

Run: python scripts/build_consolidated_inventory.py
"""
import csv
import pathlib
import re

import geopandas as gpd
import pandas as pd

MAIN = pathlib.Path(r"C:\Major")
EX = MAIN / "data" / "interim" / "inventory_extracts"
OUTD = MAIN / "data" / "processed" / "inventory"
OUTD.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- boundary ----
gadm = gpd.read_file(MAIN / "data" / "raw" / "boundary" / "gadm41_IND_2" / "gadm41_IND_2.json")
wy = gadm[(gadm["NAME_1"].astype(str).str.strip().str.lower() == "kerala")
          & (gadm["NAME_2"].astype(str).str.strip().str.lower() == "wayanad")]
if wy.empty:
    raise SystemExit("Wayanad boundary not found in GADM file")
wy = wy.to_crs(4326)
wypoly = wy.geometry.union_all() if hasattr(wy.geometry, "union_all") else wy.geometry.unary_union
area_km2 = wy.to_crs(32643).geometry.area.sum() / 1e6
print(f"Wayanad polygon area = {area_km2:,.1f} km2 (sanity: published ~2,121 km2)")

rows = []


def add(**kw):
    rows.append(kw)


# ------------------------------------------------------------ 1. GSI 14115 ----
d = pd.read_csv(EX / "inventory_gsi14115_wayanad.csv")
for _, r in d.iterrows():
    add(
        source_id="GSI14115",
        source_record_id=f"14115/p{r.pdf_page}/row{r.src_row}" +
                         (f" (printed Sl.{r.src_sl_no_printed})" if pd.notna(r.src_sl_no_printed) else ""),
        source_title="GSI 14115 Landslide Inventory of Kerala (FS 2007-2010), Wayanad table pp.135-148",
        source_file="data/raw/landslide_inventory/gsi_bhusanket/pdf/gsi_14115.pdf",
        source_ref=f"p.{r.pdf_page}",
        locality=r.locality, village=r.village, taluk=r.taluk,
        lat_dd_original=r.latitude_dd, lon_dd_original=r.longitude_dd,
        coord_precision_deg=r.coord_precision_deg,
        coord_format="DMS arc-second (as printed)",
        date_text=r.date_text_verbatim,
        event_date_iso=r.event_date_iso,
        date_certainty=r.date_certainty,
        landslide_type=re.split(
            r"\s+(?:on|during|in|at)\s+", str(r.date_text_verbatim), maxsplit=1)[0].strip(),
        geology=r.geology,
        area_text=r.area_destroyed_text,
        casualties=r.casualties_text,
        notes=r.data_quality_flag,
        publisher="Geological Survey of India",
        independence="primary (GSI field investigation)",
    )

# ------------------------------------------------- 2. GSI 2024 / 2025 sheets ---
d = pd.read_csv(EX / "inventory_gsi_pdls_wayanad.csv")
for _, r in d.iterrows():
    add(
        source_id="GSI_PDLS",
        source_record_id=r.slide_no,
        source_title=r.source_report,
        source_file=f"data/raw/landslide_inventory/gsi_bhusanket/pdf/{r.source_pdf}",
        source_ref=f"Annexure 42-point datasheet, p.{r.pdf_page}",
        locality=r.name_of_slide, village="", taluk="",
        lat_dd_original=r.latitude_dd, lon_dd_original=r.longitude_dd,
        coord_precision_deg=r.coord_precision_deg,
        coord_format="DMS arc-second (as printed; degree glyph degraded in PDF text)",
        date_text=(r.history if isinstance(r.history, str) else ""),
        event_date_iso=("2024-07-30" if str(r.slide_no).startswith("KER/WYD/58A03/2024")
                        else ("2024-06" if str(r.slide_no).startswith("KER/WYD/58A03/2025")
                              else "")),
        date_certainty="day" if str(r.slide_no).startswith("KER/WYD/58A03/2024") else "month",
        landslide_type=f"{r.material} {r.movement}".strip(),
        geology=str(r.lithology)[:120],
        area_text=str(r.area), casualties=str(r.deaths),
        notes=("2025 report; declared history 'June 2024' - the event is dated 2024, "
               "reported 21.05.2025" if "2025" in str(r.slide_no) else ""),
        publisher="Geological Survey of India",
        independence="primary (GSI field investigation)",
    )

# --------------------------------------------------- 3. GSI 14337 (2-dp) ------
d = pd.read_csv(EX / "inventory_14337_wayanad.csv")
for _, r in d.iterrows():
    add(
        source_id="GSI14337",
        source_record_id=f"14337/Sl.{r.src_sl_no}",
        source_title="GSI 14337 Landslide hazard zonation, Kasaragod/Kannur/Wayanad",
        source_file="data/raw/landslide_inventory/gsi_bhusanket/pdf/gsi_14337.pdf",
        source_ref=f"p.{r.pdf_page}",
        locality=r.location, village="", taluk="",
        lat_dd_original=r.latitude_dd, lon_dd_original=r.longitude_dd,
        coord_precision_deg=r.coord_precision_deg,
        coord_format="decimal degrees, 2 dp (~1.1 km)",
        date_text=str(r.date_of_event) if pd.notna(r.date_of_event) else "",
        event_date_iso="", date_certainty="undated",
        landslide_type=r.landslide_type, geology="", area_text="", casualties="",
        notes="", publisher="Geological Survey of India",
        independence="primary (same GSI lineage as 14115)",
    )

# ------------------------------------- 4. GSI 14768 tables 4 and 5 ------------
for fn, tbl in (("inventory_14768_table4.csv", "Table 4"),
                ("inventory_14768_table5.csv", "Table 5")):
    d = pd.read_csv(EX / fn)
    for _, r in d.iterrows():
        add(
            source_id="GSI14768",
            source_record_id=f"14768/{tbl}/Sl.{r.src_sl_no}",
            source_title="GSI 14768 1:50,000 susceptibility mapping, Mananthavady-Kalpetta-Sulthan Bathery",
            source_file="data/raw/landslide_inventory/gsi_bhusanket/pdf/gsi_14768.pdf",
            source_ref=tbl,
            locality=r.location, village="", taluk="",
            lat_dd_original=r.latitude_dd, lon_dd_original=r.longitude_dd,
            coord_precision_deg=r.coord_precision_deg,
            coord_format="decimal degrees (as published)",
            date_text=str(r.date_of_event) if "date_of_event" in r and pd.notna(r.date_of_event) else "",
            event_date_iso="", date_certainty="undated",
            landslide_type=r.landslide_type, geology="", area_text="", casualties="",
            notes="", publisher="Geological Survey of India",
            independence="primary (same GSI lineage as 14115)",
        )

# ------------------------------------------ 5. GSI 2018 post-disaster note ----
d = pd.read_csv(EX / "inventory_2018_postdisaster.csv")
for _, r in d.iterrows():
    m = re.search(r"(\d{4})", str(r.event_history))
    add(
        source_id="GSI2018",
        source_record_id=r.slide_no,
        source_title="GSI Note on post-disaster studies, landslides of June 2018, Wayanad",
        source_file="data/raw/landslide_inventory/gsi_bhusanket/pdf/gsi_2018_post_disaster_wayanad.pdf",
        source_ref="42-point datasheets",
        locality=r.landslide_name, village="", taluk="",
        lat_dd_original=r.latitude_dd, lon_dd_original=r.longitude_dd,
        coord_precision_deg=r.coord_precision_deg,
        coord_format="decimal degrees (as published)",
        date_text=str(r.event_history),
        event_date_iso=("2018-06-14" if "14th June 2018" in str(r.event_history) else
                        ("2018-06" if m else "")),
        date_certainty="day" if "14th June 2018" in str(r.event_history) else "month",
        landslide_type=f"{r.material} {r.movement_type}".strip(),
        geology=r.geology, area_text=str(r.area), casualties="",
        notes="", publisher="Geological Survey of India",
        independence="primary (GSI field investigation)",
    )

# --------------------------------------- 6. Kerala 2018 monsoon inventory -----
d = pd.read_csv(EX / "inventory_kerala2018_wayanad.csv")
for _, r in d.iterrows():
    add(
        source_id="KER2018",
        source_record_id=f"KER2018/No.{r.No}",
        source_title="Hao et al. 2020 ESSD landslide inventory of the 2018 Kerala monsoon",
        source_file="data/raw/landslide_inventory/kerala_2018_dans/Kerela landslide.shp",
        source_ref=f"feature No={r.No}",
        locality=r.Specific_r if isinstance(r.Specific_r, str) else "",
        village="", taluk="",
        lat_dd_original=r.latitude_dd, lon_dd_original=r.longitude_dd,
        coord_precision_deg=r.coord_precision_deg,
        coord_format="decimal degrees, 5 dp (GIS file)",
        date_text="2018 monsoon season (per-event dates not recorded)",
        event_date_iso="2018", date_certainty="year",
        landslide_type=r.Type_of_sl, geology="", area_text=f"{r.Area} m2", casualties="",
        notes=("derived from NRSC" if r.NRSC == "Y" else "") and "",
        publisher="Hao, van Westen et al. (DANS doi:10.17026/dans-x6c-y7x2)",
        independence="composite: built from NRSC + GSI sources, not fully independent",
    )

# ------------------------------------------------------- 7. NASA GLC ----------
d = pd.read_csv(EX / "nasa_glc_wayanad_bbox.csv")
for _, r in d.iterrows():
    add(
        source_id="NASA_GLC",
        source_record_id=f"GLC/{r.event_id}",
        source_title="NASA Global Landslide Catalog (GLC) query, Wayanad bounding box",
        source_file="data/interim/inventory_extracts/nasa_glc_wayanad_bbox.csv",
        source_ref=f"event_id {r.event_id}",
        locality=str(r.location_description), village="", taluk="",
        lat_dd_original=r.latitude, lon_dd_original=r.longitude,
        coord_precision_deg=0.01,
        coord_format="decimal degrees; GLC location_accuracy field present",
        date_text=str(pd.to_datetime(r.event_date).date()) if pd.notna(r.event_date) else "",
        event_date_iso=str(pd.to_datetime(r.event_date).date()) if pd.notna(r.event_date) else "",
        date_certainty="day",
        landslide_type=f"{r.landslide_category}/{r.landslide_trigger}",
        geology="", area_text=str(r.landslide_size),
        casualties=f"{r.fatality_count}" if pd.notna(r.fatality_count) else "",
        notes=f"GLC accuracy={r.location_accuracy}; gazetteer dist={r.gazeteer_distance}",
        publisher="NASA Goddard (Kirschbaum)",
        independence="secondary compilation from media/reports",
    )

# --------------------------------- 8. Peer-reviewed event table (2025) --------
LIT = [
    dict(locality="Mundakkai / Chooralmala / Vellarimala (Meppadi GP)",
         date="30 July 2024", iso="2024-07-30", lat=11 + 28 / 60 + 1 / 3600,
         lon=76 + 8 / 60 + 9 / 3600, dms="11deg28'01\"N 76deg08'09\"E",
         imp="~336 dead, 78 missing (as at publication)"),
    dict(locality="Puthumala, Kalladi, Vythiri",
         date="08 August 2019", iso="2019-08-08", lat=11 + 29 / 60 + 51 / 3600,
         lon=76 + 7 / 60 + 47 / 3600, dms="11deg29'51\"N 76deg07'47\"E",
         imp="11 killed, 6 missing"),
]
for e in LIT:
    add(
        source_id="LIT2025",
        source_record_id="Sreekumar2025/Table1/" + e["iso"],
        source_title="Sreekumar et al. 2025, Sci Rep, Table 1 (doi:10.1038/s41598-025-33065-9)",
        source_file="data/raw/literature_events/PMC12749052.xml",
        source_ref="Table 1",
        locality=e["locality"], village="", taluk="",
        lat_dd_original=round(e["lat"], 6), lon_dd_original=round(e["lon"], 6),
        coord_precision_deg=1 / 3600,
        coord_format=f"DMS whole-second ({e['dms']})",
        date_text=e["date"], event_date_iso=e["iso"], date_certainty="day",
        landslide_type="", geology="", area_text="", casualties=e["imp"],
        notes="literature compilation; coordinates not from a field survey by these authors",
        publisher="Scientific Reports (peer-reviewed)",
        independence="independent publication (but event facts may trace to media/GSI)",
    )

df = pd.DataFrame(rows)
print(f"\nconsolidated source records: {len(df)}")
print(df.source_id.value_counts().to_string())

# ------------------------------------------------------------- geometry ------
pts = gpd.GeoDataFrame(
    df.copy(),
    geometry=gpd.points_from_xy(df.lon_dd_original, df.lat_dd_original),
    crs=4326,
)
pts["inside_wayanad"] = pts.geometry.within(wypoly)
print(f"\npoints inside GADM Wayanad: {int(pts.inside_wayanad.sum())} / {len(pts)}")
print("outside:")
print(pts.loc[~pts.inside_wayanad, ["source_id", "source_record_id", "locality",
                                    "lat_dd_original", "lon_dd_original"]].to_string(max_colwidth=40))

# ----------------------------------------------- precision improvement -------
# Measured in EPSG:32643, not by scaling degrees, so this agrees with the
# authoritative crosswalk produced by assemble_inventory.py.
print("\n--- 2-decimal GSI 14337 records vs GSI 14115 arc-second records ---")
a = pts[pts.source_id == "GSI14337"].to_crs(32643)
b = pts[pts.source_id == "GSI14115"].to_crs(32643)
cov = []
for i, r in a.iterrows():
    d2 = b.geometry.distance(r.geometry)  # metres, metric CRS
    j = d2.idxmin()
    cov.append({
        "s14337_id": r.source_record_id, "s14337_loc": r.locality,
        "s14337_coord": f"{r.lat_dd_original},{r.lon_dd_original}",
        "s14115_id": b.loc[j, "source_record_id"],
        "s14115_loc": b.loc[j, "locality"],
        "s14115_coord": f"{b.loc[j,'lat_dd_original']},{b.loc[j,'lon_dd_original']}",
        "dist_m": round(float(d2.loc[j]), 1),
    })
cv = pd.DataFrame(cov).sort_values("dist_m")
print(cv.head(18).to_string(max_colwidth=30))
print(f"\n14337 rows within 1500 m of a 14115 record: {(cv.dist_m <= 1500).sum()} / {len(cv)}"
      f"   median {cv.dist_m.median():.0f} m")

pts.drop(columns="geometry").to_csv(OUTD / "inventory_all_source_records.csv",
                                    index=False, quoting=csv.QUOTE_MINIMAL)
print("\nwrote", OUTD / "inventory_all_source_records.csv")
