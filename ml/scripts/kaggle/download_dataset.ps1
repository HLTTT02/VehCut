param(
  [Parameter(Mandatory = $true)][string]$Owner,
  [Parameter(Mandatory = $true)][string]$DatasetSlug,
  [string]$Version = "v1"
)

$target = "ml/data/raw/kaggle/$Owner/$DatasetSlug/$Version"
New-Item -ItemType Directory -Force -Path $target | Out-Null
kaggle datasets download -d "$Owner/$DatasetSlug" -p $target --unzip
