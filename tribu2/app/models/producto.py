from pydantic import BaseModel
from typing import Optional, List
from enum import Enum


class TallaPrenda(str, Enum):
    XS = "XS"
    S = "S"
    M = "M"
    L = "L"
    XL = "XL"
    XXL = "XXL"


class CategoriaProducto(str, Enum):
    camisetas = "camisetas"
    sudaderas = "sudaderas"
    pantalones = "pantalones"
    accesorios = "accesorios"
    calzado = "calzado"


class ProductoBase(BaseModel):
    nombre: str
    descripcion: str
    precio: float
    categoria: CategoriaProducto
    genero: str = "unisex"  # unisex, masculino, femenino
    imagenes: Optional[List[str]] = []
    activo: bool = True


class ProductoCrear(ProductoBase):
    pass


class ProductoActualizar(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    precio: Optional[float] = None
    categoria: Optional[CategoriaProducto] = None
    activo: Optional[bool] = None


class ProductoRespuesta(ProductoBase):
    id: str
    slug: str

    class Config:
        from_attributes = True


# ── Inventario ────────────────────────────────────
class InventarioItem(BaseModel):
    producto_id: str
    talla: TallaPrenda
    color: str
    cantidad: int


class InventarioActualizar(BaseModel):
    cantidad: int
