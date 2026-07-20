"""
04_reporting_charts.py
-------------------------
Builds the reporting visuals for Power BI / Looker Studio: accident trends
by year, month, time of day, and city. Also exports a flattened dataset
(fact + all dims joined) ready to import directly into Power BI or Looker
Studio without needing to model the star schema relationships manually.

Output: outputs/charts/*.png
        outputs/flattened_for_bi.csv
"""

import sqlite3

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

sns.set_theme(style="whitegrid")
conn = sqlite3.connect("data/traffic_accidents.db")

flat = pd.read_sql("""
    SELECT
        f.accident_id, f.duration_minutes, f.vehicles_involved,
        t.full_datetime, t.year, t.month, t.hour, t.day_of_week, t.is_night, t.is_weekend,
        l.city, l.road_type,
        at.severity, at.weather
    FROM fact_accident f
    JOIN dim_time t            ON f.time_id = t.time_id
    JOIN dim_location l        ON f.location_id = l.location_id
    JOIN dim_accident_type at  ON f.accident_type_id = at.accident_type_id
""", conn)
flat.to_csv("outputs/flattened_for_bi.csv", index=False)

# --- Chart 1: Accidents by year & month (trend) ------------------------------
monthly = flat.groupby(["year", "month"]).size().reset_index(name="accident_count")
monthly["period"] = monthly["year"].astype(str) + "-" + monthly["month"].astype(str).str.zfill(2)

plt.figure(figsize=(13, 5))
sns.lineplot(data=monthly, x="period", y="accident_count", marker="o", color="#f97316")
plt.title("Monthly Accident Trend (2023-2025)")
plt.xticks(rotation=60, ha="right", fontsize=8)
plt.ylabel("Accident Count")
plt.xlabel("")
plt.tight_layout()
plt.savefig("outputs/charts/01_monthly_trend.png", dpi=150)
plt.close()

# --- Chart 2: Accidents by hour of day (time-of-day pattern) -----------------
hourly = flat.groupby("hour").size().reset_index(name="accident_count")
plt.figure(figsize=(10, 5))
sns.barplot(data=hourly, x="hour", y="accident_count", color="#0ea5e9")
plt.title("Accident Count by Hour of Day")
plt.xlabel("Hour (24h)")
plt.ylabel("Accident Count")
plt.tight_layout()
plt.savefig("outputs/charts/02_hourly_pattern.png", dpi=150)
plt.close()

# --- Chart 3: Accidents by city ----------------------------------------------
by_city = flat.groupby("city").size().sort_values(ascending=False).reset_index(name="accident_count")
plt.figure(figsize=(9, 5))
sns.barplot(data=by_city, y="city", x="accident_count", color="#8b5cf6")
plt.title("Total Accidents by City")
plt.xlabel("Accident Count")
plt.ylabel("")
plt.tight_layout()
plt.savefig("outputs/charts/03_accidents_by_city.png", dpi=150)
plt.close()

# --- Chart 4: Night vs Day split by city -------------------------------------
night_split = flat.groupby(["city", "is_night"]).size().unstack(fill_value=0)
night_split.columns = ["Day", "Night"]
night_split_pct = night_split.div(night_split.sum(axis=1), axis=0) * 100

plt.figure(figsize=(9, 5))
night_split_pct[["Day", "Night"]].plot(kind="barh", stacked=True, ax=plt.gca(),
                                        color=["#cbd5e1", "#1e293b"])
plt.title("Day vs Night Accident Split by City (%)")
plt.xlabel("% of Accidents")
plt.tight_layout()
plt.savefig("outputs/charts/04_night_vs_day_by_city.png", dpi=150)
plt.close()

conn.close()
print("Charts saved to outputs/charts/")
print(f"Flattened BI dataset exported: outputs/flattened_for_bi.csv ({len(flat):,} rows)")
