from fastapi import APIRouter, Request, Response, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from datetime import timedelta
from app.models.usuario import UsuarioCrear, UsuarioLogin
from app.services.auth_service import (
    hashear_password, verificar_password,
    crear_token, obtener_usuario_actual
)
from app.database import supabase
from app.config import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="app/templates")
settings = get_settings()


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    usuario = await obtener_usuario_actual(request)
    if usuario:
        return RedirectResponse("/tienda", status_code=302)
    return templates.TemplateResponse(request=request, name="tienda/login.html", context={})


@router.post("/login")
async def login(request: Request, datos: UsuarioLogin):
    resp = supabase.table("usuarios").select("*").eq("email", datos.email).single().execute()
    usuario = resp.data

    if not usuario or not verificar_password(datos.password, usuario["password_hash"]):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    if not usuario.get("activo"):
        raise HTTPException(status_code=403, detail="Cuenta desactivada")

    token = crear_token(
        {"sub": usuario["id"], "rol": usuario["rol"]},
        timedelta(minutes=settings.access_token_expire_minutes)
    )

    redirect_url = "/admin" if usuario["rol"] == "admin" else "/tienda"
    resp_redirect = RedirectResponse(redirect_url, status_code=302)
    resp_redirect.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=settings.access_token_expire_minutes * 60,
        samesite="lax"
    )
    return resp_redirect


@router.get("/registro", response_class=HTMLResponse)
async def registro_page(request: Request):
    return templates.TemplateResponse(request=request, name="tienda/registro.html", context={})


@router.post("/registro")
async def registro(datos: UsuarioCrear):
    existe = supabase.table("usuarios").select("id").eq("email", datos.email).execute()
    if existe.data:
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    nuevo = {
        "email": datos.email,
        "nombre": datos.nombre,
        "apellido": datos.apellido,
        "telefono": datos.telefono,
        "password_hash": hashear_password(datos.password),
        "rol": "cliente",
        "activo": True
    }
    supabase.table("usuarios").insert(nuevo).execute()
    return RedirectResponse("/auth/login", status_code=302)


@router.post("/logout")
async def logout():
    resp = RedirectResponse("/", status_code=302)
    resp.delete_cookie("access_token")
    return resp
