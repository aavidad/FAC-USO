# Construcción técnica de FAC-USO Andalucía

Fecha de referencia: 18 de octubre de 2026. El proyecto entrega una web WordPress importable y ocho bot provinciales. Los ensayos locales se registran en `docs/PRUEBAS.md` y `docs/PRUEBAS_IMPORTACION.md`.

## Paquete y arquitectura

`scripts/build.py` reúne los datos editoriales de `data/*.json`, ordena las páginas, asigna categorías y genera `package/facuso-arranque/content.json` y `images.json`. Los archivos distribuibles están en `dist/`:

| Archivo | Función |
| --- | --- |
| `facuso-arranque.zip` | Complemento de importación. Incluye contenidos, imágenes y el tema. Desde Herramientas > FAC-USO · Importación inicial crea la estructura y puede activar el diseño. Es la vía completa. |
| `facuso-andalucia-tema.zip` | Tema instalable por separado. |
| `facuso-andalucia.xml` | Exportación WordPress WXR 1.2 para el importador oficial. Crea contenido y menús, pero no instala tema, medios ni filtros del complemento. |

El manifiesto probado contiene 74 páginas, 132 entradas, 39 categorías y dos menús. De las páginas, 72 se publican y dos quedan en borrador: bienvenida y aviso legal. Las noticias reúnen 62 contenidos editoriales y 70 del snapshot local de los bot. El complemento usa las APIs de WordPress para entradas, categorías, menús, medios, metadatos y portada. Importa 34 imágenes en la biblioteca: 25 fotografías originales atribuidas, ocho recursos generados con IA y un montaje de campaña expresamente etiquetado. Cada noticia tiene imagen y crédito. El logotipo original se conserva como archivo del tema, junto con bandera y ocho escudos.

La importación exige capacidades de administrador y nonce. Usa un bloqueo temporal contra ejecuciones simultáneas, respeta entradas preexistentes con igual ruta o slug e informa de conflictos. Una segunda ejecución no añade contenidos ni medios duplicados. Las referencias internas `[[page:...]]` se resuelven contra los IDs reales, también bajo un subdirectorio; las referencias a archivos locales se resuelven al tema instalado. Los filtros por sector, materia y territorio se implementan con categorías nativas y shortcodes del complemento. Las consultas combinan dimensiones mediante AND, con paginación.

El XML WXR conserva el texto, categorías, menús y rutas internas para un WordPress instalado en la raíz con enlaces permanentes legibles. No configura la portada. Las rutas internas del XML empiezan por `/`, por lo que el subdirectorio y los enlaces simples requieren revisión o adaptación; el ZIP cubre esos casos. El XML asigna segundos técnicos distintos cuando dos entradas comparten título y fecha para evitar colisiones del importador; la fecha original queda en los metadatos. Si se usa el XML y se quiere mostrar las imágenes de recurso, hay que instalar el ZIP del tema. La importación XML oficial y la importación ZIP se probaron por separado.

## Tema y textos

`package/facuso-arranque/theme/` contiene PHP, CSS y JavaScript propios, sin constructor visual. El verde, rojo y blanco de FAC-USO se emplean en un diseño nuevo. La cabecera muestra bandera andaluza, logotipo original y el escudo o nombre del contexto. Justicia dispone de distintivo; los otros cuatro logotipos sectoriales quedan configurables y se muestran por texto mientras no se aporten. Las etiquetas de interfaz se generan desde `data/interfaz-es.json` a los catálogos JSON de complemento y tema. El contenido editorial vive en los JSON de `data/`.

## Bot y fuentes externas

`bot/` contiene ocho configuraciones provinciales que consultan BOE, fuentes sindicales y siete BOP con adaptadores distintos. Almería usa un lector Chrome que produce JSON validado; Huelva usa la API JSON oficial; Cádiz, Córdoba, Granada, Jaén y Sevilla usan lectores HTML. El BOP de Málaga presentó una verificación de acceso y carece de extractor activo: su bot utiliza BOE y noticias sindicales. El BOE complementa a los BOP y no garantiza cobertura de todos los anuncios provinciales. Los procesos de bot se programan cada hora mediante cron. `docs/BOT_NOTICIAS.md` detalla las fuentes y la operación.

El aprovisionador `bot/provision_wordpress.php` crea ocho usuarios con rol provincial y contraseñas de aplicación separadas mediante WP-CLI. Guarda los secretos fuera de WordPress y del repositorio; se ha ensayado la primera ejecución y la repetición sin conflictos. Por defecto el bot crea borradores; la prueba local permitió publicar para recorrer el sitio. Un control REST exige la provincia exacta y una URL de fuente HTTPS autorizada. Las cuentas de bot no pueden editar noticias ajenas, subir medios ni gestionar usuarios. XML-RPC está bloqueado para ellas. Los clientes de fuentes limitan tiempo, tamaño y destinos de las peticiones. La revisión focal independiente figura en `docs/REVISION_INDEPENDIENTE.md`; no sustituye una auditoría del alojamiento definitivo.

## Ensayo y despliegue

`docker/compose.yaml` levanta WordPress 7.1.3 con PHP 8.3, MariaDB 11.4 y Nginx. Solo el proxy escucha en `127.0.0.1:18086`; la red de WordPress y la base es interna, y WordPress tiene bloqueada la salida HTTP externa en la prueba. `docker/compose.validation.yaml` crea instalaciones de importación con prefijos de tablas separados y proxy en `127.0.0.1:18087`. Los secretos se leen de archivos locales privados en `docker/.secrets/`. La instalación de revisión remota usa `docker/production/compose.yaml` en `/opt/facuso` y el dominio https://facuso.cidonia.cloud/. Su red de datos es independiente y solo su gateway comparte la red del Caddy existente. El certificado Let’s Encrypt se renueva automáticamente.

El alojamiento de revisión, HTTPS, cron y copias están configurados en cidonia.cloud. Quedan cuentas editoriales humanas, validación de la recuperación completa del servidor, textos legales, aprobación editorial y cierre de la auditoría de seguridad completa. El bot requiere credenciales nuevas del destino; los secretos del ensayo local no se distribuyen. Antes de publicar se revisan permisos, red, privacidad, restauración y accesibilidad en el servidor real.

## Decisiones de base y contradicciones

El usuario eligió WordPress, Docker para pruebas, un tema nuevo con colores FAC-USO y ocho bot provinciales. Su decisión posterior sustituyó la idea inicial de copiar el aspecto de la web actual. El tema final es propio y no incluye aquel constructor.

## Cómo mantener este documento

Actualizar cuando cambien artefactos, fuentes, permisos, versiones, configuración o despliegue. Contrastar con `scripts/build.py`, `bot/`, el complemento, el tema y los informes de pruebas. El alcance está en `PRD.md`, los datos en `ESQUEMA_BACKEND.md` y las tareas editoriales en `PLAN_IMPLEMENTACION.md`.

ABSORBIDOS: `scripts/build.py`, `docker/compose*.yaml`, `bot/` y `package/facuso-arranque/` — parcial; se resume su funcionamiento, pero el código y la configuración siguen siendo la implementación. `20261015 MODIFICACION ESTRUCTURA WEB.odt` — parcial; las decisiones de estructura se reparten entre los seis documentos de producto.
