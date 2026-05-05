@echo off
cd /d "%~dp0"
set "PYTHONPATH=%CD%\v2\src"

python -m streamlit run v2/src/mqre_v2/gui/wfo_app.py
