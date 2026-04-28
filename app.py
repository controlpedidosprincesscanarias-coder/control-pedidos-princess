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

# ── Base de datos (psycopg2 / PostgreSQL) ─────────────────────────────────────

def get_db():
    if "db" not in g:
        g.db = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
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
                  pr.nombre as proveedor_nombre, pr.email as proveedor_email
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
            _log_email(db, dest, "interno", dest, subject, ok)

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
    return jsonify({"ok": True, "username": user["username"],
                    "nombre": user["nombre"], "rol": user["rol"]})

@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True})

@app.route("/api/me")
def me():
    if "user_id" not in session:
        return jsonify({"logged": False})
    return jsonify({"logged": True, "username": session["username"],
                    "nombre": session["nombre"], "rol": session["rol"]})

# ── API Maestros ───────────────────────────────────────────────────────────────

@app.route("/api/maestros")
@login_required
def get_maestros():
    hoteles       = rows_to_list(query("SELECT * FROM hoteles WHERE activo=1 ORDER BY codigo"))
    departamentos = rows_to_list(query("SELECT * FROM departamentos WHERE activo=1 ORDER BY nombre"))
    proveedores   = rows_to_list(query("SELECT * FROM proveedores WHERE activo=1 ORDER BY nombre"))
    return jsonify({
        "hoteles":       hoteles,
        "departamentos": departamentos,
        "proveedores":   proveedores,
        "estados":       ESTADOS_VALIDOS,
    })

# ── API Proveedores ────────────────────────────────────────────────────────────

@app.route("/api/proveedores", methods=["GET"])
@login_required
def get_proveedores():
    q = request.args.get("q", "").strip()
    if q:
        rows = query("SELECT * FROM proveedores WHERE activo=1 AND nombre ILIKE %s ORDER BY nombre",
                     (f"%{q}%",))
    else:
        rows = query("SELECT * FROM proveedores WHERE activo=1 ORDER BY nombre")
    return jsonify(rows_to_list(rows))

@app.route("/api/proveedores", methods=["POST"])
@login_required
def create_proveedor():
    data   = request.get_json(silent=True) or {}
    nombre = (data.get("nombre") or "").strip()
    if not nombre:
        return jsonify({"error": "Nombre requerido"}), 400
    db  = get_db()
    cur = execute(
        "INSERT INTO proveedores (nombre,email,telefono,contacto) VALUES (%s,%s,%s,%s) RETURNING id",
        (nombre, data.get("email",""), data.get("telefono",""), data.get("contacto",""))
    )
    new_id = cur.fetchone()["id"]
    db.commit()
    return jsonify({"ok": True, "id": new_id, "nombre": nombre}), 201

@app.route("/api/proveedores/<int:pid>", methods=["PUT"])
@admin_required
def update_proveedor(pid):
    data = request.get_json(silent=True) or {}
    db   = get_db()
    execute(
        "UPDATE proveedores SET nombre=%s,email=%s,telefono=%s,contacto=%s WHERE id=%s",
        (data.get("nombre",""), data.get("email",""),
         data.get("telefono",""), data.get("contacto",""), pid)
    )
    db.commit()
    return jsonify({"ok": True})

# ── API Pedidos ────────────────────────────────────────────────────────────────

PEDIDO_SELECT = """
    SELECT p.*,
           h.codigo  as hotel_codigo,
           h.nombre  as hotel_nombre,
           d.nombre  as departamento_nombre,
           pr.nombre as proveedor_nombre,
           pr.email  as proveedor_email,
           pr.telefono as proveedor_telefono,
           pr.contacto as proveedor_contacto,
           u1.nombre as creado_por_nombre,
           u2.nombre as modificado_por_nombre
    FROM pedidos p
    LEFT JOIN hoteles       h  ON p.hotel_id          = h.id
    LEFT JOIN departamentos d  ON p.departamento_id   = d.id
    LEFT JOIN proveedores   pr ON p.proveedor_id      = pr.id
    LEFT JOIN usuarios      u1 ON p.creado_por_id     = u1.id
    LEFT JOIN usuarios      u2 ON p.modificado_por_id = u2.id
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
        wheres.append("""
            p.estado IN ('ENVIADO AL PROVEEDOR','PENDIENTE FIRMA DIRECCION COMPRAS',
                         'PENDIENTE DE FIRMA DIRECCION HOTEL','ENTREGA PARCIAL')
            AND NOW() - p.modificado_en >= INTERVAL '7 days'
        """)

    where_sql = ("WHERE " + " AND ".join(wheres)) if wheres else ""

    order_map = {
        "fecha_desc": "p.creado_en DESC",
        "fecha_asc":  "p.creado_en ASC",
        "estado":     "p.estado, p.creado_en DESC",
        "hotel":      "h.codigo, p.creado_en DESC",
    }
    order = order_map.get(request.args.get("orden", ""), "p.creado_en DESC")

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

    cur = execute("""
        INSERT INTO pedidos (
            norden, hotel_id, departamento_id,
            fecha_solicitud, fecha_envio_visto_bueno, fecha_tramitacion,
            pedido_num, presupuesto_num, entrada_albaran_num,
            estado, comunicado_ab, comunicado_jefe_dep,
            parte_rotura, parte_ampliacion,
            proveedor_id, observaciones,
            creado_por_id, modificado_por_id
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
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

    execute("""
        UPDATE pedidos SET
            hotel_id=%s, departamento_id=%s,
            fecha_solicitud=%s, fecha_envio_visto_bueno=%s, fecha_tramitacion=%s,
            pedido_num=%s, presupuesto_num=%s, entrada_albaran_num=%s,
            estado=%s,
            comunicado_ab=%s, comunicado_jefe_dep=%s,
            parte_rotura=%s, parte_ampliacion=%s,
            proveedor_id=%s, observaciones=%s,
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
    db = get_db()
    execute("DELETE FROM pedidos WHERE id=%s", (pid,))
    db.commit()
    return jsonify({"ok": True})

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
    alertas   = rows_to_list(query(f"""
        {PEDIDO_SELECT}
        WHERE p.estado IN ('ENVIADO AL PROVEEDOR','PENDIENTE FIRMA DIRECCION COMPRAS',
                           'PENDIENTE DE FIRMA DIRECCION HOTEL','ENTREGA PARCIAL')
          AND NOW() - p.modificado_en >= INTERVAL '7 days'
        ORDER BY p.modificado_en ASC
        LIMIT 30
    """))
    return jsonify({
        "total": total, "by_estado": by_estado,
        "by_hotel": by_hotel, "alertas": alertas,
        "num_alertas": len(alertas),
    })

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
            "ANULADO":                           "f8d7da",
        }

        for p in pedidos:
            ws.append([
                p.get("norden"), p.get("hotel_codigo"), p.get("departamento_nombre"),
                p.get("fecha_solicitud"), p.get("fecha_envio_visto_bueno"),
                p.get("pedido_num"), p.get("fecha_tramitacion"),
                p.get("presupuesto_num"), p.get("estado"),
                p.get("entrada_albaran_num"),
                "SÍ" if p.get("comunicado_ab") else "NO",
                "SÍ" if p.get("comunicado_jefe_dep") else "NO",
                "SÍ" if p.get("parte_rotura") else "NO",
                "SÍ" if p.get("parte_ampliacion") else "NO",
                p.get("proveedor_nombre"), p.get("proveedor_email"),
                p.get("proveedor_telefono"), p.get("proveedor_contacto"),
                p.get("observaciones"), p.get("creado_por_nombre"), p.get("creado_en"),
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

# ── Ping endpoint (UptimeRobot) ────────────────────────────────────────────────

@app.route("/ping")
def ping():
    return "OK", 200

# ── Arranque ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
