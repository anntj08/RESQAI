# Run Report RUN-2026-10-28-05 — KSDMA-hosted GSI 2022 Wayanad LSZ shapefile: acquisition and validation

**Date:** 2026-10-28 · **Session goal:** acquire and validate the KSDMA-hosted GSI 2022 Wayanad
landslide susceptibility zones shapefile as a **separate comparison/reference dataset** — NOT
geology, never a predictor or model input, no Phase 4/5 output touched.
**Starting state:** commit `6a5e965` (RUN-2026-10-28-04 complete), tree clean.
**End state:** commit of this run (pinned in §6); dataset preserved raw + validated with
measured evidence; manifest row `LSZ-01` = **`DOWNLOADED_NOT_FULLY_VALIDATED`**; tree clean;
nothing pushed.

## 1. What was run, in order

| # | Command / file | Purpose | Result |
|---|---|---|---|
| 1 | re-read `AGENTS.md`, `reports/README.md`; `git status` | conventions + clean-start check | AGENTS.md unchanged since `355b0c0`; tree clean at `6a5e965` |
| 2 | webfetch `https://sdma.kerala.gov.in/hazard-maps/` | re-confirm the official page still lists the archive | row "Landslide Susceptibility zones of District of Kerala (GSI, 2022)- Shape files", item 11 → `/wp-content/uploads/2025/08/Wayanad.zip`; also the standing KSDMA note that the GSI LSM replaces all other Kerala LSM maps in KSDMA publications; **no explicit license statement on the page** |
| 3 | `python scripts/fetch_ksdma_lsz_wayanad.py` | download ONLY the Wayanad archive, preserve original | HTTP 200, `application/zip`, 3,072,545 B = 2.93 MB, sha256 `e5da8e031c0523a8f98a1086f4c13ebaad76721cd2afd34e6a20b35556037e2f`, Content-Length matches, magic `PK\x03\x04` → `data/raw/landslide_susceptibility_reference/Wayanad.zip` (written as `.part`, atomically renamed) + `data/interim/lsz_reference/fetch_evidence.json` |
| 4 | `python scripts/validate_ksdma_lsz_wayanad.py` | validate the actual file | sha256 re-check ✓; zip CRC ✓ (7 members); layer `Wayanad_GSI_LS.shp`: 3 MultiPolygons, EPSG:32643, attribute `Susceptibi` ∈ {High, Low, Moderate}, **3/3 geometries invalid**; coverage GADM 95.99 % / 30 m mask 95.99 % (all_touched 96.11 %) / OSM 99.07 % → `validation.json` |
| 5 | `python scripts/diagnose_lsz_boundary_fit.py` | explain the ~4 % mismatch + validity | buffer(0) changes **no** areas; GADM−LSZ = 85.08 km² / 27 parts; LSZ−GADM = 82.79 km² / 27 parts; LSZ boundary vs GADM: median 693.6 m, p95 1123.0 m, max 1456.0 m; in-archive `.shp.xml` lineage captured (§2) |
| 6 | `python scripts/lsz_rim_vs_interior.py` | rim vs interior holes | **zero interior parts**: all 27+27 difference parts touch the GADM boundary; LSZ boundary vs **OSM**: median 86.4 m, p95 282.6 m, max 422.3 m (92.4 % within 250 m) → the LSZ clip boundary follows the OSM-like boundary, not GADM |
| 7 | manifest row `LSZ-01`; `PHASE4_PROGRESS.md` §3 count sentence; `data_sources.md` §1.4 bullet | record confirmed facts | done (§5) |
| 8 | manifest post-edit row probe; p2/p3/p4 checkers; `git diff --check` | regression | probe caught a column shift (§3 #4), fixed; p2 pass, p3 470/470, p4 116/116, diff-check clean |
| 9 | commit | capture | see §6 |

## 2. Measured values (do not re-derive; every number traceable to an evidence file)

**Official page (re-fetched 2026-10-28).** KSDMA hazard-maps table row: *"Landslide
Susceptibility zones of District of Kerala (GSI, 2022)- Shape files"*, item 11
`https://sdma.kerala.gov.in/wp-content/uploads/2025/08/Wayanad.zip`. The same page states the
GSI LSM replaces all other Kerala LSM maps in KSDMA publications (NCESS 2010 link removed).
**No explicit license statement on the hosting page** → recorded as "published as public hazard
information by KSDMA; source attribution GSI 2022; no restrictions stated on hosting page".

**Archive.** `data/raw/landslide_susceptibility_reference/Wayanad.zip` — 3,072,545 B (2.93 MB),
sha256 `e5da8e031c0523a8f98a1086f4c13ebaad76721cd2afd34e6a20b35556037e2f`, HTTP 200,
`application/zip`, Content-Length match, PK magic, CRC OK on all 7 members, member dates
2025-08-15 20:39 (folder entry 2025-08-21 14:55).

**Layer `Wayanad_GSI_LS.shp` (single layer in the archive).**
- CRS **EPSG:32643** (WGS 84 / UTM zone 43N — the project's metric CRS, read from `.prj`).
- **3 features**, all MultiPolygon, dissolved by class; parts per class: High 1,366, Low 1,287, Moderate 6,769.
- Single attribute **`Susceptibi`** (DBF-truncated name) with exactly **3 classes**: High, Low, Moderate (no "Very High"/"Very Low" in this district file).
- Bounds native (m): 584,398.83–657,346.10 E / 1,266,059.95–1,324,142.24 N; bounds WGS84:
  75.77472–76.44340 E / 11.45069–11.97599 N (district reference 75.7722–76.4356 / 11.4427–11.9706 — overlap confirmed, slight east/north spill).
- **3/3 geometries formally invalid** (self-intersecting rings, typical of raster→polygon
  conversion without cleanup). Measured sensitivity: **buffer(0) changes no measured areas**
  (per-class raw = buffer(0) exactly; union 2,118.6972 km² both ways).
- Class areas (EPSG:32643, measured): **Low 1,636.2242 km² (77.2 %)**, **Moderate 401.6119 km²
  (19.0 %)**, **High 80.8611 km² (3.8 %)** of the 2,118.6972 km² union; class features do not
  overlap (sum of class areas = union area exactly).

**Coverage (three measurements, evidence `validation.json`).**
- vs **GADM 4.1 Wayanad** (vector, EPSG:32643): intersection 2,035.9088 km² of 2,120.9922 km² =
  **95.99 %**; LSZ outside GADM 82.7885 km².
- vs **project 30 m district mask** (`district_mask_30m.tif`, 2,356,538 cells = 2,120.88 km²):
  2,261,996 cells = **95.99 %** (all_touched sensitivity 96.11 %).
- vs **OSM/Nominatim boundary** (supplementary): 2,108.8019 km² of 2,128.5519 km² = **99.07 %**.

**Why not 100 % — measured, not asserted.** GADM−LSZ = 85.0834 km² in **27 parts, ALL touching
the GADM boundary — zero interior holes**; LSZ−GADM = 82.7885 km², likewise 27/27 touching
(`rim_vs_interior.json`). Largest blocks: GADM-only 25.6074 km² (W/SW edge); LSZ-only 39.657 km²
(N edge). Boundary alignment: LSZ boundary vs **GADM** median **693.6 m** (p95 1,123 m, max
1,456 m; only 6.4 % of sampled vertices within 100 m) but vs **OSM** median **86.4 m** (p95
283 m; 92.4 % within 250 m). Interpretation: the archive was clipped to KSDMA's own district
boundary (see lineage below), which agrees with the OSM boundary and disagrees with GADM 4.1 by
up to ~1.5 km in places. Against the project's working boundary (GADM), coverage is 95.99 %, so
**full district coverage is NOT claimed**.

**In-archive provenance (`Wayanad_GSI_LS.shp.xml`, ArcGIS 10.8 metadata, kept in the extracted
working copy).** Processing lineage, verbatim tool names and dates:
1. `RasterToPolygon` of **`Susceptibility_KRL.img`** (the GSI Kerala LSZ **raster**) with
   NO_SIMPLIFY, field `Susceptibi`, SINGLE_OUTER_PART — 2025-08-12;
2. `Project` to **WGS 1984 UTM Zone 43N** with an explicit input-override from **UTM Zone 44N**
   (GSI's original Kerala vector was tagged zone 44N, wrong for 74–78°E; corrected here) —
   2025-08-14;
3. `Clip` with **`I_District_boundary_District`** (KSDMA district boundary layer) — 2025-08-14;
4. `Dissolve` by `Susceptibi` — 2025-08-15 20:39:23 (matches the zip member timestamps).

**Verdict (verification vocabulary).** File integrity ✓, format ✓, CRS ✓, plausibility ✓
(3 measured classes, no interior holes, bbox overlap). NOT met: **full district coverage**
(95.99 % vs GADM), file-stated resolution/scale (1:50K comes from the KSDMA page/GSI NLSM
programme, not from inside the file), and record-level accuracy (no field check). Status:
**`DOWNLOADED_NOT_FULLY_VALIDATED`** — the honest vocabulary fit; not `VERIFIED`, not geology,
never a forecast/warning/timing product.

## 3. Bugs caught and fixes

| # | Where | What | Fix |
|---|---|---|---|
| 1 | inline `python -c` under PowerShell | nested quotes broke parsing ("unterminated string literal") | wrote `scripts/lsz_rim_vs_interior.py` (repo convention: no complex inline python) |
| 2 | `validate_ksdma_lsz_wayanad.py` | `np.issubdtype(s.dtype, np.number)` raised TypeError on pandas `StringDtype` (geopandas 1.x reads .dbf text as `str` dtype, not object) | switched to `pd.api.types.is_string_dtype` / `is_numeric_dtype` / `is_bool_dtype` |
| 3 | same script | stray `.to_numpy()` called on an already-numpy mask array (would raise AttributeError) | removed; masks are plain numpy arrays |
| 4 | `docs/data_manifest.csv` LSZ-01 row | the `format` field contains a comma and was left unquoted → every later field shifted one column right; **caught by the post-edit row probe** (all three checkers passed anyway — they do not pin per-row column alignment) | quoted the field; re-probed: 44 rows, 16 cols, all LSZ-01 fields map correctly |

## 4. Verification and gates

| Suite | Result |
|---|---|
| p2 `p2_check_consistency.py` | pass (all 28 Phase-2 ids present; 16 columns; unique ids — now 44 rows) |
| p3 `p3_check_consistency.py` | **470/470** |
| p4 `p4_check_consistency.py` | **116/116** (needs `f"{len(man)} datasets"` = "44 datasets" in `PHASE4_PROGRESS.md` §3 — satisfied by the truthful amendment) |
| `git diff --check` | clean |
| manifest row probe (ad hoc) | 44 rows, 16 cols, ids unique, LSZ-01 fields all correctly aligned after fix |

## 5. Outputs produced or changed

- `data/raw/landslide_susceptibility_reference/Wayanad.zip` — **the original archive,
  preserved unchanged** (gitignored as raw; sha256 + size recorded in the manifest row and
  `fetch_evidence.json`).
- `data/interim/lsz_reference/` — committed evidence + working copies:
  `fetch_evidence.json`, `validation.json`, `boundary_fit_diagnostics.json`,
  `rim_vs_interior.json`, and `extracted/Wayanad/` (the `.shp/.shx/.dbf` are gitignored; the
  small `.prj` (CRS evidence), `.cpg` and `.shp.xml` (lineage evidence) are committed).
- `scripts/fetch_ksdma_lsz_wayanad.py`, `scripts/validate_ksdma_lsz_wayanad.py`,
  `scripts/diagnose_lsz_boundary_fit.py`, `scripts/lsz_rim_vs_interior.py` — re-runnable.
- `docs/data_manifest.csv` — **new row `LSZ-01`** (category `landslide_susceptibility`, status
  `DOWNLOADED_NOT_FULLY_VALIDATED`, sha256 in limitations). Geology rows `GEO-01`/`GEO-02` and
  all other rows untouched.
- `docs/PHASE4_PROGRESS.md` §3 — sentence amended truthfully: "…now has **43 datasets** (44
  datasets since RUN-2026-10-28-05 added the separate KSDMA-hosted GSI-2022 Wayanad LSZ
  reference row, `LSZ-01` — a comparison dataset, not a predictor)" (keeps the checker needle
  while stating the truth).
- `docs/data_sources.md` §1.4 — LSZ bullet updated: downloaded in `RUN-2026-10-28-05`, status
  and measured coverage summarised, never-a-predictor warning.

**Explicitly NOT done:** no clipping/resampling/merging into the predictor stack; no model,
map, or Phase 4/5 output touched; no other district's archive downloaded; the LSZ file was not
compared against the Phase 5 susceptibility map (out of scope this run).

## 6. Current project state

Phase 5 baseline complete and verified (unchanged). A second susceptibility product now exists
on disk as a **reference only**: GSI 2022 Wayanad LSZ (3 dissolved class polygons, EPSG:32643,
KSDMA-clip boundary), manifest `LSZ-01`, `DOWNLOADED_NOT_FULLY_VALIDATED`, kept strictly apart
from geology `GEO-01`/`GEO-02`, Phase 3 predictors, Phase 4 sampling and Phase 5 model/map
outputs. Commit of this run: **pinned in one line below** — git log entry "LSZ-01: KSDMA
GSI-2022 Wayanad susceptibility zones acquired and validated" carries the work + this report;
a one-line follow-up commit pins the hash here.

## 7. Next-step handoff (prompt material)

* **Open decisions for the user:**
  1. Whether to run a **map-vs-map comparison** (GSI 2022 LSZ classes vs the Phase 5 RF
     susceptibility surface) in a future run. It must be framed as class/zone agreement and
     ranking comparison — never as accuracy-vs-truth (LSZ is itself a model output, not
     ground truth), and must first fix which boundary defines "the district" (project GADM
     2,121.0 km² vs the file's KSDMA clip boundary; only 95.99 % overlaps GADM).
  2. Whether to also fetch the **statewide GSI LSZ PDF**
     (`/wp-content/uploads/2025/06/Landslide_Susceptibility_Zones_Districts_FINAL.pdf`) for
     documentation — not required for any current phase.
* **What the next step must do / must not do:** must keep `LSZ-01` out of the predictor stack
  and never call it geology; must use EPSG:32643 for any area/distance work; must re-run
  `validate_ksdma_lsz_wayanad.py` before re-use if the archive is ever re-downloaded (the URL
  is a live CMS upload — content can change without notice; the sha256 pins this copy). Must
  not retrain, tune, or alter Phase 5 outputs when the comparison resumes.
* **Quick commands:** `python scripts/fetch_ksdma_lsz_wayanad.py` ·
  `python scripts/validate_ksdma_lsz_wayanad.py` · `python scripts/diagnose_lsz_boundary_fit.py`
  · `python scripts/lsz_rim_vs_interior.py` · p2/p3/p4 checkers.
* **Do not re-derive (quote as-is):** sha256 `e5da8e031c0523a8f98a1086f4c13ebaad76721cd2afd34e6a20b35556037e2f`;
  3 features / 3 classes (Low 1,636.2242 km² = 77.2 %, Moderate 401.6119 km² = 19.0 %, High
  80.8611 km² = 3.8 % of union 2,118.6972 km²); coverage GADM 95.99 % / mask 95.99 %
  (2,261,996 of 2,356,538 cells) / OSM 99.07 %; zero interior holes (27+27 boundary-touching
  parts); boundary offset vs GADM median 693.6 m vs OSM median 86.4 m; buffer(0) area delta 0.0;
  in-archive lineage (RasterToPolygon of `Susceptibility_KRL.img` → Project 44N→43N → Clip to
  `I_District_boundary_District` → Dissolve, 2025-08-12…15); KSDMA page has no explicit license.
