"""API del acortador de enlaces (FastAPI + DynamoDB)."""
import uuid

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from . import config, db
from .schemas import LinkInfo, ShortenRequest, ShortenResponse

app = FastAPI(title="Acortador de enlaces", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


def _es_uuid(valor: str) -> bool:
    try:
        uuid.UUID(valor)
        return True
    except ValueError:
        return False


def _buscar_o_404(short_code: str) -> dict:
    # Un código que no es UUID nunca puede existir: se responde 404 sin consultar la base.
    if not _es_uuid(short_code):
        raise HTTPException(status_code=404, detail="Enlace no encontrado")
    try:
        item = db.get_link(short_code)
    except (ClientError, BotoCoreError):
        raise HTTPException(status_code=503, detail="No se pudo consultar la base de datos")
    if not item:
        raise HTTPException(status_code=404, detail="Enlace no encontrado")
    return item


@app.post("/shorten", response_model=ShortenResponse, status_code=201)
def shorten(body: ShortenRequest):
    short_code = str(uuid.uuid4())  # El UUID se genera en el backend
    try:
        db.save_link(short_code, body.original_url)
    except (ClientError, BotoCoreError):
        raise HTTPException(status_code=503, detail="No se pudo guardar el enlace en la base de datos")
    return ShortenResponse(
        short_code=short_code,
        original_url=body.original_url,
        short_url=f"{config.PUBLIC_BASE_URL}/{short_code}",
    )


@app.get("/urls/{short_code}", response_model=LinkInfo)
def link_info(short_code: str):
    item = _buscar_o_404(short_code)
    return LinkInfo(
        short_code=item["short_code"],
        original_url=item["original_url"],
        created_at=item["created_at"],
    )


# Debe declararse al final: es una ruta comodín que captura cualquier /{algo}.
@app.get("/{short_code}")
def redirect(short_code: str):
    item = _buscar_o_404(short_code)
    return RedirectResponse(url=item["original_url"], status_code=307)
