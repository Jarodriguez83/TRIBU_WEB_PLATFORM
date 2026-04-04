from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from app.database import supabase
from app.services.auth_service import obtener_usuario_actual

router = APIRouter(prefix="/tienda", tags=["tienda"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def catalogo(
    request: Request,
    categoria: Optional[str] = None,
    busqueda: Optional[str] = None,
    pagina: int = Query(default=1, ge=1)
):
    usuario = await obtener_usuario_actual(request)
    limite = 12
    offset = (pagina - 1) * limite

    query = supabase.table("productos").select("*").eq("activo", True)
    if categoria:
        query = query.eq("categoria", categoria)
    if busqueda:
        query = query.ilike("nombre", f"%{busqueda}%")

    resp = query.range(offset, offset + limite - 1).execute()

    return templates.TemplateResponse(
        request=request,
        name="tienda/catalogo.html",
        context={
            "productos": resp.data or [],
            "usuario": usuario,
            "categoria_activa": categoria,
            "busqueda": busqueda,
            "pagina": pagina
        }
    )


@router.get("/{slug}", response_class=HTMLResponse)
async def detalle_producto(request: Request, slug: str):
    usuario = await obtener_usuario_actual(request)
    resp = supabase.table("productos").select("*, inventario(*)").eq("slug", slug).eq("activo", True).single().execute()

    if not resp.data:
        return templates.TemplateResponse(
            request=request, name="tienda/404.html", context={}, status_code=404
        )

    return templates.TemplateResponse(
        request=request,
        name="tienda/producto.html",
        context={"producto": resp.data, "usuario": usuario}
    )
