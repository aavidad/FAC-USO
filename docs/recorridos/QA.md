# Comprobación del vídeo de recorrido

Estado editorial: el responsable ha pedido ralentizar la navegación, mantener visibles menús y apartados mientras se explican y corregir el inicio. Esta revisión técnica no supone aceptación de ese ritmo visual. La corrección está pendiente y no se ha regenerado el vídeo.

Fecha: 18 de octubre de 2026. El vídeo se grabó en la vista previa pública local de FAC-USO Andalucía, sin entrar en WordPress. Los artefactos de trabajo están en `/home/alberto/Vídeos/FAC-USO/recorrido-9b1bb6d68b/`, fuera del repositorio.

| Artefacto | Comprobación |
| --- | --- |
| `video.mp4` | 455,40 s (7:35), 33.221.671 bytes, H.264 1440 × 900 a 25 fps, AAC mono a 48 kHz y 14 capítulos. SHA-256 `d9378b5d7520a20d142ecd3943beed0427df7b7b3c7f69ea99192170d00949a0`. |
| `voz.wav` | PCM mono de 16 bits a 24 kHz, 455,40 s. SHA-256 `8105825254416aa229c725ddf422b86526d0d31eb3ec2ae1a221c089202c7a6f`. |
| `guion.md` | 15 tramos narrados. SHA-256 `073f2879c62146244f1e7bf7c498099d8caff509674aebdedb0250a2ba45982d`. |
| `hoja-control.png` | 15 fotogramas extraídos del MP4 definitivo, uno por tramo, con tiempo, título y texto. SHA-256 `a65ad77d9193f206c1946da29676bb65369aeb5b5d92bf8ab79fce6a97fe3410`. |

`ffprobe` confirma los flujos, duración y capítulos. `ffmpeg -v error -i video.mp4 -f null -` decodificó el archivo completo con salida 0 y sin errores. La medición EBU R128 de la pista AAC dio −16,2 LUFS integrados y pico real de −1,1 dBFS. La voz WAV tiene una media de −21,9 dBFS, medida con `volumedetect`; el volumen del MP4 se ajustó para la reproducción. Los 15 tramos terminan normalmente alrededor de 1,2 segundos después de la voz; la cartela de fuentes termina 2,1 segundos después. No hay colas de varios segundos sin contenido.

Se revisaron fotogramas del MP4 al inicio, en servicios, OPAEF, la noticia, la vista móvil y las tres cartelas de los bot. El rótulo inferior final es una sola franja opaca, que cubre el rótulo de grabación y no tapa los controles usados. La vista móvil aparece centrada; su grabación muestra menú, submenú y entrada a Contacto. El capítulo de OPAEF pasa por Sevilla, la sección sindical y el Observatorio. El de Almería cambia el selector provincial de BOP a BOE. El de noticias combina sector, materia y provincia. La noticia de Justicia se abrió por su tarjeta local; muestra imagen, crédito «USO Andalucía» y el acordeón de fuente desplegado, sin abrir el destino externo. Las tres cartelas finales se identifican como esquemas explicativos sobre páginas reales; el bloque de automatización dura 2:19.

El texto sintetizado coincide exactamente con las 15 locuciones del [guion final](guion.md): SHA-256 de esas frases concatenadas `5fc3d2dc57eb91271bf2412ed2a214055f1195c5a40fc3b88506d0193e2e4eba`. Tras sintetizar se corrigieron notas editoriales del Markdown, sin cambiar ninguna locución. El nombre de la carpeta conserva la huella del archivo en el momento de preparar la voz; la huella de las frases permite comprobar la correspondencia con la edición final. Se usó el entorno de voz de ETF con `edge-tts` fijado al commit `0b1c544d020b01338ae491d7f4547729afdc39d3`, voz `es-ES-AlvaroNeural` a `+4 %`. El sintetizador recibió únicamente texto público del guion.

La primera tanda de captura usó una ruta de red que permitía continuar las peticiones del navegador. Las escenas de servicios, información, sectores, OPAEF, la noticia, móvil y las tres explicaciones de bot se regrabaron después con la guardia final: solo GET al origen local, redirecciones bloqueadas, sin service workers ni WebSocket. Las escenas conservadas de la primera tanda fueron bienvenida, portada, Conócenos, Almería BOP→BOE, filtros y Fotos/Enlaces/Afiliación. Ninguna tanda usó una sesión de WordPress ni abrió enlaces externos. El código entregado incorpora la guardia final para nuevas grabaciones.

La locución se monta por apartado, con clics y pausas dentro de cada uno. La revisión visual confirma correspondencia general entre tema narrado y páginas mostradas, pero no mide sincronía exacta por oración. La escucha subjetiva de principio a fin corresponde a la revisión editorial del archivo final; las medidas técnicas de audio no sustituyen esa escucha. El vídeo muestra una instalación local de prueba: ni el cron ni los bot se presentan como desplegados en producción, y el BOE de Málaga no se confunde con cobertura del BOP.
