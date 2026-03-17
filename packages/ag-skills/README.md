# Agricultural Data Analysis Skills

> AI-ready skills for downloading and analyzing US agricultural data using standard Python libraries.

This package provides a collection of skills for agricultural data analysis, including downloading field boundaries, soil data, weather data, satellite imagery, and performing exploratory data analysis.

## Skills Overview

### Data Download Skills

| Skill                 | Description                          |
| --------------------- | ------------------------------------ |
| `field-boundaries`    | USDA NASS Crop Sequence Boundaries   |
| `ssurgo-soil`         | USDA NRCS SSURGO soil data           |
| `nasa-power-weather`  | NASA POWER weather data              |
| `cdl-cropland`        | USDA NASS Cropland Data Layer        |
| `sentinel2-imagery`   | ESA Sentinel-2 satellite imagery     |
| `landsat-imagery`     | USGS Landsat satellite imagery       |
| `interactive-web-map` | Interactive web maps with Leaflet.js |

### Analysis Skills (EDA)

| Skill             | Description                                |
| ----------------- | ------------------------------------------ |
| `eda-explore`     | Data exploration with pandas               |
| `eda-visualize`   | Data visualization with matplotlib/seaborn |
| `eda-correlate`   | Correlation analysis                       |
| `eda-time-series` | Time series analysis                       |
| `eda-compare`     | Group comparisons and statistical tests    |

## Quick Start

### Install Dependencies

```bash
# Core dependencies
pip install geopandas pandas matplotlib requests

# For raster operations
pip install rasterio rasterstats

# For satellite imagery
pip install sentinelsat landsatxplore

# For statistical analysis
pip install scipy seaborn statsmodels
```

### Using Skills

Each skill is a standalone module. Import and use:

```python
# Example: Download field boundaries
from field_boundaries import download_fields

fields = download_fields(count=20, regions=['corn_belt'])
fields.to_file('my_fields.geojson')
```

## Dependency Chain

```
field-boundaries (REQUIRED FIRST)
    ├──> ssurgo-soil (needs field polygons)
    ├──> nasa-power-weather (needs field locations)
    ├──> cdl-cropland (uses fields for AOI)
    ├──> sentinel2-imagery (needs AOI)
    ├──> landsat-imagery (needs AOI)
    └──> interactive-web-map (visualizes fields)

eda-* skills (independent - work with any CSV)
```

## Environment Setup

For isolated environments, use UV:

```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Run skill in isolation
cd field-boundaries
uv venv .venv
source .venv/bin/activate
uv pip install -e .
```

## Data Sources

| Data             | Provider   | Format  |
| ---------------- | ---------- | ------- |
| Field Boundaries | USDA NASS  | GeoJSON |
| Soil             | USDA NRCS  | Tabular |
| Weather          | NASA POWER | NetCDF  |
| Crops            | USDA NASS  | GeoTIFF |
| Imagery          | ESA/USGS   | GeoTIFF |

All data is **public domain** or **free for research use**.

## License

See individual skill repositories for license information.

## Citation

```
USDA National Agricultural Statistics Service Cropland Data Layer. 2023.
Published crop-specific data layer [Online].
Available at https://nassgeodata.gmu.edu/CropScape/
```
