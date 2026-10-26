import pandas as pd

df = pd.read_csv("data/processed/inventory/inventory_spatial_suitability.csv")
two = df[df.coord_precision_deg_stored.round(6) >= 0.009]
print("records with stored precision >= 0.009 deg (2 dp):", len(two))
print(two.groupby(["source_id", "spatial_suitability_use"]).size().to_string())
print()
print("any used as point label:", (two.spatial_suitability_use == "point_label_ok").sum())
print()
ok = df[df.spatial_suitability_use == "point_label_ok"]
print("point_label_ok by label_role:")
print(ok.label_role.value_counts().to_string())
print()
print("coord precision classes:", df.precision_class.value_counts().to_dict())
