import marimo

__generated_with = "0.18.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import folium
    import marimo as mo
    import pandas as pd
    import geopandas as gpd
    from shapely.geometry import Point
    return Point, folium, gpd, mo, pd


@app.cell
def _(mo):
    mo.md("""
    # Cat Tracking: Home Range with GPS Points Toggle

    This notebook creates an interactive map showing cat home range polygons with the ability to toggle GPS tracking points on/off.
    """)
    return


@app.cell
def _(Point, gpd, pd):
    # Load GPS data
    df = pd.read_csv('UK-pet-cats.csv')

    # Create point geometries
    geometry = [Point(xy) for xy in zip(df["location-long"], df["location-lat"])]

    # Create GeoDataFrame
    gdf_all = gpd.GeoDataFrame(
        df, 
        geometry=geometry, 
        crs="EPSG:4326"
    )
    return df, gdf_all


@app.cell
def _(gdf_all):
    # Create convex hull polygons for each cat
    cat_gdf = gdf_all.groupby("tag-local-identifier").agg({
        'geometry': lambda x: x.union_all().convex_hull
    }).reset_index()

    # Convert to GeoDataFrame
    cat_gdf = cat_gdf.set_geometry('geometry')
    cat_gdf.crs = "EPSG:4326"

    # Calculate area in square meters using geodesic area
    cat_gdf['area_m2'] = cat_gdf.geometry.to_crs("EPSG:3857").area.round(0)
    return (cat_gdf,)


@app.cell
def _(gdf_all):
    # Create hulls WITHOUT outlier filtering
    cat_gdf_with_outliers = gdf_all.groupby("tag-local-identifier").agg({
        'geometry': lambda x: x.union_all().convex_hull
    }).reset_index()
    cat_gdf_with_outliers = cat_gdf_with_outliers.set_geometry('geometry')
    cat_gdf_with_outliers.crs = "EPSG:4326"
    cat_gdf_with_outliers['area_m2'] = cat_gdf_with_outliers.geometry.to_crs("EPSG:3857").area.round(0)

    # Create hulls WITH outlier filtering (95th percentile)
    def create_hull_without_outliers_compare(group):
        # Project to metric CRS for accurate distance calculation
        group_projected = group.to_crs("EPSG:3857")
        centroid = group_projected.geometry.union_all().centroid
        distances = group_projected.geometry.distance(centroid)
        threshold = distances.quantile(0.95)
        filtered_points = group_projected[distances <= threshold]
        # Convert back to EPSG:4326 for the hull
        return filtered_points.to_crs("EPSG:4326").geometry.union_all().convex_hull

    cat_gdf_filtered = gdf_all.groupby("tag-local-identifier").apply(
        create_hull_without_outliers_compare
    ).reset_index(name='geometry')
    cat_gdf_filtered = cat_gdf_filtered.set_geometry('geometry')
    cat_gdf_filtered.crs = "EPSG:4326"
    cat_gdf_filtered['area_m2'] = cat_gdf_filtered.geometry.to_crs("EPSG:3857").area.round(0)
    return cat_gdf_filtered, cat_gdf_with_outliers


@app.cell
def _(mo):
    mo.md("""
    ### Interactive Cat Explorer: Polygons & Routes
    """)
    return


@app.cell
def _(cat_explorer, cat_gdf_filtered, cat_gdf_with_outliers, date_slider, df, folium, pd):
    from folium.plugins import PolyLineTextPath

    if cat_explorer.value != "All Cats":
        selected_cat = cat_explorer.value

        # Filter polygons for selected cat
        poly_with = cat_gdf_with_outliers[cat_gdf_with_outliers["tag-local-identifier"] == selected_cat]
        poly_filtered = cat_gdf_filtered[cat_gdf_filtered["tag-local-identifier"] == selected_cat]

        # Create base map with filtered polygon
        m_explorer = poly_filtered.explore(
            color="blue",
            style_kwds=dict(fillOpacity=0.3, weight=2, color="blue"),
            tooltip=["tag-local-identifier", "area_m2"],
            name="Hull (95% filtered)",
            legend=True
        )

        # Add polygon with outliers as separate layer
        poly_with.explore(
            m=m_explorer,
            color="red",
            style_kwds=dict(fillOpacity=0.2, weight=2, color="red"),
            tooltip=["tag-local-identifier", "area_m2"],
            name="Hull (with outliers)"
        )

        # Get GPS points sorted by timestamp
        cat_points = df[df["tag-local-identifier"] == selected_cat].copy()
        cat_points['timestamp'] = pd.to_datetime(cat_points['timestamp'])
        cat_points = cat_points.sort_values('timestamp')
        cat_points['date'] = cat_points['timestamp'].dt.date
        
        # Filter by date range from slider
        if date_slider.value:
            start_date, end_date = date_slider.value
            cat_points = cat_points[
                (cat_points['date'] >= start_date) & 
                (cat_points['date'] <= end_date)
            ]

        # Define color palette for days
        colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 
                  'lightred', 'lightbrown', 'darkblue', 'darkgreen', 'cadetblue', 
                  'darkpurple', 'pink', 'lightblue', 'lightgreen', 'gray', 
                  'black', 'lightgray']

        # Create a color map for each unique date
        unique_dates = cat_points['date'].unique()
        date_colors = {date: colors[i % len(colors)] for i, date in enumerate(unique_dates)}

        # Group points by date and create routes for each day
        for date in unique_dates:
            day_points = cat_points[cat_points['date'] == date]
            day_color = date_colors[date]

            if len(day_points) > 1:
                route_coords = [[row["location-lat"], row["location-long"]] 
                               for _, row in day_points.iterrows()]

                arrow_line = folium.PolyLine(
                    route_coords,
                    color=day_color,
                    weight=3,
                    opacity=0.8,
                    popup=f"{selected_cat} - {date}",
                    tooltip=f"{date}"
                )
                arrow_line.add_to(m_explorer)

                # Add arrows
                PolyLineTextPath(
                    arrow_line,
                    '  ►  ',
                    repeat=True,
                    offset=10,
                    attributes={'fill': day_color, 'font-weight': 'bold', 'font-size': '24'}
                ).add_to(m_explorer)

        # Add GPS points colored by day
        for i, (idx, row) in enumerate(cat_points.iterrows()):
            day_color = date_colors[row['date']]

            folium.CircleMarker(
                location=[row["location-lat"], row["location-long"]],
                radius=4,
                popup=f"{selected_cat}<br>{row['timestamp']}<br>{row['date']}",
                tooltip=f"{row['date']}",
                color=day_color,
                fill=True,
                fillColor=day_color,
                fillOpacity=0.8,
                weight=2
            ).add_to(m_explorer)
    else:
        # Show all cats overview with both polygon types
        m_explorer = cat_gdf_with_outliers.explore(
            color="red",
            style_kwds=dict(fillOpacity=0.2, weight=2, color="red"),
            tooltip=["tag-local-identifier", "area_m2"],
            name="Hulls (with outliers)",
            legend=True
        )

        cat_gdf_filtered.explore(
            m=m_explorer,
            color="blue",
            style_kwds=dict(fillOpacity=0.3, weight=2, color="blue"),
            tooltip=["tag-local-identifier", "area_m2"],
            name="Hulls (95% filtered)"
        )

    # Add layer control
    folium.LayerControl(collapsed=False).add_to(m_explorer)

    m_explorer
    return


@app.cell
def _(cat_gdf, df, mo, pd):
    # Get the date range from the data
    df_with_dates = df.copy()
    df_with_dates['timestamp'] = pd.to_datetime(df_with_dates['timestamp'])
    df_with_dates['date'] = df_with_dates['timestamp'].dt.date
    
    min_date = df_with_dates['date'].min()
    max_date = df_with_dates['date'].max()
    
    # Create controls
    cat_explorer = mo.ui.dropdown(
        options=["All Cats"] + sorted(cat_gdf["tag-local-identifier"].tolist()),
        value="All Cats",
        label="Select a cat:"
    )
    
    date_slider = mo.ui.date_range(
        start=min_date,
        stop=max_date,
        value=[min_date, max_date],
        label="Select date range:"
    )
    
    # Display controls side by side
    mo.hstack([cat_explorer, date_slider], justify="start")
    return (cat_explorer, date_slider)


@app.cell
def _(mo):
    mo.md("""
    ### Export Full Map
    Generate a complete HTML map with all GPS points for all cats (bypasses marimo's size limit).
    """)
    return


@app.cell
def _(cat_gdf_filtered, df, folium, pd):
    from folium.plugins import PolyLineTextPath
    
    # Create base map with all filtered polygons
    m_full = cat_gdf_filtered.explore(
        column="area_m2",
        cmap="plasma",
        style_kwds=dict(fillOpacity=0.3, weight=2),
        tooltip=["tag-local-identifier", "area_m2"],
        name="Home Range Polygons",
        legend=True
    )
    
    # Color palette for days
    colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 
              'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue', 
              'darkpurple', 'pink', 'lightblue', 'lightgreen', 'gray', 
              'black', 'lightgray']
    
    # Process each cat
    for cat_id in cat_gdf_filtered["tag-local-identifier"].unique():
        cat_points = df[df["tag-local-identifier"] == cat_id].copy()
        cat_points['timestamp'] = pd.to_datetime(cat_points['timestamp'])
        cat_points = cat_points.sort_values('timestamp')
        cat_points['date'] = cat_points['timestamp'].dt.date
        
        # Create color map for this cat's dates
        unique_dates = cat_points['date'].unique()
        date_colors = {date: colors[i % len(colors)] for i, date in enumerate(unique_dates)}
        
        # Add routes for each day
        for date in unique_dates:
            day_points = cat_points[cat_points['date'] == date]
            day_color = date_colors[date]
            
            if len(day_points) > 1:
                route_coords = [[row["location-lat"], row["location-long"]] 
                               for _, row in day_points.iterrows()]
                
                arrow_line = folium.PolyLine(
                    route_coords,
                    color=day_color,
                    weight=2,
                    opacity=0.6,
                    popup=f"{cat_id} - {date}",
                    tooltip=f"{cat_id} - {date}"
                )
                arrow_line.add_to(m_full)
                
                PolyLineTextPath(
                    arrow_line,
                    '  ►  ',
                    repeat=True,
                    offset=10,
                    attributes={'fill': day_color, 'font-weight': 'bold', 'font-size': '20'}
                ).add_to(m_full)
        
        # Add GPS points
        for _, row in cat_points.iterrows():
            day_color = date_colors[row['date']]
            folium.CircleMarker(
                location=[row["location-lat"], row["location-long"]],
                radius=3,
                popup=f"{cat_id}<br>{row['timestamp']}<br>{row['date']}",
                tooltip=f"{cat_id}",
                color=day_color,
                fill=True,
                fillColor=day_color,
                fillOpacity=0.7,
                weight=1
            ).add_to(m_full)
    
    # Add layer control
    folium.LayerControl(collapsed=False).add_to(m_full)
    
    # Save to HTML file
    m_full.save("cat_tracks_full.html")
    
    "✓ Full map saved to cat_tracks_full.html"
    return


if __name__ == "__main__":
    app.run()
