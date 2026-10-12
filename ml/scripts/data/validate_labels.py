"""Validate basic YOLO detection labels and report invalid rows."""
from __future__ import annotations

import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("labels", type=Path)
parser.add_argument("--class-count", type=int, default=4)
args = parser.parse_args()
errors = []
for label in args.labels.rglob("*.txt"):
    for line_no, line in enumerate(label.read_text(encoding="utf-8").splitlines(), 1):
        values = line.split()
        try:
            class_id, *coords = map(float, values)
            valid = len(values) == 5 and 0 <= class_id < args.class_count and all(0 <= value <= 1 for value in coords)
        except ValueError:
            valid = False
        if not valid:
            errors.append(f"{label}:{line_no}: {line}")
print("invalid_rows:", len(errors))
print("\n".join(errors[:100]))
