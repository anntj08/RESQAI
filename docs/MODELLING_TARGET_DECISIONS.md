# RESQAI — Phase 4: Modelling Target Decisions

**Phase:** 4 (sampling and validation design). **Status:** decisions recorded; no model exists.
**Config authority:** `configs/p4_sampling.json` (sha256 `72d41377…e6f7a`, embedded in
`data/processed/sampling/sampling_run_config.json`).
**Hard rule carried from `AGENTS.md`:** susceptibility mapping estimates *where* terrain and
environmental conditions favour failure. It does **not** predict *when* a landslide will occur.
Nothing in this document describes, or may be quoted as, a forecast, warning or timing
prediction. No accuracy, AUC, F1 or any performance number exists in this phase.

---

## 1. The stated aim vs the estimand actually supported

The project aim is **general landslide susceptibility** for Wayanad district: a spatial ranking
of where terrain and environmental conditions favour slope failure.

What the evidence actually supports is narrower, and the difference must be carried into every
later phase:

> **Estimand (decision T1):** susceptibility *conditional on the observed inventory* — a ranking
> of terrain favourability relative to the landslide events that were recorded, under the
> sampling described in `SAMPLING_STRATEGY_REPORT.md`.

Consequences of that decision, each of which limits what a Phase 5 result may claim:

| # | Limitation | Why it follows |
|---|---|---|
| L1 | The target is a **ranking, not a probability**. | Labels are presence/background without a valid denominator; a probability of occurrence per pixel would need event rates and exposure, which no inventory here provides. |
| L2 | Not unbiased, **not fully representative** of all future landslides. | The training signal is 92 % single-event-year (335 of 363 positives dated 2018); what is learned is favourability for that observed event population. |
| L3 | Not a forecast, not a warning, and not a statement about *when* anything will move. | Susceptibility is a static spatial construct; the inventory has no usable temporal dimension for prediction (§3). |
| L4 | General susceptibility is the **long-term aim, not a claimable Phase 5 output**. | Achieving it would need temporally distributed inventories over many years; the available data cannot support or test that claim. |

These are **limitations of the target**, recorded before any modelling so they cannot be
retro-fitted as caveats after a result exists.

## 2. The label: what a positive is, and what background is not

Decision T2 — **presence-background (case-control) design**, not a two-class model:

* A **positive** is one mapped landslide *event point*: a record that passed the eligibility
  audit (§4) with `p4_use = POSITIVE_EVENT`, one per `event_group_id` — **363 positives**.
* A **background** point means **no mapped landslide at that location in the available
  inventory**. It is **not confirmed stable ground** and carries no negative-evidence claim.
* There are **no fabricated negatives** and **no synthetic labels or synthetic predictors**
  anywhere in the design.

The 363 positives are the unit of the target; the 2,097 background points (1.0/km²) are the
sampling frame that gives the ranking its contrast. Details, separation rule and density
rationale: `SAMPLING_STRATEGY_REPORT.md`.

## 3. The 2018 dominance, handled explicitly (decision T3)

Confirmed on the audited labels: **335 of 363 positives (92.3 %) are dated 2018**; the remaining
28 spread over 2006:2, 2007:15, 2008:1, 2009:7, 2019:1, 2024:2.

What the design does with this:

* **Nothing is rebalanced or reweighted.** Rebalancing to spread the label across years would
  silently change the estimand (a model calibrated to an artificial year-mix) without buying
  representativeness it cannot prove. Any future rebalancing requires a written estimand change
  first.
* **No viable temporal holdout exists, and none is invented.** Measured
  (`data/interim/p4/sensitivity.json`, §temporal): training on 2018 and testing on the 28
  non-2018 labels is technically possible but very weak (28 labels in 17 clusters, closest
  non-2018 neighbour 82.4 m from a 2018 point — temporal separation is not spatial
  separation). Training on the 28 and testing on 335 is not viable and was **not attempted**.
  The spatial folds in `SPATIAL_VALIDATION_REPORT.md` are therefore the only validation the
  data supports.
* The temporal composition is treated as a **limitation of the estimand** (L2), stated up front,
  with per-year counts preserved in `eligibility_summary.json` so no later phase can misread it.

## 4. Inventory eligibility (decision T4): one audited partition of all 468 records

`scripts/p4_eligibility.py` assigns **exactly one decision and one reason** to every Phase 3
record, without changing any Phase 2 verification outcome, without moving, snapping or
deduplicating coordinates, and without altering the three separately validated records:

| Decision | Records | Meaning |
|---|---:|---|
| `POSITIVE_EVENT` | **363** | in-window (2000–2026) event point label, one per event group |
| `POSITIVE_EVENT_DUPLICATE` | 1 | second record describing the same event group |
| `EXCLUDE_WIDEN_REQUIRED` | 1 | mapped polygon needs a widening review before point use |
| `EXCLUDE_BOUNDARY_UNCERTAIN` | 5 | sits inside the ~750 m GADM/OSM boundary ambiguity band |
| `EXCLUDE_UNDATED_SITE` | 78 | site with no usable date inside the label window |
| `EXCLUDE_PRE_2000` | 6 | dated before the 2000–2026 window |
| `EXCLUDE_NOT_IN_DISTRICT` | 12 | coordinate falls outside the district |
| `EXCLUDE_DISTRICT_CENTROID` | 1 | geocoded to the district centroid, not to the event |
| `EXCLUDE_COORDINATE_ERROR` | 1 | coordinate demonstrably wrong (record B below) |
| `EXCLUDE_SUPERSEDED` | 0 | superseded flags ride on records decided by higher-precedence rules (33 records carry `superseded` in `p4_flags`) |

Confirmed properties of this partition:

* The three records validated separately in Phase 2 remain **distinct** with their Phase 2
  statuses intact: `KER/WYD/58A03/2024/01` (A) is an eligible positive; `14115/p141/row17`
  (printed Sl.17, B) is the coordinate-error exclusion; `14115/p140/row15` (printed Sl.15, C) is
  a boundary-uncertain exclusion. No Phase 2 decision was reversed to grow the sample.
* Positives' positional uncertainty: min 10 m, median 30 m, max 30 m (measured field
  `positional_uncertainty_m`); the 100 m background exclusion radius is 3.3× the 30 m maximum.
* `data/processed/sampling/eligibility_audit.csv` is the record-level authority; per-record
  provenance and precision are preserved so no later phase can silently snap or merge them.

## 5. What this target is not (standing disclaimers)

1. It is **not a forecast** of landslide occurrence in any time window, and not a warning.
2. It is **not a probability**; any Phase 5 output is a relative favourability ranking.
3. It is **not validated for regions or event types absent from the inventory** (e.g. record
   years other than 2018 are represented by 28 points only).
4. It does **not** certify mapped-landslide-free ground: background is absence of *mapping*,
   not absence of *landslides*.
5. No susceptibility map, model, metric or accuracy figure exists yet; producing one requires
   the Phase 5 decision recorded in `PHASE4_PROGRESS.md`.

## 6. Confirmed facts vs assumptions

**Confirmed (measured on the audit and sampling files):** 468 records; 363 positive event
groups; 92.3 % of positives dated 2018; 28 non-2018 positives in 17 clusters; uncertainty
10/30/30 m; every record carries exactly one decision and a reason; the three separately
validated records are distinct and unchanged.

**Assumptions (explicitly judgements, with recorded rationale in the config):** the 2000–2026
label window; one point per event group as the label unit; treating undated and pre-2000
records as excluded-but-available (sensitivity variants, §inclusion in
`SPATIAL_VALIDATION_REPORT.md`); 2018 dominance reflecting reporting effort as much as hazard.

**Recommendation carried forward:** Phase 5, if authorised, must train on the spatial folds
only, report per-fold results, and label any susceptibility surface as *conditional on the
observed inventory* with L1–L4 attached. Phase 5 does **not** start until explicitly authorised.
