from fastapi import APIRouter, Request, Depends, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional, List
from app.services.auth_service import requerir_admin
from app.database import supabase_admin
import uuid, re

router = APIRouter(prefix="/admin/productos", tags=["admin-productos"])
templates = Jinja2Templates(directory="app/templates")


def slugify(texto: str) -> str:
    texto = texto.lower().strip()
    texto = re.sub(r'[^\w\s-]', '', texto)
    texto = re.sub(r'[\s_-]+', '-', texto)
    return texto


@router.get("/", response_class=HTMLResponse)
async def listar_productos(request: Request, admin: dict = Depends(requerir_admin)):
    resp = supabase_admin.table("productos").select("*, inventario(*)").execute()
    return templates.TemplateResponse(
        request=request,
        name="admin/productos/lista.html",
        context={"productos": resp.data or [], "admin": admin}
    )


@router.get("/nuevo", response_class=HTMLResponse)
async def nuevo_producto_form(request: Request, admin: dict = Depends(requerir_admin)):
    return templates.TemplateResponse(
        request=request,
        name="admin/productos/form.html",
        context={"admin": admin, "producto": None}
    )


@router.post("/nuevo")
async def crear_producto(
    request: Request,
    admin: dict = Depends(requerir_admin),
    nombre: str = Form(...),
    descripcion: str = Form(...),
    precio: float = Form(...),
    categoria: str = Form(...),
    genero: str = Form(default="unisex"),
    imagenes: Optional[List[UploadFile]] = File(default=None)
):
    producto_id = str(uuid.uuid4())
    urls_imagenes = []

    if imagenes:
        for img in imagenes:
            if img.filename:
                ext = img.filename.split(".")[-1]
                path = f"productos/{producto_id}/{uuid.uuid4()}.{ext}"
                contenido = await img.read()
                supabase_admin.storage.from_("imagenes").upload(path, contenido)
                url = supabase_admin.storage.from_("imagenes").get_public_url(path)
                urls_imagenes.append(url)

    supabase_admin.table("productos").insert({
        "id": producto_id,
        "nombre": nombre,
        "descripcion": descripcion,
        "precio": precio,
        "categoria": categoria,
        "genero": genero,
        "slug": slugify(nombre),
        "imagenes": urls_imagenes,
        "activo": True
    }).execute()
    return RedirectResponse("/admin/productos", status_code=302)


@router.post("/{producto_id}/eliminar")
async def eliminar_producto(producto_id: str, admin: dict = Depends(requerir_admin)):
    supabase_admin.table("productos").update({"activo": False}).eq("id", producto_id).execute()
    return RedirectResponse("/admin/productos", status_code=302)
