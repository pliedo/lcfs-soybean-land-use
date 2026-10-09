#!/usr/bin/env python3
"""Validate local raster counts against the published Hub 1 CDL smoke result."""
from __future__ import annotations

import csv
import subprocess
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.mask import mask
from shapely.geometry import mapping

ROOT = Path(__file__).resolve().parents[1]
WCS = "https://nassgeodata.gmu.edu/CropScapeService/wms_cdlall.cgi"
PIXEL_ACRES = 900 / 4046.8564224
LEGACY_BOUNDING_BOX_SOY_ACRES = 318619.7


def main() -> None:
    rings = gpd.read_file(ROOT / "output" / "facility_rings_exclusive.gpkg")
    ring = rings[(rings.hub_id == 1) & (rings.ring_index == 1)].to_crs(5070)
    geometry = ring.geometry.iloc[0]
    xmin, ymin, xmax, ymax = geometry.bounds
    tif = ROOT / "data" / "raw" / "cdl_raster_validation_hub1_2023.tif"
    tif.parent.mkdir(parents=True, exist_ok=True)
    params = (
        f"SERVICE=wcs&VERSION=1.0.0&REQUEST=GetCoverage&COVERAGE=cdl_2023&"
        f"CRS=epsg:5070&BBOX={xmin},{ymin},{xmax},{ymax}&RESX=30&RESY=30&FORMAT=gtiff"
    )
    if not tif.exists():
        subprocess.run(["curl", "--fail", "--silent", "--show-error", "--max-time", "180",
                        "-o", str(tif), f"{WCS}?{params}"], check=True)

    with rasterio.open(tif) as src:
        pixels, transform = mask(src, [mapping(geometry)], crop=True, filled=False)
        values = pixels[0].compressed().astype(int)
    counts = np.bincount(values, minlength=max(255, values.max() + 1))
    soy_acres = counts[5] * PIXEL_ACRES
    all_valid_acres = counts[1:].sum() * PIXEL_ACRES
    crop_codes = list(range(1, 62)) + list(range(66, 78)) + list(range(204, 255))
    cropland_acres = counts[crop_codes].sum() * PIXEL_ACRES
    difference = soy_acres - LEGACY_BOUNDING_BOX_SOY_ACRES
    result = {
        "hub_id": 1, "year": 2023, "ring_index": 1,
        "soy_acres_raster": soy_acres,
        "legacy_bounding_box_soy_acres": LEGACY_BOUNDING_BOX_SOY_ACRES,
        "difference_from_legacy_acres": difference,
        "difference_from_legacy_percent": difference / LEGACY_BOUNDING_BOX_SOY_ACRES * 100,
        "all_valid_acres": all_valid_acres,
        "cropland_acres": cropland_acres,
        "soy_share_all_land": soy_acres / all_valid_acres,
        "soy_share_cropland": soy_acres / cropland_acres,
    }
    out = ROOT / "output" / "diagnostics" / "cdl_raster_validation_hub1_2023.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=result)
        writer.writeheader(); writer.writerow(result)
    print(result)


if __name__ == "__main__":
    main()
