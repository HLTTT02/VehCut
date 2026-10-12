"""Build a clean YOLO dataset containing only explicitly labelled no-plate samples.

The source dataset is read-only. Output labels are remapped to one class:
0 = no_plate.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import yaml

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
NO_PLATE_NAMES = {"no-plate", "no.plate", "no_plate", "noplate"}


def normalize(value: str) -> str:
    return value.strip().casefold().replace(" ", "-")


def load_names(data_yaml: Path) -> dict[int, str]:
    payload = yaml.safe_load(data_yaml.read_text(encoding="utf-8")) or {}
    names = payload.get("names", {})
    if isinstance(names, list):
        return dict(enumerate(map(str, names)))
    return {int(index): str(name) for index, name in names.items()}


def image_files(directory: Path) -> list[Path]:
    return sorted(item for item in directory.iterdir() if item.suffix.casefold() in IMAGE_SUFFIXES)


def filter_label(label_path: Path, target_ids: set[int]) -> list[str]:
    kept: list[str] = []
    for line in label_path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if not fields:
            continue
        try:
            class_id = int(fields[0])
        except ValueError as exc:
            raise ValueError(f"Invalid class id in {label_path}: {line!r}") from exc
        if class_id in target_ids:
            kept.append("0 " + " ".join(fields[1:]))
    return kept


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="Exported YOLO dataset root")
    parser.add_argument("--output", type=Path, required=True, help="New curated dataset directory")
    parser.add_argument("--data-yaml", type=Path, default=None, help="Defaults to SOURCE/data.yaml")
    args = parser.parse_args()

    source = args.source.resolve()
    output = args.output.resolve()
    data_yaml = (args.data_yaml or source / "data.yaml").resolve()
    if not data_yaml.is_file():
        raise FileNotFoundError(f"Missing dataset YAML: {data_yaml}")

    names = load_names(data_yaml)
    target_ids = {index for index, name in names.items() if normalize(name) in NO_PLATE_NAMES}
    if not target_ids:
        raise ValueError(f"No No-Plate class found in {data_yaml}; discovered: {names}")
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite existing output: {output}")

    report: dict[str, object] = {"source": str(source), "target_class_ids": sorted(target_ids), "splits": {}}
    for source_split, output_split in (("train", "train"), ("valid", "val"), ("val", "val"), ("test", "test")):
        images = source / source_split / "images"
        labels = source / source_split / "labels"
        if not images.is_dir():
            images = source / "images" / source_split
            labels = source / "labels" / source_split
        if not images.is_dir():
            continue

        target_images = output / "images" / output_split
        target_labels = output / "labels" / output_split
        target_images.mkdir(parents=True, exist_ok=True)
        target_labels.mkdir(parents=True, exist_ok=True)
        kept = skipped = 0
        for image in image_files(images):
            label = labels / f"{image.stem}.txt"
            if not label.is_file():
                skipped += 1
                continue
            annotations = filter_label(label, target_ids)
            if not annotations:
                skipped += 1
                continue
            shutil.copy2(image, target_images / image.name)
            (target_labels / label.name).write_text("\n".join(annotations) + "\n", encoding="utf-8")
            kept += 1
        report["splits"][output_split] = {"kept": kept, "skipped": skipped}

    (output / "data.yaml").write_text(
        "path: .\ntrain: images/train\nval: images/val\ntest: images/test\nnc: 1\nnames:\n  0: no_plate\n",
        encoding="utf-8",
    )
    (output / "filter_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
