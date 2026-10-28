# RESQAI — Phase 4 Progress Log

**Scope:** modelling target, sampling design, inventory eligibility, leakage-resistant spatial
validation.
**Started:** 2026-10-26 (design). **Executed:** 2026-10-28. **Base commit:** `570af94`
(Phase 3 complete and verified).
**Rule:** append-only checkpoint log. Nothing in this phase trains a model, builds a training
table, fits parameters or reports a performance metric. Susceptibility output is never a
forecast, warning or timing prediction.

Every script is re-runnable from the repo root and reads its design from
`configs/p4_sampling.json`. Raw data and Phase 2/3 products are untouched.

---

## Stage 1 — Design config as single source of truth — DONE

- [x] `configs/p4_sampling.json`: analysis/storage CRS (EPSG:32643 / EPSG:4326), grid inputs,
      seed 20261026, background exclusion radius 100 m and density 1.0/km², spatial-validation
      block size 3,000 m, buffer gap 1,000 m, clustering threshold 1,000 m, k=5, support
      minimums 45 positives / 5 clusters — every value with a recorded rationale.
- [x] Decision that every script reads the config and embeds resolved values (sampler embeds
      the config sha256) in its own outputs, so an output is always traceable to the design
      that produced it.

## Stage 2 — Inventory eligibility audit — DONE

- [x] `scripts/p4_eligibility.py` partitions all **468** Phase 3 records into 9 decision
      classes with one reason each: 363 `POSITIVE_EVENT` (one per event group), 1 in-group
      duplicate, 5 boundary-uncertain, 78 undated, 12 not-in-district, 6 pre-2000,
      1 widen-required, 1 district-centroid, 1 coordinate-error; `EXCLUDE_SUPERSEDED` is 0 by
      construction (33 superseded flags ride on records decided by higher-precedence rules and
      are carried in `p4_flags`).
- [x] Positives by year: 2006:2, 2007:15, 2008:1, 2009:7, **2018:335**, 2019:1, 2024:2 —
      92.3 % single-year, handled as an estimand limitation (T3), not rebalanced.
- [x] Positive positional uncertainty 10 / 30 / 30 m (min / median / max).
- [x] The three separately validated records stay distinct with their Phase 2 statuses:
      `KER/WYD/58A03/2024/01` positive; `14115/p141/row17` (printed Sl.17) coordinate-error
      exclusion; `14115/p140/row15` (printed Sl.15) boundary-uncertain exclusion.

### Finding that reshaped the target

The stated aim "general susceptibility" is **not claimable** from this evidence: 92 % of the
labels come from one event year, so the supportable estimand is susceptibility *conditional on
the observed inventory* — a ranking, not a probability, and not unbiased. Decision recorded in
`docs/MODELLING_TARGET_DECISIONS.md` (T1, L1–L4) before any modelling, so the limitation is part
of the target definition rather than a post-hoc caveat.

## Stage 3 — Background sampling with exact separation — DONE

- [x] `scripts/p4_sample_background.py`: 100 m exclusion measured against **recorded positive
      coordinates**, not their grid cells.
- [x] Conservative raster mask (120.5 m margin = 100 m + max offset 20.46 m + cell half
      diagonal) plus exact cKDTree re-admission of the band: 3,348 band cells kept, **435
      rejected by the exact test** — cells a naive raster filter would have wrongly excluded.
- [x] Eligible domain **2,330,499 cells = 2,097.45 km² = 98.895 %** of the 2,120.88 km²
      district (13,195 invalid-predictor cells removed); **2,097 samples** at 1.0/km² =
      5.78 per positive; **exact minimum separation 113.7 m ≥ 100 m**; seed 20261026 recorded
      with the config sha256.

### Finding that forced a re-measurement

The first implementation masked on distance-to-positive-*cells*; because recorded positives sit
up to 20.46 m from their own cell centres, that rule under-protected a band around each event.
The separation rule was re-specified against recorded coordinates, the sampler was rewritten
(conservative mask + exact band re-admission), and the eligible domain shrank from 2,097.84 km²
to **2,097.45 km²** with the exact minimum separation verified at 113.7 m. The sensitivity
harness §1 was re-written to reproduce the same exact rule per radius, so its 100 m row
reproduces the executed domain.

## Stage 4 — Spatial folds, block-unit design — DONE

- [x] `scripts/p4_spatial_folds.py`: single-linkage 1 km clusters (76) → whole 3 km blocks
      (271 with points) → units where blocks share a cluster (241) → 5 folds by deterministic
      **12-candidate** weighted-k-means sweep + hill-climb on (support deficit, cluster
      deficit, positive spread, background spread), ties at the lowest candidate → **1,000 m
      buffer** with per-point drop audit.
- [x] Chosen candidate seed **20261028**, score [0, 0, 69, 1]; fold positives
      **[52, 121, 84, 54, 52]** (spread 69 — the measured floor, set by the atomic 121-positive
      unit); **0 mixed-fold 3 km blocks**; retained minimum train→test gap **1,001.3 m**.
- [x] `fold_drops.csv`: **418** drops (392 background, 26 positive rows, 395 unique points)
      with per-point fold, distance and reason; positives are dropped only near *neighbouring
      folds' background*, never near test positives (same-neighbourhood pairs are one cluster
      by construction).
- [x] Fold 2 flagged marginal: 84 positives but **5 distinct clusters** (meets the configured
      minimum exactly).

### Findings from the redesign

1. An earlier per-block k-means split merged clusters across folds; blocks sharing a cluster
   must move as one unit, hence the unit layer. Balance then costs spread (15 → 69), measured
   across 12 seeds and accepted as structural rather than "fixed" by splitting units.
2. The verification gate initially paired `fold_drops.csv` rows by **row order** against its
   recomputation; the file is ordered by the generator's internal point index, not by the saved
   assignment sort. Pairing was corrected to **point_id**, and the mismatch was confirmed to be
   order-only (identical point sets, identical distances).
3. `spatial_blocks.csv` counts per-block point composition; the unit-level `n_pos/n_clu/n_bg`
   are assignment weights only. A first write replicated unit totals into every block row —
   caught by the script's own count assertion and fixed.

## Stage 5 — Sensitivity of the design — DONE

- [x] `scripts/p4_sensitivity.py`, nothing retrained: exclusion radius 50/100/200/300 m →
      2,105.93 / **2,097.45** / 2,070.10 / 2,030.22 km²; density 0.5/1/2 per km² →
      1,049 / 2,097 / 4,195 samples; clustering 500/1000/2000 m → 186 / **76** / 26 clusters
      (2,000 m fails support: min 28 positives, 1 cluster/fold); buffer 0/500/1000/2000 m →
      closest cross-fold pair 150.0 m / 510.0 m / **1,001.3 m** / 2,001.2 m, drops
      0 / 69 / **418** / 1,399; k=3 [121,121,121] min 14 clusters, k=5 min 7, k=10 **fails**
      (12–34 positives); inclusion 363 → 401 → 407 points (76 → 81 clusters); temporal holdout
      not viable (28 non-2018 labels, 17 clusters, min NN 82.4 m; reverse not attempted).
- [x] Documented harness caveat: the sensitivity helper assigns without background blocks, so
      its k=5 arrangement is [86, 121, 52, 52, 52] (min 7 clusters/fold) while production is
      [52, 121, 84, 54, 52]; both meet support, conclusions unchanged.

## Stage 6 — Verification gates — DONE

- [x] `scripts/p4_verify.py`, 8 gates, all PASS:
      1 Phase 3 baseline intact (`p3_verify_all.py`, 6/6); 2 eligibility partition complete;
      3 the three special records distinct; 4 point integrity + all 24 predictor layers valid
      at every point; 5 exact background separation 113.7 m ≥ 100 m; 6 leakage (0 mixed blocks,
      groups/clusters atomic) recomputed from saved assignments; 7 support + buffer with the
      retained gap **independently recomputed by point_id** from
      `fold_assignments.csv` + `fold_drops.csv`; 8 all three scripts re-run, **nine outputs
      byte-identical**.
- [x] Manifest rows **P4-01…P4-06** added in `scripts/build_manifest.py`;
      `docs/data_manifest.csv` regenerated — **43 datasets**, 16 columns.
- [x] `scripts/p3_check_consistency.py` manifest section relaxed from an exact-total assertion
      (=37) to presence+uniqueness of all Phase 2/3 ids, following the Phase 2 checker
      precedent, with the reason documented inline; **470 checks pass**.
- [x] `.gitignore` negation `!data/processed/sampling/**` so the nine ~600 KB provenance
      tables are committed like the other small provenance artefacts; `git check-ignore`
      confirms they are trackable.

## Stage 7 — Documentation and consistency layer — DONE

- [x] `docs/MODELLING_TARGET_DECISIONS.md`, `docs/SAMPLING_STRATEGY_REPORT.md`,
      `docs/SPATIAL_VALIDATION_REPORT.md` (this log) — every number in them traced to a JSON on
      disk and asserted by `scripts/p4_check_consistency.py`.
- [x] `scripts/p4_check_consistency.py`: doc-vs-data assertions (measured counts appear in the
      docs; config sha256 in `sampling_run_config.json` matches `configs/p4_sampling.json`;
      fold invariants 0 mixed blocks / gaps > 1,000 m / support ≥ 45 positives and 5 clusters;
      required disclaimers present; positive-prediction vocabulary absent).

---

## Recovery, verification and reproducibility

All Phase 4 scripts are idempotent and read only the config, Phase 2/3 products and raw data;
they write only under `data/interim/p4/` and `data/processed/sampling/`.

```powershell
# one command, all eight gates
python scripts/p4_verify.py

# individually (design order)
python scripts/p4_eligibility.py        # 468-record audit -> eligibility_audit.csv
python scripts/p4_sample_background.py  # 2,097 background, exact separation
python scripts/p4_spatial_folds.py      # folds, drops, summary
python scripts/p4_sensitivity.py        # parameter sweeps -> sensitivity.json
python scripts/p4_check_consistency.py  # doc-vs-data assertions
python scripts/p2_check_consistency.py  # 68 Phase 2 assertions
python scripts/p3_check_consistency.py  # 470 Phase 3 assertions
python scripts/build_manifest.py        # regenerate docs/data_manifest.csv
```

After **any** edit to `configs/p4_sampling.json`: re-run sampler + fold script, then
`p4_verify.py` (gate 8 byte-compares the outputs, and the run-config embeds the config sha).

### Final measured state

| Check | Result |
|---|---|
| Phase 3 baseline | **6 / 6 gates** still pass (`570af94` products untouched) |
| Eligibility | **468** records → **363** positive event groups, 9 classes, 1 reason each |
| Background | **2,097** samples; eligible **2,097.45 km² (98.895 %)**; exact separation **113.7 m** |
| Folds | **[52, 121, 84, 54, 52]**, spread 69; **0 mixed-fold blocks**; gap **1,001.3 m > 1,000 m**; drops **418** audited |
| Verification | **8 / 8 gates** pass, incl. byte-identical regeneration of 9 outputs |
| Consistency | p4 doc-vs-data suite green; p3 **470 / 470**; p2 **68 / 68** |
| Manifest | **43 datasets**, P4-01…P4-06, all paths exist, all `VERIFIED` |
| `git diff --check` | clean (exit 0) |

**Phase 4 status: complete, with documented limitations.** No model, training table, synthetic
event, susceptibility map or performance metric exists in this phase.

## Gate to Phase 5

Phase 5 (modelling) **does not start** until the project owner explicitly authorises it. When
authorised, it must: train only on these folds; report per-fold results with fold 2 flagged
marginal; label any surface *conditional on the observed inventory*; and attach limitations
L1–L4 from `docs/MODELLING_TARGET_DECISIONS.md`. The folds are leakage-controlled by design and
verified by re-computation — the remaining risks are the ones documented, not hidden ones.

---
