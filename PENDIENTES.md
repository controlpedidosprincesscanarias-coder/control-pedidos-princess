# Tareas pendientes — Control Pedidos Princess Canarias

> Backlog de peticiones ya registradas pero **todavía no implementadas**.
> Formato: fecha de la petición, petición verbatim de Víctor, y notas
> técnicas de qué haría falta construir (para cuando se aborde). Entrada
> más reciente arriba. Cuando una tarea se implemente, se retira de aquí
> y pasa a `CHANGELOG.md` / `docs/HISTORIAL_CAMBIOS.md` con su versión.

---

# Tareas pendientes — Control Pedidos Princess Canarias

> Backlog de peticiones ya registradas pero **todavía no implementadas**.
> Formato: fecha de la petición, petición verbatim de Víctor, y notas
> técnicas de qué haría falta construir (para cuando se aborde). Entrada
> más reciente arriba. Cuando una tarea se implemente, se retira de aquí
> y pasa a `CHANGELOG.md` / `docs/HISTORIAL_CAMBIOS.md` con su versión.

---

## 2026-09-09 — Reply-To del envío manual de reclamación desde el panel (`meaEnviarEmail`)

**Contexto**: v12.32.43 y v12.32.44 (ver `CHANGELOG.md`) añadieron
`reply_to` a los tres correos que salen hacia el proveedor por la cola
automática `emails_sistema_pendientes` (puente DALI, cambio de estado,
reclamación automática). El botón "Re-notificar" del panel (modal de
alerta, función `meaEnviarEmail()` en `templates/index.html`) manda el
email directamente por EmailJS sin pasar por esa cola, y su payload
tampoco fija `reply_to` — si el proveedor responde, hoy depende de la
configuración por defecto de la cuenta EmailJS usada (la cuenta Gmail
compartida de Princess), no del comprador que hizo el envío manual.

**Qué haría falta**: cuando `_meaData.es_proveedor` sea `true`, fijar
`reply_to` en el payload de `enviarEmailJS(...)` con el primer email de
`_meaData.cc_emails` (los compradores del hotel ya vienen ahí) — mismo
criterio que se usó para la reclamación automática.

