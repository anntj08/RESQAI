"""Build docs/data_manifest.csv from a validated dataset-level registry."""
import csv
import pathlib

COLS = ["dataset_id", "category", "dataset_name", "provider", "product_version", "source_url",
        "acquisition_date", "time_period", "spatial_extent", "native_resolution", "crs", "format",
        "local_path", "size_mb", "validation_status", "limitations"]

R = []

def add(**kw):
    R.append({c: kw.get(c, "") for c in COLS})


def size_mb(*paths):
    """Sum bytes on disk for one path or several. Fails loudly if a path is absent,
    so a manifest row cannot outlive the product it describes."""
    total = 0
    for p in paths:
        p = pathlib.Path(p)
        assert p.exists(), f"manifest entry points at a missing path: {p}"
        if p.is_file():
            total += p.stat().st_size
        else:
            total += sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
    return f"{total / 1_000_000:.2f}"

add(dataset_id="DEM-01", category="dem", dataset_name="Copernicus DEM GLO-30 (DSM)",
    provider="Copernicus / ESA / Airbus (AWS Open Data)", product_version="GLO-30, Copernicus_DSM_COG_10",
    source_url="https://copernicus-dem-30m.s3.amazonaws.com/", acquisition_date="2026-10-25",
    time_period="2021 epoch", spatial_extent="2 tiles (75-77E, 11-12N) = 100% of Wayanad",
    native_resolution="30 m (1 arc-second)", crs="EPSG:4326", format="GeoTIFF (COG, float32)",
    local_path="data/raw/dem/copernicus_glo30/", size_mb="64.2", validation_status="VERIFIED",
    limitations="Digital Surface Model including canopy/buildings, not bare earth; not the NASA SRTMGL1 product; EGM2008 vertical datum")

add(dataset_id="DEM-02", category="dem", dataset_name="NASA SRTMGL1 V003 (1 arc-second)",
    provider="NASA LP DAAC / Earthdata", product_version="003",
    source_url="https://doi.org/10.5067/MEASURES/SRTM/SRTMGL1.003", acquisition_date="2026-10-25",
    time_period="February 2000 (single mission epoch)",
    spatial_extent="granules N11E075 + N11E076 required for full district coverage",
    native_resolution="30 m (1 arc-second)", crs="EPSG:4326", format="HGT (int16)",
    local_path="(not downloaded)", size_mb="0", validation_status="ACCESS_RESTRICTED",
    limitations="Data download requires authenticated Earthdata Login; no credentials exist on this machine. CMR granule search works unauthenticated, download does not")

add(dataset_id="DEM-03", category="dem", dataset_name="SRTM 1 arc-second mirror (Skadi / elevation-tiles-prod)",
    provider="Mapzen/Amazon Public Datasets mirror (source: NASA SRTM)", product_version="Skadi",
    source_url="https://s3.amazonaws.com/elevation-tiles-prod/skadi/", acquisition_date="2026-10-25",
    time_period="February 2000", spatial_extent="2 tiles (75-77E, 11-12N) = 100% of Wayanad",
    native_resolution="30 m (1 arc-second)", crs="EPSG:4326", format="HGT (int16) + .gz",
    local_path="data/raw/dem/srtm_1arcsec_skadi/", size_mb="51.9", validation_status="VERIFIED",
    limitations="Third-party mirror, not an official NASA channel and no NASA checksum. Zero voids (-32768 count = 0). Exhaustive agreement with Copernicus GLO-30 at all 2,280,319 shared district nodes: r=0.9997, MAD 3.42 m, max 147.03 m, 447 nodes >50 m. Both files are tagged AREA_OR_POINT=Point; a sub-pixel shift test finds no relative offset")

add(dataset_id="LC-01", category="landcover", dataset_name="ESA WorldCover 2021 v200",
    provider="ESA / VITO (AWS Open Data)", product_version="v200 (2021)",
    source_url="https://esa-worldcover.org/en/data-access", acquisition_date="2026-10-25",
    time_period="2021", spatial_extent="3x3 degree tile N09E075 (N09-N12, E075-E078) = 100% of Wayanad",
    native_resolution="10 m", crs="EPSG:4326", format="GeoTIFF (uint8, 11 classes)",
    local_path="data/raw/landcover/ESA_WorldCover_10m_2021_v200_N09E075_Map.tif", size_mb="75.6",
    validation_status="VERIFIED",
    limitations="Only 11 classes; shade coffee/rubber/tea plantations are largely mapped as Tree cover (class 10 = 89.6% of district), so forest vs plantation separation is weak")

add(dataset_id="RF-01", category="rainfall", dataset_name="CHIRPS v2.0 monthly precipitation",
    provider="UCSB Climate Hazards Center", product_version="v2.0",
    source_url="https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_monthly/tifs/",
    acquisition_date="2026-10-25", time_period="2000-01 to 2025-12 (312 months)",
    spatial_extent="global 50S-50N grids; Wayanad window 75.60-76.55E 11.25-12.00N",
    native_resolution="0.05 deg (~5.5 km)", crs="EPSG:4326", format="GeoTIFF.gz (float32)",
    local_path="data/raw/rainfall/chirps_v2_monthly/", size_mb="4545.6", validation_status="VERIFIED",
    limitations="Monthly only, no event-scale daily rainfall at this stage; ~5.5 km pixel is coarse for a 2121 km2 district; gauge-satellite blend, not a dense local gauge network")

add(dataset_id="GEO-01", category="geology", dataset_name="Global Lithological Map (GLiM) / LiMW 2015",
    provider="Hartmann & Moosdorf, University of Hamburg", product_version="v1.0 database, 2015 GIS export",
    source_url="https://doi.org/10.1594/PANGAEA.788537", acquisition_date="2026-10-25",
    time_period="static compilation (source maps to 2015)", spatial_extent="global; 16 polygons intersect Wayanad",
    native_resolution="1:3.75 million average source scale", crs="ESRI:54012 (World Eckert IV) native",
    format="ESRI File Geodatabase (zipped, 1.23M polygons)",
    local_path="data/raw/geology/glim/", size_mb="1138.7", validation_status="VERIFIED",
    limitations="Very coarse for district-level work (effective detail ~4 km); NOT GSI 1:50,000 geology; only 5 lithology classes intersect Wayanad; no structural or weathering detail")

add(dataset_id="GEO-02", category="geology", dataset_name="GSI Bhukosh geology / geoscience layers",
    provider="Geological Survey of India", product_version="Bhukosh portal",
    source_url="https://bhukosh.gsi.gov.in/", acquisition_date="2026-10-25",
    time_period="n/a", spatial_extent="Wayanad", native_resolution="n/a", crs="unknown",
    format="unknown", local_path="(not downloaded)", size_mb="0", validation_status="ACCESS_RESTRICTED",
    limitations="bhukosh.gsi.gov.in refused TCP connections over HTTP and HTTPS on repeated attempts; GSI Bhusanket ArcGIS REST services return 499 Token Required")

add(dataset_id="INV-01", category="landslide_inventory",
    dataset_name="GSI 14337 Landslide Hazard Zonation, Kasaragod/Kannur/Wayanad (2012-13)",
    provider="Geological Survey of India", product_version="Acc. No. 14337",
    source_url="https://bhusanket.gsi.gov.in/Output/LandslideReport/Kerala/Macro%20scale%20studies/14337.pdf",
    acquisition_date="2026-10-25", time_period="events pre-2012 (mostly 2006-2010)",
    spatial_extent="3 districts; 35 Wayanad records extracted", native_resolution="point data",
    crs="unstated (geographic degrees)", format="PDF + extracted CSV",
    local_path="data/raw/landslide_inventory/gsi_bhusanket/pdf/gsi_14337.pdf", size_mb="1.6",
    validation_status="DOWNLOADED_NOT_FULLY_VALIDATED",
    limitations="Coordinates rounded to 2 decimal places (~1.1 km uncertainty); event dates generally absent; morphometry missing for several records; not field-verified by this project")

add(dataset_id="INV-02", category="landslide_inventory",
    dataset_name="GSI 14768 Macro-scale 1:50,000 susceptibility, Mananthavady-Kalpetta-Sulthan Bathery-Vazhikkadavu (2015-16)",
    provider="Geological Survey of India", product_version="Acc. No. 14768",
    source_url="https://bhusanket.gsi.gov.in/Output/LandslideReport/Kerala/Macro%20scale%20studies/14768.pdf",
    acquisition_date="2026-10-25", time_period="archival events, undated",
    spatial_extent="study area ~1930 km2; 29 archival + 17 field records extracted",
    native_resolution="point data", crs="unstated (geographic degrees)", format="PDF + extracted CSV",
    local_path="data/raw/landslide_inventory/gsi_bhusanket/pdf/gsi_14768.pdf", size_mb="9.1",
    validation_status="DOWNLOADED_NOT_FULLY_VALIDATED",
    limitations="Archival table has no dates; 6/29 archival and 4/17 field points fall outside the GADM district polygon (study area crosses into Malappuram/Kozhikode); DMS precision varies 0.1-1 arc-second")

add(dataset_id="INV-03", category="landslide_inventory",
    dataset_name="GSI 2018 post-disaster report, June 2018 Wayanad landslides",
    provider="Geological Survey of India", product_version="FSP M4SI/NC/SR/SU-KRL/2018/21108",
    source_url="https://bhusanket.gsi.gov.in/Output/LandslideReport/Kerala/Post%20Disaster%20Studies/ADDL.%20ITEM%28LANDSLIDES%20OCCURRED%20IN%20JUNE%202018%20AT%20WAYANAD%20DISTRICT%2C%20KERALA%29.pdf",
    acquisition_date="2026-10-25", time_period="2018-06-14 to 2018-06-16",
    spatial_extent="8 slides, all inside Wayanad", native_resolution="point data",
    crs="unstated (geographic degrees)", format="PDF + extracted CSV",
    local_path="data/raw/landslide_inventory/gsi_bhusanket/pdf/gsi_2018_post_disaster_wayanad.pdf", size_mb="2.5",
    validation_status="DOWNLOADED_NOT_FULLY_VALIDATED",
    limitations="Only 8 events; coordinates to 4 decimals (~11 m) but ground accuracy not independently checked; no polygon footprints")

add(dataset_id="INV-04", category="landslide_inventory", dataset_name="NASA Global Landslide Catalog (GLC) export",
    provider="NASA Goddard Space Flight Center", product_version="export current to 2016-03-07",
    source_url="https://data.nasa.gov/docs/legacy/Global_Landslide_Catalog_Export/Global_Landslide_Catalog_Export_rows.csv",
    acquisition_date="2026-10-25", time_period="1997-2016 (catalog ends March 2016)",
    spatial_extent="global CSV; 50 Kerala rows, 9 in Wayanad bbox", native_resolution="event point",
    crs="unstated (geographic degrees)", format="CSV",
    local_path="data/raw/landslide_inventory/nasa_glc/Global_Landslide_Catalog_Export_rows.csv", size_mb="8.5",
    validation_status="VERIFIED",
    limitations="Media-derived, reported location accuracy 1-50 km; only 9 records in bbox and 1 explicitly named Wayanad; catalog ends 2016 so 2018/2019/2024 events are missing; unsuitable as primary inventory")

add(dataset_id="BND-01", category="boundary", dataset_name="Wayanad district boundary (GADM 4.1)",
    provider="GADM", product_version="4.1", 
    source_url="https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_IND_2.json.zip",
    acquisition_date="2026-10-25", time_period="2022 release",
    spatial_extent="1 MultiPolygon, 2121.0 km2, 75.772-76.436E / 11.443-11.971N",
    native_resolution="vector district", crs="EPSG:4326", format="GeoJSON (zipped)",
    local_path="data/raw/boundary/gadm41_IND_2/", size_mb="1.5", validation_status="VERIFIED",
    limitations="Research-grade global dataset, not an official Survey of India / Kerala boundary; area differs from OSM by 0.36% but the outlines differ by 744-771 m median (p90 ~1.1 km, max 1,579 m, 8.75% symmetric difference), so district membership within ~0.75 km of the edge is ambiguous")

add(dataset_id="BND-02", category="boundary", dataset_name="Wayanad district boundary (OSM/Nominatim)",
    provider="OpenStreetMap contributors", product_version="relation snapshot 2026-10-25",
    source_url="https://nominatim.openstreetmap.org/", acquisition_date="2026-10-25",
    time_period="2026 snapshot", spatial_extent="1 MultiPolygon, 2128.6 km2",
    native_resolution="vector district", crs="EPSG:4326", format="GeoJSON",
    local_path="data/raw/boundary/osm_nominatim_wayanad.geojson", size_mb="0.09", validation_status="VERIFIED",
    limitations="Crowd-sourced; used only as an independent cross-check of BND-01, not as the analysis boundary")

add(dataset_id="ADD-01", category="additional", dataset_name="HydroRIVERS v1.0 (Asia)",
    provider="WWF / HydroSHEDS", product_version="v1.0",
    source_url="https://data.hydrosheds.org/file/HydroRIVERS/HydroRIVERS_v10_as_shp.zip",
    acquisition_date="2026-10-25", time_period="static",
    spatial_extent="Asia; 1298 segments / 3195 km in Wayanad bbox", native_resolution="vector line",
    crs="EPSG:4326", format="Shapefile (zipped)",
    local_path="data/raw/additional/hydrorivers/", size_mb="90.5", validation_status="VERIFIED",
    limitations="Regional file acquired because no smaller official subset exists; modelled network, not surveyed; small streams absent")

add(dataset_id="ADD-02", category="additional", dataset_name="OSM road network (Wayanad)",
    provider="OpenStreetMap contributors", product_version="Overpass API snapshot 2026-10-25",
    source_url="https://overpass-api.de/api/interpreter", acquisition_date="2026-10-25",
    time_period="2026 snapshot", spatial_extent="13169 segments / 5968 km within district",
    native_resolution="vector line", crs="EPSG:4326", format="GeoJSON",
    local_path="data/raw/additional/osm_roads_wayanad.geojson", size_mb="6.1", validation_status="VERIFIED",
    limitations="Crowd-sourced and uneven in rural areas; a mapped road does not imply a cut slope")

add(dataset_id="BND-03", category="boundary", dataset_name="Kerala Spatial Data Infrastructure (KSDI) layers",
    provider="Kerala State IT Mission", product_version="unknown",
    source_url="https://ksdi.kerala.gov.in/", acquisition_date="2026-10-25", time_period="n/a",
    spatial_extent="Wayanad", native_resolution="unknown", crs="unknown", format="unknown",
    local_path="(not downloaded)", size_mb="0", validation_status="UNAVAILABLE",
    limitations="Host did not respond (connection timeout) from this network")

# ---------------------------------------------------------------------------
# Phase 2 additions
# ---------------------------------------------------------------------------

add(dataset_id="INV-05", category="landslide_inventory",
    dataset_name="GSI 14115 Landslide Inventory of Kerala (FS 2007-2010), Wayanad district table",
    provider="Geological Survey of India", product_version="Acc. No. 14115",
    source_url="https://bhusanket.gsi.gov.in/Output/LandslideReport/Kerala/Post%20Disaster%20Studies/14115.pdf",
    acquisition_date="2026-10-25", time_period="1961-2009 (27 of 35 records fall in 2006-2009)",
    spatial_extent="35 records, all Wayanad (2 flagged as outside the district boundary)",
    native_resolution="point data, arc-second coordinates", crs="unstated (geographic degrees)",
    format="PDF + extracted CSV", local_path="data/raw/landslide_inventory/gsi_bhusanket/pdf/gsi_14115.pdf",
    size_mb="4.9", validation_status="VERIFIED",
    limitations="Table holds 35 records under 34 printed serial numbers (Sl. 21 used twice); row 17 prints an impossible longitude (76d56'58\"E) and is retained as published; 2 rows undated; source columns interleave across page breaks so unstructured cells are kept verbatim rather than parsed")

add(dataset_id="INV-06", category="landslide_inventory",
    dataset_name="GSI Post-Disaster Studies of Landslides in Kerala, 2024 (PDLS 2024)",
    provider="Geological Survey of India", product_version="Acc. No. PDLS_2024_51817",
    source_url="https://bhusanket.gsi.gov.in/Output/LandslideReport/Kerala/Post%20Disaster%20Studies/PDLS_2024_51817.pdf",
    acquisition_date="2026-10-25", time_period="2024 monsoon (event dated 2024-07-30)",
    spatial_extent="15 slide records statewide, 1 in Wayanad (Mundakkai-Chooralmala)",
    native_resolution="point data, arc-second coordinates", crs="unstated (geographic degrees)",
    format="PDF + extracted CSV",
    local_path="data/raw/landslide_inventory/gsi_bhusanket/pdf/gsi_PDLS_2024_51817.pdf",
    size_mb="15.1", validation_status="VERIFIED",
    limitations="Single Wayanad record for a multi-lobe disaster; extent/area fields left blank ('--') by GSI; coordinate is the source area, 4.91 km from Chooralmala settlement and 1.98 km from Mundakkai village")

add(dataset_id="INV-07", category="landslide_inventory",
    dataset_name="GSI Post-Disaster Studies of Landslides in Kerala, 2025 (PDLS 2025)",
    provider="Geological Survey of India", product_version="Acc. No. PDLS_2025_61074",
    source_url="https://bhusanket.gsi.gov.in/Output/LandslideReport/Kerala/Post%20Disaster%20Studies/PDLS_2025_61074.pdf",
    acquisition_date="2026-10-25", time_period="reported 2025-05-21; declared event history 'June 2024'",
    spatial_extent="16 slide records statewide, 1 in Wayanad (Meenakshi Bridge)",
    native_resolution="point data, arc-second coordinates", crs="unstated (geographic degrees)",
    format="PDF + extracted CSV",
    local_path="data/raw/landslide_inventory/gsi_bhusanket/pdf/gsi_PDLS_2025_61074.pdf",
    size_mb="22.5", validation_status="VERIFIED",
    limitations="The only Wayanad record is a small (90 m2) road-cut rotational slide dated June 2024, not a 2025 event; its printed longitude uses a minute glyph instead of a degree glyph")

add(dataset_id="INV-08", category="landslide_inventory",
    dataset_name="Landslide inventory of the 2018 monsoon rainfall in Kerala, India",
    provider="Hao, van Westen et al.; DANS Data Station Physical and Technical Sciences",
    product_version="v2.0 (doi:10.17026/dans-x6c-y7x2)",
    source_url="https://doi.org/10.17026/dans-x6c-y7x2", acquisition_date="2026-10-25",
    time_period="2018 monsoon (June-August 2018)",
    spatial_extent="4,728 points statewide; 331 in Wayanad",
    native_resolution="point data (mapped landslide centroids)", crs="EPSG:4326",
    format="ESRI Shapefile + MIF/MID", local_path="data/raw/landslide_inventory/kerala_2018_dans/",
    size_mb="15.2", validation_status="VERIFIED",
    limitations="CC-BY-4.0 and openly licensed, but composite: built from NRSC and GSI sources plus new mapping, so it is not independent of GSI; per-event dates are not recorded (only '2018 monsoon'); 'easy-migration.zip' failed to download from objectstore.surf.nl and is a Dataverse export artefact, not data")

add(dataset_id="INV-09", category="landslide_inventory",
    dataset_name="Meppadi Landslide Post-Disaster Needs Assessment (PDNA), 2024",
    provider="Kerala State Disaster Management Authority",
    product_version="final, 2025-10 upload",
    source_url="https://sdma.kerala.gov.in/wp-content/uploads/2025/10/Meppadi-Landslide-PDNA_final_new1-2_compressed-compressed.pdf",
    acquisition_date="2026-10-25", time_period="2024-07-30 event, recovery period to 2025",
    spatial_extent="Meppadi Grama Panchayath, Vythiri Taluk, Wayanad",
    native_resolution="text report (647 pp)", crs="n/a", format="PDF + extracted text",
    local_path="data/raw/landslide_inventory/ksdma/ksdma_meppadi_pdna_2024.pdf",
    size_mb="19.8", validation_status="DOWNLOADED_NOT_FULLY_VALIDATED",
    limitations="Impact and recovery assessment, not an event inventory; contains no dated multi-event list; narrative figures not independently re-derived from underlying tables")

add(dataset_id="INV-10", category="landslide_inventory",
    dataset_name="Kerala Memorandum on the July 2024 disaster (17082024)",
    provider="Revenue Department / KSDMA, Government of Kerala",
    product_version="Memorandum dated 2024-08-17",
    source_url="https://sdma.kerala.gov.in/wp-content/uploads/2025/07/Memorandum_17082024.pdf",
    acquisition_date="2026-10-25", time_period="2024-07-30 event",
    spatial_extent="Wayanad (Meppadi GP) with statewide context",
    native_resolution="text report (35 pp)", crs="n/a", format="PDF + extracted text",
    local_path="data/raw/landslide_inventory/ksdma/ksdma_memorandum_17082024.pdf",
    size_mb="4.1", validation_status="DOWNLOADED_NOT_FULLY_VALIDATED",
    limitations="Primary evidence for event timing (about 01:15 on 2024-07-30), rainfall at Kalladi (200.2 mm on 29-07, 372.6 mm on 30-07) and the crown's distance to Mundakkai (~3 km) and Chooralmala (~5 km); fatality totals are interim government figures")

add(dataset_id="INV-11", category="landslide_inventory",
    dataset_name="KSDMA event report, October 2021 floods and landslides",
    provider="Kerala State Emergency Operations Centre / KSDMA", product_version="2022-05 upload",
    source_url="http://sdma.kerala.gov.in/wp-content/uploads/2022/05/Event-report_October-2021.pdf",
    acquisition_date="2026-10-25", time_period="2021-10-13 to 2021-10-25",
    spatial_extent="statewide", native_resolution="text report (115 pp)", crs="n/a",
    format="PDF + extracted text", local_path="data/raw/landslide_inventory/ksdma/ksdma_event_report_october2021.pdf",
    size_mb="10.7", validation_status="DOWNLOADED_NOT_FULLY_VALIDATED",
    limitations="Verified to be a SEOC daily situation log (reservoir and alert decisions), NOT a landslide inventory: Wayanad appears only in rainfall-alert lists. Contributes no event record")

add(dataset_id="INV-12", category="landslide_inventory",
    dataset_name="Global Fatal Landslide Database (GFLD) supplementary tables",
    provider="Froude & Petley 2018, NHESS (Copernicus)",
    product_version="nhess-18-2161-2018-t01..t03",
    source_url="https://nhess.copernicus.org/articles/18/2161/2018/",
    acquisition_date="2026-10-25", time_period="2004-2016 (database scope)",
    spatial_extent="global", native_resolution="n/a", crs="n/a", format="XLSX",
    local_path="data/raw/landslide_inventory/gfld/", size_mb="0.02",
    validation_status="DOWNLOADED_NOT_FULLY_VALIDATED",
    limitations="Supplements contain only the trigger-classification scheme and summary-statistic tables. The event-level database (dates, coordinates, fatalities) is NOT redistributed with the article, so GFLD contributed no Wayanad records")

add(dataset_id="INV-13", category="landslide_inventory",
    dataset_name="Recent Kerala landslide event tables from two 2025 open-access papers",
    provider="Scientific Reports (Ramesh et al. 2025; Sreekumar et al. 2025)",
    product_version="PMC12290006 / PMC12749052",
    source_url="https://doi.org/10.1038/s41598-025-07828-3 ; https://doi.org/10.1038/s41598-025-33065-9",
    acquisition_date="2026-10-25", time_period="2018-2024 events",
    spatial_extent="Kerala; 2 Wayanad records (Mundakkai 2024, Puthumala 2019)",
    native_resolution="event point (whole-second DMS)", crs="unstated (geographic degrees)",
    format="JATS XML full text", local_path="data/raw/literature_events/", size_mb="0.3",
    validation_status="DOWNLOADED_NOT_FULLY_VALIDATED",
    limitations="Event metadata only. Coordinates are compiled rather than surveyed by these authors, so their Puthumala 2019 record remains SECONDARY_SOURCE_ONLY; modelling results in these papers are out of scope for this project")

add(dataset_id="INV-14", category="landslide_inventory",
    dataset_name="GSI 15990 Detailed site-specific study of Plamoola subsidence, Wayanad (FS 2020-21)",
    provider="Geological Survey of India", product_version="Item M4LS/NC/SR/SU-KRL/2020/30826",
    source_url="https://bhusanket.gsi.gov.in/Output/LandslideReport/Kerala/Site%20Specific%20Studies/15990.pdf",
    acquisition_date="2026-10-25", time_period="subsidence 2018-08-13 to 2018-08-17",
    spatial_extent="Plamoola (Jessee Estate area), Wayanad", native_resolution="site map 1:1,000 (raster plate)",
    crs="unstated", format="PDF + extracted text",
    local_path="data/raw/landslide_inventory/gsi_bhusanket/pdf/gsi_15990.pdf",
    size_mb="3.2", validation_status="DOWNLOADED_NOT_FULLY_VALIDATED",
    limitations="The 2020-21 label is the field season, not the event year: the report dates the subsidence to 13-17 August 2018. No DMS coordinate appears in the text layer, so no point could be extracted; contributing areas are given only in km2")

add(dataset_id="INV-15", category="landslide_inventory",
    dataset_name="GSI 12272 / 12236 geo-environmental studies of landslide-prone Wynad (1992-94)",
    provider="Geological Survey of India", product_version="Acc. Nos 12272 and 12236",
    source_url="https://bhusanket.gsi.gov.in/Output/LandslideReport/Kerala/Macro%20scale%20studies/12272.pdf",
    acquisition_date="2026-10-25", time_period="1992-1994 fieldwork, pre-2000 events",
    spatial_extent="Wynad/Wayanad and Calicut districts", native_resolution="1:50,000-report plates",
    crs="unstated", format="PDF + extracted text",
    local_path="data/raw/landslide_inventory/gsi_bhusanket/pdf/", size_mb="11.1",
    validation_status="DOWNLOADED_NOT_FULLY_VALIDATED",
    limitations="Predate the 2000-2026 window; useful only as historical/geological context. 12236 has no text layer (scanned images only) and would require OCR")

add(dataset_id="INV-16", category="derived",
    dataset_name="Phase-2 consolidated Wayanad inventory (source records, events, crosswalk, coverage)",
    provider="This project", product_version="phase2-v1",
    source_url="(local derivation from INV-01..INV-14)", acquisition_date="2026-10-25",
    time_period="1961-2025, coverage table for 2000-2026",
    spatial_extent="Wayanad district", native_resolution="point data", crs="EPSG:4326",
    format="CSV", local_path="data/processed/inventory/", size_mb="0.6",
    validation_status="VERIFIED",
    limitations="A derived product, not an original source. 468 source records with 372 in the 2000-2026 window forming 371 event groups; 445/468 points fall inside the GADM polygon; no record is a field-verified observation by this project")

# ---------------------------------------------------------------------------
# Phase 3 derived products (geospatial preprocessing)
# Sizes are measured from disk at build time. Accumulated scope is recorded in
# docs/PREPROCESSING_REPORT.md; verdicts in docs/DATA_READINESS_REPORT.md.
# ---------------------------------------------------------------------------

add(dataset_id="P3-01", category="derived",
    dataset_name="Phase-3 analysis grid: 30 m common grid, district mask, metric boundary layers",
    provider="This project", product_version="phase3-grid",
    source_url="(local derivation from BND-01, BND-02)",
    acquisition_date="2026-10-26", time_period="n/a (spatial framework)",
    spatial_extent="2480 x 2013 px, EPSG:32643; extent 583110-657510 E / 1264170-1324560 N; 2,356,538 district px = 2,120.9 km2",
    native_resolution="30 m", crs="EPSG:32643",
    format="GeoTIFF (mask) + GeoPackage (boundaries) + JSON (spec) + CSV",
    local_path="data/processed/grid/", size_mb=size_mb("data/processed/grid"),
    validation_status="VERIFIED",
    limitations="The 30 m grid is a storage geometry, not a claim of 30 m information for coarser sources. Mask is pixel-centre (-0.005% vs GADM). GADM/OSM outlines differ by ~750 m median, so edge membership within ~0.75 km is ambiguous")

add(dataset_id="P3-02", category="derived",
    dataset_name="Phase-3 terrain stack: GLO-30 DSM mosaic, buffered and district DEM, slope, aspect, profile and plan curvature",
    provider="This project", product_version="phase3-dem",
    source_url="(local derivation from DEM-01, cross-checked against DEM-03)",
    acquisition_date="2026-10-26", time_period="2021 epoch surface",
    spatial_extent="District elevation 116.96-2,230.27 m; 5 district layers + 2 intermediates",
    native_resolution="30 m", crs="EPSG:32643", format="GeoTIFF (float32)",
    local_path="data/processed/dem/", size_mb=size_mb("data/processed/dem"),
    validation_status="VERIFIED",
    limitations="DSM including canopy, not bare earth (district is 90% tree cover). Slope uncertainty +/-2.24 deg (MAD vs SRTM). Aspect is nodata on 0.483% of district (flat ground). Vertical datum EGM2008: town checks show a consistent ~-30 m offset. TRI/TPI deliberately not produced")

add(dataset_id="P3-03", category="derived",
    dataset_name="Phase-3 land cover: ESA WorldCover 2021 aggregated 10 m to 30 m by mode",
    provider="This project", product_version="phase3-landcover",
    source_url="(local derivation from LC-01)", acquisition_date="2026-10-26",
    time_period="2021 snapshot", spatial_extent="7 classes over the district, 0 nodata",
    native_resolution="30 m grid; 10 m source", crs="EPSG:32643", format="GeoTIFF (uint8) + 2 CSV",
    local_path="data/processed/landcover/", size_mb=size_mb("data/processed/landcover"),
    validation_status="VERIFIED",
    limitations="Present-day 2021 proxy, not land cover at event time. Mode aggregation loses minority classes: built-up -0.151 pp (-17% relative), bare/sparse -47%, shrubland disappears. Tree cover 90.1%, and class 10 does not distinguish plantation from forest")

add(dataset_id="P3-04", category="derived",
    dataset_name="Phase-3 rainfall: CHIRPS v2.0 district monthly series and 30 m climatology rasters",
    provider="This project", product_version="phase3-rainfall",
    source_url="(local derivation from RF-01)", acquisition_date="2026-10-26",
    time_period="2000-01 to 2025-12 (312 months, no 2026)",
    spatial_extent="District area-weighted series; annual mean 2,439.1 mm (std 351.0); JJAS 1,601.1 mm",
    native_resolution="30 m grid; 0.05 deg (~5.5 km) effective", crs="EPSG:32643",
    format="GeoTIFF (float32, 12-band climatology) + 3 CSV",
    local_path="data/processed/rainfall/", size_mb=size_mb("data/processed/rainfall"),
    validation_status="VERIFIED",
    limitations="Monthly at 5.5 km: supports antecedent-condition covariates, not triggers. Upsampling creates no detail. No per-event rainfall assigned. The undeclared -9999 sentinel is absent from all district cells but present in every padded window")

add(dataset_id="P3-05", category="derived",
    dataset_name="Phase-3 soil: SoilGrids 250 m, 7 properties x 2 depths, scaled to physical units",
    provider="This project", product_version="phase3-soil",
    source_url="(local derivation from SOIL-01)", acquisition_date="2026-10-26",
    time_period="static (SoilGrids 2017 release)", spatial_extent="14 native + 14 grid rasters; 3,657 district nodata px (0.155%)",
    native_resolution="30 m grid; 250 m (~246 x 265 m) effective", crs="EPSG:32643",
    format="GeoTIFF (float32) + 2 CSV",
    local_path="data/processed/soil/", size_mb=size_mb("data/processed/soil"),
    validation_status="VERIFIED",
    limitations="Model predictions, not soil samples, and no regolith/bedrock depth. Raw 0 treated as nodata, so a genuine cfvo = 0% is discarded (50 cells, 3.1 km2). Scale factors proven by texture closure (clay+sand+silt = 100.0%)")

add(dataset_id="P3-06", category="derived",
    dataset_name="Phase-3 geology: GLiM district intersection and 5-class raster",
    provider="This project", product_version="phase3-geology",
    source_url="(local derivation from GEO-01)", acquisition_date="2026-10-26",
    time_period="static (source maps to 2015)", spatial_extent="16 polygons, 5 classes, 2,121.0 km2 = 100% of GADM",
    native_resolution="30 m grid; polygon scale ~1-4.6 km", crs="EPSG:32643",
    format="GeoPackage + GeoTIFF (uint8) + 3 CSV",
    local_path="data/processed/geology/", size_mb=size_mb("data/processed/geology"),
    validation_status="VERIFIED",
    limitations="1:3.75 M source cannot resolve local lithology: 39 GSI charnockite-gneiss records split 22/14/1 across three GLiM classes; median 1,063 m to a class boundary. Descriptive regional context only; GSI 1:50,000 remains missing. The Phase-1 bbox clip is retained unmodified alongside")

add(dataset_id="P3-07", category="derived",
    dataset_name="Phase-3 additional layers: OSM roads and HydroRIVERS clipped and reprojected to EPSG:32643",
    provider="This project", product_version="phase3-additional",
    source_url="(local derivation from ADD-01, ADD-02)", acquisition_date="2026-10-26",
    time_period="2026 snapshot", spatial_extent="13,169 road features / 5,968.2 km; 1,298 river segments / 3,195.5 km",
    native_resolution="vector line", crs="EPSG:32643", format="GeoPackage + JSON",
    local_path="data/processed/additional/", size_mb=size_mb("data/processed/additional"),
    validation_status="VERIFIED",
    limitations="Present-day proxies with no temporal depth. Roads: 0 features lost, 100.0% of in-district length retained. Rivers: 40/1,298 segments (3.08%) truncated at the boundary, so no flow routing. Distance rasters deliberately not produced")

add(dataset_id="P3-08", category="derived",
    dataset_name="Phase-3 inventory suitability: per-record precision, uncertainty class and spatial use",
    provider="This project", product_version="phase3-suitability",
    source_url="(local derivation from INV-16 and Phase 2 source tables)",
    acquisition_date="2026-10-26", time_period="1961-2025 records; usability for 2000-2026 labels",
    spatial_extent="468 source records; 408 usable point labels from 363 event groups",
    native_resolution="point data", crs="EPSG:4326", format="CSV + JSON",
    local_path="data/processed/inventory/inventory_spatial_suitability.csv",
    size_mb=size_mb("data/processed/inventory/inventory_spatial_suitability.csv",
                    "data/processed/inventory/event_group_point_status.csv",
                    "data/processed/inventory/inventory_suitability_summary.json"),
    validation_status="VERIFIED",
    limitations="A judgement layer, not new evidence: accuracy floors are assumptions. 408 point_label_ok, 36 widen, 10 boundary-uncertain, 12 not in district, 1 district centroid, 1 excluded until corrected. None of the 44 two-decimal records is a point label. 92% of usable labels are 2018. Phase 2 tables are byte-identical and were not modified")

add(dataset_id="P3-09", category="derived",
    dataset_name="Phase-3 cross-layer QA: layer inventory, grid alignment, coverage and clustering metrics",
    provider="This project", product_version="phase3-qa",
    source_url="(local derivation from all P3 products)", acquisition_date="2026-10-26",
    time_period="n/a", spatial_extent="25 layers checked; 408/408 labels valid in all 24 predictor layers",
    native_resolution="30 m", crs="EPSG:32643", format="CSV + JSON",
    local_path="data/processed/qa/", size_mb=size_mb("data/processed/qa"),
    validation_status="VERIFIED",
    limitations="Coverage is a validity test only: predictor values were read at labels to count nodata and then discarded. No training table exists. Clustering figures (76 single-linkage clusters at 1 km) are a design input, not a validation result")

out = pathlib.Path(r"C:\Major\docs\data_manifest.csv")
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=COLS)
    w.writeheader()
    w.writerows(R)
print("wrote", out, len(R), "datasets")
