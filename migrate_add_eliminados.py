"""
migrate_add_eliminados.py — Migración para bases de datos ya existentes.
Añade la tabla pedidos_eliminados si no existe.

Uso (una sola vez sobre la BD en producción):
    python migrate_add_eliminados.py
"""

import os, sys
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get("DATABASE_URL", "")
if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL no está definida.")
    sys.exit(1)

SQL = """
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
);
CREATE INDEX IF NOT EXISTS idx_eliminados_pedido_id ON pedidos_eliminados(pedido_id);
CREATE INDEX IF NOT EXISTS idx_eliminados_norden    ON pedidos_eliminados(norden);
"""

print("🔌 Conectando a la base de datos...")
try:
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    conn.autocommit = False
except Exception as e:
    print(f"❌ No se pudo conectar: {e}")
    sys.exit(1)

try:
    with conn.cursor() as cur:
        cur.execute(SQL)
    conn.commit()
    print("✅ Tabla pedidos_eliminados creada correctamente (o ya existía).")
except Exception as e:
    conn.rollback()
    print(f"❌ Error: {e}")
    sys.exit(1)
finally:
    conn.close()
