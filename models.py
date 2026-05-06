"""
Esquema de base de datos — Control Pedidos Princess Canarias
PostgreSQL (Supabase) — V2
"""

# Cada sentencia separada para ejecutarlas una a una con psycopg2
SQL_STATEMENTS = [
    # ── Hoteles ──────────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS hoteles (
        id      SERIAL PRIMARY KEY,
        codigo  TEXT NOT NULL UNIQUE,
        nombre  TEXT NOT NULL,
        activo  INTEGER NOT NULL DEFAULT 1
    )
    """,
    # ── Departamentos ─────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS departamentos (
        id     SERIAL PRIMARY KEY,
        nombre TEXT NOT NULL UNIQUE,
        activo INTEGER NOT NULL DEFAULT 1
    )
    """,
    # ── Proveedores ───────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS proveedores (
        id           SERIAL PRIMARY KEY,
        codigo       TEXT,
        nombre       TEXT NOT NULL,
        contacto     TEXT,
        email        TEXT,
        telefono     TEXT,
        movil        TEXT,
        observaciones TEXT,
        activo       INTEGER NOT NULL DEFAULT 1,
        creado_en    TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    # ── Usuarios ──────────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        id        SERIAL PRIMARY KEY,
        username  TEXT NOT NULL UNIQUE,
        nombre    TEXT NOT NULL,
        email     TEXT,
        password  TEXT NOT NULL,
        rol       TEXT NOT NULL DEFAULT 'user',
        activo    INTEGER NOT NULL DEFAULT 1,
        creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    # ── Pedidos ───────────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS pedidos (
        id                      SERIAL PRIMARY KEY,
        norden                  INTEGER NOT NULL,
        hotel_id                INTEGER NOT NULL REFERENCES hoteles(id),
        departamento_id         INTEGER REFERENCES departamentos(id),
        fecha_solicitud         TEXT,
        fecha_envio_visto_bueno TEXT,
        fecha_tramitacion       TEXT,
        pedido_num              TEXT,
        presupuesto_num         TEXT,
        entrada_albaran_num     TEXT,
        estado                  TEXT NOT NULL DEFAULT 'PENDIENTE FIRMA DIRECCION COMPRAS',
        comunicado_ab           INTEGER NOT NULL DEFAULT 0,
        comunicado_jefe_dep     INTEGER NOT NULL DEFAULT 0,
        parte_rotura            INTEGER NOT NULL DEFAULT 0,
        parte_ampliacion        INTEGER NOT NULL DEFAULT 0,
        proveedor_id            INTEGER REFERENCES proveedores(id),
        observaciones           TEXT,
        creado_por_id           INTEGER REFERENCES usuarios(id),
        modificado_por_id       INTEGER REFERENCES usuarios(id),
        creado_en               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        modificado_en           TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    # ── Adjuntos del pedido ───────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS pedido_adjuntos (
        id           SERIAL PRIMARY KEY,
        pedido_id    INTEGER NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
        tipo         TEXT NOT NULL,
        nombre       TEXT NOT NULL,
        mime_type    TEXT NOT NULL,
        datos        BYTEA NOT NULL,
        subido_por_id INTEGER REFERENCES usuarios(id),
        creado_en    TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_adjuntos_pedido ON pedido_adjuntos(pedido_id)",
    # ── Historial de estados ──────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS historial_estados (
        id           SERIAL PRIMARY KEY,
        pedido_id    INTEGER NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
        estado_antes TEXT,
        estado_nuevo TEXT NOT NULL,
        usuario_id   INTEGER REFERENCES usuarios(id),
        nota         TEXT,
        creado_en    TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    # ── Emails log ────────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS emails_log (
        id           SERIAL PRIMARY KEY,
        pedido_id    INTEGER REFERENCES pedidos(id),
        tipo         TEXT NOT NULL,
        destinatario TEXT NOT NULL,
        asunto       TEXT,
        enviado      INTEGER NOT NULL DEFAULT 0,
        error        TEXT,
        creado_en    TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    # ── Registro de pedidos eliminados ───────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS pedidos_eliminados (
        id                      SERIAL PRIMARY KEY,
        pedido_id               INTEGER NOT NULL,
        norden                  INTEGER NOT NULL,
        hotel_nombre            TEXT,
        departamento_nombre     TEXT,
        proveedor_nombre        TEXT,
        proveedor_email         TEXT,
        estado                  TEXT,
        fecha_solicitud         TEXT,
        pedido_num              TEXT,
        presupuesto_num         TEXT,
        entrada_albaran_num     TEXT,
        observaciones           TEXT,
        creado_por_nombre       TEXT,
        motivo_eliminacion      TEXT,
        eliminado_por_id        INTEGER REFERENCES usuarios(id),
        eliminado_por_nombre    TEXT,
        eliminado_en            TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_eliminados_pedido_id ON pedidos_eliminados(pedido_id)",
    "CREATE INDEX IF NOT EXISTS idx_eliminados_norden    ON pedidos_eliminados(norden)",
    # ── Índices ───────────────────────────────────────────────────────────────
    "CREATE INDEX IF NOT EXISTS idx_pedidos_hotel     ON pedidos(hotel_id)",
    "CREATE INDEX IF NOT EXISTS idx_pedidos_estado    ON pedidos(estado)",
    "CREATE INDEX IF NOT EXISTS idx_pedidos_proveedor ON pedidos(proveedor_id)",
    "CREATE INDEX IF NOT EXISTS idx_historial_pedido  ON historial_estados(pedido_id)",
    # ── Datos maestros ────────────────────────────────────────────────────────
    """
    INSERT INTO hoteles (codigo, nombre) VALUES
        ('GC', 'Gran Canaria Princess'),
        ('TA', 'Taurito Princess'),
        ('SU', 'TUI Blue Suite Princess'),
        ('MG', 'Mogan Princess'),
        ('MT', 'Maspalomas & Tabaiba Princess'),
        ('GY', 'Guayarmina Princess'),
        ('IT', 'Princess Inspire Tenerife'),
        ('JN', 'Club Jandia Princess'),
        ('FV', 'Fuerteventura Princess'),
        ('LP', 'La Palma Princess')
    ON CONFLICT DO NOTHING
    """,
    """
    INSERT INTO departamentos (nombre) VALUES
        ('PISOS'), ('RESTAURANTE'), ('RESTAURANTE & BARES'), ('BARES'),
        ('COCINA'), ('SSTT'), ('ECONOMATO'), ('RECEPCION'),
        ('ANIMACION'), ('ADMINISTRACION'), ('DIRECCION'), ('RRHH')
    ON CONFLICT DO NOTHING
    """,
    """
    INSERT INTO usuarios (username, nombre, email, password, rol) VALUES
        ('dcompras',    'Jesus Curbelo',   'jesus.curbelo@princess.es',   'Princess2026', 'admin'),
        ('comprascan',  'Victor Martin',   'victor.martin@princess.es',   'Princess2026', 'admin'),
        ('comprascan4', 'Fran Gonzalez',   'fran.gonzalez@princess.es',   'Princess2026', 'admin'),
        ('comprascan2', 'Said Driss',      'said.driss@princess.es',      'comprascan2',  'user'),
        ('comprascan3', 'David Rodriguez', 'david.rodriguez@princess.es', 'comprascan3',  'user'),
        ('comprascan6', 'Maria Cruz',      'maria.cruz@princess.es',      'comprascan6',  'user')
    ON CONFLICT DO NOTHING
    """,
]

ESTADOS_VALIDOS = [
    "PENDIENTE FIRMA DIRECCION COMPRAS",
    "PENDIENTE DE FIRMA DIRECCION HOTEL",
    "PENDIENTE COTIZACIÓN",
    "ENVIADO AL PROVEEDOR",
    "ENTREGA PARCIAL",
    "ENTREGADO",
    "CANCELADO",
]

ESTADOS_EMAIL_PROVEEDOR = {"ENVIADO AL PROVEEDOR"}

ESTADOS_EMAIL_INTERNO = {
    "ENVIADO AL PROVEEDOR",
    "ENTREGA PARCIAL",
    "ENTREGADO",
    "CANCELADO",
}
