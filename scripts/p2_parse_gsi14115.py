"""Parse the GSI 14115 "INVENTORY OF LANDSLIDES: WAYANAD DISTRICT, KERALA" table
(pp. 135-148 of gsi_14115.pdf) into a per-record CSV.

Method
------
The PDF text layer interleaves the seven table columns and breaks rows across
page boundaries, so a column-wise parse is not reliable. This parser uses the
*coordinate line* as the record spine: every record carries exactly one DMS
coordinate string and they occur in table order. For each coordinate line it
walks backwards to recover locality / village / taluk and forwards for the
toposheet.

Date fields
-----------
The type/period-of-failure column cannot be recovered mechanically for rows that
straddle a page break (the text physically precedes the coordinate). Rather than
guess, REVIEWED_DATES below records, for every row, the verbatim date phrase as
printed and a normalised ISO date. Each entry was read directly from the page
cited in pdf_page. This is a reviewed transcription, not an automatic inference;
the verbatim phrase is retained alongside the normalised value so any reader can
re-check it.

Everything else that is not mechanically recoverable is preserved verbatim in
record_text_raw so nothing is invented.

Original coordinate strings are kept unchanged in lat_dms / lon_dms. Decimal
degrees are computed deterministically from the DMS string; printed precision is
reported, not rounded up.

Known source-data defects (flagged, never silently corrected)
-------------------------------------------------------------
* record 17 "Karimani, Valamkode" prints longitude 76d56'58"E, which is ~77 km
  east of the district in Tamil Nadu. Retained as printed.
* record 15 "Thachankolli colony" falls ~0.8 km west of the GADM district
  boundary; it is a genuine border locality, flagged as outside-bbox rather than
  assumed erroneous.
* printed Sl. No. 21 is used twice (Narippara, then Chempra Tea Estate), so the
  table holds 35 records under 34 distinct serial numbers.
"""
import csv
import pathlib
import re

TXT = pathlib.Path(r"C:\Major\data\interim\gsi_pdf_text\gsi_14115.txt")
OUT = pathlib.Path(r"C:\Major\data\interim\inventory_extracts\inventory_gsi14115_wayanad.csv")

text = TXT.read_text(encoding="utf-8")
parts = re.split(r"===== PAGE (\d+) =====", text)
pages = {int(parts[i]): parts[i + 1] for i in range(1, len(parts), 2)}

CHUNKS = [(n, pages.get(n, "")) for n in range(135, 149)]
full = ""
page_offsets = []
for n, body in CHUNKS:
    page_offsets.append((len(full), n))
    full += body


def page_at(offset):
    p = CHUNKS[0][0]
    for start, n in page_offsets:
        if start <= offset:
            p = n
        else:
            break
    return p


# --- reviewed date phrases, keyed by src_row (1..35) --------------------------
# verbatim = exactly as printed; iso = normalised; certainty describes the
# weakest component that the source actually states.
REVIEWED_DATES = {
    1:  ("Debris flow during July 1961 in the midnight", "1961-07", "month"),
    2:  ("Debris flow during July1961.", "1961-07", "month"),
    3:  ("Debris flow during 1982 & June 2007.", "1982; 2007-06", "multi-event"),
    4:  ("Subsidence during 1984", "1984", "year"),
    5:  ("Debris flow during July 1988 at 2015", "1988-07", "month"),
    6:  ("Debris flow during 1988 & July 2007.", "1988; 2007-07", "multi-event"),
    7:  ("Debris flow on 19th June 1991 at 0530", "1991-06-19", "day"),
    8:  ("Debris flow on 19th June 1991 & 1st July at 1500", "1991-06-19; 1991-07-01", "multi-event"),
    9:  ("Debris slide during July 2006", "2006-07", "month"),
    10: ("Piping and land subsidence on 18th August 2006 at night.", "2006-08-18", "day"),
    11: ("Debris flow on 22nd May 2007 at 2345 to 2400 hours.", "2007-05-22", "day"),
    12: ("Debris flow on 22nd June 2007", "2007-06-22", "day"),
    13: ("Debris flow on 22nd June 2007 at night.", "2007-06-22", "day"),
    14: ("Slump and arcuate cracks on 22nd June 2007 at night.", "2007-06-22", "day"),
    15: ("Slump and arcuate cracks on 23rd June 2007 at early hours.", "2007-06-23", "day"),
    16: ("Debris slide on 29th June 2007 at early hours.", "2007-06-29", "day"),
    17: ("Debris flow on 29th June 2007 at early hours.", "2007-06-29", "day"),
    18: ("Debris slide during June 2007 in the early morning", "2007-06", "month"),
    19: ("Debris flow during June 2007 at 17.30", "2007-06", "month"),
    20: ("Debris slide during June 2007 at 6.30", "2007-06", "month"),
    21: ("A crack facilitating landslide, developed during June 2007", "2007-06", "month"),
    22: ("Subsidence and in the road cut this resulted in a debris flow", "", "undated"),
    23: ("Subsidence on 7th July 2007 in the early morning", "2007-07-07", "day"),
    24: ("Subsidence during July 2007 at 14.30", "2007-07", "month"),
    25: ("Debris slide during July 2007", "2007-07", "month"),
    26: ("Multiple slides on 9th July 2007.", "2007-07-09", "day"),
    27: ("Debris flow in 2008 at 21.00", "2008", "year"),
    28: ("Reservoir Induced Landslide", "", "undated"),
    29: ("A crack developed on 15th July 2009 at 1200 hrs", "2009-07-15", "day"),
    30: ("Debris avalanche on 15th July 2009 at 1500 hrs", "2009-07-15", "day"),
    31: ("Debris avalanche on 15th July 2009 at 1730 hrs", "2009-07-15", "day"),
    32: ("Debris slide on 15th July 2009", "2009-07-15", "day"),
    33: ("Debris avalanche on 15th July 2009 at 1500 hrs", "2009-07-15", "day"),
    34: ("Debris avalanche on 16th July 2009", "2009-07-16", "day"),
    35: ("Debris avalanche on 16th July 2009", "2009-07-16", "day"),
}

# localities whose name line sits on a different page from the coordinate
LOCALITY_FIX = {7: "Kappikalam", 31: "Kanthanpara"}

# geology for rows where the lithology cell sits before the coordinate because the
# row straddles a page break; read off the page cited in pdf_page
GEOLOGY_FIX = {
    7: "Gneiss/Charnockite", 12: "Gneiss/Charnockite", 16: "Charnockite gneiss",
    27: "Gneiss/Charnockite", 31: "Charnockite gneiss", 34: "Charnockite gneiss",
}

COORD = re.compile(
    r"(\d{1,2})\s*[°˚]\s*(\d{1,2})\s*['\u2019]\s*(\d{1,2}(?:\.\d+)?)\s*[\"”]\s*([NS])\s*,?\s*"
    r"(\d{1,3})\s*[°˚]\s*(\d{1,2})\s*['\u2019]\s*(\d{1,2}(?:\.\d+)?)\s*[\"”]\s*([EW])"
)

matches = list(COORD.finditer(full))
print(f"coordinate lines found: {len(matches)}")
assert len(matches) == 35, f"expected 35 coordinate lines, got {len(matches)}"

LIMITS = [m.start() for m in matches] + [len(full)]

records = []
for i, m in enumerate(matches):
    seg_start = LIMITS[i - 1] if i > 0 else 0
    seg_end = LIMITS[i + 1]
    before = full[seg_start:m.start()]
    after = full[m.end():seg_end]

    lines_before = [ln.strip() for ln in before.split("\n")]
    vi = next((j for j in range(len(lines_before) - 1, -1, -1)
               if re.search(r"\bVillage\b", lines_before[j])), None)
    village = re.sub(r"\s*\bVillage\b.*$", "", lines_before[vi]).strip() if vi is not None else ""

    ti = next((j for j in range(len(lines_before) - 1, -1, -1)
               if re.search(r"\bTaluk\b", lines_before[j])), None)
    taluk = re.sub(r"\s*\bTaluk\b.*$", "", lines_before[ti]).strip() if ti is not None else ""

    locality = ""
    if vi is not None:
        for j in range(vi - 1, max(vi - 6, -1), -1):
            cand = lines_before[j]
            if not cand or re.fullmatch(r"\|?\s*Page\s*", cand):
                continue
            if re.search(r"\bVillage\b|\bTaluk\b|Wayanad District", cand):
                continue
            locality = cand
            break
    locality = re.sub(r"^\d{1,2}\s+", "", locality).strip()
    locality = re.sub(r"\s{2,}", " ", locality).rstrip("*").strip()

    after_lines = [ln.strip() for ln in after.split("\n")]
    ts, ts_idx = "", None
    for j, ln in enumerate(after_lines):
        mm = re.search(r"TS\.?\s*No\.?\s*([0-9]{2}\s?[A-Z]\s?/\s?\d{1,2})", ln)
        if mm:
            ts = re.sub(r"\s+", "", mm.group(1))
            ts_idx = j
            break

    seg_flat = re.sub(r"\s+", " ", before + " " + after)
    # forward-only window: the table's columns flow across page breaks, so text
    # *before* the coordinate can belong to the previous record. Area, dimensions
    # and casualties are therefore read only from this coordinate up to the next.
    fwd_flat = re.sub(r"\s+", " ", after)

    # geology token
    geology = ""
    if re.search(r"Charnockite gneiss", fwd_flat):
        geology = "Charnockite gneiss"
    elif re.search(r"Gneiss\s*/\s*Charnockite", fwd_flat):
        geology = "Gneiss/Charnockite"

    # destroyed area
    area_txt = ""
    am = re.search(r"area of ([\d,\.]+)\s*(m2|sqkm)", fwd_flat, re.I)
    if am:
        area_txt = f"{am.group(1)} {am.group(2)}"

    dims = {}
    for key, pat in (("length_m", r"L\s*=\s*(\d+(?:\.\d+)?)\s*m"),
                     ("width_m", r"[WB]\s*=\s*(\d+(?:\.\d+)?)\s*m"),
                     ("depth_m", r"T\s*=\s*(\d+(?:\.\d+)?)\s*m")):
        mm = re.search(pat, fwd_flat, re.I)
        dims[key] = mm.group(1) if mm else ""

    # casualties: keep the sentence fragment that states loss of life
    cas = ""
    cm = re.search(r"([^.]{0,60}?(?:\d+\s*(?:people|persons?|woman|man|lives)\b[^.]{0,40}?"
                   r"(?:died|killed|taken)))[^.]*", fwd_flat, re.I)
    if cm:
        cas = cm.group(1).strip()

    lat_dd = int(m.group(1)) + int(m.group(2)) / 60 + float(m.group(3)) / 3600
    lon_dd = int(m.group(5)) + int(m.group(6)) / 60 + float(m.group(7)) / 3600
    if m.group(4) == "S":
        lat_dd = -lat_dd
    if m.group(8) == "W":
        lon_dd = -lon_dd

    dec_lat = len(m.group(3).split(".")[1]) if "." in m.group(3) else 0
    dec_lon = len(m.group(7).split(".")[1]) if "." in m.group(7) else 0
    dec = max(dec_lat, dec_lon)
    coord_precision_deg = round(1.0 / 3600.0 / (10 ** dec), 9)

    rn = re.search(r"(?:^|\n)\s*(\d{1,2})\s{1,4}(?=[A-Z0-9])", before)
    sl_printed = rn.group(1) if rn else ""

    verbatim, iso, certainty = REVIEWED_DATES[i + 1]
    raw = re.sub(r"\s+", " ", before[-800:] + " <<COORD>> " + after[:1000]).strip()

    records.append({
        "src_row": i + 1,
        "src_sl_no_printed": sl_printed,
        "locality": LOCALITY_FIX.get(i + 1, locality),
        "village": village,
        "taluk": taluk,
        "district": "Wayanad",
        "lat_dms": f"{m.group(1)}d{m.group(2)}'{m.group(3)}\"{m.group(4)}",
        "lon_dms": f"{m.group(5)}d{m.group(6)}'{m.group(7)}\"{m.group(8)}",
        "latitude_dd": round(lat_dd, 6),
        "longitude_dd": round(lon_dd, 6),
        "coord_precision_deg": coord_precision_deg,
        "toposheet": ts,
        "date_text_verbatim": verbatim,
        "event_date_iso": iso,
        "date_certainty": certainty,
        "event_year": (iso.split("-")[0] if iso and certainty != "multi-event" else
                       (";".join(sorted({d.split("-")[0] for d in iso.split("; ")})) if iso else "")),
        "geology": GEOLOGY_FIX.get(i + 1, geology),
        "area_destroyed_text": area_txt,
        "length_m": dims["length_m"],
        "width_m": dims["width_m"],
        "depth_m": dims["depth_m"],
        "casualties_text": cas,
        "data_from_outside_agency": "Y" if "*" in (locality or "") else "N",
        "source_report": "GSI 14115 LANDSLIDE INVENTORY OF KERALA (FS 2007-2010)",
        "source_pdf": "gsi_14115.pdf",
        "pdf_page": page_at(m.start()),
        "extraction_method": "coordinate-line spine; date column reviewed transcription; other columns verbatim in record_text_raw",
        "record_text_raw": raw,
    })

# asterisk flag must be read before the locality was stripped
for r in records:
    src_loc = LOCALITY_FIX.get(r["src_row"])
    # recompute from raw text: asterisk sits immediately after the locality name
    if re.search(r"\n\s*(?:\d{1,2}\s+)?" + re.escape(r["locality"]) + r"\*", full):
        r["data_from_outside_agency"] = "Y"

FLAGS = {
    17: "printed longitude 76d56'58\"E is ~77 km east of Wayanad (in Tamil Nadu); "
        "almost certainly a typographic error for 75d56'58\"E. Retained as printed, not corrected.",
    15: "falls ~0.8 km outside the western GADM boundary; a genuine border locality, not assumed erroneous.",
}
for r in records:
    r["data_quality_flag"] = FLAGS.get(r["src_row"], "")

seen = {}
for r in records:
    seen[r["src_sl_no_printed"]] = seen.get(r["src_sl_no_printed"], 0) + 1
for r in records:
    if seen[r["src_sl_no_printed"]] > 1:
        r["data_quality_flag"] = (r["data_quality_flag"] + " " if r["data_quality_flag"] else "") + \
            f"printed Sl. No. {r['src_sl_no_printed']} is duplicated in the source table."

FIELDS = list(records[0].keys())
OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS)
    w.writeheader()
    w.writerows(records)

# --- spot checks read straight off the PDF pages ------------------------------
# (src_row, expected area text, expected length_m) -- guards against column bleed
KNOWN = {
    1: ("750 m2", "50"), 2: ("81,000 m2", "450"), 3: ("500 m2", "100"),
    4: ("40,000 m2", ""), 7: ("1,500 m2", "150"), 8: ("2,000 m2", "100"),
    11: ("1,875 m2", "75"), 12: ("1,000 m2", "100"), 22: ("2,500 m2", "50"),
    24: ("225 m2", "15"), 27: ("750 m2", "75"), 33: ("12,000 m2", "300"),
    35: ("750 m2", "50"),
}
bad = []
for row, (area, length) in KNOWN.items():
    r = records[row - 1]
    if r["area_destroyed_text"] != area or r["length_m"] != length:
        bad.append((row, r["area_destroyed_text"], r["length_m"], area, length))
print(f"spot checks: {len(KNOWN) - len(bad)}/{len(KNOWN)} match the printed page")
for b in bad:
    print("  MISMATCH row", b)

print(f"\nwrote {OUT}  rows={len(records)}")
print(f"distinct printed Sl. No.: {len(set(r['src_sl_no_printed'] for r in records))}")
print(f"undated rows: {[r['src_row'] for r in records if r['date_certainty'] == 'undated']}")
print(f"multi-event rows: {[r['src_row'] for r in records if r['date_certainty'] == 'multi-event']}")
print(f"rows whose event year set includes 2000-2026: "
      f"{[r['src_row'] for r in records if any(2000 <= int(y) <= 2026 for y in re.findall(r'\\d{4}', r['event_year'] or ''))]}")
print("\nany-event-in-window count:",
      sum(1 for r in records
          if any(2000 <= int(y) <= 2026 for y in re.findall(r"\d{4}", r["event_year"] or ""))))
print("rows with empty geology:", [r["src_row"] for r in records if not r["geology"]])
print("\nall rows:")
for r in records:
    print(f"  {r['src_row']:2d} sl={r['src_sl_no_printed']:>2s} {r['locality'][:30]:30s} "
          f"{r['village'][:20]:20s} {r['latitude_dd']:9.5f} {r['longitude_dd']:9.5f} "
          f"{r['toposheet']:7s} {r['event_date_iso']:24s} area={r['area_destroyed_text']:12s} p{r['pdf_page']}")
