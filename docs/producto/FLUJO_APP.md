# Flujo de la web FAC-USO Andalucía

Fecha de referencia: 18 de octubre de 2026. El ZIP de importación instala contenido y, si se marca la casilla de diseño, el tema FAC-USO Andalucía. El recorrido se probó en el WordPress aislado descrito en `docs/PRUEBAS.md`.

## Consulta pública

Inicio abre con acceso a los servicios, contacto, cinco sectores, ocho provincias y dos bloques de seis tarjetas con foto: actualidad sindical y bolsas y oposiciones. La primera selección excluye empleo para que una misma noticia no aparezca en ambos bloques. Cada tarjeta lleva a la noticia fechada y muestra su imagen y crédito.

En «Conócenos», la persona encuentra la organización, sus órganos, historia, sedes y contacto. «Servicios a la afiliación» reúne promociones, formación y asesoría jurídica. «Información» ofrece acción sindical, salud laboral, igualdad y empleo público; este último distingue bolsas, convocatorias de oposiciones y ofertas de empleo. La fecha de una noticia no significa que siga abierto su plazo. Cada anuncio enlaza su fuente oficial para comprobar bases, rectificaciones y vigencia.

«Sectores» abre los cinco ámbitos pedidos: Justicia, Sanidad, Administración local, Administración autonómica y Administración General del Estado. Sanidad se divide en personal sanitario, gestión y servicios, y personal sociosanitario. Administración local ofrece Bomberos, Policía local, Diputaciones, Ayuntamientos, Administración y servicios, y Función pública local. Administración autonómica ofrece Universidades, Personal laboral y Funcionariado. Las páginas muestran recursos y publicaciones filtradas del ámbito.

«Provincias» permite elegir Andalucía o cualquiera de las ocho provincias. Cada provincia muestra sede, teléfono y correo públicos de USO Andalucía, acceso al BOP y noticias atribuidas a ese territorio. «Empleo público del BOP» abre una subpágina interna con provincia fija y fuente BOP seleccionada. Se pueden consultar también BOE o todas las fuentes sin salir de esa provincia. El enlace al buscador estatal se distingue como recurso externo. Los enlaces externos HTTP(S) abren una pestaña nueva y los internos conservan la actual. Sevilla incorpora OPAEF con dos subpestañas: «USO-OPAEF · Sección sindical» y «Observatorio de Igualdad, Acoso y Discriminación USO-OPAEF». Ambas conservan acceso entre sí y remiten al contacto provincial para pedir hablar con la sección. Igualdad y Diputaciones también enlazan este espacio. El observatorio explica la escucha y el acompañamiento solicitados y la preparación de reuniones para negociar el I Plan de Igualdad, sin publicar casos ni atribuir acuerdos. En Granada se enlaza además el portal de la sección sindical de USO en la Diputación. El visitante puede combinar sector, materia y territorio en el listado de noticias; los filtros se aplican juntos y mantienen la selección. La navegación móvil dispone de botón de menú y submenús; todas las páginas conservan acceso a contacto y afiliación.

«Enlaces» abre los portales de USO Andalucía, USO y FAC-USO; BOE, BOJA y los ocho BOP; empleo público, retribuciones, FNMT, Justicia, Funciona y Cl@ve. Son sitios externos de cada organismo. «Conócenos > Vídeos» permite ver la presentación de la web dentro de la propia página, con controles, subtítulos y descarga. El recorrido explica las secciones y la automatización de noticias; las imágenes cambian después de cada frase. La galería muestra 25 fotos tomadas de publicaciones originales con enlace a su fuente y un montaje ilustrativo etiquetado como generado con IA.

## Edición y noticias automáticas

El administrador instala el ZIP desde WordPress y abre Herramientas > FAC-USO · Importación inicial. La importación crea páginas, entradas, categorías, menús y medios. La casilla de diseño activa el tema y configura la portada. Si ya existe un contenido con el mismo slug, se conserva y el informe de importación señala el conflicto. La segunda importación no duplica contenido ni medios; `docs/PRUEBAS_IMPORTACION.md` registra el ensayo.

Cada hora, cron ejecuta primero el lector de Almería y después los ocho bot, con un bloqueo contra solapamientos. Cada bot provincial consulta fuentes oficiales de empleo y noticias sindicales con una cuenta propia limitada a su provincia. El modo habitual crea borradores para revisión humana; la instalación local y el entorno remoto de revisión permiten publicación automática por encargo del responsable. El bot verifica fuente HTTPS, ámbito y duplicados antes de escribir. `docs/BOT_NOTICIAS.md` explica el aprovisionamiento y las fuentes activas. El BOP de Málaga requiere un control de acceso que impide hoy su extracción directa; allí se usan BOE y noticias sindicales como fuentes automáticas.

Antes de llevar el sitio al dominio definitivo, FAC-USO Andalucía valida cargos, sedes, teléfonos, textos legales y permiso editorial de las imágenes. Aporta la bienvenida firmada y los cuatro logotipos sectoriales que aún faltan. Las noticias externas conservan atribución y fecha.

## Contradicciones encontradas

El ODT repite la lista de sectores con cambios; se aplicó la segunda, que añade Diputaciones y Ayuntamientos. Los estatutos federales incluyen Correos y Telégrafos, mientras que el encargo local enumera cinco sectores. Se mantuvieron los cinco pedidos. La primera idea de copiar el tema actual fue sustituida por la decisión posterior del usuario de crear uno nuevo.

## Cómo mantener este documento

Actualizarlo cuando cambien una ruta, un filtro, una etapa de importación o un paso editorial. Contrastar con `data/*.json`, `scripts/build.py`, el tema y el complemento. El alcance está en `PRD.md`, la construcción en `TRD.md` y los pendientes en `PLAN_IMPLEMENTACION.md`.

ABSORBIDOS: `20261015 MODIFICACION ESTRUCTURA WEB.odt` — parcial; se recoge la jerarquía, mientras que el original conserva las personas y diferencias de sus listas. `data/territorios.json` y `scripts/build.py` — parcial; la estructura y el recorrido se resumen aquí, el contenido permanece en sus ficheros.

La sección de USO Diputación de Granada presenta sus cursos ajustados a las bases de las OPE de esta administración, con capturas reales y una práctica pública de seis preguntas de TCAE. El acceso completo permanece autorizado en el portal original. El recorrido y la procedencia se documentan en `docs/CURSOS_GRANADA.md`.
