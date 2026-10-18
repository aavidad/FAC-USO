# Revisión independiente del importador, tema y bot

Fecha: 18 de octubre de 2026. Revisión focal de código y datos, realizada por un agente distinto del integrador. Skills aplicadas: `security-audit` en modo focal y `humanizer` para este texto. Se leyeron `PRD.md` y `PLAN_IMPLEMENTACION.md`.

El alcance inicial comprende `package/facuso-arranque/facuso-arranque.php`, los PHP del tema, `assets/navigation.js` y `scripts/build.py`. La ampliación posterior incluye `bot/bot.py`, sus adaptadores, Dockerfile, archivos Compose, el rol de publicación y la protección REST provincial. No cubre la configuración del alojamiento definitivo ni una auditoría completa de WordPress. No se ejecutó código del proyecto ni se probaron servicios externos ni se enviaron código o datos a terceros. Se consultó por lectura el código de WordPress del contenedor local. Las comprobaciones dinámicas corresponden al integrador y deben conservarse aparte.

## Resultado de seguridad

En la revisión inicial del importador y el tema no se identificó una vulnerabilidad de seguridad demostrada. La ampliación a las cuentas provinciales detectó una vía alternativa de publicación mediante XML-RPC que el control REST no cubría, detallada más adelante. Las conclusiones se limitan al código leído; no sustituyen las pruebas de autorización HTTP ni permiten declarar segura toda la instalación.

Los controles comprobados fueron:

- La acción administrativa requiere `manage_options`, `publish_pages`, `publish_posts` y un nonce válido. Instalar o activar el tema añade `install_themes` y `switch_themes`. La función de importación también comprueba capacidades.
- `facuso_source_url` y `facuso_external_id` se registran como metadatos REST de entradas. Su escritura exige `edit_post` sobre la entrada concreta. El primero limita el esquema a HTTPS y el segundo usa `sanitize_text_field`. Ambos son visibles mediante REST y deben contener únicamente referencias públicas, nunca credenciales.
- No se añade un endpoint anónimo para el bot. La autorización de peticiones REST corresponde también a WordPress.
- El HTML importado pasa por `wp_kses_post`. Los títulos, atributos, URL y fuentes que construyen el tema y los filtros se escapan según su contexto.
- La copia del tema utiliza rutas determinadas por el paquete; el formulario no aporta rutas de archivos ni URL de descarga.
- Los filtros aceptan términos descendientes de cada dimensión y combinan las dimensiones mediante `tax_query` con relación `AND`. El código revisado no compone SQL con los parámetros HTTP.

## Correcciones comprobadas en el código

| Problema comunicado | Estado de la corrección |
| --- | --- |
| Las entradas existentes impedían reanudar categorías y enlaces después de un fallo parcial. | Se añadieron estados `_facuso_import_stage` y un recorrido común para completar categorías y enlaces de entradas pendientes. Una tercera lectura confirmó también el traslado de fuentes y notas al recorrido común, antes de marcar la entrada como completa. |
| Un menú creado a medias se omitía en el siguiente intento. | Los menús propios tienen `_facuso_managed`; se identifican sus elementos por página y se añaden los que faltan. Los menús ajenos se conservan. |
| Una copia incompleta del tema podía activarse o bloquear los siguientes intentos. | Se copia a un directorio temporal con UUID, se comprueban archivos mínimos, se mueve al destino y se limpia el temporal. También se comprueban archivos mínimos antes de activar una instalación existente. La atomicidad del movimiento debe verificarse con el método de filesystem usado; la ruta de prueba prevista es el filesystem directo de Docker. |
| Importar sin diseño cambiaba portada y nombre del sitio; repetirlo revertía la portada elegida después. | La configuración requiere `$design` y dispone de marcas independientes para aplicarse una sola vez. Se guardan los valores anteriores. |
| Una página fuera de rango producía cientos de enlaces de paginación. | El número usado para construir el rango se limita al total real de páginas. Falta verificar la presentación de una petición fuera de rango. |
| Las páginas recién creadas podían quedar programadas por una hora fija posterior a la hora de importación. | Se usa `current_time('mysql')` cuando el contenido no tiene fecha propia. |

## Pendientes concretos

1. **Límites del XML.** `scripts/build.py` genera enlaces internos que empiezan por `/`. Requieren WordPress en la raíz del dominio y enlaces permanentes compatibles; no cubren instalaciones en subdirectorio ni el modo de enlaces simples. La documentación debe explicar esta limitación y presentar el ZIP como vía completa. Cambiar a IDs fijos en el XML no resuelve por sí solo el remapeo de IDs del importador estándar.
2. **Interrupciones dentro de operaciones WordPress.** Las marcas de propiedad y estado se guardan después de crear las entidades. El código facilita reintentos después de errores controlados, pero no acredita recuperación transaccional ante una interrupción en cualquier instrucción de `wp_insert_post` o `wp_create_nav_menu`. No prometer esa garantía.

## Datos comprobados y pruebas por cerrar

El JSON generado leído durante la primera pasada tenía 59 páginas, 44 entradas y 35 categorías. No tenía slugs duplicados entre páginas y entradas, referencias internas sin destino, referencias a páginas en borrador ni enlaces relativos a la raíz pendientes de convertir en el contenido del ZIP. Cada una de las ocho provincias tenía al menos una noticia. Estos resultados corresponden al JSON leído; una reconstrucción posterior necesita repetirlos.

Pruebas dinámicas que debe cerrar el integrador en Docker aislado:

- Importación inicial y repetida, con recuentos y comprobación de ausencia de duplicados.
- Reintento después de fallos inducidos en fuentes, categorías, enlaces, menú y copia del tema; conservación de contenido y menús editados.
- Importación sin diseño y repetición después de que el administrador cambie la portada.
- Peticiones sin sesión, con rol insuficiente o con nonce ausente o incorrecto; escritura REST propia y ajena de ambos metadatos con usuarios de prueba.
- Filtros individuales y combinados, términos de otra dimensión, parámetros de tipo inesperado y paginación fuera de rango.
- Enlaces del ZIP con rutas simples y WordPress en subdirectorio; importación del XML bajo sus requisitos documentados.
- Recorrido completo de páginas y entradas, fuentes, navegación con teclado y móvil, sin errores PHP ni enlaces internos rotos.

El integrador comunicó una primera importación local de 103 contenidos y una respuesta 200 en portada. Esta revisión no ejecutó ni verificó independientemente esa prueba.

## Identificación del código leído

SHA-256 de la segunda lectura, antes de las correcciones posteriores que pueda realizar el integrador:

```text
cc5dd46d25a44a02ba6bf7840d9cec785fe55fe49c51f6a0604fc0fc781c2fc2  package/facuso-arranque/facuso-arranque.php
cd821b680cb3b05325f6e40456af7409cd67ba0bc47a6f7de432a3a424161c06  package/facuso-arranque/theme/functions.php
f2e83453be899fc16dd19744dbefada1c6770de2254e3b51ca8cbe7d1cd32f41  package/facuso-arranque/theme/index.php
9bc35348d9f7600f6de829e46e582e08332524549e0192858c0238a3a978dbb7  package/facuso-arranque/theme/header.php
4100e9c5e1d8ba50379b268bc54282e0d106f6414eafc638b9fc5c5391dc8788  package/facuso-arranque/theme/footer.php
94c0708aae5bf8c7143db2d4cfbd49b7282f111a3b3a1532ce6979f7c1054a57  package/facuso-arranque/theme/assets/navigation.js
9cbecb7d3b83ef023fc34f8f51dee113c4248f404054588e6e1695d604117868  scripts/build.py
```

La tercera lectura confirmó la corrección de recuperación de fuentes en `facuso-arranque.php`, con SHA-256 `7afdd9f401b6c2bd2a5262800fc341738dee4b38115b870367cf6c40228b7456`.

## Ampliación: bot y cuentas provinciales

Se revisaron las peticiones salientes, contraseñas de aplicación, tratamiento de HTML y XML externos, deduplicación, restricciones del rol, categorías y metadatos REST. El análisis separa los fallos de seguridad de los límites funcionales de las fuentes.

### Publicación por XML-RPC fuera del control provincial

La primera versión del control provincial se instaló únicamente en `rest_pre_insert_post`. Una contraseña de aplicación también puede autenticar peticiones XML-RPC. La cuenta dispone de `edit_posts` y `publish_posts`; `wp.newPost` puede crear una entrada y asignarle categorías sin ejecutar el filtro REST. Por tanto, el titular de una credencial de bot podía saltarse el límite territorial y el control de URL de fuente mediante esa otra interfaz. La consecuencia es publicación fuera de la provincia autorizada; no implica acceso de administrador.

La ruta se comprobó leyendo el WordPress del contenedor: `wp-includes/user.php:387` admite `XMLRPC_REQUEST` para las contraseñas de aplicación; `class-wp-xmlrpc-server.php:309` llama a `wp_authenticate`; `wp_newPost`, `_insert_post` y la llamada a `wp_insert_post` de la línea 1741 no pasan por `rest_pre_insert_post`. El proxy local encaminaba todas las rutas al servidor WordPress.

El integrador añadió un filtro `authenticate` con prioridad 1000 que rechaza fuera de REST a cualquier cuenta con el rol o el metadato de bot. Se volvió a leer y se confirmó el cierre de la ruta descrita: XML-RPC llama a `wp_authenticate` y recibe el error; la validación de contraseñas de aplicación en REST sigue su recorrido propio. Conviene comprobarlo con una cuenta de prueba y una petición XML-RPC que intente crear un borrador fuera de su provincia, y verificar que no aparece ninguna entrada. También debe probarse el rechazo de inicio de sesión web de una cuenta de bot. La corrección está comprobada por fuente; la prueba negativa local no fue ejecutada por este revisor.

### Controles comprobados en el bot

- Las peticiones autenticadas a WordPress usan un cliente que no sigue redirecciones. Así, una respuesta 301, 302, 307 o 308 no reenvía la cabecera `Authorization` a otro destino. El código de error registra estado y endpoint; no imprime la contraseña ni la cabecera.
- Las descargas de noticias usan otro cliente, sin credenciales WordPress. Validan HTTPS, host exacto y puerto permitido, también después de cada redirección. No aceptan usuario o contraseña dentro de la URL. Las noticias RSS se limitan a una lista fija de dominios; los adaptadores de BOP construyen o comprueban destinos oficiales concretos.
- HTTP está limitado a la excepción local de WordPress y loopback; los nombres del contenedor requieren `WP_ALLOW_LOCAL_HTTP=true`. Esta excepción permite pruebas en la red local Docker y no autoriza enviar credenciales por HTTP a un dominio público.
- El límite de descarga es de 2.000.000 bytes y se lee como máximo un byte adicional para detectar excesos. Hay timeout de socket de 12 segundos. Tras la observación de que un flujo lento podía prolongar una petición, el código añadió un límite de 300 segundos para el ciclo completo mediante `SIGALRM`, comprobado por lectura.
- El primer rechazo de DTD buscaba una cadena ASCII y podía omitirse mediante XML UTF-16. Se añadió rechazo de bytes NUL antes del parser, cubriendo esa codificación y UTF-32. Se conserva el rechazo de `DOCTYPE`. No se identificó ni reprodujo una lectura de archivos o una petición externa por entidades XML.
- Se escapaban el texto del resumen, la fecha y el enlace antes de formar el HTML. Se comunicó que la decodificación de entidades en títulos podía reintroducir etiquetas; el payload ahora escapa también el título. Esta corrección evita introducir imágenes o enlaces desde un título codificado; no se presentó como una ejecución de JavaScript demostrada.
- Cada servicio Compose monta una contraseña provincial diferente en modo de solo lectura. Se ejecuta sin root, con filesystem de solo lectura, `no-new-privileges`, sin capacidades Linux y con límites de memoria, CPU y procesos. El código no necesita escribir su estado ni monta el socket Docker. Las redes de la variante local permiten consultar fuentes y alcanzar WordPress.
- El rol creado solo tiene `read`, `edit_posts`, `edit_published_posts` y `publish_posts`. No concede administración, edición de otras personas, borrado, subida de archivos ni gestión de categorías. El control REST exige la provincia asignada por metadato del usuario, prohíbe otras categorías territoriales y valida la URL de origen. La URL se guarda como enlace: su validación en el servidor no desencadena una descarga, por lo que permitir otro puerto HTTPS allí no constituye por sí mismo SSRF.

### Límites y comprobaciones restantes

La deduplicación inicialmente usaba la URL como identidad. En Cádiz, varios anuncios pueden compartir el mismo PDF y número de página; así podían perderse anuncios distintos. El autor cambió la identidad de Cádiz a URL y título, y añadió una prueba de dos anuncios en la misma página. La nueva condición se comprobó por lectura; los resultados de la prueba corresponden al autor. Es una corrección de cobertura, no una fuga de datos.

Durante la revisión inicial, Almería, Huelva y Málaga tenían desactivado el extractor BOP directo. Una actualización incorporó `adapters_huelva.py`: valida el JSON del servicio oficial, la fecha exacta, identificadores y rutas PDF relativas sin componentes vacíos, punto, doble punto, escapes o caracteres ajenos al patrón permitido. No descarga los PDF. Los adaptadores de Cádiz y Córdoba comprueban host, ruta de documento y fecha.

Almería dispone ahora de un lector de JSON generado por un navegador independiente. El lector abre un archivo regular sin seguir el enlace simbólico final, limita su tamaño, exige captura reciente, descarta fechas de anuncio fuera de la última semana y admite exclusivamente la ruta oficial de PDF en `app.dipalme.org`. El volumen compartido se monta como solo lectura en el bot. La ampliación final de esta revisión incluye el productor, descrito a continuación. Málaga conserva cobertura BOE y RSS, sin extractor BOP activo.

El integrador y el autor del bot deben conservar resultados de pruebas offline de redirecciones con credenciales ficticias, XML codificado, límites de tamaño y tiempo, título con entidades, deduplicación y provincia. La comprobación REST local debe incluir otra provincia, doble provincia, fuente ajena, edición de entrada de otra cuenta, borrado y subida de archivos. Esta revisión no ejecutó esas pruebas ni inspeccionó valores de secretos.

## Ampliación final: aprovisionamiento, navegador y medios

### Aprovisionamiento portable

Se leyó `bot/provision_wordpress.php` y su procedimiento en `docs/BOT_NOTICIAS.md`. El guion exige WP-CLI y una cuenta con `manage_options`, `create_users` y `promote_users`. Comprueba el conjunto exacto de permisos del rol, los roles y permisos directos de las cuentas existentes, su provincia y la correspondencia entre archivo y hash de contraseña de aplicación. Revisa las ocho provincias antes de crear cuentas o archivos; no invoca durante esa fase el método de WordPress que puede reparar metadatos de credenciales.

La ruta debe ser absoluta, sin enlaces simbólicos ni componentes especiales. El directorio usa `0700` y cada secreto `0400`; la creación del archivo es exclusiva y el guion revoca la credencial recién creada si no puede guardar el secreto. La salida contiene rutas y recuentos, sin valores de contraseñas. La idempotencia se refiere a ejecuciones secuenciales con estado consistente: no se acredita una transacción entre base de datos y filesystem ni recuperación automática de cualquier interrupción abrupta.

Se corrigieron dos cuestiones durante esta revisión:

- `WP_Application_Passwords::check_password` existe desde WordPress 6.8. Se añadió comprobación del método y uso de `wp_check_password` en versiones anteriores, coherente con el mínimo 6.6 del plugin. La existencia del método y su versión se comprobaron en el código local del núcleo.
- WP-CLI puede desconocer el directorio público cuando WordPress está instalado en un subdirectorio. Se añadió `FACUSO_DOCUMENT_ROOT` obligatorio si no se dispone de `DOCUMENT_ROOT`, y se comprueba que los secretos quedan fuera de esa ruta, de `ABSPATH` y de `wp-content`. El operador debe proporcionar la raíz pública real, incluidas las decisiones de publicación de su servidor.

La supresión general de hooks de creación de usuarios y credenciales se sustituyó por un filtro de correo WordPress. Así se conservan los hooks de auditoría y seguridad de otros plugins. No se certifica el comportamiento de integraciones externas instaladas en otro WordPress. El autor comunicó pruebas aisladas de ocho creaciones, ocho preservaciones en la repetición y rechazo de conflictos; este revisor confirmó el código, pero no ejecutó esas pruebas.

### Productor de Almería

Se leyeron `collector.py`, Dockerfile y Compose. El navegador usa UID 10001, filesystem de solo lectura, un volumen de salida propio, límites de CPU, memoria y procesos, capacidades eliminadas y `no-new-privileges`. No recibe contraseñas de WordPress ni monta sockets Docker; tampoco publica puertos. El bot consumidor monta el volumen compartido en solo lectura. El código extrae filas con fecha, boletín y edicto coherentes y construye URL oficiales; guarda un JSON limitado mediante sustitución atómica.

Los service workers, WebSocket y descargas están bloqueados. El filtro de solicitudes comprueba HTTPS, host, puerto y prefijo `/bop/`. La documentación declara que el host impide el aislamiento interno de Chromium y que la barrera efectiva es el contenedor, con AppArmor y seccomp. El código de Compose no desactiva esas protecciones. No se atribuye a esta configuración protección frente a cualquier vulnerabilidad de Chromium.

Se pidió revisar las redirecciones porque el primer `guard` usaba `route.continue_()`. La [documentación de Playwright sobre rutas de página](https://playwright.dev/python/docs/api/class-page#page-route) advierte de que una redirección no vuelve a llamar al handler para cada URL. El integrador cambió el control a `route.fetch(max_redirects=0)` y rechazo de respuestas 3xx antes de entregarlas al navegador; se comprobó el cambio por lectura. También se leyó `integration_redirect.py`, que usa dos servidores loopback y exige una petición al origen y cero al destino de una redirección. Esta revisión no ejecutó el fixture. No se reprodujo una petición no autorizada ni un acceso a un recurso privado y no se atribuye una vulnerabilidad SSRF confirmada. La consulta de documentación oficial no transmitió código ni datos del proyecto.

### Imágenes y adopción de noticias existentes

`facuso_import_media()` se ejecuta desde la importación administrativa. Usa un catálogo local del paquete, comprueba `realpath` bajo `theme/assets`, extensión WebP y límite de 6 MB, y emplea las funciones de medios de WordPress. No recibe una ruta ni una URL del visitante. Las funciones públicas de imagen y galería solo seleccionan entradas del catálogo; escapan URL, texto alternativo y créditos. No se encontró en ese recorrido una vía de subida para el rol de bot.

Se leyó `prepare_editorial_photos.py`: restringe las URL a HTTPS en `www.usoandalucia.es`, comprueba el vínculo entre noticia e imagen destacada, rechaza redirecciones y limita cada imagen descargada a 6 MiB. Los nombres de salida se construyen con caracteres restringidos y hash; ImageMagick se invoca con argumentos separados, límites de memoria, disco y tiempo. No se ejecutó el conversor durante esta revisión ni se auditó su implementación nativa.

La adopción de una noticia ya existente exige coincidencia del identificador externo y URL de fuente del catálogo. Añade metadatos de reconocimiento y fuentes sin sustituir texto o estado. Tanto la captura inicial como los metadatos importados contienen noticias públicas; la lectura del exportador no mostró exportación de cuentas o contraseñas.

## Evidencia local incorporada al cierre

Se leyó `docs/evidencias/qa-security.json`, generado por el integrador: autenticación del bot 200; provincia ajena, fuente maliciosa, URL con usuario, creación de usuario, subida de medio y edición o borrado de entrada ajena 403. Los métodos XML-RPC `wp.getUsersBlogs` y `wp.newPost` devolvieron fallo 403, con cero entradas de prueba al terminar. Esta evidencia respalda el cierre de la vía XML-RPC detectada. El revisor no repitió las peticiones.

Se leyó también `semgrep-php.json`: cero hallazgos y cero errores en cinco archivos analizados. Es una comprobación adicional limitada a sus reglas y archivos, no una auditoría completa. Los recuentos finales, pruebas de importación y recorrido están en `docs/PRUEBAS.md`; sustituyen los recuentos históricos de las primeras pasadas descritas arriba.

SHA-256 de la lectura de esta ampliación:

```text
2fe0943f6942d6c568767ddaf5e2baa57fc72299fa7df647e666e0fdc5f78cd4  bot/provision_wordpress.php
472ed77af9c6efb8625f03fa374a96502a0373e7fd0c278149e795b1902f6524  bot/almeria_browser/collector.py
830cda75228587616e013b71adbaf7ec27b248b2f6a1ed69a04fa963dc87597b  bot/almeria_browser/Dockerfile
627dabdda44cc7ba943b511b75f0fb1503b6c67828c36ee6fec5aeb5c301159f  bot/compose.almeria-browser.yaml
a11a41d85f1dcf7436e2a8d988e2f5f423abbea895c44fafeefe1dcb714d0ceb  package/facuso-arranque/facuso-arranque.php
fb2c2ea9504db94d238ba453b4fd4a2400118e41cb89bd3126a577163db9c3da  scripts/prepare_editorial_photos.py
```

## Revisión del enriquecimiento de anuncios BOE

La ampliación de `bot.py` obtiene el texto del anuncio únicamente mediante el cliente de descarga con HTTPS y dominios `www.boe.es` y `boe.es`. Las redirecciones mantienen esa lista y no se envían credenciales WordPress al BOE. El parser selecciona párrafos de `#textoxslt`, limita la salida a seis párrafos y 2.000 caracteres y el payload escapa cada párrafo antes de formar HTML. No se encontró en ese recorrido una nueva vía de SSRF o inyección HTML.

La actualización de entradas existentes consulta la identidad autenticada, filtra por autor, requiere identificador externo igual al slug, URL de origen, provincia y cuerpo exacto de la plantilla anterior. Envía únicamente contenido y categorías al endpoint de esa entrada. El servidor conserva la comprobación de autor y provincia. Los títulos y estados no se reemplazan. Se corrigió la pérdida potencial de categorías añadidas manualmente: si difieren del conjunto producido por el clasificador anterior, se conservan.

Se detectó una regresión del límite de tiempo: el manejador de alarma lanzaba `BotError`, que el nuevo tratamiento de errores BOE podía absorber, consumiendo la alarma de una sola ejecución. Además, `--enrich-existing` se ejecutaba antes de instalarla. El autor introdujo `CycleDeadline`, independiente de los errores recuperables de fuente, y armó la alarma también para ese modo. Se comprobaron ambas correcciones por lectura y se leyó el fixture que exige propagar `CycleDeadline` desde `fetch` a través de `enrich_boe`; este revisor no lo ejecutó.

Huella de las últimas lecturas: `bot/bot.py` SHA-256 `e501fff54ce2852676ce551f181212a9fb0091b5f084de4c8942179f79885a44`; `bot/almeria_browser/collector.py` SHA-256 `209dcedbff5e2aa1c432aee671880b85be24f34fef0ff04384c613f286fe6b44`.

## Evidencia posterior del integrador

El agente principal ejecutó `integration_redirect.py` en un contenedor de Almería sin red externa, de solo lectura, con usuario 10001 y límites de recursos. Pasó la prueba: una petición al origen y cero al destino de la redirección. El resultado está en `docs/evidencias/qa-browser-redirect.json`. Esta ejecución corresponde al integrador y no modifica la atribución de la revisión independiente por lectura.

El análisis estático PHP final examinó seis archivos con 23 reglas locales y no obtuvo hallazgos. La evidencia completa está en `docs/evidencias/semgrep-php.json`; no supone una auditoría de todo WordPress ni de su alojamiento futuro.

## Corrección de empleo provincial, enlaces y cron horario

Una revisión focal independiente comprobó el código de la selección BOP/BOE y los enlaces externos: parámetros de fuente limitados a valores conocidos, provincia fija, coincidencia de hosts anclada a un catálogo y salida escapada. No encontró vulnerabilidades confirmadas en ese alcance. Las pruebas locales de filtros y enlaces y el recorrido Chrome se registran en `PRUEBAS.md`.

Para el cron se aplicó `security-audit` en modo focal y solo lectura. Se revisaron secretos separados, ejecución sin root en contenedores, ausencia de socket Docker, límites de recursos, exclusión mutua y conservación de entradas ajenas. Se corrigieron dos defectos operativos detectados: la eliminación de un contenedor tras un timeout tenía que tener también un tiempo máximo, y el instalador debía reconocer el marcador exacto de su cron al final de línea. ShellCheck, sintaxis y validación Compose pasaron. Un ensayo con comandos simulados en bwrap, sin red y con entorno vacío, verificó las nueve ejecuciones únicas, la instalación idempotente y la conservación de un cron con un marcador parecido. No se hizo una auditoría completa del servidor.

## OPAEF: revisión de contenido y navegación

Una revisión independiente leyó `data/opaef.json` y las capturas de escritorio y móvil. Confirmó las dos subpestañas accesibles y un contenido sin acuerdos atribuidos al I Plan ni promesas de confidencialidad absoluta. Se retiró de la página del observatorio la fuente institucional del organismo porque no acreditaba su actividad: ese dato procede de la organización. La ficha permanece en la presentación general de OPAEF. Se corrigió también una concordancia. La página no recoge testimonios ni datos de casos.

## Publicación del repositorio

La revisión focal previa a GitHub comprobó exclusiones de configuración, sesiones, secretos, el ODT original y los paquetes ZIP anidados. El índice se analizó con Gitleaks en local y se contrastó con los valores de los secretos privados, sin incorporarlos al informe. La comprobación recorrió 179 archivos del índice y 597 archivos contando los ZIP anidados: cero coincidencias de secretos o rutas privadas. Una revisión independiente de fuente aprobó la exclusión del ODT y el contenido de los paquetes. Las fotos finales y los contactos profesionales previstos para la web permanecen como material público con su procedencia.

Las herramientas del vídeo transmiten al sintetizador únicamente la locución pública. El primer recorrido se capturó sin sesión, con filtrado GET/origen; la versión final de la herramienta bloquea además service workers, WebSocket y respuestas de redirección. Esta revisión de publicación no equivale a una auditoría de seguridad completa del futuro servidor de producción.
