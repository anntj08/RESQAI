"""Print the cell contents of Table 1 from PMC12749052 (recent Kerala landslide
events with locality, date, coordinates and impacts).

Only the event metadata is used: localities, dates, coordinates and documented
impacts. The paper's modelling results are not part of this project.
"""
import pathlib
import re

import pandas as pd

p = pathlib.Path(r"C:\Major\data\raw\literature_events\PMC12749052.xml")
txt = p.read_text(encoding="utf-8", errors="replace")
tables = re.findall(r"<table-wrap\b.*?</table-wrap>", txt, re.S)
t = tables[0]

rows = re.findall(r"<tr\b.*?</tr>", t, re.S)
for i, row in enumerate(rows):
    cells = re.findall(r"<t[hd]\b[^>]*>(.*?)</t[hd]>", row, re.S)
    vals = []
    for c in cells:
        c = re.sub(r"<[^>]+>", " ", c)
        c = c.replace("&#x000b0;", "deg").replace("&#x02019;", "'").replace("&#x0201d;", '"')
        c = re.sub(r"\s+", " ", c).strip()
        vals.append(c)
    print(f"row {i}: {vals}")
