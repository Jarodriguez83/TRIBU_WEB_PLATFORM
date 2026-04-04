import httpx
import hashlib
from app.config import get_settings

settings = get_settings()

WOMPI_BASE = {
    "sandbox": "https://sandbox.wompi.co/v1",
    "production": "https://production.wompi.co/v1"
}


def wompi_disponible() -> bool:
    """Retorna True solo si Wompi está configurado."""
    return bool(settings.wompi_private_key and settings.wompi_private_key != "prv_test_PENDIENTE")


def get_wompi_url() -> str:
    return WOMPI_BASE[settings.wompi_env]


async def crear_transaccion(
    referencia: str,
    monto_centavos: int,
    email_cliente: str,
    nombre_cliente: str
) -> dict:
    if not wompi_disponible():
        # Sin Wompi: retorna respuesta simulada para no romper el flujo
        return {"data": {"redirect_url": None, "status": "PENDING"}}

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{get_wompi_url()}/transactions",
            headers={"Authorization": f"Bearer {settings.wompi_private_key}"},
            json={
                "amount_in_cents": monto_centavos,
                "currency": "COP",
                "customer_email": email_cliente,
                "reference": referencia,
                "customer_data": {
                    "full_name": nombre_cliente,
                    "email": email_cliente
                }
            }
        )
        return resp.json()


def verificar_firma_webhook(firma: str, datos: str) -> bool:
    if not settings.wompi_events_secret:
        return False
    expected = hashlib.sha256(
        f"{datos}{settings.wompi_events_secret}".encode()
    ).hexdigest()
    return firma == expected


def generar_referencia(pedido_id: str) -> str:
    return f"TRIBU-{pedido_id[:8].upper()}"
