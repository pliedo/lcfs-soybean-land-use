#!/usr/bin/env python3
"""Build one exclusive CDL distance band with the USDA ImageServer.

This is a checkpointed command-line fallback for environments where the
legacy CropScape endpoint is unreliable. It queries the same public CDL image
service used by the R workflow, saves every cumulative polygon response, and
then differences adjacent cumulative catchments into true 25-mile rings.

Example:
  PYTHONPATH=/tmp/cdl_geo python code/03_extract_cdl_image_server.py --ring 1
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import subprocess
import time
from pathlib import Path

import geopandas as gpd

ROOT = Path(__file__).resolve().parents[1]
SERVICE = "https://pdi.scinet.usda.gov/image/rest/services/CDL_WM/ImageServer/computeHistograms"
PIXEL_ACRES = 900 / 4046.8564224


def timestamp(year: int) -> str:
    return str(int(dt.datetime(year, 1, 1, tzinfo=dt.timezone.utc).timestamp() * 1000))


def ring_payload(geometry) -> dict:
    projected = gpd.GeoSeries([geometry], crs=5070).to_crs(3857).iloc[0]
    polygons = [projected] if projected.geom_type == "Polygon" else list(projected.geoms)
    rings = []
    for polygon in polygons:
        rings.append([list(point) for point in polygon.exterior.coords])
        rings.extend([[list(point) for point in hole.coords] for hole in polygon.interiors])
    return {"rings": rings, "spatialReference": {"wkid": 3857}}


def fetch_histogram(payload: dict, year: int, cache_path: Path) -> dict:
    if cache_path.exists():
        return json.loads(cache_path.read_text())
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    geometry_path = cache_path.with_suffix(".geometry.json")
    temporary = cache_path.with_suffix(".download.json")
    geometry_path.write_text(json.dumps(payload, separators=(",", ":")))
    for attempt in range(1, 6):
        result = subprocess.run([
            "curl", "--fail", "--silent", "--show-error", "--max-time", "90", "-G", SERVICE,
            "--data-urlencode", "f=json",
            "--data-urlencode", "geometryType=esriGeometryPolygon",
            "--data-urlencode", f"geometry@{geometry_path}",
            "--data-urlencode", f"time={timestamp(year)}",
            "-o", str(temporary),
        ], capture_output=True, text=True)
        if result.returncode == 0 and temporary.exists():
            data = json.loads(temporary.read_text())
            if data.get("histograms"):
                temporary.replace(cache_path)
                geometry_path.unlink(missing_ok=True)
                return data
            problem = data.get("error", {}).get("message", "No histogram")
        else:
            problem = result.stderr.strip() or f"curl exit {result.returncode}"
        time.sleep(attempt * 4)
    raise RuntimeError(f"CDL request failed for {year}: {problem}")


def counts(data: dict) -> dict[int, float]:
    histogram = data["histograms"][0]
    start = round(float(histogram["min"]) + 0.5)
    return {start + i: float(count) for i, count in enumerate(histogram["counts"])}


def cropland(value: int) -> bool:
    return 1 <= value <= 61 or 66 <= value <= 77 or 204 <= value <= 254


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ring", type=int, required=True, choices=range(1, 7))
    parser.add_argument("--years", default="2013:2024")
    parser.add_argument("--hubs", default="all")
    parser.add_argument("--pause", type=float, default=1.25)
    args = parser.parse_args()
    if ":" in args.years:
        lo, hi = map(int, args.years.split(":"))
        years = list(range(lo, hi + 1))
    else:
        years = [int(x) for x in args.years.split(",")]

    rings = gpd.read_file(ROOT / "output" / "facility_rings_exclusive.gpkg")
    hub_ids = sorted(rings.hub_id.unique()) if args.hubs == "all" else [int(x) for x in args.hubs.split(",")]
    target = rings[rings.hub_id.isin(hub_ids) & (rings.ring_index <= args.ring)]
    cumulative = {(hub, index): target[(target.hub_id == hub) & (target.ring_index <= index)].geometry.union_all()
                  for hub in hub_ids for index in set([args.ring, max(1, args.ring - 1)])}

    rows = []
    total = len(hub_ids) * len(years)
    task = 0
    for hub in hub_ids:
        for year in years:
            task += 1
            high_cache = ROOT / "data" / "raw" / "cdl_image_cache" / str(year) / f"hub_{hub:03d}_outer_{args.ring:03d}.json"
            high = counts(fetch_histogram(ring_payload(cumulative[(hub, args.ring)]), year, high_cache))
            low = {}
            if args.ring > 1:
                low_cache = ROOT / "data" / "raw" / "cdl_image_cache" / str(year) / f"hub_{hub:03d}_outer_{args.ring - 1:03d}.json"
                low = counts(fetch_histogram(ring_payload(cumulative[(hub, args.ring - 1)]), year, low_cache))
            net = {code: high.get(code, 0) - low.get(code, 0) for code in set(high) | set(low)}
            soy = net.get(5, 0) * PIXEL_ACRES
            all_valid = sum(value for code, value in net.items() if code != 0) * PIXEL_ACRES
            crop = sum(value for code, value in net.items() if cropland(code)) * PIXEL_ACRES
            definition = rings[(rings.hub_id == hub) & (rings.ring_index == args.ring)].iloc[0]
            rows.append({"hub_id": hub, "year": year, "ring_index": args.ring,
                         "inner_miles": definition.inner_miles, "outer_miles": definition.outer_miles,
                         "soy_acres": soy, "all_valid_acres": all_valid, "cropland_acres": crop,
                         "soy_share_all_land": soy / all_valid if all_valid else None,
                         "soy_share_cropland": soy / crop if crop else None})
            print(f"[{task}/{total}] hub {hub}, {year}, ring {args.ring}", flush=True)
            time.sleep(args.pause)

    out = ROOT / "data" / "clean" / f"crop_outcomes_exclusive_ring_{args.ring}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=rows[0].keys())
        writer.writeheader(); writer.writerows(rows)
    print(f"Wrote {out} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
