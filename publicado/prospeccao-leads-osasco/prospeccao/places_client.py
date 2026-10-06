"""Cliente mínimo para a Google Places API (New) - Text Search."""

import time
from typing import Iterator, Optional

import requests

PLACES_ENDPOINT = "https://places.googleapis.com/v1/places:searchText"

FIELD_MASK = ",".join(
    [
        "places.id",
        "places.displayName",
        "places.formattedAddress",
        "places.nationalPhoneNumber",
        "places.internationalPhoneNumber",
        "places.rating",
        "places.userRatingCount",
        "places.websiteUri",
        "places.googleMapsUri",
        "places.businessStatus",
        "nextPageToken",
    ]
)


class PlacesApiError(RuntimeError):
    """Erro de comunicação com a Google Places API."""


def buscar_empresas(
    query: str,
    api_key: str,
    max_paginas: int = 3,
    session: Optional[requests.Session] = None,
) -> Iterator[dict]:
    """Busca empresas via Text Search (New) e itera sobre os resultados brutos da API.

    Cada página traz até 20 resultados. A API exige um pequeno atraso antes de um
    nextPageToken ficar válido, por isso o sleep entre páginas.
    """
    sess = session or requests.Session()
    page_token = None
    paginas_lidas = 0

    while True:
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": FIELD_MASK,
        }
        body = {"textQuery": query}
        if page_token:
            body["pageToken"] = page_token

        resp = sess.post(PLACES_ENDPOINT, json=body, headers=headers, timeout=30)
        if resp.status_code != 200:
            raise PlacesApiError(f"Google Places API retornou {resp.status_code}: {resp.text}")

        data = resp.json()
        for lugar in data.get("places", []):
            yield lugar

        page_token = data.get("nextPageToken")
        paginas_lidas += 1
        if not page_token or paginas_lidas >= max_paginas:
            break
        time.sleep(2)
