# ATTACHMENT 1 — Project note: landslide susceptibility mapping, Wayanad district, Kerala

> **STATUS: DRAFT FOR USER REVIEW — NOT SENT.** This is enclosure 1 of the records request drafted in
> `docs/requests/DRAFT_2026-10-29_official-inventory-request.md`. Nothing here has been sent. Fill
> every `[PLACEHOLDER]` before use. Do not describe the project as operational, early-warning or
> forecasting anywhere in this note: it is a research project on *where* conditions favour failure.

**Prepared for:** `[RECIPIENT — Geological Survey of India / KSDMA / Wayanad DDMA]`
**Date:** `[DATE]` · **Prepared by:** `[NAME]`, `[DESIGNATION]`, `[INSTITUTION / DEPARTMENT]`
**Contact:** `[EMAIL]` · `[PHONE]` · `[POSTAL ADDRESS]`

---

## 1. Purpose

This note describes a research project that maps landslide **susceptibility** in Wayanad district,
Kerala — that is, the relative likelihood that a given slope has conditions favourable to failure,
based on terrain, rainfall, land cover, soil and geology. Susceptibility mapping answers *where*
conditions favour failure. It does not answer *when* a slope will fail, and the project produces no
forecast, warning, alert or timing estimate.

The purpose of the accompanying request is narrower than the project: to establish whether official
site-level records of the July 2024 Wayanad landslides exist beyond the one post-disaster datasheet
already published and held, and, if so, whether they may be used and cited under stated conditions.

## 2. Geographic and thematic scope

| Item | Value |
|---|---|
| District | Wayanad, Kerala (working boundary: GADM 4.1, **2,121.0 km²**, cross-checked against OSM at 2,128.6 km²) |
| Extent | 75.7722–76.4356 E / 11.4427–11.9706 N (the district straddles 76°E) |
| Period | 2000–2026 |
| Inventory | 468 published source records from 8 sources; each record carries its own provenance, verification status and printed coordinate precision |
| Analysis CRS | EPSG:32643 (UTM zone 43N) for slope, distance and area; EPSG:4326 for storage |

The inventory deliberately retains **undated site records** alongside dated events, because "where
terrain has failed" is useful evidence even when the source does not state a date. Records are never
assigned an invented date to make a dataset look complete.

## 3. Intended use of any records received

1. To record what the agency states, with its identifier, page reference, printed coordinate and
   stated precision, as a new source in the inventory — not pasted into existing rows.
2. To test whether additional official site records change the spatial pattern of the susceptibility
   baseline, using the same spatially blocked validation already applied to the existing data.
3. To cite the source in any resulting report, in whatever form the agency requires.

The records would **not** be used for individual-level analysis, insurance or property decisions,
enforcement, or any real-time operational purpose.

## 4. Safeguards the project applies

- **No forecast or warning claim.** The intended output is a susceptibility surface plus spatially
  held-out ranking metrics. It is never presented as a prediction of when or exactly where a
  landslide will occur, and never as an accuracy figure for "all Wayanad landslides".
- **Spatially blocked validation.** Train/test separation is by spatial fold or landslide cluster,
  never a random split, because clustered points inflate apparent performance through spatial
  autocorrelation.
- **Provenance and precision preserved.** Coordinates are stored as printed, with the source's own
  precision recorded; nothing is snapped, rounded or silently corrected. A suspected typographic
  error in a source is flagged, not "fixed".
- **Missing fields stay missing.** Where a source prints no value, the field is recorded as absent.
  "Not recorded" is treated as a result, not as a gap to be filled by inference.
- **No inference from prose or maps.** Landslide locations are taken only from records that state
  coordinates. Narrative descriptions and mapped extents are read as context and are never converted
  into points.
- **Categorical data handled correctly.** Land cover, lithology and soil class are never
  interpolated with bilinear or bicubic resampling.
- **No synthetic events in the baseline.** Any scenario data, if ever produced, is labelled
  synthetic and never evaluated as real.
- **Restricted material respected.** Nothing received under a restriction is redistributed, and no
  access condition is bypassed or worked around.

## 5. What the project does not do

- It does not issue warnings, alerts or evacuation advice, and it is not connected to any operational
  system.
- It does not estimate casualty risk, building damage or economic loss.
- It does not attribute any specific landslide to any specific cause, landowner or activity.
- It does not publish restricted coordinates or redistribute agency data without permission.

## 6. Data handling and citation

Any material provided will be stored locally for this research, cited to the agency in every output
that uses it, and handled according to whatever conditions the agency states — including citation
form, redistribution limits and any requirement to remove it on request. A short written undertaking
can be provided if required.

## 7. Contact

`[NAME]`
`[DESIGNATION]`, `[INSTITUTION / DEPARTMENT]`
`[POSTAL ADDRESS]`
`[EMAIL]` · `[PHONE]`
`[ORCID or institutional profile — optional]`

---

*One page. No personal information beyond the requester's own contact block, which is left as a
placeholder for the user to complete.*
