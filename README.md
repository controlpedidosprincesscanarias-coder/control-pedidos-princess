# Control Pedidos Princess Canarias

Aplicación web interna para la gestión de pedidos de compras de la
**Central de Compras Princess Canarias** (Princess Hotels & Resort):
alta y seguimiento de pedidos por hotel, control de proveedores, alertas
de plazos, techo de gastos mensual con expedientes de autorización, y
administración de usuarios y familias de artículos.

> Versión actual: **v12.29.82** (ver `CHANGELOG.md` y
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

Vistas disponibles en el sidebar (algunas restringidas por rol):

- **Pedidos** — alta, edición, cambio de estado y seguimiento de pedidos
  por hotel y proveedor.
- **Alertas** — avisos de plazos de entrega vencidos o próximos a vencer.
- **Proveedores** — ficha de proveedores, contactos múltiples por
  proveedor, asignación a hoteles.
- **Pedidos eliminados** — papelera / auditoría de pedidos borrados.
- **Techo de gastos** — resumen mensual de consumo de techo por hotel
  (semáforo verde/amarillo/rojo/azul), desglose por familia de
  artículos, y expedientes de autorización de exceso (Dirección
  General) cuando un pedido supera el límite.
- **Familias de artículos** — categorías usadas para agrupar pedidos y
  aplicar límites de techo por familia.
- **Usuarios** — alta/edición de usuarios, roles y asignación de
  hoteles.
- **Integridad** — comprobaciones de consistencia de datos.
- **Config alertas** / **Config avisos** — parámetros de alertas de
  plazo y techo, y configuración de avisos automáticos.
- **Restaurar backup** — solo admin, gestión de backups de la base de
  datos.

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
