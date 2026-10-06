from __future__ import annotations

import html
from datetime import datetime
from typing import Any

_STYLE = """
:root{--bg:#16191c;--panel:#20252a;--line:#394149;--text:#f2f3ee;--muted:#9ca6ac;--orange:#ff7a1a;--green:#42bd79}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font-family:"Segoe UI",Arial,sans-serif;min-height:100vh;border-top:4px solid var(--orange)}
header{padding:22px 18px 16px;display:flex;gap:12px;align-items:center;border-bottom:1px solid var(--line)}
header span{width:38px;height:38px;border:2px solid var(--orange);display:grid;place-items:center;color:var(--orange);font-weight:800;flex:none}
header h1{font-size:16px;margin:0}
header small{display:block;color:var(--muted);font-size:11px;margin-top:2px}
main{max-width:640px;margin:0 auto;padding:18px 16px 60px}
section{margin-bottom:26px}
section h2{font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--orange);margin:0 0 10px;font-weight:700}
.card{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:12px;margin-bottom:8px}
.card.event{display:grid;grid-template-columns:52px 1fr;gap:10px;border-left:3px solid var(--orange)}
.card time{color:var(--orange);font-size:12px;font-weight:700}
.card strong{display:block;font-size:13px}
.card small{color:var(--muted);font-size:11px}
.empty{border:1px dashed var(--line);border-radius:8px;padding:20px;text-align:center;color:var(--muted);font-size:12px}
.sync{font-size:11px;color:var(--muted);display:flex;align-items:center;gap:6px;margin-bottom:16px}
.dot{width:7px;height:7px;border-radius:50%;background:var(--green);display:inline-block}
footer{text-align:center;color:var(--muted);font-size:10px;padding:20px;border-top:1px solid var(--line)}
"""


def _esc(value: Any) -> str:
    return html.escape(str(value or ""))


def _fmt_dt(value: str | None) -> str:
    if not value:
        return "—"
    try:
        dt = datetime.fromisoformat(value)
        return dt.strftime("%d/%m %H:%M")
    except ValueError:
        return value[:10]


def _list_section(title: str, rows: list[dict[str, Any]], empty_text: str) -> str:
    items = "".join(f'<div class="card"><strong>{_esc(r["label"])}</strong></div>' for r in rows)
    return f'<section><h2>{title}</h2>{items or f"<div class=\'empty\'>{empty_text}</div>"}</section>'


def _events_section(events: list[dict[str, Any]]) -> str:
    items = "".join(
        f'<div class="card event"><time>{_fmt_dt(e["start"])[3:]}</time>'
        f'<div><strong>{_esc(e["title"])}</strong><small>{_esc(e.get("location") or "Sem local")} · {_fmt_dt(e["start"])}</small></div></div>'
        for e in events
    )
    return f'<section><h2>Agenda do gestor</h2>{items or "<div class=\'empty\'>Nenhum compromisso sincronizado.</div>"}</section>'


def render_snapshot(payload: dict[str, Any]) -> str:
    sync = payload["sync"]
    last_sync = _fmt_dt(sync.get("last_sync")) if sync.get("last_sync") else "nunca"
    body = (
        _list_section("Itens em aberto", payload["open_items"], "Nenhum item em aberto no momento.")
        + _list_section("Metas da semana", payload["weekly_goals"], "Nenhuma meta definida para a semana.")
        + _list_section("Metas gerais", payload["general_goals"], "Nenhuma meta geral definida.")
        + _events_section(payload["events"])
    )
    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Painel da Obra</title><style>{_STYLE}</style></head>
<body>
<header><span>CH3</span><div><h1>Painel da Obra</h1><small>Situação atual, publicada pelo gestor</small></div></header>
<main>
<div class="sync"><span class="dot"></span>Última sincronização com o Google Agenda: {last_sync}</div>
{body}
</main>
<footer>Atualizado manualmente pelo gestor · não é ao vivo</footer>
</body></html>"""
