from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.models.carrito import CarritoAgregar
from app.services.auth_service import requerir_usuario
from app.database import supabase

router = APIRouter(prefix="/carrito", tags=["carrito"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def ver_carrito(request: Request, usuario: dict = Depends(requerir_usuario)):
    resp = supabase.table("carrito_items").select("*, productos(*)").eq("usuario_id", usuario["id"]).execute()
    items = resp.data or []
    total = sum(i["cantidad"] * i["productos"]["precio"] for i in items if i.get("productos"))
    return templates.TemplateResponse(
        request=request,
        name="tienda/carrito.html",
        context={"items": items, "total": total, "usuario": usuario}
    )


@router.post("/agregar")
async def agregar_item(datos: CarritoAgregar, usuario: dict = Depends(requerir_usuario)):
    stock = supabase.table("inventario").select("cantidad").eq("producto_id", datos.producto_id).eq("talla", datos.talla).eq("color", datos.color).single().execute()
    if not stock.data or stock.data["cantidad"] < datos.cantidad:
        raise HTTPException(status_code=400, detail="Stock insuficiente")

    existente = supabase.table("carrito_items").select("*").eq("usuario_id", usuario["id"]).eq("producto_id", datos.producto_id).eq("talla", datos.talla).eq("color", datos.color).execute()

    if existente.data:
        nueva_cantidad = existente.data[0]["cantidad"] + datos.cantidad
        supabase.table("carrito_items").update({"cantidad": nueva_cantidad}).eq("id", existente.data[0]["id"]).execute()
    else:
        supabase.table("carrito_items").insert({
            "usuario_id": usuario["id"],
            "producto_id": datos.producto_id,
            "talla": datos.talla,
            "color": datos.color,
            "cantidad": datos.cantidad
        }).execute()
    return {"mensaje": "Producto agregado al carrito"}


@router.delete("/item/{item_id}")
async def eliminar_item(item_id: str, usuario: dict = Depends(requerir_usuario)):
    supabase.table("carrito_items").delete().eq("id", item_id).eq("usuario_id", usuario["id"]).execute()
    return {"mensaje": "Item eliminado"}
