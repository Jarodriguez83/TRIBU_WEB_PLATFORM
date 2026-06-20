from fastapi import APIRouter, Depends, Request, status, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session
from app.database.database import get_session
from app.models.models import Pedido, Transaccion, Producto
from app.services.wompi import WompiService
from app.services.auth import get_current_user_optional

router = APIRouter(prefix="/pagos", tags=["PAGOS WOMPI"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/confirmacion", response_class=HTMLResponse)
async def confirmacion_pago(request: Request, id: str, db: Session = Depends(get_session), user = Depends(get_current_user_optional)):
    """
    Ruta a la que Wompi redirige al usuario tras finalizar el pago.
    Recibe el ID de transacción de Wompi por parámetro query string '?id=...'.
    """
    # Consultar Wompi para ver el estado real de la transacción
    datos_transaccion = await WompiService.consultar_transaccion(id)
    if not datos_transaccion:
        return templates.TemplateResponse(
            "confirmacion_pago.html",
            {"request": request, "estado": "ERROR", "mensaje": "No se pudo verificar la transacción con Wompi.", "user": user}
        )
    
    referencia = datos_transaccion.get("reference")
    estado_wompi = datos_transaccion.get("status") # APPROVED, DECLINED, VOIDED, ERROR, PENDING
    metodo = datos_transaccion.get("payment_method_type")
    monto_centavos = datos_transaccion.get("amount_in_cents")
    monto = monto_centavos / 100.0 if monto_centavos else 0.0

    # Buscar el pedido correspondiente
    pedido = db.query(Pedido).filter(Pedido.referencia_wompi == referencia).first()
    if not pedido:
        return templates.TemplateResponse(
            "confirmacion_pago.html",
            {"request": request, "estado": "ERROR", "mensaje": f"No se encontró ningún pedido asociado a la referencia {referencia}.", "user": user}
        )

    # Buscar o crear registro de transacción en base de datos
    transaccion = db.query(Transaccion).filter(Transaccion.wompi_id == id).first()
    if not transaccion:
        transaccion = Transaccion(
            pedido_id=pedido.id,
            wompi_id=id,
            estado=estado_wompi.lower(),
            metodo_pago=metodo,
            monto=monto
        )
        db.add(transaccion)
    else:
        transaccion.estado = estado_wompi.lower()
        transaccion.metodo_pago = metodo
    
    # Actualizar estado del pedido basado en Wompi
    # Wompi statuses: APPROVED, DECLINED, VOIDED, ERROR, PENDING
    if estado_wompi == "APPROVED":
        if pedido.estado != "pagado":
            pedido.status_changed = True
            pedido.estado = "pagado"
            # Descontar stock de productos
            for detalle in pedido.detalles:
                producto = db.query(Producto).filter(Producto.id == detalle.producto_id).first()
                if producto:
                    producto.stock = max(0, producto.stock - detalle.cantidad)
    elif estado_wompi in ["DECLINED", "VOIDED", "ERROR"]:
        pedido.estado = "cancelado"
    elif estado_wompi == "PENDING":
        pedido.estado = "pendiente"

    db.commit()
    
    # Traducir estados para la vista
    estados_es = {
        "APPROVED": "APROBADO",
        "DECLINED": "RECHAZADO",
        "VOIDED": "ANULADO",
        "ERROR": "FALLIDO",
        "PENDING": "PENDIENTE"
    }
    
    estado_traducido = estados_es.get(estado_wompi, "DESCONOCIDO")
    
    return templates.TemplateResponse(
        "confirmacion_pago.html",
        {
            "request": request,
            "estado": estado_traducido,
            "pedido": pedido,
            "referencia": referencia,
            "monto": monto,
            "transaccion_id": id,
            "user": user
        }
    )

@router.post("/webhook")
async def webhook_wompi(request: Request, db: Session = Depends(get_session)):
    """
    Webhook para notificaciones asíncronas de Wompi (transacciones aprobadas o rechazadas).
    Documentación: https://docs.wompi.co/es/colombia/webhooks/
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="JSON corrupto")
        
    # Validar firma del webhook para mayor seguridad
    if not WompiService.validar_firma_webhook(payload):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Firma de webhook inválida")
    
    # Analizar datos
    event = payload.get("event")
    if event == "transaction.updated":
        data = payload.get("data", {})
        transaction = data.get("transaction", {})
        
        wompi_id = transaction.get("id")
        referencia = transaction.get("reference")
        estado_wompi = transaction.get("status")
        metodo = transaction.get("payment_method_type")
        monto_centavos = transaction.get("amount_in_cents")
        monto = monto_centavos / 100.0 if monto_centavos else 0.0
        
        # Buscar el pedido correspondiente
        pedido = db.query(Pedido).filter(Pedido.referencia_wompi == referencia).first()
        if not pedido:
            return JSONResponse(status_code=200, content={"message": "Pedido no encontrado"})
            
        # Buscar o crear transacción
        transaccion = db.query(Transaccion).filter(Transaccion.wompi_id == wompi_id).first()
        if not transaccion:
            transaccion = Transaccion(
                pedido_id=pedido.id,
                wompi_id=wompi_id,
                estado=estado_wompi.lower(),
                metodo_pago=metodo,
                monto=monto
            )
            db.add(transaccion)
        else:
            transaccion.estado = estado_wompi.lower()
            transaccion.metodo_pago = metodo
            
        # Actualizar stock de productos si pasa a aprobado y no estaba ya aprobado
        if estado_wompi == "APPROVED" and pedido.estado != "pagado":
            pedido.estado = "pagado"
            for detalle in pedido.detalles:
                producto = db.query(Producto).filter(Producto.id == detalle.producto_id).first()
                if producto:
                    producto.stock = max(0, producto.stock - detalle.cantidad)
        elif estado_wompi in ["DECLINED", "VOIDED", "ERROR"]:
            pedido.estado = "cancelado"
            
        db.commit()
        
    return JSONResponse(status_code=200, content={"status": "procesado"})
