from pydantic import BaseModel
from typing import List, Optional
from enum import Enum
from datetime import datetime


class EstadoPedido(str, Enum):
    pendiente = "pendiente"
    pago_verificado = "pago_verificado"
    en_preparacion = "en_preparacion"
    enviado = "enviado"
    entregado = "entregado"
    cancelado = "cancelado"


class ItemPedido(BaseModel):
    producto_id: str
    nombre_producto: str
    talla: str
    color: str
    cantidad: int
    precio_unitario: float

    @property
    def subtotal(self) -> float:
        return self.cantidad * self.precio_unitario


class DireccionEnvio(BaseModel):
    nombre_completo: str
    direccion: str
    ciudad: str
    departamento: str
    codigo_postal: Optional[str] = None
    telefono: str


class PedidoCrear(BaseModel):
    items: List[ItemPedido]
    direccion_envio: DireccionEnvio
    notas: Optional[str] = None


class PedidoRespuesta(BaseModel):
    id: str
    usuario_id: str
    items: List[ItemPedido]
    direccion_envio: DireccionEnvio
    estado: EstadoPedido
    total: float
    wompi_referencia: Optional[str] = None
    wompi_transaction_id: Optional[str] = None
    creado_en: datetime
    actualizado_en: datetime

    class Config:
        from_attributes = True
