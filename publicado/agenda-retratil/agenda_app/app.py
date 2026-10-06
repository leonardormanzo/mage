from __future__ import annotations

from .api import Api, web_root

# Geometria copiada do modelo (index.html): painel colado na borda direita
# (right:0), só com respiro vertical de 8px; recolhido vira uma abinha
# pequena (22x56) centralizada na tela, também colada na borda.
EXPANDED_WIDTH = 360
PANEL_MARGIN_Y = 8
TAB_WIDTH = 22
TAB_HEIGHT = 56


def main() -> None:
    import webview

    screen = webview.screens[0]
    expanded = {
        "width": EXPANDED_WIDTH, "height": screen.height - 2 * PANEL_MARGIN_Y,
        "x": screen.width - EXPANDED_WIDTH, "y": PANEL_MARGIN_Y,
    }
    collapsed = {
        "width": TAB_WIDTH, "height": TAB_HEIGHT,
        "x": screen.width - TAB_WIDTH, "y": (screen.height - TAB_HEIGHT) // 2,
    }

    api = Api()
    window = webview.create_window(
        "Agenda Retrátil", str(web_root() / "index.html"), js_api=api,
        width=expanded["width"], height=expanded["height"], x=expanded["x"], y=expanded["y"],
        min_size=(TAB_WIDTH, TAB_HEIGHT), frameless=True, easy_drag=False, transparent=True,
        background_color="#171a1d", on_top=True,
    )
    api.bind_window(window, expanded, collapsed)
    webview.start(debug=False, private_mode=False)

