from fastapi import APIRouter, Depends, Request, Form, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session
from app.database.database import get_session
from app.models.models import Producto, Pedido, Usuario
from app.services.auth import get_current_admin
import json

router = APIRouter(prefix="/admin", tags=["ADMINISTRACIÓN"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: Session = Depends(get_session),
    admin_user: Usuario = Depends(get_current_admin)
):
    """Muestra el panel de administración con todos los pedidos y productos."""
    pedidos = db.query(Pedido).order_by(Pedido.fecha_creacion.desc()).all()
    productos = db.query(Producto).order_by(Producto.fecha_creacion.desc()).all()
    return templates.TemplateResponse(
        "admin_dashboard.html",
        {"request": request, "pedidos": pedidos, "productos": productos, "user": admin_user}
    )

@router.get("/productos/nuevo", response_class=HTMLResponse)
async def nuevo_producto_page(
    request: Request,
    admin_user: Usuario = Depends(get_current_admin)
):
    """Muestra el formulario para registrar un nuevo producto."""
    return templates.TemplateResponse(
        "admin_nuevo_producto.html",
        {"request": request, "user": admin_user, "error": None}
    )

@router.post("/productos/nuevo")
async def crear_producto(
    request: Request,
    nombre: str = Form(...),
    descripcion: str = Form(...),
    precio: float = Form(...),
    stock: int = Form(...),
    categoria: str = Form(...),
    imagen_url: str = Form(None),
    tallas_raw: str = Form(...),  # Tallas separadas por comas, ej: "S, M, L"
    db: Session = Depends(get_session),
    admin_user: Usuario = Depends(get_current_admin)
):
    """Procesa el formulario y añade un nuevo producto a la base de datos."""
    # Convertir tallas de string separado por comas a lista
    tallas = [t.strip().upper() for t in tallas_raw.split(",") if t.strip()]
    
    nuevo_prod = Producto(
        nombre=nombre,
        descripcion=descripcion,
        precio=precio,
        stock=stock,
        categoria=categoria.lower(),
        imagen_url=imagen_url or "https://via.placeholder.com/400x500",  # Imagen por defecto si no hay url
        tallas=tallas,
        activo=True
    )
    
    db.add(nuevo_prod)
    db.commit()
    
    return RedirectResponse(url="/admin/dashboard", status_code=status.HTTP_303_SEE_OTHER)
