from __future__ import annotations

from .api import Api, web_root


def main() -> None:
    import webview
    window = webview.create_window("Agenda Retrátil", str(web_root() / "index.html"), js_api=Api(),
                                   width=460, height=820, min_size=(380, 620),
                                   background_color="#171a1d", on_top=True)
    webview.start(debug=False, private_mode=False)

