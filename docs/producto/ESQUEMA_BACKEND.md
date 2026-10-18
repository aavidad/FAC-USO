# Datos y permisos de FAC-USO Andalucía

Fecha de referencia: 18 de octubre de 2026. El paquete usa tablas y API nativas de WordPress; no introduce migraciones SQL propias.

## Fuentes y entidades

| Archivo | Datos principales | Destino |
| --- | --- | --- |
| `data/institucional.json` | Organización, servicios, información, contactos y pendientes | Páginas jerárquicas |
| `data/opaef.json` | OPAEF, sección sindical, observatorio, pestañas y accesos desde Sevilla, Diputaciones e Igualdad | Tres páginas jerárquicas |
| `data/territorios.json` | Sectores, provincias, enlaces y sedes | Páginas y categorías |
| `data/noticias.json` | Noticias editoriales fechadas | Entradas |
| `data/empleo-provincial.json` | Noticias de empleo seleccionadas y verificadas | Entradas |
| `data/bot-news-snapshot.json` | 70 noticias de los ocho bot en el ensayo local | Entradas iniciales |
| `data/news-photos.json` e `imagenes-*.json` | Fotografías originales, ilustraciones y créditos | Biblioteca de medios y tema |
| `data/interfaz-es.json` | Etiquetas visibles de complemento y tema | Catálogos JSON del paquete |

`scripts/build.py` añade portada, empleo público, noticias, afiliación, aviso legal y créditos; transforma resúmenes de la web actual según `data/web-existente.json`. El manifiesto final probado tiene 74 páginas (72 publicadas y dos borradores), 132 entradas, 39 categorías y dos menús. La taxonomía `category` tiene tres ramas principales: Sectores, Materias y Territorios. «Empleo público» es una materia con hijas para bolsas, oposiciones y ofertas. «Territorios» contiene Andalucía y las ocho provincias. Cada entrada recibe las categorías que permiten filtrar su ámbito.

Cada página conserva slug, título, HTML, padre, estado, fuentes y notas. Las entradas añaden fecha y categorías. El importador registra `_facuso_key`, `_facuso_sources` y `_facuso_review`. Las noticias de bot conservan `facuso_source_url` y `facuso_external_id` para atribución y deduplicación. Las imágenes importadas guardan texto alternativo, crédito, tipo y nombre de archivo. `facuso_image_ids` relaciona cada archivo del paquete con su adjunto de WordPress. El tema y el complemento muestran la imagen correspondiente a la fuente o el recurso temático.

El importador crea términos y entradas con las APIs de WordPress; resuelve las referencias `[[page:slug]]` y `[[asset:archivo]]` después de conocer los ID y las rutas reales. Crea menús nativos con relaciones padre e hijo. Una reimportación conserva el contenido existente y no duplica imágenes. Las pruebas cubrieron una edición manual posterior y la recuperación de una importación interrumpida. En un sitio con entradas previas, la coincidencia de slug se registra como conflicto para revisión humana.

## Cuentas y escritura automática

La importación administrativa exige `manage_options`, `publish_pages`, `publish_posts` y nonce. Instalar o activar el tema añade `install_themes` y `switch_themes`. Los bot usan ocho usuarios con rol `facuso_news_bot`, ámbito provincial y contraseña de aplicación distinta. `bot/provision_wordpress.php` los crea mediante WP-CLI y guarda los secretos fuera del repositorio y del árbol web. Su ejecución repetida conserva las cuentas que coinciden y rechaza conflictos de rol, provincia o archivo de secretos. El ensayo local creó las ocho cuentas y validó la repetición.

El control de escritura REST para cada bot exige la categoría de su provincia y rechaza otra provincia, un host ajeno o una URL de fuente sin HTTPS. No permite gestión de usuarios, medios, noticias ajenas ni acceso alternativo por XML-RPC. `docs/PRUEBAS.md` registra las respuestas HTTP 403 para esos intentos. En producción se proponen borradores para revisión; el ensayo local y el entorno de revisión en cidonia.cloud usan publicación directa por encargo del responsable. Los bot consultan fuentes cada hora mediante cron y deduplican por identificador externo y provincia.

El bot de Málaga no lee el BOP provincial automáticamente porque este mostró una barrera de acceso. Recibe BOE y fuentes sindicales. El lector de Almería usa una captura JSON de Chrome validada; Huelva consume JSON oficial y otros cinco BOP tienen adaptadores HTML. La cobertura detallada figura en `docs/BOT_NOTICIAS.md`.

## Importación alternativa y datos sensibles

El WXR crea páginas, noticias, categorías y menús con el importador oficial. No transfiere imágenes binarias ni configura el tema o la portada. Las rutas del XML son de raíz y enlaces permanentes legibles; en un WordPress bajo `/portal` se debe usar el ZIP o adaptar el XML. Para evitar que el importador agrupe dos noticias con igual título y fecha, `scripts/build.py` asigna segundos técnicos únicos y conserva la fecha original en metadatos.

Los correos y teléfonos del paquete son contactos profesionales públicos. No se importan datos de afiliación. Las credenciales de bot y base de datos se guardan fuera de `dist/`. El aviso legal permanece en borrador hasta que la entidad lo apruebe. Las imágenes originales tienen enlace y crédito; el permiso editorial para publicarlas en el dominio definitivo requiere ratificación.

## Contradicciones encontradas

En una versión anterior, los 61 registros `sources` de `data/territorios.json` tenían intercambiados URL y título; se corrigieron antes de generar y probar el paquete final. El XML proporciona contenido, pero los filtros y las imágenes importadas dependen del complemento. Su límite debe tenerse en cuenta al elegir la vía de importación.

## Cómo mantener este documento

Actualizar cuando cambien campos, categorías, API, permisos, importación o fuentes del bot. Comparar `data/*.json`, `scripts/build.py`, `facuso-arranque.php`, `bot/` y las pruebas. Los recorridos están en `FLUJO_APP.md` y los pendientes en `PLAN_IMPLEMENTACION.md`.

ABSORBIDOS: `data/*.json` — parcial; se resume el modelo, los registros quedan en los JSON. `scripts/build.py`, `package/facuso-arranque/facuso-arranque.php` y `bot/` — parcial; se documenta persistencia y autorización, el código sigue siendo la implementación.

La sección de USO Diputación de Granada presenta sus cursos ajustados a las bases de las OPE de esta administración, con capturas reales y una práctica pública de seis preguntas de TCAE. El acceso completo permanece autorizado en el portal original. El recorrido y la procedencia se documentan en `docs/CURSOS_GRANADA.md`.
