"""SRTM 1-arcsec mirror (Skadi) + ESA WorldCover 2021 v200 for the Wayanad window."""
import gzip
import pathlib
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from fetch import download

RAW = pathlib.Path(r"C:\Major\data\raw")
SKADI = "https://s3.amazonaws.com/elevation-tiles-prod/skadi/{row}/{tile}.hgt.gz"
WC = ("https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/"
      "ESA_WorldCover_10m_2021_v200_{tile}_Map.tif")

for t in ["N11E075", "N11E076"]:
    dest = RAW / "dem" / "srtm_1arcsec_skadi" / f"{t}.hgt"
    gz = dest.with_suffix(".hgt.gz")
    dest.parent.mkdir(parents=True, exist_ok=True)
    download(SKADI.format(row="N11", tile=t), gz, min_bytes=1_000_000)
    if not dest.exists():
        with gzip.open(gz, "rb") as src, open(dest, "wb") as dst:
            shutil.copyfileobj(src, dst)
        print("extracted", dest.name, dest.stat().st_size)
    else:
        print("SKIP hgt exists", dest.name, dest.stat().st_size)

download(WC.format(tile="N09E075"),
         RAW / "landcover" / "ESA_WorldCover_10m_2021_v200_N09E075_Map.tif")
print("done")
