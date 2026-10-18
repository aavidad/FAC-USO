# Requisitos de producto: importación inicial FAC-USO Andalucía

Fecha de referencia: 18 de octubre de 2026. Responsable de aceptación: FAC-USO Andalucía, pendiente de designación formal.

## Propósito y personas usuarias

El encargo consiste en entregar un fichero que pueda importarse en una instalación vacía de WordPress para crear la estructura y los contenidos iniciales de FAC-USO Andalucía. Quien visite la web debe poder encontrar información de la organización, servicios para la afiliación y noticias por sector, materia y provincia. El equipo editorial necesita una estructura que pueda mantener sin rehacer menús o categorías.

Los públicos previstos son personal de las administraciones y servicios públicos, afiliación y representantes de USO, personas interesadas en afiliarse y responsables de publicación de la federación. El paquete propone cuentas provinciales restringidas para los bot; la organización aún debe designar a su equipo editorial humano.

La fuente de alcance es `20261015 MODIFICACION ESTRUCTURA WEB.odt` (documento original conservado en local, excluido del repositorio público), facilitada por la organización. También se toma como referencia la web en construcción `https://facusoandalucia.es/`, la Confederación `https://www.uso.es/`, la unión territorial `https://www.usoandalucia.es/` y la federación estatal `https://facuso.es/`. La ruta `https://facusoandalucia.es/facuso/` comunicada durante el trabajo respondía 404 el 18 de octubre de 2026; la API pública de WordPress sí exponía contenido en el dominio raíz.

## Alcance de la primera entrega

| Prioridad | Resultado esperado |
| --- | --- |
| Imprescindible | Menú con «Conócenos», «Servicios a la afiliación», «Información» y «Enlaces»; sus subpáginas siguen el ODT. |
| Imprescindible | Publicaciones clasificables por sector, materia y territorio, con Andalucía y las ocho provincias. |
| Imprescindible | Contenido inicial útil y atribuido a fuentes públicas, resumido con redacción propia. Cada página declara sus fuentes. |
| Imprescindible | Importación reproducible en WordPress vacío y comprobación en un WordPress aislado. |
| Imprescindible | Noticias sindicales y noticias de bolsas, oposiciones y ofertas de empleo separadas en portada, con fecha, fuente y provincia. |
| Imprescindible | Ocho bot provinciales para incorporar actualidad de fuentes oficiales y sindicales, con publicación en borrador como opción habitual. |
| Imprescindible | Fotografías o imágenes de recurso en todas las noticias, con origen y crédito visibles. |
| Importante | Mantener reconocible lo que ya existe en la web en construcción: entradas «Qué es la USO-Andalucía», «Historia de la USO», «Caja de Resistencia y Solidaridad» y páginas de acción sindical, salud laboral e igualdad. Si se importa sobre ese sitio, conservar sus contenidos. |
| Importante | Directorio regional del ODT, con fecha y aviso de verificación. La vocalía marcada para sustitución no aparece con nombre. |
| Pendiente de material | Bienvenida firmada por la Secretaría General, documentos regionales aprobados de congresos y resoluciones, confirmación de cargos y direcciones, y material propio autorizado para sustituir imágenes de recurso. |

El fichero [institucional.json](../../data/institucional.json) contiene las páginas de «Conócenos», «Servicios a la afiliación» e «Información», sus fuentes y los datos pendientes. La estructura de «Enlaces», los sectores, provincias, materias y publicaciones se documenta en los otros documentos de producto y en los datos de importación correspondientes.

## Criterios de aceptación

1. En WordPress vacío, una importación crea las cuatro secciones de navegación y todas las hijas solicitadas, con relaciones padre e hijo correctas.
2. Las páginas publicadas contienen texto útil y enlaces a las fuentes; una URL externa que cambie puede corregirse sin cambiar código.
3. La bienvenida permanece en borrador hasta recibir un texto aprobado por su firmante. Los cargos sin titular verificado se describen sin asignarles un nombre.
4. Las noticias pueden filtrarse por los tres ejes del ODT. Los ocho territorios provinciales están presentes.
5. El fichero de importación no contiene artículos externos íntegros, claves ni datos privados. Los correos del ODT figuran solo como contactos profesionales facilitados por la organización, con su fecha de origen.
6. Se facilita evidencia de una importación de prueba en contenedores y una relación de lo que necesita validación editorial antes de publicar.
7. Las ocho provincias tienen página, contacto y noticias filtradas; los bot no duplican una noticia al repetir su ejecución ni atribuyen un aviso a otra provincia.
8. Cada provincia dispone de un apartado interno de empleo público con anuncios de su BOP como selección inicial y BOE como filtro complementario. Los enlaces externos HTTP(S) abren otra pestaña. Los ocho bot se programan cada hora con cron.
9. OPAEF, dentro de Sevilla, ofrece dos subapartados con contenido: sección sindical USO-OPAEF y Observatorio de Igualdad, Acoso y Discriminación USO-OPAEF. Se explica el apoyo a quien lo solicita y el trabajo preparatorio del I Plan de Igualdad; no se publican casos personales.
10. Portada, entradas y galería muestran imágenes con crédito. Las imágenes generadas con IA se identifican como ilustrativas y no se presentan como fotos de sucesos reales.

## Decisiones y límites conocidos

- El usuario eligió WordPress, pidió la prueba en Docker y decidió un tema nuevo, moderno y funcional en verde, rojo y blanco de FAC-USO. El ZIP importador incluye el complemento y el tema. Posteriormente autorizó un entorno de revisión en cidonia.cloud con dominio facuso.cidonia.cloud, HTTPS y bots horarios en el servidor. Los responsables humanos de edición siguen pendientes.
- El ODT pide un escudo provincial o logo sectorial junto al logo regional según la sección. Aún faltan los ficheros oficiales de algunos distintivos y reglas de uso; ningún emblema se atribuye a una entidad sin comprobar su procedencia.
- La duplicación de sectores en el ODT introduce «Diputaciones» y «Ayuntamientos» en la segunda lista. Esta lista más detallada sirve de base, pendiente de ratificación editorial.
- La web en construcción ya tiene contenido real y taxonomías parciales. Una importación pensada para WordPress vacío podría duplicarlo si se ejecuta allí sin conciliación de slugs y entradas.
- Las condiciones de promociones, formación y prestaciones cambian. La página inicial explica el servicio y dirige a la fuente vigente, sin fijar precios, plazos o cuantías caducables.
- No se han confirmado los textos legales del sitio, formularios ni política editorial. Las fotografías oficiales incorporadas llevan procedencia y crédito; la entidad debe confirmar su autorización editorial para publicarlas en el dominio definitivo.
- El BOP de Málaga impide hoy la consulta automatizada directa con una verificación de acceso. Su bot utiliza BOE y noticias sindicales; esto no equivale a una cobertura completa del boletín provincial.

## Contradicciones encontradas

El ODT denomina «Qué es la USO-Andalucía» a una página que propone copiar de la Confederación, cuya fuente explica la USO estatal. La página inicial aclara la relación entre USO, USO Andalucía y FAC-USO; enlaza ambas fuentes sin presentarlas como la misma organización. El ODT incluye una vocal de Garantías que debe ser sustituida por jubilación: se omite su nombre hasta que llegue la composición vigente.

## Cómo mantener este documento

Actualizar alcance, prioridades y criterios cuando FAC-USO Andalucía apruebe cambios. Registrar aquí las decisiones editoriales y remitir los detalles de pila, datos, interfaz, recorrido y tareas a `TRD.md`, `ESQUEMA_BACKEND.md`, `DISENO_UI_UX.md`, `FLUJO_APP.md` y `PLAN_IMPLEMENTACION.md`.

ABSORBIDOS: `20261015 MODIFICACION ESTRUCTURA WEB.odt` — parcial; conserva el listado original, nombres y direcciones de contacto, así como las diferencias entre las dos listas de sectores. Fuentes web oficiales — parcial; se sintetizan aquí y en `data/institucional.json`, y siguen siendo referencia para actualizaciones.

La sección de USO Diputación de Granada presenta sus cursos ajustados a las bases de las OPE de esta administración, con capturas reales y una práctica pública de seis preguntas de TCAE. El acceso completo permanece autorizado en el portal original. El recorrido y la procedencia se documentan en `docs/CURSOS_GRANADA.md`.
