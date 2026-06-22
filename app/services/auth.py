import bcrypt
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from fastapi import Request, Depends, HTTPException, status
from sqlmodel import Session
from app.config import settings
from app.database.database import get_session
from app.models.models import Usuario

def hash_password(password: str) -> str:
    """Hashea una contraseña en texto plano usando bcrypt directamente."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una contraseña en texto plano contra su hash usando bcrypt."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Genera un token de acceso JWT."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """Decodifica y valida un token de acceso JWT."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None

async def get_current_user_optional(request: Request, db: Session = Depends(get_session)) -> Optional[Usuario]:
    """
    Obtiene el usuario autenticado desde el header de autorización o cookies.
    No arroja excepciones, útil para páginas públicas que cambian su UI si estás logueado.
    """
    token = None
    
    # 1. Buscar en el header Authorization
    authorization = request.headers.get("Authorization")
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
    
    # 2. Buscar en las cookies
    if not token:
        cookie_token = request.cookies.get("access_token")
        if cookie_token:
            if cookie_token.startswith("Bearer "):
                token = cookie_token.split(" ")[1]
            else:
                token = cookie_token

    if not token:
        return None

    payload = decode_access_token(token)
    if not payload:
        return None
        
    email: str = payload.get("sub")
    if not email:
        return None
        
    user = db.query(Usuario).filter(Usuario.email == email).first()
    return user

async def get_current_user(user: Optional[Usuario] = Depends(get_current_user_optional)) -> Usuario:
    """
    Dependencia que requiere que el usuario esté autenticado.
    Lanza excepción 401 si no hay usuario logueado.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Acceso no autorizado. Por favor, inicia sesión.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def get_current_admin(user: Usuario = Depends(get_current_user)) -> Usuario:
    """
    Dependencia que verifica que el usuario autenticado sea Administrador.
    Lanza excepción 403 si no tiene permisos.
    """
    if user.rol != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Se requieren permisos de administrador.",
        )
    return user
