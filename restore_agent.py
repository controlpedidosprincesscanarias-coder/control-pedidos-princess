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
