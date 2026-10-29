"""Configuración de la aplicación leída desde variables de entorno."""
import os

from dotenv import load_dotenv

load_dotenv()


def _split(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE", "short_links")

# URL pública base usada para construir short_url, p. ej. http://<ip-publica-ec2>:8000
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000").rstrip("/")

# Orígenes permitidos por CORS (la URL del sitio en S3), separados por comas.
CORS_ORIGINS = _split(os.getenv("CORS_ORIGINS", "http://localhost:5500"))

# Solo para pruebas locales con DynamoDB Local (en EC2 se deja vacío).
DYNAMODB_ENDPOINT_URL = os.getenv("DYNAMODB_ENDPOINT_URL") or None
