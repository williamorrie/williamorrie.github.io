#!/usr/bin/env python3
"""
Process cat GPS data and save as GeoJSON files.
Run this once, or whenever the source data changes.
"""

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import json
from pathlib import Path

script_dir = Path(__file__).resolve().parent
app_data_dir = script_dir.parent / "data"
hid_data_dir = script_dir.parent / "_data"

print("Loading GPS data...")
df = pd.read_csv(hid_data_dir / 'UK-pet-cats.csv')

# Create point geometries
geometry = [Point(xy) for xy in zip(df["location-long"], df["location-lat"])]
gdf_all = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")

# Add date field
gdf_all['timestamp'] = pd.to_datetime(gdf_all['timestamp'])
gdf_all['date'] = gdf_all['timestamp'].dt.date.astype(str)

# Create convex hull polygons for each cat
print("Creating polygons...")
cat_gdf = gdf_all.groupby("tag-local-identifier").agg({
    'geometry': lambda x: x.union_all().convex_hull
}).reset_index()
cat_gdf = cat_gdf.set_geometry('geometry')
cat_gdf.crs = "EPSG:4326"
cat_gdf['area_m2'] = cat_gdf.geometry.to_crs("EPSG:3857").area.round(0).astype(int)

# Save polygons to GeoJSON
print("Saving polygons...")
cat_gdf.to_file(hid_data_dir / 'cat_polygons.geojson', driver='GeoJSON')

# Process GPS points for each cat
print("Processing GPS points by cat...")
cat_data = {}

for cat_id in gdf_all["tag-local-identifier"].unique():
    print(f"  Processing {cat_id}...")
    cat_points = gdf_all[gdf_all["tag-local-identifier"] == cat_id].copy()
    cat_points = cat_points.sort_values('timestamp')
    
    # Get bounds for this cat
    bounds = cat_points.total_bounds  # [minx, miny, maxx, maxy]
    
    # Convert to GeoJSON-ready format
    features = []
    for _, row in cat_points.iterrows():
        features.append({
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [row.geometry.x, row.geometry.y]
            },
            'properties': {
                'timestamp': row['timestamp'].isoformat(),
                'date': row['date'],
                'cat_id': cat_id
            }
        })
    
    cat_data[cat_id] = {
        'bounds': [[bounds[1], bounds[0]], [bounds[3], bounds[2]]],  # [[south, west], [north, east]]
        'area_m2': int(cat_gdf[cat_gdf['tag-local-identifier'] == cat_id].iloc[0]['area_m2']),
        'geojson': {
            'type': 'FeatureCollection',
            'features': features
        }
    }

# Save all cat data
print("Saving cat GPS data...")
with open(hid_data_dir / 'cat_gps_data.json', 'w') as f:
    json.dump(cat_data, f)

# Save metadata
metadata = {
    'center': [df["location-lat"].mean(), df["location-long"].mean()],
    'cats': sorted(gdf_all["tag-local-identifier"].unique().tolist()),
    'date_range': {
        'min': gdf_all['date'].min(),
        'max': gdf_all['date'].max()
    },
    'total_points': len(df),
    'total_cats': len(cat_data)
}

with open('data/metadata.json', 'w') as f:
    json.dump(metadata, f, indent=2)

print("\n✓ Data processing complete!")
print(f"  - {len(cat_data)} cats processed")
print(f"  - {len(df)} GPS points")
print(f"  - Files saved in '{app_data_dir}' directory")
