from __future__ import annotations

import html
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from .board import BoardStore

_STYLE = """
:root{--purple:#5b3df5;--text:#242331;--muted:#777786;--surface:#f7f7fb;--card:#ffffff;--line:#e7e6ee}
*{box-sizing:border-box}
body{margin:0;background:var(--surface);color:var(--text);font-family:"Segoe UI",Arial,sans-serif;min-height:100vh}
header{padding:22px 18px 16px;display:flex;gap:12px;align-items:center;border-bottom:1px solid var(--line);background:var(--card)}
header span{width:38px;height:38px;border-radius:9px;background:var(--purple);display:grid;place-items:center;color:#fff;font-weight:800;flex:none}
header h1{font-size:16px;margin:0;color:var(--text)}
header small{display:block;color:var(--muted);font-size:11px;margin-top:2px}
main{max-width:640px;margin:0 auto;padding:18px 16px 60px}
section{margin-bottom:26px}
section h2{font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--purple);margin:0 0 10px;font-weight:700}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px;margin-bottom:8px}
.card.event{display:grid;grid-template-columns:56px 1fr;gap:10px;border-left:3px solid var(--purple)}
.card time{color:var(--purple);font-size:12px;font-weight:700}
.card strong{display:block;font-size:13px}
.card small{color:var(--muted);font-size:11px}
.empty{border:1px dashed var(--line);border-radius:8px;padding:20px;text-align:center;color:var(--muted);font-size:12px}
footer{text-align:center;color:var(--muted);font-size:10px;padding:20px;border-top:1px solid var(--line)}
"""


def _esc(value: Any) -> str:
    return html.escape(str(value or ""))


def _list_section(title: str, rows: list[dict[str, Any]], empty_text: str) -> str:
    items = "".join(f'<div class="card"><strong>{_esc(r["label"])}</strong></div>' for r in rows if not r.get("done"))
    return f'<section><h2>{title}</h2>{items or f"<div class=\'empty\'>{empty_text}</div>"}</section>'


def _events_section(events: list[dict[str, Any]]) -> str:
    items = []
    for e in events:
        when = "Dia inteiro" if e["all_day"] else datetime.fromisoformat(e["start"]).strftime("%H:%M")
        day = datetime.fromisoformat(e["start"]).strftime("%d/%m")
        items.append(
            f'<div class="card event"><time>{_esc(when)}</time>'
            f'<div><strong>{_esc(e["title"])}</strong><small>{_esc(e.get("location") or "Sem local")} · {day}</small></div></div>'
        )
    body = "".join(items) or "<div class='empty'>Nenhum compromisso sincronizado.</div>"
    return f'<section><h2>Agenda do gestor</h2>{body}</section>'


def render_snapshot(store: BoardStore) -> str:
    body = (
        _list_section("Itens em aberto", store.open_items(), "Nenhum item em aberto no momento.")
        + _list_section("Metas da semana", store.goals("semana"), "Nenhuma meta definida para a semana.")
        + _list_section("Metas gerais", store.goals("geral"), "Nenhuma meta geral definida.")
        + _events_section(store.synced_events())
    )
    now = datetime.now().strftime("%d/%m %H:%M")
    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Painel da Obra</title><style>{_STYLE}</style></head>
<body>
<header><span>PB</span><div><h1>Painel da Obra</h1><small>Situação atual, publicada pelo gestor</small></div></header>
<main>
{body}
</main>
<footer>Publicado em {now} · atualizado manualmente pelo gestor · não é ao vivo</footer>
</body></html>"""


def default_output_dir() -> Path:
    # calendar_app/ -> painel-obra-desktop/ -> publicado/ -> irmã "painel-obra"
    return Path(__file__).resolve().parents[2] / "painel-obra"


def publish(store: BoardStore, output_dir: Path | None = None) -> Path:
    target = output_dir or default_output_dir()
    target.mkdir(parents=True, exist_ok=True)
    out_file = target / "index.html"
    out_file.write_text(render_snapshot(store), encoding="utf-8")
    return out_file
