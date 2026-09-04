# Tareas pendientes — Control Pedidos Princess Canarias

> Backlog de peticiones ya registradas pero **todavía no implementadas**.
> Formato: fecha de la petición, petición verbatim de Víctor, y notas
> técnicas de qué haría falta construir (para cuando se aborde). Entrada
> más reciente arriba. Cuando una tarea se implemente, se retira de aquí
> y pasa a `CHANGELOG.md` / `docs/HISTORIAL_CAMBIOS.md` con su versión.

---

## 2026-09-03 — Localizar el `TypeError: Decimal - float` que se repite en `[COMPARAR-ALBARANES] Error aplicando coincidencia`

**Origen**: log de Render de hoy, dos apariciones seguidas (18:20:58 y
18:20:59), coincidencias `13093_336_35` y `13208_2041_41`:
`unsupported operand type(s) for -: 'decimal.Decimal' and 'float'`.

**Por qué no se ha corregido todavía**: el único punto conocido de esta
clase de fallo en esta misma cadena de llamadas
(`_notificar_cambio_estado` → `enviar_emails_estado` →
`_resumen_entregas()`) ya se corrigió en v12.32.02/v12.32.03 con un
`float()` explícito (`app.py`, línea ~2252) — así que la recurrencia de
hoy es, aparentemente, un `Decimal`/`float` **distinto**, en otro punto
todavía sin identificar de esa misma cadena (o de otra). El handler que
registraba el error solo usaba `log.error("...: %s", exc)`, que deja
únicamente el mensaje (`str(exc)`) sin traceback — así que nunca ha
sido posible ver en qué archivo/línea ocurre exactamente.

**Qué se ha hecho ya (2026-09-03, v12.32.06)**: se cambiaron a
`log.exception(...)` los tres puntos de captura de esta zona
(`_leer_texto()`, `_ejecutar_comparacion_albaranes_bg()` y el bucle de
`comparar_listado_albaranes_aplicar()`, donde ocurre exactamente este
error) para que la PRÓXIMA vez que se repita, el log de Render traiga
el traceback completo con archivo y número de línea exactos. Esto no
corrige la causa — solo la hace localizable.

**Qué hace falta para abordarlo**: la próxima vez que aparezca
`[COMPARAR-ALBARANES] Error aplicando coincidencia ...`, copiar del log
de Render las líneas siguientes (ahora sí incluirán el traceback
completo con `File "app.py", line N`) y pasarlas para localizar y
corregir la conversión de tipos que falta.

