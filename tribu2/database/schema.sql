-- ================================================================
--  TRIBU - Schema completo (Supabase / PostgreSQL)
--  Pegar y ejecutar en SQL Editor de Supabase
-- ================================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ── usuarios ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS usuarios (
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email          TEXT UNIQUE NOT NULL,
    nombre         TEXT NOT NULL,
    apellido       TEXT NOT NULL,
    telefono       TEXT,
    password_hash  TEXT NOT NULL,
    rol            TEXT NOT NULL DEFAULT 'cliente' CHECK (rol IN ('cliente','admin')),
    activo         BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── categorias ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS categorias (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre      TEXT UNIQUE NOT NULL,
    slug        TEXT UNIQUE NOT NULL,
    descripcion TEXT,
    imagen_url  TEXT,
    activa      BOOLEAN NOT NULL DEFAULT TRUE,
    orden       INT NOT NULL DEFAULT 0
);
INSERT INTO categorias (nombre, slug, orden) VALUES
    ('Camisetas','camisetas',1),('Sudaderas','sudaderas',2),
    ('Pantalones','pantalones',3),('Accesorios','accesorios',4),
    ('Calzado','calzado',5)
ON CONFLICT (slug) DO NOTHING;

-- ── productos ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS productos (
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre         TEXT NOT NULL,
    slug           TEXT UNIQUE NOT NULL,
    descripcion    TEXT NOT NULL,
    precio         NUMERIC(12,2) NOT NULL CHECK (precio > 0),
    precio_antes   NUMERIC(12,2),
    categoria      TEXT NOT NULL,
    genero         TEXT NOT NULL DEFAULT 'unisex'
                       CHECK (genero IN ('unisex','masculino','femenino')),
    imagenes       TEXT[] NOT NULL DEFAULT '{}',
    tags           TEXT[] NOT NULL DEFAULT '{}',
    activo         BOOLEAN NOT NULL DEFAULT TRUE,
    destacado      BOOLEAN NOT NULL DEFAULT FALSE,
    creado_en      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_productos_nombre_trgm
    ON productos USING GIN (nombre gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_productos_categoria
    ON productos (categoria) WHERE activo = TRUE;
CREATE INDEX IF NOT EXISTS idx_productos_destacado
    ON productos (destacado) WHERE activo = TRUE;

-- ── inventario ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS inventario (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    producto_id UUID NOT NULL REFERENCES productos(id) ON DELETE CASCADE,
    talla       TEXT NOT NULL
                    CHECK (talla IN ('XS','S','M','L','XL','XXL','UNICA')),
    color       TEXT NOT NULL,
    color_hex   TEXT,
    cantidad    INT NOT NULL DEFAULT 0 CHECK (cantidad >= 0),
    UNIQUE (producto_id, talla, color)
);
CREATE INDEX IF NOT EXISTS idx_inventario_producto ON inventario (producto_id);

-- ── carrito_items ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS carrito_items (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id  UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    producto_id UUID NOT NULL REFERENCES productos(id) ON DELETE CASCADE,
    talla       TEXT NOT NULL,
    color       TEXT NOT NULL,
    cantidad    INT NOT NULL DEFAULT 1 CHECK (cantidad > 0),
    agregado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (usuario_id, producto_id, talla, color)
);
CREATE INDEX IF NOT EXISTS idx_carrito_usuario ON carrito_items (usuario_id);

-- ── pedidos ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS pedidos (
    id                   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id           UUID NOT NULL REFERENCES usuarios(id),
    items                JSONB NOT NULL,
    direccion_envio      JSONB NOT NULL,
    subtotal             NUMERIC(12,2) NOT NULL,
    costo_envio          NUMERIC(12,2) NOT NULL DEFAULT 0,
    total                NUMERIC(12,2) NOT NULL,
    estado               TEXT NOT NULL DEFAULT 'pendiente'
                             CHECK (estado IN (
                                 'pendiente','pago_verificado',
                                 'en_preparacion','enviado',
                                 'entregado','cancelado')),
    wompi_referencia     TEXT UNIQUE,
    wompi_transaction_id TEXT,
    notas                TEXT,
    numero_seguimiento   TEXT,
    creado_en            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actualizado_en       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_pedidos_usuario ON pedidos (usuario_id);
CREATE INDEX IF NOT EXISTS idx_pedidos_estado  ON pedidos (estado);
CREATE INDEX IF NOT EXISTS idx_pedidos_fecha   ON pedidos (creado_en DESC);

-- ── historial_estados_pedido ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS historial_estados_pedido (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pedido_id    UUID NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
    estado       TEXT NOT NULL,
    nota         TEXT,
    cambiado_por UUID REFERENCES usuarios(id),
    creado_en    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Trigger: actualizar_timestamp ───────────────────────────────
CREATE OR REPLACE FUNCTION actualizar_timestamp()
RETURNS TRIGGER AS $$
BEGIN NEW.actualizado_en = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_usuarios_updated
    BEFORE UPDATE ON usuarios FOR EACH ROW EXECUTE FUNCTION actualizar_timestamp();
CREATE TRIGGER trg_productos_updated
    BEFORE UPDATE ON productos FOR EACH ROW EXECUTE FUNCTION actualizar_timestamp();
CREATE TRIGGER trg_pedidos_updated
    BEFORE UPDATE ON pedidos FOR EACH ROW EXECUTE FUNCTION actualizar_timestamp();

-- ── Trigger: historial de estados ───────────────────────────────
CREATE OR REPLACE FUNCTION registrar_cambio_estado_pedido()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.estado IS DISTINCT FROM NEW.estado THEN
        INSERT INTO historial_estados_pedido (pedido_id, estado)
        VALUES (NEW.id, NEW.estado);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_pedido_estado
    AFTER UPDATE ON pedidos FOR EACH ROW
    EXECUTE FUNCTION registrar_cambio_estado_pedido();

-- ── Row Level Security ───────────────────────────────────────────
ALTER TABLE usuarios      ENABLE ROW LEVEL SECURITY;
ALTER TABLE productos     ENABLE ROW LEVEL SECURITY;
ALTER TABLE inventario    ENABLE ROW LEVEL SECURITY;
ALTER TABLE carrito_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE pedidos       ENABLE ROW LEVEL SECURITY;
ALTER TABLE categorias    ENABLE ROW LEVEL SECURITY;

-- Usuarios: solo su propio perfil
CREATE POLICY "usuarios_select_own" ON usuarios
    FOR SELECT USING (auth.uid()::text = id::text);
CREATE POLICY "usuarios_update_own" ON usuarios
    FOR UPDATE USING (auth.uid()::text = id::text);

-- Productos e inventario: lectura pública
CREATE POLICY "productos_select_publico" ON productos
    FOR SELECT USING (activo = TRUE);
CREATE POLICY "inventario_select_publico" ON inventario
    FOR SELECT USING (TRUE);

-- Carrito: solo el dueño
CREATE POLICY "carrito_select_own" ON carrito_items
    FOR SELECT USING (auth.uid()::text = usuario_id::text);
CREATE POLICY "carrito_insert_own" ON carrito_items
    FOR INSERT WITH CHECK (auth.uid()::text = usuario_id::text);
CREATE POLICY "carrito_update_own" ON carrito_items
    FOR UPDATE USING (auth.uid()::text = usuario_id::text);
CREATE POLICY "carrito_delete_own" ON carrito_items
    FOR DELETE USING (auth.uid()::text = usuario_id::text);

-- Pedidos: solo el dueño
CREATE POLICY "pedidos_select_own" ON pedidos
    FOR SELECT USING (auth.uid()::text = usuario_id::text);
CREATE POLICY "pedidos_insert_own" ON pedidos
    FOR INSERT WITH CHECK (auth.uid()::text = usuario_id::text);

-- Categorías: lectura pública
CREATE POLICY "categorias_select_publico" ON categorias
    FOR SELECT USING (activa = TRUE);
