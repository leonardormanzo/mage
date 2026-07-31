from __future__ import annotations

from datetime import date, datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .adapter import CalendarAdapter, CalendarConflictError
from .models import CalendarEvent, EventDraft


def _parse(value: dict):
    if "dateTime" in value:
        return datetime.fromisoformat(value["dateTime"].replace("Z", "+00:00"))
    return date.fromisoformat(value["date"])


def _event(resource: dict) -> CalendarEvent:
    return CalendarEvent(
        id=resource["id"],
        title=resource.get("summary", "(Sem título)"),
        start=_parse(resource["start"]),
        end=_parse(resource["end"]),
        location=resource.get("location"),
        html_link=resource.get("htmlLink"),
        etag=resource.get("etag"),
        recurring_event_id=resource.get("recurringEventId"),
    )


def _body(draft: EventDraft) -> dict:
    draft.validate()
    result = {"summary": draft.title.strip()}
    if isinstance(draft.start, datetime):
        result["start"] = {"dateTime": draft.start.isoformat()}
        result["end"] = {"dateTime": draft.end.isoformat()}
    else:
        result["start"] = {"date": draft.start.isoformat()}
        result["end"] = {"date": draft.end.isoformat()}
    if draft.location:
        result["location"] = draft.location
    if draft.description:
        result["description"] = draft.description
    return result


class GoogleCalendarAdapter(CalendarAdapter):
    def __init__(self, credentials):
        self.service = build("calendar", "v3", credentials=credentials, cache_discovery=False)

    def list_events(self, start: datetime, end: datetime) -> list[CalendarEvent]:
        response = self.service.events().list(
            calendarId="primary",
            timeMin=start.isoformat(),
            timeMax=end.isoformat(),
            singleEvents=True,
            orderBy="startTime",
            showDeleted=False,
            maxResults=250,
        ).execute(num_retries=3)
        return [_event(item) for item in response.get("items", []) if item.get("status") != "cancelled"]

    def get_event(self, event_id: str) -> CalendarEvent:
        return _event(self.service.events().get(calendarId="primary", eventId=event_id).execute(num_retries=3))

    def create_event(self, draft: EventDraft, request_id: str) -> CalendarEvent:
        body = _body(draft)
        body["extendedProperties"] = {"private": {"localRequestId": request_id}}
        existing = self.service.events().list(
            calendarId="primary",
            privateExtendedProperty=f"localRequestId={request_id}",
            maxResults=1,
        ).execute(num_retries=3).get("items", [])
        if existing:
            return _event(existing[0])
        return _event(self.service.events().insert(calendarId="primary", body=body).execute(num_retries=3))

    def update_event(self, event_id: str, draft: EventDraft, etag: str) -> CalendarEvent:
        request = self.service.events().patch(calendarId="primary", eventId=event_id, body=_body(draft))
        request.headers["If-Match"] = etag
        try:
            return _event(request.execute(num_retries=3))
        except HttpError as exc:
            if exc.resp.status == 412:
                raise CalendarConflictError("O evento foi alterado em outro lugar.") from exc
            raise

    def delete_event(self, event_id: str, etag: str) -> None:
        request = self.service.events().delete(calendarId="primary", eventId=event_id)
        request.headers["If-Match"] = etag
        try:
            request.execute(num_retries=3)
        except HttpError as exc:
            if exc.resp.status == 412:
                raise CalendarConflictError("O evento foi alterado em outro lugar.") from exc
            raise
