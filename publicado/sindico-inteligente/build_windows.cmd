@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" py -3.12 -m venv .venv
".venv\Scripts\python.exe" -m pip install -r requirements.txt
".venv\Scripts\pyinstaller.exe" --noconfirm --clean --windowed --name "Sindico Inteligente" --add-data "sindico_app\web;web" run.py

