@echo off
echo Running mqquant full pipeline...

set PYTHONPATH=%CD%\v2\src

echo Step 1: Backtest M1
python -m mqre_v2.cli.backtest_m1_to_latest --m1-path M1.txt --strategy-name auto_demo

echo Step 2: Run pipeline
python -m mqre_v2.cli.run_latest_pipeline

echo Step 3: Git commit
git add runs/latest
git commit -m "auto update from pipeline" || echo No changes
git push

echo Done!
pause
