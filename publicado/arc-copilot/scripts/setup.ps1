$ErrorActionPreference = "Stop"
if (-not (Test-Path ".venv")) { py -3.12 -m venv .venv }
& .\.venv\Scripts\python.exe -m pip install -e ".[dev]"
& .\.venv\Scripts\alembic.exe upgrade head
& .\.venv\Scripts\python.exe -m scripts.seed
Write-Host "Pronto. Execute: .\.venv\Scripts\uvicorn.exe app.main:app --reload"

