# v12.2.2 — 10 julio 2026 (actualizado)

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
