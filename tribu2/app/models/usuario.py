from pydantic import BaseModel, EmailStr
from typing import Optional
from enum import Enum


class RolUsuario(str, Enum):
    cliente = "cliente"
    admin = "admin"


class UsuarioBase(BaseModel):
    email: EmailStr
    nombre: str
    apellido: str
    telefono: Optional[str] = None


class UsuarioCrear(UsuarioBase):
    password: str


class UsuarioLogin(BaseModel):
    email: EmailStr
    password: str


class UsuarioRespuesta(UsuarioBase):
    id: str
    rol: RolUsuario
    activo: bool

    class Config:
        from_attributes = True


class TokenRespuesta(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioRespuesta
