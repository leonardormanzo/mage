from __future__ import annotations

import json
import os
import shutil
import subprocess
import webbrowser
from pathlib import Path
from typing import Callable

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from .credentials import SecureCredentialStore

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


class OAuthManager:
    def __init__(self, store: SecureCredentialStore | None = None):
        self.store = store or SecureCredentialStore()

    def credentials(self) -> Credentials | None:
        saved = self.store.load()
        if not saved:
            return None
        credentials = Credentials.from_authorized_user_info(saved, SCOPES)
        if credentials.expired and credentials.refresh_token:
            try:
                credentials.refresh(Request())
                self.store.save(json.loads(credentials.to_json()))
            except Exception:
                self.store.clear()
                return None
        return credentials if credentials.valid else None

    def connect(
        self,
        client_secret_path: str,
        allow_default_browser: Callable[[], bool],
    ) -> Credentials:
        source = Path(client_secret_path).expanduser().resolve()
        if not source.is_file():
            raise FileNotFoundError("Arquivo de credenciais OAuth não encontrado.")

        flow = InstalledAppFlow.from_client_secrets_file(str(source), SCOPES)
        browser = self._chrome_controller()
        if browser is None:
            if not allow_default_browser():
                raise PermissionError("Uso do navegador padrão não autorizado.")
            browser_open = webbrowser.open
        else:
            browser_open = browser.open

        original_open = webbrowser.open
        webbrowser.open = browser_open
        try:
            credentials = flow.run_local_server(
                host="127.0.0.1",
                port=0,
                authorization_prompt_message="",
                success_message="Autorização concluída. Você pode fechar esta janela.",
                open_browser=True,
            )
        finally:
            webbrowser.open = original_open
        self.store.save(json.loads(credentials.to_json()))
        return credentials

    def disconnect(self) -> None:
        credentials = self.credentials()
        if credentials and credentials.token:
            try:
                from google.auth.transport.requests import AuthorizedSession
                AuthorizedSession(credentials).post(
                    "https://oauth2.googleapis.com/revoke",
                    params={"token": credentials.token},
                    timeout=10,
                )
            except Exception:
                pass
        self.store.clear()

    @staticmethod
    def _chrome_controller():
        candidates = [
            shutil.which("chrome"),
            os.path.join(os.environ.get("PROGRAMFILES", ""), "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "Application", "chrome.exe"),
        ]
        executable = next((path for path in candidates if path and os.path.isfile(path)), None)
        if not executable:
            return None

        class Chrome:
            @staticmethod
            def open(url: str, *_args, **_kwargs) -> bool:
                subprocess.Popen([executable, url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True

        return Chrome()
