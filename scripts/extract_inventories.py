"""Extract Wayanad-relevant landslide records from GSI reports into per-source CSVs.

14337 Annexure-1 : 99 records, Wayanad rows sl 65-99 (2-decimal coordinates)
14768 Table 4    : 29 archival records (DMS, 24 in Wayanad)
14768 Table 5    : 17 field-inventoried records (DMS to 1 arc-second)
2018 datasheets  : 8 records (4-decimal coordinates)

No deduplication or merging across sources. Coordinate precision is recorded per row.
"""
import csv
import pathlib
import re

TXT = pathlib.Path(r"C:\Major\data\interim\gsi_pdf_text")
OUT = pathlib.Path(r"C:\Major\data\interim\inventory_extracts")
OUT.mkdir(parents=True, exist_ok=True)


def pages(f):
    t = (TXT / f"{f}.txt").read_text(encoding="utf-8")
    p = re.split(r"===== PAGE (\d+) =====", t)
    return {int(p[i]): p[i + 1] for i in range(1, len(p), 2)}


def dms(deg, minute, sec):
    return round(float(deg) + float(minute) / 60 + float(sec) / 3600, 6)


# ---------------- 14337 Annexure-1 (pages 56-57 carry Wayanad rows 65-99) ----------
g = pages("gsi_14337")
rows = []
for n in sorted(g):
    buf = None
    for line in g[n].splitlines():
        s = line.strip()
        if not s:
            continue
        m = re.match(r"^(\d{1,3})\s+(.+?)\s+(Kasaragod|Kannur|Wayanad)\s+([\d.]+)\s+([\d.]+)\s*(.*)$", s)
        if m:
            if buf:
                rows.append(buf)
            buf = {"sl": int(m.group(1)), "location": m.group(2).strip(),
                   "district": m.group(3), "lat": float(m.group(4)), "lon": float(m.group(5)),
                   "rest": m.group(6).strip(), "page": n}
        elif buf is not None:
            buf["rest"] += " " + s
    if buf:
        rows.append(buf)

wl = [r for r in rows if r["district"] == "Wayanad"
      and 10.5 <= r["lat"] <= 12.5 and 74.0 <= r["lon"] <= 78.0]
wl.sort(key=lambda r: r["sl"])
print(f"14337: {len(wl)} Wayanad rows (sl {wl[0]['sl']}-{wl[-1]['sl']})")

with open(OUT / "inventory_14337_wayanad.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["src_sl_no", "location", "district", "latitude_dd", "longitude_dd",
                "landslide_type", "length_m", "width_m", "depth_m", "slope_context",
                "source_report", "coord_precision_deg", "date_of_event", "source_pdf", "pdf_page"])
    for r in wl:
        m = re.match(r"(.*?)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+(Natural slope|Cut slope|toe erosion)(.*)$", r["rest"])
        if m:
            typ, L, W, D, ctx, src = m.groups()
        else:
            m2 = re.match(r"(.*?)\s+(Natural slope|Cut slope|toe erosion)(.*)$", r["rest"])
            typ, L, W, D, ctx, src = (m2.group(1), "", "", "", m2.group(2), m2.group(3)) if m2 else (r["rest"], "", "", "", "", "")
        w.writerow([r["sl"], r["location"], r["district"], r["lat"], r["lon"],
                    re.sub(r"\s+", " ", typ).strip(), L, W, D, ctx.strip(), src.strip(),
                    0.01, "", "gsi_14337.pdf", r["page"]])

# ---------------- 14768 Table 4 (page 27) ----------------
g = pages("gsi_14768")
joined = re.sub(r"\s*\n\s*", " ", g[27])
pat = re.compile(
    r"(\d{1,2})\s+([A-Za-z][A-Za-z0-9 ,.\-']*?)\s+11\D{0,3}(\d{1,2})\D(\d{1,2}(?:\.\d+)?)\D{1,3}\s*"
    r"76\D{0,3}(\d{1,2})\D(\d{1,2}(?:\.\d+)?)\D{1,3}\s+([\d.\-]*)\s+([\d.\-]*)\s+([\d.\-]*)\s+"
    r"([A-Za-z][A-Za-z ]+)")
recs = [m.groups() for m in pat.finditer(joined)]
recs = [r for r in recs if int(r[0]) <= 29]
print(f"14768 Table 4: {len(recs)} rows")

with open(OUT / "inventory_14768_table4.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["src_sl_no", "location", "latitude_dd", "longitude_dd", "length_m", "width_m",
                "depth_m", "landslide_type", "coord_precision_deg", "date_of_event", "source_pdf", "source_table"])
    for sl, loc, la_m, la_s, lo_m, lo_s, L, W, D, typ in recs:
        w.writerow([sl, loc.strip(), dms(11, la_m, la_s), dms(76, lo_m, lo_s), L, W, D,
                    typ.strip(), 0.0001, "", "gsi_14768.pdf", "Table 4 (archival)"])

# ---------------- 14768 Table 5 (page 28) ----------------
joined5 = re.sub(r"\s*\n\s*", " ", g[28])
pat5 = re.compile(
    r"(\d{1,2})\s+([A-Za-z0-9 .\-']*?)\s*11\D{0,3}(\d{1,2})\D(\d{1,2})\D{1,3}\s*"
    r"76\D{0,3}(\d{1,2})\D(\d{1,2})\D{1,3}\s+([\d.\-]*)\s+([\d.\-]*)\s+([\d.\-]*)\s+"
    r"([A-Za-z][A-Za-z ()]*)")
recs5 = [m.groups() for m in pat5.finditer(joined5)]
recs5 = [r for r in recs5 if int(r[0]) <= 17]
print(f"14768 Table 5: {len(recs5)} rows")

with open(OUT / "inventory_14768_table5.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["src_sl_no", "location", "latitude_dd", "longitude_dd", "length_m", "width_m",
                "height_m", "landslide_type", "coord_precision_deg", "date_of_event", "source_pdf", "source_table"])
    for sl, loc, la_m, la_s, lo_m, lo_s, L, W, H, typ in recs5:
        w.writerow([sl, loc.strip(), dms(11, la_m, la_s), dms(76, lo_m, lo_s), L, W, H,
                    typ.strip(), 0.000278, "", "gsi_14768.pdf", "Table 5 (field inventory)"])

# ---------------- 2018 post-disaster datasheets ----------------
g = pages("gsi_2018_post_disaster_wayanad")
full = "\n".join(g[n] for n in sorted(g))
recs2018 = []
for b in re.split(r"(?=Slide No\.\s*:)", full):
    if "KER/WYD" not in b:
        continue
    def grab(label):
        mm = re.search(label + r"\s*:\s*([^\n]+)", b)
        return mm.group(1).strip() if mm else ""
    recs2018.append([grab(r"Slide No\."), grab(r"Name of the slide"), grab(r"Latitude"), grab(r"Longitude"),
                     grab(r"Length"), grab(r"Width"), grab(r"Height"), grab(r"Depth"), grab(r"Area"),
                     grab(r"Volume"), grab(r"Type of\s+Material"), grab(r"Type of movement"),
                     grab(r"Geology/Lithology"), grab(r"Landuse/ ?Landcover"), grab(r"History"),
                     grab(r"Triggering Factor")])
print(f"2018 datasheets: {len(recs2018)}")

with open(OUT / "inventory_2018_postdisaster.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["slide_no", "landslide_name", "latitude_dd", "longitude_dd", "length", "width", "height",
                "depth", "area", "volume", "material", "movement_type", "geology", "landuse",
                "event_history", "trigger", "coord_precision_deg", "source_pdf"])
    for r in recs2018:
        w.writerow(r + [0.0001, "gsi_2018_post_disaster_wayanad.pdf"])
