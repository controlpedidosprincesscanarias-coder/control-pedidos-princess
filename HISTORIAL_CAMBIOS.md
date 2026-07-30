# Historial de Cambios — Ecosistema Princess Compras (unificado)

> Documento único de seguimiento. Se actualiza cambio a cambio, entrada
> más reciente arriba. Componentes: **Organizador** (main_agenda,
> desktop), **Control Pedidos** (backend Flask principal), **Chat**
> (backend Flask/SocketIO independiente), **Infra** (Render /
> Cloudflare / GitHub Actions, no es código de la app).

---

## 2026-07-30

### [Control Pedidos] v12.22.2 — Reclamación seguía sin dispararse pese al fix anterior
- **Probado tras desplegar v12.20.8:** borrado el registro de
  `telegram_auto` de hoy para un pedido concreto (13549) en
  `whatsapp_log`, esperado, repetida la consulta — seguía sin
  aparecer ninguna reclamación.
- **Causa real:** el bloque de reclamación estaba DESPUÉS de la
  lógica de "¿toca reenviar el Telegram interno hoy?" (primer aviso /
  umbral crítico / ciclo de N días desde el ÚLTIMO envío, sea de hoy
  o de cualquier día anterior). Si el ciclo interno decía "todavía no
  toca", el `continue` de esa rama saltaba también la reclamación —
  borrar solo el registro de HOY no lo arregla, porque el ciclo mira
  la última notificación en general, no solo la de hoy.
- **Corregido:** el bloque de reclamación se movió para evaluarse
  ANTES de esa lógica de ciclo, en los dos caminos (con plazo y
  estándar), con su propia deduplicación diaria — independiente de
  si el aviso interno de Telegram está en su turno de reenvío.
  Eliminado el bloque duplicado que había quedado de v12.20.8.
- Badge de versión del sidebar actualizado a "V 12.22.2".


- **Hallazgo de paso:** la consulta de verificación que se venía usando
  (`emails_log WHERE tipo='reclamacion_proveedor_auto'`) nunca iba a
  devolver filas — la reclamación automática registra en
  `whatsapp_log`, no en `emails_log` (esa tabla es la que usa el envío
  MANUAL). Consulta correcta documentada en el CHANGELOG.
- Nuevo campo `reclamacion_auto` en el resumen de notificación de cada
  alerta; badge naranja "🤖 Reclamado auto hace Xd" en el panel
  (separado de la notificación normal) y en la vista de impresión.
- Nueva `_ya_reclamado_hoy_manual()`: si ya se mandó una reclamación
  manual hoy, la automática se omite ese día — centralizado dentro de
  `_encolar_reclamacion_proveedor_auto()`, cubre los dos caminos sin
  tocarlos por separado. No se bloqueó la dirección contraria (manual
  después de automática) — el indicador visual ya es suficiente aviso.
- Badge de versión del sidebar actualizado a "V 12.22.0".

### [Control Pedidos] v12.20.8 — Reclamación automática no se disparaba en la práctica
- **Seguimiento del 29/07:** confirmado con consultas reales
  (`/api/emails-sistema-pendientes` → `[]`, `emails_log WHERE
  tipo='reclamacion_proveedor_auto'` → 0 filas) que nunca se había
  disparado ninguna reclamación pese a llevar la casilla activada y
  36 alertas urgentes en el panel.
- **Causa encontrada:** `_job_alertas_diarias_inner()` clasifica los
  pedidos en dos caminos — (1) con `plazo_entrega_dias` informado por
  el proveedor, (2) estándar (umbrales generales de Config Alertas).
  La reclamación automática solo estaba conectada al camino (1); casi
  ningún pedido real tiene ese campo relleno, así que caen siempre en
  el (2), donde nunca se llamaba.
- **Aclarado con el usuario:** el panel "Plazo de entrega proveedor"
  ajusta los umbrales solo cuando el pedido trae un plazo propio; si
  no lo trae, deben cumplirse los plazos generales igualmente — la
  reclamación debía aplicar en ambos caminos.
- **Corregido:** añadido el mismo bloque de reclamación (mismo
  gating: activa, `nivel=="urgente"`, no notificado hoy) también al
  camino estándar, justo después de `_enviar_telegram_compradores()`.
  El filtro de estado (`ENVIADO AL PROVEEDOR`/`ENTREGA PARCIAL`) ya lo
  hace internamente `_encolar_reclamacion_proveedor_auto()`, así que
  no hizo falta añadirlo aparte.
- Badge de versión del sidebar actualizado a "V 12.20.8".
- **Pendiente:** confirmar en el próximo ciclo del job (corre cada
  minuto en horario 07-16h) que aparecen filas nuevas en `emails_log`
  con `tipo='reclamacion_proveedor_auto'`.

### [Organizador] v4.14.2 — Chat: fecha en mensajes, botón adjuntar más grande, limpiar chat
- `app/ui/chat_bubbles.py` — nueva `fecha_hora_local()` (formato
  `DD/MM HH:MM`), usada en vez de `hora_local()` en las dos ventanas;
  el ancho de burbuja ya se recalculaba dinámicamente, no hizo falta
  tocar nada más de layout.
- `app/ui/ventana_chat.py` — botón "📎" ensanchado; nuevo botón
  "🧹 Limpiar chat" junto al título de la conversación, con
  confirmación, que solo vacía la vista local (no borra nada del
  servidor).
- `app/ui/chat_popup.py` — botón "📎" ensanchado. Sin botón de
  limpiar — solo se pidió para la ventana principal.


- **Reporte inicial:** popups "[URGENTE] Pedido #13537 · Maspalomas &
  Tabaiba Princess" con un número que no aparecía en ningún listado
  filtrado por ese hotel — sospecha de alerta cruzada entre hoteles.
- **Investigado a fondo, sin acceso a la BD en vivo:** identificados
  tres numeraciones distintas coexistiendo en la misma fila —
  `norden` ("Nº" del panel, se reinicia cada año,
  `SELECT MAX(norden) WHERE EXTRACT(YEAR...)`), `pedido_num`
  ("Pedido DALI/SAP", externo), e `id` (clave primaria real, nunca se
  reinicia, incluye pedidos de años anteriores y borrados). El popup
  usaba `id` en el título — de ahí el número "irreconocible".
- **Confirmado con datos reales del usuario** (no solo teoría de
  código): captura de la pestaña Network del navegador mostrando
  `GET /api/pedidos/13537` al editar la fila correcta — el pedido
  era el correcto, del hotel correcto. Sin fallo de seguridad ni de
  segmentación de datos.
- **Corregido igualmente el problema real de fondo (claridad de UI)**
  que motivó el reporte: título del popup cambiado de `Pedido #{id}`
  a `Pedido SAP {pedido_num}` (o `Nº{norden}` si no hay SAP), mismo
  criterio que ya usaba el cuerpo del mensaje de Telegram. Corregido
  en los dos sitios donde se genera el título: backend
  (`app.py::_enviar_telegram_compradores`, cola push) y escritorio
  (`pedidos_agenda_bridge.py::_aviso_para_popup`, polling).
- Badge de versión del sidebar actualizado a "V 12.20.6".

### [Control Pedidos] v12.20.4 — Quitado el bloque de Telegram de la solicitud (fase 1)
- `templates/index.html` — eliminado el bloque promocional de Telegram
  (icono, texto, botones "Descargar para PC" / "Descargar para
  móvil") que aparecía en `#sol-panel-fase1`, entre el teléfono y la
  selección de hoteles. No aportaba nada útil en ese punto — quien
  pide acceso todavía no tiene cuenta; esa info ya vive en el manual,
  que se entrega tras crear la cuenta.
- Revisada la fase 2 ("Verificación PC") y el resto del wizard — sin
  ninguna otra mención a Telegram, no hizo falta tocar nada más.
- Badge de versión del sidebar actualizado a "V 12.20.4".

### [Control Pedidos] Reclamación automática al proveedor — revisada
- **Confirmado que `activar_reclamacion_proveedor_auto` estaba
  desactivado** (captura del panel de Configuración de Alertas, casilla
  "Enviar reclamación automática por email al proveedor cuando vence
  el plazo" sin marcar) — aclarado que esto es un sistema distinto de
  las alertas internas "Email + Telegram" visibles en el listado de
  Alertas (esas sí estaban activas; la reclamación al proveedor no).
- **Activada por el usuario hoy** — queda en seguimiento para
  confirmar que se están encolando reclamaciones reales a proveedores
  en los próximos pedidos que lleguen a nivel `urgente` (verificable
  en `emails_log` / `bridge_notificaciones` filtrando por
  `tipo='reclamacion_proveedor_auto'`).

### [Control Pedidos] Backups — consulta sobre moverlos a la nube
- **Descartado GitHub como repositorio git normal** para los backups
  (archivos grandes y cambiantes, límite de 100MB/archivo sin Git
  LFS, el repo crecería sin parar).
- **Opción viable identificada:** un **segundo proyecto Supabase
  gratuito dedicado solo a backups** — el plan Free permite 2
  proyectos activos por cuenta, cada uno con su propia cuota
  independiente (500MB BD + 1GB storage + 5GB egress), sin competir
  con la cuota del proyecto principal. Ya se usa 1 de los 2 huecos
  gratis (`control_pedidos`), queda margen para 1 más. Único cuidado:
  los proyectos Free se pausan tras 7 días de inactividad — no
  debería afectar dado que hay una tarea diaria de backup.
- **Decisión: por ahora se mantiene tal cual, en la carpeta de red
  local** (vía `restore_agent.py`) — la consulta fue informativa, sin
  cambios de código. Queda documentada la opción para retomarla más
  adelante.

### [Organizador] v4.12.8 — Acceso local mientras se aprueba el alta
- `main_agenda.py` (`_modo_alta` → `_crear_acceso`) — tras enviar la
  solicitud de acceso, se precargan en "👤 Mi Usuario": nombre a
  mostrar (nombre + primer apellido) y el usuario de login del bridge
  (= usuario de Windows), dejando la contraseña vacía a propósito.
- `app/services/admin_auth.py` (`verificar_acceso`) — nuevo caso: si
  el bridge_user ya coincide con el usuario de Windows pero no hay
  contraseña bridge guardada, la próxima contraseña que se escriba en
  el diálogo de Acceso Administración se toma como la elegida por el
  usuario — dando acceso local inmediato al panel (mínimo 4
  caracteres), **sin** validarla nunca contra Control de Pedidos.
- **Efecto:** el usuario tiene control de su Organizador (panel Admin,
  Mi Usuario) desde el minuto uno, independientemente de cuándo se
  apruebe el acceso real — pero el chat y los avisos de Control de
  Pedidos siguen bloqueados hasta que llega la cuenta real y el
  usuario sustituye la contraseña provisional por la definitiva en
  "Mi Usuario".
- Sin cambios en el resto de `verificar_acceso()` (online, fallback
  con hash propio, bloqueo tras 3 intentos) — el caso nuevo se añade
  como comprobación adicional antes del intento online.

### [Organizador] v4.12.6 — Chat rediseñado (burbujas, copiar, hora)
- **Framework:** evaluado Flet / PySide/PyQt frente a seguir con
  ttkbootstrap — descartados ambos: `main.spec` excluye explícitamente
  `PyQt5`, `PyQt6` y `wx` del build, y ttkbootstrap ya está integrado
  en 9 archivos de la UI. Se logra el rediseño dentro del mismo
  framework, sin reescribir la app.
- **Nuevo módulo `app/ui/chat_bubbles.py`** — widget `BubbleList`
  compartido entre `ventana_chat.py` y `chat_popup.py` (antes cada
  ventana mantenía su propia implementación casi idéntica con
  `tk.Text` y tags de color). Burbujas de verdad: rectángulos
  redondeados en `Canvas`, ajuste de línea por medición real de
  fuente, scroll suave con la rueda, y `hora_local()` (convierte
  `creado_en` UTC a hora local, formato `HH:MM`).
- **Copiar mensajes:** clic derecho sobre cualquier burbuja → "📋
  Copiar mensaje" — copia el texto completo al portapapeles (un
  Canvas no tiene selección nativa de texto como un `Text`).
- **`chat_popup.py`:** reescrito para usar `BubbleList`. De paso, se
  corrigió con el patrón correcto (fila de escribir empaquetada
  primero, `side="bottom"`) el mismo problema de layout que ya se
  arregló ayer en `ventana_chat.py` — ya no hace falta el `height=16`
  fijo del ANTI-REGRESIÓN del 21/07. `_cargar()` ahora ordena los
  mensajes por `creado_en` antes de recortar a los últimos 3 y
  pintarlos, en vez de confiar en el orden de la API — el más
  reciente siempre queda abajo, justo encima de la caja de escribir.
- **`ventana_chat.py`:** `txt_mensajes` sustituido por `msgs`
  (`BubbleList`); `_cargar_historial()` ordena igual por `creado_en`.
- **Compatibilidad:** `services/chat_client.py` sin tocar — es un
  cambio de presentación puro, toda la lógica de red/sockets/canales
  sigue igual.
- **Sin poder probar en entorno gráfico real** (sin Windows/Tkinter
  visual aquí) — todo compila (`py_compile`) sin errores, pero
  recomendado probar en local el ajuste de línea con mensajes largos
  y el scroll con la rueda antes de darlo por definitivo.

---

## 2026-07-27

### [Control Pedidos] + [Organizador] v12.20.2 / v4.12.4 — Solicitud de acceso en un solo paso
- **Verificado en producción el 28/07/2026**: probado con `fetch()`
  desde consola del navegador (solicitud #13) — cuenta creada,
  aprobada con rol y hoteles asignados; email de credenciales al
  usuario y email de aviso "solicitud lista para aprobar" a admins,
  ambos despachados correctamente por EmailJS (confirmados por
  capturas de bandeja de entrada real).
- Versión de backend fijada en **v12.20.2** (antes v12.20.0), con
  entrada añadida al `CHANGELOG.md` del repo `control-pedidos-princess`;
  de paso se cerró la advertencia "pendiente de aplicar en producción"
  que quedaba abierta en la entrada de v12.20.0 (los endpoints de
  bridge del login de Admin, confirmados desplegados hoy también).
- Pendiente: probar el lado del Organizador de escritorio (v4.12.4)
  en un PC real sin cuenta previa, de punta a punta.
- `templates/index.html` — actualizado el badge visual del sidebar de
  "V 12.20.0" a "V 12.20.2" (texto literal, sin relación con el hash
  MD5 de `/api/version`, que solo sirve para caché del navegador —
  ese cambia solo con cualquier edición del HTML).

### [Control Pedidos] + [Organizador] v4.12.4 — Solicitud de acceso en un solo paso
- **Backend** (`app.py`) — nuevo endpoint `POST /api/solicitar-usuario/directo`,
  para uso exclusivo del Organizador (que ya conoce el usuario de
  Windows, a diferencia de un navegador). Fusiona fase 1 (datos
  personales) + fase 2 (verificación) en una sola llamada: valida los
  6 campos, comprueba que el usuario de Windows no tenga ya cuenta
  activa (mismo check que la fase 2 real), e inserta la solicitud
  directamente con `estado='completada'` — sin token ni email
  intermedio — cayendo en la misma cola de aprobación del panel admin
  sin tocar ese panel para nada. Notifica por Telegram y encola email
  a admins (mismo mecanismo fiable de `_encolar_email_sistema` que ya
  usa la fase 1, en vez de depender de EmailJS en un navegador que
  aquí no existe). El envío de la contraseña al usuario sigue
  pasando exactamente igual que hoy, al aprobar la solicitud — este
  endpoint no toca esa parte.
- **Desktop** (`app/services/admin_auth.py`, `main_agenda.py`) — el
  formulario de "Crear acceso" del panel Admin pasa de pedir
  "nombre a mostrar + contraseña + repetir" (que creaba un acceso
  local propio vía Telegram sin seguimiento) a pedir los mismos 5
  campos que la fase 1 web (nombre, apellidos, correo, móvil,
  hoteles — Listbox de selección múltiple), llamando a la nueva
  función `solicitar_alta_directa()`. **Cambio de comportamiento
  importante:** ya no se crea ningún acceso local ni contraseña
  propia al solicitar — hay que esperar a que un admin apruebe y
  llegue el correo con las credenciales, igual que en la web.
  Diálogo ensanchado de 460 a 500px.
- Decisión explícita del usuario: se acepta perder la "prueba de
  propiedad del email" que aportaba el token/email intermedio de la
  fase 2 web, porque el origen aquí es la app interna instalada en
  el equipo del solicitante, no un navegador sin autenticar.
- No se borró el código viejo (`registrar_usuario_nuevo`,
  `solicitar_alta_plataforma`, endpoint `/api/bridge/solicitar-alta`)
  por si algo más lo referenciaba — queda sin usar desde la UI.

### [Organizador] v4.12.2 — Corrección
- `app/services/chat_client.py` — `_get_rest()`, `_post_rest()` y
  `conectar()` (socket) ahora reintentan `login()` una vez, solas,
  ante un `401` o un fallo de autenticación en el handshake, y
  repiten la petición/conexión original con la cookie nueva. Mismo
  patrón que ya usaba `pedidos_agenda_bridge.py`. Corrige el
  incidente de hoy: tras un cambio de `SECRET_KEY` en el backend, el
  chat se quedaba con una cookie muerta hasta cerrar y reabrir el
  Organizador entero a mano.

### [Manual] Manual de Usuario actualizado a v4.12.0 — cerrado
- Reescrita por completo la sección "Acceso al Panel ADMIN": fuera el
  usuario/contraseña fijo (`ADMIN` / `Princess2026`), documentado el
  flujo real (usuario de Windows autorrelleno, validación online,
  alta con aviso a un admin, respaldo offline, bloqueo de 5 min).
- Añadida la subsección "Credenciales de Control de Pedidos (chat y
  avisos)" dentro de 5.2 Gestión de Usuarios, documentando los campos
  de "Mi Usuario → Control de Pedidos — credenciales bridge".
- Corregida una referencia residual al usuario/contraseña viejo que
  quedó en la tabla de "Resolución de Incidencias Comunes".
- Revisado el resto del documento en busca de más referencias sueltas
  al sistema viejo — no queda ninguna.
- Añadida una **Guía Rápida** (2 páginas) entre la portada y el
  índice — accesos principales, cómo abrir/configurar botones,
  avisos, calendario, chat, Mi Usuario, copias de seguridad, Telegram
  e incidencias frecuentes. Con estilos propios (no usa los mismos
  `Ttulo1`/`Ttulo2` que el resto), para no meterle entradas nuevas al
  índice automático.
- Portada actualizada a v4.12.0. La sección "Chat Interno" (7.6) no
  necesitó cambios — ya documentaba grupos, imágenes/adjuntos y
  burbuja flotante hasta v4.10.0.
- **Manual dado por finalizado.**

### [Organizador] v4.10.8 — Corrección
- `app/services/admin_auth.py` — `verificar_acceso()` reordenada:
  ahora comprueba primero en LOCAL (registro propio de admin_auth y,
  si no coincide, las credenciales de "Mi Usuario" / bridge) antes de
  intentar conectar con Control de Pedidos. Si hay coincidencia local,
  se acepta el acceso sin tocar la red — evita esperas de conexión
  innecesarias con el backend caído. Si no coincide ninguna, cae al
  intento online como fuente de verdad, igual que antes.
- `main_agenda.py` — `_ventana_login_admin()`: la ventana de "Acceso
  Administración" no se redimensionaba tras aparecer el mensaje de
  error o el aviso de "sin conexión" (ventana fija, alto calculado una
  sola vez) — se recalcula ahora en ambos casos.
- `pedidos_agenda_bridge.py` (`_mostrar_error_bridge`) y
  `app/services/update_service.py` (diálogo de GitHub inaccesible):
  añadido auto-cierre a los 2 minutos sin interacción — mismo patrón
  que el auto-cierre de 5 min ya existente en "Nueva versión
  disponible" (v4.10.3).

### [Infra] Migración de `control_pedidos_chat` a cuenta Render nueva
- **Motivo:** `control-pedidos-chat` y `control-pedidos-princess`
  agotaron las 750h gratis del workspace de Render en julio (ambos
  mantenidos despiertos 24/7 vía UptimeRobot, compitiendo por el mismo
  pool de horas) → suspendidos por Render hasta el reset del día 1.
- Nuevo Web Service `control-pedidos-chat` desplegado en cuenta Render
  distinta (registro nuevo), región Frankfurt. Variables de entorno:
  `SECRET_KEY` y `DATABASE_URL` copiadas del servicio principal
  (`control-pedidos-princess`); `CHAT_DATABASE_URL`, `SUPABASE_URL`,
  `SUPABASE_SERVICE_KEY` copiadas del chat viejo. Start command
  `gunicorn -k eventlet -w 1 app:app` (Flask-SocketIO, no admite más
  workers). URL asignada: `control-pedidos-chat-f4m9.onrender.com`.
- Verificado `/ping` → `OK` y `Auto-migración del chat OK` en logs.
- Sustituido UptimeRobot por workflow de GitHub Actions
  (`.github/workflows/keep-alive-chat.yml`, repo
  `controlpedidosprincesscanarias-coder/control-pedidos-chat`): cron
  `*/10 5-16 * * 1-5` (05:00–16:50 UTC = 06:00–18:00 hora Canarias en
  verano; **hay que pasar a `6-17` en horario de invierno**, UTC+0).
  Consumo estimado ≈260h/mes, muy por debajo del límite de 750h.
  Probado con `workflow_dispatch` manual → OK.
- Worker de Cloudflare `proxy-chat.controlpedidosprincess-canarias.workers.dev`
  reapuntado (`ORIGIN` en `worker.js`) al nuevo servicio. Publicado
  ("Implementar"). No hizo falta tocar `chat_client.py` del
  Organizador — ya usaba la URL del Worker, no la de Render directa.
### [Infra] Migración de `control_pedidos_princess` a cuenta Render nueva (adelantada)
- **Motivo:** aunque el plan era esperar al reset del 1 de agosto,
  problemas organizativos de fin de mes obligaron a adelantar la
  migración — mismo procedimiento que con el chat.
- **Hallazgo:** la `GUIA_DESPLIEGUE.md` interna estaba desactualizada.
  Además de `DATABASE_URL`/`SECRET_KEY`/`EMAILS_INTERNOS`, el `app.py`
  actual (v12.19.1) también necesita `SUPABASE_URL`,
  `SUPABASE_SERVICE_ROLE_KEY` (⚠️ nombre distinto al
  `SUPABASE_SERVICE_KEY` del chat — proyecto Supabase distinto),
  `SUPABASE_STORAGE_BUCKET` (opcional, default `adjuntos-cerrados`) y
  `TELEGRAM_BOT_TOKEN`. Sin este chequeo, la migración se habría hecho
  sin Telegram ni adjuntos, sin ningún error visible hasta que alguien
  los echara en falta.
- Nuevo Web Service en cuenta Render nueva, región Frankfurt, start
  command `gunicorn -w 2 app:app` (este SÍ admite varios workers, no
  usa eventlet/websockets como el chat). URL asignada:
  `control-pedidos-princess-1k69.onrender.com`.
- Verificado `/ping` → `OK` y jobs del scheduler
  (`_job_alertas_diarias`, `_job_familia_repetida`,
  `_job_techo_urgente_admins`) ejecutándose sin errores en los logs.
- `keep-alive-princess.yml` actualizado con la nueva URL. Worker de
  Cloudflare `proxy` (el principal, no `proxy-chat`) reapuntado
  (`ORIGIN` en `worker.js`) y publicado.
- **Verificado funcionando end-to-end desde el Organizador**: login
  de Admin online y login del chat (que depende de este servicio para
  autenticar antes de conectar a `CHAT_URL`) — ambos confirmados OK.
- **v12.20.0 desplegada en la cuenta nueva** — incluye los dos
  endpoints de bridge (`/api/bridge/existe`,
  `/api/bridge/solicitar-alta`) que el `CAMBIOS.md` original marcaba
  como "pendiente de aplicar en producción". Confirmados presentes en
  el `app.py` desplegado, compila sin errores. Con esto queda cerrado
  también el pendiente original de la sesión.
- **Cuenta Render original**: **borrada por completo** (no solo el
  servicio, la cuenta entera) — confirmado que solo contenía este
  servicio suspendido antes de eliminarla. Ya no existe. Todo el
  ecosistema Princess Compras vive ahora en dos cuentas Render nuevas
  independientes (una para princesa, otra para el chat), cada una con
  su propio pool de 750h/mes, mantenidas despiertas por GitHub Actions
  en horario laboral en vez de UptimeRobot 24/7.
### [Organizador] Incidente — chat "Error de conexión" tras la migración
- **Síntoma:** tras migrar `control-pedidos-princess`, el chat mostraba
  "Error de conexión" y `401` en `/api/chat/usuarios` y
  `/api/chat/mensajes`, pese a que el login (`/api/bridge/login`)
  devolvía `200`.
- **Descartado por el camino:** cold-start de Render, dominios
  cruzados en la cookie (`chat_client.py` ya reenvía la cookie a mano
  vía `_cookie_header()`, no depende del auto-attach por dominio de
  `requests`), y desajuste de `SECRET_KEY` (se igualó explícitamente
  copiando el valor entre ambos servicios y el fallo persistió).
- **Causa real:** `chat_client.py` solo hace `login()` **una vez, al
  arrancar** el Organizador, y cachea la cookie en memoria durante
  toda la sesión de la app — a diferencia de
  `pedidos_agenda_bridge.py`, que sí reintenta el login solo al
  recibir un `401`. Como el Organizador llevaba abierto desde antes de
  las migraciones/redeploys de hoy, seguía usando una cookie de sesión
  ya inválida sin darse cuenta, y ni reabrir la ventana del chat ni
  reconectarse por escritorio remoto fuerzan un login nuevo (el
  proceso de fondo sigue siendo el mismo).
- **Solución aplicada:** cerrar el Organizador por completo (no solo
  la ventana del Chat) y reabrirlo — fuerza un `login()` nuevo con
  cookie fresca. Confirmado funcionando.
- **Pendiente:** arreglar `chat_client.py` para que reintente el login
  automáticamente tras un `401`, igual que ya hace
  `pedidos_agenda_bridge.py`, y evitar que esto vuelva a pasar tras el
  próximo redeploy del backend.
### [Organizador] v4.12.0 — Corrección
- `app/ui/ventana_chat.py` — corregidos varios bugs de layout con la
  misma causa raíz: `pack()` con tamaños fijos adivinados a mano en
  vez de medir el contenido real.
  1. **Fila de escribir/adjuntar/enviar** desaparecía en ventanas
     justas de alto — estaba empaquetada DESPUÉS del área de mensajes
     (`expand=True`), que se comía todo el hueco. Reordenada para
     empaquetarse primero (`side="bottom"`) y reservar su sitio.
  2. **Diálogo "Nueva conversación"** — mismo patrón (botón/label
     empaquetados después del Listbox expandible). Reordenado igual.
  3. **Ancho del panel lateral y del diálogo "Nueva conversación"** —
     sustituido el ancho fijo adivinado (que se quedaba corto con
     nombres largos como "Jesus Curbelc" o con el propio botón "＋
     Nueva conversación") por una medición real con
     `tkinter.font.Font.measure()` del texto más ancho presente cada
     vez que se refresca la lista o se cargan los usuarios, ajustando
     `paned.sashpos(0, ...)` o `sel.geometry()` en consecuencia (con
     tope máximo, y sin encoger nunca por debajo del mínimo).
- **Revisado `app/ui/chat_popup.py`** (burbuja flotante) por el mismo
  patrón — no necesitó cambios: ventana de tamaño fijo
  (`overrideredirect`, no redimensionable, sin listas de nombres), ya
  protegida desde el 21 de julio con un `height` fijo documentado
  como anti-regresión para este mismo tipo de bug.

### [Infra] Supabase — Security Advisor

- **ERROR corregido:** tabla `public.notificaciones_config` tenía RLS
  desactivado (expuesta sin filtro vía API REST de PostgREST). Se
  activó con `ALTER TABLE public.notificaciones_config ENABLE ROW
  LEVEL SECURITY;`.
- **29 avisos de nivel INFO restantes** ("RLS enabled, no policy") en
  el resto de tablas del proyecto de `control_pedidos_princess` — no
  requieren acción: la app se conecta directo a Postgres vía
  `psycopg2`/`DATABASE_URL`, no usa la API REST de Supabase, así que
  RLS sin políticas bloquea el acceso externo por API sin afectar al
  funcionamiento normal de la app. Security Advisor queda en 0
  errores, 0 warnings.
- **Aparte, sin relación con lo anterior:** el mismo proyecto Supabase
  entró en grace period por exceso de cuota de Egress del ciclo
  anterior (hasta el 9 de agosto) — uso actual muy por debajo de
  cuota, a vigilar sin acción por ahora.

- **Estado a 2026-07-27, cierre de la migración: sin pendientes.**
  Ambos servicios migrados, verificados end-to-end, cuenta vieja
  eliminada, UptimeRobot desmontado, workflows de GitHub Actions
  activos en ambos repos.

---

## Julio 2026 (antes de esta sesión) — main_agenda 4.10.3 / control_pedidos v12.20.0

### [Organizador] Ventana de actualización
- `app/services/update_service.py` — auto-cierre a los 5 minutos si el
  usuario no toca nada (aplica la opción segura: "solo actualizar
  versión"). Cualquier botón (Confirmar/Cancelar) o la X cancela el
  temporizador.

### [Organizador] Festivos y Vacaciones — mismo diseño que Agenda
- `app/ui/festivos.py`, `app/ui/vacaciones.py` — cabecera unificada
  (título único, sin subtítulo), ventana redimensionable en
  horizontal (antes fija), scroll con rueda del ratón, reajuste
  automático de ancho de filas y wraplength al redimensionar — igual
  que "Agenda de Avisos".

### [Organizador] + [Control Pedidos] Login Admin sin hardcode
- `app/services/admin_auth.py` (nuevo módulo) — usuario = usuario de
  Windows (no editable); si existe en Control de Pedidos, valida
  contraseña online en cada intento; si no existe, formulario de alta
  (nombre + contraseña + repetir), guardado local cifrado (Fernet,
  hash+salt PBKDF2 200k iteraciones), notifica a Control de Pedidos
  para alta manual por un admin. Bloqueo de 5 min tras 3 intentos
  fallidos, siempre en local.
- `main_agenda.py` — eliminadas `ADMIN_USER`/`ADMIN_PASSWORD`
  hardcodeadas; `_ventana_login_admin()` reescrita con el flujo de
  arriba.
- `main.spec` / `compilar.bat` / `README.md` — añadida dependencia
  `cryptography` (cifrado Fernet).
- **Control Pedidos** `app.py` — dos endpoints nuevos:
  - `GET /api/bridge/existe?usuario_windows=...` → `{"existe": bool}`
    (solo por username, nunca pide/revela contraseña).
  - `POST /api/bridge/solicitar-alta` `{usuario_windows, nombre}` →
    notifica por Telegram a los admins (reutiliza
    `_notify_solicitud_telegram`). Deliberadamente no recibe la
    contraseña.
- **Pendiente de decidir en su momento** (ver `CAMBIOS.md` original):
  criterio de "existe" en `/api/bridge/existe` (¿incluye inactivos?);
  canal de aviso de alta (Telegram vs email vs tabla de solicitudes);
  si la contraseña de alta debería viajar al servidor o no (se decidió
  que NO, para no duplicar el riesgo de `usuarios.password` en claro).

---

## Convenciones de este historial
- Versionado de Organizador Princess: 3er dígito +2 (0,2,4,6,8) →
  al pasar de 8, 2º dígito +2 y 3º vuelve a 0 (4.10.8→4.12.0) → al
  llegar el 2º a 98, 1er dígito +1 y los otros dos a 0 (4.98.8→5.0.0).
- Cada release de Organizador actualiza `APP_VERSION` en
  `main_agenda.py`, `release_notes_actual.txt` (usuario) y
  `release_notes.md` (técnico) — ver esos ficheros para el detalle
  línea a línea; este historial es el resumen unificado entre
  proyectos.
