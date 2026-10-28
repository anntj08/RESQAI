# RESQAI — Phase 4 Progress Report

**Phase:** 4 — modelling-target definition, sampling design, inventory eligibility, and
leakage-resistant spatial validation.
**Base commit:** `570af94` (Phase 3 complete and verified). **Finalised:** 2026-10-28.
**Config authority:** `configs/p4_sampling.json` (sha256 `72d41377…e6f7a`, embedded in
`data/processed/sampling/sampling_run_config.json`).
**Standing rule:** this phase contains **no model**. No model, training table, synthetic
event, susceptibility map or performance metric exists in the repository as of this run, and
none may be produced until the user explicitly moves the project to the modelling phase.
Susceptibility mapping estimates *where* terrain and environmental conditions favour failure;
it is never a statement about when a landslide will occur and must never be read as a forecast,
warning, or timing prediction.

Sections 2–5 record **confirmed results** (measured on saved files, re-checked by independent
recomputation). Section 6 separates **limitations of the design** from them. Section 7 holds
**interpretation and recommendations only**. Section 8 states the current status and the next
permitted step.

---

## 1. Purpose and scope

Phase 4 prepares — and only prepares — everything a future modelling phase needs, without
modelling:

1. **Target definition** (`docs/MODELLING_TARGET_DECISIONS.md`): the estimand the evidence
   supports is susceptibility *conditional on the observed inventory* — a ranking, not a
   probability. What a positive label is (one audited event point per `event_group_id`) and
   what background is not (not confirmed stable ground).
2. **Inventory eligibility** (`scripts/p4_eligibility.py`): an audited, additive partition of
   all 468 Phase 3 records into 9 decision classes, changing no Phase 2 verification decision
   and no coordinate.
3. **Background sampling** (`scripts/p4_sample_background.py`): presence-background design with
   an exclusion radius enforced against recorded positive coordinates.
4. **Spatial validation** (`scripts/p4_spatial_folds.py`): whole-block fold assignment with
   cluster atomicity and a verified distance buffer.
5. **Sensitivity** (`scripts/p4_sensitivity.py`): measured effect of each design judgement.

Out of scope: this phase produces no model, no accuracy/AUC/F1-style figure, no susceptibility
surface, and no synthetic event generation.

## 2. Design as configured (confirmed from `configs/p4_sampling.json` and the outputs)

| Parameter | Value | Rationale (recorded in the config) |
|---|---|---|
| Random seed | 20261026 | one seed governs eligibility→sampling→folds; stored in every output |
| Analysis / storage CRS | EPSG:32643 / EPSG:4326 | metric CRS for geometry; geographic for storage |
| Label unit | one point per `event_group_id` | 364 usable records describe 363 distinct landslides |
| Label window | 2000–2026 | matches Phase 2/3 inventory coverage |
| Background exclusion radius | 100 m | 3.3× the largest measured label uncertainty (30 m) |
| Background density | 1.0 per km², uniform | count follows area, not positive count; no implied class balance |
| Block size | 3,000 m | above the 1 km clustering scale; blocks contain whole clusters |
| Clustering threshold | 1,000 m single linkage | 363 positives → 76 clusters; one neighbourhood scale |
| Buffer gap | 1,000 m | same distance doubles as the cluster scale; removes training points from each test fold's neighbourhood |
| Folds (k) | 5 | ~70 test positives per fold; k=10 fails support (measured, §5) |
| Support minimums | 45 test positives, 5 test clusters | a fold needs several independent locations to be evaluable |
| Fold assignment | 12 deterministic candidates (seeds 20261026–20261037), weighted k-means on block-unit centroids + hill-climb; best end state wins, ties at lowest candidate | keeps the assignment a deterministic function of (data, config) |

**How the design fits together (five steps):** positives are clustered at 1,000 m (76
clusters, atomic); the district is tiled into whole 3 km blocks (271 blocks contain points);
blocks sharing a cluster merge into 241 units; whole units are assigned to folds; then every
training point within 1,000 m of any test point is dropped from that fold's training set, with
each drop recorded in `fold_drops.csv`.

**Confirmed headline results:**

* Eligibility: **468 records → 363 POSITIVE_EVENT** (one per event group) + 1 in-group
  duplicate + 103 exclusions, each with exactly one recorded reason; the three separately
  validated records (`KER/WYD/58A03/2024/01`, `14115/p141/row17`, `14115/p140/row15`) remain
  distinct with their Phase 2 statuses unchanged.
* Positives by year: 2006:2, 2007:15, 2008:1, 2009:7, **2018:335**, 2019:1, 2024:2 —
  **92.3 % single-year**; positional uncertainty 10/30/30 m (min/median/max).
* Background: eligible domain **2,330,499 cells = 2,097.45 km² = 98.895 %** of the
  2,120.88 km² district (13,195 invalid-predictor cells removed); **2,097 samples** at
  1.0/km² = **5.78 per positive**; separation measured against recorded coordinates
  (max offset 20.46 m; 3,348 band cells kept, 435 rejected by the exact test);
  **the nearest background point is 113.7 m from a positive** under the configured 100 m
  exclusion radius — re-measured independently from the saved files by verification gate 5.
* Folds: **[52, 121, 84, 54, 52]** positives (spread 69, the structural floor set by the
  atomic 121-positive unit); chosen candidate seed 20261028; **0 mixed-fold 3 km blocks**;
  **418 training points dropped** by the buffer (392 background + 26 positive rows, 395 unique
  points), each with fold, distance and reason.

## 3. Generated output files and what each is for

All in `data/processed/sampling/` (committed, ~600 KB text):

| File | What it is for |
|---|---|
| `eligibility_audit.csv` | record-level authority: all 468 records with `p4_use`, `p4_flags`, `p4_reason`, `is_group_representative` |
| `eligibility_summary.json` | decision counts, positives by year/source, uncertainty summary, sha256 of the input |
| `background_samples.csv` | the 2,097 background points (cell-centre coordinates in EPSG:32643 and EPSG:4326, distance to nearest positive) |
| `sampling_run_config.json` | resolved parameters, seed, separation measurements, config sha256 — ties every output to the exact design |
| `spatial_blocks.csv` | 271 blocks → unit → fold, with per-block point composition |
| `fold_assignments.csv` | all 2,460 analysis points with cluster, block and fold — the leakage-control authority |
| `fold_drops.csv` | the 418 buffer drops with per-point distance and reason |
| `modelling_points.csv` | the candidate positive/background table a future modelling phase trains on |
| `fold_summary.json` | per-fold support, buffer losses, leakage invariants, assignment provenance |

Scripts (all re-runnable, all read the config): `scripts/p4_eligibility.py`,
`p4_sample_background.py`, `p4_spatial_folds.py`, `p4_sensitivity.py`, `p4_verify.py`,
`p4_check_consistency.py`. Diagnostics: `data/interim/p4/` (sensitivity.json, verify_p4.json,
exploration scripts). Manifest rows **P4-01…P4-06** added; `docs/data_manifest.csv` now has
**43 datasets**. Companion decision documents: `docs/MODELLING_TARGET_DECISIONS.md`,
`docs/SAMPLING_STRATEGY_REPORT.md`, `docs/SPATIAL_VALIDATION_REPORT.md`.

## 4. Verification results (confirmed)

`scripts/p4_verify.py` reports **8 / 8 gates pass — ALL PHASE 4 GATES PASSED**, re-confirmed
on 2026-10-28 by an independent re-run against the saved outputs:

| Gate | Confirmed result |
|---|---|
| 1. Phase 3 baseline | `p3_verify_all.py` 6/6 gates; `570af94` products untouched |
| 2. Eligibility completeness | 468 records, 9 decision classes, one reason each |
| 3. Three special records | A/B/C distinct with Phase 2 statuses intact |
| 4. Point integrity | 2,460 points (363 positives / 2,097 background); all 24 predictor layers valid at every point; all inside the district |
| 5. Background separation | closest background point **113.7 m** from a recorded positive (≥ 100 m configured), recomputed from the saved coordinates |
| 6. Leakage | **363 event groups, 76 clusters and 271 blocks each lie in exactly one fold; 0 mixed-fold blocks** — recomputed from the saved `fold_assignments.csv` |
| 7. Support + buffer | every fold ≥ 45 positives and ≥ 5 clusters; the 418 saved drops match a from-scratch recomputation (point sets **and** distances, paired by `point_id`); retained train→test minimum gap **recomputed independently at 1,001.3 m > 1,000 m** configured |
| 8. Reproducibility | the 3 scripts re-run and all **9 outputs are byte-identical** |

Doc-vs-data layer: `scripts/p4_check_consistency.py` **116/116 checks pass** (config sha vs
run-config, audit partition, fold invariants recomputed by point_id, documentation needles
formatted from the JSONs, required disclaimers, sentence-level banned-vocabulary check).
Phase 3 consistency: **470 / 470**; Phase 2: all pass. `git diff --check`: clean.

## 5. Sensitivity findings (confirmed measurements; nothing retrained)

From `scripts/p4_sensitivity.py` → `data/interim/p4/sensitivity.json`. Sample counts shown per
variant:

* **Exclusion radius** 50 / 100 / 200 / 300 m → eligible **2,105.93 / 2,097.45 / 2,070.10 /
  2,030.22 km²** (99.30 / 98.895 / 97.61 / 95.72 % of district); background at 1.0/km² =
  **2,106 / 2,097 / 2,070 / 2,030**. The 100 m row reproduces the executed domain exactly.
* **Density** 0.5 / 1.0 / 2.0 per km² → **1,049 / 2,097 / 4,195 samples** (2.89 / 5.78 / 11.56
  per positive).
* **Clustering distance** 500 / 1,000 / 2,000 m → **186 / 76 / 26** clusters; 2,000 m **fails
  both support minimums** (min fold 28 positives, 1 cluster/fold).
* **Buffer gap** 0 / 500 / 1,000 / 2,000 m → closest cross-fold pair 150.0 / 510.0 /
  1,001.3 / 2,001.2 m; drops 0 / 69 / 418 / 1,399 (positives dropped 0 / 5 / 26 / 140). At
  gap 0, folds touch at 150 m — the random-split failure mode made measurable.
* **Fold count** k=3 → [121,121,121], min 14 clusters; k=5 → min 7 clusters (meets); **k=10
  fails** (fold positives 12–34 < 45).
* **Inclusion rule** primary → +undated → +undated+pre-2000: **363 → 401 → 407 points**
  (76 → 81 clusters); including undated records would not collapse the folds, but stays
  excluded because the label window requires dates.
* **Temporal holdout**: train on 2018 (335 points) and test on the **28 non-2018 labels
  across 17 clusters** is technically possible but very weak (closest non-2018 neighbour
  82.4 m from the 2018 mass — temporal separation is not spatial separation); the reverse
  direction is not viable and was not attempted.

Documented harness caveat: the sensitivity helper assigns folds without background blocks, so
its k=5 arrangement is [86, 121, 52, 52, 52] (min 7 clusters/fold) whereas production is
[52, 121, 84, 54, 52]; both meet support; conclusions unchanged.

## 6. Limitations (of the design; confirmed)

1. **Weak temporal holdout.** The 28 non-2018 positives span 6 years in 17 clusters — too few
   locations to evaluate temporal transfer. No viable temporal holdout exists in this data and
   none is invented; spatial folds are the only supported validation.
2. **92.3 % single-year inventory.** The estimand is susceptibility conditional on the
   observed inventory; it is not unbiased and not fully representative of other years' event
   populations (see `docs/MODELLING_TARGET_DECISIONS.md`, L1–L4).
3. **Ranking, not probability.** Presence-background labels support relative favourability
   only.
4. **Background is not confirmed absence.** A background point means no mapped landslide in
   the available inventory — never stable ground.
5. **Spatial independence is not asserted.** The buffer removes training points from the
   immediate neighbourhood of each test fold; folds still share terrain, land cover and
   rainfall history, and per-fold results will remain correlated to an unmeasured degree.
6. **Fold 2 is marginal.** 84 positives but only 5 distinct clusters — it meets the configured
   minimum exactly and must be flagged whenever used.
7. **Unequal folds are structural.** The 121-positive unit cannot be split without breaking
   cluster atomicity; spread 69 is the measured floor across 12 seeds.
8. **Known source limits carried from Phase 2/3:** GLiM geology at 1:3.75 M (GSI 1:50,000
   missing), no inventory record of the July 2024 Wayanad event, ~1.1 km uncertainty on
   35/89 legacy inventory records (carried per record).

## 7. Interpretation and recommendations (not confirmed results)

* The verified gap (1,001.3 m) and block atomicity make the folds a sound basis for a future
  evaluation, *provided* its results are read per fold and fold 2 is flagged.
* If the project later acquires confirmed-stable ground truth or a multi-year inventory, the
  label structure and the temporal story should be revisited as a written estimand change —
  not by rebalancing silently.
* Recommendation for any future modelling phase: train only on these folds, label every
  surface *conditional on the observed inventory*, and keep the general-susceptibility aim
  long-term rather than claimable.

## 8. Current project status and next permitted step

**Status:** Phase 4 sampling and validation preparation is **finalised and verified** — 8/8
verification gates and 116 doc-vs-data checks pass on the committed outputs; `570af94`
(Phase 3) products are untouched. The checks support exactly this claim and no more: the
*design* is verified; nothing downstream of it exists.

**Next permitted step (per `AGENTS.md`):** no modelling of any kind may start until the user
explicitly moves the project to the modelling phase. Until that decision, permitted work is
review, documentation, and data preparation only. If and when Phase 5 is authorised, it must
train on the committed folds only, report per-fold results with fold 2 flagged, and attach the
limitations in §6 and L1–L4.

**Stage history (chronology, condensed):** design config → eligibility audit → background
sampling (exact-separation re-implementation after the raster-only rule under-protected a
band) → fold redesign to block units (per-block k-means split clusters; units fix it) →
12-candidate deterministic sweep (seed 20261028 reaches the spread-69 floor) → verifier
rewrite with independent recomputation (row-order drop pairing caught and fixed to
`point_id`) → sensitivity rewrite (§1 made to reproduce the exact-separation rule) →
documentation, manifest rows P4-01…P4-06, `.gitignore` sampling negation, doc-vs-data
checker, commit `554702c`. Full detail: `reports/RUN-2026-10-28-01_phase4-completion.md`.
