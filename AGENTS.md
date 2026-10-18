# FAC-USO Andalucía

Lee `docs/producto/PRD.md` y `docs/producto/PLAN_IMPLEMENTACION.md` antes de trabajar. Para código, consulta también `TRD.md` y `ESQUEMA_BACKEND.md`; para pantallas, `FLUJO_APP.md` y `DISENO_UI_UX.md`.

- El producto es un paquete importable de WordPress, su tema y ocho bots provinciales. La selección y las fuentes están en `data/`; `scripts/build.py` genera `dist/`.
- Los logotipos son oficiales. Toda noticia debe tener una imagen; las escenas generadas y los montajes se identifican. Una foto documental se asocia a su noticia de origen.
- Cada bot tiene cuenta y ámbito provincial propios. Mantén el control de permisos en WordPress además de las validaciones del cliente. No uses cuentas administradoras en bots.
- Los boletines necesitan conectores específicos. El BOP de Málaga está bloqueado desde este entorno; su alternativa activa es el BOE. No presentes esa alternativa como cobertura completa del BOP.
- Los ensayos se ejecutan en Docker. Los guiones `bootstrap*.php` y `sync_preview.php` están restringidos a la muestra local. Los prefijos de validación no son `wp_`.
- Usa nombres DNS de contenedor únicos en las redes compartidas. La vista previa pública local está en `127.0.0.1:18086`; no publiques ese puerto en otras interfaces.
- Nunca incluyas `docker/.secrets/`, contraseñas, sesiones de navegador o copias de la base de datos en una entrega. Mantén el análisis de seguridad en local.
- Después de un cambio, ejecuta las comprobaciones proporcionales y actualiza los documentos afectados. Los ZIP son reproducibles: sus sumas deben corresponder con los archivos ensayados.
