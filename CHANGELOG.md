# Changelog

Todos los cambios notables de este proyecto se documentan aquí.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
y el versionado, [Semantic Versioning](https://semver.org/lang/es/)
(`MAJOR.MINOR.PATCH`).

> Nota: `HISTORIAL.md` cuenta el relato de cómo se llegó hasta aquí
> (decisiones, exploraciones de diseño, contexto). Este `CHANGELOG.md` es
> el registro corto y versionado de qué cambia en cada entrega, pensado
> para consultarlo de un vistazo.

> Convención de versionado (a partir de v1.17.1, a petición de Víctor):
> `backend/package.json` y `frontend/package.json` se actualizan SIEMPRE
> al mismo número en cada entrega, aunque esa entrega solo toque uno de
> los dos lados — así el número que se ve en la propia app (esquina
> inferior del menú, `Sidebar.jsx`, sacado de `frontend/package.json`)
> siempre coincide con la versión real más reciente entregada, sin
> depender de si el cambio de turno tocaba frontend o no.

## [Sin publicar]

## [1.19.68] - 2026-09-11

### Añadido
- **Botón de descarga en PDF cuando el listado de "Documentación pendiente" es muy largo** — a petición de Víctor, sobre un correo real con ~140 referencias: "cuando un listado de faltantes es tan extenso, se puede crear un PDF y enviar en vez del detalle un boton para la descarga del listado bien estructurado?". Cuando un proveedor tiene más de 30 referencias con ficha técnica pendiente, el correo de "Documentación pendiente" (`EmailProveedorModal.jsx`) ya no las itemiza una a una dentro del texto — en su lugar, incluye un botón de descarga a un PDF nuevo, público (sin necesidad de sesión, ya que el proveedor no tiene cuenta en DALI), con el listado COMPLETO de lo que le falta a ese proveedor: no solo ficha técnica, también ficha de seguridad e imagen, una columna por tipo de documento — un documento de referencia más completo que la propia lista a la que sustituye. Por debajo de 30 referencias, el correo sigue itemizando la lista dentro del propio texto, exactamente igual que hasta ahora.
- Nueva ruta pública `GET /export/documentacion-faltante-pdf/:idProveedor` (mismo router y mismo criterio de "descarga sin sesión" que ya usan `GET /export/excel` y `GET /export/pdf`) — recalcula la documentación pendiente de ese proveedor en el momento de la descarga (no una foto congelada de cuando se envió el correo).

### Verificación
- `node --check` en los tres ficheros backend tocados (`documentacionController.js`, `routes/export.js`, `utils/emailHtml.js`), limpio.
- Prueba funcional del PDF nuevo: generado con 60 artículos de muestra (para forzar salto de página), comprobado visualmente (convertido a imagen) que la cabecera, las tres columnas de "Falta"/"OK" (en rojo cuando falta), el color alterno de filas, y el pie de página con el número de página se ven correctamente en ambas páginas.
- Prueba funcional de la conversión de URL a botón en el HTML del correo (`textoPlanoAHtmlParrafos`): un párrafo con una URL al final se parte en el texto explicativo más un botón centrado con el enlace correcto; un correo sin ningún enlace (el caso de siempre, con la lista de viñetas) se sigue renderizando exactamente igual que antes.
- `npm run build` (frontend) sin errores.

## [1.19.67] - 2026-09-11

### Cambiado
- **Reorganización del Excel de "Exportar catálogo completo"** — a petición de Víctor, que mandó de vuelta el propio Excel exportado, reorganizado a mano en Excel, como plantilla a seguir ("¿podemos organizar el listado exportado como este que adjunto? filtros, tamaños columnas, nombres cabeceras columnas etc"). Cambios, todos calcados de esa plantilla: "Código Proveedor" pasa de ir al final a ir justo después de "Código DALI"; "Activo" pasa de ir justo después de "Proveedor" a ir al final; las columnas que vienen del Excel de artículos DALI (menos "Código DALI") llevan ahora el sufijo " - DALI" en la cabecera para distinguirlas de un vistazo de las columnas SAP (p.ej. "Descripción - DALI" frente a "Descripción SAP"); "Proveedor" pasa a llamarse "Proveedor Asignado - DALI"; los anchos de cada columna se han ajustado a los mismos que dejó Víctor en su plantilla (por ejemplo, la descripción pasa a ser mucho más ancha, y "Activo" mucho más estrecha); se añaden filtros de columna (el desplegable de Excel en la fila de cabeceras) sobre las 20 columnas; y "Código Proveedor" y "Activo" quedan centradas (cabecera y datos), igual que en la plantilla. Sin cambios en los datos que trae cada columna, solo en el orden, el nombre, el ancho y el formato.

### Verificación
- `node --check` en `exportController.js` y `generarExportWorker.js`, limpio.
- Prueba funcional contra el worker real: se generó un `.xlsx` con dos artículos de muestra (los mismos dos primeros del Excel de ejemplo de Víctor, uno activo y uno inactivo) y se comprobó que el fichero resultante tiene el filtro de columna en `A4:T4`, las 20 cabeceras con los nuevos nombres y en el nuevo orden, los anchos de columna exactamente iguales a los de la plantilla, la alineación centrada en "Código Proveedor" y "Activo" (cabecera y datos), y el color rojo de la fila del artículo inactivo — todo comparado directamente contra el Excel que envió Víctor.
- `npm run build` (frontend) sin errores — este cambio es solo de backend, pero se confirma que el resto de la app sigue compilando.

## [1.19.66] - 2026-09-11

### Corregido
- **"Worker terminated due to reaching memory limit: JS heap out of memory" en "Exportar catálogo completo"** — a los pocos días de desplegarse v1.19.65, Víctor reportó (con capturas del sidebar) que el botón nuevo se caía en producción con este error, en vez de descargar el Excel. Causa: para un catálogo grande (miles de artículos × 20 columnas, sin ningún filtro), la implementación original construía todo el libro Excel en memoria (`new ExcelJS.Workbook()` + `workbook.xlsx.writeBuffer()`) antes de enviar nada — cada celda se retiene como objeto JS hasta el final, así que el pico de memoria crece con el tamaño del catálogo completo y en el plan de Render usado en producción se supera el límite de heap del proceso. En el resto de exportaciones (Excel/PDF filtrados, con o sin selección manual) esto nunca ha dado problema porque manejan como mucho unos cientos de filas, no el catálogo entero.
- **Arreglo**: el worker de exportación ahora genera el Excel con `ExcelJS.stream.xlsx.WorkbookWriter`, que escribe cada fila a un fichero temporal en disco en cuanto se confirma (`fila.commit()`) y libera esa memoria de inmediato, en vez de acumular el libro entero en RAM; el controlador ya no arma el buffer completo tampoco, sino que hace streaming de ese fichero temporal directamente a la respuesta HTTP (`fs.createReadStream(...).pipe(res)`), borrándolo al terminar (o si algo falla a medias). Además, los datos que se pasan al worker (`workerData`) ahora son arrays posicionales de 20 valores en vez de objetos con 20 claves cada uno, para reducir la sobrecarga de memoria por fila también en el lado que arma los datos. El resto de exportaciones (Excel/PDF de catálogo filtrado o selección manual) no se han tocado — siguen usando el camino anterior porque ahí nunca ha habido problema de memoria.
- **Verificación**: `node --check` en los dos ficheros tocados, limpio. Prueba funcional contra el worker real (no una reimplementación): se generó un `.xlsx` de 5.000 filas × 20 columnas invocándolo exactamente como lo hace `exportarExcelCompleto`, y se comprobó que el fichero resultante abre correctamente, con las 20 cabeceras en el orden esperado, los valores de cada columna correctos, el color rojo en las filas de artículos inactivos y normal en las activas, y que el fichero temporal se borra después. Además, una comparación de pico de memoria (RSS) generando 60.000 filas × 20 columnas con ambos métodos —el buffer en memoria original y el nuevo streaming a disco— mostró una reducción del pico de ~1.491 MB a ~667 MB (un 55% menos), lo que confirma que el cambio reduce sustancialmente el consumo de memoria en el caso que causó el fallo en producción.

## [1.19.65] - 2026-09-10

### Añadido
- **Botón "Exportar catálogo completo"** — a petición de Víctor: un Excel con TODA la información que recogen los dos Excel que se importan (`ARTICULOS_DALI.xlsx` + `LISTADO_CODIGOS_DALI_-_SAP.xlsx`, ver `importController.js`) más la columna "Código Proveedor", en un único fichero — 20 columnas en total (código DALI, descripción, unidad, IGIC, naturaleza, familia, subfamilia, proveedor, activo, código SAP, descripción SAP, unidad SAP, grupo productos SAP, descripción de grupo de productos SAP, indicador de impuestos SAP, categoría valoración, tipo producto, grupo compras SAP, nombre grupo compras SAP y código proveedor). Sin ningún filtro: siempre el catálogo entero, activos e inactivos, pensado para revisión/reconciliación con los Excel de origen, no para lo que se esté viendo en pantalla. Botón nuevo en el sidebar (Gestión → Catálogo → "Exportar catálogo completo"), de descarga directa, sin pantalla propia.
- **Nuevo permiso granular `admin-exportar-completo`** — a petición de Víctor: "solo visible para el administrador principal, lo podemos poner configurable como el resto de apartados de visualización de administrador". Se suma al mismo sistema de permisos por apartado ya existente (migración `2026-09-03_permisos_admin.sql`): el administrador principal lo ve siempre, y puede concedérselo a otros administradores desde "Usuarios" — a diferencia de los 8 permisos ya existentes (que arrancaron concedidos a todos los admins de entonces), este es una capacidad nueva y arranca SIN concederse a nadie salvo al administrador principal, tal y como lo pidió.

### Verificación
- `node --check` en los cuatro archivos backend tocados, limpio.
- Prueba funcional del nuevo tipo de exportación del worker (`excel-completo`): genera un `.xlsx` real con ExcelJS a partir de artículos de muestra (uno activo, uno inactivo) y comprueba las 20 cabeceras en el orden esperado, los valores de la fila y el color rojo de la fila del artículo inactivo.
- `npm run build` (frontend) sin errores.

## [1.19.64] - 2026-09-10

### Añadido
- **Columna "Precio €" en el Excel de artículos seleccionados a mano** — a petición de Víctor: cuando un admin marca artículos con el tick del catálogo ("Ver solo marcados") y pulsa "Exportar Excel", el `.xlsx` descargado lleva ahora una columna extra al final del listado, después de "Activo", con la cabecera "Precio €". En DALI no existe ningún precio guardado (ni en la base de datos ni en la ficha del artículo), así que la columna sale siempre en blanco, pensada para rellenarla a mano — mismo tratamiento visual (celda con borde) que ya tiene "Cantidad" en el listado de comprador. Deliberadamente NO aparece en el resto de exportaciones Excel (el listado general filtrado por naturaleza/familia/búsqueda) ni en el PDF, solo en este caso concreto (`backend/src/controllers/exportController.js`, `backend/src/workers/generarExportWorker.js`).

### Verificación
- `node --check` en `exportController.js` y `generarExportWorker.js`, limpio.
- Prueba funcional aislada del worker de exportación (generando `.xlsx` real con ExcelJS y leyendo sus cabeceras) para los cuatro casos relevantes: admin+selección manual (con "Precio €"), admin sin selección manual (sin ella), no-admin (sin ella) y PDF (sin cambios) — los cuatro se comportan como se esperaba.

## [1.19.63] - 2026-09-10

### Añadido
- **Aviso de solicitudes de acceso pendientes en el menú** — a petición de Víctor ("tipo control pedidos alertas"): el botón "Solicitudes de acceso" del sidebar (Gestión → Accesos) muestra ahora un número con las peticiones pendientes de resolver, oculto por completo cuando no hay ninguna. Reutiliza el mismo `GET /admin/solicitudes-acceso` de siempre — sin endpoint nuevo, volumen bajo por diseño (altas de personal, no artículos). El contador (`App.jsx`, `refrescarSolicitudesPendientes`) se calcula solo si el admin tiene permiso sobre ese apartado (mismo criterio que el propio botón del menú, evita un 403 innecesario), se pide al iniciar sesión, se repasa cada 5 minutos, y se refresca al instante en cuanto se acepta o rechaza una solicitud (`AdminSolicitudesAcceso.jsx`, nuevo prop `onCambio`) — sin esperar a salir de esa pantalla.
- Estilo nuevo `.tab-badge`/`.tab-label-row` (`styles/index.css`) — con la etiqueta de latón (`--brass`) del propio sistema de diseño del catálogo, en vez de tomar prestados el navy/dorado de control-pedidos-princess.

### Verificación
- `npm run build` (frontend) sin errores.

## [1.19.62] - 2026-09-10

### Cambiado
- **"Documentación faltante" ya no necesita una plantilla EmailJS nueva — reutiliza la de "correo a un usuario"** — corrección sobre v1.19.60: esa entrega añadió `template_id_proveedor_1`/`template_id_proveedor_2` (migración `2026-09-09_emailjs_template_proveedor.sql`) asumiendo que hacía falta una plantilla EmailJS SEPARADA, con "Reply To" puesto a `{{reply_to}}`, para el Reply-To dinámico. Víctor mandó una captura de su plantilla "Contact Us" en EmailJS.com (las 2 cuentas): el campo "Reply To" YA tenía esa variable puesta desde siempre — la plantilla de usuario de toda la vida ya admitía Reply To dinámico, sin plantilla nueva. Se revierte: nueva migración `2026-09-10_emailjs_quitar_template_proveedor.sql` (mismo patrón que `2026-09-05_emailjs_quitar_template_admin.sql`, que vivió exactamente este mismo vaivén con el aviso a administradores) elimina esas 2 columnas; `documentacionController.js`/`emailjsConfig.js`/`AdminConfiguracionEmailjs.jsx` dejan de necesitarlas — "Documentación faltante" pasa a reutilizar `template_id_1`/`template_id_2`, pasando `reply_to` como variable adicional (`enviarProveedorPorEmailjs`, `services/emailjs.js`).
- Con esto, "Documentación faltante" queda operativa de inmediato en cuanto Víctor rellene (si no lo ha hecho ya) el "Template ID" de usuario de al menos una cuenta en Administración → Configuración EmailJS — ya no depende de ningún paso adicional en EmailJS.com.

### Verificación
`node --check` en todo el backend, limpio. `npm run build` en frontend, limpio.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.62**.

## [1.19.61] - 2026-09-10

### Corregido
- **Administración → Configuración EmailJS se quedaba en "Cargando…" para siempre si la consulta de configuración fallaba** — Víctor, tras desplegar v1.19.60: "no carga esta pantalla después de desplegar la ultima versión" (causa real, en su caso: la migración `2026-09-09_emailjs_template_proveedor.sql` todavía no estaba aplicada en Supabase, así que el `SELECT` de `configuracion_emailjs` fallaba al pedir las dos columnas nuevas que esa migración añade). El fallo real no era de la pantalla: `AdminConfiguracionEmailjs.jsx` SÍ generaba un aviso de error al fallar la carga, pero la condición que decide si mostrar "Cargando…" (`cargando || !form`) seguía siendo cierta para siempre en cuanto `form` se quedaba en `null` — el aviso nunca llegaba a pintarse porque ese `return` anticipado ocurre antes. Corregido: un estado de error de carga separado (no se autodesvanece a los 4s como el de "Guardar"), con un botón "Reintentar" — a partir de ahora, si esta pantalla falla al cargar (por esta causa o cualquier otra: red, sesión caducada, etc.), se ve el motivo en vez de un cuelgue silencioso.

### Verificación
`npm run build` limpio. Sin cambios de backend.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.61** (backend sin cambios en esta versión — se sube igual para mantener sincronizados los dos `package.json`).

## [1.19.60] - 2026-09-09

### Cambiado
- **"Documentación faltante" ya no depende de Control de Pedidos para enviar el correo — usa directamente el EmailJS propio de DALI** — a petición de Víctor: "necesito que la aplicacion catalogo asignaciones utilice su propio emailjs para solicitar la documentacion faltante, actualmente se encola y se envia desde control pedidos, pero como ya tenemos configurada propia cuenta de emailjs". Hasta ahora, al pulsar "Encolar envío" en `EmailProveedorModal.jsx`, el backend encolaba el correo en `emails_sistema_pendientes` de `control-pedidos-princess` (`controlPedidosEmailBridge.js`, `encolarEmailEnControlPedidos`, eliminada) y el envío real lo hacía el poller de esa app la próxima vez que alguien la tuviera abierta — la última dependencia de este tipo que le quedaba a DALI (el resto de sus correos son autosuficientes desde v1.15). Ahora el backend (`documentacionController.js`, `prepararEnvioDocumentacionFaltante`, antes `encolarEmailDocumentacionFaltante`, endpoint renombrado de `POST .../encolar-email` a `POST .../preparar-envio`) solo resuelve el destinatario real (sigue viniendo de Control de Pedidos, eso no cambia) y arma el HTML; el envío lo hace el propio navegador del admin, al momento, con `emailjs.send()` (nueva función `enviarProveedorPorEmailjs` en `services/emailjs.js`). El botón pasa a llamarse "Enviar email".
- **Reply-To dinámico sin el truco del puente** — la v1.19.57 ya había conseguido que, al responder, el correo le llegara al comprador que gestionó la solicitud (no al propio proveedor) modificando el poller de Control de Pedidos para aceptar un `reply_to` por envío. Con el envío directo, esto se resuelve de forma nativa: una plantilla EmailJS SEPARADA de la de "correo a un usuario" (2 columnas nuevas, `template_id_proveedor_1`/`template_id_proveedor_2` en `configuracion_emailjs`, migración `2026-09-09_emailjs_template_proveedor.sql`), con el campo "Reply To" puesto a `{{reply_to}}` en EmailJS.com — el navegador pasa `reply_to: req.user.email` (resuelto en el servidor, igual que antes) como variable en cada envío. Nuevo campo "Template ID (proveedor)" por cuenta en Administración → Configuración EmailJS, con instrucciones en el propio formulario.

### Pendiente de configuración (no bloquea el resto de la app)
- Falta crear esa plantilla en EmailJS.com (duplicar la de "correo a un usuario" y añadir el Reply To) y pegar su ID en Administración → Configuración EmailJS, en al menos una de las 2 cuentas. Hasta entonces, "Documentación faltante" sigue ofreciendo "Copiar"/"Abrir en tu cliente de correo" como alternativa manual — igual que ya hacía si el puente con Control de Pedidos fallaba.

### Verificación
`node --check` en todo el backend, limpio. `npm run build` en frontend, limpio. No hay forma de probar el envío real de punta a punta desde este entorno (necesita la plantilla EmailJS creada en producción) — pendiente de que Víctor la configure y confirme un envío real.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.60**.

## [1.19.59] - 2026-09-09

### Añadido
- **Icono y título de pestaña del navegador** — a petición de Víctor, para que la pestaña (y el acceso directo si se fija en la barra de tareas) se vea igual que la de Control de Pedidos: icono de la corona de Princess (mismos ficheros `favicon.png`/`favicon-180.png` que usa `control-pedidos-princess`, en `frontend/public/`, servidos por Vite en la raíz del sitio) y título `Catálogo Asignaciones` — el mismo nombre que ya usan la barra lateral y la pantalla de login (`Sidebar.jsx`/`LoginScreen.jsx`), que hasta ahora no llegaba a la pestaña del navegador (`frontend/index.html` tenía el título antiguo `Catálogo DALI` y no declaraba ningún icono, por lo que el navegador mostraba el icono genérico de página). `apple-touch-icon` incluido para cuando se añade a la pantalla de inicio en iOS/iPadOS.

### Verificación
`npm run build` limpio; comprobado que `favicon.png`/`favicon-180.png` quedan en la raíz de `dist/` junto a `index.html` (Vite copia `public/` tal cual) y que Render los sirve directamente igual que ya hace con `version.json`/`CHANGELOG.md` (ver comentario en `vite.config.js`), sin que la regla `/* -> /index.html` los intercepte. Sin cambios de backend.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.59** (backend sin cambios en esta versión — se sube igual para mantener sincronizados los dos `package.json`).

## [1.19.58] - 2026-09-09

### Cambiado
- **Auditoría de la versión desplegada (v1.19.57) y corrección de documentación desactualizada** — a petición de Víctor ("puedes auditar que este todo en su sitio, no falte nada y todo debidamente actualizado?"). Código revisado sin hallazgos (build de frontend y `node --check` de backend limpios; guardas de autenticación/permisos verificadas ruta por ruta en `admin.js` y consistentes en el resto de rutas). Documentación corregida en tres puntos: (1) `CHANGELOG.md` no tenía entrada para `[1.19.57]` pese a que `HISTORIAL.md` sí documentaba esa entrega (v1.39) — añadida a posteriori; (2) `README.md` y `backend/README.md` seguían listando como pendientes dos tareas de EmailJS ya resueltas desde v1.16/v1.38 (credenciales de Cuenta 1 y plantilla de aviso a administradores) — corregido para reflejar que solo queda la Cuenta 2; (3) `README.md` y `database/README.md` no advertían de que `database/schema.sql` por sí solo no basta para una instalación nueva — falta aplicar `database/migraciones/*.sql` (verificado contra el propio esquema: faltan `marcas_proveedor`, `solicitudes_acceso`, `tokens_acceso`, `configuracion_emailjs` y los permisos granulares de administrador en `usuarios`, entre otras) — añadida esa advertencia y el paso explícito en ambos documentos.

### Verificación
Cambio de documentación únicamente — nada de código que probar. `node --check` en backend y `npm run build` en frontend, limpios (sin cambios funcionales).

Versión: `backend/package.json` y `frontend/package.json` → **1.19.58** (sin cambios de código en esta versión — se sube igual para mantener sincronizados los dos `package.json`, según convención). Otros documentos revisados en esta entrega: `HISTORIAL.md` (actualizado, entrada v1.40); `frontend/README.md`, `backend/.env.example`, `render.yaml` — revisados, no aplica ningún cambio.

## [1.19.57] - 2026-09-08

### Corregido
- **El correo de "Documentación faltante" respondía al propio proveedor en vez de al comprador que lo gestiona** — a petición de Víctor, tras revisar un correo real ("Documentación pendiente — BRIGONSA GROUP 2015 SL") donde el proveedor, al pulsar "Responder", veía su propia dirección como destino en vez de la del comprador de DALI que había hecho la solicitud. Causa: el envío real de este correo lo hace Control de Pedidos (repo aparte, `control-pedidos-princess`) a través del puente que reutiliza su cola `emails_sistema_pendientes` — su poller fijaba `reply_to` al propio destinatario para TODA la cola, sin excepción para el evento `dali_documentacion_faltante`. Corregido solo en el lado DALI de este puente: `encolarEmailEnControlPedidos()` (`services/controlPedidosEmailBridge.js`) acepta ahora un `replyTo` opcional, que `encolarEmailDocumentacionFaltante()` (`controllers/documentacionController.js`) rellena con `req.user.email` — el comprador que ha iniciado sesión y gestiona la solicitud. El resto del arreglo (columna `reply_to` en la cola y el poller usándola) vive en `control-pedidos-princess` (ver su `CHANGELOG.md`, entrega v12.32.43).

**Verificación**: `node --check` en los dos archivos backend tocados, limpio. Pendiente de que Víctor confirme en Email History (EmailJS) que el "Reply-To" ya es el del comprador, no el del proveedor — ver `HISTORIAL.md` v1.39 para el detalle completo.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.57** (frontend sin cambios en esta versión — se sube igual para mantener sincronizados los dos `package.json`).

## [1.19.56] - 2026-09-07

### Añadido
- **Subida manual de imagen/ficha bloqueada sin código de proveedor** — en Administración → Artículos, la imagen y las fichas técnica/de seguridad de cada tarjeta (proveedor asignado, alternativo o marca extra) ya no se pueden subir hasta que esa tarjeta tenga guardado su código de proveedor. El selector de archivo aparece deshabilitado con un aviso explicando qué falta; en cuanto se guarda el código se habilita solo. Evita documentación grabada sin saber a qué código de proveedor pertenece. No afecta a la carga masiva por carpetas.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.56**.

## [1.19.52] - 2026-09-05

### Seguridad
- **El aviso a administradores de "Solicitud de acceso" filtraba sus emails a cualquier visitante anónimo** — al pedir "¿Has olvidado tu contraseña?" con un email NO registrado, `POST /auth/recuperar-acceso` devolvía en el JSON de respuesta (`envio.destinatario`) la lista completa de emails de administradores activos, visible para cualquiera con solo mirar DevTools → Red, sin que el correo llegara siquiera a enviarse. Corregido: `registrarSolicitudAcceso()` (`authController.js`) ya no incluye esa lista en el `envio`; el destinatario se fija ahora directamente en el panel de EmailJS, en una plantilla nueva y separada exclusiva para este aviso (columnas `template_id_admin_1`/`template_id_admin_2`, migración `2026-09-05_emailjs_template_admin.sql`). El frontend (`services/emailjs.js`) distingue por `envio.tipo` ("usuario" vs "admin") qué plantilla usar, y nunca manda el parámetro `to_email` a EmailJS para el caso "admin". "Administración → Configuración EmailJS" tiene un campo nuevo por cuenta para esta plantilla.
- Documentado y aceptado como riesgo residual conocido (sin cambios de código en esta entrega): sigue siendo observable, inspeccionando esa misma llamada a EmailJS, si un email concreto está o no registrado — ver el detalle en `HISTORIAL.md` v1.34.

### Pendiente de configuración (no bloquea el resto de la app)
- El aviso a administradores por email no se enviará hasta que se cree la plantilla "admin" en el panel de EmailJS (Cuenta 1 en producción) y se rellene su Template ID en Administración → Configuración EmailJS — mientras tanto, la solicitud de acceso se sigue registrando igual y es visible en Administración → Solicitudes de acceso.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.52**. Otros documentos revisados en esta entrega: `HISTORIAL.md` (actualizado, entrada v1.34, y lista de pendientes); `backend/README.md`, `frontend/README.md`, `README.md`, `backend/.env.example`, `DEPLOY.md` — revisados, no aplica ningún cambio (sin variables de entorno nuevas; la migración solo añade columnas, mismo procedimiento de despliegue de siempre).

## [1.19.51] - 2026-09-05

### Corregido
- **"Exportar documentación" seguía descargando la imagen genérica "SIN IMAGEN" una vez por cada artículo, en vez de una sola vez por proveedor** — bug encontrado por Víctor probando la corrección de v1.19.50 con un proveedor real (44 imágenes idénticas descargadas, una por artículo). Dos causas, las dos corregidas en `exportZipController.js`:
  - `imagenes.es_generica` no basta por sí sola: es una columna añadida el 2026-09-01 con `default false`, así que cualquier fila subida antes de esa fecha se quedó marcada `false` aunque de verdad fuera la genérica. Se añade la misma red de seguridad que ya usa `documentacionController.js` para este caso: si `es_generica` no viene marcado, un `hash_sha256` compartido por más de un artículo del mismo proveedor se toma como señal de que es la imagen de reserva.
  - Aunque `es_generica` viniera marcado, la deduplicación por "proveedor + ruta de Storage" nunca podía funcionar: `subirImagenArticulo` (`storageController.js`) guarda cada imagen en `<código_dali>/<proveedor>.<ext>` — una ruta distinta por artículo, aunque el contenido sea idéntico. La deduplicación pasa a hacerse por "proveedor + hash" (contenido), no por ruta.

### Verificación
`node --check` en `exportZipController.js`, limpio. Prueba con datos simulados calcados del caso real de Víctor (44 filas del mismo proveedor, mismo hash, ruta de Storage distinta por artículo, `es_generica = false` como una carga anterior a la migración del 2026-09-01, más una foto propia real de otro artículo con hash distinto): las 44 se detectan como genéricas y colapsan en 1 sola entrada a descargar; la foto propia no se toca.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.51** (frontend sin cambios en esta versión — se sube igual para mantener sincronizados los dos `package.json`). Otros documentos revisados en esta entrega: `HISTORIAL.md` (actualizado); `backend/README.md`, `frontend/README.md`, `README.md`, `backend/.env.example`, `DEPLOY.md` — revisados, no aplica ningún cambio (mismo endpoint, sin variables de entorno nuevas ni migración de base de datos nueva).

## [1.19.50] - 2026-09-05

### Cambiado
- **"Exportar documentación" nombra ahora cada archivo como "código de proveedor_nombre del artículo"** — a petición de Víctor. Hasta ahora cada ficha técnica, ficha de seguridad e imagen se nombraba solo con el código de proveedor (`SIN-CODIGO-DALI-<código dali>` si todavía no estaba grabado); `exportarDocumentacionZip()` (`exportZipController.js`) ahora añade también el nombre del artículo en DALI al nombre de archivo (`nombre_articulo`, añadido al `select()` de las consultas de `fichas`/`imagenes`), pasado por el mismo `nombreSeguro()` que ya limpiaba el nombre de proveedor.
- **La imagen genérica "SIN IMAGEN" de un proveedor ya no se descarga ni se empaqueta una vez por cada artículo que la tenga asignada** — mismo motivo, misma entrega: al ser la misma fila física de Storage repetida en todos los artículos de un proveedor sin foto propia (`imagenes.es_generica = true`, ver migración `2026-09-01_es_generica_imagen.sql`), incluirla por artículo era descargar y comprimir el mismo archivo decenas de veces. Ahora se detecta (`es_generica` añadido al `select()` de `imagenes`), se deduplica por proveedor + ruta de Storage y se descarga/empaqueta UNA sola vez por proveedor, como `IMAGENES/SIN IMAGEN.ext` — sin el prefijo de código/artículo, porque no pertenece a ninguno en concreto. Las imágenes propias del artículo siguen su descarga individual de siempre, ya con el nuevo nombre.

### Verificación
`node --check` en `exportZipController.js`, limpio. Revisado a mano el recorrido de `entradas`/`entradasGenericas` para los casos límite ya documentados en el propio fichero: dos artículos del mismo proveedor compartiendo código de proveedor (`nombreUnico` sigue añadiendo " (2)", " (3)"... dentro de la misma carpeta), artículo sin código de proveedor grabado (prefijo `SIN-CODIGO-DALI-<código dali>` se mantiene, ahora seguido del nombre del artículo) y proveedor con imagen genérica asignada a varios artículos a la vez (una sola descarga y una sola entrada en el zip, deduplicada antes de tocar Storage).

Versión: `backend/package.json` y `frontend/package.json` → **1.19.50** (frontend sin cambios de lógica en esta versión — solo el texto descriptivo de `AdminExportarZip.jsx`, se sube igual para mantener sincronizados los dos `package.json`). Otros documentos de mantenimiento revisados en esta entrega: `HISTORIAL.md` (actualizado); `backend/README.md` (actualizado — fila de `/admin/documentacion-zip` con el nuevo criterio de nombrado); `frontend/README.md` (actualizado — descripción de "Exportar documentación"); `README.md`, `backend/.env.example`, `DEPLOY.md` — revisados, no aplica ningún cambio (no hay ninguna variable de entorno nueva, ningún endpoint nuevo, ninguna migración de base de datos — `es_generica` ya existía — ni ningún paso de despliegue adicional).

## [1.19.49] - 2026-09-03

### Corregido
- **"Catálogo Asignaciones - SAP" se partía en dos líneas en la barra lateral**, con "- SAP" cayendo suelto en su propia línea — a raíz del renombrado de la entrega anterior (v1.19.48): "Asignaciones" es más largo que "DALI", y en los 219px de ancho de la marca del sidebar ya no cabía todo en una línea, a diferencia del login (mucho más ancho). Víctor lo señaló comparando las dos pantallas: "me gusta mas como esta en el login". `Sidebar.jsx` ahora enseña solo "Catálogo Asignaciones" (sin el "- SAP" final), igual de limpio que el título del login, y mantiene igual el subtítulo "Índice de artículos" debajo. Solo texto — sin tocar CSS ni la lógica de navegación.

### Verificación
`npx vite build`, limpio. Comprobado visualmente por captura (Playwright, cuenta 'admin' en modo demo): la marca del sidebar ya no salta de línea. `e2e-sidebar-admin.mjs` (14 aserciones) — todo OK, sin ningún error de JS.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.49** (backend sin cambios en esta versión — se sube igual para mantener sincronizados los dos `package.json`). Otros documentos de mantenimiento revisados en esta entrega: `HISTORIAL.md` (actualizado); `backend/README.md`, `frontend/README.md`, `README.md`, `backend/.env.example`, `DEPLOY.md` — revisados, no aplica ningún cambio (ajuste puramente visual de un texto, sin tocar ningún endpoint, variable de entorno ni paso de despliegue).

## [1.19.48] - 2026-09-03

### Cambiado
- **Renombrado "Catálogo DALI" → "Catálogo Asignaciones" y "Central de Compras Canarias" → "Central de Compras Princess Canarias" en todos los correos y en las pantallas de acceso** — a petición de Víctor: "cambia todas las cabeceras de los correos? No es Catálogo DALI --> Catálogo Asignaciones, no es Central de Compras Canarias --> Central de Compras Princess Canarias; revisa pantalla Login, esto lo cambiamos hace unas cuantas actualizaciones". La pantalla de login (`LoginScreen.jsx`) ya decía "Catálogo Asignaciones" desde hace tiempo, pero el cambio nunca llegó a los correos ni al resto de pantallas de la misma familia. Actualizado: cabecera (logo + título + subtítulo), asunto y cuerpo de los tres correos que genera la aplicación (`backend/src/utils/emailHtml.js`, `backend/src/controllers/authController.js`) — enlace de acceso de un solo uso (recuperación y bienvenida) y aviso a administradores de una solicitud de acceso nueva; firma de los correos de reclamación de documentación a proveedores (`EmailProveedorModal.jsx`: "Dpto. Central de Compras Princess Canarias"); la pantalla de "Elige tu contraseña" que abre el propio enlace del correo (`CanjearTokenAcceso.jsx`, la otra mitad de la familia de pantallas de acceso junto al login, que se había quedado sin actualizar); y, por la misma inconsistencia, la marca de la barra lateral una vez dentro de la aplicación (`Sidebar.jsx`: "Catálogo DALI - SAP" → "Catálogo Asignaciones - SAP") y la descripción de las cuentas EmailJS en Configuración (`AdminConfiguracionEmailjs.jsx`). Los asuntos simulados en modo demo (`services/api.js`) también se actualizaron, para que no se vea texto antiguo ni siquiera en las pruebas. No cambia ningún endpoint, variable de entorno, plantilla de EmailJS ni la cola de `control-pedidos-princess` — es un cambio de texto puro, no de mecanismo de envío.

### Verificación
`npx vite build`, limpio. `node --check` en todo `backend/src/`, limpio. `tokenaccesotest/verify.mjs` (85 aserciones, incluida la del asunto del aviso de solicitud de acceso, actualizada al nuevo texto) y `tokenaccesotest/verify-permisos.mjs` (33) — todo OK; los ficheros de ese harness que son copia de `authController.js`/`emailHtml.js` se han vuelto a sincronizar con los reales. Regresión completa E2E: `e2e-login-seguridad.mjs` (17), `e2e-token-acceso.mjs` (22), `e2e-sidebar-admin.mjs` (14), `e2e-permisos-admin.mjs` (16), `e2e-traspasar-principal.mjs` (10), `e2e-seleccion-catalogo.mjs` (25), `e2e-imprimir.mjs` (9), `e2e-export-demo-alert.mjs` (3), `e2e-usuarioform.mjs`, `e2e-descarga-export.mjs` (5), `e2e-descarga-admin-docs.mjs` (8) y `e2e-aviso-version-por-rol.mjs` (8, contra el sitio ya compilado con `vite preview`) — todo OK, sin ningún error de JS nuevo. Ninguno de estos tests hardcodeaba el texto antiguo salvo la aserción ya corregida arriba.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.48**. Otros documentos de mantenimiento revisados en esta entrega: `HISTORIAL.md` (actualizado); `README.md` — revisado; su título ("Catálogo DALI — Consulta de Artículos/Materiales") sigue usando el nombre antiguo a propósito, sin tocarlo — es la documentación interna del propio repositorio (para quien desarrolla, no para quien usa la app), igual que el nombre del repositorio en sí (`dali-sap-articulos-app`); si Víctor quiere que también cambien, que lo pida aparte, ya que afecta a la identidad del propio proyecto, no solo a un texto en pantalla; `backend/README.md`, `frontend/README.md`, `backend/.env.example`, `DEPLOY.md` — revisados, no aplica ningún cambio (no hay ninguna variable de entorno nueva, ningún endpoint nuevo ni ningún paso de despliegue adicional; los nombres de las plantillas HTML documentadas ahí no cambian, solo su contenido de texto).

## [1.19.47] - 2026-09-03

### Corregido
- **"Exportar Excel" en "Documentación faltante" y "Descargar zip" en "Exportar documentación" dejaban la pantalla en negro** — a petición de Víctor: "EL BOTON EXPORTAR EXCEL DEJA LA PANTALLA EN NEGRO, REPARAR COMO LOS DE LA INTERFAZ PRINCIPAL DE ARTICULOS ; PASA LO MISMO EN EXPORTAR DOCUMENTACION". Misma causa ya arreglada en v1.19.x para el catálogo principal: los dos botones navegaban directamente a la URL del backend con `window.open(url, "_blank")`, dejando una pestaña nueva en negro/blanco sin ninguna señal de progreso mientras el fichero se generaba (con "Exportar documentación" sin filtrar por proveedor, hasta varios minutos). `AdminDocumentacionFaltante.jsx` y `AdminExportarZip.jsx` ahora reutilizan el mismo `descargarDesdeUrl()` (fetch + blob + `<a download>`) ya probado en `App.jsx`: botón con spinner y texto "Generando…" mientras dura, deshabilitado para evitar una segunda descarga a la vez, y un aviso (`alert-warn`) si el backend responde con error — sin salir nunca de la pantalla actual. El aviso de modo demo ("no está disponible en modo demo") se mantiene exactamente igual que antes en los dos sitios. El `fetch` del navegador no impone ningún timeout propio, así que la descarga de "todos los proveedores" (varios minutos) no se ve afectada por este cambio — el backend ya desactiva su propio timeout para ese caso (`exportZipController.js`).

### Cambiado
- **"Documentación faltante" carga algo más rápido** — a raíz de la misma pregunta de Víctor ("¿SERA PORQUE NO TIENE PAGINACION COMO EL RESTO?"): esta pantalla es un informe agregado sobre TODO el catálogo activo agrupado por proveedor (no un listado artículo a artículo), así que paginarla como el resto del catálogo no encaja con lo que necesita mostrar (totales y grupos completos). Lo que sí se ha podido acortar es el tiempo de red: `documentacionController.js` pedía a Supabase, una detrás de otra, las imágenes, las fichas y los códigos de proveedor de los artículos activos — como las tres consultas son independientes entre sí, ahora se piden las tres a la vez (`Promise.all`) en vez de en serie, así que el tiempo total pasa a ser aproximadamente el de la más lenta de las tres en vez de la suma de las tres. Mismo resultado exacto, solo más rápido.

### Verificación
`npx vite build`, limpio. `node --check` en todos los ficheros de `backend/src/`, limpio. Nuevo `e2e-descarga-admin-docs.mjs` (Playwright): 8 aserciones, en dos partes — (1) contra el servidor demo (puerto 5183): el aviso de modo demo sigue apareciendo igual en los dos botones nuevos y ninguno de los dos se queda bloqueado en "Generando…" tras el aviso; (2) contra un arnés temporal (`test-descarga.html`, borrado antes de empaquetar esta entrega, mismo patrón que ya usaba `e2e-descarga-export.mjs`) y una extensión de `mock-export-server.mjs` con los dos endpoints nuevos: el nombre de fichero real se lee correctamente de `Content-Disposition` en los tres casos (Excel de documentación faltante, zip de un proveedor concreto, zip de "todos los proveedores" con más retardo simulado) y no aparece ningún error de JS sin capturar. Regresión completa sobre el resto de la aplicación: `e2e-descarga-export.mjs` (5), `e2e-export-demo-alert.mjs` (3), `e2e-imprimir.mjs` (9), `e2e-login-seguridad.mjs` (17), `e2e-permisos-admin.mjs` (15), `e2e-seleccion-catalogo.mjs` (24), `e2e-sidebar-admin.mjs` (13), `e2e-token-acceso.mjs` (22), `e2e-traspasar-principal.mjs` (10), `e2e-usuarioform.mjs` y `e2e-aviso-version-por-rol.mjs` (8, contra el sitio ya compilado con `vite preview`) — todo OK, sin ningún error de JS nuevo.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.47**. Otros documentos de mantenimiento revisados en esta entrega: `HISTORIAL.md` (actualizado); `backend/README.md` (actualizado — nota sobre la paralelización de las tres consultas en "Documentación faltante"); `frontend/README.md` (actualizado — las dos pantallas de administración de documentación ya no usan `window.open` para exportar); `README.md`, `backend/.env.example`, `DEPLOY.md` — revisados, no aplica ningún cambio (no hay ninguna variable de entorno nueva, ningún endpoint nuevo ni ningún paso de despliegue adicional).

## [1.19.46] - 2026-09-03

### Cambiado
- **El aviso de "nueva versión disponible" ya no enseña las notas de la versión a todo el mundo** — a petición de Víctor: "el exceso de información aturde al usuario, vamos a limitar la pantalla de recarga de actualización, solo mensaje de nueva actualización (para forzar la misma) con un título resumen pero sin entrar en detalles para no aburrir, solo mostrar todo a los administradores". `ComprobadorNuevaVersion.jsx` sigue comprobando la versión publicada en segundo plano y sigue forzando la recarga igual que antes (botón "Recargar ahora" o cuenta atrás de 5 minutos), pero el bloque de notas (`CHANGELOG.md`, categorías Añadido/Cambiado/Arreglado/Eliminado) ahora solo se pide y se muestra si, en el momento de detectar la versión nueva, hay una sesión de administrador activa (`fetchSesionActual()`, la misma función que ya usa `App.jsx`). Cualquier otra persona — incluida cualquiera sin sesión todavía, como en la propia pantalla de login — ve solo el mensaje resumen: cabecera, botón de recargar y cuenta atrás, sin detalle técnico de cada entrega.

### Verificación
`npx vite build`, limpio. Nuevo `e2e-aviso-version-por-rol.mjs` (Playwright, contra el sitio ya compilado con `vite preview` — las notas de la versión solo existen en `dist/CHANGELOG.md` tras un build real): 8 aserciones — sin sesión, con la cuenta 'hotel' y con la cuenta 'admin'. Sin sesión y con 'hotel' el aviso no lleva ningún bloque de notas, solo el resumen; con 'admin' sigue apareciendo el bloque completo con los bloques de versiones reales del changelog. Regresión completa sobre el resto de la aplicación: `tokenaccesotest/verify.mjs` (85 aserciones), `tokenaccesotest/verify-permisos.mjs` (33), `e2e-permisos-admin.mjs` (15), `e2e-sidebar-admin.mjs` (13), `e2e-token-acceso.mjs` (22), `e2e-imprimir.mjs` (9), `e2e-traspasar-principal.mjs` (10), `e2e-export-demo-alert.mjs` (3), `e2e-seleccion-catalogo.mjs` (24) y `e2e-login-seguridad.mjs` (17) — todo OK, sin ningún error de JS nuevo.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.46** (backend sin cambios en esta versión — se sube igual para mantener sincronizados los dos `package.json`). Otros documentos de mantenimiento revisados en esta entrega: `HISTORIAL.md` (actualizado); `frontend/README.md` (actualizado — nueva viñeta documentando el aviso de nueva versión, que hasta ahora no estaba recogido ahí); `backend/README.md`, `README.md`, `backend/.env.example`, `DEPLOY.md` — revisados, no aplica ningún cambio (cambio puramente de frontend, sin tocar ningún endpoint, variable de entorno ni paso de despliegue).

## [1.19.45] - 2026-09-03

### Añadido
- **Selección manual de artículos en el catálogo, a través de búsquedas distintas** — a petición de Víctor: "en muchas ocasiones tengo que marcar varios códigos distintos para verlos todos a la vez sin depender de los filtros actuales". Propuso una casilla justo antes del código DALI en cada fila (modo administrador) y un botón "Marcar todo/Desmarcar todo" antes del buscador. Se le preguntó también si el sentido de la selección era solo "verlos juntos en pantalla" o también "poder exportarlos/imprimirlos aparte" — eligió lo segundo (marcado en su propia pregunta de vuelta: "el resultado buscado seria... justamente el indicado en el punto 2"), lo que exigió una nueva vía de filtrado en el backend, ya que `Exportar Excel/PDF/Imprimir` no operaban sobre lo mostrado en pantalla sino que volvían a pedir los datos al backend con los 4 filtros de siempre (q/naturaleza/familia/subfamilia), incapaces de expresar "estos códigos concretos de búsquedas distintas". Confirmó además que "Marcar todo" debía cubrir TODO lo que coincide con la búsqueda activa aunque ocupe varias páginas, y que la selección no hace falta que sobreviva a una recarga de página (más simple, en memoria). Nueva casilla en `ArticuloTable.jsx` (primera columna, con `stopPropagation` para no abrir también la ficha del artículo); estado `marcados` en `App.jsx` (`Map` código→artículo completo, para no tener que volver a pedir nada al mostrar "Ver solo marcados"); botón "Marcar todo/Desmarcar todo"; barra de selección (contador, "Ver solo marcados", "Vaciar selección"). Con "Ver solo marcados" activo, `Exportar Excel`/`Exportar PDF`/`Imprimir` operan sobre exactamente los artículos marcados. Backend: `GET /export/excel` y `GET /export/pdf` (`backend/src/controllers/exportController.js`) aceptan un nuevo parámetro `codigos` (lista de `codigo_dali` separados por comas) — cuando llega, ignora por completo `q`/`naturaleza`/`familia`/`subfamilia`/`todos` y exporta EXACTAMENTE esos códigos, estén activos o no (si se marcaron a mano es porque ya se vieron y se quisieron ahí). Reservado a cualquier administrador: una petición con `codigos` sin sesión de administrador recibe `403` antes de tocar la base de datos, para que nadie sin sesión pueda usar `?codigos=` como atajo para leer artículos desactivados.

### Verificación
`npx vite build`, limpio. Nuevo harness `exporttest/` (doble de Supabase a medida para `exportController.js`, con `.in()`/`.range()`/embebidos sin `!inner`) con `verify-export-codigos.mjs`: 14 aserciones — la rama `codigos` devuelve exactamente los códigos pedidos incluyendo uno DESACTIVADO, ignora por completo el resto de filtros aunque lleguen contradictorios junto a `codigos`, descarta valores no enteros/negativos/cero sin fallar, enriquece `codigo_proveedor` igual que la rama normal, y la rama sin `codigos` sigue funcionando exactamente igual que antes (regresión). El 403 para no-administrador se prueba aparte. Nuevo `e2e-seleccion-catalogo.mjs` (Playwright, modo demo): 24 aserciones — la columna de checkbox y toda la selección están ausentes para una cuenta 'hotel'; marcar un artículo de una búsqueda y luego otro de una búsqueda completamente distinta deja los dos marcados a la vez; "Marcar todo" cubre los 3 artículos de la búsqueda activa y se suma a lo ya marcado antes; "Desmarcar todo" solo quita los de la búsqueda activa, no la selección entera; "Ver solo marcados" pinta exactamente el conjunto marcado sin paginación; exportar con la selección activa en modo demo sigue mostrando el mismo aviso de siempre sin quedarse colgado; "Vaciar selección" borra todo y apaga "Ver solo marcados" sola. Regresión completa: `tokenaccesotest/verify.mjs` (85 aserciones), `tokenaccesotest/verify-permisos.mjs` (33), `e2e-permisos-admin.mjs` (15), `e2e-sidebar-admin.mjs` (13), `e2e-token-acceso.mjs` (22), `e2e-imprimir.mjs` (9), `e2e-traspasar-principal.mjs` (10), `e2e-export-demo-alert.mjs` (3) — todo OK.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.45**. Otros documentos de mantenimiento revisados en esta entrega: `HISTORIAL.md` (actualizado); `backend/README.md` (actualizado — fila de endpoints y nueva sección "Exportación" documentando `codigos`); `frontend/README.md` (actualizado — nueva viñeta sobre la selección manual en "Qué incluye"); `README.md`, `backend/.env.example`, `DEPLOY.md` — revisados, no aplica ningún cambio (no hay ninguna variable de entorno nueva, ninguna migración de base de datos ni ningún paso de despliegue adicional — la funcionalidad reutiliza por completo las tablas y el cliente de Supabase ya existentes).

## [1.19.44] - 2026-09-03

### Añadido
- **El administrador principal ya puede traspasar su puesto a otro administrador desde la propia app** — a petición de Víctor, justo después de probar los permisos granulares recién entregados: "es muy complicado que el administrador principal pueda dar este rol a otro administrador?". Se le plantearon dos formas de resolverlo (varios administradores principales a la vez, o traspasar el puesto uno a otro sin que puedan coexistir dos) y eligió la segunda — sigue habiendo siempre exactamente un administrador principal, ahora transferible sin tocar Supabase a mano. Nuevo endpoint `POST /admin/usuarios/:id/traspasar-principal` (`backend/src/controllers/usuariosController.js`, `traspasarAdminPrincipal`): concede el puesto al destino y se lo retira a quien llama en la misma operación (por ese orden — si algo falla a mitad de camino, el peor caso es acabar con DOS principales, recuperable a mano, nunca CERO); solo lo puede usar quien YA es principal, y el destino tiene que ser una cuenta admin ya activa. Nuevo botón "Nombrar administrador principal" en `UsuarioForm.jsx`, con su propio diálogo de confirmación, visible al editar cualquier OTRO administrador activo que todavía no lo sea. Tras un traspaso con éxito, `AdminUsuarios.jsx` cierra la sesión de quien lo hizo de inmediato — como la sesión viaja en la cookie firmada, el cambio no se notaría hasta el siguiente inicio de sesión (misma limitación ya documentada para rol/permisos), y forzar el cierre evita quedarse viendo controles de "administrador principal" que ya no corresponden.

### Verificación
`npm run build` (Vite), limpio. 10 aserciones nuevas en `tokenaccesotest/verify-permisos.mjs` (23 → 33 en total): un admin normal no puede traspasar el puesto (403), no se puede traspasar a uno mismo, ni a una cuenta 'hotel', ni a un admin desactivado, y el caso de éxito confirma que el destino queda como principal, que quien lo traspasa deja de serlo, y una regresión dedicada — sigue habiendo exactamente un administrador principal, nunca cero ni dos. Nuevo `e2e-traspasar-principal.mjs` (Playwright, modo demo): 10 aserciones — el botón aparece solo donde debe (otro admin activo, no yo mismo, no ya principal), el diálogo de confirmación menciona el nombre del destino y avisa del cierre de sesión, tras confirmar la sesión se cierra sola y vuelve al login, y al volver a entrar la cuenta destino aparece con la insignia Principal y ya no muestra ni la checklist de permisos ni el propio botón de traspaso (en su lugar, el aviso de acceso total). Regresión completa: `tokenaccesotest/verify.mjs` (85 aserciones), `e2e-permisos-admin.mjs` (15), `e2e-sidebar-admin.mjs` (13), `e2e-token-acceso.mjs` (22) y `e2e-imprimir.mjs` (9) — todo OK.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.44**. Otros documentos de mantenimiento revisados en esta entrega: `HISTORIAL.md` (actualizado); `backend/README.md` (actualizado — nueva fila en la tabla de endpoints y párrafo "Traspaso del puesto" en la sección "Autenticación"); `frontend/README.md` (actualizado — nota sobre el nuevo botón en la pantalla de Usuarios); `README.md`, `backend/.env.example`, `DEPLOY.md` — revisados, no aplica ningún cambio (no hay ninguna variable de entorno nueva ni ningún paso de despliegue adicional; no hace falta ninguna migración de base de datos para esta entrega, las dos columnas ya existían desde v1.19.43).

## [1.19.43] - 2026-09-03

### Añadido
- **Permisos granulares de administrador, apartado a apartado** — a petición de Víctor ("YO COMO ADMINISTRADOR PRINCIPAL TENGA LA POTESTAD DE INCLUIR ACCESO A LOS DIFERENTES PUNTOS ... INCLUIDOS LOS DEMAS ADMINISTRADORES"). Hasta ahora, `rol = 'admin'` daba acceso a los 8 destinos de "Gestión" sin distinción. Ahora hay exactamente un **administrador principal** (`usuarios.es_admin_principal`, uno solo, fijado a mano en Supabase — nunca desde la app) con acceso incondicional a todo, y el resto de administradores tienen una columna `usuarios.permisos text[]` con el subconjunto de los 8 apartados que se les haya concedido (Artículos, Importar Excel, Documentación faltante, Fusionar proveedores, Exportar documentación, Usuarios, Solicitudes de acceso, Configuración EmailJS). Solo el principal puede: dar de alta un admin nuevo, cambiar el rol de cualquiera, cambiar los permisos de otro admin, o activar/desactivar/eliminar la cuenta de otro admin — un admin normal con permiso "Usuarios" conserva gestión completa de cuentas `hotel` y mantenimiento básico (nombre/email/contraseña) de otras cuentas admin. Nueva sección "Acceso a Gestión" en `UsuarioForm.jsx` (checklist agrupada en los mismos 4 subgrupos del sidebar) visible solo para el principal al editar un admin; el sidebar y la vista actual ocultan cualquier apartado no concedido, con la misma insignia "(acceso limitado)" junto al título "Gestión" cuando aplica. Backend: `backend/src/middleware/auth.js` (`requierePermiso()`), `backend/src/controllers/usuariosController.js` (guardas de privilegio en alta/edición/baja), `backend/src/routes/admin.js` (cada ruta de `/admin/*` exige su clave), `backend/src/controllers/authController.js` (la sesión incluye `esAdminPrincipal`/`permisos` en login, SSO y canje de token de acceso). Nueva migración `database/migraciones/2026-09-03_permisos_admin.sql` — el `DEFAULT` de `permisos` es el array completo de las 8 claves, así que todos los administradores existentes conservan acceso a todo el día del cambio (decisión de Víctor); Víctor restringe a quien haga falta después, uno a uno. Como toda la sesión viaja en la cookie firmada, un cambio de permisos (o de administrador principal) no tiene efecto hasta el siguiente inicio de sesión de esa persona — misma limitación que ya existía para los cambios de rol.

### Corregido
- **Modo demo: dar de alta un administrador nuevo dejaba el toggle de "Rol" deshabilitado**, con la pista incorrecta "No puedes cambiarte el rol a ti mismo" — efecto colateral de la nueva guarda `rolBloqueado`: `esUnoMismo` se calculaba como `editando?.id === sesion?.id`, y en modo demo la sesión no lleva `id` (no existe una cuenta real detrás), así que un alta nueva (`editando = {}`, tampoco con `id`) coincidía por accidente (`undefined === undefined`). Solo pasaba en modo demo — en producción `sesion.id` es siempre un UUID real, nunca `undefined`. `frontend/src/components/admin/AdminUsuarios.jsx`: `esUnoMismo` ahora exige además que el usuario que se está editando tenga ya un `id`.

### Verificación
`npm run build` (Vite), limpio. Nuevo `tokenaccesotest/verify-permisos.mjs`: 23 aserciones contra el doble de Supabase — cubre `requierePermiso()` y las guardas de privilegio de `crearUsuario`/`actualizarUsuario`/`eliminarUsuario` (un admin normal no puede ascender a nadie a admin, ni autoampliarse permisos, ni tocar rol/activo/permisos de otro admin, ni eliminarlo; sí puede gestionar cuentas `hotel` sin restricción y hacer mantenimiento básico de otro admin; el principal puede todo). Nuevo `e2e-permisos-admin.mjs` (Playwright, modo demo): 15 aserciones — checklist de permisos agrupada en los 4 subtítulos con las 8 casillas marcadas por defecto en un alta, lo marcado se guarda y se lee bien al reabrir en edición, la checklist desaparece si el rol pasa a "Hotel", la insignia "Principal" no aparece en una cuenta normal, y el pie del sidebar dice "Administrador principal" para la cuenta de demo. Regresión completa: `tokenaccesotest/verify.mjs` (85 aserciones, incluye `authController.js` re-sincronizado con los cambios de sesión), `e2e-sidebar-admin.mjs` (13), `e2e-token-acceso.mjs` (22) y `e2e-imprimir.mjs` (9) — todo OK, confirmando que las nuevas guardas no rompen nada de lo ya entregado.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.43**. Otros documentos de mantenimiento revisados en esta entrega: `HISTORIAL.md` (actualizado); `backend/README.md` (actualizado — tabla de endpoints y sección "Autenticación", con el nuevo modelo de permisos); `frontend/README.md` (actualizado — nota sobre visibilidad por permisos y la nueva checklist en la pantalla de Usuarios); `README.md`, `backend/.env.example`, `DEPLOY.md` — revisados, no aplica ningún cambio (no hay ninguna variable de entorno nueva; el paso de despliegue sigue siendo aplicar la migración pendiente en Supabase, ya cubierto por el procedimiento habitual).

**Importante para el despliegue**: antes de subir este backend hay que ejecutar a mano en Supabase la migración `database/migraciones/2026-09-03_permisos_admin.sql`, y luego el `UPDATE` (comentado dentro del propio fichero) que marca la cuenta de Víctor como administrador principal con su email real — sin ese `UPDATE`, nadie podría gestionar permisos de administrador desde la app hasta hacerlo a mano.

## [1.19.42] - 2026-09-03

### Cambiado
- **El apartado "Gestión" del sidebar se reorganiza en subgrupos** — a petición de Víctor ("esta todo muy liado"): los 8 destinos de administración, añadidos uno a uno con el tiempo sin ningún criterio de agrupación, se leían como una lista plana. Ahora aparecen bajo 4 subtítulos dentro de "Gestión": **Catálogo** (Artículos, Importar Excel), **Proveedores y documentación** (Documentación faltante, Fusionar proveedores, Exportar documentación), **Accesos** (Usuarios, Solicitudes de acceso) y **Sistema** (Configuración EmailJS). Elegido entre 3 alternativas (subgrupos visibles / subgrupos plegables / solo reordenar) tras consultar con Víctor. Ningún destino ni comportamiento cambia — mismos `vista`/`onNavigate` de siempre, solo el orden y el agrupado visual. `frontend/src/components/Sidebar.jsx`, `frontend/src/styles/index.css` (`.sidebar-subdivider`, nuevo).

### Corregido
- **Fallo latente de maquetación en TODA la barra lateral**: un `<button>` es `inline-block` por defecto, así que sin `width: 100%` cada pestaña del sidebar solo ocupaba el ancho de su propio texto — invisible hasta ahora porque cada botón vivía solo en su fila (naturalezas) o tenía texto largo de sobra para ocupar la línea entera él solo (los 8 de "Gestión", en su antiguo orden). Al reorganizar "Gestión" en subgrupos, dos textos cortos como "Artículos" e "Importar Excel" quedaron por primera vez como hermanos directos y se empaquetaron en la misma línea en vez de una cada uno — sacando a la luz el problema de fondo. `.tab { display: block; width: 100%; }` en `frontend/src/styles/index.css` lo corrige para todos los usos de `.tab` (catálogo y Gestión), no solo para el caso que lo hizo visible.

### Verificación
`npm run build` (Vite), limpio. Nuevo `e2e-sidebar-admin.mjs` (Playwright, modo demo): 13 aserciones — los 4 subtítulos son visibles, los 8 botones siguen llevando cada uno a su vista correcta, y una regresión dedicada al fallo de maquetación (los 8 botones ocupan el 100% del ancho de su contenedor, ninguno se empaqueta junto a otro). Regresión completa: `tokenaccesotest/verify.mjs` (85 aserciones), `e2e-token-acceso.mjs` (22 aserciones) y `e2e-imprimir.mjs` (9 aserciones) — todo OK, confirmando que el cambio de `.tab` no rompe nada en el resto de la barra lateral ni en el listado impreso. Comprobación visual con una captura de pantalla real del sidebar reorganizado.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.42**. Otros documentos de mantenimiento revisados en esta entrega: `HISTORIAL.md` (actualizado); `frontend/README.md` (actualizado — nota añadida sobre el nuevo agrupado, ver arriba); `README.md`, `backend/README.md`, `backend/.env.example`, `DEPLOY.md` — revisados, no aplica ningún cambio (no hay ninguna variable de entorno ni endpoint nuevo, es un reordenado visual del sidebar).

## [1.19.41] - 2026-09-03

### Cambiado
- **"Exportar Excel" y "Exportar PDF" ya no abren una pestaña nueva en negro/blanco mientras se genera el fichero** — a petición de Víctor ("se queda un rato en pantalla negra hasta que lo consigue descargar... que se vea que se está descargando el archivo"). Antes, `window.open(url, "_blank")` navegaba directamente a la URL del backend: con ficheros grandes, esa pestaña se quedaba en blanco/negro sin ninguna señal hasta que el navegador terminaba de descargar. Ahora la descarga se hace por `fetch()` sin salir nunca de la aplicación (`descargarDesdeUrl()` en `frontend/src/services/api.js`, llamada desde `descargarExport()` en `App.jsx`): se pide el fichero, se lee como `Blob`, se dispara la descarga real del navegador con un `<a download>` temporal, y mientras tanto el botón pulsado se deshabilita y muestra un círculo girando + "Generando…" (mismo patrón que ya tenía "Imprimir" con "Preparando…", que de paso también estrena el mismo spinner). El nombre del fichero descargado se lee de la cabecera `Content-Disposition` que ya mandaba el backend, con el mismo nombre calculado como respaldo si por lo que sea no llegara a leerse.
- **CORS del backend ahora expone `Content-Disposition`** (`backend/src/server.js`, `exposedHeaders: ["Content-Disposition"]`) — necesario para lo anterior: por defecto, un `fetch()` entre orígenes distintos (frontend y backend viven en dominios distintos en producción) no puede leer esa cabecera por JS aunque el servidor la mande, a menos que el servidor la declare explícitamente. Sin este cambio, el nombre real del fichero no habría llegado nunca al navegador (se habría visto igual de bien porque el frontend calcula el mismo nombre por su cuenta como respaldo, pero más por casualidad que por diseño).
- Nuevo estilo `.spinner` + `@keyframes girar` en `frontend/src/styles/index.css`, y `.btn:disabled` genérico (antes solo existía para `.btn-primary`; `.btn-ghost`, que es el estilo de estos tres botones, se quedaba sin ninguna señal visual de estar desactivado).

### Verificación
`npm run build` (Vite), limpio. Nuevo `e2e-descarga-export.mjs` (Playwright) contra un servidor de pruebas propio que imita `/export/pdf`/`/export/excel` con `Content-Disposition` real y CORS con `exposedHeaders` (igual que el backend real tras este cambio): 5 aserciones — el nombre de fichero real se lee correctamente de la cabecera (para PDF y Excel), el blob descargado tiene contenido, y un mensaje de error del backend (500) se propaga tal cual al usuario en vez de un genérico. Nuevo `e2e-export-demo-alert.mjs`: 3 aserciones de regresión — en modo demo (sin backend real) los botones siguen mostrando el mismo aviso de siempre y no se quedan bloqueados en "Generando…". Regresión completa: `tokenaccesotest/verify.mjs` (85 aserciones), `e2e-token-acceso.mjs` (22 aserciones) y `e2e-imprimir.mjs` (9 aserciones) — todo OK. Comprobación visual con una captura de pantalla del spinner en marcha sobre el botón "Imprimir" (mismo componente visual que usarán "Exportar Excel/PDF").

Versión: `backend/package.json` y `frontend/package.json` → **1.19.41**. Otros documentos de mantenimiento revisados en esta entrega: `HISTORIAL.md` (actualizado); `README.md`, `backend/README.md`, `frontend/README.md`, `backend/.env.example`, `DEPLOY.md` — revisados, no aplica ningún cambio (la variable `CORS_ORIGIN` que documentan no se ve afectada; `exposedHeaders` es una cabecera adicional fija en el código, no una nueva variable de entorno que configurar).

## [1.19.40] - 2026-09-03

### Añadido
- **El listado de "Imprimir" del catálogo sale más organizado, con el mismo aspecto que el PDF exportado** — a petición de Víctor. Cabecera de tabla con color (`#e5decb` de fondo, `#3a2f1f` de texto, negrita, mayúsculas), filas separadoras por familia · subfamilia (`#f4efe3`/`#8a6a2f`, negrita) y sombreado alterno en las filas de datos (`#faf7f0`) — los mismos tres colores exactos que ya usa `dibujarCabeceraTabla()`/el bucle principal del PDF real en `backend/src/workers/generarExportWorker.js`, para que impresión y PDF luzcan iguales. Se añade también un subtítulo con fecha y total de artículos ("Generado el ... · N artículo(s)"), igual que la primera página del PDF. El listado se ordena ahora por familia → subfamilia → nombre antes de imprimir (mismo criterio, replicado en el frontend, que el reordenado manual en JS que ya hace `exportController.js` — el `.order()` de Supabase sobre tablas relacionadas no se aplica de verdad ahí, así que tampoco se puede confiar en el orden que ya trae `fetchArticulos`). `frontend/src/App.jsx` (`imprimirListado`, vista de impresión), `frontend/src/styles/index.css` (`@media print`) — incluye `print-color-adjust`/`-webkit-print-color-adjust: exact`, sin lo cual la mayoría de navegadores no imprimen los fondos de color por defecto.

### Verificación
`npm run build` (Vite), limpio. Nuevo `e2e-imprimir.mjs` (Playwright, modo demo, sin abrir el diálogo nativo de impresión — se usa `page.emulateMedia({media:"print"})` sobre la página real tras pulsar "Imprimir"): 9 aserciones — cabecera y filas de grupo con los colores computados exactos del PDF, grupos en orden alfabético, subtítulo con fecha y total, y una regresión dedicada (ningún artículo aparece antes de la primera fila de grupo). Sin errores de consola. Comprobación visual adicional con una captura de pantalla real.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.40**. Otros documentos de mantenimiento revisados en esta entrega: `HISTORIAL.md` (actualizado); `README.md`, `backend/README.md`, `frontend/README.md`, `backend/.env.example`, `DEPLOY.md` — revisados, no aplica ningún cambio.

## [1.19.39] - 2026-09-03

### Cambiado
- **Documentación del keep-alive de Render (`DEPLOY.md`) actualizada al patrón que realmente funciona en producción** — sin cambios de código. Se diagnosticó junto con Víctor un problema real: con el cronjob de `cron-job.org` acotado a horario diurno (`*/8 6-22 * * *`, sin ningún ping entre las 22:00 y las 6:00), el backend tardaba entre 30 y 40 minutos en volver a responder cada mañana tras dormir toda la noche — varios `503` seguidos antes del primer `200 OK`. Revisando los logs de Render se confirmó que el arranque de la propia app es rápido (`npm start` → escuchando en ~9 segundos); el retraso estaba en que la infraestructura del plan Free de Render tarda mucho más en reaccionar tras dormir muchas horas seguidas que el "~1 minuto" que documentan para el caso de 15 minutos de inactividad. Solución aplicada: pinguear cada 12 minutos SIN restricción horaria (`*/12 * * * *`), por debajo del umbral de 15 min de Render — el servicio no vuelve a dormirse nunca. Con `listado-DALI-SAP` como único servicio Free en la cuenta, esto cuesta ~740-744 h/mes, por debajo (con margen ajustado) de las 750 h gratuitas del workspace. `DEPLOY.md` documenta ahora este patrón y el porqué, con una alternativa anotada (horario recortado pero adelantado, p.ej. `*/8 5-22 * * *`) por si en el futuro se añade otro servicio Free a la cuenta y el margen deja de ser seguro.

### Verificación
Cambio de documentación únicamente — nada de código que probar. Pendiente de confirmar por Víctor tras una noche completa con el nuevo cronjob aplicado en cron-job.org (fuera del repo, no requiere ningún deploy).

Versión: `backend/package.json` y `frontend/package.json` → **1.19.39**. Otros documentos de mantenimiento revisados en esta entrega: `HISTORIAL.md` (actualizado); `README.md`, `backend/README.md`, `frontend/README.md`, `backend/.env.example` — revisados, no aplica ningún cambio.

## [1.19.38] - 2026-09-03

### Añadido
- **Logo de Princess Hotels & Resorts también en lo alto del menú lateral** — a petición de Víctor, mismo logo (texto en negro) que ya se puso en el login (v1.19.36), a un ancho menor (130px) para caber cómodo en los 220px del sidebar, alineado a la izquierda igual que el texto de debajo (a diferencia del login, el sidebar no es una tarjeta centrada). `frontend/src/components/Sidebar.jsx`, `frontend/src/styles/index.css` (`.sidebar-brand-logo`).

### Cambiado
- **Título y subtítulo de la pantalla de login** — Víctor los editó directamente en su copia local (`Catálogo DALI` → `Catálogo Asignaciones`, `Libro de registro` → `Códigos DALI - SAP`) y mandó el archivo resultante; se adopta ese cambio como fuente de la verdad para que no se pierda en la próxima entrega. `frontend/src/components/LoginScreen.jsx`.

### Verificación
`npm run build` (Vite), limpio. Backend: 85 aserciones, sin cambios (cambio puramente visual/de texto, sin lógica nueva). End-to-end con Playwright: 22 aserciones, sin cambios en la lista (ninguna dependía del texto de marca). Comprobación visual con capturas de pantalla reales (Playwright, `npm run preview`): login con el título nuevo, y sidebar con el logo bien proporcionado tras iniciar sesión.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.38**. Otros documentos de mantenimiento revisados en esta entrega: `HISTORIAL.md` (actualizado); `README.md`, `backend/README.md`, `frontend/README.md`, `backend/.env.example`, `DEPLOY.md` — revisados, no aplica ningún cambio.

## [1.19.37] - 2026-09-03

### Cambiado
- **Mensaje de "¿Has olvidado tu contraseña?" reescrito para dejar explícito que una solicitud de acceso nueva pasa por revisión de un administrador** — a petición de Víctor: la redacción anterior, para el caso de email no registrado, decía "revisa tu bandeja de entrada en los próximos días", ambiguo y con pinta de correo automático que podía no llegar nunca ("esto no funciona"). Se decidió mantener el mismo mensaje único condicional de siempre (sigue sin nombre obligatorio, sigue sin distinguir a nivel de texto ni de comportamiento si el email está o no registrado — ver v1.16/v1.15), pero con una redacción más completa y profesional que deja claro, para el caso de solicitud nueva, que hay un paso humano de por medio (un administrador revisa y aprueba) y que puede llevar uno o dos días laborables. `backend/src/controllers/authController.js` (`MENSAJE_RECUPERACION`), `frontend/src/services/api.js` (`MENSAJE_RECUPERACION_DEMO`, mantenido idéntico letra a letra al del backend), `frontend/src/components/RecuperarAccesoModal.jsx` (texto de ayuda antes de enviar, mismo criterio).

### Verificación
`node --check` en el backend. Backend: 85 aserciones (sin cambios en la lista, el mensaje no tiene lógica propia que cubrir aparte de las ya existentes). End-to-end con Playwright: 22 aserciones (21 previas + 1 nueva: el mensaje mostrado incluye la frase "un administrador la revisará"). `npm run build` (Vite), limpio. Sin errores de consola.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.37**. Otros documentos de mantenimiento revisados en esta entrega: `HISTORIAL.md` (actualizado); `README.md`, `backend/README.md`, `frontend/README.md`, `backend/.env.example`, `DEPLOY.md` — revisados, no aplica ningún cambio.

## [1.19.36] - 2026-09-03

### Añadido
- **Logo de Princess Hotels & Resorts en la pantalla de login** — a petición de Víctor. Nuevo `frontend/src/assets/princess-logo.png` (versión con el texto en negro, generada a partir del archivo que envió — el original es blanco sobre transparente, pensado para fondo oscuro; aquí se necesitaba lo contrario para el fondo claro de `.login-card`, así que se recolorea el texto conservando la transparencia y el antialiasing del PNG original, sin tocar ni el dibujo ni la forma). Se muestra encima de "Catálogo DALI" en `LoginScreen.jsx`, dentro de `.login-brand`.

### Verificación
`npm run build` (Vite), limpio — el logo se empaqueta como asset con hash. Comprobación visual con una captura de pantalla real (Playwright, `npm run preview`) contra el build de producción: el logo aparece centrado, con buen contraste sobre el fondo claro de la tarjeta de login, sin desbordar ni deformarse.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.36**. Otros documentos de mantenimiento revisados en esta entrega: `HISTORIAL.md` (actualizado); `README.md`, `backend/README.md`, `frontend/README.md`, `backend/.env.example`, `DEPLOY.md` — revisados, no aplica ningún cambio.

## [1.19.35] - 2026-09-03

### Corregido
- **El texto de los botones a ancho completo (p.ej. "Entrar" en el login, "Elegir contraseña" al canjear un enlace de acceso, "Ver alternativas" en la ficha de artículo) salía pegado al borde izquierdo en vez de centrado** — a petición de Víctor tras verlo en la pantalla de login. La clase base `.btn` usaba `display: inline-flex; align-items: center` sin `justify-content`, que solo centra en el eje vertical; en un botón de ancho normal no se notaba (el contenido ya ocupa todo el ancho), pero en cualquier botón forzado a `width: 100%` el texto quedaba a la izquierda. Se añade `justify-content: center` a la clase base `.btn` en `frontend/src/styles/index.css` — corrige los tres botones a la vez, sin ningún efecto visible en el resto (donde ya se veía centrado por no sobrar espacio).

### Verificación
`npm run build` (Vite), limpio. Cambio puramente de CSS, sin lógica que probar con el arnés de backend/E2E.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.35**. Otros documentos de mantenimiento revisados en esta entrega: `HISTORIAL.md` (actualizado); `README.md`, `backend/README.md`, `frontend/README.md`, `backend/.env.example`, `DEPLOY.md` — revisados, no aplica ningún cambio.

## [1.19.34] - 2026-09-03

### Cambiado
- **En "¿Has olvidado tu contraseña?", el campo Nombre deja de ser obligatorio** — a petición de Víctor tras probar el flujo real ("no veo la necesidad de tener la obligacion de nombre y correo para recuperar la contraseña, si no se acuerda del nombre la hemos liado"). Ese nombre nunca se usaba para el caso más común (email ya registrado: el correo saluda con el nombre real ya guardado en la base de datos), así que exigirlo era fricción sin ningún efecto real en ese caso. Solo sigue haciendo falta para que un administrador identifique una solicitud de acceso nueva (email no registrado) — si se deja en blanco, se usa el propio email como nombre de repuesto. El formulario sigue sin poder saber (ni debe saber) de antemano si el email está o no registrado, así que el campo se mantiene siempre visible, ahora marcado "(opcional)"; se reordena además el formulario (Email primero, Nombre después) para reflejar cuál es el campo realmente necesario. `backend/src/controllers/authController.js` (`recuperarAcceso`: ya no exige `nombre`, mensaje de error actualizado a "Indica tu email."), `frontend/src/components/RecuperarAccesoModal.jsx`, `frontend/src/services/api.js` (mismo comportamiento en modo demo).

### Verificación
`node --check` en el fichero de backend tocado. Backend: 85 aserciones en total sobre el arnés de `tokenaccesotest/` (9 nuevas dedicadas a este cambio, en 3 pruebas: recuperación sin nombre para un email registrado no devuelve 400 y genera el token igualmente; solicitud de acceso sin nombre para un email no registrado usa el propio email como nombre de repuesto; sin email sigue devolviendo 400, con el mensaje de error ya actualizado). End-to-end con Playwright: 21 aserciones en total (1 nueva: enviar el formulario sin escribir nada en Nombre no queda bloqueado por la validación del navegador y muestra el mismo mensaje genérico). Sin errores de consola.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.34**. Otros documentos de mantenimiento revisados en esta entrega: `HISTORIAL.md` (actualizado); `README.md`, `backend/README.md`, `frontend/README.md`, `backend/.env.example`, `DEPLOY.md` — revisados, no aplica ningún cambio (ninguno documentaba el campo Nombre como obligatorio).

## [1.19.33] - 2026-09-02

### Añadido
- **DALI pasa a ser autosuficiente para el envío de sus correos de acceso — a petición de Víctor, tras confirmar que compartir el EmailJS de `control-pedidos-princess` arriesgaba desincronizar su contador local y volver a quedarse sin cuota a mitad de mes.** Nuevo EmailJS propio de DALI, 2 cuentas encadenadas "por seguridad" (mismo mecanismo de rotación por umbral que las 4 cuentas de esa otra app, pero con contador y credenciales propios, sin compartir nada — tabla `configuracion_emailjs`, panel nuevo Administración → Configuración EmailJS). El correo se envía SIEMPRE desde el navegador que ya está abierto en el momento de la acción (el del propio solicitante en "¿Has olvidado tu contraseña?", el del admin al aceptar una solicitud) — ya no hace falta que nadie tenga `control-pedidos-princess` abierta para que el correo llegue a enviarse. "Documentación faltante" sigue con el mecanismo anterior por ahora — anotado explícitamente como actualización próxima.
- **Enlaces de acceso de un solo uso en vez de contraseña temporal — a petición de Víctor ("enlace con token de un solo uso"), mismo patrón que ya usa `control-pedidos-princess` en su propio password-reset.** Nueva tabla `tokens_acceso` (caduca en 2h, un único uso). Quien recibe el enlace elige su propia contraseña directamente, sin que exista en ningún momento una contraseña temporal real. Sustituye a `usuarios.debe_cambiar_password`/`CambiarPasswordObligatorio.jsx` (retirado; la columna queda vestigial, no se borra). Nueva pantalla `CanjearTokenAcceso.jsx`, que `App.jsx` muestra al detectar `?token_acceso=` en la URL (mismo criterio que `?dali_token=` para el SSO). Backend: `backend/src/controllers/authController.js` (reescrito: `emitirTokenAcceso`, `validarTokenAcceso`, `canjearTokenAcceso`, retira `cambiarPasswordObligatorio`), `backend/src/controllers/solicitudesAccesoController.js` (reescrito: hash aleatorio inutilizable en vez de contraseña temporal), `backend/src/controllers/configuracionEmailjsController.js` (nuevo), `backend/src/services/emailjsConfig.js` (nuevo), `backend/src/utils/tokenAcceso.js` (nuevo), `backend/src/utils/emailHtml.js`, `backend/src/middleware/auth.js`, `backend/src/routes/auth.js`, `backend/src/routes/admin.js`. Migración nueva `database/migraciones/2026-09-02_tokens_acceso_emailjs.sql` (**aplicar en Supabase antes de desplegar**). Frontend: `frontend/src/components/CanjearTokenAcceso.jsx` (nuevo), `admin/AdminConfiguracionEmailjs.jsx` (nuevo), `services/emailjs.js` (nuevo), `RecuperarAccesoModal.jsx`, `admin/AdminSolicitudesAcceso.jsx`, `LoginScreen.jsx`, `App.jsx`, `Sidebar.jsx`, `services/api.js`, `styles/index.css`. Nueva dependencia `@emailjs/browser` en `frontend/package.json`.
- **Alcance explícitamente fuera de esta entrega, a petición de Víctor:** "Documentación faltante" (aviso a proveedores) sigue usando la cola de `control-pedidos-princess` — anotado como actualización próxima.

### Nota de diseño pendiente de confirmar
Al mover el envío de "¿Has olvidado tu contraseña?" al navegador, ese navegador necesita conocer el destinatario real para pasárselo a EmailJS — inevitable para el propio usuario (su propio email), pero para el aviso a administradores (email no registrado) significa que alguien inspeccionando la pestaña Red de su propio navegador podría distinguir, mirando esa llamada a EmailJS, si su email estaba o no registrado — una merma real, aunque menor, frente al diseño anterior (100% server-side, nunca revelaba esto). Implementado igualmente por ser el diseño más simple y por indicación explícita de avanzar rápido ("creamos la actualización y luego montamos el detalle técnico"); riesgo práctico bajo (aplicación interna, exige inspeccionar DevTools a propósito). Ver el aviso detallado en `authController.js` y en `HISTORIAL.md` v1.15 — a revisar con Víctor al configurar las cuentas EmailJS reales.

### Verificación
`npm run build` (Vite), limpio — las 2 pantallas nuevas se separan en sus propios chunks. `node --check` en los nueve ficheros de backend nuevos/tocados. Backend probado con un doble de Supabase en memoria extendido (`.delete()`, `.is(col, null)`, embebido simple `usuarios!inner(...)` — arnés nuevo en `tokenaccesotest/`, mismo patrón que `recuperaciontest/`: importa los controladores REALES sin modificar, confirmados byte-idénticos a la fuente): 71 aserciones, incluidas 4 de regresión dedicadas (un token ya canjeado no se puede reutilizar; el flag de registro de envío sin sesión se consume tras un solo uso; ya no se devuelve ninguna contraseña temporal al aceptar una solicitud; el hash de la cuenta nueva no es ni vacío ni trivial). Prueba end-to-end real con Playwright contra el frontend real en modo demo: 20 aserciones — mensaje idéntico letra a letra entre email registrado y no registrado, generación de un enlace bien formado al aceptar una solicitud, canje real del enlace verificado llamando al propio módulo `api.js` ya cargado en esa pestaña (con regresión: el mismo token no se puede canjear dos veces), pantalla `CanjearTokenAcceso` ante un enlace inválido (404, aviso, vuelta al login, URL limpiada), y guardado/persistencia de credenciales en Administración → Configuración EmailJS. Sin errores de consola en ningún caso.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.33**. Otros documentos de mantenimiento revisados en esta entrega: `README.md`, `backend/README.md`, `frontend/README.md`, `backend/.env.example` — los cuatro se actualizan (endpoints nuevos, diseño del flujo, credenciales EmailJS ya no van por variable de entorno, pendientes resueltos/anotados). Funcionalidad nueva a petición de Víctor, fuera de la auditoría full ya cerrada en v1.19.29.

## [1.19.32] - 2026-09-02

### Añadido
- **"¿Has olvidado tu contraseña?" en el login, "ojito" para ver la contraseña escrita, y una pantalla nueva de Administración → Solicitudes de acceso — a petición de Víctor, reutilizando la misma infraestructura de correo que "Documentación faltante" (cola de `emails_sistema_pendientes` en `control-pedidos-princess`, sin SMTP propio).** Un email ya registrado y activo recibe una contraseña temporal directa por correo (sin admin de por medio); uno no registrado, o desactivado, genera una solicitud de acceso y avisa a los admins activos, que pueden aceptarla (con un rol a elegir, creando o reactivando la cuenta con una contraseña temporal) o rechazarla desde la pantalla nueva. Cualquier contraseña temporal fuerza un cambio de contraseña obligatorio en el primer login (`usuarios.debe_cambiar_password`, migración nueva `database/migraciones/2026-09-02_recuperacion_acceso.sql` — **aplicar en Supabase antes de desplegar**). Nuevo `CampoPassword.jsx` (ojito compartido) reutilizado también en `UsuarioForm.jsx`. Backend: `backend/src/controllers/authController.js` (`recuperarAcceso`, `cambiarPasswordObligatorio`), `backend/src/controllers/solicitudesAccesoController.js` (nuevo), `backend/src/utils/contrasenaTemporal.js` (nuevo), `backend/src/utils/emailHtml.js`, `backend/src/middleware/auth.js`, `backend/src/routes/auth.js`, `backend/src/routes/admin.js`. Frontend: `frontend/src/components/CampoPassword.jsx` (nuevo), `RecuperarAccesoModal.jsx` (nuevo), `CambiarPasswordObligatorio.jsx` (nuevo), `admin/AdminSolicitudesAcceso.jsx` (nuevo), `LoginScreen.jsx`, `admin/UsuarioForm.jsx`, `App.jsx`, `Sidebar.jsx`, `services/api.js`, `styles/index.css`.

### Verificación
`npm run build` (Vite), limpio — la pantalla nueva se separa en su propio chunk, igual que el resto de Administración desde v1.11. `node --check` en los seis ficheros de backend nuevos/tocados. Backend probado con un doble de Supabase en memoria más un doble del puente de correo (arnés nuevo en `recuperaciontest/`, mismo patrón que `jerarquiatest/`: importa los controladores REALES sin modificar): 62 aserciones, incluidos dos casos de regresión dedicados a dos fallos que me autocorregí durante la implementación antes de cualquier prueba — orden correo-antes-que-BD en `recuperarAcceso` (si el correo falla, la contraseña antigua no se toca, para no perder el acceso sin remedio) y ausencia de un placeholder de contraseña vacía al aceptar una solicitud (la contraseña real se genera antes del único INSERT/UPDATE) — ambos confirmados reintroduciendo el fallo a propósito y viendo fallar la prueba correspondiente, luego revertidos. Prueba end-to-end real con Playwright contra el frontend real en modo demo: 21 aserciones cubriendo el ojito, el modal de recuperación, la pantalla de cambio obligatorio completa (incluida la cuenta de demo nueva `temporal@demo.dali`), y el ciclo completo de aceptar/rechazar solicitudes de acceso como admin, con la cuenta nueva apareciendo correctamente en Administración → Usuarios.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.32**. Otros documentos de mantenimiento revisados en esta entrega: `README.md`, `backend/README.md`, `frontend/README.md` — los tres se actualizan (endpoints nuevos, diseño del flujo, y las secciones de "pendientes" que mencionaban esta misma funcionalidad se marcan resueltas). Funcionalidad nueva a petición de Víctor, fuera de la auditoría full ya cerrada en v1.19.29.

## [1.19.31] - 2026-09-02

### Añadido
- **El sidebar oculta las naturalezas/familias/subfamilias sin ningún DALI activo, para un menú lateral más limpio — a petición de Víctor, con su mismo ejemplo real (naturaleza BAZAR, familia "ARTICULOS BAZAR", sin ningún activo).** `GET /jerarquia` deja de devolver el árbol completo de clasificación tal cual y ahora cuenta, por naturaleza/familia/subfamilia, cuántos artículos tiene cada rama (activos por defecto — mismo criterio `activo_dali`+`activo_general` que el resto de la app — o todos con `?todos=true`, respetado únicamente para una sesión admin, igual que en `/articulos`) y descarta cualquier nodo con el conteo a cero; un artículo sin subfamilia asignada sigue "sosteniendo visible" a su familia (y uno sin familia, a su naturaleza), sin inflar el conteo de ningún hijo suyo. El conteo se calcula pidiendo solo las 3 columnas de clasificación de `articulos` (nada de nombre, códigos, proveedor…), pensado para egress igual que el resto de esta app. El frontend vuelve a pedir el árbol cuando cambia el checkbox "Incluir no activos" (solo admin; para hotel nunca se refresca de más) y, si la naturaleza/familia/subfamilia seleccionada deja de existir en el árbol nuevo, sube sola al nivel más profundo que siga existiendo en vez de quedarse en un filtro fantasma sin nada resaltado en el menú. `backend/src/controllers/jerarquiaController.js`, `backend/src/routes/jerarquia.js`, `backend/src/controllers/articulosController.js` (constante compartida), `frontend/src/services/api.js`, `frontend/src/App.jsx`.

### Verificación
`npm run build` (Vite), limpio; `node --check` en los tres ficheros de backend tocados. Como este sandbox no tiene acceso a un Supabase real (igual que el resto de esta auditoría), la lógica de conteo/filtrado de `jerarquiaController.js` se probó con un doble de Supabase en memoria que reproduce la API encadenable real (`.from().select().eq().order().range()`), importando el propio archivo real sin modificar: 20 casos, incluido el ejemplo exacto de Víctor (BAZAR desaparece del todo para un usuario normal y reaparece completo — familia y las dos subfamilias — para un admin con "Incluir no activos"), una naturaleza/familia con una subfamilia activa y otra no (la familia se queda visible, solo se oculta la subfamilia vacía), artículos "directos" sin familia/subfamilia asignada (sostienen visible a su padre aunque sus hijos del árbol queden todos vacíos), que `activo_dali=true` con `activo_general=false` NO cuenta como activo (no basta con mirar una sola columna), que `?todos=true` se ignora para quien no es admin, paginación real con más de 1.000 filas en una tanda, y que un error de Supabase se propaga como 500 en vez de un árbol vacío silencioso. Además, prueba end-to-end real con Playwright contra el frontend real en modo demo (`admin@demo.dali` y `hotel@demo.dali`, sin mocks, mismo enfoque que el resto de la auditoría): confirmado que hotel nunca ve BAZAR ni el checkbox "Incluir no activos"; que un admin sin marcarlo ve exactamente lo mismo que hotel; que al marcarlo BAZAR reaparece con su familia y sus dos subfamilias; y que, al desmarcarlo de nuevo con BAZAR seleccionado, el sidebar recupera un estado consistente en vez de quedarse en un filtro fantasma. Antes de dar cada arreglo por bueno se comprobó también que ambas pruebas (la de conteo aislada y la end-to-end) detectan de verdad una regresión deliberada (quitar el filtro `activo_general` en el backend; quitar el filtro de activos en el modo demo del frontend) antes de revertirla.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.31**. Otros documentos de mantenimiento revisados en esta entrega: `README.md`, `frontend/README.md` — no aplica ningún cambio en ninguno; `backend/README.md` sí se actualiza (la fila de `GET /jerarquia` en la tabla de endpoints ahora refleja el filtrado y el `?todos=true`). Funcionalidad nueva a petición de Víctor, fuera de la auditoría full ya cerrada en v1.19.29.

## [1.19.30] - 2026-09-02

### Añadido
- **Botón "Imprimir" en el catálogo, junto a "Exportar Excel"/"Exportar PDF", a petición de Víctor.** A diferencia de exportar (que genera y descarga un fichero), "Imprimir" abre directamente el diálogo de impresión nativo del navegador (`window.print()`) sobre una tabla optimizada para papel, sin generar ni descargar nada. Cubre TODOS los artículos que cumplen el filtro activo en pantalla (búsqueda, naturaleza/familia/subfamilia, "ver no activos" si aplica) — igual que Exportar, no solo la página visible — trayéndolos con el mismo endpoint público de listado (`fetchArticulos`) recorrido en bucle por páginas de 3000 (el tope real del backend, `MAX_PAGE_SIZE` en `articulosController.js`) para cubrir sin problema los ~6.763 artículos activos actuales o cualquier cifra mayor en el futuro. Punto central del encargo: **el resultado impreso es SIEMPRE el mismo sea cual sea el rol de quien imprime** — admin y hotel ven exactamente las mismas columnas (Código DALI, Código SAP, Código Proveedor, Artículo, Proveedor, Unidad y una columna "Cantidad" en blanco para anotar a mano), replicando fielmente `columnasPdf(esAdmin=false)` de `backend/src/workers/generarExportWorker.js` — la vista impresa NUNCA muestra la columna "Activo" que sí ve un admin al exportar a PDF/Excel. `App.jsx`, `styles/index.css`.

### Verificación
`npm run build` (Vite), limpio. Prueba end-to-end real con Playwright contra el frontend real en modo demo (login de demo del propio proyecto, `admin@demo.dali` Y `hotel@demo.dali`, sin ningún mock): confirmado, para AMBOS roles, que el botón "Imprimir" es visible, que al pulsarlo se prepara la vista de impresión y se invoca `window.print()` (interceptado, porque Chromium sin cabeza no puede imprimir de verdad), que las cabeceras de la tabla impresa son exactamente las 7 columnas del rol hotel — nunca "Activo" — que la columna "Cantidad" llega en blanco, que `@media print` oculta de verdad `.app-shell` y muestra `.print-view` (comprobado emulando el medio "print" del navegador), y que la vista de impresión se limpia del DOM tras el evento `afterprint` (para no dejar colgada una tabla de miles de filas el resto de la sesión). Antes de dar el arreglo por bueno, se añadió a propósito una columna "Activo" condicionada a `esAdmin` en la vista de impresión y se repitió la misma prueba: falló exactamente como se esperaba (detectó tanto la cabecera de más como la presencia de "Activo"), confirmando que la prueba detecta de verdad una diferencia de columnas entre roles y no solo comprueba que algo se pinta; revertido antes de esta entrega. Aparte, se verificó el bucle de paginación (page-looping) de forma aislada, sin navegador — el catálogo demo solo tiene 22 artículos, así que nunca ejercita más de una vuelta real del bucle — reproduciendo la misma lógica exacta con una fuente de datos simulada para totales de 0, 1, 2.999, 3.000, 3.001, 6.000, 6.763 (la cifra real citada de activos DALI) y 9.000: en todos los casos se acumula el total exacto de artículos, sin duplicados ni huecos, con el número de llamadas esperado (1 llamada hasta 3.000, 2 hasta 6.000, 3 hasta 9.000).

Versión: `backend/package.json` y `frontend/package.json` → **1.19.30** (backend sin cambios en esta entrega — no ha hecho falta tocar el API, se reutiliza el endpoint público de listado ya existente; se sube igual para mantener sincronizados los dos `package.json`). Otros documentos de mantenimiento revisados en esta entrega: `README.md`, `backend/README.md`, `frontend/README.md` — no aplica ningún cambio en ninguno (ninguno menciona el botón "Exportar", tampoco hacía falta añadir "Imprimir"). Funcionalidad nueva a petición de Víctor, fuera de la auditoría full ya cerrada en v1.19.29.

## [1.19.29] - 2026-09-02

### Arreglado
- **Las 6 pantallas de Administración (más todo lo que arrastran) se descargaban SIEMPRE, para cualquier sesión, aunque la inmensa mayoría de usuarios nunca llega a abrir ninguna.** Undécima y última etapa de la auditoría full. `App.jsx` importaba de forma estática `AdminArticulos.jsx`, `ImportarExcel.jsx`, `AdminUsuarios.jsx`, `AdminDocumentacionFaltante.jsx`, `AdminProveedores.jsx` y `AdminExportarZip.jsx` — y cada una arrastra consigo sus propios componentes (p.ej. `AdminArticulos.jsx` importa además `ArticuloForm.jsx` y `CargaMasivaModal.jsx`, más de 2.000 líneas entre las dos), así que Vite metía todo eso en el mismo bundle principal para CUALQUIER visita. Toda la app exige sesión iniciada, pero de esa gente con sesión, la mayoría no es admin (`esAdmin`) y nunca ve ni una sola de estas 6 pantallas; e incluso un admin de verdad, en una sesión normal, solo visita una o dos de las 6 a la vez. Las 6 pasan a cargarse con `lazy()` de React, envueltas en un único `<Suspense>` (solo puede haber una `vista` activa a la vez, así que un límite compartido basta) — el código de cada pantalla se pide por red la primera vez que se entra de verdad a ella, no antes. `App.jsx`.

### Verificación
`npm run build` (Vite): el bundle principal baja de 255,59 KB (75,67 KB comprimido) a 180,10 KB (56,67 KB comprimido) — un 30% menos de JavaScript que descarga y ejecuta CUALQUIER visita, admin o no — y las 6 pantallas (más `ConfirmDialog.jsx`, un componente compartido entre varias) pasan a sus propios ficheros aparte, entre 0,57 KB y 39,92 KB cada uno, pedidos solo cuando hacen falta. Prueba end-to-end real con Playwright contra el frontend real en modo demo (login de demo del propio proyecto, sin ningún mock de `api.js`): confirmado que, antes de iniciar sesión, no se pide ningún módulo de administración; que, tras iniciar sesión como admin con el catálogo visible, TAMPOCO se pide ninguno todavía (ser admin no basta, hace falta entrar de verdad a una pantalla); que cada una de las 6 pantallas, al pulsar su pestaña, pide su propio módulo por red (y solo el suyo, de las que quedan por visitar) y muestra su título correctamente; que volver a una pantalla ya visitada no vuelve a pedir su módulo; y que volver al catálogo tras haber visitado las 6 sigue funcionando con normalidad. Sin errores de consola en toda la sesión.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.29** (backend sin cambios en esta versión — se sube igual para mantener sincronizados los dos `package.json`). Otros documentos de mantenimiento revisados en esta entrega: `README.md`, `backend/README.md`, `frontend/README.md` — no aplica ningún cambio en ninguno. Con esta entrega se da por completa la auditoría full de esta app (11 etapas, más dos correcciones fuera de turno sobre incidencias reales reportadas durante el proceso).

## [1.19.28] - 2026-09-02

### Arreglado
- **La tabla de resultados de la carga masiva volvía a renderizar TODAS las filas cada vez que UNA sola cambiaba de estado, con carpetas de miles de archivos.** Décima etapa de la auditoría full. Cada fila se pintaba inline dentro de `filas.map(...)`, en el propio render de `CargaMasivaModal` — un único array de estado con potencialmente miles de elementos (`CONCURRENCIA_SUBIDA`, pensado justo para carpetas de miles de archivos subiéndose varios a la vez). Cada actualización de UNA fila (`procesarFila` hace varias por archivo: "subiendo" al empezar, el resultado final al terminar) disparaba un re-render del componente entero, y `filas.map(...)` volvía a evaluar el JSX de TODAS las demás filas también, aunque su contenido no hubiera cambiado — con miles de archivos subiéndose a la vez, el trabajo de render crece con el cuadrado del número de archivos, no de forma lineal. Se extrae la fila a su propio componente, `FilaCarga`, envuelto en `memo()` — el propio patrón de actualización (`setFilas(prev => prev.map((f, idx) => idx === i ? {...} : f))`) ya devolvía la MISMA referencia para cualquier fila que no fuera la actualizada, así que memo() ahora aprovecha esa referencia estable para saltarse el render de las filas que no cambiaron. Fila de solo lectura, sin ningún botón por fila, así que no hay riesgo de que una función nueva en cada render invalide la comparación de memo() sin querer. `CargaMasivaModal.jsx`.

### Verificación
`npm run build` (Vite), limpio. Repetida la prueba end-to-end de la etapa 6 (fetchInfoYHashDocumento) sin cambios: mismos resultados exactos, confirmando que extraer la fila no cambió ningún comportamiento visible. Prueba nueva y específica (arnés en `rerendertest/`), con instrumentación temporal de conteo de renders por fila (retirada antes de esta entrega): con una carga real de 40 archivos, 40 artículos distintos, midiendo cuántas veces se renderiza CADA fila durante todo el proceso — con `memo()` (el código de esta entrega), 160 renders en total para 40 filas (4 por fila: montaje + "subiendo" + resultado final, un margen pequeño y constante) y el conteo NUNCA supera 5 en ninguna fila. Para confirmar que el ahorro es de verdad `memo()` y no un efecto casual de haber movido el JSX a otra función, se quitó `memo()` a propósito (dejando la fila igual de extraída, solo sin memoizar) y se repitió la misma prueba: 1.000 renders en total para las mismas 40 filas, con una fila llegando a renderizarse 25 veces — más de 6 veces más trabajo de render para solo 40 archivos, una diferencia que crece con el cuadrado del número de archivos en una carga real de miles.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.28** (backend sin cambios en esta versión — se sube igual para mantener sincronizados los dos `package.json`). Otros documentos de mantenimiento revisados en esta entrega: `README.md`, `backend/README.md`, `frontend/README.md` — no aplica ningún cambio en ninguno.

## [1.19.27] - 2026-09-02

### Arreglado
- **`EmailProveedorModal.jsx` se cerraba solo al seleccionar texto del correo (asunto/cuerpo) si el ratón se soltaba fuera del panel, perdiendo lo escrito.** Novena etapa de la auditoría full. Este modal cerraba con un simple `onClick={onClose}` en el fondo (`.confirm-overlay`), en vez del hook compartido `useCerrarAlClicFuera` que ya usan `ArticuloForm.jsx`, `CargaMasivaModal.jsx` y `UsuarioForm.jsx` — exactamente el patrón que ese hook existe para evitar (ver su propio comentario): el evento `click` del navegador se basa en dónde se SUELTA el botón del ratón, no en dónde se pulsó, así que seleccionar texto arrastrando dentro del panel y soltar el botón fuera de sus límites, aunque sea por un píxel, se registra como un clic en el fondo. Este modal en concreto tiene un `<textarea>` de 12 filas (el cuerpo del correo, pensado para editarse y revisarse a mano antes de enviar) y un campo de asunto — contenido real que se selecciona con frecuencia, a diferencia de un simple diálogo de confirmación de texto corto — así que era el sitio con más probabilidad real de sufrir este cierre accidental, perdiendo cualquier ajuste ya hecho al texto del correo. `EmailProveedorModal.jsx`.

### Verificación
`npm run build` (Vite), limpio. Prueba end-to-end real con Playwright (arnés nuevo en `emailmodaltest/`, con la hoja de estilos real cargada para que la geometría del panel sea la de verdad) reproduciendo el bug con eventos de ratón REALES, no un `.click()` sintético: `mousedown` dentro del `<textarea>`, varios `mousemove` intermedios (como un arrastre de selección de texto) hasta un punto fuera del panel, y `mouseup` ahí — confirmado que, ANTES del arreglo (se revirtió el cambio temporalmente para comprobarlo), esta misma prueba SÍ detecta el cierre accidental (falla, tal como se esperaba de un caso que reproduce el bug real); y que, con el arreglo aplicado, el modal ya NO se cierra en ese caso. Como contraste, se comprobó también que un clic de verdad que empieza Y termina en el propio fondo (sin arrastre) SIGUE cerrando el modal con normalidad — el hook corrige el caso de selección de texto sin romper el cierre normal de "clic fuera para cerrar".

Versión: `backend/package.json` y `frontend/package.json` → **1.19.27** (backend sin cambios en esta versión — se sube igual para mantener sincronizados los dos `package.json`). Nota aparte, no tocada en esta entrega: `ConfirmDialog.jsx` usa el mismo patrón manual (`onClick={onCancel}` en el fondo) — comparte la misma vulnerabilidad en teoría, pero su contenido es un mensaje corto de solo lectura (no un campo editable como este modal), así que el riesgo real de que alguien lo dispare seleccionando texto es mucho menor; se deja anotado aquí por si en el futuro algún `<ConfirmDialog>` pasa a mostrar contenido más largo o seleccionable. Otros documentos de mantenimiento revisados en esta entrega: `README.md`, `backend/README.md`, `frontend/README.md` — no aplica ningún cambio en ninguno.

## [1.19.26] - 2026-09-02

### Arreglado
- **`ArticuloForm.jsx`: guardar el código de un proveedor o de una marca recargaba TODA la documentación del artículo, regenerando una URL firmada de Storage por cada imagen/ficha ya guardada de CUALQUIER proveedor, solo para reflejar un cambio de texto.** Octava etapa de la auditoría full. Las 8 acciones del panel (subir/borrar imagen o ficha, guardar código de proveedor o de marca, crear/borrar marca) llamaban todas a `cargarGrupos()` tras completarse — un `GET /articulos/:id/fichas-por-proveedor` que trae, para el artículo entero, 4 tablas y además una llamada a `supabase.storage.createSignedUrl()` por cada imagen y cada ficha ya guardadas de TODOS los proveedores del artículo (ver `obtenerFichasPorProveedor`, ya señalado como sensible en su propio comentario: un incidente real anterior en el que guardar un código de proveedor tumbaba el proceso entero, ya arreglado con un try/catch — ver ese mismo comentario en `articulosController.js`). Guardar un código de proveedor o de marca (`guardarCodigoPara`/`guardarCodigoMarca`) es una simple escritura de texto que no toca ninguna imagen, ficha ni URL — con un artículo que ya tiene documentación de varios proveedores alternativos, cada guardado de un código de sobra disparaba de más varias llamadas reales a Storage. Estas dos acciones ahora actualizan el estado local (`grupos`) con el valor que el backend acaba de confirmar, sin volver a pedir nada — incluido el caso de guardar el código de un proveedor que todavía no tenía ningún grupo (primera vez), que crea el grupo mínimo correspondiente en el sitio. Las otras 6 acciones (subir/borrar imagen o ficha, crear/borrar marca) siguen recargando con `cargarGrupos()` como antes — esas sí cambian una URL de Storage de verdad, así que ahí no hay ahorro seguro posible sin arriesgar una imagen/ficha desincronizada. `ArticuloForm.jsx`.

### Verificación
`npm run build` (Vite), limpio. Prueba end-to-end real con Playwright sobre el componente `ArticuloForm.jsx` aislado (mock de la API, sin backend real, arnés nuevo en `articuloformtest/`), con un artículo con un proveedor asignado (con una marca extra ya guardada), una alternativa ya guardada, y un tercer proveedor real sin ningún grupo todavía: confirmado que guardar un nuevo código para el proveedor asignado (ya con grupo) no dispara ninguna llamada nueva a `fetchFichasPorProveedor`; que guardar el código de la marca ya existente tampoco la dispara, y que el texto de solo lectura de la marca (fuera del propio campo de edición) refleja el cambio de inmediato — prueba de que se actualizó `grupos` de verdad, no solo el input local del campo; que guardar el código de un proveedor SIN grupo previo (buscado desde cero) tampoco dispara ninguna recarga, crea el grupo correcto y, al dejar de buscarlo, aparece ya remontado en la lista de "otros proveedores guardados" con el código correcto precargado — la prueba de que el grupo nuevo quedó bien construido en el estado local, sin depender de ninguna respuesta de red para mostrarlo. En las 3 mutaciones de la prueba, `fetchFichasPorProveedor` se llamó una única vez en total (la carga inicial del panel).

Versión: `backend/package.json` y `frontend/package.json` → **1.19.26** (backend sin cambios en esta versión — se sube igual para mantener sincronizados los dos `package.json`). Otros documentos de mantenimiento revisados en esta entrega: `README.md`, `backend/README.md`, `frontend/README.md` — no aplica ningún cambio en ninguno.

## [1.19.25] - 2026-09-02

### Arreglado
- **`fetchProveedores()` sin caché: la lista completa de proveedores se pedía de nuevo en cada montaje de 4 pantallas distintas de administración, incluida una llamada nueva por CADA artículo abierto para editar.** Séptima etapa de la auditoría full. `AdminProveedores.jsx`, `AdminExportarZip.jsx` y `CargaMasivaModal.jsx` piden esta lista al montarse; `ArticuloForm.jsx` la vuelve a pedir en un `useEffect` con `[articulo.codigo_dali]` como dependencia — es decir, cada vez que el admin abre un artículo distinto para editarlo, aunque la lista de proveedores sea exactamente la misma que hace un segundo. La lista casi nunca cambia dentro de esta app (solo la toca `fusionarProveedores`, que borra un proveedor de verdad; dar de alta uno nuevo se hace directamente en Supabase). `fetchProveedores()` (`services/api.js`) ahora guarda en caché, a nivel de módulo, la respuesta ya resuelta — las llamadas siguientes la devuelven sin ninguna petición HTTP — y deduplica peticiones en vuelo (si dos componentes se montan casi a la vez, comparten una sola petición real en vez de lanzar dos). Un fallo de red NO se cachea, para no dejar la app atascada en "sin proveedores" tras un problema puntual. La caché se invalida automáticamente desde dentro de `fusionarProveedores()` tras un éxito — el único punto real de mutación —, así que `AdminProveedores.jsx` (que ya volvía a llamar a `fetchProveedores()` después de fusionar) recibe la lista fresca sin que haga falta tocar ese componente. `services/api.js`.

### Verificación
`node --check` sobre `api.js`; `npm run build` (Vite), limpio. Prueba funcional en Node puro (sin navegador — la lógica es del módulo `api.js`, no depende de React) con `fetch` global mockeado y contador de peticiones reales: confirmado que la primera llamada a `fetchProveedores()` hace 1 petición, que las siguientes NO generan peticiones nuevas y devuelven los mismos datos, que cada llamada devuelve una copia del array (mutar el resultado de una llamada no afecta a las siguientes ni a la caché interna), que 3 llamadas lanzadas EN PARALELO antes de que la primera responda comparten una única petición real (deduplicación), que `fusionarProveedores()` invalida la caché — la siguiente `fetchProveedores()` sí vuelve a pedir la lista de verdad — y que un fallo de red se propaga como error y NO se cachea (el intento siguiente vuelve a pedir de verdad, no se queda atascado repitiendo el mismo fallo).

Versión: `backend/package.json` y `frontend/package.json` → **1.19.25** (backend sin cambios en esta versión — se sube igual para mantener sincronizados los dos `package.json`). Otros documentos de mantenimiento revisados en esta entrega: `README.md`, `backend/README.md`, `frontend/README.md` — no aplica ningún cambio en ninguno.

## [1.19.24] - 2026-09-02

### Arreglado
- **Carga masiva de imágenes/fichas: dos peticiones de red por archivo antes de decidir si subirlo (una de ellas, innecesariamente pesada).** Sexta etapa de la auditoría full. `subirParaCodigoDali()` (`CargaMasivaModal.jsx`) llamaba a `fetchArticulo(idArticulo)` — trae la ficha completa del artículo, con sus 4 tablas relacionadas vía join, pensada para `ArticuloDetail.jsx` — solo para confirmar que el artículo existía y sacar su nombre y proveedor asignado, y por separado a `fetchHashDocumento()` para el hash con el que decidir si el archivo ya está subido igual (evitar una subida redundante a Storage). Con una carpeta de cientos de archivos, eso es el doble de peticiones de las necesarias para una decisión que solo necesita 4 campos (nombre del artículo, hash existente, proveedor asignado, código de proveedor coincidente) — egress y tiempo de más en cada carga masiva. Nuevo endpoint único `GET /admin/articulos/:codigoDali/documentos-hash` (`obtenerHashDocumento` en `storageController.js`, ampliado — confirmado por grep que solo lo usa esta pantalla, así que ampliar su forma de respuesta no afecta a nadie más) devuelve en una sola consulta el hash existente, el código de proveedor coincidente y los 3 campos que antes venían de `fetchArticulo` (nombre del artículo, id y nombre del proveedor realmente asignado). Frontend: `fetchHashDocumento` sustituida por `fetchInfoYHashDocumento()` (`services/api.js`), y `subirParaCodigoDali()` ya solo hace esa única llamada (en paralelo con el hash del archivo local, `Promise.all`, igual que antes). Cambio de comportamiento documentado a propósito: la función anterior `fetchHashDocumento` nunca lanzaba error (para no bloquear la subida ante un fallo de red puntual), pero ahora también confirma que el artículo existe — algo que antes garantizaba `fetchArticulo`, que SÍ lanzaba siempre — así que `fetchInfoYHashDocumento` también lanza ante cualquier fallo; un fallo puntual de esta llamada ahora deja la fila en error en vez de intentar subir a ciegas sin saber si el artículo sigue existiendo, más seguro que el comportamiento anterior. `storageController.js`, `services/api.js`, `CargaMasivaModal.jsx`.

### Verificación
`node --check` sobre los archivos de backend tocados; `npm run build` (Vite) del frontend, limpio; grep confirmando que no queda ninguna referencia viva a `fetchArticulo`/`fetchHashDocumento` en `CargaMasivaModal.jsx` (solo en comentarios históricos). Prueba funcional del backend contra un mock de Supabase en memoria (4 casos): artículo normal con proveedor asignado igual al consultado, artículo "en reserva" (consultado con un proveedor DISTINTO al asignado — confirma que `id_proveedor_asignado`/`proveedor_asignado` reflejan siempre la asignación real, no el proveedor de la consulta), artículo inexistente (404 con mensaje claro) y artículo sin hash todavía (sigue devolviendo el nombre igualmente). Prueba end-to-end real con Playwright sobre el componente `CargaMasivaModal.jsx` aislado (mock de la API, sin backend real): simulada una selección de carpeta con 3 archivos de imagen de un proveedor de prueba (artículo normal, artículo "en reserva" de otro proveedor, y un tercero cuya consulta de info+hash falla a propósito) — confirmado que los mensajes de cada fila son los esperados (nombre del artículo, aviso "en reserva" con el proveedor real cuando corresponde, mensaje de error claro en el caso fallido sin tumbar las otras dos filas), que `subirImagenArticulo` solo se llama para los 2 artículos con info válida y NUNCA para el que falló, y — el objetivo real del cambio — que se hace EXACTAMENTE una llamada a la nueva función combinada por archivo (3 archivos, 3 llamadas), no dos como antes.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.24**. Otros documentos de mantenimiento revisados en esta entrega: `README.md`, `backend/README.md`, `frontend/README.md` — no aplica ningún cambio en ninguno.

## [1.19.23] - 2026-09-02

### Arreglado
- **El diálogo de confirmación de "Eliminar imágenes repetidas" (v1.19.22) se salía de la pantalla con un grupo grande, sin scroll, dejando los botones "Cancelar"/"Sí, eliminar" inalcanzables.** Reportado por Víctor con un caso real de 168 artículos: el mensaje de confirmación enumeraba TODOS los códigos DALI del grupo, y `.confirm-box` (el cuadro genérico que usa `ConfirmDialog.jsx` en toda la app) no tenía `max-height`/`overflow-y` — con un mensaje así de largo, el cuadro crecía sin límite y no cabía en el viewport, sin ninguna forma de desplazarse hasta los botones. Dos arreglos: 1) el mensaje de esa confirmación concreta ya no enumera los códigos (la tabla justo encima ya los enseña todos) — solo dice la cantidad; 2) `.confirm-box` lleva ahora `max-height: 90vh; overflow-y: auto` (mismo criterio que ya llevaba `.email-modal-box`, la variante ancha del mismo diálogo) — defensivo para CUALQUIER `<ConfirmDialog>` con un mensaje largo en el futuro, no solo este caso concreto. `AdminProveedores.jsx`, `styles/index.css`.

### Verificación
`npm run build` (Vite), limpio. Prueba end-to-end con Playwright reproduciendo el caso real (grupo de 168 artículos, viewport reducido a 1000×500 a propósito para forzar el desbordamiento que reportó Víctor): confirmado que el mensaje del diálogo ya no incluye ningún código DALI individual (224 caracteres, legible, en vez de una lista de cientos), que el cuadro entero cabe dentro del viewport de 500px de alto (113px de altura real), y que el botón "Sí, eliminar" es visible y CLICKABLE — Playwright falla el `click()` si el elemento está tapado o fuera de la vista, así que un clic que funciona y dispara la llamada correcta es la prueba real de que es alcanzable, no solo que "debería" serlo. Repetida también la prueba anterior del grupo pequeño (4 artículos) para confirmar que no se ha roto nada.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.23** (backend sin cambios en esta versión — se sube igual para mantener sincronizados los dos `package.json`). Otros documentos de mantenimiento revisados en esta entrega: `README.md`, `backend/README.md`, `frontend/README.md` — no aplica ningún cambio en ninguno.

## [1.19.22] - 2026-09-02

### Añadido
- **Herramienta "Reparar imágenes antiguas sin marcar como genéricas"** (Administración → Fusionar proveedores, sección nueva al final de la pantalla). Reportado por Víctor: un proveedor tenía la imagen de reserva "SIN IMAGEN" asignada a TODAS sus referencias, pero la quitó de su carpeta ANTES de que existiera `imagenes.es_generica` (migración `2026-09-01_es_generica_imagen.sql`, v0.98) — esas filas se subieron por la vía normal de siempre, indistinguibles en la base de datos de fotos propias reales (`es_generica = false`, el valor por defecto). Como esos artículos "ya tienen imagen" a ojos del sistema, `GET /admin/documentacion-faltante` nunca los marca `falta_imagen: true`, así que `calcularFilasFallback()` (`CargaMasivaModal.jsx`) los salta siempre al repartir una "SIN IMAGEN" nueva — por muchas veces que Víctor repita la carga masiva con el archivo correcto, nunca les llega. Nuevos endpoints `GET`/`DELETE /admin/proveedores/:id/imagenes-repetidas`: el `GET` agrupa, para un proveedor, las imágenes `es_generica = false` que comparten EXACTAMENTE el mismo hash entre 2 o más artículos activos suyos (mismo criterio de hash compartido que ya usaba "Documentación faltante" para su aviso informativo, aquí como herramienta de limpieza en vez de solo aviso — dos fotos de artículos distintos con el archivo idéntico son, en la práctica, siempre la misma imagen subida varias veces); el `DELETE` borra (Storage + tabla) el grupo confirmado por el admin. Los artículos afectados quedan "sin imagen" — la siguiente carga masiva con la "SIN IMAGEN" correcta ya se la asigna, esta vez marcada `es_generica = true` desde el principio. `storageController.js`, `routes/admin.js`, `services/api.js`, `AdminProveedores.jsx`.

### Verificación
`node --check` sobre los archivos de backend tocados; `npm run build` (Vite) del frontend, limpio. Prueba funcional contra un mock de Supabase en memoria: proveedor con 4 artículos activos compartiendo el hash de la genérica vieja, 1 artículo con foto propia real (hash único, no debe aparecer en ningún grupo), 1 artículo YA DADO DE BAJA que también comparte el hash (no debe contar en el listado, pero sí limpiarse al borrar), una fila de OTRO proveedor con el mismo hash (nunca debe tocarse) y una fila YA marcada `es_generica = true` del mismo proveedor (la gestiona el flujo existente, no debe aparecer aquí) — confirmado: el listado detecta exactamente el grupo correcto con los 4 artículos activos correctos, el borrado elimina las 5 filas reales (4 activas + 1 de baja) sin tocar la foto propia, la fila ya marcada ni la del otro proveedor, y tras borrar el listado ya no detecta ningún grupo. Prueba end-to-end con Playwright del componente aislado (mock de la API): buscar un proveedor con grupos muestra la tabla con los códigos DALI y la cantidad correctos, "Eliminar este grupo" abre el diálogo de confirmación sin llamar todavía al backend, confirmar llama con el id de proveedor y el hash correctos y el grupo desaparece de la tabla con el aviso de éxito, y un proveedor sin grupos repetidos muestra el aviso de "nada que reparar" en vez de una tabla vacía confusa.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.22**. Otros documentos de mantenimiento revisados en esta entrega: `README.md`, `backend/README.md`, `frontend/README.md` — no aplica ningún cambio en ninguno.

## [1.19.21] - 2026-09-02

### Arreglado
- **Exportar PDF/Excel del catálogo bloqueaba el único hilo del proceso Node mientras se generaba.** Cuarta etapa de la auditoría full. `GET /export/pdf` y `GET /export/excel` (`exportController.js`) construían el documento entero directamente en el hilo principal — con el catálogo completo (hasta ~30.000 artículos si un admin exporta "incluir no activos" sin filtro), eso significa recorrer todas esas filas dibujando cada una en el PDF (varias llamadas a `doc.text()`/`doc.rect()` por fila, más el cálculo de paginación) o rellenando cada celda del Excel, todo trabajo JS puramente síncrono. Mientras dura, el plan gratuito de Render (un único proceso, un único hilo, sin cluster/PM2) no puede atender ninguna otra petición — ni las de otros usuarios, ni el propio health check — el mismo tipo de bloqueo ya diagnosticado y corregido para la importación de Excel en v1.15.2 (`parsearExcelWorker.js`), esta vez en la exportación. Se movió toda la construcción del documento (PDF y Excel) a un `worker_thread` nuevo, `workers/generarExportWorker.js`, que arma el fichero entero en memoria y lo devuelve como buffer — `exportarPdf`/`exportarExcel` ahora solo esperan ese buffer y hacen `res.end(buffer)`, un `res.write` de golpe en vez de miles de operaciones síncronas de dibujado en el propio hilo de la petición. Mismo patrón ya establecido (`parsearExcelEnWorker()` en `importController.js`): un Worker nuevo por exportación, destruido al terminar, sin pool. `exportController.js`, `workers/generarExportWorker.js` (nuevo), y un comentario corregido en `storageController.js` que apuntaba a la ubicación anterior de `nombreGrupo()`.

### Verificación
`node --check` sobre los tres archivos tocados. Prueba end-to-end real (sin mocks, con el propio `pdfkit`/`exceljs` reales) contra un catálogo sintético de 3000 artículos: confirmado que el PDF y el Excel generados son ficheros válidos (cabecera `%PDF-` y cabecera `PK`/ZIP respectivamente, tamaño proporcional al número de artículos) y — el objetivo real del cambio — que un `setInterval` de 5ms en el hilo principal siguió disparando con normalidad (364 veces) mientras el worker generaba ambos documentos en paralelo (~2s), confirmando que el hilo principal queda libre durante la generación. Prueba de contraste aparte: un bucle síncrono puro de la misma duración en el hilo principal (simulando el comportamiento anterior) deja ese mismo `setInterval` completamente congelado (0 tics), confirmando que la comparación es representativa del bloqueo real que tenía el código antes de este cambio. Prueba adicional con solo 5 artículos y usuario no admin (columna "Cantidad" en blanco en vez de "Activo") y con un tipo de exportación desconocido en `workerData` (confirma que el worker rechaza la Promise limpiamente con un mensaje claro, en vez de colgarse, ante un caso que no debería darse en producción pero que conviene que falle rápido si ocurriera).

Versión: `backend/package.json` y `frontend/package.json` → **1.19.21** (frontend sin cambios en esta versión — se sube igual para mantener sincronizados los dos `package.json`). Otros documentos de mantenimiento revisados en esta entrega: `README.md`, `backend/README.md`, `frontend/README.md` — no aplica ningún cambio en ninguno. Queda pendiente, ya reportado a Víctor pero de impacto menor y con un límite de filas más bajo por naturaleza (solo artículos con documentación incompleta, no el catálogo completo): el mismo tipo de trabajo síncrono en `exportarDocumentacionFaltanteExcel()` (`documentacionController.js`) — no se ha tocado en esta etapa por ese motivo, se deja anotado aquí por si el volumen de esa pantalla creciera lo suficiente como para justificarlo en el futuro.

## [1.19.20] - 2026-09-02

### Arreglado
- **"Documentación faltante" traía `imagenes`/`fichas`/`codigos_proveedor` completas y sin filtrar en cada carga, incluyendo filas de artículos dados de baja.** Tercera etapa de la auditoría full. `calcularDocumentacionFaltante()` (usada tanto por `GET /admin/documentacion-faltante` como por su exportación a Excel) ya paginaba correctamente estas tres tablas, pero sin ningún filtro — traía la tabla entera aunque el resto de la función solo recorre artículos ACTIVOS al final. Cuanto más crecen esas tres tablas, más egress de más para una pantalla que se abre varias veces al día. Nueva función `traerPorArticulos()` filtra por los ids de los artículos activos (troceados en lotes de 500, mismo patrón que `obtenerCodigosProveedorPorArticulos` en `articulosController.js`) en vez de traer cada tabla entera. `documentacionController.js`.
  - Efecto secundario menor, documentado en el propio código: el conteo de "imágenes con el mismo hash compartidas entre varios artículos del proveedor" (señal de reserva para detectar la imagen genérica en filas antiguas, previas a `es_generica`) ahora solo compara entre artículos activos entre sí — si una fila antigua compartía hash únicamente con un artículo ya dado de baja, deja de detectarse como "genérica" por esta vía. Solo afecta al aviso informativo de qué imágenes son genéricas en datos anteriores a la migración `2026-09-01_es_generica_imagen.sql`; no afecta a si falta o no la imagen, que sigue siendo exacto.

### Verificación
`node --check` sobre `documentacionController.js`. Prueba funcional contra un mock de Supabase en memoria con 3 artículos activos y 1 dado de baja (con imagen/ficha/código propios, para poder detectar si se consultan): confirmado que el resultado de "qué le falta a cada artículo" es idéntico al que daba la versión anterior (mismos 2 artículos incompletos, mismos campos), que el artículo dado de baja nunca aparece en el resultado, y — el objetivo real del cambio — que ninguna de las tres consultas a `imagenes`/`fichas`/`codigos_proveedor` incluye su id en el filtro `.in()`, con el total de filas realmente transferidas coincidiendo exactamente con las de los artículos activos (6 de 9 posibles, nunca las 3 del artículo de baja). Prueba aparte del troceo en lotes de 500 ids con 1200 ids simulados, confirmando 3 lotes.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.20** (frontend sin cambios en esta versión — se sube igual para mantener sincronizados los dos `package.json`). Otros documentos de mantenimiento revisados en esta entrega: `README.md`, `backend/README.md`, `frontend/README.md` — no aplica ningún cambio en ninguno.

## [1.19.19] - 2026-09-02

### Arreglado
- **`GET /articulos` (pública) sin techo en `pageSize` — una petición directa a la API podía pedir el catálogo activo completo de golpe.** Segunda etapa de la auditoría full. El endpoint es público (solo pasa por `optionalAuth`, no `requireAuth`), y `pageSize` llegaba del query string sin ningún límite superior — el frontend real siempre pide 100 con criterio (`App.jsx`/`AdminArticulos.jsx`), pero nada impedía que otra petición (`?pageSize=100000`) hiciera que el troceo interno en tandas de 1000 (`SUPABASE_MAX_ROWS_POR_PETICION`) siguiera hasta agotar el catálogo activo completo (~6700 artículos con el join a 4 tablas), sin ningún rate limiting en el proyecto. `pageSize` ahora se limita a un máximo de 3000 (`MAX_PAGE_SIZE`, el mismo valor que ya era el valor por defecto) — no cambia el comportamiento de ningún llamador legítimo actual, solo pone techo a un valor sin límite. `articulosController.js`.
- **Llamadas a Control de Pedidos sin timeout — un fallo del otro servicio se quedaba colgado en vez de fallar rápido.** Las tres llamadas salientes de `controlPedidosEmailBridge.js` (encolar email, traer proveedores, traer compradores) no tenían ningún límite de tiempo — si `control-pedidos-princess` (también en Render Free, con su propio cold-start) o el Worker de Cloudflare que hace de proxy delante tardaban o no respondían, la petición de DALI se quedaba esperando indefinidamente. Estas llamadas están en el camino de `GET /admin/documentacion-faltante`, una pantalla que se abre varias veces al día. Añadido `AbortSignal.timeout(15000)` (nativo desde Node 18, sin dependencias nuevas) a las tres, con un mensaje claro ("Control de Pedidos no ha respondido en 15s...") cuando salta — todos los sitios que llaman a estas funciones ya tenían su propio `try/catch`, así que el timeout se propaga como un fallo normal y legible, sin bloquear nada más.

### Verificación
`node --check` sobre `articulosController.js` y `controlPedidosEmailBridge.js`. Prueba unitaria aislada del cálculo de `pageSize` (mismos casos que usa el código: sin valor, 100, 3000, 100000, "100000" como texto, 1) confirmando que el resultado nunca supera 3000. Para el timeout, prueba real contra un servidor HTTP local que nunca responde: confirmado que el `fetch` se aborta exactamente al cumplirse el plazo (no antes, no se queda colgado) y lanza el mensaje esperado — mismo mecanismo que el que ya llevan las tres funciones reales, con un plazo corto solo para la prueba. Sin cambios en el frontend en esta entrega.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.19** (frontend sin cambios en esta versión — se sube igual para mantener sincronizados los dos `package.json`, según la convención ya establecida). Otros documentos de mantenimiento revisados en esta entrega: `README.md`, `backend/README.md`, `frontend/README.md` — no aplica ningún cambio en ninguno.

## [1.19.18] - 2026-09-02

### Arreglado
- **`GET /admin/documentacion-zip`: las tablas `fichas`/`imagenes`/`codigos_proveedor` se leían sin paginar — el zip de backup podía generarse incompleto en silencio.** Primera etapa de la auditoría full pedida por Víctor sobre esta app (misma operación ya hecha antes sobre Control de Pedidos). PostgREST corta cualquier `select` sin `.range()` en 1000 filas SIN devolver ningún error — el resto del backend ya tiene disciplina de paginar en tandas de 1000 (`documentacionController.js`, `exportController.js`, `proveedoresController.js`...), pero `exportZipController.js` (el endpoint pensado como copia de seguridad externa de toda la documentación, ver v0.94/v1.19.12) se quedó fuera de ese cuidado. Con el volumen actual de `fichas`/`imagenes`/`codigos_proveedor` es probable que ya se estuviera superando ese límite al exportar "Todos" los proveedores de una vez — el zip se generaba igualmente (código 200, archivo descargado) pero le faltaban archivos, sin ningún aviso de que el backup estaba incompleto. `exportarDocumentacionZip` ahora pagina las tres consultas con el mismo helper `traerTodo()` ya usado en `proveedoresController.js` (tandas de 1000 vía `.range()`, hasta agotar cada tabla).
- **Administración → Artículos: la tabla se quedaba siempre en las primeras 100 fichas, sin ninguna forma de ver el resto.** Segunda etapa de la misma auditoría. El contador de arriba ya mostraba el total real (p.ej. "29.842 ficha(s)"), pero `fetchArticulos` sin `page`/`pageSize` explícitos trae como mucho 100 filas por defecto, y esta pantalla no tenía paginación ni botón "cargar más" — un artículo que no apareciera entre esos primeros 100 (según el orden del backend) era, a efectos prácticos, invisible desde aquí salvo que se supiera buscarlo por texto exacto. `AdminArticulos.jsx` incorpora ahora la misma paginación (100 por página, botones "← Anterior"/"Siguiente →", indicador "página X de Y") que ya usa el catálogo principal en `App.jsx` — mismo patrón, mismas variables, para no introducir un criterio nuevo.

### Verificación
`node --check` sobre `exportZipController.js`; prueba unitaria aislada de la función de paginación (`traerTodo()`) contra un dataset simulado de 2500/1000/500/0 filas, confirmando el número exacto de tandas de `.range()` y que ya no se trunca a 1000. `npm run build` (Vite) del frontend completo sin errores; verificación end-to-end con Playwright sobre `AdminArticulos.jsx` aislado (mock de `fetchArticulos` con 250 artículos de prueba → 3 páginas de 100/100/50): contador con el total real y "página X de Y", botones "Anterior"/"Siguiente" deshabilitados correctamente en los extremos, cada página trae artículos distintos, y buscar con una página distinta de la 1 activa vuelve a la página 1 automáticamente en vez de dejar la tabla vacía. El flujo del zip contra Supabase real (con más de 1000 filas de verdad en alguna tabla) queda por confirmar en el Render de Víctor — este entorno no tiene acceso a esa base de datos.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.18**. Otros documentos de mantenimiento revisados en esta entrega: `README.md` (no aplica ningún cambio — no hay ninguna referencia de versión ni pendiente relacionado con esto), `backend/README.md`/`frontend/README.md` (secciones "Pendiente / siguientes pasos" revisadas, no aplica ningún cambio).

## [1.19.17] - 2026-09-02

### Corregido
- **`fichas-por-proveedor` tumbaba TODO el proceso del backend (no solo devolvía error).** Reportado por Víctor: al guardar el código de proveedor en la ficha de un artículo, la app "se reiniciaba como si fuera un deploy nuevo" en Render. Causa: `obtenerFichasPorProveedor` (llamado justo después de cada guardado, vía `ArticuloForm.jsx` → `cargarGrupos`) no tenía ningún `try/catch` — si algo dentro lanzaba (lo más probable en este caso: la migración `2026-08-31_marcas_proveedor.sql` sin aplicar todavía en Supabase, con `cargarMarcasPorArticulo` lanzando al consultar una tabla `marcas_proveedor` inexistente), la excepción quedaba como "unhandled promise rejection" — que Node, por defecto desde la v15, resuelve **terminando el proceso entero**. Render lo reiniciaba automáticamente, lo cual se veía desde fuera exactamente igual que un deploy nuevo, y tumbaba la app para todos los usuarios conectados en ese momento, no solo para quien guardó el código. Arreglado en dos capas: `obtenerFichasPorProveedor` envuelto en su propio `try/catch` (devuelve 500 normal en vez de tumbar nada); y, como red de seguridad adicional para cualquier otro controlador que pudiera tener el mismo problema, `process.on("unhandledRejection", ...)` en `server.js` para que un fallo así nunca vuelva a tirar el proceso completo.

### Verificación
`node --check` sobre los archivos tocados; arranque real del servidor con variables de entorno de prueba (`SUPABASE_URL`/`SUPABASE_SERVICE_ROLE_KEY` dummy) para confirmar que sigue levantando sin errores. Confirmado por Víctor en Render, ya en producción, tras aplicar `2026-08-31_marcas_proveedor.sql` (pendiente de una entrega anterior) y `2026-09-01_es_generica_imagen.sql`: el guardado del código de proveedor funciona sin cortes ni reinicios.

## [1.19.16] - 2026-09-01

### Añadido
- **Baja automática de la imagen genérica si "SIN IMAGEN" desaparece de la carpeta del proveedor.** Petición de Víctor: en la carga masiva de imágenes, si el archivo reservado "SIN IMAGEN" de un proveedor deja de estar en su carpeta IMAGENES respecto a una carga anterior, hay que borrar la imagen genérica que se le hubiera asignado a sus artículos y que dejen de mostrarla. Hasta ahora nada marcaba de forma explícita qué filas de `imagenes` eran esa genérica de reserva — `documentacionController.js` lo inferÍa comparando hashes entre artículos del mismo proveedor, una heurística útil para "Documentación faltante" pero no fiable para borrar (un proveedor con un solo artículo sin foto propia genera un hash que aparece una sola vez, indistinguible de una foto real). Columna nueva `imagenes.es_generica` (migración `2026-09-01_es_generica_imagen.sql`), grabada explícitamente por `subirImagenArticulo` cuando la sube la carga masiva de fallback. Endpoint nuevo `DELETE /admin/proveedores/:id/imagen-generica` borra, Storage + tabla, todas las filas marcadas `es_generica = true` de ese proveedor. `CargaMasivaModal.jsx` detecta, al elegir la carpeta, qué proveedores tenían su carpeta IMAGENES explorada en esta pasada pero ya no traen "SIN IMAGEN", avisa de ello, y dispara el borrado al pulsar "Subir".
  - **(2026-09-02)** Corrección sobre el punto anterior, mismo día: Víctor confirmó que el caso límite ya documentado ocurre de verdad — si la carpeta IMAGENES de un proveedor solo contenía "SIN IMAGEN" y ese archivo se borra sin dejar ninguna foto propia detrás, la carpeta queda VACÍA, y el selector de carpeta del navegador (`webkitdirectory`) no ve directorios vacíos, solo archivos — la detección original (comparar contra proveedores con archivos de imagen vistos en esta pasada) no veía nada de ese proveedor y la genérica se quedaba huérfana. Endpoint nuevo `GET /admin/proveedores/con-imagen-generica` (`listarProveedoresConImagenGenerica`) dice, consultando la BD directamente, qué proveedores tienen una genérica guardada AHORA MISMO — ya no hace falta verla desaparecer del árbol de archivos. `CargaMasivaModal.jsx` combina esa lista con una señal más amplia (`proveedoresEnCarpeta`: cualquier archivo del proveedor en el árbol elegido, no solo de imágenes — también cuentan fichas) y con el filtro manual de un único proveedor (cubre el caso extremo de una carpeta de proveedor totalmente vacía, sin ni siquiera fichas).

### Verificación
`node --check` sobre los archivos de backend tocados; `npm run build` (Vite) sin errores sobre el frontend completo. El flujo completo contra Supabase (migración, subida marcando `es_generica`, y borrado real al retirar "SIN IMAGEN" de una carpeta) se verificará por primera vez en el Render de Víctor — este entorno no tiene acceso a esa base de datos.

## [1.19.15] - 2026-08-31

### Añadido
- **Un mismo proveedor puede tener varias "marcas" del mismo DALI.** Víctor, volviendo a Catálogo DALI tras varias entregas en Control de Pedidos, con capturas del panel de "Proveedor asignado" de un artículo: "un mismo dali puede tener varios codigos de proveedores, pero un mismo proveedor tambien puede tener varios codigo proveedor en un mismo dali, por ejemplo, si el proveedor CADELSA nos suministra arroz vaporizado, pero tiene varias marcas a parte de la asignada, tambien deberia poder guardar la info de estas otras marcas por seguridad y control de las fichas e imagenes". Hasta ahora `codigos_proveedor`/`imagenes`/`fichas` guardaban como mucho UNA referencia por (artículo, proveedor) — suficiente para "varios proveedores por DALI" (ya existía, es la lista de "alternativas"), pero no para varias referencias del MISMO proveedor. Decisiones tomadas con Víctor antes de implementar: cada marca se identifica solo por su propio código (sin nombre de marca aparte) y, por ahora, se gestiona solo a mano desde la ficha de administración del artículo — la carga masiva por carpetas no se toca en esta entrega. Tablas nuevas (`marcas_proveedor`, `marcas_proveedor_imagenes`, `marcas_proveedor_fichas`, ver migración `2026-08-31_marcas_proveedor.sql`), separadas de las tablas "principales" a propósito: ninguna consulta ya existente (documentación faltante, exportación a Excel/zip, carga masiva) cambia de comportamiento, las marcas extra son siempre un añadido de reserva, nunca sustituyen a la referencia principal de cada proveedor. `ArticuloForm.jsx` muestra, dentro de la tarjeta de CADA proveedor (asignado, buscado o cualquiera de "otras alternativas"), una sección nueva "Otras marcas de [proveedor]" con cada marca ya guardada (código editable, imagen, fichas técnica/seguridad, botón "Eliminar esta marca" que borra código+imagen+fichas juntos) y un formulario para añadir una marca nueva con solo su código.
- **Fusionar proveedores ahora también traslada sus marcas.** Efecto colateral necesario del punto anterior: `marcas_proveedor.id_proveedor` tiene `on delete cascade` sobre `proveedores` — sin más cambios, fusionar dos proveedores (Admin → Fusionar proveedores) habría borrado en silencio todas las marcas extra del proveedor de origen al borrarlo al final de la fusión, justo la documentación "de reserva" que esta funcionalidad existe para proteger. `fusionarProveedores` (`proveedoresController.js`) traslada ahora también las marcas del origen al destino (o las descarta, con su imagen/ficha, si el destino ya tenía una marca con el mismo código para el mismo artículo) antes de borrar el proveedor de origen. El resumen de "Ver resumen antes de fusionar" (`resumenProveedor`) y el aviso final de la fusión (`AdminProveedores.jsx`) incluyen ahora también el recuento de marcas.

### Verificación
`node --check` sobre los 4 archivos de backend tocados; `npm run build` (Vite) sin errores sobre el frontend completo; en modo demo, con Playwright: la sección "Otras marcas de [proveedor]" aparece dentro de la tarjeta de un proveedor con su formulario de alta, y el intento de añadir una marca muestra correctamente el aviso "necesita el backend real" (esperado en demo, sin backend real que consultar) sin errores de consola nuevos. La migración SQL y el flujo completo de alta/edición/borrado de una marca contra Supabase se verificarán por primera vez en el propio Render de Víctor — este entorno no tiene acceso a esa base de datos.

## [1.19.14] - 2026-08-31

### Cambiado
- **"Documentación faltante": un único correo a todos los contactos principales, no uno por cada uno.** Corrección sobre el enfoque de v1.19.13 (todavía sin desplegar): Víctor, al revisar la explicación del arreglo anterior: "si hay tres correos marcados con la estrella en un proveedor, se envian 3 correos por separado? esto no es correcto, se debe enviar un unico correo pero a todos los destinatarios a la vez". Tenía razón — y Control de Pedidos ya tiene el patrón correcto en otro sitio de su propio código (reclamación automática a proveedor por pedido retrasado): un solo campo `destinatario` con todas las direcciones unidas por ", ", que EmailJS (el mecanismo de envío real) reparte como destinatarios reales de un único correo. `encolarEmailDocumentacionFaltante` (`documentacionController.js`) pasa de encolar un correo por destinatario a encolar uno solo, con `destinatarios.join(", ")`. Sin cambios en el frontend ni en Control de Pedidos — ninguno de los dos necesitaba tocarse para esto.

## [1.19.13] - 2026-08-31

### Arreglado
- **El correo de "Documentación faltante" solo llegaba a uno de los contactos marcados como principales en Control de Pedidos.** Víctor, tras revisar el envío real a MILO CANARIAS ALIMENTACION, SL (con Juan Pedro y Nicet Marquez marcados los dos con la estrella "principal" en Control de Pedidos): "porque se envio solo al primer correo si tengo los dos marcardos para envio? la ficha de proveedores de control pedidos tiene la opcion de marcar aquellos correos qu estan destinados al envio". Causa: `resolverEmailProveedorEnControlPedidos()` (`controlPedidosEmailBridge.js`) leía únicamente el campo de compatibilidad `email_principal` que expone `GET /api/externo/dali-sap/proveedores` — un único valor que control-pedidos-princess arma quedándose con solo uno de los contactos marcados — en vez de recorrer el array `contactos` completo (que sí viaja en esa misma respuesta, con el flag `es_principal` de cada uno). Ahora se recorren todos los contactos marcados como principales y se encola un correo por cada uno (`resolverEmailsProveedorEnControlPedidos`, ahora en plural), igual que ya hace Control de Pedidos para sus propios avisos a proveedores con varios contactos principales a la vez. También corregido en el listado de "Documentación faltante" (que ahora muestra todos los emails, separados por coma, en vez de solo el primero) y en la resolución por lotes usada para calcularlo. Sin cambios en el frontend — ni el `mailto:` ni el mensaje de "en cola" necesitaban tocarse, ambos ya admitían varios destinatarios separados por coma.

## [1.19.12] - 2026-08-31

### Añadido
- **Exportar documentación en zip, organizada por proveedor.** Víctor, tras confirmar que el límite del bucket de Supabase Storage (10 MB, sin relación con el código de la app) era la causa real de que la 10075 siguiera sin subir pese a la v1.19.10/v1.19.11: "existe alguna manera de que se pueda descargar todo organizado? es decir, carpeta nombre proveedor, dentro carpetas FICHAS TECNICAS, FICHAS SEGURIDAD e IMAGENES y dentro de cada una sus respectivos archivos simplemente nombrados con el codigo del proveedor? de esta manera tendria una copia limpia de lo que ahora mismo esta ok". Nuevo endpoint `GET /admin/documentacion-zip` (`exportZipController.js`, backend) que genera al vuelo, por streaming (sin acumular nada en memoria ni disco), un zip con exactamente esa estructura — la misma que espera `CargaMasivaModal.jsx` al volver a subir — a partir de lo que ya hay guardado en `fichas`/`imagenes`. Cada archivo se nombra con el código de proveedor guardado en `codigos_proveedor`; si un artículo todavía no tiene código de proveedor grabado (el mismo caso "no encontrado" de la carga masiva), se incluye igual pero como `SIN-CODIGO-DALI-<código dali>` para no perderlo. Nueva pestaña "Exportar documentación" en el menú de administración (`AdminExportarZip.jsx`), con selector opcional de un proveedor concreto o "Todos" (puede tardar varios minutos con el catálogo completo). Nueva dependencia en el backend: `archiver`.

## [1.19.11] - 2026-08-31

### Añadido
- **Aviso propio para archivos demasiado pesados en carga masiva.** Víctor, tras el arreglo del límite de tamaño en v1.19.10: "pudes poner un avsio para que cuando la carga encuentre archivos pesados, no los cargue, pero indique cual para saber y detectar el problema". Antes, un archivo por encima del límite (5 MB imágenes, 20 MB fichas) se detectaba solo al intentar subirlo, y el error quedaba como una fila roja más entre decenas de filas verdes en la tabla de resultados — fácil de no ver, como pasó con la ficha técnica del artículo 10075. Ahora `CargaMasivaModal.jsx` comprueba el tamaño de cada archivo AL ELEGIR LA CARPETA, antes de intentar nada: los que superan el límite no generan ni siquiera una fila de subida (no se intentan subir) y se listan aparte, en un aviso bien visible desde el primer momento, con su nombre, su peso real y el proveedor al que pertenecen. El aviso se mantiene visible durante todo el proceso, y la "Carga finalizada" final también recuerda cuántos se quedaron fuera por peso.

## [1.19.10] - 2026-08-31

### Arreglado
- **Carga masiva de fichas técnicas: límite de tamaño demasiado bajo (10 MB).** Víctor reportó que la carga masiva de MILO CANARIAS ALIMENTACION, S.L. no grababa la ficha técnica del artículo con código de proveedor `10075` (CENTRO JAMON IBERICO DESHUESADO), pese a que el archivo `10075_JAMON DE CEBO IBERICO NICO.pdf` estaba en la carpeta correcta con el nombre correcto (adjuntó un `dir` de PowerShell de la carpeta). El archivo pesa 15,03 MB — superaba el límite de 10 MB que `subirFichaArticulo` (`storageController.js`) aplica a toda ficha técnica o de seguridad, devolviendo un error 400 claro que la carga masiva sí muestra por fila, pero que con decenas de filas es fácil pasar por alto entre las que sí se suben bien. Subido a 20 MB (`LIMITE_TAMANO_FICHA`), con margen sobre este caso real. El mensaje de error, si se supera igualmente, ahora indica el peso real del archivo en vez de un texto fijo.

## [1.19.9] - 2026-08-31

### Documentado (sin cambio funcional)
- **Norma explícita: el cruce por email para la firma solo usa el email principal.** Víctor, al validar el arreglo de v1.19.8: "tener en cuenta que este mismo correo tambien es correo secundario en otro usuario, asi que podemos poner como norma que solo mire en el primer correo de cada usuario". Ya era así — `GET /api/externo/dali-sap/compradores` en control-pedidos-princess nunca ha seleccionado `email2`, solo `email` — pero no estaba dicho como norma en ningún sitio. Documentado explícitamente en ambos lados del puente (`controlPedidosEmailBridge.js` aquí, y el endpoint en `app.py` de control-pedidos-princess, ver su propio CHANGELOG), para que quede como decisión deliberada y no como un descuido que alguien "arregle" añadiendo `email2` más adelante.

## [1.19.8] - 2026-08-31

### Arreglado
- **Causa real del teléfono ausente: dos usuarios de Control de Pedidos comparten el mismo email.** El log de v1.19.7 lo destapó: `"centralcompras1.canarias@princess-hotels.com" SÍ coincide con "Prueba" en Control de Pedidos, pero no tiene móvil guardado allí` — esa cuenta de pruebas (`usuario prueba`, rol Compras, sin móvil) tiene el mismo email que la cuenta real de Víctor (`comprascan`, rol Admin, con móvil `+34660245366`). `resolverMovilCompradorEnControlPedidos()` usaba `.find()`, que se queda con el primero según el orden de la consulta (`ORDER BY nombre` — "Prueba" ordena antes que "Víctor..."), así que siempre encontraba la cuenta de pruebas. Ahora, si el email coincide con más de un usuario, se prefiere el que sí tiene móvil guardado. Se registra también un aviso cuando esto ocurre, para poder detectar más colisiones de este tipo sin depender de que alguien lo note en un correo real.
- Recomendado (no obligatorio, ya no bloquea nada): en Control de Pedidos → Usuarios, quitarle el email a la cuenta `usuario prueba` o darle uno distinto, para que no siga compartiendo el de una cuenta real.

## [1.19.7] - 2026-08-31

### Añadido
- **Log de diagnóstico ampliado en `resolverMovilCompradorEnControlPedidos()`.** El log de v1.19.6 confirmó que el puente responde SIN error (`Control de Pedidos respondió sin error pero ningún comprador/admin activo tiene ese email exacto guardado allí`) para un usuario que, comprobado por Víctor con una captura de "Editar usuario", sí tiene rol Administrador y móvil relleno. Sin ver la lista real que llega desde Control de Pedidos, no hay forma de distinguir "el endpoint devuelve pocos/ningún usuario" (apuntaría a algo raro en el filtro SQL o en el propio despliegue de esa app) de "el email no coincide letra por letra" (typo, dominio distinto, etc.). Ahora, cuando no hay coincidencia, se registra cuántos comprador(es)/admin(es) llegaron y su lista de emails tal cual; y si SÍ hay coincidencia por email pero sin móvil guardado, se registra también ese caso por separado.

## [1.19.6] - 2026-08-31

### Añadido
- **Log de diagnóstico para el teléfono de la firma.** Víctor confirmó, con el log de despliegue de Render, que el backend ya corre v1.19.5 (petición de imagen ya presente en el texto generado) — pero el teléfono seguía sin aparecer en la firma. `resolverFirmaAdmin()` (`documentacionController.js`) no dejaba ningún rastro de por qué: "sin teléfono" y "el puente con Control de Pedidos falló" eran indistinguibles desde fuera. Ahora, sin cambiar el comportamiento (la firma se sigue generando igual, con o sin teléfono), se registra en los logs de Render de este servicio: `[FIRMA-ADMIN] Sin teléfono para "<email>" — ...` si el puente respondió bien pero no hay coincidencia, o `[FIRMA-ADMIN] No se ha podido resolver el teléfono... <motivo>` si la llamada al puente falló (por ejemplo, si `control-pedidos-princess` todavía no tiene desplegado `/api/externo/dali-sap/compradores`, el motivo sería un 404).

## [1.19.5] - 2026-08-29

### Arreglado
- **Falta la petición de imagen en el correo generado.** Víctor, con la vista previa de un correo real generado tras v1.19.4: "no se incluye la solicitud de imagen de las referencias solicitado". Causa: la frase seguía condicionada a `faltaImagen` (`grupo.articulos.some(a => a.falta_imagen)`) — si NINGÚN artículo del grupo tenía la imagen marcada como faltante (aunque sí les faltara ficha técnica, que es lo que de verdad dispara el correo), la petición de imagen desaparecía entera. Ahora es una petición fija en todo correo de "Documentación faltante", igual que ya son fijos el resto de avisos — no depende de ningún dato del artículo.
- **Sobra la línea "Catálogo DALI · Central de Compras Canarias" después de la firma.** Quedaba de antes de añadir la firma real (v1.19.4) — con la firma completa (nombre, departamento, dirección, teléfono, email) ya al final del cuerpo, esa línea fija de `construirHtmlReclamacionDocumentacion()` quedaba como una segunda firma sin sentido justo debajo. Eliminada.

### Pendiente de confirmar
- **El teléfono de la firma sigue sin aparecer** en la prueba de Víctor, pese a que el usuario tiene el móvil guardado en Control de Pedidos (comprobado con una captura de "Editar usuario": rol Administrador, móvil `+34660245366`). No se ha encontrado ningún error en el cruce por email ni en la consulta del nuevo endpoint — la causa más probable es que `control-pedidos-princess` todavía no tenga desplegada la v12.30.53 (el nuevo `GET /api/externo/dali-sap/compradores`) en el momento de esa prueba; sin ese endpoint en producción, la llamada falla en silencio (por diseño, para no romper el correo) y la firma sale sin teléfono. Pendiente de que Víctor confirme que ambos servicios están desplegados con sus versiones más recientes antes de seguir investigando.

## [1.19.4] - 2026-08-29

### Cambiado
- **Correo de "Documentación faltante" reescrito y con firma.** Víctor, sobre un correo real ya enviado a un proveedor: "¿puedes hacer este correo mas profesional? ... indicar de una manera elegante que si es posible seria bueno que se adjunte imagen de cada una de las referencias asignadas siguiendo la misma pauta de las fichas, como nombre el codigo del articulo ; tambien falta la firma al estilo del resto de correos que se envian a los proveedores desde control pedidos ; en este caso incluir el nombre, telefono, correo del admin que realiza la gestion". Tres cambios en `generarTextoEmail()` (`EmailProveedorModal.jsx`):
  1. Redactado más formal, sin cambiar el fondo del mensaje.
  2. La petición de imagen ya no es una frase suelta: enlaza explícitamente con el aviso de nombrado de archivos, pidiendo que cada imagen se identifique con el código de artículo al inicio del nombre, igual que las fichas.
  3. Firma añadida al final ("Atentamente," + nombre + "Dpto. Central de Compras Canarias" + dirección fija + teléfono + email), con el mismo formato que `_firma_comprador_html`/`_firma_comprador_text` de control-pedidos-princess.

### Añadido
- **Teléfono de la firma resuelto contra Control de Pedidos.** DALI nunca ha tenido un campo de teléfono en su tabla de usuarios. A petición de Víctor ("¿puedes coger la info de la ficha usuarios control pedidos? los admin son los mismos y los compradores son admin en catalogo dali"), el nombre/email de la firma salen de la sesión del admin (`req.user`, sin red) y el teléfono se resuelve cruzando ese email contra los compradores/administradores de control-pedidos-princess, vía el nuevo `GET /api/externo/dali-sap/compradores` de esa app (ver su propio CHANGELOG, v12.30.53) — `resolverMovilCompradorEnControlPedidos()` en `controlPedidosEmailBridge.js`. `GET /admin/documentacion-faltante` ahora devuelve también `firma_admin: {nombre, email, telefono}`. Si el puente falla, no hay ningún usuario con ese email en Control de Pedidos, o no tiene móvil guardado, la firma se genera igual sin esa línea — nunca bloquea la generación ni el envío del correo.
- **Requiere que `control-pedidos-princess` tenga desplegada su v12.30.53** (o posterior) para que el teléfono aparezca — ver nota en `DEPLOY.md`. Sin eso, la firma sigue funcionando, solo que sin teléfono.

## [1.19.3] - 2026-08-29

### Arreglado
- **`CONTROL_PEDIDOS_URL` apuntaba a una URL que devuelve 404 desde fuera.** Víctor reportó, con una captura de "Documentación faltante": `No se ha podido consultar Control de Pedidos para resolver los emails de los proveedores (Control de Pedidos respondió 404.)`. Investigado desde fuera (no es visible en el código de DALI ni de Control de Pedidos, ambos estaban bien): `control-pedidos-princess.onrender.com` devuelve 404 en CUALQUIER ruta, incluida su propia portada — esa app no es alcanzable directamente por su URL de Render, solo a través del Worker de Cloudflare que hace de proxy delante de ella (mismo patrón que ya usa el Organizador para hablar con Control de Pedidos, confirmado en su propio `HISTORIAL_CAMBIOS.md`). `CONTROL_PEDIDOS_URL` (fijada en `render.yaml` el 2026-08-27, cuando se construyó el puente de correos) apuntaba a la URL directa de Render en vez de al proxy — probablemente nunca funcionó desde que Control de Pedidos quedó detrás de ese proxy, o dejó de hacerlo en algún momento posterior sin que nadie lo notara hasta ahora, porque hasta este correo de "Documentación faltante" nada en DALI necesitaba hablar con Control de Pedidos desde el backend.
- **Cambio en `render.yaml`/`.env.example`/`DEPLOY.md`**: `CONTROL_PEDIDOS_URL` pasa a `https://proxy.controlpedidosprincess-canarias.workers.dev`. Cambiar `render.yaml` en el repo NO actualiza el valor de un servicio ya desplegado en Render — hace falta entrar a Render → `listado-DALI-SAP` → Environment y cambiar el valor a mano (documentado también en `DEPLOY.md`).
- Sin cambios de código en `controlPedidosEmailBridge.js` ni en ningún controlador — la lógica del puente siempre estuvo bien, era solo la URL de destino.

## [1.19.2] - 2026-08-28

### Añadido
- **Vista previa real (HTML, con logo y colores) del correo de "Documentación
  faltante".** Víctor: "Necesito reconstruir el apartado envio correo
  Documentación Faltante, debería ser similar a la notificación de alerta al
  proveedor de control pedidos ... en pantalla previa del correo como en
  notificación. Ventana visual correcta con correo logo texto etc". El modal
  (`EmailProveedorModal.jsx`) pedía hasta ahora solo texto plano, sin ninguna
  vista de cómo quedaría el correo real. Ahora, en cada cambio de
  asunto/cuerpo (con el mismo `useDebouncedValue` que ya usan los
  buscadores), pide al backend el HTML ya renderizado —
  `POST /admin/documentacion-faltante/preview-email`, que reutiliza tal cual
  `construirHtmlReclamacionDocumentacion()` (`backend/src/utils/emailHtml.js`),
  la misma función que genera el correo que de verdad se encola — y lo
  muestra en una caja con borde/scroll, igual que hace Control de Pedidos en
  su propio modal de notificación de alerta al proveedor.

### Eliminado
- **El email propio de proveedor guardado en DALI ("Catálogo Dalí").** Víctor,
  en la misma petición: "olvidar el correo grabado en Catálogo Dalí, borrar
  esta info, utilizar únicamente los correos de la base datos proveedores
  control pedidos". Se elimina la columna `proveedores.email` (ver migración
  `2026-08-28_borrar_email_proveedor_dali.sql`, que sustituye a
  `2026-08-25_email_proveedor.sql`) y todo lo que la usaba: el editor inline
  de email en "Documentación faltante" (`AdminDocumentacionFaltante.jsx`),
  el endpoint `PUT /admin/proveedores/:id/email` y su función
  `actualizarEmailProveedor` en `api.js`, y el paso de "Fusionar proveedores"
  que copiaba el email del origen al destino (`proveedoresController.js`,
  `AdminProveedores.jsx`). Control de Pedidos pasa a ser la ÚNICA fuente de
  email para esta app — sin ningún fallback: si un proveedor no tiene email
  allí, "Documentación faltante" no ofrece ningún envío para él hasta que se
  añada en Control de Pedidos → Proveedores.

### Cambiado
- **`resolverEmailProveedorEnControlPedidos()` ya no cae de vuelta al email de
  DALI** (v1.19.1 lo usaba como último recurso) — devuelve `null` sin más si
  el proveedor no existe en Control de Pedidos o no tiene email guardado
  allí. Nueva función `resolverEmailsProveedoresEnControlPedidos()` (versión
  por lotes, una sola llamada a Control de Pedidos para resolver todos los
  proveedores de la pantalla de golpe, en vez de una petición por grupo) en
  `controlPedidosEmailBridge.js`.
- El resultado de "Encolar envío" ya no distingue "email de Control de
  Pedidos" vs "email de DALI" (`origen_destinatario`) porque ahora solo hay
  una fuente posible.

## [1.19.1] - 2026-08-27

### Añadido
- **"Encolar envío" usa ahora los contactos de "Proveedores" de
  `control-pedidos-princess`, no solo el único email guardado en DALI.**
  Víctor, sobre v1.19.0: "como vamos a utilizar el sistema de envios de
  control_pedidos, podriamos utilizar tambien el apartado de proveedores
  con sus correos electronicos etc? de esta manera los tenemos
  unicamente en un unico punto y podemos incluir mas correos para el
  envio, ahora en articulos es solo uno". Antes de encolar, el backend
  intenta resolver el proveedor por NOMBRE exacto contra los
  proveedores de `control-pedidos-princess`
  (`GET /api/externo/dali-sap/proveedores`, ver su `CHANGELOG.md`
  v12.30.27) y usa el contacto marcado como principal allí — donde sí
  puede haber varios contactos por proveedor, a diferencia del único
  `proveedores.email` de DALI. Si no hay proveedor con ese nombre en
  Control de Pedidos, o la consulta falla, se cae de vuelta al email
  propio de DALI sin bloquear el envío — solo falla si NINGUNO de los
  dos lados tiene un email guardado. El modal (`EmailProveedorModal.jsx`)
  muestra ahora el destinatario real confirmado por el backend, indicando
  cuándo viene de Control de Pedidos en vez del email de DALI.

  Confirmado también, a petición de Víctor: el contador de EmailJS
  ("Envíos contados" en Config Alertas de Control de Pedidos) se
  incrementa igual para estos correos encolados desde DALI — pasan por
  el mismo `enviarEmailJS()`/`registrar-envio` que cualquier otro correo
  de la cola.

  Decisión de Víctor sobre el cruce entre las dos apps: en vez de un
  enlace manual proveedor-a-proveedor o un cruce automático con revisión
  de dudosos, va a mantener el nombre de cada proveedor en Control de
  Pedidos idéntico al de DALI — "trabajar sobre una única base" — así
  que el cruce por nombre exacto (normalizado: espacios/mayúsculas
  ignorados, sin nada más "inteligente" que pueda enlazar por error dos
  empresas distintas) es suficiente y no hace falta ninguna pantalla
  nueva de enlace en DALI.

## [1.19.0] - 2026-08-27

### Añadido
- **Envío real de los correos de "Documentación faltante", reutilizando la
  infraestructura de EmailJS de `control-pedidos-princess`.** Víctor:
  "podemos aprovechar la organizacion que tenemos actualmente en
  controlpendidos para el envio de correos y que los correos de
  dalisaparticulos utilice la misma infraestuctura? la idea es que los
  correos para la solicitud de documentacion faltante utilice este
  metodo de emailjs, se podria generar dejar en cola y cuando alguien
  abra control de pedidos se lance, de esta manera podriamos
  reestructurar y hecer mas atractivo y profecional los correos
  electronicos, con logo colores etc". Hasta ahora "Generar email"
  (`EmailProveedorModal.jsx`) solo dejaba copiar el texto o abrirlo en el
  cliente de correo del propio Víctor — sin envío real ni diseño alguno.
  Ahora, un nuevo botón "Encolar envío" manda el texto ya revisado al
  backend (`POST /admin/documentacion-faltante/:idProveedor/encolar-email`),
  que lo convierte en HTML con el mismo logo y colores de cabecera que ya
  usa `control-pedidos-princess` (`backend/src/utils/emailHtml.js`, réplica
  en JS de su `_email_header_html()`) y lo encola en la MISMA cola de esa
  app (`emails_sistema_pendientes`, vía
  `backend/src/services/controlPedidosEmailBridge.js`) — el envío real lo
  sigue haciendo esa app, con su poller ya existente por EmailJS, la
  próxima vez que alguien la tenga abierta (o dentro de los 5 minutos
  siguientes si ya la tiene abierta). Copiar/mailto siguen disponibles
  como alternativa manual, no se han quitado.

  La llamada entre los dos backends (server a servidor, sin sesión de
  usuario) se autentica reutilizando `DALI_SSO_SECRET` — el secreto YA
  compartido entre ambos servicios de Render para el SSO del menú lateral
  "Catálogo DALI" — firmando el cuerpo de la petición con HMAC-SHA256, sin
  mandar el secreto tal cual ni dar de alta ninguno nuevo. Nueva variable
  `CONTROL_PEDIDOS_URL` (con valor por defecto ya puesto en `render.yaml`).
  A petición de Víctor, estos correos comparten la cuenta EmailJS activa
  de `control-pedidos-princess` en vez de tener una cuenta EmailJS propia
  — ver el `CHANGELOG.md` de ese repo (`POST
  /api/externo/dali-sap/emails-pendientes`) para el lado que recibe y
  despacha estos correos.

  De paso, se ha añadido `DALI_SSO_SECRET` a `backend/.env.example`, que
  llevaba tiempo sin esa entrada pese a ser necesaria para el SSO (ver
  `HISTORIAL.md`).

## [1.18.19] - 2026-08-27

### Añadido
- **Filtro previo por proveedor en la carga masiva de imágenes/fichas
  (`CargaMasivaModal.jsx`).** Víctor, sobre las dos capturas del modal:
  "podriamos realizar un filtro previo en la carga masiva de las fichas
  e imagenes? dar opcion a un proveedor o a todos, la idea es que si he
  modificado fichas de un unico proveedor la aplicacion no tenga que
  revisar el total innecesariamente". Nuevo desplegable "Proveedor a
  cargar" (Todos, por defecto, o uno del catálogo) antes de elegir la
  carpeta: con un proveedor concreto seleccionado, cualquier otra
  carpeta de proveedor dentro de la raíz elegida se ignora en silencio
  al clasificar los archivos — no genera fila, así que no dispara la
  comprobación de hash ni de artículo (una petición de red por archivo)
  de documentación que no se va a tocar. Las carpetas que no coinciden
  con NINGÚN proveedor del catálogo se siguen avisando igual que antes,
  filtro o no.

## [1.18.18] - 2026-08-27

### Añadido
- **Columna "Unidad" en el listado exportado (PDF y Excel) para el rol
  Hotel, entre Proveedor y Cantidad.** Petición de Víctor, con un
  `ARTICULOS_DALI.xlsx` real de referencia: la columna C de ese Excel
  ("UNIDAD" — UNIDAD, KILOGRAMO, LITRO…) ya se guardaba en cada
  artículo (`unidad_dali`) al importarlo y ya se traía en la consulta
  de exportación, pero no se mostraba en ningún listado. Con la
  columna "Cantidad" en blanco para rellenar a mano, saber si esa
  cantidad es en unidades, kilos o litros importa tanto como el propio
  número. Solo para Hotel (el listado de Admin no tiene columna
  Cantidad, así que no aplica). Probado generando un PDF y un Excel de
  muestra con datos reales del catálogo — la tabla del PDF, con la
  columna nueva, ocupa 780pt de un ancho útil de 781,89pt en A4
  apaisado: cabe justa, sin desbordar la página.

## [1.18.17] - 2026-08-27

### Cambiado
- **Email de reclamación de documentación (`EmailProveedorModal.jsx`):
  ajustes de redactado a petición de Víctor sobre un correo real ya
  enviado a un proveedor.** Junto al código de proveedor de cada
  referencia a la que le falta ficha técnica se añade ahora también el
  nombre del artículo (la descripción de DALI), "para mejor
  referencia" — un código suelto no siempre le dice nada a quien lo lee
  del lado del proveedor. Se añade una frase aclarando que un archivo
  nombrado únicamente con el código, sin la descripción detrás, también
  es válido — la carga masiva lo asocia sin problema. Y el ejemplo de
  nombre de archivo ya no es un texto fijo igual para todos los
  proveedores ("090102_ARENQUE AL CURRY"): se genera con una referencia
  real de CADA proveedor, de entre las que tiene asignadas y le faltan.

## [1.18.16] - 2026-08-27

### Añadido
- **Código de proveedor fijable también para proveedores alternativos, y
  todas las alternativas visibles a la vez, desde `ArticuloForm.jsx`.**
  Víctor, sobre el cambio anterior: "fijar el código de proveedor de un
  proveedor no asignado si también por favor, ficha completa y
  múltiples alternativas". El campo "Código de proveedor" solo permitía
  fijar el del proveedor ASIGNADO; ahora cualquier tarjeta de proveedor
  del panel (asignado, el que se busque, o cualquiera de la lista de
  abajo) tiene su propio código editable — `PUT
  /admin/articulos/:id/codigo-proveedor` ya aceptaba cualquier
  `id_proveedor` en el body, así que no hizo falta tocar esa parte del
  backend. El panel deja de mostrar una sola "ficha" a la vez (la del
  proveedor buscado en el campo de arriba): ahora lista automáticamente
  TODAS las alternativas que el artículo ya tenga guardadas, cada una
  con su ficha completa (código + imagen + ficha técnica + ficha de
  seguridad, ver/subir/eliminar), sin tener que buscarlas una a una.
  De paso se corrigió un hueco en `GET
  /articulos/:id/fichas-por-proveedor`: un proveedor con el código ya
  fijado pero sin ninguna imagen/ficha todavía no generaba grupo (la
  unión solo se hacía sobre fichas/imágenes), así que ese código quedaba
  invisible para esta gestión — ahora la unión incluye también
  `codigos_proveedor`.

## [1.18.15] - 2026-08-27

### Añadido
- **Documentación alternativa gestionable a mano desde el panel de
  admin del artículo (`ArticuloForm.jsx`).** Víctor: "en la ficha del
  artículo se debería poder incluir documentación alternativa
  manualmente en el mismo apartado admin". El campo "Proveedor" ya
  permitía SUBIR imagen/fichas para un proveedor distinto del asignado
  (quedaban en reserva), pero los indicadores de "ya tiene imagen/ficha
  guardada" y los botones "Eliminar" siempre mostraban y actuaban sobre
  el proveedor asignado, sin importar qué proveedor estuviera
  seleccionado en el buscador — no se podía ver ni borrar la
  documentación en reserva de otro proveedor desde aquí. Ahora el panel
  usa `GET /articulos/:id/fichas-por-proveedor` (el mismo endpoint del
  panel "Ver alternativas" de consulta) para mostrar en vivo la
  imagen/fichas del proveedor que esté seleccionado en cada momento
  (o el asignado, si no se ha escrito nada), con su propio estado
  "sin guardar todavía" cuando no tiene nada. El aviso de "tiene
  documentación en reserva de otro(s) proveedor(es)" ahora lista los
  nombres como botones que rellenan el buscador directamente. `DELETE
  /admin/articulos/:id/imagen` y `.../fichas/:tipo` aceptan un
  `id_proveedor` opcional por query string (por defecto, el asignado —
  compatible con las llamadas existentes) para poder borrar la reserva
  de un proveedor concreto sin tocar la del asignado.

## [1.18.14] - 2026-08-27

### Arreglado
- **Carga masiva: un código de proveedor compartido por varios DALI no
  se emparejaba con NINGUNO de ellos.** Caso real de Víctor: PROQUIMIA
  usa el código 4029017 tanto para el DALI 24004 (ASEPCOL PLUS BOTELLA
  1 LITRO) como para el 24195 (ASEPCOL PLUS GARRAFA 25 LITROS) — mismo
  producto químico en formatos distintos, con la misma documentación
  para los dos. `codigos_proveedor` nunca tuvo restricción de unicidad
  por (proveedor, código) — solo por (artículo, proveedor), así que el
  caso es legítimo — pero la consulta que busca el artículo por
  proveedor+código pedía una única fila (`.maybeSingle()`) y fallaba en
  cuanto había más de una; ese error 500 lo convertía `api.js` en
  silencio en `{ encontrado: false }`, así que el archivo caía en
  "no se encontró ningún artículo" sin subirse a ninguno de los dos.
  `GET /admin/articulos/por-codigo-proveedor` devuelve ahora todos los
  código DALI que comparten proveedor+código (`codigos_dali`, array);
  `CargaMasivaModal.jsx` sube el mismo archivo a cada uno de ellos y
  combina el resultado en una sola fila (si alguno falla entre varios,
  la fila entera se marca en error con el detalle de cada artículo, en
  vez de darse por buena a medias).
  - `backend/src/controllers/storageController.js`
    (`buscarArticuloPorCodigoProveedor`),
    `frontend/src/services/api.js`,
    `frontend/src/components/admin/CargaMasivaModal.jsx`.

## [1.18.13] - 2026-08-27

### Añadido
- **"Ver alternativas de otros proveedores" ahora incluye también la
  imagen de cada proveedor, no solo sus fichas técnica/seguridad.** La
  documentación por proveedor (imagen y fichas) ya se conservaba
  siempre "en reserva" al cambiar el proveedor asignado a un
  artículo — cambiar `id_proveedor` en `actualizarArticulo` nunca ha
  tocado `fichas`/`imagenes` de ningún proveedor — y el panel de
  alternativas de la ficha ya mostraba esas fichas guardadas; pero la
  imagen se quedaba fuera aunque estuviera guardada igual de segura.
  Ahora `GET /articulos/:id/fichas-por-proveedor` también consulta
  `imagenes` y agrupa por proveedor la unión de fichas + imagen (un
  proveedor puede tener solo imagen, sin ninguna ficha, y aparece
  igualmente como grupo), y `ArticuloDetail.jsx` pinta una miniatura
  con enlace a tamaño completo dentro de cada grupo de alternativas.
  - `backend/src/controllers/articulosController.js`
    (`obtenerFichasPorProveedor`), `frontend/src/services/api.js`,
    `frontend/src/components/ArticuloDetail.jsx`,
    `frontend/src/styles/index.css`.

## [1.18.12] - 2026-08-27

### Arreglado
- **Carga masiva: archivos reales que no se detectaban por falsos
  positivos del formato antiguo.** Aviso de Víctor con la carpeta de
  BIMBO DONUTS CANARIAS SLU (26 archivos, 18 sin subirse). El sistema
  aceptaba dos formatos de nombre a la vez —completo
  (`codigoDali_codigoSap_codigoProveedor_nombre`) y corto (solo
  `codigoProveedor_nombre`)— y probaba primero el completo con una
  regex poco estricta que confundía archivos en formato corto cuyo
  código de proveedor era numérico (`3220 BOQUERON EN VINAGRE ed
  2.pdf` se leía como si "3220" fuera el código DALI y "BOQUERON" el
  código SAP, un artículo que no existe).
  A petición explícita de Víctor ("la carga de fichas e imágenes sería
  más segura si el único código a buscar fuera el del proveedor") se
  elimina por completo el formato antiguo: `PATRON_NOMBRE_COMPLETO` y
  `parsearNombreArchivo()` se borran, y `parsearCodigoProveedorDeNombre`
  (código de proveedor, alfanumérico, seguido de espacio o "_" y el
  nombre del artículo) pasa a ser el único formato admitido en las tres
  cargas masivas (imagen/técnica/seguridad, mismo componente
  `CargaMasivaModal.jsx`). Requiere que el código de proveedor de cada
  artículo esté ya registrado de antemano (a mano o por la carga
  masiva de Excel de códigos de proveedor).
  - `frontend/src/components/admin/CargaMasivaModal.jsx`.
- Aparte del código de la app, se entregó a Víctor un script Python
  independiente (`corregir_nombres_fichas.py`, no vive en este repo)
  para renombrar en bloque los archivos que todavía están en carpetas
  compartidas con el formato antiguo, quitando los dos primeros
  códigos y dejando solo el código de proveedor + nombre.

## [1.18.11] - 2026-08-27

### Añadido
- **Administración · Usuarios: baja definitiva de un usuario**, además
  de la desactivación reversible que ya existía. Aviso de Víctor: no
  había forma de borrar de verdad una cuenta, solo desactivarla.
  Bloquea el auto-borrado y borrar el último admin activo que queda
  (mismo criterio que las demás bajas sensibles de la app). `usuarios`
  no tiene ninguna tabla que dependa de ella por FK, así que es un
  borrado real, sin dejar huérfanos.
  - `backend/src/controllers/usuariosController.js`
    (`eliminarUsuario`), `backend/src/routes/admin.js`
    (`DELETE /admin/usuarios/:id`), `frontend/src/services/api.js`,
    `frontend/src/components/admin/AdminUsuarios.jsx`,
    `frontend/src/components/admin/UsuarioForm.jsx`.

### Arreglado
- **El email de un usuario ya existente no se podía editar**, ni
  siquiera para corregir un carácter (Víctor necesitaba poder añadir
  un "&", p.ej. "chefa.canarias@..." → "chefa&b.canarias@..."). El
  campo estaba deshabilitado a propósito tras el alta; ahora es
  editable también en edición, con aviso de que las cuentas
  aprovisionadas por SSO desde Control de Pedidos necesitan el cambio
  también allí para que se sigan reconociendo como la misma cuenta.
  - `frontend/src/components/admin/UsuarioForm.jsx`,
    `backend/src/controllers/usuariosController.js`
    (`actualizarUsuario`).
- Al construir el diálogo de confirmación de borrado se detectó (no
  reportado por Víctor) que `ConfirmDialog.jsx` no marcaba
  `type="button"` en sus botones — inofensivo en los sitios donde ya
  se usaba (paneles sin `<form>`), pero al aparecer ahora anidado
  dentro del `<form>` real de `UsuarioForm.jsx`, pulsar "Cancelar" en
  el diálogo habría disparado sin querer el guardado del formulario en
  vez de limitarse a cerrar el diálogo.
  - `frontend/src/components/admin/ConfirmDialog.jsx`.

## [1.18.10] - 2026-08-27

### Arreglado
- **Carga masiva de fichas/imágenes: al terminar, el único botón
  disponible seguía diciendo "Cancelar"**, dando a entender que la
  carga (ya completada, con sus fichas subidas de verdad) se podía
  deshacer pulsándolo. Aviso de Víctor con una captura de una carga
  terminada (1946 archivos, 411 sin cambios, 1535 con error) donde
  solo aparecía "Cancelar". La detección de "terminado" tampoco era
  correcta: comparaba `ok + error === total`, que no contaba las filas
  "sin cambios" (ya estaban igual) como terminadas.
  - Nueva condición de "terminado" basada en `pendiente === 0`, banner
    de resumen (✓/⚠ según haya errores) al terminar, botón que pasa a
    decir "Cerrar", y los controles de cierre (✕ y el propio botón) se
    deshabilitan mientras la carga sigue en curso, para no poder
    cerrarla a medias sin darse cuenta.
  - `frontend/src/components/admin/CargaMasivaModal.jsx` — mismo
    componente para las tres cargas masivas (imagen/técnica/seguridad),
    así que el arreglo cubre las tres pantallas de una vez.

## [1.18.9] - 2026-08-27

### Cambiado
- **Texto del email de "Documentación pendiente" reescrito al formato
  que Víctor quiere mandar de verdad.** Antes mezclaba, código a
  código, qué le faltaba a cada artículo; ahora es una lista de viñetas
  con solo los códigos a los que les falta ficha técnica, seguida de
  avisos genéricos (no repetidos por artículo) recordando la ficha de
  seguridad y la imagen si hace falta alguna, las instrucciones de
  nomenclatura de archivo, y un cierre fijo. Verificado reconstruyendo
  con datos reales de OASISFISH (41 códigos "solo seguridad" + 14
  "técnica y seguridad" del aviso de Víctor) y comparando el resultado
  contra el ejemplo que pegó, línea a línea.
  - `frontend/src/components/admin/EmailProveedorModal.jsx`
    (`generarTextoEmail`).

## [1.18.8] - 2026-08-26

### Añadido
- **Nueva pantalla de administración "Fusionar proveedores".** Aviso de
  Víctor: cuando un proveedor cambia de nombre en SAP (ejemplo real,
  BIMBO DONUTS CANARIAS SLU → BIMBO DONUTS CANARIAS S.L.U), la
  importación de Excel lo resuelve por nombre EXACTO
  (`resolverDimensionSimple`, `backend/src/utils/dimensiones.js`) y da
  de alta un proveedor nuevo en vez de reconocer que es el mismo — el
  proveedor viejo se queda huérfano en la tabla, con su documentación
  colgando, y aparece en la ficha del artículo como "otro proveedor"
  con fichas/imagen alternativas (botón "Ver alternativas de otros
  proveedores").
  - Se elige un proveedor "origen" (el que desaparece, normalmente el
    nombre viejo) y uno "destino" (el que se queda). Antes de fusionar
    se muestra un resumen comparando cuántos artículos, imágenes,
    fichas y códigos de proveedor tiene cada uno, para poder comprobar
    de un vistazo que la dirección elegida es la correcta — con aviso
    si el origen tiene MÁS artículos asignados que el destino (señal
    de que puede estar al revés).
  - Al confirmar (con diálogo de confirmación explícito, acción
    irreversible), se traslada al destino todo lo que colgaba del
    origen — artículos asignados, imágenes, fichas, códigos de
    proveedor y email de contacto (si el destino no tenía) — y se
    borra el proveedor de origen. Si el destino ya tenía su propia
    imagen/ficha/código para el mismo artículo, se conserva la del
    destino y se descarta la del origen, nunca al revés; si un código
    de proveedor descartado era distinto al que se conserva, se avisa
    como conflicto en el resultado para revisar a mano.
  - No requiere ninguna migración de base de datos — solo trabaja con
    tablas ya existentes.
  - Archivos: `backend/src/controllers/proveedoresController.js`
    (`resumenProveedor`, `fusionarProveedores`),
    `backend/src/routes/admin.js`,
    `frontend/src/components/admin/AdminProveedores.jsx` (nuevo),
    `frontend/src/services/api.js` (`fetchResumenProveedor`,
    `fusionarProveedores`), `frontend/src/App.jsx`,
    `frontend/src/components/Sidebar.jsx`.

## [1.18.7] - 2026-08-26

### Arreglado
- **Carga masiva de imágenes/fichas: los archivos nombrados solo con el
  código de proveedor dejaban de subirse cuando ese código era
  alfanumérico o SOLO letras (p.ej. "EFIL.pdf", "AKHD.pdf").** Aviso de
  Víctor con una carpeta real de un proveedor (SISTEMAS CANARIOS DE
  CONTROL SL) donde varios códigos son así. La comprobación que
  interpreta el nombre de archivo como "solo código de proveedor"
  (formato corto, sin el resto `codigoDali_codigoSap_..._nombre`)
  exigía que ese código tuviera al menos un dígito, pensada para no
  confundirlo con un nombre de archivo cualquiera sin código (p.ej.
  "catalogo.pdf") — pero esa misma comprobación descartaba de raíz
  cualquier código real que fuera solo letras, sin subir ni la imagen
  ni la ficha y sin más aviso que "el nombre no sigue el formato
  esperado". Se quita la exigencia del dígito: ya no hacía falta como
  red de seguridad, porque el backend exige de todos modos que el
  código coincida exactamente con uno ya guardado en
  `codigos_proveedor` — un archivo que de verdad no trae ningún código
  simplemente no encuentra artículo y cae en el aviso de siempre para
  revisarlo a mano, en vez de descartarse en silencio antes de
  intentarlo.
  - `frontend/src/components/admin/CargaMasivaModal.jsx` —
    `parsearCodigoProveedorDeNombre`.

## [1.18.6] - 2026-08-25

### Añadido
- **"Documentación faltante" ahora referencia cada artículo con el
  código PROPIO del proveedor (no el código DALI/SAP, que no le dice
  nada a un proveedor externo), y permite generar el texto de un email
  reclamando justo lo que le falta a cada uno.** Petición de Víctor:
  poder mandar a cada proveedor un resumen de la documentación (ficha
  técnica, ficha de seguridad, imagen) que le falta aportar, con sus
  artículos identificados con SU código, ya que ni DALI ni SAP les
  interesan.
  - Nueva columna "Código proveedor" en la tabla y en el Excel
    exportado (junto al código DALI, que se mantiene para uso interno).
    Sale de `codigos_proveedor` (ver migración
    2026-08-20_codigos_proveedor.sql); cuando no está capturado
    todavía para un artículo se muestra "—" en la tabla, y en el email
    generado se referencia por el nombre del artículo pidiendo
    explícitamente el código.
  - Cada grupo de proveedor puede guardar ahora un email de contacto
    (campo nuevo, ver migración 2026-08-25_email_proveedor.sql —
    `proveedores` no tenía ningún dato de contacto hasta ahora),
    editable directamente desde la propia pantalla.
  - Botón "Generar email" por proveedor: abre un texto de asunto +
    cuerpo ya redactado con la lista de lo que le falta a cada
    artículo, editable antes de usarlo. Con email guardado, además
    permite abrirlo directamente en el cliente de correo del propio
    Víctor (mailto:); sin email, se copia el texto a mano. **No se
    envía ningún correo desde la app** — no hay integración de envío
    de email configurada (mismo punto pendiente que la recuperación de
    contraseña, aparcado hasta que Víctor elija proveedor de email);
    esta primera entrega genera el texto, el envío lo hace Víctor desde
    su propio correo.
  - `database/migraciones/2026-08-25_email_proveedor.sql` (ejecutar
    manualmente en Supabase antes de desplegar esta versión),
    `backend/src/controllers/proveedoresController.js`,
    `backend/src/controllers/documentacionController.js`,
    `backend/src/routes/admin.js`,
    `frontend/src/services/api.js`,
    `frontend/src/components/admin/AdminDocumentacionFaltante.jsx`,
    `frontend/src/components/admin/EmailProveedorModal.jsx` (nuevo),
    `frontend/src/styles/index.css`.

## [1.18.5] - 2026-08-25

### Cambiado
- **Imagen de la ficha de artículo: ajuste al espacio corregido tras
  feedback de Víctor sobre v1.18.4.** El cambio anterior (`object-fit:
  contain` dentro de un recuadro fijo de ancho completo x hasta 220px de
  alto) evitaba el recorte, pero para fotos que no tenían esa misma
  proporción dejaba un margen más grande de lo necesario — la foto se
  veía pequeña "flotando" dentro de un marco grande. Víctor pidió que la
  imagen aproveche el espacio al máximo sin llegar a distorsionarse.
  Ahora el propio elemento de imagen se dimensiona según la foto real
  (`width`/`height: auto` hasta los límites `max-width: 100%` /
  `max-height: 220px`) en vez de forzarse siempre al tamaño completo del
  recuadro: una foto alta usa el máximo alto disponible sin recortarse
  ni distorsionarse, y una foto ancha sigue usando el ancho completo del
  panel como antes. `frontend/src/styles/index.css`.
- `backend/package.json` sube a 1.18.5 junto con `frontend/package.json`
  (sin cambios de código en el backend) — ver convención de versionado
  más arriba.

## [1.18.4] - 2026-08-25

### Cambiado
- **Imagen de la ficha de artículo: ya no se recorta cuando la foto es
  más alta que ancha (o más ancha que alta) de lo que permite el
  recuadro.** Víctor reportó que con fotos de producto muy verticales se
  perdía el extremo superior o inferior, y preguntó si eso distorsionaba
  la imagen. Aclaración: no la distorsionaba (`object-fit: cover`
  siempre respeta las proporciones), pero sí recortaba lo que sobraba
  del recuadro para llenarlo por completo. Cambiado a
  `object-fit: contain`, que encoge la imagen entera para que quepa
  completa dentro del recuadro sin recortar nada — a cambio puede dejar
  un pequeño margen a los lados o arriba/abajo si la foto no encaja
  exacta, margen que ahora usa el fondo `--surface-sunk` para no parecer
  un hueco vacío. Verificado con una foto de producto sintética (más
  alta que ancha): antes se perdían los bordes superior e inferior,
  ahora se ve la imagen completa. `frontend/src/styles/index.css`.

## [1.18.3] - 2026-08-25

### Arreglado
- **Carga masiva de fichas técnicas/de seguridad/imágenes: archivos con
  el formato completo (código DALI_código SAP_código proveedor_nombre)
  fallaban al subir cuando el nombre usaba un ESPACIO antes del nombre
  del artículo** en vez de "_" (p.ej.
  `01453_10102036_3220 BOQUERON EN VINAGRE ed 2.pdf`, formato real de
  varios proveedores, detectado con la carpeta de AHUMADOS CANARIOS
  SA). El parser exigía "_" en los tres separadores; al no encontrar el
  cuarto, el archivo caía al formato alternativo de "solo código de
  proveedor" y cogía por error el código DALI como si fuera el código
  de proveedor, dando "artículo no encontrado" en todas las filas
  afectadas sin subir nada. Ahora se acepta "_" o espacio indistintamente
  justo antes del nombre del artículo; los tres códigos en sí (DALI, SAP,
  proveedor) siguen sin poder llevar espacios ni "_", así se sigue
  detectando con seguridad dónde termina cada uno. Verificado contra los
  30 archivos reales de la carpeta de AHUMADOS CANARIOS SA: los 20 que
  antes fallaban por este motivo ahora parsean correctamente.
  `frontend/src/components/admin/CargaMasivaModal.jsx`.
- `backend/package.json` sube a 1.18.3 junto con `frontend/package.json`
  (sin cambios de código en el backend) — ver convención de versionado
  más arriba.

## [1.18.2] - 2026-08-22

### Cambiado
- **Margen de aceptación del token de SSO reducido de 90s a 20s**, ahora
  que el arreglo de raíz está hecho en el otro lado: el TTL del propio
  token en `control_pedidos` sube de 60s a 100s (repo aparte, con el
  visto bueno de Víctor). Los 90s de v1.18.0 eran un parche temporal
  mientras ese TTL seguía en 60s — con el TTL ya arreglado, el margen
  vuelve a su papel original (solo desfase de reloj/latencia, no cargar
  con todo el cold-start), y de paso se acorta la ventana teórica en la
  que un token interceptado-pero-no-usado podría reutilizarse. Ventana
  total efectiva sin cambios en la práctica: ~120s (100s del token +
  20s aquí), antes ~150s (60s + 90s). `backend/src/controllers/authController.js`.
- `backend/package.json` y `frontend/package.json` suben a 1.18.2 (sin
  cambios de código en el frontend) — ver convención de versionado más
  arriba.

## [1.18.1] - 2026-08-22

### Cambiado
- **Aviso de "alternativas de otros proveedores" en la ficha del
  artículo, ahora en recuadro y con texto genérico**: sustituye al
  simple borde a la izquierda de v1.17.2, que se veía poco (casi se
  perdía junto a la imagen). Ahora es un pequeño recuadro con icono, en
  tono neutro (brass, no rojo/vino — esto es información, no una
  advertencia). El texto deja de listar los nombres de los proveedores
  ("En reserva de: X, Y") y pasa a ser genérico ("Hay alternativas de
  otros proveedores disponibles para este artículo"), usando la misma
  terminología que el botón "Ver alternativas de otros proveedores" que
  ya existe más abajo en la misma ficha — evita repetir la misma
  información dos veces en la misma pantalla. Los nombres concretos
  siguen disponibles al pasar el ratón por encima (tooltip).
  `frontend/src/components/ArticuloDetail.jsx`,
  `frontend/src/styles/index.css`.
- `backend/package.json` sube a 1.18.1 junto con `frontend/package.json`
  (sin cambios de código en el backend) — ver convención de versionado
  más arriba.

## [1.18.0] - 2026-08-22

### Arreglado
- **Primer acceso del día muy lento y "Comprobando sesión…" colgada,
  incluyendo el acceso automático (SSO) desde control_pedidos**:
  diagnosticado como una combinación de tres plazos demasiado ajustados
  entre sí en el plan gratuito de Render (que duerme el backend tras 15
  min sin tráfico y tarda ~60s o más en despertar — ver informe completo
  en HISTORIAL v0.60): el frontend abortaba la comprobación de sesión a
  los 20s (mucho antes de que un cold-start real terminara), y el token
  de SSO que emite control_pedidos solo era válido ~70s en total (60s +
  10s de margen), una ventana casi idéntica al propio cold-start, sin
  margen real. Se han ampliado ambos plazos en el lado de DALI (sin
  necesidad de tocar control_pedidos, que es una app/despliegue aparte):
  el timeout del frontend sube de 20s a 100s, y el margen de aceptación
  del token de SSO sube de 10s a 90s (ventana total ~150s). La pantalla
  de "Comprobando sesión…" ahora avisa, si la espera se alarga más de 4s,
  de que puede deberse a que el servidor estaba dormido, para que no
  parezca que la aplicación se ha quedado colgada.
  `frontend/src/services/api.js`, `frontend/src/App.jsx`,
  `frontend/src/styles/index.css`,
  `backend/src/controllers/authController.js`.
- **Bug de seguridad menor encontrado de paso, en el mismo código de
  SSO**: la lista antirrepetición de tokens (`_jtiUsados`) limpiaba cada
  token por su caducidad "cruda", sin contar el margen de aceptación —
  con el margen en 10s ya dejaba una ventana de 10s en la que un token
  usado podía reutilizarse sin detectarse; con el margen ahora en 90s
  esa ventana se habría ampliado a 90s de no corregirse. Se guarda ya
  con el margen sumado. `backend/src/controllers/authController.js`.

### Nota
- No se ha tocado nada en `control_pedidos` (repo/despliegue aparte):
  el arreglo "de raíz" —alargar el TTL del propio token de SSO en su
  origen— sigue disponible como mejora futura si Víctor da el visto
  bueno para tocar esa app; de momento el margen ampliado en DALI ya
  cubre un cold-start normal sin depender de ello.
- Pendiente de confirmar aparte: el episodio del 22 de agosto en el que
  el keep-alive externo (cron-job.org) recibió 503 sostenidos durante
  más de dos horas no parece explicado por ninguno de estos tres plazos
  — apunta más bien a un incidente de infraestructura de Render/Google
  Cloud (ver conversación con Víctor del 22-08-2026); no hay nada que
  ajustar en el código para ese caso concreto.

## [1.17.2] - 2026-08-22

### Cambiado
- **Aviso de "en reserva de otro proveedor" en la ficha del artículo,
  más corto y discreto**: el bloque grande en rojo bajo la foto (frase
  completa, fondo de color) se sustituye por una línea corta con un
  borde de color a la izquierda — ocupa mucho menos espacio y se lee
  más profesional. La explicación completa de siempre sigue disponible
  al pasar el ratón por encima. Solo visible para administradores
  (mismo dato de antes). `frontend/src/components/ArticuloDetail.jsx`,
  `frontend/src/styles/index.css`.
- `backend/package.json` sube a 1.17.2 junto con `frontend/package.json`
  (sin cambios de código en el backend) — ver convención de versionado
  más arriba.

## [1.17.1] - 2026-08-21

### Arreglado
- **"Importar Excel": el sondeo de progreso se quedaba sin conexión
  mientras el servidor parseaba los ficheros**: desde v1.15.2, el
  parseo (`XLSX.read()`/`sheet_to_json()`) ya no bloqueaba la petición
  POST, pero seguía siendo código síncrono — mientras se ejecutaba
  (varios segundos con los ficheros reales del catálogo, más aún en el
  plan gratuito de Render) bloqueaba el ÚNICO hilo del proceso entero,
  dejándolo sin poder responder a NINGUNA petición, incluido el propio
  sondeo de progreso. Render terminaba devolviendo 503/429 mientras
  tanto, y el frontend se rendía con "Se ha perdido la conexión
  comprobando el progreso de la importación". El parseo se ha movido a
  un `worker_thread` aparte (nativo de Node, sin dependencias nuevas) —
  el hilo principal queda libre para seguir respondiendo mientras el
  parseo corre en paralelo en otro hilo.
  `backend/src/controllers/importController.js`,
  `backend/src/workers/parsearExcelWorker.js` (nuevo).

### Cambiado
- **`frontend/package.json` se alinea a 1.17.1** (sin cambios de código
  en el frontend) — a partir de esta entrega, ambos `package.json` se
  actualizan siempre juntos, ver nota de convención de versionado más
  arriba.

## [1.17.0] - 2026-08-21

### Añadido
- **Carga masiva de imágenes/fichas: reconoce archivos nombrados solo
  con el código de proveedor**: hasta ahora el nombre de cada archivo
  tenía que seguir el formato completo
  `códigoDali_códigoSap_códigoProveedor_nombre`. Ahora, si no lo sigue,
  se prueba a interpretar que el nombre trae SOLO el código con el que
  el proveedor identifica el artículo (p.ej. `9904.pdf` o `37
  hamb.americana100g.3x25k.pdf`) y se busca en los códigos de proveedor
  ya grabados (a mano, por la carga masiva de Excel, o por script) cuál
  es su código DALI — el proveedor ya se sabe por la carpeta en la que
  vive el archivo, así que con proveedor + código de proveedor basta
  para encontrar el artículo y asignarle la imagen/ficha. Si no hay
  ninguna coincidencia grabada, la fila queda en error para revisarla a
  mano, igual que con el formato completo.
  `backend/src/controllers/storageController.js` (nuevo endpoint `GET
  /admin/articulos/por-codigo-proveedor`), `backend/src/routes/admin.js`,
  `frontend/src/services/api.js`,
  `frontend/src/components/admin/CargaMasivaModal.jsx`.

## [1.15.2] - 2026-08-21

### Arreglado
- **"Importar Excel" fallaba con 502 al subir los ficheros reales del
  catálogo** (~30.000 filas cada uno): el parseo (`XLSX.read()`) de
  ambos ficheros se hacía de forma síncrona, ANTES de responder a la
  petición — con el catálogo ya tan grande tarda varios segundos solo en
  parsear, tiempo de sobra para que el proxy por delante del backend
  cortara la conexión con un 502 antes de llegar a responder con el
  `job_id` del trabajo en segundo plano. Movido dentro del propio
  trabajo en segundo plano (igual que ya estaba troceado el guardado) —
  la petición POST ahora solo comprueba que hayan llegado los dos
  ficheros y responde al momento; un Excel con una columna que falta se
  sigue detectando igual, solo que se reporta unos segundos más tarde
  como trabajo "error" (el frontend ya sondea el estado y ya sabía
  mostrar ese mensaje). `backend/src/controllers/importController.js`.

## [1.16.0] - 2026-08-21

### Añadido
- **Aviso de nueva versión disponible, con recarga automática**: igual
  que ya tiene control_pedidos-princess — la app comprueba en segundo
  plano si se ha publicado una versión nueva (cada 30s los primeros 15
  minutos, cada 60s después) y, si la detecta, muestra un aviso con las
  notas de la versión que NO se puede cerrar sin recargar — solo el
  botón "Recargar ahora", o una cuenta atrás de 5 minutos que recarga
  sola si nadie hace nada. Así una pestaña abierta con la versión vieja
  no se queda trabajando indefinidamente contra ella. Funciona
  íntegramente desde el propio sitio estático del frontend (Render
  Static Site), sin depender del backend: cada `npm run build` escribe
  `version.json` (identificador que cambia en cada build) y una copia de
  `CHANGELOG.md` junto a `index.html`.
  `frontend/vite.config.js`,
  `frontend/src/components/ComprobadorNuevaVersion.jsx` (nuevo),
  `frontend/src/main.jsx`, `frontend/src/styles/index.css`.

## [1.15.1] - 2026-08-21

### Cambiado
- **La carga masiva de imágenes/fichas ya no sobrescribe en silencio un
  código de proveedor distinto al ya guardado**: si el archivo trae, en
  su nombre, un código de proveedor distinto al que ya había en el
  sistema para ese artículo+proveedor, ya no se pisa automáticamente —
  prevalece el código existente y se avisa en el resultado de la fila
  para revisarlo a mano si hace falta corregirlo (vía formulario de
  admin). Si no había ningún código guardado todavía, se sigue
  rellenando el hueco automáticamente, igual que antes; si el archivo no
  trae código, tampoco se toca nada, igual que antes. La edición manual
  desde el formulario de admin no cambia — sigue pudiendo corregir el
  código siempre, es la vía pensada justo para eso.
  `backend/src/controllers/storageController.js`,
  `frontend/src/components/admin/CargaMasivaModal.jsx`.

## [1.15.0] - 2026-08-21

### Añadido
- **Filtros automáticos (AutoFilter) en "Exportar Excel"**: Víctor venía
  activándolos a mano en Excel tras cada descarga para tener las
  flechitas de filtro en la cabecera — ahora el propio archivo ya sale
  con ellos activados, desde la fila de cabecera hasta la última fila
  con datos. `backend/src/controllers/exportController.js`.
- **Carga masiva de código de proveedor desde el propio listado
  exportado**: nuevo botón "Carga masiva: Código proveedor" en
  Administración → Artículos — se descarga el listado con "Exportar
  Excel", se rellena/corrige a mano la columna "Código Proveedor" en las
  filas que interesen, y se vuelve a subir ese mismo archivo tal cual,
  sin preparar nada aparte. El código se aplica siempre al proveedor que
  el artículo tiene asignado en ese momento (la columna "Proveedor" del
  Excel es solo informativa); artículos sin proveedor asignado o con un
  código DALI que no existe en el catálogo se reportan aparte, sin
  bloquear el resto. Guardado en bloques de 500 filas (no una petición
  por fila) para no arriesgar timeout con el catálogo completo (~6700
  artículos). `backend/src/controllers/storageController.js`,
  `backend/src/routes/admin.js`,
  `frontend/src/components/admin/CargaMasivaCodigoProveedorModal.jsx`
  (nuevo), `frontend/src/components/admin/AdminArticulos.jsx`,
  `frontend/src/services/api.js`.

## [1.14.0] - 2026-08-21

### Cambiado
- **Cabecera de "Código proveedor" ahora en dos líneas** ("Código" /
  "Proveedor"), igual que "Código DALI" y "Código SAP" — la columna
  ocupaba más ancho del necesario con el título en una sola línea.
  `frontend/src/components/ArticuloTable.jsx`,
  `frontend/src/components/admin/AdminArticulos.jsx`.

### Añadido
- **Código de proveedor también en las exportaciones a Excel y PDF**:
  se veía ya en pantalla (v1.13.0) pero no en "Exportar Excel"/"Exportar
  PDF" — nueva columna "Código Proveedor" entre "Código SAP" y
  "Artículo", mismo criterio que el listado (el código del proveedor
  ASIGNADO, no uno en reserva). `backend/src/controllers/exportController.js`.

## [1.13.1] - 2026-08-21

### Arreglado
- **El buscador no encontraba nada por código de proveedor**: la
  columna nueva de v1.13.0 se veía en la tabla pero el cuadro de
  búsqueda no la tenía en cuenta — reportado por Víctor buscando
  "070221" (un código de proveedor visible en la propia tabla) y
  obteniendo 0 resultados. `q` ahora también compara contra
  `codigos_proveedor.codigo`, exigiendo que el código encontrado sea el
  del proveedor ASIGNADO del artículo (no uno "en reserva" de otro
  proveedor) — así un resultado de búsqueda siempre muestra el mismo
  código por el que se encontró, sin discrepancias. Placeholder del
  buscador actualizado para mencionarlo.
  `backend/src/controllers/articulosController.js`,
  `frontend/src/App.jsx`, `frontend/src/components/admin/AdminArticulos.jsx`.

## [1.13.0] - 2026-08-20

### Añadido
- **Columna "Código proveedor" en el listado de artículos**, entre
  "Código SAP" y "Artículo - DALI" — tanto en "Todos los artículos"
  (pantalla principal, todos los roles) como en Administración →
  Artículos. Muestra el código de v1.12.0 (el que identifica el
  artículo para el proveedor asignado) sin tener que abrir la ficha de
  cada uno. `GET /articulos` ahora también lo incluye por fila (una
  consulta adicional en lotes, no una por artículo listado).
  `backend/src/controllers/articulosController.js`,
  `frontend/src/components/ArticuloTable.jsx`,
  `frontend/src/components/admin/AdminArticulos.jsx`.

## [1.12.0] - 2026-08-20

### Añadido
- **Código de proveedor, visible en la ficha del artículo y en el
  desglose de alternativas**: hasta ahora no existía en ningún sitio el
  código con el que CADA proveedor identifica un mismo artículo DALI
  (distinto del código DALI y del SAP, iguales para todos) — el nombre
  de archivo de la carga masiva ya lo traía desde siempre
  (`codigoDali_codigoSap_codigoProveedor_nombre.ext`) pero se leía y se
  descartaba sin guardarlo. Ahora se guarda: automáticamente al subir
  imagen/ficha por carga masiva (se relanza sobre archivos ya subidos y
  se rellena solo, sin tocar el archivo), y también editable/corregible
  a mano desde el formulario de admin del artículo. Se ve en la ficha
  del artículo, junto al proveedor asignado, y junto a cada proveedor
  del panel "Ver alternativas de otros proveedores" (v1.11.0). Nueva
  tabla `codigos_proveedor` (un código por artículo+proveedor, no por
  tipo de documento — ver migración
  `database/migraciones/2026-08-20_codigos_proveedor.sql`, a ejecutar
  manualmente en Supabase antes de desplegar este backend). Nuevo
  endpoint `PUT /admin/articulos/:id/codigo-proveedor`.
  `backend/src/controllers/storageController.js`,
  `backend/src/controllers/articulosController.js`,
  `backend/src/routes/admin.js`, `frontend/src/services/api.js`,
  `frontend/src/components/admin/CargaMasivaModal.jsx`,
  `frontend/src/components/ArticuloDetail.jsx`,
  `frontend/src/components/admin/ArticuloForm.jsx`,
  `frontend/src/styles/index.css`.

## [1.11.0] - 2026-08-20

### Añadido
- **Botón "Ver alternativas de otros proveedores" en la ficha del
  artículo**: hasta ahora la ficha solo mostraba la documentación
  (técnica/seguridad) del proveedor asignado en ese momento; el resto
  quedaba guardado "en reserva" sin poder verse, salvo un aviso solo
  para admin indicando que existía. A petición de Víctor, ahora
  cualquier usuario (admin u hotel) puede pulsar ese botón y ver, para
  el mismo código DALI, las fichas técnicas y de seguridad de los demás
  proveedores que las tengan guardadas — pensado para comparar
  alternativas del mercado sin tener que reasignar el proveedor primero.
  Se piden solo al pulsar el botón, no de entrada. Nuevo endpoint `GET
  /articulos/:id/fichas-por-proveedor` (agrupa por proveedor, el
  asignado primero). `backend/src/controllers/articulosController.js`,
  `backend/src/routes/articulos.js`, `frontend/src/services/api.js`,
  `frontend/src/components/ArticuloDetail.jsx`,
  `frontend/src/styles/index.css`. Sin cambios de esquema — usa las
  mismas tablas `fichas`/`id_proveedor` de la migración
  2026-08-17_documentacion_por_proveedor.sql, y no toca la imagen.

## [1.10.0] - 2026-08-20

### Cambiado
- **Carga masiva (imágenes/fichas) procesa los archivos en paralelo en
  vez de uno detrás de otro**: Víctor reportó que el proceso se sentía
  lento con carpetas de miles de archivos. La causa real no era el
  aviso del navegador al elegir la carpeta (eso es instantáneo, es
  comportamiento estándar de `<input webkitdirectory>` y no depende de
  la app), sino que `handleProcesar()` subía los archivos
  secuencialmente, esperando en cada uno a que terminasen sus dos
  peticiones de red (buscar el artículo + comprobar el hash) antes de
  pasar al siguiente. Ahora se procesan hasta 6 archivos a la vez
  (reparto por trabajadores, no por bloques fijos: en cuanto uno
  termina, coge el siguiente pendiente), acortando notablemente el
  tiempo total en carpetas grandes sin saturar el backend (plan
  gratuito de Render, un único proceso). El resultado por archivo
  (subido / sin cambios / error) es el mismo de siempre, solo cambia el
  orden en que se completan. `frontend/src/components/admin/CargaMasivaModal.jsx`.

## [1.9.1] - 2026-08-20

### Arreglado
- **Importar Excel avisaba de "cambio de código SAP" en casi cualquier
  artículo, aunque el código no hubiera cambiado**: tras desplegar
  v1.9.0, Víctor reportó 946 artículos marcados en "Revisar
  imagen/ficha técnica" con avisos como `código SAP: "10200425" →
  "10200425"` — idénticos a simple vista. Causa: `codigo_sap` (y el
  resto de campos de texto que vienen del Excel de SAP: unidad,
  categoría de valoración, tipo de producto, grupo de compras, etc.)
  es una columna `text` en Supabase, pero `XLSX.utils.sheet_to_json()`
  tipa cada celda según cómo la ve Excel — una celda con un código
  puramente numérico sin formatear como texto en el Excel de origen
  se lee como un `number` de JS. La comparación de cambios hacía
  `"10200425" !== 10200425`, que en JavaScript es `true` por ser de
  tipos distintos, aunque el valor sea idéntico como texto — avisaba
  de un cambio inexistente en cualquier artículo con código SAP
  numérico, en todas las importaciones. Confirmado reproduciendo el
  caso exacto con la propia librería `xlsx`. Corregido convirtiendo
  todos esos campos a texto (o `null` si están vacíos) al leerlos del
  Excel, antes de compararlos o guardarlos —
  `backend/src/controllers/importController.js`. Sin cambios de
  esquema ni de comportamiento salvo dejar de generar avisos falsos.

## [1.9.0] - 2026-08-20

### Cambiado
- **"Procesar importación" (Excel) deja de ser una única petición HTTP
  que aguanta todo el proceso**: con el catálogo ya lo bastante grande,
  esa petición se estaba cortando a mitad de camino (502, cuerpo vacío,
  ~39s) porque el proxy delante del backend (Cloudflare Worker o el del
  plan gratuito de Render) no esperaba tanto — reportado por Víctor.
  Ahora `POST /admin/import-excel` valida los ficheros y responde AL
  MOMENTO con un `job_id`; el guardado real (resolver dimensiones +
  bloques de 500 artículos) sigue corriendo en segundo plano en el
  mismo proceso, y el frontend sondea `GET
  /admin/import-excel/estado/:jobId` cada 2s hasta ver "completado" o
  "error", pintando una barra de progreso ("bloque X de Y") mientras
  tanto. Ninguna conexión HTTP individual necesita quedarse abierta más
  que el tiempo de una consulta de estado, así que da igual cuánto siga
  creciendo el catálogo — no depende de ningún timeout de proxy.
  `backend/src/controllers/importController.js`,
  `backend/src/routes/admin.js`, `frontend/src/services/api.js`,
  `frontend/src/components/admin/ImportarExcel.jsx`. Sin cambios de
  esquema — el estado de cada importación vive en memoria del proceso
  (se pierde si el servidor se reinicia a mitad, igual que antes; se
  olvida solo a los 30 min de terminar).

## [1.8.0] - 2026-08-20

### Añadido
- **Buscador en "Documentación faltante"**: campo de texto para filtrar
  por artículo, código DALI o proveedor, igual que el del catálogo
  principal — filtra en el propio navegador (los datos ya están cargados
  de golpe) y despliega automáticamente los grupos de proveedor con
  coincidencias, sin tener que ir abriéndolos uno a uno.
  `frontend/src/components/admin/AdminDocumentacionFaltante.jsx`.
- **Indicador de imagen genérica vs. propia**: en esa misma pantalla, la
  columna "Imagen" distinguía solo "falta" (❌) o "está" (✓), sin decir
  si esa foto es una específica del artículo o la genérica de reserva
  del proveedor ("SIN IMAGEN", ver carga masiva) — ambas se veían
  idénticas, dando a entender que ya no había nada que reclamar cuando
  en realidad seguía faltando una foto propia. Ahora, cuando la imagen
  guardada coincide byte a byte (mismo `hash_sha256`) con la de otro
  artículo del mismo proveedor, se marca como "✓ (genérica)"; si no hay
  forma de saberlo (fila subida antes de que se empezara a guardar el
  hash, v1.7.0), se marca "✓ (sin verificar)". No hace falta ninguna
  columna ni migración nueva — se calcula a partir del hash que ya se
  guarda desde v1.7.0. `backend/src/controllers/documentacionController.js`,
  `frontend/src/components/admin/AdminDocumentacionFaltante.jsx`.

## [1.7.0] - 2026-08-18

### Añadido
- **Deduplicación por hash SHA-256 en imágenes/fichas**: la carga
  masiva (`CargaMasivaModal.jsx`) resubía siempre todos los PDF/
  imágenes de la carpeta seleccionada aunque el archivo ya estuviera
  guardado tal cual (caso habitual: relanzar la carga masiva sobre la
  misma carpeta compartida para coger solo lo que haya cambiado desde
  la última vez). Se añade la columna `hash_sha256` a `fichas` e
  `imagenes` (`database/migraciones/2026-08-18_hash_documentos.sql`);
  el frontend calcula el hash del archivo local con Web Crypto
  (`frontend/src/utils/hashArchivo.js`) y lo compara contra
  `GET /admin/articulos/:id/documentos-hash` antes de subir — si
  coincide, no se transfiere el archivo. El backend calcula y guarda
  el hash en cada subida real (`backend/src/controllers/
  storageController.js`). Filas ya existentes quedan con `hash_sha256`
  en `NULL` (se rellena solo en la siguiente subida de esa fila).

### Cambiado
- Iconos de "Ficha técnica" y "Ficha de seguridad" en la ficha del
  artículo: los emoji (📄/🛡️, este último se veía casi como una gota en
  algunos dispositivos) se sustituyen por iconos de línea propios, en
  el mismo estilo del resto de la app (como el reloj de "Actualizado"
  en la cabecera) — un documento con líneas de texto para la técnica,
  un escudo con aviso para la de seguridad. `ArticuloDetail.jsx`,
  `styles/index.css`.
- **Carga masiva de imágenes/fichas rediseñada por completo**: ya no se
  pide el proveedor al principio, solo una carpeta raíz de búsqueda. La
  app recorre esa raíz buscando subcarpetas cuyo nombre coincida con un
  proveedor real del catálogo (comparación sin tildes/mayúsculas, mismo
  criterio que antes) y, dentro de cada una, la subcarpeta del tipo que
  corresponda (FICHAS TECNICAS / FICHAS SEGURIDAD / IMAGENES) — en una
  sola pasada se sube documentación de todos los proveedores presentes
  en la carpeta, no solo de uno. Cada imagen/ficha queda asociada tanto
  al artículo como al proveedor concreto de cuya carpeta vino; en la
  ficha del artículo se muestra siempre la versión del proveedor que
  tiene asignado en ese momento — el resto queda guardado en reserva y
  pasa a mostrarse solo (sin volver a subir nada) si el proveedor
  asignado cambia más adelante, p.ej. tras reimportar el Excel. Las
  carpetas que no coinciden con ningún proveedor se omiten y se avisan
  al final, sin bloquear el resto de la carga.
  `frontend/src/components/admin/CargaMasivaModal.jsx`,
  `frontend/src/services/api.js`.
- Ficha individual (`ArticuloForm.jsx`, botón "Imagen / Fichas"): el
  campo suelto "Código de proveedor" desaparece — el buscador de
  proveedor ya existente resuelve directamente el proveedor real al que
  se asocia la subida (o el ya asignado al artículo, si se deja en
  blanco), igual que en la carga masiva.
- Base de datos: imagen y fichas pasan de "una por artículo" a "una por
  artículo y proveedor" — nueva tabla `imagenes` (antes solo existía la
  columna `articulos.url_imagen`) y `fichas` gana `id_proveedor`. Ver
  `database/migraciones/2026-08-17_documentacion_por_proveedor.sql` y
  `database/schema.sql`. Las columnas antiguas
  (`articulos.url_imagen`, `articulos.codigos_proveedor_adjuntos`) se
  dejan sin borrar como histórico, pero la aplicación ya no las usa.
- Los avisos de "imagen/fichas de varios proveedores" (antes basados en
  `codigos_proveedor_adjuntos`, que ya no se actualiza) pasan a usar el
  dato real y siempre al día — se reformulan como aviso informativo
  ("hay documentación en reserva de otro proveedor"), no como anomalía
  a revisar. `ArticuloDetail.jsx`, `ArticuloForm.jsx`. El indicador
  equivalente en el listado de administración (`AdminArticulos.jsx`) se
  retira: ese dato no se puede calcular fila a fila sin consultas
  adicionales por artículo, y mostrar el antiguo (congelado) era peor
  que no mostrar nada.

### Corregido
- **Carga masiva: proveedores con punto final en el catálogo no
  casaban con su carpeta**. 17 proveedores tienen en el catálogo un
  nombre con punto final (`AHUMADOS CANARIOS, S.A.`) que su carpeta en
  disco no lleva (`AHUMADOS CANARIOS, S.A`); la comparación de nombres
  era una igualdad exacta (solo sin tildes/mayúsculas) y los marcaba
  como "no coinciden con ningún proveedor del catálogo". `normalizar()`
  ahora también recorta espacios y quita puntos finales antes de
  comparar. `frontend/src/components/admin/CargaMasivaModal.jsx`.
- **"Comprobando sesión…" seguía colgándose** entrando por el enlace de
  SSO desde `control_pedidos` (menú lateral "Catálogo DALI") tras un
  rato sin usar la app: el fix de más abajo le puso timeout a la
  comprobación de sesión normal (`fetchSesionActual`), pero
  `ssoLogin()` — la vía habitual de entrada desde `control_pedidos` —
  seguía haciendo un `fetch` sin ningún límite propio; con el backend
  dormido/caído justo al entrar por ese enlace, se quedaba colgada
  igual que antes de aquel fix. Mismo timeout de 20s aplicado también a
  `ssoLogin()` y, por consistencia y prevención, a `login()`.
  `frontend/src/services/api.js`.
- `.github/workflows/keep-alive-dali.yml`: el ping a `/health` fallaba
  ("All jobs have failed") cada vez que el backend llevaba dormido lo
  bastante como para necesitar un cold-start completo de Render Free —
  con `--max-time 30`, una respuesta de 40-60s (típica al despertar el
  servicio) hacía que `curl` cortara por timeout antes de recibir
  respuesta. Subido el margen a 90s y añadido reintento (`--retry 2
  --retry-delay 10 --retry-all-errors`) para que una sola respuesta
  lenta durante el arranque no tumbe el job entero.
- **Bug bloqueante en el frontend**: la pantalla "Comprobando sesión…"
  se podía quedar colgada varios minutos (aviso de Víctor: "SE QUEDA ASI
  UNOS MINUTOS"). `fetchSesionActual()` (`services/api.js`) no tenía
  ningún timeout propio ni manejo de error pese a estar documentada como
  "nunca lanza" — un backend lento (cold-start de Render) o caído dejaba
  el `fetch` pendiente hasta que el propio navegador se rendía por su
  cuenta (minutos), y como `App.jsx` la llamaba sin `.catch()`, si
  llegaba a rechazar la promesa quedaba sin manejar y `sesion` no se
  resolvía nunca. Ahora `fetchSesionActual()` tiene un límite propio de
  20s (`AbortController`) y siempre resuelve o rechaza con un mensaje
  legible; `App.jsx` lo captura y cae al login mostrando ese aviso (mismo
  mecanismo ya usado para errores de SSO), en vez de quedarse en blanco
  sin explicación.

### Documentación
- **Eliminados 3 archivos huérfanos del frontend**, restos de una
  refactorización anterior a la creación de `components/admin/`, que
  no importaba ningún módulo activo y solo generaban confusión por
  compartir nombre con la versión vigente:
  `frontend/src/components/AdminArticulos.jsx`,
  `frontend/src/components/ArticuloForm.jsx` (versiones antiguas, sin
  `CargaMasivaModal` ni el resto de cambios recientes) y
  `frontend/ArticuloDetail.jsx` (duplicado suelto fuera de `src/`, sin
  los iconos de línea de v0.36). Verificado con `esbuild` que
  `App.jsx` compila igual tras el borrado — ninguno estaba en uso.
- `README.md`: se retira el enlace a `docs/hallazgo-seguridad-princess.md`
  (archivo que no se incluye en este repo por tratarse de información
  crítica de otra aplicación); se deja solo la anotación breve del
  hallazgo, sin detalle ni enlace. Mismo criterio aplicado en las dos
  menciones de `HISTORIAL.md` (v0.29 y "Pendientes acumulados").
- `HISTORIAL.md` y `README.md`: limpieza de la lista de pendientes —
  se quitaron 4 puntos ya resueltos en versiones anteriores (ficha
  suelta, CI/CD, URLs firmadas, contraseñas en texto plano de
  `control-pedidos-princess`) que seguían anotados como abiertos. Sin
  cambios de código. Detalle completo en `HISTORIAL.md` → v0.31.
- **Corrección de lo anterior**: la limpieza de v0.31 se aplicó a
  `HISTORIAL.md` pero no llegó a aplicarse en `README.md` — su
  sección "Pendientes generales" seguía listando "login real" y "URLs
  firmadas" como pendientes, ambos ya implementados. Corregido ahora
  al regularizar la versión a 1.7.0.
- `HISTORIAL.md`: nueva entrada v0.38 documentando a posteriori la
  deduplicación por hash SHA-256 (columna `hash_sha256`,
  `hashArchivo.js`, endpoint `documentos-hash`), implementada en el
  código el 2026-08-18 pero sin reflejar hasta ahora ni aquí ni en
  `HISTORIAL.md`.

## [1.6.0] - 2026-08-14

Desplegado y verificado en producción (Render + Supabase) por el usuario.

### Añadido
- SSO desde `control_pedidos` (menú lateral "Catálogo DALI"): nuevo
  `POST /auth/sso` (`authController.js`) que verifica un token firmado
  de un solo uso emitido por ese backend (secreto compartido
  `DALI_SSO_SECRET`, ~60s de validez, antirrepetición por `jti`),
  aprovisiona o actualiza el usuario en `usuarios` con el rol recibido
  (comprador -> `admin`, hotel -> `hotel`) y abre sesión — el usuario
  nunca ve el formulario de login de DALI. En el frontend, `App.jsx`
  detecta `?dali_token=` en la URL al cargar y llama a `ssoLogin()` en
  vez de mostrar el login; si falla, cae al login normal mostrando el
  motivo. Nueva variable de entorno `DALI_SSO_SECRET` (ver
  `.env.example` y `render.yaml`).
- Nuevas columnas `categoria_valoracion` y `tipo_producto` en `articulos`
  (migración `2026-08-14_categoria_tipo_producto_sap.sql`), capturadas
  desde `LISTADO_CODIGOS_DALI_-_SAP.xlsx` tras su cambio de estructura
  del 2026-08-14. Aún no se muestran en ningún sitio del frontend/admin
  — quedan guardadas para cuando se necesiten.

### Corregido
- `importController.js` refrescaba solo `codigo_sap` y `descripcion_sap`
  en cada importación; el resto de metadatos SAP que ya existían en el
  esquema desde el principio (`unidad_sap`, `grupo_productos_sap`,
  `descripcion_grupo_sap`, `indicador_impuestos_sap`,
  `grupo_compras_sap`, `nombre_grupo_compras_sap`) solo se habían
  rellenado una vez, en la carga inicial (`build_csvs.py`) — se
  quedaban congelados con el valor del primer día en cada importación
  posterior desde el panel de Admin. Ahora se refrescan igual que los
  otros dos en cada importación.
- `database/build_csvs.py` leía las columnas de
  `LISTADO_CODIGOS_DALI_-_SAP.xlsx` por posición fija (`r2[3]`, `r2[9]`,
  `r2[11]`...) — con el cambio de estructura del Excel (3 columnas
  nuevas insertadas en medio), esto habría desplazado silenciosamente
  `grupo_compras_sap`, `nombre_grupo_compras_sap` y la comparación de
  `ACTIVO DALI` a las columnas equivocadas, sin ningún error. Ahora
  resuelve el índice de cada columna por su nombre de cabecera (mismo
  criterio que `importController.js`, que nunca tuvo este problema por
  la misma razón), y falla con un mensaje claro si una columna
  esperada no aparece en vez de leer la columna vecina en silencio.

### Verificado en producción
- SSO: probado por el usuario con los tres roles reales de Control de
  Pedidos tras configurar `DALI_SSO_SECRET` en ambos servicios de
  Render — admin → `admin` ✅, compras → `admin` ✅, hotel → `hotel` ✅.
- Import de artículos: confirmado que `listado-DALI-SAP` (el backend
  real de Render) desplegó bien `importController.js`. Detectado y
  resuelto de paso un servicio duplicado (`dali-backend`, creado sin
  querer por el Blueprint sync de Render al no reconocer el nombre del
  servicio real — quedó en "Failed deploy" por variables de entorno
  incompletas) — borrado por el usuario, no afectaba a producción.

## [1.5.3] - 2026-08-14

### Añadido
- Botón "Eliminar" también para la imagen del artículo, con el mismo
  criterio ya aplicado a las fichas en la v1.5.2 (que ya cubría los
  dos tipos, técnica y seguridad, desde el principio — solo faltaba la
  imagen). Nuevo endpoint `DELETE /admin/articulos/:id/imagen`
  (`storageController.js`): borra solo la imagen (Storage +
  `url_imagen`), sin tocar ninguna ficha, con confirmación
  (`ConfirmDialog.jsx`) antes de borrar de verdad — mismo patrón
  "quirúrgico" que `DELETE /admin/articulos/:id/fichas/:tipo`.

## [1.5.2] - 2026-08-14

### Añadido
- Botón "Eliminar" junto a "Ver PDF ya guardado" en la gestión de
  imagen/fichas de un artículo (`ArticuloForm.jsx`): borra esa ficha
  concreta (técnica o de seguridad) sin necesidad de sustituirla por
  otra — antes la única forma de quitar una ficha era subiendo una
  nueva del mismo tipo, no había manera de dejar el hueco vacío. Nuevo
  endpoint `DELETE /admin/articulos/:id/fichas/:tipo`
  (`storageController.js`), distinto de `DELETE
  /admin/articulos/:id/adjuntos` (que borra imagen + las dos fichas de
  golpe, pensado para el caso de un artículo desaparecido del Excel):
  este solo toca la ficha del tipo indicado, ni la imagen ni la otra
  ficha se ven afectadas. Con confirmación (`ConfirmDialog.jsx`) antes
  de borrar de verdad.

## [1.5.1] - 2026-08-14

### Añadido
- Aviso tras cada importación de Excel cuando un artículo con imagen
  y/o ficha subida desaparece del Excel (la fila deja de existir, no
  que se marque `ACTIVO=NO`) — caso raro (un codigo_dali real no
  debería desaparecer del maestro), pero si ocurre por error humano
  ahora queda visible junto al resto de avisos, con un botón "Eliminar
  documentación" por artículo (con confirmación) para limpiar la
  imagen/fichas huérfanas sin tocar el artículo en sí, que sigue
  existiendo tal cual estaba — el `upsert` de la importación nunca
  borra artículos, así que sin este aviso esa documentación se
  quedaría huérfana sin que nada lo hiciera notar. Nuevo campo
  `avisos_desaparecidos` en la respuesta de `POST /admin/import-excel`
  (`importController.js`) y nuevo endpoint
  `DELETE /admin/articulos/:id/adjuntos` (`storageController.js`).
  De paso, `ConfirmDialog.jsx` — que se había quedado sin ningún uso
  desde que se quitó el borrado manual de artículos (v1.4.0) — vuelve
  a tener trabajo, para confirmar este borrado.

## [1.5.0] - 2026-08-14

### Añadido
- Nuevo apartado "Documentación faltante" en Administración: artículos
  activos sin imagen, ficha técnica y/o ficha de seguridad, agrupados
  por proveedor — para poder reclamar a cada uno justo lo que le
  falta, sin tener que revisar el catálogo artículo a artículo. Nuevo
  `documentacionController.js` con `GET /admin/documentacion-faltante`
  (JSON agrupado) y `GET /admin/documentacion-faltante/excel` (mismo
  cálculo, en un .xlsx — una hoja por proveedor, o una sola hoja
  agrupada con columna "Proveedor" si hay más de 20, más manejable que
  decenas de pestañas). El cálculo compara todos los artículos activos
  contra la tabla `fichas` y `articulos.url_imagen` en JS, paginando en
  tandas de 1000 como el resto de exportaciones — no hace falta ningún
  cambio de esquema. Nueva pestaña en el sidebar de Administración,
  lista desplegable por proveedor en pantalla (colapsada por defecto,
  salvo el primer grupo).

## [1.4.5] - 2026-08-14

### Añadido
- Franja fija bajo el título del catálogo, visible para todos los
  usuarios (admin y hotel): fecha de la última importación de Excel,
  total de artículos DALI activos, y de esos, cuántos tienen ya
  código SAP asociado. Nuevo endpoint público `GET /estadisticas`
  (`estadisticasController.js`) — sin tabla de historial de
  importaciones aparte: la fecha se deduce del máximo de
  `articulos.fecha_actualizacion` en toda la tabla, que
  `importController.js` ya actualiza en cada fila al hacer upsert, y
  como el Excel es la única vía para tocar artículos desde v1.4.0, ese
  máximo ES la fecha de la última importación sin necesidad de
  guardarla aparte.

## [1.4.4] - 2026-08-14

### Añadido
- La subida manual de imagen/ficha desde la ficha de un artículo
  (`ArticuloForm.jsx` → `EdicionAdjuntos`) pide ahora, igual que la
  carga masiva por proveedor, un "Nombre del proveedor" (buscador
  autorellenable contra `GET /admin/proveedores`, solo para avisar si
  no coincide con el proveedor real del artículo) y un "Código de
  proveedor" (texto libre, el mismo criterio que en el nombre de
  archivo de la carga masiva) — ambos opcionales. El código, si se
  rellena, alimenta `articulos.codigos_proveedor_adjuntos` igual que
  la carga masiva, así que el aviso de "varios proveedores" (ver
  v1.4.3) ahora detecta también solapamientos que vengan de una
  subida manual, no solo de cargas masivas.

## [1.4.3] - 2026-08-14

### Añadido
- Aviso cuando el mismo `codigo_dali` recibe imagen/fichas de más de
  un proveedor a lo largo de distintas cargas masivas: nueva columna
  `articulos.codigos_proveedor_adjuntos` (`text[]`, sin duplicados),
  rellenada por `POST /admin/articulos/:id/imagen` y `/fichas` cuando
  la carga masiva (`CargaMasivaModal.jsx`) manda el `codigo_proveedor`
  sacado del nombre de archivo — la subida suelta desde la ficha de un
  artículo no lo manda, así que ahí no se toca esta columna. Con más
  de un código en el array, se muestra un aviso en la ficha de
  consulta (`ArticuloDetail.jsx`), en la vista de gestión de
  imagen/fichas del admin (`ArticuloForm.jsx`), y con un indicador "⚠
  varios proveedores" directamente en la fila de la tabla de
  Administración → Artículos, para verlo sin tener que abrir cada
  ficha. Migración
  `database/migraciones/2026-08-14_codigos_proveedor_adjuntos.sql`.
- Confirmado y documentado explícitamente (ya era el comportamiento
  real, ahora con comentarios en el código y en `backend/README.md`):
  cada subida de imagen o ficha sustituye siempre a la anterior — la
  más reciente reemplaza a la más antigua en la misma ruta del bucket
  y en la misma fila de `fichas`, nunca conviven dos versiones para el
  mismo artículo y tipo.

## [1.4.2] - 2026-08-13

### Añadido
- Dos Cloudflare Workers (`cloudflare-workers/dali-proxy.js`,
  `cloudflare-workers/dali-proxy-api.js`) como proxy inverso hacia el
  frontend y el backend en Render — algunos antivirus/filtros
  corporativos bloquean `*.onrender.com` por categoría, y el
  subdominio gratuito `*.workers.dev` de Cloudflare lo esquiva sin
  necesidad de dominio propio. Mismo patrón que
  `proxy`/`proxy-chat` en `control-pedidos-princess`. `CORS_ORIGIN`
  (backend) y `VITE_API_URL` (frontend) actualizados a las URLs de los
  Workers en vez de las `onrender.com` directas — ver `DEPLOY.md`.
  Desplegado y verificado: la URL de acceso diario a la app pasa a ser
  `https://dali-proxy.centralcompras1-canarias.workers.dev` (antes,
  directamente `https://dali-frontend.onrender.com`).

## [1.4.1] - 2026-08-13

### Añadido
- `.github/workflows/keep-alive-dali.yml`: GitHub Actions que hace
  ping a `GET /health` del backend en Render cada 10 minutos, de
  06:00 a 22:00 hora de Canarias, todos los días — para que el plan
  Free no lo duerma por inactividad (Render duerme un servicio Free
  tras ~15 min sin peticiones; el primer request tras dormirse tarda
  decenas de segundos en "despertar"). Mismo patrón ya en uso en
  `control-pedidos-princess`. El cron va en UTC fijo (`*/10 5-21 * * *`)
  cubriendo la unión de invierno (WET, UTC+0) y verano (WEST, UTC+1)
  en vez de dos crons distintos según la época del año — a cambio de
  un margen inofensivo de ~1h de más en cada extremo del horario
  según la estación. Incluye `workflow_dispatch` para poder lanzarlo
  a mano desde la pestaña Actions; probado con una ejecución manual
  (`Success`, 8s) antes de darlo por bueno.

## [1.4.0] - 2026-08-13

### Añadido
- Carga masiva de imágenes/fichas por proveedor, en Administración →
  Artículos: tres botones ("Fichas técnicas", "Fichas seguridad",
  "Imágenes") que abren `CargaMasivaModal.jsx` — buscador de proveedor
  autorellenable (nuevo `GET /admin/proveedores`) + selector de
  carpeta del sistema de archivos (`webkitdirectory`, lee también
  subcarpetas). Cada archivo debe llamarse
  `codigoDali_codigoSap_codigoProveedor_nombreDelArticulo.ext` — se
  usa el código DALI para localizar el artículo y subir el archivo
  (reutiliza los endpoints ya existentes `POST
  /admin/articulos/:id/imagen` y `/fichas`, uno por archivo, sin
  backend nuevo para la subida en sí). Antes de subir nada se muestra
  una vista previa con lo detectado en cada archivo, y tras procesar,
  el resultado fila a fila (subido / error, con motivo). Si el
  proveedor asignado al artículo no coincide con el proveedor
  elegido en el buscador, se avisa pero se sube igual — el código DALI
  del nombre del archivo manda sobre el proveedor.
- Tras cada importación de Excel, aviso destacado al admin con los
  artículos cuya descripción DALI, descripción SAP o código SAP acaba
  de cambiar Y que ya tienen una imagen y/o ficha técnica subida —
  para poder revisar si ese adjunto sigue correspondiéndose con el
  artículo actualizado, en vez de quedar desactualizado en silencio.
  Nuevo campo `avisos_actualizacion` en la respuesta de
  `POST /admin/import-excel` (`importController.js`), calculado bloque
  a bloque comparando el estado justo antes de cada bloque contra los
  valores nuevos; mostrado en `ImportarExcel.jsx` aparte de los
  `avisos` normales.

### Cambiado
- **La edición de artículos desde Administración → Artículos ya solo
  permite subir/sustituir imagen y fichas** — nunca cambiar
  nombre/clasificación/proveedor/código SAP/estado, y se quita por
  completo el botón de dar de baja (borrado) **y el de alta manual**
  ("+ Nueva ficha"). Excel (Administración → Importar Excel) pasa a
  ser la **única vía** para crear, modificar o desactivar un
  artículo, para que la base quede siempre compaginada con el origen
  real DALI-SAP. `ArticuloForm.jsx` ya no tiene ramas ni campos
  editables: siempre es la vista de solo lectura + subida de
  imagen/fichas. Los endpoints `POST /admin/articulos` y
  `PUT /admin/articulos/:id` siguen existiendo en el backend pero el
  panel ya no llama a ninguno de los dos; `DELETE /admin/articulos/:id`
  igual.
- El PDF exportado por un usuario Hotel (o sin sesión) ya no muestra
  la columna "Activo" — no tienen la opción de incluir no activos, así
  que esa columna no les aporta nada — y en su lugar aparece una
  columna "Cantidad" en blanco, con un recuadro dibujado, para poder
  usar el listado impreso como plantilla de pedido. Un admin sigue
  viendo "Activo" como hasta ahora.
- Título del PDF/Excel más ilustrativo cuando el resultado exportado
  es enteramente de un único proveedor (filtres como filtres para
  llegar ahí): en vez de "Listado de Artículos DALI —
  ALIMENTACION · "ORTHI"", pasa a decir directamente "Listado de
  asignaciones de ORTHIDAL SL" — más útil pensando en que este
  listado puede usarse como hoja de pedido. Si el resultado mezcla
  varios proveedores, título genérico con el filtro más específico
  aplicado — solo el nivel MÁS profundo al que se ha bajado (p.ej.
  solo "ALIMENTACION SECA", no "ALIMENTACION · ALIMENTACION SECA"
  encadenados), no toda la cadena de niveles.
- **Exportar Excel rehecho para ser igual que el PDF** en título,
  columnas y estructura — antes tenía sus propias columnas sueltas
  (Nombre/Unidad/Familia/Subfamilia/Proveedor/Código SAP/Activo DALI)
  sin agrupar. Ahora comparte con el PDF, mediante funciones
  extraídas a nivel de módulo (`columnasPdf`, `tituloPrincipal`,
  `nombreGrupo`): mismas 5 columnas en el mismo orden, mismo título
  automático, y el mismo agrupado por familia · subfamilia como filas
  divisorias en vez de columnas de clasificación sueltas. La celda de
  "Cantidad" lleva un borde fino para que se note que es la casilla a
  rellenar, y las filas de artículos no activos (solo visible para
  admin) se pintan en el mismo tono granate que el PDF. Probado
  generando y releyendo un .xlsx real (rol admin y rol Hotel) antes
  de darlo por bueno.

## [1.3.2] - 2026-08-11

### Añadido
- Paginación real en la tabla de artículos: 100 por página, con
  controles "← Anterior" / "Siguiente →" y "Página X de Y" bajo la
  tabla. Corrige un límite ya presente desde antes de esta sesión:
  `fetchArticulos()` siempre pedía `pageSize=3000` fijo sin paginar de
  verdad en la UI, así que "Todas las naturalezas" (~6700 activos, por
  encima de 3000) mostraba el contador de total correcto pero solo
  cargaba y dejaba ver los primeros 3000 — el resto era invisible sin
  ningún aviso. La página se reinicia a 1 al cambiar cualquier filtro
  (naturaleza, familia, subfamilia, búsqueda, incluir no activos).
- Botón "Exportar Excel" en la cabecera del catálogo, junto a
  "Exportar PDF" — mismo patrón (`urlExportarExcel`, análoga a
  `urlExportarPdf`), mismo filtro activo respetado. El backend
  (`exportarExcel`) ya usaba `fetchArticulosParaExport` desde el
  principio, así que hereda gratis el agrupado por familia/subfamilia,
  el troceo por tandas de 1000 y el filtro `todos` ya resueltos para
  el PDF — solo hacía falta el botón. De paso, nombre de archivo
  dinámico según la naturaleza filtrada (`articulos-alimentacion.xlsx`),
  igual que ya tenía el PDF.
- Subida de imagen y fichas técnicas/de seguridad a Supabase Storage:
  nuevo `storageController.js` (`POST /admin/articulos/:id/imagen`,
  `POST /admin/articulos/:id/fichas`), con URLs firmadas (24h de
  caducidad) generadas al consultar el artículo — los buckets son
  privados, nunca se guarda una URL fija. Disponible desde
  `ArticuloForm.jsx` al editar un artículo ya existente (hace falta su
  codigo_dali real, no disponible en el alta hasta guardar), y se
  muestran en `ArticuloDetail.jsx`. `DELETE /admin/articulos/:id`
  ahora borra también la imagen y fichas del Storage, para no dejar
  archivos huérfanos. Migración
  `database/migraciones/2026-08-11_fichas_unique_articulo_tipo.sql`
  (restricción única en `fichas(id_articulo, tipo)`, necesaria para
  poder sustituir una ficha sin duplicarla).

### Corregido
- **Bug real de identificación de artículos:** `GET/PUT/DELETE
  /articulos/:id` y `GET /articulos/:id/fichas` filtraban por el `id`
  interno serial de la tabla `articulos`, pero el frontend siempre
  envía `codigo_dali` en la URL — son valores completamente distintos
  (`codigo_dali` no es la clave primaria). Con miles de artículos, era
  muy probable que algún `codigo_dali` coincidiera por casualidad con
  el `id` interno de OTRO artículo, editando o borrando ese artículo
  equivocado en silencio en vez del que se estaba viendo en pantalla.
  Corregido en los cuatro sitios (`articulosController.js`) para
  filtrar siempre por `codigo_dali`; `obtenerFichasArticulo` resuelve
  primero `codigo_dali` → `id` interno antes de consultar `fichas`
  (cuya FK sí referencia el `id` interno, correctamente, por diseño).

## [1.3.0] - 2026-08-10

### Añadido
- Sidebar con navegación en cascada por la jerarquía completa:
  naturaleza → familia → subfamilia. Al pulsar una naturaleza se
  despliegan sus familias debajo; al pulsar una familia, sus
  subfamilias; cada nivel filtra el listado de artículos en cascada.
  Nuevo endpoint `GET /jerarquia` (árbol completo con IDs, tablas
  pequeñas — 13/53/253 filas — sin paginar) y nuevo estado en
  `App.jsx` (`familiaActiva`, `subfamiliaActiva`) además del
  `naturalezaActiva` que ya existía. En modo demo, el árbol se deriva
  de los artículos de muestra (`mockArticulos`), con cobertura parcial
  (solo lo que aparece en esa muestra, no las 253 subfamilias reales).
- Botón "Exportar PDF" en la cabecera del catálogo — exporta
  respetando el filtro activo (naturaleza, familia, subfamilia y/o
  búsqueda), no siempre el catálogo entero. `GET /export/pdf` y
  `GET /export/excel` (`exportController.js`) ahora aceptan los mismos
  parámetros que `GET /articulos` (`q`, `naturaleza`, `familia`,
  `subfamilia`). De paso corregido un bug ya presente: la exportación
  nunca troceaba la petición a Supabase, así que cualquier exportación
  de más de 1000 artículos (todo el catálogo, o solo ALIMENTACION, que
  ya tiene más de 2000) se cortaba en 1000 en silencio — mismo límite
  de Supabase/PostgREST ya documentado y resuelto en `listarArticulos`
  (v1.0.2), aplicado aquí con el mismo troceo por tandas de 1000.
  Deshabilitado en modo demo (no hay backend real que genere el PDF).
- **PDF reescrito como tabla real**, no volcado de texto plano:
  cabecera de columnas repetida en cada página (Código DALI, Código
  SAP, Artículo, Proveedor, Activo), agrupado por familia/subfamilia
  con fila divisoria en cada cambio de categoría, filas alternadas,
  inactivas resaltadas en granate, numeración de página, fecha de
  generación y total de artículos. El título muestra también familia y
  subfamilia cuando están filtradas, no solo la naturaleza (p.ej.
  "INMOVILIZADO · MOBILIARIO · MOBILIARIO HABITACION").
- Nueva pantalla "Usuarios" en Administración (solo admin), junto a
  Artículos e Importar Excel: alta y edición de accesos (nombre,
  email, rol, contraseña, activo/desactivado). Nuevos endpoints
  `GET/POST /admin/usuarios` y `PUT /admin/usuarios/:id`
  (`usuariosController.js`), con dos protecciones: un admin no puede
  quitarse a sí mismo el rol de administrador ni desactivar su propia
  cuenta (para no dejar la app sin ningún admin activo por un
  despiste). El alta por CLI (`npm run create-user`) se mantiene como
  vía alternativa.

### Cambiado
- Sidebar: anidado en línea (familia justo bajo su naturaleza,
  subfamilia justo bajo su familia) con un único scroll para todo el
  bloque de navegación — "Gestión" y el pie (versión/usuario) fijos
  abajo. Marca del sidebar: "Catálogo DALI" → "Catálogo DALI - SAP".
  Pie del sidebar: versión en píldora con icono de reloj (antes
  etiqueta de equipaje sin icono), "©" delante de "Princess Hotels &
  Resorts", y círculo con la inicial del usuario delante del
  nombre/rol.
- Cabecera de las tablas (consulta y panel de administración) fija al
  hacer scroll — solo se mueve el contenido de las filas. `.main` ya
  no hace scroll como un todo (antes arrastraba también el título y el
  buscador); nuevo `.main-body` separa lo fijo (filtros, contador,
  aviso de error) de lo único que debe moverse (`.table-wrap`, con su
  propio `overflow-y: auto`). `.admin-panel` recibe el mismo
  tratamiento para no cortarse.
- Códigos DALI siempre a 5 dígitos en pantalla (`06153`, no `6153`) —
  nuevo helper `frontend/src/utils/format.js`, aplicado en los 4
  sitios donde aparece la etiqueta dorada. Solo visual: el dato en
  base de datos y la búsqueda no cambian. Cabecera "Código / DALI"
  centrada, igual que ya estaba "Código / SAP".
- Rol `lectura` renombrado a `hotel` en toda la app (tabla `usuarios`,
  `create-user.js`, credenciales demo, etiquetas en pantalla) — mismo
  comportamiento de solo lectura, nombre que refleja mejor quién lo
  usa en la práctica (personal de los hoteles). Migración
  `database/migraciones/2026-08-07_rol_lectura_a_hotel.sql` para la
  base ya desplegada.

### Corregido
- **Hallazgo del Security Advisor de Supabase (ERROR, Security
  Definer View):** `v_articulos_completo` corregida con
  `security_invoker = true` (`database/schema.sql` para instalaciones
  nuevas, `database/migraciones/2026-08-05_view_security_invoker.sql`
  para la base ya desplegada) — sin esto, la vista ignoraba la RLS de
  `articulos` y podía devolver artículos no activos a un usuario
  estándar si algo la consultase alguna vez con una key
  `anon`/`authenticated`. No explotable hoy: el backend solo hace
  joins directos sobre `articulos` con la service_role key, que ya
  bypassa RLS por diseño.
- Buscar un código DALI con ceros a la izquierda (p.ej. `02276`, tal
  como se muestra en pantalla desde el relleno a 5 dígitos) no
  encontraba nada — el filtro comparaba contra el texto real sin
  ceros (`2276`). Ahora, si la búsqueda es puramente numérica, se
  normaliza quitando los ceros a la izquierda solo para la condición
  de `codigo_dali_texto`.
- **`POST /admin/import-excel` fallaba a mitad de importación**
  (`duplicate key value violates unique constraint
  "ux_articulos_codigo_sap"`, visto en el bloque 7 de 61 con el Excel
  real de ~30.000 artículos): cuando un código SAP cambia de un
  artículo a otro entre una importación y la siguiente, el artículo
  que lo tenía antes no se actualiza hasta un bloque posterior — el
  índice único parcial `ux_articulos_codigo_sap` corta el upsert en
  cuanto el bloque nuevo intenta reclamar un código que la base de
  datos todavía asigna al artículo viejo, aunque al terminar toda la
  importación no quedaría ningún duplicado real. Corregido liberando
  (`codigo_sap = null`) cualquier código SAP que un bloque vaya a
  reclamar, justo antes de guardar ese bloque, en `importController.js`.
  Cada reasignación real detectada (código SAP que pasa de un DALI a
  otro entre importaciones — p.ej. una corrección de una asociación
  mal hecha) queda registrada en los `avisos` de la respuesta de la
  importación, en vez de limpiarse en silencio.
- `importExcel()` (frontend) descartaba el mensaje real de error del
  backend y siempre mostraba "Error al procesar la importación" —
  mismo fallo ya corregido antes en `fetchArticulos` (v1.0.8), aquí
  seguía pendiente.
- **Exportar PDF no coincidía con lo que se veía en pantalla:** un
  admin exportaba siempre con los artículos no activos incluidos,
  ignorase o no el checkbox "Incluir no activos". `exportController.js`
  ahora exporta según `todos` (mismo criterio que `listarArticulos`),
  y el botón de la cabecera lo envía (`App.jsx`,
  `urlExportarPdf({ todos: esAdmin && verTodos })`).
- Dos bugs de PDFKit encontrados al probar con datos reales del
  catálogo (30.167 filas, nombres de hasta +80 caracteres):
  1) `ellipsis: true` sin `height` no trunca — hace salto de línea y
     desborda verticalmente sobre la fila siguiente. Corregido con
     `height` + `lineBreak: false` en cada celda.
  2) `doc.switchToPage()` + `text()` no dibuja nada dentro del área
     de margen inferior (bug conocido de PDFKit, no del código del
     proyecto) — así que la numeración de página no aparecía.
     Corregido numerando cada página al vuelo, según se crea, sin
     `switchToPage`, ensanchando el margen inferior a 0 solo mientras
     se dibuja el pie.
- **`usuariosController.js` sin `try/catch`** (única excepción al
  patrón que sí sigue el resto de controladores, p.ej.
  `articulosController.js`): con Express 4, un fallo inesperado
  dentro de una función `async` de una ruta no llega al middleware de
  errores — la petición se queda sin respuesta JSON, y el frontend
  solo puede mostrar su mensaje genérico de repuesto ("Error al crear
  el usuario"), sin ninguna pista real de qué falló. Envueltas las
  tres funciones (`listarUsuarios`, `crearUsuario`,
  `actualizarUsuario`) en `try/catch`. De paso, mensaje específico
  para el código `23514` (`check_violation`) apuntando a la migración
  `2026-08-07_rol_lectura_a_hotel.sql` — el error más probable si esa
  migración todavía no se ha ejecutado en la base de datos.
- Los paneles deslizantes (ficha de artículo, alta/edición de
  artículo, alta/edición de usuario) se cerraban solos al seleccionar
  texto dentro de un campo si el ratón se soltaba fuera del panel por
  poco — el evento `click` de "cerrar al hacer clic fuera" se basa en
  dónde se SUELTA el botón, no en dónde se pulsó, así que un simple
  arrastre de selección podía disparar el cierre sin que nadie
  pulsara nada. Nuevo hook `useCerrarAlClicFuera` (usado en
  `ArticuloDetail.jsx`, `ArticuloForm.jsx`, `UsuarioForm.jsx`): ahora
  exige que el clic empiece y termine en el propio fondo para cerrar.

## [1.2.0] - 2026-08-05

### Cambiado
- Cabecera de la tabla de artículos (`ArticuloTable.jsx`) reordenada y
  renombrada, en dos líneas: "Código / DALI" y "Código / SAP"
  (centrada) para las dos primeras columnas, luego "Artículo - DALI" y
  "Proveedor asignado" (antes Código · Artículo · Proveedor · Código
  SAP en una sola línea). Mismo patrón aplicado también a la tabla del
  panel de administración (`AdminArticulos.jsx`), antes con cabeceras
  simples sin coherencia con la tabla de consulta.
- Etiqueta dorada del código quita el prefijo "DALI-" (ahora solo el
  número, p.ej. `15563`) en los 4 sitios donde aparece: tabla,
  `ArticuloDetail.jsx`, `ArticuloForm.jsx` y `AdminArticulos.jsx` — el
  código SAP sigue en pruebas, el DALI es el principal por ahora.
- Checkbox "Incluir no activos (ACTIVO DALI = NO)" simplificado a
  "Incluir no activos".
- Sidebar (`Sidebar.jsx`) reestructurado: secciones "Principal" y
  "Gestión" (antes "Administración") con cabecera propia, y nuevo pie
  fijo con versión (leída de `package.json`), "Princess Hotels &
  Resorts · Central Compras Princess Canarias", usuario/rol y botón
  "Salir" — antes nombre/rol/cerrar sesión vivían en la cabecera de
  `App.jsx`. Misma paleta marfil/latón/vino de siempre.
- Sidebar y ventana de artículos con scroll independiente (`height:
  100vh` + `overflow-y: auto` cada uno) — el pie del sidebar (versión,
  usuario, Salir) queda siempre visible aunque la tabla de artículos u
  otro contenido central sea más largo que la pantalla.

## [1.1.0] - 2026-08-05

### Añadido
- `render.yaml`: backend fijado a `region: frankfurt` (antes oregon
  por defecto, sin especificar) — más cerca de Canarias. Guía de
  migración paso a paso en `DEPLOY.md` ("Migrar de región"), ya que
  Render no permite cambiar la región de un servicio existente.
- **Migración completada (5 de agosto de 2026):** backend movido de
  Oregon a Frankfurt (servicio antiguo eliminado, verificado en
  producción: login, datos reales, búsqueda). Renombrado en el
  dashboard de `dali-backend-fr` a `listado-DALI-SAP` — la URL pública
  no cambió (`https://dali-backend-fr.onrender.com`), nombre visible y
  URL `onrender.com` son independientes una vez creado el servicio.
  `render.yaml` actualizado con `name: listado-DALI-SAP` para que
  futuros despliegues desde cero (Blueprint) usen ya el nombre
  definitivo.

### Corregido
- **Bug bloqueante:** `POST /admin/articulos` no generaba ni validaba
  `codigo_dali` (`not null unique` en `schema.sql`), y `ArticuloForm.jsx`
  no lo pedía — un alta manual real fallaba siempre por violación de
  NOT NULL. Corregido asignando `codigo_dali` en el servidor (siguiente
  entero libre) al crear, con reintento automático si dos altas
  concurrentes chocan sobre el mismo código; en edición nunca se toca.

### Añadido
- **Login real** por sesión (cookie firmada, `cookie-session`), con
  caducidad diaria — patrón tomado del proyecto `control-pedidos-princess`
  aportado como referencia. Incluye `POST /auth/login`, `POST /auth/logout`,
  `GET /auth/me`, pantalla `LoginScreen.jsx` con la identidad visual del
  proyecto, y `backend/scripts/create-user.js` (`npm run create-user`)
  para dar de alta usuarios desde CLI, ya que no hay autorregistro.
- `DEPLOY.md` — guía de despliegue paso a paso (Supabase → GitHub →
  Render backend → Render frontend → CORS → primer usuario), referenciada
  desde `render.yaml` desde v0.4 pero pendiente de escribir hasta ahora.
- Panel de administración en el frontend, con sección propia en el
  sidebar (visible solo para el rol admin de la sesión):
  - **Artículos** — listado, alta, edición (mismo panel deslizante que la
    ficha de consulta) y baja con confirmación, sobre
    `POST/PUT/DELETE /admin/articulos`.
  - **Importar Excel** — bandeja de entrada para los dos Excel de origen
    y recibo de resultado (procesadas/creadas/actualizadas) con sello
    "Procesado", sobre `POST /admin/import-excel`.
  - En modo demo, ambos operan sobre datos de muestra en memoria, sin
    necesidad de backend.
- **Resolución de dimensiones nuevas en `POST /admin/import-excel`**
  (`backend/src/utils/dimensiones.js`): naturaleza, familia, subfamilia
  y proveedor se resuelven contra sus tablas antes del upsert de
  artículos, dando de alta (`get_or_create`, a prueba de condiciones de
  carrera vía `upsert`+`onConflict`) los nombres que no existían. La
  respuesta del endpoint incluye ahora `dimensiones_creadas` y `avisos`.
  Corrige un fallo silencioso: hasta ahora un Excel con una familia o
  proveedor nuevo dejaba esa fila con la FK a `null` sin avisar.
- **La misma resolución, en el alta/edición manual**
  (`POST/PUT /admin/articulos`): `articulosController.js` reutiliza
  `resolverDimensionSimple`/`resolverDimensionConFk` para traducir
  naturaleza/familia/subfamilia/proveedor (texto libre, tal como los
  manda `ArticuloForm.jsx`) a sus IDs antes de guardar, en vez de
  insertar `req.body` tal cual. Cierra el mismo fallo silencioso que
  `import-excel`, pero disparado por la acción más cotidiana del panel
  de administración: dar de alta una ficha a mano.

### Cambiado
- Auth de JWT en cabecera (`Authorization: Bearer`) a sesión por cookie.
  El toggle demo Usuario/Admin del frontend desaparece: el rol viene
  siempre de la sesión (`GET /auth/me`), nunca de un botón en la UI.
- `usuarios.hash_password` pasa a `not null`; nueva columna
  `usuarios.activo`.
- `render.yaml` y `.env.example`: `JWT_SECRET`/`JWT_EXPIRES_IN` →
  `SESSION_SECRET` + `NODE_ENV`.

### Seguridad
- Las contraseñas se hashean con **bcrypt** antes de guardarse. El
  proyecto de referencia (`control-pedidos-princess`) guarda y compara
  la contraseña en texto plano — deliberadamente no se replicó esa
  parte del patrón (ver `HISTORIAL.md` v0.7).

### Corregido
- Resto de la paleta de color antigua (verde-azulado `rgba(44,95,91)`) en
  el hover de las pestañas del sidebar — no se había actualizado en el
  rediseño a marfil/latón (v0.3).

### Pendiente
- Subida de imágenes y PDF a Supabase Storage con URLs firmadas.
- `POST /admin/articulos` no genera ni valida `codigo_dali` (columna
  `not null unique` en `schema.sql`) — `ArticuloForm.jsx` no lo pide, así
  que un alta manual real hoy falla por violación de NOT NULL. A
  diferencia del resto de pendientes de esta lista, este falla alto y
  claro (el admin ve el error al guardar), no en silencio.
- Paginación y exportación PDF/Excel desde la UI.
- Recuperación de contraseña y verificación por email tras varios días
  sin login (necesitan un proveedor de email; presentes en el proyecto
  de referencia, aquí solo documentadas).
- Tests de integración por endpoint.
- Despliegue en Render (backend) y Render/Vercel (frontend) con CI/CD.

## [1.0.9] — 2026-08-03

### Corregido
- **Buscador lento y con resultados incorrectos al escribir rápido**:
  sin "debounce", cada tecla lanzaba una petición nueva a
  `fetchArticulos` — escribir "EMICELA" disparaba 7 peticiones casi
  simultáneas, cada una con varias consultas a Supabase (búsqueda
  principal + resolución de proveedor), de ahí la lentitud reportada.
  Además, al no cancelarse ni ignorarse las respuestas antiguas, una
  petición anterior más lenta (p.ej. la del campo vacío, antes de
  escribir nada) podía resolver DESPUÉS que la más reciente y
  sobrescribir el resultado correcto con uno obsoleto — eso, y no un
  fallo del filtro en sí, era la causa de ver artículos sin relación
  con el texto buscado.
- Nuevo hook compartido `hooks/useDebouncedValue.js`: retrasa 350ms la
  actualización del texto que dispara la búsqueda, sin afectar a lo que
  se ve mientras se escribe en el campo (eso sigue siendo instantáneo).
- `App.jsx` y `AdminArticulos.jsx`: el `useEffect` que dispara la
  búsqueda ahora usa el valor debounced y lleva una guarda de
  cancelación (`cancelado`/`signalCancelado`) para ignorar la respuesta
  de una petición que ya quedó obsoleta cuando llega tarde, en vez de
  dejar que sobrescriba el resultado de una petición más reciente.

## [1.0.8] — 2026-08-03

### Corregido — el casteo de codigo_dali no funcionaba, ni en v1.0.6 ni en v1.0.7
- **Reportado**: buscar "2276" (código DALI de un artículo existente,
  DALI-2276) daba 0 resultados, con el error visible en pantalla
  `operator does not exist: integer ~~* unknown`.
- **Causa**: dos intentos distintos de castear `codigo_dali` (integer) a
  texto dentro del filtro construido por supabase-js — v1.0.6 dentro de
  un `.or()` compuesto, v1.0.7 en un `.filter()` simple — fallaron
  igual: el casteo `::text` no se estaba aplicando de verdad, así que
  Postgres intentaba `ilike` directamente sobre una columna `integer`,
  que no tiene ese operador definido.
- **Corrección de raíz, a nivel de base de datos**: en vez de seguir
  intentando castear en cada consulta, se añade `codigo_dali_texto`, una
  columna de texto GENERADA (`generated always as (codigo_dali::text)
  stored`) — Postgres la mantiene sola, sin necesidad de ningún UPDATE
  ni de tocarla al crear/editar artículos. Al ser ya una columna `text`
  normal, `ilike` se le aplica exactamente igual que a nombre_articulo o
  codigo_sap, sin casteo ni trucos.
- **Requiere acción manual antes de desplegar**: ejecutar
  `database/migraciones/2026-08-03_codigo_dali_texto.sql` en el SQL
  Editor de Supabase. Sin esa migración, esta versión del backend
  fallará con "column codigo_dali_texto does not exist". `schema.sql`
  también se actualizó para que instalaciones nuevas ya incluyan la
  columna y su índice trigram (mismo patrón que ya existía para
  nombre_articulo — pg_trgm ya estaba habilitado en el proyecto).
- `articulosController.js` simplificado: ya no hace falta la consulta
  aparte para resolver codigo_dali (la que sí seguía siendo necesaria
  para proveedor, por vivir en otra tabla, se mantiene igual).

## [1.0.7] — 2026-08-03

### Corregido — v1.0.6 rompía la búsqueda por completo
- **Reportado**: con una naturaleza activa en el sidebar (p.ej.
  ALIMENTACION), escribir cualquier texto en el buscador (probado con
  "HAMBURG") no filtraba nada — se seguían viendo todos los artículos de
  esa naturaleza, ni por nombre, ni por proveedor, ni por código.
- **Causa**: v1.0.6 metía el casteo `codigo_dali::text.ilike...` DENTRO
  de un `.or()` compuesto junto con las demás condiciones. Esa sintaxis
  de casteo dentro de un `or=(...)` no está documentada con la misma
  certeza que el casteo en un filtro simple, y la petición a Supabase
  fallaba. El fallo real quedaba oculto porque `fetchArticulos` no
  capturaba el error: la pantalla se quedaba mostrando el resultado de
  la búsqueda/naturaleza anterior sin avisar, dando la falsa impresión
  de "no encuentra nada" — nombre_articulo nunca tuvo el problema, es
  que no se estaba aplicando NINGÚN filtro nuevo.
- **Corrección backend** (`articulosController.js`): en vez de un único
  `.or()` compuesto con casteo embebido, ahora se resuelven antes, en
  dos consultas SIMPLES por separado, los `id` de artículo que
  coinciden por código DALI (`codigo_dali::text` en un filtro simple —
  sí documentado por PostgREST) y los `id` de proveedor que coinciden
  por nombre. El `.or()` final de la consulta principal solo combina
  `nombre_articulo.ilike`, `codigo_sap.ilike` (columnas de texto, sin
  casteo) y, si hubo coincidencias previas, `id.in.(...)` /
  `id_proveedor.in.(...)` — comparaciones simples sin casteo ni JOIN.
- **Corrección frontend** (`App.jsx`, `AdminArticulos.jsx`,
  `services/api.js`): se captura ahora el error de `fetchArticulos` en
  vez de dejarlo sin manejar. Si falla, se muestra un aviso visible y se
  vacía la lista (en vez de dejar resultados obsoletos en pantalla que
  parecen un resultado vacío legítimo). `fetchArticulos` propaga además
  el mensaje de error real que devuelve el backend, no un genérico fijo.

### Pendiente de verificar (sin acceso a Supabase en este entorno)
- Repetir aquí la misma prueba que falló: naturaleza ALIMENTACION +
  "HAMBURG", y en general cualquier búsqueda con naturaleza activa, por
  artículo/código DALI/código SAP/proveedor, en Catálogo y en
  Administración.

## [1.0.6] — 2026-08-03

### Añadido
- **Multi-búsqueda en los dos buscadores de la app** (Catálogo y
  Administración · Artículos, ambos comparten el mismo endpoint
  `GET /articulos`): el campo `q` antes solo buscaba en
  `nombre_articulo`; ahora busca también en `codigo_dali`, `codigo_sap`
  y `proveedor` (nombre), con coincidencia en cualquiera de los cuatro
  (OR). Placeholders de ambos buscadores actualizados para reflejarlo.
- `articulosController.js`: `codigo_dali` es `integer` en el esquema, así
  que para poder aplicarle `ilike` (que exige texto) se castea con
  `codigo_dali::text` dentro del propio filtro — casteo de columna que
  soporta PostgREST sin necesitar una columna calculada aparte.
  `proveedor` vive en una tabla distinta (`proveedores`, relación
  `id_proveedor`), así que no se puede meter tal cual en el `.or()` de
  la consulta principal: se resuelve antes con una consulta aparte a
  `proveedores.nombre_proveedor` (mismo patrón que ya se usa para
  resolver `naturaleza` de nombre a id, unas líneas arriba en el mismo
  fichero) y los `id` que coinciden se añaden como
  `id_proveedor.in.(...)` dentro del propio OR.
- Modo demo (`services/api.js`, sin `VITE_API_URL`) actualizado con el
  mismo criterio de búsqueda sobre `mockArticulos.js`, para que se
  comporte igual que contra el backend real.

### Pendiente de verificar (sin acceso a Supabase en este entorno)
- El casteo `codigo_dali::text.ilike...` y la combinación
  `id_proveedor.in.(...)` dentro de un mismo `.or()` son sintaxis
  documentada de PostgREST, pero no se ha podido probar contra el
  proyecto real de Supabase desde aquí (mismo motivo que en entregas
  anteriores). Conviene probar en cuanto se despliegue: buscar por un
  código DALI parcial, por parte de un código SAP, y por parte de un
  nombre de proveedor, en Catálogo y en Administración, con y sin filtro
  de naturaleza a la vez.

## [1.0.5] — 2026-08-03

### Corregido
- **Mismo problema que v1.0.4, ahora en Administración · Artículos**: el
  contador "N ficha(s)" del panel de administración también usaba
  `articulos.length` (el lote cargado, tope `pageSize=3000`) en vez del
  total real. Aquí el panel pide `todos: true` (activos e inactivos), así
  que el total real (p.ej. 30109 en el momento de este fix) supera aún
  más el `pageSize` — y como este número cambia con cada importación de
  Excel o alta/baja manual, no hay un valor fijo al que "ajustar" el
  `pageSize"; hace falta el total real del backend, no el tamaño del
  lote cargado.
- `AdminArticulos.jsx` guarda ahora también el `total` que devuelve
  `fetchArticulos` (mismo cambio de v1.0.4 en `services/api.js`) y lo
  usa para el contador en vez de `articulos.length`.
- Mismo límite pendiente que en v1.0.4: la tabla de administración sigue
  mostrando como máximo `pageSize=3000` filas hasta que haya paginación
  real en la UI; el contador ya es correcto de forma independiente.

## [1.0.4] — 2026-08-03

### Corregido
- **El contador "N artículo(s)" de la cabecera no mostraba el total real
  en "Todas las naturalezas"** — se quedaba clavado en 3000 (el
  `pageSize` por defecto) aunque hay ~6700 artículos activos en total.
  No era un problema de backend: `listarArticulos` ya devuelve
  `pagination.total` con un `count: "exact"` de Supabase, que no está
  limitado por el `.range()`/pageSize (por eso el recuento por
  naturaleza, arreglado en v1.0.3, sí era correcto — el total de cada
  naturaleza individual está por debajo de 3000). El fallo estaba en el
  frontend: `services/api.js` (`fetchArticulos`) descartaba ese
  `pagination` y devolvía solo `data`; `App.jsx` pintaba el contador con
  `visibles.length`, es decir, el tamaño del lote cargado (tope 3000),
  no el total real.
- `fetchArticulos` devuelve ahora `{ data, total }`, con `total` tomado
  de `pagination.total` (o `data.length` en modo demo, donde no hay
  paginación). `App.jsx` guarda ese `total` en estado y lo usa para el
  contador en vez de `visibles.length`. Se actualizó también
  `AdminArticulos.jsx`, el otro consumidor de `fetchArticulos`, para
  adaptarse al nuevo formato de retorno.
- Sigue sin haber paginación real en la tabla: con "Todas las
  naturalezas" el contador ya muestra el total correcto (~6700), pero la
  tabla sigue mostrando como máximo `pageSize=3000` filas hasta que se
  implemente paginación en la UI.

## [1.0.3] — 2026-08-03

### Corregido
- **El recuento por naturaleza seguía sin ser correcto en categorías
  grandes** (1000 en ALIMENTACION y EQUIPAMIENTO, que tienen más de
  1000 artículos activos) **incluso después de v1.0.2**. Subir el
  `pageSize` por defecto de 50 a 3000 (v1.0.2) no era suficiente: el
  proyecto de Supabase impone un tope duro de filas por petición
  (Project Settings → API → Max Rows, 1000 por defecto), que corta
  cualquier `.range()` que pida más — con independencia del `pageSize`
  de la aplicación. El resto de naturalezas (con menos de 1000 activos)
  no mostraba el problema porque nunca llegaban a chocar con ese tope.
- `listarArticulos` (`articulosController.js`) trocea ahora la petición
  en tandas de máximo 1000 filas (`SUPABASE_MAX_ROWS_POR_PETICION`) y
  las concatena hasta completar el `pageSize` solicitado o hasta que no
  queden más filas — en vez de un único `.range()` que Supabase recorta
  en silencio. Probado con un simulador del tope de 1000 filas
  (sin acceso de red a Supabase en este entorno): recupera las filas
  completas sin huecos ni duplicados.
- Sigue sin cubrir "Todas las naturalezas" sin filtro (~6700 activos en
  total, por encima de `pageSize=3000`): ver paginación pendiente.

## [1.0.2] — 2026-08-03

### Corregido
- **El filtro por naturaleza del sidebar (p.ej. "BEBIDAS") mostraba
  muchos menos artículos de los que existen realmente** — 5 en vez de
  los 413 activos que hay en BEBIDAS. Dos fallos combinados:
  1. `frontend/src/services/api.js` (`fetchArticulos`) solo aplicaba el
     parámetro `naturaleza` en modo demo; contra el backend real ni
     siquiera lo incluía en la petición a `GET /articulos`.
  2. `backend/src/controllers/articulosController.js` (`listarArticulos`)
     no aceptaba `naturaleza` como filtro en absoluto (solo
     `familia`/`subfamilia`/`proveedor`, por id).
  El resultado visible (5 artículos con nombres que empiezan por
  "7UP...") era efecto de un tercer punto: como el backend nunca recibía
  el filtro, devolvía la página 1 sin filtrar (50 artículos en orden
  alfabético), y el filtro se aplicaba solo después, en el navegador,
  sobre esos 50 — de ahí que solo sobrevivieran los pocos que
  alfabéticamente caían en esa primera página.
  Corregido: `services/api.js` ahora reenvía `naturaleza` al backend;
  `listarArticulos` la resuelve contra `naturalezas.nombre_naturaleza`
  y filtra `articulos.id_naturaleza` en el servidor.
- `pageSize` por defecto de `GET /articulos` sube de 50 a 3000, como
  parche mínimo para que el filtro por naturaleza no se quede corto en
  categorías numerosas (ALIMENTACION, la más grande, tiene ~2320
  artículos activos). No sustituye la paginación real pendiente: "Todas
  las naturalezas" sin filtro (~6700 activos en total) sigue sin
  cubrirse por completo con esto.

## [1.0.1] — 2026-08-03

### Corregido
- **PROVEEDOR, CÓDIGO SAP y la miga NATURALEZA · FAMILIA · SUBFAMILIA
  salían vacíos en el listado y la ficha**, aunque el dato estaba bien
  resuelto en la base de datos. `articulosController.js` (`GET
  /articulos`, `GET /articulos/:id`) devolvía las dimensiones anidadas
  tal como las pide Supabase (`proveedores: { nombre_proveedor }`,
  igual para `naturalezas`/`familias`/`subfamilias`), pero todo el
  frontend (`ArticuloTable.jsx`, `ArticuloDetail.jsx`,
  `ArticuloForm.jsx`, `AdminArticulos.jsx`) espera esos mismos datos
  aplanados y en singular (`articulo.proveedor`, `articulo.naturaleza`).
  Nueva función `aplanarArticulo()` en `articulosController.js` que
  convierte la respuesta anidada al formato plano que ya consume el
  frontend, aplicada tanto al listado como a la ficha individual.

## [1.0.0] — 2026-08-01

Primera versión consolidada del proyecto como monorepo listo para GitHub.

### Añadido
- **Base de datos:** esquema completo en `database/schema.sql` para
  Supabase/Postgres — tablas `naturalezas → familias → subfamilias`,
  `proveedores`, `articulos`, `fichas`, `usuarios`; índices para el
  buscador; vista `v_articulos_completo`; Row Level Security básica
  (usuario estándar solo ve `activo_dali = true`).
- **Datos:** CSV normalizados (`naturalezas.csv`, `familias.csv`,
  `subfamilias.csv`, `proveedores.csv`, `articulos.csv`) generados desde
  `ARTICULOS_DALI.xlsx` y `LISTADO_CODIGOS_DALI_-_SAP.xlsx` con
  `build_csvs.py`. Jerarquía verificada: 13 naturalezas → 53 familias →
  253 subfamilias.
- **Backend:** API REST en Node.js + Express + Supabase con los
  endpoints de la sección 7 del informe técnico (`GET /articulos`,
  `GET /articulos/:id`, `GET /articulos/:id/fichas`,
  `POST /admin/import-excel`, CRUD `/admin/articulos`,
  `GET /export/excel`, `GET /export/pdf`) y middleware de auth JWT con
  roles `admin`/`lectura`.
- **Frontend:** aplicación React + Vite con sidebar de "Naturaleza",
  buscador, tabla de artículos, panel de detalle con enlaces a fichas, y
  modo demo con datos de muestra (`mockArticulos.js`) sin necesidad de
  backend.
- **Diseño:** sistema visual "ledger de hotel con solera" — papel marfil
  `#F4EFE3`, latón `#A87C3F` como acento único de interacción, vino
  `#6E2A2A` reservado para "No activo", tipografía Fraunces/Inter/IBM
  Plex Mono, y el código de artículo como etiqueta de equipaje de latón.
- **Documentación:** `README.md` raíz con guía de arranque, `README.md`
  por carpeta (`frontend/`, `backend/`, `database/`), informe técnico en
  `docs/informe-tecnico.md`, referencia de diseño en
  `docs/design-reference/`, e `HISTORIAL.md` con el registro narrativo
  del proyecto.

### Corregido
- Desincronización entre `frontend/README.md` (aún describía la paleta
  antigua verde-azulado/Space Grotesk) y el CSS ya actualizado a
  marfil/latón/Fraunces.
