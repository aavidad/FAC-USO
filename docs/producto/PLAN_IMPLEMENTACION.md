# Estado de la entrega FAC-USO Andalucía

Fecha de referencia: 18 de octubre de 2026. El paquete y la instalación aislada están probados. Se ha desplegado un entorno de revisión en https://facuso.cidonia.cloud/ con HTTPS y bots horarios; la aprobación editorial definitiva sigue pendiente.

## Trabajo completado con evidencia local

| Resultado | Evidencia |
| --- | --- |
| Estructura y contenido | 74 páginas, de las que 72 están publicadas y dos en borrador; 132 noticias, 39 categorías, dos menús y 34 imágenes. `docs/PRUEBAS.md`. |
| Importación ZIP en WordPress vacío | 598 comprobaciones sin error; activación del tema, portada, menús y medios. Repetición con cero contenidos y medios nuevos. `docs/PRUEBAS_IMPORTACION.md`. |
| Importación XML con importador oficial | 557 comprobaciones sin error para páginas, noticias, categorías y menús. El XML requiere WordPress en raíz y enlaces permanentes legibles para sus rutas internas; tema y medios se instalan aparte. `docs/PRUEBAS_IMPORTACION.md`. |
| Enlaces bajo subdirectorio con ZIP | 552 comprobaciones sin error con `/portal`. `docs/PRUEBAS_IMPORTACION.md`. |
| Recorrido del sitio | 285 URL HTML y 48 recursos locales con HTTP 200, sin enlaces internos rotos; filtros combinados y paginación comprobados. Una pasada móvil recorrió 193 URL públicas; el último cambio visual se comprobó en portada, galería y dos noticias móviles. `docs/PRUEBAS.md`. |
| Idempotencia y recuperación | 2152 aserciones sin fallo al repetir importación, conservar una edición y recuperar una entrada interrumpida; el ensayo restauró el contenido original. Esto no acredita recuperación transaccional ante cualquier interrupción dentro de WordPress. `docs/PRUEBAS.md`. |
| Ocho bot provinciales | 70 noticias publicadas en el WordPress local, una o más por provincia; 1345 aserciones, segunda ejecución sin entradas nuevas, provincia y deduplicación comprobadas. `docs/PRUEBAS.md` y `docs/BOT_NOTICIAS.md`. |
| Aislamiento de cuentas de bot | REST provincial, URLs de fuente y acciones prohibidas probadas con respuestas 403; XML-RPC bloqueado para bot. `docs/PRUEBAS.md` y revisión focal independiente en `docs/REVISION_INDEPENDIENTE.md`. |
| Cron horario | Una entrada por usuario a las horas en punto, lector más ocho bots, primera pasada con nueve estados OK y cero duplicados; bloqueo concurrente comprobado. `docs/evidencias/qa-cron-horario.json`. |
| Aprovisionamiento portable | `bot/provision_wordpress.php` crea ocho cuentas y archivos privados mediante WP-CLI; una repetición conserva la configuración y rechaza conflictos. `docs/BOT_NOTICIAS.md`. |
| Fotografías y créditos | Todas las noticias muestran imagen y crédito; 25 fotos originales están enlazadas a su fuente, ocho recursos son ilustrativos y el montaje de campaña se identifica como generado con IA. `docs/PRUEBAS.md`. |

Los bot se ejecutan cada hora mediante cron. Almería lee el BOP mediante Chrome y JSON validado; Huelva consume la API oficial; Cádiz, Córdoba, Granada, Jaén y Sevilla usan lectores HTML. Málaga utiliza BOE y fuentes sindicales porque el BOP presenta una barrera de acceso. Esta limitación deja incompleta la vigilancia automática de ese boletín. Los 70 contenidos se guardaron como snapshot inicial; el bot sigue siendo el mecanismo para noticias futuras. La integración de avisos adicionales del BOE puede ampliar ese snapshot; sus recuentos no se dan por cambiados sin una nueva importación y prueba.

## Pendiente antes de la publicación definitiva

1. FAC-USO Andalucía debe aprobar la bienvenida firmada, el aviso legal y la política de privacidad; ambas páginas siguen en borrador. Debe ratificar cargos, correos y teléfonos, en especial la vocalía pendiente, y decidir qué equipo revisa las noticias de los bot.
2. La organización debe confirmar permisos editoriales de fotografías y distintivos, aportar los cuatro logotipos sectoriales faltantes y, si lo desea, sustituir las ilustraciones generadas por material propio. El montaje no debe presentarse como foto documental.
3. Decidir alojamiento, dominio, HTTPS, copias restaurables, cuentas humanas, roles, calendario de actualización y si los bot publicarán o crearán borradores. Los secretos de prueba no sirven para producción; deben aprovisionarse ocho credenciales nuevas.
4. Verificar contactos y enlaces externos justo antes de publicar. Revisar plazos de convocatorias contra sus bases y rectificaciones. El BOP de Málaga necesita una vía oficial de acceso automatizable o seguimiento editorial manual.
5. Repetir la prueba integral en la instalación definitiva y hacer la revisión de seguridad y accesibilidad correspondiente al hito público. La revisión local de código fue focal y los ensayos Docker no prueban el alojamiento futuro.

## Despliegue de revisión en cidonia.cloud

WordPress y MariaDB tienen volúmenes y redes propios; Caddy sirve HTTPS con Let’s Encrypt y renovación automática. Los ocho bots y el lector de Almería están instalados en el servidor, con cuentas nuevas y cron horario. Hay copias diarias y una restauración SQL ensayada sin tocar la base activa. El entorno conserva `noindex`. El manual operativo está en `docs/DESPLIEGUE_CIDONIA.md`. La auditoría completa quedó incompleta por cuota de subagentes; la revisión focal independiente y los ensayos no la sustituyen. El vídeo corregido está publicado en «Conócenos → Vídeos»: 63 fases acompasadas con la locución, 15 capítulos y subtítulos. Se ha comprobado la reproducción y el salto de tiempo en escritorio y móvil.

## Contradicciones encontradas

La primera petición de copiar el tema actual fue reemplazada por la decisión posterior de usar diseño propio. El XML ofrece una importación estándar del contenido, pero la experiencia completa de filtros, portada y medios se obtiene con el ZIP. El ODT repite sectores con diferencias; se usa la segunda lista, que incluye Diputaciones y Ayuntamientos.

## Cómo mantener este documento

Anotar una tarea como cerrada solo con prueba, fecha y artefacto. Cuando cambien los 132 contenidos, el tema o los bot, reconstruir ZIP y XML y actualizar sus ensayos y huellas. Los criterios de producto están en `PRD.md`, el recorrido en `FLUJO_APP.md` y los hallazgos editoriales en `docs/REVISION_CONTENIDO.md`.

ABSORBIDOS: `20261015 MODIFICACION ESTRUCTURA WEB.odt` — parcial; se incorpora el alcance y quedan en el original sus nombres y discrepancias. `docs/PRUEBAS.md`, `docs/PRUEBAS_IMPORTACION.md` y `docs/BOT_NOTICIAS.md` — parcial; se sintetiza el estado, esos documentos conservan comandos y evidencia detallada.

La sección de USO Diputación de Granada presenta sus cursos ajustados a las bases de las OPE de esta administración, con capturas reales y una práctica pública de seis preguntas de TCAE. El acceso completo permanece autorizado en el portal original. El recorrido y la procedencia se documentan en `docs/CURSOS_GRANADA.md`.
