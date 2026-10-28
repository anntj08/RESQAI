"""Phase 4 — record-level inventory eligibility audit.

Every one of the 468 source records gets exactly one modelling decision and an
explicit reason. The audit is additive: it reads the Phase 2 product and the Phase 3
suitability file and writes a NEW table. Neither is modified, and no source-verification
decision is changed.

Decision vocabulary (p4_use):
  POSITIVE_EVENT             usable in-window event point, representative of its group
  POSITIVE_EVENT_DUPLICATE   usable in-window event point whose group already has a
                             representative; kept for audit, never a second sample
  EXCLUDE_SUPERSEDED         a better-coordinate record from the same site exists
  EXCLUDE_WIDEN_REQUIRED     coordinate precision needs an area label, not a point
  EXCLUDE_BOUNDARY_UNCERTAIN ambiguous district membership
  EXCLUDE_UNDATED_SITE       site evidence with no event date
  EXCLUDE_PRE_2000           historical site evidence, outside the 2000-2026 window
  EXCLUDE_NOT_IN_DISTRICT    outside Wayanad
  EXCLUDE_DISTRICT_CENTROID  coordinate is the district centroid, not a site
  EXCLUDE_COORDINATE_ERROR   stored coordinate is wrong; excluded pending correction

Precedence (first match wins) is ordered by how decisive the obstacle is, so that a
record is never "rescuable" by a later rule. All non-decisive conditions are preserved
in p4_flags, so no distinction is lost when one reason wins.

Outputs:
  data/processed/sampling/eligibility_audit.csv
  data/processed/sampling/eligibility_summary.json

Run:  python scripts/p4_eligibility.py
"""
from __future__ import annotations

import hashlib
import json
import pathlib

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "configs" / "p4_sampling.json").read_text(encoding="utf-8"))
SRC = ROOT / CFG["inventory"]["source"]
OUT = ROOT / "data" / "processed" / "sampling"
OUT.mkdir(parents=True, exist_ok=True)

WINDOW = tuple(CFG["inventory"]["window_years"])


def sha256(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def decide(r: pd.Series) -> tuple[str, list[str], str]:
    """Return (p4_use, flags, reason) for one record."""
    use = str(r["spatial_suitability_use"])
    role = str(r["label_role"])
    superseded = str(r["superseded_by"]).strip() if pd.notna(r["superseded_by"]) else ""
    flags: list[str] = []

    # Flags carry every condition that applies, independently of which one decides.
    if superseded:
        flags.append("superseded")
    if use == "review_widen_label":
        flags.append("widen_required")
    if use == "review_boundary_uncertain":
        flags.append("boundary_uncertain")
    if use == "exclude_until_corrected":
        flags.append("coordinate_error")
    if use == "exclude_district_centroid":
        flags.append("district_centroid")
    if use == "exclude_not_in_district":
        flags.append("outside_district")
    if role == "SITE_EVIDENCE_UNDATED":
        flags.append("undated")
    if role == "HISTORICAL_PRE_2000":
        flags.append("pre_2000")
    if str(r["precision_class"]).startswith("C"):
        flags.append("coarse_precision")

    # Precedence: decisive obstacle first.
    if use == "exclude_not_in_district" or role == "EXCLUDED_NOT_IN_DISTRICT":
        return ("EXCLUDE_NOT_IN_DISTRICT", flags,
                "coordinate falls outside the GADM Wayanad boundary")
    if use == "exclude_until_corrected":
        return ("EXCLUDE_COORDINATE_ERROR", flags,
                f"stored coordinate is wrong and needs correction first "
                f"({r['reason']})")
    if use == "exclude_district_centroid":
        return ("EXCLUDE_DISTRICT_CENTROID", flags,
                "coordinate is the district centroid, not a site location")
    if role == "HISTORICAL_PRE_2000":
        return ("EXCLUDE_PRE_2000", flags,
                f"dated {r['event_date_iso']}, before the {WINDOW[0]}-{WINDOW[1]} window")
    if role == "SITE_EVIDENCE_UNDATED":
        return ("EXCLUDE_UNDATED_SITE", flags,
                "no event date; site evidence cannot be a dated event label")
    if use == "review_widen_label":
        return ("EXCLUDE_WIDEN_REQUIRED", flags,
                "coordinate precision supports an area label, not a point label")
    if use == "review_boundary_uncertain":
        return ("EXCLUDE_BOUNDARY_UNCERTAIN", flags,
                "position is outside GADM beyond the measured boundary disagreement "
                "envelope, so district membership is unresolved")
    if superseded:
        return ("EXCLUDE_SUPERSEDED", flags,
                f"superseded by {superseded} from the same site")

    assert role == "EVENT_POINT_IN_WINDOW" and use == "point_label_ok", (
        f"unhandled combination for {r['source_record_id']}: role={role} use={use}")
    return ("POSITIVE_EVENT", flags, "in-window dated event with a usable point label")


def main() -> None:
    src_sha = sha256(SRC)
    df = pd.read_csv(SRC).sort_values("source_record_id").reset_index(drop=True)

    decided = df.apply(decide, axis=1, result_type="expand")
    df["p4_use"] = decided[0]
    df["p4_flags"] = decided[1].map(lambda f: ";".join(f))
    df["p4_reason"] = decided[2]

    # One representative point per event group. Ties break on positional uncertainty
    # then source_record_id, so the choice is deterministic and reproducible.
    pos = df[df["p4_use"] == "POSITIVE_EVENT"].copy()
    keep = (pos.sort_values(["positional_uncertainty_m", "source_record_id"])
            .drop_duplicates("event_group_id", keep="first")
            .index)
    dup_mask = pos.index.difference(keep)
    df.loc[dup_mask, "p4_use"] = "POSITIVE_EVENT_DUPLICATE"
    df["is_group_representative"] = df.index.isin(keep)

    out = pd.DataFrame({
        "source_record_id": df["source_record_id"],
        "source_id": df["source_id"],
        "label_role": df["label_role"],
        "event_date_iso": df["event_date_iso"],
        "date_certainty": df["date_certainty"],
        "event_year": df["event_year"],
        "event_group_id": df["event_group_id"],
        "verification_status": df["verification_status"],
        "precision_class": df["precision_class"],
        "positional_uncertainty_m": df["positional_uncertainty_m"],
        "spatial_suitability_use": df["spatial_suitability_use"],
        "p4_use": df["p4_use"],
        "p4_flags": df["p4_flags"],
        "p4_reason": df["p4_reason"],
        "is_group_representative": df["is_group_representative"],
    })
    out.to_csv(OUT / "eligibility_audit.csv", index=False, encoding="utf-8",
               lineterminator="\n")

    counts = out["p4_use"].value_counts().sort_index()
    print(f"{'p4_use':<28} {'records':>8}")
    print("-" * 38)
    for k, v in counts.items():
        print(f"{k:<28} {v:>8}")
    print("-" * 38)
    print(f"{'total':<28} {len(out):>8}")

    reps = out[out["p4_use"] == "POSITIVE_EVENT"]
    print(f"\nrepresentative positives      : {len(reps)}")
    print(f"distinct event groups         : {reps['event_group_id'].nunique()}")
    print(f"duplicate points in groups    : "
          f"{(out['p4_use'] == 'POSITIVE_EVENT_DUPLICATE').sum()}")
    print(f"positives dated 2018          : {(reps['event_year'] == 2018).sum()}")
    print(f"positives dated otherwise     : {(reps['event_year'] != 2018).sum()}")
    print(f"positives with flags          : {(reps['p4_flags'] != '').sum()}")

    summary = {
        "input": {"path": CFG["inventory"]["source"], "records": int(len(df)),
                  "sha256": src_sha},
        "phase2_modified": False,
        "decisions": {k: int(v) for k, v in counts.items()},
        "totals": {
            "records": int(len(out)),
            "representative_positives": int(len(reps)),
            "distinct_event_groups": int(reps["event_group_id"].nunique()),
            "duplicate_points": int((out["p4_use"] == "POSITIVE_EVENT_DUPLICATE").sum()),
            "positives_2018": int((reps["event_year"] == 2018).sum()),
            "positives_non_2018": int((reps["event_year"] != 2018).sum()),
        },
        "positive_labels_by_year": {
            str(int(k)): int(v) for k, v in
            reps["event_year"].value_counts().sort_index().items()},
        "positive_labels_by_source": {
            str(k): int(v) for k, v in
            reps["source_id"].value_counts().sort_index().items()},
        "positive_uncertainty_m": {
            "min": float(reps["positional_uncertainty_m"].min()),
            "median": float(reps["positional_uncertainty_m"].median()),
            "max": float(reps["positional_uncertainty_m"].max()),
        },
        "window_years": list(WINDOW),
        "rules": "see docstring of scripts/p4_eligibility.py",
        "not_done": [
            "no source-verification decision was changed",
            "no Phase 2 product was modified",
            "no coordinate was snapped, moved or dropped",
            "no undated record was promoted to a dated event",
        ],
    }
    (OUT / "eligibility_summary.json").write_text(json.dumps(summary, indent=2),
                                                  encoding="utf-8")
    print(f"\nwritten -> {OUT / 'eligibility_audit.csv'}")
    print(f"written -> {OUT / 'eligibility_summary.json'}")


if __name__ == "__main__":
    main()
