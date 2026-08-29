# Control Pedidos Princess Canarias

Aplicación web interna para la gestión de pedidos de compras de la
**Central de Compras Princess Canarias** (Princess Hotels & Resort):
alta y seguimiento de pedidos por hotel, control de proveedores, alertas
de plazos, techo de gastos mensual con expedientes de autorización, y
administración de usuarios y familias de artículos.

> Versión actual: **v12.30.51** (ver `CHANGELOG.md` y
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
                        (Supabase + Render + EmailJS + UptimeRobot).
INSTRUCCIONES_RESTAURACION.md  Cómo restaurar un backup de la base de datos.
CAMBIOS_solicitud_directa_backend.md  Notas de un cambio concreto (solicitud
                        directa de acceso), documentación puntual.
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
  por hotel y proveedor.
- **Alertas** — avisos de plazos de entrega vencidos o próximos a vencer.

**Gestión** (admin + compras, y Proveedores también hotel)
- **Proveedores** — ficha de proveedores, contactos múltiples por
  proveedor, asignación a hoteles.
- **Pedidos eliminados** — papelera / auditoría de pedidos borrados.
- **Techo de gastos** — resumen mensual de consumo de techo por hotel
  (semáforo verde/amarillo/rojo/azul), desglose por familia de
  artículos, y expedientes de autorización de exceso (Dirección
  General) cuando un pedido supera el límite.

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
- **Parámetros de alertas** (antes "Config alertas", renombrada
  2026-08-29) — umbrales de plazo y techo, y configuración de las
  cuentas EmailJS.
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
- **Integridad** — comprobaciones de consistencia de datos.
- **Restaurar backup** — gestión de backups de la base de datos.

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

## Puesta en marcha

### Despliegue completo desde cero

Sigue `GUIA_DESPLIEGUE.md` paso a paso (Supabase → EmailJS → Render →
UptimeRobot).

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
