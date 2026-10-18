# Recorrido con voz: versión corregida

La versión vigente está publicada en [la web](https://facuso.cidonia.cloud/conocenos/videos/) y en [video/](../../video/README.md). Su guion es [guion-v2.md](guion-v2.md) y el plan de acciones y locuciones está en [plan-v2.json](plan-v2.json).

El método conserva la voz española usada en ETF y alinea cada frase con una pantalla. Hay 63 fases y 15 capítulos. Primero se prepara la locución y se mide su duración. Chrome graba las acciones reales contra la web pública, sin sesión de WordPress. Cada capítulo incluye un ancla visual para relacionar el reloj del navegador con los PTS del WebM. El montaje conserva el movimiento sin acelerarlo y prolonga la pantalla final durante la explicación, con un mínimo de lectura. El inicio permanece en la portada; no se usa un avance de páginas que todavía no se explica.

## Repetir en el entorno de trabajo

```sh
/home/alberto/Vídeos/ETF/.herramientas/voz/bin/python scripts/recorridos/preparar_v2.py
node scripts/recorridos/grabar_v2.mjs /home/alberto/Vídeos/FAC-USO/corregido-v2-<huella> --preflight
node scripts/recorridos/grabar_v2.mjs /home/alberto/Vídeos/FAC-USO/corregido-v2-<huella>
python3 scripts/recorridos/montar_v2.py /home/alberto/Vídeos/FAC-USO/corregido-v2-<huella>
```

`preparar_v2.py` requiere el entorno existente de edge-tts fijado usado en ETF. Se usa `es-ES-AlvaroNeural` a `+4 %`; al servicio se envía únicamente la locución pública. `FACUSO_VIDEO_OUTPUT` permite elegir una carpeta de trabajo fuera del repositorio. La captura admite `FACUSO_PLAYWRIGHT_PACKAGE` y `FACUSO_CHROME` para reutilizar una instalación de Playwright y Chrome del sistema, sin descargar dependencias al ejecutar. El montaje requiere FFmpeg con H.264/AAC, ffprobe y Pillow.

La captura bloquea service workers, WebSocket, redirecciones, métodos distintos de GET y orígenes ajenos a la web pública. Los esquemas sobre los bots se identifican como explicaciones y no se presentan como paneles reales. Los originales, pistas por frase y archivos temporales se guardan fuera del repositorio. Solo los medios finales, las capturas públicas y los guiones se versionan.

`publish-video.php` actualiza exclusivamente la página propia de Vídeos mediante CLI en el servidor, conservando una revisión. Los archivos MP4, JPG y VTT se copian al directorio público de medios y `data/video-presentacion.json` registra sus URLs y la huella del vídeo. Las credenciales no forman parte de esa publicación.

La [QA vigente](QA.md) detalla duración, codec, mínimo de lectura, subtítulos, reproducción remota y límites. Los archivos `voz.py`, `grabar.mjs`, `montar.py`, `guion.md` y `QA-v1.md` conservan la primera versión como referencia; no son el flujo usado para la corrección.

La ampliación incorpora el catálogo público, el índice TCAE C1 y la muestra real del tema de Constitución de USO Diputación de Granada. Solo se permiten GET a las rutas públicas seleccionadas y sus estilos; nunca se abre el área privada ni se envían consultas al tutor. El capítulo también se ofrece como vídeo corto en la sección de Granada.
