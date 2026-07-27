from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Protocol
from uuid import uuid4
from zoneinfo import ZoneInfo

from .credentials import delete_token, load_token, save_token
from .models import EventDraft

SCOPES = ["https://www.googleapis.com/auth/calendar"]


class CalendarAdapter(Protocol):
    def list_events(self, start: datetime, end: datetime) -> list[dict[str, Any]]: ...
    def create_event(self, draft: EventDraft, request_id: str) -> dict[str, Any]: ...
    def update_event(self, event_id: str, draft: EventDraft, etag: str | None) -> dict[str, Any]: ...
    def delete_event(self, event_id: str, etag: str | None) -> None: ...


class GoogleCalendar:
    def __init__(self) -> None:
        self._service = None

    @property
    def connected(self) -> bool:
        try:
            self._ensure_service()
            return True
        except Exception:
            return False

    def connect(self, client_secret_path: str) -> dict[str, Any]:
        from google_auth_oauthlib.flow import InstalledAppFlow
        flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
        creds = flow.run_local_server(port=0)
        save_token({
            "token": creds.token, "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri, "client_id": creds.client_id,
            "client_secret": creds.client_secret, "scopes": creds.scopes,
        })
        self._service = None
        return {"connected": True}

    def disconnect(self) -> None:
        delete_token()
        self._service = None

    def _ensure_service(self):
        if self._service:
            return self._service
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        info = load_token()
        if not info:
            raise RuntimeError("Google Agenda não conectado.")
        creds = Credentials.from_authorized_user_info(info, SCOPES)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            save_token({
                "token": creds.token, "refresh_token": creds.refresh_token,
                "token_uri": creds.token_uri, "client_id": creds.client_id,
                "client_secret": creds.client_secret, "scopes": creds.scopes,
            })
        self._service = build("calendar", "v3", credentials=creds, cache_discovery=False)
        return self._service

    def list_events(self, start: datetime | None = None, end: datetime | None = None) -> list[dict[str, Any]]:
        tz = ZoneInfo("America/Sao_Paulo")
        start = start or datetime.now(tz)
        end = end or start + timedelta(days=7)
        result = self._ensure_service().events().list(
            calendarId="primary", timeMin=start.isoformat(), timeMax=end.isoformat(),
            singleEvents=True, orderBy="startTime", maxResults=100
        ).execute()
        return [self._public(item) for item in result.get("items", [])]

    def create_event(self, draft: EventDraft, request_id: str | None = None) -> dict[str, Any]:
        draft.validate()
        body = self._body(draft)
        body["extendedProperties"] = {"private": {"agendaRetratilRequestId": request_id or str(uuid4())}}
        existing = self._ensure_service().events().list(
            calendarId="primary", privateExtendedProperty=f"agendaRetratilRequestId={body['extendedProperties']['private']['agendaRetratilRequestId']}",
            maxResults=1
        ).execute().get("items", [])
        item = existing[0] if existing else self._ensure_service().events().insert(calendarId="primary", body=body).execute()
        return self._public(item)

    def update_event(self, event_id: str, draft: EventDraft, etag: str | None) -> dict[str, Any]:
        draft.validate()
        current = self._ensure_service().events().get(calendarId="primary", eventId=event_id).execute()
        if etag and current.get("etag") != etag:
            raise RuntimeError("O evento mudou no Google Agenda. Sincronize antes de sobrescrever.")
        item = self._ensure_service().events().patch(calendarId="primary", eventId=event_id, body=self._body(draft)).execute()
        return self._public(item)

    def delete_event(self, event_id: str, etag: str | None) -> None:
        current = self._ensure_service().events().get(calendarId="primary", eventId=event_id).execute()
        if etag and current.get("etag") != etag:
            raise RuntimeError("O evento mudou no Google Agenda. Sincronize antes de excluir.")
        self._ensure_service().events().delete(calendarId="primary", eventId=event_id).execute()

    @staticmethod
    def _body(draft: EventDraft) -> dict[str, Any]:
        return {"summary": draft.title, "start": {"dateTime": draft.start.isoformat()},
                "end": {"dateTime": draft.end.isoformat()}, "location": draft.location,
                "description": draft.description}

    @staticmethod
    def _public(item: dict[str, Any]) -> dict[str, Any]:
        return {"id": item["id"], "title": item.get("summary", "(sem título)"),
                "start": item.get("start", {}).get("dateTime") or item.get("start", {}).get("date"),
                "end": item.get("end", {}).get("dateTime") or item.get("end", {}).get("date"),
                "location": item.get("location"), "etag": item.get("etag"), "html_link": item.get("htmlLink")}

