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
        id            SERIAL PRIMARY KEY,
        codigo        TEXT,
        nombre        TEXT NOT NULL,
        observaciones TEXT,
        activo        INTEGER NOT NULL DEFAULT 1,
        creado_en     TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    # ── Contactos de proveedor (múltiples por proveedor) ──────────────────────
    """
    CREATE TABLE IF NOT EXISTS proveedor_contactos (
        id           SERIAL PRIMARY KEY,
        proveedor_id INTEGER NOT NULL REFERENCES proveedores(id) ON DELETE CASCADE,
        nombre       TEXT,
        telefono     TEXT,
        movil        TEXT,
        email        TEXT,
        es_principal INTEGER NOT NULL DEFAULT 0,
        orden        INTEGER NOT NULL DEFAULT 0
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_prov_contactos ON proveedor_contactos(proveedor_id)",
    # ── Hoteles asignados a un contacto de proveedor (opcional) ────────────────
    """
    CREATE TABLE IF NOT EXISTS proveedor_contacto_hoteles (
        contacto_id INTEGER NOT NULL REFERENCES proveedor_contactos(id) ON DELETE CASCADE,
        hotel_id    INTEGER NOT NULL REFERENCES hoteles(id) ON DELETE CASCADE,
        PRIMARY KEY (contacto_id, hotel_id)
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_prov_contacto_hoteles_hotel ON proveedor_contacto_hoteles(hotel_id)",
    # ── Usuarios ──────────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        id        SERIAL PRIMARY KEY,
        username  TEXT NOT NULL UNIQUE,
        nombre    TEXT NOT NULL,
        email     TEXT,
        email2    TEXT,
        movil     TEXT,
        password  TEXT NOT NULL,
        rol       TEXT NOT NULL DEFAULT 'user',
        activo    INTEGER NOT NULL DEFAULT 1,
        creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    # ── Familias de artículos ─────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS familias (
        id     SERIAL PRIMARY KEY,
        nombre TEXT NOT NULL UNIQUE,
        activo INTEGER NOT NULL DEFAULT 1
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
        tarifa_acordada         BOOLEAN NOT NULL DEFAULT FALSE,
        estado                  TEXT NOT NULL DEFAULT 'PENDIENTE FIRMA DIRECCION COMPRAS',
        comunicado_ab           INTEGER NOT NULL DEFAULT 0,
        comunicado_jefe_dep     INTEGER NOT NULL DEFAULT 0,
        parte_rotura            INTEGER NOT NULL DEFAULT 0,
        parte_ampliacion        INTEGER NOT NULL DEFAULT 0,
        proveedor_id            INTEGER REFERENCES proveedores(id),
        observaciones           TEXT,
        familia_id              INTEGER REFERENCES familias(id),
        importe                 NUMERIC(10,2),
        sujeto_techo            INTEGER NOT NULL DEFAULT 0,
        mes_consumo_techo       TEXT,
        no_autorizado_previo    BOOLEAN NOT NULL DEFAULT FALSE,
        creado_por_id           INTEGER REFERENCES usuarios(id),
        modificado_por_id       INTEGER REFERENCES usuarios(id),
        creado_por_nombre       TEXT,
        modificado_por_nombre   TEXT,
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
        datos_thumb      BYTEA,
        thumb_mime_type  TEXT,
        es_correo    BOOLEAN NOT NULL DEFAULT FALSE,
        subido_por_id INTEGER REFERENCES usuarios(id),
        creado_en    TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_adjuntos_pedido ON pedido_adjuntos(pedido_id)",
    "CREATE INDEX IF NOT EXISTS idx_adjuntos_tipo_correo ON pedido_adjuntos(pedido_id, tipo, es_correo)",
    # ── Historial de estados ──────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS historial_estados (
        id           SERIAL PRIMARY KEY,
        pedido_id    INTEGER NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
        estado_antes TEXT,
        estado_nuevo TEXT NOT NULL,
        usuario_id   INTEGER REFERENCES usuarios(id),
        usuario_nombre TEXT,
        nota         TEXT,
        creado_en    TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    # ── Expediente de Exceso de Techo (rediseño Techo de Gastos, Fase 1) ───────
    # Registro independiente y permanente de cada autorización extraordinaria
    # de Dirección General — nunca se combina con el cálculo del Techo en sí
    # (ver mes_consumo_techo en pedidos) ni se borra. Un pedido puede tener
    # varias filas aquí si es reabrible (denegado → reintenta) — cada intento
    # es una fila independiente, nunca se sobrescribe; eso da gratis el
    # histórico cronológico por expediente (listar por pedido_id, creado_en).
    """
    CREATE TABLE IF NOT EXISTS expediente_exceso (
        id                              SERIAL PRIMARY KEY,
        pedido_id                       INTEGER NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
        hotel_id                        INTEGER NOT NULL REFERENCES hoteles(id),
        familia_id                      INTEGER REFERENCES familias(id),
        mes                             TEXT NOT NULL,
        importe_pedido                  NUMERIC(10,2),
        consumo_previo                  NUMERIC(10,2),
        exceso                          NUMERIC(10,2),
        motivo_solicitud                TEXT,
        usuario_solicitante_id          INTEGER REFERENCES usuarios(id),
        resultado                       TEXT NOT NULL DEFAULT 'pendiente',
        usuario_resuelve_id             INTEGER REFERENCES usuarios(id),
        fecha_resolucion                TIMESTAMPTZ,
        observaciones_direccion_general TEXT,
        consumido_en_solicitud          NUMERIC(10,2),
        disponible_en_solicitud         NUMERIC(10,2),
        creado_en                       TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_expediente_pedido ON expediente_exceso(pedido_id)",
    "CREATE INDEX IF NOT EXISTS idx_expediente_hotel_familia_mes ON expediente_exceso(hotel_id, familia_id, mes)",
    "CREATE INDEX IF NOT EXISTS idx_expediente_resultado ON expediente_exceso(resultado)",
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
    # ── WhatsApp log (v9.5) ───────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS whatsapp_log (
        id           SERIAL PRIMARY KEY,
        pedido_id    INTEGER REFERENCES pedidos(id),
        tipo         TEXT NOT NULL,
        destinatario TEXT NOT NULL,
        mensaje      TEXT,
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
    # ── Índices base ──────────────────────────────────────────────────────────
    "CREATE INDEX IF NOT EXISTS idx_pedidos_hotel     ON pedidos(hotel_id)",
    "CREATE INDEX IF NOT EXISTS idx_pedidos_estado    ON pedidos(estado)",
    "CREATE INDEX IF NOT EXISTS idx_pedidos_proveedor ON pedidos(proveedor_id)",
    "CREATE INDEX IF NOT EXISTS idx_historial_pedido  ON historial_estados(pedido_id)",
    # ── /api/techo/resumen: hotel_id + mes con filtro parcial sujeto_techo=1 ─
    "CREATE INDEX IF NOT EXISTS idx_pedidos_techo_mes  ON pedidos(hotel_id, creado_en) WHERE sujeto_techo = 1",
    # ── /api/techo/resumen-historico: filtro parcial sujeto_techo+estado ─────
    "CREATE INDEX IF NOT EXISTS idx_pedidos_techo_hist ON pedidos(hotel_id) WHERE sujeto_techo = 1 AND estado = 'ENVIADO AL PROVEEDOR'",
    # ── historial_estados: subconsulta COALESCE por pedido_id + estado_nuevo ─
    "CREATE INDEX IF NOT EXISTS idx_historial_estado_nuevo ON historial_estados(pedido_id, estado_nuevo, creado_en DESC)",
    # ── /api/stats: estados activos con fecha_tramitacion (alertas) ───────────
    "CREATE INDEX IF NOT EXISTS idx_pedidos_alertas ON pedidos(estado, fecha_tramitacion) WHERE estado IN ('ENVIADO AL PROVEEDOR','PENDIENTE FIRMA DIRECCION COMPRAS','PENDIENTE DE FIRMA DIRECCION HOTEL','ENTREGA PARCIAL','PENDIENTE COTIZACION')",
    # ── /api/pedidos lista paginada: ORDER BY norden DESC (orden por defecto) ─
    "CREATE INDEX IF NOT EXISTS idx_pedidos_norden ON pedidos(norden DESC)",
    # ── /api/pedidos filtro por rango de fecha_solicitud (TEXT) ──────────────
    "CREATE INDEX IF NOT EXISTS idx_pedidos_fecha_solicitud ON pedidos(fecha_solicitud)",
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
        ('LP', 'La Palma Princess'),
        ('PR', '⚠️ HOTEL PRUEBAS — no usar en operativa real')
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
    CREATE TABLE IF NOT EXISTS egress_tracking (
        fecha  DATE PRIMARY KEY,
        bytes  BIGINT NOT NULL DEFAULT 0
    )
    """,
]
# Los usuarios se crean y gestionan exclusivamente desde el panel de administración.
# No hay usuarios predefinidos en el código. Para el primer arranque usa seed_admin.py.

ESTADOS_VALIDOS = [
    "PENDIENTE FIRMA DIRECCION COMPRAS",
    "PENDIENTE DE FIRMA DIRECCION HOTEL",
    "PENDIENTE COTIZACIÓN",
    "PENDIENTE Vº Bº DIRECCIÓN GENERAL",
    "DENEGADO POR DIRECCION GENERAL",
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
    "DENEGADO POR DIRECCION GENERAL",
}
