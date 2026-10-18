# Operación de FAC-USO en cidonia.cloud

Instalación de revisión en **https://facuso.cidonia.cloud/**. Fecha: 18 de octubre de 2026. El dominio apunta a `186.240.156.68`. La web mantiene `blog_public=0` y cabecera `X-Robots-Tag: noindex, nofollow`: la aprobación editorial y la revisión completa de seguridad siguen pendientes.

## Componentes y capacidad

El servidor dispone de 4 CPU y 16 GB de RAM. Antes de instalar había 45 GB libres; después de descargar WordPress, MariaDB y Chromium quedan aproximadamente 40 GB. La carga medida fue baja y permanecen unos 13 GB de memoria disponible.

| Componente | Ubicación y aislamiento |
| --- | --- |
| Fuentes y configuración | `/opt/facuso`, propiedad de root. |
| WordPress | Proyecto Compose `facuso-cidonia`, contenedor `facuso-cidonia-wordpress-1`, volumen persistente propio. |
| Base de datos | MariaDB 11.4, contenedor `facuso-cidonia-db-1`, volumen propio y red interna; sin puerto publicado. |
| Entrada HTTP interna | Nginx sin privilegios; escucha en `127.0.0.1:18086` del host. Solo el gateway comparte la red del Caddy existente. |
| HTTPS | Caddy existente, bloque independiente de `facuso.cidonia.cloud`, certificado Let's Encrypt y renovación automática. |
| Bots | Ocho contenedores de ejecución única, cuentas provinciales y archivos de credenciales separados; lector Chromium de Almería sin credenciales WordPress. |
| Secretos | `/opt/facuso/.secrets/`, fuera del directorio web, del repositorio y de los paquetes. |
| Estados y registros | `/opt/facuso/.runtime/hourly-state/` y `hourly-logs/`. |
| Copias | `/opt/facuso/backups/`, acceso privado; retención de siete días por antigüedad. |

La configuración está en `docker/production/compose.yaml`, `nginx.conf` y `Caddyfile.facuso`. El bloque FAC-USO se añadió al Caddy existente después de validarlo; los bloques anteriores se conservaron byte a byte y Caddy se recargó sin reiniciar sus otras webs. Una copia de la configuración anterior permanece en `/opt/facuso/.runtime/Caddyfile.before-facuso`.

## Instalación y repetición

El paquete `dist/facuso-arranque.zip` se importa desde CLI mediante `/setup/init.php`, montado fuera del directorio web. El script exige CLI, el dominio previsto y entorno `staging`. La primera ejecución creó 74 páginas (72 publicadas y dos borradores), 132 noticias, 39 categorías, dos menús y 34 imágenes. Una segunda ejecución no duplicó contenido. Los archivos de español se incorporaron desde la instalación local validada.

```sh
ssh root@cidonia.cloud
cd /opt/facuso
docker compose -f docker/production/compose.yaml ps
docker compose -f docker/production/compose.yaml exec -T --user www-data wordpress php /setup/init.php
docker compose -f docker/production/compose.yaml exec -T --user www-data wordpress php /setup/provision.php
```

El segundo script reutiliza el aprovisionador con sus controles de ámbito y permisos. Crea o conserva las ocho cuentas `facuso-bot-<provincia>`; sus archivos privados son `0400`, propiedad del UID 33. No imprime claves. El administrador inicial es `facuso-admin`; su contraseña aleatoria se conserva exclusivamente en el archivo privado `admin_password` del servidor. El correo inicial `example.invalid` debe sustituirse por el del responsable cuando se configure el equipo editorial.

Los scripts `scripts/bootstrap*.php` y `sync_preview.php` pertenecen al entorno local y no se usan para este despliegue. Una reimportación conserva textos existentes: actualizar fuentes o volver a subir el ZIP no sustituye automáticamente páginas ya editadas.

## Noticias cada hora

El crontab de root ejecuta a las horas en punto:

```cron
0 * * * * /bin/bash /opt/facuso/bot/run-hourly.sh --production # FACUSO_HOURLY
```

La zona horaria del host es UTC. La copia diaria de las 03:35 se ejecuta, por tanto, a las 03:35 UTC. Los estados guardan fechas UTC. La pasada ejecuta primero el lector de Almería y después los ocho bots; `flock` evita solapamientos. Cada proceso tiene un tiempo máximo. Los contenedores no publican puertos ni reciben el socket Docker. El overlay `docker/production/collector.yaml` conecta el lector a la red de salida propia del despliegue. La configuración privada de Compose vive en `.runtime/cron.env`: HTTPS obligatorio, UID/GID 33 y publicación automática habilitada para esta instalación por encargo del responsable.

```sh
cd /opt/facuso
bash bot/run-hourly.sh --production
cat .runtime/hourly-state/almeria
tail -n 20 .runtime/hourly-logs/almeria.log
bash bot/install-cron.sh --production
```

El instalador es idempotente y conserva las tareas ajenas. Para detener las consultas futuras: `bash bot/install-cron.sh --remove`. Esto no detiene una pasada que ya está ejecutándose. Para volver a habilitarlas, use `--production`.

Las noticias iniciales pueden pertenecer al administrador que hizo la importación. El cliente compara tanto las publicaciones públicas como sus propios borradores para evitar duplicarlas. Cádiz puede tener dos anuncios distintos en la misma página PDF: la comparación incluye título y URL. Durante la primera prueba se detectaron y retiraron a la papelera 35 copias automáticas del snapshot; se conservaron sus originales. La corrección tiene pruebas sin red. Las 31 pruebas del bot y adaptadores pasaron en Docker sin red; la nueva pasada del lector y los ocho bots salió con código cero y no creó duplicados. No ejecute `reconcile-snapshot.php` como mantenimiento habitual: es una herramienta de conciliación inicial, no un purgador de noticias.

Los errores de un sumario diario se registran y no descartan los días que sí se hayan leído ni las otras fuentes. Revise los avisos del log aunque el proceso termine correctamente: una pasada correcta no garantiza que todas las fuentes hayan respondido. El BOP de Málaga sigue sin extractor activo; su bot recoge BOE y fuentes sindicales. El BOP de Jaén devuelve HTTP 500 desde el VPS para las tres fechas consultadas, aunque esos endpoints responden HTTP 200 desde el equipo local. Su conector sigue habilitado y reintenta cada hora; en la última pasada incorporó las siete coincidencias disponibles de BOE y fuentes sindicales, sin afirmar cobertura nueva del BOP. La fecha de una entrada no acredita que siga abierto un plazo de solicitud.

## Certificado y proxy

`Caddyfile.facuso` fija el directorio ACME de producción de Let's Encrypt. Se comprobó externamente un certificado para `facuso.cidonia.cloud`, emitido por Let's Encrypt YE1 y válido hasta el 16 de enero de 2027. La renovación automática usa los volúmenes persistentes de Caddy, no un cron adicional. HTTP redirige a HTTPS mediante 308.

```sh
curl -I https://facuso.cidonia.cloud/
openssl s_client -connect facuso.cidonia.cloud:443 -servername facuso.cidonia.cloud </dev/null 2>/dev/null | openssl x509 -noout -issuer -dates -ext subjectAltName
```

No sustituya el Caddyfile completo por el fragmento de este proyecto: el servidor también aloja otras webs. Haga una copia privada, añada o actualice solo el bloque FAC-USO, valide el candidato y recargue Caddy. Mantenga las claves del certificado y los datos de Caddy privados y persistentes.

## Copias y recuperación

```sh
cd /opt/facuso
bash docker/production/backup.sh
cat .runtime/last-backup
```

Hay una copia diaria a las 03:35 según el reloj del servidor. Cada carpeta fechada contiene `database.sql.gz`, `wordpress.tar.gz` y `private-config.tar.gz`. La copia SQL usa transacción consistente; la de archivos incluye `wp-content`, `wp-config.php` y `.htaccess`. **El archivo de configuración privada contiene secretos sin cifrar**: manténgalo con acceso privado y use SSH o almacenamiento cifrado para trasladarlo. Las copias no están montadas en el gateway ni en WordPress.

Se ensayó una restauración de la base en un MariaDB efímero sin red ni puertos, separado de los datos activos. La copia recuperó 74 páginas, 132 noticias, 34 adjuntos y nueve usuarios. También se verificó la integridad de ambos tar. Esto no equivale a un ensayo completo de recuperación del servidor o del almacenamiento de certificados. Se guardó una copia adicional fuera del VPS en la carpeta privada `.runtime/cidonia-backup/` del equipo de trabajo, excluida de Git.

Para recuperar una instalación, retire antes su cron y detenga únicamente el proyecto FAC-USO. Restaure archivos y SQL en volúmenes nuevos y separados, conserve el propietario de los secretos, y pruebe dominio, páginas, imágenes y permisos antes de conectarla al proxy. No importe una copia directamente sobre la base activa. No use `docker compose down -v` salvo que se pretenda borrar expresamente sus datos persistentes. La recuperación de Caddy debe conservar además sus volúmenes de certificados y los bloques de las otras webs.

## Actualización, parada y comprobaciones

Antes de actualizar, cree una copia y pruebe los paquetes en Docker local. Las imágenes de WordPress, MariaDB y Nginx están fijadas por digest en Compose; actualizar la imagen requiere revisar ese valor y recrear solo el servicio correspondiente. Las actualizaciones menores del núcleo están habilitadas; los cambios mayores requieren ensayo. No copie los secretos ni una base real al repositorio público.

```sh
cd /opt/facuso
docker compose -f docker/production/compose.yaml logs --no-color --tail=30 wordpress gateway
docker compose -f docker/production/compose.yaml stop
docker compose -f docker/production/compose.yaml up -d
```

Parar este proyecto no elimina el cron de bots. Si se detiene la web para mantenimiento, retire el cron y repóngalo al terminar. Los demás proyectos del servidor tienen su propia configuración y no deben detenerse.

El recorrido remoto comprobó 204 URL HTML y 48 recursos por HTTPS, sin errores. Chrome revisó portada, OPAEF, filtro BOP/BOE de Almería y vista móvil sin desbordamientos ni imágenes rotas. Las rutas de instalación, configuración, XML-RPC y scripts en subidas están bloqueadas. Los detalles están en `docs/evidencias/qa-cidonia-https.json`.

## Límites de la revisión de seguridad

La revisión focal independiente del código y del despliegue no encontró vulnerabilidades confirmadas. La auditoría completa quick inició cuatro reconocimientos y nueve unidades de cobertura, pero se interrumpió por la cuota de los subagentes antes de terminar caza, crítico y verificaciones. Queda registrada como **incompleta** en `/home/alberto/security-audit-skill/FAC-USO/run-1/` del equipo de trabajo. No se presenta como aprobación global. Antes de considerar este entorno la publicación definitiva deben completarse esa revisión, la aprobación editorial y los responsables de mantenimiento.
