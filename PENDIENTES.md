# Tareas pendientes — Control Pedidos Princess Canarias

> Backlog de peticiones ya registradas pero **todavía no implementadas**.
> Formato: fecha de la petición, petición verbatim de Víctor, y notas
> técnicas de qué haría falta construir (para cuando se aborde). Entrada
> más reciente arriba. Cuando una tarea se implemente, se retira de aquí
> y pasa a `CHANGELOG.md` / `docs/HISTORIAL_CAMBIOS.md` con su versión.

---

### Corrección retroactiva de departamento Restaurante/Bares en GY/IT/MT/TA — auditoría entregada (v12.32.53), pendiente de que Víctor la ejecute y revise

**Origen**: v12.32.34 (5 septiembre 2026, ver `CHANGELOG.md`) corrigió que el
código SAP 00000100/00000301 se asignaba siempre a "RESTAURANTE & BARES"
aunque GY/IT/MT/TA llevan Restaurante y Bares como departamentos separados
— pero esa entrega solo corrigió el comportamiento HACIA ADELANTE. Quedó
una pregunta explícita para Víctor: **¿hace falta revisar los pedidos de
esos 4 hoteles ya dados de alta antes de esa fecha?** Víctor respondió
(AskUserQuestion, 9 septiembre 2026): "Sí, auditar primero".

**Entregado en v12.32.53**: una auditoría de solo lectura (Admin →
Integridad → "🍽️ Auditoría puntual: departamento Restaurante/Bares
(GY/IT/MT/TA)") que lista los pedidos afectados y distingue, cruzando con
el código de departamento SAP guardado, los de **confianza alta** (código
SAP 00000100/00000301 — el bug de v12.32.34 sí pudo causarlo, con
departamento sugerido) de los que hay que **revisar a mano** (sin dato SAP
que lo confirme — podrían ser asignaciones manuales legítimas de antes del
2026-08-31). Nunca corrige nada sola; cada fila lleva un enlace para
corregir el pedido a mano desde su ficha normal, si procede.

**Qué falta**: que Víctor ejecute esta auditoría contra los datos reales
de producción y revise caso a caso los pedidos listados — empezando por
los de confianza alta — decidiendo cuáles corregir. Este punto se retira
de aquí solo cuando esa revisión se dé por completada (o Víctor decida
que no hace falta tocar nada retroactivo).

---

### Hallazgos de la auditoría del 9 de septiembre de 2026 (petición de Víctor) — ambos ya cerrados

Al auditar el ZIP ya desplegado (v12.32.47) se corrigieron 3 fallos reales
de control de acceso (ver `CHANGELOG.md` v12.32.48), y quedaron anotados
dos hallazgos adicionales pendientes de decisión. Víctor confirmó los dos:

1. **`aprobar_expediente()` no repetía todas las comprobaciones 0a-0d** —
   Víctor confirmó igualarla al resto ("sí, igualar función") — cerrado en
   v12.32.49, ver `CHANGELOG.md`.
2. **Comparación Departamento/Almacén por "contiene" en ambos sentidos**,
   que en teoría podría dar por válido un Almacén "RESTAURANTE & BARES"
   contra un Departamento "BARES" en los hoteles con Restaurante/Bares
   separados (GY/IT/MT/TA) — Víctor confirmó (9 septiembre 2026) que
   **el PDF oficial nunca trae "RESTAURANTE & BARES" como Almacén para
   esos 4 hoteles** (SAP ya los tiene separados en origen), así que este
   caso no puede darse nunca en la práctica. No requiere ningún cambio de
   código — cerrado como verificado, no como corregido.

