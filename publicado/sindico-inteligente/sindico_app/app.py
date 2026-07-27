from __future__ import annotations

from .api import Api, web_root


def main() -> None:
    import webview
    api = Api()
    webview.create_window(
        "Síndico Inteligente", str(web_root() / "index.html"), js_api=api,
        width=1380, height=860, min_size=(1040, 680), background_color="#171a1d"
    )
    webview.start(debug=False, private_mode=False)

