"""Print Kaggle dataset sources declared by pulled kernel metadata."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("metadata", type=Path)
args = parser.parse_args()
metadata = json.loads(args.metadata.read_text(encoding="utf-8"))
print("Dataset sources:")
for source in metadata.get("dataset_sources", []):
    print(f"- {source}")
