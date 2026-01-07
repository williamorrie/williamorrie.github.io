
@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 3. Identifying Patterns with GeoAI
    Pattern identification in movement data typically falls into three categories: Clustering, Anomalies, and Stay-Point Detection.

    ### A. Spatial Clustering (Hotspots)
    If you want to find where a tracked object spends most of its time (e.g., "Frequent Stops"), use the spatial clustering capabilities integrated within the GeoAI ecosystem.
    """)
    return


@app.cell
def _(gdf):
    #  uv pip install geoai-py
    import geoai
    from sklearn.cluster import DBSCAN
    import numpy as np

    # Extract coordinates for clustering
    coords = np.array(list(gdf.geometry.apply(lambda x: (x.x, x.y))))

    # Use DBSCAN to find dense clusters (stay points)
    # eps is the distance threshold, min_samples is the minimum time points
    db = DBSCAN(eps=0.001, min_samples=10).fit(coords)
    gdf['cluster'] = db.labels_

    # Filter out noise (-1) to see actual pattern centers
    patterns = gdf[gdf['cluster'] != -1]
    return


@app.cell
def _(gdf):
    import leafmap

    m2 = leafmap.Map()
    # Add the movement points to the map
    m2.add_gdf(gdf, layer_name="GPS Path", zoom_to_layer=True)
    # If you have line-string trajectories
    m2.add_data(gdf, column='cluster', cmap='viridis') 
    m2
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### NOTE

    Adding GeoAI / using leafmap over folium was quite off putting
    1. GeoAI was a massive package (~ 850 MB)
    2. Took 25 sec to run the DBSCAN
    3. The resulting "leafmap" is really unresponsive
    """)
    return


if __name__ == "__main__":
    app.run()
