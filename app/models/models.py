import uuid
from datetime import datetime
from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship, Column, JSON

class Usuario(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    nombre: str
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    ciudad: Optional[str] = None
    departamento: Optional[str] = None
    rol: str = Field(default="cliente")  # "admin" o "cliente"
    fecha_creacion: datetime = Field(default_factory=datetime.utcnow)

    # Relaciones
    pedidos: List["Pedido"] = Relationship(back_populates="usuario")

class Producto(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    nombre: str
    descripcion: str
    precio: float
    stock: int = Field(default=0)
    categoria: str  # chaquetas, buzos, gorras, hoodies, chalecos, camisetas
    imagen_url: Optional[str] = None
    # Almacena un listado de tallas como JSON (ej. ["S", "M", "L", "XL"])
    tallas: List[str] = Field(default=[], sa_column=Column(JSON))
    activo: bool = Field(default=True)
    fecha_creacion: datetime = Field(default_factory=datetime.utcnow)

    # Relaciones
    detalles: List["DetallePedido"] = Relationship(back_populates="producto")

class Pedido(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    usuario_id: uuid.UUID = Field(foreign_key="usuario.id")
    total: float
    estado: str = Field(default="pendiente")  # pendiente, pagado, enviado, entregado, cancelado
    direccion_envio: str
    ciudad: str
    departamento: str
    metodo_envio: str = Field(default="domicilio")
    costo_envio: float = Field(default=0.0)
    tracking_id: Optional[str] = None
    referencia_wompi: Optional[str] = None  # Referencia única para pasarela de pagos
    fecha_creacion: datetime = Field(default_factory=datetime.utcnow)

    # Relaciones
    usuario: Usuario = Relationship(back_populates="pedidos")
    detalles: List["DetallePedido"] = Relationship(back_populates="pedido", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    transacciones: List["Transaccion"] = Relationship(back_populates="pedido")

class DetallePedido(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    pedido_id: uuid.UUID = Field(foreign_key="pedido.id")
    producto_id: uuid.UUID = Field(foreign_key="producto.id")
    cantidad: int
    precio_unitario: float
    talla: str

    # Relaciones
    pedido: Pedido = Relationship(back_populates="detalles")
    producto: Producto = Relationship(back_populates="detalles")

class Transaccion(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    pedido_id: uuid.UUID = Field(foreign_key="pedido.id")
    wompi_id: Optional[str] = None  # ID de transacción de Wompi
    estado: str = Field(default="pendiente")  # pendiente, aprobada, rechazada, fallida
    metodo_pago: Optional[str] = None  # tarjeta, pse, nequi, bancolombia
    monto: float
    fecha_creacion: datetime = Field(default_factory=datetime.utcnow)

    # Relaciones
    pedido: Pedido = Relationship(back_populates="transacciones")
