# Historial de Cambios — Ecosistema Princess Compras (unificado)

> Documento único de seguimiento. Se actualiza cambio a cambio, entrada
> más reciente arriba. Componentes: **Organizador** (main_agenda,
> desktop), **Control Pedidos** (backend Flask principal), **Chat**
> (backend Flask/SocketIO independiente), **DALI** (catálogo de
> artículos/materiales — repo `dali-sap-articulos-app`, aparte pero
> integrado con Control Pedidos vía SSO desde el 2026-08-14, ver más
> abajo), **Infra** (Render / Cloudflare / GitHub Actions, no es código
> de la app).

> **Normas de entrega (obligatorias para cualquier cambio, ya lo
> implemente Claude, otra IA o cualquier programador humano):**
> 1. No se entrega el proyecto completo (ni el ZIP entero): solo los
>    archivos individuales modificados o creados, indicando su ruta
>    dentro del proyecto.
> 2. Toda entrega debe registrar una entrada nueva aquí (más reciente
>    arriba) y en `CHANGELOG.md`, describiendo petición, causa/hallazgo
>    y corrección aplicada.
> 3. `README.md`: la línea "Versión actual" se actualiza en **todas**
>    las entregas, sin excepción (no solo cuando el cambio es visible) —
>    quedó desincronizada 2 versiones seguidas (v12.30.82 y v12.30.83) por
>    no tratarla como obligatoria, ver entrada de la v12.30.83. Además,
>    el resto del README (funcionalidades, requisitos, secciones como
>    "Rendimiento") se actualiza si el cambio afecta a algo que documenta.
> 4. Subir el número de versión en el badge de `templates/index.html`
>    (formato `V MAJOR.MINOR.PATCH`), coherente con el de `CHANGELOG.md`
>    y esta entrada.
> 5. Revisar en cada entrega si el cambio afecta a algún otro documento
>    de mantenimiento del proyecto — `GUIA_DESPLIEGUE.md`,
>    `PENDIENTES.md`, `INSTRUCCIONES_RESTAURACION.md`,
>    `docs/hallazgo-seguridad-princess.md` — y actualizarlo si es así.
>    Dejar constancia en la entrada de este historial de qué se revisó,
>    aunque la conclusión sea "no aplica" (para que quede claro que se
>    comprobó y no que se olvidó).

---

## 2026-09-04 — [Control Pedidos] Auditoría completa a petición de Víctor: cerrado el `Decimal/float` fantasma de `PENDIENTES.md` + README puesto al día + 2 correcciones cosméticas (v12.32.22)

- **Petición de Víctor**: auditar el zip desplegado (v12.32.21) —
  verificar que todo está en su sitio, que no falta ningún archivo, y
  que la documentación está correctamente actualizada.
- **Resultado — estructura y código, todo correcto**: los 21 archivos
  completos (nada falta ni sobra frente al repo base), `app.py`
  compila sin errores, `templates/index.html` con balance correcto de
  `<div>` (958/958) y de `<script>` reales (9/9), versión consistente
  en badge/README/CHANGELOG, y verificados EN CÓDIGO (no solo en el
  CHANGELOG) los fixes de v12.32.06/15/19-21 (`KeyError: 0`,
  `NameError`, los tres `flush_cache()`).
- **1) `PENDIENTES.md` — entrada obsoleta desde v12.32.06, cerrada.**
  La entrada sobre un supuesto "nuevo" `TypeError: Decimal - float` en
  `[COMPARAR-ALBARANES]` (18:20:58/18:20:59, coincidencias
  `13093_336_35`/`13208_2041_41`) usaba EXACTAMENTE los mismos
  timestamps y códigos de coincidencia que el incidente original de
  los pedidos 40907/40908 de GY, ya corregido en v12.32.02/03 — no una
  recurrencia nueva, sino el mismo log histórico pegado de nuevo por
  error en algún momento. Confirmado con Víctor revisando el log de
  Render (Logs → buscar `COMPARAR-ALBARANES`, últimos 7 días):
  únicamente aparecen esas dos líneas del 3 de septiembre, ninguna
  posterior al despliegue del fix. Se retira la entrada.
- **2) `README.md` — puesto al día con lo añadido desde v12.32.05,
  nunca reflejado ahí.** Cada entrega desde entonces solo actualizaba
  la línea de versión, sin el bullet descriptivo correspondiente (a
  diferencia de la disciplina seguida hasta v12.30.99). Añadido: bullet
  de "Comparar Pedidos + Albaranes (SAP)" completo (creación automática
  de pedidos desde SAP v12.32.11/12/13, botón "Departamentos (SAP
  detallado)" v12.32.19, Sugerencias de Albarán confirmadas v12.32.20);
  nota de "un único documento" en Presupuesto dentro del bullet de
  Pedidos (v12.32.08); nota de "Telegram bloqueado o inservible" dentro
  del bullet de Integridad (v12.32.05).
- **3) `README.md` — corregida contradicción interna.** El bullet de
  "EmailJS y cola de correo" empezaba diciendo "las 3 cuentas EmailJS"
  pero el mismo párrafo explicaba después que son 4 desde v12.30.93 (el
  código ya usa 4 correctamente). Corregido a "4 cuentas".
- **4) `requirements.txt` — corregido comentario con nombre de función
  obsoleto.** Referenciaba `_parsear_listado_pedidos_detallado()`, que
  no existe con ese nombre; la función real es
  `_extraer_listado_detallado_completo()`.
- **Nota aparte, no corregida en esta entrega** (alcance mayor,
  requiere confirmación de Víctor antes de acometerla): "Comparar
  Pedidos + Albaranes (SAP)" es una funcionalidad mucho más antigua
  (desde v12.30.x) que tampoco tenía bullet propio en el README hasta
  ahora — se documentó de forma resumida centrada en lo añadido
  recientemente, pero un repaso completo de toda esa familia de
  funciones (incluyendo el flujo básico de comparación, anterior a
  septiembre) queda pendiente de valorar si merece más detalle.
- **Verificación**: `python3 -m py_compile app.py` sin errores (sin
  cambios en este archivo, se re-verifica por rutina). Sin cambios en
  `templates/index.html` más allá del badge de versión, ni en
  `models.py`.
- **Revisión de otros documentos (norma 5)**: `GUIA_DESPLIEGUE.md`,
  `INSTRUCCIONES_RESTAURACION.md` — no aplica, ninguno documenta estas
  funciones ni requiere cambios de despliegue.
- **Entrega**: `README.md`, `PENDIENTES.md`, `requirements.txt`,
  `templates/index.html` (solo versión), más este historial/
  `CHANGELOG.md`. `app.py` y `models.py` no cambian.

---

## 2026-09-04 — [Control Pedidos] Corrección de memoria: "Actualizar departamentos y líneas" podía tirar el servidor entero (y el job en curso) al subir un listado detallado de varios meses (v12.32.21)

- **Aviso de Víctor**, recién desplegada la v12.32.20: subiendo un listado de tres meses de golpe, tras un rato dio "El job no existe o ha caducado"; el quincenal de mayo dio el mismo error. El log de Render que pegó mostraba un reinicio completo del proceso justo entre dos consultas del mismo job.
- **Diagnóstico**: `_extraer_listado_detallado_completo()` (lector de "Actualizar departamentos y líneas", v12.32.16/18) era el único de los tres parsers de PDF grandes sin el `pagina.flush_cache()` que ya llevan los otros dos desde que se detectó el mismo problema con Albaranes (v12.32.19/20) — pdfplumber acumula memoria cacheada de cada página sin soltarla hasta cerrar el PDF entero. Confirmado con el PDF real de tres meses de Víctor (739 páginas): sin `flush_cache()`, el proceso llega a ~6,1 GB y el sistema lo mata (`oom-kill` en `dmesg`) sin terminar; en Render eso se lleva por delante el job en memoria, de ahí el "no existe o ha caducado" — y probablemente explica también que el quincenal de mayo fallara igual justo después, al caer mientras el servidor se reiniciaba, no porque el quincenal en sí pese tanto. Con `flush_cache()`, el mismo PDF de 739 páginas termina, con un pico de ~3,2 GB — mejor, aunque sigue siendo alto para varios meses de golpe (de ahí que el propio modal ya recomiende tramos quincenales; con 60-115 páginas el consumo baja en proporción).
- **Cambio en `app.py`**: una línea (`pagina.flush_cache()`) en `_extraer_listado_detallado_completo()`, mismo sitio que en los otros dos parsers. No cambia ningún resultado, solo libera memoria página a página.
- **Cambio en `templates/index.html`**: solo el número de versión del badge (norma 4) — sin cambios de interfaz.
- **Verificación**: `python3 -m py_compile app.py` sin errores. Prueba A/B aislada con el PDF real de tres meses: sin el fix, OOM a los ~6,1 GB sin terminar (confirmado por `dmesg`); con el fix, termina en 192s con ~3,2 GB de pico, 2.018 pedidos y 17.272 líneas correctas. No probado en vivo contra Render — a confirmar tras desplegar: repetir la subida del quincenal de mayo en solitario, y seguir subiendo históricos por tramos quincenales en vez de varios meses de golpe.
- **Sigue pendiente**: confirmar en Render que la subida quincenal ya no falla en solitario; si hiciera falta subir tramos de varios meses con frecuencia, valorar bajar más el consumo de memoria o subir el límite de la instancia.
- **Revisión de otros documentos (norma 5)**: `GUIA_DESPLIEGUE.md`, `INSTRUCCIONES_RESTAURACION.md`, `PENDIENTES.md`, `docs/hallazgo-seguridad-princess.md` — no aplica (corrección interna de memoria). `README.md` sí: versión actual.
- **Entrega**: `app.py`, `templates/index.html` (solo versión), `README.md`, más este historial/`CHANGELOG.md`. `models.py` y `requirements.txt` no cambian.

---

## 2026-09-04 — [Control Pedidos] Segundo paso del cruce Pedidos↔Albaranes: tier "confirmado" alimentado por el PDF de confirmación de un albarán suelto y por el nº de albarán ya registrado a mano en el pedido (v12.32.20)

- **Contexto**: tras v12.32.19, Víctor compartió un PDF ("97659.pdf") que demuestra que el programa de almacén SÍ puede imprimir, de uno en uno, un volcado de un albarán con el pedido asociado (campo "Pedido/s") — "PARA UN CASO PUNTUAL SI LO CREES CONVENIENTE", ya que no deja imprimir así por meses/proveedores. Reveló también que en Pedidos ya se anota a mano, al pasar a Entrega parcial/Total, el número de albarán y su base imponible (`entrada_albaran_num`), y preguntó si serviría también para la asociación. Confirmó que ese número es "el número de asiento DALI/SAP" — el mismo identificador que `sap_albaranes_lineas.albaran_id` (con o sin ceros a la izquierda). Ambas fuentes son asociaciones DIRECTAS, más fiables que la sugerencia por proveedor+artículo de v12.32.19.
- **Cambio en `app.py`**: `sap_albaranes_lineas` gana `pedido_num_sap_confirmado` (migración idempotente para bases ya en v12.32.19) + índices por `(hotel_id, albaran_id)` y `(hotel_id, pedido_num_sap_confirmado)`. `_extraer_albaran_confirmacion_individual()`: parser nuevo del PDF de confirmación de un albarán suelto (metadatos + líneas), extrae el/los pedido(s) de "Pedido/s". `_importar_albaran_confirmacion()`: guarda esas líneas con `pedido_num_sap_confirmado` relleno (reemplaza cualquier versión anterior del mismo albarán); si hay más de un pedido en el PDF (no visto todavía), usa el primero y avisa. `_sugerencias_albaran_pedido()` reescrita: añade un tier `confirmados` a partir de (a) `sap_albaranes_lineas.pedido_num_sap_confirmado` coincidente con el pedido, y (b) `pedidos.entrada_albaran_num` (ya existente) comparado por `albaran_id` normalizado; cada candidato de la tabla por línea gana un flag `confirmado`, ordenado primero, y deja de contar como "ambigua" una línea con un candidato confirmado. Endpoint nuevo `POST /api/albaranes/importar-confirmacion` (admin, síncrono — PDF de una página).
- **Cambio en `templates/index.html`**: tercer botón "📎 Confirmar un albarán suelto" (admin, con su modal hotel+PDF, envío directo sin job). "🔍 Sugerencias de Albarán" muestra ahora un bloque "🔒 Albarán(es) confirmado(s)" antes de la tabla por línea cuando los hay, y marca con 🔒 los candidatos confirmados dentro de esa tabla.
- **Verificación**: `python3 -m py_compile app.py` y `node --check` sobre los 8 bloques `<script>` (parser HTML real) sin errores. El parser del PDF de confirmación se verificó estructuralmente inspeccionando con pdfplumber el PDF real de Víctor, pero no se ejecutó en aislado como los parsers anteriores. No probado en vivo contra producción — a confirmar tras desplegar: subir un PDF real con "Confirmar un albarán suelto" y comprobar el resumen; comprobar que "Sugerencias de Albarán" muestra el bloque de confirmados para un pedido con `entrada_albaran_num` y albaranes ya importados.
- **Sigue pendiente**: el caso de un albarán con más de un pedido en el PDF de confirmación (no visto con datos reales); validar en uso real el tier confirmado por `entrada_albaran_num`; decidir si estas sugerencias se integran en la ficha del pedido una vez validadas.
- **Revisión de otros documentos (norma 5)**: `GUIA_DESPLIEGUE.md`, `INSTRUCCIONES_RESTAURACION.md`, `PENDIENTES.md`, `docs/hallazgo-seguridad-princess.md` — no aplica (mismo patrón que v12.32.19, sin cambios de despliegue/seguridad). `README.md` sí: versión actual.
- **Entrega**: `app.py`, `templates/index.html`, `README.md`, más este historial/`CHANGELOG.md`. `models.py` y `requirements.txt` no cambian.

---

## 2026-09-04 — [Control Pedidos] Primera entrega del cruce Pedidos↔Albaranes: importar el Listado de Albaranes de SAP y pedir sugerencias (no vinculantes) de con qué albarán se corresponde cada línea de un pedido (v12.32.19)

- **Contexto**: Víctor propuso clasificar el estado de entrega solo con la cantidad pendiente del listado detallado (sin depender del resumido), y por separado preguntó si se podía cruzar Pedidos con el nuevo Listado de Albaranes de SAP (adjuntó un ejemplo) para identificar qué albarán corresponde a qué pedido, ya que el propio programa de almacén no guarda esa relación. Antes de tocar código se hicieron pruebas empíricas con datos reales — con un giro importante a mitad de camino: las primeras pruebas mezclaban proveedores de alimentación/bebida/limpieza, que Víctor confirmó que quedan FUERA del alcance de esta app. Repetidas con el filtro correcto (proveedores `sujeto_seguimiento=TRUE` del catálogo, no una suposición por familia SAP) y una ventana más amplia (pedidos oct'25–mar'26 contra albaranes dic'25–may'26, ambos aportados por Víctor), el cruce por proveedor+código de artículo salió con 100% de cobertura, 17% de combinaciones ambiguas (media 2,4 candidatos) y 95,5% de coincidencia exacta en cantidad — base suficiente para construir la pantalla de sugerencias. La clasificación de estado de entrega por cantidad pendiente, en cambio, se queda sin datos suficientes en el alcance real de la app (18-55 pedidos según el filtro) para recomendarla — pendiente de más meses de listado resumido.
- De camino: script SQL para identificar proveedores `sujeto_seguimiento` (resuelto por chat, no es cambio de código) y, tras subir Víctor su exportación de códigos DALI, cruce por nombre para rellenar 45 de 46 proveedores que le faltaban en `proveedores.codigo_dali` (ejecutado por Víctor en Supabase).
- **Cambio en `app.py`**: tabla nueva `sap_albaranes_lineas` (proveedor, albarán, familia, código de artículo, cantidad, precio, importe, periodo) con índice `(hotel_id, codigo_articulo)` — guarda tal cual el Listado de Albaranes de Compra de SAP (jerárquico: Proveedor → Albarán → Familia → Subfamilia → Artículo), confirmado que NO trae el número de pedido SAP. `_extraer_albaranes_detallado_completo()`: parser nuevo (pdfplumber), extrae también el periodo de la cabecera del PDF. `_importar_albaranes_listado()`: guarda las líneas — si reconoce el periodo, reemplaza las de ese mismo hotel+periodo (subida idempotente); si no, inserta sin borrar y lo avisa. `_sugerencias_albaran_pedido()`: cruza las líneas de un pedido (`sap_pedidos_lineas`, v12.32.18) contra `sap_albaranes_lineas` por proveedor (normalizado con `_normalizar_nombre_proveedor()`, ya existente desde 2026-08-06 — reutilizada, no duplicada) + código de artículo; solo aplica si el proveedor está `sujeto_seguimiento`; marca coincidencias exactas por cantidad y líneas ambiguas si hay más de un candidato — sugerencia para revisar a mano, nunca escribe nada en el pedido. Endpoints nuevos, de solo lectura: `POST /api/albaranes/importar-listado` (+ estado del job, admin) y `GET /api/pedidos/<id>/sugerencias-albaran`.
- **Cambio en `templates/index.html`**: dos botones nuevos junto a "Departamentos y líneas" (admin) — "📥 Importar Albaranes (SAP detallado)" (mismo patrón de modal+job ya existente) y "🔍 Sugerencias de Albarán" (escribe el nº de pedido SAP, resuelve el pedido y muestra sus líneas con candidatos: ✅ coincidencia exacta / ❔ candidato dudoso / fila resaltada si hay varios).
- **Verificación**: `python3 -m py_compile app.py` sin errores; `node --check` sobre los 9 bloques `<script>` (extraídos con un parser HTML real) sin errores. Parser de Albaranes probado de forma aislada contra un listado real de mayo (263 páginas, 4.959 líneas, periodo detectado correctamente). No probado en vivo contra producción — a confirmar tras desplegar: subir un Listado de Albaranes real, comprobar el resumen, y probar "Sugerencias de Albarán" con un pedido conocido de un proveedor `sujeto_seguimiento` antes de confiar en la herramienta para más pedidos.
- **Sigue pendiente**: 1 proveedor sin código DALI encontrado (ALL SPORT ALTERNATIVAS DEPORTIVAS S); ampliar la prueba de clasificación por cantidad pendiente con más meses si se quiere retomar; decidir si las sugerencias se integran también dentro de la ficha del pedido una vez validadas en uso real.
- **Revisión de otros documentos (norma 5)**: `GUIA_DESPLIEGUE.md`, `INSTRUCCIONES_RESTAURACION.md`, `PENDIENTES.md` — no aplica. `README.md` sí: versión actual.
- **Entrega**: `app.py`, `templates/index.html`, `README.md`, más este historial/`CHANGELOG.md`. `models.py` y `requirements.txt` no cambian.

---

## 2026-09-04 — [Control Pedidos] Primer paso de "trazabilidad casi perfecta" — se guarda el contenido línea a línea del Listado de Pedidos DETALLADO, en la misma subida que rellena el departamento (v12.32.18)

- **Petición de Víctor**: antes de lanzarse con el histórico desde el 01-01-2026, preguntó si —ya que su idea de guardar el contenido línea a línea (pospuesta como proyecto aparte en v12.32.16) usa el mismo listado detallado que el departamento— convenía construir eso primero y hacer el histórico en un único pase, en vez de subir los mismos PDF dos veces.
- **Respuesta**: viable, pero acotado — solo la parte del listado DETALLADO se beneficia de ir junta; la parte del RESUMIDO (crear pedidos que faltan, importe/estado) no depende de esto y puede empezar ya en paralelo. Preguntado el alcance de esta entrega, Víctor eligió la opción recomendada: solo guardar los datos, sin ninguna pantalla ni comparación todavía.
- **Cambio en `app.py`**: tabla nueva `sap_pedidos_lineas` (código, descripción, unidad, cantidades pedida/recibida/pendiente, fechas, precio, descuento, importe, departamento) — sin `UNIQUE` por artículo, porque un mismo artículo puede aparecer en más de una línea del mismo pedido (verificado: 16/485 pedidos de prueba); cada subida borra e inserta de nuevo las líneas de cada pedido, evitando duplicados. `_extraer_departamentos_listado_detallado()` (v12.32.16) se sustituye por `_extraer_listado_detallado_completo()`, que en la MISMA pasada por el PDF devuelve también las 11 columnas completas de cada línea (no solo el departamento), evitando doblar el tiempo de lectura. `_actualizar_departamentos_desde_listado_detallado()` gana un tercer paso que guarda las líneas de cada pedido del PDF — sin depender de que el pedido ya tenga fila en `sap_pedidos_listado` (a diferencia del departamento). El resumen de cada subida informa también cuántas líneas se guardaron.
- **Cambio en `templates/index.html`**: botón/modal renombrados a "Departamentos y líneas (SAP detallado)"; resumen del resultado con indicador de líneas guardadas.
- **Verificación**: `python3 -m py_compile app.py` y `node --check` sin errores. Probada la extracción real contra los dos quincenales de mayo de Víctor: 485 pedidos, 4.234 líneas, 0 sin código de artículo, 0 sin departamento resuelto; el pedido 39177 vuelve a sumar exactamente 253,90 € entre sus dos líneas. No probado en vivo el guardado en BD — a confirmar tras desplegar.
- **Sigue pendiente**, sin cambios de plan: la comparación de estas líneas contra el Listado de Albaranes a nivel de referencia — proyecto aparte, todavía por diseñar.
- **Revisión de otros documentos (norma 5)**: `GUIA_DESPLIEGUE.md`, `INSTRUCCIONES_RESTAURACION.md`, `PENDIENTES.md` — no aplica. `README.md` sí: versión actual.
- **Entrega**: `app.py`, `templates/index.html`, `README.md`, más este historial/`CHANGELOG.md`. `models.py` y `requirements.txt` no cambian.

---

## 2026-09-04 — [Control Pedidos] Actualización histórica masiva sin riesgo de avisos en cadena — pausa global de alertas + el departamento se propaga al pedido al momento (v12.32.17)

- **Petición de Víctor**, al ir a subir quincenas del listado detallado desde el 01-01-2026: (1) si el orden de subida importa o hay que cubrir primero los pedidos ya auto-creados; (2) poder pausar avisos/correos internos/correos a proveedores durante la actualización masiva, porque temía que "actualizar departamentos" disparase correos de pedidos ya entregados.
- **Sobre el orden**: no importa — el emparejamiento es por número de pedido, no por fecha; solo hace falta que el listado resumido de ese periodo ya tenga fila guardada (siempre cierto para los pedidos auto-creados, que nacen de esa misma tabla). Si falta para algún pedido manual, el resumen de la subida lo avisa aparte y basta con repetirla más tarde.
- **Hallazgo corregido en la misma entrega**: `_actualizar_departamentos_desde_listado_detallado()` (v12.32.16) solo rellenaba `sap_pedidos_listado.departamento_sap_codigo` — el departamento del pedido YA dado de alta en la app solo se completaba en el backfill de `_auto_migrate()`, que corre una vez por despliegue. Con el plan de Víctor de subir muchas quincenas sueltas en el tiempo, eso habría requerido un redeploy tras cada tanda. **Cambio en `app.py`**: ahora, tras guardar el código en `sap_pedidos_listado`, si el pedido correspondiente ya existe y no tiene departamento, se le asigna al momento (nunca pisa uno ya puesto; no cambia `estado` ni `fecha_tramitacion`, así que no dispara ningún email/aviso). El resumen de cada subida informa también cuántos pedidos ya dados de alta se completaron.
- **Cambio en `app.py`**: nueva clave `pausa_avisos_automaticos` en `config_alertas` (visible en Administrador → Parámetros de alertas, sin cambios de interfaz — el panel ya lee la tabla de forma genérica), comprobada al principio de `_job_alertas_diarias_inner()`: si está activa, corta el job entero — ni Telegram a compradores, ni reclamación automática por email a proveedores, ni aviso de firma pendiente. Al reactivarla, el job vuelve a evaluar el estado real de cada pedido sin nada que "recuperar".
- **Verificación**: `python3 -m py_compile app.py` y `node --check` sin errores. No probado en vivo — a confirmar tras desplegar: activar la pausa antes de subir el histórico, revisar el resumen de cada subida, y desactivarla al terminar.
- **Revisión de otros documentos (norma 5)**: `GUIA_DESPLIEGUE.md`, `INSTRUCCIONES_RESTAURACION.md`, `PENDIENTES.md` — no aplica. `README.md` sí: versión actual.
- **Entrega**: `app.py`, `templates/index.html`, `README.md`, más este historial/`CHANGELOG.md`. `models.py` y `requirements.txt` no cambian.

---

## 2026-09-04 — [Control Pedidos] Departamento automático del Listado de Pedidos SAP — vía el listado DETALLADO, en flujo aparte, sin tocar importe/estado (v12.32.16)

- **Petición de Víctor**, adjuntando dos exportaciones reales de SAP: la que ya se usa (GY, simplificada — una línea por pedido) y una segunda (GY1, detallada — una línea por artículo, con el departamento solicitante) — preguntó si la segunda podría sustituir a la primera para aplicar automáticamente el departamento.
- **Investigación previa**: se verificó contra 2.138 pedidos reales que el departamento se extrae al 100% de fiable del listado detallado (con `pdfplumber`, no `pypdf` — este último desordena las columnas en tablas reales como esta). Pero sustituir POR COMPLETO el listado simplificado, reconstruyendo `importe_recibido`/`importe_pendiente` sumando cantidad×precio de cada línea de artículo, se probó y se descartó: contra 409 pedidos reales, esa reconstrucción no cuadra siempre al céntimo con lo que reporta SAP, y en ~2% de los casos (8/409) eso cambia la clasificación Entregado ↔ Entrega parcial — el mismo tipo de fallo que causó el incidente real de v12.32.13. Se le explicó a Víctor con el ejemplo concreto; confirmó seguir con el enfoque híbrido ("Termino primero el departamento automático").
- **Mapeo de departamentos** (decidido por Víctor sobre los 11 códigos reales del listado): COCINA PERSONAL → COCINA; SSTT → SERVICIO TECNICO; RESTAURANTE/RESTAURANTE & BARES → RESTAURANTE / BODEGA (Food Market); BAR SALON → BARES; más dos departamentos nuevos, **LAVANDERIA / LENCERIA** y **UNIFORMES PERSONAL**.
- **Cambio en `app.py`**: `_SAP_DEPARTAMENTO_MAP` (mapeo código→departamento); `sap_pedidos_listado` gana la columna `departamento_sap_codigo`; `departamentos` gana los dos departamentos nuevos; `_extraer_departamentos_listado_detallado()` (parser nuevo con `pdfplumber`, con arreglo para cabeceras de pedido que caen en el borde de página); `_actualizar_departamentos_desde_listado_detallado()` (UPDATE dirigido SOLO a `departamento_sap_codigo`, solo de pedidos que ya tienen fila en `sap_pedidos_listado` — nunca inserta ni toca importe/estado); endpoint nuevo `POST /api/pedidos/actualizar-departamentos-listado` con job en segundo plano (mismo patrón `_PDF_JOBS` que "Comparar listado PDF"); el `UPSERT` de `_guardar_listado_sap_importado()` usa `COALESCE` para que una subida del listado simplificado nunca borre un departamento ya puesto por el detallado; backfill retroactivo en `_auto_migrate()` para pedidos ya creados desde SAP sin departamento; `crear_pedidos_desde_sap()` rellena el departamento si ya se conoce.
- **Cambio en `templates/index.html`**: botón nuevo "🏷️ Departamentos (SAP detallado)" (solo admin) con su modal de subida y resumen de resultado.
- **Cambio en `requirements.txt`**: se añade `pdfplumber` (y transitivas) — solo para leer el listado detallado.
- **Verificación**: `python3 -m py_compile app.py` y `node --check` sin errores. Probada la extracción real (fuera de la app) contra los PDF de Víctor: 485 pedidos reconocidos en los dos listados quincenales de mayo (63+114 páginas) con departamento resuelto al 100% y ningún código sin mapear; el listado simplificado del mismo mes reconoce también 485 pedidos y el importe del pedido 39177 sale exactamente 253,90 € (el mismo valor que Víctor verificó a mano). No probado en vivo el flujo de subida — a confirmar tras desplegar: subir un listado detallado real y revisar el resumen, y comprobar el departamento de algún pedido dado de alta automáticamente.
- **Pendiente, a petición de Víctor** (proyecto aparte, pospuesto): almacenar el contenido línea a línea de cada pedido para poder cruzar en el futuro con los Albaranes a nivel de artículo/referencia ("trazabilidad casi perfecta") — pendiente de diseñar.
- **Revisión de otros documentos (norma 5)**: `GUIA_DESPLIEGUE.md`, `INSTRUCCIONES_RESTAURACION.md`, `PENDIENTES.md` — no aplica. `README.md` sí: versión actual.
- **Entrega**: `app.py`, `templates/index.html`, `README.md`, `models.py`, `requirements.txt`, más este historial/`CHANGELOG.md`.

---

## 2026-09-04 — [Control Pedidos] URGENTE (segundo intento): la corrección retroactiva seguía sin ejecutarse — `NameError` por llamar a funciones aún no definidas, lógica reescrita en línea (v12.32.15)

- **Detectado por Víctor**: tras desplegar v12.32.14 (badge ya "V 12.32.14"), la Línea temporal seguía mostrando exactamente los mismos pedidos sin corregir. Se le pidió el log completo de arranque de Render para no seguir a ciegas; el log reveló: `WARNING No se pudo ejecutar la corrección retroactiva de pedidos creados desde SAP (v12.32.13): name '_parse_importe_es' is not defined`.
- **Causa raíz (distinta de la de v12.32.14)**: `_auto_migrate()` se invoca a nivel de módulo (`with app.app_context(): _auto_migrate()`) justo debajo de su propia definición, cerca del principio de `app.py` — es decir, se ejecuta DURANTE la importación del archivo, antes de que Python llegue a las definiciones (mucho más abajo) de `_parse_importe_es()` y `_entrega_estado()`. Llamarlas desde dentro de `_auto_migrate()` no podía funcionar en ninguna posición del bloque. Además, al compartir todo el bucle `for _p in _afectados` un único try/except, el `NameError` en el primer pedido abortaba también los pasos que no dependían de esas funciones (nombre automático, purga de reclamaciones) para el resto del lote.
- **Cambio en `app.py`**: las llamadas a `_parse_importe_es()`/`_entrega_estado()` se sustituyen por dos funciones locales (`_parse_importe_es_local`, `_entrega_estado_local`) definidas dentro del propio bloque, con la lógica copiada en línea — sin depender de nada definido más abajo en el archivo. El cuerpo del bucle por pedido pasa a tener su propio try/except (`except Exception as exc_p`), igual que el patrón ya usado en el bloque de RLS: un pedido con datos raros ya no bloquea la corrección del resto del lote.
- **Verificación**: `python3 -m py_compile app.py` sin errores. Repasada a mano la equivalencia de las funciones locales con las originales. No probado en vivo — dado que es el tercer intento (v12.32.13 no llegó a ejecutarse, v12.32.14 llegó pero falló con NameError), se recomienda verificar tras desplegar buscando en los logs `Auto-migración OK` sin ningún `WARNING No se pudo ejecutar la corrección retroactiva`, y/o recargando la Línea temporal de los pedidos de las capturas para confirmar nombre automático y estado corregidos.
- **Revisión de otros documentos (norma 5)**: `GUIA_DESPLIEGUE.md`, `INSTRUCCIONES_RESTAURACION.md`, `PENDIENTES.md` — no aplica. `README.md` sí: versión actual.
- **Entrega**: `app.py`, `templates/index.html` (solo el número de versión del badge), `README.md`, más este historial/`CHANGELOG.md`. `models.py` y `requirements.txt` no cambian.

---

## 2026-09-04 — [Control Pedidos] URGENTE: la corrección retroactiva de v12.32.13 nunca se ejecutó — movida al principio de `_auto_migrate()` (v12.32.14)

- **Detectado por Víctor**: tras desplegar y arrancar con v12.32.13, la Línea temporal seguía mostrando los pedidos afectados con el nombre del admin y sin ningún registro de corrección de estado — la corrección retroactiva no se había aplicado.
- **Causa raíz**: `_auto_migrate()` tiene 111+ sentencias sin try/except propio dentro de un único try/except general — un fallo en cualquiera de ellas aborta toda la función a partir de ahí. La corrección de v12.32.13 se colocó al final, justo antes de `db.close()`, así que si algo anterior fallaba en ese arranque concreto, nunca llegaba a ejecutarse. Mismo patrón de fallo ya documentado en el código para un bug real de RLS en agosto de 2026, corregido entonces igual.
- **Cambio en `app.py`**: el bloque de corrección se mueve al principio de `_auto_migrate()`, justo tras el bloque de RLS — misma lógica exacta que en v12.32.13, solo cambia su posición para garantizar que se ejecute siempre.
- **Verificación**: `python3 -m py_compile app.py` sin errores; confirmado que no queda ningún duplicado ni resto huérfano en la ubicación anterior. No probado en vivo — a confirmar tras desplegar revisando la Línea temporal de los pedidos afectados.
- **Revisión de otros documentos (norma 5)**: `GUIA_DESPLIEGUE.md`, `INSTRUCCIONES_RESTAURACION.md`, `PENDIENTES.md` — no aplica. `README.md` sí: versión actual.
- **Entrega**: `app.py`, `templates/index.html`, `README.md`, más este historial/`CHANGELOG.md`. `models.py` y `requirements.txt` no cambian.

---

## 2026-09-04 — [Control Pedidos] URGENTE: corregido el estado mal calculado al crear pedidos desde SAP — disparaba reclamaciones reales a proveedores ya entregados (v12.32.13)

- **Petición de Víctor**, con capturas: los pedidos creados por la nueva automatización (v12.32.11) salían todos en "ENVIADO AL PROVEEDOR" en vez del estado real que ya mostraba el listado SAP, y eso disparó reclamaciones automáticas REALES a proveedores de pedidos ya entregados ("me están tupiendo a llamadas"). Además pidió que la trazabilidad de estas altas usara el nombre automático fijo, no el del admin.
- **Causa raíz**: al llevar `fecha_tramitacion` real (a veces de meses atrás) y quedarse en "ENVIADO AL PROVEEDOR", el job diario de alertas los trataba como gravemente retrasados y encolaba reclamaciones reales al proveedor + avisos internos.
- **Cambio en `app.py` (`crear_pedidos_desde_sap`)**: el estado inicial ahora se calcula con `_entrega_estado()` desde el propio listado SAP — Entregado/Entrega parcial/Enviado al proveedor según corresponda; un pedido ya Entregado queda fuera del job de alertas por completo. Trazabilidad corregida al texto fijo `"Automática — alta desde listado de pedidos SAP"` (mismo criterio que `_aplicar_coincidencia_albaran`).
- **Corrección retroactiva en `_auto_migrate()`**: para los pedidos ya creados mal con la v12.32.11 — corrige nombre de "creado por" e historial siempre; recalcula y corrige el estado solo si nadie lo tocó a mano desde el alta; purga de la cola cualquier reclamación automática todavía sin enviar para esos pedidos. Idempotente.
- **Cambio en `templates/index.html`**: textos del modal actualizados (ya no prometen siempre "Enviado al proveedor"); el refresco tras crear usa el estado real devuelto por el backend.
- **Verificación**: `python3 -m py_compile app.py` y `node --check` sin errores. No probado en vivo — a confirmar tras desplegar: revisar que los pedidos creados con v12.32.11 quedan con el estado correcto y que no quedan reclamaciones automáticas pendientes en la cola para ellos.
- **Revisión de otros documentos (norma 5)**: `GUIA_DESPLIEGUE.md`, `INSTRUCCIONES_RESTAURACION.md`, `PENDIENTES.md` — no aplica. `README.md` sí: versión actual.
- **Entrega**: `app.py`, `templates/index.html`, `README.md`, más este historial/`CHANGELOG.md`. `models.py` y `requirements.txt` no cambian.

---

## 2026-09-04 — [Control Pedidos] Crear pedidos desde SAP: ya no se ofrece al comparar solo Albaranes (v12.32.12)

- **Petición de Víctor**: "si se detecta nuevo pedido al comprar el listado de albaranes, pienso que mas podria ser un error que un nuevo pedido, solo realizar esta gestion de crear nuevos pedidos con el listado de pedidos y no de albaranes".
- **Antes (v12.32.11)**: la sección de creación automática se actualizaba también al terminar una comparación hecha solo con el listado de Albaranes (reutilizando el Listado de Pedidos guardado, sin leer uno nuevo) y al elegir hotel, sin haber comparado nada todavía.
- **Cambio en `templates/index.html`**: `_cargarPedidosPendientesCrearSap()` ahora solo se dispara tras procesar de verdad un PDF nuevo del Listado de Pedidos — en la comparación de un solo PDF siempre, y en la comparación combinada con Albaranes solo si esa comparación incluyó un PDF nuevo de Pedidos (dentro del `if (auditoria)`). Se quita la llamada al elegir hotel. Sin cambios en `app.py`.
- **Verificación**: `node --check` sin errores. `python3 -m py_compile app.py` sin errores (sin cambios, re-verificado por rutina).
- **Revisión de otros documentos (norma 5)**: `GUIA_DESPLIEGUE.md`, `INSTRUCCIONES_RESTAURACION.md`, `PENDIENTES.md` — no aplica. `README.md` sí: versión actual.
- **Entrega**: `templates/index.html`, `README.md`, más este historial/`CHANGELOG.md`. `app.py`, `models.py` y `requirements.txt` no cambian.

---

## 2026-09-04 — [Control Pedidos] "Comparar listado PDF (SAP)": creación automática de los pedidos que faltan por dar de alta (v12.32.11)

- **Petición de Víctor**: automatizar la creación de los pedidos que SAP ya tiene pero la app no — mostrando antes el listado (como el resumen de correo) para seleccionar y aceptar, dejando el resto de documentación pendiente de subir; que se registre la fecha de tramitación, la fecha de entrega predefinida y el número de pedido, "toda aquella info que tengamos con este listado". Aclarado con tres preguntas: (1) estado inicial siempre "Enviado al proveedor", nunca el de entrega de SAP; (2) solo se puede crear si el proveedor está identificado en el catálogo; (3) el importe (Total Pedido) también se rellena solo.
- **Cambio en `app.py`**: `_pedidos_sap_no_registrados(hotel_id)` calcula al vuelo, desde el listado SAP ya guardado, qué pedidos faltan por dar de alta (solo lectura). Nuevo `GET /api/pedidos/pendientes-crear-sap/<hotel_id>` para consultarlo sin comparar ningún PDF. Nuevo `POST /api/pedidos/crear-desde-sap` que crea las fichas seleccionadas (número, fecha de tramitación, fecha de entrega prevista, proveedor e importe desde SAP; departamento/presupuesto/adjuntos quedan pendientes), re-comprobando en el momento por si alguien ya dio de alta alguno a mano. **No llama a `enviar_emails_estado()`** aunque el estado sea "ENVIADO AL PROVEEDOR": ese correo es para pedidos nuevos de verdad, y estos ya existían en SAP — mandarlo sería un aviso duplicado al proveedor real. Registra el alta en `historial_estados`.
- **Cambio en `templates/index.html`**: nueva sección "Crear automáticamente los pedidos de SAP sin dar de alta" en el modal de comparación, con tabla seleccionable (checkbox, solo habilitado con proveedor identificado) y botón de creación masiva — se actualiza al elegir hotel y al terminar cualquiera de las dos comparaciones, siempre desde el listado guardado.
- **Verificación**: `python3 -m py_compile app.py` y `node --check` sin errores. Repasado el mapeo de campos contra el esquema real de `pedidos` (columnas de `_auto_migrate()` incluidas) y el dominio de `estado`. No probado en vivo contra producción — a confirmar tras desplegar.
- **Revisión de otros documentos (norma 5)**: `GUIA_DESPLIEGUE.md`, `INSTRUCCIONES_RESTAURACION.md`, `PENDIENTES.md` — no aplica. `README.md` sí: versión actual.
- **Entrega**: `app.py`, `templates/index.html`, `README.md`, más este historial/`CHANGELOG.md`. `models.py` y `requirements.txt` no cambian.

---

## 2026-09-04 — [Control Pedidos] "Comparar listado PDF (SAP)": listado de SAP guardado por hotel, ya no hace falta re-subirlo en cada comparación con Albaranes (v12.32.10)

- **Petición de Víctor**: cargar el Listado de Pedidos de SAP (varios meses) una vez, que la app lo guarde, y a partir de ahí ir pasando solo el Listado de Albaranes para ir contrastando y cerrando información. Aclarado: un único modal con el PDF de SAP opcional, y cada subida nueva FUSIONA con lo ya guardado (no lo reemplaza).
- **Cambio en `app.py`**: nueva tabla `sap_pedidos_listado` (upsert por hotel_id+pedido_num_sap) con `_guardar_listado_sap_importado()`/`_cargar_listado_sap_guardado()`; se guarda automáticamente en cualquier lectura de un PDF de SAP (con o sin Albaranes). `_comparar_listado_albaranes_logica()` acepta el primer PDF como opcional, usando el listado guardado si se omite (error claro si nunca se guardó ninguno para ese hotel); la auditoría completa de SAP solo se recalcula cuando hay un PDF nuevo. Nuevo endpoint `GET /api/pedidos/listado-sap-guardado/<hotel_id>`.
- **Cambio en `templates/index.html`**: con "Comparar también con Albaranes" marcado, el campo de SAP deja de ser obligatorio y se informa (al elegir hotel/marcar la casilla) de si hay listado guardado y de cuándo.
- **Verificación**: `python3 -m py_compile app.py` y `node --check` sin errores. Formato de los PDF de ejemplo de Víctor (GY.pdf/GY2.pdf) comprobado contra los patrones existentes. No probado en vivo contra producción — a confirmar tras desplegar.
- **Revisión de otros documentos (norma 5)**: `GUIA_DESPLIEGUE.md`, `INSTRUCCIONES_RESTAURACION.md`, `PENDIENTES.md` — no aplica. `README.md` sí: versión actual.
- **Entrega**: `app.py`, `templates/index.html`, `README.md`, más este historial/`CHANGELOG.md`. `models.py` y `requirements.txt` no cambian.

---

## 2026-09-04 — [Control Pedidos] Integridad → "Telegram bloqueado": fecha "Invalid Date" y motivo en JSON crudo, corregidos (v12.32.09)

- **Petición de Víctor**, con captura real del panel (comprascan6/María Cruz): "el motivo y bloqueado desde deberia aparecer mas claro y detallado".
- **"Bloqueado desde" → Invalid Date**: `_validar_integridad_operativa()` no convertía `telegram_bloqueado_en` (TIMESTAMPTZ) a ISO antes de servirlo, a diferencia del resto de fechas de la app; el frontend además le concatenaba una `'Z'` a mano, patrón solo válido para fechas "naive" como `data.timestamp`. Arreglado en ambos lados: backend con `.isoformat()`, frontend sin la `'Z'` de más (mismo patrón que `new Date(r.creado_en)` en el resto de la app).
- **"Motivo" → JSON crudo**: nueva función `_describir_motivo_telegram_bloqueo()` (`app.py`) que traduce las 5 causas conocidas a una frase clara en español + el detalle técnico real (código HTTP + descripción de Telegram) — comparte la lista de frases con `_send_telegram()` para que no se desincronicen. Backfill automático en `_auto_migrate()` para los motivos ya guardados en JSON crudo (incluye el caso real de comprascan6).
- **Cambio en `templates/index.html`**: celda de "Motivo" con más aire (letra algo mayor, salto de línea normal).
- **Verificación**: `python3 -m py_compile app.py` y `node --check` sin errores. Reproducido en local el JSON exacto del caso de Víctor. No probado en vivo contra producción — a confirmar tras desplegar.
- **Revisión de otros documentos (norma 5)**: `GUIA_DESPLIEGUE.md`, `INSTRUCCIONES_RESTAURACION.md`, `PENDIENTES.md` — no aplica. `README.md` sí: versión actual.
- **Entrega**: `app.py`, `templates/index.html`, `README.md`, más este historial/`CHANGELOG.md`. `models.py` y `requirements.txt` no cambian.

---

## 2026-09-03 — [Control Pedidos] Presupuesto: solo un documento de apoyo (PDF, Word o correo) con aviso flotante si se intenta un segundo (v12.32.08)

- **Petición de Víctor**: en el apartado Presupuesto quiere permitir adjuntar un PDF, un Word o un correo, pero solo uno de los tres — y que al intentar poner un segundo salte un aviso flotante detallado y profesional, con el mismo estilo que el aviso de "Acceso restringido" cuando un rol sin permiso entra en un apartado de admin.
- **Antes**: Presupuesto admitía, como Solicitud y Firma de techo, hasta 3 documentos + 1 correo a la vez (4 archivos combinados), y el selector permitía elegir varios de golpe.
- **Cambio en `templates/index.html`**: se quita `multiple` del selector de archivo de Presupuesto; `subirAdjuntos()` comprueba, solo para este apartado, si ya hay un adjunto o se han elegido varios archivos a la vez, y si es así cancela la subida y muestra `showFormAlert(...)` — el mismo patrón visual que `_showSbAccessToast` ("Acceso restringido"), con título, mensaje y detalle de qué hacer.
- **Cambio en `app.py` (`upload_adjunto`)**: comprobación real en el backend — para `presupuesto_doc` se cuenta cualquier adjunto ya existente (documento o correo) y se rechaza el segundo con un 400 y mensaje claro. Solicitud y Firma de techo no cambian.
- **Verificación**: `python3 -m py_compile app.py` y `node --check` sobre los bloques `<script>` de `subirAdjuntos`, sin errores. No probado en vivo contra producción — a confirmar tras desplegar.
- **Revisión de otros documentos (norma 5)**: `GUIA_DESPLIEGUE.md`, `INSTRUCCIONES_RESTAURACION.md`, `PENDIENTES.md` — no aplica. `README.md` sí: versión actual.
- **Entrega**: `app.py`, `templates/index.html`, `README.md`, más este historial/`CHANGELOG.md`. `models.py` y `requirements.txt` no cambian.

---

## 2026-09-03 — [Control Pedidos] Fix: "Nuevo pedido" arrastraba el Techo de gastos del pedido anterior (v12.32.07)

- **Petición de Víctor**: al activar "Techo de gastos" en un pedido, cerrarlo y crear uno nuevo, la casilla y los valores (familia, importe) del pedido anterior seguían ahí y el techo quedaba activado sin querer.
- **Diagnóstico**: `openPedidoModal()` solo rellena la casilla y campos de techo al **editar** (`if (id) {...}`); en un pedido nuevo dependía de `clearPedidoForm()`, que resetea el resto de checkboxes del formulario pero nunca tocaba `p-sujeto-techo` ni sus campos — se quedaban con lo último que hubiera en el DOM. Al guardar, el pedido nuevo se registraba computando para el techo por error.
- **Cambio en `templates/index.html`**:
  - `clearPedidoForm()`: desmarca `p-sujeto-techo`, oculta `techo-fields` y `techo-preview`, vacía familia/importe.
  - `openPedidoModal()`: se añade `firma-techo` a la limpieza de adjuntos (le faltaba, mismo problema con los documentos de apoyo a la firma de techo).
- **Verificación**: `node --check` sobre los bloques `<script>` afectados, sin errores. No probado en vivo contra producción (sin backend/BD disponible desde aquí) — a confirmar tras desplegar: activar techo con familia/importe, cerrar el pedido, abrir uno nuevo y comprobar que sale todo limpio.
- **Revisión de otros documentos (norma 5)**: `GUIA_DESPLIEGUE.md`, `INSTRUCCIONES_RESTAURACION.md`, `PENDIENTES.md` — no aplica (encontrado y corregido en la misma entrega). `README.md` sí: versión actual.
- **Entrega**: `templates/index.html`, `README.md`, más este historial/`CHANGELOG.md`. `app.py`, `models.py` y `requirements.txt` no cambian.

---

## 2026-09-03 — [Control Pedidos] Fix `KeyError: 0` en Auto-migración (causa raíz) + logging con traceback completo para el `Decimal`/`float` de Comparar-Albaranes (v12.32.06)

- **Petición de Víctor**: preguntó qué arreglos quedan pendientes,
  pegando log del día con el `KeyError: 0` de Auto-migración repitiéndose
  varias veces y dos nuevas apariciones del `TypeError: Decimal - float`
  en `[COMPARAR-ALBARANES]`; también preguntó por qué no ve la tarjeta
  "Telegram bloqueado" en Integridad.
- **Sobre Integridad**: la comprobación de la v12.32.05 funciona
  correctamente — 0 problemas ahora mismo, por eso se pliega en la línea
  verde "✅ Sin problemas en: ..." (igual que cualquier otra categoría
  sin incidencias) en vez de aparecer como tarjeta propia; el propio
  texto "Telegram bloqueado o inservible" ya aparece ahí en sus capturas.
- **Cambio en `app.py`**:
  - `KeyError: 0` en `_auto_migrate()`: causa raíz localizada — dos
    sentencias de seeding de `notificaciones_config` leían
    `cur.fetchone()[0]`, pero esa conexión usa `cursor_factory=
    RealDictCursor` (resultado indexado por nombre de columna, no por
    posición). Corregido aliasando `SELECT COUNT(*) AS n ...` y leyendo
    `cur.fetchone()["n"]`. Mismo patrón de bug ya cubierto
    defensivamente en otros dos puntos de la función; coincide con la
    hipótesis que recogía `PENDIENTES.md`.
  - `[COMPARAR-ALBARANES]`: el `Decimal`/`float` conocido (GY
    40907/40908) ya se corrigió en `_resumen_entregas()` en
    v12.32.02/.03, así que esta recurrencia es un punto distinto sin
    localizar. Los tres handlers de esta zona (`_leer_texto()`,
    `_ejecutar_comparacion_albaranes_bg()` y el bucle de
    `comparar_listado_albaranes_aplicar()`) pasan de `log.error()` a
    `log.exception()`, para que la próxima aparición traiga el
    traceback completo (archivo y línea) y se pueda corregir la causa,
    no solo detectarla.
- **Verificación**: `python3 -m py_compile app.py` sin errores. No
  probado en vivo contra producción — a confirmar tras desplegar:
  comprobar que Auto-migración deja de repetir `KeyError: 0`, y que si
  vuelve a aparecer el error de Comparar-Albaranes, el log ya trae
  traceback completo.
- **Revisión de otros documentos (norma 5)**: `GUIA_DESPLIEGUE.md`,
  `INSTRUCCIONES_RESTAURACION.md` — no aplica. `README.md` sí: versión
  actual. `PENDIENTES.md` sí: se retira la entrada del `KeyError: 0`
  (resuelta) y se añade una nueva para el `Decimal`/`float` de
  Comparar-Albaranes, con el logging ya preparado para localizarlo.
- **Entrega**: `app.py`, `templates/index.html` (badge de versión),
  `README.md`, `PENDIENTES.md`, más este historial/`CHANGELOG.md`.
  `models.py` y `requirements.txt` no cambian.

---

## 2026-09-03 — [Control Pedidos] Nueva comprobación en Integridad: "Telegram bloqueado o inservible" — se marca sola y se limpia sola (v12.32.05)

- **Petición de Víctor**: a raíz del `403 bot was blocked by the user`
  visto en el log de hoy, preguntó si se podía anotar en Admin →
  Integridad cuándo un usuario bloquea su bot de Telegram.
- **Diseño elegido**: en vez de una anotación manual, se automatiza por
  completo — el propio `_send_telegram()` (función central de todos
  los envíos de Telegram de la app) ya detectaba si un error era
  "permanente" (bot bloqueado, cuenta desactivada, chat borrado…); solo
  faltaba persistirlo en algún sitio visible.
- **Cambio en `app.py`**:
  - Migración: nuevas columnas `usuarios.telegram_bloqueado_en`
    (TIMESTAMPTZ, NULL = sin problema) y
    `usuarios.telegram_bloqueado_motivo` (TEXT).
  - `_marcar_telegram_bloqueado(chat_id, motivo)`: se llama desde
    `_send_telegram()` cuando el error es permanente. Fija
    `telegram_bloqueado_en` solo la primera vez (para poder mostrar
    "bloqueado desde") y siempre actualiza el motivo.
  - `_desbloquear_telegram_si_procede(chat_id)`: se llama cuando un
    envío a ese `chat_id` tiene éxito (incluido el envío de éxito tras
    el fallback a texto plano de v12.32.03) — limpia la marca sola, sin
    que un admin tenga que intervenir; solo hace falta que el usuario
    desbloquee el bot por su lado.
  - Ambas son "best-effort": un fallo al escribir en BD se registra en
    el log (`[TELEGRAM-BLOQUEO]`) y nunca interrumpe el envío real de
    Telegram.
  - `_validar_integridad_operativa()`: nueva categoría de problema
    `telegram_bloqueado`, con todos los usuarios activos (compras o
    admin) que tienen `telegram_bloqueado_en` no nulo, más recientes
    primero.
  - Digest diario de Integridad (Telegram a admins): nueva sección
    "🔴 Telegram bloqueado/inservible", tratada como CRÍTICO igual que
    "Hoteles sin comprador".
- **Cambio en `templates/index.html`**: nueva tarjeta en Admin →
  Integridad, "🔴 Telegram bloqueado o inservible" (gravedad crítica),
  mostrando usuario, nombre, fecha de bloqueo detectada y el motivo
  textual devuelto por Telegram.
- **Verificación**: `python3 -m py_compile app.py` sin errores nuevos.
  `node --check` sobre los bloques `<script>` que contienen
  `loadIntegridad()` sin errores nuevos. No probado en vivo contra
  producción (no hay forma de forzar un bloqueo real de Telegram desde
  este entorno) — a confirmar tras desplegar: verificar que la
  migración añade las dos columnas sin error, y que la fila de
  Integridad aparece/desaparece según se bloquee/desbloquee un usuario
  real de Telegram.
- **Revisión de otros documentos (norma 5)**: `GUIA_DESPLIEGUE.md`,
  `INSTRUCCIONES_RESTAURACION.md` — no aplica. `README.md` sí: versión
  actual. `PENDIENTES.md` sí: se añade una entrada nueva y aparte
  (`KeyError: 0` recurrente en `_auto_migrate()`, visto en el log de
  hoy, sin traceback completo suficiente para localizarlo con
  seguridad).
- **Entrega**: `app.py`, `templates/index.html`, `README.md`,
  `PENDIENTES.md`, `CHANGELOG.md`, este historial. `models.py` y
  `requirements.txt` no cambian.

---

## 2026-09-03 — [Control Pedidos] Fix: mensajes Telegram con Markdown roto ya no se pierden (fallback a texto plano) y fallo puntual de "read-only transaction" en la cola de emails de sistema ahora reintenta (v12.32.04)

- **Contexto**: revisando el log de Render de hoy (a raíz de la
  incidencia GY de v12.32.02/v12.32.03) aparecieron tres eventos
  independientes entre sí:
  1. `06:00` — 7 intentos seguidos de `403 Forbidden: bot was blocked
     by the user` para un usuario (`comprascan6`).
  2. `06:20` — `400 can't parse entities: Can't find end of the entity
     starting at byte offset 116` en un aviso Telegram del evento
     `solicitud_acceso`.
  3. `16:00:11` — `[EMAILS-SISTEMA] Error listando/reservando
     pendientes: cannot execute UPDATE in a read-only transaction`.
- **1) Bot bloqueado (403)**: confirmado que **no es un bug de la
  app** — ese usuario bloqueó el bot de Telegram por su lado. La app
  ya detecta este caso como error "permanente" (no lo reintenta sin
  sentido), pero solo el propio usuario, desbloqueando el bot desde su
  Telegram, puede volver a recibir avisos. No se toca código para
  esto.
- **2) Error de parseo de Markdown (400)**: diagnosticado en
  `_send_telegram()` (`app.py`) — los mensajes se construyen
  interpolando datos variables (usuario, nombre, email…) directamente
  dentro de texto con `parse_mode=Markdown`, sin escapar los
  caracteres especiales de Markdown (`*`, `_`, `` ` ``). Si alguno de
  esos datos trae un carácter de ese tipo suelto o sin pareja, Telegram
  rechaza el mensaje entero con este 400 y, como el error se marcaba
  como "no permanente", quedaba pendiente de un reintento al día
  siguiente que iba a fallar exactamente igual (el texto roto no
  cambia solo). **Cambio**: `_send_telegram()` ahora detecta
  específicamente este error y reintenta UNA vez el mismo texto sin
  `parse_mode` (como texto plano) — el aviso llega igual, aunque ese
  mensaje concreto pierda negritas/cursivas. Al estar centralizada en
  esta única función (usada por todos los avisos de Telegram de la
  app — cambios de estado, alertas, solicitudes de acceso, técho de
  gastos, etc.), el fix cubre cualquier plantilla actual y futura sin
  tener que tocar cada punto donde se construye un mensaje.
- **3) `read-only transaction` puntual (`/api/emails-sistema-pendientes`)**:
  visto una única vez en el log, sin relación con nada que esta app
  configure explícitamente (no hay ningún `SET ... READ ONLY` en el
  código) — compatible con una conexión reciclada del pool que quedó
  en ese estado por un evento puntual de la infraestructura de
  Supabase. **Cambio**: el endpoint ahora detecta ese error concreto,
  descarta del pool la conexión afectada (se cierra en vez de
  reciclarse) y reintenta la reserva de correos pendientes UNA vez con
  una conexión nueva, en lugar de devolver 500 directamente. Si el
  reintento también falla, sí se devuelve error (para no enmascarar un
  problema real y persistente).
- **Verificación**: `python3 -m py_compile app.py` sin errores nuevos.
  No fue posible reproducir en vivo ninguno de los dos errores (400 de
  Markdown, read-only) desde este entorno — a confirmar tras
  desplegar: si vuelven a aparecer, comprobar en el log las nuevas
  líneas `Telegram: fallback a texto plano...` y `[EMAILS-SISTEMA]
  Conexión en modo solo-lectura...` respectivamente, seguidas en ambos
  casos de una entrega/reserva correcta.
- **Revisión de otros documentos (norma 5)**: `GUIA_DESPLIEGUE.md`,
  `PENDIENTES.md`, `INSTRUCCIONES_RESTAURACION.md` — no aplica.
  `README.md` sí: versión actual.
- **Entrega**: `app.py`, `templates/index.html` (badge de versión),
  `README.md`, `CHANGELOG.md`, este historial. `models.py` y
  `requirements.txt` no cambian.

---

## 2026-09-03 — [Control Pedidos] Fix: un fallo al construir el correo interno de cambio de estado ya no bloquea el aviso de Telegram/popup (v12.32.03)

- **Hallazgo derivado de la incidencia GY (v12.32.02)**: al valorar si,
  además del correo de los pedidos 40907/40908, algo más se había visto
  afectado, se revisó el flujo completo de `_notificar_cambio_estado()`
  — sin poder confirmarlo de forma directa por no tener en ese momento
  acceso al Telegram del hotel GY.
- **Diagnóstico**: `_notificar_cambio_estado()` llama en secuencia a (1)
  `enviar_emails_estado()` y (2) `_telegram_cambio_estado()`, pero sin
  ningún `try/except` entre ambas — si la primera lanza una excepción
  (como el `TypeError: Decimal - float` de v12.32.02, que salta dentro
  de `enviar_emails_estado()` al construir el correo interno vía
  `_resumen_entregas()`), la función corta ahí mismo y nunca llega a
  ejecutar la segunda. Es decir: para los pedidos 40907/40908, además
  del correo, muy probablemente tampoco se disparó el aviso de
  Telegram/popup inmediato, aunque no fue posible confirmarlo con
  certeza a posteriori.
- **Cambio en `app.py`**: `_notificar_cambio_estado()` envuelve ahora la
  llamada a `enviar_emails_estado()` en un `try/except`. Si falla, se
  registra el error con `log.error("[NOTIFICAR-CAMBIO-ESTADO] ...")` y
  se sigue ejecutando `_telegram_cambio_estado()` de todas formas; al
  terminar, si hubo una excepción al construir el correo, se relanza
  para que el caller (p. ej. el bucle por-coincidencia de
  `comparar_listado_albaranes_aplicar`) siga clasificando ese caso como
  "error" exactamente igual que hasta ahora — este cambio no afecta a
  esa clasificación, solo garantiza que el Telegram/popup no dependa
  del éxito del correo.
- **Verificación**: `python3 -m py_compile app.py` sin errores nuevos.
  No probado en vivo contra producción — a confirmar tras desplegar:
  provocar (o esperar) un fallo real al construir el correo interno de
  un cambio de estado y comprobar que, pese a ello, el Telegram/popup
  sí llega, junto con la línea de log
  `[NOTIFICAR-CAMBIO-ESTADO] Fallo construyendo/encolando el correo
  interno...`.
- **Revisión de otros documentos (norma 5)**: `GUIA_DESPLIEGUE.md`,
  `PENDIENTES.md`, `INSTRUCCIONES_RESTAURACION.md` — no aplica.
  `README.md` sí: versión actual.
- **Entrega**: `app.py`, `templates/index.html` (badge de versión),
  `README.md`, `CHANGELOG.md`, este historial. `models.py` y
  `requirements.txt` no cambian.

---

## 2026-09-03 — [Control Pedidos] Fix: el correo interno de cambio de estado automático (Comparar Pedidos + Albaranes) podía no llegar a encolarse — `TypeError: Decimal - float` en `_resumen_entregas()` (v12.32.02)

- **Incidencia real reportada por Víctor (continuación de la de v12.30.99)**:
  con el fix del despacho inmediato de v12.30.99 ya desplegado, los
  correos internos de los pedidos 40907/40908 (hotel GY) seguían sin
  llegar tras confirmar "Aplicar" en "Comparar Pedidos + Albaranes",
  aunque ambos pedidos sí quedaron correctamente actualizados (ENTREGA
  PARCIAL y ENTREGADO, visibles en la Línea temporal). El correo de
  resumen de esa comparación mostró además "Registrados
  automáticamente (0)" pese a los dos cambios reales, y Víctor recordó
  haber visto un aviso en rojo, breve, en la esquina inferior derecha
  al confirmar los cambios.
- **Diagnóstico**: cruzando el log de acceso de Render (que permitió
  identificar el job de la comparación de GY, `f01786d4…`, con dos
  llamadas a `/aplicar` a las 18:20:59 y 18:21:12 UTC) con el log de
  aplicación, aparecieron en la franja exacta de la primera llamada dos
  líneas `ERROR [COMPARAR-ALBARANES] Error aplicando coincidencia
  13093_336_35` y `13208_2041_41` (los dos pedidos de GY), ambas con el
  mismo mensaje: `unsupported operand type(s) for -: 'decimal.Decimal'
  and 'float'`. La causa raíz está en `app.py`,
  `_resumen_entregas()` (línea 2245): `total_pedido` llega de
  PostgreSQL como `decimal.Decimal` (columna `NUMERIC`), mientras que
  `total_recibido` se acumula como `float` a partir de los importes de
  los albaranes parseados del PDF (`float()` en
  `_parse_albaran_entries()`) — la resta directa entre ambos tipos no
  está soportada en Python y lanza `TypeError`.
  `_aplicar_coincidencia_albaran()` ya había hecho `commit()` del
  cambio de estado antes de llamar a `_notificar_cambio_estado()` →
  `enviar_emails_estado()` (que usa `_resumen_entregas()` para el
  histórico de entregas del correo) — así que el pedido quedaba bien
  en BD, pero la excepción cortaba la construcción del correo antes de
  llegar a encolarlo. Sin capturar en ese punto, la excepción subía
  hasta el bucle del endpoint `/aplicar`, que sí atrapa por
  coincidencia y la clasificaba en `errores` en vez de `aplicadas` — de
  ahí el aviso rojo, y que el resumen contara 0 "Registrados
  automáticamente" (ese contador solo suma `aplicadas`).
- **Cambio en `app.py`**: en `_resumen_entregas()`, la resta
  `_total_pedido_val - _total_recibido_val` ahora convierte
  explícitamente `_total_pedido_val` a `float` antes de restar,
  eliminando la mezcla de tipos `Decimal`/`float`.
- **Sobre los correos de 40907/40908**: no se perdieron en la cola —
  nunca llegaron a encolarse, porque la excepción saltaba justo antes
  de `_encolar_email_pedido_retrasado`. No hay nada que recuperar de
  la cola para esos dos pedidos; el fix evita que vuelva a ocurrir en
  futuras coincidencias del mismo tipo.
- **Verificación**: `python3 -m py_compile app.py` sin errores.
  Reproducido el `TypeError` original a partir de los logs de Render
  (mismo mensaje de error, mismas dos coincidencias). No probado en
  vivo contra producción — a confirmar tras desplegar: repetir
  "Comparar Pedidos + Albaranes" en un hotel con una coincidencia que
  cambie el estado, pulsar "Aplicar" y comprobar que no aparece el
  aviso rojo, que el resumen cuenta el registro en "Registrados
  automáticamente" y que el correo interno de cambio de estado llega.
- **Revisión de otros documentos (norma 5)**: `GUIA_DESPLIEGUE.md`,
  `PENDIENTES.md`, `INSTRUCCIONES_RESTAURACION.md` — no aplica.
  `README.md` sí: versión actual.
- **Entrega**: `app.py`, `templates/index.html` (badge de versión),
  `README.md`, `CHANGELOG.md`, este historial. `models.py` y
  `requirements.txt` no cambian.

---

## 2026-09-03 — [Control Pedidos] Fix: hueco en blanco bajo la barra superior en EmailJS y cola de correo (y en las otras 10 pantallas de Sistema/Datos maestros/Alertas · Admin) — `</div>` de más cerraba `#content` antes de tiempo (v12.32.00)

- **Incidencia real reportada por Víctor**: tras desplegar v12.30.99, al
  abrir "EmailJS y cola de correo" la pantalla mostraba un hueco en
  blanco grande entre la barra superior (topbar, con el botón
  "↻ Actualizar") y la tarjeta real de configuración (con "↻ Recargar"
  / "💾 Guardar cambios"). Se sospechó primero de la pestaña, abierta
  desde el día anterior — pero el hueco persistía tras una recarga
  completa (Ctrl+Shift+R), lo que descartaba caché o estado de JS
  envejecido y apuntaba a un fallo real en el código servido.
- **Diagnóstico**: en `templates/index.html`, inmediatamente después de
  cerrarse `view-proveedores` (que cierra correctamente en la línea
  1703), quedaba un `</div>` suelto en la línea 1705 — sin explicación
  aparente, aislado entre dos líneas en blanco. Ese cierre de más
  terminaba el contenedor `#content` de forma prematura. Como
  `#content{flex:1; padding:24px; display:flex; flex-direction:column}`
  crece para ocupar el espacio disponible en el eje vertical de
  `#main`, al quedarse sin hijos (porque las vistas siguientes ya no
  estaban dentro) se expandía como una caja vacía — ese es exactamente
  el hueco visible. Y como el documento seguía "abierto" un nivel de
  más a partir de ahí, TODAS las vistas que aparecen después de
  Proveedores en el HTML (`view-eliminados`, `view-techo`,
  `view-familias`, `view-departamentos-email`,
  `view-notificaciones-contactos`, `view-integridad`,
  `view-config-alertas`, `view-config-avisos`,
  **`view-config-emailjs`**, `view-restore`, `view-usuarios`, y los
  modales intermedios) pasaban a ser hijas directas de `#main` en vez
  de `#content` — de ahí que la tarjeta real de cada una de esas
  pantallas apareciera "descolgada" justo debajo del hueco, sin el
  padding de 24px que aporta `#content`. `showView()` seguía
  funcionando bien a nivel lógico (oculta/muestra por `id`, sin
  depender de la jerarquía), por lo que el contenido cargaba y era
  interactivo con normalidad — el bug era puramente visual/estructural,
  no funcional, lo que explica que los cambios de estado y correos
  siguieran funcionando bien mientras la pantalla se veía "rota".
- **Reproducción**: se sirvió el `index.html` real (sin modificar) con
  un servidor local y se cargó la vista "EmailJS y cola de correo" con
  Playwright, interceptando las llamadas a `/api/admin/config-alertas`
  con datos equivalentes a los de la captura de Víctor (cuenta 2 en
  uso, mismos Service ID/Template ID). La captura resultante reproduce
  el hueco en blanco de forma prácticamente idéntica a la reportada.
  Un script de balanceo de etiquetas `<div>` sobre la plantilla
  confirmó exactamente un cierre de más en todo el documento, en la
  línea 1705, y que sin él el balance es perfecto (0 de más, 0 sin
  cerrar).
- **Cambio en `templates/index.html`**: se elimina el `</div>` sobrante
  de la línea 1705. Ningún otro cambio de marcado.
- **Verificación tras el fix**: se repitió la reproducción con
  Playwright contra el archivo corregido — el hueco desaparece, la
  tarjeta de "EmailJS y cola de correo" queda pegada a la barra
  superior con el padding normal. Se comprobó además, consultando el
  DOM ya renderizado, que las 15 vistas (`view-dashboard` a
  `view-usuarios`) anidan ahora como hijas directas de `#content` a la
  misma profundidad — ninguna quedó por detrás o nesteada de más.
  `python3 -m py_compile app.py` sin errores (no se tocó `app.py`; se
  ejecuta igualmente porque forma parte de la rutina de verificación
  habitual del proyecto). No probado en vivo contra producción (sin
  acceso desde este entorno) — a confirmar tras desplegar: abrir
  "EmailJS y cola de correo" y comprobar que no hay hueco; revisar de
  pasada Pedidos Eliminados, Techo de Gastos, Familias de Artículos,
  Departamentos, Notificaciones adicionales, Integridad, Parámetros de
  Alertas, Avisos por Usuario, Restaurar Backup y Usuarios, que
  compartían el mismo bug aunque menos perceptible en pantallas con
  menos contenido en la parte superior.
- **Revisión de otros documentos (norma 5)**: `GUIA_DESPLIEGUE.md`,
  `PENDIENTES.md`, `INSTRUCCIONES_RESTAURACION.md` — no aplica,
  ninguno documenta la estructura del layout/DOM de la aplicación.
  `README.md` sí: versión actual.
- **Entrega**: `templates/index.html`, `README.md`, más este historial
  y `CHANGELOG.md`. `app.py`, `models.py` y `requirements.txt` no
  cambian.

---

## 2026-09-03 — [Control Pedidos] Fix: el correo de cambio de estado automático (Comparar Pedidos + Albaranes) se quedaba en cola sin salir si nadie dejaba la app abierta 5 min más tras "Aplicar" (v12.30.99)

- **Incidencia real reportada por Víctor**: hotel GY, esta tarde — al
  confirmar los cambios detectados en "Comparar Pedidos + Albaranes" y
  pulsar "Aplicar", los pedidos 40907 y 40908 quedaron correctamente
  actualizados (ENTREGA PARCIAL / ENTREGADO, visibles en la Línea
  temporal como "Automática — listado comparativo pedidos y
  albaranes" a las 19:20), pero el correo interno de ese cambio de
  estado no llegó — comprobado en la carpeta de Enviados de Gmail
  (`in:sent`), donde solo aparecían los correos de resumen de la
  comparación de varios hoteles (asunto "Comparación pedidos+albaranes
  XX: ..."), no los de cambio de estado por pedido (asunto "[Control
  Pedidos] GY · Pedido 40907 → ...").
- **Diagnóstico — dos fallos combinados, siguiendo el rastro de la
  verificación de ayer (ver entrada anterior de hoy, sin cambio de
  código)**:
  1. `enviar_emails_estado()` encola el correo interno de cualquier
     cambio de estado — manual o automático — con un retraso fijo de
     300s (`_encolar_email_pedido_retrasado`, `visible_en = NOW() +
     300s`). Ese retraso existe para agrupar varias ediciones manuales
     SEGUIDAS sobre el mismo pedido en un único correo (evitar spam de
     un correo por cada guardado rápido) — pero un cambio automático de
     `_aplicar_coincidencia_albaran()` es una única escritura
     determinista por pedido, no hay nada que agrupar.
  2. El correo NO tiene SMTP propio: lo despacha el navegador de
     cualquier sesión admin/compras abierta, vía
     `_enviarEmailsSistemaPendientes()` — un sondeo automático cada 5
     min (`_startEmailsSistemaPolling`) más una "primera pasada
     inmediata" al abrir la app. El botón "Enviar resumen" YA disparaba
     un despacho inmediato extra nada más encolarse (para no depender
     del sondeo de 5 min, ver comentario en
     `enviarResumenComparacionAlbaranes()`), pero el botón "Aplicar" NO
     lo hacía. Combinado con el punto 1 (visible_en 5 min en el
     futuro), si la sesión que pulsó "Aplicar" se cerraba antes de que
     pasaran esos 5 minutos — plausible a última hora de la tarde — el
     correo se quedaba en la cola (`emails_sistema_pendientes`, visible
     en Admin → EmailJS → "Cola de correos de sistema pendientes"), sin
     enviarse, hasta que alguien volviera a abrir la app más tarde.
- **Cambio en `app.py`**: en `enviar_emails_estado()`, nueva variable
  `_retraso_email_estado = 2 if es_automatico else 300`, pasada como
  `retraso_segundos` en los dos encolados existentes
  (`_encolar_email_pedido_retrasado`, tanto el correo a proveedor como
  el interno). Con `es_automatico=True` (el caso de
  `_aplicar_coincidencia_albaran()`) el correo queda visible para
  envío casi de inmediato, igual que el correo de resumen. Los cambios
  de estado manuales no se tocan: siguen con los 300s de siempre.
- **Cambio en `templates/index.html`**: `_procesarResultadoAplicarAlbaran()`
  (llamada tras "Aplicar"/"Aplicar seleccionadas") dispara
  `_enviarEmailsSistemaPendientes()` cuando `aplicadas.length > 0` —
  mismo patrón exacto que ya usaban `enviarResumenComparacionPdf()` y
  `enviarResumenComparacionAlbaranes()`: adelanta el despacho desde el
  propio navegador que acaba de aplicar los cambios, en vez de esperar
  al sondeo de 5 min. Con el retraso ya casi nulo del punto anterior,
  esta llamada encuentra el correo ya visible y lo envía en el acto.
- **Verificación**: `python3 -m py_compile app.py` sin errores de
  sintaxis nuevos (persiste un `SyntaxWarning` preexistente en un
  docstring con `\.`, no relacionado). Los 9 bloques `<script>` de
  `templates/index.html` extraídos y verificados con `node --check`
  (el único bloque que da error es una plantilla HTML embebida ajena a
  JS real, ya fallaba igual antes de este cambio). No probado en vivo
  contra producción (sin acceso desde este entorno) — a confirmar tras
  desplegar: repetir "Comparar Pedidos + Albaranes" con algún pedido
  que cambie de estado, pulsar "Aplicar", y comprobar en Enviados que
  el correo "[Control Pedidos] ... → ..." llega en segundos, sin
  necesidad de esperar ni de mantener la pestaña abierta 5 min más. Si
  quedó algún correo de la incidencia de hoy (pedidos 40907/40908)
  todavía en la cola sin marcar `enviado`, seguirá ahí — revisar Admin
  → EmailJS → "Cola de correos de sistema pendientes": con la app
  abierta unos segundos ya debería despacharse solo (o usar
  "↻ Reactivar" si aparece como parado).
- **Revisión de otros documentos (norma 5)**: `GUIA_DESPLIEGUE.md`,
  `PENDIENTES.md`, `INSTRUCCIONES_RESTAURACION.md` — no aplica, ninguno
  documenta el mecanismo de retraso/despacho de esta cola.
  `docs/hallazgo-seguridad-princess.md` no existe en este repo.
  `README.md` sí — versión actual y aclaración ampliada en "Correo
  interno de cambio de estado" sobre el despacho casi inmediato en
  cambios automáticos.
- **Entrega**: `app.py`, `templates/index.html`, `README.md`, más este
  historial/`CHANGELOG.md`. `models.py` y `requirements.txt` no
  cambian.

---

## 2026-09-03 — [Control Pedidos] Verificación: los cambios de estado automáticos de "Comparar Pedidos + Albaranes" SÍ disparan el correo interno configurado, igual que un cambio manual (sin cambio de código)

- **Pregunta de Víctor**: cuando la comparación de listados ("Comparar
  listado PDF (SAP)", con o sin el cruce de albaranes de DALI) aplica
  cambios de estado automáticos en los pedidos, ¿se envían los correos
  internos configurados avisando de ese cambio de estado? ¿Debería
  funcionar igual que si lo hace un usuario humano?
- **Revisado en el código, sin necesidad de ningún cambio — ya funciona
  así por diseño desde v12.30.16/17/18/19**:
  - La comparación de **un solo PDF** ("Comparar listado PDF (SAP)",
    sin marcar la casilla de albaranes) — `_comparar_listado_pdf_logica()`
    — es de solo lectura salvo tres campos puramente informativos
    (`total_pedido`, base imponible de la última entrada, y
    `fecha_tramitacion` solo si estaba vacía): **nunca toca `estado`
    ni dispara ninguna notificación**, por diseño explícito (así lo
    documenta su propio docstring). El estado que se ve en pantalla en
    esa comparación es solo una deducción para mostrar en la tabla, no
    se guarda.
  - Cuando además se marca "+ Comparar también con el listado de
    Albaranes registrados en DALI", las coincidencias propuestas
    **nunca se aplican solas al comparar** — hace falta que el
    administrador pulse "Aplicar" (o "Aplicar todas") sobre las que
    confirma, endpoint `/api/pedidos/comparar-listado-albaranes/<job_id>/aplicar`.
  - Al aplicar una coincidencia que sí implica un cambio de estado
    (ENTREGA PARCIAL o ENTREGADO), `_aplicar_coincidencia_albaran()`
    llama a `_notificar_cambio_estado(..., es_automatico=True)`, exactamente
    la misma función central que usan todos los cambios de estado
    manuales (`update_pedido`, flujo hotel, aprobar/denegar
    expediente). Esa función llama, en este orden, a
    `enviar_emails_estado()` (correo interno, y correo a proveedor si
    aplica) y a `_telegram_cambio_estado()` (Telegram/popup
    inmediato).
  - `enviar_emails_estado()` encola el correo interno con el mismo
    mecanismo que un cambio manual — `_encolar_email_pedido_retrasado()`,
    cola con 5 minutos de retraso y antirrepetición, despachada por el
    poller de cualquier sesión admin/compras con la app abierta (no
    hace falta SMTP propio) — a los mismos destinatarios (comprador,
    rol hotel, correo de departamento y contactos adicionales
    configurados en Administrador → Notificaciones). ENTREGA PARCIAL y
    ENTREGADO están dentro de `ESTADOS_EMAIL_INTERNO` (`models.py`),
    así que el correo se dispara igual que para cualquier otro estado
    de esa lista.
  - Única diferencia real frente a un cambio manual: con
    `es_automatico=True`, `enviar_emails_estado()` **no excluye a
    nadie** de la lista de destinatarios (un cambio manual sí excluye
    el email principal de quien lo hizo, desde v12.30.18/19/97) — esto
    es intencional y viene de una petición explícita de Víctor de
    2026-08-19 (v12.30.18): *"si el cambio es automático entonces sí
    correo a ambas partes"*. Y en el Historial de estados del pedido,
    el registro se guarda con la etiqueta fija "Automática — listado
    comparativo pedidos y albaranes" en vez del nombre de quien pulsó
    "Aplicar" (v12.30.17), para que se distinga a simple vista de un
    cambio hecho a mano — pero el correo en sí llega igual.
  - Conclusión: **sí, funciona igual que si lo hiciera un usuario
    humano** (mismos destinatarios — de hecho ninguno excluido —,
    mismo contenido, mismo mecanismo de envío), con la única salvedad
    de que el registro queda etiquetado como automático para
    trazabilidad.
- **No se ha tocado ningún archivo de código** (`app.py`,
  `templates/index.html`, `models.py`) — no había ningún fallo que
  corregir. Se documenta esta verificación aquí para dejar constancia
  de la pregunta y la respuesta, y se añade una aclaración en
  `README.md` (sección "Correo interno de cambio de estado") sobre el
  comportamiento en cambios automáticos.
- **Revisión de otros documentos (norma 5)**: `CHANGELOG.md` — se
  añade la misma nota. `GUIA_DESPLIEGUE.md`, `PENDIENTES.md`,
  `INSTRUCCIONES_RESTAURACION.md` — no aplica, no documentan este
  comportamiento. `docs/hallazgo-seguridad-princess.md` no existe en
  este repo.
- **Entrega**: `README.md`, más esta nota en `docs/HISTORIAL_CAMBIOS.md`
  y `CHANGELOG.md`. `app.py`, `templates/index.html`, `models.py` y
  `requirements.txt` no cambian — la versión sigue en **v12.30.98**.

---

## 2026-09-03 — [Control Pedidos] Modal de nueva versión: solo admin ve el changelog completo, el resto de roles solo un título-resumen (v12.30.98)

- **Origen**: Víctor pidió limitar la pantalla de recarga de actualización — "el exceso de información aturde al usuario" — para que solo muestre un mensaje de nueva actualización con un título resumen, sin entrar en detalles, y que el detalle completo se reserve para los administradores.
- **Diagnóstico**: `/api/changelog` servía siempre el `CHANGELOG.md` entero (petición/diagnóstico/cambio/verificación de cada entrada) a cualquier usuario logueado sin distinguir rol, y el modal de "nueva versión detectada" lo mostraba íntegro a todo el mundo por igual, incluidos roles `compras`/`hotel` sin interés en el pormenor técnico.
- **Cambio en `app.py`**: `/api/changelog` consulta ahora `session.get("rol")`. Con `admin`, responde igual que antes (`{"changelog": "..."}` con el fichero completo). Con cualquier otro rol, nueva función `_resumen_ultima_version_changelog()` extrae solo la cabecera de versión y el título-resumen de una línea de la entrada más reciente, devuelto como `{"resumen": "..."}`, sin los párrafos de detalle.
- **Cambio en `templates/index.html`**: el modal de nueva versión pasa a tener dos bloques de cuerpo — `modal-nv-body-full` (la caja de "Notas de la versión" con badges de siempre) y `modal-nv-body-resumen` (mensaje corto, sin caja de scroll ni badges). `_mostrarModalNuevaVersion()` decide cuál mostrar según si la respuesta trae `changelog` o `resumen`. La caché en memoria (antes `_obtenerChangelog()`/`_changelogCache`, solo texto) pasa a `_obtenerInfoVersion()`/`_versionInfoCache`, guardando el objeto de respuesta completo — mismo mecanismo de promesa compartida de antes para no duplicar peticiones si el modal se dispara desde varios puntos casi a la vez (chequeo al entrar, polling periódico...). El botón "Recargar ahora" y la cuenta atrás de 5 min no cambian: siguen siendo el único cierre posible, para cualquier rol.
- **Verificación**: `python3 -m py_compile app.py` sin errores de sintaxis. Los 7 bloques `<script>` de `templates/index.html` extraídos y verificados con `node --check`, sin errores. No probado en vivo contra producción (sin acceso desde este entorno) — a confirmar tras desplegar: forzar el modal (`_testModalVersion()` en consola) con un usuario `admin` y comprobar que ve el changelog completo con badges, y con un usuario `compras`/`hotel` y comprobar que ve solo el título-resumen sin caja de detalle.
- **Revisión de otros documentos (norma 5)**: `GUIA_DESPLIEGUE.md`, `PENDIENTES.md`, `INSTRUCCIONES_RESTAURACION.md` — no aplica, ninguno documenta este modal. `docs/hallazgo-seguridad-princess.md` no existe en este repo. `README.md` sí — versión actual y nuevo bullet "Aviso de nueva versión" en "Sistema · Admin".
- **Entrega**: `app.py`, `templates/index.html`, `README.md`, más este historial/`CHANGELOG.md`. `models.py` y `requirements.txt` no cambian.

---

## 2026-09-03 — [Control Pedidos] Correo interno de cambio de estado: el email2 (correo de control) del actor ya no se excluye, solo su email principal (v12.30.97)

- **Origen**: Víctor preguntó qué ocurría con el segundo correo (`email2`) de la cuenta que realiza un cambio de estado, dado el filtro que evita que quien hace el cambio reciba el correo interno de ese mismo cambio (v12.30-19). Pidió que ese segundo correo se siga asignando siempre a los hoteles del usuario y reciba la info correspondiente, y que en el caso de una cuenta con dos correos solo se excluya el primero, nunca el segundo — el email2 es un correo de control de esa cuenta, no la persona que está operando el pedido, así que debe recibir siempre la info de los hoteles asignados con independencia de quién haga el cambio.
- **Diagnóstico**: en `enviar_emails_estado()`, `_emails_actor` se construía con `_emails_usuario(_actor)`, función pensada para listas de destinatarios (Para/CC/BCC) que deliberadamente devuelve `[email, email2]` — al usarla también para calcular a quién EXCLUIR, se excluían ambos correos de la cuenta que hizo el cambio, incluido el de control. La inclusión del email2 en los destinatarios (vía `_get_todos_usuarios_hotel()` + `_emails_usuario()`, con los hoteles ya asignados a esa cuenta) ya funcionaba correctamente desde antes — no hacía falta tocar nada ahí; el problema estaba solo en el lado de la exclusión.
- **Cambio en `app.py`**: la consulta que averigua el email del actor pasa de `SELECT email, email2 FROM usuarios WHERE id=%s` a `SELECT email FROM usuarios WHERE id=%s`, y `_emails_actor` se arma directamente con ese único valor (si existe y no está vacío), en vez de con `_emails_usuario(_actor)`. `_todos_internos` sigue filtrando por `_emails_actor` exactamente igual que antes, pero ahora la lista de exclusión nunca contiene el email2 del actor — si ese email2 coincide con un comprador o usuario hotel del hotel del pedido, sigue recibiendo el correo interno con normalidad, igual que cualquier otro destinatario.
- **Verificación**: `python3 -m py_compile app.py` sin errores de sintaxis. No probado en vivo contra producción (sin acceso desde este entorno) — a confirmar tras desplegar: hacer un cambio de estado con un usuario que tenga `email2` configurado (Usuarios → ficha de usuario) y comprobar que el correo interno de cambio de estado llega al `email2` pero no al `email` principal de esa misma cuenta.
- **Revisión de otros documentos (norma 5)**: `GUIA_DESPLIEGUE.md`, `PENDIENTES.md`, `INSTRUCCIONES_RESTAURACION.md` — no aplica, ninguno documenta esta regla de exclusión del correo interno. `docs/hallazgo-seguridad-princess.md` no existe en este repo. `README.md` sí — versión actual y aclaración añadida a la sección "Correo interno de cambio de estado" (Alertas y notificaciones · Admin), sobre que el email2 ya no se excluye.
- **Entrega**: `app.py`, `templates/index.html` (badge de versión), `README.md`, más este historial/`CHANGELOG.md`. `models.py` y `requirements.txt` no cambian.

---

## 2026-09-02 — [Control Pedidos] Icono para mostrar/ocultar la contraseña al escribirla, en login, restablecimiento y modal de Usuarios (v12.30.96)

- **Origen**: Víctor pidió el "ojito" para poder visualizar la contraseña al escribirla.
- **Contexto**: ese icono ya existía, pero solo en el modal de Usuarios (`usr-password`), con la función `togglePwdVisibility()` codificada específicamente para ese campo (id fijo, sin parámetros). Faltaba en el propio formulario de login y en el de restablecimiento de contraseña, que es justo donde más se necesita (contraseñas nuevas, tecleadas sin poder verificarlas).
- **Cambio en `templates/index.html`**: `togglePwdVisibility()` se generaliza para aceptar el id del input y el botón pulsado como parámetros (`inputId`, `btn`), manteniendo compatibilidad hacia atrás (si no se le pasa nada, sigue afectando a `usr-password` como antes). Además de alternar el `type` del input entre `password`/`text`, ahora también cambia el propio icono del botón (👁 cuando está oculta, 🙈 cuando está visible), como pista visual de en qué estado se ha quedado el campo. Se añade el mismo botón-icono a `login-pass` (login) y a `reset-nueva`/`reset-confirma` (restablecimiento de contraseña), con la misma posición/estilo que ya usaba `usr-password` pero adaptado a la paleta oscura/dorada del login (`color:rgba(180,150,60,0.6)` en vez de `#888`). Los tres botones nuevos llevan `tabindex="-1"` para no interponerse en la tabulación entre "Usuario" → "Contraseña" → "Acceder" (o entre "Nueva contraseña" → "Repetir contraseña" → "Guardar"). La llamada del modal de Usuarios se actualiza a `togglePwdVisibility('usr-password', this)` para aprovechar también el cambio de icono; su aspecto no varía.
- **`app.py` no cambia**: cambio puramente de frontend (atributo `type` del `<input>`), sin ningún dato nuevo ni distinto que viaje al servidor ni afecte a la validación de contraseñas.
- **Verificación**: `python3 -m py_compile app.py` sin errores. Los bloques `<script>` de `templates/index.html` (extraídos con un script auxiliar) verificados con `node --check`, incluido el que contiene `togglePwdVisibility()`/`doLogin()`, sin errores de sintaxis. No probado en vivo contra producción (sin acceso desde este entorno) — a confirmar tras desplegar: pulsar el icono en los tres sitios (login, modal de Usuarios, restablecimiento) y comprobar que alterna entre contraseña oculta/visible y que el icono cambia entre 👁/🙈.
- **Revisión de otros documentos (norma 5)**: `GUIA_DESPLIEGUE.md`, `PENDIENTES.md`, `INSTRUCCIONES_RESTAURACION.md` — no aplica. `docs/hallazgo-seguridad-princess.md` no existe en este repo. `README.md` — revisado; un icono en un campo de formulario no tiene entidad propia en el README, solo se actualiza la versión actual.
- **Entrega**: `templates/index.html`, `README.md` (versión actual), más este historial/`CHANGELOG.md`. `app.py`, `models.py` y `requirements.txt` no cambian.

---

## 2026-09-02 — [Control Pedidos] Login → verificación por email: cooldown y confirmación en "Reenviar código", para evitar dos códigos distintos en menos de un minuto (v12.30.95)

- **Origen**: Víctor detectó (capturas de la carpeta de enviados de Gmail) que un usuario, tras recibir correctamente el aviso de verificación por inactividad (3+ días sin login), recibía dos correos de "Código de verificación" con códigos distintos en menos de un minuto — preguntó si esto era normal.
- **Diagnóstico**: no era un doble-submit simultáneo — eso ya estaba protegido desde v12.3.0 con el flag `_loginEnCurso`, que bloquea una segunda llamada a `/api/login` mientras la primera sigue en curso. El comportamiento es, en parte, por diseño: cada llamada a `/api/login` (incluida la que dispara el botón "Reenviar código") invalida el código anterior sin usar y genera uno nuevo, para que solo el último enviado sea válido. Lo que faltaba era protección de UX: el botón "Reenviar código" no tenía cooldown ni mostraba ninguna confirmación de que el email ya se había enviado, así que ante cualquier tardanza real en la entrega (Gmail, EmailJS, red) el usuario lo pulsaba por impaciencia, invalidando sin querer un código que sí iba a llegar. El patrón de las capturas (dos códigos, exactamente 1 minuto de diferencia) encaja con esto, no con un fallo de doble-envío técnico.
- **Cambio en `templates/index.html`**: nuevo cooldown de 45s en el botón "Reenviar código" (`id="btn-reenviar-codigo"`) tras cada envío que tuvo éxito — tanto el envío automático al entrar en el paso 2 como cada reenvío manual —, con cuenta atrás visible en el propio texto del botón ("Reenviar código (45s)", deshabilitado mientras tanto) y una confirmación breve "✅ Código enviado/reenviado a tu email" bajo el botón (se oculta sola a los 6s). Si el envío FALLA (tras los 2 intentos ya existentes de `_enviarCodigoVerificacion`), no se aplica cooldown: el mensaje de error ya invitaba a pulsar "Reenviar código" de inmediato para reintentarlo, y bloquearlo en ese caso habría sido contraproducente. Nuevas funciones `_iniciarCooldownReenvio()` / `_detenerCooldownReenvio()` / `_mostrarConfirmacionReenvio()`. `_volverLoginPaso1()` (botón "← Volver") limpia el cooldown y la confirmación al descartar el intento en curso, para que el próximo intento de login arranque en estado limpio.
- **`app.py` no cambia**: la generación/invalidación de códigos en `/api/login` ya era correcta por diseño (solo el último código enviado debe ser válido); este fix es puramente de frontend, para que el usuario no dispare reenvíos innecesarios, no un cambio de lógica de backend.
- **Verificación**: los 9 bloques `<script>` de `templates/index.html` (extraídos con un script auxiliar) se verificaron con `node --check`, sin errores de sintaxis, incluido el bloque que contiene `doLogin()`/las funciones nuevas. No probado en vivo contra producción (sin acceso desde este entorno) — a confirmar tras desplegar: forzar el aviso de verificación por inactividad (usuario con `ultimo_login` de hace 3+ días) y comprobar que, tras el envío inicial, "Reenviar código" aparece deshabilitado con la cuenta atrás y el mensaje de confirmación, volviendo a habilitarse pasados los 45s.
- **Revisión de otros documentos (norma 5)**: `GUIA_DESPLIEGUE.md`, `PENDIENTES.md`, `INSTRUCCIONES_RESTAURACION.md` — no aplica, ninguno documenta el flujo de login/verificación. `docs/hallazgo-seguridad-princess.md` no existe en este repo. `README.md` — revisado; el flujo de verificación por email nunca ha tenido sección propia en el README (es un detalle del login, no una "vista" del sidebar), así que solo se actualiza la versión actual, sin bullet nuevo.
- **Entrega**: `templates/index.html`, `README.md` (versión actual), más este historial/`CHANGELOG.md`. `app.py`, `models.py` y `requirements.txt` no cambian.

---

## 2026-09-02 — [Control Pedidos] Correo interno de cambio de estado: botón de descarga del PDF también en ENTREGA PARCIAL/ENTREGADO, con importes y días transcurridos en el texto (v12.30.94)

- **Origen**: Víctor pidió dos cosas sobre el correo interno de cambio de estado (ENVIADO AL PROVEEDOR / ENTREGA PARCIAL / ENTREGA TOTAL): 1) que el botón de descarga/visualización del PDF del pedido, presente desde v12.30.55 solo en ENVIADO AL PROVEEDOR, se incluya también en ENTREGA PARCIAL y ENTREGA TOTAL (ENTREGADO); 2) que el cuerpo del correo mencione, en ENTREGA PARCIAL, por qué importe es esa entrega y cuánto queda pendiente sobre el pedido, y en ENTREGA TOTAL confirme la entrega total e indique los días transcurridos entre el pedido, las entregas parciales y la entrega total.
- **Cambio en `app.py` — botón de descarga del PDF**: la condición del bloque `_bloque_doc_html_interno`/`_bloque_doc_text_interno` pasa de `estado_nuevo == "ENVIADO AL PROVEEDOR"` a `estado_nuevo in ("ENVIADO AL PROVEEDOR", "ENTREGA PARCIAL", "ENTREGADO")`, reutilizando el mismo `_enlaces_descarga_pedido_doc()` y el mismo enlace público/temporal (`/descargas/adjunto/<token>`, sin login) que ya usaba el correo al proveedor y el propio correo interno de ENVIADO AL PROVEEDOR. El texto que acompaña al botón se adapta según el estado: en ENVIADO AL PROVEEDOR sigue mencionando "tramitado y enviado al proveedor"; en ENTREGA PARCIAL/ENTREGADO dice solo "puede descargar el documento del pedido", sin esa mención (no aplica). CANCELADO/DENEGADO POR DIRECCIÓN GENERAL siguen sin botón.
- **Cambio en `app.py` — importes y días en el texto**: `_resumen_entregas()` calcula ahora, por cada entrada del histórico de albaranes (`entrada_albaran_num`), los días transcurridos entre `fecha_tramitacion` del pedido y la fecha de esa entrega concreta (`dias_desde_pedido`); y a nivel de resumen añade `total_pedido` (tal cual en `pedido`), `total_pendiente` (`total_pedido - total_recibido`) y `dias_pedido_a_final` (días desde la tramitación hasta la entrega marcada `es_final`). El párrafo introductorio del correo (`_intro_html`/`_intro_text`, tanto HTML como texto plano) deja de ser un texto fijo en estos dos estados: en ENTREGA PARCIAL indica el importe de la entrega que acaba de registrarse y el importe pendiente sobre el total del pedido ("...queda pendiente la entrega de un total de X € sobre el pedido adjunto..."); en ENTREGADO confirma la entrega total e indica los días transcurridos desde la tramitación, mencionando el número de entregas parciales intermedias si las hubo. `_html_bloque_entregas()`/`_text_bloque_entregas()` (tabla de histórico de entregas) suman una columna/línea "Días desde pedido" por cada entrada, y una línea de "Pendiente de recibir sobre el total del pedido" cuando aplica (se omite en ENTREGADO, donde por definición no queda nada pendiente).
- **Verificación**: `python3 -m py_compile app.py` sin errores de sintaxis. La lógica de `_resumen_entregas()` (importes acumulados, pendiente, días por entrada y días hasta la entrega final) se probó de forma aislada, fuera de la app completa (sin acceso a Supabase de producción desde este entorno), con un caso de ejemplo — pedido tramitado el 01/08 con importe 1.000 €, dos entregas parciales (400 € y 350 €, a los 9 y 19 días) y una entrega final (250 €, a los 24 días): total recibido y pendiente correctos (1.000 € / 0 €) tanto en el corte ENTREGA PARCIAL como en ENTREGADO, y `dias_pedido_a_final` = 24. No probado en vivo contra producción — a confirmar tras desplegar registrando una entrega parcial y luego la entrega total sobre un pedido real.
- **Revisión de otros documentos (norma 5)**: `GUIA_DESPLIEGUE.md`, `PENDIENTES.md`, `INSTRUCCIONES_RESTAURACION.md` — no aplica, ninguno documenta el contenido de este correo. `docs/hallazgo-seguridad-princess.md` no existe en este repo. `README.md` sí: versión actual y sección "Alertas y notificaciones · Admin" (nuevo bullet "Correo interno de cambio de estado").
- **Entrega**: `app.py`, `templates/index.html` (badge de versión), `README.md`, más este historial/`CHANGELOG.md`. `models.py` y `requirements.txt` no cambian.

---

## 2026-09-01 — [Control Pedidos] Admin → EmailJS: 4ª cuenta de backup en la rotación, mismo panel que las otras 3 (v12.30.93)

- **Origen**: Víctor pidió añadir una 4ª cuenta EmailJS a la rotación, dejando el hueco en el panel de Admin para rellenarla él mismo tal cual rellenó las otras 3.
- **Por qué fue sencillo**: la rotación de cuentas ya estaba escrita en torno a la constante `_EMAILJS_MAX_CUENTAS` desde que se generalizó de 2 a 3 en v12.29.94 (ver esa entrada más abajo) — ni la lógica cíclica de `/api/emailjs/registrar-envio`, ni el aviso de Integridad, ni el job de avance de fechas de la v12.30.92 (entrada justo debajo) tienen ningún número de cuentas hardcodeado; todos recorren `range(1, _EMAILJS_MAX_CUENTAS + 1)` o equivalente. Solo hubo que subir la constante y añadir las claves de configuración de la cuenta nueva.
- **Cambio en `app.py`**: `_EMAILJS_MAX_CUENTAS` de 3 a 4. Nuevas claves `emailjs_public_key_4` / `emailjs_service_id_4` / `emailjs_template_id_4` / `emailjs_reinicio_fecha_4` en `_emailjs_defaults`, mismo patrón que las 3 existentes (`ON CONFLICT DO NOTHING`, no toca nada ya configurado en producción). El job `_job_avanzar_reinicio_emailjs()` (v12.30.92) pasa a iterar también n=4. Relabel cosmético en los `label` de configuración: cuenta 3 pasa de "(backup)" a "(terciaria)" y la cuenta 4 nueva toma "(backup)", para que la etiqueta siga describiendo a la última del ciclo en vez de quedarse en medio.
- **Cambio en `templates/index.html`**: la rejilla de tarjetas de `loadEmailjsConfig()` pasa de `[1,2,3].map(...)` a `[1,2,3,4].map(...)`, con la 4ª tarjeta con los mismos 4 campos que las demás (Public Key / Service ID / Template ID / Reinicia cupo el). El `grid-template-columns` de esa rejilla, antes fijo a `1fr 1fr 1fr` (3 columnas), pasa a `repeat(auto-fit, minmax(200px, 1fr))` para que se reparta bien con 4 tarjetas en pantallas anchas y las envuelva en 2 filas en pantallas estrechas, en vez de apretar 4 columnas fijas. El selector numérico "Cuenta activa" sube su tope de `max="3"` a `max="4"`, y los textos de ayuda del panel ("Rellena las N cuentas...", el ciclo "1→2→3→...") se actualizan a 4.
- **Verificación**: `python3 -m py_compile app.py` sin errores de sintaxis. La función `loadEmailjsConfig()` completa (extraída por balanceo de llaves) verificada con `node --check`, sin errores. No probado en vivo contra producción (sin acceso desde este entorno) — a confirmar tras desplegar que la 4ª tarjeta aparece vacía y lista para rellenar, sin afectar a las 3 ya configuradas.
- **Revisión de otros documentos (norma 5)**: `GUIA_DESPLIEGUE.md` sí aplica — el Paso 2 (EmailJS) decía literalmente "repite el proceso con una segunda (y una tercera) cuenta EmailJS gratuita"; reescrito a "hasta 3 cuentas EmailJS gratuitas más (hasta 4 en total)", aclarando que rellenar solo la Cuenta 1 sigue siendo válido (la app funciona igual, sin failover automático). `PENDIENTES.md` e `INSTRUCCIONES_RESTAURACION.md` — no aplica, no documentan el detalle de cuántas cuentas EmailJS hay. `docs/hallazgo-seguridad-princess.md` no existe en este repo. `README.md` sí — versión actual y sección "Sistema · Admin".
- **Entrega**: `app.py` (constante + defaults + job), `templates/index.html` (rejilla + badge de versión), `GUIA_DESPLIEGUE.md` (Paso 2), `README.md` (versión actual + sección "Sistema · Admin"), más este historial/`CHANGELOG.md`. `models.py` y `requirements.txt` no cambian.

---

## 2026-09-01 — [Control Pedidos] Admin → EmailJS: las 3 fechas "Reinicia cupo el" se avanzan solas (+30 días), sin entrar a EmailJS.com cada mes (v12.30.92)

- **Origen**: Víctor preguntó si el plan gratuito de EmailJS es mensual y, confirmado que sí, pidió automatizar el avance de las 3 fechas "Reinicia cupo el" (`emailjs_reinicio_fecha_1/2/3`, una por cuenta) para no tener que entrar a los paneles de EmailJS.com a copiarlas a mano cada ciclo.
- **Estado previo**: esas 3 fechas son puramente informativas desde que se añadieron en v12.30.14 (ver entrada de esa versión más abajo) — ningún código las leía; el cambio real de cuenta activa (rotación 1→2→3→1) depende solo del contador de envíos llegando al umbral configurable (195/200 por defecto), no de estas fechas.
- **Por qué +30 días y no "+1 mes"**: el ciclo gratuito de EmailJS es un *rolling* de 30 días desde el último reinicio, no un mes de calendario. Sumar un mes de calendario habría arrastrado un desfase en cuanto el mes de origen o destino tuviera menos de 31 días — caso real detectado en la propia conversación: la cuenta 2 tenía guardado 31/08/2026, y septiembre no tiene día 31.
- **Cambio en `app.py`**: nuevo job `_job_avanzar_reinicio_emailjs()` — por cada una de las 3 cuentas, si su fecha guardada ya pasó (`hoy > fecha`), le suma +30 días; si el servidor ha estado parado más de un ciclo sin correr el job, repite la suma hasta que la fecha vuelva a caer en el futuro (evita arrastrar un desfase acumulado). Registrado en `_iniciar_scheduler()` como `avanzar_reinicio_emailjs`, cron diario a las 06:00, **todos los días** (a diferencia de la mayoría de jobs de este scheduler, que solo corren lun-vie — el cupo de EmailJS también se resetea en fin de semana). Puramente informativo: no toca `emailjs_cuenta_activa` ni `emailjs_contador`, ni la rotación real de cuentas.
- **Verificación**: `python3 -m py_compile app.py` sin errores de sintaxis. No probado en vivo contra el scheduler real de producción (sin acceso desde este entorno) — a confirmar en el primer ciclo tras desplegar: la fecha de la cuenta 2 (31/08/2026, ya vencida a fecha de esta entrega) debería avanzar sola a 30/09/2026 en el primer job de las 06:00.
- **Revisión de otros documentos (norma 5)**: `GUIA_DESPLIEGUE.md`, `PENDIENTES.md` e `INSTRUCCIONES_RESTAURACION.md` — no aplica, ninguno documenta el detalle de estas fechas ni el cambio afecta a pasos de despliegue o restauración. `docs/hallazgo-seguridad-princess.md` no existe en este repo. `README.md` sí — versión actual y sección "Sistema · Admin" (bullet "EmailJS y cola de correo").
- **Entrega**: `app.py` (job nuevo + alta en el scheduler), `templates/index.html` (badge de versión), `README.md` (versión actual + sección "Sistema · Admin"), más este historial/`CHANGELOG.md`. `models.py` y `requirements.txt` no cambian.

---

## 2026-09-01 — [Control Pedidos] Panel "Emails de sistema atascados": también cierra sin reenviar las filas ya DESCARTADAS a mano (v12.30.91)

- **Origen**: al revisar el panel en vivo tras la v12.30.90, las 3 filas del incidente original (pedidos 16445/28252/41254) resultaron estar ya "descartadas" (alguien las descartó a mano cuando esa era la única opción disponible), no "paradas" como se había asumido — así que el botón nuevo de la v12.30.90 (pensado para filas "paradas") no las cubría: seguían mostrando solo "↻ Reactivar", que sí reenvía el correo de verdad y habría producido un 4º envío real.
- **Cambio en `templates/index.html`**: en `_cargarEmailsAtascados()`, la rama de filas descartadas (`descartado_en` no nulo) muestra ahora también "✅ Marcar como enviado" junto a "↻ Reactivar", con tooltips que distinguen cuál de los dos reenvía de verdad (Reactivar) y cuál no (Marcar como enviado — cierra el registro y aplica `GREATEST` sobre `comunicado_ab`/`comunicado_jefe_dep`, mismo endpoint `marcar-enviado`).
- **`app.py` no cambia**: mismo endpoint reutilizado, sin condición sobre `descartado_en`.
- **Verificación**: `node --check` sobre la función aislada, sin errores. Pendiente de confirmar en el panel real tras desplegar: las 3 filas de 16445/28252/41254 deberían mostrar ya ambos botones.
- **Revisión de otros documentos** (norma 5): igual que en v12.30.90 — no aplica a `GUIA_DESPLIEGUE.md`, `PENDIENTES.md`, `INSTRUCCIONES_RESTAURACION.md`, `docs/hallazgo-seguridad-princess.md`. `README.md` sí: versión actual y sección "Sistema · Admin".
- **Entrega**: `templates/index.html`, `README.md`, más este historial/`CHANGELOG.md`. `app.py` y `requirements.txt` no cambian.

---

## 2026-09-01 — [Control Pedidos] Panel "Emails de sistema atascados": permite cerrar a mano filas "paradas" anteriores al fix de v12.30.89 (los 3 pedidos del incidente original) (v12.30.90)

- **Origen**: repaso del incidente de la v12.30.89 (correo interno "ENVIADO AL PROVEEDOR" duplicado, pedidos LP 16445 / IT 28252 / GY 41254). Ese fix corrige la causa raíz hacia delante, pero deja sin corregir los 3 registros ya afectados: sus filas en `emails_sistema_pendientes` agotaron los reintentos ANTES de que existiera la columna `enviado_no_confirmado` (añadida en el mismo fix), así que quedaron "paradas" (`atascado=TRUE`) con `enviado_no_confirmado=FALSE` — el panel solo les ofrecía "Descartar", que cierra la fila sin aplicar `GREATEST` sobre `comunicado_ab`/`comunicado_jefe_dep`. Resultado: las casillas "Comunicado A&B" / "Comunicado Jefe Dep." de esos 3 pedidos siguen sin marcar aunque el correo sí se entregó de verdad (confirmado por capturas de Gmail). Como esas casillas están bloqueadas para edición manual desde la v12.30.65, no había ninguna vía para corregirlas sin este cambio.
- **Cambio en `templates/index.html`**: en `_cargarEmailsAtascados()`, las filas "paradas" sin `enviado_no_confirmado` (y sin descartar) muestran ahora dos botones — "✅ Marcar como enviado" (mismo endpoint `POST /api/emails-sistema-pendientes/<id>/marcar-enviado`, que ya aplica `GREATEST` sobre las marcas de comunicado desde la v12.30.89) junto al "Descartar" ya existente — con tooltip explícito de que solo debe pulsarse si el admin ha confirmado por otra vía (p. ej. bandeja de enviados) que el correo llegó de verdad, a diferencia del caso `enviado_no_confirmado=TRUE` donde esa garantía ya es automática.
- **`app.py` no cambia**: el endpoint `marcar-enviado` ya soportaba este caso desde la v12.30.89 (recibe cualquier `id` con `enviado=FALSE`); solo faltaba exponer el botón para esta situación concreta en el frontend.
- **Verificación**: `node --check` sobre la función `_cargarEmailsAtascados()` aislada, sin errores de sintaxis. No probado contra base de datos real (sin acceso a Supabase de producción desde este entorno); pendiente de confirmar tras desplegar: entrar en Admin → "Emails de sistema atascados", localizar las filas `cambio_estado_interno` de los pedidos 16445/28252/41254 y pulsar "✅ Marcar como enviado" en cada una, comprobando que las casillas de comunicado de esos pedidos quedan marcadas según corresponda (A&B solo si el departamento del pedido es COCINA/BARES/RESTAURANTE/RESTAURANTE & BARES — confirmado en 16445, pendiente de revisar en 28252/41254; Jefe Dep. solo si ese hotel+departamento tiene correo configurado en `departamento_hotel_email`).
- **Revisión de otros documentos** (norma 5): `GUIA_DESPLIEGUE.md`, `PENDIENTES.md`, `INSTRUCCIONES_RESTAURACION.md`, `docs/hallazgo-seguridad-princess.md` — no aplica, ninguno documenta este panel. `README.md` sí: versión actual y sección "Sistema · Admin".
- **Entrega**: `templates/index.html`, `README.md`, más este historial/`CHANGELOG.md`. `app.py` y `requirements.txt` no cambian.

---

## 2026-09-01 — [Control Pedidos] Corrección: duplicados reales del correo interno de cambio de estado — causa raíz + red de seguridad (v12.30.89)

- **Origen**: Víctor reportó que el correo interno de cambio de estado (ENVIADO AL PROVEEDOR / ENTREGA PARCIAL / ENTREGA TOTAL) se enviaba varias veces, descontando cupo de EmailJS cada vez. Aportó capturas de Gmail (3 correos idénticos espaciados 5 min, pedidos LP 16445 / IT 28252 / GY 41254) y, tras dos intentos con la franja horaria equivocada, el log real de Render de la franja del incidente (12:26–12:36 UTC).
- **Diagnóstico**: el flujo normal envía de verdad con `emailjs.send()` y luego confirma con `POST /api/emails-sistema-pendientes/<id>/marcar-enviado`. Si la confirmación fallaba (antes: 3 reintentos de ~1s), la fila quedaba `enviado=FALSE`, la reserva de 2 min caducaba, y el siguiente sondeo del poller (5 min después) la reclamaba y volvía a llamar a `emailjs.send()` **de verdad** — un envío real duplicado, no un simple reintento. El log de la franja correcta confirmó el patrón exacto: de cada 2 filas por pedido, la del correo al proveedor confirmaba con 200 a la primera, y la del correo interno (la que activa `marca_comunicado_ab`/`marca_comunicado_jefe_dep`) devolvía **500 de forma 100% determinista**, igual en los 3 ciclos del poller (12:26, 12:31, 12:36).
- **Causa raíz encontrada**: `pedidos.comunicado_ab`/`comunicado_jefe_dep` son columnas `INTEGER` (0/1), como en el resto de `app.py`. El bloque del 31-08 (`api_marcar_email_sistema_enviado`) hacía `comunicado_ab = (comunicado_ab OR %s)` — el `OR` lógico de SQL aplicado directamente sobre un entero, que PostgreSQL rechaza con un error de tipo siempre. Esa rama solo se dispara con `marca_comunicado_ab`/`marca_comunicado_jefe_dep` a `True`, y eso solo ocurre en el correo interno de "ENVIADO AL PROVEEDOR" — de ahí que fallasen justo esos correos, y solo esos, el 100% de las veces.
- **Cambio en `app.py`**: fix de la causa raíz — `(comunicado_ab OR %s)` → `GREATEST(comunicado_ab, %s)`, con enteros 0/1 en vez de booleanos de Python (mismo patrón que el resto de la app). Además, como red de seguridad para que un fallo de confirmación por cualquier otra causa no vuelva a duplicar un envío real: nueva columna `emails_sistema_pendientes.enviado_no_confirmado` y nuevo endpoint mínimo `POST /api/emails-sistema-pendientes/<id>/marcar-enviado-no-confirmado` (un único UPDATE, sin tocar `pedidos`) que sube `intentos` a `MAX_INTENTOS_EMAIL_SISTEMA` — la fila deja de reclamarse para siempre en vez de reenviarse al caducar la reserva. `api_emails_sistema_atascados` devuelve también `enviado_no_confirmado`.
- **Cambio en `templates/index.html`**: confirmación más robusta (de 3 intentos en ~2s a 7 intentos con backoff hasta ~90s); si se agotan, llama al nuevo endpoint de bloqueo en vez de dejar la fila expuesta a reenvío. Panel "Emails de sistema atascados": estas filas se distinguen con "✅ se envió, sin confirmar en BD" y un botón "Marcar como enviado" — nunca "Reactivar" (que sí reenviaría de verdad).
- **Verificación**: `python3 -m py_compile app.py` sin errores; `node --check` sobre los bloques `<script>` tocados. Diagnóstico confirmado contra los logs reales de Render de la franja del incidente (patrón 200/500×3 por pedido, repetido en los 3 ciclos del poller). No se ha podido reproducir contra una base de datos real desde este entorno (sin acceso a Supabase de producción).
- **Revisión de otros documentos** (norma 5): `GUIA_DESPLIEGUE.md`, `PENDIENTES.md`, `INSTRUCCIONES_RESTAURACION.md`, `docs/hallazgo-seguridad-princess.md` — no aplica, ninguno documenta esta cola ni estas columnas. `README.md` sí: versión actual y sección "Sistema · Admin".
- **Entrega**: `app.py`, `templates/index.html`, `README.md`, más este historial/`CHANGELOG.md`. `requirements.txt` no cambia.

---

## 2026-09-01 — [Control Pedidos] Repaso "agilizar y limpiar", Etapa 4 (última): `loadUsuarios()` deja de hacer una petición por usuario (v12.30.88)

- **Origen**: última etapa pendiente del repaso; Víctor confirmó seguir adelante ("CON QUE SEGUIMOS?").
- **Hallazgo** (ya identificado en la auditoría inicial, v12.30.85): `loadUsuarios()` llamaba a `/api/maestros` de forma redundante (`G.maestros` ya está en memoria desde el arranque) y hacía una petición HTTP por cada usuario con rol hotel/compras/user para sus hoteles asignados — con 40 usuarios, ~40 peticiones solo para pintar la pestaña.
- **Cambio en `app.py`**: nuevo `GET /api/usuarios/hoteles-asignados` — 2 consultas totales (`usuario_hoteles`, `usuario_comprador_hoteles`), agrupadas por `usuario_id` en Python. Los endpoints por usuario existentes no se tocan (los sigue usando el modal de edición).
- **Cambio en `templates/index.html`**: `loadUsuarios()` reescrita — ya no llama a `/api/maestros` (reutiliza `G.maestros.hoteles`) ni hace una llamada por usuario; una sola llamada a `/api/usuarios/hoteles-asignados`. Si falla, la tabla se pinta igual sin esas columnas en vez de romperse.
- **Verificación**: `python3 -m py_compile app.py` sin errores; `node --check` sobre los `<script>`. Agrupación del backend probada con datos de ejemplo. Frontend probado con harness Playwright y `api()` simulada (5 usuarios, los 4 roles): 2 llamadas totales en vez de 6 en este ejemplo pequeño (y la diferencia crece con cada usuario), mismos datos mostrados que antes por rol — 10 comprobaciones, todas correctas.
- **Cierre**: con esta entrega terminan las 4 etapas del repaso "agilizar y limpiar" (v12.30.85 a v12.30.88).
- **Entrega**: `app.py`, `templates/index.html`, `README.md`, más este historial/`CHANGELOG.md`. `requirements.txt` no cambia.

---

## 2026-09-01 — [Control Pedidos] Repaso "agilizar y limpiar", Etapa 3: botón "Exportar histórico" de expedientes a Excel (v12.30.87)

- **Origen**: cierre de la duda abierta en v12.30.86 sobre si algo externo consumía `GET /api/expedientes` sin paginar. Víctor preguntó si el botón "Imprimir" de Techo de Gastos ya mostraba esa información — se comprobó que no (usa `/api/techo/resumen-historico`, siempre acotado a un mes/año, fuente distinta) — y a partir de ahí pidió una solución mejor que paginar: un botón para exportar el histórico completo a Excel, "en cualquier momento".
- **Cambio en `app.py`**: nuevo `GET /api/expedientes/exportar` — misma consulta y filtros opcionales que `listar_expedientes()`, sin filtros exporta el histórico entero. Excel con `openpyxl`, mismo patrón visual que `exportar_excel()` (Pedidos): cabecera azul de marca, filas coloreadas por resultado (verde/amarillo/rojo, mismo criterio semáforo que Techo de Gastos en pantalla), formato moneda y fecha, mes legible ("Agosto 2026"), texto largo con ajuste de línea, fila de totales, auto-filtro, cabecera fija.
- **Cambio en `templates/index.html`**: botón "⬇ Exportar histórico" en Techo de Gastos, junto a "🖨️ Imprimir" pero con estilo distinto para no confundirlos. Nueva `exportarExpedientesExcel()`, mismo patrón que `exportarExcel()`.
- **`GET /api/expedientes` no se toca**: sigue sin paginar y sin uso en el frontend — el histórico completo ahora se consulta por el nuevo botón, no hace falta la pantalla de listado (Fase 6) que iba a depender de esa paginación.
- **Verificación**: `python3 -m py_compile app.py` sin errores; `node --check` sobre los `<script>` de `index.html`. Generación del Excel probada aparte con datos de prueba (incluidos casos límite: valores nulos, mes mal formado, expediente sin resolver) — estructura, colores, formatos y totales comprobados leyendo el `.xlsx` con `openpyxl`, y convertido a PDF con LibreOffice para una comprobación visual real (así se encontró y corrigió que la columna HOTEL quedaba en blanco en vez de "—" cuando faltaban ambos datos). Frontend probado con harness Playwright y `fetch` simulado — 10 comprobaciones, todas correctas.
- **Revisión de otros documentos** (norma 5): `GUIA_DESPLIEGUE.md`, `PENDIENTES.md`, `INSTRUCCIONES_RESTAURACION.md`, `docs/hallazgo-seguridad-princess.md` — no aplica. `README.md` sí: "Funcionalidades principales" (nuevo botón documentado) y "Rendimiento" (Etapa 6 añadida, nota "Pendiente" reducida a `loadUsuarios()`).
- **Entrega**: `app.py`, `templates/index.html`, `README.md`, más este historial/`CHANGELOG.md`. `requirements.txt` no cambia (`openpyxl` ya estaba pinneado desde antes).

---

## 2026-09-01 — [Control Pedidos] Repaso "agilizar y limpiar", Etapa 2: paginada la papelera de Pedidos Eliminados (v12.30.86)

- **Origen**: continuación de v12.30.85. Víctor confirmó seguir por etapas ("continuamos?"); esta ataca `GET /api/pedidos_eliminados`, la candidata con más impacto real en egress de las tres pendientes.
- **Hallazgo al implementar**: se comprobó que `GET /api/expedientes` (la otra candidata) no la llama nada en el frontend actual — búsqueda completa sin resultados salvo las rutas de acción (`aprobar`/`denegar`/`informe`), y su propio docstring ya avisaba de que la paginación quedaba para una "Fase 6" que nunca se construyó. Se decidió centrar esta etapa en Eliminados (uso confirmado, `loadEliminados()`) y dejar `/api/expedientes` pendiente de una respuesta de Víctor — sin saber si algo externo al repo la consume sin parámetros de paginación, no se le pone límite por defecto sin confirmarlo antes.
- **Cambio en `app.py`**: `GET /api/pedidos_eliminados` acepta ahora `page`/`page_size` (por defecto 30, máx. 100), responde `{registros,total,page,page_size,pages}` en vez del array completo. Se mantiene la clave `"registros"`.
- **Cambio en `templates/index.html`**: `loadEliminados()` reescrita para pedir por páginas; `renderElimPagination()`/`goElimPage()` nuevas (mismo patrón visual que Proveedores); nuevo bloque de paginación (`#elim-pagination`, `#elim-page-info-text`); `G.elimPage/elimPages/elimTotal` nuevos.
- **Verificación**: `python3 -m py_compile app.py` sin errores; `node --check` sobre los 9 bloques `<script>` extraídos de `index.html`. Consulta de paginación probada contra PostgreSQL 16 real (73 filas de prueba, 3 páginas). Lógica de frontend probada con un harness Playwright aislado (`api()` mockeada) — 9 comprobaciones (carga página 1, salto a página 3, vuelta a página 1), todas correctas.
- **Revisión de otros documentos** (norma 5): `GUIA_DESPLIEGUE.md`, `PENDIENTES.md`, `INSTRUCCIONES_RESTAURACION.md`, `docs/hallazgo-seguridad-princess.md` — no aplica, ninguno documenta esto. `README.md` sí: sección "Rendimiento" actualizada (nueva "Etapa 5", nota "Pendiente" reducida a `/api/expedientes` con la pregunta abierta a Víctor, y `loadUsuarios()`).
- **Entrega**: `app.py`, `templates/index.html`, `README.md`, más este historial/`CHANGELOG.md`. `requirements.txt` no cambia.

---

## 2026-09-01 — [Control Pedidos] Repaso "agilizar y limpiar", Etapa 1: índices que faltaban en `pedidos` y `historial_estados` (v12.30.85)

- **Origen**: Víctor pidió una revisión nueva de rendimiento/limpieza tras cerrar la documentación (v12.30.83-84), avisando explícitamente de tener en cuenta el consumo de egress de Supabase. Barrido con 2 agentes en paralelo (backend/frontend); cada hallazgo relevante se verificó a mano contra el código real antes de reportarlo. Aprobado ir por etapas — esta es la primera.
- **Aviso sobre egress**: esta etapa es una mejora de velocidad/cómputo, no de egress — `GET /api/pedidos` ya estaba paginado desde la Etapa 2, así que el volumen de datos devuelto no cambia. Las etapas que sí reducen egress (`/api/expedientes`, "Eliminados") quedan para después — ver nota "Pendiente" añadida en `README.md` § Rendimiento.
- **Hallazgo verificado**: `get_pedidos()` filtra por `hotel_id`/`estado`/`departamento_id`/`fecha_solicitud` y ordena por `creado_en`/`norden`, sin índice propio en ninguna de esas columnas — ni el listado paginado ni su `COUNT(*)` de paginación podían evitar recorrer la tabla entera. Mismo problema en `historial_estados.pedido_id` (detalle de cada pedido).
- **Cambio**: en `_auto_migrate()`, índices B-tree en `pedidos(hotel_id/estado/departamento_id/fecha_solicitud/creado_en/norden)`, un índice parcial en `pedidos(fecha_tramitacion) WHERE fecha_tramitacion IS NOT NULL`, y un índice compuesto `historial_estados(pedido_id, creado_en DESC)`. Mismo patrón que los índices `pg_trgm` ya existentes (cada `CREATE INDEX IF NOT EXISTS` en su propio `try/except`).
- **Verificación**: `python3 -m py_compile app.py` sin errores. PostgreSQL 16 real montado en este entorno con ~80.000 pedidos / ~200.000 filas de historial (volumen realista según el propio dashboard de Víctor); `EXPLAIN` de las 4 consultas afectadas antes/después confirma el paso de `Seq Scan`/`Parallel Seq Scan` a `Index Scan`/`Bitmap Index Scan` en las 4.
- **Revisión de otros documentos** (norma 5 de arriba): `GUIA_DESPLIEGUE.md`, `PENDIENTES.md`, `INSTRUCCIONES_RESTAURACION.md` y `docs/hallazgo-seguridad-princess.md` revisados — ninguno documenta nada relacionado con estos índices, no requieren cambios. `README.md` sí: se actualizó la sección "Rendimiento" (nueva entrada de esta etapa, se corrigió el párrafo final que ya estaba desactualizado sobre `PEDIDO_SELECT` —resuelto en v12.30.82-83— y se añadió una nota "Pendiente" con las 3 etapas que quedan).
- **Entrega**: `app.py`, `templates/index.html` (badge de versión), `README.md`, más este historial/`CHANGELOG.md`. `requirements.txt` no cambia.

---

## 2026-09-01 — [Control Pedidos] Limpieza documental: eliminado archivo obsoleto que no se había borrado de verdad (v12.30.84)

- **Origen**: al revisar la documentación por el aviso de Víctor de mantenerla siempre al día (v12.30.83), se vio que `CAMBIOS_solicitud_directa_backend.md` seguía en el ZIP del proyecto, pese a que esta misma historia (v12.30.79) decía que se había eliminado. Víctor preguntó qué recomendaba y, tras confirmar que el archivo era realmente obsoleto y no tenía ninguna otra referencia en el proyecto salvo las entradas históricas que documentan su eliminación, pidió borrarlo ("bórralo").
- **Contenido revisado de nuevo antes de borrar**: describía `POST /api/solicitar-usuario/directo` mencionando `init_db()` (retirada del código hace varias versiones) y avisando de que no se había podido probar contra una base de datos real — el endpoint lleva en producción desde v12.20.2, con entrada completa y actualizada en `CHANGELOG.md`.
- **Cambio**: archivo eliminado. Sin cambios de código (`app.py`/`templates/index.html` solo llevan el badge de versión).
- **Entrega**: eliminación de `CAMBIOS_solicitud_directa_backend.md`, `templates/index.html` (badge de versión), `README.md` (versión actual), más este historial/`CHANGELOG.md`.

---

## 2026-09-01 — [Control Pedidos] Corrección: el email de respaldo del proveedor ahora respeta el hotel del pedido (v12.30.83)

- **Origen**: al cerrar la v12.30.82, se detectó al margen (no era lo que se estaba preguntando) un segundo problema en la misma subconsulta de respaldo (`proveedor_email`): no tenía en cuenta el hotel del pedido, a diferencia de `_get_proveedor_emails_principales()` (la función "buena"), que sí lo hace desde siempre. Se dejó anotado sin tocar, Víctor confirmó que sí quería corregirlo ("si por favor").
- **Caso de borde que corrige**: un proveedor con contactos "principal" distintos asignados a hoteles distintos (agenda de Proveedores). Si el camino "bueno" no encontraba destinatario aplicable (caso de respaldo, poco frecuente), la subconsulta podía devolver el contacto "principal" de **otro** hotel del mismo proveedor — el aviso automático podía, en teoría, acabar en el hotel equivocado.
- **Cambio**: la subconsulta de respaldo aplica ahora el mismo criterio que `_get_proveedor_emails_principales()`: prioridad al contacto "principal" asignado específicamente al hotel del pedido (`proveedor_contacto_hoteles`); si no hay ninguno, cae solo a los contactos "principal" generales (sin hotel asignado); nunca a uno de un hotel distinto. Aplicado en los mismos 4 sitios que la v12.30.82.
- **Sin cambio de comportamiento** para el caso normal: proveedor sin contactos asignados a hoteles concretos (la inmensa mayoría) — resultado idéntico al de siempre.
- **Verificación**: `python3 -m py_compile app.py` sin errores. Se montó PostgreSQL 16 real en este entorno (no SQLite, por la subconsulta correlacionada de dos niveles) con 6 escenarios (contacto único general, hotel-match vs. general, contacto solo de otro hotel sin respaldo, contacto multi-hotel, empate por `orden`, pedido sin hotel) — los 6 con el resultado esperado. Las 4 cadenas SQL finales de `app.py` (incluida la de comillas escapadas `\'` en `_JOB_PEDIDO_SQL`) validadas con `EXPLAIN` contra esa base de datos.
- **Entrega**: `app.py`, `templates/index.html` (badge de versión), `README.md` (versión actual — llevaba desde v12.30.81 sin actualizar; corregido a raíz de un aviso del usuario pidiendo mantener toda la documentación al día en cada entrega, ver nota abajo), más este historial/`CHANGELOG.md`. `requirements.txt` no cambia.
- **Nota de proceso**: el usuario pidió explícitamente que, de aquí en adelante, cada entrega revise y actualice todo archivo de documentación que lo requiera (`CHANGELOG.md`, `docs/HISTORIAL_CAMBIOS.md`, badge de versión, `README.md`, y cualquier otro — `GUIA_DESPLIEGUE.md`, `PENDIENTES.md`, `INSTRUCCIONES_RESTAURACION.md` — cuando el cambio afecte a algo que documenten). Al revisar por este motivo se encontró que `README.md` llevaba 2 versiones sin actualizarse (se quedó en v12.30.81 en las entregas v12.30.82 y v12.30.83); corregido aquí. Se revisaron también `GUIA_DESPLIEGUE.md`, `PENDIENTES.md` e `INSTRUCCIONES_RESTAURACION.md`: ninguno documenta nada relacionado con `proveedor_email` o el hotel del pedido, así que no requieren cambios en esta entrega.

---

## 2026-09-01 — [Control Pedidos] Auditoría de rendimiento — cierre: email de respaldo del proveedor determinista con varios contactos "principal" (v12.30.82)

- **Origen**: punto pendiente de la Etapa 2 de la auditoría de rendimiento (v12.30.71) — la fusión de subconsultas de `PEDIDO_SELECT` se dejó sin hacer porque un proveedor puede tener varios contactos "principal" a la vez, sin criterio decidido de a cuál dar preferencia. Víctor preguntó si ese dato se usa de verdad; confirmado que sí (ver más abajo); pidió seguir adelante ("sigue adelante, acepto tu criterio").
- **Confirmado antes de tocar nada**: `proveedor_email` no es solo informativo — `_encolar_reclamacion_proveedor_auto()` lo usa como respaldo cuando `_get_proveedor_emails_principales()` (la función correcta, que sí tiene en cuenta el hotel) no encuentra ningún contacto aplicable. Ese respaldo decide a quién se manda un correo automático real.
- **Cambio**: `ORDER BY orden,id` añadido a la subconsulta de `proveedor_email` en los 4 sitios donde aparece (`enviar_emails_estado()`, `_JOB_PEDIDO_SQL`, `PEDIDO_SELECT_ALERTA`, `PEDIDO_SELECT`) — elige siempre el contacto principal más antiguo con email, mismo criterio que ya usaba `_get_proveedor_emails_principales()`. Sin cambio de comportamiento para proveedores con 0 o 1 contacto principal (la mayoría); solo se vuelve predecible el caso de varios.
- **Nota**: la fusión de subconsultas que motivó esta pregunta ya no aplica — entre v12.30.71 y esta entrega, otro cambio ya quitó `proveedor_movil`/`proveedor_contacto_nombre` de `PEDIDO_SELECT`, así que solo queda una subconsulta afectada por el "empate", sin nada más con lo que fusionarla. Este cambio es de consistencia/corrección, no de rendimiento.
- **Verificación**: `python3 -m py_compile app.py` sin errores.
- **Entrega**: `app.py`, `templates/index.html` (badge de versión), más este historial/`CHANGELOG.md`.

---

## 2026-09-01 — [Control Pedidos] Reproducibilidad, Etapa 9 (última): requirements.txt fijado a versiones exactas (v12.30.81)

- **Origen**: cierre del segundo punto pendiente de la auditoría general (Etapas 1-8, v12.30.73-80). `requirements.txt` usaba `>=`, con riesgo de que un deploy nuevo instalara silenciosamente una versión más reciente y rompiera algo sin cambios de código.
- **Origen de los números**: log de build real de Render pegado por el usuario (Shell no disponible en plan free) — no inventados.
- **Cambio**: las 9 dependencias directas fijadas con `==`, más las 12 transitivas también fijadas explícitamente, para reproducibilidad completa del entorno.
- **Verificación**: instalado en un venv limpio en este entorno de trabajo, sin errores ni conflictos. No se ha probado la app real contra estas versiones (son las mismas que ya corren en Render).
- **Entrega**: `requirements.txt`, `templates/index.html` (badge de versión), más este historial/`CHANGELOG.md`.
- **Cierre**: con esta entrega termina también el segundo (y último) punto pendiente de la auditoría general — 9 etapas, v12.30.73 a v12.30.81.

---

## 2026-08-31 — [Control Pedidos] Limpieza, Etapa 8: 2 columnas muertas en 4 consultas de pedidos (v12.30.80)

- **Origen**: al aclarar con el usuario el criterio de negocio de `PEDIDO_SELECT` (v12.30.79), se confirmó que 2 de los 5 campos de proveedor (`proveedor_movil`, `proveedor_contacto_nombre`) no los lee nadie en toda la aplicación.
- **Verificación previa clave**: confirmado que la agenda de proveedores (`/api/proveedores`, `_prov_with_contactos()`) es un camino de código distinto e independiente, no afectado por este cambio — el usuario pidió explícitamente no tocar esa información visual.
- **Cambio**: quitadas ambas subconsultas de las 4 consultas que las calculaban sin usarlas: `PEDIDO_SELECT`, `PEDIDO_SELECT_ALERTA`, `_JOB_PEDIDO_SQL`, y la consulta inline de emails pendientes (~línea 2440).
- **Verificación**: `py_compile` sin errores, revisión visual de las 4 consultas, búsqueda completa sin referencias residuales. Sin poder probar contra base de datos real desde este entorno — recomendable verificar tras desplegar.
- **Entrega**: `app.py`, `templates/index.html` (badge de versión), más este historial/`CHANGELOG.md`.

---

## 2026-08-31 — [Control Pedidos] Auditoría documental, Etapa 7: doc duplicado + UptimeRobot desactualizado + confirmación de código muerto (v12.30.79)

- **Origen**: continuación de la auditoría general (Etapas 1-6, v12.30.73-78) tras revisar los 2 documentos que quedaban sin auditar.
- **Hallazgo 1**: `CAMBIOS_solicitud_directa_backend.md` — nota de entrega obsoleta de un endpoint que lleva en producción desde v12.20.2 (58 versiones), con entrada más completa ya en `CHANGELOG.md`. Eliminado, junto con su referencia en `README.md`.
- **Hallazgo 2**: "UptimeRobot" desactualizado en `GUIA_DESPLIEGUE.md` (stack, Paso 5, costes) y `README.md` (2 menciones) — el mecanismo real, documentado solo en este mismo historial pero nunca propagado a la guía del proyecto, es el workflow de GitHub Actions. Corregido en los 3 sitios + un comentario en `app.py`.
- **Aviso fuera de alcance**: el repo hermano `control-pedidos-chat` tiene el mismo bug de cron frágil ante el cambio de hora que se corrigió aquí en la Etapa 5 — pendiente, en otro repositorio.
- **Hallazgo 3 (negativo)**: rastreo estático de las 298 funciones de `app.py` — confirmado que no queda código muerto aparte del `init_db()` ya retirado en la Etapa 6.
- **Entrega**: `GUIA_DESPLIEGUE.md`, `README.md`, `app.py` (comentario), eliminación de `CAMBIOS_solicitud_directa_backend.md`, `templates/index.html` (badge de versión), más este historial/`CHANGELOG.md`.

---

## 2026-08-31 — [Control Pedidos] Limpieza, Etapa 6 (última): variables sin uso en render.yaml + init_db() muerta en app.py (v12.30.78)

- **Origen**: cierre de la auditoría general (Etapas 1-5, v12.30.73-77), petición inicial del usuario.
- **Hallazgo 1**: `RESEND_API_KEY`/`EMAIL_FROM`/`EMAILS_INTERNOS` en `render.yaml`, sin uso real en ningún punto del código (email va por EmailJS; destinatarios internos se leen de la BD). Eliminadas de `envVars`.
- **Hallazgo 2**: función `init_db()` en `app.py`, sin llamadas en todo el proyecto (el proceso real es el script `init_db.py`). Eliminada, junto con el import huérfano de `SQL_STATEMENTS` y un comentario que la referenciaba.
- **Verificación**: `python3 -m py_compile app.py models.py init_db.py` sin errores; búsqueda completa sin referencias residuales.
- **Entrega**: `render.yaml`, `app.py`, `GUIA_DESPLIEGUE.md` (tabla de variables), `templates/index.html` (badge de versión), más este historial/`CHANGELOG.md`.
- **Cierre**: con esta entrega termina la auditoría general solicitada por el usuario — 6 etapas, v12.30.73 a v12.30.78.

---

## 2026-08-31 — [Infra] Auditoría/limpieza, Etapa 5: cron del keep-alive frágil ante el cambio de hora (v12.30.77)

- **Origen**: continuación de la auditoría general (Etapas 1-4, v12.30.73-76).
- **Hallazgo**: `.github/workflows/keep-alive-princess.yml` fijaba la ventana del cron para horario de verano, con un comentario indicando que había que cambiarla a mano en invierno — riesgo de que el servicio gratuito de Render se quede dormido en horario laboral real si se olvida.
- **Cambio**: ventana ensanchada de `5-16` a `5-18` UTC — cubre 06:00-18:00 hora Canarias en las dos estaciones (unión de las ventanas UTC de verano e invierno) sin necesidad de tocar el archivo nunca más. Coste: ~1h de pings de más en cada extremo según la época, sin impacto práctico.
- **Entrega**: `.github/workflows/keep-alive-princess.yml`, `templates/index.html` (badge de versión), más este historial/`CHANGELOG.md`.

---

## 2026-08-31 — [Control Pedidos] Auditoría documental, Etapa 4: README sin mencionar las 3 etapas de rendimiento (v12.30.76)

- **Origen**: continuación de la auditoría general (Etapas 1-3, v12.30.73-75).
- **Hallazgo**: el README no mencionaba las 3 etapas de auditoría de rendimiento ya desplegadas (v12.30.70-72) — paginación de Proveedores, índices GIN por trigramas, compresión gzip.
- **Cambio**: nueva sección "Rendimiento" en `README.md`, entre "Migraciones de base de datos" y "Puesta en marcha", resumiendo las 3 etapas, el trabajo previo del que parten, y el único punto señalado en la auditoría y dejado pendiente a propósito (`PEDIDO_SELECT`).
- **Entrega**: `README.md`, `templates/index.html` (badge de versión), más este historial/`CHANGELOG.md`.

---

## 2026-08-31 — [Control Pedidos] Auditoría/limpieza, Etapa 3 (agrupada): favicons sobredimensionados + Thumbs.db (v12.30.75)

- **Origen**: continuación de la auditoría general (Etapas 1-2, v12.30.73/74). Dos hallazgos independientes y de bajo riesgo, agrupados a petición del usuario.
- **Hallazgo 1**: `static/favicon.png` y `static/favicon-180.png` eran ambos de 1024×1024 px (236 KB y 295 KB) pese a usarse como icono de pestaña y `apple-touch-icon` — el segundo debía ser 180×180 exactos por el propio estándar que le da nombre. Redimensionados a 64×64 y 180×180 respectivamente: 236 KB → 2,1 KB, 295 KB → 11,3 KB (531 KB menos en cada carga de página). Rutas sin cambios, `templates/index.html` no se toca salvo el badge de versión.
- **Hallazgo 2**: `static/Thumbs.db` (caché de miniaturas de Windows, sin uso) seguía en el repo pese a estar ya en `.gitignore` — la regla se añadió después de que el archivo quedara trackeado. Eliminado.
- **Verificación**: inspección visual del favicon redimensionado (sin artefactos); confirmado que nada referencia `Thumbs.db`. Sin cambios de código Python.
- **Entrega**: `static/favicon.png`, `static/favicon-180.png`, eliminación de `static/Thumbs.db`, `templates/index.html` (badge de versión), más este historial/`CHANGELOG.md`.

---

## 2026-08-31 — [Control Pedidos] Auditoría documental, Etapa 2: documento de seguridad obsoleto corregido (v12.30.74)

- **Origen**: continuación de la Etapa 1 (GUIA_DESPLIEGUE.md, v12.30.73).
- **Hallazgo**: `docs/hallazgo-seguridad-princess.md` marcaba como "Sin corregir" un fallo de contraseñas en texto plano que en realidad se corrigió en v12.29.37 (hash con werkzeug + migración transparente al primer login). El documento nunca se actualizó tras el fix.
- **Verificación**: releído `login()`/`_verifica_y_migra_password()` actuales y las 4 rutas que escriben la columna `password` — todas usan `generate_password_hash()`/`check_password_hash()`. `init_db.py`, `models.py` e `INSTRUCCIONES_RESTAURACION.md` no crean contraseñas en claro en ningún punto.
- **Cambio**: añadido recuadro "✅ RESUELTO" al principio del documento con el estado real; el análisis original se conserva íntegro, marcado como histórico (útil para Organizador/Chat si tienen el mismo problema pendiente).
- **Entrega**: `docs/hallazgo-seguridad-princess.md`, `templates/index.html` (badge de versión), más este historial/`CHANGELOG.md`.

---

## 2026-08-31 — [Control Pedidos] Auditoría documental, Etapa 1: `GUIA_DESPLIEGUE.md` corregida (v12.30.73)

- **Origen**: petición del usuario de auditar la app en busca de "fallos e incongruencias... archivos fuera de lugar, README, changelog, index, algo desactualizado". Se acordó abordarlo por etapas, documentando cada una.
- **Hallazgo**: `GUIA_DESPLIEGUE.md` describía un despliegue que ya no existe en varios puntos: Start Command sin `gthread` (reintroduciría el bug de v12.29.78), Paso 2 de EmailJS mezclado por error con instrucciones de Resend, variables `RESEND_API_KEY`/`EMAIL_FROM`/`EMAILS_INTERNOS` declaradas en `render.yaml` pero sin ningún uso real en `app.py`, comando de inicialización de BD apuntando a una función muerta (`init_db()` en `app.py`, sin llamadas en todo el proyecto) en vez del script real `init_db.py`, Paso 4 (migración SQLite) obsoleto — el script referenciado no existe en el repo —, y Paso 6 (Supabase Storage) descrito como "preparación futura" cuando ya está implementado desde v12.8.0, con un enfoque técnico distinto al descrito (REST directo con `requests`, no el paquete `supabase`).
- **Cambio**: `GUIA_DESPLIEGUE.md` reescrita sección por sección con el proceso real, contrastado contra el código antes de documentarlo. Tabla de variables de entorno ampliada para cubrir todas las de `render.yaml`. Badge de versión en `templates/index.html` actualizado.
- **Fuera de alcance de esta entrega**: limpiar `render.yaml` (variables sin uso) y la función muerta `init_db()` de `app.py` — son cambios de configuración/código real, se dejan para una etapa aparte en vez de mezclarlos con una entrega puramente documental.
- **Entrega**: `GUIA_DESPLIEGUE.md`, `templates/index.html` (badge de versión), más este historial/`CHANGELOG.md`.

---

## 2026-08-31 — [Control Pedidos] Auditoría de rendimiento, Etapa 3/3 (última): compresión gzip de las respuestas del servidor (v12.30.72)

- **Origen**: continuación de las Etapas 1 y 2 — Víctor: "desplegada la dos continuamos con la 3".
- **Causa raíz**: ninguna respuesta salía comprimida. `templates/index.html` (628 KB) se sirve con `Cache-Control: no-cache` a propósito (para no servir una versión vieja tras desplegar), así que se descarga entero sin comprimir en cada carga/recarga. El JSON de la API tampoco viajaba comprimido.
- **Decisión — no se usó Flask-Compress**: probada primero, descartada al comprobar que (1) todas sus versiones dependen obligatoriamente del paquete `brotli` (extensión en C) — no hay modo "solo gzip, sin dependencias" con esa librería — y (2) con ella puesta, `index.html` (el objetivo principal) no llegaba a comprimirse con gzip: se sirve en streaming, y esa librería excluye gzip de los algoritmos de streaming (usa brotli/zstd/deflate ahí), así que el resultado dependía de que brotli funcionase de verdad en Render. Se implementó en su lugar un `after_request` propio, sin dependencias nuevas.
- **Cambio**: `_comprimir_respuesta_gzip()` (app.py) comprime con gzip las respuestas de texto (HTML/CSS/JS/JSON) cuando el navegador lo admite (`Accept-Encoding`), con `Vary: Accept-Encoding`; no toca binarios (PDF/Excel/imágenes) ni respuestas por debajo de 500 bytes. El ETag de `index()` se deja intacto a propósito, para no romper su atajo 304 existente (`If-None-Match`).
- **Verificación**: `python3 -m py_compile app.py` sin errores. Réplica aislada en Flask del patrón real de `index()` (ETag + 304): confirmado que gzip comprime y descomprime correctamente, que sin `Accept-Encoding` se sirve igual que antes, que binarios/respuestas pequeñas no se tocan, y que el atajo 304 sigue funcionando igual con la compresión activada (primera visita → gzip; revisita con ETag en caché → 304; tras "deploy" con ETag viejo → 200 + gzip de nuevo).
- **Entrega**: `app.py`, `templates/index.html` (badge de versión), más este historial/`CHANGELOG.md`.

---

## 2026-08-31 — [Control Pedidos] Auditoría de rendimiento, Etapa 2/3: índice de búsqueda por trigramas para Pedidos (v12.30.71)

- **Origen**: continuación de la Etapa 1 — Víctor: "desplegada y probada la etapa 1, seguimos con la 2?".
- **Causa raíz**: `GET /api/pedidos` busca con `ILIKE '%texto%'` (comodín al principio) sobre `pedido_num`/`observaciones`/`pr.nombre`/`h.codigo` a la vez — mismo problema que en Proveedores (Etapa 1): sin índice de apoyo, cada búsqueda recorre la tabla `pedidos` entera, y esa tabla es la que más rápido crece de toda la app.
- **Cambio**: `_auto_migrate()` (app.py) crea 2 índices GIN por trigramas nuevos sobre `pedidos.pedido_num` y `pedidos.observaciones` (mismo patrón protegido que la Etapa 1). `pr.nombre` ya estaba cubierto por el índice de Proveedores; `h.codigo` se deja sin indexar por ser una tabla de ~10 filas, donde no aporta nada.
- **Decisión — no se tocó `PEDIDO_SELECT`**: la fusión de las 3 subconsultas del "contacto principal" del proveedor (email/nombre/teléfono), contemplada en la auditoría original, se descarta por ahora: un proveedor puede tener varios contactos marcados "principal" a la vez (funcionalidad intencional, `pvSetPrincipal()`), y cada subconsulta actual resuelve su campo de forma independiente entre esos contactos — fusionarlas podría cambiar qué contacto "gana" en fichas con más de un principal. Como las 3 ya se apoyan en el índice existente de `proveedor_contactos(proveedor_id)`, el ahorro real era menor de lo esperado y no compensa el riesgo sin que Víctor decida antes el criterio de desempate. Queda pendiente de una decisión de producto, no es un arreglo técnico directo.
- **Verificación**: `python3 -m py_compile app.py` sin errores.
- **Entrega**: `app.py`, `templates/index.html` (badge de versión), más este historial/`CHANGELOG.md`.

---

## 2026-08-31 — [Control Pedidos] Auditoría de rendimiento, Etapa 1/3: Proveedores paginado + índice de búsqueda por trigramas (v12.30.70)

- **Origen**: Víctor: "necesito le realices un chequeo para buscar posibles problemas ya que esta comenzando a ir mas lenta, no alarmante pero si. La ficha proveedores se atasca un poco y en líneas generales el resto." Tras la auditoría, Víctor pidió implantar los arreglos por etapas ("implantamos por etapas si te parece") — esta es la Etapa 1, centrada en Proveedores por ser la molestia más directa.
- **Causa raíz (proveedores)**: `GET /api/proveedores` no estaba paginado — siempre devolvía la tabla entera de proveedores activos, a diferencia de `/api/pedidos` (paginado desde hace tiempo). `loadProveedores()` (templates/index.html) reconstruía la tabla completa en cada apertura de la vista y en cada tecla del buscador (debounce 300ms) — cuantos más proveedores se dan de alta con el tiempo, más pesada cada carga. El buscador usa `ILIKE '%texto%'` (comodín al principio) sobre nombre/código SAP/código DALI a la vez, patrón que no puede usar un índice normal (B-tree): cada búsqueda recorría la tabla entera. También se encontró un recálculo innecesario (un mapa hotel→código recalculado fila a fila en vez de una sola vez).
- **Otras causas detectadas en la misma auditoría, pendientes de etapas siguientes**: el buscador de Pedidos tiene el mismo problema de índice (ILIKE con comodín al principio, ejecutado dos veces por búsqueda) sobre una tabla que crece muy rápido; el listado de Pedidos arma cada fila con 6 subconsultas correlacionadas; `templates/index.html` (628 KB) se sirve sin compresión y con `Cache-Control: no-cache`.
- **Cambio**: `_auto_migrate()` (app.py) activa la extensión `pg_trgm` de PostgreSQL y crea 3 índices GIN por trigramas sobre `proveedores.nombre`/`codigo`/`codigo_dali` (cada sentencia con su propio try/except, en la parte protegida de arriba de la función). `GET /api/proveedores` pasa a aceptar `page`/`page_size` (page_size 30, máx. 100) y devuelve `{proveedores,total,page,page_size,pages}` en vez de un array plano. `loadProveedores()` (templates/index.html) pagina con el mismo patrón visual que Pedidos (`renderProvPagination()`/`goProvPage()`, nuevo estado `G.provPage`), vuelve a la página 1 en cada búsqueda nueva, y calcula el mapa hotel→código una sola vez por carga. `buscarProveedor()` (autocompletado del modal de Pedido, mismo endpoint) actualizado a la nueva forma de la respuesta.
- **Verificación**: `python3 -m py_compile app.py models.py` sin errores; `node --check` sobre el JavaScript de `templates/index.html` sin errores. Revisados los dos únicos puntos del frontend que consumen `GET /api/proveedores` para confirmar que ambos quedan adaptados a la nueva forma de la respuesta.
- **Entrega**: `app.py`, `templates/index.html` (badge de versión), más este historial/`CHANGELOG.md`.

---

## 2026-08-31 — [Control Pedidos] Departamento deshabilitado hasta elegir Hotel — evita saltarse el filtro por hotel (v12.30.69)

- **Origen**: Víctor: "EXITE UN ERROR DE ORDEN AL CREAR UN PDIDO NUEVO, NO DEBERIA DEJAR ELEGIR PROMERO EL DEPARTAMENTO PARA QUE EL FILTRO SEA CORRECTO".
- **Causa raíz**: el filtro de Departamento por hotel (v12.30.65) solo actuaba al recalcular las opciones del desplegable, pero nada impedía elegir Departamento antes que Hotel — sin hotel elegido `_departamentosExcluidosParaHotel('')` no excluye nada, así que se veía y se podía seleccionar el catálogo completo sin filtrar.
- **Cambio**: `poblarSelectDeptos()` (templates/index.html) deshabilita el select de Departamento (`disabled`) mientras no haya Hotel elegido, con el texto "— Elige primero un hotel —"; se habilita solo al elegir hotel, ya con las opciones filtradas. Al reutilizar la misma función en los tres puntos ya existentes (cambio de hotel, pedido nuevo, editar pedido) el comportamiento queda correcto en los tres sin duplicar lógica. De paso se corrige `_crearPedidoDesdeComparacion()`, que llamaba a una función inexistente (`openNuevoPedidoModal`) rompiendo el prellenado de pedido desde la comparación de PDF, y se añade ahí el refiltrado explícito de Departamento tras prellenar el hotel.
- **Verificación**: Playwright, lógica de `poblarSelectDeptos()` probada de forma aislada — sin hotel: deshabilitado + aviso; con GY: habilitado y excluye "RESTAURANTE & BARES"; con hotel sin separar: excluye "RESTAURANTE"/"BARES"; al quitar el hotel: vuelve a deshabilitarse y vaciarse; flujo de edición (hotel fijado antes de repoblar): queda habilitado con el departamento guardado.
- **Entrega**: `templates/index.html` (badge de versión incluido), más este historial/`CHANGELOG.md`.

---

## 2026-08-31 — [Control Pedidos] Código DALI obligatorio en Proveedores + aviso real de duplicado (con nombre del proveedor) — antes fallaba en silencio (v12.30.68)

- **Origen**: Víctor: "en el apartado proveedores, tanto el codigo SAP como el DALI son obligatorios al crear un proveedor, en caso de duplicidad de alguno de los dos codigos ahora esta realizando error silencioso, debera indicar que codigo esta duplicado nombre asociado etc para poder localizarlo y arreglarlo".
- **Causa raíz**: `saveProveedor()` (templates/index.html) no tenía el `try/catch` que sí tiene el resto de formularios (p. ej. `savePedido`) — `api()` lanza excepción en un 409, y esa excepción quedaba sin capturar: ningún aviso visible. Código DALI, además, no tenía ningún chequeo de duplicado en absoluto.
- **Cambio**: código DALI pasa a obligatorio (crear y editar, admin); nuevo chequeo de duplicado para código DALI (antes solo existía para código SAP y nombre); mensajes de error de ambos códigos ahora indican nombre e ID del proveedor en conflicto (`_buscar_proveedor_duplicado()`, app.py); `saveProveedor()` envuelto en try/catch con `showFormAlert` y reactivación del botón, igual que `savePedido`.
- **Verificación**: `python3 -m py_compile app.py` sin errores; Playwright con mock de un 409 de código DALI duplicado confirmó que el mensaje con el proveedor en conflicto se muestra y el botón se reactiva; confirmado también el aviso al dejar el código DALI vacío.
- **Entrega**: `app.py`, `templates/index.html` (badge de versión), más este historial/`CHANGELOG.md`.

---

## 2026-08-31 — [Control Pedidos] El correo interno de cambio de estado pasa de Bcc a CC visible + lista de destinatarios en el cuerpo (v12.30.67)

- **Origen**: Víctor confirmó primero que solo se envía un correo con todos los destinatarios juntos ("SOLO SE ENVIA UN CORREO Y VAN TODOS LOS DESTINATARIOS JUNTOS EN EL MISMO ¿VERDAD?") y a continuación pidió: "ESTE CORREO INTERNO, ME GUSTARIA QUE NO FUERA EN OCULTO, ES INTERESANTE QUE TODOS LOS INVOLUCRADOS SEPAN QUIENES ESTAN INFORMADOS".
- **Cambio**: el correo interno de cambio de estado (`cambio_estado_interno`) pasa de `bcc` a `cc` al enviarse por EmailJS (`_enviarEmailsSistemaPendientes`, templates/index.html) — el resto de correos de la misma cola (reclamación al proveedor, resúmenes, solicitudes de acceso) siguen en Bcc, sin cambios. Como red de seguridad — la copia visible depende de que la plantilla de EmailJS tenga un campo "Cc" enlazado (hay que añadirlo a mano en las 3 cuentas, instrucciones dejadas en Admin → EmailJS) — el propio cuerpo del correo (HTML y texto) añade ahora "Aviso enviado también a: ..." con la lista completa de destinatarios.
- **Verificación**: `python3 -m py_compile app.py` sin errores; HTML renderizado y revisado con el nuevo bloque de destinatarios; Playwright confirmó que el frontend carga sin errores de JS.
- **Pendiente de Víctor**: configurar el campo "Cc" en las 3 plantillas de EmailJS para que la copia sea realmente visible en la cabecera del correo (instrucciones en el propio panel Admin → EmailJS).
- **Entrega**: `app.py`, `templates/index.html` (badge de versión), más este historial/`CHANGELOG.md`.

---

## 2026-08-31 — [Control Pedidos] "Comunicado A&B" / "Comunicado Jefe Dep." se marcan solas al confirmarse el envío real del correo (v12.30.66)

- **Origen**: Víctor: "PODEMOS HACER QUE CUANDO EL CORREO INTERNO DE 'PEDIDO ENVIADO AL PROVEEDOR' VA CON COPIA AL DEPARTAMENTO A&B SE MARQUE AUTOMATICAMENTE LA CASILLA Y EN TODOS LOS CASOS QUE SE PONGA EN COPIA AL RESPONSABLE DEL DEPARTAMENTE TAMBIEN SE MARQUE LA CORRESPONDIENTE, ESTAS DOS CELDAS NO PODRAN SER MODIFICADAS POR EL USIARIO, SOLO CON EL ENVIO DEL CORREO. EN CASO DE NO TENER CORREO CONFIGURADO UN DEPARTAMENTO ENTONCES NO SE MARCARA LA DE 'COMUNICADO AL JEFE DEL DEPTO'".
- **Cambio**: "Comunicado A&B" y "Comunicado Jefe Dep." (modal de pedido, sección Comunicaciones y partes) pasan a `disabled` y dejan de enviarse en el guardado manual del pedido — solo se marcan desde el backend, en `POST /api/emails-sistema-pendientes/<id>/marcar-enviado`, cuando se confirma el envío real del correo interno ENVIADO AL PROVEEDOR: A&B si el departamento es COCINA/BARES/RESTAURANTE/RESTAURANTE & BARES, Jefe Dep. si el correo del departamento (`departamento_hotel_email`) estaba configurado y en copia (si no hay correo configurado, no se marca). Nuevas columnas `marca_comunicado_ab`/`marca_comunicado_jefe_dep` en `emails_sistema_pendientes`, calculadas al encolar y aplicadas (con OR, nunca se desmarcan solas) solo al confirmarse el envío. Se corrigió además que `_setFormCanceladoSilent` volvía a habilitar estas dos casillas al desmarcar CANCELADO.
- **Verificación**: `python3 -m py_compile app.py` sin errores; Playwright confirmó que ambas casillas están `disabled`, que conservan su valor al abrir un pedido para editar, y que no se reactivan al alternar el bloqueo por CANCELADO.
- **Entrega**: `app.py`, `templates/index.html` (badge de versión), más este historial/`CHANGELOG.md`.

---

## 2026-08-31 — [Control Pedidos] El desplegable de Departamento del pedido se filtra según el hotel (v12.30.65)

- **Origen**: Víctor: "en el apartado pedidos, cuando se indica departamento me gustaría que esto quedara filtrado, Hoteles GY - IT - MT - y TA ven todos los departamentos menos 'RESTAURANTE & BARES' el resto de hoteles ven todos menos 'RESTAURANTE' Y 'BARES' (...) ¿ES POSIBLE?"
- **Cambio** (solo `templates/index.html`, catálogo de departamentos sin tocar): el desplegable de Departamento del modal de pedido se filtra según el hotel elegido — GY/IT/MT/TA (RESTAURANTE y BARES separados) no ven "RESTAURANTE & BARES"; el resto (departamento combinado) no ven "RESTAURANTE" ni "BARES". Se refiltra al cambiar de hotel y al abrir el modal (nuevo o editar). Un departamento ya guardado que el filtro excluiría para su hotel se conserva en el desplegable marcado "(no habitual en este hotel)", nunca se oculta. El filtro de búsqueda de Pedidos (listado) no se toca.
- **Verificación**: probado con Playwright inyectando catálogo de ejemplo — GY excluye "RESTAURANTE & BARES", GC excluye "RESTAURANTE"/"BARES", y un departamento no habitual para el hotel elegido se conserva marcado en vez de desaparecer.
- **Entrega**: `templates/index.html` (badge de versión incluido), más este historial/`CHANGELOG.md`.

---

## 2026-08-31 — [Control Pedidos] Fila "Observaciones" en el correo interno, texto sin "Por la presente", A&B simplificado y más márgenes (v12.30.64)

- **Origen**: Víctor: "podemos incluir en el cuadro el apartado observaciones que ya tenemos en pedidos? esto siempre puede dar mas información relevante. Quizás la coletilla 'Por la presente ...' no es muy ... Otra cosa, al departamento de A&B simplemente se le informa para su control interno, no dar mas explicaciones. Me gusta el del techo de gasto. Yo en todos los casos intentaria ordenar mejor las lineas, los margenes."
- **Cambio** (cuadro/márgenes: en todos los estados del correo interno; redacción: solo ENVIADO AL PROVEEDOR): nueva fila Observaciones en el cuadro (omitida en CANCELADO/DENEGADO, ya mostrado aparte como motivo); "Confirmamos que..." sustituye a "Por la presente se confirma..."; aviso a A&B reducido a "Se informa también al departamento de A&B para su control interno."; se mantiene la frase de exceso de techo de v12.30.63; más margen entre bloques y más padding en el cuadro en los 5 estados del correo.
- **Verificación**: `python3 -m py_compile app.py` sin errores; HTML renderizado para caso completo (A&B + exceso + observaciones) y caso simple, capturas revisadas.
- **Entrega**: `app.py`, `templates/index.html` (badge de versión), más este historial/`CHANGELOG.md`.

---

## 2026-08-31 — [Control Pedidos] El aviso de exceso de techo de gastos se menciona también en el párrafo introductorio (v12.30.63)

- **Origen**: Víctor: "Mantén el cuadro de datos exactamente igual. Redacta un aviso interno profesional, conciso y corporativo. El texto debe confirmar la tramitación del pedido, informar al responsable del departamento y, en pedidos de Cocina/Bares/Restaurantes, notificar también a A&B. Si el pedido supera el techo de gastos establecido, indícalo explícitamente en el texto para que no pase desapercibido. Evita redundancias y limita el mensaje a 4–5 líneas."
- **Cambio, solo para ENVIADO AL PROVEEDOR** (HTML y texto plano): párrafo introductorio reestructurado en frases cortas independientes (tramitación + proveedor, departamento informado, A&B si aplica, cierre de novedades); nueva frase de aviso explícito cuando el pedido superó el techo de gastos y fue autorizado por Dirección General, sin repetir el detalle que ya da el recuadro amarillo existente justo debajo. Cuadro de datos sin cambios.
- **Verificación**: `python3 -m py_compile app.py` sin errores; HTML renderizado para las 4 combinaciones (A&B sí/no × exceso sí/no) — capturas revisadas, 3 a 6 líneas según el caso, sin redundancia con el recuadro de detalle.
- **Entrega**: `app.py`, `templates/index.html` (badge de versión), más este historial/`CHANGELOG.md`.

---

## 2026-08-31 — [Control Pedidos] Texto del correo interno "ENVIADO AL PROVEEDOR" más conciso y corporativo, nombrando al proveedor (v12.30.62)

- **Origen**: Víctor: "Redacta un aviso interno corporativo, conciso y estructurado. El mensaje debe confirmar la tramitación del pedido, indicar el proveedor y especificar que A&B queda informado cuando el pedido pertenece a Cocina, Bares o Restaurantes. Evita frases redundantes y limita el texto a 4–5 líneas. El cuadro esta perfecto, si el pedido enviado supera el techo de gasto, tambien se incluye esta información y se pone en copia a quien corresponda segun el apartado Notificaciones Adicionales, ahi esta incluido Dpto. A&B Chef Director Compras etc" — feedback sobre el párrafo entregado en v12.30.61.
- **Cambio, solo para ENVIADO AL PROVEEDOR** (HTML y texto plano): párrafo introductorio reescrito, más corto, nombrando al proveedor explícitamente ("...al proveedor **{proveedor}**, quedando el departamento de **{departamento}** informado de la gestión..."); se mantiene la frase de A&B para COCINA/BARES/RESTAURANTE/RESTAURANTE & BARES. Redacción ajustada para no cerrar la frase justo tras el nombre del proveedor (evita doble punto cuando el proveedor termina en "S.L."/"S.A."). Sin cambios en la tabla ni en el mecanismo de exceso de techo de gasto (ya correcto desde el 2026-08-28, solo verificado).
- **Verificación**: `python3 -m py_compile app.py` sin errores; HTML final renderizado con proveedores con forma jurídica al final del nombre (sin doble punto) y capturas revisadas para COCINA (con A&B) y RECEPCIÓN (sin ella).
- **Entrega**: `app.py`, `templates/index.html` (badge de versión), más este historial/`CHANGELOG.md`.

---

## 2026-08-31 — [Control Pedidos] El correo interno de "ENVIADO AL PROVEEDOR" pasa de aviso de cambio de estado a notificación de tramitación al departamento (+ A&B) (v12.30.61)

- **Origen**: Víctor: "ahora se utilizara para que todos sepan que el pedido ya ha sido enviado al proveedor y cuando, entonces ya no es necesario poner en este caso Estado Anterior y Estado Nuevo (...) por la presente se informa al responsable del Dpto. X que su pedido ha sido tramitado correctamente al proveedor y entramos en el proceso de espera para la entrega (...) en los casos de que el departamento sea COCINA, BARES, RESTAURANTE Y/O RESTAURANTE & BARES, también se comunica al departamento de A&B para su control (...) dar las instrucciones pertinentes para descargar el PDF".
- **Cambio, solo para ENVIADO AL PROVEEDOR** (el resto de estados de este correo no cambian): se retiran las filas Estado anterior/Estado nuevo; nuevo párrafo introductorio dirigido al departamento del pedido, con línea adicional para A&B cuando el departamento es COCINA/BARES/RESTAURANTE/RESTAURANTE & BARES (nombres exactos de `models.py`); frase explicativa añadida antes del botón de descarga del PDF.
- **Verificación**: `python3 -m py_compile app.py` sin errores; HTML final renderizado y revisado con datos de ejemplo (COCINA con línea de A&B, ECONOMATO sin ella, tabla sin filas de estado).
- **Entrega**: `app.py`, `templates/index.html` (badge de versión), más este historial/`CHANGELOG.md`.

---

## 2026-08-31 — [Control Pedidos] Botón "Reactivar" para correos de sistema descartados + purga automática a los 2 días (v12.30.60)

- **Origen**: Víctor, sobre "Cola de correos de sistema pendientes" (admin → EmailJS y Cola de Correo): "esto, una vez descartado no tiene sentido seguir llenado la pantalla, podemos poner otro botón para reactivar y que a los 2 días cauque y se elimine el envío descartado".
- **Antes**: una fila descartada a mano se quedaba en la tabla para siempre como constancia, acumulándose sin valor real y sin forma de deshacer el descarte salvo tocando la BD a mano.
- **Cambio**: botón "↻ Reactivar" en las filas ya descartadas (`POST /api/admin/emails-sistema-pendientes/<id>/reactivar`) — limpia `descartado_en` y resetea `intentos` si ya había agotado el cupo, para que vuelva a intentarse de verdad. Cada fila descartada muestra cuánto le queda antes de autoeliminarse. Nuevo job diario (04:00, `_job_purgar_emails_sistema_descartados`) que borra las descartadas hace más de 2 días.
- **Verificación**: `python3 -m py_compile app.py` sin errores; renderizado probado con datos simulados (descartada hace 1 día, hace 3 días ya vencida, y una fila sin descartar de control).
- **Entrega**: `app.py`, `templates/index.html` (badge de versión), más este historial/`CHANGELOG.md`.

---

## 2026-08-31 — [Control Pedidos] Cabecera fija también en Pedidos, Alertas, Familias de Artículos y Usuarios (v12.30.59)

- **Origen**: Víctor, con capturas de las 4 pantallas: "todas estas pantallas también bloquear esto en lo alto de la ventana para scrol de las 4 opciones adjuntas" — mismo comportamiento de v12.30.58 (Proveedores), extendido a estas 4 vistas.
- **Cambio**: en Pedidos se pegan debajo de la barra superior el buscador+filtros y la fila "Busca por:"; en Alertas, el título de la tarjeta + Imprimir y su fila de filtros; en Familias de Artículos y Usuarios (sin buscador propio), solo el título de la tarjeta. En los 4 casos, además, la cabecera de columnas de la tabla. Mismo mecanismo que Proveedores: offsets calculados en JS con un helper genérico compartido (`_ajustarStickyApilado()`), y `overflow-x:auto` de `.table-wrap` anulado solo en estas 4 tablas (mismo motivo ya documentado en la entrada de Proveedores).
- **Verificación**: carga en Chromium headless sin errores de JS; las 4 vistas probadas con datos de prueba y scroll simulado por Playwright, con capturas confirmando el resultado antes de entregar.
- **Entrega**: `templates/index.html` (único archivo con cambios), más este historial/`CHANGELOG.md`.

---

## 2026-08-31 — [Control Pedidos] Buscador de proveedores por código SAP/DALI además de nombre + cabecera de tabla fija al hacer scroll (v12.30.58)

- **Origen**: Víctor, sobre Proveedores (ya con 2151 registros): "debe dejar buscar por nombre, codigo sap y codigo dali, cuando se realiza scrol se debe quedar fijo la parte superior siempre visible".
- **Cambio 1**: `GET /api/proveedores?q=...` ahora compara `q` contra `nombre`, `codigo` y `codigo_dali` (OR, todos `ILIKE`) — antes solo miraba `nombre`.
- **Cambio 2**: el buscador y la fila de cabecera de la tabla se quedan pegados debajo de la barra superior durante el scroll (offset calculado en JS a partir de la altura real de ambos, no hardcodeado). Hubo que anular `overflow-x:auto` de `.table-wrap` solo para esta tabla (`#prov-table-wrap{overflow:visible}`) porque ese overflow convierte también `overflow-y` en `auto` de forma implícita, lo que impedía que la cabecera se pegara contra la ventana — comprobado con un test aislado en Playwright antes de aplicarlo.
- **Verificación**: `python3 -m py_compile app.py` sin errores; carga en Chromium headless sin errores de JS; reproducción aislada de la estructura real confirma visualmente el scroll fijo.
- **Entrega**: `app.py`, `templates/index.html` (badge de versión), más este historial/`CHANGELOG.md`.

---

## 2026-08-31 — [Control Pedidos] Corregido: la migración de "Código DALI" vivía al final de `_auto_migrate()` y nunca se ejecutaba — 500 en /api/proveedores (v12.30.57)

- **Origen**: Víctor, tras desplegar v12.30.56 — capturas de "Proveedores" con "Error al cargar" y el toast `Error cargando proveedores: [500] ... column "codigo_dali" does not exist`.
- **Causa**: antipatrón ya sufrido dos veces antes en este mismo archivo (`sujeto_seguimiento`, `total_pedido`) y documentado explícitamente en el código: `_auto_migrate()` encadena ~111 sentencias bajo un único try/except general; la migración de `codigo_dali` se puso (por error) al final de la función, así que cualquier fallo en cualquiera de las sentencias anteriores la dejaba sin ejecutar, sin aviso salvo un 500 en producción.
- **Cambio**: movida al bloque protegido del principio de `_auto_migrate()`, con su propio try/except, junto a `sujeto_seguimiento` y `total_pedido`. Mismo `ALTER TABLE proveedores ADD COLUMN IF NOT EXISTS codigo_dali TEXT`, sin cambios de esquema.
- **Verificación**: `python3 -m py_compile app.py` sin errores.
- **Entrega**: `app.py`, `templates/index.html` (badge de versión), más este historial/`CHANGELOG.md`.

---

## 2026-08-31 — [Control Pedidos] Campo "Código DALI" en proveedores + solo admin crea/modifica nombre y códigos + corregido el guardado de contactos para compras (v12.30.56)

- **Origen**: Víctor, sobre la ficha de proveedores: "en la ficha de proveedores, necesito junto a la casilla CODGIGO SAP, OTRA PARA CODIGO DALI ; Actualmente estamos trabajando con los dos sistemas y vamos asociando tanto artículos como proveedores. Ambas celdas de edicion manual por los roles con permiso de edición y creacion de proveedores, creo que solo es admin la creacion y modificacion del nombre y codigo, los compradores pueden editar contactos ( esto ultimo verificalo porque creo que les da error o no hace nada cuando intentan guardar los cambios="
- **Comprobado (bug confirmado)**: compras no podía guardar ningún cambio en un proveedor, ni siquiera solo contactos. El modal oculta nombre/código para compras, así que `saveProveedor()` nunca enviaba `codigo`; `update_proveedor()` lo exigía siempre antes de procesar los contactos ("El código SAP es obligatorio"), rompiendo cualquier guardado de compras.
- **Aclarado con Víctor**: la creación de proveedores (`POST /api/proveedores`) llevaba desde el 10-ago-2026 abierta también a compras (decisión explícita de aquella entrega). Confirmó que ahora quiere que quede solo para admin, igual que la modificación de nombre/código — compras se queda con la edición de contactos/observaciones de los proveedores ya existentes.
- **Cambio**: columna nueva `codigo_dali TEXT` en `proveedores` (migración automática); input "Código DALI" junto a "Código SAP" en el modal (creación y edición-admin; en modo compras se muestran ambos en solo-lectura). `POST /api/proveedores` ahora exige admin (antes admin+compras); botón "+ Nuevo proveedor" oculto para compras. `PUT /api/proveedores/<id>`: nombre/código SAP/código DALI solo se toman del payload si el rol es admin — si no, se conservan de BD (mismo patrón que `sujeto_seguimiento`), lo que de paso corrige el bug de guardado para compras.
- **Verificación**: `python3 -m py_compile app.py` sin errores.
- **Entrega**: `app.py`, `templates/index.html` (badge de versión + modal + tabla), más este historial/`CHANGELOG.md`.

---

## 2026-08-31 — [Control Pedidos] El correo interno de "ENVIADO AL PROVEEDOR" también lleva ahora el botón de descarga del PDF del pedido (v12.30.55)

- **Origen**: Víctor, tras revisar el correo interno real de un pedido enviado al proveedor (sin ningún botón visible): "¿no habíamos modificado tanto el correo interno de comunicación estado ENVIADO AL PROVEEDOR como el que se envía al mismo proveedor para este asunto, para que adjúntense un botón y poder descargar el PDF del pedido en destino?"
- **Comprobado**: no — el botón de descarga (`_enlaces_descarga_pedido_doc()` + `/descargas/adjunto/<token>`, enlace público y temporal en vez de adjuntar el PDF) solo se había añadido al correo AL PROVEEDOR (v12.30.40, 28 agosto 2026). El correo interno de ese mismo cambio de estado (`enviar_emails_estado()`, bloque `ESTADOS_EMAIL_INTERNO`) nunca lo tuvo — no era un fallo, no estaba en el alcance de la petición original.
- **Cambio**: mismo bloque de botón (mismo estilo visual, mismo enlace público sin login) añadido también al correo interno, en HTML y en texto plano, pero solo cuando `estado_nuevo == "ENVIADO AL PROVEEDOR"` — igual que el correo al proveedor; el resto de estados que usan este mismo bloque interno (ENTREGA PARCIAL, ENTREGADO, CANCELADO) no llevan el botón, al no haber un PDF nuevo que enseñar en esos casos.
- **Verificación**: `python3 -m py_compile app.py` sin errores.
- **Entrega**: solo `app.py` y `templates/index.html` (badge de versión), más este historial/`CHANGELOG.md`.

---

## 2026-08-31 — [Control Pedidos ↔ DALI] Norma documentada: el cruce por email para la firma de DALI solo mira el email principal, nunca email2 (sin cambio funcional) (v12.30.54)

- **Origen**: al probar la firma del correo de DALI (endpoint de v12.30.53), apareció una colisión real de datos: dos usuarios de esta app comparten el mismo email principal — `comprascan` (Víctor, cuenta real, con móvil) y `usuario prueba` (cuenta de pruebas, sin móvil) — que hacía que DALI cogiera la cuenta equivocada. Resuelto del lado de DALI (prefiere, entre varias coincidencias, la que tiene móvil — ver `HISTORIAL.md` de `dali-sap-articulos-app`, v0.90/v1.19.8).
- **Aviso de Víctor al validar ese arreglo**: "tener en cuenta que este mismo correo tambien es correo secundario en otro usuario, asi que podemos poner como norma que solo mire en el primer correo de cada usuario".
- **Comprobado**: `GET /api/externo/dali-sap/compradores` ya seleccionaba solo `email` (columna principal), nunca `email2`, desde que se creó — sin cambio de código necesario. Se documenta explícitamente en el docstring del endpoint como decisión deliberada, para que no se "mejore" sin querer añadiendo `email2` al cruce en el futuro (reintroduciría el mismo tipo de colisión).
- **Verificación**: `python3 -m py_compile app.py models.py` sin errores.
- **Entrega**: solo `app.py` (comentario), `templates/index.html` (badge de versión) y este historial/`CHANGELOG.md`.

---

## 2026-08-29 — [Control Pedidos ↔ DALI] Nuevo endpoint del puente: nombre/email/móvil de compradores y admins, para la firma de los correos de "Documentación faltante" de DALI (v12.30.53)

- **Origen del cambio**: petición sobre DALI, no sobre esta app — Víctor pidió mejorar el correo de "Documentación faltante" de `dali-sap-articulos-app` (más profesional, petición elegante de imagen por referencia, y una firma "al estilo del resto de correos que se envían a los proveedores desde control pedidos" con nombre, teléfono y correo del admin que gestiona el envío). Al investigar, la tabla `usuarios` de DALI nunca ha tenido columna de teléfono, ni la sesión de esa app lo guarda en ningún sitio.
- **Decisión de Víctor**: en vez de añadir un campo de teléfono nuevo en DALI (o fijar uno solo para todos), reutilizar el que YA existe aquí — "¿puedes coger la info de la ficha usuarios control pedidos? los admin son los mismos y los compradores son admin en catalogo dali". Es decir, DALI cruza por email contra los usuarios de esta app.
- **Cambio en `app.py`**: nuevo `GET /api/externo/dali-sap/compradores`, mismo esquema de autenticación que el ya existente `GET /api/externo/dali-sap/proveedores` (firma HMAC-SHA256 con `DALI_SSO_SECRET` en `X-Dali-Timestamp`/`X-Dali-Signature`, sin sesión de usuario — llamada servidor a servidor). Devuelve `{nombre, email, movil}` de los usuarios activos con rol `compras` o `admin` (los dos roles que, en la práctica, son las cuentas de administrador de DALI). No expone contraseña ni ningún otro dato de la tabla `usuarios`.
- **Sin cambios de esquema ni de datos** en esta app — la columna `movil` de `usuarios` ya existía (`models.py`); este cambio solo la expone, de solo lectura, a través del puente ya existente con DALI.
- **Lado DALI** (repo `dali-sap-articulos-app`, ver su propio `HISTORIAL.md` v0.86 / `CHANGELOG.md` v1.19.4): `controlPedidosEmailBridge.js` (nuevas `obtenerCompradoresDeControlPedidos()`/`resolverMovilCompradorEnControlPedidos()`), `documentacionController.js` (`resolverFirmaAdmin()`, expuesta en `GET /admin/documentacion-faltante` como `firma_admin`), y `EmailProveedorModal.jsx` (firma añadida al final del correo generado). Si el puente falla o no hay coincidencia por email, la firma se genera igual, sin la línea de teléfono.
- **Versión**: badge de `templates/index.html` y `CHANGELOG.md` → **V 12.30.53**.
- **Verificación**: `python3 -m py_compile app.py models.py` sin errores.
- **Entrega**: solo se modifica `app.py` (nuevo endpoint), `templates/index.html` (badge de versión) y este historial/`CHANGELOG.md` — sin cambios de esquema, sin necesidad de migración.

---

## 2026-08-29 — [Control Pedidos] Techo (€) y EmailJS salen de "Parámetros de alertas" a sus propias pantallas (v12.30.52)

- Víctor: "puedes continuar" — segunda parte de la reorganización de admin (v12.30.51), sacando de "Parámetros de alertas" dos cosas sin relación con umbrales de alerta: los límites € del techo de gastos y la configuración de EmailJS.
- **Cambio en `templates/index.html`**: el grupo `techo` (6 claves €/%/conteo) se mueve a un bloque nuevo "⚙️ Límites de Techo de Gastos" dentro de la propia vista "Techo de gastos", visible solo para admin (esa vista la comparte con compras). El grupo `emailjs` (3 cuentas rotativas, cupo, cola de correos atascados) se mueve a una vista nueva "📤 EmailJS y Cola de Correo", bajo "Sistema · Admin". Mismo endpoint de siempre (`GET`/`PUT /api/admin/config-alertas`, ya agnóstico de grupo) — sin cambios en `app.py`.
- De paso, `saveConfigAlertas()` pasa de buscar inputs en todo el documento a buscar solo dentro de su propia vista, para no arrastrar cambios sin guardar de las pantallas nuevas (las vistas ocultas no se quitan del DOM, solo se tapan).
- **Verificación**: `python3 -m py_compile app.py models.py` y `node --check` sin errores. Comprobación de que los 15 `data-view` siguen únicos y sin ids duplicados tras mover los dos bloques.

## 2026-08-29 — [Control Pedidos] Reorganización del menú lateral: las pantallas admin-only se agrupan por dominio (v12.30.51)

- Víctor: "¿puedes revisar en control pedidos todos los apartados exclusivos de admin? Ahora mismo creo que están todos regados sin organización, ¿puedes reubicar mejor todo?"
- Investigación previa: las 8 pantallas admin-only (Familias, Departamentos, Notificaciones adicionales, Usuarios, Integridad, Config alertas, Config. Avisos, Restaurar backup) vivían todas dentro de una única sección "Gestión", mezcladas sin separación con 3 pantallas de uso diario compartidas con compras/hotel — solo el orden de cuándo se fueron añadiendo, sin ninguna agrupación funcional. El control de acceso real vive en el backend (`admin_required` u comprobación equivalente por ruta); reordenar el menú no toca permisos.
- **Cambio en `templates/index.html` (sidebar)**: "Gestión" se queda solo con lo compartido (Proveedores, Pedidos eliminados, Techo de gastos). Las 8 pantallas admin-only pasan a 4 secciones nuevas con "· Admin" en el título: **Datos maestros** (Familias), **Alertas y notificaciones** (Departamentos, Notificaciones adicionales, Parámetros de alertas, Avisos por usuario), **Usuarios y accesos** (Usuarios), **Sistema** (Integridad, Restaurar backup). Ninguna ruta, permiso ni contenido cambió — solo el menú.
- **Renombradas** "Config alertas" → **Parámetros de alertas** y "Config. Avisos" → **Avisos por usuario** (nombres antiguos casi sinónimos en español, fáciles de confundir) — actualizado también en el título de cada vista, el aviso de "sin permiso", el título de pestaña, y dos mensajes que las citaban por nombre (aviso de Integridad sobre EmailJS, Telegram de umbral de envíos).
- **Verificación**: `python3 -m py_compile app.py models.py` y `node --check` sin errores. Comprobación programática de que los 14 `data-view` siguen únicos y con su vista correspondiente.

## 2026-08-28 — [Control Pedidos] Correo interno "ENVIADO AL PROVEEDOR": explica la superación del techo de gastos y la autorización de Dirección General cuando aplica (v12.30.50)

- Víctor: quiere que, cuando el pedido enviado había pasado por autorización de Dirección General (exceso de techo), el propio correo interno de cambio de estado lo explique — totales, familia, motivo de la superación, quién y cuándo lo autorizó — y llegue igual a todos los destinatarios ya definidos.
- **Cambio en `app.py` (`enviar_emails_estado`)**: reutiliza la detección de v12.30.49 (`ENVIADO AL PROVEEDOR` desde `PENDIENTE Vº Bº DIRECCIÓN GENERAL`) para consultar el expediente de exceso aprobado y construir un aviso destacado con familia, motivo, disponible/importe/exceso en el momento de la solicitud, y quién/cuándo lo autorizó — insertado al principio del mismo correo interno de siempre, sin cambiar la lista de destinatarios.
- **Verificación**: `python3 -m py_compile app.py models.py` sin errores. Prueba aislada de la construcción del bloque (4 casos) — todos correctos.

## 2026-08-28 — [Control Pedidos] "Notificaciones adicionales": nueva columna para poner en copia solo en envíos que superaron el techo de gastos y pasaron por autorización DG (v12.30.49)

- Víctor: quiere que sea opcional (como las otras columnas) poner un contacto en copia específicamente cuando el pedido enviado había superado el techo de gastos y tuvo que pasar por autorización de Dirección General.
- **Cambio en `app.py`**: nuevo pseudo-estado `ESTADO_NOTIF_EXCESO_TECHO_DG` (no es un estado real de pedido), sexta columna independiente de las 5 de `ESTADOS_EMAIL_INTERNO` — compatible con "ENVIADO AL PROVEEDOR" (las dos reglas se pueden marcar a la vez, sin excluirse).
- **Cambio en `app.py` (`enviar_emails_estado`)**: se detecta el envío tras exceso autorizado comprobando `estado_nuevo="ENVIADO AL PROVEEDOR"` + `estado_antes="PENDIENTE Vº Bº DIRECCIÓN GENERAL"` — la única transición que produce `aprobar_expediente()`.
- **Cambio en `templates/index.html`**: sexta columna en la matriz, con fondo amarillo y tooltip explicativo para distinguirla de las columnas de estado real.
- **Verificación**: `python3 -m py_compile app.py models.py` y `node --check` sin errores. Prueba aislada de la lógica de selección de reglas (7 casos) y de la validación de estados aceptados (6 casos) — todos correctos.

## 2026-08-28 — [Control Pedidos] Auditoría completa: "Necesita atención" del Dashboard (y 2 sitios más) mostraban el Nº interno en vez del Nº Pedido DALI/SAP (v12.30.48)

- Víctor, con capturas del Dashboard ("Pedido 702 lleva 46 días..."): sigue viendo el Nº lineal interno en avisos/comunicaciones en vez del Nº Pedido DALI/SAP — pide revisar TODOS los apartados (Pedidos, Alertas, Dashboard, Techo de Gastos, etc.) para zanjarlo.
- Barrido completo de las 57 apariciones de `norden` en `app.py` y 18 en `templates/index.html`: 3 sitios con el problema real, el resto ya correcto (columnas de tabla con ambos números claramente etiquetados por separado, o ya usaban `pedido_num` con `norden` solo como reserva).
- **Cambio en `app.py` (`necesita_atencion`)**: el diccionario que alimenta el aviso del Dashboard omitía `pedido_num` pese a tenerlo disponible en la consulta de origen — se añade.
- **Cambio en `templates/index.html`**: widget "Necesita atención" y "Resumen de la semana" del Dashboard pasan a mostrar `pedido_num` con `norden` como reserva (mismo patrón ya usado desde v12.30.41 en la Línea temporal). El modal de confirmación al eliminar un pedido, que nunca consultaba `pedido_num`, también se corrige.
- **Verificación**: `python3 -m py_compile app.py models.py` y `node --check` sin errores. Revisión manual uno por uno de los 75 puntos localizados.

## 2026-08-28 — [Control Pedidos] Nuevo apartado "Notificaciones adicionales" (solo admin): contactos sueltos en copia según departamento del pedido + estado nuevo (v12.30.47)

- Víctor: quiere registrar contactos que no son usuarios de la app (Administrativo A&B, Director de Compras, Chef Ejecutivo) y decidir, por departamento del pedido + estado nuevo, a cuáles poner en copia en el correo interno de cambio de estado — ejemplo: Cocina + ENVIADO AL PROVEEDOR → copia al Chef Ejecutivo.
- Confirmado con Víctor: contactos y reglas globales para toda la cadena (no varían por hotel, a diferencia del correo de Departamentos).
- **Cambio en `app.py`/`models.py`**: dos tablas nuevas, `notificacion_contactos` y `notificacion_contacto_reglas` (contacto_id + departamento_id + estado, único). Solo tiene sentido un estado de `ESTADOS_EMAIL_INTERNO` — el resto se descarta al guardar.
- **Cambio en `app.py` (`enviar_emails_estado`)**: añade los contactos con regla aplicable al mismo correo interno de cambio de estado, en copia, sin duplicar destinatarios.
- **Cambio en `app.py`**: CRUD completo (`GET`/`POST`/`PUT`/`DELETE`) en `/api/admin/notificaciones-contactos`.
- **Cambio en `templates/index.html`**: nuevo apartado "🔔 Notificaciones adicionales" — alta de contactos + tarjeta por contacto con matriz de checkboxes Departamento × Estado.
- **Verificación**: `python3 -m py_compile app.py models.py` y `node --check` sin errores. Prueba aislada de la lógica de fusión de destinatarios (5 casos: nuevo, duplicado, dos correos, sin correo, sin reglas) — todos correctos.

## 2026-08-28 — [Control Pedidos] "Comparar listado PDF (SAP)": rellena sola la Fecha tramitación de pedidos antiguos sin el PDF oficial individual adjuntado (v12.30.46)

- Víctor acepta la idea propuesta tras v12.30.45: extender a la comparación masiva del listado de SAP el mismo auto-relleno de Fecha tramitación ya implementado para el PDF oficial individual.
- **Cambio en `app.py`**: `_comparar_listado_pdf_logica` añade una tercera escritura silenciosa — rellena `fecha_tramitacion` con la "fecha de pedido" del listado SAP, SOLO si el pedido no tenía ninguna guardada (nunca se sobrescribe un valor existente, a diferencia de Total Pedido/base imponible). Al reutilizarse desde `_comparar_listado_albaranes_logica`, también aplica a "Comparar Pedidos + Albaranes".
- **Cambio en `templates/index.html`**: nuevo aviso "💾 N «Fecha tramitación» rellenada(s) sola(s)" en el resumen de la comparación.
- **Verificación**: `python3 -m py_compile app.py` y `node --check` sin errores. Prueba aislada de la lógica de relleno con 7 casos (vacía/ya rellena/no encontrado/fecha PDF vacía o inválida/mezcla de varios pedidos) — todos correctos.

## 2026-08-28 — [Control Pedidos] "Fecha tramitación": solo correo electrónico (ya no PDF) — se comprueba/auto-rellena con Fecha Pedido y Fecha Entrega del PDF oficial (v12.30.45)

- Víctor, a partir de dos capturas: el adjunto de «Fecha tramitación» debe ser solo correo electrónico (eliminar PDF, mismo estilo de instrucciones que «Nº Pedido DALI/SAP»); al cargar el PDF de «Nº Pedido» comprobar también su «Fecha Pedido» — si falta la Fecha tramitación, rellenarla sola; si ya hay una y difiere, preguntar cuál es la correcta; y si faltan Fecha de entrega específica y Plazo entrega (días), preguntar si registrar la «Fecha Entrega» del PDF.
- Confirmado con Víctor: se mantiene un único correo en este apartado (ya era así); el correo sigue sin ser obligatorio para pasar a ENVIADO AL PROVEEDOR.
- **Cambio en `app.py`**: `upload_adjunto` separa `tramit_eml` (solo `.eml`/`.msg`) de `vb_eml` (sin cambios, correo o PDF). `_parsear_pdf_pedido_oficial` reconoce también «Fecha Pedido»/«Fecha Entrega» (opcionales, no rechazan el PDF si faltan) y las devuelve en la respuesta de la subida sin escribirlas en la base de datos.
- **Cambio en `templates/index.html`**: nueva `_procesarFechasPdfPedidoOficial()` — auto-rellena o pregunta (con `confirm()`) según los casos de arriba; botón de «Fecha tramitación» ahora solo acepta `.eml`/`.msg`, con texto explicativo al estilo de «Nº Pedido».
- **Verificación**: `python3 -m py_compile app.py` y `node --check` sin errores. Prueba con el PDF real (pedido 16287): reconoce Fecha Pedido 21/08/2026 y Fecha Entrega 21/09/2026.

## 2026-08-28 — [Control Pedidos] "Comparar listado PDF (SAP)" + Albaranes: rellena sola la Base imp. (€) de CUALQUIER entrada ya registrada a la que le faltaba, no solo la última (v12.30.44)

- Víctor, a partir de dos capturas del modal "Comparar listado PDF (SAP)": "cuando realizamos la comparativa de listados y se localizan pedidos introducidos y entradas parciales o totales, el sistema modifica el estado automáticamente e introduce los totales sin igic, cuando estas entradas parciales o totales ya estan registradas pero no se rellenó la celda total sin igic, la aplicacion deberia comprobar si tiene o no valor esta celda y rellenarla en caso de que este vacia".
- **Hueco detectado**: los dos mecanismos de auto-relleno existentes eran demasiado estrechos — `_comparar_listado_pdf_logica()` solo recalcula la ÚLTIMA entrada de cada pedido, y la excepción de `_comparar_listado_albaranes_logica()` (v12.30.36) solo rellenaba la entrada del ÚNICO albarán emparejado en esa comparación. Una entrada antigua no-última, fuera de las coincidencias propuestas, nunca se tocaba aunque su número SÍ apareciera en el "Listado de Albaranes" recién subido.
- **Cambio en `app.py` (`_comparar_listado_albaranes_logica`)**: la excepción anterior se sustituye por un barrido general — recorre TODAS las entradas de TODOS los pedidos ya dados de alta de este hotel y rellena la Base imp. (€) de cualquiera que tenga número de entrada pero le falte el importe, si ese número coincide (normalizado) con un albarán del PDF 2 recién subido. Nunca sobrescribe un valor ya introducido ni toca número/fecha/estado. Un número duplicado en el PDF 2 se descarta por seguridad. Solo aplica cuando se compara CON el listado de Albaranes (PDF 2) — la comparación de un solo PDF sigue igual (sin ese detalle por albarán no se puede resolver).
- **Cambio en `templates/index.html`**: texto del aviso "💾 N base imponible actualizada(s) sola(s)" actualizado ("entradas ya registradas") para reflejar el alcance ampliado.
- **Verificación**: `python3 -m py_compile app.py` y `node --check` sin errores. Prueba aislada del barrido con varios casos (entrada no-última rellenada, entrada ya rellena intacta, sin coincidencia, registro duplicado descartado, varios pedidos a la vez, entrada legacy sin fecha) — todos correctos.

## 2026-08-28 — [Control Pedidos] "Nº Entrada DALI/SAP": la Base imp. (€) de cada entrada pasa a ser obligatoria (parcial o final) (v12.30.43)

- Víctor: "vamos a poner que el total sin igic sea obligatorio para continuar, tanto en parcial como en total" (a partir de una captura de una entrada sin base imponible rellena).
- **Cambio en `app.py`**: nueva `_validar_base_imponible_entradas()` — exige base imponible > 0 en TODAS las entradas (también las antiguas ya guardadas, no solo la nueva). Aplicada en `update_pedido()` al guardar en ENTREGA PARCIAL o ENTREGADO, tanto en la rama de rol Hotel como en la general — 422 con mensaje claro si falta alguna.
- **Cambio en `templates/index.html`**: `_validarBaseImponibleAlbaran()` valida antes de guardar (ambos flujos), resalta la primera casilla vacía; placeholder/título del campo actualizados a obligatorio.
- **Verificación**: `python3 -m py_compile app.py` y `node --check` sin errores. Prueba aislada de `_validar_base_imponible_entradas()` con 7 casos (sin entradas, con/sin importe, importe 0, varias entradas mixtas) — todos correctos.

## 2026-08-28 — [Control Pedidos] "Nº Pedido (DALI/SAP)" solo admite el PDF oficial PRINCESS — Nº Pedido y Total Pedido se leen solos, ya no editables (v12.30.42)

- Víctor: solo se debe poder cargar el PDF de pedido oficial PRINCESS (SAP/DALI, formato fijo) en ese apartado; al subirlo, rellenar solo "Nº Pedido" (del "PEDIDO 00016287" del PDF) y "Total Pedido" (suma de la columna Importe, NO el "Total Pedido..." del PDF, que no incluye descuentos); ambas celdas dejan de ser editables a mano; bloquear el paso a ENVIADO AL PROVEEDOR sin el PDF correcto, con mensaje didáctico; quitar la anotación "opcional" del Total Pedido.
- Confirmado con Víctor: se elimina la opción de correo .eml/.msg en este apartado (solo PDF oficial); al borrar el PDF, los valores ya leídos se conservan hasta subir uno nuevo.
- **Cambio en `app.py`**: nueva `_parsear_pdf_pedido_oficial()` (lee con `pypdf`, regex sobre Nº de Pedido y líneas Cantidad/Precio/Importe, suma Importe) — PDF no reconocido = rechazado con mensaje claro, nunca se guarda a medias. `upload_adjunto` (tipo `pedido_doc`): solo PDF, exige lectura correcta, actualiza `pedido_num`/`total_pedido` del pedido al guardar. `create_pedido`/`update_pedido`: ignoran esos dos campos si llegan del formulario — solo cambian vía el PDF (o, `total_pedido`, también vía "Comparar listado PDF (SAP)"). Validación de ENVIADO AL PROVEEDOR actualizada al nuevo mensaje.
- **Cambio en `templates/index.html`**: ambos campos de solo lectura para todos los roles, "(automático)" en vez de "(SAP, opcional)", adjuntar solo admite `.pdf`, autorelleno inmediato tras subir, aviso previo a ENVIADO AL PROVEEDOR actualizado, atajo "Crear pedido desde comparación" ya no escribe el campo (solo avisa del Nº SAP).
- **Aviso**: pedidos ya en curso (no enviados aún al proveedor) necesitarán el PDF oficial para poder avanzar, aunque ya tuvieran Nº de Pedido a mano — comportamiento pedido explícitamente por Víctor.
- **Verificación**: `python3 -m py_compile app.py` y `node --check` sin errores. Prueba con el PDF real (pedido 16287): reconoce "16287" y 4.614,60 € correctamente, ignorando el 7.491,00 € incorrecto del PDF. Prueba con PDF no oficial: rechazado con mensaje didáctico.

## 2026-08-28 — [Control Pedidos] "Línea temporal": mostraba el Nº interno del pedido en vez del Nº Pedido (DALI/SAP) (v12.30.41)

- Víctor, a partir de dos capturas del panel principal: "en estos avisos no se está utilizando el número de pedido DA/SAP que sería lo correcto, creo que es el número de apunte #".
- **Confirmado**: el widget usaba `p.norden` (Nº interno autoincremental de la app) en vez de `p.pedido_num` (Nº Pedido DALI/SAP) — mismo criterio ya aplicado en otros paneles (v12.19), no aplicado hasta ahora en este widget.
- **Cambio en `app.py`**: la consulta de `timeline` en `/api/dashboard` añade `p.pedido_num`.
- **Cambio en `templates/index.html`**: se muestra `pedido_num`, con reserva al Nº interno (`#123`) solo si el pedido aún no tiene Nº Pedido (DALI/SAP) asignado.
- **Verificación**: `python3 -m py_compile app.py` y `node --check` sin errores.

## 2026-08-28 — [Control Pedidos] Correo "ENVIADO AL PROVEEDOR": enlace de descarga del PDF del pedido en vez de adjuntarlo (v12.30.40)

- Víctor preguntó primero si se podía adjuntar el PDF del pedido (el de "Nº Pedido DALI/SAP") con EmailJS al pasar a ENVIADO AL PROVEEDOR — se investigó y se confirmó que solo es posible en planes de pago de EmailJS (la cuenta actual está en el plan Free, sin adjuntos) y que el propio límite de subida de la app (20MB) podría superar incluso el tope del plan más caro.
- Víctor, alternativa: "se me ocurre si en vez de adjuntar el archivo se ponga un enlace para descargar de Supabase pulsando en él".
- **Cambio en `models.py`/`app.py`**: nueva tabla `adjunto_descarga_tokens` (token por adjunto, 180 días de validez, reutilizable), en el bloque protegido de `_auto_migrate()`.
- **Cambio en `app.py`**: `_obtener_o_crear_token_adjunto()`/`_enlaces_descarga_pedido_doc()` generan el/los enlaces del PDF de "Nº Pedido (DALI/SAP)"; `enviar_emails_estado()` los añade como botón en el correo al proveedor (sin PDF subido, el correo sale igual, sin enlace). Lógica de servir un adjunto extraída a `_servir_adjunto_response()`, reutilizada por el endpoint existente (`/api/adjuntos/<id>`, con sesión) y por el nuevo endpoint público `GET /descargas/adjunto/<token>` (sin login, para el proveedor).
- Sin coste adicional ni cambio de plan de EmailJS — sustituye por completo la idea de adjuntar el archivo.
- **Verificación**: `python3 -m py_compile app.py` sin errores. Cambio íntegramente de backend, `templates/index.html` no tocado salvo el badge de versión.

## 2026-08-28 — [Control Pedidos] Nuevo apartado "Departamentos" (solo admin): correo por hotel, en copia en el correo interno de cambio de estado (v12.30.39)

- Víctor (registrado antes en `PENDIENTES.md`): correos internos de cambio de estado con copia también al departamento solicitante del pedido — cada hotel tiene su propio correo para el mismo departamento (ej. RESTAURANTE de JN ≠ RESTAURANTE de GY).
- Confirmado con Víctor: pantalla propia en el sidebar (solo admin), solo correo (sin Telegram/popup), y sin correo registrado = se omite en silencio.
- **Cambio en `models.py`/`app.py`**: nueva tabla `departamento_hotel_email` (hotel+departamento → email/email2), en el bloque protegido de `_auto_migrate()`.
- **Cambio en `app.py`**: `GET`/`PUT /api/admin/departamentos-email` (admin); `enviar_emails_estado()` añade el correo del departamento del pedido a la lista de copia, si existe.
- **Cambio en `templates/index.html`**: apartado "📧 Departamentos" — selector de hotel + tabla editable, guardado en bloque.
- Retirado de `PENDIENTES.md`.
- **Verificación**: `python3 -m py_compile app.py` y `node --check` sin errores. Prueba aislada de `_emails_usuario()`.

## 2026-08-28 — [Control Pedidos] El popup de "familia repetida"/techo mensual podía repetirse cada pocos minutos sin parar (v12.30.38)

- Víctor: "la alerta en popup al comprador cuando se tiene duplicada la familia en techo de gastos ¿por qué se recibe cada pocos minutos continuamente?"
- **Causa**: el dedup diario de `_job_familia_repetida_inner()` y `_job_alertas_techo_mensual()` solo se registraba dentro del bucle de Telegram — si un comprador solo tenía el popup activado (sin Telegram para ese evento, o con Telegram activado pero sin `chat_id`), esa fila de control nunca se escribía y el job volvía a encolar el popup en cada pasada.
- **Cambio en `app.py`**: en ambos jobs, el dedup se registra ahora una sola vez por hotel en cuanto hay al menos un destinatario, sin depender de que el envío por Telegram se complete.
- **Pendiente de confirmar**: patrón similar, más estrecho, detectado en `_job_techo_urgente_admins_inner()` (avisos a admins) — no tocado, a la espera de que Víctor confirme si también le ocurre ahí.
- **Verificación**: `python3 -m py_compile app.py` sin errores.

## 2026-08-28 — [Control Pedidos] El correo/Telegram de cambio de estado automático ya no muestra el nombre de quien tenía la sesión abierta (v12.30.37)

- Víctor, a partir de dos correos reales: "Si es automático no indicar el nombre del administrador, se indica cierre automático comparación listados fecha hora" — y de paso preguntó por qué una entrega no tenía base imponible.
- **Causa**: `enviar_emails_estado()` / `_telegram_cambio_estado()` mostraban siempre `usuario_nombre` (quien tenía la sesión abierta) en "Realizado por"/"Modificado por", sin distinguir un cambio manual de uno decidido por el cruce automático (`_aplicar_coincidencia_albaran()`, `es_automatico=True`) — y ese flag ni siquiera llegaba hasta Telegram.
- **Cambio en `app.py`**: con `es_automatico=True`, ambos canales muestran "Cierre automático — comparación de listados (fecha hora)" en vez del nombre. Cambios manuales, sin cambios.
- **Sobre la base imponible que faltaba**: no era un bug — esos correos son de entradas registradas antes del 27/08 (antes de que existiera la celda "Base imp."). Se autocompletará en la próxima comparación tras desplegar v12.30.36 (entregada justo antes, ver abajo).
- **Verificación**: `python3 -m py_compile app.py` sin errores.

## 2026-08-28 — [Control Pedidos] "Comparar Pedidos + Albaranes": la base imponible de coincidencias ya al día se rellena sola, sin esperar a "Aplicar" (v12.30.36)

- Víctor: "vale si esta información ya está cruzada y es correcta ¿porqué no la automatizamos también junto a la que ya tenemos automatizada?" — tras explicarle en v12.30.35 qué hace "Aplicar todas las seleccionadas" y qué queda pendiente cuando una fila ya está en el estado correcto.
- **Causa**: las filas `sin_cambios_pendientes=True` (albarán ya registrado, estado ya correcto, fecha ya guardada) están excluidas tanto de la tabla visible como del aviso de confirmación automática (v12.30.32) — `_aplicar_coincidencia_albaran()` nunca se llega a llamar para ellas, así que una base imponible que faltase nunca se rellenaba, pese a que el mecanismo de v12.30.35 ya sabe hacerlo.
- **Cambio en `app.py`**: `_comparar_listado_albaranes_logica()` gana una única excepción a su contrato de "solo lectura" (mismo criterio que Total Pedido/base imponible en `_comparar_listado_pdf_logica()`, v12.30.30/31): si una coincidencia es `sin_cambios_pendientes=True` y le falta la base imponible, se rellena sola con el importe de esa coincidencia — nunca toca fecha, número de entrada nuevo ni estado, eso sigue requiriendo "Aplicar" explícito. Escritura antes de invocar internamente a `_comparar_listado_pdf_logica()`, para que su cálculo (más fiable) prevalezca si tocan la misma entrada. Nuevo contador `base_imponible_albaranes_actualizados`.
- **Cambio en `templates/index.html`**: nuevo indicador en el resumen de "Comparar Pedidos + Albaranes" con el recuento de bases imponibles rellenadas así.
- **Verificación**: `python3 -m py_compile app.py` sin errores. Prueba aislada en Python (6 casos: relleno, no sobrescritura, entrada correcta entre varias, normalización de ceros, sin albarán registrado, importe `None`) — todos correctos. `node --check` sobre el JS extraído de `templates/index.html`, sin errores.

## 2026-08-28 — [Control Pedidos] "Aplicar todas las seleccionadas" ya rellena también la base imponible de la entrada de albarán (v12.30.35)

- Víctor: "los totales de las entregas aun estando en el estado correcto se copian si las celdas están vacías?" — confirmé que no y pidió conectarlo.
- **Causa**: `_aplicar_coincidencia_albaran()` (botón "Aplicar todas las seleccionadas") es anterior a la celda "Base imp. (€)" por entrada (v12.30.31) y nunca se conectó con ella — solo guardaba número + fecha del albarán, aunque el importe ya estaba disponible en ese momento (es la misma columna "Importe" que se ve en la tabla de coincidencias).
- **Cambio en `app.py`**: `_serializar_entrada_albaran()` gana un 3er parámetro opcional `base_imponible`. Al crear una entrada nueva se guarda ya con su importe; si la entrada ya existía sin importe, se rellena la celda vacía sin tocar número/fecha ni duplicar nada.
- **Verificación**: `python3 -m py_compile app.py` sin errores. Prueba aislada en Python de los 5 casos (nueva con/sin importe, relleno de existente, reparseo, caso sin fecha) — todos correctos.

## 2026-08-28 — [Control Pedidos] "Comparar listado PDF (SAP)" fallaba con `column "total_pedido" does not exist` — la columna nunca se creó en Supabase (v12.30.34)

- Víctor: al usar "Comparar listado PDF (SAP)" en Pedidos, error `column "total_pedido" does not exist LINE 1: SELECT id, norden, pedido_num, estado, total_pedido, entrada...` — con capturas del modal y del aviso.
- **Causa**: el `ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS total_pedido NUMERIC(10,2)` de v12.30.30 vivía casi al final de `_auto_migrate()`, dentro del tramo de 100+ sentencias sin `try/except` individual — si cualquier sentencia anterior fallaba por cualquier motivo, la función entera se abortaba ahí y esta columna, al ir casi la última, nunca se creaba. Mismo patrón de fallo ya documentado en el código y sufrido antes con `sujeto_seguimiento`.
- **Cambio en `app.py`**: la sentencia se traslada al bloque protegido del principio de `_auto_migrate()` (el mismo que ya usan `sujeto_seguimiento` y el hotel "PR"), con su propio `try/except`, para que se intente en cada arranque sin depender de que el resto de la función no falle antes de llegar a ella.
- **Arreglo inmediato dado a Víctor** para desbloquear sin esperar al redeploy: ejecutar a mano en el editor SQL de Supabase `ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS total_pedido NUMERIC(10,2);` (misma sentencia, idempotente y segura).
- **Verificación**: `python3 -m py_compile app.py` sin errores.

## 2026-08-27 — [Control Pedidos] Comparación Pedidos+Albaranes: pendientes sin aplicar ya no desaparecen del correo, y todos los correos de pedidos muestran los importes como base imponible sin IGIC (v12.30.33)

- Víctor: "la información de lo pendiente en caso de no hacerlo automáticamente se registra también en el correo, por otro lado, las comunicaciones tanto internas como a los proveedores, deberán llevar también los valores de entregas parciales, totales, total pedido etc, indicando siempre que se tratan de bases imponibles (totales sin IGIC)".
- **Parte 1**: si el administrador cancelaba el aviso de confirmación automática de v12.30.32 (o esas coincidencias no llegaban a aplicarse por cualquier motivo), desaparecían del correo de resumen sin dejar rastro. `comparar_listado_albaranes_enviar_resumen()` calcula ahora `coincidencias_no_aplicadas` y `_email_resumen_comparacion_albaranes()` las añade a "⏳ Pendientes de realizar" con el motivo y el estado destino.
- **Parte 2**: `_resumen_entregas()` incorpora la base imponible de cada entrada y `total_recibido`; `_html_bloque_entregas()` / `_text_bloque_entregas()` / `_telegram_bloque_entregas()` muestran importes por entrega y el aviso fijo de base imponible (sin IGIC). El correo interno de cambio de estado añade fila "Total Pedido (base imponible)" (distinta de "Importe (techo de gastos)"). El correo al proveedor de confirmar recepción, el recordatorio "enviado al proveedor sin confirmar", el recordatorio de "entrega parcial sin cerrar" (con detalle completo de entregas) y el aviso de "pendiente de firma" incluyen ahora el Total Pedido con el mismo aviso. El correo de la comparación Pedidos+Albaranes también incluye el aviso de base imponible. Nuevo helper `_nota_base_imponible_html()` / `_nota_base_imponible_text()` reutilizado en todos los puntos.
- **Fuera de alcance, decisión comunicada a Víctor**: los correos de "cotización pendiente" no llevan Total Pedido — en esa fase del pedido normalmente aún no está cumplimentado.
- **Verificación**: `python3 -m py_compile app.py` sin errores. No se tocó `templates/index.html` (cambio íntegro de backend/plantillas de correo).

## 2026-08-27 — [Control Pedidos] "Comparar Pedidos + Albaranes": registro automático de entregas con un único aviso de confirmación (v12.30.32)

- Víctor: "en la comparación de pedidos, cuando las entregas parciales o totales no existen registradas en controlpedidos, la aplicación las registrará automáticamente cambiando también automáticamente los estados al que corresponda... solo preguntar al finalizar la comparación y con aceptar por parte del administrador se realizará automáticamente". Aclaró después que el registro automático solo debe activarse cuando se aportan los DOS listados (Pedidos + Albaranes).
- **Hallazgo**: revisando `/api/pedidos/comparar-listado-albaranes/<job_id>/aplicar` (v12.30.15) ya existía todo el mecanismo — acepta `{"todas": true}` para aplicar de una vez todas las coincidencias, y el correo de resumen ya incluía la sección "✅ Registrados automáticamente". Solo faltaba el disparador.
- **Cambio en `templates/index.html`**: al terminar la comparación de los dos PDF, si hay coincidencias con cambios reales pendientes, un único aviso pregunta si registrarlas automáticamente ahora (llama a `.../aplicar` con `{todas:true}`). Si se cancela, la tabla de revisión manual sigue disponible igual que antes.
- **Cambio en `app.py`**: el correo de resumen conjunto añade el mismo aviso que el correo del listado de un solo PDF, pidiendo al comprador que dé de alta manualmente los pedidos no registrados (la creación automática de pedidos nuevos queda fuera de alcance).
- **Verificación**: `python3 -m py_compile app.py` y `node --check` sobre el JS extraído de `templates/index.html`, sin errores.

## 2026-08-27 — [Control Pedidos] Nueva celda "Base imp. (€)" por entrada DALI/SAP, rellenada automáticamente al comparar (v12.30.31)

- Víctor: "añadir junto a las entradas también una celda donde introducir siempre la base imponible de las entradas... completando la misma con el listado de pedido en comparación, si la entrega es parcial se completa con la columna 7, si es total con la 7, restando las entradas parciales previas que pudieran existir".
- **Diferencia clave con Total Pedido**: SAP solo da un importe recibido ACUMULADO por pedido (columna 7), no desglosado por albarán — hay que descontar lo que ya corresponde a entregas parciales anteriores del mismo pedido.
- **Cambio en `app.py`**: el formato de `pedidos.entrada_albaran_num` gana un tercer segmento opcional "NUM::FECHA::BASE_IMPONIBLE", retrocompatible (`_parse_albaran_entries`, `format_albaran_display`, nueva `_construir_entrada_albaran_num`). `_comparar_listado_pdf_logica()` calcula la base imponible de la ÚLTIMA entrada de cada pedido localizado con al menos una entrada ya registrada = columna 7 menos la suma de bases imponibles ya registradas en entradas anteriores; si no hay ninguna anterior, es directamente la columna 7. Resultado negativo (datos inconsistentes) → no se escribe, se deja para revisión manual.
- **Cambio en `templates/index.html`**: nueva celda "Base imp. (€)" editable en cada fila de entradas DALI/SAP. El resumen de "Comparar listado PDF" muestra cuántas se han actualizado.
- **Verificación**: `python3 -m py_compile app.py` sin errores. Suite aislada en Python del parseo/reconstrucción del nuevo formato de 3 segmentos (retrocompatibilidad y round-trip), todas correctas. `node --check` sin errores.

## 2026-08-27 — [Control Pedidos] Nuevo campo "Total Pedido", rellenado automáticamente al comparar el listado de SAP (v12.30.30)

- Víctor: "podemos insertar el total del pedido localizado en un apartado TOTAL PEDIDO que aún no existe en la ventana creación edición pedido?... que al introducir el PDF y localizar el pedido la aplicación lo cumplimente como valor real del pedido. El valor será la columna sexta del PDF PEDIDOS" — adjuntó un PDF real del "Listado de Pedidos" de SAP para identificar la columna.
- **Hallazgo**: la 6ª columna visual del PDF ya se extraía internamente como `importe_base` (base imponible del pedido en SAP) en `_PATRON_LISTADO_SIMPLIFICADO`, usada en "Comparar listado PDF" — no hacía falta tocar el parseo, solo guardarla.
- **Cambio en `app.py`**: nueva columna `pedidos.total_pedido` (NUMERIC, opcional); `POST/PUT /api/pedidos` la aceptan y guardan igual que el resto de campos (editable a mano). `_comparar_listado_pdf_logica()` guarda `total_pedido = importe_base` sin pedir confirmación — única excepción a la filosofía de "solo propone, nunca escribe sola", justificada por ser un campo puramente informativo (no dispara emails ni cambia estado). Solo escribe si el valor cambia.
- **Cambio en `templates/index.html`**: nuevo campo "Total Pedido (€)" en la ficha del pedido. El resumen de "Comparar listado PDF" muestra cuántos se han actualizado en esta pasada.
- **Verificación**: `python3 -m py_compile app.py` y `node --check`, sin errores.

## 2026-08-27 — [Control Pedidos] Techo de Gastos: al aprobar navegando directo a esa sección, vuelve a la ficha del pedido y avisa de que ya está ENVIADO AL PROVEEDOR (v12.30.29)

- Víctor, continuando el fix de v12.30.28: "cuando se aprueba el techo de gasto se deberá devolver a la ventana de pedido y con un aviso en pantalla indicar que ya se puede cambiar el estado a ENVIADO AL PROVEEDOR". Al revisar `aprobar_expediente()`, el backend ya cambiaba el pedido a ENVIADO AL PROVEEDOR automáticamente al aprobar (incluye email al proveedor) — no había ningún cambio manual pendiente. Víctor matizó: comportamiento distinto según si se llega a Techo de Gastos desde un intento bloqueado en la ficha del pedido (dejar como está, solo toast) o navegando allí directamente (reabrir la ficha y avisar).
- **Cambio en `templates/index.html`**: `guardarPedido()` anota en `G._techoOrigenPedidoExpId` el id del expediente que provoca su redirect automático. `resolverExpedienteTecho()` compara ese id contra el expediente aprobado: si coincide, comportamiento sin cambios (toast); si no coincide, abre `openPedidoModal()` de ese pedido y muestra un aviso confirmando que ya se envió al proveedor.
- **Cambio en `app.py`**: la respuesta de `POST /api/expedientes/<id>/aprobar` incluye ahora `pedido_id`.
- **Verificación**: `python3 -m py_compile app.py` y `node --check`, sin errores.

## 2026-08-27 — [Control Pedidos] Pedidos → ENVIADO AL PROVEEDOR: dejar de duplicar el apunte de Techo de Gastos en cada reintento (v12.30.28)

- Víctor: cuando un pedido PENDIENTE FIRMA DIRECCION GENERAL intenta pasar a ENVIADO AL PROVEEDOR, se genera un apunte en Techo de Gastos que hay que aceptar allí — si el usuario insiste en reintentar sin darse cuenta, se generaban tantos apuntes duplicados como intentos.
- **Causa**: en `update_pedido()`, antes de crear un nuevo `expediente_exceso` no se comprobaba si ya existía uno pendiente sin resolver para ese pedido.
- **Cambio en `app.py`**: se busca primero si ya hay un `expediente_exceso` con `resultado='pendiente'`; si lo hay, se corta ahí (nunca se crea un segundo) y se devuelve 422 con `expediente_pendiente_id`/`hotel_codigo`.
- **Cambio en `templates/index.html`**: `guardarPedido()` reconoce `r.expediente_pendiente_id`, cierra el modal, avisa, y lleva directamente a la tarjeta de Techo de Gastos correspondiente (`irATechoHotel()`).
- **Nota**: no fusiona ni borra apuntes duplicados ya creados antes de este cambio — esos hay que resolverlos a mano.
- **Verificación**: `python3 -m py_compile app.py` y `node --check` (8 bloques `<script>`, 178.889 caracteres), sin errores.

## 2026-08-27 — [Control Pedidos] Nuevo endpoint `GET /api/externo/dali-sap/proveedores`: DALI puede reutilizar los contactos de "Proveedores" de esta app (v12.30.27)

- Víctor, sobre el puente de correos de v12.30.26: "como vamos a utilizar el sistema de envíos de control_pedidos, podríamos utilizar también el apartado de proveedores con sus correos electrónicos etc? de esta manera los tenemos únicamente en un único punto y podemos incluir más correos para el envío, ahora en artículos es solo uno". Confirmado también que el contador de EmailJS se descuenta igual para estos correos encolados — no hay ningún camino que los salte.
- **Cambio en `app.py`**: nuevo `GET /api/externo/dali-sap/proveedores`, misma autenticación por firma HMAC que `POST .../emails-pendientes` (v12.30.26), devuelve los proveedores activos con sus contactos (reutilizando `_prov_with_contactos`) — nombre, `email_principal` y lista completa de contactos con email. DALI cruza por NOMBRE exacto contra su propio catálogo (Víctor mantiene los nombres idénticos entre ambas apps a propósito) y usa el contacto principal como destinatario; si no hay contacto marcado como principal, usa el primero (mismo comportamiento que tenía antes con el email único).
- **Verificación**: `python3 -m py_compile app.py` sin errores.

## 2026-08-27 — [Control Pedidos + DALI] Puente de correos desde el catálogo DALI: sus avisos de "documentación faltante" pasan a usar la cola y el envío por EmailJS de esta app (v12.30.26)

- Víctor: "podemos aprovechar la organización que tenemos actualmente en controlpedidos para el envío de correos y que los correos de dalisaparticulos utilicen la misma infraestructura?... la idea es que los correos para la solicitud de documentación faltante utilicen este método de EmailJS, se podría generar, dejar en cola y cuando alguien abra Control de Pedidos se lance, de esta manera podríamos reestructurar y hacer más atractivo y profesional los correos electrónicos, con logo, colores etc." La reclamación de documentación pendiente a un proveedor la generaba DALI como texto plano para copiar o abrir en el cliente de correo de Víctor — sin envío real ni diseño.
- **Cambio en `app.py`**: nuevo `POST /api/externo/dali-sap/emails-pendientes`, sin sesión de usuario (llamada servidor a servidor desde el backend Node de DALI) protegido con firma HMAC-SHA256 usando el secreto ya compartido `DALI_SSO_SECRET` (hasta ahora solo usado para el SSO del menú "Catálogo DALI") — nada nuevo que configurar en Render. El correo se inserta en `emails_sistema_pendientes` (`evento_codigo='dali_documentacion_faltante'`) y lo despacha el poller que ya existía, sin cambios en el frontend de esta app. Comparte la cuenta EmailJS activa de esta app (entra en la rotación normal entre las 3 cuentas).
- Ver el repo de DALI (`HISTORIAL.md`) para el lado que genera y envía estos correos.
- **Verificación**: `python3 -m py_compile app.py` sin errores.

## 2026-08-22 — [Control Pedidos + DALI] SSO hacia DALI: token subido de 60s a 100s, margen de DALI reajustado de 90s a 20s (v12.30.25 / DALI v1.18.2)

- Víctor, en DALI: primer acceso del día muy lento, "Comprobando
  sesión…" congelada, y a veces caída al login manual entrando desde el
  menú "Catálogo DALI" de aquí, aunque las credenciales fueran
  correctas.
- **Causa (diagnosticada en el repo de DALI, ver su `HISTORIAL.md`
  v0.60)**: el backend de DALI (plan gratuito de Render) duerme tras 15
  min sin tráfico y tarda ~60s (a veces más) en despertar. El token de
  SSO que genera este backend (`_generar_token_sso_dali`) solo duraba
  60s (70s con el margen de reloj del lado de DALI) — una ventana casi
  calcada al propio cold-start, sin margen real. El mismo día se aplicó
  primero un parche solo en DALI (margen de aceptación ampliado a 90s,
  DALI v1.18.0) para no bloquear en tocar este repo sin permiso; este
  cambio es el arreglo de raíz, con el visto bueno explícito de Víctor.
- **Cambio en `app.py`** (Control Pedidos): `_generar_token_sso_dali`,
  `ttl_segundos` sube de 60 a 100 — cubre un cold-start normal de Render
  por sí solo, con margen de sobra.
- **Cambio en `backend/src/controllers/authController.js`** (DALI, repo
  aparte `dali-sap-articulos-app`): `SSO_MARGEN_RELOJ_SEGUNDOS` baja de
  90 a 20 — con el TTL ya arreglado arriba, el margen vuelve a ser solo
  margen real de reloj/latencia, no un sustituto del TTL. `backend/` y
  `frontend/package.json` de DALI suben a 1.18.2.
- Ventana total efectiva del token: ~120s (100s + 20s) — antes ~150s
  (60s + 90s), pero repartidos de forma menos correcta (todo el peso en
  el margen "parche" de DALI en vez de en el TTL de origen).
- **Verificación**: `python3 -m py_compile app.py` (Control Pedidos) y
  `node --check` sobre `authController.js` (DALI), ambos sin errores.

## 2026-08-20 — [Control Pedidos] Recordatorio de "correos de sistema en cola": seguía avisando de filas descartadas/paradas, con título de popup engañoso (v12.30.24)

- Víctor, justo tras descartar a mano 4 correos atascados: le llegó un
  popup titulado "📋 Nueva solicitud de acceso" avisando de esas mismas
  4 filas ya descartadas — título sin relación con el contenido real.
- **Causa**: `_job_recordar_emails_sistema_pendientes()` nunca excluía
  de su consulta las filas ya descartadas (`descartado_en`) ni las ya
  paradas por el freno de reintentos (`intentos >= MAX_INTENTOS...`) —
  las seguía contando como "pendientes" y avisando cada 30 min, aunque
  abrir la app no fuera a hacer nada por ellas. Además reutilizaba
  `_notify_solicitud_telegram()`, con el título fijo "Nueva solicitud
  de acceso" pensado para otro tipo de aviso completamente distinto.
- **Cambio en `app.py`**: consulta del job ahora excluye descartadas y
  ya-agotadas. El job llama a `_notificar_evento()` directamente, mismos
  destinatarios configurados de siempre, pero con título correcto:
  "⏰ Correos de sistema en cola".
- **Verificación**: `python3 -m py_compile app.py` sin errores.

## 2026-08-20 — [Control Pedidos] Envíos automáticos por EmailJS: correo real duplicado cuando fallaba la confirmación tras un envío exitoso (v12.30.23)

- Víctor, tras desplegar v12.30.22: el panel de cola mostraba solo 4
  filas antiguas ya descartadas/agotadas (0 activas) y aun así "ya paso
  a 116 emailjs" — el cupo seguía bajando con la cola visible limpia.
- **Causa**: en el poller `_enviarEmailsSistemaPendientes()`, si el
  correo se enviaba con éxito por EmailJS pero la llamada posterior de
  confirmación (`marcar-enviado`) fallaba (red, sesión caducada...), la
  fila quedaba `enviado = FALSE` aunque ya se hubiera entregado de
  verdad. Al caducar la reserva de 2 minutos, la misma fila se
  reenviaba DE VERDAD por EmailJS de nuevo — duplicado real, no un 413
  fallido, descontando cupo con éxito cada vez. Encaja con los 3
  correos de resumen idénticos que Víctor había encontrado antes en su
  bandeja de enviados.
- **Cambio en `templates/index.html`**: la confirmación se reintenta
  ahora hasta 3 veces con una breve espera entre intentos antes de
  rendirse; si aun así falla, se deja un error claro en consola en vez
  de un aviso genérico indistinguible de un fallo de envío real.
- **Verificación**: `node --check` sobre el JS extraído, sin errores.

## 2026-08-20 — [Control Pedidos] Cola de emails de sistema: bajar el margen de reintentos y ampliar el panel de admin a toda la cola pendiente (v12.30.22)

- Víctor, tras desplegar v12.30.21: "de 76 emailjs paso a 91 y un solo
  correo enviado" — 15 peticiones descontadas de golpe, con un único
  correo (el de esta prueba) realmente enviado. Preguntó si podía ser
  cola acumulada de antes.
- **Causa**: confirmado, sí es cola acumulada de antes. El freno de
  v12.30.21 añadió la columna `intentos` con `DEFAULT 0`, que rellena a
  0 el contador en las filas YA existentes en la cola (las oversized de
  pruebas anteriores a v12.30.20) — arrancan con el cupo de reintentos
  completo por delante en vez de con lo ya acumulado, así que tras el
  propio despliegue del freno cada una pudo fallar y descontar cupo
  hasta 8 veces más antes de pararse sola, sin aparecer aún en el panel
  de "Correos atascados" (que solo mostraba filas ya agotadas). La
  captura de red de Víctor lo confirma: los 4 fallos 413 ocurren en la
  PRIMERA llamada a `emails-sistema-pendientes` (280 kB), antes de
  invocarse "Enviar resumen" — son filas viejas, no el correo nuevo
  (que se envió bien a la primera).
- **Cambio en `app.py`**: `MAX_INTENTOS_EMAIL_SISTEMA` bajado de 8 a 3
  — acorta el margen de cupo que las filas ya atascadas desde antes
  pueden seguir gastando tras cada despliegue del freno, sin penalizar
  reintentos legítimos por fallos puntuales de red. `GET
  /api/admin/emails-sistema-atascados` ampliado para listar TODA la
  cola pendiente (no solo las ya agotadas), ordenada por tamaño de HTML
  descendente, con un campo `atascado` para distinguir "parado" de
  "aún reintentando".
- **Cambio en `templates/index.html`**: el panel Admin → Config
  alertas → EmailJS ("Cola de correos de sistema pendientes") muestra
  ahora la cola completa con una etiqueta de estado por fila — el botón
  "Descartar" sigue disponible en cualquier fila, sin esperar a que se
  pare sola.
- **Verificación**: `python3 -m py_compile app.py` y `node --check`
  sin errores.

## 2026-08-19 — [Control Pedidos] Cola de emails de sistema: freno de reintentos infinitos — descontaba cupo de EmailJS sin límite sin llegar a entregarse (v12.30.21)

- Víctor, tras desplegar v12.30.20: "estaba en 54 emailjs y pasó a 71" —
  17 peticiones descontadas sin que llegara ningún correo nuevo.
- **Causa**: el fix de tamaño de v12.30.20 solo afecta a correos
  NUEVOS al encolarse — no cambia el contenido de una fila que ya
  llevaba encolada desde antes del despliegue, con el HTML antiguo
  (más grande). Esa fila seguía fallando siempre (413) y, como la cola
  no tenía límite de reintentos, se reintentaba sola indefinidamente
  cada vez que caducaba su reserva de 2 minutos — descontando cupo en
  cada intento, con o sin éxito, sin que nadie lo viera.
- **Cambio en `app.py`**: nuevas columnas `intentos` y `descartado_en`
  en `emails_sistema_pendientes`. La cola deja de reintentar una fila
  al llegar a 8 intentos sin éxito, o si se descarta a mano. Nuevos
  endpoints de admin para listar y descartar correos atascados.
- **Cambio en `templates/index.html`**: Admin → Config alertas →
  EmailJS muestra ahora un aviso de "Correos atascados" (asunto,
  destinatario, intentos, tamaño, botón Descartar) cuando los hay —
  antes este drenaje de cupo era invisible desde la aplicación.
- **Nota**: la fila que llevaba fallando desde antes de hoy dejará de
  reintentarse sola al acumular 8 intentos (puede que ya los tenga) —
  no hace falta tocar la base de datos a mano.
- **Verificación**: `python3 -m py_compile app.py` y `node --check`
  sin errores. Migración idempotente vía `_auto_migrate()`.

## 2026-08-19 — [Control Pedidos] Correo de resumen de "Comparar Pedidos + Albaranes": límite de tamaño conjunto en vez de tres límites independientes (v12.30.20)

- Víctor: "llego un correo con el resumen pero descontó casi 10 correos
  en emailjs, en F12 salen varios intentos fallidos".
- **Causa**: los fixes anteriores de hoy acotaban cada una de las 3
  tablas del correo (sin dar de alta / registrados automáticamente /
  pendientes) por separado, con un límite de filas fijo cada una — pero
  eso no evita que la SUMA de las tres, cuando las tres son grandes a
  la vez, siga superando el límite real de EmailJS. Simulación: 120 +
  90 + 79 filas (recortadas a 50 cada una, el límite anterior) daban
  62.083 caracteres — muy por encima del límite conocido que causa 413.
- **Cambio en `app.py`**: `_email_resumen_comparacion_albaranes()`
  reescrita para probar niveles de recorte cada vez más agresivos —
  (50,50,50) → (30,30,25) → (15,15,12) → (6,6,5) filas por tabla — y
  quedarse con el primero cuyo tamaño total quede bajo un margen de
  seguridad (22.000 caracteres; el caso real conocido: 24.002 SÍ
  llegó, 36.445 dio 413). Ya no hay límites fijos independientes por
  tabla. La pantalla sigue sin ningún límite, como siempre.
- **Verificación**: `python3 -m py_compile app.py` sin errores.
  Simulación con el caso extremo (120/90/79 filas grandes a la vez):
  recorta automáticamente a 19.078 caracteres. El caso real de 79
  pendientes solos se queda en el primer nivel, 16.264 caracteres, sin
  recorte innecesario.

## 2026-08-19 — [Control Pedidos] Correo de cambio de estado: excluir solo a la persona concreta (no a todo su rol) + Comparar Pedidos + Albaranes: pedido 42644 dejaba de mostrarse siempre pendiente aunque ya estaba ENTREGADO (v12.30.19)

- Víctor, sobre el correo (v12.30.18): "solo se excluya a la persona
  concreta" — no a todo el lado/rol (comprador u hotel), porque puede
  haber más de una persona por rol en el mismo hotel y las demás deben
  seguir recibiendo el correo.
- **Cambio en `app.py`**: `enviar_emails_estado()` ya no excluye por
  rol — consulta el email (y email2) de `usuario_id` y lo quita de la
  lista de destinatarios del correo interno; el resto de compañeros de
  su mismo rol siguen recibiéndolo con normalidad. Automático o sin
  `usuario_id` conocido: se manda a todos, como antes.
- Víctor, sobre la comparativa: "seguimos con problemas de
  identificación aun enviando el listado desde el 01-05-2026 ; sigue
  identificando el pedido 42644 como entrega parcial" — con los dos PDF
  completos del hotel FV adjuntos.
- **Causa**: en los PDF, el pedido SAP 00042644 tiene base 1.513,35 €
  pero SAP solo registra 1.274,40 € "recibido" (238,95 € pendientes
  según SAP), así que `_entrega_estado()` lo clasifica "Entrega
  parcial". El pedido ya está ENTREGADO en la app (esos 1.274,40 €
  coinciden con el albarán DALI 00081970, ya registrado).
  `_aplicar_coincidencia_albaran()` ya protegía este caso (no retrocede
  un ENTREGADO), pero la comparativa no aplicaba esa misma protección
  al construir la fila: seguía mostrando "ENTREGADO → ENTREGA PARCIAL"
  como si fuera a retroceder, así que el pedido reaparecía como
  pendiente en cada comparación aunque no había nada que hacer.
- **Cambio en `app.py`**: nueva constante única `_ORDEN_ENTREGA_ESTADOS`
  (antes duplicada dentro de `_aplicar_coincidencia_albaran()`), usada
  también en `_comparar_listado_albaranes_logica()` para calcular
  `estado_ya_avanzado` (el pedido ya está, en la app, por delante de lo
  que propone SAP) y marcar `sin_cambios_pendientes` cuando no hay
  ningún cambio real que aplicar, en vez de reaparecer indefinidamente.
- **Cambio en `templates/index.html`**: con `estado_ya_avanzado`, la
  columna de estado muestra "ENTREGADO (ya en un estado más avanzado —
  SAP aún lo muestra como ENTREGA PARCIAL)" en vez de un falso
  retroceso "ENTREGADO → ENTREGA PARCIAL".
- **Verificación**: `python3 -m py_compile app.py` y `node --check`
  sin errores. Extraído el texto de los PDF adjuntos, localizada la
  línea real del pedido 42644 y el albarán 00081970, y reproducido el
  caso en una simulación aislada: `estado_ya_avanzado=True`,
  `sin_cambios_pendientes=True` con los importes y el estado reales.

## 2026-08-19 — [Control Pedidos] Correo de cambio de estado: solo a quien NO ha hecho el cambio — quien lo hizo sigue recibiendo su popup/Telegram (v12.30.18)

- Víctor: "cuando se cambia un estado de pedido, actualmente se envía
  automáticamente un correo al comprador y también al rol hotel,
  podríamos hacer que el correo solo se le envíe al que no ha realizado
  el cambio? es decir, si el cambio lo realiza el hotel, le llega el
  correo al comprador y viceversa, al que ha realizado el cambio le
  debería llegar únicamente un popup ; si el cambio es automático
  entonces sí correo a ambas partes".
- **Cambio en `app.py`**: `enviar_emails_estado()` gana dos parámetros,
  `usuario_id` y `es_automatico`. El correo interno de cambio de estado
  ya no va siempre a compradores + usuarios hotel del hotel — se
  consulta el rol de `usuario_id` (quien hizo el cambio) y se excluye su
  lado: rol `hotel` → correo solo a compradores; cualquier otro rol
  (compras, admin...) → correo solo a usuarios hotel. Con
  `es_automatico=True` (o sin `usuario_id` conocido) se mantiene el
  comportamiento anterior, correo a ambas partes.
  `_notificar_cambio_estado()` reenvía ambos parámetros, sin tocar
  `_telegram_cambio_estado()` — el Telegram/popup del bridge es un canal
  aparte, configurable por usuario en Administrador → Configuración de
  Avisos, no filtrado por quién hizo el cambio, así que quien hizo el
  cambio sigue enterándose por ahí.
- Todos los puntos que disparan un cambio de estado manual (flujo
  normal y flujo hotel de `update_pedido`, aprobar/denegar expediente
  de exceso, creación de pedido) pasan ahora su `usuario_id`. El único
  punto marcado `es_automatico=True` es `_aplicar_coincidencia_albaran()`
  (comparativa de PDF, ver entrada anterior de hoy, v12.30.16/17) —
  coherente con que ese cambio ya se etiqueta "Automática" en el
  Historial de estados.
- **Verificación**: `python3 -m py_compile app.py` y `node --check`
  sobre el JS de `templates/index.html` sin errores. Simulación aislada
  de la lógica de exclusión con 4 escenarios (comprador, hotel, admin,
  automático/desconocido): destinatarios correctos en todos los casos.

## 2026-08-19 — [Control Pedidos] Historial de estados: los registros automáticos de "Comparar Pedidos + Albaranes" ya no aparecen a nombre de quien pulsó "Aplicar" (v12.30.17)

- Víctor: "EN LA TRAZABILIDAD DE CAMBIOS, LOS EJECUTADOS
  AUTOMATICAMENTE DEBERIAN SALIR ASI DEFINIDOS Y NO CON NOMBRE DE
  USUARIO, POR EJEMPLO ENTREGA PARCIAL Automática listado comparativo
  pedidos y albaranes FECHA TAL" — un cambio de estado aplicado
  automáticamente desde la comparativa de PDF salía en el "Historial de
  estados" del pedido con el nombre de quien había pulsado "Aplicar",
  indistinguible de un cambio hecho a mano.
- **Causa**: `_aplicar_coincidencia_albaran()` guardaba en
  `historial_estados.usuario_nombre` el nombre de la sesión que
  confirmó la aplicación, igual que en un cambio manual — el aviso de
  que era automático solo aparecía al final, entre comillas, en la
  nota.
- **Cambio en `app.py`**: esa fila de `historial_estados` ahora guarda
  un texto fijo, `"Automática — listado comparativo pedidos y
  albaranes"`, en vez del nombre real del usuario. Solo afecta a esta
  fila (lo que se ve en el Historial de estados del pedido); no toca
  `modificado_por_id/nombre` del pedido ni los cambios de estado
  manuales, que siguen mostrando el nombre real de quien los hizo.
- **Verificación**: `python3 -m py_compile app.py` sin errores.
  Confirmado que no hay otro punto de aplicación automática con el
  mismo problema (la comparación de solo pedidos, "Comparar listado PDF
  (SAP)", es de solo lectura, sin función de aplicación equivalente).

## 2026-08-19 — [Control Pedidos] Comparar Pedidos + Albaranes: entrada de albarán duplicada con ceros a la izquierda al aplicar una coincidencia, y el pedido volvía a salir como pendiente (v12.30.16)

- Víctor reportó (con capturas) que, al aplicar una coincidencia
  encontrada en "Comparar Pedidos + Albaranes", el campo "Nº Entrada
  DALI/SAP" del pedido acababa con dos entradas para el mismo albarán:
  "81970" y "00081970" (con distinta fecha cada una) — y que en la
  siguiente comparación el mismo pedido volvía a salir como "no
  cerrado" (pendiente).
- **Causa**: dos comprobaciones en `app.py` comparaban el número de
  registro DALI contra lo ya guardado en `entrada_albaran_num` con un
  `in` de texto plano, sin ignorar los ceros a la izquierda — a
  diferencia de los números de pedido, que ya se normalizan con
  `_normalizar_pedido_num()`. Con "81970" ya registrado y "00081970"
  entrante desde el PDF (o al revés), ni `_aplicar_coincidencia_albaran()`
  reconocía que ya estaba (añadía una entrada nueva duplicada) ni
  `ya_registrado` en `_comparar_listado_albaranes_logica()` lo detectaba
  (el pedido seguía saliendo como pendiente en cada comparación
  posterior).
- **Cambio en `app.py`**: nueva `_normalizar_num_albaran()` (mismo
  criterio que `_normalizar_pedido_num()`), usada ahora en ambos
  puntos: `ya_registrado` compara número normalizado contra cada
  entrada ya parseada de `entrada_albaran_num_actual`
  (`_parse_albaran_entries()`), y `_aplicar_coincidencia_albaran()`
  comprueba con la misma normalización antes de añadir una entrada
  nueva, evitando el duplicado. No fusiona automáticamente duplicados
  que ya existieran en pedidos de antes de este cambio.
- **Verificación**: `python3 -m py_compile app.py` sin errores.
  Simulación aislada en Python reproduciendo el caso ("81970" ya
  registrado + "00081970" entrante, y el caso inverso): tanto
  `ya_registrado` como el guard de duplicados dan el resultado correcto
  en ambos sentidos; un caso de control con números realmente distintos
  ("81970" vs "81971") confirma que no se confunden.

## 2026-08-19 — [Control Pedidos] Comparar Pedidos + Albaranes: el correo de resumen no llegaba en hoteles con muchos pendientes — EmailJS lo rechazaba por tamaño, HTTP 413 (v12.30.15)

- Tras descartar cupo agotado y conexión de Gmail rota (ver entrada
  anterior), el síntoma seguía sin explicación: el correo se quedaba en
  cola, EmailJS descontaba cupo de la cuenta activa, pero nunca llegaba.
  Revisando el Network del navegador al pulsar "Enviar resumen por
  correo" se vieron varias peticiones `send` a la API de EmailJS con
  **status 413 (Payload Too Large)** — la petición se cuenta contra el
  cupo pero EmailJS la rechaza por ser demasiado grande. Caso real: un
  hotel con 79 filas en "pendientes de revisión manual", cada una con
  el texto largo del "posible candidato" (v12.30.11/12) — el HTML del
  correo superaba el límite de tamaño por petición de EmailJS.
- **Cambio en `app.py`**: `_motivo_sin_pedido()` (solo el correo; la
  pantalla tiene su propio texto, sin límite) se acorta a menos de la
  mitad, manteniendo lo esencial. `_email_resumen_comparacion_albaranes()`
  añade un límite de 50 filas a la tabla de pendientes del correo (mismo
  patrón que ya usaba `pedidos_faltantes`), con aviso de cuántas se han
  omitido — el contador del asunto y del título sigue mostrando el total
  real; la pantalla de la app sigue mostrando el listado completo sin
  recortar.
- **Verificación**: `python3 -m py_compile app.py` sin errores. Se
  simuló un caso de 79 pendientes con un script aparte: el correo pasa
  de 36.445 a 24.002 caracteres con el límite aplicado. No se pudo
  reproducir el 413 exacto contra la API real de EmailJS desde este
  entorno (sin credenciales de producción) — recomendado repetir la
  comparación del hotel con más pendientes tras desplegar y confirmar en
  el Network del navegador que las peticiones `send` devuelven 200.

## 2026-08-19 — [Control Pedidos] Admin → Config alertas → EmailJS: campo de fecha de reinicio de cupo por cuenta (v12.30.14)

- Investigando por qué había dejado de enviarse el resumen de "Comparar
  Pedidos + Albaranes" (ver más abajo) se descubrió que las 3 cuentas
  EmailJS que usa la app en rotación automática son 3 cuentas EmailJS.com
  independientes, cada una con su propio cupo de 200 envíos/mes y su
  propia fecha de reinicio — y que la Cuenta 2 y la Cuenta 3 estaban
  agotadas (200/200) en ese momento, forzando el cambio automático a la
  Cuenta 1. Saber cuándo recupera cupo cada cuenta exigía entrar a cada
  una por separado en EmailJS.com.
- Petición de Víctor: poder indicar la fecha de reinicio de cada cuenta
  desde el propio panel de la app, para tenerlas todas controladas de un
  vistazo.
- **Cambio en `app.py`**: 3 nuevas claves de configuración
  (`emailjs_reinicio_fecha_1/2/3`, puramente informativas, sin uso en
  ninguna lógica automática), añadidas a `_auto_migrate()` y a los
  valores por defecto de `get_config()`.
- **Cambio en `templates/index.html`**: nuevo campo de fecha "Reinicia
  cupo el" en cada una de las 3 tarjetas de cuenta del panel Admin →
  Config alertas → EmailJS, y aviso con la fecha de la cuenta
  actualmente activa en la cabecera del panel. El guardado ya era
  genérico (por `id="cfg_..."`), no hizo falta tocar el JS de guardado.
- **Verificación**: `python3 -m py_compile app.py` y `node --check`
  sobre el JS extraído, ambos sin errores. Cambio aditivo y puramente
  informativo.

## 2026-08-19 — [Control Pedidos] Comparar Pedidos + Albaranes: identificar los pedidos por su número DALI/SAP, no por el "Nº" lineal interno (v12.30.13)

- Petición de Víctor: "MEJOR INDICAR NUMERO PEDIDO DALI / SAP Y NO EL
  LINEAL Nº; ES MAS INTUITIVO Y FACIL DE VERIFICAR EN NUESTROS
  LISTADOS" — varias referencias a un pedido en la pantalla "Comparar
  listado PDF" (Pedidos + Albaranes) se mostraban como "42438 (Nº618)":
  el número de pedido DALI/SAP seguido, entre paréntesis, del número de
  línea interno correlativo de la app. Ese segundo número no aparece en
  los listados que Víctor consulta para verificar, así que solo añadía
  ruido.
- **Cambio en `app.py`** (`_motivo_sin_pedido`): el "posible candidato"
  sugerido para un albarán sin pareja de importe exacto se identifica
  ahora solo por su número de pedido DALI/SAP.
- **Cambio en `templates/index.html`**: mismo criterio en las tres
  referencias a pedidos de esa pantalla que mostraban el "(Nº...)": la
  tabla de coincidencias propuestas, la fila de "pendiente sin
  albarán" y el "posible candidato" de "pendiente sin pedido". El resto
  de la aplicación no se ha tocado — la petición era específica de esta
  herramienta.
- **Verificación**: `python3 -m py_compile app.py` y `node --check`
  sobre el JS extraído, ambos sin errores. Cambio de presentación
  únicamente.

## 2026-08-19 — [Control Pedidos] Comparar Pedidos + Albaranes: mensaje del "posible candidato" más claro y accionable (v12.30.12)

- Petición de Víctor, tras ver en pantalla el nuevo aviso de v12.30.11
  ("Posible candidato ya en la app... verificar importe manualmente"):
  pedía que el texto indicara que existe un pedido de fecha anterior que
  no se puede verificar sin un listado de pedidos de esa fecha (porque
  el importe registrado es distinto del importe recibido), y que
  invitara explícitamente a adjuntar un listado más completo o a
  verificarlo a mano — para que quede claro por qué sigue saliendo el
  aviso y qué hacer para que deje de salir.
- **Cambio en `app.py`**: nueva función `_motivo_sin_pedido(a)`
  (antes el texto estaba dentro de `_fila_sin_pedido`, sin reutilizar),
  con un mensaje que nombra el pedido candidato con su importe
  registrado en la app, explica que ese importe es solo la estimación
  con la que se dio de alta el pedido — no el importe realmente
  recibido según SAP — y termina con la instrucción concreta: adjuntar
  un listado de SAP que cubra esa fecha, o comprobarlo a mano,
  advirtiendo de que si no se hace ninguna de las dos cosas el aviso
  seguirá saliendo en todas las comparaciones futuras.
- **Cambio en `templates/index.html`**: misma redacción para el motivo
  mostrado en pantalla, incluyendo ahora también el importe registrado
  en la app del pedido candidato.
- **Verificación**: `python3 -m py_compile app.py` y `node --check`
  sobre el JS extraído, ambos sin errores. Cambio de texto únicamente,
  no toca el criterio de coincidencia de v12.30.11.

## 2026-08-19 — [Control Pedidos] Comparar Pedidos + Albaranes: la corrección anterior (v12.30.10) no resolvía el caso SISCOCAN/Nº618 — corregido el criterio de coincidencia (v12.30.11)

- Tras desplegar v12.30.10 (ver entrada de más abajo), Víctor volvió a
  lanzar la misma comparación con los mismos PDF y envió capturas del
  correo resultante: el albarán DALI 00082014 (SISCOCAN GRUPO COMERCIAL
  SL, 2.774,39 €) seguía en "Pendientes de realizar (10)", ya con el
  texto reformulado de v12.30.10 ("Sin ningún pedido Entregado/Parcial
  con ese importe...") pero SIN pasar al nuevo apartado "ya registrados
  en la app" que se había añadido. El texto nuevo confirmaba que el
  despliegue sí había llegado a producción, pero la lógica de v12.30.10
  no encontraba el pedido Nº618 como candidato — la corrección anterior
  era insuficiente.
- **Causa encontrada**: v12.30.10 comparaba el albarán contra los
  pedidos ya dados de alta en la base de datos usando la misma clave
  `(proveedor_id, importe)` que el cruce contra el PDF de SAP. Pero
  `pedidos.importe` es un importe introducido A MANO al dar de alta o
  editar el pedido — estimación/presupuesto usado para el techo de
  gastos mensual — y no tiene por qué coincidir con el importe
  realmente recibido según SAP (que solo se conoce leyendo un PDF de
  SAP recién subido). El pedido Nº618 en la BD tiene, con toda
  probabilidad, un `importe` distinto de 2.774,39 € (el importe
  base/estimado, no el recibido), así que la comparación exacta por
  importe daba 0 candidatos y el caso seguía cayendo en
  "pendientes_sin_pedido".
- **Corrección en `app.py`** (`_comparar_listado_albaranes_logica`): se
  sustituye la comparación exacta por importe contra la BD por un
  criterio más flojo pero fiable — mismo proveedor Y que el número de
  pedido de la app NO esté entre los vistos en el PDF de SAP recién
  subido (`vistos1`), es decir, que quede fuera del rango de fechas que
  cubre ese PDF (como el caso real del pedido Nº618). Si para un
  proveedor hay EXACTAMENTE UN pedido de la app en esa situación
  (Entregado o Entrega parcial), se adjunta como `posible_pedido_hint`
  al elemento correspondiente de `pendientes_sin_pedido` — sin sacarlo
  de la lista de pendientes (el importe no se puede verificar con este
  criterio, así que no se da por resuelto automáticamente) y sin
  aplicar ningún cambio: es solo una pista para la revisión manual. Se
  elimina el apartado independiente `ya_registrados_en_app` de
  v12.30.10 — con la nueva lógica ningún caso puede darse por
  "resuelto" con seguridad, así que ya no tiene sentido sacarlo de
  pendientes.
- **Cambio en `templates/index.html`**: se elimina la sección plegable
  "Ver albaranes de pedidos más antiguos ya registrados en la app"
  añadida en v12.30.10. La fila de "pendientes_sin_pedido" muestra
  ahora, cuando aplica, el motivo con la pista del posible pedido
  candidato.
- **Cambio en el correo** (`_email_resumen_comparacion_albaranes`): se
  elimina el bloque verde "📎 Albaranes de DALI de pedidos más
  antiguos, ya registrados en la app" de v12.30.10. El motivo de cada
  fila "sin pedido" en la tabla de pendientes incluye la pista de
  posible candidato cuando la hay.
- **Verificación**: `python3 -m py_compile app.py` y `node --check`
  sobre el JS extraído de `templates/index.html`, ambos sin errores. Se
  simuló el caso SISCOCAN/Nº618 con un script Python independiente
  (mismo algoritmo que el nuevo código, con `vistos1` sin el pedido 618
  y un único pedido ENTREGADO de ese proveedor en la "base de datos"
  simulada) y se confirmó que ahora sí se adjunta como
  `posible_pedido_hint`. Sin poder probar contra la base de datos real
  de producción desde este entorno — recomendado, de nuevo, volver a
  lanzar la misma comparación tras desplegar para confirmar en pantalla
  que la fila de SISCOCAN/00082014 menciona el pedido Nº618.

## 2026-08-19 — [Control Pedidos] Comparar Pedidos + Albaranes: "Sin pedido... en la app" salía aunque el pedido SÍ estuviera registrado y Entregado

- Aviso de Víctor, con capturas: la tabla "Pendientes de realizar" del
  correo de "Comparar listado PDF" (Pedidos + Albaranes) mostraba
  "Albarán DALI 00082014, SISCOCAN GRUPO COMERCIAL SL, 2.774,39 €, Sin
  pedido Entregado/Parcial con ese importe en la app" — pero el pedido
  Nº618 de ese proveedor SÍ está dado de alta y en estado ENTREGADO en
  la app (captura del listado de Pedidos filtrado por "SISCO"). Adjuntó
  también los dos PDF usados (`FV.pdf` listado de SAP, `FV2.pdf`
  listado de albaranes DALI) y el propio zip de la app en producción.
- **Causa encontrada**, tras leer `_comparar_listado_albaranes_logica()`
  (`app.py`) y extraer el texto real de los dos PDF con `pypdf`: el
  cruce solo comparaba el albarán de DALI contra los pedidos que
  aparecían en el PDF de SAP recién subido — nunca contra los pedidos
  ya dados de alta en la propia base de datos de la app. `FV.pdf` solo
  cubría pedidos desde el 28/07/2026 en adelante (SISCOCAN no aparece
  en ningún sitio del texto extraído), mientras que el pedido Nº618 se
  tramitó el 02/06/2026 — casi dos meses antes, fuera del rango de ese
  PDF concreto. Su albarán en DALI, en cambio, se registró el
  10/08/2026 (sí dentro del PDF de albaranes, importe exacto 2.774,3850
  €, confirmado en el texto de `FV2.pdf`). Como el pedido nunca podía
  aparecer como candidato del lado del PDF de SAP, el cruce lo daba por
  "sin pedido" — y el texto del mensaje ("...en la app") daba a
  entender, incorrectamente, que el pedido no estaba registrado en la
  aplicación, cuando el problema real era solo que no salía en ESE PDF.
- **Cambio en `app.py`**: antes de dar por "sin pedido" un albarán sin
  pareja en el PDF de SAP, se comprueba una segunda vez contra los
  pedidos ya dados de alta en la base de datos (mismo proveedor +
  mismo importe, entre los que están Entregado o Entrega parcial), sin
  depender de qué cubra el PDF de turno. Si hay exactamente un pedido
  de la app que cuadra, se saca de "pendientes_sin_pedido" y pasa a un
  nuevo apartado informativo, `ya_registrados_en_app` — no requiere
  ninguna acción. Si hay 0 o más de 1 candidato en la app, se deja tal
  cual pendiente (mismo criterio de "ante la duda, no inventar" que ya
  usa el resto de esta función para los empates). El texto de motivo
  para los que sigan quedando pendientes de verdad se reformula: "Sin
  ningún pedido Entregado/Parcial con ese importe (ni en el PDF de SAP
  ni ya dado de alta en la app)".
- **Cambio en `templates/index.html`**: nueva sección plegable "Ver
  albaranes de pedidos más antiguos ya registrados en la app", en
  verde, debajo de "pendientes de revisión manual" — oculta por
  completo cuando no aplica. Nueva "pill" en el resumen cuando hay
  alguno.
- **Cambio en el correo** (`_email_resumen_comparacion_albaranes`):
  nuevo bloque "📎 Albaranes de DALI de pedidos más antiguos, ya
  registrados en la app", en verde, con el pedido de la app al que
  corresponde cada uno.
- **Verificación**: `python3 -m py_compile app.py` y `node --check`
  sobre el JS extraído de `templates/index.html`, ambos sin errores. El
  hallazgo se confirmó leyendo el texto real de los PDF adjuntados
  (`pypdf`), no solo inspeccionando el código. Sin poder probar contra
  la base de datos real de producción desde este entorno — recomendado
  relanzar la misma comparación (mismos dos PDF) tras desplegar, para
  confirmar que el albarán 00082014/SISCOCAN pasa de "pendiente" a la
  nueva sección "ya registrados en la app".
- `README.md` y el badge de `templates/index.html` actualizados a
  v12.30.10.

---

## 2026-08-17 — [Control Pedidos] Ningún aviso automático (Telegram/popup) en fin de semana

- Petición de Víctor: "Control pedidos no debería enviar popup ni
  Telegram los findes de semana".
- **Hallazgo**: la mayoría de los jobs automáticos del scheduler
  (`_iniciar_scheduler()`, `app.py`) ya solo corrían lun-vie (alertas
  diarias de pedidos, techo urgente a admins, techo mensual, familia/
  partida repetida) — pero tres se habían quedado sin esa restricción y
  seguían disparando todos los días, sábado y domingo incluidos:
  - `health_check_diario` (07:05) — Telegram + popup bridge a admins si
    detecta problemas de configuración operativa.
  - `alerta_consumo_diaria` (08:30) — Telegram + popup bridge a admins
    si el consumo de Supabase (egress o tamaño de BD) se acerca o
    supera el límite del plan Free.
  - `recordar_emails_sistema_pendientes` (cada 10 min, 07:00-21:00) —
    Telegram con recordatorio si hay emails de sistema en cola sin
    despachar (p.ej. Fase 2 de solicitudes de acceso).
- **Cambio en `app.py`**: se añade `day_of_week="mon-fri"` a los tres
  `scheduler.add_job(...)`, mismo criterio ya usado en el resto de jobs
  de alertas — lo que caiga en fin de semana se retoma el lunes con
  normalidad. Los dos jobs puramente internos sin ningún canal de aviso
  (snapshot diario de tamaño de BD a las 08:10, migración de adjuntos
  cerrados a Storage a las 03:00) se dejan corriendo todos los días —
  no molestan a nadie y conservan el histórico completo aunque el
  AVISO de consumo de la mañana siguiente se retrase un par de días.
- **Verificación**: `python3 -m py_compile app.py` sin errores. Sin
  forma de probar el disparo real del scheduler en fin de semana desde
  este entorno (depende del reloj real del servidor en producción) —
  recomendado confirmar tras desplegar que estos tres jobs no aparecen
  en el log de Render de un sábado/domingo (buscar "[HEALTH]",
  "[CONSUMO]" o "[RECORDATORIO EMAILS SISTEMA]").
- `README.md` y el badge de versión de `templates/index.html`
  actualizados a v12.30.09 (el de `README.md` llevaba varias versiones
  desactualizado, se aprovecha para ponerlo al día).

---

## 2026-08-15 (2) — [Control Pedidos] Comparar Pedidos + Albaranes: el resultado y el correo son la unión de las dos comparaciones

- Continuación directa de la entrada anterior (hoy mismo, v12.30.07). Tras
  verla en pantalla, el usuario pidió: "si se realiza el trabajo con los 2
  PDF el resultado entregado deberá ser una unión de ambos, es decir, la
  información que lanza el primero mas la que lanza ambos, para enviar un
  único correo al comprador y admin" — señalando que, al marcar la
  casilla del segundo PDF, la tabla de auditoría del primer PDF (pedidos
  de SAP sin dar de alta en la app, o dados de alta pero sin ese estado de
  entrega) dejaba de verse por completo, sustituida solo por la sección
  de coincidencias con los albaranes — y que el correo final debía ser
  uno solo, no dos independientes.
- **Cambios en `app.py`**:
  - `_comparar_listado_albaranes_logica()` calcula ahora, además del
    cruce con los albaranes, la auditoría completa del PDF 1 —
    reutilizando tal cual `_comparar_listado_pdf_logica(hotel_id,
    pdf1_bytes)` sobre el mismo PDF 1 (releerlo y reanalizarlo tiene un
    coste asumible, es un job en segundo plano, y evita duplicar esa
    lógica) — y la añade al resultado devuelto como clave nueva
    `auditoria_pdf1`.
  - El endpoint `POST .../comparar-listado-albaranes/<job_id>/enviar-resumen`
    calcula a partir de `auditoria_pdf1` la misma lista de "pedidos sin
    dar de alta con proveedor identificado" que ya usaba el correo de un
    solo PDF (mismo filtro: solo proveedor identificado con certeza,
    igual criterio de fiabilidad que siempre), y aborta con error si las
    tres fuentes de contenido del correo (pedidos sin dar de alta,
    aplicados, pendientes) están vacías a la vez — no tiene sentido
    encolar un correo vacío.
  - `_email_resumen_comparacion_albaranes()` gana los parámetros
    `pedidos_faltantes`, `total_pdf1_audit`, `excluidos_pdf1_audit` y
    `no_identificados_audit`, y construye el correo con tres bloques en
    un único envío: 📋 pedidos de SAP sin dar de alta en la app (mismo
    formato de tabla que el correo de un solo PDF), ✅ registrados
    automáticamente y ⏳ pendientes de realizar (los dos ya existentes de
    v12.30.07). El asunto del correo pasa a incluir los tres recuentos.
- **Cambios en `templates/index.html`**: al terminar la comparación con
  los dos PDF (`_pollCompararListadoAlbaranes`, status `done`), además de
  la sección de coincidencias con albaranes se muestra también la tabla
  de auditoría completa del PDF 1 — reutilizando sin duplicar código la
  tabla/checkbox/función ya existentes de la comparación de un solo PDF
  (`_cmpPdfResultado`, `#cmp-pdf-resultado`, `_renderCompararPdfResultado()`),
  justo encima de la sección de albaranes. El botón de correo propio de
  esa tabla se oculta en este modo (`#cmp-pdf-btn-enviar-resumen`), para
  que solo quede un botón — el de la sección de albaranes, renombrado a
  "Enviar resumen por correo (pedidos + albaranes)" — que dispara el
  correo ya unificado en el backend.
- **Verificación**: `python3 -m py_compile app.py` y sintaxis de los
  bloques `<script>` de `templates/index.html` (extracción + `node
  --check`), ambos sin errores. Sigue sin probarse contra base de datos
  en vivo, igual que la entrada anterior.
- Versión: `V 12.30.07` → `V 12.30.08`.

## 2026-08-15 — [Control Pedidos] Comparar Pedidos + Albaranes: cruce automático propuesto con el listado de albaranes de DALI

- **Petición del usuario**: ampliar la comparación de listado PDF ya
  existente (Pedidos → Comparar listado PDF, que lee el "Listado de
  Pedidos" de SAP contra lo ya dado de alta en la app) para leer también
  un segundo PDF — el "Listado de Albaranes" que exporta DALI — y buscar
  similitudes entre ambos: el primero es un listado de pedidos, el
  segundo un listado de albaranes registrados en DALI en base a esos
  pedidos (columnas: nº registro DALI, nº registro + nº albarán
  proveedor, proveedor, fecha de registro, departamento del hotel,
  importe). La coincidencia a buscar es proveedor + importe del albarán
  contra proveedor + importe del pedido Entregado/Entrega parcial del
  primer listado; al coincidir, registrar en el pedido la fecha de
  tramitación (la del PDF 1), la fecha/nº de entrega (la del PDF 2) y el
  estado automático según el resultado; en el correo final indicar los
  registros hechos automáticamente y los pendientes de hacer; usar
  siempre solo proveedores sujetos a seguimiento, en ambos PDF. Se
  adjuntaron dos PDF de muestra (GY.pdf con el formato ya soportado,
  GY2.pdf con el formato nuevo de albaranes).
- **Decisiones acordadas con el usuario antes de implementar** (vía
  pregunta de aclaración, por tratarse de escritura automática sobre
  datos de producción — las cuatro respuestas fueron la opción
  recomendada):
  1. El importe a cruzar del PDF 1 es el **recibido** (no el
     base/total) de cada pedido Entregado/Entrega parcial.
  2. Ninguna coincidencia se aplica sola: siempre hay que **revisar y
     confirmar** en pantalla antes de escribir nada en la base de datos.
  3. La fecha de tramitación del PDF 1 **solo se rellena si el pedido no
     tiene ya una guardada** — nunca sobrescribe una existente.
  4. Si un mismo proveedor + importe encaja con más de una pareja
     posible (ambigüedad en cualquiera de los dos lados), **todas esas
     parejas van a una lista de pendientes de revisión manual** — nunca
     se adivina cuál es la correcta.
- **Formato del segundo PDF (albaranes DALI)** — reto principal: pypdf
  extrae el texto en el orden del flujo interno del PDF, no en el orden
  visual de las columnas, y varios campos llegan pegados sin separador
  (importe→fecha, departamento→nombre de proveedor). Se resolvió con un
  patrón de expresión regular nuevo (`_PATRON_LISTADO_ALBARANES`, con
  `re.S` para tolerar saltos de línea dentro de un mismo campo),
  validado **265/265** líneas contra el PDF de muestra real. El
  departamento (pegado al proveedor sin separador) se identifica tratando
  los nombres de departamento como catálogo cerrado y comprobando cuál de
  ellos es *prefijo* del texto combinado (`_match_departamento_prefijo`);
  lo que sobra tras quitar ese prefijo se trata como nombre de proveedor
  y se cruza contra el catálogo de `proveedores` con el mismo
  emparejamiento por normalización ya usado en la comparación de un solo
  PDF (`_match_proveedor_catalogo`, extraído a nivel de módulo para
  reutilizarlo). El importe con 4 decimales que aparece a veces en este
  formato ("8.350,8600") no necesitó parser nuevo: `_parse_importe_es`
  (sin tocar) ya lo interpreta bien al solo intercambiar separadores
  antes de `float()`.
- **Cambios en `app.py`**:
  - `_comparar_listado_albaranes_logica(hotel_id, pdf1_bytes, pdf2_bytes)`:
    lógica pura (sin escritura en BD) que lee ambos PDF, filtra por
    `sujeto_seguimiento` en los dos lados, agrupa por
    `(proveedor_id, importe redondeado a 2 decimales)` y reparte el
    resultado en `coincidencias` (pareja única 1↔1), `pendientes_ambiguos`
    (más de una pareja posible en cualquier lado), `pendientes_sin_albaran`
    (pedido Entregado/Parcial en SAP sin albarán DALI que encaje en
    importe) y `pendientes_sin_pedido` (albarán DALI sin pedido que
    encaje) — reparto exhaustivo y sin solapes en un único bucle sobre
    las claves de ambos grupos, para no contar nada dos veces. Pedidos en
    estado `CANCELADO`/`DENEGADO POR DIRECCION GENERAL` quedan siempre
    excluidos de la escritura automática.
  - `_aplicar_coincidencia_albaran(db, coincidencia, usuario_id, usuario_nombre)`:
    aplica una coincidencia ya confirmada por el admin, de forma
    idempotente — vuelve a leer el pedido fresco de BD, rellena
    `fecha_tramitacion` solo si estaba vacía, añade el número de albarán
    a `entrada_albaran_num` (formato `"NUM::FECHA"`, mismo que ya usa la
    edición manual) solo si no estaba ya presente, y sube el `estado`
    solo si supone avanzar (nunca lo retrocede, vía un orden explícito
    ENVIADO AL PROVEEDOR/PENDIENTE COTIZACIÓN < ENTREGA PARCIAL <
    ENTREGADO). Si no hay nada que cambiar, no escribe ni notifica y lo
    indica en la respuesta. Si el estado sí cambia, llama a
    `_notificar_cambio_estado()` — la misma función que ya usa el resto
    de la app — así el email y el popup de este cambio automático
    heredan sin código adicional el retraso de 5 minutos y la
    antirrepetición recién implementados (v12.30.05/06).
  - Tres endpoints nuevos, solo para `admin`, con el mismo patrón de job
    en segundo plano (`threading.Thread` + diccionario `_PDF_JOBS`) y
    sondeo corto desde el frontend que ya usaba la comparación de un
    único PDF, para no toparse con timeouts de proxy en listados
    grandes: `POST /api/pedidos/comparar-listado-albaranes` (arranca el
    job, recibe los dos ficheros por `multipart/form-data`), `GET
    .../comparar-listado-albaranes/<job_id>` (sondeo de estado/resultado),
    `POST .../<job_id>/aplicar` (aplica una o varias coincidencias
    confirmadas, `{"claves": [...]}` o `{"todas": true}`, devuelve
    `aplicadas`/`sin_cambios`/`errores`) y `POST
    .../<job_id>/enviar-resumen` (correo con lo aplicado en la sesión —
    acumulado en el propio job entre llamadas a `/aplicar` — y lo que
    sigue pendiente, encolado vía `_encolar_email_sistema`, mismo
    mecanismo sin SMTP propio que el resto de correos internos).
- **Cambios en `templates/index.html`**: el modal "Comparar listado PDF"
  gana una casilla opcional "+ Comparar también con el listado de
  Albaranes registrados en DALI" que revela un segundo selector de
  fichero; al marcarla, `compararListadoPdf()` llama al endpoint nuevo en
  vez del de siempre y el resultado se muestra en una sección aparte
  (`_pollCompararListadoAlbaranes` / `_renderCompararAlbaranesResultado`):
  tabla de coincidencias propuestas con casilla de selección por fila y
  botón "Aplicar" individual, botón para aplicar de golpe todas las
  seleccionadas (`aplicarCoincidenciasAlbaranes`), lista plegable de
  pendientes de revisión manual agrupando los tres tipos
  (`_togglePendientesAlbaran`) y botón de correo resumen
  (`enviarResumenComparacionAlbaranes`, mismo patrón de despacho
  inmediato de la cola que el resto de acciones de envío manual de esta
  app).
- **Verificación**: `python3 -m py_compile app.py` sin errores tras cada
  edición. Sintaxis de los bloques `<script>` de `templates/index.html`
  comprobada extrayéndolos y pasándolos por `node --check` (no hay
  linter de JS embebido disponible en este entorno) — sin errores. El
  patrón de lectura del PDF de albaranes se validó aparte, por script
  independiente, contra el listado de muestra real (265/265 filas). **Sin
  probar contra base de datos en vivo** — este entorno no tiene acceso a
  una; queda pendiente de una prueba real en producción con hotel,
  catálogo de proveedores/departamentos y un listado de albaranes real
  antes de darlo por cerrado del todo.
- Versión: `V 12.30.06` → `V 12.30.07`.

## 2026-08-14 13:45 — [Control Pedidos] Correo de cambio de estado: mismo retraso de 5 minutos y antirrepetición que el popup

- Continuación directa de la entrada anterior (`2026-08-14 13:00`, popup).
  El usuario preguntó "tambien llegan correos electronicos de aviso
  inmediatos con el cambio de estado?" — respuesta: sí, y de forma aún
  más inmediata que el popup (se enviaban directamente desde el
  navegador de quien guardaba el pedido, sin ninguna cola de servidor de
  por medio, vía EmailJS en el frontend). Con "si por favor" pidió
  aplicar la misma protección de 5 minutos / solo-el-último-cambio.
- **Diferencia clave frente al popup**: el popup ya vivía en una cola
  "pull" en base de datos (`bridge_notificaciones`) que el Organizador
  sondea, así que el retraso se implementó con una columna `visible_en`.
  El correo, en cambio, se devolvía en la respuesta JSON de
  `PUT /api/pedidos/<id>` y el frontend lo enviaba de inmediato vía
  EmailJS — no había ninguna cola de la que tirar. Se decidió (en vez de
  construir una cola nueva desde cero) reutilizar
  `emails_sistema_pendientes`, una cola ya existente en esta misma app
  para correos generados por jobs sin navegador abierto (techo urgente,
  familias repetidas, solicitudes de acceso...), con su propio poller de
  5 minutos ya funcionando en el frontend
  (`_enviarEmailsSistemaPendientes`) y su propia reserva atómica
  anti-duplicados (`en_proceso_desde`, v12.29.96) — evita reinventar esa
  infraestructura.
- **Cambios en `app.py`**:
  - `emails_sistema_pendientes` gana la columna `visible_en`
    (`TIMESTAMPTZ NOT NULL DEFAULT NOW()`) — por defecto inmediata,
    compatible con el resto de eventos de esa cola.
  - Función nueva `_encolar_email_pedido_retrasado()`: inserta (o
    sobrescribe, si ya hay uno sin enviar/sin reservar para el mismo
    pedido + tipo de correo) una fila con `visible_en = NOW() + 5min`.
  - `enviar_emails_estado()` ya no construye una lista para devolver:
    llama a `_encolar_email_pedido_retrasado()` para el correo al
    proveedor (`evento_codigo='cambio_estado_proveedor'`) y para el
    interno (`evento_codigo='cambio_estado_interno'`, con el resto de
    compradores/hotel en `cc_emails`). Sigue devolviendo `[]` por
    compatibilidad con los callers (`create_pedido`/`update_pedido`),
    que lo incluyen en su respuesta JSON como `emails_pendientes`.
  - `GET /api/emails-sistema-pendientes` añade `AND visible_en <= NOW()`
    a la reserva atómica — mismo patrón que el filtro añadido al bridge
    de popups.
- **Cambios en `templates/index.html`**: comentario actualizado en
  `_enviarEmailsPendientesEstado()` (ahora en desuso — se deja la
  función y sus llamadas tal cual, inofensivas, para no tocar
  `savePedido()` sin necesidad) y en el poller de `emails_sistema_
  pendientes`, documentando que también despacha estos dos eventos
  nuevos.
- **Aviso trasladado al usuario** (no es un bug, es una consecuencia del
  diseño elegido): el despacho de esta cola solo lo hacen sesiones
  `admin`/`compras` con la app abierta (`_startEmailsSistemaPolling()`
  nunca se llama para rol `hotel` — así ha sido siempre para el resto de
  correos de esta cola). Antes, el envío inmediato salía desde
  cualquier sesión, incluida una de rol `hotel` actualizando un
  albarán. Cubierto por el job de recordatorio ya existente
  (`_job_recordar_emails_sistema_pendientes`, cada 10 min en 07–21h),
  que avisa por Telegram a admins si la cola lleva más de 10 min sin
  despacharse — se aplica automáticamente también a estos dos eventos
  nuevos, sin cambios adicionales.
- Versión: `V 12.30.06` (badge en `templates/index.html`),
  `CHANGELOG.md` actualizado con la misma entrada.
- Verificación: `python3 -m py_compile app.py` sin errores. Pendiente de
  confirmación del usuario en producción: cambiar de estado un pedido a
  `ENVIADO AL PROVEEDOR` (o `ENTREGA PARCIAL`/`ENTREGADO`/`CANCELADO`) y
  comprobar que el correo llega una única vez, hasta 5 + 5 minutos
  después (5 de espera + hasta 5 de margen del siguiente sondeo del
  poller), y no antes; revisar también que el remitente/"responder a"
  del correo al proveedor sigue funcionando igual que antes (mismo
  valor, `p.destinatario`, pero ahora viaja como `reply_to` en vez de
  `email` en el payload de EmailJS — mismo patrón que el resto de la
  cola, no debería cambiar nada, pero conviene confirmarlo con un envío
  real).

## 2026-08-14 13:00 — [Control Pedidos] Popup de cambio de estado: antirrepetición con espera de 5 minutos

- Petición del usuario (Víctor): "vamos a modificar los envios de popup
  ... cada vez que se realiza un cambio de estado en los pedidos, se
  envia un popup automatico, para evitar que se envien repeticiones
  automaticas debido a errores en cambios de pedidos, podemos
  relentizar el envio a 5 minutos, realizando unicamente el envio del
  ultimo cambio realizado en el pedido entendiendo que es el unico y
  final?"
- **Alcance**: el popup entregado al Organizador (main_agenda) vía la
  cola `bridge_notificaciones` (`GET /api/bridge/notificaciones`),
  específicamente el de tipo `cambio_estado` (evento
  `cambio_estado_pedido`, disparado desde `_telegram_cambio_estado()`
  en cada `PUT /api/pedidos/<id>` que cambia el estado). El Telegram de
  ese mismo evento **no se ha tocado** — el usuario pidió explícitamente
  solo el popup, y ambos canales ya eran independientes entre sí desde
  v12.17.0.
- **Diseño**: la cola `bridge_notificaciones` es de tipo "pull" — el
  Organizador la consume sondeando `GET /api/bridge/notificaciones`, que
  devuelve las filas no leídas y las marca leídas en el momento. Eso
  permite implementar el retraso sin ningún planificador/cron nuevo:
  basta con que una fila no sea "visible" hasta que corresponda.
  - Columna nueva `bridge_notificaciones.visible_en` (`TIMESTAMPTZ NOT
    NULL DEFAULT NOW()`) — por defecto inmediata (compatible con el
    resto de tipos de popup, que no cambian).
  - `_encolar_bridge_notificacion()` (`app.py`) gana el parámetro
    `retraso_segundos`; para `cambio_estado` se llama con
    `retraso_segundos=300`.
  - Con `retraso_segundos>0`: si ya existe un aviso sin leer para el
    mismo `(usuario, tipo, pedido_id)`, se SOBRESCRIBE su contenido y se
    reinicia `visible_en = NOW() + 5min`, en vez de insertar una fila
    nueva — así, varias correcciones seguidas sobre el mismo pedido
    dentro de esa ventana colapsan en un único popup, con el contenido
    del último cambio. Si no hay ninguno pendiente, se inserta uno
    nuevo con `visible_en = NOW() + 5min`.
  - `GET /api/bridge/notificaciones` añade `AND visible_en <= NOW()` al
    filtro — una fila con `visible_en` en el futuro simplemente no se
    devuelve todavía (ni se marca leída), así que reaparece sondeo tras
    sondeo hasta que el plazo se cumple.
- **Base de datos**: la columna se añade automáticamente al arrancar
  (`_auto_migrate()`, tanto en el `CREATE TABLE IF NOT EXISTS` para
  instalaciones nuevas como en un `ALTER TABLE ADD COLUMN IF NOT
  EXISTS` explícito para la base de datos ya existente en producción)
  — sin ninguna acción manual en Supabase, a diferencia de los cambios
  recientes en DALI.
- Versión: `V 12.30.05` (badge en `templates/index.html`),
  `CHANGELOG.md` actualizado con la misma entrada.
- Verificación: `python3 -m py_compile app.py` sin errores. Pendiente
  de confirmación del usuario en producción: cambiar de estado el mismo
  pedido dos o tres veces seguidas (en menos de 5 min) y comprobar que
  el Organizador recibe un único popup, con el último estado, pasados
  los 5 minutos desde el último cambio — y que un cambio de estado
  aislado (sin repetición) también llega con normalidad, solo que 5
  minutos más tarde que antes.

## 2026-08-14 12:15 — [Control Pedidos] Implementado: correo a proveedor ya no duplica el aviso interno

- Implementa lo pedido en la entrada anterior ("PENDIENTE — Correo a
  proveedor en 'ENVIADO AL PROVEEDOR' duplica aviso a comprador/hotel",
  ver más abajo) a petición del usuario ("podemos realizar las
  operacion pendientes en control_pedidos?").
- **Cambio en `app.py`** (`enviar_emails_estado()`): quitada la clave
  `"bcc": _todos_internos` del `pendientes.append({...})` del bloque
  "Correo al proveedor" (~línea 1930) — ese correo pasa a enviarse
  única y exclusivamente a los contactos del proveedor. Actualizado el
  comentario de ese bloque (~línea 1860) y el del bloque "Correo
  interno" (~línea 1936) para que ambos describan correctamente el
  comportamiento real: el correo interno (a compradores + usuarios
  hotel) es ahora el único que informa a los internos del cambio a
  `ENVIADO AL PROVEEDOR`, sin duplicado.
- No fue necesario tocar `_log_email` ni el consumo en frontend: el
  `bcc` en el JSON que arma el backend ya se trataba como opcional en
  `templates/index.html` (`(p.bcc || []).join(',') || ''`, ~línea
  5078), así que quitar la clave no rompe el envío vía EmailJS —
  simplemente no añade destinatarios en copia oculta.
- Sin cambios en el resto de estados (`ENTREGA PARCIAL`, `ENTREGADO`,
  `CANCELADO`, `DENEGADO POR DIRECCION GENERAL`): esos correos internos
  nunca llevaron ese BCC duplicado, el problema era exclusivo de
  `ENVIADO AL PROVEEDOR`.
- Versión: `V 12.30.04` (badge en `templates/index.html`),
  `CHANGELOG.md` actualizado con la misma entrada.
- Verificación: `python3 -m py_compile app.py` sin errores. Pendiente
  de que el usuario confirme en producción tras el próximo despliegue
  (pasar un pedido real a `ENVIADO AL PROVEEDOR` y comprobar que
  comprador/hotel reciben el aviso una sola vez, vía el correo
  interno, y que el proveedor recibe el suyo sin BCC).

## 2026-08-14 (pendiente — ya implementado, ver entrada de arriba 2026-08-14 12:15)

### [Control Pedidos] PENDIENTE — Correo a proveedor en "ENVIADO AL PROVEEDOR" duplica aviso a comprador/hotel
- **Reportado por el usuario (Víctor), como recordatorio de trabajo
  pendiente — no implementado en esta entrada** (implementado después,
  ver la entrada `2026-08-14 12:15` arriba).
- Comportamiento actual (`app.py`, función que envía los correos al
  cambiar de estado, ~línea 1853 en adelante): cuando un pedido pasa a
  `ENVIADO AL PROVEEDOR` se disparan **dos** correos:
  1. Correo al proveedor (bloque `## Correo al proveedor`, ~línea
     1860): para los contactos del proveedor, **con BCC a
     `_todos_internos`** (compradores + usuarios hotel del hotel, línea
     ~1930).
  2. Correo interno de cambio de estado (bloque `## Correo interno`,
     ~línea 1936): para el primer comprador, BCC al resto de
     compradores + usuarios hotel — `ESTADOS_EMAIL_INTERNO` incluye
     `ENVIADO AL PROVEEDOR`.
- El propio comentario del código en el bloque 1 (línea ~1863: "NO se
  envía correo interno adicional para este estado — el BCC ya cubre a
  todos los internos sin duplicar") **ya no es cierto** respecto al
  comportamiento real: el comentario del bloque 2 (línea ~1939) lo
  contradice explícitamente ("para ENVIADO AL PROVEEDOR este correo
  interno se manda ADEMÁS del correo al proveedor de arriba") — es
  decir, el código evolucionó y quedó un comentario desactualizado
  justo donde describe lo contrario de lo que pasa. Resultado: comprador
  y hotel reciben el aviso de "enviado al proveedor" **dos veces**
  (una vía BCC del correo al proveedor, otra vía el correo interno
  dedicado), con el mismo pedido e información.
- **Corrección pedida por el usuario**: el correo al proveedor debe
  enviarse **únicamente al proveedor** (quitar el BCC a
  `_todos_internos` en ese bloque, ~línea 1930) — el correo interno ya
  informa a comprador y hotel, así que no hace falta duplicar.
- **Dónde tocar cuando se implemente**: quitar o vaciar la clave
  `"bcc": _todos_internos` del diccionario `pendientes.append({...})`
  del bloque "Correo al proveedor" (~línea 1930), y actualizar el
  comentario de ese bloque (~línea 1863) para que refleje el
  comportamiento real ya existente del bloque de correo interno (que
  no cambia). Revisar también si `_log_email` (~línea 1926) o algún
  resumen/exportación depende de que ese correo lleve BCC.
- Sin cambios de código en esta entrada — queda solo como recordatorio
  para una próxima entrega.

## 2026-08-14 11:35

### [Control Pedidos + DALI] v12.30.02/v12.30.03 (Control Pedidos) — Integración: acceso SSO de un clic al catálogo DALI desde el menú lateral y el Dashboard
- Petición del usuario (Víctor): que cualquier usuario de Control de
  Pedidos (admin, compras u hotel) pudiera acceder a la nueva app
  DALI (`dali-sap-articulos-app`, hasta ahora un proyecto aparte, sin
  ninguna relación operativa con este) desde el dashboard o el menú
  lateral, con los usuarios ya dados de alta allí automáticamente y
  con rol comprador → administrador en DALI, rol hotel → mismo rol
  (hotel, de solo consulta) en DALI.
- Diseño elegido, de entre tres opciones planteadas (SSO transparente /
  cuentas sincronizadas con login propio / solo enlace sin sincronizar):
  **SSO transparente por token firmado entre los dos backends** — el
  usuario nunca ve el login de DALI. Encajaba bien porque los dos
  proyectos ya comparten el mismo patrón de sesión (cookie firmada, sin
  store de servidor) — de hecho DALI documentó en su día
  (`docs/hallazgo-seguridad-princess.md`) que copió ese patrón de este
  mismo proyecto.
- **Cambios en Control Pedidos** (`app.py`): `DALI_SSO_SECRET` /
  `DALI_FRONTEND_URL` / `DALI_ROL_MAP` (`admin`→`admin`,
  `compras`→`admin`, `hotel`→`hotel`), función
  `_generar_token_sso_dali()` (HMAC-SHA256, token de un solo uso,
  ~60s de validez), endpoint `GET /api/dali/sso`
  (`@login_required`, devuelve la URL con el token o un error claro si
  el usuario no tiene email registrado — DALI identifica por email).
  `templates/index.html`: ítem "🧾 Catálogo DALI" en el menú lateral y
  tarjeta de acceso rápido en el Dashboard (rediseñada en v12.30.03 a
  petición del usuario: icono en círculo, fondo degradado navy/dorado,
  sin mencionar el detalle de usuario/contraseña), función JS
  `abrirDali()`. `render.yaml`: variables `DALI_SSO_SECRET` /
  `DALI_FRONTEND_URL`.
- **Cambios en DALI** (repo aparte, no incluido en este historial
  unificado salvo este resumen — ver su propio `HISTORIAL.md`):
  `POST /auth/sso` (`authController.js`) verifica la firma y caducidad
  del token, aprovisiona o actualiza el usuario en su tabla `usuarios`
  con el rol recibido, y abre sesión. En el frontend, `App.jsx` detecta
  `?dali_token=` al cargar y llama a ese endpoint en vez de mostrar el
  login; si falla, cae al login normal explicando el motivo.
- **Verificación:** `python3 -m py_compile app.py` sin errores;
  `node --check` sobre los ficheros JS tocados del backend de DALI sin
  errores; JSX comprobado con `esbuild` (sin bundlear) sin errores.
  Probado en producción por el usuario con los tres roles reales tras
  desplegar y configurar `DALI_SSO_SECRET` en ambos servicios de
  Render: admin → admin ✅, compras → admin ✅, hotel → hotel ✅.
- Pendiente/a vigilar: la organización de Supabase
  (`controlpedidosprincesscanarias-coder's Org`) está en "grace period"
  por cuota del plan Free (Fair Use Policy) — no bloquea lo de hoy
  (este proyecto va holgado en su propio uso), pero conviene que el
  usuario revise qué proyecto de la org la está agotando antes de que
  algo empiece a devolver 402. Fuera del alcance de este cambio.
- Sin cambios en `README.md` de Control Pedidos (no documenta
  integraciones externas de este tipo); badge de versión actualizado a
  "V 12.30.02" en v12.30.02.

## 2026-08-14 09:40

### [Control Pedidos] v12.30.00 — Columna "Entrega": ahora es "Entregado" si el importe recibido es igual O SUPERIOR a la base (antes exigía igualdad exacta)
- Petición del usuario: precisar la regla de la columna "Entrega" —
  "entrega completa es cuando columna 7 => 6; entrega parcial cuando
  7 >0 y <6; no entregado 7 = 0" (columna 6 = base imponible, columna 7
  = importe recibido, listado simplificado de SAP).
- Antes (`_entrega_estado`): "Entregado" exigía columna 7 == columna 6
  exacto — si el importe recibido superaba ligeramente a la base
  (recargos, ajustes, redondeos…), el pedido quedaba mal clasificado
  como "Entrega parcial" aunque ya estaba completo.
- Ahora: columna 7 ≥ columna 6 → "Entregado"; 0 < columna 7 < columna 6
  → "Entrega parcial"; columna 7 ≤ 0 → "No entregado" (un importe
  recibido negativo, dato anómalo, se trata también como "No
  entregado"). Afecta a la columna "Entrega" en pantalla, al recuento
  de entregados/parciales/no entregados y al correo de resumen.
- Verificación: `python3 -m py_compile app.py` sin errores. Reprocesados
  los 2 PDF reales disponibles comparando regla antigua vs. nueva: PDF
  de La Palma Princess (199 pedidos) — 13 pedidos pasan de "Entrega
  parcial" a "Entregado" (recuento total: antes 35/36, ahora 48/23, los
  128 "No entregado" no cambian); listado simplificado de 221 pedidos —
  38 pedidos cambian igual (antes 66/57, ahora 104/19, los 98 "No
  entregado" no cambian).
- Sin cambios en `templates/index.html` más allá del badge de versión
  (la columna "Entrega" ya se pinta con el valor de `_entrega_estado()`,
  sin lógica propia en el frontend). Badge del sidebar actualizado a
  "V 12.30.00"; entrada añadida en `CHANGELOG.md`; `README.md`
  actualizado.

## 2026-08-14 09:10

### [Control Pedidos] v12.29.98 — "Estado aparente" del correo de "Comparar listado PDF": nuevo caso "SIN ENTREGAR" (antes se confundía con "ENTREGA PARCIAL")
- Reporte del usuario: en el correo de pedidos de SAP/DALI sin dar de
  alta (hotel La Palma Princess, PDF adjunto), 4 pedidos salían con
  "Estado aparente: ENTREGA PARCIAL" y a la vez columna "Entrega: No
  entregado" — parecía contradictorio.
- Diagnóstico: comprobado con el propio PDF adjunto (pedidos 00016080,
  00016147, 00016165, 00016171) — los 4 tienen importe recibido = 0,00
  (nada recibido todavía) e importe pendiente = importe base completo.
  No es contradictorio: son dos columnas independientes a propósito
  ("Entrega" compara base vs. recibido; "Estado aparente" mira solo si
  la columna 8 del SAP, importe pendiente, es > 0). El problema es que
  esa regla era binaria y no distinguía "no ha llegado nada todavía" de
  "ya llegó una parte" — ambos casos tienen importe pendiente > 0, así
  que ambos salían como "ENTREGA PARCIAL".
- Ajuste, a petición del usuario ("ajustar lógica"): `_estado_aparente_entrega()`
  pasa a mirar también el importe recibido (columna 7, dato en bruto,
  no un cálculo) y distingue 3 casos: pendiente ≤ 0 → ENTREGA COMPLETA
  (igual que antes); pendiente > 0 y recibido ≤ 0 → SIN ENTREGAR
  (nuevo); pendiente > 0 y recibido > 0 → ENTREGA PARCIAL (reservado
  ahora a cuando de verdad ha llegado algo pero falta el resto).
  Actualizado el color del correo (rojo oscuro / ámbar / verde) y el
  texto explicativo bajo la tabla.
- Verificación: `python3 -m py_compile app.py` sin errores; `node
  --check` sobre el JS del frontend sin errores (sin cambios de
  frontend — el campo solo se usa en el correo). Reprocesados los 2 PDF
  reales disponibles: el PDF reportado (199 pedidos) — los 4 pedidos
  del correo pasan de "ENTREGA PARCIAL" a "SIN ENTREGAR" confirmado con
  los importes reales (recibido=0,00 en los 4), recuento total 128 SIN
  ENTREGAR / 23 ENTREGA PARCIAL / 48 ENTREGA COMPLETA; y el listado
  simplificado de 221 pedidos usado en entregas anteriores, que sigue
  parseando sin errores (97 / 19 / 105).
- Badge de versión del sidebar actualizado a "V 12.29.98"; entrada
  añadida en `CHANGELOG.md`; `README.md` actualizado.

## 2026-08-13 08:15

### [Control Pedidos] v12.29.96 — Fix: correos de la cola de sistema duplicados por carrera (race condition) entre pestañas/sesiones
- Reporte del usuario: el pedido Nº 39909 (reclamación automática por
  "Entrega parcial pendiente de completar") llegó DOS veces idénticas a
  la bandeja de entrada del admin, y aparece dos veces en "Enviados" de
  Gmail, ambas a las 7:43 — con capturas del panel de alertas, la
  bandeja de entrada, "Enviados" de Gmail, y un fragmento de logs de
  Render de ese minuto.
- Investigación: la reclamación automática al proveedor
  (`_encolar_reclamacion_proveedor_auto`, dentro del job diario de
  alertas) ya tiene buena protección contra insertar la fila dos veces
  el mismo día (`_ya_notificado_hoy` + comprobación final de seguridad)
  — descartado que el problema esté en el encolado.
- Problema real, en el despacho de la cola
  (`emails_sistema_pendientes`): `_enviarEmailsSistemaPendientes()`
  (frontend) hacía `GET /api/emails-sistema-pendientes` (lista filas
  `enviado=FALSE`), enviaba de verdad por EmailJS, y solo DESPUÉS
  marcaba la fila como enviada con `POST .../marcar-enviado` — sin
  ningún bloqueo entre ambos pasos. Si dos pestañas/sesiones (dos
  usuarios admin/compras, o una recarga de página mientras el ciclo de
  5 minutos ya estaba en marcha) pedían la cola casi a la vez, ambas
  veían la misma fila pendiente y ambas la mandaban de verdad por
  EmailJS antes de que ninguna la marcara — dos correos reales por un
  solo aviso. Posible porque el servidor corre con varios hilos
  (`render.yaml`: `--worker-class gthread --threads 4`), procesando dos
  peticiones en paralelo de verdad dentro del mismo proceso.
- Corrección: `GET /api/emails-sistema-pendientes` ahora RESERVA
  atómicamente las filas que devuelve, en una sola sentencia SQL
  (`UPDATE ... SELECT ... FOR UPDATE SKIP LOCKED ... RETURNING`),
  marcando `en_proceso_desde = NOW()`. Una segunda petición concurrente
  ya no ve esas filas como disponibles (se excluyen las reservadas hace
  menos de 2 minutos) y con `SKIP LOCKED` no espera bloqueada a que la
  primera termine. Si una sesión reserva una fila y nunca confirma el
  envío (falla EmailJS, se cierra la pestaña a media faena…), la
  reserva caduca sola a los 2 minutos y otra sesión puede reintentarla,
  sin perder ningún envío. Nueva columna
  `emails_sistema_pendientes.en_proceso_desde` (migración idempotente
  en `_auto_migrate()`).
- Verificación: `python3 -m py_compile app.py` sin errores. Reproducido
  el bug y la corrección con un PostgreSQL real (no simulado): dos
  "sesiones" en hilos separados pidiendo la cola en el mismo instante —
  con el SQL antiguo (`SELECT` simple) ambas ven y "envían" la misma
  fila (duplicado reproducido tal cual lo reportó el usuario); con el
  SQL nuevo (`UPDATE ... FOR UPDATE SKIP LOCKED`) solo una de las dos la
  reclama. Verificada también la caducidad de la reserva (3 min → vuelve
  a ser reclamable; 0 min → no lo es; ya `enviado=TRUE` → nunca
  reaparece).
- Sin cambios necesarios en `templates/index.html` (el frontend ya
  hacía correctamente GET → enviar → marcar-enviado; el fix es
  enteramente del lado del servidor). Badge de versión del sidebar
  actualizado a "V 12.29.96"; entrada añadida en `CHANGELOG.md`;
  `README.md` actualizado.

## 2026-08-12 09:40

### [Control Pedidos] v12.29.94 — Tercera cuenta EmailJS de backup: rotación cíclica entre 3 cuentas (1→2→3→1)
- Petición del usuario: con la v12.29.92 ya desplegada, incorporar una
  tercera cuenta EmailJS ("Cuenta1 (principal)", "Cuenta2 (secundaria)",
  "Cuenta3 (backup)") y que el sistema salte automáticamente de una a
  otra en cuanto se consuman los envíos establecidos por cuenta.
- Backend (`app.py`): `_auto_migrate()` → `_emailjs_defaults` ampliado
  con 3 filas nuevas (`emailjs_public_key_3`, `emailjs_service_id_3`,
  `emailjs_template_id_3`), etiquetas de las cuentas 1/2 renombradas a
  "(principal)"/"(secundaria)" (inserción idempotente vía `ON CONFLICT
  (clave) DO NOTHING`, no toca instalaciones ya desplegadas salvo para
  añadir las 3 claves nuevas); `get_config()` con las 3 claves nuevas en
  los valores por defecto.
- Nuevas constantes/helpers: `_EMAILJS_MAX_CUENTAS = 3`,
  `_emailjs_cuenta_valida(valor)` (normaliza a un entero 1–3, con 1 como
  valor por defecto ante datos corruptos o fuera de rango) y
  `_emailjs_siguiente_cuenta(activa)` (siguiente cuenta del ciclo, 3→1
  incluido).
- `GET /api/emailjs/config` → usa `_emailjs_cuenta_valida()` en vez del
  antiguo recorte binario (1 o 2).
- `POST /api/emailjs/registrar-envio` → sustituido el cambio
  BIDIRECCIONAL (1⇄2) por uno CÍCLICO: al llegar al umbral, se busca la
  siguiente cuenta del ciclo (1→2→3→1) que tenga las 3 credenciales
  completas, probando hasta las 3 antes de rendirse; si ninguna otra
  cuenta está completa, no cambia (igual que antes) y queda aviso en
  Integridad.
- Admin → Integridad (comprobación EmailJS) → generalizada de "la otra
  cuenta" a "la siguiente cuenta del ciclo", y el aviso de "umbral
  alcanzado sin backup" ahora comprueba las 2 cuentas restantes (no solo
  la inmediatamente siguiente).
- Frontend (`templates/index.html`): tarjeta de administración de
  EmailJS (Config alertas) ampliada de 2 a 3 paneles de cuenta ("Cuenta
  1 (principal)" / "Cuenta 2 (secundaria)" / "Cuenta 3 (backup)"), campo
  "Cuenta activa" ahora acepta 1–3, texto explicativo actualizado para
  describir el ciclo de 3 cuentas.
- Verificación: `python3 -m py_compile app.py` sin errores; `node
  --check` sobre los bloques `<script>` extraídos de
  `templates/index.html` sin errores; lógica de rotación cíclica
  verificada en un script aislado (ciclo completo 1→2→3→1 con las 3
  cuentas completas, salto correcto de 1 directamente a 3 cuando la
  cuenta 2 no tiene credenciales, sin cambio cuando solo la cuenta
  activa está completa, y `_emailjs_cuenta_valida` recortando
  correctamente valores fuera de rango o inválidos).
- Badge de versión del sidebar actualizado a "V 12.29.94"; entrada
  añadida en `CHANGELOG.md`; `README.md` actualizado a la versión
  actual.

## 2026-08-12 08:05

### [Control Pedidos] v12.29.92 — Fix: 3 tipos de email SÍ consumían cuota real de EmailJS pero el contador no los contaba
- Pregunta del usuario (de cara a incorporar una 3ª cuenta EmailJS de
  backup): ¿el contador de envíos se está llevando correctamente? ¿se
  descuentan todos los correos, incluidos los automáticos, los de
  recuperación de contraseña, los de petición de usuario, etc.?
- Investigación: revisado el helper central `enviarEmailJS()`
  (`templates/index.html`) — confirmado que es el único punto que llama
  a `emailjs.send()` en todo el frontend (un único resultado en el
  código para `emailjs\.send\(`, dentro del propio helper), así que no
  hay ningún envío que se salte el wrapper por error de código. El
  wrapper llama después a `POST /api/emailjs/registrar-envio` para
  incrementar el contador.
- Bug real encontrado: ese endpoint llevaba `@login_required` a secas.
  Tres flujos legítimos llaman a `enviarEmailJS()` desde un navegador
  SIN sesión iniciada todavía — el email SÍ se envía de verdad
  (`emailjs.send()` no necesita login), pero la llamada posterior a
  `registrar-envio` fallaba con 401 y se descartaba en silencio (a
  propósito, para no romper el envío ya hecho), así que el contador
  nunca se enteraba: 1) recuperación de contraseña
  (`solicitar_reset_password`, usuario aún sin sesión); 2) código de
  verificación de login (`login()`, cuando hace falta verificación por
  inactividad — se envía ANTES de que `_completar_login()` cree la
  sesión); 3) confirmación de "Fase 2" de solicitar acceso
  (`solicitar_usuario_fase2()`, usuario nuevo sin cuenta —
  `sin_email=True` siempre, no solo como fallback).
- Los correos automáticos de sistema (reclamaciones, avisos de firma
  pendiente, resumen de "Comparar listado PDF", etc.) SÍ se contaban
  bien — se despachan vía `_enviarEmailsSistemaPendientes()`, pero solo
  mientras un admin/compras tiene la app abierta, es decir, con sesión
  ya iniciada.
- Corrección (sin quitar la protección del endpoint por completo):
  nueva función `_permite_registrar_envio_no_autenticado()` — los 3
  endpoints anteriores dejan ahora, justo antes de devolver los datos
  del email pendiente de enviar, una marca de UN SOLO USO en la sesión
  (`session["pdte_registrar_envio_email"] = True`, sin necesidad de
  login). `registrar-envio` acepta la petición si hay sesión válida O
  si esa marca está presente — y la consume con `pop` (no `get`), así
  que no sirve más que para ese envío concreto: no abre la puerta a que
  cualquiera incremente el contador a voluntad desde fuera.
- Verificado con un Flask de prueba aislado (sin depender de la base de
  datos real): sin marca ni sesión → 401 (protegido); tras la marca que
  deja el backend → el siguiente registrar-envio → 200; un segundo
  intento sin volver a marcar → 401 de nuevo (uso único confirmado, no
  reutilizable).
- `app.py` compila sin errores. Sin cambios en `templates/index.html`
  (el frontend ya llamaba correctamente a
  `enviarEmailJS()`/`registrar-envio` en los 3 casos — el bug estaba
  solo en el backend). `README.md` actualizado a la versión actual.
  Badge de versión del sidebar actualizado a "V 12.29.92"; entrada
  añadida en `CHANGELOG.md`.
- **Pendiente, a petición del usuario**: incorporar una 3ª cuenta
  EmailJS de backup (actualmente el sistema rota entre 2, cuenta 1 ⇄
  cuenta 2) — no incluido en esta entrega, a la espera de confirmar
  alcance.

## 2026-08-11 13:30

### [Control Pedidos] v12.29.90 — Nuevo "estado aparente" en el correo (ENTREGA PARCIAL / ENTREGA COMPLETA), a partir de la 8ª columna del listado SAP
- Petición del usuario: si el valor de la 8ª columna del PDF (importe
  pendiente) es superior a 0, indicar en el correo con estado aparente
  "ENTREGA PARCIAL"; si es 0 o negativo, "ENTREGA COMPLETA" — ambos
  casos se muestran, para revisión final por el comprador y el hotel.
- Cambio: la 8ª columna del listado simplificado (importe pendiente),
  que hasta ahora se descartaba (grupo no capturado del patrón), pasa a
  capturarse y usarse. Nueva función `_estado_aparente_entrega()` — a
  propósito **independiente** de `_entrega_estado()` (que compara base
  vs. recibido, columnas 6/7): el importe pendiente que trae SAP no
  siempre coincide con "base − recibido" calculado a mano (confirmado
  con el propio PDF real, p.ej. pedido 00029249: base 164,39, recibido
  0,00, pendiente informado 193,40 — no cuadra la resta), así que se
  usa tal cual lo da SAP en vez de recalcularlo.
- Regla aplicada literalmente: `pendiente > 0` → `"ENTREGA PARCIAL"`;
  `pendiente == 0` o negativo → `"ENTREGA COMPLETA"`. Se llama
  "aparente" a propósito: es una lectura directa del PDF, no una
  verificación.
- Nuevo campo `estado_aparente` en cada pedido del resultado (además de
  `importe_pendiente`). `_email_resumen_pdf_sap()` añade una columna
  "Estado aparente" a la tabla del correo (verde para ENTREGA COMPLETA,
  ámbar para ENTREGA PARCIAL) y una nota aclaratoria de que es una
  lectura automática pendiente de confirmación final por el comprador y
  el hotel.
- Verificado contra el listado real de 221 pedidos (hotel MT): 221/221
  reconocidos con los 10 grupos del patrón (antes 9), 116 ENTREGA
  PARCIAL / 105 ENTREGA COMPLETA, suma correcta. Probado también el
  correo con datos reales: la columna y la nota aparecen correctamente.
- `app.py` compila sin errores. Los 9 bloques `<script>` de
  `templates/index.html` pasan `node --check` (sin cambios de frontend
  en esta entrega — el cambio es 100% de `app.py`). `README.md`
  actualizado a la versión actual. Badge de versión del sidebar
  actualizado a "V 12.29.90"; entrada añadida en `CHANGELOG.md`.

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
