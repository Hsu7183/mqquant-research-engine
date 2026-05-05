$RepoRoot = $PSScriptRoot
Set-Location $RepoRoot
$env:PYTHONPATH = Join-Path $RepoRoot "v2\src"

python -m streamlit run v2/src/mqre_v2/gui/wfo_app.py
