# Historial de Cambios — Ecosistema Princess Compras (unificado)

> Documento único de seguimiento. Se actualiza cambio a cambio, entrada
> más reciente arriba. Componentes: **Organizador** (main_agenda,
> desktop), **Control Pedidos** (backend Flask principal), **Chat**
> (backend Flask/SocketIO independiente), **Infra** (Render /
> Cloudflare / GitHub Actions, no es código de la app).

---

## 2026-07-31 (15)

### [Control Pedidos] v12.27.10 — Backup EmailJS bidireccional + reinicio de contador
- El usuario confirmó los datos de v12.27.8 (cuenta 1 activa,
  contador en 8) y aportó una cuenta 2 de backup ya existente (otra
  cuenta EmailJS previa: `service_dwwha2g` / `template_krpvmda` /
  Public Key `WCiU7q8WT1i8AQTbR`), aclarando que el contador debe
  reiniciarse a 0 en cada cambio — "siempre empieza en 1 y termina en
  195".
- `POST /api/emailjs/registrar-envio` corregido: antes solo cambiaba
  1→2 una vez y nunca reiniciaba el contador (seguía subiendo por
  encima de 195 indefinidamente tras el cambio). Ahora:
  - El cambio es bidireccional — calcula `destino = 2 if activa==1
    else 1` y cambia a esa cuenta sea cual sea la activa.
  - El contador se reinicia a `0` en la misma transacción del
    cambio, para que la cuenta recién activada empiece su propio
    ciclo de 1 a 195.
  - Pensado para funcionar como round-robin continuo entre las 2
    cuentas: cuando la segunda también llegue al umbral, lo normal es
    que la primera ya se haya renovado del lado de EmailJS (ciclo
    gratuito mensual), y vuelva a servir de backup.
- Comprobación de Integridad (`_validar_integridad_operativa`)
  generalizada del mismo modo: en vez de asumir siempre "activa=1,
  backup=2", calcula `_otra = 2 if _activa==1 else 1` y evalúa la
  completitud de las credenciales de esa cuenta, sea cual sea.
- Nota del panel Admin → Config Alertas → EmailJS actualizada
  ("rellena ambas cuentas... cambia a la OTRA cuenta... reinicia el
  contador a 0").
- Nota: las credenciales reales de las 2 cuentas ya confirmadas por
  el usuario NO se tocan por migración (viven como datos ya
  existentes en la base de datos de producción, con
  `ON CONFLICT DO NOTHING`) — se rellenan/confirman directamente
  desde el panel de administración ya construido en v12.27.8.
- Badge de versión del sidebar actualizado a "V 12.27.10"; entrada
  añadida en `CHANGELOG.md`.

---

## 2026-07-31 (14)

### [Control Pedidos] v12.27.8 — Backup automático de cuenta EmailJS
- Motivo: a raíz de haberse quedado sin cuota EmailJS (200/mes) a
  mitad de ciclo por exceso de pruebas — se pidió un recuento de
  correos enviados que, al llegar a 195 (5 antes del límite), cambie
  solo las 3 credenciales para que los envíos sigan sin cortarse,
  dejando constancia del cambio en Integridad.
- Nuevas claves en `config_alertas` (grupo `emailjs`, migración
  `ON CONFLICT DO NOTHING`): `emailjs_public_key_1/2`,
  `emailjs_service_id_1/2`, `emailjs_template_id_1/2` (cuenta 1 =
  activa por defecto, inicializada con las credenciales ya en uso en
  producción; cuenta 2 = backup, vacía hasta que el admin la rellene),
  `emailjs_cuenta_activa`, `emailjs_contador`, `emailjs_umbral_cambio`
  (195 por defecto) y `emailjs_cambio_automatico_en`.
- `GET /api/emailjs/config` (sin login, igual que antes con las
  constantes hardcodeadas — el public key ya era público de por sí):
  credenciales de la cuenta activa + contador/umbral, para que el
  frontend inicialice `emailjs.init()` dinámicamente.
- `POST /api/emailjs/registrar-envio` (con login): incrementa el
  contador de forma atómica (`UPDATE ... RETURNING`, sin razas entre
  usuarios concurrentes). Si se alcanza el umbral con la cuenta 1
  activa y la cuenta 2 tiene las 3 credenciales completas, cambia a
  la cuenta 2 y registra la fecha (`pytz Atlantic/Canary`, mismo
  criterio de zona horaria que el resto de la app). Si la cuenta 2 no
  está lista, NO cambia — para no dejar la app sin poder enviar — y
  se marca como aviso urgente en Integridad.
- Frontend: `emailjs.init()` en `<head>` ahora es asíncrono
  (`window._emailjsCfgReady`), cargado desde `/api/emailjs/config` en
  vez de una Public Key fija. Nuevo helper central `enviarEmailJS()`
  que sustituye a las 9 llamadas directas a
  `emailjs.send(EMAILJS_SERVICE_ID, EMAILJS_TEMPLATE_ID, ...)` — tras
  cada envío correcto llama a `/api/emailjs/registrar-envio` y, si el
  backend indica que hubo cambio de cuenta, reinicializa
  `emailjs.init()` con la nueva Public Key sobre la marcha (sin
  recargar la página) para que el resto de envíos de esa misma sesión
  ya usen la cuenta nueva.
- Admin → Config Alertas: nuevo panel especial "📧 EmailJS — cuentas
  y backup automático" (renderizado aparte del bucle genérico
  numero/bool, porque necesita campos de texto) — barra de progreso
  contador/umbral, cuenta activa, y las 3 credenciales de cada una de
  las 2 cuentas en cajas separadas; reutiliza el mismo
  `saveConfigAlertas()` genérico (ya recogía cualquier
  `input[id^="cfg_"]`, sin cambios ahí).
- Admin → Integridad: nueva clave `emailjs` en
  `_validar_integridad_operativa()` con 3 posibles avisos (cambio ya
  realizado / umbral alcanzado sin backup — crítico / cerca del
  umbral sin backup — aviso), y su tarjeta correspondiente en el
  panel visual ("📧 Cuenta EmailJS", gravedad dinámica según el tipo
  de aviso).
- Badge de versión del sidebar actualizado a "V 12.27.8"; entrada
  añadida en `CHANGELOG.md`.

---

## 2026-07-31 (13)

### [Control Pedidos] v12.27.6 — Correos por hotel: invertido el criterio por defecto
- Petición: tras implementar v12.27.4, el usuario pidió invertir el
  planteamiento — que cada contacto nazca con TODOS los hoteles
  marcados (en vez de ninguno = "general" invisible), y que el admin
  desmarque los que no le correspondan. Y que los contactos que ya
  existen en este momento queden marcados así automáticamente, sin
  tener que hacerlo uno por uno a mano.
- Migración automática añadida junto a la de v12.27.4 (misma sección
  del arranque, ejecutada en cada deploy pero solo con efecto la
  primera vez): `INSERT ... SELECT pc.id, h.id FROM
  proveedor_contactos pc CROSS JOIN hoteles h WHERE NOT EXISTS
  (SELECT 1 FROM proveedor_contacto_hoteles WHERE contacto_id=pc.id)`
  — marca todos los hoteles a cada contacto que a día de hoy no tenga
  ninguna fila en `proveedor_contacto_hoteles`, es decir, todos los
  contactos existentes (la función es nueva, nadie ha marcado nada
  todavía). Es idempotente por construcción: un contacto que ya tenga
  al menos una fila (porque se restringió a mano después) queda fuera
  del `NOT EXISTS` y no se vuelve a tocar.
- Frontend (`_pvFillContactoHoteles`): cuando un contacto no tiene
  ninguna restricción guardada (`selected.length === 0` — contacto
  nuevo, o caso residual), las casillas de hoteles se muestran ahora
  TODAS marcadas por defecto, en vez de todas vacías. Si ya tiene una
  selección guardada, se respeta tal cual sin cambios.
- Textos de ayuda actualizados (cabecera "Contactos" y por-fila) para
  reflejar "desmarca los que no le correspondan" en vez de "vacío =
  general".
- Sin cambios en `_get_proveedor_emails_principales()` ni en el
  guardado de contactos — ya guardaban correctamente lo que estuviera
  marcado; solo cambiaba qué se veía marcado por defecto en pantalla,
  y ahora además hay datos reales en BD para los contactos ya
  existentes en vez de depender del fallback implícito.
- Badge de versión del sidebar actualizado a "V 12.27.6"; entrada
  añadida en `CHANGELOG.md`.

---

## 2026-07-31 (12)

### [Control Pedidos] v12.27.4 — Correos específicos por hotel en contactos de proveedor
- Petición: poder asignar en la ficha de un proveedor uno o varios
  hoteles a cada contacto, para que las reclamaciones automáticas
  vayan al contacto responsable del hotel del pedido en concreto (no
  a todos los principales generales del proveedor a la vez),
  manteniendo la copia al comprador de ese hotel (ya existía desde
  antes, sin cambios).
- Nueva tabla `proveedor_contacto_hoteles` (contacto_id, hotel_id, PK
  compuesta, ON DELETE CASCADE en ambos sentidos) — migración
  incremental en `app.py` (CREATE TABLE IF NOT EXISTS) y definición en
  `models.py` para instalaciones nuevas.
- `_get_proveedor_emails_principales(proveedor_id, hotel_id=None)`:
  si se pasa `hotel_id` y hay contactos ★ principal asignados
  específicamente a ese hotel, se usan SOLO esos; si no hay ninguno
  (o no se pasa hotel_id), cae al comportamiento de siempre —
  contactos principales SIN ningún hotel asignado (generales). Un
  contacto sin filas en la tabla nueva sigue siendo general.
- Actualizados los 5 puntos donde se llama a esa función para pasar
  también `pedido.get("hotel_id")` (o el hotel_id calculado en el
  caso de la validación al pasar a ENVIADO AL PROVEEDOR, que antes
  solo se calculaba dentro de un `if` de techo de gastos — ahora se
  calcula siempre que hace falta).
- `_prov_with_contactos()` (listado de proveedores) ahora también
  devuelve `hotel_ids` por contacto (array_agg vía subconsulta
  correlacionada). `create_proveedor()` y `update_proveedor()`
  guardan los `hotel_ids` de cada contacto tras el INSERT (usando el
  id devuelto por `RETURNING id`) — el patrón de "borrar y
  reinsertar todos los contactos" que ya usaba la ficha se mantiene
  igual, y el `ON DELETE CASCADE` limpia solo la tabla nueva.
- Frontend: cada fila de contacto en la ficha de proveedor tiene ahora
  una sección "🏨 Hoteles asignados a este contacto" con checkboxes
  de todos los hoteles (cargados una vez, cacheados en
  `_pvHotelesCache`, vía `/api/maestros`); vacío = general. La tabla
  de listado de proveedores muestra un indicador 🏨 con los códigos
  de hotel cuando un contacto tiene alguno asignado. Añadida nota
  explicativa sobre el comportamiento junto al título "Contactos".
- Badge de versión del sidebar actualizado a "V 12.27.4"; entrada
  añadida en `CHANGELOG.md`.

---

## 2026-07-31 (11)

### [Control Pedidos] v12.27.2 — Correo interno de cambio de estado mejorado
- Petición: el correo interno de cambio de estado (mostrado con
  captura real de un ENTREGADO) llegaba muy básico — se pidió
  redacción más cuidada/profesional, extenderlo también a ENVIADO AL
  PROVEEDOR (antes solo cubierto por el BCC del correo externo, sin
  aviso interno propio), y que indique el nombre del usuario que
  realizó el cambio (dato que nunca debe salir en el correo al
  proveedor).
- `enviar_emails_estado()` ahora acepta `usuario_nombre` — se pasa
  desde `_notificar_cambio_estado()` (cambios manuales, ya recibía
  `usuario_nombre` para Telegram pero no lo pasaba a los emails) y
  desde `create_pedido()` (alta directa en un estado con correo
  interno, usando `session.get("nombre")`). Se añade como línea
  "Realizado por:" en el correo interno (HTML y texto), solo si hay
  nombre disponible.
- Quitada la exclusión de ENVIADO AL PROVEEDOR del bloque de correo
  interno (antes `ESTADOS_EMAIL_INTERNO - ESTADOS_EMAIL_PROVEEDOR`,
  ahora directamente `ESTADOS_EMAIL_INTERNO`, que ya lo incluía) —
  para ese estado ahora se envían DOS correos: el externo al
  proveedor (con BCC a los internos, sin cambios) y este interno
  nuevo, dirigido solo a comprador(es) + usuario(s) hotel.
- Redacción del cuerpo: icono por estado en asunto y cabecera (📤
  enviado al proveedor, 📦 entrega parcial, ✅ entregado, ❌
  cancelado), separador visual (línea de guiones), secciones "📋
  Datos del pedido" y "📦 [histórico de entregas]" cuando aplica, pie
  de aviso automático al final. Aplicado igual en `body_text_i` (el
  que realmente se entrega, ya que EmailJS usa `cuerpo_text ||
  cuerpo_html`) y en `body_html_i`.
- Destinatarios sin cambios — `_todos_internos` ya combinaba
  compradores + usuarios hotel del hotel del pedido (con soporte de
  `email2` desde v12.25.8); simplemente ahora también se usa para
  ENVIADO AL PROVEEDOR.
- Probado con datos de ejemplo (Pedido 23979, TUI Blue Suite Princess)
  reproduciendo el caso de la captura — salida verificada limpia y
  bien estructurada.
- Badge de versión del sidebar actualizado a "V 12.27.2"; entrada
  añadida en `CHANGELOG.md`.

---

## 2026-07-31 (10)

### [Control Pedidos] v12.27.0 — El email de usuario no debe bloquear el guardado
- Corrección sobre v12.25.8: el usuario aclaró que la ficha de usuario
  SÍ debe poder guardarse sin email — la falta de email en
  compradores/admins activos ya se detecta y avisa en Admin →
  Integridad (`_validar_integridad_operativa()`, claves
  `compradores_sin_email` / `admins_sin_email`), así que bloquear el
  guardado era redundante e innecesariamente restrictivo. Además, un
  admin debe poder dejar el email vacío A PROPÓSITO como forma de
  anular el envío de correos a un usuario concreto sin tener que
  desactivar la cuenta entera.
- Quitada la validación "El email es obligatorio" tanto en
  `/api/usuarios` (POST `create_usuario` y PUT `update_usuario`) como
  en `saveUsuario()` del frontend.
- Ficha de usuario: quitado el asterisco de obligatorio del campo
  Email, añadida nota explicando que dejarlo vacío anula los envíos a
  ese usuario y que Integridad lo señalará como aviso informativo si
  corresponde (sin bloquear nada).
- `email2` no se ve afectado por este cambio, sigue opcional sin
  ninguna validación.
- Badge de versión del sidebar actualizado a "V 12.27.0"; entrada
  añadida en `CHANGELOG.md`.

---

## 2026-07-31 (9)

### [Control Pedidos] v12.25.8 — Segundo email opcional por usuario
- Petición: poder asignar en la ficha de usuarios un segundo email
  (opcional, el primero sigue siendo obligatorio), de forma que cuando
  un comprador tenga los 2 asignados, todos los correos que se envíen
  sobre sus hoteles lleguen a ambos — pero que la firma de los correos
  salientes siga usando solo el primero.
- Nueva columna `email2` en `usuarios` (migración `ALTER TABLE ... ADD
  COLUMN IF NOT EXISTS`, más la definición de tabla actualizada en
  `models.py` para instalaciones nuevas).
- Nuevo helper `_emails_usuario(u)` → devuelve `[email]` o `[email,
  email2]` sin duplicados; usado exclusivamente para listas de
  destinatarios, nunca para la firma.
- Actualizados los 6 puntos donde se construían listas de
  destinatarios a partir de compradores para que incluyan `email2`
  cuando exista:
  1. BCC del correo de confirmación de recepción al proveedor
     (`_emails_compradores` en el flujo de cambio de estado)
  2. Destinatarios de `_encolar_aviso_cotizacion_sin_proveedor()`
  3. Destinatarios de `_encolar_aviso_firma_pendiente_auto()`
  4. CC de `_encolar_reclamacion_proveedor_auto()`
  5. TO/CC del endpoint manual `/api/alertas/<id>/email-preview`
  6. CC recalculado en backend de `/api/alertas/<id>/enviar-email`
     (comparando contra el conjunto de direcciones ya en el TO, no
     solo una — el TO puede traer 2 direcciones si el destinatario
     interno tiene email2)
- `_get_compradores_hotel()` y `_get_todos_usuarios_hotel()`
  (compradores) ahora seleccionan también `email2` en su SQL.
- API `/api/usuarios`: `email` obligatorio (validado en POST y PUT,
  error 400 si viene vacío), `email2` opcional; el listado GET
  devuelve también `email2`.
- Frontend: nuevo campo "Email 2 (opcional)" en la ficha de usuario
  con nota explicativa; el email principal se marca como obligatorio
  (`Email *`) con validación también en el propio formulario antes de
  guardar. La tabla de usuarios muestra el segundo email debajo del
  principal cuando existe.
- Badge de versión del sidebar actualizado a "V 12.25.8"; entrada
  añadida en `CHANGELOG.md`.

---

## 2026-07-31 (8)

### [Control Pedidos] v12.25.6 — La firma corporativa se quedó a medias en 2 plantillas
- Reportado con capturas reales de Gmail (carpeta Enviados de
  `controlpedidosprincess.canarias@gmail.com`) tras confirmar v12.25.4
  desplegada: el espaciado ya salía limpio (arreglo de v12.25.4 OK),
  pero la firma de un correo de "Solicitud de cotización" seguía en
  formato antiguo ("Nombre / email · Móvil: xxx"), sin "Dpto. Central
  de Compras Canarias" ni la dirección — el cambio de v12.25.0 no
  había llegado del todo.
- Causa encontrada revisando el código: al aplicar la firma
  corporativa en v12.25.0, el reemplazo masivo (script Python contando
  3 ocurrencias) solo sustituyó el BLOQUE DE VISUALIZACIÓN final
  (quitar "Dpto. Central de Compras Princess en Canarias" / "Princess
  Hotels & Resorts" duplicados antes de `{_firma_contacto}`), pero NO
  tocó la construcción de la variable `_firma_contacto` en sí en 2 de
  las 3 plantillas — solo `_email_template_enviado_proveedor` se
  actualizó a `_firma_comprador_html()` explícitamente en ese momento;
  `_email_template_entrega_parcial` y
  `_email_template_pendiente_cotizacion` conservaban la construcción
  manual antigua (`· Móvil:`), que seguía compilando sin dar ningún
  error — por eso no se detectó hasta ver un correo real.
- Corregido: las 3 plantillas usan ahora
  `_firma_comprador_html(comprador_nombre, comprador_email,
  comprador_movil)` de forma consistente. Verificado con `grep` que no
  queda ningún "· Móvil:" en `app.py`.
- Badge de versión del sidebar actualizado a "V 12.25.6"; entrada
  añadida en `CHANGELOG.md`.

---

## 2026-07-31 (7)

### [Control Pedidos] v12.25.4 — Líneas en blanco duplicadas en correos automáticos
- Reportado con una captura de un correo real de Entrega Parcial (56
  días, Cocina): llegaba con líneas en blanco entre casi cada dato
  (Pedido Nº, Hotel, Departamento, Estado actual...) — "muy
  desorganizado" — pero SIN línea en blanco entre "Días transcurridos"
  y "Observaciones", pista clave para dar con la causa.
- Causa: `_html_a_texto_plano()` (fallback que convierte `body_html` a
  texto plano cuando no hay `cuerpo_text` explícito — reclamación
  automática al proveedor, aviso de firma pendiente, aviso de
  cotización sin proveedor) no neutralizaba los saltos de línea/
  indentación que trae el propio código fuente Python (las plantillas
  son f-strings multilínea) antes de insertar sus propios saltos de
  línea al convertir `<br>`/`</p>` — el resultado eran saltos dobles
  en casi todas partes, salvo en el único `<br>` que estaba en la
  misma línea de código que el texto siguiente (el caso de
  Observaciones, que no tenía el salto de línea "extra" del código
  fuente porque no hay ninguno ahí).
- Corregido: ahora se colapsa TODO el espacio en blanco crudo del HTML
  de entrada a un único espacio antes de insertar los saltos de línea
  con significado (igual que hace un navegador). `</p>`/`</div>`/
  `</h1-6>` → línea en blanco; `<br>`/`</tr>`/`</li>` → salto simple.
  Probado localmente contra un HTML equivalente al del correo real
  reportado — resultado limpio.
- Nota para el usuario: la firma que aparecía en esa misma captura
  (sin "Dpto. Central de Compras Canarias" ni dirección, formato
  "email · Móvil: xxx") es la firma ANTIGUA, de antes de v12.25.0 —
  indica que el `app.py` desplegado en Render en ese momento aún no
  incluía el cambio de firma corporativa; pendiente de confirmar con
  el usuario si ya se ha redesplegado desde entonces.
- Badge de versión del sidebar actualizado a "V 12.25.4"; entrada
  añadida en `CHANGELOG.md`.

---

## 2026-07-31 (6)

### [Control Pedidos] v12.25.2 — Cambio de cuenta EmailJS por agotamiento de cuota
- Motivo: la cuenta EmailJS anterior (Service ID `service_dwwha2g`)
  quedó a 5 peticiones de agotar el límite gratuito de 200/mes, con
  15 días aún por delante hasta el reset del ciclo (14 agosto) —
  muchas pruebas y ajustes de la app consumieron la cuota.
- Se guió al usuario paso a paso para crear una cuenta EmailJS nueva
  e independiente (contador propio desde 0): conectar el mismo Gmail
  `controlpedidosprincess.canarias@gmail.com` como servicio, crear una
  plantilla nueva replicando los campos que la app ya manda en sus
  llamadas `emailjs.send(...)` (destinatarios: `to_email`, `bcc`,
  `reply_to`; contenido: `{{subject}}` y `{{message}}`, con
  `white-space: pre-wrap` para respetar los saltos de línea del texto
  plano), y obtener Public Key / Service ID / Template ID.
- Credenciales actualizadas en `templates/index.html`:
  - Public Key: `WCiU7q8WT1i8AQTbR` → `bxFzHypsIrNqcDh15`
  - Service ID: `service_dwwha2g` → `service_shvrzuv`
  - Template ID: `template_krpvmda` → `template_1zrv4ze`
- La cuenta anterior no se elimina — queda como reserva con su propio
  ciclo de reset.
- Badge de versión del sidebar actualizado a "V 12.25.2"; entrada
  añadida en `CHANGELOG.md`.

---

## 2026-07-31 (5)

### [Control Pedidos] v12.25.0 — Firma corporativa estándar en los correos
- Petición: sustituir la firma de los correos con firma de comprador
  por el formato corporativo que ya se usa en otros correos de la
  empresa (captura de pantalla de una firma real): nombre, "Dpto.
  Central de Compras Canarias", línea en blanco, dirección física
  (Av. Touroperador Tui, s/n — 35100 Maspalomas, Gran Canaria),
  teléfono con prefijo (+34) y email — cambiando nombre/teléfono/
  email por los del comprador correspondiente en cada envío.
- Nuevas funciones compartidas `_firma_comprador_html()` /
  `_firma_comprador_text()` — departamento y dirección fijos; nombre,
  (+34) móvil y email variables según el comprador que firma (se
  omiten sin dejar hueco si falta nombre o móvil).
- Sustituye la firma en los 4 puntos que ya la llevaban: correo de
  confirmación de recepción al proveedor, y las plantillas
  `_email_template_enviado_proveedor`, `_email_template_entrega_parcial`
  y `_email_template_pendiente_cotizacion` (esta última reutilizada
  también por la reclamación automática al proveedor). Se quitan las
  líneas duplicadas "Dpto. Central de Compras Princess en Canarias" /
  "Princess Hotels & Resorts" que había antes de la firma, y se
  mantiene solo "Atentamente," como saludo de cierre.
- Los avisos internos al comprador (firma pendiente, cotización sin
  proveedor) NO llevan firma personal (van como "Mensaje automático
  generado por el sistema") — sin cambios ahí, no aplicaba.
- Badge de versión del sidebar actualizado a "V 12.25.0"; entrada
  añadida en `CHANGELOG.md`.
- Pendiente si se quiere ir más allá: la cabecera de color de esos
  mismos correos sigue diciendo "Dpto. Central de Compras **Princess
  en** Canarias" (ligeramente distinto al texto de la firma nueva,
  "Dpto. Central de Compras Canarias") — no se tocó por no ser parte
  de la firma pedida, pero queda anotado por si se quiere unificar.

---

## 2026-07-31 (4)

### [Control Pedidos] v12.23.8 — Aviso automático al comprador en Pendiente Firma Compras/Hotel
- Petición: que Pendiente Firma Dirección Compras y Pendiente Firma
  Dirección Hotel también avisen automáticamente por email al
  comprador de lo que está pendiente, igual que ya se hizo con
  Pendiente Cotización.
- Se preguntó explícitamente con qué criterio disparar el email, dado
  que estos dos estados tienen el umbral "Urgente" en 0 = nunca por
  defecto (a diferencia de Enviado al Proveedor / Entrega Parcial /
  Pendiente Cotización, donde si tiene sentido). Se decidió: mismo
  criterio que ya usa el Telegram automático para estos dos estados
  (1ª alerta + repetición por ciclo, sin exigir "urgente").
- Nueva función `_encolar_aviso_firma_pendiente_auto()`, llamada desde
  `_job_alertas_diarias_inner()` justo cuando también se envía el
  Telegram automático (mismo disparo, sin ciclo de dedup propio).
  Bajo el mismo interruptor maestro que el resto de avisos
  automáticos por email (`activar_reclamacion_proveedor_auto`) —
  reetiquetado en el panel admin porque ya no es solo "reclamación a
  proveedor" (migración `UPDATE`, no `ON CONFLICT`, porque la fila ya
  existía en producción).
- Reutiliza `_email_template_pendiente_firma()` (antes solo se usaba
  en la propuesta manual del panel) — un único envío con todos los
  compradores del hotel juntos en "Para:". Ajustada la frase de cierre
  ("gestione con Dirección de Compras/Hotel la revisión y firma...")
  para que tenga sentido yendo al comprador, que no es quien firma.
- `_ya_reclamado_hoy_manual()` generalizada con parámetro `tipo`
  (antes fija a `alerta_proveedor`) — ahora también acepta
  `alerta_interno`, para que el aviso automático no duplique un envío
  manual del mismo día hecho desde el panel.
- Badge de versión del sidebar actualizado a "V 12.23.8"; entrada
  añadida en `CHANGELOG.md`.

---

## 2026-07-31 (3)

### [Control Pedidos] v12.23.6 — Empaquetado de los 3 cambios de hoy
- Los tres cambios de hoy (firma con nombre/móvil del comprador,
  reclamación automática extendida a Pendiente Cotización, y aviso al
  comprador cuando Pendiente Cotización no tiene proveedor) se
  liberan juntos como v12.23.6. Badge de versión del sidebar
  (`templates/index.html`) actualizado; entrada añadida en
  `CHANGELOG.md`.
- A partir de ahora: en cada entrega se mantienen sincronizados
  `CHANGELOG.md`, este `HISTORIAL_CAMBIOS.md` y la versión del badge
  en `templates/index.html`; y solo se entregan los archivos
  modificados, indicando la ruta exacta del repo donde colocarlos.

### [Control Pedidos] PENDIENTE COTIZACIÓN sin proveedor asignado — aviso al comprador
- Petición: cuando la reclamación automática de PENDIENTE COTIZACIÓN
  (añadida en el cambio anterior) no encuentra proveedor asignado en el
  pedido, en vez de omitirse en silencio, enviar un correo únicamente
  al/los comprador(es) del hotel indicando que la cotización de la
  solicitud con fecha X sigue pendiente y que no hay proveedor
  asignado hasta la fecha.
- Nueva plantilla `_email_template_cotizacion_sin_proveedor()` (aviso
  interno, mismo estilo que "pendiente de firma": cabecera azul,
  tabla con Pedido Nº / Nº Orden / Hotel / Departamento / "Proveedor:
  Sin proveedor asignado hasta la fecha" / Días en espera /
  Observaciones si las hay).
- Nueva función `_encolar_aviso_cotizacion_sin_proveedor()`: un único
  envío con todos los compradores del hotel juntos en "Para:" (mismo
  patrón que el resto de envíos a varios destinatarios).
- `_encolar_reclamacion_proveedor_auto()` ahora, cuando el pedido está
  en PENDIENTE COTIZACIÓN y no hay ningún email de proveedor
  disponible, delega en la función de arriba en vez de devolver
  `False` sin más. Para ENVIADO AL PROVEEDOR / ENTREGA PARCIAL el
  comportamiento no cambia (siempre se omite si no hay proveedor,
  porque en esos estados el proveedor ya debería estar asignado).
- Reutiliza el mismo tipo de dedup en `whatsapp_log`
  (`reclamacion_proveedor_auto`), así que respeta el mismo ciclo y
  umbral crítico ya configurados en Config Alertas para Pendiente
  Cotización (`cotizacion_ciclo`, `cotizacion_urgente`, `dias_critico`)
  — sin lógica nueva que mantener sincronizada aparte.

---

## 2026-07-31 (2)

### [Control Pedidos] Reclamación automática al proveedor extendida a Pendiente Cotización
- Petición: tras revisar cómo se gestionan los avisos automáticos por
  tiempo transcurrido (Telegram siempre automático; email casi siempre
  manual salvo la reclamación automática, antes limitada a ENVIADO AL
  PROVEEDOR y ENTREGA PARCIAL), extender esa reclamación automática
  también a PENDIENTE COTIZACIÓN.
- `_encolar_reclamacion_proveedor_auto()` ahora acepta también el
  estado PENDIENTE COTIZACIÓN (antes solo ENVIADO AL PROVEEDOR /
  ENTREGA PARCIAL). `_build_alerta_email()` ya tenía plantilla propia
  para este estado (`_email_template_pendiente_cotizacion`), así que
  no requería cambio adicional ahí.
- Nueva clave de configuración `cotizacion_ciclo` (Admin → Config
  Alertas → grupo "💬 Pendiente cotización", default 3 días) —
  antes ese estado no tenía ciclo de repetición (avisaba una sola vez
  al hacerse urgente); ahora, con `activar_reclamacion_proveedor_auto`
  activado (ya lo estaba desde el 29/07), la reclamación al proveedor
  se repetirá cada N días mientras el pedido siga sin cotizar — mismo
  patrón ya usado en los otros estados con ciclo.
- Efecto colateral esperado y coherente con el resto de estados: al
  compartirse la misma clave `ciclo` entre el reenvío de Telegram y el
  de la reclamación por email, el aviso interno por Telegram de
  Pendiente Cotización también pasa de "solo una vez" a repetirse
  cada `cotizacion_ciclo` días — igual que ya ocurre en Enviado al
  Proveedor, Firma Compras, Firma Hotel y Entrega Parcial.
- Migración añadida con `ON CONFLICT (clave) DO NOTHING` para que la
  clave se cree sola en la base de datos de producción ya existente,
  sin tocar nada a mano.

---

## 2026-07-31

### [Control Pedidos] Firma de correos — nombre y móvil del comprador junto al email
- Petición: en todos los correos que se envían con la firma del
  comprador (email en la firma), añadir también su nombre y móvil.
- Afecta a los dos puntos del código donde se compone esa firma:
  - Correo de confirmación de recepción al proveedor (al cambiar el
    pedido a un estado de `ESTADOS_EMAIL_PROVEEDOR`).
  - Las 3 plantillas de alerta que llevan firma de comprador —
    `_email_template_enviado_proveedor`, `_email_template_entrega_parcial`,
    `_email_template_pendiente_cotizacion` — usadas tanto por el envío
    manual (`_build_alerta_email`) como por la reclamación automática
    (`_encolar_reclamacion_proveedor_auto`, que reutiliza la misma
    plantilla).
- `_get_todos_usuarios_hotel()` ahora también selecciona `u.movil`
  para los compradores (antes solo `id, username, nombre, email`),
  necesario para el primer punto; `_get_compradores_hotel()` (usada
  en el segundo punto) ya devolvía `movil`.
- Formato de firma: nombre en negrita, salto de línea, email
  (mailto) y " · Móvil: XXXXXXXXX" a continuación si el comprador
  tiene móvil registrado; si no tiene nombre o móvil, esa parte se
  omite sin dejar hueco en blanco.
- La plantilla de "pendiente de firma" (aviso interno a Dirección de
  Compras/Hotel) no lleva firma de comprador — no se ha tocado.

---

## 2026-07-30

### [Control Pedidos] v12.23.4 — Un envío por contacto "principal" del proveedor, en vez de uno solo
- Reabre el asunto que se había dado por cerrado — reportado: el
  pedido 23979 llegó 2 veces, el 40130 3 veces, el 15147 2 veces, el
  28090 1 vez... coincidía exactamente con cuántos contactos tiene
  cada proveedor marcados como "principal" en su ficha.
- Causa: `_encolar_reclamacion_proveedor_auto()` pasaba
  `proveedor_emails` (lista) como `destinatarios_email` a
  `_encolar_email_sistema()`, que encola una fila (= un envío) por
  cada elemento de la lista.
- Corregido: un único envío, con todos los contactos principales
  juntos en el "Para:" (`", ".join(proveedor_emails)`) — mismo
  patrón ya usado correctamente en los otros dos sitios del código
  que mandan email a proveedor (aviso al cambiar de estado y
  "Re-notificar" manual), que nunca tuvieron este problema.
- Badge de versión del sidebar actualizado a "V 12.23.4".


- Reportado: la reclamación solo evitaba mandarse dos veces el mismo
  día, no respetaba ningún ciclo — reclamaría todos los días mientras
  el pedido siguiera urgente.
- Petición: que siga las pautas ya configuradas en Config Alertas
  (controlable desde el panel de administración).
- `_nunca_notificado()` y `_dias_ultima_notificacion()` ahora aceptan
  `tipo` (antes fijo a `telegram_auto`), compatible hacia atrás.
- Camino estándar: reutiliza el mismo `cfg["ciclo"]` configurado por
  estado — sin ciclo definido para un estado, no repite tras la
  primera vez.
- Camino con plazo: sin cambios, ya respetaba su propio ciclo
  ("Plazo entrega — Ciclo urgente tras vencer") desde el principio.
- Badge de versión del sidebar actualizado a "V 12.23.2".
- **✅ Reenviadas a mano las 21 reclamaciones** que salieron con HTML
  crudo antes de v12.23.0 (borrado su registro de `whatsapp_log` del
  día para forzar reevaluación) — confirmado que llegaron legibles y
  que los popups internos (Telegram) correctamente **no** se
  duplicaron, al ser un registro independiente (`telegram_auto`)
  que no se tocó.
- **✅ ASUNTO DADO POR CERRADO** (30/07/2026).


- Reportado: aunque la reclamación por fin se disparó (v12.22.8), el
  proveedor la recibió con etiquetas HTML literales
  (`<div style="font-family:Arial...`) en vez de un email legible.
- Causa: el frontend usa `message: p.cuerpo_text || p.cuerpo_html || ''`
  para EmailJS — `_encolar_reclamacion_proveedor_auto()` era la única
  de las 5 llamadas a `_encolar_email_sistema()` que no pasaba
  `cuerpo_text`, así que caía al HTML crudo como si fuera texto plano.
- Corregido con `_html_a_texto_plano()` (conversor básico HTML→texto),
  aplicado dentro de `_encolar_email_sistema()` como red de seguridad
  general — protege también cualquier llamada futura que se olvide de
  pasar `cuerpo_text`. Revisadas las otras 4 llamadas — todas ya
  pasaban su propia versión en texto.
- Badge de versión del sidebar actualizado a "V 12.23.0".
- **Pendiente:** confirmar con la próxima reclamación real que el
  email llega legible.


- El log de v12.22.6 mostró `dias=None` en TODOS los pedidos pese a
  fechas válidas — `_dias_desde_fecha()` referenciaba `_d`/`_dt`, dos
  nombres que nunca existieron en su ámbito (solo imports locales de
  otras funciones sin relación). Cada llamada lanzaba `NameError`,
  silenciado por un `except Exception: return None` genérico.
- **Alcance real, más amplio de lo que parecía** — afecta a 3 sitios:
  el job diario de alertas, la reclamación automática, y **la alerta
  inmediata al cambiar el estado de un pedido** (esta última no se
  había mencionado hasta ahora). El sistema de "días sin avance"
  llevaba tiempo sin disparar nada nuevo en ninguno de los tres.
- Corregido usando los nombres bien importados a nivel de módulo
  (`datetime`, `date as _date`). El `except` ahora registra la
  excepción real con `log.warning()` en vez de tragársela en
  silencio, para que esto no vuelva a pasar desapercibido.
- Badge de versión del sidebar actualizado a "V 12.22.8".
- **✅ CONFIRMADO EN PRODUCCIÓN** — reclamación real recibida (pedido
  SAP 27742, Maspalomas & Tabaiba, 55 días, formato correcto) y
  popups al administrador también llegando bien. Los tres frentes
  afectados por el bug quedan verificados funcionando.


- Job de las 11:00 completó en 336ms con "0 enviadas, 0 omitidas" —
  demasiado rápido para 33+ alertas reales, y `omitidos` (que sí se
  incrementa en el primer gate que casi todos deberían tocar) también
  en 0 → sospecha de que `alertas_raw` (consulta propia del job,
  distinta de la del panel) devuelve 0 filas.
- Añadido `RECLAMACION-DEBUG alertas_raw=N filas` tras la consulta, y
  traza por pedido en la entrada del camino estándar (estado, cfg
  encontrado, campo/valor de fecha de referencia, días, umbral).
- Badge de versión del sidebar actualizado a "V 12.22.6".
- **Pendiente:** revisar logs tras el próximo despliegue y ciclo.


- Pedido #13549 (probado en detalle: Fuerteventura, sin plazo, `ENVIADO
  AL PROVEEDOR`, `URGENTE`, 95 días) seguía sin reclamación tras
  v12.22.2. Descartados los dos motivos de omisión silenciosa más
  obvios: proveedor GRUPO DISTRIBUIDRO GARAU sí tiene email
  (`javier.garcia@garau.es`), y Fuerteventura sí tiene comprador con
  email (`comprascan4`).
- Sin Shell disponible en el plan Free de Render para inspeccionar
  el código desplegado directamente (requiere plan Starter).
- Añadido logging de diagnóstico (`BUILD-MARKER`, `RECLAMACION-DEBUG`
  en el bucle principal y en los dos primeros retornos silenciosos de
  `_encolar_reclamacion_proveedor_auto()`) — sin tocar el
  comportamiento, solo visibilidad, para localizar la causa real en
  la próxima ejecución del job vía búsqueda de logs en Render.
- Badge de versión del sidebar actualizado a "V 12.22.4".
- **Pendiente:** revisar los logs `RECLAMACION-DEBUG` tras el próximo
  ciclo del job (07-16h) para identificar la causa exacta.


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
