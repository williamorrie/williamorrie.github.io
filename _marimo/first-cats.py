import marimo

__generated_with = "0.18.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import folium
    import marimo as mo
    import pandas as pd
    import contextily as ctx
    import geopandas as gpd
    import matplotlib.pyplot as plt

    from shapely import wkb
    from shapely.geometry import Point
    return Point, ctx, folium, gpd, mo, pd, plt, wkb


@app.cell
def _(mo):
    df = mo.sql(
        f"""
        INSTALL spatial;
        LOAD spatial;

        SELECT "timestamp", "location-long", "location-lat"
            FROM READ_CSV('UK-pet-cats.csv')
        WHERE "tag-local-identifier" = 'Ares'
        ORDER BY timestamp
        """
    )
    return (df,)


@app.cell
def _(Point, ctx, df, gpd, plt):
    # 1. create geo points
    geometry = [Point(xy) for xy in zip(df["location-long"],
                                       df["location-lat"])]

    # 2. Create a WGS84 (standard lat / long) geoframe
    geo_df = gpd.GeoDataFrame(df, crs="EPSG:4326", geometry=geometry)

    # 3. Re-project to Web Mercrator
    geo_df = geo_df.to_crs(epsg=3857)

    # 4. Plotting
    fig, ax = plt.subplots(figsize=(8, 8))
    geo_df.plot(ax=ax, markersize=10, color="red", alpha=0.5, marker="o")

    # Add a basemap 
    ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)

    ax.set_axis_off()
    plt.title("Cat Moves")
    plt.show()
    return


@app.cell
def _(mo):
    _ = mo.sql(
        f"""
        CREATE VIEW cat_hulls_3857 AS
        SELECT 
            "tag-local-identifier",
            -- 2. Finally, transform the resulting polygon to Web Mercator (3857)
            ST_Transform(
                -- 1. Create the Convex Hull in the original 4326
                ST_ConvexHull(ST_Collect(list(ST_Point("location-long", "location-lat")))),
                'EPSG:4326', 
                'EPSG:3857'
            ) AS geometry
        FROM 'UK-pet-cats.csv'
        GROUP BY "tag-local-identifier";
        SELECT * FROM cat_hulls_3857;
        """,
        output=False
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Projection
    Initially used DuckDb to convert "spherical" lat/long (EPSG:4326) to "flat" meters (EPSG:3857), as the initial "Cat Moves" plot did this.

    Will now use folio (Leaflet.js) to create the map and it can convert on the fly
    """)
    return


@app.cell
def _(mo):
    area_df = mo.sql(
        f"""
        CREATE VIEW cat_hulls_area AS
        SELECT 
            "tag-local-identifier",
            -- 1. Get WKB, then 2. Cast to standard BLOB for Polars/Marimo
            ST_AsWKB(
                ST_ConvexHull(ST_Collect(list(ST_Point("location-long", "location-lat"))))
            )::BLOB AS geometry,
            ROUND(ST_Area_Spheroid(
                ST_ConvexHull(ST_Collect(list(ST_Point("location-long", "location-lat"))))
            ), 0) AS area_m2
        FROM 'UK-pet-cats.csv'
        -- WHERE "tag-local-identifier" = 'Bits-Tag'
        GROUP BY "tag-local-identifier";

        SELECT * FROM cat_hulls_area;
        """,
        output=False
    )
    return (area_df,)


@app.cell
def _(area_df, gpd, wkb):
    # Convert the Polars dataframe to Pandas
    pdf = area_df.to_pandas()

    # Convert the raw bytes to Shapely geometry
    # The bytes() call ensures we are passing a clean buffer to shapely
    pdf['geometry'] = pdf['geometry'].apply(lambda x: wkb.loads(bytes(x)))

    # Finalize the GeoDataFrame
    cat_gdf = gpd.GeoDataFrame(pdf, geometry='geometry', crs="EPSG:4326")
    return (cat_gdf,)


@app.cell
def _(cat_gdf):
    cat_gdf.explore(column="area_m2")
    return


@app.cell
def _(cat_gdf):
    # 1. Create a version of the data that is just points (the centers of the hulls)
    cat_centroids = cat_gdf.copy()
    cat_centroids['geometry'] = cat_gdf.centroid

    # 2. Plot the polygons first
    m = cat_gdf.explore(
        column="area_m2",
        cmap="plasma",
        style_kwds=dict(fillOpacity=0.5, weight=2),
        tooltip=["tag-local-identifier", "area_m2"],
        name="Home Range Polygons"
    )

    # 3. Add the centroids on top as markers that are easy to see
    cat_centroids.explore(
        m=m,                      # Plot on the same map 'm'
        color="black",            # Contrast color
        marker_kwds=dict(radius=5, fill=True),
        tooltip="tag-local-identifier",
        name="Cat Locations"
    )

    m
    return


@app.cell
def _(cat_gdf, folium):
    # 1. Create the base interactive map using the polygons
    mf = cat_gdf.explore(
        column="tag-local-identifier",  # Each cat gets its own color
        cmap="Set1",                   # High-contrast categorical colors
        style_kwds=dict(fillOpacity=0.4, weight=3),
        tooltip=["tag-local-identifier", "area_m2"],
        name="Cat Territories"
    )

    # 2. Add permanent labels at the center of each polygon
    for idx, row in cat_gdf.iterrows():
        # Calculate the center of the hull for the label placement
        centroid = row.geometry.centroid

        # Add a DivIcon (transparent background text) to the map
        folium.map.Marker(
            [centroid.y, centroid.x],
            icon=folium.DivIcon(
                html=f"""<div style="font-family: sans-serif; color: black; font-weight: bold; 
                         background-color: white; border: 1px solid black; border-radius: 3px; 
                         padding: 2px; font-size: 10pt; width: 80px;">
                         {row['tag-local-identifier']}</div>"""
            )
        ).add_to(mf)

    mf.save("cat_polygons_labeled.html")
    return (row,)


@app.cell
def _(mo):
    _df = mo.sql(
        f"""
        WITH daily_counts AS (
                SELECT 
                    "tag-local-identifier" AS tag_id, 
                    CAST(timestamp AS DATE) as gps_date, 
                    COUNT(*) as points_per_day
                FROM READ_CSV('UK-pet-cats.csv')
                GROUP BY tag_id, gps_date
            )
            SELECT 
                tag_id,
            	COUNT(*) AS active_days,
                MIN(points_per_day) as min_daily,
                MAX(points_per_day) as max_daily,
                ROUND(MEDIAN(points_per_day), 1) as median_daily,
                ROUND(AVG(points_per_day), 1) as avg_daily
            FROM daily_counts
            GROUP BY tag_id
            ORDER BY avg_daily DESC
        """
    )
    return


@app.cell
def _(Point, gpd, pd):
    # Load your GPS data
    all_df = pd.read_csv('UK-pet-cats.csv') 

    # Convert to GeoDataFrame
    geometry_2 = [Point(xy) for xy in zip(all_df["location-long"], all_df["location-lat"])] 
    gdf = gpd.GeoDataFrame(all_df, geometry=geometry_2, crs="EPSG:4326")

    # Important: Sort by timestamp to preserve movement patterns
    gdf['timestamp'] = pd.to_datetime(gdf['timestamp'])
    gdf = gdf.sort_values('timestamp')
    return (gdf,)


@app.cell
def _(gdf):
    gdf
    return


@app.cell
def _(mo):
    mo.md("""
    ### Home Range Polygons with GPS Points Toggle
    """)
    return


@app.cell
def _(cat_gdf, folium, pd, row):
    # Load all GPS points
    all_cats_df = pd.read_csv('UK-pet-cats.csv')

    # Create the base map with polygons
    m_toggle = cat_gdf.explore(
        column="area_m2",
        cmap="plasma",
        style_kwds=dict(fillOpacity=0.5, weight=2),
        tooltip=["tag-local-identifier", "area_m2"],
        name="Home Range Polygons",
        legend=True
    )

    # Add GPS points as a separate layer group
    gps_layer = folium.FeatureGroup(name="GPS Points", show=False)

    # Add individual GPS points for each cat
    for cat_id in cat_gdf["tag-local-identifier"].unique():
        cat_points = all_cats_df[all_cats_df["tag-local-identifier"] == cat_id]

        for idx2, row2 in cat_points.iterrows():
            folium.CircleMarker(
                location=[row["location-lat"], row["location-long"]],
                radius=3,
                popup=f"{cat_id}<br>{row['timestamp']}",
                tooltip=cat_id,
                color="red",
                fill=True,
                fillColor="red",
                fillOpacity=0.6,
                weight=1
            ).add_to(gps_layer)

    # Add the GPS points layer to the map
    gps_layer.add_to(m_toggle)

    # Add layer control to toggle between views
    folium.LayerControl(collapsed=False).add_to(m_toggle)

    m_toggle
    return


if __name__ == "__main__":
    app.run()
