# Hallazgo de seguridad — contraseñas en texto plano (`control-pedidos-princess`)

**Detectado:** 02/08/2026, al revisar `app.py` como referencia para el
login de este proyecto (DALI).
**Severidad:** Alta.
**Estado:** Sin corregir en el proyecto original a fecha de este documento.

---

## Resumen

El login de `control-pedidos-princess` guarda las contraseñas de los
usuarios **en texto plano** en la base de datos y las compara
directamente, sin ningún tipo de hash. Cualquiera con acceso a la base
de datos, a un backup, o a un volcado accidental en logs, ve las
contraseñas de todos los usuarios tal cual las escribieron.

## Evidencia

**Login** (`app.py`, función `login()`, ~línea 5096):

```python
user = query(
    "SELECT * FROM usuarios WHERE username=%s AND password=%s AND activo=1",
    (username, password), one=True
)
```

La contraseña que escribe el usuario se compara byte a byte contra la
columna `password` de la tabla `usuarios` — si esa columna se puede
leer, se conocen las contraseñas de todo el mundo.

**Cambio de contraseña por reset** (`app.py`, función
`cambiar_password_con_token()`, ~línea 5455):

```python
execute("UPDATE usuarios SET password=%s WHERE id=%s", (nueva, row["usuario_id"]))
```

La nueva contraseña se guarda tal cual, sin hashear, así que el
problema se perpetúa cada vez que alguien resetea la suya.

No hay en todo `app.py` ninguna llamada a una función de hash (no hay
`bcrypt`, `werkzeug.security`, `hashlib` aplicado a la contraseña, ni
nada equivalente) — se ha comprobado con una búsqueda completa del
fichero.

## Impacto

- **Fuga de base de datos o backup** → contraseñas de todos los
  usuarios expuestas directamente, sin ni siquiera tener que
  crackearlas.
- **Reutilización de contraseñas**: si algún usuario reutiliza esa
  misma contraseña en otro sitio (bastante habitual), la fuga no se
  queda solo en esta app.
- **Cualquiera con acceso de lectura a la base de datos** (un
  desarrollador, una herramienta de administración de Supabase/Postgres
  mal configurada, un log de queries) ve contraseñas reales sin
  necesidad de vulnerar nada más.

## Corrección propuesta

Sustituir la columna de texto plano por un hash, y comparar con la
función de verificación correspondiente en vez de `=`:

1. **Añadir `bcrypt` a `requirements.txt`** (o usar
   `werkzeug.security.generate_password_hash` /
   `check_password_hash`, que ya viene con Flask y evita una
   dependencia nueva).

2. **Al dar de alta o cambiar una contraseña**, guardar el hash, no el
   valor recibido:
   ```python
   from werkzeug.security import generate_password_hash
   hash_password = generate_password_hash(nueva)
   execute("UPDATE usuarios SET password=%s WHERE id=%s", (hash_password, row["usuario_id"]))
   ```

3. **En el login**, dejar de filtrar por contraseña en el `SELECT` y
   comparar el hash en Python:
   ```python
   from werkzeug.security import check_password_hash

   user = query(
       "SELECT * FROM usuarios WHERE username=%s AND activo=1",
       (username,), one=True
   )
   if not user or not check_password_hash(user["password"], password):
       return jsonify({"error": "Usuario o contraseña incorrectos"}), 401
   ```

4. **Migrar las contraseñas existentes**: no se puede "hashear" una
   contraseña ya guardada en texto plano de forma retroactiva sin que
   el usuario la vuelva a escribir (es la naturaleza de un hash). Dos
   opciones:
   - Forzar un reset de contraseña a todos los usuarios en el próximo
     despliegue (más simple, más seguro).
   - O, al primer login exitoso tras el despliegue, comparar en texto
     plano una última vez y sustituir inmediatamente por el hash
     (permite una transición sin interrumpir a nadie, pero mantiene la
     columna en texto plano un poco más — usar solo si forzar el reset
     no es viable).

5. Revisar también `INSTRUCCIONES_RESTAURACION.md` / `init_db.py` por
   si crean usuarios iniciales con contraseña en texto plano
   directamente en el script de arranque — habría que aplicar el mismo
   hash ahí.

## Cómo se resolvió en este proyecto (DALI), como referencia

`backend/src/controllers/authController.js` usa `bcrypt.compare()`
contra `usuarios.hash_password`, y `backend/scripts/create-user.js`
hashea con `bcrypt.hash()` antes de guardar — ningún punto del código
guarda ni compara la contraseña en texto plano. Es el mismo patrón que
la corrección propuesta arriba, en Node en vez de Python.
