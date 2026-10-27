from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class IncomingMessage:
    external_id: str
    origin_phone: str
    destination_phone: str
    message_type: str
    content: str


class WhatsAppProvider(ABC):
    @abstractmethod
    def parse_webhook(self, payload: dict) -> IncomingMessage:
        raise NotImplementedError

    @abstractmethod
    def send_text(self, destination: str, text: str) -> dict:
        raise NotImplementedError


class MockWhatsAppProvider(WhatsAppProvider):
    def parse_webhook(self, payload: dict) -> IncomingMessage:
        return IncomingMessage(
            external_id=payload["external_id"],
            origin_phone=payload.get("origin_phone", "mock-origin"),
            destination_phone=payload["destination_phone"],
            message_type=payload.get("message_type", "text"),
            content=payload.get("content", ""),
        )

    def send_text(self, destination: str, text: str) -> dict:
        return {"provider": "mock", "destination": destination, "text": text, "sent": True}


class MetaWhatsAppProvider(WhatsAppProvider):
    """Integração real com o WhatsApp Cloud API."""

    def __init__(self, access_token: str | None = None, phone_id: str | None = None):
        self.access_token = access_token
        self.phone_id = phone_id
        self.api_url = "https://graph.facebook.com/v19.0"

    def parse_webhook(self, payload: dict) -> IncomingMessage:
        try:
            entry = payload["entry"][0]
            changes = entry["changes"][0]
            value = changes["value"]
            
            # Identify destination phone (business phone)
            destination_phone = value["metadata"]["display_phone_number"]
            
            # The payload contains messages
            if "messages" not in value or not value["messages"]:
                raise ValueError("Nenhuma mensagem no payload")
                
            msg = value["messages"][0]
            message_type = msg.get("type", "unknown")
            
            content = ""
            if message_type == "text":
                content = msg["text"]["body"]
            elif message_type in ("image", "audio", "video", "document"):
                # Store the media ID to fetch later, or just signal there's media
                content = msg[message_type].get("id", "")
                
            return IncomingMessage(
                external_id=msg["id"],
                origin_phone=msg["from"],
                destination_phone=destination_phone,
                message_type=message_type,
                content=content,
            )
        except (KeyError, IndexError) as e:
            raise ValueError(f"Payload do WhatsApp malformado: {e}")

    def send_text(self, destination: str, text: str) -> dict:
        if not self.access_token or not self.phone_id:
            raise RuntimeError("WHATSAPP_ACCESS_TOKEN ou WHATSAPP_PHONE_ID não configurados")
            
        import httpx
        url = f"{self.api_url}/{self.phone_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": destination,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }
        
        response = httpx.post(url, headers=headers, json=data, timeout=10.0)
        response.raise_for_status()
        return response.json()
