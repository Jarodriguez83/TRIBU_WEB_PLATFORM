from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.services.auth_service import requerir_admin
from app.database import supabase_admin
from datetime import datetime, timedelta

router = APIRouter(prefix="/admin/reportes", tags=["admin-reportes"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def dashboard_reportes(request: Request, admin: dict = Depends(requerir_admin)):
    hace_30_dias = (datetime.utcnow() - timedelta(days=30)).isoformat()

    ventas = supabase_admin.table("pedidos").select("total, estado, creado_en").eq("estado", "pago_verificado").gte("creado_en", hace_30_dias).execute()
    total_ventas = sum(p["total"] for p in (ventas.data or []))
    cantidad_pedidos = len(ventas.data or [])

    nuevos_usuarios = supabase_admin.table("usuarios").select("id", count="exact").gte("creado_en", hace_30_dias).execute()

    return templates.TemplateResponse(
        request=request,
        name="admin/reportes/dashboard.html",
        context={
            "admin": admin,
            "total_ventas": total_ventas,
            "cantidad_pedidos": cantidad_pedidos,
            "nuevos_usuarios": nuevos_usuarios.count or 0,
            "ventas_recientes": ventas.data or []
        }
    )
