@echo off
echo Running mqquant full pipeline...

set PYTHONPATH=%CD%\v2\src

echo Step 1: Run strategy search
python -m mqre_v2.cli.run_strategy_search ^
  --m1-path M1.txt ^
  --num-strategies 300 ^
  --seed 42 ^
  --start-date 2020-01-01 ^
  --end-date 2026-12-31

echo Step 2: Git commit
git add runs/latest reports
git commit -m "data: update L1-L4 pipeline outputs" || echo No changes
git push

echo Done!
pause
