Write-Host "Running mqquant full pipeline..."

$env:PYTHONPATH="$PWD\v2\src"

Write-Host "Step 1: Backtest M1"
python -m mqre_v2.cli.backtest_m1_to_latest --m1-path M1.txt --strategy-name auto_demo

Write-Host "Step 2: Run pipeline"
python -m mqre_v2.cli.run_latest_pipeline

Write-Host "Step 3: Git push"
git add runs/latest
git commit -m "auto update from pipeline" 2>$null
git push

Write-Host "Done!"
