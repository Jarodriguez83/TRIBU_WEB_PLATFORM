from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from app.config import get_settings
from app.database import supabase

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)


def verificar_password(password_plano: str, password_hash: str) -> bool:
    return pwd_context.verify(password_plano, password_hash)


def hashear_password(password: str) -> str:
    return pwd_context.hash(password)


def crear_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decodificar_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        return None


async def obtener_usuario_actual(request: Request) -> Optional[dict]:
    """Obtiene usuario del token en cookie o header. Retorna None si no hay sesión."""
    token = request.cookies.get("access_token")
    if not token:
        return None
    payload = decodificar_token(token)
    if not payload:
        return None
    usuario_id = payload.get("sub")
    if not usuario_id:
        return None
    resp = supabase.table("usuarios").select("*").eq("id", usuario_id).single().execute()
    return resp.data if resp.data else None


async def requerir_usuario(request: Request) -> dict:
    """Igual que obtener_usuario_actual pero lanza 401 si no hay sesión."""
    usuario = await obtener_usuario_actual(request)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sesión requerida")
    return usuario


async def requerir_admin(request: Request) -> dict:
    """Igual que requerir_usuario pero exige rol admin."""
    usuario = await requerir_usuario(request)
    if usuario.get("rol") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso restringido")
    return usuario
