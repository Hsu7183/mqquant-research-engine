Write-Host "Running mqquant full pipeline..."

$env:PYTHONPATH="$PWD\v2\src"

Write-Host "Step 1: Run strategy search"
python -m mqre_v2.cli.run_strategy_search `
  --m1-path M1.txt `
  --num-strategies 300 `
  --seed 42 `
  --start-date 2020-01-01 `
  --end-date 2026-12-31 `
  --workers 0 `
  --progress-every 10 `
  --slippage-points 2 `
  --fee-money 0 `
  --tax-rate 0.00002 `
  --point-value 50 `
  --qty 1 `
  --min-net-profit-per-trade 0 `
  --max-trades-per-day 999999

Write-Host "Step 2: Git push"
git add runs/latest reports
git commit -m "data: update L1-L4 pipeline outputs" 2>$null
git push

Write-Host "Done!"
