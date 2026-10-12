"""Evaluate a checkpoint and append metrics to the experiment table."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from ultralytics import YOLO

parser = argparse.ArgumentParser()
parser.add_argument("--model", required=True, type=Path)
parser.add_argument("--data", required=True, type=Path)
parser.add_argument("--name", required=True)
parser.add_argument("--imgsz", type=int, default=640)
args = parser.parse_args()
metrics = YOLO(str(args.model)).val(data=str(args.data), imgsz=args.imgsz)
output = Path("ml/results/metrics.csv")
write_header = not output.exists()
with output.open("a", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    if write_header:
        writer.writerow(["model", "precision", "recall", "map50", "map50_95"])
    writer.writerow([args.name, metrics.box.mp, metrics.box.mr, metrics.box.map50, metrics.box.map])
