# Avisos de empleo del BOP de Almería

Este contenedor consulta el [sumario público del BOP de Almería](https://app.dipalme.org/bop/publico.zul) con Chromium. Busca los tres últimos días laborables, comprueba la fecha de publicación de cada fila y recoge hasta 20 avisos sobre plazas, bolsas y procesos selectivos. Guarda `/data/almeria_bop.json` mediante sustitución atómica. El bot de Almería lee ese archivo y crea borradores en WordPress.

El JSON usa `schema: 1`, `generated_at` en UTC e `items` con `title`, `url`, `date`, `excerpt` vacío y `source: "bop"`. Cada enlace apunta al PDF individual en el dominio oficial. Si el portal cambia o deja de responder, el archivo previo conserva sus datos; el consumidor comprueba su antigüedad antes de usarlos.

Para ejecutar una consulta local después de crear la red `facuso-importacion_acceso`:

```sh
docker compose -f bot/compose.almeria-browser.yaml --profile bots build almeria_browser
docker compose -f bot/compose.almeria-browser.yaml --profile bots run --rm almeria_browser --once
```

En servicio, el cron horario ejecuta una consulta única antes del bot de Almería mediante `--once`; el modo de bucle manual también espera una hora entre consultas. Véase [operación del cron](../../docs/BOT_NOTICIAS.md). Tiene navegador sin sesión persistente, usuario propio, sistema de archivos de solo lectura, sin credenciales de WordPress y sin puertos publicados. Solo admite solicitudes HTTPS al área `/bop/` de `app.dipalme.org`: obtiene cada respuesta sin seguir redirecciones y bloquea cualquier respuesta 3xx. El AppArmor del equipo impide activar la caja de aislamiento interna de Chromium; la barrera efectiva es el contenedor con AppArmor, seccomp y capacidades eliminadas. La red de Docker permite salir a Internet; la regla del navegador limita sus propias solicitudes, pero no sustituye una política de salida de red del despliegue.

Prueba del analizador sin navegador:

```sh
python -m unittest discover -s bot/almeria_browser -p 'test_*.py'
```

La regresión de redirecciones usa dos servidores de prueba en el loopback del contenedor, sin salida a Internet. El primero devuelve un 302 al segundo y comprueba que este no recibe solicitudes:

```sh
docker run --rm --network none --read-only --user 10001:10001 \
  --tmpfs /tmp:rw,nosuid,size=64m --shm-size 128m --memory 512m \
  --cpus 1 --pids-limit 128 --cap-drop ALL --security-opt no-new-privileges:true \
  --mount type=bind,src="$PWD/bot/almeria_browser",dst=/app,readonly \
  --entrypoint python bot-almeria_browser /app/integration_redirect.py
```
