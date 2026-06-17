# =============================================================================
#  restore_agent.py — Agente local de restauración (Opción C)
#  © VAMA 2026 — Central Compras Princess Canarias
#
#  Qué hace en cada ciclo:
#    0. Caduca peticiones 'pendiente' con más de 24h sin ser recogidas
#       (estado → 'error', error_msg explicativo). Evita peticiones zombi
#       si el agente estuvo parado varios días.
#    1. Consulta la tabla `restore_queue` en Supabase.
#    2. Si hay una petición en estado 'pendiente', la marca 'en_proceso'.
#    3. Genera un BACKUP DE SEGURIDAD AUTOMÁTICO del estado actual
#       (carpeta pre_restore_YYYYMMDD_HHMMSS) ANTES de tocar nada.
#       Si este paso falla, la restauración se aborta sin borrar nada.
#    4. Lee el backup solicitado desde la carpeta de red (\\shtabaiba\...).
#    5. Borra los datos actuales en Supabase y los reemplaza por los del backup
#       (modo "pedidos" o "completo", según se eligió en el panel web).
#    6. Sube los adjuntos como ficheros binarios a pedido_adjuntos.
#    7. Marca la petición como 'completado' (con resumen) o 'error'.
#
#  El panel web NUNCA restaura directamente: solo inserta la fila en
#  restore_queue. Este script, ejecutado en tu PC con acceso a la red local
#  y a Supabase, es el único que ejecuta la restauración real.
#
#  Si algo sale mal durante la restauración, el backup pre_restore_* generado
#  en el paso 3 permite deshacer el desaguisado restaurándolo manualmente
#  desde el propio panel web, como cualquier otro backup.
#
#  Uso manual:
#    python restore_agent.py            (un solo ciclo y termina)
#    python restore_agent.py --loop      (bucle infinito, comprueba cada 60s)
#
#  Uso automático: ver restore_agent.bat + Programador de Tareas de Windows.
# =============================================================================

import os
import sys
import json
import re
import time
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path

import psycopg2
import psycopg2.extras

# ── Configuración ─────────────────────────────────────────────────────────────

DATABASE_URL         = os.environ.get("DATABASE_URL", "")
INTERVALO_SEGUNDOS   = int(os.environ.get("RESTORE_AGENT_INTERVALO", "60"))
CADUCIDAD_HORAS      = int(os.environ.get("RESTORE_AGENT_CADUCIDAD_HORAS", "24"))

TABLAS_JSON = [
    "hoteles", "departamentos", "familias",
    "proveedores", "proveedor_contactos",
    "usuarios",
    "pedidos", "historial_estados",
    "pedidos_eliminados",
    "emails_log", "whatsapp_log",
]

MIME_MAP = {
    ".pdf":  "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".doc":  "application/msword",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".xls":  "application/vnd.ms-excel",
    ".png":  "image/png",
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
    ".eml":  "message/rfc822",
    ".msg":  "application/vnd.ms-outlook",
}

PATRON_ADJUNTO = re.compile(r"^pedido_(\d+)_(.+?)_(.+)$")

# ── Fix v11.8.6 — Caché de listado de backups (ver sincronizar_cache_backups) ──
PATRON_BACKUP_DIARIO      = re.compile(r"^backup_(\d{8})_(\d{4})$")
PATRON_BACKUP_PRE_RESTORE = re.compile(r"^pre_restore_(\d{8})_(\d{6})$")


def normalizar_ruta_backup(ruta):
    """Debe coincidir exactamente con _normalizar_ruta_backup() en app.py."""
    return ruta.strip().rstrip("\\/").lower()


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def conectar():
    return psycopg2.connect(
        DATABASE_URL,
        cursor_factory=psycopg2.extras.RealDictCursor,
        connect_timeout=30,
    )


def nombre_seguro(texto):
    for c in r'\/:*?"<>|':
        texto = texto.replace(c, "_")
    return texto.strip()


def insertar_filas(cur, conn, tabla, filas, excluir_ids=None):
    if not filas:
        return 0
    excluir_ids = excluir_ids or []
    cols   = [k for k in filas[0].keys() if k != "id"]
    ph     = ", ".join(["%s"] * len(cols))
    campos = ", ".join(cols)
    n = 0
    for fila in filas:
        if fila.get("id") in excluir_ids:
            continue
        vals = [fila.get(c) for c in cols]
        try:
            cur.execute(f"INSERT INTO {tabla} ({campos}) VALUES ({ph})", vals)
            n += 1
        except Exception as e:
            log(f"  AVISO: fila saltada en {tabla}: {e}")
            conn.rollback()
    return n


# ── PUNTO A: Backup de seguridad automático antes de restaurar ───────────────

def crear_backup_seguridad(conn, carpeta_destino_base):
    """
    Genera una copia de seguridad completa del estado ACTUAL de la base de
    datos (igual que backup_pedidos.py) justo antes de aplicar una
    restauración. Si algo sale mal durante la restauración, este backup
    permite volver atrás sin pérdida de datos.

    Devuelve el nombre de la carpeta creada, p.ej. "pre_restore_20260616_183501".
    Lanza excepción si no consigue completarlo (la restauración se aborta).
    """
    ts      = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre  = f"pre_restore_{ts}"
    carpeta = Path(carpeta_destino_base) / nombre
    adj_dir = carpeta / "adjuntos"

    carpeta.mkdir(parents=True, exist_ok=False)
    adj_dir.mkdir(parents=True, exist_ok=False)

    log(f"  Generando backup de seguridad previo: {nombre}")

    with conn.cursor() as cur:
        datos       = {}
        total_filas = 0

        for tabla in TABLAS_JSON:
            cur.execute(f"SELECT * FROM {tabla}")
            filas = cur.fetchall()
            datos[tabla] = json.loads(json.dumps([dict(f) for f in filas], default=str))
            total_filas += len(filas)

        with open(carpeta / "datos.json", "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)

        cur.execute("""
            SELECT pa.id, pa.pedido_id, pa.nombre, pa.mime_type, pa.datos, pa.tipo,
                   p.norden
            FROM pedido_adjuntos pa
            JOIN pedidos p ON p.id = pa.pedido_id
            ORDER BY p.norden, pa.id
        """)
        adjuntos    = cur.fetchall()
        n_adj       = 0
        bytes_total = 0

        for adj in adjuntos:
            tipo_tag = nombre_seguro(adj["tipo"] or "adj")
            nom_orig = nombre_seguro(adj["nombre"] or f"adjunto_{adj['id']}")
            nom_fich = f"pedido_{adj['norden']:04d}_{tipo_tag}_{nom_orig}"
            if len(nom_fich) > 200:
                ext      = Path(nom_orig).suffix
                nom_fich = nom_fich[:195] + ext

            raw = bytes(adj["datos"])
            with open(adj_dir / nom_fich, "wb") as f:
                f.write(raw)
            n_adj       += 1
            bytes_total += len(raw)

    with open(carpeta / "backup_log.txt", "w", encoding="utf-8") as flog:
        flog.write("=" * 60 + "\n")
        flog.write("  BACKUP DE SEGURIDAD PRE-RESTAURACION (automatico)\n")
        flog.write(f"  Generado por : restore_agent.py\n")
        flog.write(f"  Fecha/hora   : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        flog.write(f"  Motivo       : restauracion de otro backup solicitada desde el panel web\n")
        flog.write("=" * 60 + "\n\n")
        flog.write(f"Tablas exportadas : {len(TABLAS_JSON)}\n")
        flog.write(f"Filas totales     : {total_filas:,}\n")
        flog.write(f"Adjuntos          : {n_adj}\n")
        flog.write(f"Tamano adjuntos   : {bytes_total / (1024*1024):.2f} MB\n")
        flog.write("\nEste backup se genero automaticamente como red de seguridad.\n")
        flog.write("Puedes restaurarlo desde el panel web igual que cualquier otro backup\n")
        flog.write("si la restauracion que lo origino no dio el resultado esperado.\n")

    log(f"  Backup de seguridad completado: {n_adj} adjuntos, {total_filas} filas")
    return nombre


# ── PUNTO C: Caducidad de peticiones pendientes ───────────────────────────────

def caducar_pendientes_antiguas(conn):
    """
    Marca como 'error' cualquier petición 'pendiente' con más de
    CADUCIDAD_HORAS sin ser recogida (p.ej. el agente estuvo parado varios
    días). Evita que el panel web muestre "esperando..." indefinidamente
    sobre una petición que ya no tiene sentido ejecutar a ciegas.
    """
    limite = datetime.now(timezone.utc) - timedelta(hours=CADUCIDAD_HORAS)

    with conn.cursor() as cur:
        cur.execute("""
            UPDATE restore_queue
            SET estado = 'error',
                completado_en = NOW(),
                error_msg = %s
            WHERE estado = 'pendiente' AND solicitado_en < %s
            RETURNING id, backup_nombre
        """, (
            f"Peticion caducada: lleva pendiente mas de {CADUCIDAD_HORAS}h sin que "
            f"el agente local la procesara. Si el PC estuvo apagado o sin red, "
            f"vuelve a solicitar la restauracion desde el panel.",
            limite
        ))
        caducadas = cur.fetchall()
        conn.commit()

    for c in caducadas:
        log(f"  Peticion #{c['id']} ({c['backup_nombre']}) caducada por antiguedad")

    return len(caducadas)


# ── Fix v11.8.6 — Caché de listado de backups ─────────────────────────────────
#
# El panel web (/api/admin/backup/listar) corre en Render y no tiene acceso
# a la carpeta de red local, igual que ya pasaba con la restauración. Este
# agente, que sí tiene acceso, escanea la carpeta en cada ciclo y sube el
# resultado a la tabla `backups_cache` en Supabase; el panel web solo lee
# esa tabla.

def escanear_carpeta_backups(carpeta):
    """
    Escanea `carpeta` en busca de subcarpetas de backup (diario o
    pre_restore) y devuelve una lista de dicts listos para subir a
    `backups_cache`. Si la carpeta no existe o no hay permisos, la
    excepción se propaga tal cual para que el llamante decida qué hacer
    (no se toca la caché existente en ese caso).
    """
    resultado = []

    for entry in sorted(carpeta.iterdir(), reverse=True):
        if not entry.is_dir():
            continue

        m_diario = PATRON_BACKUP_DIARIO.match(entry.name)
        m_pre    = PATRON_BACKUP_PRE_RESTORE.match(entry.name)

        if m_diario:
            fecha_str, hora_str = m_diario.group(1), m_diario.group(2)
            fecha_fmt = f"{fecha_str[6:8]}/{fecha_str[4:6]}/{fecha_str[:4]} {hora_str[:2]}:{hora_str[2:]}"
            fecha_raw = datetime.strptime(fecha_str + hora_str, "%Y%m%d%H%M")
            tipo = "diario"
        elif m_pre:
            fecha_str, hora_str = m_pre.group(1), m_pre.group(2)
            fecha_fmt = f"{fecha_str[6:8]}/{fecha_str[4:6]}/{fecha_str[:4]} {hora_str[:2]}:{hora_str[2:4]}:{hora_str[4:6]}"
            fecha_raw = datetime.strptime(fecha_str + hora_str, "%Y%m%d%H%M%S")
            tipo = "pre_restore"
        else:
            continue

        total_bytes = sum(f.stat().st_size for f in entry.rglob("*") if f.is_file())
        mb          = total_bytes / (1024 * 1024)
        adj_dir     = entry / "adjuntos"
        n_adjuntos  = len(list(adj_dir.iterdir())) if adj_dir.exists() else 0

        log_path   = entry / "backup_log.txt"
        tiene_log  = log_path.exists()
        log_texto  = None
        if tiene_log:
            try:
                log_texto = log_path.read_text(encoding="utf-8", errors="replace")
                if len(log_texto) > 300_000:
                    log_texto = log_texto[:300_000] + "\n\n[... log truncado, demasiado largo para la caché ...]"
            except Exception as e:
                log_texto = f"[No se pudo leer backup_log.txt: {e}]"

        resultado.append({
            "nombre":        entry.name,
            "fecha":         fecha_fmt,
            "fecha_raw":     fecha_raw,
            "mb":            round(mb, 1),
            "adjuntos":      n_adjuntos,
            "tiene_log":     tiene_log,
            "log_contenido": log_texto,
            "valido":        (entry / "datos.json").exists(),
            "tipo":          tipo,
        })

    return resultado


def sincronizar_cache_backups(conn, carpeta_str):
    """
    Escanea la carpeta de backups configurada y actualiza `backups_cache`
    en Supabase. Si el escaneo falla (carpeta no accesible, PC sin red al
    recurso, etc.) NO se borra la caché existente: se deja como estaba y
    el panel web mostrará el aviso de "agente sin sincronizar" en cuanto
    lleve unos minutos desactualizada, en vez de mostrar una lista vacía
    o un error confuso.
    """
    carpeta   = Path(carpeta_str)
    ruta_norm = normalizar_ruta_backup(carpeta_str)

    # Tabla creada también desde app.py (_auto_migrate); se repite aquí por
    # si el agente arranca antes de que la web haya hecho su primer arranque.
    try:
        with conn.cursor() as cur:
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
        conn.commit()
    except Exception as e:
        conn.rollback()
        log(f"  AVISO: no se pudo verificar/crear backups_cache: {e}")
        return

    scan_inicio = datetime.now(timezone.utc)

    try:
        backups = escanear_carpeta_backups(carpeta)
    except Exception as e:
        log(f"  AVISO: no se pudo escanear '{carpeta_str}' para la cache de backups: {e}")
        return

    try:
        with conn.cursor() as cur:
            for b in backups:
                cur.execute("""
                    INSERT INTO backups_cache
                        (ruta, ruta_normalizada, nombre, fecha, fecha_raw,
                         mb, adjuntos, tiene_log, log_contenido, valido, tipo, actualizado_en)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (ruta_normalizada, nombre) DO UPDATE SET
                        ruta           = EXCLUDED.ruta,
                        fecha          = EXCLUDED.fecha,
                        fecha_raw      = EXCLUDED.fecha_raw,
                        mb             = EXCLUDED.mb,
                        adjuntos       = EXCLUDED.adjuntos,
                        tiene_log      = EXCLUDED.tiene_log,
                        log_contenido  = EXCLUDED.log_contenido,
                        valido         = EXCLUDED.valido,
                        tipo           = EXCLUDED.tipo,
                        actualizado_en = NOW()
                """, (
                    carpeta_str, ruta_norm, b["nombre"], b["fecha"], b["fecha_raw"],
                    b["mb"], b["adjuntos"], b["tiene_log"], b["log_contenido"],
                    b["valido"], b["tipo"],
                ))

            # Backups que ya no están en la carpeta (borrados manualmente,
            # rotación antigua...) se retiran de la caché.
            cur.execute("""
                DELETE FROM backups_cache
                WHERE ruta_normalizada = %s AND actualizado_en < %s
            """, (ruta_norm, scan_inicio))
            eliminados = cur.rowcount

        conn.commit()

        if eliminados:
            log(f"  Cache de backups: {len(backups)} activo(s), {eliminados} retirado(s) (ya no existen)")
        else:
            log(f"  Cache de backups sincronizada: {len(backups)} backup(s) en '{carpeta_str}'")

    except Exception as e:
        conn.rollback()
        log(f"  AVISO: fallo sincronizando backups_cache: {e}")


def procesar_peticion(conn, peticion, carpeta_pre_restore_base):
    """Ejecuta la restauración real para una petición de la cola."""
    queue_id = peticion["id"]
    nombre   = peticion["backup_nombre"]
    ruta     = peticion["backup_ruta"]
    modo     = peticion["modo"]

    log(f"Procesando peticion #{queue_id}: backup={nombre} modo={modo}")

    carpeta_backup = Path(ruta) / nombre
    json_path      = carpeta_backup / "datos.json"
    adj_dir        = carpeta_backup / "adjuntos"

    if not carpeta_backup.exists():
        raise FileNotFoundError(f"Carpeta de backup no accesible: {carpeta_backup}")
    if not json_path.exists():
        raise FileNotFoundError(f"datos.json no encontrado en {carpeta_backup}")

    # ── PASO PREVIO OBLIGATORIO: backup de seguridad del estado actual ───────
    try:
        nombre_pre_restore = crear_backup_seguridad(conn, carpeta_pre_restore_base)
    except Exception as e:
        raise RuntimeError(
            f"No se pudo generar el backup de seguridad previo (la restauracion "
            f"se ha abortado sin tocar datos): {e}"
        )

    with conn.cursor() as cur:
        cur.execute(
            "UPDATE restore_queue SET pre_restore_backup = %s WHERE id = %s",
            (nombre_pre_restore, queue_id)
        )
        conn.commit()

    with open(json_path, "r", encoding="utf-8") as f:
        datos = json.load(f)

    resumen = {"pre_restore_backup": nombre_pre_restore}

    with conn.cursor() as cur:

        cur.execute("DELETE FROM pedidos")
        cur.execute("DELETE FROM pedidos_eliminados")
        cur.execute("DELETE FROM emails_log")
        cur.execute("DELETE FROM whatsapp_log")
        log(f"  Pedidos, historial, adjuntos y logs borrados. Modo={modo}")

        uid_admin_actual = None
        if modo == "completo":
            solicitante = peticion.get("solicitado_por")
            if solicitante:
                cur.execute("SELECT id FROM usuarios WHERE username = %s OR nombre = %s",
                            (solicitante, solicitante))
                row = cur.fetchone()
                uid_admin_actual = row["id"] if row else None

            cur.execute("DELETE FROM proveedores")
            cur.execute("DELETE FROM familias")
            cur.execute("DELETE FROM hoteles")
            cur.execute("DELETE FROM departamentos")
            if uid_admin_actual:
                cur.execute("DELETE FROM usuarios WHERE id != %s", (uid_admin_actual,))
            else:
                log("  AVISO: no se identifico al usuario solicitante; "
                    "se conservan TODOS los usuarios actuales por seguridad")
            log("  Borrado completo (proveedores, familias, hoteles, departamentos)")

        if modo == "completo":
            resumen["proveedores"]   = insertar_filas(cur, conn, "proveedores",         datos.get("proveedores", []))
            resumen["contactos"]     = insertar_filas(cur, conn, "proveedor_contactos", datos.get("proveedor_contactos", []))
            resumen["familias"]      = insertar_filas(cur, conn, "familias",            datos.get("familias", []))
            resumen["hoteles"]       = insertar_filas(cur, conn, "hoteles",             datos.get("hoteles", []))
            resumen["departamentos"] = insertar_filas(cur, conn, "departamentos",       datos.get("departamentos", []))
            excluir = [uid_admin_actual] if uid_admin_actual else []
            resumen["usuarios"]      = insertar_filas(cur, conn, "usuarios",            datos.get("usuarios", []),
                                                       excluir_ids=excluir)

        resumen["pedidos"]            = insertar_filas(cur, conn, "pedidos",            datos.get("pedidos", []))
        resumen["historial"]          = insertar_filas(cur, conn, "historial_estados",  datos.get("historial_estados", []))
        resumen["pedidos_eliminados"] = insertar_filas(cur, conn, "pedidos_eliminados", datos.get("pedidos_eliminados", []))
        resumen["emails_log"]         = insertar_filas(cur, conn, "emails_log",         datos.get("emails_log", []))
        resumen["whatsapp_log"]       = insertar_filas(cur, conn, "whatsapp_log",       datos.get("whatsapp_log", []))

        log(f"  Tablas restauradas: { {k:v for k,v in resumen.items() if k!='pre_restore_backup'} }")

        n_adj       = 0
        errores_adj = []

        if adj_dir.exists():
            cur.execute("SELECT id, norden FROM pedidos")
            mapa_pedidos = {row["norden"]: row["id"] for row in cur.fetchall()}

            ficheros = sorted(adj_dir.iterdir())
            log(f"  Restaurando {len(ficheros)} adjuntos...")

            for fichero in ficheros:
                if not fichero.is_file():
                    continue
                m = PATRON_ADJUNTO.match(fichero.name)
                if not m:
                    continue

                norden    = int(m.group(1))
                tipo      = m.group(2)
                nom_orig  = m.group(3)
                pedido_id = mapa_pedidos.get(norden)

                if not pedido_id:
                    errores_adj.append(f"Pedido norden={norden} no encontrado para {fichero.name}")
                    continue

                mime_type = MIME_MAP.get(fichero.suffix.lower(), "application/octet-stream")

                try:
                    raw = fichero.read_bytes()
                    cur.execute(
                        "INSERT INTO pedido_adjuntos (pedido_id, tipo, nombre, mime_type, datos) "
                        "VALUES (%s, %s, %s, %s, %s)",
                        (pedido_id, tipo, nom_orig, mime_type, raw)
                    )
                    n_adj += 1
                except Exception as e:
                    errores_adj.append(f"{fichero.name}: {e}")

        resumen["adjuntos"] = n_adj
        resumen["errores"]  = len(errores_adj)
        if errores_adj:
            resumen["errores_detalle"] = errores_adj[:15]
            log(f"  AVISO: {len(errores_adj)} adjuntos con error")

        conn.commit()

    log(f"  Adjuntos restaurados: {n_adj} | Errores: {resumen['errores']}")
    return resumen


def ejecutar_ciclo(carpeta_pre_restore_base):
    if not DATABASE_URL:
        log("ERROR: la variable de entorno DATABASE_URL no esta configurada.")
        return False

    try:
        conn = conectar()
    except Exception as e:
        log(f"ERROR: no se pudo conectar a Supabase: {e}")
        return False

    try:
        n_caducadas = caducar_pendientes_antiguas(conn)
        if n_caducadas:
            log(f"  {n_caducadas} peticion(es) caducada(s) por superar {CADUCIDAD_HORAS}h pendientes")

        sincronizar_cache_backups(conn, str(carpeta_pre_restore_base))

        with conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM restore_queue
                WHERE estado = 'pendiente'
                ORDER BY solicitado_en ASC
                LIMIT 1
            """)
            peticion = cur.fetchone()

        if not peticion:
            return False

        queue_id = peticion["id"]

        with conn.cursor() as cur:
            cur.execute(
                "UPDATE restore_queue SET estado='en_proceso', iniciado_en=NOW() WHERE id=%s",
                (queue_id,)
            )
            conn.commit()

        log(f"Peticion #{queue_id} marcada como en_proceso")

        try:
            resumen = procesar_peticion(conn, peticion, carpeta_pre_restore_base)

            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE restore_queue
                    SET estado='completado', completado_en=NOW(), resumen=%s
                    WHERE id=%s
                """, (json.dumps(resumen, default=str), queue_id))
                conn.commit()

            log(f"Peticion #{queue_id} completada correctamente "
                f"(backup de seguridad previo: {resumen.get('pre_restore_backup')})")

        except Exception as e:
            conn.rollback()
            error_txt = f"{e}"
            log(f"ERROR procesando peticion #{queue_id}: {error_txt}")
            traceback.print_exc()

            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE restore_queue
                    SET estado='error', completado_en=NOW(), error_msg=%s
                    WHERE id=%s
                """, (error_txt, queue_id))
                conn.commit()

        return True

    finally:
        conn.close()


def main():
    modo_loop = "--loop" in sys.argv

    backup_destino_base = os.environ.get("BACKUP_DESTINO", str(Path(__file__).parent))
    carpeta_pre_restore_base = Path(backup_destino_base)

    log("=" * 60)
    log("  AGENTE LOCAL DE RESTAURACION - Princess Canarias")
    log(f"  Modo                : {'bucle continuo (cada ' + str(INTERVALO_SEGUNDOS) + 's)' if modo_loop else 'un solo ciclo'}")
    log(f"  Caducidad pendientes: {CADUCIDAD_HORAS}h")
    log(f"  Backups pre-restore : {carpeta_pre_restore_base}")
    log("=" * 60)

    if not modo_loop:
        hubo_trabajo = ejecutar_ciclo(carpeta_pre_restore_base)
        if not hubo_trabajo:
            log("No hay peticiones pendientes.")
        return 0

    log("Iniciando bucle. Pulsa Ctrl+C para detener.")
    while True:
        try:
            ejecutar_ciclo(carpeta_pre_restore_base)
        except Exception as e:
            log(f"ERROR inesperado en el ciclo: {e}")
            traceback.print_exc()
        time.sleep(INTERVALO_SEGUNDOS)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        log("Detenido por el usuario.")
        sys.exit(0)
