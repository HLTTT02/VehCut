"""Compare evaluated model rows stored in metrics.csv."""
from __future__ import annotations

import csv
from pathlib import Path

rows = list(csv.DictReader(Path("ml/results/metrics.csv").open(encoding="utf-8")))
rows.sort(key=lambda row: float(row.get("map50_95", 0) or 0), reverse=True)
for row in rows:
    print(f"{row.get('model')}: mAP50-95={row.get('map50_95')}, recall={row.get('recall')}")
