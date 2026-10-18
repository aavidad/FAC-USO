# Vídeo de recorrido FAC-USO Andalucía

El guion público está en [guion.md](guion.md). El resultado se guarda fuera del repositorio, en `/home/alberto/Vídeos/FAC-USO/recorrido-<huella>/`. La carpeta contiene `video.mp4`, `voz.wav`, `guion.md`, `capitulos.txt`, `ficha-tecnica.md`, `hoja-control.png`, capturas por escena y los clips originales. El vídeo se grabó sobre la vista previa local `127.0.0.1:18086`; no representa un despliegue de producción.

El método sigue el recorrido de ETF: voz `es-ES-AlvaroNeural` a `+4 %` con la versión fijada de `edge-tts`, WAV mono a 24 kHz, grabación real con Playwright y Chrome del sistema, salida H.264 de 1440 × 900 a 25 fps, AAC y normalización a −16 LUFS. La bienvenida muestra un avance de pantallas reales. Después se navega con clics y selectores; las tres cartelas finales explican los bots sobre imágenes de la web y se identifican como esquemas, no como controles de WordPress.

Para repetirlo en este entorno:

```sh
python3 scripts/recorridos/voz.py
node scripts/recorridos/grabar.mjs /home/alberto/Vídeos/FAC-USO/recorrido-<huella>
python3 scripts/recorridos/montar.py /home/alberto/Vídeos/FAC-USO/recorrido-<huella>
```

La huella se imprime al preparar la voz. La grabación conserva escenas terminadas si un enlace cambia y hay que reanudar. Antes de reanudar, se corrige el selector contra la página pública actual y se comprueba que el guion no haya cambiado. Si cambia el guion, `voz.py` crea otra carpeta para no mezclar audio de distintas versiones. Las variables `FACUSO_VIDEO_OUTPUT`, `FACUSO_EDGE_PYTHON` y `FACUSO_PLAYWRIGHT_PACKAGE` permiten escoger la salida externa, el intérprete con la versión fijada de `edge-tts` y una instalación existente de `playwright-core`; sus valores predeterminados señalan al kit local de ETF. `FACUSO_CHROME` permite indicar otro Chrome del sistema. No se instalan dependencias al ejecutar el recorrido.

El navegador solo permite solicitudes GET al origen local, además de `about:` y `data:` para su funcionamiento interno. Bloquea service workers, WebSocket y redirecciones HTTP; no inicia sesión ni abre las fuentes externas. El sintetizador recibe únicamente las frases públicas del guion, sin capturas, contraseñas ni sesiones. Las rutas de producción y el estado editorial no se infieren de las cartelas.

La revisión final comprueba duración, códecs, capítulos, pista audible, correspondencia general entre voz y acciones, texto de OPAEF, selector BOP/BOE de Almería, filtros combinados, vista móvil, crédito de imágenes y límite del BOP de Málaga. Las capturas por escena y `hoja-control.png` ayudan a localizar un tramo, pero hay que revisar también el MP4 completo. La locución de cada apartado es continua; no se ha calculado una alineación exacta de cada oración con cada clic.
