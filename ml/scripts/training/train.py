"""Train an Ultralytics model from a YAML experiment config."""
from __future__ import annotations

import argparse
from pathlib import Path

import yaml
from ultralytics import YOLO

parser = argparse.ArgumentParser()
parser.add_argument("--config", required=True, type=Path)
args = parser.parse_args()
config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
model = YOLO(config.pop("model"))
model.train(**config)
