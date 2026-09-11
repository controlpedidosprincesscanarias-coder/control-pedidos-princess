/**
 * (2026-08-27) Generador del HTML de los correos que DALI encola en la
 * cola de control-pedidos-princess (ver
 * ../services/controlPedidosEmailBridge.js y EmailProveedorModal.jsx).
 *
 * Réplica en JS, a propósito casi literal, de `_email_header_html()` /
 * `_email_html_simple()` en el `app.py` de control-pedidos-princess — a
 * petición explícita de Víctor: "utilizar lo mismo que utiliza
 * controlpedidos" (mismo logo, mismos colores de cabecera), no un diseño
 * propio de DALI. El logo NO se copia a este repo: se referencia
 * directamente la imagen ya alojada en control-pedidos-princess
 * (CONTROL_PEDIDOS_URL/static/logo-sidebar-email.png), la misma URL que
 * usa esa app en sus propios correos — así un cambio de logo allí se
 * refleja aquí sin tocar nada en DALI.
 *
 * Un único template EmailJS del lado de control-pedidos
 * (`template_1zrv4ze`, campo `{{{{message}}}}` sin escapar) recibe
 * cualquier HTML que se le pase — no hace falta crear ni tocar ninguna
 * plantilla de EmailJS para esto, basta con generar aquí el HTML
 * completo, igual que ya hace esa app para sus propios tipos de correo.
 */

const CONTROL_PEDIDOS_URL = (
  process.env.CONTROL_PEDIDOS_URL || "https://control-pedidos-princess.onrender.com"
).replace(/\/$/, "");

/**
 * Cabecera estándar (logo + título + subtítulo) — mismo layout y mismos
 * colores por defecto que `_email_header_html()` en control-pedidos.
 */
function cabeceraHtml(titulo, subtitulo, colorFondo = "#0f2044", colorTitulo = "#ffffff", colorSubtitulo = "#b9c3dc") {
  return `
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:${colorFondo};">
    <tr>
      <td style="padding:16px 0 16px 24px;vertical-align:middle;" valign="middle">
        <h2 style="margin:0;color:${colorTitulo};font-size:18px;">${titulo}</h2>
        <p style="margin:4px 0 0;color:${colorSubtitulo};font-size:13px;">${subtitulo}</p>
      </td>
      <td style="padding:12px 24px 12px 16px;vertical-align:middle;text-align:right;width:1%;white-space:nowrap;" valign="middle" align="right">
        <img src="${CONTROL_PEDIDOS_URL}/static/logo-sidebar-email.png" alt="Princess Hotels &amp; Resorts"
             width="60" height="56"
             style="height:56px;width:60px;display:block;margin-left:auto;">
      </td>
    </tr>
  </table>
  `;
}

// (2026-09-11) Detecta una URL http(s) dentro de un bloque de texto —
// usado más abajo para convertir en botón el enlace de descarga del PDF
// de "documentación pendiente" (ver `generarTextoEmail` en
// EmailProveedorModal.jsx: por encima de cierto número de referencias,
// el correo deja de itemizarlas y en su lugar incluye una frase con
// este enlace). `\S+` sin más recorte porque el texto que arma
// `generarTextoEmail` deja la URL siempre como último token del párrafo,
// sin puntuación pegada detrás.
const PATRON_URL = /https?:\/\/\S+/;

/**
 * Convierte el texto plano ya redactado en EmailProveedorModal.jsx
 * (párrafos separados por línea en blanco, líneas de "* algo" como
 * viñetas) en HTML de correo — sin reescribir el contenido, solo el
 * formato: mismo redactado que Víctor ya revisó y editó en el modal.
 *
 * (2026-09-11) Un párrafo (no una lista) que contenga una URL http(s) se
 * parte en dos: el texto antes de la URL como párrafo normal, y la URL
 * como un botón centrado con el mismo estilo que ya usa
 * `construirHtmlTokenAcceso()` más abajo en este fichero — en vez de
 * mostrar el enlace en crudo. Como la URL vive dentro del propio
 * `cuerpo` (el mismo texto editable en el `<textarea>` del modal), la
 * vista previa y el correo real la tratan exactamente igual, sin
 * ningún parámetro nuevo que mantener sincronizado entre frontend y
 * backend — mismo criterio de "la vista previa es SIEMPRE fiel a lo que
 * se envía" que ya sigue el resto de esta función.
 */
function textoPlanoAHtmlParrafos(cuerpo) {
  const bloques = String(cuerpo || "")
    .split(/\n{2,}/)
    .map((b) => b.trim())
    .filter(Boolean);

  return bloques
    .map((bloque) => {
      const lineas = bloque.split("\n").map((l) => l.trim()).filter(Boolean);
      const esLista = lineas.length > 0 && lineas.every((l) => l.startsWith("* "));
      if (esLista) {
        const items = lineas.map((l) => `<li>${l.slice(2)}</li>`).join("\n        ");
        return `<ul style="margin:8px 0;padding-left:20px;">\n        ${items}\n      </ul>`;
      }

      const textoCompleto = lineas.join("<br>");
      const coincidenciaUrl = textoCompleto.match(PATRON_URL);
      if (coincidenciaUrl) {
        const url = coincidenciaUrl[0];
        const antes = textoCompleto.slice(0, coincidenciaUrl.index).trim();
        const despues = textoCompleto.slice(coincidenciaUrl.index + url.length).trim();
        const partes = [];
        if (antes) partes.push(`<p style="margin:0 0 12px;">${antes}</p>`);
        partes.push(
          `<p style="margin:0 0 12px;text-align:center;"><a href="${url}" ` +
            `style="display:inline-block;background:#0f2044;color:#ffffff;text-decoration:none;` +
            `font-weight:bold;padding:10px 24px;border-radius:6px;">Descargar listado completo (PDF)</a></p>`
        );
        if (despues) partes.push(`<p style="margin:0 0 12px;">${despues}</p>`);
        return partes.join("\n      ");
      }

      return `<p style="margin:0 0 12px;">${textoCompleto}</p>`;
    })
    .join("\n      ");
}

/**
 * HTML completo del correo de reclamación de documentación a un
 * proveedor — mismo "sobre" (tarjeta con cabecera, cuerpo, pie) que
 * `_email_html_simple()` en control-pedidos, con el asunto/cuerpo ya
 * redactado y revisado por Víctor en EmailProveedorModal.jsx.
 */
export function construirHtmlReclamacionDocumentacion({ proveedor, asunto, cuerpo }) {
  const cuerpoHtml = textoPlanoAHtmlParrafos(cuerpo);
  // (2026-08-29) A petición de Víctor, se quita el pie fijo "Catálogo DALI
  // · Central de Compras Canarias" que iba después de la firma — desde
  // que el propio cuerpo ya termina con la firma completa (nombre,
  // departamento, dirección, teléfono, email — ver generarTextoEmail() en
  // EmailProveedorModal.jsx), esa línea suelta quedaba fuera de lugar,
  // como una segunda firma sin sentido justo debajo de la firma real.
  return `
    <div style="font-family:sans-serif;max-width:560px;margin:0 auto;
                background:#f9f9f9;border-radius:10px;overflow:hidden;
                border:1px solid #e0e0e0;">
      ${cabeceraHtml("Documentación pendiente", proveedor)}
      <div style="padding:22px 24px;font-size:14px;color:#333;line-height:1.6;">
        ${cuerpoHtml}
      </div>
    </div>
  `.trim();
}

// (2026-09-02) `nombre` en las dos plantillas de abajo puede venir de un
// formulario público SIN sesión (`POST /auth/recuperar-acceso`, ver
// authController.js) — a diferencia del resto de este archivo, hasta
// ahora siempre alimentado con datos ya validados/de admin (proveedor de
// la propia BD, texto que Víctor redacta y revisa en
// EmailProveedorModal.jsx). Sin escapar, alguien podría escribir HTML/JS
// en el campo "nombre" de esa solicitud y que acabara ejecutándose en el
// cliente de correo de quien la abra (típicamente un admin). `email` no
// necesita este mismo escape en la práctica (el regex de formato del
// controlador ya descarta `< > " '`), pero se escapa igual por si acaso
// cambiara esa validación en el futuro sin recordar este detalle.
function escaparHtml(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

/**
 * (2026-09-02, v1.15) HTML del correo con el ENLACE de un solo uso para
 * elegir contraseña propia — sustituye a la contraseña temporal (la
 * versión anterior de esta función, `construirHtmlContrasenaTemporal`,
 * generaba y mostraba la contraseña en el propio correo; ver HISTORIAL
 * v1.15 para el porqué del cambio a token+enlace). Dos contextos
 * posibles, mismo "sobre" (ver comentario de arriba), solo cambia la
 * introducción:
 *   - `contexto: "recuperacion"` — el propio usuario pulsó "¿Has
 *     olvidado tu contraseña?" con un email YA registrado (ver
 *     `emitirTokenAcceso` en authController.js) — nadie ha aprobado
 *     nada, es autoservicio sobre su propia cuenta.
 *   - `contexto: "bienvenida"` — un admin acaba de ACEPTAR una
 *     solicitud de acceso (ver solicitudesAccesoController.js) y la
 *     cuenta se crea aquí por primera vez; nunca ha existido ninguna
 *     contraseña real que transmitir.
 * El enlace caduca en 2h y solo puede canjearse una vez (ver tabla
 * `tokens_acceso` / CanjearTokenAcceso.jsx).
 */
export function construirHtmlTokenAcceso({ nombre, email, enlace, contexto = "recuperacion" }) {
  const esBienvenida = contexto === "bienvenida";
  const titulo = esBienvenida ? "Acceso concedido" : "Recuperar acceso";
  const introHtml = esBienvenida
    ? `<p style="margin:0 0 12px;">Hola ${escaparHtml(nombre)}, se te ha concedido acceso a <strong>Catálogo Asignaciones</strong>. Pulsa el siguiente enlace para elegir tu contraseña y entrar por primera vez:</p>`
    : `<p style="margin:0 0 12px;">Hola ${escaparHtml(nombre)}, hemos recibido una petición para recuperar el acceso a tu cuenta de <strong>Catálogo Asignaciones</strong> (${escaparHtml(email)}). Pulsa el siguiente enlace para elegir una contraseña nueva:</p>`;

  return `
    <div style="font-family:sans-serif;max-width:560px;margin:0 auto;
                background:#f9f9f9;border-radius:10px;overflow:hidden;
                border:1px solid #e0e0e0;">
      ${cabeceraHtml(titulo, "Catálogo Asignaciones · Central de Compras Princess Canarias")}
      <div style="padding:22px 24px;font-size:14px;color:#333;line-height:1.6;">
        ${introHtml}
        <p style="margin:0 0 20px;text-align:center;">
          <a href="${enlace}" style="display:inline-block;background:#0f2044;color:#ffffff;text-decoration:none;
             font-weight:bold;padding:12px 28px;border-radius:6px;">Elegir mi contraseña</a>
        </p>
        <p style="margin:0 0 12px;color:#666;font-size:12px;">Si el botón no funciona, copia este enlace en tu navegador:<br>
          <a href="${enlace}" style="color:#0f2044;word-break:break-all;">${enlace}</a>
        </p>
        <p style="margin:0;">Este enlace caduca en 2 horas y solo se puede usar una vez. ${
          esBienvenida
            ? ""
            : "Si no has pedido esto, puedes ignorar este correo — tu contraseña actual sigue funcionando igual, no se ha tocado nada todavía."
        }</p>
      </div>
    </div>
  `.trim();
}

/**
 * (2026-09-02) HTML del correo de aviso a los administradores cuando
 * alguien pide acceso con un email que todavía no está dado de alta (o
 * que está desactivado) — ver `registrarSolicitudAcceso` en
 * authController.js. `nombre`/`email` son los que la propia persona ha
 * escrito en el formulario público, SIN validar más allá del formato —
 * ver `escaparHtml` arriba.
 */
export function construirHtmlSolicitudAcceso({ nombre, email }) {
  return `
    <div style="font-family:sans-serif;max-width:560px;margin:0 auto;
                background:#f9f9f9;border-radius:10px;overflow:hidden;
                border:1px solid #e0e0e0;">
      ${cabeceraHtml("Solicitud de acceso", "Catálogo Asignaciones · Central de Compras Princess Canarias")}
      <div style="padding:22px 24px;font-size:14px;color:#333;line-height:1.6;">
        <p style="margin:0 0 12px;">Alguien ha pedido acceso a <strong>Catálogo Asignaciones</strong> con un email que todavía no está dado de alta:</p>
        <p style="margin:0 0 4px;"><strong>Nombre:</strong> ${escaparHtml(nombre)}</p>
        <p style="margin:0 0 16px;"><strong>Email:</strong> ${escaparHtml(email)}</p>
        <p style="margin:0;">Puedes aceptar o rechazar la petición desde Catálogo Asignaciones → Administración → Solicitudes de acceso.</p>
      </div>
    </div>
  `.trim();
}
