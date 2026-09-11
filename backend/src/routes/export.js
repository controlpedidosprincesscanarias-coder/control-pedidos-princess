import { Router } from "express";
import { optionalAuth } from "../middleware/auth.js";
import { exportarExcel, exportarPdf } from "../controllers/exportController.js";
import { generarPdfDocumentacionFaltantePorProveedor } from "../controllers/documentacionController.js";

const router = Router();

router.get("/excel", optionalAuth, exportarExcel);
router.get("/pdf", optionalAuth, exportarPdf);

// (2026-09-11) Enlace de descarga del PDF de documentación pendiente de
// un proveedor concreto — ver el comentario largo de
// `generarPdfDocumentacionFaltantePorProveedor()` en
// documentacionController.js para el porqué de que sea público y sin
// caducidad: el destinatario es el propio proveedor, sin cuenta en
// DALI, y este enlace va dentro del correo que le envía
// EmailProveedorModal.jsx cuando el listado de referencias pendientes
// es demasiado largo para itemizarlo dentro del propio cuerpo.
router.get("/documentacion-faltante-pdf/:idProveedor", optionalAuth, generarPdfDocumentacionFaltantePorProveedor);

export default router;
