# Tareas pendientes — Control Pedidos Princess Canarias

> Backlog de peticiones ya registradas pero **todavía no implementadas**.
> Formato: fecha de la petición, petición verbatim de Víctor, y notas
> técnicas de qué haría falta construir (para cuando se aborde). Entrada
> más reciente arriba. Cuando una tarea se implemente, se retira de aquí
> y pasa a `CHANGELOG.md` / `docs/HISTORIAL_CAMBIOS.md` con su versión.

---

## 2026-09-03 — Investigar `KeyError: 0` recurrente en `_auto_migrate()`

**Origen**: detectado al revisar el log de Render del día de hoy (no
reportado explícitamente por Víctor, aparece solo en el log). La línea
`log.exception("Auto-migración — traceback completo del fallo:")`
(`app.py`, dentro del `except` de `_auto_migrate()`) se dispara
repetidamente a lo largo del día — 17:33, 18:50, 19:32, 20:09, 20:35,
21:22 — siempre con el mismo error de fondo: `KeyError: 0`.

**Por qué no se ha corregido todavía**: el fragmento de log pegado solo
trae la cabecera (`Traceback (most recent call last):`) y la última
línea (`KeyError: 0`), sin el resto del traceback (archivo y número de
línea exactos) — y `_auto_migrate()` es una función de ~1550 líneas
con más de 100 sentencias de migración, así que sin esa localización
exacta no es seguro adivinar cuál falla y aplicar un fix a ciegas.

**Qué hace falta para abordarlo**:
1. El traceback completo de una de esas ejecuciones (Render → Logs,
   buscar `Auto-migración — traceback completo del fallo` y copiar las
   líneas siguientes hasta `KeyError: 0` inclusive — normalmente
   4-8 líneas con la ruta de `app.py` y el número de línea exacto).
2. Con eso, localizar la sentencia (probablemente un
   `cur.fetchone()[0]` o similar acceso posicional sobre un resultado
   `RealDictRow`, que no soporta índices enteros y lanza justo
   `KeyError: 0`) y corregirla.

**Nota aparte**: como `_auto_migrate()` solo registra el fallo con
`log.warning`/`log.exception` y sigue sin interrumpir el arranque
("Auto-migración omitida"), esto no ha causado ningún problema visible
hasta ahora — pero al repetirse en cada arranque/reinicio del proceso,
esa sentencia de migración concreta nunca llega a aplicarse.

