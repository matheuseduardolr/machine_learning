"""Transforma nome e endereço em coordenadas usadas como atributos do K-Means."""

from __future__ import annotations

import json
import re
import time
import unicodedata

from geopy.exc import (
    GeocoderQuotaExceeded,
    GeocoderServiceError,
    GeocoderTimedOut,
    GeocoderUnavailable,
)
from geopy.geocoders import ArcGIS

from project_clustering_kmeans.settings import (
    ACCEPTED_ADDR_TYPES,
    CACHE_PATH,
    KNOWN_COORDINATES,
    LAT_MAX,
    LAT_MIN,
    LON_MAX,
    LON_MIN,
    MIN_SCORE,
    STOPWORDS,
)


def fold(value: str) -> str:
    text = unicodedata.normalize("NFKD", value)
    text = "".join(char for char in text if not unicodedata.combining(char))
    return text.casefold()


def normalize_address(endereco: str) -> str:
    text = re.sub(r"\s+", " ", endereco).strip()
    text = re.sub(r"(^|\s)R\.\s*", r"\1Rua ", text, flags=re.IGNORECASE)
    text = re.sub(r"\bAv\.?\s+", "Avenida ", text, flags=re.IGNORECASE)
    text = re.sub(
        r"\bProf(?!essora?\b)[º°ªa\.]*(?=\s)",
        "Professor ",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"\bDr[aº°\.]*(?=\s)", "Doutor", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def street_candidates(endereco: str) -> list[str]:
    raw = normalize_address(endereco)
    raw = re.sub(r"\bn[º°]\.?\s*", " ", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\bs/n\b", " ", raw, flags=re.IGNORECASE)
    numbers = re.findall(r"\d+", raw)
    base = re.split(r"\b(?:lotes?|quadras?|qd)\b", raw, maxsplit=1, flags=re.IGNORECASE)[0]
    base = re.sub(r"[,;]+", " ", base)
    base = re.sub(r"\s+", " ", base).strip(" ,.-")
    name = re.sub(r"\d+", " ", base)
    name = re.sub(r"\s+", " ", name).strip(" ,.-")

    candidates: list[str] = []

    def add(value: str) -> None:
        value = re.sub(r"\s+", " ", value).strip(" ,.-")
        if len(value) >= 3 and value not in candidates:
            candidates.append(value)

    has_lot = re.search(r"\b(?:lotes?|qd|quadra)\b", raw, flags=re.IGNORECASE)
    if has_lot and numbers and name:
        add(f"{name} {numbers[-1]}")
    add(base)
    if numbers and name:
        add(f"{name} {numbers[-1]}")
    if name:
        add(name)
    return candidates


def in_bbox(lat: float, lon: float) -> bool:
    return LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX


def distinctive_tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", fold(text))
    return {word for word in words if len(word) > 2 and not word.isdigit() and word not in STOPWORDS}


def within_one_edit(left: str, right: str) -> bool:
    if abs(len(left) - len(right)) > 1 or min(len(left), len(right)) < 5:
        return False
    if len(left) == len(right):
        return sum(char_a != char_b for char_a, char_b in zip(left, right)) <= 1
    longer, shorter = (left, right) if len(left) > len(right) else (right, left)
    index_long = index_short = skips = 0
    while index_long < len(longer) and index_short < len(shorter):
        if longer[index_long] != shorter[index_short]:
            skips += 1
            if skips > 1:
                return False
            index_long += 1
            continue
        index_long += 1
        index_short += 1
    return True


def shares_token(expected: str, found: str) -> bool:
    expected_tokens = distinctive_tokens(expected)
    found_tokens = distinctive_tokens(found)
    if not expected_tokens or not found_tokens:
        return False
    return any(
        token == other or within_one_edit(token, other)
        for token in expected_tokens
        for other in found_tokens
    )


class Geocoder:
    def __init__(self) -> None:
        self.client = ArcGIS(timeout=20)
        self.cache: dict[str, dict | None] = {}
        if CACHE_PATH.exists():
            self.cache = json.loads(CACHE_PATH.read_text(encoding="utf-8"))

    def save(self) -> None:
        CACHE_PATH.write_text(
            json.dumps(self.cache, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def lookup(self, query: str, city: str, expected_text: str) -> dict | None:
        key = f"arcgis|{query}"
        if key in self.cache:
            return self.cache[key]

        location = None
        for attempt in range(3):
            try:
                location = self.client.geocode(query, out_fields="*")
                break
            except GeocoderQuotaExceeded:
                time.sleep(10)
            except (GeocoderTimedOut, GeocoderServiceError, GeocoderUnavailable):
                time.sleep(2 * (attempt + 1))
        time.sleep(0.25)

        payload = self._accept(location, city, expected_text)
        self.cache[key] = payload
        return payload

    def _accept(self, location, city: str, expected_text: str) -> dict | None:
        if location is None or not in_bbox(location.latitude, location.longitude):
            return None
        raw = location.raw or {}
        attributes = raw.get("attributes") or {}
        found_city = str(attributes.get("City") or "")
        addr_type = str(attributes.get("Addr_type") or "")
        if addr_type not in ACCEPTED_ADDR_TYPES:
            return None
        score = float(raw.get("score") or 0)
        if score < MIN_SCORE[addr_type]:
            return None
        matched = str(attributes.get("Match_addr") or location.address or "")
        if not shares_token(expected_text, matched):
            return None
        city_matches = fold(city) in fold(found_city)
        # A cidade da planilha às vezes não é a do logradouro. Nesse caso só vale
        # o resultado se a rua da coluna Endereço foi encontrada de fato.
        if not city_matches and addr_type == "POI":
            return None
        quality = "rua" if addr_type == "StreetName" else "endereco"
        return {
            "lat": location.latitude,
            "lon": location.longitude,
            "address": matched,
            "quality": quality,
            "score": score,
            "addr_type": addr_type,
            "city": found_city,
        }

    def geocode_row(
        self, ordem: int, nome: str, endereco: str, bairro: str, cidade: str
    ) -> dict | None:
        city = cidade.split("/")[0].strip()
        streets = [] if fold(endereco) == fold(bairro) else street_candidates(endereco)
        attempts: list[tuple[str, str]] = []
        for street in streets:
            attempts.append((f"{street}, {bairro}, {city}, Alagoas, Brasil", street))
        attempts.append((f"{nome}, {bairro}, {city}, Alagoas, Brasil", nome))
        for street in streets[:1]:
            attempts.append((f"{street}, {city}, Alagoas, Brasil", street))

        best_street = None
        for query, expected in attempts:
            found = self.lookup(query, city, expected)
            if found is None:
                continue
            if found["quality"] == "endereco":
                return {**found, "query": query}
            if best_street is None:
                best_street = {**found, "query": query}
        if best_street is not None:
            return best_street
        known = KNOWN_COORDINATES.get(ordem)
        if known is None:
            return None
        latitude, longitude = known
        return {
            "lat": latitude,
            "lon": longitude,
            "address": f"{endereco}, {bairro}, {cidade}",
            "quality": "informada",
            "score": None,
            "addr_type": "manual",
            "city": city,
            "query": "coordenada informada",
        }
