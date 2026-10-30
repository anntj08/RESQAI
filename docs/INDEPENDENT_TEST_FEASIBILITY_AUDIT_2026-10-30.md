# Independent real-data test — Stage 1 feasibility audit

**Date:** 2026-10-30 · **Run:** RUN-2026-10-30-01 · **Type:** read-only audit of local data and
training membership. **No model was run, no score was computed, no metric was inspected, no file
outside this document and its run report was modified.**

**Question:** is there a real landslide dataset already on disk that is independent of the Phase 5
training set and large enough to support an honest test of the fixed Random Forest susceptibility
baseline?

**Answer: no.** Every dated event record for 2000–2026 that exists locally is already a Phase 5
training label, and the 2024 records — the natural demonstration target — are two event groups in a
single fold (fold 3), which is below the five-cluster minimum the project already treats as marginal.
The records that never entered training are undated, out of the temporal window, or spatially the
same sites as training labels. Nothing on disk can be scored honestly today.

> **Vocabulary kept.** Susceptibility is a relative ranking of *where* conditions favour failure. It
> is not a prediction of whether or when a landslide occurs. Background points mean "no mapped event
> in the available inventory", never confirmed stable ground. ROC-AUC and average precision are
> presence–background ranking metrics, not accuracy.

---

## 1. What was audited

| Item | Path |
|---|---|
| Exact modelling points used by Phase 5 | `data/processed/sampling/modelling_points.csv` (2,460 rows) |
| Fold membership | `data/processed/sampling/fold_assignments.csv` |
| 1,000 m test-fold buffer drops | `data/processed/sampling/fold_drops.csv` (418 rows) |
| Background sample | `data/processed/sampling/background_samples.csv` (2,097 rows) |
| Per-record eligibility decisions | `data/processed/sampling/eligibility_audit.csv` (468 rows) |
| Sampling run metadata | `data/processed/sampling/sampling_run_config.json` |
| Full source-record table | `data/processed/inventory/inventory_source_records.csv` (468 rows, 8 sources) |
| Cross-source duplicate links | `data/processed/inventory/duplicate_crosswalk.csv` (45 rows) |
| 2024 corroboration distances | `data/processed/inventory/2024_corroboration.json` |
| Year-by-year coverage | `data/processed/inventory/coverage_2000_2026.csv` (27 rows) |
| Two GSI PDLS Wayanad datasheets | `data/interim/inventory_extracts/inventory_gsi_pdls_wayanad.csv` |
| Source discovery (2024) | `docs/SOURCE_DISCOVERY_2024_WAYANAD_INVENTORY.md` (RUN-10) |
| Request package status | `docs/requests/` (RUN-11/12), `reports/RUN-2026-10-29-12_*.md` |

Existing verification evidence was reused; no gate was re-run, because no inconsistency required it.

---

## 2. The reference frame: what Phase 5 actually trained on

From `modelling_points.csv` and `sampling_run_config.json`:

- **2,460 modelling points** = **363 positives** (label 1) + **2,097 background** (label 0), ratio 5.78:1,
  seed 20261026, EPSG:32643, 30 m grid, 100 m positive exclusion radius.
- **76 distinct clusters**; folds hold 471 / 541 / 503 / 473 / 472 points.
- Positives by event year: **2018 = 335**, 2007 = 15, 2009 = 7, 2006 = 2, 2024 = 2, 2019 = 1,
  2008 = 1.
- **Non-2018 positives: 28 labels in 28 event groups across 17 clusters** — the same figure already
  recorded in `docs/PHASE5_PROGRESS.md` §4 ("not viable, so temporal transfer is untested").
- `fold_drops.csv`: 418 drops (392 background, 26 positive), every one a 1,000 m test-fold buffer rule.
- Background: 2,097 rows, all in-district, all with valid predictors, minimum 113.7 m from a positive.

**Consequence for this audit:** independence is not "was the record from 2024?" but "is the record's
`event_group_id` absent from these 363 positives, and is its location outside the 1,000 m buffer that
already removes training points from held-out folds?" A record that is in the training set cannot be a
test record at any fold, because every fold model saw it in the other four folds.

---

## 3. Candidate audit table

Usable = in-district, dated inside 2000–2026 where the candidate has dates, and carrying a point
coordinate. "Overlap" is measured two ways: exact `event_group_id` membership, and distance in
EPSG:32643 to the nearest of the 363 training positives.

| # | Candidate dataset (source IDs) | Event / date coverage | Usable records | Distinct event groups | Verification / provenance | Overlap with Phase 5 training | Comparison class available | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | Phase 4 inventory as a whole (8 sources) | 1961–2024 | 468 records, 363 labelled positives | 363 dated groups + 78 undated records | mixed: `SOURCE_CONFIRMED` / `CORROBORATED` / `SECONDARY_SOURCE_ONLY` / `NEEDS_REVIEW` | **100 %** — this *is* the training set | n/a | **NOT INDEPENDENT** |
| 2 | 2018 core (`KER2018` 331 + `GSI2018` 8) | 2018 monsoon | 339 records → 335 positives | 335 | `SOURCE_CONFIRMED` (GSI), KSDMA/DanS compilation | **335/335 in training**, 65 clusters | n/a | **NOT INDEPENDENT** |
| 3 | GSI 14115 2006–2009 (`GSI14115`) | 2006–2009 | 25 | 25 | `SOURCE_CONFIRMED`, ≤100 m precision | **25/25 in training** | n/a | **NOT INDEPENDENT** |
| 4 | **2024 events** (`GSI_PDLS` ×2, `LIT2025` ×1) | 30 Jul 2024 + Jun 2024 | 3 records → 2 labels (1 duplicate merged) | **2** (`EV-2024-MUNDAKKAI`, `EV-2024-MEENAKSHI-BRIDGE`) | `SOURCE_CONFIRMED` (GSI) + `CORROBORATED` (LIT2025) | **2/2 in training, both fold 3**; distance to nearest positive **0.00 m** | only the 2,097 Phase 4 background points, all training labels | **NOT INDEPENDENT** (and **INSUFFICIENT**: 2 clusters < 5 minimum) |
| 5 | 2019 Puthumala (`LIT2025`) | 8 Aug 2019 | 1 | 1 (`EV-2019-PUTHUMALA`) | `SECONDARY_SOURCE_ONLY` (single peer-reviewed table) | **in training, fold 3**; distance **0.00 m** | none | **NOT INDEPENDENT** (and **INSUFFICIENT**) |
| 6 | Pre-2000 GSI 14115 (`GSI14115`) | 1961, 1984, 1988, 1991 | 6 | 6 | `SOURCE_CONFIRMED`, ≤100 m precision | not labelled, but **5 of 6 within 1,000 m of a training positive** (220–617 m); only one at 1,833 m | would need a fresh background | **INSUFFICIENT** |
| 7 | Undated site records (`GSI14337` 35, `GSI14768` 41, `GSI14115` 2) | **no dates** | 78 (73 spatially usable; 43 ≤100 m, 35 300–800 m) | 0 dated; 28 spatial clusters at 1 km | mixed precision; `GSI14337`/`GSI14768` are regional compilations | `GSI14337`: **35/35 crosswalked to `GSI14115`, 26 of those are training positives**; `GSI14768`: 16/41 within 100 m, 24/41 within 1 km | would need a fresh background | **INSUFFICIENT** |
| 8 | NASA Global Landslide Catalog (`NASA_GLC`) | 1997–2016 | 9 records, **0 usable in district** (7 outside, 1 district centroid, 1 needs widening) | 0 | media-derived, reported location accuracy 1–50 km | n/a | none | **INSUFFICIENT** |
| 9 | Global Fatal Landslide Database (`GFLD`) | 2004–2016 | **0 event records** (supplementary summary tables only) | 0 | article supplement, no event table redistributed | n/a | none | **INSUFFICIENT** |
| 10 | KSDMA / NDMA / CEMS 2024 documents | 2024 | **0 coordinate tables** (reports and maps only) | 0 | official prose/recovery documents | n/a | none | **INSUFFICIENT** |

Rows 8–10 were already classified in RUN-10 (`docs/SOURCE_DISCOVERY_2024_WAYANAD_INVENTORY.md`) and in
`docs/data_manifest.csv` (INV-04, INV-12); they are listed here only so the candidate space is closed.

---

## 4. Overlap measurements (EPSG:32643, exact)

### 4.1 The three post-2018 event groups are training points, to the metre

| Event group | Training point | Fold | Cluster | Nearest positive | Nearest background |
|---|---|---|---|---|---|
| `EV-2024-MUNDAKKAI` | `POS-EV-2024-MUNDAKKAI` | 3 | 13 | **0.00 m** (itself) | 208.0 m (`BG-02092`, fold 3) |
| `EV-2024-MEENAKSHI-BRIDGE` | `POS-EV-2024-MEENAKSHI-BRIDGE` | 3 | 14 | **0.00 m** (itself) | 141.4 m (`BG-02008`, fold 3) |
| `EV-2019-PUTHUMALA` | `POS-EV-2019-PUTHUMALA` | 3 | 75 | **0.00 m** (itself) | 160.5 m (`BG-02067`, fold 3) |

The 0.00 m values are not a tolerance: the stored modelling coordinate reproduces the source record
exactly. `EV-2024-MUNDAKKAI` uses the GSI datasheet coordinate (11.462778, 76.134167); the independent
Sreekumar et al. (2025) record (11.466944, 76.135833) sits **495.29 m** away and was merged into the
same group as `POSITIVE_EVENT_DUPLICATE`, so the second 2024 record is not an extra test case either.
`EV-2024-MEENAKSHI-BRIDGE` and `EV-2019-PUTHUMALA` each reproduce their single source coordinate at
0.00 m.

No candidate group is absent from the training set. Every *usable* 2000–2026 dated event record on
disk is a label; the only in-window records that are not labels are the 5 boundary-uncertain and 1
coordinate-error records, which are unusable as test points rather than independent of training. The
"2024 test set" is two points the model was fitted on.

### 4.2 Distance profile of the pools that never entered training

| Pool | n | min | median | max | ≤100 m of a positive | ≤1 km |
|---|---|---|---|---|---|---|
| Undated site records | 78 | 0 m | 434 m | 16,579 m | **16** | **58** |
| Pre-2000 dated | 6 | 220 m | 551 m | 1,833 m | 0 | **5** |
| Boundary-uncertain | 5 | 288 m | 1,321 m | 5,829 m | 0 | 1 |
| Outside district | 12 | 5,534 m | 20,908 m | 46,582 m | 0 | 0 |

Even the never-labelled pool is not locationally independent: 16 undated records sit within 100 m of a
training positive and 58 within 1 km. Raising the exclusion radius does not rescue it — at >1 km only
20 undated records remain (17 precise, 3 coarse) in 10 clusters, and those are still undated
`GSI14337`/`GSI14768` records, which are village-centroid restatements of the same GSI investigations
(§4.3).

### 4.3 The undated compilation is a restatement, not a second dataset

`duplicate_crosswalk.csv` contains **35 rows linking every `GSI14337` record to a `GSI14115` record**
(distances 126.6 m – 16,579 m; basis "same publisher lineage; 14337 gives village centroid at 2 dp,
14115 the surveyed site"). Of those 35 partners, **26 are Phase 5 training positives**, 7 are pre-2000,
2 are themselves undated. So `GSI14337` cannot serve as an independent test set: 26 of its 35 rows are
the same investigations the model was trained on, recorded at coarser coordinates.

`GSI14768` has no crosswalk rows; 16 of its 41 undated in-district records are within 100 m of a
training positive, which is strong evidence of the same sites recorded twice. Its records carry no
dates, so they cannot support an event-level test even if the duplication were resolved.

---

## 5. Sufficiency and the comparison class

**Record/cluster sufficiency.** The project's own configured minimum is **5 distinct clusters per
evaluation group**, and fold 2 is already flagged marginal at exactly 5. The candidates fall far below
that:

| Candidate | Clusters available for an out-of-training test | Against the 5-cluster minimum |
|---|---|---|
| 2024 events | **2** (clusters 13, 14) | fails |
| 2019 Puthumala | **1** (cluster 75) | fails |
| Pre-2000 events | 6, of which **1** is >1 km from a training positive | fails |
| Undated records | 28 spatial clusters, but **0 dated**; 26/35 `GSI14337` rows duplicate training positives | fails |

**Comparison class.** A ranking test needs positives *and* background. The only background on disk is
the 2,097 Phase 4 points, and every one is a training label in the model being tested; its 100 m
exclusion radius was also fitted around the training positives. Scoring test positives against that
background would measure separation from the model's own negatives, not independent performance. A
fresh background can be drawn from the same 30 m district grid with the same exclusion rule, but it
must be pre-registered before any score is looked at, and it remains drawn from the same sampling
frame — a limitation to state, not to hide.

**What a landslide-only point set can and cannot support.** With enough independent clusters, a
presence–background ranking test (case ranking against a separately justified background sample) is
defensible. It does **not** establish classification accuracy, false-positive rates, calibration, or
performance on confirmed stable ground — the inventory contains no confirmed absences.

---

## 6. Status of the official-data request

- The letter and three attachments exist in `docs/requests/` and are internally consistent
  (RUN-11, RUN-12).
- **Nothing has been sent.** All four files still carry the `STATUS: … NOT SENT` banner; RUN-11 and
  RUN-12 both record "no draft sent, no agency contacted"; the tree is clean at `c6303c4`.
- **No reply and no new dataset exists locally.** The newest file anywhere under `data/raw` is
  `data/raw/landslide_susceptibility_reference/Wayanad.zip` (2026-10-28 23:27); the newest file in
  `docs/requests/` is 2026-10-29 21:44. Nothing was added after the package was prepared.
- **This audit does not infer that a request was sent**, and it did not contact anyone.

---

## 7. Readiness conclusion (plain language)

**A real independent test cannot be run today.** There are two independent reasons, and either one
alone would be enough:

1. **Every usable 2000–2026 event on disk is in the training set.** The 2024 Mundakkai–Chooralmala
   and Meenakshi Bridge records, the 2019 Puthumala record, and all 25 GSI 2006–2009 events are among
   the 363 positives, and all three post-2018 groups sit in fold 3. Testing on them would re-score
   points the model was fitted on.
2. **The records that are not in training are too few, undated, or the same sites.** The pre-2000 pool
   is six records with five of six within 1 km of a training positive. The 78 undated records have no
   dates, and 26 of the 35 `GSI14337` rows are already training positives under a coarser coordinate.

So the honest statement for a faculty audience today is: the baseline has spatially held-out
presence–background ranking results from Phase 5, and **no independent validation has been performed**.
That is a defensible position; presenting a 2024 score computed on training points would not be.

**What is missing, specifically:**

- Site-level records for the July 2024 event **beyond the single Mundakkai–Chooralmala datasheet
  point** — the other lobes and the Attamalai/Vellarimala/Chooralmala incidences named only in report
  prose. These are the subject of the prepared request.
- **At least ~15–20 distinct, dated event clusters** outside the training set to make an evaluation
  group comparable in size to the weakest Phase 5 fold (fold 2: 84 positives, 5 clusters — already
  marginal). Two or six clusters cannot support a per-fold-style claim.
- **A pre-registered background sample** that is disjoint from the 2,097 training background points,
  with the exclusion rule fixed before any score is seen.
- **A locked protocol** stating in advance: which records, which exclusion radius, which metric
  (ROC-AUC and/or average precision as ranking measures), what counts as support, and how the result
  will be worded if it is weak.

---

## 8. Recommended staged path (each stage independently verifiable)

**Stage 2 — acquisition and validation (data first, no model).**
Acquire whatever official site records become available (reply to the prepared request, or another
public source found later). Validate each record as a new source: identifier, printed coordinate,
stated precision, date, provenance, access condition. Add records to the inventory through the normal
acquisition → validation → manifest route; never paste them into existing rows. Gate: a record table
with per-record status, and a count of **distinct event groups not present in the 363 training
positives**. If that count is below ~15 clusters, stop and report "insufficient for an independent
test" — do not lower the bar.

**Stage 3 — locked test protocol (still no scoring).**
Freeze, in a committed document, before any score is computed: the candidate record set (by stable
ID), the exclusion radius against training points, the background sampling rule and seed, the metrics
and their names (ranking, not accuracy), the per-group reporting unit, and the wording rules. Gate: a
protocol file whose hash is recorded, plus an independence check that every candidate is outside the
training set and outside the 1,000 m buffer.

**Stage 4 — evaluation and demonstration.**
Run the fixed Phase 5 configuration unchanged against the locked protocol. Report per-group ranking
metrics with support and cluster counts beside them, exactly as Phase 5 does, and state the
limitations first. Gate: recomputation reproduces the reported numbers, and the independence check is
re-run inside the evaluation script so a leak cannot pass silently.

**Explicitly out of scope for all three stages:** tuning the Random Forest, replacing it, adding
synthetic events, or describing any output as a forecast, warning, or timing prediction.

---

## 9. What must not be done next (guard rails)

- Do not score the 2024 or 2019 points. They are training labels; any number produced from them is
  in-sample and must not be presented as validation.
- Do not treat `GSI14337` as an independent dataset. It is a village-centroid restatement of
  `GSI14115`, 26/35 of which are training positives.
- Do not lower the 5-cluster minimum or drop the fold-2 caveat to make a small test look adequate.
- Do not relabel undated records with inferred dates, and do not snap coordinates to increase apparent
  independence.
- Do not call a background sample "stable ground", and do not call ROC-AUC "accuracy".
- Do not describe the project as forecasting or early warning.

---

## 10. Evidence index

| Claim | Evidence |
|---|---|
| 2,460 points, 363/2,097 split, folds, seed, CRS | `data/processed/sampling/modelling_points.csv`, `sampling_run_config.json` |
| 28 non-2018 positives / 17 clusters | `modelling_points.csv` (event_year, cluster_id); matches `docs/PHASE5_PROGRESS.md` §4 |
| 2024/2019 groups are training points at 0.00 m | `modelling_points.csv` rows `POS-EV-2024-MUNDAKKAI`, `POS-EV-2024-MEENAKSHI-BRIDGE`, `POS-EV-2019-PUTHUMALA` |
| 495.29 m duplicate merge | `data/processed/inventory/2024_corroboration.json`; `duplicate_crosswalk.csv` |
| 35/35 `GSI14337` → `GSI14115` links, 26 to positives | `data/processed/inventory/duplicate_crosswalk.csv` + `eligibility_audit.csv` |
| Undated/pre-2000 distance profiles | `inventory_source_records.csv` coordinates → EPSG:32643 vs `modelling_points.csv` positives |
| 418 drops, 1,000 m buffer | `data/processed/sampling/fold_drops.csv` |
| NASA GLC / GFLD unusable | `docs/data_manifest.csv` INV-04, INV-12 |
| No 2024 inventory in official channels | `docs/SOURCE_DISCOVERY_2024_WAYANAD_INVENTORY.md` |
| Request not sent, no reply | `docs/requests/*` banners; `reports/RUN-2026-10-29-11`, `-12`; `data/raw` mtimes |
