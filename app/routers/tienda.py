import uuid
from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session
from typing import Optional
from app.database.database import get_session
from app.models.models import Producto, Pedido, DetallePedido, Usuario
from app.services.auth import get_current_user_optional, get_current_user
from app.services.wompi import WompiService
from app.config import settings

router = APIRouter(tags=["TIENDA VIRTUAL"])
templates = Jinja2Templates(directory="app/templates")

# Listado de departamentos y ciudades de Colombia con tarifa de envío base
DEPARTAMENTOS_COLOMBIA = {
    "Bogota D.C.": {"ciudades": ["Bogota D.C."], "envio": 8000},
    "Antioquia": {"ciudades": ["Medellin", "Envigado", "Bello", "Itagui", "Rionegro"], "envio": 12000},
    "Cundinamarca": {"ciudades": ["Soacha", "Chia", "Zipaquira", "Facatativa"], "envio": 10000},
    "Valle del Cauca": {"ciudades": ["Cali", "Palmira", "Tulua", "Buenaventura"], "envio": 14000},
    "Atlantico": {"ciudades": ["Barranquilla", "Soledad", "Puerto Colombia"], "envio": 14000},
    "Santander": {"ciudades": ["Bucaramanga", "Floridablanca", "Giron"], "envio": 13000},
    "Bolivar": {"ciudades": ["Cartagena", "Turbaco"], "envio": 15000}
}

@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_session), user: Optional[Usuario] = Depends(get_current_user_optional)):
    """Página de inicio de TRIBU. Carga las colecciones destacadas (4 últimos productos)."""
    # Trae los 4 productos más recientes y activos
    productos_destacados = db.query(Producto).filter(Producto.activo == True).order_by(Producto.fecha_creacion.desc()).limit(4).all()
    return templates.TemplateResponse(
        "inicio.html", 
        {"request": request, "productos": productos_destacados, "user": user}
    )

@router.get("/catalogo", response_class=HTMLResponse)
async def catalogo(
    request: Request,
    categoria: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_session),
    user: Optional[Usuario] = Depends(get_current_user_optional)
):
    """Página del catálogo de productos con filtros por categoría y búsqueda."""
    query = db.query(Producto).filter(Producto.activo == True)
    
    if categoria:
        query = query.filter(Producto.categoria == categoria.lower())
    if search:
        query = query.filter(
            (Producto.nombre.ilike(f"%{search}%")) | 
            (Producto.descripcion.ilike(f"%{search}%"))
        )
        
    productos = query.order_by(Producto.fecha_creacion.desc()).all()
    return templates.TemplateResponse(
        "catalogo.html", 
        {"request": request, "productos": productos, "categoria_activa": categoria, "search": search, "user": user}
    )

@router.get("/producto/{producto_id}", response_class=HTMLResponse)
async def detalle_producto(
    request: Request,
    producto_id: uuid.UUID,
    db: Session = Depends(get_session),
    user: Optional[Usuario] = Depends(get_current_user_optional)
):
    """Página de detalle del producto."""
    producto = db.query(Producto).filter(Producto.id == producto_id, Producto.activo == True).first()
    if not producto:
        raise HTTPException(status_code=404, detail="El producto no existe o no está disponible.")
    
    # Trae 4 productos relacionados de la misma categoría
    relacionados = db.query(Producto).filter(
        Producto.categoria == producto.categoria,
        Producto.id != producto.id,
        Producto.activo == True
    ).limit(4).all()
    
    return templates.TemplateResponse(
        "producto.html", 
        {"request": request, "producto": producto, "relacionados": relacionados, "user": user}
    )

@router.get("/carrito", response_class=HTMLResponse)
async def carrito(request: Request, user: Optional[Usuario] = Depends(get_current_user_optional)):
    """Página del carrito de compras (se gestiona localmente en JS)."""
    return templates.TemplateResponse("carrito.html", {"request": request, "user": user})

@router.get("/checkout", response_class=HTMLResponse)
async def checkout_page(
    request: Request, 
    user: Usuario = Depends(get_current_user)
):
    """Página de formulario de envío y pago (requiere login)."""
    return templates.TemplateResponse(
        "checkout.html", 
        {"request": request, "user": user, "departamentos": DEPARTAMENTOS_COLOMBIA}
    )

@router.post("/checkout")
async def procesar_checkout(
    request: Request,
    nombre: str = Form(...),
    telefono: str = Form(...),
    direccion: str = Form(...),
    departamento: str = Form(...),
    ciudad: str = Form(...),
    cart_data: str = Form(...),  # Datos del carrito serializados en JSON desde el input hidden
    db: Session = Depends(get_session),
    user: Usuario = Depends(get_current_user)
):
    """
    Procesa los datos de envío, crea el pedido en estado 'pendiente' y
    renderiza la pantalla de pago de Wompi con la firma de integridad generada.
    """
    import json
    try:
        items = json.loads(cart_data)
        if not items:
            raise ValueError()
    except Exception:
        # Si el carrito está vacío o corrupto, redirige con error
        return RedirectResponse(url="/carrito?error=carrito_vacio", status_code=status.HTTP_303_SEE_OTHER)
    
    # Validar tarifa de envío basada en departamento
    envio_info = DEPARTAMENTOS_COLOMBIA.get(departamento, {"envio": 15000})
    costo_envio = envio_info["envio"]
    
    # Calcular el total de productos y validar existencias
    subtotal = 0.0
    detalles_pedido = []
    
    for item in items:
        prod_id = uuid.UUID(item["id"])
        talla = item["talla"]
        cantidad = int(item["cantidad"])
        
        producto = db.query(Producto).filter(Producto.id == prod_id, Producto.activo == True).first()
        if not producto or producto.stock < cantidad:
            # Si un producto ya no tiene stock, retornar al carrito con alerta
            return templates.TemplateResponse(
                "carrito.html",
                {"request": request, "user": user, "error": f"El producto {producto.nombre if producto else 'desconocido'} no cuenta con stock suficiente."}
            )
        
        item_total = producto.precio * cantidad
        subtotal += item_total
        
        # Guardar temporalmente el detalle
        detalles_pedido.append(
            DetallePedido(
                producto_id=producto.id,
                cantidad=cantidad,
                precio_unitario=producto.precio,
                talla=talla
            )
        )
    
    total = subtotal + costo_envio
    referencia_wompi = f"TRIBU-{uuid.uuid4().hex[:8].upper()}-{int(request.scope.get('timestamp', 0) or 0)}"
    
    # Crear Pedido
    pedido = Pedido(
        usuario_id=user.id,
        total=total,
        estado="pendiente",
        direccion_envio=direccion,
        ciudad=ciudad,
        departamento=departamento,
        costo_envio=costo_envio,
        referencia_wompi=referencia_wompi
    )
    db.add(pedido)
    db.commit()
    db.refresh(pedido)
    
    # Asignar ID de pedido a los detalles y guardarlos
    for detalle in detalles_pedido:
        detalle.pedido_id = pedido.id
        db.add(detalle)
    db.commit()
    
    # Generar firma de integridad para Wompi
    firma_integridad = WompiService.generar_firma_integridad(
        referencia=referencia_wompi,
        total_cop=total
    )
    
    # Renderizar pantalla de pasarela de pago (Widget de Wompi)
    return templates.TemplateResponse(
        "pago_wompi.html",
        {
            "request": request,
            "pedido": pedido,
            "referencia": referencia_wompi,
            "total_centavos": int(total * 100),
            "total": total,
            "wompi_public_key": settings.WOMPI_PUBLIC_KEY,
            "firma_integridad": firma_integridad,
            "redirect_url": f"{settings.BASE_URL}/pagos/confirmacion",
            "email_usuario": user.email,
            "nombre_usuario": user.nombre,
            "telefono_usuario": telefono or user.telefono
        }
    )

@router.get("/perfil", response_class=HTMLResponse)
async def perfil(request: Request, db: Session = Depends(get_session), user: Usuario = Depends(get_current_user)):
    """Muestra el perfil del usuario logueado con su historial de pedidos."""
    pedidos = db.query(Pedido).filter(Pedido.usuario_id == user.id).order_by(Pedido.fecha_creacion.desc()).all()
    return templates.TemplateResponse(
        "perfil.html", 
        {"request": request, "user": user, "pedidos": pedidos}
    )
