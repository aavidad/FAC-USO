# Formación de USO Diputación de Granada

Revisión: 18/10/2026. Apartado: https://facuso.cidonia.cloud/territorios/granada/diputacion-de-granada/.

La sección presenta el portal https://uso.dipgra.cloud/ y sus cursos para OPE de la Diputación, adaptados a las bases de cada proceso. El resumen contrasta el catálogo público con los controladores del portal consultados por SSH en lectura. Diferencia cursos disponibles, especialidades en preparación y revisión, y acceso completo autorizado por afiliación y especialidad. No da por habilitadas todas las herramientas en todos los cursos.

Las capturas de `imagenes/cursos-granada/` proceden de Chrome, sin sesión, de tres vistas reales: catálogo `/opes`, ficha pública TCAE C1 de promoción interna e índice de 21 temas, y muestra `/tests`. Esta última procede del curso de TCAE de turno libre: incluye un fragmento de Constitución, audio por apartados, infografía y seis preguntas. No se confunde con el curso de promoción interna. Las capturas no contienen alumnos, cuentas, códigos de acceso ni pantallas administrativas.

El test integrado reproduce exclusivamente las seis preguntas, opciones, explicaciones y fragmentos que el servidor ya muestra públicamente. Se conservan en `data/muestra-tcae.json`; no se extrae ni publica el banco privado. El shortcode `[facuso_muestra_tcae]` ofrece selección, corrección, explicaciones y reinicio. Todo ocurre en el navegador, sin formularios enviados, cuentas, cookies ni almacenamiento de respuestas. Los enlaces al portal original abren una pestaña nueva. El audio se copia únicamente del fragmento ya público `/demo/tcae/tema-1/audio/b0004.mp3` al paquete, para reproducirlo desde el propio dominio: las protecciones de origen del portal impiden su reproducción cruzada. No se cambian esas protecciones.

El portal original impide incrustaciones de otras webs mediante CSP y X-Frame-Options. Se mantienen esas protecciones: FAC-USO muestra capturas y la pequeña práctica pública con atribución, en lugar de abrir el área privada en un iframe o cambiar sus cabeceras.

Se aplican las skills `playwright-cli`, `security-audit` en revisión focal y `usar-orquesta-para-opes` en su excepción explícita de observación e integración de una entrega existente. Este trabajo no redacta temarios, preguntas o explicaciones nuevas ni modifica la producción de cursos. La revisión de seguridad comprueba salida escapada en PHP, etiquetas del cliente por `textContent`, destinos fijos, ausencia de escrituras o nuevas API y ausencia de autenticación en las capturas. No sustituye la auditoría completa pendiente.

Verificación reproducible: `node scripts/check_granada.mjs https://facuso.cidonia.cloud`. Comprueba seis aciertos, preguntas sin responder, error, reinicio, explicaciones, imágenes, anchura móvil, enlaces externos y errores JavaScript. Evidencia en `docs/evidencias/qa-cursos-granada.json`.

La actualización remota se acota a la página propia de Granada con `docker/production/publish-granada.php`, por CLI, dominio y entorno de revisión verificados y revisión de WordPress conservada. Se ejecuta una copia privada previa; no se usan los scripts de muestra local en el servidor.

La página incluye además un vídeo corto dedicado al curso, con controles y subtítulos. El mismo recorrido forma parte del capítulo de Granada del vídeo general; ambos conservan la navegación a ritmo de la locución.

El vídeo corto dura 1:45 y el general ampliado 13:46. Ambos están publicados y probados en escritorio y móvil con sus subtítulos. En XML, la muestra se exporta como preguntas y respuestas desplegables sin dependencia del complemento; el ZIP ofrece selección y corrección interactiva.
