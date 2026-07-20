"""
01_generate_accident_data.py
-------------------------------
Generates a synthetic traffic accident dataset spanning 3 years across
6 cities, with realistic patterns baked in:
  - Higher accident rates during evening rush hour and late-night weekends
  - Longer accident durations for higher-severity incidents
  - Seasonal variation (more accidents in winter months)

Output: data/raw_traffic_accidents.csv
"""

import numpy as np
import pandas as pd

rng = np.random.default_rng(11)

CITIES = ["Hanoi", "Ho Chi Minh City", "Da Nang", "Hai Phong", "Can Tho", "Nha Trang"]
ROAD_TYPES = ["Highway", "Urban Street", "Intersection", "Bridge", "Residential"]
WEATHER = ["Clear", "Rain", "Fog", "Storm"]
SEVERITY = ["Minor", "Moderate", "Severe", "Fatal"]
SEVERITY_WEIGHTS = [0.55, 0.28, 0.13, 0.04]

N_ACCIDENTS = 26000

dates = pd.date_range("2023-01-01", "2025-12-31", freq="h")

records = []
for _ in range(N_ACCIDENTS):
    # Weight toward evening rush hour (17-20h) and late night (23-2h)
    hour_weights = np.ones(24)
    hour_weights[17:21] *= 3.0
    hour_weights[22:24] *= 2.0
    hour_weights[0:3] *= 2.2
    hour_weights[6:9] *= 1.8
    hour_weights /= hour_weights.sum()
    hour = rng.choice(24, p=hour_weights)

    # Seasonal weight: more accidents Nov-Feb
    month_weights = np.array([1.3, 1.2, 1.0, 0.9, 0.9, 0.9, 0.9, 0.9, 1.0, 1.1, 1.3, 1.4])
    month_weights /= month_weights.sum()
    month = rng.choice(np.arange(1, 13), p=month_weights)

    year = rng.choice([2023, 2024, 2025])
    day = rng.integers(1, 28)
    dt = pd.Timestamp(year=year, month=int(month), day=int(day), hour=int(hour))

    city = rng.choice(CITIES, p=[0.28, 0.30, 0.14, 0.12, 0.08, 0.08])
    road_type = rng.choice(ROAD_TYPES)
    weather = rng.choice(WEATHER, p=[0.6, 0.25, 0.1, 0.05])
    severity = rng.choice(SEVERITY, p=SEVERITY_WEIGHTS)

    # Duration correlated with severity
    base_duration = {"Minor": 20, "Moderate": 45, "Severe": 90, "Fatal": 150}[severity]
    duration = max(5, rng.normal(base_duration, base_duration * 0.3))

    is_night = 1 if (hour >= 22 or hour < 6) else 0

    records.append({
        "accident_id": f"ACC-{len(records):06d}",
        "accident_datetime": dt,
        "city": city,
        "road_type": road_type,
        "weather": weather,
        "severity": severity,
        "duration_minutes": round(duration, 1),
        "is_night": is_night,
        "vehicles_involved": rng.integers(1, 5),
    })

df = pd.DataFrame(records)
df.to_csv("data/raw_traffic_accidents.csv", index=False)
print(f"Generated {len(df):,} accident records -> data/raw_traffic_accidents.csv")
