# VehCut ML workspace

`app/` only runs inference. This `ml/` workspace is for Kaggle sources, data curation, Colab training, evaluation, and model comparison.

## Data lifecycle

```text
Kaggle kernel/dataset
→ data/raw/kaggle (immutable)
→ data/interim (normalize, validate, deduplicate)
→ data/curated/vehicle_detection_v1
→ Colab experiment
→ model_weights (approved best.pt only)
```

## Kaggle

Pull a notebook into the planned folder:

```powershell
pwsh ml/scripts/kaggle/pull_kernel.ps1 -Owner tangocduc -KernelSlug yolo-v11-nano
```

Read its `kernel-metadata.json`, then download every declared dataset source:

```powershell
pwsh ml/scripts/kaggle/download_dataset.ps1 -Owner OWNER -DatasetSlug DATASET -Version v1
```

Raw data must never be modified. Only curated data is used for training. The placeholder model directory does not contain a fake `best.pt`; copy an approved Colab artifact into it after evaluation.
