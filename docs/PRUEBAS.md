# Pruebas del paquete FAC-USO Andalucía

El ensayo se hizo el 18 de octubre de 2026 sobre WordPress 7.1.3 en los contenedores locales de `docker/compose.yaml`. El servidor solo escucha en `127.0.0.1:18086`; la red de WordPress y MariaDB es interna y WordPress tiene bloqueada la salida HTTP externa. Se usó Chrome del sistema mediante `playwright-cli`.

## Resultado comprobado

| Comprobación | Resultado |
| --- | --- |
| Estructura WordPress | 74 páginas importadas, 72 publicadas y 2 borradores; 132 noticias, 39 categorías y 34 medios. |
| Instalación limpia | El ZIP final superó 598 comprobaciones en WordPress vacío; repetirlo no duplicó contenido. El XML actualizado superó 557 comprobaciones y el ZIP bajo subdirectorio 543. Véase [PRUEBAS_IMPORTACION.md](PRUEBAS_IMPORTACION.md). |
| Reimportación | 2152 aserciones sin fallo al combinar bots, medios y reimportación: conserva una edición hecha después de importar y recupera una entrada interrumpida. La prueba restauró el contenido original. |
| Recorrido HTTP | 132 noticias públicas, 282 URL HTML y 48 recursos locales, todos con HTTP 200; sin enlaces internos rotos, marcadores sin resolver ni errores PHP visibles. |
| Filtros | Combinaciones AND de sector, materia y provincia, selección conservada y conteos comparados con la taxonomía real. Paginación extrema sin error. |
| Provincias | Ocho páginas con correo, teléfono, escudo y noticias visibles. |
| Chrome móvil | Una pasada completa previa recorrió las 193 URL públicas a 390 × 844 sin desbordamientos ni errores JavaScript. Tras el último cambio visual, se revisaron portada, galería y dos noticias; seis fotos de empleo cargaron, sin desbordamientos ni errores JavaScript. |
| Chrome escritorio | Portada a 1440 × 900: navegación visible, dos bloques de seis tarjetas con foto y sin desbordamiento. |
| Fotografías | Las 132 noticias tienen imagen y crédito; portada sin entradas repetidas y con fotos variadas (seis distintas en actualidad y cuatro en empleo en la última muestra). Cuatro consultas seguidas mostraron el mismo orden. Las doce tarjetas conservan la misma foto en su ficha; los ocho recursos ilustrativos son distintos. Galería con 25 fotos originales enlazadas a su fuente; montaje ilustrativo etiquetado como generado con IA. |
| Búsqueda y archivo | Búsqueda: 5 de 5 tarjetas con foto; archivo de Granada: 10 de 10. Favicon oficial servido como PNG. Dos noticias BOE muestran texto oficial enriquecido y enlace a la fuente; dos anuncios de Universidad de Cádiz tienen las categorías autonómica y universidades. |
| Permisos HTTP | Importación anónima HTTP 400; REST POST anónimo 401; administrador sin nonce 403; suscriptor importación 403 y REST POST 401. Recuentos de páginas y noticias intactos. |
| Ocho bots provinciales | 1345 aserciones: ocho cuentas con rol, provincia y contraseña de aplicación, cada una con al menos una noticia publicada. Son 70 noticias de bot: Almería 11, Cádiz 8, Córdoba 3, Granada 8, Huelva 5, Jaén 12, Málaga 6 y Sevilla 17. Almería aporta 7 anuncios BOP y Huelva 4. Cádiz conserva dos avisos distintos en la misma página PDF. Segunda ejecución de los ocho bots: cero noticias duplicadas. Los falsos positivos 327, 331 y 357 están ausentes; cero títulos con HTML y cero noticias en otro territorio. |
| Seguridad del bot | Para Granada, autenticación REST HTTP 200; provincia ajena, host malicioso, URL con usuario, crear usuario, subir medio, editar y borrar noticia ajena: todos HTTP 403. `wp.getUsersBlogs` y `wp.newPost` por XML-RPC devolvieron fallo 403; cero entradas de prueba antes y después. |

Los detalles están en [qa-crawl.json](evidencias/qa-crawl.json), [qa-security.json](evidencias/qa-security.json), [qa-ui-final.json](evidencias/qa-ui-final.json), [qa-last-ui.json](evidencias/qa-last-ui.json), [qa-ui-browser.log](evidencias/qa-ui-browser.log), [qa-bots.json](evidencias/qa-bots.json) y [qa-bots-rerun.json](evidencias/qa-bots-rerun.json). Las capturas son [portada escritorio](evidencias/qa-inicio-escritorio.png), [portada móvil](evidencias/qa-inicio-movil.png), [empleo móvil](evidencias/qa-empleo-movil.png) y [galería móvil](evidencias/qa-galeria-movil.png).

## Correcciones provinciales y enlaces externos

El paquete crea ocho páginas hijas de empleo público, una por provincia. La fuente inicial es su BOP y se ofrecen BOE o todas las fuentes como selección expresa. Almería muestra nueve anuncios BOP y cuatro BOE en la muestra. Málaga conserva el estado vacío de BOP; no se presenta BOE como sustitución del boletín provincial.

`test_provincial_jobs.php` superó 165 comprobaciones y `test_external_links.php` otras 27. Las pruebas verifican provincia y materia fijas frente a parámetros manipulados, selección de fuente, URLs con host ajeno o engañoso y atributos de enlaces. La verificación general con `--bots` pasó 2189 comprobaciones. El nuevo rastreo de 282 páginas y 48 recursos no encontró errores ni avisos: [qa-crawl-provincial.json](evidencias/qa-crawl-provincial.json).

En Chrome se siguió una noticia desde Almería en la misma pestaña y se abrió su fuente en otra, conservando la original y con `window.opener === null`. La respuesta externa fue simulada. Se verificaron también enlaces añadidos dinámicamente y ausencia de desbordamiento a 390 × 844. [Evidencia](evidencias/qa-provincial-browser.json) y [captura](evidencias/qa-empleo-almeria.png). La revisión focal independiente del código de filtros y enlaces no encontró vulnerabilidades confirmadas.

## OPAEF: sección sindical y observatorio

Se incorporaron tres páginas: OPAEF bajo Sevilla y sus dos subpestañas «USO-OPAEF · Sección sindical» y «Observatorio de Igualdad, Acoso y Discriminación USO-OPAEF». El contenido explica el apoyo solicitado y la preparación de reuniones para negociar el I Plan de Igualdad. Las medidas se describen como propuestas para debatir, sin atribuir acuerdos ni publicar casos personales. La ficha institucional del organismo se cita en la página general; la actividad del observatorio procede de la indicación de la organización.

La revisión independiente verificó la navegación y el contenido. Chrome confirmó dos enlaces de pestañas, estado activo por `aria-current`, contexto de Sevilla, navegación interna en la misma pestaña y ausencia de desbordamiento en las tres páginas a 390 × 844. La comprobación general pasó 2210 aserciones. El rastreo actualizado recorrió 285 páginas y 48 recursos, sin errores ni avisos. Véanse [qa-opaef.json](evidencias/qa-opaef.json) y [qa-crawl-opaef.json](evidencias/qa-crawl-opaef.json).

## Cron horario

Se instaló una sola entrada `0 * * * *` en el crontab del usuario local, con el servicio cron activo y zona horaria del host Europe/Madrid. Los nueve bucles anteriores se detuvieron y sus contenedores se retiraron conservando el volumen BOP. Una primera pasada manual completó el lector de Almería y los ocho bots con salida cero: siete avisos BOP recogidos por el lector y cero noticias nuevas o duplicadas en los bots. Una ejecución simultánea se omitió mediante `flock`. El instalador se repitió sin duplicar su entrada. [Evidencia de estados y recuentos](evidencias/qa-cron-horario.json).

ShellCheck, sintaxis Bash y configuración Compose pasaron. El ensayo aislado de comandos simulados verificó instalación idempotente, conservación de tareas ajenas y nueve ejecuciones únicas. Las 29 pruebas de los adaptadores y bot pasaron en Docker sin red. La revisión independiente confirmó el timeout de limpieza y la coincidencia exacta del marcador cron. No se ha esperado a una activación posterior del reloj: el recorrido real probado fue manual con el mismo runner instalado en cron.

## Repetición

Desde la raíz del proyecto, con el contenedor ya importado:

```bash
docker compose -f docker/compose.yaml exec -T --user www-data wordpress php /pruebas/verify_wp.php
docker compose -f docker/compose.yaml exec -T --user www-data wordpress php /pruebas/verify_wp.php --mutation
docker compose -f docker/compose.yaml exec -T --user www-data wordpress php /pruebas/verify_wp.php --bots
docker compose -f docker/compose.yaml exec -T --user www-data wordpress php /pruebas/verify_wp.php --bot-details
python3 scripts/crawl_site.py
python3 docs/evidencias/qa-ui-final.py
python3 docs/evidencias/qa-last-ui.py
```

La comprobación HTTP de permisos necesita un suscriptor local de prueba, que se elimina al terminar:

```bash
docker compose -f docker/compose.yaml exec -T --user www-data wordpress php /pruebas/verify_wp.php --security-fixture
python3 scripts/crawl_site.py --security --security-bot --out docs/evidencias/qa-security.json
docker compose -f docker/compose.yaml exec -T --user www-data wordpress php /pruebas/verify_wp.php --security-cleanup
```

Para recorrer las páginas con Chrome del sistema:

```bash
playwright-cli -s=facuso-qa open http://127.0.0.1:18086/ --browser=chrome
playwright-cli -s=facuso-qa run-code --filename=docs/evidencias/qa-ui-browser.js
playwright-cli -s=facuso-qa close
```

La prueba de seguridad fue focal: inspección del control de capacidades y nonce del importador, más solicitudes locales con usuarios anónimo, suscriptor y bot provincial, incluidos dos métodos XML-RPC. No representa una auditoría completa del núcleo, los plugins de terceros, la configuración futura de alojamiento ni la seguridad de las fuentes externas. El recorrido comprueba que las URL externas tienen una estructura válida y HTTPS; su disponibilidad y exactitud editorial requieren revisión antes de publicar.

Las sumas SHA-256 de los exportables ensayados constan en [PRUEBAS_IMPORTACION.md](PRUEBAS_IMPORTACION.md) y en `dist/SHA256SUMS.txt` para la entrega actual. La comprobación debe asociarse a esos archivos, sin trasladar los recuentos de un paquete anterior.

## Instalación de revisión en cidonia.cloud

WordPress se importó por CLI en el nuevo volumen del servidor: 74 páginas, 132 noticias, 39 categorías y 34 imágenes. La repetición conservó los contenidos. Se comprobaron 204 páginas HTML y 48 recursos locales a través de HTTPS con certificado validado y redirección HTTP 308; las otras webs de cidonia.cloud y juegos.cidonia.cloud conservaron HTTP 200. Chrome comprobó portada, OPAEF y Observatorio, cambio BOP→BOE de Almería, enlaces externos y vista móvil sin imágenes rotas ni desbordamiento. [Evidencia HTTPS](evidencias/qa-cidonia-https.json).

El lector y los ocho bots completaron una pasada con código cero y cero noticias nuevas o duplicadas después de corregir la consulta de publicaciones públicas importadas por otro autor. Se retiraron a papelera únicamente 35 copias automáticas creadas en la primera prueba y se conservaron los originales del snapshot. Se añadieron regresiones sobre ese caso y sobre un sumario BOP no disponible: 31 pruebas sin red pasaron. El BOP de Jaén devuelve HTTP 500 desde el VPS, aunque responde desde el equipo local; se registra y se continúa con las demás fuentes. Málaga conserva su limitación conocida. [Estados de los bots](evidencias/qa-bots-cidonia.json).

Se instaló un cron horario y una copia diaria privada. Una copia SQL se restauró en un MariaDB efímero, sin red ni puertos y separado de la base activa, con los recuentos esperados. Los archivos tar pasaron su comprobación de integridad y una copia privada se guardó fuera del VPS. [Evidencia de restauración](evidencias/qa-restauracion-cidonia.json). El manual de operación y los límites del ensayo están en [DESPLIEGUE_CIDONIA.md](DESPLIEGUE_CIDONIA.md).

La revisión focal independiente de código y configuración no encontró vulnerabilidades confirmadas. La auditoría completa quick se interrumpió por el límite de uso de los subagentes tras el reconocimiento; consta como incompleta y sus nueve unidades quedan diferidas. No se afirma una aprobación global de seguridad ni una prueba completa de recuperación del servidor.
