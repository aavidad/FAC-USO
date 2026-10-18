# Vídeo corregido: ritmo y correspondencia con la voz

Versión 2 publicada en [Conócenos → Vídeos](https://facuso.cidonia.cloud/conocenos/videos/). Se sustituyó la navegación rápida de la primera versión por **56 fases**, cada una con su propia locución, acción y permanencia. La bienvenida permanece en la portada y el menú se mantiene visible mientras se explica.

El resultado dura **11:35,3**, con 15 capítulos, H.264 1440 × 1000 a 25 fps, AAC y 56 cues de subtítulos en castellano. SHA-256 del MP4: `93523f3a4a94d2ec9c1d0b24ce850de2953d578f97a29c59f9511708da0b36a9`.

Se midió un mínimo de **8,35 segundos de permanencia tras cada acción**. La voz de cada fase empieza después de preparar su pantalla y termina antes del cambio siguiente. Las transiciones de la navegación se conservan a velocidad real y el montaje prolonga el último fotograma para dar tiempo a la explicación y a la lectura. Un ancla visual relaciona el reloj de la captura con los PTS del WebM, siguiendo el método ETF.

La voz conserva el estilo de la primera edición: `es-ES-AlvaroNeural`, velocidad `+4 %`, WAV mono de 24 kHz y normalización del MP4 a −16 LUFS. Se generó por frases para medir cada pista por separado. La narración se actualizó para explicar que la web y los bots ya están instalados en cidonia.cloud, con las limitaciones actuales de los BOP de Málaga y Jaén.

`ffprobe` verificó los flujos y capítulos. El MP4 completo decodificó sin errores. Se comprobó matemáticamente que todas las pistas de voz quedan dentro de su fase y se revisaron fotogramas del principio, menú, OPAEF, móvil y automatización. La hoja de control usa fotogramas del MP4 final, no capturas alternativas.

Se publicó el archivo en el directorio de medios de WordPress y se verificó su huella mediante una descarga HTTP/2 completa desde fuera del servidor. El proxy transmite estos medios sin acumular el MP4 en su tmpfs limitada. HTTP Range devuelve 206 y los tipos MIME de vídeo, póster y VTT son correctos.

Chrome comprobó reproducción, pausa, salto al segundo 180 y carga de los 56 cues de subtítulos. El elemento no tiene error de medios. En una pantalla de 390 px, el documento mide 390 px y el vídeo 354 px, sin desbordamiento. Las cancelaciones de Range al buscar otra posición o cerrar el navegador son operaciones esperadas de Chromium; no hubo errores nuevos de protocolo tras la corrección del proxy.

La actualización se realizó mediante un script CLI restringido a esta instalación y exclusivamente a la página propia `conocenos/videos`, guardando una revisión previa. El código de inicialización no es un endpoint HTTP. La fuente del vídeo en el paquete es una URL HTTPS pública, no una ruta de secretos ni una sesión de acceso. Los binarios están en `video/` del repositorio; el ZIP del complemento conserva su tamaño reducido y referencia el vídeo alojado.

Los resultados y límites están en [qa-video-v2.json](../evidencias/qa-video-v2.json). La revisión técnica acredita las comprobaciones descritas; la aceptación editorial del ritmo y la explicación corresponde al responsable.
