"""
Migración v11.4.0 — Plazo de entrega por pedido
================================================
1. Añade columna  pedidos.plazo_entrega_dias  (INTEGER, nullable)
2. Inserta clave  activar_uso_plazo_entrega   en config_alertas  (booleano, default '1')

Seguro de ejecutar varias veces (IF NOT EXISTS / ON CONFLICT DO NOTHING).
"""

import os
import sys
import psycopg2
import psycopg2.extras

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: variable DATABASE_URL no definida.", file=sys.stderr)
    sys.exit(1)

SQL = [
    # ── 1. Nueva columna en pedidos ───────────────────────────────────────────
    """
    ALTER TABLE pedidos
        ADD COLUMN IF NOT EXISTS plazo_entrega_dias INTEGER;
    """,
    # ── 2. Nueva clave de configuración ──────────────────────────────────────
    """
    INSERT INTO config_alertas (clave, valor, tipo, label, grupo, orden)
    VALUES (
        'activar_uso_plazo_entrega',
        '1',
        'bool',
        'Activar alertas basadas en plazo de entrega del proveedor',
        'global',
        2
    )
    ON CONFLICT (clave) DO NOTHING;
    """,
]

def run():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    conn.autocommit = False
    cur = conn.cursor()
    try:
        for stmt in SQL:
            cur.execute(stmt)
            print(f"OK: {stmt.strip()[:80]}")
        conn.commit()
        print("\n✅ Migración v11.4.0 completada.")
    except Exception as exc:
        conn.rollback()
        print(f"\n❌ Error — rollback: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    run()
