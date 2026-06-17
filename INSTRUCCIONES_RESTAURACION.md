# Restauración de backups — Opción C (cola desacoplada)
© VAMA 2026 — Central Compras Princess Canarias

## Resumen del funcionamiento

```
PANEL WEB (Render)                    TU PC (agente local)
───────────────────                   ──────────────────────────────
Admin entra en "Restaurar backup"
Selecciona un backup de la lista
Pulsa "Solicitar restauración"  ──►   INSERT en restore_queue (pendiente)
                                       
Panel hace polling cada 5s            restore_agent.bat (cada 1 minuto)
"⏳ Pendiente..."                       ¿hay petición pendiente?
                                       SÍ →
                                         Marca 'en_proceso'
"⚙️ Restaurando..."           ◄──        Lee backup de \\shtabaiba\...
                                         Borra datos actuales en Supabase
                                         Inserta datos del backup
                                         Sube adjuntos
                                         Marca 'completado' + resumen
"✅ Completado: 673 pedidos,  ◄──
   310 adjuntos..."
```

Render (donde corre la web) **no tiene acceso** a tu carpeta de red local,
así que nunca ejecuta la restauración directamente. Solo encola la petición.
Quien restaura de verdad es tu PC, a través de `restore_agent.py`.

---

## Archivos de este paquete relacionados con backup/restauración

| Fichero | Dónde se ejecuta | Qué hace |
|---|---|---|
| `backup_pedidos.py` / `.bat` | Tu PC (tarea L-V 17:00) | Genera la copia de seguridad diaria |
| `restore_agent.py` / `.bat` | Tu PC (tarea cada 1 min) | Procesa peticiones de restauración pendientes |
| Panel web → "Restaurar backup" | Render (la nube) | Solo consulta/encola; nunca ejecuta directamente |

---

## 1. Instalación del agente de restauración

### 1.1 Copiar ficheros
Coloca `restore_agent.py` y `restore_agent.bat` en la **misma carpeta**
donde ya tienes el backup, por ejemplo:

```
C:\ComprasPrincess\Backup\
  backup_pedidos.py
  backup_pedidos.bat
  restore_agent.py        ← nuevo
  restore_agent.bat        ← nuevo
```

### 1.2 Configurar credenciales
Abre `restore_agent.bat` y comprueba que la línea `DATABASE_URL` tiene
la misma cadena de conexión que ya usas en `backup_pedidos.bat`. Si la
cambiaste alguna vez (reset de password en Supabase), actualízala en
**ambos** ficheros `.bat`.

---

## 2. Prueba manual

Antes de programarlo, compruébalo a mano:

```
cd C:\ComprasPrincess\Backup
.\restore_agent.bat
```

Si no hay ninguna petición pendiente, verás en `restore_agent.log`:
```
[...] No hay peticiones pendientes.
```

Para probarlo de verdad: entra en el panel web → "Restaurar backup" →
selecciona un backup → "Solicitar restauración" → confirma. Luego ejecuta
`.\restore_agent.bat` manualmente y comprueba que el panel web pasa de
"⏳ Pendiente" a "✅ Completado".

---

## 3. Programador de Tareas de Windows — Agente de restauración

Además de la tarea de backup que ya tienes, crea una **segunda tarea**:

1. `Windows + R` → `taskschd.msc` → Enter
2. **"Crear tarea básica..."**
   - Nombre: `Agente Restauración Control Pedidos`
3. **Desencadenador:**
   - Selecciona **"Diariamente"**
   - Repetir tarea cada: **1 minuto**, durante: **Indefinidamente**
   - (Si el asistente básico no permite "cada 1 minuto", créala con
     cualquier hora de inicio y luego edítala en Propiedades → pestaña
     **Desencadenadores** → editar → marcar "Repetir tarea cada" → 1 minuto
     → "durante" → 1 día, con la casilla de repetición indefinida)
4. **Acción:** Iniciar un programa
   - Programa: `C:\ComprasPrincess\Backup\restore_agent.bat`
   - Iniciar en: `C:\ComprasPrincess\Backup`
5. **Propiedades finales** (igual que con el backup):
   - ✅ Ejecutar tanto si el usuario inició sesión como si no
   - ✅ Ejecutar con privilegios más altos
   - Pestaña Configuración: ✅ Si la tarea ya se está ejecutando, no iniciar
     otra instancia (importante para evitar solapamientos)

> 💡 **Nota:** ejecutarlo cada minuto es ligero — el script comprueba la
> tabla `restore_queue` y, si no hay nada pendiente, termina en menos de
> un segundo. No genera carga apreciable en Supabase ni en tu PC.

---

## 4. Qué pasa si tu PC está apagado

La petición se queda en estado `pendiente` indefinidamente. El panel web
seguirá mostrando "⏳ Esperando a que el agente local la recoja..." hasta
que:
- Enciendas el PC y la tarea programada se ejecute (máx. 1 minuto después
  de iniciar sesión, según configuración de Windows), o
- Ejecutes `restore_agent.bat` manualmente.

No hay timeout automático: la petición espera todo el tiempo que sea
necesario, no se pierde ni se duplica.

---

## 5. Verificar que funciona

- **`restore_agent.log`** en la carpeta del agente — log de cada ciclo
- Tabla `restore_queue` en Supabase (SQL Editor):
  ```sql
  SELECT id, backup_nombre, modo, estado, solicitado_en, completado_en
  FROM restore_queue
  ORDER BY solicitado_en DESC
  LIMIT 10;
  ```
- Panel web → el mensaje de estado se actualiza solo cada 5 segundos

---

## 6. Seguridad y límites

- Solo usuarios con rol **admin** pueden solicitar restauraciones
  (protegido por `@admin_required` en ambas rutas del panel web)
- Solo se permite **una petición pendiente o en proceso a la vez** — si
  intentas solicitar otra mientras hay una en curso, el panel lo bloquea
- El modo **"completo"** intenta conservar al usuario que solicitó la
  restauración; si no lo identifica, conserva todos los usuarios actuales
  por seguridad en lugar de arriesgarse a borrar todas las cuentas
- Cada restauración registra quién la solicitó (`solicitado_por`) y queda
  en el historial de la tabla `restore_queue` para auditoría

---

## 7. Red de seguridad: backup automático previo a cada restauración

Antes de tocar un solo dato, `restore_agent.py` genera **siempre** una
copia de seguridad completa del estado actual con el nombre
`pre_restore_YYYYMMDD_HHMMSS`, guardada en la misma carpeta de red que los
backups diarios. Si la restauración da un resultado inesperado, ese backup
aparece en la lista del panel web (marcado con la etiqueta 🛟 *Seguridad*
en fondo amarillo) y puede restaurarse exactamente igual que cualquier otro.

Si la generación de este backup de seguridad falla por cualquier motivo
(carpeta de red no accesible, disco lleno, etc.), la restauración solicitada
se **aborta sin tocar la base de datos** — nunca se borra nada sin tener
primero una vía de vuelta atrás garantizada.

El nombre del backup de seguridad generado queda también registrado en la
columna `pre_restore_backup` de `restore_queue`, visible en el mensaje de
resultado que muestra el panel web tras completarse la restauración.

---

## 8. Caducidad de peticiones pendientes

Si el agente local lleva parado varios días (PC apagado, sin red, tarea
desactivada...), una petición podría quedarse en estado `pendiente`
indefinidamente, con el panel web mostrando "esperando..." sin fin.

Para evitarlo, cada vez que el agente arranca un ciclo comprueba primero si
hay peticiones `pendiente` con más de **24 horas** de antigüedad. Si las
hay, las marca automáticamente como `error` con un mensaje explicativo, y
el panel web lo refleja de inmediato. Si sigues necesitando esa
restauración, simplemente vuelves a solicitarla desde el panel.

Este plazo es configurable mediante la variable de entorno
`RESTORE_AGENT_CADUCIDAD_HORAS` en `restore_agent.bat` (por defecto 24).

---

## 9. Verificación post-restauración

El resumen que devuelve cada restauración completada incluye siempre un
contador explícito de **errores** (adjuntos que no se pudieron vincular a
ningún pedido, por ejemplo), no solo el recuento de elementos restaurados
correctamente. El panel web lo muestra así:

```
✅ Restauración completada (backup_20260616_1700, modo: pedidos).
Pedidos: 673 | Adjuntos: 310 | Historial: 761 | Errores: 0
🛟 Backup de seguridad previo generado: pre_restore_20260617_090512
```

Si `Errores` es mayor que 0, el mensaje se muestra en amarillo (aviso) en
lugar de verde, y el detalle de los primeros 15 errores queda guardado en
el campo `resumen` de `restore_queue` (columna `errores_detalle`) para
poder consultarlo si hace falta investigar qué falló.

