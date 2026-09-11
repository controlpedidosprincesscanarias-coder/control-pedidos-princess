# API DALI — Backend

API REST (Node.js + Express + Supabase) para el proyecto descrito en
`docs/informe-tecnico.md`. Implementa los endpoints de la sección 7 del
informe.

## Puesta en marcha

```bash
npm install
cp .env.example .env      # rellena SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SESSION_SECRET...
npm run dev
```

Antes de arrancar, aplica el esquema en Supabase (SQL editor) con
`schema.sql` y carga los datos iniciales importando, en este orden,
`naturalezas.csv → familias.csv → subfamilias.csv → proveedores.csv → articulos.csv`
(Table Editor → Import data from CSV).

Como no hay pantalla de autorregistro, da de alta el primer usuario a mano:

```bash
npm run create-user -- --nombre="Tu Nombre" --email=tu@empresa.com --rol=admin --password=algo-largo
```

## Endpoints implementados

(2026-09-03) La columna "Auth" dice `admin` para toda ruta bajo
`/admin/*`, pero desde esta versión eso ya no es todo-o-nada: cada una de
esas rutas exige además, vía `requierePermiso("<clave>")`, una de las
claves de "Gestión" (9 desde el 2026-09-10, ver más abajo) — el
**administrador principal** (`es_admin_principal`, uno solo, ver más
abajo) pasa siempre; un administrador normal solo si esa clave está en su
columna `permisos`. El detalle de qué ruta pertenece a qué clave está en
`src/routes/admin.js` (agrupado por comentarios) y, en la app, se
corresponde con los mismos destinos de "Gestión" del sidebar.

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| GET | `/health` | – | Estado del servicio |
| POST | `/auth/login` | – | `{ email, password }` → fija la sesión (cookie) |
| POST | `/auth/sso` | – | Token firmado (HMAC-SHA256, `DALI_SSO_SECRET`) emitido por `control-pedidos-princess` → aprovisiona/actualiza el usuario y fija la sesión, sin login manual |
| POST | `/auth/logout` | – | Cierra la sesión |
| GET | `/auth/me` | sesión | Usuario de la sesión actual |
| POST | `/auth/recuperar-acceso` | – | `{ email, nombre }` → "¿Has olvidado tu contraseña?". Si el email está registrado y activo, genera un enlace de acceso de un solo uso; si no, prepara el aviso a los admins de una solicitud de acceso. Responde SIEMPRE el mismo mensaje genérico (no revela qué emails existen) y devuelve `envio` (`{tipo, destinatario?, asunto, cuerpoHtml, cuerpoText}` o `null`) para que el frontend lo mande por EmailJS desde este mismo navegador — `envio.tipo` distingue plantilla "usuario" (destinatario incluido, es la propia persona) de "admin" (destinatario NUNCA incluido, se fija en la propia plantilla EmailJS) — ver `HISTORIAL.md` v1.15 y v1.34/v1.19.52 |
| GET | `/auth/token-acceso/:token` | – | Valida un enlace de acceso (existe, no caducado, no usado) antes de mostrar el formulario de "elige tu contraseña" |
| POST | `/auth/canjear-token-acceso` | – | `{ token, password }` → canjea el enlace, guarda la contraseña elegida y abre sesión directamente (auto-login) |
| GET | `/auth/emailjs-config` | opcional | Credenciales de la cuenta EmailJS de DALI actualmente activa para la plantilla "usuario" (o `{configurado:false}`), más — por separado, campo `admin` — las de la plantilla de aviso a administradores si están configuradas (`null` si no) — para que el frontend llame a `emailjs.init()`/`emailjs.send()` |
| POST | `/auth/emailjs-registrar-envio` | opcional* | Incrementa el contador local de envíos de la cuenta activa y rota a la otra cuenta al llegar al umbral. *Sin sesión, solo se acepta justo después de un `recuperar-acceso` que generó un envío (flag de un solo uso) |
| GET | `/articulos` | opcional | Listado + búsqueda avanzada. `?todos=true` solo admin |
| GET | `/articulos/:id` | opcional | Detalle de un artículo |
| GET | `/articulos/:id/fichas` | – | Fichas técnicas/seguridad del artículo (solo del proveedor asignado) |
| GET | `/articulos/:id/fichas-por-proveedor` | – | Fichas, IMAGEN y CÓDIGO DE PROVEEDOR de TODOS los proveedores con algo guardado para ese artículo (documentación, o solo el código si aún no se subió nada), agrupadas por proveedor (`asignado: true/false`) — alimenta "Ver alternativas de otros proveedores" en la ficha y la gestión por proveedor de `ArticuloForm.jsx` (admin) |
| GET | `/jerarquia` | opcional | Árbol naturaleza → familia → subfamilia (con IDs), para el sidebar desplegable — solo incluye ramas con al menos un artículo (activo, salvo `?todos=true` solo admin) |
| GET | `/estadisticas` | – | Fecha de la última importación, total DALI activos, total con código SAP — para la franja de la cabecera |
| POST | `/admin/import-excel` | admin | Sube los dos Excel (multipart, campos `articulos_dali` y `listado_sap`) y hace upsert |
| GET | `/admin/import-excel/estado/:jobId` | admin | Progreso de una importación en curso (procesa por lotes en segundo plano) |
| POST | `/admin/articulos` | admin | Alta manual de artículo — sigue existiendo en el backend pero el panel ya no lo llama (ver más abajo) |
| PUT | `/admin/articulos/:id` | admin | Edición |
| DELETE | `/admin/articulos/:id` | admin | Baja (borra también su imagen y fichas del Storage) — el panel de administración ya no llama a este endpoint (ver más abajo), pero se deja disponible |
| GET | `/admin/articulos/:id/documentos-hash` | admin | Hash SHA-256 de la imagen/fichas ya guardadas del artículo (por proveedor) — el frontend lo compara contra el hash local antes de subir, para no retransferir un archivo idéntico al ya guardado |
| POST | `/admin/articulos/:id/imagen` | admin | Sube/sustituye la foto del artículo **para un proveedor concreto** (multipart, campo `imagen`, opcional `id_proveedor` — id real de `proveedores`; si se omite, usa el proveedor ya asignado al artículo) |
| DELETE | `/admin/articulos/:id/imagen` | admin | Borra SOLO la imagen, sin tocar las fichas (opcional `?id_proveedor=`: borra la reserva de ese proveedor en vez de la del asignado) |
| POST | `/admin/articulos/:id/fichas` | admin | Sube/sustituye una ficha **para un proveedor concreto** (multipart, campos `tipo`, `ficha`, opcional `id_proveedor`, mismo criterio que la imagen) |
| DELETE | `/admin/articulos/:id/adjuntos` | admin | Borra imagen y fichas del artículo (Storage + DB) sin tocar el artículo — para limpiar documentación huérfana (ver `avisos_desaparecidos`) |
| DELETE | `/admin/articulos/:id/fichas/:tipo` | admin | Borra SOLO esa ficha ("tecnica" o "seguridad"), sin tocar la imagen ni la otra ficha (mismo `?id_proveedor=` opcional que el borrado de imagen) |
| PUT | `/admin/articulos/:id/codigo-proveedor` | admin | Guarda/actualiza el código con el que un proveedor concreto identifica ese artículo (`id_proveedor`, `codigo`) |
| GET | `/admin/articulos/por-codigo-proveedor` | admin | Busca qué artículo(s) usa un proveedor (`id_proveedor`) para identificar un código (`codigo`) — devuelve `codigos_dali` (array; puede haber más de un DALI con el mismo proveedor+código, p.ej. un mismo producto en varios formatos) |
| POST | `/admin/articulos/carga-masiva-codigo-proveedor` | admin | Sube en bloque la columna "Código Proveedor" de un .xlsx (mismo formato que `GET /export/excel`) |
| POST | `/admin/articulos/:id/marcas-proveedor` | admin | Da de alta una marca extra del mismo proveedor para este artículo (`id_proveedor`, `codigo`) — "por seguridad y control", además de (nunca en vez de) la referencia principal de ese proveedor; ver `HISTORIAL.md` v0.97 |
| PUT | `/admin/marcas-proveedor/:idMarca/codigo` | admin | Actualiza el código de una marca ya creada |
| DELETE | `/admin/marcas-proveedor/:idMarca` | admin | Borra la marca entera (código + imagen + fichas + Storage) |
| POST | `/admin/marcas-proveedor/:idMarca/imagen` | admin | Sube/sustituye la imagen de esa marca (multipart, campo `imagen`) |
| DELETE | `/admin/marcas-proveedor/:idMarca/imagen` | admin | Borra solo la imagen de la marca |
| POST | `/admin/marcas-proveedor/:idMarca/fichas` | admin | Sube/sustituye una ficha de esa marca (multipart, campos `tipo`, `ficha`) |
| DELETE | `/admin/marcas-proveedor/:idMarca/fichas/:tipo` | admin | Borra solo esa ficha ("tecnica" o "seguridad") de la marca |
| GET | `/admin/usuarios` | admin | Listado de usuarios |
| POST | `/admin/usuarios` | admin | Alta de usuario (nombre, email, rol, password) |
| PUT | `/admin/usuarios/:id` | admin | Edición (nombre/email/rol/activo/password, todos opcionales) |
| DELETE | `/admin/usuarios/:id` | admin | Baja definitiva (no reversible) — bloqueada para la propia cuenta y para el último admin activo que quede; para una baja reversible, usar `activo: false` en `PUT` |
| POST | `/admin/usuarios/:id/traspasar-principal` | admin | Traspasa el puesto de administrador principal a `:id` (cuenta admin activa) y se lo retira a quien llama — solo lo puede usar quien YA es principal, aunque el propio endpoint exija además el permiso `admin-usuarios` por consistencia con el resto del grupo (ver más abajo) |
| GET | `/admin/solicitudes-acceso` | admin | Listado de solicitudes de acceso (pendientes primero, más recientes primero) — ver `POST /auth/recuperar-acceso` arriba, que es quien las crea |
| POST | `/admin/solicitudes-acceso/:id/aceptar` | admin | `{ rol }` (`admin`\|`hotel`, por defecto `hotel`) → crea o reactiva la cuenta (con un hash aleatorio inutilizable, nunca transmitido), marca la solicitud como aceptada y devuelve `envio`+`link` de un enlace de bienvenida de un solo uso para que el navegador del admin lo mande por EmailJS |
| POST | `/admin/solicitudes-acceso/:id/rechazar` | admin | Marca la solicitud como rechazada, sin avisar por correo |
| GET | `/admin/emailjs-config` | admin | Configuración completa (con credenciales) de las 2 cuentas EmailJS de DALI |
| PUT | `/admin/emailjs-config` | admin | Actualiza credenciales/umbral/cuenta activa de las cuentas EmailJS |
| GET | `/admin/proveedores` | admin | Listado simple de proveedores (id + nombre), para el buscador de la carga masiva y de la ficha individual |
| GET | `/admin/proveedores/:id/resumen` | admin | Cuántos artículos/imágenes/fichas/códigos de proveedor tiene un proveedor — para comparar antes de fusionar dos proveedores |
| POST | `/admin/proveedores/fusionar` | admin | Traslada todo lo del proveedor "origen" al "destino" y borra el origen (acción irreversible) — para cuando SAP renombra un proveedor y queda duplicado |
| GET | `/admin/proveedores/con-imagen-generica` | admin | Ids (+ cantidad de artículos) de los proveedores que tienen AHORA MISMO alguna imagen genérica ("SIN IMAGEN") guardada — usado por `CargaMasivaModal.jsx` para detectar bajas incluso si la carpeta IMAGENES del proveedor ha quedado vacía (ver `HISTORIAL.md` v0.98/v0.99) |
| DELETE | `/admin/proveedores/:id/imagen-generica` | admin | Borra (Storage + tabla) la imagen genérica de reserva de TODOS los artículos de ese proveedor |
| GET | `/admin/documentacion-faltante` | admin | Artículos activos sin imagen/ficha técnica/ficha seguridad, agrupados por proveedor, con su código de proveedor |
| GET | `/admin/documentacion-faltante/excel` | admin | Igual, en un .xlsx (una hoja por proveedor, o una sola hoja agrupada si hay más de 20) |
| POST | `/admin/documentacion-faltante/preview-email` | admin | `{ idProveedor, asunto, cuerpo }` → devuelve el HTML del correo (mismo que resolvería `preparar-envio`) sin resolver destinatario ni enviarlo, para previsualizar mientras se edita |
| POST | `/admin/documentacion-faltante/:idProveedor/preparar-envio` | admin | `{ asunto, cuerpo }` → resuelve el destinatario real contra Control de Pedidos, genera el HTML (mismo logo/colores que `control-pedidos-princess`) y devuelve las credenciales EmailJS (reutiliza el mismo Template ID "de usuario", ver `HISTORIAL.md` v1.44); el envío real lo hace el navegador justo después, con el EmailJS propio de DALI (desde v1.19.60 — antes se encolaba en `emails_sistema_pendientes` de esa app, ver `HISTORIAL.md` v1.42) |
| GET | `/admin/documentacion-zip` | admin | Descarga un .zip con la documentación de todos los proveedores organizada en carpetas (`PROVEEDOR/FICHAS TECNICAS\|FICHAS SEGURIDAD\|IMAGENES/<código proveedor>_<artículo>.ext`; la imagen genérica "SIN IMAGEN" de cada proveedor se incluye una única vez, como `IMAGENES/SIN IMAGEN.ext`) — ver `HISTORIAL.md` v0.94, v1.32 y v1.33 |
| GET | `/export/excel` | opcional | Descarga .xlsx del listado visible según rol (o de una selección manual de códigos — ver "Exportación" más abajo) |
| GET | `/export/pdf` | opcional | Descarga .pdf del listado visible según rol (o de una selección manual de códigos — ver "Exportación" más abajo) |
| GET | `/export/documentacion-faltante-pdf/:idProveedor` | público, sin sesión | (2026-09-11) Descarga un .pdf con TODO lo que le falta a ese proveedor (ficha técnica, ficha de seguridad, imagen — una columna por tipo), recalculado en el momento de la petición. Pensado para el propio proveedor, sin cuenta en DALI: el correo de "Documentación pendiente" enlaza aquí en vez de itemizar la lista dentro del texto cuando es muy larga — ver "Documentación faltante" más abajo |
| GET | `/admin/export-completo` | admin + permiso `admin-exportar-completo` | (2026-09-10) Descarga .xlsx con TODA la información de los dos Excel que se importan (DALI + SAP) más "Código Proveedor", sin ningún filtro — todo el catálogo, activos e inactivos. Reservado al administrador principal por defecto, concedible a otros admins desde "Usuarios" — ver "Exportación" más abajo |

## Autenticación

Sesión por **cookie firmada** (`cookie-session`, sin store de servidor —
los datos de sesión viajan cifrados/firmados en la propia cookie, igual
que hace Flask por defecto), no JWT en cabecera. El middleware
`requireAuth` (en `src/middleware/auth.js`) lee `req.session` y adjunta
`req.user = { id, nombre, email, rol, esAdminPrincipal, permisos }`.

La sesión **caduca cada día** (huso Canarias, `src/utils/fecha.js`): si
`req.session.loginDate` no es la fecha de hoy, se invalida y hay que
volver a iniciar sesión — evita que una pestaña olvidada en la oficina
quede autenticada indefinidamente.

Las contraseñas se guardan como hash **bcrypt** (`usuarios.hash_password`
en `schema.sql`), nunca en texto plano. Se dan de alta desde la pantalla
Administración → Usuarios (`POST /admin/usuarios`), por CLI con
`npm run create-user` (ver arriba), o aceptando una solicitud de acceso
(`POST /admin/solicitudes-acceso/:id/aceptar`, ver más abajo) — no hay
autorregistro directo, solo un admin puede crear una cuenta (o aprobar
una solicitud que la crea).

**Permisos granulares de administrador** (2026-09-03,
`database/migraciones/2026-09-03_permisos_admin.sql`) — v1.19.43: a
petición de Víctor, ya no todo administrador tiene acceso a todo
"Gestión" por el mero hecho de tener `rol = 'admin'`. Hay exactamente un
**administrador principal** (`usuarios.es_admin_principal = true`, fijado
a mano en Supabase — sin ningún endpoint ni pantalla para cambiarlo,
adrede: no hay forma de que dos cuentas se disputen ese papel, y solo se
toca directamente en la base de datos) con acceso incondicional a todo,
y que es el único que puede: dar de alta otro admin, cambiar el `rol` de
cualquiera, cambiar los `permisos` de otro admin, o activar/desactivar/
eliminar la cuenta de otro admin. El resto de administradores tienen una
columna `usuarios.permisos text[]` con un subconjunto de las claves de
"Gestión" (`PERMISOS_VALIDOS` en `usuariosController.js`), aplicado en
cada ruta de `/admin/*` por `requierePermiso()` (ver
`src/middleware/auth.js`); sin esa clave, un admin normal sigue pudiendo
gestionar cuentas `hotel` sin restricción y hacer mantenimiento básico
(nombre/email/contraseña) de OTRAS cuentas admin, pero no tocar su rol,
permisos, ni activarlas/desactivarlas/eliminarlas. Como toda la sesión
viaja en la cookie firmada (ver arriba), un cambio de `permisos` o de
`es_admin_principal` **no tiene efecto hasta que esa persona vuelva a
iniciar sesión** — la misma limitación que ya existía para los cambios
de `rol`. Tras aplicar la migración original, todos los admins existentes
conservaron acceso a todo (el `DEFAULT` de la columna era el array
completo de las 8 claves de entonces) — Víctor restringe a quien haga
falta después, uno a uno, desde Administración → Usuarios.

(2026-09-10) Novena clave, `admin-exportar-completo` (botón "Exportar
catálogo completo"): a diferencia de las 8 anteriores, esta NO se añadió
al `DEFAULT` de la columna `permisos` — es una capacidad nueva, así que
arranca sin concederse a ningún admin existente, solo al administrador
principal (que siempre pasa esta comprobación). Víctor decide desde
Administración → Usuarios a quién más se la concede, si a alguien.

**Traspaso del puesto** (2026-09-03, `POST /admin/usuarios/:id/traspasar-principal`) —
v1.19.44: como `es_admin_principal` no se puede tocar desde ninguna
pantalla ni endpoint genérico (a propósito, ver arriba), el único modo
de que ese puesto cambie de manos sin entrar en Supabase a mano es este
endpoint dedicado — concede el puesto a `:id` y se lo retira a quien
llama, las dos cosas en la misma operación (nunca "varios principales a
la vez": Víctor lo eligió explícitamente así al preguntárselo). El
destino tiene que ser ya una cuenta `admin` activa. Como el cambio de
sesión tampoco se nota hasta el siguiente login (mismo párrafo de
arriba), el frontend (`AdminUsuarios.jsx`) cierra la sesión de quien
traspasa justo después de un traspaso con éxito, para que no se quede
viendo controles de "administrador principal" que ya no le corresponden.

**Recuperación de acceso** (2026-09-02, `POST /auth/recuperar-acceso` +
`database/migraciones/2026-09-02_tokens_acceso_emailjs.sql`) — v1.15:
DALI dejó de depender de `control-pedidos-princess` para estos correos
(la versión anterior, v1.14, sí encolaba en esa app — ver
`database/migraciones/2026-09-02_recuperacion_acceso.sql` e
`HISTORIAL.md` v1.14). Ahora DALI tiene su propio EmailJS (2 cuentas
encadenadas "por seguridad", configurables desde Administración →
Configuración EmailJS — ver `src/services/emailjsConfig.js`) y el envío
lo dispara SIEMPRE un navegador que ya está abierto en el momento de la
acción: el del propio solicitante (autoservicio, sin sesión) o el del
admin que acepta una solicitud.

Un email ya registrado y activo recibe un ENLACE de acceso de un solo
uso (tabla `tokens_acceso`, caduca en 2h) — al pulsarlo, la propia
persona elige su contraseña directamente, sin que exista en ningún
momento una contraseña temporal real (sustituye al diseño de v1.14). Uno
no registrado (o desactivado) genera una fila en `solicitudes_acceso` y
prepara el aviso a los admins activos, para que la acepten o rechacen
desde Administración → Solicitudes de acceso — aceptarla también emite
un enlace de bienvenida de un solo uso, nunca una contraseña.
`usuarios.debe_cambiar_password` (de la migración anterior) queda
vestigial: ya no lo lee ni lo escribe ningún código de esta versión. Ver
`HISTORIAL.md` v1.15 para el diseño original (por qué un EmailJS propio
en vez de compartir el de `control-pedidos-princess`, límite de una
petición cada 3 minutos por email, mensaje de respuesta siempre
genérico) y `HISTORIAL.md` v1.34/v1.19.52 para la revisión de seguridad
posterior: el aviso a admins ya NO manda el destinatario desde el
navegador (viajaba en el JSON de respuesta, visible para cualquier
visitante anónimo inspeccionando DevTools → Red) — usa ahora una
plantilla EmailJS separada con el destinatario fijado en el propio panel
de EmailJS (`template_id_admin_1`/`template_id_admin_2`, ver
`src/services/emailjsConfig.js`). Queda documentado y aceptado como
riesgo residual conocido (sin resolver a propósito) que sigue siendo
observable, inspeccionando esa misma llamada, si un email concreto está
o no registrado.

"Documentación faltante" sigue usando la cola de
`emails_sistema_pendientes` en `control-pedidos-princess` (vía
`controlPedidosEmailBridge.js`) por ahora — queda anotado como
actualización próxima, fuera de esta versión.

(2026-09-03) `GET /admin/documentacion-faltante` (y su exportación a
Excel) es un informe AGREGADO sobre todo el catálogo activo, agrupado por
proveedor — no un listado paginable artículo a artículo como
`GET /articulos`, así que no admite paginación de la misma forma (necesita
traer y cruzar todo para poder calcular los grupos y los totales
correctos). `calcularDocumentacionFaltante()` (`documentacionController.js`)
pide las tres tablas relacionadas (imágenes, fichas, códigos de
proveedor) con `Promise.all` en vez de una tras otra — las tres son
independientes entre sí, así que lanzarlas a la vez recorta el tiempo
total a, aproximadamente, el de la más lenta de las tres. Ver
`HISTORIAL.md` v1.29.

(2026-09-11) En `EmailProveedorModal.jsx`, cuando un proveedor tiene más
de 30 referencias con ficha técnica pendiente (`UMBRAL_LISTADO_FICHA_TECNICA_PDF`),
el correo deja de itemizarlas una a una y en su lugar enlaza a
`GET /export/documentacion-faltante-pdf/:idProveedor` — un PDF con TODO
lo pendiente de ese proveedor (ficha técnica, ficha de seguridad e
imagen). La URL viaja como texto plano dentro del propio cuerpo del
correo; `textoPlanoAHtmlParrafos()` (`src/utils/emailHtml.js`) la
detecta y la pinta como un botón en el HTML final — no hace falta
ningún parámetro nuevo en `preview-email`/`preparar-envio`. Ver
`HISTORIAL.md` v1.50.

Con `credentials: true` en CORS, la variable `CORS_ORIGIN` es
obligatoria (no vale `*`) — ver `.env.example`.

## Exportación

`GET /export/excel` y `GET /export/pdf` (`src/controllers/exportController.js`)
aceptan los mismos cuatro filtros que `GET /articulos` (`q`, `naturaleza`,
`familia`, `subfamilia`, `todos`) para exportar justo lo que se ve en
pantalla con esos filtros aplicados.

(2026-09-03) Además admiten `codigos` — una lista de `codigo_dali`
separados por comas (p.ej. `?codigos=101,202,303`) — a petición de
Víctor, para poder exportar/imprimir justo los artículos que ha ido
marcando a mano en el catálogo, que pueden venir de búsquedas
completamente distintas y por tanto no se pueden expresar con los cuatro
filtros de siempre. Cuando llega `codigos`, el resto de filtros
(`q`/`naturaleza`/`familia`/`subfamilia`/`todos`) se ignora por completo,
y se exportan EXACTAMENTE esos códigos, estén activos o no — si se
marcaron a mano en pantalla es porque ya se vieron y se quisieron ahí,
así que no tiene sentido volver a filtrarlos por `activo_dali`/
`activo_general`. Esta vía está reservada a cualquier administrador
(`rol === 'admin'`, sin hacer falta ningún permiso granular de "Gestión"
de por medio): una petición con `codigos` y sin sesión de administrador
recibe `403` antes de tocar la base de datos — sin esa comprobación,
cualquier visitante sin sesión podría usar `?codigos=` para leer datos de
artículos desactivados que normalmente solo ve un admin con "Incluir no
activos" marcado.

(2026-09-10) Cuando `GET /export/excel` recibe `codigos` de un admin (la
selección manual de arriba), el `.xlsx` lleva una columna extra al final del
listado, después de "Activo", con la cabecera "Precio €" — siempre en
blanco, para rellenarla a mano; DALI no guarda ningún precio de artículo.
No aparece en el resto de exportaciones Excel ni en el PDF (ver
`incluirColumnaPrecioEnExcel()` en `exportController.js` y su uso en
`generarExportWorker.js`).

(2026-09-10) `GET /admin/export-completo` es un endpoint aparte de los dos
de arriba (no acepta ningún filtro ni `codigos`) — genera un `.xlsx` con las
20 columnas que recogen entre los dos los Excel de `POST
/admin/import-excel` (artículos DALI + SAP) más "Código Proveedor",
siempre del catálogo entero (`fetchArticulosCompletoParaExport()`, sin
`.eq("activo_dali", ...)` ni ningún otro filtro). Vive en `routes/admin.js`
en vez de `routes/export.js` precisamente para poder exigir el permiso
granular `admin-exportar-completo` (`requierePermiso`, ver más arriba
"Permisos granulares de administrador"), no solo `optionalAuth` como el
resto de exportaciones.

(2026-09-03) Todos los botones de descarga del frontend (catálogo
principal, "Documentación faltante" y "Exportar documentación") llaman a
estos endpoints por `fetch` (`descargarDesdeUrl()` en
`frontend/src/services/api.js`), no navegando la pestaña directamente con
`window.open()` — necesita `exposedHeaders: ["Content-Disposition"]` en
CORS (ver más abajo, `src/server.js`) para poder leer el nombre real del
fichero desde JS. Ver `HISTORIAL.md` v1.29 para el porqué (pestaña en
negro/blanco sin ninguna señal de progreso en ficheros grandes).

## Importación de Excel y dimensiones nuevas

`POST /admin/import-excel` resuelve naturaleza, familia, subfamilia y
proveedor contra sus tablas antes de guardar los artículos
(`src/utils/dimensiones.js`, función `get_or_create`): si el Excel trae
un nombre que no existía, se da de alta automáticamente y se usa su id
recién creado — no se guarda ninguna fila con la FK a `null` solo porque
el nombre sea nuevo. Es la misma lógica que usa `database/build_csvs.py`
para la carga inicial, aquí aplicada en caliente en cada importación. La
respuesta incluye `dimensiones_creadas` (cuántos registros nuevos de cada
tabla se han dado de alta) y `avisos` si, pese a todo, alguna fila no
logra resolverse.

La respuesta también incluye `avisos_actualizacion`: artículos cuya
descripción DALI, descripción SAP o código SAP acaba de cambiar con
esta importación Y que ya tienen una imagen y/o ficha técnica subida
(`storageController.js`) — esos adjuntos podrían haber quedado
desactualizados o mostrando información que ya no corresponde al
artículo. Se calcula bloque a bloque (mismo troceo de 500 en 500 que
el resto de la importación), comparando el estado justo antes de cada
bloque contra los valores nuevos. `ImportarExcel.jsx` lo muestra
destacado, aparte de los `avisos` normales.

Y `avisos_desaparecidos`: artículos que estaban en la base de datos
pero ya no aparecen en el Excel que se acaba de importar (no que se
hayan marcado `ACTIVO=NO` — que la fila directamente ya no exista) Y
que tienen imagen y/o alguna ficha subida. No debería pasar (un
codigo_dali real no debería desaparecer del maestro), y por eso no se
borra nada solo — el upsert nunca hace `DELETE`, así que el artículo
se queda tal cual en la base de datos, solo su documentación se queda
huérfana sin que nada la use. `ImportarExcel.jsx` lo muestra con un
botón "Eliminar documentación" por artículo (con confirmación) que
llama a `DELETE /admin/articulos/:id/adjuntos` — borra la imagen y las
fichas, nunca el artículo en sí; la decisión sigue siendo siempre
manual, la importación solo detecta y avisa.

`POST /admin/articulos` (alta manual) y `PUT /admin/articulos/:id`
(edición de datos) siguen existiendo en el backend, pero **el panel de
administración ya no llama a ninguno de los dos** — los artículos solo
se crean y se actualizan importando el Excel, es la única vía, para que
la base quede siempre compaginada con el origen real DALI-SAP.
`ArticuloForm.jsx` ya no tiene ningún campo editable: solo muestra los
datos del artículo en modo lectura y permite subir/sustituir su imagen
y fichas (`POST /admin/articulos/:id/imagen` y `/fichas`).

### Documentación por proveedor (imagen y fichas)

**(2026-08-17, v1.7.0)** Imagen y fichas dejaron de ser "una por
artículo" y pasan a guardarse **una por artículo y proveedor** —
tablas `imagenes` y `fichas` (`id_proveedor` real, FK a `proveedores`,
no un código de texto libre). `POST .../imagen` y `POST .../fichas`
aceptan un campo opcional `id_proveedor`; si se omite, se usa el
proveedor ya asignado al artículo (comportamiento antiguo, sigue
funcionando igual para una subida suelta desde la ficha de un
artículo). `CargaMasivaModal.jsx` recorre una carpeta raíz con una
subcarpeta por proveedor (nombre real, sin tildes/mayúsculas) y sube
en una sola pasada documentación de todos los proveedores presentes,
sin que unos sustituyan a otros. En la ficha del artículo se muestra
siempre la versión del proveedor que tiene asignado en ese momento; el
resto queda en reserva y pasa a mostrarse (sin volver a subir nada) si
el proveedor asignado cambia más adelante, p.ej. tras reimportar el
Excel.

Las columnas antiguas `articulos.url_imagen` y
`articulos.codigos_proveedor_adjuntos` (texto libre, sin FK) se dejan
sin borrar como histórico, pero la aplicación ya no las lee ni las
escribe — con `id_proveedor` real por fila en `imagenes`/`fichas`, qué
proveedores tienen documentación de un artículo es una consulta
directa, no hace falta duplicarlo en un array de texto.

**Deduplicación por hash (v1.7.0):** antes de subir un archivo, el
frontend calcula su SHA-256 con Web Crypto
(`frontend/src/utils/hashArchivo.js`) y lo compara contra
`GET /admin/articulos/:id/documentos-hash` — si coincide con lo ya
guardado para ese proveedor, no se transfiere el archivo. El backend
calcula y guarda el hash (columna `hash_sha256`) en cada subida real.
Pensado sobre todo para relanzar la carga masiva sobre la misma
carpeta compartida y que solo suba lo que haya cambiado desde la
última vez.

`POST /admin/articulos` asigna `codigo_dali` en el servidor (siguiente
entero libre, máximo actual + 1) — el formulario no lo pide, coherente
con el texto "Código pendiente de asignar" de `ArticuloForm.jsx`. Con
reintento automático (hasta 5 veces) si dos altas concurrentes chocan
sobre el mismo código. En edición, `codigo_dali` nunca se toca aunque
llegara en el body.

## Pendiente / siguientes pasos

- Verificación por email tras varios días sin login (distinto de la
  recuperación de acceso, ya implementada — ver más arriba y
  `HISTORIAL.md` v1.15; ahora que DALI tiene su propio EmailJS, esto
  podría apoyarse en el mismo `services/emailjsConfig.js`).
- "Documentación faltante" migrar del puente con `control-pedidos-princess`
  al EmailJS propio de DALI, igual que ya se hizo con la recuperación de
  acceso — anotado explícitamente por Víctor como actualización próxima
  al pedir v1.15, no incluido en esta versión.
- Rellenar las credenciales de la **Cuenta 2** de EmailJS en
  Administración → Configuración EmailJS — la Cuenta 1 ya está rellena
  con credenciales reales y confirmada funcionando en producción,
  incluido el envío del aviso a administradores, desde v1.16/v1.38 (ver
  `HISTORIAL.md`). La Cuenta 2 solo entra en juego por rotación
  automática al llegar al umbral de envíos — no bloquea el uso normal
  mientras tanto. Al rellenarla, revisar también en EmailJS.com que
  "Allow API calls" esté activado para esa cuenta/servicio (causa real
  de que el aviso a administradores no llegara pese a tener ya la
  Private Key puesta — ver `HISTORIAL.md` v1.38).
- Tests de integración por endpoint.
