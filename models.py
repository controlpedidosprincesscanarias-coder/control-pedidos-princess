"""
migrate_sqlite_to_pg.py
Migra los datos existentes de pedidos.db → Supabase PostgreSQL.

Uso:
    pip install psycopg2-binary
    python migrate_sqlite_to_pg.py --sqlite pedidos.db --pg "postgresql://..."
"""

import argparse, sqlite3, sys
import psycopg2
from psycopg2.extras import RealDictCursor

TABLES_ORDER = [
    "hoteles",
    "departamentos",
    "usuarios",
    "proveedores",
    "pedidos",
    "historial_estados",
    "emails_log",
]

def migrate(sqlite_path: str, pg_url: str):
    src = sqlite3.connect(sqlite_path)
    src.row_factory = sqlite3.Row
    dst = psycopg2.connect(pg_url, cursor_factory=RealDictCursor)

    for table in TABLES_ORDER:
        rows = src.execute(f"SELECT * FROM {table}").fetchall()
        if not rows:
            print(f"  {table}: vacía, omitida")
            continue

        cols   = rows[0].keys()
        placeholders = ", ".join(["%s"] * len(cols))
        col_names    = ", ".join(cols)
        sql = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"

        with dst.cursor() as cur:
            for row in rows:
                cur.execute(sql, list(row))

        # Restablece la secuencia SERIAL para que empiece por encima del MAX existente
        with dst.cursor() as cur:
            try:
                cur.execute(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), MAX(id)) FROM {table}")
            except Exception:
                pass

        dst.commit()
        print(f"  {table}: {len(rows)} filas migradas ✓")

    src.close()
    dst.close()
    print("\nMigración completada.")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sqlite", required=True, help="Ruta al pedidos.db")
    ap.add_argument("--pg",     required=True, help="PostgreSQL connection string")
    args = ap.parse_args()
    migrate(args.sqlite, args.pg)
