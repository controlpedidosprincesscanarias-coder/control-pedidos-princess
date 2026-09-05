# Control Pedidos Princess Canarias

Aplicación web interna para la gestión de pedidos de compras de la
**Central de Compras Princess Canarias** (Princess Hotels & Resort):
alta y seguimiento de pedidos por hotel, control de proveedores, alertas
de plazos, techo de gastos mensual con expedientes de autorización, y
administración de usuarios y familias de artículos.

> Versión actual: **v12.32.38** (ver `CHANGELOG.md` y
> `docs/HISTORIAL_CAMBIOS.md` para el detalle de cada cambio).

---

## Stack técnico

| Componente | Tecnología |
|---|---|
| Backend | Python 3.12 + Flask (`app.py`, monolito de una sola app) |
| Base de datos | PostgreSQL (Supabase) vía `psycopg2` |
| Frontend | HTML/CSS/JS vanilla en una sola plantilla (`templates/index.html`) — sin build step, sin framework |
| Email | EmailJS, gestionado íntegramente desde el frontend (sin configuración de servidor) |
| Tareas programadas | APScheduler (`BackgroundScheduler`) — alertas, avisos de techo, limpieza |
| Servidor de producción | Gunicorn |
| Despliegue | Render.com (`render.yaml`) |
| Notificaciones | WhatsApp / Telegram / email (según configuración) |

El proyecto **no tiene build step ni dependencias de frontend**: todo el
HTML, CSS y JS de la aplicación vive en `templates/index.html`, servido
directamente por Flask.

---

## Estructura del repositorio

```
app.py                 Backend Flask completo: rutas, lógica de negocio,
                        migraciones automáticas (_auto_migrate), scheduler
                        de alertas y jobs de fondo.
models.py               SQL_STATEMENTS (esquema completo de la BD, solo
                        se usa en el primer despliegue, ver más abajo),
                        constantes de estados de pedido.
init_db.py               Script MANUAL para inicializar una base de datos
                        NUEVA y vacía (primer despliegue). No se ejecuta
                        automáticamente nunca más — ver sección
                        "Migraciones de base de datos" abajo.
templates/index.html     Frontend completo (SPA de una sola página):
                        sidebar, todas las vistas, JS de la aplicación.
static/                  Assets estáticos (logos, iconos).
requirements.txt        Dependencias Python.
render.yaml               Configuración de despliegue en Render.
CHANGELOG.md             Historial de versiones de Control Pedidos
                        (entrada más reciente arriba).
docs/HISTORIAL_CAMBIOS.md Historial unificado de todo el ecosistema
                        Princess Compras (Control Pedidos + Organizador +
                        Chat + Infra), por fecha.
GUIA_DESPLIEGUE.md        Guía paso a paso para desplegar desde cero
                        (Supabase + Render + EmailJS + GitHub Actions).
INSTRUCCIONES_RESTAURACION.md  Cómo restaurar un backup de la base de datos.
```

---

## Funcionalidades principales

Vistas disponibles en el sidebar, agrupadas por bloques (2026-08-29:
reordenado el menú a petición de Víctor — las vistas exclusivas de admin
estaban todas mezcladas sin separación dentro de "Gestión"; ahora cada
bloque agrupa un mismo dominio y lleva "· Admin" en el título cuando es
exclusivo de administración. Es solo una reorganización del menú — ninguna
vista cambió de función ni de ruta, dos se renombraron para dejar de
confundirse entre sí, ver más abajo):

**Principal** (todos los roles)
- **Pedidos** — alta, edición, cambio de estado y seguimiento de pedidos
  por hotel y proveedor. El apartado "Presupuesto" admite un único
  documento de apoyo (PDF, Word o correo) — desde v12.32.08, intentar
  adjuntar un segundo muestra un aviso flotante explicando que hay que
  quitar el actual primero. El Proveedor ya no se busca/selecciona a
  mano — desde v12.32.35 se lee y asigna solo al adjuntar el PDF del
  pedido oficial en «Nº Pedido (DALI/SAP)» (igual que Nº Pedido/Total
  Pedido); si no se reconoce en el catálogo, avisa con el código/nombre
  leídos para verificarlo/darlo de alta en Admin → Proveedores. El
  Departamento seleccionado se verifica contra el "Almacén" de ese
  mismo PDF — si no coincide, avisa y bloquea el paso a ENVIADO AL
  PROVEEDOR hasta corregirlo. Control de duplicados (v12.32.36): el Nº
  de Pedido leído del PDF no puede coincidir con el de otro pedido ya
  registrado en el mismo hotel — se rechaza al adjuntar el PDF, con una
  segunda comprobación de seguridad al pasar a ENVIADO AL PROVEEDOR. El
  Hotel seleccionado se verifica también (v12.32.38) contra el
  "HOTEL/CENTRO" de cabecera de ese mismo PDF — si no coincide, avisa y
  bloquea igualmente el paso a ENVIADO AL PROVEEDOR hasta corregirlo
  (evita registrar y tramitar un pedido en el hotel equivocado).
- **Alertas** — avisos de plazos de entrega vencidos o próximos a vencer.

**Gestión** (admin + compras, y Proveedores también hotel)
- **Proveedores** — ficha de proveedores, contactos múltiples por
  proveedor, asignación a hoteles.
- **Comparar Pedidos + Albaranes (SAP)** (admin, botón "📄 Comparar
  listado PDF" — base desde 2026-08-06, ampliada desde entonces) — la
  herramienta admite subir hasta dos PDF que exporta SAP para un hotel:
  - **Listado de Pedidos** (simplificado, una línea por pedido, siempre
    obligatorio salvo la excepción de más abajo): se comparan todos los
    números de pedido contra los ya dados de alta en la app, para
    detectar compras hechas en SAP sin registrar aquí, y se deduce el
    estado de entrega de cada uno (Entregado / Entrega parcial / No
    entregado) comparando importe del pedido vs. importe recibido. De
    paso, sin pedir confirmación (no cambia estado ni dispara avisos):
    rellena `Total Pedido`, la base imponible de la última entrada ya
    registrada, y la fecha de tramitación si estaba vacía. Los
    proveedores marcados como "no sujetos a seguimiento" (ficha de
    Proveedores — pensado para alimentación/bebida) quedan excluidos
    del todo. Desde v12.32.10, este listado se guarda por hotel al
    subirlo, así que las comparaciones siguientes con Albaranes pueden
    omitirlo y reutilizar el último guardado.
  - **+ Comparar también con el listado de Albaranes** (casilla
    opcional, DALI, desde 2026-08-15): cruza el importe YA RECIBIDO de
    cada pedido que SAP marca Entregado/Entrega parcial con el importe
    de cada albarán del segundo PDF — al coincidir proveedor e importe,
    propone (nunca aplica solo) registrar fecha de tramitación, número
    de entrada del albarán y cambio de estado; hay que confirmar cada
    coincidencia con "Aplicar" antes de que se guarde nada. Un cambio de
    estado aplicado así dispara el mismo correo interno y aviso de
    Telegram/popup que un cambio manual (con los mismos destinatarios;
    solo cambia que no se excluye a nadie, y que el correo se despacha
    casi al instante en vez de esperar los 5 min habituales), y queda
    marcado en el Historial de estados como "Automática — listado
    comparativo pedidos y albaranes" en vez del nombre de quien pulsó
    "Aplicar". Empates (mismo proveedor+importe con más de un candidato)
    nunca se autorregistran — quedan para decisión manual. Desde
    v12.32.20, además de esas sugerencias por proveedor+importe, hay un
    nivel "confirmado" que no depende de coincidir por importe: a partir
    de un PDF de confirmación de un albarán suelto (que SAP sí puede
    imprimir para un único albarán, con el pedido asociado ya indicado),
    o directamente del número de albarán que ya se hubiera anotado a
    mano en el propio pedido al registrar una entrega.
  - Los pedidos que SAP ya tiene y la app todavía no se pueden
    seleccionar y crear automáticamente con un clic (v12.32.11) — con el
    estado inicial real de SAP (no siempre "Enviado al proveedor") y
    trazabilidad marcada como automática, no con el nombre del admin;
    esta opción solo se ofrece al procesar el Listado de Pedidos, nunca
    al comparar solo Albaranes (v12.32.12/13).
  - Botón aparte "🏷️ Departamentos (SAP detallado)" (v12.32.19): a
    partir de un segundo tipo de listado SAP, más detallado (una línea
    por artículo, con el departamento solicitante), rellena
    automáticamente el departamento de los pedidos que ya tienen fila
    guardada del listado simplificado — nunca toca importe ni estado, y
    nunca da de alta pedidos nuevos.
  - Cada comparación puede enviarse como correo de resumen a los
    destinatarios configurados, con el detalle de pedidos sin dar de
    alta, registrados automáticamente y pendientes de revisar a mano.
- **Pedidos eliminados** — papelera / auditoría de pedidos borrados.
- **Techo de gastos** — resumen mensual de consumo de techo por hotel
  (semáforo verde/amarillo/rojo/azul), desglose por familia de
  artículos, y expedientes de autorización de exceso (Dirección
  General) cuando un pedido supera el límite. Los propios límites en €
  se configuran aquí mismo, en un bloque "⚙️ Límites de Techo de Gastos"
  visible solo para admin (movido el 2026-08-29 desde "Parámetros de
  alertas", donde vivía sin relación visible con esta pantalla — mismas
  claves y mismo endpoint de siempre, solo cambió dónde se edita).
  Botón "⬇ Exportar histórico" (2026-09-01) junto al de "🖨️ Imprimir":
  descarga en Excel el histórico completo de expedientes de exceso de
  techo — todos los hoteles y meses, no solo el mes en pantalla.

**Datos maestros · Admin**
- **Familias de artículos** — categorías usadas para agrupar pedidos y
  aplicar límites de techo por familia.

**Alertas y notificaciones · Admin**
- **Departamentos** (2026-08-28): correo de contacto por hotel para cada
  departamento (el mismo departamento puede tener un correo distinto en
  cada hotel). El correo interno de cambio de estado de un pedido se
  envía con copia al correo del departamento que lo solicitó, si está
  registrado aquí.
- **Notificaciones adicionales** (2026-08-28): contactos sueltos que no
  son usuarios de la app (p. ej. Chef Ejecutivo, Director de Compras,
  Administrativo A&B), globales para toda la cadena, a los que se pone
  en copia en el correo interno de cambio de estado según el
  departamento del pedido y el estado nuevo concreto (p. ej. Cocina +
  ENVIADO AL PROVEEDOR → copia al Chef Ejecutivo). Incluye también una
  columna extra, independiente de las de estado real, para poner en copia
  a un contacto específicamente cuando el pedido enviado había superado
  el techo de gastos del mes y tuvo que pasar por autorización de
  Dirección General — en ese caso, además, el propio correo interno de
  cambio de estado explica el motivo de la superación, la familia, los
  importes y quién y cuándo lo autorizó, y llega igual a todos los
  destinatarios internos ya configurados (comprador, rol hotel,
  departamento y contactos adicionales).
- **Correo interno de cambio de estado** (ENVIADO AL PROVEEDOR / ENTREGA
  PARCIAL / ENTREGADO): además del cuadro de datos y el histórico de
  entregas, desde 2026-08-31 incluye un botón para descargar/visualizar
  el PDF del pedido tramitado (mismo enlace público y temporal que el
  correo al proveedor) — hasta 2026-09-02 solo aparecía en ENVIADO AL
  PROVEEDOR. Desde v12.30.94, ese mismo botón se muestra también en
  ENTREGA PARCIAL y ENTREGADO, y el párrafo introductorio pasa a ser
  dinámico: en ENTREGA PARCIAL indica el importe de la entrega
  registrada y el importe pendiente sobre el total del pedido; en
  ENTREGADO confirma la entrega total y el número de días transcurridos
  desde la tramitación del pedido (contando las entregas parciales
  intermedias si las hubo). La tabla de histórico de entregas del correo
  suma una columna "Días desde pedido" con ese mismo dato por cada
  entrada (parcial o final). Quien realiza el cambio de estado no
  recibe este correo con su email principal (ya sabe lo que acaba de
  hacer), pero si esa cuenta tiene un segundo correo (`email2`,
  Usuarios → ficha de usuario) configurado como correo de control, ese
  segundo correo sigue recibiéndolo siempre, para los hoteles
  asignados a la cuenta, con independencia de quién haya hecho el
  cambio (v12.30.97). Cuando el cambio de estado lo aplica el propio
  sistema automáticamente (al confirmar "Aplicar" en "Comparar
  Pedidos + Albaranes") en vez de una persona en ese momento, este
  correo se envía igual — mismos destinatarios, mismo contenido —
  con dos diferencias: no se excluye a nadie (no hay "quien hizo el
  cambio" que ya lo sepa de antemano), y desde v12.30.99 se despacha
  prácticamente al instante en vez de esperar los 5 min habituales
  (el retraso existe para agrupar varias ediciones manuales seguidas
  sobre el mismo pedido, algo que no aplica a un cambio automático) —
  el propio botón "Aplicar" adelanta el envío igual que ya hacía
  "Enviar resumen", sin depender de que alguien deje la app abierta
  varios minutos más. Llega a comprador, rol hotel, departamento y
  contactos adicionales configurados, igual que un cambio manual. En
  el Historial de estados del pedido, este tipo de registro aparece
  con la etiqueta "Automática — listado comparativo pedidos y
  albaranes" en vez del nombre de quien pulsó "Aplicar", para
  distinguirlo a simple vista de un cambio hecho a mano
  (v12.30.16/17/18/19/99).
- **Parámetros de alertas** (antes "Config alertas", renombrada
  2026-08-29) — umbrales de plazo de entrega, cotización, firma y
  repetición de popups. Ya NO incluye los límites de techo (ver
  "Gestión" arriba) ni la configuración de EmailJS (ver "Sistema"
  abajo) — se sacaron de aquí el 2026-08-29 por no tener relación con
  umbrales de alerta.
- **Avisos por usuario** (antes "Config. Avisos", renombrada
  2026-08-29) — quién recibe cada aviso automático (Telegram/popup/email)
  por evento. Se renombraron estas dos porque sus nombres anteriores
  ("Config alertas" / "Config. Avisos") eran casi sinónimos en español y
  se confundían con facilidad; siguen siendo la misma pantalla y la misma
  funcionalidad de siempre.

**Usuarios y accesos · Admin**
- **Usuarios** — alta/edición de usuarios, roles y asignación de
  hoteles.

**Sistema · Admin**
- **Integridad** — comprobaciones de consistencia de datos. Incluye,
  desde v12.32.05, "Telegram bloqueado o inservible": se marca sola
  cuando Telegram deja de poder entregar avisos a un usuario (bot
  bloqueado, cuenta desactivada, chat borrado) y desaparece sola en
  cuanto vuelve a recibir uno con éxito — no requiere que un admin la
  resuelva a mano, solo que el usuario desbloquee el bot por su lado.
- **EmailJS y cola de correo** (movida aquí el 2026-08-29 desde
  "Parámetros de alertas", donde estaba mezclada con umbrales de alerta
  sin relación con esto) — credenciales y rotación automática de las 4
  cuentas EmailJS, cupo consumido, y la cola de correos de sistema
  pendientes de enviar (con la opción de descartar/reactivar a mano una
  fila atascada). Mismo endpoint de siempre (`/api/admin/config-alertas`),
  solo cambió dónde se edita. Desde v12.30.89, una fila que sí llegó a
  enviarse de verdad pero cuya confirmación en BD falló se distingue con
  "✅ se envió, sin confirmar en BD" y un botón "Marcar como enviado" —
  nunca "Reactivar" para estas, que sí reenviaría el correo de verdad.
  Desde v12.30.90, las filas "paradas" (agotaron reintentos) de ANTES de
  que existiera esa distinción también pueden cerrarse con el mismo botón
  "✅ Marcar como enviado" (junto a "Descartar"), para los casos en que el
  admin ya ha confirmado por otra vía (p. ej. Gmail) que el correo sí se
  entregó — aplica las marcas de "Comunicado A&B"/"Comunicado Jefe Dep."
  igual que si se hubiera confirmado a la primera. Desde v12.30.91, ese
  mismo botón está disponible también para filas ya descartadas a mano
  (junto a "Reactivar") — a diferencia de "Reactivar", "Marcar como
  enviado" nunca reenvía el correo, solo cierra el registro. Desde
  v12.30.92, las 3 fechas "Reinicia cupo el" (una por cuenta EmailJS)
  ya no hay que actualizarlas a mano cada mes: un job diario (06:00,
  todos los días) las avanza solo +30 días en cuanto se cumplen, así
  el panel siempre muestra la próxima fecha real sin entrar a
  EmailJS.com. Desde v12.30.93, son 4 cuentas en rotación (1 principal,
  2 secundaria, 3 terciaria, 4 backup) en vez de 3 — mismo mecanismo,
  con una tarjeta más que rellenar de la misma forma que las otras.
- **Restaurar backup** — gestión de backups de la base de datos.
- **Aviso de nueva versión** (todos los roles, al detectar un despliegue
  nuevo en el servidor) — modal de recarga obligatoria (con cuenta atrás
  de 5 min). Desde v12.30.98, a petición de Víctor ("el exceso de
  información aturde al usuario"), solo el rol `admin` ve las notas de
  versión completas (`CHANGELOG.md` con petición/diagnóstico/cambio); el
  resto de roles ve únicamente el título-resumen de una línea de la
  última entrada, sin entrar en detalles — en ambos casos el único botón
  disponible sigue siendo "Recargar ahora".

### Roles de usuario

- `admin` — acceso completo a todas las vistas y hoteles.
- `compras` — gestión de pedidos con hoteles asignados.
- `hotel` — acceso limitado a su propio hotel; sin acceso a Techo de
  Gastos ni a vistas de administración.
- `user` — rol genérico adicional usado en algunos flujos de permisos.

---

## Migraciones de base de datos — cómo funciona (importante)

Este es el punto que más ha dado problemas históricamente (ver
`CHANGELOG.md` v12.29.32 y v12.29.33), así que conviene tenerlo claro:

- **`models.py` → `SQL_STATEMENTS`**: define el esquema completo
  (`CREATE TABLE IF NOT EXISTS ...`) pensado para un despliegue **desde
  cero**, sobre una base de datos nueva y vacía. **Solo se ejecuta a
  mano**, corriendo `python init_db.py` (requiere `DATABASE_URL` en el
  entorno). Nadie vuelve a ejecutar este script sobre una base de datos
  de producción ya existente.
- **`app.py` → `_auto_migrate()`**: función que **sí se ejecuta
  automáticamente en cada arranque del servidor** (`with
  app.app_context(): _auto_migrate()`, justo después de definir la
  función). Aquí es donde deben vivir todas las migraciones idempotentes
  (`ALTER TABLE ... ADD COLUMN IF NOT EXISTS`, `CREATE TABLE IF NOT
  EXISTS`, `INSERT ... ON CONFLICT DO NOTHING`) para que se apliquen
  solas al desplegar, sin pasos manuales.

**Regla práctica:** cualquier cambio de esquema nuevo (tabla, columna,
índice, fila de configuración por defecto) debe añadirse **también**
dentro de `_auto_migrate()` en `app.py`, no solo en `SQL_STATEMENTS`
(`models.py`) — de lo contrario nunca llegará a aplicarse en producción,
aunque el código que depende de ese cambio de esquema sí esté
desplegado. Esto ya ha causado dos bugs reales (hotel de pruebas "PR" en
v12.29.32, tabla `expediente_exceso` en v12.29.33).

---

## Rendimiento

La app se ha auditado y optimizado por etapas (agosto-septiembre 2026,
ver `CHANGELOG.md` para el detalle técnico completo de cada una):

- **Etapa 1 (v12.30.70)** — `GET /api/proveedores` pasó a paginar (antes
  devolvía siempre la tabla completa) y se crearon índices GIN por
  trigramas (extensión `pg_trgm`) sobre `proveedores.nombre/codigo/codigo_dali`,
  para que el buscador (`ILIKE '%texto%'`, comodín al principio) deje de
  recorrer la tabla entera en cada búsqueda.
- **Etapa 2 (v12.30.71)** — mismo problema de índice, ahora en
  `pedidos.pedido_num` y `pedidos.observaciones` — la tabla que más
  rápido crece de toda la app.
- **Etapa 3 (v12.30.72)** — compresión gzip de las respuestas del
  servidor (`_comprimir_respuesta_gzip()` en `app.py`): `index.html`
  (628 KB) y el JSON de la API viajan hasta un 80-90% más ligeros. No
  se usó Flask-Compress — ver el porqué en el propio CHANGELOG.
- **Cierre de un punto pendiente de la Etapa 2 (v12.30.82-83)** — el
  respaldo `proveedor_email` (usado en `PEDIDO_SELECT` y otras 3
  consultas donde se repite) pasó a ser determinista cuando un
  proveedor tiene varios contactos "principal" a la vez, y a respetar
  el hotel del pedido — el criterio de desempate que quedaba pendiente
  aquí abajo ya está decidido y aplicado.
- **Etapa 4 (v12.30.85)** — índices B-tree en `pedidos` (`hotel_id`,
  `estado`, `departamento_id`, `fecha_solicitud`, `creado_en`, `norden`,
  `fecha_tramitacion`) y en `historial_estados.pedido_id`: el listado
  principal de Pedidos (filtro + orden + su propio `COUNT` de
  paginación) y el detalle de cada pedido dejaron de recorrer la tabla
  entera en cada petición.

Estas etapas se apoyan en el trabajo previo de v12.7.0 (pool de
conexiones psycopg2, en vez de abrir una conexión nueva por petición) y
del "Fix egress" de julio 2026 (`index.html` se sirve con ETag +
`Cache-Control: no-cache`, así que el navegador revalida con una
petición condicional ligera en vez de descargar el archivo entero en
cada recarga).

- **Etapa 5 (v12.30.86)** — la vista "Eliminados" (papelera de pedidos)
  pasó a paginar igual que Proveedores/Pedidos: `GET
  /api/pedidos_eliminados` devolvía la tabla completa sin límite (un
  histórico que nunca se purga, solo crece), y a diferencia de los
  índices de la Etapa 4 esto sí reduce egress de Supabase de verdad, no
  solo velocidad.

- **Etapa 6 (v12.30.87)** — nuevo botón "⬇ Exportar histórico" en Techo
  de Gastos (`GET /api/expedientes/exportar`): Excel profesional del
  histórico completo de expedientes de exceso de techo, a petición de
  Víctor. `GET /api/expedientes` (el listado en bruto sin este Excel) se
  confirmó que no lo usa nada en el frontend actual — la pantalla que
  iba a necesitarlo (Fase 6) nunca se construyó — así que se deja como
  está en vez de paginarlo; el histórico completo ahora se consulta a
  través del botón de exportar, no de esa dirección.

- **Etapa 7 (v12.30.88, última del repaso "agilizar y limpiar")** —
  `loadUsuarios()` (pestaña Usuarios · Admin) hacía una petición HTTP
  por cada usuario con hoteles asignados más una llamada redundante a
  `/api/maestros` (ya cargado en `G.maestros` desde el arranque de la
  app) — con 40 usuarios, ~40 peticiones solo para pintar esa tabla.
  Nuevo `GET /api/usuarios/hoteles-asignados` trae las asignaciones de
  todos los usuarios de una sola vez; los endpoints por usuario
  (`GET /api/usuarios/<id>/hoteles[-compras]`) se mantienen tal cual,
  los sigue usando el modal de edición de un usuario concreto.

Con esto se cierran las 7 etapas del repaso "agilizar y limpiar"
(v12.30.85-88) iniciado a petición de Víctor.

---

## Puesta en marcha

### Despliegue completo desde cero

Sigue `GUIA_DESPLIEGUE.md` paso a paso (Supabase → EmailJS → Render →
GitHub Actions).

### Desarrollo local (resumen rápido)

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

export DATABASE_URL="postgresql://..."   # Supabase u otra Postgres
export SECRET_KEY="una-cadena-aleatoria-larga"

# Solo la primera vez, sobre una base de datos nueva y vacía:
python init_db.py

python app.py
```

En producción se usa Gunicorn (ver `render.yaml`):

```bash
gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 300
```

### Variables de entorno

| Variable | Obligatoria | Descripción |
|---|---|---|
| `DATABASE_URL` | Sí | Cadena de conexión PostgreSQL (Supabase) |
| `SECRET_KEY` | Sí | Clave de sesión Flask — debe coincidir con la del servicio de Chat si se usa |
| `RESEND_API_KEY` | No | Envío de emails desde backend (opcional) |
| `EMAIL_FROM` | No | Remitente de emails del sistema |
| `EMAILS_INTERNOS` | No | Lista de emails internos separados por coma |

---

## Convenciones del proyecto

- **Un único commit de versión por cambio funcional**: cada corrección o
  nueva funcionalidad sube el número de versión (`vMAJOR.MINOR.PATCH`,
  visible en el badge del sidebar, `templates/index.html`) y añade una
  entrada en `CHANGELOG.md` (específico de Control Pedidos) y en
  `docs/HISTORIAL_CAMBIOS.md` (historial unificado del ecosistema,
  organizado por fecha).
- **Migraciones siempre en `_auto_migrate()`** (ver sección anterior),
  nunca solo en `models.py`.
- No hay suite de tests automatizados en este proyecto — la
  verificación de cada cambio se documenta en el propio changelog
  (compilación sin errores, comprobación manual del flujo afectado,
  etc.).

---

## Documentos relacionados

- `CHANGELOG.md` — historial de versiones de Control Pedidos.
- `docs/HISTORIAL_CAMBIOS.md` — historial unificado de todo el
  ecosistema (Control Pedidos + Organizador + Chat + Infra).
- `GUIA_DESPLIEGUE.md` — guía de despliegue completa desde cero.
- `INSTRUCCIONES_RESTAURACION.md` — restauración de backups.
