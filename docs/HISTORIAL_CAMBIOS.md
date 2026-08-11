# Historial de Cambios — Ecosistema Princess Compras (unificado)

> Documento único de seguimiento. Se actualiza cambio a cambio, entrada
> más reciente arriba. Componentes: **Organizador** (main_agenda,
> desktop), **Control Pedidos** (backend Flask principal), **Chat**
> (backend Flask/SocketIO independiente), **Infra** (Render /
> Cloudflare / GitHub Actions, no es código de la app).

> **Normas de entrega (obligatorias para cualquier cambio, ya lo
> implemente Claude, otra IA o cualquier programador humano):**
> 1. No se entrega el proyecto completo (ni el ZIP entero): solo los
>    archivos individuales modificados o creados, indicando su ruta
>    dentro del proyecto.
> 2. Toda entrega debe registrar una entrada nueva aquí (más reciente
>    arriba) y en `CHANGELOG.md`, describiendo petición, causa/hallazgo
>    y corrección aplicada.
> 3. Actualizar `README.md` si el cambio afecta a algo que el README
>    documenta (versión actual, funcionalidades, requisitos, etc.).
> 4. Subir el número de versión en el badge de `templates/index.html`
>    (formato `V MAJOR.MINOR.PATCH`), coherente con el de `CHANGELOG.md`
>    y esta entrada.

---

## 2026-08-11 13:15

### [Control Pedidos] v12.29.88 — Correo de resumen "Comparar listado PDF": solo pedidos con proveedor identificado
- Petición del usuario: en el correo de resumen que se envía al
  comprador, solo deben aparecer los pedidos cuyo proveedor se ha
  identificado correctamente contra el catálogo — el resto de
  información (pedidos de proveedor no identificado) es solo para
  revisión visual del admin en la propia pantalla, no debe salir en el
  correo.
- Corrección (`comparar_listado_pdf_enviar_resumen`): los pedidos sin
  dar de alta se filtran ahora en dos grupos — `pedidos_faltantes`
  (proveedor identificado, `proveedor_identificado: true`) es lo único
  que entra en la tabla del correo; `no_identificados` es solo un
  recuento. Si no queda ningún pedido con proveedor identificado, el
  endpoint devuelve un aviso claro en vez de enviar un correo vacío
  (indicando cuántos hay pendientes de revisar en pantalla, si los hay).
- `_email_resumen_pdf_sap()` gana el parámetro `no_identificados`: si es
  mayor que 0, añade una nota de aviso (⚠️, fondo amarillo) indicando
  cuántos pedidos adicionales hay sin dar de alta pero con proveedor no
  identificado, sin listarlos — remite a revisarlos en pantalla en vez
  de incluirlos con datos no del todo fiables.
- `templates/index.html`: el botón "📧 Enviar resumen por correo" ahora
  solo se muestra si hay al menos un pedido faltante CON proveedor
  identificado (antes se mostraba con cualquier pedido faltante,
  identificado o no) — evita un clic que solo lleva a un error si todo
  lo pendiente es de proveedor no identificado.
- Probado con datos simulados extraídos directamente de las funciones
  reales del código (`_email_resumen_pdf_sap`): un pedido de proveedor
  no identificado no aparece en la tabla del correo, y si hay alguno, la
  nota de aviso con el recuento sí aparece.
- `app.py` compila sin errores. Los 9 bloques `<script>` de
  `templates/index.html` pasan `node --check`. `README.md` actualizado
  a la versión actual. Badge de versión del sidebar actualizado a
  "V 12.29.88"; entrada añadida en `CHANGELOG.md`.

## 2026-08-11 12:10

### [Control Pedidos] v12.29.86 — "Comparar listado PDF" pasa a leer el listado SIMPLIFICADO de SAP (MT2) + estado de entrega derivado
- Petición del usuario: adaptar "Comparar listado PDF" para leer el
  "Listado de Pedidos" SIMPLIFICADO que exporta SAP (una línea por
  pedido, sin el detalle de artículos — mucho más ligero que el listado
  completo usado hasta ahora, MT) y, aprovechando que esa vista trae el
  importe del pedido y el importe recibido en la misma línea, deducir
  el estado real de entrega de cada pedido sin abrir el listado
  completo: importe recibido = 0 → "No entregado"; importe recibido =
  importe del pedido → "Entregado"; cualquier otra cantidad → "Entrega
  parcial".
- Nuevo patrón de reconocimiento `_PATRON_LISTADO_SIMPLIFICADO`
  (sustituye al anterior, pensado para el listado completo con
  artículos, "NNNNNNNN - Pedido DD/MM/AAAA HH:MM:SS (PROVEEDOR
  Teléfono:...)") — verificado contra un listado real de 221 pedidos
  del hotel MT, 221/221 reconocidos.
- Hallazgo durante la propia verificación, antes de dar el cambio por
  bueno: el texto que devuelve `pypdf.extract_text()` para este PDF NO
  sigue el orden visual de las columnas de la tabla, sino el orden real
  del contenido del PDF (`Nº pedido, fecha/hora, importe base,
  proveedor, fecha pedido, fecha entrega, estado, importe recibido,
  importe pendiente`) — el patrón se construyó contra ese orden real,
  no el visual.
- Segundo hallazgo, tras una primera entrega que el usuario reportó con
  "No se ha reconocido ningún pedido en el PDF": la verificación previa
  se hizo sin querer con `pypdf` 3.17.4 (versión antigua ya presente en
  el entorno de pruebas de la IA), no con la que realmente instala este
  proyecto (`requirements.txt`: `pypdf>=4.0`, sin techo de versión →
  instala la última disponible, 6.15.0 en el momento de esta entrega).
  Entre pypdf 3.x y ≥4 cambió el extractor de texto: donde el PDF no
  tiene un espacio real entre dos columnas contiguas (solo separación
  por posición X), pypdf 3.x rellenaba con un espacio al extraer el
  texto y pypdf ≥4 ya no lo hace — el texto sale pegado
  ("2.852,10PILSA HOSTELERIA...") justo en 3 de los separadores del
  patrón (importe base→proveedor, proveedor→fecha de pedido,
  estado→importe recibido), que exigían espacio obligatorio y por eso
  no reconocían nada en el entorno real.
- Corregido: esos separadores (y el resto, por consistencia) pasan de
  "uno o más espacios" a "cero o más" — sigue funcionando igual si hay
  espacio, y ya no rompe si no lo hay. Reverificado contra el mismo
  listado real de 221 pedidos con pypdf 3.17.4 Y con pypdf 6.15.0
  (221/221 en ambos casos) antes de esta entrega.
- Nuevos campos por pedido en el resultado de
  `_comparar_listado_pdf_logica()`: `fecha_pedido`, `fecha_entrega`,
  `importe_base`, `importe_recibido`, `estado_sap` (Abierto/Cerrado tal
  cual lo trae SAP) y `entrega_estado` (Entregado / Entrega parcial /
  No entregado). El resumen añade contadores
  `entregados`/`entregas_parciales`/`no_entregados`.
- `templates/index.html`: tabla de resultados de "Comparar listado PDF"
  con columnas nuevas (fecha de pedido, fecha de entrega, importe,
  recibido, estado de entrega con icono/color), filtro adicional por
  estado de entrega, píldoras de resumen nuevas, y texto del modal
  actualizado para reflejar que ahora se usa el listado simplificado.
  Correo de resumen (`_email_resumen_pdf_sap`) añade una columna con el
  estado de entrega de cada pedido sin registrar.
- `app.py` compila sin errores (`python3 -m py_compile`). Los 9 bloques
  `<script>` de `templates/index.html` pasan `node --check`. `README.md`
  actualizado a la versión actual. Badge de versión del sidebar
  actualizado a "V 12.29.86"; entrada añadida en `CHANGELOG.md`.

## 2026-08-11 09:00

### [Control Pedidos] v12.29.84 — Correo de resumen: despacho inmediato en vez de esperar al ciclo de 5 min
- Consulta del usuario: el correo de resumen llegó bien, pero tardó
  "un ratito" — no fue casi automático como el resto de correos,
  ¿por qué?
- Respuesta, confirmada revisando el código: es exactamente el mismo
  sistema de siempre — pero el navegador solo revisa la cola de
  correos pendientes cada 5 minutos
  (`_startEmailsSistemaPolling`, `setInterval(..., 5*60*1000)`). Con
  las alertas automáticas nunca se nota, porque solo se ven ya
  llegadas en la bandeja; al pulsar un botón y quedarse esperando,
  si toca a mitad del ciclo de 5 min, sí se nota.
- Mejora aplicada: `enviarResumenComparacionPdf()` dispara ahora un
  despacho inmediato (`_enviarEmailsSistemaPendientes()`) justo
  después de encolar el correo, desde el propio navegador que acaba
  de generarlo — mismo mecanismo de siempre (EmailJS desde el
  navegador), solo se adelanta el primer intento en vez de esperar
  al siguiente ciclo automático de 5 min.
- `app.py` sin cambios (solo frontend). Los 9 bloques `<script>` de
  `templates/index.html` pasan `node --check`. `README.md`
  actualizado a la versión actual. Badge de versión del sidebar
  actualizado a "V 12.29.84"; entrada añadida en `CHANGELOG.md`.

## 2026-08-10 13:10

### [Control Pedidos] v12.29.82 — Correo de resumen: confirmado el filtrado + columnas reordenadas
- Pregunta del usuario: ¿qué tratamiento reciben los "NO
  encontrados" en el correo de resumen? ¿solo se envían los sujetos
  a seguimiento?
- Confirmado revisando el propio código: `resultado["pedidos"]` (de
  donde se filtran los "no encontrados" para el correo) nunca
  contiene los proveedores excluidos — se descartan antes, dentro de
  `_comparar_listado_pdf_logica()`
  (`if prov_match and not prov_match["sujeto_seguimiento"]:
  continue`). El correo ya enviaba exactamente lo pedido: solo
  pedidos sujetos a seguimiento y no registrados en la app — es
  imposible que se cuele uno excluido, porque nunca llega a entrar
  en la lista de la que se filtra.
- Único ajuste real hecho: orden de columnas de la tabla del correo,
  a petición del usuario — Nº Pedido → Proveedor → Fecha (antes Nº
  Pedido → Fecha → Proveedor). Verificado con datos simulados
  extraídos con `ast` directamente del código real.
- `app.py` compila sin errores. `README.md` actualizado a la versión
  actual. Badge de versión del sidebar actualizado a "V 12.29.82";
  entrada añadida en `CHANGELOG.md`.

## 2026-08-10 12:50

### [Control Pedidos] v12.29.80 — "Comparar listado PDF": correo de resumen al comprador + texto aclarado
- Petición: 1) que el resultado solo muestre pedidos de proveedores
  sujetos a seguimiento, indicando el resto solo como recuento;
  2) enviar un correo interno al comprador responsable del hotel,
  con copia al administrador que hace la consulta, con el resumen
  de pedidos detectados en SAP/DALI pendientes de dar de alta en la
  app.
- Punto 1 ya lo hacía la funcionalidad desde su diseño original
  (la tabla de resultados nunca ha mostrado los proveedores
  excluidos) — solo se ajustó el texto del recuento a la redacción
  exacta pedida: "➖ X pedidos de proveedores no sujetos a
  seguimiento" (antes decía "excluidos (sin seguimiento)").
- Punto 2, nuevo:
  - Botón "📧 Enviar resumen por correo" en el resultado, visible
    solo si hay pedidos sin registrar (`no_encontrados > 0`).
    Acción explícita, no automática al terminar la comparación —
    para no reenviar sin querer si se vuelve a comparar el mismo
    listado mientras se revisa el resultado.
  - Nuevo
    `POST /api/pedidos/comparar-listado-pdf/<job_id>/enviar-resumen`:
    busca el/los comprador(es) del hotel con
    `_get_compradores_hotel()` (ya existente, misma asignación que
    usan las alertas), y encola un correo con copia al administrador
    que hizo la consulta, vía `_encolar_email_sistema()` — mismo
    mecanismo de cola que el resto de correos automáticos de la app
    (se despacha desde el navegador de quien tenga la app abierta,
    sin SMTP propio en el servidor).
  - Nueva plantilla `_email_resumen_pdf_sap()` — mismo estilo visual
    que el resto de correos internos de la app (`_email_header_html`
    + tabla + pie); tabla con Nº de pedido SAP, fecha y proveedor,
    acotada a 100 filas (con aviso de "y X más" si hay más) para no
    generar un correo kilométrico con listados grandes. Probada con
    datos simulados extraídos con `ast`: asunto correcto, recorte a
    100 filas y aviso del resto, todo funcionando.
  - Si el hotel no tiene ningún comprador con email asignado, el
    endpoint avisa con un error claro en vez de fallar en silencio.
- `app.py` compila sin errores; los 9 bloques `<script>` de
  `templates/index.html` pasan `node --check`. `README.md`
  actualizado a la versión actual. Badge de versión del sidebar
  actualizado a "V 12.29.80"; entrada añadida en `CHANGELOG.md`.

## 2026-08-10 12:15

### [Control Pedidos] v12.29.78 — Fix: "El job no existe o ha caducado" al comparar un listado PDF
- Reportado con captura: al comparar el listado, el primer sondeo ya
  daba "El job no existe o ha caducado — vuelve a subir el PDF",
  pese a que el `job_id` se había creado bien un instante antes
  (v12.29.74).
- Causa probable: `render.yaml` arrancaba gunicorn con `--workers 1`
  sin más — que usa por defecto el tipo de worker "sync", capaz de
  atender solo una petición a la vez en todo el proceso. Mientras el
  hilo en segundo plano de v12.29.74 procesaba el PDF (~8s de
  trabajo intensivo), el proceso podía quedarse sin responder con la
  rapidez que exige el health check de Render
  (`healthCheckPath: /ping`) — y si Render considera el proceso no
  saludable aunque sea un instante, reinicia el contenedor, lo que
  borra de golpe toda la memoria del proceso (incluido `_PDF_JOBS`,
  donde vivía el job a medias).
- Corregido: `startCommand` en `render.yaml` cambia a
  `--worker-class gthread --threads 4` — reparte las peticiones
  entrantes del mismo worker entre varios hilos, así que el health
  check y los sondeos del navegador se siguen atendiendo con
  normalidad mientras el hilo de fondo procesa el PDF. No requiere
  ninguna dependencia nueva (`gthread` es un tipo de worker propio de
  gunicorn, ya presente vía `requirements.txt`).
- **Aviso importante para el despliegue**: si el servicio en Render
  tiene el "Start Command" configurado directamente en el panel de
  Render (Settings → Start Command) en vez de leerlo de
  `render.yaml` en cada despliegue, hay que actualizarlo también ahí
  a mano con el mismo comando — `render.yaml` por sí solo no basta
  si el servicio no está gestionado como Blueprint desde este
  archivo.
- `app.py` sin cambios — este fix es solo de configuración de
  despliegue (`render.yaml`). Badge de versión del sidebar
  actualizado a "V 12.29.78"; entrada añadida en `CHANGELOG.md`.

## 2026-08-10 11:35

### [Control Pedidos] v12.29.76 — Spinner de carga profesional, en los colores de marca
- Petición: algo visual y profesional mientras se procesa (p. ej. el
  listado PDF) — en vez del texto plano actual, algo tipo el círculo
  de carga de Windows, o la animación de "pensando" de Claude.
- Cambio: la clase `.loading` (usada en "cargando pedidos" y en
  "Comparar listado PDF") ahora dibuja un spinner con CSS puro, sin
  imágenes ni dependencias nuevas — un anillo girando en dorado
  (estilo Windows) con un círculo interior que se llena y se vacía en
  azul marino, usando los propios colores de marca de la app
  (`--gold`/`--gold2`/`--navy2`). Construido con `::before`/`::after`
  sobre la propia clase `.loading`, así que no ha hecho falta tocar
  el HTML de ninguna de las 2 pantallas que ya la usaban — lo heredan
  automáticamente sin cambios de marcado.
- `app.py` sin cambios (solo CSS). Los 9 bloques `<script>` de
  `templates/index.html` pasan `node --check`; llaves del bloque
  `<style>` comprobadas cuadradas (301 abiertas / 301 cerradas).
  `README.md` actualizado a la versión actual. Badge de versión del
  sidebar actualizado a "V 12.29.76"; entrada añadida en
  `CHANGELOG.md`.

## 2026-08-10 11:10

### [Control Pedidos] v12.29.74 — Fix: "Comparar listado PDF" fallaba con PDFs grandes ("Unexpected token '<' ... is not valid JSON")
- Reportado con captura y el PDF real que lo disparó (178 páginas,
  hotel MT): al comparar, saltaba
  `Unexpected token '<', "<html>" is not valid JSON`.
- Causa: el proceso completo —leer el PDF, extraer el texto de las
  178 páginas (~8s medidos contra el propio PDF real) y comparar
  contra los pedidos ya registrados— se hacía todo dentro de una
  única petición HTTP. Con el cold-start del servicio gratuito de
  Render sumado a esos ~8s de proceso, la petición tardaba más que
  el timeout de algún punto intermedio entre el navegador y el
  servidor (el proxy delante de la app), que cortaba la conexión y
  devolvía su propia página de error HTML en lugar de dejar pasar la
  respuesta JSON — de ahí el `<html>` en el mensaje de error que veía
  el usuario.
- Corregido haciendo el endpoint asíncrono:
  - `POST /api/pedidos/comparar-listado-pdf` ahora solo valida el
    archivo y arranca el trabajo pesado en un hilo aparte
    (`threading`), respondiendo al momento con un `job_id` — muy por
    debajo de cualquier timeout, sea cual sea.
  - Nuevo `GET /api/pedidos/comparar-listado-pdf/<job_id>` para
    consultar el resultado — el frontend hace polling cada 2
    segundos (hasta 5 minutos) en vez de esperar una sola respuesta
    larga.
  - El hilo en segundo plano usa `with app.app_context()` — mismo
    patrón ya usado en `init_db()` — porque `query()`/`get_db()`
    dependen de `g`, con ámbito de petición, no accesible desde un
    hilo nuevo sin esto.
  - Estado de los jobs en memoria (`_PDF_JOBS` + `threading.Lock()`
    a nivel de módulo), con limpieza automática de jobs de más de 30
    minutos para no acumular memoria indefinidamente.
  - La lógica de extracción/comparación en sí no cambia de
    comportamiento — se movió a una función aparte,
    `_comparar_listado_pdf_logica()`, para poder llamarla igual
    desde una petición normal o desde el hilo en segundo plano.
    Verificada de nuevo, extraída directamente del código con `ast`
    (mismo patrón ya usado en la Fase 8 del rediseño de Techo),
    contra el PDF real del reporte (178 páginas / 563 pedidos,
    tiempo total ~8,3s) — mismo resultado que antes del refactor.
- `app.py` compila sin errores; los 9 bloques `<script>` de
  `templates/index.html` pasan `node --check`. `README.md`
  actualizado a la versión actual. Badge de versión del sidebar
  actualizado a "V 12.29.74"; entrada añadida en `CHANGELOG.md`.

## 2026-08-10 10:30

### [Control Pedidos] v12.29.72 — "Sujeto a seguimiento" restringido solo a Admin
- Petición: los roles hotel y compras no deben poder modificar el
  campo "Sujeto a seguimiento en Comparar listado PDF" de la ficha
  de proveedor.
- Hotel ya no podía crear ni editar proveedores en absoluto
  (`create_proveedor`/`update_proveedor` ya devolvían 403 para ese
  rol) — sin cambios necesarios ahí.
- Compras sí puede seguir editando la ficha del proveedor con
  normalidad (nombre, código, contactos, observaciones), pero ya no
  este campo en concreto:
  - Backend: al crear un proveedor, si quien hace la petición no es
    admin, se crea siempre con el valor por defecto (`FALSE`),
    ignorando lo que trajera el payload. Al editar, si no es admin,
    se conserva el valor que ya tuviera guardado el proveedor en vez
    de aceptar lo que llegue en la petición — así, aunque compras
    edite cualquier otra cosa de la ficha (añadir un contacto, por
    ejemplo), este campo no se toca ni se resetea sin querer.
  - Frontend: el checkbox se deshabilita (no solo se oculta) para
    cualquiera que no sea admin, con un aviso "Solo un administrador
    puede cambiar esto" junto al texto de ayuda — doble seguridad,
    el backend rechaza el cambio igualmente aunque alguien fuerce el
    DOM del navegador.
- `app.py` compila sin errores; los 9 bloques `<script>` de
  `templates/index.html` pasan `node --check`. `README.md`
  actualizado a la versión actual. Badge de versión del sidebar
  actualizado a "V 12.29.72"; entrada añadida en `CHANGELOG.md`.

## 2026-08-10 10:05

### [Control Pedidos] v12.29.70 — Fix: los proveedores seguían saliendo "Sujeto a seguimiento" pese al cambio a opt-in
- Reportado con captura: al editar un proveedor, el checkbox salía
  marcado — contradiciendo el propio texto de ayuda de al lado, que
  ya decía "Desmarcado por defecto para todos los proveedores"
  (v12.29.68, entregado minutos antes).
- Causa: el SQL de emergencia entregado el mismo día para desbloquear
  `/api/proveedores` (v12.29.66, antes de que el usuario pidiera el
  cambio a opt-in) creaba la columna con `DEFAULT TRUE`. Al haberse
  ejecutado, `sujeto_seguimiento` quedó creada con todos los
  proveedores en `TRUE` — y la migración de v12.29.68
  (`ADD COLUMN IF NOT EXISTS ... DEFAULT FALSE`) es un no-op si la
  columna ya existe (por diseño de `IF NOT EXISTS`), así que nunca
  llegó a corregir nada, ni el `DEFAULT` ni los valores ya puestos.
- Corregido: nueva migración que consulta el `DEFAULT` real de la
  columna en `information_schema.columns` y, si no es `FALSE`
  (columna inexistente, o existente con el `DEFAULT` antiguo),
  corrige el `DEFAULT` de la columna **y** resetea a `FALSE` los
  proveedores que estuvieran en `TRUE` — seguro de hacer aquí porque,
  al ser una funcionalidad recién nacida y con la pantalla rota hasta
  ahora, nadie ha podido marcar todavía ningún proveedor a propósito.
  Es correctiva y de una sola vez: en cuanto el `DEFAULT` quede en
  `FALSE`, la condición deja de cumplirse y no se vuelve a tocar nada
  en arranques futuros — cualquier proveedor que un admin marque
  después de esto queda a salvo para siempre, no se resetea en cada
  reinicio del servidor.
- `app.py` compila sin errores. `README.md` actualizado a la versión
  actual. Badge de versión del sidebar actualizado a "V 12.29.70";
  entrada añadida en `CHANGELOG.md`.

## 2026-08-10 09:20

### [Control Pedidos] v12.29.68 — Causa raíz del fallo de migración, "Comparar listado PDF" solo Admin, filtro de proveedores invertido a opt-in
- Usuario reportó que, incluso en v12.29.64 (posterior a cuando se
  "arreglaron"), seguían los 3 errores de RLS en Supabase Y el 500
  de `/api/proveedores` — confirmando que el fix anterior
  (aislar cada migración en su propio try/except) no era suficiente
  por sí solo.
- **Causa raíz encontrada**: las 3 migraciones más recientes (RLS,
  `sujeto_seguimiento`, hotel de pruebas `PR`) vivían casi al final
  de `_auto_migrate()`, una función con 111 sentencias de migración
  en total. Si cualquiera de las ~108 sentencias *anteriores* a
  ellas fallaba por el motivo que fuera —sin relación con estos
  cambios—, el `except` genérico de toda la función paraba la
  ejecución justo ahí, y estas 3, al estar casi al final, nunca
  llegaban a aplicarse. El try/except individual de cada una (fix
  de v12.29.66) las protegía de fallar POR SÍ MISMAS, pero no de
  nunca llegar a EJECUTARSE si algo anterior ya había abortado la
  función entera.
- Corregido moviendo las 3 al principio del todo de
  `_auto_migrate()`, justo después de `with db.cursor() as cur:` —
  antes de cualquier otra de las 108 sentencias restantes. Así se
  garantiza que se apliquen siempre en cada arranque, pase lo que
  pase más abajo en el resto de la función esa misma ejecución.
  Cada una conserva además su propio try/except, por si alguna de
  estas 3 en concreto falla.
- Pendiente, no localizado todavía: cuál de las ~108 sentencias
  restantes es la que ha estado fallando (o ha estado fallando en
  algún momento) — revisar el log de arranque real del servidor,
  buscando "Auto-migración omitida", identificaría la causa de
  fondo de fondo si se quiere perseguir más allá de blindar el
  orden de estas 3.
- **"Comparar listado PDF" — restringido solo a Admin** (petición
  del usuario; antes admin+compras): backend
  (`if session.get("rol") != "admin"`) y visibilidad del botón en
  el frontend actualizados a la vez, en los 2 puntos de
  inicialización donde se controla.
- **Filtro de proveedores invertido a opt-in** (petición del
  usuario; antes opt-out): con muchos más proveedores de compra
  diaria que proveedores a seguir, es más seguro que todos
  empiecen apagados y el admin encienda solo los que le interesa
  vigilar. `sujeto_seguimiento` pasa a `DEFAULT FALSE`; checkbox de
  la ficha de proveedor desmarcado por defecto, tanto al crear uno
  nuevo como al abrir uno existente que nunca se haya marcado
  explícitamente; texto de ayuda del checkbox reescrito para
  reflejar el nuevo criterio; docstring del endpoint de comparación
  actualizado para avisar de que, hasta que se marquen proveedores,
  el listado devolverá pocos o ningún pedido evaluado —
  comportamiento esperado, no un fallo.
- `app.py` compila sin errores; los 9 bloques `<script>` de
  `templates/index.html` pasan `node --check`. `README.md`
  actualizado a la versión actual. Badge de versión del sidebar
  actualizado a "V 12.29.68"; entrada añadida en `CHANGELOG.md`.

## 2026-08-10 08:40

### [Control Pedidos] v12.29.66 — Fix: /api/proveedores caía con 500 — migración de sujeto_seguimiento nunca se ejecutó
- Reportado con captura de la consola del navegador:
  `[500] Error inesperado: column "sujeto_seguimiento" does not exist`
  — la pantalla de Proveedores se quedaba vacía, sin más pista.
- Causa: `_auto_migrate()` tiene 111 sentencias de migración en
  total, y la inmensa mayoría (incluida la de `sujeto_seguimiento`,
  casi al final de la función) no tenía su propio `try/except` — si
  cualquier sentencia ANTERIOR fallaba por el motivo que fuera, sin
  relación con este cambio concreto, el `except` genérico de toda la
  función paraba la ejecución justo ahí, y esta `ALTER TABLE` nunca
  llegaba a aplicarse.
- Arreglo inmediato comunicado al usuario para desbloquear sin
  esperar a un redeploy — SQL seguro de ejecutar a mano en el SQL
  Editor de Supabase:
  `ALTER TABLE proveedores ADD COLUMN IF NOT EXISTS
  sujeto_seguimiento BOOLEAN NOT NULL DEFAULT TRUE;`
- Corregido de raíz en el código:
  - La migración de `sujeto_seguimiento` y la del hotel de pruebas
    `PR` (v12.29.32-33, también sin proteger) se aíslan ahora en su
    propio `try/except` — mismo patrón ya usado para RLS y
    `expediente_exceso` — para que sean robustas frente a cualquier
    fallo anterior no relacionado en la misma ejecución de
    `_auto_migrate()`.
  - `loadProveedores()` (frontend) no capturaba la excepción de
    `api()` — si la petición fallaba, la pantalla se quedaba vacía
    sin ningún aviso, indistinguible de "no hay proveedores de
    verdad". Así es exactamente como se llegó a reportar esto como
    "no salen los proveedores" en vez de como un error real. Ahora
    se captura y se muestra con un `toast()` de error, con el
    detalle exacto del fallo — para que la próxima vez que algo así
    pase, se vea de inmediato que es un error, no una lista vacía.
- Pendiente, no localizado en esta corrección: qué sentencia ANTERIOR
  de las 111 de `_auto_migrate()` estuvo fallando y provocando esto
  — revisar el log de arranque real del servidor (buscar
  "Auto-migración omitida") para identificarla, si se quiere llegar a
  la causa raíz de fondo en vez de solo blindar las migraciones más
  recientes una a una.
- `app.py` compila sin errores; los 9 bloques `<script>` de
  `templates/index.html` pasan `node --check`. `README.md`
  actualizado a la versión actual. Badge de versión del sidebar
  actualizado a "V 12.29.66"; entrada añadida en `CHANGELOG.md`.

## 2026-08-10 08:15

### [Control Pedidos] v12.29.64 — Fix: el +34 del teléfono salía duplicado en la firma de los correos
- Reportado con captura de un correo real: la firma mostraba
  `(+34) +34681111792` — el prefijo repetido.
- Causa: `_firma_comprador_html()`/`_firma_comprador_text()`
  anteponen siempre `"(+34)"` al móvil guardado del usuario, pero el
  propio campo del formulario sugiere como placeholder
  "+34 600 000 000" — algunos usuarios lo guardan ya con el prefijo
  incluido, y entonces se duplicaba al construir la firma.
- Corregido: nuevo helper `_formatear_movil_firma()` que quita
  cualquier `+34`/`0034`/`34` inicial (con o sin espacio después) del
  móvil guardado antes de anteponer el `(+34)` fijo de la firma — el
  resultado sale limpio se haya guardado el número como se haya
  guardado. Probado contra varios formatos realistas
  (`+34681111792`, `34681111792`, `0034681111792`, con espacios al
  principio/final...), todos correctos.
- `app.py` compila sin errores. `README.md` actualizado a la versión
  actual. Badge de versión del sidebar actualizado a "V 12.29.64";
  entrada añadida en `CHANGELOG.md`.

## 2026-08-06 11:35

### [Control Pedidos] v12.29.62 — Seguridad: RLS activado en 3 tablas nuevas (aviso del Security Advisor de Supabase)
- Reportado con el propio informe del linter de Supabase (tabla de
  hallazgos pegada tal cual): `RLS Disabled in Public` sobre
  `public.proveedor_contacto_hoteles`, `public.expediente_exceso` y
  `public.bridge_popup_visto` — 3 tablas creadas en sesiones
  recientes de esta misma semana que se quedaron sin el
  `ENABLE ROW LEVEL SECURITY` que ya se aplicaba a otras 4 tablas
  desde julio (`egress_tracking`, `db_size_tracking`,
  `db_vacuum_log`, `agente_heartbeat`).
- Mismo criterio ya verificado entonces, sin ningún cambio de
  comportamiento: esta app nunca usa la API REST automática de
  Supabase (PostgREST) — todo habla por conexión directa a Postgres
  con `DATABASE_URL`, nunca con la anon key — así que activar RLS
  sin ninguna política es 100% seguro para el funcionamiento, solo
  cierra el acceso público accidental por esa otra vía que la app no
  usa de todos modos.
- Añadidas las 3 tablas a la misma tupla ya existente dentro de
  `_auto_migrate()` — comentario actualizado para reflejar que la
  lista ya no son solo las 4 tablas originales de julio, sino que se
  amplía según el propio Security Advisor va señalando tablas
  nuevas sin este `ALTER` desde el principio.
- `app.py` compila sin errores. `README.md` actualizado a la versión
  actual. Badge de versión del sidebar actualizado a "V 12.29.62";
  entrada añadida en `CHANGELOG.md`.

## 2026-08-06 11:20

### [Control Pedidos] v12.29.60 — Nueva funcionalidad: comparar listado PDF de SAP contra los pedidos registrados
- Petición: poder cargar semanalmente, por hotel, el "Listado de
  Pedidos" que exporta SAP, y que la app indique qué pedidos de ese
  listado NO están dados de alta aquí para su seguimiento — más un
  filtro de proveedores para excluir del aviso a los de compra diaria
  (alimentación/bebida), que no se siguen en esta aplicación.
- Probado contra un listado real (262 páginas / 622 pedidos, hotel
  Guayarmina) antes de dar la extracción por buena, no solo en
  teoría. Confirmado que el formato de SAP es 100% fijo y
  predecible — no hace falta ningún tipo de lectura "de IA" costosa,
  basta con una expresión regular sobre el texto del PDF. Se
  encontró y corrigió un caso real de emparejamiento de proveedor
  por una tilde ("Pastelería" vs "Pasteleria" del listado) durante
  la propia prueba, antes de dar el emparejamiento por bueno.
- Nueva dependencia `pypdf` (`requirements.txt`) — lectura del PDF en
  Python puro, sin depender de ningún binario del sistema (más
  portable en un despliegue de Render estándar que
  `pdftotext`/poppler, que necesitarían instalarse aparte).
- Nueva columna `sujeto_seguimiento` en `proveedores` (migración
  automática dentro de `_auto_migrate()`, `DEFAULT TRUE` — todos los
  proveedores existentes quedan "sujetos" por defecto, hay que
  desmarcar los de alimentación/bebida a mano). Nuevo checkbox en la
  ficha de cada proveedor: "Sujeto a seguimiento en 'Comparar listado
  PDF'".
- Nuevo endpoint `POST /api/pedidos/comparar-listado-pdf`
  (`hotel_id` + `file` en el `form-data`): extrae todos los números
  de pedido de SAP con el patrón
  `NNNNNNNN - Pedido DD/MM/AAAA HH:MM:SS (PROVEEDOR...)` (verificado
  contra el listado real, 622/622 sin ningún fallo), y los compara
  contra `pedido_num` de los pedidos de ese hotel en la app —
  normalizando ceros a la izquierda para no dar falsos "no
  encontrado" por diferencias de formato entre quien lo tecleó y el
  número real de SAP. El emparejamiento de nombres de proveedor (para
  aplicar el filtro de seguimiento) normaliza acentos, puntuación y
  formas societarias comunes (SL/SA/SLL/SLU/SCOOP/CB), con
  coincidencia exacta primero y, si falla, parcial (uno contiene al
  otro). Los pedidos de un proveedor marcado `sujeto_seguimiento=FALSE`
  se excluyen del todo del resultado — ni cuentan como encontrados ni
  como no encontrados.
- Nuevo botón "📄 Comparar listado PDF" en la pantalla de Pedidos,
  visible solo para admin/compras (igual que el backend) — modal con
  selector de hotel, subida del PDF, resumen visual (📄 total en el
  listado / ✅ encontrados / ⛔ no encontrados / ➖ excluidos por el
  filtro), tabla con filtro "mostrar solo los que faltan" (marcado
  por defecto), aviso ⚠️ cuando un proveedor del PDF no se ha podido
  identificar en el catálogo, y botón "➕ Crear pedido" por cada fila
  que falte — abre el formulario de alta con el hotel y el Nº de SAP
  ya rellenados, para no tener que volver a teclearlos.
- `app.py` compila sin errores; los 9 bloques `<script>` de
  `templates/index.html` pasan `node --check` sin ningún fallo.
  `README.md` actualizado a la versión actual. Badge de versión del
  sidebar actualizado a "V 12.29.60"; entrada añadida en
  `CHANGELOG.md`.
- **Pendiente / posibles mejoras futuras, no implementadas todavía**:
  recordatorio automático semanal para que un admin no se olvide de
  subir los listados; pantalla para revisar/editar en bloque qué
  proveedores están marcados como no-seguidos, en vez de tener que
  entrar ficha por ficha.

## 2026-08-06 09:45

### [Control Pedidos] v12.29.58 — Fix real: el panel de Alertas nunca reflejaba los correos automáticos como enviados
- Continuación directa de v12.29.56, confirmado con un correo real
  recibido por el usuario (pedido 694, aviso de firma pendiente): el
  correo salió correctamente, pero la pantalla seguía mostrando "Sin
  notificar".
- Causa: `ultima_notif_email` (subconsulta de `PEDIDO_SELECT_STATS`
  que decide si la columna "Notificación" del panel de Alertas dice
  "Notificado" o "Sin notificar") solo miraba `emails_log` — la tabla
  de envíos MANUALES (botón "Notificar"/"Re-notificar"). Todos los
  correos automáticos (reclamación al proveedor, aviso de firma
  pendiente, aviso de cotización sin proveedor) se encolan y
  despachan vía `emails_sistema_pendientes`, una tabla distinta que
  esta subconsulta nunca consultaba. Bug sistemático, no solo del
  caso reportado — visible también en la fila 723 de la propia
  captura del usuario, con "🤖 Reclamado auto hace hoy" y "⛔ Sin
  notificar" a la vez, contradictorio a simple vista.
- Corregido: `PEDIDO_SELECT_STATS` combina ahora ambas fuentes con
  `GREATEST()` entre `emails_log.creado_en` (manual) y
  `emails_sistema_pendientes.enviado_en` (automático, solo filas con
  `enviado=TRUE` — el momento real de envío, no el de encolado).
- `README.md` actualizado a la versión actual (preferencia del
  usuario: mantenerlo siempre al día junto con el `CHANGELOG.md`).
  No existe `test_flujo.py` en este proyecto — nada que actualizar
  ahí.
- `app.py` compila sin errores. Badge de versión del sidebar
  actualizado a "V 12.29.58"; entrada añadida en `CHANGELOG.md`.

## 2026-08-06 09:15

### [Control Pedidos] v12.29.56 — Telegram bloqueado por el usuario: dejar de reintentar
- Continuación directa de v12.29.54, confirmado con log real de Render:
  el pedido 13513 fallaba siempre con `HTTP 403: {"error_code":403,
  "description":"Forbidden: bot was blocked by the user"}` — la persona
  destinataria bloqueó el bot en su Telegram. Reintentar cada día
  (comportamiento nuevo de v12.29.54) tampoco lo iba a arreglar — a
  petición del usuario, se da por terminado en vez de seguir
  intentándolo indefinidamente.
- `_send_telegram()` detecta errores 400/403 de Telegram permanentes
  (bot bloqueado, cuenta desactivada, chat inexistente — por texto de
  la `description`, Telegram no da un código específico) y devuelve
  un nuevo flag `permanente: True`, distinto de un fallo transitorio
  (timeout, 5xx) que sí debe seguir reintentándose al día siguiente.
- Los 4 puntos que registran el resultado en `whatsapp_log`
  (`telegram_estado`, `telegram_auto` en sus 2 variantes,
  `telegram_techo`) tratan ahora `ok=True OR permanente=True` como
  "hecho" — un bot bloqueado deja de generar un intento fallido cada
  día sin tocar nada más.
- De paso, se investigó a fondo (a petición del usuario) el problema
  paralelo del correo automático que "no está saliendo" para el mismo
  pedido — **sin encontrar ningún bug**: el log confirma que el aviso
  sí se encoló correctamente
  (`[AVISO-FIRMA-AUTO] Pedido 13513 — aviso de firma pendiente
  encolado`); esta app no tiene SMTP propio, el envío real depende de
  que alguien tenga la aplicación abierta en el navegador (se
  despacha vía EmailJS cada 5 min mientras haya sesión activa, tanto
  para admin como para compras). Ya existe además
  `_job_recordar_emails_sistema_pendientes()`, que manda un Telegram
  de recordatorio si un email lleva más de 10 min en cola sin
  nadie que lo despache (07:00-21:00). Comportamiento esperado del
  diseño, no un fallo — pendiente de que el usuario confirme si tuvo
  la app abierta desde que se generó el aviso esta mañana.
- `app.py` compila sin errores. Badge de versión del sidebar
  actualizado a "V 12.29.56"; entrada añadida en `CHANGELOG.md`.

## 2026-08-06 08:30

### [Control Pedidos] v12.29.54 — Fix: un envío fallido bloqueaba las notificaciones automáticas para siempre
- Reportado: pedidos con 50-65 días sin firma/cotización seguían en
  "Sin notificar" pese al tiempo transcurrido, mientras otros del
  mismo hotel sí se notificaban con normalidad. Diagnosticado en
  varias rondas de logs de Render (`RECLAMACION-DEBUG` y
  `[SCHEDULER]`) junto con el usuario.
- Causa real, confirmada en el código: `_nunca_notificado()` y
  `_ya_notificado_hoy()` contaban cualquier fila en `whatsapp_log`,
  tuviera o no éxito (`enviado=0` también contaba). Si el primer
  intento de Telegram fallaba (p. ej. sin destinatarios configurados
  para ese hotel en el evento "alerta_pedido_hotel", Admin → Config.
  Avisos), igual quedaba registrada una fila, y el sistema daba por
  "ya intentado" un envío que nunca llegó a nadie — bloqueando
  cualquier reintento para siempre. La pantalla de Alertas sí
  distinguía bien éxito de fallo, por eso seguía mostrando
  correctamente "Sin notificar" mientras el sistema, por dentro, ya
  había dejado de intentarlo.
- Corregido con cuidado de no crear un problema nuevo:
  `_nunca_notificado()` ahora exige `enviado=1` — un fallo deja de
  contar como "hecho para siempre". `_ya_notificado_hoy()` se deja a
  propósito SIN ese filtro, para seguir frenando reintentos cada
  minuto (el job corre cada minuto) si algo sigue fallando dentro del
  mismo día. Resultado: un pedido que falla se reintenta una vez al
  día, no 1440 veces, hasta que se resuelva la causa de fondo.
- Mismo patrón revisado en `_ya_reclamado_hoy_manual()` — se probó el
  mismo fix y se revirtió a propósito por la misma razón (evitar
  spam intradía); solo queda el fix en `_nunca_notificado()`.
- Pendiente de confirmar por el usuario: revisar en Admin → Config.
  Avisos los destinatarios configurados para "alerta_pedido_hotel" en
  el hotel GY, ya que es la explicación más probable (aunque no
  confirmada por falta de retención de logs tan atrás en Render) del
  fallo original del primer intento.
- `app.py` compila sin errores. Badge de versión del sidebar
  actualizado a "V 12.29.54"; entrada añadida en `CHANGELOG.md`.

## 2026-08-05

### [Control Pedidos] v12.29.53 — Fecha de entrega prevista también visible en la lista de Pedidos (no solo en Alertas)
- Petición: el usuario observó que bajo "F. Tramitación" algunos
  pedidos muestran una fecha de entrega estimada y otros no, y
  planteó la hipótesis de que dependía de si el criterio era "días de
  plazo" o "fecha prevista" del proveedor.
- Investigación: revisando `_resolver_fecha_entrega_prevista` (`app.py`)
  y su uso en `_clasificar_alertas`, se confirmó que el campo
  `fecha_entrega_prevista` se rellena igual sin importar el origen del
  dato (prioridad: fecha específica del proveedor → plazo en días).
  El motivo real de la diferencia entre las dos capturas era otro: esa
  fecha solo se pintaba en la tabla de **Alertas**
  (`_renderAlertasTabla`), nunca en la lista de **Pedidos**
  (`renderPedidosTable`) — y además Alertas solo muestra pedidos que
  ese día generan alerta (con el fix v12.29.52 recién aplicado, un
  pedido con fecha de entrega aún lejana puede no aparecer ahí en
  absoluto). El usuario confirmó y pidió ver la misma información en
  ambas pantallas.
- Corrección (`templates/index.html`):
  - Nueva función `_fechaEntregaPrevistaCliente(p)`: calcula en
    cliente la fecha de entrega prevista con la misma prioridad que
    el backend — 1) `fecha_entrega_especifica` si el proveedor dio un
    día concreto; 2) `fecha_tramitacion + plazo_entrega_dias` si hay
    plazo informado; 3) nada si no hay ninguno de los dos. No hizo
    falta tocar el backend: `/api/pedidos` ya devuelve
    `plazo_entrega_dias` y `fecha_entrega_especifica` en cada pedido
    (`p.*` de `PEDIDO_SELECT`).
  - `renderPedidosTable()`: la celda de F. Tramitación añade ahora,
    cuando aplica, la misma línea "📅 fecha" (mismo estilo/tooltip)
    que ya existía en Alertas — visible para cualquier pedido con
    fecha específica o plazo informados, sin depender de si hoy
    genera alerta.
- Verificado: los bloques `<script>` de `templates/index.html` pasan
  `node --check` sin errores tras el cambio. Badge de versión del
  sidebar actualizado a "V 12.29.53"; entrada añadida en
  `CHANGELOG.md`; `README.md` sincronizado (solo el número de
  versión). `app.py` no se ha tocado en esta entrega.

### [Control Pedidos] v12.29.52 — Fix crítico: pedidos con fecha de entrega específica todavía lejana se reclamaban al proveedor por el criterio equivocado
- Reportado con capturas: el pedido 692 (GY, CASA DELFIN SA), con
  `Fecha de entrega específica = 27/08/2026` indicada por el propio
  proveedor y grabada en el pedido, apareció en Alertas como 🔴
  URGENTE ("37 días") con "🚚 Reclamado auto hoy" — pese a que
  faltaban 22 días para la fecha que el proveedor había comprometido.
  Pregunta del usuario: "¿qué criterio está siguiendo?".
- Causa raíz (`app.py`): hay dos vías para calcular la alerta de un
  pedido en ENVIADO AL PROVEEDOR/ENTREGA PARCIAL — (1) vía plazo
  (`_alertas_plazo_entrega`, basada en la fecha de entrega
  específica o `fecha_tramitacion + plazo_entrega_dias`, que solo
  devuelve algo en días concretos: N días antes, el día exacto, o
  cada M días después de vencer) y (2) vía estándar
  (`_build_umbrales`, cuenta días desde `fecha_tramitacion` sin mirar
  ninguna fecha de entrega). Tanto en el job diario
  (`_job_alertas_diarias_inner`) como en el endpoint que alimenta la
  pantalla de Alertas (`_clasificar_alertas`, usado por
  `/api/stats`), el código decidía la vía con
  `if info_plazo: ... else: <vía estándar>` — pero `None` de la vía 1
  significa dos cosas distintas que el código no distinguía: "sin
  plazo/fecha informados" (correcto caer a la vía estándar) o "con
  fecha informada, pero hoy no toca aviso por esa vía" (debería ser
  simplemente "sin alerta hoy", nunca caer a la vía estándar). En el
  segundo caso caía igualmente a la vía estándar, que solo mira días
  desde `fecha_tramitacion` (37 días) e ignora la fecha de entrega
  concreta y todavía vigente — de ahí la reclamación automática
  injustificada.
- Ya existía una función `_debe_usar_logica_plazo(pedido)` escrita
  exactamente para resolver esta ambigüedad (pedido con plazo/fecha
  informados Y función activada → usar solo la vía plazo), pero
  **nunca se llamaba desde ningún sitio** — quedó huérfana desde que
  se creó.
- Corrección: en `_job_alertas_diarias_inner` y en `_clasificar_alertas`
  se usa ahora `_debe_usar_logica_plazo(p)` para decidir de entrada si
  el pedido "vive" en la vía de plazo. Si es así: se evalúa
  `_alertas_plazo_entrega()`; si hoy no toca aviso por esa vía, se
  omite sin más (sin alerta, sin reclamación, sin caer a la vía
  estándar). La vía estándar solo se aplica ahora a pedidos sin
  ninguna fecha/plazo de entrega informado, o con la función
  desactivada globalmente (`activar_uso_plazo_entrega = 0`).
- **Nota importante:** el fix evita que se repita a partir de ahora,
  pero la reclamación automática de hoy para el pedido 692 ya había
  salido antes de aplicar la corrección — no se puede deshacer un
  correo ya enviado. Si hace falta, avisar manualmente al proveedor
  de que fue un error del sistema.
- `app.py` compila sin errores (`python3 -m py_compile`). Badge de
  versión del sidebar actualizado a "V 12.29.52"; entrada añadida en
  `CHANGELOG.md`; `README.md` sincronizado (solo el número de
  versión).

## 2026-08-04

### [Ecosistema] Reunificación de historiales — nota de fusión
- Detectado (2026-08-05): ambas copias del historial se habían
  desincronizado en direcciones distintas — a esta copia (Control de
  Pedidos) le faltaban las 3 entradas de Organizador de esta misma
  fecha (v4.16.3/.4/.5); a la copia de Organizador le faltaban 34
  entradas de Control de Pedidos (v12.29.4 a v12.29.53). Se fusionan
  aquí las 3 entradas de Organizador que faltaban — el orden exacto
  entre ellas y las entradas de Control de Pedidos de este mismo día
  no se ha podido reconstruir con precisión de minutos (ninguna de las
  dos copias guardaba hora, solo fecha), así que quedan agrupadas
  juntas en vez de intercaladas una a una.

### [Organizador] v4.16.5 (`update_service.py`) — Misma gracia de 5 min aplicada al check de actualizaciones de GitHub
- Detectado al revisar el fix anterior (v4.16.4): el check de
  actualizaciones contra GitHub (`_check_update_github()`,
  `app/services/update_service.py`) tenía el mismo síntoma que el
  bridge de Control de Pedidos, pero SIN NINGÚN límite — cada fallo
  (HTTPError, URLError, excepción inesperada) mostraba el diálogo
  "⚠️ Error al comprobar actualizaciones" al momento y se reprogramaba
  a los 30 min sin más, sin tope diario. Con GitHub inalcanzable un
  rato (proxy, incidencia, corte puntual), el diálogo podía repetirse
  cada 30 minutos indefinidamente.
- Cambio: `_check_update_github()` gana el parámetro
  `_es_reintento_gracia` (default `False`). El primer fallo llama a
  `_conceder_gracia_update()`, que programa un único reintento
  silencioso a los 5 minutos del mismo check en vez de avisar. Si el
  reintento tiene éxito, se descarta en silencio (log únicamente); si
  también falla, se muestra el diálogo con el error de ese segundo
  intento, y el propio reintento retoma el ciclo normal de 30 min al
  reprogramarse él solo.
- `APP_VERSION` → "v4.16.5" en `main_agenda.py`; `MyAppVersion` →
  "4.16.5" en `OrganizadorPrincess_Setup.iss`; entrada añadida en
  `release_notes/release_notes.md` y `release_notes_actual.txt`.

### [Organizador] v4.16.4 (`pedidos_agenda_bridge.py` v4.9) — Gracia de 5 min antes de avisar de un corte de conexión
- Petición: el diálogo "⚠️ Error de conexión con Control de Pedidos"
  saltaba con el primer fallo de red (login, `/api/bridge/alertas` o
  `/api/bridge/notificaciones`), aunque fuera un corte puntual que se
  resuelve solo (wifi, cold start de Render, una petición perdida).
- Cambio: ningún fallo de conexión abre el diálogo al momento. La
  primera vez que falla cualquiera de esas tres operaciones se llama
  a la nueva `_reportar_fallo_conexion()`, que NO avisa — programa un
  único reintento a los 5 minutos (`_GRACIA_RECONEXION_SEGUNDOS`) de
  la misma operación que falló. Si el reintento tiene éxito, el
  fallo se descarta en silencio (queda constancia en
  `bridge_errors.log`). Si el reintento también falla, entonces sí se
  abre el diálogo, con el error de ese segundo intento (puede no
  coincidir con el del primero). Varios fallos casi a la vez (p. ej.
  login y alertas juntos) no programan un reintento cada uno — todos
  son síntoma del mismo corte, basta con uno (`_gracia_en_curso`).
- `login()` se divide en `_intentar_login()` (silenciosa, devuelve
  `(ok, titulo, cuerpo)`) + `login()` (delega en
  `_reportar_fallo_conexion()` si falla), para reutilizar el mismo
  intento en la llamada normal y en el reintento a los 5 min.
  `_sincronizar_alertas()` y `_procesar_push()` siguen el mismo patrón
  con closures locales.
- Sin cambios en el límite de "1 diálogo por tipo de error y día" de
  `_mostrar_error_bridge()` (v4.3) — la gracia de 5 min ocurre antes
  de llegar a ese punto, no lo sustituye.
- `APP_VERSION` actualizado a "v4.16.4" en `main_agenda.py` y
  `MyAppVersion` a "4.16.4" en `OrganizadorPrincess_Setup.iss`; entrada
  añadida en `release_notes/release_notes.md` y
  `release_notes/release_notes_actual.txt`.

### [Organizador + Control Pedidos] v4.16.3 / v12.29.46 — Prueba: popup entregado una única vez (dedup en servidor)
- Motivo: comprador de INSIRE reportó el mismo popup repitiéndose
  "continuamente" en el mismo día.
- Causa probable: el dedup de repetición de popups vivía en memoria de
  Organizador Princess (`_estado_popups`), se perdía al reiniciar la
  app y volvía a mostrar avisos ya vistos.
- Prueba: el dedup se mueve a Control de Pedidos (tabla
  `bridge_popup_visto`, persistente). `/api/bridge/alertas` ahora solo
  entrega cada aviso una vez por usuario/pedido/nivel, para siempre —
  si la app está cerrada cuando el pedido entra en alerta, se entrega
  en cuanto reconecte, pero solo esa vez, sin reintentos posteriores.
  Detalle completo en `CHANGELOG.md` (Control Pedidos, v12.29.46) y en
  el docstring de `_sincronizar_alertas()` (Organizador, v4.8).

### [Control Pedidos] v12.29.51 — Fix: contador "N pedidos" no se actualizaba a 0 cuando la búsqueda no encontraba resultados
- Reportado: "en la pantalla de pedidos así como en la de alertas, la
  búsqueda por código pedido no funciona", con capturas mostrando una
  búsqueda por `4130` sin resultados ("No hay pedidos que mostrar")
  pero con el contador inferior aún en "721 pedidos".
- Investigación: se repasó `loadPedidos()`/backend `get_pedidos()`
  (búsqueda `ILIKE` sobre `pedido_num`, `proveedor.nombre`,
  `observaciones`, `hotel.codigo`) y `aplicarFiltrosAlertas()`
  (filtro cliente sobre las alertas activas). Ambos funcionan
  correctamente por subcadena. Al confirmar con el usuario el dato
  exacto, se aclaró que `4130` era un error de tecleo por `40130` — la
  búsqueda en sí no tenía ningún bug de fondo.
- Bug real detectado durante la investigación (`templates/index.html`,
  `loadPedidos()`): con 0 resultados, `renderPagination()` —única
  función que actualiza `#page-info-text` ("N pedidos") y
  `#pagination`— no se llegaba a invocar, así que el contador y la
  paginación se quedaban con los valores de la carga/búsqueda
  anterior, en vez de reflejar que no hay resultados. Esto reforzaba
  la sensación de que "la búsqueda no funciona" aunque el filtrado en
  sí fuera correcto.
- Corrección: en la rama de 0 resultados de `loadPedidos()`, se fija
  `#page-info-text` a `"0 pedidos"` y se vacía `#pagination`
  (`innerHTML = ''`), igual que ocurriría con cualquier búsqueda sin
  coincidencias.
- Solo se entrega este bug confirmado — no se ha tocado la lógica de
  búsqueda (backend `ILIKE` ni filtro cliente de Alertas), que ya
  funcionaba como se esperaba.
- Verificado: los 8 bloques `<script>` de `templates/index.html`
  pasan `node --check` sin errores tras el cambio. Badge de versión
  del sidebar actualizado a "V 12.29.51"; entrada añadida en
  `CHANGELOG.md`; `README.md` sincronizado (solo el número de
  versión). `app.py` no se ha tocado — el cambio es exclusivamente de
  frontend.

### [Control Pedidos] v12.29.50 — Rol hotel sin acceso visible a proveedores + avisos de validación del modal de Pedidos con el patrón visual de "Acceso restringido"
- **Petición 1 (confirmación de permisos):** el usuario confirmó que
  el rol `hotel` no debe poder crear ni editar proveedores (solo
  `admin` y `compras`, ver v12.29.49) y pidió "evitar los errores
  siempre" — es decir, no mostrar en el frontend acciones que el
  usuario no puede completar, aunque el backend ya las bloquee.
  - Causa: el backend ya devolvía 403 para `hotel` en
    `create_proveedor`/`update_proveedor` (desde v12.29.49), pero el
    botón "✏ Editar" seguía visible en la lista de Proveedores para
    ese rol, así que `hotel` se topaba con el mismo síntoma original
    (pulsar Guardar y que "no pase nada").
  - Corrección (`templates/index.html`):
    - Template de fila de la lista de Proveedores: para
      `G.rol === 'hotel'` el botón "✏ Editar" se sustituye por un
      indicador "🔒 Solo lectura" (con tooltip). Para `admin` y
      `compras` no cambia nada.
    - `saveProveedor()`: guardia defensiva al inicio — si
      `G.rol === 'hotel'`, corta la ejecución y muestra el aviso
      visual nuevo (ver punto 2) en vez de dejar que la petición
      llegue al backend y falle en silencio. Es un cinturón de
      seguridad adicional al botón oculto, por si `saveProveedor()`
      se invocara desde otro punto en el futuro.
- **Petición 2 (más visual):** en la ventana de crear/editar pedido,
  cuando falta algo obligatorio y da error, se pidió que el aviso se
  vea "siguiendo el mismo patrón" que el aviso de "Acceso
  restringido" del sidebar (tarjeta oscura centrada con icono/título),
  en vez del pequeño toast rojo de esquina — "es más visual".
  - Corrección (`templates/index.html`):
    - Nuevo componente `#form-alert-toast` (HTML + CSS): mismo patrón
      que `#sb-access-toast` (tarjeta `rgba(26,38,65,.97)` centrada,
      `position:fixed;bottom:80px;left:50%`), con borde rojo (en vez
      de dorado) y título/icono configurables por llamada; admite una
      segunda línea de detalle (útil para listas de campos que
      faltan, p.ej. "Nº Pedido" + "PDF" a la vez).
    - Nueva función `showFormAlert(mensaje, { title, detail,
      duracion })` que rellena y muestra el componente (auto-oculta a
      los 6 s por defecto).
    - `savePedido()`: los 10 `toast(msg,'error',...)` de validación y
      error de la función pasan a `showFormAlert(...)` — modo hotel
      (cancelar no permitido, error al guardar albarán), falta hotel,
      nota obligatoria (CANCELADO / denegar DG), proveedor sin
      asignar, proveedor sin email, Nº Pedido/PDF faltante (con la
      lista en la línea de detalle), familia/importe del techo, error
      de negocio del backend al crear/actualizar, y error de conexión
      del `catch`. Los mensajes de éxito (`'success'`) y el aviso de
      techo superado (`'warning'`) se mantienen como el toast pequeño
      de siempre — el patrón nuevo es solo para errores/validación en
      ese modal, según lo pedido.
- Verificación: los 8 bloques `<script>` de `templates/index.html`
  pasan `node --check` sin errores de sintaxis tras los cambios.
  Badge de versión del sidebar actualizado a "V 12.29.50"; entrada
  añadida en `CHANGELOG.md`; `README.md` sincronizado (solo el número
  de versión). `app.py` no se ha tocado en esta entrega — ambos
  cambios eran exclusivamente de frontend.

### [Control Pedidos] v12.29.49 — Fix: comprador no podía crear ni editar proveedores (botón Guardar no hacía nada)
- Petición del usuario: "los compradores no pueden editar la ficha de
  proveedor y si deberían poder, cuando se pulsa guardar no hace
  nada". Confirmado a continuación que también debían poder **crear**
  proveedores nuevos, no solo editar los existentes.
- **Nota de versión / por qué v12.29.49 y no v12.29.48:** este fix se
  desarrolló primero contra un snapshot (`control_pedidos_v12_29_47.zip`)
  y se numeró en su momento como v12.29.48. Al recibir después el zip
  de la versión realmente desplegada (`control_pedidos_v12_29_48.zip`),
  esta ya incluía **otro** fix distinto con ese mismo número (el de
  "familia repetida", justo debajo) — es decir, el número v12.29.48 se
  usó dos veces en paralelo, en dos sesiones distintas, para dos
  cambios distintos. Para no pisar la entrada real ni el código ya
  desplegado, este fix de proveedores se ha renumerado a **v12.29.49**
  y se ha aplicado directamente sobre la base real subida por el
  usuario (que ya contenía el fix de familia repetida intacto).
  **Lección para próximas entregas:** antes de numerar una versión
  nueva, confirmar con el usuario cuál es el último número
  realmente desplegado (no asumir que el último zip que nos pasaron
  es el que sigue en producción sin cambios adicionales).
- Causa encontrada: `POST /api/proveedores` y
  `PUT /api/proveedores/<id>` (`app.py`) estaban protegidas con
  `@admin_required` (solo `rol == "admin"`), así que un comprador
  recibía `403 Solo administradores` al guardar. El frontend
  (`saveProveedor()`, `templates/index.html`) no captura la excepción
  que lanza el helper `api()` ante un error no controlado como este
  403, así que el fallo era silencioso para el usuario.
- Corrección (`app.py`): `create_proveedor()` y `update_proveedor()`
  pasan de `@admin_required` a `@login_required` + comprobación
  explícita `session.get("rol") not in ("admin", "compras")` → 403,
  mismo patrón ya usado en `get_pedidos_eliminados()`. Ahora admin y
  comprador pueden crear/editar proveedores; el rol `hotel` sigue sin
  poder (solo consulta, sin cambios).
- Se han dejado **sin tocar**, restringidas a admin: `delete_proveedor()`
  y la importación masiva por Excel (`importar_proveedores`).
- Corrección (`templates/index.html`): `_refreshProvAdminControls()`
  ahora muestra el botón "+ Nuevo proveedor" de la vista Proveedores
  también para `rol === 'compras'` (antes solo admin). El botón
  "Importar Excel" sigue solo para admin.
- `app.py` compila sin errores (`python3 -m py_compile`). Badge de
  versión del sidebar actualizado a "V 12.29.49"; entrada añadida en
  `CHANGELOG.md`; `README.md` sincronizado (solo el número de
  versión).

### [Control Pedidos] v12.29.48 — Fix: aviso "familia repetida" saltaba con el primer pedido, sin duplicado real
- Reportado: el comprador seguía recibiendo el aviso 🔴 "Familia/Partida
  REPETIDA" de forma constante, pese a que en el hotel no existía
  ningún pedido duplicado de esa familia — solo un único pedido sujeto
  a techo.
- Causa raíz: `_job_familia_repetida_inner()` (`app.py`) contaba TODOS
  los pedidos de la familia sin excluir ninguno, y comparaba con
  `HAVING COUNT(*) >= techo_max_pedidos_familia`. Con el valor por
  defecto de `techo_max_pedidos_familia` (= 1), la condición ejecutada
  era en la práctica `COUNT(*) >= 1`: el primer y único pedido de
  cualquier familia ya la marcaba como "repetida".
- Inconsistencia detectada frente a `_check_techo()` (la función que
  bloquea el paso a ENVIADO AL PROVEEDOR): esa función excluye el
  propio pedido del recuento antes de comparar, así que solo bloquea
  cuando ya existía otro pedido antes — comportamiento correcto. El
  job de aviso diario no tenía esa exclusión.
- Corrección: en la consulta SQL del job, `HAVING COUNT(*) >= %s` pasa
  a `HAVING COUNT(*) > %s`. El job ahora solo alerta cuando el número
  de pedidos de la familia supera el máximo configurado (repetición
  real), no cuando simplemente lo alcanza con el primer pedido.
- Sin cambios en `_check_techo()` (ya era correcta) ni en
  `techo_max_pedidos_familia` (sigue en 1 por defecto — el límite de
  negocio no cambia, solo se corrige cuándo se considera "repetido").
- Badge de versión del sidebar actualizado a "V 12.29.48"; entrada
  añadida en `CHANGELOG.md`; `README.md` sincronizado con la versión
  (estaba desactualizado desde v12.29.44).

### [Control Pedidos] v12.29.44 — Simplificación del registro de entrada DALI/SAP: ENTREGADO + CANCELADO
- Petición: simplificar el paso de "Nº Entrada DALI / SAP" — de tres
  checkboxes (ENTREGA PARCIAL, ENTREGA TOTAL, CANCELADO) a solo dos
  (ENTREGADO, CANCELADO). Dentro de "entrega" se mantiene igual: si es
  total se marca la entrada como final y el estado pasa a ENTREGADO; si
  es parcial se pueden añadir tantas entradas como sean necesarias, y
  la última se marca como final para cerrar (ENTREGADO) — mientras
  tanto el estado real sigue siendo ENTREGA PARCIAL.
- Solo frontend (`templates/index.html`): "ENTREGA PARCIAL" y "ENTREGA
  TOTAL" se fusionan en un único checkbox `chk-entregado` ("ENTREGADO"),
  que abre la misma lista editable de entradas de antes.
- Eliminado el mini-modal de "ENTREGA TOTAL" (`modal-albaran-total`,
  `abrirModalAlbaranTotal()`, `cerrarModalAlbaranTotal()`) — ya no hace
  falta: para una entrega total basta con añadir una entrada y marcarla
  como "Entrada final".
- El checkbox "Entrada final" por fila (ya existente) sigue decidiendo
  el estado real: marcado → `ENTREGADO`, sin marcar → `ENTREGA
  PARCIAL`. Solo una entrada final a la vez, igual que antes.
- `initAlbaranSection()`, `onAlbaranCheckChange()` y
  `_onAlbaranFinalChange()` actualizados para el checkbox único, sin
  cambios de comportamiento en la lista de entradas en sí.
- Sin cambios en `app.py` ni en los estados internos (`ESTADOS_VALIDOS`
  en `models.py`) — es puramente una simplificación de la interfaz de
  captura, el backend sigue guardando/validando `ENTREGA PARCIAL` /
  `ENTREGADO` / `CANCELADO` exactamente igual.
- Badge de versión del sidebar actualizado a "V 12.29.44"; entrada
  añadida en `CHANGELOG.md`; `README.md` sincronizado con la versión
  (estaba desactualizado desde v12.29.43).

## 2026-08-03

### [Control Pedidos] v12.29.43 — Nueva funcionalidad: alarma y listado adjunto cuando un pedido está sujeto a techo de gastos
- Solicitado: que al activar "sujeto al techo de gasto mensual" en un
  pedido salte alguna alarma indicando que la autorización (firma) está
  sujeta a techo de gastos, y que se pueda adjuntar algún listado de
  apoyo a la solicitud de firma.
- Frontend: al marcar la casilla de techo en la ficha del pedido,
  aparece un aviso destacado junto a un botón para adjuntar uno o
  varios documentos de apoyo ("Adjuntar listado a la solicitud de
  firma"), nuevo tipo de adjunto `firma_techo_doc` (PDF/Word/Excel/
  correo, mismas validaciones que "Nº Presupuesto"). No visible para el
  rol Hotel.
- Backend: `_email_template_pendiente_firma()` (recordatorio de pedido
  pendiente de firma, automático y manual) incluye ahora un aviso
  destacado si el pedido es `sujeto_techo`, con familia e importe, y
  menciona si hay documentos de apoyo adjuntos. `firma_techo_doc`
  registrado en `TIPOS_ADJUNTO_VALIDOS`. `_JOB_PEDIDO_SQL` y
  `PEDIDO_SELECT_ALERTA` amplían sus columnas con `sujeto_techo`,
  `familia_id`, `importe` y `familia_nombre` (nuevo `LEFT JOIN
  familias`).
- `app.py` compila sin errores. Badge de versión del sidebar
  actualizado a "V 12.29.43"; entrada añadida en `CHANGELOG.md`.
  Archivos modificados: `app.py`, `templates/index.html`.

### [Control Pedidos] v12.29.42 — Corrección: hotel de pruebas ("PR") también visible para el usuario dedicado
- Corrección sobre v12.29.41: el hotel `PR` no debía quedar restringido
  solo a admin, sino visible también para el usuario dedicado a estas
  pruebas (username `usuario prueba`), sea cual sea su rol real
  (Compras en este caso) — admin sigue viéndolo igual.
- Nueva constante `USERNAME_HOTEL_PRUEBAS = "usuario prueba"` y helper
  `_puede_ver_hotel_pruebas()` en `app.py`, que sustituye las
  comprobaciones de `rol == "admin"` de v12.29.41 en `/api/maestros`,
  `/api/pedidos` (listado/detalle/crear/editar), `/api/stats`,
  `/api/dashboard/resumen`, `/api/techo/resumen[-historico]`,
  `/api/exportar` y `POST /api/importar`.
- Los jobs automáticos (familias repetidas, techo urgente, techo
  mensual) vuelven a incluir `PR` en su recorrido de hoteles: sus
  destinatarios ya se resuelven por hotel vía `_resolver_notificacion()`,
  así que solo llega a quien esté configurado para ese hotel — excluirlo
  del todo habría impedido probar el pipeline de alertas.
- `app.py` compila sin errores. Badge de versión del sidebar actualizado
  a "V 12.29.42"; entrada añadida en `CHANGELOG.md`.

## 2026-08-03

### [Control Pedidos] v12.29.41 — Hotel de pruebas ("PR") restringido solo al rol admin
- Petición: el hotel de pruebas (código `PR`, creado en v12.29.32) solo
  debe estar disponible para el rol admin; compras y hotel no deben
  verlo ni interactuar con sus pedidos en ningún sitio de la app.
- `/api/maestros` (dropdown de hoteles usado en toda la app): excluye
  `PR` para compras; refuerzo también en la rama del rol hotel.
- `/api/pedidos` (listado) y `/api/pedidos/<id>` (detalle): excluyen/
  bloquean `PR` para cualquier rol que no sea admin.
- `POST /api/pedidos` y `PUT /api/pedidos/<id>`: rechazan crear o
  reasignar un pedido al hotel `PR` si el usuario no es admin.
- `/api/stats`, `/api/dashboard/resumen`, `/api/techo/resumen` y
  `/api/techo/resumen-historico`: excluyen `PR` de conteos, gráficos,
  alertas y rankings para compras.
- `/api/exportar` (Excel) y `POST /api/importar` (importación masiva):
  excluyen `PR` para compras/hotel.
- Jobs automáticos (familias repetidas, techo urgente, techo mensual):
  excluyen `PR` del recorrido de hoteles activos, para no generar
  notificaciones reales sobre este hotel de pruebas.
- Paneles exclusivamente admin (compradores por hotel, configuración de
  avisos, importación/reset, integridad operativa) sin cambios — siguen
  mostrando `PR`, como corresponde a su uso interno de admin.
- Nueva constante `HOTEL_CODIGO_PRUEBAS = "PR"` y helper
  `_es_hotel_pruebas_id()` en `app.py`.
- `app.py` compila sin errores. Badge de versión del sidebar actualizado
  a "V 12.29.41"; entrada añadida en `CHANGELOG.md`.

## 2026-08-03

### [Control Pedidos] v12.29.40 — Logo nítido en emails + motivo real en avisos de CANCELADO/DENEGADO
- Petición: el logo de la cabecera de los correos se veía distorsionado/
  borroso, y los correos de cancelación (o denegación por Dirección
  General) no indicaban el motivo ni la trazabilidad de quién hizo el
  cambio, solo el campo "Observaciones" del pedido (casi siempre vacío).
- Logo borroso: causa era el escalado CSS de `logo-sidebar.png`
  (787×731 px original) a 56/64/40 px — mala calidad de downscale en
  clientes de correo (especialmente Outlook). Generados
  `static/logo-sidebar-email.png` (121×112) y
  `static/logo-sidebar-email-64.png` (138×128), versiones retina 2x
  pre-escaladas con remuestreo Lanczos. `_email_header_html()` y los 6
  bloques de cabecera sueltos (correos de solicitud de acceso)
  actualizados para usarlas, con `width`/`height` explícitos en el
  `<img>`.
- Motivo/trazabilidad: el motivo real vive en `historial_estados.nota`
  en el momento de la transición de estado, no en `pedido.observaciones`
  — por eso no salía en el correo aunque el usuario lo hubiera escrito.
  `enviar_emails_estado()` ahora consulta `historial_estados` por
  `pedido_id` + `estado_nuevo` y añade "Motivo de la cancelación" /
  "Motivo de la denegación" al correo (HTML y texto plano), con
  fallback a `observaciones`. La fila "Realizado por" ya existente
  cubre quién hizo el cambio.
- `DENEGADO POR DIRECCION GENERAL` añadido a `ESTADOS_EMAIL_INTERNO`
  (`models.py`) — antes no se enviaba ningún correo interno para ese
  estado.
- `app.py` y `models.py` compilan sin errores. Badge de versión del
  sidebar actualizado a "V 12.29.40"; entrada añadida en
  `CHANGELOG.md`.

## 2026-08-02

## 2026-08-02

### [Control Pedidos] v12.29.39 — Auditoría fin de semana en jobs automáticos: techo mensual se había quedado fuera
- Petición: revisar todos los puntos de envío de Telegram/popup para que
  cumplan el mismo criterio de fin de semana de v12.29.38.
- Encontrado: `_job_alertas_techo_mensual_inner()` (semáforo mensual a
  compradores) corría los 7 días — inconsistente con sus dos jobs
  hermanos del rediseño de Techo de Gastos (techo urgente y familia
  repetida), que ya tenían el guardián lun-vie.
- Corregido: mismo guardián de fin de semana al inicio de la función +
  `day_of_week="mon-fri"` en el `scheduler.add_job` correspondiente.
- Revisados y dejados tal cual (event-driven, reacción inmediata a una
  acción real de un usuario, no jobs automáticos): cambio manual de
  estado de pedido, alerta al crear pedido sujeto a techo, solicitudes
  de acceso, copias de supervisión, y los 2 botones manuales "Enviar
  Telegram" del panel.
- Revisados y dejados sin tocar, a petición expresa del usuario: alerta
  de consumo Supabase (egress/tamaño BD) y alerta de integridad de BD —
  son avisos de infraestructura, no de negocio de pedidos; siguen
  avisando los 7 días de la semana.
- `app.py` compila sin errores. Badge de versión del sidebar
  actualizado a "V 12.29.39"; entrada añadida en `CHANGELOG.md` y
  versión actualizada en `README.md`.

### [Control Pedidos] v12.29.38 — Reclamación/aviso/Telegram/popup ya no salen en fin de semana
- Petición: la reclamación automática al proveedor, el aviso de firma
  pendiente, el Telegram a compradores y el popup de main_agenda
  (Organizador Princess) se enviaban también en sábado y domingo — se
  pidió retrasarlos al lunes sin tocar el conteo de días naturales ni
  el ciclo de reenvío.
- Corregido: nuevo guardián al inicio de `_job_alertas_diarias_inner()`
  — si es sábado o domingo (`ahora.weekday() >= 5`), el job no envía
  nada. Es el único punto donde salen los cuatro avisos (los dos
  correos y el Telegram+popup vía `_enviar_telegram_compradores` →
  `_encolar_bridge_notificacion`), así que un solo guardián cubre los
  tres canales sin duplicar lógica.
- También añadido `day_of_week="mon-fri"` al `scheduler.add_job` del
  job (`alertas_cada_minuto`), igual que ya tenían techo urgente y
  familia repetida — evita despertar el proceso en balde el fin de
  semana.
- Nada más cambia: `_dias_desde_fecha()` sigue en días naturales, y el
  ciclo de reenvío sigue basado en la fecha real del último aviso en
  `whatsapp_log` — al no haber envío en fin de semana, el recuento
  continúa con normalidad desde el último aviso real (viernes) hasta
  el lunes.
- Sin cambios en main_agenda: al no encolarse nada en
  `bridge_notificaciones` el fin de semana, el bridge no tiene nada que
  recoger ese día.
- `app.py` compila sin errores. Badge de versión del sidebar
  actualizado a "V 12.29.38"; entrada añadida en `CHANGELOG.md` y
  versión actualizada en `README.md`.

### [Control Pedidos] v12.29.37 — Seguridad: las contraseñas se guardaban en texto plano
- Hallazgo detectado al revisar `app.py` como referencia para el login
  de otro proyecto (DALI): tanto `/api/login` como el login usado por
  el bridge de Organizador Princess comparaban la contraseña recibida
  directamente contra la columna `password` de `usuarios` con `=` en el
  SQL, sin hash. Lo mismo al guardar una contraseña nueva: reset por
  token, alta automática tras solicitud aprobada, y alta/edición de
  usuario desde el panel de Admin — los 4 puntos guardaban texto plano.
- Corregido: las 4 escrituras pasan a usar `generate_password_hash`
  (werkzeug, ya viene con Flask) y los 2 logins pasan a comparar con
  `check_password_hash`, a través de una función común
  `_verifica_y_migra_password()`.
- Migración transparente: esa función detecta si la contraseña guardada
  sigue en texto plano (cuentas creadas antes de esta versión) y, si la
  comparación legacy coincide, la rehashea y sobreescribe en la BD en
  ese mismo login — sin forzar reset a nadie y sin ninguna ventana de
  usuarios bloqueados.
- El email de bienvenida con contraseña temporal sigue enviando la
  contraseña en claro al usuario nuevo, igual que antes; solo cambia lo
  que se guarda en la BD.
- `app.py` compila sin errores. Badge de versión del sidebar
  actualizado a "V 12.29.37"; entrada añadida en `CHANGELOG.md` y
  versión actualizada en `README.md`.
- **Verificado en producción (2026-08-02, ~16:38h):** primer login tras
  el despliegue (cuenta admin) devuelve `200` sin incidencias — la
  migración transparente a hash funcionó al primer intento, sin ningún
  401 ni reset forzado.
- **PENDIENTE — auditoría de contraseñas aún no migradas:** dar unos
  días (una semana natural, para cubrir a quien no entra todos los
  días) y luego correr en Supabase:
  ```sql
  SELECT id, username, nombre, email, rol, activo, ultimo_login
  FROM usuarios
  WHERE password NOT LIKE 'pbkdf2:%'
    AND password NOT LIKE 'scrypt:%'
  ORDER BY ultimo_login ASC NULLS FIRST;
  ```
  Cada usuario se migra solo a hash al hacer login (ver corrección de
  arriba), así que esta consulta antes de tiempo listaría a casi todo
  el mundo sin decir nada útil. Pasados unos días, lo que quede en el
  resultado son las cuentas que de verdad llevan tiempo sin entrar —
  esas son las candidatas a un reset manual desde Admin → Usuarios
  para cerrar la migración del todo.

### [Control Pedidos] v12.29.36 — Corrección real: login mostraba "Error de conexión" también con contraseña incorrecta
- Primero se confirmó, con logs de Render del arranque siguiente al
  despliegue de la v12.29.35, que la migración de `expediente_exceso`
  se ejecutó correctamente (`CREATE TABLE ejecutado` + `índices OK`) —
  el bug de "Techo de Gastos" queda resuelto.
- Reportado a continuación: el login seguía dando "Error de conexión".
  Revisando los logs de Render en el momento exacto del intento, el
  servidor respondía con normalidad: `POST /api/login` devolvía 401
  (no un fallo de red), la respuesta esperada cuando la contraseña no
  coincide, con el mensaje correcto `"Usuario o contraseña
  incorrectos"` ya incluido por el backend.
- Causa real: el `catch` de `doLogin()` en el frontend ignoraba por
  completo ese mensaje y mostraba siempre "Error de conexión" fuera
  cual fuera el motivo del fallo — así que una contraseña incorrecta
  se veía indistinguible de un problema real de conectividad.
- Corregido: el `catch` ahora recupera y muestra el detalle real
  devuelto por `api()` (p.ej. "Usuario o contraseña incorrectos"), y
  solo cae al genérico "Error de conexión" cuando de verdad no hay
  respuesta del servidor.
- `app.py` sin cambios en esta versión. Badge de versión del sidebar
  actualizado a "V 12.29.36"; entrada añadida en `CHANGELOG.md`.

### [Control Pedidos] v12.29.35 — Diagnóstico: la migración de expediente_exceso sigue sin aplicarse
- Tras desplegar la v12.29.33/34, `/api/techo/resumen` seguía dando
  `psycopg2.errors.UndefinedTable: relation "expediente_exceso" does
  not exist` (confirmado con logs de Render del proceso arrancado tras
  el despliegue nuevo, no del anterior).
- Se localizó en los logs `Auto-migración omitida: 0` justo después de
  `[MIGRACION] Hotel de pruebas 'PR' insertado` — exactamente donde se
  añadió el bloque de `expediente_exceso` en la v12.29.33. El mensaje
  `"0"` no aportaba ninguna pista real porque `_auto_migrate()` solo
  registraba `str(e)`, sin traceback.
- Cambio (solo diagnóstico, no corrige el fallo todavía):
  - El `except` general de `_auto_migrate()` ahora vuelca el traceback
    completo con `log.exception(...)`.
  - El bloque de `expediente_exceso` se envuelve en su propio
    `try/except`, con log detallado (`tipo=... repr=...`) antes de
    relanzar la excepción — para saber con certeza si el fallo está en
    el `CREATE TABLE` o en alguno de los `CREATE INDEX`.
- `app.py` compila sin errores. Badge de versión del sidebar
  actualizado a "V 12.29.35"; entrada añadida en `CHANGELOG.md`. La
  causa real y su corrección quedan pendientes de ver en los logs del
  próximo arranque.

### [Control Pedidos] v12.29.34 — Documentación: README general de la aplicación
- Añadido `README.md` en la raíz del proyecto: no existía ninguna
  documentación general del repositorio hasta ahora.
- Contenido: stack técnico, estructura de archivos, funcionalidades por
  vista (Pedidos, Alertas, Proveedores, Techo de gastos, Familias,
  Usuarios, Integridad, Config alertas/avisos, Restaurar backup), roles
  de usuario (admin/compras/hotel/user), explicación detallada de cómo
  funcionan las migraciones automáticas de base de datos
  (`_auto_migrate()` en `app.py`, que corre en cada arranque, frente a
  `SQL_STATEMENTS`/`init_db.py`, que solo corre a mano en el primer
  despliegue) — el punto exacto que causó los bugs reales de v12.29.32
  (hotel "PR") y v12.29.33 (tabla `expediente_exceso`), puesta en
  marcha local/producción, variables de entorno, y convenciones del
  proyecto.
- Cambio puramente documental, no afecta a `app.py`. Badge de versión
  del sidebar actualizado a "V 12.29.34"; entrada añadida en
  `CHANGELOG.md`.

### [Control Pedidos] v12.29.33 — Corrección real: "Techo de Gastos" se quedaba colgado en "Cargando…"
- Usuario reportó, con captura de pantalla, que la vista "Techo de
  gastos" se quedaba en "Cargando…" indefinidamente, sin llegar a
  mostrar datos ni ningún error.
- Causa real, encontrada revisando el código: mismo patrón exacto que
  el bug del hotel "PR" de la v12.29.32. La tabla `expediente_exceso`
  (rediseño de Techo de Gastos, Fase 1) solo estaba definida en
  `SQL_STATEMENTS` (`models.py`), lista que **solo ejecuta
  `init_db.py`** a mano, en el primer despliegue sobre una base de
  datos nueva y vacía. Como la base de datos de producción ya existía
  y nadie vuelve a correr `init_db.py` sobre ella, la tabla nunca
  llegó a crearse — pese a que todo el código que la usa
  (`/api/techo/resumen`, expedientes de exceso, etc.) estaba
  desplegado correctamente.
- Consecuencia en cascada: `/api/techo/resumen` fallaba con 500
  ("relation expediente_exceso does not exist"); en el frontend,
  `_fetchTecho()` capturaba ese error y devolvía `null` en vez de
  relanzarlo, pero `loadTecho()` no comprobaba ese caso y accedía a
  `d.mes` directamente sobre `null` — excepción sin capturar justo
  después de pintar "Cargando…", dejando la vista colgada ahí para
  siempre sin ningún aviso visible.
- Corregido:
  - `app.py`: se repite la creación de `expediente_exceso` (+ sus 3
    índices) dentro de `_auto_migrate()` — la función que sí corre en
    cada arranque del servidor —, con `CREATE TABLE/INDEX IF NOT
    EXISTS`. Se ejecutará solo en el próximo arranque, sin ningún
    riesgo de duplicado si `init_db.py` ya se llegó a ejecutar alguna
    vez.
  - `templates/index.html`: `loadTecho()` ahora comprueba si
    `_fetchTecho()` devolvió `null` y muestra un mensaje de error
    visible en la propia vista en vez de quedarse colgada en
    "Cargando…" sin explicación.
- `app.py` compila sin errores. Badge de versión del sidebar
  actualizado a "V 12.29.33"; entrada añadida en `CHANGELOG.md`. No
  hay tests automatizados en el proyecto que requieran actualización.

## 2026-08-01

### [Control Pedidos] v12.29.32 — Corrección real: el hotel "PR" nunca llegaba a insertarse
- Usuario reportó, con capturas y el log de Render, que el hotel de
  pruebas seguía sin aparecer incluso tras desplegar el zip correcto
  y verificado (`expediente_exceso` presente, `PR` presente en
  `models.py`, versión correcta) y reiniciar el servidor.
- Causa real, encontrada revisando la estructura de arranque de
  `app.py`: el `INSERT` del hotel `PR` (v12.29.28) se había añadido a
  `SQL_STATEMENTS` (`models.py`) — pero esa lista **solo la ejecuta
  `init_db.py`**, un script MANUAL pensado para "el primer
  despliegue" sobre una base de datos nueva y vacía (así lo dice su
  propio docstring: "Uso: python init_db.py"). La función que sí
  corre automáticamente en cada arranque del servidor es otra
  completamente distinta, `_auto_migrate()` (llamada en el startup
  de la app, `db.autocommit=True`, cada `ALTER`/`CREATE`/`INSERT` se
  confirma al momento) — ahí es donde vivían correctamente las 8
  fases del rediseño de Techo (`fecha_entrega_especifica`,
  `mes_consumo_techo`, `no_autorizado_previo`, el backfill de la Fase
  7...), por eso esas sí se aplicaron solas sin que nadie tuviera que
  hacer nada manual. El hotel, en cambio, se quedó en el sitio
  equivocado — nadie vuelve a ejecutar `init_db.py` a mano sobre una
  base de datos de producción ya existente, así que nunca llegaba a
  crearse pese a que el código desplegado era correcto de principio a
  fin.
- Corregido: el mismo `INSERT INTO hoteles (...) VALUES ('PR', ...)
  ON CONFLICT DO NOTHING` se repite ahora también dentro de
  `_auto_migrate()`, justo después del backfill de la Fase 7 — se
  ejecutará solo, en el próximo arranque del servidor. Se deja
  también en `models.py`/`SQL_STATEMENTS` sin tocar, para que las
  instalaciones nuevas de verdad (`init_db.py` en un despliegue desde
  cero) lo sigan teniendo — el `ON CONFLICT DO NOTHING` en ambos
  sitios hace que no haya ningún riesgo de duplicado si alguna vez
  coinciden.
- Nuevo log `[MIGRACION] Hotel de pruebas 'PR' insertado` — solo sale
  la primera vez que corre y de verdad inserta la fila (`cur.rowcount`
  tras el `ON CONFLICT DO NOTHING`), para poder confirmarlo en el
  arranque sin tener que consultar la base de datos directamente.
- `app.py` compila sin errores. Badge de versión del sidebar
  actualizado a "V 12.29.32"; entrada añadida en `CHANGELOG.md`.

### [Control Pedidos] v12.29.30 — Corrección: 4 modales sin scroll interno
- Reportado (con captura): no se podía llegar a la sección de hoteles
  asignados en el modal "Editar usuario" para marcar el hotel de
  pruebas "PR".
- Causa real: la clase `modal-box`, usada por 4 modales (Editar/Nuevo
  usuario, Familia, Preferencias de dashboard, Confirmar eliminar),
  no tenía ningún estilo CSS propio en absoluto — le faltaba el
  `max-height:90vh;overflow-y:auto` que sí tiene la clase `modal`
  (usada correctamente por el resto de modales de la app, incluidos
  `.modal-header`/`.modal-footer` con `position:sticky`). Sin esa
  regla, cuando el contenido no cabía en la pantalla, el modal se
  salía del viewport sin ninguna forma de hacer scroll — ni para
  llegar al bloque de hoteles, ni en pantallas pequeñas al propio
  botón "Guardar".
- Corregido: las 4 `<div class="modal-box">` pasan a `<div
  class="modal">`. Confirmado que `modal-box` no tenía ninguna otra
  referencia en el archivo (ni CSS ni JS), así que el cambio no
  afecta a nada más.
- Nota aparte, no relacionada con el bug: el bloque "🛒 Hoteles
  asignados (Compras)" solo aparece cuando el Rol del usuario está en
  "Compras" — con rol Administrador ese bloque no se muestra en
  absoluto (los admins ya tienen acceso a todos los hoteles).
- `app.py` sin cambios (fix solo de `templates/index.html`). Badge de
  versión del sidebar actualizado a "V 12.29.30"; entrada añadida en
  `CHANGELOG.md`.

### [Control Pedidos] v12.29.28 — Hotel de pruebas "PR" para el checklist del rediseño de Techo
- Petición: antes de desplegar/probar las fases del rediseño de Techo
  de Gastos, crear un hotel y un usuario de pruebas separados de la
  operativa real, para poder ejecutar el checklist manual sin riesgo.
- Confirmado con el usuario que los hoteles están hardcodeados —
  `models.py`, `INSERT INTO hoteles (...) VALUES (...) ON CONFLICT DO
  NOTHING` dentro de `SQL_STATEMENTS` (se ejecuta en cada arranque),
  sin ningún endpoint `/api/hoteles` para crearlos desde el panel de
  administración.
- Añadida una fila más a ese mismo `INSERT`: código `PR`, nombre
  `⚠️ HOTEL PRUEBAS — no usar en operativa real` (nombre
  deliberadamente inconfundible en cualquier desplegable o listado,
  para que nadie lo use por error en un pedido de verdad). Como el
  `ON CONFLICT` es por `codigo` (columna `UNIQUE`), no toca ninguno de
  los 10 hoteles reales ya existentes — se inserta solo, sin
  migración aparte, en el próximo arranque del servidor.
- Recordado al usuario: los límites de techo
  (`techo_max_pedido`/`techo_max_mes`/etc.) son una configuración
  global compartida por todos los hoteles, no algo ajustable solo
  para este hotel de pruebas — para el checklist hay que diseñar los
  importes de los pedidos de prueba para que superen los límites ya
  configurados, no bajar esos límites (afectaría también a los
  hoteles reales).
- Próximo paso del usuario: crear un comprador de pruebas y
  asignarlo a este hotel `PR` desde Admin → Usuarios, antes de
  empezar a ejecutar `tests/CHECKLIST_PRUEBAS_MANUALES_TECHO.md`.
- `app.py`/`models.py` compilan sin errores. Badge de versión del
  sidebar actualizado a "V 12.29.28"; entrada añadida en
  `CHANGELOG.md`.

### [Control Pedidos] v12.29.26 — Rediseño Techo de Gastos, Fase 8 de 9 (pruebas) — CIERRE DEL REDISEÑO
- Continuación de la Fase 7 (v12.29.24). Última fase del alcance — la
  Fase 9 (aprobación parcial) queda explícitamente fuera según el
  propio documento de diseño. Con esta entrega se cierran las 9 fases
  completas del rediseño, desde el modelo de datos (v12.29.8) hasta
  aquí.
- Nuevo `tests/test_techo_gastos.py` — 23 pruebas automáticas
  ejecutadas de verdad contra `app.py`, no contra una copia: usa el
  módulo `ast` de Python para extraer el código fuente EXACTO de
  `_check_techo()`, `_techo_snapshot()`,
  `_calcular_fecha_entrega_prevista()` y
  `_resolver_fecha_entrega_prevista()` directamente del archivo, lo
  ejecuta en un espacio de nombres aislado con mocks controlados de
  `query()`/`get_config()`/`rows_to_list()` (sin necesidad de Postgres
  ni de crear la app Flask), y comprueba cada regla con asserts
  simples de Python — sin depender de pytest ni de nada del proyecto.
  Cobertura: las 4 reglas de `_check_techo()` (importe individual, nº
  pedidos por familia, acumulado mensual del hotel, acumulado mensual
  por familia) incluidos sus casos límite (justo en el borde, varios
  motivos a la vez, familia sin límite específico), `_techo_snapshot()`
  con y sin consumo previo, y una prueba de regresión específica para
  el bug `_d`/`_dt` encontrado y corregido en la Fase 1
  (`_calcular_fecha_entrega_prevista()` devolvía siempre `None`
  silenciosamente). **Resultado real de ejecutarlo: 23/23 pruebas
  superadas.** Se lanza con `python3 tests/test_techo_gastos.py`.
- Nuevo `tests/CHECKLIST_PRUEBAS_MANUALES_TECHO.md` — 11 bloques de
  pruebas manuales para todo lo que necesita servidor Flask y base de
  datos reales, que no se puede probar con mocks: circuito básico sin
  exceso, circuito con desvío a Dirección General, aprobar, denegar,
  reabrir un pedido denegado (verificando que se crea una fila NUEVA
  en `expediente_exceso` sin tocar la anterior), cancelar con
  liberación de `mes_consumo_techo` y trazabilidad, compromiso
  potencial y semáforo azul, informe imprimible (verificando que el
  snapshot NO cambia aunque otros pedidos consuman techo después),
  alertas y jobs, backfill/idempotencia, y una batería de pruebas de
  regresión para confirmar que nada de lo tocado en esta sesión (plazo
  de entrega, firma corporativa de correos) se ha visto afectado.
- `app.py` compila sin errores (sin cambios de backend en esta fase,
  solo los 2 archivos de test nuevos en `tests/`). Badge de versión
  del sidebar actualizado a "V 12.29.26"; entrada añadida en
  `CHANGELOG.md`.
- **REDISEÑO DE TECHO DE GASTOS COMPLETO** — de v12.29.8 (Fase 1) a
  v12.29.26 (Fase 8), 9 versiones, con revisión y pruebas en cada
  fase. Recomendado ejecutar el checklist manual contra un entorno
  real antes de considerarlo probado en producción del todo.

### [Control Pedidos] v12.29.24 — Rediseño Techo de Gastos, Fase 7 de 9 (migración/backfill)
- Continuación de la Fase 6 (v12.29.22). **Esta versión modifica datos
  existentes en producción al desplegarse** — aviso explícito en el
  propio `CHANGELOG.md`.
- Motivo: los pedidos que ya estaban en `ENVIADO AL PROVEEDOR`/
  `ENTREGA PARCIAL`/`ENTREGADO` antes de que existiera
  `mes_consumo_techo` (Fase 1) se habrían quedado con esa columna
  vacía para siempre — invisibles para el cálculo del techo del mes
  en que de verdad se enviaron, tanto en `/api/techo/resumen` (si
  coincidiera con el mes actual) como sobre todo en
  `/api/techo/resumen-historico` (Fase 4).
- Nuevo `UPDATE pedidos ... SET mes_consumo_techo = ...` en el bloque
  de migraciones de arranque de `app.py`: rellena la columna una sola
  vez para los pedidos afectados
  (`sujeto_techo=1 AND mes_consumo_techo IS NULL AND estado IN
  ('ENVIADO AL PROVEEDOR','ENTREGA PARCIAL','ENTREGADO')`), con el
  mismo criterio de fallback (`COALESCE`) que usaba el endpoint
  histórico antes de simplificarse en la Fase 4: el último registro
  de "pasó a ENVIADO AL PROVEEDOR" en `historial_estados` para ese
  pedido; si no hay ninguno, `fecha_tramitacion`; si tampoco,
  `creado_en` del propio pedido como último recurso.
  `NULLIF(fecha_tramitacion, '')` evita un error de cast si esa
  columna TEXT viene vacía.
- **Idempotente por diseño**: el propio `WHERE mes_consumo_techo IS
  NULL` hace que, en cualquier arranque posterior — o directamente en
  una base de datos ya migrada — la sentencia no actualice ninguna
  fila. No hace falta ningún flag ni tabla de control de versión de
  migración aparte.
- Queda registrado en el log del servidor
  (`log.info("[MIGRACION] Backfill mes_consumo_techo...")`) cuántos
  pedidos se vieron afectados la primera vez que corre, para poder
  confirmar que se ejecutó y cuánto alcance tuvo.
- Estados excluidos a propósito: los 2 estados nuevos del rediseño
  (`PENDIENTE Vº Bº DIRECCIÓN GENERAL`/`DENEGADO POR DIRECCION
  GENERAL`) no pueden tener pedidos "antiguos" porque no existían
  antes de este rediseño; `CANCELADO` tampoco se toca porque
  cancelar ya libera `mes_consumo_techo` desde la Fase 2 — un pedido
  cancelado antes del rediseño simplemente nunca lo tuvo, que es el
  estado "correcto" para él de todos modos.
- `app.py` compila sin errores. Badge de versión del sidebar
  actualizado a "V 12.29.24"; entrada añadida en `CHANGELOG.md`.
- **Pendiente**: Fase 8 (pruebas de los casos límite del rediseño
  completo). La Fase 9 (aprobación parcial) queda fuera de alcance
  según el propio documento de diseño.

### [Control Pedidos] v12.29.22 — Rediseño Techo de Gastos, Fase 6 (parte 2 de 2, cierre): pantalla de Techo y acciones
- Continuación de la parte 1 (v12.29.20). Con esta entrega se cierra
  la Fase 6 al completo.
- **Decisiones de alcance, comunicadas y confirmadas con el
  usuario**: en vez de construir una página aparte de "panel de
  expedientes", las acciones de aprobar/denegar/imprimir quedan como
  acciones rápidas directamente en las tarjetas de la pantalla de
  Techo (que ya es donde se ve todo lo demás — no tenía sentido
  duplicar la información en dos sitios). La "tabla cronológica" del
  punto 11 se considera ya cubierta por el informe imprimible de la
  Fase 5 (que ya la incluye), en vez de construir una vista en
  pantalla aparte solo para eso. `GET /api/expedientes` (histórico
  completo, Fase 4) sigue sin pantalla de navegación propia — queda
  disponible por API para cuando se pida explícitamente.
- Pantalla de Techo (`loadTecho()`):
  - Semáforo con el nuevo caso `azul` — color (`#cfe2ff`/`#0d6efd`),
    icono 🔵, y color de barra de progreso propios, sin pisar los
    umbrales rojo/amarillo/verde ya existentes (decisión ya tomada
    en la Fase 4: el azul se superpone, no sustituye el cálculo).
  - Nuevo bloque "🧮 Compromiso potencial" — solo se muestra si hay
    algo pendiente de Dirección General en ese hotel, para no
    ensuciar la tarjeta cuando no aporta nada nuevo respecto a
    "Acumulado".
  - Nuevo bloque "🔵 Pendientes de Vº Bº Dirección General" por
    tarjeta — cada expediente pendiente con su pedido, familia,
    importe, motivo, y 3 botones: ✅ Aprobar, ❌ Denegar, 🖨️ Imprimir
    informe.
  - Nuevo bloque "✅ Excesos autorizados este mes" — resumen
    compacto (total + lista con importe y botón imprimir por fila).
- Nueva función `resolverExpedienteTecho(eid, accion)`: captura la
  nota con `prompt()` del navegador (obligatoria al denegar, opcional
  al aprobar — validación también en el propio JS antes de llamar al
  backend, que ya la exige de todos modos) y llama a
  `POST /api/expedientes/<id>/aprobar` o `/denegar` (Fase 2). Elección
  pragmática para esta primera versión — un modal en condiciones en
  vez de `prompt()` sería un cambio contenido a esta única función si
  se prefiere más adelante. Tras resolver: reutiliza
  `_enviarEmailsPendientesEstado()`, invalida las cachés de stats y
  techo, y refresca la vista activa (Techo o Pedidos).
- `app.py` compila sin errores. Badge de versión del sidebar
  actualizado a "V 12.29.22"; entrada añadida en `CHANGELOG.md`.
- **Con esto, la Fase 6 (frontend) queda cerrada del todo.**
  **Pendiente**: Fases 7-9 (backfill de `mes_consumo_techo` para
  pedidos ya en producción con estado `ENVIADO AL PROVEEDOR`/
  posteriores, y pruebas de los casos límite del rediseño completo).

### [Control Pedidos] v12.29.20 — Rediseño Techo de Gastos, Fase 6 (parte 1 de 2): guardado y validaciones
- Continuación de la Fase 5 (v12.29.18). Fase 6 es la más grande
  (frontend completo), así que se entrega en 2 partes — esta primera
  cubre guardado/validaciones; el panel de expedientes y la pantalla
  de Techo actualizada quedan para la parte 2.
- Quitado el `confirm()` de JS obsoleto en el guardado de pedidos —
  el backend nunca más devuelve `techo_errores` desde la Fase 2, así
  que ese bloque era código muerto (inofensivo pero confuso).
  Sustituido por un `toast()` informativo, tipo `warning` (nuevo
  estilo CSS `.toast.warning`), cuando el pedido queda pendiente de
  Vº Bº de Dirección General en vez de enviarse.
- `create_pedido()`/`update_pedido()`: nuevos campos en la respuesta
  JSON — `estado_final` (el estado que realmente quedó guardado,
  puede diferir del solicitado si el circuito de techo lo desvió) y
  `requiere_autorizacion_dg` (booleano). `create_pedido()` no tiene
  el gate de techo en sí (solo `update_pedido()`, decisión de la
  Fase 2), pero se le añadieron los mismos campos por consistencia de
  forma en la respuesta.
- `onEstadoChange()`: `notaObligatoria` ahora también se activa
  cuando el estado destino es `DENEGADO POR DIRECCION GENERAL`
  (además del caso ya existente de reactivar desde `CANCELADO`) —
  etiqueta y placeholder del campo Nota diferenciados según el caso
  ("motivo de la denegación" vs "motivo por el que se reactiva").
  Misma extensión aplicada en la validación real de guardado (bloque
  aparte que sí impide guardar sin nota, `onEstadoChange()` solo
  cambia el aspecto visual).
- Nueva marca visual "⚠️ SIN AUTORIZAR" en el listado de pedidos
  (`renderPedidosTable`) cuando `no_autorizado_previo = TRUE` (punto
  5) — mismo patrón que el badge "📉 TECHO" ya existente.
- Encontrado de propina: los 2 estados nuevos no tenían color de
  badge propio en `estadoBadge()` — caían en el de "pendiente
  compras" por el `|| 'pendiente-compras'` de fallback, dando un
  color confuso. Añadidas variables CSS `--s-pendiente-dg` (azul) /
  `--s-denegado-dg` (rojo distinto del de `CANCELADO`) y sus clases
  `.badge-pendiente-dg` / `.badge-denegado-dg`.
- `app.py` compila sin errores. Badge de versión del sidebar
  actualizado a "V 12.29.20"; entrada añadida en `CHANGELOG.md`.
- **Pendiente**: Fase 6 parte 2 (panel de expedientes completo —
  listado, detalle, aprobar/denegar con nota obligatoria, botón
  imprimir informe —, actualizar pantalla de Techo con los bloques
  pendientes/excesos/compromiso potencial/semáforo azul, tabla
  cronológica en el detalle de cada expediente), más Fases 7-9
  (backfill, pruebas).

### [Control Pedidos] v12.29.18 — Rediseño Techo de Gastos, Fase 5 de 9 (informe imprimible)
- Continuación de la Fase 4 (v12.29.16). Alcance: nuevo endpoint que
  genera el informe (Sección 10 del documento de diseño), reutilizando
  el mecanismo de impresión que ya existe en el proyecto (v11.5.4/
  v11.5.8) en vez de crear uno nuevo desde cero.
- Nuevo `GET /api/expedientes/<id>/informe`: devuelve en una sola
  llamada todo lo necesario para el informe —
  - El expediente completo, con su fotografía presupuestaria
    **congelada** (`consumido_en_solicitud`/`disponible_en_solicitud`/
    `importe_pedido`/`consumo_previo`/`exceso`) — estos valores nunca
    se recalculan aquí (punto 10): el informe siempre refleja la
    situación que había en el momento exacto de la solicitud, aunque
    otros pedidos hayan consumido techo después. Para la situación en
    vivo ya está `/api/techo/resumen` (Fase 4), no este endpoint.
  - Datos del pedido asociado (usa `PEDIDO_SELECT`, ya trae hotel/
    departamento/proveedor/importe).
  - Histórico cronológico de TODOS los intentos de ese mismo pedido
    (mismo dato que `/api/expedientes/pedido/<id>` de la Fase 4,
    incluido también aquí para no necesitar una segunda llamada al
    montar el informe).
  - Histórico de excesos anteriores YA RESUELTOS (no pendientes) del
    mismo hotel + familia — contexto para quien tenga que decidir
    ("¿esto ya ha pasado antes en este hotel/familia?"), limitado a
    los 20 más recientes. `familia_id` puede ser `NULL`, gestionado
    con una cláusula `IS NULL` aparte cuando corresponde.
- Nueva función `imprimirExpediente(eid)` en `templates/index.html` —
  reutiliza `_abrirVentanaImpresion()` y `_fmtEur()`, exactamente el
  mismo patrón que ya usan `imprimirTecho()` e `imprimirAlertas()`
  (construir un HTML, abrir ventana, `window.print()`). El informe
  incluye: cabecera con el resultado (pendiente/aprobado/denegado),
  datos generales, tabla de situación del techo (snapshot), motivo de
  la solicitud, bloque de resolución (o un espacio con líneas en
  blanco y hueco para firma si sigue pendiente y se va a imprimir en
  papel), tabla de cronología de reintentos de este pedido (si hay
  más de uno), y tabla de excesos anteriores del hotel/familia.
- **Sin botón en la interfaz todavía** — la función queda lista para
  conectarse al panel de expedientes de la Fase 6 (donde tiene
  sentido añadir el botón "🖨️ Imprimir informe" junto a
  aprobar/denegar), no se ha forzado ningún acceso provisional desde
  otro sitio de la interfaz para no adelantar trabajo de esa fase.
- `app.py` compila sin errores. Badge de versión del sidebar
  actualizado a "V 12.29.18"; entrada añadida en `CHANGELOG.md`.
- **Pendiente**: Fases 6-9 (frontend completo — incluido el panel de
  expedientes donde cuelgan aprobar/denegar/imprimir y los bloques
  nuevos de la pantalla de Techo —, backfill, pruebas).

### [Control Pedidos] v12.29.16 — Rediseño Techo de Gastos, Fase 4 de 9 (endpoints de consulta)
- Continuación de la Fase 3 (v12.29.14). Alcance: reescribir
  `/api/techo/resumen` y `/resumen-historico` sobre `mes_consumo_techo`,
  añadir los bloques "pendientes"/"excesos autorizados" (Sección 8),
  el indicador Compromiso potencial (punto 9), el semáforo con el caso
  🔵/azul (punto 12), y los 2 endpoints nuevos de expedientes.
- `/api/techo/resumen`: filtro de pedidos cambiado de
  `EXTRACT(YEAR/MONTH FROM p.creado_en)` a `mes_consumo_techo = %s`.
  Nueva query de `expediente_exceso` del mes (pendientes + aprobados),
  agrupada por hotel junto a los pedidos. Cada hotel del resultado
  lleva ahora también: `pendientes_dg` (lista de expedientes),
  `pendientes_dg_importe`, `excesos_autorizados` (lista),
  `excesos_autorizados_importe`, y `compromiso_potencial` (=
  `acumulado + pendientes_dg_importe`, punto 9 — no modifica el
  cálculo del techo, solo visibilidad). El semáforo rojo/amarillo/
  verde mantiene exactamente los mismos umbrales de siempre (decisión
  ya tomada en Fase 3: no tocar `techo_max_pedidos` sin que se pida
  explícitamente), y se añade el nuevo caso `"azul"` que se superpone
  a los anteriores cuando el hotel tiene algún expediente `pendiente`
  este mes (punto 12).
- `/api/techo/resumen-historico`: simplificado de raíz. Antes
  calculaba la "fecha de envío" con un
  `COALESCE(historial_estados, fecha_tramitacion, creado_en)` +
  `DATE_TRUNC`, y exigía además `p.estado = 'ENVIADO AL PROVEEDOR'` —
  lo que EXCLUÍA incorrectamente cualquier pedido que ya hubiera
  avanzado a ENTREGA PARCIAL/ENTREGADO desde entonces (un pedido de
  hace 3 meses ya entregado desaparecía silenciosamente de su propio
  mes histórico). Ahora usa `mes_consumo_techo` directamente, que ya
  captura el mes real de consumo con independencia del estado actual
  — más simple y, de paso, corrige ese fallo de fondo que llevaba
  ahí desde antes del rediseño. Los `CANCELADO` quedan excluidos
  automáticamente porque cancelar limpia `mes_consumo_techo` (Fase
  2), no hace falta filtrarlo aparte. Mismos bloques nuevos que el
  resumen del mes actual (pendientes/excesos/compromiso/semáforo).
- Nuevo `GET /api/expedientes` (Sección 9 — histórico completo, nunca
  se borra): filtros opcionales por querystring `hotel_id`,
  `familia_id`, `resultado` (pendiente/aprobado/denegado), `mes`
  (YYYY-MM). Sin filtros, devuelve todos, del más reciente al más
  antiguo — la paginación, si hace falta, se decide en la Fase 6.
- Nuevo `GET /api/expedientes/pedido/<pedido_id>` (punto 11 —
  histórico cronológico dentro de un expediente concreto): todas las
  filas de `expediente_exceso` de ese `pedido_id`, ordenadas por
  fecha — sale gratis, porque cada reintento tras una denegación ya
  es una fila independiente desde la Fase 1/2, no hace falta ninguna
  tabla ni cálculo adicional. Restringido al mismo criterio de rol
  que el resto del módulo (sin acceso para rol `hotel`), por
  consistencia con los demás endpoints de techo.
- `app.py` compila sin errores. Badge de versión del sidebar
  actualizado a "V 12.29.16"; entrada añadida en `CHANGELOG.md`.
- **Pendiente**: Fases 5-9 (informe imprimible, frontend completo,
  backfill de `mes_consumo_techo` para pedidos ya en producción,
  pruebas de los casos límite).

### [Control Pedidos] v12.29.14 — Rediseño Techo de Gastos, Fase 3 (cierre): job de familia repetida
- Usuario confirmó: `_job_familia_repetida_inner()` también debe
  migrarse a `mes_consumo_techo`, cerrando la duda dejada abierta en
  v12.29.12.
- Filtro de la consulta de familias repetidas cambiado de
  `EXTRACT(YEAR/MONTH FROM p.creado_en)` a `mes_consumo_techo = %s` —
  mismo criterio que `_job_techo_urgente_admins_inner()` y
  `_job_alertas_techo_mensual_inner()`. Comentario del docstring
  actualizado (ya no dice "mismo límite que aplica _check_techo al
  crear/editar", puesto que desde la Fase 2 ya no se comprueba ahí).
- Con esto, los 3 jobs de alertas de techo son consistentes entre sí
  — todos cuentan pedidos por consumo real (`mes_consumo_techo`), no
  por fecha de creación. Fase 3 queda cerrada del todo.
- `app.py` compila sin errores. Badge de versión del sidebar
  actualizado a "V 12.29.14"; entrada añadida en `CHANGELOG.md`.
- **Pendiente**: Fases 4-9 (endpoints de consulta, informe
  imprimible, frontend completo, backfill, pruebas).

### [Control Pedidos] v12.29.12 — Rediseño Techo de Gastos, Fase 3 de 9 (jobs de alertas)
- Continuación de la Fase 2 (v12.29.10). Alcance de esta fase, tal
  como lo nombra el documento de diseño: solo `_job_techo_urgente_admins`
  y `_job_alertas_techo_mensual`.
- `_job_techo_urgente_admins_inner()`: filtro de la consulta de
  pedidos del mes cambiado de `EXTRACT(YEAR/MONTH FROM p.creado_en)`
  a `mes_consumo_techo = %s` — igual criterio que `_check_techo()`
  desde la Fase 2. `year`/`month` quedan como variables sin usar en
  la función (inofensivo, no se ha limpiado por no tocar más de lo
  necesario).
- `_job_alertas_techo_mensual_inner()`: mismo cambio de filtro.
- Nueva alerta específica por Telegram a admins cuando se detecta
  `no_autorizado_previo = TRUE` en algún pedido (punto 5 del
  rediseño) — se añade al final de `_job_techo_urgente_admins_inner()`,
  consulta pedidos con el flag activo que no se hayan notificado
  todavía (dedup vía `whatsapp_log`, tipo
  `telegram_no_autorizado_previo`, por `pedido_id`), y avisa a los
  mismos destinatarios que ya reciben el aviso de techo urgente. Esto
  es solo para visibilidad inmediata — la constancia permanente ya
  queda en `historial_estados` desde la Fase 2 (el choke-point de
  `update_pedido()` ya la registra siempre que corresponde).
- **Encontrado, sin tocar, pendiente de confirmación con el
  usuario**: `_job_familia_repetida_inner()` (alerta de "familia
  repetida", relacionada con `techo_max_pedidos_familia`) sigue
  filtrando por `creado_en`, con la misma inconsistencia semántica
  que tenían los 2 jobs de arriba antes de esta fase — cuenta
  pedidos por fecha de creación, no por si de verdad han llegado a
  consumir presupuesto. No estaba nombrada explícitamente en la Fase
  3 del documento de diseño (que solo cita
  `_job_techo_urgente_admins` y `_job_alertas_techo_mensual` por
  nombre), así que no se ha tocado por respeto al alcance cerrado del
  documento — a la espera de que el usuario confirme si también debe
  migrarse a `mes_consumo_techo` o si se deja aparte a propósito.
- `app.py` compila sin errores. Badge de versión del sidebar
  actualizado a "V 12.29.12"; entrada añadida en `CHANGELOG.md`.
- **Pendiente**: Fases 4-9 (endpoints de consulta con los nuevos
  bloques "pendientes"/"excesos", informe imprimible, frontend
  completo, backfill, pruebas).

### [Control Pedidos] v12.29.10 — Rediseño Techo de Gastos, Fase 2 de 9 (lógica de negocio central)
- Continuación de la Fase 1 (v12.29.8, modelo de datos). Esta fase
  hace el circuito realmente funcional: el pedido puede quedar
  bloqueado en `PENDIENTE Vº Bº DIRECCIÓN GENERAL` de verdad, con
  expediente creado y trazabilidad.
- **Decisión de arquitectura** (documentada explícitamente al
  usuario, distinta a la letra literal del documento): en vez de un
  endpoint nuevo `/solicitar-autorizacion`, el circuito se engancha
  **dentro** de `update_pedido()`, justo donde ya se validaba
  "proveedor obligatorio / PDF obligatorio" para `ENVIADO AL
  PROVEEDOR` — es el único choke-point real por el que pasa
  cualquier vía que intente ese cambio de estado (flujo normal,
  edición directa de admin...). Motivo: evita duplicar toda esa
  validación en un endpoint aparte, y satisface de forma natural el
  "chequeo de integridad" del punto 5 sin código repetido — no hace
  falta un endpoint separado ni el frontend necesita un botón nuevo,
  el flujo de "cambiar estado" de siempre simplemente puede terminar
  en un estado distinto al pedido.
- `_check_techo()` reescrita:
  - Filtro por `mes_consumo_techo = %s` en vez de
    `EXTRACT(YEAR/MONTH FROM p.creado_en)` — ahora solo cuentan
    pedidos que YA han consumido techo de verdad (pasaron por
    ENVIADO AL PROVEEDOR), no por su fecha de creación.
  - Eliminada la antigua "Regla 1" (máximo N pedidos sujetos al techo
    por hotel/mes, agregado sin distinguir familia) — decisión de
    negocio del rediseño (punto 4): solo queda vigente el límite por
    hotel + familia (`techo_max_pedidos_familia`).
  - Ya NO bloquea el guardado — sigue devolviendo la lista de
    motivos, pero ahora son el detonante del circuito, no un 422.
  - Docstring reescrito explicando el cambio de momento de disparo.
- Nueva función `_techo_snapshot(hotel_id, mes_str)`: fotografía
  consumido/disponible del hotel en el momento exacto de la llamada
  — usada para congelar `consumido_en_solicitud`/
  `disponible_en_solicitud` en `expediente_exceso` al crear la fila
  (punto 10 — nunca se recalcula después, ni siquiera si otros
  pedidos consumen techo más tarde).
- `create_pedido()`: eliminado el bloqueo por techo al crear un
  pedido — ya no comprueba `_check_techo()` en absoluto.
- `update_pedido()`:
  - Eliminado el bloqueo genérico por techo en cualquier edición
    (antes disparaba en cualquier cambio si `sujeto_techo`, ahora
    solo importa al intentar pasar a `ENVIADO AL PROVEEDOR`).
  - Dentro del bloque de validación de `ENVIADO AL PROVEEDOR`
    (después de que pasen las comprobaciones de proveedor/docs/nº
    pedido existentes — un pedido bloqueado por techo no debe
    además pedir cosas que aún no hacen falta): si `sujeto_techo` y
    no hay ya un `expediente_exceso` con `resultado='aprobado'` para
    este pedido+mes, se ejecuta `_check_techo()`; si hay motivos, se
    crea el expediente (`resultado='pendiente'`, con el snapshot) y
    se sobrescribe `estado_nuevo` a
    `PENDIENTE Vº Bº DIRECCIÓN GENERAL` — el resto de la función
    (UPDATE, historial, commit, notificación) sigue funcionando sin
    ningún cambio adicional, ya que solo depende del valor final de
    `estado_nuevo`.
  - `mes_consumo_techo` añadido al UPDATE final: se rellena con el
    mes actual SOLO en el instante real de la transición a `ENVIADO
    AL PROVEEDOR` (`estado_nuevo=="ENVIADO AL PROVEEDOR" and
    estado_antes!="ENVIADO AL PROVEEDOR"`); se libera (`NULL`) si el
    pedido pasa a `CANCELADO` y ya lo tenía relleno — con nota de
    trazabilidad completa en `historial_estados` (nº pedido, importe,
    quién dio el visto bueno original — consultado del propio
    `historial_estados` —, quién cancela). Nada se borra (punto 7).
  - Estado `DENEGADO POR DIRECCION GENERAL` es reabrible por diseño:
    si se reedita y se reintenta el envío, el mismo mecanismo vuelve
    a ejecutarse y crea un expediente NUEVO e independiente (nunca
    sobrescribe el anterior denegado) — da gratis el histórico
    cronológico por expediente de la Fase 4/punto 11.
- Nuevos endpoints:
  - `POST /api/expedientes/<id>/aprobar`: valida que el expediente
    siga pendiente y el pedido siga en
    `PENDIENTE Vº Bº DIRECCIÓN GENERAL`, revalida que el proveedor
    siga teniendo contacto con email (crítico para el envío — no se
    repiten el resto de validaciones de "listo para enviar", ver
    limitación documentada en el propio docstring), marca el
    expediente `aprobado`, pasa el pedido a `ENVIADO AL PROVEEDOR`
    con `mes_consumo_techo` relleno, y reutiliza
    `_notificar_cambio_estado()` — mismo email/aviso que cualquier
    otro cambio de estado, sin lógica nueva de notificación.
  - `POST /api/expedientes/<id>/denegar`: motivo obligatorio (punto
    8), marca el expediente `denegado`, pasa el pedido a
    `DENEGADO POR DIRECCION GENERAL`. La fecha de resolución no es
    un campo manual — se toma automáticamente de `NOW()` al guardar.
- **Fuera de alcance de esta fase, documentado explícitamente**: la
  recarga masiva desde Excel (`reset_e_importar`, herramienta de
  admin para reset completo) no pasa por este circuito — inserta
  pedidos directamente con el estado que traiga el Excel. Su
  interacción con `mes_consumo_techo` la cubrirá el backfill de la
  Fase 7 (que de hecho tendrá que contemplar que un reset completo
  también borra cualquier `mes_consumo_techo` ya migrado).
- `app.py` compila sin errores en todo momento durante la
  implementación. Badge de versión del sidebar actualizado a
  "V 12.29.10"; entrada añadida en `CHANGELOG.md`.
- **Pendiente**: Fases 3-9 (jobs de alertas, endpoints de consulta
  con los nuevos bloques "pendientes"/"excesos", informe imprimible,
  frontend completo — incluido quitar el `confirm()` de JS ya
  obsoleto, aunque inofensivo mientras tanto —, backfill, pruebas).

### [Control Pedidos] v12.29.8 — Rediseño Techo de Gastos, Fase 1 de 9 (modelo de datos)
- Usuario aportó un "Informe técnico de actuación" completo y cerrado
  (diseño de negocio ya decidido, sin puntos abiertos) para rediseñar
  el módulo de Techo de Gastos: de "preventivo sin autoridad real"
  (aviso `confirm()` de JS saltable por cualquiera, sin rastro) a un
  circuito de autorización real vía Dirección General, con
  trazabilidad completa. Separa **Techo de Gasto** (situación
  presupuestaria del mes) de **Expediente de Exceso** (registro
  permanente e independiente de cada autorización extraordinaria).
- Plan por fases (9 en total): 1) modelo de datos, 2) lógica de
  negocio central, 3) jobs de alertas, 4) endpoints de consulta,
  5) informe imprimible, 6) frontend, 7) migración/backfill,
  8) pruebas, 9) evolución futura (aprobación parcial — fuera de
  alcance de esta v1). Cada fase deja el sistema funcional antes de
  pasar a la siguiente; empezado por la Fase 1 en esta entrega.
- **Fase 1 — Modelo de datos** (única fase de esta entrega, sin
  cambios de comportamiento visible todavía):
  - `ESTADOS_VALIDOS` (`models.py`): 2 estados nuevos —
    `PENDIENTE Vº Bº DIRECCIÓN GENERAL` (bloquea el envío al
    proveedor hasta resolución) y `DENEGADO POR DIRECCION GENERAL`
    (reabrible — se puede reeditar y reintentar, cuenta como
    denegación en el histórico aunque el pedido nunca haya consumido
    techo). Dirección General NO es un rol nuevo — es un paso del
    flujo definido por el estado del pedido, igual que las otras
    "PENDIENTE FIRMA...". No se toca el sistema de roles.
  - Nueva tabla `expediente_exceso`: `id`, `pedido_id`, `hotel_id`,
    `familia_id`, `mes` (YYYY-MM), `importe_pedido`, `consumo_previo`,
    `exceso`, `motivo_solicitud`, `usuario_solicitante_id`,
    `resultado` (pendiente/aprobado/denegado),
    `usuario_resuelve_id`, `fecha_resolucion`,
    `observaciones_direccion_general`, `consumido_en_solicitud`,
    `disponible_en_solicitud`, `creado_en`. Un pedido puede tener
    varias filas si es reabrible — cada intento es una fila
    independiente, nunca se sobrescribe (da gratis el histórico
    cronológico por expediente de la Fase 4). Las columnas
    `consumido_en_solicitud`/`disponible_en_solicitud` son la
    "fotografía presupuestaria congelada": se rellenan una sola vez
    al crear la fila (Fase 2) y nunca se recalculan — el informe de
    la Fase 5 las lee siempre a ellas, nunca vuelve a llamar a
    `_check_techo()`/`techo_resumen` para reconstruir el histórico.
  - 2 columnas nuevas en `pedidos`: `mes_consumo_techo` (TEXT,
    YYYY-MM — se rellena SOLO al pasar a ENVIADO AL PROVEEDOR, se
    vacía si se cancela después; sustituye a filtrar por `creado_en`
    en todas las consultas de consumo desde la Fase 2) y
    `no_autorizado_previo` (BOOLEAN — flag de integridad para cuando
    un pedido llega a ENVIADO AL PROVEEDOR sin autorización de
    Dirección General cuando debería).
  - Añadidas también a la definición base de `models.py`
    (`SQL_STATEMENTS`, que se ejecuta en cada arranque) para
    instalaciones nuevas — la tabla `expediente_exceso` se crea sola
    en cualquier instalación (`CREATE TABLE IF NOT EXISTS`); las 2
    columnas de `pedidos` necesitan además el `ALTER TABLE ... ADD
    COLUMN IF NOT EXISTS` de `app.py` para las instalaciones que ya
    existen (el `CREATE TABLE IF NOT EXISTS` de `pedidos` es un
    no-op si la tabla ya existe, no añade columnas nuevas por sí
    solo — mismo patrón ya usado para `plazo_entrega_dias` y
    `fecha_entrega_especifica`).
- Verificado que no hay ninguna validación de estado en `app.py` que
  bloquee los 2 estados nuevos (solo 2 fallbacks genéricos de
  importación masiva, sin lista blanca cerrada).
- `app.py` y `models.py` compilan sin errores. Badge de versión del
  sidebar actualizado a "V 12.29.8"; entrada añadida en
  `CHANGELOG.md`.
- **Pendiente**: Fases 2-9, a entregar en próximos mensajes dado el
  tamaño del rediseño (lógica de `_check_techo()`, nuevos endpoints
  de solicitud/aprobación/denegación, jobs de alertas, endpoints de
  consulta con los nuevos bloques "pendientes"/"excesos", informe
  imprimible, frontend completo, backfill de `mes_consumo_techo` para
  pedidos ya en producción, y pruebas de los casos límite).

### [Control Pedidos] v12.29.6 — Ajuste visual: plazo entrega y fecha específica juntos
- Petición (con captura): "Plazo entrega (días)" y "Fecha de entrega
  específica" (v12.29.4) quedaban en filas distintas de la rejilla
  del formulario — poco identificativo, al ser dos formas
  alternativas del mismo dato.
- Unidos en un mismo `.form-group`, lado a lado con flexbox
  (`display:flex;gap:16px`) — antes eran 2 `.form-group` separados
  que caían en filas distintas de la rejilla automática. Sin cambios
  de comportamiento ni de backend, solo maquetación
  (`templates/index.html`).
- Badge de versión del sidebar actualizado a "V 12.29.6"; entrada
  añadida en `CHANGELOG.md`.

### [Control Pedidos] v12.29.4 — Fecha de entrega específica del proveedor + bug crítico corregido
- Petición: junto a "Plazo entrega (días)", añadir un campo de fecha
  de entrega concreta — si el proveedor da un día exacto en vez de
  "X días", las reclamaciones se calculan a partir de esa fecha. Si
  no se rellena nada, igual que hasta ahora.
- 🔴 **Bug crítico encontrado y corregido de paso, no buscado**:
  `_calcular_fecha_entrega_prevista()` usaba `_d`/`_dt`, nombres que
  NUNCA se importaron en esa función. Como `fecha_tramitacion` se
  guarda como TEXT, siempre caía en la rama que los necesitaba,
  lanzaba `NameError` silenciado por un `except Exception: return
  None`, y devolvía `None` siempre — mismo patrón de fallo ya
  corregido en `_dias_desde_fecha` el 30 de julio, pero que aquí se
  quedó sin arreglar. Consecuencia: **toda la lógica de alertas por
  "Plazo entrega (días)" llevaba inactiva desde que existe la
  funcionalidad**, sin ningún error visible en logs — nunca disparó
  un aviso por esa vía. Corregido usando los nombres bien importados
  a nivel de módulo (`datetime`, `_date` — mismo patrón ya
  establecido en `_dias_desde_fecha`).
- Nueva columna `fecha_entrega_especifica` (DATE) en `pedidos`
  (migración `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`).
- Nueva función `_resolver_fecha_entrega_prevista(pedido)`: prioriza
  la fecha específica si existe; si no, calcula por
  `fecha_tramitacion + plazo_entrega_dias` (comportamiento de
  siempre); si no hay ninguno de los dos, `None`.
- `_alertas_plazo_entrega()` y `_debe_usar_logica_plazo()`
  actualizadas para usar el nuevo resolutor — reclamaciones
  automáticas y clasificación de alertas ya respetan la prioridad
  fecha específica > plazo en días.
- Añadida la columna a `_JOB_PEDIDO_SQL` y `PEDIDO_SELECT_STATS`, y
  al `INSERT`/`UPDATE` de `create_pedido`/`update_pedido`.
  `PEDIDO_SELECT` (listado/detalle) ya la incluye automáticamente,
  usa `p.*`.
- Frontend: nuevo campo "Fecha de entrega específica (proveedor)"
  junto a "Plazo entrega (días)", con nota explicando la prioridad.
  `actualizarFechaEntregaPrevista()` prioriza la fecha específica si
  está rellena. Oculto también para el rol hotel, igual que el plazo
  en días. Tooltip del badge "📅 Entrega prevista" en el listado
  actualizado para reflejar las 2 fuentes posibles.
- `app.py` compila sin errores en todo momento durante la
  implementación. Badge de versión del sidebar actualizado a
  "V 12.29.4"; entrada añadida en `CHANGELOG.md`.

### [Organizador] v4.16.2 — Corrección: "Limpiar chat" afectaba a varias conversaciones a la vez
- Reportado: el botón "Limpiar chat" debería borrar solo la
  conversación abierta, no todas.
- Causa raíz en `app/db/sqlite.py`: al abrir una conversación privada
  NUEVA (sin mensajes todavía), `_abrir_nueva_conversacion()` pasa
  `canal_id=None` a propósito (lo resuelve el backend con el primer
  mensaje). Sin guarda, `set_chat_limpiado(None, ...)` guardaba la
  marca bajo la clave JSON `"null"` — y TODAS las conversaciones
  nuevas sin resolver comparten ese mismo `canal_id=None` hasta que
  reciben su primer mensaje. Limpiar una conversación nueva marcaba
  como limpiadas también todas las demás conversaciones nuevas sin
  resolver que hubiera en ese momento, no solo la abierta.
- Corregido con una guarda (`if not canal_id`) en
  `get_chat_limpiado()`/`set_chat_limpiado()` — un canal sin resolver
  simplemente no guarda ni aplica ninguna marca (tampoco hace falta:
  si no tiene `canal_id` es porque no tiene mensajes todavía). No
  hizo falta tocar `ventana_chat.py` ni `chat_popup.py`, ya llamaban
  bien a estas funciones — el fallo estaba solo en el almacenamiento.
- Los archivos compilan sin errores. `APP_VERSION` → `v4.16.2`;
  `release_notes_actual.txt` y `release_notes.md` actualizados.

### [Organizador] v4.16.0 — Corrección: solicitud de acceso volvía a bloquear el panel Admin
- Reportado (con captura del diálogo de solicitud): tras crear la
  contraseña momentánea, cerrar y reabrir el Organizador dejaba sin
  poder entrar al panel de Administración — volvía a salir el
  formulario de "Enviar solicitud" en vez del de acceso.
- Bug real en el fix de v4.14.4: `_solicitud_pendiente` exigía
  además `not _bp_pend` (contraseña bridge vacía). Cubría el primer
  reinicio (recién enviada la solicitud, sin contraseña local
  todavía), pero en cuanto el usuario creaba su contraseña momentánea
  (bloque "1-bis" de `admin_auth.verificar_acceso()`, que la guarda
  con `update_bridge_credentials`), `bridge_password` dejaba de estar
  vacío — y en el siguiente reinicio la condición volvía a fallar,
  forzando otra vez `_modo_alta()`. Resultado: quien ya se había
  creado su contraseña momentánea se quedaba bloqueado para siempre,
  sin poder usarla.
- Corregido: se quita el requisito de contraseña vacía —
  `_solicitud_pendiente` pasa a ser solo "el usuario de Windows ya
  tiene una solicitud registrada" (`bridge_user == uwin`), tenga o no
  tenga ya contraseña local. El subtítulo del diálogo se adapta
  (invita a "crear" la contraseña si aún no hay, o a "introducirla"
  si ya existe), pero en ambos casos se queda en modo login sin
  forzar nunca el formulario de alta mientras la solicitud siga sin
  aprobar.
- Confirmado de paso que el guardado automático en "Mi Usuario" →
  credenciales bridge ya funcionaba bien (se relee de la BD local
  cada vez que se abre esa ventana) — el usuario no llegaba a verlo
  por este bloqueo previo, no era un problema aparte.
- `main_agenda.py` compila sin errores. `APP_VERSION` → `v4.16.0`;
  `release_notes_actual.txt` y `release_notes.md` actualizados.

### [Organizador] v4.14.8 — "Limpiar chat" pasa a ser persistente por equipo
- Petición: que el histórico desaparezca de verdad cada vez que se
  pulsa "Limpiar chat", no solo la vista de esa sesión — hasta ahora,
  al salir del chat y volver a entrar, todo reaparecía (diseño
  deliberado desde v4.14.2, pero se pidió cambiarlo).
- `app/db/sqlite.py` — 3 funciones nuevas sobre el mismo `config.json`
  que ya usa el resto de la app (sin tocar SQLite):
  `get_chat_limpiado(canal_id)` / `set_chat_limpiado(canal_id,
  marca_iso)` (guardan/leen, por canal, la fecha/hora ISO 8601 UTC del
  último "Limpiar chat"), y `filtrar_mensajes_limpiados(canal_id,
  mensajes)` (descarta los mensajes con `creado_en` anterior o igual a
  esa marca — comparación de strings directa, sin parsear fechas).
- `app/ui/ventana_chat.py`: `_limpiar_chat()` guarda la marca antes de
  vaciar la vista; `_cargar_historial()` filtra por ella antes de
  pintar. Texto del diálogo de confirmación actualizado para explicar
  el nuevo alcance.
- `app/ui/chat_popup.py`: mismo filtro aplicado en `_cargar()`, para
  que la burbuja flotante sea coherente con la ventana principal.
- **Alcance — local por equipo, no de servidor:** no hay acceso desde
  este proyecto al backend de chat (Flask/SocketIO independiente), así
  que es un filtro en el cliente — el marcador vive en `config.json`
  de `%APPDATA%\OrganizadorPrincess`. No borra nada del servidor: el
  resto de participantes del canal sigue viendo el historial completo,
  y si el mismo usuario entra desde otro PC también lo verá ahí hasta
  que limpie también en ese equipo. Un borrado real de servidor
  requeriría tocar el backend de chat, fuera del alcance de este repo.
- Los 3 archivos compilan sin errores. `APP_VERSION` → `v4.14.8`;
  `release_notes_actual.txt` y `release_notes.md` actualizados.

### [Organizador] v4.14.6 — Contraste de "Limpiar chat" y texto de ayuda (chat)
- Petición: mejorar el contraste del botón "Limpiar chat" y del texto
  bajo "Elige uno o varios compañeros" en el chat; verificar de paso
  si "Limpiar chat" realmente limpia algo, dado que al salir y volver
  a entrar todo sigue ahí.
- Causa del contraste: la app usa el tema oscuro `superhero`, donde
  `bootstyle="secondary"` (`#4e5d6c`) contra el fondo `bg` (`#2b3e50`)
  da un ratio de contraste de ~1.6:1 — muy por debajo del mínimo
  legible (4.5:1 texto normal, WCAG AA). Verificado consultando la
  paleta real del tema (`ttkbootstrap.themes.standard.
  STANDARD_THEMES["superhero"]`), no a ojo.
- Corregido en `app/ui/ventana_chat.py`:
  - Botón "🧹 Limpiar chat": `secondary-outline` → `info-outline`
    (`#5bc0de` ≈ 4.8:1 de contraste).
  - Texto de ayuda bajo "Elige uno o varios compañeros:" (diálogo
    `_abrir_nueva_conversacion`): `secondary` → `light` (`#ABB6C2` ≈
    5.0:1).
  - De propina (mismo problema, no pedido explícitamente): la
    etiqueta `lbl_estado` ("Conectando…", estado inicial antes de
    resolver a 🟢/🟡/🔴) también usaba `secondary` → cambiada a
    `light` igual que las anteriores.
  - `app/ui/chat_popup.py` no tiene ni el botón ni el selector de
    compañeros (solo existen en la ventana principal) — nada que
    tocar ahí para estos 2 puntos.
- (Ver corrección posterior el mismo día: se decidió cambiar este
  comportamiento — el histórico SÍ desaparece ahora al pulsar
  "Limpiar chat".) `APP_VERSION` v4.14.6.

### [Organizador] v4.14.4 — Fix: contraseña momentánea no dejaba continuar con solicitud ya enviada
- Reportado: al reabrir «⚙ Admin» tras haber enviado ya una solicitud
  de acceso (pendiente de aprobación), volvía a salir siempre el
  formulario de "Enviar solicitud" en vez de dejar escribir la
  contraseña momentánea.
- Causa: `_comprobar_existencia_bg()` forzaba `_modo_alta()` cada vez
  que `existe_en_plataforma(uwin)` devolvía `False`, sin distinguir
  "nunca se ha pedido acceso" de "ya se pidió, pendiente de
  aprobación" — ambos casos dan `existe=False` porque el usuario aún
  no existe de verdad en Control de Pedidos.
- Corregido en `main_agenda.py`: se comprueba
  `get_bridge_credentials(uwin)` — si `bridge_user == uwin` y
  `bridge_password` está vacío (estado que deja `_crear_acceso()` al
  enviar la solicitud, vía `update_bridge_credentials(uwin, uwin,
  "")`), se considera solicitud pendiente y se mantiene el modo login
  con subtítulo explicativo, en vez de forzar el formulario de alta.
  Así se llega al bloque "1-bis" ya existente en
  `admin_auth.verificar_acceso()` (2026-07-28), que acepta la primera
  contraseña introducida ahí como contraseña momentánea de acceso
  local — antes nunca se llegaba a esa pantalla. No hizo falta tocar
  `admin_auth.py`, esa lógica ya funcionaba bien.
- Nota aparte, no relacionada con este fix: el correo de aprobación
  de la solicitud no llega al usuario — no es un bug de este proyecto
  (el Organizador solo hace la petición HTTP al proxy de Control de
  Pedidos; el envío del correo lo genera el backend de Control de
  Pedidos al aprobar la solicitud, fuera del alcance de este repo).
  Pendiente de revisar desde el lado de Control de Pedidos si se
  aporta acceso a ese código.
- `main_agenda.py` compila sin errores. `APP_VERSION` v4.14.4.

### [Ecosistema] A partir de ahora: HISTORIAL_CAMBIOS.md es un único documento compartido
- Petición del usuario: como Organizador y Control de Pedidos van
  relacionados, el historial de ambas aplicaciones debe ser siempre
  el mismo archivo — no dos copias que se van desincronizando (esta
  misma sesión, la copia de Organizador se había quedado en el 29 de
  julio mientras la de Control de Pedidos seguía sumando entradas).
  Fusionadas aquí las 2 entradas de Organizador que solo estaban en
  su copia (v4.14.6 y v4.14.4) — de aquí en adelante, cada entrega
  actualiza este único documento, y hay que subirlo igual a los dos
  repos (o valorar que uno de los dos lo referencie en vez de
  duplicarlo).

---

## 2026-07-31 (27)

### [Control Pedidos] v12.29.2 — Revisión del zip v12.29.0 + 2 correos sin logo
- A petición del usuario, revisión completa del zip subido (v12.29.0)
  contra el código real, no solo contra el propio CHANGELOG.
- ✅ Confirmado correcto: Techo de gastos por familia (v12.28.0 y
  v12.29.0) — `_check_techo()` Reglas 2 y 4, job de familia repetida
  con `HAVING COUNT(*) >= %s` configurable, los 2 endpoints de resumen
  (`/api/techo/resumen` y `-historico`) devolviendo
  `familias_conteo`/`familias_importe`/`max_pedidos_familia`/
  `max_importe_familia`, y su renderizado en frontend (tarjetas +
  exportación/impresión) — todo revisado línea a línea.
- ✅ Confirmado correcto: logo en las 7 plantillas de proveedor/
  internas (v12.27.22) — `_email_header_html()` con tabla (no
  flexbox, más compatible con Outlook y similares), usada
  exactamente en las 7 plantillas que dice el CHANGELOG.
- ❌ Encontrado: 2 correos se quedaron sin logo pese al "sí, a
  todos" — el código de verificación de login
  (`_email_html_simple()`, la plantilla de la captura original que
  motivó la petición) y el de restablecimiento de contraseña, que ni
  siquiera usaba `_email_html_simple()` (párrafos sueltos sin
  plantilla). Corregido: `_email_html_simple()` ahora envuelve el
  cuerpo con `_email_header_html()`; el email de reset de contraseña
  pasa a usar `_email_html_simple()` igual que el resto de correos
  cortos tipo "código/enlace". Probado con datos de ejemplo — salida
  limpia.
- ❌ Encontrado: `CHANGELOG.md` con 2 cabeceras de versión perdidas
  (v12.28.0 y v12.27.22 — el contenido estaba, pero sin su línea
  `# vX.Y.Z — fecha`, quedando concatenadas bajo la versión
  siguiente). Mismo tipo de fallo que ya se dio un par de veces en
  esta conversación al insertar una entrada nueva encima de una
  existente. Corregido. `docs/HISTORIAL_CAMBIOS.md` sí las tenía
  bien, no hizo falta tocarlo por eso.
- `app.py` compila sin errores en todo momento durante la revisión.
- Badge de versión del sidebar actualizado a "V 12.29.2"; entrada
  añadida en `CHANGELOG.md`.

---

## 2026-07-31 (26)

### [Control Pedidos] v12.29.0 — Techo de gastos: importe máximo (€) también configurable por hotel/mes y familia
- Petición del usuario, continuación directa de v12.28.0: además de limitar
  el **Nº de pedidos** por hotel/mes y familia, se pide poder limitar el
  **importe (€)** que puede acumular una familia concreta en el mes —
  hasta ahora el único tope en € era el mensual del hotel entero
  (`techo_max_mes`, Regla 3 de `_check_techo`).
- Nuevo parámetro editable en Config alertas → 💳 Techo de gastos:
  **"Techo — Importe máximo mensual por hotel y familia (€)"**
  (nueva clave `techo_max_mes_familia`, independiente de
  `techo_max_pedidos_familia` que ya limitaba el Nº de pedidos).
  Por defecto **0 = sin límite**, para no cambiar nada en producción hasta
  que un admin ponga un valor > 0.
- `_check_techo()`: nueva **Regla 4** — suma el importe de los pedidos de
  esa familia en el hotel/mes y, si `techo_max_mes_familia > 0`, bloquea
  el pedido cuando ese acumulado superaría el límite (mismo mecanismo que
  ya usaba la Regla 3 a nivel de hotel/mes total, incluido el "forzar"
  para usuarios con permiso).
- `/api/techo/resumen` y `/api/techo/resumen-historico`: devuelven ahora
  también `familias_importe` (€ acumulado por familia este mes) y
  `max_importe_familia`, además de los campos ya añadidos en v12.28.0.
- Pestaña 📉 Techo de gastos (tarjetas por hotel): la línea "Familias:"
  añade el importe acumulado de cada familia frente al nuevo límite
  (`Nombre (n/máx pedidos · importe/máx €)`) cuando el límite en € está
  activo, y resalta en ámbar tanto por Nº de pedidos como por importe.
- Exportación/impresión del resumen de Techo de gastos: el resaltado de
  "familia repetida" ahora también se dispara si el importe acumulado de
  la familia alcanza el nuevo límite en €, no solo por Nº de pedidos.
- Migración `ON CONFLICT DO NOTHING` (auto-ejecutada por `_auto_migrate()`
  al arrancar la app) + seed para instalaciones nuevas — **no requiere
  ninguna acción manual en Supabase**.
- Pendiente / fuera de alcance de esta petición: no se ha dado de alta un
  aviso automático dedicado (Telegram/popup) para cuando se supera este
  importe por familia — de momento solo bloquea la creación del pedido y
  se ve reflejado en el resumen/dashboard. Para una alerta proactiva
  habría que registrar un nuevo evento en `eventos_aviso`, igual que
  existe para "Familia repetida".
- Badge de versión del sidebar → "V 12.29.0".

## 2026-07-31 (25)

### [Control Pedidos] v12.28.0 — Techo de gastos: Nº de pedidos configurable por hotel/mes y familia (antes fijo a 1)
- Petición del usuario: hasta ahora una familia de artículos solo podía
  usarse **una vez al mes por hotel** — regla fija en código dentro de
  `_check_techo()` (Regla 2: "Ya existe un pedido de la familia... solo
  puede usarse una vez al mes"). El único número editable desde Config
  alertas → 💳 Techo de gastos era el máximo de pedidos **totales** por
  hotel/mes (`techo_max_pedidos`), no el máximo por familia.
- Nuevo parámetro editable **"Techo — Nº máximo de pedidos por hotel/mes y
  familia"** (`techo_max_pedidos_familia`), por defecto **1** (mismo
  comportamiento que antes hasta que un admin lo cambie), en el mismo
  grupo que los 4 campos existentes de Techo de gastos.
- `_check_techo()`: la Regla 2 deja de bloquear con un mensaje fijo de
  "ya usada este mes" y pasa a comparar el nº de pedidos de esa familia
  en el hotel/mes contra el nuevo límite configurable (mismo patrón que
  la Regla 1, que ya hacía esto a nivel de hotel/mes total).
- Job `_job_familia_repetida_inner` (alerta 🔴 "Familia/Partida REPETIDA"
  a comprador y admins, cada 2 días por defecto): el `HAVING COUNT(*) > 1`
  fijo en SQL pasa a `HAVING COUNT(*) >= techo_max_pedidos_familia`, para
  que dispare exactamente en el mismo umbral que ahora bloquea la
  creación del pedido — antes de este cambio, con el límite en 1, esta
  alerta y el bloqueo de creación ya coincidían por casualidad (>1 y
  bloqueo a partir de 1 repetición); con el límite configurable, sin este
  ajuste se habrían desincronizado.
- `/api/techo/resumen` y `/api/techo/resumen-historico`: devuelven ahora
  `familias_conteo` (nº de pedidos por familia este mes) y
  `max_pedidos_familia`, además de los campos ya existentes.
- Pestaña 📉 Techo de gastos (tarjetas por hotel): la línea "Familias:"
  pasa de listar solo nombres a mostrar el conteo de cada familia frente
  al límite (`Nombre (n/máximo)`), resaltando en ámbar las que están al
  límite o por encima.
- Exportación/impresión del resumen de Techo de gastos: el resaltado de
  "familia repetida" (antes fijo a `> 1`) usa ahora el mismo límite
  configurable por hotel.
- No hizo falta tocar el HTML de Config alertas: el panel se pinta
  dinámicamente desde la tabla `config_alertas`, así que el nuevo campo
  aparece solo en cuanto existe la fila en BD.
- Migración `ON CONFLICT DO NOTHING` (auto-ejecutada por `_auto_migrate()`
  al arrancar la app) + seed para instalaciones nuevas — **no requiere
  ninguna acción manual en Supabase**.
- Badge de versión del sidebar → "V 12.28.0".

## 2026-07-31 (24)

### [Control Pedidos] v12.27.22 — Cabecera con logo también en emails de proveedor / internos de pedidos
- Petición del usuario: el logo aplicado en v12.27.19-21 solo cubría
  los emails de acceso/admin (verificación, Fase 1, Fase 2...). Faltaban
  los emails "de negocio" — proveedores y avisos internos de pedidos.
- Localizados 7 puntos de envío sin el patrón de cabecera con logo:
  enviado al proveedor, entrega parcial, pendiente de cotización,
  pendiente de firma (Dirección de Compras / Dirección del Hotel),
  cotización sin proveedor asignado, confirmación de recepción al
  proveedor y aviso interno de cambio de estado. Los 5 primeros tenían
  una banda de color plana sin logo; los 2 últimos no llevaban ninguna
  cabecera.
- Creada una única función `_email_header_html(...)` que genera la
  cabecera estándar (título/subtítulo a la izquierda, logo Princess a
  la derecha) — es ahora el único punto de configuración de la
  cabecera para todos los emails de la app, presentes y futuros.
  Las 7 plantillas se han migrado a usarla, respetando el color rojo
  (proveedor) o navy (interno) que ya tenían.
- Badge de versión del sidebar → "V 12.27.22".

## 2026-07-31 (23)

### [Control Pedidos] v12.27.21 — Fix: logo no aparecía en 3 de las 6 cabeceras + contraste del subtítulo
- Reportado con captura real del correo "[FASE 1] Nueva solicitud de
  acceso": la franja navy no mostraba el logo (ni siquiera el icono
  de imagen rota) y el subtítulo "Control de Pedidos · Princess
  Canarias" apenas se distinguía.
- Causa raíz del logo: 3 de las 6 plantillas tocadas en v12.27.20
  (Fase 1 a admins, alta desde el Organizador, Fase 2 completada)
  calculaban `app_url` con `os.environ.get("APP_URL", "")` — fallback
  vacío. Si la variable de entorno `APP_URL` no está definida en
  Render, el `src` de la imagen queda como ruta relativa
  (`/static/logo-sidebar.png`), que no resuelve dentro de un cliente
  de correo (no hay "página actual" de la que colgar la ruta) — de
  ahí que no se viera ni el icono de imagen rota, directamente no se
  intentaba cargar. Igualado el fallback en las 3 al mismo que ya
  usaban las otras 3 plantillas: `https://control-pedidos-princess.onrender.com`.
- Causa raíz del contraste: el subtítulo usaba
  `color:rgba(255,255,255,.6)`. Clientes de correo basados en el
  motor de Word (Outlook de escritorio clásico) son conocidos por
  ignorar `rgba()` en `color`, cayendo a un color por defecto poco
  legible sobre fondo navy. Cambiado a un hex sólido
  (`color:#b9c3dc`) en las 5 cabeceras que llevan subtítulo, para
  que se renderice igual en todos los clientes.
- Alcance: los 3 fallbacks de `app_url` corregidos son exactamente
  los mismos 3 tocados en v12.27.20 más el compacto de "Cuenta
  creada automáticamente" (que reutiliza el `app_url` ya corregido
  de la misma función). No se ha tocado el `app_url` de la línea
  5917 (usado solo para el enlace de fallback por Telegram, no
  aparece en el cuerpo del email).
- Badge de versión del sidebar actualizado a "V 12.27.21".
- Pendiente de confirmar tras desplegar: probar con una solicitud
  nueva (no un correo ya recibido antes del despliegue) para
  verificar que ahora sí carga el logo.

---

## 2026-07-31 (22)

### [Control Pedidos] v12.27.20 — Logo aplicado a todas las cabeceras de email restantes
- Petición: extender a todos el mismo tratamiento de logo aplicado en
  v12.27.19 al correo de "Verificación de acceso".
- Localizadas 6 plantillas de email con cabecera en banda de color +
  título + (opcional) subtítulo. Solo 3 son estrictamente "navy"
  (`#0f2044`): Fase 1 a admins, Fase 2 (hecha en v12.27.19) y
  bienvenida al usuario (ya tenía logo, pero en otra posición —
  ver abajo). Las otras 3 usan la misma estructura en verde (`#065f46`):
  alta desde el Organizador, Fase 2 completada, y el aviso compacto
  "Cuenta creada automáticamente" a admins. Se ha aplicado el mismo
  patrón a las 6, no solo a las navy, para que todo el sistema de
  emails quede visualmente consistente.
- Cabecera del email de bienvenida (única que ya llevaba logo)
  reconvertida al mismo patrón de tabla de dos columnas: antes el
  logo iba apilado arriba del título (38px, `margin-bottom`); ahora
  va a la derecha ocupando la franja completa (64px), igual que el
  resto.
- Aviso compacto "Cuenta creada automáticamente" (banda más baja,
  sin subtítulo) recibe un logo más pequeño (40px) con paddings
  proporcionalmente más ajustados (10px/20px) para no desbordar esa
  franja, que es más corta que las demás.
- `app_url` no estaba definida en el ámbito de la función de "Fase 2
  completada" (`solicitar_usuario_fase2`) — no hacía falta hasta
  ahora porque esa plantilla no usaba ninguna URL en el cuerpo del
  email. Añadida la asignación (`os.environ.get("APP_URL", "")`)
  justo antes del `body_html` para poder referenciar el logo.
- Todas las cabeceras usan ahora `<table>` de dos columnas en vez de
  `<div>` — más fiable en Outlook, que ignora flex/grid.
- Badge de versión del sidebar actualizado a "V 12.27.20".

---

## 2026-07-31 (21)

### [Control Pedidos] v12.27.19 — Logo en la cabecera del email de "Verificación de acceso" (Fase 2)
- Petición: añadir el logo a la cabecera navy del correo "Verificación
  de acceso" (el que lleva el enlace "Continuar verificación →" tras
  una solicitud de alta), agrandado y a la derecha de la franja,
  ocupando su alto.
- Corregido un matiz sobre el origen de esta plantilla: pese a que en
  la petición se atribuía a `_email_html_simple()`, ese correo en
  realidad se construye en `_construir_email_fase2()`, con su propia
  cabecera fija (`<div style="background:#0f2044...">`), estructuralmente
  igual a la del email de bienvenida pero sin logo. `_email_html_simple()`
  no lleva cabecera propia — solo genera el cuerpo (párrafos/botón) que
  se inserta en la plantilla externa de EmailJS, así que no era el sitio
  a tocar.
- Cabecera pasada de `<div>` a una `<table>` de dos columnas (más fiable
  en clientes de correo tipo Outlook, que ignoran flex/grid): columna
  izquierda con el título + subtítulo igual que antes, columna derecha
  con `<img src=".../logo-sidebar.png">` a 64px de alto, alineada a la
  derecha (`align="right"`, `margin-left:auto`).
- Alturas de padding cuadradas a propósito entre ambas columnas
  (texto: `24px 0 24px 28px`; logo: `14px 28px 14px 16px`) para que el
  logo quede centrado verticalmente y visualmente ocupe la franja
  completa con un margen de 14px arriba/abajo, en vez de tocar los
  bordes.
- Alcance: solo este correo (Fase 2 / verificación de acceso). El
  resto de plantillas con la misma cabecera navy sin logo (aviso Fase 1
  a admins, aviso de alta a admins, y las que use en el futuro
  `_email_html_simple()` si se le añade cabecera propia) se quedan
  igual, pendientes de que se pida explícitamente.
- Badge de versión del sidebar actualizado a "V 12.27.19".

---

## 2026-07-31 (20)

### [Control Pedidos] v12.27.18 — Aviso de nueva versión: sin cierre sin recargar + cuenta atrás
- Petición: tras el fix de v12.27.16 (pestañas obsoletas seguían
  despachando la cola de emails con lógica antigua), reforzar el
  propio aviso de nueva versión — que no se pueda cerrar sin recargar,
  y que se recargue sola pasados 5 minutos por si nadie está delante
  de la pantalla en ese momento.
- Quitado el botón "Ahora no" del modal — ahora solo queda "↻
  Recargar ahora". Comprobado que no había backdrop-click ni tecla
  Escape que lo cerrasen (el listener de Escape ya existente solo
  afecta a `modal-backup-log` y `modal-restore`, no a este).
- Eliminada `_cerrarModalVersion()` — era la única vía para
  descartar el aviso sin recargar (guardaba el hash de versión y
  ocultaba el modal sin más); sin uso una vez quitado el botón que la
  llamaba.
- Nuevo temporizador `_iniciarCuentaAtrasNuevaVersion()`: al mostrar
  el modal arranca una cuenta atrás de 5:00 minutos visible en el
  propio aviso (`<strong id="modal-nv-countdown-num">`); al llegar a
  0:00 llama sola a `_recargarConVersion()`. Guardado contra
  duplicados (`if (_nvCountdownTimer) return`) por si
  `_mostrarModalNuevaVersion()` se invoca más de una vez estando ya
  visible. Se limpia (`clearInterval`) si el usuario recarga a mano
  antes de que termine la cuenta atrás.
- Badge de versión del sidebar actualizado a "V 12.27.18"; entrada
  añadida en `CHANGELOG.md`.

---

## 2026-07-31 (19)

### [Control Pedidos] v12.27.16 — Fix: pestañas con versión desactualizada seguían despachando la cola de emails
- Detectado en pruebas reales: un email de "[FASE 1] Nueva solicitud
  de acceso" llegó al administrador en texto plano (con separadores
  `====`), pese a que el usuario confirmó que tanto `app.py` como
  `index.html` de v12.27.12 ya estaban desplegados (index desplegado
  primero, app.py después).
- Causa raíz encontrada revisando `_cerrarModalVersion()`: al pulsar
  "Ahora no" en el aviso de nueva versión, la pestaña actualiza su
  hash de versión conocido **sin recargar la página** — deja de
  avisar de nuevo, pero sigue ejecutando el JS antiguo indefinidamente.
  Ese correo de Fase 1 se envía automáticamente vía la cola
  `emails_sistema_pendientes`, despachada por "el primer admin que
  tenga la app abierta" — si esa pestaña es una que quedó desactualizada,
  usa la lógica antigua (`cuerpo_text` antes que `cuerpo_html`) sin que
  nadie se entere.
- Fix: `_mostrarModalNuevaVersion()` (punto único llamado desde los 4
  sitios donde se detecta versión nueva: chequeo al cargar, polling
  cada 30s/60s, `refreshCurrentView`) ahora para el timer del poller
  de emails de sistema (`_emailsSistemaPollTimer`) en cuanto se
  dispara — una pestaña obsoleta deja de despachar correos con lógica
  vieja; la cola queda pendiente para otra pestaña actualizada.
- No corrige el correo de Fase 1 ya enviado (histórico), solo evita
  que se repita hacia adelante.
- Badge de versión del sidebar actualizado a "V 12.27.16"; entrada
  añadida en `CHANGELOG.md`.

---

## 2026-07-31 (18)

### [Control Pedidos] v12.27.14 — Logo de empresa en el email de bienvenida
- Tras confirmar por captura que el email de "cuenta creada" ya
  llegaba con el HTML completo (cabecera navy, tarjeta de
  credenciales, botón dorado), se pidió añadir el logo de la empresa.
- Preguntado el alcance (solo este email vs. las ~5 plantillas con la
  misma cabecera navy): el usuario eligió limitarlo solo al email de
  bienvenida.
- Añadido `<img src="{app_url}/static/logo-sidebar.png">` en la
  cabecera de `body_html_u`, reutilizando el mismo logo que ya se usa
  en el sidebar de la app (pensado para fondo navy) y el mismo
  `app_url` que ya usaba esta función para el botón "Acceder al
  sistema" — necesario porque un email requiere URL absoluta.
- Badge de versión del sidebar actualizado a "V 12.27.14"; entrada
  añadida en `CHANGELOG.md`.

---

## 2026-07-31 (17)

### [Control Pedidos] v12.27.12 — Correos EmailJS en HTML real (antes texto plano)
- Motivo: los correos vía EmailJS salían en texto plano
  (`{{message}}`, doble llave) aunque casi todos los endpoints ya
  construían un `body_html` cuidado con estilos que se descartaba
  antes de llegar al frontend. El usuario cambió la plantilla EmailJS
  (`template_1zrv4ze`) a `{{{message}}}` (triple llave, sin escapar,
  en modo Code editor) para poder aprovecharlo.
- Backend (`app.py`): 3 endpoints que ya generaban `body_html` /
  `body_html_u` / `body_html_a` pero no lo devolvían en el JSON ahora
  sí lo incluyen (fase 2 completada → aviso admin; alta de
  usuario/admins al aprobar solicitud). Nuevo helper reutilizable
  `_email_html_simple()` para correos cortos tipo código/enlace, usado
  en el nuevo `body_html` del código de verificación de login (único
  caso que no tenía versión HTML previa).
- Frontend (`index.html`): los 8 puntos que llaman a
  `enviarEmailJS(...)` pasan a priorizar `body_html`/`cuerpo_html`
  sobre `body_text`/`cuerpo_text` en el campo `message` (login, reset
  de contraseña, fase 2, aprobar solicitud ×2, cambios de estado de
  pedido, preview de alerta manual, cola de emails de sistema).
- Verificado con capturas reales del usuario: plantilla EmailJS
  guardada correctamente con triple llave, campos `to_email` /
  `reply_to` / `bcc` alineados con el payload, y el email de
  bienvenida llegando ya con el HTML completo (cabecera navy, tarjeta
  de credenciales, botón).
- Fix adicional durante la verificación: quitado `white-space:
  pre-wrap` de la plantilla EmailJS (a petición, editado por el
  usuario) — con HTML real ese estilo hacía que el navegador respetara
  también los saltos de línea/indentación "de formato del código
  fuente" de los f-strings Python, duplicando el espaciado.
- Badge de versión del sidebar actualizado a "V 12.27.12"; entrada
  añadida en `CHANGELOG.md`.

---

## 2026-07-31 (16)

### [Control Pedidos] Verificación end-to-end del backup automático EmailJS — cerrado
- v12.27.10 desplegada y confirmada en el panel Admin → Config
  Alertas → EmailJS: cuenta 1 (principal) en uso con sus 3
  credenciales correctas, cuenta 2 (backup) rellena con la cuenta
  EmailJS anterior (`service_dwwha2g` / `template_krpvmda` /
  `WCiU7q8WT1i8AQTbR`).
- Prueba real solicitada al usuario: envío de una notificación real
  desde Alertas → el contador subió de 8 a 9 correctamente,
  confirmando que `enviarEmailJS()` + `/api/emailjs/registrar-envio`
  funcionan de punta a punta en producción (no solo la pantalla).
- Asunto cerrado: backup automático de cuenta EmailJS (contador,
  cambio bidireccional 1↔2 con reinicio, panel de administración e
  Integridad) queda dado por bueno en producción.

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
