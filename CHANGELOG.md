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
