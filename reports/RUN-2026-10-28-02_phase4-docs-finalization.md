# Run Report RUN-2026-10-28-02 — Phase 4 documentation finalised after independent review

**Date:** 2026-10-28 · **Session goal:** review the Phase 4 sources of truth and outputs,
confirm the 8/8 gate conclusion against them, finalise `docs/PHASE4_PROGRESS.md`.
**Starting state:** commit `821e256` (run-report convention in place); Phase 4 work committed
at `554702c`; tree clean.
**End state:** commit **`889da2c`**, tree clean, all suites green, nothing pushed.

## 1. What was run, in order

| # | Action | Purpose | Result |
|---|---|---|---|
| 1 | read `AGENTS.md` | current instructions | no-modelling rule, run-report convention, style rules confirmed |
| 2 | read `configs/p4_sampling.json` | design authority review | all parameters + rationale as documented; sha `72d41377…e6f7a` |
| 3 | read `data/interim/p4/verify_p4.json` | the 8/8 claim under review | verdict "ALL PHASE 4 GATES PASSED", 8/8, all details consistent |
| 4 | read `data/interim/p4/sensitivity.json` + list `data/processed/sampling/` | output review | 9 outputs present; all sensitivity values match prior docs |
| 5 | read all five Phase 4 scripts (`p4_eligibility.py`, `p4_sample_background.py`, `p4_spatial_folds.py` (header + buffer/leakage sections), `p4_verify.py` (gates 6–8), `p4_sensitivity.py`) | confirm scripts implement what docs claim | consistent; no discrepancy found |
| 6 | `python scripts/p4_verify.py` | **independent confirmation of the 8/8 conclusion** | **8/8 gates PASS**, exit 0 (details §4) |
| 7 | `python scripts/p4_check_consistency.py` + p3 + p2 checkers | doc-vs-data + regression | 116/116 · 470/470 · p2 all pass |
| 8 | rewrote `docs/PHASE4_PROGRESS.md` | requested finalised structure (§8 sections) | done; one banned-vocab trip fixed (§3) |
| 9 | re-run consistency + `git diff --check` | closing verification | 116/116, exit 0 |
| 10 | commit doc (+ p3 verify_all timing churn) | capture | `889da2c` |

## 2. Measured values (do not re-derive)

Unchanged from RUN-2026-10-28-01 (§2 there has the full list with citations). Key confirmations
this run: verification gate 5 recomputed **113.7 m** minimum background-to-positive distance
from the saved coordinates (radius 100 m); gate 6 recomputed **0 mixed-fold blocks** with all
363 event groups / 76 clusters / 271 blocks in exactly one fold; gate 7 recomputed support
**[52, 121, 84, 54, 52]** (all ≥ 45 positives, ≥ 5 clusters; fold 2 = 5 clusters) and the
retained train→test gap **1,001.3 m > 1,000 m** from `fold_assignments.csv` + `fold_drops.csv`
paired by `point_id`; gate 8 regenerated all 9 outputs **byte-identical**.

## 3. Bugs caught and fixes

| # | Where | What | Fix |
|---|---|---|---|
| 1 | `docs/PHASE4_PROGRESS.md` §1 | sentence "Out of scope: any model, any accuracy/AUC/F1-style figure…" listed the banned terms without an in-sentence negation → failed the sentence-level banned-vocabulary tripwire (by design: the doc must carry the negation literally) | reworded to "this phase produces no model, no accuracy/AUC/F1-style figure, no susceptibility surface, and no synthetic event generation." |

No other failures. **No concrete inconsistency was found between scripts, config and saved
outputs; no sampling code, configuration or generated output was changed** (the only repo
change besides the doc was `data/interim/p3/verify_all.json` timing fields, the known churn
from p3_verify_all running inside verification gate 1).

## 4. Verification and gates

| Suite | Result |
|---|---|
| `p4_verify.py` (re-run this session) | **8/8 PASS** — incl. Phase 3 baseline 6/6, 113.7 m separation, leakage recomputation from saved assignments, buffer 1,001.3 m, byte-identical regeneration |
| `p4_check_consistency.py` | **116/116 PASS** (incl. the rewritten progress doc) |
| `p3_check_consistency.py` / `p2_check_consistency.py` | **470/470** / all pass |
| `git diff --check` | exit 0 |

## 5. Outputs produced or changed

* `docs/PHASE4_PROGRESS.md` — rewritten to the finalised structure: purpose/scope · confirmed
  design parameters + rationale · output-file inventory (what each of the 9 products is for) ·
  verification results (8/8, with the 113.7 m and fold-check records) · sensitivity findings
  with sample counts · limitations (incl. the weak temporal holdout: 28 non-2018 labels across
  17 clusters) · interpretation/recommendations kept separate · status + next permitted step ·
  condensed stage chronology pointing to the run report.
* `data/interim/p3/verify_all.json` — timing churn only.
* This report.

## 6. Current project state

Phase 4 sampling and validation preparation is finalised and verified (8/8 gates + 116 doc-vs-data
checks on committed outputs). The checks support exactly that claim and no more: the design is
verified; no model, training table, synthetic event, susceptibility map or performance metric
exists. Phase 3 baseline `570af94` products untouched. Chain: `889da2c` ← `821e256` ← `554702c`
← `570af94`.

## 7. Next-step handoff (prompt material)

* **Decision the user must make:** authorise Phase 5 (modelling) or not — per `AGENTS.md` no
  modelling may start until the user explicitly moves the project to the modelling phase.
* **If authorised, the Phase 5 prompt should carry:** train only on the committed folds;
  per-fold reporting with fold 2 flagged marginal (5 clusters); label every surface
  *conditional on the observed inventory (92.3 % 2018)* — a ranking, never a probability and
  never a forecast/warning/timing statement; attach limitations L1–L4 and §6 of
  `docs/PHASE4_PROGRESS.md`; EPSG:32643 for geometry; never interpolate categorical rasters;
  mask CHIRPS −9999 nodata; un-scale SoilGrids integers.
* **Quick commands:** `python scripts/p4_verify.py` (8 gates) ·
  `python scripts/p4_check_consistency.py` (116) · p2/p3 checkers · `git log --oneline -4`.
* **Do not re-derive (quote as-is):** 2,097.45 km² / 98.895 % · 2,097 background · 5.78 per
  positive · 113.7 m · 76 clusters / 241 units / 271 blocks / 0 mixed · [52, 121, 84, 54, 52],
  spread 69 · chosen seed 20261028 · gap 1,001.3 m · drops 418 (392 bg + 26 pos rows, 395
  unique) · k=10 fails · temporal holdout not viable (28 labels / 17 clusters / min NN 82.4 m)
  · 92.3 % 2018.
