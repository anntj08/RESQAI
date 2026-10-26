import json
m = json.load(open("data/processed/qa/readiness_metrics.json"))
print("point_label_records_tested", m["point_label_records_tested"])
print("in_window_point_records", m["in_window_point_records"])
print("distinct_event_groups", m["distinct_event_groups"])
print(json.dumps(m["nearest_neighbour_distance_m"], indent=2))
print(json.dumps(m["single_linkage_clusters"], indent=2))
print(json.dumps(m["records_per_year"], indent=2))
print("date_precision", m["date_precision"])
print("share_2018_pct", m["share_2018_pct"])
for k, v in m["coverage_by_layer"].items():
    print("%-56s %4d/%-4d %6.2f%%  nodata=%d" % (k, v["valid"], v["points_tested"],
                                                 v["coverage_pct"], v["nodata"]))
