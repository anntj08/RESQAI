import rasterio

files = [
    r"data/raw/dem/copernicus_glo30/Copernicus_DSM_COG_10_N11_00_E075_00_DEM.tif",
    r"data/raw/dem/copernicus_glo30/Copernicus_DSM_COG_10_N11_00_E076_00_DEM.tif",
    r"data/raw/dem/srtm_1arcsec_skadi/N11E075.hgt",
    r"data/raw/dem/srtm_1arcsec_skadi/N11E076.hgt",
]
res = [1 / 3600]
for f in files:
    with rasterio.open(f) as ds:
        t = ds.transform
        print("=" * 78)
        print(f.split("/")[-1])
        print("  driver   :", ds.driver)
        print("  shape    :", ds.shape)
        print("  transform: c=%.10f f=%.10f a=%.12f e=%.12f" % (t.c, t.f, t.a, t.e))
        print("  bounds   : %.10f %.10f %.10f %.10f" % ds.bounds)
        print("  AREA_OR_POINT tag:", ds.tags().get("AREA_OR_POINT"))
        print("  last centre (c+(w-1)a): %.10f" % (t.c + t.a * (ds.width - 1)))
        print("  implied right edge     : %.10f" % (t.c + t.a * ds.width))
print()
print("1/3600 = %.12f" % (1 / 3600))
print("75 - 1/3600 = %.10f" % (75 - 1 / 3600))
print("75 - 0.5/3600 = %.10f" % (75 - 0.5 / 3600))
print("12 + 0.5/3600 = %.10f" % (12 + 0.5 / 3600))
