---
name: interactive-web-map
description: Create professional, self-contained interactive web maps for agricultural data visualization. Generate single HTML files with embedded data, layer controls, choropleth styling, and customizable dashboards using Leaflet.js.
version: 2.0.0
author: Boreal Bytes
tags: [web-map, visualization, leaflet, geospatial, interactive, dashboard, choropleth]
---

# Skill: interactive-web-map

## Description

Create professional, self-contained interactive web maps for agricultural data analysis. This skill teaches you to create **standalone HTML files** that can be opened directly in any web browser, shared via email, or deployed to any web server.

**Key Features:**

- **Self-contained**: Single HTML file with all data embedded
- **Layer control**: Toggle between field boundaries, soil data, weather stations
- **Choropleth styling**: Color-code fields by any data attribute
- **Multiple basemaps**: OpenStreetMap, Satellite, Terrain
- **Performance optimized**: Handles 200+ fields smoothly

## Prerequisites

```bash
pip install pandas geopandas
```

## Quick Start: Create a Field Map

```python
import json
import geopandas as gpd

fields = gpd.read_file('field-boundaries/examples/sample_2_fields.geojson')
geojson_data = json.loads(fields.to_json())

html_content = '''<!DOCTYPE html>
<html>
<head>
    <title>Agricultural Fields Map</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
</head>
<body>
    <div id="map" style="height: 100vh;"></div>
    <script>
        var map = L.map('map').setView([44.5, -93.5], 8);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
        var fieldData = ''' + json.dumps(geojson_data) + ''';
        L.geoJSON(fieldData, {
            style: { color: "#2E7D32", weight: 2, fillOpacity: 0.3 },
            onEachFeature: function(feature, layer) {
                layer.bindPopup(
                    '<b>Field:</b> ' + feature.properties.field_id + '<br>' +
                    '<b>Area:</b> ' + feature.properties.area_acres.toFixed(1) + ' acres'
                );
            }
        }).addTo(map);
    </script>
</body>
</html>'''

with open('field_map.html', 'w') as f:
    f.write(html_content)

print("Created: field_map.html")
```

## Professional Dashboard Example

```python
import json
import geopandas as gpd

fields = gpd.read_file('field-boundaries/examples/sample_2_fields.geojson')
bounds = fields.total_bounds
center_lat = (bounds[1] + bounds[3]) / 2
center_lon = (bounds[0] + bounds[2]) / 2
geojson_data = json.loads(fields.to_json())

html = f'''<!DOCTYPE html>
<html>
<head>
    <title>Agricultural Dashboard</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body {{ margin: 0; font-family: sans-serif; }}
        #container {{ display: flex; height: 100vh; }}
        #sidebar {{ width: 300px; background: #fff; padding: 20px; overflow-y: auto; }}
        #map {{ flex: 1; }}
        .panel {{ margin: 15px 0; padding: 10px; background: #f5f5f5; border-radius: 5px; }}
    </style>
</head>
<body>
    <div id="container">
        <div id="sidebar">
            <h1>Dashboard</h1>
            <div class="panel">
                <h3>Layers</h3>
                <label><input type="checkbox" checked onchange="toggleFields()"> Fields</label>
            </div>
        </div>
        <div id="map"></div>
    </div>
    <script>
        var map = L.map('map').setView([{center_lat}, {center_lon}], 10);
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png').addTo(map);
        var fields = L.geoJSON({json.dumps(geojson_data)}, {{
            style: {{ color: '#1B5E20', weight: 2, fillOpacity: 0.6 }},
            onEachFeature: function(f, l) {{
                l.bindPopup('<b>Field:</b> ' + f.properties.field_id + '<br><b>Acres:</b> ' + f.properties.area_acres.toFixed(1));
            }}
        }}).addTo(map);
    </script>
</body>
</html>'''

with open('dashboard.html', 'w') as f:
    f.write(html)
```

## Styling Color Palettes

### Crop Types
```javascript
const cropColors = {
  Corn: '#2E7D32',
  Soybeans: '#F9A825',
  Wheat: '#E65100',
  Cotton: '#1565C0',
  Default: '#757575',
};
```

### Soil pH (Acid → Neutral → Alkaline)
```javascript
function getPHColor(ph) {
  if (ph < 6.0) return '#1565C0';
  if (ph < 6.5) return '#43A047';
  if (ph < 7.5) return '#2E7D32';
  return '#C62828';
}
```

### NDVI
```javascript
function getNDVIColor(ndvi) {
  if (ndvi < 0.2) return '#8B4513';
  if (ndvi < 0.4) return '#FFD700';
  if (ndvi < 0.6) return '#9ACD32';
  if (ndvi < 0.8) return '#228B22';
  return '#006400';
}
```

## Performance Tips

```javascript
L.geoJSON(data, {
    renderer: L.canvas(),  // Use Canvas instead of SVG
    style: {...},
    onEachFeature: {...}
}).addTo(map);
```

## Resources

- [Leaflet Documentation](https://leafletjs.com/)
- [Leaflet Plugins](https://leafletjs.com/plugins.html)
- [ColorBrewer](https://colorbrewer2.org/)
