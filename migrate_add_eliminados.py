"""
init_db.py — Inicializa la base de datos PostgreSQL (Supabase) en el primer despliegue.

Uso:
    python init_db.py

Requiere la variable de entorno DATABASE_URL configurada, igual que en Render.
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from models import SQL_STATEMENTS

DATABASE_URL = os.environ.get("DATABASE_URL", "")

if not DATABASE_URL:
    print("❌ ERROR: La variable de entorno DATABASE_URL no está definida.")
    print("   Exporta la URL de conexión de Supabase antes de ejecutar este script.")
    print("   Ejemplo: export DATABASE_URL='postgresql://...'")
    sys.exit(1)

print("🔌 Conectando a la base de datos...")
try:
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    conn.autocommit = False
except Exception as e:
    print(f"❌ No se pudo conectar: {e}")
    sys.exit(1)

print(f"⚙️  Ejecutando {len(SQL_STATEMENTS)} sentencias SQL...")
try:
    with conn.cursor() as cur:
        for i, stmt in enumerate(SQL_STATEMENTS, 1):
            preview = stmt.strip().splitlines()[0][:60]
            print(f"   [{i:02d}] {preview}...")
            cur.execute(stmt)
    conn.commit()
    print("✅ Base de datos inicializada correctamente.")
except Exception as e:
    conn.rollback()
    print(f"❌ Error durante la inicialización: {e}")
    sys.exit(1)
finally:
    conn.close()
