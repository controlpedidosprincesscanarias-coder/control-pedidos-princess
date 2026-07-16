# Guía de despliegue — Control Pedidos Princess
## Stack: Render (Flask) + Supabase (PostgreSQL) + EmailJS (email, frontend) + UptimeRobot (anti-sleep)

> **v9.2.0** — Contactos múltiples por proveedor. Los campos `telefono` y `movil` se han
> unificado en una única columna `telefono` dentro de la tabla `proveedor_contactos`.
> La migración es automática al arrancar la app: si un proveedor tenía datos en los
> campos legacy (`contacto`, `email`, `telefono`, `movil`), se crea automáticamente
> su primer registro de contacto conservando todos los datos.


---

## PASO 1 — Supabase: crear proyecto y base de datos

1. Entra en https://supabase.com → **New project**
   - Nombre: `control-pedidos-princess`
   - Contraseña BD: genera una fuerte y guárdala
   - Región: **West EU (Ireland)** — la más cercana a Canarias

2. Una vez creado, ve a **Settings → Database → Connection string → URI**
   Copia la cadena. Tiene este formato:
   ```
   postgresql://postgres:[TU-PASSWORD]@db.xxxxxxxxxxxx.supabase.co:5432/postgres
   ```
   ⚠️ Sustituye `[TU-PASSWORD]` por la contraseña que pusiste.

3. Ve a **SQL Editor** y ejecuta el schema inicial.
   Puedes hacerlo pegando el contenido de `models.py` (las sentencias en `SQL_STATEMENTS`)
   o dejando que Flask lo ejecute en el primer arranque con `init_db()`.

### PASO 1b — Segunda Supabase, solo para el chat (v12.6.0, opcional)

Las tablas del chat (`chat_canales`, `chat_participantes`, `chat_mensajes`,
`chat_lecturas`) pueden vivir en un proyecto de Supabase **distinto** al de
pedidos, para no competir por la misma cuota de egress/almacenamiento. No es
obligatorio — si no haces este paso, el chat simplemente usa la misma
Supabase de siempre (`DATABASE_URL`) y todo sigue funcionando igual.

1. Repite el punto 1 de arriba, pero con otro nombre: `control-pedidos-chat`.
2. Copia su Connection String (igual que en el punto 2).
3. **No hace falta ejecutar ningún SQL a mano aquí**: la app crea las 4
   tablas del chat sola en el primer arranque (`_auto_migrate_chat()`),
   igual que ya hace con el resto de tablas.
4. En Render añadirás esta URI como variable `CHAT_DATABASE_URL` — ver
   PASO 3.

---

## PASO 2 — EmailJS: envío de email desde el frontend

1. El email se gestiona íntegramente desde el frontend vía EmailJS (sin configuración en el servidor).
2. Ve a **API Keys → Create API Key**
   - Nombre: `princess-pedidos`
   - Permisos: Full access
3. Copia la clave (`re_xxxxxxxxxx...`)

**Opcional — dominio propio:**
Si quieres que los emails salgan desde `compras@princess.es` en lugar de
Configura tu Service ID y Template ID en EmailJS y actualiza las constantes en el frontend.

---

## PASO 3 — Render: desplegar el backend

1. Entra en https://render.com → **New → Web Service**
2. Conecta tu repositorio de GitHub (`control_pedidos_web`)
3. Configura el servicio:
   - **Runtime:** Python 3
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `gunicorn -k eventlet -w 1 app:app`
   - **Plan:** Free

   > ⚠️ **Chat interno (v12.6.0):** el Start Command cambia respecto a versiones
   > anteriores (`gunicorn app:app`, sin `-k eventlet -w 1`). El worker `eventlet`
   > es el que permite mantener las conexiones WebSocket abiertas para el chat en
   > tiempo real. Si por lo que sea no se puede aplicar este cambio (o el
   > **Worker de Cloudflare** que hace de proxy — `proxy.controlpedidosprincess-
   > canarias.workers.dev` — no reenvía la cabecera `Upgrade` de WebSocket, algo
   > que no se puede confirmar sin revisar su código), el chat NO se rompe: la
   > librería cliente de socket.io degrada sola a long-polling. Solo se pierde
   > la entrega instantánea, no la funcionalidad. `-w 1` es intencional: con
   > eventlet, un solo proceso ya gestiona muchas conexiones concurrentes
   > mediante green threads; varios workers de gunicorn partirían las salas de
   > socket.io entre procesos que no se ven entre sí.

4. En **Environment → Add Environment Variable**, añade estas variables:

   | Variable | Valor |
   |---|---|
   | `DATABASE_URL` | La URI de Supabase del Paso 1 |
   | `CHAT_DATABASE_URL` | *(opcional, v12.6.0)* La URI de Supabase del Paso 1b, solo para el chat. Si la omites, el chat usa `DATABASE_URL`. |
   | `SECRET_KEY` | Una cadena aleatoria larga |
   | *(sin variables de email)* | El email se gestiona en el frontend vía EmailJS |
   | `EMAILS_INTERNOS` | `victor.martin@princess.es,jesus.curbelo@princess.es` |

5. Haz clic en **Create Web Service** y espera el primer deploy (~2 min).

6. **Inicializar la base de datos** (solo la primera vez):
   En la consola Shell de Render, ejecuta:
   ```bash
   python -c "from app import init_db; init_db()"
   ```

---

## PASO 4 — Migrar datos del SQLite actual (si tienes pedidos existentes)

En tu máquina local, con el `pedidos.db` descargado de Render:

```bash
pip install psycopg2-binary
python migrate_sqlite_to_pg.py \
  --sqlite pedidos.db \
  --pg "postgresql://postgres:[PASSWORD]@db.xxxx.supabase.co:5432/postgres"
```

El script migra todas las tablas respetando los IDs existentes.

---

## PASO 5 — UptimeRobot: eliminar el letargo de 15 minutos

1. Regístrate en https://uptimerobot.com (plan gratuito: 50 monitores)
2. **New Monitor:**
   - Type: **HTTP(s)**
   - Friendly Name: `Princess Pedidos — keepalive`
   - URL: `https://TU-APP.onrender.com/ping`
   - Monitoring Interval: **Every 14 minutes**
3. Guarda. Ya no habrá más letargo.

El endpoint `/ping` ya está incluido en `app.py` y devuelve `OK 200`.

---

## PASO 6 — Supabase Storage: PDFs (preparación futura)

Cuando necesites subir documentos PDF a los pedidos:

1. En Supabase → **Storage → New bucket**
   - Nombre: `pedidos-docs`
   - Public: No (privado)

2. Instala el cliente:
   ```
   # Añadir a requirements.txt:
   supabase>=2.0
   ```

3. Añade a las variables de entorno en Render:
   ```
   SUPABASE_URL = https://xxxx.supabase.co
   SUPABASE_KEY = eyJ...  (Settings → API → service_role key)
   ```

4. Añade la columna en PostgreSQL (SQL Editor de Supabase):
   ```sql
   ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS documentos_pdf TEXT[];
   ```

5. Snippet de subida (añadir a `app.py` cuando lo necesites):
   ```python
   from supabase import create_client

   _sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])

   def subir_pdf(pedido_id: int, archivo_bytes: bytes, nombre: str) -> str:
       path = f"pedidos/{pedido_id}/{nombre}"
       _sb.storage.from_("pedidos-docs").upload(path, archivo_bytes,
           {"content-type": "application/pdf"})
       return _sb.storage.from_("pedidos-docs").create_signed_url(path, 86400)["signedURL"]
   ```

---

## Resumen de costes

| Servicio | Plan | Coste |
|---|---|---|
| Render | Free | 0 € |
| Supabase | Free (500 MB BD, 1 GB Storage) | 0 € |
| EmailJS | Free tier | 0 € |
| UptimeRobot | Free (50 monitores) | 0 € |
| **TOTAL** | | **0 €/mes** |

---

## Archivos modificados respecto a la versión original

| Archivo | Cambio |
|---|---|
| `app.py` | SQLite → psycopg2; `?` → `%s`; `datetime('now')` → `NOW()`; email via EmailJS (frontend); endpoint `/ping` |
| `models.py` | `SQL_STATEMENTS` como lista; `AUTOINCREMENT` → `SERIAL`; `LIKE` → `ILIKE` disponible |
| `requirements.txt` | Añadido `psycopg2-binary`, `gunicorn`; eliminado lo innecesario |
| `migrate_sqlite_to_pg.py` | Nuevo — migración de datos existentes |
