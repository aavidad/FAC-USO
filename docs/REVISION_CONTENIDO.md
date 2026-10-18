# Revisión del contenido inicial

Fecha: 18 de octubre de 2026. Se revisaron los datos editoriales, el manifiesto generado y los resultados del WordPress local. La revisión editorial de FAC-USO Andalucía sigue pendiente antes de publicar el dominio definitivo.

## Estructura y atribución

El manifiesto probado contiene 63 páginas, de las que 61 están publicadas y dos en borrador, 132 noticias y 39 categorías. Las noticias reúnen 62 contenidos seleccionados y 70 entradas del snapshot de los ocho bot. Las 132 tienen fecha y fuente HTTPS; ninguna tiene fecha posterior al 18 de octubre de 2026. La clasificación por provincia da Almería 15, Cádiz 13, Córdoba 9, Granada 12, Huelva 11, Jaén 15, Málaga 9 y Sevilla 28 asignaciones. Algunas noticias abarcan más de un territorio, por lo que la suma de etiquetas provinciales supera el número de entradas. El recorrido local comprobó las ocho páginas de provincia con noticias visibles y sin referencias internas rotas (`docs/PRUEBAS.md`).

Cada página provincial muestra dirección, teléfono y correo de la sede territorial publicados por USO Andalucía, enlace a su directorio, BOP y recurso de empleo público. Granada enlaza además la sección sindical de USO en la Diputación y su contacto público. Estos teléfonos no se presentan como líneas exclusivas de FAC-USO Andalucía. Antes de publicarlos en el dominio real debe confirmarse su vigencia con el directorio y quién atiende asuntos de la federación.

El archivo de empleo distingue oferta, convocatoria y bolsa. Cada noticia conserva fecha, organismo y enlace al anuncio original. El texto recuerda que una publicación histórica no demuestra que un plazo siga abierto. Los bot se limitan a lo que puede extraerse de las fuentes; el BOE complementa siete BOP y el BOP de Málaga carece por ahora de lector automático debido a la verificación de acceso. Sus anuncios requieren seguimiento editorial o una vía oficial automatizable. El bot evita publicar falsos positivos y no traslada noticias a otra provincia en el ensayo local; las cifras y pruebas constan en `docs/PRUEBAS.md`.

## Noticias sindicales e imágenes

Los resúmenes de comunicaciones sindicales atribuyen denuncias, cifras y demandas a la organización que las publica. Las afirmaciones sobre sentencias o decisiones judiciales, como las relativas al SAS en Jerez, Diputación de Córdoba, bomberos de Morón y concurso de traslados de Justicia, deben contrastarse con la resolución primaria antes de usarse como referencia jurídica. La fuente sindical permanece enlazada para conocer la posición y fecha originales.

Las 132 entradas muestran imagen y crédito en la prueba. El paquete contiene 25 fotografías procedentes de publicaciones originales de USO Andalucía, cada una con enlace a su noticia, ocho imágenes de recurso generadas con IA y un montaje de campaña. El montaje está etiquetado como ilustrativo y explica que su escena y multitud no corresponden a un acto documentado. La galería muestra las 25 fotos originales. Antes de usar estas imágenes en el dominio definitivo, la organización debe confirmar el permiso editorial y los créditos. El logotipo regional se conserva como imagen original; los ocho escudos provinciales tienen atribución en `data/assets.json`. Faltan cuatro logotipos sectoriales específicos.

## Páginas institucionales pendientes

La bienvenida y el aviso legal permanecen en borrador. La primera necesita texto firmado; el segundo, los datos y decisiones del responsable del sitio. Los nombres y correos de la Ejecutiva y Garantías proceden del ODT del 15 de octubre de 2026. Hay que ratificarlos, incluida la vocalía pendiente de sustitución. El correo de Comunicación aparece en el ODT con una tilde en la parte local y no se debe inventar una dirección alternativa. La página de congresos distingue actos de estructuras relacionadas de la documentación propia aún no aportada.

Algunas subpáginas sectoriales tienen una introducción breve y un enlace general a estatutos; sus publicaciones filtradas aportan actividad, pero conviene añadir convenios, acuerdos y recursos oficiales de cada especialidad cuando la organización los facilite. La segunda lista de sectores del ODT, que incluye Diputaciones y Ayuntamientos, guio la jerarquía actual. Las páginas de fotos y vídeos remiten también a publicaciones originales; las fotos incorporadas no convierten la galería en un archivo institucional completo.

## Corrección y prueba de enlaces

Durante la preparación se detectaron 61 metadatos de fuentes de `data/territorios.json` con URL y título intercambiados. Se corrigieron antes de generar los archivos finales. Una comprobación local del manifiesto da cero URL de fuente sin HTTPS, y el rastreo del WordPress probado terminó con 289 URL HTML y 47 recursos locales en HTTP 200. Esa prueba comprueba rutas internas y carga local; los enlaces externos, teléfonos, cargos y situación de cada convocatoria deben cotejarse de nuevo antes de la publicación pública.

## Decisiones editoriales pendientes

FAC-USO Andalucía debe aprobar la bienvenida y textos legales, validar cargos y contactos, determinar quién revisa las noticias automáticas, confirmar permisos de fotos y logotipos, y decidir el tratamiento de anuncios caducados. La revisión de seguridad y el ensayo de importación están documentados en `docs/REVISION_INDEPENDIENTE.md`, `docs/PRUEBAS.md` y `docs/PRUEBAS_IMPORTACION.md`. El cierre de estas decisiones se sigue en `docs/producto/PLAN_IMPLEMENTACION.md`.
