param(
  [Parameter(Mandatory = $true)][string]$Owner,
  [Parameter(Mandatory = $true)][string]$KernelSlug
)

$target = "ml/external/kaggle/kernels/$Owner/$KernelSlug"
New-Item -ItemType Directory -Force -Path $target | Out-Null
kaggle kernels pull "$Owner/$KernelSlug" -p $target -m
