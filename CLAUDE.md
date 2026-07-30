# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository purpose and layout

This is **not a single application** — it's Leonardo Manzo's personal monorepo that separates
public, shippable projects from private local-only files. Root layout:

- `publicado/` — every project here is version-controlled and pushed to GitHub / deployed publicly.
  Each subfolder is an **independent project** with its own README, dependencies, and (where
  applicable) its own git-ignore rules. There is no shared build system, package.json, or
  dependency tree across projects — treat each `publicado/<project>/` as its own root when working
  on it.
- `privado/` — local-only content (drafts, credentials, personal exports). Ignored by git via
  `.gitignore` at the repo root; it will not exist in a fresh checkout and must never be created
  or committed to.
- `Site/` — a legacy standalone export ("Mago da IA - Home Standalone.html") kept for reference;
  not part of the deployed site.
- `wrangler.toml` / `_redirects` — the repo root is deployed as a static site (Cloudflare
  Pages/Workers, `[assets] directory = "./"`). `_redirects` sends `/` → `/publicado/portfolio/`
  (302), i.e. the portfolio project is the public entry point.

When asked to work "on the repo" without a project named, ask which `publicado/<project>/` is
meant — changes rarely span more than one.

## The `publicado/` projects

Two shapes of project recur:

**A. Static single-page demos (HTML/CSS/JS, no backend, no build step)**
`checklist-de-obra/`, `diario-de-obra/`, `mago-da-ia/`, `portfolio/`, `vigia-obra-frontend/`, and
the web demo (`index.html`) inside `agenda-retratil/` and `sindico-inteligente/`. Each is a single
`index.html` (markup + styles + script inline). State lives only in memory/`localStorage` and does
not persist across reloads unless the README says otherwise. Open the file directly in a browser,
or serve the folder (`npx serve .`). There is no linter or bundler configured for these — don't
introduce one unless asked.

Several of these are explicitly **prototypes/demos**, not the real product — their READMEs contain
a "Falta para terminar" (what's left) section describing known gaps (no persistence, no real
backend wiring, broken legacy links, etc.). Check that section before assuming something is a bug.

**B. Local-first Python desktop apps (pywebview)**
`agenda-retratil/agenda_app/` and `sindico-inteligente/sindico_app/` share one architecture:

- `app.py` — creates a `pywebview` window pointed at `web/index.html`, with a Python `Api` object
  injected as `js_api`.
- `api.py` — the `Api` class is the entire boundary between JS and Python. Every method wraps its
  call in `_call()`, which returns `{"ok": True, "data": ...}` or `{"ok": False, "error": str(exc)}`
  — the JS side (`web/app.js`) always gets a uniform envelope, never a raw exception.
  `web_root()` resolves the frontend path differently depending on whether the app is frozen
  (PyInstaller `sys._MEIPASS`) or running from source.
- `web/` — the actual frontend (`index.html`, `app.js`, `styles.css`) that pywebview loads; it
  calls Python methods through the injected `js_api` bridge, not HTTP.
- `service.py` / `services.py` — business logic, called from `Api`, independent of pywebview.
- `db.py` — SQLite persistence, local data dir (`%LOCALAPPDATA%\<AppName>`).
- `models.py` — plain data classes used across `service`/`db`/`api`.
- Data never leaves the machine except through explicit, confirmation-gated integrations
  (`agenda_app/google_calendar.py` for Google Calendar OAuth; `credentials.py` stores tokens in the
  Windows Credential Manager via `keyring`). No AI key is required or embedded for either app to
  function.
- Distribution: `build_windows.cmd` creates a venv, installs `requirements.txt`, and runs
  PyInstaller with `--add-data "<app>/web;web"` to bundle the frontend into the executable.
  `launch_*.cmd` is the double-click entry point for end users (bootstraps the venv on first run).

**C. CLI/pipeline (no UI)**
`vigia-obra-seguranca/vigia_obra/` — analyzes a construction-site video with the Anthropic API and
flags safety non-conformities (NR-18, NR-6, NR-35). Structure:

- `main.py` — CLI entrypoint (`python -m vigia_obra.main <video> [--interval] [--max-frames]
  [--model] [--effort] [--output]`). Emits **NDJSON to stdout** (one JSON object per line, flushed
  immediately) so a parent process (e.g. an Electron/Tauri/Node frontend) can stream progress via
  subprocess without waiting for completion. Event types: `start`, `progress`, `error`, `done`. The
  `done` event's `disclaimer` field is the text a frontend **must** display — the assistive-only
  nature of the analysis is carried there, not in the occurrences JSON. `vigia-obra-frontend/` is a
  mocked prototype of that consumer (`mockEvents` in its `index.html`); it is not wired to the real
  pipeline yet.
- `frame_extractor.py` — extracts frames at a fixed interval via OpenCV (no `ffmpeg` dependency).
- `vision_analyzer.py` — sends a frame to the Claude API and parses detected occurrences.
- Requires `ANTHROPIC_API_KEY` in `.env` (copy from `.env.example`); cost scales linearly with
  frame count, so `--interval`/`--model` are the cost levers (see README for guidance).

## Common commands

Each Python project is self-contained; `cd` into it first.

**agenda-retratil/** and **sindico-inteligente/** (same pattern):
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python run.py                          # run the desktop app
.\.venv\Scripts\python -m unittest discover -s tests -v # run all tests
.\.venv\Scripts\python -m unittest tests.test_agenda.AgendaTests.test_name -v  # single test (agenda-retratil)
.\.venv\Scripts\python -m unittest tests.test_services.<TestClass>.<test_name> -v  # single test (sindico-inteligente)
.\build_windows.cmd                                     # build Windows executable into dist\
```
(Both use `unittest`, not pytest — no `pytest.ini`/`conftest.py` in either project.)

**vigia-obra-seguranca/**:
```sh
python -m venv .venv
.venv\Scripts\activate       # Windows; use source .venv/bin/activate on POSIX
pip install -r requirements.txt
copy .env.example .env       # then set ANTHROPIC_API_KEY
python -m vigia_obra.main path\to\video.mp4 --interval 5 --output ocorrencias.json
```
This project has no `tests/` directory currently.

**Static demo projects** (`checklist-de-obra/`, `diario-de-obra/`, `mago-da-ia/`, `portfolio/`,
`vigia-obra-frontend/`): no build/test/lint commands — open `index.html` directly, or `npx serve .`
to serve over HTTP.

There is no repo-wide build, lint, or test command — each project's commands above are scoped to
that project's folder only.

## Conventions

- Never write into `privado/` or otherwise try to "restore" it — it's intentionally absent from
  version control.
- Before committing anything, check `git status` to confirm no private/local files are staged
  (this is called out explicitly in the root README as the practical rule for this repo).
- New public projects go in their own `publicado/<project-name>/` folder with an `index.html` (for
  web projects) and a README describing what it is, how to run it, and — importantly — a section
  on what's simulated/mocked vs. real, matching the pattern every existing project README follows.
- Desktop apps (`agenda_app`, `sindico_app`) keep **all** state changes behind explicit user
  confirmation and never require a paid AI key to function; don't add functionality that silently
  calls external services.
