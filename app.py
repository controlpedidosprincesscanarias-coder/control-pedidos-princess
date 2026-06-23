"""
Control Pedidos Princess Canarias — Flask + PostgreSQL (Supabase)
Despliegue: Render.com  |  BD: Supabase  |  Email: EmailJS (frontend)
"""

import os, json, logging, secrets, atexit, hashlib
from datetime import datetime, timedelta, timezone, date as _date
from functools import wraps

from apscheduler.schedulers.background import BackgroundScheduler

import psycopg2
from psycopg2.extras import RealDictCursor

from flask import Flask, request, jsonify, send_from_directory, session, g
from models import SQL_STATEMENTS, ESTADOS_VALIDOS, ESTADOS_EMAIL_PROVEEDOR, ESTADOS_EMAIL_INTERNO

# ── Configuración ──────────────────────────────────────────────────────────────

DATABASE_URL = os.environ.get("DATABASE_URL", "")          # Supabase → Settings → Database → URI
SECRET_KEY = os.environ["SECRET_KEY"]

# Email — gestionado enteramente por EmailJS en el frontend
# EMAILS_INTERNOS eliminado: los destinatarios internos se leen siempre de la BD (rol admin/compras)

app = Flask(__name__)
app.secret_key = SECRET_KEY
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

def _auto_migrate():
    """Añade columnas/tablas nuevas de forma idempotente."""
    try:
        db = psycopg2.connect(
            DATABASE_URL, cursor_factory=RealDictCursor,
            connect_timeout=20,
        )
        db.autocommit = True
        with db.cursor() as cur:
            # Columnas legacy de proveedores (para DBs antiguas)
            for col_name, col_type in [("codigo","TEXT"),("movil","TEXT"),("observaciones","TEXT"),
                                        ("contacto","TEXT"),("email","TEXT"),("telefono","TEXT")]:
                cur.execute(f"ALTER TABLE proveedores ADD COLUMN IF NOT EXISTS {col_name} {col_type}")
            # Tabla de contactos múltiples (v9.2)
            cur.execute("""
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
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_prov_contactos ON proveedor_contactos(proveedor_id)")
            # Nuevas columnas v9.4 (para DBs existentes sin ellas)
            cur.execute("ALTER TABLE proveedor_contactos ADD COLUMN IF NOT EXISTS movil TEXT")
            # es_principal: añadir sin NOT NULL primero (seguro para tablas con filas existentes)
            cur.execute("ALTER TABLE proveedor_contactos ADD COLUMN IF NOT EXISTS es_principal INTEGER DEFAULT 0")
            cur.execute("UPDATE proveedor_contactos SET es_principal=0 WHERE es_principal IS NULL")
            # Marcar como principal el contacto de orden=0 si ninguno tiene es_principal=1
            cur.execute("""
                UPDATE proveedor_contactos SET es_principal=1
                WHERE id IN (
                    SELECT DISTINCT ON (proveedor_id) id FROM proveedor_contactos
                    WHERE proveedor_id NOT IN (SELECT proveedor_id FROM proveedor_contactos WHERE es_principal=1)
                    ORDER BY proveedor_id, orden, id
                )
            """)
            # Migrar datos legacy: si hay contacto/email/telefono/movil y no hay contactos aún
            cur.execute("""
                INSERT INTO proveedor_contactos (proveedor_id, nombre, telefono, movil, email, es_principal, orden)
                SELECT id,
                       NULLIF(TRIM(COALESCE(contacto,'')), ''),
                       NULLIF(TRIM(COALESCE(telefono,'')), ''),
                       NULLIF(TRIM(COALESCE(movil,'')), ''),
                       NULLIF(TRIM(COALESCE(email,'')), ''),
                       1,
                       0
                FROM proveedores
                WHERE NOT EXISTS (SELECT 1 FROM proveedor_contactos pc WHERE pc.proveedor_id = proveedores.id)
                  AND (TRIM(COALESCE(contacto,''))!='' OR TRIM(COALESCE(email,''))!=''
                       OR TRIM(COALESCE(telefono,''))!='' OR TRIM(COALESCE(movil,''))!='')
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS pedido_adjuntos (
                    id            SERIAL PRIMARY KEY,
                    pedido_id     INTEGER NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
                    tipo          TEXT NOT NULL,
                    nombre        TEXT NOT NULL,
                    mime_type     TEXT NOT NULL,
                    datos         BYTEA NOT NULL,
                    subido_por_id INTEGER REFERENCES usuarios(id),
                    creado_en     TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_adjuntos_pedido ON pedido_adjuntos(pedido_id)")
            # ── Tokens de restablecimiento de contraseña ──────────────────────
            cur.execute("""
                CREATE TABLE IF NOT EXISTS password_reset_tokens (
                    id         SERIAL PRIMARY KEY,
                    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
                    token      TEXT NOT NULL UNIQUE,
                    expira_en  TIMESTAMPTZ NOT NULL,
                    usado      INTEGER NOT NULL DEFAULT 0
                )
            """)
            # ── Columna móvil en usuarios (v9.5) ─────────────────────────────
            cur.execute("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS movil TEXT")
            # ── Columnas nombre cache en pedidos e historial (v9.9.7) ─────────
            cur.execute("ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS creado_por_nombre TEXT")
            cur.execute("ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS modificado_por_nombre TEXT")
            cur.execute("ALTER TABLE historial_estados ADD COLUMN IF NOT EXISTS usuario_nombre TEXT")
            # Rellenar cache para registros existentes (ejecución única, segura)
            cur.execute("""
                UPDATE pedidos p SET creado_por_nombre = u.nombre
                FROM usuarios u WHERE u.id = p.creado_por_id AND p.creado_por_nombre IS NULL
            """)
            cur.execute("""
                UPDATE pedidos p SET modificado_por_nombre = u.nombre
                FROM usuarios u WHERE u.id = p.modificado_por_id AND p.modificado_por_nombre IS NULL
            """)
            cur.execute("""
                UPDATE historial_estados h SET usuario_nombre = u.nombre
                FROM usuarios u WHERE u.id = h.usuario_id AND h.usuario_nombre IS NULL
            """)
            # ── Tabla asignación hoteles a usuario hotel (v9.9.5) ─────────────
            cur.execute("""
                CREATE TABLE IF NOT EXISTS usuario_hoteles (
                    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
                    hotel_id   INTEGER NOT NULL REFERENCES hoteles(id)  ON DELETE CASCADE,
                    PRIMARY KEY (usuario_id, hotel_id)
                )
            """)
            # Permite gestionar desde admin qué hoteles atiende cada comprador,
            # reemplazando el diccionario HOTEL_COMPRADOR hardcodeado.
            cur.execute("""
                CREATE TABLE IF NOT EXISTS usuario_comprador_hoteles (
                    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
                    hotel_id   INTEGER NOT NULL REFERENCES hoteles(id)  ON DELETE CASCADE,
                    PRIMARY KEY (usuario_id, hotel_id)
                )
            """)
            cur.execute("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS telegram_chat_id TEXT")
            # Añade índice único sobre hotel_id para garantizar a nivel de BD
            # que ningún hotel pueda tener más de un comprador asignado.
            # Se usa CREATE UNIQUE INDEX IF NOT EXISTS para ser idempotente.
            cur.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS uq_comprador_hotel
                ON usuario_comprador_hoteles (hotel_id)
            """)
            # ── Log de WhatsApp (v9.5) ───────────────────────────────────────
            cur.execute("""
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
            """)
            # ── Techo de gastos (v9.0) ───────────────────────────────────────
            cur.execute("""
                CREATE TABLE IF NOT EXISTS familias (
                    id     SERIAL PRIMARY KEY,
                    nombre TEXT NOT NULL UNIQUE,
                    activo INTEGER NOT NULL DEFAULT 1
                )
            """)
            cur.execute("ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS familia_id INTEGER REFERENCES familias(id)")
            cur.execute("ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS importe NUMERIC(10,2)")
            cur.execute("""
                DO $$ BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='pedidos' AND column_name='sujeto_techo'
                    ) THEN
                        ALTER TABLE pedidos ADD COLUMN sujeto_techo INTEGER NOT NULL DEFAULT 0;
                    END IF;
                END $$;
            """)
            # ── Tabla config_alertas (v10.5) ─────────────────────────────────────
            cur.execute("""
                CREATE TABLE IF NOT EXISTS config_alertas (
                    clave  TEXT PRIMARY KEY,
                    valor  TEXT NOT NULL,
                    tipo   TEXT NOT NULL DEFAULT 'numero',
                    label  TEXT NOT NULL,
                    grupo  TEXT NOT NULL DEFAULT 'general',
                    orden  INTEGER NOT NULL DEFAULT 0
                )
            """)
            cur.execute("SELECT COUNT(*) as n FROM config_alertas")
            row = cur.fetchone()
            n = row[0] if isinstance(row, tuple) else row['n']
            if n == 0:
                defaults = [
                    ("enviado_primera",        "15", "numero", "Enviado al proveedor — 1ª alerta (días)",           "estado_enviado",    1),
                    ("enviado_urgente",         "25", "numero", "Enviado al proveedor — Urgente (días)",             "estado_enviado",    2),
                    ("enviado_ciclo",           "10", "numero", "Enviado al proveedor — Ciclo repetición (días)",    "estado_enviado",    3),
                    ("firma_compras_primera",    "8", "numero", "Firma Dir. Compras — 1ª alerta (días)",             "estado_firma",      1),
                    ("firma_compras_urgente",    "0", "numero", "Firma Dir. Compras — Urgente (días, 0=nunca)",      "estado_firma",      2),
                    ("firma_compras_ciclo",      "8", "numero", "Firma Dir. Compras — Ciclo repetición (días)",      "estado_firma",      3),
                    ("firma_hotel_primera",      "5", "numero", "Firma Dir. Hotel — 1ª alerta (días)",               "estado_firma",      4),
                    ("firma_hotel_urgente",      "0", "numero", "Firma Dir. Hotel — Urgente (días, 0=nunca)",        "estado_firma",      5),
                    ("firma_hotel_ciclo",        "5", "numero", "Firma Dir. Hotel — Ciclo repetición (días)",        "estado_firma",      6),
                    ("entrega_parcial_primera", "10", "numero", "Entrega Parcial — 1ª alerta (días)",                "estado_entrega",    1),
                    ("entrega_parcial_urgente",  "0", "numero", "Entrega Parcial — Urgente (días, 0=nunca)",         "estado_entrega",    2),
                    ("entrega_parcial_ciclo",   "10", "numero", "Entrega Parcial — Ciclo repetición (días)",         "estado_entrega",    3),
                    ("cotizacion_primera",       "2", "numero", "Pendiente Cotización — 1ª alerta (días)",           "estado_cotizacion", 1),
                    ("cotizacion_urgente",       "3", "numero", "Pendiente Cotización — Urgente (días)",             "estado_cotizacion", 2),
                    ("dias_critico",            "60", "numero", "Días crítico global (fuerza reenvío urgente)",      "global",            1),
                    ("activar_uso_plazo_entrega","1",  "bool",   "Activar alertas basadas en plazo de entrega del proveedor", "global", 2),
                    ("plazo_aviso_dias_antes",   "5",  "numero", "Plazo entrega — Aviso previo (días antes de la entrega)",   "plazo_entrega", 1),
                    ("plazo_urgente_ciclo",       "2",  "numero", "Plazo entrega — Ciclo urgente tras vencer (cada N días)",   "plazo_entrega", 2),
                    ("plazo_parcial_aviso_dias_antes", "3", "numero", "Entrega Parcial c/plazo — Aviso previo (días antes)",   "plazo_entrega", 3),
                    ("plazo_parcial_urgente_ciclo",    "2", "numero", "Entrega Parcial c/plazo — Ciclo urgente (cada N días)", "plazo_entrega", 4),
                    ("techo_max_pedido",      "3000", "numero", "Techo — Importe máximo por pedido (€)",             "techo",             1),
                    ("techo_max_mes",         "6000", "numero", "Techo — Importe máximo mensual por hotel (€)",      "techo",             2),
                    ("techo_max_pedidos",        "2", "numero", "Techo — Nº máximo de pedidos por hotel/mes",        "techo",             3),
                    ("techo_pct_amarillo",      "60", "numero", "Techo — % consumido para alerta 🟡 amarilla (defecto 60%)",  "techo",             4),
                ]
                cur.executemany(
                    "INSERT INTO config_alertas (clave,valor,tipo,label,grupo,orden) VALUES (%s,%s,%s,%s,%s,%s)",
                    defaults
                )
            # ── Solicitudes de acceso en 2 fases (v10.5) ────────────────────
            cur.execute("""
                CREATE TABLE IF NOT EXISTS solicitudes_acceso (
                    id              SERIAL PRIMARY KEY,
                    nombre          TEXT NOT NULL,
                    apellidos       TEXT NOT NULL,
                    email           TEXT NOT NULL,
                    hoteles         TEXT NOT NULL,
                    usuario_windows TEXT,
                    token           TEXT UNIQUE,
                    estado          TEXT NOT NULL DEFAULT 'fase1_pendiente',
                    ip_solicitante  TEXT,
                    creado_en       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    token_expira    TIMESTAMPTZ,
                    completado_en   TIMESTAMPTZ
                )
            """)
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_solicitudes_token ON solicitudes_acceso(token)"
            )
            # Migración v11.6.7: columna movil en solicitudes_acceso
            cur.execute(
                "ALTER TABLE solicitudes_acceso ADD COLUMN IF NOT EXISTS movil TEXT"
            )
            # ── Tabla cola de notificaciones para el bridge agenda (v10.7.7) ──────
            # Cada fila es un aviso pendiente de entregar a un usuario concreto.
            # El bridge lo consume con GET /api/bridge/notificaciones y marca leído.
            cur.execute("""
                CREATE TABLE IF NOT EXISTS bridge_notificaciones (
                    id           SERIAL PRIMARY KEY,
                    usuario      TEXT NOT NULL,         -- username del destinatario
                    tipo         TEXT NOT NULL,         -- 'cambio_estado' | 'alerta_auto' | 'techo'
                    pedido_id    INTEGER,               -- puede ser NULL (p.ej. alertas de techo)
                    titulo       TEXT NOT NULL,
                    mensaje      TEXT NOT NULL,
                    nivel        TEXT NOT NULL DEFAULT 'aviso',  -- 'aviso' | 'urgente'
                    leido        BOOLEAN NOT NULL DEFAULT FALSE,
                    creado_en    TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_bridge_notif_usuario_leido "
                "ON bridge_notificaciones(usuario, leido)"
            )
            # ── v11.4.0 — Plazo de entrega por pedido ─────────────────────────
            cur.execute(
                "ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS plazo_entrega_dias INTEGER"
            )
            for _clave, _valor, _tipo, _label, _grupo, _orden in [
                ('activar_uso_plazo_entrega',      '1', 'bool',   'Activar alertas basadas en plazo de entrega del proveedor', 'global',        2),
                ('plazo_aviso_dias_antes',          '5', 'numero', 'Plazo entrega — Aviso previo (días antes de la entrega)',   'plazo_entrega', 1),
                ('plazo_urgente_ciclo',             '2', 'numero', 'Plazo entrega — Ciclo urgente tras vencer (cada N días)',   'plazo_entrega', 2),
                ('plazo_parcial_aviso_dias_antes',  '3', 'numero', 'Entrega Parcial c/plazo — Aviso previo (días antes)',       'plazo_entrega', 3),
                ('plazo_parcial_urgente_ciclo',     '2', 'numero', 'Entrega Parcial c/plazo — Ciclo urgente (cada N días)',     'plazo_entrega', 4),
            ]:
                cur.execute("""
                    INSERT INTO config_alertas (clave, valor, tipo, label, grupo, orden)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (clave) DO NOTHING
                """, (_clave, _valor, _tipo, _label, _grupo, _orden))
            # ── v11.9.0 — Cola de restauración de backups (Opción C) ──────────
            # El panel web inserta filas aquí; un agente local (restore_agent.py)
            # ejecutado en el PC con acceso a la carpeta de red las procesa.
            cur.execute("""
                CREATE TABLE IF NOT EXISTS restore_queue (
                    id                  SERIAL PRIMARY KEY,
                    backup_nombre       TEXT NOT NULL,
                    backup_ruta         TEXT NOT NULL,
                    modo                TEXT NOT NULL DEFAULT 'pedidos',
                    estado              TEXT NOT NULL DEFAULT 'pendiente',
                    solicitado_por      TEXT,
                    solicitado_en       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    iniciado_en         TIMESTAMPTZ,
                    completado_en       TIMESTAMPTZ,
                    resumen             JSONB,
                    error_msg           TEXT,
                    pre_restore_backup  TEXT
                )
            """)
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_restore_queue_estado ON restore_queue(estado)"
            )
            # Columna añadida en v11.9.1 — backups existentes de v11.9.0 la reciben aquí
            cur.execute(
                "ALTER TABLE restore_queue ADD COLUMN IF NOT EXISTS pre_restore_backup TEXT"
            )
            # ── Fix v11.8.6 — Listado de backups vía caché del agente local ───
            # /api/admin/backup/listar intentaba leer Path(ruta) directamente
            # en el servidor (Render), que no tiene acceso a la red local de
            # la oficina — el mismo problema ya resuelto para /restaurar con
            # la cola restore_queue. Ahora restore_agent.py escanea la carpeta
            # de backups en cada ciclo y sincroniza el resultado aquí; el
            # panel web solo lee esta tabla, nunca toca el filesystem.
            cur.execute("""
                CREATE TABLE IF NOT EXISTS backups_cache (
                    id                SERIAL PRIMARY KEY,
                    ruta              TEXT NOT NULL,
                    ruta_normalizada  TEXT NOT NULL,
                    nombre            TEXT NOT NULL,
                    fecha             TEXT NOT NULL,
                    fecha_raw         TIMESTAMP,
                    mb                NUMERIC NOT NULL DEFAULT 0,
                    adjuntos          INTEGER NOT NULL DEFAULT 0,
                    tiene_log         BOOLEAN NOT NULL DEFAULT FALSE,
                    log_contenido     TEXT,
                    valido            BOOLEAN NOT NULL DEFAULT FALSE,
                    tipo              TEXT NOT NULL DEFAULT 'diario',
                    actualizado_en    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE (ruta_normalizada, nombre)
                )
            """)
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_backups_cache_ruta ON backups_cache(ruta_normalizada)"
            )

            # ── v11.9.4 — Columna es_correo en pedido_adjuntos ──────────────
            # Antes, distinguir un correo (.eml/.msg) de un documento normal
            # se hacía mirando la extensión del nombre del archivo guardado
            # (nombre ILIKE '%.eml'), tanto en las validaciones de subida como
            # en las de cambio de estado. Funciona, pero es un acoplamiento
            # frágil: si el nombre se llega a guardar de otra forma en algún
            # punto futuro, la clasificación se rompe en silencio sin que
            # salte ningún error. Pasamos a una columna explícita.
            cur.execute(
                "ALTER TABLE pedido_adjuntos ADD COLUMN IF NOT EXISTS es_correo BOOLEAN"
            )
            # Backfill: rellenar la columna para adjuntos ya existentes,
            # usando la misma heurística de extensión que se usaba antes
            # (es la única información disponible para datos ya guardados).
            # A partir de aquí, todo adjunto nuevo se inserta con el valor
            # ya calculado en el momento de la subida, sin volver a inferir.
            cur.execute("""
                UPDATE pedido_adjuntos
                SET es_correo = (
                    LOWER(nombre) LIKE '%.eml' OR LOWER(nombre) LIKE '%.msg'
                )
                WHERE es_correo IS NULL
            """)
            cur.execute(
                "ALTER TABLE pedido_adjuntos ALTER COLUMN es_correo SET DEFAULT FALSE"
            )
            cur.execute(
                "ALTER TABLE pedido_adjuntos ALTER COLUMN es_correo SET NOT NULL"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_adjuntos_tipo_correo ON pedido_adjuntos(pedido_id, tipo, es_correo)"
            )
            # ── v12.0.5 — Tarifa acordada (pedido sin presupuesto) ──────────
            # Permite marcar un pedido como "tarifa acordada" para eximirlo
            # de la obligatoriedad de Nº Presupuesto + documento adjunto al
            # pasar a ENVIADO AL PROVEEDOR. Por defecto siempre desmarcado.
            cur.execute(
                "ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS tarifa_acordada BOOLEAN NOT NULL DEFAULT FALSE"
            )
        db.close()
        log.info("Auto-migración OK")
    except Exception as e:
        log.warning(f"Auto-migración omitida: {e}")

with app.app_context():
    _auto_migrate()

# ── Base de datos (psycopg2 / PostgreSQL) ─────────────────────────────────────

def get_db():
    if "db" not in g:
        if not DATABASE_URL:
            raise RuntimeError(
                "DATABASE_URL no está configurada. "
                "Ve a Render → tu servicio → Environment y añade la variable DATABASE_URL "
                "con la URI de tu base de datos PostgreSQL (Supabase → Settings → Database → URI)."
            )
        g.db = psycopg2.connect(
            DATABASE_URL,
            cursor_factory=RealDictCursor,
            connect_timeout=10,
            keepalives=1,
            keepalives_idle=30,
            keepalives_interval=10,
            keepalives_count=3,
        )
        g.db.autocommit = False
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop("db", None)
    if db:
        db.close()

def init_db():
    """Ejecuta el esquema inicial en PostgreSQL. Llamar solo una vez."""
    with app.app_context():
        db = get_db()
        with db.cursor() as cur:
            for stmt in SQL_STATEMENTS:
                cur.execute(stmt)
            # Migración: añadir columnas nuevas a proveedores si no existen
            for col_def in [
                ("codigo",        "TEXT"),
                ("movil",         "TEXT"),
                ("observaciones", "TEXT"),
            ]:
                cur.execute(f"""
                    ALTER TABLE proveedores ADD COLUMN IF NOT EXISTS {col_def[0]} {col_def[1]}
                """)
        db.commit()
        log.info("Base de datos inicializada en PostgreSQL")

def query(sql, args=(), one=False):
    """SELECT helper — devuelve list[RealDictRow] o un RealDictRow."""
    with get_db().cursor() as cur:
        cur.execute(sql, args)
        rv = cur.fetchall()
    return (rv[0] if rv else None) if one else rv

def execute(sql, args=()):
    """INSERT/UPDATE/DELETE helper — devuelve el cursor para leer RETURNING."""
    cur = get_db().cursor()
    cur.execute(sql, args)
    return cur

def row_to_dict(row):
    return dict(row) if row else None

def rows_to_list(rows):
    return [dict(r) for r in rows]

def format_albaran_display(albaran_str):
    """
    Convierte el string de albarán almacenado al formato legible para Excel/emails.
    Formato almacenado: "NUM1::FECHA1 | NUM2::FECHA2"
    Formato legible:   "NUM1 (FECHA1) | NUM2 (FECHA2)"
    Retrocompatible con el formato antiguo "NUM1 | NUM2".
    """
    if not albaran_str:
        return albaran_str
    partes = []
    for entry in albaran_str.split('|'):
        entry = entry.strip()
        if not entry:
            continue
        if '::' in entry:
            num, fecha = entry.split('::', 1)
            num, fecha = num.strip(), fecha.strip()
            partes.append(f"{num} ({fecha})" if fecha else num)
        else:
            partes.append(entry)
    return ' | '.join(partes) if partes else albaran_str


def _parse_albaran_entries(albaran_str):
    """
    Parsea el campo entrada_albaran_num ("NUM::FECHA | NUM::FECHA | NUM")
    en una lista de entregas: [{"num": str, "fecha_iso": "YYYY-MM-DD"|None}, ...]
    Retrocompatible con entradas antiguas sin fecha (solo "NUM").
    Conserva el orden cronológico en que fueron registradas.
    """
    if not albaran_str:
        return []
    entradas = []
    for entry in albaran_str.split('|'):
        entry = entry.strip()
        if not entry:
            continue
        if '::' in entry:
            num, fecha = entry.split('::', 1)
            num, fecha = num.strip(), fecha.strip()
        else:
            num, fecha = entry, ''
        entradas.append({"num": num or '—', "fecha_iso": fecha or None})
    return entradas


def _fecha_es(fecha_val):
    """Convierte una fecha 'YYYY-MM-DD' (o similar) en 'DD/MM/YYYY'. None si no hay valor."""
    if not fecha_val:
        return None
    try:
        return datetime.strptime(str(fecha_val)[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        return str(fecha_val)


def _resumen_entregas(pedido: dict, estado_nuevo: str = None) -> dict:
    """
    Construye un resumen de las entregas (albaranes) registradas en el pedido
    a partir de entrada_albaran_num, listo para insertar en correos/Telegram
    de cambio de estado.

    Cuando el estado de referencia es ENTREGADO, la última entrada registrada
    se marca como "es_final" (la entrega que cierra el pedido).

    Devuelve:
        {
          "entregas":        [{"num","fecha_iso","fecha_es","es_final"}, ...],
          "total":           int,
          "ultima_fecha_es": str|None,   # fecha de la entrega más reciente registrada
          "tiene_fechas":    bool,       # alguna entrega tiene fecha informada
        }
    """
    entradas = _parse_albaran_entries(pedido.get("entrada_albaran_num"))
    estado_ref = estado_nuevo or pedido.get("estado")
    out = []
    for idx, e in enumerate(entradas):
        es_final = (estado_ref == "ENTREGADO" and idx == len(entradas) - 1)
        out.append({
            "num":       e["num"],
            "fecha_iso": e["fecha_iso"],
            "fecha_es":  _fecha_es(e["fecha_iso"]),
            "es_final":  es_final,
        })
    fechas_validas = [e["fecha_es"] for e in out if e["fecha_es"]]
    return {
        "entregas":        out,
        "total":           len(out),
        "ultima_fecha_es": fechas_validas[-1] if fechas_validas else None,
        "tiene_fechas":    bool(fechas_validas),
    }


def _html_bloque_entregas(resumen: dict, estado_nuevo: str) -> str:
    """Tabla HTML con el histórico de entregas (albaranes + fechas) para el correo interno."""
    if not resumen["entregas"]:
        return ""
    filas = []
    for i, e in enumerate(resumen["entregas"], 1):
        etiqueta = "Entrega final (TOTAL)" if e["es_final"] else f"Entrega parcial {i}"
        fecha_txt = e["fecha_es"] or "fecha no indicada"
        estilo = ' style="background:#e8f5e9;font-weight:600"' if e["es_final"] else ''
        filas.append(
            f'<tr{estilo}><td>{i}</td><td>{etiqueta}</td>'
            f'<td>{e["num"]}</td><td>{fecha_txt}</td></tr>'
        )
    titulo = ("Histórico de entregas registradas" if estado_nuevo == "ENTREGADO"
              else "Entregas parciales registradas hasta la fecha")
    plural = "s" if resumen["total"] != 1 else ""
    return (
        f'<p style="margin:16px 0 6px"><b>{titulo}</b> ({resumen["total"]} entrada{plural}):</p>'
        f'<table border="1" cellpadding="6" style="border-collapse:collapse;font-family:sans-serif;font-size:13px">'
        f'<tr style="background:#f0f0f0"><th>#</th><th>Tipo</th><th>Nº Entrada DALI/SAP</th><th>Fecha</th></tr>'
        + "".join(filas) + "</table>"
    )


def _text_bloque_entregas(resumen: dict, estado_nuevo: str) -> str:
    """Bloque de texto plano con el histórico de entregas, para el correo interno (fallback texto)."""
    if not resumen["entregas"]:
        return ""
    titulo = ("Histórico de entregas registradas" if estado_nuevo == "ENTREGADO"
              else "Entregas parciales registradas hasta la fecha")
    lineas = [f"{titulo} ({resumen['total']}):"]
    for i, e in enumerate(resumen["entregas"], 1):
        etiqueta = "ENTREGA FINAL (TOTAL)" if e["es_final"] else f"Entrega parcial {i}"
        fecha_txt = e["fecha_es"] or "fecha no indicada"
        lineas.append(f"  {i}. {etiqueta} — Nº {e['num']} — {fecha_txt}")
    return "\n".join(lineas)


def _telegram_bloque_entregas(resumen: dict, estado_nuevo: str) -> list:
    """Líneas (para añadir a un mensaje Markdown de Telegram) con el histórico de entregas."""
    if not resumen["entregas"]:
        return []
    titulo = ("📦 *Histórico de entregas*" if estado_nuevo == "ENTREGADO"
              else "📦 *Entregas parciales hasta la fecha*")
    lineas = ["", f"{titulo} ({resumen['total']}):"]
    for i, e in enumerate(resumen["entregas"], 1):
        marca = "✅" if e["es_final"] else "▫️"
        etiqueta = "Entrega final (TOTAL)" if e["es_final"] else f"Parcial {i}"
        fecha_txt = e["fecha_es"] or "sin fecha"
        lineas.append(f"{marca} {etiqueta} — Nº {e['num']} — {fecha_txt}")
    return lineas

# ── Autenticación ──────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "No autenticado"}), 401
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "No autenticado"}), 401
        if session.get("rol") != "admin":
            return jsonify({"error": "Solo administradores"}), 403
        return f(*args, **kwargs)
    return decorated

def current_user_id():
    return session.get("user_id")

def _log_email(db, pedido_id, tipo, destinatario, asunto, enviado, error=None):
    with db.cursor() as cur:
        cur.execute(
            "INSERT INTO emails_log (pedido_id,tipo,destinatario,asunto,enviado,error) VALUES (%s,%s,%s,%s,%s,%s)",
            (pedido_id, tipo, destinatario, asunto, 1 if enviado else 0, error)
        )

def enviar_emails_estado(db, pedido_id: int, estado_nuevo: str, estado_antes: str = None):
    """
    Construye los correos de notificación de cambio de estado (proveedor +
    internos) y los registra en _log_email. El envío lo hace el frontend
    vía EmailJS (único canal de email), por lo que no se intenta envío aquí:
    se devuelve una lista de correos pendientes para
    que el caller (create_pedido / update_pedido) la incluya en su respuesta
    JSON y el frontend los envíe vía EmailJS justo después de guardar.

    Devuelve: list[dict] — cada dict trae lo necesario para emailjs.send:
        {"tipo", "to_email", "bcc", "asunto", "body_text"}
    """
    pendientes = []

    pedido = row_to_dict(query(
        """SELECT p.*, h.nombre as hotel_nombre, h.codigo as hotel_codigo,
                  d.nombre as departamento_nombre,
                  pr.nombre as proveedor_nombre,
                  (SELECT email FROM proveedor_contactos WHERE proveedor_id=pr.id AND email IS NOT NULL AND email!='' AND es_principal=1 LIMIT 1) as proveedor_email,
                  (SELECT COALESCE(NULLIF(movil,''), NULLIF(telefono,'')) FROM proveedor_contactos WHERE proveedor_id=pr.id AND es_principal=1 LIMIT 1) as proveedor_movil,
                  (SELECT nombre FROM proveedor_contactos WHERE proveedor_id=pr.id AND es_principal=1 LIMIT 1) as proveedor_contacto_nombre
           FROM pedidos p
           LEFT JOIN hoteles h ON p.hotel_id = h.id
           LEFT JOIN departamentos d ON p.departamento_id = d.id
           LEFT JOIN proveedores pr ON p.proveedor_id = pr.id
           WHERE p.id = %s""", (pedido_id,), one=True
    ))
    if not pedido:
        return pendientes

    _proveedor_emails = _get_proveedor_emails_principales(pedido.get("proveedor_id"))
    _usuarios_hotel   = _get_todos_usuarios_hotel(pedido.get("hotel_codigo",""))
    _emails_compradores = [u["email"] for u in _usuarios_hotel["compradores"] if u.get("email")]
    _emails_hotel_users = [u["email"] for u in _usuarios_hotel["hotel_users"]  if u.get("email")]
    # Todos los internos del hotel (compradores + usuarios hotel) para BCC
    _todos_internos = list(dict.fromkeys(_emails_compradores + _emails_hotel_users))  # sin duplicados

    # ── Correo al proveedor (solo ENVIADO AL PROVEEDOR) ───────────────────────
    # Para:  todos los contactos principales del proveedor
    # BCC:   todos los usuarios del hotel (compradores + rol hotel)
    # Nota:  NO se envía correo interno adicional para este estado —
    #        el BCC ya cubre a todos los internos sin duplicar.
    if estado_nuevo in ESTADOS_EMAIL_PROVEEDOR and _proveedor_emails:
        _compradores_firma = _usuarios_hotel["compradores"]
        if not (_compradores_firma and _compradores_firma[0].get("email")):
            log.warning("[EMAIL] Pedido %s: no hay comprador con email asignado al hotel %s — email a proveedor omitido",
                        pedido_id, pedido.get("hotel_codigo",""))
        else:
            _email_comprador_firma = _compradores_firma[0]["email"]
            body_html = f"""
            <p style="background:#fff7e6;border:1px solid #f0c36d;color:#7a5b00;padding:10px 14px;border-radius:4px;font-size:12.5px;margin:0 0 18px">
              ⚠️ Este correo es exclusivo para notificaciones automáticas. Por favor, responda única y exclusivamente a la dirección que firma este comunicado.
            </p>
            <p>Estimado/a proveedor/a,</p>
            <p>
              Recientemente habrá recibido, a través de nuestro sistema habitual de pedidos, el pedido que se detalla a continuación.
              El presente correo tiene como finalidad <strong>confirmar su recepción</strong> y solicitarle que, a la mayor brevedad posible,
              nos indique si ha recibido dicho pedido y nos facilite la <strong>fecha estimada de entrega en el hotel</strong>.
            </p>
            <p style="background:#f5f8ff;border-left:4px solid #1a3c6e;padding:12px 16px;border-radius:0 4px 4px 0;margin:18px 0">
              <strong>Pedido Nº:</strong> {pedido.get('pedido_num','—')}<br>
              <strong>Hotel:</strong> {pedido.get('hotel_nombre','—')}<br>
              <strong>Departamento:</strong> {pedido.get('departamento_nombre','—')}
            </p>
            <p>
              Para confirmar la recepción del pedido y facilitar la fecha estimada de entrega, por favor responda
              a la dirección de correo que figura en la firma de este mensaje:
              <a href="mailto:{_email_comprador_firma}">{_email_comprador_firma}</a>
            </p>
            <p>Quedamos a su disposición para cualquier consulta.<br><br>
               Atentamente,<br>
               <strong>Dpto. Central de Compras Princess en Canarias</strong><br>
               Princess Hotels &amp; Resorts<br>
               <a href="mailto:{_email_comprador_firma}">{_email_comprador_firma}</a>
            </p>
            <p style="font-size:11.5px;color:#8a6d00;background:#fff7e6;border:1px solid #f0c36d;padding:8px 12px;border-radius:4px;margin-top:14px">
              Este correo es exclusivo para notificaciones automáticas. Por favor, responda única y exclusivamente a la dirección que firma este comunicado.
            </p>
            """
            body_text = (
                f"Estimado/a proveedor/a,\n\n"
                f"Recientemente habrá recibido, a través de nuestro sistema habitual de pedidos, el pedido que se detalla a continuación.\n"
                f"El presente correo tiene como finalidad confirmar su recepción y solicitarle que, a la mayor brevedad posible,\n"
                f"nos indique si ha recibido dicho pedido y nos facilite la fecha estimada de entrega en el hotel.\n\n"
                f"Pedido Nº: {pedido.get('pedido_num','—')}\n"
                f"Hotel: {pedido.get('hotel_nombre','—')}\n"
                f"Departamento: {pedido.get('departamento_nombre','—')}\n\n"
                f"Para confirmar la recepción del pedido y facilitar la fecha estimada de entrega, por favor responda\n"
                f"a la dirección de correo que figura en la firma de este mensaje: {_email_comprador_firma}\n\n"
                f"Quedamos a su disposición para cualquier consulta.\n\n"
                f"Atentamente,\nDpto. Central de Compras Princess en Canarias\n"
                f"Princess Hotels & Resorts\n{_email_comprador_firma}\n\n"
                f"Este correo es exclusivo para notificaciones automáticas. "
                f"Por favor, responda única y exclusivamente a la dirección que firma este comunicado."
            )
            _destino_proveedor = ", ".join(_proveedor_emails)
            _log_email(db, pedido_id, "proveedor", _destino_proveedor, subject := f"Pedido Nº {pedido.get('pedido_num','—')} — Princess Hotels & Resorts", False, "Pendiente de envío vía EmailJS")
            pendientes.append({
                "tipo":      "proveedor",
                "to_email":  _destino_proveedor,
                "bcc":       _todos_internos,   # compradores + usuarios hotel en BCC
                "asunto":    subject,
                "body_html": body_html,
                "body_text": body_text,
            })

    # ── Correo interno (ENTREGA PARCIAL, ENTREGADO, CANCELADO) ───────────────
    # Para:  primer comprador del hotel
    # BCC:   resto de compradores + usuarios hotel del mismo hotel
    # Nota:  ENVIADO AL PROVEEDOR queda excluido aquí — ya está cubierto
    #        por el BCC del correo al proveedor enviado arriba.
    ESTADOS_EMAIL_INTERNO_SIN_PROVEEDOR = ESTADOS_EMAIL_INTERNO - ESTADOS_EMAIL_PROVEEDOR
    if estado_nuevo in ESTADOS_EMAIL_INTERNO_SIN_PROVEEDOR and _todos_internos:
        _resumen_ent = _resumen_entregas(pedido, estado_nuevo)

        # Días transcurridos desde la tramitación, para contexto de seguimiento
        _dias_transcurridos = None
        try:
            if pedido.get("fecha_tramitacion"):
                _ft = datetime.strptime(str(pedido["fecha_tramitacion"])[:10], "%Y-%m-%d").date()
                _dias_transcurridos = (datetime.now(timezone.utc).date() - _ft).days
        except Exception:
            _dias_transcurridos = None

        _importe_txt    = f"{pedido.get('importe'):.2f} €" if pedido.get('importe') is not None else '—'
        _fecha_tram_txt = _fecha_es(pedido.get('fecha_tramitacion')) or '—'
        _dias_txt       = f" ({_dias_transcurridos} día(s) desde tramitación)" if _dias_transcurridos is not None else ''

        _INTRO_ESTADO = {
            "ENTREGA PARCIAL": "Se ha registrado una <strong>entrega parcial</strong> en este pedido. A continuación se detalla el histórico de entregas recibidas hasta la fecha.",
            "ENTREGADO":        "El pedido ha sido marcado como <strong>ENTREGADO</strong> (entrega total). A continuación se detalla el histórico completo de entregas, incluyendo la fecha de la entrega final.",
            "CANCELADO":        "El pedido ha sido <strong>CANCELADO</strong>.",
        }
        _intro_html = _INTRO_ESTADO.get(estado_nuevo, "")
        _intro_html_block = f"<p>{_intro_html}</p>" if _intro_html else ""

        subject_i = f"[Control Pedidos] {pedido.get('hotel_codigo','')} · Pedido {pedido.get('pedido_num','—')} → {estado_nuevo}"
        if estado_nuevo == "ENTREGADO" and _resumen_ent["ultima_fecha_es"]:
            subject_i += f" ({_resumen_ent['ultima_fecha_es']})"
        elif estado_nuevo == "ENTREGA PARCIAL" and _resumen_ent["ultima_fecha_es"]:
            subject_i += f" — última entrega {_resumen_ent['ultima_fecha_es']}"

        body_html_i = f"""
        <p>Cambio de estado en el sistema de Control de Pedidos:</p>
        {_intro_html_block}
        <table border="1" cellpadding="6" style="border-collapse:collapse;font-family:sans-serif;font-size:13px">
          <tr><td><b>Hotel</b></td><td>{pedido.get('hotel_nombre','')} ({pedido.get('hotel_codigo','')})</td></tr>
          <tr><td><b>Departamento</b></td><td>{pedido.get('departamento_nombre','')}</td></tr>
          <tr><td><b>Pedido Nº</b></td><td>{pedido.get('pedido_num','—')}</td></tr>
          <tr><td><b>Presupuesto Nº</b></td><td>{pedido.get('presupuesto_num') or '—'}</td></tr>
          <tr><td><b>Proveedor</b></td><td>{pedido.get('proveedor_nombre','—')}</td></tr>
          <tr><td><b>Importe</b></td><td>{_importe_txt}</td></tr>
          <tr><td><b>Estado anterior</b></td><td>{estado_antes or '—'}</td></tr>
          <tr><td><b>Estado nuevo</b></td><td><b>{estado_nuevo}</b></td></tr>
          <tr><td><b>Fecha tramitación</b></td><td>{_fecha_tram_txt}{_dias_txt}</td></tr>
        </table>
        {_html_bloque_entregas(_resumen_ent, estado_nuevo)}
        """
        if estado_nuevo == "CANCELADO" and pedido.get("observaciones"):
            body_html_i += f'<p style="margin-top:14px"><b>Observaciones / motivo:</b><br>{pedido.get("observaciones")}</p>'

        _INTRO_ESTADO_TXT = {
            "ENTREGA PARCIAL": "Se ha registrado una entrega parcial en este pedido. A continuación se detalla el histórico de entregas recibidas hasta la fecha.",
            "ENTREGADO":        "El pedido ha sido marcado como ENTREGADO (entrega total). A continuación se detalla el histórico completo de entregas, incluyendo la fecha de la entrega final.",
            "CANCELADO":        "El pedido ha sido CANCELADO.",
        }
        _intro_text = _INTRO_ESTADO_TXT.get(estado_nuevo, "")

        body_text_i = (
            f"Cambio de estado en el sistema de Control de Pedidos:\n\n"
            + (f"{_intro_text}\n\n" if _intro_text else "")
            + f"Hotel: {pedido.get('hotel_nombre','')} ({pedido.get('hotel_codigo','')})\n"
            + f"Departamento: {pedido.get('departamento_nombre','')}\n"
            + f"Pedido Nº: {pedido.get('pedido_num','—')}\n"
            + f"Presupuesto Nº: {pedido.get('presupuesto_num') or '—'}\n"
            + f"Proveedor: {pedido.get('proveedor_nombre','—')}\n"
            + f"Importe: {_importe_txt}\n"
            + f"Estado anterior: {estado_antes or '—'}\n"
            + f"Estado nuevo: {estado_nuevo}\n"
            + f"Fecha tramitación: {_fecha_tram_txt}{_dias_txt}"
        )
        _bloque_text_ent = _text_bloque_entregas(_resumen_ent, estado_nuevo)
        if _bloque_text_ent:
            body_text_i += "\n\n" + _bloque_text_ent
        if estado_nuevo == "CANCELADO" and pedido.get("observaciones"):
            body_text_i += f"\n\nObservaciones / motivo:\n{pedido.get('observaciones')}"

        for dest in _todos_internos:
            _log_email(db, pedido_id, "interno", dest, subject_i, False, "Pendiente de envío vía EmailJS")
        pendientes.append({
            "tipo":      "interno",
            "to_email":  _todos_internos[0],
            "bcc":       _todos_internos[1:],
            "asunto":    subject_i,
            "body_html": body_html_i,
            "body_text": body_text_i,
        })

    return pendientes

# ── Helper norden ──────────────────────────────────────────────────────────────

# La asignación ya no está hardcodeada: se gestiona desde el panel de admin
# en Usuarios → sección "Hoteles asignados (compras)".
# La función _get_compradores_hotel(hotel_codigo) sustituye al antiguo diccionario
# HOTEL_COMPRADOR y lee en tiempo real qué compradores tienen ese hotel asignado.

# ── Telegram Bot — alertas automáticas ─────────────────────────────────────────
TELEGRAM_BOT_TOKEN      = os.environ.get("TELEGRAM_BOT_TOKEN", "")
# ADMIN_TELEGRAM_CHAT_ID eliminado: los chat_id se gestionan desde el panel de admin (campo telegram_chat_id en usuario)

# ── Tipos de alerta que generan copia de supervisión a los administradores ──────
# "urgente"       → job diario con nivel urgente (pedidos críticos parados)
# "techo"         → alerta de techo de gastos (supervisión financiera)
# "cambio_estado" → cambio de estado CON bloque de alerta activo
# "aviso"         → recordatorio diario → NO se copia (evitar saturación)
# Solo las alertas URGENTES llegan a admins por supervisión automática.
# techo-rojo usa tipo="urgente"; techo-amarillo y cambio_estado sin alerta urgente NO llegan a admins.
TIPOS_SUPERVISION_ADMIN = {"urgente"}


def _get_admin_emails() -> list:
    """
    Devuelve lista de emails de todos los usuarios con rol admin o compras activos en BD.
    Los destinatarios se gestionan exclusivamente desde el panel de administración.
    USO: notificaciones de pedidos (cambios de estado, alertas).
    NUNCA usar para solicitudes de acceso — usar _get_solo_admin_emails().
    """
    try:
        admins = rows_to_list(query(
            "SELECT email FROM usuarios WHERE rol IN ('admin','compras') AND activo=1 "
            "AND email IS NOT NULL AND TRIM(email) != ''"
        )) or []
        return [a["email"] for a in admins if a.get("email")]
    except Exception as exc:
        log.error("[_get_admin_emails] Error consultando emails admin/compras: %s", exc)
        return []


def _get_solo_admin_emails() -> list:
    """
    Devuelve ÚNICAMENTE emails de administradores (rol='admin') activos en BD.
    Los administradores se gestionan exclusivamente desde el panel de administración.
    """
    try:
        admins = rows_to_list(query(
            "SELECT email FROM usuarios WHERE rol='admin' AND activo=1 "
            "AND email IS NOT NULL AND TRIM(email) != ''"
        )) or []
        return [a["email"] for a in admins if a.get("email")]
    except Exception as exc:
        log.error("[_get_solo_admin_emails] Error consultando emails admin: %s", exc)
        return []


def _get_admins_telegram() -> list:
    """
    Devuelve lista de dicts {username, nombre, telegram_chat_id} de todos los
    administradores activos que tienen telegram_chat_id configurado en BD.
    El campo telegram_chat_id se gestiona desde el panel de administración.
    """
    try:
        admins = rows_to_list(query(
            "SELECT username, nombre, telegram_chat_id FROM usuarios "
            "WHERE rol='admin' AND activo=1 AND telegram_chat_id IS NOT NULL "
            "AND TRIM(telegram_chat_id) != ''"
        )) or []
    except Exception as exc:
        log.error("[_get_admins_telegram] Error consultando admins con Telegram: %s", exc)
        admins = []
    return admins


def _notify_solicitud_telegram(texto: str) -> None:
    """
    Envia un mensaje Telegram a todos los admins con chat_id configurado.
    Usado para notificaciones del flujo de solicitudes de acceso (Fase 1 / Fase 2).
    """
    admins = _get_admins_telegram()
    if not admins:
        log.debug("[SOL_TELEGRAM] Sin admins con Telegram configurado.")
        return
    for adm in admins:
        username = adm.get("username", "admin")
        chat_id  = adm.get("telegram_chat_id")
        if chat_id:
            res = _send_telegram(chat_id, texto)
            log.info("[SOL_TELEGRAM] -> %s (%s): %s",
                     username, chat_id,
                     "OK" if res.get("ok") else res.get("error"))
        # Encolar en bridge para que el admin lo vea también en main_agenda
        _encolar_bridge_notificacion(
            usuario=username,
            tipo="solicitud_acceso",
            titulo="📋 Nueva solicitud de acceso",
            mensaje=texto.replace("*", ""),
            nivel="aviso",
            pedido_id=None,
        )


def _enviar_supervision_admins(texto: str, tipo_supervision: str,
                               titulo_bridge: str = None,
                               pedido_id_bridge: int = None) -> None:
    """
    Envía copia de supervisión a todos los admins con Telegram configurado,
    SOLO si el tipo_supervision está en TIPOS_SUPERVISION_ADMIN.

    Parámetros:
        texto             – Mensaje ya construido (igual que el enviado al comprador).
        tipo_supervision  – "urgente" | "techo" | "cambio_estado" | "aviso" | …
        titulo_bridge     – Título descriptivo para la entrada en Agenda/bridge.
                            Si es None se usa un texto genérico de supervisión.
        pedido_id_bridge  – ID del pedido relacionado (None para alertas sin pedido).
    """
    if tipo_supervision not in TIPOS_SUPERVISION_ADMIN:
        return  # Este tipo no requiere copia a admins

    admins = _get_admins_telegram()
    if not admins:
        log.debug("[SUPERVISION] Sin admins con Telegram — tipo=%s", tipo_supervision)
        return

    prefijo = "\U0001F4CB *[Supervisión Admin]* — copia automática\n\n"
    texto_admin = prefijo + texto

    for adm in admins:
        chat_id  = adm.get("telegram_chat_id")
        username = adm.get("username", "admin")
        if chat_id:
            res = _send_telegram(chat_id, texto_admin)
            log.info("[SUPERVISION] Telegram admin → %s (%s) tipo=%s: %s",
                     username, chat_id, tipo_supervision,
                     "OK" if res.get("ok") else res.get("error"))
        # ── Encolar en bridge agenda para este admin ────────────────────────
        # Usar el título descriptivo si se proporcionó, o uno genérico
        _encolar_bridge_notificacion(
            usuario=username,
            tipo="supervision",
            titulo=titulo_bridge or "📋 [Supervisión Admin] — copia automática",
            mensaje=texto.replace("*", ""),
            nivel="urgente",
            pedido_id=pedido_id_bridge,
        )


def _get_compradores_hotel(hotel_codigo: str) -> list:
    """
    Devuelve lista de dicts {username, nombre, email, movil, telegram_chat_id}
    de los usuarios con rol 'compras' que tienen asignado el hotel indicado.

    Sustituye al antiguo diccionario HOTEL_COMPRADOR hardcodeado.
    La asignación se gestiona desde admin: Usuarios → Hoteles asignados (compras).
    """
    if not hotel_codigo:
        return []
    hotel_codigo = hotel_codigo.upper()
    hotel_row = query("SELECT id FROM hoteles WHERE codigo=%s AND activo=1", (hotel_codigo,), one=True)
    if not hotel_row:
        return []
    hotel_id = hotel_row["id"]
    rows = rows_to_list(query(
        """SELECT u.id, u.username, u.nombre, u.email, u.movil, u.telegram_chat_id
           FROM usuarios u
           JOIN usuario_comprador_hoteles uch ON uch.usuario_id = u.id
           WHERE uch.hotel_id = %s AND u.activo = 1 AND u.rol = 'compras'
           ORDER BY u.nombre""",
        (hotel_id,)
    ))
    return rows

def _get_usuarios_hotel_rol_telegram(hotel_codigo: str) -> list:
    """
    Devuelve lista de dicts {username, nombre, email, movil, telegram_chat_id}
    de los usuarios con rol 'hotel' asignados al hotel indicado (tabla
    usuario_hoteles), SIN filtrar por si tienen o no telegram_chat_id —
    eso se comprueba en el momento de enviar (igual que con los compradores).

    Equivalente, para el canal Telegram, a la parte "hotel_users" de
    _get_todos_usuarios_hotel() (que se usa para los correos). Se mantiene
    como función independiente porque el correo filtra por email NOT NULL
    y aquí no aplica ese filtro (lo relevante es el telegram_chat_id).
    """
    if not hotel_codigo:
        return []
    hotel_codigo = hotel_codigo.upper()
    hotel_row = query("SELECT id FROM hoteles WHERE codigo=%s AND activo=1", (hotel_codigo,), one=True)
    if not hotel_row:
        return []
    hotel_id = hotel_row["id"]
    rows = rows_to_list(query(
        """SELECT u.id, u.username, u.nombre, u.email, u.movil, u.telegram_chat_id
           FROM usuarios u
           JOIN usuario_hoteles uh ON uh.usuario_id = u.id
           WHERE uh.hotel_id = %s AND u.activo = 1 AND u.rol = 'hotel'
           ORDER BY u.nombre""",
        (hotel_id,)
    ))
    return rows

def _send_telegram(chat_id: str, text: str) -> dict:
    """Envía un mensaje de Telegram al chat_id indicado. Devuelve {ok, error}."""
    import urllib.request, urllib.error
    try:
        payload = json.dumps({"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())
            return {"ok": result.get("ok", False), "error": None}
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        log.error("Telegram HTTP %s para chat_id %s: %s", e.code, chat_id, body)
        return {"ok": False, "error": f"HTTP {e.code}: {body[:200]}"}
    except Exception as e:
        log.error("Telegram error para chat_id %s: %s", chat_id, e)
        return {"ok": False, "error": str(e)}


def _encolar_bridge_notificacion(usuario: str, tipo: str, titulo: str, mensaje: str,
                                  nivel: str = "aviso", pedido_id: int = None) -> None:
    """
    Inserta una fila en bridge_notificaciones para que el bridge de main_agenda
    la recoja en la próxima consulta a /api/bridge/notificaciones.

    Esta función se llama SIEMPRE que se envía un Telegram a un comprador o admin,
    garantizando paridad total entre los avisos de Telegram y los de main_agenda.

    Parámetros:
        usuario   – username del destinatario (igual que en la tabla usuarios)
        tipo      – 'cambio_estado' | 'alerta_auto' | 'techo' | 'supervision'
        titulo    – línea resumen (se mostrará como título del popup)
        mensaje   – cuerpo completo del aviso
        nivel     – 'aviso' | 'urgente'
        pedido_id – id del pedido (None para alertas de techo sin pedido concreto)
    """
    try:
        db = get_db()
        db.cursor().execute(
            """INSERT INTO bridge_notificaciones
               (usuario, tipo, pedido_id, titulo, mensaje, nivel)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (usuario.lower(), tipo, pedido_id, titulo, mensaje, nivel)
        )
        db.commit()
    except Exception as exc:
        log.warning("bridge_notif: no se pudo encolar para %s — %s", usuario, exc)


def _enviar_telegram_compradores(pedido: dict, dias: int, nivel: str) -> list:
    """
    Envía alerta automática por Telegram a los compradores responsables del hotel.
    Los compradores se obtienen dinámicamente desde BD via _get_compradores_hotel().
    Devuelve lista de resultados [{username, chat_id, ok, error}].
    """
    hotel_codigo = (pedido.get("hotel_codigo") or "").upper()
    compradores  = _get_compradores_hotel(hotel_codigo)
    if not compradores:
        log.warning("Telegram: sin compradores para hotel %s", hotel_codigo)
        return []

    # ── Construir mensaje compacto y limpio ──────────────────────────────────
    emoji     = "🔴" if nivel == "urgente" else "🟡"
    nivel_txt = "ALERTA URGENTE" if nivel == "urgente" else "AVISO"
    estado    = pedido.get("estado", "")

    estado_titulo = {
        "ENVIADO AL PROVEEDOR":               "Enviado al proveedor",
        "PENDIENTE FIRMA DIRECCION COMPRAS":  "Pendiente firma compras",
        "PENDIENTE DE FIRMA DIRECCION HOTEL": "Pendiente firma hotel",
        "ENTREGA PARCIAL":                    "Entrega parcial",
        "PENDIENTE COTIZACIÓN":               "Pendiente cotización",
    }.get(estado, estado.capitalize())

    hotel_cod  = pedido.get("hotel_codigo", "?")
    hotel_nom  = pedido.get("hotel_nombre", "")
    proveedor  = pedido.get("proveedor_nombre") or ""
    pedido_sap = pedido.get("pedido_num") or ""
    norden     = pedido.get("norden") or ""
    fecha_ref  = pedido.get("fecha_tramitacion") or pedido.get("fecha_solicitud") or ""

    def _fmt_fecha(f):
        if not f:
            return ""
        try:
            if hasattr(f, "strftime"):
                return f.strftime("%d/%m/%Y")
            parts = str(f)[:10].split("-")
            return "/".join(reversed(parts)) if len(parts) == 3 else str(f)[:10]
        except Exception:
            return str(f)[:10]

    lineas = [f"{emoji} *{nivel_txt} — {estado_titulo}*", ""]
    lineas.append(f"🏨 Hotel: *{hotel_cod}* — {hotel_nom}")
    if pedido_sap:
        lineas.append(f"📄 Pedido SAP: *{pedido_sap}*")
    elif norden:
        lineas.append(f"📄 Línea #: *{norden}*")
    if proveedor:
        lineas.append(f"🏢 Proveedor: {proveedor}")
    if fecha_ref:
        lineas.append(f"📅 Fecha origen: {_fmt_fecha(fecha_ref)}")
    lineas.append(f"⏳ Sin respuesta: *{dias} días*")
    lineas += ["", "— Control Pedidos Princess Canarias"]
    texto = "\n".join(lineas)

    # ── Construir título corto para el popup de agenda ────────────────────────
    pid_pedido = pedido.get("id")
    titulo_bridge = f"{emoji} [{nivel_txt}] Pedido #{pid_pedido} · {hotel_cod}"

    resultados = []
    for comp in compradores:
        username = comp.get("username", "?")
        chat_id  = comp.get("telegram_chat_id")
        if not chat_id:
            log.warning("Telegram: sin telegram_chat_id para %s", username)
            resultados.append({"username": username, "chat_id": None, "ok": False, "error": "Sin telegram_chat_id"})
        else:
            res = _send_telegram(chat_id, texto)
            log.info("Telegram → %s (%s): %s", username, chat_id, "OK" if res["ok"] else res["error"])
            resultados.append({"username": username, "chat_id": chat_id, **res})
        # ── Encolar en bridge agenda (independiente de si tiene Telegram) ─────
        _encolar_bridge_notificacion(
            usuario=username,
            tipo="alerta_auto",
            titulo=titulo_bridge,
            mensaje=texto.replace("*", ""),  # quitar markdown de Telegram
            nivel=nivel,
            pedido_id=pid_pedido,
        )

    # ── Encolar en bridge agenda para ADMINS (paridad total con compradores) ─────
    # Los admins reciben en su Agenda exactamente los mismos avisos que el comprador,
    # independientemente del nivel (aviso o urgente), para poder supervisar el estado
    # real de los pedidos sin depender únicamente del polling de 15 min.
    for adm in _get_admins_telegram():
        adm_username = adm.get("username", "admin")
        _encolar_bridge_notificacion(
            usuario=adm_username,
            tipo="supervision",
            titulo=titulo_bridge,
            mensaje=texto.replace("*", ""),
            nivel=nivel,
            pedido_id=pid_pedido,
        )

    # ── Copia Telegram de supervisión a admins (solo alertas urgentes) ───────────
    # El Telegram de supervisión solo se envía para urgentes (evitar saturación).
    # El aviso en Agenda ya lo cubre el bloque anterior para todos los niveles.
    _enviar_supervision_admins(
        texto, nivel,
        titulo_bridge=titulo_bridge,
        pedido_id_bridge=pid_pedido,
    )  # nivel="urgente" → copia Telegram; "aviso" → omite Telegram (Agenda ya encolada arriba)

    return resultados

# ── Telegram inmediato por cambio de estado en edición de pedido ───────────────

# Estados que activan Telegram inmediato al cambiar durante una edición.
# Se excluyen estados terminales sin acción pendiente (SERVIDO TOTAL, CANCELADO).
def _calcular_info_alerta(pedido: dict, estado_nuevo: str,
                          ignorar_si_modificacion_manual: bool = False) -> dict | None:
    """
    Dado un pedido y su nuevo estado, calcula si ese estado genera una condición
    de alerta según UMBRALES_ALERTAS, y devuelve un dict con:
        { "nivel": "aviso"|"urgente", "dias": int, "motivo": str }
    Si no genera alerta, devuelve None.

    Se usa para enriquecer el mensaje de Telegram con contexto de alerta
    cuando el cambio de estado recae en un estado vigilado.

    Parámetro ignorar_si_modificacion_manual:
    ─────────────────────────────────────────
    Cuando True, suprime SIEMPRE la alerta temporal aunque el estado esté en
    UMBRALES_ALERTAS y los días superen el umbral.

    Motivación: las alertas de tipo "N días desde tramitación" están pensadas
    para detectar pedidos *parados* sin acción. Cuando el operador acaba de
    cambiar el estado manualmente (p. ej. PENDIENTE → ENVIADO AL PROVEEDOR),
    añadir "⚠️ 15 días desde tramitación" es contradictorio — el usuario
    literalmente acaba de actuar. El job diario (_job_alertas_diarias) ya
    recoge esa alerta en su próxima ejecución si el pedido sigue sin avanzar.

    Por tanto:
    - ignorar_si_modificacion_manual=False (default) → comportamiento normal,
      usado por el job diario y consultas de diagnóstico.
    - ignorar_si_modificacion_manual=True → sin bloque de alerta, usado desde
      _telegram_cambio_estado (cambios manuales desde update_pedido).
    """
    # ── Guard: si es cambio manual, la alerta temporal es contradictoria ──────
    if ignorar_si_modificacion_manual:
        return None

    cfg = _build_umbrales().get(estado_nuevo)
    if not cfg:
        return None  # estado no vigilado (SERVIDO TOTAL, CANCELADO, etc.)

    fecha_ref_campo = cfg.get("fecha_ref", "fecha_tramitacion")
    dias = _dias_desde_fecha(pedido.get(fecha_ref_campo))
    if dias is None or dias < cfg["primera"]:
        return None  # aún dentro del plazo normal, no hay alerta

    nivel  = "urgente" if (cfg.get("urgente") and dias >= cfg["urgente"]) else "aviso"
    motivo = (
        f"{dias} días desde {'fecha de solicitud' if fecha_ref_campo == 'fecha_solicitud' else 'tramitación'} "
        f"(umbral: {cfg['primera']}d"
        + (f", urgente: {cfg['urgente']}d" if cfg.get("urgente") else "")
        + ")"
    )
    return {"nivel": nivel, "dias": dias, "motivo": motivo}


def _telegram_cambio_estado(db, pedido_id: int, estado_nuevo: str, estado_antes: str,
                             usuario_nombre: str = "",
                             es_cambio_manual: bool = True) -> None:
    """
    Envía Telegram inmediato en cambio de estado (PUT /api/pedidos/<pid>),
    alineado con la misma lógica que el correo interno (enviar_emails_estado):

    - Solo se dispara para los estados establecidos en ESTADOS_EMAIL_INTERNO
      ("ENVIADO AL PROVEEDOR", "ENTREGA PARCIAL", "ENTREGADO", "CANCELADO").
      Para el resto de estados (PENDIENTE...) no se envía nada, igual que
      ocurre con el correo.
    - Nunca se envía Telegram al proveedor (a diferencia del correo, que sí
      le escribe en ENVIADO AL PROVEEDOR) — el Telegram es exclusivamente
      un canal interno.
    - Destinatarios internos: compradores del hotel + usuarios con rol
      "hotel" asignados a ese hotel (igual conjunto que el BCC del correo
      interno). Se comprueba individualmente quién tiene telegram_chat_id
      configurado: si un usuario hotel no lo tiene, simplemente no recibe
      Telegram, pero el comprador (si tiene chat_id) lo recibe igualmente.
      Si, en cambio, el usuario hotel SÍ tiene chat_id configurado, también
      recibe la comunicación, igual que el comprador.
    - Si el nuevo estado genera una condición de alerta (UMBRALES_ALERTAS)
      Y es_cambio_manual=False, se añade al mensaje: nivel y motivo (días).
    - Con es_cambio_manual=True (default para cambios desde update_pedido):
      el bloque de alerta temporal se suprime. Motivo: las alertas de "N días
      desde tramitación" detectan pedidos parados sin acción; mostrarla justo
      cuando el operador acaba de actuar sería contradictorio. El job diario
      recoge la alerta en su próxima ejecución si el pedido sigue sin avanzar.
    - SIN protección _ya_notificado_hoy: los cambios manuales siempre llegan.
      El job diario usa su propia deduplicación (tipo='telegram_auto').
    - Registra en whatsapp_log con tipo='telegram_estado' para trazabilidad
      separada del job automático.
    """
    # ── Filtro de estados: igual conjunto que el correo interno ──────────────
    if estado_nuevo not in ESTADOS_EMAIL_INTERNO:
        log.debug("[ESTADO] Estado %s fuera de ESTADOS_EMAIL_INTERNO — sin Telegram", estado_nuevo)
        return

    try:
        pedido = row_to_dict(query(f"{PEDIDO_SELECT_ALERTA} WHERE p.id=%s", (pedido_id,), one=True))
        if not pedido:
            log.warning("[ESTADO] Pedido %s no encontrado para Telegram", pedido_id)
            return

        hotel_cod   = (pedido.get("hotel_codigo") or "").upper()
        # ── Destinatarios internos: compradores + usuarios rol "hotel" ───────
        # (mismo conjunto de personas que reciben el BCC del correo interno;
        # aquí se comprueba uno por uno quién tiene telegram_chat_id).
        compradores  = _get_compradores_hotel(hotel_cod)
        usuarios_hot = _get_usuarios_hotel_rol_telegram(hotel_cod)
        destinatarios = compradores + usuarios_hot
        if not destinatarios:
            log.warning("[ESTADO] Sin compradores ni usuarios hotel para %s", hotel_cod)
            return

        # ── Bloque base: siempre presente ─────────────────────────────────────
        num_pedido = pedido.get("pedido_num") or f"Nº Orden {pedido.get('norden', '?')}"
        _ICONO_ESTADO = {
            "ENTREGA PARCIAL": "📦 Entrega parcial registrada.",
            "ENTREGADO":        "✅ Pedido entregado en su totalidad.",
            "CANCELADO":        "❌ Pedido cancelado.",
        }
        lineas = [
            "🔔 *Cambio de estado*",
            f"Hotel: *{pedido.get('hotel_codigo', '?')}* — {pedido.get('hotel_nombre', '')}",
            f"Pedido: *{num_pedido}*",
        ]
        if pedido.get("presupuesto_num"):
            lineas.append(f"Presupuesto: {pedido.get('presupuesto_num')}")
        lineas.append(f"Proveedor: {pedido.get('proveedor_nombre', '—')}")
        if pedido.get("importe") is not None:
            lineas.append(f"Importe: {pedido.get('importe'):.2f} €")
        lineas.append(f"Estado: {estado_antes or '—'}  →  *{estado_nuevo}*")
        if usuario_nombre:
            lineas.append(f"Modificado por: {usuario_nombre}")
        _intro_tg = _ICONO_ESTADO.get(estado_nuevo)
        if _intro_tg:
            lineas += ["", _intro_tg]

        # ── Histórico de entregas (albaranes + fechas), parciales y/o total ───
        _resumen_ent_tg = _resumen_entregas(pedido, estado_nuevo)
        lineas += _telegram_bloque_entregas(_resumen_ent_tg, estado_nuevo)

        # ── Motivo de cancelación, si lo hay ──────────────────────────────────
        if estado_nuevo == "CANCELADO" and pedido.get("observaciones"):
            lineas += ["", f"📝 Motivo: {pedido.get('observaciones')}"]

        # ── Bloque de alerta: solo si el nuevo estado genera alerta ───────────
        # ignorar_si_modificacion_manual suprime alertas temporales contradictorias
        # cuando el operador acaba de actuar (ver docstring de _calcular_info_alerta)
        info_alerta = _calcular_info_alerta(pedido, estado_nuevo,
                                            ignorar_si_modificacion_manual=es_cambio_manual)
        if info_alerta:
            emoji_nivel = "🔴" if info_alerta["nivel"] == "urgente" else "⚠️"
            lineas += [
                "",
                f"{emoji_nivel} *Alerta {info_alerta['nivel'].upper()}*",
                f"Motivo: {info_alerta['motivo']}",
            ]

        lineas.append("— Control Pedidos Princess Canarias")
        texto = "\n".join(lineas)

        # ── Título corto para popup bridge ────────────────────────────────────
        nivel_estado = info_alerta["nivel"] if info_alerta else "aviso"
        titulo_bridge = f"🔔 Cambio estado pedido #{pedido_id} · {pedido.get('hotel_codigo', '?')}"

        # ── Envío: compradores + usuarios rol "hotel" con telegram_chat_id ────────
        resultados = []
        for comp in destinatarios:
            username = comp.get("username", "?")
            chat_id  = comp.get("telegram_chat_id")
            if not chat_id:
                log.warning("[ESTADO] Sin telegram_chat_id para %s", username)
                resultados.append({"username": username, "chat_id": None,
                                   "ok": False, "error": "Sin telegram_chat_id"})
            else:
                res = _send_telegram(chat_id, texto)
                log.info("[ESTADO] Telegram → %s (%s): %s",
                         username, chat_id, "OK" if res["ok"] else res["error"])
                resultados.append({"username": username, "chat_id": chat_id, **res})
            # ── Encolar en bridge agenda (siempre, con o sin Telegram) ─────────
            _encolar_bridge_notificacion(
                usuario=username,
                tipo="cambio_estado",
                titulo=titulo_bridge,
                mensaje=texto.replace("*", ""),
                nivel=nivel_estado,
                pedido_id=pedido_id,
            )

        # ── Copia de supervisión a admins: solo si la alerta es urgente ────────
        # Cambio de estado normal o con alerta no urgente → solo al comprador.
        # Cambio de estado con alerta urgente → comprador + admins.
        if info_alerta and info_alerta.get("nivel") == "urgente":
            _enviar_supervision_admins(
                texto, "urgente",
                titulo_bridge=titulo_bridge,
                pedido_id_bridge=pedido_id,
            )

        # ── Log en whatsapp_log (tipo separado del job diario) ─────────────────
        nota_log = f"Cambio estado: {estado_antes} → {estado_nuevo}"
        if info_alerta:
            nota_log += f" | Alerta {info_alerta['nivel']} ({info_alerta['dias']}d)"
        for r in resultados:
            _log_whatsapp(
                db, pedido_id, "telegram_estado",
                r.get("username", "?"),
                nota_log,
                r.get("ok", False),
                r.get("error"),
            )
        db.commit()

    except Exception as exc:
        log.exception("[ESTADO] Error enviando Telegram cambio estado pedido %s: %s",
                      pedido_id, exc)


def _notificar_cambio_estado(db, pedido_id: int, estado_nuevo: str, estado_antes: str,
                              usuario_nombre: str = "") -> list:
    """
    Centraliza todas las notificaciones de un cambio de estado manual.

    Llama en orden a:
      1. enviar_emails_estado       → correo al proveedor y/o internos
      2. _telegram_cambio_estado    → mensaje Telegram inmediato (sin alerta temporal)

    Uso en update_pedido — tanto flujo normal como flujo hotel:

        if estado_nuevo != estado_antes:
            pendientes = _notificar_cambio_estado(db, pid, estado_nuevo, estado_antes,
                                     usuario_nombre=session.get("nombre", ""))

    Devuelve la lista de correos pendientes de envío vía EmailJS (ver
    enviar_emails_estado), para que el caller la incluya en su respuesta JSON.

    Ventajas de centralizar aquí:
    - update_pedido no acumula lógica de negocio de notificaciones.
    - El flujo hotel pasa por aquí igual que el flujo normal: cualquier
      canal futuro (Teams, Slack, push, webhook) queda cubierto automáticamente
      para ambos flujos con un único cambio en este método.
    - es_cambio_manual=True queda encapsulado: el caller no necesita saber
      el detalle de la supresión de alertas contradictorias.
    """
    pendientes = enviar_emails_estado(db, pedido_id, estado_nuevo, estado_antes)
    _telegram_cambio_estado(db, pedido_id, estado_nuevo, estado_antes,
                             usuario_nombre=usuario_nombre,
                             es_cambio_manual=True)
    return pendientes


# ── Job diario: alertas por fecha (independiente del usuario) ──────────────────

def get_config() -> dict:
    """Carga la configuración de alertas desde BD. Cachea en g Flask."""
    try:
        from flask import g as _g
        if hasattr(_g, '_config_alertas'):
            return _g._config_alertas
    except RuntimeError:
        pass

    try:
        rows = query("SELECT clave, valor, tipo FROM config_alertas")
        cfg = {}
        for r in (rows or []):
            v = r["valor"]
            if r["tipo"] == "numero":
                try:
                    v = float(v) if "." in str(v) else int(v)
                except (ValueError, TypeError):
                    pass
            cfg[r["clave"]] = v
    except Exception as exc:
        log.error("[get_config] Error leyendo config_alertas, usando defaults: %s", exc)
        cfg = {}

    defaults = {
        "enviado_primera": 15, "enviado_urgente": 25, "enviado_ciclo": 10,
        "firma_compras_primera": 8, "firma_compras_urgente": 0, "firma_compras_ciclo": 8,
        "firma_hotel_primera": 5, "firma_hotel_urgente": 0, "firma_hotel_ciclo": 5,
        "entrega_parcial_primera": 10, "entrega_parcial_urgente": 0, "entrega_parcial_ciclo": 10,
        "cotizacion_primera": 2, "cotizacion_urgente": 3,
        "dias_critico": 60,
        "activar_uso_plazo_entrega": 1,
        "plazo_aviso_dias_antes": 5,
        "plazo_urgente_ciclo": 2,
        "plazo_parcial_aviso_dias_antes": 3,
        "plazo_parcial_urgente_ciclo": 2,
        "techo_max_pedido": 3000, "techo_max_mes": 6000,
        "techo_max_pedidos": 2, "techo_pct_amarillo": 60,
    }
    for k, v in defaults.items():
        cfg.setdefault(k, v)

    try:
        from flask import g as _g
        _g._config_alertas = cfg
    except RuntimeError:
        pass
    return cfg


def _build_umbrales() -> dict:
    """UMBRALES_ALERTAS construido dinámicamente desde BD."""
    c = get_config()
    return {
        "ENVIADO AL PROVEEDOR": {
            "primera": c["enviado_primera"],
            "urgente": c["enviado_urgente"] or None,
            "ciclo":   c["enviado_ciclo"],
        },
        "PENDIENTE FIRMA DIRECCION COMPRAS": {
            "primera": c["firma_compras_primera"],
            "urgente": c["firma_compras_urgente"] or None,
            "ciclo":   c["firma_compras_ciclo"],
        },
        "PENDIENTE DE FIRMA DIRECCION HOTEL": {
            "primera": c["firma_hotel_primera"],
            "urgente": c["firma_hotel_urgente"] or None,
            "ciclo":   c["firma_hotel_ciclo"],
        },
        "ENTREGA PARCIAL": {
            "primera": c["entrega_parcial_primera"],
            "urgente": c["entrega_parcial_urgente"] or None,
            "ciclo":   c["entrega_parcial_ciclo"],
        },
        "PENDIENTE COTIZACIÓN": {
            "primera": c["cotizacion_primera"],
            "urgente": c["cotizacion_urgente"] or None,
            "ciclo":   None,
            "fecha_ref": "fecha_solicitud",
        },
    }


UMBRALES_ALERTAS = {
    "ENVIADO AL PROVEEDOR": {
        "primera": 15, "urgente": 25, "ciclo": 10,
    },
    "PENDIENTE FIRMA DIRECCION COMPRAS": {
        "primera": 8, "urgente": None, "ciclo": 8,
    },
    "PENDIENTE DE FIRMA DIRECCION HOTEL": {
        "primera": 5, "urgente": None, "ciclo": 5,
    },
    "ENTREGA PARCIAL": {
        "primera": 10, "urgente": None, "ciclo": 10,
    },
    "PENDIENTE COTIZACIÓN": {
        "primera": 2, "urgente": 3, "ciclo": None, "fecha_ref": "fecha_solicitud",
    },
}

def _dias_desde_fecha(fecha_str):
    """Calcula días transcurridos desde una fecha (string o date/datetime)."""
    if not fecha_str:
        return None
    try:
        if hasattr(fecha_str, 'date'):
            f = fecha_str.date()
        elif isinstance(fecha_str, _d):
            f = fecha_str
        else:
            f = _dt.strptime(str(fecha_str)[:10], "%Y-%m-%d").date()
        return (_date.today() - f).days
    except Exception:
        return None

def _ya_notificado_hoy(pedido_id: int, tipo: str = "telegram_auto") -> bool:
    """
    Devuelve True si ya se envió una notificación del tipo indicado para este pedido HOY.
    - tipo='telegram_auto'   → job diario de alertas por fecha
    - tipo='telegram_estado' → cambio de estado inmediato desde update_pedido
    Evita duplicar notificaciones si la misma acción se dispara varias veces.
    """
    try:
        row = query(
            """SELECT COUNT(*) as n FROM whatsapp_log
               WHERE pedido_id=%s AND tipo=%s
                 AND DATE(creado_en AT TIME ZONE 'Atlantic/Canary') =
                     (NOW() AT TIME ZONE 'Atlantic/Canary')::date""",
            (pedido_id, tipo), one=True
        )
        return (row["n"] if row else 0) > 0
    except Exception:
        return False

# SQL inline para el job (no depende de PEDIDO_SELECT_ALERTA que se define más abajo)
_JOB_PEDIDO_SQL = """
    SELECT p.id, p.norden, p.pedido_num, p.presupuesto_num, p.estado,
           p.fecha_tramitacion, p.fecha_solicitud, p.observaciones,
           p.plazo_entrega_dias,
           h.codigo as hotel_codigo, h.nombre as hotel_nombre,
           d.nombre as departamento_nombre,
           pr.nombre as proveedor_nombre,
           (SELECT email FROM proveedor_contactos WHERE proveedor_id=pr.id AND email IS NOT NULL AND email!=\'\' AND es_principal=1 LIMIT 1) as proveedor_email,
           (SELECT COALESCE(NULLIF(movil,\'\'),NULLIF(telefono,\'\')) FROM proveedor_contactos WHERE proveedor_id=pr.id AND es_principal=1 LIMIT 1) as proveedor_movil,
           (SELECT nombre FROM proveedor_contactos WHERE proveedor_id=pr.id AND es_principal=1 LIMIT 1) as proveedor_contacto_nombre
    FROM pedidos p
    LEFT JOIN hoteles h ON p.hotel_id = h.id
    LEFT JOIN departamentos d ON p.departamento_id = d.id
    LEFT JOIN proveedores pr ON p.proveedor_id = pr.id
"""

def _nunca_notificado(pedido_id: int) -> bool:
    """Devuelve True si el pedido nunca ha recibido un telegram_auto."""
    try:
        row = query(
            "SELECT COUNT(*) as n FROM whatsapp_log WHERE pedido_id=%s AND tipo='telegram_auto'",
            (pedido_id,), one=True
        )
        return (row["n"] if row else 0) == 0
    except Exception:
        return True  # En caso de error, asumir que nunca se notificó

def _dias_ultima_notificacion(pedido_id: int):
    """Devuelve cuántos días han pasado desde la última telegram_auto enviada (enviado=1)."""
    try:
        row = query(
            """SELECT DATE(MAX(creado_en)) as ultima FROM whatsapp_log
               WHERE pedido_id=%s AND tipo='telegram_auto' AND enviado=1""",
            (pedido_id,), one=True
        )
        if not row or not row["ultima"]:
            return None
        from datetime import date as _d
        ultima = row["ultima"]
        if hasattr(ultima, "date"):
            ultima = ultima.date()
        return (_d.today() - ultima).days
    except Exception:
        return None



# ── Helpers para lógica de plazo de entrega ──────────────────────────────────

def _calcular_fecha_entrega_prevista(fecha_tramitacion, plazo_dias):
    """
    Devuelve (date) fecha_tramitacion + plazo_dias, o None si falta algún dato.
    """
    if not fecha_tramitacion or not plazo_dias:
        return None
    try:
        if hasattr(fecha_tramitacion, 'date'):
            base = fecha_tramitacion.date()
        elif isinstance(fecha_tramitacion, _d):
            base = fecha_tramitacion
        else:
            base = _dt.strptime(str(fecha_tramitacion)[:10], "%Y-%m-%d").date()
        return base + timedelta(days=int(plazo_dias))
    except Exception:
        return None


def _alertas_plazo_entrega(pedido: dict, cfg_activado: bool):
    """
    Calcula si hoy debe generarse una alerta basada en el plazo de entrega
    informado por el proveedor.

    Estados soportados:
      - ENVIADO AL PROVEEDOR  → usa plazo_aviso_dias_antes / plazo_urgente_ciclo
      - ENTREGA PARCIAL       → usa plazo_parcial_aviso_dias_antes / plazo_parcial_urgente_ciclo

    Reglas (umbrales configurables desde Admin → Config Alertas):
      - primerAviso : EXACTAMENTE N días antes de fecha_entrega_prevista
      - silencio    : entre N-1 y 1 días antes
      - avisoEntrega: el mismo día de fecha_entrega_prevista  (delta == 0)
      - urgenteCada : cada M días a partir del día siguiente  (delta == M, 2M, 3M …)

    Devuelve None si no aplica, o dict {"nivel": "aviso"|"urgente", "motivo": str,
                                         "fecha_entrega_prevista": date}
    """
    if not cfg_activado:
        return None

    estado = pedido.get("estado")
    if estado == "ENVIADO AL PROVEEDOR":
        cfg_key_aviso  = "plazo_aviso_dias_antes"
        cfg_key_ciclo  = "plazo_urgente_ciclo"
        cfg_def_aviso  = 5
        cfg_def_ciclo  = 2
    elif estado == "ENTREGA PARCIAL":
        cfg_key_aviso  = "plazo_parcial_aviso_dias_antes"
        cfg_key_ciclo  = "plazo_parcial_urgente_ciclo"
        cfg_def_aviso  = 3
        cfg_def_ciclo  = 2
    else:
        return None

    plazo = pedido.get("plazo_entrega_dias")
    if not plazo:
        return None

    fecha_entrega = _calcular_fecha_entrega_prevista(
        pedido.get("fecha_tramitacion"), plazo
    )
    if not fecha_entrega:
        return None

    cfg = get_config()
    dias_aviso = int(cfg.get(cfg_key_aviso, cfg_def_aviso) or cfg_def_aviso)
    ciclo      = int(cfg.get(cfg_key_ciclo,  cfg_def_ciclo)  or cfg_def_ciclo)
    if ciclo < 1:
        ciclo = 1  # evitar división por cero

    from datetime import date as _d
    hoy   = _d.today()
    delta = (hoy - fecha_entrega).days  # negativo = antes, 0 = hoy, positivo = después

    fecha_str = fecha_entrega.strftime("%d/%m/%Y")

    # Primer aviso: únicamente el día exacto de N días antes
    if delta == -dias_aviso:
        return {
            "nivel":  "aviso",
            "motivo": f"Entrega prevista el {fecha_str} (faltan {dias_aviso} días)",
            "fecha_entrega_prevista": fecha_entrega,
        }

    # Silencio entre -(N-1) y -1 inclusive
    if -(dias_aviso - 1) <= delta <= -1:
        return None

    # Aviso el día exacto de la entrega
    if delta == 0:
        return {
            "nivel":  "urgente",
            "motivo": f"Hoy es la fecha de entrega prevista ({fecha_str})",
            "fecha_entrega_prevista": fecha_entrega,
        }

    # Urgente cada M días a partir del día siguiente (delta == M, 2M, 3M …)
    if delta > 0 and delta % ciclo == 0:
        return {
            "nivel":  "urgente",
            "motivo": f"Entrega prevista {fecha_str} superada hace {delta} día(s)",
            "fecha_entrega_prevista": fecha_entrega,
        }

    return None


def _debe_usar_logica_plazo(pedido: dict) -> bool:
    """True si el pedido tiene plazo informado Y la feature está activada en config."""
    cfg = get_config()
    activado = bool(int(cfg.get("activar_uso_plazo_entrega", 1) or 0))
    return activado and bool(pedido.get("plazo_entrega_dias"))


def _job_alertas_diarias():
    """
    Job automático: calcula alertas por fecha y envía Telegram
    a los compradores responsables sin ninguna interacción del usuario.
    Se ejecuta cada 60 segundos en horario 07:00-16:00 hora Canarias.

    Lógica de envío (por pedido):
      1. Nunca ha recibido telegram_auto  → envía siempre (primer aviso)
      2. días >= get_config()['dias_critico'] → envía siempre (umbral crítico)
      3. Resto                            → solo envía si han pasado >= ciclo días
                                            desde la última notificación
    En todos los casos, _ya_notificado_hoy() evita duplicados dentro del mismo día.
    """
    with app.app_context():
        _job_alertas_diarias_inner()

def _job_alertas_diarias_inner():
    log.info("▶ [SCHEDULER] Inicio job alertas diarias — %s", _date.today())
    try:
        alertas_raw = rows_to_list(query(
            _JOB_PEDIDO_SQL + """
            WHERE p.estado IN (
                \'ENVIADO AL PROVEEDOR\',
                \'PENDIENTE FIRMA DIRECCION COMPRAS\',
                \'PENDIENTE DE FIRMA DIRECCION HOTEL\',
                \'ENTREGA PARCIAL\',
                \'PENDIENTE COTIZACIÓN\'
            )
              AND (
                p.fecha_tramitacion IS NOT NULL
                OR (p.estado = \'PENDIENTE COTIZACIÓN\' AND p.fecha_solicitud IS NOT NULL)
              )
            ORDER BY p.fecha_tramitacion ASC
        """))
    except Exception as exc:
        log.error("[SCHEDULER] Error consultando pedidos: %s", exc)
        return

    enviados = 0
    omitidos = 0
    cfg_activar_plazo = bool(int(get_config().get("activar_uso_plazo_entrega", 1) or 0))

    for p in alertas_raw:
        # ── Lógica por plazo de entrega (si el pedido la tiene y está activada) ─
        info_plazo = _alertas_plazo_entrega(p, cfg_activar_plazo)
        if info_plazo:
            # Usar lógica de plazo en lugar de la estándar para ENVIADO AL PROVEEDOR
            nivel  = info_plazo["nivel"]
            motivo = info_plazo["motivo"]
            dias   = _dias_desde_fecha(p.get("fecha_tramitacion")) or 0

            if _ya_notificado_hoy(p["id"], "telegram_auto"):
                omitidos += 1
                continue

            # Para alertas de plazo: siempre enviar si corresponde (ciclo cada 2 días
            # ya está controlado por _alertas_plazo_entrega — solo devuelve algo
            # en días que toca). Dedup entre jobs del mismo día: _ya_notificado_hoy.
            debe_enviar = True
            log.info("[SCHEDULER-PLAZO] Pedido %s — %s (%s)", p["id"], nivel, motivo)

            resultados = _enviar_telegram_compradores(p, dias, nivel)
            try:
                db = get_db()
                for r in resultados:
                    _log_whatsapp(
                        db, p["id"], "telegram_auto",
                        r.get("username", "?"),
                        f"Alerta plazo entrega {nivel} — {motivo}",
                        r.get("ok", False),
                        r.get("error"),
                    )
                db.commit()
            except Exception as exc:
                log.error("[SCHEDULER] Error guardando log (plazo) pedido %s: %s", p["id"], exc)
            enviados += 1
            continue
        # ── Lógica estándar (sin plazo informado o feature desactivada) ──────────

        cfg = _build_umbrales().get(p["estado"])
        if not cfg:
            continue

        fecha_ref_campo = cfg.get("fecha_ref", "fecha_tramitacion")
        dias = _dias_desde_fecha(p.get(fecha_ref_campo))
        if dias is None or dias < cfg["primera"]:
            continue

        nivel = "urgente" if (cfg["urgente"] and dias >= cfg["urgente"]) else "aviso"

        # No enviar si ya se notificó hoy (evita duplicados por los 60 ciclos diarios)
        if _ya_notificado_hoy(p["id"], "telegram_auto"):
            omitidos += 1
            continue

        # ── Decisión de envío ────────────────────────────────────────────────
        # 1) Primer aviso: el pedido nunca recibió telegram_auto → enviar siempre
        # 2) Umbral crítico: >= 60 días → enviar siempre
        # 3) Resto: respetar ciclo — solo si han pasado >= ciclo días desde el último
        debe_enviar = False
        motivo_omision = ""

        if _nunca_notificado(p["id"]):
            debe_enviar = True
            log.info("[SCHEDULER] Pedido %s — primer aviso (%dd)", p["id"], dias)
        elif dias >= get_config()["dias_critico"]:
            debe_enviar = True
            log.info("[SCHEDULER] Pedido %s — umbral crítico (%dd >= %dd)", p["id"], dias, get_config()["dias_critico"])
        else:
            ciclo = cfg.get("ciclo")
            if ciclo:
                dias_desde_ultimo = _dias_ultima_notificacion(p["id"])
                if dias_desde_ultimo is None or dias_desde_ultimo >= ciclo:
                    debe_enviar = True
                    log.info("[SCHEDULER] Pedido %s — ciclo OK (%dd desde último)", p["id"], dias_desde_ultimo or 0)
                else:
                    motivo_omision = f"ciclo no cumplido ({dias_desde_ultimo}d < {ciclo}d)"
            else:
                motivo_omision = "sin ciclo, ya notificado anteriormente"

        if not debe_enviar:
            log.debug("[SCHEDULER] Pedido %s omitido — %s", p["id"], motivo_omision)
            omitidos += 1
            continue
        # ────────────────────────────────────────────────────────────────────

        resultados = _enviar_telegram_compradores(p, dias, nivel)

        # Registrar en whatsapp_log
        try:
            db = get_db()
            for r in resultados:
                _log_whatsapp(
                    db, p["id"], "telegram_auto",
                    r.get("username", "?"),
                    f"Alerta automática {nivel} — {dias}d sin respuesta",
                    r.get("ok", False),
                    r.get("error"),
                )
            db.commit()
        except Exception as exc:
            log.error("[SCHEDULER] Error guardando log pedido %s: %s", p["id"], exc)

        enviados += 1

    log.info("✅ [SCHEDULER] Job finalizado — %d alertas enviadas, %d omitidas", enviados, omitidos)


# ── Job de alerta FAMILIA/PARTIDA REPETIDA — rojo inmediato + reenvío dinámico ──
#
# Disparo:  cuando un hotel repite familia dentro del mismo mes (Regla 2 de _check_techo).
# Primera alerta: Telegram rojo 🔴 al comprador del hotel + a todos los admins.
# Reenvíos:
#   - Comprador  → 1 mensaje por hotel y día (todas las familias agrupadas)
#   - Admins     → 1 mensaje por hotel cada 2 días (todas las familias agrupadas)
# Deduplicación: máx. 1 notificación por HOTEL (no por familia) y día natural.
#
# Tipos usados en whatsapp_log:
#   'familia_repetida_comprador'   → dedup diario a nivel hotel
#   'familia_repetida_admin'       → dedup/ciclo 2 días a nivel hotel
# ──────────────────────────────────────────────────────────────────────────────────


def _ya_notificado_familia_repetida_hotel_hoy(hotel_codigo: str, tipo: str) -> bool:
    """Devuelve True si ya se envió hoy una alerta de familia repetida para este hotel."""
    try:
        row = query(
            """SELECT COUNT(*) as n FROM whatsapp_log
               WHERE pedido_id IS NULL
                 AND tipo = %s
                 AND destinatario LIKE %s
                 AND DATE(creado_en AT TIME ZONE 'Atlantic/Canary') =
                     (NOW() AT TIME ZONE 'Atlantic/Canary')::date""",
            (tipo, f"%{hotel_codigo}|famrep%"), one=True
        )
        return (row["n"] if row else 0) > 0
    except Exception:
        return False


def _dias_desde_ultimo_familia_repetida_admin(hotel_codigo: str) -> int | None:
    """
    Días transcurridos desde la última notificación 'familia_repetida_admin'
    para este hotel. None si nunca se envió.
    """
    try:
        row = query(
            """SELECT DATE(MAX(creado_en) AT TIME ZONE 'Atlantic/Canary') as ultima
               FROM whatsapp_log
               WHERE pedido_id IS NULL
                 AND tipo = 'familia_repetida_admin'
                 AND destinatario LIKE %s""",
            (f"%{hotel_codigo}|famrep%",), one=True
        )
        if not row or row["ultima"] is None:
            return None
        import pytz
        hoy = datetime.now(pytz.timezone("Atlantic/Canary")).date()
        return (hoy - row["ultima"]).days
    except Exception:
        return None


def _log_familia_repetida_hotel(hotel_codigo: str, tipo: str,
                                 destinatario: str, mensaje: str,
                                 enviado: bool, error=None) -> None:
    """Registra en whatsapp_log el envío de alerta de familia repetida (a nivel hotel)."""
    try:
        db = get_db()
        db.cursor().execute(
            "INSERT INTO whatsapp_log (pedido_id,tipo,destinatario,mensaje,enviado,error) "
            "VALUES (NULL,%s,%s,%s,%s,%s)",
            (tipo, f"{hotel_codigo}|famrep|{destinatario}",
             mensaje, 1 if enviado else 0, error)
        )
        db.commit()
    except Exception as exc:
        log.error("[FAM-REP] Error guardando log %s %s: %s", hotel_codigo, destinatario, exc)


def _job_familia_repetida() -> None:
    """
    Job que detecta hoteles con familia/partida repetida en el mes actual
    y dispara UNA alerta agrupada al comprador (diario) y a los admins (cada 2 días).
    Un único mensaje por hotel lista todas las familias repetidas.
    """
    with app.app_context():
        _job_familia_repetida_inner()


def _job_familia_repetida_inner() -> None:
    """Lógica interna del job de familia repetida."""
    import pytz
    tz_canarias = pytz.timezone("Atlantic/Canary")
    ahora = datetime.now(tz_canarias)

    # Solo en horario laboral (lun-vie 07:00-16:59)
    if ahora.weekday() >= 5 or not (7 <= ahora.hour <= 16):
        log.debug("[FAM-REP] Fuera de horario o día no laborable — saltando")
        return

    year, month = ahora.year, ahora.month
    mes_txt = ahora.strftime("%B %Y")

    log.info("▶ [FAM-REP] Revisando familias repetidas — %s", ahora.strftime("%Y-%m-%d %H:%M"))

    try:
        hoteles = rows_to_list(query(
            "SELECT id, codigo, nombre FROM hoteles WHERE activo=1 ORDER BY codigo"
        ))
    except Exception as exc:
        log.error("[FAM-REP] Error consultando hoteles: %s", exc)
        return

    enviados = 0

    for hotel in hoteles:
        hotel_id     = hotel["id"]
        hotel_codigo = (hotel["codigo"] or "").upper()
        hotel_nombre = hotel["nombre"] or ""

        # ── Detectar familias que aparecen más de una vez este mes ─────────
        try:
            familias_repetidas = rows_to_list(query("""
                SELECT p.familia_id, f.nombre as familia_nombre,
                       COUNT(*) as num_pedidos
                FROM pedidos p
                LEFT JOIN familias f ON p.familia_id = f.id
                WHERE p.hotel_id = %s
                  AND p.sujeto_techo = 1
                  AND p.estado NOT IN ('CANCELADO')
                  AND EXTRACT(YEAR  FROM p.creado_en) = %s
                  AND EXTRACT(MONTH FROM p.creado_en) = %s
                  AND p.familia_id IS NOT NULL
                GROUP BY p.familia_id, f.nombre
                HAVING COUNT(*) > 1
                ORDER BY f.nombre
            """, (hotel_id, year, month)))
        except Exception as exc:
            log.error("[FAM-REP] Error consultando pedidos hotel %s: %s", hotel_codigo, exc)
            continue

        if not familias_repetidas:
            continue

        # ── Construir UN único mensaje con todas las familias repetidas ────
        reenvio_adm = _dias_desde_ultimo_familia_repetida_admin(hotel_codigo)

        reenvio_txt = (
            f"⏱ Reenvío automático — sin resolver desde hace {reenvio_adm}d\n"
            if reenvio_adm is not None else
            "🔔 Primera alerta — familias repetidas detectadas\n"
        )

        familias_lista = "\n".join(
            "  • {} ({} pedidos)".format(
                f["familia_nombre"] or "ID {}".format(f["familia_id"]),
                f["num_pedidos"]
            )
            for f in familias_repetidas
        )

        texto = (
            "🔴 *ALERTA — Familia/Partida REPETIDA en el mes*\n"
            "\n"
            f"🏨 Hotel: *{hotel_codigo}* — {hotel_nombre}\n"
            "\n"
            f"📂 Familias repetidas ({len(familias_repetidas)}):\n"
            f"{familias_lista}\n"
            "\n"
            f"📅 Mes: {mes_txt}\n"
            f"{reenvio_txt}"
            "— Control Pedidos Princess Canarias"
        )

        titulo_bridge = (
            f"🔴 [FAMILIA REPETIDA] {hotel_codigo} — "
            f"{len(familias_repetidas)} familia(s)"
        )

        # ── Notificar al COMPRADOR (1 vez por hotel y día) ────────────────
        skip_comp = _ya_notificado_familia_repetida_hotel_hoy(
            hotel_codigo, "familia_repetida_comprador"
        )
        if not skip_comp:
            compradores = _get_compradores_hotel(hotel_codigo)
            if not compradores:
                log.warning("[FAM-REP] Sin compradores para hotel %s", hotel_codigo)
            else:
                for comp in compradores:
                    username = comp.get("username", "?")
                    chat_id  = comp.get("telegram_chat_id")
                    # ⚠️ LOG PRIMERO — garantiza dedup aunque falle el envío Telegram
                    _log_familia_repetida_hotel(
                        hotel_codigo, "familia_repetida_comprador",
                        username,
                        f"Familia repetida x{len(familias_repetidas)} — {mes_txt}",
                        False
                    )
                    if chat_id:
                        res = _send_telegram(chat_id, texto)
                        ok  = res.get("ok", False)
                        log.info("[FAM-REP] → comprador %s hotel %s (%d familias): %s",
                                 username, hotel_codigo, len(familias_repetidas),
                                 "OK" if ok else res.get("error"))
                        if ok:
                            try:
                                db = get_db()
                                db.cursor().execute(
                                    """UPDATE whatsapp_log SET enviado=1
                                       WHERE ctid = (
                                           SELECT ctid FROM whatsapp_log
                                           WHERE tipo='familia_repetida_comprador'
                                             AND destinatario=%s AND enviado=0
                                           ORDER BY creado_en DESC LIMIT 1
                                       )""",
                                    (f"{hotel_codigo}|famrep|{username}",)
                                )
                                db.commit()
                            except Exception as _elog:
                                log.warning("[FAM-REP] No se pudo actualizar log enviado comprador %s: %s", username, _elog)
                    else:
                        log.warning("[FAM-REP] Sin telegram_chat_id para comprador %s", username)
                    _encolar_bridge_notificacion(
                        usuario=username,
                        tipo="techo",
                        titulo=titulo_bridge,
                        mensaje=texto.replace("*", ""),
                        nivel="urgente",
                        pedido_id=None,
                    )
        else:
            log.debug("[FAM-REP] Comprador hotel %s — ya notificado hoy, omitiendo", hotel_codigo)

        # ── Notificar a ADMINS (1 vez por hotel cada 2 días) ──────────────
        skip_adm_hoy = _ya_notificado_familia_repetida_hotel_hoy(
            hotel_codigo, "familia_repetida_admin"
        )
        if skip_adm_hoy:
            log.debug("[FAM-REP] Admin hotel %s — ya notificado hoy, omitiendo", hotel_codigo)
        elif reenvio_adm is not None and reenvio_adm < 2:
            log.debug("[FAM-REP] Admin hotel %s — último aviso hace %d día(s), esperando 2d",
                      hotel_codigo, reenvio_adm)
        else:
            admins = _get_admins_telegram()
            if not admins:
                log.warning("[FAM-REP] Sin admins con Telegram configurado")
            else:
                for adm in admins:
                    username = adm.get("username", "?")
                    chat_id  = adm.get("telegram_chat_id")
                    # ⚠️ LOG PRIMERO — garantiza dedup aunque falle el envío Telegram
                    _log_familia_repetida_hotel(
                        hotel_codigo, "familia_repetida_admin",
                        username,
                        f"Familia repetida x{len(familias_repetidas)} — {mes_txt}",
                        False
                    )
                    if chat_id:
                        res = _send_telegram(chat_id, texto)
                        ok  = res.get("ok", False)
                        log.info("[FAM-REP] → admin %s hotel %s (%d familias): %s",
                                 username, hotel_codigo, len(familias_repetidas),
                                 "OK" if ok else res.get("error"))
                        if ok:
                            try:
                                db = get_db()
                                db.cursor().execute(
                                    """UPDATE whatsapp_log SET enviado=1
                                       WHERE ctid = (
                                           SELECT ctid FROM whatsapp_log
                                           WHERE tipo='familia_repetida_admin'
                                             AND destinatario=%s AND enviado=0
                                           ORDER BY creado_en DESC LIMIT 1
                                       )""",
                                    (f"{hotel_codigo}|famrep|{username}",)
                                )
                                db.commit()
                            except Exception as _elog:
                                log.warning("[FAM-REP] No se pudo actualizar log enviado admin %s: %s", username, _elog)
                    else:
                        log.warning("[FAM-REP] Sin telegram_chat_id para admin %s", username)
                    _encolar_bridge_notificacion(
                        usuario=username,
                        tipo="techo",
                        titulo=titulo_bridge,
                        mensaje=texto.replace("*", ""),
                        nivel="urgente",
                        pedido_id=None,
                    )

        enviados += 1

    log.info("✅ [FAM-REP] Fin revisión — %d hoteles con familias repetidas notificados", enviados)


# ── Job de techo URGENTE — cada 60 s, laborables 07:00-17:00, reenvío c/2 días ─

def _techo_urgente_es_horario_valido() -> bool:
    """
    Devuelve True si ahora mismo cumple las tres condiciones de envío:
      1. Día laborable (lunes=0 … viernes=4)
      2. Hora local (Atlantic/Canary) entre 07:00 y 16:59 inclusive
      3. El mes actual no ha cambiado respecto al mes del techo (siempre True aquí;
         la comprobación de mes se hace al calcular el semáforo, que usa CURRENT MONTH)
    """
    import pytz
    tz_canarias = pytz.timezone("Atlantic/Canary")
    ahora = datetime.now(tz_canarias)
    if ahora.weekday() >= 5:          # sábado=5, domingo=6
        return False
    if not (7 <= ahora.hour <= 16):   # 07:00–16:59; a las 17:00 ya no entra
        return False
    return True


def _ya_notificado_techo_urgente_hoy(hotel_codigo: str) -> bool:
    """
    Devuelve True si ya se envió hoy una alerta de techo URGENTE a admins
    para este hotel (tipo 'telegram_techo_urgente_admin').
    """
    try:
        row = query(
            """SELECT COUNT(*) as n FROM whatsapp_log
               WHERE pedido_id IS NULL
                 AND tipo = 'telegram_techo_urgente_admin'
                 AND destinatario LIKE %s
                 AND DATE(creado_en AT TIME ZONE 'Atlantic/Canary') =
                     (NOW() AT TIME ZONE 'Atlantic/Canary')::date""",
            (f"%{hotel_codigo}%",), one=True
        )
        return (row["n"] if row else 0) > 0
    except Exception as exc:
        log.error("[_ya_notificado_techo_urgente_hoy] Error consultando log para hotel %s: %s", hotel_codigo, exc)
        return False


def _dias_desde_ultimo_techo_urgente_admin(hotel_codigo: str) -> int | None:
    """
    Devuelve los días naturales transcurridos desde la última notificación
    de techo URGENTE a admins para este hotel, o None si nunca se envió.
    """
    try:
        row = query(
            """SELECT DATE(MAX(creado_en) AT TIME ZONE 'Atlantic/Canary') as ultima
               FROM whatsapp_log
               WHERE pedido_id IS NULL
                 AND tipo = 'telegram_techo_urgente_admin'
                 AND destinatario LIKE %s""",
            (f"%{hotel_codigo}%",), one=True
        )
        if not row or row["ultima"] is None:
            return None
        import pytz
        from datetime import date as _d
        hoy = datetime.now(pytz.timezone("Atlantic/Canary")).date()
        return (hoy - row["ultima"]).days
    except Exception as exc:
        log.error("[_dias_desde_ultimo_techo_urgente_admin] Error consultando log para hotel %s: %s", hotel_codigo, exc)
        return None


def _log_techo_urgente_admin(hotel_codigo: str, destinatario: str,
                              mensaje: str, enviado: bool, error=None) -> None:
    """Registra en whatsapp_log el envío de alerta de techo URGENTE a admins."""
    try:
        db = get_db()
        db.cursor().execute(
            "INSERT INTO whatsapp_log (pedido_id,tipo,destinatario,mensaje,enviado,error) "
            "VALUES (NULL,'telegram_techo_urgente_admin',%s,%s,%s,%s)",
            (destinatario, mensaje, 1 if enviado else 0, error)
        )
        db.commit()
    except Exception as exc:
        log.error("[TECHO-URG] Error guardando log %s %s: %s", hotel_codigo, destinatario, exc)


def _job_techo_urgente_admins() -> None:
    """
    Job que se ejecuta cada 60 segundos.

    Notifica a los administradores por Telegram cuando un hotel tiene su techo
    mensual en estado URGENTE (semáforo rojo), con las siguientes reglas:

    • Solo en días laborables (lun–vie).
    • Solo entre las 07:00 y las 16:59 (hora Canarias).
    • Primer envío: el mismo día en que el hotel entra en URGENTE.
    • Reenvíos: cada 2 días naturales desde el último aviso a admins,
      siempre que el hotel siga en rojo Y no haya cambiado de mes.
    • Deduplicación diaria: como máximo 1 notificación por hotel y día.
    """
    with app.app_context():
        _job_techo_urgente_admins_inner()


def _job_techo_urgente_admins_inner() -> None:
    """Lógica interna del job de techo urgente a admins."""

    if not _techo_urgente_es_horario_valido():
        log.debug("[TECHO-URG] Fuera de horario o día no laborable — saltando")
        return

    import pytz
    tz_canarias = pytz.timezone("Atlantic/Canary")
    ahora = datetime.now(tz_canarias)
    year, month = ahora.year, ahora.month

    log.info("▶ [TECHO-URG] Revisando techos URGENTES — %s", ahora.strftime("%Y-%m-%d %H:%M"))

    try:
        hoteles = rows_to_list(query(
            "SELECT id, codigo, nombre FROM hoteles WHERE activo=1 ORDER BY codigo"
        ))
    except Exception as exc:
        log.error("[TECHO-URG] Error consultando hoteles: %s", exc)
        return

    cfg = get_config()
    enviados = 0

    for hotel in hoteles:
        hotel_id     = hotel["id"]
        hotel_codigo = (hotel["codigo"] or "").upper()
        hotel_nombre = hotel["nombre"] or ""

        # ── 1. Calcular semáforo del mes actual ───────────────────────────
        try:
            pedidos = rows_to_list(query("""
                SELECT p.importe, p.familia_id, f.nombre as familia_nombre
                FROM pedidos p
                LEFT JOIN familias f ON p.familia_id = f.id
                WHERE p.hotel_id = %s
                  AND p.sujeto_techo = 1
                  AND p.estado NOT IN ('CANCELADO')
                  AND EXTRACT(YEAR  FROM p.creado_en) = %s
                  AND EXTRACT(MONTH FROM p.creado_en) = %s
            """, (hotel_id, year, month)))
        except Exception as exc:
            log.error("[TECHO-URG] Error consultando pedidos hotel %s: %s", hotel_codigo, exc)
            continue

        acumulado   = sum(float(p["importe"] or 0) for p in pedidos)
        num_pedidos = len(pedidos)

        # Semáforo urgente — solo dispara si es genuinamente ROJO:
        #   ROJO → acumulado >= techo_max_mes (100%)  O  num_pedidos >= techo_max_pedidos
        #   El job mensual ya cubre el amarillo (60% o 1 pedido) al comprador.
        #   Este job urgente solo notifica a admins cuando el techo está realmente superado.
        es_rojo = (
            acumulado >= cfg["techo_max_mes"]
            or num_pedidos > cfg["techo_max_pedidos"]
        )
        if not es_rojo:
            log.debug(
                "[TECHO-URG] Hotel %s — %.1f %% del techo (%d pedidos), no urgente",
                hotel_codigo,
                acumulado / cfg["techo_max_mes"] * 100 if cfg["techo_max_mes"] else 0,
                num_pedidos
            )
            continue

        # ── 2. Deduplicación diaria (máx. 1 aviso/hotel/día) ─────────────
        if _ya_notificado_techo_urgente_hoy(hotel_codigo):
            log.debug("[TECHO-URG] Hotel %s — ya notificado hoy, omitiendo", hotel_codigo)
            continue

        # ── 3. Regla de reenvío cada 2 días ──────────────────────────────
        dias_desde_ultimo = _dias_desde_ultimo_techo_urgente_admin(hotel_codigo)
        if dias_desde_ultimo is not None and dias_desde_ultimo < 2:
            log.debug(
                "[TECHO-URG] Hotel %s — último aviso hace %d día(s), esperando 2d",
                hotel_codigo, dias_desde_ultimo
            )
            continue

        # ── 4. Construir y enviar mensaje ─────────────────────────────────
        mes_txt = ahora.strftime("%B %Y")
        pct     = int(acumulado / cfg["techo_max_mes"] * 100) if cfg["techo_max_mes"] else 0

        familias_lista = "\n".join(
            f"• {f}" for f in sorted({
                p["familia_nombre"] for p in pedidos if p.get("familia_nombre")
            })
        ) or "—"

        motivo = []
        if acumulado >= cfg["techo_max_mes"]:
            motivo.append(f"gasto {acumulado:,.2f} € ≥ límite {cfg['techo_max_mes']:,.0f} € (100 %)")
        if num_pedidos >= cfg["techo_max_pedidos"]:
            motivo.append(f"{num_pedidos} pedidos ≥ máximo {cfg['techo_max_pedidos']}")

        reenvio_txt = (
            f"⏱ Reenvío automático — {dias_desde_ultimo}d sin resolver\n"
            if dias_desde_ultimo is not None else
            "🔔 Primera alerta de techo URGENTE\n"
        )

        texto = (
            "🔴 *URGENTE — Techo mensual SUPERADO*\n"
            "\n"
            f"🏨 Hotel: *{hotel_codigo}* — {hotel_nombre}\n"
            "\n"
            f"💰 Acumulado: *{acumulado:,.2f} €* ({pct} % del límite)\n"
            f"📦 Pedidos sujetos: {num_pedidos} / {cfg['techo_max_pedidos']}\n"
            f"⚠️ Motivo: {' | '.join(motivo)}\n"
            "\n"
            f"📂 Familias:\n{familias_lista}\n"
            "\n"
            f"📅 Mes: {mes_txt}\n"
            f"{reenvio_txt}"
            "— Control Pedidos Princess Canarias"
        )

        admins = _get_admins_telegram()
        if not admins:
            log.warning("[TECHO-URG] Sin admins con Telegram configurado")
            continue

        for adm in admins:
            username = adm.get("username", "?")
            chat_id  = adm.get("telegram_chat_id")
            if chat_id:
                res = _send_telegram(chat_id, texto)
                ok  = res.get("ok", False)
                log.info(
                    "[TECHO-URG] → admin %s hotel %s: %s",
                    username, hotel_codigo, "OK" if ok else res.get("error")
                )
                _log_techo_urgente_admin(
                    hotel_codigo,
                    f"{username}|{hotel_codigo}",
                    f"Techo URGENTE admin — {acumulado:,.2f} € — {mes_txt}",
                    ok, res.get("error")
                )
            # ── Encolar en bridge agenda para este admin ─────────────────────
            _encolar_bridge_notificacion(
                usuario=username,
                tipo="techo",
                titulo=f"💰 [TECHO URGENTE] Hotel {hotel_codigo} — {mes_txt}",
                mensaje=texto.replace("*", ""),
                nivel="urgente",
                pedido_id=None,
            )

        enviados += 1
        log.info(
            "[TECHO-URG] ✅ Hotel %s notificado a admins — %.2f € / %d pedidos",
            hotel_codigo, acumulado, num_pedidos
        )

    log.info("✅ [TECHO-URG] Fin revisión — %d hoteles urgentes notificados", enviados)


# ── Job de alertas de techo mensual ───────────────────────────────────────────

def _ya_notificado_techo_mes_hoy(hotel_codigo: str, semaforo: str) -> bool:
    """
    Devuelve True si ya se envió hoy una alerta de techo mensual para este hotel
    con el mismo nivel de semáforo (rojo/amarillo).
    Usa whatsapp_log con pedido_id=NULL y tipo='telegram_techo_mes_<semaforo>'.
    """
    tipo = f"telegram_techo_mes_{semaforo}"
    try:
        row = query(
            """SELECT COUNT(*) as n FROM whatsapp_log
               WHERE pedido_id IS NULL
                 AND tipo = %s
                 AND destinatario LIKE %s
                 AND DATE(creado_en AT TIME ZONE 'Atlantic/Canary') =
                     (NOW() AT TIME ZONE 'Atlantic/Canary')::date""",
            (tipo, f"%{hotel_codigo}%"), one=True
        )
        return (row["n"] if row else 0) > 0
    except Exception:
        return False


def _log_whatsapp_techo_mes(hotel_codigo: str, semaforo: str, destinatario: str,
                             mensaje: str, enviado: bool, error=None) -> None:
    """Registra en whatsapp_log una notificación de techo mensual (sin pedido_id)."""
    tipo = f"telegram_techo_mes_{semaforo}"
    try:
        db = get_db()
        db.cursor().execute(
            "INSERT INTO whatsapp_log (pedido_id,tipo,destinatario,mensaje,enviado,error) "
            "VALUES (NULL,%s,%s,%s,%s,%s)",
            (tipo, destinatario, mensaje, 1 if enviado else 0, error)
        )
        db.commit()
    except Exception as exc:
        log.error("[TECHO-MES] Error guardando log %s %s: %s", hotel_codigo, destinatario, exc)


def _job_alertas_techo_mensual() -> None:
    """
    Job diario que notifica por Telegram el estado del techo de gastos mensual por hotel.

    Lógica:
      - semáforo ROJO  (techo superado o nº pedidos >= máximo):
          → alerta URGENTE al comprador del hotel  +  copia supervisión a admins
      - semáforo AMARILLO (>= 75 % del techo o nº pedidos == máximo - 1):
          → aviso al comprador del hotel  (sin copia a admins)
      - semáforo VERDE  → sin notificación

    Deduplicación: solo envía una vez por hotel y nivel en el mismo día natural.
    """
    with app.app_context():
        _job_alertas_techo_mensual_inner()


def _job_alertas_techo_mensual_inner() -> None:
    """Lógica interna del job — llamada siempre dentro de app.app_context()."""
    from datetime import date as _date_local
    hoy   = _date_local.today()
    year  = hoy.year
    month = hoy.month

    log.info("▶ [TECHO-MES] Inicio job techo mensual — %s", hoy)

    try:
        hoteles = rows_to_list(query(
            "SELECT id, codigo, nombre FROM hoteles WHERE activo=1 ORDER BY codigo"
        ))
    except Exception as exc:
        log.error("[TECHO-MES] Error consultando hoteles: %s", exc)
        return

    enviados = 0
    omitidos = 0

    for hotel in hoteles:
        hotel_id     = hotel["id"]
        hotel_codigo = (hotel["codigo"] or "").upper()
        hotel_nombre = hotel["nombre"] or ""

        # ── Calcular acumulado del mes ────────────────────────────────────────
        try:
            pedidos = rows_to_list(query("""
                SELECT p.importe, p.familia_id, f.nombre as familia_nombre
                FROM pedidos p
                LEFT JOIN familias f ON p.familia_id = f.id
                WHERE p.hotel_id = %s
                  AND p.sujeto_techo = 1
                  AND p.estado NOT IN ('CANCELADO')
                  AND EXTRACT(YEAR  FROM p.creado_en) = %s
                  AND EXTRACT(MONTH FROM p.creado_en) = %s
            """, (hotel_id, year, month)))
        except Exception as exc:
            log.error("[TECHO-MES] Error consultando pedidos hotel %s: %s", hotel_codigo, exc)
            continue

        acumulado   = sum(float(p["importe"] or 0) for p in pedidos)
        num_pedidos = len(pedidos)

        # Semáforo:
        #   ROJO     → acumulado >= techo_max_mes  O  num_pedidos > techo_max_pedidos (techo realmente superado)
        #   AMARILLO → acumulado >= techo_max_mes * pct_amarillo/100  O  num_pedidos >= techo_max_pedidos (límite alcanzado)
        #   VERDE    → sin actividad sujeta al techo (sin notificación)
        umbral_amarillo = get_config()["techo_max_mes"] * get_config()["techo_pct_amarillo"] / 100
        if acumulado >= get_config()["techo_max_mes"] or num_pedidos > get_config()["techo_max_pedidos"]:
            semaforo = "rojo"
        elif acumulado >= umbral_amarillo or num_pedidos >= get_config()["techo_max_pedidos"]:
            semaforo = "amarillo"
        else:
            omitidos += 1
            log.debug("[TECHO-MES] Hotel %s — verde, sin notificación", hotel_codigo)
            continue

        # ── Deduplicación diaria por hotel + nivel ────────────────────────────
        if _ya_notificado_techo_mes_hoy(hotel_codigo, semaforo):
            omitidos += 1
            log.info("[TECHO-MES] Hotel %s — YA NOTIFICADO HOY semaforo=%s, omitiendo", hotel_codigo, semaforo)
            continue

        log.info("[TECHO-MES] Hotel %s — semaforo=%s acumulado=%.2f pedidos=%d -> enviando",
                 hotel_codigo, semaforo, acumulado, num_pedidos)
        compradores = _get_compradores_hotel(hotel_codigo)
        if not compradores:
            log.warning("[TECHO-MES] Sin compradores para hotel %s", hotel_codigo)
            continue

        # ── Construir mensaje ─────────────────────────────────────────────────
        mes_txt      = hoy.strftime("%B %Y")
        pct          = int(acumulado / get_config()["techo_max_mes"] * 100) if get_config()["techo_max_mes"] else 0
        familias_txt = ", ".join({
            p["familia_nombre"] for p in pedidos if p.get("familia_nombre")
        }) or "—"

        if semaforo == "rojo":
            emoji     = "🔴"
            nivel_txt = "URGENTE — Techo mensual superado"
        else:
            emoji     = "🟡"
            nivel_txt = f"AVISO — Techo mensual al {pct} %"

        familias_lista = "\n".join(
            f"• {f}" for f in sorted({p["familia_nombre"] for p in pedidos if p.get("familia_nombre")})
        ) or "—"

        _techo_mes     = get_config()["techo_max_mes"]
        _techo_pedidos = get_config()["techo_max_pedidos"]
        texto = (
            f"{emoji} *{nivel_txt}*\n"
            f"\n"
            f"🏨 Hotel: *{hotel_codigo}* — {hotel_nombre}\n"
            f"\n"
            f"💰 Acumulado actual: *{acumulado:,.2f} €*\n"
            f"📊 Límite configurado: {_techo_mes:,.0f} €\n"
            f"📦 Pedidos sujetos: {num_pedidos} / {_techo_pedidos}\n"
            f"\n"
            f"📂 Familias:\n{familias_lista}\n"
            f"\n"
            f"📅 Mes: {mes_txt}\n"
            "— Control Pedidos Princess Canarias"
        )

        # ── Enviar a compradores ──────────────────────────────────────────────
        nivel_techo = "urgente" if semaforo == "rojo" else "aviso"
        for comp in compradores:
            username = comp.get("username", "?")
            chat_id  = comp.get("telegram_chat_id")
            if chat_id:
                res = _send_telegram(chat_id, texto)
                ok  = res.get("ok", False)
                log.info("[TECHO-MES] → %s (%s): %s", username, hotel_codigo,
                         "OK" if ok else res.get("error"))
                _log_whatsapp_techo_mes(
                    hotel_codigo, semaforo,
                    f"{username}|{hotel_codigo}",
                    f"Techo mensual {semaforo} — {acumulado:,.2f} € — {mes_txt}",
                    ok, res.get("error")
                )
            else:
                log.warning("[TECHO-MES] Sin telegram_chat_id para %s", username)
            # ── Encolar en bridge agenda ──────────────────────────────────────
            _encolar_bridge_notificacion(
                usuario=username,
                tipo="techo",
                titulo=f"{emoji} [{nivel_txt}] Hotel {hotel_codigo} — {mes_txt}",
                mensaje=texto.replace("*", ""),
                nivel=nivel_techo,
                pedido_id=None,
            )

        # ── Copia a admins: gestionada exclusivamente por _job_techo_urgente_admins ──
        # No se envía copia aquí para evitar duplicado. El job _job_techo_urgente_admins
        # es el canal oficial hacia admins (con reenvío cada 2 días, horario laboral
        # y deduplicación diaria).

        enviados += 1

    log.info("✅ [TECHO-MES] Job finalizado — %d hoteles notificados, %d omitidos",
             enviados, omitidos)


def _telegram_alerta_techo(pedido_id: int, hotel_codigo: str, importe: float, familia_nombre: str):
    """
    Envía Telegram inmediato cuando se crea un pedido sujeto al techo de gastos.
    Se dispara en el momento del INSERT, sin esperar al job diario.
    """
    try:
        pedido = row_to_dict(query(f"{PEDIDO_SELECT_ALERTA} WHERE p.id=%s", (pedido_id,), one=True))
        if not pedido:
            return

        hotel_cod   = (hotel_codigo or pedido.get("hotel_codigo") or "").upper()
        compradores = _get_compradores_hotel(hotel_cod)
        if not compradores:
            log.warning("[TECHO] Sin compradores para hotel %s", hotel_cod)
            return

        mes_txt = _date.today().strftime("%B %Y")
        pedido_sap = pedido.get("pedido_num") or ""
        norden_val = pedido.get("norden") or ""
        ref_line   = f"📄 Pedido SAP: *{pedido_sap}*" if pedido_sap else f"📄 Línea #: *{norden_val}*"

        texto = (
            "🏦 *Nuevo pedido sujeto a techo de gastos*\n"
            f"\n"
            f"🏨 Hotel: *{pedido.get('hotel_codigo','?')}* — {pedido.get('hotel_nombre','')}\n"
            f"{ref_line}\n"
            f"📂 Familia: {familia_nombre or '—'}\n"
            f"💰 Importe: *{importe:,.2f} €*\n"
            f"📅 Mes: {mes_txt}\n"
            f"\n"
            "⚠️ Este pedido computa en el techo de gastos mensual.\n"
            "— Control Pedidos Princess Canarias"
        )

        resultados = []
        for comp in compradores:
            username = comp.get("username", "?")
            chat_id  = comp.get("telegram_chat_id")
            if chat_id:
                res = _send_telegram(chat_id, texto)
                log.info("[TECHO] Telegram → %s (%s): %s", username, chat_id, "OK" if res["ok"] else res["error"])
                resultados.append({"username": username, "chat_id": chat_id, **res})
            # ── Encolar en bridge agenda ──────────────────────────────────────
            _encolar_bridge_notificacion(
                usuario=username,
                tipo="techo",
                titulo=f"🏦 Nuevo pedido sujeto a techo · Hotel {hotel_cod}",
                mensaje=texto.replace("*", ""),
                nivel="aviso",
                pedido_id=pedido_id,
            )

        # ── Copia de supervisión a admins: creación de pedido sujeto a techo es siempre urgente ──
        _enviar_supervision_admins(
            texto, "urgente",
            titulo_bridge=f"🏦 [Supervisión] Nuevo pedido techo · Hotel {hotel_cod}",
            pedido_id_bridge=pedido_id,
        )

        # Registrar en log
        db = get_db()
        for r in resultados:
            _log_whatsapp(
                db, pedido_id, "telegram_techo",
                r.get("username", "?"),
                f"Alerta techo gastos — {importe:,.2f} € — {familia_nombre}",
                r.get("ok", False),
                r.get("error"),
            )
        db.commit()

    except Exception as exc:
        log.error("[TECHO] Error enviando telegram techo pedido %s: %s", pedido_id, exc)


def _get_proveedor_emails_principales(proveedor_id) -> list:
    """Devuelve la lista de emails de TODOS los contactos marcados como
    principales (es_principal=1) para un proveedor, en el orden definido
    por `orden`. Un proveedor puede tener varios contactos marcados a la
    vez con la estrella dorada — todos reciben las notificaciones como
    destinatario directo ("Para:"), no en copia."""
    if not proveedor_id:
        return []
    rows = query(
        """SELECT email FROM proveedor_contactos
           WHERE proveedor_id=%s AND es_principal=1
             AND email IS NOT NULL AND email != ''
           ORDER BY orden, id""",
        (proveedor_id,)
    ) or []
    return [r["email"] for r in rows]


def _get_todos_usuarios_hotel(hotel_codigo: str) -> dict:
    """
    Devuelve todos los usuarios activos asignados a un hotel, separados por rol:
      - "compradores": rol='compras' en usuario_comprador_hoteles
      - "hotel_users": rol='hotel'   en usuario_hoteles
    Cada lista contiene dicts con {id, username, nombre, email}.
    Uso: determinar destinatarios de correos internos de cambio de estado,
    incluyendo tanto el comprador responsable como el usuario del hotel.
    """
    if not hotel_codigo:
        return {"compradores": [], "hotel_users": []}
    hotel_codigo = hotel_codigo.upper()
    hotel_row = query("SELECT id FROM hoteles WHERE codigo=%s AND activo=1", (hotel_codigo,), one=True)
    if not hotel_row:
        return {"compradores": [], "hotel_users": []}
    hotel_id = hotel_row["id"]

    compradores = rows_to_list(query(
        """SELECT u.id, u.username, u.nombre, u.email
           FROM usuarios u
           JOIN usuario_comprador_hoteles uch ON uch.usuario_id = u.id
           WHERE uch.hotel_id = %s AND u.activo = 1 AND u.rol = 'compras'
             AND u.email IS NOT NULL AND TRIM(u.email) != ''
           ORDER BY u.nombre""",
        (hotel_id,)
    )) or []

    hotel_users = rows_to_list(query(
        """SELECT u.id, u.username, u.nombre, u.email
           FROM usuarios u
           JOIN usuario_hoteles uh ON uh.usuario_id = u.id
           WHERE uh.hotel_id = %s AND u.activo = 1 AND u.rol = 'hotel'
             AND u.email IS NOT NULL AND TRIM(u.email) != ''
           ORDER BY u.nombre""",
        (hotel_id,)
    )) or []

    return {"compradores": compradores, "hotel_users": hotel_users}


def _get_compradores_cc(hotel_codigo: str):
    """Devuelve lista de dicts {email, nombre, movil} de los compradores responsables del hotel.
    Usa _get_compradores_hotel() para obtener los compradores dinámicamente desde BD."""
    return _get_compradores_hotel(hotel_codigo)

# ── Plantillas de email por tipo de alerta (v9.5) ─────────────────────────────

def _email_template_enviado_proveedor(pedido: dict, dias: int, urgente: bool, comprador_email: str = "") -> tuple:
    """Pedido enviado al proveedor sin acuse de recibo tras varios días."""
    nivel = "URGENTE" if urgente else "Recordatorio"
    subject = f"[{nivel}] Seguimiento pedido Nº {pedido.get('pedido_num','—')} — Princess Hotels & Resorts"
    body = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto">
      <div style="background:#8B0000;padding:16px 24px;border-radius:6px 6px 0 0">
        <h2 style="color:#fff;margin:0;font-size:18px">Princess Hotels &amp; Resorts</h2>
        <p style="color:#f5c6c6;margin:4px 0 0;font-size:13px">Dpto. Central de Compras Princess en Canarias</p>
      </div>
      <div style="border:1px solid #e0e0e0;border-top:none;padding:24px;border-radius:0 0 6px 6px">
        <p style="background:#fff7e6;border:1px solid #f0c36d;color:#7a5b00;padding:10px 14px;border-radius:4px;font-size:12.5px;margin:0 0 18px">
          ⚠️ Este correo es exclusivo para notificaciones automáticas. Por favor, responda única y exclusivamente a la dirección que firma este comunicado.
        </p>
        <p>Estimado/a proveedor/a,</p>
        <p>Nos ponemos en contacto con usted en relación al pedido que figura a continuación,
           el cual fue tramitado hace <strong>{dias} días</strong> y aún no hemos recibido confirmación de entrega.</p>
        <p style="margin:16px 0;line-height:2;font-size:14px">
          <strong>Pedido Nº:</strong> {pedido.get('pedido_num','—')}<br>
          <strong>Hotel:</strong> {pedido.get('hotel_nombre','—')}<br>
          <strong>Departamento:</strong> {pedido.get('departamento_nombre','—')}<br>
          <strong>Estado actual:</strong> <span style="color:#8B0000">{pedido.get('estado','ENVIADO AL PROVEEDOR')}</span><br>
          <strong>Días transcurridos:</strong> <span style="color:{'#dc2626' if urgente else '#b45309'};font-weight:bold">{dias} días</span>{('<br><strong>Observaciones:</strong> ' + pedido['observaciones']) if pedido.get('observaciones') else ''}
        </p>
        <p>Le rogamos que nos confirme el estado actual del pedido y la fecha estimada de entrega
           a la mayor brevedad posible.</p>
        {'<p style="color:#dc2626;font-weight:bold;border:1px solid #fca5a5;background:#fee2e2;padding:10px;border-radius:4px">⚠️ ATENCIÓN: Esta es una solicitud urgente. Por favor, responda en el día de hoy.</p>' if urgente else ''}
        <p>Muchas gracias por su colaboración.</p>
        <hr style="border:none;border-top:1px solid #eee;margin:20px 0">
        <p style="font-size:12px;color:#666">Atentamente,<br>
           <strong>Dpto. Central de Compras Princess en Canarias</strong><br>
           Princess Hotels &amp; Resorts<br>
           <a href="mailto:{comprador_email}" style="color:#8B0000">{comprador_email}</a></p>
        <p style="font-size:11.5px;color:#8a6d00;background:#fff7e6;border:1px solid #f0c36d;padding:8px 12px;border-radius:4px;margin-top:14px">
          Este correo es exclusivo para notificaciones automáticas. Por favor, responda única y exclusivamente a la dirección que firma este comunicado.
        </p>
      </div>
    </div>
    """
    return subject, body

def _email_template_pendiente_firma(pedido: dict, dias: int, tipo: str) -> tuple:
    """Pedido pendiente de firma (dirección compras o dirección hotel)."""
    if tipo == "PENDIENTE FIRMA DIRECCION COMPRAS":
        dest_label = "Dirección de Compras"
        accion = "firma por parte de Dirección de Compras"
    else:
        dest_label = "Dirección del Hotel"
        accion = "firma por parte de la Dirección del Hotel"
    subject = f"[Recordatorio] Pedido Nº {pedido.get('pedido_num','—')} pendiente de {accion}"
    body = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto">
      <div style="background:#1a3a6b;padding:16px 24px;border-radius:6px 6px 0 0">
        <h2 style="color:#fff;margin:0;font-size:18px">Princess Hotels &amp; Resorts</h2>
        <p style="color:#a8c0e8;margin:4px 0 0;font-size:13px">Control de Pedidos — Aviso interno</p>
      </div>
      <div style="border:1px solid #e0e0e0;border-top:none;padding:24px;border-radius:0 0 6px 6px">
        <p>Se le notifica que el siguiente pedido lleva <strong>{dias} días</strong>
           pendiente de {accion}:</p>
        <table style="width:100%;border-collapse:collapse;margin:16px 0;font-size:14px">
          <tr style="background:#f5f5f5"><td style="padding:8px 12px;border:1px solid #ddd;font-weight:bold;width:40%">Pedido Nº</td>
              <td style="padding:8px 12px;border:1px solid #ddd">{pedido.get('pedido_num','—')}</td></tr>
          <tr><td style="padding:8px 12px;border:1px solid #ddd;font-weight:bold">Nº de Orden</td>
              <td style="padding:8px 12px;border:1px solid #ddd">{pedido.get('norden','—')}</td></tr>
          <tr style="background:#f5f5f5"><td style="padding:8px 12px;border:1px solid #ddd;font-weight:bold">Hotel</td>
              <td style="padding:8px 12px;border:1px solid #ddd">{pedido.get('hotel_nombre','—')}</td></tr>
          <tr><td style="padding:8px 12px;border:1px solid #ddd;font-weight:bold">Departamento</td>
              <td style="padding:8px 12px;border:1px solid #ddd">{pedido.get('departamento_nombre','—')}</td></tr>
          <tr style="background:#f5f5f5"><td style="padding:8px 12px;border:1px solid #ddd;font-weight:bold">Proveedor</td>
              <td style="padding:8px 12px;border:1px solid #ddd">{pedido.get('proveedor_nombre','—')}</td></tr>
          <tr><td style="padding:8px 12px;border:1px solid #ddd;font-weight:bold">Días en espera</td>
              <td style="padding:8px 12px;border:1px solid #ddd;color:#b45309;font-weight:bold">{dias} días</td></tr>
          {f'<tr style="background:#f5f5f5"><td style="padding:8px 12px;border:1px solid #ddd;font-weight:bold">Observaciones</td><td style="padding:8px 12px;border:1px solid #ddd">{pedido["observaciones"]}</td></tr>' if pedido.get("observaciones") else ''}
        </table>
        <p>Por favor, proceda con la revisión y firma del pedido a la mayor brevedad posible
           para no retrasar el proceso de compra.</p>
        <hr style="border:none;border-top:1px solid #eee;margin:20px 0">
        <p style="font-size:12px;color:#666">Mensaje automático generado por el sistema de Control de Pedidos.<br>
           <strong>Princess Hotels &amp; Resorts</strong></p>
      </div>
    </div>
    """
    return subject, body

def _email_template_entrega_parcial(pedido: dict, dias: int, comprador_email: str = "") -> tuple:
    """Pedido con entrega parcial sin cierre."""
    subject = f"[Seguimiento] Pedido Nº {pedido.get('pedido_num','—')} — Entrega parcial pendiente de completar"
    body = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto">
      <div style="background:#8B0000;padding:16px 24px;border-radius:6px 6px 0 0">
        <h2 style="color:#fff;margin:0;font-size:18px">Princess Hotels &amp; Resorts</h2>
        <p style="color:#f5c6c6;margin:4px 0 0;font-size:13px">Dpto. Central de Compras Princess en Canarias</p>
      </div>
      <div style="border:1px solid #e0e0e0;border-top:none;padding:24px;border-radius:0 0 6px 6px">
        <p style="background:#fff7e6;border:1px solid #f0c36d;color:#7a5b00;padding:10px 14px;border-radius:4px;font-size:12.5px;margin:0 0 18px">
          ⚠️ Este correo es exclusivo para notificaciones automáticas. Por favor, responda única y exclusivamente a la dirección que firma este comunicado.
        </p>
        <p>Estimado/a proveedor/a,</p>
        <p>Le contactamos en relación al pedido indicado, cuya entrega se registró de forma
           <strong>parcial</strong> hace <strong>{dias} días</strong> y aún está pendiente de completarse.</p>
        <p style="margin:16px 0;line-height:2;font-size:14px">
          <strong>Pedido Nº:</strong> {pedido.get('pedido_num','—')}<br>
          <strong>Hotel:</strong> {pedido.get('hotel_nombre','—')}<br>
          <strong>Departamento:</strong> {pedido.get('departamento_nombre','—')}<br>
          <strong>Estado actual:</strong> <span style="color:#8B0000">ENTREGA PARCIAL</span><br>
          <strong>Días transcurridos:</strong> <span style="color:#b45309;font-weight:bold">{dias} días</span>{('<br><strong>Observaciones:</strong> ' + pedido['observaciones']) if pedido.get('observaciones') else ''}
        </p>
        <p>Le rogamos que nos informe sobre la fecha prevista para completar la entrega pendiente.</p>
        <p>Muchas gracias.</p>
        <hr style="border:none;border-top:1px solid #eee;margin:20px 0">
        <p style="font-size:12px;color:#666">Atentamente,<br>
           <strong>Dpto. Central de Compras Princess en Canarias</strong><br>
           Princess Hotels &amp; Resorts<br>
           <a href="mailto:{comprador_email}" style="color:#8B0000">{comprador_email}</a></p>
        <p style="font-size:11.5px;color:#8a6d00;background:#fff7e6;border:1px solid #f0c36d;padding:8px 12px;border-radius:4px;margin-top:14px">
          Este correo es exclusivo para notificaciones automáticas. Por favor, responda única y exclusivamente a la dirección que firma este comunicado.
        </p>
      </div>
    </div>
    """
    return subject, body

def _email_template_pendiente_cotizacion(pedido: dict, dias: int, urgente: bool, comprador_email: str = "") -> tuple:
    """Pedido pendiente de cotización del proveedor."""
    nivel = "URGENTE" if urgente else "Solicitud de cotización"
    subject = f"[{nivel}] Cotización solicitada — {pedido.get('hotel_nombre','Princess Hotels')} — Princess Hotels & Resorts"
    body = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto">
      <div style="background:#8B0000;padding:16px 24px;border-radius:6px 6px 0 0">
        <h2 style="color:#fff;margin:0;font-size:18px">Princess Hotels &amp; Resorts</h2>
        <p style="color:#f5c6c6;margin:4px 0 0;font-size:13px">Dpto. Central de Compras Princess en Canarias</p>
      </div>
      <div style="border:1px solid #e0e0e0;border-top:none;padding:24px;border-radius:0 0 6px 6px">
        <p style="background:#fff7e6;border:1px solid #f0c36d;color:#7a5b00;padding:10px 14px;border-radius:4px;font-size:12.5px;margin:0 0 18px">
          ⚠️ Este correo es exclusivo para notificaciones automáticas. Por favor, responda única y exclusivamente a la dirección que firma este comunicado.
        </p>
        <p>Estimado/a proveedor/a,</p>
        <p>Le recordamos que hace <strong>{dias} días</strong> se le solicitó cotización
           para el siguiente pedido y aún estamos a la espera de su propuesta económica.</p>
        <p style="margin:16px 0;line-height:2;font-size:14px">
          <strong>Pedido Nº:</strong> {pedido.get('pedido_num','—')}<br>
          <strong>Hotel:</strong> {pedido.get('hotel_nombre','—')}<br>
          <strong>Departamento:</strong> {pedido.get('departamento_nombre','—')}<br>
          <strong>Estado actual:</strong> <span style="color:#8B0000">PENDIENTE COTIZACIÓN</span><br>
          <strong>Días transcurridos:</strong> <span style="color:{'#dc2626' if urgente else '#b45309'};font-weight:bold">{dias} días</span>{('<br><strong>Observaciones:</strong> ' + pedido['observaciones']) if pedido.get('observaciones') else ''}
        </p>
        {'<p style="color:#dc2626;font-weight:bold;border:1px solid #fca5a5;background:#fee2e2;padding:10px;border-radius:4px">⚠️ URGENTE: Necesitamos su cotización hoy para no retrasar la tramitación del pedido.</p>' if urgente else '<p>Le agradecemos que nos envíe su mejor oferta a la mayor brevedad posible.</p>'}
        <hr style="border:none;border-top:1px solid #eee;margin:20px 0">
        <p style="font-size:12px;color:#666">Atentamente,<br>
           <strong>Dpto. Central de Compras Princess en Canarias</strong><br>
           Princess Hotels &amp; Resorts<br>
           <a href="mailto:{comprador_email}" style="color:#8B0000">{comprador_email}</a></p>
        <p style="font-size:11.5px;color:#8a6d00;background:#fff7e6;border:1px solid #f0c36d;padding:8px 12px;border-radius:4px;margin-top:14px">
          Este correo es exclusivo para notificaciones automáticas. Por favor, responda única y exclusivamente a la dirección que firma este comunicado.
        </p>
      </div>
    </div>
    """
    return subject, body

def _build_alerta_email(pedido: dict, dias: int, nivel: str) -> tuple:
    """Selecciona la plantilla correcta según el estado del pedido y devuelve (subject, body, es_proveedor).
    Devuelve (None, None, False) si no hay comprador con email asignado al hotel."""
    estado    = pedido.get("estado", "")
    urgente   = nivel == "urgente"
    # Obtener email del comprador responsable del hotel para incluir en la firma
    _compradores = _get_compradores_cc(pedido.get("hotel_codigo",""))
    if not (_compradores and _compradores[0].get("email")):
        log.warning("[ALERTA EMAIL] Pedido %s: no hay comprador con email asignado al hotel %s — email de alerta omitido",
                    pedido.get("id"), pedido.get("hotel_codigo",""))
        return None, None, False
    _comprador_email = _compradores[0]["email"]
    if estado == "ENVIADO AL PROVEEDOR":
        s, b = _email_template_enviado_proveedor(pedido, dias, urgente, _comprador_email)
        return s, b, True
    elif estado in ("PENDIENTE FIRMA DIRECCION COMPRAS", "PENDIENTE DE FIRMA DIRECCION HOTEL"):
        s, b = _email_template_pendiente_firma(pedido, dias, estado)
        return s, b, False
    elif estado == "ENTREGA PARCIAL":
        s, b = _email_template_entrega_parcial(pedido, dias, _comprador_email)
        return s, b, True
    elif estado == "PENDIENTE COTIZACIÓN":
        s, b = _email_template_pendiente_cotizacion(pedido, dias, urgente, _comprador_email)
        return s, b, True
    return None, None, False

def _whatsapp_text(pedido: dict, dias: int, nivel: str) -> str:
    """Genera el texto de WhatsApp/Telegram (plano, sin HTML) para notificación al comprador."""
    emoji      = "🔴" if nivel == "urgente" else "🟡"
    nivel_txt  = "ALERTA URGENTE" if nivel == "urgente" else "AVISO"
    hotel_cod  = pedido.get("hotel_codigo", "—")
    hotel_nom  = pedido.get("hotel_nombre", "")
    pedido_sap = pedido.get("pedido_num") or ""
    norden     = pedido.get("norden") or ""
    proveedor  = pedido.get("proveedor_nombre") or ""
    estado     = pedido.get("estado", "—")

    lineas = [f"{emoji} *{nivel_txt}*", ""]
    lineas.append(f"🏨 Hotel: *{hotel_cod}* — {hotel_nom}")
    if pedido_sap:
        lineas.append(f"📄 Pedido SAP: *{pedido_sap}*")
    elif norden:
        lineas.append(f"📄 Línea #: *{norden}*")
    if proveedor:
        lineas.append(f"🏢 Proveedor: {proveedor}")
    lineas.append(f"📋 Estado: {estado}")
    lineas.append(f"⏳ Días transcurridos: *{dias}*")
    lineas += ["", "— Control Pedidos Princess Canarias"]
    return "\n".join(lineas)

def _log_whatsapp(db, pedido_id, tipo, destinatario, mensaje, enviado, error=None):
    with db.cursor() as cur:
        cur.execute(
            "INSERT INTO whatsapp_log (pedido_id,tipo,destinatario,mensaje,enviado,error) VALUES (%s,%s,%s,%s,%s,%s)",
            (pedido_id, tipo, destinatario, mensaje, 1 if enviado else 0, error)
        )

# ── API: preparar propuesta de email por alerta ───────────────────────────────

PEDIDO_SELECT_ALERTA = """
    SELECT p.id, p.norden, p.pedido_num, p.presupuesto_num, p.estado,
           p.fecha_tramitacion, p.fecha_solicitud, p.observaciones,
           p.proveedor_id,
           h.codigo as hotel_codigo, h.nombre as hotel_nombre,
           d.nombre as departamento_nombre,
           pr.nombre as proveedor_nombre,
           (SELECT email FROM proveedor_contactos WHERE proveedor_id=pr.id AND email IS NOT NULL AND email!='' AND es_principal=1 LIMIT 1) as proveedor_email,
           (SELECT COALESCE(NULLIF(movil,''),NULLIF(telefono,'')) FROM proveedor_contactos WHERE proveedor_id=pr.id AND es_principal=1 LIMIT 1) as proveedor_movil,
           (SELECT nombre FROM proveedor_contactos WHERE proveedor_id=pr.id AND es_principal=1 LIMIT 1) as proveedor_contacto_nombre
    FROM pedidos p
    LEFT JOIN hoteles h ON p.hotel_id = h.id
    LEFT JOIN departamentos d ON p.departamento_id = d.id
    LEFT JOIN proveedores pr ON p.proveedor_id = pr.id
"""

@app.route("/api/alertas/<int:pedido_id>/email-preview", methods=["GET"])
@login_required
def alerta_email_preview(pedido_id):
    """Devuelve la propuesta de email (destinatarios + cuerpo) para una alerta concreta."""
    dias_str = request.args.get("dias", "0")
    nivel    = request.args.get("nivel", "aviso")
    try:
        dias = int(dias_str)
    except Exception:
        dias = 0

    pedido = row_to_dict(query(f"{PEDIDO_SELECT_ALERTA} WHERE p.id=%s", (pedido_id,), one=True))
    if not pedido:
        return jsonify({"error": "Pedido no encontrado"}), 404

    subject, body_html, es_proveedor = _build_alerta_email(pedido, dias, nivel)
    if not subject:
        return jsonify({"error": "No hay plantilla para este estado"}), 400

    hotel_codigo = pedido.get("hotel_codigo", "")
    compradores  = _get_compradores_cc(hotel_codigo)

    # Destinatario principal
    if es_proveedor:
        _proveedor_emails = _get_proveedor_emails_principales(pedido.get("proveedor_id"))
        to_email   = ", ".join(_proveedor_emails)
        to_nombre  = pedido.get("proveedor_nombre") or ""
    else:
        # Email interno: comprador responsable como destinatario
        to_email  = compradores[0]["email"] if compradores else ""
        to_nombre = compradores[0]["nombre"] if compradores else ""

    cc_emails = [c["email"] for c in compradores if c.get("email") and c["email"] != to_email]

    # WhatsApp text para compradores (legacy manual)
    wa_text = _whatsapp_text(pedido, dias, nivel)
    wa_recipients = [{"nombre": c["nombre"], "movil": c.get("movil","")} for c in compradores if c.get("movil")]

    # Telegram — compradores asignados al hotel (dinámico desde BD)
    _compradores_telegram = _get_compradores_hotel(hotel_codigo.upper())
    telegram_recipients = [
        {"username": c.get("username"), "chat_id": c.get("telegram_chat_id"), "nombre": c.get("nombre", c.get("username"))}
        for c in _compradores_telegram if c.get("telegram_chat_id")
    ]

    return jsonify({
        "pedido_id":     pedido_id,
        "estado":        pedido.get("estado"),
        "hotel_codigo":  hotel_codigo,
        "hotel_nombre":  pedido.get("hotel_nombre"),
        "pedido_num":    pedido.get("pedido_num"),
        "proveedor_nombre": pedido.get("proveedor_nombre"),
        "es_proveedor":  es_proveedor,
        "to_email":      to_email,
        "to_nombre":     to_nombre,
        "cc_emails":     cc_emails,
        "compradores":   compradores,
        "subject":       subject,
        "body_html":     body_html,
        "wa_text":       wa_text,
        "wa_recipients": wa_recipients,
        "telegram_recipients": telegram_recipients,
        "dias":            dias,
        "nivel":           nivel,
    })

@app.route("/api/alertas/<int:pedido_id>/enviar-email", methods=["POST"])
@login_required
def alerta_enviar_email(pedido_id):
    """Envía el email de alerta al destinatario/s indicados y lo registra en emails_log."""
    data      = request.get_json(silent=True) or {}
    to_email  = (data.get("to_email") or "").strip()
    subject   = (data.get("subject") or "").strip()
    body_html = data.get("body_html") or ""
    body_text = data.get("body_text") or ""
    dias      = int(data.get("dias", 0))
    nivel     = data.get("nivel", "aviso")
    es_proveedor = data.get("es_proveedor", False)

    if not to_email or not subject:
        return jsonify({"error": "Faltan destinatario o asunto"}), 400

    # ── Recalcular CC en backend para no depender del frontend ────────────────
    # El frontend puede no enviar cc_emails o enviarlos incompletos.
    # Siempre recalculamos los compradores asignados al hotel del pedido.
    pedido_data = row_to_dict(query(f"{PEDIDO_SELECT_ALERTA} WHERE p.id=%s", (pedido_id,), one=True))
    if pedido_data:
        hotel_codigo = pedido_data.get("hotel_codigo", "")
        compradores_hotel = _get_compradores_cc(hotel_codigo)
        # CC = todos los compradores del hotel excepto si su email coincide con el TO principal
        cc_emails_backend = [
            c["email"] for c in compradores_hotel
            if c.get("email") and c["email"].strip() != to_email
        ]
    else:
        cc_emails_backend = []

    # Combinar con cualquier CC extra que venga del frontend (sin duplicados)
    cc_frontend = [e.strip() for e in (data.get("cc_emails") or []) if e.strip()]
    cc_emails = list(dict.fromkeys(cc_emails_backend + [e for e in cc_frontend if e not in cc_emails_backend]))

    log.info("Alerta email pedido %s → TO: %s | CC/BCC: %s", pedido_id, to_email, cc_emails)

    db = get_db()
    resultados = []

    # Registro en log — el envío real lo hace el frontend vía EmailJS
    tipo_log = "alerta_proveedor" if es_proveedor else "alerta_interno"
    _log_email(db, pedido_id, tipo_log, to_email, subject, False, "Pendiente de envío vía EmailJS")
    resultados.append({"email": to_email, "ok": True, "error": None, "mode": "emailjs_pending"})

    # ── Telegram automático — se dispara siempre al enviar la alerta ──────────
    # pedido_data ya fue cargado arriba para calcular los CC
    if not pedido_data:
        pedido_data = row_to_dict(query(f"{PEDIDO_SELECT_ALERTA} WHERE p.id=%s", (pedido_id,), one=True))
    telegram_resultados = []
    if pedido_data:
        telegram_resultados = _enviar_telegram_compradores(pedido_data, dias, nivel)
        for tr in telegram_resultados:
            _log_whatsapp(db, pedido_id, "telegram_auto",
                          tr.get("username", "?"),
                          f"Alerta {nivel} — {pedido_data.get('hotel_codigo')} · Pedido {pedido_data.get('pedido_num')}",
                          tr["ok"], tr.get("error"))

    db.commit()
    todos_ok = all(r["ok"] for r in resultados)
    primer_error = next((r["error"] for r in resultados if not r["ok"]), None)
    return jsonify({
        "ok": todos_ok,
        "resultados": resultados,
        "error": primer_error,
        "telegram": telegram_resultados,
        # Datos para que el frontend envíe vía EmailJS
        "email_pendiente": {
            "to_email":  to_email,
            "cc_emails": cc_emails,
            "subject":   subject,
            "body_html": body_html,
            "body_text": body_text,
        },
    })

@app.route("/api/alertas/<int:pedido_id>/log-whatsapp", methods=["POST"])
@login_required
def alerta_log_whatsapp(pedido_id):
    """Registra en BD que se inició un envío de WhatsApp (el envío real es client-side via wa.me)."""
    data         = request.get_json(silent=True) or {}
    destinatario = (data.get("destinatario") or "").strip()
    mensaje      = (data.get("mensaje") or "").strip()
    if not destinatario:
        return jsonify({"error": "Destinatario requerido"}), 400
    db = get_db()
    _log_whatsapp(db, pedido_id, "alerta_comprador", destinatario, mensaje, True)
    db.commit()
    return jsonify({"ok": True})


@app.route("/api/alertas/<int:pedido_id>/enviar-telegram", methods=["POST"])
@login_required
def alerta_enviar_telegram(pedido_id):
    """Envía alerta automática por Telegram a los compradores del hotel."""
    data  = request.get_json(silent=True) or {}
    dias  = int(data.get("dias", 0))
    nivel = data.get("nivel", "aviso")

    pedido = row_to_dict(query(f"{PEDIDO_SELECT_ALERTA} WHERE p.id=%s", (pedido_id,), one=True))
    if not pedido:
        return jsonify({"error": "Pedido no encontrado"}), 404

    resultados = _enviar_telegram_compradores(pedido, dias, nivel)

    db = get_db()
    for tr in resultados:
        _log_whatsapp(db, pedido_id, "telegram_auto",
                      tr.get("username", "?"),
                      f"Alerta {nivel} — {pedido.get('hotel_codigo')} · Pedido {pedido.get('pedido_num')}",
                      tr["ok"], tr.get("error"))
    db.commit()

    todos_ok = all(r["ok"] for r in resultados)
    return jsonify({"ok": todos_ok, "resultados": resultados})



def _next_norden(db):
    year = datetime.now().year
    with db.cursor() as cur:
        cur.execute(
            "SELECT COALESCE(MAX(norden), 0) as mx FROM pedidos WHERE EXTRACT(YEAR FROM creado_en) = %s",
            (year,)
        )
        row = cur.fetchone()
    return (row["mx"] or 0) + 1

# ── Rutas estáticas ────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory("templates", "index.html")

@app.route("/api/version")
def app_version():
    """
    Devuelve un hash MD5 del contenido real de index.html.
    Cualquier cambio en el archivo, por pequeño que sea, produce un hash diferente.
    """
    try:
        tpl_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "index.html")
        with open(tpl_path, "rb") as f:
            version_hash = hashlib.md5(f.read()).hexdigest()[:12]
    except Exception:
        version_hash = "unknown"
    return jsonify({"version": version_hash})

@app.route("/api/changelog")
def app_changelog():
    """
    Devuelve el contenido del archivo CHANGELOG.md para mostrarlo en el modal
    de nueva versión detectada en el cliente.
    """
    try:
        changelog_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "CHANGELOG.md")
        with open(changelog_path, "r", encoding="utf-8") as f:
            contenido = f.read()
    except FileNotFoundError:
        contenido = "_No hay notas de versión disponibles._"
    except Exception as e:
        contenido = f"_Error al leer el changelog: {e}_"
    return jsonify({"changelog": contenido})

@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory("static", filename)

# ── API Auth ───────────────────────────────────────────────────────────────────

@app.route("/api/login", methods=["POST"])
def login():
    body     = request.get_json(silent=True) or {}
    username = body.get("username", "").strip().lower()
    password = body.get("password", "").strip()

    user = query(
        "SELECT * FROM usuarios WHERE username=%s AND password=%s AND activo=1",
        (username, password), one=True
    )
    if not user:
        return jsonify({"error": "Usuario o contraseña incorrectos"}), 401

    session.clear()
    session["user_id"]  = user["id"]
    session["username"] = user["username"]
    session["nombre"]   = user["nombre"]
    session["rol"]      = user["rol"]
    # Para usuario hotel: cargar sus hoteles asignados
    hoteles_ids = []
    if user["rol"] == "hotel":
        rows = query("SELECT hotel_id FROM usuario_hoteles WHERE usuario_id=%s", (user["id"],))
        hoteles_ids = [r["hotel_id"] for r in rows]
    session["hoteles_ids"] = hoteles_ids
    return jsonify({"ok": True, "id": user["id"], "username": user["username"],
                    "nombre": user["nombre"], "rol": user["rol"], "hoteles_ids": hoteles_ids})

@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True})

# ── Restablecimiento de contraseña ────────────────────────────────────────────

@app.route("/api/password-reset/solicitar", methods=["POST"])
def solicitar_reset_password():
    """El usuario introduce su username o email y recibe un enlace de reset."""
    body    = request.get_json(silent=True) or {}
    usuario = (body.get("usuario") or "").strip().lower()
    if not usuario:
        return jsonify({"error": "Indica tu usuario o email"}), 400

    user = query(
        "SELECT * FROM usuarios WHERE (username=%s OR email=%s) AND activo=1",
        (usuario, usuario), one=True
    )
    # Siempre respuesta OK para no revelar si el usuario existe
    if not user or not user.get("email"):
        return jsonify({"ok": True, "msg": "Si el usuario existe, recibirás un correo."})

    # Generar token seguro con 2 h de validez
    token    = secrets.token_urlsafe(32)
    expira   = datetime.utcnow() + timedelta(hours=2)
    db       = get_db()
    # Invalidar tokens anteriores del mismo usuario
    execute("UPDATE password_reset_tokens SET usado=1 WHERE usuario_id=%s AND usado=0", (user["id"],))
    execute(
        "INSERT INTO password_reset_tokens (usuario_id, token, expira_en) VALUES (%s,%s,%s)",
        (user["id"], token, expira)
    )
    db.commit()

    # Construir enlace (se puede configurar la URL base con env var APP_URL)
    app_url  = os.environ.get("APP_URL", request.host_url.rstrip("/"))
    link     = f"{app_url}/?reset_token={token}"

    subject  = "Restablecimiento de contraseña – Control de Pedidos"
    body_html = f"""
    <p>Hola <strong>{user['nombre']}</strong>,</p>
    <p>Hemos recibido una solicitud para restablecer tu contraseña.</p>
    <p><a href="{link}" style="background:#8B0000;color:#fff;padding:10px 20px;
       border-radius:4px;text-decoration:none;display:inline-block;">
       Restablecer contraseña</a></p>
    <p>Este enlace es válido durante <strong>2 horas</strong>.<br>
    Si no lo solicitaste, ignora este mensaje.</p>
    <p style="color:#666;font-size:12px;">Control de Pedidos · Princess Canarias</p>
    """
    # Siempre loguear el enlace en el servidor
    log.info("PASSWORD RESET solicitado por '%s' (id=%s) — enlace: %s",
             user["username"], user["id"], link)

    # El envío real lo hace el frontend vía EmailJS
    log.info("PASSWORD RESET — datos pendientes de envío vía EmailJS a '%s' (%s)", user["username"], user.get("email"))
    return jsonify({
        "ok":        True,
        "sin_email": True,
        "link":      link,
        "email":     user.get("email", ""),
        "nombre":    user.get("nombre", user.get("username", "")),
        "subject":   subject,
        "body_html": body_html,
        "msg":       "Email pendiente de envío vía EmailJS.",
    })


@app.route("/api/password-reset/validar/<token>", methods=["GET"])
def validar_reset_token(token):
    """Comprueba si el token es válido y no ha caducado."""
    row = query(
        """SELECT prt.*, u.nombre FROM password_reset_tokens prt
           JOIN usuarios u ON u.id = prt.usuario_id
           WHERE prt.token=%s AND prt.usado=0 AND prt.expira_en > NOW()""",
        (token,), one=True
    )
    if not row:
        return jsonify({"valido": False, "error": "El enlace no es válido o ha caducado"}), 400
    return jsonify({"valido": True, "nombre": row["nombre"]})


@app.route("/api/password-reset/cambiar", methods=["POST"])
def cambiar_password_con_token():
    """El usuario envía el token + nueva contraseña elegida por él."""
    body     = request.get_json(silent=True) or {}
    token    = (body.get("token") or "").strip()
    nueva    = (body.get("nueva_password") or "").strip()
    if not token or not nueva:
        return jsonify({"error": "Datos incompletos"}), 400
    if len(nueva) < 6:
        return jsonify({"error": "La contraseña debe tener al menos 6 caracteres"}), 400

    row = query(
        "SELECT * FROM password_reset_tokens WHERE token=%s AND usado=0 AND expira_en > NOW()",
        (token,), one=True
    )
    if not row:
        return jsonify({"error": "El enlace no es válido o ha caducado"}), 400

    db = get_db()
    execute("UPDATE usuarios SET password=%s WHERE id=%s", (nueva, row["usuario_id"]))
    execute("UPDATE password_reset_tokens SET usado=1 WHERE token=%s", (token,))
    db.commit()
    return jsonify({"ok": True, "msg": "Contraseña actualizada correctamente"})

# ══════════════════════════════════════════════════════════════════════════════
#  SOLICITUD DE ACCESO EN 2 FASES (v10.5)
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/solicitar-usuario/detectar-windows", methods=["GET"])
def detectar_usuario_windows():
    """
    Intenta detectar el usuario Windows del cliente.
    En entornos web públicos siempre devuelve None;
    útil solo en intranet con autenticación Windows integrada (NTLM/Kerberos).
    """
    import os as _os
    usuario = _os.environ.get("USERNAME") or _os.environ.get("USER") or ""
    if usuario and usuario not in ("root", "www-data", "nobody", "daemon"):
        return jsonify({"usuario_windows": usuario})
    return jsonify({"usuario_windows": None})


# ─── FASE 1: recibir datos básicos, guardar en BD, notificar admin ────────────

@app.route("/api/solicitar-usuario", methods=["POST"])
def solicitar_usuario_fase1():
    """
    FASE 1 — El usuario rellena nombre, apellidos, email y hotel(es).
    Se guarda la solicitud con estado 'fase1_pendiente' y se notifica
    a los admins. No se requiere usuario Windows todavía.
    """
    import re as _re

    body      = request.get_json(silent=True) or {}
    nombre    = (body.get("nombre") or "").strip()
    apellidos = (body.get("apellidos") or "").strip()
    email_sol = (body.get("email") or "").strip()
    movil_sol = (body.get("movil") or "").strip()
    hoteles   = (body.get("hoteles") or body.get("hotel") or "").strip()

    if not nombre:
        return jsonify({"error": "El nombre es obligatorio"}), 400
    if not apellidos:
        return jsonify({"error": "Los apellidos son obligatorios"}), 400
    if not email_sol:
        return jsonify({"error": "El correo electrónico es obligatorio"}), 400
    if not _re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email_sol):
        return jsonify({"error": "El formato del correo electrónico no es válido"}), 400
    if not movil_sol:
        return jsonify({"error": "El teléfono móvil de empresa es obligatorio"}), 400
    if not hoteles:
        return jsonify({"error": "Debes seleccionar al menos un hotel"}), 400

    nombre_completo = f"{nombre} {apellidos}"
    ip_cliente = request.remote_addr or ""

    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
            INSERT INTO solicitudes_acceso
                (nombre, apellidos, email, hoteles, movil, estado, ip_solicitante)
            VALUES (%s, %s, %s, %s, %s, 'fase1_pendiente', %s)
            RETURNING id
        """, (nombre, apellidos, email_sol, hoteles, movil_sol, ip_cliente))
        sol_id = cur.fetchone()["id"]
    db.commit()

    app_url   = os.environ.get("APP_URL", "").rstrip("/")
    url_admin = f"{app_url}/admin/solicitudes#{sol_id}" if app_url else ""
    asunto    = f"[FASE 1] Nueva solicitud de acceso — {nombre_completo}"

    body_html = f"""
    <div style="font-family:sans-serif;max-width:620px;margin:0 auto;
                background:#f9f9f9;border-radius:10px;overflow:hidden;
                border:1px solid #e0e0e0;">
      <div style="background:#0f2044;padding:24px 28px;">
        <h2 style="margin:0;color:#c9a84c;font-size:18px;">
          📋 Nueva solicitud de acceso — Fase 1
        </h2>
        <p style="margin:6px 0 0;color:rgba(255,255,255,.6);font-size:13px;">
          Control de Pedidos · Princess Canarias
        </p>
      </div>
      <div style="padding:24px 28px;">
        <p style="margin:0 0 16px;font-size:14px;color:#333;">
          Se ha recibido una nueva solicitud. El usuario
          <strong>aún no ha verificado su usuario Windows</strong>.
          Revisad los datos y, si son correctos, usad el panel de administración
          para enviarle el archivo de verificación (Fase 2).
        </p>
        <table border="0" cellpadding="0" cellspacing="0"
               style="width:100%;font-size:14px;border-collapse:collapse;">
          <tr style="border-bottom:1px solid #eee;">
            <td style="padding:10px 0;color:#888;width:160px;">Nombre completo</td>
            <td style="padding:10px 0;font-weight:600;">{nombre_completo}</td>
          </tr>
          <tr style="border-bottom:1px solid #eee;">
            <td style="padding:10px 0;color:#888;">Correo electrónico</td>
            <td style="padding:10px 0;">
              <a href="mailto:{email_sol}" style="color:#0f2044;">{email_sol}</a>
            </td>
          </tr>
          <tr style="border-bottom:1px solid #eee;">
            <td style="padding:10px 0;color:#888;">Móvil empresa</td>
            <td style="padding:10px 0;">{movil_sol}</td>
          </tr>
          <tr style="border-bottom:1px solid #eee;">
            <td style="padding:10px 0;color:#888;">Hotel(es)</td>
            <td style="padding:10px 0;">{hoteles}</td>
          </tr>
          <tr>
            <td style="padding:10px 0;color:#888;">ID solicitud</td>
            <td style="padding:10px 0;font-family:monospace;">#{sol_id}</td>
          </tr>
        </table>
        {f'<div style="margin-top:24px;text-align:center;"><a href="{url_admin}" style="display:inline-block;padding:12px 28px;background:#c9a84c;color:#0f2044;border-radius:7px;text-decoration:none;font-weight:700;font-size:14px;">➜ Ver solicitud y enviar Fase 2</a></div>' if url_admin else ''}
      </div>
      <div style="padding:14px 28px;background:#f0f0f0;font-size:11px;color:#aaa;">
        Mensaje automático · Control Pedidos Princess Canarias
      </div>
    </div>
    """

    body_text = (
        f"NUEVA SOLICITUD DE ACCESO (FASE 1)\n"
        f"{'='*44}\n"
        f"Nombre        : {nombre_completo}\n"
        f"Email         : {email_sol}\n"
        f"Móvil empresa : {movil_sol}\n"
        f"Hotel(es)     : {hoteles}\n"
        f"ID solicitud  : #{sol_id}\n"
        f"{'='*44}\n"
        f"Accede al panel de administración para revisar y enviar el archivo de verificación (Fase 2)."
    )

    destinatarios = _get_solo_admin_emails()

    if not destinatarios:
        log.warning("[SOL_FASE1] Sin emails admin. Sol #%s", sol_id)
        return jsonify({"ok": True, "sol_id": sol_id,
                        "msg": "Solicitud registrada (sin email de admin configurado)"})

    # Telegram SIEMPRE, antes de devolver la respuesta al frontend
    _notify_solicitud_telegram(
        f"\U0001F514 *[FASE 1] Nueva solicitud de acceso*\n\n"
        f"\U0001F464 *{nombre} {apellidos}*\n"
        f"\U0001F4E7 {email_sol}\n"
        f"\U0001F3E8 {hoteles}\n"
        f"\U0001F4CB Solicitud `#{sol_id}`\n\n"
        f"Accede al panel para enviarle el archivo de verificaci\u00f3n (Fase 2)."
        + (f"\n\U0001F517 {url_admin}" if url_admin else "")
    )

    # Email via EmailJS en el frontend (sin_email=True siempre)
    return jsonify({
        "ok": True, "sol_id": sol_id, "sin_email": True,
        "destinatarios": destinatarios,
        "asunto": asunto, "body_text": body_text,
        "reply_to": email_sol,
    })


# ─── ADMIN: listar solicitudes de acceso ──────────────────────────────────────

@app.route("/api/admin/solicitudes-acceso", methods=["GET"])
def admin_listar_solicitudes():
    """Devuelve todas las solicitudes de acceso (solo admins)."""
    if session.get("rol") != "admin":
        return jsonify({"error": "Sin permisos"}), 403
    rows = query("""
        SELECT id, nombre, apellidos, email, hoteles, usuario_windows,
               estado, creado_en, completado_en
        FROM solicitudes_acceso
        ORDER BY creado_en DESC
        LIMIT 200
    """)
    return jsonify(rows)


# ─── ADMIN: generar y descargar el .bat para Fase 2 ──────────────────────────

@app.route("/api/admin/solicitudes-acceso/<int:sol_id>/generar-bat", methods=["POST", "GET"])
def admin_generar_bat(sol_id):
    """
    Genera un token único, actualiza estado a 'fase2_pendiente' y devuelve
    un archivo .bat. Al ejecutarlo, Windows resuelve %USERNAME% y abre el
    navegador con token + usuario ya detectado automáticamente.
    """
    if session.get("rol") != "admin":
        return jsonify({"error": "Sin permisos"}), 403

    sol = query("SELECT * FROM solicitudes_acceso WHERE id=%s", (sol_id,), one=True)
    if not sol:
        return jsonify({"error": "Solicitud no encontrada"}), 404
    if sol["estado"] not in ("fase1_pendiente",):
        return jsonify({"error": f"La solicitud ya está en estado '{sol['estado']}'"}), 409

    import secrets as _sec
    token     = _sec.token_urlsafe(32)
    expira_en = datetime.utcnow() + timedelta(hours=72)

    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
            UPDATE solicitudes_acceso
            SET token=%(token)s, token_expira=%(expira)s, estado='fase2_pendiente'
            WHERE id=%(id)s
        """, {"token": token, "expira": expira_en, "id": sol_id})
    db.commit()

    app_url  = os.environ.get("APP_URL", "https://control-pedidos-princess.onrender.com").rstrip("/")
    nombre_c = f"{sol['nombre']} {sol['apellidos']}"

    # %USERNAME% la resuelve Windows al ejecutar el .bat — clave del truco
    bat_content = (
        f"@echo off\r\n"
        f":: Control de Pedidos Princess - Verificacion de acceso\r\n"
        f":: Solicitud de: {nombre_c}\r\n"
        f":: Archivo de un solo uso - expira en 72 horas\r\n"
        f"::\r\n"
        f":: Instrucciones: haz doble clic en este archivo.\r\n"
        f":: Se abrira el navegador con tu usuario Windows detectado automaticamente.\r\n"
        f"@echo Abriendo verificacion de acceso, por favor espera...\r\n"
        f"set TOKEN={token}\r\n"
        f"set URL={app_url}/?token=%TOKEN%^&wu=%USERNAME%\r\n"
        f"start \"\" \"%URL%\"\r\n"
        f"exit\r\n"
    )

    from flask import Response
    nombre_archivo = (
        f"verificar_acceso_"
        f"{sol['nombre'].lower().replace(' ','_')}_"
        f"{sol['apellidos'].split()[0].lower()}.bat"
    )
    return Response(
        bat_content,
        mimetype="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{nombre_archivo}"'}
    )


# ─── ADMIN: enviar Fase 2 por email al usuario ────────────────────────────────

@app.route("/api/admin/solicitudes-acceso/<int:sol_id>/enviar-fase2", methods=["POST"])
def admin_enviar_fase2(sol_id):
    """
    Genera el token si no existe, y envía al usuario un email con
    instrucciones + enlace para completar la Fase 2.
    """
    if session.get("rol") != "admin":
        return jsonify({"error": "Sin permisos"}), 403

    sol = query("SELECT * FROM solicitudes_acceso WHERE id=%s", (sol_id,), one=True)
    if not sol:
        return jsonify({"error": "Solicitud no encontrada"}), 404

    # Generar token si no tiene aún
    if not sol["token"]:
        import secrets as _sec
        token     = _sec.token_urlsafe(32)
        expira_en = datetime.utcnow() + timedelta(hours=72)
        db = get_db()
        with db.cursor() as cur:
            cur.execute("""
                UPDATE solicitudes_acceso
                SET token=%(t)s, token_expira=%(e)s, estado='fase2_pendiente'
                WHERE id=%(id)s
            """, {"t": token, "e": expira_en, "id": sol_id})
        db.commit()
        sol = query("SELECT * FROM solicitudes_acceso WHERE id=%s", (sol_id,), one=True)

    app_url   = os.environ.get("APP_URL", "https://control-pedidos-princess.onrender.com").rstrip("/")
    url_token = f"{app_url}/?token={sol['token']}"
    nombre_c  = f"{sol['nombre']} {sol['apellidos']}"
    asunto    = "Verificación de acceso — Control de Pedidos Princess (Fase 2)"

    body_html = f"""
    <div style="font-family:sans-serif;max-width:620px;margin:0 auto;
                background:#f9f9f9;border-radius:10px;overflow:hidden;
                border:1px solid #e0e0e0;">
      <div style="background:#0f2044;padding:24px 28px;">
        <h2 style="margin:0;color:#c9a84c;font-size:18px;">🔐 Verifica tu acceso al sistema</h2>
        <p style="margin:6px 0 0;color:rgba(255,255,255,.6);font-size:13px;">
          Control de Pedidos · Princess Canarias
        </p>
      </div>
      <div style="padding:28px;">
        <p style="margin:0 0 12px;font-size:15px;color:#333;">
          Hola, <strong>{nombre_c}</strong>
        </p>
        <p style="margin:0 0 20px;font-size:14px;color:#555;line-height:1.6;">
          Tu solicitud de acceso ha sido revisada. Para completar el proceso
          necesitamos verificar tu usuario de Windows. Tienes <strong>dos opciones</strong>:
        </p>
        <div style="background:#fff;border:2px solid #c9a84c;border-radius:8px;
                    padding:18px 20px;margin-bottom:16px;">
          <p style="margin:0 0 8px;font-weight:700;color:#0f2044;font-size:14px;">
            ✅ Opción recomendada — Archivo de verificación
          </p>
          <p style="margin:0 0 10px;font-size:13px;color:#555;line-height:1.5;">
            Adjunto a este email encontrarás el archivo <strong>verificar_acceso.bat</strong>:
          </p>
          <ol style="margin:0 0 0 18px;font-size:13px;color:#555;line-height:1.9;">
            <li>Guarda el archivo adjunto en tu escritorio.</li>
            <li>Haz <strong>doble clic</strong> sobre él.</li>
            <li>Se abrirá el navegador con tu usuario Windows ya detectado.</li>
            <li>Pulsa <em>Completar verificación</em>.</li>
          </ol>
        </div>
        <div style="background:#fff;border:1px solid #ddd;border-radius:8px;
                    padding:18px 20px;margin-bottom:24px;">
          <p style="margin:0 0 8px;font-weight:700;color:#0f2044;font-size:14px;">
            🔗 Opción alternativa — Enlace directo
          </p>
          <p style="margin:0 0 12px;font-size:13px;color:#555;">
            Si no puedes ejecutar el archivo, usa este enlace e introduce
            tu usuario Windows manualmente.
          </p>
          <div style="text-align:center;">
            <a href="{url_token}"
               style="display:inline-block;padding:11px 24px;background:#1a3a6b;
                      color:#fff;border-radius:7px;text-decoration:none;
                      font-weight:600;font-size:13px;">Continuar verificación →</a>
          </div>
        </div>
        <p style="margin:0;font-size:12px;color:#aaa;line-height:1.5;">
          Enlace personal e intransferible. Caduca en <strong>72 horas</strong>.
          Si tienes problemas contacta con el departamento de informática.
        </p>
      </div>
      <div style="padding:14px 28px;background:#f0f0f0;font-size:11px;color:#aaa;">
        Mensaje automático · Control Pedidos Princess Canarias
      </div>
    </div>
    """

    body_text = (
        f"Hola {nombre_c},\n\n"
        f"Tu solicitud de acceso ha sido revisada. Para completarla, ejecuta\n"
        f"el archivo .bat adjunto (haz doble clic) o abre este enlace:\n\n"
        f"{url_token}\n\n"
        f"El enlace caduca en 72 horas.\n\nControl Pedidos Princess Canarias"
    )

    # El envío real lo hace el frontend vía EmailJS
    log.info("[SOL_FASE2] Email pendiente de envío vía EmailJS a %s", sol["email"])
    return jsonify({
        "ok":           True,
        "sin_email":    True,
        "destinatarios": [sol["email"]],
        "asunto":       asunto,
        "body_html":    body_html,
        "body_text":    body_text,
        "url_token":    url_token,
    })


# ─── FASE 2: el usuario llega con token + wu, completa la solicitud ───────────

@app.route("/api/solicitar-usuario/completar-fase2", methods=["POST"])
def solicitar_usuario_fase2():
    """
    FASE 2 — El usuario ejecutó el .bat o abrió el enlace.
    Valida token + usuario_windows, marca como completada y notifica admins.
    """
    import re as _re

    body            = request.get_json(silent=True) or {}
    token           = (body.get("token") or "").strip()
    usuario_windows = (body.get("usuario_windows") or "").strip().upper()

    if not token:
        return jsonify({"error": "Token no proporcionado"}), 400
    if not usuario_windows:
        return jsonify({"error": "El usuario Windows es obligatorio"}), 400

    sol = query("SELECT * FROM solicitudes_acceso WHERE token=%s", (token,), one=True)
    if not sol:
        return jsonify({"error": "Enlace no válido o ya utilizado"}), 404

    if sol["token_expira"]:
        expira = sol["token_expira"]
        if hasattr(expira, "tzinfo") and expira.tzinfo:
            from datetime import timezone
            now = datetime.now(timezone.utc)
        else:
            now = datetime.utcnow()
        if now > expira:
            return jsonify({
                "error": "Este enlace ha caducado (72 horas). "
                         "Contacta con el administrador para generar uno nuevo."
            }), 410

    if sol["estado"] == "completada":
        return jsonify({"error": "Esta solicitud ya fue completada anteriormente."}), 409

    usuario_existente = query(
        "SELECT id, activo FROM usuarios WHERE LOWER(username)=LOWER(%s)",
        (usuario_windows,), one=True
    )
    if usuario_existente:
        if usuario_existente["activo"]:
            return jsonify({
                "error": f"El usuario Windows '{usuario_windows}' ya tiene una cuenta activa en el sistema. "
                         f"Puedes iniciar sesión directamente o recuperar tu contraseña si la olvidaste.",
                "ya_existe": True
            }), 409
        else:
            return jsonify({
                "error": f"El usuario Windows '{usuario_windows}' existe en el sistema pero está desactivado. "
                         f"Contacta con el administrador para reactivar tu cuenta.",
                "ya_existe": True,
                "desactivado": True
            }), 409

    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
            UPDATE solicitudes_acceso
            SET usuario_windows=%(uw)s, estado='completada',
                completado_en=NOW(), token=NULL
            WHERE id=%(id)s
        """, {"uw": usuario_windows, "id": sol["id"]})
    db.commit()

    nombre_c = f"{sol['nombre']} {sol['apellidos']}"
    asunto   = f"[FASE 2 COMPLETADA] Alta usuario — {nombre_c} / {usuario_windows}"

    body_html = f"""
    <div style="font-family:sans-serif;max-width:620px;margin:0 auto;
                background:#f9f9f9;border-radius:10px;overflow:hidden;
                border:1px solid #e0e0e0;">
      <div style="background:#065f46;padding:24px 28px;">
        <h2 style="margin:0;color:#6ee7b7;font-size:18px;">
          ✅ Solicitud completa — Crear cuenta de usuario
        </h2>
        <p style="margin:6px 0 0;color:rgba(255,255,255,.6);font-size:13px;">
          Control de Pedidos · Princess Canarias
        </p>
      </div>
      <div style="padding:24px 28px;">
        <p style="margin:0 0 16px;font-size:14px;color:#333;">
          El usuario ha completado la verificación.
          <strong>Ya podéis crear la cuenta</strong> con los siguientes datos:
        </p>
        <table border="0" cellpadding="0" cellspacing="0"
               style="width:100%;font-size:14px;border-collapse:collapse;">
          <tr style="background:#f0fdf4;border-bottom:1px solid #d1fae5;">
            <td style="padding:12px 14px;color:#065f46;font-weight:700;width:170px;">Usuario Windows</td>
            <td style="padding:12px 14px;font-family:monospace;font-size:16px;font-weight:700;color:#0f2044;">
              {usuario_windows}
            </td>
          </tr>
          <tr style="border-bottom:1px solid #eee;">
            <td style="padding:10px 14px;color:#888;">Nombre completo</td>
            <td style="padding:10px 14px;font-weight:600;">{nombre_c}</td>
          </tr>
          <tr style="border-bottom:1px solid #eee;">
            <td style="padding:10px 14px;color:#888;">Correo electrónico</td>
            <td style="padding:10px 14px;">
              <a href="mailto:{sol['email']}" style="color:#0f2044;">{sol['email']}</a>
            </td>
          </tr>
          <tr style="border-bottom:1px solid #eee;">
            <td style="padding:10px 14px;color:#888;">Hotel(es)</td>
            <td style="padding:10px 14px;">{sol['hoteles']}</td>
          </tr>
          <tr>
            <td style="padding:10px 14px;color:#888;">ID solicitud</td>
            <td style="padding:10px 14px;font-family:monospace;">#{sol['id']}</td>
          </tr>
        </table>
      </div>
      <div style="padding:14px 28px;background:#f0f0f0;font-size:11px;color:#aaa;">
        Mensaje automático · Control Pedidos Princess Canarias
      </div>
    </div>
    """

    body_text = (
        f"SOLICITUD COMPLETADA — CREAR CUENTA\n"
        f"{'='*44}\n"
        f"Usuario Windows : {usuario_windows}\n"
        f"Nombre          : {nombre_c}\n"
        f"Email           : {sol['email']}\n"
        f"Hotel(es)       : {sol['hoteles']}\n"
        f"ID solicitud    : #{sol['id']}\n"
        f"{'='*44}\n"
        f"Crea la cuenta en el sistema con los datos anteriores."
    )

    destinatarios = _get_solo_admin_emails()
    app_url       = os.environ.get("APP_URL", "").rstrip("/")
    url_admin     = f"{app_url}/admin/solicitudes#{sol['id']}" if app_url else ""

    if not destinatarios:
        log.warning("[SOL_FASE2] Sin emails admin. Sol #%s", sol["id"])
        return jsonify({"ok": True,
                        "msg": "¡Verificación completada! Los administradores podrán verla en el panel."})

    # Telegram SIEMPRE, antes de devolver la respuesta al frontend
    _notify_solicitud_telegram(
        f"\u2705 *[FASE 2 COMPLETADA] Alta pendiente de aprobar*\n\n"
        f"\U0001F464 *{nombre_c}*\n"
        f"\U0001F5A5 Usuario Windows: `{usuario_windows}`\n"
        f"\U0001F4E7 {sol['email']}\n"
        f"\U0001F3E8 {sol['hoteles']}\n"
        f"\U0001F4CB Solicitud `#{sol['id']}` — lista para aprobar."
        + (f"\n\U0001F517 {url_admin}" if url_admin else "")
    )

    # Email via EmailJS en el frontend (sin_email=True siempre)
    return jsonify({
        "ok":            True,
        "sin_email":     True,
        "destinatarios": destinatarios,
        "asunto":        asunto,
        "body_text":     body_text,
        "url_admin":     url_admin,
        "reply_to":      sol["email"],
        "msg": "¡Verificación completada! Los administradores han recibido todos los datos para crear tu cuenta."
    })


# ─── ADMIN: aprobar solicitud → crear cuenta automáticamente ─────────────────

@app.route("/api/admin/solicitudes-acceso/<int:sol_id>/aprobar", methods=["POST"])
def admin_aprobar_solicitud(sol_id):
    """
    Aprueba una solicitud en estado 'completada':
      1. Crea el usuario con usuario_windows como username.
      2. Asigna los hoteles por nombre (mapeo nombre → id).
      3. Genera contraseña temporal.
      4. Envía email de bienvenida al solicitante con sus credenciales.
      5. Marca la solicitud como 'aprobada'.
    """
    if session.get("rol") != "admin":
        return jsonify({"error": "Sin permisos"}), 403

    sol = query("SELECT * FROM solicitudes_acceso WHERE id=%s", (sol_id,), one=True)
    if not sol:
        return jsonify({"error": "Solicitud no encontrada"}), 404
    if sol["estado"] != "completada":
        return jsonify({"error": f"La solicitud está en estado '{sol['estado']}', debe estar 'completada' para aprobarla"}), 409

    username = (sol["usuario_windows"] or "").strip().lower()
    if not username:
        return jsonify({"error": "No hay usuario Windows registrado en esta solicitud"}), 400

    # Comprobar que el username no existe ya
    existing = query("SELECT id FROM usuarios WHERE username=%s", (username,), one=True)
    if existing:
        return jsonify({"error": f"Ya existe un usuario con el username '{username}'"}), 409

    # Generar contraseña temporal legible: Princess + 4 dígitos
    import random as _rnd
    password_temp = "Princess" + str(_rnd.randint(1000, 9999))

    nombre_c = f"{sol['nombre']} {sol['apellidos']}"
    db = get_db()

    # Crear usuario (v11.6.7: se incluye movil de la solicitud y rol 'compras' por defecto)
    cur = execute(
        "INSERT INTO usuarios (username, nombre, email, password, movil, rol, activo) VALUES (%s,%s,%s,%s,%s,'compras',1) RETURNING id",
        (username, nombre_c, sol["email"], password_temp, sol.get("movil") or None)
    )
    new_uid = cur.fetchone()["id"]

    # Mapear hoteles texto → IDs (comparación flexible, ignorando mayúsculas y & vs and)
    def _normalizar(s):
        return s.lower().replace("&", "and").replace("  ", " ").strip()

    todos_hoteles = rows_to_list(query("SELECT id, nombre FROM hoteles WHERE activo=1"))
    hoteles_texto = [h.strip() for h in (sol["hoteles"] or "").split(",")]
    hotel_ids_asignados = []
    hoteles_no_encontrados = []
    for ht in hoteles_texto:
        if not ht:
            continue
        hn = _normalizar(ht)
        match = next((h for h in todos_hoteles if _normalizar(h["nombre"]) == hn), None)
        # Búsqueda parcial como fallback
        if not match:
            match = next((h for h in todos_hoteles if hn in _normalizar(h["nombre"]) or _normalizar(h["nombre"]) in hn), None)
        if match:
            hotel_ids_asignados.append(match["id"])
        else:
            hoteles_no_encontrados.append(ht)

    for hid in hotel_ids_asignados:
        execute(
            "INSERT INTO usuario_hoteles (usuario_id, hotel_id) VALUES (%s,%s) ON CONFLICT DO NOTHING",
            (new_uid, hid)
        )

    # Marcar solicitud como aprobada
    execute(
        "UPDATE solicitudes_acceso SET estado='aprobada' WHERE id=%s",
        (sol_id,)
    )
    db.commit()

    # Email de bienvenida al nuevo usuario
    app_url   = os.environ.get("APP_URL", "https://control-pedidos-princess.onrender.com").rstrip("/")
    asunto_u  = "✅ Tu acceso ha sido aprobado — Control de Pedidos Princess"
    hoteles_lista = sol["hoteles"] or "—"
    aviso_hoteles = (
        f"<p style='margin:0 0 10px;font-size:12px;color:#b45309;'>"
        f"⚠️ Los siguientes hoteles no se pudieron asignar automáticamente y requerirán ajuste manual: "
        f"<strong>{', '.join(hoteles_no_encontrados)}</strong></p>"
    ) if hoteles_no_encontrados else ""

    body_html_u = f"""
    <div style="font-family:sans-serif;max-width:620px;margin:0 auto;
                background:#f9f9f9;border-radius:10px;overflow:hidden;
                border:1px solid #e0e0e0;">
      <div style="background:#0f2044;padding:24px 28px;">
        <h2 style="margin:0;color:#c9a84c;font-size:18px;">🎉 ¡Tu cuenta ha sido creada!</h2>
        <p style="margin:6px 0 0;color:rgba(255,255,255,.6);font-size:13px;">
          Control de Pedidos · Princess Canarias
        </p>
      </div>
      <div style="padding:28px;">
        <p style="margin:0 0 16px;font-size:15px;color:#333;">
          Hola, <strong>{nombre_c}</strong>
        </p>
        <p style="margin:0 0 20px;font-size:14px;color:#555;line-height:1.6;">
          Tu solicitud de acceso ha sido aprobada. Ya puedes acceder al sistema
          con las siguientes credenciales:
        </p>
        <div style="background:#fff;border:2px solid #c9a84c;border-radius:8px;
                    padding:20px 24px;margin-bottom:20px;">
          <table border="0" cellpadding="0" cellspacing="0" style="width:100%;font-size:14px;">
            <tr>
              <td style="padding:8px 0;color:#888;width:140px;">Usuario</td>
              <td style="padding:8px 0;font-family:monospace;font-size:16px;
                         font-weight:700;color:#0f2044;">{username}</td>
            </tr>
            <tr>
              <td style="padding:8px 0;color:#888;">Contraseña temporal</td>
              <td style="padding:8px 0;font-family:monospace;font-size:16px;
                         font-weight:700;color:#c9a84c;">{password_temp}</td>
            </tr>
            <tr>
              <td style="padding:8px 0;color:#888;">Hoteles asignados</td>
              <td style="padding:8px 0;font-size:13px;color:#333;">{hoteles_lista}</td>
            </tr>
          </table>
        </div>
        {aviso_hoteles}
        <div style="text-align:center;margin-bottom:20px;">
          <a href="{app_url}"
             style="display:inline-block;padding:12px 28px;background:#0f2044;
                    color:#c9a84c;border-radius:7px;text-decoration:none;
                    font-weight:700;font-size:14px;">Acceder al sistema →</a>
        </div>
        <p style="margin:0;font-size:12px;color:#aaa;line-height:1.5;">
          Por seguridad, te recomendamos cambiar la contraseña en tu primer acceso.<br>
          Si tienes cualquier problema contacta con el departamento de compras.
        </p>
      </div>
      <div style="padding:14px 28px;background:#f0f0f0;font-size:11px;color:#aaa;">
        Mensaje automático · Control Pedidos Princess Canarias
      </div>
    </div>
    """

    body_text_u = (
        f"Hola {nombre_c},\n\n"
        f"Tu solicitud de acceso ha sido aprobada.\n\n"
        f"Usuario         : {username}\n"
        f"Contraseña temp.: {password_temp}\n"
        f"Hoteles         : {hoteles_lista}\n\n"
        f"Accede en: {app_url}\n\n"
        f"Te recomendamos cambiar la contraseña en tu primer acceso.\n\n"
        f"Control Pedidos Princess Canarias"
    )

    # El envío real lo hace el frontend vía EmailJS — siempre pendiente
    res_u = {"ok": False}

    # Email de confirmación a los admins
    asunto_a = f"[APROBADA] Alta usuario {username} — {nombre_c}"
    body_html_a = f"""
    <div style="font-family:sans-serif;max-width:580px;margin:0 auto;
                background:#f9f9f9;border-radius:10px;overflow:hidden;
                border:1px solid #e0e0e0;">
      <div style="background:#065f46;padding:20px 24px;">
        <h2 style="margin:0;color:#6ee7b7;font-size:16px;">✅ Cuenta creada automáticamente</h2>
      </div>
      <div style="padding:20px 24px;font-size:14px;color:#333;">
        <p>La solicitud #{sol_id} de <strong>{nombre_c}</strong> ha sido aprobada.</p>
        <table border="0" cellpadding="0" cellspacing="0" style="font-size:13px;width:100%;">
          <tr><td style="color:#888;padding:5px 0;width:130px;">Username</td><td style="font-family:monospace;font-weight:700;">{username}</td></tr>
          <tr><td style="color:#888;padding:5px 0;">Email</td><td>{sol['email']}</td></tr>
          <tr><td style="color:#888;padding:5px 0;">Hoteles</td><td>{hoteles_lista}</td></tr>
          {'<tr><td style="color:#b45309;padding:5px 0;">⚠️ Sin asignar</td><td style="color:#b45309;">' + ", ".join(hoteles_no_encontrados) + "</td></tr>" if hoteles_no_encontrados else ""}
        </table>
        <p style="margin:14px 0 0;font-size:12px;color:#aaa;">
          El usuario ha recibido su email de bienvenida con credenciales.
        </p>
      </div>
    </div>
    """
    body_text_a = (
        f"Cuenta creada automáticamente\n\n"
        f"La solicitud #{sol_id} de {nombre_c} ha sido aprobada.\n\n"
        f"Username: {username}\n"
        f"Email   : {sol['email']}\n"
        f"Hoteles : {hoteles_lista}\n"
        + (f"⚠️ Hoteles sin asignar: {', '.join(hoteles_no_encontrados)}\n" if hoteles_no_encontrados else "")
        + f"\nEl usuario ha recibido su email de bienvenida con credenciales."
    )
    destinatarios = _get_solo_admin_emails()
    # Los emails a admins también se envían desde el frontend vía EmailJS
    admins_email_enviado = False

    return jsonify({
        "ok":       True,
        "uid":      new_uid,
        "username": username,
        "password": password_temp,
        "hoteles_asignados":      hotel_ids_asignados,
        "hoteles_no_encontrados": hoteles_no_encontrados,
        "email_enviado":          res_u.get("ok", False),
        # Datos para que el frontend envíe vía EmailJS:
        "email_usuario_pendiente": (not res_u.get("ok", False)) and {
            "to_email":  sol["email"],
            "asunto":    asunto_u,
            "body_text": body_text_u,
        } or None,
        "email_admins_pendiente": (not admins_email_enviado and destinatarios) and {
            "destinatarios": destinatarios,
            "asunto":        asunto_a,
            "body_text":     body_text_a,
        } or None,
        "abrir_edicion":          True,
        "msg": f"Cuenta creada para {nombre_c} ({username})."
    })


# ─── ADMIN: rechazar solicitud ────────────────────────────────────────────────

@app.route("/api/admin/solicitudes-acceso/<int:sol_id>/rechazar", methods=["POST"])
def admin_rechazar_solicitud(sol_id):
    if session.get("rol") != "admin":
        return jsonify({"error": "Sin permisos"}), 403
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            "UPDATE solicitudes_acceso SET estado='rechazada' WHERE id=%s", (sol_id,)
        )
    db.commit()
    return jsonify({"ok": True})

@app.route("/api/me")
def me():
    if "user_id" not in session:
        return jsonify({"logged": False})
    return jsonify({"logged": True, "id": session["user_id"], "username": session["username"],
                    "nombre": session["nombre"], "rol": session["rol"],
                    "hoteles_ids": session.get("hoteles_ids", [])})

# ── API Maestros ───────────────────────────────────────────────────────────────

@app.route("/api/maestros")
@login_required
def get_maestros():
    if session.get("rol") == "hotel":
        hoteles_ids = session.get("hoteles_ids", [])
        if hoteles_ids:
            placeholders = ",".join(["%s"] * len(hoteles_ids))
            hoteles = rows_to_list(query(
                f"SELECT * FROM hoteles WHERE activo=1 AND id IN ({placeholders}) ORDER BY codigo",
                tuple(hoteles_ids)
            ))
        else:
            hoteles = []
    else:
        hoteles = rows_to_list(query("SELECT * FROM hoteles WHERE activo=1 ORDER BY codigo"))
    departamentos = rows_to_list(query("SELECT * FROM departamentos WHERE activo=1 ORDER BY nombre"))
    familias      = rows_to_list(query("SELECT * FROM familias WHERE activo=1 ORDER BY nombre"))
    return jsonify({
        "hoteles":       hoteles,
        "departamentos": departamentos,
        "proveedores":   [],
        "estados":       ESTADOS_VALIDOS,
        "familias":      familias,
    })

# ── API Familias ───────────────────────────────────────────────────────────────

@app.route("/api/familias", methods=["GET"])
@login_required
def get_familias():
    rows = rows_to_list(query("SELECT * FROM familias WHERE activo=1 ORDER BY nombre"))
    return jsonify(rows)

@app.route("/api/familias", methods=["POST"])
@admin_required
def create_familia():
    data   = request.get_json(silent=True) or {}
    nombre = (data.get("nombre") or "").strip()
    if not nombre:
        return jsonify({"error": "Nombre requerido"}), 400
    db  = get_db()
    cur = execute("INSERT INTO familias (nombre) VALUES (%s) ON CONFLICT (nombre) DO NOTHING RETURNING id", (nombre,))
    row = cur.fetchone()
    if not row:
        return jsonify({"error": "Ya existe una familia con ese nombre"}), 409
    db.commit()
    return jsonify({"ok": True, "id": row["id"], "nombre": nombre}), 201

@app.route("/api/familias/<int:fid>", methods=["PUT"])
@admin_required
def update_familia(fid):
    data   = request.get_json(silent=True) or {}
    nombre = (data.get("nombre") or "").strip()
    if not nombre:
        return jsonify({"error": "Nombre requerido"}), 400
    db = get_db()
    execute("UPDATE familias SET nombre=%s WHERE id=%s", (nombre, fid))
    db.commit()
    return jsonify({"ok": True})

@app.route("/api/familias/<int:fid>", methods=["DELETE"])
@admin_required
def delete_familia(fid):
    db  = get_db()
    cnt = query("SELECT COUNT(*) as n FROM pedidos WHERE familia_id=%s AND sujeto_techo=1", (fid,), one=True)["n"]
    if cnt > 0:
        return jsonify({"error": f"No se puede eliminar: tiene {cnt} pedido(s) asociado(s)"}), 409
    execute("UPDATE familias SET activo=0 WHERE id=%s", (fid,))
    db.commit()
    return jsonify({"ok": True})

# ── API Usuarios (gestión admin) ───────────────────────────────────────────────

@app.route("/api/usuarios", methods=["GET"])
@admin_required
def get_usuarios():
    rows = rows_to_list(query(
        "SELECT id, username, nombre, email, movil, rol, activo, creado_en, telegram_chat_id FROM usuarios ORDER BY nombre"
    ))
    return jsonify(rows)

@app.route("/api/usuarios", methods=["POST"])
@admin_required
def create_usuario():
    data     = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip().lower()
    nombre   = (data.get("nombre")   or "").strip()
    password = (data.get("password") or "").strip()
    if not username or not nombre or not password:
        return jsonify({"error": "username, nombre y contraseña son obligatorios"}), 400
    existing = query("SELECT id FROM usuarios WHERE username=%s", (username,), one=True)
    if existing:
        return jsonify({"error": "Ya existe un usuario con ese username"}), 409
    db  = get_db()
    rol = data.get("rol", "user")
    if rol not in ("admin", "user", "hotel", "compras"):
        rol = "user"
    cur = execute(
        "INSERT INTO usuarios (username, nombre, email, movil, password, rol, activo, telegram_chat_id) VALUES (%s,%s,%s,%s,%s,%s,1,%s) RETURNING id",
        (username, nombre, data.get("email",""), data.get("movil",""), password, rol,
         (data.get("telegram_chat_id") or "").strip() or None)
    )
    new_id = cur.fetchone()["id"]
    db.commit()
    return jsonify({"ok": True, "id": new_id}), 201

@app.route("/api/usuarios/<int:uid>", methods=["PUT"])
@admin_required
def update_usuario(uid):
    data = request.get_json(silent=True) or {}
    db   = get_db()
    # No permitir que el admin se quite el rol a sí mismo
    if uid == current_user_id() and data.get("rol") in ("user", "hotel", "compras"):
        return jsonify({"error": "No puedes quitarte el rol de administrador a ti mismo"}), 400
    # Construir UPDATE dinámico solo con campos enviados
    fields, args = [], []
    if "nombre" in data:
        fields.append("nombre=%s"); args.append(data["nombre"].strip())
    if "email" in data:
        fields.append("email=%s"); args.append(data["email"].strip())
    if "movil" in data:
        fields.append("movil=%s"); args.append((data["movil"] or "").strip())
    if "rol" in data and data["rol"] in ("admin", "user", "hotel", "compras"):
        fields.append("rol=%s"); args.append(data["rol"])
    if "activo" in data:
        # ── Protección: no desactivar comprador si deja hoteles huérfanos ────
        desactivando = (not data["activo"]) or (data["activo"] == 0)
        if desactivando:
            usuario_actual = query("SELECT rol, activo FROM usuarios WHERE id=%s", (uid,), one=True)
            if usuario_actual and usuario_actual["rol"] == "compras" and usuario_actual["activo"] == 1:
                huerfanos = rows_to_list(query("""
                    SELECT h.codigo FROM hoteles h
                    JOIN usuario_comprador_hoteles uch ON uch.hotel_id = h.id
                    WHERE uch.usuario_id = %s
                      AND h.activo = 1
                      AND NOT EXISTS (
                          SELECT 1 FROM usuario_comprador_hoteles uch2
                          JOIN usuarios u2 ON u2.id = uch2.usuario_id
                          WHERE uch2.hotel_id = h.id
                            AND uch2.usuario_id != %s
                            AND u2.activo = 1
                            AND u2.rol = 'compras'
                      )
                """, (uid, uid)))
                if huerfanos:
                    codigos = ", ".join(r["codigo"] for r in huerfanos)
                    return jsonify({
                        "error": f"⚠️ No se puede desactivar: los hoteles {codigos} quedarían sin comprador asignado. "
                                 f"Reasígnalos a otro comprador antes de desactivar este usuario."
                    }), 409
        fields.append("activo=%s"); args.append(1 if data["activo"] else 0)
    if "password" in data and data["password"].strip():
        fields.append("password=%s"); args.append(data["password"].strip())
    if "telegram_chat_id" in data:
        fields.append("telegram_chat_id=%s"); args.append((data["telegram_chat_id"] or "").strip() or None)
    if not fields:
        return jsonify({"error": "Nada que actualizar"}), 400
    args.append(uid)
    execute(f"UPDATE usuarios SET {', '.join(fields)} WHERE id=%s", args)
    db.commit()
    # Si cambié mi propio nombre, actualizar sesión
    if uid == current_user_id() and "nombre" in data:
        session["nombre"] = data["nombre"].strip()
    return jsonify({"ok": True})

# ── API Hoteles de usuario (rol hotel) ────────────────────────────────────────

@app.route("/api/usuarios/<int:uid>/hoteles", methods=["GET"])
@admin_required
def get_usuario_hoteles(uid):
    rows = rows_to_list(query(
        "SELECT hotel_id FROM usuario_hoteles WHERE usuario_id=%s", (uid,)
    ))
    return jsonify([r["hotel_id"] for r in rows])

@app.route("/api/usuarios/<int:uid>/hoteles", methods=["PUT"])
@admin_required
def set_usuario_hoteles(uid):
    data = request.get_json(silent=True) or {}
    hotel_ids = data.get("hotel_ids", [])
    db = get_db()
    execute("DELETE FROM usuario_hoteles WHERE usuario_id=%s", (uid,))
    for hid in hotel_ids:
        execute("INSERT INTO usuario_hoteles (usuario_id, hotel_id) VALUES (%s,%s) ON CONFLICT DO NOTHING", (uid, hid))
    db.commit()
    return jsonify({"ok": True})

# ── API Hoteles de usuario compras (rol compras) ──────────────────────────────
# Permite asignar/desasignar hoteles a compradores desde el panel de admin,
# sustituyendo el diccionario HOTEL_COMPRADOR hardcodeado.

@app.route("/api/usuarios/<int:uid>/hoteles-compras", methods=["GET"])
@admin_required
def get_usuario_comprador_hoteles(uid):
    """Devuelve los hotel_id asignados a un usuario compras."""
    rows = rows_to_list(query(
        "SELECT hotel_id FROM usuario_comprador_hoteles WHERE usuario_id=%s", (uid,)
    ))
    return jsonify([r["hotel_id"] for r in rows])


@app.route("/api/usuarios/<int:uid>/hoteles-compras", methods=["PUT"])
@admin_required
def set_usuario_comprador_hoteles(uid):
    """
    Reemplaza completamente los hoteles asignados a un usuario compras.

    Modelo: 1 hotel → 1 comprador.
    Si algún hotel ya tiene otro comprador asignado, devuelve 409 con la lista
    de conflictos para que el frontend muestre la confirmación de reasignación.
    Si se envía forzar=true, los hoteles en conflicto se reasignan automáticamente
    (se eliminan del comprador anterior).
    """
    data      = request.get_json(silent=True) or {}
    hotel_ids = data.get("hotel_ids", [])
    forzar    = bool(data.get("forzar", False))
    db        = get_db()

    # ── Protección: hoteles que este comprador va a PERDER → ¿quedarán huérfanos? ──
    # Se calcula antes de cualquier DELETE. Un hotel queda huérfano si:
    #   - está actualmente asignado a este comprador
    #   - NO está en la nueva lista hotel_ids
    #   - NO tiene otro comprador alternativo activo
    hoteles_actuales = [
        r["hotel_id"] for r in rows_to_list(
            query("SELECT hotel_id FROM usuario_comprador_hoteles WHERE usuario_id=%s", (uid,))
        )
    ]
    hoteles_a_perder = [hid for hid in hoteles_actuales if hid not in hotel_ids]
    huerfanos_por_vaciado = []
    for hid in hoteles_a_perder:
        otro_comprador = query(
            """SELECT u.id FROM usuario_comprador_hoteles uch
               JOIN usuarios u ON u.id = uch.usuario_id
               WHERE uch.hotel_id = %s AND uch.usuario_id != %s
                 AND u.activo = 1 AND u.rol = 'compras'
               LIMIT 1""",
            (hid, uid), one=True
        )
        if not otro_comprador:
            hotel = query("SELECT codigo, nombre FROM hoteles WHERE id=%s AND activo=1", (hid,), one=True)
            if hotel:
                huerfanos_por_vaciado.append({
                    "hotel_id":     hid,
                    "hotel_codigo": hotel["codigo"],
                    "hotel_nombre": hotel["nombre"],
                })
    if huerfanos_por_vaciado:
        codigos = ", ".join(h["hotel_codigo"] for h in huerfanos_por_vaciado)
        return jsonify({
            "ok": False,
            "error": f"⚠️ Los hoteles {codigos} quedarían sin comprador asignado. "
                     f"Asígnalos a otro comprador antes de quitárselos a este usuario.",
            "huerfanos": huerfanos_por_vaciado,
        }), 409

    # ── Detectar conflictos: hoteles ya asignados a otro comprador ───────────
    conflictos = []
    for hid in hotel_ids:
        otro = query(
            """SELECT u.id, u.nombre
               FROM usuario_comprador_hoteles uch
               JOIN usuarios u ON u.id = uch.usuario_id
               WHERE uch.hotel_id = %s AND uch.usuario_id != %s
               LIMIT 1""",
            (hid, uid), one=True
        )
        if otro:
            hotel = query("SELECT codigo, nombre FROM hoteles WHERE id=%s", (hid,), one=True)
            conflictos.append({
                "hotel_id":               hid,
                "hotel_codigo":           hotel["codigo"]  if hotel else str(hid),
                "hotel_nombre":           hotel["nombre"]  if hotel else "",
                "comprador_actual_id":    otro["id"],
                "comprador_actual_nombre": otro["nombre"],
            })

    # Si hay conflictos y no se ha confirmado la reasignación, devolver 409
    if conflictos and not forzar:
        return jsonify({"ok": False, "conflictos": conflictos}), 409

    # ── Reasignación: quitar estos hoteles de cualquier comprador anterior ────
    for hid in hotel_ids:
        execute("DELETE FROM usuario_comprador_hoteles WHERE hotel_id=%s", (hid,))

    # ── Borrar asignaciones previas de este comprador y aplicar las nuevas ────
    execute("DELETE FROM usuario_comprador_hoteles WHERE usuario_id=%s", (uid,))
    for hid in hotel_ids:
        execute(
            "INSERT INTO usuario_comprador_hoteles (usuario_id, hotel_id) VALUES (%s,%s)",
            (uid, hid)
        )
    db.commit()
    reasignados = len(conflictos) if forzar else 0
    log.info(
        "Hoteles-compras actualizados: usuario_id=%s hoteles=%s reasignados=%s",
        uid, hotel_ids, reasignados
    )
    return jsonify({"ok": True, "reasignados": reasignados})


@app.route("/api/compradores-por-hotel")
@admin_required
def get_compradores_por_hotel():
    """
    Devuelve un resumen de todos los hoteles con sus compradores asignados.
    Incluye campo sin_comprador=True para los hoteles que no tienen comprador,
    y un resumen de integridad global al final.
    Útil para que admin visualice la distribución actual y detecte huérfanos.
    """
    hoteles = rows_to_list(query("SELECT id, codigo, nombre FROM hoteles WHERE activo=1 ORDER BY codigo"))
    resultado = []
    huerfanos = 0
    for hotel in hoteles:
        compradores = rows_to_list(query(
            """SELECT u.id, u.username, u.nombre, u.email, u.movil, u.telegram_chat_id
               FROM usuarios u
               JOIN usuario_comprador_hoteles uch ON uch.usuario_id = u.id
               WHERE uch.hotel_id = %s AND u.activo = 1 AND u.rol = 'compras'
               ORDER BY u.nombre""",
            (hotel["id"],)
        ))
        sin_comprador = len(compradores) == 0
        if sin_comprador:
            huerfanos += 1
        resultado.append({
            "hotel_id":      hotel["id"],
            "hotel_codigo":  hotel["codigo"],
            "hotel_nombre":  hotel["nombre"],
            "compradores":   compradores,
            "sin_comprador": sin_comprador,
        })
    return jsonify({
        "hoteles":   resultado,
        "integridad": {
            "total_hoteles":       len(resultado),
            "hoteles_sin_comprador": huerfanos,
            "ok":                  huerfanos == 0,
        },
    })


@app.route("/api/usuarios/<int:uid>", methods=["DELETE"])
@admin_required
def delete_usuario(uid):
    # No puede eliminarse a sí mismo
    if uid == current_user_id():
        return jsonify({"error": "No puedes eliminar tu propio usuario"}), 400
    # Verificar que existe y obtener nombre
    user = query("SELECT id, username, nombre FROM usuarios WHERE id=%s", (uid,), one=True)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    nombre = user["nombre"]
    db = get_db()
    # ── Protección: no eliminar comprador si deja hoteles huérfanos ──────────
    if user_row := query("SELECT rol FROM usuarios WHERE id=%s", (uid,), one=True):
        if user_row["rol"] == "compras":
            huerfanos = rows_to_list(query("""
                SELECT h.codigo FROM hoteles h
                JOIN usuario_comprador_hoteles uch ON uch.hotel_id = h.id
                WHERE uch.usuario_id = %s
                  AND h.activo = 1
                  AND NOT EXISTS (
                      SELECT 1 FROM usuario_comprador_hoteles uch2
                      JOIN usuarios u2 ON u2.id = uch2.usuario_id
                      WHERE uch2.hotel_id = h.id
                        AND uch2.usuario_id != %s
                        AND u2.activo = 1
                        AND u2.rol = 'compras'
                  )
            """, (uid, uid)))
            if huerfanos:
                codigos = ", ".join(r["codigo"] for r in huerfanos)
                return jsonify({
                    "error": f"⚠️ No se puede eliminar: los hoteles {codigos} quedarían sin comprador asignado. "
                             f"Reasígnalos a otro comprador antes de eliminar este usuario."
                }), 409
    # ── Congelar nombre en pedidos antes de que la FK quede NULL ─────────────
    execute("""
        UPDATE pedidos SET creado_por_nombre = %s
        WHERE creado_por_id = %s AND (creado_por_nombre IS NULL OR creado_por_nombre = '')
    """, (nombre, uid))
    execute("""
        UPDATE pedidos SET modificado_por_nombre = %s
        WHERE modificado_por_id = %s AND (modificado_por_nombre IS NULL OR modificado_por_nombre = '')
    """, (nombre, uid))
    execute("""
        UPDATE historial_estados SET usuario_nombre = %s
        WHERE usuario_id = %s AND (usuario_nombre IS NULL OR usuario_nombre = '')
    """, (nombre, uid))
    # ── Eliminar usuario (usuario_hoteles y password_reset_tokens en CASCADE) ─
    execute("DELETE FROM usuarios WHERE id=%s", (uid,))
    db.commit()
    return jsonify({"ok": True})

# ── API Proveedores ────────────────────────────────────────────────────────────

def _prov_with_contactos(rows):
    """Añade lista de contactos a cada proveedor."""
    result = rows_to_list(rows)
    if not result:
        return result
    ids = [p["id"] for p in result]
    placeholders = ",".join(["%s"] * len(ids))
    contactos_rows = rows_to_list(query(
        f"SELECT proveedor_id,nombre,telefono,movil,email,es_principal FROM proveedor_contactos WHERE proveedor_id IN ({placeholders}) ORDER BY proveedor_id,es_principal DESC,orden,id",
        tuple(ids)
    ))
    # Agrupar por proveedor_id
    from collections import defaultdict
    cmap = defaultdict(list)
    for c in contactos_rows:
        cmap[c["proveedor_id"]].append({
            "nombre":       c["nombre"] or "",
            "telefono":     c["telefono"] or "",
            "movil":        c["movil"] or "",
            "email":        c["email"] or "",
            "es_principal": bool(c["es_principal"]),
        })
    for p in result:
        p["contactos"] = cmap.get(p["id"], [])
        # Campos de compatibilidad: usar contacto principal (o primero si no hay)
        principal = next((c for c in p["contactos"] if c.get("es_principal")), p["contactos"][0] if p["contactos"] else {})
        p["contacto"]       = principal.get("nombre", "")
        p["email"]          = principal.get("email", "")
        p["telefono"]       = principal.get("telefono", "")
        p["movil_principal"] = principal.get("movil", "")
    return result

@app.route("/api/proveedores", methods=["GET"])
@login_required
def get_proveedores():
    q = request.args.get("q", "").strip()
    if q:
        rows = query(
            "SELECT id,codigo,nombre,observaciones FROM proveedores WHERE activo=1 AND nombre ILIKE %s ORDER BY nombre",
            (f"%{q}%",))
    else:
        rows = query("SELECT id,codigo,nombre,observaciones FROM proveedores WHERE activo=1 ORDER BY nombre")
    result = _prov_with_contactos(rows)
    # Rol hotel: solo consulta — se eliminan observaciones de la respuesta
    if session.get("rol") == "hotel":
        for p in result:
            p.pop("observaciones", None)
    return jsonify(result)

@app.route("/api/proveedores", methods=["POST"])
@admin_required
def create_proveedor():
    data   = request.get_json(silent=True) or {}
    nombre = (data.get("nombre") or "").strip()
    codigo = (data.get("codigo") or "").strip()
    if not nombre:
        return jsonify({"error": "Nombre requerido"}), 400
    if not codigo:
        return jsonify({"error": "El código SAP es obligatorio"}), 400
    # Anti-duplicado: mismo nombre (insensible a mayúsculas)
    dup_nombre = query(
        "SELECT id FROM proveedores WHERE activo=1 AND LOWER(nombre)=LOWER(%s)", (nombre,)
    )
    if rows_to_list(dup_nombre):
        return jsonify({"error": f"Ya existe un proveedor con el nombre '{nombre}'"}), 409
    # Anti-duplicado: mismo código SAP
    dup_codigo = query(
        "SELECT id FROM proveedores WHERE activo=1 AND codigo=%s", (codigo,)
    )
    if rows_to_list(dup_codigo):
        return jsonify({"error": f"Ya existe un proveedor con el código SAP '{codigo}'"}), 409
    db  = get_db()
    cur = execute(
        "INSERT INTO proveedores (codigo,nombre,observaciones) VALUES (%s,%s,%s) RETURNING id",
        (codigo, nombre, data.get("observaciones",""))
    )
    new_id = cur.fetchone()["id"]
    # Insertar contactos
    contactos = data.get("contactos", [])
    for i, c in enumerate(contactos):
        nombre_c    = (c.get("nombre") or "").strip() or None
        tel_c       = (c.get("telefono") or "").strip() or None
        movil_c     = (c.get("movil") or "").strip() or None
        email_c     = (c.get("email") or "").strip() or None
        principal_c = 1 if c.get("es_principal") else 0
        if nombre_c or tel_c or movil_c or email_c:
            execute(
                "INSERT INTO proveedor_contactos (proveedor_id,nombre,telefono,movil,email,es_principal,orden) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (new_id, nombre_c, tel_c, movil_c, email_c, principal_c, i)
            )
    db.commit()
    return jsonify({"ok": True, "id": new_id, "nombre": nombre}), 201

@app.route("/api/proveedores/<int:pid>", methods=["PUT"])
@admin_required
def update_proveedor(pid):
    data   = request.get_json(silent=True) or {}
    nombre = (data.get("nombre") or "").strip()
    codigo = (data.get("codigo") or "").strip()
    if not nombre:
        return jsonify({"error": "Nombre requerido"}), 400
    if not codigo:
        return jsonify({"error": "El código SAP es obligatorio"}), 400
    # Anti-duplicado: nombre en uso por otro proveedor
    dup_nombre = query(
        "SELECT id FROM proveedores WHERE activo=1 AND LOWER(nombre)=LOWER(%s) AND id!=%s", (nombre, pid)
    )
    if rows_to_list(dup_nombre):
        return jsonify({"error": f"Ya existe otro proveedor con el nombre '{nombre}'"}), 409
    # Anti-duplicado: código SAP en uso por otro proveedor
    dup_codigo = query(
        "SELECT id FROM proveedores WHERE activo=1 AND codigo=%s AND id!=%s", (codigo, pid)
    )
    if rows_to_list(dup_codigo):
        return jsonify({"error": f"Ya existe otro proveedor con el código SAP '{codigo}'"}), 409
    db   = get_db()
    execute(
        "UPDATE proveedores SET codigo=%s,nombre=%s,observaciones=%s WHERE id=%s",
        (codigo, nombre, data.get("observaciones",""), pid)
    )
    # Reemplazar contactos
    execute("DELETE FROM proveedor_contactos WHERE proveedor_id=%s", (pid,))
    contactos = data.get("contactos", [])
    for i, c in enumerate(contactos):
        nombre_c    = (c.get("nombre") or "").strip() or None
        tel_c       = (c.get("telefono") or "").strip() or None
        movil_c     = (c.get("movil") or "").strip() or None
        email_c     = (c.get("email") or "").strip() or None
        principal_c = 1 if c.get("es_principal") else 0
        if nombre_c or tel_c or movil_c or email_c:
            execute(
                "INSERT INTO proveedor_contactos (proveedor_id,nombre,telefono,movil,email,es_principal,orden) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (pid, nombre_c, tel_c, movil_c, email_c, principal_c, i)
            )
    db.commit()
    return jsonify({"ok": True})

@app.route("/api/proveedores/<int:pid>", methods=["DELETE"])
@admin_required
def delete_proveedor(pid):
    db = get_db()
    row = query("SELECT COUNT(*) as cnt FROM pedidos WHERE proveedor_id=%s", (pid,))
    cnt = rows_to_list(row)[0]["cnt"] if row else 0
    if cnt > 0:
        return jsonify({"error": f"No se puede eliminar: tiene {cnt} pedido{'s' if cnt!=1 else ''} asociado{'s' if cnt!=1 else ''}"}), 409
    execute("DELETE FROM proveedor_contactos WHERE proveedor_id=%s", (pid,))
    execute("DELETE FROM proveedores WHERE id=%s", (pid,))
    db.commit()
    return jsonify({"ok": True})

@app.route("/api/proveedores/exportar", methods=["GET"])
@login_required
def exportar_proveedores():
    if session.get("rol") == "hotel":
        return jsonify({"error": "Sin permisos"}), 403
    try:
        import openpyxl, io
        from datetime import datetime as dt
        from openpyxl.styles import Font, PatternFill, Alignment
        from flask import send_file

        provs = _prov_with_contactos(query(
            "SELECT id,codigo,nombre,observaciones FROM proveedores WHERE activo=1 ORDER BY nombre"
        ))

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Proveedores"

        # Cabeceras: CODIGO · PROVEEDOR · PRINCIPAL · CONTACTO · TELEFONO · MOVIL · EMAIL · OBSERVACIONES
        headers = ["CODIGO", "PROVEEDOR", "PRINCIPAL", "CONTACTO", "TELEFONO", "MOVIL", "EMAIL", "OBSERVACIONES"]
        col_widths = [14, 42, 10, 25, 18, 18, 35, 38]

        hdr_fill_prov = PatternFill("solid", fgColor="1B2A4A")
        hdr_fill_ctc  = PatternFill("solid", fgColor="2E5090")
        hdr_font      = Font(bold=True, color="FFFFFF")

        ctc_cols = {3, 4, 5, 6, 7}  # columnas de contacto (1-based)
        for col_idx, h in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_idx, value=h)
            cell.fill = hdr_fill_ctc if col_idx in ctc_cols else hdr_fill_prov
            cell.font = hdr_font
            cell.alignment = Alignment(horizontal="center")

        for i, w in enumerate(col_widths, 1):
            ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w

        # Freeze header row
        ws.freeze_panes = "A2"

        # Estilos de filas
        from openpyxl.styles import Border, Side
        thin = Side(style="thin", color="D0D7E3")
        border = Border(bottom=thin)
        fill_principal = PatternFill("solid", fgColor="FFF8E7")   # dorado claro → principal
        fill_alt       = PatternFill("solid", fgColor="F5F7FA")   # gris claro → proveedor sin color
        fill_ctc_alt   = PatternFill("solid", fgColor="EEF2FA")   # azul muy claro → contacto secundario

        r_idx = 2
        for p in provs:
            contactos = p.get("contactos", [{}])
            if not contactos:
                contactos = [{}]
            for ci, c in enumerate(contactos):
                es_principal = c.get("es_principal", ci == 0)
                principal_val = "★" if es_principal else ""

                # Color de fila
                if es_principal:
                    row_fill = fill_principal
                elif ci > 0:
                    row_fill = fill_ctc_alt
                else:
                    row_fill = None

                vals = [
                    p.get("codigo") or ""      if ci == 0 else "",
                    p.get("nombre") or ""      if ci == 0 else "",
                    principal_val,
                    c.get("nombre") or "",
                    c.get("telefono") or "",
                    c.get("movil") or "",
                    c.get("email") or "",
                    p.get("observaciones") or "" if ci == 0 else "",
                ]
                for col_idx, val in enumerate(vals, 1):
                    cell = ws.cell(row=r_idx, column=col_idx, value=val)
                    cell.border = border
                    if col_idx == 3:  # PRINCIPAL col
                        cell.alignment = Alignment(horizontal="center")
                        cell.font = Font(bold=True, color="B8860B")
                    if row_fill:
                        cell.fill = row_fill
                r_idx += 1

        # Nota de instrucciones en la parte inferior
        ws.cell(row=r_idx + 1, column=1, value="INSTRUCCIONES DE IMPORTACIÓN:").font = Font(bold=True, color="1B2A4A")
        instrucciones = [
            "• CODIGO: código SAP (obligatorio). Identifica al proveedor — si ya existe se actualiza, si no existe se crea.",
            "• PRINCIPAL: Escribe ★ o 1 o SI en la fila del contacto que recibirá emails/WhatsApp automáticos. Solo uno por proveedor.",
            "• Varios contactos del mismo proveedor: repite CODIGO y PROVEEDOR en filas adicionales, deja OBSERVACIONES vacío.",
            "• TELEFONO: teléfono fijo.  MOVIL: móvil/WhatsApp (se usará para alertas automáticas).",
            "• Para eliminar todos los contactos de un proveedor: deja CONTACTO, TELEFONO, MOVIL y EMAIL vacíos.",
        ]
        for i, txt in enumerate(instrucciones, r_idx + 2):
            cell = ws.cell(row=i, column=1, value=txt)
            cell.font = Font(italic=True, color="555555", size=9)
            ws.merge_cells(start_row=i, start_column=1, end_row=i, end_column=len(headers))

        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        filename = f"PROVEEDORES_{dt.now().strftime('%Y%m%d_%H%M')}.xlsx"
        return send_file(buf, as_attachment=True, download_name=filename,
                         mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


def _parse_excel_proveedores(archivo):
    """
    Lee un .xlsx de proveedores y devuelve (prov_order, prov_data).
    prov_data[key] = {codigo, nombre, observaciones, contactos: [(nombre,tel,movil,email,es_principal), ...]}
    Hace todo el trabajo en memoria — sin tocar la BD — para minimizar el tiempo de conexión.
    """
    import openpyxl
    wb = openpyxl.load_workbook(archivo, data_only=True, read_only=True)
    ws = wb.active
    raw_headers = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))]
    headers = [str(h).strip().upper() if h is not None else "" for h in raw_headers]

    PRINCIPAL_SI = {"★", "1", "SI", "SÍ", "S", "YES", "Y", "TRUE"}

    def col(row, name):
        try:
            idx = headers.index(name)
            v = row[idx].value
            if v is None:
                return None
            s = str(v).strip()
            return s if s and s.lower() not in ("none", "nan") else None
        except (ValueError, IndexError):
            return None

    prov_data  = {}   # key → dict
    prov_order = []   # mantener orden de aparición

    last_key = None  # último proveedor visto — para filas de contacto extra sin CODIGO/PROVEEDOR

    for row in ws.iter_rows(min_row=2):
        nombre = col(row, "PROVEEDOR")
        codigo = col(row, "CODIGO") or ""

        if nombre:
            # Fila con proveedor identificado → crear/localizar entrada
            key = codigo or nombre
            if key not in prov_data:
                obs = col(row, "OBSERVACIONES") or ""
                prov_data[key] = {
                    "codigo":        codigo,
                    "nombre":        nombre,
                    "observaciones": obs,
                    "contactos":     [],
                }
                prov_order.append(key)
            last_key = key
        else:
            # Fila sin PROVEEDOR → contacto adicional del último proveedor visto
            key = last_key

        if key is None:
            continue  # fila suelta sin proveedor de referencia, ignorar

        c_nombre    = col(row, "CONTACTO")  or ""
        c_tel       = col(row, "TELEFONO")  or ""
        c_movil     = col(row, "MOVIL")     or ""
        c_email     = col(row, "EMAIL")     or ""
        c_principal = col(row, "PRINCIPAL") or ""
        es_principal = str(c_principal).strip().upper() in PRINCIPAL_SI

        if c_nombre or c_tel or c_movil or c_email:
            prov_data[key]["contactos"].append(
                (c_nombre, c_tel, c_movil, c_email, es_principal)
            )

    wb.close()

    # Garantizar que cada proveedor con contactos tenga exactamente uno principal
    for key in prov_order:
        ctcs = prov_data[key]["contactos"]
        if ctcs and not any(c[4] for c in ctcs):
            ctcs[0] = (ctcs[0][0], ctcs[0][1], ctcs[0][2], ctcs[0][3], True)

    return prov_order, prov_data

@app.route("/api/proveedores/importar", methods=["POST"])
@admin_required
def importar_proveedores():
    """
    Importación incremental: actualiza existentes (por código SAP), inserta nuevos.
    Usa bulk operations para evitar timeouts con listas grandes (>500 proveedores).
    Total de round-trips a la BD: ~5, independientemente del tamaño del Excel.
    """
    try:
        if "archivo" not in request.files:
            return jsonify({"ok": False, "error": "No se recibió ningún archivo"}), 400
        archivo = request.files["archivo"]
        if not archivo.filename.endswith((".xlsx", ".xls")):
            return jsonify({"ok": False, "error": "El archivo debe ser .xlsx"}), 400

        # ── 1. Parsear Excel completamente en memoria (sin BD) ──────────────
        prov_order, prov_data = _parse_excel_proveedores(archivo)

        # ── 2. Una sola query para saber qué proveedores ya existen ─────────
        from psycopg2.extras import execute_values
        db  = get_db()
        existentes = {r["codigo"]: r["id"] for r in rows_to_list(
            query("SELECT id, codigo FROM proveedores WHERE codigo IS NOT NULL AND codigo != ''")
        )}

        to_update = []   # (nombre, obs, id)
        to_insert = []   # (codigo, nombre, obs)

        for key in prov_order:
            p = prov_data[key]
            codigo = p["codigo"]
            if codigo and codigo in existentes:
                to_update.append((p["nombre"], p["observaciones"], existentes[codigo]))
            else:
                to_insert.append((codigo or None, p["nombre"], p["observaciones"]))

        # ── 3. Bulk UPDATE de proveedores existentes ─────────────────────────
        actualizados = 0
        with db.cursor() as cur:
            if to_update:
                execute_values(
                    cur,
                    """UPDATE proveedores AS p SET nombre=v.nombre, observaciones=v.obs
                       FROM (VALUES %s) AS v(nombre, obs, id)
                       WHERE p.id = v.id::int""",
                    to_update,
                    template="(%s, %s, %s)"
                )
                actualizados = len(to_update)

        # ── 4. Bulk INSERT de proveedores nuevos → recuperar sus IDs ─────────
        insertados = 0
        nuevos_ids = {}   # codigo_o_nombre → id
        if to_insert:
            with db.cursor() as cur:
                execute_values(
                    cur,
                    """INSERT INTO proveedores (codigo, nombre, observaciones)
                       VALUES %s
                       ON CONFLICT DO NOTHING
                       RETURNING id, codigo, nombre""",
                    to_insert,
                    template="(%s, %s, %s)",
                    fetch=True
                )
                rows = cur.fetchall()
                for row in rows:
                    k = row["codigo"] or row["nombre"]
                    nuevos_ids[k] = row["id"]
                    insertados += 1

        # Mapear todos los keys a su ID final
        key_to_id = {}
        for key in prov_order:
            p = prov_data[key]
            codigo = p["codigo"]
            if codigo and codigo in existentes:
                key_to_id[key] = existentes[codigo]
            else:
                kid = nuevos_ids.get(codigo) or nuevos_ids.get(p["nombre"])
                if kid:
                    key_to_id[key] = kid

        # ── 5. Reemplazar contactos: DELETE existentes + bulk INSERT nuevos ──
        ids_con_datos = list(key_to_id.values())
        if ids_con_datos:
            with db.cursor() as cur:
                # DELETE en un solo IN (una query)
                cur.execute(
                    "DELETE FROM proveedor_contactos WHERE proveedor_id = ANY(%s)",
                    (ids_con_datos,)
                )

                # Construir todas las filas de contactos a insertar
                contactos_rows = []
                for key in prov_order:
                    pid = key_to_id.get(key)
                    if pid is None:
                        continue
                    for orden, (cn, ct, cm, ce, ep) in enumerate(prov_data[key]["contactos"]):
                        contactos_rows.append((
                            pid,
                            cn or None,
                            ct or None,
                            cm or None,
                            ce or None,
                            1 if ep else 0,
                            orden
                        ))

                # INSERT en una sola query bulk
                if contactos_rows:
                    execute_values(
                        cur,
                        """INSERT INTO proveedor_contactos
                           (proveedor_id, nombre, telefono, movil, email, es_principal, orden)
                           VALUES %s""",
                        contactos_rows,
                        template="(%s, %s, %s, %s, %s, %s, %s)",
                        page_size=500
                    )

        db.commit()
        return jsonify({"ok": True, "insertados": insertados, "actualizados": actualizados, "errores": []})

    except Exception as e:
        import traceback
        log.error(f"importar_proveedores error: {traceback.format_exc()}")
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/proveedores/importar/reset", methods=["POST"])
@login_required
def importar_proveedores_reset():
    """Solo admin: borra todos los proveedores e importa desde el Excel.
    Usa bulk operations para evitar timeouts con listas grandes.
    Total de round-trips a la BD: ~4, independientemente del tamaño del Excel.
    """
    if session.get("rol") != "admin":
        return jsonify({"ok": False, "error": "Acceso restringido a administradores"}), 403
    try:
        if "archivo" not in request.files:
            return jsonify({"ok": False, "error": "No se recibió ningún archivo"}), 400
        archivo = request.files["archivo"]
        if not archivo.filename.endswith((".xlsx", ".xls")):
            return jsonify({"ok": False, "error": "El archivo debe ser .xlsx"}), 400

        # ── 1. Parsear Excel completamente en memoria ────────────────────────
        prov_order, prov_data = _parse_excel_proveedores(archivo)

        from psycopg2.extras import execute_values
        db = get_db()

        with db.cursor() as cur:
            # ── 2. Limpiar todo de una vez (3 queries) ───────────────────────
            cur.execute("UPDATE pedidos SET proveedor_id = NULL WHERE proveedor_id IS NOT NULL")
            cur.execute("DELETE FROM proveedor_contactos")
            cur.execute("DELETE FROM proveedores")

            # ── 3. Bulk INSERT proveedores → recuperar IDs en un paso ────────
            prov_rows = [
                (prov_data[k]["codigo"] or None, prov_data[k]["nombre"], prov_data[k]["observaciones"])
                for k in prov_order
            ]
            execute_values(
                cur,
                "INSERT INTO proveedores (codigo, nombre, observaciones) VALUES %s RETURNING id, codigo, nombre",
                prov_rows,
                template="(%s, %s, %s)",
                page_size=500,
                fetch=True
            )
            inserted_rows = cur.fetchall()

            # Mapear codigo/nombre → id preservando el orden
            key_to_id = {}
            for row in inserted_rows:
                k = row["codigo"] or row["nombre"]
                key_to_id[k] = row["id"]

            # ── 4. Bulk INSERT de todos los contactos ────────────────────────
            contactos_rows = []
            for key in prov_order:
                pid = key_to_id.get(key)
                if pid is None:
                    continue
                for orden, (cn, ct, cm, ce, ep) in enumerate(prov_data[key]["contactos"]):
                    contactos_rows.append((
                        pid,
                        cn or None,
                        ct or None,
                        cm or None,
                        ce or None,
                        1 if ep else 0,
                        orden
                    ))

            if contactos_rows:
                execute_values(
                    cur,
                    """INSERT INTO proveedor_contactos
                       (proveedor_id, nombre, telefono, movil, email, es_principal, orden)
                       VALUES %s""",
                    contactos_rows,
                    template="(%s, %s, %s, %s, %s, %s, %s)",
                    page_size=500
                )

        db.commit()
        insertados = len(prov_order)
        return jsonify({"ok": True, "insertados": insertados, "actualizados": 0, "errores": []})

    except Exception as e:
        import traceback
        log.error(f"importar_proveedores_reset error: {traceback.format_exc()}")
        return jsonify({"ok": False, "error": str(e)}), 500


# ── Validación techo de gastos ─────────────────────────────────────────────────
# Nota: los valores de techo (techo_max_pedido, techo_max_mes, techo_max_pedidos)
# se leen siempre desde get_config() → BD. No se asignan aquí para no llamar
# a get_config() fuera de contexto Flask (rompe el arranque en Render).

def _check_techo(hotel_id, familia_id, importe, mes_str, excluir_pedido_id=None):
    """
    Comprueba las reglas del techo de gastos para un pedido nuevo o editado.
    mes_str: 'YYYY-MM'  (mes natural del pedido, normalmente el actual)
    excluir_pedido_id: al editar, excluimos el propio pedido del conteo.

    Devuelve lista de strings con los errores detectados (vacía = OK).
    """
    cfg     = get_config()
    errores = []

    if importe and float(importe) > cfg["techo_max_pedido"]:
        lim = cfg["techo_max_pedido"]
        errores.append(
            f"⚠️ El importe {float(importe):,.2f} € supera el límite individual de {lim:,.0f} € por pedido."
        )

    if not familia_id:
        return errores   # sin familia no hay más que comprobar

    year, month = map(int, mes_str.split("-"))

    excl_clause = "AND p.id != %s" if excluir_pedido_id else ""
    excl_args   = (excluir_pedido_id,) if excluir_pedido_id else ()

    # Pedidos sujetos al techo en este hotel/mes
    base_args = (hotel_id, year, month) + excl_args
    sql = (
        "SELECT p.id, p.familia_id, f.nombre as familia_nombre, "
        "COALESCE(p.importe, 0) as importe "
        "FROM pedidos p "
        "LEFT JOIN familias f ON p.familia_id = f.id "
        "WHERE p.hotel_id = %s "
        "  AND p.sujeto_techo = 1 "
        "  AND p.estado NOT IN ('CANCELADO') "
        "  AND EXTRACT(YEAR  FROM p.creado_en) = %s "
        "  AND EXTRACT(MONTH FROM p.creado_en) = %s "
        + ("  " + excl_clause if excl_clause else "")
    )
    pedidos_mes = rows_to_list(query(sql, base_args))

    # Regla 1: máximo N pedidos sujetos al techo por hotel/mes
    max_pedidos = cfg["techo_max_pedidos"]
    if len(pedidos_mes) >= max_pedidos:
        errores.append(
            f"🚫 Ya hay {len(pedidos_mes)} pedido(s) sujeto(s) al techo este mes para este hotel "
            f"(máximo {max_pedidos})."
        )

    # Regla 2: no puede repetirse la familia en el mismo hotel/mes
    familias_usadas = [p["familia_id"] for p in pedidos_mes]
    if int(familia_id) in familias_usadas:
        familia_row = query("SELECT nombre FROM familias WHERE id=%s", (familia_id,), one=True)
        fname = familia_row["nombre"] if familia_row else "ID {}".format(familia_id)
        errores.append(
            f"🚫 Ya existe un pedido de la familia \u00ab{fname}\u00bb este mes para este hotel. "
            f"Cada familia solo puede usarse una vez al mes por hotel."
        )

    # Regla 3: acumulado mensual no puede superar el techo mensual
    techo_mes     = cfg["techo_max_mes"]
    acumulado     = sum(float(p["importe"]) for p in pedidos_mes)
    nuevo_importe = float(importe) if importe else 0.0
    if acumulado + nuevo_importe > techo_mes:
        errores.append(
            f"⚠️ El acumulado del mes sería {acumulado + nuevo_importe:,.2f} € "
            f"(actual {acumulado:,.2f} € + nuevo {nuevo_importe:,.2f} €), "
            f"superando el techo mensual de {techo_mes:,.0f} €."
        )

    return errores

@app.route("/api/techo/resumen")
@login_required
def techo_resumen():
    """Devuelve el resumen del techo de gastos del mes actual por hotel.

    Versión optimizada: 2 queries fijas (hoteles + pedidos del mes en un solo
    SELECT) en lugar del patrón N+1 anterior (1 query por hotel).
    get_config() se lee una sola vez y sus valores se reutilizan para todos
    los hoteles.
    """
    if session.get("rol") == "hotel":
        return jsonify({"error": "Sin permisos"}), 403
    from datetime import date
    hoy   = date.today()
    year  = hoy.year
    month = hoy.month

    # ── 1. Configuración: una sola lectura ───────────────────────────────────
    cfg              = get_config()
    techo_max_mes    = cfg["techo_max_mes"]
    techo_max_pedido = cfg["techo_max_pedido"]
    techo_max_ped_n  = cfg["techo_max_pedidos"]   # max numero de pedidos
    pct_amarillo     = cfg["techo_pct_amarillo"]
    umbral_amarillo  = techo_max_mes * pct_amarillo / 100

    # ── 2. Hoteles activos: una query ────────────────────────────────────────
    hoteles = rows_to_list(query(
        "SELECT id, codigo, nombre FROM hoteles WHERE activo=1 ORDER BY codigo"
    ))
    if not hoteles:
        return jsonify({"mes": f"{year}-{month:02d}", "hoteles": []})

    hotel_ids = [h["id"] for h in hoteles]
    ph        = ",".join(["%s"] * len(hotel_ids))

    # ── 3. Pedidos del mes: una sola query para todos los hoteles ────────────
    pedidos_mes = rows_to_list(query(f"""
        SELECT p.id, p.hotel_id, p.importe, p.familia_id,
               f.nombre  AS familia_nombre,
               p.pedido_num, p.estado, p.norden,
               pr.nombre AS proveedor_nombre,
               p.observaciones
        FROM pedidos p
        LEFT JOIN familias    f  ON p.familia_id    = f.id
        LEFT JOIN proveedores pr ON p.proveedor_id  = pr.id
        WHERE p.hotel_id IN ({ph})
          AND p.sujeto_techo = 1
          AND p.estado NOT IN ('CANCELADO')
          AND EXTRACT(YEAR  FROM p.creado_en) = %s
          AND EXTRACT(MONTH FROM p.creado_en) = %s
        ORDER BY p.hotel_id, p.creado_en
    """, hotel_ids + [year, month]))

    # ── 4. Agrupar pedidos por hotel en memoria ──────────────────────────────
    from collections import defaultdict
    pedidos_por_hotel: dict = defaultdict(list)
    for p in pedidos_mes:
        pedidos_por_hotel[p["hotel_id"]].append(p)

    # ── 5. Construir resultado ────────────────────────────────────────────────
    resultado = []
    for hotel in hoteles:
        pedidos         = pedidos_por_hotel[hotel["id"]]
        acumulado       = sum(float(p["importe"] or 0) for p in pedidos)
        num_pedidos     = len(pedidos)
        familias_usadas = [p["familia_nombre"] for p in pedidos if p["familia_nombre"]]

        # Semaforo:
        #   ROJO     -> acumulado >= techo_max_mes  O  num_pedidos > techo_max_ped_n
        #   AMARILLO -> acumulado >= umbral_amarillo O  num_pedidos >= techo_max_ped_n
        if acumulado >= techo_max_mes or num_pedidos > techo_max_ped_n:
            semaforo = "rojo"
        elif acumulado >= umbral_amarillo or num_pedidos >= techo_max_ped_n:
            semaforo = "amarillo"
        else:
            semaforo = "verde"

        resultado.append({
            "hotel_id":        hotel["id"],
            "hotel_codigo":    hotel["codigo"],
            "hotel_nombre":    hotel["nombre"],
            "num_pedidos":     num_pedidos,
            "max_pedidos":     techo_max_ped_n,
            "acumulado":       acumulado,
            "techo_mes":       techo_max_mes,
            "techo_pedido":    techo_max_pedido,
            "familias_usadas": familias_usadas,
            "semaforo":        semaforo,
            "pedidos":         pedidos,
        })

    return jsonify({"mes": f"{year}-{month:02d}", "hoteles": resultado})

@app.route("/api/techo/resumen-historico")
@login_required
def techo_resumen_historico():
    """Devuelve el techo de gastos de un mes/año concreto, solo pedidos ENVIADO AL PROVEEDOR.

    Versión optimizada: 2 queries fijas (hoteles + pedidos del mes en un solo
    SELECT con COALESCE de fecha) en lugar del patrón N+1 anterior.
    get_config() se lee una sola vez. El filtro de mes/año se aplica en SQL
    con DATE_TRUNC, evitando traer todos los pedidos a Python para filtrar.
    """
    if session.get("rol") == "hotel":
        return jsonify({"error": "Sin permisos"}), 403

    try:
        year  = int(request.args.get("year",  0))
        month = int(request.args.get("month", 0))
        if not (2020 <= year <= 2099 and 1 <= month <= 12):
            return jsonify({"error": "Parámetros year/month inválidos"}), 400
    except (TypeError, ValueError):
        return jsonify({"error": "Parámetros year/month inválidos"}), 400

    # ── 1. Configuración: una sola lectura ───────────────────────────────────
    cfg              = get_config()
    techo_max_mes    = cfg["techo_max_mes"]
    techo_max_pedido = cfg["techo_max_pedido"]
    techo_max_ped_n  = cfg["techo_max_pedidos"]
    pct_amarillo     = cfg["techo_pct_amarillo"]
    umbral_amarillo  = techo_max_mes * pct_amarillo / 100

    # ── 2. Hoteles activos: una query ────────────────────────────────────────
    hoteles = rows_to_list(query(
        "SELECT id, codigo, nombre FROM hoteles WHERE activo=1 ORDER BY codigo"
    ))
    if not hoteles:
        return jsonify({"mes": f"{year}-{month:02d}", "hoteles": [], "historico": True})

    hotel_ids = [h["id"] for h in hoteles]
    ph        = ",".join(["%s"] * len(hotel_ids))

    # ── 3. Pedidos del mes histórico: una sola query para todos los hoteles ──
    # La fecha de referencia es cuándo pasó a ENVIADO AL PROVEEDOR (historial),
    # con fallback a fecha_tramitacion y por último a creado_en.
    # DATE_TRUNC filtra en BD; no se trae ningún pedido de otros meses a Python.
    pedidos_mes = rows_to_list(query(f"""
        SELECT p.id, p.hotel_id, p.importe, p.familia_id,
               f.nombre  AS familia_nombre,
               p.pedido_num, p.estado, p.norden,
               pr.nombre AS proveedor_nombre,
               p.observaciones,
               COALESCE(
                   (SELECT hs.creado_en FROM historial_estados hs
                    WHERE hs.pedido_id = p.id
                      AND hs.estado_nuevo = 'ENVIADO AL PROVEEDOR'
                    ORDER BY hs.creado_en DESC LIMIT 1),
                   p.fecha_tramitacion::timestamptz,
                   p.creado_en
               ) AS fecha_envio
        FROM pedidos p
        LEFT JOIN familias    f  ON p.familia_id   = f.id
        LEFT JOIN proveedores pr ON p.proveedor_id = pr.id
        WHERE p.hotel_id IN ({ph})
          AND p.sujeto_techo = 1
          AND p.estado = 'ENVIADO AL PROVEEDOR'
          AND DATE_TRUNC('month', COALESCE(
                  (SELECT hs2.creado_en FROM historial_estados hs2
                   WHERE hs2.pedido_id = p.id
                     AND hs2.estado_nuevo = 'ENVIADO AL PROVEEDOR'
                   ORDER BY hs2.creado_en DESC LIMIT 1),
                  p.fecha_tramitacion::timestamptz,
                  p.creado_en
              )) = DATE_TRUNC('month', MAKE_DATE(%s, %s, 1)::timestamptz)
        ORDER BY p.hotel_id, fecha_envio
    """, hotel_ids + [year, month]))

    # ── 4. Agrupar por hotel en memoria ──────────────────────────────────────
    from collections import defaultdict
    pedidos_por_hotel: dict = defaultdict(list)
    for p in pedidos_mes:
        pedidos_por_hotel[p["hotel_id"]].append(p)

    # ── 5. Construir resultado ────────────────────────────────────────────────
    resultado = []
    for hotel in hoteles:
        pedidos         = pedidos_por_hotel[hotel["id"]]
        acumulado       = sum(float(p["importe"] or 0) for p in pedidos)
        num_pedidos     = len(pedidos)
        familias_usadas = [p["familia_nombre"] for p in pedidos if p["familia_nombre"]]

        if acumulado >= techo_max_mes or num_pedidos > techo_max_ped_n:
            semaforo = "rojo"
        elif acumulado >= umbral_amarillo or num_pedidos >= techo_max_ped_n:
            semaforo = "amarillo"
        else:
            semaforo = "verde"

        resultado.append({
            "hotel_id":        hotel["id"],
            "hotel_codigo":    hotel["codigo"],
            "hotel_nombre":    hotel["nombre"],
            "num_pedidos":     num_pedidos,
            "max_pedidos":     techo_max_ped_n,
            "acumulado":       acumulado,
            "techo_mes":       techo_max_mes,
            "techo_pedido":    techo_max_pedido,
            "familias_usadas": familias_usadas,
            "semaforo":        semaforo,
            "pedidos":         pedidos,
        })

    return jsonify({"mes": f"{year}-{month:02d}", "hoteles": resultado, "historico": True})


# ── API Pedidos ────────────────────────────────────────────────────────────────

# ── Lógica de clasificación de alertas — fuente única de verdad ──────────────
#
# Tres consumidores usaban copias idénticas de esta lógica:
#   • /api/stats        (bloque rol=hotel)
#   • /api/stats        (bloque resto de roles)
#   • /api/bridge/alertas
#
# Extraída aquí para que cualquier cambio de umbral o regla se aplique
# en los tres sitios sin riesgo de desincronización.
# ─────────────────────────────────────────────────────────────────────────────

from datetime import date as _date_alerta, datetime as _dt_alerta


def _dias_desde_alerta(fecha_str) -> int | None:
    """Días transcurridos desde fecha_str hasta hoy. None si no parseable."""
    if not fecha_str:
        return None
    try:
        if hasattr(fecha_str, "date"):
            f = fecha_str.date()
        elif isinstance(fecha_str, _date_alerta):
            f = fecha_str
        else:
            f = _dt_alerta.strptime(str(fecha_str)[:10], "%Y-%m-%d").date()
        return (_date_alerta.today() - f).days
    except Exception:
        return None


# Umbrales por estado (días desde fecha de referencia).
# "primera": días mínimos para emitir aviso.
# "urgente": días para escalar a urgente (None = nunca).
# "ciclo":   cada cuántos días se reavisa (no usado en clasificación actual).
# "fecha_ref": campo de fecha a usar (default "fecha_tramitacion").
_UMBRALES_ALERTAS: dict = {
    "ENVIADO AL PROVEEDOR":              {"primera": 15, "urgente": 25, "ciclo": 10},
    "PENDIENTE FIRMA DIRECCION COMPRAS": {"primera": 8,  "urgente": None, "ciclo": 8},
    "PENDIENTE DE FIRMA DIRECCION HOTEL":{"primera": 5,  "urgente": None, "ciclo": 5},
    "ENTREGA PARCIAL":                   {"primera": 10, "urgente": None, "ciclo": 10},
    "PENDIENTE COTIZACIÓN":              {"primera": 2,  "urgente": 3, "ciclo": None,
                                          "fecha_ref": "fecha_solicitud"},
}


def _clasificar_alertas(pedidos_raw: list, cfg_activar_plazo: bool) -> list:
    """Clasifica una lista de pedidos y devuelve solo los que generan alerta.

    Para cada pedido:
      1. Si tiene plazo_entrega_dias y cfg_activar_plazo=True, aplica la
         lógica de _alertas_plazo_entrega (fecha de entrega esperada).
      2. Si no, aplica la lógica estándar de _UMBRALES_ALERTAS.

    Añade a cada pedido:
      • dias_tramitacion  (int)
      • nivel_alerta      ("aviso" | "urgente")
      • fecha_entrega_prevista (str ISO o None)

    Devuelve la lista ordenada: urgentes primero, luego por días descendente.
    """
    alertas: list = []
    for p in pedidos_raw:
        # ── Lógica plazo de entrega ──────────────────────────────────────
        info_plazo = _alertas_plazo_entrega(p, cfg_activar_plazo)
        if info_plazo:
            dias = _dias_desde_alerta(p.get("fecha_tramitacion")) or 0
            p["dias_tramitacion"]      = dias
            p["nivel_alerta"]          = info_plazo["nivel"]
            fep = info_plazo["fecha_entrega_prevista"]
            p["fecha_entrega_prevista"] = fep.strftime("%Y-%m-%d") if fep else None
            alertas.append(p)
            continue
        # ── Lógica estándar ─────────────────────────────────────────────
        cfg = _UMBRALES_ALERTAS.get(p["estado"])
        if not cfg:
            continue
        fecha_ref_campo = cfg.get("fecha_ref", "fecha_tramitacion")
        dias = _dias_desde_alerta(p.get(fecha_ref_campo))
        if dias is None or dias < cfg["primera"]:
            continue
        nivel = "urgente" if (cfg["urgente"] and dias >= cfg["urgente"]) else "aviso"
        p["dias_tramitacion"]      = dias
        p["nivel_alerta"]          = nivel
        p["fecha_entrega_prevista"] = None
        alertas.append(p)

    alertas.sort(key=lambda x: (0 if x["nivel_alerta"] == "urgente" else 1,
                                 -x["dias_tramitacion"]))
    return alertas


# ── Selector reducido para /api/stats (alertas del dashboard) ────────────────
# Solo los campos que loadAlertas() y updateAlertBadge() consumen.
# Sin subconsultas a proveedor_contactos — esos datos solo hacen falta al
# abrir el modal de email/telegram de una alerta concreta (usa PEDIDO_SELECT_ALERTA).
PEDIDO_SELECT_STATS = """
    SELECT p.id, p.norden, p.pedido_num, p.estado,
           p.fecha_tramitacion, p.fecha_solicitud,
           p.plazo_entrega_dias, p.observaciones, p.importe,
           h.codigo  as hotel_codigo,
           h.nombre  as hotel_nombre,
           d.nombre  as departamento_nombre,
           pr.nombre as proveedor_nombre,
           f.nombre  as familia_nombre,
           EXISTS (
               SELECT 1 FROM pedido_adjuntos pa WHERE pa.pedido_id = p.id
           ) AS has_adjuntos
    FROM pedidos p
    LEFT JOIN hoteles       h  ON p.hotel_id        = h.id
    LEFT JOIN departamentos d  ON p.departamento_id = d.id
    LEFT JOIN proveedores   pr ON p.proveedor_id    = pr.id
    LEFT JOIN familias      f  ON p.familia_id      = f.id
"""

PEDIDO_SELECT = """
    SELECT p.*,
           h.codigo  as hotel_codigo,
           h.nombre  as hotel_nombre,
           d.nombre  as departamento_nombre,
           pr.nombre as proveedor_nombre,
           (SELECT email FROM proveedor_contactos WHERE proveedor_id=pr.id AND email IS NOT NULL AND email!='' AND es_principal=1 LIMIT 1) as proveedor_email,
                  (SELECT COALESCE(NULLIF(movil,''), NULLIF(telefono,'')) FROM proveedor_contactos WHERE proveedor_id=pr.id AND es_principal=1 LIMIT 1) as proveedor_movil,
                  (SELECT nombre FROM proveedor_contactos WHERE proveedor_id=pr.id AND es_principal=1 LIMIT 1) as proveedor_contacto_nombre,
           (SELECT telefono FROM proveedor_contactos WHERE proveedor_id=pr.id AND telefono IS NOT NULL AND telefono!='' ORDER BY orden,id LIMIT 1) as proveedor_telefono,
           (SELECT nombre FROM proveedor_contactos WHERE proveedor_id=pr.id ORDER BY orden,id LIMIT 1) as proveedor_contacto,
           COALESCE(p.creado_por_nombre,    u1.nombre) as creado_por_nombre,
           COALESCE(p.modificado_por_nombre, u2.nombre) as modificado_por_nombre,
           f.nombre  as familia_nombre,
           EXISTS (
               SELECT 1 FROM pedido_adjuntos pa WHERE pa.pedido_id = p.id
           ) AS has_adjuntos
    FROM pedidos p
    LEFT JOIN hoteles       h  ON p.hotel_id          = h.id
    LEFT JOIN departamentos d  ON p.departamento_id   = d.id
    LEFT JOIN proveedores   pr ON p.proveedor_id      = pr.id
    LEFT JOIN usuarios      u1 ON p.creado_por_id     = u1.id
    LEFT JOIN usuarios      u2 ON p.modificado_por_id = u2.id
    LEFT JOIN familias      f  ON p.familia_id        = f.id
"""

@app.route("/api/pedidos")
@login_required
def get_pedidos():
    wheres, args = [], []

    # Restricción por rol hotel: solo ve sus hoteles asignados
    if session.get("rol") == "hotel":
        hoteles_ids = session.get("hoteles_ids", [])
        if not hoteles_ids:
            return jsonify({"pedidos": [], "total": 0, "page": 1, "page_size": 20, "pages": 1})
        placeholders = ",".join(["%s"] * len(hoteles_ids))
        wheres.append(f"p.hotel_id IN ({placeholders})")
        args += hoteles_ids

    q           = request.args.get("q", "").strip()
    hotel       = request.args.get("hotel_id", "")
    estado      = request.args.get("estado", "")
    depto       = request.args.get("departamento_id", "")
    alerta      = request.args.get("alerta", "")
    fecha_desde = request.args.get("fecha_desde", "").strip()
    fecha_hasta = request.args.get("fecha_hasta", "").strip()

    if q:
        wheres.append("(p.pedido_num ILIKE %s OR pr.nombre ILIKE %s OR p.observaciones ILIKE %s OR h.codigo ILIKE %s)")
        args += [f"%{q}%"] * 4
    if hotel:
        wheres.append("p.hotel_id = %s"); args.append(hotel)
    if estado:
        wheres.append("p.estado = %s"); args.append(estado)
    if depto:
        wheres.append("p.departamento_id = %s"); args.append(depto)
    if fecha_desde:
        wheres.append("p.fecha_solicitud >= %s"); args.append(fecha_desde)
    if fecha_hasta:
        wheres.append("p.fecha_solicitud <= %s"); args.append(fecha_hasta)
    if alerta == "1":
        # Filtro rápido: pedidos con fecha_tramitacion y estado activo
        # (el cálculo exacto de días y nivel se hace en /api/stats)
        wheres.append("""
            p.estado IN ('ENVIADO AL PROVEEDOR','PENDIENTE FIRMA DIRECCION COMPRAS',
                         'PENDIENTE DE FIRMA DIRECCION HOTEL','ENTREGA PARCIAL')
            AND p.fecha_tramitacion IS NOT NULL
        """)

    where_sql = ("WHERE " + " AND ".join(wheres)) if wheres else ""

    order_map = {
        "fecha_desc": "p.creado_en DESC",
        "fecha_asc":  "p.creado_en ASC",
        "estado":     "p.estado, p.creado_en DESC",
        "hotel":      "h.codigo, p.creado_en DESC",
    }
    order = order_map.get(request.args.get("orden", ""), "p.norden DESC")

    try:
        page      = max(1, int(request.args.get("page", 1)))
        page_size = max(1, min(100, int(request.args.get("page_size", 20))))
    except ValueError:
        page, page_size = 1, 20

    count_sql = f"""SELECT COUNT(*) as total FROM pedidos p
                    LEFT JOIN hoteles h ON p.hotel_id=h.id
                    LEFT JOIN proveedores pr ON p.proveedor_id=pr.id {where_sql}"""
    total = query(count_sql, args, one=True)["total"]

    sql     = f"{PEDIDO_SELECT} {where_sql} ORDER BY {order} LIMIT %s OFFSET %s"
    pedidos = rows_to_list(query(sql, args + [page_size, (page - 1) * page_size]))

    return jsonify({
        "pedidos":   pedidos,
        "total":     total,
        "page":      page,
        "page_size": page_size,
        "pages":     max(1, (total + page_size - 1) // page_size),
    })

@app.route("/api/pedidos/<int:pid>")
@login_required
def get_pedido(pid):
    p = row_to_dict(query(f"{PEDIDO_SELECT} WHERE p.id=%s", (pid,), one=True))
    if not p:
        return jsonify({"error": "No encontrado"}), 404
    historial = rows_to_list(query(
        """SELECT h.*, COALESCE(h.usuario_nombre, u.nombre) as usuario_nombre
           FROM historial_estados h LEFT JOIN usuarios u ON h.usuario_id=u.id
           WHERE h.pedido_id=%s ORDER BY h.creado_en DESC""", (pid,)
    ))
    return jsonify({"pedido": p, "historial": historial})

@app.route("/api/pedidos", methods=["POST"])
@login_required
def create_pedido():
    data   = request.get_json(silent=True) or {}
    db     = get_db()
    uid    = current_user_id()
    norden = _next_norden(db)
    estado = data.get("estado", "PENDIENTE FIRMA DIRECCION COMPRAS")

    sujeto_techo = 1 if data.get("sujeto_techo") else 0
    familia_id   = data.get("familia_id") or None
    importe      = data.get("importe") or None

    # Validación techo de gastos
    if sujeto_techo and not data.get("_forzar_techo"):
        from datetime import date
        mes_str = date.today().strftime("%Y-%m")
        errores = _check_techo(data.get("hotel_id"), familia_id, importe, mes_str)
        if errores:
            return jsonify({"ok": False, "techo_errores": errores}), 422

    cur = execute("""
        INSERT INTO pedidos (
            norden, hotel_id, departamento_id,
            fecha_solicitud, fecha_envio_visto_bueno, fecha_tramitacion,
            pedido_num, presupuesto_num, entrada_albaran_num,
            tarifa_acordada,
            estado, comunicado_ab, comunicado_jefe_dep,
            parte_rotura, parte_ampliacion,
            proveedor_id, observaciones,
            familia_id, importe, sujeto_techo,
            plazo_entrega_dias,
            creado_por_id, modificado_por_id,
            creado_por_nombre, modificado_por_nombre
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        RETURNING id
    """, (
        norden,
        data.get("hotel_id"), data.get("departamento_id"),
        data.get("fecha_solicitud"), data.get("fecha_envio_visto_bueno"),
        data.get("fecha_tramitacion"),
        data.get("pedido_num"), data.get("presupuesto_num"),
        data.get("entrada_albaran_num"),
        bool(data.get("tarifa_acordada")),
        estado,
        1 if data.get("comunicado_ab") else 0,
        1 if data.get("comunicado_jefe_dep") else 0,
        1 if data.get("parte_rotura") else 0,
        1 if data.get("parte_ampliacion") else 0,
        data.get("proveedor_id"), data.get("observaciones"),
        familia_id, importe, sujeto_techo,
        data.get("plazo_entrega_dias") or None,
        uid, uid,
        session.get("nombre"), session.get("nombre"),
    ))
    pedido_id = cur.fetchone()["id"]

    execute(
        "INSERT INTO historial_estados (pedido_id,estado_nuevo,usuario_id,usuario_nombre,nota) VALUES (%s,%s,%s,%s,%s)",
        (pedido_id, estado, uid, session.get("nombre"), "Pedido creado")
    )
    db.commit()

    _pendientes_email = enviar_emails_estado(db, pedido_id, estado)

    # ── Telegram inmediato si el pedido está sujeto al techo de gastos ────────
    if sujeto_techo:
        nombre_familia = None
        if familia_id:
            row_f = query("SELECT nombre FROM familias WHERE id=%s", (familia_id,), one=True)
            nombre_familia = row_f["nombre"] if row_f else None
        hotel_codigo = query("SELECT codigo FROM hoteles WHERE id=%s", (data.get("hotel_id"),), one=True)
        hotel_cod = hotel_codigo["codigo"] if hotel_codigo else ""
        _telegram_alerta_techo(pedido_id, hotel_cod, float(importe or 0), nombre_familia or "—")

    return jsonify({"ok": True, "id": pedido_id, "norden": norden, "emails_pendientes": _pendientes_email}), 201

@app.route("/api/pedidos/<int:pid>", methods=["PUT"])
@login_required
def update_pedido(pid):
    data = request.get_json(silent=True) or {}
    db   = get_db()
    uid  = current_user_id()

    pedido_actual = row_to_dict(query("SELECT * FROM pedidos WHERE id=%s", (pid,), one=True))
    if not pedido_actual:
        return jsonify({"error": "No encontrado"}), 404

    # ── Restricción rol hotel: solo puede modificar entrada_albaran_num, sin CANCELADO ──
    if session.get("rol") == "hotel":
        hoteles_ids = session.get("hoteles_ids", [])
        if pedido_actual["hotel_id"] not in hoteles_ids:
            return jsonify({"error": "Sin acceso a este pedido"}), 403
        # Solo permitir campos de albarán; ignorar todo lo demás
        albaran_val = data.get("entrada_albaran_num", pedido_actual["entrada_albaran_num"])
        # Determinar estado: SERVIDO PARCIAL / TOTAL según albarán, pero nunca CANCELADO
        estado_solicitado = data.get("estado", pedido_actual["estado"])
        if estado_solicitado == "CANCELADO":
            return jsonify({"error": "El usuario Hotel no puede cancelar pedidos"}), 403
        execute("""
            UPDATE pedidos SET
                entrada_albaran_num=%s, estado=%s,
                modificado_por_id=%s, modificado_por_nombre=%s, modificado_en=NOW()
            WHERE id=%s
        """, (albaran_val, estado_solicitado, uid, session.get("nombre"), pid))
        estado_antes = pedido_actual["estado"]
        if estado_solicitado != estado_antes:
            execute(
                "INSERT INTO historial_estados (pedido_id,estado_antes,estado_nuevo,usuario_id,usuario_nombre,nota) VALUES (%s,%s,%s,%s,%s,%s)",
                (pid, estado_antes, estado_solicitado, uid, session.get("nombre"), data.get("nota_historial", ""))
            )
        db.commit()
        _pendientes_email = []
        if estado_solicitado != estado_antes:
            _pendientes_email = _notificar_cambio_estado(
                db,
                pid,
                estado_solicitado,
                estado_antes,
                usuario_nombre=session.get("nombre", ""),
            )
        return jsonify({"ok": True, "id": pid, "emails_pendientes": _pendientes_email})
    # ── Fin restricción hotel ──────────────────────────────────────────────────

    estado_antes = pedido_actual["estado"]
    estado_nuevo = data.get("estado", estado_antes)

    sujeto_techo = data.get("sujeto_techo", pedido_actual.get("sujeto_techo", 0))
    sujeto_techo = 1 if sujeto_techo else 0
    familia_id   = data.get("familia_id", pedido_actual.get("familia_id"))
    importe      = data.get("importe", pedido_actual.get("importe"))

    # Validación techo si está sujeto
    if sujeto_techo and not data.get("_forzar_techo"):
        from datetime import date
        mes_str = date.today().strftime("%Y-%m")
        hotel_id = data.get("hotel_id", pedido_actual["hotel_id"])
        errores = _check_techo(hotel_id, familia_id, importe, mes_str, excluir_pedido_id=pid)
        if errores:
            return jsonify({"ok": False, "techo_errores": errores}), 422

    # ── Validación obligatoria para ENVIADO AL PROVEEDOR ─────────────────────
    if estado_nuevo == "ENVIADO AL PROVEEDOR" and estado_antes != "ENVIADO AL PROVEEDOR":
        errores_envio = []

        # 0a. Proveedor asignado obligatorio
        proveedor_id_val = data.get("proveedor_id", pedido_actual.get("proveedor_id"))
        if not proveedor_id_val:
            errores_envio.append(
                "No se puede pasar a ENVIADO AL PROVEEDOR porque el pedido no tiene proveedor asignado. "
                "Asigne un proveedor antes de cambiar el estado."
            )
        else:
            # 0b. El proveedor debe tener al menos un contacto principal con email
            emails_proveedor = _get_proveedor_emails_principales(proveedor_id_val)
            if not emails_proveedor:
                # Obtener el nombre del proveedor para dar un mensaje más claro
                prov_row = query("SELECT nombre FROM proveedores WHERE id=%s", (proveedor_id_val,), one=True)
                prov_nombre = (prov_row["nombre"] if prov_row else f"ID {proveedor_id_val}")
                errores_envio.append(
                    f"El proveedor «{prov_nombre}» no tiene ningún correo electrónico configurado en su ficha "
                    f"(contacto principal con email). Acceda a la ficha del proveedor, añada un email al contacto "
                    f"principal y vuelva a cambiar el estado."
                )

        if errores_envio:
            return jsonify({"ok": False, "error": " | ".join(errores_envio), "errores": errores_envio}), 422

        # 1. Nº Pedido (DALI/SAP) obligatorio
        pedido_num_val = data.get("pedido_num", pedido_actual.get("pedido_num") or "")
        if not (pedido_num_val or "").strip():
            errores_envio.append("El campo «Nº Pedido (DALI/SAP)» es obligatorio para pasar a ENVIADO AL PROVEEDOR.")

        # 2. Adjunto pedido_doc: máximo 1 documento (PDF/Word, obligatorio)
        #    y máximo 1 correo electrónico (opcional) — pueden coexistir ambos.
        adjuntos_pedido = rows_to_list(query(
            "SELECT id, nombre, es_correo FROM pedido_adjuntos WHERE pedido_id=%s AND tipo='pedido_doc'",
            (pid,)
        ))
        docs_pedido    = [a for a in adjuntos_pedido if not a["es_correo"]]
        correos_pedido = [a for a in adjuntos_pedido if a["es_correo"]]
        if len(docs_pedido) == 0:
            errores_envio.append("Debe adjuntar un documento (PDF/Word) en la sección «Nº Pedido (DALI/SAP)».")
        elif len(docs_pedido) > 1:
            errores_envio.append("Solo se permite un documento (PDF/Word) en la sección «Nº Pedido (DALI/SAP)» (actualmente hay %d)." % len(docs_pedido))
        if len(correos_pedido) > 1:
            errores_envio.append("Solo se permite un correo electrónico en la sección «Nº Pedido (DALI/SAP)» (actualmente hay %d)." % len(correos_pedido))

        # 3. Nº Presupuesto obligatorio (salvo pedidos con tarifa acordada,
        #    que por definición no requieren presupuesto)
        tarifa_acordada_val = data.get("tarifa_acordada", pedido_actual.get("tarifa_acordada", False))
        if not tarifa_acordada_val:
            presupuesto_num_val = data.get("presupuesto_num", pedido_actual.get("presupuesto_num") or "")
            if not (presupuesto_num_val or "").strip():
                errores_envio.append("El campo «Nº Presupuesto» es obligatorio para pasar a ENVIADO AL PROVEEDOR.")

            # 4. Adjunto presupuesto_doc: mínimo 1 documento (puede haber también correos)
            adjuntos_presupuesto = rows_to_list(query(
                "SELECT id, nombre, es_correo FROM pedido_adjuntos WHERE pedido_id=%s AND tipo='presupuesto_doc'",
                (pid,)
            ))
            docs_presupuesto = [a for a in adjuntos_presupuesto if not a["es_correo"]]
            if len(adjuntos_presupuesto) == 0:
                errores_envio.append("Debe adjuntar al menos un documento (PDF/Word) en la sección «Nº Presupuesto».")
            elif len(docs_presupuesto) == 0:
                errores_envio.append("Debe adjuntar al menos un documento (PDF/Word) en «Nº Presupuesto» (solo correo electrónico no es suficiente).")

        if errores_envio:
            return jsonify({"ok": False, "error": " | ".join(errores_envio), "errores": errores_envio}), 422
    # ── Fin validación ENVIADO AL PROVEEDOR ──────────────────────────────────

    ESTADOS_SIN_TRAMITAR = {
        "PENDIENTE FIRMA DIRECCION COMPRAS",
        "PENDIENTE DE FIRMA DIRECCION HOTEL",
    }
    fecha_sol_nueva  = data.get("fecha_solicitud")
    fecha_sol_actual = pedido_actual.get("fecha_solicitud")
    if (
        fecha_sol_nueva
        and not fecha_sol_actual
        and estado_nuevo in ESTADOS_SIN_TRAMITAR
        and "estado" not in data
    ):
        estado_nuevo = "PENDIENTE COTIZACIÓN"

    execute("""
        UPDATE pedidos SET
            hotel_id=%s, departamento_id=%s,
            fecha_solicitud=%s, fecha_envio_visto_bueno=%s, fecha_tramitacion=%s,
            pedido_num=%s, presupuesto_num=%s, entrada_albaran_num=%s,
            tarifa_acordada=%s,
            estado=%s,
            comunicado_ab=%s, comunicado_jefe_dep=%s,
            parte_rotura=%s, parte_ampliacion=%s,
            proveedor_id=%s, observaciones=%s,
            familia_id=%s, importe=%s, sujeto_techo=%s,
            plazo_entrega_dias=%s,
            modificado_por_id=%s, modificado_por_nombre=%s, modificado_en=NOW()
        WHERE id=%s
    """, (
        data.get("hotel_id",            pedido_actual["hotel_id"]),
        data.get("departamento_id",      pedido_actual["departamento_id"]),
        data.get("fecha_solicitud",      pedido_actual["fecha_solicitud"]),
        data.get("fecha_envio_visto_bueno", pedido_actual["fecha_envio_visto_bueno"]),
        data.get("fecha_tramitacion",    pedido_actual["fecha_tramitacion"]),
        data.get("pedido_num",           pedido_actual["pedido_num"]),
        data.get("presupuesto_num",      pedido_actual["presupuesto_num"]),
        data.get("entrada_albaran_num",  pedido_actual["entrada_albaran_num"]),
        bool(data.get("tarifa_acordada", pedido_actual.get("tarifa_acordada", False))),
        estado_nuevo,
        1 if data.get("comunicado_ab",       pedido_actual["comunicado_ab"]) else 0,
        1 if data.get("comunicado_jefe_dep", pedido_actual["comunicado_jefe_dep"]) else 0,
        1 if data.get("parte_rotura",        pedido_actual["parte_rotura"]) else 0,
        1 if data.get("parte_ampliacion",    pedido_actual["parte_ampliacion"]) else 0,
        data.get("proveedor_id",  pedido_actual["proveedor_id"]),
        data.get("observaciones", pedido_actual["observaciones"]),
        familia_id, importe, sujeto_techo,
        data.get("plazo_entrega_dias", pedido_actual.get("plazo_entrega_dias")) or None,
        uid, session.get("nombre"), pid,
    ))

    if estado_nuevo != estado_antes:
        execute(
            "INSERT INTO historial_estados (pedido_id,estado_antes,estado_nuevo,usuario_id,usuario_nombre,nota) VALUES (%s,%s,%s,%s,%s,%s)",
            (pid, estado_antes, estado_nuevo, uid, session.get("nombre"), data.get("nota_historial", ""))
        )

    db.commit()

    _pendientes_email = []
    if estado_nuevo != estado_antes:
        _pendientes_email = _notificar_cambio_estado(db, pid, estado_nuevo, estado_antes,
                                 usuario_nombre=session.get("nombre", ""))

    return jsonify({"ok": True, "emails_pendientes": _pendientes_email})

@app.route("/api/pedidos/<int:pid>", methods=["DELETE"])
@admin_required
def delete_pedido(pid):
    data   = request.get_json(silent=True) or {}
    motivo = (data.get("motivo") or "").strip()
    if not motivo:
        return jsonify({"error": "Debes indicar el motivo de la eliminación"}), 400

    db  = get_db()
    uid = current_user_id()

    # ── 1. Capturar datos completos del pedido antes de borrar ───────────────
    pedido = row_to_dict(query(f"{PEDIDO_SELECT} WHERE p.id=%s", (pid,), one=True))
    if not pedido:
        return jsonify({"error": "Pedido no encontrado"}), 404

    admin_nombre = session.get("nombre", session.get("username", "Desconocido"))

    # ── 2. Guardar registro histórico en pedidos_eliminados ──────────────────
    execute("""
        INSERT INTO pedidos_eliminados (
            pedido_id, norden, hotel_nombre, departamento_nombre,
            proveedor_nombre, proveedor_email, estado,
            fecha_solicitud, pedido_num, presupuesto_num,
            entrada_albaran_num, observaciones, creado_por_nombre,
            motivo_eliminacion, eliminado_por_id, eliminado_por_nombre
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        pid,
        pedido.get("norden"),
        pedido.get("hotel_nombre"),
        pedido.get("departamento_nombre"),
        pedido.get("proveedor_nombre"),
        pedido.get("proveedor_email"),
        pedido.get("estado"),
        pedido.get("fecha_solicitud"),
        pedido.get("pedido_num"),
        pedido.get("presupuesto_num"),
        pedido.get("entrada_albaran_num"),
        pedido.get("observaciones"),
        pedido.get("creado_por_nombre"),
        motivo,
        uid,
        admin_nombre,
    ))

    # ── 3. Eliminar el pedido (CASCADE borra adjuntos e historial) ───────────
    execute("DELETE FROM pedidos WHERE id=%s", (pid,))
    db.commit()
    return jsonify({"ok": True, "norden": pedido.get("norden")})

# ── Registro de pedidos eliminados ────────────────────────────────────────────

@app.route("/api/pedidos_eliminados")
@login_required
def get_pedidos_eliminados():
    if session.get("rol") not in ("admin", "compras"):
        return jsonify({"error": "Acceso restringido"}), 403
    registros = rows_to_list(query(
        "SELECT * FROM pedidos_eliminados ORDER BY eliminado_en DESC"
    ))
    return jsonify({"registros": registros})

# ── API Stats ──────────────────────────────────────────────────────────────────

@app.route("/api/stats")
@login_required
def get_stats():
    # ── Restricción rol hotel: solo sus hoteles asignados, alertas filtradas ──
    if session.get("rol") == "hotel":
        hoteles_ids = session.get("hoteles_ids", [])
        if not hoteles_ids:
            return jsonify({"total": 0, "by_estado": [], "by_hotel": [],
                            "alertas": [], "num_alertas": 0})
        placeholders = ",".join(["%s"] * len(hoteles_ids))
        total = query(
            f"SELECT COUNT(*) as n FROM pedidos WHERE hotel_id IN ({placeholders})",
            hoteles_ids, one=True)["n"]
        by_estado = rows_to_list(query(
            f"SELECT estado, COUNT(*) as total FROM pedidos WHERE hotel_id IN ({placeholders}) GROUP BY estado ORDER BY total DESC",
            hoteles_ids))
        by_hotel = rows_to_list(query(
            f"""SELECT h.codigo, h.nombre, COUNT(p.id) as total
                FROM hoteles h LEFT JOIN pedidos p ON p.hotel_id=h.id
                WHERE h.id IN ({placeholders})
                GROUP BY h.id, h.codigo, h.nombre ORDER BY total DESC""",
            hoteles_ids))
        # Calcular alertas reales para los hoteles visibles del usuario hotel
        alertas_raw_h = rows_to_list(query(f"""
            {PEDIDO_SELECT_STATS}
            WHERE p.estado IN (
                'ENVIADO AL PROVEEDOR',
                'PENDIENTE FIRMA DIRECCION COMPRAS',
                'PENDIENTE DE FIRMA DIRECCION HOTEL',
                'ENTREGA PARCIAL',
                'PENDIENTE COTIZACIÓN'
            )
              AND p.hotel_id IN ({placeholders})
              AND (
                p.fecha_tramitacion IS NOT NULL
                OR (p.estado = 'PENDIENTE COTIZACIÓN' AND p.fecha_solicitud IS NOT NULL)
              )
            ORDER BY p.fecha_tramitacion ASC
        """, hoteles_ids))
        cfg_activar_plazo_h = bool(int(get_config().get("activar_uso_plazo_entrega", 1) or 0))
        alertas_h = _clasificar_alertas(alertas_raw_h, cfg_activar_plazo_h)
        return jsonify({"total": total, "by_estado": by_estado,
                        "by_hotel": by_hotel, "alertas": alertas_h,
                        "num_alertas": len(alertas_h)})
    # ── Resto de roles ────────────────────────────────────────────────────────
    # total se deriva de by_estado: evita un COUNT(*) redundante sobre la tabla.
    by_estado = rows_to_list(query(
        "SELECT estado, COUNT(*) as total FROM pedidos GROUP BY estado ORDER BY total DESC"
    ))
    total = sum(r["total"] for r in by_estado)
    by_hotel  = rows_to_list(query(
        """SELECT h.codigo, h.nombre, COUNT(p.id) as total
           FROM hoteles h LEFT JOIN pedidos p ON p.hotel_id=h.id
           GROUP BY h.id, h.codigo, h.nombre ORDER BY total DESC"""
    ))
    # ── Alertas: clasificadas por _clasificar_alertas (fuente única) ──────────
    alertas_raw = rows_to_list(query(f"""
        {PEDIDO_SELECT_STATS}
        WHERE p.estado IN (
            'ENVIADO AL PROVEEDOR',
            'PENDIENTE FIRMA DIRECCION COMPRAS',
            'PENDIENTE DE FIRMA DIRECCION HOTEL',
            'ENTREGA PARCIAL',
            'PENDIENTE COTIZACIÓN'
        )
          AND (
            p.fecha_tramitacion IS NOT NULL
            OR (p.estado = 'PENDIENTE COTIZACIÓN' AND p.fecha_solicitud IS NOT NULL)
          )
        ORDER BY p.fecha_tramitacion ASC
    """))
    cfg_activar_plazo = bool(int(get_config().get("activar_uso_plazo_entrega", 1) or 0))
    alertas = _clasificar_alertas(alertas_raw, cfg_activar_plazo)

    return jsonify({
        "total": total, "by_estado": by_estado,
        "by_hotel": by_hotel, "alertas": alertas,
        "num_alertas": len(alertas),
    })

# ── API Bridge Agenda — alertas filtradas por usuario (v10.3) ─────────────────
#
# Endpoint consumido por pedidos_agenda_bridge.py en cada instancia de
# main_agenda. Devuelve SOLO las alertas que corresponden al usuario logado:
#
#   rol='compras' → alertas de los hoteles asignados en usuario_comprador_hoteles
#   rol='admin'   → todas las alertas (supervisión global)
#   rol='hotel'   → alertas de los hoteles asignados en usuario_hoteles (lectura)
#
# Misma lógica de umbrales y niveles que /api/stats pero filtrada.
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/bridge/alertas")
@login_required
def bridge_alertas_usuario():
    """
    Devuelve las alertas activas filtradas por el usuario de la sesión.
    Usado por pedidos_agenda_bridge.py para mostrar popups personalizados
    en main_agenda sin mezclar avisos entre compradores.
    """
    from datetime import date as _date, datetime as _dt

    rol      = session.get("rol", "")
    user_id  = session.get("user_id")

    # ── Determinar qué hotel_ids aplican al usuario ───────────────────────────
    if rol == "admin":
        # El admin recibe sus avisos exclusivamente por la cola push
        # (/api/bridge/notificaciones): techo urgente y supervisión de pedidos urgentes.
        # El polling de todos los pedidos en estado alertable es el canal del comprador,
        # no del supervisor. Devolver vacío evita que la agenda del admin muestre
        # el seguimiento diario de cada pedido de todos los hoteles.
        return jsonify({"alertas": [], "num_alertas": 0,
                        "usuario": session.get("username"), "rol": rol})
    elif rol == "compras":
        # Hoteles asignados al comprador en usuario_comprador_hoteles
        rows = rows_to_list(query(
            "SELECT hotel_id FROM usuario_comprador_hoteles WHERE usuario_id=%s",
            (user_id,)
        ))
        hotel_ids = [r["hotel_id"] for r in rows]
        if not hotel_ids:
            return jsonify({"alertas": [], "num_alertas": 0,
                            "usuario": session.get("username"), "rol": rol})
        placeholders = ",".join(["%s"] * len(hotel_ids))
        filtro_hotel_sql = f"AND p.hotel_id IN ({placeholders})"
        filtro_args      = hotel_ids
    elif rol == "hotel":
        # Rol hotel: no accede a la vista de alertas
        return jsonify({"alertas": [], "num_alertas": 0,
                        "usuario": session.get("username"), "rol": rol})
    else:
        # Rol desconocido: sin alertas
        return jsonify({"alertas": [], "num_alertas": 0,
                        "usuario": session.get("username"), "rol": rol})

    # ── Consulta de pedidos en estados alertables ─────────────────────────────
    # Usa PEDIDO_SELECT_STATS (sin subconsultas de proveedor_contactos) y
    # _clasificar_alertas (fuente única de verdad para umbrales y niveles).
    alertas_raw = rows_to_list(query(f"""
        {PEDIDO_SELECT_STATS}
        WHERE p.estado IN (
            'ENVIADO AL PROVEEDOR',
            'PENDIENTE FIRMA DIRECCION COMPRAS',
            'PENDIENTE DE FIRMA DIRECCION HOTEL',
            'ENTREGA PARCIAL',
            'PENDIENTE COTIZACIÓN'
        )
          AND (
            p.fecha_tramitacion IS NOT NULL
            OR (p.estado = 'PENDIENTE COTIZACIÓN' AND p.fecha_solicitud IS NOT NULL)
          )
          {filtro_hotel_sql}
        ORDER BY p.fecha_tramitacion ASC
    """, filtro_args))
    cfg_activar_plazo_bridge = bool(int(get_config().get("activar_uso_plazo_entrega", 1) or 0))
    alertas = _clasificar_alertas(alertas_raw, cfg_activar_plazo_bridge)

    return jsonify({
        "alertas":     alertas,
        "num_alertas": len(alertas),
        "usuario":     session.get("username"),
        "nombre":      session.get("nombre"),
        "rol":         rol,
    })


# ── API Bridge: cola de notificaciones push (v10.7.7) ────────────────────────

@app.route("/api/bridge/notificaciones", methods=["GET"])
@login_required
def bridge_notificaciones_usuario():
    """
    Devuelve las notificaciones pendientes (no leídas) para el usuario de la sesión
    y las marca como leídas en la misma transacción.

    Garantiza paridad total con Telegram: cada vez que se envía un Telegram a un
    comprador o admin, se encola una fila en bridge_notificaciones para que
    main_agenda la reciba como popup inmediato.

    Respuesta:
    {
        "notificaciones": [
            {
                "id": 42,
                "tipo": "cambio_estado",      -- 'cambio_estado'|'alerta_auto'|'techo'|'supervision'
                "pedido_id": 123,             -- puede ser null
                "titulo": "...",
                "mensaje": "...",
                "nivel": "urgente",           -- 'aviso'|'urgente'
                "creado_en": "2026-05-25T..."
            }, ...
        ],
        "total": 3,
        "usuario": "comprador1",
        "rol": "compras"
    }
    """
    usuario  = session.get("username", "").lower()
    rol      = session.get("rol", "")

    try:
        rows = rows_to_list(query(
            """SELECT id, tipo, pedido_id, titulo, mensaje, nivel, creado_en
               FROM bridge_notificaciones
               WHERE usuario = %s AND leido = FALSE
               ORDER BY creado_en ASC""",
            (usuario,)
        ))
    except Exception as exc:
        log.warning("bridge_notif GET: error leyendo notificaciones — %s", exc)
        return jsonify({"notificaciones": [], "total": 0, "usuario": usuario, "rol": rol})

    if rows:
        ids = [r["id"] for r in rows]
        placeholders = ",".join(["%s"] * len(ids))
        try:
            db = get_db()
            db.cursor().execute(
                f"UPDATE bridge_notificaciones SET leido=TRUE WHERE id IN ({placeholders})",
                ids
            )
            db.commit()
        except Exception as exc:
            log.warning("bridge_notif: no se pudo marcar como leído — %s", exc)

    # Serializar timestamps a ISO string
    notifs = []
    for r in rows:
        r = dict(r)
        if hasattr(r.get("creado_en"), "isoformat"):
            r["creado_en"] = r["creado_en"].isoformat()
        notifs.append(r)

    return jsonify({
        "notificaciones": notifs,
        "total":          len(notifs),
        "usuario":        usuario,
        "rol":            rol,
    })


# ── API Reset completo (admin only) ───────────────────────────────────────────

@app.route("/api/importar/backup", methods=["GET"])
@admin_required
def exportar_backup_previo():
    """Genera y devuelve un Excel con todos los pedidos actuales (backup previo al reset)."""
    try:
        import openpyxl, io
        from openpyxl.styles import Font, PatternFill, Alignment

        pedidos = rows_to_list(query(f"{PEDIDO_SELECT} ORDER BY p.norden ASC"))

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "BACKUP PEDIDOS"

        HEADERS = [
            "Nº ORDEN", "HOTEL", "DEPARTAMENTO", "FECHA SOLICITUD",
            "FECHA ENVÍO Vº Bº", "PEDIDO Nº", "FECHA TRAMITACIÓN",
            "Nº PRESUPUESTO", "ESTADO", "Nº ENTRADA DALI / SAP",
            "COMUNICADO A&B", "COMUNICADO JEFE DEP.",
            "PARTE ROTURA", "PARTE AMPLIACIÓN",
            "PROVEEDOR", "EMAIL PROVEEDOR", "TELÉFONO", "CONTACTO",
            "OBSERVACIONES", "CREADO POR", "CREADO EN",
        ]
        ws.append(HEADERS)
        header_fill = PatternFill("solid", fgColor="8B0000")
        header_font = Font(bold=True, color="FFFFFF")
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")

        def strip_tz(val):
            if hasattr(val, "tzinfo") and val.tzinfo is not None:
                return val.replace(tzinfo=None)
            return val

        for p in pedidos:
            ws.append([
                p.get("norden"), p.get("hotel_codigo"), p.get("departamento_nombre"),
                strip_tz(p.get("fecha_solicitud")), strip_tz(p.get("fecha_envio_visto_bueno")),
                p.get("pedido_num"), strip_tz(p.get("fecha_tramitacion")),
                p.get("presupuesto_num"), p.get("estado"),
                format_albaran_display(p.get("entrada_albaran_num")),
                "SÍ" if p.get("comunicado_ab") else "NO",
                "SÍ" if p.get("comunicado_jefe_dep") else "NO",
                "SÍ" if p.get("parte_rotura") else "NO",
                "SÍ" if p.get("parte_ampliacion") else "NO",
                p.get("proveedor_nombre"), p.get("proveedor_email"),
                p.get("proveedor_telefono"), p.get("proveedor_contacto"),
                p.get("observaciones"), p.get("creado_por_nombre"), strip_tz(p.get("creado_en")),
            ])

        COL_WIDTHS = [8,8,22,14,14,16,14,18,32,16,12,14,12,12,28,28,14,16,40,18,18]
        for i, w in enumerate(COL_WIDTHS, 1):
            ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w
        ws.freeze_panes = "A2"

        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        from flask import send_file
        filename = f"BACKUP_PEDIDOS_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return send_file(buf,
                         mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                         as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/importar/reset", methods=["POST"])
@admin_required
def reset_e_importar():
    """
    Borra TODOS los pedidos (incluidos adjuntos PDF/imágenes via CASCADE)
    y el historial. Luego importa el Excel recibido desde cero.
    Solo accesible para administradores.
    """
    from datetime import datetime as dt
    try:
        import openpyxl

        if "archivo" not in request.files:
            return jsonify({"ok": False, "error": "No se recibió ningún archivo"}), 400

        archivo = request.files["archivo"]
        if not archivo.filename.endswith((".xlsx", ".xls")):
            return jsonify({"ok": False, "error": "El archivo debe ser .xlsx"}), 400

        db  = get_db()
        uid = current_user_id()

        # ── 1. Borrado total (CASCADE elimina adjuntos, historial, eliminados) ──
        with db.cursor() as cur_del:
            cur_del.execute("DELETE FROM pedidos")                # CASCADE → adjuntos + historial
            # pedidos_eliminados puede no existir si no se ejecutó la migración
            cur_del.execute("""
                DO $$ BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_schema = 'public'
                          AND table_name   = 'pedidos_eliminados'
                    ) THEN
                        DELETE FROM pedidos_eliminados;
                    END IF;
                END $$;
            """)

        log.info("RESET: todos los pedidos eliminados por admin user_id=%s", uid)

        # ── 2. Leer Excel y construir filas (misma lógica que /api/importar) ──
        wb = openpyxl.load_workbook(archivo, data_only=True)
        ws = wb.active
        headers = [str(c.value).strip().upper() if c.value else "" for c in ws[1]]

        def col_raw(row, name):
            try:
                idx = headers.index(name)
                return row[idx].value
            except (ValueError, IndexError):
                return None

        def col(row, name):
            v = col_raw(row, name)
            return str(v).strip() if v is not None else None

        def parse_date(val):
            if val is None:
                return None
            if hasattr(val, 'strftime'):
                return val.strftime("%Y-%m-%d")
            try:
                n = int(float(str(val)))
                if 30000 < n < 60000:
                    from openpyxl.utils.datetime import from_excel
                    return from_excel(n).strftime("%Y-%m-%d")
            except Exception:
                pass
            for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
                try:
                    return dt.strptime(str(val).strip(), fmt).strftime("%Y-%m-%d")
                except Exception:
                    pass
            log.warning("[reset_e_importar] Fecha no reconocida en Excel, valor descartado: %r", val)
            return None

        def bool_val(val):
            if not val:
                return 0
            return 1 if str(val).strip().upper() in ("SÍ", "SI", "S", "1", "TRUE", "YES") else 0

        hoteles_cache     = {r["codigo"]: r["id"] for r in rows_to_list(query("SELECT id, codigo FROM hoteles WHERE activo=1"))}
        deptos_cache      = {r["nombre"].upper(): r["id"] for r in rows_to_list(query("SELECT id, nombre FROM departamentos WHERE activo=1"))}
        proveedores_cache = {r["nombre"].upper(): r["id"] for r in rows_to_list(query("SELECT id, nombre FROM proveedores WHERE activo=1"))}

        errores = []
        filas_validas = []

        # Numeración correlativa desde 1 (reset completo)
        year = datetime.now().year

        for i, row in enumerate(ws.iter_rows(min_row=2), start=2):
            hotel_codigo = col(row, "HOTEL")
            if not hotel_codigo:
                continue

            hotel_id = hoteles_cache.get(str(hotel_codigo).upper())
            if not hotel_id:
                errores.append(f"Fila {i}: hotel '{hotel_codigo}' no encontrado")
                continue

            depto_nombre = col(row, "DEPARTAMENTO")
            depto_id = deptos_cache.get(str(depto_nombre).upper()) if depto_nombre else None

            prov_nombre = col(row, "PROVEEDOR")
            prov_id = proveedores_cache.get(str(prov_nombre).upper()) if prov_nombre else None

            estado_raw = col(row, "ESTADO")
            estado = estado_raw if estado_raw in ESTADOS_VALIDOS else "PENDIENTE FIRMA DIRECCION COMPRAS"

            # norden siempre correlativo desde 1, independiente del Excel
            filas_validas.append({
                "norden":    len(filas_validas) + 1,
                "hotel_id":  hotel_id, "depto_id": depto_id,
                "fecha_sol": parse_date(col_raw(row, "FECHA SOLICITUD")),
                "fecha_env": parse_date(col_raw(row, "FECHA ENVÍO Vº Bº")),
                "fecha_tra": parse_date(col_raw(row, "FECHA TRAMITACIÓN")),
                "pedido_num":  col(row, "PEDIDO Nº"),
                "presup_num":  col(row, "Nº PRESUPUESTO"),
                "albaran_num": col(row, "Nº ENTRADA DALI / SAP"),
                "estado":    estado,
                "com_ab":    bool_val(col(row, "COMUNICADO A&B")),
                "com_jefe":  bool_val(col(row, "COMUNICADO JEFE DEP.")),
                "p_rotura":  bool_val(col(row, "PARTE ROTURA")),
                "p_amplia":  bool_val(col(row, "PARTE AMPLIACIÓN")),
                "prov_id":   prov_id,
                "obs":       col(row, "OBSERVACIONES"),
            })

        # ── 3. Bulk insert ─────────────────────────────────────────────────────
        insertados = 0
        if filas_validas:
            from psycopg2.extras import execute_values
            _nombre = session.get("nombre")
            with db.cursor() as cur_i:
                pedido_rows = [
                    (f["norden"], f["hotel_id"], f["depto_id"],
                     f["fecha_sol"], f["fecha_env"], f["fecha_tra"],
                     f["pedido_num"], f["presup_num"], f["albaran_num"],
                     f["estado"], f["com_ab"], f["com_jefe"],
                     f["p_rotura"], f["p_amplia"], f["prov_id"],
                     f["obs"], uid, uid, _nombre, _nombre)
                    for f in filas_validas
                ]
                ids = execute_values(cur_i, """
                    INSERT INTO pedidos (
                        norden, hotel_id, departamento_id,
                        fecha_solicitud, fecha_envio_visto_bueno, fecha_tramitacion,
                        pedido_num, presupuesto_num, entrada_albaran_num,
                        estado, comunicado_ab, comunicado_jefe_dep,
                        parte_rotura, parte_ampliacion,
                        proveedor_id, observaciones,
                        creado_por_id, modificado_por_id,
                        creado_por_nombre, modificado_por_nombre
                    ) VALUES %s RETURNING id
                """, pedido_rows, fetch=True)

                insertados = len(ids)

                historial_rows = [
                    (ids[idx]["id"], filas_validas[idx]["estado"], uid, _nombre, "Importado desde Excel (reset completo)")
                    for idx in range(len(ids))
                ]
                execute_values(cur_i, """
                    INSERT INTO historial_estados (pedido_id, estado_nuevo, usuario_id, usuario_nombre, nota)
                    VALUES %s
                """, historial_rows)

        db.commit()
        log.info("RESET completado: %d pedidos importados por admin user_id=%s", insertados, uid)
        return jsonify({"ok": True, "insertados": insertados, "errores": errores})

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ── API Importar Excel ─────────────────────────────────────────────────────────

@app.route("/api/importar", methods=["POST"])
@login_required
def importar_excel():
    try:
        import openpyxl
        from datetime import datetime as dt

        if "archivo" not in request.files:
            return jsonify({"ok": False, "error": "No se recibió ningún archivo"}), 400

        archivo = request.files["archivo"]
        if not archivo.filename.endswith((".xlsx", ".xls")):
            return jsonify({"ok": False, "error": "El archivo debe ser .xlsx"}), 400

        wb = openpyxl.load_workbook(archivo, data_only=True)
        ws = wb.active

        # Leer cabeceras de la primera fila
        headers = [str(c.value).strip().upper() if c.value else "" for c in ws[1]]

        def col_raw(row, name):
            try:
                idx = headers.index(name)
                return row[idx].value
            except (ValueError, IndexError):
                return None

        def col(row, name):
            v = col_raw(row, name)
            return str(v).strip() if v is not None else None

        def parse_date(val):
            if val is None:
                return None
            if hasattr(val, 'strftime'):
                return val.strftime("%Y-%m-%d")
            try:
                n = int(float(str(val)))
                if 30000 < n < 60000:
                    from openpyxl.utils.datetime import from_excel
                    return from_excel(n).strftime("%Y-%m-%d")
            except Exception:
                pass
            for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
                try:
                    return dt.strptime(str(val).strip(), fmt).strftime("%Y-%m-%d")
                except Exception:
                    pass
            log.warning("[importar_excel] Fecha no reconocida en Excel, valor descartado: %r", val)
            return None

        def bool_val(val):
            if not val:
                return 0
            return 1 if str(val).strip().upper() in ("SÍ", "SI", "S", "1", "TRUE", "YES") else 0

        db = get_db()
        uid = current_user_id()

        # Cachés para no consultar la BD en cada fila
        hoteles_cache      = {r["codigo"]: r["id"] for r in rows_to_list(query("SELECT id, codigo FROM hoteles WHERE activo=1"))}
        deptos_cache       = {r["nombre"].upper(): r["id"] for r in rows_to_list(query("SELECT id, nombre FROM departamentos WHERE activo=1"))}
        proveedores_cache  = {r["nombre"].upper(): r["id"] for r in rows_to_list(query("SELECT id, nombre FROM proveedores WHERE activo=1"))}

        errores = []
        filas_validas = []

        # 1. Obtener norden base en UNA sola query
        year = datetime.now().year
        with db.cursor() as cur_n:
            cur_n.execute(
                "SELECT COALESCE(MAX(norden), 0) as mx FROM pedidos WHERE EXTRACT(YEAR FROM creado_en) = %s",
                (year,)
            )
            base_norden = (cur_n.fetchone()["mx"] or 0) + 1

        # 2. Procesar todas las filas en memoria (sin queries)
        for i, row in enumerate(ws.iter_rows(min_row=2), start=2):
            hotel_codigo = col(row, "HOTEL")
            if not hotel_codigo:
                continue

            hotel_id = hoteles_cache.get(str(hotel_codigo).upper())
            if not hotel_id:
                errores.append(f"Fila {i}: hotel '{hotel_codigo}' no encontrado")
                continue

            depto_nombre = col(row, "DEPARTAMENTO")
            depto_id = deptos_cache.get(str(depto_nombre).upper()) if depto_nombre else None

            prov_nombre = col(row, "PROVEEDOR")
            prov_id = proveedores_cache.get(str(prov_nombre).upper()) if prov_nombre else None

            estado_raw = col(row, "ESTADO")
            estado = estado_raw if estado_raw in ESTADOS_VALIDOS else "PENDIENTE FIRMA DIRECCION COMPRAS"

            filas_validas.append({
                "norden": base_norden + len(filas_validas),
                "hotel_id": hotel_id, "depto_id": depto_id,
                "fecha_sol": parse_date(col_raw(row, "FECHA SOLICITUD")),
                "fecha_env": parse_date(col_raw(row, "FECHA ENVÍO Vº Bº")),
                "fecha_tra": parse_date(col_raw(row, "FECHA TRAMITACIÓN")),
                "pedido_num": col(row, "PEDIDO Nº"),
                "presup_num": col(row, "Nº PRESUPUESTO"),
                "albaran_num": col(row, "Nº ENTRADA DALI / SAP"),
                "estado": estado,
                "com_ab": bool_val(col(row, "COMUNICADO A&B")),
                "com_jefe": bool_val(col(row, "COMUNICADO JEFE DEP.")),
                "p_rotura": bool_val(col(row, "PARTE ROTURA")),
                "p_amplia": bool_val(col(row, "PARTE AMPLIACIÓN")),
                "prov_id": prov_id,
                "obs": col(row, "OBSERVACIONES"),
            })

        # 3. Bulk insert en 2 queries únicas
        insertados = 0
        if filas_validas:
            from psycopg2.extras import execute_values
            _nombre = session.get("nombre")
            with db.cursor() as cur_i:
                pedido_rows = [
                    (f["norden"], f["hotel_id"], f["depto_id"],
                     f["fecha_sol"], f["fecha_env"], f["fecha_tra"],
                     f["pedido_num"], f["presup_num"], f["albaran_num"],
                     f["estado"], f["com_ab"], f["com_jefe"],
                     f["p_rotura"], f["p_amplia"], f["prov_id"],
                     f["obs"], uid, uid, _nombre, _nombre)
                    for f in filas_validas
                ]
                ids = execute_values(cur_i, """
                    INSERT INTO pedidos (
                        norden, hotel_id, departamento_id,
                        fecha_solicitud, fecha_envio_visto_bueno, fecha_tramitacion,
                        pedido_num, presupuesto_num, entrada_albaran_num,
                        estado, comunicado_ab, comunicado_jefe_dep,
                        parte_rotura, parte_ampliacion,
                        proveedor_id, observaciones,
                        creado_por_id, modificado_por_id,
                        creado_por_nombre, modificado_por_nombre
                    ) VALUES %s RETURNING id
                """, pedido_rows, fetch=True)

                insertados = len(ids)

                historial_rows = [
                    (ids[idx]["id"], filas_validas[idx]["estado"], uid, _nombre, "Importado desde Excel")
                    for idx in range(len(ids))
                ]
                execute_values(cur_i, """
                    INSERT INTO historial_estados (pedido_id, estado_nuevo, usuario_id, usuario_nombre, nota)
                    VALUES %s
                """, historial_rows)

        db.commit()
        return jsonify({"ok": True, "insertados": insertados, "errores": errores})

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ── API Exportar Excel ─────────────────────────────────────────────────────────

@app.route("/api/exportar")
@login_required
def exportar_excel():
    try:
        import openpyxl, io
        from openpyxl.styles import Font, PatternFill, Alignment
        from flask import send_file

        pedidos = rows_to_list(query(f"{PEDIDO_SELECT} ORDER BY p.creado_en DESC"))

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "CONTROL PEDIDOS"

        HEADERS = [
            "Nº ORDEN", "HOTEL", "DEPARTAMENTO", "FECHA SOLICITUD",
            "FECHA ENVÍO Vº Bº", "PEDIDO Nº", "FECHA TRAMITACIÓN",
            "Nº PRESUPUESTO", "ESTADO", "Nº ENTRADA DALI / SAP",
            "COMUNICADO A&B", "COMUNICADO JEFE DEP.",
            "PARTE ROTURA", "PARTE AMPLIACIÓN",
            "PROVEEDOR", "EMAIL PROVEEDOR", "TELÉFONO", "CONTACTO",
            "OBSERVACIONES", "CREADO POR", "CREADO EN",
        ]
        ws.append(HEADERS)
        header_fill = PatternFill("solid", fgColor="1a3a6b")
        header_font = Font(bold=True, color="FFFFFF")
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")

        ESTADO_COLORES = {
            "ENTREGADO":                         "d4edda",
            "ENVIADO AL PROVEEDOR":              "cce5ff",
            "ENTREGA PARCIAL":                   "fff3cd",
            "PENDIENTE FIRMA DIRECCION COMPRAS": "ffeeba",
            "PENDIENTE DE FIRMA DIRECCION HOTEL":"ffe8a1",
            "CANCELADO":                           "f8d7da",
        }

        def strip_tz(val):
            """Elimina tzinfo de datetimes para compatibilidad con openpyxl/Excel."""
            if hasattr(val, "tzinfo") and val.tzinfo is not None:
                return val.replace(tzinfo=None)
            return val

        for p in pedidos:
            ws.append([
                p.get("norden"), p.get("hotel_codigo"), p.get("departamento_nombre"),
                strip_tz(p.get("fecha_solicitud")), strip_tz(p.get("fecha_envio_visto_bueno")),
                p.get("pedido_num"), strip_tz(p.get("fecha_tramitacion")),
                p.get("presupuesto_num"), p.get("estado"),
                format_albaran_display(p.get("entrada_albaran_num")),
                "SÍ" if p.get("comunicado_ab") else "NO",
                "SÍ" if p.get("comunicado_jefe_dep") else "NO",
                "SÍ" if p.get("parte_rotura") else "NO",
                "SÍ" if p.get("parte_ampliacion") else "NO",
                p.get("proveedor_nombre"), p.get("proveedor_email"),
                p.get("proveedor_telefono"), p.get("proveedor_contacto"),
                p.get("observaciones"), p.get("creado_por_nombre"), strip_tz(p.get("creado_en")),
            ])
            color = ESTADO_COLORES.get(p.get("estado", ""), "FFFFFF")
            fill  = PatternFill("solid", fgColor=color)
            for cell in ws[ws.max_row]:
                cell.fill = fill

        COL_WIDTHS = [8,8,22,14,14,16,14,18,32,16,12,14,12,12,28,28,14,16,40,18,18]
        for i, w in enumerate(COL_WIDTHS, 1):
            ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w
        ws.freeze_panes = "A2"

        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        filename = f"CONTROL_PEDIDOS_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        return send_file(buf,
                         mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                         as_attachment=True, download_name=filename)
    except ImportError:
        return jsonify({"error": "openpyxl no instalado"}), 500

# ── Adjuntos (PDFs e imágenes de artículos) ───────────────────────────────────

TIPOS_ADJUNTO_VALIDOS = {
    "presupuesto_pdf", "pedido_pdf", "imagen_articulo",
    "pedido_doc",       # PDF/Word/correo vinculado a Nº Pedido DALI/SAP
    "presupuesto_doc",  # PDF/Word/correo vinculado a Nº Presupuesto
    "solicitud_doc",    # Excel/PDF/Word + correo vinculado a Fecha Solicitud
    "vb_eml",           # Correo .eml/.msg vinculado a Fecha Envio Vº Bº
    "tramit_eml",       # Correo .eml/.msg vinculado a Fecha Tramitacion
}
MIME_PERMITIDOS = {
    "application/pdf",
    "image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "message/rfc822",
    "application/vnd.ms-outlook",
    "application/octet-stream",
}
EXT_CORREO = {".eml", ".msg"}
EXT_DOC    = {".xlsx", ".xls", ".docx", ".doc", ".pdf"}
MIME_SOLICITUD_DOC = {
    "application/pdf",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "message/rfc822", "application/vnd.ms-outlook", "application/octet-stream",
}
MIME_CORREO = {"message/rfc822", "application/vnd.ms-outlook", "application/octet-stream"}
MAX_ADJUNTO_BYTES = 20 * 1024 * 1024  # 20 MB por archivo (límite absoluto de respaldo)

# ── Límites de peso ajustados por tipo de contenido ──────────────────────────
# Los PDF/Word de gestión normal (albaranes, presupuestos, solicitudes) no
# deberían pesar más que un escaneado de pocas páginas. Los correos .eml/.msg
# llevan adjuntos incrustados, por lo que su límite es algo mayor pero sigue
# acotado para no arrastrar archivos grandes dentro del correo.
MAX_BYTES_DOCUMENTO = 5 * 1024 * 1024   # 5 MB — PDF / Word / Excel
MAX_BYTES_CORREO    = 3 * 1024 * 1024   # 3 MB — .eml / .msg
MAX_BYTES_IMAGEN    = 2 * 1024 * 1024   # 2 MB — imagen_articulo

# ── Límites de cantidad por apartado ──────────────────────────────────────────
# En los apartados que aceptan documento + correo, se cuentan por separado.
MAX_DOCUMENTOS_POR_APARTADO = 3
MAX_CORREOS_POR_APARTADO    = 1

@app.route("/api/pedidos/<int:pid>/adjuntos", methods=["GET"])
@login_required
def get_adjuntos(pid):
    rows = query(
        "SELECT id, tipo, nombre, mime_type, es_correo, creado_en FROM pedido_adjuntos WHERE pedido_id=%s ORDER BY tipo, creado_en",
        (pid,)
    )
    return jsonify({"ok": True, "adjuntos": rows_to_list(rows)})


@app.route("/api/pedidos/<int:pid>/adjuntos", methods=["POST"])
@login_required
def upload_adjunto(pid):
    # Verificar que el pedido existe
    pedido = query("SELECT id FROM pedidos WHERE id=%s", (pid,), one=True)
    if not pedido:
        return jsonify({"ok": False, "error": "Pedido no encontrado"}), 404

    tipo = request.form.get("tipo", "")
    if tipo not in TIPOS_ADJUNTO_VALIDOS:
        return jsonify({"ok": False, "error": f"Tipo inválido. Valores: {', '.join(TIPOS_ADJUNTO_VALIDOS)}"}), 400

    if "archivo" not in request.files:
        return jsonify({"ok": False, "error": "No se recibió ningún archivo"}), 400

    archivo = request.files["archivo"]
    if not archivo.filename:
        return jsonify({"ok": False, "error": "Nombre de archivo vacío"}), 400

    datos = archivo.read()
    if len(datos) > MAX_ADJUNTO_BYTES:
        return jsonify({"ok": False, "error": "El archivo supera el límite de 20 MB"}), 400

    mime = archivo.mimetype or "application/octet-stream"
    ext  = os.path.splitext(archivo.filename.lower())[1]  # ej. ".eml", ".xlsx"
    es_correo = ext in EXT_CORREO or mime in MIME_CORREO

    if tipo in ("presupuesto_pdf", "pedido_pdf"):
        if mime != "application/pdf":
            return jsonify({"ok": False, "error": "Solo se aceptan archivos PDF en este apartado"}), 400
        if len(datos) > MAX_BYTES_DOCUMENTO:
            return jsonify({"ok": False, "error": f"El PDF supera el límite de {MAX_BYTES_DOCUMENTO // (1024*1024)} MB para este apartado"}), 400

    elif tipo == "imagen_articulo":
        if len(datos) > MAX_BYTES_IMAGEN:
            return jsonify({"ok": False, "error": f"La imagen supera el límite de {MAX_BYTES_IMAGEN // (1024*1024)} MB para este apartado"}), 400

    elif tipo == "pedido_doc":
        if mime not in MIME_SOLICITUD_DOC:
            return jsonify({"ok": False, "error": "Formato no permitido. Use PDF, Word o correo (.eml/.msg)"}), 400
        if mime == "application/octet-stream" and ext not in EXT_CORREO | EXT_DOC:
            return jsonify({"ok": False, "error": "Extensión de archivo no reconocida. Use PDF, Word o correo (.eml/.msg)"}), 400
        if len(datos) > MAX_BYTES_DOCUMENTO:
            return jsonify({"ok": False, "error": f"El documento supera el límite de {MAX_BYTES_DOCUMENTO // (1024*1024)} MB para este apartado"}), 400

        # Máximo 1 documento (PDF/Word) y máximo 1 correo en esta sección;
        # pueden coexistir un documento y un correo a la vez.
        existentes = rows_to_list(query(
            "SELECT es_correo FROM pedido_adjuntos WHERE pedido_id=%s AND tipo='pedido_doc'",
            (pid,)
        ))
        n_docs_existentes    = sum(1 for a in existentes if not a["es_correo"])
        n_correos_existentes = sum(1 for a in existentes if a["es_correo"])

        if es_correo:
            if n_correos_existentes >= 1:
                return jsonify({"ok": False, "error": "Ya existe un correo adjunto en «Nº Pedido (DALI/SAP)». Elimínelo antes de subir uno nuevo."}), 400
        else:
            if n_docs_existentes >= 1:
                return jsonify({"ok": False, "error": "Ya existe un documento adjunto en «Nº Pedido (DALI/SAP)». Elimínelo antes de subir uno nuevo."}), 400

    elif tipo in ("presupuesto_doc", "solicitud_doc"):
        etiqueta = "PDF, Word o correo (.eml/.msg)" if tipo == "presupuesto_doc" else "Excel, Word, PDF o correo (.eml/.msg)"
        if mime not in MIME_SOLICITUD_DOC:
            return jsonify({"ok": False, "error": f"Formato no permitido. Use {etiqueta}"}), 400
        if mime == "application/octet-stream" and ext not in EXT_CORREO | EXT_DOC:
            return jsonify({"ok": False, "error": "Extensión de archivo no reconocida"}), 400

        if es_correo:
            if len(datos) > MAX_BYTES_CORREO:
                return jsonify({"ok": False, "error": f"El correo supera el límite de {MAX_BYTES_CORREO // (1024*1024)} MB para este apartado"}), 400
            n_correos = query(
                "SELECT COUNT(*) as n FROM pedido_adjuntos WHERE pedido_id=%s AND tipo=%s AND es_correo",
                (pid, tipo), one=True
            )
            if n_correos and n_correos["n"] >= MAX_CORREOS_POR_APARTADO:
                return jsonify({"ok": False, "error": f"Ya existe un correo adjunto en este apartado. Máximo {MAX_CORREOS_POR_APARTADO}. Elimínelo antes de subir uno nuevo."}), 400
        else:
            if len(datos) > MAX_BYTES_DOCUMENTO:
                return jsonify({"ok": False, "error": f"El documento supera el límite de {MAX_BYTES_DOCUMENTO // (1024*1024)} MB para este apartado"}), 400
            n_docs = query(
                "SELECT COUNT(*) as n FROM pedido_adjuntos WHERE pedido_id=%s AND tipo=%s AND NOT es_correo",
                (pid, tipo), one=True
            )
            if n_docs and n_docs["n"] >= MAX_DOCUMENTOS_POR_APARTADO:
                return jsonify({"ok": False, "error": f"Máximo {MAX_DOCUMENTOS_POR_APARTADO} documentos en este apartado. Elimine alguno antes de subir uno nuevo."}), 400

    elif tipo in ("vb_eml", "tramit_eml"):
        if mime not in MIME_CORREO:
            return jsonify({"ok": False, "error": "Solo se aceptan correos electronicos (.eml, .msg)"}), 400
        if mime == "application/octet-stream" and ext not in EXT_CORREO:
            return jsonify({"ok": False, "error": "Solo se aceptan archivos .eml o .msg"}), 400
        if len(datos) > MAX_BYTES_CORREO:
            return jsonify({"ok": False, "error": f"El correo supera el límite de {MAX_BYTES_CORREO // (1024*1024)} MB para este apartado"}), 400
        existentes = query(
            "SELECT COUNT(*) as n FROM pedido_adjuntos WHERE pedido_id=%s AND tipo=%s",
            (pid, tipo), one=True
        )
        if existentes and existentes["n"] >= MAX_CORREOS_POR_APARTADO:
            return jsonify({"ok": False, "error": f"Ya existe un correo adjunto en este apartado. Máximo {MAX_CORREOS_POR_APARTADO}. Elimínelo antes de subir uno nuevo."}), 400

    else:
        if mime not in MIME_PERMITIDOS:
            return jsonify({"ok": False, "error": f"Tipo de archivo no permitido: {mime}"}), 400

    uid = current_user_id()
    db  = get_db()
    cur = execute(
        "INSERT INTO pedido_adjuntos (pedido_id, tipo, nombre, mime_type, datos, es_correo, subido_por_id) VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id",
        (pid, tipo, archivo.filename, mime, psycopg2.Binary(datos), es_correo, uid)
    )
    adjunto_id = cur.fetchone()["id"]
    db.commit()
    return jsonify({"ok": True, "id": adjunto_id}), 201


@app.route("/api/adjuntos/<int:aid>", methods=["GET"])
@login_required
def download_adjunto(aid):
    from flask import Response
    row = query("SELECT nombre, mime_type, datos, es_correo FROM pedido_adjuntos WHERE id=%s", (aid,), one=True)
    if not row:
        return jsonify({"ok": False, "error": "Adjunto no encontrado"}), 404
    # Los correos (.eml/.msg) se sirven como attachment para que el SO
    # los abra con el gestor de correo predeterminado.
    # El resto (PDF, imagenes, Word) se sirven inline para previsualizacion.
    disposition = "attachment" if row["es_correo"] else "inline"
    return Response(
        bytes(row["datos"]),
        mimetype=row["mime_type"],
        headers={"Content-Disposition": f'{disposition}; filename="{row["nombre"]}"'}
    )


@app.route("/api/adjuntos/<int:aid>", methods=["DELETE"])
@login_required
def delete_adjunto(aid):
    db  = get_db()
    row = query("SELECT id FROM pedido_adjuntos WHERE id=%s", (aid,), one=True)
    if not row:
        return jsonify({"ok": False, "error": "Adjunto no encontrado"}), 404
    execute("DELETE FROM pedido_adjuntos WHERE id=%s", (aid,))
    db.commit()
    return jsonify({"ok": True})


# ── Ping endpoint (UptimeRobot) ────────────────────────────────────────────────

@app.route("/ping")
def ping():
    return "OK", 200

# ── Error handlers globales (siempre JSON para rutas /api/) ───────────────────

@app.errorhandler(404)
def not_found(e):
    if request.path.startswith("/api/"):
        return jsonify({"ok": False, "error": "Ruta no encontrada"}), 404
    return send_from_directory("templates", "index.html")

@app.errorhandler(500)
def server_error(e):
    if request.path.startswith("/api/"):
        return jsonify({"ok": False, "error": f"Error interno del servidor: {str(e)}"}), 500
    return jsonify({"ok": False, "error": str(e)}), 500

@app.errorhandler(Exception)
def unhandled_exception(e):
    import traceback
    app.logger.error("Excepción no capturada:\n" + traceback.format_exc())
    if request.path.startswith("/api/"):
        return jsonify({"ok": False, "error": f"Error inesperado: {str(e)}"}), 500
    return jsonify({"ok": False, "error": str(e)}), 500

# ── Health Monitoring — validación de integridad operativa ────────────────────
# _validar_integridad_operativa() detecta configuraciones incompletas que
# causarían fallos silenciosos en alertas, emails y Telegram:
#   · hoteles activos sin comprador asignado
#   · compradores (rol='compras') sin ningún hotel asignado
#   · usuarios activos con rol compras/hotel sin email
#   · usuarios activos con rol compras sin telegram_chat_id
#   · emails vacíos en usuarios admin
# Devuelve un dict con todos los problemas encontrados y un flag global ok=True/False.

def _validar_integridad_operativa() -> dict:
    """
    Analiza la configuración de usuarios, hoteles y compradores y detecta
    huecos que provocarían fallos silenciosos en alertas, Telegram y emails.
    Usa queries agregadas (sin bucles N+1) para evitar cuelgues con BDs lentas.
    Devuelve:
      {
        "ok": bool,
        "timestamp": "ISO-8601",
        "problemas": {
          "hoteles_sin_comprador":    [...],
          "compradores_sin_hoteles":  [...],
          "compradores_sin_telegram": [...],
          "compradores_sin_movil":    [...],
          "compradores_sin_email":    [...],
          "admins_sin_email":         [...],
          "hoteles_duplicados":       [...],   # hoteles con > 1 comprador (violación uq)
        },
        "resumen": {
          "total_hoteles_activos": int,
          "total_compradores":     int,
          "total_problemas":       int,
        }
      }
    """

    problemas: dict = {
        "hoteles_sin_comprador":    [],
        "compradores_sin_hoteles":  [],
        "compradores_sin_telegram": [],
        "compradores_sin_movil":    [],
        "compradores_sin_email":    [],
        "admins_sin_email":         [],
        "hoteles_duplicados":       [],
    }

    try:
        db = get_db()
        # Aplicar timeout de statement para evitar cuelgues indefinidos
        with db.cursor() as _cur:
            _cur.execute("SET LOCAL statement_timeout = '15s'")

        # ── Totales para el resumen ──────────────────────────────────────────
        total_hoteles_activos = (query(
            "SELECT COUNT(*) AS n FROM hoteles WHERE activo=1", one=True
        ) or {}).get("n", 0)

        total_compradores = (query(
            "SELECT COUNT(*) AS n FROM usuarios WHERE rol='compras' AND activo=1", one=True
        ) or {}).get("n", 0)

        # ── Hoteles activos sin ningún comprador activo asignado ─────────────
        sin_comprador = rows_to_list(query(
            """SELECT h.id AS hotel_id, h.codigo AS hotel_codigo, h.nombre AS hotel_nombre
               FROM hoteles h
               WHERE h.activo = 1
                 AND NOT EXISTS (
                     SELECT 1 FROM usuario_comprador_hoteles uch
                     JOIN usuarios u ON u.id = uch.usuario_id
                     WHERE uch.hotel_id = h.id AND u.activo = 1 AND u.rol = 'compras'
                 )
               ORDER BY h.codigo"""
        ))
        problemas["hoteles_sin_comprador"] = sin_comprador

        # ── Compradores activos sin ningún hotel asignado ────────────────────
        sin_hoteles = rows_to_list(query(
            """SELECT u.id AS usuario_id, u.username, u.nombre
               FROM usuarios u
               WHERE u.rol = 'compras' AND u.activo = 1
                 AND NOT EXISTS (
                     SELECT 1 FROM usuario_comprador_hoteles uch
                     WHERE uch.usuario_id = u.id
                 )
               ORDER BY u.nombre"""
        ))
        problemas["compradores_sin_hoteles"] = sin_hoteles

        # ── Compradores sin telegram_chat_id ─────────────────────────────────
        sin_telegram = rows_to_list(query(
            """SELECT id AS usuario_id, username, nombre
               FROM usuarios
               WHERE rol = 'compras' AND activo = 1
                 AND (telegram_chat_id IS NULL OR TRIM(telegram_chat_id) = '')
               ORDER BY nombre"""
        ))
        problemas["compradores_sin_telegram"] = sin_telegram

        # ── Compradores sin móvil ─────────────────────────────────────────────
        sin_movil = rows_to_list(query(
            """SELECT id AS usuario_id, username, nombre
               FROM usuarios
               WHERE rol = 'compras' AND activo = 1
                 AND (movil IS NULL OR TRIM(movil) = '')
               ORDER BY nombre"""
        ))
        problemas["compradores_sin_movil"] = sin_movil

        # ── Compradores sin email ─────────────────────────────────────────────
        sin_email_comp = rows_to_list(query(
            """SELECT id AS usuario_id, username, nombre
               FROM usuarios
               WHERE rol = 'compras' AND activo = 1
                 AND (email IS NULL OR TRIM(email) = '')
               ORDER BY nombre"""
        ))
        problemas["compradores_sin_email"] = sin_email_comp

        # ── Admins sin email ──────────────────────────────────────────────────
        sin_email_admin = rows_to_list(query(
            """SELECT id AS usuario_id, username, nombre
               FROM usuarios
               WHERE rol = 'admin' AND activo = 1
                 AND (email IS NULL OR TRIM(email) = '')
               ORDER BY nombre"""
        ))
        problemas["admins_sin_email"] = sin_email_admin

        # ── Hoteles con más de un comprador activo (viola uq_comprador_hotel) ─
        duplicados = rows_to_list(query(
            """SELECT h.codigo AS hotel_codigo, h.nombre AS hotel_nombre,
                      COUNT(uch.usuario_id) AS n_compradores
               FROM hoteles h
               JOIN usuario_comprador_hoteles uch ON uch.hotel_id = h.id
               JOIN usuarios u ON u.id = uch.usuario_id AND u.activo = 1 AND u.rol = 'compras'
               WHERE h.activo = 1
               GROUP BY h.id, h.codigo, h.nombre
               HAVING COUNT(uch.usuario_id) > 1
               ORDER BY h.codigo"""
        ))
        problemas["hoteles_duplicados"] = duplicados

    except Exception as exc:
        log.error("[INTEGRIDAD] Error validando integridad: %s", exc)
        return {
            "ok": False,
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(exc),
            "problemas": problemas,
            "resumen": {"total_hoteles_activos": 0, "total_compradores": 0, "total_problemas": -1},
        }

    total_problemas = sum(len(v) for v in problemas.values())
    return {
        "ok": total_problemas == 0,
        "timestamp": datetime.utcnow().isoformat(),
        "problemas": problemas,
        "resumen": {
            "total_hoteles_activos": int(total_hoteles_activos),
            "total_compradores":     int(total_compradores),
            "total_problemas":       total_problemas,
        },
    }


def _job_health_check(force: bool = False):
    """
    Job diario (07:05 hora Canarias): valida integridad operativa y envía
    Telegram al administrador si detecta problemas de configuración.
    Si force=True (llamada manual desde el botón admin), envía siempre
    aunque no haya problemas, para confirmar que el canal funciona.
    Nunca bloquea operaciones — solo alerta.
    """
    with app.app_context():
        _job_health_check_inner(force)

def _job_health_check_inner(force: bool = False):
    log.info("▶ [HEALTH] Inicio job integridad operativa — %s", _date.today())
    resultado = _validar_integridad_operativa()

    # ── Destinatarios: todos los admins activos con telegram_chat_id en BD ──
    # El campo telegram_chat_id se gestiona exclusivamente desde el panel de administración.
    admins_bd = _get_admins_telegram()

    def _enviar_a_admins(texto_msg):
        for adm in admins_bd:
            res = _send_telegram(adm["telegram_chat_id"], texto_msg)
            log.info("[HEALTH] Telegram → %s (%s): %s",
                     adm["username"], adm["telegram_chat_id"],
                     "OK" if res.get("ok") else res.get("error"))

    if resultado.get("ok"):
        log.info("✅ [HEALTH] Integridad OK — sin problemas detectados")
        if force and admins_bd:
            _enviar_a_admins(
                "✅ *Control Pedidos — Integridad OK*\n\n"
                f"Sistema en buen estado — ningún problema detectado.\n"
                f"🏨 Hoteles activos: {resultado['resumen']['total_hoteles_activos']}\n"
                f"🛒 Compradores activos: {resultado['resumen']['total_compradores']}"
            )
        elif force:
            log.warning("[HEALTH] Sin admins con Telegram configurado — no se envió confirmación")
        return

    # Construir mensaje de alerta
    probs = resultado["problemas"]
    lineas = ["🚨 *ALERTA DE CONFIGURACIÓN — Control Pedidos*", ""]

    if probs["hoteles_sin_comprador"]:
        lineas.append(f"❌ *Hoteles sin comprador ({len(probs['hoteles_sin_comprador'])})* — CRÍTICO:")
        for h in probs["hoteles_sin_comprador"]:
            lineas.append(f"  · {h['hotel_codigo']} — {h['hotel_nombre']}")
        lineas.append("")

    if probs["compradores_sin_hoteles"]:
        lineas.append(f"⚠️ *Compradores sin hoteles ({len(probs['compradores_sin_hoteles'])})* :")
        for u in probs["compradores_sin_hoteles"]:
            lineas.append(f"  · {u['nombre']} ({u['username']})")
        lineas.append("")

    if probs["compradores_sin_telegram"]:
        lineas.append(f"⚠️ *Compradores sin Telegram ({len(probs['compradores_sin_telegram'])})* :")
        for u in probs["compradores_sin_telegram"]:
            lineas.append(f"  · {u['nombre']} ({u['username']})")
        lineas.append("")

    if probs["compradores_sin_email"]:
        lineas.append(f"⚠️ *Compradores sin email ({len(probs['compradores_sin_email'])})* :")
        for u in probs["compradores_sin_email"]:
            lineas.append(f"  · {u['nombre']} ({u['username']})")
        lineas.append("")

    if probs["admins_sin_email"]:
        lineas.append(f"⚠️ *Admins sin email ({len(probs['admins_sin_email'])})* :")
        for u in probs["admins_sin_email"]:
            lineas.append(f"  · {u['nombre']} ({u['username']})")
        lineas.append("")

    lineas.append(f"📋 Total problemas: *{resultado['resumen']['total_problemas']}*")
    lineas.append("— Accede al panel admin → Integridad para ver el detalle.")

    texto = "\n".join(lineas)

    # Enviar a todos los admins con Telegram configurado
    if admins_bd:
        _enviar_a_admins(texto)
    else:
        log.warning("[HEALTH] Sin admins con Telegram configurado — alerta solo en log")

    log.warning("[HEALTH] %d problema(s) de integridad detectados: %s",
                resultado["resumen"]["total_problemas"],
                {k: len(v) for k, v in probs.items() if v})


# ── Scheduler: alertas automáticas por Telegram ───────────────────────────────
# Corre dentro del mismo proceso gunicorn — sin Redis, sin Celery, sin workers.
# Cada 60 segundos, en horario 07:00-16:00 hora Canarias (todos los días),
# revisa todos los pedidos activos y envía Telegram si procede.
# La protección _ya_notificado_hoy() evita duplicados: aunque el job corra
# 540 veces al día, cada pedido solo recibe UNA alerta por día.

def _iniciar_scheduler():
    scheduler = BackgroundScheduler(timezone="Atlantic/Canary")
    # Intervalo: cada 60 segundos, solo entre las 07:00 y las 16:00 locales.
    # hour='7-15' → APScheduler ejecuta mientras hour esté en [7..15],
    # es decir desde las 07:00:00 hasta las 15:59:59 — el último ciclo
    # arranca a las 15:59 y el siguiente ya sería las 16:00, fuera de rango.
    scheduler.add_job(
        _job_alertas_diarias,
        trigger="cron",
        hour="7-15",          # 07:00 → 15:59 (inclusive)
        minute="*",
        second="0",           # en punto de cada minuto
        id="alertas_cada_minuto",
        replace_existing=True,
        misfire_grace_time=60,
    )
    # Job de techo URGENTE a admins: cada 60 segundos, lun-vie, 07:00-16:59.
    # La lógica interna aplica deduplicación diaria y el ciclo de 2 días.
    scheduler.add_job(
        _job_techo_urgente_admins,
        trigger="cron",
        day_of_week="mon-fri",  # solo días laborables
        hour="7-16",            # 07:00 → 16:59 (función interna bloquea ≥ 17:00)
        minute="*",
        second="0",
        id="techo_urgente_admins",
        replace_existing=True,
        misfire_grace_time=60,
    )
    # Job de techo mensual: una vez al día a las 08:00 hora Canarias
    scheduler.add_job(
        _job_alertas_techo_mensual,
        trigger="cron",
        hour="8",
        minute="0",
        second="0",
        id="alertas_techo_mensual",
        replace_existing=True,
        misfire_grace_time=3600,  # 1 hora — tolera reinicios de Render tras el cron de 08:00
    )
    # Job de familia/partida repetida: cada 60s, lun-vie 07:00-16:59.
    # Comprador: alerta diaria. Admins: alerta cada 2 días.
    scheduler.add_job(
        _job_familia_repetida,
        trigger="cron",
        day_of_week="mon-fri",
        hour="7-16",
        minute="*",
        second="0",
        id="familia_repetida",
        replace_existing=True,
        misfire_grace_time=60,
    )
    # Job de integridad: una vez al día a las 07:05 hora Canarias
    scheduler.add_job(
        _job_health_check,
        trigger="cron",
        hour="7",
        minute="5",
        second="0",
        id="health_check_diario",
        replace_existing=True,
        misfire_grace_time=300,
    )
    scheduler.start()
    log.info("✅ Scheduler iniciado — alertas cada 60s en horario 07:00-16:00 (Atlantic/Canary)")
    log.info("✅ Scheduler — techo URGENTE admins cada 60s, lun-vie 07:00-16:59 (Atlantic/Canary)")
    log.info("✅ Scheduler — alertas techo mensual diarias a las 08:00 (Atlantic/Canary)")
    log.info("✅ Scheduler — familia/partida repetida cada 60s, lun-vie 07:00-16:59 (Atlantic/Canary)")
    log.info("✅ Scheduler — health check diario a las 07:05 (Atlantic/Canary)")
    atexit.register(lambda: scheduler.shutdown(wait=False))

_iniciar_scheduler()
# ── Endpoint manual para forzar el job de alertas (admin only) ────────────────

@app.route("/api/admin/test-scheduler", methods=["POST"])
@admin_required
def test_scheduler():
    """
    Ejecuta el job de alertas inmediatamente.
    Útil para verificar que el scheduler funciona sin esperar a las 08:00/14:00.
    POST /api/admin/test-scheduler
    """
    import threading
    resultados = {"iniciado": True, "mensaje": "Job ejecutándose en segundo plano — revisa los móviles en unos segundos."}
    t = threading.Thread(target=_job_alertas_diarias, daemon=True)
    t.start()
    log.info("▶ [MANUAL] Job alertas lanzado manualmente por admin")
    return jsonify({"ok": True, **resultados})


@app.route("/api/admin/test-techo-mensual", methods=["POST"])
@admin_required
def test_techo_mensual():
    """
    Ejecuta el job de alertas de techo mensual inmediatamente.
    Útil para verificar que las notificaciones de techo funcionan sin esperar a las 08:00.
    POST /api/admin/test-techo-mensual
    """
    import threading
    t = threading.Thread(target=_job_alertas_techo_mensual, daemon=True)
    t.start()
    log.info("▶ [MANUAL] Job techo mensual lanzado manualmente por admin")
    return jsonify({
        "ok": True,
        "iniciado": True,
        "mensaje": "Job techo mensual ejecutándose en segundo plano — revisa los móviles en unos segundos."
    })


@app.route("/api/admin/test-techo-urgente", methods=["POST"])
@admin_required
def test_techo_urgente_admins():
    """
    Ejecuta el job de techo URGENTE a admins inmediatamente, ignorando
    la restricción de horario — útil para pruebas desde el panel de admin.
    POST /api/admin/test-techo-urgente
    """
    import threading
    t = threading.Thread(target=_job_techo_urgente_admins, daemon=True)
    t.start()
    log.info("\u25b6 [MANUAL] Job techo URGENTE admins lanzado manualmente por admin")
    return jsonify({
        "ok": True,
        "iniciado": True,
        "mensaje": "Job techo URGENTE admins ejecutándose en segundo plano."
    })


@app.route("/api/admin/test-familia-repetida", methods=["POST"])
@admin_required
def test_familia_repetida():
    """
    Lanza manualmente el job de alerta de familia/partida repetida.
    POST /api/admin/test-familia-repetida
    """
    import threading
    t = threading.Thread(target=_job_familia_repetida, daemon=True)
    t.start()
    log.info("\u25b6 [MANUAL] Job familia repetida lanzado manualmente por admin")
    return jsonify({
        "ok": True,
        "iniciado": True,
        "mensaje": "Job familia/partida repetida ejecutándose en segundo plano."
    })


@app.route("/api/admin/config-alertas", methods=["GET"])
@admin_required
def api_get_config_alertas():
    """Devuelve toda la configuración de alertas agrupada."""
    try:
        rows = rows_to_list(query(
            "SELECT clave, valor, tipo, label, grupo, orden FROM config_alertas ORDER BY grupo, orden"
        ))
        grupos = {}
        for r in rows:
            grupos.setdefault(r["grupo"], []).append(r)
        return jsonify({"ok": True, "config": rows, "grupos": grupos})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.route("/api/admin/config-alertas", methods=["PUT"])
@admin_required
def api_save_config_alertas():
    """Guarda uno o varios valores. Body: {clave: valor, ...}"""
    data = request.get_json() or {}
    if not data:
        return jsonify({"ok": False, "error": "Sin datos"}), 400
    try:
        db  = get_db()
        cur = db.cursor()
        for clave, valor in data.items():
            cur.execute("UPDATE config_alertas SET valor=%s WHERE clave=%s", (str(valor), clave))
        db.commit()
        log.info("[CONFIG] Configuración actualizada — claves: %s", list(data.keys()))
        return jsonify({"ok": True, "actualizadas": len(data)})
    except Exception as exc:
        log.error("[CONFIG] Error guardando config: %s", exc)
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.route("/api/admin/techo-dedup-reset", methods=["POST"])
@admin_required
def techo_dedup_reset():
    """
    Borra los registros de deduplicación de techo del día actual en whatsapp_log,
    permitiendo que el job vuelva a enviar las alertas aunque ya lo haya hecho hoy.
    POST /api/admin/techo-dedup-reset
    """
    try:
        db  = get_db()
        cur = db.cursor()
        cur.execute(
            """DELETE FROM whatsapp_log
               WHERE tipo LIKE 'telegram_techo_mes_%'
                 AND DATE(creado_en AT TIME ZONE 'Atlantic/Canary') =
                     (NOW() AT TIME ZONE 'Atlantic/Canary')::date"""
        )
        deleted = cur.rowcount
        db.commit()
        log.info("[TECHO-DEDUP-RESET] Eliminados %d registros de dedup del dia — forzado por admin", deleted)
        return jsonify({"ok": True, "eliminados": deleted,
                        "mensaje": f"{deleted} registros de deduplicacion eliminados. Ahora puedes lanzar test-techo-mensual."})
    except Exception as exc:
        log.error("[TECHO-DEDUP-RESET] Error: %s", exc)
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.route("/api/admin/reset-alertas-hoy", methods=["POST"])
@admin_required
def reset_alertas_hoy():
    """
    Borra los registros de deduplicacion del dia actual para alertas de pedidos (telegram_auto),
    permitiendo que el job diario vuelva a enviar como si fuera la primera vez hoy.
    POST /api/admin/reset-alertas-hoy
    """
    try:
        db  = get_db()
        cur = db.cursor()
        cur.execute(
            """DELETE FROM whatsapp_log
               WHERE tipo = 'telegram_auto'
                 AND DATE(creado_en AT TIME ZONE 'Atlantic/Canary') =
                     (NOW() AT TIME ZONE 'Atlantic/Canary')::date"""
        )
        deleted = cur.rowcount
        db.commit()
        log.info("[ALERTAS-RESET] Eliminados %d registros telegram_auto del dia — forzado por admin", deleted)
        return jsonify({"ok": True, "eliminados": deleted,
                        "mensaje": f"{deleted} registros de dedup de pedidos eliminados. Ahora puedes lanzar test-scheduler."})
    except Exception as exc:
        log.error("[ALERTAS-RESET] Error: %s", exc)
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.route("/api/admin/integridad", methods=["GET"])
@admin_required
def get_integridad():
    """
    Ejecuta _validar_integridad_operativa() en tiempo real y devuelve el resultado.
    Usado por el panel de admin para mostrar el badge de aviso y el detalle de problemas.
    GET /api/admin/integridad
    """
    resultado = _validar_integridad_operativa()
    return jsonify(resultado)


@app.route("/api/admin/test-health", methods=["POST"])
@admin_required
def test_health_check():
    """
    Fuerza el job de health check inmediatamente (mismo que corre a las 07:05).
    Envía Telegram al admin si hay problemas.
    POST /api/admin/test-health
    """
    import threading
    t = threading.Thread(target=lambda: _job_health_check(force=True), daemon=True)
    t.start()
    log.info("▶ [MANUAL] Job health-check lanzado manualmente por admin")
    return jsonify({"ok": True, "mensaje": "Health check ejecutándose — revisa Telegram en unos segundos."})


# ── RESTAURACIÓN DE BACKUP ────────────────────────────────────────────────────

def _normalizar_ruta_backup(ruta):
    """Normaliza una ruta de carpeta para comparaciones fiables: sin espacios
    sobrantes, sin barra final y sin distinguir mayúsculas (Windows no
    distingue mayúsculas/minúsculas en rutas). Debe coincidir exactamente
    con la normalización que aplica restore_agent.py al escribir la caché."""
    return ruta.strip().rstrip("\\/").lower()


@app.route("/api/admin/backup/listar", methods=["POST"])
@admin_required
def backup_listar():
    """
    Devuelve la lista de backups disponibles para la ruta indicada.

    Fix v11.8.6: esta ruta dejó de intentar leer Path(ruta) directamente en
    el servidor — Render no tiene acceso a la red local de la oficina, el
    mismo motivo por el que /api/admin/backup/restaurar ya pasó a usar una
    cola (restore_queue) en vez de ejecutar acciones contra el filesystem.

    Ahora lee de `backups_cache`, una tabla que `restore_agent.py` mantiene
    sincronizada desde tu PC en cada ciclo (escanea BACKUP_DESTINO y sube el
    resultado a Supabase). Esta ruta nunca toca disco.
    """
    data = request.get_json(silent=True) or {}
    ruta = data.get("ruta", "").strip()

    if not ruta:
        return jsonify({"ok": False, "error": "Ruta no especificada"}), 400

    ruta_norm = _normalizar_ruta_backup(ruta)

    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
            SELECT nombre, fecha, mb, adjuntos, tiene_log, valido, tipo, actualizado_en
            FROM backups_cache
            WHERE ruta_normalizada = %s
            ORDER BY fecha_raw DESC NULLS LAST, nombre DESC
        """, (ruta_norm,))
        filas = cur.fetchall()

    if not filas:
        return jsonify({
            "ok": True,
            "backups": [],
            "aviso": (
                "El agente local (restore_agent.py) todavía no ha reportado ningún "
                "backup para esta ruta exacta. Comprueba que la tarea programada esté "
                "activa en el PC y que la ruta coincide con BACKUP_DESTINO en "
                "restore_agent.bat."
            ),
        })

    ultimo_escaneo = max(f["actualizado_en"] for f in filas)
    minutos = int((datetime.now(timezone.utc) - ultimo_escaneo).total_seconds() // 60)

    resp = {
        "ok": True,
        "backups": [
            {
                "nombre":    f["nombre"],
                "fecha":     f["fecha"],
                "mb":        float(f["mb"]),
                "adjuntos":  f["adjuntos"],
                "tiene_log": f["tiene_log"],
                "valido":    f["valido"],
                "tipo":      f["tipo"],
            }
            for f in filas
        ],
        "ultimo_escaneo_minutos": minutos,
    }

    if minutos > 5:
        resp["aviso"] = (
            f"El agente local lleva {minutos} minutos sin sincronizar la caché. "
            "Si tu PC está apagado o la tarea programada está desactivada, esta "
            "lista puede no reflejar los backups más recientes."
        )

    return jsonify(resp)


@app.route("/api/admin/backup/log", methods=["POST"])
@admin_required
def backup_ver_log():
    """
    Devuelve el contenido del backup_log.txt de un backup concreto.
    POST /api/admin/backup/log
    Body JSON: { "ruta": "...", "nombre": "backup_20260616_1700" }

    Fix v11.8.6: igual que /api/admin/backup/listar, esta ruta dejó de leer
    el fichero directamente desde el filesystem de Render (sin acceso a la
    red local). El contenido se lee de `backups_cache`, donde lo deja
    restore_agent.py al sincronizar la lista de backups.
    """
    data   = request.get_json(silent=True) or {}
    ruta   = data.get("ruta",   "").strip()
    nombre = data.get("nombre", "").strip()

    if not ruta or not nombre:
        return jsonify({"ok": False, "error": "Faltan parámetros"}), 400

    ruta_norm = _normalizar_ruta_backup(ruta)

    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
            SELECT tiene_log, log_contenido
            FROM backups_cache
            WHERE ruta_normalizada = %s AND nombre = %s
        """, (ruta_norm, nombre))
        fila = cur.fetchone()

    if not fila:
        return jsonify({
            "ok": False,
            "error": "Este backup no aparece en la caché del agente local. "
                     "Pulsa \"Actualizar lista\" para refrescarla."
        }), 404

    if not fila["tiene_log"] or not fila["log_contenido"]:
        return jsonify({"ok": False, "error": "El fichero backup_log.txt no existe en este backup"}), 404

    return jsonify({"ok": True, "log": fila["log_contenido"], "nombre": nombre})


@app.route("/api/admin/backup/restaurar", methods=["POST"])
@admin_required
def backup_restaurar():
    """
    OPCIÓN C — Cola de restauración desacoplada.

    Esta ruta NO restaura nada directamente (Render no tiene acceso a la
    carpeta de red local). En su lugar, registra una petición en la tabla
    `restore_queue`. Un agente local (restore_agent.py), ejecutado en el PC
    con acceso a \\shtabaiba\... y a Supabase, sondea esta tabla cada minuto,
    procesa la petición pendiente más antigua y marca el resultado.

    POST /api/admin/backup/restaurar
    Body JSON: { "ruta": "...", "nombre": "backup_20260616_1700", "modo": "pedidos" }
    """
    data   = request.get_json(silent=True) or {}
    ruta   = data.get("ruta",   "").strip()
    nombre = data.get("nombre", "").strip()
    modo   = data.get("modo",   "pedidos")

    if not ruta or not nombre:
        return jsonify({"ok": False, "error": "Faltan parámetros: ruta y nombre son obligatorios"}), 400
    if modo not in ("pedidos", "completo"):
        return jsonify({"ok": False, "error": "Modo no válido. Usa 'pedidos' o 'completo'"}), 400

    # Evitar encolar si ya hay una petición pendiente o en proceso
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            "SELECT id, backup_nombre, estado FROM restore_queue "
            "WHERE estado IN ('pendiente','en_proceso') "
            "ORDER BY solicitado_en DESC LIMIT 1"
        )
        existente = cur.fetchone()

        if existente:
            return jsonify({
                "ok": False,
                "error": f"Ya hay una restauración {existente['estado']} "
                         f"({existente['backup_nombre']}). Espera a que finalice."
            }), 409

        usuario_nombre = session.get("nombre") or session.get("username") or "admin"

        cur.execute("""
            INSERT INTO restore_queue (backup_nombre, backup_ruta, modo, estado, solicitado_por)
            VALUES (%s, %s, %s, 'pendiente', %s)
            RETURNING id
        """, (nombre, ruta, modo, usuario_nombre))
        nueva_id = cur.fetchone()["id"]
        db.commit()

    log.info("[RESTORE-QUEUE] Petición #%s encolada. backup=%s modo=%s por=%s",
              nueva_id, nombre, modo, usuario_nombre)

    return jsonify({
        "ok": True,
        "encolado": True,
        "queue_id": nueva_id,
        "mensaje": "Petición registrada. El agente local la procesará en menos de 1 minuto."
    })


@app.route("/api/admin/backup/estado", methods=["GET"])
@admin_required
def backup_estado_cola():
    """
    Devuelve el estado de la última petición de restauración encolada,
    para que el panel web haga polling y muestre el progreso en tiempo real.

    GET /api/admin/backup/estado
    """
    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
            SELECT id, backup_nombre, modo, estado, solicitado_por,
                   solicitado_en, iniciado_en, completado_en, resumen, error_msg,
                   pre_restore_backup
            FROM restore_queue
            ORDER BY solicitado_en DESC
            LIMIT 1
        """)
        fila = cur.fetchone()

    if not fila:
        return jsonify({"ok": True, "hay_peticion": False})

    return jsonify({
        "ok": True,
        "hay_peticion": True,
        "id":                 fila["id"],
        "backup_nombre":      fila["backup_nombre"],
        "modo":               fila["modo"],
        "estado":             fila["estado"],
        "solicitado_por":     fila["solicitado_por"],
        "solicitado_en":      fila["solicitado_en"].isoformat() if fila["solicitado_en"] else None,
        "iniciado_en":        fila["iniciado_en"].isoformat()   if fila["iniciado_en"]   else None,
        "completado_en":      fila["completado_en"].isoformat() if fila["completado_en"] else None,
        "resumen":            fila["resumen"],
        "error_msg":          fila["error_msg"],
        "pre_restore_backup": fila["pre_restore_backup"],
    })


# ── Arranque ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
