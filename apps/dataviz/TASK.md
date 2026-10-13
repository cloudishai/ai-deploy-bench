# Data / Visualization App: Sales Dashboard

Build an interactive sales dashboard for a small company, using its order data in
`data/sales.csv`: 2,400 order lines from 2025.

## Data

`data/sales.csv` has the columns `order_id`, `date` (YYYY-MM-DD), `region`, `category`, `product`,
`units`, `unit_price` and `revenue` (units × unit_price). It is the app's read-only data source;
you may load it into a database or keep it in memory.

## Dashboard (`GET /`)

- Filters for region, category and a date range.
- KPI tiles: total revenue, number of orders, and units sold.
- Charts: revenue by month (line or bar) and revenue by category (bar or pie).
- Changing a filter updates the KPIs and charts without a full page reload.
- A table of the matching orders, paginated or limited (for example the latest 50).

## Summary API (`GET /api/summary`)

Optional query parameters, combined with AND: `region` and `category` (exact match), `start` and
`end` (inclusive dates, YYYY-MM-DD). Responds `200` with:

```json
{
  "total_revenue": 123456.78,
  "orders": 1234,
  "units": 5678,
  "revenue_by_month": [{"month": "2025-01", "revenue": 10234.5}],
  "revenue_by_category": [{"category": "Electronics", "revenue": 50000.0}]
}
```

- `orders` is the number of matching rows, and `units` the sum of their `units`. Revenue values are
  sums of `revenue` rounded to 2 decimals.
- `revenue_by_month` lists months that have matching rows, in ascending order.
- `revenue_by_category` lists categories that have matching rows, by revenue in descending order.
- When no rows match, respond with zeros and empty arrays.
