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

### PASO 1b — Chat: ya NO se despliega aquí (desde v12.7.0)

Desde v12.7.0 el chat interno vive en su propio Web Service de Render
(`control_pedidos_chat`), separado de este, para aislar su memoria de la de
pedidos/alertas tras un OOM que se llevaba por delante los dos a la vez.
Ver `GUIA_DESPLIEGUE.md` dentro de ese paquete para desplegarlo. Este
servicio (pedidos) ya no necesita `CHAT_DATABASE_URL` ni el worker
`eventlet`.

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
   - **Start command:** `gunicorn -w 2 app:app`
   - **Plan:** Free

   > ℹ️ **v12.7.0:** ya no hace falta `-k eventlet -w 1`. Ese Start Command
   > era necesario mientras el chat (WebSocket) vivía en este mismo proceso;
   > al haberse movido a su propio servicio (`control_pedidos_chat`), este
   > servicio vuelve a gunicorn estándar y puede usar varios workers (`-w 2`
   > como punto de partida — ajusta según la RAM de tu plan), más robusto
   > que un único proceso. **Importante:** `SECRET_KEY` debe seguir siendo la
   > misma que uses en `control_pedidos_chat` — el chat valida la sesión
   > leyendo la misma cookie que crea el login de este servicio.

4. En **Environment → Add Environment Variable**, añade estas variables:

   | Variable | Valor |
   |---|---|
   | `DATABASE_URL` | La URI de Supabase del Paso 1 |
   | `SECRET_KEY` | Una cadena aleatoria larga (cópiala también en `control_pedidos_chat`) |
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
