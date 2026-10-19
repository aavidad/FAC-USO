# Diseño de FAC-USO Andalucía

Fecha de referencia: 18 de octubre de 2026. La interfaz está en `package/facuso-arranque/theme/`; los textos breves se generan desde `data/interfaz-es.json`. La prueba visual local figura en `docs/PRUEBAS.md`.

## Identidad y cabecera

El tema usa el verde, rojo y blanco de FAC-USO en una composición nueva. Conserva intacto el archivo del logotipo original publicado por la organización, acompañado por la bandera de Andalucía. Una página o noticia territorial muestra el escudo de su provincia; las ocho imágenes están incorporadas y acreditadas. Una sección sectorial muestra su nombre y, cuando existe, su distintivo. Justicia incluye imagen propia. Faltan los cuatro logotipos oficiales de Sanidad, Administración local, Administración autonómica y Administración General del Estado; el personalizador permite añadirlos sin modificar la plantilla.

`style.css` define verde `#00683d`, verde oscuro `#00482b` y rojo `#cf2c1b`, fondo blanco, tipografía del sistema, foco visible y ancho máximo de 1240 píxeles. Las tarjetas pasan de varias columnas a una en móvil. La cabecera ofrece navegación principal, botón de menú en pantalla estrecha y controles para submenús. Hay enlace de salto al contenido y etiquetas para los filtros.

## Portada y páginas

Inicio presenta servicios, contacto, cinco sectores y ocho provincias. Debajo hay seis tarjetas de «Actualidad sindical» y seis de «Bolsas y oposiciones». La primera consulta excluye el empleo para evitar entradas repetidas; la segunda se limita a esa materia. Todas las tarjetas de noticias llevan imagen, fecha y resumen. La imagen de la cabecera es un recurso ilustrativo identificado como IA.

Las páginas interiores presentan ruta de navegación, título, texto, enlaces a secciones hijas y noticias relacionadas. «Información > Empleo público» explica la diferencia entre oferta, convocatoria y bolsa; sus tres subpáginas permiten consultar cada tipo. Cada provincia tiene una subpágina de empleo con filtro de fuente: BOP provincial, BOE o todas. Las tarjetas identifican el boletín junto a la fecha; un BOP sin resultados no se sustituye silenciosamente por BOE. Los enlaces externos abren otra pestaña con `noopener noreferrer`. El listado general y los apartados de sector o provincia combinan filtros por sector, materia y territorio. Se muestra el número de resultados y la paginación conserva los parámetros. Un resultado vacío tiene mensaje específico y una acción para reiniciar la búsqueda.

OPAEF emplea dos enlaces de navegación con estilo de pestañas. El apartado activo se distingue por color y `aria-current="page"`; son enlaces nativos accesibles por teclado y funcionan sin JavaScript. El título completo del observatorio se conserva y el texto se adapta al móvil.

La página de Vídeos incorpora un reproductor nativo adaptable al ancho de pantalla, con imagen de portada, subtítulos en castellano y enlace de descarga. El vídeo corregido mantiene la portada al dar la bienvenida y asigna una pantalla a cada explicación.

La página de Fotos contiene una galería de 25 imágenes tomadas de publicaciones originales de USO Andalucía, enlazadas a la noticia de origen. Incluye también un montaje de campaña etiquetado como ilustración generada a partir de una foto original; el texto aclara que la escena y la multitud no documentan un acto real. Los ocho recursos visuales generados con IA se describen como ilustraciones. Cada entrada tiene imagen y crédito; las 25 fotos originales se muestran cuando hay coincidencia con la fuente y, en otro caso, se elige un recurso temático. El crédito forma parte del contenido visible, no solo del texto alternativo.

## Accesibilidad y pruebas

La prueba local recorrió las 193 URL públicas en Chrome móvil antes del último ajuste visual y no encontró desbordamientos ni errores de JavaScript. Tras ese ajuste se revisaron portada, galería y dos noticias en móvil, y la portada en escritorio. El rastreo final de 285 URL HTML y 48 recursos locales terminó sin fallo. `docs/PRUEBAS.md` conserva alcance, capturas y límites de estos recorridos. La revisión independiente de usabilidad está en `docs/REVISION_INDEPENDIENTE.md`; la aceptación editorial final corresponde a FAC-USO Andalucía.

Mantener foco visible, navegación por teclado, etiquetas accesibles y texto alternativo cuando se sustituyan imágenes. La organización debe confirmar los cuatro distintivos sectoriales faltantes y el permiso editorial de las fotos antes de publicar el sitio definitivo. Las noticias de empleo muestran fecha y fuente oficial; no se insinúa que una convocatoria histórica siga abierta.

## Contradicciones encontradas

El ODT pidió un distintivo sectorial en cada sección, pero solo Justicia tiene un archivo identificado para este paquete. Las otras áreas se identifican por su nombre hasta recibir material autorizado. La decisión posterior del usuario sustituyó el diseño de la web en construcción por un tema propio moderno.

## Cómo mantener este documento

Actualizar al cambiar colores, cabecera, navegación, tarjetas, galería o accesibilidad. Contrastar con `theme/style.css`, sus plantillas y `facuso-arranque.php`. El recorrido de cada persona está en `FLUJO_APP.md` y las aprobaciones pendientes en `PLAN_IMPLEMENTACION.md`.

ABSORBIDOS: `20261015 MODIFICACION ESTRUCTURA WEB.odt` — parcial; cabecera y navegación se reflejan aquí, mientras que el original conserva detalles de cargos. `package/facuso-arranque/theme/` — parcial; se documenta el patrón visible, su código permanece en el tema.

La sección de USO Diputación de Granada presenta sus cursos ajustados a las bases de las OPE de esta administración, con capturas reales y una práctica pública de seis preguntas de TCAE. El acceso completo permanece autorizado en el portal original. El recorrido y la procedencia se documentan en `docs/CURSOS_GRANADA.md`.

El 19/10/2026 se incorpora la identidad de USO Administración Local Sevilla facilitada por el responsable (`imagenes/Imagen pegada.png`), sin modificar el diseño de la imagen. Se muestra en la página provincial y en su contexto de cabecera, incluidos sus apartados hijos.
