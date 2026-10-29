"""Modelos de entrada y salida de la API."""
from pydantic import BaseModel, field_validator


class ShortenRequest(BaseModel):
    original_url: str

    @field_validator("original_url")
    @classmethod
    def validar_url(cls, value: str) -> str:
        from urllib.parse import urlparse

        value = value.strip()
        parsed = urlparse(value)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValueError("La URL debe comenzar con http:// o https:// y tener un dominio válido")
        if len(value) > 2048:
            raise ValueError("La URL es demasiado larga (máximo 2048 caracteres)")
        return value


class ShortenResponse(BaseModel):
    short_code: str
    original_url: str
    short_url: str


class LinkInfo(BaseModel):
    short_code: str
    original_url: str
    created_at: str
