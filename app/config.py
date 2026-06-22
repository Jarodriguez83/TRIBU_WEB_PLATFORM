# IMPORTACIONES
from pydantic_settings import BaseSettings
from pydantic import field_validator, ValidationInfo
from typing import Literal
from functools import lru_cache

# CONFIGURACIÓN DE LA APLICACIÓN
class Settings(BaseSettings):  

    #APLICACIÓN: 
    APP_NAME: str = "TRIBU STORE API"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    BASE_URL: str = "http://localhost:8000"
    SECRET_KEY: str

    # SUPABASE
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_BUCKET_PRODUCTOS: str = "productos"
    SUPABASE_BUCKET_AVATARS: str = "avatars"

    # BASE DE DATOS - POSTGRESQL DE SUPABASE
    DATABASE_URL: str

    # AUTENTICACIÓN  
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24  # 1 DÍA
    JWT_REFRESH_EXPIRE_DAYS: int = 7  # 7 DÍAS

    # SESIONES
    SESSION_SECRET_KEY: str
    SESSION_MAX_AGE: int = 60 * 60 * 24 * 7  # 7 DÍAS

    # PAGOS WOMPI
    WOMPI_PUBLIC_KEY: str
    WOMPI_PRIVATE_KEY: str
    WOMPI_EVENTS_KEY: str  #TODO: PARA VALIDAR LOS WEBHOOKS DE WOMPI
    WOMPI_BASE_URL: str = "https://sandbox.wompi.co/v1" #TODO: CAMBIAR A PRODUCCIÓN

    # EMAIL 
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_FROM_NAME: str = "TRIBU STORE"
    MAIL_STARTTLS: bool = True # PARA USAR TLS  
    MAIL_SSL_TLS: bool = False # PARA USAR SSL/TLS

    # IMAGENES  
    MAX_IMAGE_SIZE: int = 5 
    ALLOWED_IMAGE_TYPES: list[str] = ["image/jpeg", "image/png", "image/webp"]

    # PAGINACIÓN 
    ITEMS_PER_PAGE: int = 12

    # VALIDADORES 
    @field_validator("SECRET_KEY", "JWT_SECRET_KEY", "SESSION_SECRET_KEY")
    @classmethod
    def validar_claves_seguras(cls, v: str, info: ValidationInfo) -> str:
        if len(v) < 32:
            raise ValueError(
                f"{info.field_name} DEBE TENER AL MENOS 32 CARACTERES PARA SER SEGURO.")
        return v
    
    @field_validator("DATABASE_URL")
    @classmethod
    def validar_database_url(cls, v: str) -> str:
        if not v.startswith("postgresql") and not v.startswith("sqlite"):
            raise ValueError("DATABASE_URL DEBE SER UNA URL DE POSTGRESQL O SQLITE VÁLIDA.")
        return v
    
    @field_validator("WOMPI_BASE_URL")
    @classmethod
    def validar_wompi_base_url(cls, v: str, info: ValidationInfo) -> str:
        # SI USA SANDBOX O PRODUCCIÓN
        environment = info.data.get("ENVIRONMENT") if info.data else None
        if environment == "production" and "sandbox" in v:
            raise ValueError("WOMPI_BASE_URL NO PUEDE USAR EL ENDPOINT DE SANDBOX EN PRODUCCIÓN.")
        return v
    
    #PROPIEDADES CALCULADAS  
    @property
    def max_image_size_bytes(self) -> int:
        return self.MAX_IMAGE_SIZE * 1024 * 1024  # CONVERTIR MB A BYTES
    
    @property
    def es_desarrollo(self) -> bool:
        return self.ENVIRONMENT == "development" #TRUE SI EL AMBIENTE ES DE DESARROLLO
    
    @property
    def es_produccion(self) -> bool:
        return self.ENVIRONMENT == "production" #TRUE SI EL AMBIENTE ES DE PRODUCCIÓN
    
    @property
    def wowpi_url_transacciones(self) -> str:
        return f"{self.WOMPI_BASE_URL}/transactions" # URL PARA CREAR TRANSACCIONES EN WOMPI
    
    @property
    def wowpi_url_merchants(self) -> str:
        return f"{self.WOMPI_BASE_URL}/merchants/{self.WOMPI_PUBLIC_KEY}" # URL PARA OBTENER INFORMACIÓN DEL COMERCIANTE EN WOMPI

    # CONFIGURACIÓN DEL ARCHIVO .env
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True, 
        "extra": "forbid"  # PROHÍBE VARIABLES NO DEFINIDAS EN LA CLASE
    }

    # INSTANCIA GLOBAL DE CONFIGURACIÓN
@lru_cache()  # CACHEA LA INSTANCIA PARA MEJORAR EL RENDIMIENTO
def get_settings() -> "Settings":
    return Settings()
settings = get_settings()