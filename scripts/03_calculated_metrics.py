"""
03_calculated_metrics.py
---------------------------
Computes the calculated measures referenced in the case study:
  - Night accident percentage (overall, and by city / road type)
  - Accident duration statistics (mean, median, p90 by severity)

These map 1:1 to MDX calculated members (see mdx_queries.mdx) that would be
defined on the SSAS cube, e.g.:

  CREATE MEMBER CURRENTCUBE.[Measures].[Night Accident %] AS
      ([Measures].[Accident Count], [Time].[Is Night].&[1])
      / [Measures].[Accident Count];

Output: outputs/night_accident_pct.csv
        outputs/duration_stats_by_severity.csv
"""

import sqlite3

import pandas as pd

conn = sqlite3.connect("data/traffic_accidents.db")

# --- Night accident % overall and by city -----------------------------------
query_city = """
SELECT
    l.city,
    COUNT(*)                                              AS total_accidents,
    SUM(t.is_night)                                       AS night_accidents,
    ROUND(100.0 * SUM(t.is_night) / COUNT(*), 2)          AS night_accident_pct
FROM fact_accident f
JOIN dim_time t     ON f.time_id = t.time_id
JOIN dim_location l ON f.location_id = l.location_id
GROUP BY l.city
ORDER BY night_accident_pct DESC;
"""
night_by_city = pd.read_sql(query_city, conn)
night_by_city.to_csv("outputs/night_accident_pct.csv", index=False)

overall_pct = (
    night_by_city["night_accidents"].sum() / night_by_city["total_accidents"].sum() * 100
)

print("Night Accident % by City:")
print(night_by_city.to_string(index=False))
print(f"\nOverall night accident %: {overall_pct:.2f}%")

# --- Accident duration statistics by severity -------------------------------
query_duration = """
SELECT
    at.severity,
    COUNT(*)                                   AS accident_count,
    ROUND(AVG(f.duration_minutes), 1)          AS avg_duration_min,
    ROUND(MIN(f.duration_minutes), 1)          AS min_duration_min,
    ROUND(MAX(f.duration_minutes), 1)          AS max_duration_min
FROM fact_accident f
JOIN dim_accident_type at ON f.accident_type_id = at.accident_type_id
GROUP BY at.severity
ORDER BY avg_duration_min DESC;
"""
duration_stats = pd.read_sql(query_duration, conn)

# Median / p90 need pandas since SQLite lacks percentile functions
raw_durations = pd.read_sql("""
    SELECT at.severity, f.duration_minutes
    FROM fact_accident f
    JOIN dim_accident_type at ON f.accident_type_id = at.accident_type_id
""", conn)

pct_stats = raw_durations.groupby("severity")["duration_minutes"].agg(
    median_duration_min=lambda s: round(s.median(), 1),
    p90_duration_min=lambda s: round(s.quantile(0.9), 1),
).reset_index()

duration_stats = duration_stats.merge(pct_stats, on="severity")
duration_stats.to_csv("outputs/duration_stats_by_severity.csv", index=False)

print("\nAccident Duration Stats by Severity:")
print(duration_stats.to_string(index=False))

conn.close()
