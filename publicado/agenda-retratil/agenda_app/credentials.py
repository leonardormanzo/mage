from __future__ import annotations

import json
from typing import Any

SERVICE = "AgendaRetratil"
TOKEN_USER = "google-oauth-token"


def save_token(token: dict[str, Any]) -> None:
    import keyring
    keyring.set_password(SERVICE, TOKEN_USER, json.dumps(token))


def load_token() -> dict[str, Any] | None:
    import keyring
    value = keyring.get_password(SERVICE, TOKEN_USER)
    return json.loads(value) if value else None


def delete_token() -> None:
    import keyring
    try:
        keyring.delete_password(SERVICE, TOKEN_USER)
    except keyring.errors.PasswordDeleteError:
        pass

