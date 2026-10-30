# Run Report RUN-2026-10-30-01 — Independent real-data test, Stage 1: feasibility audit

**Date:** 2026-10-30 · **Session goal:** audit the local inventory against the exact Phase 4/5
training set and decide whether an honest independent test of the fixed Random Forest susceptibility
baseline is possible now — audit only, no evaluator, no score, no metric.
**Starting state:** commit `c6303c4` (RUN-2026-10-29-12 hash pin); tree clean.
**End state:** audit document + this report committed (hash in §6); tree clean; nothing pushed; no
agency contacted, no data acquired, no Phase 4/5 artefact touched. **Verdict: no local dataset
supports an honest independent test today.**

## 1. What was run, in order

| # | Command / file | Purpose | Result (exit, key numbers) |
|---|---|---|---|
| 1 | `Get-Date`, `git status --short`, `git log --oneline -4`, list `reports/RUN-*` | establish date, baseline commit, next run number | 2026-10-30; HEAD `c6303c4`; clean; no 2026-10-30 report → this is `01` |
| 2 | read `AGENTS.md`, `reports/README.md` | conventions + report template | read |
| 3 | read `docs/PHASE5_PROGRESS.md`, `docs/PHASE5_LIVE_DEMO.md`, `docs/SOURCE_DISCOVERY_2024_WAYANAD_INVENTORY.md`, `docs/INVENTORY_VERIFICATION_REPORT.md`, RUN-10/11/12 | project context, prior verification, request status | read; RUN-10 already closed the public-source question |
| 4 | list `data/processed`, `data/interim`, `data/raw/landslide_inventory` | enumerate local tables and raw sources | 8 inventory sources; GFLD/NASA/CEMS present but unusable (already documented) |
| 5 | `python` dump of `modelling_points.csv`, `fold_assignments.csv`, `fold_drops.csv`, `background_samples.csv`, `eligibility_audit.csv` (`%TEMP%\opencode\audit_stage1_a.py`, `_b.py`) | exact training composition and per-record eligibility | 2,460 points (363/2,097); 76 clusters; 468 eligibility rows; 418 drops |
| 6 | `python` distance script (`audit_stage1_c.py`) — EPSG:32643 via `pyproj` | distance of every never-labelled pool to the 363 training positives | undated 78: 16 ≤100 m, 58 ≤1 km; pre-2000 6: 5 ≤1 km |
| 7 | `python` dump (`audit_stage1_d.py`) | 2024 corroboration distances; raw-data mtimes; request package status | 495.3 m duplicate; newest raw file 2026-10-28 23:27; tree clean |
| 8 | `python` dump (`audit_stage1_e.py`, `_g.py`) | 2018 cluster count; undated group status; `GSI14337` crosswalk | 335 positives/65 clusters; 35/35 crosswalked, 26 to training positives |
| 9 | `python` dump (`audit_stage1_f.py`) | undated pool after 1/2.5/5/10 km exclusion | >1 km: 20 records, 10 clusters, 17 precise |
| 10 | `python` dump (`audit_stage1_h.py`) | which source coordinate carries each post-2018 label | all three at 0.00 m; LIT duplicate 495.29 m |
| 11 | `Select-String` on `docs/data_sources.md`, `docs/data_manifest.csv` | confirm other GSI PDFs / GFLD / NASA contain no usable Wayanad records | no Wayanad tabular inventory in 12236/12272/14252/14253/14336/14767/14999/15990 |
| 12 | write `docs/INDEPENDENT_TEST_FEASIBILITY_AUDIT_2026-10-30.md` | the deliverable audit | 10-row candidate table, overlap measurements, readiness conclusion, staged path |
| 13 | write this report | run record | — |

No model was run. No evaluation script was created. No score, ROC-AUC, average precision or rank was
computed for any candidate — computing one would itself have been an in-sample evaluation.

## 2. Measured values (do not re-derive)

All from `data/processed/sampling/` unless stated.

**Training set (the reference frame):**

| Quantity | Value | Source |
|---|---|---|
| Modelling points | **2,460** = 363 positives + 2,097 background | `modelling_points.csv` |
| Distinct positive event groups | 363 (one point per group) | `modelling_points.csv` |
| Distinct clusters (positives) | **76** | `modelling_points.csv` |
| Fold sizes | 471 / 541 / 503 / 473 / 472 | `modelling_points.csv` |
| Positives by year | 2018 **335**, 2007 15, 2009 7, 2006 2, 2024 **2**, 2019 **1**, 2008 1 | `modelling_points.csv` |
| Non-2018 positives | **28 labels / 28 groups / 17 clusters** (matches `PHASE5_PROGRESS.md` §4) | `modelling_points.csv` |
| Test-fold buffer drops | **418** (392 background, 26 positive), all 1,000 m | `fold_drops.csv` |
| Background minimum distance to a positive | 113.7 m | `background_samples.csv` |
| Seed / CRS / grid | 20261026 / EPSG:32643 / 30 m | `sampling_run_config.json` |

**Post-2018 candidates — all three are training points, exactly:**

| Event group | Training point | Fold | Cluster | Nearest positive | Nearest background |
|---|---|---|---|---|---|
| `EV-2024-MUNDAKKAI` | `POS-EV-2024-MUNDAKKAI` | 3 | 13 | **0.00 m** | 208.0 m |
| `EV-2024-MEENAKSHI-BRIDGE` | `POS-EV-2024-MEENAKSHI-BRIDGE` | 3 | 14 | **0.00 m** | 141.4 m |
| `EV-2019-PUTHUMALA` | `POS-EV-2019-PUTHUMALA` | 3 | 75 | **0.00 m** | 160.5 m |

- `EV-2024-MUNDAKKAI` label coordinate = GSI datasheet 11.462778 / 76.134167 (0.00 m match).
- The independent Sreekumar et al. (2025) 2024 record is **495.29 m** away and merged as
  `POSITIVE_EVENT_DUPLICATE` — not an extra test case (`2024_corroboration.json`).
- No candidate group is absent from training.

**Never-labelled pools — distance to nearest training positive (EPSG:32643):**

| Pool | n | min | median | max | ≤100 m | ≤1 km |
|---|---|---|---|---|---|---|
| Undated site records | 78 | 0 m | 434 m | 16,579 m | **16** | **58** |
| Pre-2000 dated (GSI14115) | 6 | 220 m | 551 m | 1,833 m | 0 | **5** |
| Boundary-uncertain | 5 | 288 m | 1,321 m | 5,829 m | 0 | 1 |
| Outside district | 12 | 5,534 m | 20,908 m | 46,582 m | 0 | 0 |

**Undated pool composition and duplication:**

- 78 records: `GSI14768` 41, `GSI14337` 35, `GSI14115` 2; precision 43 A (≤100 m) / 35 C (300–800 m);
  0 with a date; 28 spatial clusters at 1 km single linkage.
- After excluding everything within 1 km of a training positive: **20 records in 10 clusters** (17
  precise, 3 coarse) — still undated and still the same two compilations.
- `duplicate_crosswalk.csv`: **35/35 `GSI14337` records link to a `GSI14115` record**; of those
  partners **26 are training positives**, 7 pre-2000, 2 undated. Link distances 126.6 m – 16,579 m.
- `GSI14768`: 46 records = 41 undated + 5 outside district; no crosswalk rows; 16/41 within 100 m and
  24/41 within 1 km of a training positive.

**Unusable candidates (already documented, reused not re-measured):**

- NASA GLC (`INV-04`): 9 records, 1997–2016, 1–50 km reported accuracy; 0 usable in district
  (7 outside, 1 district centroid, 1 needs widening).
- GFLD (`INV-12`): supplementary summary tables only; **0 event records** redistributed.
- KSDMA/NDMA/CEMS 2024 documents: 0 coordinate tables (`SOURCE_DISCOVERY_2024_WAYANAD_INVENTORY.md`).
- Other GSI volumes (12236, 12272, 14252, 14253, 14336, 14767, 14999, 15990): no Wayanad tabular
  inventory (`docs/data_sources.md` L135–137, L152).

**Request status:** prepared, **not sent**; no reply; no new dataset. Newest file under `data/raw` is
`data/raw/landslide_susceptibility_reference/Wayanad.zip` (2026-10-28 23:27); newest in `docs/requests/`
is 2026-10-29 21:44.

## 3. Bugs caught and fixes

1. **Schema assumption error.** The first audit script assumed `inventory_source_records.csv` had an
   `event_year` column; it does not (year lives in `eligibility_audit.csv`). Fix: join on
   `(source_id, source_record_id)`. No repo file affected.
2. **Truncated console output.** The first script printed all 384 non-2018 eligibility rows and the
   terminal cut the head off. Fix: narrowed each query to the question being asked (candidate groups,
   distances, counts) instead of dumping tables.
3. **PowerShell native-command noise.** `python` tracebacks surface as `NativeCommandError`; harmless,
   but it masked the real `KeyError` in run 1 of the script. Fix: read the traceback body, not the
   wrapper.
4. **Near-miss in wording (caught before commit).** An early sentence said "every 2000–2026 dated
   record on disk is a label", which is too strong: the 5 boundary-uncertain and 1 coordinate-error
   records are in-window but unusable, not independent. Fixed to "every *usable* 2000–2026 dated event
   record", with the six exceptions named.

No inconsistency was found that required re-running a Phase 2/3/4/5 gate, so none was re-run.

## 4. Verification and gates

| Check | Result |
|---|---|
| Independence by stable ID (`event_group_id` ∈ 363 positives) | 3/3 post-2018 candidate groups present; 0 absent |
| Independence by metric-CRS distance | all 3 candidates **0.00 m** from a training positive |
| Fold membership | all 3 in **fold 3**; none in `fold_drops.csv` (they are training, not held out) |
| Background comparison class | 2,097 points exist; **all** are training labels → not usable as an independent comparison |
| Cluster sufficiency vs configured 5-cluster minimum | 2024: 2 → fails; 2019: 1 → fails; pre-2000: effectively 1 → fails |
| Duplicate handling | 495.29 m LIT duplicate merged, not double-counted |
| Request status | NOT SENT banners intact; no reply file; no new raw data after 2026-10-28 |
| Files modified outside this run's two outputs | **none** (`git status` clean before writing; only the audit doc and this report are new) |
| Phase 2/3/4/5 gates | **not run** — read-only documentation audit, no product touched |
| `git diff --check` | run at staging |

**No evaluator, no score, no metric, no model run.** This is the key verification: the audit is
membership and distance bookkeeping only.

## 5. Outputs produced or changed

| File | Status | Contents |
|---|---|---|
| `docs/INDEPENDENT_TEST_FEASIBILITY_AUDIT_2026-10-30.md` | **new** | 10-row candidate table with verdicts; exact overlap measurements; sufficiency and comparison-class analysis; request status; plain-language readiness conclusion; 3-stage path; guard rails; evidence index |
| `reports/RUN-2026-10-30-01_independent-test-feasibility-audit.md` | **new** | This report |
| `%TEMP%\opencode\audit_stage1_{a..h}.py` | temp only | Audit helpers; **not** in the repo |

No source data, inventory record, label, coordinate, Phase 4 output, Phase 5 output, manifest row or
request file was modified.

## 6. Current project state

- **Phase 5:** unchanged. Fixed Random Forest baseline, 5 spatial folds, per-fold ranking metrics as
  recorded in `docs/PHASE5_PROGRESS.md`. No model, metric, map or output was read for scoring or
  written.
- **Phase 4:** unchanged — 2,460 points, 418 drops, 5 folds.
- **Inventory:** unchanged — 468 source records, 8 sources, 363 labelled positives, 78 undated,
  statuses as recorded.
- **Request package:** unchanged and still **NOT SENT**; placeholders intact.
- **Independent test:** **not possible with local data.** No validation claim exists or was created.
- Commit: `62142aa` (audit + this report; hash pinned in the follow-up commit).

## 7. Next-step handoff (prompt material)

- **Decisions the user must make:**
  1. Whether to accept "no independent test yet" as the faculty-demonstration position, presenting the
     Phase 5 spatially held-out results with their stated limits, and describing the independent test
     as pending data. (Recommended, and the only honest option today.)
  2. Whether to pursue the pending official request (RUN-11/12 package still unsent, placeholders
     unfilled) as the acquisition route for Stage 2.
  3. Whether a *site-level, undated* sensitivity check is worth doing later — 20 undated records >1 km
     from any training positive, 10 clusters — knowing it cannot support an event-level claim and that
     `GSI14337` duplicates training sites. (Recommendation: not as a headline result.)
  4. Whether to correct the Phase 2 `coord_precision_deg` discrepancy for the 2024 PDLS row — still
     open from RUN-12, still not done, still needs a re-baseline decision.
- **What the next step must do / must not do:**
  - Do **not** score the 2024, 2019 or 2006–2009 points; they are training labels. Any number from
    them is in-sample and must never be called validation.
  - Do **not** treat `GSI14337` as independent (35/35 crosswalked; 26 partners are training positives).
  - Do **not** lower the 5-cluster minimum, and do **not** reuse the 2,097 training background points
    as a test comparison class.
  - Do **not** add dates, snap coordinates, or merge records to manufacture independence.
  - Do **not** tune or replace the Random Forest, and do **not** use synthetic events as validation.
  - Stage 2 is **acquisition and validation first**; scoring comes only after a locked protocol.
- **Quick commands:**
  - `python %TEMP%\opencode\audit_stage1_b.py` (training composition, candidate groups, distances)
  - `python %TEMP%\opencode\audit_stage1_g.py` (`GSI14337` crosswalk accounting)
  - `python -c "import csv;print(len(list(csv.DictReader(open('data/processed/sampling/modelling_points.csv',encoding='utf-8')))))"`
  - `git log --oneline -3`, `git status --short`
- **Do not re-derive:** 2,460 points = 363 + 2,097; 76 clusters; folds 471/541/503/473/472; 418 drops
  (392/26); 28 non-2018 positives / 17 clusters; the three post-2018 groups at 0.00 m in fold 3
  (clusters 13, 14, 75); 495.29 m duplicate; undated 78 with 16 ≤100 m / 58 ≤1 km; pre-2000 6 with 5
  ≤1 km; `GSI14337` 35/35 crosswalked with 26 training positives; >1 km undated subset = 20 records /
  10 clusters; NASA GLC 0 usable; GFLD 0 event records; request NOT SENT with no reply.
