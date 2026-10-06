from __future__ import annotations

import json
from typing import Any

import keyring

SERVICE = "site-diary-google-calendar"
ACCOUNT = "primary-calendar-oauth"


class SecureCredentialStore:
    """Stores authorized OAuth material in Windows Credential Manager."""

    def load(self) -> dict[str, Any] | None:
        raw = keyring.get_password(SERVICE, ACCOUNT)
        return json.loads(raw) if raw else None

    def save(self, value: dict[str, Any]) -> None:
        keyring.set_password(SERVICE, ACCOUNT, json.dumps(value))

    def clear(self) -> None:
        try:
            keyring.delete_password(SERVICE, ACCOUNT)
        except keyring.errors.PasswordDeleteError:
            pass

