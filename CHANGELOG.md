# v12.30.48 — 28 agosto 2026

🐛 Auditoría completa: el widget "Necesita atención" del Dashboard (y otros dos sitios puntuales) mostraban el Nº interno en vez del Nº Pedido (DALI/SAP)

**Petición de Víctor**, a partir de dos capturas del Dashboard con el aviso "Pedido 702 (MT, CASA DELFIN,SA) lleva 46 días en «ENVIADO AL PROVEEDOR» sin avanzar.": "siguen apareciendo avisos y o comunicaciones haciendo referencia el pedido lineal # y no al Nº pedido Dali/Sap, puedes revisar todos los apartados para zanjar este asunto? Pedidos, Alertas, Dasboard, Techo Gasto, etc?"

**Alcance de la revisión**: barrido completo de las 57 apariciones de `norden` en `app.py` y las 18 de `templates/index.html`, apartado por apartado (Pedidos, Alertas, Dashboard, Techo de Gastos, Pedidos eliminados, correos internos y al proveedor, Telegram/WhatsApp, exportaciones a Excel e informes imprimibles). Se han encontrado y corregido 3 sitios con el problema real; el resto de apariciones de `norden` ya eran correctas: o bien columnas de tabla claramente etiquetadas por separado ("Nº" / "Pedido DALI / SAP") pensadas para poder consultar ambos números a la vez (tablas de Pedidos, Alertas, Pedidos eliminados, exportaciones de Techo de Gastos y Alertas, backups Excel), o bien ya usaban el patrón correcto de mostrar primero `pedido_num` y recurrir a `norden` solo como reserva para el caso raro de un pedido que aún no tenga Nº Pedido (DALI/SAP) asignado (Telegram de cambio de estado, avisos de techo, WhatsApp/Telegram de alertas, tarjetas y expedientes de Techo de Gastos, "Comparar listado PDF").

**Cambio en `app.py` (`dashboard_stats`, construcción de `necesita_atencion`)**: el diccionario que alimenta el aviso "Necesita atención" del Dashboard (y el resumen semanal) incluía `id` y `norden` pero omitía `pedido_num`, aunque la consulta de la que sale (`alertas`, vía `PEDIDO_SELECT_STATS`) ya lo trae — se añade `"pedido_num": top.get("pedido_num")` al diccionario.

**Cambio en `templates/index.html` (widget "Necesita atención" del Dashboard y "Resumen de la semana")**: `Pedido ${na.norden || na.id}` pasa a `Pedido ${na.pedido_num || ('#' + (na.norden || na.id))}` en los dos sitios que consumen ese mismo dato — mismo patrón de prioridad ya usado en el resto de la app desde v12.30.41 (Línea temporal del Dashboard).

**Cambio en `templates/index.html` (modal de confirmación al eliminar un pedido)**: la frase "Vas a eliminar el pedido Nº {norden}" nunca consultaba `pedido_num` — pasa a mostrar el Nº Pedido (DALI/SAP) cuando existe, con el mismo `Nº {norden}` de antes como reserva.

**Verificación**: `python3 -m py_compile app.py models.py` sin errores. `node --check` sobre el JS extraído de `templates/index.html`, sin errores. Revisión manual, uno por uno, de los 75 puntos localizados por el barrido (con su contexto de tabla/cabecera o de función) para clasificar cada uno como correcto o pendiente de arreglo antes de tocar nada.

# v12.30.47 — 28 agosto 2026

✨ Nuevo apartado "Notificaciones adicionales" (solo admin): contactos sueltos en copia según departamento del pedido + estado nuevo

**Petición de Víctor**: "necesito un apartado donde registrar varios correos electrónicos más y también donde decidir que tipo de correos se envía a cada uno de ellos en copia, es decir, ahora mismo los correos internos de cambio de estado, tenemos configurado que se envíen automáticamente al comprador, rol hotel y departamento. Ahora quiero poder decidir que cambios de estado y que pedidos también enviar con copia a estos nuevos correos [...] La idea es poder decidir que pedidos según departamento también se envían a que otros correos, siempre en copia. Por ejemplo, los pedidos de cocina, quizás me pueda interesar que al cambiar el estado a ENVIADO AL PROVEEDOR se ponga en copia al Chef Ejecutivo por ejemplo". Ejemplos de contactos a crear: Administrativo A&B, Director de Compras, Chef Ejecutivo.

**Decisión confirmada con Víctor** antes de implementar: los contactos y sus reglas son globales para toda la cadena (mismo correo y mismas reglas en los 4 hoteles) — a diferencia del correo de Departamentos por hotel (v12.30.39), que sí varía por hotel.

**Cambio en `models.py` / `app.py` (`_auto_migrate`)**: dos tablas nuevas — `notificacion_contactos` (nombre, email, email2, activo) y `notificacion_contacto_reglas` (contacto_id, departamento_id, estado, único por combinación), en el bloque protegido de `_auto_migrate()` con su propio `try/except` cada una, y en `models.py` para instalaciones nuevas. Los "estados" con sentido son únicamente los de `ESTADOS_EMAIL_INTERNO` (los que de verdad disparan el correo interno de cambio de estado) — una regla con cualquier otro estado se descarta en silencio al guardar.

**Cambio en `app.py` (`enviar_emails_estado`)**: tras la copia al departamento solicitante (v12.30.39), se añade una nueva consulta — para el departamento del pedido y el estado nuevo, busca los contactos activos con una regla que aplique y los añade al mismo correo interno, con copia a todos (nunca aparte), sin duplicar direcciones ya incluidas. Se omite en silencio si no hay ninguna regla — nunca bloquea el envío.

**Cambio en `app.py` (endpoints nuevos)**: `GET /api/admin/notificaciones-contactos` (catálogo de contactos con sus reglas + catálogo de departamentos + lista de estados válidos), `POST /api/admin/notificaciones-contactos` (crear contacto), `PUT /api/admin/notificaciones-contactos/<id>` (actualizar nombre/email/email2/activo y reemplazar por completo el conjunto de reglas de ese contacto de una vez), `DELETE /api/admin/notificaciones-contactos/<id>` (eliminar, cascada a sus reglas). Todos `@admin_required`, mismo patrón que el resto de endpoints de administración.

**Cambio en `templates/index.html`**: nuevo apartado "🔔 Notificaciones adicionales" en el sidebar (solo admin, junto a "Departamentos") — formulario para crear un contacto nuevo (nombre + correo + correo 2 opcional) y, por cada contacto ya creado, una tarjeta con sus datos editables y una matriz de checkboxes Departamento × Estado (los 5 estados de `ESTADOS_EMAIL_INTERNO`) para marcar en qué combinaciones recibe copia — cada tarjeta tiene su propio botón "💾 Guardar" y "🗑️ Eliminar" (la lista de contactos es dinámica, a diferencia de Departamentos, así que no hay un único botón para toda la pantalla).

**Verificación**: `python3 -m py_compile app.py models.py` sin errores. `node --check` sobre el JS extraído de `templates/index.html`, sin errores. Prueba aislada en Python de la lógica de fusión de destinatarios (contacto nuevo se añade, contacto ya presente no duplica, contacto con dos correos añade ambos, contacto sin correo se salta en silencio, sin reglas no cambia nada) — todos los casos correctos.

# v12.30.46 — 28 agosto 2026

✨ "Comparar listado PDF (SAP)": rellena sola la Fecha tramitación de pedidos antiguos que nunca tuvieron el PDF oficial individual adjuntado

**Petición de Víctor** (idea propuesta por Claude tras la entrega de v12.30.45 y aceptada por Víctor): "cuando comparas el «Listado de Pedidos» PDF de SAP, aplica la misma comprobación que ya hace el PDF oficial individual — rellenar sola la Fecha tramitación si falta, usando la fecha de pedido que también trae ese listado, para los pedidos antiguos que nunca tuvieron el PDF oficial individual adjuntado".

**Cambio en `app.py` (`_comparar_listado_pdf_logica`)**: tercera escritura silenciosa (junto a Total Pedido y la base imponible de la última entrada, ya existentes desde v12.30.27/v12.30.44) — para cada pedido localizado en el listado de SAP, si `pedidos.fecha_tramitacion` está vacía, se rellena con la "fecha de pedido" de esa misma línea del PDF. A diferencia de Total Pedido y la base imponible (que se sobrescriben si el valor calculado cambia), esta NUNCA se sobrescribe una vez tiene un valor — no hay ningún usuario delante durante esta comparación en segundo plano a quien preguntarle cuál de las dos fechas es la correcta, así que ante la duda no se toca (mismo criterio de fondo que la comprobación interactiva del PDF oficial individual de v12.30.45, pero sin la parte de "preguntar", que en este caso masivo no aplica). Como `_comparar_listado_albaranes_logica()` reutiliza internamente esta función para su propia auditoría del PDF 1, este relleno queda disponible también desde "Comparar Pedidos + Albaranes", sin cambios adicionales.

**Cambio en `templates/index.html`**: nuevo aviso "💾 N «Fecha tramitación» rellenada(s) sola(s)" en el resumen de "Comparar listado PDF (SAP)" (`_renderCompararPdfResultado`, reutilizado también por la comparación combinada con Albaranes) — mismo estilo que los avisos ya existentes de Total Pedido y base imponible.

**Verificación**: `python3 -m py_compile app.py` sin errores. `node --check` sobre el JS extraído de `templates/index.html`, sin errores. Prueba aislada en Python de la lógica de relleno con 7 casos (fecha vacía → se rellena, fecha ya presente → intacta pase lo que pase el PDF, pedido no encontrado en la app, fecha del PDF vacía, fecha del PDF con formato inválido, fecha vacía representada como cadena vacía en vez de NULL, y una mezcla de varios pedidos a la vez) — todos correctos.

# v12.30.45 — 28 agosto 2026

✨ "Fecha tramitación": solo admite correo electrónico (ya no PDF) — y se comprueba/auto-rellena con la Fecha Pedido y Fecha Entrega del PDF oficial

**Petición de Víctor**, a partir de dos capturas del formulario (sección "Fechas del flujo" y el PDF oficial con "Fecha Pedido"/"Fecha Entrega" en cabecera): "el archivo adjunto de FECHA TRAMITACION deberá ser ahora solo y exclusivamente un enlace de correo electrónico del pedido enviado al proveedor, así que eliminamos poder introducir cualquier otro tipo de archivo y dejamos las instrucciones al estilo que ya tenemos en el apartado Nº PEDIDO DALI/SAP, cuando se cargue el PDF del Nº PEDIDO se deberá también verificar la fecha de tramitación incluida en el PDF «Fecha Pedido» si no se ha introducido fecha tramitacion, ponemos esta automáticamente y si la hemos introducido y difiere, entonces preguntar al usuario cual de las 2 es la correcta para dejar en este apartado. En caso de no haber introducido en el pedido fecha de entrega o plazo de entrega días, preguntar al usuario si registramos la fecha de entrega indicada en el pedido (PDF) y en caso afirmativo la incluimos en el apartado FECHA DE ENTREGA ESPECÍFICA".

**Decisiones confirmadas con Víctor** antes de implementar: se mantiene el límite de un único correo en «Fecha tramitación» (ya se aplicaba antes de este cambio a los correos de este apartado, aunque hasta ahora convivía con hasta 3 PDF); el correo sigue siendo opcional — no se exige para poder pasar a ENVIADO AL PROVEEDOR (a diferencia del PDF oficial de «Nº Pedido», que sí es obligatorio desde v12.30.42).

**Cambio en `app.py` (`upload_adjunto`, tipo `tramit_eml`)**: separado del tipo `vb_eml` (que sigue admitiendo correo o PDF, sin cambios — la petición de Víctor solo afectaba a «Fecha tramitación»); ahora solo admite `.eml`/`.msg`, se rechaza cualquier PDF u otro tipo de archivo.

**Cambio en `app.py` (`_parsear_pdf_pedido_oficial`)**: además de Nº de Pedido y Total Pedido, reconoce (con dos expresiones regulares nuevas) "Fecha Pedido" y "Fecha Entrega" del PDF oficial y las devuelve en formato ISO — a diferencia del Nº de Pedido y el Total, estos dos campos son opcionales: si no se reconocen, no se rechaza el PDF, simplemente no hay fecha que proponer. `upload_adjunto` (tipo `pedido_doc`) las incluye en la respuesta de la subida (`fecha_pedido_iso`, `fecha_entrega_iso`) — sin escribir nada en la base de datos por esa vía, a diferencia de `pedido_num`/`total_pedido`, porque «Fecha tramitación» y «Fecha de entrega específica» siguen siendo campos normales, editables a mano.

**Cambio en `templates/index.html`**: nueva `_procesarFechasPdfPedidoOficial()`, llamada tras leer con éxito el PDF de «Nº Pedido (DALI/SAP)» — si «Fecha tramitación» está vacía, se rellena sola con la «Fecha Pedido» del PDF; si ya tiene un valor distinto, se pregunta (con `confirm()`, mismo patrón ya usado en toda la app) cuál de las dos dejar; si «Fecha de entrega específica» y «Plazo entrega (días)» están AMBOS vacíos, se pregunta si registrar la «Fecha Entrega» del PDF como «Fecha de entrega específica». Los valores rellenados aquí quedan pendientes de guardar como el resto del formulario (no se escriben solos en la base de datos). El botón de «Fecha tramitación» pasa a aceptar solo `.eml`/`.msg`, con el mismo estilo de texto explicativo que ya tiene «Nº Pedido (DALI/SAP)».

**Verificación**: `python3 -m py_compile app.py` sin errores. `node --check` sobre el JS extraído de `templates/index.html`, sin errores. Prueba con el PDF real de ejemplo (pedido 16287, `pypdf`): reconoce Fecha Pedido 21/08/2026 y Fecha Entrega 21/09/2026, además de los campos ya verificados en v12.30.42 (Nº Pedido 16287, Total 4.614,60 €).

# v12.30.44 — 28 agosto 2026

✨ "Comparar listado PDF (SAP)" + Albaranes: rellena sola la Base imp. (€) de CUALQUIER entrada ya registrada a la que le faltaba, no solo la última

**Petición de Víctor**, a partir de dos capturas del modal "Comparar listado PDF (SAP)" con la opción "+ Comparar también con el listado de Albaranes registrados en DALI": "cuando realizamos la comparativa de listados (ver imagen) y se localizan pedidos introducidos y entradas parciales o totales, el sistema modifica el estado automáticamente e introduce los totales sin igic, cuando estas entradas parciales o totales ya estan registradas pero no se rellenó la celda total sin igic, la aplicacion deberia comprobar si tiene o no valor esta celda y rellenarla en caso de que este vacia".

**Contexto — el hueco detectado**: la app ya tenía dos mecanismos de auto-relleno de Base imp. (€), pero ninguno cubría el caso general — `_comparar_listado_pdf_logica()` solo recalcula la ÚLTIMA entrada de cada pedido (a partir del importe acumulado que trae SAP), y la única excepción de `_comparar_listado_albaranes_logica()` (v12.30.36) solo rellenaba la entrada ligada al ÚNICO albarán emparejado como "coincidencia sin cambios pendientes" de esa comparación en concreto. Una entrada antigua, no-última, de un pedido que no aparecía entre esas coincidencias (por ejemplo por ser de una entrega parcial ya superada, o porque SAP ya no la lista como pendiente) nunca se tocaba, aunque su número de entrada SÍ apareciera en el "Listado de Albaranes" recién subido.

**Cambio en `app.py` (`_comparar_listado_albaranes_logica`)**: sustituida la excepción anterior (limitada a una entrada por comparación) por un barrido general — tras cruzar los dos PDF, recorre TODAS las entradas de TODOS los pedidos ya dados de alta de este hotel (no solo los que aparecen en la tabla de coincidencias propuestas) y, para cada entrada que ya tiene número de "Nº Entrada DALI/SAP" pero le falta la Base imp. (€), busca ese número (normalizado, ignorando ceros a la izquierda) entre los albaranes del "Listado de Albaranes" (PDF 2) recién subido — si lo encuentra, rellena solo ese campo con el importe de ese albarán. Nunca sobrescribe un valor ya introducido, y nunca toca el número de entrada, la fecha o el estado (eso sigue requiriendo confirmación explícita vía "Aplicar"). Un número de registro que aparezca duplicado en el PDF 2 se descarta por seguridad, sin adivinar cuál de los dos importes es el correcto. Este barrido solo se ejecuta al comparar CON el listado de Albaranes (PDF 2) — la comparación de un solo PDF ("Comparar listado PDF (SAP)" sin la opción de Albaranes) no tiene acceso al detalle por albarán necesario y sigue igual que antes (solo recalcula la última entrada).

**Cambio en `templates/index.html`**: el aviso "💾 N base imponible actualizada(s) sola(s)" del modal de comparación de Albaranes actualiza su texto ("entradas ya registradas" en vez de "ya al día") para reflejar el alcance ampliado — sigue siendo el mismo contador, ahora cubre más casos.

**Verificación**: `python3 -m py_compile app.py` sin errores. `node --check` sobre el JS extraído de `templates/index.html`, sin errores. Prueba aislada en Python del barrido con datos representativos: pedido con dos entradas donde falta la base imponible de la PRIMERA (no la última) y su número coincide con un albarán del PDF 2 → se rellena solo esa; entrada que ya tiene base imponible → no se toca; entrada sin coincidencia en el PDF 2 → no se toca; número de registro duplicado en el PDF 2 → se descarta esa entrada por seguridad; varios pedidos con varias entradas a la vez; entrada legacy sin fecha (formato antiguo, solo número) — todos los casos correctos.

# v12.30.43 — 28 agosto 2026

🐛 "Nº Entrada DALI/SAP": la Base imp. (€) de cada entrada pasa a ser obligatoria (parcial o final)

**Petición de Víctor**, a partir de una captura de una entrada de "Nº Entrada DALI / SAP" sin base imponible rellena: "vamos a poner que el total sin igic sea obligatorio para continuar, tanto en parcial como en total".

**Cambio en `app.py` (`_validar_base_imponible_entradas`, nueva)**: comprueba que TODAS las entradas de la lista (no solo la que se acaba de añadir) tengan una base imponible > 0 — se aplica sobre toda la lista para que un pedido con alguna entrada antigua sin rellenar (de antes de este cambio) no se pueda seguir editando sin completarla también.

**Cambio en `app.py` (`update_pedido`)**: la validación se aplica cada vez que se guarda un pedido con estado ENTREGA PARCIAL o ENTREGADO, tanto en la rama de rol Hotel (que es la que gestiona normalmente esta sección) como en la rama general — si falta alguna base imponible, se rechaza con 422 y el mensaje "La Base imp. (€) es obligatoria en cada entrada de «Nº Entrada DALI / SAP» — tanto en una entrada parcial como en la entrada final (total) — para poder continuar."

**Cambio en `templates/index.html`**: nueva función `_validarBaseImponibleAlbaran()`, llamada antes de guardar (en ambos flujos de guardado, Hotel y el resto de roles) cuando el estado es ENTREGA PARCIAL o ENTREGADO — si falta alguna, muestra el aviso y resalta la primera casilla vacía, sin llegar a enviar la petición. Placeholder y título del campo actualizados ("Base imp. (€) *") para reflejar que ya no es opcional.

**Verificación**: `python3 -m py_compile app.py` sin errores. `node --check` sobre el JS extraído de `templates/index.html`, sin errores. Prueba aislada en Python de `_validar_base_imponible_entradas()`: sin entradas (válido), una entrada con importe (válido), entrada sin importe / solo número / importe 0 (inválidas), dos entradas con una sin rellenar (inválido) — todos los casos correctos.

# v12.30.42 — 28 agosto 2026

✨ "Nº Pedido (DALI/SAP)": solo admite el PDF del pedido oficial PRINCESS — Nº de Pedido y Total Pedido se leen solos y dejan de ser editables

**Petición de Víctor**, a partir de una captura del formulario de pedido y del PDF oficial de un pedido tramitado (16287): "me gustaría que solo se pudiera cargar un PDF y del formato que también adjunto, este PDF puede tener el nombre que sea pero la estructura siempre la misma, es nuestro formato de pedido oficial, una vez cargado obligatoriamente, la aplicación debe leer y rellenar dos celdas automáticamente del pedido CELDA «Nº Pedido (DALI/SAP)» y CELDA «Total Pedido (€) (SAP, opcional)» la primera con el valor del PDF «PEDIDO» en el ejemplo «16287» y la segunda con el valor de la suma de los importes, en el ejemplo 4314,60 + 300 = 4614,60 € ; no indicar el indicado en el PDF como «TOTAL PEDIDO» ya que este valor no es correcto porque no aparecen los descuentos aplicados. Estas dos celdas no se podrán rellenar manualmente y únicamente se podrá cambiar el estado a ENVIADO si se adjunta el PDF correcto, lanzar mensaje didáctico al usuario en caso de faltar indicando que se debe adjuntar en este punto únicamente el PDF del pedido oficial PRINCESS ; eliminar la anotación de opcional en el campo total".

**Decisiones confirmadas con Víctor** antes de implementar: se elimina la opción de adjuntar correo .eml/.msg en este apartado (solo PDF oficial); si se elimina el PDF ya adjuntado, el Nº de Pedido y el Total Pedido conservan su último valor leído (no se vacían) hasta que se suba un PDF nuevo, que los sobrescribe — evita perder datos de pedidos ya avanzados si alguien borra el adjunto por error.

**Cambio en `app.py` (`_parsear_pdf_pedido_oficial`, nueva)**: lee el PDF con `pypdf` (mismo enfoque que `_comparar_listado_pdf_logica`, ver comentario sobre el orden real del texto extraído) y reconoce, con dos expresiones regulares tolerantes al formato: el Nº de Pedido (línea "PEDIDO 00016287" → "16287", sin ceros a la izquierda, vía `_normalizar_pedido_num`) y todas las líneas de artículo con su Cantidad/Precio/Importe, sumando la columna Importe — nunca el "Total Pedido..." que trae el propio PDF al pie, que no incluye los descuentos. Si el PDF no se puede leer o no se reconoce esa estructura, se rechaza el archivo entero con un mensaje claro pidiendo el PDF oficial correcto — nunca se guarda un resultado a medias o adivinado.

**Cambio en `app.py` (`upload_adjunto`, tipo `pedido_doc`)**: deja de admitir Word y correo .eml/.msg — solo PDF; se rechaza cualquier archivo cuyo contenido no se reconozca como el pedido oficial (ver arriba); al guardarse con éxito, la app actualiza sola `pedido_num` y `total_pedido` del pedido y los devuelve en la respuesta.

**Cambio en `app.py` (`create_pedido`/`update_pedido`)**: `pedido_num` y `total_pedido` dejan de aceptarse desde el formulario — se ignoran aunque se envíen, y sus valores solo cambian a través de la subida del PDF oficial (o, para `total_pedido`, también vía "Comparar listado PDF (SAP)", que sigue funcionando igual). La validación de paso a ENVIADO AL PROVEEDOR ahora exige el PDF oficial adjunto (Nº de Pedido y Total Pedido ya rellenos), con el mensaje: "Debe adjuntar el PDF del pedido oficial PRINCESS en la sección «Nº Pedido (DALI/SAP)»...".

**Cambio en `templates/index.html`**: los campos "Nº Pedido (DALI/SAP)" y "Total Pedido (€)" pasan a ser de solo lectura para todos los roles (antes solo lo era para el rol Hotel), con la anotación "(automático)" en vez de "(SAP, opcional)"; el botón de adjuntar solo acepta `.pdf`; tras subir el PDF, los dos campos se rellenan al momento con la respuesta del servidor; la comprobación previa a pasar a ENVIADO AL PROVEEDOR (y su aviso) se actualiza al nuevo mensaje. El atajo "Crear pedido desde comparación" (que prellenaba el Nº de Pedido con el Nº de SAP encontrado en el listado) ya no escribe ese campo — ahora solo avisa del Nº de SAP a buscar, ya que escribirlo no tendría efecto al guardar.

**Aviso para pedidos ya en curso**: los pedidos creados antes de este cambio que todavía no hayan pasado a ENVIADO AL PROVEEDOR necesitarán el PDF oficial adjunto para poder avanzar, aunque ya tuvieran un Nº de Pedido escrito a mano — es el comportamiento pedido explícitamente por Víctor. Los pedidos que ya pasaron ese estado no se ven afectados.

**Verificación**: `python3 -m py_compile app.py` sin errores. `node --check` sobre el JS extraído de `templates/index.html`, sin errores. Prueba con el PDF real de ejemplo (pedido 16287, `pypdf` 3.17.4): reconoce Nº Pedido "16287" y Total Pedido 4.614,60 € (4.314,60 + 300,00), ignorando el "Total Pedido..." incorrecto (7.491,00 €) que trae el PDF. Prueba con un PDF no oficial: se rechaza con el mensaje didáctico, sin guardar nada.

# v12.30.41 — 28 agosto 2026

🐛 "Línea temporal" (panel principal): mostraba el Nº interno del pedido en vez del Nº Pedido (DALI/SAP)

**Petición/reporte de Víctor**, a partir de dos capturas del widget "Línea temporal": "en estos avisos no se está utilizando el número de pedido DA/SAP que sería lo correcto, creo que es el número de apunte #".

**Confirmado**: el widget mostraba `p.norden` — el "Nº" lineal interno de la app (autoincremental, sin relación con SAP/DALI) — en vez de `p.pedido_num`, el campo "Nº Pedido (DALI/SAP)" que el usuario introduce a mano y que sí aparece en los listados de SAP/DALI que maneja. Es exactamente el mismo criterio que ya se aplicó en el resumen de comparación de albaranes (v12.19, ver comentario en `app.py` junto a `pedido_num_sap`) y que ya se usa en otros paneles de la app (p. ej. la vista de detalle de alertas) — aquí simplemente no se había aplicado en este widget en concreto.

**Cambio en `app.py`**: la consulta de `/api/dashboard` (`timeline`) añade `p.pedido_num` al `SELECT` junto al `norden` que ya traía.

**Cambio en `templates/index.html`**: el renderizado de "Línea temporal" muestra ahora `pedido_num` como número principal; si un pedido todavía no tiene Nº Pedido (DALI/SAP) asignado, se sigue mostrando el Nº interno con el prefijo "#" como reserva (`#123`) — mismo patrón ya usado en el panel de alertas (`p.pedido_num||('#'+p.norden)`), para que nunca falte una referencia aunque sea la interna.

**Verificación**: `python3 -m py_compile app.py` sin errores. `node --check` sobre el JS extraído de `templates/index.html`, sin errores.

# v12.30.40 — 28 agosto 2026

✨ Correo "ENVIADO AL PROVEEDOR": enlace de descarga del PDF del pedido en vez de adjuntarlo (EmailJS en el plan Free no admite adjuntos)

**Contexto — petición previa de Víctor** (a partir de dos capturas del campo "Nº Pedido (DALI/SAP)" con un PDF adjunto): "es posible adjuntar PDF en el envío de correos con emailjs? la idea es que cuando el cambio de estado sea a ENVIADO AL PROVEEDOR, se adjunte el PDF del pedido que tenemos en el apartado Nº PEDIDO (DALI/SAP)". Se investigó la vía de adjuntar el archivo con EmailJS: es técnicamente posible, pero solo en los planes de pago (Personal 9€/mes hasta 500KB, Professional 15€/mes hasta 2MB, Business 40€/mes hasta 30MB) — la cuenta actual está en el plan Free, que no admite adjuntos en absoluto, y el propio límite de subida de la app (20MB) podría superar incluso el tope del plan Business.

**Petición de Víctor** (alternativa, tras conocer esas limitaciones): "se me ocurre si en vez de adjuntar el archivo se ponga un enlace para descargar de Supabase pulsando en él".

**Cambio en `models.py` / `app.py` (`_auto_migrate`)**: nueva tabla `adjunto_descarga_tokens` (`adjunto_id` → `pedido_adjuntos.id`, `token` único, `expira_en`, `creado_en`) — un token por archivo, válido 180 días, reutilizable (no de un solo uso) hasta que caduque. Añadida en el bloque protegido de `_auto_migrate()`, con su propio `try/except`, y en `models.py` justo después de `pedido_adjuntos` (de la que depende por clave foránea).

**Cambio en `app.py` (nuevas funciones)**: `_obtener_o_crear_token_adjunto(adjunto_id)` genera (o reutiliza si sigue vigente) el token de un adjunto. `_enlaces_descarga_pedido_doc(pedido_id)` localiza el/los PDF subidos en "Nº Pedido (DALI/SAP)" (tipo `pedido_doc` o el legacy `pedido_pdf`, excluyendo los `.eml/.msg` de evidencia interna) y devuelve sus enlaces de descarga; si no hay ningún PDF en ese apartado, devuelve una lista vacía y el correo se envía igual, sin enlace — nunca se bloquea el envío por esto. El filtro de PDF acepta tanto `mime_type='application/pdf'` como `application/octet-stream` con nombre terminado en ".pdf", porque la validación de subida de "pedido_doc" permite ese mime genérico para un PDF real cuando el navegador no lo identifica correctamente, y ese es el valor que queda grabado tal cual.

**Cambio en `app.py` (`enviar_emails_estado`)**: en el correo "Correo al proveedor" (el que se envía al cambiar el estado a ENVIADO AL PROVEEDOR), se añade un botón de descarga por cada PDF encontrado en "Nº Pedido (DALI/SAP)", justo después de la nota de IGIC. Sin PDF, el correo sale exactamente igual que hasta ahora, sin ninguna sección de más.

**Cambio en `app.py` (descarga pública sin login)**: la lógica de servir un adjunto (ETag/caché, origen transparente en base de datos o Supabase Storage) se extrae del endpoint existente `/api/adjuntos/<id>` a un helper compartido, `_servir_adjunto_response()`. Nuevo endpoint público `GET /descargas/adjunto/<token>` (sin `@login_required`, pensado para que lo abra el proveedor desde el correo) que valida el token contra `adjunto_descarga_tokens` y, si es válido y no ha caducado, sirve exactamente el mismo archivo con el mismo helper. El token da acceso únicamente al archivo con el que se generó, nunca a ningún otro adjunto ni a ninguna otra parte de la app. No hay revocación manual desde la app: si hiciera falta invalidar un enlace ya enviado, basta con borrar la fila correspondiente en Supabase.

**Sin coste adicional ni cambio de plan de EmailJS** — esta vía sustituye por completo a la idea de adjuntar el archivo directamente.

**Verificación**: `python3 -m py_compile app.py` sin errores. No se ha tocado `templates/index.html` (cambio íntegramente de backend), por lo que no aplica `node --check` más allá de la comprobación habitual del badge.

# v12.30.39 — 28 agosto 2026

✨ Nuevo apartado "Departamentos" (solo admin): correo por hotel para cada departamento, en copia en el correo interno de cambio de estado de sus pedidos

**Petición de Víctor** (registrada primero en `PENDIENTES.md` el 28/08, implementada hoy tras confirmar el diseño): "apartado para registrar los correos electrónicos de los diferentes departamentos que tenemos registrados al uso en el apartado departamento de pedidos; tener en cuenta que cada hotel tiene sus correos diferenciados entre departamentos y hoteles; la idea es que los correos internos de cambio de estado de los pedidos que ahora se envían al rol hotel y compradores, se envíen con copia al departamento solicitante del pedido, ejemplo, pedido JN restaurante, se debe enviar el correo interno al comprador JN al rol hotel JN y al correo del departamento restaurante del JN, mismo correo con copia a todos."

**Decisiones de diseño confirmadas con Víctor** antes de implementar: la nueva pantalla es un apartado propio en el sidebar ("Departamentos", solo admin — `departamentos` no tenía ninguna pantalla de administración hasta ahora); la copia solo se añade al correo electrónico (Telegram y popup, sin cambios); si un departamento de un hotel concreto no tiene correo registrado, el correo se envía igual a rol hotel y compradores, simplemente sin copia — sin ningún aviso adicional.

**Cambio en `models.py` / `app.py` (`_auto_migrate`)**: nueva tabla `departamento_hotel_email` (`hotel_id`, `departamento_id`, `email`, `email2`, único por hotel+departamento) — necesaria porque `departamentos` es un catálogo único y global (mismo "RESTAURANTE" en todos los hoteles); esta tabla es la que permite que cada hotel tenga su propio correo para el mismo departamento. Añadida en el bloque protegido de `_auto_migrate()`, con su propio `try/except`, siguiendo la misma regla que ya obligó a mover `total_pedido` y `sujeto_seguimiento` ahí.

**Cambio en `app.py` (endpoints)**: `GET /api/admin/departamentos-email?hotel_id=<id>` (catálogo de departamentos + correos ya registrados para ese hotel) y `PUT /api/admin/departamentos-email` (guarda de una vez todos los departamentos de un hotel; una fila con los dos correos vacíos borra el registro). Ambos `@admin_required`, mismo patrón que `/api/admin/config-avisos`.

**Cambio en `app.py` (`enviar_emails_estado`)**: tras construir la lista de destinatarios internos (comprador + rol hotel, con la exclusión de quien hizo el cambio si no es automático), se añade el correo del departamento del pedido para su hotel, si existe — en el mismo correo, con copia a todos, nunca aparte. No se excluye aunque coincida con el email de quien hizo el cambio (es un buzón de departamento, no una persona). Se omite en silencio si no hay correo registrado.

**Cambio en `templates/index.html`**: nuevo apartado "📧 Departamentos" en el sidebar (solo admin, junto a "Familias artículos") con selector de hotel y una tabla editable (Departamento / Correo / Correo 2) que se guarda de una vez con "💾 Guardar cambios" — mismo patrón visual que "Config. Avisos".

**Verificación**: `python3 -m py_compile app.py` sin errores. `node --check` sobre el JS extraído de `templates/index.html`, sin errores. Prueba aislada en Python de `_emails_usuario()` con los casos relevantes (sin fila, con los dos correos, con uno solo, con ambos vacíos) — todos correctos.

**Retirado de `PENDIENTES.md`** al quedar implementado — ver esta entrada y `docs/HISTORIAL_CAMBIOS.md` para el detalle.

# v12.30.38 — 28 agosto 2026

🐛 El popup de "familia de artículos repetida" (y el de techo mensual) podía llegar cada pocos minutos, sin parar, en vez de una vez al día

**Petición/reporte de Víctor**: "la alerta en popup al comprador cuando se tiene duplicada la familia en techo de gastos ¿por qué se recibe cada pocos minutos continuamente?"

**Causa**: tanto `_job_familia_repetida_inner()` como `_job_alertas_techo_mensual()` calculan cada día si ya se avisó a un hotel ("dedup diario") consultando `whatsapp_log` — pero esa fila de control solo se escribía **dentro del bucle de envío por Telegram** (`familia_repetida`: solo si había al menos un destinatario de Telegram configurado para ese evento; `techo_mes`: solo si además ese destinatario tenía `telegram_chat_id` guardado). El popup, en cambio, se encola en un bucle aparte, totalmente independiente — así que si un comprador tiene el popup activado pero NO tiene Telegram configurado para ese evento concreto (o lo tiene activado pero sin `chat_id` registrado, caso de `techo_mes`), la fila de dedup nunca se llegaba a escribir. Resultado: el job (que se reevalúa periódicamente) volvía a considerar "no notificado hoy" en cada pasada y encolaba un popup nuevo cada vez — de ahí los avisos cada pocos minutos sin parar que reportó Víctor.

**Cambio en `app.py`**: en ambos jobs, se registra ahora el dedup diario **una sola vez por hotel**, en cuanto se sabe que hay al menos un destinatario (por cualquier canal), antes de intentar el envío — en vez de depender de que el envío por Telegram llegue a completarse con éxito. El envío real (Telegram + popup) sigue funcionando exactamente igual que antes; lo único que cambia es que a partir de ahora sí queda constancia de que el hotel ya fue avisado hoy, incluso cuando ese comprador solo tiene activado el popup.

**Nota — no tocado en este cambio**: se ha detectado un patrón parecido, más estrecho, en `_job_techo_urgente_admins_inner()` (avisos de techo URGENTE a administradores): si un admin tiene el evento activado en Telegram pero sin `telegram_chat_id` guardado, el popup podría repetirse igual que aquí. Se deja anotado para revisar si Víctor confirma que también le está ocurriendo ahí — no se ha tocado porque no es el caso reportado y requeriría confirmar antes el escenario exacto.

**Verificación**: `python3 -m py_compile app.py` sin errores. No se ha tocado `templates/index.html` en la parte de JS (solo el badge de versión).

# v12.30.37 — 28 agosto 2026

🐛 El correo (y Telegram) de cambio de estado automático mostraba el nombre de quien tenía la sesión abierta en "Realizado por", como si hubiera tramitado el pedido a mano

**Petición/reporte de Víctor**, a partir de dos correos reales de "Aviso interno" (ENTREGA PARCIAL pedido 41025 y ENTREGADO pedido 27812): "Si es automático no indicar el nombre del administrador, se indica cierre automático comparación listados fecha hora, o algo por el estilo".

**Causa**: `enviar_emails_estado()` construye la fila "Realizado por" siempre a partir de `usuario_nombre` — el nombre de quien tenía la sesión abierta cuando se disparó el cambio —, sin distinguir si el cambio lo decidió una persona en ese momento (cambio manual desde la ficha del pedido) o si lo decidió el cruce automático de "Comparar Pedidos + Albaranes" (`_aplicar_coincidencia_albaran()`, que llama con `es_automatico=True`, pero hasta ahora ese parámetro solo se usaba para decidir a quién EXCLUIR de los destinatarios, no para cambiar el contenido de esa fila). El mismo problema existía en el aviso de Telegram/popup (`_telegram_cambio_estado()`, fila "Modificado por"), que ni siquiera recibía `es_automatico`.

**Cambio en `app.py`**: cuando `es_automatico=True`, tanto el correo interno ("Realizado por") como Telegram/popup ("Modificado por") muestran ahora "Cierre automático — comparación de listados (DD/MM/AAAA HH:MM)" (hora Atlantic/Canary, momento del envío) en vez del nombre de la persona. `_notificar_cambio_estado()` propaga `es_automatico` también a `_telegram_cambio_estado()` (antes se perdía en ese punto). Sin cambios en cambios manuales: se sigue mostrando el nombre de quien lo ha hecho, como siempre.

**Sobre "ENTREGA PARCIAL no tiene la base imponible" (mismo mensaje de Víctor)**: revisado — no es un fallo del código actual. Las fechas de tramitación de esos dos correos (19/08 y 04/08/2026) son anteriores al 27 de agosto, cuando se introdujo la celda "Base imp. (€)" (v12.30.31) — esas entradas de albarán se registraron antes de que existiera ese campo, así que nunca se guardó. Es exactamente el hueco que ya cierra v12.30.36 (entregado hoy mismo, un poco antes): en cuanto Víctor despliegue esa versión y vuelva a ejecutar "Comparar listado PDF (SAP)" con esos mismos pedidos todavía presentes en el PDF de SAP, sus bases imponibles se rellenarán solas, sin ninguna acción manual. No se ha reenviado ni se puede reenviar el correo ya entregado — pero el registro del pedido en la app sí quedará correcto para cualquier consulta o aviso posterior.

**Verificación**: `python3 -m py_compile app.py` sin errores. Prueba manual del fragmento nuevo con `pytz` instalado (rama automática y rama manual) — ambas devuelven el texto esperado. No se ha tocado `templates/index.html` en este cambio (es íntegramente de backend), por lo que no aplica `node --check` más allá de la comprobación habitual del badge.

# v12.30.36 — 28 agosto 2026

✨ "Comparar Pedidos + Albaranes": la base imponible de coincidencias ya al día (sin nada más pendiente) se rellena sola, sin esperar a que se pulse "Aplicar"

**Petición de Víctor**: "vale si esta información ya está cruzada y es correcta ¿porqué no la automatizamos también junto a la que ya tenemos automatizada?" — tras la explicación de v12.30.35 sobre qué hace "Aplicar todas las seleccionadas" y qué queda por aplicar cuando una fila ya está en el estado correcto (`sin_cambios_pendientes`), Víctor pidió automatizar también ese caso.

**Causa/motivo**: las filas con `sin_cambios_pendientes=True` (el pedido ya tiene ese albarán registrado, ya está en el estado objetivo y ya tiene fecha de tramitación) quedan excluidas tanto de la tabla visible de "Coincidencias propuestas" como del aviso de confirmación automática de v12.30.32 (que filtra explícitamente `!c.sin_cambios_pendientes`) — así que `_aplicar_coincidencia_albaran()` nunca llega a ejecutarse para ellas, ni siquiera para rellenar una base imponible que faltase, aunque el rellenado de v12.30.35 ya sabe hacerlo perfectamente en cuanto se le llama.

**Cambio en `app.py`**: `_comparar_listado_albaranes_logica()` (documentada hasta ahora como estrictamente "de solo lectura, no escribe nada") gana una única excepción más, con el mismo criterio ya usado en `_comparar_listado_pdf_logica()` para Total Pedido y la base imponible de la última entrada (v12.30.30/31): durante el propio cruce, si una coincidencia resulta `sin_cambios_pendientes=True` y la entrada de albarán ya registrada no tiene base imponible guardada, se rellena directamente con el importe de esa misma coincidencia — de forma silenciosa e idempotente, sin disparar notificaciones ni tocar fecha_tramitación, número de entrada nuevo ni estado (esos tres siempre requieren "Aplicar" explícito, sin cambios respecto a antes). La escritura se hace ANTES de llamar internamente a `_comparar_listado_pdf_logica()` (para la auditoría combinada), para que si ambas tocan la base imponible de la misma última entrada, el cálculo de esa función (más fiable, basado en el acumulado real de SAP) sea el que prevalezca. Nuevo contador `base_imponible_albaranes_actualizados` en el resultado.

**Cambio en `templates/index.html`**: nuevo indicador junto al resumen de "Comparar Pedidos + Albaranes" ("💾 N base imponible actualizada(s) sola(s) (ya al día)"), con el mismo estilo que el indicador equivalente de "Comparar listado PDF (SAP)".

**Qué sigue exactamente igual (nada de esto se ha tocado)**: fecha de tramitación, alta de una entrada de albarán nueva y cambio de estado siguen requiriendo confirmación explícita — a mano fila a fila con "Aplicar", con "Aplicar todas las seleccionadas", o con el aviso de confirmación automática al terminar la comparación (v12.30.32). Lo único nuevo es que una base imponible que faltaba en una fila que ya no tenía NADA MÁS pendiente ya no se queda vacía para siempre por no tener ninguna vía de aplicación que la alcance.

**Verificación**: `python3 -m py_compile app.py` sin errores. Prueba aislada en Python (parseo/reconstrucción con las mismas funciones reales del archivo): relleno de una entrada sin base imponible, no sobrescritura de una que ya la tenía, relleno de la entrada correcta en un pedido con varias entradas sin tocar las demás, coincidencia con normalización de ceros a la izquierda, sin cambio si el albarán no está registrado, sin cambio si el importe de la coincidencia es `None` — las 6 correctas. `node --check` sobre el JS extraído de `templates/index.html`, sin errores.

# v12.30.35 — 28 agosto 2026

✨ "Aplicar todas las seleccionadas" (Comparar Pedidos + Albaranes) ya rellena también la base imponible de la entrada, no solo el número y la fecha

**Petición de Víctor**: "los totales de las entregas aun estando en el estado correcto se copian si las celdas están vacías?" — tras confirmarle que no, pidió que se conectara.

**Causa**: `_aplicar_coincidencia_albaran()` (la función detrás del botón "Aplicar todas las seleccionadas" de "Comparar listado PDF" → "Coincidencias con el listado de Albaranes") es de v12.30.15, anterior a la celda "Base imp. (€)" por entrada (v12.30.31) — nunca se conectó con ella. Al registrar una entrada de albarán, solo guardaba número + fecha; el importe (la columna "Importe" que ya se ve en la propia tabla de coincidencias, el mismo con el que se emparejó pedido y albarán) estaba disponible en ese momento pero nunca se guardaba.

**Cambio en `app.py`**: `_serializar_entrada_albaran()` gana un 3er parámetro opcional `base_imponible` (retrocompatible, formato `NUM::FECHA::IMPORTE`). `_aplicar_coincidencia_albaran()` ahora:
- Al crear una entrada **nueva**, la guarda ya con su base imponible.
- Si la entrada **ya existía** (registrada antes de este cambio, o a mano) pero sin base imponible, la rellena sin tocar el número ni la fecha ya guardados, ni duplicar nada — solo si la celda estaba vacía.

**Verificación**: `python3 -m py_compile app.py` sin errores. Prueba aislada en Python: entrada nueva con importe, entrada nueva sin importe (retrocompatibilidad), relleno de una entrada existente vacía, reparseo del resultado final, y el caso sin fecha con importe — todos correctos.

# v12.30.34 — 28 agosto 2026

🐛 "Comparar listado PDF (SAP)" fallaba con `column "total_pedido" does not exist` pese a llevar desplegado desde v12.30.30 — la columna nunca llegó a crearse en Supabase

**Petición/reporte de Víctor**: al usar "Comparar listado PDF (SAP)" en Pedidos, la aplicación devolvía el error `column "total_pedido" does not exist LINE 1: SELECT id, norden, pedido_num, estado, total_pedido, entrada...` — con capturas de pantalla del modal y el aviso de error.

**Causa**: la sentencia `ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS total_pedido NUMERIC(10,2)` (añadida en v12.30.30) vivía casi al final de `_auto_migrate()`, justo antes de `db.close()` — y esa función tiene más de 100 sentencias SQL seguidas dentro de un único `try/except` sin protección individual. Si CUALQUIERA de esas otras sentencias fallaba por el motivo que fuera (sin relación con `total_pedido`), la excepción genérica paraba la ejecución ahí mismo y esta columna, al estar casi la última, nunca llegaba a crearse — sin ningún aviso visible salvo un `log.warning` genérico en los logs de Render, fácil de pasar por alto. Es exactamente el mismo patrón de fallo, ya documentado en el propio código, que en su día dejó sin aplicar la columna `sujeto_seguimiento` (bug real confirmado entonces en producción).

**Cambio en `app.py`**: la sentencia se traslada al bloque protegido que ya existe al principio de `_auto_migrate()` (el mismo que se creó para `sujeto_seguimiento` y el hotel de pruebas "PR"), con su propio `try/except` individual — así se garantiza que se intenta aplicar en cada arranque pase lo que pase con el resto de la función esa misma ejecución, y si por algún motivo fallara, quedaría un aviso específico (`No se pudo añadir la columna pedidos.total_pedido: ...`) en vez de uno genérico indistinguible de cualquier otro fallo.

**Arreglo inmediato para desbloquear ahora mismo, sin esperar al redeploy**: ejecutar directamente en el editor SQL de Supabase:
```sql
ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS total_pedido NUMERIC(10,2);
```
Es la misma sentencia, exactamente igual de segura e idempotente que la que ya corre sola en cada arranque — no hace nada si la columna ya existiera.

**Verificación**: `python3 -m py_compile app.py` sin errores. No se ha tocado `templates/index.html` en la parte de JS (solo el badge de versión), por lo que no aplica `node --check` más allá de la comprobación habitual.

# v12.30.33 — 27 agosto 2026

✨ Las coincidencias detectadas pero no aplicadas automáticamente ya no desaparecen del correo de resumen — y todos los correos de pedidos (internos y a proveedores) muestran ahora los importes (Total Pedido, entregas parciales/totales) etiquetados siempre como base imponible, sin IGIC

**Petición de Víctor**: "LA INFORMACION DE LO PENDIENTE EN CASO DE NO HACERLO AUTOMATICAMENTE SE REGISTRA TAMBIEN EN EL CORREO, POR OTRO LADO, LAS COMUNICACIONES TANTO INTERNAS COMO A LOS PROVEEDORES, DEVERAN LLEVAR TAMBIEN LOS VALORES DE ENTREGAS PARCIALES, TOTALES, TOTAL PEDIDO ETC, INDICANDO SIEMPRE QUE SE TRATAN DE BASES IMPONIBLES (TATALES SIN IGIC)" — continuación directa de la confirmación automática de entregas de v12.30.32.

**Parte 1 — pendientes que no se aplican, ahora sí quedan en el correo**: hasta ahora, si el administrador cancelaba el aviso de confirmación de v12.30.32 (o por cualquier motivo esas coincidencias no llegaban a aplicarse), esos cambios detectados simplemente desaparecían del correo de resumen — no había ningún rastro de que seguían pendientes de registrar. `comparar_listado_albaranes_enviar_resumen()` calcula ahora `coincidencias_no_aplicadas` (las que el motor de comparación pudo emparejar con seguridad, menos las que sí se aplicaron), y `_email_resumen_comparacion_albaranes()` las añade a la sección "⏳ Pendientes de realizar" con una fila explicando el motivo ("detectado — el administrador no lo confirmó al comparar; aplícalo en pantalla") y el cambio de estado que le correspondería.

**Parte 2 — importes en base imponible en todas las comunicaciones relevantes**:
- `_resumen_entregas()` incorpora ahora la base imponible de cada entrada registrada (ya guardada por v12.30.31) y calcula `total_recibido` (suma de todas las entradas con importe). `_html_bloque_entregas()` / `_text_bloque_entregas()` / `_telegram_bloque_entregas()` muestran el importe de cada entrega, la línea de total recibido, y un aviso fijo de que son importes en base imponible (sin IGIC).
- El correo interno de cambio de estado (`enviar_emails_estado()`) añade una fila "Total Pedido (base imponible)" — distinta de "Importe (techo de gastos)", que ya existía y que es un campo aparte (el importe usado para el control del Techo de Gastos mensual) — y muestra el aviso de base imponible cuando corresponde.
- El correo al proveedor de "confirmar recepción" (mismo `enviar_emails_estado()`, rama ENVIADO AL PROVEEDOR) incluye el Total Pedido cuando está disponible, con el mismo aviso.
- `_email_template_enviado_proveedor()` (recordatorio sin confirmar tras X días) y `_email_template_entrega_parcial()` (recordatorio de entrega parcial sin cerrar) incluyen ahora el Total Pedido y, en el segundo caso, el detalle completo de entregas registradas hasta la fecha (reutilizando `_html_bloque_entregas`).
- `_email_template_pendiente_firma()` añade una fila de Total Pedido cuando ya está disponible en ese momento (además del importe de techo que ya mostraba condicionalmente).
- `_email_resumen_comparacion_albaranes()` (el correo de la comparación Pedidos+Albaranes, que ya mostraba importes en sus tablas) incluye el mismo aviso de base imponible.
- Nuevo helper reutilizado en todos los puntos anteriores: `_nota_base_imponible_html()` / `_nota_base_imponible_text()`.

**Decisión de alcance, comunicada aquí para que Víctor pueda pedir lo contrario**: se ha dejado FUERA de este cambio `_email_template_pendiente_cotizacion()` y `_email_template_cotizacion_sin_proveedor()` (recordatorios de cotización pendiente) — en esa fase del pedido (antes de tramitarlo) el Total Pedido normalmente todavía no está cumplimentado, así que añadir la fila ahí no aportaría información real la mayoría de las veces. Si se prefiere incluirla igualmente (por si en algún caso sí está disponible), se puede añadir sin más.

**Verificación**: `python3 -m py_compile app.py` sin errores. No se ha tocado `templates/index.html` en este cambio (es íntegramente de backend/plantillas de correo), por lo que no aplica `node --check`.

# v12.30.32 — 27 agosto 2026

✨ "Comparar Pedidos + Albaranes": al terminar la comparación, un único aviso pregunta si registrar automáticamente las entregas que falten — antes había que revisar la tabla fila a fila y pulsar "Aplicar" a mano

**Petición de Víctor**: "en la comparación de pedidos, cuando las entregas parciales o totales no existen registradas en controlpedidos, la aplicación las registrará automáticamente cambiando también automáticamente los estados al que corresponda, entrega parcial o entrega total. Solo preguntar al finalizar la comparación y con aceptar por parte del administrador se realizará automáticamente, en el envío del correo con la info se detallarán los cambios automáticos realizados. La creación de pedidos no registrados por ahora será solicitada en dicho correo y lo deberá realizar manualmente el comprador." Le pregunté qué número de entrada usar para registrar automáticamente, dado que el PDF de un solo listado (Pedidos) no trae ningún número de albarán DALI — aclaró que el registro automático **solo** debe activarse cuando se aportan los DOS listados (Pedidos + Albaranes), usando el número de registro que ya trae el segundo listado.

**Nada que construir en el backend**: revisando `/api/pedidos/comparar-listado-albaranes/<job_id>/aplicar` (v12.30.15) resultó que YA existía todo el mecanismo necesario — acepta `{"todas": true}` para aplicar de una vez TODAS las coincidencias propuestas (nueva entrada de albarán + cambio de estado a ENTREGA PARCIAL/ENTREGADO vía `_aplicar_coincidencia_albaran()`), y el correo de resumen (`_email_resumen_comparacion_albaranes`) ya incluye una sección "✅ Registrados automáticamente" con el detalle de cada cambio aplicado. Lo único que faltaba era la forma de disparar ese "aplicar todas" — hasta ahora solo un botón manual al final de una tabla de revisión fila a fila.

**Cambio en `templates/index.html`**: en cuanto termina la comparación de los dos PDF (Pedidos + Albaranes), si hay alguna coincidencia con cambios reales pendientes (excluyendo las que ya estaban al día), se muestra un único aviso con el recuento y el detalle (pedido → estado destino) preguntando si registrarlas automáticamente ahora. Si el administrador acepta, se llama al mismo endpoint `.../aplicar` con `{todas:true}` — igual que pulsar "Aplicar todas las seleccionadas" a mano, solo que ahora se ofrece directamente al terminar, sin tener que bajar a la tabla. Si cancela, no se toca nada — la tabla de revisión sigue disponible exactamente igual que antes, para aplicar manualmente fila a fila o más tarde.

**Cambio en `app.py`**: el correo de resumen conjunto (`_email_resumen_comparacion_albaranes`) añade, junto a la lista de "Pedidos de SAP sin dar de alta en la app", el mismo aviso explícito que ya tenía el correo del listado de un solo PDF — pidiendo al comprador que dé de alta manualmente esos pedidos, ya que la creación automática de pedidos nuevos queda fuera de alcance por ahora (a petición explícita de Víctor).

**Verificación**: `python3 -m py_compile app.py` sin errores. `node --check` sobre el JS extraído de `templates/index.html`, sin errores.

# v12.30.31 — 27 agosto 2026

✨ Nueva celda "Base imp. (€)" junto a cada entrada DALI/SAP, rellenada automáticamente al comparar el listado de SAP con la base imponible real de ese albarán concreto

**Petición de Víctor**: "del mismo modo, añadir junto a las entradas también una celda donde introducir siempre la base imponible de las entradas, indicar que siempre se indicará la base imponible del albarán. Esta celda también será opcional, completando la misma con el listado de pedido en comparación, si la entrega es parcial, se completa con el valor de la columna 7, si la entrega es total con la 7. Se deberá verificar las entradas parciales que pudieran existir y restar el valor de las celdas existentes para poder saber el correspondiente a la última entrega, en caso de total igual, se restará la suma de las entradas parciales si las hubiera y se cumplimentará la celda con el resultado, en caso de no existir entradas parciales el valor de la celda será el total de la columna 7. El valor de la columna 6 es la base imponible del pedido original" — "del mismo modo" que el Total Pedido de v12.30.30: automático, sin confirmación, pero editable a mano si se quiere.

**Diferencia clave con Total Pedido**: SAP solo da un importe recibido ACUMULADO por pedido (columna 7), no desglosado por albarán — así que no basta con copiar la columna 7 en la entrada más reciente: hay que descontar antes lo que ya corresponde a entregas parciales anteriores del mismo pedido.

**Cambio en `app.py`**: el formato de `pedidos.entrada_albaran_num` (ya "NUM::FECHA" por entrada, separadas por " | ") gana un tercer segmento opcional — "NUM::FECHA::BASE_IMPONIBLE" — retrocompatible con entradas antiguas sin ese segmento (`_parse_albaran_entries`, `format_albaran_display`, ambas actualizadas; nueva `_construir_entrada_albaran_num` para reescribir una sola entrada sin tocar las demás). `_comparar_listado_pdf_logica()` (el mismo motor de v12.30.30) calcula, para cada pedido localizado que ya tenga al menos una entrada registrada: base imponible de la ÚLTIMA entrada = importe recibido acumulado del PDF (columna 7) menos la suma de las bases imponibles YA registradas en las entradas anteriores de ese pedido — si no hay ninguna anterior, el valor es directamente la columna 7 completa. Se aplica igual tanto en "Entrega parcial" como en "Entregado" (en una entrega total la columna 7 coincide con el total del pedido, así que el resultado es el mismo). Si el resultado saliera negativo (datos ya inconsistentes), no se escribe nada — se deja en blanco para revisión manual en vez de guardar un importe sin sentido. Solo se toca si el pedido ya tiene alguna entrada creada — esto nunca inventa una entrada nueva, solo rellena la base imponible de la última que ya exista.

**Cambio en `templates/index.html`**: nueva celda "Base imp. (€)" en cada fila de la lista de entradas DALI/SAP (junto a Nº de entrada y Fecha), editable a mano — mismo criterio de opcionalidad que pidió Víctor. El resumen de "Comparar listado PDF" muestra ahora también cuántas de estas celdas se han actualizado en esta pasada.

**Verificación**: `python3 -m py_compile app.py` sin errores. Suite de pruebas aisladas en Python del parseo/reconstrucción del nuevo formato de 3 segmentos (retrocompatibilidad con "NUM", "NUM::FECHA", ida y vuelta con "NUM::FECHA::IMPORTE", y `format_albaran_display` con y sin base imponible) — todas correctas. `node --check` sobre el JS extraído de `templates/index.html`, sin errores.

# v12.30.30 — 27 agosto 2026

✨ Nuevo campo "Total Pedido" en la ficha del pedido, rellenado automáticamente al comparar el listado de SAP (sin necesidad de escribirlo a mano)

**Petición de Víctor**: "cuando se realiza la comparación de listados, podemos insertar el total del pedido localizado en un apartado TOTAL PEDIDO que aun no existe en la ventana creación edición pedido? la idea es que este valor no lo tenga que introducir manualmente el comprador al generar o editar el pedido (si lo puede hacer si quiere) pero que al introducir el PDF y localizar el pedido la aplicación lo cumplimente como valor real del pedido. El valor será la columna sexta del PDF PEDIDOS" — adjuntó también un PDF real del "Listado de Pedidos" de SAP para identificar la columna. Revisando la extracción ya existente (`_PATRON_LISTADO_SIMPLIFICADO`, usada en "Comparar listado PDF"), la 6ª columna visual del PDF (justo después del proveedor) ya se extraía y usaba internamente como `importe_base` — la base imponible del pedido en SAP — así que no hacía falta tocar el parseo, solo guardarla en un campo nuevo.

**Cambio en `app.py`**: nueva columna `pedidos.total_pedido` (NUMERIC, opcional). `POST/PUT /api/pedidos` la aceptan y guardan igual que el resto de campos del formulario — el comprador puede escribirla a mano si quiere, exactamente como pidió Víctor. Además, `_comparar_listado_pdf_logica()` (el motor de "Comparar listado PDF", usado tanto por la comparación de un solo PDF como por la combinada con Albaranes) ahora guarda `total_pedido = importe_base` directamente en cada pedido localizado, sin pedir confirmación — única excepción a la filosofía de "solo propone, nunca escribe sola" del resto de esta función, justificada porque es un campo puramente informativo (no dispara emails ni cambia el estado del pedido, a diferencia de un cambio de entrega). Solo escribe cuando el valor cambia de verdad, para no generar escrituras de más si se compara el mismo listado varias veces.

**Cambio en `templates/index.html`**: nuevo campo "Total Pedido (€)" en la ficha del pedido, junto a "Nº Pedido (DALI/SAP)" y "Nº Presupuesto". El resumen de "Comparar listado PDF" muestra ahora cuántos "Total Pedido" se han actualizado en esta pasada, para que quede constancia en pantalla de que se ha escrito algo en la base de datos.

**Verificación**: `python3 -m py_compile app.py` sin errores. `node --check` sobre el JS extraído de `templates/index.html`, sin errores.

# v12.30.29 — 27 agosto 2026

✨ Techo de Gastos: al aprobar un apunte navegando directamente a esa sección (sin venir de un intento bloqueado en la ficha del pedido), la aplicación vuelve a la ficha del pedido y avisa de que ya está ENVIADO AL PROVEEDOR

**Petición de Víctor**, continuando el fix de v12.30.28: "cuando se aprueba el techo de gasto se debera devolver a la ventana de pedido y con un aviso en pantalla indicar que ya se puede cambiar el estado a ENVIADO AL PROVEEDOR indicando las observaciones que precise necesarias". Antes de tocar nada, se revisó `aprobar_expediente()` en `app.py`: al aprobar, el backend YA cambia el pedido a `ENVIADO AL PROVEEDOR` automáticamente en ese mismo momento (incluye email al proveedor) — no hay ningún cambio de estado manual pendiente que hacer. Se lo planteé a Víctor con una pregunta directa y matizó su petición: "puede ser que si se llego a este punto desde la ventana de pedido al intentar cambiar el estado a ENVIADO entonces si se termine el proceso automaticamente como esta, pero si se llega al apartado TECHO DE GASTO y se acepta sin pasar por pedido, entonces si abra directamente la ventana e indique al usuario lo comentado para cambiar el estado" — es decir: comportamiento distinto según de dónde venga la aprobación.

**Cambio en `templates/index.html`**: `guardarPedido()` anota ahora en `G._techoOrigenPedidoExpId` el id del expediente que provoca su redirect automático a Techo de Gastos (v12.30.28). `resolverExpedienteTecho()` compara ese id contra el expediente que se acaba de aprobar: si coincide (el usuario viene justo de esa ficha, acaba de cerrarla), se deja el comportamiento actual sin cambios — un toast de confirmación, sin volver a abrir nada. Si NO coincide (aprobación hecha revisando Techo de Gastos por su cuenta, sin haber pasado por esa ficha en este mismo intento), se abre automáticamente `openPedidoModal()` de ese pedido y se muestra un aviso en pantalla (`showFormAlert`, el mismo mecanismo de aviso que ya usa el resto de la ficha) confirmando que el pedido ya se ha enviado al proveedor — sin pedirle que cambie nada más a mano, porque el backend ya lo hizo.

**Cambio en `app.py`**: la respuesta de `POST /api/expedientes/<id>/aprobar` incluye ahora `pedido_id`, necesario para que el frontend sepa qué ficha reabrir en el caso anterior.

**Verificación**: `python3 -m py_compile app.py` sin errores. `node --check` sobre el JS extraído de `templates/index.html`, sin errores.

# v12.30.28 — 27 agosto 2026

🐛 Pedidos → ENVIADO AL PROVEEDOR: dejar de duplicar el apunte de Techo de Gastos en cada reintento — y llevar directamente a Víctor a resolverlo en vez de dejarle reintentar a ciegas

**Petición/reporte de Víctor**: "en controlpedidos, apartado pedidos, cuando un pedido que tiene estado PENDIENTE FIRMA DIRECCION GENERAL y se intenta pasar a ENVIADO AL PROVEEDOR, se genera un apunte en el apartado TECHO DE GASTO y es aqui donde hay que aceptar finalmente para que el pedido pase correctamente a ENVIADO AL PROVEEDOR. El problema esta en que si el usuario no se da cuenta e insiste en cambiar el formato a ENVIADO AL PROVEEDOR, se generan tantos apuntes en el apartado TECHO DE GASTO como intentos se realice, multiplicando este apunte tantas veces como intentos se realicen. Esto es un error y pienso se soluciona facilmente si cuando se realiza el intento de cambio a ENVIADO la aplicacion abre directamente el apartado TECHO DE GASTO y realiza el comentario que se debe aceptar el apunte o algo por el estilo para terminar este proceso, no duplicando nunca este apunte y solo dando opcion del camino de estado aceptando este paso pero sin tener que acordarse e ir por su cuenta".

**Causa**: en `update_pedido()`, dentro del circuito de autorización de Techo de Gastos (rediseño Fase 2, 01-08-2026), cuando un pedido `sujeto_techo` no tiene ya un `expediente_exceso` **aprobado** para el mes, se vuelve a llamar a `_check_techo()` y, si sigue habiendo motivos de exceso, se inserta un nuevo `expediente_exceso` con `resultado='pendiente'` — sin comprobar antes si YA existe uno pendiente sin resolver para ese mismo pedido. Cada reintento desde la ficha del pedido (típico cuando alguien insiste en cambiar a ENVIADO AL PROVEEDOR sin saber que ya hay un apunte esperando su Vº Bº en Techo de Gastos) volvía a pasar por esa misma rama y creaba OTRO expediente pendiente más — tantos como intentos, exactamente como describe Víctor.

**Cambio en `app.py`**: antes de volver a comprobar el techo, se busca si el pedido ya tiene un `expediente_exceso` con `resultado='pendiente'`. Si lo tiene (y no hay ninguno aprobado para el mes), la petición se corta ahí — nunca se crea un segundo apunte — y se devuelve `422` con `expediente_pendiente_id` y `hotel_codigo`, la misma familia de respuesta que ya usa el resto de validaciones de negocio de "ENVIADO AL PROVEEDOR" (`esValidacionDeNegocio` en `templates/index.html`, así el frontend la trata como dato normal en vez de lanzar una excepción).

**Cambio en `templates/index.html`**: `guardarPedido()` reconoce ahora `r.expediente_pendiente_id` — cierra el modal del pedido, muestra un aviso, y lleva directamente a la sección Techo de Gastos con la tarjeta del hotel correspondiente ya resaltada (reutilizando `irATechoHotel()`, la misma función que ya usa el resto de la app para este tipo de navegación), en vez de dejar el mensaje perdido en la ficha del pedido y al usuario sin saber a dónde ir. Ahí, en la tarjeta de "Pendientes de Vº Bº Dirección General", es donde ya existía la opción de Aprobar/Denegar (`resolverExpedienteTecho()`) — sin necesidad de nada nuevo en esa parte.

**Nota importante**: este cambio evita que se generen NUEVOS duplicados a partir de ahora, pero no fusiona ni borra los apuntes pendientes duplicados que ya se hayan creado antes de este despliegue por el mismo motivo — esos habrá que resolverlos (aprobar/denegar) a mano uno a uno en Techo de Gastos, o pedir un script de limpieza puntual si se prefiere automatizarlo.

**Verificación**: `python3 -m py_compile app.py` sin errores. `node --check` sobre el JS extraído de `templates/index.html` (8 bloques `<script>`, 178.889 caracteres), sin errores.

# v12.30.27 — 27 agosto 2026

✨ Nuevo endpoint `GET /api/externo/dali-sap/proveedores`: DALI puede usar los contactos (nombre/email/es_principal) de "Proveedores" de esta app como destinatario de sus correos de documentación faltante, en vez de mantener un único email duplicado en su propia base

**Petición de Víctor**, sobre el puente de correos de v12.30.26: "imagino que el control de envios sigue descontando tambien estos ecolados - por otro lado como vamos a utilizar el sistema de envios de control_pedidos, podriamos utilizar tambien el apartado de proveedores con sus correos electronicos etc? de esta manera los tenemos unicamente en un unico punto y podemos incluir mas correos para el envio, ahora en articulos es solo uno". Confirmado lo primero: el contador de EmailJS (`emailjs_contador`, ver panel "Config Alertas") se incrementa igual para estos correos — pasan por el mismo `enviarEmailJS()`/`registrar-envio` que cualquier otro de la cola, no hay ningún camino que los salte.

**Cambio en `app.py`**: nuevo `GET /api/externo/dali-sap/proveedores`, misma autenticación por firma HMAC que `POST .../emails-pendientes` (v12.30.26), devuelve los proveedores activos de esta app con sus contactos (reutilizando `_prov_with_contactos`, la misma función que ya usa `GET /api/proveedores`) — nombre, `email_principal` (el contacto marcado como principal, o el primero si no hay ninguno) y la lista completa de contactos con email. DALI cruza por NOMBRE exacto contra su propio catálogo (Víctor va a mantener los nombres de proveedor idénticos entre las dos apps a propósito, para poder trabajar "sobre una única base" sin mantener un mapeo id-a-id aparte) y usa el contacto principal como destinatario — si un proveedor no tiene contacto marcado como principal en esta app, sigue funcionando igual que antes (usa el primero), así que nadie pierde alcance respecto al email único que tenía guardado en DALI.

**Verificación**: `python3 -m py_compile app.py` sin errores.

# v12.30.26 — 27 agosto 2026

✨ Puente de correos desde el catálogo DALI (`dali-sap-articulos-app`): nuevo endpoint para que sus correos de "documentación faltante" usen la misma cola y el mismo envío por EmailJS que ya tiene esta app, con logo y colores en vez de texto plano

**Petición de Víctor**: "podemos aprovechar la organizacion que tenemos actualmente en controlpendidos para el envio de correos y que los correos de dalisaparticulos utilice la misma infraestuctura? la idea es que los correos para la solicitud de documentacion faltante utilice este metodo de emailjs, se podria generar dejar en cola y cuando alguien abra control de pedidos se lance, de esta manera podriamos reestructurar y hecer mas atractivo y profecional los correos electronicos, con logo colores etc". La reclamación de documentación pendiente a un proveedor la generaba DALI como texto plano para copiar o abrir en el cliente de correo del propio Víctor — sin envío real ni diseño.

**Cambio en `app.py`**: nuevo `POST /api/externo/dali-sap/emails-pendientes`, sin sesión de usuario (es una llamada servidor a servidor desde el backend Node de DALI, no desde un navegador con cookie de esta app) pero protegido con una firma HMAC-SHA256 del cuerpo de la petición usando el secreto YA compartido entre ambos servicios de Render (`DALI_SSO_SECRET`, hasta ahora solo usado para el SSO del menú lateral "Catálogo DALI") — nada nuevo que configurar en Render. El correo recibido se inserta directamente en `emails_sistema_pendientes` (`evento_codigo='dali_documentacion_faltante'`) y lo despacha el poller que ya existe (`_enviarEmailsSistemaPendientes`, cada 5 min con sesión admin/compras abierta), sin ningún cambio en el frontend de esta app. A petición de Víctor, comparte la cuenta EmailJS activa de esta app en vez de tener una cuenta dedicada — entra en la rotación normal entre las 3 cuentas si hiciera falta. Ver el repo de DALI (su propio `CHANGELOG.md`/`HISTORIAL.md`) para el lado que genera y envía estos correos.

**Verificación**: `python3 -m py_compile app.py` sin errores.

# v12.30.25 — 22 agosto 2026

🔧 SSO hacia DALI: el token de acceso automático subía de 60s a 100s de duración — evita que caduque durante un cold-start normal del backend de DALI (plan gratuito de Render)

**Petición/reporte de Víctor**: en el catálogo DALI, el primer acceso del día tardaba mucho y se quedaba en "Comprobando sesión…", y entrando por el enlace "Catálogo DALI" desde aquí a veces caía al login manual con un aviso de acceso fallido, aunque las credenciales fueran correctas. Diagnosticado en el propio repo de DALI (ver su `HISTORIAL.md`, v0.60): el backend de DALI vive en el plan gratuito de Render, que duerme tras 15 min sin tráfico y tarda ~60s (a veces más) en despertar — y el token de SSO que genera este backend (`_generar_token_sso_dali`) solo duraba 60s (70s contando el margen de reloj del lado de DALI), una ventana casi calcada al propio cold-start, sin margen real. Como primer parche (mismo día, solo en DALI) se amplió el margen de aceptación en ese lado a 90s; este cambio es el arreglo de raíz en el origen del token, con el visto bueno explícito de Víctor para tocar este repo.

**Cambio en `app.py`**: `_generar_token_sso_dali`, el parámetro `ttl_segundos` sube de 60 a 100 — cubre un cold-start normal de Render con margen de sobra por sí solo. Coordinado con DALI: su margen de aceptación (`SSO_MARGEN_RELOJ_SEGUNDOS` en `authController.js`) baja de 90s a 20s en el mismo cambio, volviendo a ser solo margen real de reloj/latencia en vez de sustituto del TTL. Ventana total efectiva: ~120s (antes ~150s, pero repartidos de forma menos correcta: 60s de TTL + 90s de parche).

**Verificación**: `python3 -m py_compile app.py` sin errores.

# v12.30.24 — 20 agosto 2026

🐛 Recordatorio de "correos de sistema en cola": seguía avisando de filas ya descartadas o ya paradas por el freno de reintentos, con un título de popup engañoso ("Nueva solicitud de acceso")

**Petición/reporte de Víctor**: justo después de descartar a mano los 4 correos atascados desde el nuevo panel de admin (v12.30.22), le llegó un aviso emergente titulado "📋 Nueva solicitud de acceso" cuyo cuerpo decía "Hay 4 emails de sistema en cola sin enviar (resumen_comparacion_albaranes), esperando a que alguien abra la aplicación para despacharlos automáticamente" — justamente sobre las mismas 4 filas que acababa de descartar, con un título que no tenía nada que ver con el contenido real del aviso.

**Causa (dos fallos en el mismo job)**: `_job_recordar_emails_sistema_pendientes()` (corre cada 10 min, 07:00–21:00) avisa por Telegram/popup cuando hay filas `enviado = FALSE` sin recordar en los últimos 30 minutos — pero su consulta nunca excluía las filas ya descartadas a mano (`descartado_en`) ni las que ya agotaron sus reintentos (`intentos >= MAX_INTENTOS_EMAIL_SISTEMA`, ver v12.30.21/22): las seguía contando como "pendientes" para siempre y avisando de ellas cada 30 minutos, aunque abrir la aplicación no fuera a hacer nada por ellas (una está descartada a propósito, la otra ya no se reintenta sola). Además, el job reutilizaba `_notify_solicitud_telegram()` — pensada para avisos de solicitudes de acceso (Fase 1/2) — que lleva fijo el título de popup "📋 Nueva solicitud de acceso", sin relación con este aviso.

**Cambio en `app.py`**: la consulta del job añade `AND descartado_en IS NULL AND intentos < MAX_INTENTOS_EMAIL_SISTEMA`, así que una fila descartada o ya parada por el freno deja de generar recordatorios. El job ahora llama a `_notificar_evento()` directamente (mismos destinatarios configurados que antes, evento `solicitud_acceso`, sin cambios ahí) pero con un título de popup correcto: "⏰ Correos de sistema en cola".

**Verificación**: `python3 -m py_compile app.py` sin errores.

# v12.30.23 — 20 agosto 2026

🐛 Envíos automáticos por EmailJS: correo real duplicado cuando fallaba la confirmación tras un envío exitoso — explica los reenvíos y el consumo de cupo que seguía subiendo con la cola ya vacía

**Petición/reporte de Víctor**: tras desplegar v12.30.22, el panel de "Cola de correos de sistema pendientes" mostraba solo 4 filas antiguas ya descartadas/agotadas (0 filas activas) y aun así "ya paso a 116 emailjs" — el cupo siguió bajando pese a que la cola visible estaba limpia.

**Causa**: en `_enviarEmailsSistemaPendientes()` (el poller que envía la cola de sistema vía EmailJS desde el navegador), el flujo era: 1) `emailjs.send(...)` (el correo YA se envía de verdad aquí) y 2) `POST /marcar-enviado` para que el backend no lo vuelva a ofrecer. Si el paso 2 fallaba por cualquier motivo (red, sesión caducada, pestaña recargándose a media faena...) el `catch` solo registraba un aviso en consola y seguía — la fila se quedaba `enviado = FALSE` en la base de datos aunque el correo SÍ se hubiera entregado. Pasados los 2 minutos de reserva, esa misma fila volvía a ofrecerse al siguiente sondeo (el propio, u otra pestaña abierta) y se reenviaba DE VERDAD por EmailJS — un duplicado real al destinatario, no un simple 413 fallido, descontando cupo con éxito en cada reenvío. Esto encaja exactamente con los 3 correos de resumen idénticos que Víctor encontró antes en su bandeja de "Enviados" a distintas horas, y explica por qué el cupo seguía bajando incluso con la cola de "atascados" ya completamente vacía tras v12.30.22 — el problema no estaba en filas atascadas sin enviar, sino en filas que SÍ se enviaban pero no lograban confirmarse.

**Cambio en `templates/index.html`**: la confirmación (`marcar-enviado`) se reintenta ahora hasta 3 veces con una breve espera entre intentos antes de darse por vencida, para que un fallo puntual de red no deje la fila "viva" para un reenvío real. Si aun así las 3 confirmaciones fallan, se registra un error claro en consola indicando que ese correo concreto puede reenviarse duplicado en el próximo sondeo — visibilidad que antes no existía (antes era un simple `console.warn` genérico e indistinguible de un fallo de envío real).

**Verificación**: `node --check` sobre el JS extraído de `templates/index.html`, sin errores.

# v12.30.22 — 20 agosto 2026

🐛 Cola de emails de sistema: bajar el margen de reintentos y ampliar el panel de admin a toda la cola pendiente — filas atascadas desde antes de v12.30.21 seguían descontando cupo de EmailJS tras desplegar el freno

**Petición/reporte de Víctor**: tras desplegar v12.30.21 (freno de reintentos infinitos), volvió a probar y "de 76 emailjs paso a 91 y un solo correo enviado" — 15 peticiones descontadas de golpe, con un único correo (el resumen de esta prueba) realmente enviado. Preguntó si podía ser cola acumulada de antes.

**Causa**: confirmado — sí es cola acumulada de antes de hoy. El freno de v12.30.21 añadió la columna `intentos` con `ALTER TABLE ... ADD COLUMN IF NOT EXISTS intentos INTEGER NOT NULL DEFAULT 0`: esto rellena a **0** el contador en las filas que YA estaban en la cola (las oversized de pruebas anteriores a v12.30.20, con el HTML grande de antes del recorte adaptativo). Es decir, esas filas arrancaron con el cupo de reintentos completo por delante en vez de con los intentos que ya llevaban acumulados — así que, tras el propio despliegue del freno, cada una pudo fallar y descontar cupo hasta 8 veces más (el límite de v12.30.21) antes de pararse sola, sin que nada de eso fuera visible en el panel de "Correos atascados" (que solo mostraba filas que ya hubieran agotado esos intentos). La captura de red del último intento de Víctor confirma este diagnóstico: los 4 fallos 413 ocurren en la PRIMERA llamada a `emails-sistema-pendientes` (280 kB de respuesta), antes incluso de invocarse "Enviar resumen" para esta prueba — son filas viejas, no el correo nuevo (que se envió bien a la primera).

**Cambio en `app.py`**: `MAX_INTENTOS_EMAIL_SISTEMA` bajado de 8 a 3 — acorta el margen de "cupo regalado" que las filas ya atascadas desde antes de hoy pueden seguir gastando tras cada despliegue del freno, sin penalizar reintentos legítimos por fallos puntuales de red. `GET /api/admin/emails-sistema-atascados` ampliado para listar TODA la cola pendiente (`enviado = FALSE`), no solo las filas que ya agotaron los intentos — ordenadas por tamaño de HTML descendente (las más grandes, más sospechosas de fallar por 413, arriba del todo) y con un nuevo campo `atascado` para distinguir "parado" de "aún reintentando".

**Cambio en `templates/index.html`**: el panel Admin → Config alertas → EmailJS ("Cola de correos de sistema pendientes") ahora muestra la cola completa, con una etiqueta de estado por fila ("reintentando" / "parado (agotó reintentos)" / "descartado") — el botón "Descartar" sigue disponible en cualquier fila, sin esperar a que se pare sola: Víctor puede entrar ahora mismo y descartar a mano las filas grandes que sigan drenando cupo, en vez de esperar a que agoten sus 3 intentos.

**Verificación**: `python3 -m py_compile app.py` sin errores. `node --check` sobre el JS extraído de `templates/index.html`, sin errores.

# v12.30.21 — 19 agosto 2026

🐛 Cola de emails de sistema: freno de reintentos infinitos — un correo que fallaba SIEMPRE al enviarse descontaba cupo de EmailJS sin límite, sin llegar nunca a entregarse

**Petición/reporte de Víctor**: tras desplegar v12.30.20 (límite de tamaño conjunto del correo de resumen), probó de nuevo y "estaba en 54 emailjs y pasó a 71" — 17 peticiones descontadas sin que llegara ningún correo nuevo.

**Causa**: el fix de tamaño de v12.30.20 solo cambia cómo se CONSTRUYE un correo nuevo al encolarlo — no toca el contenido de una fila que ya llevaba encolada desde ANTES del despliegue, con el HTML antiguo (más grande, generado con el código previo). Esa fila, generada en las pruebas anteriores a hoy, seguía fallando siempre (413 — el motivo original de todo este hilo) y, como `emails_sistema_pendientes` no tenía ningún límite de reintentos, la reserva de la fila caducaba sola cada 2 minutos y volvía a reintentarse indefinidamente desde cualquier sesión abierta — descontando cupo de EmailJS en cada intento, con o sin éxito, para siempre, sin que nadie lo viera.

**Cambio en `app.py`**: nuevas columnas `intentos` (contador, se incrementa en cada reclamo atómico de la fila) y `descartado_en` (descarte manual) en `emails_sistema_pendientes`. `GET /api/emails-sistema-pendientes` deja de devolver/reintentar una fila al llegar a `MAX_INTENTOS_EMAIL_SISTEMA` (8) intentos sin éxito, o si se descartó a mano — se para sola en vez de sangrar cupo indefinidamente. Nuevos endpoints de admin: `GET /api/admin/emails-sistema-atascados` (lista las filas que agotaron intentos o se descartaron) y `POST /api/admin/emails-sistema-pendientes/<id>/descartar` (descarte manual).

**Cambio en `templates/index.html`**: Admin → Config alertas → EmailJS muestra ahora, cuando hay alguno, un aviso "⚠️ Correos atascados — agotaron los reintentos sin enviarse" con asunto, destinatario, nº de intentos, tamaño y un botón "Descartar" por fila — visibilidad que antes no existía en absoluto (el drenaje de cupo era completamente invisible desde la aplicación).

**Nota importante**: con este cambio, la fila que llevaba fallando desde antes de hoy dejará de reintentarse sola en cuanto acumule 8 intentos (puede que ya los tenga, en cuyo caso se para en el propio despliegue) — no hace falta ninguna intervención manual en la base de datos. Aparecerá en el nuevo panel de "Correos atascados" para poder revisarla/descartarla.

**Verificación**: `python3 -m py_compile app.py` y `node --check` sobre el JS de `templates/index.html`, sin errores. Migración (`ALTER TABLE ... ADD COLUMN IF NOT EXISTS`) idempotente, vía `_auto_migrate()`, como el resto de columnas de esta tabla.

# v12.30.20 — 19 agosto 2026

🐛 Correo de resumen de "Comparar Pedidos + Albaranes": recorte de tamaño definitivo — límite conjunto en vez de tres límites independientes

**Petición de Víctor**: "llego un correo con el resumen pero descontó casi 10 correos en emailjs, en F12 salen varios intentos fallidos".

**Causa**: el fix de v12.30.15 (y el de hace un momento, ampliando el recorte a "sin dar de alta" y "registrados automáticamente") acotaba cada una de las 3 tablas del correo (📋 sin dar de alta, ✅ registrados automáticamente, ⏳ pendientes de realizar) por SEPARADO, con un límite de filas fijo cada una. El problema: un límite fijo por tabla no evita que la SUMA de las tres, cuando las tres tienen muchas filas a la vez (como el caso real de Víctor), siga superando el límite real de tamaño de EmailJS — simulación con 120 "sin dar de alta" + 90 "registrados" + 79 "pendientes" (los tres recortados a 50 cada uno, el límite anterior): 62.083 caracteres, muy por encima del límite conocido que causa 413. Eso explica el síntoma: el correo llegó, pero después de que ~10 intentos anteriores (con contenido ligeramente distinto en cada recomparación) fallasen por tamaño y descontasen cupo igualmente.

**Cambio en `app.py`**: `_email_resumen_comparacion_albaranes()` reescrita para probar varios niveles de recorte cada vez más agresivos — (50,50,50) → (30,30,25) → (15,15,12) → (6,6,5) filas por tabla — y quedarse con el primer resultado cuyo tamaño total quede por debajo de un margen de seguridad (22.000 caracteres, con margen respecto al caso real conocido: 24.002 caracteres SÍ llegó, 36.445 dio 413). Ya no hay tres límites fijos independientes — el correo se recorta lo justo para entrar dentro del margen conocido, sea cual sea la combinación de tamaños de las tres tablas. La pantalla sigue sin ningún límite, como siempre — el listado completo se ve siempre ahí.

**Verificación**: `python3 -m py_compile app.py` sin errores. Simulación aislada con el caso extremo (120/90/79 filas grandes en las tres tablas a la vez): el resultado ahora recorta automáticamente hasta 19.078 caracteres (nivel de recorte (15,15,12)), por debajo del margen de seguridad. El caso real de 79 "pendientes" solos (sin las otras dos tablas) se queda en el primer nivel (50,50,50) con 16.264 caracteres, sin recorte adicional innecesario.

# v12.30.19 — 19 agosto 2026

✏️ Correo de cambio de estado: excluir solo a la persona que hizo el cambio (no a todo su rol) — y 🐛 Comparar Pedidos + Albaranes: dejar de mostrar como "pendiente" un pedido ya ENTREGADO solo porque SAP aún marca un pequeño importe pendiente (caso pedido 42644)

**Petición de Víctor (correo)**: tras v12.30.18, aclaró que la exclusión debía ser "solo se excluya a la persona concreta" — no a todo el lado/rol (comprador u hotel) de quien hizo el cambio, porque un hotel o un departamento de compras puede tener más de una persona con acceso y las demás sí deben seguir recibiendo el correo.

**Cambio en `app.py` (correo)**: `enviar_emails_estado()` ya no calcula un "lado actor" (comprador/hotel) a partir del rol de `usuario_id` — ahora consulta directamente el email (y email2) de esa persona y lo quita de la lista de destinatarios del correo interno (`compradores + usuarios hotel`), dejando a todos los demás —incluidos sus compañeros del mismo rol— con el correo normal. Con `es_automatico=True` o sin `usuario_id` conocido, se sigue mandando a todos, sin excluir a nadie, igual que antes.

---

**Petición de Víctor (comparativa)**: "seguimos con problemas de identificación aun enviando el listado desde el 01-05-2026 ; sigue identificando el pedido 42644 como entrega parcial" — con capturas y, en este mensaje, los dos PDF completos (listado de pedidos y de albaranes del hotel FV) para revisar el caso.

**Causa**: revisando los PDF adjuntos, el pedido SAP `00042644` (proveedor ABEL LORENZO HENRIQUEZ) tiene base imponible 1.513,35 € pero SAP solo registra 1.274,40 € como "recibido" (238,95 € pendientes según SAP) — por eso `_entrega_estado()` lo clasifica como "Entrega parcial". El pedido, sin embargo, ya está marcado `ENTREGADO` en la app (esos 1.274,40 € coinciden exactamente con el albarán DALI `00081970` del 06/08/2026, ya registrado). `_aplicar_coincidencia_albaran()` ya protegía este caso correctamente (no retrocede un pedido `ENTREGADO` a `ENTREGA PARCIAL`, ver v12.30.16/17 y comentario "no retroceder el estado"), pero **la comparativa en sí** no tenía en cuenta esa misma protección al construir la fila de "coincidencia": seguía calculando `estado_objetivo = ENTREGA PARCIAL` y mostrando "ENTREGADO → ENTREGA PARCIAL" como si aplicar la coincidencia fuera a retroceder el pedido — así que cada comparación (aunque se subiera un listado de SAP que cubriera bien la fecha) volvía a presentar el pedido 42644 como pendiente de revisión, sin que hubiera realmente nada que hacer.

**Cambio en `app.py`**: nueva constante `_ORDEN_ENTREGA_ESTADOS` (fuente única, antes duplicada como variable local dentro de `_aplicar_coincidencia_albaran()`), usada ahora también en `_comparar_listado_albaranes_logica()` al construir cada "coincidencia": se calcula `estado_ya_avanzado` (el pedido ya está, en la app, en un estado más avanzado — ENTREGADO — que el que propone SAP para esta línea) y se usa junto con `ya_registrado` para decidir `sin_cambios_pendientes` — si el albarán ya está registrado y el pedido no va a cambiar de estado (ni porque ya coincide, ni porque ya está por delante), la fila se marca como resuelta (se atenúa, checkbox desmarcado) igual que las demás coincidencias sin acción pendiente, en vez de reaparecer indefinidamente. Se añade también el campo `estado_ya_avanzado` a la respuesta.

**Cambio en `templates/index.html`**: cuando `estado_ya_avanzado` es cierto, la columna de estado ya no muestra "ENTREGADO → ENTREGA PARCIAL" — muestra "ENTREGADO (ya en un estado más avanzado — SAP aún lo muestra como ENTREGA PARCIAL)", dejando claro que no hay ningún retroceso real y por qué sigue apareciendo en el PDF de SAP.

**Verificación**: `python3 -m py_compile app.py` y `node --check` sobre el JS de `templates/index.html`, sin errores. Extraído el texto de los dos PDF adjuntos (`pypdf`) y localizada la línea real del pedido 42644 en el listado de SAP y el albarán 00081970 en el de DALI, para reproducir el caso exacto en una simulación aislada en Python: con los importes reales (base 1.513,35 / recibido 1.274,40) y el estado app ENTREGADO, `estado_ya_avanzado=True`, `sin_cambios_pendientes=True` — la fila deja de mostrarse como pendiente de acción.

# v12.30.18 — 19 agosto 2026

✨ Correo de cambio de estado: ya no se manda a las dos partes por igual — solo a quien NO ha hecho el cambio (quien lo hizo ya lo sabe, y sigue recibiendo su popup/Telegram como hasta ahora)

**Petición de Víctor**: "Se me ocurre, que cuando se cambia un estado de pedido, actualmente se envía automáticamente un correo al comprador y también al rol hotel, podríamos hacer que el correo solo se le envíe al que no ha realizado el cambio? es decir, si el cambio lo realiza el hotel, le llega el correo al comprador y viceversa, al que a realizado el cambio le debería llegar únicamente un popup ; si el cambio es automático entonces si correo a ambas partes".

**Cambio en `app.py`**:

`enviar_emails_estado()`: nuevos parámetros `usuario_id` y `es_automatico`. El correo interno de cambio de estado (`ESTADOS_EMAIL_INTERNO`: ENVIADO AL PROVEEDOR, ENTREGA PARCIAL, ENTREGADO, CANCELADO) ya no se manda siempre a `compradores + usuarios hotel` del hotel — se consulta el rol de `usuario_id` (quien ha hecho el cambio) y se excluye su lado de los destinatarios: si es rol `hotel`, el correo va solo a los compradores; si es cualquier otro rol (compras, admin...), va solo a los usuarios hotel. Con `es_automatico=True` (o sin `usuario_id`, o si el usuario no se encuentra) se mantiene el comportamiento anterior — correo a ambas partes — que es exactamente lo que pidió Víctor para los cambios automáticos.

`_notificar_cambio_estado()`: agrega los mismos dos parámetros y los reenvía a `enviar_emails_estado()` — no toca `_telegram_cambio_estado()` (Telegram + popup del bridge son un canal totalmente aparte, con sus propios destinatarios configurables en Administrador → Configuración de Avisos, evento `cambio_estado_pedido`; no filtrado por quién hizo el cambio — así que quien hizo el cambio sigue enterándose por ahí, tal como pidió Víctor).

Todos los puntos que disparan un cambio de estado manual pasan ahora su `usuario_id` (el `uid` de la sesión que hace la petición): flujo normal y flujo hotel de `update_pedido`, aprobar/denegar expediente de exceso (Dirección General), y la creación de un pedido si nace directamente en un estado de `ESTADOS_EMAIL_INTERNO`. El único punto marcado explícitamente `es_automatico=True` es `_aplicar_coincidencia_albaran()` (aplicar una coincidencia desde "Comparar Pedidos + Albaranes", ver v12.30.16/17) — coherente con que ese mismo cambio ya se etiqueta como "Automática" en el Historial de estados desde v12.30.17.

**Verificación**: `python3 -m py_compile app.py` y `node --check` sobre el JS de `templates/index.html` (sin cambios funcionales en el frontend para esto), ambos sin errores. Simulación aislada en Python de la función de exclusión con 4 escenarios (cambio manual por comprador, por hotel, por admin, y automático/desconocido): en cada caso los destinatarios del correo interno son los esperados — el lado que actúa queda excluido salvo en el caso automático, donde se mantienen ambos.

# v12.30.17 — 19 agosto 2026

✏️ Historial de estados: los registros automáticos de "Comparar Pedidos + Albaranes" ya no aparecen a nombre de quien pulsó "Aplicar"

**Petición de Víctor**: "EN LA TRAZABILIDAD DE CAMBIOS, LOS EJECUTADOS AUTOMATICAMENTE DEBERIAN SALIR ASI DEFINIDOS Y NO CON NOMBRE DE USUARIO, POR EJEMPLO ENTREGA PARCIAL Automática listado comparativo pedidos y albaranes FECHA TAL" — en el "Historial de estados" del pedido (ver capturas del bug anterior, v12.30.16), un cambio de estado a ENTREGADO/ENTREGA PARCIAL aplicado automáticamente desde la comparativa de PDF salía con el nombre del usuario que había pulsado "Aplicar" en pantalla — indistinguible, a simple vista, de un cambio hecho a mano por esa persona desde la ficha del pedido.

**Causa**: `_aplicar_coincidencia_albaran()` guardaba en `historial_estados.usuario_nombre` el nombre de la sesión que confirmó la aplicación (`session.get("nombre")`, pasado desde el endpoint `.../aplicar`) — igual que cualquier cambio manual. El texto que sí indicaba que era automático ("Registro automático — comparación de listados PDF...") solo aparecía al final, entre comillas, en la nota — poco visible frente al nombre de la persona en primer plano.

**Cambio en `app.py`**: en `_aplicar_coincidencia_albaran()`, la fila que se inserta en `historial_estados` para este tipo de cambio ya no usa el nombre del usuario que pulsó "Aplicar" — usa un texto fijo, `"Automática — listado comparativo pedidos y albaranes"`, en su lugar. Solo afecta a esta fila de `historial_estados` (lo que se ve en el Historial de estados del pedido); no toca `modificado_por_id`/`modificado_por_nombre` del pedido (uso interno, no visible en pantalla) ni el resto de flujos de cambio de estado manuales, que siguen mostrando el nombre real de quien hizo el cambio.

**Verificación**: `python3 -m py_compile app.py` sin errores. Revisado que no hay otro punto de "aplicar automáticamente" con el mismo problema (la comparación de solo pedidos, "Comparar listado PDF (SAP)", es de solo lectura y no tiene una función de aplicación equivalente).

# v12.30.16 — 19 agosto 2026

🐛 Comparar Pedidos + Albaranes: al aplicar una coincidencia se duplicaba la entrada de albarán con ceros a la izquierda, y el pedido volvía a salir como pendiente en la siguiente comparación

**Petición de Víctor**: "CUANDO SE ENCUENTRA UN PEDIDO Y SE DA LA OPCION DE ACTUALIZARLO DESDE LA COMPARATIVA, GENERA UNA NUEVA ENTRADA INDICANDO EL MISMO NUMERO DE ALBARAN PERO CON LOS CEROS A LA IZQ. LUEGO EN LA SIGUIENDE COMPARACION VUELVE A SALIR COMO NO CERRADO" — con capturas mostrando el campo "Nº Entrada DALI/SAP" de un pedido con dos entradas para el mismo albarán: "81970" y "00081970", con fechas distintas.

**Causa**: dos puntos de `app.py` comparaban el número de registro DALI (`registro_dali`, tal como aparece en el PDF de "Listado de Albaranes") contra lo ya guardado en `entrada_albaran_num` con un simple `in` de texto (substring), sin normalizar los ceros a la izquierda — a diferencia de los números de pedido, que sí se comparan con `_normalizar_pedido_num()` desde v12.30.06 aprox. Si el pedido ya tenía registrado, por ejemplo, "81970" (tecleado a mano sin ceros) y el PDF de DALI traía "00081970" (como aparece literalmente en su listado), el `in` de texto no lo reconocía como el mismo albarán:
1. `_aplicar_coincidencia_albaran()` (al confirmar "Actualizar" desde la comparativa): añadía una **entrada nueva** "00081970" en vez de detectar que ya estaba registrada — de ahí el duplicado en el campo "Nº Entrada DALI/SAP".
2. `ya_registrado` dentro de `_comparar_listado_albaranes_logica()`: por el mismo motivo no marcaba el pedido como ya registrado, así que la siguiente comparación lo volvía a mostrar como pendiente ("no cerrado"), invitando a aplicarlo otra vez — y potencialmente a duplicar aún más si el PDF trae otra variante de ceros.

**Cambio en `app.py`**: nueva función `_normalizar_num_albaran()` (mismo criterio que `_normalizar_pedido_num()`: quita ceros a la izquierda y espacios, mayúsculas). Se usa ahora en los dos puntos afectados:
- `_comparar_listado_albaranes_logica()`: `ya_registrado` compara el `registro_dali` del PDF, normalizado, contra cada entrada ya parseada de `entrada_albaran_num_actual` (vía `_parse_albaran_entries()`), en vez de buscar el texto tal cual dentro de la cadena completa.
- `_aplicar_coincidencia_albaran()`: antes de añadir una entrada nueva a `entrada_albaran_num`, comprueba (con la misma normalización) si ya existe una entrada equivalente — si la hay, no añade nada, evitando el duplicado.

Nota: esto evita que se generen **nuevos** duplicados y hace que la siguiente comparación reconozca correctamente cualquiera de las dos variantes (con o sin ceros) como "ya registrado". No fusiona automáticamente duplicados que ya existieran en pedidos de antes de este cambio — esos pedidos concretos pueden seguir mostrando las dos entradas hasta que se editen a mano si se quiere limpiar el histórico.

**Verificación**: `python3 -m py_compile app.py` sin errores. Simulación aislada en Python (fuera de la app, sin BD) reproduciendo el caso reportado: con "81970" ya registrado y `registro_dali` "00081970" entrante (y también el caso inverso), `ya_registrado` y el guard de duplicados de `_aplicar_coincidencia_albaran()` dan ahora `True`/"no duplica" en ambos sentidos; un caso de control con dos números realmente distintos ("81970" vs "81971") confirma que no se marcan como iguales por error.

# v12.30.15 — 19 agosto 2026

🐛 Comparar Pedidos + Albaranes: el correo de resumen no llegaba en hoteles con muchos pendientes — EmailJS lo rechazaba por tamaño (HTTP 413)

**Contexto**: tras descartar cupo agotado y conexión de Gmail rota (ver v12.30.14 y las entradas anteriores de hoy), el síntoma seguía sin explicación — el correo se quedaba en cola, EmailJS descontaba cupo de la cuenta activa, pero nunca llegaba. Revisando el Network del navegador (herramientas de desarrollador) al pulsar "Enviar resumen por correo" se vieron varias peticiones `send` a la API de EmailJS con **status 413 (Payload Too Large)** — la petición se envía y EmailJS la cuenta contra el cupo, pero la rechaza sin completarla por ser demasiado grande. El caso real que lo disparó: un hotel con 79 filas en "pendientes de revisión manual", cada una con el texto explicativo largo del "posible candidato" (añadido en v12.30.11/12) — el HTML del correo superaba el límite de tamaño por petición de EmailJS.

**Cambio en `app.py`**:

`_motivo_sin_pedido()` (usado solo en el correo — la pantalla tiene su propio texto, sin límite de tamaño): se acorta el texto del "posible candidato" a menos de la mitad, manteniendo la información esencial (pedido, estado, importe de la app, y las dos acciones a tomar).

`_email_resumen_comparacion_albaranes()`: se añade un límite de 50 filas a la tabla de "pendientes de revisión manual" del correo (mismo patrón que ya usaba `pedidos_faltantes` con `LIMITE_FILAS`), con aviso "…y N más — consulta el listado completo en la aplicación" cuando se recorta. El contador que aparece en el asunto y en el título del bloque ("⏳ Pendientes de realizar (N)") sigue mostrando el total real, sin recortar — solo se acorta la tabla de filas. La pantalla de la aplicación (que lee directamente del JSON de la comparación, no de este correo) sigue mostrando siempre el listado completo, sin límite.

**Verificación**: `python3 -m py_compile app.py` sin errores. Se simuló un caso de 79 pendientes (con la misma mezcla de categorías que el caso real) con un script Python aparte que ejecuta `_email_resumen_comparacion_albaranes()` de forma aislada: el correo generado pasa de 36.445 caracteres (comportamiento anterior, sin límite) a 24.002 caracteres con el límite de 50 filas — margen razonable por debajo del límite de tamaño de EmailJS. No se ha podido reproducir el error 413 exacto contra la API real de EmailJS desde este entorno (sandbox sin las credenciales de producción) — recomendado repetir la comparación del hotel con más pendientes tras desplegar, y confirmar en el Network del navegador que las peticiones `send` devuelven 200 en vez de 413.

# v12.30.14 — 19 agosto 2026

✨ Admin → Config alertas → EmailJS: campo de fecha de reinicio de cupo por cuenta

**Contexto**: investigando por qué había dejado de enviarse el resumen de "Comparar Pedidos + Albaranes" descubrimos que las 3 cuentas EmailJS que usa la app en rotación automática (Cuenta 1 principal, Cuenta 2 secundaria, Cuenta 3 backup) son 3 cuentas EmailJS.com independientes, cada una con su propio cupo de 200 envíos/mes y su propia fecha de reinicio — y que en ese momento la Cuenta 2 y la Cuenta 3 estaban agotadas (200/200), lo que había forzado el cambio automático a la Cuenta 1. Para saber cuándo recupera cupo cada cuenta había que entrar a cada una de las 3 por separado en EmailJS.com — nada de esto se veía desde la propia aplicación.

**Petición de Víctor**: "Podemos insertar un espacio donde indicar la fecha de reinicio de cada una de las cuentas a 0, para tenerlas controladas desde este mismo panel?"

**Cambio en `app.py`**: 3 nuevas claves de configuración (`emailjs_reinicio_fecha_1/2/3`, tipo `fecha`, grupo `emailjs`), añadidas a `_auto_migrate()` con `ON CONFLICT DO NOTHING` (no toca nada existente) y a los valores por defecto de `get_config()`. Son puramente informativas — no las usa ninguna lógica automática, solo se guardan para consulta desde el panel; el admin las rellena a mano copiando la fecha "Resets on ..." que muestra cada cuenta en su propio panel de EmailJS.com.

**Cambio en `templates/index.html`** (Admin → Config alertas → EmailJS): nuevo campo de fecha "Reinicia cupo el" dentro de cada una de las 3 tarjetas de cuenta (junto a Public Key/Service ID/Template ID) — se guarda solo con "Guardar cambios" como el resto de campos de ese panel (el guardado ya es genérico por `id="cfg_..."`, no ha hecho falta tocar `saveConfigAlertas()`). Además, en la cabecera del panel ("Cuenta en uso ahora mismo: N") se muestra ahora también la fecha de reinicio de la cuenta actualmente activa, si está rellena, para verla de un vistazo sin desplegarse hasta su tarjeta.

**Verificación**: `python3 -m py_compile app.py` y `node --check` sobre el JS extraído de `templates/index.html`, ambos sin errores. Cambio aditivo y puramente informativo — no afecta a la lógica de envío ni de rotación automática de cuentas.

# v12.30.13 — 19 agosto 2026

✏️ Comparar Pedidos + Albaranes: identificar los pedidos por su número DALI/SAP, no por el "Nº" lineal interno de la app

**Petición de Víctor**: "MEJOR INDICAR NUMERO PEDIDO DALI / SAP Y NO EL
LINEAL Nº; ES MAS INTUITIVO Y FACIL DE VERIFICAR EN NUESTROS LISTADOS"
— en la pantalla de "Comparar listado PDF" (Pedidos + Albaranes), varias
referencias a un pedido se mostraban como "42438 (Nº618)": el número de
pedido DALI/SAP (`pedido_num`, el mismo que aparece en los listados de
SAP y de DALI que maneja el usuario) seguido, entre paréntesis, del
"Nº" — el número de línea interno correlativo de la app (`norden`,
irrelevante fuera de la propia aplicación). Ese segundo número no
aparece en los listados que Víctor consulta para verificar, así que
solo añadía ruido.

**Cambio en `app.py`** (`_motivo_sin_pedido`): el "posible candidato"
que se sugiere para un albarán sin pareja de importe exacto ahora se
identifica solo por su número de pedido DALI/SAP, sin el "(Nº...)".

**Cambio en `templates/index.html`**: mismo criterio en las tres
referencias a pedidos de la pantalla "Comparar listado PDF" (Pedidos +
Albaranes) que mostraban el "(Nº...)": la tabla de coincidencias
propuestas, la fila de "pendiente sin albarán" (pedido de SAP entregado
sin albarán DALI con ese importe) y el "posible candidato" de
"pendiente sin pedido". Las demás pantallas de la aplicación (listado
de Pedidos, comparación de un solo PDF de SAP, etc.) no se han tocado —
quedan fuera del alcance de esta petición, que Víctor hizo
específicamente sobre esta herramienta de comparación.

**Verificación**: `python3 -m py_compile app.py` y `node --check` sobre
el JS extraído de `templates/index.html`, ambos sin errores. Cambio de
presentación únicamente — no toca ningún criterio de coincidencia ni de
datos.

# v12.30.12 — 19 agosto 2026

✏️ Comparar Pedidos + Albaranes: mensaje del "posible candidato" más claro y accionable (a petición de Víctor)

**Petición de Víctor**, tras ver en pantalla el nuevo aviso de v12.30.11
("Posible candidato ya en la app... verificar importe manualmente"):
"SERIA MEJOR INDICAR QUE EXISTE UN PEDIDO DE FECHA ANTERIOR EL CUAL NO
PODEMOS VERIFICAR SIN UN LISTADO DE PEDIDOS DE ESTA FECHA YA QUE EL
IMPORTE ES SUPERIOR AL REGISTRADO; O ALGO POR EL ESTILO; PARA QUE EL
USUARIO O ADJUNTE UN LISTADO MAS COMPLETO O QUE LO VERIFIQUE
MANUALMENTE YA QUE SI NO SIEMPRE SEGUIRA SALIENDO EL AVISO". El texto
anterior decía que había un "posible candidato" y pedía "verificar
importe manualmente", pero no explicaba POR QUÉ no se podía verificar
solo, ni qué había que hacer para que el aviso dejara de salir.

**Cambio en `app.py`**: nueva función `_motivo_sin_pedido(a)`
(compartida por la tabla de pendientes y el correo — antes el texto
estaba repetido/hardcodeado en `_fila_sin_pedido`), con un mensaje más
explícito: nombra el pedido candidato con su importe registrado en la
app, explica que ese importe es solo la estimación con la que se dio de
alta el pedido — no el importe realmente recibido según SAP, que puede
ser distinto (p.ej. por entregas parciales) — y que por eso no se puede
confirmar solo con los datos disponibles. Termina con la instrucción
concreta: adjuntar un listado de SAP que cubra esa fecha, o comprobarlo
a mano — advirtiendo explícitamente de que, si no se hace ninguna de
las dos cosas, el aviso seguirá saliendo en todas las comparaciones
futuras (para que quede claro que la aplicación, sin más información,
no puede resolverlo por sí sola).

**Cambio en `templates/index.html`**: mismo texto (misma redacción,
duplicada en JS porque la tabla de pendientes se renderiza en el
navegador) para el motivo mostrado en pantalla cuando hay
`posible_pedido_hint`, incluyendo ahora también el importe registrado
en la app del pedido candidato (antes no se mostraba en la fila).

**Verificación**: `python3 -m py_compile app.py` y `node --check`
sobre el JS extraído de `templates/index.html`, ambos sin errores.
Cambio puramente de texto/mensaje — no toca el criterio de coincidencia
introducido en v12.30.11 (mismo proveedor + pedido fuera del PDF de SAP
recién subido), que ya se verificó por separado.

# v12.30.11 — 19 agosto 2026

🐛 Comparar Pedidos + Albaranes: la corrección de v12.30.10 no resolvía el caso SISCOCAN/Nº618 — corregido el criterio de coincidencia

**Aviso de Víctor**: tras desplegar v12.30.10, volvió a comparar los
mismos PDF y envió capturas del correo resultante — el albarán DALI
00082014 (SISCOCAN GRUPO COMERCIAL SL, 2.774,39 €) seguía en "Pendientes
de realizar (10)", con el nuevo texto reformulado ("Sin ningún pedido
Entregado/Parcial con ese importe...") pero SIN pasar al nuevo apartado
"ya registrados en la app". El texto nuevo confirmaba que el despliegue
sí había llegado a producción, pero la lógica de la v12.30.10 no
encontraba el pedido Nº618 como candidato.

**Causa encontrada**: la v12.30.10 comparaba el albarán contra los
pedidos ya dados de alta en la base de datos usando la clave
`(proveedor_id, importe)` — la misma que usa el cruce contra el PDF de
SAP. Pero `pedidos.importe` (la columna de la tabla `pedidos`) es un
importe introducido A MANO al dar de alta o editar el pedido —
estimación/presupuesto usado para el techo de gastos mensual — y NO
tiene por qué coincidir con el importe realmente recibido según SAP
(que solo se conoce al leer un PDF de SAP recién subido, en la variable
transitoria `importe_recibido`). El pedido Nº618 en la BD probablemente
tiene un `importe` distinto de 2.774,39 € (el importe base/estimado del
pedido, no el recibido), así que la comparación exacta por importe
daba 0 candidatos y el caso seguía cayendo en "pendientes_sin_pedido".

**Corrección en `app.py`** (`_comparar_listado_albaranes_logica`): se
sustituye la comparación exacta por importe contra la base de datos por
un criterio más flojo pero fiable — mismo proveedor Y que el número de
pedido de la app NO esté entre los vistos en el PDF de SAP recién
subido (`vistos1`, ya usado internamente por la función para deduplicar
el PDF1) — es decir, que quede fuera del rango de fechas que cubre ese
PDF, como el caso real del pedido Nº618. Si para un proveedor hay
EXACTAMENTE UN pedido de la app en esa situación (Entregado o Entrega
parcial), se adjunta como `posible_pedido_hint` al elemento
correspondiente de `pendientes_sin_pedido` — SIN sacarlo de la lista de
pendientes (el importe no se puede verificar con este criterio, así que
no se da por resuelto automáticamente) y sin aplicar ningún cambio: es
solo una pista para que la persona que revisa lo pendiente no tenga que
buscar el pedido a mano. Se elimina el apartado independiente
`ya_registrados_en_app` (v12.30.10) — con la nueva lógica ningún caso
puede darse por "resuelto" con seguridad, así que ya no tiene sentido
sacarlo de pendientes; el pedido candidato se muestra como pista dentro
de la misma fila de "pendientes de revisión manual".

**Cambio en `templates/index.html`**: se elimina la sección plegable
"Ver albaranes de pedidos más antiguos ya registrados en la app" (ya no
se genera ese apartado). La fila de "pendientes_sin_pedido" en la tabla
de pendientes muestra ahora, cuando aplica, el motivo con la pista del
posible pedido candidato en vez de un texto genérico.

**Cambio en el correo** (`_email_resumen_comparacion_albaranes`): se
elimina el bloque "📎 Albaranes de DALI de pedidos más antiguos, ya
registrados en la app". El motivo de cada fila "sin pedido" en la tabla
de pendientes incluye la misma pista de posible candidato cuando la
hay.

**Verificación**: `python3 -m py_compile app.py` sin errores; `node
--check` sobre el JS extraído de `templates/index.html` sin errores.
Se simuló el caso SISCOCAN/Nº618 con un script Python independiente
(mismo algoritmo que el nuevo código: `vistos1` sin el pedido 618,
un único pedido ENTREGADO de ese proveedor en la "base de datos"
simulada) y se confirmó que ahora sí se adjunta como
`posible_pedido_hint` al albarán 00082014. Sin poder probar contra la
base de datos real de producción desde este entorno (sandbox sin
acceso a Supabase) — recomendado volver a lanzar la misma comparación
(mismos dos PDF) tras desplegar, para confirmar en pantalla que la fila
de SISCOCAN/00082014 en "Pendientes de realizar" ahora menciona el
pedido Nº618 como posible candidato.

# v12.30.10 — 19 agosto 2026

🐛 Comparar Pedidos + Albaranes: "Sin pedido... en la app" salía aunque el pedido SÍ estuviera registrado y Entregado

**Aviso de Víctor**: "EN CONTROL PEDIDOS FILTRO REALIZADO EN PEDIDOS CON
PDFs DA UN RESULTADO INCORECTO A REVISAR; HEMOS DETECTADO QUE DA UN
PEDIDO COMO NO REGISTRADO EN LA PLATAFORMA, PERO EL CASO ES QUE SI ESTA
REGISTRADO E INCLUSO CON ESTADO ENTREGADO" — con capturas: la tabla
"Pendientes de realizar" del correo mostraba "Albarán DALI 00082014,
SISCOCAN GRUPO COMERCIAL SL, 2.774,39 €, Sin pedido Entregado/Parcial
con ese importe en la app", pero el pedido Nº618 de ese proveedor SÍ
está dado de alta y en estado ENTREGADO en la app (captura del listado
de Pedidos filtrado por "SISCO").

**Causa encontrada**, tras leer el código de
`_comparar_listado_albaranes_logica()` y los dos PDF adjuntados por
Víctor (`FV.pdf` = listado de pedidos de SAP, `FV2.pdf` = listado de
albaranes de DALI): el cruce solo comparaba el albarán contra los
pedidos que aparecían en el PDF de SAP recién subido — nunca contra los
pedidos ya dados de alta en la propia base de datos de la app. El PDF
de SAP que subió Víctor solo cubría pedidos desde el 28/07/2026 en
adelante (confirmado extrayendo el texto del PDF: ninguna fecha
anterior, ni rastro de "SISCOCAN"), mientras que el pedido Nº618 se
tramitó el 02/06/2026 — casi dos meses antes, fuera del rango de ese
PDF. Su albarán en DALI, en cambio, se registró el 10/08/2026 (dentro
del PDF de albaranes). Como el pedido nunca podía aparecer como
candidato del lado del PDF de SAP, el cruce lo daba por "sin pedido" —
y el texto del mensaje ("...en la app") daba a entender, incorrectamente,
que el pedido no estaba registrado en la aplicación, cuando el problema
real era solo que no salía en ESE PDF concreto.

**Cambio en `app.py`** (`_comparar_listado_albaranes_logica`): antes de
dar por "sin pedido" un albarán sin pareja en el PDF de SAP, se
comprueba una segunda vez contra los pedidos ya dados de alta en la
base de datos (mismo proveedor + mismo importe, entre los que están
Entregado o Entrega parcial) — sin depender de qué cubra el PDF de
turno. Si hay exactamente un pedido de la app que cuadra, se saca de
"pendientes_sin_pedido" (no requiere ninguna acción) y pasa a un nuevo
apartado, `ya_registrados_en_app`, informativo. Si hay 0 o más de 1
candidato en la app, se deja tal cual pendiente — mismo criterio de
"ante la duda, no inventar" que ya usa el resto de esta función para
los empates. De paso, se reformula el texto del motivo para los que
sigan quedando pendientes de verdad: "Sin ningún pedido Entregado/
Parcial con ese importe (ni en el PDF de SAP ni ya dado de alta en la
app)" — ya no puede confundirse con "no está en la aplicación".

**Cambio en `templates/index.html`**: nueva sección plegable "Ver
albaranes de pedidos más antiguos ya registrados en la app", en verde
(no es un problema), justo debajo de "pendientes de revisión manual" —
oculta por completo cuando no aplica. Nueva "pill" en el resumen cuando
hay alguno. Mismo texto de motivo corregido en la tabla de pendientes.

**Cambio en el correo** (`_email_resumen_comparacion_albaranes`): nuevo
bloque "📎 Albaranes de DALI de pedidos más antiguos, ya registrados en
la app", en verde, con el pedido de la app al que corresponde cada uno
— separado del bloque de pendientes de verdad.

**Verificación**: `python3 -m py_compile app.py` sin errores; `node
--check` sobre el JS extraído de `templates/index.html` sin errores.
Se confirmó el hallazgo leyendo el texto real de los dos PDF que
adjuntó Víctor (`FV.pdf`/`FV2.pdf`) con `pypdf` — SISCOCAN no aparece
en ningún sitio de `FV.pdf`, y el albarán 00082014 de `FV2.pdf` trae
exactamente 2.774,3850 €, coincidiendo con la captura. Sin poder probar
contra la base de datos real de producción desde este entorno (sandbox
sin acceso a Supabase) — recomendado volver a lanzar la misma
comparación (mismos dos PDF) tras desplegar, para confirmar en pantalla
que el albarán 00082014/SISCOCAN pasa de "pendiente" a la nueva sección
"ya registrados en la app".

# v12.30.09 — 17 agosto 2026

🔕 Ningún aviso automático (Telegram/popup) en fin de semana

**Petición de Víctor**: "Control pedidos no debería enviar popup ni
Telegram los findes de semana". La mayoría de los jobs automáticos del
scheduler (`_iniciar_scheduler()`, `app.py`) ya solo corrían lun-vie
(alertas diarias de pedidos, techo urgente, techo mensual, familia
repetida), pero tres se habían quedado sin esa restricción y seguían
disparando todos los días, sábado y domingo incluidos:

- `health_check_diario` (07:05) — Telegram + popup bridge a admins si
  detecta problemas de configuración (hoteles sin comprador, etc.).
- `alerta_consumo_diaria` (08:30) — Telegram + popup bridge a admins si
  el consumo de Supabase (egress o tamaño de BD) se acerca o supera el
  límite del plan Free.
- `recordar_emails_sistema_pendientes` (cada 10 min, 07:00-21:00) —
  Telegram con recordatorio si hay emails de sistema en cola sin
  despachar.

**Cambio**: se añade `day_of_week="mon-fri"` a los tres, mismo criterio
que el resto de jobs de alertas — lo que caiga en fin de semana se
retoma el lunes con normalidad, sin aviso perdido (el snapshot diario de
tamaño de BD, que sí sigue corriendo todos los días porque no manda
nada, conserva el histórico completo aunque el AVISO de consumo se
retrase). Los dos jobs puramente internos sin ningún canal de aviso
(snapshot de tamaño de BD a las 08:10, migración de adjuntos a Storage a
las 03:00) se dejan corriendo todos los días — no tiene sentido
restringirlos, no molestan a nadie.

**Verificación**: `python3 -m py_compile app.py` sin errores. Sin forma
de probar el propio disparo del scheduler en fin de semana desde este
entorno (dependería del reloj real del servidor en producción) —
recomendado confirmar tras desplegar que estos tres jobs no aparecen en
el log de un sábado/domingo (buscar "[HEALTH]", "[CONSUMO]" o
"[RECORDATORIO EMAILS SISTEMA]" en los logs de Render de ese día).

# v12.30.08 — 15 agosto 2026

🔗 Comparar Pedidos + Albaranes: el resultado y el correo son la unión de las dos comparaciones

**Petición del usuario**, tras ver el resultado de v12.30.07 en pantalla:
"si se realiza el trabajo con los 2 PDF el resultado entregado deberá ser
una unión de ambos, es decir, la información que lanza el primero mas la
que lanza ambos, para enviar un único correo al comprador y admin" — hasta
ahora, al marcar la casilla del segundo PDF, la tabla de auditoría del
primer PDF (pedidos sin dar de alta o sin entregar) dejaba de mostrarse
del todo, sustituida solo por la sección de coincidencias con los
albaranes; y aunque hubiera aparecido, cada sección tenía su propio botón
de correo independiente.

**Cambio — backend (`app.py`)**: `_comparar_listado_albaranes_logica()`
calcula ahora también, además del cruce con los albaranes, la auditoría
completa del PDF 1 (reutilizando tal cual `_comparar_listado_pdf_logica()`
sobre el mismo PDF 1) y la añade al resultado como `auditoria_pdf1`. El
endpoint `.../enviar-resumen` construye a partir de ella la misma lista de
"pedidos sin dar de alta" que ya usaba el correo de un solo PDF, y
`_email_resumen_comparacion_albaranes()` la incorpora como una sección
más del correo — que pasa a tener tres bloques en un único envío: 📋
pedidos de SAP sin dar de alta, ✅ registrados automáticamente y ⏳
pendientes de realizar. Si las tres secciones están vacías, no se envía
nada (mismo criterio que el correo de un solo PDF).

**Cambio — frontend (`templates/index.html`)**: al terminar la
comparación con los dos PDF, se muestra también la tabla de auditoría
completa del PDF 1 (reutilizando la tabla/checkbox de filtro ya
existentes) justo encima de la sección de coincidencias con los
albaranes — y se oculta el botón de correo de esa tabla, para que solo
quede un botón "Enviar resumen por correo (pedidos + albaranes)" que
envía el correo conjunto ya unificado en el backend.

**Verificación**: `python3 -m py_compile app.py` y sintaxis de los
bloques `<script>` de `templates/index.html` (`node --check` sobre el JS
extraído), ambos sin errores. Sin pruebas contra base de datos en vivo —
sigue pendiente la primera prueba real en producción, igual que en
v12.30.07.

# v12.30.07 — 15 agosto 2026

📦 Comparar Pedidos + Albaranes: cruce automático propuesto con el listado de albaranes de DALI

**Petición del usuario**: en Pedidos → Comparar listado PDF, ampliar la
comparación existente (que solo lee el "Listado de Pedidos" de SAP contra
lo ya dado de alta en la app) para leer también un segundo PDF — el
"Listado de Albaranes" que exporta DALI — y cruzar ambos: los pedidos que
SAP ya muestra como Entregado/Entrega parcial contra los albaranes ya
registrados en DALI para ese mismo proveedor e importe. Al coincidir,
proponer completar en el pedido la fecha de tramitación, el número de
entrada del albarán y el cambio de estado, y en el correo final indicar
tanto lo registrado automáticamente como lo pendiente de revisar. Solo se
tienen en cuenta proveedores marcados como sujetos a seguimiento, en
ambos PDF.

**Diseño acordado con el usuario** (antes de tocar nada, por tratarse de
escritura automática sobre datos de producción):
- El importe que debe coincidir es el **recibido** del pedido (no el
  base/total), frente al importe del albarán.
- Ninguna coincidencia se escribe sola: siempre hay que **revisarla y
  confirmarla** en pantalla antes de aplicarla (una a una o en bloque).
- La fecha de tramitación del PDF 1 solo se rellena si el pedido **no
  tiene ya una guardada** — nunca se sobrescribe una existente.
- Si un mismo proveedor + importe encaja con más de una pareja posible
  (varios pedidos y/o albaranes ese día), **no se adivina**: todos esos
  casos van a una lista de "pendientes de revisión manual".

**Cambio — backend (`app.py`)**: nueva función `_comparar_listado_albaranes_logica()`
que lee el segundo PDF con un patrón de texto nuevo (`_PATRON_LISTADO_ALBARANES`,
validado 265/265 líneas contra un listado real de muestra), identifica
proveedor y departamento de cada albarán — el nombre del departamento
llega pegado al del proveedor sin separador en el texto extraído del PDF,
así que se identifica por coincidencia de prefijo contra el catálogo de
`departamentos` — y cruza ambos listados por `(proveedor_id, importe)`.
El resultado se reparte en `coincidencias` (pareja única en ambos lados),
`pendientes_ambiguos` (más de una pareja posible), `pendientes_sin_albaran`
(pedido Entregado/Parcial en SAP sin albarán DALI que encaje) y
`pendientes_sin_pedido` (albarán DALI sin pedido que encaje). Nueva
`_aplicar_coincidencia_albaran()` aplica una coincidencia ya confirmada de
forma idempotente (no duplica el albarán si ya estaba registrado, no
retrocede el estado si ya estaba más avanzado, no repite notificaciones si
no hay nada que cambiar) reutilizando `_notificar_cambio_estado()` — así
hereda automáticamente el antirrepetición de 5 minutos del popup y el
correo de cambio de estado (v12.30.05/06). Tres endpoints nuevos, todo
solo para administradores y con el mismo patrón de job en segundo plano +
sondeo que ya usaba la comparación de un solo PDF (para no toparse con
timeouts de proxy en listados grandes): `POST/GET
/api/pedidos/comparar-listado-albaranes[/<job_id>]`,
`POST .../<job_id>/aplicar` (aplica una o varias coincidencias
confirmadas) y `POST .../<job_id>/enviar-resumen` (correo con lo
registrado y lo pendiente, mismo mecanismo de cola que el resto de
correos internos de la app).

**Cambio — frontend (`templates/index.html`)**: en el modal "Comparar
listado PDF" se añade una casilla opcional "+ Comparar también con el
listado de Albaranes registrados en DALI" que revela un segundo selector
de fichero; al marcarla, el botón Comparar llama al nuevo endpoint en vez
del existente. El resultado se muestra en una sección nueva con las
coincidencias propuestas (una fila por pareja, con casilla de selección y
botón "Aplicar" individual, más un botón para aplicar todas las
seleccionadas de golpe) y una lista plegable de pendientes de revisión
manual, además del botón para enviar el correo resumen.

**Verificación**: `python3 -m py_compile app.py` y comprobación de
sintaxis de los bloques `<script>` de `templates/index.html` (vía
`node --check` sobre el JS extraído), ambos sin errores. El patrón de
lectura del segundo PDF se validó por separado contra el listado de
muestra real (265/265 filas reconocidas). Sin pruebas contra base de
datos en vivo — no hay acceso a una en este entorno; queda pendiente de
probar en producción con un listado real de albaranes antes de darlo por
cerrado.

# v12.30.06 — 14 agosto 2026

📧 Correo de cambio de estado: mismo retraso de 5 minutos y antirrepetición que el popup

**Petición del usuario**, continuación directa de v12.30.05: "¿también llegan
correos electrónicos de aviso inmediatos con el cambio de estado?" → sí, y
además de forma más inmediata que el popup (se enviaban directamente desde
el navegador de quien guardaba el pedido, sin ninguna cola de por medio) →
"si por favor" a aplicar la misma protección.

**Cambio**: los correos de cambio de estado (proveedor / interno,
`enviar_emails_estado()` en `app.py`) dejan de devolverse para envío
inmediato desde el navegador que hizo el cambio. Ahora se encolan con 5
minutos de retraso en `emails_sistema_pendientes` — la misma cola que ya
usaba la app para los correos generados por jobs sin navegador abierto
(techo urgente, familias repetidas, solicitudes de acceso...) — vía la
función nueva `_encolar_email_pedido_retrasado()`. Si el mismo pedido
cambia de estado otra vez antes de que se cumplan esos 5 minutos, se
sobrescribe el correo pendiente (contenido + cuenta atrás) en vez de
encolar uno nuevo: solo se entrega el último cambio.

El envío real lo sigue haciendo el navegador vía EmailJS (esta app no tiene
SMTP propio) — pero ahora lo hace el poller de "emails de sistema" que ya
revisaba esa cola cada 5 minutos desde cualquier sesión admin/compras
abierta (`_enviarEmailsSistemaPendientes` en `templates/index.html`), con
reserva atómica anti-duplicados ya existente. Efecto colateral positivo:
el envío ya no depende de que quien hizo el cambio no cierre la pestaña
antes de que EmailJS termine.

**Base de datos**: columna nueva `emails_sistema_pendientes.visible_en`
(`TIMESTAMPTZ NOT NULL DEFAULT NOW()`), añadida automáticamente por
`_auto_migrate()` — sin acción manual en Supabase. Por defecto inmediata
(`NOW()`), así que el resto de correos de esa cola no cambia de
comportamiento.

**Aviso**: a diferencia del envío inmediato de antes (que salía desde
cualquier sesión, incluida la de rol `hotel`), el despacho de esta cola
solo lo hacen sesiones `admin`/`compras` con la app abierta — mismo
comportamiento que ya tenían el resto de correos automáticos de esta cola.
Si nadie de compras/admin abre la app en un buen rato, el job de
recordatorio ya existente (`_job_recordar_emails_sistema_pendientes`, cada
10 min en horario 07–21h) avisa por Telegram con la cola pendiente — cubre
también este caso nuevo sin cambios adicionales.

# v12.30.05 — 14 agosto 2026

🔕 Popup de cambio de estado: antirrepetición con espera de 5 minutos

**Petición del usuario**: cada cambio de estado de un pedido disparaba un
popup inmediato en el Organizador (main_agenda) — si un pedido cambiaba
de estado varias veces seguidas por error (y se corregía al momento), el
comprador/hotel recibía un popup por cada cambio, en vez de uno solo con
el estado final.

**Cambio**: `_encolar_bridge_notificacion()` (`app.py`) admite ahora
`retraso_segundos` — para el popup de `cambio_estado_pedido` se pasa
`retraso_segundos=300` (5 min). El aviso no se hace visible para el
bridge (`GET /api/bridge/notificaciones`, columna nueva `visible_en`)
hasta pasados esos 5 minutos desde el último cambio de ese pedido; si
llega otro cambio antes de que se cumpla el plazo, se sobrescribe el
mismo aviso (contenido + cuenta atrás) en vez de encolar uno nuevo. El
resultado: como mucho un popup por pedido cada 5 minutos, siempre con el
último estado. El Telegram de cambio de estado **no** se ha tocado —
sigue siendo inmediato, tal y como pidió el usuario (solo el popup).
Sin cambios para el resto de tipos de popup (`alerta_auto`, `techo`,
`familia_repetida`, `supervision`, `consumo`, `integridad`): siguen
siendo inmediatos, `visible_en` por defecto es `NOW()`.

**Base de datos**: columna nueva `bridge_notificaciones.visible_en`
(`TIMESTAMPTZ NOT NULL DEFAULT NOW()`), añadida automáticamente por
`_auto_migrate()` al arrancar — no requiere ninguna acción manual en
Supabase.

# v12.30.04 — 14 agosto 2026

📧 Fix: el correo al proveedor ya no duplica el aviso interno

**Problema reportado por el usuario**: al pasar un pedido a `ENVIADO AL
PROVEEDOR` se enviaban dos correos que informaban dos veces a los mismos
destinatarios internos — el correo interno propiamente dicho (a
compradores y usuarios hotel) y, además, el correo externo al
proveedor, que llevaba en copia oculta (BCC) a esos mismos compradores y
usuarios hotel. El comprador y el hotel recibían la misma notificación
dos veces.

**Cambio**: en `enviar_emails_estado()` (`app.py`), el correo al
proveedor deja de llevar `bcc` a los internos — ahora se envía única y
exclusivamente al proveedor. El correo interno (que ya se enviaba en
paralelo para este mismo estado) sigue siendo, él solo, quien informa a
compradores y usuarios hotel del cambio de estado. Sin cambios en el
resto de estados (`ENTREGA PARCIAL`, `ENTREGADO`, `CANCELADO`,
`DENEGADO POR DIRECCION GENERAL`), que nunca llevaban ese BCC duplicado.

# v12.30.03 — 14 agosto 2026

🎨 Tarjeta "Catálogo DALI" del Dashboard, rediseñada

**Petición del usuario**: la tarjeta de acceso a DALI en el Dashboard
(añadida en v12.30.02) tenía que ser "más visual", y no hacía falta
explicar que se entra sin contraseña adicional — solo qué hace.

**Cambio**: nueva clase `.dash-dali-card` — icono en círculo, fondo
degradado navy/dorado (misma paleta que el resto de la app), flecha "→"
indicando que abre algo, efecto hover (elevación + sombra). Texto
reducido a qué es y qué permite consultar, sin mencionar el mecanismo de
acceso. Mismo `onclick="abrirDali()"` de siempre, sin cambios de lógica.

# v12.30.02 — 14 agosto 2026

🧾 Nuevo: acceso de un clic al catálogo DALI desde el menú lateral y el dashboard

**Petición del usuario**: que cualquier usuario (admin, compras u hotel)
pueda acceder a la nueva app de catálogo DALI desde el dashboard o el
menú lateral, con los usuarios de aquí ya dados de alta allí — rol
compras -> administrador en DALI, rol hotel -> mismo rol (hotel, de solo
consulta) en DALI.

**Qué se añade**: nuevo endpoint `GET /api/dali/sso` (`@login_required`):
genera un token firmado de un solo uso (HMAC-SHA256, ~60s de validez,
secreto compartido `DALI_SSO_SECRET`) con el email/nombre del usuario de
la sesión y su rol ya mapeado (`DALI_ROL_MAP`: admin->admin,
compras->admin, hotel->hotel), y devuelve la URL de DALI con ese token.
Nuevo item "🧾 Catálogo DALI" en el menú lateral (visible para los tres
roles) y una tarjeta de acceso rápido en el Dashboard — ambos llaman a
`abrirDali()`, que pide la URL y la abre en una pestaña nueva.

El backend de DALI (repo aparte) verifica la firma, aprovisiona o
actualiza el usuario en su propia tabla `usuarios` con el rol recibido, y
abre sesión sin pedir contraseña — el usuario nunca ve el login de DALI.
Si el usuario no tiene email registrado aquí, se avisa con un mensaje
claro en vez de fallar en silencio (DALI identifica usuarios por email).

**Configuración pendiente antes de desplegar**: variables de entorno
`DALI_SSO_SECRET` (idéntica en este servicio y en el backend de DALI) y
`DALI_FRONTEND_URL` en Render — ver `render.yaml` y el informe de
integración entregado junto con este cambio.

**Verificación**: `python3 -c "import ast; ast.parse(open('app.py').read())"`
sin errores. Pendiente de probar en caliente contra un DALI_SSO_SECRET
real una vez configurado en ambos servicios de Render.

# v12.30.00 — 14 agosto 2026 09:40

🔧 Columna "Entrega": ahora es "Entregado" si el importe recibido es igual O SUPERIOR a la base (antes exigía igualdad exacta)

**Petición del usuario**: precisar la regla de la columna "Entrega" —
"entrega completa es cuando columna 7 => 6; entrega parcial cuando
7 >0 y <6; no entregado 7 = 0" (columna 6 = base imponible, columna 7 =
importe recibido, del listado simplificado de SAP).

**Antes** (`_entrega_estado`): "Entregado" exigía columna 7 == columna 6
exacto — si el importe recibido informado en SAP superaba ligeramente a
la base (recargos, ajustes, redondeos…), el pedido se quedaba mal
clasificado como "Entrega parcial" aunque en realidad ya estaba
completo.

**Ahora**: columna 7 ≥ columna 6 → "Entregado"; 0 < columna 7 < columna
6 → "Entrega parcial"; columna 7 ≤ 0 → "No entregado" (se trata también
un importe recibido negativo, dato anómalo, como "No entregado" por
seguridad). Afecta tanto a la columna "Entrega" en pantalla como al
recuento de entregados/parciales/no entregados y al correo de resumen.

**Verificación**: `python3 -m py_compile app.py` sin errores. Reprocesados
los 2 PDF reales disponibles comparando la regla antigua vs. la nueva:
- PDF de La Palma Princess (199 pedidos): 13 pedidos cambian de "Entrega
  parcial" a "Entregado" (todos con recibido ligeramente por encima de
  la base, p. ej. pedido 00015988: base 118,00 / recibido 127,00).
  Recuento total: antes 35 Entregado / 36 Entrega parcial, ahora 48
  Entregado / 23 Entrega parcial (los 128 "No entregado" no cambian).
- Listado simplificado de 221 pedidos: 38 pedidos cambian de igual
  forma. Recuento total: antes 66 Entregado / 57 Entrega parcial, ahora
  104 Entregado / 19 Entrega parcial (los 98 "No entregado" no cambian).

Sin cambios en `templates/index.html` más allá del badge de versión (la
columna "Entrega" ya se pinta con el valor que devuelve
`_entrega_estado()`, sin lógica propia en el frontend). Badge del
sidebar actualizado a "V 12.30.00". `README.md` actualizado.

# v12.29.98 — 14 agosto 2026 09:10

🏷️ "Estado aparente" del correo de "Comparar listado PDF": nuevo caso "SIN ENTREGAR" (antes se confundía con "ENTREGA PARCIAL")

**Reporte del usuario**: en el correo de pedidos de SAP/DALI sin dar de
alta (hotel La Palma Princess, LP.pdf adjunto), 4 pedidos salían con
"Estado aparente: ENTREGA PARCIAL" y a la vez columna "Entrega: No
entregado" — parecía contradictorio. Se preguntó "¿por qué indica
entrega parcial?".

**Diagnóstico**: comprobado con el propio PDF que el usuario adjuntó
(00016080, 00016147, 00016165, 00016171) — los 4 tienen importe
recibido = 0,00 (nada recibido todavía) e importe pendiente = importe
base completo. No es contradictorio: son dos columnas independientes a
propósito ("Entrega" compara base vs. recibido; "Estado aparente" mira
solo si columna 8 del SAP, importe pendiente, es > 0). El problema es
que esa regla original de "Estado aparente" era binaria (pendiente >0 =
PARCIAL, si no COMPLETA) y no distinguía "no ha llegado nada todavía"
de "ya llegó una parte" — ambos casos tienen importe pendiente > 0, así
que ambos salían como "ENTREGA PARCIAL", aunque en el primer caso no ha
llegado literalmente nada.

**Ajuste, a petición del usuario** ("ajustar lógica"): `_estado_aparente_entrega()`
pasa a mirar también el importe recibido (columna 7, dato en bruto del
SAP, no un cálculo) y ahora distingue 3 casos en vez de 2:
- pendiente ≤ 0 → **ENTREGA COMPLETA** (igual que antes)
- pendiente > 0 y recibido ≤ 0 → **SIN ENTREGAR** (nuevo — nada recibido todavía)
- pendiente > 0 y recibido > 0 → **ENTREGA PARCIAL** (reservado ahora a cuando de verdad ha llegado algo, pero falta el resto)

Actualizado también el color del correo (rojo oscuro para "SIN
ENTREGAR", ámbar para "ENTREGA PARCIAL", verde para "ENTREGA COMPLETA")
y el texto explicativo bajo la tabla, que ahora describe los 3 casos.

**Verificación**: `python3 -m py_compile app.py` sin errores; `node
--check` sobre el JS de `templates/index.html` sin errores (no hay
cambios de frontend — "Estado aparente" solo se usa en el correo, nunca
se pinta en pantalla). Reprocesados los 2 PDF reales disponibles:
- `LP.pdf` (el reportado, 199 pedidos): los 4 pedidos del correo pasan
  de "ENTREGA PARCIAL" a "SIN ENTREGAR", confirmado con los importes
  reales extraídos del propio PDF (recibido=0,00 en los 4). Recuento
  total: 128 SIN ENTREGAR, 23 ENTREGA PARCIAL, 48 ENTREGA COMPLETA.
- `MT2.pdf` (regresión, 221 pedidos): sigue parseando sin errores, 97
  SIN ENTREGAR, 19 ENTREGA PARCIAL, 105 ENTREGA COMPLETA.

Badge de versión del sidebar actualizado a "V 12.29.98". `README.md`
actualizado.

# v12.29.96 — 13 agosto 2026 08:15

🐛 Fix: correos de la cola de sistema duplicados por carrera (race condition) entre pestañas/sesiones

**Reporte del usuario**: el pedido Nº 39909 (reclamación automática por
"Entrega parcial pendiente de completar") llegó DOS veces idénticas a la
bandeja de entrada del admin, y aparece dos veces en "Enviados" de Gmail,
ambas a las 7:43. Se adjuntaron capturas del panel de alertas, la bandeja
de entrada, la bandeja de enviados de Gmail, y un fragmento de los logs
de Render de ese minuto.

**Investigación**: la reclamación automática al proveedor
(`_encolar_reclamacion_proveedor_auto`, dentro del job diario de
alertas) ya tiene buena protección contra insertar la fila dos veces el
mismo día (`_ya_notificado_hoy`, más una comprobación final de
seguridad) — descartado que el problema esté en el ENCOLADO.

El problema real está en el DESPACHO de la cola
(`emails_sistema_pendientes`): `_enviarEmailsSistemaPendientes()`
(frontend) hacía `GET /api/emails-sistema-pendientes` (lista las filas
`enviado=FALSE`), enviaba de verdad por EmailJS, y solo DESPUÉS marcaba
la fila como enviada con `POST .../marcar-enviado`. Entre esos dos pasos
no había ningún bloqueo: si dos pestañas/sesiones (dos usuarios
admin/compras, o simplemente una recarga de página mientras el ciclo de
5 minutos ya estaba en marcha) pedían la cola casi a la vez, **ambas
veían la misma fila como pendiente y ambas la mandaban de verdad por
EmailJS** antes de que ninguna llegara a marcarla — dos correos reales
por un solo aviso. Esto es posible porque el servidor corre con varios
hilos (`render.yaml`: `--worker-class gthread --threads 4`), así que dos
peticiones sí se procesan en paralelo de verdad dentro del mismo
proceso.

**Corrección**: `GET /api/emails-sistema-pendientes` ahora RESERVA
atómicamente las filas que devuelve, en la misma sentencia SQL
(`UPDATE ... SELECT ... FOR UPDATE SKIP LOCKED ... RETURNING`), marcando
`en_proceso_desde = NOW()`. Una segunda petición concurrente ya no ve
esas filas como disponibles (se excluyen las reservadas hace menos de 2
minutos) y con `SKIP LOCKED` ni siquiera espera bloqueada a que la
primera termine — sigue con lo que quede libre. Si una sesión reserva
una fila y nunca confirma el envío (falla EmailJS, se cierra la pestaña
a media faena…), la reserva caduca sola a los 2 minutos y otra sesión
puede reintentarla con normalidad, sin perder ningún envío.

Nueva columna `emails_sistema_pendientes.en_proceso_desde` (migración
idempotente en `_auto_migrate()`, `ALTER TABLE ... ADD COLUMN IF NOT
EXISTS`).

**Verificación**: `python3 -m py_compile app.py` sin errores. Reproducido
el bug y la corrección con un PostgreSQL real (no simulado): dos
"sesiones" en hilos separados pidiendo la cola en el mismo instante
(con una barrera para maximizar la colisión) — con el SQL antiguo
(`SELECT` simple) ambas ven y "envían" la misma fila (duplicado
reproducido tal cual lo reportó el usuario); con el SQL nuevo
(`UPDATE ... FOR UPDATE SKIP LOCKED`) solo una de las dos la reclama, la
otra recibe 0 filas. Verificada también la caducidad de la reserva: una
fila "reservada" hace 3 minutos vuelve a ser reclamable, una reservada
hace 0 minutos NO lo es, y una fila ya marcada `enviado=TRUE` nunca
vuelve a aparecer aunque su reserva haya caducado.

Sin cambios necesarios en `templates/index.html` (el frontend ya hacía
correctamente GET → enviar → marcar-enviado; el fix es enteramente del
lado del servidor). Badge de versión del sidebar actualizado a
"V 12.29.96". `README.md` actualizado.

# v12.29.94 — 12 agosto 2026 09:40

🔁 Tercera cuenta EmailJS de backup: rotación cíclica entre 3 cuentas (1→2→3→1)

**Petición del usuario**: con la v12.29.92 ya desplegada, incorporar una
tercera cuenta EmailJS ("Cuenta1 (principal)", "Cuenta2 (secundaria)",
"Cuenta3 (backup)") y que el sistema salte automáticamente de una a otra
en cuanto se consuman los envíos establecidos por cuenta.

**Backend (`app.py`)**:
- `_auto_migrate()` → `_emailjs_defaults` ampliado con 3 filas nuevas
  (`emailjs_public_key_3`, `emailjs_service_id_3`, `emailjs_template_id_3`)
  y renombradas las etiquetas de las cuentas 1/2 a "(principal)"/
  "(secundaria)" (inserción idempotente vía `ON CONFLICT (clave) DO
  NOTHING`, no toca instalaciones ya desplegadas salvo para añadir las 3
  claves nuevas).
- `get_config()` → añadidas las 3 claves nuevas a los valores por defecto.
- Nuevas constantes/helpers: `_EMAILJS_MAX_CUENTAS = 3`,
  `_emailjs_cuenta_valida(valor)` (normaliza a un entero 1–3, con 1 como
  valor por defecto ante datos corruptos) y
  `_emailjs_siguiente_cuenta(activa)` (siguiente cuenta del ciclo,
  3→1 incluido).
- `GET /api/emailjs/config` → usa `_emailjs_cuenta_valida()` en vez del
  antiguo recorte binario (1 o 2).
- `POST /api/emailjs/registrar-envio` → sustituido el cambio
  BIDIRECCIONAL (1⇄2) por un cambio CÍCLICO: al llegar al umbral, se
  busca la siguiente cuenta del ciclo (1→2→3→1) que tenga las 3
  credenciales completas, probando hasta las 3 antes de rendirse; si
  ninguna otra cuenta está completa, no cambia (igual que antes) y queda
  aviso en Integridad.
- Admin → Integridad (comprobación EmailJS) → generalizada de "la otra
  cuenta" a "la siguiente cuenta del ciclo", y el aviso de "umbral
  alcanzado sin backup" ahora comprueba las 2 cuentas restantes (no solo
  la inmediatamente siguiente).

**Frontend (`templates/index.html`)**: tarjeta de administración de
EmailJS (Config alertas) ampliada de 2 a 3 paneles de cuenta ("Cuenta 1
(principal)" / "Cuenta 2 (secundaria)" / "Cuenta 3 (backup)"), campo
"Cuenta activa" ahora acepta 1–3, y texto explicativo actualizado para
describir el ciclo de 3 cuentas.

**Verificación**: `python3 -m py_compile app.py` sin errores; `node
--check` sobre los bloques `<script>` extraídos de `templates/index.html`
sin errores; lógica de rotación cíclica verificada en un script aislado
(ciclo completo 1→2→3→1 con las 3 cuentas completas, salto correcto de 1
directamente a 3 cuando la cuenta 2 no tiene credenciales, sin cambio
cuando solo la cuenta activa está completa, y `_emailjs_cuenta_valida`
recortando correctamente valores fuera de rango o inválidos).

Badge de versión del sidebar actualizado a "V 12.29.94". `README.md`
actualizado.

# v12.29.92 — 12 agosto 2026 08:05

🐛 Fix: 3 tipos de email SÍ consumían cuota real de EmailJS pero el contador no los contaba

**Pregunta del usuario** (de cara a incorporar una 3ª cuenta EmailJS de
backup): ¿el contador de envíos se está llevando correctamente? ¿se
descuentan todos los correos, incluidos los automáticos, los de
recuperación de contraseña, los de petición de usuario, etc.?

**Investigación**: revisado el helper central `enviarEmailJS()`
(`templates/index.html`) — confirmado que es el único punto que llama a
`emailjs.send()` en todo el frontend (grep de `emailjs\.send\(` — un
único resultado, dentro del propio helper), así que no hay ningún envío
que se salte el wrapper por error de código. El wrapper llama después a
`POST /api/emailjs/registrar-envio` para incrementar el contador.

**Bug real encontrado**: ese endpoint llevaba `@login_required` a secas.
Tres flujos legítimos llaman a `enviarEmailJS()` desde un navegador
**sin sesión iniciada todavía** — el email SÍ se envía de verdad
(`emailjs.send()` no necesita login), pero la llamada posterior a
`registrar-envio` fallaba con 401 y se descartaba en silencio (a
propósito, para no romper el envío ya hecho), así que el contador nunca
se enteraba:
1. Recuperación de contraseña (`solicitar_reset_password` → el usuario
   aún no ha iniciado sesión).
2. Código de verificación de login (`login()`, cuando hace falta
   verificación por inactividad — el email se envía ANTES de que
   `_completar_login()` cree la sesión).
3. Confirmación de "Fase 2" de solicitar acceso
   (`solicitar_usuario_fase2()`, usuario nuevo sin cuenta —
   `sin_email=True` siempre, no solo como fallback).

Los correos automáticos de sistema (reclamaciones, avisos de firma
pendiente, resumen de "Comparar listado PDF", etc.) SÍ se contaban bien
— se despachan vía `_enviarEmailsSistemaPendientes()`, pero solo
mientras un admin/compras tiene la app abierta, es decir, con sesión ya
iniciada.

**Corrección** (sin quitar la protección del endpoint por completo):
nueva función `_permite_registrar_envio_no_autenticado()` — los 3
endpoints anteriores dejan ahora, justo antes de devolver los datos del
email pendiente de enviar, una marca de UN SOLO USO en la sesión
(`session["pdte_registrar_envio_email"] = True`, sin necesidad de
login). `registrar-envio` acepta la petición si hay sesión válida O si
esa marca está presente — y la consume con `pop` (no `get`), así que no
sirve más que para ese envío concreto: no abre la puerta a que cualquiera
incremente el contador a voluntad desde fuera.

Verificado con un Flask de prueba aislado (sin depender de la base de
datos real): sin marca ni sesión → 401 (protegido); tras la marca que
deja el backend → el siguiente registrar-envio → 200; un segundo intento
sin volver a marcar → 401 de nuevo (uso único confirmado, no reutilizable).

`app.py` compila sin errores. Sin cambios en `templates/index.html` (el
frontend ya llamaba correctamente a `enviarEmailJS()`/`registrar-envio`
en los 3 casos — el bug estaba solo en el backend). `README.md`
actualizado. Badge de versión del sidebar actualizado a "V 12.29.92".

**Pendiente, a petición del usuario**: incorporar una 3ª cuenta EmailJS
de backup (actualmente el sistema rota entre 2, cuenta 1 ⇄ cuenta 2) —
no incluido en esta entrega, a la espera de confirmar alcance.

# v12.29.90 — 11 agosto 2026 13:30

🏷️ Nuevo "estado aparente" en el correo (ENTREGA PARCIAL / ENTREGA COMPLETA), a partir de la 8ª columna del listado SAP

**Petición del usuario**: si el valor de la 8ª columna del PDF (importe
pendiente) es superior a 0, indicar en el correo con estado aparente
"ENTREGA PARCIAL"; si es 0 o negativo, "ENTREGA COMPLETA" — ambos casos
se muestran, para revisión final por el comprador y el hotel.

**Cambio**: la 8ª columna del listado simplificado (importe pendiente),
que hasta ahora se descartaba (`(?:...)`, grupo no capturado), pasa a
capturarse y usarse. Nueva función `_estado_aparente_entrega()` — a
propósito **independiente** de `_entrega_estado()` (que compara base
vs. recibido, columnas 6/7): el importe pendiente que trae SAP no
siempre coincide con "base − recibido" calculado a mano (confirmado
con el propio PDF real, p.ej. pedido 00029249: base 164,39, recibido
0,00, pendiente informado 193,40 — no cuadra la resta), así que se usa
tal cual lo da SAP en vez de recalcularlo.

Regla aplicada literalmente: `pendiente > 0` → `"ENTREGA PARCIAL"`;
`pendiente == 0` o negativo → `"ENTREGA COMPLETA"`. Se llama "aparente"
a propósito: es una lectura directa del PDF, no una verificación.

Nuevo campo `estado_aparente` en cada pedido del resultado (además de
`importe_pendiente`). `_email_resumen_pdf_sap()` añade una columna
"Estado aparente" a la tabla del correo (verde para ENTREGA COMPLETA,
ámbar para ENTREGA PARCIAL) y una nota aclaratoria de que es una
lectura automática pendiente de confirmación final por el comprador y
el hotel.

Verificado contra el listado real de 221 pedidos (hotel MT): 221/221
reconocidos con los 10 grupos del patrón (antes 9), 116 ENTREGA
PARCIAL / 105 ENTREGA COMPLETA, suma correcta. Probado también el
correo con datos reales: la columna y la nota aparecen correctamente.

`app.py` compila sin errores. Los 9 bloques `<script>` de
`templates/index.html` pasan `node --check` (sin cambios de frontend
en esta entrega — el cambio es 100% de `app.py`). `README.md`
actualizado. Badge de versión del sidebar actualizado a "V 12.29.90".

# v12.29.88 — 11 agosto 2026 13:15

📧 Correo de resumen "Comparar listado PDF": solo pedidos con proveedor identificado

**Petición del usuario**: en el correo de resumen que se envía al
comprador, solo deben aparecer los pedidos cuyo proveedor se ha
identificado correctamente contra el catálogo — el resto de información
(pedidos de proveedor no identificado) es solo para revisión visual del
admin en la propia pantalla, no debe salir en el correo.

**Cambio** (`comparar_listado_pdf_enviar_resumen`): los pedidos sin dar
de alta se filtran ahora en dos grupos —
`pedidos_faltantes` (proveedor identificado, `proveedor_identificado:
true`) es lo único que entra en la tabla del correo; `no_identificados`
es solo un recuento. Si no queda ningún pedido con proveedor
identificado, el endpoint devuelve un aviso claro en vez de enviar un
correo vacío (indicando cuántos hay pendientes de revisar en pantalla,
si los hay).

`_email_resumen_pdf_sap()` gana el parámetro `no_identificados`: si es
mayor que 0, añade una nota de aviso (⚠️, fondo amarillo) indicando
cuántos pedidos adicionales hay sin dar de alta pero con proveedor no
identificado, sin listarlos — remite a revisarlos en pantalla en vez de
incluirlos con datos no del todo fiables.

`templates/index.html`: el botón "📧 Enviar resumen por correo" ahora
solo se muestra si hay al menos un pedido faltante CON proveedor
identificado (antes se mostraba con cualquier pedido faltante,
identificado o no) — evita un clic que solo lleva a un error si todo lo
pendiente es de proveedor no identificado.

Probado con datos simulados extraídos directamente de las funciones
reales del código (`_email_resumen_pdf_sap`): un pedido de proveedor no
identificado no aparece en la tabla del correo, y si hay alguno, la nota
de aviso con el recuento sí aparece.

`app.py` compila sin errores. Los 9 bloques `<script>` de
`templates/index.html` pasan `node --check`. `README.md` actualizado.
Badge de versión del sidebar actualizado a "V 12.29.88".

# v12.29.86 — 11 agosto 2026 12:10

✨ "Comparar listado PDF" pasa a leer el listado SIMPLIFICADO de SAP (MT2) + estado de entrega derivado

**Petición del usuario**: adaptar "Comparar listado PDF" para leer el
"Listado de Pedidos" SIMPLIFICADO que exporta SAP (una línea por pedido,
sin el detalle de artículos — mucho más ligero que el listado completo
usado hasta ahora, MT) y, aprovechando que esa vista trae el importe del
pedido y el importe recibido en la misma línea, deducir el estado real
de entrega de cada pedido sin abrir el listado completo: importe
recibido = 0 → "No entregado"; importe recibido = importe del pedido →
"Entregado"; cualquier otra cantidad → "Entrega parcial".

**Cambio principal**: nuevo patrón de reconocimiento
`_PATRON_LISTADO_SIMPLIFICADO` (sustituye al anterior, pensado para el
listado completo con artículos) — verificado contra un listado real de
221 pedidos del hotel MT, 221/221 reconocidos.

**Hallazgo 1** (durante la propia verificación): el texto que devuelve
`pypdf.extract_text()` para este PDF NO sigue el orden visual de las
columnas de la tabla, sino el orden real del contenido del PDF (Nº
pedido, fecha/hora, importe base, proveedor, fecha pedido, fecha
entrega, estado, importe recibido, importe pendiente) — el patrón se
construyó contra ese orden real, no el visual.

**Hallazgo 2** (tras una primera entrega que el usuario reportó con "No
se ha reconocido ningún pedido en el PDF"): la verificación previa se
hizo sin querer con `pypdf` 3.17.4 (versión antigua ya presente en el
entorno de pruebas), no con la que realmente instala este proyecto
(`requirements.txt`: `pypdf>=4.0`, sin techo → instala la última
disponible, 6.15.0 en el momento de esta entrega). Entre pypdf 3.x y ≥4
cambió el extractor de texto: donde el PDF no tiene un espacio real
entre dos columnas contiguas (solo separación por posición X), pypdf
3.x rellenaba con un espacio al extraer el texto y pypdf ≥4 ya no lo
hace — el texto sale pegado ("2.852,10PILSA HOSTELERIA...") justo en 3
de los separadores del patrón, que exigían espacio obligatorio y por
eso no reconocían nada en el entorno real.

**Corrección**: esos separadores (y el resto, por consistencia) pasan de
"uno o más espacios" a "cero o más" — sigue funcionando igual si hay
espacio, y ya no rompe si no lo hay. Reverificado contra el mismo
listado real de 221 pedidos con pypdf 3.17.4 Y con pypdf 6.15.0
(221/221 en ambos casos) antes de esta entrega.

**Nuevos campos** por pedido en el resultado: `fecha_pedido`,
`fecha_entrega`, `importe_base`, `importe_recibido`, `estado_sap`
(Abierto/Cerrado tal cual lo trae SAP) y `entrega_estado` (Entregado /
Entrega parcial / No entregado). El resumen añade contadores
`entregados`/`entregas_parciales`/`no_entregados`. Tabla de "Comparar
listado PDF" con columnas nuevas, filtro por estado de entrega y
píldoras de resumen; correo de resumen con columna de estado de entrega.

`app.py` compila sin errores. Los 9 bloques `<script>` de
`templates/index.html` pasan `node --check`. `README.md` actualizado.
Badge de versión del sidebar actualizado a "V 12.29.86".

# v12.29.84 — 11 agosto 2026 09:00

⚡ Correo de resumen: despacho inmediato en vez de esperar al ciclo de 5 min

**Consulta del usuario**: el correo de resumen llegó bien, pero tardó "un
ratito" — no fue casi automático como el resto de correos, ¿por qué?

**Respuesta**: es exactamente el mismo sistema de siempre (confirmado
revisando el código) — pero el navegador solo revisa la cola de correos
pendientes cada 5 minutos (`_startEmailsSistemaPolling`,
`setInterval(...,  5*60*1000)`). Con las alertas automáticas nunca se
nota, porque solo se ven ya llegadas en la bandeja; al pulsar un botón y
quedarse esperando, si toca a mitad del ciclo de 5 min, sí se nota.

**Mejora**: `enviarResumenComparacionPdf()` dispara ahora un despacho
inmediato (`_enviarEmailsSistemaPendientes()`) justo después de encolar
el correo, desde el propio navegador que acaba de generarlo — mismo
mecanismo de siempre (EmailJS desde el navegador), solo se adelanta el
primer intento en vez de esperar al siguiente ciclo automático.

`app.py` sin cambios (solo frontend). Los 9 bloques `<script>` pasan
`node --check`. `README.md` actualizado. Badge de versión del sidebar
actualizado a "V 12.29.84".

# v12.29.82 — 10 agosto 2026 13:10

🔧 Correo de resumen: confirmado el filtrado + columnas reordenadas

**Pregunta del usuario**: ¿qué tratamiento reciben los "NO encontrados"
en el correo de resumen? ¿solo se envían los sujetos a seguimiento?

**Confirmado revisando el propio código**: `resultado["pedidos"]` (de
donde se filtran los "no encontrados" para el correo) nunca contiene los
proveedores excluidos — se descartan antes, en
`_comparar_listado_pdf_logica()` (`if prov_match and not
prov_match["sujeto_seguimiento"]: continue`). Es decir, el correo ya
enviaba exactamente lo pedido: solo pedidos sujetos a seguimiento y no
registrados en la app — es imposible que se cuele uno excluido, porque
nunca llega a entrar en la lista de la que se filtra.

**Único ajuste real**: orden de columnas de la tabla del correo, a
petición del usuario — Nº Pedido → Proveedor → Fecha (antes Nº Pedido →
Fecha → Proveedor). Verificado con datos simulados extraídos con `ast`.

`app.py` compila sin errores. `README.md` actualizado. Badge de versión
del sidebar actualizado a "V 12.29.82".

# v12.29.80 — 10 agosto 2026 12:50

✨ "Comparar listado PDF": correo de resumen al comprador + texto aclarado

**Petición**: 1) que el resultado solo muestre pedidos de proveedores
sujetos a seguimiento, indicando el resto solo como recuento; 2) enviar
un correo interno al comprador responsable del hotel, con copia al
administrador que hace la consulta, con el resumen de pedidos detectados
en SAP/DALI pendientes de dar de alta en la app.

**1) Ya lo hacía** (desde el diseño original), solo se ajustó el texto
del recuento a la redacción exacta pedida: "➖ X pedidos de proveedores
no sujetos a seguimiento" (antes "excluidos (sin seguimiento)") — la
tabla de resultados solo ha mostrado nunca los evaluados.

**2) Nuevo — correo de resumen:**
- Nuevo botón "📧 Enviar resumen por correo" en el resultado, visible
  solo si hay pedidos sin registrar. Acción explícita, no automática al
  terminar la comparación — para no reenviar sin querer si se vuelve a
  comparar el mismo listado mientras se revisa el resultado.
- Nuevo `POST /api/pedidos/comparar-listado-pdf/<job_id>/enviar-resumen`:
  busca el/los comprador(es) del hotel (`_get_compradores_hotel()`, ya
  existente — misma asignación que usan las alertas), y encola un correo
  con copia al administrador que hizo la consulta (mismo mecanismo de
  cola que el resto de correos automáticos de la app —
  `_encolar_email_sistema()`, se despacha desde el navegador de quien
  tenga la app abierta).
- Nueva plantilla `_email_resumen_pdf_sap()` — mismo estilo visual que
  el resto de correos internos de la app; tabla con Nº de pedido SAP,
  fecha y proveedor, acotada a 100 filas (con aviso de "y X más" si hay
  más) para no generar un correo kilométrico con listados grandes.
  Probada con datos simulados: asunto correcto, recorte a 100 filas y
  aviso del resto funcionando.
- Si el hotel no tiene ningún comprador con email asignado, el endpoint
  avisa con un error claro en vez de fallar en silencio.

`app.py` compila sin errores; los 9 bloques `<script>` de
`templates/index.html` pasan `node --check`. `README.md` actualizado.
Badge de versión del sidebar actualizado a "V 12.29.80".

# v12.29.78 — 10 agosto 2026 12:15

🐛 Fix: "El job no existe o ha caducado" al comparar un listado PDF

**Reportado con captura**: al comparar el listado, el primer sondeo ya
daba "El job no existe o ha caducado — vuelve a subir el PDF", pese a
que el `job_id` se había creado bien un instante antes (v12.29.74).

**Causa probable**: `render.yaml` arrancaba gunicorn con
`--workers 1` sin más — que usa por defecto el tipo de worker **"sync"**,
capaz de atender solo **una petición a la vez** en todo el proceso.
Mientras el hilo en segundo plano de v12.29.74 procesaba el PDF (~8s de
trabajo intensivo), el proceso podía quedarse sin responder con la
rapidez que exige el *health check* de Render (`healthCheckPath: /ping`)
— y si Render considera el proceso no saludable aunque sea un instante,
**reinicia el contenedor**, lo que borra de golpe toda la memoria del
proceso (incluido `_PDF_JOBS`, donde vivía el job a medias).

**Corregido**: `startCommand` en `render.yaml` cambia a
`--worker-class gthread --threads 4` — reparte las peticiones entrantes
del mismo worker entre varios hilos, así que el health check y los
sondeos del navegador se siguen atendiendo con normalidad mientras el
hilo de fondo procesa el PDF. No requiere ninguna dependencia nueva
(`gthread` es un tipo de worker propio de gunicorn, ya en
`requirements.txt`).

**⚠️ Importante para el despliegue**: si tu servicio en Render tiene el
"Start Command" configurado directamente en el panel de Render (Settings
→ Start Command), en vez de leerlo de `render.yaml` en cada despliegue,
tendrás que actualizarlo también ahí a mano con el mismo comando —
`render.yaml` por sí solo no basta si el servicio no está gestionado
como Blueprint desde este archivo.

`app.py` sin cambios — este fix es solo de configuración de despliegue.
Badge de versión del sidebar actualizado a "V 12.29.78".

# v12.29.76 — 10 agosto 2026 11:35

✨ Spinner de carga profesional, en los colores de marca

**Petición:** algo visual y profesional mientras se procesa (p. ej. el
listado PDF) — en vez del texto plano actual, algo tipo el círculo de
carga de Windows.

**Cambio:** la clase `.loading` (usada en "cargando pedidos" y en
"Comparar listado PDF") ahora dibuja un spinner con CSS puro, sin
imágenes ni dependencias nuevas — un anillo girando en dorado (estilo
Windows) con un círculo interior que se llena y se vacía en azul marino,
los colores de marca de la app (`--gold`/`--navy2`). Al construirse con
`::before`/`::after` sobre la propia clase, no ha hecho falta tocar el
HTML de ninguna de las 2 pantallas que ya la usaban — lo heredan
automáticamente.

`app.py` sin cambios (solo CSS). Los 9 bloques `<script>` de
`templates/index.html` pasan `node --check`; llaves del bloque `<style>`
comprobadas cuadradas (301/301). `README.md` actualizado. Badge de
versión del sidebar actualizado a "V 12.29.76".

# v12.29.74 — 10 agosto 2026 11:10

🐛 Fix: "Comparar listado PDF" fallaba con PDFs grandes ("Unexpected token '<' ... is not valid JSON")

**Reportado con captura + PDF real** (178 páginas, hotel MT): al comparar,
saltaba el error `Unexpected token '<', "<html>" is not valid JSON`.

**Causa:** el proceso completo — leer el PDF, extraer el texto de las 178
páginas (~8s medidos contra el propio PDF real) y comparar contra los
pedidos ya registrados — se hacía todo dentro de una única petición
HTTP. Con el cold-start del servicio gratuito de Render sumado a esos
~8s de proceso, la petición tardaba más que el timeout de algún punto
intermedio entre el navegador y el servidor (el proxy delante de la
app), que cortaba la conexión y devolvía su propia página de error HTML
en lugar de dejar pasar la respuesta JSON — de ahí el "`<html>`" en el
mensaje.

**Corregido haciendo el endpoint asíncrono:**
- `POST /api/pedidos/comparar-listado-pdf` ahora solo valida el archivo y
  arranca el trabajo pesado en un hilo aparte (`threading`), respondiendo
  **al momento** con un `job_id` — muy por debajo de cualquier timeout,
  sea cual sea.
- Nuevo `GET /api/pedidos/comparar-listado-pdf/<job_id>` para consultar
  el resultado — el frontend hace polling cada 2 segundos (hasta 5
  minutos) en vez de esperar una sola respuesta larga.
- El hilo en segundo plano usa `with app.app_context()`, mismo patrón ya
  usado en `init_db()`, porque `query()`/`get_db()` dependen de `g` (con
  ámbito de petición, no accesible desde un hilo nuevo sin esto).
- Estado de los jobs en memoria (`_PDF_JOBS`, con lock), con limpieza
  automática de jobs de más de 30 minutos para no acumular memoria.
- La lógica de extracción/comparación en sí no cambia — se movió a
  `_comparar_listado_pdf_logica()`, probada de nuevo contra el PDF real
  del reporte (178 páginas / 563 pedidos) para confirmar que el
  comportamiento es idéntico tras el refactor.

`app.py` compila sin errores; los 9 bloques `<script>` de
`templates/index.html` pasan `node --check`. `README.md` actualizado.
Badge de versión del sidebar actualizado a "V 12.29.74".

# v12.29.72 — 10 agosto 2026 10:30

🔒 "Sujeto a seguimiento" — restringido solo a Admin (Compras sigue pudiendo editar el resto de la ficha)

**Petición:** los roles hotel y compras no deben poder modificar el campo
"Sujeto a seguimiento en Comparar listado PDF" de la ficha de proveedor.

- **Hotel** ya no podía crear ni editar proveedores en absoluto
  (`create_proveedor`/`update_proveedor` ya devolvían 403) — sin cambios
  necesarios ahí.
- **Compras** sí puede seguir editando la ficha del proveedor con
  normalidad (nombre, código, contactos, observaciones), pero ya no este
  campo en concreto:
  - Backend: al crear, si quien hace la petición no es admin, se crea
    siempre con el valor por defecto (`FALSE`), ignorando lo que trajera
    el payload. Al editar, si no es admin, se conserva el valor que ya
    tuviera guardado el proveedor en vez de aceptar lo que llegue en la
    petición — así, aunque compras edite otra cosa de la ficha (un
    contacto, por ejemplo), este campo no se toca ni se resetea sin
    querer.
  - Frontend: el checkbox se deshabilita (no solo se oculta) para
    cualquiera que no sea admin, con un aviso "Solo un administrador
    puede cambiar esto" — doble seguridad, el backend rechaza el cambio
    igualmente aunque alguien fuerce el DOM.

`app.py` compila sin errores; los 9 bloques `<script>` pasan
`node --check`. `README.md` actualizado. Badge de versión del sidebar
actualizado a "V 12.29.72".

# v12.29.70 — 10 agosto 2026 10:05

🐛 Fix: los proveedores seguían saliendo "Sujeto a seguimiento" pese al cambio a opt-in

**Reportado con captura**: al editar un proveedor, el checkbox salía
marcado — contradiciendo el texto de ayuda de al lado, que ya decía
"Desmarcado por defecto para todos los proveedores".

**Causa**: el SQL de emergencia entregado ayer para desbloquear
`/api/proveedores` (v12.29.66, antes de pedir el cambio a opt-in) creaba
la columna con `DEFAULT TRUE`. Al ejecutarse, la columna `sujeto_seguimiento`
quedó creada con todos los proveedores en `TRUE` — y la migración de
v12.29.68 (`ADD COLUMN IF NOT EXISTS ... DEFAULT FALSE`) es un no-op si
la columna ya existe, así que nunca corrigió nada.

**Corregido**: nueva migración que consulta el `DEFAULT` real de la
columna en `information_schema` y, si no es `FALSE` (columna inexistente
o con el `DEFAULT` antiguo), corrige el `DEFAULT` **y** resetea a `FALSE`
los proveedores que estuvieran en `TRUE` — seguro de hacer porque, al ser
una funcionalidad recién nacida y con la pantalla rota hasta ahora,
nadie ha podido marcar todavía ninguno a propósito. Es correctiva y de
una sola vez: en cuanto el `DEFAULT` quede en `FALSE`, deja de tocar
nada en arranques futuros — cualquier proveedor que un admin marque
después queda a salvo para siempre.

`app.py` compila sin errores. `README.md` actualizado. Badge de versión
del sidebar actualizado a "V 12.29.70".

# v12.29.68 — 10 agosto 2026 09:20

🔧 3 ajustes: causa raíz del fallo de migración, "Comparar listado PDF" solo admin, filtro de proveedores invertido a opt-in

**1) Causa raíz del fallo de migración (RLS + sujeto_seguimiento seguían sin aplicarse en v12.29.64):**
Las 3 migraciones más recientes (RLS, `sujeto_seguimiento`, hotel de
pruebas `PR`) vivían casi al final de `_auto_migrate()`, una función con
111 sentencias en total. Si cualquiera de las ~108 sentencias
*anteriores* a ellas fallaba por el motivo que fuera, el `except`
genérico de toda la función paraba la ejecución ahí mismo y estas 3
nunca llegaban a aplicarse — coincide exactamente con que el usuario
seguía viendo los errores de RLS en Supabase y el 500 de `/api/proveedores`
incluso en v12.29.64 (posterior a cuando se "arreglaron"). **Movidas las
3 al principio del todo de `_auto_migrate()`**, antes de cualquier otra
sentencia — así se garantiza que se apliquen siempre, pase lo que pase
más abajo en el resto de la función esa misma ejecución.

**2) "Comparar listado PDF" — ahora solo Admin** (antes admin+compras):
backend (`if session.get("rol") != "admin"`) y botón del frontend
actualizados a la vez.

**3) Filtro de proveedores invertido a opt-in** (antes opt-out): con
tantos proveedores de compra diaria frente a los pocos que interesa
seguir, es más seguro que todos empiecen apagados y el admin encienda
solo los que quiere vigilar. `sujeto_seguimiento` pasa a `DEFAULT FALSE`;
checkbox de la ficha de proveedor desmarcado por defecto (tanto al crear
como al no haberlo marcado nunca en uno existente); avisado en el propio
endpoint de comparación: hasta que se marquen proveedores, el listado
devolverá pocos o ningún pedido evaluado — comportamiento esperado, no
un fallo.

`app.py` compila sin errores; los 9 bloques `<script>` pasan
`node --check`. `README.md` actualizado. Badge de versión del sidebar
actualizado a "V 12.29.68".

# v12.29.66 — 10 agosto 2026 08:40

🐛 Fix: /api/proveedores caía con 500 — migración de sujeto_seguimiento nunca se ejecutó

**Reportado con captura de la consola del navegador**:
`[500] Error inesperado: column "sujeto_seguimiento" does not exist`.

**Causa:** `_auto_migrate()` tiene 111 sentencias de migración en total, y
la inmensa mayoría (incluida la de `sujeto_seguimiento`, casi al final)
NO tenía su propio `try/except` — si cualquier sentencia ANTERIOR fallaba
por el motivo que fuera (sin relación con este cambio concreto), el
`except` genérico de toda la función paraba ahí la ejecución, y esta
`ALTER TABLE` nunca se llegaba a aplicar.

**Arreglo inmediato para desbloquear ahora mismo, sin esperar a un
redeploy** (comunicado directamente al usuario, seguro de ejecutar a
mano en el SQL Editor de Supabase):
```sql
ALTER TABLE proveedores ADD COLUMN IF NOT EXISTS sujeto_seguimiento BOOLEAN NOT NULL DEFAULT TRUE;
```

**Corregido de raíz:**
- La migración de `sujeto_seguimiento` y la del hotel de pruebas `PR`
  (v12.29.32-33, también bare) se aíslan ahora en su propio
  `try/except` — mismo patrón ya usado para RLS y `expediente_exceso` —
  para que sean robustas frente a cualquier fallo anterior no
  relacionado en la misma ejecución de `_auto_migrate()`.
- `loadProveedores()` (frontend) capturaba la excepción de `api()` sin
  querer: si la petición fallaba, la pantalla se quedaba vacía **sin
  ningún aviso**, indistinguible de "no hay proveedores de verdad" — así
  es como se llegó a reportar esto como "no salen los proveedores" en
  vez de como un error. Ahora se captura y se muestra con un `toast()`
  de error, con el detalle exacto del fallo.
- Pendiente, no localizado en esta corrección: qué sentencia ANTERIOR de
  las 111 de `_auto_migrate()` estuvo fallando y provocando esto —
  revisar el log de arranque real del servidor (buscar
  "Auto-migración omitida") para identificarla, si se quiere ir a la
  causa raíz de fondo en vez de solo blindar las migraciones más
  recientes.

`app.py` compila sin errores; los 9 bloques `<script>` de
`templates/index.html` pasan `node --check`. `README.md` actualizado a la
versión actual. Badge de versión del sidebar actualizado a "V 12.29.66".

# v12.29.64 — 10 agosto 2026 08:15

🔧 Fix: el +34 del teléfono salía duplicado en la firma de los correos

**Reportado con captura**: la firma mostraba `(+34) +34681111792` — el
prefijo repetido.

**Causa:** `_firma_comprador_html()`/`_firma_comprador_text()` anteponen
siempre `"(+34)"` al móvil guardado del usuario, pero el propio campo del
formulario sugiere como placeholder "+34 600 000 000" — algunos usuarios
lo guardan ya con el prefijo incluido, y entonces se duplicaba.

**Corregido:** nuevo helper `_formatear_movil_firma()` que quita
cualquier `+34`/`0034`/`34` inicial (con o sin espacio) del móvil
guardado antes de anteponer el `(+34)` fijo de la firma — el resultado
sale limpio se haya guardado el número como se haya guardado. Probado
contra varios formatos realistas (`+34681111792`, `34681111792`,
`0034681111792`, con espacios...), todos correctos.

`app.py` compila sin errores. `README.md` actualizado a la versión
actual. Badge de versión del sidebar actualizado a "V 12.29.64".

# v12.29.62 — 6 agosto 2026 11:35

🔒 Seguridad — RLS activado en 3 tablas nuevas (aviso del Security Advisor de Supabase)

**Reportado** con el propio informe del linter de Supabase: `RLS Disabled
in Public` sobre `proveedor_contacto_hoteles`, `expediente_exceso` y
`bridge_popup_visto` — 3 tablas creadas en sesiones recientes que se
quedaron sin el mismo `ENABLE ROW LEVEL SECURITY` que ya se aplicaba a
otras 4 tablas desde julio.

**Mismo criterio ya verificado entonces, sin cambios de comportamiento**:
esta app nunca usa la API REST automática de Supabase (PostgREST) — todo
habla por conexión directa a Postgres con `DATABASE_URL`, nunca con la
anon key — así que activar RLS sin ninguna política es 100% seguro para
el funcionamiento; solo cierra el acceso público accidental por esa otra
vía. Añadidas las 3 tablas a la misma lista ya existente en
`_auto_migrate()`.

`app.py` compila sin errores. `README.md` actualizado a la versión
actual. Badge de versión del sidebar actualizado a "V 12.29.62".

# v12.29.60 — 6 agosto 2026 11:20

✨ Nueva funcionalidad: comparar listado PDF de SAP contra los pedidos registrados

**Petición:** poder cargar semanalmente, por hotel, el "Listado de Pedidos"
que exporta SAP, y que la aplicación indique qué pedidos de ese listado NO
están dados de alta aquí para su seguimiento — más un filtro para excluir
proveedores de compra diaria (alimentación/bebida) que no se siguen en
esta app.

**Probado contra un listado real** (262 páginas / 622 pedidos, hotel
Guayarmina) antes de dar la extracción por buena — sin extracción "de IA"
ni nada costoso: el formato de SAP es 100% fijo y predecible (verificado
línea a línea), así que basta con una expresión regular sobre el texto
del PDF. Se encontró y corrigió un caso real de emparejamiento de
proveedor por una tilde ("Pastelería" vs "Pasteleria") durante la propia
prueba.

**Cambios:**
- Nueva dependencia `pypdf` (`requirements.txt`) — lectura del PDF en
  Python puro, sin depender de ningún binario del sistema (más portable
  en Render que `pdftotext`/poppler).
- Nueva columna `sujeto_seguimiento` en `proveedores` (migración
  automática, `DEFAULT TRUE`) — nuevo checkbox en la ficha de cada
  proveedor ("Sujeto a seguimiento en Comparar listado PDF"),
  desmarcable para alimentación/bebida.
- Nuevo endpoint `POST /api/pedidos/comparar-listado-pdf` — recibe un PDF
  + `hotel_id`, extrae todos los números de pedido de SAP con una
  expresión regular ya verificada contra un listado real, y los compara
  contra `pedido_num` de los pedidos de ese hotel en la app. El
  emparejamiento de nombres de proveedor (para aplicar el filtro de
  seguimiento) normaliza acentos, puntuación y formas societarias
  comunes (SL/SA/SLL...), con coincidencia exacta y, si falla, parcial.
- Nuevo botón "📄 Comparar listado PDF" en la pantalla de Pedidos (solo
  admin/compras) — modal con selector de hotel, subida del PDF, resumen
  (encontrados / no encontrados / excluidos por el filtro), tabla
  filtrable ("mostrar solo los que faltan"), y botón de acceso directo
  para crear el pedido que falte con el hotel y el Nº de SAP ya
  rellenados.

`app.py` compila sin errores; los 9 bloques `<script>` de
`templates/index.html` pasan `node --check`. Badge de versión del sidebar
actualizado a "V 12.29.60".

# v12.29.58 — 6 agosto 2026 09:45

🐛 Fix real: el panel de Alertas nunca reflejaba los correos automáticos como enviados

**Confirmado con un correo real recibido por el usuario** (pedido 694, aviso
de firma pendiente) que la pantalla seguía mostrando "Sin notificar" pese a
que el email había salido correctamente.

**Causa:** `ultima_notif_email` (la subconsulta que decide si la columna
"Notificación" del panel de Alertas dice "Notificado" o "Sin notificar")
**solo miraba `emails_log`** — la tabla donde se registran los envíos
MANUALES (botón "Notificar"/"Re-notificar"). Pero **todos los correos
automáticos** (reclamación al proveedor, aviso de firma pendiente, aviso de
cotización sin proveedor...) se encolan y despachan a través de una tabla
distinta, `emails_sistema_pendientes`, que esta subconsulta nunca
consultaba. Resultado: cualquier pedido que solo hubiera recibido avisos
automáticos (nunca un clic manual) se quedaba marcado "Sin notificar" para
siempre en pantalla, aunque el correo hubiera salido de verdad — visible
también en la fila 723 de la propia captura del usuario, con "Reclamado
auto hace hoy" pero "Sin notificar" al mismo tiempo, contradictorio a
simple vista.

**Corregido:** `PEDIDO_SELECT_STATS` combina ahora ambas fuentes con
`GREATEST()` — `emails_log.creado_en` (manual) y
`emails_sistema_pendientes.enviado_en` (automático, solo filas con
`enviado=TRUE`, que es el momento real de envío, no el de encolado). Este
bug era sistemático — afectaba a todo pedido notificado únicamente por vía
automática, no solo al caso reportado.

`README.md` actualizado a la versión actual. `app.py` compila sin errores.
Badge de versión del sidebar actualizado a "V 12.29.58".

# v12.29.56 — 6 agosto 2026 09:15

🐛 Telegram bloqueado por el usuario: dejar de reintentar, en vez de fallar cada día

**Confirmado con log real de Render**: el pedido 13513 fallaba siempre con
`HTTP 403: {"error_code":403,"description":"Forbidden: bot was blocked by
the user"}` — la persona destinataria bloqueó el bot en su Telegram. No es
un fallo del sistema, así que reintentar cada día (con el fix de v12.29.54)
tampoco iba a arreglarlo — a petición del usuario, ahora se da por
terminado en vez de seguir intentándolo indefinidamente.

**Cambios:**
- `_send_telegram()` detecta errores 400/403 de Telegram que indican que
  **nunca** va a poder entregarse reintentando (bot bloqueado, cuenta
  desactivada, chat inexistente) y los marca con un nuevo flag
  `permanente: True` — a diferencia de un fallo transitorio (timeout, 5xx),
  que sí debe seguir reintentándose al día siguiente.
- Los 4 puntos donde se registra el resultado en `whatsapp_log`
  (`telegram_estado`, `telegram_auto` ×2, `telegram_techo`) tratan ahora
  `ok=True OR permanente=True` como "hecho" — un bot bloqueado deja de
  generar un intento fallido cada día, sin necesidad de tocar nada más.
- El correo automático NO se ve afectado por este cambio — es un canal
  totalmente independiente (cola `emails_sistema_pendientes`, revisado
  aparte a petición del usuario: sin ningún bug encontrado, el
  comportamiento es el esperado del diseño "se envía desde el navegador
  de quien tenga la app abierta").

`app.py` compila sin errores. Badge de versión del sidebar actualizado a
"V 12.29.56".

# v12.29.54 — 6 agosto 2026 08:30

🐛 Fix: un envío fallido bloqueaba las notificaciones automáticas para siempre

**Reportado:** pedidos con 50-65 días sin firma/cotización seguían en "Sin
notificar" pese a llevar muchísimo tiempo esperando, mientras otros del
mismo hotel sí se notificaban con normalidad. Diagnosticado con logs de
Render en varias rondas (`RECLAMACION-DEBUG` y `[SCHEDULER]`).

**Causa real, confirmada en el código:** `_nunca_notificado()` y
`_ya_notificado_hoy()` contaban CUALQUIER fila en `whatsapp_log`, tuviera
o no éxito (`enviado=0` también contaba). Si el primer intento de enviar
un Telegram fallaba — por ejemplo, sin destinatarios configurados para
ese hotel en el evento "alerta_pedido_hotel" (Admin → Config. Avisos) —
igual quedaba registrada una fila, y a partir de ahí el sistema daba por
"ya intentado" un envío que nunca llegó a nadie, **bloqueando cualquier
reintento para siempre**. La pantalla de Alertas, en cambio, sí distinguía
bien éxito de fallo — por eso seguía mostrando correctamente "Sin
notificar" mientras el sistema, por dentro, ya había dejado de intentarlo.

**Corregido con cuidado de no crear un problema nuevo:**
- `_nunca_notificado()` ahora exige `enviado=1` — un fallo ya no cuenta
  como "hecho para siempre".
- `_ya_notificado_hoy()` se deja **a propósito sin ese filtro** — sigue
  contando cualquier intento (éxito o fallo) dentro del MISMO día, para
  seguir frenando reintentos cada minuto si algo sigue fallando. El
  resultado: un pedido que falla se reintenta **una vez al día**, no
  1440 veces — hasta que se resuelva la causa de fondo (previsiblemente,
  revisar los destinatarios de "alerta_pedido_hotel" para el hotel
  afectado en Admin → Config. Avisos) y el envío tenga éxito de verdad.
- Mismo fix aplicado a `_ya_reclamado_hoy_manual()`, revertido después al
  mismo criterio por la misma razón — solo se mantiene el fix en
  `_nunca_notificado()`.

`app.py` compila sin errores. Badge de versión del sidebar actualizado a
"V 12.29.54".

# v12.29.53 — 5 agosto 2026

✨ Fecha de entrega prevista ("📅 fecha") visible también en la lista
de Pedidos, no solo en Alertas

**Petición:** el usuario observó que bajo "F. Tramitación" algunos
pedidos muestran una fecha de entrega estimada y otros no, y pensó que
dependía de si el criterio configurado era "días de plazo" o "fecha
prevista" del proveedor. Al revisar el código se confirmó que **no**
depende del origen del dato (ambos casos usan el mismo campo
`fecha_entrega_prevista`, con prioridad fecha específica → plazo en
días) — lo que pasaba es que esa fecha solo se mostraba en la pantalla
de **Alertas**, nunca en la lista de **Pedidos** (que además solo
enseña los pedidos que ese día generan alerta, así que un pedido con
fecha de entrega aún lejana puede no aparecer ahí en absoluto, sin
relación con el tipo de dato). El usuario pidió ver la misma
información en ambas pantallas.

**Cambios (`templates/index.html`):**
- Nueva función `_fechaEntregaPrevistaCliente(p)`: calcula en cliente
  la fecha de entrega prevista de un pedido con la misma prioridad
  que el backend (`_resolver_fecha_entrega_prevista` en `app.py`):
  1) `fecha_entrega_especifica` si el proveedor dio un día concreto;
  2) `fecha_tramitacion + plazo_entrega_dias` si hay plazo informado;
  3) nada si no hay ninguno de los dos. No requiere cambios en el
  backend: `/api/pedidos` ya devuelve `plazo_entrega_dias` y
  `fecha_entrega_especifica` en cada pedido (`p.*` de `PEDIDO_SELECT`).
- `renderPedidosTable()`: la celda de F. Tramitación ahora añade,
  cuando aplica, la misma línea "📅 fecha" (mismo estilo y tooltip)
  que ya existía en la tabla de Alertas — se muestra para cualquier
  pedido con fecha específica o plazo informados, sin depender de si
  hoy genera o no alerta.

**Archivos entregados en esta corrección:** `templates/index.html`,
`CHANGELOG.md`, `docs/HISTORIAL_CAMBIOS.md`, `README.md` (solo el
número de versión). `app.py` no se ha tocado — el dato ya se recibía
en el frontend, solo faltaba calcularlo y pintarlo en esa tabla.

# v12.29.52 — 5 agosto 2026

🐛 Fix crítico: pedidos con "Fecha de entrega específica" (o "Plazo
entrega") todavía lejana se reclamaban automáticamente al proveedor
por el criterio equivocado (días desde tramitación)

**Síntoma reportado:** el pedido 692 (GY, CASA DELFIN SA), con
`Fecha de entrega específica = 27/08/2026` indicada por el propio
proveedor, apareció en Alertas como 🔴 URGENTE con "37 días" y "🚚
Reclamado auto hoy" — pese a que aún faltaban 22 días para la fecha
que el proveedor había comprometido.

**Causa raíz (`app.py`):** existen dos vías para calcular si un
pedido en ENVIADO AL PROVEEDOR / ENTREGA PARCIAL debe generar alerta:
1. **Vía plazo** (`_alertas_plazo_entrega`): usa la fecha de entrega
   específica o `fecha_tramitacion + plazo_entrega_dias`, con aviso
   solo en días concretos (N días antes, el día exacto, y cada M días
   después de vencer). Fuera de esos días concretos devuelve `None`.
2. **Vía estándar** (`_build_umbrales`): cuenta días desde
   `fecha_tramitacion` sin mirar ninguna fecha de entrega, con
   umbrales fijos por estado (p. ej. "Urgente = 20 días").

Tanto en el job diario (`_job_alertas_diarias_inner`) como en el
endpoint que alimenta la pantalla de Alertas (`_clasificar_alertas`,
usado por `/api/stats`), el código decidía qué vía usar con
`if info_plazo: ... else: <vía estándar>`. El problema: `None` de la
vía 1 significa dos cosas distintas que el código no distinguía —
"este pedido no tiene fecha/plazo informado" (correcto caer a la vía
estándar) **o** "este pedido sí tiene fecha informada, pero hoy no es
un día de aviso por esa vía" (no debería caer a ningún sitio, debería
significar simplemente "sin alerta hoy"). En el segundo caso, el
código caía igualmente a la vía estándar, que solo mira días desde
`fecha_tramitacion` (37 días en este caso) e ignora por completo que
el proveedor ya dio una fecha de entrega concreta y todavía vigente
— de ahí la reclamación automática injustificada.

Existía ya una función `_debe_usar_logica_plazo(pedido)`, escrita
exactamente para resolver esta ambigüedad (comprueba si el pedido
tiene plazo/fecha informados Y la función está activada), pero
**nunca se llamaba desde ningún sitio** — quedó huérfana.

**Corrección:** en ambos puntos (`_job_alertas_diarias_inner` y
`_clasificar_alertas`), se usa ahora `_debe_usar_logica_plazo(p)` para
decidir de entrada si el pedido "vive" en la vía de plazo. Si es así:
- Se evalúa `_alertas_plazo_entrega()`.
- Si hoy no toca aviso por esa vía, se omite sin más (no se genera
  alerta, no se reclama, no cae a la vía estándar).
- La vía estándar (días desde `fecha_tramitacion`) solo se aplica
  ahora a pedidos que **no** tienen ninguna fecha/plazo de entrega
  informado, o cuando la función está desactivada globalmente
  (`activar_uso_plazo_entrega = 0`).

**Nota importante:** este fix evita que se repita a partir de ahora,
pero la reclamación automática de hoy para el pedido 692 ya salió
(encolada/enviada al proveedor) antes de aplicar la corrección — no
se puede deshacer un correo ya enviado. Si hace falta, se puede
avisar manualmente al proveedor de que la reclamación fue un error
del sistema.

**Archivos entregados en esta corrección:** `app.py`,
`templates/index.html` (solo el badge de versión), `CHANGELOG.md`,
`docs/HISTORIAL_CAMBIOS.md`, `README.md`.

# v12.29.51 — 4 agosto 2026

🐛 Fix: contador de pedidos ("N pedidos") se quedaba con el valor
anterior cuando la búsqueda no encontraba resultados

**Contexto:** al investigar un reporte de "la búsqueda por Nº de
pedido no funciona" (que resultó ser un error de tecleo del usuario —
buscaba `4130` en vez de `40130`, no un bug de la búsqueda en sí), se
revisó el flujo completo de `loadPedidos()` y sí apareció un bug real:
con 0 resultados, la vista mostraba "No hay pedidos que mostrar" pero
el contador inferior seguía marcando el total de la carga anterior
(p. ej. "721 pedidos"), dando la falsa impresión de que la búsqueda no
se había aplicado.

**Causa (`templates/index.html`, `loadPedidos()`):** `renderPagination()`
—la única función que actualiza `#page-info-text` y `#pagination`—
solo se llamaba dentro de la rama `else` (cuando sí hay resultados).
La rama `if (!d.pedidos.length)` únicamente mostraba el mensaje de
vacío, sin tocar el contador ni la paginación, que quedaban con lo
último renderizado.

**Corrección:** en la rama de 0 resultados, ahora también se fija
`#page-info-text` a `"0 pedidos"` y se vacía `#pagination`
(`innerHTML=''`), igual que ocurre con cualquier búsqueda vacía.

**Archivos entregados en esta corrección:** `templates/index.html`,
`CHANGELOG.md`, `docs/HISTORIAL_CAMBIOS.md`, `README.md` (solo el
número de versión). Confirmado con `node --check` sobre los 8 bloques
`<script>` del HTML.

# v12.29.50 — 4 agosto 2026

🎨 Rol `hotel` sin acceso visible a editar/crear proveedores + avisos de
validación del modal de Pedidos con el mismo patrón visual que "Acceso
restringido"

**Petición 1 — confirmación de permisos:** se confirmó que el rol
`hotel` no debe poder crear ni editar proveedores (solo `admin` y
`compras`, ver v12.29.49). Hasta ahora el backend ya lo bloqueaba
(403), pero el frontend seguía mostrando el botón "✏ Editar" en la
lista de Proveedores para `hotel`, así que al pulsar Guardar el
usuario se encontraba con el mismo problema de antes (fallo
silencioso). Se pidió "evitar los errores siempre", es decir, no
mostrar acciones que el usuario no puede completar.

**Cambios (`templates/index.html`):**
- Vista Proveedores (`loadProveedores` → template de fila): para
  `rol === 'hotel'` el botón "✏ Editar" se sustituye por un indicador
  "🔒 Solo lectura" (con tooltip explicativo); para `admin` y
  `compras` se mantiene el botón como hasta ahora.
- `saveProveedor()`: guardia defensiva añadida al inicio de la
  función — si `G.rol === 'hotel'` corta la ejecución y muestra el
  nuevo aviso visual (ver siguiente punto) en vez de dejar que la
  petición llegue al backend y falle en silencio. Es un cinturón de
  seguridad adicional al botón oculto, por si se invocara la función
  desde otro punto en el futuro.

**Petición 2 — avisos de validación más visuales en el modal de
Pedidos:** se pidió que los errores de "falta algo" en la ventana de
crear/editar pedido (hotel, nota obligatoria, proveedor sin email,
Nº Pedido/PDF faltante, familia/importe del techo, errores del
backend, error de conexión) se muestren con el mismo patrón visual
que el aviso "🔒 Acceso restringido" del sidebar (tarjeta oscura
centrada, con título e icono, en vez del pequeño toast rojo de la
esquina, "más visual").

**Cambios (`templates/index.html`):**
- Nuevo componente `#form-alert-toast` (HTML + CSS), mismo patrón
  visual que `#sb-access-toast` (tarjeta `rgba(26,38,65,.97)`
  centrada, `position:fixed;bottom:80px;left:50%`), con borde rojo en
  vez de dorado y título/icono configurables. Admite una segunda línea
  de detalle (`sb-toast-roles` reutilizada), útil para listas de
  campos que faltan.
- Nueva función JS `showFormAlert(mensaje, opts)` —
  `opts = { title, detail, duracion }` — que rellena y muestra el
  nuevo componente (auto-oculta a los 6 s por defecto, configurable
  por llamada).
- `savePedido()`: los 10 `toast(msg,'error',...)` de validación y
  error de la función (modo hotel: cancelar no permitido y error de
  guardado; falta hotel; nota obligatoria; proveedor sin asignar;
  proveedor sin email; Nº Pedido/PDF faltante — con el detalle en la
  segunda línea; familia/importe del techo; error de negocio del
  backend al crear/actualizar; error de conexión en el `catch`) pasan
  a `showFormAlert(...)`. Los mensajes de éxito (`'success'`) y el
  aviso de techo superado (`'warning'`) se mantienen como el toast
  pequeño de siempre, sin cambios — el patrón nuevo es solo para
  errores/validación en ese modal.
- Verificado: los 8 bloques `<script>` de `templates/index.html`
  pasan `node --check` sin errores de sintaxis tras los cambios.

**Archivos entregados en esta corrección:** `templates/index.html`,
`CHANGELOG.md`, `docs/HISTORIAL_CAMBIOS.md`, `README.md` (solo el
número de versión). `app.py` no se ha tocado en esta entrega — ambos
cambios eran exclusivamente de frontend.

# v12.29.49 — 4 agosto 2026

🐛 Fix: comprador no podía crear ni editar proveedores (botón Guardar
no hacía nada)

**Nota de versión:** esta corrección se hizo primero contra un
snapshot del proyecto (subido como `control_pedidos_v12_29_47.zip`) y
se numeró en su momento como v12.29.48. Al recibir después la versión
realmente desplegada (`control_pedidos_v12_29_48.zip`), esta ya traía
otro fix distinto — el de "familia repetida" de abajo — usando ese
mismo número v12.29.48. Para no pisar esa entrada, este fix de
proveedores se renumera aquí a **v12.29.49** y se aplica sobre la base
real desplegada (que ya incluye el fix de familia repetida).

**Síntoma reportado:** un usuario con rol `compras` (comprador) abría
la ficha de un proveedor, pulsaba "Guardar cambios" y no pasaba nada
visible — ni error, ni confirmación, ni cierre del modal.

**Causa:** `POST /api/proveedores` y `PUT /api/proveedores/<id>`
estaban protegidas con `@admin_required` (solo `rol == "admin"`). Un
comprador recibía un `403 Solo administradores`. Como la función
`saveProveedor()` del frontend no captura la excepción que lanza el
helper `api()` ante un error no controlado, el 403 quedaba silencioso
para el usuario (solo visible en la consola del navegador) — de ahí
la sensación de que el botón "no hacía nada".

**Cambios (`app.py`):**
- `create_proveedor()` y `update_proveedor()`: pasan de `@admin_required`
  a `@login_required` + comprobación explícita
  `session.get("rol") not in ("admin", "compras")` → 403. Mismo patrón
  ya usado en `get_pedidos_eliminados()`. Ahora admin y comprador
  pueden crear/editar proveedores; el rol `hotel` sigue sin poder
  (consulta únicamente, como ya lo era).
- Sin cambios en `delete_proveedor()` ni en la importación masiva por
  Excel (`importar_proveedores`): se mantienen restringidas a admin
  por ser acciones más sensibles/destructivas.

**Cambios (`templates/index.html`):**
- `_refreshProvAdminControls()`: el botón "+ Nuevo proveedor" de la
  vista Proveedores ahora también se muestra para `rol === 'compras'`
  (antes solo para admin, lo que era inconsistente con el acceso
  rápido "Nuevo proveedor" del dashboard, que sí lo permitía a
  comprador desde `renderAccesosRapidos()`). El botón de "Importar
  Excel" sigue solo para admin.
- Badge de versión del sidebar actualizado a "V 12.29.49".

**Archivos entregados en esta corrección:** `app.py`,
`templates/index.html`, `CHANGELOG.md`, `docs/HISTORIAL_CAMBIOS.md`,
`README.md` (solo el número de versión), aplicados sobre la base real
subida por el usuario (`control_pedidos_v12_29_48.zip`).

# v12.29.48 — 4 agosto 2026

🐛 Fix: aviso "familia repetida" saltaba con el primer pedido (sin
duplicado real)

**Síntoma reportado:** el comprador de INSIRE seguía recibiendo el aviso
🔴 "Familia/Partida REPETIDA" de forma constante después de v12.29.47,
pese a que en el hotel no existía ningún pedido duplicado de esa
familia — solo un único pedido.

**Causa raíz:** `_job_familia_repetida_inner()` (el job diario que
detecta y notifica familias repetidas) contaba **todos** los pedidos de
la familia sin excluir ninguno, y comparaba con
`HAVING COUNT(*) >= techo_max_pedidos_familia`. Como
`techo_max_pedidos_familia` vale **1** por defecto, la condición
ejecutada era en la práctica `COUNT(*) >= 1`: el primer y único pedido
de cualquier familia ya cumplía la condición y se marcaba como
"repetida", sin que existiera un segundo pedido.

Esto era inconsistente con `_check_techo()` (la función que sí bloquea
el paso a ENVIADO AL PROVEEDOR): esa función excluye el propio pedido
del recuento antes de comparar, así que solo bloquea cuando **ya
existía otro pedido antes** — comportamiento correcto. El job de aviso
diario no tenía esa exclusión y disparaba un día antes de tiempo, con
el primer pedido.

**Cambio:** en la consulta SQL del job (`app.py`, función
`_job_familia_repetida_inner`), `HAVING COUNT(*) >= %s` pasa a
`HAVING COUNT(*) > %s`. Ahora el job solo alerta cuando el número de
pedidos de la familia **supera** el máximo configurado (repetición
real), no cuando simplemente lo alcanza con el primer pedido.

No se ha tocado `_check_techo()` (Regla de bloqueo al enviar al
proveedor): esa función ya era correcta, porque excluye el pedido en
curso del recuento antes de comparar.

# v12.29.47 — 4 agosto 2026 (PRUEBA)

🧪 Prueba: popup de main_agenda se entrega una única vez (dedup en servidor)

**Síntoma reportado:** el comprador de INSIRE recibía el mismo popup de
aviso "continuamente" a lo largo del día en Organizador Princess.

**Causa probable:** `/api/bridge/alertas` devolvía siempre TODAS las
alertas activas del usuario, y era `pedidos_agenda_bridge.py` (en el
propio Organizador Princess) quien decidía si tocaba repetir el popup,
con un intervalo en horas guardado **en memoria** (`_estado_popups`).
Si la app se reiniciaba, ese historial se perdía y los avisos volvían
a saltar de golpe; si el comprador tenía varios pedidos urgentes
acumulados, cada uno repetía cada hora por separado, dando sensación
de repetición constante.

**Cambio (a petición de VAMA, como prueba):** el dedup se mueve al
servidor.
- Nueva tabla `bridge_popup_visto (usuario, pedido_id, nivel)` —
  registra qué popups ya se le entregaron a cada usuario, de forma
  permanente (no se resetea al reiniciar Organizador Princess).
- Nueva función `_filtrar_popups_no_vistos()`: filtra las alertas
  activas contra esta tabla y marca como vistas las que se devuelven,
  en la misma llamada. Si el pedido escala de nivel (aviso→urgente) se
  trata como aviso nuevo. Si el pedido deja de ser alertable
  (resuelto/cambio de estado), se purga su fila — si vuelve a alertar
  más adelante, se trata como nuevo.
- `/api/bridge/alertas` ahora devuelve en `"alertas"` **solo** lo
  pendiente de entregar (para disparar el popup), y por separado
  `total_activas` / `urgentes_activas` / `normales_activas` con el
  recuento completo sin filtrar, para que el resumen del saludo diario
  de Organizador Princess siga mostrando el total real de alertas
  activas y no solo las nuevas de ese ciclo.
- **Comportamiento resultante:** si Organizador Princess está cerrada
  en el momento en que un pedido entra en alerta, el popup se le
  entregará en cuanto vuelva a conectar — pero solo esa vez; no se
  repite nunca más para ese pedido+nivel, ni con reintentos horarios
  ni al reiniciar la app.
- Contrapartida de esta prueba: se elimina el reintento periódico por
  nivel (`popup_horas_critico`/`popup_horas_normal`, configurable
  desde Admin → Config Alertas). Si el comprador cierra el popup sin
  actuar sobre el pedido, ya no volverá a recordárselo — a validar si
  esto es aceptable o si conviene reintroducir algún recordatorio,
  ahora también con dedup persistente.

**Cambios (`pedidos_agenda_bridge.py` v4.8, Organizador Princess):**
`_sincronizar_alertas()` simplificada — ya no decide repetición, solo
muestra lo que el servidor le manda. `_estado_popups` y las funciones
de repetición quedan sin usar (no se borran, por si hay que revertir
la prueba).

# v12.29.46 — 4 agosto 2026

🐛 Fix: pedidos en PENDIENTE FIRMA DIRECCION COMPRAS / PENDIENTE DE
FIRMA DIRECCION HOTEL nunca generaban alerta

**Síntoma:** un pedido llevaba semanas en "PENDIENTE DE FIRMA
DIRECCION HOTEL" (o "...COMPRAS") y aparecía correctamente en el
listado de Pedidos con ese filtro, pero nunca salía en el panel de
Alertas ni generaba avisos por Telegram, por muchos días que pasaran.

**Causa:** estos dos estados son justo los que `ESTADOS_SIN_TRAMITAR`
marca como "sin fecha_tramitacion todavía" — ese campo se rellena más
adelante en el flujo, así que para pedidos en estos estados
`fecha_tramitacion` está siempre vacío (se ve como "—" en la columna
F. TRAMIT. del listado). La configuración de umbrales
(`_build_umbrales()`) no tenía `fecha_ref` explícito para ninguno de
los dos, así que `_clasificar_alertas()` (panel de Alertas) y el job
de reclamaciones por Telegram caían en el valor por defecto
`"fecha_tramitacion"` — que al estar siempre vacío para estos estados
hacía que el cálculo de días diera `None` y la alerta se descartara
siempre, sin importar cuánto tiempo llevara esperando firma.

**Cambios (`app.py`):**
- `_build_umbrales()`: añadido `"fecha_ref": "fecha_solicitud"` a
  `PENDIENTE FIRMA DIRECCION COMPRAS` y `PENDIENTE DE FIRMA DIRECCION
  HOTEL`, igual que ya tenía `PENDIENTE COTIZACIÓN`. Ahora los días de
  espera se cuentan desde que se solicitó el pedido, que es la fecha
  que sí existe siempre en estos estados.
- Mismo cambio en el dict `UMBRALES_ALERTAS` (legacy, solo
  documentación/valores por defecto) para que no quede inconsistente.
- Afecta tanto al panel de Alertas del dashboard como al job
  automático de avisos por Telegram, que comparten `_build_umbrales()`.

# v12.29.45 — 4 agosto 2026

🐛 Fix: "Fecha de entrega específica" (proveedor) no se quedaba grabada visualmente

**Síntoma:** al rellenar "Fecha de entrega específica" en el pedido y
guardar, la fecha SÍ se guardaba en BD, pero al reabrir el pedido el
campo aparecía vacío — daba la impresión de que no se había grabado.

**Causa:** `fecha_entrega_especifica` es la única fecha de `pedidos`
guardada como columna `DATE` real (el resto — `fecha_solicitud`,
`fecha_envio_visto_bueno`, `fecha_tramitacion`... — son `TEXT` con
formato `YYYY-MM-DD`). Al devolverla en JSON, el serializador por
defecto de Flask convierte cualquier `date`/`datetime` a formato
RFC 1123 (`"Wed, 10 Aug 2026 00:00:00 GMT"`) en vez de ISO. El
`<input type="date">` del frontend no acepta ese formato y lo descarta
silenciosamente, dejando el campo vacío al reabrir el modal — aunque
el guardado en BD siempre fue correcto.

**Cambios (`app.py`):**
- Nueva función `_normalizar_fecha_entrega_especifica(p)`: convierte
  el valor a texto ISO (`YYYY-MM-DD`) si llega como `date`/`datetime`.
- Aplicada en los tres puntos donde un pedido con esta columna se
  devuelve al frontend: `GET /api/pedidos` (listado), `GET
  /api/pedidos/<id>` (detalle) y `_clasificar_alertas()` (usada por
  los endpoints de stats/alertas del dashboard).
- No se ha tocado el guardado (`POST`/`PUT`), que ya funcionaba bien;
  el problema era solo de lectura/visualización.

# v12.29.44 — 4 agosto 2026

📦 Simplificación del registro de entrada DALI/SAP: ENTREGADO + CANCELADO

**Petición:** simplificar el paso de "Nº Entrada DALI / SAP" — en vez de
tres checkboxes (ENTREGA PARCIAL, ENTREGA TOTAL, CANCELADO), mostrar
solo dos (ENTREGADO, CANCELADO). Dentro de "entrega" se mantiene el
mecanismo actual: si es una entrega total se marca la entrada como
final y el estado pasa directamente a ENTREGADO; si es parcial se
pueden ir añadiendo tantas entradas como sean necesarias, y la última
se marca como final para cerrar la entrega (estado ENTREGADO) —
mientras tanto el estado real sigue siendo ENTREGA PARCIAL.

**Cambios (solo frontend, `templates/index.html`):**
- Los checkboxes "ENTREGA PARCIAL" y "ENTREGA TOTAL" se fusionan en un
  único checkbox **ENTREGADO** (`chk-entregado`), que abre la misma
  lista editable de entradas de antes (número + fecha + botón "＋
  Añadir entrada DALI / SAP").
- Eliminado el mini-modal que pedía un único Nº Entrada DALI/SAP al
  marcar "ENTREGA TOTAL" directamente (`modal-albaran-total` y sus
  funciones `abrirModalAlbaranTotal()` / `cerrarModalAlbaranTotal()`) —
  ya no hace falta: para una entrega total ahora basta con añadir una
  entrada y marcarla como "Entrada final" en el mismo formulario.
- El checkbox "Entrada final" de cada fila (ya existente) sigue siendo
  el mecanismo que decide el estado real: marcado → `ENTREGADO`; sin
  marcar → `ENTREGA PARCIAL`. Solo puede haber una entrada final a la
  vez, igual que antes.
- `initAlbaranSection()`, `onAlbaranCheckChange()` y
  `_onAlbaranFinalChange()` actualizados para el checkbox único; sin
  cambios de comportamiento en la lista de entradas en sí.
- Los estados internos (`ENTREGA PARCIAL`, `ENTREGADO`, `CANCELADO`) no
  cambian — sigue siendo exactamente lo que guarda/valida el backend
  (`ESTADOS_VALIDOS` en `models.py`); esto es puramente una
  simplificación de la interfaz de captura.

**Archivos modificados:**
- `templates/index.html`
- `README.md` (versión)

Badge de versión del sidebar actualizado a "V 12.29.44".

# v12.29.43 — 3 agosto 2026

✨ Nueva funcionalidad — alarma y listado adjunto cuando un pedido está sujeto a techo de gastos

**Solicitado:** cuando se activa "sujeto al techo de gasto mensual" en un
pedido, debe saltar alguna alarma que indique que la autorización (firma)
está sujeta a techo de gastos, y debe poder adjuntarse algún listado de
apoyo a la solicitud de firma.

**Añadido:**
- **Frontend** — al marcar "Este pedido computa para el techo de gasto
  mensual" en la ficha del pedido, aparece un aviso destacado (📉) junto
  a un botón para adjuntar uno o varios documentos de apoyo ("Adjuntar
  listado a la solicitud de firma"), nuevo tipo de adjunto
  `firma_techo_doc` (PDF, Word, Excel o correo .eml/.msg — mismas
  validaciones de tamaño/formato que "Nº Presupuesto"). No visible para
  el rol Hotel (oculto por la restricción de formulario ya existente).
- **Backend** — `_email_template_pendiente_firma()` (el recordatorio
  automático/manual de "pedido pendiente de firma") ahora incluye un
  aviso destacado si el pedido está `sujeto_techo`, con familia e
  importe, y menciona si hay documentos de apoyo adjuntos para que quien
  gestione la firma los consulte antes de decidir.
- `firma_techo_doc` registrado en `TIPOS_ADJUNTO_VALIDOS` y añadido a la
  validación compartida con `presupuesto_doc`/`solicitud_doc`.
- `_JOB_PEDIDO_SQL` y `PEDIDO_SELECT_ALERTA` (las dos consultas que
  alimentan los avisos de firma pendiente, automático y manual) amplían
  sus columnas con `sujeto_techo`, `familia_id`, `importe` y
  `familia_nombre` (nuevo `LEFT JOIN familias`).

**Archivos modificados:**
- `app.py`
- `templates/index.html`

`app.py` compila sin errores. Badge de versión del sidebar actualizado
a "V 12.29.43".

# v12.29.42 — 3 agosto 2026

🔧 Corrección: hotel de pruebas ("PR") también visible para el usuario dedicado

**Corrección sobre v12.29.41:** la restricción anterior dejaba el hotel
`PR` visible solo para el rol admin. El planteamiento correcto es que
también debe verlo/usarlo el usuario dedicado a estas pruebas
(username `usuario prueba`), **sea cual sea su rol real** (en la
captura aparece como rol Compras) — admin sigue viéndolo igual que
hasta ahora.

**Cambios:**
- Nueva constante `USERNAME_HOTEL_PRUEBAS = "usuario prueba"` y helper
  `_puede_ver_hotel_pruebas()` (`app.py`), que sustituye a las
  comprobaciones puntuales de `rol == "admin"` introducidas en v12.29.41
  en todos los puntos donde se filtraba el hotel `PR`: `/api/maestros`,
  `/api/pedidos` (listado, detalle, crear, editar), `/api/stats`,
  `/api/dashboard/resumen`, `/api/techo/resumen` (actual e histórico),
  `/api/exportar` (Excel) y `POST /api/importar`.
- Los jobs automáticos (familias repetidas, techo urgente, techo
  mensual) vuelven a recorrer TODOS los hoteles activos, incluido `PR`:
  sus destinatarios se resuelven por hotel vía `_resolver_notificacion()`
  (configuración de avisos por hotel/evento), así que solo llegan a
  quien esté configurado como destinatario de ese hotel en concreto —
  no hay filtrado adicional que hacer ahí, y excluirlo habría impedido
  probar el pipeline de alertas con este hotel.
- Si el username del usuario de pruebas cambiara, basta con actualizar
  `USERNAME_HOTEL_PRUEBAS` en `app.py` (línea única).

**Archivos modificados:**
- `app.py`
- `templates/index.html` (badge de versión)
- `README.md` (versión)

`app.py` compila sin errores. Badge de versión del sidebar actualizado
a "V 12.29.42".

# v12.29.41 — 3 agosto 2026

🔒 Hotel de pruebas ("PR") restringido solo al rol admin

**Petición:** el hotel de pruebas (código `PR`, creado en v12.29.32 para
pruebas internas) solo debe estar disponible para el rol admin — el
resto de usuarios (compras, hotel) no deben poder verlo ni interactuar
con sus pedidos en ningún sitio de la aplicación.

**Cambios:**
- `/api/maestros` (dropdown de hoteles usado en toda la app para crear/
  filtrar pedidos): excluye `PR` para compras; el rol hotel ya estaba
  limitado a sus hoteles asignados, se añade la exclusión también ahí
  por seguridad.
- `/api/pedidos` (listado) y `/api/pedidos/<id>` (detalle): excluyen/
  bloquean el hotel `PR` para cualquier rol que no sea admin.
- `POST /api/pedidos` y `PUT /api/pedidos/<id>`: rechazan crear o
  reasignar un pedido al hotel `PR` si el usuario no es admin.
- `/api/stats`, `/api/dashboard/resumen`, `/api/techo/resumen` y
  `/api/techo/resumen-historico`: excluyen el hotel `PR` de conteos,
  gráficos, alertas y rankings para compras.
- `/api/exportar` (Excel) y `POST /api/importar` (importación masiva):
  excluyen el hotel `PR` para compras/hotel.
- Jobs automáticos de alertas (familias repetidas, techo urgente, techo
  mensual): excluyen el hotel `PR` del recorrido de hoteles activos,
  para que no genere notificaciones reales a compradores/hoteles.
- Paneles exclusivamente admin (gestión de compradores por hotel,
  configuración de avisos, importación/reset, integridad operativa) se
  mantienen sin cambios — siguen mostrando `PR`, como corresponde a su
  uso interno de admin.
- Nueva constante `HOTEL_CODIGO_PRUEBAS = "PR"` y helper
  `_es_hotel_pruebas_id()` en `app.py` para centralizar la comprobación.

**Archivos modificados:**
- `app.py`
- `templates/index.html` (badge de versión)
- `README.md` (versión)

`app.py` compila sin errores. Badge de versión del sidebar actualizado
a "V 12.29.41".

# v12.29.40 — 3 agosto 2026

📧 Logo nítido en cabeceras de email + motivo real en avisos de CANCELADO / DENEGADO

**Petición:** el logo de la cabecera se veía distorsionado/borroso en los
correos de aviso interno. Además, en los correos de cancelación (y
denegación por Dirección General) no se estaba indicando el motivo ni
quién realizó el cambio, solo el campo "Observaciones" del pedido (casi
siempre vacío).

**Corregido — logo borroso:**
- Causa: los correos usaban `logo-sidebar.png` (787×731 px original) escalado
  vía CSS a 56/64/40 px — muchos clientes de correo (sobre todo Outlook, motor
  Word) hacen un downscale de mala calidad de imágenes grandes.
- Generados `static/logo-sidebar-email.png` (121×112, retina 2x para 56/40 px)
  y `static/logo-sidebar-email-64.png` (138×128, retina 2x para 64 px) con
  remuestreo Lanczos.
- `_email_header_html()` y los 6 bloques de cabecera sueltos (correos de
  solicitud de acceso) actualizados para usar estos assets con `width`/`height`
  explícitos en el `<img>`.

**Corregido — motivo y trazabilidad en CANCELADO / DENEGADO:**
- El motivo real de la cancelación/denegación se guarda en
  `historial_estados.nota` en el momento de la transición, no en
  `pedido.observaciones` (campo aparte, normalmente vacío) — por eso el
  correo se quedaba sin motivo.
- `enviar_emails_estado()` ahora consulta `historial_estados` por
  `pedido_id` + `estado_nuevo` y muestra "Motivo de la cancelación" /
  "Motivo de la denegación" en el correo (HTML y texto plano), con
  fallback a `observaciones` si no hubiera nota.
- `DENEGADO POR DIRECCION GENERAL` añadido a `ESTADOS_EMAIL_INTERNO`
  (`models.py`) — antes no se enviaba ningún correo interno para ese
  estado.
- La fila "Realizado por" (ya existente) sigue cubriendo quién hizo el
  cambio.

**Archivos modificados:**
- `app.py`
- `models.py`
- `templates/index.html` (badge de versión)
- `static/logo-sidebar-email.png` (nuevo)
- `static/logo-sidebar-email-64.png` (nuevo)

`app.py` y `models.py` compilan sin errores. Badge de versión del sidebar
actualizado a "V 12.29.40".

# v12.29.39 — 2 agosto 2026

🗓️ Auditoría de fin de semana en jobs automáticos — techo mensual se había quedado fuera

**Petición:** revisar todos los puntos donde se envía Telegram/popup para
que cumplan el mismo criterio de fin de semana aplicado en v12.29.38 (no
avisar en sábado/domingo, retomar el lunes).

**Encontrado:** `_job_alertas_techo_mensual_inner()` — el tercer job
automático del rediseño de Techo de Gastos (junto a techo urgente y
familia repetida, ambos ya con este guardián) — corría los 7 días de la
semana. Inconsistente con sus dos jobs hermanos.

**Corregido:**
- Guardián de fin de semana al inicio de `_job_alertas_techo_mensual_inner()`,
  igual que en `_job_alertas_diarias_inner()` y en
  `_techo_urgente_es_horario_valido()`.
- `day_of_week="mon-fri"` añadido al `scheduler.add_job` de
  `alertas_techo_mensual`.

**Revisados y dejados tal cual, a propósito (event-driven, no jobs
automáticos):**
- `_telegram_cambio_estado` — cambio manual de estado de un pedido
- `_telegram_alerta_techo` — al crear un pedido nuevo sujeto a techo
- `_notify_solicitud_telegram` / `_enviar_supervision_admins` —
  solicitudes de acceso y copias de supervisión
- Los 2 botones manuales "Enviar Telegram" del panel de alertas

Estos son reacción inmediata a una acción real de una persona — deben
salir el mismo día, sea fin de semana o no.

**Revisados y dejados sin tocar, a petición expresa:** `_job_alerta_consumo_inner`
(cuota Supabase/egress) y `_job_health_check_inner` (integridad BD) — son
alertas de infraestructura, no de negocio de pedidos; siguen avisando
los 7 días de la semana.

`app.py` compila sin errores. Badge de versión del sidebar actualizado
a "V 12.29.39".

# v12.29.38 — 2 agosto 2026

🗓️ Correo de reclamación, Telegram y popup de main_agenda ya no salen en fin de semana

**Petición:** el envío automático de la reclamación al proveedor, el aviso
de firma pendiente, el Telegram a compradores y el popup de main_agenda
(Organizador Princess) se disparaban también en sábado y domingo — se
pidió retrasarlos al lunes sin tocar el conteo de días naturales ni el
ciclo de reenvío.

**Corregido:**
- `_job_alertas_diarias_inner()` — nuevo guardián al inicio: si
  `ahora.weekday() >= 5` (sábado/domingo), el job no envía nada y
  termina. Este es el único punto donde salen los cuatro avisos
  (reclamación al proveedor, aviso de firma pendiente, Telegram y popup
  vía `_enviar_telegram_compradores` → `_encolar_bridge_notificacion`),
  así que un solo guardián cubre los tres canales.
- Scheduler (`scheduler.add_job` de `alertas_cada_minuto`) — añadido
  `day_of_week="mon-fri"`, igual que ya tenían los jobs de techo urgente
  y familia repetida, para no ejecutar el job en balde en fin de semana.
- **Nada más cambia:** `_dias_desde_fecha()` sigue en días naturales sin
  tocar (sábado y domingo suman igual al contador), y el ciclo de
  reenvío (`_dias_ultima_notificacion` / `_ya_notificado_hoy`) sigue
  basándose en la fecha real del último aviso en `whatsapp_log` — al no
  guardarse ningún aviso en fin de semana, el recuento continúa con
  normalidad desde el último aviso real (viernes) hasta el lunes, sin
  necesidad de ningún caso especial.
- No requiere cambios en main_agenda: al no encolarse nada en
  `bridge_notificaciones` durante el fin de semana, el bridge
  simplemente no tiene nada que recoger ese día.

`app.py` compila sin errores. Badge de versión del sidebar actualizado
a "V 12.29.38".

# v12.29.37 — 2 agosto 2026

🔒 Seguridad — las contraseñas se guardaban en texto plano en la base de datos

**Hallazgo:** revisando `app.py` como referencia para el login de otro
proyecto (DALI) se detectó que el login (`/api/login`, y el equivalente
usado por el bridge de Organizador Princess) comparaba la contraseña
recibida directamente contra la columna `password` de `usuarios` con un
simple `=` en el SQL, sin ningún tipo de hash. Lo mismo ocurría al
guardar una contraseña nueva: reset por token, alta automática de
usuario tras solicitud aprobada, y alta/edición de usuario desde el
panel de administración. Cualquiera con acceso de lectura a la base de
datos (fuga, backup, herramienta de administración mal configurada, log
de queries) veía las contraseñas de todos los usuarios tal cual las
escribieron.

**Corregido:**
- Las contraseñas ahora se guardan siempre con `generate_password_hash`
  (werkzeug, ya incluido con Flask — sin dependencia nueva) en los 4
  puntos donde se escriben: reset por token, alta automática de
  solicitud, alta de usuario y edición de usuario desde Admin.
- El login (los dos endpoints: `/api/login` y el del bridge) compara
  ahora con `check_password_hash` a través de una función común,
  `_verifica_y_migra_password()`.
- **Migración transparente, sin forzar reset a nadie:** esa función
  detecta si la contraseña guardada todavía está en texto plano (cuentas
  creadas antes de esta versión) y, si la comparación legacy coincide,
  la rehashea y sobreescribe en la BD en ese mismo login. Cada usuario
  queda migrado la próxima vez que entra, sin darse cuenta y sin ninguna
  ventana en la que se quede sin poder acceder.
- El email de bienvenida con contraseña temporal (alta automática de
  solicitudes) sigue enviando la contraseña en claro al usuario nuevo,
  como hasta ahora — solo cambia lo que se guarda en la BD, que pasa a
  ser el hash.

`app.py` compila sin errores. Badge de versión del sidebar actualizado
a "V 12.29.37".

# v12.29.36 — 2 agosto 2026

🔧 Corrección real — el login mostraba "Error de conexión" también con contraseña incorrecta

**Confirmado primero:** la migración de `expediente_exceso` de la
v12.29.35 se ejecutó correctamente en el arranque siguiente (logs:
`[MIGRACION] Tabla expediente_exceso — CREATE TABLE ejecutado` +
`índices OK`) — el bug de "Techo de Gastos" queda resuelto.

**Reportado a continuación:** el login seguía dando "Error de conexión"
tras ese despliegue. Revisando los logs de Render en el momento exacto
del intento de login, el servidor respondía con total normalidad
(`POST /api/login` → 401, no un fallo de red ni un timeout) — el 401 es
la respuesta correcta del backend cuando la contraseña no coincide, y
ya trae el mensaje adecuado (`{"error": "Usuario o contraseña
incorrectos"}`).

**Causa real:** el `catch` de `doLogin()` en el frontend ignoraba por
completo ese mensaje y mostraba siempre el texto genérico "Error de
conexión", sin importar el motivo real del fallo — así que una simple
contraseña incorrecta parecía un problema de conectividad del servidor.

**Corregido:** el `catch` ahora recupera el detalle real que devuelve
`api()` (`Usuario o contraseña incorrectos`, o cualquier otro mensaje
de error del servidor) y solo cae al genérico "Error de conexión"
cuando de verdad no hay respuesta del servidor (fallo de red puro, sin
código de estado HTTP).

`app.py` sin cambios en esta versión. Badge de versión del sidebar
actualizado a "V 12.29.36".

# v12.29.35 — 2 agosto 2026

🔍 Diagnóstico — la migración de expediente_exceso sigue sin aplicarse; añadido logging detallado

**Reportado:** tras desplegar la v12.29.33/34, `/api/techo/resumen` seguía
dando `psycopg2.errors.UndefinedTable: relation "expediente_exceso" does
not exist`. Revisando los logs de Render se confirmó que
`_auto_migrate()` está lanzando `Auto-migración omitida: 0` justo
después de insertar el hotel "PR" — es decir, justo donde se añadió el
bloque de `expediente_exceso` en la v12.29.33. El mensaje `"0"` no da
ninguna pista real: `_auto_migrate()` solo registraba `str(e)` de la
excepción, sin traceback, así que era imposible saber en qué línea
exacta fallaba ni por qué.

**Cambio (solo diagnóstico, no arregla nada todavía):**
- El `except` general de `_auto_migrate()` ahora vuelca el traceback
  completo con `log.exception(...)` además del mensaje corto.
- El bloque de creación de `expediente_exceso` se ha envuelto en su
  propio `try/except`, que registra el tipo de excepción y su `repr()`
  completo (`[MIGRACION] FALLO creando expediente_exceso — tipo=...
  repr=...`) antes de relanzarla — así se sabrá con certeza si el fallo
  está en el `CREATE TABLE`, en algún `CREATE INDEX`, o en otro punto.

Con esto desplegado, el próximo arranque del servidor dejará en los
logs de Render la causa real y exacta del fallo, que se corregirá en la
siguiente versión.

`app.py` compila sin errores. Badge de versión del sidebar actualizado a
"V 12.29.35".

# v12.29.34 — 2 agosto 2026

📄 Documentación — README general de la aplicación

Se añade `README.md` en la raíz del proyecto con documentación general:
stack técnico, estructura del repositorio, funcionalidades por vista,
roles de usuario, cómo funcionan las migraciones automáticas de base de
datos (`_auto_migrate()` vs `init_db.py`/`models.py` — el punto que ha
causado los dos bugs reales de v12.29.32 y v12.29.33), puesta en marcha
local y en producción, variables de entorno, y convenciones del
proyecto (versión + changelog + historial en cada cambio).

No afecta a `app.py` ni a la lógica de la aplicación — cambio puramente
documental. Badge de versión del sidebar actualizado a "V 12.29.34".

# v12.29.33 — 2 agosto 2026

🔧 Corrección real — "Techo de Gastos" se quedaba colgado en "Cargando…" para siempre

**Reportado:** la vista "Techo de gastos" se queda cargando y no llega a
mostrar ningún dato, ni un error.

**Causa encontrada tras revisar el código:** exactamente el mismo patrón
de bug que el hotel de pruebas "PR" de la v12.29.32. La tabla
`expediente_exceso` (rediseño de Techo de Gastos, Fase 1) solo estaba
definida en `SQL_STATEMENTS` (`models.py`) — y esa lista **solo la
ejecuta `init_db.py`**, un script manual pensado para "el primer
despliegue" sobre una base de datos nueva y vacía. Como esta base de
datos ya existe y nadie vuelve a correr `init_db.py` sobre producción,
la tabla nunca llegó a crearse, pese a que el código que la usa
(`/api/techo/resumen`) sí estaba desplegado correctamente.

Al no existir la tabla, `/api/techo/resumen` fallaba con un error 500
("relation expediente_exceso does not exist"). En el frontend,
`_fetchTecho()` capturaba ese error y devolvía `null` en vez de
relanzarlo — pero `loadTecho()` no comprobaba ese caso y hacía `d.mes`
directamente sobre `null`, lo que lanzaba una excepción sin capturar
justo después de pintar "Cargando…". Resultado: la vista se quedaba
colgada en "Cargando…" para siempre, sin ningún mensaje de error visible
para el usuario.

**Corregido:**
- `app.py`: se repite la creación de `expediente_exceso` (y sus 3
  índices) dentro de `_auto_migrate()`, la función que sí corre en cada
  arranque del servidor — con `CREATE TABLE/INDEX IF NOT EXISTS`, sin
  ningún riesgo de duplicado si `init_db.py` ya se llegó a ejecutar en
  algún momento. Se ejecutará solo, en el próximo arranque, sin tocar
  nada más.
- `templates/index.html`: `loadTecho()` ahora comprueba si `_fetchTecho()`
  devolvió `null` y muestra un aviso de error visible ("⚠️ No se ha
  podido cargar el techo de gastos...") en vez de quedarse colgada en
  "Cargando…" sin explicación — para que, si algo similar vuelve a pasar
  en el futuro, se note enseguida en vez de parecer que la app está
  rota.

`app.py` compila sin errores. Badge de versión del sidebar actualizado a
"V 12.29.33".

# v12.29.32 — 1 agosto 2026

🔧 Corrección real — el hotel de pruebas "PR" nunca llegaba a insertarse en despliegues existentes

**Causa encontrada tras revisar logs y código, no un problema del despliegue del
usuario**: el `INSERT` del hotel `PR` (v12.29.28) se añadió a `SQL_STATEMENTS`
(`models.py`) — pero esa lista **solo la ejecuta `init_db.py`**, un script
manual pensado para "el primer despliegue" sobre una base de datos nueva
y vacía (así lo dice su propio docstring). La función que sí corre
automáticamente en cada arranque del servidor es otra completamente
distinta, `_auto_migrate()` — ahí es donde vivían correctamente las 8
fases del rediseño de Techo (por eso esas sí funcionaron), pero el hotel
se quedó en el sitio equivocado. Como nadie vuelve a ejecutar
`init_db.py` a mano sobre una base de datos de producción ya existente,
el hotel nunca llegaba a crearse pese a que el código desplegado era
correcto.

**Corregido**: el mismo `INSERT ... ON CONFLICT DO NOTHING` se repite
ahora también dentro de `_auto_migrate()`, justo después del backfill de
la Fase 7 — se ejecutará solo, en el próximo arranque del servidor, sin
tocar nada más. Se deja también en `models.py`/`SQL_STATEMENTS` para que
las instalaciones nuevas de verdad (`init_db.py` en un despliegue desde
cero) lo sigan teniendo — el `ON CONFLICT DO NOTHING` en ambos sitios
hace que no haya ningún riesgo de duplicado.

Nuevo log `[MIGRACION] Hotel de pruebas 'PR' insertado` para poder
confirmarlo en el arranque.

`app.py` compila sin errores. Badge de versión del sidebar actualizado a
"V 12.29.32".

# v12.29.30 — 1 agosto 2026

🔧 Corrección — 4 modales sin scroll interno (no dejaban llegar a los campos de abajo)

**Reportado:** no se podía llegar a la sección de hoteles asignados en el
modal "Editar usuario" para marcar el hotel de pruebas.

**Causa real:** la clase `modal-box`, usada por 4 modales (Editar/Nuevo
usuario, Familia, Preferencias de dashboard, Confirmar eliminar), **no
tenía ningún estilo CSS propio** — le faltaba el `max-height:90vh;
overflow-y:auto` que sí tiene la clase `modal` (la que usa correctamente
el resto de modales de la app). Sin esa regla, cuando el contenido no
cabía en la pantalla, el modal simplemente se salía del viewport sin
ninguna forma de hacer scroll para llegar a lo de más abajo (el bloque de
hoteles, o incluso el propio botón "Guardar" en pantallas pequeñas).

**Corregido**: las 4 `<div class="modal-box">` pasan a `<div
class="modal">`, igual que el resto — ahora sí hacen scroll interno con
cabecera y pie fijos (`sticky`), como estaba pensado desde el principio.

**Nota aparte, no relacionada con el bug**: el bloque "🛒 Hoteles
asignados (Compras)" solo aparece cuando el **Rol** del usuario está en
"Compras" — si el usuario en el que estabas es Administrador, ese bloque
no se muestra en absoluto (los admins tienen acceso a todos los hoteles
por defecto, no hace falta asignárselos uno a uno).

`app.py` sin cambios. Badge de versión del sidebar actualizado a
"V 12.29.30".

# v12.29.28 — 1 agosto 2026

🏨 Nuevo hotel "PR — Hotel Pruebas", para poder probar el rediseño de Techo de Gastos sin tocar datos reales

Los hoteles están hardcodeados (`models.py`, sin ningún endpoint `/api/hoteles` para crearlos desde el panel) — se añade uno nuevo por el mismo mecanismo ya existente: una fila más en el `INSERT ... ON CONFLICT DO NOTHING` que ya corre en cada arranque, así que no hace falta ninguna migración aparte y no toca los 10 hoteles reales.

- Código `PR`, nombre `⚠️ HOTEL PRUEBAS — no usar en operativa real` (deliberadamente imposible de confundir con uno real en cualquier desplegable o listado).
- Pensado para ejecutar el checklist manual del rediseño de Techo de Gastos (`tests/CHECKLIST_PRUEBAS_MANUALES_TECHO.md`) sin arriesgar datos de producción — crea un comprador de pruebas y asígnalo a este hotel.
- Recuerda: los límites de techo (`techo_max_pedido`, `techo_max_mes`, etc.) son una configuración global, no por hotel — no los toques para forzar el circuito, diseña los importes de prueba para que los superen a propósito.

`app.py`/`models.py` compilan sin errores. Badge de versión del sidebar actualizado a "V 12.29.28".

# v12.29.26 — 1 agosto 2026

🏗️ Rediseño de Techo de Gastos — Fase 8: pruebas (cierre del rediseño)

**Última fase del alcance** (la Fase 9, aprobación parcial, queda fuera
según el propio documento de diseño). Con esto se cierran las 9 fases del
rediseño completo, iniciado con el modelo de datos (v12.29.8) y terminado
aquí.

**Nuevo `tests/test_techo_gastos.py`** — 23 pruebas automáticas,
**ejecutadas de verdad contra el código actual** (no contra una copia):
extrae con `ast` el código fuente exacto de `_check_techo()`,
`_techo_snapshot()`, `_calcular_fecha_entrega_prevista()` y
`_resolver_fecha_entrega_prevista()` directamente de `app.py`, lo ejecuta
en un espacio aislado con mocks controlados de `query()`/`get_config()`
(sin necesidad de una base de datos real ni de Flask), y comprueba cada
regla con asserts — incluida una prueba de regresión específica para el
bug `_d`/`_dt` que se encontró y corrigió en la Fase 1 del rediseño.
**Resultado: 23/23 superadas.** Se ejecuta con
`python3 tests/test_techo_gastos.py`, sin dependencias del proyecto.

**Nuevo `tests/CHECKLIST_PRUEBAS_MANUALES_TECHO.md`** — 11 bloques de
pruebas manuales para todo lo que necesita servidor + base de datos
reales (circuito completo, expedientes, aprobar/denegar, cancelar con
liberación de techo, informe imprimible con snapshot congelado, alertas,
backfill, regresión) — pensado para ejecutarse contra un entorno real
antes de dar el rediseño por completamente probado en producción.

`app.py` compila sin errores (sin cambios de backend en esta fase, solo
los 2 archivos de test nuevos). Badge de versión del sidebar actualizado
a "V 12.29.26".

# v12.29.24 — 1 agosto 2026

🏗️ Rediseño de Techo de Gastos — Fase 7: migración/backfill

**⚠️ Esta versión modifica datos existentes en producción al desplegarse**
— léelo antes de subir.

Los pedidos que ya estaban en `ENVIADO AL PROVEEDOR`/`ENTREGA PARCIAL`/
`ENTREGADO` **antes** de que existiera la columna `mes_consumo_techo`
(Fase 1) se habrían quedado con ella vacía para siempre — y por tanto
invisibles para el cálculo del techo del mes en que de verdad se
enviaron, tanto en el resumen del mes actual como sobre todo en el
histórico por meses.

**Cambio:** nuevo `UPDATE` en el bloque de migraciones de arranque —
rellena `mes_consumo_techo` una sola vez para esos pedidos, con el mismo
criterio de fallback que usaba el endpoint histórico antes de
simplificarse en la Fase 4 (`COALESCE` entre el último registro de "pasó
a ENVIADO AL PROVEEDOR" en `historial_estados`, `fecha_tramitacion`, y
`creado_en` como último recurso). Es **idempotente**: el propio
`WHERE mes_consumo_techo IS NULL` hace que, en cualquier arranque
posterior (o en una base de datos ya migrada), no actualice ninguna fila.
Queda registrado en el log del servidor cuántos pedidos se vieron
afectados la primera vez que corre.

`app.py` compila sin errores. Badge de versión del sidebar actualizado a
"V 12.29.24".

# v12.29.22 — 1 agosto 2026

🏗️ Rediseño de Techo de Gastos — Fase 6 (parte 2 de 2, cierre): pantalla de Techo y acciones

Cierra la Fase 6 (frontend). Decisiones de alcance, comunicadas al
usuario: en vez de una página aparte de "panel de expedientes", las
acciones quedan como acciones rápidas en las propias tarjetas de la
pantalla de Techo (que ya es donde se ve todo lo demás); y la "tabla
cronológica" del punto 11 se considera ya cubierta por el informe
imprimible de la Fase 5, sin duplicar una vista en pantalla solo para eso.
`GET /api/expedientes` (histórico completo, Fase 4) sigue sin pantalla de
navegación propia — pendiente si se pide explícitamente.

**Cambios:**
- Pantalla de Techo (`loadTecho()`): semáforo con el nuevo caso 🔵 azul
  (color, icono, barra de progreso); nuevo bloque "🧮 Compromiso
  potencial" (solo visible si hay algo pendiente); nuevo bloque "🔵
  Pendientes de Vº Bº Dirección General" por tarjeta, con acciones
  directas ✅ Aprobar / ❌ Denegar / 🖨️ Imprimir por cada expediente; nuevo
  bloque "✅ Excesos autorizados este mes" (resumen + botón imprimir por
  fila).
- Nueva función `resolverExpedienteTecho(eid, accion)`: captura la nota
  (obligatoria al denegar, opcional al aprobar) con `prompt()` — elección
  pragmática para esta primera versión, contenida a una sola función si
  se prefiere un modal más adelante — y llama a
  `/api/expedientes/<id>/aprobar` o `/denegar` (Fase 2).

`app.py` compila sin errores. Badge de versión del sidebar actualizado a
"V 12.29.22".

# v12.29.20 — 1 agosto 2026

🏗️ Rediseño de Techo de Gastos — Fase 6 (parte 1 de 2): guardado y validaciones

Entrega parcial de la Fase 6 (frontend) por su tamaño — el panel de
expedientes y la pantalla de Techo actualizada llegan en la parte 2.

**Cambios:**
- Quitado el `confirm()` de JS obsoleto en el guardado de pedidos (nunca
  más lo dispara el backend desde la Fase 2) — sustituido por un toast
  informativo cuando el pedido queda pendiente de Vº Bº de Dirección
  General.
- `create_pedido()`/`update_pedido()` devuelven ahora `estado_final` y
  `requiere_autorizacion_dg` para que el frontend sepa si el estado
  guardado coincide con el solicitado.
- `onEstadoChange()` y la validación de guardado: nota obligatoria
  extendida a `DENEGADO POR DIRECCION GENERAL` (mismo mecanismo que ya
  existía para reactivar desde `CANCELADO`, punto 8 del rediseño).
- Marca visual "⚠️ SIN AUTORIZAR" en el listado de pedidos cuando
  `no_autorizado_previo = TRUE` (punto 5).
- De propina: los 2 estados nuevos no tenían color de badge propio (caían
  en el de "pendiente compras", confuso) — añadidos `--s-pendiente-dg` /
  `--s-denegado-dg` y sus clases `.badge-*`.

`app.py` compila sin errores. Badge de versión del sidebar actualizado a
"V 12.29.20".

# v12.29.18 — 1 agosto 2026

🏗️ Rediseño de Techo de Gastos — Fase 5: informe imprimible

**Cambios:**
- Nuevo endpoint `GET /api/expedientes/<id>/informe` — todo lo necesario
  para el informe en una sola llamada: el expediente con su fotografía
  presupuestaria **congelada** (nunca recalculada, punto 10 — para eso
  ya está `/api/techo/resumen` si se quiere la situación en vivo), datos
  del pedido, histórico cronológico de reintentos de ese mismo pedido, e
  histórico de excesos anteriores ya resueltos del mismo hotel+familia
  (contexto para Dirección General).
- Nueva función `imprimirExpediente(eid)` en el frontend — **reutiliza
  `_abrirVentanaImpresion()`**, el mismo mecanismo que ya usan
  `imprimirTecho()` e `imprimirAlertas()` desde v11.5.4/v11.5.8. No se ha
  creado ningún sistema de impresión nuevo.
- El informe incluye: datos generales, situación del techo (snapshot),
  motivo de la solicitud, resolución (o espacio para firma/observaciones
  manuscritas si sigue pendiente), cronología de reintentos, y excesos
  anteriores del hotel/familia.
- **Sin botón en la interfaz todavía** — la función queda lista para
  conectarse al panel de expedientes de la Fase 6, que es donde tiene
  sentido el botón "🖨️ Imprimir informe".

`app.py` compila sin errores. Badge de versión del sidebar actualizado a
"V 12.29.18".

# v12.29.16 — 1 agosto 2026

🏗️ Rediseño de Techo de Gastos — Fase 4: endpoints de consulta

**Cambios:**
- `/api/techo/resumen`: filtro cambiado a `mes_consumo_techo`. Nuevos
  bloques por hotel — `pendientes_dg` / `excesos_autorizados` (listas de
  expedientes, Sección 8), `compromiso_potencial` = consumido + pendiente
  DG (punto 9), y semáforo con nuevo caso **azul** cuando hay algún
  expediente pendiente (punto 12) — se superpone a rojo/amarillo/verde.
- `/api/techo/resumen-historico`: simplificado — antes calculaba la fecha
  de envío con un `COALESCE(historial_estados, fecha_tramitacion,
  creado_en)` + `DATE_TRUNC`, y exigía `estado='ENVIADO AL PROVEEDOR'`,
  lo que **excluía incorrectamente** cualquier pedido que ya hubiera
  avanzado a ENTREGA PARCIAL/ENTREGADO desde entonces (un pedido de hace
  3 meses ya entregado desaparecía de su mes histórico). Ahora usa
  `mes_consumo_techo` directamente — más simple y más correcto. Mismos
  bloques nuevos que el resumen del mes actual.
- Nuevo `GET /api/expedientes` (Sección 9 — histórico completo, nunca se
  borra): filtros opcionales `hotel_id`, `familia_id`, `resultado`, `mes`.
- Nuevo `GET /api/expedientes/pedido/<pedido_id>` (punto 11 — histórico
  cronológico dentro de un expediente concreto): todas las filas de ese
  pedido, ordenadas por fecha — gratis, porque cada reintento tras
  denegación ya es una fila independiente desde la Fase 1/2.

`app.py` compila sin errores. Badge de versión del sidebar actualizado a
"V 12.29.16".

# v12.29.14 — 1 agosto 2026

🏗️ Rediseño de Techo de Gastos — Fase 3 (cierre): job de familia repetida

Confirmado por el usuario: `_job_familia_repetida_inner()` (alerta de
"familia repetida", `techo_max_pedidos_familia`) también migrada de
`EXTRACT(YEAR/MONTH FROM p.creado_en)` a `mes_consumo_techo = %s`, igual
criterio que los otros 2 jobs de techo — ahora los 3 jobs de alertas de
techo son consistentes entre sí. Con esto se cierra del todo la Fase 3.

`app.py` compila sin errores. Badge de versión del sidebar actualizado a
"V 12.29.14".

# v12.29.12 — 1 agosto 2026

🏗️ Rediseño de Techo de Gastos — Fase 3: jobs de alertas

**Cambios:**
- `_job_techo_urgente_admins_inner()` y `_job_alertas_techo_mensual_inner()`:
  filtro cambiado de `EXTRACT(YEAR/MONTH FROM p.creado_en)` a
  `mes_consumo_techo = %s`, igual que `_check_techo()` — ahora ambos jobs
  cuentan pedidos por consumo real, no por fecha de creación.
- Nueva alerta específica por Telegram a admins cuando se detecta
  `no_autorizado_previo = TRUE` en algún pedido — visibilidad inmediata del
  caso anómalo, además de la constancia permanente ya guardada en
  `historial_estados`. Deduplicada por pedido (una sola vez).

**⚠️ Encontrado, sin tocar — pendiente de confirmación:** `_job_familia_repetida_inner()`
(alerta de "familia repetida", relacionada con `techo_max_pedidos_familia`)
sigue filtrando por `creado_en`, con la misma inconsistencia semántica que
los 2 jobs de arriba tenían antes de esta fase. No estaba nombrada
explícitamente en la Fase 3 del documento de diseño, así que no se ha
tocado — a la espera de confirmar si también debe migrarse a
`mes_consumo_techo` o si se deja aparte a propósito.

`app.py` compila sin errores. Badge de versión del sidebar actualizado a
"V 12.29.12".

# v12.29.10 — 1 agosto 2026

🏗️ Rediseño de Techo de Gastos — Fase 2: lógica de negocio central

**Decisión de arquitectura** (en vez del endpoint separado
`/solicitar-autorizacion` del documento original): el circuito de
Dirección General queda enganchado **dentro** de `update_pedido()`, en el
único punto por el que pasa cualquier vía que intente cambiar el estado a
`ENVIADO AL PROVEEDOR` — evita duplicar toda la validación de "proveedor
obligatorio / PDF obligatorio" en un endpoint aparte y cumple de forma
natural el chequeo de integridad. El frontend no necesita ningún botón
nuevo — el flujo normal de "cambiar estado" simplemente puede terminar en
`PENDIENTE Vº Bº DIRECCIÓN GENERAL` en vez de `ENVIADO AL PROVEEDOR`.

**Cambios:**
- `_check_techo()` reescrita: filtra por `mes_consumo_techo` en vez de
  `creado_en` (solo pedidos ya enviados cuentan); eliminada la antigua
  Regla 1 (límite agregado de nº pedidos por hotel — decisión de negocio:
  solo queda el límite por hotel+familia). Ya no bloquea el guardado, solo
  devuelve motivos.
- Nueva función `_techo_snapshot()` — fotografía consumido/disponible del
  hotel/mes, usada para congelar `consumido_en_solicitud`/
  `disponible_en_solicitud` en el expediente (nunca se recalcula después).
- `create_pedido()` / `update_pedido()`: eliminado el bloqueo por techo al
  crear/editar (`_forzar_techo` ya no existe). El único chequeo real ahora
  vive dentro de la validación de `ENVIADO AL PROVEEDOR`: si sujeto a
  techo y hay motivos (y no hay ya un expediente aprobado para ese mes), se
  abre un `expediente_exceso` y el pedido queda en
  `PENDIENTE Vº Bº DIRECCIÓN GENERAL` en vez de enviarse.
- `mes_consumo_techo` se rellena solo al pasar de verdad a `ENVIADO AL
  PROVEEDOR`, y se libera (vuelve a NULL) si se cancela después — con nota
  de trazabilidad completa en `historial_estados` (nº pedido, importe,
  quién dio el visto bueno original, quién cancela).
- Nuevos endpoints `POST /api/expedientes/<id>/aprobar` y `/denegar` —
  aprobar reutiliza `_notificar_cambio_estado()` (mismo email/aviso que
  cualquier cambio de estado); denegar exige motivo obligatorio.
- Fuera de alcance de esta fase: la recarga masiva desde Excel
  (`reset_e_importar`, herramienta de admin) no pasa por este circuito —
  su interacción con `mes_consumo_techo` la cubrirá el backfill de la
  Fase 7.

`app.py` compila sin errores. Badge de versión del sidebar actualizado a
"V 12.29.10".

# v12.29.8 — 1 agosto 2026

🏗️ Rediseño de Techo de Gastos — Fase 1: modelo de datos

**Contexto:** primera fase de un rediseño grande del módulo de Techo de
Gastos (informe técnico de actuación aportado por el usuario, diseño
cerrado en 9 fases), que lo convierte de "preventivo sin autoridad real"
(aviso saltable por cualquiera) a un circuito de autorización real con
trazabilidad completa vía Dirección General, separando el **Techo de
Gasto** (situación presupuestaria del mes) del **Expediente de Exceso**
(registro permanente de cada autorización extraordinaria).

**Esta entrega es solo la Fase 1 (modelo de datos)** — todavía no cambia
ningún comportamiento visible; las fases siguientes (lógica de negocio,
jobs, endpoints, informe, frontend, migración/backfill, pruebas) llegarán
en próximas entregas.

**Cambios:**
- `ESTADOS_VALIDOS` (`models.py`): 2 estados nuevos —
  `PENDIENTE Vº Bº DIRECCIÓN GENERAL` y `DENEGADO POR DIRECCION GENERAL`
  (reabrible, cuenta como denegación en el histórico aunque el pedido
  nunca haya consumido techo).
- Nueva tabla `expediente_exceso` — un pedido puede tener varias filas si
  es reabrible (cada intento es una fila independiente, nunca se
  sobrescribe); incluye desde ya las columnas de "fotografía
  presupuestaria congelada" (`consumido_en_solicitud`,
  `disponible_en_solicitud`) para que el informe de Fase 5 nunca tenga que
  recalcular el histórico.
- 2 columnas nuevas en `pedidos`: `mes_consumo_techo` (se rellena solo al
  pasar a `ENVIADO AL PROVEEDOR`, se vacía al cancelar) y
  `no_autorizado_previo` (flag de integridad).
- Migraciones con `IF NOT EXISTS`, mismo patrón que el resto de `app.py` —
  sin acción manual en Supabase.

Badge de versión del sidebar actualizado a "V 12.29.8".

# v12.29.6 — 1 agosto 2026

🎨 Ajuste visual — "Plazo entrega (días)" y "Fecha de entrega específica" juntos

Los dos campos añadidos en v12.29.4 quedaban en filas distintas de la
rejilla del formulario (uno emparejado con "Fecha tramitación", el otro
solo en su propia fila) — poco identificativo al ser dos formas
alternativas del mismo dato. Unidos ahora en un mismo bloque, lado a lado,
para que se vea de un vistazo que son opciones relacionadas. Sin cambios
de comportamiento ni de backend, solo maquetación.

Badge de versión del sidebar actualizado a "V 12.29.6".

# v12.29.4 — 1 agosto 2026

📅 Fecha de entrega específica del proveedor (alternativa al plazo en días)

**Petición:** junto a "Plazo entrega (días)", añadir un campo de fecha de
entrega concreta — si el proveedor da un día exacto en vez de "X días", las
reclamaciones se calculan a partir de esa fecha. Si no se rellena nada,
igual que hasta ahora.

**🔴 Bug crítico encontrado y corregido de paso (no buscado):**
`_calcular_fecha_entrega_prevista()` usaba dos nombres (`_d`, `_dt`) que
NUNCA se importaron en esa función. Como `fecha_tramitacion` se guarda como
TEXT, la función siempre caía en la rama que los necesitaba, lanzaba un
`NameError` silenciado por un `except Exception: return None`, y devolvía
`None` siempre — mismo patrón de fallo ya corregido en `_dias_desde_fecha`
el 30 de julio, pero que aquí se quedó sin arreglar. **Resultado: toda la
lógica de alertas por "Plazo entrega (días)" llevaba inactiva desde que
existe la funcionalidad**, sin ningún error visible en logs — nunca disparó
un aviso por esa vía. Corregido usando los nombres bien importados a nivel
de módulo (`datetime`, `_date`).

**Cambios:**
- Nueva columna `fecha_entrega_especifica` (DATE) en `pedidos`.
- Nueva función `_resolver_fecha_entrega_prevista(pedido)`: prioriza la
  fecha específica si existe; si no, calcula por
  `fecha_tramitacion + plazo_entrega_dias` (comportamiento de siempre); si
  no hay ninguno de los dos, `None` — igual que cuando no se rellenaba nada.
- `_alertas_plazo_entrega()` y `_debe_usar_logica_plazo()` usan el nuevo
  resolutor — las reclamaciones automáticas y la clasificación de alertas ya
  respetan la prioridad fecha específica > plazo en días.
- Añadida la columna a las consultas SQL del job de alertas y de `/api/stats`,
  y al `INSERT`/`UPDATE` de pedidos.
- Frontend: nuevo campo "Fecha de entrega específica (proveedor)" junto a
  "Plazo entrega (días)", con nota explicando la prioridad. El cálculo de
  "📅 Entrega prevista" que ya se mostraba en el formulario ahora prioriza
  la fecha específica si está rellena. Oculto también para el rol hotel,
  igual que el plazo en días.

Badge de versión del sidebar actualizado a "V 12.29.4".

# v12.29.2 — 31 julio 2026

🔧 Revisión de las últimas actualizaciones + 2 correos que se quedaron sin logo

**A petición del usuario, revisión completa del zip subido (v12.29.0)
contra el código real**, no solo contra el propio CHANGELOG. Resultado:

✅ **Correcto — Techo de gastos por familia (v12.28.0 y v12.29.0):**
`_check_techo()` Reglas 2 y 4, job de familia repetida, los 2 endpoints
de resumen y su renderizado en frontend (tarjetas + exportación/impresión)
— todo revisado línea a línea, sin fallos.

✅ **Correcto — Logo en 7 plantillas de proveedor/internas (v12.27.22):**
`_email_header_html()` bien diseñada (tabla, no flexbox — mucho más
compatible con clientes de correo tipo Outlook) y usada en las 7
plantillas que dice el CHANGELOG.

❌ **Encontrado — 2 correos se quedaron sin logo pese al "sí, a todos":**
el código de verificación de login (`_email_html_simple()`, la plantilla
de la captura original) y el de restablecimiento de contraseña seguían
sin cabecera de marca — ninguno de los dos usaba `_email_header_html()`
ni el helper con logo. Corregido: `_email_html_simple()` ahora envuelve
el cuerpo con `_email_header_html()`, y el email de reset de contraseña
(antes párrafos sueltos sin plantilla) pasa a usar `_email_html_simple()`
igual que el resto de correos cortos tipo "código/enlace".

❌ **Encontrado — `CHANGELOG.md` con 2 cabeceras de versión perdidas:**
las entradas de v12.28.0 y v12.27.22 estaban presentes en el cuerpo del
texto pero sin su línea `# vX.Y.Z — fecha` — quedaban concatenadas bajo
la cabecera de la versión siguiente. Corregido (mismo tipo de fallo que
ya se dio un par de veces al insertar entradas nuevas encima de una
existente — hay que llevar cuidado de reincluir la cabecera de la
entrada que ya estaba). `docs/HISTORIAL_CAMBIOS.md` sí las tenía
correctamente, no hizo falta tocarlo por eso.

Badge de versión del sidebar actualizado a "V 12.29.2".

# v12.29.0 — 31 julio 2026

📉 Techo de gastos — importe máximo (€) también configurable por hotel/mes **y familia**

**Petición:** tras el límite de Nº de pedidos por hotel/mes y familia
(v12.28.0), se pide el mismo control pero en importe: hasta ahora el único
tope en € era el mensual **por hotel** (`techo_max_mes`, Regla 3 de
`_check_techo`); no había forma de limitar cuánto podía gastar **una
familia concreta** en el mes sin tocar código.

**Cambio:** nuevo parámetro editable **"Techo — Importe máximo mensual por
hotel y familia (€)"** (`techo_max_mes_familia`), en el mismo grupo 💳
*Techo de gastos*. Por defecto **0 = sin límite** (no cambia nada en
producción hasta que un admin ponga un valor > 0).

**Apartados revisados y actualizados:**
- `_check_techo()` — nueva Regla 4: suma el importe de los pedidos de esa
  familia en el hotel/mes y, si `techo_max_mes_familia > 0`, bloquea el
  pedido si el acumulado de la familia superaría ese importe (igual que la
  Regla 3 ya hacía a nivel de hotel/mes total).
- `/api/techo/resumen` y `/api/techo/resumen-historico` — devuelven ahora
  también `familias_importe` (€ acumulado por familia) y
  `max_importe_familia`.
- Pestaña **📉 Techo de gastos** (tarjetas por hotel) — la línea "Familias:"
  añade el importe acumulado de cada familia frente al nuevo límite
  (`Nombre (n/max pedidos · importe/max €)`) cuando el límite en € está
  activo, y resalta en ámbar tanto por Nº de pedidos como por importe.
- Exportación/impresión del resumen de Techo de gastos — el resaltado de
  "familia repetida" ahora también se dispara si el importe acumulado de
  la familia alcanza el nuevo límite en €, no solo por Nº de pedidos.
- Migración `ON CONFLICT DO NOTHING` para instalaciones ya desplegadas +
  seed para instalaciones nuevas — no requiere ninguna acción manual en
  Supabase.

No se ha añadido (todavía) un aviso automático dedicado por Telegram/popup
cuando se supera este importe por familia — solo bloquea la creación del
pedido y se ve reflejado en el resumen/dashboard. Si se quiere una alerta
proactiva como la de "Familia repetida", habría que darla de alta como
nuevo evento en `eventos_aviso` (fuera del alcance de esta petición).

Badge de versión del sidebar actualizado a "V 12.29.0".



📉 Techo de gastos — límite de pedidos configurable por hotel/mes **y familia**

**Petición:** hasta ahora, "Familia/partida repetida" era una regla fija en
código: una familia de artículos solo podía usarse **una vez al mes por
hotel** (Regla 2 de `_check_techo`), y el único número configurable desde
Config alertas → Techo de gastos era el máximo de pedidos **totales** por
hotel/mes (`techo_max_pedidos`). No se podía permitir, por ejemplo, 2 o 3
pedidos de la misma familia al mes sin tocar código.

**Cambio:** nuevo parámetro editable **"Techo — Nº máximo de pedidos por
hotel/mes y familia"** (`techo_max_pedidos_familia`, por defecto **1** —
mismo comportamiento que antes hasta que un admin lo cambie), en el mismo
grupo 💳 *Techo de gastos* que los 4 campos existentes.

**Apartados revisados y actualizados:**
- `_check_techo()` — la Regla 2 ya no bloquea "familia ya usada este mes";
  ahora compara el nº de pedidos de esa familia en el hotel/mes contra el
  nuevo límite configurable (igual que la Regla 1 ya hacía a nivel de
  hotel/mes total).
- Job `_job_familia_repetida_inner` (alerta 🔴 "Familia/Partida REPETIDA" a
  comprador y admins) — el `HAVING COUNT(*) > 1` fijo en SQL pasa a
  `HAVING COUNT(*) >= techo_max_pedidos_familia`, para que dispare
  exactamente en el mismo umbral que ahora bloquea la creación del pedido.
- `/api/techo/resumen` y `/api/techo/resumen-historico` — devuelven ahora
  `familias_conteo` (nº de pedidos por familia) y `max_pedidos_familia`,
  además de los campos existentes.
- Pestaña **📉 Techo de gastos** (tarjetas por hotel) — la línea "Familias:"
  muestra ahora el conteo de cada familia frente al límite
  (`Nombre (n/max)`) y resalta en ámbar las que están al límite o por
  encima.
- Exportación/impresión del resumen de Techo de gastos — el resaltado de
  "familia repetida" (antes fijo a `> 1`) usa ahora el mismo límite
  configurable por hotel.
- No fue necesario tocar el HTML de Config alertas: el panel se pinta
  dinámicamente desde `config_alertas`, así que el nuevo campo aparece solo
  en cuanto existe la fila en BD (migración `ON CONFLICT DO NOTHING` para
  instalaciones ya desplegadas + seed para instalaciones nuevas).

Badge de versión del sidebar actualizado a "V 12.28.0".

# v12.28.0 — 31 julio 2026



🖼️ Logo aplicado también a los emails de proveedor / internos de pedidos

**Petición:** el logo de la cabecera (v12.27.19-21) solo se había aplicado
a los emails de acceso/admin. Faltaban los emails "de negocio": los que
se mandan a proveedores y los internos de cambio de estado, firmas
pendientes y cotizaciones.

**Causa:** esos 7 puntos de envío no usaban el patrón de cabecera con
tabla + logo; unos llevaban una banda de color plana sin logo
(`_email_template_enviado_proveedor`, `_email_template_pendiente_firma`,
`_email_template_entrega_parcial`, `_email_template_pendiente_cotizacion`,
`_email_template_cotizacion_sin_proveedor`) y otros dos no llevaban
ninguna cabecera (el email de confirmación al proveedor y el aviso
interno de cambio de estado, ambos dentro de `enviar_emails_estado`).

**Cambios:**
- Nueva función única `_email_header_html(titulo, subtitulo, color_fondo,
  color_titulo, color_subtitulo)` — genera la cabecera estándar (tabla
  con título/subtítulo a la izquierda y el logo `logo-sidebar.png` a la
  derecha). Es el único sitio que hay que tocar para cambiar el logo,
  los textos por defecto o los colores de cabecera en toda la app.
- Las 7 plantillas de arriba ahora llaman a `_email_header_html(...)` en
  vez de repetir su propia banda de color:
  - Proveedor (rojo `#8B0000`): enviado al proveedor, entrega parcial,
    pendiente de cotización, confirmación de recepción de pedido.
  - Interno (navy `#1a3a6b`): pendiente de firma (Dirección de Compras /
    Dirección del Hotel), cotización sin proveedor asignado, aviso de
    cambio de estado de pedido.
- Contenedor exterior de cada plantilla ajustado (`border-radius` +
  `overflow:hidden`) para que la cabecera en tabla mantenga las esquinas
  redondeadas que antes daba la banda de color.

Badge de versión del sidebar actualizado a "V 12.27.22".

# v12.27.22 — 31 julio 2026

# v12.27.21 — 31 julio 2026

🐞 Fix — logo no aparecía en 3 de las 6 cabeceras + subtítulo poco legible

**Motivo:** captura real del email "[FASE 1] Nueva solicitud de acceso"
mostrando la franja navy sin logo (ni siquiera icono de imagen rota) y
el subtítulo "Control de Pedidos · Princess Canarias" casi invisible.

**Causas y cambios:**
- Logo ausente: 3 de las 6 plantillas tocadas en v12.27.20 (Fase 1 a
  admins, alta desde el Organizador, Fase 2 completada) calculaban
  `app_url` con fallback vacío (`os.environ.get("APP_URL", "")`). Sin
  esa variable definida en Render, el logo quedaba con `src` relativo,
  que no resuelve dentro de un cliente de correo. Igualado el
  fallback en las 3 al que ya usaban las otras 3:
  `https://control-pedidos-princess.onrender.com`.
- Subtítulo poco legible: usaba `color:rgba(255,255,255,.6)`, que
  Outlook de escritorio clásico (motor Word) suele ignorar,
  cayendo a un color por defecto sobre fondo navy. Cambiado a un hex
  sólido (`color:#b9c3dc`) en las 5 cabeceras con subtítulo.

Badge de versión del sidebar actualizado a "V 12.27.21".

# v12.27.20 — 31 julio 2026

🖼️ Logo aplicado a todas las cabeceras de email restantes

**Petición:** extender a todos el tratamiento de logo aplicado en
v12.27.19 al email de "Verificación de acceso".

**Cambios:**
- Localizadas 6 plantillas con cabecera en banda de color + título +
  subtítulo: 3 navy (`#0f2044`) — Fase 1 a admins, Fase 2, bienvenida
  al usuario — y 3 verdes (`#065f46`) — alta desde el Organizador,
  Fase 2 completada, "Cuenta creada automáticamente" (compacto).
  Aplicado el mismo patrón a las 6, no solo a las navy.
- Cabecera de bienvenida (única que ya llevaba logo) reconvertida al
  mismo patrón: antes el logo iba apilado arriba del título (38px);
  ahora va a la derecha ocupando la franja completa (64px), igual que
  el resto.
- Aviso compacto "Cuenta creada automáticamente" recibe un logo más
  pequeño (40px) con paddings ajustados a su franja, más corta que
  las demás.
- Todas las cabeceras pasan de `<div>` a `<table>` de dos columnas —
  más fiable en Outlook, que ignora flex/grid.
- Añadida la asignación de `app_url` (que faltaba) en la función de
  "Fase 2 completada", necesaria para poder referenciar el logo ahí.

Badge de versión del sidebar actualizado a "V 12.27.20".

# v12.27.19 — 31 julio 2026

🖼️ Logo en la cabecera del email de "Verificación de acceso" (Fase 2)

**Petición:** añadir el logo a la cabecera navy del correo con el
enlace "Continuar verificación →" tras una solicitud de alta,
agrandado y a la derecha de la franja, ocupando su alto.

**Cambios:**
- Cabecera pasada de `<div>` a `<table>` de dos columnas (más fiable
  en Outlook): título + subtítulo a la izquierda, logo de 64px de
  alto a la derecha.
- Alturas de padding cuadradas entre ambas columnas para que el logo
  quede centrado verticalmente, ocupando la franja con un margen de
  14px arriba/abajo en vez de tocar los bordes.
- Alcance inicial: solo este correo (Fase 2). El resto de plantillas
  con cabecera similar se dejaron pendientes — ver v12.27.20.

Badge de versión del sidebar actualizado a "V 12.27.19".

# v12.27.18 — 31 julio 2026

🔒 Aviso de nueva versión — ya no se puede cerrar sin recargar

**Petición:** tras el fix de v12.27.16 (pestañas obsoletas seguían
despachando correos), reforzar el propio aviso: quitar la forma de
cerrarlo sin recargar, y que se recargue sola pasados 5 minutos por
si nadie está delante de la pantalla.

**Cambios:**
- Quitado el botón "Ahora no" — el modal de nueva versión ahora solo
  tiene "↻ Recargar ahora". No hay backdrop-click ni tecla Escape que
  lo cierre (ya no los había; se confirmó explícitamente).
- Eliminada `_cerrarModalVersion()` — era la única vía para
  descartarlo sin recargar, ya no tiene sentido mantenerla.
- Nuevo temporizador `_iniciarCuentaAtrasNuevaVersion()`: cuenta atrás
  visible en el propio modal (`5:00` → `0:00`) que, al llegar a cero,
  llama sola a `_recargarConVersion()`. Pensado para pestañas de
  fondo sin nadie delante — si el usuario recarga antes a mano, el
  temporizador se limpia sin más.

Badge de versión del sidebar actualizado a "V 12.27.18".

# v12.27.16 — 31 julio 2026

🛑 Fix — pestañas con versión desactualizada seguían despachando la cola de emails

**Motivo:** en pruebas reales tras v12.27.12, un email de "[FASE 1] Nueva
solicitud de acceso" llegó en texto plano pese a que backend y frontend
ya estaban desplegados con la prioridad `cuerpo_html` corregida. Causa:
ese correo lo despachó automáticamente la pestaña de un admin que
llevaba abierta desde antes del despliegue — el aviso de "nueva
versión disponible" es solo informativo, y cerrarlo con "Ahora no"
silencia el aviso **sin recargar la página**, así que esa pestaña
seguía ejecutando el JS antiguo (con la prioridad `cuerpo_text`) de
forma indefinida.

**Cambio:**
- `_mostrarModalNuevaVersion()` — llamada desde los 4 puntos donde se
  detecta versión nueva (chequeo al cargar, polling periódico,
  `refreshCurrentView`) — ahora detiene el poller de la cola de
  emails de sistema (`_emailsSistemaPollTimer`) en cuanto se dispara.
  Así una pestaña obsoleta deja de despachar correos con lógica
  antigua; la cola queda a la espera de otra pestaña ya actualizada
  (o de que esta se recargue).

Badge de versión del sidebar actualizado a "V 12.27.16".

# v12.27.14 — 31 julio 2026

🖼️ Logo de empresa en el email de bienvenida

**Petición:** tras confirmar que el email de "cuenta creada" ya
llegaba con el HTML completo (cabecera navy, tarjeta de credenciales,
botón), se pidió añadir el logo de la empresa en la cabecera.

**Cambio:**
- Cabecera de `body_html_u` (email de bienvenida al aprobar una
  solicitud de acceso): añadido `<img>` con `/static/logo-sidebar.png`
  — el mismo logo que ya se usa en el sidebar de la app sobre fondo
  navy, para que se vea igual de bien en la cabecera del correo.
- La URL del logo se construye con `app_url` (el mismo valor que ya
  usa esta función para el botón "Acceder al sistema") porque un
  email necesita una URL absoluta — una ruta relativa no resolvería
  en el cliente de correo.
- Alcance deliberadamente limitado a este email — hay otras ~5
  plantillas con la misma cabecera navy (aviso Fase 1 a admins, Fase
  2, aviso de alta a admins...) que de momento se quedan sin logo, a
  la espera de que se pida extenderlo.

Badge de versión del sidebar actualizado a "V 12.27.14".

# v12.27.12 — 31 julio 2026

📧 Correos EmailJS en HTML real (antes texto plano) — plantilla con triple llave

**Motivo:** los correos vía EmailJS se enviaban en texto plano
(`{{message}}`), aunque casi todos los endpoints ya construían una
versión `body_html` cuidada con estilos que simplemente se
descartaba antes de llegar al frontend. Con la plantilla EmailJS
(`template_1zrv4ze`) cambiada a `{{{message}}}` (triple llave, sin
escapar), se recupera ese HTML en vez de reconstruir el mensaje a
mano en texto plano.

**Backend (`app.py`):**
- 3 endpoints que ya generaban `body_html`/`body_html_u`/`body_html_a`
  pero no lo incluían en la respuesta JSON ahora lo devuelven junto
  al `body_text` existente (fase 2 completada → aviso admin, y alta
  de usuario/admins al aprobar solicitud).
- Nuevo helper `_email_html_simple()` — genera el HTML de correos
  cortos tipo "código / enlace" (saludo, párrafos, botón opcional)
  reutilizando el mismo estilo visual (tarjeta, botón `#8B0000`,
  pie gris) sin repetirlo en cada f-string.
- El código de verificación de login (único caso sin versión HTML
  previa) ahora también genera `body_html` con `_email_html_simple()`.
- Comentario de `_html_a_texto_plano()` actualizado: deja de ser la
  ruta principal (`cuerpo_html` pasa por delante de `cuerpo_text` en
  el frontend) y queda como generador de respaldo.

**Frontend (`index.html`):**
- Los 8 puntos que llaman a `enviarEmailJS(...)` pasan a usar el
  `body_html`/`cuerpo_html` correspondiente en el campo `message`,
  con `body_text` como respaldo si faltara (login, reset de
  contraseña, fase 2, aprobar solicitud ×2, cambios de estado de
  pedido, preview de alerta manual, cola de emails de sistema).
- Reset de contraseña: eliminada la plantilla de texto plano
  duplicada a mano en el frontend — usa directamente el `body_html`
  que el backend ya construía.
- Preview de alerta manual (`meaEnviarEmail`): envía
  `_meaData.body_html` directo en vez de convertirlo primero a texto
  plano con `construirTextoCorreoPlano()`.

Badge de versión del sidebar actualizado a "V 12.27.12".

# v12.27.10 — 31 julio 2026

📧 Backup EmailJS — cambio bidireccional (1↔2) con reinicio de contador

**Confirmado con el usuario:** cuenta 1 activa con contador en 8, y
una cuenta 2 de backup (otra cuenta EmailJS ya existente) lista para
usar. Aclarado que el contador debe reiniciarse a 0 en cada cambio,
de forma que cada cuenta cuente siempre de 1 a 195 en su ciclo.

**Corregido respecto a v12.27.8** (que solo cambiaba 1→2 una vez y
no reiniciaba el contador):
- El cambio automático ahora es bidireccional: al llegar al umbral
  cambia a la OTRA cuenta, sea cual sea la activa (1→2 o 2→1).
- El contador se reinicia a 0 en el mismo cambio — cada cuenta cuenta
  siempre de 1 a 195 en su propio ciclo, indefinidamente.
- Pensado para que, cuando la segunda cuenta también llegue al
  umbral, la primera ya se haya renovado del lado de EmailJS (su
  ciclo gratuito es mensual) y pueda reutilizarse como backup de la
  backup — round-robin continuo entre las 2 cuentas.
- Integridad y la nota del panel de administración actualizadas para
  reflejar el comportamiento bidireccional.

Badge de versión del sidebar actualizado a "V 12.27.10".

# v12.27.8 — 31 julio 2026

📧 Backup automático de cuenta EmailJS al acercarse al límite gratuito

**Motivo:** a raíz de haberse quedado sin cuota EmailJS (200/mes) a
mitad de ciclo por exceso de pruebas — se pidió un recuento de
correos enviados que, al llegar a 195 (5 antes del límite), cambie
solo las 3 credenciales para que los envíos sigan sin cortarse,
dejando constancia del cambio en Integridad.

**Cómo funciona:**
- Las credenciales EmailJS ya NO van fijas en el código — el
  frontend las pide al backend al cargar la página
  (`GET /api/emailjs/config`), que decide qué cuenta (1 o 2) está
  activa. Un cambio de cuenta se aplica sin desplegar nada.
- Nuevo helper central `enviarEmailJS()` — sustituye a las 9 llamadas
  directas a `emailjs.send(...)` de toda la app. Tras cada envío
  correcto, registra el envío en el backend
  (`POST /api/emailjs/registrar-envio`), que incrementa un contador de
  forma atómica.
- Al llegar el contador al umbral (195 por defecto, configurable) con
  la cuenta 1 activa: si la cuenta 2 (backup) tiene sus 3 credenciales
  completas, el sistema cambia solo a la cuenta 2 y registra la fecha
  del cambio. Si la cuenta 2 no está lista, NO cambia (para no
  dejar la app sin poder enviar) y queda como aviso urgente.
- Nuevo panel en Admin → Config Alertas ("📧 EmailJS — cuentas y
  backup automático"): credenciales de las 2 cuentas, contador y
  umbral editables, y quién está activa ahora mismo — con una nota de
  cómo forzar la vuelta a la cuenta 1 tras crear otra de backup.
- Admin → Integridad: nueva tarjeta "📧 Cuenta EmailJS" — avisa si ya
  se hizo un cambio automático, si se alcanzó el umbral sin backup
  listo (crítico), o si se está cerca del umbral sin backup
  configurado (aviso).

Badge de versión del sidebar actualizado a "V 12.27.8".

# v12.27.6 — 31 julio 2026

🏨 Correos por hotel — invertido el criterio por defecto

**Petición:** en vez de "vacío = general (todos los hoteles)" como
estado invisible en la ficha, que cada contacto nazca con **todos**
los hoteles marcados explícitamente, y sea el admin quien desmarque
los que no le correspondan — operación inversa a como se planteó en
v12.27.4. Y que los contactos que ya existen en este momento queden
marcados así, sin tener que hacerlo a mano uno por uno.

**Cambios:**
- Migración automática (una sola vez, idempotente): marca todos los
  hoteles a cada contacto que a día de hoy no tenga ninguno asignado
  en `proveedor_contacto_hoteles` — es decir, todos los contactos
  existentes, porque la función es nueva. Solo toca contactos sin
  ninguna fila, así que nunca vuelve a tocar un contacto ya
  restringido a mano después.
- Ficha de proveedor: las casillas de hoteles de un contacto ahora
  aparecen **todas marcadas por defecto** cuando no tiene ninguna
  restricción guardada (contacto nuevo, o caso residual) — antes
  aparecían todas vacías. Textos de ayuda actualizados en
  consecuencia ("desmarca los que no le correspondan").
- Sin cambios en el backend de envío
  (`_get_proveedor_emails_principales`) ni en el guardado — el
  resultado de "todo marcado" ya se guardaba correctamente como lista
  explícita de hoteles, solo cambiaba lo que se veía por defecto en
  pantalla.

Badge de versión del sidebar actualizado a "V 12.27.6".

# v12.27.4 — 31 julio 2026

🏨 Correos específicos por hotel en la ficha de proveedores

**Petición:** poder asignar en la ficha de un proveedor uno o varios
hoteles a cada contacto, de forma que las reclamaciones automáticas
vayan al contacto responsable del hotel del pedido en concreto (en
vez de a todos los contactos "principal" generales del proveedor),
manteniendo la copia al comprador del hotel (ya existía).

**Cómo funciona:**
- Nueva tabla `proveedor_contacto_hoteles` (contacto ↔ hotel).
- Un contacto **sin** hoteles asignados sigue siendo "general" — se
  usa para cualquier hotel del proveedor, comportamiento de siempre.
- Un contacto **con** hoteles asignados solo se usa para pedidos de
  esos hoteles — si existe al menos un contacto ★ principal asignado
  al hotel del pedido, se usa(n) SOLO ese(s); si no hay ninguno
  específico para ese hotel, se cae a los generales.
- `_get_proveedor_emails_principales(proveedor_id, hotel_id)` ahora
  recibe el hotel del pedido — actualizado en los 5 puntos donde se
  llama (correo al cambiar a Enviado al Proveedor, reclamación
  automática, vista previa/envío manual, validación al pasar a Enviado
  al Proveedor).
- Ficha de proveedor: cada contacto tiene ahora una sección "🏨
  Hoteles asignados a este contacto" con checkboxes de todos los
  hoteles (vacío = general). La lista de proveedores también muestra
  un indicador 🏨 con los hoteles cuando un contacto tiene alguno
  asignado.
- El CC al comprador del hotel en la reclamación automática no
  cambia — seguía y sigue funcionando igual, independientemente de a
  qué contacto del proveedor vaya el "Para:".

Badge de versión del sidebar actualizado a "V 12.27.4".

# v12.27.2 — 31 julio 2026

✍️ Correo interno de cambio de estado — redacción mejorada + ENVIADO AL PROVEEDOR + quién hizo el cambio

**Petición:** el correo interno de cambio de estado (Entregado,
Entrega Parcial, Cancelado) llegaba muy básico. Se pidió: redacción
más cuidada y profesional, extenderlo también a ENVIADO AL PROVEEDOR
(antes solo cubierto por el BCC del correo externo al proveedor, sin
un aviso interno propio), y que indique quién realizó el cambio de
estado (dato que no puede salir en el correo al proveedor).

**Cambios:**
- `enviar_emails_estado()` acepta ahora `usuario_nombre` — se pasa
  desde `_notificar_cambio_estado()` (cambios de estado manuales) y
  desde `create_pedido()` (alta directa en un estado con correo
  interno). Se añade como línea "Realizado por:" en el correo interno,
  solo si hay nombre disponible.
- El correo interno ahora también se genera para ENVIADO AL PROVEEDOR
  (antes excluido a propósito) — se envía ADEMÁS del correo externo al
  proveedor, no en su lugar.
- Redacción: icono por estado (📤 enviado, 📦 entrega parcial, ✅
  entregado, ❌ cancelado) en asunto y cabecera del cuerpo, separadores
  visuales, secciones "📋 Datos del pedido" y "📦 [histórico de
  entregas]", pie de aviso automático. Aplicado tanto al texto plano
  (el que realmente se entrega — ver EmailJS) como al HTML.
- Destinatarios sin cambios: comprador(es) + usuario(s) hotel del
  hotel del pedido, ya combinados en `_todos_internos`.

Badge de versión del sidebar actualizado a "V 12.27.2".

# v12.27.0 — 31 julio 2026

🔧 Corrección — el email de usuario no debe ser obligatorio para guardar

**Motivo:** en v12.25.8 se añadió una validación que bloqueaba guardar
la ficha de usuario sin email. Correcto según el planteamiento
inicial, pero el usuario aclaró: la falta de email en compradores/
admins activos ya se detecta y avisa en Admin → Integridad
(`compradores_sin_email`, `admins_sin_email`), así que bloquear el
guardado es innecesario — y además le quita a un admin la posibilidad
de dejar el email vacío a propósito para anular el envío de correos a
un usuario concreto, sin tener que desactivar la cuenta entera.

**Corrección:** quitada la validación de email obligatorio en
`/api/usuarios` (POST y PUT) y en el formulario del frontend. La
ficha de usuario ahora explica junto al campo Email que dejarlo vacío
anula los envíos a ese usuario, y que Integridad lo señalará como
aviso informativo si corresponde. `email2` no se ve afectado, sigue
opcional sin cambios.

Badge de versión del sidebar actualizado a "V 12.27.0".

# v12.25.8 — 31 julio 2026

📧 Segundo email opcional por usuario (ficha de usuarios)

**Petición:** poder asignar un segundo email (opcional) a cada
usuario, de forma que cuando un comprador tenga los 2 asignados,
todos los correos que se envíen sobre sus hoteles lleguen a ambos —
pero que la firma siga usando solo el primero (obligatorio).

**Implementación:**
- Nueva columna `email2` en `usuarios` (opcional; `email` pasa a ser
  obligatorio, validado tanto en el backend — `/api/usuarios` POST/PUT
  — como en el propio formulario del frontend).
- Nuevo helper `_emails_usuario(u)` → `[email]` o `[email, email2]`,
  usado en TODOS los puntos donde el email de un comprador se usa como
  **destinatario** (BCC del correo al proveedor al cambiar de estado,
  CC de la reclamación automática, destinatarios de los avisos
  internos de firma pendiente y cotización sin proveedor, y TO/CC de
  los envíos manuales desde el panel de alertas) — nunca en la firma,
  que sigue usando en exclusiva `_firma_comprador_html()`/
  `_firma_comprador_text()` con el email principal.
- Ficha de usuario (Admin → Usuarios): nuevo campo "Email 2
  (opcional)" con nota explicativa; el email principal ahora se marca
  como obligatorio (`Email *`). La tabla de usuarios muestra el
  segundo email debajo del principal cuando existe.

Badge de versión del sidebar actualizado a "V 12.25.8".

# v12.25.6 — 31 julio 2026

🔧 Corrección — 2 de las 3 plantillas se quedaron con la firma antigua

**Reportado:** con capturas reales de Gmail (carpeta Enviados),
confirmando que la firma seguía saliendo en el formato antiguo
("Nombre / email · Móvil: xxx") en vez del corporativo (v12.25.0),
en un correo de "Solicitud de cotización" — pero el arreglo de
espaciado de v12.25.4 sí se veía correctamente aplicado.

**Causa:** al aplicar la firma corporativa en v12.25.0, el reemplazo
masivo solo tocó el bloque de visualización final (quitar las líneas
"Dpto. Central de Compras Princess en Canarias" / "Princess Hotels &
Resorts" duplicadas) en las 3 plantillas de alerta, pero la
construcción de la variable `_firma_contacto` en sí — la que arma
nombre/email/móvil — solo se actualizó a `_firma_comprador_html()` en
`_email_template_enviado_proveedor`. `_email_template_entrega_parcial`
y `_email_template_pendiente_cotizacion` se quedaron con la
construcción manual antigua (`· Móvil:`, sin departamento ni
dirección), sin que se notara porque ambas compilaban perfectamente.

**Corrección:** las 3 plantillas usan ahora, de forma consistente,
`_firma_contacto = _firma_comprador_html(comprador_nombre,
comprador_email, comprador_movil)`. Verificado que no queda ningún
rastro de "· Móvil:" en todo `app.py`.

Badge de versión del sidebar actualizado a "V 12.25.6".

# v12.25.4 — 31 julio 2026

🔧 Corrección — correos automáticos llegaban con líneas en blanco duplicadas

**Reportado:** un correo real de "Entrega parcial" (56 días,
departamento Cocina) llegó con líneas en blanco entre casi cada dato
(Pedido Nº, Hotel, Departamento, Estado actual...), muy desorganizado
— excepto entre "Días transcurridos" y "Observaciones", que sí salían
pegados sin línea en blanco.

**Causa:** `_html_a_texto_plano()` (red de seguridad que convierte el
`body_html` de un correo a texto plano cuando no se le pasa un
`cuerpo_text` explícito — el caso de la reclamación automática al
proveedor, el aviso de firma pendiente y el aviso de cotización sin
proveedor) no tenía en cuenta que las plantillas HTML son f-strings
Python escritas en varias líneas con indentación: esos saltos de línea
"de formato del código fuente" son ruido invisible en HTML (el
navegador los ignora), pero la función los dejaba intactos y ADEMÁS
insertaba su propio salto de línea al convertir cada `<br>`/`</p>` —
resultado: doble salto de línea en casi cualquier sitio, EXCEPTO en el
único punto donde el `<br>` estaba en la misma línea de código que el
texto siguiente (la excepción "Observaciones" pegado, que fue la pista
que confirmó la causa).

**Corrección:** ahora se colapsa primero todo el espacio en blanco
crudo (saltos de línea, tabulaciones, espacios repetidos) a un único
espacio — igual que hace un navegador al renderizar HTML — y solo
después se insertan los saltos de línea con significado real
(`<br>` → salto simple; cierre de párrafo/bloque/título → línea en
blanco; cierre de fila/elemento de lista → salto simple). Probado
contra un HTML equivalente al del correo real reportado — resultado
limpio.

Badge de versión del sidebar actualizado a "V 12.25.4".

# v12.25.2 — 31 julio 2026

🔑 Cambio de cuenta EmailJS (cuota de 200 peticiones/mes agotándose)

**Motivo:** la cuenta EmailJS anterior (`service_dwwha2g`) se quedó a
5 peticiones de agotar el límite gratuito del mes, con 15 días aún
por delante hasta el reset del ciclo (14 agosto) — muchas pruebas y
ajustes de la aplicación consumieron la cuota.

**Solución:** cuenta EmailJS nueva, independiente, con su propio
contador de 200/mes desde cero. Mismo Gmail conectado
(`controlpedidosprincess.canarias@gmail.com`), plantilla replicada
con los mismos campos (`to_email`, `bcc`, `reply_to` en destinatarios;
`{{subject}}` / `{{message}}` en asunto y cuerpo, con
`white-space: pre-wrap` para respetar los saltos de línea del texto
plano que le manda la app).

Credenciales actualizadas en `templates/index.html`:
- Public Key: `WCiU7q8WT1i8AQTbR` → `bxFzHypsIrNqcDh15`
- Service ID: `service_dwwha2g` → `service_shvrzuv`
- Template ID: `template_krpvmda` → `template_1zrv4ze`

La cuenta anterior no se ha borrado — sigue existiendo con su propio
ciclo, disponible como reserva si hiciera falta.

Badge de versión del sidebar actualizado a "V 12.25.2".

# v12.25.0 — 31 julio 2026

✍️ Firma corporativa estándar en los correos al proveedor

**Petición:** sustituir la firma que llevaban los correos con firma de
comprador por el formato corporativo ya usado en el resto de
correspondencia de Compras (nombre, departamento, dirección física,
teléfono con prefijo y email), cambiando nombre/teléfono/email por
los del comprador que corresponda en cada caso.

**Antes:**
```
Atentamente,
Dpto. Central de Compras Princess en Canarias
Princess Hotels & Resorts
{Nombre}
{email} · Móvil: {móvil}
```

**Ahora:**
```
Atentamente,
{Nombre}
Dpto. Central de Compras Canarias

Av. Touroperador Tui, s/n
35100 - Maspalomas (Gran Canaria)
(+34) {móvil}
{email}
```

**Implementación:** dos funciones nuevas y compartidas,
`_firma_comprador_html()` / `_firma_comprador_text()` — dirección y
departamento fijos, nombre/teléfono/email según el comprador (se
omiten sin dejar hueco si el comprador no tiene móvil o nombre
registrado). Sustituye la firma en los 4 puntos que ya llevaban firma
de comprador: correo de confirmación de recepción al proveedor, y las
plantillas `_email_template_enviado_proveedor`,
`_email_template_entrega_parcial` y `_email_template_pendiente_cotizacion`
(esta última reutilizada también por la reclamación automática). Los
avisos internos al comprador (firma pendiente, cotización sin
proveedor) no llevan firma personal — sin cambios ahí.

Badge de versión del sidebar actualizado a "V 12.25.0".

# v12.23.8 — 31 julio 2026

📧 Aviso automático al comprador en Pendiente Firma Dirección Compras / Dirección Hotel

**Petición:** que estos dos estados también avisen por email
automáticamente al comprador del hotel de lo que está pendiente,
igual que ya se hacía con Pendiente Cotización.

**Criterio de disparo:** decidido junto con el usuario — estos dos
estados tienen el umbral "Urgente" en 0 = nunca por defecto, así que
en vez de exigir nivel urgente (que nunca se alcanzaría), el email se
dispara con el mismo criterio que ya usa el Telegram automático para
estos estados: 1ª alerta + repetición por ciclo (Config Alertas).

**Implementación:**
- Nueva función `_encolar_aviso_firma_pendiente_auto()`, bajo el mismo
  interruptor maestro que el resto de avisos automáticos por email
  (`activar_reclamacion_proveedor_auto`) — reetiquetado en el panel
  admin a "Enviar avisos automáticos por email (reclamación a
  proveedor y avisos internos) cuando corresponda", porque ya cubre
  más que solo la reclamación al proveedor.
- Reutiliza la plantilla `_email_template_pendiente_firma()` ya
  existente (antes solo se usaba para la propuesta manual desde el
  panel) — un único envío con todos los compradores del hotel juntos
  en "Para:". Se ajustó su frase de cierre ("gestione con Dirección de
  Compras/Hotel...") para que tenga sentido yendo al comprador, que no
  es quien firma.
- `_ya_reclamado_hoy_manual()` generalizada para aceptar un `tipo`
  (antes fija a `alerta_proveedor`); ahora también soporta
  `alerta_interno`, para que el aviso automático no duplique un envío
  manual del mismo día desde el panel.

Badge de versión del sidebar actualizado a "V 12.23.8".

# v12.23.6 — 31 julio 2026



📧 Firma de correos con nombre y móvil del comprador + reclamación automática también para Pendiente Cotización

**1. Firma de correos — nombre y móvil junto al email del comprador**
En todos los correos que llevan firma de comprador (confirmación de
recepción al proveedor, y las plantillas de alerta de Enviado al
Proveedor / Entrega Parcial / Pendiente Cotización, incluida la
reclamación automática que las reutiliza), la firma ahora muestra
nombre en negrita, el email (mailto) y "· Móvil: XXXXXXXXX" si el
comprador tiene móvil registrado. `_get_todos_usuarios_hotel()` ahora
también selecciona el móvil de los compradores.

**2. Reclamación automática al proveedor, extendida a Pendiente Cotización**
Antes limitada a Enviado al Proveedor y Entrega Parcial. Nueva clave
de configuración `cotizacion_ciclo` (Admin → Config Alertas → grupo
"💬 Pendiente cotización", default 3 días) — antes ese estado no
repetía nunca el aviso. Efecto esperado: el reenvío de Telegram de
Pendiente Cotización también pasa a repetirse cada `cotizacion_ciclo`
días, igual que en el resto de estados con ciclo.

**3. Pendiente Cotización sin proveedor asignado → aviso al comprador**
Cuando la reclamación automática de Pendiente Cotización no encuentra
proveedor asignado en el pedido, ya no se omite en silencio: envía un
único correo interno a los compradores del hotel, indicando la fecha
de la solicitud, los días en espera y "Proveedor: Sin proveedor
asignado hasta la fecha". Reutiliza el mismo ciclo/dedup que la
reclamación normal.

Badge de versión del sidebar actualizado a "V 12.23.6".

# v12.23.4 — 30 julio 2026

🔧 Corrección — un pedido recibía tantas reclamaciones como contactos "principal" tuviera el proveedor

**Reportado:** en la misma tanda, el pedido 23979 llegó 2 veces, el
40130 3 veces, el 15147 2 veces, el 28090 1 vez... Confirmado que no
eran destinatarios distintos: coincidía exactamente con cuántos
contactos tiene cada proveedor marcados como "principal" (estrella
dorada) en su ficha.

**Causa:** `_encolar_reclamacion_proveedor_auto()` pasaba
`proveedor_emails` (una lista) como `destinatarios_email` a
`_encolar_email_sistema()` — que encola **una fila, y por tanto un
envío independiente, por cada elemento de esa lista**. Con 2-3
contactos "principal", salían 2-3 reclamaciones separadas del mismo
pedido en la misma pasada del job.

**Corrección:** un único envío, con todos los contactos principales
juntos en el "Para:" (`", ".join(proveedor_emails)`) — mismo patrón
que ya usan correctamente los otros dos sitios del código que mandan
email a proveedor (el aviso al cambiar de estado y el "Re-notificar"
manual), que nunca tuvieron este problema.

Badge de versión del sidebar actualizado a "V 12.23.4".

# v12.23.2 — 30 julio 2026

🔧 La reclamación estándar reclamaba TODOS los días — ahora respeta el ciclo de Config Alertas

**Reportado por el usuario:** tras confirmar que la reclamación
automática ya se dispara, notó que solo evitaba mandarse dos veces
*el mismo día* — pero no respetaba ningún ciclo de varios días, así
que un pedido urgente recibiría reclamación TODOS los días hasta
resolverse, en vez de cada N días.

**Petición:** que siga las mismas pautas ya configuradas en Config
Alertas, para poder controlarlas desde el panel de administración.

**Cambio:**
- `_nunca_notificado()` y `_dias_ultima_notificacion()` — ahora
  aceptan un parámetro `tipo` (antes fijo a `'telegram_auto'`),
  compatible hacia atrás (mismo comportamiento si no se pasa).
- Camino **estándar** (sin plazo informado): la reclamación ahora
  reutiliza el mismo `cfg["ciclo"]` que ya se configura por estado en
  Config Alertas — el mismo número que controla cada cuántos días se
  reenvía el aviso interno. Sin ciclo definido para un estado (p. ej.
  "Pendiente Cotización" en la captura del usuario, que solo tiene
  "1ª alerta" y "Urgente" sin ciclo), no se repite tras la primera vez.
- Camino **con plazo informado**: sin cambios — ya respetaba su
  propio ciclo ("Plazo entrega — Ciclo urgente tras vencer", panel
  "Plazo de entrega proveedor") desde el principio, integrado en
  `_alertas_plazo_entrega()`.
- Se mantiene la protección de "nunca dos veces el mismo día" como
  red de seguridad final, aunque el job se dispare más de una vez.

Badge de versión del sidebar actualizado a "V 12.23.2".

# v12.23.0 — 30 julio 2026

🔧 Corrección — la reclamación llegaba con el HTML crudo como cuerpo del email

**El hallazgo:** aunque el email de reclamación por fin se disparó
(v12.22.8 arregló que se generara), el usuario reportó que el
proveedor lo recibió con etiquetas HTML literales
(`<div style="font-family:Arial...`) en vez de un email legible.

**Causa:** el frontend arma el envío por EmailJS así:
```javascript
message: p.cuerpo_text || p.cuerpo_html || '',
```
`_encolar_reclamacion_proveedor_auto()` era la única llamada a
`_encolar_email_sistema()` de las 5 que hay en el código que **no**
pasaba `cuerpo_text` (versión en texto plano) — solo `cuerpo_html`.
Con `cuerpo_text` vacío, la cadena `||` cae al HTML crudo, y EmailJS
lo manda tal cual como si fuera texto plano — de ahí las etiquetas
visibles.

**Corrección:** añadida `_html_a_texto_plano()`, un conversor básico
de HTML a texto (saltos de línea en `<br>`/`</p>`/`</div>`, quita el
resto de etiquetas, desescapa entidades). Se aplica dentro de
`_encolar_email_sistema()` — si a alguna llamada (esta u otra futura)
se le olvida pasar `cuerpo_text` explícito, ahora se genera solo a
partir del HTML, en vez de dejarlo en blanco. Revisadas las otras 4
llamadas a esta función — todas ya pasaban su propia versión en texto,
así que el problema era exclusivo de la reclamación.

Badge de versión del sidebar actualizado a "V 12.23.0".

# v12.22.8 — 30 julio 2026

🔥 CAUSA RAÍZ ENCONTRADA — `_dias_desde_fecha()` llevaba tiempo devolviendo `None` siempre, para todo

**El hallazgo:** el log de diagnóstico de v12.22.6 mostró `dias=None`
en TODOS los pedidos evaluados, pese a que `valor_campo` mostraba
fechas con buena pinta (`2026-06-05`, etc.). La función tenía:

```python
elif isinstance(fecha_str, _d):
    f = fecha_str
else:
    f = _dt.strptime(...)
```

`_d` y `_dt` **nunca existieron en el ámbito de esta función** — solo
como imports locales dentro de otras funciones sin ninguna relación.
Cada llamada lanzaba un `NameError` por dentro, silenciado por un
`except Exception: return None` genérico. Resultado: `_dias_desde_fecha()`
devolvía `None` siempre, para cualquier pedido, sin ninguna excepción.

**Alcance real del bug — bastante más amplio de lo que parecía:**
esta función se usa en 3 sitios, los tres afectados por igual:
1. El job diario de alertas (`_job_alertas_diarias_inner`) — origen
   de toda esta investigación de los últimos días.
2. La reclamación automática al proveedor (dependía del `dias`
   calculado aquí).
3. **La alerta inmediata al cambiar el estado de un pedido** — esta
   no se había mencionado hasta ahora, pero estaba igual de rota.

Es decir: el sistema de "días sin avance" llevaba, con toda
probabilidad, tiempo sin disparar NADA nuevo — ni alertas internas,
ni reclamaciones — más allá de lo que ya estuviera registrado de
antes. Las notificaciones antiguas que se veían en el panel
("Notificado hace X días") eran de antes de que este bug entrara en
el código, no evidencia de que siguiera funcionando.

**Corrección:** usa los nombres correctamente importados a nivel de
módulo (`datetime` y `date as _date`, línea ~7 del archivo) en vez de
los inexistentes `_d`/`_dt`. Además, el `except` ahora registra la
excepción real con `log.warning()` en vez de tragársela en silencio —
para que un fallo de este tipo nunca vuelva a pasar desapercibido
tanto tiempo.

**Con este fix, el job de las 07-16h debería empezar a generar
alertas y reclamaciones normalmente** desde el próximo ciclo — sin
necesidad de ningún otro cambio.

Badge de versión del sidebar actualizado a "V 12.22.8".

# v12.22.6 — 30 julio 2026

🔍 Solo diagnóstico — el job termina en 336ms con 0/0, la sospecha ahora es que `alertas_raw` viene vacío

**Hallazgo:** en la ejecución de las 11:00, el job completó en 336ms
con "0 alertas enviadas, 0 omitidas" — demasiado rápido para estar
recorriendo las 33+ alertas urgentes reales que muestra el panel. Como
`omitidos` también quedó en 0 (y ese contador SÍ se incrementa en el
primer gate del camino estándar que casi todos los pedidos deberían
tocar), lo más probable es que la propia consulta SQL del job
(`alertas_raw`), que es DISTINTA de la que usa el panel de Alertas,
esté devolviendo 0 filas.

**Cambio (sigue sin tocar comportamiento):**
- `RECLAMACION-DEBUG alertas_raw=N filas` justo tras la consulta —
  confirma de una vez si el problema está ahí.
- Traza por cada pedido al entrar en el camino estándar: estado,
  si hay configuración de umbrales para ese estado, el campo de
  fecha de referencia usado, su valor, los días calculados y el
  umbral de "primera alerta" — para ver exactamente en qué escalón
  se cae un pedido si `alertas_raw` sí trae filas.

Badge de versión del sidebar actualizado a "V 12.22.6".

# v12.22.4 — 30 julio 2026

🔍 Solo diagnóstico — logging detallado para localizar por qué la reclamación seguía sin dispararse

**Contexto:** tras v12.22.2, el pedido #13549 (Fuerteventura, PILSA/GARAU,
95 días, sin plazo informado, `ENVIADO AL PROVEEDOR`, `URGENTE`) seguía
sin generar ninguna reclamación pasada más de una hora — y proveedor y
comprador SÍ tienen email registrado (descartados los dos motivos de
omisión silenciosa más obvios). No hay Shell disponible en el plan
Free de Render para inspeccionar el código desplegado directamente.

**Cambio (sin tocar el comportamiento, solo visibilidad):**
- Línea `BUILD-MARKER v12.22.2 reclamacion-fix activo` al inicio de
  cada ejecución del job — confirma en los logs que el código
  desplegado es el correcto, sin necesitar Shell.
- `RECLAMACION-DEBUG` con `pedido`, `estado`, `dias`, si la casilla
  está activa, y si ya se notificó la reclamación hoy — para CADA
  pedido urgente evaluado por el camino estándar.
- `RECLAMACION-DEBUG pedido=X resultado_encolar=True/False` justo
  después de intentar encolarla.
- Dentro de `_encolar_reclamacion_proveedor_auto()`: log explícito en
  los dos primeros puntos de retorno silencioso (estado no válido /
  `_build_alerta_email` sin resultado o `es_proveedor=False`) — antes
  solo el de "proveedor sin email" quedaba registrado.

**Cómo leerlo:** en Render → Logs, buscar `RECLAMACION-DEBUG` o
`BUILD-MARKER`, en el minuto siguiente a un despliegue o dentro del
rango horario 07-16h (el job solo corre en ese tramo).

# v12.22.2 — 30 julio 2026

🔧 Corrección más profunda — la reclamación seguía sin dispararse pese al fix de v12.20.8

**Contexto:** tras desplegar v12.20.8, se probó forzando el reenvío de
un pedido concreto (borrando su registro de `telegram_auto` de hoy en
`whatsapp_log`) y seguía sin aparecer ninguna reclamación. Investigado
con el usuario: el bloque de reclamación estaba colocado DESPUÉS de
toda la lógica de "¿toca reenviar el Telegram interno hoy?" (primer
aviso / umbral crítico ≥60 días / ciclo de N días desde el último
envío). Si esa lógica decidía "todavía no toca" — porque el ciclo de
reenvío del aviso interno (p. ej. cada 2 días) no había cumplido,
aunque el pedido llevara semanas urgente — el `continue` de esa rama
saltaba todo lo de después, incluida la reclamación. Borrar solo el
registro de HOY no arregla esto: el ciclo mira la ÚLTIMA notificación,
sea de hoy o de cualquier día anterior.

**Cambio:** el bloque de reclamación automática se movió para
evaluarse ANTES de esa lógica de ciclo, en los dos caminos (con plazo
y estándar) — con su propia deduplicación diaria
(`_ya_notificado_hoy(..., 'reclamacion_proveedor_auto')`),
completamente independiente de si el aviso interno de Telegram está
en su turno de reenvío o no. Es una decisión de negocio distinta:
"reclamar al proveedor" no debería depender de "cuándo le toca
otro toque de atención interno al comprador".

Eliminado el bloque duplicado que había quedado en v12.20.8 (ahora
solo hay una copia por camino, movida arriba).

Badge de versión del sidebar actualizado a "V 12.22.2".

# v12.22.0 — 30 julio 2026

🚀 Indicador visual de reclamación automática + evita solapar manual y automática el mismo día

**Contexto:** tras corregir en v12.20.8 que la reclamación automática
nunca se disparaba fuera del camino "con plazo", el usuario preguntó
si había algún punto visual para ver si ya se había reclamado
automáticamente — para no mandar una reclamación manual duplicando
una que el sistema ya envió solo. **También se detectó de paso** que
la consulta de verificación usada hasta ahora
(`emails_log WHERE tipo='reclamacion_proveedor_auto'`) nunca iba a
devolver filas: la reclamación automática registra su envío en
`whatsapp_log` (vía `_log_whatsapp`), no en `emails_log` — esa tabla
solo la usa el envío MANUAL (`alerta_proveedor`). Consulta correcta
para comprobar reclamaciones automáticas:
```sql
SELECT creado_en, pedido_id, destinatario, mensaje
FROM whatsapp_log
WHERE tipo = 'reclamacion_proveedor_auto' AND enviado = 1
ORDER BY creado_en DESC LIMIT 20;
```

**Cambios:**
1. **Indicador visual** — nuevo campo `reclamacion_auto` en el resumen
   de última notificación de cada alerta (`_resumen_ultima_notificacion`,
   alimentado por una nueva subconsulta a `whatsapp_log` en
   `PEDIDO_SELECT_STATS`). En el panel de Alertas aparece un badge
   naranja "🤖 Reclamado auto hace Xd" debajo de la notificación
   normal, sin mezclarse con ella. Incluido también en la vista de
   impresión.
2. **Evitar solapamiento manual/automático** — nueva función
   `_ya_reclamado_hoy_manual()` (consulta `emails_log` por
   `tipo='alerta_proveedor'` hoy) usada dentro de
   `_encolar_reclamacion_proveedor_auto()`: si un comprador ya mandó
   una reclamación manual hoy (botón "Re-notificar"), la automática se
   omite ese día — centralizado en la función compartida, así que
   cubre los dos caminos (con plazo y estándar) sin tocar cada uno.
   No se bloqueó la dirección contraria (mandar manual después de la
   automática) — el indicador visual ya avisa antes de hacerlo, y
   forzar un bloqueo ahí quitaría margen a un admin que quiera
   insistir a propósito.

Badge de versión del sidebar actualizado a "V 12.22.0".

# v12.20.8 — 30 julio 2026

🔧 Corrección — reclamación automática al proveedor no se disparaba nunca en la práctica

**Motivo:** el usuario activó la casilla "Enviar reclamación
automática por email al proveedor cuando vence el plazo" y, tras
varios días con pedidos urgentes de sobra en el panel de Alertas, la
tabla `emails_log` seguía sin ninguna fila con
`tipo='reclamacion_proveedor_auto'`. Investigado con el usuario:
`_job_alertas_diarias_inner()` clasifica los pedidos en dos caminos —
(1) **con plazo**: el pedido tiene `plazo_entrega_dias` informado por
el proveedor, usa `_alertas_plazo_entrega()`; (2) **estándar**: sin
ese campo, usa los umbrales generales de Config Alertas
(`_UMBRALES_ALERTAS`). La reclamación automática solo estaba
conectada al camino (1) — y la inmensa mayoría de los pedidos
urgentes reales no tienen `plazo_entrega_dias` relleno, así que caen
siempre en el camino (2), donde la reclamación nunca se llamaba.

**Aclaración del usuario, confirmada como diseño correcto:** el panel
"Plazo de entrega proveedor" ajusta los umbrales SOLO cuando el
pedido trae un plazo propio informado por el proveedor; si no lo
trae, deben cumplirse igualmente los plazos generales del panel — es
decir, la reclamación automática debía aplicar en ambos caminos, no
solo en el (1).

**Cambio:** añadido el mismo bloque de reclamación automática
(idéntico gating: `activar_reclamacion_proveedor_auto` activo,
`nivel == "urgente"`, no notificado ya hoy) también al camino (2),
justo después de `_enviar_telegram_compradores()`. La seguridad de
estado (`ENVIADO AL PROVEEDOR` / `ENTREGA PARCIAL`) ya la comprueba
internamente `_encolar_reclamacion_proveedor_auto()`, así que llamarla
sin filtrar por estado en el camino (2) es seguro — para el resto de
estados (`PENDIENTE COTIZACIÓN`, etc.) simplemente no hace nada.

Badge de versión del sidebar actualizado a "V 12.20.8".

# v12.20.6 — 29 julio 2026

🔧 Corrección — identificador reconocible en los popups de "Pedido sin avance"

**Motivo:** el título del popup mostraba `pedido.get("id")` — el id
interno de la fila en la base de datos, un contador global sin
relación con lo que se ve en la web — en vez de un número
reconocible. Investigado a fondo con el usuario tras un reporte de
aparente fallo de seguridad (alertas cruzadas entre hoteles);
confirmado con una petición de red real (`GET /api/pedidos/13537`)
que el pedido era correcto y del hotel correcto — el problema era de
claridad de interfaz, no de segmentación de datos.

**Cambio:** `_enviar_telegram_compradores()` — `titulo_bridge` ahora
usa `pedido_num` (SAP) si existe, o si no `norden` (el "Nº" de línea
del panel), con el id interno solo como último recurso — mismo
criterio que ya aplicaba el cuerpo del mensaje de Telegram.

**Contraparte de escritorio:** `main_agenda` v4.14.0
(`pedidos_agenda_bridge.py`, `_aviso_para_popup()`), mismo fix para
el popup que genera el propio Organizador al consultar la lista de
alertas activas.

Badge de versión del sidebar actualizado a "V 12.20.6".

# v12.20.4 — 28 julio 2026

🧹 Quitado el bloque de Telegram de la solicitud de acceso (fase 1)

**Motivo:** el bloque promocional de Telegram (qué es, enlaces de
descarga para PC/móvil) que aparecía en `#sol-panel-fase1`, entre el
teléfono y la selección de hoteles, no aporta nada útil en ese
momento — quien está pidiendo acceso todavía no tiene cuenta ni sabe
si se la van a aprobar. Esa información ya vive en el manual de
usuario, que se entrega una vez la cuenta está creada.

**Cambio:** eliminado el bloque completo (icono, texto explicativo,
botones "Descargar para PC" / "Descargar para móvil") de
`templates/index.html`. No se ha tocado nada de la fase 2
("Verificación PC") ni del resto del wizard — se revisó y no tenía
ninguna mención a Telegram.

# v12.20.2 — 28 julio 2026

🚀 Solicitud de acceso en un solo paso desde el Organizador de Escritorio

**Motivo:** el Organizador ya conoce el usuario de Windows de quien lo
usa — el rodeo de la web (fase 1 con los datos personales → email con
token → descarga y ejecución de un `.bat` que detecta `%USERNAME%` →
fase 2) solo existe porque un navegador no tiene forma de leer esa
información directamente. Desde la app de escritorio ese rodeo es
innecesario.

**Nuevo — `POST /api/solicitar-usuario/directo`:** fusiona en una sola
llamada lo que en la web son fase 1 (`nombre`, `apellidos`, `email`,
`movil`, `hoteles`) + fase 2 (`usuario_windows`). Valida los 6 campos,
comprueba que el usuario de Windows no tenga ya cuenta activa (mismo
chequeo que la fase 2 real; `409` con `ya_existe` si ya existe), e
inserta la solicitud directamente con `estado='completada'` — sin
generar token ni depender de que el solicitante reciba y abra un
email — así que cae en la misma cola de aprobación del panel admin
(`GET /api/admin/solicitudes-acceso`) sin ningún cambio en ese panel.
Notifica por Telegram y encola el email a admins vía
`_encolar_email_sistema` (mismo mecanismo fiable que ya usa la fase 1;
no depende de EmailJS en un navegador del solicitante, que en este
caso no existe).

**Sin cambios en el flujo de aprobación:** `/api/admin/solicitudes-acceso/<id>/aprobar`
sigue creando la cuenta y enviando la contraseña exactamente igual que
hoy, sea cual sea el origen de la solicitud (web en dos fases, o este
endpoint nuevo en un solo paso).

**Decisión de seguridad asumida:** se pierde la comprobación de
"propiedad del email" que aportaba el token intermedio de la fase 2
web — aceptable aquí porque el origen es la app interna instalada en
el equipo del solicitante, no un navegador sin autenticar.

**No se ha tocado nada del flujo web existente** (`/api/solicitar-usuario`
fase 1, `/api/solicitar-usuario/completar-fase2` fase 2, ni el wizard
del frontend) — el endpoint nuevo es una vía paralela exclusiva para
el Organizador.

**Contraparte de escritorio:** `main_agenda` v4.12.4
(`admin_auth.solicitar_alta_directa()` + formulario de "Crear acceso"
rediseñado con los 5 campos de la fase 1 web).

✅ **Verificado en producción el 28/07/2026** — probado con
`fetch()` desde consola del navegador (solicitud #13, creada, aprobada,
cuenta activa con rol y hoteles asignados, email de credenciales y
email de aviso a admins ambos despachados por EmailJS). Pendiente de
verificar el lado del Organizador de escritorio en un PC real sin
cuenta previa.

# v12.20.0 — 27 julio 2026

🔐 Nuevos endpoints de bridge para el login de Admin sin usuario/contraseña fijos (Organizador de Escritorio)

**Motivo:** el Organizador de Escritorio (`main_agenda`) tenía un usuario y
contraseña de Administración fijos y hardcodeados en el propio código
(`ADMIN_USER`/`ADMIN_PASSWORD`). Se sustituye por un sistema que usa el
usuario de Windows de cada persona y valida su contraseña contra Control
de Pedidos — este cambio son los dos endpoints nuevos que ese sistema
necesita en el backend; la parte de escritorio se entrega aparte
(`main_agenda_4_10_5`).

**Nuevo — `GET /api/bridge/existe`:** dado `usuario_windows`, responde
`{"existe": true/false}` consultando solo por `username` en `usuarios`
(`activo=1`) — nunca pide ni revela la contraseña. Lo usa el Organizador
para decidir si mostrar el formulario de login (usuario ya existe) o el
de alta (usuario nuevo).

**Nuevo — `POST /api/bridge/solicitar-alta`:** dado `{usuario_windows,
nombre}`, notifica por Telegram a los administradores (reutiliza
`_notify_solicitud_telegram`, ya existente) para que creen la cuenta
manualmente. Devuelve `409` si el usuario ya existe. **Deliberadamente no
recibe ni almacena la contraseña elegida** — el Organizador la guarda solo
en local, cifrada; este endpoint únicamente avisa de que hay una
solicitud pendiente, y el administrador crea la cuenta real desde Admin →
Usuarios con la contraseña que el usuario le indique por otra vía.

**Sin cambios en `usuarios` ni en el resto de endpoints existentes** —
`/api/bridge/login`, ya usado por el bridge de avisos, se reutiliza tal
cual para validar la contraseña de un usuario existente.

✅ **Desplegado y verificado en producción el 27/07/2026** —
confirmado con el Organizador de Escritorio funcionando de punta a
punta contra estos dos endpoints (login online + fallback offline).

# v12.19.1 — 23 julio 2026

🔧 La cola de emails de sistema también la despachan los compradores

**Motivo:** el poller que envía la cola `emails_sistema_pendientes` vía
EmailJS (incluida la reclamación automática a proveedor de v12.19.0)
estaba limitado a `rol === 'admin'` solo por una decisión antigua del
frontend — el backend ya lo permitía a cualquier usuario logueado
(`@login_required`, no `@admin_required`). Como los compradores ven todos
los hoteles (no solo los suyos), tiene sentido que también ayuden a
despachar la cola, en vez de depender solo de que un admin tenga la app
abierta.

**Cambiado:** el poller ahora se activa para `rol === 'admin'` **o**
`rol === 'compras'`, en los dos puntos donde arranca (login y recarga de
sesión). Sin cambios de backend — ya lo permitía.

# v12.19.0 — 23 julio 2026

📨 Reclamación automática por email al proveedor (plazo de entrega vencido)

**Qué hace:** cuando el plazo de entrega informado por el proveedor vence
(mismo cálculo que ya usan los avisos Telegram por plazo — nivel `urgente`
en `_alertas_plazo_entrega`) y el pedido sigue en `ENVIADO AL PROVEEDOR` o
`ENTREGA PARCIAL`, el job diario de alertas encola automáticamente el email
de reclamación al proveedor — la misma plantilla que ya se usaba para el
envío manual desde la ficha del pedido — con los compradores del hotel en
copia (bcc). Un envío por pedido y día natural (deduplicado igual que el
resto de alertas automáticas, vía `whatsapp_log`).

**Cómo se envía:** igual que el resto de la cola `emails_sistema_pendientes`
— esta app no tiene SMTP propio, así que el despacho real lo hace EmailJS
desde el navegador del primer admin que tenga la app abierta (poll cada 5
min). Es decir: la reclamación se genera y encola sola, sin que nadie tenga
que abrir el pedido ni pulsar "enviar", pero el envío físico sigue
dependiendo de que haya una sesión de admin activa en algún momento del día.

**Activación:** desactivado por defecto. Se activa desde Admin →
Configuración de Alertas → grupo "Plazo entrega" → *"Enviar reclamación
automática por email al proveedor cuando vence el plazo"*.

**Cambios técnicos:**
- Nueva clave `activar_reclamacion_proveedor_auto` en `config_alertas`.
- Nuevas columnas `cc_emails` y `pedido_id` en `emails_sistema_pendientes`
  (para llevar copia a compradores y trazabilidad del pedido de origen).
- `_encolar_email_sistema()` acepta ahora `cc_emails` y `pedido_id`.
- Nueva función `_encolar_reclamacion_proveedor_auto()`, reutiliza
  `_build_alerta_email()` y `_get_proveedor_emails_principales()`.
- El job diario (`_job_alertas_diarias_inner`) invoca la nueva función tras
  el envío de Telegram cuando `nivel == "urgente"`.
- El frontend (`_enviarEmailsSistemaPendientes`) envía ahora `bcc` a
  EmailJS con los `cc_emails` de cada fila pendiente.

# v12.18.2 — 23 julio 2026

🐛 Corrige rotura de layout en toda la app tras "Configuración de Avisos"

**Reportado:** en Usuarios (y previsiblemente en cualquier vista después de
Config. Avisos en el HTML) la pantalla aparecía con un hueco en blanco
enorme, un "Cargando configuración…" flotando a media pantalla, y el
contenido real más abajo, requiriendo hacer scroll para verlo.

**Causa:** una edición anterior (dentro del refactor de Configuración de
Avisos) dejó un fragmento duplicado y huérfano — un `#config-avisos-body`
repetido con `</div>` de más — que cerraba prematuramente los contenedores
`.content`/`.main`/`.app`. Todas las vistas definidas después de
"Configuración de Avisos" en el HTML (Restaurar backup, Usuarios...)
quedaban entonces fuera del contenedor normal de scroll, con el layout roto.

**Arreglado:** eliminado el bloque duplicado. Sin cambios de backend — es un
fix puro de HTML/maquetación.

# v12.18.1 — 23 julio 2026

🔔 Configuración de Avisos — cada pestaña muestra solo sus usuarios

**Reportado:** en la pestaña "🏨 Avisos para Compradores y Hoteles" seguían
apareciendo también los administradores como columna — las dos pestañas
compartían la misma lista completa de usuarios (admin + compras + hotel).

**Arreglado:** cada pestaña filtra ahora su propia lista:
- 👑 Administradores → solo usuarios con rol `admin`.
- 🏨 Compradores y Hoteles → solo usuarios con rol `compras` u `hotel`.

Cambio puramente de frontend (la misma respuesta del backend, filtrada en
el navegador según la pestaña activa) — no afecta a datos guardados ni
requiere tocar `notificaciones_config`.

# v12.18.0 — 23 julio 2026

🔔 Configuración de Avisos — dos pestañas: Administradores / Compradores y Hoteles

Sustituye los dos bloques apilados de la v12.17.2 (que seguían generando
confusión con el selector de hotel único arriba de todo) por **dos pestañas
completamente separadas**:

- **👑 Avisos para Administradores** — los eventos globales de supervisión
  (cambio de estado con alerta urgente, pedido crítico parado, techo
  superado, familias repetidas a nivel admin, salud del sistema, egress,
  solicitudes de acceso). Sin selector de hotel — ni siquiera aparece en
  esta pestaña, para que sea imposible pensar que depende de un hotel.
- **🏨 Avisos para Compradores y Hoteles** — los eventos operativos por
  hotel (cambio de estado normal, alertas de pedido pendiente, techo
  mensual, nuevo pedido sujeto a techo, familia repetida al comprador). Aquí
  sí aparece el selector de hotel, dentro de la propia pestaña.

Cada pestaña guarda de forma independiente — "Guardar cambios" solo aplica a
lo que esté visible en ese momento. Backend sin cambios respecto a la
v12.17.2 (la separación admin/hotel ya coincidía exactamente con
requiere_hotel=FALSE/TRUE; este cambio es puramente de interfaz).

# v12.17.2 — 22 julio 2026

🔔 Configuración de Avisos — corrige confusión entre eventos globales y por hotel

**Reportado:** al marcar destinatarios de "Cambio de estado con alerta urgente"
o "Pedido crítico parado" con Fuerteventura seleccionado, y luego cambiar el
selector a Gran Canaria, la configuración parecía "traspasarse" al segundo
hotel; al modificarla ahí, desaparecía del primero.

**Causa:** esos dos eventos son globales por diseño (una única lista de
destinatarios para supervisión de admins de todos los hoteles a la vez — son
justo los que generaron el problema original con Fuerteventura). El dato en
BD era correcto en todo momento; el problema era de interfaz: al mostrar
eventos globales y por hotel mezclados bajo el mismo selector de hotel, sin
separación visual, era natural interpretar que todo dependía del hotel
elegido.

**Arreglado:**
- El panel ahora separa físicamente **dos bloques**: "🌐 Avisos globales"
  (fijo, no depende del selector) arriba, y "🏨 Avisos del hotel: X" (sí
  depende del selector) debajo — ya no hay una sola tabla mezclando ambos
  tipos con un simple badge por fila.
- Defensa en profundidad en el backend: `PUT /api/admin/config-avisos` ahora
  decide el `hotel_id` de cada fila en servidor, según `requiere_hotel` en
  `eventos_aviso` — ignora lo que mande el navegador para ese campo. Así,
  aunque hubiera otro fallo de interfaz en el futuro, es imposible guardar
  un evento global con un hotel real (o uno por-hotel sin ninguno).
- Saneado automático al arrancar: borra cualquier fila que se hubiera
  guardado con un hotel_id indebido en un evento global durante las pruebas
  de hoy con la interfaz anterior. Si tenías algo marcado para "Cambio de
  estado con alerta urgente"/"Pedido crítico parado" con Fuerteventura o
  Gran Canaria seleccionados, revísalo tras desplegar — puede haberse
  limpiado y haga falta volver a marcarlo (Jesus Curbelo / Victor Martin).

# v12.17.1 — 22 julio 2026

🔔 Configuración de Avisos v2 — fase 2: techo de gastos y familias repetidas

Continuación de la v12.17.0: los tres avisos al comprador que quedaron fuera
a propósito de la primera entrega pasan ahora también por el panel unificado
Administrador → Configuración de Avisos, con selector de hotel:

- `techo_mensual_comprador` — job diario de techo mensual (semáforo
  amarillo/rojo). Antes: `_get_compradores_hotel()` fijo dentro de
  `_job_alertas_techo_mensual_inner`.
- `techo_nuevo_pedido_comprador` — aviso inmediato al crear un pedido sujeto
  a techo. Antes: `_get_compradores_hotel()` fijo dentro de
  `_telegram_alerta_techo`.
- `familia_repetida_comprador` — aviso al comprador cuando se repite una
  familia/partida en el mes. Antes: `_get_compradores_hotel()` fijo dentro
  de `_job_familia_repetida_inner`.

Los tres son eventos por hotel (`requiere_hotel=TRUE`), con Telegram y popup
configurables de forma independiente, igual que los dos de la fase 1. Semilla
automática al arrancar: copia tal cual quién recibía qué antes de esta
versión (gate independiente del de la v12.17.0, así que aplica igual si esta
instalación ya tenía desplegada la v12.17.0 con la tabla `notificaciones_config`
ya poblada).

De paso, se corrige una inconsistencia menor de la v12.17.0: la vista previa
de "Reclamación" (`GET /api/alertas/<id>/email-preview`) mostraba la lista de
Telegram del antiguo `_get_compradores_hotel()`, que ya no coincidía con
quién realmente recibe el aviso tras el cambio de la fase 1 — ahora usa el
mismo resolver (`alerta_pedido_hotel`) que el envío real.

**Lo que sigue igual, a propósito:** el modelo "1 hotel → 1 comprador"
(`usuario_comprador_hoteles`) se mantiene intacto para destinatario
principal/CC del correo interno (`_get_compradores_cc`) y para cualquier otro
uso de propiedad del hotel que no sea "a quién avisamos" — eso no formaba
parte del alcance de este cambio.

# v12.17.0 — 22 julio 2026

🔔 Configuración de Avisos v2 — panel unificado, ahora también por hotel

**Motivo:** una reclamación urgente (50 días, hotel Fuerteventura) llegó por
Telegram y popup a los 4 compradores en vez de solo al responsable de ese
hotel. La causa: el evento de supervisión `pedido_urgente_admin` tenía
configurados a los 4 compradores (en vez de a los admins), en Administrador →
Configuración de Avisos — se corrigió esa configuración directamente en BD sin
necesidad de tocar código. A raíz de esto, se ha ampliado el propio panel para
que este tipo de ajuste ya no dependa de tocar la base de datos a mano.

**Qué cambia:**
- El panel de Configuración de Avisos, que hasta ahora solo cubría 8 eventos
  globales de supervisión admin, incorpora dos eventos operativos nuevos que
  antes estaban fijos por código:
  - `cambio_estado_pedido` — el Telegram/popup inmediato al cambiar el estado
    de un pedido (antes: `_get_compradores_hotel()` + `_get_usuarios_hotel_rol_telegram()`).
  - `alerta_pedido_hotel` — el aviso automático del job diario y el botón
    «Re-notificar» de la vista Alertas (antes: `_get_compradores_hotel()`).
- Estos dos eventos son **por hotel**: el panel incluye un selector de hotel
  arriba de la matriz, y cada hotel tiene su propia lista de destinatarios —
  así un comprador o el personal de un hotel nunca ven avisos de otros
  hoteles, sin depender de que nadie recuerde marcar bien las casillas.
- La lista de usuarios seleccionables ahora incluye también el **rol "hotel"**
  (antes solo admin/compras), para poder decidir explícitamente si el
  personal de un hotel recibe estos avisos o no.
- Nuevo canal independiente: **popup** (🔔, Organizador Princess), separado
  de Telegram — antes el popup viajaba siempre pegado a quien tuviera
  Telegram marcado; ahora cada uno es un checkbox propio.
- Tabla nueva `notificaciones_config` (evento_codigo, hotel_id nullable,
  usuario_id, telegram, email, popup), sustituyendo a `config_avisos` para
  todo lo nuevo. Semilla automática al desplegar: copia tal cual quién
  recibía qué en el modelo anterior, así el día 1 nadie deja de recibir
  nada — a partir de ahí, todo editable desde el panel.
- `GET/PUT /api/admin/config-avisos` amplían su contrato para aceptar
  `hotel_id` y el canal `popup`; `GET /api/config-avisos/resolver` acepta
  `hotel_id` opcional y `canal=popup`.

**Deliberadamente fuera de esta versión** (queda para una fase 2, para no
arriesgar dos refactors grandes a la vez): los avisos de techo de gastos y de
familias de artículos repetidas al comprador siguen usando
`_get_compradores_hotel()` sin pasar por este panel — sí se mantiene, como
hasta ahora, el modelo "1 hotel → 1 comprador" (`usuario_comprador_hoteles`)
para todo lo que no es estrictamente "a quién avisamos": destinatario
principal del correo interno, CC, dashboards, etc.

# v12.16.4 — 22 julio 2026

🔒 Fix: RLS deshabilitado en tablas propias (Security Advisor de Supabase)

El Security Advisor de Supabase marcó `public.db_vacuum_log` como error ("RLS Disabled in Public") — cualquier tabla del esquema `public` queda expuesta vía la API REST automática (PostgREST) salvo que tenga Row Level Security activo. Ya se corrigió a mano por SQL Editor en la base de datos en producción; este cambio lo deja también fijado en el código, para que cualquier instalación futura (o una restauración completa desde cero) no vuelva a crear estas tablas sin RLS.

Esta app nunca usa la API REST de Supabase — backend y frontend hablan siempre por conexión directa a Postgres (`DATABASE_URL`), nunca con la `anon key` — así que activar RLS sin políticas es inofensivo para el funcionamiento, solo cierra un acceso público que no debería existir.

Alcance a propósito limitado a las tablas introducidas por las mejoras de egress/tamaño de BD/Storage — no se toca ninguna tabla propia de la aplicación (`pedidos`, `usuarios`, etc.):
- `egress_tracking`, `db_size_tracking`, `db_vacuum_log`
- `agente_heartbeat` (creada por `restore_agent.py`, no por esta app — se incluye aquí también por si el agente no ha corrido todavía en una instalación nueva)

# v12.16.2 — 22 julio 2026

🎨 Dashboard: comparativas reales, sparklines, narrativa automática y
widgets configurables — además del icono de la app en la pestaña del
navegador

Cuatro mejoras del Dashboard, todas pensadas para acercarlo al nivel de
un panel de control comercial sin añadir dependencias externas ni tocar
el resto de la aplicación, más un detalle de imagen de marca.

🖼️ Icono de la aplicación en la pestaña del navegador
- Añadido `static/favicon.png` (32×32) y `static/favicon-180.png`
  (apple-touch-icon), generados a partir del propio `logo-sidebar.png`
  recortado y centrado en un lienzo cuadrado transparente. Sustituye el
  folio en blanco genérico que mostraba antes la pestaña del navegador.
- `templates/index.html`: añadidas las etiquetas `<link rel="icon">` y
  `<link rel="apple-touch-icon">` en el `<head>`. No requiere cambios en
  `app.py` — Flask ya sirve `static/` de forma automática.

📊 Indicadores comparativos reales en las 4 tarjetas superiores
- `GET /api/dashboard/resumen`: nuevo bloque `entregas_variacion`
  (entregas registradas este mes vs. mes anterior), con el mismo patrón
  que ya existía para el total de pedidos.
- Las 4 stat-cards pasan de texto plano a "chips" de color:
  - **Pedidos**: variación real vs. mes anterior (ya existía el dato,
    faltaba mostrarlo bien) + tooltip con la variación del importe
    (dato que el backend ya calculaba pero no se usaba en ningún sitio).
  - **Entregados**: variación real de entregas vs. mes anterior (nueva);
    el % de cumplimiento anterior pasa a tooltip.
  - **Pendientes**: días de espera media, coloreado por umbral (verde
    ≤3 días, ámbar 3–6, rojo >6).
  - **Alertas**: desglose urgentes/avisos, coloreado por severidad.

📈 Sparklines (mini-gráficos de tendencia)
- `GET /api/dashboard/resumen`: nuevo bloque `series` con la evolución
  diaria de los últimos 14 días de "pedidos creados" y "entregas
  registradas" (días sin movimiento incluidos como 0, vía
  `generate_series`, para longitud de serie constante).
- Tarjetas de **Pedidos** y **Entregados**: mini-gráfico de línea con
  área sombreada en SVG puro (sin librerías), con tooltip nativo al
  pasar el ratón. No se añadió a Pendientes/Alertas por ser fotos del
  estado actual sin historial diario real detrás.

💡 Narrativa de datos — nueva tarjeta "Resumen de la semana"
- Solo frontend: `_buildInsights()` traduce las cifras que ya devuelve
  `/api/dashboard/resumen` (variación de pedidos/entregas/importe,
  hotel líder en cumplimiento, hotel con más alertas, proveedor con
  incidencias, tiempo medio de espera, SLA de aprobación, pedido que
  necesita atención urgente) en frases en lenguaje natural.
- Prioriza lo urgente primero, solo muestra variaciones significativas
  (≥8-10%) para evitar ruido, máximo 5 frases, y un mensaje neutro
  ("todo en orden") si no hay nada destacable esa semana.

⚙️ Widgets configurables — ocultar y reordenar el Dashboard
- Nueva columna `usuarios.dashboard_prefs` (TEXT, JSON) — cada usuario
  guarda su propia configuración; `NULL` = por defecto (todo visible,
  orden original), sin necesidad de sembrar nada al crear el usuario.
- Nuevos endpoints `GET`/`PUT /api/dashboard/prefs`, con validación de
  los widgets recibidos contra un catálogo fijo en el backend.
- Los widgets del Dashboard (Resumen de la semana, Actividad de hoy,
  Accesos rápidos, Por estado, Por hotel, Línea temporal, Ranking de
  proveedores, Hoteles, Últimos pedidos) pasan a vivir en un contenedor
  único reordenable; las 4 stat-cards superiores quedan fijas siempre
  visibles, por ser los indicadores principales.
- Nuevo botón "⚙️ Personalizar dashboard" abre un modal con
  checkboxes (mostrar/ocultar) y arrastrar para reordenar
  (drag & drop nativo, sin librerías). "Guardar" persiste vía la API y
  aplica al momento; "Restablecer" vuelve a la configuración por
  defecto.

# v12.16.0 — 21 julio 2026

📎 PDF también permitido donde antes solo se aceptaba correo

En el modal de pedido, "Fecha envío Vº Bº" y "Fecha tramitación" solo
aceptaban adjuntar el correo original (.eml/.msg). Ahora también
aceptan PDF — por si el correo se ha impreso/escaneado a PDF en vez de
guardarse como archivo de correo. Eran los dos únicos apartados
correo-only de todo el formulario (el resto, como "Fecha solicitud" o
"Nº Pedido DALI/SAP", ya admitían documento + correo).

Cambios:
- `POST /api/pedidos/<id>/adjuntos`: para `vb_eml`/`tramit_eml` ahora
  se acepta PDF además de `.eml`/`.msg`. Documento y correo son slots
  independientes (como en `pedido_doc`): pueden convivir un PDF y un
  correo a la vez en el mismo apartado, cada uno con su propio límite
  (1 correo, hasta 3 PDF).
- Frontend: los botones pasan de "✉️ Adjuntar correo" a
  "📎 Adjuntar correo / PDF", con el selector de archivo aceptando
  `.pdf` además de `.eml`/`.msg`. El icono de la lista de adjuntos ya
  distinguía PDF de correo automáticamente, sin cambios ahí.

# v12.14.1 — 21 julio 2026

🐛 Hotfix — Guardar hoteles-compras se quedaba "colgado", sin avisar de nada

La causa real de "no me deja reasignar", más profunda que el fallo de
v12.14.0: el helper `api()` lanza una excepción para cualquier respuesta
que no sea 2xx, con una única excepción prevista para el 422 de techo de
gastos. El endpoint de hoteles-compras responde con **409** cuando hay
conflictos o huérfanos — un código que `api()` no tenía contemplado, así
que lo convertía en excepción **antes** de que `saveUsuario()` llegara a
mirar `rc.conflictos`/`rc.huerfanos`. Como esa llamada no estaba dentro
de un try/catch, la excepción quedaba sin capturar: no salía ningún
toast, el modal no se cerraba, se quedaba parado sin más — el
`confirm()` de reasignación nunca llegó a ejecutarse ni una sola vez
desde que se construyó esta pantalla.

Corregido: `api()` ahora también trata como respuesta normal (no
excepción) el 409 de `{ok:false, conflictos:[...]}` /
`{ok:false, huerfanos:[...]}` — acotado a esa forma exacta, para no
tocar ningún otro 409 del resto de la aplicación.

Nota sobre el comportamiento cuando hay huérfanos Y conflictos a la vez
(p. ej. quitar dos hoteles sin sustituto Y tomar dos hoteles de otro
comprador en el mismo guardado): el backend detecta los huérfanos
primero, así que solo se ve un `confirm()` (por los huérfanos); al
aceptarlo se reintenta con `forzar=true`, que de paso también resuelve
los conflictos sin un segundo aviso específico para esos. El resultado
final es correcto, pero si preferís un único diálogo que liste ambos
problemas a la vez, es un ajuste aparte que puedo hacer.

# v12.14.0 — 21 julio 2026

🐛 No dejaba reasignar hoteles entre compradores

`PUT /api/usuarios/<id>/hoteles-compras` tiene dos protecciones: evitar
que un hotel se quede sin comprador ("huérfanos") y avisar si un hotel
ya está asignado a otro comprador ("conflictos"). La segunda ya tenía
confirmación + reintento con `forzar=true`; la primera **no tenía
ninguna forma de continuar** — bloqueaba en seco con un 409 y el
frontend directamente mostraba el error y paraba.

Efecto práctico: reasignar un hotel de un comprador A a un comprador B
solo funcionaba si lo hacías en un orden concreto (añadirlo primero a
B, confirmar la reasignación, y ya después quitarlo de A si hacía
falta). Si lo intentabas al revés — quitárselo primero a A, pensando en
dárselo a B a continuación — se quedaba bloqueado sin más, sin ninguna
pista de cómo seguir. Con varias reasignaciones a la vez es fácil caer
en ese orden y parecer que "no deja reasignar" nada.

Cambios:
- `set_usuario_comprador_hoteles()`: el bloqueo por huérfanos ahora
  respeta `forzar=true`, igual que ya hacía el de conflictos.
- Frontend: el caso de huérfanos ya no es un bloqueo silencioso — pide
  confirmación ("¿Continuar de todas formas? Asígnalos a otro usuario
  después") y, si confirmas, reintenta con `forzar=true`.

# v12.13.0 — 21 julio 2026

🔒 Dos huecos de seguridad cross-hotel + 🐛 accesos rápidos del Dashboard

Seguridad:
- `GET /api/pedidos/<id>` ahora comprueba que el pedido pertenezca a un
  hotel del usuario cuando `rol == 'hotel'` (403 "Sin acceso a este
  pedido"), igual que ya hacía `PUT /api/pedidos/<id>`. Antes se podía
  ver la ficha completa de un pedido de otro hotel probando IDs
  directamente contra la API.
- `GET /api/exportar` (descarga de Excel) ahora filtra por
  `hoteles_ids` cuando `rol == 'hotel'`, en vez de exportar los pedidos
  de todos los hoteles para cualquier usuario logado.

Bug del Dashboard (Nivel 1, v12.9.0):
- Los accesos rápidos "Ver alertas", "Techo de gastos" e "Integridad"
  no funcionaban — el HTML generado tenía comillas dobles anidadas
  (`onclick="showViewGuarded('alertas', document.querySelector('[data-view="alertas"]'))"`),
  así que el navegador cortaba el atributo `onclick` en la primera
  comilla interna y el botón quedaba roto. "Nuevo pedido", "Nuevo
  proveedor" e "Importar Excel" sí funcionaban porque no tenían
  comillas anidadas — por eso solo fallaban "varios, no todos".
  Corregido con un helper `_dashQuickNav(view)` que hace la navegación
  en JS real en vez de construir la llamada como texto dentro del
  atributo HTML.

# v12.12.0 — 21 julio 2026

📬 Fase 2 de solicitud de acceso: envío por cola en vez del navegador del solicitante

Confirmado con un dato clave: antes de automatizar Fase 1→Fase 2 (v12.4),
cuando un admin aprobaba a mano, el email llegaba bien. La diferencia real
no era el contenido del email (arreglado en v12.11.0) sino **quién** lo
dispara: antes salía del navegador de un admin (equipo de trabajo
conocido, en red corporativa, con los dominios de EmailJS ya permitidos);
desde v12.4 salía del navegador de quien solicita el acceso — por
definición alguien nuevo, probablemente en un equipo sin homologar o una
red más restrictiva.

Cambios:
- `solicitar_usuario_fase1()` ya no devuelve los emails para que el
  navegador del solicitante los mande por EmailJS. Ahora se **encolan**
  en `emails_sistema_pendientes` — la misma cola que ya usa el resto de
  avisos de sistema (techo, integridad, egress) desde v12.4 — y los
  despacha el navegador del primer admin que abra la aplicación. Mismo
  mecanismo, misma fiabilidad que tenía el proceso manual original.
- `emails_sistema_pendientes` gana `solicitud_acceso_id` (para vincular
  la fila a la solicitud y mostrar su estado en el panel) y
  `recordado_en` (para no repetir el recordatorio cada 10 minutos).
- Nuevo job `_job_recordar_emails_sistema_pendientes` (cada 10 min,
  07:00–21:00): si hay algo en la cola sin enviar desde hace más de 10
  minutos y no se ha recordado en los últimos 30, manda un Telegram a
  los admins — *"Abre Control de Pedidos para completarlo"*. El propio
  aviso de Telegram de Fase 1 ya deja claro desde el primer momento que
  hace falta abrir la app.
- Panel admin: el badge bajo cada solicitud ahora distingue "⏳ En cola
  — esperando que se abra la app" de "📧 Enviado (cola) · fecha".
- El botón "Reenviar Fase 2" (ahora "Enviar/reenviar Fase 2") se
  mantiene tal cual — sigue disparando desde el navegador del admin que
  lo pulsa, sin pasar por la cola, porque en ese caso ya hay un admin
  presente y no aporta nada encolarlo.
- Actualizado el texto del panel de éxito que ve el solicitante: ya no
  promete el email "en unos segundos" ni menciona el paso del `.bat`
  (retirado del email en v12.11.0).

Trade-off asumido a propósito: la Fase 2 deja de ser "instantánea (pero
a veces no llega nunca)" y pasa a ser "en minutos, pero de verdad
llega" — siempre que algún admin abra la app en un plazo razonable; el
recordatorio de Telegram está para cubrir justo ese caso.

# v12.11.0 — 21 julio 2026

🐛 Fase 2 de solicitud de acceso no llegaba al usuario

Diagnóstico: tanto el envío automático (tras completar Fase 1) como el
reenvío manual desde el panel admin usan el mismo `emailjs.send()` desde
el navegador. El botón manual reportaba éxito (toast verde) pero el
usuario nunca recibía el email — es decir, EmailJS aceptaba el envío y
el fallo ocurría después, fuera de este código. La causa más probable:
el email de Fase 2 mencionaba un archivo `verificar_acceso.bat` como
adjunto ("haz doble clic para verificar tu acceso") que en realidad
**nunca se adjuntaba** — `emailjs.send()` en esta app nunca ha mandado
adjuntos, el único sitio que genera el `.bat` de verdad es un endpoint
aparte que lo descarga al navegador del *admin*, sin relación con el
envío automático. Ese patrón (adjunto ejecutable + verificación urgente
por enlace) es una combinación clásica que los filtros anti-phishing
corporativos (Microsoft 365 Safe Attachments, Mimecast…) suelen poner
en cuarentena en silencio — el remitente nunca ve el rebote.

Cambios:
- `_construir_email_fase2()` reescrito: ya no promete ningún adjunto,
  solo el enlace de verificación — mismo patrón que el resto de emails
  transaccionales de la app, con menos "señales" de phishing.
- Corregido el texto del aviso a admins, que también mencionaba el
  archivo inexistente.
- Nuevo: `solicitudes_acceso` registra si el `emailjs.send()` del
  navegador tuvo éxito o no (`fase2_email_estado`,
  `fase2_email_detalle`, `fase2_email_en`), tanto en el alta automática
  como en el reenvío manual, vía el nuevo endpoint
  `POST /api/solicitudes-acceso/<id>/registrar-envio-fase2`.
- El panel admin de Usuarios ahora muestra, bajo el estado de cada
  solicitud, si el email de Fase 2 se envió (con fecha) o falló (con
  detalle del error en el tooltip) — antes no había forma de saberlo
  sin que el usuario avisara.

No tocado a propósito: seguir dejando el botón "💾 Descargar .bat" tal
cual — es la vía manual (el admin lo descarga y lo adjunta él mismo,
por ejemplo desde Outlook) que sigue teniendo sentido si el correo
corporativo del hotel bloquea sistemáticamente los envíos vía EmailJS.

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
