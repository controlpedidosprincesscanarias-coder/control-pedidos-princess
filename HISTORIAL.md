# Historial del proyecto — Catálogo DALI

Registro de la evolución del proyecto, para saber en todo momento qué hay
hecho, qué se decidió y por qué, y qué queda pendiente. Actualízalo en
cada entrega o cambio relevante (añade una entrada nueva arriba, no borres
las anteriores).

Convención de entrega (actualizada 2026-09-02, a petición de Víctor): cada
entrega se empaqueta SIEMPRE en un único ZIP, con cada archivo modificado o
creado colocado en su ruta real dentro del proyecto (frontend/, backend/,
components/admin/, etc.; los que pertenecen a la raíz van directamente en
ella, sin carpetas adicionales) — nunca archivos sueltos ni el proyecto
completo. Motivo del cambio: varios archivos comparten nombre en carpetas
distintas (p.ej. `package.json`, `README.md` en backend/ y frontend/ a la
vez), y con archivos sueltos había que aclarar la ruta de cada uno en la
propia entrega; con la estructura de carpetas ya dentro del ZIP, sustituir
cada archivo es simplemente descomprimir sobre el proyecto real. (Antes de
esta fecha la convención era la contraria — archivos individuales sueltos,
nunca ZIP — ver versiones anteriores de esta nota si hace falta contexto de
entregas previas.)

---

## v1.50 — Botón de descarga en PDF para listados largos de "Documentación pendiente" (v1.19.68)

Víctor, al final de un correo real de ejemplo con ~140 referencias sin ficha técnica: "CUANDO UN LISTADO DE FALTANTES ES TA EXTENSO, SE PUEDE CREAR UN PDF Y ENVIAR EN VEZ DEL DETALLE UN BOTON PARA LA DESCARGA DEL LISTADO BIEN ESTRUCTURADO?".

**El problema que señalaba**: `generarTextoEmail()` en `EmailProveedorModal.jsx` (ver v0.?? / comentario del 2026-08-26 en ese mismo fichero) ya itemiza SOLO la ficha técnica con una viñeta "* código — artículo" por referencia — un rediseño explícito de la versión aún anterior, que itemizaba las tres cosas y "quedaba como una lista interminable". Pero ese rediseño no puso ningún tope: con un proveedor que de verdad tiene decenas de referencias con ficha técnica pendiente (el caso real que mandó Víctor, ~140), la lista de viñetas por sí sola vuelve a ser kilométrica — el mismo problema que se quiso resolver entonces, solo que ahora limitado a un único tipo de documento en vez de tres.

**Antes de tocar código, se decidieron dos cosas con Víctor**:
1. **Cuándo cambiar de lista a botón**: solo a partir de cierto número de referencias — con pocas, la lista sigue tal cual (no hace falta un PDF para dos o tres artículos); a partir de ahí, se sustituye por el botón. Se ha fijado ese umbral en 30 referencias con ficha técnica pendiente (`UMBRAL_LISTADO_FICHA_TECNICA_PDF` en `EmailProveedorModal.jsx`) — un número redondo, fácil de ajustar si con el uso real resulta demasiado alto o bajo.
2. **Qué lleva el PDF**: no solo un volcado de la lista de ficha técnica que sustituye — el PDF trae el listado COMPLETO de todo lo pendiente de ese proveedor (ficha técnica, ficha de seguridad e imagen, una columna por tipo, marcando "Falta"/"OK" en cada una) — un documento de referencia más completo para el proveedor, aunque cambie ligeramente lo que hoy ve en el correo cuando se dispara este caso.

**Cómo se ha implementado, y por qué así**:
- **El PDF** (`generarPdfDocumentacionFaltante()`, nuevo, en `documentacionController.js`) se dibuja con PDFKit, mismo estilo visual (colores, tipografía, cabecera de tabla, pie de página con número de página) que el PDF de catálogo ya existente (`generarPdfBuffer()` en `generarExportWorker.js`) — para que un documento generado por DALI se reconozca como tal independientemente de cuál sea. A diferencia de ese otro PDF (que sí corre en un hilo aparte, `worker_threads`, por el volumen del catálogo completo — hasta ~30.000 filas, la causa del "out of memory" corregido en v1.19.66), este se genera síncronamente en el propio controlador: el volumen aquí es, como mucho, el catálogo de UN proveedor (cientos de artículos, no decenas de miles) — el mismo orden de magnitud que ya genera síncronamente, sin ningún problema, la exportación a Excel de esta misma pantalla (`exportarDocumentacionFaltanteExcel()`, ya existente).
- **La ruta es pública, sin sesión** (`GET /export/documentacion-faltante-pdf/:idProveedor`, en el mismo router que ya expone `GET /export/excel` y `GET /export/pdf` sin autenticación) — el destinatario del enlace es el PROPIO proveedor externo, que no tiene ninguna cuenta en DALI con la que iniciar sesión, así que no puede vivir bajo `/admin` como el resto de "Documentación faltante". No lleva token de un solo uso ni caduca: recalcula la documentación pendiente de ese proveedor EN EL MOMENTO en que se pincha el enlace — si el proveedor abre el correo varios días después, ve lo que falta de verdad entonces, no una foto congelada de cuando se envió el correo. El dato expuesto (qué documentación falta de un proveedor) se ha considerado de sensibilidad comparable a la del propio catálogo, ya público sin sesión desde antes — no se ha añadido ninguna protección extra sobre el `idProveedor` en la URL; si Víctor prefiriera más adelante un enlace con token/caducidad, es un cambio acotado a esta única función.
- **El botón dentro del correo**: en vez de añadir un parámetro nuevo (`enlacePdf`) que hubiera que ir pasando a mano por `EmailProveedorModal.jsx` → `services/api.js` → `documentacionController.js` → `emailHtml.js` (cuatro sitios que mantener sincronizados para una sola cosa), se ha optado por algo más simple: `generarTextoEmail()` mete la URL del PDF como texto plano dentro del propio `cuerpo` del correo (el mismo campo que ya se edita a mano en el `<textarea>` del modal), y `textoPlanoAHtmlParrafos()` (`emailHtml.js`) — la función que ya convierte ese texto en el HTML final — se ha enseñado a reconocer una URL http(s) dentro de un párrafo y pintarla como un botón centrado, en vez de como texto suelto. Como la URL vive dentro del mismo `cuerpo` que ya se usa para la vista previa Y para el envío real (mismo criterio de "la vista previa es SIEMPRE fiel a lo que se envía" que ya seguía esta función desde que se creó, ver 2026-08-28), no hace falta ningún parámetro ni cambio en las llamadas a `preview-email`/`preparar-envio` — funciona automáticamente, y sigue funcionando si el día de mañana otro tipo de correo de este mismo flujo necesita meter un enlace parecido.
- El resto del correo (avisos generales de ficha de seguridad/imagen, ejemplo de nombre de archivo, firma) no cambia — el botón sustituye ÚNICAMENTE a la lista de viñetas de ficha técnica cuando es demasiado larga, nada más.

**Verificación**: `node --check` en los tres ficheros backend tocados, limpio. Generado un PDF real de prueba con 60 artículos (para forzar salto de página) y convertido a imagen para revisión visual: cabecera con título/subtítulo, las tres columnas "Ficha técnica"/"Ficha de seguridad"/"Imagen" con "Falta" en rojo y "OK" en negro, color alterno de filas, salto de página correcto con cabecera de tabla repetida y pie de página con el número — todo correcto en las dos páginas. Probada también la conversión de URL a botón en `textoPlanoAHtmlParrafos()`: un párrafo con la URL al final se parte en el texto explicativo más un botón HTML centrado con el enlace correcto (comprobado que el `href` es exactamente la URL esperada y que no queda ningún texto de URL suelto sin convertir), y un correo de control SIN ningún enlace (la lista de viñetas de siempre) se sigue renderizando exactamente igual que antes de este cambio. `npm run build` en frontend, limpio.

**Ficheros editados**: `backend/src/controllers/documentacionController.js`, `backend/src/routes/export.js`, `backend/src/utils/emailHtml.js`, `frontend/src/services/api.js`, `frontend/src/components/admin/EmailProveedorModal.jsx`.

---

## v1.49 — Reorganización del Excel de "Exportar catálogo completo": orden, cabeceras, anchos y filtros (v1.19.67)

Víctor, adjuntando `catalogodalicompleto.xlsx` (el propio Excel exportado por la app, reorganizado a mano en Excel): "PODEMOS ORGANIZAR EL LISTADO EXPORTADO COMO ESTE QUE ADJUNTO? FILTROS, TAMAÑOS COLUMNAS, NOMBRES CABACERAS COLUMNAS ETC".

**Cómo se ha averiguado qué cambiar**: se ha abierto el Excel que mandó Víctor con `openpyxl` (mismos datos, mismas ~30.000 filas, misma fila de título/subtítulo/cabecera que ya generaba la app) y se ha comparado columna a columna, celda a celda, contra lo que produce el propio código: mismo contenido pero con el orden de columnas cambiado a mano, las cabeceras renombradas, los anchos de columna ajustados, un filtro de Excel (`Datos → Filtro`) puesto sobre la fila de cabeceras, y dos columnas centradas. Es decir, no pedía datos nuevos ni menos columnas — pedía que la app generase directamente el fichero con el mismo aspecto que él ya se había currado a mano en Excel, para no tener que repetir ese trabajo cada vez que exporta.

**Qué cambia exactamente** (los 20 campos y todos los datos siguen siendo los mismos, ver v1.47 para su origen):
- **Orden de columnas**: "Código Proveedor" pasa de ir al final (columna 20) a ir en segundo lugar, justo después de "Código DALI". "Activo" pasa de ir en noveno lugar (justo después de "Proveedor") a ir al final, en su sitio.
- **Cabeceras**: las columnas que vienen del Excel de artículos DALI llevan ahora el sufijo " - DALI" (excepto "Código DALI", que ya lo deja claro por sí sola) — "Descripción - DALI", "Unidad - DALI", "IGIC - DALI", "Naturaleza - DALI", "Familia - DALI", "Subfamilia - DALI" — para que se distingan de un vistazo de las columnas que vienen del Excel de SAP (que ya llevan "SAP" en el nombre, sin cambios: "Código SAP", "Descripción SAP", etc.). Además, "Proveedor" pasa a llamarse "Proveedor Asignado - DALI", más claro que el nombre genérico anterior. "Código Proveedor" y "Activo" mantienen su nombre, solo cambian de posición.
- **Anchos de columna**: ajustados a los mismos que dejó Víctor en su plantilla — el cambio más notable es "Descripción - DALI", que pasa de un ancho medio a uno muy generoso (para que quepan descripciones largas sin cortar), y "Activo", que pasa a ser muy estrecha (solo necesita caber "SI"/"NO").
- **Filtros**: se activa el filtro de columna de Excel (la flechita desplegable de "Datos → Filtro") sobre toda la fila de cabeceras (rango `A4:T4`, la fila 4 porque las tres primeras son el título, el subtítulo y una fila en blanco) — así Víctor puede filtrar y ordenar directamente desde Excel sin tener que activarlo él mismo cada vez.
- **Alineación**: "Código Proveedor" y "Activo" quedan centradas, tanto la cabecera como cada valor de datos — igual que en la plantilla de Víctor. El resto de columnas se queda con la alineación por defecto de Excel (texto a la izquierda, números a la derecha), como hasta ahora.

**Nota técnica**: el `autoFilter` de ExcelJS en el modo streaming que se usa aquí (desde la v1.19.66, para evitar el "out of memory" del catálogo completo) solo admite fijar el RANGO donde aparece el desplegable de filtro (p.ej. `"A4:T4"`), no qué opciones concretas están marcadas dentro de cada desplegable — de hecho, ni siquiera el propio formato `.xlsx` guarda eso: cuando se aplica un filtro en Excel y se guarda el fichero, Excel solo recuerda el rango con el filtro activado, no la selección hecha en ese momento (que es una vista temporal, no un dato persistido). Así que el comportamiento aquí implementado (filtro activado y listo para usar, sin ninguna opción premarcada) es exactamente equivalente a lo que Excel guardaría de la plantilla de Víctor.

**Verificación**: `node --check` en `exportController.js` y `generarExportWorker.js`, limpio. Se ha generado un `.xlsx` real con el worker de producción (no una reimplementación) usando como datos de prueba los dos primeros artículos reales del propio Excel que mandó Víctor (uno activo, uno inactivo), y se ha comprobado, comparando directamente contra su fichero: el rango del filtro (`A4:T4`), las 20 cabeceras con los nuevos nombres y en el nuevo orden, los 20 anchos de columna (coinciden exactamente, hasta los decimales), la alineación centrada de "Código Proveedor" y "Activo" en cabecera y en datos, y el color rojo de la fila del artículo inactivo (que ya funcionaba desde v1.47, y sigue funcionando tras el reordenado). `npm run build` en frontend, limpio — este cambio no toca frontend, pero se confirma que el resto de la app sigue compilando.

**Ficheros editados**: `backend/src/controllers/exportController.js`, `backend/src/workers/generarExportWorker.js`.

---

## v1.48 — Arreglo del "out of memory" en "Exportar catálogo completo" (v1.19.66)

Víctor, con capturas del sidebar de producción: "VERSION 1.19.65 DESPLEGADA" — las capturas mostraban el botón nuevo "Exportar catálogo completo" (entregado en v1.47/v1.19.65) y, justo debajo, el texto en rojo "Worker terminated due to reaching memory limit: JS heap out of memory".

**Qué pasaba**: el botón funcionaba en las pruebas hechas antes de la entrega anterior (con catálogos de muestra pequeños), pero en producción, con el catálogo real completo (miles de artículos, sin ningún filtro, 20 columnas por fila), el proceso se quedaba sin memoria y el worker moría a mitad de generar el fichero. La causa está en cómo se construía el Excel la primera vez: `generarExcelCompletoBuffer` armaba todo el libro en memoria con `new ExcelJS.Workbook()` y no lo volcaba a ningún sitio hasta tener el fichero entero listo (`workbook.xlsx.writeBuffer()`) — cada celda de cada fila se queda como objeto vivo en el heap de Node hasta ese momento, así que cuantas más filas tiene el catálogo, más memoria pico hace falta, sin ningún límite práctico. El resto de exportaciones (Excel/PDF filtrados por naturaleza/familia/búsqueda, o de la selección manual) nunca ha dado este problema porque como mucho manejan unos cientos de filas — la exportación completa es la primera que procesa el catálogo entero de una vez, y ahí es donde salió el límite de memoria del proceso en el plan de Render de producción.

**Qué se ha cambiado**: dos cosas, las dos apuntando a bajar el pico de memoria de esta exportación en concreto (el resto de exportaciones no se han tocado, porque nunca han tenido este problema):
1. El worker ahora genera el Excel con la API de streaming de ExcelJS (`ExcelJS.stream.xlsx.WorkbookWriter`), que escribe cada fila a un fichero temporal en disco tan pronto como se confirma (`fila.commit()`), en vez de guardarla en memoria hasta el final — la memoria de una fila ya escrita se libera de inmediato, así que el pico de memoria deja de crecer con el tamaño del catálogo. El controlador (`exportarExcelCompleto`), en vez de esperar un buffer completo y mandarlo con `res.end(buffer)`, ahora hace streaming de ese fichero temporal directamente a la respuesta HTTP con `fs.createReadStream(...).pipe(res)`, y lo borra al terminar (o si la conexión se corta a medias).
2. Los datos que se le pasan al worker han dejado de ser objetos con 20 claves por fila (`{codigo_dali: ..., nombre_articulo: ..., ...}`) y ahora son arrays posicionales de 20 valores (`[valor1, valor2, ...]`) — cada objeto JS con propiedades tiene cierta sobrecarga de memoria en V8 que un array plano no tiene, y al pasar miles de filas de una vez por `workerData` (que hace una copia estructurada, así que existen brevemente por duplicado en los dos hilos) esa sobrecarga por fila también contaba. El orden de las columnas y sus cabeceras no cambian, solo la forma interna en que viajan los datos.

Como efecto colateral menor: al usar la API de streaming, se ha quitado la celda de título combinada (merge) de la cabecera del Excel — ExcelJS documenta mal el comportamiento de `mergeCells` en modo streaming y no valía la pena arriesgar un fichero corrupto por un detalle puramente estético; el título y subtítulo se siguen viendo igual (negrita, cursiva), solo que sin combinar las celdas de alrededor.

**Verificación**: `node --check` en `exportController.js` y `generarExportWorker.js`, limpio. Se ha probado el worker real (no una reimplementación de prueba) generando un `.xlsx` de 5.000 filas × 20 columnas exactamente como lo invoca `exportarExcelCompleto` en producción, y comprobando: las 20 cabeceras en el orden correcto, los valores de una fila de muestra, que las filas de artículos inactivos salen en rojo y las activas en negro normal, el número total de filas de la hoja, y que el fichero temporal se borra correctamente después de generarse. Además, para tener una medida cuantitativa del problema original, se hizo una comparación de pico de memoria (RSS del proceso, muestreado cada 20ms) generando 60.000 filas × 20 columnas con el método antiguo (buffer en memoria) frente al nuevo (streaming a disco): el pico bajó de ~1.491 MB a ~667 MB, una reducción del 55% — consistente con que el catálogo real de producción (bastante más grande que las pruebas hechas antes de la entrega anterior, pero del mismo orden de magnitud que 60.000 filas) es la causa más probable de que solo fallara en producción y no en las pruebas previas.

**Ficheros editados**: `backend/src/controllers/exportController.js`, `backend/src/workers/generarExportWorker.js`.

---

## v1.47 — Botón "Exportar catálogo completo", solo para el administrador principal por defecto (v1.19.65)

Víctor: "Necesito un botón solo visible para el administrador principal, lo podemos poner configurable como el resto de apartados de visualización de administrador, necesito un botón para exportar un Excel total de toda la información que recogen los dos Excel que se importan más la columna de código proveedor".

**Qué se añade**: un botón nuevo en el sidebar, "Exportar catálogo completo" (Gestión → Catálogo, justo debajo de "Importar Excel" — el reverso natural de esa importación), que descarga directamente un `.xlsx` con el catálogo entero, sin ningún filtro (activos e inactivos, sin depender de lo que se esté viendo en pantalla ni de ninguna búsqueda/selección). El fichero lleva las 20 columnas siguientes, en este orden: Código DALI, Descripción, Unidad, IGIC, Naturaleza, Familia, Subfamilia, Proveedor y Activo (las que trae el Excel de artículos DALI que se importa), Código SAP, Descripción SAP, Unidad SAP, Grupo productos SAP, Descripción grupo productos SAP, Indicador impuestos SAP, Categoría valoración, Tipo producto, Grupo compras SAP y Nombre grupo compras SAP (las que trae el Excel de SAP), y por último Código Proveedor — la columna que Víctor pidió sumar aparte, ya presente en el resto de exportaciones del catálogo. Es un botón de descarga directa (mismo patrón fetch+blob que "Exportar Excel"/"Exportar PDF" del catálogo, con su propio spinner "Generando…"), no una pantalla nueva — no hacía falta ninguna, es un único fichero sin parámetros que elegir.

**Cómo queda restringido, y cómo se hace "configurable"**: se suma una novena clave (`admin-exportar-completo`) al mismo sistema de permisos por apartado que ya existía para el resto de "Gestión" (migración `2026-09-03_permisos_admin.sql`, ver HISTORIAL de esa fecha) — el administrador principal la tiene siempre (se salta esta lista, como todas), y puede concedérsela a cualquier otro administrador desde "Usuarios" → casilla "Exportar catálogo completo" (grupo "Catálogo"), exactamente como pidió ("lo podemos poner configurable como el resto de apartados"). La diferencia con los 8 permisos que ya existían: aquellos arrancaron concedidos a TODOS los administradores de entonces (para no bloquear a nadie de golpe el día del cambio); este es una capacidad que no existía hasta ahora, así que arranca SIN concederse a nadie salvo al administrador principal — nadie pierde nada que ya tuviera, y nadie gana nada que no se le haya dado explícitamente. El backend hace la misma comprobación real (`requierePermiso("admin-exportar-completo")` en la ruta `GET /admin/export-completo`) — el botón oculto en el menú es solo comodidad de interfaz, la protección de verdad está ahí.

**De dónde sale cada columna**: se ha revisado `importController.js` para replicar exactamente las columnas de los dos Excel que Víctor sube en "Importar Excel" — `ARTICULOS_DALI.xlsx` (CODIGO, DESCRIPCION, UNIDAD, IGIC, NATURALEZA, FAMILIA, SUBFAMILIA, PROVEEDOR, ACTIVO) y `LISTADO_CODIGOS_DALI_-_SAP.xlsx` (CODIGO SAP, DESCRIPCION SAP, UNIDAD SAP, GRUPO PRODUCTOS SAP, Descripción de grupo de productos SAP, Indicador de impuestos SAP, Categoría valoración, Tipo de producto, GRUPO COMPRAS SAP, NOMBRE GRUPO COMPRAS SAP) — con cabeceras en el estilo del resto de la app (Título con mayúscula inicial) en vez de las mayúsculas sueltas de los Excel de origen, para que se lea igual que el resto de listados de DALI. No se incluye `activo_general` (columna interna de la base de datos, no viene de ninguno de los dos Excel) — si Víctor la necesita también, es un añadido rápido.

**Verificación**: `node --check` en los cuatro archivos backend tocados (`exportController.js`, `generarExportWorker.js`, `routes/admin.js`, `usuariosController.js`), limpio. Se ha probado el nuevo tipo de exportación del worker (`excel-completo`) generando un `.xlsx` real con ExcelJS a partir de dos artículos de muestra (uno activo, uno inactivo con todos los campos SAP vacíos) y comprobando las 20 cabeceras en el orden esperado, los valores de la fila de cada uno, y que la fila del inactivo sale en rojo — igual que ya hace el resto de exportaciones con los artículos dados de baja. `npm run build` en frontend, limpio (Vite, 84 módulos).

**Ficheros editados**: `backend/src/controllers/exportController.js`, `backend/src/workers/generarExportWorker.js`, `backend/src/routes/admin.js`, `backend/src/controllers/usuariosController.js`, `frontend/src/services/api.js`, `frontend/src/App.jsx`, `frontend/src/components/Sidebar.jsx`, `frontend/src/components/admin/UsuarioForm.jsx`.

---

## v1.46 — Columna "Precio €" en el Excel de artículos seleccionados a mano (v1.19.64)

Víctor: "Necesito que cuando un usuario admin, pulse en exportar Excel y teniendo artículos seleccionados con el tick junto a DALI, el archivo que se exporta contenga una nueva columna al final del listado después de activo, con la cabecera precio €".

**Aclarado antes de tocar código**: en DALI no existe ningún campo de precio, ni en la tabla `articulos` ni en ninguna ficha — nunca se ha guardado un precio de artículo en esta aplicación. Se le preguntó a Víctor qué debía llevar la columna y dónde debía aparecer; confirmó que la columna sale en blanco, para rellenarla a mano después (no hace falta ningún campo nuevo en la base de datos ni en `ArticuloForm.jsx`), y que solo debe aparecer en el Excel de la selección manual — el "tick junto a DALI" con el que se marcan artículos en el catálogo y que, con "Ver solo marcados" activo, sustituye a los cuatro filtros de siempre en la exportación (ver `?codigos=` en `exportController.js`, HISTORIAL v1.03 y CHANGELOG 2026-09-03). El resto de exportaciones Excel (el listado general filtrado por naturaleza/familia/búsqueda) y el PDF se quedan exactamente igual que hasta ahora.

**Qué se añade**: cuando `GET /export/excel` recibe `?codigos=` de un admin, el `.xlsx` generado lleva una columna extra al final, después de "Activo", con la cabecera "Precio €" — siempre vacía, con el mismo borde de "celda para rellenar a mano" que ya tiene la columna "Cantidad" del listado de comprador (misma idea: una casilla en blanco pensada para completarse fuera de la aplicación). `exportController.js` calcula un flag nuevo (`incluirColumnaPrecioEnExcel`: admin + `codigos` presente) y lo pasa al worker de generación (`generarExportWorker.js`) junto con el resto de datos ya resueltos — la columna se añade ahí, DESPUÉS de calcular las columnas compartidas con el PDF (`columnasPdf()`), precisamente para que el PDF y el resto de Excel no la hereden sin querer.

**Verificación**: `node --check` en los dos archivos tocados del backend, limpio. Como no hay ningún harness de pruebas de exportación en este proyecto, se ha escrito una prueba funcional puntual que invoca el worker real (mismo `Worker` que usa `exportController.js`) con datos de artículo de ejemplo, generando un `.xlsx` de verdad con ExcelJS y leyendo sus cabeceras, para los cuatro casos relevantes: admin con selección manual (aparece "Precio €" al final), admin sin selección manual (no aparece), usuario no admin (no aparece, aunque llegara el flag mal puesto) y PDF (sin cambios, se genera igual que siempre). Los cuatro se comportaron como se esperaba.

**Ficheros editados**: `backend/src/controllers/exportController.js`, `backend/src/workers/generarExportWorker.js`, `backend/README.md`.

---

## v1.45 — Aviso de solicitudes de acceso pendientes en el menú (v1.19.63)

Víctor, comparando dos capturas del menú de control-pedidos-princess ("Alertas" con un número junto al botón) y de Catálogo Asignaciones ("Solicitudes de acceso" sin ningún aviso): "se puede poner un aviso en el menú que indique si tengo asuntos pendientes en el apartado solicitudes de accesos? tipo control pedidos alertas".

**Qué se añade**: el botón "Solicitudes de acceso" del sidebar (Gestión → Accesos) lleva ahora, cuando hay alguna pendiente, un número a su derecha — oculto del todo cuando no hay ninguna, exactamente como pidió. Reutiliza el `GET /admin/solicitudes-acceso` que ya existía para la propia pantalla (sin paginación, volumen bajo por diseño — altas de personal, no artículos): no hace falta ningún endpoint nuevo solo para contar, basta con filtrar `estado === "pendiente"` sobre lo que ya devuelve.

**Cuándo se calcula**: `App.jsx` (`refrescarSolicitudesPendientes`) lo pide al iniciar sesión (si el admin tiene el permiso `admin-solicitudes-acceso` — mismo criterio que ya usa el propio botón del menú para mostrarse o no, así se evita también un 403 innecesario contra ese endpoint para quien no tiene acceso), lo repasa cada 5 minutos por si llega una solicitud nueva mientras se está en otra pantalla, y lo refresca al instante en cuanto se acepta o rechaza una solicitud (`AdminSolicitudesAcceso.jsx` recibe un nuevo prop `onCambio`, llamado justo después de cada acción resuelta con éxito) — sin tener que salir de esa pantalla y volver a entrar para verlo actualizado.

**Estilo**: en vez de reutilizar el navy/dorado de control-pedidos-princess (paleta ajena a este proyecto), el número usa la etiqueta de latón (`--brass`) que ya es el único acento de interacción del propio sistema de diseño del catálogo (ver cabecera de `styles/index.css` — "el acento único: latón"), coherente con el resto del sidebar. Clases nuevas `.tab-label-row` (reparte el texto del botón y el número en extremos opuestos, sin tocar `.tab`, que sigue siendo `display:block` a propósito) y `.tab-badge`.

**Verificación**: `npm run build` en frontend, limpio (Vite, 84 módulos). No se ha tocado el backend — se reutiliza tal cual el endpoint ya existente.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.63** (por convención, aunque el backend no cambia en esta entrega).

**Ficheros editados**: `frontend/src/App.jsx`, `frontend/src/components/Sidebar.jsx`, `frontend/src/components/admin/AdminSolicitudesAcceso.jsx`, `frontend/src/styles/index.css`.

---

## v1.44 — Corrección de v1.42: "Documentación faltante" no necesitaba una plantilla EmailJS nueva (v1.19.62)

Víctor, mostrando el panel de EmailJS.com de su plantilla "Contact Us" (las 2 cuentas, `template_fpn6ekk` y `template_s0arcr9`) y el listado de "Email Templates": el campo "Reply To" de esa plantilla YA tenía puesta la variable `{{reply_to}}` — junto con `{{bcc}}`/`{{cc}}`, también ya presentes — sin que nadie hubiera tenido que pedirlo ni tocarlo para esto.

**Qué pasó**: la v1.42/v1.19.60 (entrega anterior) dio por hecho que, para poder fijar un "Responder a" dinámico en el correo de "Documentación faltante" (el comprador que gestiona la solicitud, no un buzón fijo), hacía falta una plantilla EmailJS SEPARADA de la de "correo a un usuario" — porque esa era la única forma que parecía tener sentido sin haber comprobado primero lo que la plantilla real de Víctor ya traía configurado. Se añadieron `template_id_proveedor_1`/`template_id_proveedor_2` (migración `2026-09-09_emailjs_template_proveedor.sql`) y un campo nuevo en Administración → Configuración EmailJS, pidiéndole a Víctor que duplicara su plantilla y añadiera `{{reply_to}}` a mano — trabajo de más que resultó innecesario: su plantilla de usuario, la de siempre, ya tenía exactamente ese campo puesto.

**Corrección**: se revierte el diseño de v1.42, con el mismo patrón ya usado una vez en este proyecto para un caso idéntico (`template_id_admin_1`/`template_id_admin_2`, añadidas y luego eliminadas el mismo día en v1.36/v1.19.53-54 al descubrir que tampoco hacía falta plantilla separada) — nueva migración `2026-09-10_emailjs_quitar_template_proveedor.sql` (`drop column if exists`, segura de ejecutar tanto si la migración de v1.42 llegó a aplicarse en Supabase como si no). "Documentación faltante" pasa a reutilizar `template_id_1`/`template_id_2` — la misma plantilla "de usuario" de siempre — añadiendo `reply_to` a los parámetros que ya se mandaban (`enviarProveedorPorEmailjs`, `services/emailjs.js`); `emailjsConfig.js` pierde `credencialesCuentaProveedor`/`obtenerConfiguracionEmailjsProveedorParaNavegador` (ya sin uso) y vuelve a usar `obtenerConfiguracionEmailjsParaNavegador`, la misma función que ya usaba el correo de usuario. El campo "Template ID (proveedor)" desaparece de Administración → Configuración EmailJS — en su lugar, un aviso junto al Private Key recuerda que el correo a proveedor reutiliza el "Template ID" de arriba y qué necesita ese campo "Reply To" en EmailJS.com.

**Consecuencia práctica**: "Documentación faltante" queda operativo en cuanto el "Template ID" de usuario esté relleno en al menos una cuenta — que para Víctor ya era el caso desde v1.15 — sin ningún paso adicional en EmailJS.com. Si Víctor había llegado a ejecutar la migración de v1.42 en Supabase antes de ver este mensaje, no pasa nada: las columnas quedan simplemente sin usar hasta que se ejecute esta migración de vuelta; si no llegó a ejecutarla, tampoco pasa nada (`drop column if exists`).

**Verificación**: `node --check` en todo el backend, limpio. `npm run build` en frontend, limpio.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.62**.

**Ficheros editados**: `backend/src/services/emailjsConfig.js`, `backend/src/controllers/documentacionController.js`, `backend/src/controllers/configuracionEmailjsController.js`, `frontend/src/services/emailjs.js`, `frontend/src/services/api.js`, `frontend/src/components/admin/AdminConfiguracionEmailjs.jsx`, `database/migraciones/2026-09-10_emailjs_quitar_template_proveedor.sql`.

---

## v1.43 — "Configuración EmailJS" se quedaba en "Cargando…" para siempre si fallaba la carga (v1.19.61)

Víctor, tras desplegar v1.19.60: "no carga esta pantalla después de desplegar la ultima versión" — captura de Administración → Configuración EmailJS, en blanco salvo el texto "Cargando…".

**Causa real, en este caso concreto**: la migración `2026-09-09_emailjs_template_proveedor.sql` (v1.42, la entrega anterior) todavía no se había aplicado en Supabase. `obtenerConfiguracionEmailjs()` (`backend/src/services/emailjsConfig.js`) pide SIEMPRE las 14 columnas de `configuracion_emailjs`, incluidas las 2 nuevas (`template_id_proveedor_1`/`template_id_proveedor_2`) — sin esa migración aplicada, el `SELECT` falla en Postgres con "column ... does not exist", `GET /admin/emailjs-config` responde 500, y el frontend recibe un error al cargar. Aplicar la migración en el SQL Editor de Supabase (el paso manual de siempre, documentado en la propia migración) resuelve esto de inmediato, sin redesplegar nada.

**Pero había un segundo fallo, en el propio componente, que ocultaba el primero**: `AdminConfiguracionEmailjs.jsx` SÍ capturaba ese error y generaba un aviso (`setAviso({tipo: "warn", ...})`), pero el render tenía `if (cargando || !form) { return <"Cargando…"> }` ANTES de llegar al bloque que muestra `aviso` — como un error de carga nunca llega a poner `form` (solo lo hace un `.then` que no se ejecuta si la promesa se rechaza), esa condición se quedaba cierta para siempre y la pantalla mostraba "Cargando…" de forma indefinida, sin que el aviso de error (que sí se había generado) llegara nunca a pintarse. Este fallo es independiente de la causa real de arriba — habría ocurrido igual ante cualquier otro motivo de fallo de carga (sesión caducada, red, lo que sea), y ya existía desde que se creó esta pantalla en v1.15, solo que nunca se había topado con un caso real que lo disparara hasta ahora.

**Corrección**: nuevo estado `errorCarga`, separado del `aviso` genérico (que se autodesvanece a los 4s, pensado para el resultado de "Guardar" — no encaja con un error de carga inicial, que necesita quedarse visible). Si `cargando` es `true` se sigue mostrando "Cargando…"; si termina de cargar y `form` sigue siendo `null`, se muestra el mensaje de error real con un botón "Reintentar" (vuelve a llamar a `cargar()`) en vez de dejar la pantalla en blanco.

**Verificación**: `npm run build` limpio. No se ha podido reproducir el fallo original en este entorno (necesitaría una base de datos real sin la migración aplicada) — la corrección se ha verificado leyendo el flujo de estados a mano; pendiente de que Víctor aplique la migración pendiente de v1.42 y confirme que la pantalla carga con normalidad.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.61** (backend sin cambios de código en esta versión).

**Ficheros editados**: `frontend/src/components/admin/AdminConfiguracionEmailjs.jsx`.

---

## v1.42 — "Documentación faltante" deja de depender de Control de Pedidos para enviarse: EmailJS propio de DALI, con Reply To dinámico (v1.19.60)

Víctor: "necesito que la aplicacion catalogo asignaciones utilice su propio emailjs para solicitar la documentacion faltante, actualmente se encola y se envia desde control pedidos, pero como ya tenemos configurada propia cuenta de emailjs".

**Contexto**: desde v1.15 (v1.19.33), DALI envía por sí mismo casi todos sus correos (recuperación de acceso, bienvenida, aviso a administradores) con su propio EmailJS — la única excepción, dejada anotada explícitamente como "actualización próxima" en la propia migración `2026-09-02_tokens_acceso_emailjs.sql`, era "Documentación faltante": ese correo a proveedor se seguía encolando en `emails_sistema_pendientes` de `control-pedidos-princess` (ver v0.82) y lo enviaba de verdad el poller de esa otra aplicación, la próxima vez que alguien la tuviera abierta en el navegador — normalmente en minutos, pero nunca al momento, y dependiente de una app externa que DALI ya no necesitaba para nada más.

**Qué cambia — el envío, no la resolución del destinatario**: el email del proveedor sigue viniendo exclusivamente de Control de Pedidos (`resolverEmailsProveedorEnControlPedidos`, sin cambios — Víctor no ha pedido tocar eso, y sigue siendo la única fuente real de esos contactos). Lo único que cambia es el mecanismo de ENVÍO:

- `backend/src/controllers/documentacionController.js`: la función `encolarEmailDocumentacionFaltante` pasa a llamarse `prepararEnvioDocumentacionFaltante` (endpoint `POST /admin/documentacion-faltante/:idProveedor/encolar-email` → `POST .../preparar-envio`). Ya no llama a `encolarEmailEnControlPedidos` — en su lugar, resuelve el destinatario y el HTML igual que antes, y además consulta la configuración EmailJS de la plantilla de proveedor (`obtenerConfiguracionEmailjsProveedorParaNavegador`, en `services/emailjsConfig.js`), devolviéndolo todo junto al frontend: destinatario, asunto, HTML, texto, `reply_to` y credenciales EmailJS. Este endpoint ya NO envía nada — solo prepara.
- `frontend/src/services/emailjs.js`: nueva función `enviarProveedorPorEmailjs`, que llama a `emailjs.send()` desde el navegador del admin con lo que acaba de devolver el backend — mismo patrón que `enviarPorEmailjs` (recuperación/bienvenida) desde v1.15, aplicado ahora también aquí.
- `EmailProveedorModal.jsx`: el botón "Encolar envío" pasa a llamarse "Enviar email"; al pulsarlo, primero pide al backend que prepare el envío y después llama a `enviarProveedorPorEmailjs` — el correo sale de verdad al momento, no queda "en cola a la espera de que alguien abra Control de Pedidos". Mensajes de éxito/error actualizados en consecuencia; "Copiar"/"Abrir en tu cliente de correo" se mantienen intactos como alternativa manual.
- `backend/src/services/controlPedidosEmailBridge.js`: se elimina `encolarEmailEnControlPedidos` (ya sin ningún llamador) — el resto del archivo (resolución de emails de proveedor y teléfono de comprador contra Control de Pedidos) sigue en uso, sin cambios.

**Reply To dinámico, sin el truco del puente**: la v1.19.57 (ver v1.39) había resuelto que, al responder este correo, le llegara al comprador que gestionó la solicitud — pero lo hizo modificando el POLLER DE CONTROL DE PEDIDOS para aceptar un `reply_to` por envío, un arreglo que solo tenía sentido mientras el envío pasara por esa app. Con el envío directo, ese mismo resultado se consigue de forma nativa en EmailJS: una plantilla NUEVA y SEPARADA de la de "correo a un usuario" (mismo "sobre" — `to_email`/`asunto`/`mensaje_html`/`mensaje_texto` — más el campo "Reply To" puesto a la variable `{{reply_to}}`, en vez de vacío o fijo). Se añaden dos columnas a `configuracion_emailjs` (`template_id_proveedor_1`/`template_id_proveedor_2`, migración `2026-09-09_emailjs_template_proveedor.sql`) y un campo nuevo por cuenta en Administración → Configuración EmailJS, con las instrucciones exactas (duplicar la plantilla de usuario, añadir `{{reply_to}}` en "Reply To") escritas en el propio formulario. Mismo `public_key`/`service_id` que el resto de la cuenta — solo cambia la plantilla.

**Verificación**: `node --check` en todo el backend, limpio. `npm run build` en frontend, limpio. No se ha podido probar el envío real de punta a punta desde este entorno — necesita la plantilla creada en EmailJS.com en producción, con Reply To configurado — pendiente de que Víctor la cree, pegue el ID en Administración → Configuración EmailJS y confirme un envío real a un proveedor.

**Pendiente de configuración (no bloquea el resto de la app)**: hasta que esa plantilla se cree y su ID se rellene (al menos en una de las 2 cuentas), "Documentación faltante" solo ofrece "Copiar"/"Abrir en tu cliente de correo" para este envío en concreto — igual criterio que ya se aplicaba si el puente con Control de Pedidos fallaba o no estaba configurado.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.60**.

**Ficheros editados**: `backend/src/controllers/documentacionController.js`, `backend/src/services/controlPedidosEmailBridge.js`, `backend/src/services/emailjsConfig.js`, `backend/src/controllers/configuracionEmailjsController.js`, `backend/src/routes/admin.js`, `frontend/src/services/emailjs.js`, `frontend/src/services/api.js`, `frontend/src/components/admin/EmailProveedorModal.jsx`, `frontend/src/components/admin/AdminConfiguracionEmailjs.jsx`, `database/migraciones/2026-09-09_emailjs_template_proveedor.sql`, `README.md`, `backend/README.md`, `frontend/README.md`, `DEPLOY.md`.

---

## v1.41 — Icono (corona Princess) y título "Catálogo Asignaciones" en la pestaña del navegador (v1.19.59)

Víctor pidió que la aplicación se vea en la barra de tareas como Control de Pedidos: "el icono princess y como nombre Catálogo Asignaciones" — adjuntando una captura comparando ambas pestañas: la de Control de Pedidos con la corona junto al nombre, la de DALI con el icono genérico de página y el título "Catálogo DALI".

**Causa**: `frontend/index.html` nunca declaró ningún `<link rel="icon">` (el navegador cae al icono por defecto) y se quedó con el título original del proyecto, `Catálogo DALI`, aunque la propia app ya se presenta como "Catálogo Asignaciones" en la barra lateral y en el login desde hace tiempo (`Sidebar.jsx`, `LoginScreen.jsx`) — el título de la pestaña simplemente no se había actualizado a la vez.

**Cambio**: copiados `favicon.png` (64×64) y `favicon-180.png` (180×180, usado como `apple-touch-icon`) desde `control-pedidos-princess/static/` — el mismo icono de la corona, sin el texto "Princess Hotels & Resorts" — a una carpeta nueva `frontend/public/` (hasta ahora no existía; Vite copia su contenido tal cual a la raíz de `dist/` en cada build, igual que ya hace con `version.json`/`CHANGELOG.md` desde el plugin de aviso de nueva versión). `frontend/index.html`: añadidos los dos `<link>` de icono y cambiado `<title>` a `Catálogo Asignaciones`.

**Verificación**: `npm run build` limpio; confirmado que `favicon.png`/`favicon-180.png` aparecen en `dist/` junto a `index.html` tras el build, y que Render los serviría directamente (comprobación de fichero real antes de aplicar la regla de reescritura de la SPA), igual que ya ocurre con los otros dos ficheros estáticos generados en build. Sin cambios de backend.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.59** (backend sin cambios de código en esta versión — se sube igual para mantener sincronizados los dos `package.json`).

**Ficheros editados/nuevos**: `frontend/index.html`, `frontend/public/favicon.png` (nuevo), `frontend/public/favicon-180.png` (nuevo).

---

## v1.40 — Auditoría de la versión desplegada (v1.19.57): documentación desactualizada corregida en tres puntos (v1.19.58)

Víctor subió la versión que tenía desplegada en producción y pidió una auditoría completa ("puedes auditar que este todo en su sitio, no falte nada y todo debidamente actualizado?"), la misma tarea que se le hizo antes al repo de Control de Pedidos.

**Código**: sin hallazgos. `node --check` limpio en todo `backend/src`, `npm run build` limpio en `frontend`. Se revisó explícitamente la cadena de autenticación/permisos (`middleware/auth.js`: `requireAuth` → `requireAdmin` → `requierePermiso(clave)`) y se confirmó que `backend/src/routes/admin.js` aplica `requierePermiso` en las 177 líneas/todas las rutas sin ninguna excepción, y que el resto de rutas que usan `optionalAuth` o ningún guard (`articulos.js`, `estadisticas.js`, `export.js`, `jerarquia.js`, `auth.js`) lo hacen de forma intencionada y justificada (endpoints públicos genuinos, como las estadísticas del catálogo). También se comprobó `backend/.env.example` y `render.yaml` contra todos los usos reales de `process.env.*`: consistentes.

**Documentación — tres desajustes encontrados y corregidos**:

1. **`CHANGELOG.md` sin entrada para `[1.19.57]`**: esa entrega ya estaba documentada aquí (v1.39, más arriba) pero nunca se trasladó al `CHANGELOG.md` corto. Añadida a posteriori, con el mismo contenido.
2. **Pendientes obsoletos en `README.md` y `backend/README.md`**: ambos seguían listando como pendiente rellenar las credenciales de la Cuenta 1 de EmailJS y crear la plantilla de aviso a administradores — ambas cosas resueltas y confirmadas funcionando en producción desde v1.16/v1.38 (ver más abajo, "Pendientes acumulados"). Corregido: solo queda pendiente la Cuenta 2 (no bloquea el uso normal, solo entra en juego por rotación automática al llegar al umbral de envíos).
3. **`schema.sql` no advertía de que por sí solo no basta**: comprobando `database/schema.sql` contra las 15 migraciones en `database/migraciones/`, faltan en el esquema base tablas y columnas que el código actual da por hechas — `marcas_proveedor` (y sus dos tablas asociadas de imágenes/fichas), `solicitudes_acceso`, `tokens_acceso`, `configuracion_emailjs`, y los permisos granulares de administrador (`es_admin_principal`/`permisos`) en `usuarios`. Se decidió con Víctor documentar el hueco en vez de fundir las migraciones en `schema.sql` (opción "Solo documentar", más simple y sin riesgo de introducir un error al fusionar 15 ficheros a mano) — añadida la advertencia y el paso explícito de aplicar `database/migraciones/*.sql` en orden de fecha, en `README.md` y `database/README.md`.

**Sin cambios de código** — auditoría y documentación únicamente.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.58** (se sube igual, sin cambios de código, para mantener sincronizados los dos `package.json` según la convención de v1.17.1 — mismo precedente que v1.19.39).

**Ficheros editados**: `README.md`, `backend/README.md`, `database/README.md`, `CHANGELOG.md`, `HISTORIAL.md` (esta entrada), `backend/package.json`, `frontend/package.json`.

---

## v1.39 — El correo de "Documentación faltante" ya no responde al propio proveedor: el "Responder a" pasa a ser el comprador que lo gestiona (v1.19.57)

A petición de Víctor, tras revisar un correo real de "Documentación pendiente — BRIGONSA GROUP 2015 SL": el proveedor, al pulsar "Responder", veía su propia dirección como destino en vez de la del comprador que había gestionado la solicitud desde DALI — pidió que fuera configurable, "por ejemplo, grabar qué responder a... el correo del comprador".

**Causa**: el envío real de este correo lo hace Control de Pedidos (repo `control-pedidos-princess`, aparte), a través del puente que reutiliza su cola `emails_sistema_pendientes` (ver v1.15). Su poller (`_enviarEmailsSistemaPendientes`, `templates/index.html`) fijaba `reply_to: p.destinatario` para TODA esa cola, sin ninguna excepción para el evento `dali_documentacion_faltante` — comportamiento correcto para el resto de eventos (avisos internos a admins/compradores, donde da igual), pero incorrecto para un correo saliente a un proveedor externo.

**Cambio (solo lado DALI de este puente)**: `encolarEmailEnControlPedidos()` (`services/controlPedidosEmailBridge.js`) acepta ahora un parámetro opcional `replyTo`, que viaja como `reply_to` en el body de `POST /api/externo/dali-sap/emails-pendientes`. `encolarEmailDocumentacionFaltante()` (`controllers/documentacionController.js`) lo rellena con `req.user.email` — el mismo email de sesión que ya usa `resolverFirmaAdmin()` para firmar el cuerpo del correo (nombre/teléfono/email del admin que gestiona), así que no hace falta resolver ni guardar ningún dato nuevo en DALI: el comprador que pidió la documentación es, por diseño, quien ha iniciado sesión.

El resto del arreglo (columna `reply_to` en `emails_sistema_pendientes`, el propio endpoint del puente aceptándola, y el poller usándola con `p.reply_to || p.destinatario` como antes) vive en el repo de Control de Pedidos — ver su `CHANGELOG.md`/`docs/HISTORIAL_CAMBIOS.md`, entrega v12.32.43 (renumerada desde v12.32.42 al comprobar que esa versión ya estaba en uso en producción por un cambio real y no relacionado — OCR de PDF firmado/escaneado —, ver esa misma entrega para el detalle).

**Verificación**: `node --check` en los dos archivos backend tocados, limpio. Sin acceso a Control de Pedidos real desde este entorno, no se ha probado el envío de punta a punta — pendiente de que Víctor despliegue los dos repos y confirme en Email History (EmailJS) que el "Reply-To" del correo de "Documentación faltante" ya es el email del comprador, no el del proveedor.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.57** (frontend sin cambios en esta versión — se sube igual para mantener sincronizados los dos `package.json`).

**Ficheros editados**: `backend/src/services/controlPedidosEmailBridge.js`, `backend/src/controllers/documentacionController.js`.

---

## v1.38 — Diagnóstico: el aviso a administradores no llegaba tras rellenar la Private Key (sin cambios de código)

Víctor aplicó las migraciones `2026-09-05_emailjs_admin_backend.sql`/`2026-09-05_emailjs_quitar_template_admin.sql` y rellenó la Private Key de la Cuenta 1 en Administración → Configuración EmailJS (ver pendiente de v1.36), pero el aviso a administradores seguía sin llegar tras una solicitud de acceso — reportado como fallo de "la última actualización".

**Diagnóstico, sin tocar código**: revisando el circuito completo (migración → columna `private_key_1` → guardado desde el panel → `enviarAvisoAdministradores()` → llamada REST a EmailJS) no apareció ningún bug — todo el código de v1.35/v1.36 (v1.19.53/54) es correcto. Dos falsos negativos por el camino antes de dar con la causa real:

1. Una primera prueba pareció no dejar rastro en el historial de EmailJS porque la fila que se veía (`Template ID: __ejs-test-mail-service__`) era en realidad el botón "Test It" del panel de EmailJS.com, no un envío de la app.
2. Una segunda prueba, con un email que ya había estado dado de alta y se había borrado, tampoco disparó ningún envío — pero no por el cooldown de 3 minutos (`_dentroDeCooldown`, ya había pasado tiempo de sobra), sino porque ya existía una fila `pendiente` en `solicitudes_acceso` para ese mismo email de un intento anterior: `registrarSolicitudAcceso()` corta en `if (existente) return;` sin volver a intentar el envío, y el mensaje genérico de éxito que ve quien lo pide no distingue este caso (a propósito, por diseño, para no revelar si un email existe).

**La causa real**, encontrada en los logs de Render: `EmailJS respondió 403: API access from non-browser environments is currently disabled`. La cuenta EmailJS de DALI tenía desactivado por defecto el acceso a su API REST desde fuera del navegador — ajuste de la propia cuenta EmailJS.com (Account → Security → "Allow API calls"), no relacionado con la Private Key en sí ni con nada del repositorio. Con ese ajuste activado, una solicitud de prueba y una solicitud real de un compañero llegaron correctamente el mismo día (ver Email History: dos filas `OK` con `Template: Contact Us`, `Service: CatalogoAsignacionesDaliSap`).

De paso, Víctor corrigió también el "From Name" de la plantilla EmailJS (Cuenta 1) en el propio panel de EmailJS.com, de "Control de Pedidos Princess" a "Central Compras Princess Canarias" — cambio cosmético pendiente desde v1.16, sin relación con el fallo de arriba.

**Sin cambios de código en esta entrega** — ni de versión de `package.json` — todo lo corregido fue configuración externa (EmailJS.com) más las migraciones y la Private Key que ya había aplicado Víctor. Se deja esta entrada por el valor de diagnóstico: si el aviso a administradores vuelve a fallar en el futuro (p.ej. al configurar la Cuenta 2, o tras crear una cuenta EmailJS nueva), revisar primero el mismo ajuste "Allow API calls" antes de sospechar del código.

---

## v1.37 — Exige código de proveedor guardado antes de subir imagen o ficha manualmente (v1.19.56)

A petición de Víctor: al gestionar la documentación de un artículo desde Administración → Artículos, era posible subir la imagen o una ficha (técnica o de seguridad) de un proveedor ANTES de haber guardado el código con el que ese proveedor identifica el artículo — dejando el archivo grabado sin ninguna forma de saber a qué código de proveedor corresponde, hasta que alguien se acordara de rellenarlo después. Afecta solo a la subida **manual** por tarjeta (`ArticuloForm.jsx`); la carga masiva por carpetas (`CargaMasivaModal.jsx`) no se toca en esta entrega, al depender ya de un nombre de archivo con el código incluido.

**Cambio**: en `TarjetaDocumentacion` (subcomponente de `ArticuloForm.jsx`, reutilizado tanto para la tarjeta de un proveedor —campo `codigo_proveedor`— como para una marca extra suya —campo `codigo`, ver `SeccionMarcas`—), los selectores de archivo de imagen y de cada ficha se deshabilitan mientras esa tarjeta no tenga código guardado, con un aviso justo encima explicando qué falta: "Para poder subir imagen o fichas de este proveedor, primero indica su código de proveedor arriba y pulsa 'Guardar'." En cuanto se guarda el código, el aviso desaparece y los selectores se habilitan solos, sin recargar nada. Como red de seguridad adicional, `handleSubirImagen`/`handleSubirFicha` repiten la misma comprobación antes de llamar al backend, por si el archivo llegara a seleccionarse por otra vía.

**Verificación**: `npx esbuild` sobre `ArticuloForm.jsx` (bundle, sin errores de sintaxis/JSX) — sin acceso a un backend/Supabase real desde este entorno, no se ha podido probar el flujo de punta a punta; pendiente de que Víctor lo confirme en la app real.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.56**.

**Ficheros editados**: `frontend/src/components/admin/ArticuloForm.jsx`, `frontend/README.md`.

---

## v1.36 — Se elimina el template separado de aviso a administradores: ya no hacía falta (v1.19.54)

A petición de Víctor tras preguntar si seguía siendo necesario un template EmailJS separado para el aviso a administradores, ahora que ese envío lo hace el backend (v1.19.53): revisando `utils/emailHtml.js` se confirma que NO hacía falta. El HTML completo del correo (cabecera, título, cuerpo, botón) lo genera siempre el propio backend en JavaScript y viaja como parámetro (`mensaje_html`/`mensaje_texto`/`asunto`) — la plantilla de EmailJS en sí es un "sobre" genérico idéntico en los dos casos (correo a un usuario y aviso a administradores): mismas 4 variables (`to_email`, `asunto`, `mensaje_html`, `mensaje_texto`), nada más. El template separado (`template_id_admin_1`/`template_id_admin_2`, añadido en v1.34/v1.19.52) solo existía porque en aquel diseño una plantilla necesitaba `to_email` fijo y la otra como variable — motivo ya superado desde que el backend rellena `to_email` como variable en los dos casos por igual (v1.19.53).

**Cambio**: se eliminan las columnas `template_id_admin_1`/`template_id_admin_2` (migración `2026-09-05_emailjs_quitar_template_admin.sql`) — el aviso a administradores reutiliza `template_id_1`/`template_id_2`, las mismas plantillas de siempre. `credencialesCuentaAdmin()` (`services/emailjsConfig.js`) usa ahora `template_id_N` en vez de `template_id_admin_N`; sigue exigiendo `private_key_N` (eso sí distingue de verdad un envío del navegador de uno del backend). "Administración → Configuración EmailJS" pierde el campo "Template ID (aviso a administradores)" — un campo menos que rellenar por cuenta, solo queda Private Key como novedad.

**Verificación**: `node --check` en los archivos backend y `.js` de frontend tocados, limpio; revisión visual del JSX. Grep de todo el repo confirma que no queda ninguna referencia viva a `template_id_admin` fuera de las migraciones históricas (que no se editan, ver convención del proyecto).

Versión: `backend/package.json` y `frontend/package.json` → **1.19.54**.

**Ficheros NUEVOS en esta entrega**: `database/migraciones/2026-09-05_emailjs_quitar_template_admin.sql`.
**Ficheros editados**: `backend/src/services/emailjsConfig.js`, `backend/src/controllers/configuracionEmailjsController.js`, `frontend/src/services/api.js`, `frontend/src/components/admin/AdminConfiguracionEmailjs.jsx`.

---

## v1.35 — El aviso a administradores pasa a enviarlo el backend, no el navegador (v1.19.53)

Corrige un fallo en el propio diseño de v1.34/v1.19.52 (misma sesión, mismo día): fijar el destinatario del aviso a administradores directamente en el panel de EmailJS ("To email" fijo, sin variable) solo funciona si esa lista nunca cambia — y en DALI los administradores se dan de alta/baja desde Administración → Usuarios, así que habría exigido entrar a mano en EmailJS.com cada vez que cambiara quién es admin, con riesgo real de desincronizarse. Víctor lo hizo notar al intentar rellenar ese campo.

**La causa real** nunca fue que el destinatario no pudiera ser dinámico — fue que esa llamada a EmailJS la disparaba el navegador del visitante anónimo que pide "¿Has olvidado tu contraseña?", así que cualquier dato que viajara en ella (la lista de emails en v1.19.52-anterior-al-fix, o incluso solo qué plantilla se usa) quedaba visible inspeccionando DevTools → Red.

**La corrección**: mover ESTA llamada en concreto al backend. `registrarSolicitudAcceso()` (`authController.js`) resuelve ahora los administradores activos consultando `usuarios` (dinámico, como siempre) y llama a la función nueva `enviarAvisoAdministradores()` (`services/emailjsConfig.js`), que llama DIRECTAMENTE a la API REST de EmailJS (`https://api.emailjs.com/api/v1.0/email/send`) autenticándose con la **Private Key** de la cuenta (no la Public Key) — el navegador no interviene en ningún momento en este envío, así que no hay nada que un visitante pueda inspeccionar, y el destinatario sigue siendo dinámico sin mantenimiento manual. `registrarSolicitudAcceso()` ya no devuelve ningún `envio` para esta rama — el correo se envía y se registra (contador/rotación, mismo mecanismo de siempre) enteramente en el servidor, best-effort (si falla, la solicitud queda igual registrada y visible en Administración → Solicitudes de acceso). El template de aviso a administradores debe llevar ahora `{{to_email}}` como variable (no fijo, al revés de lo que pedía v1.19.52) — el backend la rellena en cada envío.

Columnas nuevas `private_key_1`/`private_key_2` en `configuracion_emailjs` (migración `2026-09-05_emailjs_admin_backend.sql`) — **nunca** se exponen al navegador: `obtenerConfiguracionEmailjsParaNavegador()` ya no devuelve nada del aviso a administradores en absoluto (antes exponía sus credenciales de plantilla). "Administración → Configuración EmailJS" tiene un campo nuevo "Private Key (aviso a administradores)" por cuenta (`type="password"`).

**Verificación**: `node --check` en los archivos backend y en los `.js` de frontend tocados, limpio; revisión visual del JSX modificado. Sin acceso a una cuenta EmailJS real ni a Supabase desde este entorno, no se ha podido probar un envío de punta a punta — pendiente de que Víctor: (1) aplique la migración nueva, (2) cambie el campo "To email" de la plantilla "aviso a administradores" (Cuenta 1) de vuelta a variable (`{{to_email}}`), y (3) rellene la Private Key de esa cuenta (EmailJS.com → Account → Security → API Keys) en Administración → Configuración EmailJS.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.53**.

**Ficheros NUEVOS en esta entrega**: `database/migraciones/2026-09-05_emailjs_admin_backend.sql`.
**Ficheros editados**: `backend/src/controllers/authController.js`, `backend/src/services/emailjsConfig.js`, `backend/src/controllers/configuracionEmailjsController.js`, `frontend/src/services/emailjs.js`, `frontend/src/services/api.js`, `frontend/src/components/admin/AdminConfiguracionEmailjs.jsx`.

---

## v1.34 — Revisión de seguridad de v1.15: el aviso a administradores filtraba sus emails a cualquier visitante anónimo (v1.19.52)

Al revisar la "decisión de diseño pendiente" que había quedado anotada explícitamente en v1.15 (ver ese comentario grande en `authController.js`) apareció un problema más grave del que sugería esa nota original — dos problemas distintos, no uno:

**1. (GRAVE, corregido en esta entrega) Filtrado de emails de administradores a cualquier visitante anónimo.** Al pedir "¿Has olvidado tu contraseña?" con un email NO registrado, `POST /auth/recuperar-acceso` respondía siempre con el mismo mensaje genérico de siempre — pero el propio JSON de esa respuesta incluía un campo `envio.destinatario` con la lista completa de emails de administradores activos, para que el frontend se la pasara a EmailJS. Cualquiera, con sesión o sin ella, podía verla con solo abrir DevTools → Red y mirar la respuesta de esa llamada, sin que el correo llegara siquiera a enviarse — un único intento con un email cualquiera que no existiera bastaba para obtener la lista completa de administradores del sistema, direcciones que no se muestran en ninguna otra pantalla no-admin de la aplicación.

**2. (menor, ACEPTADO como riesgo residual conocido, no se toca en esta entrega) Enumeración de emails registrados.** Aunque se corrija el punto 1, sigue siendo observable, mirando esa misma llamada a EmailJS, si un email concreto está o no registrado (asunto y forma de destinatario distintos entre las dos ramas). Cerrarlo del todo exigiría un rediseño mayor (dejar de enviar el correo desde el navegador para este caso, volviendo a encolarlo en el servidor). Dada la naturaleza de la aplicación (interna, acceso restringido a quien tenga la URL, exige inspeccionar DevTools a propósito), se documenta y se acepta tal cual salvo que Víctor prefiera en el futuro ese rediseño mayor.

**La corrección del punto 1.** Cada una de las 2 cuentas EmailJS de DALI pasa a tener DOS templates en vez de uno (columnas nuevas `template_id_admin_1`/`template_id_admin_2` en `configuracion_emailjs`, ver migración `2026-09-05_emailjs_template_admin.sql`): el de siempre, para correos a un usuario concreto (recuperación/bienvenida, destinatario = esa misma persona, sin nada que filtrar), y uno nuevo, exclusivo para el aviso a administradores, con el destinatario fijado directamente en el panel de EmailJS (campo "To email" de la plantilla) en vez de recibido como parámetro `to_email` desde el navegador. `registrarSolicitudAcceso()` (`authController.js`) deja de construir y devolver `envio.destinatario` con la lista de admins — solo comprueba que exista al menos uno activo antes de seguir. El `envio` que prepara cada función ahora lleva un campo `tipo` ("usuario" o "admin") para que `services/emailjs.js` (frontend) elija la plantilla/credenciales correctas y, en el caso "admin", nunca incluya ningún parámetro `to_email` en la llamada a EmailJS — así, aunque alguien inspeccione DevTools → Red, esa llamada ya no contiene ninguna dirección de administrador. `services/emailjsConfig.js` (backend) resuelve por separado las credenciales de la plantilla "usuario" y de la "admin" (pueden faltar independientemente: si la de "admin" no está configurada todavía, ese aviso concreto simplemente no se envía por correo, la solicitud se sigue registrando igual — mismo criterio best-effort que ya regía el resto del flujo). "Administración → Configuración EmailJS" (`AdminConfiguracionEmailjs.jsx`) tiene ahora un segundo campo "Template ID (aviso a administradores)" por cuenta, con la advertencia de fijar el destinatario en el propio panel de EmailJS.

**Verificación**: `node --check` en los archivos backend tocados, limpio. Revisión manual del nuevo flujo en `services/emailjs.js`: confirmado que el objeto pasado a `emailjs.send()` para `tipo: "admin"` no incluye la clave `to_email` en ningún caso. Sin acceso a una cuenta EmailJS real ni a Supabase desde este entorno, no se ha podido probar un envío de punta a punta — pendiente de que Víctor cree la plantilla "admin" en el panel de EmailJS (Cuenta 1, la que ya está en producción) y rellene el campo nuevo en Administración → Configuración EmailJS antes de que el aviso a administradores vuelva a enviarse por correo.

Documentos de mantenimiento revisados en esta entrega: `HISTORIAL.md` (esta misma entrada); `README.md`, `backend/README.md`, `frontend/README.md`, `backend/.env.example`, `DEPLOY.md` — revisados, no aplica ningún cambio (sin variables de entorno nuevas; la migración nueva solo añade columnas, no requiere ningún paso de despliegue distinto de las anteriores).

Versión: `backend/package.json` y `frontend/package.json` → **1.19.52**.

**Ficheros NUEVOS en esta entrega**: `database/migraciones/2026-09-05_emailjs_template_admin.sql`.
**Ficheros editados**: `backend/src/controllers/authController.js`, `backend/src/services/emailjsConfig.js`, `backend/src/controllers/configuracionEmailjsController.js`, `frontend/src/services/emailjs.js`, `frontend/src/services/api.js`, `frontend/src/components/admin/AdminConfiguracionEmailjs.jsx`.

---

## v1.33 — La imagen genérica "SIN IMAGEN" seguía repitiéndose por artículo, esta vez de verdad corregido (v1.19.51)

Víctor probó la corrección de v1.19.50 exportando un proveedor real (AHUMADOS CANARIOS SA) y mandó el zip resultante: la imagen "SIN IMAGEN" seguía descargándose una vez por cada artículo (44 archivos .png, todos con nombre distinto siguiendo el nuevo criterio código+artículo) en vez de una sola vez. Comprobando el propio zip con `md5sum` se confirmó que los 44 archivos eran byte a byte idénticos — la deduplicación de v1.19.50 no había funcionado, y por dos motivos distintos, ninguno de los dos cubierto por esa entrega:

**1. `es_generica` no basta por sí sola en filas antiguas.** La columna se añadió el 2026-09-01 (migración `2026-09-01_es_generica_imagen.sql`) con `default false` — cualquier fila de `imagenes` subida ANTES de esa fecha se quedó con `es_generica = false` aunque de verdad fuera la "SIN IMAGEN" del proveedor, porque nadie retroetiquetó las filas ya existentes al desplegar la migración. `documentacionController.js` ya tenía resuelto exactamente este mismo problema desde antes (ver su comentario largo sobre `conteoHashPorProveedor`): si `es_generica` no viene marcado, un `hash_sha256` compartido por MÁS DE UN artículo del mismo proveedor es la señal de que es la imagen de reserva y no una foto propia real (una foto propia solo por pura casualidad compartiría hash exacto con otro artículo). `exportarDocumentacionZip()` (`exportZipController.js`) no tenía esta red de seguridad — solo miraba `es_generica`, así que las 44 filas de AHUMADOS CANARIOS SA (subidas antes de la migración) cayeron en "imagen propia" y se nombraron una a una.

**2. Aunque `es_generica` hubiera venido marcado, la deduplicación tampoco habría funcionado.** La entrega anterior deduplicaba por "proveedor + ruta de Storage" (`im.url_imagen`), asumiendo que el archivo físico se reutilizaba entre artículos. Pero `subirImagenArticulo` (`storageController.js`) guarda cada imagen en `<código_dali>/<proveedor>.<extensión>` — una ruta DISTINTA por artículo, aunque el contenido sea exactamente el mismo archivo "SIN IMAGEN" repetido. Con rutas siempre distintas, la clave de deduplicación de v1.19.50 nunca podía coincidir entre dos filas, así que en la práctica no deduplicaba nada, ni siquiera para filas ya marcadas `es_generica = true` correctamente.

**La corrección.** Se añadió `hash_sha256` al `select()` de `imagenes` y una función `esImagenGenerica()` que combina las dos señales, en ese orden de prioridad: `es_generica === true` explícito si está presente, y si no, el mismo criterio de hash compartido que ya usa `documentacionController.js` (mismo límite ya documentado ahí: una fila sin ningún hash guardado — subida antes de la migración `2026-08-18_hash_documentos.sql` y nunca vuelta a subir desde entonces — no se puede distinguir por esta vía y se trata como propia, igual que en esa otra pantalla). La deduplicación de descargas pasó de "proveedor + ruta de Storage" a "proveedor + hash" — agrupa de verdad por CONTENIDO, sea cual sea la ruta física de cada fila; si alguna fila genérica no tiene hash guardado (detectada solo por `es_generica` explícito), se agrupa por proveedor sin más, asumiendo que solo hay una imagen genérica activa por proveedor a la vez — mismo supuesto ya usado por `DELETE /admin/proveedores/:id/imagen-generica`, que borra TODAS las filas `es_generica = true` de un proveedor de una sola vez.

**Verificación**: `node --check` en `exportZipController.js`, limpio. Prueba con datos simulados calcados del caso real de Víctor (script en `/tmp`, no forma parte del repositorio): 44 filas del mismo proveedor con el mismo hash, ruta de Storage distinta por artículo (como en el zip real recibido) y `es_generica = false` (simulando una carga previa a la migración), más una fila de foto propia real de otro artículo con hash distinto — resultado: las 44 se detectan como genéricas y colapsan en 1 sola entrada a descargar, y la foto propia no se ve afectada. Sin acceso a Supabase real desde este entorno, es la validación más cercana posible sin desplegar.

Documentos de mantenimiento revisados en esta entrega: `HISTORIAL.md` (esta misma entrada); `CHANGELOG.md` (actualizado); `backend/README.md`, `frontend/README.md`, `README.md`, `backend/.env.example`, `DEPLOY.md` — revisados, no aplica ningún cambio (mismo endpoint de antes, sin variables de entorno nuevas ni migración de base de datos nueva).

Versión: `backend/package.json` y `frontend/package.json` → **1.19.51** (frontend sin cambios en esta versión, se sube igual para mantener sincronizados los dos `package.json`).

**Ficheros NUEVOS o BORRADOS en esta entrega**: ninguno. Todos los cambios de código de esta entrega son ediciones de ficheros que ya existían.

---

## v1.32 — "Exportar documentación" nombra los archivos con el artículo, y ya no repite la imagen genérica por cada uno (v1.19.50)

Víctor mandó una captura de la pantalla "Administración · Exportar documentación" con dos peticiones sobre el mismo zip: "necesito que a cada archivo a exportar se le nombre de la siguiente manera, código proveedor _ y el nombre del articulo en DALI" y, aparte, que cuando la imagen asociada a un artículo es la común "SIN IMAGEN" de su proveedor, esta se descargue una única vez y no repetida con cada uno de los artículos que la tienen asignada — "solo descargar por separado las imágenes propias del articulo".

**El nombre de archivo.** `exportarDocumentacionZip()` (`exportZipController.js`) nombraba hasta ahora cada ficha técnica, ficha de seguridad e imagen solo con el código de proveedor guardado en `codigos_proveedor` para ese artículo (o `SIN-CODIGO-DALI-<código dali>` si todavía no estaba grabado — el mismo caso ya resuelto desde `documentacionController.js` y la carga masiva de códigos por Excel). Las consultas de `fichas`/`imagenes` no traían el nombre del artículo porque nunca hacía falta para nada más que agrupar por proveedor; se añadió `nombre_articulo` al `select()` de las dos (`articulos!inner(codigo_dali, nombre_articulo)`) y el nombre de archivo pasó a ser `<código proveedor o SIN-CODIGO-DALI-...>_<nombre del artículo>`, con el nombre del artículo limpiado por el mismo `nombreSeguro()` que ya se usaba para el nombre de la carpeta de proveedor (mismos caracteres problemáticos: comas, puntos, paréntesis... habituales también en nombres de artículo).

**La imagen genérica.** El motivo de fondo ya estaba resuelto en otra entrega (`2026-09-01_es_generica_imagen.sql`): cuando un proveedor sube su "SIN IMAGEN" de reserva en la carga masiva, se graba una fila en `imagenes` por cada artículo suyo sin foto propia, todas apuntando a la MISMA ruta física en Supabase Storage, con `es_generica = true` para poder distinguirlas de una foto real. El export de documentación nunca había mirado esa columna — trataba cada fila igual, así que un proveedor con 40 artículos sin foto propia acababa con el mismo archivo "SIN IMAGEN" descargado y comprimido 40 veces dentro de su carpeta IMAGENES. Se añadió `es_generica` al `select()` de `imagenes` y, antes de construir la lista de descargas, las filas genéricas se separan del resto y se deduplican por `proveedor + ruta de Storage` (no por artículo — varios artículos del mismo proveedor comparten la misma fila física) en un `Map`, así que cada archivo físico distinto se descarga y se empaqueta una sola vez. Al no pertenecer a ningún artículo en concreto, no lleva el nuevo nombre `código_artículo`: se guarda con nombre fijo `SIN IMAGEN.<extensión>` dentro de `<Proveedor>/IMAGENES/`, en su propio bucle separado del de fichas+imágenes propias (mismo patrón de `procesarEnParalelo` con concurrencia limitada, mismo manejo de fallos por archivo sin tumbar el zip entero) pero compartiendo el mismo `Map` de "nombres ya usados por carpeta" para que nunca colisione con una foto propia real que por casualidad se llamara igual.

Se actualizó también el texto descriptivo de la propia pantalla (`AdminExportarZip.jsx`) para reflejar el nuevo criterio de nombrado y la deduplicación de "SIN IMAGEN", y la nota de abajo sobre artículos sin código de proveedor grabado, para que mencione que ahora el nombre de archivo lleva también el nombre del artículo.

**Verificación**: `node --check` en `exportZipController.js`, limpio. Revisados a mano los casos límite ya documentados en el propio fichero: dos artículos del mismo proveedor con el mismo código de proveedor (`nombreUnico` sigue resolviendo el choque con " (2)", " (3)"...); artículo sin código de proveedor grabado (prefijo `SIN-CODIGO-DALI-<código dali>`, ahora seguido del nombre del artículo); y un proveedor con la imagen genérica asignada a varios artículos a la vez (una sola descarga, una sola entrada en el zip).

Documentos de mantenimiento revisados en esta entrega: `HISTORIAL.md` (esta misma entrada); `CHANGELOG.md` (actualizado); `backend/README.md` (actualizado — fila de `/admin/documentacion-zip` con el nuevo criterio de nombrado); `frontend/README.md` (actualizado — descripción de "Exportar documentación"); `README.md`, `backend/.env.example`, `DEPLOY.md` — revisados, no aplica ningún cambio (no hay ninguna variable de entorno nueva, ningún endpoint nuevo, ninguna migración de base de datos — `es_generica` ya existía desde la entrega del 2026-09-01 — ni ningún paso de despliegue adicional).

Versión: `backend/package.json` y `frontend/package.json` → **1.19.50** (frontend sin cambios de lógica en esta versión, solo texto — se sube igual para mantener sincronizados los dos `package.json`).

**Ficheros NUEVOS o BORRADOS en esta entrega**: ninguno. Todos los cambios de código de esta entrega son ediciones de ficheros que ya existían.

---

## v1.31 — La marca del sidebar ya no se parte en dos líneas (v1.19.49)

Corrección pequeña, a caballo de la entrega anterior. Víctor mandó dos capturas comparando la marca del login ("Catálogo Asignaciones" en una línea, limpio) con la de la barra lateral ("Catálogo Asignaciones" seguido de "- SAP" cayendo suelto en su propia línea, torcido) y un comentario corto: "me gusta mas como esta en el login". El motivo era simple: "Asignaciones" pesa más que "DALI", y en los 219px de ancho de `.sidebar-brand` (bastante más estrecho que la tarjeta de login, centrada y con más aire) el texto completo ya no cabía en una línea — algo que con el nombre antiguo, más corto, nunca había pasado. Se quitó el "- SAP" final de esa línea, dejando solo "Catálogo Asignaciones", igual de limpio que el título del login; el subtítulo de debajo ("Índice de artículos") no cambia. Comprobado con una captura real (Playwright, sesión de admin en modo demo) antes de dar la entrega por buena — la manera más directa de verificar un ajuste puramente visual.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.49** (backend sin cambios en esta versión — se sube igual para mantener sincronizados los dos `package.json`).

**Ficheros NUEVOS o BORRADOS en esta entrega**: ninguno.

---

## v1.30 — "Catálogo DALI" pasa a ser "Catálogo Asignaciones" también en los correos y en el resto de pantallas de acceso (v1.19.48)

Víctor mandó dos capturas de la cabecera de un correo de "Recuperar acceso" — fondo azul oscuro, logo de Princess, título "Recuperar acceso" y debajo "Catálogo DALI · Central de Compras Canarias" — con una petición concreta: "me puedes cambiar todas las cabeceras de los correos? No es Catálogo DALI --> Catálogo Asignaciones, no es Central de Compras Canarias --> Central de Compras Princess Canarias; revisa pantalla Login, esto lo cambiamos hace unas cuantas actualizaciones".

La pista de "esto lo cambiamos hace unas cuantas actualizaciones" era clave: `LoginScreen.jsx` en efecto ya decía "Catálogo Asignaciones" desde hace tiempo — el cambio de nombre ya se había hecho, pero solo ahí. Un repaso por el resto del proyecto encontró el mismo texto antiguo, "Catálogo DALI" y/o "Central de Compras Canarias", sobreviviendo en bastantes más sitios de los que sugería la propia captura de Víctor:

- Los tres correos que genera de verdad la aplicación (`backend/src/utils/emailHtml.js`, `backend/src/controllers/authController.js`): la cabecera con logo (justo la de la captura), el asunto y el cuerpo del correo de acceso de un solo uso (recuperación y bienvenida), y el aviso a administradores cuando alguien pide acceso con un email nuevo.
- La firma de los correos de reclamación de documentación a proveedores (`EmailProveedorModal.jsx`): "Dpto. Central de Compras Canarias" — un correo real que sale de la aplicación hacia fuera, a proveedores externos, con la firma de quien lo envía.
- `CanjearTokenAcceso.jsx` — la pantalla de "Elige tu contraseña" que se abre al pulsar el propio enlace del correo. Esta es la pieza que de verdad explica el "revisa pantalla Login" de Víctor: es la otra mitad de la misma familia de pantallas que `LoginScreen.jsx` (incluso comparte las mismas clases CSS, `login-shell`/`login-card`/`login-brand`), pero al cambiar el nombre en el login en su momento, esta pantalla hermana se quedó fuera y seguía diciendo "Catálogo DALI".
- Dos sitios más, encontrados por la misma inconsistencia aunque no estaban en lo que pidió Víctor explícitamente: la marca de la barra lateral una vez dentro de la aplicación (`Sidebar.jsx`: "Catálogo DALI - SAP", visible constantemente para cualquier persona con sesión iniciada) y la descripción de las cuentas EmailJS en Administración → Configuración EmailJS. Se corrigieron también — dejar "Catálogo DALI" ahí, justo después de haber "arreglado todo", habría sido la clase de detalle que Víctor nota enseguida.
- Los asuntos de correo simulados en modo demo (`services/api.js`) — no se envía ningún correo real en demo, pero el texto que se enseña como vista previa se actualizó igual, para que no aparezca la marca antigua ni en una prueba.

Deliberadamente NO se ha tocado: el título del propio `README.md` del repositorio ("Catálogo DALI — Consulta de Artículos/Materiales") ni el nombre del repositorio en sí (`dali-sap-articulos-app`) — son identidad del proyecto de cara a quien lo mantiene, no texto que vea un usuario de la aplicación, y cambiarlos es una decisión de otro calibre que Víctor no ha pedido; se le avisa por si quiere abordarlo aparte. Tampoco se han tocado los comentarios de código que mencionan "Catálogo DALI" como contexto histórico (por qué se hizo algo en su momento) — reescribir esos sería alterar el propio relato de por qué existe el código, no una corrección de texto visible.

Efecto colateral encontrado y arreglado de paso: el proyecto tiene un harness de pruebas aislado (`tokenaccesotest/`) con copias propias de `authController.js`/`emailHtml.js` para poder probarlos sin tocar Supabase de verdad — esas copias se habían quedado desincronizadas de los ficheros reales en cuanto se editó el texto, así que se han vuelto a sincronizar, y la única aserción que comprobaba el asunto exacto del correo (`verify.mjs`) se ha actualizado al nuevo texto.

**Verificación**: `npx vite build`, limpio; `node --check` en todo `backend/src/`, limpio. `tokenaccesotest/verify.mjs` (85 aserciones) y `verify-permisos.mjs` (33) — todo OK tras sincronizar las copias del harness. Regresión E2E completa: login/recuperación de acceso, enlaces de acceso de un solo uso, sidebar y permisos de administrador, traspaso de administrador principal, selección de artículos, impresión, exportación (catálogo principal y los dos botones de documentación arreglados en la entrega anterior), aviso de nueva versión por rol — todo OK, sin ningún error de JS nuevo. Ninguno de esos tests dependía del texto exacto cambiado, salvo la aserción de `verify.mjs` ya corregida.

Documentos de mantenimiento revisados en esta entrega: `HISTORIAL.md` (esta misma entrada); `README.md` — revisado, se deja el nombre antiguo en el título a propósito (ver arriba); `backend/README.md`, `frontend/README.md`, `backend/.env.example`, `DEPLOY.md` — revisados, no aplica ningún cambio (cambio de texto puro, sin tocar ningún endpoint, variable de entorno, plantilla de EmailJS ni paso de despliegue).

Versión: `backend/package.json` y `frontend/package.json` → **1.19.48**.

**Ficheros NUEVOS o BORRADOS en esta entrega**: ninguno. Todos los cambios de código de esta entrega son ediciones de ficheros que ya existían.

---

## v1.29 — "Documentación faltante" y "Exportar documentación" también se libran de la pantalla en negro (v1.19.47)

Con v1.19.46 ya entregada, Víctor mandó dos capturas de las pantallas "Administración · Documentación faltante" y "Administración · Exportar documentación" y una petición muy concreta: "ESTE APARTADO DOCUMENTACION FALTANTE ES EL QUE TARDA UN POQUITO MAS EN CARGAR, ¿SERA PORQUE NO TIENE PAGINACION COMO EL RESTO? EL BOTON EXPORTAR EXCEL DEJA LA PANTALLA EN NEGRO, REPARAR COMO LOS DE LA INTERFAZ PRINCIPAL DE ARTICULOS ; PASA LO MISMO EN EXPORTAR DOCUMENTACION". Dos asuntos distintos en un mismo mensaje: una duda sobre lentitud, y un bug real ya reconocido — la misma pantalla en negro del catálogo principal, ahora detectada en otros dos sitios.

**El bug de la pantalla en negro.** Revisando `AdminDocumentacionFaltante.jsx` (botón "Exportar Excel") y `AdminExportarZip.jsx` (botón "Descargar zip") se confirmó al momento: los dos seguían usando `window.open(url, "_blank")` para disparar la descarga — el mismo patrón que ya se había cambiado en `App.jsx` para el catálogo principal el mismo día (antes de v1.19.46), pero que nunca se propagó a estos otros dos botones porque no formaban parte de aquel cambio. Con ficheros grandes, esa pestaña nueva se queda en negro/blanco sin ninguna señal de progreso hasta que el navegador termina de descargar — en "Exportar documentación" sin filtrar por proveedor concreto, el propio backend avisa en pantalla de que puede tardar "varios minutos", así que ahí el problema es aún más visible. Arreglado igual que el catálogo principal: los dos botones ahora llaman a `descargarDesdeUrl()` (services/api.js, ya existente y ya probado) — fetch + blob + un `<a download>` temporal, sin salir nunca de la pantalla, con spinner y texto "Generando…" mientras dura y bloqueado para no lanzar una segunda descarga a la vez. El aviso de modo demo de siempre ("no está disponible en modo demo") se mantiene exactamente igual en los dos sitios — solo cambia lo que pasa cuando SÍ hay backend real detrás. Se comprobó también que el `fetch` del navegador no tiene ningún timeout propio por defecto, así que la descarga de "todos los proveedores" (varios minutos) no se ve afectada por el cambio — el backend ya desactiva su propio timeout para ese caso concreto desde que existe ese endpoint (`req.setTimeout(0)`/`res.setTimeout(0)` en `exportZipController.js`).

**La duda de la lentitud.** La pregunta de Víctor daba por hecho que faltaba paginación "como el resto" — pero "Documentación faltante" no es un listado de artículos como el catálogo principal, es un INFORME agregado: recorre TODOS los artículos activos (6693 de 6736 en su captura), cruza imagen/fichas/código de cada uno contra su proveedor asignado, y los agrupa por proveedor con sus totales. Paginar esa respuesta como se pagina el catálogo (una página de artículos sueltos) rompería justamente lo que la pantalla necesita mostrar — los grupos y los totales completos, no un trozo. Se le explicó esta distinción tal cual. Dicho esto, sí había una mejora real y sencilla disponible: `calcularDocumentacionFaltante()` (documentacionController.js) pedía a Supabase, una detrás de otra, tres consultas completamente independientes entre sí (imágenes, fichas y códigos de proveedor de los artículos activos) — cada una ya paginada en tandas de 1000 desde el 2026-09-02, pero las tres en SERIE, sumando sus tres tiempos de red uno tras otro. Como ninguna depende del resultado de otra, ahora se lanzan las tres a la vez con `Promise.all`, así que el tiempo total pasa a ser aproximadamente el de la más lenta de las tres en vez de la suma de las tres — mismo resultado exacto, solo más rápido, sin tocar la forma de la respuesta ni el frontend en absoluto.

**Verificación**: `npx vite build`, limpio; `node --check` en todo `backend/src/`, limpio. Nuevo `e2e-descarga-admin-docs.mjs` (Playwright), 8 aserciones en dos partes — contra el servidor demo: el aviso de modo demo sigue apareciendo igual en los dos botones nuevos, sin quedarse ninguno bloqueado en "Generando…" tras el aviso; contra un arnés temporal (`test-descarga.html`, el mismo patrón ya usado en `e2e-descarga-export.mjs`, borrado antes de empaquetar esta entrega) y una extensión de `mock-export-server.mjs` con los dos endpoints nuevos: el nombre real del fichero se lee correctamente de `Content-Disposition` en los tres casos (Excel de documentación faltante, zip de un proveedor concreto, zip de "todos los proveedores" con más retardo simulado), sin ningún error de JS sin capturar. Regresión completa sobre el resto de la aplicación (permisos, traspaso de administrador principal, selección de artículos, sidebar, impresión, enlaces de acceso, login/recuperación, exportación del catálogo principal, aviso de nueva versión por rol) — todo OK.

Documentos de mantenimiento revisados en esta entrega: `HISTORIAL.md` (esta misma entrada); `backend/README.md` (actualizado — nota sobre la paralelización de las tres consultas de "Documentación faltante"); `frontend/README.md` (actualizado — las dos pantallas ya no usan `window.open` para exportar); `README.md`, `backend/.env.example`, `DEPLOY.md` — revisados, no aplica ningún cambio (no hay ninguna variable de entorno nueva, ningún endpoint nuevo ni ningún paso de despliegue adicional).

Versión: `backend/package.json` y `frontend/package.json` → **1.19.47**.

**Ficheros NUEVOS o BORRADOS en esta entrega** (ver la lección de la incidencia de abajo — señalados aparte a propósito): ninguno. Todos los cambios de código de esta entrega son ediciones de ficheros que ya existían.

---

## Incidencia de producción — `generarExportWorker.js` nunca llegó a desplegarse, y auditoría posterior (sin cambio de versión)

Justo tras recibir v1.19.45, Víctor probó a exportar la selección recién marcada y le saltó, en pantalla, `Cannot find module '/opt/render/project/src/backend/src/workers/generarExportWorker.js'`. Antes de suponer nada sobre el código nuevo se le pidió un dato clave: si una exportación NORMAL, sin ninguna selección marcada, fallaba igual — confirmó que sí. Eso descartaba de raíz que fuera cosa de la función de selección de hoy: el fichero que construye el PDF/Excel de verdad (introducido hace muchas versiones, v1.19.21, para que exportar el catálogo completo no bloqueara el proceso Node mientras se generaba el documento) sencillamente no estaba en su Render.

Comprobando el propio repositorio de GitHub de Víctor se confirmó al 100%: en `backend/src/workers/` solo estaba `parsearExcelWorker.js` — `generarExportWorker.js`, al ser un fichero NUEVO (no la edición de uno ya existente), nunca se subió al aplicar a mano alguna entrega anterior. Víctor lo añadió con "Add files via upload" en GitHub y Render lo desplegó solo (`autoDeploy: true`) — exportar volvió a funcionar.

Dado lo serio de haber estado así sin que nadie lo notara, Víctor pidió una auditoría completa: comparar su repositorio desplegado, archivo por archivo, contra el estado que debería tener en v1.19.45. Se subió su zip real y se comparó con `diff -rq` contra la copia de referencia, se corrió `node --check` sobre todo el backend y `npx vite build` sobre su frontend real, y se hizo un barrido de "código huérfano" (ficheros que ya no importa nadie). Resultado: la app en sí estaba bien — mismas versiones, mismo `CHANGELOG.md`/`HISTORIAL.md`/READMEs, todas las migraciones presentes, backend y frontend compilando limpios — pero aparecieron tres restos más del mismo patrón exacto (algo que había que BORRAR o AÑADIR de cero, no editar, se quedó a medias en alguna entrega anterior, sobre todo alrededor de v1.15, cuando la contraseña temporal se sustituyó por enlaces de acceso de un solo uso):

- `frontend/src/components/CambiarPasswordObligatorio.jsx` — la pantalla de cambio de contraseña obligatorio de antes de los enlaces de un solo uso, huérfana (nadie la importaba ya en ningún sitio, confirmado también porque ni siquiera entraba en el `dist/` del build).
- `backend/src/utils/contrasenaTemporal.js` — el generador de aquella contraseña temporal, mismo caso, con un comentario en `tokenAcceso.js` que ya decía explícitamente "ya sin uso desde...".
- `frontend/package-lock.json` de Víctor sin `@emailjs/browser`, aunque sí estaba en `package.json` — no debería estar rompiendo nada ahora mismo (Render construye con `npm install`, no `npm ci`, así que se instala igual), pero el lockfile committeado no reflejaba de verdad lo instalado.

Víctor borró los dos ficheros huérfanos él mismo desde GitHub. De paso también borró `backend/.env.example` (no era necesario, pero tampoco hace daño — ese fichero no lo lee la aplicación, es solo documentación de referencia) y preguntó qué hacer con el lockfile, que no se puede arreglar a mano editando texto. Se le regeneró aquí mismo (`npm install --package-lock-only` contra su `package.json` real) y se le devolvió listo para subir, junto con el `.env.example` corregido y al día.

**Lección para las próximas entregas**: el patrón de fallo, las dos veces, fue el mismo — un cambio que no es "sustituir el contenido de un fichero que ya existe", sino "borrar este fichero" o "añadir este fichero nuevo", se pierde con más facilidad al aplicar una entrega a mano sobre GitHub. A partir de ahora, cualquier entrega que incluya un fichero NUEVO o pida BORRAR uno existente lo señalará aparte, explícitamente, en su propio apartado de la entrega — no solo dentro de la lista general de cambios.

---

## v1.28 — El aviso de "nueva versión disponible" ya no aburre a todo el mundo con el detalle técnico (v1.19.46)

Tras la incidencia de arriba, Víctor volvió sobre otro asunto ya observado en el día a día: "el exceso de información aturde al usuario, vamos a limitar la pantalla de recarga de actualización, solo mensaje de nueva actualización (para forzar la misma) con un título resumen pero sin entrar en detalles para no aburrir, solo mostrar todo a los administradores". El aviso de nueva versión (`ComprobadorNuevaVersion.jsx`, v1.13 — comprobación periódica de `dist/version.json`, un aviso que fuerza la recarga con un botón o una cuenta atrás de 5 minutos) hasta ahora enseñaba a TODO el mundo, sin distinción de rol, el bloque completo de notas de la versión: los apartados Añadido/Cambiado/Arreglado/Eliminado del propio `CHANGELOG.md`, con su lenguaje técnico de cada entrega. Para alguien del equipo que solo quiere seguir consultando el catálogo, esa cantidad de detalle en cada despliegue no aporta nada y sí puede generar la sensación de "esto cambia constantemente".

El componente vive fuera del árbol de `App.jsx` (es hermano de `<App/>` en `main.jsx`, a propósito, para poder avisar de una versión nueva incluso en la propia pantalla de login, antes de que exista ninguna sesión) — así que no tiene la sesión disponible por props y tuvo que pedirla ella misma. Se hace justo al detectar la versión nueva, con `fetchSesionActual()` (la misma función que ya usa `App.jsx`, `GET /auth/me`), no antes ni en cada ciclo de sondeo: si no hay sesión todavía (login, "Comprobando sesión…") o la llamada falla por cualquier motivo, se queda en el resumen sin detalle — el criterio más prudente por defecto, no un caso de error a vigilar aparte. Solo si la sesión activa en ESE momento es de administrador se pide `dist/CHANGELOG.md` y se pinta el bloque completo, exactamente igual que hasta ahora. La cabecera (título, mensaje corto, botón "Recargar ahora" y la cuenta atrás) se mantiene igual para todo el mundo — es precisamente el "título resumen" que pidió Víctor, y ya era lo bastante corto de por sí.

**Verificación**: `npx vite build`, limpio. Nuevo `e2e-aviso-version-por-rol.mjs` (Playwright) — a diferencia del resto de pruebas end-to-end de este proyecto, tuvo que correr contra el sitio ya COMPILADO (`vite build` + `vite preview`), no contra el servidor de desarrollo de siempre: las notas de la versión solo existen en `dist/CHANGELOG.md` tras un build real (lo copia ahí el plugin `avisoNuevaVersionPlugin`), así que probarlo en modo desarrollo habría dado un falso fallo ajeno a lo que cambió aquí (el filtro por rol, no el mecanismo de copiar el changelog). 8 aserciones: sin sesión (pantalla de login) y con la cuenta 'hotel', el aviso no lleva ningún bloque de notas, solo el resumen; con la cuenta 'admin' sigue apareciendo el bloque completo, con los bloques de versiones reales leídos del changelog de verdad. Regresión completa sobre el resto de la aplicación (permisos, traspaso de administrador principal, selección de artículos, sidebar, impresión, enlaces de acceso, exportación en modo demo) — todo OK, sin ningún error de JS nuevo.

Documentos de mantenimiento revisados en esta entrega: `HISTORIAL.md` (esta misma entrada); `frontend/README.md` (actualizado — nueva viñeta documentando el aviso de nueva versión, que hasta ahora no estaba recogido ahí en absoluto); `backend/README.md`, `README.md`, `backend/.env.example`, `DEPLOY.md` — revisados, no aplica ningún cambio (cambio puramente de frontend, sin tocar ningún endpoint, variable de entorno ni paso de despliegue).

Versión: `backend/package.json` y `frontend/package.json` → **1.19.46** (backend sin cambios en esta versión — se sube igual para mantener sincronizados los dos `package.json`).

---

## v1.27 — Selección manual de artículos, a través de búsquedas distintas (v1.19.45)

Con los permisos granulares (v1.25) y el traspaso de administrador principal (v1.26) ya funcionando y confirmados, Víctor pasó a otro asunto del día a día: "necesito poder filtrar en pantalla por referencias. Ahora mismo el buscador es muy completo y el menú de familias de la izquierda también, pero en muchas ocasiones tengo que marcar varios códigos distintos para verlos todos a la vez sin depender de los filtros actuales." Propuso él mismo el diseño con bastante detalle: en modo administrador, una casilla justo antes del código DALI en cada fila, la selección fija en pantalla pase lo que pase con el filtro, y un botón "Marcar todo/Desmarcar todo" antes del buscador.

Antes de tocar código hacía falta aclarar el propósito real de esa selección: ¿solo verla junta en pantalla, o también poder exportarla/imprimirla aparte? Se le planteó la disyuntiva y, en vez de elegir directamente una de las opciones ofrecidas, hizo la pregunta clave de vuelta: "Si elijo la opción 1, se entiende que los botones imprimir y/o exportar, solo aplica a lo mostrado/filtrado en pantalla, así que el resultado buscado seria el correcto que es justamente el indicado en el punto 2 ¿lo entendí bien?" No — y ahí estaba el verdadero problema de diseño de toda esta entrega: los botones "Exportar Excel"/"Exportar PDF"/"Imprimir" NUNCA leyeron la tabla ya pintada en pantalla; siempre volvieron a pedir los datos al backend con los mismos 4 filtros de siempre (q/naturaleza/familia/subfamilia). Un simple toggle "ver solo lo marcado" habría cambiado lo que se VE, pero no lo que esos botones EXPORTAN — habría hecho falta, sin decirlo, la opción más completa desde el principio. Se le explicó esa desconexión y se siguió adelante con el diseño completo (ver juntos en pantalla Y poder exportar/imprimir justo la selección) sin que hiciera falta insistir más — quedó claro con la explicación.

Quedaban dos decisiones más, resueltas ambas por las recomendadas: "Marcar todo" cubre TODO lo que coincide con la búsqueda activa, aunque ocupe varias páginas — no solo la página que se ve en ese momento (el catálogo real ronda las ~30.000 filas, así que una búsqueda amplia sí puede pasar de una página, aunque la muestra de demo con ~22 artículos casi nunca lo necesite). Y la selección no hace falta que sobreviva a una recarga de página — "basta con que aguante mientras no recargues", igual que el resto del estado de esta pantalla (búsqueda, filtros, página), que tampoco sobrevive a un F5.

El diseño resultante tiene dos mitades. En el frontend (`App.jsx`), un `Map` en memoria (`marcados`, código DALI → el artículo completo tal cual lo devuelve `fetchArticulos`, no solo el código) guarda la selección — guardar el objeto entero, no solo el número, significa que "Ver solo marcados" puede pintar nombre/proveedor/SAP/etc. de cada fila marcada sin volver a pedir nada al backend, aunque esos artículos vengan de una búsqueda que ya no está activa. La casilla nueva (`ArticuloTable.jsx`, primera columna, justo antes del código DALI como pidió) lleva `stopPropagation()` en su propio click — sin eso, marcar la casilla habría abierto también la ficha completa del artículo, dos acciones a la vez donde solo se pidió una. "Marcar todo/Desmarcar todo" decide su ETIQUETA mirando solo la página visible ahora mismo (barato, sin pedir nada extra en cada tecleo), pero la ACCIÓN de verdad siempre recorre todas las páginas del filtro activo — en el peor de los casos (una búsqueda amplia que sí cruza varias páginas) la etiqueta podría no coincidir un instante con lo que en realidad va a hacer el botón, pero la acción sigue siendo la correcta. "Vaciar selección" es un botón aparte, deliberadamente distinto de "Desmarcar todo": este último solo quita lo que coincide con la búsqueda ACTUAL, mientras que "Vaciar selección" borra la selección entera de golpe, sea cual sea su origen — para no tener que ir repitiendo cada búsqueda anterior una a una solo para desmarcarla.

La otra mitad vive en el backend, y es la pieza que de verdad faltaba: `GET /export/excel` y `GET /export/pdf` (`exportController.js`) aceptan ahora un cuarto — y excluyente — parámetro `codigos` (lista de `codigo_dali` separados por comas). Cuando llega, se ignoran por completo `q`/`naturaleza`/`familia`/`subfamilia`/`todos`, y se exportan EXACTAMENTE esos códigos, estén activos o no: si Víctor los marcó a mano en pantalla es porque ya los vio y los quiso ahí, así que no tiene sentido volver a aplicarles el filtro de `activo_dali`/`activo_general` (que normalmente excluye del todo los artículos desactivados salvo que un admin marque "Incluir no activos"). Precisamente por eso hacía falta cerrar un hueco de seguridad antes de dejarlo así: sin ninguna comprobación de por medio, cualquier visitante SIN sesión habría podido usar `?codigos=` como atajo para leer nombre/SAP/proveedor de artículos desactivados que de otra forma solo ve un administrador. `rechazarSiCodigosSinAdmin()` responde `403` de inmediato si llega `codigos` sin una sesión de administrador detrás, antes de tocar la base de datos siquiera — misma cuenta reservada al rol `admin` sin más (no hace falta ningún permiso granular de "Gestión" concreto, igual que el resto de esta pantalla).

**Verificación**: no existía ningún harness que ejercitara `exportController.js` — se creó uno nuevo, `exporttest/`, con un doble de Supabase a medida (soporta `.in()`/`.range()`/embebidos "tabla(campo)" sin `!inner`, que el doble ya existente en `tokenaccesotest/` no necesitaba para nada de lo que prueba). `verify-export-codigos.mjs`: 14 aserciones — la rama `codigos` trae exactamente los códigos pedidos, incluyendo uno explícitamente DESACTIVADO en la fixture (la comprobación central de todo el diseño de seguridad de este cambio); ignora por completo el resto de filtros aunque lleguen deliberadamente contradictorios junto a `codigos`; descarta de la lista cualquier valor no entero, negativo o cero sin reventar; enriquece `codigo_proveedor` exactamente igual que la rama de siempre; y la rama SIN `codigos` sigue funcionando tal cual (regresión, incluida `todos=true`). El 403 sin sesión de administrador se prueba aparte, junto con que un admin de verdad no queda bloqueado. Deliberadamente no se probó a través de `exportarExcel`/`exportarPdf` (los handlers HTTP reales, que delegan la generación del documento a un `worker_thread`): lo que cambió aquí es la lógica de qué se consulta y quién puede pedirlo, no cómo se dibuja el PDF/Excel — forzar el worker solo habría añadido una dependencia más frágil sin probar nada nuevo.

En el frontend, nuevo `e2e-seleccion-catalogo.mjs` (Playwright, modo demo): 24 aserciones. Con la cuenta 'hotel' no aparece ni la columna de checkbox, ni el botón "Marcar todo", ni la barra de selección — con la cuenta admin, sí. Marcar un artículo con la búsqueda "queso" y después otro con la búsqueda "silla" (dos búsquedas sin ningún artículo en común) deja los DOS marcados a la vez — la comprobación central de "verlos juntos sin depender del filtro actual" que pidió Víctor. Con la búsqueda "cong" (3 artículos activos en la muestra de demo), "Marcar todo" los suma a los 2 ya marcados antes (5 en total) y "Desmarcar todo" solo quita esos 3, dejando intactos los otros 2 — confirma que una acción no pisa a la otra. "Ver solo marcados" pinta exactamente esos 5 artículos, sin controles de paginación. Exportar con la selección activa en modo demo sigue mostrando el mismo aviso de "no disponible en modo demo" de siempre, sin quedarse colgado en "Generando…" — el modo demo no puede ejercitar la descarga real con `?codigos=` (`urlExportarExcel`/`urlExportarPdf` devuelven `null` sin backend real, misma limitación ya conocida de `e2e-export-demo-alert.mjs`), así que esa parte queda cubierta por las 14 aserciones de `exporttest/` contra el controller real. Por último, "Vaciar selección" borra la selección entera y apaga "Ver solo marcados" ella sola. Regresión completa sobre todo lo anterior: `tokenaccesotest/verify.mjs` (85), `tokenaccesotest/verify-permisos.mjs` (33), `e2e-permisos-admin.mjs` (15), `e2e-sidebar-admin.mjs` (13), `e2e-token-acceso.mjs` (22), `e2e-imprimir.mjs` (9), `e2e-traspasar-principal.mjs` (10) y `e2e-export-demo-alert.mjs` (3) — todo OK. `npx vite build`, limpio.

Documentos de mantenimiento revisados en esta entrega: `HISTORIAL.md` (esta misma entrada); `backend/README.md` (actualizado — fila de endpoints y nueva sección "Exportación" documentando `codigos`); `frontend/README.md` (actualizado — nueva viñeta sobre la selección manual en "Qué incluye"); `README.md`, `backend/.env.example`, `DEPLOY.md` — revisados, no aplica ningún cambio: no hace falta ninguna variable de entorno nueva, ninguna migración de base de datos ni ningún paso de despliegue adicional — la funcionalidad reutiliza por completo las tablas y el cliente de Supabase ya existentes.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.45**.

---

## v1.26 — Traspaso del puesto de administrador principal (v1.19.44)

Nada más comprobar que los permisos granulares de v1.25 funcionaban de verdad, Víctor preguntó lo lógico: "ahora que lo tenemos funcionando y comprobado que funciona correctamente, es muy complicado que el administrador principal pueda dar este rol a otro administrador?". Con razón — v1.25 dejó el puesto de administrador principal fijo y solo editable a mano en Supabase (decisión suya, "solo yo" en vez de "puede haber varios"), y eso significaba que si algún día quería pasarle el testigo a otra persona (por ejemplo, si dejara de llevar él la gestión del día a día), tendría que pedir que alguien entrara directamente en la base de datos.

Antes de tocar nada se le presentó la disyuntiva que ya se había dejado a medias en v1.25: ¿varios administradores principales a la vez, o seguir teniendo uno solo pero poder traspasárselo? Eligió otra vez la opción más simple — traspaso, uno cada vez — por el mismo motivo que ya llevó a "solo yo" la primera vez: mantener siempre clara la respuesta a "¿quién manda de verdad aquí?", sin la complejidad añadida de varias personas con la misma potestad al mismo tiempo pudiendo, en teoría, contradecirse entre ellas.

El diseño resultante es una acción dedicada, no un campo más de la edición normal de un usuario: `POST /admin/usuarios/:id/traspasar-principal` (`traspasarAdminPrincipal` en `usuariosController.js`) concede el puesto al destino Y se lo retira a quien llama, las dos cosas en la misma llamada — nunca queda a medias por accidente porque alguien mande solo la mitad del cambio. El orden de las dos escrituras es deliberado: primero se CONCEDE al nuevo, y solo si eso sale bien se RETIRA al actual. Si algo fallara justo entre medias (un fallo de red, Supabase caído a mitad de la operación), el peor caso posible es acabar con DOS administradores principales — raro, pero se arregla con una actualización directa en Supabase — en vez de CERO, que habría dejado a todo el mundo sin nadie que pudiera volver a gestionar permisos de administrador desde la app hasta entrar a mano a arreglarlo (el mismo agujero que ya se advertía en la migración de v1.25 si nunca se marca a nadie como principal). Solo puede llamar a este endpoint quien YA es administrador principal — ni siquiera un admin con el permiso "Usuarios" concedido puede usarlo para saltarse esa barrera, exactamente el mismo criterio que ya se aplicó en v1.25 a dar de alta un admin, cambiarle el rol a alguien, o eliminar la cuenta de otro administrador.

En la pantalla de Usuarios, el administrador principal ve ahora un botón "Nombrar administrador principal" al editar cualquier OTRO admin activo que todavía no lo sea (`UsuarioForm.jsx`) — con su propio diálogo de confirmación, aparte del guardado normal del formulario, porque es una acción demasiado seria como para que se cuele sin querer al guardar otro cambio cualquiera. El mensaje del diálogo deja explícito lo que va a pasar: la otra cuenta pasa a tener acceso a todo, y quien confirma deja de tenerlo. Justo después de un traspaso con éxito, la propia sesión se cierra sola — como toda la sesión viaja en una cookie firmada (no hay ningún servidor de sesiones al que avisar de nada), el cambio de `es_admin_principal` no se notaría por sí solo hasta el siguiente inicio de sesión, y dejar a quien acaba de traspasar el puesto viendo todavía los controles de "administrador principal" (que ya no le corresponden de verdad, aunque la cookie todavía diga que sí) habría sido confuso — mejor forzar la salida y que vuelva a entrar ya como un administrador normal más.

**Verificación**: 10 aserciones nuevas en `tokenaccesotest/verify-permisos.mjs` (23 → 33 en total) — un admin normal no puede traspasar el puesto (403, y el principal sigue siendo el mismo tras el intento), no se puede traspasar a uno mismo, ni a una cuenta 'hotel', ni a un administrador desactivado, y el caso de éxito comprueba tanto que el destino queda marcado como principal y quien lo traspasa deja de estarlo, como una regresión dedicada a la invariante central de todo este diseño: sigue habiendo exactamente un administrador principal, nunca cero ni dos. Nuevo `e2e-traspasar-principal.mjs` (Playwright, modo demo) — 10 aserciones: el botón aparece únicamente donde tiene sentido (otro admin activo, no uno mismo, no ya principal), el diálogo de confirmación menciona el nombre de quien lo va a recibir y avisa del cierre de sesión, al confirmar la sesión se cierra sola y vuelve a la pantalla de login, y al volver a entrar la cuenta destino aparece con la insignia Principal en la tabla y, al reabrirla, ya no muestra ni la checklist de permisos ni el propio botón de traspaso — en su lugar, el aviso de que tiene acceso a todo siempre. El script tuvo que dejar de recargar la página al volver a iniciar sesión tras el cierre automático: una recarga de verdad habría perdido la lista de usuarios de demo (en memoria del propio módulo JS) y con ella la cuenta de prueba recién creada, dando un fallo falso ajeno a lo que se estaba probando. Regresión completa sobre todo lo anterior: `tokenaccesotest/verify.mjs` (85 aserciones), `e2e-permisos-admin.mjs` (15), `e2e-sidebar-admin.mjs` (13), `e2e-token-acceso.mjs` (22) y `e2e-imprimir.mjs` (9) — todo OK. `npm run build` (Vite), limpio.

Documentos de mantenimiento revisados en esta entrega: `HISTORIAL.md` (esta misma entrada); `backend/README.md` (actualizado — fila nueva en la tabla de endpoints y párrafo "Traspaso del puesto" en la sección "Autenticación"); `frontend/README.md` (actualizado — nota sobre el nuevo botón en la pantalla de Usuarios); `README.md`, `backend/.env.example`, `DEPLOY.md` — revisados, no aplica ningún cambio. No hace falta ninguna migración nueva de base de datos: las dos columnas (`es_admin_principal`, `permisos`) ya se crearon en v1.25.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.44**.

---

## v1.25 — Permisos granulares de administrador (v1.19.43)

Víctor: "ES MUY COMPLICADO INTRODUCIR UN NUEVO ROL? LA IDEA ES QUE YO COMO ADMINISTRADOR PRINCIPAL TENGA LA POTESTAD DE INCLUIR E INCLUIR ACCESO A LOS DIFERENTES PUNTOS DE LOS DIFERENTES MENOS, INCLUIDOS LOS DEMAS ADMINISTRADORES" — con la reorganización de "Gestión" en subgrupos recién entregada (v1.24) todavía fresca, Víctor pidió ir más lejos: hasta ahora `rol = 'admin'` era todo o nada, cualquier administrador veía y podía tocar los 8 apartados de "Gestión" por igual. Él quería poder decidir, cuenta por cuenta, a qué apartados concretos llega cada administrador — incluidos otros administradores, no solo cuentas `hotel`.

Antes de tocar nada se le hicieron dos preguntas, porque las respuestas cambiaban bastante el diseño. La primera: "¿Puede haber más de un administrador principal?" — eligió "Solo yo (recomendado)": un único administrador principal, fijo, sin ninguna pantalla ni endpoint para cambiarlo (se marca a mano en Supabase). Esto simplifica mucho el modelo — no hace falta resolver qué pasa si dos principales se contradicen, ni dar de alta un segundo principal desde la app — a cambio de que, si algún día hiciera falta un segundo, habría que tocar la base de datos directamente en vez de hacerlo desde la pantalla de Usuarios. La segunda: "¿Qué acceso deberían tener los administradores que YA existen hoy?" — eligió "Todo, como ahora (recomendado)": nadie pierde acceso el día del cambio, y Víctor va restringiendo a quien haga falta, uno a uno, cuando le convenga. Esto se traduce directamente en el `DEFAULT` de la nueva columna `permisos`: el array completo de las 8 claves, así que la propia migración (`ALTER TABLE ... ADD COLUMN`) rellena automáticamente a todos los administradores existentes sin necesidad de un `UPDATE` aparte.

El modelo final tiene dos columnas nuevas en `usuarios` (migración `database/migraciones/2026-09-03_permisos_admin.sql`): `es_admin_principal boolean` (una sola cuenta en `true`, nunca editable desde la app) y `permisos text[]` (subconjunto de las 8 claves de "Gestión" — las mismas cadenas que ya usan `vista` en el frontend y las rutas del sidebar: `admin-articulos`, `admin-importar`, `admin-usuarios`, `admin-documentacion`, `admin-proveedores`, `admin-exportar-zip`, `admin-solicitudes-acceso`, `admin-configuracion-emailjs`). El administrador principal pasa siempre, tenga lo que tenga en `permisos` (de hecho ni se le mira esa columna). Un administrador normal necesita la clave concreta.

La parte más delicada fue decidir qué puede hacer un administrador normal con permiso "Usuarios" sobre OTRAS cuentas de administrador — Víctor no lo pidió con estas palabras exactas, pero hacía falta una frontera clara para que "conceder el apartado Usuarios" no equivaliera por la puerta de atrás a "conceder también la potestad de ascender a alguien a admin o quitarle el suyo a otro". Se decidió: un admin normal con "Usuarios" puede seguir gestionando cuentas `hotel` sin ninguna restricción nueva (dar de alta, editar, desactivar, eliminar — igual que siempre), y puede hacer **mantenimiento básico** de otras cuentas admin (corregir nombre, email, contraseña), pero NO puede: cambiar el rol de nadie, cambiar los permisos de otro admin, activar/desactivar la cuenta de otro admin, ni eliminarla. Esas cuatro acciones quedan reservadas al administrador principal. El backend aplica esto en `usuariosController.js`: `crearUsuario` rechaza con 403 dar de alta un `rol: 'admin'` si quien lo pide no es principal; `actualizarUsuario` mira si el cuerpo de la petición trae `rol`, `permisos`, o `activo` apuntando a una cuenta que YA es admin, y si es así exige ser principal (consultando el rol actual del objetivo en la base de datos, no el que venga en la petición); `eliminarUsuario` rechaza borrar una cuenta `rol='admin'` si quien lo pide no es principal.

El middleware `requierePermiso(clave)` (`backend/src/middleware/auth.js`) es la puerta de cada ruta de `/admin/*` — se añadió como capa extra sobre `requireAuth`/`requireAdmin`, que siguen ahí sin cambios. Las ~30 rutas de `admin.js` se agruparon por clave; la única que dio para pensar fue `POST /admin/articulos/carga-masiva-codigo-proveedor` — el nombre de la URL sugiere "Importar Excel", pero investigando dónde se abre el modal que la llama (`CargaMasivaCodigoProveedorModal.jsx`) resultó estar dentro de `AdminArticulos.jsx`, no en la pantalla de Importar Excel — así que se agrupó bajo `admin-articulos`, con un comentario en el código para que nadie vuelva a caer en la misma trampa del nombre.

En el frontend, `App.jsx` gana un `tienePermiso(clave)` (mismo cálculo que ya hacía `esAdmin`, ahora también mirando `esAdminPrincipal`/`permisos`) que decide si se muestra cada vista de "Gestión" — puramente defensivo, la aplicación real de la regla siempre pasa por el backend. `Sidebar.jsx` oculta cada uno de los 8 botones y, si un subgrupo entero se queda sin ningún botón visible, también su subtítulo; el propio divisor "Gestión" se le añade "(acceso limitado)" cuando quien mira no es el principal. `UsuarioForm.jsx` estrena una checklist "Acceso a Gestión" (agrupada en los mismos 4 subgrupos del sidebar, para que se lea con el mismo criterio que ya conoce Víctor) que solo ve el administrador principal, y solo al editar una cuenta con `rol: admin` que no sea el propio principal (a él no hace falta restringirle nada, tiene acceso a todo siempre). Los toggles de "Rol" y "Estado" se deshabilitan (con una pista de por qué) cuando quien los mira no es principal y la cuenta objetivo no es la suya propia.

Durante la implementación salió un fallo que habría roto silenciosamente casi todas las ediciones de un admin normal: el `handleSubmit` de `UsuarioForm.jsx` para edición mandaba SIEMPRE `rol` y `activo` en el payload, sin mirar si de verdad habían cambiado. Con las nuevas guardas del backend (que rechazan con 403 cualquier petición que traiga `rol`/`permisos`, o `activo` sobre otro admin, si quien la manda no es principal), eso habría bloqueado hasta el cambio más inocente — corregir solo el nombre — hecho por un admin normal sobre la cuenta de otra persona, porque `rol` siempre iba en el cuerpo aunque no hubiera cambiado. Se corrigió comparando `form.rol`/`form.activo` contra los valores originales del usuario y solo incluyéndolos en el payload si de verdad cambiaron — como los propios toggles ya están deshabilitados cuando no se pueden tocar, `form.rol`/`form.activo` no pueden divergir del original en ese caso, así que el diff refleja fielmente "¿se ha tocado esto de verdad?" sin necesitar ninguna comprobación de permisos aparte.

También salió, ya en las pruebas E2E en modo demo, un efecto colateral del mismo tipo de guarda pero en sentido contrario: dar de alta un administrador NUEVO dejaba el toggle de "Rol" deshabilitado, con la pista "No puedes cambiarte el rol a ti mismo" — que no tiene ningún sentido en un alta. La causa: `esUnoMismo` se calcula como `editando?.id === sesion?.id`, y en modo demo la sesión no lleva ningún `id` (no hay una cuenta real de Supabase detrás, ver el comentario correspondiente en `services/api.js`); un alta nueva tampoco tiene `id` todavía (`editando = {}`), así que ambos lados de la comparación eran `undefined` y coincidían por pura casualidad. Nunca se había notado porque, antes de esta entrega, nada deshabilitaba el toggle de Rol para un alta nueva. Se corrigió en `AdminUsuarios.jsx` exigiendo además que el usuario que se está editando tenga ya un `id` — una cuenta sin id todavía nunca puede ser "uno mismo", ni en demo ni en producción (donde `sesion.id` es siempre un UUID real y este caso ya no se daba).

**Verificación**: nuevo `tokenaccesotest/verify-permisos.mjs` — 23 aserciones a nivel de controller contra el doble de Supabase (ampliado con `.neq()` y `select(..., {count:'exact', head:true})`, que le hacían falta a `eliminarUsuario`): cubre `requierePermiso()` y las cuatro guardas de privilegio en `crearUsuario`/`actualizarUsuario`/`eliminarUsuario`, en ambos sentidos — lo que un admin normal NO puede hacer (ascender a alguien a admin, autoampliarse permisos, tocar rol/permisos/activo/borrado de otro admin) y lo que SÍ puede seguir haciendo (gestión completa de cuentas hotel, mantenimiento básico de otro admin). Se detectó de paso que `tokenaccesotest/controllers/authController.js` había quedado desactualizado respecto al real tras los cambios de sesión en `login`/`ssoLogin`/`canjearTokenAcceso` — se volvió a copiar y se re-verificó `tokenaccesotest/verify.mjs` completo (85 aserciones) para confirmar que nada se rompió. Nuevo `e2e-permisos-admin.mjs` (Playwright, modo demo) — 15 aserciones: la checklist de permisos aparece agrupada en los 4 subtítulos con las 8 casillas marcadas por defecto en una alta nueva, lo que se marca/desmarca se guarda y se lee bien al reabrir en edición, la checklist desaparece si el rol pasa a "Hotel", ninguna cuenta normal lleva la insignia "Principal", y el pie del sidebar dice "Administrador principal" para la cuenta de demo (que en modo demo se trata siempre como tal — no hay forma de simular en el navegador un administrador limitado de verdad, ver el comentario en `services/api.js`). Regresión completa sobre lo ya existente: `e2e-sidebar-admin.mjs` (13 aserciones), `e2e-token-acceso.mjs` (22) y `e2e-imprimir.mjs` (9) — todo OK. `npm run build` (Vite), limpio.

Documentos de mantenimiento revisados en esta entrega: `HISTORIAL.md` (esta misma entrada); `backend/README.md` (actualizado — tabla de endpoints con nota sobre el nuevo filtro por permiso, sección "Autenticación" con el modelo completo); `frontend/README.md` (actualizado — nota sobre visibilidad por permisos en el sidebar y la nueva checklist de la pantalla de Usuarios); `README.md`, `backend/.env.example`, `DEPLOY.md` — revisados, no aplica ningún cambio.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.43**.

**Pendiente antes de desplegar**: aplicar a mano en Supabase la migración `database/migraciones/2026-09-03_permisos_admin.sql`, y después el `UPDATE` (comentado dentro del propio fichero, con un email de ejemplo) que marca la cuenta de Víctor como administrador principal — con su email real. Sin ese paso, nadie tiene `es_admin_principal = true` y nadie podría gestionar permisos de administrador desde la app hasta corregirlo a mano.

---

## v1.24 — El apartado "Gestión" del sidebar se reorganiza en subgrupos (v1.19.42)

Víctor: "el apartado admin, se puede reorganizar mejor? hemos ido introduciendo apartados y creo esta todo muy liado". Con razón — "Gestión" había empezado con un par de destinos (Artículos, Importar Excel) y con el tiempo, entrega tras entrega, había ido creciendo hasta 8 (Usuarios, Documentación faltante, Fusionar proveedores, Exportar documentación, Solicitudes de acceso, Configuración EmailJS), todos en una sola lista plana sin ningún criterio de agrupación — cada uno se añadió donde tocaba en su momento, no donde tenía más sentido junto a los demás.

Antes de tocar nada se le presentaron a Víctor 3 formas de reorganizarlo: (A) agrupar en subtítulos dentro de "Gestión", todo visible; (B) los mismos subgrupos pero plegables, tipo acordeón; (C) solo reordenar los 8 sin subtítulos nuevos. Eligió la (A) — el cambio más simple que resuelve el problema real (que se lean agrupados), sin la complejidad extra de un acordeón que un menú de 8 botones no necesita.

Los 4 grupos, pensados por función (no por cuándo se añadió cada uno): **Catálogo** (Artículos, Importar Excel — el día a día de consulta/carga de datos), **Proveedores y documentación** (Documentación faltante, Fusionar proveedores, Exportar documentación — todo lo relacionado con la ficha de cada proveedor), **Accesos** (Usuarios, Solicitudes de acceso — quién puede entrar) y **Sistema** (Configuración EmailJS — ajustes técnicos de la propia app). En `Sidebar.jsx` esto es literal: un `<div className="sidebar-subdivider">` por grupo intercalado entre los botones — ningún `vista`/`onNavigate` cambia, así que no hay ningún riesgo de romper la navegación, solo el orden en el que aparecen y los subtítulos que los separan. El nuevo `.sidebar-subdivider` en `index.css` es un escalón visual por debajo de `.sidebar-divider` (el de "Principal"/"Gestión"): más pequeño, sin tanto peso, para que quede claro que es un subgrupo y no una sección nueva al mismo nivel.

Al probar la reorganización salió un fallo de fondo que llevaba ahí desde siempre, solo que invisible: un `<button>` es `inline-block` por defecto en el navegador, así que sin `width: 100%` cada pestaña del sidebar (tanto las de "Gestión" como las del árbol de naturalezas) solo ocupa el ancho de su propio texto, no el ancho completo de la fila. Nunca se había notado porque, o bien el botón vivía solo dentro de su propio div (las naturalezas, cada una en su `<div key={n.id}>`), o bien el texto era tan largo ("Documentación faltante", "Configuración EmailJS") que ya ocupaba la fila entera él solo en el orden antiguo. En cuanto "Artículos" e "Importar Excel" — dos textos cortos — pasaron a ser hermanos directos dentro del mismo grupo, se empaquetaron uno junto al otro en la misma línea en vez de cada uno en la suya, y lo mismo con "Documentación faltante" + "Fusionar proveedores". Se corrigió de raíz añadiendo `display: block; width: 100%;` a la clase `.tab` compartida — no un parche solo para "Gestión", sino la corrección real para toda la barra lateral, que además evita que el mismo fallo vuelva a aparecer si en el futuro se reordena o se añade cualquier otra pestaña de texto corto en cualquier parte del sidebar.

**Verificación**: `npm run build` (Vite), limpio. Nuevo `e2e-sidebar-admin.mjs` (Playwright, modo demo): 13 aserciones — los 4 subtítulos son visibles, los 8 botones siguen llevando cada uno a su destino correcto (comprobado por el título de cada pantalla tras el clic), y una regresión dedicada al fallo de empaquetado (cada uno de los 8 botones mide exactamente el 100% del ancho de su contenedor). Regresión completa sobre lo ya existente para confirmar que el cambio de `.tab` no rompe nada más: `tokenaccesotest/verify.mjs` (85 aserciones), `e2e-token-acceso.mjs` (22 aserciones) y `e2e-imprimir.mjs` (9 aserciones) — todo OK. Captura de pantalla real del sidebar completo, con "Gestión" ya reorganizado y cada botón en su propia línea.

Documentos de mantenimiento revisados en esta entrega: `HISTORIAL.md` (esta misma entrada); `frontend/README.md` (actualizado — nota breve sobre el nuevo agrupado de "Gestión", justo antes de la lista de bullets de cada pantalla de administración); `README.md`, `backend/README.md`, `backend/.env.example`, `DEPLOY.md` — revisados, no aplica ningún cambio.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.42**.

---

## v1.23 — "Exportar Excel/PDF" se queda en la aplicación con un spinner, en vez de abrir una pestaña en negro (v1.19.41)

Víctor: "CUANDO INTENTO EXPORTAR EN EXCEL O PDF, SI ES MUY GRANDE EL ARCHIVO, SE QUEDA UN RATO EN PANTALLA NEGRA HASTA QUE LO CONSIGUE DESCARGAR. SE PUEDE HACER QUE SE MANTENGA EN LA APLICACION Y UN CIRCULO DANDO VUELTAS O ALGO POR EL ESTILO QUE SE VEA QUE SE ESTA DESCARGANDO EL ARCHIVO?"

Los botones "Exportar Excel"/"Exportar PDF" (`App.jsx`) construían la URL del backend (`urlExportarExcel()`/`urlExportarPdf()` en `services/api.js`) y hacían `window.open(url, "_blank")` — una navegación directa del navegador a esa URL en una pestaña nueva. Con ficheros pequeños apenas se notaba (la pestaña se abre y cierra casi al momento), pero con un listado grande el backend tarda varios segundos en generar el PDF/Excel entero (se construye completo en un hilo aparte antes de mandar nada, ver `generarDocumentoEnWorker` en `exportController.js`) y esa pestaña se quedaba en blanco/negro todo ese rato, sin ninguna pista de que algo estuviera pasando — de ahí la sensación de "esto no funciona" que Víctor describía.

La solución: en vez de navegar a la URL, pedirla por `fetch()` desde la propia aplicación (igual que ya hace cualquier otra llamada autenticada, con `credentials: "include"`) y tratar la respuesta como `Blob`; con el blob ya descargado, se crea una URL de objeto (`URL.createObjectURL`) y se dispara la descarga real del navegador con un `<a download>` temporal — sin volver a salir nunca de la pantalla actual. Se añadió `descargarDesdeUrl()` en `services/api.js` (hace el fetch + lee el blob + extrae el nombre del fichero de la cabecera `Content-Disposition`) y `descargarExport()` en `App.jsx` (la llama, gestiona el estado de "en marcha" y dispara la descarga con el `<a>` temporal). Mientras dura, el botón pulsado se deshabilita y muestra un pequeño círculo girando + "Generando…" — exactamente el mismo patrón visual que ya tenía "Imprimir" con su "Preparando…" (que de paso también pasa a usar el mismo spinner nuevo, por coherencia).

Un detalle que se llevó su rato de investigación: leer la cabecera `Content-Disposition` desde `fetch()` en una petición entre orígenes distintos (el frontend y el backend viven en dominios distintos en producción) NO funciona por defecto, aunque el servidor la mande — el navegador solo deja leer por JS un puñado de cabeceras "simples" a menos que el servidor declare explícitamente cuáles más exponer, vía CORS. Sin arreglar esto, el nombre de fichero real (`articulos-<naturaleza>.xlsx`/`.pdf`, calculado en `exportController.js`) nunca habría llegado al cliente — el resultado visible habría sido el mismo, porque el frontend calcula el mismo nombre por su cuenta como respaldo si la cabecera no se puede leer, pero por casualidad, no por diseño. Se corrigió en `backend/src/server.js`, añadiendo `exposedHeaders: ["Content-Disposition"]` a la configuración de `cors()`.

De paso, se aprovechó para dar a `.btn-ghost` (el estilo de estos tres botones) un estado `:disabled` visible — antes solo `.btn-primary` tenía uno; `.btn-ghost` se quedaba sin ninguna señal de estar desactivado más allá del propio spinner/texto.

**Verificación**: `npm run build` (Vite), limpio. Para probar de verdad el mecanismo nuevo (no solo revisarlo a ojo), se montó un servidor de pruebas propio (`mock-export-server.mjs`, fuera del repo) que imita `/export/pdf`/`/export/excel` con una cabecera `Content-Disposition` real y la misma configuración de CORS con `exposedHeaders` que ahora lleva el backend real, más una pequeña página de arnés (`test-descarga.html`, temporal, borrada antes de empaquetar esta entrega) que importa y ejercita la función real `descargarDesdeUrl()` de `services/api.js`. Nuevo `e2e-descarga-export.mjs` (Playwright): 5 aserciones — el nombre de fichero real se lee correctamente de la cabecera para PDF y Excel (confirmando que el arreglo de CORS funciona de verdad, no solo en teoría), el blob descargado tiene contenido, y un error 500 simulado del backend se propaga al usuario con su mensaje real en vez de uno genérico. `page.waitForEvent("download")` de Playwright confirma además que el navegador dispara una descarga real y con el nombre correcto. Nuevo `e2e-export-demo-alert.mjs`: 3 aserciones de regresión sobre el modo demo (sin backend real) — los botones siguen mostrando el mismo aviso de siempre y no se quedan bloqueados en "Generando…" tras él. Regresión completa sobre lo ya existente: `tokenaccesotest/verify.mjs` (85 aserciones), `e2e-token-acceso.mjs` (22 aserciones) y `e2e-imprimir.mjs` (9 aserciones) — todo OK. Captura de pantalla real del spinner en marcha sobre "Imprimir" (mismo componente visual que estrenarán "Exportar Excel/PDF").

Documentos de mantenimiento revisados en esta entrega: `HISTORIAL.md` (esta misma entrada); `README.md`, `backend/README.md`, `frontend/README.md`, `backend/.env.example`, `DEPLOY.md` — revisados, no aplica ningún cambio (la cabecera expuesta es fija en el código, no una variable de entorno nueva que documentar).

Versión: `backend/package.json` y `frontend/package.json` → **1.19.41**.

---

## v1.22 — El listado impreso adopta el mismo aspecto que el PDF exportado (v1.19.40)

Víctor pidió que el botón "Imprimir" del catálogo (v1.12) saliera "más organizado, las cabeceras con color como los PDF que exportamos". Hasta ahora `.print-view` era una tabla lisa en blanco y negro (bordes grises, sin agrupar) — funcional pero sin ningún parecido visual con el PDF real, que sí tiene cabecera con color, separadores por familia/subfamilia y sombreado alterno.

Se revisó `backend/src/workers/generarExportWorker.js` para sacar los colores y el criterio EXACTOS que usa el PDF: cabecera `#e5decb` de fondo con texto `#3a2f1f` en negrita mayúscula (`dibujarCabeceraTabla()`), separador de grupo `#f4efe3`/`#8a6a2f` también en negrita (agrupado por `familia · subfamilia`, con "Sin familia"/"Sin subfamilia" para lo que no tiene), sombreado alterno `#faf7f0` cada dos filas sobre el array ya ordenado, y un subtítulo "Generado el `<fecha>` · N artículo(s)" bajo el título. También se encontró, en un comentario del propio `exportController.js`, que el agrupado del PDF no confía en el `.order()` de Supabase sobre tablas relacionadas (no se aplicaba de verdad — un bug ya diagnosticado y corregido en su momento, ver versión correspondiente) y en su lugar reordena el array a mano en JS antes de dibujar; se replicó el mismo criterio de reordenado (familia → subfamilia → nombre, con el mismo centinela para "sin familia/subfamilia" al final) en el frontend, en `imprimirListado()` de `App.jsx`, justo antes de guardar `articulosParaImprimir` — sin este paso, agrupar por familia sobre una lista NO ordenada por familia habría producido decenas de grupos diminutos y repetidos en vez de bloques limpios.

En la vista de impresión (`App.jsx`), las filas se construyen ahora como un array plano que intercala una fila de grupo (con `colSpan` a todo el ancho) cada vez que cambia `familia · subfamilia`, seguida de sus artículos — mismo patrón lineal que el bucle principal del PDF, evitando anidar un segundo `.map()`. El CSS de `@media print` (`styles/index.css`) añade `print-color-adjust`/`-webkit-print-color-adjust: exact` en `.print-view` — sin esa propiedad, la mayoría de navegadores omiten los fondos de color al imprimir por defecto (para ahorrar tinta), así que sin ella los colores nuevos no habrían llegado a verse en el papel aunque estuvieran bien puestos en la hoja de estilos.

**Verificación**: `npm run build` (Vite), limpio. Nuevo arnés `e2e-imprimir.mjs` (Playwright, modo demo) — en vez de intentar disparar `window.print()` de verdad (abre el diálogo nativo del sistema operativo, no automatizable), se pulsa "Imprimir" en pantalla normal y LUEGO se activa `page.emulateMedia({media:"print"})` sobre la página ya cargada, lo que aplica de verdad las reglas de `@media print` del navegador — no es una aproximación, es exactamente lo que se imprimiría. 9 aserciones: colores computados de cabecera y fila de grupo idénticos, letra a letra, a los del PDF (`rgb(229, 222, 203)`/`rgb(58, 47, 31)` y `rgb(244, 239, 227)` respectivamente — no solo lo que dice la hoja de estilos, el valor real que el navegador aplicaría), grupos en orden alfabético, subtítulo con fecha y total, y una regresión dedicada (ningún artículo aparece antes de la primera fila de grupo que le corresponde). Sin errores de consola. Comprobación visual adicional con una captura de pantalla real del resultado.

Documentos de mantenimiento revisados en esta entrega: `HISTORIAL.md` (esta misma entrada); `README.md`, `backend/README.md`, `frontend/README.md`, `backend/.env.example`, `DEPLOY.md` — revisados, no aplica ningún cambio.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.40**.

---

## v1.21 — Diagnóstico y solución del despertar lento de Render tras dormir toda la noche (v1.19.39, solo documentación)

Víctor reportó un patrón raro en `cron-job.org`: durante el día, el ping cada 8 minutos (`*/8 6-22 * * *`, horario acotado de 6:00 a 22:00 para ahorrar horas del plan Free de Render) funcionaba sin problema, pero cada mañana, tras dormir toda la noche (sin ningún ping entre las 22:00 y las 6:00), el backend tardaba en volver a responder — varios `503 Service Unavailable` seguidos hasta que finalmente arrancaba, coincidiendo siempre con que él hiciera una prueba manual.

Se le pidió una captura del historial de ejecuciones de cron-job.org, que mostró el patrón exacto: cinco pings seguidos con `503` entre las 6:16 y las 6:48 (hora de Canarias, la zona del propio cronjob), y a partir de las 6:56 todo en verde otra vez — un hueco de unos 30-40 minutos. Se buscó primero si Render documentaba un tiempo de recuperación mayor al esperado (búsqueda web a la documentación oficial: Render promete "~1 minuto" para el caso típico de 15 minutos de inactividad, y confirma el límite de 750 horas gratuitas por workspace al mes) — no cuadraba con los 30-40 minutos observados, así que se le pidió revisar los propios logs de Render (pestaña Logs del servicio) para esa franja horaria.

El log que trajo fue revelador: `Running 'npm start'` a las 05:49:50 UTC (06:49:50 hora de Canarias) y `API DALI escuchando` a las 05:49:59 UTC — **9 segundos** de arranque real. Es decir, el problema NO está en la app (arranca rapidísimo una vez que Render decide arrancarla) sino en que Render tardó desde las 6:16 (o antes) hasta las 6:49 en siquiera empezar a levantar el contenedor tras dormir 8 horas seguidas — mucho más que el "~1 minuto" que documentan para el caso de 15 minutos de sueño mínimo. Conclusión: no es un fallo de nuestro código, es el propio plan Free de Render reaccionando mucho más lento de lo habitual ante sueños muy largos.

Se plantearon dos caminos con Víctor: (1) nunca dejarlo dormir, con ping por debajo de 15 minutos las 24 horas — elimina el problema del todo, pero en horas de Render equivale a tenerlo encendido 24/7 (~740-744 h/mes, cerca del límite de 750 h/mes); o (2) seguir dejándolo dormir de noche pero adelantar el inicio de la ventana diurna, para que el despertar lento pase de madrugada sin que nadie lo note. Confirmó que `listado-DALI-SAP` es el único servicio Free en su cuenta de Render (sin nada más compitiendo por las mismas 750 horas), así que se recomendó la opción 1: cambiar el crontab a `*/12 * * * *`, sin restricción de horas — por debajo del umbral de 15 min, nunca debería volver a dormirse.

**Cambio**: solo documentación, sin tocar código de la aplicación — el cronjob en sí vive en `cron-job.org`, fuera de este repo, y Víctor lo cambió directamente ahí. Se actualiza `DEPLOY.md` (sección "Keep-alive del backend") para que el patrón documentado (antes: cada 5 minutos, todos los días, `*/5 * * * *` — ya desactualizado desde que Víctor lo acotó a horario diurno en algún momento posterior) refleje el que de verdad funciona en producción, con el porqué completo del diagnóstico y una alternativa anotada (horario recortado pero adelantado) por si en el futuro se añade otro servicio Free a la cuenta y el margen de horas deja de ser seguro.

**Verificación**: pendiente de confirmar por Víctor tras una noche completa con el cronjob nuevo aplicado — no hay nada de código que probar en esta entrega.

Documentos de mantenimiento revisados en esta entrega: `HISTORIAL.md` (esta misma entrada), `DEPLOY.md` (actualizado); `README.md`, `backend/README.md`, `frontend/README.md`, `backend/.env.example` — revisados, no aplica ningún cambio.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.39** (solo por la convención de mantener ambos números en lockstep en cada entrega — esta no toca ni una línea de código de la app).

---

## v1.20 — Logo también en el menú lateral; título del login renombrado por Víctor (v1.19.38)

Víctor preguntó dónde vivía el texto "Catálogo DALI" / "LIBRO DE REGISTRO" del login para poder revisarlo y cambiarlo él mismo — se le indicó `LoginScreen.jsx` (línea del texto) y `index.css` (`.login-brand`/`.login-brand span`, para el estilo), y de paso se le señaló que "Catálogo DALI" también aparece en `CanjearTokenAcceso.jsx` (con otro subtítulo) y en `Sidebar.jsx`/`index.html` si quería tocarlo en más sitios. Volvió con dos cosas en el mismo mensaje: una captura del menú lateral pidiendo poner ahí también el logo de Princess ("adaptando como es normal el tamaño"), y el propio `LoginScreen.jsx` ya editado por él, con el título cambiado a "Catálogo Asignaciones" y el subtítulo a "Códigos DALI - SAP".

**Cambio 1 — logo en el sidebar**: mismo PNG que ya se usa en el login (`assets/princess-logo.png`, texto en negro, v1.19.36), pero a un ancho menor (130px, frente a los 190px del login) para caber con holgura en los 220px de ancho del propio sidebar (`.sidebar-brand-logo`, `Sidebar.jsx`). Alineado a la izquierda, no centrado — el sidebar no es una tarjeta centrada como el login, sigue el mismo eje que el texto "Catálogo DALI - SAP" de debajo.

**Cambio 2 — título del login**: se adopta tal cual el archivo que mandó Víctor ya editado — no se le pregunta de nuevo el texto, ya lo decidió y lo entregó hecho. Se incorpora como fuente de la verdad en el repo, precisamente para que la próxima entrega no lo pise sin querer con el texto anterior.

**Verificación**: `npm run build` (Vite), limpio. Cambio puramente visual — 85 aserciones de backend y 22 de E2E siguen en verde sin ninguna nueva (ninguna prueba existente dependía de este texto de marca). Comprobación visual real con capturas de pantalla (Playwright, `npm run preview` + login con `admin@demo.dali`): título nuevo visible en el login, logo bien proporcionado y alineado en el sidebar tras entrar.

Documentos de mantenimiento revisados en esta entrega: `HISTORIAL.md` (esta misma entrada); `README.md`, `backend/README.md`, `frontend/README.md`, `backend/.env.example`, `DEPLOY.md` — revisados, no aplica ningún cambio.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.38**.

---

## v1.19 — Mensaje de "¿Has olvidado tu contraseña?" más profesional para la solicitud de acceso nueva (v1.19.37)

Al ver funcionar de verdad el flujo de solicitud de acceso, Víctor planteó una duda de fondo: **"cuando el correo no esta registrado si debe obligar a introducir el nombre e indicar que deberá esperar que un administrador verifique y acepte el acceso a la aplicación o algo por el estilo profesional y coherente. Para no dar pie a pensar 'Esto no funciona' ¿que opinas?"** — es decir, planteaba dos cosas a la vez: volver a exigir el nombre solo para ese caso, y dejar claro que hace falta la aprobación de un admin.

Se le presentaron tres caminos con `AskUserQuestion`: (1) un mensaje único mejorado, que sigue sin distinguir los dos casos pero explica ambos desenlaces con más detalle; (2) distinguir de verdad el caso "solicitud nueva" (nombre obligatorio solo ahí, mensaje distinto), señalando el coste real de esa opción — permitiría a cualquiera averiguar qué emails tienen cuenta en DALI con solo probar el formulario, reabriendo exactamente el riesgo de enumeración que v1.15 ya identificó y decidió asumir de forma controlada; y (3) dejarlo tal cual. Eligió la (1), el mensaje único mejorado — coherente con no reabrir ese riesgo.

**Cambio**: se mantiene intacto todo el comportamiento — nombre sigue opcional (v1.16), mensaje sigue siendo el mismo condicional sin distinguir a nivel de texto ni de lógica qué ha pasado por detrás (v1.15) — solo cambia la REDACCIÓN de `MENSAJE_RECUPERACION`. La versión anterior, para el caso "solicitud nueva", decía "revisa tu bandeja de entrada en los próximos días" — ambigua, sonaba a que llegaría un correo automático sin más; alguien probando con un email nuevo y sin recibir nada en un rato podía pensar, razonablemente, que la función estaba rota. La nueva redacción deja explícito que hay un paso humano de por medio: *"Si aún no tienes cuenta, hemos registrado tu solicitud de acceso: un administrador la revisará y, si la aprueba, te llegará un correo de bienvenida con tu enlace de acceso — puede tardar uno o dos días laborables."* Se actualizó en paralelo, y se mantiene deliberadamente idéntica letra a letra (hay una prueba E2E dedicada a comprobarlo), la copia de este mensaje que vive en modo demo (`MENSAJE_RECUPERACION_DEMO` en `services/api.js`, no hay backend ahí que lo devuelva). El texto de ayuda que se ve ANTES de enviar el formulario (`RecuperarAccesoModal.jsx`) se retocó con el mismo criterio, para no quedar descoordinado con lo que se ve después.

**Verificación**: `node --check` en el backend. Las 85 aserciones de `tokenaccesotest/` siguen en verde sin cambios en la lista (el mensaje no tiene lógica propia, solo texto). Se amplió `e2e-token-acceso.mjs` con una aserción nueva que confirma, contra el frontend real en modo demo, que el mensaje mostrado incluye la frase "un administrador la revisará" — 22 aserciones en total, todas en verde. `npm run build` (Vite), limpio.

Documentos de mantenimiento revisados en esta entrega: `HISTORIAL.md` (esta misma entrada); `README.md`, `backend/README.md`, `frontend/README.md`, `backend/.env.example`, `DEPLOY.md` — revisados, no aplica ningún cambio.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.37**.

---

## v1.18 — Logo de Princess Hotels & Resorts en el login (v1.19.36)

Víctor mandó el logo oficial de Princess Hotels & Resorts (icono de corona + "Princess" en cursiva + "HOTELS & RESORTS") y pidió ponerlo en la pantalla de login, con fondo transparente y el texto todo en negro. El archivo que mandó ya venía con fondo transparente, pero el texto era blanco — invisible al verlo sobre un fondo claro, por eso al abrirlo parecía "en blanco" a simple vista; solo se apreciaba el dibujo componiéndolo sobre un fondo oscuro. Es el logo real de la empresa (Princess Hotels & Resorts / Central Compras Princess Canarias, la organización de Víctor), para uso interno en su propia herramienta — no un asset de terceros.

Se recoloreó el PNG (Python/Pillow: mismo canal alfa, RGB puesto a negro) en vez de redibujarlo, para conservar exactamente el antialiasing y la forma originales — resultado en `frontend/src/assets/princess-logo.png`. Se añadió a `LoginScreen.jsx` (import como asset de Vite, para que se empaquete con hash como el resto de assets) encima de "Catálogo DALI", dentro de `.login-brand`, con una clase nueva `.login-brand-logo` (ancho fijo 190px, alto automático, centrado). No se tocó `CanjearTokenAcceso.jsx`, que comparte la misma cabecera `.login-brand` — Víctor solo pidió la pantalla de login; si quiere el logo ahí también, es un cambio de una línea cuando lo pida.

**Verificación**: `npm run build` (Vite), limpio. Comprobación visual real: `npm run preview` contra el build de producción + captura de pantalla con Playwright, confirmando que el logo se ve centrado, con buen contraste y sin deformarse ni desbordar la tarjeta.

Documentos de mantenimiento revisados en esta entrega: `HISTORIAL.md` (esta misma entrada); `README.md`, `backend/README.md`, `frontend/README.md`, `backend/.env.example`, `DEPLOY.md` — revisados, no aplica ningún cambio.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.36**.

---

## v1.17 — Botones a ancho completo con el texto centrado; aclaraciones sobre solicitudes de acceso y el contador de envíos (v1.19.35)

Tras entregar v1.16, Víctor mandó dos capturas (login y Administración → Configuración EmailJS, ya con la Cuenta 1 activa y "1 envío(s) registrado(s)") con tres preguntas en el mismo mensaje.

**1) "el botón ENTRAR debería estar mas centrado el texto ¿no?"** — cierto, y era un fallo real de CSS, no cosmético aislado a ese botón: la clase base `.btn` (usada por casi todos los botones de la app) pone `display: inline-flex; align-items: center`, que centra en el eje VERTICAL, pero nunca tuvo `justify-content`, que es lo que centra en el eje horizontal — con un botón de ancho natural no se nota (el contenido ya llena el botón entero), pero en cualquier botón forzado a `width: 100%` el texto queda pegado al borde izquierdo. Buscando todos los sitios afectados aparecieron tres, no solo "Entrar": el propio login (`LoginScreen.jsx`), el botón de elegir contraseña nueva al canjear un enlace de acceso (`CanjearTokenAcceso.jsx`, comparte la misma clase `.login-submit`), y "Ver alternativas" en la ficha de artículo (`ArticuloDetail.jsx`, clase `.btn-alternativas`). Se corrige en el sitio correcto — `justify-content: center` en la clase base `.btn`, `frontend/src/styles/index.css` — en vez de parchear cada botón suelto, así cualquier botón futuro a ancho completo sale ya centrado por defecto.

**2) "y para la nueva solicitud de usuario? como seria?"** — se le explicó el flujo completo para que lo probara si quería: desde el login, "¿Has olvidado tu contraseña?" con un email que NO esté dado de alta en DALI muestra exactamente el mismo mensaje genérico que uno registrado (a propósito, ver v1.15) y registra una solicitud pendiente; como admin, en Administración → Solicitudes de acceso aparece esa solicitud con el nombre (el escrito, o el propio email de repuesto si se dejó en blanco — ver v1.16) y el email, lista para Aceptar (crea la cuenta con el rol que elija el admin y envía un enlace de bienvenida) o Rechazar.

**3) "no descuenta solo los correos enviados?"** — confirmado revisando `services/emailjs.js` y `emailjsConfig.js`: el contador de la cuenta activa (`registrarEnvioEmailjs()`) solo se incrementa DESPUÉS de que `emailjs.send()` haya tenido éxito — un fallo de envío nunca lo toca. Y cuenta por LLAMADA a EmailJS, no por destinatario: una solicitud de acceso nueva, aunque su aviso llegue a varios administradores a la vez (`destinatario` es la lista de emails de admins activos, unidos por coma, en una sola llamada a `emailjs.send()`), solo suma 1 al contador — igual que una recuperación normal dirigida a una sola persona.

**Verificación**: `npm run build` (Vite), limpio. Cambio puramente de CSS (los otros dos puntos fueron aclaraciones, sin tocar código), sin lógica nueva que cubrir en los arneses de backend/E2E ya existentes.

Documentos de mantenimiento revisados en esta entrega: `HISTORIAL.md` (esta misma entrada); `README.md`, `backend/README.md`, `frontend/README.md`, `backend/.env.example`, `DEPLOY.md` — revisados, no aplica ningún cambio.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.35**.

---

## v1.16 — El campo Nombre deja de ser obligatorio en "¿Has olvidado tu contraseña?" (v1.19.34)

Sesión de configuración guiada de EmailJS/Render tras entregar v1.15. Víctor confirmó por captura que la migración `2026-09-02_tokens_acceso_emailjs.sql` ya estaba aplicada en Supabase, creó su propia cuenta EmailJS ("CatalogoDaliSap", separada de la de `control-pedidos-princess`) y rellenó la Cuenta 1 en Administración → Configuración EmailJS con credenciales reales. Se revisó juntos, a partir de sus capturas, que la plantilla de esa cuenta usara los mismos nombres de variable que envía `services/emailjs.js` (`{{{asunto}}}`, `{{{mensaje_html}}}`, `{{to_email}}` — no los de la plantilla "Contáctenos" original de Control de Pedidos, que usa `subject`/`message`); Víctor ya los tenía corregidos al enseñar la captura. Se confirmó que el "From Name" seguía diciendo "Control de Pedidos Princess" (recomendado cambiarlo, cosmético, pendiente de que Víctor lo haga cuando quiera) y que el resto de campos opcionales (`reply_to`, `bcc`, `cc`) pueden quedarse sin tocar sin causar ningún problema, al no ser obligatorios y no rellenarse nunca desde el código. Se explicó el flujo completo de despliegue (`git push` con `autoDeploy: true` en `render.yaml` — sin necesidad de tocar variables de entorno en Render para esta función, ya que las credenciales EmailJS viven en la base de datos) y se confirmó, por captura del pie de página de la app ("V 1.19.33"), que el deploy había llegado bien a producción. Se aclaró también que la app funciona perfectamente con una sola cuenta EmailJS configurada — la Cuenta 2 solo entra en juego por rotación al llegar al umbral de envíos, no es un requisito para que el envío funcione desde ya.

Con eso, Víctor hizo la prueba real end-to-end de "¿Has olvidado tu contraseña?" en producción y confirmó que funciona ("perfecto, funciona"), pero señaló un problema de UX real en el propio formulario: exigir tanto el nombre como el email para recuperar el acceso es fricción innecesaria — **"no veo la necesidad de tener la obligacion de nombre y correo para recuperar la contraseña, si no se acuerda del nombre la hemos liado"**. Al revisar el código se confirmó que tenía toda la razón: el nombre escrito en ese formulario NUNCA se usaba para la rama de recuperación (email ya registrado) — el correo siempre saluda con `usuario.nombre`, el que ya hay guardado en la base de datos —, así que el campo obligatorio no protegía nada ni identificaba a nadie en el caso más común, solo añadía una oportunidad de bloquear a alguien sin motivo real. El único caso donde el nombre sí se usa de verdad es la rama de "solicitud de acceso" (email no registrado), para que el admin sepa quién la pide.

**Cambio**: `nombre` pasa a ser opcional en `POST /auth/recuperar-acceso` — `backend/src/controllers/authController.js` ya no lo exige (el `if (!email || !nombre)` pasa a `if (!email)`, con el mensaje de error actualizado a "Indica tu email."); si se omite y la rama resulta ser una solicitud de acceso nueva, se usa el propio email como nombre de repuesto (`nombre: nombre || email`, mismo patrón que ya usaba `ssoLogin()` para cuentas SSO sin nombre explícito). El formulario sigue sin poder saber de antemano si el email está o no registrado (por la misma razón de no-enumeración de v1.15), así que el campo Nombre no desaparece — se queda siempre visible, ahora marcado "(opcional)", y se reordena el formulario para poner primero el campo realmente necesario: Email arriba (con el foco automático), Nombre debajo. `RecuperarAccesoModal.jsx` (input, etiqueta, texto de ayuda y comentario de cabecera actualizados) y `services/api.js` (mismo criterio de repuesto en modo demo, `nombreCorto || correo`).

**Verificación**: `node --check` en `authController.js`. Se ampliaron ambos arneses ya existentes en vez de crear uno nuevo, al ser un cambio pequeño y localizado sobre código ya cubierto: `tokenaccesotest/verify.mjs` (copia de `authController.js` resincronizada con la fuente real, confirmada byte-idéntica) pasa de 71 a 85 aserciones — las 9 nuevas cubren, con 3 pruebas dedicadas: que un email registrado y activo recupera el acceso sin escribir nombre (ya no hay 400); que un email no registrado sin nombre registra la solicitud usando el propio email como nombre, tanto en el aviso a administradores como en la fila guardada; y que omitir el email sí sigue dando 400, con el mensaje ya actualizado. `e2e-token-acceso.mjs` pasa de 20 a 21 aserciones — la nueva confirma, contra el frontend real en modo demo, que enviar el formulario sin escribir nada en Nombre no queda bloqueado por la validación `required` del propio navegador y muestra el mismo mensaje genérico de siempre. Todas las aserciones, en ambos arneses, en verde.

Documentos de mantenimiento revisados en esta entrega: `HISTORIAL.md` (esta misma entrada); `README.md`, `backend/README.md`, `frontend/README.md`, `backend/.env.example`, `DEPLOY.md` — revisados, no aplica ningún cambio (ninguno documentaba el campo Nombre como obligatorio, así que no quedaban desactualizados).

Versión: `backend/package.json` y `frontend/package.json` → **1.19.34**.

---

## v1.15 — DALI autosuficiente para el envío de correo: EmailJS propio y enlaces de acceso de un solo uso (v1.19.33)

Continuación directa de v1.14, a petición de Víctor, tras varias preguntas suyas sobre las dependencias de disponibilidad del diseño anterior. Primero preguntó si, para que funcione la recuperación de acceso, tenía que estar `control-pedidos-princess` operativa, y si hacía falta que alguien tuviera una sesión abierta ahí aunque el keep-alive de GitHub Actions la mantenga despierta ("control de pedidos se mantiene despierto con github, es necesario que tambien este una sesion aboerta?"). Confirmé que sí: el keep-alive solo evita el cold-sleep del backend, pero el envío real por EmailJS lo dispara el poller de 5 minutos del navegador de quien tenga esa app abierta — sin eso, los correos de DALI se quedaban encolados indefinidamente. Preguntó también si el propio password-reset de Control de Pedidos tenía esa misma dependencia ("cuando un usuario pulsa olvide la contraseña ¿no tiene que existir una sesion abierta en control de pedidos verdad?") — no, revisé su código real (`solicitar_reset_password()` en su `app.py`) y confirmé que no: genera un token+enlace y lo manda por EmailJS directamente desde el navegador de quien lo pide, sin ninguna cola ni sesión de por medio. A partir de ahí, Víctor propuso automatizar lo que se pudiera sin depender de que alguien tenga otra app abierta, y preguntó por la viabilidad de compartir las 4 cuentas EmailJS de Control de Pedidos con DALI ("si compartimos las cuentas de emailjs con control pedidos ¿seguirian descontando usos en el panel de control pedidos?"). Expliqué el riesgo concreto: el contador de esa app es un contador LOCAL propio, que solo se incrementa cuando su propio backend lo autoriza (sesión, o un flag de un solo uso para sus 3 flujos sin login conocidos) — DALI no tiene forma de activar ese flag desde fuera, así que sus envíos consumirían cuota real de forma invisible para ese contador, arriesgando que la cuenta real se agotara a mitad de mes antes de que la rotación automática lo detectara — el mismo fallo que motivó construir el sistema de 4 cuentas en primer lugar. Recomendé una cuenta EmailJS separada y propia para DALI.

Con esa base, Víctor preguntó si montar un panel en DALI como el de Control de Pedidos, con 2 cuentas EmailJS "por seguridad", permitiría reordenar la aplicación para hacerla autosuficiente sin encolamientos, y si podía reutilizar la misma cuenta Gmail que ya usa en Control de Pedidos para las cuentas EmailJS nuevas. Confirmé ambas cosas: sí es viable (y, a diferencia de Control de Pedidos, DALI no necesita ni cola ni poller — todos sus disparadores de correo ya tienen un navegador vivo presente en el momento de la acción, nunca un envío diferido/debounced como sí tiene Control de Pedidos con sus 5 minutos de consolidación), y sí puede reutilizar la misma cuenta Gmail (EmailJS factura por cuenta EmailJS/Public Key, no por dominio que llama ni por buzón conectado — el mismo Gmail puede estar "Service" de varias cuentas EmailJS distintas, con cuota independiente cada una, que es exactamente por qué Control de Pedidos encadena 4).

Un primer intento de usar `AskUserQuestion` con tres preguntas concretas (qué cuenta EmailJS usar, cómo diseñar la recuperación, qué alcance darle) no le llegó a Víctor ("no te llego mi respuesta?") — se repitieron las mismas tres preguntas en texto plano como alternativa, y respondió con instrucciones claras y textuales: **"1. este punto lo dejamos anotado como actualizacion proxima."** (para "Documentación faltante" — queda explícitamente FUERA de esta entrega, no se toca); **"2. enlace con token de un solo uso mejor"** (en vez de contraseña temporal, para "recuperar acceso" — mismo patrón que ya usa Control de Pedidos en su propio password-reset); y **"creamos la actualizacion y luego montamos el detalle tecnico"** — construir el código/funcionalidad ahora, sin credenciales EmailJS reales todavía, y montar las cuentas reales juntos después.

**Diseño — backend**: migración nueva (`database/migraciones/2026-09-02_tokens_acceso_emailjs.sql`, a aplicar a mano en Supabase antes de desplegar — como el resto de migraciones de este proyecto): tabla `tokens_acceso` (usuario_id, token único, tipo `recuperacion`\|`bienvenida`, expira_en a 2h, usado_en, un índice parcial sobre "tokens sin usar de este usuario" para poder invalidar los anteriores al emitir uno nuevo) y `configuracion_emailjs` (fila única — `id boolean primary key default true check (id)` fuerza que solo pueda existir una — con las credenciales de las 2 cuentas, contador y umbral de rotación). `usuarios.debe_cambiar_password` (de la migración de v1.14) queda vestigial: no se borra la columna, pero ningún código de esta versión la lee ni la escribe.

`authController.js` se reescribe en la sección de recuperación de acceso: `emitirTokenAcceso(usuario, tipo)` sustituye a la generación de contraseña temporal — invalida (borra) los tokens sin usar del mismo tipo para ese usuario, genera uno nuevo (32 bytes aleatorios en base64url, mismo tamaño que `secrets.token_urlsafe(32)` de Control de Pedidos), construye el enlace a partir de `CORS_ORIGIN` (reutilizado como base — evita añadir una variable de entorno nueva tipo `APP_URL`, ya que ese valor ya es exactamente la URL del frontend) y devuelve `{envio, link}` — `envio` es el objeto `{destinatario, asunto, cuerpoHtml, cuerpoText}` que el FRONTEND manda por EmailJS, no el backend: aquí ya no hay ningún envío de correo desde el servidor. `recuperarAcceso()` ahora responde `{ok, mensaje, envio}` — mensaje genérico de siempre, más el envío (o `null` si no hay nada que mandar: cooldown, solicitud duplicada, sin admins activos). Nuevas `validarTokenAcceso()` (`GET /auth/token-acceso/:token`, pública) y `canjearTokenAcceso()` (`POST /auth/canjear-token-acceso`, pública) — la segunda guarda la contraseña elegida, marca el token usado, y abre sesión directamente (auto-login), sin pedir de nuevo el email. `solicitudesAccesoController.js` cambia `aceptarSolicitudAcceso()`: en vez de contraseña temporal, crea/reactiva la cuenta con un hash bcrypt ALEATORIO e inutilizable (nunca transmitido a nadie — mismo truco que ya usaba `ssoLogin()` para cuentas aprovisionadas por SSO) y emite un token de bienvenida, devolviendo `{data, envio, link, avisoCorreo}`.

Nuevo `configuracionEmailjsController.js` + `services/emailjsConfig.js`: `GET /auth/emailjs-config` (público) da al navegador las credenciales de la cuenta activa — con fallback automático a la otra cuenta si la activa tiene alguna credencial incompleta, y `configurado: false` si ninguna de las dos las tiene completas (caso normal recién desplegado, antes de que Víctor rellene el panel). `POST /auth/emailjs-registrar-envio` incrementa el contador local tras un envío ya hecho con éxito por el navegador, y rota a la otra cuenta al llegar al umbral (por defecto 195, igual margen que Control de Pedidos bajo el límite real de ~200/mes del plan gratuito de EmailJS) — gateado: hace falta sesión autenticada (el admin aceptando una solicitud) O un flag de un solo uso que deja `recuperarAcceso()` en la sesión anónima justo cuando de verdad generó un envío (`req.session.pdteRegistrarEnvioEmail`, mismo mecanismo en espíritu que `_permite_registrar_envio_no_autenticado()` de Control de Pedidos) — sin esta doble puerta, cualquiera podría llamar al endpoint repetidamente y desincronizar el contador respecto al uso real de la cuenta. `GET`/`PUT /admin/emailjs-config` (solo admin) para el panel de administración.

**Decisión de diseño pendiente de confirmar con Víctor** (identificada durante la implementación, no una pregunta suya explícita): al mover el envío de correo al navegador, ese navegador necesita conocer el destinatario real para pasárselo a EmailJS. Para el propio usuario en el contexto "recuperación" no hay ningún problema — es su propio email, que él mismo ha escrito. Pero en el contexto "solicitud" (email no registrado), el destinatario son los administradores — alguien inspeccionando la pestaña Red de su propio navegador podría distinguir, mirando esa llamada concreta a EmailJS, si su email estaba o no registrado en la aplicación; antes esto era imposible porque el correo se armaba y encolaba enteramente en el servidor. Es una merma real, aunque menor, de la protección de no-enumeración que sí garantizaba el diseño de v1.14. Se ha implementado igualmente — el mensaje que VE la persona (`MENSAJE_RECUPERACION`) sigue siendo idéntico letra a letra en los dos casos, y la propia respuesta JSON del backend no distingue nada por su forma, solo el CONTENIDO de `envio.destinatario` cambia — porque el riesgo práctico es bajo para una aplicación interna (exige inspeccionar DevTools a propósito) y porque Víctor pidió avanzar rápido. Mitigación posible si se quisiera cerrar del todo más adelante: un segundo template EmailJS con el destinatario fijado en el propio panel de EmailJS (no pasado como parámetro desde el navegador) para el aviso a administradores — no implementada, por ser un cambio de alcance no pedido. Comentario largo al respecto en `authController.js`; queda anotado aquí explícitamente para revisarlo con Víctor al montar las cuentas EmailJS reales.

**Diseño — frontend**: nuevo `services/emailjs.js` — `enviarPorEmailjs(envio)` es la única función que llama de verdad a `emailjs.send()` (paquete nuevo `@emailjs/browser`), consultando antes `GET /auth/emailjs-config`; best-effort a propósito (nunca lanza: si EmailJS falla o no está configurado, devuelve `{enviado:false, motivo}` en vez de romper el flujo, igual que hacía `avisoCorreo` en v1.14) y, si el envío tiene éxito, registra el envío (también best-effort). `RecuperarAccesoModal.jsx` llama a `enviarPorEmailjs()` tras `recuperarAcceso()` pero muestra SIEMPRE el mismo mensaje genérico, sin importar si el envío tuvo éxito o no — evita que un fallo de correo se traduzca en un mensaje distinto que delate qué rama del servidor se tomó (ver la decisión de diseño pendiente, arriba). `AdminSolicitudesAcceso.jsx` sí muestra el enlace en crudo tras aceptar (además de intentar enviarlo por correo) — aquí no hay ningún problema de filtración, quien lo ve ya es un admin autenticado. Nuevo `CanjearTokenAcceso.jsx` sustituye a `CambiarPasswordObligatorio.jsx` (retirado): valida el token al montar (`GET /auth/token-acceso/:token`), muestra un saludo con el nombre si es válido, deja elegir la contraseña nueva (con `CampoPassword.jsx`, mismo ojito reutilizado) y comprobación de coincidencia en el propio cliente, y al enviarla abre sesión automáticamente. `App.jsx` detecta `?token_acceso=` en la URL en un `useEffect` de montaje (mismo criterio que `?dali_token=` para el SSO — se limpia enseguida de la barra de direcciones) y muestra `CanjearTokenAcceso` ANTES que cualquier otro estado (incluso "comprobando sesión…"), tenga o no ya una sesión previa. Nuevo `AdminConfiguracionEmailjs.jsx` — formulario con las 3 credenciales de cada una de las 2 cuentas, el umbral de rotación y la cuenta activa, más un aviso informativo con el contador actual.

En modo demo (`services/api.js`), `recuperarAcceso()`/`validarTokenAcceso()`/`canjearTokenAcceso()`/`aceptarSolicitudAcceso()`/`fetchConfigEmailjsAdmin()`/`actualizarConfigEmailjsAdmin()` replican el mismo comportamiento sobre copias en memoria (`demoTokensAcceso`, `demoConfigEmailjs`) — se retira la cuenta de demo fija `temporal@demo.dali` de v1.14 (ya no hace falta, no hay pantalla de cambio obligatorio que demostrar con una cuenta prefabricada) y `recuperarAcceso()` en demo pasa a mirar `demoListaUsuarios` (la tabla `usuarios` simulada, la que el panel de administración puede modificar) en vez de la lista fija de contraseñas de login, igual criterio que el backend real. `obtenerConfigEmailjs()`/`registrarEnvioEmailjs()` son no-op en demo (`configurado: false` siempre) — nunca se llega a llamar a EmailJS de verdad en modo demo, el resto del flujo ya queda simulado en memoria.

**Ningún fallo propio detectado durante la implementación en este segmento** (a diferencia de v1.14, donde se autocorrigieron dos antes de cualquier prueba) — el diseño reutiliza patrones ya validados en la entrega anterior (orden de operaciones, invalidación de tokens anteriores, hash aleatorio inutilizable calcado del que ya usaba `ssoLogin()`), y las 71 aserciones de backend (ver Verificación) no encontraron ningún caso roto en el primer intento.

**Verificación**: `npm run build` (Vite), limpio — `AdminConfiguracionEmailjs.jsx` y `AdminSolicitudesAcceso.jsx` (ya existía) se separan en sus propios chunks. `node --check` en los nueve ficheros de backend nuevos/tocados. Backend probado con un doble de Supabase en memoria extendido para esta versión (arnés nuevo en `tokenaccesotest/`, mismo patrón que `recuperaciontest/` de v1.14: importa `authController.js`/`solicitudesAccesoController.js`/`configuracionEmailjsController.js` REALES sin modificar ni una línea, confirmados byte-idénticos a la fuente tras la prueba) — se le añadieron al doble de Supabase soporte para `.delete()`, `.is(col, null)` (con el mismo criterio que Postgres: un campo nunca asignado en un `insert()` cuenta como `null`, no solo `undefined`) y un embebido simple `usuarios!inner(...)` para las dos consultas de `tokens_acceso` que lo necesitan. 71 aserciones: generación/invalidación de tokens (un segundo token del mismo tipo reemplaza al anterior; un tipo distinto no lo toca), las tres ramas de `recuperarAcceso` (registrado activo, desactivado tratado como no registrado, no registrado) más cooldown/duplicados/sin-admins, `validarTokenAcceso` (válido, usado → 410, caducado → 410, inexistente → 404), `canjearTokenAcceso` (contraseña corta, canje válido con auto-login, y una prueba de regresión dedicada: el mismo token no se puede canjear una segunda vez), `aceptarSolicitudAcceso` (cuenta nueva sin devolver ninguna contraseña, con una prueba de regresión dedicada de que el hash no es ni vacío ni una contraseña trivial; ya activa → 409; reactivar desactivada), rotación de `emailjsConfig` (fallback a la otra cuenta si la activa está incompleta, rotación al umbral solo si la otra cuenta SÍ está completa, contador que sigue subiendo sin rotar si no lo está) y el gateado de `registrarEnvioEmailjsEndpoint` (autenticado siempre vale; sin sesión hace falta el flag; el flag se consume tras un solo uso — regresión dedicada).

Prueba end-to-end real con Playwright contra el frontend real en modo demo: 20 aserciones. Se documenta explícitamente en el propio script la limitación de fondo del modo demo para esta funcionalidad — todos sus datos viven en memoria del navegador y se pierden en cualquier recarga real de página (igual que YA le pasa a `demoArticulos`/`demoListaUsuarios` desde mucho antes), así que "abrir el enlace" en el sentido literal de una navegación real solo es reproducible desde una pestaña recién cargada que, por definición, nunca tiene en memoria un token generado un momento antes en OTRA carga de página — no es un fallo de esta versión, es una limitación ya inherente a cómo funciona el resto del modo demo. Por eso se separan dos cosas que sí son comprobables de verdad, sin fingir una continuidad que el modo demo no tiene: (1) que la propia UI genera de verdad un mensaje idéntico letra a letra entre email registrado y no registrado, y que "Aceptar solicitud" produce un enlace bien formado (`?token_acceso=`, origen correcto) sin ningún error de consola sin capturar; (2) que ese enlace generado por la UI es de verdad redimible — verificado llamando a `validarTokenAcceso`/`canjearTokenAcceso` del MISMO módulo `api.js` ya cargado en esa pestaña (misma memoria, sin recargar), confirmando nombre/email/rol correctos y, como regresión, que el mismo token no se puede canjear dos veces; y (3) que `CanjearTokenAcceso.jsx` como componente, en una carga de página fresca (100% reproducible), maneja bien un enlace inválido/inexistente — aviso de error, botón de vuelta al login, URL limpiada. Se comprueba además, por separado, el guardado y persistencia de credenciales en Administración → Configuración EmailJS. Sin errores de consola en ningún bloque.

Documentos de mantenimiento revisados en esta entrega: `README.md` (sección "Pendientes generales" actualizada: recuperación de acceso ahora autosuficiente, "Documentación faltante" anotado como próxima actualización); `backend/README.md` (tabla de endpoints con las 7 rutas nuevas/cambiadas, sección "Autenticación" reescrita con el diseño v1.15 y la decisión de diseño pendiente, `req.user` sin `debeCambiarPassword`, "Pendiente" actualizado); `frontend/README.md` (documenta `CanjearTokenAcceso.jsx`, `AdminConfiguracionEmailjs.jsx`, retira las menciones a `CambiarPasswordObligatorio.jsx`/contraseña temporal, nota sobre la dependencia nueva `@emailjs/browser`); `backend/.env.example` (aclara que `CORS_ORIGIN` ahora también es la base de los enlaces de acceso, y que las credenciales EmailJS van por el panel de administración, no por variable de entorno).

**Importante para el despliegue**: esta entrega necesita aplicar a mano en Supabase la migración `database/migraciones/2026-09-02_tokens_acceso_emailjs.sql` ANTES de desplegar el backend nuevo (crea `tokens_acceso` y `configuracion_emailjs` — sin ellas, `recuperarAcceso()`/`aceptarSolicitudAcceso()` fallarían). El correo NO se enviará de verdad hasta rellenar las credenciales reales de las 2 cuentas EmailJS desde Administración → Configuración EmailJS (el enlace se sigue generando igual mientras tanto, disponible para copiar a mano) — pendiente de hacer juntos, según lo acordado ("creamos la actualizacion y luego montamos el detalle tecnico"). En `frontend/`, ejecutar `npm install` para traer la dependencia nueva `@emailjs/browser` antes de `npm run dev`/`npm run build`.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.33**.

---

## v1.14 — "¿Has olvidado tu contraseña?", ojito de la contraseña, y solicitudes de acceso admin-aprobadas (v1.19.32)

Funcionalidad nueva a petición de Víctor, fuera de la auditoría full (ya cerrada en v1.11/v1.19.29), tras entregar el sidebar más limpio (v1.13). Adjuntó dos capturas del login (`LoginScreen.jsx`) y `controlpedidosprincessmain.zip`, con el encargo textual: "podemos incluir el 'ojito' que visualiza la escritura de la contraseña? Podemos incluir un botón para no recuerdo contraseña? utilizar tal y como hacemos ya con documentación faltante, utilizamos emailjs de control pedidos, si el correo no esta registrado, se envía un aviso por correo electrónico a los admin de la aplicación indicando que este usuario esta solicitando acceder, si se acepta se le envía un nuevo correo al nuevo usuario con una contraseña temporal aleatoria para que en la primera entrada pueda cambiar." — tres piezas: (1) un "ojito" para ver/ocultar la contraseña al escribirla, (2) un botón de "olvidé mi contraseña" en el login, (3) un flujo de doble camino reutilizando la misma infraestructura de correo que "Documentación faltante" (cola de `emails_sistema_pendientes` en `control-pedidos-princess`, sin SMTP propio en ningún sitio — el envío real lo hace EmailJS desde el navegador de un admin).

Antes de escribir código se resolvieron dos ambigüedades reales con Víctor, ambas con la opción recomendada: **qué pasa si el email SÍ está registrado y se pulsa "olvidé mi contraseña"** — contraseña temporal directa por correo, sin pasar por ningún admin (es la propia cuenta del usuario, autoservicio); **cómo "acepta" un admin una solicitud nueva (email no registrado)** — pantalla nueva dedicada, "Administración → Solicitudes de acceso" con una tabla `solicitudes_acceso` propia y acciones Aceptar/Rechazar por fila, en vez de reutilizar la pantalla ya existente de Administración → Usuarios (opción descartada explícitamente por Víctor).

**Diseño — backend**: migración nueva (`database/migraciones/2026-09-02_recuperacion_acceso.sql`, a aplicar a mano en Supabase antes de desplegar esta versión — como el resto de migraciones de este proyecto, no se funde en `schema.sql`): añade `usuarios.debe_cambiar_password boolean not null default false` y crea `solicitudes_acceso` (id, nombre, email, estado `pendiente`\|`aceptada`\|`rechazada`, creado_en, resuelto_en, resuelto_por), con un índice único parcial que evita una segunda solicitud PENDIENTE para el mismo email.

`POST /auth/recuperar-acceso` (público, sin sesión — `authController.js`): valida `email`+`nombre`, aplica un cooldown en memoria de 3 minutos por email (mismo patrón que el antirrepetición `_jtiUsados` ya existente del SSO), y busca el email en `usuarios`. Si existe y está `activo`, genera una contraseña temporal (`crypto.randomInt` sobre un alfabeto sin caracteres confusos — `contrasenaTemporal.js`, nuevo) y la envía por correo; si no existe, o existe pero está **desactivada** (tratada igual que "no registrada" a propósito — una cuenta que un admin desactivó no debe recuperarse sola sin que alguien lo revise), registra una fila en `solicitudes_acceso` y avisa por correo a los admins activos (sin duplicar si ya hay una pendiente para ese email). Responde SIEMPRE el mismo mensaje genérico, exista o no el email — para no revelar qué direcciones están dadas de alta en la aplicación, mismo criterio de no-enumeración que ya seguía el propio `login()`.

`POST /admin/solicitudes-acceso/:id/aceptar` (`solicitudesAccesoController.js`, nuevo) crea o reactiva la cuenta con el rol elegido por el admin (`admin`\|`hotel`, por defecto `hotel`), le pone una contraseña temporal real y `debe_cambiar_password: true`, marca la solicitud como aceptada, y encola el correo de bienvenida — devolviendo también la contraseña en la respuesta como red de seguridad si el correo no llega a tiempo (aquí sí es seguro devolverla: quien la ve es un admin autenticado realizando una acción explícita, no filtra nada a nadie que no debería verla). `POST /admin/solicitudes-acceso/:id/rechazar` solo marca la solicitud como rechazada, sin avisar a quien la pidió. `POST /auth/cambiar-password-obligatorio` (requiere sesión) es el paso final: pide la contraseña actual (la temporal) + la nueva, comprueba la actual por hash, y pone `debe_cambiar_password: false` tanto en BD como en la sesión — `middleware/auth.js` pasa a adjuntar `debeCambiarPassword` en `req.user`, y `login()`/`ssoLogin()` lo propagan (`ssoLogin()` lo fija siempre a `false`: nunca hay contraseña que cambiar entrando por SSO).

**Dos fallos que me autocorregí durante la implementación, antes de cualquier prueba** (ninguno fue detectado por Víctor ni por una prueba fallida — los encontré revisando mi propio primer borrador):

1. *Orden correo-antes-que-BD invertido.* El primer borrador de `emitirContrasenaTemporal()` guardaba la contraseña nueva en BD y SOLO DESPUÉS intentaba encolar el correo. Si el encolado fallaba (Control de Pedidos caído/lento — un caso real, documentado en `controlPedidosEmailBridge.js` con su propio timeout de 15s), la cuenta se quedaba con una contraseña nueva que nadie conocía, sin ninguna forma de recuperar el acceso salvo pedirlo otra vez — un bloqueo PEOR que el que se pretendía arreglar. Arreglado invirtiendo el orden: se encola el correo PRIMERO (si falla, se aborta sin haber tocado nada — la contraseña antigua sigue funcionando) y solo si el correo se encola bien se actualiza la BD.
2. *Placeholder de contraseña vacía.* El primer borrador de `aceptarSolicitudAcceso()` insertaba la cuenta nueva con `hash_password: ""` como placeholder, pensando sustituirlo enseguida en un segundo paso. Si ese segundo paso fallaba por cualquier motivo, quedaba una cuenta con un hash vacío (inutilizable) y, encima, un reintento chocaría con la guarda de "ya existe una cuenta activa" — un callejón sin salida confuso. Arreglado generando la contraseña real ANTES del único INSERT/UPDATE, así que nunca existe un estado intermedio con la contraseña vacía.

**Diseño — frontend**: `CampoPassword.jsx` (nuevo, componente compartido) centraliza el "ojito" — un botón que alterna `type="password"`/`type="text"` sobre el mismo input, con su propio estado — reutilizado en `LoginScreen.jsx`, `UsuarioForm.jsx` (decisión propia, no pedida explícitamente: mismo campo de contraseña, misma consistencia visual) y la nueva pantalla de cambio obligatorio. `RecuperarAccesoModal.jsx` (nuevo) es el formulario de "¿Has olvidado tu contraseña?" — un diálogo centrado (no el panel lateral `.detail-panel` de administración: aquí todavía no hay sesión ni "app shell" detrás) con nombre+email, mostrando siempre el mismo mensaje genérico que devuelve el backend. `CambiarPasswordObligatorio.jsx` (nuevo) es la pantalla de bloqueo — `App.jsx` la muestra en vez del resto de la app si `sesion.debeCambiarPassword` es `true`, justo después de los dos `return` tempranos ya existentes ("comprobando sesión" / "sin sesión"), respetando el mismo orden. `AdminSolicitudesAcceso.jsx` (nuevo, cargado con `lazy()` igual que las otras 6 pantallas de administración desde v1.11) mirra el patrón de `AdminUsuarios.jsx`: tabla de pendientes con un selector de rol y Aceptar/Rechazar por fila, más una tabla de resueltas debajo; tras aceptar, enseña la contraseña temporal en pantalla (con aviso si el correo no se pudo encolar). Nueva pestaña "Solicitudes de acceso" en el sidebar de administración.

En modo demo (`services/api.js`), `recuperarAcceso()`/`cambiarPasswordObligatorio()`/`fetchSolicitudesAcceso()`/`aceptarSolicitudAcceso()`/`rechazarSolicitudAcceso()` replican el mismo comportamiento sobre copias en memoria, sin backend — incluida una cuenta de demo nueva, `temporal@demo.dali` / `Temporal123`, con `debeCambiarPassword: true` ya puesto desde el login, para poder ver/probar la pantalla forzada sin depender de pasar antes por el flujo real; y una solicitud de acceso sembrada de fábrica (`prueba@demo.dali`) para que la pantalla nueva no se vea vacía la primera vez.

**Verificación**: `npm run build` (Vite), limpio — `AdminSolicitudesAcceso.jsx` se separa en su propio chunk (4,42 KB), igual que las otras 5 pantallas de administración desde v1.11. `node --check` en los seis ficheros de backend nuevos/tocados. Backend probado con un doble de Supabase en memoria (arnés nuevo en `recuperaciontest/`, mismo patrón que `jerarquiatest/` de v1.13: reproduce la parte encadenable de `@supabase/supabase-js` que de verdad usa este código —`select/insert/update` + `eq` + `maybeSingle/single`, o awaited directamente— e importa `authController.js`/`solicitudesAccesoController.js` REALES sin modificar ni una línea) más un doble del puente de correo (registra las llamadas, puede forzar que la siguiente falle). 62 aserciones: contraseña temporal directa para email registrado y activo; cuenta desactivada tratada como no registrada (pasa a solicitud, sin tocar su contraseña); email no registrado crea una solicitud y avisa a los admins; solicitud pendiente duplicada no se repite ni reenvía aviso; cero admins activos no revienta (la solicitud se registra igual); cooldown de 3 minutos por email; `cambiarPasswordObligatorio()` con sus cuatro validaciones (actual incorrecta, nueva corta, igual a la actual, caso correcto); las tres funciones de `solicitudesAccesoController.js` (listar, aceptar creando cuenta nueva, aceptar con email ya activo → 409, aceptar reactivando una cuenta desactivada con el rol elegido, rechazar, doble-resolución bloqueada, id inexistente → 404); y, explícitamente, los dos fallos que me autocorregí (arriba) como pruebas de regresión dedicadas. Antes de dar cada arreglo por bueno se reintrodujo cada fallo a propósito (el orden BD-antes-que-correo; el placeholder de contraseña vacía) y se confirmó que las pruebas de regresión correspondientes fallan de verdad, no solo que existen — revertido cada uno antes de esta entrega.

Prueba end-to-end real con Playwright contra el frontend real en modo demo (`admin@demo.dali`, `hotel@demo.dali`, `temporal@demo.dali`, sin ningún mock): 21 aserciones cubriendo el ojito (oculta por defecto, lo muestra en claro sin perder lo escrito, lo vuelve a ocultar); el modal de "¿Has olvidado tu contraseña?" (se abre, mensaje genérico correcto, se cierra); la pantalla de cambio obligatorio completa (entrar con `temporal@demo.dali` la fuerza; una contraseña nueva de menos de 8 caracteres bloquea el envío por la propia validación HTML5 del campo, sin llegar a la API; las dos contraseñas nuevas que no coinciden se rechazan con el mensaje correcto; con datos válidos entra a la app normal); y el ciclo completo de Solicitudes de acceso como admin (rechazar la solicitud sembrada de fábrica y verla pasar a "Rechazada" en resueltas; generar una solicitud nueva de verdad a través del propio modal de recuperación, aceptarla con rol "Administrador", ver el aviso con la contraseña temporal y nombre/email correctos, verla pasar a "Aceptada", y confirmar que la cuenta nueva aparece en Administración → Usuarios con el rol elegido). Comprobado también, por separado, que el mismo componente `CampoPassword.jsx` funciona igual dentro de `UsuarioForm.jsx` (alta de usuario desde Administración → Usuarios).

Documentos de mantenimiento revisados en esta entrega: `README.md` (se actualiza la sección "Pendientes generales" — la recuperación de contraseña por email deja de figurar como pendiente); `backend/README.md` (tabla de endpoints con las 5 rutas nuevas, sección "Autenticación" ampliada con el diseño del flujo y `req.user.debeCambiarPassword`, "Pendiente" separa la verificación por inactividad —que sigue abierta— de la recuperación de contraseña —ya resuelta—); `frontend/README.md` (documenta el ojito, el modal de recuperación, la pantalla de cambio obligatorio y la nueva pantalla de administración; se retira la pantalla de "olvidé mi contraseña" de "Pendiente / siguientes pasos", que queda sin pendientes).

**Importante para el despliegue**: esta entrega necesita aplicar a mano en Supabase la migración `database/migraciones/2026-09-02_recuperacion_acceso.sql` ANTES de desplegar el backend nuevo (añade la columna `usuarios.debe_cambiar_password` y la tabla `solicitudes_acceso` — sin ella, `login()`/`recuperarAcceso()` fallarían al intentar leer/escribir esa columna).

Versión: `backend/package.json` y `frontend/package.json` → **1.19.32**.

---

## v1.13 — Sidebar más limpio: se ocultan las naturalezas/familias/subfamilias sin ningún DALI activo (v1.19.31)

Funcionalidad nueva a petición de Víctor, fuera de la auditoría full (ya cerrada en v1.11/v1.19.29), tras entregar el botón "Imprimir" (v1.12): "para tener un menú mas limpio, es posible que aquellas subfamilias que no tengan Dalí activos directamente no se vean en el menú lateral? si una familia contiene subfamilias y ninguna de estas tienen artículos activos lo mismo, se ocultan a la vista, en caso de pulsar 'incluir no activos' entonces si aparecerían". Adjuntó dos capturas del sidebar y del catálogo mostrando el ejemplo real: la naturaleza BAZAR, con su única familia "ARTICULOS BAZAR", sin ningún DALI activo — al entrar ahí, "0 artículo(s)" y "Ningún artículo coincide con la búsqueda".

**Diagnóstico**: `GET /jerarquia` (`jerarquiaController.js`) devolvía el árbol de clasificación (naturaleza → familia → subfamilia) completo y sin filtrar, tal cual está la tabla `naturalezas`/`familias`/`subfamilias` en Supabase — sin cruzar en ningún momento contra `articulos` para saber si una rama tiene contenido de verdad. `Sidebar.jsx` pintaba el árbol recibido sin más criterio, así que una rama sin ningún artículo activo (o sin ningún artículo en absoluto) aparecía en el menú exactamente igual que una con miles — el único indicio de que estaba vacía era entrar y ver "0 artículo(s)".

**Solución**: `GET /jerarquia` pasa a calcular, para cada naturaleza/familia/subfamilia, cuántos artículos tiene — por defecto solo los activos (mismo criterio `activo_dali = true AND activo_general = true` que ya usa el resto de la app para un usuario normal), y con `?todos=true` (respetado únicamente si quien pregunta tiene sesión admin, exactamente igual que en `GET /articulos`) cuenta también los inactivos — y descarta del árbol devuelto cualquier nodo cuyo conteo sea cero. El conteo (`obtenerConteosClasificacion`, nueva función en `jerarquiaController.js`) recorre `articulos` pidiendo solo tres columnas enteras (`id_naturaleza, id_familia, id_subfamilia`, nada de nombre/códigos/proveedor — el resto del árbol ya lo trae la propia consulta a naturalezas/familias/subfamilias) y clasifica cada fila en el nivel MÁS PROFUNDO que tenga asignado: un artículo con familia pero sin subfamilia "sostiene visible" a su familia sin inflar el conteo de ninguna subfamilia suya en concreto, y de igual manera un artículo con naturaleza pero sin familia sostiene visible a su naturaleza. La ruta `GET /jerarquia` pasa a llevar `optionalAuth` (antes no llevaba ningún middleware) para poder saber, igual que `/articulos`, si quien pregunta es admin — sigue siendo pública, sin `requireAuth`, un usuario sin sesión simplemente nunca puede pedir `?todos=true`.

En el frontend, `fetchJerarquia()` (`services/api.js`) pasa a aceptar `{ todos }` y a reenviarlo como query param; el modo demo replica el mismo criterio en JS a partir de `mockArticulos` (que ya trae varios `activo_dali: false` a propósito, incluida TODA la naturaleza BAZAR de la muestra — el mismo ejemplo real que dio Víctor, una casualidad útil para las pruebas). `App.jsx` deja de pedir el árbol "una sola vez sin más" y pasa a depender de `incluirNoActivosMenu` (`esAdmin && verTodos`, el mismo estado del checkbox "Incluir no activos" del catálogo) — solo se refresca cuando ese valor cambia de verdad, así que para hotel (que nunca ve el checkbox) el árbol se sigue pidiendo una única vez, igual que antes. Añadido también un efecto pequeño: si el árbol cambia y la naturaleza/familia/subfamilia que el usuario tenía seleccionada deja de existir en el árbol nuevo (típicamente, un admin desmarca "Incluir no activos" mientras tenía abierta una rama que solo tenía artículos inactivos), la selección sube sola al nivel más profundo que siga existiendo — igual que si se hubiera pulsado ahí mismo en el sidebar — en vez de quedarse en un filtro "fantasma" sin ningún botón resaltado en el menú y sin manera evidente de volver atrás salvo "Todas las naturalezas".

Decisión de diseño explícita: el conteo se hace con una consulta ligera y dedicada (tres columnas enteras por fila, sin `SELECT_COMPLETO`) en vez de reutilizar el listado de artículos ya existente — traer el catálogo completo (~6.763 activos) solo para calcular qué ramas del sidebar mostrar habría sido un coste de egress de Supabase muy por encima del beneficio, para una funcionalidad puramente cosmética de navegación; el conteo, en cambio, se pide una única vez al cargar la app y, como mucho, una vez más si un admin marca/desmarca el checkbox — nunca por cada tecla de una búsqueda ni por cada cambio de página.

**Verificación**: `npm run build` (Vite), limpio; `node --check` en los tres ficheros de backend tocados (`jerarquiaController.js`, `articulos.js`/rutas, `articulosController.js`, este último solo por exportar la constante `SUPABASE_MAX_ROWS_POR_PETICION` ya existente para reutilizarla). Este sandbox no tiene acceso a un Supabase real — igual que el resto de esta auditoría — así que `obtenerConteosClasificacion`/`obtenerJerarquia` se probaron con un doble de Supabase en memoria (arnés nuevo en `jerarquiatest/`) que reproduce la parte de la API encadenable de `@supabase/supabase-js` que de verdad usa este código (`.from().select().eq().order().range()`, con `.range()` paginando de verdad por encima de 1.000 filas), importando el propio `jerarquiaController.js` REAL sin modificar ni una línea — no una reimplementación de su lógica. 20 aserciones, cubriendo: el ejemplo exacto de Víctor (BAZAR desaparece del todo para un usuario normal, reaparece completo — familia y las dos subfamilias — para un admin con "Incluir no activos"); una naturaleza con una subfamilia activa y otra no (la familia se queda visible por la primera, solo se oculta la vacía); artículos "directos" sin familia o sin subfamilia asignada (sostienen visible a su padre aunque los hijos del árbol se queden todos sin ningún artículo propio); que `activo_dali=true` con `activo_general=false` NO cuenta como activo (una naturaleza cuyo único artículo está en ese estado se queda oculta igual, no basta con mirar una sola de las dos columnas); que `?todos=true` en la URL se ignora del todo para quien no tiene sesión admin; y que un error de Supabase se propaga como 500 en vez de devolver en silencio un árbol vacío. Para confirmar que la prueba detecta de verdad una regresión y no solo que "algo se pinta", se quitó a propósito el filtro `activo_general` del backend y se comprobó que el caso dedicado a esa combinación falla como se esperaba; revertido antes de esta entrega.

Aparte, prueba end-to-end real con Playwright contra el frontend real en modo demo (`admin@demo.dali` y `hotel@demo.dali`, sin ningún mock, mismo enfoque ya usado en el resto de esta auditoría): confirmado que hotel nunca ve BAZAR en el sidebar ni el checkbox "Incluir no activos" en ningún sitio del DOM; que un admin con el checkbox sin marcar ve exactamente el mismo árbol que hotel (sin BAZAR); que al marcarlo BAZAR reaparece, con su familia "ARTICULOS BAZAR" y sus dos subfamilias ("BEBIDAS BAZAR", "CREMAS SOLARES BAZAR"); y que, al desmarcarlo de nuevo con BAZAR todavía seleccionado, el sidebar recupera un estado consistente (como mucho un botón queda resaltado) en vez de quedarse en un filtro fantasma. También aquí se comprobó la detección de una regresión deliberada (quitar el filtro de activos del modo demo de `fetchJerarquia()` en `services/api.js`): la prueba falló señalando que BAZAR seguía visible donde no debía, confirmando que de verdad ejercita el comportamiento y no solo la forma del árbol; revertido antes de esta entrega. Por último, se repitió sin cambios la prueba end-to-end del botón "Imprimir" (v1.12) para confirmar que tocar `services/api.js` (mismo fichero, función distinta) no le afectó — mismos resultados exactos.

Documentos de mantenimiento revisados en esta entrega: `README.md`, `frontend/README.md` — no aplica ningún cambio en ninguno; `backend/README.md` sí se actualiza (la fila de `GET /jerarquia` en la tabla de endpoints ya no dice "árbol completo" y ahora menciona el filtrado por artículos y el `?todos=true` solo-admin, igual que ya documentaba `/articulos`).

Versión: `backend/package.json` y `frontend/package.json` → **1.19.31**.

---

## v1.12 — Botón "Imprimir" en el catálogo, con las mismas columnas para admin y hotel (v1.19.30)

Funcionalidad nueva a petición de Víctor, fuera de la auditoría full (ya cerrada en v1.11/v1.19.29): "necesito incluir un botón que pueda imprimir los que tengamos filtrado en pantalla, en diferencia con exportar, necesito que tanto el rol admin como el rol hotel al imprimir obtengan el mismo resultado". Se adjuntaron dos capturas del catálogo (vista "Todos los artículos") con los botones "Exportar Excel"/"Exportar PDF" ya existentes y la configuración de columnas de la exportación en PDF del rol hotel, como referencia del resultado que debía replicar "Imprimir".

Antes de escribir código se resolvieron dos ambigüedades reales con Víctor (mecanismo y alcance), ambas resueltas con la opción recomendada: **mecanismo** — diálogo de impresión nativo del navegador (`window.print()`), no generar un PDF forzado a las columnas de hotel y descargarlo; **alcance** — todos los artículos que cumplen el filtro activo en pantalla, en todas las páginas, igual que "Exportar" ya hace, no solo la página visible en ese momento.

**Diseño**: no hacía falta ningún cambio de backend — el endpoint público de listado ya existente (`GET /articulos`, `fetchArticulos()` en `services/api.js`) sirve igual para traer el conjunto completo filtrado, sin pasar por el pipeline de exportación a fichero (`exportController.js`/`generarExportWorker.js`, con su propia consulta "sin aplanar" y su generación de PDF/Excel real). La diferencia de forma de los datos entre los dos caminos importaba: el endpoint de listado devuelve los artículos ya "aplanados" (`aplanarArticulo()` en `articulosController.js`: `articulo.proveedor` como texto simple, no el objeto anidado `articulo.proveedores.nombre_proveedor` que usa el pipeline de exportación), así que la tabla de impresión tuvo que construirse con esos nombres de campo aplanados, no los del PDF/Excel.

Con potencialmente miles de artículos filtrados (hasta ~6.763 activos hoy) y el tope real del backend de 3.000 filas por página (`MAX_PAGE_SIZE` en `articulosController.js`, el mismo límite que ya obligó a paginar en la segunda etapa de la auditoría full), `imprimirListado()` recorre las páginas necesarias en un bucle simple, acumulando resultados hasta cubrir el `total` que devuelve el propio backend en cada respuesta.

El requisito central —resultado idéntico para admin y hotel— se resolvió con la decisión más simple posible: la tabla de impresión no consulta `esAdmin` en ningún momento para decidir columnas, sencillamente solo conoce las 7 columnas del rol hotel (Código DALI, Código SAP, Código Proveedor, Artículo, Proveedor, Unidad, Cantidad en blanco), calcadas de `columnasPdf(esAdmin=false)` en `backend/src/workers/generarExportWorker.js`. No hay ninguna rama de código que pueda mostrar "Activo" al imprimir, para ningún rol — no es un caso que haya que vigilar en tiempo de ejecución, es imposible por construcción.

Para la propia mecánica de imprimir sin generar fichero: la tabla completa se pinta en un `<div className="print-view">` oculto en pantalla normal (`display: none`) y solo visible dentro de `@media print` (CSS nuevo en `styles/index.css`, sin precedente hasta ahora en este proyecto), colocado como HERMANO de `.app-shell` (el `return` de `App.jsx` pasa a envolverse en un `<>...</>` para poder tener los dos como hermanos) en vez de anidado dentro — así `@media print` solo necesita ocultar `.app-shell` entero y mostrar `.print-view`, sin tener que lidiar con ocultar selectivamente hijos concretos del árbol normal de la app. Dos `useEffect` nuevos (declarados, como exige React, antes de los `return` tempranos de "comprobando sesión"/"sin sesión" que tiene `App.jsx`) hacen el resto: uno llama a `window.print()` con `requestAnimationFrame` en cuanto la lista a imprimir deja de ser `null` (esperar un frame evita abrir el diálogo con la tabla todavía vacía en algunos navegadores), y otro escucha el evento `afterprint` de la ventana para volver a poner la lista a `null` y desmontar la tabla — así no queda una tabla de miles de filas colgada en el DOM el resto de la sesión, y la próxima vez que se pulse "Imprimir" trae datos frescos en vez de reutilizar los de la vez anterior.

**Verificación**: `npm run build` (Vite), limpio. Prueba end-to-end real con Playwright contra el frontend real en modo demo (login de demo del propio proyecto, `admin@demo.dali` Y `hotel@demo.dali`, sin ningún mock de `api.js`, siguiendo el mismo enfoque ya usado en la etapa final de la auditoría full): para cada uno de los dos roles por separado, confirmado que el botón "Imprimir" está visible en la topbar; que al pulsarlo aparece la tabla de impresión en el DOM y se invoca `window.print()` (interceptado con una función propia antes del clic, porque un Chromium sin cabeza no puede imprimir de verdad); que las 7 cabeceras de la tabla son exactamente las del rol hotel, en el mismo orden, para los DOS roles por igual, y que "Activo" no aparece nunca; que la última columna ("Cantidad") llega vacía; que emulando el medio `print` del navegador (`page.emulateMedia`) `.app-shell` pasa a `display: none` de verdad y `.print-view` a `display: block`; y que, al disparar `afterprint`, `.print-view` se desmonta del DOM. Sin errores de consola relevantes en ninguna de las dos sesiones (filtrado el único ruido ya conocido de este entorno de pruebas, `ERR_TUNNEL_CONNECTION_FAILED` del proxy de red del sandbox, ajeno por completo al código bajo prueba). Para probar que la prueba detecta de verdad una diferencia de columnas entre roles — no solo que algo se pinta en pantalla — se introdujo a propósito una columna "Activo" condicionada a `esAdmin` en la vista de impresión y se repitió la misma prueba contra ese código roto: falló exactamente como se esperaba, señalando tanto la cabecera de más como la presencia explícita de "Activo"; revertido de inmediato tras confirmarlo. Por separado, como el catálogo de modo demo solo tiene 22 artículos (nunca ejercita más de una vuelta real del bucle de paginación), se verificó esa lógica de forma aislada, sin navegador, reproduciendo el mismo algoritmo exacto con una fuente de datos simulada para totales de 0, 1, 2.999, 3.000, 3.001, 6.000, 6.763 (la cifra real de activos DALI citada en el requisito) y 9.000 artículos: en los ocho casos se acumula el total exacto sin duplicados ni huecos, con el número de llamadas esperado a `fetchArticulos` (1 llamada hasta 3.000 artículos, 2 hasta 6.000, 3 hasta 9.000).

Documentos de mantenimiento revisados en esta entrega: `README.md`, `backend/README.md`, `frontend/README.md` — no aplica ningún cambio en ninguno (ninguno menciona el botón "Exportar" hoy, así que tampoco hacía falta documentar "Imprimir" en ellos).

Versión: `backend/package.json` y `frontend/package.json` → **1.19.30** (backend sin cambios en esta entrega — no hizo falta tocar el API, se reutiliza el endpoint público de listado ya existente; se sube igual para mantener sincronizados los dos `package.json`).

---

## v1.11 — Undécima y última etapa de la auditoría full: las 6 pantallas de Administración se cargaban siempre, para cualquiera (v1.19.29)

Último pendiente de la lista de frontend, y cierre de la auditoría full completa de esta app.

**Diagnóstico**: `App.jsx` importaba de forma estática las 6 pantallas de Administración (`AdminArticulos.jsx`, `ImportarExcel.jsx`, `AdminUsuarios.jsx`, `AdminDocumentacionFaltante.jsx`, `AdminProveedores.jsx`, `AdminExportarZip.jsx`), cada una arrastrando además sus propios componentes — `AdminArticulos.jsx`, por ejemplo, importa `ArticuloForm.jsx` y `CargaMasivaModal.jsx`, más de 2.000 líneas entre las dos, los dos componentes más grandes de todo el frontend. Con importaciones estáticas, Vite mete todo eso en el mismo bundle principal, así que CUALQUIER visita a la app descarga y ejecuta ese código, lo use o no. Toda la app exige sesión iniciada (no hay catálogo público sin cuenta), pero de esa gente con sesión, la inmensa mayoría no tiene rol admin (`esAdmin`) y nunca llega a abrir ni una sola de estas 6 pantallas; e incluso un admin de verdad, en una sesión de trabajo normal, suele visitar solo una o dos de las 6 a la vez, no las 6 juntas.

**Solución**: las 6 pasan a cargarse con `lazy()` de React en vez de una importación estática normal, envueltas en un único `<Suspense>` compartido — como solo puede haber una `vista` de administración activa a la vez (es un interruptor de estado, no rutas independientes), no hace falta un límite de carga por pantalla, uno solo basta para las 6. El resto de la app (login, catálogo, ficha de artículo) sigue cargando de golpe como siempre, sin ningún cambio para quien nunca toca Administración — que es, precisamente, a quien más beneficia este cambio.

**Verificación**: `npm run build` (Vite) muestra el resultado de un vistazo: el bundle principal baja de 255,59 KB (75,67 KB comprimido) a 180,10 KB (56,67 KB comprimido) — un 30% menos de JavaScript que descarga y ejecuta cualquier visita a la app, sea admin o no — y las 6 pantallas (más `ConfirmDialog.jsx`, compartido entre varias de ellas) pasan a ficheros propios de entre 0,57 KB y 39,92 KB, pedidos solo cuando hacen falta de verdad. Para comprobar que el comportamiento es correcto y no solo que el bundle es más pequeño, se hizo una prueba end-to-end real con Playwright contra el frontend real corriendo en modo demo — sin ningún mock de `api.js`, usando el propio login de demostración del proyecto (`admin@demo.dali`) — siguiendo las peticiones de red reales del navegador: confirmado que, antes de iniciar sesión, no se pide ningún módulo de administración; que, tras iniciar sesión como admin con el catálogo ya visible, TAMPOCO se pide ninguno todavía (ser admin no es suficiente por sí solo, hace falta entrar de verdad a una pantalla concreta); que cada una de las 6, al pulsar su pestaña en el menú, pide su propio módulo por red — y únicamente el suyo, de entre las que quedan por visitar — y muestra su título correctamente; que volver a una pantalla ya visitada no vuelve a pedir su módulo de nuevo; y que, tras haber visitado las 6, volver al catálogo principal sigue funcionando con total normalidad. Sin errores de consola en ningún momento de toda la sesión de prueba.

Documentos de mantenimiento revisados en esta entrega: `README.md`, `backend/README.md`, `frontend/README.md` — no aplica ningún cambio en ninguno.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.29** (backend sin cambios en esta versión — se sube igual para mantener sincronizados los dos `package.json`).

**Con esta entrega se da por completa la auditoría full de la aplicación DALI**, pedida por Víctor con el mismo criterio ya aplicado antes sobre Control de Pedidos: 11 etapas en total (v1.00 a v1.11 en esta lista), cubriendo desde paginación y límites sin techo en el backend hasta caché de peticiones repetidas, recargas de más y, por último, el tamaño del bundle del frontend — más dos correcciones fuera de turno (v1.04, v1.05) sobre incidencias reales que Víctor reportó en producción durante el propio proceso de auditoría, atendidas de inmediato por delante del orden previsto. Cada entrega, en su día, se verificó de forma independiente (pruebas funcionales contra mocks en memoria cuando bastaba, y pruebas end-to-end reales con Playwright — a veces contra el frontend real en modo demo, sin ningún mock — cuando el comportamiento a comprobar dependía de verdad del navegador) y se documentó por separado en `CHANGELOG.md` y aquí.

---

## v1.10 — Décima etapa de la auditoría full: la tabla de la carga masiva volvía a renderizar TODAS las filas por cada una que cambiaba (v1.19.28)

Último pendiente de peso de la lista de frontend: la tabla de resultados de `CargaMasivaModal.jsx` no estaba preparada para carpetas de verdad grandes — el propio archivo ya avisa en sus comentarios de carpetas de "miles de archivos", el caso que motivó `CONCURRENCIA_SUBIDA` (varios archivos subiéndose a la vez) y, en la sexta etapa de esta misma auditoría, reducir de dos peticiones a una por archivo.

**Diagnóstico**: `filas` es un único array de estado en `CargaMasivaModal`, con un elemento por archivo — con una carpeta de miles, un array de miles de elementos. Cada fila se pintaba inline, dentro de `filas.map(...)`, en el propio render del componente padre. El problema: `procesarFila` actualiza el estado de UNA fila varias veces mientras se procesa (marca "subiendo" al empezar, y el resultado final al terminar) — y cada una de esas actualizaciones de una sola fila volvía a renderizar el componente `CargaMasivaModal` ENTERO, lo que a su vez volvía a evaluar `filas.map(...)` y por tanto el JSX de TODAS las demás filas también, aunque su contenido no hubiera cambiado ni un poco. Con `CONCURRENCIA_SUBIDA` archivos subiéndose a la vez y miles de filas en la tabla, ese es trabajo de render que crece con el cuadrado del número de archivos: el doble de archivos no es el doble de trabajo, es cuatro veces más.

**Solución**: se extrae la fila de la tabla a su propio componente, `FilaCarga`, envuelto en `memo()` de React. La clave que hace esto seguro y realmente eficaz es que el propio patrón de actualización de `filas` YA estaba escrito de forma compatible, sin que hiciera falta cambiarlo: las cuatro llamadas a `setFilas` de `procesarFila` usan siempre `prev.map((f, idx) => (idx === i ? {...cambios} : f))` — para cualquier fila que NO sea la `i`-ésima, esa expresión devuelve la MISMA referencia `f` de antes, sin crear un objeto nuevo. `memo()` compara las props de cada `FilaCarga` por referencia entre un render y el siguiente: con la fila ya aislada en su propio componente, React ahora puede aprovechar esa referencia estable para saltarse por completo el render de cualquier fila cuyo objeto no haya cambiado, en vez de volver a evaluar su JSX solo porque OTRA fila cambió de estado. Al ser una fila de solo lectura (sin ningún botón, callback ni interacción propia), no hay ningún riesgo de que una función recién creada en cada render invalide esa comparación por accidente — el caso ideal para `memo()`.

**Verificación**: `npm run build` (Vite), limpio. Se repitió sin cambios la prueba end-to-end de la sexta etapa (comprobando `fetchInfoYHashDocumento`, casos normal/"en reserva"/error) para confirmar que extraer la fila a su propio componente no alteró ningún comportamiento visible — mismos resultados exactos. Para medir el ahorro real de renders se construyó una prueba nueva (arnés en `rerendertest/`) con una instrumentación temporal de conteo (un contador por nombre de archivo, retirado del código antes de esta entrega) sobre una carga real de 40 archivos, 40 artículos distintos: con `memo()` — el código de esta entrega — el total de renders de toda la tabla durante la carga completa fue 160 (4 por fila de media: montaje, "subiendo" y el resultado final, un margen pequeño y constante, igual sea cual sea el tamaño de la carpeta), sin que ninguna fila individual superase 5 renders. Para demostrar que el ahorro es de verdad cosa de `memo()` y no un efecto casual de haber movido el JSX a otra función, se quitó `memo()` a propósito (dejando la fila igual de aislada, solo sin memoizar) y se repitió exactamente la misma prueba: 1.000 renders en total para las mismas 40 filas, con una fila llegando a renderizarse 25 veces — más de 6 veces más trabajo de render para solo 40 archivos, una diferencia que crece con el cuadrado del número de archivos en una carga real de miles, no con el número de archivos en sí.

Documentos de mantenimiento revisados en esta entrega: `README.md`, `backend/README.md`, `frontend/README.md` — no aplica ningún cambio en ninguno.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.28** (backend sin cambios en esta versión — se sube igual para mantener sincronizados los dos `package.json`). Con esto quedan cerrados todos los pendientes de peso identificados en la auditoría full de esta app; el único pendiente restante (code-splitting del bundle del frontend) es de impacto menor y se deja para cuando el bundle crezca lo suficiente como para justificarlo — el bundle actual ronda los 255 KB (76 KB comprimido), lejos todavía de ser un problema real de carga.

---

## v1.09 — Novena etapa de la auditoría full: `EmailProveedorModal.jsx` se cerraba solo al seleccionar texto (v1.19.27)

Siguiente pendiente de la lista de frontend: `EmailProveedorModal.jsx` no usaba el hook compartido `useCerrarAlClicFuera`, ya adoptado en el resto de paneles con el mismo patrón "clic fuera para cerrar".

**Diagnóstico**: `useCerrarAlClicFuera` (`hooks/useCerrarAlClicFuera.js`) existe específicamente para un bug real ya documentado en su propio comentario: el navegador decide dónde ocurre un `click` según dónde se SUELTA el botón del ratón, no según dónde se pulsó — así que seleccionar texto arrastrando dentro de un panel y soltar el botón fuera de sus límites, aunque sea por un solo píxel, se registra como un clic en el fondo del modal. Con el cierre "ingenuo" (`onClick={onDismiss}` directo en el fondo), eso cierra el panel solo, sin que nadie pulsara nada a propósito. `ArticuloForm.jsx`, `CargaMasivaModal.jsx` y `UsuarioForm.jsx` ya usan el hook; `EmailProveedorModal.jsx` se había quedado con el patrón antiguo. Es, además, el sitio con más motivo real para sufrirlo: tiene un `<textarea>` de 12 filas (el cuerpo del correo a un proveedor, pensado para revisarse y ajustarse a mano antes de "Encolar envío") y un campo de asunto — contenido que de verdad se selecciona (para corregir una frase, copiar un fragmento, etc.), a diferencia de un simple mensaje de confirmación de una línea.

**Solución**: `EmailProveedorModal.jsx` pasa a usar `useCerrarAlClicFuera(onClose)` sobre el `.confirm-overlay`, exactamente igual que los demás paneles — un cambio de una línea de comportamiento (además de la línea de import), sin tocar el resto del modal.

**Verificación**: `npm run build` (Vite), limpio. Prueba end-to-end real con Playwright (arnés nuevo en `emailmodaltest/`, cargando la hoja de estilos real del proyecto para que el tamaño y la posición del panel en pantalla sean los de verdad, no los de un `<div>` sin estilos) que reproduce el bug con eventos de ratón REALES — `page.mouse.down`/`move`/`up`, no un `.click()` sintético de un solo punto — para que el navegador calcule el `click` resultante exactamente como lo haría con un usuario de verdad: `mousedown` dentro del `<textarea>`, varios movimientos intermedios simulando un arrastre de selección de texto, y `mouseup` en un punto claramente fuera del panel (viewport de 1200×900, panel centrado con fondo visible a los lados). Antes de dar el arreglo por bueno, se revirtió temporalmente el cambio y se volvió a correr la MISMA prueba contra el código antiguo: falló exactamente como se esperaba (el modal se cerraba solo), confirmando que la prueba detecta de verdad el bug real y no solo el síntoma que se recuerda de memoria. Con el arreglo aplicado, la misma prueba pasa: el modal no se cierra con ese arrastre. Como contraste, se comprobó también que un clic real que empieza y termina en el propio fondo (sin ningún arrastre) sigue cerrando el modal con normalidad — el hook corrige el caso de selección de texto sin dejar de cerrar el panel cuando de verdad se pulsa fuera.

Documentos de mantenimiento revisados en esta entrega: `README.md`, `backend/README.md`, `frontend/README.md` — no aplica ningún cambio en ninguno.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.27** (backend sin cambios en esta versión — se sube igual para mantener sincronizados los dos `package.json`). Nota aparte, no tocada en esta entrega: `ConfirmDialog.jsx` comparte el mismo patrón manual de cierre — en teoría la misma vulnerabilidad — pero su contenido es un mensaje corto de solo lectura, sin ningún campo editable, así que el riesgo real de dispararlo por accidente es mucho menor; queda anotado por si en el futuro algún `<ConfirmDialog>` pasa a mostrar contenido más largo o seleccionable. Pendientes de frontend que quedan por delante: re-renderizados innecesarios por fila en `CargaMasivaModal`, y ningún code-splitting en el bundle del frontend — ambos de impacto menor que lo ya resuelto en esta auditoría.

---

## v1.08 — Octava etapa de la auditoría full: guardar un código en `ArticuloForm.jsx` recargaba TODA la documentación del artículo (v1.19.26)

Siguiente pendiente de la lista de frontend: `ArticuloForm.jsx` recargaba de más tras cada guardado, no solo al abrir un artículo distinto (eso ya se corrigió indirectamente en v1.07, al cachear `fetchProveedores()`) — esta vez, dentro del propio panel de un artículo, cada una de sus 8 acciones (subir/borrar imagen o ficha, guardar código de proveedor o de marca, crear/borrar marca) volvía a pedir TODA la documentación del artículo tras completarse.

**Diagnóstico**: las 8 funciones de `ArticuloForm.jsx` que mutan algo (`subirImagenPara`, `subirFichaPara`, `guardarCodigoPara`, `crearMarcaPara`, `guardarCodigoMarca`, `subirImagenParaMarca`, `subirFichaParaMarca`, y el borrado unificado `handleConfirmarBorrar`) terminaban todas con `await cargarGrupos()` — una recarga completa de `GET /articulos/:id/fichas-por-proveedor`. Ese endpoint no es una simple consulta a la base de datos: por cada imagen y cada ficha YA GUARDADA de CUALQUIER proveedor de ese artículo, llama además a `supabase.storage.createSignedUrl()` para renovar su URL de descarga — un artículo con documentación de varios proveedores alternativos puede acumular fácilmente diez o más de esas llamadas a Storage en una sola recarga. El caso más llamativo: `guardarCodigoPara`/`guardarCodigoMarca` guardan un simple texto (el código con el que un proveedor o una de sus marcas identifica el artículo) — no tocan ninguna imagen, ficha ni URL — y aun así disparaban la misma recarga completa que subir una imagen nueva. Guardar el código de un proveedor es, además, probablemente la acción más repetida de esta pantalla en el día a día (introducir o corregir referencias cruzadas de proveedores), así que era también la que más veces pagaba ese coste de más sin necesitarlo.

**Solución**: `guardarCodigoPara` y `guardarCodigoMarca` dejan de llamar a `cargarGrupos()` — en su lugar, actualizan el estado local `grupos` con el valor que el backend acaba de confirmar (ambos endpoints ya devolvían `{ id_proveedor/id, codigo }`, justo lo necesario). Para `guardarCodigoPara` se cubre también el caso de un proveedor que todavía no tuviera ningún grupo (primera vez que se le guarda algo para este artículo, buscado desde el desplegable de "otro proveedor"): se crea en el sitio un grupo mínimo, con los mismos campos que construiría el propio backend para un proveedor con solo código (sin fichas, sin imagen, sin marcas) — usando datos ya disponibles en el propio componente (la lista de proveedores, ya cacheada desde v1.07). El resto de acciones (subir/borrar imagen o ficha, crear/borrar marca) siguen recargando con `cargarGrupos()` sin cambios — esas sí cambian de verdad una URL de Storage o crean/eliminan filas, así que ahí replicar la lógica del backend en el frontend sería mucho más arriesgado para un ahorro menor.

**Verificación**: `npm run build` (Vite), limpio. Prueba end-to-end real con Playwright del componente `ArticuloForm.jsx` aislado (mock de la API, sin backend real, arnés nuevo en `articuloformtest/`) con un dataset pensado para cubrir los 3 casos relevantes: un proveedor asignado con una marca extra ya guardada, un proveedor alternativo ya guardado, y un TERCER proveedor real sin ningún grupo todavía. Confirmado, paso a paso: guardar un código nuevo para el proveedor asignado (con grupo ya existente) no dispara ninguna llamada nueva a `fetchFichasPorProveedor`; guardar el código de la marca ya existente tampoco la dispara, y el texto de solo lectura de esa marca (fuera de su propio campo de edición, que no depende de ningún refresco) muestra el cambio de inmediato — la prueba de que `grupos` se actualizó de verdad, no solo el campo que se acababa de editar; y guardar el código de un proveedor SIN grupo previo (buscado desde cero, campo vacío al empezar) tampoco dispara ninguna recarga, y al dejar de buscar ese proveedor aparece ya remontado en la lista de "otros proveedores guardados", con el código correcto precargado en un campo recién montado — prueba de que el grupo nuevo quedó bien construido en el estado local, sin depender de ninguna respuesta de red para mostrarse bien. En las 3 mutaciones de la prueba, `fetchFichasPorProveedor` se llamó una única vez en total: la carga inicial del panel.

Documentos de mantenimiento revisados en esta entrega: `README.md`, `backend/README.md`, `frontend/README.md` — no aplica ningún cambio en ninguno.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.26** (backend sin cambios en esta versión — se sube igual para mantener sincronizados los dos `package.json`). Pendientes de frontend que quedan por delante: `EmailProveedorModal.jsx` sin `useCerrarAlClicFuera` (el hook ya existe y lo usa correctamente `CargaMasivaModal.jsx` — arreglo pequeño y ya acotado en cuanto se llegue a él), re-renderizados innecesarios por fila en `CargaMasivaModal`, y ningún code-splitting en el bundle del frontend.

---

## v1.07 — Séptima etapa de la auditoría full: `fetchProveedores()` sin caché, pedida de nuevo en 4 pantallas distintas (v1.19.25)

Se continúa con el siguiente pendiente de la lista de frontend: la lista de proveedores se pedía entera, sin ninguna caché, cada vez que se montaba cualquiera de los 4 sitios que la usan.

**Diagnóstico**: `AdminProveedores.jsx`, `AdminExportarZip.jsx` y `CargaMasivaModal.jsx` llaman a `fetchProveedores()` en su `useEffect` de montaje — cada apertura de la pantalla o del modal vuelve a pedir la lista completa, aunque no haya cambiado desde la última vez. El caso más repetido con diferencia es `ArticuloForm.jsx`: su `useEffect` tiene `[articulo.codigo_dali]` como dependencia, así que cada vez que el admin abre un artículo DISTINTO para editarlo — el flujo normal de trabajo, repetido decenas de veces seguidas al revisar el catálogo — se lanza una llamada nueva a `fetchProveedores()`, trayendo exactamente la misma lista de siempre. Dentro de esta app, la lista de proveedores solo cambia en un sitio: `fusionarProveedores()` (fusión de dos proveedores en uno, "Fusionar proveedores" en `AdminProveedores.jsx`), que borra uno de los dos de verdad; dar de alta un proveedor nuevo se hace directamente en Supabase, fuera de esta app. Es decir: un dato que en la práctica es fijo durante toda una sesión de trabajo, pedido una y otra vez.

**Solución**: caché en memoria a nivel de módulo dentro de `fetchProveedores()` (`services/api.js`). La primera llamada de la sesión hace la petición real y guarda el resultado; las siguientes devuelven una COPIA de esos datos ya guardados, sin ninguna petición HTTP — copia, no la misma referencia, para que ningún componente pueda mutar por accidente el array compartido en el futuro y afectar a los demás sin darse cuenta. Se añade también deduplicación de peticiones en vuelo: si dos componentes se montan casi a la vez (p. ej. al arrancar la app), comparten la misma petición real en curso en vez de lanzar dos por separado. Un fallo de red NO se cachea a propósito — el siguiente intento vuelve a pedir de verdad — para no dejar la aplicación atascada mostrando "sin proveedores" por un problema puntual de conexión. La caché se invalida ella sola, automáticamente, desde dentro de `fusionarProveedores()` justo tras un éxito — el único punto real de la app que cambia la lista —, así que `AdminProveedores.jsx` (que ya volvía a llamar a `fetchProveedores()` después de fusionar, para refrescar su propia tabla) recibe la lista fresca de verdad sin que haga falta cambiar nada en ese componente.

**Verificación**: `node --check` sobre `api.js`; `npm run build` (Vite), limpio. Al ser lógica pura del módulo `api.js` (no depende de renderizado de React ni del DOM), se verificó con una prueba funcional en Node puro, sin navegador: se mockeó `fetch` global con un contador de peticiones reales y se comprobó, paso a paso: que la primera llamada a `fetchProveedores()` hace exactamente 1 petición; que la 2ª y 3ª llamada no generan ninguna petición nueva y devuelven los mismos datos que la 1ª; que cada llamada devuelve una copia distinta del array (mutar el resultado de una llamada, a propósito en la prueba, no afecta a llamadas posteriores); que 3 llamadas lanzadas EN PARALELO antes de que la primera responda comparten una única petición real, no tres; que tras `fusionarProveedores()` la siguiente `fetchProveedores()` sí vuelve a pedir la lista de verdad (la caché se invalidó); y que un fallo de red simulado se propaga como error normal y NO queda cacheado — el intento siguiente hace una petición real nueva, en vez de repetir el mismo fallo indefinidamente.

Documentos de mantenimiento revisados en esta entrega: `README.md`, `backend/README.md`, `frontend/README.md` — no aplica ningún cambio en ninguno.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.25** (backend sin cambios en esta versión — se sube igual para mantener sincronizados los dos `package.json`). Pendientes de frontend que quedan por delante: recarga completa de `ArticuloForm.jsx` tras cada guardado, `EmailProveedorModal.jsx` sin `useCerrarAlClicFuera` (el hook ya existe y lo usa correctamente `CargaMasivaModal.jsx` — arreglo pequeño y ya acotado en cuanto se llegue a él), re-renderizados innecesarios por fila en `CargaMasivaModal`, y ningún code-splitting en el bundle del frontend.

---

## v1.06 — Sexta etapa de la auditoría full: carga masiva hacía dos peticiones por archivo, una de ellas innecesariamente pesada (v1.19.24)

Se retoma el orden normal de la auditoría full tras las dos correcciones fuera de turno (v1.04, v1.05). Siguiente pendiente de la lista de frontend: `subirParaCodigoDali()` (`CargaMasivaModal.jsx`), la función que decide, por cada archivo de una carga masiva, si subirlo o no.

**Diagnóstico**: por cada archivo, la función llamaba a dos endpoints por separado — `fetchArticulo(idArticulo)`, que trae la ficha COMPLETA del artículo con sus 4 tablas relacionadas vía join (pensada para `ArticuloDetail.jsx`, la pantalla de detalle de un artículo), solo para confirmar que existía y sacar su nombre y proveedor asignado; y `fetchHashDocumento()`, aparte, para el hash con el que decidir si el archivo ya está subido igual y evitar una subida redundante a Storage. Con una carpeta real de cientos de archivos (el caso normal de una carga masiva), eso es el doble de peticiones de las que hacen falta para una decisión que en realidad solo necesita 4 datos: nombre del artículo, hash ya existente, id del proveedor realmente asignado y su nombre. Egress y tiempo de más en cada carga, en una pantalla que se usa con frecuencia.

**Solución**: se amplía el endpoint que ya se usaba para el hash — `GET /admin/articulos/:codigoDali/documentos-hash` (`obtenerHashDocumento`, `storageController.js`) — para que devuelva también esos 3 campos que antes solo salían de `fetchArticulo`. Antes de tocarlo, se confirmó por grep que este endpoint SOLO lo usa `CargaMasivaModal.jsx` (a diferencia de `GET /articulos/:id`, que sigue intacto porque `ArticuloDetail.jsx` sí necesita la ficha completa) — así que ampliar su forma de respuesta es seguro, no rompe ningún otro llamador. En el frontend, `fetchHashDocumento` se sustituye por `fetchInfoYHashDocumento()` (`services/api.js`), y `subirParaCodigoDali()` pasa a hacer una única llamada a esa función (en paralelo con el cálculo del hash del archivo local, igual que antes, con `Promise.all`).

Un detalle de comportamiento que se documentó a propósito en el propio código, backend y frontend: la `fetchHashDocumento` anterior nunca lanzaba error — cualquier fallo se traducía en "sin hash, sube igual", para no bloquear la carga ante un problema de red puntual. La nueva `fetchInfoYHashDocumento` sí lanza ante cualquier fallo, porque ahora también confirma que el artículo existe — algo que antes garantizaba `fetchArticulo`, que SIEMPRE lanzaba si fallaba. Es un cambio de comportamiento deliberado: sin una llamada aparte que confirme la existencia del artículo, subir "a ciegas" ante un fallo de esta llamada sería menos seguro que antes, no más — así que se prefiere que la fila quede en error visible (como ya pasaba con un fallo de `fetchArticulo`) en vez de intentar una subida que podría ir a un artículo que ya no existe.

**Verificación**: `node --check` sobre los archivos de backend tocados; `npm run build` (Vite) del frontend, limpio; grep confirmando que no queda ninguna referencia viva a `fetchArticulo`/`fetchHashDocumento` en `CargaMasivaModal.jsx` (solo en comentarios históricos, a propósito, como registro de por qué cambió). Prueba funcional del backend contra un mock de Supabase en memoria, 4 casos: artículo normal con el proveedor asignado igual al que consulta, artículo "en reserva" (consultado con un proveedor DISTINTO al asignado — confirma que la respuesta siempre refleja la asignación REAL del artículo, no el proveedor de la consulta), artículo inexistente (404 con mensaje claro) y artículo sin hash todavía (sigue devolviendo el nombre igual). Prueba end-to-end real con Playwright sobre el componente `CargaMasivaModal.jsx` aislado (mock de la API, sin backend real, arnés nuevo en `cargamasivatest/`): simulada una selección de carpeta con 3 archivos de imagen de un proveedor de prueba — uno normal, uno "en reserva" de otro proveedor, y uno cuya consulta de info+hash falla a propósito (simulando un artículo borrado justo entre resolver el código de proveedor y consultar su info) — confirmado que los mensajes de cada fila son los esperados (nombre del artículo, aviso "en reserva" con el nombre real del proveedor asignado, mensaje de error claro en el caso fallido, sin que tumbe las otras dos filas ni el resto de la carga), que `subirImagenArticulo` solo se llama para los 2 artículos con info válida y nunca para el que falló, y — el objetivo real de este cambio — que se hace EXACTAMENTE una llamada a la nueva función combinada por archivo (3 archivos, 3 llamadas, con el `codigoDali`/`tipo`/`idProveedor` correctos en cada una), no dos como antes.

Documentos de mantenimiento revisados en esta entrega: `README.md`, `backend/README.md`, `frontend/README.md` — no aplica ningún cambio en ninguno.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.24**. Pendientes de frontend que quedan por delante, en el mismo orden ya establecido: `fetchProveedores()` sin caché entre varias pantallas de administración, recarga completa de `ArticuloForm.jsx` tras cada guardado, `EmailProveedorModal.jsx` sin `useCerrarAlClicFuera` (el hook ya existe y lo usa correctamente `CargaMasivaModal.jsx` — arreglo pequeño y ya acotado en cuanto se llegue a él), re-renderizados innecesarios por fila en `CargaMasivaModal`, y ningún code-splitting en el bundle del frontend.

---

## v1.05 — El diálogo de "Eliminar imágenes repetidas" se salía de la pantalla con un grupo grande (v1.19.23)

Corrección directa sobre v1.04, el mismo día: Víctor probó la herramienta nueva contra un proveedor real con 168 artículos afectados y reportó "no hace scrol y no puedo captar o cancelar la lista es amplia" — el diálogo de confirmación no cabía en la pantalla y no había forma de llegar a los botones.

**Causa**: el mensaje de confirmación enumeraba los 168 códigos DALI del grupo entero (pensado para grupos pequeños, como los 4 artículos de las pruebas) y `.confirm-box` — el cuadro genérico que usa `ConfirmDialog.jsx` en toda la aplicación, no solo aquí — no tenía ningún límite de altura ni scroll propio. Con un mensaje tan largo, el cuadro crecía sin tope y se salía del viewport, dejando "Cancelar"/"Sí, eliminar" fuera de la vista, inalcanzables sea cual sea el tamaño de la ventana.

**Arreglo, en dos partes**: primero, el mensaje de esta confirmación concreta ya no enumera los códigos — la tabla justo encima del botón ya los enseña todos, no hace falta repetirlos dentro del propio diálogo, así que ahora solo dice la cantidad ("Se eliminará la imagen de 168 artículo(s) — revisa la lista en la tabla de arriba"). Segundo, y más importante a largo plazo: `.confirm-box` lleva ahora `max-height: 90vh` + `overflow-y: auto` (el mismo criterio que ya llevaba `.email-modal-box`, la variante ancha de este mismo diálogo, usada en el email de "Documentación faltante") — así que si en el futuro cualquier otro `<ConfirmDialog>` de la aplicación recibe un mensaje largo, se desplaza en vez de desbordar la pantalla, sin depender de que cada sitio que lo use recuerde mantener su mensaje corto.

**Verificación**: `npm run build` (Vite), limpio. Prueba end-to-end con Playwright reproduciendo el caso real: un grupo de 168 artículos, con el viewport del navegador reducido a propósito (1000×500, para forzar el mismo desbordamiento que vivió Víctor) — confirmado que el mensaje ya no lleva ningún código DALI individual, que el cuadro entero cabe dentro de esos 500px de alto (113px de altura real), y que el botón "Sí, eliminar" es visible y CLICKABLE de verdad: Playwright rechaza el `click()` si el elemento está tapado o fuera de la vista, así que un clic que funciona y dispara la llamada correcta al backend es la prueba de que es alcanzable, no solo una suposición visual. Repetida también la prueba end-to-end del grupo pequeño de v1.04 para confirmar que sigue funcionando igual.

Documentos de mantenimiento revisados en esta entrega: `README.md`, `backend/README.md`, `frontend/README.md` — no aplica ningún cambio en ninguno.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.23** (backend sin cambios en esta versión — se sube igual para mantener sincronizados los dos `package.json`).

---

## v1.04 — Reparar imágenes "SIN IMAGEN" antiguas subidas antes de que existiera `es_generica` (v1.19.22)

Víctor reportó un problema real con un proveedor concreto, fuera del orden de la auditoría (se atiende antes de continuar con los pendientes de frontend, por ser un bloqueo activo): "un proveedor en concreto tenia imagen generica en todas sus referencias pero la quite antes de la actualizacion realizada para este efecto, entonces se han quedado unas imagenes en archivos erronea y cuando pongo el archivo SIN IMAGEN estos DALI no aplican la nueva SIN IMAGEN".

**Diagnóstico**: la imagen de reserva "SIN IMAGEN" de v0.98 se distingue de una foto propia por la columna `imagenes.es_generica`, grabada explícitamente por `subirImagenArticulo` desde la migración `2026-09-01_es_generica_imagen.sql`. Antes de esa fecha, la "SIN IMAGEN" de un proveedor se subía por la vía normal de siempre, igual que cualquier foto propia — sin nada que la distinguiera en la base de datos. El proveedor de Víctor tenía la genérica antigua asignada a TODAS sus referencias, subida ANTES de esa migración; al quitar el archivo "SIN IMAGEN" viejo de su carpeta, esas filas de `imagenes` se quedaron huérfanas, indistinguibles de fotos propias reales (`es_generica = false`, el valor por defecto). Efecto en cadena: `GET /admin/documentacion-faltante` calcula "le falta la imagen" simplemente comprobando si existe una fila en `imagenes` para ese artículo/proveedor — como sí existe (aunque sea la genérica vieja mal etiquetada), esos artículos nunca salen como `falta_imagen: true`; y `calcularFilasFallback()` (`CargaMasivaModal.jsx`), que es quien reparte la "SIN IMAGEN" nueva a los artículos sin foto, solo mira exactamente esa lista. Resultado: por muchas veces que Víctor suba el archivo "SIN IMAGEN" correcto, nunca llega a esos artículos — ya "tienen imagen" a ojos del sistema.

**Solución**: nueva herramienta en Administración → "Fusionar proveedores" (sección añadida al final de esa misma pantalla): "Reparar imágenes antiguas sin marcar como genéricas". Dos endpoints nuevos, mismo patrón que `listarProveedoresConImagenGenerica`/`eliminarImagenGenericaProveedor` (v0.98, previsualizar antes de borrar): `GET /admin/proveedores/:id/imagenes-repetidas` agrupa, para el proveedor elegido, las imágenes `es_generica = false` que comparten EXACTAMENTE el mismo hash entre 2 o más artículos activos suyos — mismo criterio de hash compartido que ya usaba "Documentación faltante" para su aviso informativo (`imagen_generica`), aquí reaprovechado como herramienta de limpieza real: dos fotos de artículos DISTINTOS con el archivo idéntico byte a byte son, en la práctica, siempre la misma imagen subida varias veces, nunca una coincidencia. El admin ve los artículos de cada grupo (código DALI y nombre) antes de decidir; `DELETE /admin/proveedores/:id/imagenes-repetidas` (con el hash del grupo confirmado) borra esas filas, Storage + tabla. Los artículos afectados vuelven a aparecer como "sin imagen" — la siguiente carga masiva con la "SIN IMAGEN" correcta en la carpeta del proveedor ya se la asigna, esta vez marcada `es_generica = true` desde el principio, así que este problema concreto no debería volver a darse para esas filas.

**Verificación**: `node --check` sobre los archivos de backend tocados (`storageController.js`, `routes/admin.js`); `npm run build` (Vite) del frontend, limpio. Prueba funcional contra un mock de Supabase en memoria con un dataset pensado para cubrir los casos límite: 4 artículos activos con el hash de la genérica vieja (el caso real de Víctor), 1 artículo con foto propia real de hash único (no debe entrar en ningún grupo — una foto legítima nunca debe borrarse por error), 1 artículo YA DADO DE BAJA que también comparte el hash (no cuenta en el listado que ve el admin, pero sí se limpia de paso al borrar el grupo, sin que eso afecte a nada visible), una fila de OTRO proveedor con el mismo hash exacto (nunca debe tocarse, aislamiento por proveedor confirmado) y una fila YA marcada `es_generica = true` del mismo proveedor (la gestiona el flujo existente de v0.98, no debe aparecer duplicada aquí). Confirmado: el listado detecta exactamente 1 grupo con los 4 artículos activos correctos; el borrado elimina las 5 filas reales (4 activas + 1 de baja) sin tocar la foto propia real, la fila ya marcada, ni la del otro proveedor; tras borrar, el listado ya no detecta ningún grupo para ese proveedor. Prueba end-to-end con Playwright del componente `AdminProveedores.jsx` aislado (mock de la API, sin backend real): buscar el proveedor con grupos muestra la tabla con los códigos DALI y la cantidad correctos, "Eliminar este grupo" abre el diálogo de confirmación con los códigos afectados SIN llamar todavía al backend, confirmar llama con el id de proveedor y el hash correctos y el grupo desaparece de la tabla con el aviso de éxito, y un proveedor sin grupos repetidos muestra el aviso de "nada que reparar" en vez de una tabla vacía ambigua.

Documentos de mantenimiento revisados en esta entrega: `README.md`, `backend/README.md`, `frontend/README.md` — no aplica ningún cambio en ninguno.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.22**. Se retoma a continuación el orden normal de la auditoría full, con los pendientes de frontend (peticiones redundantes de la carga masiva, caché de proveedores entre pantallas, recarga completa de `ArticuloForm.jsx` tras cada guardado, etc.) salvo que Víctor indique lo contrario.

---

## v1.03 — Cuarta etapa de la auditoría full: exportar PDF/Excel del catálogo bloqueaba el único hilo del proceso Node (v1.19.21)

Continuación directa de v1.02, siguiendo el orden de impacto acordado con Víctor tras presentarle todos los hallazgos de la auditoría — este era el último pendiente de impacto alto en backend.

**El problema.** `GET /export/pdf` y `GET /export/excel` (`exportController.js`) generaban el documento entero directamente en el hilo principal, dentro de la propia petición HTTP: para el PDF, un `doc.pipe(res)` con `doc.text()`/`doc.rect()` fila a fila; para el Excel, `sheet.addRow()` fila a fila. Con el catálogo completo (hasta ~30.000 artículos si un admin marca "incluir no activos" sin ningún filtro), eso es trabajo JS puramente síncrono y proporcional al número de filas. El plan gratuito de Render en el que corre DALI es un único proceso Node con un único hilo (sin cluster ni PM2, confirmado ya en la auditoría inicial) — mientras ese trabajo dura, el proceso no puede atender ninguna otra petición, ni de otros usuarios ni del propio health check de Render. Es exactamente el mismo problema ya diagnosticado y corregido para la IMPORTACIÓN de Excel en v1.15.2 (`parsearExcelWorker.js`, ver esa entrada más abajo): entonces fue el sondeo de progreso el que se quedaba sin respuesta; aquí sería cualquier otra pantalla o usuario mientras alguien exporta el catálogo completo.

**La solución**: el mismo patrón que ya funciona para la importación, aplicado a la exportación. Nuevo `workers/generarExportWorker.js`: recibe los artículos ya resueltos contra Supabase (sin cliente de Supabase ni `req` dentro del hilo — no hacen falta ahí), construye el PDF o el Excel COMPLETO en memoria (un buffer) dentro de ese hilo aparte, y lo devuelve por `postMessage`. `exportarPdf`/`exportarExcel` en `exportController.js` ahora solo esperan ese buffer y hacen `res.end(buffer)` — un único `write` de golpe, en vez de miles de operaciones de dibujado síncronas en el hilo de la petición. `columnasPdf()` y `nombreGrupo()` quedan duplicadas en el worker (mismo criterio ya usado en el propio `exportController.js` para `obtenerCodigosProveedorPorArticulos`/`limpiarParaFiltroOr`: no cruzar imports entre `controllers/` y `workers/` por funciones puntuales — si cambian las columnas del export hay que tocar los dos sitios).

**Verificación**: `node --check` sobre los tres archivos tocados (`exportController.js`, `workers/generarExportWorker.js`, y un comentario en `storageController.js` que señalaba la ubicación anterior de `nombreGrupo()`, actualizado). Prueba end-to-end REAL — sin mocks, con `pdfkit`/`exceljs` de verdad — contra un catálogo sintético de 3000 artículos: PDF y Excel generados son ficheros válidos (cabecera `%PDF-` y cabecera ZIP/`PK` respectivamente), y lo importante — un `setInterval` de 5ms en el hilo principal siguió disparando con normalidad (364 tics) mientras el worker generaba ambos documentos en paralelo (~2 segundos), confirmando que el hilo principal queda libre. Prueba de contraste aparte, para verificar que la medición anterior es representativa: un bucle síncrono puro de la misma duración en el hilo principal deja ese mismo `setInterval` completamente congelado (0 tics) — así se ve, medido, el tipo de bloqueo que tenía el código antes de este cambio. Pruebas adicionales con solo 5 artículos (usuario no admin, columna "Cantidad" en blanco) y con un tipo de exportación desconocido (confirma que el worker rechaza limpiamente con un mensaje claro en vez de colgarse).

Documentos de mantenimiento revisados en esta entrega: `README.md`, `backend/README.md`, `frontend/README.md` — no aplica ningún cambio en ninguno.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.21** (frontend sin cambios en esta versión — se sube igual para mantener sincronizados los dos `package.json`). Con esto quedan cerrados todos los hallazgos de impacto ALTO de backend de la auditoría full. Queda pendiente, de impacto menor por tener un volumen de filas mucho más acotado (solo artículos con documentación incompleta, no el catálogo completo): el mismo tipo de trabajo síncrono en `exportarDocumentacionFaltanteExcel()` (`documentacionController.js`) — deliberadamente no tocado en esta etapa, anotado por si el volumen de esa pantalla creciera lo suficiente en el futuro. Para las siguientes etapas, ya solo queda frontend: peticiones redundantes de la carga masiva, caché de proveedores entre pantallas, recarga completa de `ArticuloForm.jsx` tras cada guardado, `EmailProveedorModal.jsx` sin cerrar al clic fuera, re-renders innecesarios en la carga masiva y ausencia de code-splitting.

---

## v1.02 — Tercera etapa de la auditoría full: "Documentación faltante" traía imagenes/fichas/codigos_proveedor completas sin filtrar (v1.19.20)

Continuación directa de v1.01, siguiendo el orden de impacto acordado con Víctor tras presentarle todos los hallazgos de la auditoría.

**"Documentación faltante" traía las tres tablas de detalle completas y sin filtrar, incluyendo artículos dados de baja.** `calcularDocumentacionFaltante()` (usada tanto por `GET /admin/documentacion-faltante` como por su exportación a Excel) ya paginaba correctamente `imagenes`, `fichas` y `codigos_proveedor` en tandas de 1000 vía `.range()` — no había riesgo de truncado silencioso ahí — pero sin ningún filtro: traía cada tabla entera, mientras que el resto de la función solo recorre artículos ACTIVOS (`activo_dali` y `activo_general`) al calcular qué le falta a cada uno. Cuanto más crecen esas tres tablas con el tiempo, más egress de más para una pantalla que Víctor abre varias veces al día. Nueva función `traerPorArticulos()` en `documentacionController.js`: filtra por los ids de los artículos activos, troceados en lotes de 500 (mismo patrón que `obtenerCodigosProveedorPorArticulos` en `articulosController.js`, para no meter un segundo criterio de troceo en el proyecto) en vez de traer cada tabla entera.

**Efecto secundario menor, documentado en el propio código:** el conteo de "imágenes con el mismo hash compartidas entre varios artículos del proveedor" (señal de reserva para detectar la imagen genérica en filas antiguas, previas a la columna `es_generica` de v0.98) ahora solo compara entre artículos activos entre sí — si una fila antigua compartía hash únicamente con un artículo ya dado de baja, deja de detectarse como "genérica" por esta vía. Alcance deliberadamente acotado: solo afecta al aviso informativo de qué imágenes son genéricas en datos anteriores a la migración `2026-09-01_es_generica_imagen.sql`; no afecta en ningún caso a si falta o no la imagen (`falta_imagen`), que sigue siendo exacto.

**Verificación**: `node --check` sobre `documentacionController.js`. Prueba funcional contra un mock de Supabase en memoria con 3 artículos activos (uno completo, uno sin ficha de seguridad, uno sin nada) y 1 artículo dado de baja con imagen/ficha/código propios (para poder detectar si llegaban a consultarse): confirmado que el resultado de "qué le falta a cada artículo" es idéntico al que daba la versión anterior, que el artículo dado de baja nunca aparece en el resultado, y — el objetivo real del cambio — que ninguna de las tres consultas incluye su id en el filtro `.in()`, con el total de filas realmente transferidas coincidiendo exactamente con las de los artículos activos (6 de 9 posibles, nunca las del artículo de baja). Prueba aparte del troceo en lotes de 500 ids con 1200 ids simulados, confirmando 3 lotes (500/500/200). Sin acceso a Supabase real desde este entorno, es la validación más cercana posible sin desplegar.

Documentos de mantenimiento revisados en esta entrega: `README.md`, `backend/README.md`, `frontend/README.md` — no aplica ningún cambio en ninguno.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.20** (frontend sin cambios en esta versión — se sube igual para mantener sincronizados los dos `package.json`). Quedan pendientes, para las siguientes etapas: en backend, la exportación de PDF/Excel bloqueando el hilo único de Node; en frontend, las peticiones redundantes de la carga masiva, la caché de proveedores entre pantallas, y la recarga completa de `ArticuloForm.jsx` tras cada guardado — ninguna de las etapas 1-3 ha tocado frontend salvo la paginación de `AdminArticulos.jsx` en la primera.

---

## v1.01 — Segunda etapa de la auditoría full: `pageSize` sin tope en `GET /articulos` y llamadas a Control de Pedidos sin timeout (v1.19.19)

Continuación directa de v1.00, siguiendo el orden de impacto acordado con Víctor tras presentarle todos los hallazgos de la auditoría.

**1. `GET /articulos` sin techo en `pageSize`.** El endpoint es público (solo pasa por `optionalAuth`) y `pageSize` llegaba del query string sin ningún límite superior — el frontend real siempre pide 100 (`App.jsx`/`AdminArticulos.jsx`), pero nada impedía que una petición directa a la API pidiera, por ejemplo, `pageSize=100000`: el troceo interno en tandas de 1000 (pensado solo para sortear el límite de PostgREST, no como protección) seguiría hasta agotar el catálogo activo completo, sin ningún rate limiting en el proyecto. Se añadió un techo de 3000 (`MAX_PAGE_SIZE`, el mismo valor que ya era el `pageSize` por defecto) — no cambia nada para ningún llamador legítimo actual, solo pone límite a un valor que antes no lo tenía. `articulosController.js`.

**2. Llamadas a Control de Pedidos sin timeout.** Las tres llamadas salientes de `controlPedidosEmailBridge.js` (encolar email de "Documentación faltante", traer proveedores, traer compradores) no tenían ningún límite de tiempo — si `control-pedidos-princess` o su proxy de Cloudflare tardaban o no respondían, la petición de DALI se quedaba colgada indefinidamente en vez de fallar rápido. Estas llamadas están en el camino de `GET /admin/documentacion-faltante`. Se añadió `AbortSignal.timeout(15000)` (nativo desde Node 18) a las tres, con un mensaje claro cuando salta.

**Verificación**: `node --check` sobre los dos archivos tocados. Prueba unitaria del cálculo de `pageSize` contra los mismos casos que usa el código (sin valor, 100, 3000, 100000, "100000" como texto, 1), confirmando que nunca supera 3000. Para el timeout, prueba real contra un servidor HTTP local que nunca responde, con el mismo mecanismo (`AbortSignal.timeout`) que llevan las tres funciones reales: confirmado que el `fetch` se aborta exactamente al cumplirse el plazo (ni antes ni se cuelga) y lanza el mensaje esperado.

Documentos de mantenimiento revisados en esta entrega: `README.md`, `backend/README.md`, `frontend/README.md` — no aplica ningún cambio en ninguno.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.19** (frontend sin cambios en esta versión — se sube igual para mantener sincronizados los dos `package.json`). Quedan pendientes, para las siguientes etapas: en backend, el egress de "Documentación faltante" (trae `imagenes`/`fichas`/`codigos_proveedor` completas sin filtrar) y la exportación de PDF/Excel bloqueando el hilo único de Node; en frontend, las peticiones redundantes de la carga masiva, la caché de proveedores entre pantallas, y la recarga completa de `ArticuloForm.jsx` tras cada guardado.

---

## v1.00 — Primera etapa de la auditoría full: zip de backup truncado en silencio y Administración → Artículos sin paginar (v1.19.18)

Víctor pidió expresamente aplicar la misma operación de auditoría full que ya se hizo sobre Control de Pedidos a esta aplicación DALI ("PODEMOS REALIZAR LA MISMA OPERACION DE AUDITORIA FULL CON ESTA APLICACION AHORA?"), con el mismo criterio de entrega por etapas y el mismo cuidado por el consumo de egress de Supabase. Se hizo una auditoría completa de backend (Node/Express/Supabase) y frontend (React/Vite) por separado, presentando los hallazgos a Víctor antes de tocar nada — confirmó seguir con los dos de impacto alto que eran bugs de fiabilidad reales, no solo de rendimiento.

**1. Zip de backup de documentación truncado en silencio.** `GET /admin/documentacion-zip` (endpoint pensado como copia de seguridad externa completa, ver v0.94) leía `fichas`, `imagenes` y `codigos_proveedor` sin paginar, a diferencia de prácticamente el resto del backend, que sí respeta el límite de 1000 filas por petición que impone PostgREST/Supabase sin avisar. Con el volumen actual de esas tres tablas es probable que ya se estuviera superando ese límite al exportar "Todos" los proveedores de una vez — el zip se generaba con éxito (código 200, archivo descargado) pero le faltaban archivos, sin ningún aviso de que el backup estaba incompleto. Es el peor tipo de fallo posible para una función de backup: parece que funciona. Arreglado reutilizando el mismo helper `traerTodo()` (paginación en tandas de 1000 vía `.range()`) que ya existía en `proveedoresController.js` para "Fusionar proveedores" — `exportZipController.js`.

**2. Administración → Artículos sin paginación real.** El contador de la cabecera ya mostraba el total real de fichas (p.ej. varios miles), pero la tabla en sí solo traía los primeros 100 resultados del orden del backend, sin ningún control para ver el resto — a diferencia del catálogo principal (`App.jsx`), que sí pagina. Con ~30.000 artículos en el catálogo completo, un artículo que no apareciera entre esos primeros 100 al entrar sin buscar nada era, a efectos prácticos, invisible desde esta pantalla salvo que se supiera su código o nombre exacto para buscarlo. Se añadió a `AdminArticulos.jsx` la misma paginación que ya usa `App.jsx` (100 por página, botones "← Anterior"/"Siguiente →", indicador "página X de Y", vuelta automática a la página 1 si una búsqueda deja la página actual fuera de rango) — mismo patrón y mismos nombres de variable a propósito, para no introducir un segundo criterio de paginación en el proyecto.

**Verificación**: `node --check` sobre `exportZipController.js`. Para la paginación del zip, prueba unitaria aislada del helper `traerTodo()` contra un dataset simulado (2500, 1000 exactas, 500 y 0 filas), confirmando el número exacto de tandas de `.range()` en cada caso y que ya no se trunca a 1000 — sin acceso a Supabase real desde este entorno, es la validación más cercana posible a "más de 1000 filas de verdad" sin desplegar. Para la paginación de `AdminArticulos.jsx`: `npm run build` (Vite) del frontend completo sin errores, y una verificación end-to-end con Playwright montando el componente de forma aislada (mock de `fetchArticulos` con 250 artículos de prueba repartidos en 3 páginas de 100/100/50) — confirmado: el contador muestra el total real y "página X de Y", "Anterior"/"Siguiente" se deshabilitan correctamente en los extremos, cada página trae artículos distintos entre sí, y escribir en el buscador estando en la página 2 vuelve sola a la página 1 en vez de dejar la tabla vacía por estar fuera de rango. El flujo del zip contra Supabase real, con más de 1000 filas de verdad en alguna de las tres tablas, queda por confirmar en el propio Render de Víctor.

Documentos de mantenimiento revisados en esta entrega: `README.md` (no aplica ningún cambio), `backend/README.md`/`frontend/README.md` (secciones "Pendiente / siguientes pasos" revisadas, no aplica ningún cambio).

Versión: `backend/package.json` y `frontend/package.json` → **1.19.18**. Quedan pendientes, para las siguientes etapas de esta misma auditoría (backend: egress de "Documentación faltante", `pageSize` sin tope en `GET /articulos`, timeouts en las llamadas a Control de Pedidos, exportación de PDF/Excel bloqueando el hilo único de Node; frontend: peticiones redundantes de carga masiva, caché de proveedores entre pantallas, recarga completa de `ArticuloForm.jsx` tras cada guardado, y el resto de hallazgos de impacto medio/bajo ya reportados a Víctor).

---

## v0.99 — El proceso del backend se caía entero por una excepción sin capturar (v1.19.17)

Nada más desplegar v1.19.16, Víctor reportó que al guardar el código de proveedor en la ficha de un artículo, la app "se reiniciaba como si fuera un deploy nuevo" en Render — con capturas del panel mostrando "Failed to fetch" en el guardado, y más tarde, con las herramientas de desarrollador abiertas, un 502 concreto en `GET /articulos/:id/fichas-por-proveedor` justo después de que el guardado del código respondiera 200. Se descartaron por el camino, con evidencia, dos sospechas iniciales: el cron de keep-alive de cron-job.org (ejecuciones en verde, cada 8 minutos) y el plan gratuito de Render durmiéndose (el fallo era determinista, siempre en esa misma acción, no aleatorio).

**Causa real**: `obtenerFichasPorProveedor` (`articulosController.js`) llama a `cargarMarcasPorArticulo` (`marcasProveedorController.js`, de v0.97) dentro de un `Promise.all`, sin ningún `try/catch` en ningún punto de la cadena. Si esa consulta lanza — el caso más probable en el momento del incidente: la migración `2026-08-31_marcas_proveedor.sql` de v0.97 todavía no estaba aplicada en el Supabase de Víctor, así que la tabla `marcas_proveedor` no existía — la excepción queda como "unhandled promise rejection". Node, desde la v15, **termina el proceso entero** por defecto ante esto (no lo convierte en una respuesta 500, como sí hace Express con un error síncrono dentro de una ruta). Render reinicia el proceso caído automáticamente, lo cual se ve desde fuera exactamente igual que un deploy nuevo — y como `ArticuloForm.jsx` llama a `fichas-por-proveedor` (`cargarGrupos`) justo después de cada guardado de código de proveedor, la app se caía cada vez que se usaba esa acción, para TODOS los usuarios conectados en ese momento, no solo para quien la disparó.

**Cambio**: `obtenerFichasPorProveedor` envuelto en su propio `try/catch` — un fallo ahí pasa a ser un 500 normal para esa única petición, nunca tumba nada más. Como red de seguridad adicional, por si algún otro controlador tuviera el mismo problema hoy o en el futuro, `process.on("unhandledRejection", ...)` en `server.js` registra el error en vez de dejar que Node mate el proceso.

Confirmado con Víctor, paso a paso, que las migraciones `2026-08-31_marcas_proveedor.sql` y `2026-09-01_es_generica_imagen.sql` (de v0.98) ya estaban ambas aplicadas en su Supabase — con esas tablas ya existiendo, el fallo original desapareció por completo, y el `try/catch` queda como blindaje para el futuro, no como parche del síntoma.

**Verificación**: `node --check` sobre `articulosController.js` y `server.js`; arranque real del servidor con variables de entorno de prueba (`SUPABASE_URL`/`SUPABASE_SERVICE_ROLE_KEY` dummy) para confirmar que sigue levantando sin errores. Confirmado por Víctor en Render, ya en producción: el guardado del código de proveedor funciona sin cortes ni reinicios.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.17** (frontend sin cambios en esta versión — se sube igual para mantener sincronizados los dos `package.json`).

---

## v0.98 — Baja automática de la imagen genérica cuando "SIN IMAGEN" desaparece de la carpeta del proveedor (v1.19.16)

Víctor: "en la carga masiva de imágenes, si la imagen genérica 'SIN IMAGEN' desaparece de la carpeta de IMAGENES, se debe eliminar también en supabase y todos los artículos de ese proveedor dejar de ver esa imagen genérica". La carga masiva ya sabía subir "SIN IMAGEN" como imagen de reserva para los artículos de un proveedor que no tuvieran foto propia (funcionalidad previa, sin entrada propia en este historial); lo que faltaba era el camino inverso.

**El problema de fondo**: nada marcaba de forma explícita qué filas de `imagenes` eran esa genérica de reserva y cuáles eran fotos propias de un artículo. `documentacionController.js` (sección "Documentación faltante") lo inferÍa comparando hashes entre artículos del mismo proveedor — una heurística útil ahí, pero no fiable para borrar: un proveedor con un solo artículo sin foto propia genera un hash que aparece una sola vez, indistinguible de una foto real.

**Diseño**: columna nueva `imagenes.es_generica` (migración `2026-09-01_es_generica_imagen.sql`), grabada explícitamente por `subirImagenArticulo` cuando la sube la carga masiva de fallback — ya no hace falta inferir nada. Endpoint nuevo `DELETE /admin/proveedores/:id/imagen-generica` borra, Storage + tabla, todas las filas marcadas `es_generica = true` de ese proveedor — los artículos afectados no necesitan ningún otro cambio: al no quedarles ninguna imagen para ese proveedor, vuelven a aparecer como "sin imagen" sin más. `CargaMasivaModal.jsx` detecta, al elegir la carpeta, qué proveedores tenían su carpeta IMAGENES explorada en esta pasada pero ya no traen "SIN IMAGEN", avisa de ello, y dispara el borrado al pulsar "Subir".

**Corrección el mismo día**: Víctor confirmó que un caso límite ya anotado en el propio código ocurre de verdad — si la carpeta IMAGENES de un proveedor solo contenía "SIN IMAGEN" y ese archivo se borra sin dejar ninguna foto propia detrás, la carpeta queda completamente vacía, y el selector de carpeta del navegador (`webkitdirectory`) no ve directorios vacíos, solo archivos — la detección original no veía nada de ese proveedor y la genérica se quedaba huérfana. Se resolvió desde el otro lado: endpoint nuevo `GET /admin/proveedores/con-imagen-generica` (`listarProveedoresConImagenGenerica`) dice, consultando la BD directamente, qué proveedores tienen una genérica guardada AHORA MISMO — ya no hace falta verla desaparecer del árbol de archivos. `CargaMasivaModal.jsx` combina esa lista con una señal más amplia (`proveedoresEnCarpeta`: cualquier archivo del proveedor en el árbol elegido, no solo de imágenes — también cuentan fichas) y con el filtro manual de un único proveedor (cubre el caso extremo de una carpeta de proveedor totalmente vacía, sin ni siquiera fichas).

**Verificación**: `node --check` sobre los archivos de backend tocados; `npm run build` (Vite) sin errores sobre el frontend completo. El flujo completo contra Supabase (migración, subida marcando `es_generica`, y borrado real al retirar "SIN IMAGEN" de una carpeta) se verificó por primera vez en el Render de Víctor.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.16**.

---

## v0.97 — Un mismo proveedor puede tener varias marcas del mismo DALI (v1.19.15)

Víctor volvió a Catálogo DALI tras varias entregas seguidas en Control de Pedidos, con dos capturas del panel "Proveedor asignado — CADELSA" de un artículo (código de proveedor, imagen, ficha técnica, ficha de seguridad, y la sección "Añadir o gestionar otro proveedor"): "un mismo dali puede tener varios codigos de proveedores, pero un mismo proveedor tambien puede tener varios codigo proveedor en un mismo dali, por ejemplo, si el proveedor CADELSA nos suministra arroz vaporizado, pero tiene varias marcas a parte de la asignada, tambien deberia poder guardar la info de estas otras marcas por seguridad y control de las fichas e imagenes".

Lo primero que pedía (varios proveedores por un mismo DALI) ya existía — es la lista de "alternativas" que ya se ve en ese mismo panel, con su propio código/imagen/fichas por proveedor (`codigos_proveedor`/`imagenes`/`fichas`, todas con un `unique (id_articulo, id_proveedor)` de fondo). Lo segundo — que el MISMO proveedor pudiera tener más de una referencia para el mismo artículo — era nuevo: esas tres tablas no admiten más de una fila por (artículo, proveedor), así que hoy no había dónde guardar una segunda marca de CADELSA sin pisar la primera.

Antes de tocar el esquema se le preguntó a Víctor por dos decisiones de diseño: (1) si cada marca necesitaba un nombre/etiqueta propio además del código, o bastaba con el código para distinguirlas — eligió que bastara con el código, sin campo de nombre aparte; (2) si la carga masiva por carpetas tenía que soportar ya varias marcas del mismo proveedor, o si podía quedarse solo en alta manual por ahora — eligió alta manual por ahora, dejando la carga masiva para una entrega futura si hace falta.

**Diseño**: tres tablas nuevas y separadas de las "principales" (`marcas_proveedor`, `marcas_proveedor_imagenes`, `marcas_proveedor_fichas` — ver migración `database/migraciones/2026-08-31_marcas_proveedor.sql`), en vez de tocar los `unique` existentes de `codigos_proveedor`/`imagenes`/`fichas`. Decisión deliberada: así ninguna consulta que ya existía (documentación faltante, exportación a Excel, exportación a zip, carga masiva de imágenes/fichas/código de proveedor) cambia de comportamiento ni necesita revisarse — todas ellas siguen viendo exactamente una fila por (artículo, proveedor), que sigue siendo LA referencia de ese proveedor para ese artículo. Las marcas extra son estrictamente un añadido de reserva ("por seguridad y control", como pidió Víctor), nunca sustituyen a esa referencia ni participan en los cálculos de qué falta por subir.

**Backend**: `marcasProveedorController.js` (nuevo) — alta/borrado de una marca, guardar su código, subir/borrar su imagen y sus fichas técnica/seguridad, todo igual de estricto que `storageController.js` (mismos límites de tamaño 5MB/20MB, mismo hash SHA-256 para saltar subidas idénticas, mismas rutas privadas con URL firmada de 24h) pero en su propia carpeta de Storage (`marcas-proveedor/<id>...`) para no arriesgar ninguna colisión con las rutas ya existentes. `obtenerFichasPorProveedor` (`articulosController.js`) incrusta ahora un array `marcas` en cada grupo de proveedor que ya devolvía, para que `ArticuloForm.jsx` las muestre sin tener que hacer una consulta aparte.

**El detalle que casi se cuela**: `marcas_proveedor.id_proveedor` referencia `proveedores(id) on delete cascade` — al revisar `fusionarProveedores` (`proveedoresController.js`, la pantalla "Fusionar proveedores" que traslada todo lo de un proveedor duplicado a otro y borra el de origen) se vio que, sin más cambios, fusionar un proveedor con marcas extra habría borrado esas marcas en silencio al borrar el proveedor de origen al final de la fusión — justo la documentación que esta funcionalidad existe para proteger. Se añadió un paso más a la fusión (mismo criterio que ya usa para `codigos_proveedor`: si el destino ya tiene una marca con el mismo código para el mismo artículo se descarta la del origen, si no se traslada) antes de borrar el proveedor de origen. El resumen de "Ver resumen antes de fusionar" y el aviso final de la fusión (`AdminProveedores.jsx`) muestran ahora también el recuento de marcas.

**Frontend**: `ArticuloForm.jsx` — dentro de la tarjeta de CADA proveedor (el asignado, el que se busque, o cualquiera de "otras alternativas") se añade una sección "Otras marcas de [proveedor]": cada marca ya guardada con su código editable, su imagen y sus fichas (mismo componente `TarjetaDocumentacion` que ya se usaba para la referencia principal, reutilizado tal cual), un botón "Eliminar esta marca" que borra código+imagen+fichas juntos con confirmación, y un formulario para añadir una marca nueva escribiendo solo su código.

**Verificación**: `node --check` sobre los 4 archivos de backend tocados (`marcasProveedorController.js`, `articulosController.js`, `proveedoresController.js`, `routes/admin.js`); `npm run build` (Vite) del frontend completo sin errores; en modo demo (`admin@demo.dali`), con Playwright: la sección "Otras marcas de..." aparece correctamente dentro de la tarjeta de un proveedor, con su formulario de alta, y el intento de añadir una marca muestra el aviso esperado "necesita el backend real" (no hay backend real que consultar en demo) sin ningún error de consola nuevo. La migración SQL en sí y el flujo completo contra Supabase (crear/editar/borrar una marca de verdad, con archivos reales) quedan por verificar en el propio Render de Víctor — este entorno de trabajo no tiene acceso a esa base de datos ni a ese Storage.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.15**.

---

## v0.96 — Corrección de v0.95: un único correo a todos los principales, no uno por cada uno (v1.19.14)

Antes de que Víctor llegara a desplegar v1.19.13, corrigió el enfoque del arreglo: "si hay tres correos marcados con la estrella en un proveedor, se envian 3 correos por separado? esto no es correcto, se debe enviar un unico correo pero a todos los destinatarios a la vez". El arreglo anterior (v0.95) sí resolvía el bug real (que Nicet Marquez nunca recibía nada), pero replicando el patrón equivocado de Control de Pedidos: `_get_proveedor_emails_principales()` + el bucle por defecto de `_encolar_email_sistema()`, pensado para notificaciones internas donde SÍ se quiere un correo separado por persona.

Revisando el propio `app.py` de Control de Pedidos apareció el patrón correcto, ya en uso ahí mismo para la reclamación automática a proveedor por pedido retrasado (`_encolar_email_sistema("reclamacion_proveedor_auto", ...)`): un comentario explícito dice "Se quiere un único envío, con todos los contactos principales juntos en el 'Para:' ... EmailJS sí admite varias direcciones separadas por comas en un solo campo 'to_email'", y arma el destinatario con `", ".join(proveedor_emails)`. Confirmado además que la tabla `emails_sistema_pendientes` y el poller de EmailJS (`templates/index.html`) no parten ni validan ese campo en ningún punto — es texto opaco de principio a fin, así que una lista separada por comas llega intacta hasta la propia API de EmailJS, que sí la reparte como destinatarios reales.

**Cambio**: `encolarEmailDocumentacionFaltante` (`documentacionController.js`) deja de encolar un correo por destinatario (bucle) y encola uno solo, con `destinatario = destinatarios.join(", ")` — mismo criterio que la reclamación automática a proveedor de Control de Pedidos. Sin tocar `controlPedidosEmailBridge.js` (ya devolvía la lista completa desde v0.95, aquí solo cambia cómo se usa esa lista), ni el frontend (el mensaje "En cola — se enviará a..." y el propio `destinatario` que devuelve el backend siguen siendo el mismo texto unido por ", " de antes), ni Control de Pedidos (su infraestructura ya soportaba esto, no hacía falta ningún cambio ahí).

**Verificación**: `node --check` sobre `documentacionController.js`.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.14** (frontend sin cambios en esta versión — se sube igual para mantener sincronizados los dos `package.json`).

---

## v0.95 — El correo de "Documentación faltante" solo llegaba a un contacto principal, aunque hubiera varios marcados (v1.19.13)

Víctor, revisando el correo real que le llegó a MILO CANARIAS ALIMENTACION, SL (captura de Gmail: asunto "Documentación pendiente — MILO CANARIAS ALIMENTACION, SL", "para jpedro"): "porque se envio solo al primer correo si tengo los dos marcardos para envio? la ficha de proveedores de control pedidos tiene la opcion de marcar aquellos correos qu estan destinados al envio" — con una captura de la ficha del proveedor en Control de Pedidos mostrando DOS contactos, Juan Pedro y Nicet Marquez (Calidad), ambos con la estrella dorada de "principal" marcada.

**Investigación**: en control-pedidos-princess, `_get_proveedor_emails_principales()` (`app.py`, usada para sus propios avisos a proveedores) ya soporta varios contactos principales a la vez y de hecho lo documenta explícitamente en su docstring: "Un proveedor puede tener varios contactos marcados a la vez con la estrella dorada — todos reciben las notificaciones como destinatario directo". El endpoint que consume DALI, sin embargo, `GET /api/externo/dali-sap/proveedores`, no usa esa función — usa `_prov_with_contactos()` (pensada para la pantalla de administración de Proveedores, no para repartir un envío), que arma un campo de compatibilidad `email_principal` quedándose con **uno solo** de los contactos marcados (`next((c for c in p["contactos"] if c.get("es_principal")), ...)`), aunque el array `contactos` completo (con el `es_principal` de cada uno) sí viaja también en la misma respuesta. En el lado de DALI, `emailPrincipalDe()` (`controlPedidosEmailBridge.js`) leía únicamente ese campo de compatibilidad, sin mirar nunca el array `contactos` — de ahí que Nicet Marquez, aunque estuviera correctamente marcada como principal y presente en la respuesta, nunca llegara a usarse.

**Cambio**: resuelto enteramente en el lado de DALI, sin tocar control-pedidos-princess — el array `contactos` que ya venía en la respuesta trae todo lo necesario. `emailPrincipalDe()` pasa a `emailsPrincipalesDe()` (`controlPedidosEmailBridge.js`), que recorre `contactos` y devuelve TODOS los que tengan `es_principal` con email (cayendo al primer contacto con email si ninguno está marcado, mismo criterio de reserva de antes). `resolverEmailProveedorEnControlPedidos()` pasa a `resolverEmailsProveedorEnControlPedidos()` (plural) devolviendo un array en vez de un único email; su versión "por lotes" (`resolverEmailsProveedoresEnControlPedidos`, usada para el listado de la pantalla) igual. En `documentacionController.js`, `encolarEmailDocumentacionFaltante` ahora encola un correo por cada destinatario resuelto (`POST /api/externo/dali-sap/emails-pendientes` solo admite un `destinatario` por llamada, así que se llama una vez por cada uno) — mismo criterio "una fila por destinatario" que ya usa `_encolar_email_sistema()` en Control de Pedidos para sus propios envíos con varios contactos principales. `grupo.email`, en el listado, pasa a ser un texto con todos los emails separados por ", " en vez de uno solo.

Deliberadamente sin tocar el frontend: el `mailto:` de `EmailProveedorModal.jsx` ya soporta varios destinatarios separados por coma sin cambio alguno, y el mensaje "En cola — se enviará a {resultadoEncolado?.destinatario}" también, porque el backend ahora manda ese mismo campo como texto unido (`destinatarios.join(", ")`), a propósito, para no tener que tocar la vista.

**Verificación**: `node --check` sobre `controlPedidosEmailBridge.js` y `documentacionController.js`. Import real de `documentacionController.js` con variables de entorno de prueba (con `npm install` temporal para resolver `exceljs` y demás dependencias, luego revertido — sin backend real detrás), sin errores.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.13** (frontend sin cambios en esta versión — se sube igual para mantener sincronizados los dos `package.json`, según la convención ya establecida).

---

## v0.94 — Límite real del bucket de Supabase Storage (10 MB) y exportación de documentación en zip organizada (v1.19.12)

Tras desplegar v1.19.11, Víctor relanzó la carga masiva de fichas técnicas de MILO CANARIAS y la 10075 seguía fallando — pero ya no con el error de tamaño de la app, sino con un mensaje nuevo y en inglés: `"The object exceeded the maximum allowed size"`. Ese texto no lo genera este código (los mensajes propios están en español) — es el error tal cual de la propia API de Supabase Storage. Explicación: `LIMITE_TAMANO_FICHA` (código de la app) y el límite de tamaño del bucket `articulo-fichas` (configurado aparte, en el dashboard de Supabase) son dos topes independientes — subir uno no toca el otro. El bucket seguía en su valor original de **10 MB**, así que aunque la app ya dejaba pasar hasta 20 MB, Supabase rechazaba igual el archivo de 15,03 MB antes de guardarlo. Confirmado en capturas del dashboard (Storage → articulo-fichas → 10 MB) y corregido a mano ahí mismo, subiéndolo a **25 MB** (con margen sobre los 20 MB de la app). No fue necesario ningún cambio de código para esta parte — es una configuración externa al repo, ya anotada como riesgo en el propio comentario de v0.92.

De paso, comprobado con una carga masiva real sobre `Todos los proveedores` (varios cientos de filas, muchos proveedores distintos) que el resto de "con error" de las pruebas anteriores no tenía relación con el tamaño: son, tal como estaba previsto, artículos cuyo código de proveedor todavía no está grabado en `codigos_proveedor` — mensaje `"No se encontró ningún artículo con código de proveedor..."`, comportamiento ya documentado (ver comentario de `procesarFila` en `CargaMasivaModal.jsx`), no un fallo nuevo.

A raíz de todo este episodio, Víctor pidió una forma de tener "una copia limpia de lo que ahora mismo esta ok": "existe alguna manera de que se pueda descargar todo organizado? es decir, carpeta nombre proveedor, dentro carpetas FICHAS TECNICAS, FICHAS SEGURIDAD e IMAGENES y dentro de cada una sus respectivos archivos simplemente nombrados con el codigo del proveedor?".

**Cambio (nueva funcionalidad)**:
- Nuevo endpoint `GET /admin/documentacion-zip?proveedor_id=<opcional>` (`backend/src/controllers/exportZipController.js`) — genera un `.zip` por streaming (sin acumular nada en memoria ni en disco, usando `archiver`) con exactamente la estructura de carpetas `PROVEEDOR / FICHAS TECNICAS|FICHAS SEGURIDAD|IMAGENES / archivo`, la misma que espera `CargaMasivaModal.jsx` al volver a subir. Recorre `fichas`/`imagenes` con proveedor asignado, descarga cada archivo de Supabase Storage (`supabase.storage.from(bucket).download(...)`, primer uso de ese método en el repo — hasta ahora solo se generaban URLs firmadas) con 4 descargas en paralelo (mismo patrón `CONCURRENCIA_*` que ya usa la carga masiva en el frontend), y nombra cada archivo con el código de proveedor guardado en `codigos_proveedor`; si no hay código guardado para ese artículo+proveedor, se incluye igual como `SIN-CODIGO-DALI-<código dali>` en vez de perderlo. `proveedor_id` opcional: sin él exporta todos los proveedores de una vez (puede tardar varios minutos con el catálogo completo — se desactiva el timeout de la petición para esto).
- Nueva pestaña de administración "Exportar documentación" (`frontend/src/components/admin/AdminExportarZip.jsx`), con un desplegable para elegir un proveedor concreto o "Todos", y un botón que abre la descarga (mismo patrón `window.open(url)` que ya usan los otros exports a Excel/PDF — no hace falta manejar el blob a mano).
- Nueva dependencia en el backend: `archiver` (streaming de zip, no había ninguna librería de zip en el proyecto hasta ahora).

**Verificación**: `node --check` sobre `exportZipController.js` y `admin.js`. Import real del controlador y de `admin.js` con variables de entorno de prueba (sin backend real detrás), sin errores. `npm run build` (Vite) del frontend completo, sin errores ni avisos.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.12**.

---

## v0.93 — Aviso propio, visible desde el primer momento, para archivos demasiado pesados en carga masiva (v1.19.11)

Víctor, tras confirmar el arreglo de v0.92 (límite de 10 a 20 MB): "pudes poner un avsio para que cuando la carga encuentre archivos pesados, no los cargue, pero indique cual para saber y detectar el problema" — la petición no era solo el arreglo puntual, sino que el problema en general (un archivo por encima del límite) fuera fácil de detectar la próxima vez, sin depender de leer con atención una tabla de decenas de filas.

**Cambio en `CargaMasivaModal.jsx`**:
- `CONFIG_POR_TIPO` gana un campo `tamanoMaximoBytes` por tipo (5 MB imágenes, 20 MB fichas) — DEBE mantenerse igual al límite real del backend (`storageController.js`); se deja anotado como advertencia en el propio código, ya que son dos archivos distintos sin forma de compartir la constante entre frontend y backend en este proyecto.
- `clasificarArchivos()` comprueba el tamaño de cada archivo justo después de confirmar que es del tipo/carpeta correcta, ANTES de intentar resolver su código de proveedor o generar una fila de subida — un archivo demasiado pesado ya no llega a la tabla de resultados como una fila más (ni se intenta subir: cero peticiones de red desperdiciadas), se aparta en su propia lista.
- Nuevo aviso (`alert alert-warn`) que lista esos archivos por nombre, peso real (formateado como "15,0 MB") y proveedor, visible en cuanto se elige la carpeta — antes incluso de pulsar "Subir". Se mantiene visible durante todo el proceso (no depende de la tabla de resultados, que solo aparece si hay algo pendiente/subido).
- El aviso de "no se ha encontrado ningún archivo…" ahora también comprueba que no haya archivos demasiado pesados, para no decir "no se ha encontrado nada" cuando en realidad SÍ había archivos, solo que ninguno pasaba el límite.
- El banner final "Carga finalizada" menciona también cuántos se quedaron fuera por peso, por si se ha llegado hasta el final del proceso sin volver a mirar el aviso de arriba.

**Verificación**: `npx esbuild` sobre `CargaMasivaModal.jsx`, sin errores. Prueba manual de `formatearMb()` y de la comparación de tamaño con el caso real de Víctor (15.766.188 bytes): con el límite ya en 20 MB (v0.92) ese archivo concreto ahora pasa sin problema; se comprobó también que un archivo por encima de 20 MB sí se detecta correctamente antes de subir.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.11** (backend sin cambios en esta versión — se sube igual para mantener sincronizados los dos `package.json`, según la convención ya establecida).

---

## v0.92 — Carga masiva de MILO CANARIAS: el artículo 10075 no grababa su ficha técnica — límite de 10 MB (v1.19.10)

Víctor, en un problema nuevo y sin relación con la firma de correos: "no esta leyendo correctamente las fichas tecnicas desde carga masiva eligiendo un unico proveedor (MILO CANARIAS)" — con captura del detalle del artículo `00424` (CENTRO JAMON IBERICO DESHUESADO, código de proveedor `10075`) sin ficha técnica, y un `dir` completo de PowerShell de la carpeta `FICHAS TECNICAS` de ese proveedor, señalando que el archivo `10075_JAMON DE CEBO IBERICO NICO.pdf` sí está ahí.

Investigación: el nombre del archivo sigue exactamente el único formato admitido desde v0.83 (`codigoProveedor_resto.pdf`, ver `CargaMasivaModal.jsx`), así que no era un problema de parseo de nombre. Revisando `storageController.js` (`subirFichaArticulo`, el endpoint que usa tanto la carga masiva como la ficha individual), apareció el límite: `archivo.size > 10 * 1024 * 1024` — un tope de 10 MB para cualquier PDF de ficha técnica o de seguridad. El archivo de Víctor pesa 15.766.188 bytes (~15,03 MB), confirmado en el propio `dir` (y coincide byte a byte con una copia antigua del mismo PDF bajo el nombre viejo `DALI_00000424_-_SAP_10100294_-...pdf`, mismo tamaño exacto). Ese endpoint SÍ devuelve un error 400 claro ("El PDF no puede superar 10 MB.") y la carga masiva SÍ lo muestra por fila (columna de estado/mensaje en rojo) — pero entre decenas de filas subidas correctamente, una fila en rojo es fácil de no ver.

**Cambio**: límite subido de 10 a 20 MB (`LIMITE_TAMANO_FICHA`, `storageController.js`), con margen razonable sobre este caso real sin abrir la puerta a archivos desproporcionados. El mensaje de error, si se supera igualmente, ahora dice el peso real del archivo en MB en vez de un texto fijo, para que sea más fácil detectar el problema la próxima vez sin tener que ir a comprobar el tamaño a mano. Se deja anotado en el propio código que el bucket de Supabase Storage `articulo-fichas` tiene su propio límite de tamaño configurado en su dashboard (no en este repo) — si algún día hiciera falta subir el límite de la app por encima de ese, habría que revisarlo también ahí.

**Verificación**: `node --check` sobre `storageController.js`, sin errores. No se ha necesitado tocar el frontend — no había ninguna validación de tamaño duplicada del lado del cliente.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.10**.

---

## v0.91 — Norma documentada: el cruce de email para la firma solo mira el email principal, nunca email2 (v1.19.9)

Al validar el arreglo de v0.90 (preferir, entre varias coincidencias, la que tenga móvil), Víctor avisó de un riesgo relacionado: "tener en cuenta que este mismo correo tambien es correo secundario en otro usuario, asi que podemos poner como norma que solo mire en el primer correo de cada usuario". Comprobado: el endpoint `/api/externo/dali-sap/compradores` de control-pedidos-princess ya seleccionaba solo `email` (nunca `email2`) desde que se creó en v0.86 — así que no hacía falta ningún cambio de código, pero tampoco estaba dicho en ningún sitio como una decisión a propósito, así que quien tocara ese endpoint más adelante podría "mejorarlo" añadiendo `email2` al cruce sin saber que eso reintroduciría justo el tipo de colisión que costó cuatro iteraciones diagnosticar en v0.87-v0.90.

**Cambio**: comentario explícito en ambos lados del puente (`controlPedidosEmailBridge.js` aquí, y el docstring del endpoint en `app.py` de control-pedidos-princess) dejando la norma por escrito, citando la petición de Víctor tal cual.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.9**.

---

## v0.90 — Encontrada y arreglada la causa real: dos usuarios de Control de Pedidos con el mismo email (v1.19.8)

El log ampliado de v1.19.7 dio la respuesta a la primera petición: `[CONTROL-PEDIDOS-BRIDGE] "centralcompras1.canarias@princess-hotels.com" SÍ coincide con "Prueba" en Control de Pedidos, pero no tiene móvil guardado allí`. Víctor confirmó con una captura del listado de Usuarios de Control de Pedidos: hay una cuenta `usuario prueba` (nombre "Prueba", rol Compras, sin móvil, sin ID de Telegram — claramente una cuenta de pruebas nunca despejada) con el MISMO email que su propia cuenta real `comprascan` (Víctor A. Martin Andrade, rol Admin, móvil `+34660245366`).

`resolverMovilCompradorEnControlPedidos()` (`controlPedidosEmailBridge.js`) usaba `compradores.find(...)`, que se queda con el PRIMER elemento del array que cumpla la condición — y el array viene ordenado por nombre desde la consulta SQL de Control de Pedidos (`ORDER BY nombre`), así que "Prueba" (P) siempre ganaba a "Víctor A. Martin Andrade" (V) por orden alfabético. Cualquier admin cuyo email coincidiera por casualidad con el de esa cuenta de pruebas se habría encontrado con el mismo problema.

**Cambio**: en vez de `.find()` sobre TODOS los comprador(es), ahora se filtran primero TODAS las coincidencias por ese email (`.filter()`) y, si hay más de una, se prefiere la que sí tiene móvil relleno (`coincidencias.find(c => c.movil) || coincidencias[0]`) — no depende de que se limpie la cuenta de pruebas para funcionar bien desde ya. Se añadió también un aviso en el log específico para este caso (coincidencia múltiple), distinto del aviso de "sin coincidencia" o "coincide pero sin móvil" ya existentes, para poder detectar futuras colisiones de email sin tener que llegar hasta aquí otra vez a base de capturas de pantalla.

Verificado con un script aparte replicando la lógica exacta contra los datos reales de la captura de Víctor (Prueba y Víctor A. Martin Andrade con el mismo email, solo Víctor con móvil): elige correctamente a "Víctor A. Martin Andrade" con `+34660245366`.

Recomendado a Víctor, aunque ya no es necesario para que funcione: en Control de Pedidos → Usuarios, quitarle el email a `usuario prueba` (o ponerle uno que no sea real), para evitar que seguir usando esa cuenta de pruebas cause más colisiones de este tipo con otras funciones que en el futuro también crucen por email.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.8**.

---

## v0.89 — Log de diagnóstico ampliado: qué lista de compradores llega realmente de Control de Pedidos (v1.19.7)

Víctor desplegó v1.19.6 y pegó el log de Render: `[FIRMA-ADMIN] Sin teléfono para "centralcompras1.canarias@princess-hotels.com" — Control de Pedidos respondió sin error pero ningún comprador/admin activo tiene ese email exacto guardado allí, o no tiene móvil relleno.` Junto con capturas de "Editar usuario" en Control de Pedidos mostrando que ese mismo usuario (username `comprascan`, nombre "Víctor A. Martin Andrade") sí tiene rol Administrador, está activo, y tiene el móvil `+34660245366` guardado.

El log de v1.19.6 ya distingue "el puente falló" de "no hay coincidencia", y esto último es justo lo que está pasando — pero sin ver la lista real que devuelve `/api/externo/dali-sap/compradores`, no se puede saber si el problema es que esa lista viene vacía o incompleta (algo raro en el filtro SQL de esa nueva ruta, o en su propio despliegue) o si el email en sí no coincide exactamente entre las dos apps (un carácter distinto, un dominio distinto, un espacio de más — la captura de Control de Pedidos corta el campo Email a "centralcompras1.canar" por el ancho del recuadro, así que no se puede comprobar a simple vista si el resto coincide letra por letra con "centralcompras1.canarias@princess-hotels.com").

**Cambio**: `resolverMovilCompradorEnControlPedidos()` (`controlPedidosEmailBridge.js`) ahora registra, cuando no hay coincidencia, cuántos comprador(es)/admin(es) llegaron de Control de Pedidos y su lista completa de emails tal cual — así se ve de un vistazo si la lista está vacía/corta (apunta a un problema del lado de Control de Pedidos) o si trae el usuario esperado pero con un email ligeramente distinto (apunta a un desajuste de datos entre las dos apps). Si hay coincidencia por email pero sin móvil guardado, también se distingue con su propio aviso.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.7**.

---

## v0.88 — Log de diagnóstico para el teléfono de la firma, que sigue sin aparecer (v1.19.6)

Víctor pegó el log completo del despliegue de Render del backend (`dali-backend-fr`): commit correcto, build OK, `dali-articulos-api@1.19.5` arrancando, y — pegado justo detrás, como prueba — el texto de un correo real ya generado con esa versión: la petición de imagen SÍ aparece ya ("Adicionalmente, y siempre que les sea posible, les agradeceríamos que nos hicieran llegar también una imagen..."), confirmando que el arreglo de v0.87 funciona una vez el backend está de verdad desplegado. Pero cierra con: "solo falta el telefono en la firma" — la firma sale con nombre, departamento, dirección y email, pero sin la línea del teléfono.

Con el código ya confirmado correcto (diff exacto entre lo entregado y lo que Víctor tiene en GitHub, sin ninguna diferencia) y el backend confirmado en la versión correcta, el problema solo puede estar en la llamada al puente en sí — pero `resolverFirmaAdmin()` no dejaba ningún rastro: atrapaba cualquier fallo en silencio (a propósito, para no romper el correo) sin registrar nada, así que "no hay teléfono guardado" y "la llamada al puente falló" eran indistinguibles desde fuera. Sin un log, seguir adivinando (¿Control de Pedidos sin desplegar? ¿email que no coincide? ¿secreto mal configurado?) no lleva a ningún sitio verificable.

**Cambio**: `resolverFirmaAdmin()` ahora registra en los logs de Render de este mismo servicio (backend) el motivo exacto cuando el teléfono sale vacío — sin cambiar el comportamiento de cara al correo, que se sigue generando igual con o sin esa línea. Pendiente: que Víctor vuelva a generar un correo y pegue el fragmento de log de Render con `[FIRMA-ADMIN]` para saber con certeza si es un problema de despliegue de Control de Pedidos, de coincidencia de email, o de configuración del puente.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.6**.

---

## v0.87 — Dos arreglos sobre el correo de v0.86, y el teléfono de la firma pendiente de confirmar (v1.19.5)

Víctor probó v1.19.4 con un proveedor real y pegó el texto exacto generado, señalando tres problemas: "no se incluye la solicitud de imagen de las referencias solicitado, no se incluye el teléfono del administrador, eliminar la ultima frase del correo despues de la firma 'Catálogo DALI · Central de Compras Canarias'". Junto con el texto, adjuntó una captura de "Editar usuario" en Control de Pedidos mostrando que su propio usuario (rol Administrador) sí tiene el móvil guardado (`+34660245366`).

**1. Falta la petición de imagen** — bug real en la lógica de v0.86: la frase seguía dentro de `if (faltaImagen)`, con `faltaImagen = grupo.articulos.some(a => a.falta_imagen)` calculado sobre TODOS los artículos del grupo, no solo los que aparecen listados en el correo (los que tienen `falta_ficha_tecnica`). Si un proveedor tenía artículos pendientes de ficha técnica pero, por casualidad, ninguno de sus artículos (de todo el grupo, no solo los listados) tenía la imagen marcada como faltante, la frase desaparecía entera — exactamente lo que le pasó a Víctor en su prueba. Corregido quitando la condición: la petición de imagen es ahora fija en todo correo de este tipo, igual que el resto de avisos (Víctor la pidió originalmente como una petición de cortesía general — "si es posible seria bueno" —, no como algo condicionado a un dato concreto).

**2. Línea sobrante tras la firma** — al añadir la firma real en v0.86, se quedó sin quitar la línea fija `<p>Catálogo DALI · Central de Compras Canarias</p>` que `construirHtmlReclamacionDocumentacion()` (`emailHtml.js`) añadía siempre al final del cuerpo — una reliquia de antes de que hubiera firma. Con la firma real ya ahí, esa línea leía como una segunda firma sin sentido justo debajo de la primera. Eliminada.

**3. Teléfono ausente en la firma** — investigado a fondo sin encontrar ningún bug: el rol guardado para "Administrador" en el desplegable de Control de Pedidos es literalmente `admin` (`<option value="admin">Administrador</option>`, `templates/index.html`), que es justo lo que consulta el nuevo endpoint (`WHERE rol IN ('compras', 'admin')`); el nombre y el email de la firma SÍ aparecieron correctamente en la prueba de Víctor (proceden de `req.user` en DALI, sin red), lo que confirma que la parte de la firma que no depende del puente funciona bien. La explicación más probable, dado que no hay ningún fallo de lógica visible: `control-pedidos-princess` todavía no tenía desplegada la v12.30.53 (el nuevo `GET /api/externo/dali-sap/compradores`) en el momento de esa prueba concreta — sin ese endpoint en producción, la llamada del puente falla (404) y, por diseño (para no bloquear nunca el correo), `resolverFirmaAdmin()` la traga en silencio y deja `telefono: null`. Se avisó a Víctor de esta dependencia al entregar v1.19.4 (nota en `DEPLOY.md`), así que es plausible que desplegara DALI antes que Control de Pedidos, o que el despliegue de Control de Pedidos aún no hubiera terminado de propagarse en Render en el momento de la prueba. Queda pendiente de que confirme que ambos servicios están al día antes de seguir investigando esta parte.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.5**.

---

## v0.86 — Correo de "Documentación faltante" reescrito, con firma (teléfono cruzado contra Control de Pedidos) (v1.19.4)

Víctor pegó el texto completo, tal cual se había enviado a un proveedor real, del correo que genera "Documentación faltante" y pidió: "¿puedes hacer este correo mas profesional? la idea esta clara y entendible, pero se que lo puedes redactar mejor siguiendo las pautas establecidas, indicar de una manera elegante que si es posible seria bueno que se adjunte imagen de cada una de las referencias asignadas siguiendo la misma pauta de las fichas, como nombre el codigo del articulo ; tambien falta la firma al estilo del resto de correos que se envian a los proveedores desde control pedidos ; en este caso incluir el nombre, telefono, correo del admin que realiza la gestion".

Investigación previa: `generarTextoEmail()` en `EmailProveedorModal.jsx` (el redactado real) y `construirHtmlReclamacionDocumentacion()` en `emailHtml.js` (el envoltorio HTML, que solo convierte párrafos/viñetas — no reescribe el texto). Para la firma, se buscó el patrón "estándar" que usa control-pedidos-princess: `_firma_comprador_html`/`_firma_comprador_text` en su `app.py` ("Firma estándar de correo saliente, v12.24.0") — nombre, "Dpto. Central de Compras Canarias", dirección fija (Av. Touroperador Tui, s/n · 35100 Maspalomas), teléfono con prefijo "(+34)" y email, precedido de "Atentamente,". Al intentar rellenar ese teléfono, aparece un bloqueo real: la tabla `usuarios` de DALI (`database/schema.sql`) nunca ha tenido columna de teléfono/móvil, y tampoco la sesión (`sesion` en `App.jsx`, ni `req.user` en el backend) — ninguna migración la añadió nunca.

Se preguntó a Víctor cómo resolver ese teléfono (opciones: añadir un campo propio por admin, un número fijo de departamento, o dejar la firma sin teléfono por ahora). Respondió con una cuarta opción, más simple que las tres planteadas: "¿puedes coger la info de la ficha usuarios control pedidos? los admin son los mismos y los compradores son admin en catalogo dali" — es decir, cruzar por email contra los usuarios que YA existen en control-pedidos-princess (que sí tiene columna `movil`, confirmado en `models.py`), en vez de duplicar el dato en DALI.

**Cambio en `control-pedidos-princess` (`app.py`, v12.30.53)**: nuevo `GET /api/externo/dali-sap/compradores`, mismo esquema de autenticación (firma HMAC con `DALI_SSO_SECRET`, sin sesión) que el ya existente `GET /api/externo/dali-sap/proveedores`. Devuelve `{nombre, email, movil}` de los usuarios activos con rol `compras` o `admin` — los dos roles que, en la práctica, son las mismas personas que administran DALI.

**Cambio en DALI**:
- `backend/src/services/controlPedidosEmailBridge.js`: `obtenerCompradoresDeControlPedidos()` y `resolverMovilCompradorEnControlPedidos(email)` (cruce por email normalizado a minúsculas), mismo patrón que las funciones ya existentes para proveedores.
- `backend/src/controllers/documentacionController.js`: nueva `resolverFirmaAdmin(req)` — nombre/email de `req.user` (sin red), teléfono resuelto contra Control de Pedidos (si falla o no hay coincidencia, `telefono: null`, sin romper nada). `GET /admin/documentacion-faltante` ahora devuelve también `firma_admin`.
- `frontend/src/components/admin/AdminDocumentacionFaltante.jsx`: pasa `datos.firma_admin` a `EmailProveedorModal` como prop `firmaAdmin`.
- `frontend/src/components/admin/EmailProveedorModal.jsx`: `generarTextoEmail(grupo, firmaAdmin)` reescrito:
  1. Tono más formal ("Estimados/as," + frase de apertura), mismo contenido de fondo.
  2. La petición de imagen ("siempre que les sea posible... identificada del mismo modo que se indica a continuación") ahora enlaza con el aviso de nombrado de archivos en vez de repetir la norma por separado — la misma pauta (código de artículo al inicio del nombre) se explica una sola vez para fichas técnicas, fichas de seguridad e imágenes.
  3. Firma final con el formato de Control de Pedidos: nombre, departamento, dirección fija, teléfono (si lo hay) y email — si `firmaAdmin` no tiene teléfono (bridge caído o sin coincidencia), esa línea simplemente no aparece, igual que ya hace Control de Pedidos cuando a un comprador no le tiene guardado el móvil.
- `frontend/src/utils/format.js`: `formatearMovilFirma()`, réplica en JS de `_formatear_movil_firma()` (quita cualquier +34/0034/34 inicial antes de anteponer el "(+34)" fijo de la firma, para no duplicar el prefijo si el número ya se guardó con él).

**Verificación**: `node --check` sobre los dos archivos de backend tocados, sin errores. `npx esbuild` sobre los tres archivos de frontend tocados (con extensión, sin flag `--loader` porque falla al leer de fichero en vez de stdin), sin errores. `python3 -m py_compile app.py models.py` en control-pedidos-princess, sin errores. Prueba manual del texto generado (script aparte con la misma lógica) con y sin `firmaAdmin`, confirmando que sin firma (o sin teléfono) el correo se genera igual, sin líneas vacías ni fallos.

**Importante para el despliegue**: esta versión de DALI necesita que `control-pedidos-princess` tenga también desplegada su v12.30.53 (el nuevo endpoint `/api/externo/dali-sap/compradores`) para que el teléfono aparezca en la firma — si se despliega DALI antes, no se rompe nada, la firma sale igual pero sin esa línea hasta que se actualice también ese otro servicio.

Versión: `backend/package.json` y `frontend/package.json` → **1.19.4**. `control-pedidos-princess` → **v12.30.53**.

---

## v0.85 — CONTROL_PEDIDOS_URL apuntaba a la URL directa de Render en vez de al proxy de Cloudflare (v1.19.3)

Víctor, con una captura de "Documentación faltante": el banner de aviso decía `No se ha podido consultar Control de Pedidos para resolver los emails de los proveedores (Control de Pedidos respondió 404.)`.

Primer intento de diagnóstico: revisar la ruta `GET /api/externo/dali-sap/proveedores` en `app.py` de control-pedidos-princess y la llamada correspondiente en `controlPedidosEmailBridge.js` — coinciden exactamente, ruta y payload correctos por ambos lados, sin ningún cambio de código reciente que pudiera haberla roto.

Como el código en sí no mostraba nada raro, se probó a pedir esa URL directamente desde fuera (`https://control-pedidos-princess.onrender.com/api/externo/dali-sap/proveedores`): 404. Se probó también la portada de esa misma app (`/`, que sí tiene ruta definida en su `app.py`) y su healthcheck (`/ping`): los dos también 404. Es decir, la URL de Render de control-pedidos-princess no responde a NADA desde fuera — no es un problema de esa ruta en concreto.

Víctor confirmó el motivo: control-pedidos-princess no se sirve directamente por su URL de Render — vive detrás de un Worker de Cloudflare que hace de proxy (`https://proxy.controlpedidosprincess-canarias.workers.dev`), el mismo patrón que ya usa el Organizador para hablar con Control de Pedidos (confirmado en el propio `HISTORIAL_CAMBIOS.md` de ese proyecto: "el Organizador solo hace la petición HTTP al proxy de Control de Pedidos"). `CONTROL_PEDIDOS_URL`, fijada el 2026-08-27 al construir este puente de correos, apuntaba a la URL directa de Render en vez de a ese proxy — el puente de "Documentación faltante" fue la primera pieza de DALI en necesitar hablar con Control de Pedidos desde el backend (server a server, sin pasar por el navegador de nadie), así que este error de configuración no tenía forma de haberse notado antes.

**Cambio**: `CONTROL_PEDIDOS_URL` en `render.yaml`/`.env.example`/`DEPLOY.md` pasa a `https://proxy.controlpedidosprincess-canarias.workers.dev`. Sin cambios de código — la lógica de `controlPedidosEmailBridge.js` siempre estuvo bien. Importante: cambiar `render.yaml` en el repo no actualiza el valor ya guardado en un servicio de Render existente — hace falta que Víctor entre a Render → `listado-DALI-SAP` → Environment y cambie el valor de `CONTROL_PEDIDOS_URL` a mano (el `render.yaml` del repo queda como referencia correcta para el futuro, o para un despliegue nuevo desde cero).

Versión: `backend/package.json` y `frontend/package.json` → **1.19.3**.

---

## v0.84 — Reconstrucción del correo de "Documentación faltante": vista previa real, sin email propio de DALI (v1.19.2)

Víctor, tras ver funcionando el encolado por Control de Pedidos (v0.83),
subió capturas de tres pantallas — el modal "Notificación de alerta" de
Control de Pedidos (la referencia a seguir), el "Documentación faltante"
de DALI con su propio editor de email inline, y el "Generar email" de
DALI, en texto plano sin ninguna vista previa — y pidió: "Necesito
reconstruir el apartado envio correo Documentación Faltante, debería ser
similar a la notificación de alerta al proveedor de control pedidos,
olvidar el correo grabado en Catálogo Dalí, borrar esta info, utilizar
únicamente los correos de la base datos proveedores control pedidos, en
pantalla previa del correo como en notificación. Ventana visual correcta
con correo logo texto etc, si el usuario acepta se encola y cuando
cualquier tipo de usuario abra control pedido entonces se envia con
emailjs."

Lo último de la petición — encolar y enviar por EmailJS al abrir Control
de Pedidos — ya estaba construido y funcionando desde v1.19.0/v1.19.1
(ver v0.82/v0.83 más abajo); no hacía falta tocar nada de eso ni del lado
de control-pedidos-princess. Quedaban dos cosas de verdad nuevas:

**1. Vista previa visual real.** Antes, `EmailProveedorModal.jsx` solo
mostraba un `<input>` para el asunto y un `<textarea>` para el cuerpo, sin
ninguna vista de cómo quedaría el correo real. Se estudió cómo lo resuelve
Control de Pedidos en su propio modal de referencia
(`abrirModalEmailAlerta`, `#mea-body-preview`): pide al backend el HTML ya
renderizado y lo inyecta con `innerHTML`, sin reimplementar el maquetado
en JS. Se siguió el mismo criterio aquí: nuevo endpoint puro y sin tocar
la base de datos, `POST /admin/documentacion-faltante/preview-email`
(`previsualizarEmailDocumentacionFaltante` en `documentacionController.js`),
que reutiliza tal cual `construirHtmlReclamacionDocumentacion()` — la
misma función que ya usaba `encolarEmailDocumentacionFaltante` para
construir el correo de verdad — así que la vista previa es SIEMPRE fiel a
lo que se envía, sin riesgo de que diverjan dos implementaciones del
mismo maquetado. En el frontend, `EmailProveedorModal.jsx` pide esa vista
previa en cada cambio de asunto o cuerpo, con el mismo hook
`useDebouncedValue` que ya usan los buscadores, para no lanzar una
petición en cada pulsación de tecla.

**2. Fin del email propio de DALI.** Hasta ahora `proveedores.email` (la
columna añadida en la migración `2026-08-25_email_proveedor.sql`) convivía
con los contactos de Control de Pedidos: v1.19.1 usaba Control de Pedidos
como primera opción pero caía de vuelta al email de DALI si no encontraba
proveedor allí. Víctor pidió cortar esa doble fuente de raíz: "olvidar el
correo grabado en Catálogo Dalí, borrar esta info, utilizar únicamente los
correos de la base datos proveedores control pedidos". Se eliminó por
completo: la columna (migración
`database/migraciones/2026-08-28_borrar_email_proveedor_dali.sql`, que
sustituye a la de 08-25), el editor inline de email en
`AdminDocumentacionFaltante.jsx` (estado, handlers y el botón
"Cambiar"/"Añadir email" que se veía en la captura que subió Víctor), el
endpoint `PUT /admin/proveedores/:id/email` y su `actualizarEmailProveedor`
en `api.js`, y el paso de "Fusionar proveedores"
(`proveedoresController.js`) que copiaba el email de un proveedor a otro
al fusionarlos — ese último se encontró por `grep` como segundo consumidor
de la misma columna, no mencionado explícitamente por Víctor pero que
habría quedado escribiendo en una columna ya borrada. `resolverEmailProveedorEnControlPedidos()`
ya no tiene ningún fallback: si el proveedor no existe en Control de
Pedidos, o existe pero ninguno de sus contactos tiene email, devuelve
`null` y ahí termina la búsqueda — el modal y la pantalla de
"Documentación faltante" lo dejan claro con un mensaje que apunta a
Control de Pedidos → Proveedores en vez de ofrecer añadirlo aquí.

Se añadió también una versión "por lotes" del resolver
(`resolverEmailsProveedoresEnControlPedidos`) para
`calcularDocumentacionFaltante()`, que puede agrupar artículos en varias
decenas de proveedores distintos — trae la lista completa de Control de
Pedidos UNA sola vez en vez de una petición HTTP por proveedor. Si esa
llamada falla (Control de Pedidos no responde, red caída…), la pantalla
no se rompe: se sigue mostrando la documentación faltante con todos los
emails vacíos y un aviso (`aviso_bridge`) explicando que no se pudieron
resolver por ahora.

Versión final: `backend/package.json` y `frontend/package.json` →
**1.19.2** (misma convención desde v1.17.1: los dos suben juntos aunque un
cambio concreto solo toque un lado).

---

## v0.83 — "Encolar envío" usa los contactos de Proveedores de Control de Pedidos (v1.19.1)

Víctor, sobre el aviso de v0.82 (captura del panel "Config Alertas" de
Control de Pedidos, contador EmailJS en 162/195): "imagino que el
control de evios sigue descontando tambien estos ecolados - por otro
lado como vamos a utilizar el sistema de envios de control_pedidos,
podriamos utilizar tambien el apartado de proveedores con sus correos
electronicos etc? de esta manera los tenemos unicamente en un unico
punto y podemos incluir mas correos para el envio, ahora en articulos
es solo uno".

**Primera parte, confirmado por código, no hacía falta cambiar nada**:
sí, el contador de EmailJS de Control de Pedidos se incrementa igual
para los correos encolados desde DALI — `_enviarEmailsSistemaPendientes()`
llama a `enviarEmailJS()` para cualquier fila de la cola sin distinguir
su `evento_codigo`, y esa función siempre registra el envío
(`POST /api/emailjs/registrar-envio`) al terminar.

**Segunda parte — investigación**: `proveedores` de DALI es mínimo
(`id`, `nombre_proveedor` único por el import de Excel/SAP, y un único
`email` opcional añadido a mano por Víctor, ver migración
2026-08-25_email_proveedor.sql). Control de Pedidos, en cambio, ya
tiene `proveedores` + `proveedor_contactos` (varios contactos por
proveedor, cada uno con nombre/teléfono/móvil/email/`es_principal`) —
exactamente lo que pedía Víctor, ya construido y en uso para sus propios
correos de pedidos.

**Decisión sobre cómo cruzar los proveedores de las dos apps**: se
preguntó a Víctor entre enlace manual proveedor-a-proveedor (con un
buscador nuevo en DALI) o cruce automático por nombre con revisión de
los que no coincidieran. Su respuesta fue otra: "la lista de proveedores
actual de articulos es la correcta, limpia y filtrada, voy a actualizar
la de control_pedidos para que tenga exactamente los mismos nombres y
trabajar sobre una unica base" — es decir, va a hacer él mismo que los
nombres coincidan exactamente en las dos apps, así que el cruce por
nombre (normalizado: espacios y mayúsculas/minúsculas ignorados, nada
más "inteligente" que pudiera enlazar por error dos empresas distintas)
es suficiente y no hace falta ninguna pantalla nueva de enlace ni un
mapeo id-a-id guardado en ninguna de las dos bases.

**Cambio en control-pedidos-princess** (`app.py`): nuevo
`GET /api/externo/dali-sap/proveedores`, misma firma HMAC que el
endpoint de encolar (v0.82) — devuelve los proveedores activos con sus
contactos, reutilizando `_prov_with_contactos` (la misma función que ya
usa `GET /api/proveedores` para su propia pantalla de Proveedores). Ver
su propio `CHANGELOG.md` (v12.30.27).

**Cambio en DALI**: `controlPedidosEmailBridge.js` gana
`resolverEmailProveedorEnControlPedidos(nombreProveedor)` — trae la
lista completa y cruza por nombre exacto normalizado, devolviendo el
email del contacto marcado como principal (o el primero con email si no
hay ninguno marcado, mismo criterio que ya aplica Control de Pedidos
internamente). `documentacionController.js`
(`encolarEmailDocumentacionFaltante`) lo intenta primero; si no hay
proveedor con ese nombre allí, o la llamada falla por cualquier motivo,
cae de vuelta al `proveedores.email` propio de DALI sin bloquear el
envío — solo da error si NINGUNO de los dos lados tiene un email
guardado. `EmailProveedorModal.jsx` muestra el destinatario real que
confirma el backend (puede ya no coincidir con el email guardado en
DALI) y aclara cuándo viene de Control de Pedidos.

No se ha tocado la pantalla de "Documentación faltante"
(`AdminDocumentacionFaltante.jsx`) ni el campo `proveedores.email` de
DALI — siguen ahí tal cual, como respaldo para cuando un proveedor
todavía no exista (o no coincida de nombre) en Control de Pedidos.

---

## v0.82 — Envío real de "Documentación faltante" vía la cola de Control de Pedidos (v1.19.0)

Víctor, junto con dos zips (`controlpedidosprincessmain.zip` y una copia
del propio proyecto DALI): "podemos aprovechar la organizacion que
tenemos actualmente en controlpendidos para el envio de correos y que
los correos de dalisaparticulos utilice la misma infraestuctura? la idea
es que los correos para la solicitud de documentacion faltante utilice
este metodo de emailjs, se podria generar dejar en cola y cuando alguien
abra control de pedidos se lance, de esta manera podriamos reestructurar
y hecer mas atractivo y profecional los correos electronicos, con logo
colores etc ... ¿es factible? esto luego se utilizaria tambien para el
punto que tenemos pendiente de recuperacion contraseña pero seria un
segundo paso".

**Investigación previa**: control-pedidos-princess no tiene SMTP propio
tampoco — resuelve el envío de correo con EmailJS desde el navegador
(`emailjs.send()`), con una cola en Postgres
(`emails_sistema_pendientes`) que un poller del frontend
(`_enviarEmailsSistemaPendientes()`, cada 5 min con sesión admin/compras
abierta) despacha y confirma, con protección contra duplicados
(reserva atómica `en_proceso_desde`), reintentos infinitos
(`intentos`/`descartado_en`) y rotación automática entre hasta 3 cuentas
EmailJS al agotar cupo — un mecanismo real, maduro, con varios bugs de
producción ya encontrados y corregidos (duplicados, 413 por tamaño,
cupo agotado). Todo el HTML de sus correos se genera en Python y se
pasa entero al único template EmailJS que usa esa app
(`template_1zrv4ze`, campo `{{{{message}}}}` sin escapar) — no hace
falta gestionar una plantilla de EmailJS por tipo de correo. Confirmado
también: ambas apps ya comparten un secreto (`DALI_SSO_SECRET`,
desplegado en los dos servicios de Render) para el SSO del menú lateral
"Catálogo DALI" — reutilizable para autenticar esta nueva llamada sin
dar de alta nada nuevo en Render.

**Arquitectura elegida** (de las dos posibles, confirmada con Víctor):
un puente servidor-a-servidor. El backend de DALI, tras generar el HTML
con el mismo logo/colores que ya usa control-pedidos
(`backend/src/utils/emailHtml.js`, réplica de su `_email_header_html()`),
llama a un endpoint NUEVO en control-pedidos
(`POST /api/externo/dali-sap/emails-pendientes`, ver su propio
`CHANGELOG.md`) que inserta la fila directamente en SU
`emails_sistema_pendientes` — así el poller que YA existe allí la
despacha sin ningún cambio en su frontend, exactamente como describió
Víctor ("cuando alguien abra control de pedidos se lance"). La
alternativa descartada era que DALI montara su propia cola/EmailJS
independiente, replicando el patrón entero sin depender de
control-pedidos — más aislado entre apps, pero más trabajo y sin
aprovechar de verdad la infraestructura ya construida y ya depurada
allí, que es justo lo que pedía Víctor.

**Autenticación de la llamada**: se reutiliza `DALI_SSO_SECRET` (no un
secreto nuevo) firmando el cuerpo de la petición con HMAC-SHA256 —
mismo esquema que el token de SSO, pero sin caducidad corta ni jti (un
reintento aquí, como mucho, duplica una fila en la cola, no compromete
ninguna cuenta). Nueva variable `CONTROL_PEDIDOS_URL` con valor por
defecto ya puesto en `render.yaml`, y `DALI_SSO_SECRET` añadido por fin
a `backend/.env.example` (llevaba tiempo señalado como pendiente).

**Decisiones confirmadas con Víctor** antes de implementar:
- El cupo EmailJS se comparte con la cuenta activa de control-pedidos
  (sin cuenta dedicada aparte para DALI).
- Se mantiene un paso de revisión: "Generar email" sigue mostrando el
  texto editable de siempre; un nuevo botón "Encolar envío" (en
  `EmailProveedorModal.jsx`) es el que de verdad lo manda a la cola.
  Copiar/mailto se mantienen como alternativa manual, no se han quitado.
- La cabecera del correo (logo, colores) reutiliza literalmente la
  misma imagen que ya usa control-pedidos-princess (referenciada por URL,
  sin copiar el archivo a este repo) — nada de un diseño propio de DALI
  para este correo en concreto.

**Pendiente explícitamente aparcado por Víctor**: reutilizar este mismo
puente para la recuperación de contraseña (ver "Pendiente / siguientes
pasos" en `frontend/README.md`) — lo pidió como un segundo paso
deliberadamente posterior a este.

---

## v0.81 — Filtro previo por proveedor en la carga masiva (v1.18.19)

Víctor, con dos capturas del modal "Carga masiva de fichas técnicas":
"podriamos realizar un filtro previo en la carga masiva de las fichas e
imagenes? dar opcion a un proveedor o a todos, la idea es que si he
modificado fichas de un unico proveedor la aplicacion no tenga que
revisar el total innecesariamente".

El modal (`CargaMasivaModal.jsx`, compartido por las tres cargas
masivas — imagen/tecnica/seguridad, ver `CONFIG_POR_TIPO`) siempre pide
la carpeta RAÍZ que contiene la de cada proveedor, y hasta ahora
procesaba todas las que reconocía a la vez — cada archivo detectado
dispara, al subir, una comprobación de hash contra lo ya guardado
(`fetchHashDocumento`) más una consulta del artículo
(`fetchArticulo`), una petición de red por archivo. Si Víctor solo
había tocado la carpeta de un proveedor dentro de esa raíz compartida,
la carga masiva repasaba igualmente TODOS los proveedores presentes,
sin ninguna forma de acotarla.

Se añadió un desplegable "Proveedor a cargar" (Todos — por defecto,
comportamiento de siempre — o uno concreto del catálogo) antes del
selector de carpeta. Con un proveedor elegido, `clasificarArchivos`
ignora en silencio cualquier carpeta de OTRO proveedor real que
encuentre bajo la raíz — no genera fila para ella, así que no llega a
haber ninguna petición de red sobre esos archivos. Las carpetas que no
coinciden con ningún proveedor del catálogo (typos, carpetas sueltas)
se siguen avisando en la lista de "no reconocidas" exactamente igual
que antes, filtro activo o no — solo se silencian las que SÍ son un
proveedor válido pero no el elegido.

Probado en Node replicando `clasificarArchivos` con tres proveedores de
ejemplo y una carpeta sin reconocer de por medio: sin filtro salen las
tres filas (una por proveedor) y la carpeta rara avisada; filtrando a
uno solo, solo su fila, con la carpeta rara igual de avisada — las
otras dos, ni rastro (ni fila ni aviso). `vite build` sin errores.

- `frontend/src/components/admin/CargaMasivaModal.jsx`.

## v0.80 — Columna "Unidad" en el listado exportado para Hotel (v1.18.18)

Víctor pegó de nuevo el mismo correo de reclamación de documentación
que ya se había ajustado en v0.79 (confirmado luego que era porque aún
no lo había desplegado en Render) y, aparte, adjuntó un
`ARTICULOS_DALI.xlsx` real y un PDF de ejemplo del listado exportado
("Listado de asignaciones de ALCRUZ CANARIAS SL"), pidiendo: "EXPORTAR
PDF Y EXPORTAR EXCEL para ROL HOTEL, añadir columna entre PROVEEDOR Y
CANTIDAD con el valor de la columna C de este excel que es uno de los
dos que se importan desde admin".

Revisando el Excel adjunto, la columna C de `ARTICULOS_DALI.xlsx` es
"UNIDAD" (fila de cabecera en la fila 7: CODIGO, DESCRIPCION, UNIDAD,
FAMILIA, SUBFAMILIA, NATURALEZA, IGIC, PROVEEDOR, ACTIVO) — valores
como UNIDAD, KILOGRAMO o LITRO. Ese dato YA se guardaba al importar
(`articulos.unidad_dali`) y `fetchArticulosParaExport`
(`exportController.js`) ya lo traía en la consulta — pero
`columnasPdf()`, que define las columnas tanto del PDF como del Excel
(el Excel reutiliza exactamente las mismas), no lo incluía en ningún
sitio. Se añadió una columna "Unidad" entre "Proveedor" y "Cantidad",
solo en la rama de Hotel (`esAdmin === false`) — el listado de Admin no
tiene columna "Cantidad" (tiene "Activo" en su lugar), así que no
aplicaba ahí.

Antes de entregarlo se generaron un PDF y un Excel de prueba con datos
representativos del catálogo real (unidades UNIDAD/KILOGRAMO/LITRO) —
el PDF confirmó que la tabla, con la columna nueva, cabe en el ancho
útil de una A4 apaisada (780pt de las 781,89pt disponibles con el
margen de 30pt de cada lado) sin desbordar la página, y el Excel
confirmó que la cabecera y los valores quedan en el orden correcto.

- `backend/src/controllers/exportController.js` (`columnasPdf`,
  `ANCHO_POR_COLUMNA`).

## v0.79 — Redactado del email de reclamación: descripción junto al código, nombrado alternativo válido, ejemplo real por proveedor (v1.18.17)

Víctor, pegando el correo que genera el sistema para un proveedor real
(referencias 050805, 020204, 020205, 070403, 070406, 060101, 060404,
060435, con el aviso de ficha de seguridad y el ejemplo fijo "090102_
ARENQUE AL CURRY" al final): "seria conveniente que junto al codigo del
proveedor aparezca nuestra descripción del articulo para mejor
referencia, igualmente indicar que si los archivos llegan únicamente
cada uno con su codigo de articulo tambien es valido porque nuestro
sistema los asocia sin problema; el ejemplo del arenque es de este
proveedor, para cada proveedor utilizar un ejemplo de sus referencias
asisgnadas y faltantes".

Tres ajustes en `generarTextoEmail` (`EmailProveedorModal.jsx`):
- Cada línea de la lista de referencias sin ficha técnica pasa de
  mostrar solo `código de proveedor` a `código de proveedor —
  nombre del artículo`, para que quien lea el correo del lado del
  proveedor sepa de qué producto se trata sin tener que cruzarlo con su
  propio listado.
- Se añade una frase aclarando que un archivo nombrado ÚNICAMENTE con
  el código, sin la descripción detrás, también es válido — cierto
  desde que la carga masiva solo admite ese formato corto (v0.72/
  v1.18.12): "código_descripción" es cómodo para que el proveedor
  identifique el archivo, pero no obligatorio.
- El ejemplo de nombre de archivo del final ("Ejemplo: X_Y") deja de
  ser un texto fijo copiado del primer correo que se generó
  ("090102_ARENQUE AL CURRY", que no significaba nada para ningún otro
  proveedor) y pasa a construirse con una referencia real de CADA
  proveedor — prioriza una de las que le faltan de ficha técnica (ya
  que es la lista que se acaba de mostrar arriba), y si ninguna de sus
  referencias tiene código de proveedor guardado todavía, omite esa
  parte de la frase en vez de forzar un ejemplo inventado.

Al construir el ejemplo se coló un fallo de puntuación en la primera
versión (`. Ejemplo: X_Y Si el archivo llega…`, sin punto entre las dos
frases, ambas quedaban pegadas) — se detectó simulando la salida con
tres casos representativos en Node (proveedor con códigos, proveedor
sin ningún código guardado, proveedor al que solo le falta ficha de
seguridad) antes de entregar, y se corrigió añadiendo el punto que
faltaba. `vite build` sin errores.

- `frontend/src/components/admin/EmailProveedorModal.jsx`.

## v0.78 — Código de proveedor fijable para alternativos + todas las alternativas visibles a la vez (v1.18.16)

Víctor, justo después de recibir el cambio anterior (v0.77): "fijar el
código de proveedor de un proveedor no asignado si también por favor,
ficha completa y multiples alternetivas" — es decir, tres cosas juntas:
(1) poder fijar el código con el que un proveedor ALTERNATIVO identifica
el artículo, no solo el asignado; (2) que cada proveedor muestre su
"ficha completa" (código + imagen + las dos fichas); (3) poder ver
varias alternativas a la vez, no una por una a base de buscarlas.

Revisando el backend, la vía para fijar el código
(`PUT /admin/articulos/:id/codigo-proveedor`, `actualizarCodigoProveedor`
en `storageController.js`) ya aceptaba cualquier `id_proveedor` en el
body — nunca estuvo restringida al asignado. El límite estaba solo en
`ArticuloForm.jsx`: el campo "Código de proveedor" únicamente se
mostraba y se guardaba para `articulo.id_proveedor`, sin ninguna vía
para apuntar a otro. Y el diseño de v0.77, aunque ya dejaba ver/
gestionar la documentación de un proveedor alternativo, lo hacía de uno
en uno — tenías que escribir su nombre en el buscador para ver su
ficha, sin ningún sitio donde verlas todas juntas.

Rediseño de `ArticuloForm.jsx` en torno a "tarjetas de proveedor"
reutilizables (`CampoCodigoProveedor` para el código,
`TarjetaDocumentacion` para imagen + las dos fichas, cada una con su
propio estado de subida/error, así una tarjeta ocupada no bloquea las
demás):
- **Proveedor asignado** — su tarjeta completa arriba del todo, igual
  que antes pero ahora reutilizando el mismo componente que el resto.
- **Añadir o gestionar otro proveedor** — el buscador que ya había,
  ahora abre la ficha completa (código + imagen + fichas) de cualquier
  proveedor que se busque, sea nuevo o ya tenga algo guardado.
- **Documentación de otros proveedores guardada** — lista NUEVA: todas
  las alternativas que el artículo ya tenga (código y/o imagen y/o
  fichas), cada una en su propia tarjeta con borde propio, visibles
  todas a la vez sin tener que buscarlas.

De paso salió un hueco al hacer las pruebas: un proveedor con el código
ya fijado a mano pero sin ninguna imagen/ficha subida todavía no
generaba grupo en `GET /articulos/:id/fichas-por-proveedor`
(`obtenerFichasPorProveedor`, `articulosController.js`) — la unión de
proveedores se construía solo a partir de `fichas`/`imagenes`, nunca de
`codigos_proveedor`, así que ese código guardado quedaba invisible para
esta gestión (aunque estuviera bien guardado en la base). Se corrigió
añadiendo `codigos_proveedor` a esa unión, con su propio join a
`proveedores` para el nombre.

`node --check` en el backend y `vite build` sin errores.

- `backend/src/controllers/articulosController.js`
  (`obtenerFichasPorProveedor`),
  `frontend/src/components/admin/ArticuloForm.jsx` (reescrito),
  `frontend/src/styles/index.css` (clases `.adjuntos-titulo` y
  `.tarjeta-proveedor` nuevas).

## v0.77 — Gestión manual de documentación alternativa desde el panel de admin del artículo (v1.18.15)

Víctor, aportando dos capturas del panel de admin del artículo (código
de proveedor de OASISFISH SL, campo "Proveedor" y las tres subidas de
imagen/ficha técnica/ficha de seguridad): "en la ficha del artículo se
debería poder incluir documentación alternativa manualmente en el
mismo apartado admin". Esto conecta con lo que había explicado poco
antes en mayúsculas sobre cómo deben comportarse las fichas técnicas,
seguridad e imágenes: siempre asociadas a un proveedor, mostrando la
del proveedor asignado en cada momento, pero conservando en reserva la
de cualquier otro proveedor que haya subido algo alguna vez —
mostrando tantas como se vayan acumulando y sin borrar nunca esa
información alternativa cuando el proveedor asignado cambia.

Revisando `ArticuloForm.jsx` se confirmó que la mitad del trabajo ya
estaba hecha: el campo "Proveedor" (buscador con autocompletado) ya
permitía SUBIR una imagen o ficha para un proveedor distinto del
asignado, y quedaba correctamente en reserva sin tocar la del
asignado. Lo que faltaba era la otra mitad — VER y BORRAR esa reserva
desde el mismo sitio: los indicadores de "ya tiene imagen guardada" /
"ver PDF ya guardado" y los botones "Eliminar" leían siempre el estado
cargado al abrir el panel (`fetchFichas` + `articulo.url_imagen`), que
es siempre el del proveedor ASIGNADO — cambiar el campo "Proveedor"
del buscador no cambiaba lo que se veía ni lo que se podía borrar, así
que no había manera de gestionar la reserva de otro proveedor sin salir
de la ficha.

Arreglo en tres capas:
- `backend/src/controllers/storageController.js`: `DELETE
  /admin/articulos/:id/imagen` y `DELETE
  /admin/articulos/:id/fichas/:tipo` aceptan ahora un `id_proveedor`
  opcional por query string (vía el `resolverIdProveedor` que ya
  existía para las subidas) — sin el parámetro se comportan exactamente
  igual que antes (proveedor asignado), así que ningún llamador
  existente se ve afectado.
- `frontend/src/services/api.js`: `eliminarImagenArticulo` y
  `eliminarFichaArticulo` aceptan un `idProveedor` opcional y lo añaden
  como `?id_proveedor=...` si se indica.
- `frontend/src/components/admin/ArticuloForm.jsx`: en vez de guardar
  el estado de imagen/fichas en variables locales que solo se rellenan
  al abrir el panel, ahora pide `GET /articulos/:id/fichas-por-proveedor`
  (el mismo endpoint que ya usaba el panel de consulta para "Ver
  alternativas de otros proveedores") y muestra en vivo la imagen/
  fichas del proveedor que esté escrito en el buscador en cada momento
  (o el asignado, si se deja en blanco), con su propio "sin imagen/
  ficha guardada para este proveedor" cuando no tiene nada todavía. El
  aviso de que el artículo tiene documentación en reserva de otros
  proveedores ahora lista sus nombres como botones que rellenan el
  buscador directamente, para no tener que teclearlos a mano. Subir o
  borrar cualquier adjunto vuelve a pedir esos datos para que el panel
  quede siempre al día sin recargar la ficha entera.

`node --check` en el backend y `vite build` sin errores.

- `backend/src/controllers/storageController.js`,
  `frontend/src/services/api.js`,
  `frontend/src/components/admin/ArticuloForm.jsx`,
  `frontend/src/styles/index.css` (clase `.btn-link` nueva, para los
  nombres de proveedor del aviso).

## v0.76 — Un mismo código de proveedor en varios DALI dejaba de emparejarse con cualquiera de ellos (v1.18.14)

Víctor: "cuando un mismo proveedor tiene varios DALI con un mismo
codigo proveedor, la aplicacion no asigna la documentacion a ninguna,
ejemplo 4029017 aosicado a DALI 24004 y 24195; existen casos como
este, es un mismo producto quimico en diferentes formatos, pero la
documentacion es la misma", con una captura de la ficha del 24004
(ASEPCOL PLUS BOTELLA 1 LITRO, proveedor PROQUIMIA SA, código
proveedor 4029017).

Esto ya lo había anotado como riesgo pendiente al hacer el cambio a
"código de proveedor único" de v0.72/v1.18.12: `codigos_proveedor`
solo tiene restricción de unicidad por (id_articulo, id_proveedor) —
nunca por (id_proveedor, codigo) — así que un mismo proveedor SIEMPRE
pudo tener el mismo código en más de un artículo, y es un caso
legítimo tal como confirma Víctor (mismo producto, formatos distintos,
misma documentación). El fallo estaba en
`buscarArticuloPorCodigoProveedor` (`storageController.js`): la
consulta pedía una única fila (`.maybeSingle()`), que lanza error en
cuanto hay más de una — ese error 500 lo convertía `api.js` en
silencio en `{ encontrado: false }` ("si falla la consulta, se trata
como no encontrado"), así que el archivo caía en "no se encontró
ningún artículo" y no se subía a NINGUNO de los dos DALI, ni siquiera
al que hubiera sido inequívoco si el otro no existiera.

Arreglo en dos capas:
- El endpoint ya no exige una fila única: agrupa por `id_articulo`,
  resuelve todos los código DALI que comparten ese proveedor+código y
  los devuelve en `codigos_dali` (array, orden ascendente) —
  `codigo_dali` (singular) se mantiene por compatibilidad, es solo el
  primero.
- `CargaMasivaModal.jsx` sube el mismo archivo a cada uno de los
  código DALI devueltos, no solo al primero. La columna "Código DALI"
  de la tabla muestra todos juntos cuando hay más de uno (p.ej. "24004,
  24195"). Si alguno de los artículos fallara mientras el resto va
  bien, la fila entera se marca en error con el detalle de cada
  artículo (para que se revise a mano en vez de darse por buena a
  medias sin que Víctor se entere de que uno de los dos se quedó sin
  documentación).

Probado con datos simulados replicando el caso PROQUIMIA exacto
(agrupación/orden del backend) y los cinco escenarios de combinación
de resultados de una fila (único artículo, varios con éxito, uno que
falla entre varios, todos sin cambios, mezcla ok+sin_cambios) — sin
acceso de red a Supabase en este entorno, verificado con réplicas
mínimas de la lógica en Node. `vite build` sin errores.

- `backend/src/controllers/storageController.js`
  (`buscarArticuloPorCodigoProveedor`), `frontend/src/services/api.js`,
  `frontend/src/components/admin/CargaMasivaModal.jsx`.

## v0.75 — "Ver alternativas de otros proveedores" también enseña la imagen, no solo las fichas (v1.18.13)

Víctor, a raíz de la pantalla de "Fusionar proveedores" (v0.68):
"LAS FICHAS TECNICAS, SEGURIDAD E IMAGENES SE ASOCIAN SIEMPRE A UN
PROVEEDOR Y SON LAS QUE SE MUESTRAN EN LA FICHA SEGUN EL PROVEEDOR
ASIGNADO AL DALI, CUANDO UN PROVEEDOR ASIGNADO CAMBIA, ESTA
DOCUMENTACION SE DEBERIA MANTENER ASOCIADA AL PROVEEDOR PERO
OFRECERLA COMO ALTERNATIVA EN LA FICHA EN EL APARTADO AVILITADO PARA
ESTO; NUNCA BORRAR ESTA INFO ALTERNATIVA Y MOSTRAR TANTAS COMO SE
VAYAN ACUMULANDO".

Revisando el código antes de tocar nada: casi todo lo que pedía ya
estaba construido, de una petición suya anterior (2026-08-17/
2026-08-20, ver `schema.sql` y `articulosController.js`). Cambiar el
proveedor asignado a un artículo (`actualizarArticulo`) solo toca la
columna `id_proveedor` — nunca ha tocado ninguna fila de
`fichas`/`imagenes` de ningún proveedor, así que la documentación de
cualquier proveedor que alguna vez subió algo se queda guardada "en
reserva" para siempre, y el botón "Ver alternativas de otros
proveedores" de `ArticuloDetail.jsx` ya existía, agrupando por
proveedor todo lo que hubiera acumulado.

El único hueco real: ese panel de alternativas (`obtenerFichasPorProveedor`)
solo devolvía fichas técnica/seguridad — la imagen se quedaba fuera a
propósito ("Solo incluye fichas técnica/seguridad (no imagen)", decía
el propio comentario del código), aunque estuviera guardada igual de
segura que las fichas. Se completa: el endpoint consulta también
`imagenes` y construye los grupos por proveedor a partir de la UNIÓN de
quien tenga ficha o imagen (un proveedor puede tener solo imagen, sin
ninguna ficha, y aparece igual como grupo — antes se habría perdido
del todo). `ArticuloDetail.jsx` pinta una miniatura (mismo criterio
visual que `.detail-imagen`, más pequeña) con enlace a tamaño completo
dentro de cada grupo de alternativas.

Probado con datos simulados: proveedor con ficha+imagen, proveedor
solo con ficha, proveedor SOLO con imagen (el caso que antes se perdía)
— los tres se agrupan y ordenan bien (asignado primero, resto
alfabético). `vite build` sin errores.

- `backend/src/controllers/articulosController.js`
  (`obtenerFichasPorProveedor`), `frontend/src/services/api.js`,
  `frontend/src/components/ArticuloDetail.jsx`,
  `frontend/src/styles/index.css`.

## v0.74 — Limpieza completa de fichas/imágenes en Supabase antes de recargar todo desde cero

Víctor: "vamos a limpiar toda la base y cargar todo de nuevo, para
limpiar duplicidades y posibles archivos cargados incorrectamente...
me puedes indicar para realizar un borrado completo de fichas
seguridad, tecnicas e imagenes en Supabase?" — a raíz de haber cerrado
el cambio a "código de proveedor único" (v0.72) y el script de
renombrado (v0.73), quiso empezar de cero en vez de ir corrigiendo
carpeta a carpeta.

No es un cambio de código: se le indicó el procedimiento para que lo
ejecute él mismo (borrado de datos en producción, fuera de lo que se
hace sin que el propio Víctor lo lance). Antes de dar los pasos se le
preguntó con AskUserQuestion si la limpieza debía incluir también
`codigos_proveedor` — eligió que NO, para no tener que volver a
registrar a mano los códigos ya capturados; la carga masiva podrá
seguir encontrando cada artículo por su código en cuanto vuelva a
subir los archivos. Se le dieron dos pasos independientes (borrar solo
uno deja al otro huérfano): `DELETE` de las tablas `fichas`/`imagenes`
+ reseteo de las dos columnas obsoletas de `articulos`
(`url_imagen`, `codigos_proveedor_adjuntos`) que dependían del sistema
antiguo, y vaciar los buckets de Storage `articulo-fichas` /
`articulo-imagenes` desde el propio panel de Supabase (no por SQL
contra `storage.objects`, que puede dejar archivos huérfanos sin
borrar de verdad). Con aviso de hacerlo en un momento de poco tráfico
y de comprobar backup antes, al ser irreversible.

## v0.73 — Script aparte para renombrar en bloque archivos en formato antiguo

Víctor, con un listado real de `AHUMADOS CANARIOS SA\FICHAS TECNICAS`
(29 archivos, la mayoría en el formato de tres códigos): "tengo varias
carpetas ya en este formato, podemos crear un script python para que
compruebe todos los archivos de la misma carpeta donde se ejecute y
busque este patrón existente, una vez encontrado debera eliminar los 2
primeros codigos separados por _ y dejar codigo unico el tercero
separado del resto por _".

No es parte de la app — es una herramienta aparte que no vive en este
repositorio, entregada como zip (`corregir_nombres_fichas.py` +
`CORREGIR_NOMBRES.bat` + `LEEME.txt`), siguiendo el mismo patrón de
seguridad que otros scripts previos entregados a Víctor: simulación
por defecto (no toca nada hasta que se confirma con "S"), log a
fichero además de a pantalla, recursivo desde la carpeta donde se
ejecuta (para poder cubrir de una vez varias carpetas de proveedor
colgando de una carpeta superior), detección de colisiones por
carpeta, y restringido a extensiones .pdf/.jpg/.jpeg/.png/.webp.
Probado con una carpeta sintética que reproduce los tres ejemplos
reales de Víctor, un archivo ya en formato nuevo (para comprobar
idempotencia), una colisión provocada a propósito y una subcarpeta
(para probar la recursividad).

El `.bat` de la primera entrega se quedó colgado en el equipo de
Víctor sin mostrar ningún mensaje después del primer aviso. Causa más
probable: la comprobación de Python (`where python`) puede encontrar
como "instalado" el alias que Windows crea hacia la Microsoft Store
cuando Python no está instalado de verdad, sin que eso sirva para
ejecutar nada — y el `.bat` original, además, llevaba tildes/"¿" que
se veían como caracteres corruptos en la consola (posible lío de
codificación, aunque no necesariamente la causa del cuelgue).
Reescrito en ASCII puro, comprobando de verdad `python`/`py`/`python3`
con `--version` en vez de solo `where`, con `cd /d "%~dp0"` al
principio para que la búsqueda siempre parta de la carpeta del propio
`.bat` pase lo que pase, y con un mensaje explícito de diagnóstico si
no encuentra ningún intérprete que funciona de verdad (incluyendo el
aviso del truco de la Microsoft Store).

## v0.72 — Carga masiva: código de proveedor como único formato admitido (v1.18.12)

Continuación directa de v0.73 (el diagnóstico y el script de
renombrado son posteriores en este relato porque se cuentan primero,
pero la decisión de simplificar el formato surgió aquí, antes de que
el script terminara de resolverse). Tras el diagnóstico de la carpeta
de BIMBO (18 de 26 archivos mal detectados por el formato antiguo),
Víctor preguntó, para curarse en salud: "para evitar mas problemas, la
carga de fichas e imagenes seria mas segura si el unico codgio a
buscar fuera el del proveedor? estando asociado siempre en listado a
un DALI ¿tendria algun fallo u omision?". Se le dio una valoración
honesta (sin fallos estructurales siempre que el código de proveedor
esté pre-registrado; el único requisito nuevo es que la carga masiva
de código de proveedor por Excel, ya existente, se use primero) y
confirmó: "si vamos a realizar el cambio, recuerda que el codigo del
proveedor puede ser alfanumerico y el formato quedaria 'codigo_nombre'
o 'cosigo nombre' y el nombre puede tener espacios y signos" — dato
importante porque `parsearCodigoProveedorDeNombre` ya cumplía
justo esa forma sin cambios de lógica, solo hacía falta quitar el
formato competidor.

Se elimina por completo `PATRON_NOMBRE_COMPLETO` y
`parsearNombreArchivo()` (el formato de tres códigos
`codigoDali_codigoSap_codigoProveedor_nombre`); `parsearCodigoProveedorDeNombre`
pasa a ser el único camino en las tres cargas masivas. Como
consecuencia, cualquier archivo que siga en el formato antiguo deja de
reconocerse hasta que se renombre (de ahí el script de v0.73) y el
código de proveedor de cada artículo tiene que estar ya grabado de
antemano. Verificado con las 26 rutas reales de BIMBO y varios
ejemplos de código alfanumérico; `vite build` sin errores.

- `frontend/src/components/admin/CargaMasivaModal.jsx`.

## v0.71 — Usuarios: baja definitiva y email editable (v1.18.11)

Víctor, con capturas de "Editar usuario" para Domingo Vega mostrando
el campo Email deshabilitado: "para el apartado de usuarios, no me
deja eliminar solo desactivar, y tampoco puedo introducir correos
electrónicos con caracteres, por ejemplo tendría que poner
'chefa&b.canarias@princess-hotels.com' y no me deja." Dos peticiones
independientes en un mismo mensaje.

Email: el campo estaba deshabilitado a propósito tras el alta (no
había forma de corregirlo después). Se habilita también en edición,
con un aviso justo debajo explicando que las cuentas que entran por
SSO desde Control de Pedidos necesitan el cambio también allí, o la
próxima vez que entren por ese camino se les creará una cuenta nueva
con el email antiguo en vez de reconocer la existente.

Baja definitiva: hasta ahora `usuarios` solo se podía desactivar
(`activo = false`), nunca borrar de verdad. Comprobado en `schema.sql`
que `usuarios` no tiene ninguna tabla que dependa de ella por FK, así
que un borrado real no deja huérfanos. Nuevo
`DELETE /admin/usuarios/:id`, con las mismas dos salvaguardas que ya
usa el resto de la app para bajas sensibles: no se puede auto-borrar
la propia cuenta, y no se puede borrar el último administrador activo
que queda (cuenta los demás admins activos antes de permitirlo).

Al integrar el botón "Eliminar usuario" con su `ConfirmDialog` dentro
de `UsuarioForm.jsx` se detectó (no reportado por Víctor, revisando el
propio cambio antes de entregarlo) que `ConfirmDialog.jsx` no marcaba
`type="button"` en sus botones — sin consecuencias en los sitios donde
ya se usaba (paneles sueltos con `<div>`, sin `<form>` de por medio),
pero al quedar ahora anidado dentro del `<form>` real de
`UsuarioForm.jsx`, pulsar "Cancelar" en el diálogo de confirmación
habría disparado sin querer el `onSubmit` del formulario (guardar los
cambios) en vez de limitarse a cerrar el diálogo. Corregido antes de
que llegara a pasar.

- `frontend/src/components/admin/UsuarioForm.jsx`,
  `frontend/src/components/admin/ConfirmDialog.jsx`,
  `frontend/src/components/admin/AdminUsuarios.jsx`,
  `frontend/src/services/api.js`,
  `backend/src/controllers/usuariosController.js`,
  `backend/src/routes/admin.js`.

## v0.70 — Carga masiva: el botón seguía diciendo "Cancelar" al terminar (v1.18.10)

Víctor pegó dos capturas de una "Carga masiva de fichas técnicas" ya
terminada (1946 archivo(s) detectado(s) · 411 sin cambios · 1535 con
error) donde el único botón disponible seguía diciendo "Cancelar":
"una vez terminado devería decir algo como finalizado y salir o algo
que no sea CANCELAR que da equívoco. Revisar todas estas pantallas de
carga masiva de archivos para que todo cumpla la expectativa." Al
preguntar si el arreglo debía cubrir las tres cargas masivas (imagen/
técnica/seguridad), confirmó que sí — pero las tres comparten un único
componente (`CargaMasivaModal.jsx`, `CONFIG_POR_TIPO`), así que un
solo arreglo ya las cubre todas.

La detección de "terminado" tampoco era correcta:
`resumen.ok + resumen.error === resumen.total` no contaba las filas
"sin cambios" (ya estaban igual, no hacía falta volver a subirlas)
como parte del total ya procesado, así que una carga con muchas filas
"sin cambios" nunca se daba por terminada. Se corrige a
`resumen.pendiente === 0`; se añade un banner de resumen (✓ verde si
no hubo errores, ⚠ si los hubo) al terminar, el botón pasa a decir
"Cerrar" en vez de "Cancelar", y tanto el botón como la ✕ de cerrar se
deshabilitan mientras la carga sigue en curso, para que no se pueda
cerrar a medias por error pensando que ya ha terminado.

- `frontend/src/components/admin/CargaMasivaModal.jsx`.

## v0.69 — Reescritura del email de "Documentación pendiente" (v1.18.9)

Víctor pegó su propio formato deseado para el email de proveedores con
documentación pendiente, junto con el que la aplicación generaba en
ese momento para OASISFISH, pidiendo el cambio al primero: una lista
de viñetas solo con los códigos a los que les falta ficha técnica,
seguida de avisos genéricos (no repetidos código a código) recordando
la ficha de seguridad y la imagen cuando hagan falta, las
instrucciones de nomenclatura del archivo, y un cierre fijo.

`generarTextoEmail` (`EmailProveedorModal.jsx`) se reescribe entera:
filtra `grupo.articulos` por `falta_ficha_tecnica` para la lista de
viñetas (solo si hay alguna), construye un array de avisos con frases
condicionales para seguridad/imagen (cada una elige su palabra de
apertura — "Les recordamos"/"Asimismo..." o "Necesitamos"/
"Adicionalmente..." — según si ya hay contenido previo en el mensaje),
añade siempre el párrafo de convención de nombres y el cierre, y une
todo con saltos de línea dobles entre "Buenos días," y "Un saludo,".
Verificado reconstruyendo en un script Node aparte los datos reales de
OASISFISH que pegó Víctor (41 códigos "solo seguridad" + 14 "técnica y
seguridad") y comparando el resultado contra su ejemplo, línea a
línea — coincide exactamente, incluida la estructura de párrafos en
blanco.

(Se olvidó adjuntar el archivo modificado en la primera respuesta —
Víctor avisó con "no veo archivos adjuntos" — corregido enviándolo
aparte.)

- `frontend/src/components/admin/EmailProveedorModal.jsx`.

---

## v0.68 — Nueva pantalla "Fusionar proveedores": limpia duplicados por cambio de nombre en SAP (v1.18.8 — pendiente de desplegar)

Víctor mandó dos capturas de la ficha del artículo 29985 (BIMBO BURGER
S/GLUTEN RUSTICA PAQ. 2 UNID., proveedor "BIMBO DONUTS CANARIAS SLU",
código de proveedor 512305) donde el desplegable "Ver alternativas de
otros proveedores" mostraba "BIMBO DONUTS CANARIAS S.L.U — código
512305" como si fuera OTRO proveedor con su propia ficha técnica —
mismo código, nombre casi idéntico (solo cambian los puntos). Pregunta:
"cuando un proveedor es renombrado el sistema guarda la info del
proveedor nombre anterior como otro proveedor, como puedo borrar esta
info?".

Causa raíz confirmada leyendo `resolverDimensionSimple`
(`backend/src/utils/dimensiones.js`), usada desde
`importController.js` para resolver `articulos.PROVEEDOR` contra la
tabla `proveedores`: es un `get_or_create` por nombre EXACTO
(`.in(columnaNombre, unicos)` + `upsert(..., { onConflict:
columnaNombre })`), sin ningún tipo de normalización de mayúsculas,
tildes o puntuación — a diferencia de `CargaMasivaModal.jsx`, que sí
tiene su propio `normalizar()` para este mismo tipo de problema (ver
HISTORIAL v0.?? / 2026-08-18, "17 proveedores del catálogo llevaban un
punto final que su carpeta no tenía"). Si SAP cambia el nombre de un
proveedor — aunque sea solo puntuación, "SLU" → "S.L.U." — el texto ya
no coincide con la fila existente, se da de alta una fila NUEVA en
`proveedores`, y los artículos pasan a apuntar a esa fila nueva en la
siguiente importación. La fila VIEJA se queda huérfana: sus
`imagenes`/`fichas`/`codigos_proveedor` (que siguen enlazados a su id
antiguo) no se tocan, y como el artículo ya no la tiene como proveedor
asignado, aparecen mostrados como documentación "de otro proveedor" en
vez de reconocerse como la misma.

Pregunté con AskUserQuestion dos cosas: qué hacer con el caso BIMBO
concreto ahora mismo, y si quería una solución duradera para cuando
vuelva a pasar. Víctor eligió: fusionar y borrar el proveedor viejo
para BIMBO, y construir una herramienta de fusión reutilizable en vez
de normalizar la comparación de la importación (esta segunda opción no
se descartó por mala idea, sino porque Víctor prefirió no tocar el
comportamiento de la importación en sí — normalizar ahí evitaría
duplicados por cambios MENORES de puntuación, pero seguiría sin
resolver un cambio de nombre real, así que la herramienta de fusión
hacía falta de todos modos).

Construida como una pantalla nueva de Administración, "Fusionar
proveedores" (`AdminProveedores.jsx`): se eligen dos proveedores
existentes de un desplegable con autocompletado (mismo patrón
`<input list>` + `<datalist>` que ya usa `ArticuloForm.jsx` para el
mismo propósito) — "origen" (el que desaparece) y "destino" (el que se
queda) — y antes de poder fusionar se pide un resumen de cada uno
(`GET /admin/proveedores/:id/resumen`, 4 consultas de solo conteo) que
se muestra en una tabla comparativa, con un aviso si el origen tiene
MÁS artículos asignados que el destino (señal de tenerlos al revés).
Solo entonces se puede confirmar, con un `ConfirmDialog` que repite
ambos nombres y advierte que no se puede deshacer.

El backend (`fusionarProveedores`, `proveedoresController.js`) traslada
al destino todo lo que cuelga del origen:
- `articulos.id_proveedor`: se reasignan todos sin condiciones.
- `codigos_proveedor`, `imagenes`, `fichas`: van una fila por
  (artículo[, tipo]) y proveedor (`unique` en `schema.sql`) — si el
  destino YA tenía su propia fila para ese mismo artículo, se conserva
  la del destino y se descarta la del origen, nunca al revés. Para
  `codigos_proveedor`, si el código descartado era distinto al que se
  conserva, se informa como "conflicto" en la respuesta (mismo
  criterio de "nunca pisar en silencio" que `guardarCodigoProveedor`
  en `storageController.js`) para que Víctor lo revise a mano si hace
  falta. El archivo en Storage de una imagen/ficha trasladada NO se
  renombra — decisión deliberada: la ruta guardada sigue sirviendo tal
  cual esté (el backend nunca la recalcula a partir del id_proveedor al
  LEER, solo al volver a SUBIR algo — `subirImagenArticulo`/
  `subirFichaArticulo` ya limpian solas la ruta vieja el día que
  alguien suba algo nuevo para ese artículo+proveedor), así que mover
  archivos en Storage durante la fusión habría sido complejidad extra
  sin ninguna ganancia real.
- `proveedores.email`: si el destino no tenía y el origen sí, se copia.
- Por último se borra la fila del proveedor de origen — para entonces
  ya no debería quedar ninguna FK apuntándole.

Si la petición falla a mitad (p.ej. un error de red tras mover
artículos pero antes de llegar a fichas), no hace falta deshacer nada
a mano: cada paso solo mueve lo que TODAVÍA sigue en el origen, así
que repetir la fusión con los mismos origen/destino retoma justo donde
se quedó, sin duplicar trabajo ni pisar nada ya movido.

No hace falta ninguna migración de base de datos — la funcionalidad
trabaja solo con tablas que ya existían (`proveedores`, `articulos`,
`imagenes`, `fichas`, `codigos_proveedor`), sin cambiar el esquema.

Verificado con `node --check` (backend/src/controllers/
proveedoresController.js, backend/src/routes/admin.js), `npx vite
build` (55 módulos, sin errores) y un render con Playwright de un HTML
estático usando el CSS compilado real, con datos de ejemplo del propio
caso BIMBO, para comprobar visualmente la tabla comparativa, los
avisos y el diálogo de confirmación.

---

## v0.67 — Carga masiva: códigos de proveedor alfanuméricos o solo letras dejaban de subir imagen/fichas (v1.18.7 — pendiente de desplegar)

Víctor mandó una captura de la ficha del artículo 24010 (FILM 50 CM. ESTIRABLE
- PALETIZAR, proveedor SISTEMAS CANARIOS DE CONTROL SL, código de proveedor
"EFIL") junto con el listado real de su carpeta de fichas técnicas de ese
proveedor (`dir` de PowerShell): `EFIL.pdf`, `A40350.pdf`, `AKHD.pdf`,
`B02C.pdf`, `V004.pdf`, `L51.pdf`... y dijo: "no se están leyendo las fichas e
imágenes cuando el codigo del proveedor es alfanumérico o solo alfa".

Causa: en `CargaMasivaModal.jsx`, cuando un archivo no sigue el formato
completo `codigoDali_codigoSap_codigoProveedor_nombre` (que es el caso de
estos archivos — vienen nombrados SOLO con el código de proveedor, formato
corto añadido en la v1.18 a petición de Víctor, ver v0.?? de más abajo /
2026-08-21), se prueba el formato alternativo
`parsearCodigoProveedorDeNombre`, que interpreta el primer trozo del nombre
(antes del primer espacio o "_") como el código. Esa función exigía que el
candidato tuviera al menos un dígito
(`if (!candidato || !/\d/.test(candidato)) return null;`), pensado
originalmente para no confundir con un nombre de archivo cualquiera sin
ningún código (p.ej. "catalogo.pdf"). Pero con códigos de proveedor reales
que son solo letras — "EFIL", "AKHD" — esa comprobación los descartaba
directamente: la fila ni siquiera llegaba a intentar la búsqueda contra
`codigos_proveedor`, se marcaba como error de formato y ni la imagen ni la
ficha se subían.

Se comprobó que la protección del dígito no hacía falta: la búsqueda real
(`buscarArticuloPorCodigoProveedor`, backend) ya exige una coincidencia EXACTA
del código contra lo guardado en `codigos_proveedor` — un archivo que de
verdad no trae ningún código de proveedor (p.ej. "BOLSA PAN.pdf",
"envase alumino.pdf", que también aparecían en la misma carpeta real de
Víctor) simplemente no encuentra artículo con ese "código" y cae en el mismo
aviso de error de siempre ("no se encontró ningún artículo con código de
proveedor... revísalo a mano"), sin riesgo de emparejar mal un archivo. Se
quitó la exigencia del dígito en `parsearCodigoProveedorDeNombre`
(`frontend/src/components/admin/CargaMasivaModal.jsx`) — ahora "EFIL.pdf",
"AKHD.pdf", "A40350.pdf", "V004.pdf", "L51.pdf" y similares se reconocen
igual que los códigos numéricos.

Verificado con un script Node aparte reproduciendo la función con los
nombres reales de la carpeta de Víctor (antes y después del cambio) y con
`npx vite build` (54 módulos, sin errores).

---

## v0.66 — Documentación faltante: código de proveedor + generar email de reclamación (v1.18.6 — pendiente de desplegar)

Víctor: "Podemos de alguna manera realizar resúmenes de documentación
faltante por proveedor (fichas técnicas, seguridad e imágenes),
referenciada por su código interno ya que dali y SAP no les interesa.
La idea es poder enviar correo electrónico a cada proveedor
solicitando la documentación faltante."

**Punto de partida**: el resumen por proveedor YA existía (pantalla
"Documentación faltante", `AdminDocumentacionFaltante.jsx` /
`documentacionController.js`, ver entregas anteriores no cubiertas en
detalle aquí) — agrupado por proveedor, con exportación a Excel. Lo que
faltaba era referenciar cada artículo con el código PROPIO del
proveedor en vez del código DALI (que a un proveedor externo no le
dice nada), y la posibilidad de generar el email de reclamación.

**Decisión con Víctor sobre el envío de email**: antes de tocar nada
se le preguntó cómo quería que funcionara el envío, porque no hay
ninguna integración de correo configurada en el backend (mismo punto
aparcado que "recuperar contraseña por email", pendiente de que elija
proveedor de email/SMTP) y añadir eso habría sido una tarea bastante
más grande con una decisión suya de por medio. Eligió la opción
inmediata: generar el texto del email (asunto + cuerpo) y enviarlo él
mismo desde su propio correo, sin montar ninguna integración de envío
todavía. También eligió ir añadiendo el email de cada proveedor él
mismo desde la propia app, a su ritmo, en vez de precargarlos todos de
golpe desde un Excel.

**Arreglo**:
- Migración `2026-08-25_email_proveedor.sql`: añade `email` (opcional)
  a `proveedores` — no existía ningún dato de contacto hasta ahora.
- `documentacionController.js`: `calcularDocumentacionFaltante` ahora
  también resuelve, por artículo, el código con el que el proveedor
  ASIGNADO lo identifica (tabla `codigos_proveedor`, mismo patrón que
  imagen/fichas: solo interesa el código del proveedor asignado, no el
  de otros proveedores "en reserva"). Los grupos por proveedor pasan a
  agruparse por `id_proveedor` (no solo por nombre) para poder llevar
  también su email. El Excel exportado gana la columna "Código
  proveedor" junto a "Código DALI".
- `proveedoresController.js` / `admin.js`: nuevo endpoint
  `PUT /admin/proveedores/:id/email` para guardar (o borrar) el email
  de un proveedor, con una validación de formato básica.
- `AdminDocumentacionFaltante.jsx`: nueva columna "Código proveedor" en
  la tabla (con "—" cuando no está capturado todavía; la búsqueda
  también encuentra por este código); nueva barra por proveedor con
  editor del email de contacto y botón "Generar email".
- `EmailProveedorModal.jsx` (nuevo componente): construye un asunto y
  un cuerpo de email listando lo que le falta a cada artículo,
  referenciado con "vuestro código X" cuando existe o con el nombre del
  artículo (pidiendo explícitamente el código) cuando no — así el email
  también sirve para ir completando ese dato con el tiempo. Editable
  antes de usarlo; botón "Copiar" (portapapeles) siempre disponible, y
  si el proveedor tiene email guardado, además un enlace mailto: para
  abrirlo directamente en el cliente de correo, con aviso si el texto
  es muy largo (algunos clientes recortan cuerpos largos en mailto:).
  No se manda nada desde la app.
- `index.css`: nueva barra `.documentacion-grupo-toolbar`, reutiliza el
  patrón de `.codigo-proveedor-editor` para el editor de email, nuevo
  `.email-modal-box` (variante más ancha de `.confirm-box`, con el
  filo en `--brass` en vez de `--wine` por no ser una acción
  destructiva), y estilo de `textarea` dentro de `.field` (no existía
  ninguno hasta ahora). Se añadió también `text-decoration: none` y
  `display: inline-flex` a `.btn` porque es la primera vez que se usa
  esa clase sobre un `<a>` (el enlace mailto:), no solo sobre
  `<button>`.
- `backend/package.json` y `frontend/package.json` suben a 1.18.6.
- **Verificación**: `npx vite build` sin errores. `node --check` sobre
  los tres archivos de backend tocados. Comparativa visual con
  Playwright (CSS real compilado, datos sintéticos realistas) de: la
  tabla con la columna nueva y la barra de email, el estado de edición
  del email, y el modal "Generar email" en sus dos variantes (con y
  sin email guardado) — confirma alineación correcta del botón mailto:
  junto a los demás botones y legibilidad del texto generado.
- **Pendiente para Víctor antes de desplegar**: ejecutar la migración
  `2026-08-25_email_proveedor.sql` en el SQL Editor de Supabase.
- **Nota**: el envío automático de correo desde la app (para más
  adelante, si Víctor lo quiere) sigue pendiente de que elija un
  proveedor de email — mismo punto que la recuperación de contraseña,
  ver lista de pendientes.

---

## v0.65 — Imagen de la ficha de artículo: ajuste corregido para aprovechar el espacio al máximo (v1.18.5 — pendiente de desplegar)

Tras ver la comparativa de v0.64, Víctor: "la idea es que la imagen se
ajuste al maximo al espacio pero siempre sin distorcionar la misma".

**Diagnóstico**: el arreglo de v0.64 (`object-fit: contain` dentro de
un recuadro FIJO — ancho 100% del panel, alto de hasta 220px) sí
cumplía "sin distorsionar" y "sin recortar", pero no "al máximo del
espacio": al forzar el mismo recuadro grande para cualquier foto,
"contain" encogía la imagen para que cupiera dentro y dejaba de fondo
(--surface-sunk) un margen más amplio de lo necesario en los lados
cuando la foto no compartía la proporción del recuadro — la foto se
veía pequeña dentro de un marco de sobra. Se verificó el efecto con una
segunda comparativa (Playwright, foto alta tipo botella + foto ancha
tipo bandeja): en la versión de v0.64 la foto alta quedaba con mucho
margen lateral visible.

**Arreglo**: en vez de fijar el tamaño del recuadro y encoger la foto
dentro con "contain", se deja que el propio elemento `<img>` se
dimensione según la foto real: `width: auto; height: auto` con los
límites `max-width: 100%` (ancho del panel) y `max-height: 220px` (el
mismo tope de antes). Así la foto usa el máximo espacio disponible en
la dimensión que le corresponda — una foto alta llega hasta los 220px
de alto (con menos ancho si le corresponde), una foto ancha llega hasta
el 100% del ancho — sin recortar nunca nada (nada queda fuera del
encuadre) y sin distorsionar nunca (las proporciones originales de la
foto no cambian). Se centra con `margin: 0 auto` para que quede
equilibrada cuando no ocupa el ancho completo. `object-fit: contain` se
deja puesto como salvaguarda adicional (no debería activarse nunca con
este dimensionado, pero no estorba). `frontend/src/styles/index.css`.

- `backend/package.json` y `frontend/package.json` suben a 1.18.5 (ver
  convención de v0.58) — sin cambios de código en el backend esta vez.
- **Verificación**: `npx vite build` sin errores. Nueva comparativa
  visual con Playwright, esta vez con DOS fotos sintéticas (una alta
  tipo botella, una ancha tipo bandeja) para confirmar ambos casos:
  la foto alta ahora usa un recuadro ajustado a su propio ancho (mucho
  menos margen que en v0.64), y la foto ancha sigue llenando el ancho
  completo del panel como antes. Captura enviada a Víctor para
  confirmación visual directa.

---

## v0.64 — Imagen de la ficha de artículo ya no se recorta (object-fit: contain) (v1.18.4 — pendiente de desplegar)

Víctor: "las imágenes que se muestran en la ficha del articulo, se puede
hacer para que se ajuste al espacio y no se quede nada fuera?
¿sistorciona esto la imagen?" (se entiende "¿distorsiona esto la
imagen?").

**Diagnóstico**: `.detail-imagen` en `frontend/src/styles/index.css`
usaba `object-fit: cover`. Aclaración importante para Víctor: `cover`
NO distorsiona la imagen — nunca la estira ni la achata, siempre respeta
sus proporciones originales (eso solo pasaría con `object-fit: fill`,
que no se usa aquí) — pero sí RECORTA lo que sobra del recuadro para
llenarlo por completo cuando la foto y el recuadro no tienen la misma
proporción. Con fotos de producto más altas que anchas (botellas,
latas en vertical, etc.) esto recorta el extremo superior o inferior,
que es justo lo que Víctor notó.

**Arreglo**: cambiado a `object-fit: contain`, que también respeta
siempre las proporciones (tampoco distorsiona nunca) pero encoge la
imagen entera para que quepa completa dentro del recuadro sin recortar
nada. A cambio, puede dejar un pequeño margen a los lados o
arriba/abajo cuando la foto y el recuadro no encajan exactos — para que
ese margen no se vea como un hueco vacío o roto, se añadió
`background: var(--surface-sunk)` (el mismo tono de fondo hundido que
ya se usa en otras zonas de la app). `frontend/src/styles/index.css`.

- `backend/package.json` y `frontend/package.json` suben a 1.18.4 (ver
  convención de v0.58) — sin cambios de código en el backend esta vez.
- **Verificación**: `npx vite build` sin errores. Comparativa visual
  generada con Playwright usando una foto de producto sintética (más
  alta que ancha, con marcas de texto "BORDE SUPERIOR"/"BORDE INFERIOR"
  para que el recorte fuera evidente) renderizada con el CSS real
  compilado: en el "antes" (`cover`) se pierden ambos bordes; en el
  "después" (`contain`) se ve la imagen completa con márgenes laterales
  discretos. Captura enviada a Víctor para confirmación visual directa.

---

## v0.63 — Carga masiva: archivos con espacio antes del nombre del artículo se interpretaban mal (v1.18.3 — pendiente de desplegar)

Víctor, desde PowerShell, listando la carpeta compartida real de
proveedores (`G:\CARPETA COMPRADORES\FT - FS - MCA - DOCUMENTACION\...`):
"porque la carga masiva de fichas tecnicas del proveedor AHUMADOS
CANARIOS SA no esta cargando nada?" — con el listado completo de los 30
PDF de `AHUMADOS CANARIOS SA\FICHAS TECNICAS`.

**Diagnóstico**: se simuló `parsearNombreArchivo` (CargaMasivaModal.jsx)
contra los 30 nombres reales pegados por Víctor, sin necesidad de
reproducir nada en la app en sí. 20 de los 30 usan un ESPACIO entre el
código de proveedor y el nombre del artículo en vez de "_" — p.ej.
`01453_10102036_3220 BOQUERON EN VINAGRE ed 2.pdf` (formato completo en
espíritu: código DALI, código SAP, código proveedor, nombre — pero con
el tercer separador siendo un espacio, no "_"). El parser exigía "_" en
los tres separadores (`sinExtension.split("_")`, mínimo 4 trozos): al
no encontrar un cuarto trozo, esos 20 archivos fallaban el formato
completo y caían al formato alternativo "solo código de proveedor" (ver
v1.17.0) — que coge el PRIMER trozo del nombre como si fuera el código
de proveedor. Para estos archivos ese primer trozo es "01453" (el
CÓDIGO DALI), no "3220" (el código de proveedor real) — así que la
carga masiva buscaba un artículo con código de proveedor "01453" (que
no existe) y todas esas filas acababan en error al pulsar "Subir", sin
subir nada. Confirmado con una simulación en Node.js del parser
original contra los 30 nombres: exactamente 20 fallan, 10 funcionan
(los que sí usaban "_" en los tres separadores, p.ej.
`02153_10100279_7219_MERLUZA_REBOZADA_AL_HUEVO.pdf`).

**Arreglo**: `parsearNombreArchivo` pasa de `split("_")` a una expresión
regular (`^(\d+)_([^_\s]+)_([^_\s]+)[_\s](.+)$`) que acepta "_" o
espacio indistintamente como separador ANTES del nombre del artículo —
los tres códigos en sí (`[^_\s]+`) siguen sin poder llevar espacios ni
"_", así se sigue detectando con seguridad dónde termina cada uno, sin
ambigüedad. Reprocesados los 30 nombres reales de Víctor con el parser
nuevo: los 30 parsean correctamente ahora (antes 10/30).
`frontend/src/components/admin/CargaMasivaModal.jsx`.
- `backend/package.json` y `frontend/package.json` suben a 1.18.3 (ver
  convención de v0.58) — sin cambios de código en el backend esta vez.
- **Verificación**: simulación en Node.js del parser (viejo y nuevo)
  contra los 30 nombres reales pegados por Víctor (no archivos de
  prueba genéricos). `npx vite build` sin errores.
- **Nota para Víctor**: si tras desplegar esto la carpeta
  `AHUMADOS CANARIOS SA` sigue sin cargar nada, pero ahora aparece como
  "no coincide con ningún proveedor del catálogo" (en vez de filas con
  error una a una), el problema sería otro — que el nombre exacto de la
  carpeta no coincide con el `nombre_proveedor` dado de alta en el
  sistema (p.ej. una coma o abreviatura distinta) — se puede comprobar
  y corregir aparte si hiciera falta.

---

## v0.62 — Arreglo de raíz del TTL del token SSO en control_pedidos, margen de DALI ajustado de vuelta (v1.18.2 — pendiente de desplegar)

Tras repasar juntos los pendientes del proyecto ("De todos los puntos,
por cual me recomiendas empezar" → se le propuso empezar por este, con
el TTL del SSO como primer paso por ser rápido, de bajo riesgo, y con el
contexto del diagnóstico de v0.60 todavía fresco; Víctor respondió
"Ok").

Con el visto bueno explícito de Víctor para tocar `control_pedidos`
(repo/despliegue aparte), se aplicó el arreglo "de raíz" que había
quedado pendiente en v0.60: en vez de que el margen de DALI cargue con
todo el peso de compensar un cold-start lento, el propio token de SSO
pasa a durar lo suficiente por sí mismo.

- **`control_pedidos/app.py`**: `_generar_token_sso_dali`, el parámetro
  `ttl_segundos` sube de 60 a 100 — cubre un cold-start normal de Render
  (~60s documentados) con margen de sobra por sí solo, sin depender
  tanto del margen de reloj del otro lado.
- **DALI, `backend/src/controllers/authController.js`**:
  `SSO_MARGEN_RELOJ_SEGUNDOS` baja de 90 a 20 — los 90s de v0.60 eran un
  parche mientras el TTL de arriba seguía en 60s; con el TTL ya
  arreglado, el margen vuelve a su papel original (desfase de
  reloj/latencia de verificación, no sustituto del TTL), y de paso se
  acorta la ventana teórica de reutilización de un token
  interceptado-pero-no-usado que el parche de v0.60 había ensanchado.
  Ventana total efectiva prácticamente sin cambios: ~120s (100s + 20s)
  frente a los ~150s (60s + 90s) de v0.60 — la diferencia es de dónde
  viene ese margen, no de cuánto dura en total.
- **Entrega**: siguiendo las normas de entrega de
  `control_pedidos/docs/HISTORIAL_CAMBIOS.md` (obligatorias para
  cualquier cambio en ese repo): solo archivos individuales con ruta
  (nunca el ZIP completo en ese proyecto), entrada nueva en su propio
  `CHANGELOG.md` y en `docs/HISTORIAL_CAMBIOS.md` (documento unificado
  del ecosistema, que también sigue la parte de DALI), versión subida a
  v12.30.25 en el badge de `templates/index.html` y en `README.md`.
- **Verificación**: `python3 -m py_compile app.py` (control_pedidos) y
  `node --check` sobre `authController.js` (DALI), ambos sin errores.
- `backend/package.json` y `frontend/package.json` de DALI suben a
  1.18.2 (ver convención de v0.58) — sin cambios de código en el
  frontend de DALI esta vez.

---

## v0.61 — Aviso de "alternativas de otros proveedores" en recuadro, con texto genérico (v1.18.1 — desplegado)

Víctor, tras ver la captura de v0.59 ya desplegada en producción
("HIELO CUBITOS BOLSA", "En reserva de: ALCRUZ CANARIAS SL, EMICELA
SA"), pidió: "el mensaje de reserva, mejor lo encuadramos para que sea
mas visual y ponemos algo genérico como, disponibles mas alternativas a
este articulo en fichas técnicas, o algo asi mas profesional, ¿que
opninas?"

Se estuvo de acuerdo con la propuesta y se afinó en dos puntos:

- **Recuadro en vez de borde suelto**: v0.59 dejó solo un borde de color
  a la izquierda del texto, sin fondo ni caja — demasiado discreto,
  casi se perdía visualmente junto a la imagen del artículo. Ahora es un
  pequeño recuadro (fondo `--surface-sunk`, borde `--line`, icono `i`
  de información en `--brass`) — se nota como aviso reconocible sin
  volver a ocupar tanto espacio como el bloque original en rojo de antes
  de v0.59.
- **Texto genérico, pero reutilizando terminología ya existente**: en
  vez de listar los nombres de los proveedores en el texto visible
  ("En reserva de: X, Y"), ahora dice "Hay alternativas de otros
  proveedores disponibles para este artículo" — la misma expresión
  ("alternativas de otros proveedores") que ya usa el botón "Ver
  alternativas de otros proveedores" que existe más abajo en la misma
  ficha (`handleToggleAlternativas`, ya en el código desde antes de este
  segmento). Se prefirió esta redacción a la sugerida literalmente por
  Víctor ("...en fichas técnicas") porque el aviso también cubre la
  imagen, no solo las fichas técnicas, y porque reutilizar el término
  exacto del botón hace que las dos piezas de la pantalla "hablen
  igual" en vez de tener dos frases distintas para lo mismo. Los
  nombres concretos de los proveedores no se pierden: se mantienen en
  el `title` (tooltip nativo al pasar el ratón), igual que ya hacía
  v0.59 con la frase completa.
  `frontend/src/components/ArticuloDetail.jsx`,
  `frontend/src/styles/index.css`.
- `backend/package.json` sube a 1.18.1 junto con `frontend/package.json`
  (sin cambios de código en el backend) — ver convención de v0.58.
- **Verificación**: `npx vite build` sin errores. Captura comparativa
  antes/después con el mismo CSS ya compilado (Playwright, offline, sin
  tocar la app desplegada), mismo método que en v0.59.

---

## v0.60 — Cold-start de Render vs. timeout del frontend vs. TTL del token SSO (v1.18.0 — desplegado)

Víctor reportó (con captura de "Comprobando sesión…" congelada): "porque
el primer arranque del dia tarda mucho y queda asi? incluso salta el
error de contraseña y hay que poderla otra vez, llamando desde
control_pedidos a Dali-Sap-Articvulos". Pidió explícitamente, primero,
solo una explicación, sin tocar nada: "Solo quiero que me expliques, sin
tocar nada todavía".

**Diagnóstico (solo explicación, sesión previa de este mismo hilo):**
- Render, plan free (`render.yaml`: `plan: free`), suspende el backend
  tras 15 min sin tráfico entrante y tarda "about one minute" en
  reactivarlo (documentación oficial de Render, confirmada con
  WebFetch).
- El frontend abortaba la comprobación de sesión a los 20s
  (`TIMEOUT_SESION_MS`, fijado en la sesión de HISTORIAL v0.33) — muy
  por debajo de ese cold-start real, así que un primer acceso del día
  casi siempre abortaba antes de que el backend llegara a responder.
- El acceso automático desde control_pedidos (`?dali_token=`) usa un
  token de SSO firmado (HMAC-SHA256, secreto compartido
  `DALI_SSO_SECRET`) generado por `_generar_token_sso_dali` en
  `control_pedidos/app.py` (repo hermano, `ttl_segundos=60` por
  defecto) — con el margen de reloj de DALI en 10s
  (`SSO_MARGEN_RELOJ_SEGUNDOS`), la ventana total en la que ese token se
  aceptaba era de solo ~70s, casi calcada al propio tiempo de
  cold-start, sin margen real. Esto explica el "error de contraseña"
  que menciona Víctor: no es una contraseña incorrecta, es
  `LoginScreen.jsx` mostrando el aviso de que el SSO falló
  (`avisoInicial`) y cayendo al formulario manual.

**Investigación adicional (mismo hilo, después de la explicación
inicial):** Víctor montó por su cuenta un keep-alive externo
(cron-job.org, cada 5 min entre las 6:00 y las 22:00 hora de Canarias) —
que a su vez empezó a fallar con 503 rápidos y sostenidos durante más de
dos horas la madrugada del 22 de agosto. Se revisaron logs reales de
despliegue de Render (pegados por Víctor) y se encontró un hueco de
~18h sin ninguna línea de log que englobaba exactamente esa ventana de
fallos — indicando que las peticiones no llegaban ni a invocar el
proceso Node. Se descartó la cuota mensual agotada (99h de 750h
consumidas, captura de Billing → Usage) y se encontró un incidente real
de Render (proveedor upstream Google Cloud, afectando a Frankfurt entre
otras regiones) pero de dos días antes (20 de agosto, resuelto a las
19:40 UTC) — no coincide en fecha con el fallo del 22, y las barras de
disponibilidad de 90 días de Render no muestran ninguna incidencia
adicional en agosto. La comunidad de Render tiene varios hilos abiertos
y sin resolver sobre exactamente este patrón (503 sostenidos, sin
relación aparente con cambios de código) — se concluyó que es más
probable que sea una variabilidad de infraestructura de Render no
publicada como incidente, que algo achacable a esta app o a su código.

**Decisión, tras el "OK, ajustamos lo propuesto" de Víctor (el plan de
pago de Render queda para más adelante, no se toca ahora):** arreglar
en el lado de DALI lo que sí depende de nosotros, sin tocar
`control_pedidos` (repo/despliegue aparte, pendiente del visto bueno de
Víctor si algún día se quiere hacer el arreglo "de raíz" ahí: alargar
el TTL del propio token).

- `TIMEOUT_SESION_MS` (frontend, `services/api.js`): 20s → 100s. Cubre
  un cold-start real con margen, y queda por debajo de la nueva ventana
  de aceptación del token de SSO (~150s) para no esperar más de lo que
  el propio token permitiría de todos modos.
- `SSO_MARGEN_RELOJ_SEGUNDOS` (backend, `authController.js`): 10s → 90s.
  Ventana total del token de SSO: ~60s (TTL propio, control_pedidos) +
  90s (margen, DALI) ≈ 150s — suficiente para un cold-start lento sin
  depender de tocar la otra app. Es un compromiso consciente: alarga
  algo la ventana teórica en la que un token interceptado-pero-no-usado
  podría reutilizarse; aceptable para un enlace interno de un solo uso
  cuya seguridad real la da el antirrepetición (`_jtiUsados`), no el
  margen de reloj.
- **Bug encontrado de paso**: `_marcarJtiUsadoOFallar` limpiaba cada jti
  de `_jtiUsados` por la caducidad "cruda" del token (`payload.exp`),
  sin contar el margen — con el margen en 10s ya dejaba una ventana de
  10s en la que un token ya usado podía "olvidarse" del Map y volver a
  aceptarse sin detectarse como repetido; al subir el margen a 90s esa
  ventana se habría ampliado a 90s de no corregirse. Se guarda ahora
  `payload.exp + SSO_MARGEN_RELOJ_SEGUNDOS`, para que el jti se recuerde
  mientras el token siga siendo válido.
- **UX**: la pantalla "Comprobando sesión…" (`App.jsx`) se queda ahora
  potencialmente bastante más tiempo en pantalla (hasta 100s en el peor
  caso) — sin ningún aviso, eso sería indistinguible de estar
  colgada/rota. Se añade un mensaje que aparece solo si la espera supera
  `ESPERA_LARGA_AVISO_MS` (4s, exportado desde `api.js`), explicando que
  puede deberse a que el servidor estaba dormido y que no hace falta
  recargar. Por debajo de 4s no se muestra nada, para no meter ruido en
  el caso normal (respuesta en bien menos de un segundo).
- `backend/package.json` y `frontend/package.json` suben a 1.18.0 (ver
  convención de v0.58).
- **Verificación**: `node --check` sobre `authController.js`, `npx vite
  build` sin errores.
- **Pendiente/fuera de alcance de esta entrega**: el episodio del
  cron-job.org del 22 de agosto sigue sin una causa 100% confirmada
  (apunta a infraestructura de Render, no a esta app) — no hay código
  que ajustar para ese caso concreto por ahora. El TTL del token de SSO
  en `control_pedidos` sigue en 60s (sin tocar, es otra app); el margen
  ampliado en DALI ya cubre un cold-start normal sin necesidad de eso.
  El plan de pago de Render (elimina el sleep por completo) queda
  aparcado para más adelante, a petición de Víctor.

---

## v0.59 — Aviso de "en reserva de otro proveedor" más corto en la ficha del artículo (v1.17.2 — desplegado)

Víctor pidió: "En la ficha del artículo, donde se ve la imagen y las
fichas, cuando existe algún otro proveedor con el mismo artículo, la
aplicación muestra un mensaje grande en rojo bajo la foto indicando
esto. Podemos realizar este mensaje más corto y profesional? Que no
ocupe tanto espacio."

- **Antes**: `.alert.alert-warn` (mismo estilo que los avisos de error
  de carga masiva) con la frase completa — "Este artículo tiene también
  imagen/fichas guardadas de otro(s) proveedor(es) (X, Y), en reserva —
  se mostrarán automáticamente si el proveedor asignado cambia a uno de
  ellos." — bloque de fondo vino, 4 líneas o más según cuántos
  proveedores hubiera.
- **Ahora**: una línea corta ("En reserva de: X, Y") con un simple
  borde de color a la izquierda, sin fondo — la frase completa de
  siempre se mantiene como `title` (tooltip nativo al pasar el ratón),
  así no se pierde información, solo protagonismo visual.
  `frontend/src/components/ArticuloDetail.jsx`,
  `frontend/src/styles/index.css` (`.aviso-reserva`, nueva — no se
  tocó `.alert-warn` en sí, ese estilo lo siguen usando otros avisos de
  la app, p.ej. en `CargaMasivaModal.jsx`, y no venía al caso
  cambiarlo ahí).
- **Verificación**: `npx vite build` sin errores. Captura comparativa
  antes/después con el mismo CSS ya compilado (Playwright, offline, sin
  tocar la app desplegada) para confirmar visualmente la diferencia de
  espacio antes de entregar.
- Aplicada también la convención de v0.58: `backend/package.json` sube
  a 1.17.2 junto con `frontend/package.json`, aunque esta entrega no
  toque nada del backend.

---

## v0.58 — Convención nueva: backend y frontend suben de versión siempre juntos (v1.17.1 — desplegado)

Tras desplegar v1.17.1, Víctor confirmó que la importación ya funciona
("AHORA SI CARGO") y preguntó por qué el número de versión que se ve en
la propia app (esquina inferior del menú) seguía marcando 1.17.0 en vez
de 1.17.1. Motivo: ese número sale de `frontend/package.json`
(`Sidebar.jsx`, `import { version as APP_VERSION } from
"../../package.json"`), y v1.17.1 había sido una entrega solo de
backend — el frontend no había cambiado, así que su versión no se
había tocado, aunque el backend sí llevara ya la 1.17.1.

Víctor respondió: "actualizamos siempre la version en pares, historial
y changelog" — a partir de ahora, `backend/package.json` y
`frontend/package.json` se suben SIEMPRE al mismo número en cada
entrega, aunque esa entrega solo toque uno de los dos lados (igual que
ya se hacía, sin pensarlo mucho, cuando ambos cambiaban a la vez — ver
v1.15.0/v1.15.1 — pero no cuando solo cambiaba uno, ver v1.15.2 vs
v1.16.0, o el propio v1.17.1 vs v1.17.0 que motivó la pregunta). Así el
número que se ve en la app siempre coincide con la entrega real más
reciente, sea cual sea el lado que haya cambiado.

- **Aplicado retroactivamente ya mismo**: `frontend/package.json` y
  `frontend/package-lock.json` suben a 1.17.1 (sin ningún cambio de
  código en el frontend, solo el número) para igualar al backend, que
  ya estaba en 1.17.1 desde la entrega anterior.
- **Verificación**: `npx vite build` sin errores; comprobado que el
  bundle generado (`dist/assets/index-*.js`) contiene el texto
  "1.17.1", confirmando que el badge de la app mostrará el número
  correcto en cuanto se despliegue este build.
- **Nota de convención, añadida también al propio `CHANGELOG.md`**: de
  aquí en adelante, toda entrega sube ambos `package.json` al mismo
  número, y esta nota queda documentada ahí para que no se pierda entre
  entregas.

---

## v0.57 — "Importar Excel": el sondeo de progreso se quedaba sin conexión mientras el servidor parseaba (v1.17.1 — desplegado)

Víctor subió dos capturas de DevTools (pestaña Network) mostrando
"Importar Excel" con el mensaje "Se ha perdido la conexión comprobando
el progreso de la importación", sin más texto — se investigó a partir
de las propias capturas.

- **Diagnóstico, primer intento (descartado)**: la hipótesis inicial fue
  "el backend se queda bloqueado, así que el sondeo no recibe respuesta
  y salta el timeout" — cierta en parte, pero la propia captura de
  Network lo desmentía como explicación completa: tras el primer sondeo
  cancelado a los 15s (timeout del frontend), los siguientes NO se
  quedaban colgados, volvían con **503** y **429** en menos de 150ms
  cada uno. Eso no lo devuelve un proceso bloqueado, lo devuelve algo
  delante de él.
- **Diagnóstico real**: el parseo de los Excel (`XLSX.read()` +
  `sheet_to_json()`) seguía siendo código síncrono desde dentro del
  trabajo en segundo plano (ver v0.44/v0.55) — v0.55 solo evitó que
  bloqueara la RESPUESTA HTTP del POST, pero seguía bloqueando el ÚNICO
  hilo del proceso Node mientras se ejecutaba, ya que "en segundo
  plano" (nadie hace `await` desde la petición) no es lo mismo que "sin
  bloquear el hilo" — solo una operación de E/S real cede el control.
  Mientras el parseo corre (varios segundos con los ~30.000 artículos
  reales, medido: 3,8s en local sin apenas margen de CPU de sobra),
  Render deja de recibir respuesta del proceso a NINGUNA petición,
  incluido su propio chequeo de salud, y empieza a devolver 503
  (servicio no disponible) y 429 (límite de peticiones) desde su propia
  capa — sin pasar por el Express de la app, esas respuestas no llevan
  las cabeceras CORS que pone la propia app, así que el navegador no
  puede leerlas y las convierte en un fallo de red genérico
  ("Failed to fetch") — que es justo lo que cuenta `api.js` como fallo
  de conexión (`fallosSeguidos`, se rinde a partir de 6 seguidos: el
  timeout inicial + los 3×503 + los 2×429 de la captura de Víctor
  suman exactamente 6). El trabajo en sí no se pierde — sigue corriendo
  en el servidor, tal y como ya avisa el propio mensaje — pero el
  admin se queda sin forma de verlo hasta que la instancia se
  recupera y recarga la pantalla.
- **Arreglo**: el parseo se mueve a un `worker_thread` de Node aparte
  (nativo, sin dependencia nueva) — `backend/src/workers/
  parsearExcelWorker.js` recibe los dos ficheros en crudo y hace el
  `XLSX.read()`/`sheet_to_json()` en su propio hilo, devolviendo las
  filas ya parseadas (o el error) al hilo principal por mensaje.
  `importController.js` lo envuelve en `parsearExcelEnWorker()` y lo
  usa donde antes llamaba a `XLSX.read()` directamente — el resto del
  comportamiento (columnas obligatorias, mensaje de error) no cambia.
  Con esto, el hilo principal queda libre durante todo el parseo y
  sigue pudiendo responder al sondeo de progreso y a los health checks
  mientras tanto.
- **Verificación**: `node --check` de los dos archivos tocados sin
  errores. Probado con los dos ficheros reales de Víctor (30.179 filas
  cada uno) con un script aparte que compara ambos caminos:
  - Código antiguo (síncrono, en el hilo principal): un timer de 200ms
    puesto a sonar ANTES del parseo no suena ni una sola vez durante
    los 3,8s que tarda — confirma el bloqueo total del hilo.
  - Código nuevo (worker_thread): el mismo timer, ahora en el hilo
    principal mientras el parseo corre en el worker, suena con
    normalidad cada ~200ms durante los 4,8s que tarda (algo más que en
    el hilo principal por el coste de arrancar el worker y copiar los
    buffers, insignificante frente al problema que resuelve) —
    confirma que el hilo principal queda libre. En ambos casos el
    resultado del parseo es idéntico: 30.179 filas en cada fichero, con
    las columnas obligatorias presentes.
- **Nota**: no se ha tocado el Worker de Cloudflare
  (`cloudflare-workers/dali-proxy-api.js`) ni la configuración de
  Render — igual que en v0.55, el arreglo elimina la causa del bloqueo
  en origen, no hace falta tocar nada de lo que hay delante.

---

## v0.56 — Carga masiva de imágenes/fichas: reconoce archivos nombrados solo con el código de proveedor (v1.17.0 — desplegado)

Víctor preguntó (a raíz de haber recibido el script `rellenar_articulos.py`
corregido, que ya deja muchos códigos de proveedor grabados en el
sistema): "como ya tenemos muchos códigos proveedores grabados, podemos
modificar la carga de imágenes y fichas masivas? si al principio del
archivo solo tiene un código, entendemos que es el del proveedor y
buscamos asociarlo al mismo" — y adjuntó dos archivos de ejemplo, tal y
como los tiene organizados en las carpetas de cada proveedor:
`9904.pdf` (solo el código, sin nada más) y `37 hamb.americana100g.3x25k.pdf`
(código, espacio, y el resto de la descripción).

- **Contexto**: hasta ahora, la carga masiva de imágenes/fichas
  (`CargaMasivaModal.jsx`, ver v0.46/v0.53) exigía que cada archivo
  siguiera el formato completo
  `códigoDali_códigoSap_códigoProveedor_nombre` — el código DALI, sacado
  directamente del nombre, es lo que identifica a qué artículo va cada
  imagen/ficha. El proveedor en sí ya se sabe por la carpeta en la que
  vive el archivo (no por el nombre), eso no cambia. Lo que faltaba era
  una vía para cuando el archivo NO trae el código DALI en el nombre,
  solo el código propio del proveedor — algo que antes no se podía
  resolver porque apenas había códigos de proveedor grabados, pero que
  ahora sí es viable: entre la carga masiva de código proveedor por
  Excel (v0.52) y el propio script de PDFs de Víctor, la tabla
  `codigos_proveedor` ya tiene bastante cobertura.
- **Diseño**: si el nombre del archivo no encaja con el formato completo
  de 4 partes, se prueba un formato alternativo — el trozo antes del
  primer espacio o guion bajo (o el nombre entero sin extensión, si no
  hay ninguno de los dos) se toma como candidato a código de proveedor,
  siempre que tenga al menos un dígito (para no confundir con un nombre
  de archivo cualquiera). Con ese código y el proveedor de la carpeta,
  se consulta un endpoint nuevo (`GET
  /admin/articulos/por-codigo-proveedor`) que busca en `codigos_proveedor`
  qué artículo usa ese proveedor para ese código, y devuelve su código
  DALI — a partir de ahí, la fila sigue exactamente el mismo camino de
  siempre (comprobar hash, subir si hace falta, guardar el código de
  proveedor si no había ninguno). Si no hay ninguna coincidencia
  grabada, la fila queda en error ("No se encontró ningún artículo con
  código de proveedor…") para revisarla a mano, en vez de bloquear el
  resto de la carga.
  - La resolución se hace al procesar cada fila (al pulsar "Subir"), no
    al elegir la carpeta — así la tabla se puede rellenar al instante
    con miles de archivos sin lanzar una consulta al backend por cada
    uno solo para mostrar la lista; mientras tanto, la columna "Código
    DALI" de estas filas muestra "cód. prov. X (por resolver)".
- **Archivos tocados**: `backend/src/controllers/storageController.js`
  (nuevo `buscarArticuloPorCodigoProveedor`), `backend/src/routes/admin.js`
  (nueva ruta), `frontend/src/services/api.js` (nuevo
  `buscarArticuloPorCodigoProveedor`),
  `frontend/src/components/admin/CargaMasivaModal.jsx`
  (`parsearCodigoProveedorDeNombre` nuevo, `clasificarArchivos` y
  `procesarFila` adaptados, texto de ayuda del modal actualizado).
- **Verificación**: `node --check` de los tres archivos backend/JS
  tocados sin errores; `npx vite build` del frontend sin errores;
  probado en Node aparte el nuevo `parsearCodigoProveedorDeNombre` con
  los dos ejemplos reales de Víctor (`9904.pdf` → `"9904"`, `37
  hamb.americana100g.3x25k.pdf` → `"37"`) y con un nombre sin ningún
  código (`catalogo.pdf` → `null`, correctamente descartado) y con un
  nombre de formato completo (para confirmar que ese sigue tomando la
  vía de siempre, sin pasar por el formato alternativo).
- **Nota**: no se han vuelto a subir los dos PDF de ejemplo de Víctor a
  ningún sitio — son solo muestra del formato de nombre, esta entrega es
  el código de la funcionalidad, no un procesado de esos ficheros
  concretos (a diferencia del encargo anterior con `rellenar_articulos.py`).

---

## v0.55 — "Importar Excel" daba 502 con los ficheros reales del catálogo (v1.15.2 — desplegado)

Víctor subió dos capturas (duplicadas) de la pantalla "Importar Excel"
mostrando `import-excel` con estado 502 y 41.34s de duración en la
pestaña Network de DevTools, más "Failed to fetch" en la propia app, y
adjuntó los dos ficheros reales (`ARTICULOS_DALI.xlsx`,
`LISTADO_CODIGOS_DALI_-_SAP.xlsx`) sin más texto — se investigó y
arregló directamente, sin hacer falta pedirle nada más: el propio 502 a
los ~41s y el patrón de los ficheros ya apuntaban al mismo problema de
timeout que este archivo llevaba documentado desde v0.20 (2026-08-20),
solo que en otro punto del proceso.

- **Diagnóstico**: se descargaron los dos ficheros adjuntos y se midió
  en local cuánto tarda `XLSX.read()` en parsearlos — 6,3 segundos
  combinados (30.179 filas cada uno). Ese parseo se hacía de forma
  SÍNCRONA en `importarExcel()`, ANTES de crear el trabajo en segundo
  plano y responder con el `job_id` — el comentario que lo introdujo
  (v0.20) decía explícitamente "rápido, en memoria", cierto en su
  momento pero ya no con el catálogo actual. En el plan gratuito de
  Render (CPU compartida/limitada) ese mismo parseo es previsiblemente
  bastante más lento que en local — de sobra para que el proxy por
  delante del backend (Cloudflare Worker o el propio proxy del plan
  gratuito de Render) cortara la conexión con un 502 antes de que la
  petición llegara siquiera a responder. Es decir: v0.20 troceó el
  GUARDADO (bloques de 500) para que no bloquease la respuesta, pero el
  PARSEO de entrada se quedó fuera de aquel arreglo — y era él quien
  ahora tropezaba con el mismo límite, con el catálogo ya crecido.
- **Arreglo**: `procesarImportacionEnSegundoPlano()` pasa a recibir los
  ficheros en crudo (`bufferDali`/`bufferSap`) en vez de las filas ya
  parseadas, y hace el `XLSX.read()` + `sheet_to_json()` + validación de
  columnas obligatorias ella misma, como primer paso — DENTRO del
  trabajo en segundo plano, no antes de responder. Si falta una columna
  o el archivo no se puede leer, el trabajo termina en `estado: "error"`
  con el mismo mensaje de siempre (`finalizarTrabajo`), en vez de
  devolver un 400 síncrono. `importarExcel()` (la petición POST) ahora
  solo comprueba que hayan llegado los dos ficheros — instantáneo — y
  responde con el `job_id` al momento, sin ningún trabajo de CPU de por
  medio.
  - No hizo falta tocar el frontend: `importExcel()`
    (`frontend/src/services/api.js`) ya sondea `GET
    /admin/import-excel/estado/:jobId` cada 2 segundos y ya sabía
    convertir `estado.estado === "error"` en el mismo mensaje de error
    que antes daba la respuesta síncrona — un Excel con una columna que
    falta se sigue detectando igual, solo que se reporta unos segundos
    más tarde (uno o dos ciclos de sondeo) en vez de al instante.
- **Verificación**: `node --check` de `importController.js` sin
  errores. Probado aparte con un script Node independiente sobre los
  DOS ficheros reales que adjuntó Víctor: validan correctamente
  (30.179 filas cada uno, ~5,7s de parseo) y, con una copia del Excel
  DALI con la cabecera "CODIGO" renombrada a propósito (simulando una
  columna que falta), se detecta el mismo error de siempre
  (`Falta columna "CODIGO" en articulos_dali.`) y el trabajo simulado
  queda en `estado: "error"` con ese mensaje — confirmando que el
  arreglo no cambia el comportamiento de validación, solo cuándo ocurre.
- **Nota**: no se ha tocado `cloudflare-workers/dali-proxy-api.js` ni
  la configuración de Render — el arreglo elimina la necesidad de
  cualquier timeout más generoso ahí, porque ya no hay ninguna petición
  que se quede varios segundos esperando una respuesta.

---

## v0.54 — Aviso de nueva versión disponible, con recarga automática (v1.16.0 — desplegado)

Petición directa de Víctor: "en control_pedidos, tenemos programado que
se revicen nuevas actualizaciones cada poco y obliga a recargar para
trabajar con la nueva version aun teniendo abierta la anterior, necesito
que en esta aplicacion dali-sap-articulos-app tambien haga esta funcion,
con lectura de novedades y recuento para actualizacion automatica".

- **Investigación previa**: se revisó `control-pedidos-princess-main`
  (copia local en `/home/claude/work/control_pedidos`) para replicar el
  mismo comportamiento, no reinventarlo. Ese proyecto es Flask (Python)
  sirviendo un único `index.html` gigante — calcula un hash MD5 del
  archivo en cada petición (`/api/version`), lo compara contra el que
  guardó el navegador, y si difiere muestra un modal con el changelog y
  una cuenta atrás de 5 minutos que recarga sola. El polling es cada 30s
  los primeros 15 minutos y cada 60s después, sin backoff. El modal no
  tiene botón de cerrar aparte de "Recargar ahora" — a propósito, es
  forzoso.
- **Adaptación al stack de esta app**: dali-sap-articulos-app no tiene
  ese mismo punto de apoyo — el frontend se despliega como sitio
  estático en Render (`render.yaml`: `runtime: static`, `staticPublishPath: dist`),
  compilado con Vite, sin ningún servidor propio detrás sirviendo
  `index.html` en caliente como hace Flask. En vez de forzar ese
  mecanismo a través del backend (que además vive en otro servicio de
  Render, con su propio ciclo de despliegue independiente del
  frontend), se resolvió íntegramente del lado del frontend:
  - Nuevo plugin de Vite (`avisoNuevaVersionPlugin`, en
    `vite.config.js`) que, al terminar cada `npm run build`, escribe
    `dist/version.json` con un identificador que cambia en cada build
    (la hora del build en milisegundos — no hace falta git ni tocar el
    backend) y copia `CHANGELOG.md` (que vive en la raíz del monorepo,
    fuera de `frontend/`) a `dist/CHANGELOG.md`. Ambos quedan servidos
    como archivos estáticos junto a `index.html`, en el mismo origen.
  - Confirmado que Render sirve un archivo real de `dist/` tal cual si
    existe, ANTES de aplicar la regla de reescritura `/* -> /index.html`
    del Blueprint (pensada solo para las rutas de la SPA) — así que
    `version.json`/`CHANGELOG.md` se sirven directamente, sin que esa
    regla los intercepte.
  - Nuevo componente `ComprobadorNuevaVersion.jsx`, montado en
    `main.jsx` como HERMANO de `<App/>` (no dentro) — así comprueba la
    versión pase lo que pase dentro de `App.jsx` ("Comprobando
    sesión…", pantalla de login o la app ya cargada), igual que
    control_pedidos comprueba tanto antes como después de entrar. Al
    montarse, fija una "versión de referencia" con la primera lectura
    de `/version.json`; en cada comprobación posterior (mismo esquema
    30s/15min → 60s de control_pedidos), si el valor cambia, se muestra
    el aviso.
  - El aviso trae las notas de la versión: se parsea `CHANGELOG.md` (el
    formato "Keep a Changelog" que ya usa este repo — `## [x.y.z] -
    fecha`, `### Añadido/Cambiado/Arreglado/Eliminado`, ítems `- texto`
    que pueden seguir en líneas indentadas debajo) y se muestran como
    mucho las 3 versiones más recientes, con una etiqueta de color por
    tipo de cambio (Nuevo/Mejora/Fix/Eliminado) — adaptado al formato
    real de ESTE changelog, distinto al de control_pedidos (ese usa
    emojis por línea; este usa encabezados `###` por sección).
  - Estilo propio de esta app (papel marfil/latón/vino, Fraunces + Inter
    — ver `--bg`/`--brass`/`--wine` en `styles/index.css`), no una copia
    del navy/gold de control_pedidos: modal centrado con fondo
    difuminado, cabecera con el aviso, cuerpo con el changelog resumido
    (scroll si hace falta) y pie con la cuenta atrás + el botón "↻
    Recargar ahora". Sin botón de cerrar ni clic-fuera para descartar —
    forzoso, como pidió Víctor.
  - Ayuda de prueba `window._testAvisoNuevaVersion()` (consola del
    navegador) para comprobar el aviso sin esperar a un despliegue real
    — mismo criterio que el `_testModalVersion()` que ya tiene
    control_pedidos.
- **Verificación**: `npm run build` genera `dist/version.json` (con un
  valor numérico distinto en cada build) y `dist/CHANGELOG.md`
  correctamente. Parser del changelog probado aparte con un script Node
  independiente sobre el `CHANGELOG.md` real generado: extrae
  correctamente las 3 versiones más recientes, une líneas de
  continuación de un mismo ítem, y descarta el bloque vacío "Sin
  publicar". No se pudo hacer una comprobación visual en navegador en
  esta sesión (permiso de navegación denegado) — la lógica de
  parseo/generación de archivos y el propio `npm run build` sí quedaron
  verificados.
- **Pendiente**: como con toda esta app, hace falta el despliegue real
  en Render para que el mecanismo funcione en producción — no requiere
  ningún cambio de configuración adicional en `render.yaml` (el
  `buildCommand` ya es `npm install && npm run build`, que ya ejecuta el
  plugin nuevo).

---

## v0.53 — La carga masiva de imágenes/fichas ya no pisa un código de proveedor distinto en silencio (v1.15.1 — desplegado)

Petición directa de Víctor, sobre el comportamiento de la carga masiva
de imágenes/fichas (no la de código proveedor de v1.15.0, esa es aparte
— ver más abajo): "si en la carga masiva de fichas e imagenes no se
adjunta codigo proveedor o codigo sap, prevalece la informacion que ya
exista en el sistema, no se elimina datos, si el codigo proveedor
indicado en los pdf o imagenes es diferente al existente se indica al
usuario para su conocimiento pero no se guarda, prevaleciendo el codigo
proveedor existente".

- **Código SAP**: revisado — la carga masiva de imágenes/fichas nunca lo
  ha tocado (solo se lee del nombre del archivo para mostrarlo en
  pantalla, nunca se manda al backend ni se guarda desde ahí; el único
  sitio que actualiza `codigo_sap` es "Importar Excel"). No hacía falta
  ningún cambio para esa parte de la petición.
- **Código proveedor — comportamiento anterior**: si el nombre del
  archivo traía un código distinto al ya guardado, se sobrescribía sin
  más, tanto si el archivo se subía de verdad (el propio backend lo
  guardaba tras la subida) como si el archivo resultaba "sin cambios"
  por hash idéntico (el frontend lo actualizaba aparte con una petición
  ligera). No había manera de saber, sin mirar historial, que un
  archivo mal nombrado podía haber pisado un código correcto.
- **Comportamiento nuevo**: `guardarCodigoProveedor()`
  (`storageController.js`) gana un parámetro `permitirSobrescribir`
  (por defecto `true`, sin cambios para la edición manual desde el
  formulario de admin — esa vía sigue pudiendo corregir siempre). Con
  `permitirSobrescribir: false` (el que ahora usan las cuatro llamadas
  de `subirImagenArticulo`/`subirFichaArticulo`, una por cada
  combinación subida-real/sin-cambios), la función primero mira si ya
  había un código guardado para ese artículo+proveedor:
  - Si no había nada → se guarda (rellena el hueco, no es "sobrescribir").
  - Si ya había el mismo valor → no hace falta escribir nada.
  - Si ya había un valor DISTINTO → NO se toca; se devuelve
    `{ motivo: "conflicto", valorExistente, valorIntentado }` para que
    el llamador decida qué hacer con esa información.
  Las respuestas de `subirImagenArticulo`/`subirFichaArticulo` incluyen
  ahora `aviso_codigo_proveedor` (el objeto de conflicto, o `null`) para
  que el frontend lo muestre. En `CargaMasivaModal.jsx`, tanto la rama
  de "archivo sin cambios" (que antes llamaba directamente a
  `actualizarCodigoProveedor` sin comprobar nada) como la rama de subida
  real ahora respetan esta misma regla — el mensaje de resultado de la
  fila añade un aviso legible ("el archivo trae código de proveedor
  "X", distinto al ya guardado "Y" — se mantiene el guardado, revísalo a
  mano si hace falta corregirlo") en vez de sobrescribir sin decir nada.
- **Nota importante**: esto NO afecta a la carga masiva de código
  proveedor desde el Excel exportado (v1.15.0, botón "Carga masiva:
  Código proveedor") — esa sigue sobrescribiendo siempre, a propósito:
  es una corrección explícita hecha a mano por Víctor sobre el propio
  listado, equivalente a la edición manual del formulario de admin, no
  una lectura automática de nombre de archivo que pueda venir mal
  formada.
- **Verificación**: `node --check` de `storageController.js` sin
  errores; `npm run build` del frontend sin errores; tabla de decisión
  de `guardarCodigoProveedor` (sin código nuevo, hueco vacío + código
  nuevo, mismo valor, valores distintos, espacios de más) probada aparte
  con un script Node independiente — todos los casos correctos.

---

## v0.52 — AutoFilter en Excel + carga masiva de código proveedor desde el propio export (v1.15.0 — desplegado)

Víctor subió un Excel real descargado desde la app (`articulos.xlsx`, con
filtros de Excel ya activados a mano por él) y preguntó dos cosas a la
vez: "¿PODEMOS HACER QUE SE APLIQUEN LOS FILTROS COMO YO LOS HE PUESTO
AUTOMATICAMENTE? PODEMOS APROVECHAR TAMBIEN ESTE LISTADO PARA REALIZAR
CARGA MASIVA DE CODIGO PROVEEDOR? NUEVO APARTADO EN ARTICULOS PARA
CARGAR UN TERCER ARCHIVO O ME DAS OPCIONES".

1. **AutoFilter automático en "Exportar Excel"**: inspeccionado el
   archivo que subió (unzip + grep del XML) — traía
   `<autoFilter ref="A4:F6930"/>` sin ningún criterio de filtro guardado,
   solo el desplegable activado (lo que hace Excel con Ctrl+Shift+L).
   Confirmado con una prueba mínima aparte que ExcelJS NO activa esto
   por defecto (sin fijarlo, el XML resultante no lleva `<autoFilter>`
   en absoluto) — así que lo que Víctor venía haciendo a mano tras cada
   descarga no estaba automatizado. Ahora `exportarExcel` fija
   `sheet.autoFilter` desde la fila de cabecera (4) hasta la última fila
   con datos (`sheet.rowCount`), en las columnas exportadas — reproduce
   exactamente el rango que él tenía puesto a mano. Las filas divisorias
   de grupo quedan dentro del rango filtrable, sin dar ningún error (se
   pueden ocultar/mostrar igual que cualquier otra fila).
   `backend/src/controllers/exportController.js`.
2. **Carga masiva de código de proveedor, reaprovechando el listado
   exportado**: en vez de preparar un archivo aparte, Víctor descarga
   "Exportar Excel", rellena o corrige a mano la columna "Código
   Proveedor" en las filas que le interesan y sube ese mismo archivo en
   un nuevo botón "Carga masiva: Código proveedor" (Administración →
   Artículos), en un modal propio de un solo archivo — más simple que
   `CargaMasivaModal.jsx` (esa sube carpetas enteras de imágenes/PDFs;
   esta un único .xlsx). Se le preguntó a Víctor dónde debía vivir esta
   opción (botón nuevo junto a los de carga masiva existentes / tercer
   archivo dentro de "Importar Excel" / pantalla nueva dedicada) — eligió
   la primera, la recomendada, para no mezclar este proceso con el de
   alta/actualización de catálogo.
   - Backend nuevo (`cargaMasivaCodigoProveedor`,
     `storageController.js`): localiza la fila de cabecera buscando la
     celda "Código DALI" (no asume que esté siempre en la fila 4) y
     localiza "Código Proveedor" por nombre de columna, no por posición
     fija. Cada fila con un "Código DALI" numérico válido cuenta como
     dato — las filas divisorias de grupo (solo texto en esa celda) se
     descartan solas al convertir a número (`NaN`), sin detectarlas
     aparte. Filas con código vacío o "—" se cuentan pero no se tocan
     (nunca se borra un código ya guardado por venir la celda vacía).
   - El código se aplica SIEMPRE al proveedor que el artículo tiene
     asignado HOY en la base de datos — la columna "Proveedor" del Excel
     es solo informativa, no se usa para elegir a quién pertenece el
     código ni se valida contra ella. Decisión deliberada (más simple y
     más robusta que exigir que el Excel esté "fresco"): si el artículo
     cambió de proveedor asignado entre la exportación y esta subida, el
     código se guarda para el proveedor de hoy, que es a quien de verdad
     hay que pedirle ese material.
   - Artículos con un código DALI que no existe en el catálogo, o sin
     ningún proveedor asignado (no hay a quién atribuirle el código), se
     reportan aparte en la respuesta (con una muestra + el total) sin
     bloquear el resto de filas válidas.
   - Guardado en un único `upsert()` por lote de 500 filas (mismo patrón
     que `procesarImportacionEnSegundoPlano`,
     `importController.js`), no una petición por fila — con hasta ~6700
     artículos posibles en el listado completo, evita el mismo riesgo de
     timeout ya documentado ahí. No hace falta el patrón de trabajo en
     segundo plano de la importación grande (aquí no hay resolución de
     dimensiones ni comprobaciones extra por bloque): responde en la
     misma petición.
   - Nuevo endpoint `POST /admin/articulos/carga-masiva-codigo-proveedor`
     (multipart, campo `archivo`), nueva función `cargaMasivaCodigoProveedor`
     en `frontend/src/services/api.js`, nuevo componente
     `CargaMasivaCodigoProveedorModal.jsx`, botón nuevo en
     `AdminArticulos.jsx`.
- **Verificación**: `node --check` de los archivos backend tocados sin
  errores; prueba aparte con ExcelJS confirmando que el
  `<autoFilter ref="A4:F24"/>` generado coincide con el rango esperado
  (cabecera → última fila). Lógica de parseo de la carga masiva de
  código de proveedor probada con un script Node independiente (filas
  divisorias, título/subtítulo, huecos vacíos, código DALI duplicado
  con "última fila gana", código como texto numérico, cabecera o
  columna ausente) — todos los casos correctos. Reprobada también contra
  el `articulos.xlsx` real que subió Víctor: cabecera detectada en la
  fila 4, 6.737 filas de datos separadas correctamente de las filas
  divisorias de grupo, 33 con código de proveedor ya relleno (de la
  carga masiva de fichas/imágenes que ya lo backfillea, v1.12.0) y 6.704
  sin código todavía. También `npm run build` del frontend sin errores.
- **Pendiente**: la migración `2026-08-20_codigos_proveedor.sql` (de
  v1.12.0) sigue sin confirmación de Víctor de haberse ejecutado en
  Supabase — esta carga masiva depende de esa tabla igual que el resto
  de funciones de código de proveedor.

---

## v0.51 — Cabecera en dos líneas + código de proveedor en Excel/PDF (v1.14.0 — desplegado)

Dos pulidos pedidos por Víctor sobre las mismas capturas de v1.13.1
(búsqueda por "070221" ya funcionando):

1. **Cabecera de "Código proveedor" en dos líneas**: la pidió con el
   mismo formato que "Código DALI" y "Código SAP" ("Código" arriba,
   "Proveedor" debajo, centrado) — con el título en una sola línea la
   columna se veía más ancha de lo necesario. Cambio puramente visual,
   mismo dato, mismo sitio en la tabla.
   `frontend/src/components/ArticuloTable.jsx`,
   `frontend/src/components/admin/AdminArticulos.jsx`.
2. **Código de proveedor también en Excel y PDF**: la columna nueva de
   v1.13.0 solo se veía en pantalla — "Exportar Excel"/"Exportar PDF"
   seguían sin ella. `fetchArticulosParaExport()`
   (`exportController.js`) ahora también pide `id`/`id_proveedor` de
   cada artículo y resuelve su código de proveedor con la misma lógica
   de `obtenerCodigosProveedorPorArticulos` que ya usa
   `listarArticulos` (duplicada aquí a propósito, mismo criterio que
   `limpiarParaFiltroOr`: no cruzar imports entre controllers por una
   función puntual). Nueva columna "Código Proveedor" en
   `columnasPdf()` (compartida entre PDF y Excel), entre "Código SAP"
   y "Artículo" — igual posición que en la tabla en pantalla. Se
   estrecharon un poco "Artículo" (260→250pt) y "Proveedor"
   (200→190pt) para dejarle sitio sin salirse del ancho de página A4
   apaisado.
- **Verificación**: `node --check` de `exportController.js` sin
  errores; la lógica de reparto del código por artículo es la misma ya
  probada en v1.13.0 (Map por `"idArticulo:idProveedor"`, solo el
  proveedor asignado cuenta). También `npm run build` del frontend sin
  errores.

---

## v0.50 — El buscador no encontraba nada por código de proveedor (v1.13.1 — desplegado)

Reportado por Víctor justo después de v1.13.0 (capturas): buscó
"070221" — el código de proveedor que se ve en la propia fila de "TARTA
CRUMBLE ALBARICOQUE ALMENDRA VAINILLA 1100GR" (SURPAN SL) — y el
buscador dio "0 artículo(s)", aunque el dato estaba justo ahí delante en
la columna nueva. Pregunta directa: "NO BUSCA POR CODIGO PROVEEDOR?".

- **Causa**: el buscador (`q`, `listarArticulos`) nunca llegó a mirar
  `codigos_proveedor` — solo se añadió la columna a la tabla (v1.13.0),
  pero el filtro de búsqueda (`nombre_articulo`, `codigo_dali_texto`,
  `codigo_sap`, proveedor por nombre) se quedó igual que antes, sin
  tocar.
- **Arreglo**: mismo patrón ya usado para "proveedor" (que también vive
  en otra tabla): antes de construir la consulta principal, se busca en
  `codigos_proveedor` qué códigos coinciden con `q` — pero, a
  diferencia de "proveedor", aquí hace falta comprobar que ese código
  sea el del proveedor QUE EL ARTÍCULO TIENE ASIGNADO, no uno guardado
  "en reserva" de otro proveedor (`codigos_proveedor` puede tener varias
  filas por artículo, una por cada proveedor con documentación suya).
  Sin esa comprobación, un resultado de búsqueda podría no coincidir
  con el código que muestra la columna, muy confuso. Se resuelve con
  `articulos!inner(id_proveedor)` embebido en la misma consulta (la FK
  ya existe, sin petición de más) y se filtra en JS antes de añadir esos
  artículos al `.or()` de la consulta principal, como
  `id.in.(...)`.
- **Placeholder del buscador actualizado** en ambas pantallas para
  mencionar "código proveedor", así se sabe que se puede buscar por ahí.
- **Verificación**: probado aparte el filtrado "solo el proveedor
  asignado cuenta como match" con datos de ejemplo — confirmado que un
  código guardado en reserva de otro proveedor NO cuela como resultado.
  También `npm run build` y `node --check` sin errores.

---

## v0.49 — Código de proveedor también como columna del listado (v1.13.0 — desplegado)

Continuación directa de v0.48: con el código de proveedor ya visible en
la ficha del artículo, Víctor pidió verlo también como columna en la
tabla, entre "Código SAP" y "Artículo - DALI" — tanto en la pantalla
principal (todos los roles) como en Administración → Artículos.

- **`GET /articulos` (`listarArticulos`, articulosController.js)**:
  nueva función `obtenerCodigosProveedorPorArticulos(idsArticulo)` que
  trae de golpe los códigos de todos los artículos de la página actual
  (troceado en lotes de 500 ids, cada lote paginado con `.range()` por
  si devolviera más de 1000 filas — mismo criterio de
  SUPABASE_MAX_ROWS_POR_PETICION que ya usaba el resto del listado),
  en vez de una consulta por fila. Se guarda en un `Map` clave
  `"idArticulo:idProveedor"` porque puede haber más de un código
  guardado por artículo (uno por cada proveedor con documentación
  suya, no solo el asignado — los de otros proveedores quedan "en
  reserva" y no deben aparecer en esta columna). Cada fila del listado
  se queda solo con el código que coincide con SU proveedor asignado.
- **`frontend/src/components/ArticuloTable.jsx`** (pantalla principal,
  todos los roles) y **`frontend/src/components/admin/
  AdminArticulos.jsx`** (Administración → Artículos): nueva columna
  "Código proveedor" en ambas tablas, en la misma posición.
- **Verificación**: la lógica de reparto del Map se probó aparte con
  datos de ejemplo incluyendo el caso límite que importa aquí — un
  código guardado para un proveedor DISTINTO al asignado de ese
  artículo (documentación en reserva) — confirmado que ese código NO
  se filtra a la columna, y que dos artículos que comparten el mismo
  proveedor no mezclan sus códigos entre sí. También `npm run build`
  y `node --check` sin errores.
- **Coste**: una consulta adicional por página de listado (no por fila)
  — mismo orden de magnitud que las demás consultas ya existentes en
  este mismo endpoint (proveedor, familia, subfamilia…), no cambia el
  patrón de rendimiento del listado.

---

## v0.48 — Código de proveedor: guardarlo de verdad y verlo en la ficha (v1.12.0 — desplegado)

Continuación directa de v0.47: al enseñar las fichas de otros
proveedores, Víctor pidió también ver, tanto en la ficha del artículo
como en cada grupo del panel de alternativas, el código con el que CADA
proveedor identifica ese artículo — "ya que el DALI y el SAP sí son los
mismos" (para todos los proveedores), pero el código de referencia
propio de cada uno no.

Repasando el código, ese dato NO existe en ningún sitio de la base de
datos hoy. Lo más parecido: el nombre de archivo de la carga masiva ya
trae un tercer segmento (`codigoDali_codigoSap_codigoProveedor_
nombre.ext`, ver `parsearNombreArchivo` en CargaMasivaModal.jsx) que
desde la migración "documentación por proveedor" del 2026-08-17 se lee
y se descarta explícitamente ("ya NO se usa para nada: el proveedor
real se determina por la carpeta").

Antes de implementar, pregunté cómo debía rellenarse ese código, dado
que no hay ningún dato retroactivo de dónde sacarlo salvo relanzando la
carga masiva:

- Solo automático desde carga masiva (aprovechando el segmento que ya
  se lee pero se descarta),
- solo editable a mano desde el formulario de admin del artículo, o
- ambas cosas.

Víctor eligió **ambas** (recomendado).

- **Nueva tabla `codigos_proveedor`** (migración
  `database/migraciones/2026-08-20_codigos_proveedor.sql`, a ejecutar a
  mano en el SQL Editor de Supabase antes de desplegar este backend):
  `(id_articulo, id_proveedor, codigo, actualizado_en)`, único por
  `(id_articulo, id_proveedor)`. Un solo valor por artículo+proveedor,
  no por tipo de documento — el mismo proveedor usa el mismo código
  tanto en su imagen como en sus dos fichas, así que no hace falta
  guardarlo repetido (y desincronizable) en `imagenes`/`fichas`.
- **Captura automática por carga masiva**
  (`CargaMasivaModal.jsx`): `parsearNombreArchivo` ya no descarta el
  tercer segmento del nombre, lo devuelve como `codigoProveedor`. Se
  manda como campo `codigo_proveedor` en la misma petición de subida
  (`subirImagenArticulo`/`subirFichaArticulo`,
  `storageController.js`) — sin petición de red extra.
- **También cuando el archivo NO cambia** ("sin cambios" por hash
  idéntico): si el código de proveedor leído del nombre es distinto al
  ya guardado (o no había ninguno), se actualiza aparte con un `PUT
  /admin/articulos/:id/codigo-proveedor` ligero, sin volver a subir el
  archivo entero. Así, relanzar la carga masiva sobre una carpeta ya
  subida basta para rellenar retroactivamente el código de todo lo que
  ya estaba, sin tocar ni un archivo. Para poder comparar, `GET
  .../documentos-hash` ahora devuelve también el código ya guardado,
  no solo el hash.
- **Editable a mano** (`ArticuloForm.jsx`): nuevo campo "Código de
  proveedor (nombre del proveedor asignado)" con su propio botón
  Guardar, deshabilitado si el artículo no tiene proveedor asignado
  todavía. Usa el mismo `PUT /admin/articulos/:id/codigo-proveedor`.
- **Visible en la ficha del artículo** (`ArticuloDetail.jsx`): nueva
  fila "Código proveedor" junto a "Proveedor", con el código del
  proveedor asignado — y, en el panel de alternativas (v1.11.0), cada
  grupo de proveedor muestra también su propio código junto al nombre.
  `obtenerArticulo` y `obtenerFichasPorProveedor`
  (`articulosController.js`) lo añaden a su respuesta.
- **Verificación**: `parsearNombreArchivo` probado aparte con nombres
  de archivo reales (con y sin el segmento de código de proveedor) —
  confirmado que extrae el código correcto y sigue devolviendo `null`
  para nombres sin el formato esperado, igual que antes. También `npm
  run build` y `node --check` de todos los archivos backend tocados,
  sin errores.
- **Pendiente antes de desplegar**: ejecutar la migración
  `2026-08-20_codigos_proveedor.sql` en el SQL Editor de Supabase —
  sin ella, cualquier subida por carga masiva o guardado manual del
  código dará error (tabla inexistente).

---

## v0.47 — Ficha del artículo: ver alternativas de otros proveedores (v1.11.0 — desplegado)

Víctor preguntó si la ficha del artículo mostraba todas las fichas
técnicas de ese DALI o solo la del proveedor asignado. Repasando el
código (`obtenerFichasArticulo` en articulosController.js), confirmé que
solo se enseña la del proveedor asignado en ese momento — el resto
(guardado por la migración "documentación por proveedor" del 2026-08-17)
queda en reserva, visible solo como un aviso genérico para admin
indicando que existe, sin poder abrirla.

A partir de ahí, a Víctor se le ocurrió: si un DALI tiene fichas
técnicas de varios proveedores distintos, poder verlas todas
clasificadas por proveedor directamente desde la ficha, a modo de
"alternativas del mercado" para ese artículo.

Antes de implementarlo, pregunté dos cosas para no dar por hecho el
alcance:

- **Quién debía verlo**: ¿todos los usuarios de la app (admin y hotel) o
  solo admin, igual que el aviso de "documentación en reserva" que ya
  existía? Víctor eligió **todos los usuarios**.
- **Qué tipo de documentación incluir**: ¿solo fichas técnicas, técnicas
  + seguridad, o también la imagen de cada proveedor? Víctor eligió
  **fichas técnicas + de seguridad** (sin imagen).

Con eso decidido:

- **Nuevo endpoint `GET /articulos/:id/fichas-por-proveedor`**
  (`backend/src/controllers/articulosController.js`,
  `obtenerFichasPorProveedor`): a diferencia de `obtenerFichasArticulo`
  (que filtra por `id_proveedor = articulo.id_proveedor`), este trae
  TODAS las fichas técnica/seguridad del artículo con proveedor
  asignado (se excluyen las legado sin `id_proveedor`, si quedara
  alguna sin migrar), las agrupa por proveedor y marca cuál es el
  asignado. Sin `requireAuth`/`optionalAuth`, igual que la ruta
  hermana `/fichas` — no distingue rol, lo ve cualquiera que use la
  app. `backend/src/routes/articulos.js`.
- **`frontend/src/services/api.js`**: nueva `fetchFichasPorProveedor()`,
  con fallback de demo (dos proveedores simulados) para poder ver el
  panel sin backend real.
- **`frontend/src/components/ArticuloDetail.jsx`**: nuevo botón "Ver
  alternativas de otros proveedores" debajo de las fichas del
  proveedor asignado — al pulsarlo (y solo entonces, para no añadir una
  petición de más a cada apertura de ficha) pide las fichas por
  proveedor y muestra, para cada proveedor DISTINTO del asignado
  (el asignado ya se ve arriba, no se repite aquí), sus fichas técnica
  y de seguridad como enlaces. Si no hay ninguna alternativa, se avisa
  con un mensaje en vez de dejar el panel vacío. Estilos nuevos en
  `frontend/src/styles/index.css` (`.detail-alternativas`,
  `.btn-alternativas`, `.alternativas-panel`, `.alternativa-grupo`),
  reutilizando las clases `.btn-ghost`/`.alert`/`.ficha-link` ya
  existentes para no introducir un estilo distinto al resto de la app.
- **Verificación**: la lógica de agrupar por proveedor y ordenar (el
  asignado primero, el resto alfabético, con acentos) se probó aparte
  con datos de ejemplo — confirmado que agrupa bien, ordena bien
  incluyendo nombres con tilde, y que el filtro de "otros proveedores"
  del frontend excluye correctamente al asignado. También `npm run
  build` sin errores.
- **Sin cambios de esquema**: usa las mismas tablas `fichas` (con su
  columna `id_proveedor`) que ya existían desde la migración
  2026-08-17_documentacion_por_proveedor.sql — no hace falta migrar
  nada nuevo.

---

## v0.46 — Carga masiva: subida en paralelo en vez de una a una (v1.10.0 — desplegado)

Víctor preguntó por qué el navegador vuelve a pedir confirmación para
subir 2.617 archivos cada vez que relanza la carga masiva sobre la
misma carpeta, sin haber cambiado nada en ella, y notó que el proceso
"relentiza mucho". Antes de tocar nada, le expliqué que son dos cosas
distintas:

- **El aviso del navegador ("¿Quieres subir X archivos a este sitio
  web?")** no lo controla la app: es el comportamiento estándar de
  `<input type="file" webkitdirectory>` — Chrome no recuerda nunca el
  permiso de una carpeta entre selecciones, así que siempre vuelve a
  preguntar. Y ese aviso en sí es instantáneo (solo lista archivos, no
  procesa nada), así que no es la causa de la lentitud percibida.
  Evitarlo del todo requeriría cambiar a la File System Access API
  (recuerda el permiso, pero solo en Chrome/Edge) — se deja pendiente,
  ver más abajo.
- **La lentitud real** estaba en `handleProcesar()`: los archivos se
  subían secuencialmente, uno detrás de otro, y por cada uno se hacían
  dos peticiones de red (`fetchArticulo` + `fetchHashDocumento`) antes
  de decidir siquiera si hacía falta subirlo. Con carpetas de miles de
  archivos, eso son miles de idas y vueltas en fila.

Preguntado explícitamente qué hacer con esta explicación de por medio,
Víctor pidió atacar la lentitud real (paralelizar), dejando la API de
selección de carpeta para otro momento.

- **Cambio en `frontend/src/components/admin/CargaMasivaModal.jsx`**:
  la lógica de cada archivo (comprobar artículo → comparar hash →
  subir si hace falta) se extrajo a `procesarFila()`, y
  `handleProcesar()` ahora lanza hasta `CONCURRENCIA_SUBIDA` (6)
  "trabajadores" en paralelo que van consumiendo un índice compartido
  de filas pendientes — en cuanto uno termina su archivo, coge el
  siguiente disponible, sin bloques fijos ni huecos. 6 es un término
  medio: baja mucho el tiempo total sin disparar demasiadas peticiones
  a la vez contra un backend de un único proceso (plan gratuito de
  Render) ni contra Supabase Storage.
- **El resultado por archivo no cambia**: subido / sin cambios (ya
  estaba igual) / error se calculan exactamente igual que antes, fila a
  fila — solo cambia el orden en que se van completando, ya no es
  estrictamente el de la tabla.
- **Verificación**: simulado el reparto por trabajadores fuera de React
  (mismo algoritmo, con retardos aleatorios) contra varios tamaños,
  incluyendo un caso de 2.617 filas con un 99% pendientes —
  confirmado que cada fila pendiente se procesa exactamente una vez
  (ninguna se salta ni se duplica) y que la concurrencia real nunca
  supera 6, sea cual sea el tamaño de la carpeta. También `npm run
  build` sin errores.
- **Pendiente, no incluido en esta entrega**: la File System Access API
  para que el navegador no vuelva a pedir la carpeta cada vez. Se
  ofreció como opción y Víctor prefirió centrarse primero en la
  velocidad; queda abierto por si se retoma más adelante.

---

## v0.45 — Importar Excel: aviso falso de "cambio de código SAP" por un desajuste de tipos, no un cambio real (v1.9.1 — desplegado)

Reportado por Víctor justo después de desplegar v1.9.0 (importación en
segundo plano): la importación terminó bien (30.175 filas procesadas),
pero avisó de 946 artículos con "cambio de código SAP" mostrando el
mismo valor a ambos lados, p.ej. `código SAP: "10200425" →
"10200425"`. Preguntó por qué, si no se había cambiado ninguna
descripción.

- **Causa**: `articulos.codigo_sap` es una columna `text` en Supabase
  (ver schema.sql) — al leerla, Supabase siempre devuelve un string de
  JS. Pero `XLSX.utils.sheet_to_json()` (que parsea el Excel) tipa cada
  celda según el tipo que Excel le haya asignado, no según la columna
  de destino: una celda con un código puramente numérico como
  "10200425", si no está formateada como texto en el Excel de origen,
  se lee como un `number` de JS. La comparación de
  `avisosActualizacion` (`(antes.codigo_sap || "") !==
  (nuevo.codigo_sap || "")`) hacía entonces `"10200425" !== 10200425`
  — en JavaScript, `!==` compara también el tipo, así que esto da
  `true` aunque el valor sea idéntico como texto. Resultado: CASI
  CUALQUIER artículo con código SAP puramente numérico (la inmensa
  mayoría) se marcaba como "cambiado" en TODAS las importaciones,
  aunque nada hubiera cambiado de verdad — de ahí el número tan alto
  (946) sin que hubiera ninguna razón real para tantos cambios de golpe.
- **Verificación del diagnóstico**: reproducido con la propia librería
  `xlsx` — un workbook con una celda numérica `10200425` (sin formato
  de texto) se lee de vuelta como `typeof === "number"`; comparado
  contra el string `"10200425"` que devolvería Supabase, `!==` da
  `true`. Tras aplicar la conversión a texto antes de comparar, el
  mismo caso da `false` (sin cambio), como debe ser.
- **Cambio en `backend/src/controllers/importController.js`**: nueva
  función `textoONull(valor)` (convierte a string y recorta espacios, o
  `null` si está vacío) aplicada a `codigo_sap`, `descripcion_sap` y al
  resto de campos de texto que vienen del Excel de SAP (unidad,
  grupo de productos, categoría de valoración, tipo de producto, grupo
  de compras...) al construir cada fila del upsert — antes de
  compararlos con lo guardado y antes de guardarlos, así ambos lados de
  cualquier comparación son siempre texto, nunca una mezcla de string y
  number.
- **Sin cambios de esquema** ni de comportamiento salvo dejar de
  generar avisos falsos — los cambios reales de código SAP se siguen
  detectando y avisando igual que siempre.
- **Verificación**: `node --check` del controller sin errores.
  Reproducción aislada con `xlsx` real (no simulada) confirmando el
  bug antes del fix y su ausencia después, con los mismos valores
  exactos del caso reportado (10200425).

## v0.44 — Importar Excel en segundo plano: la petición ya no aguanta todo el proceso (v1.9.0 — desplegado)

Reportado por Víctor con captura de DevTools: al pulsar "Procesar
importación" con los dos Excel, la petición `import-excel` acababa en
502 con cuerpo vacío a los 39,03s. Preguntó si era un fallo puntual o
si el proceso se estaba volviendo demasiado lento.

- **Diagnóstico**: no era un fallo puntual ni un problema de los datos.
  `POST /admin/import-excel` resuelve dimensiones (naturaleza, familia,
  subfamilia, proveedor) y guarda el catálogo completo en bloques de
  500 contra Supabase, TODO dentro de la misma petición HTTP, que no
  respondía hasta terminar. El troceo en bloques (con `setImmediate`
  entre uno y otro) ya existía para que el health check de Render no
  matara la instancia a mitad — pero eso no evita que la conexión HTTP
  en sí, de principio a fin, se corte por otro motivo: el tráfico pasa
  por un Cloudflare Worker de proxy inverso
  (`cloudflare-workers/dali-proxy-api.js`) hacia el backend en Render
  (plan free), y tanto el Worker como el proxy del plan gratuito
  cortan conexiones que tardan demasiado en recibir respuesta. A medida
  que el catálogo (~30.000 artículos) siga creciendo, el proceso
  completo cada vez tarda más, así que esto solo iba a empeorar.
- **Cambio**: `POST /admin/import-excel` ahora valida los dos ficheros
  (columnas requeridas, lectura del XLSX — rápido, en memoria) y, si
  está todo en orden, responde EN SEGUIDA con un `job_id`, sin esperar
  a que se guarde nada. El trabajo real (resolver dimensiones + los
  bloques de guardado) sigue corriendo en segundo plano dentro del
  mismo proceso Node
  (`procesarImportacionEnSegundoPlano()` en
  `backend/src/controllers/importController.js`), actualizando su
  progreso en un Map en memoria (`bloque_actual`/`total_bloques`). Nuevo
  endpoint `GET /admin/import-excel/estado/:jobId`
  (`backend/src/routes/admin.js`) para consultarlo.
- **Frontend**: `services/api.js` → `importExcel()` ahora hace el POST,
  coge el `job_id` y sondea el endpoint de estado cada 2s (con su propio
  timeout corto por consulta, tolerando hasta 5 fallos de red seguidos
  sin abortar el sondeo entero) hasta ver "completado" (devuelve el
  mismo resultado de siempre) o "error" (lanza con el mensaje real).
  `ImportarExcel.jsx` pinta "Procesando… bloque X de Y" en el botón y un
  aviso explicando que la importación sigue corriendo en el servidor
  aunque se cierre la pantalla.
- **Sin cambios de esquema**: el estado de cada trabajo vive en memoria
  del proceso Node, no en base de datos — deliberado, para no añadir
  tabla ni migración solo para esto. Contrapartida: si el servidor se
  reinicia a mitad de una importación, el trabajo en curso se pierde
  sin más aviso que dejar de avanzar (habría que relanzarla) — mismo
  riesgo que ya existía antes con la petición síncrona, no es una
  regresión. Los trabajos terminados se olvidan solos a los 30 min.
- **Verificación**: `npm run build` del frontend sin errores. Backend
  verificado con un arnés aislado (Express real + Excel de prueba +
  Supabase apuntando a un puerto cerrado a propósito): el POST responde
  202 con `job_id` en ~57ms (antes habría esperado a todo el proceso),
  el sondeo ve "procesando" mientras corre en segundo plano, y al fallar
  la conexión a Supabase (esperado, puerto cerrado) el trabajo pasa
  correctamente a "error" con el mensaje real en vez de perderse.

## v0.43 — Buscador e indicador de imagen genérica en "Documentación faltante" (v1.8.0 — desplegado)

Petición de Víctor Martin: "Podemos incluir un buscador en este apartado
similar al que ya tenemos en el panel principal? también se debería
indicar cuando la imagen cargada es genérica o del material".

- **Buscador**: `AdminDocumentacionFaltante.jsx` carga de golpe TODOS
  los artículos con algo pendiente (no pagina desde el servidor como el
  catálogo principal), así que el filtro es puramente en el navegador,
  sin llamada nueva al backend ni debounce — sobre nombre, código DALI
  (con y sin ceros a la izquierda) y proveedor, insensible a
  mayúsculas/tildes (misma normalización NFD que ya usan
  `CargaMasivaModal.jsx`/`ArticuloForm.jsx`). Con texto en el buscador,
  los grupos de proveedor con coincidencias se despliegan solos —
  buscar por el nombre de un proveedor entero equivale a pulsar su
  cabecera, porque todos sus artículos comparten ese campo.
- **Imagen genérica vs. propia**: no existe ninguna columna que marque
  explícitamente "esta imagen es la genérica de reserva del proveedor"
  — la carga masiva simplemente sube el mismo archivo "SIN IMAGEN" a
  todos los artículos del proveedor que no tenían foto propia (ver
  `CargaMasivaModal.jsx`, `NOMBRE_IMAGEN_GENERICA`). Pero desde v1.7.0
  cada imagen guarda su `hash_sha256`, así que si el mismo hash aparece
  en más de un artículo del mismo proveedor, es prácticamente seguro
  que es esa foto de reserva y no una específica del material — no ha
  hecho falta ninguna migración, solo agrupar por `(id_proveedor, hash)`
  en `calcularDocumentacionFaltante()`
  (`backend/src/controllers/documentacionController.js`) y devolver un
  nuevo campo `imagen_generica` (`true` = compartida/genérica, `false`
  = hash único/propia, `null` = hay imagen pero sin hash guardado —
  fila anterior a v1.7.0, no se puede saber). El frontend pinta
  "✓ (genérica)" o "✓ (sin verificar)" junto al check normal, con un
  `title` explicando el porqué al pasar el ratón.
- **Verificación**: `npm run build` del frontend sin errores (51
  módulos), `node --check` del controller sin errores. Sin cambios de
  esquema — no hace falta ninguna migración nueva para este cambio.

## v0.42 — Auditoría de documentación (a petición de Víctor Martin: "revisa que todo esté en su sitio")

Revisión completa del repo (no solo `.github`/`DEPLOY.md`/`HISTORIAL.md`
de v0.41) buscando código huérfano, inconsistencias entre `render.yaml`
y la documentación, y documentación desactualizada frente al código
real. Sin cambios de comportamiento de la aplicación — solo
configuración e documentación.

- **Código huérfano**: ninguno. Se verificó que los 3 archivos
  duplicados detectados en v0.39 (`components/AdminArticulos.jsx`,
  `components/ArticuloForm.jsx`, `ArticuloDetail.jsx` suelto fuera de
  `src/`) siguen fuera del repo, y que todos los controllers del
  backend están enganchados desde alguna ruta (ninguno sin usar).
- **`render.yaml` desincronizado desde la migración a Frankfurt** (5 de
  agosto): `DEPLOY.md` (sección "Migrar de región") afirma que
  `render.yaml` ya lleva `region: frankfurt` y `name: listado-DALI-SAP`
  — pero el archivo real seguía con `name: dali-backend` y sin
  `region` en absoluto. Es decir, un despliegue nuevo desde cero
  (Blueprint) habría creado el servicio con un nombre distinto al que
  el resto de `DEPLOY.md` da por hecho (`listado-DALI-SAP`), y en la
  región por defecto de Render (Oregon), no en Frankfurt. Corregido:
  `render.yaml` ahora sí lleva ambos campos.
- **`DALI_SSO_SECRET` ausente de `backend/.env.example`**: la entrada
  de HISTORIAL.md que documentó el SSO (ver más abajo, sección SSO)
  decía que se había añadido a `.env.example`, pero no estaba. Sin
  esto, replicar el entorno local desde cero deja el SSO roto sin
  ningún aviso hasta probarlo. Añadida la variable con comentario
  explicando que debe coincidir con el valor en
  `control-pedidos-princess`.
- **`DEPLOY.md`, tabla de variables del paso 3, no incluía
  `DALI_SSO_SECRET`**: Render la pide igualmente en el Blueprint (es
  `sync: false`), pero sin la tabla no queda claro qué valor poner.
  Añadida la fila.
- **`backend/README.md` describía la API previa a v1.7.0**: la sección
  "Importación de Excel y dimensiones nuevas" seguía documentando
  `codigo_proveedor` (texto libre, escrito en
  `articulos.codigos_proveedor_adjuntos`) como el mecanismo para
  asociar imagen/fichas a un proveedor — sustituido en v1.7.0 por
  `id_proveedor` real (FK a `proveedores`) y el modelo "una fila por
  artículo y proveedor". Tampoco mencionaba `POST /auth/sso` ni
  `GET /admin/articulos/:id/documentos-hash` (deduplicación por hash,
  también de v1.7.0), ambos ya en el código pero ausentes de la tabla
  de endpoints. Reescrita la tabla y la sección de imagen/fichas para
  reflejar el sistema actual.
- **`frontend/README.md` describía una versión bastante anterior**:
  cuentas demo desactualizadas (`usuario@demo.dali` en vez de
  `hotel@demo.dali`), rol `lectura` en vez de `hotel` (renombrado el
  2026-08-07), sin mención del login por SSO, y el panel de
  administración solo listaba "Artículos" e "Importar Excel" — sin
  "Carga masiva", "Usuarios" ni "Documentación faltante", las tres ya
  presentes en el sidebar desde hace varias versiones. Reescrita esa
  sección completa.
- Sin cambios de código de aplicación (frontend/backend) ni de
  esquema — todo el trabajo es de `render.yaml`, `.env.example` y los
  tres `.md` mencionados.

---

## v0.41 — Migración del keep-alive de GitHub Actions a cron-job.org

- **Detonante**: SSO desde `control-pedidos-princess` (menú lateral
  "Catálogo DALI") se quedaba colgado en "Comprobando sesión…" tras un
  rato sin usar la app. Al investigar, el keep-alive de
  `.github/workflows/keep-alive-dali.yml` (ping cada 10 min vía
  GitHub Actions) mostraba huecos reales de 20-36 minutos entre
  ejecuciones "cada 10 min" nominales — tiempo de sobra para que
  Render (límite de 15 min de inactividad en el plan Free) durmiera
  el backend de todos modos. No es un problema del código de la app
  ni de la config de Render: es que el scheduler de GitHub Actions en
  el plan Free no garantiza la cadencia configurada, solo la trata
  como orientativa.
- **Solución**: se activa un cronjob en
  [cron-job.org](https://cron-job.org) apuntando a `GET /health` del
  backend cada 5 minutos — servicio dedicado a esto, sin la cola
  compartida de GitHub Actions de por medio. Documentado el alta paso
  a paso en `DEPLOY.md` ("Keep-alive del backend (cron-job.org)").
- **Incidente en la primera hora de vida del cronjob** (20 de agosto,
  mañana): las dos primeras ejecuciones (9:40 y 9:45 hora Canaria)
  fallaron con 503. Diagnóstico cruzando logs de Render con el
  historial de cron-job.org:
  - Última actividad en los logs de Render antes del hueco: 07:59
    UTC (08:59 hora Canaria) — el backend se durmió a los ~15 min sin
    tráfico, sobre las 9:15 local, y no hay nada en los logs hasta el
    evento de deploy de las 8:46 UTC. Motivo: el cronjob de
    cron-job.org se activó por primera vez esa misma mañana, así que
    hasta entonces nada lo mantenía despierto.
  - En medio de esa ventana (8:46 UTC / 9:46 local) entró un push
    nuevo que disparó un auto-deploy en Render; su primer intento de
    build falló con *"Exited with status 1 because of an internal
    system error"* — error interno de la propia infraestructura de
    Render, no del código del proyecto. Un deploy manual inmediato
    (8:54 UTC) sí salió bien (**Live**).
  - El ping de las 9:55 (el primero tras el deploy manual bueno) ya
    dio `200 OK`, y todas las ejecuciones posteriores cada 5 min se
    mantuvieron en verde — confirmando que ambas causas (sueño previo
    a la activación del keep-alive + fallo de build transitorio
    solapado en el tiempo) quedaron resueltas y no son un patrón que
    se espere que se repita.
- **Cambio de configuración**: se retira el `schedule` de
  `.github/workflows/keep-alive-dali.yml` (queda solo con
  `workflow_dispatch`, para lanzarlo a mano si hace falta probar
  `/health` sin salir de GitHub) — mantenerlo como "respaldo" no
  aportaba cobertura real dado el problema de fiabilidad detectado, así
  que un único sitio fiable que vigilar (cron-job.org) es preferible a
  dos, uno de los cuales se sabe que falla. Se conservan todos los
  comentarios y el histórico de fixes previos del `.yml` (el ajuste de
  `--max-time 90` con reintentos, etc.) por si se quisiera reactivar
  el `schedule` en el futuro.
- Sin cambios en el código de la aplicación (backend/frontend) — todo
  el trabajo es de configuración de infraestructura (cron-job.org) y
  documentación (`DEPLOY.md`).

---

## v0.40 — Incidencia de despliegue en Render: credencial de GitHub rota (no relacionado con el código, afecta a varios proyectos)

- **Síntoma**: fallo de deploy con "We are unable to access to your
  GitHub repository" en tres proyectos independientes sobre el mismo
  GitHub (`controlpedidosprincesscanarias-coder`):
  **control-pedidos-chat**, **listado-DALI-SAP** y **dali-frontend**
  (este catálogo). Pese a que la GitHub App "Render" seguía instalada
  con `Repository access: All repositories` y permisos correctos en
  los tres casos. Ocurrió repartido en dos cuentas de Render distintas
  ("Organizador Escritorio's workspace" y "Central's workspace"), lo
  que confirma que no es un problema de un repo, proyecto o cuenta en
  concreto, sino algo que puede repetirse en cualquier servicio de
  Render conectado a este GitHub.
- **Causa real**: no es la GitHub App instalada la que falla, sino la
  credencial en **Render → Account Settings → Account Security → Git
  Deployment Credentials** (sección distinta de "Login Methods") —
  esa credencial se rompe/caduca de forma independiente a la
  instalación de la App en GitHub, así que revisar permisos en GitHub
  no sirve de nada por sí solo. Confirmado también por soporte de
  Render.
- **Solución** (repetible, confirmada en las dos cuentas): en esa
  credencial, menú "..." → **Disconnect credential** → **Add
  credential** → GitHub → completar la pantalla de autorización de
  GitHub. Tras eso el selector de repos de Render vuelve a listar todo
  con normalidad. **Si vuelve a pasar en cualquiera de los tres
  proyectos (o en uno nuevo), este es el primer sitio a mirar antes de
  tocar nada del código o de los permisos en GitHub.**
- **Efecto colateral encontrado al reintentar `dali-frontend`**: una
  vez resuelto el acceso, apareció un fallo distinto y no relacionado,
  `Publish directory dist does not exist` — el Build Command del
  servicio estaba vacío. Se rellenó con `npm install && npm run
  build` (Publish Directory ya era `dist`, correcto) y el deploy
  terminó bien.
- Sin impacto en el código de ninguna de las tres apps ni en
  producción real: los tres servicios siguieron sirviendo el último
  deploy bueno mientras se diagnosticaba, no hubo caída de cara al
  usuario.

---

## v0.39 — Limpieza de archivos huérfanos y ajuste del hallazgo de seguridad excluido (v1.7.0 — desplegado y verificado)

- Al revisar el proyecto completo para regularizar la versión a 1.7.0
  se detectaron 3 archivos del frontend con el mismo nombre que otros
  vigentes pero en ruta distinta, sin ningún import que los alcanzara
  desde `App.jsx`: `frontend/src/components/AdminArticulos.jsx` y
  `frontend/src/components/ArticuloForm.jsx` (versiones previas a la
  creación de la carpeta `components/admin/`, sin `CargaMasivaModal`
  ni el resto de cambios de v0.34 en adelante) y
  `frontend/ArticuloDetail.jsx` (duplicado suelto fuera de `src/`, sin
  los iconos de línea de v0.36). Es, casi con toda seguridad, la causa
  de la confusión de nombres repetidos ya anotada en la cabecera de
  este archivo ("Convención de entrega").
- A petición de Víctor, se eliminan los 3. Verificado con `npx esbuild`
  sobre `App.jsx` que la app compila igual tras el borrado — ninguno
  estaba en uso.
- **Hallazgo de seguridad de `control-pedidos-princess`**: se detectó
  que `README.md` y `HISTORIAL.md` enlazaban a
  `docs/hallazgo-seguridad-princess.md`, un archivo que no existe en
  este repo (ni en este ni en entregas anteriores revisadas). A
  petición de Víctor, se deja el hallazgo solo anotado (sin detalle ni
  enlace) en `README.md` y en las dos menciones de este archivo —
  se excluye deliberadamente el archivo en sí por tratarse de
  información crítica de otra aplicación, no un archivo perdido a
  recuperar.
- Sin impacto en producción: cambios puramente de limpieza de
  archivos y documentación, no requiere despliegue del backend.

---

## v0.38 — Deduplicación por hash SHA-256 en imágenes/fichas (v1.7.0 — desplegado y verificado)

- La carga masiva (`CargaMasivaModal.jsx`, v0.34) resube siempre todos
  los PDF/imágenes de la carpeta seleccionada, aunque el archivo sea
  exactamente el mismo que ya está guardado — caso habitual: se vuelve
  a lanzar la carga masiva sobre la misma carpeta compartida para
  coger solo lo que el proveedor haya añadido o cambiado desde la
  última vez. Sin nada que comparar, la única forma de saberlo era
  descargar y comparar el archivo ya guardado byte a byte.
- **Cambio en base de datos**: se añade `hash_sha256` (SHA-256 del
  contenido, en hex) a `fichas` e `imagenes`
  (`database/migraciones/2026-08-18_hash_documentos.sql`, ya reflejada
  en `database/schema.sql`). `NULL` para las filas ya existentes — no
  se recalcula en retroactivo (no hay acceso al archivo original desde
  SQL); se rellena solo la próxima vez que se vuelva a subir algo para
  esa fila.
- **Cambio en el backend** (`backend/src/controllers/
  storageController.js`): calcula el hash de cada archivo subido con
  `crypto.createHash("sha256")` y lo guarda en `fichas`/`imagenes`.
  Nuevo endpoint `GET /admin/articulos/:id/documentos-hash` (ver
  `backend/src/routes/admin.js`) para que el frontend pueda consultar
  el hash ya guardado de un artículo/tipo/proveedor antes de subir
  nada.
- **Cambio en el frontend**: nueva utilidad
  `frontend/src/utils/hashArchivo.js` (SHA-256 vía Web Crypto,
  `crypto.subtle.digest`, sin dependencias) usada por
  `CargaMasivaModal.jsx` para calcular el hash de cada archivo local y
  compararlo contra el hash ya guardado en el backend — si coinciden,
  se descarta la subida sin transferir el PDF/imagen entero.
- **Nota**: esta entrada documenta a posteriori un cambio que ya
  estaba implementado en el código (comentario fechado 2026-08-18 en
  `hashArchivo.js`) pero que se había quedado sin reflejar aquí ni en
  `CHANGELOG.md` — añadida al revisar el estado completo del proyecto
  antes de regularizar la versión a 1.7.0.

---

## v0.37 — Carga masiva: 17 proveedores con punto final en el catálogo no casaban con su carpeta (v1.7.0 — desplegado y verificado)

- Detectado al revisar una carga masiva real de fichas técnicas
  (`ARTICULOS_DALI.xlsx` + captura del modal "Carga masiva de fichas
  técnicas"): 17 carpetas de proveedor (`AHUMADOS CANARIOS, S.A`,
  `MERITEM S.L`, `SUSHICAN, S.L`...) aparecían como "no coinciden con
  ningún proveedor del catálogo y se han omitido", pese a existir en
  el catálogo con ese mismo nombre.
- **Causa**: el `nombre_proveedor` de esos 17 registros en el catálogo
  lleva un punto final (`AHUMADOS CANARIOS, S.A.`) que la carpeta
  correspondiente en disco no tiene (`AHUMADOS CANARIOS, S.A`) —
  probablemente por una normalización manual posterior del nombre en
  el Excel de origen, después de haberse creado ya las carpetas. La
  función `normalizar()` de `CargaMasivaModal.jsx` (v0.34) solo quitaba
  tildes y pasaba a mayúsculas, así que esa diferencia de puntuación
  bastaba para que la comparación de igualdad exacta fallara.
- **Cambio en `frontend/src/components/admin/CargaMasivaModal.jsx`**:
  `normalizar()` recorta espacios al inicio/final, colapsa espacios
  múltiples a uno solo y elimina punto(s) final(es), además de seguir
  quitando tildes. Usada tanto para casar carpeta↔proveedor como
  carpeta↔tipo (FICHAS TECNICAS/SEGURIDAD/IMAGENES), así que cubre
  ambos matching de una vez y cualquier variante similar de puntuación
  o espaciado que pueda darse en el futuro entre el nombre de carpeta
  del usuario y el `nombre_proveedor` del catálogo. No ha hecho falta
  tocar el Excel ni la base de datos.
- **Verificación**: comparado el listado completo de proveedores del
  catálogo (182, extraídos de `ARTICULOS_DALI.xlsx`) contra los
  nombres de carpeta reales de la captura — confirmado que las 17
  carpetas afectadas difieren únicamente en el punto final, y que con
  la nueva `normalizar()` las 17 pasan a casar. Sin acceso a la app
  real (backend + Supabase) desde este entorno para probar el modal en
  vivo.

---

## v0.36 — Iconos de línea para "Ficha técnica"/"Ficha de seguridad" en vez de emoji (v1.7.0 — desplegado y verificado)

- Víctor, con capturas de la sección "Fichas" de la ficha del
  artículo: "PODEMOS PONER INDICATIVOS MAS TECNICOS Y VISUALES PARA LAS
  FICHAS TECNICAS Y SEGURIDAD ?" — en su captura, el emoji 🛡️ (escudo)
  se veía casi como una gota azul, poco reconocible como "seguridad".
- **Cambio en `frontend/src/components/ArticuloDetail.jsx`**: se
  sustituyen los dos emoji (📄 Ficha técnica / 🛡️ Ficha de seguridad)
  por dos iconos SVG propios, `IconFichaTecnica` e `IconFichaSeguridad`
  — mismo estilo de línea fina que ya usa el icono del reloj en
  `App.jsx` (`viewBox 16x16`, `stroke="currentColor"`, sin relleno,
  salvo el punto del aviso): un documento con líneas de texto para la
  ficha técnica (hoja de especificaciones) y un escudo con un aviso
  dentro para la de seguridad (hoja de datos de seguridad/riesgos). Se
  usa `currentColor` (no un color nuevo) para heredar el único acento
  del sistema de diseño (`--brass`, ver comentario en
  `styles/index.css`: "acento único... reservado solo para 'No
  activo'" el otro color, `--wine`) — la distinción entre las dos
  fichas es de FORMA, no de color, para no romper esa regla.
- **Cambio en `frontend/src/styles/index.css`**: `.ficha-link` pasa de
  `display: block` a `display: flex` con `gap` para alinear el icono
  junto al texto (mismo patrón que `.estadisticas-item` en la cabecera).
- **Verificación**: `npx esbuild` sin errores sobre
  `ArticuloDetail.jsx`; `npx vite build` completo sin errores (50
  módulos). Renderizado también con Playwright contra un HTML mínimo
  con las mismas reglas CSS y los mismos SVG, para confirmar visualmente
  el resultado antes de entregarlo (captura enviada a Víctor) — no hay
  forma de levantar la app real completa (backend + Supabase) desde
  este entorno.

---

## v0.35 — "Comprobando sesión…" seguía colgándose: ssoLogin() se había quedado sin el timeout que sí tenía fetchSesionActual() (v1.7.0 — desplegado y verificado)

- Víctor, con las mismas dos capturas de siempre ("Comprobando
  sesión…"): "SE SIGUE QUEDANDO ASI CUANDO PASAMOS RATO SIN ENTRAR" —
  tras haber dado por resuelto este mismo síntoma en v0.33.
- **Causa**: v0.33 arregló `fetchSesionActual()` (la comprobación de
  sesión normal al cargar la app) añadiéndole timeout propio y
  capturando su error en `App.jsx`. Pero hay una TERCERA vía de entrada
  a la app, `ssoLogin()` — la que se usa al llegar desde el menú
  lateral "Catálogo DALI" de `control_pedidos` (`?dali_token=` en la
  URL, ver `App.jsx`) — que se quedó sin tocar en aquel arreglo: seguía
  haciendo un `fetch()` normal, sin `AbortController` ni límite de
  tiempo propio. "Pasar un rato sin entrar" es exactamente lo que dormía
  el backend (Render Free, ~15 min de inactividad) y entrar de nuevo por
  el enlace de `control_pedidos` — probablemente la vía habitual de
  Víctor para llegar a DALI — es la que seguía sin protección: con el
  backend dormido, ese `fetch` se podía quedar colgado indefinidamente,
  reproduciendo el mismo "Comprobando sesión…" congelado que se había
  dado por arreglado, aunque por una ruta de código distinta a la que
  se tocó en v0.33.
- **Cambio en `frontend/src/services/api.js`**: se extrae
  `mensajePorFalloDeRed(e)` (mismo texto que ya usaba
  `fetchSesionActual()` según sea timeout o fallo de red, ahora
  compartido) y se envuelve también `ssoLogin()` con
  `fetchConTimeout(..., TIMEOUT_SESION_MS)` — mismos 20s que
  `fetchSesionActual()`. De paso, se le aplica lo mismo a `login()`
  (el formulario normal de email/contraseña), que tampoco tenía
  timeout propio — no había ningún aviso de que esa vía fallara, pero
  es el mismo patrón de riesgo (backend lento/caído dejando el botón
  "Entrando…" colgado sin explicación) y el arreglo es idéntico y sin
  coste, así que se cierra la misma vía de bloqueo en las tres formas
  de entrar a la app en vez de solo en la que ya había dado la cara dos
  veces.
- **Verificación**: `npx esbuild` sin errores de sintaxis sobre
  `services/api.js`. Sin poder reproducir el cold-start real del
  backend desde este entorno (sandbox sin salida a `onrender.com`) —
  recomendado, tras desplegar, entrar por el enlace de `control_pedidos`
  después de un rato largo sin actividad (o parar el keep-alive un
  momento) para confirmar que ahora sí aparece el aviso de "el servidor
  está tardando más de lo normal…" en vez de quedarse colgada.
- **Nota aparte, no tocada aquí**: el keep-alive
  (`.github/workflows/keep-alive-dali.yml`, v0.32) solo hace ping de
  05:00 a 21:00 UTC (06:00-22:00 hora de Canarias) — fuera de ese
  horario el backend se duerme por diseño, así que un cold-start ahí es
  esperable y no un fallo; además, los cron de GitHub Actions no son
  puntuales al segundo (pueden retrasarse varios minutos en momentos de
  carga), así que un hueco puntual algo mayor de 15 min dentro del
  horario tampoco sería sorprendente. Este cambio no evita el
  cold-start en sí — solo hace que la app se recupere sola en vez de
  quedarse colgada cuando ocurre.

---

## v0.34 — Carga masiva rediseñada: por carpeta de proveedor, no por proveedor único al inicio, y documentación por proveedor en base de datos (v1.7.0 — desplegado y verificado)

- Víctor, tras preguntar cómo funcionaba realmente la carga masiva
  (capturas de la UI y de una carpeta real de Windows con `EMICELA` y
  `ORTHIDAL SL`, cada una con `FICHAS SEGURIDAD` / `FICHAS TECNICAS` /
  `IMAGENES` dentro), pidió cambiar el flujo por completo: "no vamos a
  pedir proveedor al inicio, solo ruta de búsqueda, en esa ruta la
  aplicación deberá buscar las carpetas con los nombres de los
  proveedores tal y como están definidos en el listado (...) si es
  imágenes recorrerá todos los proveedores y sus carpetas imágenes y
  grabarán la imagen para el DALI y el proveedor, pero la visualización
  en la ficha será para el proveedor asignado en línea, guardando el
  resto cargado por si el proveedor cambia".
- **Dos decisiones previas, confirmadas por Víctor (opción recomendada
  en ambas)**:
  1. Imagen/fichas ya existentes (sin proveedor asociado, del modelo
     anterior) se migran al proveedor que cada artículo tiene asignado
     ahora mismo, para que no desaparezca nada de la vista al pasar al
     nuevo modelo.
  2. Una carpeta de la ruta de búsqueda cuyo nombre no coincide con
     ningún proveedor del catálogo se omite y se avisa al final del
     proceso, sin bloquear el resto de la carga.
- **Modelo de datos** (`database/migraciones/2026-08-17_documentacion_por_proveedor.sql`,
  `database/schema.sql`): antes, cada artículo tenía como mucho una
  imagen (`articulos.url_imagen`) y una ficha de cada tipo
  (`fichas`, única por `(id_articulo, tipo)`), sin proveedor asociado.
  Ahora puede haber una versión por proveedor: `fichas` gana
  `id_proveedor` (con backfill al proveedor actual de cada artículo
  para las filas existentes) y la unicidad pasa a
  `(id_articulo, tipo, id_proveedor)`; nueva tabla `imagenes` con la
  misma forma que `fichas` (única por `(id_articulo, id_proveedor)`),
  poblada a partir de `articulos.url_imagen`. `id_proveedor` admite
  NULL (artículo o carga sin proveedor resoluble, caso residual).
  `articulos.url_imagen` y `articulos.codigos_proveedor_adjuntos`
  se dejan en el esquema sin borrar (histórico/reversibilidad) pero
  documentadas como obsoletas — la aplicación ya no las lee ni escribe.
- **Backend** (`backend/src/controllers/storageController.js`): las
  subidas (`subirImagenArticulo`/`subirFichaArticulo`) ahora reciben un
  `id_proveedor` opcional en el body — si no se manda, se usa el
  proveedor ya asignado al artículo (`resolverIdProveedor`), igual que
  el comportamiento anterior para una subida suelta desde la ficha. La
  ruta en Storage pasa a incluir el proveedor
  (`{codigoDali}/{proveedor|sin-proveedor}...`) para que varias
  versiones del mismo artículo no se pisen entre sí. Los borrados
  (`eliminarFichaArticulo`/`eliminarImagenArticulo`) pasan a ser
  quirúrgicos: solo tocan la fila del proveedor asignado, sin afectar a
  las reservas de otros proveedores; `eliminarAdjuntosArticulo` sigue
  borrando todo, de todos los proveedores, como antes (pensado para
  limpiar huérfanos). Como Postgres/PostgREST no encuentra NULL con
  `.eq()`, se añade `filtrarPorProveedor()` para usar `.is()` cuando
  corresponde, y se usa en todos los sitios que filtran por
  `id_proveedor` (aquí y en `articulosController.js`).
- **Backend — lectura** (`articulosController.js`): `obtenerArticulo` y
  `obtenerFichasArticulo` dejan de leer `articulos.url_imagen` /
  la fila única de `fichas` y en su lugar consultan `imagenes`/`fichas`
  filtrando por el `id_proveedor` que el artículo tiene asignado AHORA
  MISMO — este único cambio es lo que hace que, si el proveedor
  asignado de un artículo cambia más adelante (p.ej. al reimportar el
  Excel), la imagen/ficha de ese nuevo proveedor (si ya estaba guardada
  en reserva de una carga masiva anterior) pase a mostrarse sola, sin
  ningún código adicional en la importación. Nuevo campo
  `proveedores_con_documentacion_reserva` en la respuesta de
  `obtenerArticulo` (solo para admin), con los nombres de los demás
  proveedores que tienen algo guardado para ese artículo.
  `eliminarArticulo` (baja de ficha) pasa a limpiar en Storage las
  imágenes de TODOS los proveedores del artículo antes de borrarlo (el
  `on delete cascade` de la FK limpia las filas de `imagenes`/`fichas`
  solo, no el contenido real del bucket).
- **Backend — otros dos sitios que aún dependían de `url_imagen`**,
  encontrados con un barrido (`grep -rln "url_imagen"`) tras rehacer los
  controladores principales, para no dejar ningún consumo obsoleto sin
  arreglar:
  - `documentacionController.js` ("Documentación faltante"): en vez de
    comprobar solo si existe alguna fila en `imagenes`/`fichas` para un
    artículo, ahora comprueba si existe la del proveedor que el
    artículo tiene asignado — si no, cuenta como que "falta", aunque
    haya una versión guardada en reserva de otro proveedor (que es
    justo lo correcto: esa versión no se está mostrando).
  - `importController.js` (avisos de "cambios detectados" y detección
    de artículos desaparecidos con documentación adjunta): pasan a
    consultar `imagenes` en vez de `articulos.url_imagen`, con criterio
    amplio ("cualquier proveedor cuenta") porque aquí el objetivo es
    avisar a un humano de que hay algo que revisar/limpiar, no decidir
    qué se muestra.
- **Frontend — `CargaMasivaModal.jsx` reescrito**: el campo de texto
  "Proveedor" del inicio desaparece; en su lugar, un único selector de
  carpeta (`webkitdirectory`, como antes) que apunta a la raíz de
  búsqueda. Al elegir la carpeta, la app recorre todos los archivos,
  identifica el proveedor de cada uno por el nombre de su carpeta de
  primer nivel (comparado contra el catálogo real de proveedores, sin
  tildes/mayúsculas) y, dentro de esa carpeta, filtra por la subcarpeta
  del tipo correspondiente a este modal (igual criterio de nombres que
  ya existía). Las carpetas de primer nivel que no coinciden con ningún
  proveedor se listan aparte, como aviso, sin bloquear el resto. La
  tabla de resultados gana una columna "Proveedor"; cada subida manda
  el `id_proveedor` real (resuelto de la carpeta) en vez del antiguo
  `codigo_proveedor` de texto libre sacado del nombre del archivo (que
  ya no se usa para nada, aunque el formato de nombre —
  `codigoDali_codigoSap_codigoProveedor_nombre.ext` — se sigue
  exigiendo igual, por compatibilidad). El mensaje de cada fila subida
  indica si coincide con el proveedor asignado del artículo o si queda
  "en reserva" — ya no es un aviso de anomalía, es el funcionamiento
  normal esperado de una carga con varios proveedores a la vez.
- **Frontend — el resto**: `api.js` renombra el parámetro
  `codigoProveedor` a `idProveedor` en `subirImagenArticulo`/
  `subirFichaArticulo` (mandan `id_proveedor` en vez de
  `codigo_proveedor`). `ArticuloForm.jsx` quita el campo suelto "Código
  de proveedor"; el buscador de proveedor que ya existía ahora resuelve
  directamente el `id_proveedor` real que se manda al backend (en
  blanco = usa el proveedor ya asignado al artículo). El aviso de
  "varios proveedores" de `ArticuloForm.jsx` y `ArticuloDetail.jsx` pasa
  de leer `codigos_proveedor_adjuntos` (congelado, ya no se escribe) a
  `proveedores_con_documentacion_reserva`, con redacción informativa en
  vez de alarmante. El indicador equivalente en la tabla de
  `AdminArticulos.jsx` se retira sin más: ese dato ya no se puede
  calcular fila a fila desde el listado sin consultas adicionales por
  artículo, y mantener el antiguo (congelado, cada vez más desfasado)
  era peor que no mostrar nada — el dato real y al día sigue disponible
  por artículo, abriendo su panel "Imagen / Fichas".
- **Verificación**: `node --check` sin errores en los cuatro
  controladores de backend tocados
  (`storageController.js`, `articulosController.js`,
  `documentacionController.js`, `importController.js`); `npm install` +
  `npx vite build` en `frontend/` sin errores (50 módulos, build de
  producción completo). Sin poder probar contra Supabase/Storage reales
  desde este entorno (sandbox sin esa conexión) — antes de desplegar,
  ejecutar a mano la migración SQL en el editor de Supabase (fuera de
  este entorno) y probar una carga masiva real con la estructura de
  carpetas de ejemplo (proveedor con varias subcarpetas de tipo) para
  confirmar que las reservas y el cambio de proveedor asignado se
  comportan como se espera.

---

## v0.33 — "Comprobando sesión…" colgada varios minutos: timeout y manejo de error en fetchSesionActual()

- Aviso de Víctor con dos capturas de la app parada en "Comprobando
  sesión…": "SE QUEDA ASI UNOS MUNUTOS" — venía justo después de revisar
  el fallo del keep-alive (v0.32), así que apuntaba al mismo origen: el
  backend lento/dormido en Render.
- **Causa encontrada en el código** (`frontend/src/App.jsx` +
  `frontend/src/services/api.js`): `App` empieza con `sesion === undefined`
  y muestra "Comprobando sesión…" hasta que se resuelve; para eso llama a
  `fetchSesionActual().then(setSesion)` — **sin `.catch()`**, confiando en
  el comentario de esa función ("nunca lanza"). Pero `fetchSesionActual()`
  hacía un `fetch()` normal, sin ningún timeout propio: si el backend
  tardaba en responder (cold-start de Render) o la conexión fallaba, la
  promesa se quedaba pendiente hasta que el propio navegador se rendía
  por su cuenta — de ahí los "minutos" — y si entonces rechazaba, al no
  haber ningún `.catch()` en `App.jsx` la promesa quedaba sin manejar:
  `sesion` no se resolvía nunca y la pantalla de carga no salía de ahí ni
  aunque el backend se hubiera despertado ya, solo recargando la página a
  mano.
- **Cambio en `services/api.js`**:
  - `fetchConTimeout()`: envoltorio nuevo sobre `fetch()` con
    `AbortController`, reutilizable.
  - `fetchSesionActual()` usa ahora `fetchConTimeout(..., TIMEOUT_SESION_MS)`
    con `TIMEOUT_SESION_MS = 20000` (20s — de sobra para una respuesta
    normal, sin dejar al usuario esperando minutos si de verdad hay un
    problema). Deja de estar documentada como "nunca lanza": ahora SÍ
    puede rechazar (timeout, red caída, o JSON inesperado en la
    respuesta — p.ej. una página de error en vez de JSON durante un
    cold-start a medias), siempre con un mensaje en español listo para
    enseñar en pantalla, no un error técnico crudo.
- **Cambio en `App.jsx`**: el `useEffect` de arranque ahora sí encadena
  `.catch()` a `fetchSesionActual()` — si falla, cae al login normal
  (como si no hubiera sesión) pero mostrando el motivo, reutilizando el
  mismo mecanismo que ya existía para errores de SSO (antes
  `errorSso`/`setErrorSso`, renombrado a `avisoInicial`/`setAvisoInicial`
  porque ahora cubre los dos casos). Así nunca se vuelve a dar el caso de
  `sesion` sin resolver: o hay sesión, o no la hay, o hay un aviso
  explicando por qué no se pudo comprobar — pero la pantalla de carga
  siempre acaba saliendo sola.
- **Verificación**: `npm install` + `npx vite build` en `frontend/` sin
  errores (50 módulos, build de producción completo); `node --check`
  sobre `services/api.js` sin errores de sintaxis. Sin poder probarlo
  contra el backend real desde este entorno (sandbox sin salida a
  `onrender.com`) — recomendado abrir la app tras desplegar esto y forzar
  el caso lento (p.ej. tras un rato largo sin actividad) para confirmar
  que ahora sí aparece el aviso en vez de quedarse colgada.

---

## v0.32 — Fix del keep-alive: el propio ping fallaba por timeout corto en el cold-start

- Aviso recibido por correo de GitHub Actions: "Keep-alive backend DALI:
  All jobs have failed" — el paso `ping` fallaba en ~32s, dos ejecuciones
  seguidas.
- **Causa**: el workflow (`.github/workflows/keep-alive-dali.yml`, v0.20)
  usa `curl --fail --max-time 30` contra `GET /health`. Si el backend
  llevaba dormido lo bastante (plan Free de Render, se duerme tras ~15
  min sin peticiones), el cold-start real puede tardar 40-60s o más en
  responder — más que el margen de 30s que tenía el propio ping, así que
  `curl` corta por timeout (`curl: (28) Operation timed out`) justo
  antes de que el backend termine de arrancar. Es decir: el workflow que
  existe para evitar el cold-start se encontraba con uno igualmente en
  el primer ping del día (o tras cualquier hueco largo sin tráfico), y
  fallaba en vez de simplemente tardar más esa vez.
- **Diagnóstico hecho sin acceso a los logs reales de Actions ni al
  panel de Render** (sesión en la nube sin navegador conectado ni
  credenciales de Render en este momento) — inferido a partir del
  tiempo de fallo (32s, justo el margen de 30s más el arranque del
  runner) y del comportamiento conocido de Render Free. **Pendiente de
  confirmar**: si tras este cambio se siguen viendo fallos, revisar
  directamente en el panel de Render que el servicio `dali-backend-fr`
  no esté suspendido por otro motivo (p. ej. inactividad prolongada más
  allá del sueño normal, o algún límite del plan Free).
- **Cambio**: `curl --max-time 30` → `--max-time 90` (margen cómodo para
  un cold-start típico) y se añade `--retry 2 --retry-delay 10
  --retry-all-errors`, para que una sola respuesta lenta o un 5xx
  mientras el servicio todavía arranca no tumbe el job entero — reintenta
  hasta 2 veces más, con 10s de espera entre cada uno, todo dentro de la
  misma ejecución.
- Sin pruebas end-to-end contra el Render real desde este entorno
  (sandbox sin salida a `onrender.com`) — sintaxis del YAML verificada
  con `python3 -c "import yaml; yaml.safe_load(...)"`, sin errores.
  Recomendado lanzarlo a mano una vez (`workflow_dispatch`, pestaña
  Actions) para confirmarlo en real antes de dejarlo correr solo.

---

## v0.31 — Limpieza de pendientes desactualizados (documentación, sin cambios de código)

- A petición de Víctor ("que mas tenemos pendiente?" → repaso conjunto
  de pendientes de este proyecto y de `control-pedidos-princess`; "si
  por favor" → confirmación para limpiar esta lista), se revisó
  entrada por entrada la sección "Pendientes acumulados" de este
  archivo y la sección "Pendientes generales" de `README.md` contra el
  estado real del código, en vez de fiarse de lo que decían.
- Resultado: 4 puntos que ya estaban resueltos desde hacía versiones
  pero seguían anotados como pendientes:
  - Borrar una ficha ya subida sin sustituirla → resuelto en v0.27.
  - Despliegue en Render con CI/CD desde GitHub → hecho desde v0.6.
  - URLs firmadas para imágenes/PDF (`createSignedUrl`) → ya
    implementado.
  - Contraseñas en texto plano en `control-pedidos-princess` → corregido
    en ese proyecto (`_verifica_y_migra_password`, hash +
    migración automática).
  - Además, en `README.md` (sección "Pendientes generales") dos frases
    describían como pendiente el "login real" y las "URLs firmadas",
    ambos implementados hace varias versiones.
- Se quitaron de las listas de pendientes (dejando constancia de por
  qué, con una nota de limpieza fechada, no borrando el rastro sin
  más) y solo quedan los puntos genuinamente abiertos: recuperación de
  contraseña por email + verificación por inactividad (backend, falta
  proveedor de email) y la pantalla de "olvidé mi contraseña"
  (frontend). No se ha tocado nada de `backend/README.md` ni
  `frontend/README.md`: sus propias secciones de pendientes se
  revisaron también y seguían siendo correctas.
- Sin impacto en producción: cambio puramente documental, no requiere
  despliegue.

---

## v0.29 — SSO desde Control de Pedidos (v1.6.0 — desplegado y verificado)

- Integración pedida por el usuario (Víctor): que los usuarios de
  `control-pedidos-princess` (otro proyecto, hasta ahora sin relación
  operativa con este — con un único vínculo previo, puramente de
  referencia de diseño, por un hallazgo de seguridad de contraseñas en
  texto plano detectado y corregido en ese proyecto; detalle no
  documentado en este repo por tratarse de información de otra
  aplicación) accedan a
  este catálogo desde su menú lateral/Dashboard, con la cuenta
  aprovisionada automáticamente y el rol correcto: rol `compras`
  (comprador) allí → `admin` aquí; rol `hotel` allí → `hotel` aquí
  (coincide de nombre — no es casualidad: el rol de solo lectura se
  renombró de `lectura` a `hotel` el 2026-08-07, ver
  `database/migraciones/2026-08-07_rol_lectura_a_hotel.sql`). El
  registro completo de la decisión de diseño (por qué SSO transparente
  y no cuentas con login propio, ni un simple enlace) está en el
  historial unificado del otro proyecto,
  `docs/HISTORIAL_CAMBIOS.md` en `control-pedidos-princess`, entrada
  `2026-08-14 11:35`.
- Nuevo `POST /auth/sso` (`authController.js`): verifica un token
  firmado (HMAC-SHA256, secreto compartido `DALI_SSO_SECRET`, ~60s de
  validez, antirrepetición por `jti`) emitido por el backend de Control
  de Pedidos, y aprovisiona/actualiza el usuario en `usuarios` — nuevo
  usuario: contraseña aleatoria e inutilizable, solo entra vía SSO;
  usuario ya existente: se actualiza nombre/rol, nunca se toca el
  `hash_password` (por si en el futuro también necesita entrar con
  usuario/contraseña propios de DALI).
- Frontend: `App.jsx` detecta `?dali_token=` en la URL al montar, limpia
  la URL enseguida (no debe quedar en el historial del navegador ni
  poder reutilizarse recargando), y llama a `ssoLogin()`
  (`services/api.js`) en vez de mostrar `LoginScreen`. Si el SSO falla,
  cae al login normal mostrando el motivo (`LoginScreen` acepta ahora
  un `errorInicial`).
- Nueva variable de entorno `DALI_SSO_SECRET` (`.env.example`,
  `render.yaml`) — debe ser idéntica a la del otro servicio de Render.
- Verificación: `node --check` sobre los ficheros del backend tocados,
  sin errores; JSX comprobado con `esbuild` (sin bundlear), sin
  errores. Probado en producción por el usuario con los tres roles
  reales de Control de Pedidos: admin → `admin` ✅, compras → `admin`
  ✅, hotel → `hotel` ✅.

---

## v0.30 — LISTADO_CODIGOS_DALI_-_SAP.xlsx cambia de estructura: import robustecido, 2 columnas SAP nuevas capturadas (v1.6.0 — desplegado y verificado)

- Aviso del usuario (Víctor): el Excel de SAP había cambiado de
  estructura, con columnas nuevas insertadas — pidió comprobar que el
  import seguía sirviendo y que la información recogida seguía siendo
  válida.
- Comprobación con el fichero real (30.174 filas), usando la misma
  versión exacta de la librería `xlsx` (SheetJS) que usa
  `importController.js` en producción, no una suposición: como el
  import lee las columnas **por nombre** (no por posición), insertar
  columnas nuevas en medio no rompe nada — `CODIGO DALI`, `ACTIVO
  DALI`, `CODIGO SAP - TEST`, `DESCRIPCION SAP - TEST` siguen exactos.
  Sin duplicados de `CODIGO DALI`, solo 1 fila (de 30.174) con `ACTIVO
  DALI` en blanco, sin impacto (ese campo del Excel SAP no se usa para
  calcular `activo_dali`, que sale del otro Excel).
- Al mirar más a fondo, sí encontré algo real que corregir (no causado
  por este cambio de Excel, ya existía, pero es el mismo tipo de
  problema — "el Excel trae información que la app no mantiene al
  día"): el esquema ya reservaba columnas para
  `unidad_sap`/`grupo_productos_sap`/`descripcion_grupo_sap`/
  `indicador_impuestos_sap`/`grupo_compras_sap`/`nombre_grupo_compras_sap`
  desde el principio, rellenadas una vez en la carga inicial
  (`build_csvs.py`) pero nunca refrescadas por el import del día a día
  — se habían quedado congeladas con el valor del primer día, sin que
  nadie lo notara porque ningún sitio de la app las lee ni las muestra
  (comprobado con búsqueda completa en frontend y backend).
- Decisión del usuario, de tres opciones planteadas (dejarlo tal cual /
  capturar sin mostrar / capturar y mostrar en la ficha): **capturar en
  base de datos, sin mostrarlo todavía**. Aplicado:
  - Migración `2026-08-14_categoria_tipo_producto_sap.sql`: nuevas
    columnas `categoria_valoracion` y `tipo_producto` (las 2 que de
    verdad son nuevas en el Excel — el resto de "nuevas" columnas del
    fichero ya tenían su columna reservada desde el principio).
    `schema.sql` actualizado igual, para instalaciones nuevas.
  - `importController.js`: las 8 columnas SAP (las 6 que ya existían +
    las 2 nuevas) se refrescan ahora en cada importación, no solo
    `codigo_sap`/`descripcion_sap` como hasta ahora.
  - `database/build_csvs.py` (el script de carga inicial, que su propio
    README dice que "es útil si se vuelven a actualizar los Excel" —
    justo el caso de hoy): leía la hoja SAP por posición fija de
    columna. Con el desplazamiento real de 3 columnas insertadas,
    `grupo_compras_sap`, `nombre_grupo_compras_sap` y la comparación de
    `ACTIVO DALI` habrían quedado leyendo la columna vecina
    equivocada, en silencio, sin ningún error — confirmado
    reproduciendo la resolución de índices contra el Excel real:
    `GRUPO COMPRAS SAP` pasó de la posición 9 a la 12, `NOMBRE GRUPO
    COMPRAS SAP` de 10 a 13, `ACTIVO DALI` de 11 a 14. Reescrito para
    resolver cada columna por su nombre de cabecera, igual que
    `importController.js`, con error explícito si una columna
    esperada no aparece.
- Verificación: `python3 -m py_compile database/build_csvs.py` sin
  errores; `node --check` sobre `importController.js` sin errores;
  resolución de columnas e índices de `build_csvs.py` reproducida
  contra el Excel real (SAP) confirmando los valores esperados fila a
  fila. No se ha podido probar `build_csvs.py` de principio a fin (no
  hay una copia actualizada de `ARTICULOS_DALI.xlsx` con la que
  probarlo junto al SAP nuevo), pero la parte que cambia — lectura de
  la hoja SAP — sí queda verificada contra el fichero real.
- **Despliegue**: la migración se ejecutó a mano en el SQL Editor de
  Supabase; `importController.js` se llevó al repo y Render lo
  desplegó sobre el servicio real, `listado-DALI-SAP` (Deployed). De
  paso se detectó y limpió un efecto secundario sin relación con este
  cambio en sí: el Blueprint sync de Render creó un servicio duplicado
  en blanco, `dali-backend` — el nombre que dice `render.yaml`, pero
  distinto del nombre real del servicio en producción
  (`listado-DALI-SAP`), así que Render no lo reconoció como "el mismo
  servicio" y creó uno nuevo en vez de actualizar el existente. Quedó
  en "Failed deploy" por variables de entorno incompletas (nunca tuvo
  tráfico real) y el usuario lo borró. Confirmado el usuario: última
  versión desplegada y funcionando.

---

## v0.28 — Borrar también la imagen, sin sustituirla (v1.5.3)

- Aclaración tras la v0.27: la ficha de seguridad ya estaba cubierta
  desde el principio (el bucle recorría "tecnica" y "seguridad" por
  igual) — lo que de verdad faltaba era la imagen, que nunca tuvo un
  botón equivalente.
- Nuevo `DELETE /admin/articulos/:id/imagen`: mismo criterio
  "quirúrgico" que las fichas — borra solo la imagen (Storage +
  `url_imagen`), sin tocar ninguna ficha. No toca
  `codigos_proveedor_adjuntos` (igual que el borrado de fichas): ese
  campo es un histórico compartido de qué proveedores han aportado
  algún adjunto, sin registrar cuál vino de la imagen y cuál de cada
  ficha, así que no hay forma fiable de saber si un código queda
  "huérfano" al borrar solo uno de los adjuntos — se deja tal cual.
- Botón "Eliminar" junto a la imagen en `ArticuloForm.jsx`, con la
  misma confirmación que ya tenían las fichas.

---

## v0.27 — Borrar una ficha suelta sin sustituirla (v1.5.2)

- Pedido concreto de la lista de pendientes: hasta ahora, la única
  forma de quitar una ficha técnica o de seguridad era subiendo una
  nueva del mismo tipo (upsert) — no había manera de dejar el hueco
  vacío sin rellenarlo con algo.
- Nuevo `DELETE /admin/articulos/:id/fichas/:tipo`: borra solo esa
  ficha (Storage + fila de `fichas`), sin tocar la imagen ni la ficha
  del otro tipo. Deliberadamente distinto del `DELETE
  /admin/articulos/:id/adjuntos` de la v1.5.1 (que borra todo de
  golpe, pensado para el caso de un artículo desaparecido del Excel) —
  ese es "todo o nada", este es quirúrgico, para el caso normal de
  "esta ficha en concreto ya no vale, quítala".
- Botón "Eliminar" junto al enlace "Ver PDF ya guardado" en
  `ArticuloForm.jsx`, con confirmación de por medio
  (`ConfirmDialog.jsx`, que ya había recuperado uso en la v1.5.1).

---

## v0.26 — Avisar y permitir limpiar documentación de artículos desaparecidos del Excel (v1.5.1)

- Pregunta que llevó a esto: "¿se tienen en cuenta los PDF de fichas y
  las imágenes almacenadas al importar?" — respuesta: sí, el upsert
  solo escribe los campos que vienen del Excel (nombre, clasificación,
  proveedor, código SAP, activo), nunca toca `url_imagen` ni la tabla
  `fichas`, así que una imagen o ficha nunca se borra ni se sustituye
  por una importación. Lo único que faltaba cubrir: el caso (raro, más
  error humano que algo que deba pasar en el flujo normal) de que un
  codigo_dali directamente desaparezca del Excel — como el `upsert`
  nunca borra artículos, ese artículo se queda tal cual en la base de
  datos, pero su documentación queda huérfana sin que nada lo avisara.
- Nuevo aviso `avisos_desaparecidos` tras cada importación: compara
  todos los codigo_dali en base de datos contra los del Excel recién
  subido, y de los que faltan, solo interesan los que tienen imagen
  y/o ficha que limpiar. Con un botón "Eliminar documentación" por
  artículo (confirmación de por medio) que borra la imagen/fichas
  (Storage + DB) sin tocar el artículo — decisión siempre manual, el
  aviso solo detecta y ofrece la opción.
- `ConfirmDialog.jsx` (sin ningún uso desde que se quitó el borrado
  manual de artículos en v1.4.0) recupera su sitio aquí, para
  confirmar este borrado — evita un `window.confirm()` nativo poco
  cuidado y reaprovecha un componente que ya estaba listo.

---

## v0.25 — Documentación faltante por proveedor (v1.5.0)

- Pedido: un apartado en Administración que muestre los artículos
  activos sin ficha técnica, sin ficha de seguridad y/o sin imagen,
  agrupados por proveedor asignado, para poder reclamar a cada
  proveedor justo lo que le falta aportar.
- Sin cambio de esquema: el cálculo compara todos los artículos
  activos (paginados en tandas de 1000, mismo límite ya conocido de
  Supabase/PostgREST) contra la tabla `fichas` y
  `articulos.url_imagen`, todo en JS — no había forma directa de
  expresar "NOT EXISTS en fichas" con supabase-js sin añadir una vista
  o una función RPC, y con los volúmenes de esta app (~6700 activos,
  unos pocos miles de fichas) hacerlo en JS es rápido de sobra.
- Incluye exportación a Excel del mismo listado — una hoja por
  proveedor si son 20 o menos (límite práctico: Excel no admite
  nombres de hoja de más de 31 caracteres ni ciertos símbolos, y
  decenas de pestañas dejan de ser manejables), si no, una sola hoja
  con columna "Proveedor" para agrupar visualmente sin pestañas.
- Probado generando y releyendo un .xlsx real (con las dos ramas,
  hojas separadas y hoja única) antes de darlo por bueno.

---

## v0.24 — Franja de estadísticas en la cabecera, visible para todos (v1.4.5)

- Pedido: fecha de la última actualización de Excel, total de
  artículos DALI activos, y de esos, cuántos tienen código SAP
  asociado — visible en la pantalla principal para cualquier usuario,
  no solo admin.
- Sin necesidad de una tabla de historial de importaciones: la fecha
  se deduce del máximo de `articulos.fecha_actualizacion` en toda la
  tabla — `importController.js` ya la actualiza en cada fila al hacer
  upsert, y desde que el Excel es la única vía para tocar artículos
  (v1.4.0), ese máximo ya ES la fecha de la última importación.
- Nuevo endpoint público `GET /estadisticas` (sin auth, como
  `/jerarquia` — no es información sensible), consultado una vez al
  entrar al catálogo.

---

## v0.23 — Carga manual coherente con la carga masiva: también pide proveedor (v1.4.4)

- Motivo: tras el aviso de "varios proveedores" (v0.22/v1.4.3), la
  subida manual desde la ficha de un artículo se quedaba fuera de esa
  trazabilidad — no pedía ningún dato de proveedor, así que nunca
  participaba en la detección.
- `ArticuloForm.jsx` (`EdicionAdjuntos`) añade, opcionales, "Nombre del
  proveedor" (mismo buscador autorellenable que `CargaMasivaModal.jsx`,
  contra `GET /admin/proveedores` — solo para avisar si no coincide
  con el proveedor real del artículo, no se guarda) y "Código de
  proveedor" (texto libre, mismo criterio que el nombre de archivo de
  la carga masiva — este sí alimenta
  `articulos.codigos_proveedor_adjuntos`).
- Con esto, el aviso de "varios proveedores" detecta solapamientos
  vengan de donde vengan — carga masiva o subida manual — sin ninguna
  diferencia de comportamiento entre las dos vías.

---

## v0.22 — Detectar cuando un mismo DALI recibe adjuntos de proveedores distintos (v1.4.3)

- Motivo: con la carga masiva por proveedor ya en marcha, era posible
  que el mismo `codigo_dali` recibiera imagen/fichas en cargas
  distintas hechas para proveedores distintos (artículo mal
  clasificado, cambio de proveedor no reflejado aún en Excel, o
  simplemente una carga con la carpeta equivocada) sin que quedara
  ningún rastro visible de que había pasado.
- Nueva columna `articulos.codigos_proveedor_adjuntos` (`text[]`, sin
  duplicados): se rellena con el `codigo_proveedor` sacado del nombre
  de archivo cada vez que la carga masiva sube algo — la subida suelta
  desde la ficha de un artículo no lo manda, así que ahí no se toca.
  Con más de un código en el array, se avisa en tres sitios: la ficha
  de consulta, la vista de gestión de imagen/fichas del admin, y un
  indicador directo en la fila de la tabla de Administración →
  Artículos.
- Se aprovechó para documentar explícitamente (ya era así, pero solo
  se sobreentendía) que cada subida sustituye siempre a la anterior —
  la más reciente reemplaza a la más antigua en la misma ruta del
  bucket y en la misma fila de `fichas`, nunca conviven dos versiones.

---

## v0.21 — Proxy con Cloudflare Workers para esquivar bloqueos de antivirus (v1.4.2)

- Motivo: algunos antivirus/filtros corporativos bloquean
  `*.onrender.com` por categoría (dominios de hosting en la nube),
  impidiendo el acceso a la app desde esas redes.
- Solución: dos Cloudflare Workers como proxy inverso — subdominio
  gratuito `*.workers.dev`, sin necesidad de dominio propio ni de
  delegar DNS de nada. Mismo patrón ya en uso en
  `control-pedidos-princess` (`proxy`/`proxy-chat`), replicado aquí
  desde cero (sin acceso al código original de esos dos, solo al
  patrón general de proxy inverso) como `dali-proxy.js` (hacia
  `dali-frontend.onrender.com`) y `dali-proxy-api.js` (hacia
  `dali-backend-fr.onrender.com`), en `cloudflare-workers/`.
- Se descartó primero la vía de dominio propio + Cloudflare DNS
  (CNAME con proxy naranja) al confirmar que el patrón ya usado en el
  otro proyecto era justamente Workers en `*.workers.dev`, más simple
  y sin coste ni gestión de DNS de por medio.
- Tras desplegar los dos Workers, se actualizaron `CORS_ORIGIN`
  (backend) y `VITE_API_URL` (frontend, con rebuild obligatorio — las
  `VITE_*` se incrustan en el build) a las URLs de los Workers en vez
  de las `onrender.com` directas.
- **Desplegado y verificado**: la URL de acceso diario a la app pasa a
  ser `https://dali-proxy.centralcompras1-canarias.workers.dev`
  (antes, directamente `https://dali-frontend.onrender.com`).

---

## v0.20 — Keep-alive de GitHub Actions para el backend en Render (v1.4.1)

- Nuevo `.github/workflows/keep-alive-dali.yml`: ping automático a
  `GET /health` del backend cada 10 minutos, de 06:00 a 22:00 hora de
  Canarias, todos los días — evita que el plan Free de Render duerma
  el servicio por inactividad (se duerme tras ~15 min sin peticiones;
  el primer request tras dormirse tarda decenas de segundos en
  responder). Mismo patrón que ya usa `control-pedidos-princess`.
- El cron de GitHub Actions va siempre en UTC fijo, y Canarias cambia
  de hora igual que el resto de la UE (WET/WEST) pero con un desfase
  distinto al peninsular — en vez de dos crons distintos según la
  época del año (y acordarse de cambiarlo a mano dos veces al año), se
  usa el rango `*/10 5-21 * * *` UTC, que es la unión de ambas
  estaciones: cubre las 06:00-22:00 locales tanto en invierno como en
  verano, a cambio de un margen inofensivo de ~1h de más en cada
  extremo según la estación.
- Verificado con una ejecución manual (`workflow_dispatch`) desde la
  pestaña Actions de GitHub antes de darlo por bueno: `Success`, 8s,
  el paso `ping` en 2s.

---

## v0.19 — De la exportación con formato al catálogo gestionado 100% desde Excel (v1.0.9 → v1.4.0)

Arco largo de trabajo, con varias entregas encadenadas — se resume aquí
de un tirón en vez de una entrada por cada `CHANGELOG.md` intermedio
(`v1.1.0` a `v1.4.0`), que ya tiene el detalle línea a línea de cada
cambio si hace falta consultarlo.

- **Jerarquía desplegable del sidebar** (`v1.3.0`): navegación en
  cascada naturaleza → familia → subfamilia, con filtrado en cascada
  del listado. Nuevo endpoint `GET /jerarquia`. Tras varias vueltas de
  ajuste de UX (scroll fijo vs. anidado en línea), se quedó en anidado
  en línea con un único scroll — la versión de "franjas separadas"
  rompía la relación visual entre naturaleza y sus familias.
- **Exportar PDF con formato real** (`v1.2.0`–`v1.3.0`): de un volcado
  de texto plano a una tabla de verdad, agrupada por familia/subfamilia,
  con cabecera repetida por página y numeración. Dos bugs de PDFKit
  encontrados probando con datos reales (30.167 filas): `ellipsis`
  sin `height` no trunca (desborda en vez de recortar), y
  `switchToPage()` no dibuja dentro del margen inferior — la
  numeración de página se resolvió pintándola al vuelo, sin
  `switchToPage`. Más tarde se descubrió que el `.order()` de Supabase
  sobre tablas relacionadas tampoco se aplicaba de verdad (mismo tipo
  de fallo silencioso ya visto en la jerarquía del sidebar) — el
  agrupado real se acabó haciendo en JS, no confiando en Postgres.
- **Gestión de usuarios** (`v1.3.0`): pantalla nueva en Administración,
  con los roles `admin`/`hotel` (antes `lectura` — renombrado por
  claridad, mismo comportamiento de solo lectura).
- **Bug real de identificación de artículos** (`v1.3.2`):
  `GET/PUT/DELETE /articulos/:id` filtraban por el `id` interno serial
  de la tabla, pero el frontend siempre manda `codigo_dali` — con
  miles de artículos, algún `codigo_dali` podía coincidir por
  casualidad con el `id` interno de OTRO artículo, editando/borrando
  el equivocado en silencio. Encontrado al construir la subida de
  imágenes (necesitaba tener claro qué identificador usar) y corregido
  en los cuatro sitios afectados.
- **Storage de imágenes y fichas** (`v1.3.2`): subida de foto y fichas
  técnica/seguridad por artículo, con URLs firmadas (buckets privados,
  24h de caducidad) — nunca una URL fija guardada en la base de datos.
- **Excel-como-única-fuente-de-verdad** (`v1.4.0`): decisión de
  producto importante — la edición manual de artículos desde
  Administración deja de poder tocar nombre/clasificación/
  proveedor/código SAP/estado, y se quitan por completo el alta manual
  y el borrado. Excel (`POST /admin/import-excel`) pasa a ser la única
  vía para crear, modificar o desactivar un artículo, para que la base
  quede siempre compaginada con el origen real DALI-SAP — el panel de
  administración de artículos queda reducido a "buscar un artículo y
  gestionar su imagen/fichas". De la mano, aviso automático tras cada
  importación: si un artículo con imagen/ficha técnica ya subida
  cambia de descripción o código SAP, se avisa al admin para que
  compruebe si el adjunto sigue correspondiéndose.
- **Carga masiva por proveedor** (`v1.4.0`): tres botones en
  Administración → Artículos para subir imágenes/fichas técnicas/
  fichas de seguridad de golpe, por proveedor — buscador de proveedor
  autorellenable + selector de carpeta (`webkitdirectory`, lee
  subcarpetas). Convención de nombre de archivo:
  `codigoDali_codigoSap_codigoProveedor_nombreDelArticulo.ext` — el
  código DALI del nombre manda sobre cualquier otra cosa a la hora de
  decidir a qué artículo va cada archivo. Reutiliza los endpoints de
  subida ya existentes (uno por archivo), sin backend nuevo para la
  subida en sí, solo el listado de proveedores (`GET
  /admin/proveedores`).
- **Exportación pensada como hoja de pedido** (`v1.4.0`): el PDF/Excel
  que exporta un usuario Hotel ya no muestra la columna "Activo" (no
  tienen esa opción) y en su lugar trae una columna "Cantidad" en
  blanco, con recuadro, para anotar un pedido a mano. El título se
  volvió más inteligente: "Listado de asignaciones de [Proveedor]"
  cuando el resultado es enteramente de un proveedor, o solo el nivel
  más específico del filtro de categoría (no toda la cadena) en caso
  contrario. Por último, Excel se rehizo para compartir exactamente la
  misma estructura que el PDF (mismas columnas, mismo título, mismo
  agrupado) — antes tenían columnas y organización distintas entre sí.

---

## v0.18 — Buscador lento y con resultados incorrectos: sin debounce, cada tecla disparaba su propia petición

- **Síntoma reportado**: la app se notaba muy lenta al escribir
  búsquedas largas ("EMICELA" costaba mucho); y, buscando "MILO", se
  veían "5196 artículo(s)" con nombres que no tenían nada que ver
  ("0030463 JABONERA CROMO", "7-11 RADIANT", "7UP..."), como si no
  filtrara en absoluto — aunque no había ningún error visible en
  pantalla, y "EMICELA" completo sí había funcionado bien poco antes.
- **Diagnóstico, dos problemas relacionados, no uno**:
  1. **Sin debounce**: el `useEffect` que dispara `fetchArticulos` tenía
     `query` como dependencia directa — cada pulsación de tecla contaba
     como un cambio de estado y disparaba una petición nueva. Escribir
     "EMICELA" (7 letras) lanzaba 7 peticiones casi simultáneas, cada
     una con varias consultas reales a Supabase por debajo (la búsqueda
     principal en `articulos`, más la resolución de `proveedor` por
     nombre en una tabla aparte — ver v0.15/v0.17). De ahí la lentitud:
     no era una petición lenta, eran muchas peticiones pesadas a la vez.
  2. **Condición de carrera**: ninguna de esas peticiones se cancelaba
     ni se ignoraba al llegar tarde. Si la petición de un estado
     anterior (p.ej. el campo vacío, antes de escribir "MILO", que
     devuelve TODOS los artículos y por tanto tarda más en transferirse)
     tardaba más que la de "MILO" en resolver, su respuesta llegaba
     DESPUÉS y sobrescribía el estado de React con el resultado
     desactualizado — de ahí ver el listado completo sin relación con
     "MILO", sin ningún error: la petición de "MILO" sí había
     funcionado y devuelto lo correcto, solo que una respuesta más
     tardía y ajena se pintó encima.
- **Por qué no se vio en pruebas anteriores**: los fixes de v1.0.6 a
  v1.0.8 se probaron escribiendo términos cortos o pegando el texto de
  una vez (p.ej. "2276"), lo que dispara pocas peticiones y raramente
  deja tiempo a que se solapen respuestas fuera de orden. El problema
  aparece de forma consistente al escribir con normalidad, tecla a
  tecla, términos largos.
- **Corrección**:
  - Se creó `hooks/useDebouncedValue.js`, un hook compartido que
    retrasa 350ms la actualización del valor que dispara la búsqueda,
    sin afectar a lo que se ve en el campo de texto mientras se escribe
    (eso sigue siendo instantáneo, solo se retrasa cuándo se lanza la
    petición).
  - En `App.jsx` y `AdminArticulos.jsx`, el `useEffect` de búsqueda pasa
    a depender del valor debounced, no del valor tecla a tecla, y añade
    una guarda de cancelación: cada vez que el efecto se vuelve a
    ejecutar (o el componente se desmonta), marca como "cancelada" la
    ejecución anterior, y su `.then()`/`.catch()` comprueban esa marca
    antes de tocar el estado — así, aunque una petición vieja llegue
    tarde, su resultado se descarta en vez de sobrescribir el bueno.
  - En `AdminArticulos.jsx` se separó la lógica de carga en
    `realizarCarga(qUsado, { signalCancelado })`, reutilizada tanto por
    el `useEffect` de búsqueda (con guarda) como por `cargar()` (la
    recarga puntual tras guardar/borrar una ficha, sin debounce ni
    guarda — no hace falta, no se dispara en ráfaga).
- **Patrón para el futuro**: cualquier búsqueda o filtro que dispare una
  petición de red en cada cambio de un campo de texto debe llevar
  debounce y una guarda de cancelación por defecto, no añadirse después
  de que aparezca el problema — es la combinación exacta que causó este
  fallo.

## v0.17 — El casteo de codigo_dali no funcionaba de ningún modo: solución de raíz con una columna generada

- **Síntoma reportado**: con el fix de v0.16 ya desplegado, buscar
  "2276" (el código DALI de un artículo real, DALI-2276) daba 0
  resultados — y esta vez, gracias al manejo de errores añadido en
  v0.16, se veía el motivo en pantalla: `operator does not exist:
  integer ~~* unknown`.
- **Qué confirma este error**: que el casteo `codigo_dali::text` que se
  intentó en v0.16 (dentro de un `.or()` compuesto) NO se estaba
  aplicando de verdad — Postgres estaba recibiendo un `ilike` aplicado
  directamente sobre la columna `codigo_dali`, que es `integer`, y ese
  operador no existe para ese tipo sin castear antes.
- **Segundo intento, también fallido**: mover el casteo a un `.filter()`
  SIMPLE (no dentro de un `or` compuesto), confiando en que ahí sí es
  sintaxis bien documentada por PostgREST. Mismo error. Dos enfoques
  distintos de "castear en el momento de la consulta" han fallado igual
  contra este proyecto de Supabase — puede que el motivo exacto esté en
  cómo maneja supabase-js el `::` al construir la URL de la petición
  desde este cliente en concreto, pero en la práctica lo importante es
  que castear en cada consulta no es fiable aquí.
- **Decisión: solución de raíz, a nivel de base de datos, no un tercer
  intento de casteo en la consulta**. Se añade `codigo_dali_texto`: una
  columna de texto GENERADA (`generated always as (codigo_dali::text)
  stored`) — Postgres la calcula y mantiene sola en cada INSERT/UPDATE
  de `codigo_dali`, no hace falta escribirla nunca a mano ni rellenarla
  con un UPDATE masivo tras crearla. Al ser ya una columna `text`
  normal en la tabla, `ilike` se le aplica exactamente igual que a
  nombre_articulo o codigo_sap — sin casteo, sin trucos de sintaxis,
  sin depender de cómo el cliente construya la petición.
- **Se añade también un índice trigram** sobre la nueva columna
  (`ix_articulos_codigo_dali_texto_trgm`), mismo patrón que ya existía
  para nombre_articulo — la extensión `pg_trgm` ya estaba habilitada en
  este proyecto por ese motivo, así que no hace falta activarla de
  nuevo.
- **Requiere una acción manual que no se puede hacer desde aquí**: no
  hay framework de migraciones en este proyecto (schema.sql es el
  documento de referencia, se aplica a mano). Se creó
  `database/migraciones/2026-08-03_codigo_dali_texto.sql` con el `alter
  table` y el índice, para ejecutarlo en el SQL Editor de Supabase.
  **Sin ejecutar esa migración, la v1.0.8 del backend no funcionará en
  absoluto** — fallará con "column codigo_dali_texto does not exist" en
  cualquier búsqueda con texto. También se actualizó `schema.sql` para
  que una instalación nueva desde cero ya incluya esta columna sin
  necesitar la migración aparte.
- **Simplificación resultante en `articulosController.js`**: al no
  necesitar ya resolver codigo_dali con una consulta aparte (como en
  v0.16), el código de búsqueda queda más simple — solo `proveedor`
  sigue necesitando su propia consulta previa, porque de verdad vive en
  otra tabla, no por ningún problema de tipos.
- **Patrón para el futuro**: cuando un casteo dentro de un filtro de
  Supabase/PostgREST no se comporta como dice la documentación, no
  merece la pena insistir con variantes de sintaxis del mismo truco —
  mejor materializar el dato en el tipo correcto a nivel de columna
  (generada si es derivable de otra, como aquí) y evitar el casteo por
  completo.

## v0.16 — v0.15 rompía la búsqueda por completo: con naturaleza activa, no filtraba nada

- **Síntoma reportado**: con ALIMENTACION seleccionada en el sidebar,
  escribir "HAMBURG" en el buscador seguía mostrando los 2319 artículos
  de esa naturaleza sin filtrar — ni por nombre, ni por proveedor, ni
  por ningún código.
- **Diagnóstico real, dos capas**:
  1. **La búsqueda en sí fallaba**: v0.15 metía el casteo
     `codigo_dali::text.ilike...` DENTRO de la sintaxis compuesta de un
     `.or()` junto con nombre_articulo, codigo_sap e
     `id_proveedor.in.(...)`. El casteo de columna es sintaxis
     documentada de PostgREST, pero solo con certeza para un filtro
     SIMPLE (`columna::tipo=operador.valor` como parámetro suelto) —
     dentro de la sintaxis compuesta de `or=(...)` no hay la misma
     garantía, y en producción la petición fallaba.
  2. **El fallo quedaba invisible**: `fetchArticulos` en `App.jsx` y
     `AdminArticulos.jsx` no capturaba ese error (`.then().finally()`
     sin `.catch()`). Al fallar la petición, el estado de React se
     quedaba con el resultado de la carga anterior — el listado
     completo de ALIMENTACION de antes de escribir nada — sin ningún
     aviso en pantalla. De ahí la sensación de "no encuentra nada":
     en realidad no se había aplicado ningún filtro nuevo en absoluto,
     ni el que ya funcionaba antes (nombre_articulo) ni los nuevos.
- **Por qué antes (v0.13/v0.14, el bug del contador) esto no se vio**:
  aquellos fixes no tocaban el `.or()` de búsqueda, así que nunca
  llegaron a ejercitar esta ruta de código nueva ni su manejo de
  errores — el contador podía estar mal sin que la petición fallara.
- **Corrección**:
  - Backend (`articulosController.js`): se elimina el casteo dentro del
    `.or()` compuesto. Ahora se resuelven antes, en dos consultas
    SIMPLES independientes (no compuestas), los `id` de artículo que
    coinciden por código DALI y los `id` de proveedor que coinciden por
    nombre. El `.or()` final de la consulta principal a `articulos`
    solo combina piezas de bajo riesgo: dos `ilike` sobre columnas de
    texto propias de la tabla (sin casteo, sin JOIN) y, si hubo
    coincidencias en las consultas previas, `id.in.(...)` /
    `id_proveedor.in.(...)` — comparaciones simples sobre columnas de
    `articulos`, sin casteo ni tabla relacionada de por medio.
  - Frontend: se captura el error en `App.jsx` y `AdminArticulos.jsx`
    (antes sin manejar) y se muestra un aviso visible en vez de dejar
    resultados obsoletos en pantalla sin explicación. `fetchArticulos`
    (`services/api.js`) propaga además el mensaje de error real del
    backend en vez de un texto genérico fijo, para poder diagnosticar
    el próximo fallo sin tener que adivinarlo desde una captura de
    pantalla.
- **Lección para el patrón general**: cuando una función que carga datos
  no captura sus propios errores, un fallo de backend se disfraza de
  "no hay resultados" en vez de mostrarse como lo que es — un fallo de
  la petición. A partir de ahora, cualquier nuevo `fetchX().then(...)` en
  este proyecto debe llevar su `.catch()`, no solo su `.finally()`.

## v0.15 — Multi-búsqueda: artículo, código DALI, código SAP y proveedor en un mismo cuadro

- **Petición**: los dos buscadores de la app (Catálogo y Administración ·
  Artículos) solo buscaban por nombre de artículo. Se pidió que
  buscaran también por código DALI, código SAP y proveedor, todo desde
  el mismo cuadro de texto — sin tener que elegir en qué campo buscar.
- **Por qué un único cambio en backend cubre las dos pantallas**: ambos
  buscadores (`App.jsx` y `AdminArticulos.jsx`) llaman a la misma
  función `fetchArticulos`, que llama al mismo endpoint
  `GET /articulos?q=...`. Arreglando `listarArticulos` una vez, las dos
  pantallas quedan cubiertas — no hace falta duplicar lógica de
  búsqueda en el frontend.
- **Dos obstáculos técnicos, no solo "añadir más campos al OR"**:
  1. `codigo_dali` es de tipo `integer` en el esquema (`schema.sql`), y
     `ilike` exige texto — Postgres no hace ese cast implícito. Se
     resuelve casteando dentro del propio filtro con
     `codigo_dali::text.ilike...`, sintaxis de casteo de columna que
     soporta PostgREST directamente en el filtro, sin añadir una
     columna calculada a la tabla ni tocar el esquema.
  2. `proveedor` no es una columna de `articulos`, es el nombre de una
     fila en la tabla `proveedores`, relacionada por `id_proveedor`. No
     se puede meter sin más en el `.or()` de la consulta a `articulos`.
     Se resuelve en dos pasos, reutilizando el mismo patrón que ya
     existía para `naturaleza` (resolver nombre -> id antes de
     filtrar, unas líneas arriba en el mismo controlador): primero se
     consulta `proveedores` por nombre parcial, se recogen los `id`
     que coinciden, y se añaden como una condición más dentro del OR
     (`id_proveedor.in.(id1,id2,...)`). Si el texto buscado no coincide
     con ningún proveedor, esa rama simplemente no se añade — las otras
     tres (artículo/código DALI/código SAP) siguen funcionando igual.
- **Detalle de robustez**: la coma y los paréntesis tienen significado
  especial en la sintaxis de filtros de PostgREST (`.or()`) — si el
  texto buscado los llevara literalmente, romperían el filtro entero.
  Se añadió `limpiarParaFiltroOr()` para quitarlos antes de interpolar
  el texto de búsqueda en la condición.
- Actualizado también el modo demo (`services/api.js`, sin backend real)
  con el mismo criterio, para que el comportamiento sea el mismo
  probando en local sin Supabase.
- **Sin verificar contra Supabase real** (igual que en entregas
  anteriores, este entorno no tiene red hacia el proyecto de Supabase):
  el casteo `::text` dentro de un filtro y la combinación de
  `columna.in.(...)` junto a otras condiciones dentro de un mismo
  `.or()` son sintaxis documentada de PostgREST, pero conviene probarlo
  en cuanto esté desplegado — especialmente buscar por código DALI
  parcial (p.ej. solo los primeros dígitos) y por proveedor a la vez que
  hay un filtro de naturaleza activo, para confirmar que el AND entre el
  filtro de naturaleza y el OR de la búsqueda se aplica como se espera.

## v0.14 — Mismo bug del contador que v0.13, ahora en Administración · Artículos (30109 fichas, activas e inactivas)

- **Síntoma reportado**: en "Administración · Artículos" (que carga
  `todos: true`, activos e inactivos) el contador "N ficha(s)" también se
  quedaba clavado en el tope de `pageSize` en vez de mostrar el total
  real — en el momento de reportarlo, 30109.
- **Diagnóstico**: exactamente el mismo bug que v0.13 (`App.jsx`), solo
  que en el otro componente que consume `fetchArticulos`:
  `AdminArticulos.jsx` pintaba el contador con `articulos.length` (el
  lote cargado) en vez de con el `total` que ya devuelve la función desde
  v0.13. Como aquí se listan todos los estados (no solo activos), el
  total es aún mayor y la diferencia con el lote cargado más evidente.
- **Nota del propio Victor Martin, importante para no "arreglarlo" con un
  número fijo**: este total puede variar en cualquier momento — al
  cargar un nuevo Excel o al dar de alta/baja una ficha a mano — así que
  la solución tiene que leer siempre el total real del backend en cada
  carga, nunca un valor guardado o calculado una vez.
- **Corrección**: `AdminArticulos.jsx` guarda el `total` que ya devuelve
  `fetchArticulos` (desde v0.13) en estado, junto a `articulos`, y lo usa
  para el contador en vez de `articulos.length`. Sin cambios en backend
  ni en `services/api.js`: el `total` ya era correcto ahí, solo faltaba
  usarlo en este segundo consumidor.
- **Pauta reforzada**: al arreglar un consumidor de una función que
  cambia de forma de retorno (aquí, `fetchArticulos` pasó de devolver un
  array a devolver `{ data, total }` en v0.13), revisar TODOS los
  puntos de llamada, no solo el que motivó el cambio — este mismo bug ya
  se evitó de churro en `AdminArticulos.jsx` al adaptar el `.then()` para
  que no rompiera, pero se pasó por alto que también tenía su propio
  contador con el mismo problema de fondo.

## v0.13 — El total general "N artículo(s)" se quedaba en 3000 aunque el conteo por naturaleza ya estaba bien (v0.12)

- **Síntoma reportado**: en "Todas las naturalezas" el contador de la
  cabecera mostraba "3000 artículo(s)", aunque en la práctica hay ~6700
  activos. El conteo al filtrar por una naturaleza concreta (el fix de
  v0.11/v0.12) sí era correcto.
- **Diagnóstico**: el número 3000 coincidía exactamente con el
  `pageSize` por defecto — misma pauta que en v0.12 (número exacto y
  redondo = firma de un límite técnico, no un cálculo de negocio). Pero
  esta vez el límite NO estaba en el backend: `listarArticulos` ya
  devuelve `pagination.total` con un `count: "exact"` de Supabase, que
  no está limitado por el `.range()`/pageSize (por eso el conteo por
  naturaleza individual, siempre por debajo de 3000, salía bien). El
  fallo estaba en el frontend: `services/api.js` (`fetchArticulos`)
  descartaba ese `pagination` y devolvía solo `data`; `App.jsx` pintaba
  el contador con `visibles.length` — el tamaño del lote realmente
  cargado (tope `pageSize=3000`), no el total real.
- **Por qué "ya estaba solucionado" en naturalezas y no en el total**:
  v0.12 arregló que cada naturaleza individual devolviera todas sus
  filas sin truncar en el tope de Supabase de 1000/petición. Pero
  mientras el total de una naturaleza se mantuviera por debajo del
  `pageSize=3000` de la app, `visibles.length` (el bug real) coincidía
  con el total por pura casualidad de rango. Solo se hace visible el
  fallo cuando el total sin filtrar (~6700) supera ese `pageSize`.
- **Corrección**: `fetchArticulos` devuelve ahora `{ data, total }`
  (con `total = pagination.total`, o `data.length` en modo demo, donde
  no hay paginación). `App.jsx` guarda `total` en estado y lo usa para
  el contador en vez de `visibles.length`. Se adaptó también
  `AdminArticulos.jsx`, el otro consumidor de `fetchArticulos`, al nuevo
  formato de retorno — si no, habría roto ahí al recibir `{data, total}`
  donde esperaba un array.
- **Fuera de alcance, ya documentado**: la tabla en sí sigue mostrando
  como máximo `pageSize=3000` filas en "Todas las naturalezas" — el
  contador ya es correcto, pero listar más de 3000 filas de golpe sigue
  necesitando paginación real en la UI, no solo en el contador.

## v0.12 — El tope de 1000 filas de Supabase seguía cortando ALIMENTACION/EQUIPAMIENTO después de v0.11

- **Síntoma reportado**: tras el fix de v0.11 (filtro por naturaleza),
  ALIMENTACION y EQUIPAMIENTO — las dos naturalezas con más de 1000
  artículos activos — mostraban exactamente 1000, ni uno más. El resto
  de naturalezas (todas por debajo de 1000 activos) salían correctas.
- **Diagnóstico**: "exactamente 1000, ni uno más" no encaja con un
  filtro mal resuelto (eso daría un número arbitrario, no un tope
  redondo) — encaja con un límite duro de paginación. v0.11 subió el
  `pageSize` por defecto de 50 a 3000 asumiendo que un `.range()` más
  generoso bastaría, pero pasó por alto que **Supabase impone su propio
  tope de filas por petición a nivel de proyecto** (Project Settings →
  API → Max Rows, 1000 salvo que se cambie ahí en el panel de Supabase),
  que corta el `.range()` en 1000 con independencia de lo que pida la
  aplicación. El `pageSize=3000` de v0.11 nunca llegaba a aplicarse:
  Supabase ya había recortado antes de que el valor importara.
- **Por qué no se detectó en v0.11**: BEBIDAS (413 activos, el caso
  probado entonces) está por debajo de 1000, así que el fix de v0.11
  (resolver y aplicar el filtro de naturaleza en el servidor) ya daba el
  número correcto para ese caso concreto — el tope de Supabase solo se
  manifiesta en naturalezas con más de 1000 activos, que no se
  comprobaron en esa entrega.
- **Corrección**: en vez de depender de subir el ajuste "Max Rows" en el
  panel de Supabase (un cambio de configuración fuera del repo, no
  garantizado en todos los entornos/planes), `listarArticulos` trocea la
  petición en tandas de máximo 1000 filas
  (`SUPABASE_MAX_ROWS_POR_PETICION`) y las concatena hasta completar el
  `pageSize` solicitado o hasta que una tanda vuelva con menos filas de
  las pedidas (señal de que no quedan más). El conteo total
  (`count: "exact"`) se pide solo en la primera tanda — es el mismo en
  todas porque el filtro no cambia entre tandas, solo el rango.
- Nueva función interna `construirQuery()` que reconstruye la consulta
  con los mismos filtros en cada vuelta del bucle — necesario porque el
  query builder de supabase-js no se puede reutilizar tras ejecutar un
  `.range()`.
- Verificado con un simulador en Node del tope de 1000 filas (mismo
  motivo que en entradas anteriores: sin red en este entorno para
  probarlo de verdad contra Supabase) — recupera 2320 de 2320 filas
  simuladas, sin huecos ni duplicados, para un caso equivalente a
  ALIMENTACION.
- **Fuera de alcance, ya documentado**: "Todas las naturalezas" sin
  filtro sigue sin cubrirse completa (~6700 activos, por encima del
  `pageSize=3000`); necesita paginación real en la UI, no otro ajuste
  de tamaños.

### Pauta para próximos cambios de este tipo

Un número que sale **exacto y redondo** (1000, 500, 100...) casi nunca
es un cálculo real de negocio — es la firma de un límite técnico
(paginación, tope de filas de la API/BD, límite de un componente de UI).
Antes de sospechar de la lógica de filtrado o de los datos, comprobar:

1. ¿El número coincide con un límite conocido de la plataforma
   (Supabase Max Rows, tamaño de página por defecto de una librería,
   límite de un `LIMIT` o `TOP` en SQL)? Si sí, ese es el sospechoso
   principal, no el filtro.
2. Si hay que superar ese límite, **no asumas que basta con subir un
   parámetro propio** (`pageSize`, `limit`...) — comprueba si hay un
   tope impuesto por debajo (aquí, por la plataforma Supabase) que corte
   antes de que ese parámetro llegue a aplicarse. En ese caso, hace
   falta trocear en varias peticiones más pequeñas que ese tope, no una
   petición más grande.
3. Prueba siempre con el caso más grande conocido, no solo con el que
   reportó el fallo — aquí, probar BEBIDAS (413) no habría revelado el
   problema; solo se ve con ALIMENTACION o EQUIPAMIENTO (>1000).

## v0.11 — El filtro por naturaleza del sidebar se quedaba corto (5 de 413 en BEBIDAS)

- **Síntoma reportado**: al filtrar por "BEBIDAS" en el sidebar, la app
  mostraba solo 5 artículos, con el Excel de origen (`ARTICULOS_DALI.xlsx`
  filtrado por NATURALEZA=BEBIDAS, ACTIVO=SI) confirmando 413.
- **Diagnóstico, en dos capas** (siguiendo la pauta dejada en v0.10:
  primero comprobar si el dato existe, luego si la forma de la petición/
  respuesta encaja):
  1. El dato existe: `database/articulos.csv` cruzado con
     `naturalezas.csv` confirma 413 artículos con `id_naturaleza` =
     BEBIDAS y `activo_dali = true`.
  2. La petición nunca llegaba completa al backend: `App.jsx` sí llama a
     `fetchArticulos({ naturaleza: naturalezaActiva, ... })`, pero
     `services/api.js` solo usaba `naturaleza` para filtrar el array de
     modo demo — contra el backend real (`API_URL` configurada) no lo
     añadía a los `URLSearchParams`. Y aunque lo hubiera añadido,
     `listarArticulos` (`articulosController.js`) no tenía `naturaleza`
     entre los filtros aceptados (solo `familia`/`subfamilia`/
     `proveedor`, por id).
  - Los "5 artículos" concretos (todos "7UP...") no eran aleatorios:
     salían de que, sin filtro real, el backend devolvía su página 1
     (50 filas, orden alfabético por `nombre_articulo`) y el filtro de
     `App.jsx` (`visibles = articulos.filter(a => a.naturaleza ===
     naturalezaActiva)`, pensado como filtro auxiliar, no como el único)
     se aplicaba solo sobre esas 50 — los únicos 5 que, alfabéticamente,
     empiezan por algo anterior a "7UP" y son BEBIDAS.
- **Corrección**:
  - `services/api.js`: `fetchArticulos` añade `naturaleza` a los
    `URLSearchParams` cuando hay backend real (antes solo existía la
    rama de modo demo).
  - `articulosController.js`: `listarArticulos` acepta `naturaleza`
    (nombre exacto), la resuelve contra `naturalezas.nombre_naturaleza`
    y filtra `articulos.id_naturaleza` en el servidor — no en el
    navegador. Si el nombre no existe, responde lista vacía en vez de
    ignorar el filtro en silencio.
  - `pageSize` por defecto sube de 50 a 3000: parche mínimo para que
    una naturaleza numerosa (ALIMENTACION, ~2320 activos) no vuelva a
    quedarse corta por el límite de página, no una paginación real.
- **Fuera de alcance deliberado, ya documentado como pendiente antes de
  esta entrada**: "Todas las naturalezas" (sin filtro) sigue limitado
  por no tener paginación real en la UI — con ~6700 artículos activos
  en total, ni el `pageSize` de 3000 lo cubre entero. Subir el
  `pageSize` otra vez no es la solución correcta para ese caso; lo es
  la paginación pendiente ya anotada en `CHANGELOG.md`/`HISTORIAL.md`
  desde antes de este cambio.
- Verificado con `node --check` sobre ambos ficheros modificados (mismo
  motivo que en entradas anteriores: sin red en este entorno para
  correrlo de verdad contra Supabase).

### Pauta para próximos cambios de este tipo

Cuando un filtro "se queda corto" (menos resultados de los que debería,
pero no cero), comprobar en este orden antes de tocar código:

1. **¿El parámetro llega realmente hasta el backend?** — mirar la
   petición de red (o, como aquí, leer `services/api.js` línea a línea)
   antes de asumir que el problema está en el `select` de Supabase o en
   la resolución de dimensiones. Un dato que "se pierde" con un
   subconjunto pequeño y no reproducible a simple vista suele ser un
   parámetro que se cae por el camino, no un filtro mal escrito.
2. **¿Ese filtro está soportado en el backend?** — `grep` de los
   `req.query` destructurados en el controlador correspondiente. Añadir
   un filtro nuevo (como `naturaleza` aquí) sigue el mismo patrón que
   `familia`/`subfamilia`/`proveedor`: resolver nombre → id si el
   frontend manda texto libre, filtrar por id contra la tabla.
3. **Si el número que sale es pequeño y "con forma" (unos pocos,
   agrupados por algún criterio como orden alfabético)**, sospechar de
   un filtrado que se está aplicando tarde, en el cliente, sobre un
   subconjunto ya recortado por paginación — no de que falten filas en
   la base de datos.

## v0.10 — PROVEEDOR/CÓDIGO SAP no se veían en el panel (aunque estaban bien resueltos en BD)

- **Síntoma reportado**: en `Administración · Artículos` las columnas
  PROVEEDOR y CÓDIGO SAP salían siempre en "—", y la miga de pan
  NATURALEZA · FAMILIA · SUBFAMILIA salía vacía, incluso en artículos
  para los que el usuario había comprobado a mano que el dato SÍ está
  en los Excel de origen.
- **Diagnóstico**: no era un problema de datos ni de la importación.
  `SELECT_COMPLETO` en `articulosController.js` pide las dimensiones
  como relaciones anidadas de Supabase — `proveedores ( id,
  nombre_proveedor )`, igual para `naturalezas`/`familias`/
  `subfamilias` — así que la API devolvía `articulo.proveedores.
  nombre_proveedor` (objeto, en plural). Pero **todo** el frontend
  (`ArticuloTable.jsx`, `ArticuloDetail.jsx`, `ArticuloForm.jsx`,
  `AdminArticulos.jsx`) está escrito leyendo el nombre ya aplanado y en
  singular: `articulo.proveedor`, `articulo.naturaleza`. Esa clave no
  existía nunca en la respuesta → `undefined` → "—" en la UI, con
  independencia de si el artículo tenía o no proveedor asignado.
  Verificado cruzando `database/articulos.csv` con `proveedores.csv`:
  el artículo de ejemplo del reporte (DALI-15563) sí tiene
  `id_proveedor` resuelto a un nombre real. El dato estaba bien; solo
  el mapeo de la respuesta estaba roto.
- **CÓDIGO SAP vacío en ese mismo artículo era, aparte, un caso
  legítimo** (no bug): ese `codigo_dali` no tiene código SAP asignado
  todavía en `LISTADO_CODIGOS_DALI_-_SAP.xlsx` (está entre los ~540
  "MATERIALES PENDIENTES DE CREAR EN SAP" que el propio Excel de origen
  contabiliza aparte). Al ser un campo plano en `SELECT_COMPLETO` (no
  anidado), no compartía la causa del fallo de PROVEEDOR/NATURALEZA/
  FAMILIA/SUBFAMILIA.
- **Corrección**: un único punto de cambio, en el backend
  (`articulosController.js`), en vez de tocar los cuatro componentes
  del frontend. Nueva función `aplanarArticulo(row)` que convierte la
  fila anidada de Supabase al formato plano que el frontend ya
  consume, aplicada en `listarArticulos` (`GET /articulos`) y
  `obtenerArticulo` (`GET /articulos/:id`). Se conservan también los
  `id_naturaleza`/`id_familia`/`id_subfamilia`/`id_proveedor` por si
  algún consumo futuro los necesita.
- **Fuera de alcance deliberado**: `crearArticulo`/`actualizarArticulo`
  (`POST`/`PUT /admin/articulos`) devuelven la fila con `.select()`
  plano de la tabla `articulos` (sin joins), así que su respuesta
  tampoco trae `proveedor`/`naturaleza` como nombre — pero
  `AdminArticulos.jsx` no pinta esa respuesta directamente: tras guardar
  siempre vuelve a llamar a `cargar()` (`GET /articulos`), que ya sale
  aplanado. No se ha tocado por no ser necesario para el fallo
  reportado; si en el futuro se necesita el nombre en la respuesta
  directa del alta/edición, aplicar ahí `aplanarArticulo()` también.
- Verificado con `node --check` sobre `articulosController.js` (mismo
  motivo que en entradas anteriores: sin red en este entorno para
  correrlo de verdad contra Supabase).

### Pauta para próximos cambios de este tipo

Antes de dar por buena una lectura ("no me sale tal campo"), separar
dos preguntas distintas y comprobarlas por separado:

1. **¿El dato existe en la base de datos?** — cruzar el CSV/tabla de
   origen (`database/*.csv` o una consulta directa) contra el registro
   concreto que falla. Si el dato SÍ está ahí, el fallo es de
   transporte/mapeo (API ↔ frontend), no de importación ni de
   resolución de dimensiones.
2. **¿La forma de la respuesta de la API coincide con lo que el
   frontend espera leer?** — en este proyecto, cualquier `select` de
   Supabase con relaciones anidadas (`tabla_hija ( columnas )`) devuelve
   un objeto anidado en plural con el nombre de la tabla, no el campo
   plano en singular que usan los componentes. Antes de añadir o tocar
   un `select` con joins, revisar cómo lo consume el componente
   correspondiente (`grep` del nombre de campo en `frontend/src`) para
   no repetir este mismo desajuste en otro endpoint.

Si aparece el mismo síntoma en otro listado futuro (fichas, export,
etc.), empezar por el punto 2 antes de sospechar de la importación o
de Supabase.

## v0.9 — La misma resolución de dimensiones, en el alta/edición manual

- Continuación directa de v0.8: `POST/PUT /admin/articulos`
  (`crearArticulo`/`actualizarArticulo`) insertaba `req.body` tal cual,
  sin traducir naturaleza/familia/subfamilia/proveedor (texto libre,
  como los manda `ArticuloForm.jsx`) a sus `id_*`. Era el mismo fallo
  que se acababa de corregir en la importación de Excel, solo que
  disparado por la acción más cotidiana del panel de administración —
  dar de alta una ficha a mano — no por una carga masiva puntual.
- `articulosController.js` gana `construirPayloadArticulo(body)`, que
  reutiliza `resolverDimensionSimple`/`resolverDimensionConFk` de
  `src/utils/dimensiones.js` (el mismo módulo de v0.8, sin cambios) para
  resolver los cuatro nombres antes de guardar. No hizo falta escribir
  lógica nueva de resolución, solo enchufar la que ya existía en un
  segundo punto de entrada.
- Al escribir esto salió a la luz un gap distinto, no corregido aquí
  porque no es del mismo tipo: `articulos.codigo_dali` es
  `not null unique` en `schema.sql`, pero `ArticuloForm.jsx` nunca lo
  pide — un alta manual real hoy fallaría por violación de NOT NULL.
  Se deja fuera de esta entrada a propósito: a diferencia de una FK a
  `null`, esto no se cuela en silencio — el admin ve el error al
  guardar y sabe que algo falta. Queda anotado en "Pendientes
  acumulados" para decidir aparte (¿lo genera el servidor? ¿lo pide el
  formulario?).
- Verificado con `node --check` y bundle de `esbuild` (mismo motivo que
  en v0.5/v0.8: sin red en este entorno para correrlo de verdad contra
  Supabase).

## v0.8 — Resolver dimensiones nuevas en la importación de Excel

- Hasta ahora `POST /admin/import-excel` dejaba `id_naturaleza`,
  `id_familia`, `id_subfamilia` e `id_proveedor` sin resolver — el
  comentario en el propio `importController.js` lo marcaba como
  pendiente ("usar la misma lógica de get_or_create de build_csvs.py").
  Con 30.000 artículos y altas de proveedor frecuentes, tarde o
  temprano un Excel iba a traer un nombre nuevo y o bien fallaba la
  importación entera, o la fila se guardaba con la FK a null sin que
  nadie se enterase hasta buscar el artículo y no encontrarlo (o
  encontrarlo sin familia). A diferencia de "falta paginación", este
  era un fallo silencioso esperando a pasar, no una carencia visible.
- `backend/src/utils/dimensiones.js` (nuevo): `resolverDimensionSimple`
  (naturalezas, proveedores — sin FK adicional) y
  `resolverDimensionConFk` (familias depende de naturaleza, subfamilias
  de familia — la unicidad real es `(fk, nombre)`, no solo `nombre`,
  igual que en `build_csvs.py`). Ambas: seleccionan lo que ya existe,
  y para lo que falta hacen `upsert` (no `insert`) con `onConflict` —
  así, si dos importaciones concurrentes dan de alta el mismo nombre
  nuevo a la vez, la segunda recibe el id ya creado por la primera en
  vez de romper por violación de unicidad.
- `importController.js`: antes del upsert de `articulos`, resuelve
  NATURALEZA → PROVEEDOR → FAMILIA (depende de la naturaleza ya
  resuelta) → SUBFAMILIA (depende de la familia ya resuelta), en ese
  orden, y usa los ids resultantes en cada fila. La respuesta ahora
  incluye `dimensiones_creadas` (cuántas naturalezas/familias/
  subfamilias/proveedores nuevos se han dado de alta en esa
  importación) y `avisos` si, pese a todo, alguna fila no logra
  resolver su familia o subfamilia — para que quede constancia en vez
  de guardarse en silencio.
- Sintaxis verificada con `node --check` y bundle de `esbuild`
  resolviendo los imports internos (mismo motivo que en v0.5: sin
  acceso de red en este entorno para instalar dependencias y correr el
  backend real contra Supabase).
- Pendiente explícito, no resuelto aquí: el formulario de alta/edición
  manual del frontend (`ArticuloForm.jsx`) sigue sugiriendo
  familia/subfamilia/proveedor por datalist sin pasar por esta misma
  resolución — un alta manual con un nombre nuevo escrito a mano no
  pasa por `get_or_create`, solo la importación de Excel.

## v0.7 — Login real, tomando como referencia el proyecto de Princess

- Se sustituye el toggle demo Usuario/Admin (pendiente marcado desde
  v0.5) por autenticación real, siguiendo el patrón del proyecto
  `control-pedidos-princess` que aportó el usuario como referencia:
  - **Sesión por cookie firmada** (`cookie-session`, sin store de
    servidor), no JWT en cabecera — mismo principio que la sesión de
    Flask en Princess (cookie firmada con `secret_key`, sin
    Flask-Session).
  - **Caducidad diaria de sesión** (huso Canarias): si
    `session.loginDate` no es la fecha de hoy, se invalida — calcado
    del `login_required`/`admin_required` de Princess.
  - `admin_required` → nuestro `requireAdmin`, ya existía y no ha
    hecho falta tocarlo; solo cambia de dónde lee el usuario
    (`req.session` en vez de un JWT verificado).
- **Desviación deliberada del proyecto de referencia**: en Princess la
  contraseña se guarda y compara en texto plano
  (`WHERE username=%s AND password=%s`). Aquí se hashea con
  **bcrypt** (`usuarios.hash_password`) y se compara con
  `bcrypt.compare`. No se ha replicado la parte insegura del patrón.
- Se añade `backend/scripts/create-user.js` (`npm run create-user`)
  para dar de alta usuarios desde CLI — no hay autorregistro, igual
  que en Princess no lo hay para el alta directa de admin (allí existe
  además una "solicitud de acceso en 2 fases" que aquí no se replica
  por ahora).
- `schema.sql`: `usuarios.hash_password` pasa a `not null`, se añade
  `usuarios.activo` (baja de acceso sin borrar el usuario, igual que
  el `activo=1` que consulta el login de Princess).
- Frontend: nueva pantalla `LoginScreen.jsx` con la misma identidad
  marfil/latón/Fraunces; `App.jsx` comprueba la sesión al cargar
  (`GET /auth/me`) en vez de arrancar siempre en modo Usuario.
  `services/api.js`: todas las llamadas pasan a `credentials:
  "include"` en vez de recibir un `token` por parámetro.
- **Deliberadamente fuera de esta entrega** (presentes en Princess,
  aquí solo documentadas como pendientes): código de verificación por
  email tras varios días sin login, y recuperación de contraseña por
  email — ambas dependen de un proveedor de email que este proyecto
  no tiene configurado (Princess lo resuelve enviando desde el
  frontend vía EmailJS).
- `DEPLOY.md`: nuevo paso 6 ("Primer usuario"), checklist de
  verificación ampliada con comprobaciones de sesión/rol.
  `render.yaml`: `JWT_SECRET` → `SESSION_SECRET` + `NODE_ENV=production`
  (necesario para que la cookie se marque `secure`).

---

## v0.6 — Guía de despliegue

- Se escribe `DEPLOY.md`, que faltaba desde v0.4: `render.yaml` ya
  apuntaba a él pero el documento no existía.
- Orden de despliegue documentado paso a paso: Supabase (schema +
  import de los 5 CSV en orden) → GitHub → Render vía Blueprint
  (`dali-backend` primero, para tener su URL) → `dali-frontend`
  (rellenando `VITE_API_URL` con esa URL) → cerrar el círculo
  rellenando `CORS_ORIGIN` del backend con la URL del frontend ya
  desplegado.
- Se documenta explícitamente el motivo del orden: si se despliega el
  frontend primero, de todas formas hay que volver a `dali-backend` a
  rellenar `CORS_ORIGIN`, así que hacerlo en este orden evita ida y
  vuelta.
- Checklist de verificación final (health check, "Conectado a la API"
  en vez de "Modo demo", visibilidad de no-activos en modo Admin, 401
  en `/admin/*` sin token).
- Nota de aviso: el toggle Usuario/Admin del frontend es solo
  demostrativo de la UI, no control de acceso real — no debe
  confundirse con seguridad hasta que exista login real (pendiente
  desde v0.5).

---

## v0.5 — Panel de administración coherente con la identidad visual

- Se construye lo que faltaba del frontend: el panel de administración
  (hasta ahora el frontend era solo de consulta). Se descarta
  deliberadamente el patrón de "admin genérico" (tabla CRUD + modal
  Bootstrap + dropzone de subida estándar) y se extiende la misma
  metáfora de ledger de hotel usada en el catálogo:
  - **Sidebar:** la sección "Administración" aparece bajo una costura
    punteada, como un cajón aparte del archivador — solo visible en modo
    Admin.
  - **Artículos (CRUD):** el formulario de alta/edición reutiliza el
    mismo panel deslizante que la ficha de detalle de consulta (misma
    "ficha", no un formulario aparte). El código de artículo se muestra
    como la etiqueta de latón habitual, o como "Código pendiente de
    asignar" en alta nueva. La baja pide confirmación en un diálogo con
    filo vino — la tinta roja del libro de contabilidad marcando una
    baja, ya usada para el badge "No activo".
  - **Importar Excel:** en vez de una barra de progreso de subida
    genérica, una bandeja de entrada (dropzone) para los dos Excel de
    origen y, al terminar, un recibo con las cifras del proceso rematado
    por un sello de latón "Procesado" en diagonal.
- Se detecta y corrige un resto de la paleta de color antigua que había
  quedado sin actualizar en el rediseño de v0.3: el hover de las pestañas
  del sidebar seguía usando el verde-azulado `rgba(44, 95, 91)` en vez
  del latón de la paleta actual.
- `services/api.js` incorpora las funciones de CRUD
  (`createArticulo`/`updateArticulo`/`deleteArticulo`) e importación
  (`importExcel`), con equivalentes de modo demo (datos de muestra
  mutables en memoria, sin backend) para poder probar el flujo completo
  sin desplegar nada.
- Sintaxis verificada con `esbuild` (parseo JSX + resolución de imports
  internos) al no haber acceso de red disponible para instalar
  dependencias y compilar con Vite en este entorno.

## v0.4 — 2026-08-01 — Empaquetado del monorepo para GitHub

- Se consolidan en un único repositorio los tres entregables que hasta
  ahora vivían en zips sueltos: `backend-api.zip`, `files.zip`
  (frontend + preview de diseño) y `files1.zip` (schema + CSV).
- Estructura final: `frontend/`, `backend/`, `database/`, `docs/`.
- Se corrige el `README.md` del frontend, que aún describía la paleta de
  color antigua (verde-azulado `#2C5F5B` / rojo-teja `#B5502E` / Space
  Grotesk) cuando el CSS ya usa la paleta marfil/latón (ver v0.3). El
  código (`index.css`, `index.html`) ya estaba al día; solo la
  documentación estaba desincronizada.
- Se añade `.gitignore` raíz (node_modules, `.env`, builds, los `.xlsx`
  originales) y este `HISTORIAL.md`.
- El informe técnico original (`listado_consulta.md`) pasa a
  `docs/informe-tecnico.md` como documento de referencia de arquitectura.
- El mockup de un solo fichero (`preview_v2.jsx`, con datos de muestra
  embebidos) se conserva como referencia visual en
  `docs/design-reference/`, fuera del código de la app real.

## v0.3 — Rediseño visual: de "almacén genérico" a "ledger de hotel"

- Cambio de dirección de diseño completo sobre el frontend ya funcional:
  - Papel marfil envejecido `#F4EFE3` (antes fondo cream `#F5F4F0` sin
    carácter).
  - Latón `#A87C3F` como único acento de interacción (bordes activos,
    código de artículo, estado "Activo"), sustituyendo el verde-azulado
    genérico `#2C5F5B`.
  - Vino/burdeos `#6E2A2A` reservado solo para "No activo" — se piensa
    como tinta roja de libro de contabilidad, no como rojo de alerta de
    interfaz (antes rojo-teja `#B5502E`).
  - Tipografía de títulos: Space Grotesk (geométrica/neutra) → Fraunces
    (serif editorial, cartelería de hotel con solera). Se mantienen Inter
    (texto) e IBM Plex Mono (códigos DALI/SAP).
  - Elemento de firma nuevo: el código de cada artículo (`DALI-1352`) se
    dibuja como una etiqueta de equipaje de latón (rectángulo con "ojal"
    circular) en vez de una píldora/badge genérico.
- Se genera `preview_v2.jsx` como exploración rápida de un solo fichero
  para validar la dirección antes de aplicarla al proyecto modular.

## v0.2 — Backend API (Node.js + Express + Supabase)

- Implementación completa de los endpoints de la sección 7 del informe
  técnico: `GET /articulos` (búsqueda avanzada + regla de visibilidad
  `activo_dali`), `GET /articulos/:id`, `GET /articulos/:id/fichas`,
  `POST /admin/import-excel`, CRUD `POST|PUT|DELETE /admin/articulos`,
  `GET /export/excel`, `GET /export/pdf`.
- Middleware de autenticación JWT (`src/middleware/auth.js`) con roles
  `admin`/`lectura`, preparado para sustituirse por Supabase Auth.
- Sintaxis verificada archivo por archivo.
- Pendiente identificado: resolución de dimensiones nuevas (familia,
  subfamilia, proveedor) en la importación de Excel, subida a Storage y
  endpoint de login — documentado en `backend/README.md`.

## v0.1 — Modelo de datos y carga inicial desde los Excel de origen

- Análisis de `ARTICULOS_DALI.xlsx` y `LISTADO_CODIGOS_DALI_-_SAP.xlsx`:
  jerarquía verificada 100% consistente — **13 naturalezas → 53 familias
  → 253 subfamilias** (cada familia pertenece a una única naturaleza,
  cada subfamilia a una única familia).
- Se añade la tabla `naturalezas` (nivel superior a familia) al modelo de
  datos del informe original, más los campos de código SAP presentes en
  el segundo Excel.
- `schema.sql`: DDL completa para Supabase/Postgres — tablas
  normalizadas, índices para el buscador (nombre, código DALI/SAP,
  familia, subfamilia, proveedor), vista `v_articulos_completo` con los
  joins resueltos, y Row Level Security básica (usuario estándar solo ve
  `activo_dali = true`).
- `build_csvs.py`: script que genera los CSV normalizados con IDs
  enlazados a partir de los dos Excel — reutilizable si se vuelven a
  actualizar los Excel de origen.
- CSV generados: `naturalezas.csv`, `familias.csv`, `subfamilias.csv`,
  `proveedores.csv`, `articulos.csv`, listos para importar en ese orden.

## v0.0 — Informe técnico inicial

- Documento base (`docs/informe-tecnico.md`) con la arquitectura general
  (React/TS + API REST + Supabase), reglas de visibilidad por rol
  (`ACTIVO DALI`), modelo de datos, funcionalidades principales,
  seguridad/roles y endpoints esenciales.

---

## Pendientes acumulados (vigentes a fecha de la última entrada)

> Limpieza 2026-08-14: esta lista llevaba tiempo sin revisarse y tenía
> puntos ya resueltos en versiones posteriores a cuando se anotaron, sin
> que nadie los tachara. Se quitaron de aquí (no se repite el detalle,
> ya está en sus propias entradas de versión):
> - Borrar una ficha ya subida sin sustituirla → resuelto en v0.27
>   (`DELETE /admin/articulos/:id/fichas/:tipo`).
> - Despliegue en Render con CI/CD desde GitHub → hecho, en marcha desde
>   hace tiempo (ver v0.6, `DEPLOY.md`).
> - URLs firmadas para imágenes/PDF → ya implementado
>   (`storageController.js`/`articulosController.js`, `createSignedUrl`).
> - El hallazgo de `control-pedidos-princess` (contraseñas en texto
>   plano) → corregido en ese proyecto (`_verifica_y_migra_password`,
>   hash con `check_password_hash` + migración automática en el primer
>   login). El registro detallado del hallazgo no se incluye en este
>   repo por tratarse de información crítica de otra aplicación (ver
>   `README.md` para la anotación breve).

> Limpieza 2026-09-02: se quita de aquí la recuperación de contraseña por
> email y la pantalla de "olvidé mi contraseña" — resueltas en v1.14
> (ver esa entrada para el detalle completo: contraseña temporal
> automática para email ya registrado, solicitud de acceso
> admin-aprobada para email no registrado).

> Limpieza 2026-09-02 (v1.15): se quita de aquí "hacer DALI autosuficiente
> para el envío de correo (EmailJS propio) y enlaces de un solo uso en
> vez de contraseña temporal" — resuelto en v1.15 (ver esa entrada para
> el detalle completo). Queda anotada, esta vez explícitamente a petición
> de Víctor como actualización próxima (no resuelta todavía), la
> migración de "Documentación faltante" del puente con Control de
> Pedidos a ese mismo EmailJS propio.

> Limpieza 2026-09-03 (v1.16): se quita de aquí "rellenar las credenciales
> reales de la Cuenta 1 de EmailJS y desplegar v1.15/1.19.33 en Render" —
> hecho junto con Víctor en esta sesión (cuenta EmailJS propia
> "CatalogoDaliSap" creada, plantilla revisada y con las variables
> correctas, deploy confirmado en producción por el número de versión en
> el pie de página). Se deja anotada, en su lugar, la Cuenta 2 — todavía
> sin rellenar — y el cambio cosmético pendiente del "From Name" de esa
> plantilla, que sigue diciendo "Control de Pedidos Princess".

> Limpieza 2026-09-07 (v1.38): se quitan de aquí "aplicar las migraciones
> del aviso a administradores y rellenar la Private Key de la Cuenta 1"
> y "cambiar el From Name de la plantilla" — ambas hechas por Víctor
> (ver esa entrada para el detalle completo, incluida la causa real de
> por qué el aviso no llegaba pese a tener ya la Private Key puesta:
> "Allow API calls" desactivado en EmailJS.com, no un fallo del código).
> Confirmado con una solicitud de prueba y una real de un compañero,
> ambas entregadas el mismo día.

> Limpieza 2026-09-09 (v1.42): se quita de aquí "migrar 'Documentación
> faltante' del puente de correo con Control de Pedidos al EmailJS propio
> de DALI" — resuelto en v1.42, a petición de Víctor. Queda anotado, en
> su lugar (ver más abajo), el único paso manual que falta para que el
> envío directo funcione de verdad: crear en EmailJS.com la plantilla
> de proveedor (con Reply To dinámico) y pegar su ID en Administración →
> Configuración EmailJS.

> Limpieza 2026-09-10 (v1.44): se quita de aquí "crear en EmailJS.com la
> plantilla de proveedor y pegar su ID" — resultó innecesario: la
> plantilla de usuario de siempre ya tenía "Reply To" con `{{reply_to}}`
> puesto (Víctor lo confirmó con una captura de EmailJS.com), así que se
> revirtió el diseño de v1.42 en v1.44 y "Documentación faltante" ya
> funciona con la configuración que Víctor tiene desde v1.15 — sin
> ningún paso manual nuevo pendiente.

- **Backend:** verificación por email tras varios días sin login (ahora
  podría apoyarse en el EmailJS propio de DALI, ver v1.15, en vez de
  necesitar un proveedor de email nuevo o el puente con Control de
  Pedidos); tests de integración por endpoint.
- Rellenar las credenciales de la **Cuenta 2** de EmailJS de DALI desde
  Administración → Configuración EmailJS — la Cuenta 1 ya está rellena
  con credenciales reales y confirmada funcionando en producción,
  incluido el envío a administradores (v1.38); falta la segunda, que
  solo entra en juego por rotación automática al llegar al umbral de
  envíos (no bloquea el uso normal mientras tanto). Al rellenarla,
  revisar también en EmailJS.com que "Allow API calls" esté activado
  para esa cuenta/servicio (ver v1.38) — si es la misma cuenta EmailJS
  que la Cuenta 1, ya debería valer con el mismo ajuste.
