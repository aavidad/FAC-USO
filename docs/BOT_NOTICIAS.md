# Noticias provinciales automáticas

El paquete WordPress contiene los contenidos iniciales. Los ocho bots de `bot/` añaden las noticias posteriores: uno por provincia, con cuenta y contraseña de aplicación propias. Cada bot consulta fuentes públicas, clasifica sus hallazgos y los envía a WordPress mediante la API REST. La configuración habitual crea borradores para revisión. En el WordPress local de pruebas se puede usar `BOT_PUBLISH=true` para comprobar el recorrido completo.

## Instalación remota

La web y los ocho bots están instalados en https://facuso.cidonia.cloud/. El cron horario usa `--production`; el lector de Almería emplea `docker/production/collector.yaml`. Las credenciales son nuevas y privadas del servidor. El manual completo está en [DESPLIEGUE_CIDONIA.md](DESPLIEGUE_CIDONIA.md). El BOP de Jaén está devolviendo HTTP 500 desde ese VPS: su bot registra los avisos y continúa con BOE y fuentes sindicales, reintentando el boletín en cada pasada.

## Fuentes activas

| Provincia | Fuentes oficiales de empleo | Noticias sindicales |
|---|---|---|
| Almería | [BOE, sección II.B](https://www.boe.es/datosabiertos/api/api.php?lang=es) y [BOP de Almería](https://app.dipalme.org/bop/publico.zul) mediante Chrome | [FAC-USO Andalucía](https://facusoandalucia.es/feed/), [USO](https://www.uso.es/feed/) |
| Cádiz | BOE y [BOP de Cádiz](https://www.bopcadiz.es/index.html) | FAC-USO Andalucía y USO |
| Córdoba | BOE y [BOP de Córdoba](https://bop.dipucordoba.es/) | FAC-USO Andalucía y USO |
| Granada | BOE y [BOP de Granada](https://bop.dipgra.es/publica/consulta-de-bops/) | FAC-USO Andalucía y USO |
| Huelva | BOE y [BOP de Huelva](https://s2.diphuelva.es/servicios/bope_web/UltimoBop) | FAC-USO Andalucía y USO |
| Jaén | BOE y [BOP de Jaén](https://bop.dipujaen.es/) | FAC-USO Andalucía y USO |
| Málaga | BOE | FAC-USO Andalucía y USO |
| Sevilla | BOE y [BOP de Sevilla](https://bopsevilla.dipusevilla.es/publica/consulta-de-bops/) | FAC-USO Andalucía y USO |

El BOE se consulta por la [API oficial de sumarios](https://www.boe.es/datosabiertos/documentos/APIsumarioBOE.pdf), durante los últimos siete días, en la sección II.B de oposiciones y concursos. Los BOP activos se consultan durante tres días; Huelva ofrece [anuncios en JSON por fecha](https://s2.diphuelva.es/lib/bope/anuncios_bop/ajaxAnuncios.php). Los RSS sindicales se filtran por provincia mencionada en el título. Un anuncio que menciona dos provincias puede publicarse en ambas, con registros separados.

La cobertura del BOE es complementaria: no equivale a leer todos los BOP. Almería necesita un contenedor adicional con Chrome porque su portal ejecuta JavaScript; entrega al bot principal un archivo JSON de anuncios verificados. El [BOP de Málaga](https://www.bopmalaga.es/bopma.php) mostró una verificación de acceso y sigue sin extractor activo. Los anuncios iniciales de Málaga sí están en el paquete de importación cuando la fuente concreta pudo verificarse manualmente.

## Qué publica

Cada noticia lleva el título, la fecha de la publicación original y un enlace a ella. Para el BOE añade hasta seis párrafos, con un máximo conjunto de 2.000 caracteres, tomados del texto HTML oficial. Si ese texto no está disponible, conserva fecha y enlace. Los RSS sindicales usan como máximo 25 palabras del título y no copian el cuerpo de la noticia. El bot no calcula plazos ni da por abierta una convocatoria; los requisitos y fechas deben comprobarse en el anuncio original. No descarga PDF ni adjuntos.

Las categorías son la provincia, el sector y la materia. Las materias de empleo se guardan como `empleo-publico`, `bolsas-de-trabajo`, `oposiciones` u `ofertas-de-empleo-publico`. El bot conserva `facuso_source_url` y un identificador externo. Antes de insertar consulta las publicaciones públicas de su provincia y sus propios borradores; así reconoce también el snapshot importado por un administrador. Después comprueba el slug calculado para esa provincia. Una segunda ejecución no debe añadir duplicados.

El sector se asigna cuando el título identifica al organismo: por ejemplo, una universidad andaluza entra en Universidades y Administración autonómica, mientras que un ayuntamiento entra en Administración local. Si el título no permite conocerlo, la noticia conserva la provincia y la materia sin forzar un sector.

## Cuentas y secretos

WordPress debe tener instalado el plugin `facuso-arranque`, las categorías del paquete y ocho usuarios `facuso-bot-<provincia>` con permisos limitados a su provincia. Cada usuario necesita una contraseña de aplicación distinta. El aprovisionador la guarda en un archivo con el nombre de la provincia bajo un directorio privado; estos archivos no se incluyen en el paquete ni en Git.

## Aprovisionar una instalación nueva

Tras importar el paquete y activar `facuso-arranque`, ejecute [provision_wordpress.php](../bot/provision_wordpress.php) con [WP-CLI `eval-file`](https://developer.wordpress.org/cli/commands/eval-file/) y una cuenta administradora. La web de destino debe ofrecer HTTPS para las [contraseñas de aplicación](https://developer.wordpress.org/rest-api/using-the-rest-api/authentication/). Prepare un directorio padre privado, escribible por el usuario que ejecuta WP-CLI y situado fuera de `ABSPATH`, `wp-content` y el directorio público de la web. Por ejemplo, si ese usuario tiene acceso a `/srv/facuso-privado`:

```bash
install -d -m 0700 /srv/facuso-privado
FACUSO_DOCUMENT_ROOT=/ruta/publica/de/la/web wp --path=/ruta/a/wordpress --user=ADMIN eval-file /ruta/al/paquete/bot/provision_wordpress.php -- /srv/facuso-privado/bots
```

`FACUSO_DOCUMENT_ROOT` debe señalar el directorio que sirve el servidor web, incluso cuando WordPress esté instalado en un subdirectorio. El guion crea `bots` con permisos `0700` y ocho archivos con permisos `0400`. Muestra rutas y recuentos, nunca las claves. También crea las ocho cuentas `facuso-bot-<provincia>` con el rol restringido del plugin y una contraseña web aleatoria que no se entrega. Las contraseñas de aplicación se usan solo con la API REST; el plugin impide el acceso de esas cuentas por el formulario de WordPress. El guion bloquea los correos de WordPress durante esta ejecución y no llama a Telegram. Si hay otros plugins que notifican por vías propias al crear usuarios, revise esa configuración antes de aprovisionar.

Repita el mismo comando si necesita comprobarlo: conservará cuentas y secretos que coincidan. Si encuentra una cuenta con otro rol o ámbito, un secreto que no corresponde al bot o permisos de archivo inseguros, se detiene antes de crear nada. No copie `scripts/bootstrap_bots.php` al destino: ese archivo pertenece únicamente al ensayo Docker local y rota credenciales cada vez.

En una instalación con contenedores, monte el mismo directorio privado en el contenedor que ejecuta WP-CLI y en el host donde corre Compose; use en ambos la misma ruta absoluta. Los archivos `0400` solo los lee su propietario: compruebe su UID/GID con `stat -c '%u:%g' /srv/facuso-privado/bots/almeria` y establezca `BOT_UID` y `BOT_GID` con esos valores. Después, desde `bot/`, configure `WP_APP_PASSWORD_DIR=/srv/facuso-privado/bots` y `WP_BASE_URL=https://tu-wordpress.example`. Construya las imágenes y programe la ejecución horaria como se indica a continuación. El valor predeterminado es crear borradores para revisión. No incluya `BOT_PUBLISH=true` en el despliegue hasta que la redacción decida publicar automáticamente.

## Cron cada hora

Cron ejecuta una pasada a las horas en punto (`0 * * * *`), con la zona horaria del host. El lector de Almería se ejecuta primero y después los ocho bots, una sola vez cada uno. Un bloqueo `flock` impide solapar pasadas; cada proceso tiene un tiempo máximo y se elimina su contenedor al terminar. No quedan bucles de seis horas activos. La deduplicación conserva las noticias que ya existen.

Desde la raíz del proyecto, cree `.runtime/cron.env` con permisos `0600` y propietario igual al usuario que ejecutará cron. Es un archivo de variables de Compose: el runner no lo ejecuta como código. Incluya `WP_BASE_URL`, `WP_APP_PASSWORD_DIR` y, si los secretos pertenecen a otro UID/GID, `BOT_UID` y `BOT_GID`. Para producción use HTTPS y mantenga `BOT_PUBLISH=false` hasta decidir la publicación automática.

En el ensayo local se usan estos valores adicionales:

```dotenv
WP_BASE_URL=http://facuso-importacion-wordpress-1
WP_ALLOW_LOCAL_HTTP=true
WP_APP_PASSWORD_DIR=/ruta/absoluta/a/los/secretos/bots
BOT_PUBLISH=true
HUELVA_BOP_IP=IP_PUBLICA_VIGENTE_DEL_BOP
```

Construya las imágenes antes de instalar el cron:

```bash
docker compose --env-file .runtime/cron.env -f bot/compose.yaml -f bot/compose.local.yaml --profile bots build
docker compose --env-file .runtime/cron.env -f bot/compose.almeria-browser.yaml --profile bots build
bash bot/install-cron.sh --local
crontab -l
```

El instalador conserva las entradas de cron ajenas y no duplica la suya al repetirlo. En un despliegue público, omita `--local` y ajuste la red del lector de Almería al despliegue. Para retirar solo esta tarea: `bash bot/install-cron.sh --remove`.

Puede lanzar una pasada manual con `bash bot/run-hourly.sh --local`. Los resultados por provincia se guardan en `.runtime/hourly-state/` y los registros acotados y rotatorios en `.runtime/hourly-logs/`. Un fallo en una fuente no impide ejecutar los otros bots; Almería mantiene su archivo anterior y el consumidor comprueba su antigüedad. Los estados usan fechas UTC. El host, Docker y el servicio cron deben estar encendidos; una instalación local apagada no ejecuta tareas pendientes.

Si se migra desde los bucles anteriores, detenga sus ocho servicios y el lector antes de instalar la tarea horaria; no borre el volumen `facuso_almeria_bop`. Los contenedores de cada pasada son de ejecución única y tienen `restart: "no"`.

El lector de Almería no dispone de contraseña de WordPress. Comparte con el bot un volumen Docker que este monta en solo lectura. Si el archivo aún no existe, el bot sigue procesando el BOE y los RSS.

`compose.local.yaml` conecta cada bot a las redes Docker `facuso-importacion_local` y `facuso-importacion_acceso`. Use el nombre exclusivo del contenedor `facuso-importacion-wordpress-1`: el alias genérico `wordpress` puede coincidir con otra instalación de pruebas en la red compartida. La resolución DNS de `s2.diphuelva.es` falló en este equipo; `HUELVA_BOP_IP` permite la resolución local mientras se comprueba el certificado TLS con el nombre oficial. Verifique la IP pública vigente y retire la excepción cuando DNS vuelva a funcionar. Los contenedores no necesitan permisos de administración de WordPress ni acceso al socket de Docker.

Se puede comprobar una provincia sin escribir en WordPress:

```bash
python3 bot.py --province granada --dry-run
```

Si ya existen noticias creadas por una versión anterior del bot, complete los textos del BOE y corrija sus categorías una sola vez por provincia:

```bash
docker compose --env-file ../.runtime/cron.env -f compose.yaml --profile bots run --rm -T cadiz --province cadiz --enrich-existing --dry-run
docker compose --env-file ../.runtime/cron.env -f compose.yaml --profile bots run --rm -T cadiz --province cadiz --enrich-existing
```

El comando solo modifica publicaciones de la cuenta provincial con identificador de bot y cuerpo igual a la plantilla automática anterior. Deja intactos los textos editados por una persona. En el ensayo local se añaden también `-f compose.local.yaml` a los comandos anteriores.

Y pasar las pruebas sin acceso a la red:

```bash
python3 -m unittest -q test_bot.py test_adapters_west.py test_adapters_missing.py test_adapters_huelva.py
```

La configuración de fuentes está en `bot/sources.json`. Solo se admiten los dominios oficiales definidos en el código. Una redirección de una fuente a otro dominio se rechaza; WordPress no sigue redirecciones autenticadas. Las respuestas se limitan a 2 MB y las peticiones tienen un tiempo máximo de 12 segundos.
