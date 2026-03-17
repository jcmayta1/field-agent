---
name: landsat-imagery
description: Search, download, and process Landsat 8/9 satellite imagery for agricultural fields. Use when the user needs to acquire Landsat scenes, calculate vegetation indices (NDVI/EVI), or perform long-term remote sensing analysis using standard Python libraries (landsatxplore, rasterio).
version: 1.0.0
author: Boreal Bytes
tags: [landsat, usgs, satellite, ndvi, rasterio, remote-sensing, geospatial]
---

# Skill: landsat-imagery

## Description

Search the USGS Landsat archive and download Landsat 8/9 imagery for agricultural field boundaries. This skill teaches standard open-source libraries — `landsatxplore` for scene search/download via the USGS M2M API, and `rasterio` for raster I/O, clipping, and vegetation index calculation. All examples use field boundaries from the `field-boundaries` skill as the area of interest (AOI).

## When to Use This Skill

- **Acquiring Landsat imagery**: Search and download scenes from USGS EarthExplorer
- **Vegetation indices**: Calculate NDVI, EVI, or other band-math indices
- **Long-term trends**: Landsat archive goes back to 1984 (30 m, 16-day revisit)
- **Field-level analysis**: Clip scenes to field boundaries and extract zonal statistics
- **Cross-sensor comparison**: Compare Landsat 30 m with Sentinel-2 10 m data

## Prerequisites

```bash
# Install UV if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh
```

You also need a **free USGS EarthExplorer account**:

1. Register at <https://ers.cr.usgs.gov/register>
2. Store credentials as environment variables (see Environment Variables below)

## Example Data

Sample metadata is included in the `examples/` directory:

- `examples/sample_scene_metadata.json` — Real Landsat 8/9 scene metadata for the field-boundaries sample AOI
- `examples/README.md` — Description of example files and usage

Use the field-boundaries sample data as AOI for all examples:

```python
import geopandas as gpd

fields = gpd.read_file('field-boundaries/examples/sample_2_fields.geojson')
print(fields[['field_id', 'area_acres', 'crop_name']])

# Output:
#           field_id  area_acres crop_name
# 0  271623002471299    3.704844      Corn
# 1  271623001561551    6.408551      Corn
```

## Quick Start

```bash
# Search Landsat scenes and calculate NDVI in one shot
uv run --with landsatxplore --with rasterio --with geopandas --with numpy python << 'EOF'
from landsatxplore.api import API
import geopandas as gpd
import os

api = API(os.environ['USGS_USERNAME'], os.environ['USGS_PASSWORD'])

fields = gpd.read_file('field-boundaries/examples/sample_2_fields.geojson')
bbox = fields.total_bounds

scenes = api.search(
    dataset='landsat_ot_c2_l2',
    bbox=(bbox[1], bbox[0], bbox[3], bbox[2]),
    start_date='2024-06-01',
    end_date='2024-08-31',
    max_cloud_cover=20
)

print(f"Found {len(scenes)} scenes")
for scene in scenes[:3]:
    print(f"  {scene['display_id']} — cloud: {scene['cloud_cover']}%")

api.logout()
EOF
```

## Installation (Isolated Environment)

```bash
cd landsat-imagery
uv venv .venv
source .venv/bin/activate
uv pip install landsatxplore rasterio geopandas numpy matplotlib shapely
```

## Key Bands (Landsat 8/9 OLI)

| Band | Name            | Wavelength (nm) | Resolution | Agricultural Use       |
| ---- | --------------- | --------------- | ---------- | ---------------------- |
| B2   | Blue            | 450-510         | 30 m       | Water penetration      |
| B3   | Green           | 530-590         | 30 m       | Vegetation vigor       |
| B4   | Red             | 640-670         | 30 m       | Chlorophyll absorption |
| B5   | NIR             | 850-880         | 30 m       | Vegetation biomass     |
| B6   | SWIR1           | 1570-1650       | 30 m       | Moisture content       |
| B7   | SWIR2           | 2110-2290       | 30 m       | Mineral / dry veg      |
| B10  | Thermal (TIRS1) | 10600-11190     | 100 m      | Surface temperature    |

## Usage Examples

### Example 1: Search and Download Scenes with landsatxplore

```python
from landsatxplore.api import API
from landsatxplore.earthexplorer import EarthExplorer
import geopandas as gpd
import os

api = API(os.environ['USGS_USERNAME'], os.environ['USGS_PASSWORD'])
ee = EarthExplorer(os.environ['USGS_USERNAME'], os.environ['USGS_PASSWORD'])

fields = gpd.read_file('field-boundaries/examples/sample_2_fields.geojson')
bbox = fields.total_bounds

scenes = api.search(
    dataset='landsat_ot_c2_l2',
    bbox=(bbox[1], bbox[0], bbox[3], bbox[2]),
    start_date='2024-06-01',
    end_date='2024-08-31',
    max_cloud_cover=20
)
print(f"Found {len(scenes)} scenes")

if scenes:
    best = sorted(scenes, key=lambda s: s['cloud_cover'])[0]
    print(f"Downloading: {best['display_id']}")
    ee.download(best['entity_id'], output_dir='data/landsat/')

api.logout()
ee.logout()
```

### Example 2: Calculate NDVI with rasterio + numpy

```python
import rasterio
import numpy as np
from pathlib import Path

def calculate_ndvi(red_path: str, nir_path: str, output_path: str) -> str:
    """Calculate NDVI = (NIR - Red) / (NIR + Red)."""
    with rasterio.open(red_path) as red_src:
        red = red_src.read(1).astype('float32')
        profile = red_src.profile.copy()

    with rasterio.open(nir_path) as nir_src:
        nir = nir_src.read(1).astype('float32')

    denominator = nir + red
    ndvi = np.where(denominator > 0, (nir - red) / denominator, np.nan)

    profile.update(dtype='float32', count=1, compress='lzw', nodata=np.nan)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(ndvi, 1)

    print(f"NDVI saved: {output_path}")
    return output_path
```

### Example 3: Zonal Statistics per Field

```python
import rasterio
from rasterio.mask import mask
import geopandas as gpd
import numpy as np
import pandas as pd
import json

def zonal_stats(raster_path: str, fields_path: str) -> pd.DataFrame:
    fields = gpd.read_file(fields_path)
    results = []

    with rasterio.open(raster_path) as src:
        for idx, field in fields.iterrows():
            geom = [json.loads(gpd.GeoSeries([field.geometry]).to_json())['features'][0]['geometry']]
            out_image, _ = mask(src, geom, crop=True, nodata=np.nan)
            data = out_image[0]
            valid = data[~np.isnan(data)]

            if len(valid) > 0:
                results.append({
                    'field_id': field.get('field_id', f'field_{idx}'),
                    'mean': float(np.mean(valid)),
                    'std': float(np.std(valid)),
                    'min': float(np.min(valid)),
                    'max': float(np.max(valid)),
                })

    return pd.DataFrame(results)
```

## Data Source

- **Provider**: USGS / NASA
- **Dataset**: Landsat 8/9 Collection 2 Level-2 Science Products
- **Access**: USGS EarthExplorer via `landsatxplore` (M2M API)
- **Archive**: 1984-present (Landsat 4-9)
- **Resolution**: 30 m multispectral, 100 m thermal
- **Revisit**: 16 days (8 days combined L8 + L9)

## Comparison with Sentinel-2

| Feature    | Landsat 8/9          | Sentinel-2   |
| ---------- | -------------------- | ------------ |
| Resolution | 30 m                 | 10-60 m      |
| Revisit    | 16 days (8 combined) | 5 days       |
| Archive    | 1984-present         | 2015-present |

## Environment Variables

| Variable      | Required | Description                 |
| ------------- | -------- | --------------------------- |
| USGS_USERNAME | Yes      | USGS EarthExplorer username |
| USGS_PASSWORD | Yes      | USGS EarthExplorer password |

```bash
export USGS_USERNAME='your_username'
export USGS_PASSWORD='your_password'
```

## Resources

- [USGS EarthExplorer](https://earthexplorer.usgs.gov/)
- [landsatxplore documentation](https://github.com/yannforget/landsatxplore)
- [rasterio documentation](https://rasterio.readthedocs.io/)
- [Landsat Collection 2 Level-2 Science Products](https://www.usgs.gov/landsat-missions/landsat-collection-2-level-2-science-products)
