Write-Host "Running mqquant full pipeline..."

$env:PYTHONPATH="$PWD\v2\src"

Write-Host "Step 1: Run L1-L4 pipeline"
python -m mqre_v2.cli.run_l1_l4_pipeline --m1-path M1.txt --strategy-name simple_m1_demo --start-date 2020-01-01 --end-date 2026-12-31

Write-Host "Step 2: Git push"
git add runs/latest reports
git commit -m "data: update L1-L4 pipeline outputs" 2>$null
git push

Write-Host "Done!"
