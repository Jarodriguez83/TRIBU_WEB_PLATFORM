# IMPORTACIONES PRINCIPALES  
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager

# IMPORTACIÓN DE ROUTERS
from app.routers import (
    auth, 
    productos, 
    pedidos, 
    pagos,  
    admin,  
    tienda
) 

# IMPORTACIÓN DE CONFIGURACIÓN
from app.config import settings  
from app.database.database import init_db

# LIFESPAN DE LA APLICACIÓN: EJECUTA CÓDIGOS ANTES DE INICIAR Y DESPUÉS DE DETENER LA APLICACIÓN
@asynccontextmanager
async def lifespan(app: FastAPI):
    # LO QUE SE EJECUTA ANTES DE INICIAR LA APLICACIÓN
    print(" INICIANDO APLICACIÓN DE TRIBU")
    print(f" AMBIENTE: {settings.ENVIRONMENT}")
    print(f" BASE URL: {settings.BASE_URL}")
    
    # Crear tablas en base de datos si no existen
    try:
        init_db()
        print(" BASE DE DATOS INICIALIZADA CORRECTAMENTE (TABLAS CREADAS)")
    except Exception as e:
        print(f" ERROR AL INICIALIZAR LA BASE DE DATOS: {e}")
        print(" Nota: Verifica tu DATABASE_URL en el archivo .env")

    yield  # AQUÍ SE INICIA LA APLICACIÓN
    
    # LO QUE SE EJECUTA DESPUÉS DE DETENER LA APLICACIÓN
    print(" DETENIENDO APLICACIÓN DE TRIBU")

# INSTANCIA PRINCIPAL DE FASTAPI
app = FastAPI(
    title="TRIBU STORE API",
    description="PLATAFORMA WEB DE LA TIENDA URBANA TRIBU - VIRTUAL STORE",
    version="0.1.0",
    lifespan=lifespan
)

# ARCHIVOS ESTÁTICOS
app.mount(
    "/static", 
    StaticFiles(directory="app/static"), 
    name="static"
)

# REGISTRO DE ROUTERS
# Nota: tienda.router se incluye de último por poseer rutas base comodín (wildcards)

app.include_router(auth.router)
app.include_router(productos.router)
app.include_router(pedidos.router)
app.include_router(pagos.router)
app.include_router(admin.router)
app.include_router(tienda.router)

# RUTA DE SALUD - VERIFICACIÓN DE QUE LA APLICACIÓN ESTÁ FUNCIONANDO
@app.get("/health", tags=["SISTEMA"])
async def health_check():
    return {
        "status": "OK", 
        "message": "TRIBU STORE API IS RUNNING!", 
        "version": "0.1.0", 
        "environment": settings.ENVIRONMENT
    }
