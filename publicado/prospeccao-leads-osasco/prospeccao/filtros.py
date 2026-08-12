"""Normalização dos resultados da Places API e filtro de empresas sem site."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Empresa:
    nome: str
    endereco: str
    telefone: Optional[str]
    rating: Optional[float]
    avaliacoes: Optional[int]
    tem_site: bool
    site: Optional[str]
    google_maps_url: Optional[str]
    status: Optional[str]


def normalizar_lugar(lugar: dict) -> Empresa:
    website = lugar.get("websiteUri")
    return Empresa(
        nome=lugar.get("displayName", {}).get("text", "").strip(),
        endereco=lugar.get("formattedAddress", ""),
        telefone=lugar.get("nationalPhoneNumber") or lugar.get("internationalPhoneNumber"),
        rating=lugar.get("rating"),
        avaliacoes=lugar.get("userRatingCount"),
        tem_site=bool(website),
        site=website,
        google_maps_url=lugar.get("googleMapsUri"),
        status=lugar.get("businessStatus"),
    )


def filtrar_sem_site(empresas: List[Empresa]) -> List[Empresa]:
    return [e for e in empresas if not e.tem_site]
