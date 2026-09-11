import { mockArticulos } from "../data/mockArticulos.js";

// Define VITE_API_URL en un .env para conectar contra el backend real
// (ver /backend). Sin esa variable, la app funciona en modo demo con
// datos de muestra reales de tu catálogo.
const API_URL = import.meta.env.VITE_API_URL || null;

export const isDemoMode = !API_URL;

// La auth va por cookie de sesión (credentials: "include" en cada
// fetch), no por token en cabecera — el navegador la envía solo. Ver
// backend/src/server.js (cookie-session) y src/middleware/auth.js.
const FETCH_OPTS = { credentials: "include" };

// (2026-08-17) Límite propio para las llamadas que deciden si se
// enseña "Comprobando sesión…"/el login o ya se entra a la app
// (fetchSesionActual, login, ssoLogin) — sin esto, un `fetch` sin
// respuesta se queda pendiente hasta que el propio navegador/SO se
// rinda por su cuenta (minutos, no segundos, y en algunos casos nunca
// de forma perceptible), dejando a quien esté mirando la pantalla sin
// ninguna forma de saber qué pasa ni de reintentar.
//
// (2026-08-22) Subido de 20s a 100s (ver HISTORIAL v0.60): 20s parecía
// de sobra para una respuesta normal (<1s), pero es MUCHO más corto que
// un cold-start real de Render en el plan free (~60s documentados, a
// veces más) — así que cualquier primer acceso del día, sobre todo
// entrando por el enlace de SSO desde control_pedidos, abortaba casi
// siempre antes de que el backend llegara a responder, aunque el
// backend fuera a responder bien poco después. 100s da margen real a un
// cold-start lento (y queda por debajo de los ~150s que ahora acepta el
// token de SSO — ver SSO_MARGEN_RELOJ_SEGUNDOS en authController.js —
// para no esperar más de lo que el propio token permite) sin dejar al
// usuario esperando de verdad varios minutos si el problema es otro
// (backend caído, incidente de infraestructura, etc.).
const TIMEOUT_SESION_MS = 100000;

// (2026-08-22) A partir de qué espera se considera "larga" y vale la
// pena avisar de que puede deberse a un cold-start, en vez de dejar la
// pantalla de "Comprobando sesión…" en silencio sin más explicación que
// antes (ver App.jsx). Por debajo de esto no se dice nada — la inmensa
// mayoría de las comprobaciones responden en bien menos de un segundo,
// y avisar siempre de "puede tardar" ahí solo generaría ruido/dudas sin
// necesidad.
export const ESPERA_LARGA_AVISO_MS = 4000;

// (2026-08-17) Mismo motivo que arriba pero para el mensaje de error:
// se centraliza aquí porque login(), ssoLogin() y fetchSesionActual()
// necesitan el mismo texto según el tipo de fallo (timeout vs red
// caída), y así no queda cada una con su redacción propia.
function mensajePorFalloDeRed(e) {
  return e.name === "AbortError"
    ? "El servidor ha tardado demasiado en responder (más de un minuto y medio) — puede haber un problema de verdad, no solo estar despertando. Inténtalo de nuevo en un momento."
    : "No se pudo conectar con el servidor. Comprueba tu conexión e inténtalo de nuevo.";
}

/** Como fetch(), pero aborta con AbortError si tarda más de `ms`. */
async function fetchConTimeout(url, opciones, ms) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), ms);
  try {
    return await fetch(url, { ...opciones, signal: controller.signal });
  } finally {
    clearTimeout(timeoutId);
  }
}

// Copia mutable en memoria de los artículos, usada SOLO en modo demo para
// que el panel de administración (alta/edición/baja) tenga algo real sobre
// lo que operar sin necesidad de backend. Se pierde al recargar la página.
let demoArticulos = mockArticulos.map((a) => ({ ...a }));

// Credenciales de demo (solo existen en memoria del navegador, modo demo).
// En un backend real estas contraseñas estarían hasheadas — ver
// backend/scripts/create-user.js para dar de alta usuarios reales.
const DEMO_USUARIOS = [
  { email: "admin@demo.dali", password: "admin123", nombre: "Admin (demo)", rol: "admin" },
  { email: "hotel@demo.dali", password: "hotel123", nombre: "Hotel (demo)", rol: "hotel" },
];

// (2026-09-03) Permisos granulares por apartado de "Gestión" — a
// petición de Víctor. Mismas 8 claves que `PERMISOS_VALIDOS` en
// backend/src/controllers/usuariosController.js y que las opciones de
// UsuarioForm.jsx. En modo demo no hay concepto real de "administrador
// principal" (solo hay una cuenta admin fija, DEMO_USUARIOS) — para no
// tener que simular todo el circuito de permisos aquí, la cuenta admin
// de demo se trata siempre como administrador principal (acceso a
// todo), igual que se comportaba la app entera antes de este cambio.
const PERMISOS_TODOS = [
  "admin-articulos",
  "admin-importar",
  "admin-usuarios",
  "admin-documentacion",
  "admin-proveedores",
  "admin-exportar-zip",
  "admin-solicitudes-acceso",
  "admin-configuracion-emailjs",
];
// Copia mutable en memoria de la lista de usuarios, usada SOLO en modo
// demo para que la pantalla de administración de usuarios tenga algo
// real sobre lo que operar. Independiente de DEMO_USUARIOS (esa es la
// lista fija con la que se puede iniciar sesión en demo) — dar de alta
// un usuario aquí no permite luego entrar con él, es solo para probar
// la pantalla. Se pierde al recargar la página.
let demoListaUsuarios = DEMO_USUARIOS.map((u, i) => ({
  id: `demo-${i}`,
  nombre: u.nombre,
  email: u.email,
  rol: u.rol,
  activo: true,
  creado_en: new Date().toISOString(),
  // (2026-09-03) es_admin_principal se deja siempre false aquí — en
  // demo, "quién puede gestionar permisos" lo decide la SESIÓN activa
  // (ver login()/demoSesion.esAdminPrincipal más abajo, siempre true
  // para la cuenta admin de demo), no esta fila de la lista.
  es_admin_principal: false,
  permisos: u.rol === "admin" ? PERMISOS_TODOS : [],
}));
let demoUsuarioIdSeq = demoListaUsuarios.length;
let demoSesion = null;

// (2026-09-02) "¿Has olvidado tu contraseña?" + solicitudes de acceso —
// copia mutable en memoria, mismo criterio que demoListaUsuarios. Se
// arranca con una solicitud pendiente ya puesta para que la pantalla de
// Administración → Solicitudes de acceso no se vea vacía la primera vez
// que se prueba en demo, igual que demoListaUsuarios ya arranca con las
// cuentas de DEMO_USUARIOS en vez de una lista vacía.
let demoSolicitudesAcceso = [
  {
    id: "demo-solicitud-0",
    nombre: "Persona de prueba (demo)",
    email: "prueba@demo.dali",
    estado: "pendiente",
    creado_en: new Date().toISOString(),
    resuelto_en: null,
  },
];
let demoSolicitudIdSeq = demoSolicitudesAcceso.length;

// (2026-09-02, v1.15) Enlaces de un solo uso — copia mutable en memoria,
// mismo criterio que demoListaUsuarios/demoSolicitudesAcceso. Sustituye
// a la contraseña temporal simulada que había antes (HISTORIAL v1.14):
// recuperarAcceso()/aceptarSolicitudAcceso() en demo generan aquí un
// token "de mentira" y devuelven el enlace completo (con
// window.location.origin, para que funcione de verdad al pegarlo en la
// misma pestaña — ver enlaceTokenDemo más abajo), y
// validarTokenAcceso()/canjearTokenAcceso() lo consultan igual que
// harían contra la tabla `tokens_acceso` real.
let demoTokensAcceso = []; // { token, usuarioEmail, nombre, rol, tipo, usado }

// (2026-09-02, v1.15) Configuración EmailJS de DALI — copia mutable en
// memoria para poder probar la pantalla de Administración →
// Configuración EmailJS sin backend. Sin credenciales por defecto
// (`configurado: false`, ver obtenerConfigEmailjs más abajo) — en modo
// demo nunca se llega a enviar nada por EmailJS de verdad, ver
// services/emailjs.js.
let demoConfigEmailjs = {
  cuenta_activa: 1,
  contador: 0,
  umbral_cambio: 195,
  public_key_1: "",
  service_id_1: "",
  template_id_1: "",
  // (2026-09-05, v1.19.53) `private_key_N` — el backend la usa para
  // llamar a la API REST de EmailJS directamente desde el servidor al
  // enviar el aviso a administradores (ver services/emailjsConfig.js);
  // no interviene en nada de lo que hace este archivo en modo demo, se
  // replica aquí solo para que el formulario de Administración →
  // Configuración EmailJS tenga el mismo shape en demo que en real.
  // (2026-09-05, v1.19.54) Ya no hay `template_id_admin_N` — el aviso a
  // administradores reutiliza `template_id_N`, el mismo de siempre.
  // (2026-09-09/10) "Documentación faltante" (correo a proveedor) también
  // reutiliza `template_id_N` — ver services/emailjs.js
  // (enviarProveedorPorEmailjs) y HISTORIAL.md v1.44.
  private_key_1: "",
  public_key_2: "",
  service_id_2: "",
  template_id_2: "",
  private_key_2: "",
  actualizado_en: new Date().toISOString(),
};

/** Enlace completo de un token de acceso "de mentira" — ver demoTokensAcceso. */
function enlaceTokenDemo(token) {
  return `${window.location.origin}${window.location.pathname}?token_acceso=${token}`;
}

function generarTokenDemo() {
  return `demo-${Math.random().toString(36).slice(2, 10)}${Date.now().toString(36)}`;
}

function delay(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function siguienteCodigoDemo() {
  const maximo = demoArticulos.reduce((m, a) => Math.max(m, Number(a.codigo_dali) || 0), 0);
  return maximo + 1;
}

/**
 * POST /auth/login
 *
 * (2026-08-17) Igual que fetchSesionActual (ver TIMEOUT_SESION_MS más
 * arriba): sin timeout propio, un backend dormido/caído dejaba este
 * `fetch` pendiente hasta que el navegador se rindiera por su cuenta —
 * el botón de "Entrar" se quedaba en "Entrando…" indefinidamente, sin
 * ningún mensaje. Con esto, como mucho 20s antes de un error legible.
 */
export async function login(email, password) {
  if (!API_URL) {
    await delay(300);
    const usuario = DEMO_USUARIOS.find(
      (u) => u.email === email.trim().toLowerCase() && u.password === password
    );
    if (!usuario) throw new Error("Email o contraseña incorrectos.");
    demoSesion = {
      nombre: usuario.nombre,
      email: usuario.email,
      rol: usuario.rol,
      esAdminPrincipal: usuario.rol === "admin",
      permisos: usuario.rol === "admin" ? PERMISOS_TODOS : [],
    };
    return demoSesion;
  }

  let res;
  try {
    res = await fetchConTimeout(
      `${API_URL}/auth/login`,
      {
        ...FETCH_OPTS,
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      },
      TIMEOUT_SESION_MS
    );
  } catch (e) {
    throw new Error(mensajePorFalloDeRed(e));
  }
  const body = await res.json();
  if (!res.ok) throw new Error(body.error || "Error al iniciar sesión.");
  return body.usuario;
}

/**
 * POST /auth/sso — inicio de sesión automático llegando desde el menú
 * lateral "Catálogo DALI" de control_pedidos (ver App.jsx, que detecta
 * ?dali_token= en la URL al cargar y llama a esto en vez de mostrar el
 * login). No existe en modo demo: no hay backend real que verifique el
 * token.
 *
 * (2026-08-17) FIX: este era el único de los tres inicios de sesión
 * (junto a fetchSesionActual y login) que se había quedado SIN timeout
 * propio al arreglar el bloqueo de "Comprobando sesión…" (ver
 * HISTORIAL v0.33) — y es precisamente la vía por la que se suele
 * entrar a DALI desde control_pedidos. Si el backend estaba
 * dormido/caído justo al llegar por ese enlace, este `fetch` se podía
 * quedar colgado indefinidamente (sin límite propio ni el del
 * navegador llegando a disparar en un tiempo razonable), reproduciendo
 * exactamente el mismo "Comprobando sesión…" congelado que se había
 * dado por arreglado — el aviso de Víctor de que "SE SIGUE QUEDANDO
 * ASI CUANDO PASAMOS RATO SIN ENTRAR" encaja con esto: pasar un rato
 * sin entrar es justo lo que deja al backend (Render Free) dormido,
 * y volver a entrar por el enlace de control_pedidos es la vía que
 * seguía sin protección.
 */
export async function ssoLogin(token) {
  if (!API_URL) {
    throw new Error("El acceso automático desde Control de Pedidos necesita el backend real — no está disponible en modo demo.");
  }
  let res;
  try {
    res = await fetchConTimeout(
      `${API_URL}/auth/sso`,
      {
        ...FETCH_OPTS,
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token }),
      },
      TIMEOUT_SESION_MS
    );
  } catch (e) {
    throw new Error(mensajePorFalloDeRed(e));
  }
  const body = await res.json();
  if (!res.ok) throw new Error(body.error || "No se pudo iniciar sesión automáticamente.");
  return body.usuario;
}

/** POST /auth/logout */
export async function logout() {
  if (!API_URL) {
    await delay(100);
    demoSesion = null;
    return;
  }
  await fetch(`${API_URL}/auth/logout`, { ...FETCH_OPTS, method: "POST" });
}

// (2026-09-02) Mismo mensaje genérico que MENSAJE_RECUPERACION en el
// backend (authController.js) — se repite aquí solo para el modo demo,
// donde no hay backend que lo devuelva; en real, el mensaje que se
// enseña es siempre el que llega en la respuesta. (2026-09-03: texto
// reescrito para dejar explícito, en el caso de solicitud nueva, que
// hace falta que un admin revise y apruebe a mano — ver el porqué en el
// comentario de MENSAJE_RECUPERACION del backend. Mantener los dos
// textos idénticos letra a letra.)
const MENSAJE_RECUPERACION_DEMO =
  "Si tu email ya está dado de alta, en breve deberías recibir un correo con un enlace para elegir una contraseña nueva. Si aún no tienes cuenta, hemos registrado tu solicitud de acceso: un administrador la revisará y, si la aprueba, te llegará un correo de bienvenida con tu enlace de acceso — puede tardar uno o dos días laborables.";

/**
 * POST /auth/recuperar-acceso — "¿Has olvidado tu contraseña?" en
 * LoginScreen.jsx. Pública (no requiere sesión), responde siempre el
 * mismo mensaje genérico tanto si el email está registrado como si no
 * — ver authController.js. Devuelve además `envio` (o `null`) para que
 * RecuperarAccesoModal.jsx lo mande por EmailJS desde este mismo
 * navegador (ver services/emailjs.js) — v1.15, sustituye al diseño
 * anterior (contraseña temporal encolada en control-pedidos-princess).
 *
 * En demo: si el email coincide con una cuenta registrada y activa
 * (`demoListaUsuarios`, no la lista fija de contraseñas — igual que el
 * backend real mira la tabla `usuarios`, no una lista de credenciales),
 * genera un token/enlace de mentira; si no, se añade a
 * `demoSolicitudesAcceso` igual que haría el backend real, para poder
 * probar también la pantalla de Administración → Solicitudes de acceso
 * en demo sin backend.
 */
export async function recuperarAcceso({ email, nombre }) {
  if (!API_URL) {
    await delay(250);
    const correo = (email || "").trim().toLowerCase();
    // (2026-09-03) Nombre opcional — si no lo escriben, se usa el propio
    // email como repuesto (solo importa para la rama de "solicitud de
    // acceso" de abajo; para la de recuperación no se usa en absoluto,
    // mismo comportamiento que el backend real, ver authController.js).
    const nombreCorto = (nombre || "").trim().slice(0, 120) || correo;
    const usuario = demoListaUsuarios.find((u) => u.email === correo);

    let envio = null;
    if (usuario && usuario.activo) {
      const token = generarTokenDemo();
      demoTokensAcceso = [
        { token, usuarioEmail: usuario.email, nombre: usuario.nombre, rol: usuario.rol, tipo: "recuperacion", usado: false },
        ...demoTokensAcceso.filter((t) => !(t.usuarioEmail === usuario.email && t.tipo === "recuperacion")),
      ];
      const enlace = enlaceTokenDemo(token);
      envio = {
        tipo: "usuario",
        destinatario: usuario.email,
        asunto: "Recuperar acceso — Catálogo Asignaciones (demo)",
        cuerpoHtml: `<p>Enlace de demo (no se envía ningún correo real): <a href="${enlace}">${enlace}</a></p>`,
        cuerpoText: `Enlace de demo (no se envía ningún correo real): ${enlace}`,
      };
    } else {
      const yaPendiente = demoSolicitudesAcceso.some((s) => s.email === correo && s.estado === "pendiente");
      if (!yaPendiente) {
        demoSolicitudesAcceso = [
          {
            id: `demo-solicitud-${demoSolicitudIdSeq++}`,
            nombre: nombreCorto,
            email: correo,
            estado: "pendiente",
            creado_en: new Date().toISOString(),
            resuelto_en: null,
          },
          ...demoSolicitudesAcceso,
        ];
        // (2026-09-05, v1.19.53) `envio` se queda en `null` a propósito
        // — en real, esta rama ya no devuelve nada al navegador en
        // absoluto: el aviso a administradores lo envía el backend
        // directamente por la API REST de EmailJS (ver
        // registrarSolicitudAcceso() en authController.js), así que el
        // modo demo no tiene nada equivalente que simular aquí.
      }
    }
    return { ok: true, mensaje: MENSAJE_RECUPERACION_DEMO, envio };
  }

  const res = await fetch(`${API_URL}/auth/recuperar-acceso`, {
    ...FETCH_OPTS,
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, nombre }),
  });
  const body = await res.json().catch(() => null);
  if (!res.ok) throw new Error(body?.error || "No se ha podido procesar la solicitud.");
  return body;
}

/**
 * GET /auth/token-acceso/:token — valida un enlace de acceso antes de
 * mostrar el formulario de "elige tu contraseña" (CanjearTokenAcceso.jsx).
 */
export async function validarTokenAcceso(token) {
  if (!API_URL) {
    await delay(150);
    const fila = demoTokensAcceso.find((t) => t.token === token);
    if (!fila) throw new Error("Este enlace no es válido.");
    if (fila.usado) throw new Error("Este enlace ya se ha usado.");
    return { ok: true, nombre: fila.nombre, email: fila.usuarioEmail, tipo: fila.tipo };
  }
  const res = await fetch(`${API_URL}/auth/token-acceso/${encodeURIComponent(token)}`, FETCH_OPTS);
  const body = await res.json().catch(() => null);
  if (!res.ok) throw new Error(body?.error || "Este enlace no es válido.");
  return body;
}

/**
 * POST /auth/canjear-token-acceso — canjea el enlace por una contraseña
 * elegida por el propio usuario y abre sesión directamente (auto-login),
 * igual que hace el backend real.
 */
export async function canjearTokenAcceso({ token, password }) {
  if (!API_URL) {
    await delay(250);
    if (!password || password.length < 8) throw new Error("La contraseña debe tener al menos 8 caracteres.");
    const fila = demoTokensAcceso.find((t) => t.token === token);
    if (!fila) throw new Error("Este enlace no es válido.");
    if (fila.usado) throw new Error("Este enlace ya se ha usado.");
    fila.usado = true;
    demoSesion = {
      nombre: fila.nombre,
      email: fila.usuarioEmail,
      rol: fila.rol,
      esAdminPrincipal: fila.rol === "admin",
      permisos: fila.rol === "admin" ? PERMISOS_TODOS : [],
    };
    return { ok: true, usuario: demoSesion };
  }
  const res = await fetch(`${API_URL}/auth/canjear-token-acceso`, {
    ...FETCH_OPTS,
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token, password }),
  });
  const body = await res.json().catch(() => null);
  if (!res.ok) throw new Error(body?.error || "No se ha podido canjear el enlace.");
  return body;
}

/**
 * GET /auth/emailjs-config — credenciales de la cuenta EmailJS activa
 * (o `{configurado:false}` si el panel de administración todavía no se
 * ha rellenado). Ver services/emailjs.js. En demo siempre
 * `configurado:false` — no hay ninguna cuenta EmailJS real que usar, el
 * resto del flujo ya está simulado en memoria (ver arriba).
 */
export async function obtenerConfigEmailjs() {
  if (!API_URL) {
    await delay(80);
    return { configurado: false, admin: null };
  }
  const res = await fetch(`${API_URL}/auth/emailjs-config`, FETCH_OPTS);
  const body = await res.json().catch(() => null);
  if (!res.ok) throw new Error(body?.error || "No se pudo consultar la configuración de EmailJS.");
  return body;
}

/** POST /auth/emailjs-registrar-envio — ver services/emailjs.js. No-op en demo. */
export async function registrarEnvioEmailjs() {
  if (!API_URL) {
    await delay(50);
    return { ok: true };
  }
  const res = await fetch(`${API_URL}/auth/emailjs-registrar-envio`, { ...FETCH_OPTS, method: "POST" });
  const body = await res.json().catch(() => null);
  if (!res.ok) throw new Error(body?.error || "No se pudo registrar el envío de EmailJS.");
  return body;
}

/** GET /admin/emailjs-config — configuración completa (con credenciales) para el panel de admin. */
export async function fetchConfigEmailjsAdmin() {
  if (!API_URL) {
    await delay(150);
    return { ...demoConfigEmailjs };
  }
  const res = await fetch(`${API_URL}/admin/emailjs-config`, FETCH_OPTS);
  const body = await res.json().catch(() => null);
  if (!res.ok) throw new Error(body?.error || "No se pudo cargar la configuración de EmailJS.");
  return body.data;
}

/** PUT /admin/emailjs-config — guarda credenciales/umbral/cuenta activa. */
export async function actualizarConfigEmailjsAdmin(cambios) {
  if (!API_URL) {
    await delay(200);
    demoConfigEmailjs = { ...demoConfigEmailjs, ...cambios, actualizado_en: new Date().toISOString() };
    return { ok: true, data: { ...demoConfigEmailjs } };
  }
  const res = await fetch(`${API_URL}/admin/emailjs-config`, {
    ...FETCH_OPTS,
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(cambios),
  });
  const body = await res.json().catch(() => null);
  if (!res.ok) throw new Error(body?.error || "No se pudo guardar la configuración de EmailJS.");
  return body;
}

/**
 * GET /auth/me — sesión actual, o null si no hay sesión.
 *
 * (2026-08-17) FIX: antes se documentaba como "nunca lanza", pero en la
 * práctica sí podía rechazar — sin capturarlo en ningún sitio — si la
 * red fallaba o el JSON de la respuesta venía mal formado (p.ej. una
 * página de error HTML de Render en vez de JSON durante un cold-start),
 * y como no tenía ningún timeout propio, un backend lento se quedaba
 * colgado varios minutos antes de que el navegador se rindiera por su
 * cuenta. App.jsx llamaba a esto sin `.catch()` confiando en que nunca
 * lanzaría — la promesa rechazada quedaba sin manejar y la app se
 * quedaba en "Comprobando sesión…" para siempre. Ahora SÍ puede lanzar
 * (a propósito, con un mensaje legible para mostrar en el login), con
 * un límite de `TIMEOUT_SESION_MS` para no depender del timeout propio
 * del navegador — quien llame debe capturarlo (ver App.jsx).
 */
export async function fetchSesionActual() {
  if (!API_URL) {
    await delay(100);
    return demoSesion;
  }
  let res;
  try {
    res = await fetchConTimeout(`${API_URL}/auth/me`, FETCH_OPTS, TIMEOUT_SESION_MS);
  } catch (e) {
    throw new Error(mensajePorFalloDeRed(e));
  }
  if (!res.ok) return null;
  try {
    const { usuario } = await res.json();
    return usuario;
  } catch {
    throw new Error("El servidor respondió de forma inesperada — inténtalo de nuevo en unos segundos.");
  }
}

/**
 * Lista artículos. Si hay backend configurado, llama a GET /articulos
 * con los filtros como query params. En modo demo, filtra el array local.
 */
/**
 * Devuelve { data, total }. `total` es el recuento real de artículos que
 * cumplen el filtro (viene de `pagination.total` en el backend, un
 * `count: "exact"` de Supabase que NO está limitado por pageSize/range).
 * `data` es solo la página pedida (`page`/`pageSize`, 100 por defecto) —
 * antes se pedía siempre un pageSize=3000 fijo sin paginación real en la
 * UI, así que "Todas las naturalezas" (~6700 activos, por encima de
 * 3000) mostraba el total correcto en el contador pero solo cargaba y
 * mostraba los primeros 3000 en la tabla, sin ninguna forma de ver el
 * resto. Ver App.jsx para los controles de paginación.
 */
export async function fetchArticulos({ q, naturaleza, familia, subfamilia, todos, page = 1, pageSize = 100 } = {}) {
  if (!API_URL) {
    await delay(150); // simula latencia de red
    const qMin = (q || "").toLowerCase();
    const data = demoArticulos.filter((a) => {
      if (!todos && !a.activo_dali) return false;
      if (naturaleza && a.naturaleza !== naturaleza) return false;
      // En modo demo no hay IDs de familia/subfamilia (los datos de
      // muestra no los llevan) — familia/subfamilia llegan aquí como
      // {id, nombre_familia}/{id, nombre_subfamilia} (ver
      // fetchJerarquia más abajo), y en demo el "id" es directamente
      // el nombre, así que comparar por nombre funciona igual que
      // comparar por id en el backend real.
      if (familia && a.familia !== familia.nombre_familia) return false;
      if (subfamilia && a.subfamilia !== subfamilia.nombre_subfamilia) return false;
      if (qMin) {
        // Multi-búsqueda (mismo criterio que el backend real, ver
        // articulosController.js): artículo, código DALI, código SAP o
        // proveedor — coincide en cualquiera de los cuatro.
        const coincide =
          a.nombre_articulo.toLowerCase().includes(qMin) ||
          String(a.codigo_dali).includes(qMin) ||
          (a.codigo_sap || "").toLowerCase().includes(qMin) ||
          (a.proveedor || "").toLowerCase().includes(qMin);
        if (!coincide) return false;
      }
      return true;
    });
    // La muestra de demo es pequeña (~22 artículos), pero se pagina
    // igual que en real para que los controles de paginación se
    // comporten igual en los dos modos, aunque aquí casi nunca haga
    // falta pasar de página 1.
    const inicio = (page - 1) * pageSize;
    return { data: data.slice(inicio, inicio + pageSize), total: data.length };
  }

  const params = new URLSearchParams();
  if (q) params.set("q", q);
  if (naturaleza) params.set("naturaleza", naturaleza);
  if (familia) params.set("familia", familia.id);
  if (subfamilia) params.set("subfamilia", subfamilia.id);
  if (todos) params.set("todos", "true");
  params.set("page", page);
  params.set("pageSize", pageSize);

  const res = await fetch(`${API_URL}/articulos?${params}`, FETCH_OPTS);
  if (!res.ok) {
    // Antes descartaba el cuerpo de la respuesta y siempre lanzaba el
    // mismo mensaje genérico — al capturar ahora el error en
    // App.jsx/AdminArticulos.jsx (ver HISTORIAL v0.16 y v0.17), merece
    // la pena propagar el motivo real que da el backend (p.ej. un
    // fallo de sintaxis de filtro en Supabase) en vez de ocultarlo.
    const cuerpo = await res.json().catch(() => null);
    throw new Error(cuerpo?.error || "Error al cargar artículos");
  }
  const { data, pagination } = await res.json();
  return { data, total: pagination?.total ?? data.length };
}

/**
 * URL de GET /export/pdf con el filtro activo (mismo criterio que
 * fetchArticulos: naturaleza como nombre, familia/subfamilia como
 * objeto {id, ...}). Se navega directamente a esta URL (window.open)
 * en vez de usar fetch — la cookie de sesión viaja igual
 * (sameSite=none en producción, ver server.js) y así el navegador se
 * encarga de la descarga del PDF sin pasar el binario por JS. Devuelve
 * null en modo demo: no hay backend real que genere el PDF.
 */
export function urlExportarPdf({ q, naturaleza, familia, subfamilia, todos, codigos } = {}) {
  if (!API_URL) return null;
  const params = new URLSearchParams();
  // (2026-09-03) `codigos` — selección manual de artículos marcados a
  // mano en pantalla (ver App.jsx, `seleccionados`) — sustituye a los 4
  // filtros de siempre, nunca se combinan: cuando llega, el backend
  // ignora q/naturaleza/familia/subfamilia/todos por completo (ver
  // fetchArticulosParaExport en exportController.js).
  if (codigos?.length) {
    params.set("codigos", codigos.join(","));
    return `${API_URL}/export/pdf?${params}`;
  }
  if (q) params.set("q", q);
  if (naturaleza) params.set("naturaleza", naturaleza);
  if (familia) {
    params.set("familia", familia.id);
    params.set("familiaNombre", familia.nombre_familia);
  }
  if (subfamilia) {
    params.set("subfamilia", subfamilia.id);
    params.set("subfamiliaNombre", subfamilia.nombre_subfamilia);
  }
  if (todos) params.set("todos", "true");
  return `${API_URL}/export/pdf?${params}`;
}

/** Igual que urlExportarPdf pero contra GET /export/excel. */
export function urlExportarExcel({ q, naturaleza, familia, subfamilia, todos, codigos } = {}) {
  if (!API_URL) return null;
  const params = new URLSearchParams();
  if (codigos?.length) {
    params.set("codigos", codigos.join(","));
    return `${API_URL}/export/excel?${params}`;
  }
  if (q) params.set("q", q);
  if (naturaleza) params.set("naturaleza", naturaleza);
  if (familia) params.set("familia", familia.id);
  if (subfamilia) params.set("subfamilia", subfamilia.id);
  if (todos) params.set("todos", "true");
  return `${API_URL}/export/excel?${params}`;
}

/**
 * (2026-09-10) URL de GET /admin/export-completo — a petición de Víctor,
 * el Excel "total" con todas las columnas de los dos Excel que se
 * importan (DALI + SAP) más el Código Proveedor, sin ningún filtro (todo
 * el catálogo, activos e inactivos). A diferencia de
 * urlExportarExcel/urlExportarPdf, no acepta ningún parámetro — siempre
 * es el catálogo entero. Reservado a quien tenga concedido el permiso
 * `admin-exportar-completo` (el administrador principal, u otro admin al
 * que se lo conceda desde "Usuarios") — el 403 si no lo tiene lo pone el
 * backend (`requierePermiso`, ver routes/admin.js), esta función solo
 * construye la URL. Devuelve null en modo demo, igual que las otras dos.
 */
export function urlExportarCatalogoCompleto() {
  if (!API_URL) return null;
  return `${API_URL}/admin/export-completo`;
}

/**
 * (2026-09-03) Descarga el fichero de una de las dos URLs de arriba por
 * fetch, en vez de dejar que sea el navegador quien navegue directo a la
 * URL con `window.open(url, "_blank")` — a petición de Víctor: con
 * ficheros grandes, esa pestaña nueva se quedaba en negro/blanco un buen
 * rato hasta que terminaba de descargar, sin ninguna señal de que algo
 * estuviera pasando. Con fetch + blob la app se queda en la pantalla de
 * siempre y puede enseñar un spinner mientras tanto (ver App.jsx). La
 * cookie de sesión viaja igual que en cualquier otra llamada
 * (credentials: "include", ver FETCH_OPTS arriba).
 *
 * `nombrePorDefecto` es el nombre que ya calcula el propio backend a
 * partir de los mismos parámetros (ver `nombreArchivo` en
 * exportController.js: `articulos-<naturaleza>.xlsx`/`.pdf` o
 * `articulos.xlsx`/`.pdf` sin naturaleza) — se usa tal cual si por lo que
 * sea la cabecera Content-Disposition no llega o no se puede leer
 * (necesita `exposedHeaders` en el CORS del backend, ver server.js).
 */
export async function descargarDesdeUrl(url, nombrePorDefecto) {
  const res = await fetch(url, FETCH_OPTS);
  if (!res.ok) {
    const cuerpo = await res.json().catch(() => null);
    throw new Error(cuerpo?.error || `No se ha podido generar el fichero (error ${res.status}).`);
  }
  const blob = await res.blob();
  const disposicion = res.headers.get("Content-Disposition") || "";
  const coincidencia = /filename="?([^";]+)"?/i.exec(disposicion);
  const nombreArchivo = coincidencia ? coincidencia[1] : nombrePorDefecto;
  return { blob, nombreArchivo };
}

// (2026-09-02) Caché en memoria de fetchProveedores() — séptima etapa de
// la auditoría full. La lista de proveedores casi nunca cambia (dentro
// de esta app, solo la toca `fusionarProveedores` más abajo; un
// proveedor nuevo se da de alta directamente en Supabase, fuera de esta
// app) pero se estaba pidiendo entera, de nuevo, cada vez que se
// montaba cualquiera de los 4 sitios que la usan: `AdminProveedores.jsx`,
// `AdminExportarZip.jsx`, `CargaMasivaModal.jsx` (una vez por cada
// apertura del modal) y, el caso que más se repite en un día normal,
// `ArticuloForm.jsx` — una llamada nueva por CADA artículo distinto que
// se abre para editar, trayendo siempre la misma lista de siempre. Con
// un catálogo de proveedores que ya ronda el centenar y una pantalla de
// administración que se abre muchas veces al día, es tráfico repetido
// para un dato que en la práctica es casi estático durante toda la
// sesión.
//
// Caché simple a nivel de módulo: se guarda la respuesta ya resuelta
// (se pierde sola al recargar la página, que es justo cuándo interesa
// refrescar por si acaso) y, aparte, se deduplican peticiones en vuelo
// (si dos componentes se montan casi a la vez — p.ej. la app entera al
// arrancar — solo se lanza una petición real de verdad, las dos
// comparten la misma promesa en vez de ir cada una por su lado). Un
// fallo NO se cachea — el siguiente intento vuelve a pedir de verdad —
// para no dejar la app atascada en "sin proveedores" por un problema de
// red puntual. Invalidada explícitamente solo en el único punto que de
// verdad cambia la lista desde esta app: `fusionarProveedores()`, que ya
// llama a `invalidarCacheProveedores()` tras un éxito — así el código
// que la usa (`AdminProveedores.jsx`, que ya volvía a llamar a
// `fetchProveedores()` después de fusionar, sin cambios aquí) recibe la
// lista fresca sin que haga falta tocar nada más. Se devuelve una copia
// del array cacheado en cada llamada (no la misma referencia) para que
// ningún componente pueda, por accidente en el futuro, mutar en sitio el
// array compartido y afectar a los demás sin darse cuenta.
let cacheProveedores = null; // array ya resuelto, o null si no hay nada cacheado todavía
let cacheProveedoresEnVuelo = null; // promesa de la petición en curso, o null

/**
 * GET /admin/proveedores — listado simple para el buscador
 * autorellenable de la carga masiva por proveedor (ver
 * CargaMasivaModal.jsx) y para los otros 3 sitios que lo usan (ver
 * comentario de la caché justo arriba). En modo demo se deriva de los
 * artículos de muestra.
 */
export async function fetchProveedores() {
  if (cacheProveedores) return [...cacheProveedores];
  if (cacheProveedoresEnVuelo) return cacheProveedoresEnVuelo.then((datos) => [...datos]);

  cacheProveedoresEnVuelo = (async () => {
    if (!API_URL) {
      await delay(100);
      const nombres = [...new Set(demoArticulos.map((a) => a.proveedor).filter(Boolean))].sort();
      return nombres.map((nombre_proveedor, id) => ({ id, nombre_proveedor }));
    }
    const res = await fetch(`${API_URL}/admin/proveedores`, FETCH_OPTS);
    if (!res.ok) {
      const cuerpo = await res.json().catch(() => null);
      throw new Error(cuerpo?.error || "Error al cargar los proveedores");
    }
    const { data } = await res.json();
    return data;
  })();

  try {
    cacheProveedores = await cacheProveedoresEnVuelo;
    return [...cacheProveedores];
  } finally {
    cacheProveedoresEnVuelo = null;
  }
}

/**
 * Fuerza que la próxima fetchProveedores() vuelva a pedir la lista de
 * verdad al backend, en vez de devolver la copia cacheada. Se llama
 * automáticamente desde fusionarProveedores() tras un éxito (ver más
 * abajo) — no hace falta llamarla a mano salvo que se añada, en el
 * futuro, algún otro sitio de esta app que también pueda cambiar la
 * lista de proveedores.
 */
export function invalidarCacheProveedores() {
  cacheProveedores = null;
  cacheProveedoresEnVuelo = null;
}

/**
 * GET /admin/documentacion-faltante — artículos activos sin imagen,
 * ficha técnica y/o ficha de seguridad, agrupados por proveedor. En
 * modo demo no hay datos reales de fichas/imagen para calcular esto
 * con sentido, así que se devuelve vacío.
 */
export async function fetchDocumentacionFaltante() {
  if (!API_URL) {
    await delay(100);
    return { grupos: [], total_articulos: 0, total_activos: demoArticulos.length };
  }
  const res = await fetch(`${API_URL}/admin/documentacion-faltante`, FETCH_OPTS);
  if (!res.ok) {
    const cuerpo = await res.json().catch(() => null);
    throw new Error(cuerpo?.error || "Error al cargar la documentación faltante");
  }
  return res.json();
}

/** URL de descarga del Excel de documentación faltante (null en modo demo) */
export function urlDocumentacionFaltanteExcel() {
  if (!API_URL) return null;
  return `${API_URL}/admin/documentacion-faltante/excel`;
}

/**
 * URL pública (sin sesión, ver `GET /export/documentacion-faltante-pdf/:id`
 * en backend/src/routes/export.js) del PDF con TODO lo que le falta a un
 * proveedor concreto (ficha técnica, ficha de seguridad e imagen, una
 * columna por tipo) — a petición de Víctor: cuando el listado de
 * referencias pendientes de un proveedor es muy largo, el correo de
 * "Documentación pendiente" (`EmailProveedorModal.jsx`) enlaza aquí en
 * vez de itemizarlas todas dentro del propio texto. Null en modo demo,
 * igual que el resto de URLs de descarga de este fichero.
 */
export function urlDocumentacionFaltantePdf(idProveedor) {
  if (!API_URL) return null;
  return `${API_URL}/export/documentacion-faltante-pdf/${idProveedor}`;
}

/**
 * URL de descarga del zip de documentación organizada por proveedor
 * (carpeta NOMBRE_PROVEEDOR / FICHAS TECNICAS|FICHAS SEGURIDAD|IMAGENES /
 * archivo nombrado con el código de proveedor) — copia de seguridad de
 * lo que ya está cargado en DALI, con la misma estructura que espera la
 * carga masiva para poder volver a subirlo si hiciera falta (ver
 * CargaMasivaModal.jsx y exportZipController.js en el backend).
 * `proveedorId` opcional: sin él exporta todos los proveedores a la vez
 * (puede tardar varios minutos). null en modo demo.
 */
export function urlExportarDocumentacionZip(proveedorId) {
  if (!API_URL) return null;
  const params = new URLSearchParams();
  if (proveedorId) params.set("proveedor_id", proveedorId);
  const qs = params.toString();
  return `${API_URL}/admin/documentacion-zip${qs ? `?${qs}` : ""}`;
}

/**
 * POST /admin/documentacion-faltante/preview-email — renderiza (sin
 * tocar la base de datos) el HTML final del correo de reclamación de
 * documentación, con el mismo logo/colores/maquetación que ya usa
 * control-pedidos-princess en sus propios correos — ver
 * backend/src/utils/emailHtml.js (`construirHtmlReclamacionDocumentacion`,
 * reutilizada tal cual por el backend para esto) y
 * EmailProveedorModal.jsx (pantalla previa del correo, a petición de
 * Víctor: "en pantalla previa del correo como en notificación. Ventana
 * visual correcta con correo logo texto etc").
 *
 * Pensada para llamarse en cada cambio de asunto/cuerpo (emparejada
 * con el hook `useDebouncedValue` en el modal) — no disponible en modo
 * demo, ya que necesita el backend real.
 */
export async function fetchPreviewEmailDocumentacion({ proveedor, asunto, cuerpo }) {
  if (!API_URL) {
    throw new Error("La vista previa del correo necesita el backend real — no está disponible en modo demo.");
  }
  const res = await fetch(`${API_URL}/admin/documentacion-faltante/preview-email`, {
    ...FETCH_OPTS,
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ proveedor, asunto, cuerpo }),
  });
  if (!res.ok) {
    const cuerpoResp = await res.json().catch(() => null);
    throw new Error(cuerpoResp?.error || "Error al generar la vista previa del correo.");
  }
  return res.json();
}

/**
 * POST /admin/documentacion-faltante/:idProveedor/preparar-envio
 *
 * (2026-08-27, envío directo por EmailJS propio desde 2026-09-09) Resuelve
 * en el servidor el destinatario real (contra Control de Pedidos), el
 * HTML del correo (mismo logo/colores que ya usa control-pedidos-princess,
 * ver backend/src/utils/emailHtml.js) y las credenciales EmailJS —
 * reutiliza el mismo Template ID "de usuario" de siempre, ver
 * HISTORIAL.md v1.44 — ver
 * backend/src/controllers/documentacionController.js
 * (prepararEnvioDocumentacionFaltante). Esta llamada NO envía nada
 * todavía: el envío real lo hace el propio navegador justo después,
 * llamando a `enviarProveedorPorEmailjs` (services/emailjs.js) con lo que
 * devuelve esta función — ver EmailProveedorModal.jsx. No disponible en
 * modo demo — es una llamada real a Control de Pedidos para resolver el
 * destinatario.
 */
export async function prepararEnvioDocumentacionFaltante(idProveedor, { asunto, cuerpo }) {
  if (!API_URL) {
    throw new Error("Preparar el envío necesita el backend real — no está disponible en modo demo.");
  }
  const res = await fetch(`${API_URL}/admin/documentacion-faltante/${idProveedor}/preparar-envio`, {
    ...FETCH_OPTS,
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ asunto, cuerpo }),
  });
  if (!res.ok) {
    const cuerpoResp = await res.json().catch(() => null);
    throw new Error(cuerpoResp?.error || "Error al preparar el envío del correo.");
  }
  return res.json();
}

/**
 * GET /admin/proveedores/:id/resumen — cuántos artículos, imágenes,
 * fichas y códigos de proveedor tiene ligados un proveedor concreto.
 * Ver AdminProveedores.jsx (pantalla "Fusionar proveedores").
 */
export async function fetchResumenProveedor(idProveedor) {
  if (!API_URL) {
    throw new Error("El resumen de proveedores necesita el backend real — no está disponible en modo demo.");
  }
  const res = await fetch(`${API_URL}/admin/proveedores/${idProveedor}/resumen`, FETCH_OPTS);
  if (!res.ok) {
    const cuerpo = await res.json().catch(() => null);
    throw new Error(cuerpo?.error || "Error al cargar el resumen del proveedor");
  }
  return res.json();
}

/**
 * POST /admin/proveedores/fusionar — traslada todo lo que cuelga de
 * `idOrigen` (artículos asignados, imágenes, fichas, códigos de
 * proveedor) a `idDestino` y borra `idOrigen`. Ver AdminProveedores.jsx
 * y el comentario largo de fusionarProveedores en
 * backend/src/controllers/proveedoresController.js para el motivo
 * (proveedores duplicados por un cambio de nombre en SAP/Excel).
 */
export async function fusionarProveedores(idOrigen, idDestino) {
  if (!API_URL) {
    throw new Error("Fusionar proveedores necesita el backend real — no está disponible en modo demo.");
  }
  const res = await fetch(`${API_URL}/admin/proveedores/fusionar`, {
    ...FETCH_OPTS,
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id_origen: idOrigen, id_destino: idDestino }),
  });
  if (!res.ok) {
    const cuerpo = await res.json().catch(() => null);
    throw new Error(cuerpo?.error || "Error al fusionar los proveedores");
  }
  // La fusión borra un proveedor de verdad (ver fusionarProveedores en
  // proveedoresController.js) — la lista cacheada por fetchProveedores()
  // ya no es válida, así que se invalida aquí mismo, en el único sitio
  // que de verdad cambia la lista desde esta app (ver comentario largo
  // junto a fetchProveedores). AdminProveedores.jsx ya vuelve a llamar a
  // fetchProveedores() justo después de una fusión con éxito; con la
  // caché invalidada aquí, esa llamada trae la lista fresca de verdad,
  // sin que AdminProveedores.jsx necesite saber nada de la caché.
  invalidarCacheProveedores();
  return res.json();
}

/**
 * GET /estadisticas — fecha de la última importación de Excel, total
 * de artículos DALI activos, y de esos, cuántos tienen código SAP. Se
 * muestra en la cabecera, visible para todos los usuarios. En modo
 * demo se calcula sobre los artículos de muestra.
 */
export async function fetchEstadisticas() {
  if (!API_URL) {
    await delay(100);
    const activos = demoArticulos.filter((a) => a.activo_dali);
    return {
      ultima_actualizacion: new Date().toISOString(),
      total_dali_activos: activos.length,
      total_sap_activos: activos.filter((a) => a.codigo_sap).length,
    };
  }
  const res = await fetch(`${API_URL}/estadisticas`, FETCH_OPTS);
  if (!res.ok) {
    const cuerpo = await res.json().catch(() => null);
    throw new Error(cuerpo?.error || "Error al cargar las estadísticas");
  }
  return res.json();
}

/**
 * GET /jerarquia — árbol de naturaleza -> familia -> subfamilia, con
 * IDs, para el sidebar desplegable (Sidebar.jsx). En modo demo se
 * deriva de los ~22 artículos de muestra (naturaleza/familia/
 * subfamilia por nombre, sin IDs reales) usando el propio nombre como
 * "id" — suficiente para navegar el árbol de demo, aunque no cubre las
 * 253 subfamilias reales, solo las que aparecen en la muestra.
 *
 * (2026-09-02) A petición de Víctor, para un menú lateral más limpio:
 * el backend real (ver jerarquiaController.js) ya excluye del árbol
 * cualquier naturaleza/familia/subfamilia sin NINGÚN artículo (activo,
 * salvo `todos: true` — y eso, igual que en `fetchArticulos`, el
 * propio backend solo lo respeta si quien pregunta tiene sesión de
 * admin). El modo demo replica el mismo criterio en JS a partir de
 * `mockArticulos` (que ya trae algunos `activo_dali: false` a
 * propósito, incluida toda la naturaleza BAZAR — el mismo ejemplo real
 * que dio Víctor) para que el comportamiento se vea igual sin backend.
 */
export async function fetchJerarquia({ todos } = {}) {
  if (!API_URL) {
    await delay(100);
    const fuente = todos ? mockArticulos : mockArticulos.filter((a) => a.activo_dali);
    const porNaturaleza = new Map();
    for (const a of fuente) {
      if (!porNaturaleza.has(a.naturaleza)) porNaturaleza.set(a.naturaleza, new Map());
      const porFamilia = porNaturaleza.get(a.naturaleza);
      if (!porFamilia.has(a.familia)) porFamilia.set(a.familia, new Set());
      porFamilia.get(a.familia).add(a.subfamilia);
    }
    return [...porNaturaleza.entries()].map(([nombre_naturaleza, porFamilia]) => ({
      id: nombre_naturaleza,
      nombre_naturaleza,
      familias: [...porFamilia.entries()].map(([nombre_familia, subfamilias]) => ({
        id: nombre_familia,
        nombre_familia,
        subfamilias: [...subfamilias].map((nombre_subfamilia) => ({
          id: nombre_subfamilia,
          nombre_subfamilia,
        })),
      })),
    }));
  }

  const params = new URLSearchParams();
  if (todos) params.set("todos", "true");
  const qs = params.toString();
  const res = await fetch(`${API_URL}/jerarquia${qs ? `?${qs}` : ""}`, FETCH_OPTS);
  if (!res.ok) throw new Error("Error al cargar la clasificación de artículos");
  const { data } = await res.json();
  return data;
}

/**
 * GET /articulos/:id — detalle de un solo artículo. La tabla y el
 * listado ya traen todo lo necesario para mostrarse a sí mismos; esta
 * función existe para pedir el dato que SOLO se resuelve al detalle
 * (la URL firmada de la imagen — la fila de la lista trae la ruta
 * cruda del bucket privado, no una URL que se pueda mostrar
 * directamente, ver ArticuloDetail.jsx).
 */
export async function fetchArticulo(codigoDali) {
  if (!API_URL) {
    await delay(100);
    return demoArticulos.find((a) => a.codigo_dali === codigoDali) || null;
  }
  const res = await fetch(`${API_URL}/articulos/${codigoDali}`, FETCH_OPTS);
  if (!res.ok) {
    const cuerpo = await res.json().catch(() => null);
    throw new Error(cuerpo?.error || "Error al cargar el artículo");
  }
  const { data } = await res.json();
  return data;
}

/** GET /articulos/:id/fichas — en modo demo devuelve un par de fichas simuladas */
export async function fetchFichas(codigoDali) {
  if (!API_URL) {
    await delay(100);
    return [
      { id: 1, tipo: "tecnica", url_pdf: "#" },
      { id: 2, tipo: "seguridad", url_pdf: "#" },
    ];
  }
  const res = await fetch(`${API_URL}/articulos/${codigoDali}/fichas`, FETCH_OPTS);
  if (!res.ok) throw new Error("Error al cargar fichas");
  const { data } = await res.json();
  return data;
}

/**
 * GET /articulos/:id/fichas-por-proveedor — fichas técnicas y de
 * seguridad, E IMAGEN (2026-08-27), de TODOS los proveedores que tienen
 * documentación guardada para este DALI (no solo el asignado), agrupadas
 * por proveedor. Ver botón "Ver alternativas de otros proveedores" en
 * ArticuloDetail.jsx. En modo demo simula dos proveedores (el asignado y
 * uno "alternativo") para poder ver el panel sin backend real.
 */
export async function fetchFichasPorProveedor(codigoDali) {
  if (!API_URL) {
    await delay(100);
    return [
      {
        id_proveedor: 1,
        nombre_proveedor: "Proveedor asignado (demo)",
        codigo_proveedor: "REF-001",
        asignado: true,
        fichas: [
          { id: 1, tipo: "tecnica", url_pdf: "#" },
          { id: 2, tipo: "seguridad", url_pdf: "#" },
        ],
        imagen: null,
        // (2026-08-31) Marcas extra del mismo proveedor (ver
        // marcasProveedorController.js) — mismo proveedor, mismo
        // artículo, código/imagen/fichas propios de cada una.
        marcas: [{ id: 101, codigo: "REF-001-INTEGRAL", imagen: null, fichas: [] }],
      },
      {
        id_proveedor: 2,
        nombre_proveedor: "Otro proveedor (demo)",
        codigo_proveedor: "OTRO-REF-42",
        asignado: false,
        fichas: [{ id: 3, tipo: "tecnica", url_pdf: "#" }],
        imagen: { id: 1, url_imagen: "https://placehold.co/300x200?text=Imagen+demo" },
        marcas: [],
      },
    ];
  }
  const res = await fetch(`${API_URL}/articulos/${codigoDali}/fichas-por-proveedor`, FETCH_OPTS);
  if (!res.ok) throw new Error("Error al cargar las fichas por proveedor");
  const { data } = await res.json();
  return data;
}

/** POST /admin/articulos — alta manual de ficha */
export async function createArticulo(payload) {
  if (!API_URL) {
    await delay(200);
    const nuevo = { ...payload, codigo_dali: siguienteCodigoDemo() };
    demoArticulos = [nuevo, ...demoArticulos];
    return nuevo;
  }
  const res = await fetch(`${API_URL}/admin/articulos`, {
    ...FETCH_OPTS,
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Error al crear el artículo");
  const { data } = await res.json();
  return data;
}

/** PUT /admin/articulos/:id — edición de ficha */
export async function updateArticulo(codigoDali, payload) {
  if (!API_URL) {
    await delay(200);
    demoArticulos = demoArticulos.map((a) =>
      a.codigo_dali === codigoDali ? { ...a, ...payload, codigo_dali } : a
    );
    return demoArticulos.find((a) => a.codigo_dali === codigoDali);
  }
  const res = await fetch(`${API_URL}/admin/articulos/${codigoDali}`, {
    ...FETCH_OPTS,
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Error al actualizar el artículo");
  const { data } = await res.json();
  return data;
}

/** DELETE /admin/articulos/:id — baja de ficha */
export async function deleteArticulo(codigoDali) {
  if (!API_URL) {
    await delay(150);
    demoArticulos = demoArticulos.filter((a) => a.codigo_dali !== codigoDali);
    return true;
  }
  const res = await fetch(`${API_URL}/admin/articulos/${codigoDali}`, {
    ...FETCH_OPTS,
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Error al dar de baja el artículo");
  return true;
}

// (2026-08-20) Sondeo de progreso de la importación — ver
// importController.js. Cada consulta de estado individual lleva su
// propio timeout corto (no tiene sentido esperar más que eso por una
// sola consulta), pero un fallo puntual de red no aborta el sondeo
// entero: se tolera hasta IMPORT_POLL_MAX_FALLOS_SEGUIDOS fallos
// seguidos antes de rendirse, para que un corte de wifi de unos segundos
// durante una importación de varios minutos no la dé por perdida sin
// necesidad (la importación en sí sigue corriendo en el servidor pase
// lo que pase con el navegador que la lanzó).
const IMPORT_POLL_INTERVAL_MS = 2000;
const IMPORT_POLL_TIMEOUT_MS = 15000;
const IMPORT_POLL_MAX_FALLOS_SEGUIDOS = 5;

/**
 * POST /admin/import-excel — sube ARTICULOS_DALI.xlsx y/o
 * LISTADO_CODIGOS_DALI_-_SAP.xlsx y hace upsert (sección 5 del informe
 * técnico). En modo demo simula un resultado plausible sin tocar datos.
 *
 * (2026-08-20) La importación real (miles de artículos, varios bloques
 * de guardado contra Supabase) corre en segundo plano en el backend —
 * ver importController.js. Antes esta función esperaba una única
 * respuesta HTTP a que TODO el proceso terminara, y con el catálogo ya
 * lo bastante grande esa conexión se cortaba a mitad de camino (502,
 * reportado por Víctor) porque el proxy delante del backend
 * (Cloudflare Worker / Render) no esperaba tanto. Ahora el POST vuelve
 * enseguida con un `job_id`, y esta función sondea
 * GET /admin/import-excel/estado/:jobId cada
 * `IMPORT_POLL_INTERVAL_MS` hasta ver "completado" o "error" — ninguna
 * conexión individual necesita quedarse abierta más que el tiempo de
 * una consulta de estado, así que da igual cuánto crezca el catálogo.
 *
 * `onProgress`, opcional: se llama en cada sondeo con
 * `{ estado, bloque_actual, total_bloques }` para poder pintar una
 * barra de progreso mientras se espera.
 */
export async function importExcel({ articulosFile, sapFile }, { onProgress } = {}) {
  if (!API_URL) {
    await delay(1100);
    const avisos = [];
    if (!articulosFile) avisos.push("No se ha adjuntado ARTICULOS_DALI.xlsx: no se procesará el catálogo maestro.");
    if (!sapFile) avisos.push("No se ha adjuntado el listado de códigos SAP: el cruce con SAP quedará pendiente.");
    const procesadas = demoArticulos.length;
    return {
      procesadas,
      creadas: 0,
      actualizadas: articulosFile || sapFile ? procesadas : 0,
      sinCambios: 0,
      avisos,
      fecha: new Date().toISOString(),
    };
  }

  const form = new FormData();
  if (articulosFile) form.append("articulos_dali", articulosFile);
  if (sapFile) form.append("listado_sap", sapFile);

  const res = await fetch(`${API_URL}/admin/import-excel`, {
    ...FETCH_OPTS,
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    // Antes descartaba el cuerpo y siempre lanzaba el mismo mensaje
    // genérico (mismo fallo ya corregido en fetchArticulos, ver
    // HISTORIAL v0.16/v1.0.8) — ocultaba el motivo real que da el
    // backend (columna que falta, error de Supabase, fila concreta que
    // no se pudo resolver...), dejando "Error al procesar la
    // importación" como único mensaje pase lo que pase.
    const cuerpo = await res.json().catch(() => null);
    throw new Error(cuerpo?.error || "Error al procesar la importación");
  }
  const { job_id: jobId } = await res.json();

  let fallosSeguidos = 0;
  while (true) {
    await delay(IMPORT_POLL_INTERVAL_MS);

    let estadoRes;
    try {
      estadoRes = await fetchConTimeout(
        `${API_URL}/admin/import-excel/estado/${jobId}`,
        FETCH_OPTS,
        IMPORT_POLL_TIMEOUT_MS
      );
    } catch {
      fallosSeguidos++;
      if (fallosSeguidos > IMPORT_POLL_MAX_FALLOS_SEGUIDOS) {
        throw new Error(
          "Se ha perdido la conexión comprobando el progreso de la importación. Puede que siga corriendo en el servidor — espera un momento y recarga esta pantalla para comprobarlo."
        );
      }
      continue;
    }

    if (!estadoRes.ok) {
      const cuerpo = await estadoRes.json().catch(() => null);
      throw new Error(cuerpo?.error || "Error consultando el progreso de la importación.");
    }
    fallosSeguidos = 0;

    const estado = await estadoRes.json();
    onProgress?.(estado);
    if (estado.estado === "completado") return estado.resultado;
    if (estado.estado === "error") throw new Error(estado.error || "Error procesando la importación.");
    // estado.estado === "procesando" -> seguir sondeando
  }
}

/** GET /admin/usuarios */
export async function fetchUsuarios() {
  if (!API_URL) {
    await delay(150);
    return [...demoListaUsuarios];
  }
  const res = await fetch(`${API_URL}/admin/usuarios`, FETCH_OPTS);
  if (!res.ok) {
    const cuerpo = await res.json().catch(() => null);
    throw new Error(cuerpo?.error || "Error al cargar los usuarios");
  }
  const { data } = await res.json();
  return data;
}

/** POST /admin/usuarios — alta de usuario (nombre, email, rol, password) */
export async function crearUsuario(payload) {
  if (!API_URL) {
    await delay(200);
    if (demoListaUsuarios.some((u) => u.email === payload.email.toLowerCase())) {
      throw new Error("Ya existe un usuario con ese email.");
    }
    const nuevo = {
      id: `demo-${demoUsuarioIdSeq++}`,
      nombre: payload.nombre,
      email: payload.email.toLowerCase(),
      rol: payload.rol,
      activo: true,
      creado_en: new Date().toISOString(),
      es_admin_principal: false,
      permisos:
        payload.rol === "admin" ? (Array.isArray(payload.permisos) ? payload.permisos : PERMISOS_TODOS) : [],
    };
    demoListaUsuarios = [nuevo, ...demoListaUsuarios];
    return nuevo;
  }
  const res = await fetch(`${API_URL}/admin/usuarios`, {
    ...FETCH_OPTS,
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const cuerpo = await res.json().catch(() => null);
    throw new Error(cuerpo?.error || "Error al crear el usuario");
  }
  const { data } = await res.json();
  return data;
}

/**
 * PUT /admin/usuarios/:id — edición (nombre/rol/activo/password, todos
 * opcionales — solo se manda lo que ha cambiado).
 */
export async function actualizarUsuario(id, cambios) {
  if (!API_URL) {
    await delay(200);
    demoListaUsuarios = demoListaUsuarios.map((u) => (u.id === id ? { ...u, ...cambios } : u));
    return demoListaUsuarios.find((u) => u.id === id);
  }
  const res = await fetch(`${API_URL}/admin/usuarios/${id}`, {
    ...FETCH_OPTS,
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(cambios),
  });
  if (!res.ok) {
    const cuerpo = await res.json().catch(() => null);
    throw new Error(cuerpo?.error || "Error al actualizar el usuario");
  }
  const { data } = await res.json();
  return data;
}

/**
 * DELETE /admin/usuarios/:id — elimina el usuario de verdad (no solo lo
 * desactiva). Las guardas (no borrarte a ti mismo, no dejar la app sin
 * ningún admin activo) las aplica el backend; aquí en demo se replica
 * solo la de "a ti mismo" porque es la única que UsuarioForm.jsx no
 * comprueba ya por su cuenta con `esUnoMismo`.
 */
export async function eliminarUsuario(id) {
  if (!API_URL) {
    await delay(200);
    demoListaUsuarios = demoListaUsuarios.filter((u) => u.id !== id);
    return;
  }
  const res = await fetch(`${API_URL}/admin/usuarios/${id}`, {
    ...FETCH_OPTS,
    method: "DELETE",
  });
  if (!res.ok) {
    const cuerpo = await res.json().catch(() => null);
    throw new Error(cuerpo?.error || "Error al eliminar el usuario");
  }
}

/**
 * POST /admin/usuarios/:id/traspasar-principal
 *
 * (2026-09-03, v1.19.44) Traspasa el puesto fijo de administrador
 * principal a otra cuenta admin activa — solo lo puede llamar quien YA
 * es principal (lo aplica el backend; ver el comentario grande en
 * usuariosController.js para el porqué de un traspaso en vez de
 * "varios principales a la vez", que fue justo lo que Víctor eligió al
 * preguntárselo). Tras un traspaso con éxito, `AdminUsuarios.jsx` cierra
 * la sesión de quien lo hizo — ver ese archivo para el motivo (la cookie
 * de sesión no se entera sola del cambio).
 *
 * En modo demo esto solo cambia `es_admin_principal` dentro de
 * `demoListaUsuarios` (para poder probar el resto de la pantalla) — la
 * propia sesión de demo sigue tratándose siempre como principal (ver
 * login() más arriba), no hay forma de simular en el navegador "dejar
 * de serlo uno mismo" sin una cuenta real detrás.
 */
export async function traspasarAdminPrincipal(id) {
  if (!API_URL) {
    await delay(200);
    const objetivo = demoListaUsuarios.find((u) => u.id === id);
    if (!objetivo) throw new Error("Usuario no encontrado.");
    if (objetivo.rol !== "admin") {
      throw new Error("Solo se puede nombrar administrador principal a una cuenta con rol Administrador.");
    }
    if (!objetivo.activo) {
      throw new Error("No se puede nombrar administrador principal a una cuenta desactivada.");
    }
    demoListaUsuarios = demoListaUsuarios.map((u) => ({ ...u, es_admin_principal: u.id === id }));
    return;
  }
  const res = await fetch(`${API_URL}/admin/usuarios/${id}/traspasar-principal`, {
    ...FETCH_OPTS,
    method: "POST",
  });
  if (!res.ok) {
    const cuerpo = await res.json().catch(() => null);
    throw new Error(cuerpo?.error || "Error al traspasar el puesto de administrador principal");
  }
}

/**
 * (2026-09-02) "Solicitudes de acceso" — pantalla nueva de Administración
 * para aceptar/rechazar las peticiones que llegan desde "¿Has olvidado tu
 * contraseña?" con un email no registrado (ver recuperarAcceso() arriba y
 * solicitudesAccesoController.js del backend).
 */

/** GET /admin/solicitudes-acceso */
export async function fetchSolicitudesAcceso() {
  if (!API_URL) {
    await delay(150);
    // Pendientes primero, más recientes primero dentro de cada estado —
    // mismo orden que el índice de la migración/la consulta real.
    return [...demoSolicitudesAcceso].sort((a, b) => {
      if (a.estado !== b.estado) return a.estado === "pendiente" ? -1 : 1;
      return new Date(b.creado_en) - new Date(a.creado_en);
    });
  }
  const res = await fetch(`${API_URL}/admin/solicitudes-acceso`, FETCH_OPTS);
  if (!res.ok) {
    const cuerpo = await res.json().catch(() => null);
    throw new Error(cuerpo?.error || "Error al cargar las solicitudes de acceso");
  }
  const { data } = await res.json();
  return data;
}

/**
 * POST /admin/solicitudes-acceso/:id/aceptar — body: { rol }. Devuelve
 * { data, envio, link, avisoCorreo } — v1.15: `envio` es lo que
 * AdminSolicitudesAcceso.jsx manda por EmailJS desde el navegador del
 * propio admin (ver services/emailjs.js), `link` es el enlace de
 * bienvenida en crudo (red de seguridad si el correo no llega) — ya no
 * hay ninguna contraseña temporal que devolver (ver el comentario largo
 * en solicitudesAccesoController.js).
 */
export async function aceptarSolicitudAcceso(id, { rol = "hotel" } = {}) {
  if (!API_URL) {
    await delay(250);
    const solicitud = demoSolicitudesAcceso.find((s) => s.id === id);
    if (!solicitud) throw new Error("Solicitud no encontrada.");
    if (solicitud.estado !== "pendiente") {
      throw new Error(`Esta solicitud ya está "${solicitud.estado}" — no se puede volver a resolver.`);
    }
    if (demoListaUsuarios.some((u) => u.email === solicitud.email && u.activo)) {
      throw new Error(
        `Ya existe una cuenta ACTIVA con "${solicitud.email}" — revísala en Administración → Usuarios en vez de aceptar esta solicitud.`
      );
    }
    const nuevo = {
      id: `demo-${demoUsuarioIdSeq++}`,
      nombre: solicitud.nombre,
      email: solicitud.email,
      rol,
      activo: true,
      creado_en: new Date().toISOString(),
    };
    demoListaUsuarios = [nuevo, ...demoListaUsuarios];
    demoSolicitudesAcceso = demoSolicitudesAcceso.map((s) =>
      s.id === id ? { ...s, estado: "aceptada", resuelto_en: new Date().toISOString() } : s
    );

    const token = generarTokenDemo();
    demoTokensAcceso = [{ token, usuarioEmail: nuevo.email, nombre: nuevo.nombre, rol: nuevo.rol, tipo: "bienvenida", usado: false }, ...demoTokensAcceso];
    const link = enlaceTokenDemo(token);
    const envio = {
      destinatario: nuevo.email,
      tipo: "usuario",
      asunto: "Acceso concedido — Catálogo Asignaciones (demo)",
      cuerpoHtml: `<p>Enlace de demo (no se envía ningún correo real): <a href="${link}">${link}</a></p>`,
      cuerpoText: `Enlace de demo (no se envía ningún correo real): ${link}`,
    };
    return { ok: true, data: nuevo, envio, link, avisoCorreo: null };
  }
  const res = await fetch(`${API_URL}/admin/solicitudes-acceso/${id}/aceptar`, {
    ...FETCH_OPTS,
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ rol }),
  });
  const body = await res.json().catch(() => null);
  if (!res.ok) throw new Error(body?.error || "Error al aceptar la solicitud.");
  return body;
}

/** POST /admin/solicitudes-acceso/:id/rechazar */
export async function rechazarSolicitudAcceso(id) {
  if (!API_URL) {
    await delay(200);
    const solicitud = demoSolicitudesAcceso.find((s) => s.id === id);
    if (!solicitud) throw new Error("Solicitud no encontrada.");
    if (solicitud.estado !== "pendiente") {
      throw new Error(`Esta solicitud ya está "${solicitud.estado}" — no se puede volver a resolver.`);
    }
    const actualizada = { ...solicitud, estado: "rechazada", resuelto_en: new Date().toISOString() };
    demoSolicitudesAcceso = demoSolicitudesAcceso.map((s) => (s.id === id ? actualizada : s));
    return actualizada;
  }
  const res = await fetch(`${API_URL}/admin/solicitudes-acceso/${id}/rechazar`, {
    ...FETCH_OPTS,
    method: "POST",
  });
  const body = await res.json().catch(() => null);
  if (!res.ok) throw new Error(body?.error || "Error al rechazar la solicitud.");
  return body.data;
}

/**
 * POST /admin/articulos/:codigoDali/imagen — sube/sustituye la foto del
 * artículo. Solo disponible editando un artículo ya guardado (necesita
 * su codigo_dali real) — ver ArticuloForm.jsx. Deshabilitada en modo
 * demo, no hay backend real que guarde el archivo.
 *
 * (2026-08-17) `idProveedor` sustituye al antiguo `codigoProveedor` de
 * texto libre — ahora se manda el id real de `proveedores` (o se omite,
 * y el backend resuelve el proveedor asignado del propio artículo). Ver
 * storageController.js (resolverIdProveedor) y migración
 * 2026-08-17_documentacion_por_proveedor.sql: cada imagen/ficha se
 * guarda asociada a UN proveedor concreto, no solo al artículo.
 *
 * (2026-08-20) `codigoProveedor` (opcional): el código con el que ESE
 * proveedor identifica el artículo (distinto de `idProveedor`, que es
 * el id interno de `proveedores`) — si se manda, el backend lo guarda
 * en `codigos_proveedor` como parte de esta misma petición, sin
 * necesidad de otra llamada aparte (ver migración
 * 2026-08-20_codigos_proveedor.sql).
 *
 * (2026-09-01) `esGenerica` (opcional, por defecto false): true cuando
 * este archivo es la imagen de reserva "SIN IMAGEN" del proveedor, no
 * una foto propia del artículo — lo manda CargaMasivaModal.jsx al subir
 * los fallback calculados en `calcularFilasFallback`. Se graba en
 * `imagenes.es_generica` (migración 2026-09-01_es_generica_imagen.sql)
 * para poder borrarla después con seguridad (ver
 * eliminarImagenGenericaProveedor más abajo) si "SIN IMAGEN" desaparece
 * de la carpeta del proveedor en una carga masiva posterior.
 */
export async function subirImagenArticulo(codigoDali, archivo, idProveedor, codigoProveedor, esGenerica) {
  if (!API_URL) {
    throw new Error("Subir imágenes necesita el backend real — no está disponible en modo demo.");
  }
  const form = new FormData();
  form.append("imagen", archivo);
  if (idProveedor) form.append("id_proveedor", idProveedor);
  if (codigoProveedor) form.append("codigo_proveedor", codigoProveedor);
  if (esGenerica) form.append("es_generica", "true");
  const res = await fetch(`${API_URL}/admin/articulos/${codigoDali}/imagen`, {
    ...FETCH_OPTS,
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const cuerpo = await res.json().catch(() => null);
    throw new Error(cuerpo?.error || "Error al subir la imagen");
  }
  return res.json();
}

/**
 * POST /admin/articulos/:codigoDali/fichas — sube/sustituye la ficha
 * técnica o de seguridad (según `tipo`, "tecnica" o "seguridad") del
 * artículo. Mismas condiciones que subirImagenArticulo (ver nota
 * `idProveedor`/`codigoProveedor` de ahí arriba).
 */
export async function subirFichaArticulo(codigoDali, tipo, archivo, idProveedor, codigoProveedor) {
  if (!API_URL) {
    throw new Error("Subir fichas necesita el backend real — no está disponible en modo demo.");
  }
  const form = new FormData();
  form.append("tipo", tipo);
  form.append("ficha", archivo);
  if (idProveedor) form.append("id_proveedor", idProveedor);
  if (codigoProveedor) form.append("codigo_proveedor", codigoProveedor);
  const res = await fetch(`${API_URL}/admin/articulos/${codigoDali}/fichas`, {
    ...FETCH_OPTS,
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const cuerpo = await res.json().catch(() => null);
    throw new Error(cuerpo?.error || "Error al subir la ficha");
  }
  return res.json();
}

/**
 * GET /admin/articulos/:codigoDali/documentos-hash?tipo=...&id_proveedor=...
 * Hash SHA-256 (hex) ya guardado para ese documento, el código de
 * proveedor ya guardado para ese artículo+proveedor (o `null` cada uno
 * si no hay nada todavía), y — desde el 2026-09-02 — también
 * `idArticulo`/`nombreArticulo`/`idProveedorAsignado`/`proveedorAsignado`
 * (quinta etapa de la auditoría full, ver el comentario largo de
 * `obtenerHashDocumento` en storageController.js). Pensado para
 * consultarse ANTES de subirImagenArticulo/subirFichaArticulo y
 * ahorrarse la subida entera si el archivo local ya coincide, y para
 * construir el mensaje de la fila (nombre del artículo, si el proveedor
 * de esta carga es el asignado o "en reserva") — todo en UNA sola
 * petición en vez de esta más `fetchArticulo` por separado, que era como
 * lo hacía CargaMasivaModal.jsx hasta esta versión.
 *
 * A diferencia de la función anterior (`fetchHashDocumento`, que
 * devolvía `{ hash: null }` en cualquier fallo para no bloquear la
 * subida — el hash-check era solo una optimización sobre un artículo
 * cuya existencia ya se había confirmado aparte, con `fetchArticulo`),
 * ahora esta misma petición es también la que confirma que el artículo
 * existe, así que un fallo aquí SÍ se propaga (lanza) — ya no hay forma
 * de "confirmar que existe" por otro lado si esta falla. Mismo criterio
 * que ya tenía `fetchArticulo`: un fallo se refleja como fila en error,
 * revisable a mano o reintentando la carga masiva, en vez de subir a
 * ciegas sin saber si el artículo es real.
 *
 * En modo demo lanza directamente (esta función solo se usa desde la
 * carga masiva, que ya avisa en otro sitio que necesita el backend real
 * — ver `CargaMasivaModal.jsx`).
 */
export async function fetchInfoYHashDocumento(codigoDali, tipo, idProveedor) {
  if (!API_URL) {
    throw new Error("La carga masiva necesita el backend real — no está disponible en modo demo.");
  }
  const params = new URLSearchParams({ tipo });
  if (idProveedor) params.set("id_proveedor", idProveedor);
  const res = await fetch(`${API_URL}/admin/articulos/${codigoDali}/documentos-hash?${params}`, FETCH_OPTS);
  if (!res.ok) {
    const cuerpo = await res.json().catch(() => null);
    throw new Error(cuerpo?.error || `Artículo no encontrado con código DALI ${codigoDali}.`);
  }
  const { hash, codigo_proveedor, id_articulo, nombre_articulo, id_proveedor_asignado, proveedor_asignado } =
    await res.json();
  return {
    hash,
    codigoProveedor: codigo_proveedor,
    idArticulo: id_articulo,
    nombreArticulo: nombre_articulo,
    idProveedorAsignado: id_proveedor_asignado,
    proveedorAsignado: proveedor_asignado,
  };
}

/**
 * PUT /admin/articulos/:codigoDali/codigo-proveedor — escribe/corrige a
 * mano el código con el que `idProveedor` identifica este artículo (ver
 * migración 2026-08-20_codigos_proveedor.sql). Usado por
 * ArticuloForm.jsx (edición manual) y por CargaMasivaModal.jsx cuando
 * detecta que una fila está "sin cambios" por hash pero el código de
 * proveedor leído del nombre de archivo es distinto al ya guardado.
 */
export async function actualizarCodigoProveedor(codigoDali, idProveedor, codigo) {
  if (!API_URL) {
    throw new Error("Guardar el código de proveedor necesita el backend real — no está disponible en modo demo.");
  }
  const res = await fetch(`${API_URL}/admin/articulos/${codigoDali}/codigo-proveedor`, {
    ...FETCH_OPTS,
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id_proveedor: idProveedor, codigo }),
  });
  if (!res.ok) {
    const cuerpo = await res.json().catch(() => null);
    throw new Error(cuerpo?.error || "Error al guardar el código de proveedor");
  }
  return res.json();
}

/**
 * GET /admin/articulos/por-codigo-proveedor?id_proveedor=&codigo= —
 * busca qué artículo(s) usa ESE proveedor para identificar el código
 * indicado (ver migración 2026-08-20_codigos_proveedor.sql) y devuelve
 * su(s) código(s) DALI. Pensado para CargaMasivaModal.jsx cuando el
 * nombre del archivo trae solo el código de proveedor (p.ej.
 * "9904.pdf"), en vez del formato completo "códigoDali_códigoSap_
 * códigoProveedor_nombre" — el proveedor ya se sabe por la carpeta, así
 * que con esto basta para encontrar el artículo.
 *
 * (2026-08-27) Puede haber más de un artículo con el mismo proveedor +
 * código (mismo producto en varios formatos, ver comentario en
 * storageController.js) — la respuesta trae `codigos_dali` (array) con
 * todos ellos; `codigo_dali` (singular) se mantiene por compatibilidad
 * y es solo el primero.
 *
 * En modo demo siempre devuelve `{ encontrado: false }` (no hay backend
 * real que consultar).
 */
export async function buscarArticuloPorCodigoProveedor(idProveedor, codigo) {
  if (!API_URL) return { encontrado: false };
  const params = new URLSearchParams({ id_proveedor: idProveedor, codigo });
  const res = await fetch(`${API_URL}/admin/articulos/por-codigo-proveedor?${params}`, FETCH_OPTS);
  if (!res.ok) return { encontrado: false }; // si falla la consulta, se trata como "no encontrado" (la fila pasa a error, revisar a mano)
  return res.json();
}

/**
 * POST /admin/articulos/carga-masiva-codigo-proveedor — sube en un solo
 * archivo .xlsx el mismo listado que descarga "Exportar Excel"
 * (columnas "Código DALI" y "Código Proveedor", entre otras), con la
 * columna de código de proveedor ya rellenada/corregida a mano, y el
 * backend aplica esos códigos en bloque (ver storageController.js) —
 * pensado para reaprovechar la propia exportación como plantilla de
 * carga masiva, en vez de tener que preparar un archivo aparte.
 */
export async function cargaMasivaCodigoProveedor(archivo) {
  if (!API_URL) {
    throw new Error("La carga masiva de código de proveedor necesita el backend real — no está disponible en modo demo.");
  }
  const form = new FormData();
  form.append("archivo", archivo);
  const res = await fetch(`${API_URL}/admin/articulos/carga-masiva-codigo-proveedor`, {
    ...FETCH_OPTS,
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const cuerpo = await res.json().catch(() => null);
    throw new Error(cuerpo?.error || "Error al procesar la carga masiva de código de proveedor");
  }
  return res.json();
}

/**
 * DELETE /admin/articulos/:codigoDali/adjuntos — borra la imagen y
 * todas las fichas del artículo (Storage + DB), sin tocar el
 * artículo en sí. Pensado para limpiar documentación huérfana de un
 * codigo_dali que ha desaparecido del Excel maestro (ver
 * avisos_desaparecidos en la respuesta de importExcel).
 */
export async function eliminarAdjuntosArticulo(codigoDali) {
  if (!API_URL) {
    throw new Error("Esta acción necesita el backend real — no está disponible en modo demo.");
  }
  const res = await fetch(`${API_URL}/admin/articulos/${codigoDali}/adjuntos`, {
    ...FETCH_OPTS,
    method: "DELETE",
  });
  if (!res.ok) {
    const cuerpo = await res.json().catch(() => null);
    throw new Error(cuerpo?.error || "Error al eliminar la documentación adjunta");
  }
}

/**
 * DELETE /admin/articulos/:codigoDali/fichas/:tipo — borra SOLO esa
 * ficha ("tecnica" o "seguridad"), sin tocar la imagen ni la otra
 * ficha. A diferencia de eliminarAdjuntosArticulo (todo de golpe),
 * esta es para quitar una ficha suelta sin tener que sustituirla.
 *
 * 2026-08-27: idProveedor es opcional — si se indica, borra la ficha
 * reservada para ESE proveedor (no necesariamente el asignado), para
 * poder gestionar documentación alternativa desde ArticuloForm.jsx.
 * Si se omite, se comporta igual que antes (proveedor asignado).
 */
export async function eliminarFichaArticulo(codigoDali, tipo, idProveedor) {
  if (!API_URL) {
    throw new Error("Esta acción necesita el backend real — no está disponible en modo demo.");
  }
  const query = idProveedor != null ? `?id_proveedor=${encodeURIComponent(idProveedor)}` : "";
  const res = await fetch(`${API_URL}/admin/articulos/${codigoDali}/fichas/${tipo}${query}`, {
    ...FETCH_OPTS,
    method: "DELETE",
  });
  if (!res.ok) {
    const cuerpo = await res.json().catch(() => null);
    throw new Error(cuerpo?.error || "Error al eliminar la ficha");
  }
}

/**
 * DELETE /admin/articulos/:codigoDali/imagen — borra SOLO la imagen,
 * sin tocar las fichas. Mismo criterio que eliminarFichaArticulo,
 * incluyendo el idProveedor opcional (ver comentario de arriba).
 */
export async function eliminarImagenArticulo(codigoDali, idProveedor) {
  if (!API_URL) {
    throw new Error("Esta acción necesita el backend real — no está disponible en modo demo.");
  }
  const query = idProveedor != null ? `?id_proveedor=${encodeURIComponent(idProveedor)}` : "";
  const res = await fetch(`${API_URL}/admin/articulos/${codigoDali}/imagen${query}`, {
    ...FETCH_OPTS,
    method: "DELETE",
  });
  if (!res.ok) {
    const cuerpo = await res.json().catch(() => null);
    throw new Error(cuerpo?.error || "Error al eliminar la imagen");
  }
}

/**
 * GET /admin/proveedores/con-imagen-generica — ids (+ cantidad de
 * artículos afectados) de los proveedores que ACTUALMENTE tienen alguna
 * imagen genérica ("SIN IMAGEN") guardada. Ver
 * listarProveedoresConImagenGenerica, storageController.js.
 *
 * (2026-09-02) Usado por CargaMasivaModal.jsx para saber, ANTES de
 * procesar la carpeta, qué proveedores podrían perder su imagen
 * genérica si esta carga ya no trae "SIN IMAGEN" para ellos — hace
 * falta esta consulta porque el selector de carpeta del navegador
 * (`webkitdirectory`) no ve carpetas vacías: si la carpeta IMAGENES de
 * un proveedor se queda sin ningún archivo (solo tenía "SIN IMAGEN" y se
 * ha borrado, sin dejar ninguna foto propia detrás), no hay ningún
 * archivo suyo que la detección normal (`clasificarArchivos`) pueda ver.
 * Sabiendo de antemano quién tiene una genérica guardada, no hace falta
 * verla desaparecer del árbol de archivos — basta con confirmar que ese
 * proveedor forma parte de la carpeta elegida (por cualquier archivo
 * suyo, no solo de imágenes, o por el filtro manual de un único
 * proveedor) y que esta carga no trae "SIN IMAGEN" para él.
 *
 * Si falla, se devuelve `[]` (no bloquea el resto de la carga masiva —
 * simplemente no se detecta ninguna baja en esta pasada).
 */
export async function fetchProveedoresConImagenGenerica() {
  if (!API_URL) return [];
  const res = await fetch(`${API_URL}/admin/proveedores/con-imagen-generica`, FETCH_OPTS);
  if (!res.ok) return [];
  const { proveedores } = await res.json().catch(() => ({ proveedores: [] }));
  return proveedores || [];
}

/**
 * DELETE /admin/proveedores/:idProveedor/imagen-generica — borra la
 * imagen genérica de reserva ("SIN IMAGEN") de TODOS los artículos de
 * ese proveedor que la tuvieran asignada — Storage + tabla `imagenes`,
 * ver eliminarImagenGenericaProveedor en storageController.js. Devuelve
 * `{ eliminadas }` (puede ser 0, no es un error). Usado por
 * CargaMasivaModal.jsx cuando "SIN IMAGEN" desaparece de la carpeta
 * IMAGENES de un proveedor respecto a una carga anterior (ver
 * detectarProveedoresSinGenerica ahí).
 */
export async function eliminarImagenGenericaProveedor(idProveedor) {
  if (!API_URL) {
    throw new Error("Esta acción necesita el backend real — no está disponible en modo demo.");
  }
  const res = await fetch(`${API_URL}/admin/proveedores/${idProveedor}/imagen-generica`, {
    ...FETCH_OPTS,
    method: "DELETE",
  });
  if (!res.ok) {
    const cuerpo = await res.json().catch(() => null);
    throw new Error(cuerpo?.error || "Error al eliminar la imagen genérica del proveedor");
  }
  return res.json();
}

/**
 * GET /admin/proveedores/:id/imagenes-repetidas — grupos de imágenes de
 * este proveedor que comparten exactamente el mismo hash entre 2 o más
 * artículos activos suyos (`es_generica = false`, ver el comentario
 * largo de listarImagenesRepetidasProveedor en storageController.js).
 * Herramienta de reparación para el caso reportado por Víctor: un
 * proveedor que tenía "SIN IMAGEN" asignada a todas sus referencias,
 * pero subida ANTES de que existiera `es_generica` — al no estar
 * marcadas, esos artículos "ya tienen imagen" a ojos del sistema y
 * nunca reciben la "SIN IMAGEN" nueva por mucho que se repita la carga
 * masiva. Ver AdminProveedores.jsx.
 */
export async function fetchImagenesRepetidasProveedor(idProveedor) {
  if (!API_URL) {
    throw new Error("Esta herramienta necesita el backend real — no está disponible en modo demo.");
  }
  const res = await fetch(`${API_URL}/admin/proveedores/${idProveedor}/imagenes-repetidas`, FETCH_OPTS);
  if (!res.ok) {
    const cuerpo = await res.json().catch(() => null);
    throw new Error(cuerpo?.error || "Error al buscar imágenes repetidas del proveedor");
  }
  return res.json();
}

/**
 * DELETE /admin/proveedores/:id/imagenes-repetidas — borra (Storage +
 * tabla) el grupo de imágenes repetidas identificado por `hash` (uno de
 * los que devuelve fetchImagenesRepetidasProveedor). Los artículos
 * afectados vuelven a aparecer como "sin imagen" — la siguiente carga
 * masiva con "SIN IMAGEN" en la carpeta del proveedor ya se la asigna
 * correctamente, marcada `es_generica = true` desde el principio.
 */
export async function eliminarImagenesRepetidasProveedor(idProveedor, hash) {
  if (!API_URL) {
    throw new Error("Esta acción necesita el backend real — no está disponible en modo demo.");
  }
  const res = await fetch(`${API_URL}/admin/proveedores/${idProveedor}/imagenes-repetidas`, {
    ...FETCH_OPTS,
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ hash }),
  });
  if (!res.ok) {
    const cuerpo = await res.json().catch(() => null);
    throw new Error(cuerpo?.error || "Error al eliminar las imágenes repetidas del proveedor");
  }
  return res.json();
}

/* ═══════════════════════════════════════════════════════════════════
 * Marcas extra de un mismo proveedor (2026-08-31)
 *
 * Un proveedor puede tener más de una referencia/marca para el mismo
 * DALI (ej. CADELSA suministrando arroz vaporizado en varias marcas
 * además de la asignada) — cada marca tiene SOLO su propio código de
 * proveedor (sin nombre aparte, decisión tomada con Víctor), imagen y
 * fichas, siempre además de (nunca en vez de) la referencia principal
 * de ese proveedor en `fetchFichasPorProveedor`. Gestión manual desde
 * ArticuloForm.jsx — por ahora la carga masiva por carpetas no crea ni
 * reconoce marcas. Ver backend/src/controllers/marcasProveedorController.js.
 * ═══════════════════════════════════════════════════════════════════ */

/** POST /admin/articulos/:codigoDali/marcas-proveedor — Body: {id_proveedor, codigo}. */
export async function crearMarcaProveedor(codigoDali, idProveedor, codigo) {
  if (!API_URL) {
    throw new Error("Añadir una marca necesita el backend real — no está disponible en modo demo.");
  }
  const res = await fetch(`${API_URL}/admin/articulos/${codigoDali}/marcas-proveedor`, {
    ...FETCH_OPTS,
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id_proveedor: idProveedor, codigo }),
  });
  if (!res.ok) {
    const cuerpo = await res.json().catch(() => null);
    throw new Error(cuerpo?.error || "Error al crear la marca");
  }
  return res.json();
}

/** PUT /admin/marcas-proveedor/:idMarca/codigo — Body: {codigo}. */
export async function actualizarCodigoMarcaProveedor(idMarca, codigo) {
  if (!API_URL) {
    throw new Error("Guardar el código de la marca necesita el backend real — no está disponible en modo demo.");
  }
  const res = await fetch(`${API_URL}/admin/marcas-proveedor/${idMarca}/codigo`, {
    ...FETCH_OPTS,
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ codigo }),
  });
  if (!res.ok) {
    const cuerpo = await res.json().catch(() => null);
    throw new Error(cuerpo?.error || "Error al guardar el código de la marca");
  }
  return res.json();
}

/** DELETE /admin/marcas-proveedor/:idMarca — borra la marca completa (código + imagen + fichas). */
export async function eliminarMarcaProveedor(idMarca) {
  if (!API_URL) {
    throw new Error("Esta acción necesita el backend real — no está disponible en modo demo.");
  }
  const res = await fetch(`${API_URL}/admin/marcas-proveedor/${idMarca}`, {
    ...FETCH_OPTS,
    method: "DELETE",
  });
  if (!res.ok) {
    const cuerpo = await res.json().catch(() => null);
    throw new Error(cuerpo?.error || "Error al eliminar la marca");
  }
}

/** POST /admin/marcas-proveedor/:idMarca/imagen */
export async function subirImagenMarcaProveedor(idMarca, archivo) {
  if (!API_URL) {
    throw new Error("Subir imágenes necesita el backend real — no está disponible en modo demo.");
  }
  const form = new FormData();
  form.append("imagen", archivo);
  const res = await fetch(`${API_URL}/admin/marcas-proveedor/${idMarca}/imagen`, {
    ...FETCH_OPTS,
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const cuerpo = await res.json().catch(() => null);
    throw new Error(cuerpo?.error || "Error al subir la imagen");
  }
  return res.json();
}

/** POST /admin/marcas-proveedor/:idMarca/fichas — Body: campo "tipo" ("tecnica"|"seguridad") + "ficha". */
export async function subirFichaMarcaProveedor(idMarca, tipo, archivo) {
  if (!API_URL) {
    throw new Error("Subir fichas necesita el backend real — no está disponible en modo demo.");
  }
  const form = new FormData();
  form.append("tipo", tipo);
  form.append("ficha", archivo);
  const res = await fetch(`${API_URL}/admin/marcas-proveedor/${idMarca}/fichas`, {
    ...FETCH_OPTS,
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const cuerpo = await res.json().catch(() => null);
    throw new Error(cuerpo?.error || "Error al subir la ficha");
  }
  return res.json();
}

/** DELETE /admin/marcas-proveedor/:idMarca/imagen */
export async function eliminarImagenMarcaProveedor(idMarca) {
  if (!API_URL) {
    throw new Error("Esta acción necesita el backend real — no está disponible en modo demo.");
  }
  const res = await fetch(`${API_URL}/admin/marcas-proveedor/${idMarca}/imagen`, {
    ...FETCH_OPTS,
    method: "DELETE",
  });
  if (!res.ok) {
    const cuerpo = await res.json().catch(() => null);
    throw new Error(cuerpo?.error || "Error al eliminar la imagen");
  }
}

/** DELETE /admin/marcas-proveedor/:idMarca/fichas/:tipo */
export async function eliminarFichaMarcaProveedor(idMarca, tipo) {
  if (!API_URL) {
    throw new Error("Esta acción necesita el backend real — no está disponible en modo demo.");
  }
  const res = await fetch(`${API_URL}/admin/marcas-proveedor/${idMarca}/fichas/${tipo}`, {
    ...FETCH_OPTS,
    method: "DELETE",
  });
  if (!res.ok) {
    const cuerpo = await res.json().catch(() => null);
    throw new Error(cuerpo?.error || "Error al eliminar la ficha");
  }
}
