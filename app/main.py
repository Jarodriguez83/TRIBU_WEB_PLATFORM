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

# LIFESPAN DE LA APLICACIÓN: EJECUTA CÓDIGOS ANTES DE INICIAR Y DESPUÉS DE DETENER LA APLICACIÓN
async def lifespan(app: FastAPI):
    # LO QUE SE EJECUTA ANTES DE INICIAR LA APLICACIÓN
    print(" INICIANDO APLICACIÓN DE TRIBU")
    print(f" AMBIENTE: {settings.ENVIRONMENT}")
    print(f" BASE URL: {settings.BASE_URL}")
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

# ARCHIVOS ESTÁTICOS Y PLANTILLAS
app.mount(
    "/static", 
    StaticFiles(directory="app/static"), 
    name="static"
    )

# REGISTRO DE ROUTERS
    # RUTAS PÚBLICAS    

    # RUTAS DE AUTENTICACIÓN

    # RUTAS DE PRODUCTOS

    # RUTAS DE PEDIDOS

    # RUTAS DE PAGOS

    # RUTAS DE ADMINISTRACIÓN

    # RUTA DE SALUD - VERIFICACIÓN DE QUE LA APLICACIÓN ESTÁ FUNCIONANDO
@app.get("/health", tags=["SISTEMA"])
async def health_check():
    return {
        "status": "OK", 
        "message": "TRIBU STORE API IS RUNNING!", 
        "version": "0.1.0", 
        "environment": settings.ENVIRONMENT
        }
