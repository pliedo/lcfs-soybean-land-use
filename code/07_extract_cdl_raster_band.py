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
import time
import random
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.mask import mask
from shapely.geometry import box, mapping

ROOT = Path(__file__).resolve().parents[1]
WCS = "https://nassgeodata.gmu.edu/CropScapeService/wms_cdlall.cgi"
PIXEL_ACRES = 900 / 4046.8564224
MAX_TILE_METRES = 50000


def cropland(code: int) -> bool:
    return 1 <= code <= 61 or 66 <= code <= 77 or 204 <= code <= 254


def get_raster(geometry, year: int, target: Path) -> None:
    xmin, ymin, xmax, ymax = geometry.bounds
    params = (
        f"SERVICE=wcs&VERSION=1.0.0&REQUEST=GetCoverage&COVERAGE=cdl_{year}&"
        f"CRS=epsg:5070&BBOX={xmin},{ymin},{xmax},{ymax}&RESX=30&RESY=30&FORMAT=gtiff"
    )
    last_error = None
    for attempt in range(6):
        target.unlink(missing_ok=True)
        try:
            subprocess.run([
                "curl", "--fail", "--silent", "--show-error", "--max-time", "300",
                "-o", str(target), f"{WCS}?{params}"
            ], check=True)
            # The service can return a text error page with HTTP 200. Verify
            # the download is a readable GeoTIFF before accepting it.
            with rasterio.open(target):
                pass
            return
        except (subprocess.CalledProcessError, rasterio.errors.RasterioIOError) as exc:
            last_error = exc
            target.unlink(missing_ok=True)
            if attempt < 5:
                time.sleep((2 ** attempt) + random.uniform(0, 2))
    raise RuntimeError(f"CDL WCS download failed after 6 attempts for {year}: {last_error}")


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
    if len(selected) > 1:
        raise ValueError(f"Expected at most one exclusive ring polygon for hub {args.hub}, band {args.ring}")
    if len(selected) == 0:
        out = ROOT / "batch-results" / f"hub_{args.hub:03d}"
        out.mkdir(parents=True, exist_ok=True)
        zero = {"hub_id": args.hub, "year": None, "ring_index": args.ring,
                "inner_miles": (args.ring - 1) * 25, "outer_miles": args.ring * 25,
                "soy_pixels": 0, "all_valid_pixels": 0, "cropland_pixels": 0,
                "soy_acres": 0, "all_valid_acres": 0, "cropland_acres": 0,
                "soy_share_all_land": None, "soy_share_cropland": None}
        with (out / "crop_outcomes.csv").open("w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=zero.keys()); writer.writeheader()
            writer.writerows([{**zero, "year": year} for year in years])
        with (out / "cdl_class_composition.csv").open("w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=["hub_id", "year", "ring_index", "inner_miles", "outer_miles", "cdl_code", "pixel_count", "acres", "share_all_valid_pixels", "is_soy", "is_cropland"])
            writer.writeheader()
        print(f"hub {args.hub}, ring {args.ring} has zero exclusive area", flush=True)
        return
    definition = selected.iloc[0]
    geometry = definition.geometry
    scratch = Path("/tmp") / f"cdl-hub-{args.hub:03d}-ring-{args.ring}"
    scratch.mkdir(parents=True, exist_ok=True)
    categories, outcomes = [], []

    for year in years:
        xmin, ymin, xmax, ymax = geometry.bounds
        x_breaks = list(np.arange(xmin, xmax, MAX_TILE_METRES)) + [xmax]
        y_breaks = list(np.arange(ymin, ymax, MAX_TILE_METRES)) + [ymax]
        counts = np.zeros(256, dtype=np.int64)
        tile_number = 0

        for x0, x1 in zip(x_breaks[:-1], x_breaks[1:]):
            for y0, y1 in zip(y_breaks[:-1], y_breaks[1:]):
                tile_geometry = geometry.intersection(box(x0, y0, x1, y1))
                if tile_geometry.is_empty:
                    continue
                tile_number += 1
                raster = scratch / f"cdl_{year}_tile_{tile_number:03d}.tif"
                try:
                    get_raster(tile_geometry, year, raster)
                    with rasterio.open(raster) as src:
                        pixels, _ = mask(src, [mapping(tile_geometry)], crop=True, filled=False)
                        values = pixels[0].compressed().astype(int)
                    if values.size:
                        tile_counts = np.bincount(values, minlength=256)
                        if len(tile_counts) > len(counts):
                            counts = np.pad(counts, (0, len(tile_counts) - len(counts)))
                        counts[:len(tile_counts)] += tile_counts
                finally:
                    raster.unlink(missing_ok=True)

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
        print(f"completed hub {args.hub}, ring {args.ring}, year {year}, tiles {tile_number}", flush=True)

    out = ROOT / "batch-results" / f"hub_{args.hub:03d}"
    out.mkdir(parents=True, exist_ok=True)
    with (out / "crop_outcomes.csv").open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=outcomes[0].keys()); writer.writeheader(); writer.writerows(outcomes)
    with (out / "cdl_class_composition.csv").open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=categories[0].keys()); writer.writeheader(); writer.writerows(categories)


if __name__ == "__main__":
    main()
