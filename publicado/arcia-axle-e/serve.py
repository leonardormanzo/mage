"""Servidor local sem cache: o navegador sempre recarrega cart.js/textures.js atualizados.

POST /salvar?nome=arquivo.png grava o corpo da requisição (PNG) em imagens/ — usado pela
ficha técnica para exportar a imagem. Só aceita nomes simples terminados em .png.
"""
import http.server
import re
import socketserver
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
EXPORTS = Path(__file__).resolve().parent / "imagens"
SAFE_NAME = re.compile(r"^[\w\-]{1,80}\.png$")
MAX_BYTES = 40 * 1024 * 1024
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


class NoCache(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, must-revalidate")
        super().end_headers()

    def do_POST(self):
        url = urlparse(self.path)
        name = parse_qs(url.query).get("nome", [""])[0]
        length = int(self.headers.get("Content-Length") or 0)
        if url.path != "/salvar" or not SAFE_NAME.match(name):
            return self.send_error(400, "nome inválido")
        if not 0 < length <= MAX_BYTES:
            return self.send_error(413, "tamanho inválido")
        data = self.rfile.read(length)
        if not data.startswith(PNG_MAGIC):
            return self.send_error(415, "apenas PNG")
        EXPORTS.mkdir(exist_ok=True)
        (EXPORTS / name).write_bytes(data)
        self.send_response(201)
        self.end_headers()
        self.wfile.write(f"imagens/{name}".encode())


socketserver.TCPServer.allow_reuse_address = True
with socketserver.ThreadingTCPServer(("127.0.0.1", PORT), NoCache) as httpd:
    print(f"http://localhost:{PORT}/index.html")
    httpd.serve_forever()
