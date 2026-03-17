#!/usr/bin/env python3
"""
SSURGO Soil Mapping with Satellite Basemap

Creates a 3x3 panel visualization of soil data for an agricultural field
in Grundy County, Iowa with satellite imagery basemap.

Requirements:
- Use real SSURGO polygons (not mock 3x3 grid)
- Natural Breaks (Jenks) classification with 3 classes
- Discrete choropleth colors (not gradients)
- 40-60% opacity for soil polygons over satellite imagery
- Green subtle polygon outlines
- Prominent field boundary
- Consistent extent across panels
- 30m headland buffer
"""

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import contextily as ctx
import numpy as np
from shapely.geometry import box, Polygon
from shapely.ops import unary_union
import warnings

warnings.filterwarnings("ignore")

SSURGO_GEOJSON = "data/SSURGO2/ssurgo_enriched_correct.geojson"
FIELD_BOUNDARY_GEOJSON = "data/SSURGO2/field_boundary.geojson"
HEADLAND_GEOJSON = "data/SSURGO2/headland_buffer.geojson"
OUTPUT_PATH = "data/SSURGO2/soil_maps_3x3.png"

ESRI_IMAGERY_URL = (
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
)
ESRI_ATTRIBUTION = "Esri World Imagery"

POLYGON_ALPHA = 0.5
POLYGON_EDGE_COLOR = "#228B22"


def natural_breaks(values, n_classes=3):
    """Natural Breaks (Jenks) classification - simplified implementation."""
    values = np.array(values)
    values = values[~np.isnan(values)]

    if len(values) < n_classes:
        return np.linspace(values.min(), values.max(), n_classes + 1)

    try:
        from sklearn.cluster import KMeans

        X = values.reshape(-1, 1)
        kmeans = KMeans(n_clusters=n_classes, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X)

        cluster_centers = kmeans.cluster_centers_.flatten()
        sorted_centers = np.sort(cluster_centers)

        breaks = []
        for center in sorted_centers:
            breaks.append(values[np.abs(values - center).argmin()])

        breaks = sorted(breaks)
        breaks.insert(0, values.min() - 0.001)
        breaks.append(values.max() + 0.001)

        return np.array(breaks[: n_classes + 1])
    except ImportError:
        return np.quantile(values, np.linspace(0, 1, n_classes + 1))


def classify_natural_breaks(values, n_classes=3):
    """Classify values into natural breaks classes."""
    breaks = natural_breaks(values, n_classes)

    classes = np.zeros(len(values), dtype=int)
    for i in range(1, len(breaks) - 1):
        classes[values > breaks[i]] = i

    return classes, breaks


def get_extent(gdf):
    """Get extent (minx, maxx, miny, maxy) from geodataframe in EPSG:3857."""
    bounds = gdf.total_bounds
    return (bounds[0], bounds[2], bounds[1], bounds[3])


def swap_coordinates(geom):
    """Swap (lat, lon) to (lon, lat) for a polygon or multipolygon."""
    from shapely.geometry import Polygon, MultiPolygon, LineString, Point

    if geom.is_empty:
        return geom

    if geom.geom_type == "Polygon":
        return Polygon([(lon, lat) for lat, lon in geom.exterior.coords])
    elif geom.geom_type == "MultiPolygon":
        return MultiPolygon(swap_coordinates(p) for p in geom.geoms)
    return geom


def load_ssurgo_data(field_boundary_geom):
    """Load real SSURGO polygons, clip to field boundary, and aggregate properties by mukey."""
    ssurgo = gpd.read_file(SSURGO_GEOJSON)
    print(f"Loaded {len(ssurgo)} SSURGO polygons")

    # Fix: coordinates are in (lat, lon) order, need to swap to (lon, lat)
    ssurgo["geometry"] = ssurgo["geometry"].apply(swap_coordinates)
    ssurgo = ssurgo.set_crs("EPSG:4326")

    # Create field boundary GeoDataFrame for clipping
    field_gdf = gpd.GeoDataFrame(geometry=[field_boundary_geom], crs="EPSG:4326")

    # Clip SSURGO polygons to field boundary
    print("Clipping SSURGO polygons to field boundary...")
    clipped = gpd.overlay(ssurgo, field_gdf, how="intersection")
    print(f"Clipped to {len(clipped)} polygons within field")

    mukey_props = (
        clipped.groupby("mukey")
        .agg(
            {
                "om_r": "mean",
                "ph1to1h2o_r": "mean",
                "awc_r": "mean",
                "claytotal_r": "mean",
                "sandtotal_r": "mean",
                "cec7_r": "mean",
            }
        )
        .reset_index()
    )

    mukey_props.columns = ["mukey", "om", "ph", "awc", "clay", "sand", "cec"]
    mukey_props["mukey"] = mukey_props["mukey"].astype(str)

    ssurgo_merged = clipped.merge(mukey_props, on="mukey", how="left")

    # Dissolve by mukey (may have multiple polygons per mukey after clipping)
    dissolved = ssurgo_merged.dissolve(by="mukey", as_index=False)
    dissolved = dissolved.reset_index(drop=True)

    print(f"Dissolved to {len(dissolved)} unique soil map units within field")
    print(f"Bounds (WGS84): {dissolved.total_bounds}")

    return dissolved


def load_field_boundary():
    """Load field boundary from GeoJSON."""
    fb = gpd.read_file(FIELD_BOUNDARY_GEOJSON)
    print(f"Loaded field boundary: {len(fb)} polygon(s)")
    return fb.geometry[0]


def load_headland_buffer():
    """Load headland buffer from GeoJSON."""
    hb = gpd.read_file(HEADLAND_GEOJSON)
    print(f"Loaded headland buffer: {len(hb)} polygon(s)")
    return hb.geometry[0]


def add_satellite_basemap(ax, extent=None, zoom="auto"):
    """Add satellite basemap to matplotlib axis using direct Esri tile URL.

    Sets extent BEFORE adding basemap to ensure proper tile loading.
    """
    # Set extent FIRST so contextily knows what tiles to fetch
    if extent is not None:
        ax.set_xlim(extent[0], extent[1])
        ax.set_ylim(extent[2], extent[3])

    # Add basemap after setting extent
    try:
        ctx.add_basemap(
            ax,
            crs="EPSG:3857",
            source=ESRI_IMAGERY_URL,
            zoom=zoom,
            attribution=ESRI_ATTRIBUTION,
        )
        print("  Added Esri World Imagery basemap")
    except Exception as e:
        print(f"  Warning: Could not add Esri satellite basemap: {e}")
        try:
            ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)
            print("  Fallback: Added OpenStreetMap basemap")
        except Exception as e2:
            print(f"  ERROR: Could not add fallback basemap: {e2}")


def plot_field_boundary(ax, field_boundary, headland=None):
    """Plot field boundary with optional headland buffer."""
    if headland is not None:
        headland_gdf = gpd.GeoDataFrame(geometry=[headland], crs="EPSG:4326")
        headland_proj = headland_gdf.to_crs("EPSG:3857")
        headland_proj.plot(
            ax=ax, facecolor="none", edgecolor="red", linewidth=2.5, linestyle="--", zorder=4
        )

    field_gdf = gpd.GeoDataFrame(geometry=[field_boundary], crs="EPSG:4326")
    field_proj = field_gdf.to_crs("EPSG:3857")
    field_proj.plot(ax=ax, facecolor="none", edgecolor="black", linewidth=2.5, zorder=5)


def create_legend_elements(breaks, colors):
    """Create legend elements for natural breaks classes."""
    labels = ["Low", "Medium", "High"]

    patches = []
    for i, (color, label) in enumerate(zip(colors, labels)):
        if i < len(breaks) - 1:
            label_text = f"{label}: {breaks[i]:.2f}-{breaks[i + 1]:.2f}"
        else:
            label_text = label
        patches.append(mpatches.Patch(facecolor=color, edgecolor="black", label=label_text))

    return patches


def plot_soil_map(
    ax,
    soil_gdf,
    column,
    title,
    base_colors,
    field_boundary=None,
    headland=None,
    extent=None,
    show_legend=True,
):
    """Plot a soil property map with satellite basemap and natural breaks classification."""
    soil_proj = soil_gdf.to_crs("EPSG:3857")

    values = soil_proj[column].values
    classes, breaks = classify_natural_breaks(values, n_classes=3)
    soil_proj = soil_proj.copy()
    soil_proj["class"] = classes

    cmap = mcolors.ListedColormap(base_colors)

    add_satellite_basemap(ax, extent=extent)

    soil_proj.plot(
        column="class",
        ax=ax,
        cmap=cmap,
        alpha=POLYGON_ALPHA,
        edgecolor=POLYGON_EDGE_COLOR,
        linewidth=0.8,
        legend=False,
        vmin=0,
        vmax=2,
    )

    if field_boundary is not None:
        plot_field_boundary(ax, field_boundary, headland)

    if show_legend:
        legend_patches = create_legend_elements(breaks, base_colors)
        ax.legend(
            handles=legend_patches,
            loc="lower right",
            fontsize=7,
            title=f"{title}\n(Natural Breaks)",
            title_fontsize=7,
            framealpha=0.9,
        )

    ax.set_title(title, fontsize=10, fontweight="bold")
    ax.set_axis_off()


def create_3x3_soil_maps():
    """Create 3x3 panel visualization of soil properties."""
    print("Loading field boundary...")
    field_boundary = load_field_boundary()

    print("Loading headland buffer...")
    headland = load_headland_buffer()

    print("Loading and clipping SSURGO data...")
    soil_gdf = load_ssurgo_data(field_boundary)

    soil_proj = soil_gdf.to_crs("EPSG:3857")
    common_extent = get_extent(soil_proj)
    print(f"Common extent: {common_extent}")

    print("Creating 3x3 visualization...")
    fig, axes = plt.subplots(3, 3, figsize=(16, 16))
    fig.suptitle(
        "SSURGO Soil Analysis - Grundy County, Iowa (~81 acres)\nNatural Breaks (Jenks) Classification - 3 Classes",
        fontsize=14,
        fontweight="bold",
    )

    om_colors = ["#d9f0a3", "#78c679", "#238443"]
    ph_colors = ["#d73027", "#fee08b", "#1a9850"]
    awc_colors = ["#deebf7", "#9ecae1", "#3182bd"]
    clay_colors = ["#fee6ce", "#fd8d3c", "#d94801"]
    sand_colors = ["#e1bee7", "#ab47bc", "#6a1b9a"]
    cec_colors = ["#e0e0e0", "#7570b3", "#3f007d"]

    ax = axes[0, 0]
    field_gdf = gpd.GeoDataFrame(geometry=[field_boundary], crs="EPSG:4326")
    field_proj = field_gdf.to_crs("EPSG:3857")
    add_satellite_basemap(ax, extent=common_extent)
    field_proj.plot(ax=ax, facecolor="none", edgecolor="black", linewidth=2.5, zorder=5)
    ax.set_title("Field Boundary", fontsize=10, fontweight="bold")
    ax.set_axis_off()

    ax = axes[0, 1]
    add_satellite_basemap(ax, extent=common_extent)
    soil_proj = soil_gdf.to_crs("EPSG:3857")
    soil_proj.plot(
        ax=ax,
        column="mukey",
        cmap="tab10",
        alpha=POLYGON_ALPHA,
        edgecolor=POLYGON_EDGE_COLOR,
        linewidth=0.8,
        legend=False,
    )
    plot_field_boundary(ax, field_boundary)
    ax.set_title("SSURGO Soil Map Units", fontsize=10, fontweight="bold")
    ax.set_axis_off()

    ax = axes[0, 2]
    plot_soil_map(
        ax,
        soil_gdf,
        "om",
        "Organic Matter (%)",
        om_colors,
        field_boundary=field_boundary,
        headland=headland,
        extent=common_extent,
    )

    ax = axes[1, 0]
    plot_soil_map(
        ax,
        soil_gdf,
        "ph",
        "Soil pH",
        ph_colors,
        field_boundary=field_boundary,
        headland=headland,
        extent=common_extent,
    )

    ax = axes[1, 1]
    plot_soil_map(
        ax,
        soil_gdf,
        "awc",
        "Available Water Capacity (in/in)",
        awc_colors,
        field_boundary=field_boundary,
        headland=headland,
        extent=common_extent,
    )

    ax = axes[1, 2]
    plot_soil_map(
        ax,
        soil_gdf,
        "clay",
        "Clay (%)",
        clay_colors,
        field_boundary=field_boundary,
        headland=headland,
        extent=common_extent,
    )

    ax = axes[2, 0]
    plot_soil_map(
        ax,
        soil_gdf,
        "sand",
        "Sand (%)",
        sand_colors,
        field_boundary=field_boundary,
        headland=headland,
        extent=common_extent,
    )

    ax = axes[2, 1]
    add_satellite_basemap(ax, extent=common_extent)

    soil_proj = soil_gdf.to_crs("EPSG:3857")
    values = soil_proj["om"].values
    classes, breaks = classify_natural_breaks(values, n_classes=3)
    soil_proj = soil_proj.copy()
    soil_proj["class"] = classes

    soil_proj.plot(
        column="class",
        ax=ax,
        cmap=mcolors.ListedColormap(om_colors),
        alpha=POLYGON_ALPHA,
        edgecolor=POLYGON_EDGE_COLOR,
        linewidth=0.8,
        legend=False,
        vmin=0,
        vmax=2,
    )

    headland_gdf = gpd.GeoDataFrame(geometry=[headland], crs="EPSG:4326")
    headland_proj = headland_gdf.to_crs("EPSG:3857")
    headland_proj.plot(
        ax=ax, facecolor="none", edgecolor="red", linewidth=2.5, linestyle="--", zorder=4
    )

    field_gdf = gpd.GeoDataFrame(geometry=[field_boundary], crs="EPSG:4326")
    field_proj = field_gdf.to_crs("EPSG:3857")
    field_proj.plot(ax=ax, facecolor="none", edgecolor="black", linewidth=2.5, zorder=5)

    legend_patches = create_legend_elements(breaks, om_colors)
    ax.legend(
        handles=legend_patches,
        loc="lower right",
        fontsize=7,
        title="OM (%) - Headland\n(Natural Breaks)",
        title_fontsize=7,
        framealpha=0.9,
    )

    ax.set_title(f"Headland Buffer (30m) with OM", fontsize=10, fontweight="bold")
    ax.set_axis_off()

    ax = axes[2, 2]
    plot_soil_map(
        ax,
        soil_gdf,
        "cec",
        "CEC7 (meq/100g)",
        cec_colors,
        field_boundary=field_boundary,
        headland=headland,
        extent=common_extent,
    )

    plt.tight_layout()

    plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight", facecolor="white", edgecolor="none")
    print(f"Saved: {OUTPUT_PATH}")

    plt.close()

    return soil_gdf, field_boundary, headland


if __name__ == "__main__":
    soil_gdf, field_boundary, headland = create_3x3_soil_maps()

    print("\nSummary:")
    print(f"  Soil map units: {len(soil_gdf)}")
    print(f"  Properties mapped: OM, pH, AWC, Clay, Sand, CEC")
    print(f"  Classification: Natural Breaks (Jenks) with 3 classes")
    print(f"  Polygon alpha: {POLYGON_ALPHA}")
    print(f"  Polygon edge color: {POLYGON_EDGE_COLOR}")
