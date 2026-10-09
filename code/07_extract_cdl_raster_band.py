#!/usr/bin/env python3
"""Extract official CDL class composition for one exclusive 25-mile band.

Each task downloads a temporary USDA WCS GeoTIFF for one hub-year bounding
window, masks it to the exact exclusive ring polygon, and writes pixel counts
and acres by CDL class. Raw rasters are temporary; derived CSVs are committed.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
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


def cropland(code: int) -> bool:
    return 1 <= code <= 61 or 66 <= code <= 77 or 204 <= code <= 254


def get_raster(geometry, year: int, target: Path) -> None:
    xmin, ymin, xmax, ymax = geometry.bounds
    params = (
        f"SERVICE=wcs&VERSION=1.0.0&REQUEST=GetCoverage&COVERAGE=cdl_{year}&"
        f"CRS=epsg:5070&BBOX={xmin},{ymin},{xmax},{ymax}&RESX=30&RESY=30&FORMAT=gtiff"
    )
    subprocess.run([
        "curl", "--fail", "--silent", "--show-error", "--max-time", "300",
        "-o", str(target), f"{WCS}?{params}"
    ], check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hub", type=int, required=True)
    parser.add_argument("--ring", type=int, required=True, choices=range(1, 7))
    parser.add_argument("--years", default="2013:2024")
    args = parser.parse_args()
    if ":" in args.years:
        lo, hi = map(int, args.years.split(":"))
        years = range(lo, hi + 1)
    else:
        years = [int(x) for x in args.years.split(",")]

    rings = gpd.read_file(ROOT / "output" / "facility_rings_exclusive.gpkg")
    selected = rings[(rings.hub_id == args.hub) & (rings.ring_index == args.ring)].to_crs(5070)
    if len(selected) != 1:
        raise ValueError(f"Expected one exclusive ring polygon for hub {args.hub}, band {args.ring}")
    definition = selected.iloc[0]
    geometry = definition.geometry
    scratch = Path("/tmp") / f"cdl-hub-{args.hub:03d}-ring-{args.ring}"
    scratch.mkdir(parents=True, exist_ok=True)
    categories, outcomes = [], []

    for year in years:
        raster = scratch / f"cdl_{year}.tif"
        try:
            get_raster(geometry, year, raster)
            with rasterio.open(raster) as src:
                pixels, _ = mask(src, [mapping(geometry)], crop=True, filled=False)
                values = pixels[0].compressed().astype(int)
            counts = np.bincount(values, minlength=max(255, values.max() + 1))
            all_valid = int(counts[1:].sum())
            crop_pixels = int(counts[[code for code in range(len(counts)) if cropland(code)]].sum())
            soy_pixels = int(counts[5])
            for code, count in enumerate(counts):
                if count:
                    categories.append({
                        "hub_id": args.hub, "year": year, "ring_index": args.ring,
                        "inner_miles": definition.inner_miles, "outer_miles": definition.outer_miles,
                        "cdl_code": code, "pixel_count": int(count), "acres": count * PIXEL_ACRES,
                        "share_all_valid_pixels": count / all_valid if all_valid else None,
                        "is_soy": code == 5, "is_cropland": cropland(code),
                    })
            outcomes.append({
                "hub_id": args.hub, "year": year, "ring_index": args.ring,
                "inner_miles": definition.inner_miles, "outer_miles": definition.outer_miles,
                "soy_pixels": soy_pixels, "all_valid_pixels": all_valid, "cropland_pixels": crop_pixels,
                "soy_acres": soy_pixels * PIXEL_ACRES,
                "all_valid_acres": all_valid * PIXEL_ACRES,
                "cropland_acres": crop_pixels * PIXEL_ACRES,
                "soy_share_all_land": soy_pixels / all_valid if all_valid else None,
                "soy_share_cropland": soy_pixels / crop_pixels if crop_pixels else None,
            })
            print(f"completed hub {args.hub}, ring {args.ring}, year {year}", flush=True)
        finally:
            raster.unlink(missing_ok=True)

    out = ROOT / "batch-results" / f"hub_{args.hub:03d}"
    out.mkdir(parents=True, exist_ok=True)
    with (out / "crop_outcomes.csv").open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=outcomes[0].keys()); writer.writeheader(); writer.writerows(outcomes)
    with (out / "cdl_class_composition.csv").open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=categories[0].keys()); writer.writeheader(); writer.writerows(categories)


if __name__ == "__main__":
    main()
