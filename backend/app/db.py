"""Acceso a DynamoDB (capa de persistencia)."""
from datetime import datetime, timezone
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from . import config


def _get_table():
    # Sin claves explícitas: boto3 usa la cadena de credenciales por defecto,
    # que en EC2 obtiene credenciales temporales del rol IAM de la instancia.
    resource = boto3.resource(
        "dynamodb",
        region_name=config.AWS_REGION,
        endpoint_url=config.DYNAMODB_ENDPOINT_URL,
    )
    return resource.Table(config.DYNAMODB_TABLE)


_table = None


def table():
    global _table
    if _table is None:
        _table = _get_table()
    return _table


def save_link(short_code: str, original_url: str) -> dict:
    item = {
        "short_code": short_code,
        "original_url": original_url,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    # Evita sobrescribir un registro existente (colisión prácticamente imposible con UUID).
    table().put_item(
        Item=item,
        ConditionExpression="attribute_not_exists(short_code)",
    )
    return item


def get_link(short_code: str) -> Optional[dict]:
    try:
        response = table().get_item(Key={"short_code": short_code})
    except ClientError:
        raise
    return response.get("Item")
