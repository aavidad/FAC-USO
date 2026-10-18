# Fotografías y recursos visuales

Las noticias muestran una fotografía o una imagen de recurso, también cuando llegan de los bots. Las fotos de USO Andalucía se asocian a su artículo original. Para anuncios sin fotografía se usa un banco de escenas ilustrativas, con variación estable entre imágenes de empleo público.

| Recurso | Ubicación y procedencia |
| --- | --- |
| Logotipo regional y SPJ-USO | `package/facuso-arranque/theme/assets/`; originales publicados por FAC-USO Andalucía. |
| Escudos provinciales y bandera | Mismo directorio; fuentes y licencias en `data/assets.json`. |
| 25 imágenes de noticias | `assets/fotos-noticias/`, versiones WebP en `package/facuso-arranque/theme/assets/noticias/`; créditos, URL y descripción en `data/news-photos.json`. |
| Ocho fotos de recurso generadas | `assets/fotos-generadas/`, versiones WebP en el directorio de assets del tema. Identificadas como imágenes de recurso generadas con IA. |
| Montaje de campaña | `assets/montajes/campana-spj-uso.png` y `package/facuso-arranque/theme/assets/montaje-campana.webp`. |

Se utilizó la herramienta integrada `image_gen`, sin la alternativa por API o CLI. Los prompts están en `data/imagegen-prompts.json` y `data/imagenes-empleo-prompts.json`. Los originales se conservan; las versiones WebP son las que se incluyen en la entrega de WordPress. Las imágenes se incorporan también a la biblioteca de medios para que una persona editora pueda reutilizarlas.

El montaje parte de una fotografía publicada el 17 de septiembre de 2026 en [USO Andalucía](https://www.usoandalucia.es/44420-2/). La multitud y el escenario son generados; la franja visible «MONTAJE ILUSTRATIVO» y el pie de imagen lo aclaran. Está en la galería de propuestas de campaña y no sustituye la fotografía documental de la noticia. Antes de usarlo como pieza corporativa debe comprobarse la fidelidad de las marcas impresas en el original.

Los logotipos de la cabecera y de los sectores se conservan como recursos oficiales. No se ha adoptado ningún logotipo generado. Faltan los distintivos oficiales específicos de cuatro sectores; el tema permite incorporarlos desde el personalizador.
