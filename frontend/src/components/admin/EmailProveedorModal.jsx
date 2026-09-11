import { useEffect, useMemo, useState } from "react";
import {
  prepararEnvioDocumentacionFaltante,
  fetchPreviewEmailDocumentacion,
  urlDocumentacionFaltantePdf,
} from "../../services/api.js";
import { enviarProveedorPorEmailjs } from "../../services/emailjs.js";
import { useDebouncedValue } from "../../hooks/useDebouncedValue.js";
import { useCerrarAlClicFuera } from "../../hooks/useCerrarAlClicFuera.js";
import { formatearMovilFirma } from "../../utils/format";

/**
 * (2026-08-25) Genera el texto de un email reclamando a un proveedor
 * la documentación (imagen/ficha técnica/ficha de seguridad) que le
 * falta, referenciando cada artículo con SU PROPIO código (ver
 * migración 2026-08-20_codigos_proveedor.sql) — a petición de Víctor,
 * porque el código DALI o el SAP no le dicen nada a un proveedor
 * externo. Cuando un artículo no tiene código de proveedor guardado
 * todavía, se referencia por su nombre y se pide explícitamente que
 * indiquen su código — así el email también sirve para ir rellenando
 * ese dato con el tiempo.
 *
 * (2026-08-26) Reescrito el redactado a petición de Víctor: la versión
 * anterior listaba un "- vuestro código X: falta ficha técnica, ficha
 * de seguridad" por cada artículo, lo cual con más de 50 artículos
 * quedaba como una lista interminable y repetitiva. Ahora sigue el
 * modelo de correo que Víctor ya usa a mano: una lista con viñetas
 * SOLO de las referencias a las que les falta ficha técnica (el dato
 * que de verdad varía artículo a artículo), y luego un aviso general
 * — sin repetir cada código — para la ficha de seguridad y la imagen,
 * ya que esos se piden "para todo lo que nos suministren actualmente"
 * en vez de listarse uno a uno. Cada aviso general solo aparece si de
 * verdad falta algo de ese tipo en el grupo, y el primero que aparezca
 * ajusta su frase de enlace ("Asimismo…"/"Adicionalmente…" solo tienen
 * sentido si hay contenido previo en el correo).
 *
 * El asunto y el cuerpo son editables antes de enviarlos — igual que
 * antes, copiarlos o abrirlos en el cliente de correo del propio Víctor
 * (mailto:) sigue disponible como alternativa manual.
 *
 * (2026-08-27, envío directo por EmailJS propio desde 2026-09-09)
 * "Enviar email": este botón pide primero al backend (POST
 * /admin/documentacion-faltante/:id/preparar-envio) que resuelva el
 * destinatario real (contra Control de Pedidos) y arme el HTML con el
 * mismo logo y colores que ya usa control-pedidos-princess, y a
 * continuación envía el correo DE VERDAD, al momento, desde este mismo
 * navegador, con el EmailJS propio de DALI (ver
 * services/emailjs.js, `enviarProveedorPorEmailjs`) — a petición de
 * Víctor: "necesito que la aplicacion catalogo asignaciones utilice su
 * propio emailjs para solicitar la documentacion faltante, actualmente
 * se encola y se envia desde control pedidos". Hasta el 2026-09-09 este
 * botón se llamaba "Encolar envío" y dejaba el correo en la cola de
 * control-pedidos-princess, a la espera de que alguien tuviera esa otra
 * aplicación abierta para que se enviara de verdad — ya no depende de
 * eso. Si algo falla (plantilla EmailJS de proveedor sin configurar,
 * Control de Pedidos no responde al resolver el destinatario, sin
 * red…), el error lo dice claramente y "Copiar"/mailto siguen
 * disponibles sin necesidad de cerrar y reabrir el modal.
 *
 * (2026-08-27) Tres ajustes a petición de Víctor sobre un email ya
 * generado y enviado a un proveedor real:
 * 1. Junto al código de proveedor de cada referencia se añade también
 *    el nombre del artículo (la descripción propia de DALI) — "para
 *    mejor referencia", ya que un código suelto no siempre le dice
 *    nada a quien lo lee del lado del proveedor sin tener delante su
 *    propio listado.
 * 2. Se añade una frase aclarando que un archivo nombrado ÚNICAMENTE
 *    con el código (sin la descripción detrás) también es válido —
 *    la carga masiva (`CargaMasivaModal.jsx`) ya solo admite ese
 *    formato corto de nombre de archivo desde v1.18.12, así que
 *    "código_descripción" es cómodo para que ellos identifiquen el
 *    archivo, pero no hace falta que lo incluyan si no quieren.
 * 3. El ejemplo de nombre de archivo ya no es un texto fijo
 *    ("090102_ARENQUE AL CURRY", que no significaba nada para un
 *    proveedor distinto de aquel al que se le generó la primera vez):
 *    ahora se construye con una referencia real de ESTE proveedor, de
 *    entre las que tiene asignadas y le faltan.
 *
 * (2026-08-28) Reconstruido a petición de Víctor: "debería ser similar
 * a la notificación de alerta al proveedor de control pedidos ...
 * pantalla previa del correo como en notificación. Ventana visual
 * correcta con correo logo texto etc". Antes este modal solo mostraba
 * el asunto/cuerpo en texto plano, sin ninguna vista de cómo quedaría
 * el correo real; ahora, igual que el modal de referencia
 * (`abrirModalEmailAlerta` en control-pedidos-princess), pide al
 * backend el HTML ya renderizado (mismo logo/colores que esa app, ver
 * `construirHtmlReclamacionDocumentacion` en emailHtml.js) y lo
 * inyecta tal cual — no se reimplementa el maquetado aquí, para que la
 * vista previa sea SIEMPRE fiel a lo que de verdad se envía. Además,
 * el email de destino ya no puede editarse ni añadirse desde DALI: solo
 * se usa el que resuelve Control de Pedidos por nombre de proveedor
 * (ver controlPedidosEmailBridge.js) — si no lo tiene, este modal no
 * ofrece ningún envío para ese proveedor hasta que se añada allí.
 *
 * (2026-08-29) Tres ajustes a petición de Víctor sobre un email real ya
 * enviado a un proveedor: "¿puedes hacer este correo mas profesional?
 * la idea esta clara y entendible, pero se que lo puedes redactar mejor
 * siguiendo las pautas establecidas, indicar de una manera elegante que
 * si es posible seria bueno que se adjunte imagen de cada una de las
 * referencias asignadas siguiendo la misma pauta de las fichas, como
 * nombre el codigo del articulo ; tambien falta la firma al estilo del
 * resto de correos que se envian a los proveedores desde control
 * pedidos ; en este caso incluir el nombre, telefono, correo del admin
 * que realiza la gestion":
 * 1. Redactado revisado con un tono más formal ("Estimados/as," en vez
 *    de "Buenos días,", una frase de apertura que da contexto antes de
 *    entrar en la lista) sin cambiar el fondo del mensaje.
 * 2. La petición de imagen ya no es una frase suelta: ahora enlaza
 *    explícitamente con el aviso de nombrado de archivos, pidiendo que
 *    cada imagen se identifique "del mismo modo que las fichas técnicas
 *    y de seguridad" (código de artículo al inicio del nombre) — es la
 *    misma pauta, dicha una sola vez para los tres tipos de documento en
 *    vez de repetirla.
 * 3. Firma añadida al final, con el mismo formato que
 *    `_firma_comprador_html`/`_firma_comprador_text` de
 *    control-pedidos-princess (nombre, departamento, dirección fija,
 *    teléfono con prefijo "(+34)" y email) — mismo "Atentamente," como
 *    entradilla, en vez de "Un saludo,". `firmaAdmin` ({ nombre, email,
 *    telefono }) lo resuelve el backend a partir de quien tiene la
 *    sesión abierta (ver AdminDocumentacionFaltante.jsx /
 *    documentacionController.js): el nombre/email son los del admin de
 *    DALI; el teléfono, al no existir ese campo en DALI, se cruza por
 *    email contra los compradores/administradores ya dados de alta en
 *    Control de Pedidos — si no hay ninguno con ese email allí, o no
 *    tiene móvil guardado, esa línea de la firma simplemente se omite
 *    (igual que ya hace Control de Pedidos cuando falta el dato), sin
 *    que eso impida generar ni enviar el correo.
 *
 * (2026-09-11) A petición de Víctor, sobre un correo real con ~140
 * referencias: "cuando un listado de faltantes es tan extenso, se puede
 * crear un PDF y enviar en vez del detalle un boton para la descarga
 * del listado bien estructurado?". Por encima de
 * `UMBRAL_LISTADO_FICHA_TECNICA_PDF` referencias con ficha técnica
 * pendiente, la lista con viñetas de "* código — artículo" (que es la
 * que se hacía interminable) se sustituye por un párrafo corto que
 * enlaza a `GET /export/documentacion-faltante-pdf/:idProveedor` (ruta
 * pública, ver backend/src/routes/export.js) — un PDF con TODO lo
 * pendiente de este proveedor (no solo ficha técnica: también ficha de
 * seguridad e imagen, una columna por tipo), más completo que la propia
 * lista a la que sustituye. El enlace viaja como texto plano dentro del
 * `cuerpo` (mismo campo editable de siempre) — `textoPlanoAHtmlParrafos`
 * en `backend/src/utils/emailHtml.js` lo detecta y lo pinta como un
 * botón en el HTML del correo, así que la vista previa y el envío real
 * quedan automáticamente sincronizados sin ningún parámetro nuevo que
 * mantener aparte. El resto del correo (avisos generales de ficha de
 * seguridad/imagen, firma) no cambia.
 */
const UMBRAL_LISTADO_FICHA_TECNICA_PDF = 30;

function generarTextoEmail(grupo, firmaAdmin) {
  const referenciaDe = (a) =>
    a.codigo_proveedor
      ? `${a.codigo_proveedor} — ${a.nombre_articulo}`
      : `«${a.nombre_articulo}» (no tenemos vuestro código para este artículo — indicádnoslo si podéis)`;

  const faltaTecnica = grupo.articulos.filter((a) => a.falta_ficha_tecnica);
  const faltaSeguridad = grupo.articulos.some((a) => a.falta_ficha_seguridad);

  // Ejemplo de nombre de archivo con una referencia real de este
  // proveedor (prioriza una a la que le falte ficha técnica, ya que es
  // la lista que se acaba de mostrar arriba) — si ninguna de sus
  // referencias tiene código de proveedor guardado todavía, no hay
  // ejemplo posible y se omite esa parte de la frase.
  const articuloEjemplo =
    faltaTecnica.find((a) => a.codigo_proveedor) ||
    grupo.articulos.find((a) => a.codigo_proveedor) ||
    null;
  const ejemploNombreArchivo = articuloEjemplo
    ? `${articuloEjemplo.codigo_proveedor}_${articuloEjemplo.nombre_articulo}`
    : null;

  const partes = [
    "Estimados/as,",
    "Nos ponemos en contacto con ustedes para solicitarles la documentación pendiente de varias " +
      "de las referencias que actualmente nos suministran.",
  ];
  let hayContenidoPrevio = false;

  if (faltaTecnica.length > 0) {
    if (faltaTecnica.length > UMBRAL_LISTADO_FICHA_TECNICA_PDF && grupo.id_proveedor != null) {
      // (2026-09-11) Listado demasiado largo para itemizarlo aquí — ver
      // comentario grande de más arriba. La URL queda como último token
      // del párrafo, sin puntuación pegada detrás, para que
      // `textoPlanoAHtmlParrafos` la reconozca sin ambigüedad.
      const enlacePdf = urlDocumentacionFaltantePdf(grupo.id_proveedor);
      partes.push(
        `Al tratarse de ${faltaTecnica.length} referencias, en vez de detallarlas aquí una a una, hemos ` +
          "preparado un listado completo en PDF con el detalle de cada referencia (ficha técnica, ficha " +
          `de seguridad e imagen). Puede descargarlo en el siguiente enlace:\n\n${enlacePdf}`
      );
    } else {
      partes.push(
        "Necesitamos que nos hagan llegar la ficha técnica de las siguientes referencias, para las " +
          "cuales no disponemos todavía de dicha documentación:\n\n" +
          faltaTecnica.map((a) => `* ${referenciaDe(a)}`).join("\n")
      );
    }
    hayContenidoPrevio = true;
  }

  const avisos = [];
  if (faltaSeguridad) {
    avisos.push(
      (hayContenidoPrevio ? "Asimismo, les recordamos" : "Les recordamos") +
        " que toda referencia que actualmente nos estén suministrando y disponga de ficha de " +
        "seguridad deberá incluirla también en el envío."
    );
    hayContenidoPrevio = true;
  }
  // (2026-08-29) A petición de Víctor, la petición de imagen ya NO depende
  // de `faltaImagen` (antes, si ningún artículo del grupo tenía la imagen
  // marcada como faltante, el correo no la pedía en absoluto — Víctor
  // reportó, sobre un correo real ya generado, que la frase directamente
  // no aparecía). Ahora es una petición fija en todo correo de este tipo,
  // igual que ya son fijos el aviso de ficha de seguridad-si-aplica y el
  // de nombrado de archivos: "si es posible seria bueno que se adjunte
  // imagen de cada una de las referencias asignadas". Tampoco es ya una
  // frase suelta: enlaza explícitamente con el aviso de nombrado de
  // archivos de más abajo (misma pauta que las fichas — código de
  // artículo al inicio del nombre), en vez de repetir la norma dos veces.
  avisos.push(
    (hayContenidoPrevio ? "Adicionalmente, y siempre que les sea posible, les agradeceríamos" : "Siempre que les sea posible, les agradeceríamos") +
      " que nos hicieran llegar también una imagen de cada una de las referencias señaladas, " +
      "identificada del mismo modo que se indica a continuación para el resto de la documentación."
  );
  hayContenidoPrevio = true;
  avisos.push(
    "Para facilitar la correcta clasificación y archivo, les rogamos que el nombre de cada " +
      "archivo que nos remitan —ficha técnica, ficha de seguridad o imagen— comience con el " +
      "código de artículo correspondiente" +
      (ejemploNombreArchivo ? `. Ejemplo: ${ejemploNombreArchivo}.` : ".") +
      " Un archivo nombrado únicamente con el código, sin nada más detrás, también es válido: " +
      "nuestro sistema lo asocia sin problema."
  );
  avisos.push(
    "Agradecemos de antemano su colaboración y quedamos a la espera de recibir la documentación " +
      "en cuanto les sea posible. No duden en contactar con nosotros ante cualquier consulta."
  );
  partes.push(avisos.join("\n"));

  // (2026-08-29) Firma al estilo del resto de correos de Control de
  // Pedidos a proveedores (mismo formato que _firma_comprador_text en su
  // app.py) — ver comentario largo de generarTextoEmail más arriba.
  const nombreFirma = firmaAdmin?.nombre || "";
  const emailFirma = firmaAdmin?.email || "";
  const movilFirma = firmaAdmin?.telefono ? formatearMovilFirma(firmaAdmin.telefono) : "";
  const lineasFirma = [];
  if (nombreFirma) lineasFirma.push(nombreFirma);
  lineasFirma.push("Dpto. Central de Compras Princess Canarias");
  lineasFirma.push("");
  lineasFirma.push("Av. Touroperador Tui, s/n");
  lineasFirma.push("35100 - Maspalomas (Gran Canaria)");
  if (movilFirma) lineasFirma.push(`(+34) ${movilFirma}`);
  if (emailFirma) lineasFirma.push(emailFirma);
  partes.push("Atentamente,\n\n" + lineasFirma.join("\n"));

  const asunto = `Documentación pendiente — ${grupo.proveedor}`;
  const cuerpo = partes.join("\n\n");

  return { asunto, cuerpo };
}

// mailto: no tiene un límite oficial, pero varios clientes de correo
// (Outlook en particular) truncan o fallan con cuerpos largos — por
// encima de este umbral se avisa de que "Copiar" es más fiable que
// abrir directamente el cliente de correo.
const AVISO_LONGITUD_MAILTO = 1500;

export default function EmailProveedorModal({ grupo, firmaAdmin, onClose }) {
  // (2026-09-02) Novena etapa de la auditoría full: este modal cerraba
  // con un simple onClick={onClose} en el fondo (.confirm-overlay), en
  // vez del hook compartido useCerrarAlClicFuera ya usado en
  // ArticuloForm.jsx/CargaMasivaModal.jsx/UsuarioForm.jsx — justo el
  // patrón que ese hook existe para evitar (ver su comentario): seleccionar
  // texto arrastrando el ratón y soltar el botón fuera del panel, aunque
  // sea por un píxel, se registra como un clic en el fondo (el evento
  // `click` se basa en dónde se SUELTA el botón, no en dónde se pulsó), así
  // que el modal se cerraba solo, perdiendo lo escrito. Este modal en
  // concreto tiene un `<textarea>` de 12 filas (el cuerpo del correo,
  // editable) y un campo de asunto — contenido que de verdad se selecciona
  // y edita a mano antes de enviar, a diferencia de un simple diálogo de
  // confirmación de texto corto — así que era el sitio con más
  // probabilidad real de sufrir justo este cierre accidental.
  const overlayHandlers = useCerrarAlClicFuera(onClose);

  const textoInicial = useMemo(() => generarTextoEmail(grupo, firmaAdmin), [grupo, firmaAdmin]);
  const [asunto, setAsunto] = useState(textoInicial.asunto);
  const [cuerpo, setCuerpo] = useState(textoInicial.cuerpo);
  const [copiado, setCopiado] = useState(false);
  const [errorCopia, setErrorCopia] = useState(null);

  // (2026-08-27, envío directo desde 2026-09-09) Estado del envío — ver
  // prepararEnvioDocumentacionFaltante en services/api.js y
  // enviarProveedorPorEmailjs en services/emailjs.js. "enviado" deja el
  // botón desactivado tras un envío correcto, para no mandar el mismo
  // correo dos veces sin querer si Víctor vuelve a pulsarlo.
  const [estadoEnvio, setEstadoEnvio] = useState("inicial"); // inicial | enviando | enviado | error
  const [errorEnvio, setErrorEnvio] = useState(null);
  // (2026-08-27) El destinatario real puede no ser grupo.email: si hay un
  // proveedor con el mismo nombre en Control de Pedidos, se usa SU
  // contacto principal (ver documentacionController.js) — se guarda lo
  // que confirma el backend para no dar por hecho cuál de los dos se usó.
  const [resultadoEnvio, setResultadoEnvio] = useState(null);

  const cuerpoLargo = cuerpo.length > AVISO_LONGITUD_MAILTO;

  // (2026-08-28) Vista previa del correo tal y como se enviará de
  // verdad (logo/colores de Control de Pedidos) — se pide al backend
  // en cada cambio de asunto/cuerpo, con debounce para no lanzar una
  // petición en cada pulsación de tecla (mismo criterio que los
  // buscadores, ver useDebouncedValue.js).
  const asuntoDebounced = useDebouncedValue(asunto, 400);
  const cuerpoDebounced = useDebouncedValue(cuerpo, 400);
  const [previewHtml, setPreviewHtml] = useState("");
  const [cargandoPreview, setCargandoPreview] = useState(true);
  const [errorPreview, setErrorPreview] = useState(null);

  useEffect(() => {
    let cancelado = false;
    setCargandoPreview(true);
    setErrorPreview(null);
    fetchPreviewEmailDocumentacion({ proveedor: grupo.proveedor, asunto: asuntoDebounced, cuerpo: cuerpoDebounced })
      .then(({ html }) => {
        if (!cancelado) setPreviewHtml(html);
      })
      .catch((e) => {
        if (!cancelado) setErrorPreview(e.message || "No se ha podido generar la vista previa del correo.");
      })
      .finally(() => {
        if (!cancelado) setCargandoPreview(false);
      });
    return () => {
      cancelado = true;
    };
  }, [grupo.proveedor, asuntoDebounced, cuerpoDebounced]);

  async function enviarEmail() {
    setEstadoEnvio("enviando");
    setErrorEnvio(null);
    try {
      const preparado = await prepararEnvioDocumentacionFaltante(grupo.id_proveedor, { asunto, cuerpo });
      const resultado = await enviarProveedorPorEmailjs({
        destinatario: preparado.destinatario,
        asunto: preparado.asunto,
        cuerpoHtml: preparado.cuerpoHtml,
        cuerpoText: preparado.cuerpoText,
        replyTo: preparado.replyTo,
        config: preparado.emailjs,
      });
      if (!resultado.enviado) {
        throw new Error(resultado.motivo || "No se ha podido enviar el correo.");
      }
      setResultadoEnvio(preparado);
      setEstadoEnvio("enviado");
    } catch (e) {
      setEstadoEnvio("error");
      setErrorEnvio(e.message || "No se ha podido enviar el correo.");
    }
  }

  async function copiar() {
    setErrorCopia(null);
    const texto = `Asunto: ${asunto}\n\n${cuerpo}`;
    try {
      await navigator.clipboard.writeText(texto);
      setCopiado(true);
      setTimeout(() => setCopiado(false), 2000);
    } catch {
      setErrorCopia("No se ha podido copiar automáticamente — selecciona el texto y cópialo a mano.");
    }
  }

  const mailtoHref = grupo.email
    ? `mailto:${grupo.email}?subject=${encodeURIComponent(asunto)}&body=${encodeURIComponent(cuerpo)}`
    : null;

  return (
    <div className="confirm-overlay" {...overlayHandlers}>
      <div className="confirm-box email-modal-box" onClick={(e) => e.stopPropagation()}>
        <h3>Email para {grupo.proveedor}</h3>
        <p>
          Revisa y ajusta el texto antes de enviarlo — la vista previa de abajo muestra el correo tal y
          como se enviará de verdad, con el mismo logo y colores que ya usan los correos de Control de
          Pedidos. "Enviar email" lo manda de verdad, al momento, al email guardado en Control de Pedidos
          para este proveedor — o puedes seguir copiando el texto o abriéndolo en tu propio cliente de
          correo, como antes.
        </p>

        <div className="field">
          <label>Asunto</label>
          <input
            type="text"
            value={asunto}
            onChange={(e) => {
              setAsunto(e.target.value);
              if (estadoEnvio !== "enviando") setEstadoEnvio("inicial");
            }}
          />
        </div>

        <div className="field">
          <label>Cuerpo</label>
          <textarea
            rows={12}
            value={cuerpo}
            onChange={(e) => {
              setCuerpo(e.target.value);
              if (estadoEnvio !== "enviando") setEstadoEnvio("inicial");
            }}
          />
        </div>

        <div className="field">
          <label>Vista previa del correo</label>
          {errorPreview ? (
            <p className="field-hint">{errorPreview}</p>
          ) : (
            <div className="email-preview-box" aria-busy={cargandoPreview}>
              {cargandoPreview && !previewHtml ? (
                <p className="field-hint">Generando vista previa…</p>
              ) : (
                <div dangerouslySetInnerHTML={{ __html: previewHtml }} />
              )}
            </div>
          )}
        </div>

        {estadoEnvio === "enviado" && (
          <div className="alert alert-ok">
            Enviado a {resultadoEnvio?.destinatario || grupo.email} — es el contacto guardado en Control de
            Pedidos para este proveedor. Si vuelves a editar el texto, puedes enviarlo de nuevo.
          </div>
        )}
        {estadoEnvio === "error" && <div className="alert alert-warn">{errorEnvio}</div>}

        {!grupo.email && (
          <p className="field-hint-block">
            Este proveedor todavía no tiene un email guardado en Control de Pedidos, así que solo puedes
            copiar el texto. Añádelo en Control de Pedidos → Proveedores para poder enviarlo directamente o
            abrirlo en tu cliente de correo la próxima vez.
          </p>
        )}

        {grupo.email && cuerpoLargo && (
          <p className="field-hint">
            El texto es largo — algunos clientes de correo recortan el cuerpo al abrir un enlace mailto:. Si
            "Abrir en tu cliente de correo" no trae todo el texto, usa "Copiar" y pégalo a mano.
          </p>
        )}

        {errorCopia && <p className="field-hint">{errorCopia}</p>}

        <div className="form-actions">
          <button type="button" className="btn btn-ghost btn-sm" onClick={onClose}>
            Cerrar
          </button>
          <button type="button" className="btn btn-ghost btn-sm" onClick={copiar}>
            {copiado ? "Copiado ✓" : "Copiar asunto y cuerpo"}
          </button>
          {mailtoHref && (
            <a className="btn btn-ghost btn-sm" href={mailtoHref}>
              Abrir en tu cliente de correo
            </a>
          )}
          {grupo.email && (
            <button
              type="button"
              className="btn btn-primary btn-sm"
              disabled={estadoEnvio === "enviando" || estadoEnvio === "enviado"}
              onClick={enviarEmail}
            >
              {estadoEnvio === "enviando"
                ? "Enviando…"
                : estadoEnvio === "enviado"
                ? "Enviado ✓"
                : "Enviar email"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
