.PHONY: setup up migrate seed test lint down

setup:
	python -m venv .venv
	.venv/Scripts/python -m pip install -e ".[dev]"

up:
	docker compose up --build

migrate:
	.venv/Scripts/alembic upgrade head

seed:
	.venv/Scripts/python -m scripts.seed

test:
	.venv/Scripts/python -m pytest

lint:
	.venv/Scripts/python -m ruff check .

down:
	docker compose down

