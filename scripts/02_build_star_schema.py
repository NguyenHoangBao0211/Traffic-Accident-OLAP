"""
02_build_star_schema.py
--------------------------
Designs and loads a star schema for the traffic accident data:

    dim_time        -- one row per hour (date, year, month, day, hour, is_night, day_of_week)
    dim_location     -- one row per (city, road_type) combination
    dim_accident_type-- one row per (severity, weather) combination
    fact_accident     -- grain: one row per accident, FKs into the three dims,
                          + measures (duration_minutes, vehicles_involved, accident_count=1)

This mirrors the dimensional model an SSAS cube would be built on top of.

Output: data/traffic_accidents.db (SQLite -- swap engine for real SQL Server + SSAS)
"""

import sqlite3

import pandas as pd

DB_PATH = "data/traffic_accidents.db"


def build_dim_time(df: pd.DataFrame) -> pd.DataFrame:
    dt = df["accident_datetime"]
    dim = pd.DataFrame({
        "time_id": dt.dt.strftime("%Y%m%d%H").astype(int),
        "full_datetime": dt,
        "year": dt.dt.year,
        "month": dt.dt.month,
        "day": dt.dt.day,
        "hour": dt.dt.hour,
        "day_of_week": dt.dt.day_name(),
        "is_night": df["is_night"],
        "is_weekend": dt.dt.dayofweek.isin([5, 6]).astype(int),
    }).drop_duplicates(subset="time_id")
    return dim


def build_dim_location(df: pd.DataFrame) -> pd.DataFrame:
    dim = df[["city", "road_type"]].drop_duplicates().reset_index(drop=True)
    dim.insert(0, "location_id", dim.index + 1)
    return dim


def build_dim_accident_type(df: pd.DataFrame) -> pd.DataFrame:
    dim = df[["severity", "weather"]].drop_duplicates().reset_index(drop=True)
    dim.insert(0, "accident_type_id", dim.index + 1)
    return dim


def build_fact(df: pd.DataFrame, dim_location: pd.DataFrame, dim_accident_type: pd.DataFrame) -> pd.DataFrame:
    fact = df.merge(dim_location, on=["city", "road_type"], how="left")
    fact = fact.merge(dim_accident_type, on=["severity", "weather"], how="left")
    fact["time_id"] = fact["accident_datetime"].dt.strftime("%Y%m%d%H").astype(int)

    fact = fact[[
        "accident_id", "time_id", "location_id", "accident_type_id",
        "duration_minutes", "vehicles_involved",
    ]].copy()
    fact["accident_count"] = 1
    return fact


if __name__ == "__main__":
    raw = pd.read_csv("data/raw_traffic_accidents.csv", parse_dates=["accident_datetime"])

    dim_time = build_dim_time(raw)
    dim_location = build_dim_location(raw)
    dim_accident_type = build_dim_accident_type(raw)
    fact = build_fact(raw, dim_location, dim_accident_type)

    conn = sqlite3.connect(DB_PATH)
    dim_time.to_sql("dim_time", conn, if_exists="replace", index=False)
    dim_location.to_sql("dim_location", conn, if_exists="replace", index=False)
    dim_accident_type.to_sql("dim_accident_type", conn, if_exists="replace", index=False)
    fact.to_sql("fact_accident", conn, if_exists="replace", index=False)

    for tbl, col in [("fact_accident", "time_id"), ("fact_accident", "location_id"),
                      ("fact_accident", "accident_type_id")]:
        conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{tbl}_{col} ON {tbl}({col})")
    conn.commit()
    conn.close()

    print(f"dim_time:          {len(dim_time):,} rows")
    print(f"dim_location:      {len(dim_location):,} rows")
    print(f"dim_accident_type: {len(dim_accident_type):,} rows")
    print(f"fact_accident:     {len(fact):,} rows")
    print(f"\nStar schema loaded -> {DB_PATH}")

    # --- Equivalent SQL Server + SSAS notes ---
    # 1. Load these same 4 tables into SQL Server (swap to pyodbc/SQLAlchemy mssql+pyodbc)
    # 2. In Visual Studio SSDT, create a new Analysis Services Multidimensional
    #    project, add a Data Source View over these 4 tables, and build a cube
    #    with fact_accident as the fact table and the 3 dims as dimensions.
    # 3. See mdx_queries.mdx for the equivalent MDX queries to run against the cube.
