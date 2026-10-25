"""Dataset 1 (DEM) + Dataset 2 (land cover) acquisition: Wayanad bbox 75.60-76.55E, 11.25-12.00N."""
import gzip
import pathlib
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from fetch import download

RAW = pathlib.Path(r"C:\Major\data\raw")

COP = ("https://copernicus-dem-30m.s3.amazonaws.com/"
       "Copernicus_DSM_COG_10_{tile}_DEM/Copernicus_DSM_COG_10_{tile}_DEM.tif")
SKADI = "https://s3.amazonaws.com/elevation-tiles-prod/skadi/{row}/{tile}.hgt.gz"
WC = ("https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/"
      "ESA_WorldCover_10m_2021_v200_{tile}_Map.tif")

# Tiles intersecting 75.60-76.55 E, 11.25-12.00 N -> rows N11, cols E075/E076
tiles = ["N11_00_E075_00", "N11_00_E076_00"]

for t in tiles:
    download(COP.format(tile=t), RAW / "dem" / "copernicus_glo30" / f"Copernicus_DSM_COG_10_{t}_DEM.tif")

for t in tiles:
    dest = RAW / "dem" / "srtm_1arcsec_skadi" / f"{t}.hgt"
    gz = dest.with_suffix(".hgt.gz")
    download(SKADI.format(row="N11", tile=t), gz, min_bytes=1_000_000)
    if not dest.exists():
        with gzip.open(gz, "rb") as src, open(dest, "wb") as dst:
            shutil.copyfileobj(src, dst)
        print("extracted", dest.name, dest.stat().st_size)

# WorldCover 2021 v200: 3x3 degree tile N09E075 covers N09-N12 / E075-E078
download(WC.format(tile="N09E075"), RAW / "landcover" / "ESA_WorldCover_10m_2021_v200_N09E075_Map.tif")
print("done")
