from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.models.pedido import PedidoCrear
from app.services.auth_service import requerir_usuario
from app.services.wompi import crear_transaccion, generar_referencia
from app.database import supabase
import uuid

router = APIRouter(prefix="/pedidos", tags=["pedidos"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def mis_pedidos(request: Request, usuario: dict = Depends(requerir_usuario)):
    resp = supabase.table("pedidos")\
        .select("*")\
        .eq("usuario_id", usuario["id"])\
        .order("creado_en", desc=True)\
        .execute()

    return templates.TemplateResponse("tienda/mis_pedidos.html", {
        "request": request,
        "pedidos": resp.data or [],
        "usuario": usuario
    })


@router.post("/crear")
async def crear_pedido(datos: PedidoCrear, usuario: dict = Depends(requerir_usuario)):
    total = sum(i.cantidad * i.precio_unitario for i in datos.items)
    pedido_id = str(uuid.uuid4())
    referencia = generar_referencia(pedido_id)

    pedido = {
        "id": pedido_id,
        "usuario_id": usuario["id"],
        "items": [i.dict() for i in datos.items],
        "direccion_envio": datos.direccion_envio.dict(),
        "total": total,
        "estado": "pendiente",
        "wompi_referencia": referencia,
        "notas": datos.notas
    }
    supabase.table("pedidos").insert(pedido).execute()

    # Crear transacción en Wompi (monto en centavos)
    wompi_resp = await crear_transaccion(
        referencia=referencia,
        monto_centavos=int(total * 100),
        email_cliente=usuario["email"],
        nombre_cliente=f"{usuario['nombre']} {usuario['apellido']}"
    )

    return {
        "pedido_id": pedido_id,
        "wompi_url": wompi_resp.get("data", {}).get("redirect_url"),
        "referencia": referencia
    }


@router.post("/webhook/wompi")
async def webhook_wompi(request: Request):
    """Recibe confirmaciones de pago de Wompi."""
    body = await request.json()
    evento = body.get("event")

    if evento == "transaction.updated":
        transaccion = body["data"]["transaction"]
        referencia = transaccion.get("reference")
        estado_wompi = transaccion.get("status")

        estado_pedido = {
            "APPROVED": "pago_verificado",
            "DECLINED": "cancelado",
            "VOIDED": "cancelado"
        }.get(estado_wompi, "pendiente")

        supabase.table("pedidos")\
            .update({
                "estado": estado_pedido,
                "wompi_transaction_id": transaccion.get("id")
            })\
            .eq("wompi_referencia", referencia)\
            .execute()

    return {"status": "ok"}
