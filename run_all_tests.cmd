@echo off
set PYTHONPATH=%CD%\v2\src
python -m pytest -q
pause
