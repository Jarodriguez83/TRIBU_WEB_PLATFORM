# BASE DE DATOS - CONFIGURACIÓN
from sqlmodel import SQLModel, create_engine, Session
from app.config import settings

# Crear motor de base de datos (PostgreSQL de Supabase, local, o SQLite)
# echo=True en desarrollo para auditar las queries generadas por SQLModel
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.es_desarrollo,
    pool_pre_ping=not settings.DATABASE_URL.startswith("sqlite"),
    connect_args=connect_args
)

def init_db():
    """Crea todas las tablas de SQLModel si no existen."""
    # Importamos los modelos antes de crear las tablas para que SQLModel los registre
    from app.models import models
    SQLModel.metadata.create_all(engine)

def get_session():
    """Generador de sesiones para la inyección de dependencias en las rutas."""
    with Session(engine) as session:
        yield session
