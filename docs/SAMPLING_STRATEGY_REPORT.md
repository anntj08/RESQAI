# RESQAI — Phase 4: Sampling Strategy Report

**Phase:** 4 (sampling and validation design). **Status:** executed and verified; no model exists.
**Config authority:** `configs/p4_sampling.json`; resolved values + config sha256 recorded in
`data/processed/sampling/sampling_run_config.json`.
**Scope of every claim below:** design of the *sampling*; nothing is trained, scored or mapped.
Susceptibility output, when it eventually exists, is **not a forecast**, warning or timing
prediction (see `MODELLING_TARGET_DECISIONS.md`, L1–L4).

---

## 1. Why presence-background and not a two-class problem (decision S1)

A two-class model needs confirmed absences. No dataset tells us *where landsliding did not
happen*: absence of a record in an inventory is absence of *mapping*, not absence of
*landslides*. Fabricating negatives would invent evidence; the design refuses this.

The adopted design is **presence-background (case-control)**:

* **Positives (363):** audited event points, one per `event_group_id`, from
  `data/processed/sampling/eligibility_audit.csv`.
* **Background (2,097):** sampled locations that carry the meaning **"no mapped landslide
  here"** — and *only* that meaning. A background point is **not confirmed stable ground**, is
  not a negative in any evidential sense, and must never be presented as one.
* **No synthetic labels, no synthetic predictors, no fabricated negatives.** Every point in the
  design is either a recorded event coordinate or a district grid cell that passed the
  separation rule below.

Consequence for Phase 5: models are evaluated as **ranking** tools; likelihood ratios,
probabilities or "probability of landslide" surfaces are not claimable from this label
structure.

## 2. The eligible domain (decision S2): 100 m exclusion, measured exactly

**Separation rule (the part that was re-implemented once and re-measured):** a background
sample may not lie within **100 m** of a *recorded positive coordinate* — the coordinate itself,
not the 30 m grid cell that contains it. The recorded positives sit up to **20.46 m** away from
their own cell centres (cell half-diagonal 21.21 m), so a naive "distance from positive cells"
filter under-protects a band of cells around each event.

Measured on the executed run (`sampling_run_config.json`, `separation`):

| Quantity | Value |
|---|---|
| District cells (30 m grid) | 2,356,538 = 2,120.88 km² |
| Cells with ≥1 invalid predictor layer | 13,195 (removed from the domain) |
| Max positive-to-own-cell-centre offset | 20.46 m (half-diagonal bound 21.21 m) |
| Conservative raster margin applied | 120.5 m = 100 m + max offset + cell diagonal |
| Band cells kept by the exact test | 3,348 of 3,783 (435 rejected by the exact test) |
| **Eligible cells** | **2,330,499 = 2,097.45 km² = 98.895 % of the district** |
| **Exact minimum background-to-positive distance after sampling** | **113.7 m ≥ 100 m** |

The two-step procedure (conservative raster mask, then exact cKDTree re-admission of the band)
is the honest version: the raster step is fast and errs on the safe side; the exact step
reclaims the cells the raster step wrongly excluded, so the reported domain matches the rule
actually enforced. The nearest background point to any recorded positive is 113.7 m — the rule
is *satisfied with margin*, not merely on average.

## 3. Density (decision S3): 1.0 background per km², uniform

* **1.0/km² over the eligible domain → 2,097 samples → 5.78 background points per positive.**
* **Uniform**, not ratio-matched to positives and not land-cover-stratified. Rationale: the
  background is the sampling frame for the ranking; stratifying it by land cover would change
  the frame the model sees and re-weight regions by design choice rather than by evidence.
  Density sensitivity: 0.5/km² → 1,049 samples (2.89/positive); 2.0/km² → 4,195 (11.56/positive)
  — recorded in `data/interim/p4/sensitivity.json` §density.
* Samples are unique 30 m cell centres (`row`,`col` unique, checked); positions stored both as
  EPSG:32643 metric (`x_32643`,`y_32643`) and EPSG:4326 storage columns.

## 4. Randomness, seeds and the config authority (decision S4)

* One seed governs the whole design: **`random_seed = 20261026`** in `configs/p4_sampling.json`.
* Every script reads the config and writes the resolved values into its own outputs; the
  sampler additionally records the **sha256 of the config file** (`72d41377…e6f7a`) at run time,
  so an output can always be tied to the exact design that produced it.
* Because the seed is fixed and stored, re-running `python scripts/p4_sample_background.py`
  reproduces the identical 2,097 points — verified byte-for-byte by
  `scripts/p4_verify.py` (gate 8, regeneration + re-hash of all nine outputs).
* Changing any parameter is done **only** in `configs/p4_sampling.json`; after any edit, the
  sampler and fold scripts must be re-run before `p4_verify.py`, so gate 8's byte-comparison
  stabilises on the new design (the run-config embeds the config hash for exactly this reason).

## 5. Sensitivity of the two sampling choices

From `scripts/p4_sensitivity.py` (§1 uses the same exact-separation rule as the sampler, so its
radius row at 100 m reproduces the executed domain exactly):

| Exclusion radius | Eligible area | % of district | Background @1.0/km² |
|---:|---:|---:|---:|
| 50 m | 2,105.93 km² | 99.30 % | 2,106 |
| **100 m (chosen)** | **2,097.45 km²** | **98.895 %** | **2,097** |
| 200 m | 2,070.10 km² | 97.61 % | 2,070 |
| 300 m | 2,030.22 km² | 95.72 % | 2,030 |

Reading: the exclusion choice costs 0.70–4.28 % of the district; the chosen 100 m is 3.3× the
maximum measured label uncertainty (30 m), so even a worst-case positional error of a recorded
positive cannot place it inside an accepted background sample. Density 0.5×/1×/2× changes the
background count proportionally (1,049 / 2,097 / 4,195) and nothing else in the design.

## 6. What the background sample is not (standing disclaimers)

1. Not evidence of stability: background means *no mapped landslide here in this inventory*.
2. Not a balanced class: 5.78 background per positive is a sampling choice, not a class prior.
3. Not independent labels: background points sample a continuous terrain field; their
   neighbours are correlated by geography (this is exactly why the validation folds are
   spatially blocked — see `SPATIAL_VALIDATION_REPORT.md`).
4. Not a substitute for field negative surveys; if the project later acquires confirmed-stable
   ground truth, the label structure can be revisited as a written estimand change.

## 7. Confirmed facts vs assumptions

**Confirmed (measured):** eligible domain 2,097.45 km² / 98.895 %; 13,195 invalid-predictor
cells; max offset 20.46 m; band 3,348 kept / 435 rejected; 2,097 unique samples; 5.78 per
positive; exact minimum separation 113.7 m; seed 20261026; config sha256 matches the file on
disk.

**Assumptions (judgements, rationale recorded in config):** 100 m radius (3.3× worst label
uncertainty; ~0.5 % area cost vs 50 m); 1.0/km² density (~5.8 contrasts per label, standard for
case-control designs); uniform frame over a stratum-free domain; 30 m cell centres as the only
allowed sample positions (so every point sits on the common predictor grid).
