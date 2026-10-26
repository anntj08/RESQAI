import pandas as pd

df = pd.read_csv("data/processed/inventory/inventory_spatial_suitability.csv")
print(df.shape)
print(list(df.columns))
print()
u = df["spatial_suitability_use"].value_counts()
print(u)
print()
if "dist_outside_boundary_m" in df.columns:
    s = df[df.spatial_suitability_use == "review_boundary_uncertain"]
    print("review_boundary_uncertain n =", len(s))
    print(s[["source_record_id", "dist_outside_boundary_m"]].to_string(index=False))
    print("min/max:", s.dist_outside_boundary_m.min(), s.dist_outside_boundary_m.max())
print()
if "positional_uncertainty_m" in df.columns:
    print(df.groupby("spatial_suitability_use")["positional_uncertainty_m"].agg(["min", "median", "max"]))
