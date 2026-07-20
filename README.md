# Traffic Accident Data Analysis & OLAP Cube

Dimensional data modeling project: designs a star schema for traffic
accident data, builds an OLAP cube for multidimensional analysis, and
prepares reporting datasets for Power BI and Looker Studio.

**Stack:** Python, SQL (SQL Server-compatible / SQLite), Excel Pivot, MDX, SSAS, Power BI, Looker Studio

## Project Structure

```
traffic-accident-olap-cube/
├── data/
│   ├── raw_traffic_accidents.csv      # synthetic raw accident records
│   └── traffic_accidents.db           # SQLite star schema (4 tables)
├── scripts/
│   ├── 01_generate_accident_data.py
│   ├── 02_build_star_schema.py        # dims + fact table construction
│   ├── 03_calculated_metrics.py       # night % , duration stats
│   └── 04_reporting_charts.py         # BI-ready charts + flattened export
├── sql/
│   └── mdx_queries.mdx                # reference MDX for the real SSAS cube
└── outputs/
    ├── night_accident_pct.csv
    ├── duration_stats_by_severity.csv
    ├── flattened_for_bi.csv
    └── charts/
```

## 1. Data Modeling — Star Schema

`02_build_star_schema.py` designs a classic star schema:

| Table | Grain | Notes |
|---|---|---|
| `dim_time` | 1 row per hour | year, month, day, hour, day_of_week, is_night, is_weekend |
| `dim_location` | 1 row per (city, road_type) | 6 cities × 5 road types |
| `dim_accident_type` | 1 row per (severity, weather) | 4 severities × 4 weather conditions |
| `fact_accident` | 1 row per accident | FKs into all 3 dims + measures (duration, vehicles involved, count) |

> **Engine note:** loads into **SQLite** for a zero-install reproducible
> pipeline. The schema is identical to what you'd load into **SQL Server**
> to build the actual SSAS cube on top of — swap the SQLAlchemy engine
> string (see comments in the script) and nothing else changes.

## 2. OLAP Cube (SSAS) & MDX

The dimensional model above is exactly what SSAS needs: one fact table +
conformed dimensions. To build the real cube:

1. Load the 4 tables into SQL Server
2. In SSDT, create an Analysis Services Multidimensional project → Data
   Source View over the 4 tables → Cube Wizard with `fact_accident` as
   the measure group
3. Add calculated members (`Night Accident %`, `Avg Duration Minutes`) —
   full MDX in [`sql/mdx_queries.mdx`](sql/mdx_queries.mdx)

Since this repo doesn't ship a live SSAS server, `03_calculated_metrics.py`
computes the **same calculated measures in SQL** so the results are
reproducible without SSAS installed.

## 3. Calculated Measures — Key Results

**Night Accident %** (accidents occurring 22:00–06:00):

| City | Night Accident % |
|---|---|
| Can Tho | 35.4% |
| Da Nang | 35.3% |
| Hai Phong | 34.7% |
| Nha Trang | 33.7% |
| Ho Chi Minh City | 33.3% |
| Hanoi | 33.1% |
| **Overall** | **33.9%** |

**Accident Duration by Severity:**

| Severity | Avg (min) | Median (min) | P90 (min) |
|---|---|---|---|
| Fatal | 147.9 | 148.4 | 204.1 |
| Severe | 90.6 | 90.0 | 125.2 |
| Moderate | 45.1 | 45.1 | 62.5 |
| Minor | 19.9 | 19.9 | 27.6 |

## 4. Reporting — Power BI / Looker Studio

`04_reporting_charts.py` exports `outputs/flattened_for_bi.csv` — the fact
table pre-joined with all three dimensions — so it can be imported directly
into Power BI or Looker Studio without needing to rebuild the relationships.
It also generates the core trend charts:

- Monthly accident trend (seasonality — winter months peak)
- Accidents by hour of day (rush hour + late-night peaks)
- Accidents by city
- Day vs. night split by city

## How to Run

```bash
pip install -r requirements.txt
python scripts/01_generate_accident_data.py
python scripts/02_build_star_schema.py
python scripts/03_calculated_metrics.py
python scripts/04_reporting_charts.py
```

## Key Findings

- Accidents peak during **evening rush hour (17:00–20:00)** and
  **late night (22:00–02:00)**, together accounting for a disproportionate
  share of daily incidents.
- **~34% of all accidents occur at night**, despite night hours being a
  minority of the day — confirming higher per-hour night risk.
- Accident duration scales sharply with severity: a **Fatal** accident
  closes a road for **~2.5 hours on average**, ~7.5x longer than a Minor one.
- Winter months (Nov–Feb) show the highest accident volume, consistent with
  reduced visibility and wet/foggy road conditions.
