# TRIBU — Plataforma Web

> "No seguimos tendencias, las transformamos."

Tienda virtual de ropa urbana unisex construida con FastAPI + Supabase + Jinja2.

## Stack

| Capa | Tecnología |
|------|-----------|
| Backend | FastAPI + Uvicorn |
| Templates | Jinja2 |
| Base de datos | Supabase (PostgreSQL) |
| Autenticación | JWT (jose) + bcrypt |
| Pagos | Wompi (Colombia) |
| Deploy | Render |

## Inicio rápido

```bash
# 1. Clonar e instalar dependencias
pip install -r requirements.txt

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus claves de Supabase y Wompi

# 3. Crear tablas en Supabase
# Ir a Supabase > SQL Editor > pegar database/schema.sql > Run

# 4. Correr el servidor
uvicorn app.main:app --reload --port 8000
```

## Estructura

```
tribu/
├── app/
│   ├── main.py              # Punto de entrada
│   ├── config.py            # Variables de entorno
│   ├── database.py          # Clientes Supabase
│   ├── routers/             # Rutas HTTP
│   │   ├── auth.py          # Login / registro
│   │   ├── productos.py     # Catálogo público
│   │   ├── carrito.py       # Carrito de compras
│   │   ├── pedidos.py       # Pedidos + Wompi
│   │   └── admin/           # Panel administrativo
│   ├── models/              # Esquemas Pydantic
│   ├── services/            # Lógica de negocio
│   │   ├── auth_service.py  # JWT, roles, sesiones
│   │   └── wompi.py         # Integración pagos
│   └── templates/           # Jinja2 HTML
│       ├── tienda/          # Vistas del cliente
│       └── admin/           # Vistas del admin
├── database/
│   └── schema.sql           # Tablas + RLS + Triggers
└── .env.example
```

## Roles

- `cliente`: Navega, compra, ve sus pedidos
- `admin`: Accede a `/admin`, gestiona productos, pedidos, usuarios y reportes

## Wompi

- Sandbox: usar `pub_test_*` y `prv_test_*`
- El webhook de Wompi debe apuntar a: `https://tu-dominio.com/pedidos/webhook/wompi`
- En producción cambiar `WOMPI_ENV=production` en `.env`
