# Backend — alta en un solo paso desde el Organizador

## Nuevo endpoint: `POST /api/solicitar-usuario/directo`

Fusiona fase 1 + fase 2 en una sola llamada, para uso exclusivo del
Organizador de escritorio (que ya conoce el usuario de Windows).

**Body esperado (JSON):**
```json
{
  "nombre": "...", "apellidos": "...", "email": "...",
  "movil": "...", "hoteles": "Hotel A, Hotel B",
  "usuario_windows": "DCOMPRAS"
}
```

**Qué hace:**
1. Valida los 6 campos (mismas reglas que fase 1 + fase 2 web).
2. Comprueba que `usuario_windows` no tenga ya cuenta activa
   (mismo check que la fase 2 real) — devuelve 409 con `ya_existe`
   si ya existe (activa o desactivada).
3. Inserta la solicitud directamente con `estado='completada'`,
   sin generar token ni depender de ningún email intermedio — cae
   en la misma cola que ya usa el panel admin
   (`GET /api/admin/solicitudes-acceso`), sin tocar ese panel.
4. Notifica por Telegram (siempre) y encola un email a los admins
   vía `_encolar_email_sistema` (mismo mecanismo fiable que ya usa
   la fase 1 — lo despacha el primer admin que abra la app, no
   depende de EmailJS en un navegador que no existe en este caso).
5. El envío de la contraseña al usuario sigue pasando exactamente
   igual que hoy: cuando el admin aprueba desde
   `/api/admin/solicitudes-acceso/<id>/aprobar` — **este endpoint
   nuevo no toca esa parte para nada.**

**No he podido ejecutarlo contra una base de datos real** — solo
verificado que compila (`py_compile`) y que el `INSERT` usa
exactamente las columnas de la tabla `solicitudes_acceso` tal como
está definida en `init_db()`. Recomiendo probarlo en local o con una
solicitud de prueba antes de darlo por bueno en producción.
