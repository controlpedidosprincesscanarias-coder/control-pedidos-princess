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
