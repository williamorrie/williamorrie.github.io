import marimo

__generated_with = "0.18.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import duckdb
    import marimo as mo

    DATABASE_URL = "_data/cats.duckdb"
    engine = duckdb.connect(DATABASE_URL, read_only=False)
    return engine, mo


@app.cell
def _(engine, mo):
    _df = mo.sql(
        f"""
        -- DROP TABLE IF EXISTS cat_points;
        -- DROP INDEX IF EXISTS spatial_idx;
        """,
        engine=engine
    )
    return


@app.cell
def _(engine, mo):
    df = mo.sql(
        f"""
        INSTALL spatial;
        LOAD spatial;

        -- 1. Create the table from your CSV
        CREATE TABLE IF NOT EXISTS cat_points AS 
        SELECT "timestamp",
            "tag-local-identifier" as "tag_id",
            ST_Point("location-long", "location-lat") AS geom 
        FROM read_csv_auto('_data/UK-pet-cats.csv');

        -- 2. Create the R-Tree spatial index
        CREATE INDEX IF NOT EXISTS spatial_idx ON cat_points USING RTREE (geom);
        """,
        engine=engine
    )
    return


@app.cell
def _(cat_points, engine, mo):
    _df = mo.sql(
        f"""
        SELECT COUNT (*) FROM cat_points
        """,
        engine=engine
    )
    return


@app.cell
def _(cat_points, engine, mo):
    _df = mo.sql(
        f"""
        SELECT 
            a.tag_id AS tag_1, a.timestamp AS timestamp_1,
            b.tag_id AS tag_2, b.timestamp AS timestamp_2,
            ST_Distance_Spheroid(a.geom, b.geom) as dist_meters,
        FROM cat_points a
        JOIN cat_points b
          ON date_trunc('hour', a.timestamp) = date_trunc('hour', b.timestamp)
        WHERE ST_DWithin(a.geom, b.geom, 0.005) -- roughly 500m in degrees
          AND a.tag_id < b.tag_id
        ORDER BY dist_meters;
        """,
        engine=engine
    )
    return


if __name__ == "__main__":
    app.run()
