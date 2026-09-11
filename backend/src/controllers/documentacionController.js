import ExcelJS from "exceljs";
import PDFDocument from "pdfkit";
import { supabase } from "../config/supabase.js";
import { construirHtmlReclamacionDocumentacion } from "../utils/emailHtml.js";
import {
  resolverEmailsProveedorEnControlPedidos,
  resolverEmailsProveedoresEnControlPedidos,
  resolverMovilCompradorEnControlPedidos,
} from "../services/controlPedidosEmailBridge.js";
import { obtenerConfiguracionEmailjsParaNavegador } from "../services/emailjsConfig.js";

const SUPABASE_MAX_ROWS_POR_PETICION = 1000; // ver nota en exportController.js

// (2026-09-02) Mismo tamaño de lote que `obtenerCodigosProveedorPorArticulos`
// en articulosController.js — un `.in("id_articulo", ...)` con miles de
// ids puede a su vez devolver más filas de las que Supabase entrega en
// una sola petición, así que también hace falta trocear los propios ids
// además de paginar cada lote con `.range()`.
const TAMANO_LOTE_IDS = 500;

/**
 * Trae de `tabla` únicamente las filas cuyo `id_articulo` esté entre
 * `idsArticulo` (troceado en lotes de `TAMANO_LOTE_IDS`, cada lote
 * paginado con `.range()` hasta agotarlo) — reemplaza a traer la tabla
 * COMPLETA sin filtrar, que es lo que hacía esta función hasta el
 * 2026-09-02.
 *
 * Antes, `imagenes`/`fichas`/`codigos_proveedor` se leían enteras en
 * cada carga de "Documentación faltante" (`GET
 * /admin/documentacion-faltante` y su exportación a Excel), incluyendo
 * filas de artículos DADOS DE BAJA que el resto de la función ni
 * siquiera llega a usar (el bucle final solo recorre `articulos`
 * activos) — cuanto más crecen esas tres tablas, más egress de más para
 * una pantalla que un admin puede abrir varias veces al día. Filtrar por
 * los ids de los artículos activos (ya resueltos justo antes, ver
 * `calcularDocumentacionFaltante`) trae solo lo que de verdad hace
 * falta.
 */
async function traerPorArticulos(tabla, columnas, idsArticulo) {
  const filas = [];
  for (let i = 0; i < idsArticulo.length; i += TAMANO_LOTE_IDS) {
    const loteIds = idsArticulo.slice(i, i + TAMANO_LOTE_IDS);
    let offset = 0;
    while (true) {
      const { data, error } = await supabase
        .from(tabla)
        .select(columnas)
        .in("id_articulo", loteIds)
        .range(offset, offset + SUPABASE_MAX_ROWS_POR_PETICION - 1);
      if (error) throw new Error(error.message);
      filas.push(...(data || []));
      if (!data || data.length < SUPABASE_MAX_ROWS_POR_PETICION) break;
      offset += SUPABASE_MAX_ROWS_POR_PETICION;
    }
  }
  return filas;
}

/**
 * Trae todos los artículos activos (paginando en tandas de 1000 —
 * mismo límite de Supabase/PostgREST ya documentado en
 * exportController.js), y toda la imagen/fichas, y calcula en JS qué le
 * falta a cada artículo. Se hace así en vez de con una consulta SQL
 * de un tirón porque supabase-js no tiene una forma directa de
 * expresar "NOT EXISTS en fichas" sin usar una vista o una función
 * RPC — y con ~6700 activos y unos pocos miles de fichas, hacerlo en
 * JS es rápido y no complica el esquema con nada nuevo.
 *
 * (2026-08-17) Desde que imagen/fichas se guardan una POR PROVEEDOR (ver
 * migración 2026-08-17_documentacion_por_proveedor.sql), "le falta la
 * imagen/ficha" ya no es tan simple como "¿existe alguna fila para este
 * id_articulo?" — puede existir, pero de OTRO proveedor (en reserva), lo
 * cual para efectos de "qué se está mostrando ahora mismo" es lo mismo
 * que no tenerla. Por eso aquí se compara siempre contra el
 * id_proveedor que cada artículo tiene asignado, no solo la presencia
 * de la fila.
 */
async function calcularDocumentacionFaltante() {
  const articulos = [];
  let offset = 0;
  while (true) {
    const { data, error } = await supabase
      .from("articulos")
      .select("id, codigo_dali, nombre_articulo, id_proveedor, proveedores(nombre_proveedor)")
      .eq("activo_dali", true)
      .eq("activo_general", true)
      .order("nombre_articulo")
      .range(offset, offset + SUPABASE_MAX_ROWS_POR_PETICION - 1);
    if (error) throw new Error(error.message);
    articulos.push(...(data || []));
    if (!data || data.length < SUPABASE_MAX_ROWS_POR_PETICION) break;
    offset += SUPABASE_MAX_ROWS_POR_PETICION;
  }

  // Map<id_articulo, Map<id_proveedor, { hash: hash_sha256|null, esGenerica: boolean }>>
  // — imagen guardada para ese artículo/proveedor, junto con su hash (null
  // si se subió antes de la migración 2026-08-18_hash_documentos.sql y
  // nunca se ha vuelto a subir desde entonces).
  //
  // (2026-08-20) También se cuenta, por proveedor, cuántos artículos
  // DISTINTOS comparten exactamente el mismo hash de imagen — señal de
  // reserva para filas ANTIGUAS que no traen `es_generica` marcado (ver
  // más abajo).
  //
  // (2026-09-01) Desde la migración 2026-09-01_es_generica_imagen.sql,
  // `imagenes.es_generica` marca EXPLÍCITAMENTE qué filas son la imagen de
  // reserva "SIN IMAGEN" del proveedor (grabado por `subirImagenArticulo`
  // al subir vía CargaMasivaModal.jsx) — ya no hace falta inferirlo. La
  // comparación de hash de abajo se mantiene solo como red de seguridad
  // para filas subidas ANTES de esa migración (`es_generica = false` en
  // todas por el `default false`, aunque de verdad fueran la genérica) —
  // en cuanto esa carga masiva se repita, la fila se regraba con
  // `es_generica` correcto y deja de depender del hash.
  //
  // (2026-09-02) Desde que `imagenes` se filtra por los artículos ACTIVOS
  // (ver `traerPorArticulos` más arriba, antes se traía la tabla entera
  // sin filtrar), este conteo por hash compartido ya solo ve coincidencias
  // entre artículos activos entre sí — si una fila antigua (sin
  // `es_generica`) comparte hash únicamente con un artículo YA DADO DE
  // BAJA, deja de contar como "compartida" y esa imagen concreta pasa de
  // `imagen_generica: true` a `null` en vez de detectarse por esta señal
  // de reserva. Impacto acotado a filas previas a la migración
  // 2026-09-01_es_generica_imagen.sql (las nuevas ya se marcan de forma
  // explícita, sin depender de este conteo) y solo afecta al aviso
  // informativo "es la imagen genérica del proveedor", no a si falta o no
  // la imagen — que sigue siendo exacto.
  const idsArticulosActivos = articulos.map((a) => a.id);

  // (2026-09-03) Las tres consultas de abajo (imágenes, fichas, códigos
  // de proveedor) son totalmente independientes entre sí — cada una
  // filtra por los mismos `idsArticulosActivos` pero contra una tabla
  // distinta, ninguna necesita el resultado de otra. Hasta ahora se
  // pedían una detrás de otra (`await` secuencial), sumando sus tres
  // tiempos de red en vez de solaparlos — a petición de Víctor
  // ("¿SERA PORQUE NO TIENE PAGINACION COMO EL RESTO?"): la causa real
  // de la lentitud de esta pantalla no es la falta de paginación en el
  // frontend, sino que este es un INFORME agregado sobre todo el
  // catálogo activo (agrupado por proveedor) y no un listado paginable
  // artículo a artículo como el catálogo principal — necesita traer y
  // cruzar TODO para poder mostrar los totales y los grupos correctos,
  // así que paginar la respuesta no encajaría con lo que pide esta
  // pantalla. Lo que sí se puede acortar es el tiempo de red: al
  // lanzar las tres peticiones a la vez con `Promise.all` en vez de
  // una tras otra, el tiempo total pasa a ser (aproximadamente) el de
  // la más lenta de las tres, no la suma de las tres.
  const [filasImagenes, filasFichas, filasCodigos] = await Promise.all([
    traerPorArticulos("imagenes", "id_articulo, id_proveedor, hash_sha256, es_generica", idsArticulosActivos),
    traerPorArticulos("fichas", "id_articulo, tipo, id_proveedor", idsArticulosActivos),
    traerPorArticulos("codigos_proveedor", "id_articulo, id_proveedor, codigo", idsArticulosActivos),
  ]);

  const imagenPorArticulo = new Map();
  const conteoHashPorProveedor = new Map(); // Map<"idProveedor::hash", Set<id_articulo>>
  for (const img of filasImagenes) {
    if (!imagenPorArticulo.has(img.id_articulo)) imagenPorArticulo.set(img.id_articulo, new Map());
    imagenPorArticulo
      .get(img.id_articulo)
      .set(img.id_proveedor, { hash: img.hash_sha256 || null, esGenerica: img.es_generica === true });
    if (img.hash_sha256) {
      const clave = `${img.id_proveedor}::${img.hash_sha256}`;
      if (!conteoHashPorProveedor.has(clave)) conteoHashPorProveedor.set(clave, new Set());
      conteoHashPorProveedor.get(clave).add(img.id_articulo);
    }
  }

  // Map<id_articulo, Map<tipo, Set<id_proveedor>>>
  const proveedoresConFicha = new Map();
  for (const f of filasFichas) {
    if (!proveedoresConFicha.has(f.id_articulo)) proveedoresConFicha.set(f.id_articulo, new Map());
    const porTipo = proveedoresConFicha.get(f.id_articulo);
    if (!porTipo.has(f.tipo)) porTipo.set(f.tipo, new Set());
    porTipo.get(f.tipo).add(f.id_proveedor);
  }

  // Map<id_articulo, Map<id_proveedor, codigo>> — código con el que CADA
  // proveedor identifica ese artículo (ver migración
  // 2026-08-20_codigos_proveedor.sql). Se resuelve igual que
  // imagen/fichas: solo interesa el código del proveedor ASIGNADO del
  // artículo, no los de otros proveedores "en reserva".
  //
  // (2026-08-25) Petición de Víctor: al reclamar documentación a un
  // proveedor, referenciar cada artículo con SU código (el que él usa
  // para identificarlo), no con el código DALI ni el SAP — esos no le
  // dicen nada a un proveedor externo. Cuando no hay código de
  // proveedor guardado para ese artículo (columna sin rellenar todavía,
  // carga masiva que nunca capturó ese dato, o alta manual), se usa el
  // nombre del artículo como referencia de reserva — ver `codigo_proveedor:
  // null` más abajo y su uso en el frontend.
  const codigoProveedorPorArticulo = new Map();
  for (const c of filasCodigos) {
    if (!codigoProveedorPorArticulo.has(c.id_articulo)) {
      codigoProveedorPorArticulo.set(c.id_articulo, new Map());
    }
    codigoProveedorPorArticulo.get(c.id_articulo).set(c.id_proveedor, c.codigo);
  }

  const filasIncompletas = [];
  for (const a of articulos) {
    const filaImagen = imagenPorArticulo.get(a.id)?.get(a.id_proveedor); // undefined | { hash, esGenerica }
    const tieneImagen = filaImagen !== undefined;
    const tieneTecnica = proveedoresConFicha.get(a.id)?.get("tecnica")?.has(a.id_proveedor) ?? false;
    const tieneSeguridad = proveedoresConFicha.get(a.id)?.get("seguridad")?.has(a.id_proveedor) ?? false;
    const faltaImagen = !tieneImagen;
    const faltaFichaTecnica = !tieneTecnica;
    const faltaFichaSeguridad = !tieneSeguridad;
    if (!faltaImagen && !faltaFichaTecnica && !faltaFichaSeguridad) continue; // completo, no interesa

    // true = imagen genérica de reserva del proveedor (tipo "SIN
    // IMAGEN"); false = foto propia del material; null = hay imagen pero
    // no se puede determinar (fila anterior a la migración de hash, sin
    // hash_sha256 guardado, y tampoco marcada `es_generica`) o
    // directamente no hay imagen. Prioridad: `es_generica` explícito
    // (2026-09-01) si está marcado; si no, la vieja señal por hash
    // compartido, para no perder la distinción en filas antiguas que
    // todavía no se han vuelto a subir desde esa migración.
    let imagenGenerica = null;
    if (tieneImagen) {
      if (filaImagen.esGenerica) {
        imagenGenerica = true;
      } else if (filaImagen.hash) {
        imagenGenerica = (conteoHashPorProveedor.get(`${a.id_proveedor}::${filaImagen.hash}`)?.size ?? 0) > 1;
      }
    }

    filasIncompletas.push({
      codigo_dali: a.codigo_dali,
      nombre_articulo: a.nombre_articulo,
      proveedor: a.proveedores?.nombre_proveedor || null,
      id_proveedor: a.id_proveedor ?? null,
      codigo_proveedor: codigoProveedorPorArticulo.get(a.id)?.get(a.id_proveedor) || null,
      falta_imagen: faltaImagen,
      falta_ficha_tecnica: faltaFichaTecnica,
      falta_ficha_seguridad: faltaFichaSeguridad,
      imagen_generica: imagenGenerica,
    });
  }

  // Agrupado por proveedor — "Sin proveedor asignado" al final,
  // el resto por orden alfabético.
  const porProveedor = new Map();
  for (const fila of filasIncompletas) {
    const clave = fila.id_proveedor ?? "sin-proveedor";
    if (!porProveedor.has(clave)) {
      porProveedor.set(clave, {
        id_proveedor: fila.id_proveedor,
        proveedor: fila.proveedor || "Sin proveedor asignado",
        email: null, // se rellena justo abajo, resuelto contra Control de Pedidos
        articulos: [],
      });
    }
    porProveedor.get(clave).articulos.push(fila);
  }
  const grupos = [...porProveedor.values()].sort((a, b) => {
    if (a.id_proveedor === null) return 1;
    if (b.id_proveedor === null) return -1;
    return a.proveedor.localeCompare(b.proveedor, "es");
  });

  // (2026-08-28) A petición de Víctor: "olvidar el correo grabado en
  // Catálogo Dalí, borrar esta info, utilizar únicamente los correos de
  // la base de datos proveedores control pedidos" — DALI ya no guarda
  // ningún email propio de proveedor (ver migración
  // 2026-08-28_borrar_email_proveedor_dali.sql); el que se muestra aquí
  // y el que se usa para encolar el envío (ver
  // encolarEmailDocumentacionFaltante más abajo) sale SIEMPRE de los
  // contactos marcados como principales del proveedor equivalente en
  // control-pedidos-princess, cruzado por nombre. Se resuelve en UNA
  // sola llamada al puente para todos los grupos a la vez
  // (resolverEmailsProveedoresEnControlPedidos), en vez de una por
  // proveedor. Si el puente no está configurado o la llamada falla
  // (servicio caído, red…), no se rompe la pantalla — se deja
  // `email: null` en todos los grupos y se avisa aparte en
  // `aviso_bridge`, para que el frontend lo muestre sin impedir ver la
  // documentación faltante en sí (que no depende de esto).
  //
  // (2026-08-31) `grupo.email` puede traer VARIOS emails separados por
  // ", " — Víctor: "la ficha de proveedores de control pedidos tiene la
  // opcion de marcar aquellos correos que estan destinados al envio", y
  // un proveedor puede tener más de un contacto marcado a la vez (ver
  // `resolverEmailsProveedoresEnControlPedidos`, que ahora devuelve un
  // array por proveedor en vez de un único email). Se deja como texto
  // unido aquí a propósito, sin tocar el frontend: sirve tal cual como
  // display informativo (AdminDocumentacionFaltante.jsx) y como target
  // de un `mailto:` con varios destinatarios (EmailProveedorModal.jsx,
  // que ya admite la sintaxis `mailto:a@x,b@y` sin cambios); el envío
  // real por Control de Pedidos (más abajo) no depende de este campo,
  // usa el array completo directamente.
  let avisoBridge = null;
  const nombresAResolver = grupos.filter((g) => g.id_proveedor !== null).map((g) => g.proveedor);
  if (nombresAResolver.length > 0) {
    try {
      const emailsPorNombre = await resolverEmailsProveedoresEnControlPedidos(nombresAResolver);
      for (const grupo of grupos) {
        if (grupo.id_proveedor !== null) {
          const emails = emailsPorNombre.get(grupo.proveedor) || [];
          grupo.email = emails.length > 0 ? emails.join(", ") : null;
        }
      }
    } catch (e) {
      avisoBridge =
        "No se ha podido consultar Control de Pedidos para resolver los emails de los proveedores " +
        `(${e.message}) — vuelve a intentarlo en unos minutos.`;
    }
  }

  return {
    grupos,
    total_articulos: filasIncompletas.length,
    total_activos: articulos.length,
    aviso_bridge: avisoBridge,
  };
}

/**
 * (2026-08-29) Nombre/email/teléfono del admin autenticado, para firmar
 * el correo de "Documentación faltante" que va a generarse en el
 * frontend (EmailProveedorModal.jsx) — a petición de Víctor: "en este
 * caso incluir el nombre, telefono, correo del admin que realiza la
 * gestion". Nombre/email ya están en `req.user` (cookie de sesión, sin
 * red); el teléfono NO existe en ningún campo de DALI (su tabla
 * `usuarios` nunca ha tenido esa columna), así que se resuelve contra
 * control-pedidos-princess cruzando por email — Víctor: "¿puedes coger
 * la info de la ficha usuarios control pedidos? los admin son los
 * mismos y los compradores son admin en catalogo dali". Si el puente
 * falla o no hay ningún comprador con ese email allí, `telefono` queda
 * en `null` y la firma simplemente omite esa línea — igual que hace
 * Control de Pedidos cuando a un comprador no le tiene guardado el
 * móvil, esto no debe impedir generar ni enviar el correo.
 */
async function resolverFirmaAdmin(req) {
  const nombre = req.user?.nombre || "";
  const email = req.user?.email || "";
  let telefono = null;
  try {
    telefono = await resolverMovilCompradorEnControlPedidos(email);
    // (2026-08-31) Log de diagnóstico — a petición de Víctor, el teléfono
    // seguía sin aparecer tras confirmar que "Documentación faltante" ya
    // corría en v1.19.5 (backend con el fix desplegado, log de Render
    // verificado). Sin este aviso, "no hay teléfono" y "el puente falló"
    // son indistinguibles desde fuera — este log en los logs de Render de
    // este servicio (backend) deja ver cuál de los dos está pasando de
    // verdad, sin cambiar el comportamiento: la firma se sigue generando
    // igual, con o sin teléfono, esto es solo para poder depurarlo.
    if (!telefono) {
      console.warn(
        `[FIRMA-ADMIN] Sin teléfono para "${email}" — Control de Pedidos respondió sin error pero ningún ` +
          "comprador/admin activo tiene ese email exacto guardado allí, o no tiene móvil relleno."
      );
    }
  } catch (e) {
    console.error(`[FIRMA-ADMIN] No se ha podido resolver el teléfono de "${email}" contra Control de Pedidos: ${e.message}`);
    telefono = null; // puente caído/no configurado — la firma se genera igual, sin teléfono
  }
  return { nombre, email, telefono };
}

/** GET /admin/documentacion-faltante */
export async function obtenerDocumentacionFaltante(req, res) {
  try {
    const [resultado, firmaAdmin] = await Promise.all([
      calcularDocumentacionFaltante(),
      resolverFirmaAdmin(req),
    ]);
    res.json({ ...resultado, firma_admin: firmaAdmin });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

/**
 * GET /admin/documentacion-faltante/excel — mismo cálculo, en un
 * .xlsx con una hoja por proveedor (o una sola hoja con separadores
 * si hay demasiados proveedores para pestañas manejables — Excel
 * limita el nombre de hoja a 31 caracteres y no admite ciertos
 * símbolos, así que con más de ~20 proveedores se usa una sola hoja
 * agrupada, más fácil de manejar que decenas de pestañas).
 */
export async function exportarDocumentacionFaltanteExcel(_req, res) {
  try {
    const { grupos } = await calcularDocumentacionFaltante();

    const workbook = new ExcelJS.Workbook();
    const LIMITE_HOJAS_SEPARADAS = 20;
    const columnas = [
      { header: "Código DALI", key: "codigo_dali", width: 14 },
      // (2026-08-25) Código propio del proveedor (ver migración
      // 2026-08-20_codigos_proveedor.sql) — a petición de Víctor, para
      // poder reclamar documentación referenciando cada artículo con el
      // código que el PROVEEDOR usa, no con el código DALI (que no le
      // dice nada). Puede venir vacío si nunca se ha capturado ese dato
      // para este artículo/proveedor.
      { header: "Código proveedor", key: "codigo_proveedor", width: 18 },
      { header: "Artículo", key: "nombre_articulo", width: 55 },
      { header: "Falta imagen", key: "falta_imagen", width: 14 },
      { header: "Falta ficha técnica", key: "falta_ficha_tecnica", width: 18 },
      { header: "Falta ficha seguridad", key: "falta_ficha_seguridad", width: 20 },
    ];
    const filaComoTexto = (a) => ({
      codigo_dali: a.codigo_dali,
      codigo_proveedor: a.codigo_proveedor || "",
      nombre_articulo: a.nombre_articulo,
      falta_imagen: a.falta_imagen ? "SI" : "",
      falta_ficha_tecnica: a.falta_ficha_tecnica ? "SI" : "",
      falta_ficha_seguridad: a.falta_ficha_seguridad ? "SI" : "",
    });

    if (grupos.length <= LIMITE_HOJAS_SEPARADAS) {
      for (const grupo of grupos) {
        // Nombre de hoja válido en Excel: máx 31 caracteres, sin : \ / ? * [ ]
        const nombreHoja = grupo.proveedor.replace(/[:\\/?*[\]]/g, "").slice(0, 31) || "Sin proveedor";
        const sheet = workbook.addWorksheet(nombreHoja);
        sheet.columns = columnas;
        sheet.getRow(1).font = { bold: true };
        sheet.getRow(1).eachCell((c) => {
          c.fill = { type: "pattern", pattern: "solid", fgColor: { argb: "FFE5DECB" } };
        });
        grupo.articulos.forEach((a) => sheet.addRow(filaComoTexto(a)));
      }
    } else {
      const sheet = workbook.addWorksheet("Documentación faltante");
      sheet.columns = [{ header: "Proveedor", key: "proveedor", width: 32 }, ...columnas];
      sheet.getRow(1).font = { bold: true };
      sheet.getRow(1).eachCell((c) => {
        c.fill = { type: "pattern", pattern: "solid", fgColor: { argb: "FFE5DECB" } };
      });
      for (const grupo of grupos) {
        grupo.articulos.forEach((a) =>
          sheet.addRow({ proveedor: grupo.proveedor, ...filaComoTexto(a) })
        );
      }
    }

    res.setHeader(
      "Content-Type",
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    );
    res.setHeader("Content-Disposition", "attachment; filename=documentacion-faltante.xlsx");
    await workbook.xlsx.write(res);
    res.end();
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

/**
 * POST /admin/documentacion-faltante/:idProveedor/preparar-envio
 * Body: `{ asunto, cuerpo }` — el texto ya redactado y revisado por
 * Víctor en EmailProveedorModal.jsx (mismo `generarTextoEmail()` de
 * siempre, editable antes de enviar).
 *
 * (2026-08-27, encolaba en Control de Pedidos; 2026-09-09, envío directo
 * por el EmailJS propio de DALI — ver más abajo) Resuelve en el servidor
 * todo lo que hace falta para enviar este correo — destinatario real,
 * HTML ya maquetado, credenciales EmailJS de la cuenta activa (la misma
 * plantilla "de usuario" de siempre, `template_id_N` — ver más abajo) —
 * y se lo devuelve al frontend, que es quien de verdad llama a
 * `emailjs.send()` desde el navegador del admin que tiene la sesión
 * abierta (ver EmailProveedorModal.jsx, `enviarProveedorPorEmailjs` en
 * services/emailjs.js). Este endpoint NO envía nada por sí mismo: solo
 * prepara. El destinatario se resuelve aquí, en el servidor — no se
 * confía en ninguno que pueda llegar del cliente — para no poder
 * redirigir el envío a una dirección distinta con solo manipular la
 * petición.
 *
 * (2026-09-09) A petición de Víctor: "necesito que la aplicacion
 * catalogo asignaciones utilice su propio emailjs para solicitar la
 * documentacion faltante, actualmente se encola y se envia desde
 * control pedidos, pero como ya tenemos configurada propia cuenta de
 * emailjs" — hasta ahora este endpoint (entonces `POST
 * .../encolar-email`) encolaba el correo en `emails_sistema_pendientes`
 * de control-pedidos-princess (ver services/controlPedidosEmailBridge.js,
 * `encolarEmailEnControlPedidos`, ya eliminada) y el envío real lo hacía
 * el poller de esa app, la próxima vez que alguien la tuviera abierta —
 * dependencia que DALI ya había quitado para el resto de sus correos
 * desde v1.15 (ver migración 2026-09-02_tokens_acceso_emailjs.sql), pero
 * que quedó pendiente para este caso concreto (nota de alcance explícita
 * en esa misma migración). El Reply-To dinámico (comprador que gestiona
 * la solicitud, ver v1.19.57/HISTORIAL v1.39) ya no necesita el truco del
 * puente: la plantilla "de usuario" de siempre (`template_id_N`, ver
 * services/emailjsConfig.js) ya tenía `{{reply_to}}` puesto en su campo
 * "Reply To" en EmailJS.com desde el principio — no hizo falta ninguna
 * plantilla nueva (un primer intento en v1.19.60 sí creó una separada,
 * revertido en v1.19.62 al comprobarlo, ver HISTORIAL v1.44).
 *
 * Se sigue usando `resolverEmailsProveedorEnControlPedidos` para el
 * DESTINATARIO — eso no cambia: Control de Pedidos sigue siendo la única
 * fuente del email del proveedor (ver el comentario grande más abajo,
 * heredado de cuando este endpoint se llamaba `encolarEmailDocumentacionFaltante`),
 * lo único que deja de depender de esa app es el ENVÍO en sí.
 *
 * (2026-08-28) A petición de Víctor: "olvidar el correo grabado en
 * Catálogo Dalí, borrar esta info, utilizar únicamente los correos de
 * la base de datos proveedores control pedidos" — se ha eliminado el
 * fallback al email propio de DALI que existía hasta ahora
 * (`proveedores.email`, ver migración
 * 2026-08-28_borrar_email_proveedor_dali.sql, que borra esa columna).
 * El ÚNICO origen posible del destinatario es
 * `resolverEmailsProveedorEnControlPedidos` (por NOMBRE exacto contra los
 * proveedores de control-pedidos-princess — Víctor mantiene los nombres
 * idénticos entre las dos apps a propósito, ver HISTORIAL.md v0.83). Si
 * no hay proveedor con ese nombre en Control de Pedidos, si ninguno de
 * sus contactos tiene email, o si la llamada al puente falla, se
 * devuelve error explicando que hay que añadir/revisar el email en
 * Control de Pedidos → Proveedores — nunca en DALI, que ya no guarda
 * ninguno.
 *
 * (2026-08-31) Un proveedor puede tener VARIOS contactos marcados como
 * principales a la vez en Control de Pedidos (la estrella dorada admite
 * más de uno) — Víctor, tras comprobar que a MILO CANARIAS, con Juan
 * Pedro y Nicet Marquez marcados los dos, solo le llegó a Juan Pedro:
 * "porque se envio solo al primer correo si tengo los dos marcardos
 * para envio?". Causa: `resolverEmailsProveedorEnControlPedidos` (antes
 * `resolverEmailProveedorEnControlPedidos`, singular) devolvía un único
 * email — ver el comentario de `emailsPrincipalesDe` en
 * `controlPedidosEmailBridge.js` para el detalle completo. Ahora
 * devuelve la lista completa.
 *
 * Un único correo con todos los contactos principales juntos en el
 * "Para:" — no uno por destinatario. Víctor: "si hay tres correos
 * marcados con la estrella en un proveedor, se envian 3 correos por
 * separado? esto no es correcto, se debe enviar un unico correo pero a
 * todos los destinatarios a la vez" — EmailJS admite varias direcciones
 * separadas por comas en un solo campo `to_email`, así que basta con
 * unir los emails resueltos con ", " en un único `destinatario`.
 *
 * Si el puente con Control de Pedidos falla al resolver el destinatario,
 * o si la plantilla EmailJS de proveedor todavía no está configurada, se
 * devuelve un error claro — el modal sigue ofreciendo copiar/mailto como
 * alternativa manual, esto no lo sustituye, solo se suma.
 */
export async function prepararEnvioDocumentacionFaltante(req, res) {
  try {
    const idProveedor = Number(req.params.idProveedor);
    if (!Number.isInteger(idProveedor)) {
      return res.status(400).json({ error: "id de proveedor inválido." });
    }

    const asunto = String(req.body?.asunto || "").trim();
    const cuerpo = String(req.body?.cuerpo || "").trim();
    if (!asunto || !cuerpo) {
      return res.status(400).json({ error: "Faltan asunto o cuerpo del correo." });
    }

    const { data: proveedor, error: proveedorError } = await supabase
      .from("proveedores")
      .select("id, nombre_proveedor")
      .eq("id", idProveedor)
      .maybeSingle();
    if (proveedorError) return res.status(500).json({ error: proveedorError.message });
    if (!proveedor) return res.status(404).json({ error: "Proveedor no encontrado." });

    let destinatarios = [];
    try {
      destinatarios = await resolverEmailsProveedorEnControlPedidos(proveedor.nombre_proveedor);
    } catch (e) {
      return res.status(502).json({
        error:
          `No se ha podido consultar Control de Pedidos para resolver el email de "${proveedor.nombre_proveedor}": ${e.message}`,
      });
    }
    if (destinatarios.length === 0) {
      return res.status(400).json({
        error:
          `No hay ningún email guardado para "${proveedor.nombre_proveedor}" en Control de Pedidos — ` +
          "añádelo ahí (Proveedores → contactos del proveedor) antes de enviar.",
      });
    }

    const cuerpoHtml = construirHtmlReclamacionDocumentacion({
      proveedor: proveedor.nombre_proveedor,
      asunto,
      cuerpo,
    });

    // Un único correo con todos los contactos principales juntos en el
    // "Para:" — no uno por destinatario (ver comentario de arriba).
    const destinatario = destinatarios.join(", ");
    // (2026-09-07) Si el proveedor responde a este correo, debe llegarle
    // al comprador que lo gestionó, no a un buzón fijo. `req.user.email`
    // es el mismo email de sesión que ya usa `resolverFirmaAdmin` para
    // firmar el cuerpo del correo — no hace falta resolverlo aparte. Se
    // envía tal cual al frontend, que lo pasa como variable `reply_to`
    // a la plantilla EmailJS de proveedor (Reply To dinámico).
    const replyTo = req.user?.email || null;

    const emailjs = await obtenerConfiguracionEmailjsParaNavegador();

    res.json({ ok: true, destinatarios, destinatario, asunto, cuerpoHtml, cuerpoText: cuerpo, replyTo, emailjs });
  } catch (err) {
    res.status(502).json({
      error: `No se ha podido preparar el envío: ${err.message} — puedes seguir usando "Copiar" o "Abrir en tu cliente de correo".`,
    });
  }
}

/**
 * POST /admin/documentacion-faltante/preview-email
 * Body: `{ proveedor, asunto, cuerpo }` → `{ html }`.
 *
 * (2026-08-28) A petición de Víctor: la ventana de "Generar email" debe
 * mostrar una vista previa real del correo — con el mismo logo/colores
 * que control-pedidos-princess, no solo el asunto/cuerpo en texto plano
 * — igual que ya hace esa app en su propia "Notificación de alerta"
 * (ver `#mea-body-preview` en su `templates/index.html`). En vez de
 * duplicar en el frontend la lógica de `construirHtmlReclamacionDocumentacion`
 * (utils/emailHtml.js) — con el riesgo de que las dos versiones acaben
 * divergiendo — EmailProveedorModal.jsx llama aquí (con un pequeño
 * debounce mientras se edita, `useDebouncedValue`) para pedir SIEMPRE
 * el HTML generado por la misma función que de verdad se encola al
 * pulsar "Encolar envío": lo que se ve en la vista previa es exactamente
 * lo que recibirá el proveedor.
 *
 * No hace ninguna consulta a la base de datos (no necesita `idProveedor`,
 * solo el nombre del proveedor para el título de la cabecera) — es una
 * función pura, segura de llamar en cada pulsación de tecla sin más
 * coste que el propio texto.
 */
export async function previsualizarEmailDocumentacionFaltante(req, res) {
  try {
    const proveedor = String(req.body?.proveedor || "").trim();
    const asunto = String(req.body?.asunto || "").trim();
    const cuerpo = String(req.body?.cuerpo || "").trim();
    if (!proveedor) return res.status(400).json({ error: "Falta el nombre del proveedor." });

    const html = construirHtmlReclamacionDocumentacion({ proveedor, asunto, cuerpo });
    res.json({ html });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

const MARGEN_PDF_DOC_FALTANTE = 30;
const ALTO_FILA_PDF_DOC_FALTANTE = 16;
const ALTO_CABECERA_PDF_DOC_FALTANTE = 22;

// (2026-09-11) Columnas del PDF de documentación pendiente por proveedor
// — mismo orden y mismo criterio que ya usa `exportarDocumentacionFaltanteExcel`
// más arriba (Código DALI, Código proveedor, Artículo, y las tres
// columnas de "falta X"), para que el PDF y el Excel de esta misma
// pantalla se lean igual. Aparte, no reutilizada, porque esa función
// trabaja con ExcelJS (`sheet.addRow(objeto)`) y esta con PDFKit
// (dibujo manual celda a celda) — mismo criterio de "controllers/ y
// workers/ no se cruzan" ya documentado en exportController.js, aquí
// aplicado a dos formatos dentro del mismo controlador.
const COLUMNAS_PDF_DOC_FALTANTE = [
  { titulo: "Código DALI", ancho: 62, valor: (a) => String(a.codigo_dali) },
  { titulo: "Código Proveedor", ancho: 110, valor: (a) => a.codigo_proveedor || "—" },
  { titulo: "Artículo", ancho: 280, valor: (a) => a.nombre_articulo },
  { titulo: "Ficha técnica", ancho: 90, valor: (a) => (a.falta_ficha_tecnica ? "Falta" : "OK") },
  { titulo: "Ficha de seguridad", ancho: 100, valor: (a) => (a.falta_ficha_seguridad ? "Falta" : "OK") },
  { titulo: "Imagen", ancho: 90, valor: (a) => (a.falta_imagen ? "Falta" : "OK") },
];

/**
 * (2026-09-11, a petición de Víctor) Genera en PDFKit el listado completo
 * de documentación pendiente de UN proveedor, con una columna por tipo
 * de documento (ficha técnica / ficha de seguridad / imagen) marcando
 * qué le falta a cada artículo — pensado para sustituir, cuando el
 * listado es muy largo, a la lista de "* código — artículo" que hasta
 * ahora se metía entera dentro del cuerpo del correo (ver
 * `generarTextoEmail` en EmailProveedorModal.jsx: por encima de cierto
 * número de referencias, el correo enlaza aquí en vez de listarlas una
 * a una). A diferencia de esa lista (que solo itemizaba la ficha
 * técnica), este PDF es el listado COMPLETO de todo lo pendiente del
 * proveedor — las tres columnas, para cualquier artículo al que le
 * falte algo — un documento de referencia más completo para el
 * proveedor, no solo un sustituto 1:1 de la lista que reemplaza.
 *
 * Mismo estilo visual (colores, tipografía, pie de página) que
 * `generarPdfBuffer()` en `generarExportWorker.js`, pero SIN pasar por
 * un hilo aparte: aquí el volumen es, como mucho, el catálogo completo
 * de UN proveedor (cientos de artículos, no las ~30.000 filas del
 * catálogo entero que causaron el "out of memory" corregido en
 * v1.19.66) — el mismo orden de magnitud que ya genera síncronamente
 * `exportarDocumentacionFaltanteExcel()` justo arriba en este mismo
 * fichero, sin que eso haya dado ningún problema.
 */
function generarPdfDocumentacionFaltante(articulos, proveedor) {
  return new Promise((resolve, reject) => {
    const doc = new PDFDocument({ margin: MARGEN_PDF_DOC_FALTANTE, size: "A4", layout: "landscape" });
    const trozos = [];
    doc.on("data", (trozo) => trozos.push(trozo));
    doc.on("end", () => resolve(Buffer.concat(trozos)));
    doc.on("error", reject);

    const altoPagina = doc.page.height;
    const anchoTabla = COLUMNAS_PDF_DOC_FALTANTE.reduce((suma, c) => suma + c.ancho, 0);
    let numeroPagina = 1;

    function dibujarPiePagina() {
      const yGuardado = doc.y;
      const margenInferiorGuardado = doc.page.margins.bottom;
      doc.page.margins.bottom = 0;
      doc
        .fontSize(7)
        .font("Helvetica")
        .fillColor("#888888")
        .text(`Página ${numeroPagina}`, MARGEN_PDF_DOC_FALTANTE, altoPagina - MARGEN_PDF_DOC_FALTANTE + 8, {
          width: anchoTabla,
          align: "right",
        });
      doc.fillColor("black");
      doc.page.margins.bottom = margenInferiorGuardado;
      doc.y = yGuardado;
    }

    function dibujarCabeceraTabla() {
      const y = doc.y;
      doc.rect(MARGEN_PDF_DOC_FALTANTE, y, anchoTabla, ALTO_CABECERA_PDF_DOC_FALTANTE).fill("#e5decb");
      doc.fillColor("#3a2f1f").font("Helvetica-Bold").fontSize(8);
      let x = MARGEN_PDF_DOC_FALTANTE;
      for (const col of COLUMNAS_PDF_DOC_FALTANTE) {
        doc.text(col.titulo.toUpperCase(), x + 4, y + 7, {
          width: col.ancho - 8,
          height: ALTO_CABECERA_PDF_DOC_FALTANTE - 4,
          ellipsis: true,
          lineBreak: false,
        });
        x += col.ancho;
      }
      doc.fillColor("black").font("Helvetica");
      doc.y = y + ALTO_CABECERA_PDF_DOC_FALTANTE;
    }

    function dibujarCabeceraPagina(esPrimeraPagina) {
      if (esPrimeraPagina) {
        doc
          .fontSize(15)
          .font("Helvetica-Bold")
          .text(`Documentación pendiente — ${proveedor}`, MARGEN_PDF_DOC_FALTANTE, MARGEN_PDF_DOC_FALTANTE, {
            width: anchoTabla,
          });
        doc
          .fontSize(8)
          .font("Helvetica")
          .fillColor("#666666")
          .text(
            `Generado el ${new Date().toLocaleString("es-ES")} · ${articulos.length} referencia(s) con documentación pendiente`,
            MARGEN_PDF_DOC_FALTANTE,
            doc.y + 2
          )
          .fillColor("black");
        doc.moveDown(0.8);
      }
      dibujarCabeceraTabla();
    }

    function asegurarEspacio(altoNecesario) {
      if (doc.y + altoNecesario > altoPagina - MARGEN_PDF_DOC_FALTANTE) {
        dibujarPiePagina();
        doc.addPage();
        numeroPagina++;
        doc.y = MARGEN_PDF_DOC_FALTANTE;
        dibujarCabeceraPagina(false);
      }
    }

    dibujarCabeceraPagina(true);

    articulos.forEach((a, i) => {
      asegurarEspacio(ALTO_FILA_PDF_DOC_FALTANTE);
      const y = doc.y;
      if (i % 2 === 0) {
        doc.rect(MARGEN_PDF_DOC_FALTANTE, y, anchoTabla, ALTO_FILA_PDF_DOC_FALTANTE).fill("#faf7f0");
      }
      doc.fillColor("black").fontSize(8);
      let x = MARGEN_PDF_DOC_FALTANTE;
      for (const col of COLUMNAS_PDF_DOC_FALTANTE) {
        const texto = col.valor(a);
        // "Falta" en rojo, para que salte a la vista de un vistazo cuál
        // de las tres columnas es la que de verdad falta en cada fila
        // (no todas las filas tienen los tres tipos pendientes a la vez).
        if (texto === "Falta") doc.fillColor("#8a4040");
        doc.text(texto, x + 4, y + 4, {
          width: col.ancho - 8,
          height: ALTO_FILA_PDF_DOC_FALTANTE - 4,
          ellipsis: true,
          lineBreak: false,
        });
        doc.fillColor("black");
        x += col.ancho;
      }
      doc.y = y + ALTO_FILA_PDF_DOC_FALTANTE;
    });

    dibujarPiePagina();
    doc.end();
  });
}

/**
 * GET /export/documentacion-faltante-pdf/:idProveedor — PÚBLICO, sin
 * sesión (ver `routes/export.js`, mismo router y mismo criterio de
 * "descarga pública" que ya usan `GET /export/excel` y `GET
 * /export/pdf`): el destinatario de este enlace es el PROPIO proveedor
 * externo, dentro del correo de "Documentación pendiente" que genera
 * `EmailProveedorModal.jsx` — un proveedor no tiene ninguna cuenta en
 * DALI con la que iniciar sesión, así que este endpoint no puede vivir
 * bajo `/admin` (protegido por `requierePermiso`) como el resto de
 * "Documentación faltante".
 *
 * A propósito NO usa un token de un solo uso ni caduca: recalcula la
 * documentación pendiente de este proveedor EN EL MOMENTO en que se
 * pincha el enlace (mismo cálculo que `calcularDocumentacionFaltante()`,
 * reutilizado tal cual y filtrado al grupo de este proveedor), así que
 * si el proveedor abre el correo varios días después de recibirlo, el
 * PDF que descarga refleja lo que falta de verdad en ese momento, no
 * una foto congelada de cuando se envió el correo — más útil que un
 * enlace que caduca o que muestra datos desactualizados. El dato
 * expuesto (qué documentación falta de un proveedor) es de sensibilidad
 * comparable a la del propio catálogo exportable por `/export/pdf` /
 * `/export/excel`, ya público sin sesión desde antes — no hace falta
 * más protección que un `idProveedor` que haya que conocer.
 */
export async function generarPdfDocumentacionFaltantePorProveedor(req, res) {
  try {
    const idProveedor = Number(req.params.idProveedor);
    if (!Number.isInteger(idProveedor)) {
      return res.status(400).json({ error: "id de proveedor inválido." });
    }

    const { data: proveedor, error: proveedorError } = await supabase
      .from("proveedores")
      .select("id, nombre_proveedor")
      .eq("id", idProveedor)
      .maybeSingle();
    if (proveedorError) return res.status(500).json({ error: proveedorError.message });
    if (!proveedor) return res.status(404).json({ error: "Proveedor no encontrado." });

    const { grupos } = await calcularDocumentacionFaltante();
    const grupo = grupos.find((g) => g.id_proveedor === idProveedor);
    const articulos = grupo?.articulos || [];

    const buffer = await generarPdfDocumentacionFaltante(articulos, proveedor.nombre_proveedor);

    res.setHeader("Content-Type", "application/pdf");
    res.setHeader(
      "Content-Disposition",
      `attachment; filename=documentacion-pendiente-${proveedor.nombre_proveedor.replace(/[^a-z0-9]+/gi, "-")}.pdf`
    );
    res.end(buffer);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}
