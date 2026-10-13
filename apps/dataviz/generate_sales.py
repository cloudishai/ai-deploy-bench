"""Generates fixtures/data/sales.csv deterministically.

The CSV is committed; rerun this only to change the dataset:

    python apps/dataviz/generate_sales.py
"""

import csv
import datetime as dt
import random
from pathlib import Path

SEED = 20250101
ROWS = 2400
REGIONS = ["North", "South", "East", "West"]
CATALOG = {
    "Electronics": [("Laptop", 899.0, 1499.0), ("Monitor", 149.0, 399.0), ("Headphones", 39.0, 249.0)],
    "Furniture": [("Desk", 199.0, 699.0), ("Office Chair", 99.0, 449.0), ("Bookshelf", 79.0, 249.0)],
    "Office Supplies": [("Paper Pack", 4.0, 12.0), ("Pens (12)", 3.0, 9.0), ("Stapler", 8.0, 25.0)],
    "Software": [("Antivirus License", 29.0, 79.0), ("Office Suite", 69.0, 149.0), ("Design Tool", 99.0, 299.0)],
}
# Seasonality and regional skew make filtered charts visibly different.
MONTH_WEIGHTS = [0.7, 0.75, 0.9, 0.95, 1.0, 1.0, 0.85, 0.9, 1.1, 1.15, 1.4, 1.6]
REGION_WEIGHTS = [1.0, 0.8, 1.2, 1.1]


def main() -> None:
    rng = random.Random(SEED)
    start = dt.date(2025, 1, 1)
    days = [start + dt.timedelta(days=i) for i in range(365)]
    day_weights = [MONTH_WEIGHTS[d.month - 1] for d in days]
    rows = []
    for date in sorted(rng.choices(days, weights=day_weights, k=ROWS)):
        category = rng.choice(list(CATALOG))
        product, low, high = rng.choice(CATALOG[category])
        units = rng.randint(1, 3) if category in ("Electronics", "Furniture") else rng.randint(1, 20)
        unit_price = round(rng.uniform(low, high), 2)
        rows.append(
            {
                "date": date.isoformat(),
                "region": rng.choices(REGIONS, weights=REGION_WEIGHTS)[0],
                "category": category,
                "product": product,
                "units": units,
                "unit_price": f"{unit_price:.2f}",
                "revenue": f"{round(units * unit_price, 2):.2f}",
            }
        )
    out = Path(__file__).parent / "fixtures" / "data" / "sales.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = ["order_id", "date", "region", "category", "product", "units", "unit_price", "revenue"]
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for i, row in enumerate(rows, start=1):
            writer.writerow({"order_id": f"SO-{i:05d}", **row})
    print(f"wrote {len(rows)} rows to {out}")


if __name__ == "__main__":
    main()
