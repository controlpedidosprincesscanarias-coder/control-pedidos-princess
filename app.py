"""
Control Pedidos Princess Canarias — Flask + PostgreSQL (Supabase) + Resend
Despliegue: Render.com  |  BD: Supabase  |  Email: Resend
"""

import os, json, logging
from datetime import datetime
from functools import wraps

import psycopg2
from psycopg2.extras import RealDictCursor

from flask import Flask, request, jsonify, send_from_directory, session, g
from models import SQL_STATEMENTS, ESTADOS_VALIDOS, ESTADOS_EMAIL_PROVEEDOR, ESTADOS_EMAIL_INTERNO

# ── Configuración ──────────────────────────────────────────────────────────────

DATABASE_URL = os.environ.get("DATABASE_URL", "")          # Supabase → Settings → Database → URI
SECRET_KEY   = os.environ.get("SECRET_KEY", "princess-canarias-2026-dev-key")

# Email — Resend (preferido) o SMTP como fallback
RESEND_API_KEY   = os.environ.get("RESEND_API_KEY", "")
EMAIL_FROM       = os.environ.get("EMAIL_FROM", "compras@princess.es")
EMAILS_INTERNOS  = [e.strip() for e in os.environ.get("EMAILS_INTERNOS", "").split(",") if e.strip()]

# SMTP fallback (solo si no hay RESEND_API_KEY)
SMTP_HOST     = os.environ.get("SMTP_HOST", "")
SMTP_PORT     = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER     = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")

app = Flask(__name__)
app.secret_key = SECRET_KEY
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

def _auto_migrate():
    """Añade columnas/tablas nuevas de forma idempotente."""
    try:
        db = psycopg2.connect(
            DATABASE_URL, cursor_factory=RealDictCursor,
            connect_timeout=10,
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
                    email        TEXT,
                    orden        INTEGER NOT NULL DEFAULT 0
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_prov_contactos ON proveedor_contactos(proveedor_id)")
            # Migrar datos legacy: si hay contacto/email/telefono/movil y no hay contactos aún
            cur.execute("""
                INSERT INTO proveedor_contactos (proveedor_id, nombre, telefono, email, orden)
                SELECT id,
                       NULLIF(TRIM(COALESCE(contacto,'')), ''),
                       NULLIF(TRIM(COALESCE(telefono,'') || CASE WHEN TRIM(COALESCE(movil,''))!='' THEN ' / '||TRIM(movil) ELSE '' END), ''),
                       NULLIF(TRIM(COALESCE(email,'')), ''),
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

# ── Email (Resend preferido, SMTP como fallback) ───────────────────────────────

def _send_email(to: str, subject: str, body_html: str) -> bool:
    # ── Resend ────────────────────────────────────────────────────────────────
    if RESEND_API_KEY:
        try:
            import urllib.request
            payload = json.dumps({
                "from":    EMAIL_FROM,
                "to":      [to],
                "subject": subject,
                "html":    body_html,
            }).encode()
            req = urllib.request.Request(
                "https://api.resend.com/emails",
                data=payload,
                headers={
                    "Authorization": f"Bearer {RESEND_API_KEY}",
                    "Content-Type":  "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status == 200
        except Exception as e:
            log.error("Resend error enviando a %s: %s", to, e)
            return False

    # ── SMTP fallback ─────────────────────────────────────────────────────────
    if SMTP_HOST and SMTP_USER:
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"]    = EMAIL_FROM
            msg["To"]      = to
            msg.attach(MIMEText(body_html, "html", "utf-8"))
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as s:
                s.starttls()
                s.login(SMTP_USER, SMTP_PASSWORD)
                s.sendmail(EMAIL_FROM, [to], msg.as_string())
            return True
        except Exception as e:
            log.error("SMTP error enviando a %s: %s", to, e)
            return False

    log.warning("Email no configurado — omitido para %s", to)
    return False

def _log_email(db, pedido_id, tipo, destinatario, asunto, enviado, error=None):
    with db.cursor() as cur:
        cur.execute(
            "INSERT INTO emails_log (pedido_id,tipo,destinatario,asunto,enviado,error) VALUES (%s,%s,%s,%s,%s,%s)",
            (pedido_id, tipo, destinatario, asunto, 1 if enviado else 0, error)
        )

def enviar_emails_estado(db, pedido_id: int, estado_nuevo: str, estado_antes: str = None):
    pedido = row_to_dict(query(
        """SELECT p.*, h.nombre as hotel_nombre, h.codigo as hotel_codigo,
                  d.nombre as departamento_nombre,
                  pr.nombre as proveedor_nombre,
                  (SELECT email FROM proveedor_contactos WHERE proveedor_id=pr.id AND email IS NOT NULL AND email!='' ORDER BY orden,id LIMIT 1) as proveedor_email
           FROM pedidos p
           LEFT JOIN hoteles h ON p.hotel_id = h.id
           LEFT JOIN departamentos d ON p.departamento_id = d.id
           LEFT JOIN proveedores pr ON p.proveedor_id = pr.id
           WHERE p.id = %s""", (pedido_id,), one=True
    ))
    if not pedido:
        return

    if estado_nuevo in ESTADOS_EMAIL_PROVEEDOR and pedido.get("proveedor_email"):
        subject = f"Pedido Nº {pedido.get('pedido_num','—')} — Princess Hotels"
        body = f"""
        <p>Estimado/a <strong>{pedido.get('proveedor_nombre','')}</strong>,</p>
        <p>Le informamos que el pedido <strong>Nº {pedido.get('pedido_num','—')}</strong>
           del hotel <strong>{pedido.get('hotel_nombre','')}</strong>
           ({pedido.get('departamento_nombre','')}) ha sido tramitado.</p>
        <p><strong>Estado actual:</strong> {estado_nuevo}</p>
        <p>Atentamente,<br>Departamento de Compras<br>Princess Hotels &amp; Resorts — Canarias</p>
        """
        ok = _send_email(pedido["proveedor_email"], subject, body)
        _log_email(db, pedido_id, "proveedor", pedido["proveedor_email"], subject, ok)

    if estado_nuevo in ESTADOS_EMAIL_INTERNO and EMAILS_INTERNOS:
        subject = f"[Control Pedidos] {pedido.get('hotel_codigo','')} · Pedido {pedido.get('pedido_num','—')} → {estado_nuevo}"
        body = f"""
        <p>Cambio de estado en el sistema de Control de Pedidos:</p>
        <table border="1" cellpadding="6" style="border-collapse:collapse;font-family:sans-serif">
          <tr><td><b>Hotel</b></td><td>{pedido.get('hotel_nombre','')}</td></tr>
          <tr><td><b>Departamento</b></td><td>{pedido.get('departamento_nombre','')}</td></tr>
          <tr><td><b>Pedido Nº</b></td><td>{pedido.get('pedido_num','—')}</td></tr>
          <tr><td><b>Proveedor</b></td><td>{pedido.get('proveedor_nombre','—')}</td></tr>
          <tr><td><b>Estado anterior</b></td><td>{estado_antes or '—'}</td></tr>
          <tr><td><b>Estado nuevo</b></td><td><b>{estado_nuevo}</b></td></tr>
        </table>
        """
        for dest in EMAILS_INTERNOS:
            ok = _send_email(dest, subject, body)
            _log_email(db, pedido_id, "interno", dest, subject, ok)

# ── Helper norden ──────────────────────────────────────────────────────────────

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
    return jsonify({"ok": True, "id": user["id"], "username": user["username"],
                    "nombre": user["nombre"], "rol": user["rol"]})

@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True})

@app.route("/api/me")
def me():
    if "user_id" not in session:
        return jsonify({"logged": False})
    return jsonify({"logged": True, "id": session["user_id"], "username": session["username"],
                    "nombre": session["nombre"], "rol": session["rol"]})

# ── API Maestros ───────────────────────────────────────────────────────────────

@app.route("/api/maestros")
@login_required
def get_maestros():
    hoteles       = rows_to_list(query("SELECT * FROM hoteles WHERE activo=1 ORDER BY codigo"))
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
        "SELECT id, username, nombre, email, rol, activo, creado_en FROM usuarios ORDER BY nombre"
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
    cur = execute(
        "INSERT INTO usuarios (username, nombre, email, password, rol, activo) VALUES (%s,%s,%s,%s,%s,1) RETURNING id",
        (username, nombre, data.get("email",""), password, data.get("rol","user"))
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
    if uid == current_user_id() and data.get("rol") == "user":
        return jsonify({"error": "No puedes quitarte el rol de administrador a ti mismo"}), 400
    # Construir UPDATE dinámico solo con campos enviados
    fields, args = [], []
    if "nombre" in data:
        fields.append("nombre=%s"); args.append(data["nombre"].strip())
    if "email" in data:
        fields.append("email=%s"); args.append(data["email"].strip())
    if "rol" in data and data["rol"] in ("admin","user"):
        fields.append("rol=%s"); args.append(data["rol"])
    if "activo" in data:
        fields.append("activo=%s"); args.append(1 if data["activo"] else 0)
    if "password" in data and data["password"].strip():
        fields.append("password=%s"); args.append(data["password"].strip())
    if not fields:
        return jsonify({"error": "Nada que actualizar"}), 400
    args.append(uid)
    execute(f"UPDATE usuarios SET {', '.join(fields)} WHERE id=%s", args)
    db.commit()
    # Si cambié mi propio nombre, actualizar sesión
    if uid == current_user_id() and "nombre" in data:
        session["nombre"] = data["nombre"].strip()
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
        f"SELECT proveedor_id,nombre,telefono,email FROM proveedor_contactos WHERE proveedor_id IN ({placeholders}) ORDER BY proveedor_id,orden,id",
        tuple(ids)
    ))
    # Agrupar por proveedor_id
    from collections import defaultdict
    cmap = defaultdict(list)
    for c in contactos_rows:
        cmap[c["proveedor_id"]].append({
            "nombre": c["nombre"] or "",
            "telefono": c["telefono"] or "",
            "email": c["email"] or "",
        })
    for p in result:
        p["contactos"] = cmap.get(p["id"], [])
        # Campos de compatibilidad para la vista de pedidos (primer contacto)
        first = p["contactos"][0] if p["contactos"] else {}
        p["contacto"]  = first.get("nombre", "")
        p["email"]     = first.get("email", "")
        p["telefono"]  = first.get("telefono", "")
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
    return jsonify(_prov_with_contactos(rows))

@app.route("/api/proveedores", methods=["POST"])
@admin_required
def create_proveedor():
    data   = request.get_json(silent=True) or {}
    nombre = (data.get("nombre") or "").strip()
    if not nombre:
        return jsonify({"error": "Nombre requerido"}), 400
    db  = get_db()
    cur = execute(
        "INSERT INTO proveedores (codigo,nombre,observaciones) VALUES (%s,%s,%s) RETURNING id",
        (data.get("codigo",""), nombre, data.get("observaciones",""))
    )
    new_id = cur.fetchone()["id"]
    # Insertar contactos
    contactos = data.get("contactos", [])
    for i, c in enumerate(contactos):
        nombre_c = (c.get("nombre") or "").strip() or None
        tel_c    = (c.get("telefono") or "").strip() or None
        email_c  = (c.get("email") or "").strip() or None
        if nombre_c or tel_c or email_c:
            execute(
                "INSERT INTO proveedor_contactos (proveedor_id,nombre,telefono,email,orden) VALUES (%s,%s,%s,%s,%s)",
                (new_id, nombre_c, tel_c, email_c, i)
            )
    db.commit()
    return jsonify({"ok": True, "id": new_id, "nombre": nombre}), 201

@app.route("/api/proveedores/<int:pid>", methods=["PUT"])
@admin_required
def update_proveedor(pid):
    data = request.get_json(silent=True) or {}
    db   = get_db()
    execute(
        "UPDATE proveedores SET codigo=%s,nombre=%s,observaciones=%s WHERE id=%s",
        (data.get("codigo",""), data.get("nombre",""), data.get("observaciones",""), pid)
    )
    # Reemplazar contactos
    execute("DELETE FROM proveedor_contactos WHERE proveedor_id=%s", (pid,))
    contactos = data.get("contactos", [])
    for i, c in enumerate(contactos):
        nombre_c = (c.get("nombre") or "").strip() or None
        tel_c    = (c.get("telefono") or "").strip() or None
        email_c  = (c.get("email") or "").strip() or None
        if nombre_c or tel_c or email_c:
            execute(
                "INSERT INTO proveedor_contactos (proveedor_id,nombre,telefono,email,orden) VALUES (%s,%s,%s,%s,%s)",
                (pid, nombre_c, tel_c, email_c, i)
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
    try:
        import openpyxl, io
        from openpyxl.styles import Font, PatternFill, Alignment
        from flask import send_file

        provs = _prov_with_contactos(query(
            "SELECT id,codigo,nombre,observaciones FROM proveedores WHERE activo=1 ORDER BY nombre"
        ))

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Proveedores"

        headers = ["CODIGO", "PROVEEDOR", "CONTACTO", "TELEFONO", "EMAIL", "OBSERVACIONES"]
        header_fill = PatternFill("solid", fgColor="1B2A4A")
        header_font = Font(bold=True, color="FFFFFF")

        for col_idx, h in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_idx, value=h)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")

        col_widths = [15, 45, 25, 20, 35, 40]
        for i, w in enumerate(col_widths, 1):
            ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w

        r_idx = 2
        for p in provs:
            contactos = p.get("contactos", [{}])
            if not contactos:
                contactos = [{}]
            for ci, c in enumerate(contactos):
                ws.cell(row=r_idx, column=1, value=p.get("codigo") or "" if ci == 0 else "")
                ws.cell(row=r_idx, column=2, value=p.get("nombre") or "" if ci == 0 else "")
                ws.cell(row=r_idx, column=3, value=c.get("nombre") or "")
                ws.cell(row=r_idx, column=4, value=c.get("telefono") or "")
                ws.cell(row=r_idx, column=5, value=c.get("email") or "")
                ws.cell(row=r_idx, column=6, value=p.get("observaciones") or "" if ci == 0 else "")
                r_idx += 1

        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        from datetime import datetime as dt
        filename = f"PROVEEDORES_{dt.now().strftime('%Y%m%d_%H%M')}.xlsx"
        return send_file(buf, as_attachment=True, download_name=filename,
                         mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/proveedores/importar", methods=["POST"])
@login_required
def importar_proveedores():
    try:
        import openpyxl
        if "archivo" not in request.files:
            return jsonify({"ok": False, "error": "No se recibió ningún archivo"}), 400
        archivo = request.files["archivo"]
        if not archivo.filename.endswith((".xlsx", ".xls")):
            return jsonify({"ok": False, "error": "El archivo debe ser .xlsx"}), 400

        wb = openpyxl.load_workbook(archivo, data_only=True)
        ws = wb.active
        headers = [str(c.value).strip().upper() if c.value else "" for c in ws[1]]

        def col(row, name):
            try:
                idx = headers.index(name)
                v = row[idx].value
                return str(v).strip() if v is not None else None
            except (ValueError, IndexError):
                return None

        db = get_db()
        existentes = {r["codigo"]: r["id"] for r in rows_to_list(
            query("SELECT id, codigo FROM proveedores WHERE codigo IS NOT NULL AND codigo != ''")
        )}

        # Agrupar filas por proveedor (codigo+nombre)
        from collections import defaultdict
        prov_data = {}   # codigo -> {nombre, obs, contactos:[]}
        prov_order = []  # mantener orden

        for row in ws.iter_rows(min_row=2):
            codigo  = col(row, "CODIGO")
            nombre  = col(row, "PROVEEDOR")
            if not nombre:
                continue
            key = codigo or nombre
            if key not in prov_data:
                prov_data[key] = {
                    "codigo": codigo or "",
                    "nombre": nombre,
                    "observaciones": col(row, "OBSERVACIONES") or "",
                    "contactos": []
                }
                prov_order.append(key)
            # Contacto de esta fila
            c_nombre = col(row, "CONTACTO") or ""
            c_tel    = col(row, "TELEFONO") or col(row, "MOVIL") or ""
            c_email  = col(row, "EMAIL") or ""
            if c_nombre or c_tel or c_email:
                prov_data[key]["contactos"].append((c_nombre, c_tel, c_email))

        insertados = 0
        actualizados = 0

        with db.cursor() as cur_i:
            for key in prov_order:
                p = prov_data[key]
                codigo = p["codigo"]
                if codigo and codigo in existentes:
                    pid = existentes[codigo]
                    cur_i.execute(
                        "UPDATE proveedores SET observaciones=%s WHERE id=%s",
                        (p["observaciones"], pid)
                    )
                    cur_i.execute("DELETE FROM proveedor_contactos WHERE proveedor_id=%s", (pid,))
                    for i, (cn, ct, ce) in enumerate(p["contactos"]):
                        cur_i.execute(
                            "INSERT INTO proveedor_contactos (proveedor_id,nombre,telefono,email,orden) VALUES (%s,%s,%s,%s,%s)",
                            (pid, cn or None, ct or None, ce or None, i)
                        )
                    actualizados += 1
                else:
                    cur_i.execute(
                        "INSERT INTO proveedores (codigo,nombre,observaciones) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING RETURNING id",
                        (codigo, p["nombre"], p["observaciones"])
                    )
                    row_r = cur_i.fetchone()
                    if row_r:
                        new_pid = row_r["id"]
                        for i, (cn, ct, ce) in enumerate(p["contactos"]):
                            cur_i.execute(
                                "INSERT INTO proveedor_contactos (proveedor_id,nombre,telefono,email,orden) VALUES (%s,%s,%s,%s,%s)",
                                (new_pid, cn or None, ct or None, ce or None, i)
                            )
                        insertados += 1

        db.commit()
        return jsonify({"ok": True, "insertados": insertados, "actualizados": actualizados, "errores": []})

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/proveedores/importar/reset", methods=["POST"])
@login_required
def importar_proveedores_reset():
    """Solo admin: borra todos los proveedores e importa desde el Excel."""
    if session.get("rol") != "admin":
        return jsonify({"ok": False, "error": "Acceso restringido a administradores"}), 403
    try:
        import openpyxl
        if "archivo" not in request.files:
            return jsonify({"ok": False, "error": "No se recibió ningún archivo"}), 400
        archivo = request.files["archivo"]
        if not archivo.filename.endswith((".xlsx", ".xls")):
            return jsonify({"ok": False, "error": "El archivo debe ser .xlsx"}), 400

        wb = openpyxl.load_workbook(archivo, data_only=True)
        ws = wb.active
        headers = [str(c.value).strip().upper() if c.value else "" for c in ws[1]]

        def col(row, name):
            try:
                idx = headers.index(name)
                v = row[idx].value
                return str(v).strip() if v is not None else None
            except (ValueError, IndexError):
                return None

        from collections import defaultdict
        prov_data = {}
        prov_order = []

        for row in ws.iter_rows(min_row=2):
            nombre = col(row, "PROVEEDOR")
            if not nombre:
                continue
            codigo = col(row, "CODIGO") or ""
            key = codigo or nombre
            if key not in prov_data:
                prov_data[key] = {
                    "codigo": codigo,
                    "nombre": nombre,
                    "observaciones": col(row, "OBSERVACIONES") or "",
                    "contactos": []
                }
                prov_order.append(key)
            c_nombre = col(row, "CONTACTO") or ""
            c_tel    = col(row, "TELEFONO") or col(row, "MOVIL") or ""
            c_email  = col(row, "EMAIL") or ""
            if c_nombre or c_tel or c_email:
                prov_data[key]["contactos"].append((c_nombre, c_tel, c_email))

        db = get_db()
        insertados = 0
        with db.cursor() as cur:
            cur.execute("UPDATE pedidos SET proveedor_id = NULL WHERE proveedor_id IS NOT NULL")
            cur.execute("DELETE FROM proveedor_contactos")
            cur.execute("DELETE FROM proveedores")
            for key in prov_order:
                p = prov_data[key]
                cur.execute(
                    "INSERT INTO proveedores (codigo,nombre,observaciones) VALUES (%s,%s,%s) RETURNING id",
                    (p["codigo"], p["nombre"], p["observaciones"])
                )
                pid = cur.fetchone()["id"]
                for i, (cn, ct, ce) in enumerate(p["contactos"]):
                    cur.execute(
                        "INSERT INTO proveedor_contactos (proveedor_id,nombre,telefono,email,orden) VALUES (%s,%s,%s,%s,%s)",
                        (pid, cn or None, ct or None, ce or None, i)
                    )
                insertados += 1

        db.commit()
        return jsonify({"ok": True, "insertados": insertados, "actualizados": 0, "errores": []})

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ── Validación techo de gastos ─────────────────────────────────────────────────

TECHO_MAX_PEDIDO   = 3000.00   # €  por pedido individual
TECHO_MAX_MES      = 6000.00   # €  acumulado mensual por hotel
TECHO_MAX_PEDIDOS  = 2         # nº máximo de pedidos sujetos al techo por hotel/mes

def _check_techo(hotel_id, familia_id, importe, mes_str, excluir_pedido_id=None):
    """
    Comprueba las reglas del techo de gastos para un pedido nuevo o editado.
    mes_str: 'YYYY-MM'  (mes natural del pedido, normalmente el actual)
    excluir_pedido_id: al editar, excluimos el propio pedido del conteo.

    Devuelve lista de strings con los errores detectados (vacía = OK).
    """
    errores = []
    if importe and float(importe) > TECHO_MAX_PEDIDO:
        errores.append(
            f"⚠️ El importe {float(importe):,.2f} € supera el límite individual de {TECHO_MAX_PEDIDO:,.0f} € por pedido."
        )

    if not familia_id:
        return errores   # sin familia no hay más que comprobar

    year, month = map(int, mes_str.split("-"))

    excl_clause = "AND p.id != %s" if excluir_pedido_id else ""
    excl_args   = (excluir_pedido_id,) if excluir_pedido_id else ()

    # Pedidos sujetos al techo en este hotel/mes
    base_args = (hotel_id, year, month) + excl_args
    pedidos_mes = rows_to_list(query(f"""
        SELECT p.id, p.familia_id, f.nombre as familia_nombre,
               COALESCE(p.importe, 0) as importe
        FROM pedidos p
        LEFT JOIN familias f ON p.familia_id = f.id
        WHERE p.hotel_id = %s
          AND p.sujeto_techo = 1
          AND p.estado NOT IN ('CANCELADO')
          AND EXTRACT(YEAR  FROM p.creado_en) = %s
          AND EXTRACT(MONTH FROM p.creado_en) = %s
          {excl_clause}
    """, base_args))

    # Regla 1: máximo 2 pedidos sujetos al techo por hotel/mes
    if len(pedidos_mes) >= TECHO_MAX_PEDIDOS:
        errores.append(
            f"🚫 Ya hay {len(pedidos_mes)} pedido(s) sujeto(s) al techo este mes para este hotel "
            f"(máximo {TECHO_MAX_PEDIDOS})."
        )

    # Regla 2: no puede repetirse la familia en el mismo hotel/mes
    familias_usadas = [p["familia_id"] for p in pedidos_mes]
    if int(familia_id) in familias_usadas:
        familia_row = query("SELECT nombre FROM familias WHERE id=%s", (familia_id,), one=True)
        fname = familia_row["nombre"] if familia_row else f"ID {familia_id}"
        errores.append(
            f"🚫 Ya existe un pedido de la familia «{fname}» este mes para este hotel. "
            f"Cada familia solo puede usarse una vez al mes por hotel."
        )

    # Regla 3: acumulado mensual no puede superar 6.000 €
    acumulado = sum(float(p["importe"]) for p in pedidos_mes)
    nuevo_importe = float(importe) if importe else 0.0
    if acumulado + nuevo_importe > TECHO_MAX_MES:
        errores.append(
            f"⚠️ El acumulado del mes sería {acumulado + nuevo_importe:,.2f} € "
            f"(actual {acumulado:,.2f} € + nuevo {nuevo_importe:,.2f} €), "
            f"superando el techo mensual de {TECHO_MAX_MES:,.0f} €."
        )

    return errores

@app.route("/api/techo/resumen")
@login_required
def techo_resumen():
    """Devuelve el resumen del techo de gastos del mes actual por hotel."""
    from datetime import date
    hoy    = date.today()
    year   = hoy.year
    month  = hoy.month

    hoteles = rows_to_list(query("SELECT id, codigo, nombre FROM hoteles WHERE activo=1 ORDER BY codigo"))
    resultado = []
    for hotel in hoteles:
        pedidos = rows_to_list(query("""
            SELECT p.id, p.importe, p.familia_id, f.nombre as familia_nombre,
                   p.pedido_num, p.estado, p.norden
            FROM pedidos p
            LEFT JOIN familias f ON p.familia_id = f.id
            WHERE p.hotel_id = %s
              AND p.sujeto_techo = 1
              AND p.estado NOT IN ('CANCELADO')
              AND EXTRACT(YEAR  FROM p.creado_en) = %s
              AND EXTRACT(MONTH FROM p.creado_en) = %s
            ORDER BY p.creado_en
        """, (hotel["id"], year, month)))

        acumulado     = sum(float(p["importe"] or 0) for p in pedidos)
        num_pedidos   = len(pedidos)
        familias_usadas = [p["familia_nombre"] for p in pedidos if p["familia_nombre"]]

        # Semáforo
        if num_pedidos >= TECHO_MAX_PEDIDOS or acumulado >= TECHO_MAX_MES:
            semaforo = "rojo"
        elif num_pedidos == TECHO_MAX_PEDIDOS - 1 or acumulado >= TECHO_MAX_MES * 0.75:
            semaforo = "amarillo"
        else:
            semaforo = "verde"

        resultado.append({
            "hotel_id":       hotel["id"],
            "hotel_codigo":   hotel["codigo"],
            "hotel_nombre":   hotel["nombre"],
            "num_pedidos":    num_pedidos,
            "max_pedidos":    TECHO_MAX_PEDIDOS,
            "acumulado":      acumulado,
            "techo_mes":      TECHO_MAX_MES,
            "techo_pedido":   TECHO_MAX_PEDIDO,
            "familias_usadas": familias_usadas,
            "semaforo":       semaforo,
            "pedidos":        pedidos,
        })

    return jsonify({"mes": f"{year}-{month:02d}", "hoteles": resultado})

# ── API Pedidos ────────────────────────────────────────────────────────────────

PEDIDO_SELECT = """
    SELECT p.*,
           h.codigo  as hotel_codigo,
           h.nombre  as hotel_nombre,
           d.nombre  as departamento_nombre,
           pr.nombre as proveedor_nombre,
           (SELECT email FROM proveedor_contactos WHERE proveedor_id=pr.id AND email IS NOT NULL AND email!='' ORDER BY orden,id LIMIT 1) as proveedor_email,
           (SELECT telefono FROM proveedor_contactos WHERE proveedor_id=pr.id AND telefono IS NOT NULL AND telefono!='' ORDER BY orden,id LIMIT 1) as proveedor_telefono,
           (SELECT nombre FROM proveedor_contactos WHERE proveedor_id=pr.id ORDER BY orden,id LIMIT 1) as proveedor_contacto,
           u1.nombre as creado_por_nombre,
           u2.nombre as modificado_por_nombre,
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

    q      = request.args.get("q", "").strip()
    hotel  = request.args.get("hotel_id", "")
    estado = request.args.get("estado", "")
    depto  = request.args.get("departamento_id", "")
    alerta = request.args.get("alerta", "")

    if q:
        wheres.append("(p.pedido_num ILIKE %s OR pr.nombre ILIKE %s OR p.observaciones ILIKE %s OR h.codigo ILIKE %s)")
        args += [f"%{q}%"] * 4
    if hotel:
        wheres.append("p.hotel_id = %s"); args.append(hotel)
    if estado:
        wheres.append("p.estado = %s"); args.append(estado)
    if depto:
        wheres.append("p.departamento_id = %s"); args.append(depto)
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
        """SELECT h.*, u.nombre as usuario_nombre
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
            estado, comunicado_ab, comunicado_jefe_dep,
            parte_rotura, parte_ampliacion,
            proveedor_id, observaciones,
            familia_id, importe, sujeto_techo,
            creado_por_id, modificado_por_id
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        RETURNING id
    """, (
        norden,
        data.get("hotel_id"), data.get("departamento_id"),
        data.get("fecha_solicitud"), data.get("fecha_envio_visto_bueno"),
        data.get("fecha_tramitacion"),
        data.get("pedido_num"), data.get("presupuesto_num"),
        data.get("entrada_albaran_num"),
        estado,
        1 if data.get("comunicado_ab") else 0,
        1 if data.get("comunicado_jefe_dep") else 0,
        1 if data.get("parte_rotura") else 0,
        1 if data.get("parte_ampliacion") else 0,
        data.get("proveedor_id"), data.get("observaciones"),
        familia_id, importe, sujeto_techo,
        uid, uid,
    ))
    pedido_id = cur.fetchone()["id"]

    execute(
        "INSERT INTO historial_estados (pedido_id,estado_nuevo,usuario_id,nota) VALUES (%s,%s,%s,%s)",
        (pedido_id, estado, uid, "Pedido creado")
    )
    db.commit()

    enviar_emails_estado(db, pedido_id, estado)
    return jsonify({"ok": True, "id": pedido_id, "norden": norden}), 201

@app.route("/api/pedidos/<int:pid>", methods=["PUT"])
@login_required
def update_pedido(pid):
    data = request.get_json(silent=True) or {}
    db   = get_db()
    uid  = current_user_id()

    pedido_actual = row_to_dict(query("SELECT * FROM pedidos WHERE id=%s", (pid,), one=True))
    if not pedido_actual:
        return jsonify({"error": "No encontrado"}), 404

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
            estado=%s,
            comunicado_ab=%s, comunicado_jefe_dep=%s,
            parte_rotura=%s, parte_ampliacion=%s,
            proveedor_id=%s, observaciones=%s,
            familia_id=%s, importe=%s, sujeto_techo=%s,
            modificado_por_id=%s, modificado_en=NOW()
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
        estado_nuevo,
        1 if data.get("comunicado_ab",       pedido_actual["comunicado_ab"]) else 0,
        1 if data.get("comunicado_jefe_dep", pedido_actual["comunicado_jefe_dep"]) else 0,
        1 if data.get("parte_rotura",        pedido_actual["parte_rotura"]) else 0,
        1 if data.get("parte_ampliacion",    pedido_actual["parte_ampliacion"]) else 0,
        data.get("proveedor_id",  pedido_actual["proveedor_id"]),
        data.get("observaciones", pedido_actual["observaciones"]),
        familia_id, importe, sujeto_techo,
        uid, pid,
    ))

    if estado_nuevo != estado_antes:
        execute(
            "INSERT INTO historial_estados (pedido_id,estado_antes,estado_nuevo,usuario_id,nota) VALUES (%s,%s,%s,%s,%s)",
            (pid, estado_antes, estado_nuevo, uid, data.get("nota_historial", ""))
        )

    db.commit()

    if estado_nuevo != estado_antes:
        enviar_emails_estado(db, pid, estado_nuevo, estado_antes)

    return jsonify({"ok": True})

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
@admin_required
def get_pedidos_eliminados():
    registros = rows_to_list(query(
        "SELECT * FROM pedidos_eliminados ORDER BY eliminado_en DESC"
    ))
    return jsonify({"registros": registros})

# ── API Stats ──────────────────────────────────────────────────────────────────

@app.route("/api/stats")
@login_required
def get_stats():
    total     = query("SELECT COUNT(*) as n FROM pedidos", one=True)["n"]
    by_estado = rows_to_list(query(
        "SELECT estado, COUNT(*) as total FROM pedidos GROUP BY estado ORDER BY total DESC"
    ))
    by_hotel  = rows_to_list(query(
        """SELECT h.codigo, h.nombre, COUNT(p.id) as total
           FROM hoteles h LEFT JOIN pedidos p ON p.hotel_id=h.id
           GROUP BY h.id, h.codigo, h.nombre ORDER BY total DESC"""
    ))
    # ── Alertas por estado cruzando fecha_tramitacion ─────────────────────────
    # Umbrales (días desde fecha_tramitacion):
    #   ENVIADO AL PROVEEDOR               → primera ≥15d; urgente ≥25d; luego c/10d
    #   PENDIENTE FIRMA DIRECCIÓN COMPRAS  → aviso c/8d
    #   PENDIENTE DE FIRMA DIRECCIÓN HOTEL → aviso c/5d
    #   ENTREGA PARCIAL                    → aviso c/10d
    #   ENTREGADO / CANCELADO              → sin alerta
    alertas_raw = rows_to_list(query(f"""
        {PEDIDO_SELECT}
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

    from datetime import date as _date, datetime as _dt

    def _dias_desde(fecha_str):
        if not fecha_str:
            return None
        try:
            if hasattr(fecha_str, 'date'):
                f = fecha_str.date()
            elif isinstance(fecha_str, _date):
                f = fecha_str
            else:
                s = str(fecha_str)[:10]
                f = _dt.strptime(s, "%Y-%m-%d").date()
            return (_date.today() - f).days
        except Exception:
            return None

    UMBRALES = {
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

    alertas = []
    for p in alertas_raw:
        cfg = UMBRALES.get(p["estado"])
        if not cfg:
            continue
        # Elegir la fecha de referencia según el estado
        fecha_ref_campo = cfg.get("fecha_ref", "fecha_tramitacion")
        dias = _dias_desde(p.get(fecha_ref_campo))
        if dias is None:
            continue

        primera = cfg["primera"]
        urgente = cfg["urgente"]

        if dias < primera:
            continue  # aún no toca avisar

        nivel = "urgente" if (urgente and dias >= urgente) else "aviso"
        p["dias_tramitacion"] = dias
        p["nivel_alerta"]     = nivel
        alertas.append(p)

    # Urgentes primero, luego por días descendente
    alertas.sort(key=lambda x: (0 if x["nivel_alerta"] == "urgente" else 1, -x["dias_tramitacion"]))

    return jsonify({
        "total": total, "by_estado": by_estado,
        "by_hotel": by_hotel, "alertas": alertas,
        "num_alertas": len(alertas),
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
            "Nº PRESUPUESTO", "ESTADO", "Nº ENTRADA ALBARÁN",
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
                p.get("entrada_albaran_num"),
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
    try:
        import openpyxl
        from datetime import datetime as dt

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
                "albaran_num": col(row, "Nº ENTRADA ALBARÁN"),
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
            with db.cursor() as cur_i:
                pedido_rows = [
                    (f["norden"], f["hotel_id"], f["depto_id"],
                     f["fecha_sol"], f["fecha_env"], f["fecha_tra"],
                     f["pedido_num"], f["presup_num"], f["albaran_num"],
                     f["estado"], f["com_ab"], f["com_jefe"],
                     f["p_rotura"], f["p_amplia"], f["prov_id"],
                     f["obs"], uid, uid)
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
                        creado_por_id, modificado_por_id
                    ) VALUES %s RETURNING id
                """, pedido_rows, fetch=True)

                insertados = len(ids)

                historial_rows = [
                    (ids[idx]["id"], filas_validas[idx]["estado"], uid, "Importado desde Excel (reset completo)")
                    for idx in range(len(ids))
                ]
                execute_values(cur_i, """
                    INSERT INTO historial_estados (pedido_id, estado_nuevo, usuario_id, nota)
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
                "albaran_num": col(row, "Nº ENTRADA ALBARÁN"),
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
            with db.cursor() as cur_i:
                pedido_rows = [
                    (f["norden"], f["hotel_id"], f["depto_id"],
                     f["fecha_sol"], f["fecha_env"], f["fecha_tra"],
                     f["pedido_num"], f["presup_num"], f["albaran_num"],
                     f["estado"], f["com_ab"], f["com_jefe"],
                     f["p_rotura"], f["p_amplia"], f["prov_id"],
                     f["obs"], uid, uid)
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
                        creado_por_id, modificado_por_id
                    ) VALUES %s RETURNING id
                """, pedido_rows, fetch=True)

                insertados = len(ids)

                historial_rows = [
                    (ids[idx]["id"], filas_validas[idx]["estado"], uid, "Importado desde Excel")
                    for idx in range(len(ids))
                ]
                execute_values(cur_i, """
                    INSERT INTO historial_estados (pedido_id, estado_nuevo, usuario_id, nota)
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
            "Nº PRESUPUESTO", "ESTADO", "Nº ENTRADA ALBARÁN",
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
                p.get("entrada_albaran_num"),
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
MAX_ADJUNTO_BYTES = 20 * 1024 * 1024  # 20 MB por archivo

@app.route("/api/pedidos/<int:pid>/adjuntos", methods=["GET"])
@login_required
def get_adjuntos(pid):
    rows = query(
        "SELECT id, tipo, nombre, mime_type, creado_en FROM pedido_adjuntos WHERE pedido_id=%s ORDER BY tipo, creado_en",
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

    if tipo in ("presupuesto_pdf", "pedido_pdf"):
        if mime != "application/pdf":
            return jsonify({"ok": False, "error": "Solo se aceptan archivos PDF en este apartado"}), 400

    elif tipo in ("pedido_doc", "presupuesto_doc"):
        if mime not in MIME_SOLICITUD_DOC:
            return jsonify({"ok": False, "error": "Formato no permitido. Use PDF, Word o correo (.eml/.msg)"}), 400
        if mime == "application/octet-stream" and ext not in EXT_CORREO | EXT_DOC:
            return jsonify({"ok": False, "error": "Extensión de archivo no reconocida"}), 400

    elif tipo == "solicitud_doc":
        if mime not in MIME_SOLICITUD_DOC:
            return jsonify({"ok": False, "error": "Formato no permitido. Use Excel, Word, PDF o correo (.eml/.msg)"}), 400
        if mime == "application/octet-stream" and ext not in EXT_CORREO | EXT_DOC:
            return jsonify({"ok": False, "error": "Extension de archivo no reconocida"}), 400

    elif tipo in ("vb_eml", "tramit_eml"):
        if mime not in MIME_CORREO:
            return jsonify({"ok": False, "error": "Solo se aceptan correos electronicos (.eml, .msg)"}), 400
        if mime == "application/octet-stream" and ext not in EXT_CORREO:
            return jsonify({"ok": False, "error": "Solo se aceptan archivos .eml o .msg"}), 400

    else:
        if mime not in MIME_PERMITIDOS:
            return jsonify({"ok": False, "error": f"Tipo de archivo no permitido: {mime}"}), 400

    uid = current_user_id()
    db  = get_db()
    cur = execute(
        "INSERT INTO pedido_adjuntos (pedido_id, tipo, nombre, mime_type, datos, subido_por_id) VALUES (%s,%s,%s,%s,%s,%s) RETURNING id",
        (pid, tipo, archivo.filename, mime, psycopg2.Binary(datos), uid)
    )
    adjunto_id = cur.fetchone()["id"]
    db.commit()
    return jsonify({"ok": True, "id": adjunto_id}), 201


@app.route("/api/adjuntos/<int:aid>", methods=["GET"])
@login_required
def download_adjunto(aid):
    from flask import Response
    row = query("SELECT nombre, mime_type, datos FROM pedido_adjuntos WHERE id=%s", (aid,), one=True)
    if not row:
        return jsonify({"ok": False, "error": "Adjunto no encontrado"}), 404
    # Los correos (.eml/.msg) se sirven como attachment para que el SO
    # los abra con el gestor de correo predeterminado.
    # El resto (PDF, imagenes, Word) se sirven inline para previsualizacion.
    ext = os.path.splitext(row["nombre"].lower())[1]
    disposition = "attachment" if ext in {".eml", ".msg"} else "inline"
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

# ── Arranque ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
