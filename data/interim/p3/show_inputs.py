import json

m = json.load(open("data/interim/p3/inputs_metadata.json"))
for k, r in m["rasters"].items():
    if not r.get("exists"):
        print(k, "MISSING")
        continue
    print("%-34s %5dx%-5d %-8s %-11s res=%.8f nd=%s min=%s max=%s" % (
        k, r["width"], r["height"], r["dtype"], r["crs"], r["res"][0],
        r["nodata"], r["sample_min"], r["sample_max"]))
print()
for k, v in m["vectors"].items():
    print("%-18s n=%-7s crs=%-11s %s" % (k, v.get("n_features"), v.get("crs"),
                                          v.get("geom_types")))
print()
print("chirps files", m["chirps_file_count"])
