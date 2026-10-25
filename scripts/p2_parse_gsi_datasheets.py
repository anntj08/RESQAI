"""Parse the GSI 42-point geo-parametric datasheets for the two Wayanad slides
recorded in the 2024 and 2025 post-disaster reports.

Sources
-------
gsi_PDLS_2024_51817.pdf, Annexure p.95-96, Slide No. KER/WYD/58A03/2024/01
gsi_PDLS_2025_61074.pdf, Annexure-1 p.80-81, Slide No. KER/WYD/58A03/2025/01

These are the only Wayanad entries in either report (verified: 'KER/WYD'
occurs once in each report's full text).

Field positions 1-42 are labelled in the PDF; this parser maps the label to value
with a regex per field and falls back to verbatim text. Coordinates are printed
without a degree glyph for the 2024 sheet (the superscript was lost in the text
layer): "11027'46"" is read as 11 deg 27' 46" N, matching the printed
"76008'03"" = 76 deg 08' 03" E.
"""
import csv
import pathlib
import re

BASE = pathlib.Path(r"C:\Major\data\interim\gsi_pdf_text")
OUT = pathlib.Path(r"C:\Major\data\interim\inventory_extracts\inventory_gsi_pdls_wayanad.csv")


def page(stem, n):
    t = (BASE / f"{stem}.txt").read_text(encoding="utf-8")
    p = re.split(r"===== PAGE (\d+) =====", t)
    pgs = {int(p[i]): p[i + 1] for i in range(1, len(p), 2)}
    return pgs[n]


def flat(s):
    return re.sub(r"\s+", " ", s).strip()


def field(block, label, nxt):
    tail = re.escape(nxt) if nxt else r"\Z"
    m = re.search(re.escape(label) + r"\s*:?\s*(.*?)(?=" + tail + r")", block, re.S)
    return flat(m.group(1)) if m else ""


def dms_to_dd(d, m, s):
    return round(int(d) + int(m) / 60 + float(s) / 3600, 6)


def parse_degraded_dms(s):
    """Parse a DMS string whose degree glyph has been replaced by a literal '0',
    e.g. '11027\\'46"' is 11 deg 27' 46" and '76008\\'03"' is 76 deg 08' 03".
    Returns (degrees, minutes, seconds). Raises if the pattern does not fit, so a
    silent mis-read is impossible."""
    m = re.fullmatch(r"(\d{2})0(\d{2})['\u2019](\d{2}(?:\.\d+)?)", s)
    if not m:
        raise ValueError(f"unexpected degraded DMS: {s!r}")
    return m.groups()


def parse_dms(s):
    m = re.fullmatch(r"(\d{2})[\u00b0\u02da]?(\d{2})['\u2019](\d{2}(?:\.\d+)?)", s)
    if not m:
        raise ValueError(f"unexpected DMS: {s!r}")
    return m.groups()


records = []

# ---------------- 2024: Mundakkai-Chooralmala ----------------
b24 = page("gsi_PDLS_2024_51817", 95) + page("gsi_PDLS_2024_51817", 96)
b24 = re.sub(r"\n\s*\d{1,2}\s+", "\n", b24)  # drop the 1..42 field numbers
f24 = flat(b24)

m = re.search(r"Latitude\s*:?\s*(\d{2}0\d{2}['\u2019]\d{2}(?:\.\d+)?)", f24)
lat = dms_to_dd(*parse_degraded_dms(m.group(1)))
m = re.search(r"Longitude\s*:?\s*(\d{2}0\d{2}['\u2019]\d{2}(?:\.\d+)?)", f24)
lon = dms_to_dd(*parse_degraded_dms(m.group(1)))

records.append({
    "slide_no": "KER/WYD/58A03/2024/01",
    "state": "Kerala", "district": "Wayanad",
    "toposheet": "58A/03",
    "name_of_slide": field(f24, "Name of the slide", "NH/SH/Locality"),
    "locality": field(f24, "NH/SH/Locality", "Latitude"),
    "latitude_dd": lat, "longitude_dd": lon,
    "coord_text_verbatim": "11" + "027'46\"N / 76" + "008'03\"E (degree glyph absent in PDF text layer)",
    "coord_precision_deg": round(0.01 / 3600, 9),
    "length": field(f24, "Length", "Width"), "width": field(f24, "Width", "Height"),
    "height": field(f24, "Height", "Area"), "area": field(f24, "Area", "Depth"),
    "depth": field(f24, "Depth", "Volume"), "volume": field(f24, "Volume", "Run out distance"),
    "runout": field(f24, "Run out distance", "Type of Material"),
    "material": field(f24, "Type of Material", "Type of movement"),
    "movement": field(f24, "Type of movement", "Rate of movement"),
    "rate": field(f24, "Rate of movement", "Activity"),
    "activity": field(f24, "Activity", "Distribution"),
    "distribution": field(f24, "Distribution", "Style"),
    "style": field(f24, "Style", "Failure mechanism"),
    "failure_mechanism": field(f24, "Failure mechanism", "History"),
    "history": field(f24, "History", "Geomorphology"),
    "geomorphology": field(f24, "Geomorphology", "Geology/Lithology"),
    "lithology": field(f24, "Geology/Lithology", "Structure"),
    "landuse": field(f24, "Landuse/ Landcover", "Hydrological condition"),
    "trigger": field(f24, "Triggering Factor", "Death of persons"),
    "deaths": field(f24, "Death of persons", "People affected"),
    "communication": field(f24, "Communication", "Infrastructure"),
    "geoscientific_causes": field(f24, "Geo-scientific Causes", "Remedial measures"),
    "remedial": field(f24, "Remedial measures", "Remarks"),
    "category": "", "date_of_reporting": "",
    "source_report": "GSI PDLS 2024, Post-Disaster Studies of Landslides in Kerala, 2024",
    "source_pdf": "gsi_PDLS_2024_51817.pdf", "pdf_page": 95,
})

# ---------------- 2025: Meenakshi Bridge ----------------
b25 = page("gsi_PDLS_2025_61074", 80) + page("gsi_PDLS_2025_61074", 81)
b25 = re.sub(r"\n\s*\d{1,2}\s+", "\n", b25)
f25 = flat(b25)

m = re.search(r"Latitude\s*:?\s*(\d{2}[\u00b0\u02da]?\d{2}['\u2019]\d{2}(?:\.\d+)?)", f25)
lat = dms_to_dd(*parse_dms(m.group(1)))
# the printed longitude is malformed: 76' 08' 8.34"  (minute glyph where the degree
# glyph belongs). Read as 76 deg 08' 08.34" E.
m = re.search(r"Longitude\s*:?\s*(\d{2})['\u2019]\s*(\d{2})['\u2019]\s*(\d{1,2}(?:\.\d+)?)", f25)
lon = dms_to_dd(*m.groups())

records.append({
    "slide_no": "KER/WYD/58A03/2025/01",
    "state": "Kerala", "district": "Wayanad",
    "toposheet": "58A/02",
    "name_of_slide": field(f25, "Name of the slide", "NH/SH/Locality"),
    "locality": field(f25, "NH/SH/Locality", "Latitude"),
    "latitude_dd": lat, "longitude_dd": lon,
    "coord_text_verbatim": "11°31'15.67\" / 76' 08' 8.34\" (degree glyph printed as a minute glyph in longitude)",
    "coord_precision_deg": round(0.01 / 3600, 9),
    "length": field(f25, "Length", "Width"), "width": field(f25, "Width", "Height"),
    "height": field(f25, "Height", "Area"), "area": field(f25, "Area", "Depth"),
    "depth": field(f25, "Depth", "Volume"), "volume": field(f25, "Volume", "Run out distance"),
    "runout": field(f25, "Run out distance", "Type of Material"),
    "material": field(f25, "Type of Material", "Type of movement"),
    "movement": field(f25, "Type of movement", "Rate of movement"),
    "rate": field(f25, "Rate of movement", "Activity"),
    "activity": field(f25, "Activity", "Distribution"),
    "distribution": field(f25, "Distribution", "Style"),
    "style": field(f25, "Style", "Failure mechanism"),
    "failure_mechanism": field(f25, "Failure mechanism", "History"),
    "history": field(f25, "History", "Geomorphology"),
    "geomorphology": field(f25, "Geomorphology", "Geology/Lithology"),
    "lithology": field(f25, "Geology/Lithology", "Structure"),
    "landuse": field(f25, "Landuse/ Landcover", "Hydrological condition"),
    "trigger": field(f25, "Triggering Factor", "Death of persons"),
    "deaths": field(f25, "Death of persons", "People affected"),
    "communication": field(f25, "Communication", "Infrastructure"),
    "geoscientific_causes": field(f25, "Geo-scientific Causes", "Remedial measures"),
    "remedial": field(f25, "Remedial measures", "Remarks"),
    "category": field(f25, "Landslide Category", ""),
    "date_of_reporting": field(f25, "Date of Reporting", "Landslide Category"),
    "source_report": "GSI PDLS 2025, Post-Disaster Studies of Landslides in Kerala, 2025",
    "source_pdf": "gsi_PDLS_2025_61074.pdf", "pdf_page": 80,
})

FIELDS = list(records[0].keys())
OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS)
    w.writeheader()
    w.writerows(records)

print(f"wrote {OUT} rows={len(records)}\n")
for r in records:
    print(f"{r['slide_no']}  {r['name_of_slide']}")
    print(f"   coord {r['latitude_dd']}, {r['longitude_dd']}   (verbatim: {r['coord_text_verbatim']})")
    for k in ("length", "width", "height", "area", "depth", "volume", "runout", "material",
              "movement", "rate", "activity", "distribution", "style", "failure_mechanism",
              "history", "lithology", "landuse", "trigger", "deaths", "category", "date_of_reporting"):
        print(f"   {k:18s}: {r[k][:150]}")
    print()
