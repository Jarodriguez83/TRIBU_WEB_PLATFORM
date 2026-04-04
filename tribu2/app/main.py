from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from app.config import get_settings

from app.routers import auth, productos, carrito, pedidos
from app.routers.admin import productos as admin_productos
from app.routers.admin import reportes as admin_reportes
from app.services.auth_service import obtener_usuario_actual

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    docs_url="/api/docs" if settings.app_env == "development" else None,
    redoc_url=None
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

app.include_router(auth.router)
app.include_router(productos.router)
app.include_router(carrito.router)
app.include_router(pedidos.router)
app.include_router(admin_productos.router)
app.include_router(admin_reportes.router)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    usuario = await obtener_usuario_actual(request)
    return templates.TemplateResponse(
        request=request,
        name="tienda/home.html",
        context={"usuario": usuario}
    )


@app.get("/admin", response_class=HTMLResponse)
async def admin_home(request: Request):
    from app.services.auth_service import requerir_admin
    admin = await requerir_admin(request)
    return templates.TemplateResponse(
        request=request,
        name="admin/dashboard.html",
        context={"admin": admin}
    )


@app.exception_handler(404)
async def not_found(request: Request, exc):
    return templates.TemplateResponse(
        request=request,
        name="tienda/404.html",
        context={},
        status_code=404
    )


@app.exception_handler(500)
async def server_error(request: Request, exc):
    return templates.TemplateResponse(
        request=request,
        name="tienda/500.html",
        context={},
        status_code=500
    )
