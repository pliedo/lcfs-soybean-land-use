#!/usr/bin/env python3
"""Build Beamer-ready priority figures from the completed CDL panel."""
from pathlib import Path
import warnings
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "clean" / "crop_outcomes_exclusive.csv"
GPKG = ROOT / "output" / "facility_rings_exclusive.gpkg"
OUT = ROOT / "output" / "figures" / "priority"
OUT.mkdir(parents=True, exist_ok=True)

BAND_LABELS = {
    1: "0–25", 2: "25–50", 3: "50–75",
    4: "75–100", 5: "100–125", 6: "125–150",
}
STYLES = {
    "classic": {
        "background": "#FFFFFF", "foreground": "#243447",
        "colors": ["#00429D", "#2E59A8", "#4771B2", "#5D8ABD", "#72A2C7", "#89BDD0"],
        "grid": "#D8DEE7",
    },
    "dark": {
        "background": "#101820", "foreground": "#F4F7FA",
        "colors": ["#FFB000", "#FF7C43", "#F95D6A", "#D45087", "#A05195", "#665191"],
        "grid": "#44515C",
    },
    "monochrome": {
        "background": "#FFFFFF", "foreground": "#111111",
        "colors": ["#111111", "#353535", "#595959", "#7D7D7D", "#A1A1A1", "#C5C5C5"],
        "grid": "#D0D0D0",
    },
}

def save_figure(fig, stem):
    fig.savefig(OUT / f"{stem}.png", dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
    fig.savefig(OUT / f"{stem}.pdf", bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)

def soybean_summary():
    d = pd.read_csv(DATA)
    d = d[d["year"].between(2014, 2024)].copy()
    s = (d.groupby(["year", "ring_index"], as_index=False)
           .agg(soy_pixels=("soy_pixels", "sum"),
                all_valid_pixels=("all_valid_pixels", "sum"),
                cropland_pixels=("cropland_pixels", "sum")))
    s["soy_share_all_land"] = s["soy_pixels"] / s["all_valid_pixels"]
    s["soy_share_cropland"] = s["soy_pixels"] / s["cropland_pixels"]
    s["distance_ring_miles"] = s["ring_index"].map(BAND_LABELS)
    s.to_csv(OUT / "soybean_share_by_ring_summary.csv", index=False)
    return s

def plot_trends(summary, style_name, style):
    fig, ax = plt.subplots(figsize=(12.8, 7.2))
    fig.patch.set_facecolor(style["background"])
    ax.set_facecolor(style["background"])
    for i, ring in enumerate(sorted(BAND_LABELS)):
        z = summary[summary["ring_index"] == ring]
        ax.plot(z["year"], 100 * z["soy_share_all_land"], color=style["colors"][i],
                linewidth=2.8, marker="o", markersize=4.8, label=f"{BAND_LABELS[ring]} miles")
    ax.set_xlabel("Year", fontsize=15)
    ax.set_ylabel("Soybean pixels (% of all valid land pixels)", fontsize=15)
    ax.set_xticks(range(2014, 2025, 2))
    ax.tick_params(labelsize=12, colors=style["foreground"])
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(style["foreground"])
    ax.xaxis.label.set_color(style["foreground"])
    ax.yaxis.label.set_color(style["foreground"])
    ax.grid(axis="y", color=style["grid"], linewidth=0.8, alpha=0.75)
    legend = ax.legend(title="Exclusive distance ring", ncol=2, frameon=False,
                       loc="upper left", fontsize=11, title_fontsize=11)
    for text in legend.get_texts():
        text.set_color(style["foreground"])
    legend.get_title().set_color(style["foreground"])
    ax.margins(x=0.015)
    fig.tight_layout()
    save_figure(fig, f"soybean_share_by_ring_{style_name}")

def state_boundaries(target_crs):
    url = "https://www2.census.gov/geo/tiger/GENZ2024/shp/cb_2024_us_state_20m.zip"
    try:
        states = gpd.read_file(url)
        states = states[(states["STATEFP"].astype(int) < 60) &
                        (~states["STUSPS"].isin(["AK", "HI", "PR"]))]
        return states.to_crs(target_crs)
    except Exception as exc:
        warnings.warn(f"State boundaries unavailable; continuing without them: {exc}")
        return None

def plot_map(rings, states, style_name, style):
    fig, ax = plt.subplots(figsize=(12.8, 7.2))
    fig.patch.set_facecolor(style["background"])
    ax.set_facecolor(style["background"])
    if states is not None:
        states.plot(ax=ax, facecolor=style["background"], edgecolor=style["grid"], linewidth=0.45)
    for i, ring in enumerate(sorted(BAND_LABELS, reverse=True)):
        z = rings[rings["ring_index"] == ring]
        z.plot(ax=ax, facecolor=style["colors"][i], edgecolor=style["colors"][i],
               linewidth=0.30, alpha=0.34)
    inner = rings[rings["ring_index"] == 1].copy()
    hubs = inner.copy()
    hubs["geometry"] = hubs.geometry.centroid
    hubs.plot(ax=ax, color=style["foreground"], markersize=8, alpha=0.85)
    ax.set_axis_off()
    ax.set_aspect("equal")
    handles = [Line2D([0], [0], color=style["colors"][i], lw=7, alpha=0.65,
                      label=f"{BAND_LABELS[ring]} miles")
               for i, ring in enumerate(sorted(BAND_LABELS, reverse=True))]
    handles.reverse()
    legend = ax.legend(handles=handles, title="Exclusive distance ring", frameon=False,
                       ncol=2, loc="lower left", fontsize=10.5, title_fontsize=11)
    for text in legend.get_texts():
        text.set_color(style["foreground"])
    legend.get_title().set_color(style["foreground"])
    fig.tight_layout(pad=0.2)
    save_figure(fig, f"crusher_catchment_rings_{style_name}")

def main():
    summary = soybean_summary()
    rings = gpd.read_file(GPKG)
    if "ring_index" not in rings.columns:
        if "ring_id" in rings.columns:
            rings = rings.rename(columns={"ring_id": "ring_index"})
        else:
            raise RuntimeError(f"No ring index field in {list(rings.columns)}")
    rings["ring_index"] = rings["ring_index"].astype(int)
    states = state_boundaries(rings.crs)
    for name, style in STYLES.items():
        plot_trends(summary, name, style)
        plot_map(rings, states, name, style)
    print(f"Wrote priority figures to {OUT}")

if __name__ == "__main__":
    main()
