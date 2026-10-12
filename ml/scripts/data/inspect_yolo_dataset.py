"""Report image/label counts without modifying a dataset."""
from __future__ import annotations

import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("dataset", type=Path)
args = parser.parse_args()
images = [path for path in args.dataset.rglob("*") if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}]
labels = list(args.dataset.rglob("*.txt"))
print({"images": len(images), "labels": len(labels), "yaml": [str(path) for path in args.dataset.rglob("*.yaml")]})
