# FAC-USO Andalucía

La web de muestra funciona en [http://127.0.0.1:18086/](http://127.0.0.1:18086/). Solo es accesible desde este equipo. WordPress, la base de datos y los bots se ejecutan en Docker.

Repositorio: [aavidad/FAC-USO](https://github.com/aavidad/FAC-USO). Contiene el código, los datos editoriales, las imágenes finales del tema, los instaladores y los manuales. La configuración privada y el documento original de especificaciones se conservan fuera de Git. Las condiciones de los materiales están en [NOTICE.md](NOTICE.md) y las pautas de seguridad en [SECURITY.md](SECURITY.md).

[Vídeo con voz: recorrido de 7:35](video/README.md) · [Capturas](imagenes/README.md) · [Descargar la entrega](https://github.com/aavidad/FAC-USO/releases/tag/v1.0.0).

## Instalar en un WordPress vacío

1. En WordPress, abre **Plugins → Añadir plugin → Subir plugin**.
2. Sube `dist/facuso-arranque.zip` y actívalo. El servidor debe permitir archivos de al menos 8 MB; el Docker de prueba admite 16 MB.
3. Abre **Herramientas → FAC-USO · Importación inicial**.
4. Deja marcada la instalación del diseño y pulsa **Importar FAC-USO Andalucía**.

El paquete incluye páginas, noticias, categorías, menús, tema e imágenes. Usa direcciones de la instalación de destino y conserva el contenido preexistente. Se puede repetir para completar elementos que falten; no reemplaza textos ya editados. Si un nombre ya está ocupado, el informe lo indica.

La bienvenida del secretario general y el aviso legal permanecen en borrador. Los contactos institucionales y los cuatro logotipos sectoriales aún no aportados requieren revisión de la organización. Los logotipos publicados son los oficiales recuperados de sus fuentes; las fotografías de recurso generadas se identifican como tales. El montaje de campaña aparece etiquetado y separado de las fotos de noticias reales.

## Archivos de entrega

| Archivo | Uso |
| --- | --- |
| `dist/facuso-arranque.zip` | Instalación recomendada: contenido, tema, navegación, filtros y biblioteca de imágenes. |
| `dist/facuso-andalucia.xml` | Alternativa de contenido para Herramientas → Importar → WordPress. |
| `dist/facuso-andalucia-tema.zip` | Tema independiente para Apariencia → Temas → Subir tema. |
| `dist/contenido-fuentes.json` | Contenido y referencias de la selección inicial. |
| `dist/facuso-entrega-completa.zip` | Paquete de entrega con instaladores, bots e instrucciones; se descomprime antes de usarlo. |

El XML no instala el tema, no configura la portada y no transporta los archivos de imagen. Sus enlaces relativos requieren WordPress en la raíz del dominio y enlaces permanentes `/%postname%/`; las imágenes incluidas en el tema requieren instalar también el ZIP del tema. Para una instalación en subdirectorio, usa el ZIP principal. En el XML, algunas publicaciones con igual título y día reciben segundos diferentes para que el importador oficial no las descarte como duplicadas; conservan el día y su fecha de origen en metadatos.

## Noticias automáticas

Hay ocho bots provinciales con conectores específicos y cuentas separadas. Un cron horario ejecuta el lector de Almería y los ocho bots con un bloqueo para evitar solapamientos. Las pruebas locales publican automáticamente; en otra instalación la configuración predeterminada crea borradores. Cada entrada conserva el enlace oficial, la fecha y su provincia. Cada provincia tiene su apartado interno de empleo público, con su BOP seleccionado y BOE como alternativa; los enlaces externos abren otra pestaña. Los bots rechazan fuentes fuera de su lista, evitan duplicados y no dan por abierto un plazo solo porque el anuncio sea reciente.

[BOT_NOTICIAS.md](docs/BOT_NOTICIAS.md) explica la configuración, las credenciales y el arranque. Almería necesita el lector de boletín con navegador; Huelva usa su API oficial. El BOP de Málaga bloquea la lectura automatizada desde este entorno: su bot sigue recogiendo convocatorias del BOE y noticias sindicales. No debe considerarse una cobertura completa de las bolsas de su BOP.

OPAEF dispone de sección sindical y Observatorio de Igualdad, Acoso y Discriminación, accesibles desde Sevilla, Diputaciones e Igualdad.

Las credenciales no están en los paquetes. El aprovisionador de WP-CLI crea cuentas y secretos nuevos para cada instalación y los guarda fuera del directorio web.

## Pruebas y mantenimiento

- [Pruebas de navegación, imágenes y permisos](docs/PRUEBAS.md).
- [Ensayos de instalación limpia de ZIP y XML](docs/PRUEBAS_IMPORTACION.md).
- [Revisión independiente de seguridad](docs/REVISION_INDEPENDIENTE.md).
- [Documentos de producto](docs/producto/PRD.md).

Para reconstruir los archivos desde los datos editoriales: `python scripts/build.py` (requiere Python y `lxml`; importar en WordPress no requiere Python). `python scripts/package_release.py` crea la entrega completa. El código de preparación y verificación vive en `scripts/`. Los guiones `bootstrap*.php` y `sync_preview.php` están restringidos al entorno local de muestra; no son guiones de despliegue en producción.

Para parar WordPress: `docker compose -f docker/compose.yaml stop`. Para detener las consultas automáticas, retira su cron con `bash bot/install-cron.sh --remove`; sus contenedores son de ejecución única. Los comandos están en el manual. No uses `down -v` si quieres conservar las noticias y los ajustes locales.
