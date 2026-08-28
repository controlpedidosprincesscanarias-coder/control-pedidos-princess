# Tareas pendientes — Control Pedidos Princess Canarias

> Backlog de peticiones ya registradas pero **todavía no implementadas**.
> Formato: fecha de la petición, petición verbatim de Víctor, y notas
> técnicas de qué haría falta construir (para cuando se aborde). Entrada
> más reciente arriba. Cuando una tarea se implemente, se retira de aquí
> y pasa a `CHANGELOG.md` / `docs/HISTORIAL_CAMBIOS.md` con su versión.

---

## Correo interno de cambio de estado — copia al departamento solicitante del pedido

**Fecha de la petición**: 2026-08-28.

**Petición de Víctor** (verbatim, a partir de una captura del modal "Nuevo pedido" con los desplegables Hotel/Departamento): "apartado para registrar los correos electrónicos de los diferentes departamentos que tenemos registrados al uso en el apartado departamento de pedidos; tener en cuenta que cada hotel tiene sus correos diferenciados entre departamentos y hoteles; la idea es que los correos internos de cambio de estado de los pedidos que ahora se envían al rol hotel y compradores, se envíen con copia al departamento solicitante del pedido, ejemplo, pedido JP restaurante, se debe enviar el correo interno al comprador JN al rol hotel JN y al correo del departamento restaurante del JN, mismo correo con copia a todos." — aclarado después: el "JP" del ejemplo es un lapsus, el hotel del ejemplo es siempre **JN (Jandía Princess)**.

**Ejemplo aclarado**: pedido de JN (Jandía Princess), departamento RESTAURANTE. El correo interno de cambio de estado debe ir, en un único envío con copia a todos: comprador(es) de JN, rol hotel de JN, y el correo registrado para el departamento RESTAURANTE de JN.

**Qué haría falta construir** (análisis del código actual, para cuando se implemente):

- `departamentos` (`models.py`) es hoy un catálogo **global**: `id`, `nombre`, `activo` — sin ninguna columna de email, y sin relación con `hoteles`. El mismo departamento (p. ej. "RESTAURANTE") es una única fila compartida por todos los hoteles.
- Lo que pide Víctor requiere un email **por combinación (hotel, departamento)**, no uno por departamento a secas — el mismo "RESTAURANTE" tiene un correo distinto en cada hotel. Hace falta una tabla nueva de relación, por ejemplo `departamento_hotel_email` (`hotel_id`, `departamento_id`, `email`, `email2` opcional), con un apartado de administración (probablemente dentro de "Familias de artículos" / "Departamentos" o un apartado nuevo) para registrar/editar esos correos, hotel a hotel.
- `enviar_emails_estado()` (`app.py`, ~línea 2032) es donde se arma la lista de destinatarios del correo interno de cambio de estado (`_todos_internos`, ahora mismo `_emails_compradores` + `_emails_hotel_users`, con exclusión de quien hizo el cambio si no es automático — ver v12.30.37). Habría que añadir a esa lista el email de `departamento_hotel_email` para `(pedido.hotel_id, pedido.departamento_id)`, si existe, con el mismo criterio de "un único correo con copia a todos" que ya se usa (no un correo aparte al departamento).
- Pendiente de decidir con Víctor: si un departamento de un hotel no tiene correo registrado, ¿se omite sin más (comportamiento por defecto más simple) o se avisa de algún modo de que falta configurar? Y si tanto el departamento como el rol hotel/comprador coinciden con la misma persona, evitar duplicar destinatario en la cabecera (ya hay lógica de deduplicación en `_todos_internos`, reutilizable).

**Alcance no confirmado todavía**: si esto debe aplicar también a Telegram/popup (`_telegram_cambio_estado`) o solo al correo — Víctor solo mencionó "los correos internos".
