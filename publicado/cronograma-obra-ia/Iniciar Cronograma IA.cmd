@echo off
setlocal
title Cronograma IA
cd /d "%~dp0"

set "PY_ABS=C:\Users\Leonardo Manzo\AppData\Local\Programs\Python\Python312\python.exe"
if exist "%PY_ABS%" (
  set "PY=%PY_ABS%"
) else (
  set "PY=python"
)

set "VENV_DIR=%~dp0.venv"

if not exist "%VENV_DIR%\Scripts\python.exe" (
  echo Preparando o Cronograma IA pela primeira vez, aguarde um instante...
  "%PY%" -m venv "%VENV_DIR%"
  if errorlevel 1 (
    echo.
    echo Nao foi possivel criar o ambiente Python. Verifique se o Python esta instalado.
    pause
    exit /b 1
  )
  "%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip >nul
  "%VENV_DIR%\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 (
    echo.
    echo Falha ao instalar as dependencias. Veja o erro acima.
    pause
    exit /b 1
  )
)

"%VENV_DIR%\Scripts\python.exe" -m streamlit run app.py

pause
