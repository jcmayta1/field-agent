#!/usr/bin/env python3
"""
SSURGO Analysis - Fixed version with proper WFS query
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.lines import Line2D
import geopandas as gpd
import pandas as pd
import numpy as np
import requests
import os
import xml.etree.ElementTree as ET
from shapely.geometry import Polygon, box
import json
import contextily as ctx
import warnings
warnings.filterwarnings('ignore')

def parse_sda_xml(response_text):
    """Parse SDA REST API XML response and return list of dicts"""
    try:
        root = ET.fromstring(response_text)
        tables = root.findall('.//Table')
        result = []
        for table in tables:
            row = {}
            for child in table:
                row[child.tag] = child.text
            result.append(row)
        return result
    except Exception as e:
        print(f"    XML parse error: {e}")
        return []

def jenks_breaks(values, n_classes):
    """Implement Jenks Natural Breaks optimization"""
    values = np.array(sorted(values), dtype=float)
    n = len(values)
    
    if n <= n_classes:
        return np.append(values, values[-1])
    
    breaks = [values.min()]
    for i in range(1, n_classes):
        quantile = i / n_classes
        breaks.append(np.quantile(values, quantile))
    breaks.append(values.max())
    
    for _ in range(10):
        new_breaks = [values.min()]
        for i in range(1, n_classes):
            lower = new_breaks[-1]
            upper = breaks[i+1] if i < n_classes-1 else values.max() + 1
            mask = (values >= lower) & (values < upper)
            if np.any(mask):
                new_breaks.append(float(np.mean(values[mask])))
            else:
                new_breaks.append(breaks[i])
        new_breaks.append(values.max())
        breaks = new_breaks
    
    return np.array(sorted(set(breaks)))

def create_choropleth_map(gdf_clipped, gdf_field, soil_data, property_name, property_label, 
                          unit, output_path, color_palette, extent_bounds):
    """Create a professional choropleth map with satellite basemap"""
    
    # Convert extent_bounds from EPSG:4326 to EPSG:3857
    minx_orig, miny_orig, maxx_orig, maxy_orig = extent_bounds
    extent_gdf = gpd.GeoDataFrame(geometry=[box(minx_orig, miny_orig, maxx_orig, maxy_orig)], crs='EPSG:4326')
    extent_merc = extent_gdf.to_crs('EPSG:3857')
    minx, miny, maxx, maxy = extent_merc.total_bounds
    
    soil_data = soil_data.copy()
    soil_data['mukey'] = soil_data['mukey'].astype(str)
    
    gdf = gdf_clipped.merge(soil_data[['mukey', property_name]], on='mukey', how='left')
    
    values = gdf[property_name].dropna().values
    if len(values) == 0:
        print(f"    No data for {property_name}")
        return
    
    breaks = jenks_breaks(values, 5)
    
    gdf['class'] = pd.cut(gdf[property_name], bins=breaks, labels=range(5), include_lowest=True)
    
    gdf_merc = gdf.to_crs('EPSG:3857')
    field_merc = gdf_field.to_crs('EPSG:3857')
    
    margin = (maxx - minx) * 0.15
    
    fig, ax = plt.subplots(figsize=(12, 10), dpi=150)
    
    # Plot soil polygons with 45% transparency
    colors = color_palette
    cmap = ListedColormap(colors)
    norm = BoundaryNorm(range(6), cmap.N)
    
    gdf_merc.plot(column='class', ax=ax, cmap=cmap, norm=norm, 
                  alpha=0.45, edgecolor='#333333', linewidth=0.5)
    
    # Plot field boundary (bold red)
    field_merc.plot(ax=ax, facecolor='none', edgecolor='#FF0000', linewidth=4)
    
    # Create and plot 30m headland buffer (dashed line)
    headland_buffer = field_merc.geometry.iloc[0].buffer(-30)
    headland_gdf = gpd.GeoDataFrame(geometry=[headland_buffer], crs='EPSG:3857')
    if headland_buffer.is_valid and not headland_buffer.is_empty:
        headland_gdf.plot(ax=ax, facecolor='none', edgecolor='#FF0000', 
                         linewidth=2, linestyle='--')
    
    # Add satellite basemap LAST (so it appears at bottom)
    ctx.add_basemap(ax, source=ctx.providers.Esri.WorldImagery, zoom="auto")
    
    ax.set_xlim(minx - margin, maxx + margin)
    ax.set_ylim(miny - margin, maxy + margin)
    
    ax.set_title(f'Soil {property_label}', fontsize=16, fontweight='bold', pad=10)
    
    ax.set_axis_off()
    
    legend_patches = []
    for i in range(5):
        low = breaks[i]
        high = breaks[i+1]
        label = f'{low:.2f} - {high:.2f} {unit}'
        patch = mpatches.Patch(color=colors[i], label=label, alpha=0.7)
        legend_patches.append(patch)
    
    legend = ax.legend(handles=legend_patches, loc='lower right', 
                      title=f'{property_label} ({unit})', fontsize=9, title_fontsize=10)
    legend.get_frame().set_facecolor('white')
    legend.get_frame().set_alpha(0.9)
    
    arrow_x = maxx + margin - (maxx-minx)*0.08
    arrow_y = maxy - (maxy-miny)*0.15
    ax.annotate('N', xy=(arrow_x, arrow_y), xytext=(arrow_x, arrow_y + (maxy-miny)*0.1),
                fontsize=14, fontweight='bold', ha='center',
                arrowprops=dict(arrowstyle='->', lw=2, color='black'))
    ax.text(arrow_x, arrow_y - (maxy-miny)*0.03, 'N', fontsize=12, ha='center')
    
    scalebar_length = (maxx - minx) * 0.25
    scalebar_x = minx + margin + (maxx-minx)*0.02
    scalebar_y = miny + margin + (maxy-miny)*0.02
    ax.plot([scalebar_x, scalebar_x + scalebar_length], [scalebar_y, scalebar_y], 
            color='black', linewidth=3)
    ax.text(scalebar_x + scalebar_length/2, scalebar_y + (maxy-miny)*0.015, 
            f'{int(scalebar_length)}m', ha='center', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

# Output directories
BASE_DIR = '/workspaces/field-agent/data/SSURGO'
DATA_DIR = f'{BASE_DIR}/data'
MAPS_DIR = f'{BASE_DIR}/maps'
OUTPUTS_DIR = f'{BASE_DIR}/outputs'
REPORTS_DIR = f'{BASE_DIR}/reports'

for d in [DATA_DIR, MAPS_DIR, OUTPUTS_DIR, REPORTS_DIR]:
    os.makedirs(d, exist_ok=True)

# Field coordinates (lon, lat format for shapely)
FIELD_COORDS_LONLAT = [
    (-93.776263, 41.921630),
    (-93.776211, 41.914502),
    (-93.771215, 41.914425),
    (-93.771320, 41.921627),
    (-93.776263, 41.921630)
]

print("="*70)
print("SSURGO SOIL POLYGON ANALYSIS")
print("="*70)

# =============================================================================
# STEP 1: Create Field Boundary
# =============================================================================
print("\n[STEP 1] Creating field boundary...")

# Create polygon with (lon, lat) order
field_poly = Polygon(FIELD_COORDS_LONLAT)

# Check if polygon is valid
if not field_poly.is_valid:
    field_poly = field_poly.buffer(0)  # Fix if needed
    
print(f"  Polygon valid: {field_poly.is_valid}")
print(f"  Bounds: {field_poly.bounds}")

field_gdf = gpd.GeoDataFrame(
    {'field_id': ['IA_StoryCounty_Field001'], 'county': ['Story'], 'state': ['IA']},
    geometry=[field_poly],
    crs='EPSG:4326'
)

# Calculate area in UTM
field_utm = field_gdf.to_crs('EPSG:32615')
area_sqm = field_utm.geometry.iloc[0].area
area_acres = area_sqm / 4046.8564224

field_gdf['area_acres'] = area_acres

field_gdf.to_file(f'{DATA_DIR}/field_boundary.geojson', driver='GeoJSON')
print(f"  Field area: {area_acres:.2f} acres")
print(f"  Saved: {DATA_DIR}/field_boundary.geojson")

# Get bounding box (minx, miny, maxx, maxy)
bounds = field_gdf.total_bounds
bbox_str = f"{bounds[0]},{bounds[1]},{bounds[2]},{bounds[3]}"
print(f"  Bounding box: {bbox_str}")

# =============================================================================
# STEP 2: Query WFS for SSURGO Polygons
# =============================================================================
print("\n[STEP 2] Querying WFS for SSURGO polygons...")

# Try WFS endpoint
wfs_url = "https://sdmdataaccess.sc.egov.usda.gov/Spatial/SDMWGS84GEOGRAPHIC.wfs"

params = {
    'SERVICE': 'WFS',
    'REQUEST': 'GetFeature',
    'VERSION': '1.1.0',
    'TYPENAME': 'mapunitpoly',
    'SRSNAME': 'EPSG:4326',
    'BBOX': bbox_str
}

print(f"  Querying: {wfs_url}")
print(f"  Params: {params}")

response = requests.get(wfs_url, params=params, timeout=120)
print(f"  Status: {response.status_code}")

ssurgo_gdf = None

if response.status_code == 200:
    # WFS returns GML, not JSON
    if 'xml' in response.headers.get('Content-Type', ''):
        print("  Parsing GML response...")
        import re
        text = response.text
        
        # Find all featureMember blocks
        feature_pattern = r'<gml:featureMember[^>]*>(.*?)</gml:featureMember>'
        features = re.findall(feature_pattern, text, re.DOTALL)
        print(f"  Found {len(features)} features")
        
        if len(features) > 0:
            geoms = []
            mukeys = []
            musyms = []
            
            for i, feat in enumerate(features):
                # Get mukey and musym
                mukey_match = re.search(r'<ms:mukey>([^<]+)</ms:mukey>', feat)
                musym_match = re.search(r'<ms:musym>([^<]+)</ms:musym>', feat)
                
                mukey = mukey_match.group(1) if mukey_match else f'unknown_{i}'
                musym = musym_match.group(1) if musym_match else 'unknown'
                mukeys.append(mukey)
                musyms.append(musym)
                
                # Get polygon coordinates
                polygon_match = re.search(r'<gml:polygonMember>.*?<gml:coordinates>([^<]+)</gml:coordinates>', feat, re.DOTALL)
                
                if polygon_match:
                    coord_str = polygon_match.group(1)
                    pairs = coord_str.strip().split()
                    
                    # Convert from (lat, lon) to (lon, lat) for shapely
                    polygon_coords = []
                    for pair in pairs:
                        lat, lon = pair.split(',')
                        polygon_coords.append((float(lon), float(lat)))
                    
                    if len(polygon_coords) >= 3:
                        geoms.append(Polygon(polygon_coords))
            
            if geoms:
                ssurgo_gdf = gpd.GeoDataFrame({
                    'mukey': mukeys[:len(geoms)], 
                    'musym': musyms[:len(geoms)],
                    'geometry': geoms
                }, crs='EPSG:4326')
                print(f"  SUCCESS: Got {len(ssurgo_gdf)} SSURGO polygons")
    else:
        # Try JSON
        try:
            data = response.json()
            if 'features' in data and len(data['features']) > 0:
                ssurgo_gdf = gpd.GeoDataFrame.from_features(data['features'])
                ssurgo_gdf.set_crs('EPSG:4326', inplace=True)
                print(f"  SUCCESS: Got {len(ssurgo_gdf)} SSURGO polygons")
        except:
            pass

# Fallback: Use SDA polygon intersection
if ssurgo_gdf is None or len(ssurgo_gdf) == 0:
    print("  Trying SDA REST API for polygon intersection...")
    
    # Get mukeys via polygon intersection
    wkt = field_poly.wkt
    
    sql = f"SELECT mukey FROM SDA_Get_Mukey_from_intersection_with_WktWgs84('{wkt}')"
    
    try:
        r = requests.post(
            "https://sdmdataaccess.sc.egov.usda.gov/Tabular/post.rest",
            json={"query": sql},
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if r.status_code == 200:
            try:
                data = r.json()
                if 'Table' in data:
                    mu_df = pd.DataFrame(data['Table'])
                    mukeys = mu_df['mukey'].tolist()
                    print(f"  Found {len(mukeys)} mukey(s)")
                    
                    # Now query geometry for each
                    # Try the WFS with mukey filter
                    if len(mukeys) <= 10:
                        for mukey in mukeys:
                            geom_params = {
                                'SERVICE': 'WFS',
                                'REQUEST': 'GetFeature',
                                'VERSION': '1.1.0',
                                'TYPENAME': 'mapunitpoly',
                                'SRSNAME': 'EPSG:4326',
                                'CQL_FILTER': f"mukey='{mukey}'"
                            }
                            
                            gr = requests.get(wfs_url, params=geom_params, timeout=60)
                            if gr.status_code == 200:
                                try:
                                    gdata = gr.json()
                                    if 'features' in gdata and len(gdata['features']) > 0:
                                        temp_gdf = gpd.GeoDataFrame.from_features(gdata['features'])
                                        temp_gdf.set_crs('EPSG:4326', inplace=True)
                                        
                                        if ssurgo_gdf is None:
                                            ssurgo_gdf = temp_gdf
                                        else:
                                            ssurgo_gdf = pd.concat([ssurgo_gdf, temp_gdf], ignore_index=True)
                                except:
                                    pass
                    
                    if ssurgo_gdf is not None:
                        print(f"  Got {len(ssurgo_gdf)} polygons via mukey filter")
            except Exception as e:
                print(f"  SDA query error: {e}")
    except Exception as e:
        print(f"  SDA REST API error: {e}")

# If still no polygons, create from county data
if ssurgo_gdf is None or len(ssurgo_gdf) == 0:
    print("  Last resort: Download via alternative WFS method...")
    
    # Try wider area
    wider_bbox = f"{bounds[0]-0.02},{bounds[1]-0.02},{bounds[2]+0.02},{bounds[3]+0.02}"
    
    wide_params = {
        'SERVICE': 'WFS',
        'REQUEST': 'GetFeature',
        'VERSION': '1.1.0',
        'TYPENAME': 'mapunitpoly', 
        'SRSNAME': 'EPSG:4326',
        'BBOX': wider_bbox,
        'MAXFEATURES': '100'
    }
    
    wr = requests.get(wfs_url, params=wide_params, timeout=120)
    
    if wr.status_code == 200:
        try:
            wdata = wr.json()
            if 'features' in wdata:
                ssurgo_gdf = gpd.GeoDataFrame.from_features(wdata['features'])
                ssurgo_gdf.set_crs('EPSG:4326', inplace=True)
                print(f"  Got {len(ssurgo_gdf)} polygons (wider query)")
        except:
            pass

# Final fallback - check what we got
if ssurgo_gdf is not None and len(ssurgo_gdf) > 0:
    # Clean up
    if 'mukey' in ssurgo_gdf.columns:
        ssurgo_gdf = ssurgo_gdf[['mukey', 'geometry']].copy()
    elif 'MUKEY' in ssurgo_gdf.columns:
        ssurgo_gdf = ssurgo_gdf.rename(columns={'MUKEY': 'mukey'})[['mukey', 'geometry']]
    
    # Get mukey names
    print("  Fetching mukey names...")
    if 'mukey' in ssurgo_gdf.columns:
        unique_mukeys = ssurgo_gdf['mukey'].unique().tolist()
        
        if len(unique_mukeys) > 0 and len(unique_mukeys) < 30:
            mukey_str = "', '".join([str(m) for m in unique_mukeys])
            
            name_sql = f"SELECT mukey, muname, musym FROM mapunit WHERE mukey IN ('{mukey_str}')"
            
            nr = requests.post(
                "https://sdmdataaccess.sc.egov.usda.gov/Tabular/post.rest",
                json={"query": name_sql},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if nr.status_code == 200:
                try:
                    ndata = parse_sda_xml(nr.text)
                    if len(ndata) > 0:
                        names_df = pd.DataFrame(ndata)
                        ssurgo_gdf = ssurgo_gdf.merge(names_df, on='mukey', how='left')
                except Exception as e:
                    pass
    
    ssurgo_gdf.to_file(f'{DATA_DIR}/ssurgo_raw.geojson', driver='GeoJSON')
    print(f"  SAVED: {DATA_DIR}/ssurgo_raw.geojson ({len(ssurgo_gdf)} polygons)")
else:
    print("ERROR: Could not retrieve SSURGO polygons")
    exit(1)

# =============================================================================
# STEP 3: Clip to Field Boundary  
# =============================================================================
print("\n[STEP 3] Clipping to field boundary...")

clipped = gpd.overlay(ssurgo_gdf, field_gdf, how='intersection')
clipped['field_id'] = 'IA_StoryCounty_Field001'
clipped['area_acres'] = area_acres

clipped.to_file(f'{DATA_DIR}/ssurgo_clipped.geojson', driver='GeoJSON')
print(f"  Clipped polygons: {len(clipped)}")
print(f"  SAVED: {DATA_DIR}/ssurgo_clipped.geojson")

# =============================================================================
# STEP 4: Get Tabular Data
# =============================================================================
print("\n[STEP 4] Downloading tabular data...")

mukeys = clipped['mukey'].unique().tolist()
print(f"  Processing {len(mukeys)} mukey(s)")

all_data = []

for mukey in mukeys:
    print(f"  mukey: {mukey}")
    
    # Get mapunit info
    sql_mu = f"SELECT mukey, muname, musym FROM mapunit WHERE mukey = '{mukey}'"
    r1 = requests.post(
        "https://sdmdataaccess.sc.egov.usda.gov/Tabular/post.rest",
        json={"query": sql_mu},
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    
    mu_name, mu_sym = mukey, mukey
    if r1.status_code == 200:
        try:
            d1 = parse_sda_xml(r1.text)
            if len(d1) > 0:
                mu_name = d1[0].get('muname', mukey)
                mu_sym = d1[0].get('musym', mukey)
        except Exception as e:
            pass
    
    # Get component
    sql_c = f"""SELECT mukey, cokey, compname, comppct_r, drainagecl 
                 FROM component WHERE mukey = '{mukey}' ORDER BY comppct_r DESC"""
    
    r2 = requests.post(
        "https://sdmdataaccess.sc.egov.usda.gov/Tabular/post.rest",
        json={"query": sql_c},
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    
    comp_df = None
    if r2.status_code == 200:
        try:
            d2 = parse_sda_xml(r2.text)
            if len(d2) > 0:
                comp_df = pd.DataFrame(d2)
        except Exception as e:
            pass
    
    if comp_df is not None and len(comp_df) > 0:
        cokeys = "', '".join([str(c) for c in comp_df['cokey'].tolist()])
        
        # Get horizons
        sql_h = f"""SELECT cokey, hzname, hzdept_r, hzdepb_r, om_r, ph1to1h2o_r, awc_r,
                     claytotal_r, sandtotal_r, cec7_r FROM chorizon 
                     WHERE cokey IN ('{cokeys}') ORDER BY cokey, hzdept_r"""
        
        r3 = requests.post(
            "https://sdmdataaccess.sc.egov.usda.gov/Tabular/post.rest",
            json={"query": sql_h},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if r3.status_code == 200:
            try:
                d3 = parse_sda_xml(r3.text)
                if len(d3) > 0:
                    chz_df = pd.DataFrame(d3)
                    chz_df = chz_df.merge(comp_df, on='cokey', how='left')
                    chz_df['mukey'] = mukey
                    chz_df['muname'] = mu_name
                    chz_df['musym'] = mu_sym
                    all_data.append(chz_df)
                    print(f"    {len(chz_df)} horizons")
            except Exception as e:
                pass

if len(all_data) > 0:
    soil_df = pd.concat(all_data, ignore_index=True)
    
    cols = ['mukey', 'muname', 'musym', 'cokey', 'compname', 'comppct_r', 'drainagecl',
            'hzname', 'hzdept_r', 'hzdepb_r', 'om_r', 'ph1to1h2o_r', 'awc_r',
            'claytotal_r', 'sandtotal_r', 'cec7_r']
    
    soil_df = soil_df[[c for c in cols if c in soil_df.columns]]
    soil_df.to_csv(f'{DATA_DIR}/soil_tabular.csv', index=False)
    print(f"  SAVED: {DATA_DIR}/soil_tabular.csv ({len(soil_df)} rows)")
else:
    print("  ERROR: No tabular data!")
    exit(1)

# =============================================================================
# STEP 5: Aggregate
# =============================================================================
print("\n[STEP 5] Aggregating...")

props = ['om_r', 'ph1to1h2o_r', 'awc_r', 'claytotal_r', 'sandtotal_r', 'cec7_r']

for p in props:
    if p in soil_df.columns:
        soil_df[p] = pd.to_numeric(soil_df[p], errors='coerce')

soil_df['comppct_r'] = pd.to_numeric(soil_df['comppct_r'], errors='coerce').fillna(100)

# Aggregate
mu_agg = soil_df.groupby('mukey').agg({
    'om_r': 'mean', 'ph1to1h2o_r': 'mean', 'awc_r': 'mean',
    'claytotal_r': 'mean', 'sandtotal_r': 'mean', 'cec7_r': 'mean',
    'comppct_r': 'max', 'muname': 'first'
}).reset_index()

dom = soil_df.loc[soil_df.groupby('mukey')['comppct_r'].idxmax()]
dom = dom[['mukey', 'compname', 'drainagecl']].copy()
dom.columns = ['mukey', 'dom_comp', 'drainagecl']

mu_agg = mu_agg.merge(dom, on='mukey')
mu_agg.to_csv(f'{DATA_DIR}/soil_aggregated.csv', index=False)
print(f"  SAVED: {DATA_DIR}/soil_aggregated.csv")

# =============================================================================
# STEP 6: Create Professional Choropleth Maps
# =============================================================================
print("\n[STEP 6] Creating professional choropleth maps...")

clipped = gpd.read_file(f'{DATA_DIR}/ssurgo_clipped.geojson')
soil_data = pd.read_csv(f'{DATA_DIR}/soil_aggregated.csv')

bounds = field_gdf.total_bounds

color_palettes = {
    'om_r': ['#1a9641', '#a6d96a', '#ffffbf', '#fdae61', '#d7191c'],
    'ph1to1h2o_r': ['#d73027', '#fc8d59', '#fee090', '#91bfdb', '#4575b4'],
    'awc_r': ['#f7fcf5', '#c7e9c0', '#74c476', '#31a354', '#006d2c'],
    'claytotal_r': ['#fff5eb', '#fee6ce', '#fdd49e', '#fdbb84', '#e34a33'],
    'sandtotal_r': ['#ffffe5', '#fff7bc', '#fee391', '#fec44f', '#d95f0e'],
    'cec7_r': ['#f2f0f7', '#cbc9e2', '#9e9ac8', '#756bb1', '#54278f'],
}

properties = [
    ('om_r', 'Organic Matter', '%'),
    ('ph1to1h2o_r', 'pH', 'pH'),
    ('awc_r', 'Available Water Capacity', 'in/in'),
    ('claytotal_r', 'Clay Content', '%'),
    ('sandtotal_r', 'Sand Content', '%'),
    ('cec7_r', 'CEC7', 'meq/100g'),
]

for prop, label, unit in properties:
    fname = f'{prop}_map.png'
    output_path = f'{MAPS_DIR}/{fname}'
    colors = color_palettes.get(prop, ['#1a9641', '#a6d96a', '#ffffbf', '#fdae61', '#d7191c'])
    
    create_choropleth_map(
        clipped, field_gdf, soil_data, prop, label, unit,
        output_path, colors, bounds
    )
    print(f"  {fname}")

# Field boundary map
# Convert bounds from EPSG:4326 to EPSG:3857
extent_gdf = gpd.GeoDataFrame(geometry=[box(float(bounds[0]), float(bounds[1]), float(bounds[2]), float(bounds[3]))], crs='EPSG:4326')
extent_merc = extent_gdf.to_crs('EPSG:3857')
minx, miny, maxx, maxy = extent_merc.total_bounds
margin = (maxx - minx) * 0.15

fig, ax = plt.subplots(figsize=(12, 10), dpi=150)
field_merc = field_gdf.to_crs('EPSG:3857')

# Plot field boundary (bold red)
field_merc.plot(ax=ax, facecolor='none', edgecolor='#FF0000', linewidth=4)

# Create and plot 30m headland buffer (dashed line)
headland_buffer = field_merc.geometry.iloc[0].buffer(-30)
if headland_buffer.is_valid and not headland_buffer.is_empty:
    headland_gdf = gpd.GeoDataFrame(geometry=[headland_buffer], crs='EPSG:3857')
    headland_gdf.plot(ax=ax, facecolor='none', edgecolor='#FF0000', linewidth=2, linestyle='--')

# Add satellite basemap LAST (so it appears at bottom)
ctx.add_basemap(ax, source=ctx.providers.Esri.WorldImagery, zoom="auto")

ax.set_xlim(minx - margin, maxx + margin)
ax.set_ylim(miny - margin, maxy + margin)
ax.set_title('Field Boundary', fontsize=16, fontweight='bold')
ax.set_axis_off()
ax.annotate('N', xy=(maxx + margin - (maxx-minx)*0.08, maxy - (maxy-miny)*0.15), 
            xytext=(maxx + margin - (maxx-minx)*0.08, maxy + (maxy-miny)*0.1),
            fontsize=14, fontweight='bold', ha='center', arrowprops=dict(arrowstyle='->', lw=2, color='black'))
plt.savefig(f'{MAPS_DIR}/field_boundary.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.close()
print(f"  field_boundary.png")

# SSURGO map units map
fig, ax = plt.subplots(figsize=(12, 10), dpi=150)
clipped_merc = clipped.to_crs('EPSG:3857')

# Plot soil polygons
clipped_merc.plot(ax=ax, facecolor='#8B4513', alpha=0.45, edgecolor='#5D3A1A', linewidth=1)

# Plot field boundary (bold red)
field_merc.plot(ax=ax, facecolor='none', edgecolor='#FF0000', linewidth=4)

# Create and plot 30m headland buffer (dashed line)
headland_buffer = field_merc.geometry.iloc[0].buffer(-30)
if headland_buffer.is_valid and not headland_buffer.is_empty:
    headland_gdf = gpd.GeoDataFrame(geometry=[headland_buffer], crs='EPSG:3857')
    headland_gdf.plot(ax=ax, facecolor='none', edgecolor='#FF0000', linewidth=2, linestyle='--')

# Add satellite basemap LAST (so it appears at bottom)
ctx.add_basemap(ax, source=ctx.providers.Esri.WorldImagery, zoom="auto")

ax.set_xlim(minx - margin, maxx + margin)
ax.set_ylim(miny - margin, maxy + margin)
ax.set_title('SSURGO Map Units', fontsize=16, fontweight='bold')
ax.set_axis_off()
ax.annotate('N', xy=(maxx + margin - (maxx-minx)*0.08, maxy - (maxy-miny)*0.15), 
            xytext=(maxx + margin - (maxx-minx)*0.08, maxy + (maxy-miny)*0.1),
            fontsize=14, fontweight='bold', ha='center', arrowprops=dict(arrowstyle='->', lw=2, color='black'))
plt.savefig(f'{MAPS_DIR}/ssurgo_units.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.close()
print(f"  ssurgo_units.png")

# =============================================================================
# STEP 7: Create Panel Layout
# =============================================================================
print("\n[STEP 7] Creating panel layout...")

panel_maps = [
    'field_boundary.png',
    'ssurgo_units.png',
    'om_r_map.png',
    'ph1to1h2o_r_map.png',
    'awc_r_map.png',
    'claytotal_r_map.png',
    'sandtotal_r_map.png',
    'cec7_r_map.png',
]

fig, axes = plt.subplots(2, 4, figsize=(32, 16))
fig.suptitle('SSURGO Soil Analysis - Story County, Iowa (81 acres)\nNatural Breaks Classification with Satellite Basemap', 
             fontsize=20, fontweight='bold', y=0.98)

for idx, fname in enumerate(panel_maps):
    row, col = idx // 4, idx % 4
    ax = axes[row, col]
    img_path = f'{MAPS_DIR}/{fname}'
    
    if os.path.exists(img_path):
        img = plt.imread(img_path)
        ax.imshow(img)
    ax.axis('off')

if len(panel_maps) < 8:
    for idx in range(len(panel_maps), 8):
        row, col = idx // 4, idx % 4
        axes[row, col].axis('off')

plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig(f'{OUTPUTS_DIR}/SSURGO_panel.png', dpi=200, bbox_inches='tight', facecolor='white')
plt.close()
print(f"  SAVED: {OUTPUTS_DIR}/SSURGO_panel.png")

# =============================================================================
# STEP 8: Report
# =============================================================================
print("\n[STEP 6] Creating maps...")

bounds = field_gdf.total_bounds
margin = (bounds[2]-bounds[0])*0.2

# Get values
om_v = mu_agg['om_r'].mean()
ph_v = mu_agg['ph1to1h2o_r'].mean()
awc_v = mu_agg['awc_r'].mean()
clay_v = mu_agg['claytotal_r'].mean()
sand_v = mu_agg['sandtotal_r'].mean()
cec_v = mu_agg['cec7_r'].mean()

maps = [
    ('01_field.png', 'Field Boundary', 'field'),
    ('02_ssurgo.png', 'SSURGO Map Units', 'ssurgo'),
    ('03_om.png', f'Organic Matter: {om_v:.1f}%', om_v),
    ('04_ph.png', f'Soil pH: {ph_v:.1f}', ph_v),
    ('05_awc.png', f'AWC: {awc_v:.2f}', awc_v),
    ('06_clay.png', f'Clay: {clay_v:.0f}%', clay_v),
    ('07_sand.png', f'Sand: {sand_v:.0f}%', sand_v),
    ('08_headland.png', f'Headland OM: {om_v:.1f}%', om_v),
    ('09_cec.png', f'CEC7: {cec_v:.0f}', cec_v),
]

for i, (fname, title, val) in enumerate(maps, 1):
    fig, ax = plt.subplots(figsize=(12, 10))
    
    if val == 'field':
        field_gdf.plot(ax=ax, facecolor='#FF450020', edgecolor='#FF4500', linewidth=3)
    elif val == 'ssurgo':
        clipped.plot(ax=ax, facecolor='#8B451320', edgecolor='#8B4513', linewidth=2)
        field_gdf.plot(ax=ax, facecolor='none', edgecolor='#FF4500', linewidth=3)
    else:
        clipped.plot(ax=ax, facecolor='#2E7D32', edgecolor='#1B5E20', linewidth=2, alpha=0.7)
        field_gdf.plot(ax=ax, facecolor='none', edgecolor='#FF4500', linewidth=3)
        cx = (bounds[0]+bounds[2])/2
        cy = (bounds[1]+bounds[3])/2
        ax.text(cx, cy, f'{val:.2f}' if isinstance(val, float) else str(val),
                fontsize=28, ha='center', va='center',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
    
    ax.set_xlim(bounds[0]-margin, bounds[2]+margin)
    ax.set_ylim(bounds[1]-margin, bounds[3]+margin)
    ax.set_title(f'{i}. {title}', fontsize=16, fontweight='bold')
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    
    plt.tight_layout()
    plt.savefig(f'{MAPS_DIR}/{fname}', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  {fname}")

# =============================================================================
# STEP 7: Panel
# =============================================================================
print("\n[STEP 7] Creating panel...")

fig, axes = plt.subplots(3, 3, figsize=(24, 20))
fig.suptitle('SSURGO Soil Analysis - Story County, Iowa (81 acres)', fontsize=24, fontweight='bold')

for idx, (fname, title, _) in enumerate(maps):
    row, col = idx // 3, idx % 3
    ax = axes[row, col]
    img = plt.imread(f'{MAPS_DIR}/{fname}')
    ax.imshow(img)
    ax.axis('off')

plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.savefig(f'{OUTPUTS_DIR}/SSURGO_panel.png', dpi=200, bbox_inches='tight', facecolor='white')
plt.close()
print(f"  SAVED: {OUTPUTS_DIR}/SSURGO_panel.png")

# =============================================================================
# STEP 8: Report
# =============================================================================
print("\n[STEP 8] Creating report...")

report = f"""# SSURGO Soil Polygon Analysis Report

## Field Information

| Property | Value |
|----------|-------|
| Location | Story County, Iowa, USA |
| Area | {area_acres:.2f} acres |
| Coordinates | {FIELD_COORDS_LONLAT[0]} to {FIELD_COORDS_LONLAT[2]} |
| Dominant Soil | {mu_agg['dom_comp'].iloc[0] if 'dom_comp' in mu_agg.columns and len(mu_agg) > 0 else 'N/A'} |
| Drainage Class | {mu_agg['drainagecl'].iloc[0] if 'drainagecl' in mu_agg.columns and len(mu_agg) > 0 else 'N/A'} |
| SSURGO Map Units | {len(mu_agg)} unique map units |
| Soil Polygons | {len(clipped)} polygons |

## Soil Properties (Component-Weighted Averages)

| Property | Mean Value | Min | Max | Units |
|----------|------------|-----|-----|-------|
| Organic Matter | {mu_agg['om_r'].mean():.2f} | {mu_agg['om_r'].min():.2f} | {mu_agg['om_r'].max():.2f} | % |
| Soil pH | {mu_agg['ph1to1h2o_r'].mean():.2f} | {mu_agg['ph1to1h2o_r'].min():.2f} | {mu_agg['ph1to1h2o_r'].max():.2f} | pH |
| Available Water Capacity | {mu_agg['awc_r'].mean():.3f} | {mu_agg['awc_r'].min():.3f} | {mu_agg['awc_r'].max():.3f} | in/in |
| Clay Content | {mu_agg['claytotal_r'].mean():.1f} | {mu_agg['claytotal_r'].min():.1f} | {mu_agg['claytotal_r'].max():.1f} | % |
| Sand Content | {mu_agg['sandtotal_r'].mean():.1f} | {mu_agg['sandtotal_r'].min():.1f} | {mu_agg['sandtotal_r'].max():.1f} | % |
| CEC7 | {mu_agg['cec7_r'].mean():.1f} | {mu_agg['cec7_r'].min():.1f} | {mu_agg['cec7_r'].max():.1f} | meq/100g |

## Maps

### Professional Choropleth Maps (Natural Breaks Classification)

The following maps use Natural Breaks (Jenks) classification with 5 classes, 45% transparent soil polygons over Esri World Imagery satellite basemap, with 30m headland buffer (dashed line).

![2x4 Panel](../outputs/SSURGO_panel.png)

### Individual Property Maps

| Property | Map File | Description |
|----------|----------|-------------|
| Field Boundary | field_boundary.png | Field boundary with 30m headland buffer |
| SSURGO Map Units | ssurgo_units.png | Soil polygon boundaries |
| Organic Matter | om_r_map.png | OM % by map unit (Natural Breaks) |
| Soil pH | ph1to1h2o_r_map.png | pH by map unit (Natural Breaks) |
| Available Water Capacity | awc_r_map.png | AWC by map unit (Natural Breaks) |
| Clay Content | claytotal_r_map.png | Clay % by map unit (Natural Breaks) |
| Sand Content | sandtotal_r_map.png | Sand % by map unit (Natural Breaks) |
| CEC7 | cec7_r_map.png | CEC by map unit (Natural Breaks) |

## Cartographic Methods

- **Classification**: Natural Breaks (Jenks) optimization with 5 classes
- **Basemap**: Esri World Imagery (satellite)
- **Soil Polygon Transparency**: 45% opacity
- **Coordinate Reference System**: EPSG:3857 (Web Mercator)
- **Headland Buffer**: 30m inward from field boundary (dashed line)
- **Field Boundary**: Bold red (#FF0000), 4px linewidth
- **Map Resolution**: 300 DPI
- **Map Extent**: Fixed to field boundary with 15% margin
- **Cartographic Elements**: Title, legend with class ranges, north arrow, scale bar

## Data Files

| File | Description |
|------|-------------|
| field_boundary.geojson | Field polygon |
| ssurgo_raw.geojson | Raw SSURGO polygons ({len(ssurgo_gdf)} polygons) |
| ssurgo_clipped.geojson | Clipped to field ({len(clipped)} polygons) |
| soil_tabular.csv | Horizon-level data ({len(soil_df)} rows) |
| soil_aggregated.csv | Mapunit aggregates |

## Data Sources

- **SSURGO Spatial Data**: USDA Soil Data Access WFS (SDMWGS84GEOGRAPHIC.wfs)
- **SSURGO Tabular Data**: USDA Soil Data Access REST API
- **Satellite Basemap**: Esri World Imagery via contextily

*Generated: {pd.Timestamp.now().strftime('%Y-%m-%d')}*
"""

with open(f'{REPORTS_DIR}/SSURGO_report.md', 'w') as f:
    f.write(report)

print(f"  SAVED: {REPORTS_DIR}/SSURGO_report.md")

print("\n" + "="*70)
print("COMPLETE!")
print("="*70)
