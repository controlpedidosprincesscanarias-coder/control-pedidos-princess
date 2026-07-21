# v12.10.3 — 21 julio 2026

🔒 Redacción de importe para rol hotel en `/api/pedidos`

Extiende el criterio ya aplicado en el Dashboard (v12.10.2) al resto de
endpoints de pedidos:

- `GET /api/pedidos` (listado): el campo `importe` de cada fila se
  devuelve `null` para el rol `hotel`. De paso corrige un detalle en la
  propia tabla: el tooltip de la insignia "📉 TECHO" mostraba el importe
  real en texto plano al pasar el ratón, aunque el campo estuviera
  oculto en el modal — ahora muestra "sin importe" para ese rol, igual
  que ya hacía cuando el pedido no tenía importe.
- `GET /api/pedidos/<id>` (ficha individual, la que usa el modal de
  edición): mismo tratamiento. Verificado que es seguro: `PUT
  /api/pedidos/<id>` ya ignoraba por completo el campo `importe`
  enviado por un usuario hotel (solo actualiza `entrada_albaran_num` y
  `estado`), así que redactar el importe en la lectura no rompe el
  guardado.

Dos cosas que encontré de paso, relacionadas pero **no corregidas
todavía** porque cambian comportamiento de acceso, no solo de qué
campo se ve — a la espera de que confirmes si quieres que las toque:

1. `GET /api/pedidos/<id>` no comprueba que el pedido pertenezca a un
   hotel asignado al usuario `hotel` (sí lo hace `PUT`, pero no `GET`).
   Un usuario hotel podría ver la ficha completa de un pedido de OTRO
   hotel probando IDs por la URL de la API directamente.
2. `GET /api/exportar` (Excel) no filtra en absoluto por
   `hoteles_ids` — genera el Excel de TODOS los pedidos de TODOS los
   hoteles para cualquier usuario logado, incluido rol hotel.

# v12.10.2 — 21 julio 2026

🔒 Permisos por rol en `/api/dashboard/resumen`

- El bloque `importe` (importe total del mes e importe del mes anterior)
  ahora se devuelve como `null` para el rol `hotel`, en vez de mandarlo
  aunque no se pintara en pantalla. Mismo criterio que ya aplica el resto
  de la app (el campo importe se oculta en el modal de pedido para ese
  rol) — llevado también al nivel de API, no solo de interfaz.
- Revisado el resto del endpoint: pendientes, alertas, actividad de hoy,
  últimos pedidos, hoteles, línea temporal, ranking de proveedores y SLA
  ya estaban correctamente filtrados por `hoteles_ids` para el rol
  hotel, igual que `/api/pedidos` y `/api/stats`. El rol `compras` sigue
  viendo todos los hoteles, coherente con el resto del Dashboard.

# v12.10.1 — 21 julio 2026

🐛 Hotfix — Dashboard se quedaba en "Cargando..." indefinidamente

Al rediseñar las tarjetas superiores en v12.9.0 se eliminó la tarjeta
"Enviados proveedor" (`#st-enviado`) del HTML, pero quedó una línea en
`loadStats()` que seguía intentando escribirle el texto. Al no existir
ya el elemento, `document.getElementById('st-enviado')` devolvía `null`
y el `.textContent = ...` lanzaba un `TypeError` que cortaba en seco la
ejecución de `loadStats()` — justo antes de los gráficos, los accesos
rápidos y la llamada a `loadDashboardResumen()`. Por eso Actividad de
hoy, Línea temporal, Ranking de proveedores, Hoteles y Últimos pedidos
se quedaban permanentemente en "Cargando…".

Corregido: eliminada la referencia a `st-enviado`. Verificado que no
quedan más IDs huérfanos comparando todos los `getElementById(...)`
contra los `id="..."` definidos en la plantilla.

# v12.10.0 — 21 julio 2026

📊 Dashboard Ejecutivo — Nivel 2 (v13, segunda entrega)

Continúa el rediseño del Dashboard iniciado en v12.9.0. Todo sigue
construido sobre `/api/dashboard/resumen`, sin cambios de esquema.

Cambios:
- **Línea temporal**: últimos 15 eventos de `historial_estados`
  (pedido, hotel, estado nuevo, usuario, hora/fecha), con scroll interno.
- **Ranking de proveedores**: pedidos totales, % de cumplimiento y nº de
  "incidencias" (pedidos de ese proveedor actualmente en alerta — no hay
  tabla de reclamaciones real, se aproxima así a propósito, documentado
  en el propio código).
- **SLA de aprobación**: días medios entre que un pedido entra en estado
  de firma/aprobación y sale como "ENVIADO AL PROVEEDOR", calculado
  sobre los últimos 90 días vía `historial_estados` (CTE con `MIN` por
  pedido para evitar contar dos veces si hubo reenvíos). Se muestra como
  badge junto al ranking de proveedores.
- **Widget "Necesita atención"**: banner en la parte superior del
  Dashboard con el pedido con la alerta más crítica (reutiliza el orden
  ya calculado por `_clasificar_alertas` — urgentes primero, luego por
  días), con acceso directo a la ficha. Solo aparece si hay alertas.

Pendiente para más adelante (fuera del Dashboard): tabla real de
reclamaciones/incidencias por proveedor, y comparativa de precios para
el indicador de ahorro — ninguno de los dos existe todavía como
concepto en el modelo de datos.

# v12.9.0 — 20 julio 2026

📊 Dashboard Ejecutivo — Nivel 1 (v13, primera entrega)

Primera tanda del rediseño del Dashboard: todo construido sobre datos que
ya existían en la BD, sin cambios de esquema. Objetivo: que el Dashboard
responda en segundos a "¿qué tengo pendiente hoy?" en vez de solo mostrar
cantidades.

Cambios:
- Nuevo endpoint `GET /api/dashboard/resumen`, **separado** de `/api/stats`
  a propósito — `/api/stats` se usa desde medio programa (badge del
  sidebar, vista Alertas, impresión, tras guardar/eliminar un pedido) y
  cualquier query añadida ahí se paga en todos esos sitios. El nuevo
  endpoint solo se dispara al abrir el Dashboard, con su propia caché de
  30s en el frontend (mismo patrón que `_fetchStats`/`_fetchTecho`).
- Tarjetas superiores "inteligentes": Pedidos (variación % vs mes
  anterior), Entregados (% de cumplimiento), Pendientes (nº activos +
  tiempo medio de espera en días) y Alertas (desglose urgentes/avisos).
- Bloque "Actividad de hoy": entregas y envíos a proveedor registrados
  hoy (vía `historial_estados`), pedidos esperando firma/aprobación,
  alertas urgentes activas.
- Bloque "Accesos rápidos", filtrado por rol (los de `hotel` no ven
  crear pedido/proveedor/importar, igual que ya pasaba en la topbar).
- Tarjetas por hotel: pedidos, % de cumplimiento con semáforo
  🟢/🟡/🔴 (≥95% / ≥85% / resto) y nº de alertas activas — sustituye
  la idea de "mapa de hoteles" de la propuesta.
- Bloque "Últimos pedidos" (6 más recientes) con acceso directo a cada
  ficha.
- Los gráficos "Por estado" y "Por hotel" existentes se mantienen sin
  cambios (siguen alimentados por `/api/stats`).

Pendiente para el Nivel 2 (siguiente entrega): línea temporal de
eventos, ranking de proveedores, SLA de aprobación y widget "Necesita
atención".

# v12.8.6 — 17 julio 2026

🧠 Migración de adjuntos a Storage: pico de memoria acotado

Prevención — no motivado por un OOM real, pero de la misma familia que el
que ya obligó a separar el chat a su propio servicio en la v12.7.0 (ver esa
entrada). El job nocturno de migración (`_job_migrar_adjuntos_storage`)
traía con `fetchall()` el lote entero (hasta 50 adjuntos, hasta
`MAX_ADJUNTO_BYTES` = 20 MB cada uno) antes de empezar a subir el primero.
En el peor caso teórico — varios adjuntos grandes cerrados la misma noche —
eso podía suponer varios cientos de MB retenidos a la vez, por encima de
los 512 MB del plan Free de Render.

Cambios:
- El bucle ahora hace un `SELECT ... LIMIT 1` por adjunto en vez de traer
  el lote completo de golpe: memoria en uso constante (un adjunto a la
  vez) en lugar de proporcional al tamaño del lote.
- Las filas que fallan la subida en la misma ejecución se excluyen (`id !=
  ALL(...)`) de las siguientes vueltas del bucle, para que el `SELECT ...
  LIMIT 1` no las devuelva otra vez y el job no se quede atascado en ellas.
- Sin cambios de comportamiento observables: mismo límite de 50 por
  ejecución, misma marca `storage_path`/`datos=NULL` fila a fila, mismo
  endpoint manual (`POST /api/admin/migrar-adjuntos-storage`) y mismo job
  nocturno de las 03:00. El egress hacia Supabase no cambia — se leen los
  mismos bytes totales, solo repartidos en más consultas pequeñas en vez
  de una grande.

# v12.8.4 — 17 julio 2026

🐛 Fix: `/api/changelog` (125 KB) se pedía duplicado en la misma carga

Detectado en logs de Render: la carga inicial completa de la app (`/api/me`, `/api/maestros`, `/api/stats`... y `/api/changelog`) aparecía repetida dos veces seguidas en cuestión de segundos. `_mostrarModalNuevaVersion()` tiene varios puntos de entrada (chequeo al cargar, polling periódico, `refreshCurrentView()`) que podían solaparse tras un deploy, cada uno pidiendo el changelog por su cuenta.

No se persiguió la causa exacta del doble disparo (podría ser el proxy de Cloudflare Worker, un listener duplicado, etc.) — en su lugar, `_obtenerChangelog()` cachea el resultado en memoria de sesión + comparte la promesa en vuelo entre llamadas simultáneas, así que aunque algo dispare la función dos veces, `/api/changelog` solo se pide una vez de verdad. Es correcto de todas formas: el contenido no cambia dentro de una misma sesión (solo cambia con un deploy nuevo, momento en el que la página se recarga entera).

# v12.8.2 — 17 julio 2026

🗜️ Compactación automática (VACUUM FULL) tras migrar adjuntos a Storage

Poner `datos=NULL` al migrar un adjunto libera el espacio lógicamente, pero Postgres no encoge el archivo físico en disco por sí solo — sin este cambio, el tamaño reportado de `pedido_adjuntos` no bajaría nunca aunque el conteo de "migrados" fuera subiendo cada noche.

Cambios:
- Nueva tabla `db_vacuum_log` (fecha, mb_antes, mb_después, mb_liberados).
- Nueva función `_vacuum_full_adjuntos()` — conexión propia con autocommit (VACUUM FULL no puede ir dentro de una transacción normal), mide tamaño antes/después, registra el resultado.
- El job nocturno de migración (03:00) encadena la compactación **solo si esa noche se migró al menos un adjunto** — evita bloquear la tabla sin motivo las noches en que no hay nada nuevo que compactar.
- El botón manual "Migrar lote ahora" (Admin → Integridad) **no** compacta — solo migra. VACUUM FULL toma un lock exclusivo sobre la tabla, y ese botón puede pulsarse en horario de oficina con gente usando la app; la compactación se reserva para la ventana de madrugada.
- Admin → Integridad → Tamaño de BD: nueva línea con la fecha y MB liberados de la última compactación.

# v12.8.0 — 16 julio 2026

📦 Adjuntos de pedidos cerrados migrados a Supabase Storage

`pedido_adjuntos.datos` es, con diferencia, la mayor consumidora del tamaño de base de datos (277 MB de ~306 MB totales — los archivos se guardan como `bytea`, en TOAST). Los adjuntos de pedidos ya cerrados (`ENTREGADO`/`CANCELADO`) no vuelven a escribirse nunca, así que se migran a Supabase Storage: siguen siendo consultables exactamente igual desde `/api/adjuntos/<id>`, solo cambia dónde vive el byte.

**Importante — esto reduce tamaño de BD, no egress.** Storage tiene su propia cuota (separada, 1 GB en el plan Free), pero cada descarga desde Storage sigue contando como egress igual que antes contaba el `SELECT` de la columna `datos`.

Cambios:
- Esquema: `pedido_adjuntos.storage_path` (nueva, TEXT), `datos` deja de ser `NOT NULL` (se pone a `NULL` tras migrar, liberando el TOAST). `datos_thumb` **no se toca** — las miniaturas se quedan siempre en Postgres, pequeñas, para que la vista previa siga siendo instantánea aunque el original esté en Storage.
- Nuevos helpers de Storage (`_storage_subir`, `_storage_descargar`, `_storage_borrar`, `_storage_asegurar_bucket`) — llamadas directas a la API REST de Storage con la `service_role` key (bypassa RLS; el control de acceso lo sigue haciendo esta app con `@login_required`, igual que ahora). Bucket privado, creado automáticamente al arrancar si no existe.
- Nuevo job diario `_job_migrar_adjuntos_storage`, a las 03:00 — migra por lotes de 50 los adjuntos de pedidos cerrados que aún viven en la BD. Cada fila se marca migrada inmediatamente tras subirse, así que un job interrumpido a mitad retoma donde lo dejó al día siguiente, sin repetir trabajo.
- `download_adjunto()` y el backfill de miniaturas en `download_adjunto_thumb()` ahora comprueban `storage_path`: si está migrado, sirven desde Storage; si no, desde `datos` como siempre. El fix de ETag-antes-de-traer-el-archivo (v12.3.5) se mantiene intacto en ambos casos.
- `delete_adjunto()` borra también el objeto en Storage cuando aplica.
- Admin → Integridad → Tamaño de BD: nuevo bloque con el progreso (migrados / pendientes) y botón **"Migrar lote ahora"** para lanzar un lote manualmente sin esperar a las 03:00.
- Nuevo endpoint `POST /api/admin/migrar-adjuntos-storage`.
- Nueva dependencia: `requests` (llamadas HTTP a la API de Storage).

**Requiere configuración antes de desplegar** — dos variables de entorno nuevas en Render:
- `SUPABASE_URL`: la URL del proyecto (`https://xxxx.supabase.co`), **no** la de conexión a la base de datos.
- `SUPABASE_SERVICE_ROLE_KEY`: Supabase → Settings → API → `service_role` (⚠️ nunca la `anon`/`public` — esta clave bypassa todos los permisos, debe quedarse solo en el servidor).

Sin estas dos variables, la app funciona exactamente igual que antes (los adjuntos se siguen guardando en la BD, sin error ni degradación) — la migración simplemente se queda desactivada, con un aviso visible en Admin → Integridad.

# v12.7.0 — 16 julio 2026

🔀 El chat interno sale de este servicio (aislamiento de memoria tras OOM)

Los logs de Render mostraron un `SIGKILL` por falta de memoria en el
proceso único (`gunicorn -k eventlet -w 1`) que alojaba a la vez pedidos,
alertas, scheduler y el chat con sus websockets. Se mueve el chat a un
servicio de Render independiente (`control_pedidos_chat`), para que un
pico de memoria en uno no tumbe al otro.

Cambios en este servicio:
- Quitadas todas las rutas `/api/chat/*`, los handlers de `socketio.on(...)`,
  la instancia `SocketIO`, el pool `_chat_pool`/`get_chat_db()`/
  `query_chat()`/`execute_chat()` y `CHAT_DATABASE_URL`. Cero cambio de
  comportamiento de pedidos/alertas — solo se retira código que ya no vive
  aquí (ver paquete `control_pedidos_chat_v1_0_0`).
- `requirements.txt`: quitados `flask-socketio` y `eventlet` (ya no se usan).
- Start Command en Render: vuelve a gunicorn estándar (`gunicorn -w 2
  app:app`), sin `-k eventlet -w 1` — puede volver a usar varios workers.
- `SECRET_KEY` sigue siendo obligatoria y debe coincidir exactamente con la
  del nuevo servicio de chat: es la que firma la cookie de sesión que ambos
  servicios comparten para no duplicar el login.

# v12.6.4 — 16 julio 2026

📮 Alerta combinada egress + tamaño BD, umbral bajado a 50%, movida a las 08:30

Hasta ahora había una sola alerta (solo egress, umbral 80%, a las 08:00). Se combina con tamaño de BD en un único mensaje/popup, para no duplicar avisos sobre la misma cuota de Supabase.

Cambios:
- `EGRESS_UMBRAL_AVISO_PCT`: 80% → **50%**.
- Nuevo `DB_SIZE_UMBRAL_AVISO_PCT = 50%` (sobre `DB_SIZE_LIMITE_MB = 512`, el límite del plan Free).
- `_job_alerta_egress` → renombrado `_job_alerta_consumo`: comprueba ambas métricas y envía **un único** Telegram + popup bridge si cualquiera de las dos supera su umbral (egress con `⚠️` si supera, BD con `⚠️` si supera, ambas cifras siempre visibles en el mensaje para dar contexto).
- Horario: **08:30** (antes 08:00) — 20 min después del snapshot diario de tamaño de BD (08:10, sin cambios, sigue siendo independiente para el histórico de tendencia).
- Egress sigue siendo el acumulado por día desde `egress_tracking` (con el mismo desfase de "hasta ayer" ya documentado); tamaño de BD se consulta en vivo en el momento del job, no depende del snapshot de las 08:10.
- Dedup diario movido de `tipo='egress_alerta'` a `tipo='consumo_alerta'` en `whatsapp_log`.
- El evento en Config Avisos (antes "Consumo de egress (Supabase) elevado") se renombra a "Consumo Supabase elevado (egress / tamaño BD)" — mismo `codigo` (`egress_alerta`), mismos destinatarios ya configurados, sin que el admin tenga que volver a marcar nada.
- Endpoint `/api/admin/test-egress` y su botón en Integridad ("📶 Probar alerta consumo (egress + BD)") sin cambiar de ruta/nombre de función, por compatibilidad — ahora disparan la alerta combinada.

# v12.6.2 — 16 julio 2026

🗄️ Seguimiento de tamaño de base de datos (Admin → Integridad)

A diferencia del egress, el tamaño de la base de datos solo crece — no hay ningún mecanismo de caché que lo compense. Tras confirmar que `pedido_adjuntos` es, con diferencia, la mayor consumidora (277 MB de 306 MB totales — los archivos se guardan como `bytea`, en TOAST), se añade visibilidad sobre la tendencia sin depender de entrar al dashboard de Supabase.

Cambios:
- Nueva tabla `db_size_tracking` (fecha, bytes_total, bytes_adjuntos).
- Nuevo job diario `_job_db_size_tracking`, a las 08:10 hora Canarias (justo después de la alerta de egress) — snapshot vía `pg_database_size()` y `pg_total_relation_size('pedido_adjuntos')`.
- Nuevo endpoint `GET /api/admin/db-size` — historial de los últimos 30 días + valor en vivo calculado al vuelo (para tener dato desde el primer momento, sin esperar al primer job de las 08:10).
- Nueva tarjeta en Admin → Integridad, debajo de los bloques de problemas: total actual (con % sobre los 512 MB del plan Free), tamaño de `pedido_adjuntos` en concreto, y tabla de los últimos 30 días.

Puramente informativo por ahora — sin alerta automática por Telegram/bridge todavía (a diferencia de egress). Si el seguimiento confirma que hace falta, el siguiente paso natural es purgar adjuntos antiguos o migrarlos a Supabase Storage.

# v12.6.0 — 15 julio 2026

💬 Chat interno entre usuarios (privado 1 a 1 + canal general), en tiempo real,
con Supabase separada

Hasta ahora no había forma de que los compañeros que comparten la app
(compradores, hoteles, admins) se comunicasen entre ellos sin salir a
WhatsApp o email. Se añade un chat que reutiliza el mismo usuario/contraseña
de Control de Pedidos — no hay alta ni login nuevo.

Cambios:
- Nuevas tablas `chat_canales`, `chat_participantes`, `chat_mensajes` y
  `chat_lecturas` (esta última solo para el contador de no leídos), en una
  Supabase **separada** de la de pedidos (nueva variable opcional
  `CHAT_DATABASE_URL`) para no competir por su cuota de egress/almacenamiento,
  que ya iba saturada. Si no se configura, cae a `DATABASE_URL` de siempre.
  Las tablas de chat nunca han tenido `FOREIGN KEY` hacia `usuarios` ni
  ninguna tabla de pedidos, así que el cambio no toca el esquema existente.
- Canal `general` fijo, visible para todos los usuarios activos, más canales
  privados 1 a 1 creados bajo demanda (id determinista `dm:usuarioA:usuarioB`,
  ordenado alfabéticamente, para no duplicar conversación).
- Entrega en tiempo real vía **Flask-SocketIO**: eventos `connect`,
  `unirse_canal`, `enviar_mensaje` → `nuevo_mensaje`. Reutiliza la sesión de
  Flask ya existente (`manage_session=True`), sin autenticación paralela.
- Endpoints REST equivalentes (`GET/POST /api/chat/mensajes`,
  `GET /api/chat/canales`, `GET /api/chat/usuarios`) para que cualquier
  cliente que aún no hable socket.io (o si el WebSocket no llega a
  establecerse) siga funcionando por polling, sin perder mensajes.
- **Requiere cambiar el Start Command en Render** a
  `gunicorn -k eventlet -w 1 app:app` — ver GUIA_DESPLIEGUE.md. Sin este
  cambio el chat sigue funcionando (long-polling), pero sin entrega instantánea.
- Pendiente: interfaz de chat en el frontend web (`templates/index.html`).
  Este release deja lista toda la base de datos y la API; el cliente de
  escritorio (Organizador Princess v4.8.0) ya lo incorpora.

# v12.5.0 — 15 julio 2026

📮 Reenvío a admins configurable en techo urgente y familia repetida

Cambios:
- 2 claves nuevas en `config_alertas`, nuevo grupo en Admin → Config Alertas: "📮 Reenvío a Admins (Techo / Familia repetida)":
  - `techo_urgente_admin_reenvio_dias` (default 2)
  - `familia_repetida_admin_reenvio_dias` (default 2)
- 2 números mágicos corregidos — antes `< 2` hardcodeado en el código, ahora leen `get_config()`:
  - Job de techo urgente a admins (reenvío cada N días)
  - Job de familia/partida repetida a admins (reenvío cada N días)

Bug de etiquetado corregido: las notificaciones push de "familia/partida repetida" (tanto a comprador como a admin) se encolaban con `tipo="techo"` en `bridge_notificaciones`, mezclándose con las de techo de gastos real. Ahora usan `tipo="familia_repetida"`, un tipo propio. Inocuo para lo ya desplegado (main_agenda no filtra por `tipo`, solo lo muestra/loguea), pero deja el dato limpio por si en el futuro se quiere tratar distinto.

Lo que se deja tal cual, con su motivo:
- `cambio_estado`, `solicitud_acceso`, "techo nuevo pedido" → eventos puntuales, no recordatorios; no tiene sentido regular su repetición.
- `alerta_auto` (Telegram/push de pedidos en alerta) → ya era configurable en días vía las claves `<estado>_ciclo` + `dias_critico`, ya existentes en Admin.
- `egress`, `health` → alertas de infraestructura para admin, cadencia diaria intencionada por diseño del job, no de negocio de pedidos.

# v12.4.6 — 15 julio 2026

🔁 Repetición de popups configurable por tipo y nivel de alerta

Hasta ahora la frecuencia con la que un popup de Agenda se repetía para un pedido en alerta (🔴 urgente / 🟡 aviso) estaba fija en el código de main_agenda (`INTERVALO_POPUP_URGENTE`/`NORMAL`), igual para todos los tipos de alerta. Ahora es configurable por tipo desde Admin → Config Alertas.

Cambios (`control_pedidos` — `app.py` + `templates/index.html`):
- 15 claves nuevas en `config_alertas`, grupo "🔁 Repetición de Popups en Agenda" — 3 por cada uno de los 5 tipos (Enviado al proveedor, Firma Compras, Firma Hotel, Entrega Parcial, Cotización): `<tipo>_popup_repetir` (on/off), `<tipo>_popup_horas_critico`, `<tipo>_popup_horas_normal`.
- El panel de Config Alertas ya renderiza cualquier clave/grupo de forma genérica, así que solo hizo falta añadir el label del grupo y la unidad ("horas") en `index.html` — el formulario en sí no cambió.
- `_clasificar_alertas()` añade estos 3 campos a cada alerta antes de devolverla en `/api/bridge/alertas`, para que main_agenda sepa cómo repetir cada una.

Bug corregido de paso: `_clasificar_alertas()` usaba un diccionario de umbrales fijo en código (`_UMBRALES_ALERTAS`) en vez de `_build_umbrales()` — la función que sí lee de Admin y que ya usaba el resto de la app. Esto significaba que cambiar los días de "Enviado al proveedor — Urgente" en Admin no afectaba a los popups de Agenda, solo al email/Telegram del job diario. Ahora los tres canales (popup, email, Telegram) leen del mismo sitio.

Cambios en `main_agenda` (`pedidos_agenda_bridge.py`), publicados como v4.7.0 / bridge v4.7:
- `_debe_mostrar_popup()` y `_aviso_para_popup()` leen `popup_repetir`/`popup_horas_critico`/`popup_horas_normal` de cada alerta recibida, en vez de las constantes fijas de antes (que quedan como fallback si el servidor no manda esos campos — compatibilidad con versiones anteriores de `control_pedidos`).
- Si `popup_repetir=False`, el popup se muestra una única vez por pedido.
- Bug corregido: el reseteo del temporizador al escalar de "aviso" a "urgente" comparaba contra un nivel `"normal"` que nunca existe (debía ser `"aviso"`), así que nunca se disparaba — el popup podía tardar mucho más de lo esperado en repetirse tras un cambio de nivel.

Requiere main_agenda/bridge ≥ v4.7.0 para aprovechar la repetición configurable — con una versión anterior del bridge, sigue funcionando con los intervalos fijos de siempre (fallback de compatibilidad, sin romper nada).

# v12.4.4 — 15 julio 2026

🐛 Fix: aviso falso "agente sin sincronizar" en Restaurar Backup

`ultimo_escaneo` se calculaba como `MAX(actualizado_en)` de `backups_cache` — pero esa columna solo se toca cuando un backup cambia de verdad (fix de egress anterior). Como normalmente solo hay un backup nuevo al día (17:00), el panel podía avisar de "agente sin sincronizar hace 60+ minutos" aunque `restore_agent.py` estuviera corriendo perfectamente cada 5 minutos sin encontrar nada nuevo que subir.

`/api/admin/backup/listar` ahora lee de una tabla nueva, `agente_heartbeat`, que `restore_agent.py` actualiza en cada ciclo — haya cambios o no. Si el agente todavía no está actualizado (tabla o fila inexistente), cae de vuelta al cálculo antiguo como red de seguridad, así que no rompe nada para quien no haya desplegado el `restore_agent.py` nuevo todavía.

Requiere desplegar también la versión de `restore_agent.py` con el heartbeat (ver `ComprasPrincess_Backup`) — si solo se actualiza `app.py`, el aviso seguirá comportándose como antes (fallback automático, no falla, pero tampoco se arregla).

# v12.4.2 — 15 julio 2026 (hotfix)

🐛 Fix: `_job_alertas_diarias` rota desde el deploy de v12.4.0

v12.4.0 (Configuración de Avisos) se ramificó desde v12.3.6, antes del hotfix v12.3.8, así que traía de vuelta el mismo `NameError: name '_job_alertas_diarias_inner' is not defined` que ya se había corregido una vez (ver v12.3.8 más abajo). Se revisaron también los otros 5 jobs en segundo plano (familia repetida, techo urgente, techo mensual, alerta de egress, health check) y estaban bien — el problema era exclusivo de `_job_alertas_diarias`.

Corregido: se restaura la línea `def _job_alertas_diarias_inner():` en su sitio.

# v12.4.0 — 15 julio 2026

🔔 Configuración de Avisos: destinatarios de Telegram/email configurables por evento, sin tocar código

Hasta ahora, quién recibía cada tipo de alerta de sistema (cambios de estado urgentes, techo de gastos superado, familias repetidas, egress, integridad, solicitudes de acceso...) estaba hardcodeado: `TIPOS_SUPERVISION_ADMIN = {"urgente"}` decidía qué tipos se replicaban a admins, y "todos los admins con `telegram_chat_id`" (o "todos los admins con email") recibían indiscriminadamente cualquier evento de ese tipo. Añadir o quitar un destinatario, o decidir que un evento concreto solo interese a una persona, requería tocar `app.py`.

Cambios:
- Nuevas tablas `eventos_aviso` (catálogo de 8 causas: cambio de estado urgente, pedido crítico parado, techo superado, nuevo pedido sujeto a techo, familias repetidas, egress, integridad, solicitud de acceso) y `config_avisos` (qué usuario recibe qué evento, por qué canal — Telegram y/o email).
- Nueva sección **Administrador → Configuración de Avisos**: matriz eventos × usuarios con checkbox de Telegram/email por celda. Si nadie está marcado para un evento, no se envía nada — ya no hay un fallback "todos los admins".
- `TIPOS_SUPERVISION_ADMIN`, `_get_admins_telegram()`, `_get_admin_emails()` y `_get_solo_admin_emails()` (esta última mantenida como alias de compatibilidad hacia el evento `solicitud_acceso`) quedan sustituidas por `_destinatarios_evento(evento_codigo, canal)` y el dispatcher único `_notificar_evento(...)`.
- Nuevo endpoint `GET /api/config-avisos/resolver?evento=...&canal=...` para que main_agenda (vía el bridge) o cualquier otro módulo consulte esta configuración en tiempo real, sin pasar por el panel de admin.
- El canal email para avisos de sistema (egress, integridad, techo, familias) no tenía SMTP propio en el backend — solo existía el envío vía EmailJS en el navegador. Se añade una cola (`emails_sistema_pendientes`) que el primer admin con sesión abierta envía en segundo plano cada 5 minutos; a diferencia de Telegram, este canal no es instantáneo si no hay ningún admin con la app abierta.

# v12.3.8 — 15 julio 2026 (hotfix)

🐛 Fix: `_job_alertas_diarias` rota desde el deploy de v12.3.6

Al añadir `_flush_egress_bytes()` tras `_job_alertas_diarias_inner()` en v12.3.6 se borró por error la línea `def _job_alertas_diarias_inner():`, fusionando el cuerpo de esa función dentro de `_job_alertas_diarias()`. Resultado: el job (corre cada minuto, 07:00-15:59h) fallaba cada vez con `NameError: name '_job_alertas_diarias_inner' is not defined` — ninguna alerta diaria por Telegram a compradores se envió desde el deploy hasta este hotfix. Los otros 5 jobs tocados en el mismo cambio (familia repetida, techo urgente, techo mensual, alerta de egress, health check) se revisaron y estaban bien.

Corregido: se restaura la línea `def _job_alertas_diarias_inner():` en su sitio.

# v12.3.6 — 14 julio 2026

📊 Egress: estimación más fiel + aviso automático movido a las 08:00

Hasta ahora `egress_tracking` (y por tanto el aviso automático de Telegram/bridge) solo contaba los bytes que Flask reenvía al navegador. Eso subestimaba mucho el egress real que factura Supabase: por ejemplo, un adjunto ya cacheado en el navegador responde 304 (0 bytes hacia el usuario), pero la fila con el archivo completo se seguía leyendo de Postgres para comparar el ETag — tráfico real, invisible para nuestra propia cifra.

Cambios:
- `query()` (punto único por el que pasan todos los `SELECT` de la app) ahora estima el tamaño de cada fila leída y lo acumula en el contexto de la petición o job en curso (`_track_db_bytes`, `_tam_fila`, `_tam_valor`).
- `_track_egress()` (hook `after_request`) suma esos bytes de lectura de Postgres a los bytes de respuesta HTTP antes de guardar el total del día.
- Los 6 jobs en segundo plano (alertas diarias, familia repetida, techo urgente admins, techo mensual, alerta de egress, health check) llaman a `_flush_egress_bytes()` al terminar, para que sus propias lecturas de Postgres —que no pasan por `_track_egress`, al no haber respuesta HTTP— también queden registradas.
- `_job_alerta_egress` (aviso por Telegram + popup bridge si se acerca/supera el umbral del plan Free) pasa de ejecutarse a las 20:30 a las **08:00 hora Canaria**, al principio de la jornada de oficina. Nota: esto reintroduce el desfase que la versión anterior evitaba deliberadamente — un cruce del umbral a media tarde no se avisará hasta la mañana siguiente.

Sigue sin cubrir Auth, Storage, Realtime ni Log Drains (esta app no usa Supabase Storage; todo se guarda como `bytea` en Postgres), pero para el patrón de uso real de esta app la cifra ahora debería acercarse mucho más al contador oficial de Supabase que antes.

# v12.3.5 — 14 julio 2026

📉 Fix: `/api/adjuntos/<id>` seguía descargando el adjunto completo desde Supabase aunque el navegador ya lo tuviera en caché (304)

El fix anterior de egress (v12.x, cabeceras `Cache-Control`/`ETag`) evitaba que el navegador volviera a *pedir* el archivo, pero la consulta SQL que trae la columna `datos` (el adjunto completo, hasta 2MB) seguía ejecutándose ANTES de comprobar el `If-None-Match`. Resultado: cada apertura de un pedido con adjuntos, aunque terminara en un 304 sin cuerpo hacia el navegador, ya había hecho que la app descargara el archivo entero desde Postgres — egress de base de datos invisible tanto para el usuario como para el contador interno `egress_tracking` (que solo mide bytes de respuesta HTTP salientes, no el tráfico Postgres↔app).

Cambio:
- `download_adjunto()`: el `ETag` se comprueba primero con una consulta ligera (`SELECT id`, sin `datos`); solo si hace falta servir el contenido real se ejecuta la consulta completa.

# v12.3.4 — 14 julio 2026

🔔 Fix: popups de Integridad y Egress no llegaban a main_agenda (solo Telegram)

Los avisos de "ALERTA DE CONFIGURACIÓN — Integridad" (job diario 07:05 + botón "Probar" del panel admin) y "Egress Supabase" (job diario 20:30 + botón "Probar" del panel admin) son exclusivos de administrador: nunca tuvieron contrapartida de comprador, así que —a diferencia del resto de notificaciones de la app— nunca pasaron por la auditoría de paridad Telegram↔bridge de v12.2.x. Solo llamaban a `_send_telegram()`, sin encolar nunca una fila en `bridge_notificaciones`; el resultado era que llegaban perfectamente al Telegram del admin pero jamás disparaban un popup en main_agenda, ya fuera por el job automático o por los botones "Probar" (`/api/admin/test-health`, `/api/admin/test-egress`) del panel de administración — ambos ejecutan la misma función interna, así que el fallo era idéntico en ambos casos.

Cambios:
- `_job_health_check_inner()`: cada envío de Telegram a un admin ahora encola también una notificación en `bridge_notificaciones` (tipo `integridad`, nivel `urgente` si hay problemas reales, `aviso` para la confirmación "todo OK" del botón "Probar").
- `_job_alerta_egress_inner()`: mismo tratamiento (tipo `egress`, nivel `urgente` si el ciclo ya superó el 100%, `aviso` si solo se acerca al umbral).
- `pedidos_agenda_bridge.py` no necesitó ningún cambio: `/api/bridge/notificaciones` ya procesa cualquier tipo de notificación de forma genérica — el problema era exclusivamente que estas dos rutas nunca llegaban a encolar nada.

# v12.3.2 — 14 julio 2026

⚡ Solicitud de acceso: Fase 2 automática, sin intervención del admin

Hasta ahora el flujo de alta de usuario requería que un admin recibiera el email de Fase 1 y pulsase manualmente "Enviar Fase 2" para que el usuario recibiera el enlace/.bat de verificación. Ahora, en cuanto el usuario envía el formulario de Fase 1, el backend genera el token de verificación y dispara automáticamente el email de Fase 2 al propio usuario — el admin ya no tiene que hacer nada en este paso.

Cambios:
- `/api/solicitar-usuario` (Fase 1) genera el token, guarda la solicitud directamente en estado `fase2_pendiente` y devuelve, junto al aviso informativo para los admins, el email de Fase 2 listo para que el frontend lo envíe al usuario vía EmailJS en el mismo golpe.
- El aviso a los admins (Telegram + email) pasa a ser puramente informativo: ya no incluye ninguna acción pendiente.
- `/api/admin/solicitudes-acceso/<id>/enviar-fase2` y `/generar-bat` se conservan como reenvío/regeneración manual (p.ej. si el email automático falla o el enlace caduca) — el botón del panel de admin pasa a llamarse "🔁 Reenviar Fase 2". `generar-bat` reutiliza el token vigente en vez de invalidarlo si ya se envió uno válido.
- Se extrajo la construcción del email de Fase 2 a `_construir_email_fase2()`, reutilizada tanto en el envío automático como en el reenvío manual.

El resto del flujo no cambia: el usuario recibe el email, ejecuta el .bat (o el enlace), completa la Fase 2, y el admin aprueba y crea la cuenta como hasta ahora.

# v12.3.0 — 14 julio 2026

🔐 Fix: código de verificación por email invalidado antes de poder usarse

Tras varios días sin acceder, algunos usuarios reportaban que el primer código de verificación recibido por email nunca funcionaba ("código incorrecto o caducado"), viéndose obligados siempre a pulsar "Reenviar código" para completar el login. El email llegaba correctamente y a tiempo — el problema no era el envío.

Causa: el botón "Acceder" no se deshabilitaba mientras la petición de login estaba en curso (p.ej. mientras Render despertaba tras estar dormido varios días), así que un doble clic o un Enter mantenido podía disparar una segunda llamada a /api/login. Cada llamada invalida por diseño cualquier código anterior sin usar antes de generar uno nuevo — con lo que el primer código, aunque el email llegara perfectamente, quedaba invalidado por la segunda petición antes de que el usuario llegara a introducirlo. El mensaje de error era idéntico tanto si el código realmente había caducado por tiempo como si había sido superado por uno más nuevo, lo que ocultaba la causa real.

Novedades

Bloqueo de doble-submit en el login: mientras hay una petición a /api/login en curso, el botón "Acceder" queda deshabilitado y no se admite un segundo envío, evitando que se generen dos códigos para un mismo intento.
Mensajes de error diferenciados en /api/login/verificar-codigo: ahora distingue entre código incorrecto, código superado por uno más reciente (probable doble solicitud de login) y código realmente caducado por tiempo — cada caso queda además registrado en el log del servidor con el id y timestamps de la fila implicada.
Endurecido el cálculo de expira_en: se usa datetime.now(timezone.utc) en vez de datetime.utcnow() (naive) al insertarlo en la columna TIMESTAMPTZ, para no depender de que la sesión de Postgres tenga el timezone en UTC por defecto — la ventana de 10 minutos es demasiado ajustada como para arriesgarse a un desfase de interpretación.
Envío del email de verificación (EmailJS) con un reintento automático y aviso visible en pantalla si aun así falla, en vez de fallar en silencio como antes.

# v12.2.8 — 13 julio 2026

📉 Reducción de egress — caché de index.html + logos como ficheros estáticos

Tras el fix de adjuntos/miniaturas de v12.2.0, index.html seguía siendo el mayor origen de egress: se servía sin ninguna cabecera de caché, así que cada apertura de la app o refresco de pestaña descargaba el archivo entero (570 KB), de los cuales 151 KB eran dos logos incrustados en base64.

Novedades

`/` ahora responde con ETag (el mismo hash MD5 que ya usaba /api/version) y Cache-Control: no-cache — el navegador revalida con una petición condicional ligera y solo descarga el archivo completo si de verdad cambió tras un despliegue.
Los dos logos (login y sidebar) se extrajeron de base64 a ficheros reales en /static/ (logo-login.jpg, logo-sidebar.png), reduciendo index.html de 570 KB a 419 KB.
Nueva cabecera Cache-Control (7 días) en la ruta /static/<filename>, que antes no tenía ninguna.
Nota: uno de los dos logos estaba etiquetado como image/png en el data URI original pero sus bytes reales eran JPEG — se corrigió la extensión/mime al extraerlo (logo-login.jpg).

# v12.2.6 — 13 julio 2026

🔔 Paridad Telegram ↔ popups de main_agenda + login dedicado para el bridge

Auditoría completa de los 12 puntos donde la app envía Telegram, para garantizar que main_agenda recibe el mismo aviso como popup, solo para el usuario correspondiente según su rol y sus pedidos.

Novedades

Corregido: los avisos rutinarios a compradores (nivel "aviso") ya no se replicaban también en la Agenda de todos los admins — ahora los admins solo reciben popup para solicitudes de acceso y eventos marcados como urgentes, igual que en el resto de la app.
Nueva ruta /api/bridge/login: login dedicado para cuentas de servicio (como el bridge de main_agenda) que se salta el paso de verificación por email tras varios días de inactividad — imprescindible porque ese proceso corre desatendido y nunca podría introducir el código. Las credenciales validadas son las mismas de siempre.
Confirmado tras la auditoría: el resto de los 10 puntos que envían Telegram ya encolaban correctamente el popup equivalente para el destinatario exacto (comprador, hotel o admin, según corresponda).

# v12.2.5 — 10 julio 2026

🔐 Seguridad de sesión: caducidad diaria + verificación por email

Los usuarios suelen dejar la aplicación abierta todo el día en el ordenador de la oficina, así que la sesión nunca llegaba a expirar de forma natural.

Novedades

La sesión ahora caduca automáticamente al cambiar de día (hora Canarias): la primera acción del día siguiente pide contraseña de nuevo, aunque la pestaña llevara abierta desde el día anterior.
Si han pasado 3 días o más desde el último login de una cuenta, además de la contraseña se exige un código de 6 dígitos enviado al email registrado del usuario, válido 10 minutos. El uso diario normal no se ve afectado por este paso adicional.
Nueva tabla login_verification_codes y columna usuarios.ultimo_login.
Si un usuario no tiene email registrado, este paso se omite automáticamente para no bloquearlo.

# v12.2.4 — 10 julio 2026 (actualizado)

Resumen de este último cambio:

Bug encontrado: dos temporizadores de comprobación de versión corriendo en paralelo desde que se abre la app (uno cada 30s durante 15 min, otro cada 60s desde el principio) — coincidían cada minuto y duplicaban la llamada a /api/version. El impacto en bytes es pequeño (27 bytes por llamada), pero es una duplicación real de tráfico innecesaria, y con varios ordenadores de oficina abiertos a la vez, suma.
Arreglado: el temporizador de 60s ahora solo arranca cuando termina la fase rápida de 15 minutos — nunca hay dos activos simultáneamente.

📶 Añadida alerta automática de egress por Telegram

Complementa el fix de reducción de egress de esta misma versión: ahora la app estima a diario cuánto egress lleva consumido en el ciclo de facturación actual de Supabase y avisa a los admins por Telegram si se acerca o supera el límite del plan Free.

Novedades

Nueva tabla egress_tracking: acumula por día los bytes de cada respuesta que sirve la app (hook interno, sin coste extra).
Job diario a las 08:15 (hora Canarias): si el acumulado del ciclo actual (desde el día 23) supera el 80% del límite, envía Telegram a los admins con el % consumido. Aviso único al día.
Nuevo botón "📶 Probar alerta egress" en el panel de Integridad, para forzar el aviso manualmente y confirmar que el canal funciona.
Nota: es una estimación interna basada en lo que sirve la app, no el contador exacto de Supabase — para el dato oficial, revisar Supabase → Organization → Usage.

# v12.2.0 — 8 julio 2026

📉 Reducción de egress — caché de adjuntos + miniaturas de imágenes

El proyecto de Supabase venía superando el límite mensual de egress del plan Free (5 GB), con restricciones activas en el dashboard. Investigando el consumo, se detectó que los adjuntos (PDF, imágenes, correos) se re-descargaban enteros cada vez que se abría un pedido, sin ningún tipo de caché.

Novedades

Los adjuntos ahora se sirven con cabecera Cache-Control de larga duración (son inmutables: nunca se editan, solo se suben nuevos o se borran), con soporte de ETag/304 como respaldo.
Las imágenes de artículo (imagen_articulo) ya no se muestran a tamaño completo como miniatura: se genera una versión reducida (240px, JPEG) en el momento de subida y se sirve por una nueva ruta /api/adjuntos/<id>/thumb.
Las imágenes subidas antes de este cambio generan su miniatura la primera vez que se piden (de forma transparente) y queda guardada para siempre — no requiere ninguna migración manual de datos.
Al hacer clic en la miniatura se sigue abriendo la imagen original a tamaño completo, sin cambios para el usuario.
Requiere añadir la dependencia Pillow (ya incluida en requirements.txt).

# v12.1.8 — 26 junio 2026

🏨 El usuario Hotel ya puede ver el panel de Alertas (solo de sus hoteles)

Hasta ahora la sección "Alertas" del menú estaba bloqueada para el rol Hotel, aunque el dashboard ya le mostraba el contador de avisos pendientes.

Novedades

El menú "Alertas" aparece ahora también para el rol Hotel.
La tabla muestra únicamente las alertas de seguimiento de los hoteles que tiene asignados ese usuario (igual que ya ocurre en Pedidos y en el Dashboard).
Sigue sin tener acceso a "Techo de gastos", que continúa reservado a Administrador y Compras.
El botón "✉ Notificar / 🔁 Re-notificar" no se muestra para este rol, ya que el envío de avisos a proveedor/compras sigue siendo una acción exclusiva de Administrador y Compras; el botón "✏ Editar" se mantiene con las mismas restricciones de edición que ya tenía el rol Hotel en Pedidos.

🗑️ Botón de borrado en Solicitudes de acceso (Admin)

El listado de "Solicitudes de acceso" (dentro de Gestión de usuarios) ya permite eliminar una solicitud del histórico, igual que ya se podía hacer con los usuarios en la tabla de arriba.

Novedades

Nuevo botón 🗑 en cada fila de Solicitudes de acceso, sea cual sea su estado (pendiente, aprobada, rechazada).
Pensado para limpiar el histórico de solicitudes ya tramitadas o duplicadas/erróneas (por ejemplo, la solicitud #7 rechazada del ejemplo de Pepe Martín).
Pide confirmación antes de borrar, igual que el resto de acciones destructivas de la plataforma.
Si la solicitud ya estaba aprobada, borrarla del histórico no afecta a la cuenta de usuario que ya se creó: solo desaparece el registro de la solicitud.

# v12.1.6 — 23 junio 2026

🔍 Filtros en el panel de Alertas de seguimiento

Hasta ahora, el panel de Alertas mostraba siempre el listado completo, sin poder acotarlo como sí se podía en Pedidos.

Novedades

Barra de filtros igual que en Pedidos, encima de la tabla de Alertas: buscador libre (proveedor, pedido, hotel), hotel, estado, nivel (Urgente/Aviso) y si ya fue notificada o no.
Filtrado instantáneo: al elegir un filtro, la tabla se actualiza al momento sin recargar datos del servidor.
Contador "Mostrando X de Y alertas" para saber de un vistazo cuántas hay tras aplicar el filtro.
Botón "✕ Limpiar" para quitar todos los filtros de golpe.
Mensaje claro cuando ningún resultado coincide con el filtro elegido.

# v12.1.4 — 23 junio 2026

🔔 Trazabilidad de notificaciones en el panel de Alertas de seguimiento

Hasta ahora, al pulsar "Notificar" en una alerta de seguimiento no quedaba visible si esa alerta ya había sido avisada antes, con el riesgo de notificar varias veces sin saberlo al proveedor o al comprador.

Novedades

Nueva columna "Notificación" en la tabla de Alertas de seguimiento: muestra si la alerta ya se notificó, cuándo (fecha y hora) y por qué canal (Email, Telegram, o ambos). Si nunca se notificó, se indica claramente "⛔ Sin notificar".
El botón cambia de "✉ Notificar" a "🔁 Re-notificar" cuando ya existe un envío previo, con un tooltip que muestra la fecha exacta de la última notificación.
Aviso dentro del modal de envío: si la alerta ya fue notificada antes, aparece un banner de advertencia con la fecha y el canal, antes de confirmar un nuevo envío.
El informe de impresión de Alertas incluye también esta información para mantener la trazabilidad sobre papel.

La fecha de "última notificación" se calcula a partir del histórico ya registrado en el sistema (envíos de email de alerta y avisos de Telegram), sin necesidad de ninguna tabla ni configuración nueva.



📬 Notificaciones de cambio de estado más claras y completas (correo y Telegram)

Se enriquece el contenido de los avisos automáticos (correo interno y Telegram) que se generan al cambiar el estado de un pedido, para dar una visión completa y autoexplicativa del seguimiento de entregas sin tener que entrar al sistema.

🎯 Qué cambia
Situación anterior

El aviso solo indicaba el hotel, departamento, pedido, proveedor y el cambio de estado (anterior → nuevo), sin ninguna referencia a las fechas de entrega.

Novedades

Histórico de entregas con fechas: en ENTREGA PARCIAL y ENTREGADO, el correo y el mensaje de Telegram incluyen ahora la lista completa de entregas (albaranes) registradas hasta la fecha, cada una con su número y su fecha. La entrega que cierra el pedido (ENTREGADO) se resalta como "Entrega final (TOTAL)".
Mensaje introductorio según el estado: una frase de contexto aclara qué ha ocurrido (entrega parcial registrada, entrega total completada, o pedido cancelado), antes de entrar en el detalle.
Más datos de control y seguimiento: se añade el número de presupuesto, el importe del pedido, la fecha de tramitación y los días transcurridos desde entonces — útil para detectar pedidos que se demoran.
Motivo de cancelación visible: si el pedido se cancela y hay observaciones registradas, se muestran en el aviso.
Asunto del correo más informativo: incluye la fecha de la última entrega registrada cuando aplica.


📧 Mejora de la comunicación con proveedores en pedidos enviados

Se rediseña el contenido del correo enviado al proveedor cuando un pedido pasa al estado ENVIADO AL PROVEEDOR, con el objetivo de mejorar la comprensión del mensaje y aumentar la tasa de respuesta por parte del proveedor.

🎯 Nuevo enfoque de comunicación
Situación anterior

El correo informaba únicamente de que el pedido había sido tramitado.

Ejemplo conceptual:

Su pedido ha sido tramitado.

Aunque correcto desde el punto de vista técnico, el mensaje no explicaba claramente:

Que el proveedor ya había recibido previamente el pedido.
Qué acción concreta se esperaba de él.
Cuál era el objetivo de la comunicación.
✉️ Referencia explícita al pedido previamente enviado

El nuevo texto contextualiza el mensaje indicando que el proveedor ya recibió el pedido a través del sistema habitual.

Se incorpora una introducción similar a:

Recientemente habrá recibido, a través de nuestro sistema habitual de pedidos,
el pedido que se detalla a continuación.
Beneficios
Evita que el proveedor interprete el correo como un nuevo pedido.
Refuerza la continuidad de la conversación comercial.
Reduce posibles duplicidades o confusiones.
📅 Solicitud clara de fecha estimada de entrega

Se añade una explicación directa del motivo del correo.

El mensaje indica expresamente que la finalidad es:

Confirmar la correcta recepción del pedido.
Solicitar la fecha prevista de entrega.

Ejemplo conceptual:

El presente correo tiene como finalidad confirmar su recepción y solicitarle
la fecha estimada de entrega en el hotel.
📨 Llamada a la acción mejorada

Se incorpora un bloque específico solicitando una respuesta directa al comprador responsable.

El proveedor recibe instrucciones claras para:

Confirmar la recepción.
Indicar la fecha estimada de entrega.
Responder directamente al comprador asignado.
Resultado

El correo deja de ser meramente informativo y pasa a ser una solicitud operativa concreta.

👤 Mayor visibilidad del comprador responsable

El correo del comprador aparece ahora en dos ubicaciones:

En la solicitud de respuesta

Dentro del cuerpo principal del mensaje.

En la firma

Junto a los datos de contacto habituales.

Beneficios
Facilita la respuesta inmediata del proveedor.
Reduce consultas innecesarias.
Mejora la trazabilidad de las comunicaciones.
🧹 Simplificación de información no relevante
Eliminado "Estado actual"

Se elimina del correo el bloque:

Estado actual: ENVIADO AL PROVEEDOR

al considerarse información interna que no aporta valor al destinatario externo.

Beneficios
Mensaje más limpio.
Menor ruido visual.
Mayor foco en la acción requerida.
🎨 Nuevo bloque visual de identificación del pedido

Se incorpora un panel destacado con borde corporativo Princess para agrupar la información principal del pedido.

Información resaltada
Número de pedido.
Hotel.
Proveedor.
Referencias relevantes.
Datos operativos asociados.
Objetivo

Permitir que el proveedor identifique rápidamente el pedido sin necesidad de leer todo el contenido del correo.

✅ Resultado
Comunicación más clara y orientada a la acción.
Menor riesgo de que el proveedor ignore el correo.
Solicitud explícita de confirmación y fecha de entrega.
Mejor identificación del pedido.
Mayor visibilidad del comprador responsable.
Eliminación de información interna irrelevante.
Diseño más profesional y alineado con la operativa real de seguimiento de pedidos.

# v12.1.0 — 19 junio 2026

## 🗑️ Eliminación definitiva de Resend

Resend queda completamente eliminado del proyecto. Todo el envío de email pasa a gestionarse desde el frontend vía EmailJS, de forma consistente con lo que ya ocurría desde la v11.9.6 para cambios de estado, notificaciones a proveedores y aprobación de usuarios.

### Contexto: inconsistencia del changelog anterior

El changelog desde v11.9.6 declaraba "Eliminada la dependencia funcional de Resend", lo cual era cierto para:
- ✅ Cambios de estado
- ✅ Notificaciones automáticas a proveedor
- ✅ Aprobación de usuario (con fallback EmailJS)

Pero no lo era para:
- ❌ Envío manual de alertas (`/api/alertas/<id>/enviar-email`)
- ❌ Recuperación de contraseña (`/api/password-reset/solicitar`)
- ❌ Solicitud de acceso Fase 2 (`/api/admin/solicitudes-acceso/<id>/enviar-fase2`)

Esta versión cierra esas tres excepciones.

### Cambios (por fases)

**Fase 1 — `/api/alertas/<id>/enviar-email`**
- Eliminada la llamada a `_send_email()`.
- El endpoint registra el email en `emails_log` con estado `Pendiente de envío vía EmailJS`.
- El JSON de respuesta incluye `email_pendiente` con `to_email`, `cc_emails`, `subject`, `body_html` y `body_text` para que el frontend lo envíe vía EmailJS.

**Fase 2 — `/api/password-reset/solicitar`**
- Eliminadas las llamadas a `_send_email()` (al usuario y al admin como fallback).
- El endpoint devuelve siempre `sin_email: true` con `link`, `email`, `nombre`, `subject` y `body_html`.
- El frontend ya manejaba este caso; ahora es el único camino.

**Fase 3 — `/api/admin/solicitudes-acceso/<id>/enviar-fase2`** y **`/api/solicitar-usuario/completar-fase2`**
- Eliminadas todas las llamadas a `_send_email()` (email al usuario solicitante y emails a admins).
- Ambos endpoints devuelven siempre los datos pendientes para EmailJS.
- El frontend ya tenía la lógica de envío; ahora se activa siempre.

**Fase 4 — Limpieza de backend**
- Eliminada la función `_send_email()`.
- Eliminadas las constantes `RESEND_API_KEY` y `EMAIL_FROM`.
- Eliminadas las variables de entorno SMTP (nunca llegaron a usarse en producción).
- Actualizado el docstring del módulo.

**Fase 5 — Limpieza de infraestructura**
- Eliminado `render.yaml` (contenía referencias a `RESEND_API_KEY` y `EMAIL_FROM`).

**Fase 6 — Documentación**
- Actualizada `GUIA_DESPLIEGUE.md`: eliminadas todas las referencias a Resend; el Paso 2 ahora describe la configuración de EmailJS en el frontend.
- Corregida la inconsistencia del changelog: la declaración "Eliminada la dependencia funcional de Resend" es ahora completamente cierta.

---

# v12.0.8 — 19 junio 2026

## 🔔 Telegram de cambio de estado alineado con el correo interno

El Telegram inmediato de cambio de estado (`_telegram_cambio_estado`) pasa a comportarse igual que el correo interno, con la única excepción de que **nunca se envía Telegram al proveedor**:

- **Filtro de estados:** ahora solo se dispara para los mismos estados que el correo interno (`ESTADOS_EMAIL_INTERNO`: `ENVIADO AL PROVEEDOR`, `ENTREGA PARCIAL`, `ENTREGADO`, `CANCELADO`). Antes se enviaba en cualquier cambio de estado, incluidos los `PENDIENTE...`.
- **Destinatarios ampliados:** además de los compradores del hotel, ahora también reciben Telegram los usuarios con rol "hotel" asignados a ese hotel (igual conjunto de destinatarios que el BCC del correo interno), siempre que tengan `telegram_chat_id` configurado.
- **Comportamiento ante falta de chat_id:** si un usuario hotel no tiene `telegram_chat_id`, simplemente no recibe Telegram, pero el comprador (si lo tiene) lo recibe igualmente — y viceversa. No es necesario que ambos lo tengan.
- Nueva función `_get_usuarios_hotel_rol_telegram()` para obtener los usuarios rol "hotel" de un hotel junto con su `telegram_chat_id`.

---

# v12.0.6 — 19 junio 2026

## 🏷️ Tarifa acordada (pedidos sin presupuesto)

Se añade una casilla **"🏷️ Tarifa acordada (pedido sin presupuesto)"** en el apartado de presupuesto del formulario de pedido.

- Por defecto está **siempre desmarcada**: el usuario debe poder introducir el Nº Presupuesto y adjuntar su documento normalmente.
- Si se **marca**, el campo Nº Presupuesto y el botón de adjuntar documento se deshabilitan visualmente y dejan de ser obligatorios.
- Al pasar el pedido a `ENVIADO AL PROVEEDOR`, si la casilla está marcada, el backend **omite** la validación de Nº Presupuesto obligatorio y de documento adjunto, permitiendo guardar el pedido sin ese requisito.
- Nueva columna `tarifa_acordada` (booleano, por defecto `FALSE`) en la tabla `pedidos`, migrada automáticamente al arrancar la app.

---

# v12.0.4 — 19 junio 2026

## 🛡️ Validación obligatoria de proveedor antes de "ENVIADO AL PROVEEDOR"

Esta versión incorpora una nueva capa de protección para evitar que un pedido pueda cambiar al estado:

```text
ENVIADO AL PROVEEDOR
```

cuando no existe un proveedor válido o cuando el proveedor seleccionado no dispone de ninguna dirección de correo electrónico operativa para recibir la comunicación.

El objetivo es garantizar que todo pedido marcado como enviado tenga realmente un destinatario disponible.

---

## 🚫 Problema detectado

Hasta ahora era posible que un usuario cambiara un pedido a:

```text
ENVIADO AL PROVEEDOR
```

aunque ocurriera alguna de estas situaciones:

### Caso 1

```text
Pedido sin proveedor asignado
```

---

### Caso 2

```text
Proveedor asignado
↓
Sin email en contactos principales
```

---

### Consecuencia

El pedido quedaba registrado como enviado aunque posteriormente el sistema no tuviera ningún destinatario real al que enviar la comunicación.

Esto podía generar:

* Pedidos aparentemente enviados.
* Ausencia de notificación al proveedor.
* Incidencias de seguimiento.
* Pérdida de trazabilidad operativa.

---

## 🔒 Doble barrera de validación

La protección se implementa tanto en backend como en frontend.

---

## ⚙️ Backend (`app.py`)

### Validación en `update_pedido()`

Se añaden nuevas comprobaciones dentro del flujo:

```python
PUT /api/pedidos/<pid>
```

cuando el estado solicitado es:

```text
ENVIADO AL PROVEEDOR
```

---

### Check 0a — Proveedor obligatorio

Antes de ejecutar cualquier otra validación se verifica que exista un proveedor asociado.

Si no existe:

```text
proveedor_id vacío
```

la API devuelve:

```http
HTTP 422
```

con el mensaje:

```text
Asigne un proveedor antes de cambiar el estado.
```

---

### Check 0b — Email obligatorio

Si existe proveedor, el sistema verifica que al menos uno de los contactos principales disponga de correo electrónico.

La comprobación utiliza la función oficial:

```python
_get_proveedor_emails_principales()
```

---

### Error devuelto

Si no existe ningún email válido:

```http
HTTP 422
```

incluyendo:

* Nombre del proveedor.
* Descripción del problema.
* Instrucción para corregirlo.

Ejemplo:

```text
El proveedor no dispone de ningún email principal configurado.
Acceda a la ficha del proveedor y añada un email al contacto principal.
```

---

### Prioridad de ejecución

Estas comprobaciones se ejecutan antes de:

* Nº Pedido (DALI/SAP)
* Nº Presupuesto
* Adjuntos obligatorios
* Cualquier otra validación documental

para ofrecer al usuario un mensaje directo y sin información irrelevante.

---

## 🖥️ Frontend (`templates/index.html`)

### Respuesta inmediata al usuario

Se añade una validación preventiva antes de enviar la petición al servidor.

---

### Al seleccionar un proveedor

La función:

```javascript
seleccionarProveedor()
```

almacena ahora también el correo principal en:

```html
data-email
```

del campo oculto:

```html
#p-proveedor
```

---

### Al abrir un pedido existente

Cuando se carga el modal:

```javascript
openPedido()
```

el sistema rellena automáticamente:

```html
data-email
```

utilizando:

```javascript
proveedor_email
```

recibido desde la API.

---

### Al limpiar el proveedor

Si el usuario elimina el proveedor seleccionado:

* Se limpia el identificador.
* Se limpia el nombre.
* Se limpia también `data-email`.

evitando información residual.

---

## 🚨 Nuevas validaciones en `savePedido()`

Antes de ejecutar cualquier otra comprobación de:

```text
ENVIADO AL PROVEEDOR
```

se verifican los nuevos requisitos.

---

### Sin proveedor

El sistema:

* Bloquea el guardado.
* Muestra un toast descriptivo.
* Sitúa el foco automáticamente en el campo proveedor.

Duración:

```text
8 segundos
```

---

### Sin email principal

El sistema:

* Bloquea el guardado.
* Muestra el nombre del proveedor afectado.
* Indica cómo resolver el problema desde la ficha del proveedor.

Duración:

```text
10 segundos
```

---

## 🎯 Beneficios operativos

### Integridad del proceso

Todo pedido marcado como:

```text
ENVIADO AL PROVEEDOR
```

dispone necesariamente de:

* Proveedor asignado.
* Destinatario válido.

---

### Mejor experiencia de usuario

Los errores se detectan inmediatamente.

El usuario recibe instrucciones claras para resolver el problema sin necesidad de revisar múltiples validaciones posteriores.

---

### Protección multicapa

La validación existe en:

* Frontend (experiencia de usuario).
* Backend (seguridad definitiva).

Aunque alguien manipule la interfaz o invoque la API directamente, las reglas continúan aplicándose.

---

## ✅ Resultado

* Ya no es posible enviar pedidos sin proveedor.
* Ya no es posible enviar pedidos a proveedores sin email configurado.
* Validación coherente entre frontend y backend.
* Mensajes de error más claros y accionables.
* Mayor trazabilidad del proceso de compras.
* Reducción de incidencias derivadas de configuraciones incompletas de proveedores.
* Garantía de que todo pedido marcado como enviado tiene un destinatario real disponible.

# v12.0.2 — 19 junio 2026

## 📧 Unificación y optimización de destinatarios en correos de cambio de estado

Esta versión simplifica y consolida la lógica de distribución de correos asociados a los cambios de estado de pedidos, eliminando duplicidades y garantizando que cada destinatario reciba únicamente las comunicaciones que realmente le corresponden.

---

## 🔄 Nuevo modelo de notificaciones para "ENVIADO AL PROVEEDOR"

### Situación anterior

Cuando un pedido pasaba a:

```text
ENVIADO AL PROVEEDOR
```

el sistema generaba:

* Correo al proveedor.
* Correo interno independiente para seguimiento.

Esto podía provocar duplicidad de comunicaciones para los usuarios responsables del hotel.

---

### Nuevo funcionamiento

A partir de esta versión se genera un único correo.

#### Destinatarios principales

Todos los contactos del proveedor marcados como:

```text
⭐ PRINCIPAL
```

reciben la comunicación en el campo:

```text
Para:
```

---

### Seguimiento interno mediante BCC

Los usuarios internos asociados al hotel reciben copia oculta:

```text
BCC
```

Incluye:

* Compradores asignados al hotel.
* Usuarios con rol Hotel asociados al mismo hotel.

---

### Beneficios

* Eliminación de correos duplicados.
* Menor volumen de notificaciones.
* Seguimiento completo para todos los responsables internos.
* Proveedor y equipo interno comparten exactamente la misma comunicación.

---

## 🏨 Correos internos de cierre y seguimiento

### Estados afectados

```text
ENTREGA PARCIAL
ENTREGADO
CANCELADO
```

Estos estados continúan generando exclusivamente comunicaciones internas.

El proveedor no recibe ningún correo asociado a estos cambios.

---

### Distribución de destinatarios

El sistema utiliza ahora una lógica homogénea para todos estos estados.

#### Campo "Para"

Se asigna al primer comprador responsable del hotel.

---

#### Campo "BCC"

Se incorporan:

* Resto de compradores asignados al hotel.
* Todos los usuarios con rol Hotel asociados al mismo hotel.

---

### Resultado

Todos los responsables operativos reciben la información sin exponer entre sí las direcciones de correo.

---

## 🔒 Aislamiento completo por hotel

Se refuerza el filtrado de destinatarios utilizando siempre:

```python
hotel_codigo
```

del pedido que origina la notificación.

---

### Garantía operativa

Un cambio de estado en un pedido de:

```text
Hotel IT
```

solo podrá generar correos para:

* Compradores del Hotel IT.
* Usuarios Hotel del Hotel IT.

---

### Exclusiones automáticas

No recibirán comunicaciones:

* Compradores de otros hoteles.
* Usuarios Hotel de otros hoteles.
* Usuarios sin vinculación con el hotel del pedido.

---

## 🧹 Deduplicación automática de destinatarios

Se añade protección frente a configuraciones donde un mismo usuario pueda aparecer por múltiples vías de asignación.

Ejemplo:

```text
usuario_comprador_hoteles
usuario_hoteles
```

---

### Nuevo comportamiento

La construcción final de destinatarios aplica:

```python
dict.fromkeys(...)
```

para eliminar repeticiones manteniendo el orden original.

---

### Beneficios

* Un usuario nunca recibe el mismo correo dos veces.
* Evita duplicidades provocadas por configuraciones cruzadas.
* Mantiene la trazabilidad correcta de las comunicaciones.

---

## 🎯 Resultado

* Eliminados correos internos duplicados en "ENVIADO AL PROVEEDOR".
* Seguimiento interno integrado mediante BCC.
* Correos internos unificados para ENTREGADO, CANCELADO y ENTREGA PARCIAL.
* Filtrado estricto por hotel.
* Protección frente a destinatarios duplicados.
* Menor volumen de correo generado.
* Mayor coherencia y mantenibilidad en la lógica de notificaciones.
* Distribución más limpia y alineada con la estructura organizativa de cada hotel.

# v12.0.0 — 18 junio 2026

## ⭐ Gestión avanzada de contactos principales de proveedor

Esta versión introduce una mejora importante en la gestión de contactos de proveedores, permitiendo definir múltiples destinatarios prioritarios para las comunicaciones automáticas del sistema.

El objetivo es adaptar el envío de notificaciones a la realidad operativa de muchos proveedores, donde intervienen varios departamentos (compras, administración, logística, dirección comercial, etc.).

---

## ⭐ Múltiples contactos principales

### Situación anterior

Cada proveedor solo podía tener un único contacto marcado como principal.

La selección funcionaba de forma exclusiva:

```text
Contacto A  ⭐ Principal
Contacto B
Contacto C
```

Al marcar un nuevo contacto, el anterior perdía automáticamente dicha condición.

---

### Nuevo funcionamiento

Ahora es posible marcar varios contactos simultáneamente como principales.

Ejemplo:

```text
Contacto Compras        ⭐ PRINCIPAL
Contacto Logística      ⭐ PRINCIPAL
Contacto Administración ⭐ PRINCIPAL
```

Todos los contactos seleccionados mantienen visible el distintivo:

```text
PRINCIPAL
```

de forma simultánea.

---

## 📧 Nuevo sistema centralizado de destinatarios

### Nueva función backend

Se incorpora:

```python
_get_proveedor_emails_principales()
```

como punto único para obtener los correos electrónicos principales de un proveedor.

---

### Beneficios

Antes existían múltiples consultas independientes con lógica similar:

```sql
LIMIT 1
```

repartidas por distintas zonas del sistema.

Ahora:

* La lógica queda centralizada.
* Se elimina duplicidad de código.
* Se simplifica el mantenimiento futuro.
* Se garantiza un comportamiento uniforme.

---

## 📨 Correos automáticos de cambio de estado

### Integración en `enviar_emails_estado()`

Los correos automáticos asociados a cambios de estado utilizan ahora:

```python
_get_proveedor_emails_principales()
```

como fuente oficial de destinatarios.

---

### Nuevo comportamiento

Si existen varios contactos principales:

```text
compras@proveedor.com
logistica@proveedor.com
administracion@proveedor.com
```

todos se incorporan directamente al campo:

```text
Para:
```

como destinatarios principales.

---

## 🚨 Modal "Enviar email de alerta"

### Integración completa

El envío manual desde:

```text
Enviar email de alerta
```

utiliza exactamente la misma lógica.

---

### Resultado

Las alertas se envían simultáneamente a todos los contactos marcados como principales.

Esto garantiza que las incidencias importantes lleguen a todos los interlocutores relevantes del proveedor.

---

## 🔄 Consistencia entre comunicaciones

A partir de esta versión:

### Correos automáticos

* Cambios de estado.
* Notificaciones operativas.

### Correos manuales

* Alertas enviadas desde la aplicación.

utilizan exactamente el mismo conjunto de destinatarios.

---

## 📊 Ámbitos no modificados

Por decisión de diseño, esta versión no altera los procesos donde el correo del proveedor se utiliza únicamente como dato informativo.

Entre ellos:

* Exportaciones Excel.
* Auditoría de pedidos eliminados.
* Informes históricos.
* Consultas de visualización.

En estos casos se mantiene el comportamiento existente para evitar cambios innecesarios en formatos y reportes ya consolidados.

---

## ⚠️ Consideración operativa

Con el nuevo modelo pueden existir tres escenarios:

### Caso 1

```text
1 contacto principal
```

Comportamiento idéntico al anterior.

---

### Caso 2

```text
Varios contactos principales
```

Todos reciben la comunicación simultáneamente.

---

### Caso 3

```text
Ningún contacto principal
```

La función:

```python
_get_proveedor_emails_principales()
```

devuelve una lista vacía.

En consecuencia:

* No se generan destinatarios.
* No se envía correo al proveedor.
* No se produce error de aplicación.

Este comportamiento queda pendiente de validación operativa para decidir si en futuras versiones debe existir un mecanismo de respaldo automático.

---

## 🎯 Objetivo de la mejora

La funcionalidad responde a una necesidad operativa habitual:

* Compras quiere recibir las reclamaciones.
* Logística necesita conocer incidencias de entrega.
* Administración debe disponer de determinadas comunicaciones.
* Dirección comercial puede requerir visibilidad sobre pedidos estratégicos.

Ahora el administrador puede definir exactamente qué contactos participan en las notificaciones simplemente marcándolos como principales desde la ficha del proveedor.

---

## 🛠️ Corrección de ruta de backups corporativos

### Problema detectado

Durante las validaciones posteriores a la implantación del nuevo sistema distribuido de restauración de copias de seguridad se detectó que parte de la configuración seguía apuntando a una ruta local basada en unidad mapeada.

Ruta incorrecta detectada:

```text
G:\CARPETA COMPRADORES\COMPRADOR 1 - VICTOR MARTIN\04.PEDIDOS EXTERNOS CONTROL\Backups
```

Este enfoque dependía de configuraciones específicas de Windows y podía provocar comportamientos distintos según el equipo donde se ejecutara el agente de restauración.

---

### Ruta corregida

Se establece como ubicación oficial de trabajo la ruta UNC corporativa:

```text
\\shtabaiba\direccioncomprascanarias$\CARPETA COMPRADORES\COMPRADOR 1 - VICTOR MARTIN\04.PEDIDOS EXTERNOS CONTROL\Backups
```

---

### Beneficios

* Eliminada la dependencia de unidades mapeadas (`G:`).
* Compatibilidad entre todos los equipos autorizados.
* Mayor fiabilidad para tareas programadas de Windows.
* Acceso uniforme para backup y restauración.
* Menor riesgo de incidencias por diferencias de configuración local.

---

### Componentes afectados

La corrección aplica a:

* `restore_agent.py`
* Sincronización de `backups_cache`
* Listado de backups desde el panel de administración
* Lectura de logs asociados a backups
* Procesos de restauración ejecutados desde la aplicación

---

### Riesgo

**Muy bajo.**

No se modifica la lógica de restauración ni la estructura de base de datos.

Únicamente se corrige la ubicación física utilizada para acceder a las copias de seguridad corporativas.

---

## ✅ Resultado

### Gestión de proveedores

* Soporte para múltiples contactos principales por proveedor.
* Eliminación de consultas duplicadas basadas en `LIMIT 1`.
* Centralización de la lógica de destinatarios.
* Correos automáticos enviados a todos los responsables relevantes.
* Correos manuales alineados con la misma configuración.
* Mayor flexibilidad operativa para la gestión de proveedores.

### Sistema de backups

* Restauraciones utilizando la ruta corporativa oficial.
* Eliminada la dependencia de unidades mapeadas.
* Mayor fiabilidad en procesos de backup y recuperación.
* Consistencia entre todos los equipos autorizados.

### Resultado global

* Arquitectura más robusta.
* Menor duplicidad de código.
* Mayor mantenibilidad.
* Mejor alineación con la operativa real de Compras.
* Preparación para futuras ampliaciones de notificaciones multidestinatario.

## v11.9.8 — 18 junio 2026

### 📧 Corrección de destinatarios en correos internos de cambio de estado

Se corrige un problema en la generación de correos internos asociados a determinados cambios de estado de pedido.

---

## 🐛 Problema detectado

Cuando un pedido cambiaba a alguno de los estados:

```text
ENTREGADO
CANCELADO
ENTREGA PARCIAL
```

el correo interno reutilizaba una variable procedente de otro bloque de código diseñado originalmente para los correos enviados al proveedor.

Como consecuencia, los destinatarios podían no corresponder exactamente con los responsables del hotel asociado al pedido.

---

## 🔍 Causa raíz

La lógica utilizaba:

```python
_get_admin_emails()
```

para determinar los destinatarios internos.

Esta función está diseñada para otros procesos globales del sistema y devuelve usuarios con perfil:

* Administrador
* Compras

sin filtrar por hotel.

De hecho, su propio propósito es servir para notificaciones generales de pedidos y tareas administrativas.

---

## ✅ Solución aplicada

Se sustituye la obtención de destinatarios por:

```python
_get_compradores_cc(pedido.get("hotel_codigo",""))
```

que ya era la función utilizada en los correos enviados al proveedor para determinar los responsables del hotel correspondiente.

---

## 🔄 Unificación de la lógica de destinatarios

A partir de esta versión:

### Correo al proveedor

Utiliza:

```python
_get_compradores_cc()
```

para calcular las copias de seguimiento.

---

### Correo interno

Utiliza exactamente la misma función:

```python
_get_compradores_cc()
```

como fuente de verdad única para determinar los compradores responsables.

---

## 🏨 Filtrado correcto por hotel

Los correos internos quedan ahora correctamente limitados al hotel asociado al pedido.

Ejemplo:

```text
Pedido Hotel IT
      ↓
Compradores asignados Hotel IT
      ↓
Correo interno
```

Sin incluir compradores de otros hoteles.

---

## 👥 Soporte para múltiples compradores

La corrección mantiene el comportamiento multiusuario ya existente.

Si un hotel tiene varios compradores asignados:

```text
Comprador A
Comprador B
Comprador C
```

el sistema distribuye los destinatarios siguiendo el patrón estándar:

* Primer destinatario → Para
* Resto → BCC

garantizando la recepción por todos los responsables del hotel.

---

## 📦 Estados afectados

La corrección aplica específicamente a los estados:

```text
ENTREGADO
CANCELADO
ENTREGA PARCIAL
```

que utilizan el flujo de correo interno y no pasan por el bloque de notificaciones al proveedor.

---

## 🛡️ Impacto

* Eliminado el riesgo de notificaciones cruzadas entre hoteles.
* Destinatarios alineados con la asignación real de compradores.
* Unificación de la lógica de cálculo de responsables.
* Reducción de duplicidad de criterios de envío.
* Mayor coherencia entre correos internos y externos.

---

## ✅ Resultado

Las notificaciones internas de cierre, cancelación o entrega parcial llegan únicamente a los compradores responsables del hotel asociado al pedido, utilizando la misma fuente de verdad que el resto de comunicaciones del sistema.

## v11.9.6 — 18 junio 2026

### 📧 Finalización de la migración operativa a EmailJS

Esta versión completa la migración de los flujos críticos de correo electrónico hacia **EmailJS + Gmail**, eliminando la dependencia funcional de Resend en los procesos de negocio más importantes de la aplicación.

El backend deja de intentar enviar correos directamente en estos flujos y pasa a delegar el envío al frontend mediante EmailJS, siguiendo la misma arquitectura ya utilizada en recuperación de contraseña.

---

## 👤 Aprobación de usuarios

### Situación anterior

Al aprobar un usuario:

```text id="oldflow1"
Administrador
      ↓
Backend (Resend)
      ↓
Error silencioso
      ↓
Aviso manual al administrador
```

Las credenciales se generaban correctamente, pero el correo de bienvenida no llegaba automáticamente al usuario cuando Resend no estaba operativo.

---

### Nuevo funcionamiento

Al aprobar un usuario:

```text id="newflow1"
Administrador
      ↓
Backend genera credenciales
      ↓
Frontend recibe datos pendientes
      ↓
EmailJS envía correo
      ↓
Usuario recibe acceso
```

---

### Mejoras incorporadas

* Eliminada la dependencia funcional de Resend para el correo de bienvenida.
* El backend devuelve la información necesaria para el envío.
* El frontend realiza el envío mediante EmailJS.
* Se mantiene el mecanismo de respaldo manual en caso de fallo de EmailJS.
* La experiencia de aprobación vuelve a estar completamente automatizada.

---

## 🔔 Avisos internos a administradores

### Situación anterior

Las notificaciones internas asociadas a nuevas aprobaciones seguían dependiendo de la infraestructura antigua de correo.

En entornos sin Resend operativo:

```text id="oldflow2"
Notificación admin
      ↓
No enviada
```

---

### Nuevo funcionamiento

Las notificaciones se generan dentro del mismo flujo EmailJS utilizado para la aprobación.

Resultado:

* Avisos automáticos.
* Sin dependencia de Resend.
* Comportamiento consistente con el resto de la aplicación.

---

## 📦 Correos de cambio de estado de pedidos

### Refactorización completa de `enviar_emails_estado()`

Se sustituye el envío directo desde backend por un modelo de correos pendientes.

---

### Situación anterior

```text id="oldflow3"
Cambio de estado
      ↓
enviar_emails_estado()
      ↓
Resend
      ↓
Correo no enviado
```

En instalaciones sin Resend operativo, proveedores y destinatarios internos no recibían las notificaciones.

---

### Nuevo funcionamiento

```text id="newflow3"
Cambio de estado
      ↓
Backend construye correos
      ↓
emails_pendientes
      ↓
Frontend
      ↓
EmailJS
      ↓
Destinatarios finales
```

---

### Correos afectados

#### Externos

* Proveedores.
* Seguimiento operativo asociado al pedido.

#### Internos

* Compradores.
* Administradores.
* Destinatarios definidos por el flujo de estado.

---

## 👥 Comprador asignado en copia oculta (BCC)

Nueva mejora en las notificaciones enviadas a proveedores.

El comprador asignado al hotel se incorpora automáticamente como:

```text id="bcc1"
BCC
```

Beneficios:

* Seguimiento completo de las comunicaciones.
* Visibilidad del comprador responsable.
* Sin exponer direcciones internas al proveedor.

---

## 🔄 Integración en todos los flujos de guardado

Se incorpora soporte para correos pendientes en:

### Creación de pedido

```text id="cp1"
create_pedido()
```

---

### Actualización estándar

```text id="up1"
update_pedido()
```

---

### Actualización desde perfil Hotel

```text id="up2"
update_pedido() - flujo Hotel
```

---

## 📨 Nueva función frontend

### `_enviarEmailsPendientesEstado()`

Nueva función responsable de:

* Procesar los correos devueltos por el backend.
* Ejecutar el envío mediante EmailJS.
* Gestionar errores de envío.
* Mantener coherencia con el resto de comunicaciones de la aplicación.

---

## 🛡️ Estrategia de resiliencia

Se mantiene un mecanismo de respaldo para evitar bloqueos operativos.

Si EmailJS no pudiera enviar un correo:

* El guardado del pedido continúa.
* El usuario recibe información del fallo.
* Se conserva la posibilidad de comunicación manual.

La aplicación nunca pierde datos ni interrumpe el flujo principal de trabajo.

---

## 🧹 Preparación para eliminación definitiva de Resend

Esta versión deja la infraestructura antigua de correo en estado de compatibilidad temporal.

Actualmente:

```text id="prep1"
Resend
```

permanece presente únicamente como código legado pendiente de retirada.

Las funcionalidades migradas ya no dependen de:

* `RESEND_API_KEY`
* `_send_email()`
* `api.resend.com`

para su funcionamiento operativo.

---

## 📋 Próxima fase prevista

La siguiente iteración permitirá eliminar definitivamente:

```text id="prep2"
RESEND_API_KEY
EMAIL_FROM
_send_email()
Integraciones api.resend.com
Código heredado asociado
```

una vez validados los flujos en producción.

---

## ✅ Resultado

* Migración práctica completada hacia EmailJS + Gmail.
* Correos de bienvenida nuevamente automáticos.
* Notificaciones de cambio de estado restauradas.
* Compradores incluidos automáticamente en copia oculta.
* Eliminada la dependencia funcional de Resend en procesos críticos.
* Arquitectura de correo unificada y coherente.
* Preparación para retirada definitiva del código legado de envío.

## v11.9.4 — 17 junio 2026

### 🗄️ Columna dedicada `es_correo` en adjuntos

#### Motivo del cambio

* La distinción entre un correo (`.eml`/`.msg`) y un documento normal (PDF, Word, Excel) se calculaba en varios puntos del código mirando la extensión guardada en el nombre del archivo.
* Este enfoque funcionaba, pero dependía de que el nombre se siguiera guardando siempre de la misma forma. Cualquier cambio futuro en ese punto podría romper la clasificación sin que saltara ningún error visible.

#### Cambio de esquema

* Añadida la columna:

```sql
es_correo BOOLEAN NOT NULL DEFAULT FALSE
```

a la tabla `pedido_adjuntos`.

* Migración segura sobre datos ya existentes:

  1. Columna añadida primero como *nullable*.
  2. Backfill de los registros existentes, aplicando la misma heurística de extensión usada anteriormente.
  3. Una vez completado el backfill, se fija el valor por defecto y se marca la columna como `NOT NULL`.

* Nuevo índice:

```sql
idx_adjuntos_tipo_correo (pedido_id, tipo, es_correo)
```

para acelerar los recuentos por tipo y apartado introducidos en la versión anterior.

#### Uso consistente en todo el backend

* `upload_adjunto`: el valor de `es_correo` se calcula una sola vez en el momento de la subida y se guarda directamente, sin volver a inferirlo en cada lectura posterior.
* Los recuentos de documentos y correos por apartado (`presupuesto_doc`, `solicitud_doc`) pasan a filtrar por la columna (`AND es_correo` / `AND NOT es_correo`) en lugar de por patrones de nombre.
* `download_adjunto`: la cabecera `Content-Disposition` (`inline` para previsualización, `attachment` para correos) se decide ahora también a partir de esta columna, unificando el criterio en todo el archivo.
* Los listados de adjuntos de pedido y presupuesto separan documentos y correos usando el mismo campo.

#### Cambio de comportamiento en `pedido_doc`

* Antes: el apartado **Nº Pedido (DALI/SAP)** admitía un único adjunto en total, fuera documento o correo.
* Ahora: admite **1 documento y 1 correo de forma simultánea**, en línea con el criterio ya aplicado en `presupuesto_doc` y `solicitud_doc`.

---

### ✅ Resultado

* Una única fuente de verdad para distinguir correos de documentos en toda la aplicación.
* Eliminado el riesgo de que un cambio futuro en el formato del nombre de archivo rompa silenciosamente los recuentos o la previsualización.
* Migración aplicada de forma segura sobre los adjuntos ya existentes, sin pérdida de clasificación.
* Mayor flexibilidad en el apartado de pedido, permitiendo documento y correo a la vez.


## v11.9.2 — 17 junio 2026

### 📎 Límites de tamaño y cantidad en adjuntos

#### Motivo del cambio

* Los adjuntos (PDF, Word, Excel, correos `.eml`/`.msg`, imágenes) se almacenan directamente en la base de datos PostgreSQL de Supabase.
* Sin límites específicos por tipo de contenido, el ritmo de crecimiento medido ponía en riesgo el límite de espacio del plan gratuito en pocos meses.

#### Nuevos límites de peso por tipo de contenido

* **Documentos** (PDF / Word / Excel): máximo **5 MB** por archivo.
* **Correos** (`.eml` / `.msg`): máximo **3 MB** por archivo.
* **Imágenes** (`imagen_articulo`): máximo **2 MB** por archivo.

Sustituyen al límite genérico anterior de 20 MB para todos los tipos, que se mantiene únicamente como tope absoluto de respaldo.

#### Nuevos límites de cantidad por apartado

* **`pedido_doc`**: máximo 1 adjunto.
* **`presupuesto_doc`** y **`solicitud_doc`**: máximo **3 documentos** + **1 correo**, contados de forma independiente.
* **`vb_eml`** y **`tramit_eml`**: máximo 1 correo cada uno.

#### Alcance del cambio

* Los nuevos límites afectan únicamente a las subidas realizadas a partir de esta versión.
* Los adjuntos ya existentes en base de datos no se ven afectados ni se eliminan.

---

### ✅ Resultado

* Reducción del ritmo de crecimiento del espacio ocupado en Supabase.
* Mensajes de error específicos indicando el límite exacto cuando un archivo lo supera.
* Mayor previsibilidad sobre el tamaño máximo de la base de datos a medio plazo.

## v11.9.0 — 17 junio 2026

### 📧 Mejora de comunicaciones con proveedores

Se incorpora un aviso destacado en todos los correos enviados a proveedores para reducir el riesgo de respuestas dirigidas a destinatarios incorrectos y mejorar la trazabilidad de las comunicaciones.

---

### ✉️ Plantillas de correo actualizadas

Se modifica el contenido de las siguientes plantillas:

#### Reclamación de pedido sin confirmación de entrega

```text
_email_template_enviado_proveedor
```

---

#### Reclamación de entrega parcial pendiente

```text
_email_template_entrega_parcial
```

---

#### Recordatorio de cotización pendiente

```text
_email_template_pendiente_cotizacion
```

---

#### Notificación de cambio de estado

Generada desde:

```text
enviar_emails_estado()
```

---

### 🟨 Nuevo aviso destacado

En cada uno de los correos dirigidos a proveedores se incorpora el mismo mensaje informativo en dos ubicaciones:

#### Inicio del mensaje

* Aviso destacado en color amarillo.
* Visible nada más abrir el correo.

#### Zona de firma

* Repetido junto a los datos del comprador.
* Situado inmediatamente encima de la dirección de correo de contacto.

Objetivo:

* Evitar respuestas a direcciones incorrectas.
* Facilitar la identificación del interlocutor responsable.
* Mejorar la comunicación entre proveedor y comprador.

---

### ℹ️ Exclusión deliberada

No se modifica:

```text
_email_template_pendiente_firma
```

ya que este correo se envía exclusivamente a destinatarios internos:

* Dirección de Compras.
* Dirección del Hotel.

Por tanto, no existe riesgo de respuesta errónea por parte de proveedores externos.

---

## 🔍 Mejora de observabilidad y diagnóstico

Se incorporan nuevos registros de trazabilidad (*logging*) en puntos críticos del sistema.

Estas mejoras no modifican la lógica de negocio ni el comportamiento funcional de la aplicación.

Su objetivo es facilitar el diagnóstico de incidencias en producción.

---

### 👥 Notificaciones a administradores

Se añaden logs en:

```text
_get_admin_emails()
_get_solo_admin_emails()
_get_admins_telegram()
```

#### Utilidad

Si aparecen mensajes asociados a estas funciones en los logs de Render:

* Indican un fallo al consultar la tabla de usuarios.
* Permiten distinguir entre:

  * Problemas de base de datos.
  * Problemas de envío de correo.
  * Problemas de Telegram.

---

### ⚙️ Configuración del sistema

Se añade trazabilidad en:

```text
get_config()
```

#### Utilidad

Permite detectar cuándo la aplicación está utilizando los valores por defecto en lugar de la configuración almacenada desde el panel de administración.

Ejemplos afectados:

* Umbrales de alertas.
* Días de seguimiento.
* Techos de gasto.
* Configuración operativa.

---

### 🚨 Alertas urgentes de techo de gasto

Se añaden registros en:

```text
_ya_notificado_techo_urgente_hoy()
_dias_desde_ultimo_techo_urgente_admin()
```

#### Utilidad

Permiten detectar incidencias que podrían provocar:

* Alertas urgentes duplicadas.
* Reenvíos innecesarios a administradores.
* Fallos de verificación de avisos previos.

---

### 📥 Importaciones Excel

Se añade trazabilidad en:

```text
reset_e_importar()
importar_excel()
```

#### Utilidad

Se registran advertencias cuando una fecha importada:

* No coincide con ninguno de los formatos esperados.
* No puede convertirse correctamente.

Estas incidencias:

* No detienen la importación.
* No generan errores para el usuario.
* Facilitan la identificación de datos inconsistentes en los ficheros origen.

---

## 🛡️ Riesgo y compatibilidad

### Compatibilidad total

* No se modifican estructuras de base de datos.
* No se alteran APIs existentes.
* No cambian permisos ni roles.
* No se modifica la lógica de negocio.

### Riesgo de despliegue

**Muy bajo.**

Todos los cambios se limitan a:

* Mejoras visuales en correos.
* Incorporación de registros diagnósticos.
* Incremento de visibilidad operativa para administración y soporte.

---

### ✅ Resultado

* Comunicaciones más claras con proveedores.
* Menor riesgo de respuestas enviadas al destinatario incorrecto.
* Mayor trazabilidad en procesos críticos.
* Diagnóstico mucho más rápido de incidencias en producción.
* Visibilidad de problemas de configuración y datos importados.
* Sin impacto funcional ni cambios de comportamiento para los usuarios.


## v11.8.8 — 17 junio 2026

### 🛡️ Validaciones reforzadas para "ENVIADO AL PROVEEDOR"

Se endurecen los controles de calidad documental antes de permitir que un pedido pase al estado **ENVIADO AL PROVEEDOR**, garantizando que toda la documentación obligatoria esté correctamente registrada.

---

### ✅ Nuevas validaciones de cambio de estado

Las comprobaciones se ejecutan únicamente cuando el pedido entra en el estado:

```text
ENVIADO AL PROVEEDOR
```

No afectan a posteriores ediciones de pedidos que ya se encuentren en dicho estado.

---

### 📄 Nº Pedido (DALI / SAP)

Nuevo requisito obligatorio:

* El campo **Nº Pedido (DALI / SAP)** debe contener un valor.
* Si está vacío, se bloquea el cambio de estado.

---

### 📎 Documento de pedido (`pedido_doc`)

Nuevas reglas obligatorias:

* Debe existir **exactamente 1 adjunto** de tipo pedido.
* El adjunto debe ser un documento válido:

  * PDF
  * Word

No se admiten:

* Correos electrónicos (`.eml`)
* Correos Outlook (`.msg`)

La validación genera error cuando:

* No existe ningún adjunto.
* Existen varios adjuntos de pedido.
* El único adjunto disponible es un correo electrónico.

---

### 📑 Nº Presupuesto

Nuevo requisito obligatorio:

* El campo **Nº Presupuesto** debe contener un valor.
* Si está vacío, se bloquea el cambio de estado.

---

### 📎 Documento de presupuesto (`presupuesto_doc`)

Nuevas reglas obligatorias:

* Debe existir al menos un documento válido:

  * PDF
  * Word

Se permite la existencia adicional de correos electrónicos asociados.

Sin embargo, la validación genera error cuando:

* No existe ningún documento.
* Solo existen correos electrónicos (`.eml` o `.msg`).

---

### 🔒 Protección adicional en la subida de adjuntos

#### Adjuntos de pedido (`pedido_doc`)

Se añaden restricciones preventivas en `upload_adjunto`.

##### Correos electrónicos bloqueados

No se permite subir:

* `.eml`
* `.msg`

como documento de pedido.

El sistema devuelve un mensaje explicativo indicando que únicamente se admiten documentos oficiales.

##### Límite de un único documento

Solo puede existir un adjunto de tipo:

```text
pedido_doc
```

Si ya existe uno registrado:

* La subida se rechaza.
* Se informa al usuario del motivo.

Con ello se evita la acumulación accidental de múltiples versiones del mismo documento.

---

#### Adjuntos de presupuesto (`presupuesto_doc`)

Sin cambios funcionales.

Continúan permitiéndose:

* Documentos PDF.
* Documentos Word.
* Correos electrónicos asociados.

---

### ⚠️ Respuesta de validación unificada

Cuando alguna comprobación falla, la API devuelve:

```http
HTTP 422 Unprocessable Entity
```

con estructura:

```json
{
  "ok": false,
  "errores": [
    "...",
    "...",
    "..."
  ]
}
```

Características:

* Se devuelve un mensaje independiente por cada problema detectado.
* El frontend puede mostrar todas las incidencias simultáneamente.
* El usuario corrige todos los errores en una única revisión, evitando ciclos repetitivos de validación.

---

### ✅ Resultado

* Se garantiza la existencia de documentación mínima obligatoria antes del envío al proveedor.
* Se evita el uso de correos electrónicos como documento oficial de pedido.
* Se asegura la existencia de referencias DALI/SAP y presupuestos asociados.
* Se previene la duplicidad de documentos de pedido.
* Se mejora la calidad documental y la trazabilidad del proceso de compras.
* Se proporciona una experiencia de usuario más clara mediante validaciones agrupadas y mensajes detallados.

## v11.8.6 — 17 junio 2026

### 🔄 Evolución del sistema de restauración — Arquitectura distribuida

Esta versión sustituye el modelo inicial de restauración directa desde el servidor por una arquitectura basada en cola de trabajo y agente local, eliminando las limitaciones de acceso entre Render y la red corporativa.

---

### 🏗️ Nueva arquitectura de restauración

#### Antes

El servidor web intentaba acceder directamente a la carpeta de backups ubicada en la red local de la empresa.

```text
Render (Cloud)
      ↓
\\Servidor\Backups
```

Este enfoque presentaba limitaciones debido a que la infraestructura cloud no tiene acceso directo a recursos internos de red.

---

#### Ahora

La restauración se realiza mediante una cola de trabajo centralizada en Supabase.

```text
Administrador
      │
      ▼
Solicitud restauración
      │
      ▼
restore_queue
      ▲
      │
restore_agent.py
      │
      ▼
Carpeta Backups
```

El panel web solicita la restauración y un agente local autorizado ejecuta físicamente el proceso.

---

### 🗄️ Nueva tabla de control

#### `restore_queue`

Se incorpora una cola persistente para gestionar solicitudes de restauración.

Permite registrar:

* Backup solicitado.
* Tipo de restauración.
* Usuario solicitante.
* Fecha de solicitud.
* Estado de ejecución.
* Resultado final.
* Errores producidos.

La tabla se crea automáticamente mediante el sistema de auto-migración existente.

---

### 🔧 Cambios Backend (`app.py`)

#### `/api/admin/backup/restaurar`

Cambio de comportamiento:

**Antes**

* Ejecutaba directamente la restauración.

**Ahora**

* Inserta una solicitud en `restore_queue`.
* Verifica que no exista otra restauración pendiente.
* Devuelve el estado de la petición.

---

#### Nueva ruta `/api/admin/backup/estado`

Permite consultar el estado de ejecución de una restauración.

Estados soportados:

```text
Pendiente
En proceso
Completado
Error
```

La información se utiliza para actualizar la interfaz en tiempo real.

---

### 🖥️ Mejoras Frontend (`templates/index.html`)

#### Nuevo flujo "Solicitar restauración"

El botón principal pasa a denominarse:

```text
🔄 Solicitar restauración
```

reflejando el nuevo funcionamiento basado en cola.

---

#### Información para el administrador

El modal de confirmación informa ahora de que:

* La restauración será ejecutada por el agente local autorizado.
* El proceso suele completarse en menos de un minuto.
* El usuario puede seguir el progreso en tiempo real.

---

#### Seguimiento automático

Incorporado sistema de polling cada 5 segundos.

La interfaz actualiza automáticamente el estado:

```text
Pendiente
↓
En proceso
↓
Completado
```

o

```text
Pendiente
↓
Error
```

sin necesidad de recargar la página.

---

#### Resumen de restauración

Al finalizar correctamente se muestra información detallada:

* Pedidos restaurados.
* Adjuntos restaurados.
* Historial recuperado.
* Resultado final del proceso.

---

### 💻 Nuevo componente local

#### `restore_agent.py`

Nuevo agente de restauración ejecutado desde la red corporativa.

Responsabilidades:

* Consultar periódicamente `restore_queue`.
* Detectar nuevas solicitudes.
* Acceder a la carpeta de backups corporativa.
* Restaurar información en Supabase.
* Recuperar adjuntos.
* Actualizar el estado de la operación.

---

#### `restore_agent.bat`

Nuevo lanzador Windows para ejecutar el agente utilizando la misma configuración y conexión ya empleadas por el sistema de backup automático.

---

### 🛡️ Seguridad y fiabilidad

#### Backup automático previo a la restauración

Antes de iniciar cualquier restauración, el agente genera automáticamente una copia de seguridad del estado actual.

Esto permite:

```text
Estado actual
      ↓
Backup de seguridad
      ↓
Restauración solicitada
```

facilitando la reversión en caso de incidencia.

---

#### Registro del backup de seguridad

Cada restauración conserva la referencia del backup preventivo generado antes de ejecutar la operación.

---

#### Caducidad automática de solicitudes

Las peticiones pendientes con más de 24 horas de antigüedad son invalidadas automáticamente para evitar ejecuciones accidentales o tareas obsoletas.

---

#### Auditoría ampliada

Cada restauración registra:

* Usuario solicitante.
* Fecha de solicitud.
* Fecha de inicio.
* Fecha de finalización.
* Resultado obtenido.
* Mensajes de error.
* Backup preventivo generado.

---

### 📖 Documentación

#### `INSTRUCCIONES_RESTAURACION.md`

Nuevo documento de configuración y puesta en marcha.

Incluye:

* Instalación del agente.
* Configuración de la tarea programada.
* Verificación del flujo completo.
* Resolución de incidencias habituales.

---

### ✅ Resultado

* Eliminada la dependencia entre Render y la red corporativa.
* Restauraciones gestionadas desde la aplicación web.
* Ejecución segura mediante agente autorizado.
* Seguimiento en tiempo real del progreso.
* Auditoría completa de todas las operaciones.
* Backup automático previo a cualquier restauración.
* Mayor robustez y capacidad de recuperación ante errores.
* Arquitectura preparada para crecimiento y mantenimiento a largo plazo.

---

### 🔍 Listado de backups también vía agente local

La migración a la arquitectura distribuida se aplicó inicialmente solo a
`/api/admin/backup/restaurar`. La consulta de backups disponibles
(`/api/admin/backup/listar`, botón "Buscar backups" del panel) seguía
intentando leer la carpeta de red directamente desde Render, con el mismo
problema de fondo: la infraestructura cloud no tiene acceso a la red
corporativa, sea cual sea el formato de la ruta (letra de unidad mapeada
o ruta UNC `\\Servidor\...`).

Se completa ahora la migración con el mismo patrón agente-local + Supabase:

```text
restore_agent.py (cada ciclo)
      ↓
Escanea carpeta de backups
      ↓
backups_cache (Supabase)
      ↑
/api/admin/backup/listar (Render) — solo lee esta tabla
```

* Nueva tabla `backups_cache`, creada automáticamente por el sistema de
  auto-migración existente (igual que `restore_queue`).
* `restore_agent.py` sincroniza esta tabla en cada ciclo (cada 1 minuto,
  vía la misma tarea programada que ya procesa restauraciones), antes de
  comprobar si hay peticiones pendientes.
* Si el escaneo falla puntualmente (carpeta no accesible, PC sin red), la
  caché anterior se conserva tal cual — nunca se vacía la lista por un
  fallo transitorio.
* El panel web muestra un aviso si la caché lleva más de 5 minutos sin
  sincronizarse, o si nunca se ha sincronizado para la ruta indicada, en
  vez del genérico "La ruta no existe o no está accesible".
* `/api/admin/backup/log` (botón "📋 Log" de cada backup) tenía el mismo
  problema — leía `backup_log.txt` directamente desde Render. Ahora el
  agente local sube el contenido del log a `backups_cache` junto con el
  resto de metadatos, y esta ruta solo lee de ahí.


## v11.8.4 — 16 junio 2026

### 🔄 Nuevo sistema de restauración de backups

#### Restauración completa desde la interfaz de administración

* Incorporado un nuevo módulo de restauración accesible exclusivamente para usuarios con rol **Administrador**.
* Permite consultar y restaurar copias de seguridad almacenadas en la carpeta de red configurada para backups.

### 🗄️ Nuevas rutas Backend (`app.py`)

#### `/api/admin/backup/listar`

* Nueva ruta para consultar los backups disponibles.
* Devuelve:

  * Nombre del backup.
  * Fecha y hora de creación.
  * Tamaño de la copia.
  * Número de adjuntos incluidos.

#### `/api/admin/backup/restaurar`

* Nueva ruta encargada de ejecutar el proceso de restauración.
* Permite seleccionar entre dos modalidades de recuperación:

  * **Solo pedidos**
  * **Restauración completa**

### 🖥️ Nuevo panel "Restaurar backup"

#### Acceso desde el menú lateral

* Añadido el botón:

```text
🔄 Restaurar backup
```

* Visible únicamente para usuarios Administrador.

#### Exploración de copias disponibles

* El sistema permite consultar automáticamente la ubicación de backups configurada.
* Se muestran todas las copias disponibles con formato:

```text
backup_YYYYMMDD_HHMM
```

incluyendo:

* Fecha.
* Tamaño.
* Información de contenido.

### ⚠️ Restauración segura

#### Modal de confirmación reforzada

Antes de ejecutar cualquier restauración:

* Se muestra una ventana de confirmación específica.
* Se incluyen advertencias visibles sobre el impacto de la operación.
* El administrador debe confirmar explícitamente la acción antes de continuar.

### 🔧 Modos de restauración

#### Solo pedidos (recomendado)

* Restaura exclusivamente la información relacionada con pedidos.
* Conserva:

  * Usuarios.
  * Roles.
  * Proveedores.
  * Configuración del sistema.

Ideal para recuperar pedidos eliminados o revertir incidencias operativas sin afectar al resto de la aplicación.

#### Restauración completa

* Restaura todos los datos contenidos en la copia de seguridad.
* Sustituye la información actual por la existente en el backup seleccionado.

Indicada para escenarios de recuperación global del sistema.

### 📎 Recuperación automática de adjuntos

* Durante el proceso de restauración se recuperan también los documentos asociados.
* Los adjuntos se vuelven a registrar automáticamente en la base de datos.
* Se mantiene la vinculación entre pedidos y documentación restaurada.

### ⚡ Funciones Frontend incorporadas

Se añaden las funciones:

```javascript
restoreCargarLista()
restoreSeleccionar()
restoreCancelar()
restoreEjecutar()
```

encargadas de:

* Consultar los backups disponibles.
* Gestionar la selección de copias.
* Controlar el flujo de confirmación.
* Ejecutar la restauración solicitada.

### ✅ Resultado

* Recuperación de datos completamente integrada en la aplicación.
* Eliminada la necesidad de intervenciones manuales sobre la base de datos para restauraciones habituales.
* Restauración segura mediante confirmación explícita.
* Posibilidad de recuperar únicamente pedidos sin afectar a usuarios, proveedores o configuraciones.
* Recuperación automática de la documentación asociada a cada pedido.


## v11.8.2 — 16 junio 2026

### ✅ Validación obligatoria para "ENVIADO AL PROVEEDOR"

#### Nuevo control previo al envío

* Incorporada una validación en `index.html` que se ejecuta únicamente cuando un pedido cambia al estado:

```text
ENVIADO AL PROVEEDOR
```

* El objetivo es garantizar que el pedido dispone de la información mínima necesaria antes de considerarse enviado.

### 🔍 Validaciones realizadas

Antes de permitir el cambio de estado, el sistema comprueba:

#### Nº Pedido (DALI / SAP)

* El campo **Nº Pedido (DALI / SAP)** debe contener un valor.
* No se permite el envío de pedidos sin referencia de pedido registrada.

#### Documento PDF adjunto

* Debe existir al menos un documento adjunto asociado al pedido.
* La validación utiliza los elementos ya renderizados en `#adj-pedido-list` mediante `cargarAdjuntos()`.

### 🚫 Comportamiento cuando faltan datos

Si alguno de los requisitos no se cumple:

* Se muestra un mensaje de error mediante toast rojo durante 7 segundos.
* El mensaje indica exactamente qué información falta.
* El guardado se cancela automáticamente.
* El modal permanece abierto para que el usuario complete los datos pendientes.

#### Ayuda visual para el usuario

Cuando falta el Nº Pedido:

* El campo se resalta con borde rojo.
* Recibe el foco automáticamente.
* El resaltado desaparece en cuanto el usuario comienza a introducir información.

### 🔄 Activación inteligente

La validación solo se ejecuta cuando existe un cambio real hacia el estado **ENVIADO AL PROVEEDOR**.

#### Casos validados

✅ Pedido nuevo creado directamente como **ENVIADO AL PROVEEDOR**

✅ Pedido que pasa de **PENDIENTE** a **ENVIADO AL PROVEEDOR**

✅ Pedido cancelado que se reactiva y vuelve a **ENVIADO AL PROVEEDOR**

#### Casos excluidos

✅ Pedido que ya estaba en **ENVIADO AL PROVEEDOR** y se reabre para modificar otros datos

* En este caso la validación no se ejecuta nuevamente.
* El usuario puede guardar cambios sin bloqueos innecesarios.

### 🎯 Resultado

* Se evita el envío de pedidos sin número de referencia DALI/SAP.
* Se garantiza la existencia de documentación asociada antes del envío.
* Se reduce el riesgo de incidencias operativas y trazabilidad incompleta.
* La validación actúa únicamente en el momento adecuado, sin interferir en posteriores ediciones del pedido.


## v11.8.0 — 16 junio 2026

### ⚡ Refactorización y optimización del sistema de Alertas

#### Unificación de la lógica de clasificación de alertas

* Extraída la nueva función global:

```python
_clasificar_alertas(pedidos_raw, cfg_activar_plazo)
```

* Centraliza todo el proceso de clasificación de alertas, incluyendo:

  * Estados de alerta.
  * Cálculo de antigüedad.
  * Validación de plazos de entrega.
  * Aplicación de umbrales configurables.

#### Parseo de fechas unificado

* Incorporada la función:

```python
_dias_desde_alerta(fecha_str)
```

* Sustituye múltiples implementaciones locales que realizaban la misma tarea.
* Se elimina código duplicado y se garantiza un comportamiento consistente en todos los módulos de alertas.

#### Umbrales centralizados

* Creado el diccionario único:

```python
_UMBRALES_ALERTAS
```

* Sustituye las estructuras duplicadas:

  * `UMBRALES_H`
  * `UMBRALES`
  * `UMBRALES_BRIDGE`

* Todas las reglas de clasificación utilizan ahora una única fuente de configuración.

#### Simplificación de endpoints

* Los distintos consumidores del sistema de alertas quedan reducidos a:

  1. Consulta de datos.
  2. Llamada a `_clasificar_alertas()`.

* Cualquier modificación futura de reglas, umbrales o criterios de clasificación requiere cambios en un único punto del código.

### 🔧 Unificación de Bridge Alertas

#### Consistencia total entre endpoints

* `bridge_alertas` pasa a utilizar:

  * `_clasificar_alertas()`
  * `PEDIDO_SELECT_STATS`

* Eliminado el SQL específico que mantenía anteriormente.

* Los tres endpoints relacionados con alertas comparten ahora:

  * La misma lógica de clasificación.
  * Los mismos criterios de cálculo.
  * El mismo origen de datos.

### ⚡ Optimización de `/api/stats`

#### Eliminación de COUNT(*) redundante

* En los perfiles Administrador y Compras se elimina la consulta adicional:

```sql
SELECT COUNT(*) FROM pedidos
```

* El total de pedidos se obtiene ahora directamente a partir de los resultados ya devueltos por:

```sql
GROUP BY estado
```

mediante:

```python
sum(r["total"] for r in by_estado)
```

#### Beneficios

* Una consulta menos a la base de datos por cada llamada a `/api/stats`.
* Menor latencia en Dashboard, Alertas y Badges.
* Reducción de carga sobre PostgreSQL.

### ✅ Resultado

* Eliminada la duplicación de lógica de alertas existente en varios módulos.
* Mantenimiento significativamente más sencillo.
* Comportamiento homogéneo entre todos los endpoints de alertas.
* Menor riesgo de inconsistencias futuras.
* Reducción de consultas innecesarias a la base de datos.
* Mejora adicional del rendimiento de estadísticas y paneles de control.


## v11.7.8 — 16 junio 2026

### ⚡ Optimización de rendimiento — Estadísticas y Alertas

#### Nueva capa de caché para estadísticas

* Incorporado `_fetchStats(force)` siguiendo el mismo patrón utilizado en `_fetchTecho()`.
* Añadido almacenamiento temporal en memoria con:

  * TTL de 30 segundos.
  * Reutilización de peticiones en curso (*inflight deduplication*).
  * Función `_invalidarStats()` para forzar la actualización cuando los datos cambian.
* Se evita la generación de múltiples peticiones simultáneas a `/api/stats`.

#### Refactorización de consumo de estadísticas

Las siguientes funciones dejan de realizar llamadas directas a:

```javascript
api('/api/stats')
```

y pasan a utilizar:

```javascript
_fetchStats()
```

* `loadStats()`
* `updateAlertBadge()`
* `loadAlertas()`
* `imprimirAlertas()`

#### Optimización del flujo de guardado

* Tras crear o modificar un pedido se ejecuta:

```javascript
await Promise.all([
    _fetchStats(true),
    loadTechoAlertas()
]);
```

* Las vistas posteriores reutilizan automáticamente la caché de estadísticas ya actualizada.
* Eliminadas peticiones redundantes a la red durante:

  * Guardado de pedidos.
  * Eliminación de pedidos.
  * Importaciones.
  * `refreshCurrentView()`.

#### Reducción de carga sobre `/api/stats`

* Incorporado el nuevo selector `PEDIDO_SELECT_STATS`.
* Esta versión elimina las 5 subconsultas relacionadas con `proveedor_contactos` que no son necesarias para cálculos de estadísticas y alertas.
* Las consultas internas de `/api/stats` utilizan ahora este selector optimizado.

#### Conservación de funcionalidad completa

* `PEDIDO_SELECT` permanece sin cambios para:

  * Modal de edición de pedidos.
  * Listado paginado de pedidos.
  * Pantallas donde sí es necesario mostrar información de contacto de proveedores.

### ✅ Resultado

* Menos peticiones HTTP duplicadas.
* Menor carga sobre PostgreSQL.
* Menor tiempo de respuesta en Dashboard, Alertas y Badges.
* Actualización inmediata de estadísticas tras operaciones de creación, edición, eliminación e importación de pedidos.
* Arquitectura de caché unificada para Techo de Gastos y Estadísticas.


## v11.7.4 — 15 junio 2026

### 🐛 Corrección crítica — Bloqueos en Análisis de Integridad

#### Diagnóstico del problema

* Se identificó un cuello de botella en `_validar_integridad_operativa()`.
* La validación utilizaba un patrón **N+1 Queries**, ejecutando:

  * Una consulta adicional por cada hotel para localizar su comprador asignado.
  * Una consulta adicional por cada comprador para localizar sus hoteles asociados.
* En entornos con numerosos hoteles o compradores, o durante periodos de latencia elevada de la base de datos, la acumulación de consultas podía provocar tiempos de respuesta extremadamente largos.
* El frontend no disponía de timeout para la petición, por lo que permanecía indefinidamente mostrando el mensaje:

  > "Analizando sistema..."

### 🔧 Optimización Backend (`app.py`)

#### Eliminación de consultas N+1

* Reescrita la lógica de validación para utilizar únicamente consultas agregadas mediante `EXISTS` y `GROUP BY`.
* El proceso completo pasa a ejecutarse mediante **7 consultas fijas**, independientemente del número de hoteles o compradores existentes.
* Se elimina el crecimiento lineal del número de consultas y se mejora significativamente el rendimiento.

#### Protección frente a bloqueos de base de datos

* Añadido:

  ```sql
  SET LOCAL statement_timeout = '15s'
  ```
* Si alguna consulta supera los 15 segundos de ejecución, PostgreSQL cancela automáticamente la operación.
* El sistema devuelve un error controlado en lugar de quedar bloqueado indefinidamente.

#### Nuevo control de integridad

* Incorporada la validación:

  * **`compradores_sin_movil`**
* Detecta compradores que no tienen número de teléfono móvil registrado en el sistema.

### 🎨 Mejoras Frontend (`templates/index.html`)

#### Timeout de comunicación

* `loadIntegridad()` incorpora ahora `AbortController`.
* Se establece un tiempo máximo de espera de 20 segundos para la llamada al backend.
* Si el análisis no finaliza en ese periodo, se muestra:

  > "⏱ Tiempo de espera agotado"
* Se evita que la interfaz permanezca bloqueada indefinidamente.

#### Nuevos indicadores visuales

* Añadido bloque específico para mostrar incidencias de:

  * **Compradores sin móvil registrado**

#### Información de auditoría

* El resumen de integridad muestra ahora la hora exacta de ejecución del análisis.
* Formato:

  > "Analizado a las HH:MM:SS"

### ✅ Resultado

* Eliminados los bloqueos indefinidos durante el análisis de integridad.
* Rendimiento estable independientemente del volumen de hoteles y compradores.
* Protección frente a consultas lentas o bloqueadas.
* Mejor visibilidad de incidencias relacionadas con teléfonos móviles de compradores.
* Mejor experiencia de usuario gracias a los timeouts y mensajes informativos.


## v11.7.2 — 15 junio 2026

### 🔧 Mejora de UX — Navegación guiada por permisos

#### Sidebar unificada para todos los usuarios

* Todos los elementos del menú lateral pasan a ser visibles para cualquier usuario.
* Eliminados los `style="display:none"` utilizados para ocultar opciones según el rol.
* Cada elemento incorpora ahora un atributo `data-roles` que define explícitamente los perfiles autorizados.
* Los accesos del menú utilizan `showViewGuarded()` en lugar de `showView()` para validar permisos antes de navegar.

#### Indicadores visuales de acceso restringido

* Añadida la clase CSS `.sb-item.sb-locked`.
* Las secciones no disponibles para el usuario actual se muestran atenuadas (45% de opacidad) y con cursor `not-allowed`.
* Se incorpora automáticamente el icono 🔒 para identificar visualmente los accesos restringidos.

#### Nuevo sistema de aviso de acceso

* Incorporado el componente flotante `#sb-access-toast`.
* Cuando un usuario intenta acceder a una sección no autorizada, se muestra un aviso durante 3,5 segundos indicando los perfiles con acceso permitido.
* El sistema evita la navegación y proporciona una explicación inmediata del motivo de la restricción.

#### Nuevas funciones JavaScript

* **`_applySidebarRoleStyles()`**

  * Recorre todos los elementos del menú.
  * Compara el rol del usuario con los permisos definidos en `data-roles`.
  * Añade o elimina dinámicamente la clase `sb-locked` y el icono de bloqueo.

* **`showViewGuarded(view, el)`**

  * Intercepta los clics sobre el menú lateral.
  * Si el usuario dispone de permisos, ejecuta `showView()`.
  * Si no dispone de permisos, bloquea la navegación y muestra el aviso correspondiente.

* **`_showSbAccessToast(view, allowedRoles)`**

  * Genera mensajes informativos contextualizados.
  * Ejemplo:

    > "La sección Alertas no está disponible para tu perfil. Acceso permitido a: 👑 Administrador, 🛒 Compras."

#### Matriz de permisos visible para el usuario

| Sección            | Hotel | Compras | Admin |
| ------------------ | :---: | :-----: | :---: |
| Dashboard          |   ✅   |    ✅    |   ✅   |
| Pedidos            |   ✅   |    ✅    |   ✅   |
| Alertas            |   🔒  |    ✅    |   ✅   |
| Proveedores        |   ✅   |    ✅    |   ✅   |
| Pedidos eliminados |   🔒  |    ✅    |   ✅   |
| Techo de gastos    |   🔒  |    ✅    |   ✅   |
| Familias artículos |   🔒  |    🔒   |   ✅   |
| Usuarios           |   🔒  |    🔒   |   ✅   |
| Integridad         |   🔒  |    🔒   |   ✅   |
| Config. alertas    |   🔒  |    🔒   |   ✅   |

### ✅ Resultado

* Los usuarios conocen todas las funcionalidades existentes en la plataforma, aunque no tengan acceso a ellas.
* Se elimina la sensación de "menús desaparecidos" según el rol.
* La navegación resulta más intuitiva y transparente.
* Los permisos continúan aplicándose de forma segura en el frontend antes de acceder a cada sección.


## v11.7.0 — 15 junio 2026

### 🔧 Mejoras — Visibilidad de pedidos y adjuntos para rol Hotel

#### Pedidos DALI / SAP visibles para Hotel

* Modificada la función `_applyHotelRolePedidoModal()` para que los usuarios con rol **hotel** puedan visualizar el campo **Nº Pedido (DALI/SAP)** dentro del modal de pedidos.
* El grupo que contiene `#p-pedido-num` deja de ocultarse durante la adaptación de la interfaz para este rol.

#### Sección "Referencias DALI / SAP" visible

* Ajustada la lógica de ocultación de `.form-section`.
* Ahora se mantiene visible la sección **"Referencias DALI / SAP"** para usuarios de hotel, ocultándose únicamente el resto de secciones no permitidas.

#### Campo Nº Pedido protegido

* El campo `#p-pedido-num` pasa a mostrarse en modo **solo lectura (`readOnly`)** para evitar modificaciones por parte del usuario de hotel.
* Se aplica estilo visual con fondo gris para indicar claramente que el dato es informativo.

#### Adjuntos del pedido visibles

* El contenedor `#adj-pedido-list` deja de ocultarse para el rol hotel.
* Los usuarios pueden consultar los documentos asociados al pedido DALI/SAP.
* Se oculta el botón **📎 Adjuntar doc. / correo** (`lbl-pedido-doc`) para impedir nuevas cargas.

#### Protección de documentos

* Tras renderizar los adjuntos mediante `cargarAdjuntos()`, se ocultan los botones `.adj-del` correspondientes a los documentos del pedido.
* El usuario hotel puede visualizar los archivos, pero no eliminarlos.

#### Restauración para el resto de roles

* En el bloque `else` de `_applyHotelRolePedidoModal()` se restauran las propiedades originales del campo:

  * `readOnly = false`
  * color de fondo original
  * color de texto original

### ✅ Resultado

Los usuarios con rol **Hotel** pueden ahora consultar:

* Número de pedido DALI/SAP.
* Documentación adjunta al pedido.

Manteniendo las restricciones de edición, carga y eliminación de documentos.

## v11.6.8 — 15 junio 2026
### 🐛 Fix — Flujo alta de usuario (Fase 1 / Fase 2)
- **Fix: `movil` no se guardaba en `solicitudes_acceso`**: el campo `movil` recogido en Fase 1 no se insertaba en la tabla (faltaba en el `INSERT`). Añadida migración `ALTER TABLE solicitudes_acceso ADD COLUMN IF NOT EXISTS movil TEXT` y corregido el `INSERT`.
- **Fix: `movil` no se transfería al usuario nuevo**: al aprobar la solicitud, el `INSERT INTO usuarios` no incluía el campo `movil`. Ahora se copia directamente desde la solicitud.
- **Fix: rol incorrecto al crear usuario**: el usuario se creaba con `rol='user'` (legacy). Ahora se crea con `rol='compras'` como valor predeterminado.
- **Mejora UX — modal de edición automático al aprobar**: tras aprobar una solicitud en Fase 2, se abre automáticamente el modal de edición del usuario recién creado (con nombre, email, móvil y hoteles ya cargados) para que el administrador asigne el rol definitivo sin pasos adicionales. El título del modal indica visualmente la acción pendiente.

## v11.6.6 — 03 junio 2026
### 🐛 Correcciones críticas — Techo de Gastos y Alertas
- **Fix crítico — `get_config()` a nivel de módulo**: se eliminaron tres asignaciones `get_config()[...] = ...` que se ejecutaban al importar la aplicación, antes de que Flask tuviera contexto de BD. Esto corrompía la caché de configuración y hacía que `_check_techo` usara valores incorrectos o fallara silenciosamente en el arranque de Render.
- **Fix crítico — f-strings con comillas dobles anidadas**: corregidas 4 f-strings en `_check_techo` y en el job de alertas mensuales que usaban `get_config()["clave"]` dentro de `f"..."`. Esta sintaxis solo es válida en Python ≥ 3.12; en Python 3.11 (Render) causa `SyntaxError` que desactiva silenciosamente la validación del techo.
- **Fix frontend — `loadTechoAlertas` siempre se ejecutaba**: corregido un `if` sin llaves en `showView()` que hacía que `loadTechoAlertas()` se llamara en **todas** las navegaciones de vista, no solo en `alertas`. Esto provocaba peticiones 403 para el rol `hotel` que rompían la cadena de inicialización del dashboard.
- **Fix frontend — rol `hotel` llamaba a `/api/techo/resumen`**: añadida guardia `if (G.rol === 'hotel') return` en `loadTecho()`, `loadTechoAlertas()`, `loadStats()` y `updateAlertBadge()`. El endpoint devuelve 403 para este rol, lo que lanzaba excepciones no controladas que impedían renderizar el dashboard correctamente a los usuarios de hotel.

## v11.6.4 — 03 junio 2026
### 🔧 Mejoras
- Incorporado fechas en las entregas parciales y totales.

## v11.6.2 — 02 junio 2026
### 🔧 Mejoras
- Incorporado filtro por hotel y fecha para imprimir pedidos.

## v11.6.0 — 01 junio 2026
### 🐛 Fix crítico
- Corregido: el aviso de nueva versión **no aparecía** cuando el usuario tenía la sesión ya abierta y recargaba la página (flujo de restauración de sesión no iniciaba el polling ni capturaba la versión base).
- Corregido: al hacer login, si había versión nueva se guardaba el hash antiguo como referencia, haciendo que el polling nunca detectara cambios posteriores.
- Ahora **ambos flujos** (login nuevo + recarga con sesión activa) capturan `G._appVersion` y arrancan el polling correctamente.

## v11.5.9 — 01 junio 2026

### 🔧 Mejoras
- Detector de nueva versión más rápido: comprueba cada 30 segundos durante los primeros 15 minutos tras cargar la app (antes esperaba 1 minuto completo), ideal para detectar despliegues recientes en Render.
- Corregido caso donde `_appVersion` podía quedar `null` e impedir la detección.

## v11.5.8 — 01 junio 2026

### ✅ Novedades
- Ahora podemos imprimir los pedidos, tramos fechas y estados.
## v11.5.6 — 01 junio 2026

### ✅ Novedades
- Ahora podemos imprimir los pedidos.

---

## v11.5.4 — 01 junio 2026

### ✅ Novedades
- Ahora podemos imprimir los historicos de techo de gastos. Pedidos enviados.

## v11.5.2 — 29 mayo 2026

### ✅ Novedades
- Organización Telegram Administradores.
## v11.5.0 — 29 mayo 2026

### ✅ Novedades
- Limpieza y organizacion codigo.

### ✅ Novedades
- Campo de plazo de entrega en pedidos con cálculo automático de fecha prevista.
- Sistema de alertas de techo por familia de producto.
- Desde el panel de Admin. se pueden establecer plazos para los avisos de todas las alertas.

### 🐛 Correcciones
- Badge de alertas no se actualizaba correctamente al cambiar de vista.
- Importación de proveedores ahora actualiza contactos existentes por código.
- Penel de actualizacion mejorado.

## v11.4.8 — 27 mayo 2026

### ✅ Novedades
- Al detectar una nueva versión en el servidor se muestra una ventana
  con las notas de actualización en lugar de recargar silenciosamente.
- Comprobación automática de nueva versión cada 5 minutos en segundo plano.
- Nuevo endpoint `/api/changelog` que sirve este archivo.

### 🔧 Mejoras
- El botón "Ahora no" cierra el aviso y no vuelve a aparecer hasta la
  siguiente versión distinta.
