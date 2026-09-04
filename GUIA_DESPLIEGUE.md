# Guía de despliegue — Control Pedidos Princess
## Stack: Render (Flask) + Supabase (PostgreSQL) + EmailJS (email, frontend) + GitHub Actions (anti-sleep)

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

3. El schema inicial (`models.py` → `SQL_STATEMENTS`) se ejecuta con el
   script `init_db.py` en el **Paso 3.6**, una vez que `DATABASE_URL` ya
   está configurada en Render — no hace falta pegarlo a mano en el SQL
   Editor de Supabase.

### PASO 1b — Chat: ya NO se despliega aquí (desde v12.7.0)

Desde v12.7.0 el chat interno vive en su propio Web Service de Render
(`control_pedidos_chat`), separado de este, para aislar su memoria de la de
pedidos/alertas tras un OOM que se llevaba por delante los dos a la vez.
Ver `GUIA_DESPLIEGUE.md` dentro de ese paquete para desplegarlo. Este
servicio (pedidos) ya no necesita `CHAT_DATABASE_URL` ni el worker
`eventlet`.

---

## PASO 2 — EmailJS: envío de email desde el frontend

> ⚠️ **Corregido (antes se mezclaba con Resend):** los pasos "API Keys →
> Create API Key" y una clave con formato `re_xxxxxxxxxx` que aparecían
> aquí son de **Resend**, no de EmailJS — un cruce de dos proveedores de
> email que llegó a esta guía por error y nunca se corrigió. `RESEND_API_KEY`
> existe como variable opcional en `render.yaml` pero **no la usa
> ningún punto de `app.py` a día de hoy** (verificado por búsqueda
> completa del fichero) — puedes dejarla sin rellenar.

El email se gestiona íntegramente desde el frontend vía EmailJS, sin
necesidad de ninguna variable de entorno en Render. Desde v12.27.8 las
credenciales **no van hardcodeadas en el frontend**: se guardan en la
tabla `config_alertas` y el navegador las pide en cada carga a
`GET /api/emailjs/config`, así que un cambio de cuenta se aplica al
momento, sin desplegar nada.

1. Crea una cuenta en https://www.emailjs.com (plan gratuito: 200
   envíos/mes) y dentro, un **Service** (conecta tu Gmail/Outlook) y una
   **Template**.
2. Copia estos 3 valores: **Public Key** (Account → General), **Service
   ID** y **Template ID** (el de la plantilla que acabas de crear).
3. En la propia app, entra como `admin` → menú lateral **"EmailJS y cola
   de correo"** → pega los 3 valores en **Cuenta 1 (principal)**.
4. **Opcional pero recomendado — failover automático:** repite el
   proceso con hasta 3 cuentas EmailJS gratuitas más (v12.30.93: hasta 4
   cuentas en total en rotación) y rellena también **Cuenta 2**,
   **Cuenta 3** y **Cuenta 4** en ese mismo panel. El sistema lleva la
   cuenta de envíos y, al acercarse al límite gratuito de 200/mes
   (umbral configurable, 195 por defecto), cambia solo a la siguiente
   cuenta del ciclo (1→2→3→4→1→...) sin cortar el envío de correos ni
   requerir ningún despliegue. No hace falta rellenar las 4 desde el
   principio — con solo la Cuenta 1 la app funciona igual, simplemente
   sin failover automático si esa cuenta agota su cupo.

---

## PASO 3 — Render: desplegar el backend

1. Entra en https://render.com → **New → Web Service**
2. Conecta tu repositorio de GitHub (`control_pedidos_web`)
3. Configura el servicio:
   - **Runtime:** Python 3
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --worker-class gthread --threads 4 --timeout 300`
   - **Plan:** Free

   > ℹ️ **v12.29.78 (vigente):** este es el Start Command real, el mismo
   > que usa `render.yaml`. **No uses `gunicorn -w 2 app:app`** (versión
   > antigua de esta guía, hasta v12.29.77): con varios workers "sync",
   > mientras el hilo en segundo plano de "Comparar listado PDF" procesa
   > un PDF (~8s), el worker que lo atiende puede dejar de responder al
   > *health check* (`/ping`) a tiempo — Render lo considera no saludable,
   > **reinicia el contenedor** y el job en memoria se pierde a medias
   > ("El job no existe o ha caducado"). `--worker-class gthread --threads 4`
   > reparte las peticiones entrantes del mismo worker entre varios hilos,
   > así que el health check y los sondeos del navegador se siguen
   > atendiendo con normalidad mientras el hilo de fondo trabaja. No añade
   > ninguna dependencia nueva (`gthread` es un tipo de worker propio de
   > gunicorn). **Importante:** si tu servicio en Render tiene el "Start
   > Command" fijado a mano en el panel (Settings → Start Command) en vez
   > de leerlo de `render.yaml`, tendrás que pegar este comando ahí
   > también — `render.yaml` solo no basta si el servicio no está
   > gestionado como Blueprint desde este archivo. Ver `CHANGELOG.md`
   > v12.29.78 para el detalle completo del incidente que motivó este
   > cambio. (La nota histórica sobre `-k eventlet -w 1` y el chat en
   > WebSocket, de v12.7.0, ya no aplica desde que el chat vive en su
   > propio servicio `control_pedidos_chat` — sigue siendo cierto que
   > `SECRET_KEY` debe coincidir entre ambos servicios, la sesión se
   > valida con la misma cookie.)

   > ℹ️ **v12.32.21/24 — mismo síntoma ("El job no existe o ha
   > caducado"), causa distinta: memoria, no health check.** El plan
   > **Free de Render son 512 MB de RAM** para todo el proceso. Subir un
   > PDF de SAP demasiado grande (probado: un listado detallado de tres
   > meses, 739 páginas) a "Actualizar departamentos y líneas" o
   > "Importar Albaranes" agota esa memoria — confirmado en el panel de
   > eventos de Render como *"Instance failed: ... Ran out of memory
   > (used over 512MB)"` — y Render reinicia el servicio ENTERO, no solo
   > el job: mientras se recupera, la app deja de responder para TODOS
   > los usuarios, no solo para quien subió el PDF. La v12.32.21 redujo
   > el consumo de memoria de ese lector (`pagina.flush_cache()` en
   > pdfplumber, ya usado en los lectores de Albaranes desde antes), pero
   > no basta por sí sola con un PDF de varios cientos de páginas en un
   > plan de 512 MB. La v12.32.24 añadió un límite duro de 200 páginas
   > (`_LIMITE_PAGINAS_PDF_LISTADO_GRANDE` en `app.py`): un PDF más
   > grande se rechaza al instante con un aviso claro, sin llegar a
   > gastar memoria de verdad. Los listados quincenales que ya recomienda
   > el propio formulario (60-115 páginas) quedan muy por debajo de ese
   > límite y no se ven afectados. Si en el futuro hiciera falta subir
   > tramos más grandes con frecuencia, la opción de fondo es **subir el
   > plan de Render** (más RAM) — subir solo el límite de páginas sin más
   > RAM real detrás volvería a arriesgarse al mismo reinicio para todos.

4. En **Environment → Add Environment Variable**, añade estas variables
   (lista sincronizada con `render.yaml` — si añades una variable nueva
   ahí, añádela también aquí):

   | Variable | Obligatoria | Valor |
   |---|---|---|
   | `DATABASE_URL` | Sí | La URI de Supabase del Paso 1 |
   | `SECRET_KEY` | Sí | Cadena aleatoria larga (Render la genera sola si usas `render.yaml` como Blueprint); cópiala también en `control_pedidos_chat` |
   | `SUPABASE_URL` | Solo si usas Storage (Paso 6) | `https://xxxx.supabase.co` — la URL del **proyecto**, no la de la BD |
   | `SUPABASE_SERVICE_ROLE_KEY` | Solo si usas Storage (Paso 6) | Settings → API → **service_role** (nunca la `anon`/pública) |
   | `SUPABASE_STORAGE_BUCKET` | No | Por defecto `adjuntos-cerrados` si no se define |
   | `DALI_SSO_SECRET` | Solo si integras con DALI | Debe ser idéntica a la del backend de DALI |
   | `DALI_FRONTEND_URL` | No | Por defecto el proxy Cloudflare de DALI ya en producción |

5. Haz clic en **Create Web Service** y espera el primer deploy (~2 min).

6. **Inicializar la base de datos** (solo la primera vez, sobre una BD
   nueva y vacía — nunca sobre una ya en uso):
   En la consola Shell de Render (o en local, con `DATABASE_URL`
   exportada), ejecuta:
   ```bash
   python init_db.py
   ```
   (Ver `README.md` → "Migraciones de base de datos" para el porqué:
   este script solo se corre a mano una vez; los cambios de esquema
   posteriores los aplica `_auto_migrate()` solo, en cada arranque.)

---

## PASO 4 — Migrar datos del SQLite actual — ⚠️ YA NO APLICA

Este paso documentaba la migración **puntual** de SQLite a PostgreSQL de
los inicios del proyecto (antes de v9). `migrate_sqlite_to_pg.py` era un
script de un solo uso para esa migración y **no existe en este
repositorio** (ni falta: la app lleva muchísimas versiones sobre
PostgreSQL/Supabase, sin ningún `pedidos.db` de por medio). Se deja esta
sección solo para que quede constancia de por qué existió, sin instrucciones
que seguir. Para restaurar datos de un backup ya en Postgres, usa
`INSTRUCCIONES_RESTAURACION.md` en su lugar.

---

## PASO 5 — Anti-letargo: workflow de GitHub Actions

> ⚠️ **Corregido:** esta guía recomendaba UptimeRobot. El mecanismo real
> en producción es un workflow de GitHub Actions
> (`.github/workflows/keep-alive-princess.yml`, ya incluido en este
> repositorio) que hace ping a `/ping` cada 10 minutos en horario
> laboral (L-V, 06:00-18:00 hora Canarias, cubriendo verano e invierno
> sin necesidad de tocarlo — ver v12.30.77). No requiere ninguna cuenta
> ni configuración externa: en cuanto el repositorio está en GitHub con
> Actions habilitado (viene activado por defecto), el workflow se
> ejecuta solo. Si prefieres UptimeRobot en su lugar (por ejemplo, para
> cubrir también fines de semana o fuera de horario laboral, cosa que
> el workflow actual no hace a propósito, para no gastar minutos de
> Actions sin necesidad), los pasos originales seguían siendo válidos:
> https://uptimerobot.com, monitor HTTP(s) sobre `/ping`, cada 5-14 min.

El endpoint `/ping` ya está incluido en `app.py` y devuelve `OK 200`.

---

## PASO 6 — Supabase Storage: adjuntos de pedidos cerrados (v12.8.0, ya implementado)

Esto ya **no** es una preparación futura: está construido y en
producción desde v12.8.0. Los adjuntos de pedidos ya cerrados
(`ENTREGADO`/`CANCELADO`) se migran automáticamente de la columna
`pedido_adjuntos.datos` (bytea, la mayor consumidora del tamaño de la
BD) a Supabase Storage, para aligerar la base de datos — la consulta
sigue siendo idéntica desde `/api/adjuntos/<id>`, solo cambia dónde vive
el byte. **No** se usa el paquete `supabase` (no está en
`requirements.txt`): la implementación real llama directamente a la API
REST de Supabase Storage con `requests`, ya en `requirements.txt`. Si
partes de cero:

1. En Supabase → **Storage → New bucket**
   - Nombre: `adjuntos-cerrados` (o el que pongas en
     `SUPABASE_STORAGE_BUCKET`)
   - Public: No (privado)

2. Añade estas variables en Render (ver tabla completa en el Paso 3.4):
   `SUPABASE_URL` (URL del **proyecto**, no de la BD) y
   `SUPABASE_SERVICE_ROLE_KEY` (Settings → API → **service_role**, nunca
   la `anon`/pública — esta clave no debe llegar nunca al navegador).

3. No hace falta tocar el esquema a mano ni escribir código: la lógica
   de subida/lectura ya está en `app.py` y se activa sola en cuanto
   `SUPABASE_URL` y `SUPABASE_SERVICE_ROLE_KEY` están configuradas
   (`STORAGE_CONFIGURADO`). Sin esas dos variables, la app sigue
   funcionando normalmente — los adjuntos simplemente se quedan en la
   BD en vez de migrarse a Storage.

---

## Resumen de costes

| Servicio | Plan | Coste |
|---|---|---|
| Render | Free | 0 € |
| Supabase | Free (500 MB BD, 1 GB Storage) | 0 € |
| EmailJS | Free tier | 0 € |
| GitHub Actions (anti-sleep) | Free (2.000 min/mes privado, ilimitado público) | 0 € |
| **TOTAL** | | **0 €/mes** |

---

## Archivos modificados respecto a la versión original

| Archivo | Cambio |
|---|---|
| `app.py` | SQLite → psycopg2; `?` → `%s`; `datetime('now')` → `NOW()`; email via EmailJS (frontend); endpoint `/ping` |
| `models.py` | `SQL_STATEMENTS` como lista; `AUTOINCREMENT` → `SERIAL`; `LIKE` → `ILIKE` disponible |
| `requirements.txt` | Añadido `psycopg2-binary`, `gunicorn`; eliminado lo innecesario |

> `migrate_sqlite_to_pg.py` — mencionado aquí en versiones antiguas de
> esta tabla, era el script de la migración puntual de los inicios del
> proyecto. No existe en este repositorio (ver Paso 4).
