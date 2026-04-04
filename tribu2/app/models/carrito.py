from pydantic import BaseModel
from typing import List, Optional


class ItemCarrito(BaseModel):
    producto_id: str
    talla: str
    color: str
    cantidad: int


class CarritoAgregar(BaseModel):
    producto_id: str
    talla: str
    color: str
    cantidad: int = 1


class CarritoActualizar(BaseModel):
    cantidad: int


class CarritoRespuesta(BaseModel):
    items: List[dict]
    total: float
    cantidad_items: int
