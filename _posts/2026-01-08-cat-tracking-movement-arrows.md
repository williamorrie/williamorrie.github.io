---
layout: post
title: "Cat Tracking Movement Visualization with Direction Arrows"
---

### Idea
Get a refresher on working with GIS data and explore how DuckDB can help with spatial data processing. Coming from a SQL background rather than Python, I wanted to investigate whether DuckDB's spatial extension could simplify geospatial workflows. Also wanted to try out [Marimo](https://marimo.io/){:target="_blank"} as a pure Python alternative to Jupyter notebooks.

### Visualization
View the [Cat Movement Arrows Map](https://williamorrie.github.io/cat_arrows.html){:target="_blank"}

### Process
1. Downloaded cat GPS tracking data from [Movebank](https://www.movebank.org){:target="_blank"} (UK pet cats dataset)
2. Initial data exploration in [`_marimo/first-cats.py`](https://github.com/williamorrie/williamorrie.github.io/blob/master/_marimo/first-cats.py){:target="_blank"} using DuckDB's spatial extension for:
   - Loading and querying CSV data with SQL
   - Creating convex hull polygons for each cat's territory
   - Calculating spherical areas with `ST_Area_Spheroid`
   - Converting between coordinate systems (EPSG:4326 ↔ EPSG:3857)
3. Used Folium to create initial map visualization
4. Initially exported maps with `map.save('page.html')` to share online
5. Progressed to automated HTML generation using scripts in [`_html_gen/`](https://github.com/williamorrie/williamorrie.github.io/tree/master/_html_gen){:target="_blank"}:
   - `process_cat_data.py` - Pre-processes GPS data and generates GeoJSON files
   - `cat_arrows.py` - Creates interactive HTML with dynamic data loading
6. Added directional arrows and date range filtering for movement analysis

### Why This Approach?
- **DuckDB**: Familiar SQL syntax for spatial operations instead of Python-heavy geopandas chains
- **Marimo**: Live updates when editing code, better for iterative data exploration
- **Automated generation**: Scripts separate data processing from visualization, keeping HTML files lightweight

### Technologies
- DuckDB spatial extension for SQL-based GIS queries
- Marimo for interactive Python notebooks
- GeoPandas and Shapely for geometry handling
- Folium/Leaflet.js for web mapping
- OpenStreetMap tiles for base map

### Results
Successfully created an interactive visualization showing cat movement patterns and territories. The DuckDB approach made spatial queries more intuitive for SQL users, and Marimo's reactive design improved the exploration workflow. Automated scripts make it easy to regenerate the visualization when data updates.


#### Data Source
[Original data](<https://datarepository.movebank.org/entities/datapackage/4ef43458-a0c0-4ff0-aed4-64b07cedf11c)>) from [movebank.org](https://www.movebank.org/cms/movebank-main) published under Creative Commons 
