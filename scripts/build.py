"""Construye el paquete portable y el WXR desde los datos editoriales."""
from pathlib import Path
import copy
import html
import json
import re
import zipfile
from urllib.parse import urlparse
from datetime import datetime, timezone
import unicodedata
from zoneinfo import ZoneInfo
from lxml import etree as ET
from lxml import html as LH

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'package/facuso-arranque'
DIST = ROOT / 'dist'

def read(name):
    return json.loads((ROOT / 'data' / name).read_text())

def page(slug, title, body, parent='', status='publish', sources=None):
    return dict(slug=slug, title=title, html=body, parent=parent, status=status,
                sources=sources or [], notes=[])

def ordered(items):
    output = []
    todo = list(items)
    while todo:
        ready = [p for p in todo if not p.get('parent') or p['parent'] in {x['slug'] for x in output}]
        if not ready:
            raise ValueError('Jerarquía cíclica o padre inexistente: ' + str([x['slug'] for x in todo]))
        output.extend(ready)
        todo = [p for p in todo if p not in ready]
    return output

def build_content():
    institutional, territories, news = read('institucional.json'), read('territorios.json'), read('noticias.json')
    opaef = read('opaef.json')
    pages = copy.deepcopy(institutional['pages'] + territories['pages'] + opaef['pages'])
    by_slug = {p['slug']: p for p in pages}
    opaef_navigation = by_slug['opaef']
    for item in opaef['pages']:
        links = []
        for tab in opaef_navigation['tabs']:
            active = tab['page'] == item['slug']
            links.append('<a class="fac-button' + ('' if active else ' secondary')
                         + '" href="[[page:' + tab['page'] + ']]"'
                         + (' aria-current="page"' if active else '') + '>'
                         + html.escape(tab['label']) + '</a>')
        by_slug[item['slug']]['html'] = ('<nav class="fac-actions fac-opaef-tabs" aria-label="'
            + html.escape(opaef_navigation['navigation_label'], quote=True) + '">'
            + ''.join(links) + '</nav>\n' + by_slug[item['slug']]['html'])
    for entry in opaef.get('entry_points', []):
        by_slug[entry['page']]['html'] += entry['html']
    # El origen es útil para la trazabilidad, pero los textos públicos hablan de la organización.
    by_slug['comision-ejecutiva-regional']['html'] = re.sub(r'^<p>.*?</p>',
        '<p>La Comisión Ejecutiva Regional distribuye su trabajo en las siguientes áreas. Directorio facilitado por la organización el 15 de octubre de 2026.</p>',
        by_slug['comision-ejecutiva-regional']['html'], count=1)
    by_slug['comision-ejecutiva-regional']['html'] = by_slug['comision-ejecutiva-regional']['html'].replace('Según el mismo directorio, ', '')
    by_slug['que-es-la-uso-andalucia']['html'] = by_slug['que-es-la-uso-andalucia']['html'].split('</p>')[0] + '</p><p>La afiliación participa a través de su sección sindical, su federación profesional y su unión territorial. Puedes ampliar la información en la <a href="https://www.uso.es/que-es-la-uso/">presentación de USO</a> y consultar la <a href="https://www.usoandalucia.es/">actividad de USO Andalucía</a>.</p>'
    by_slug['historia-de-la-uso']['html'] = by_slug['historia-de-la-uso']['html'].split('</p>')[0] + '</p><p>La <a href="https://www.uso.es/historia/">historia publicada por la Confederación</a> recorre los orígenes del sindicato, la clandestinidad y su desarrollo. Sus documentos permiten conocer la evolución de la organización y de su actividad sindical.</p>'
    by_slug['crs']['html'] = by_slug['crs']['html'].split('</p>')[0] + '</p><p>Para solicitar una prestación, consulta al sindicato la antigüedad de afiliación exigida, la documentación del conflicto y el procedimiento aplicable. Las cuantías y los requisitos vigentes se recogen en la <a href="https://www.uso.es/servicios-afiliacion/">información confederal de servicios</a> y en el <a href="https://www.uso.es/wp-content/uploads/2024/10/sindicato-uso-caja-de-resistencia-y-solidaridad-crs.pdf">documento sobre la CRS</a>.</p>'
    by_slug['fotos']['html'] = '<p>Consulta las imágenes de actos, movilizaciones y encuentros sindicales que acompañan las <a href="https://www.usoandalucia.es/fac-uso/">noticias de FAC-USO en Andalucía</a> y la <a href="https://facuso.es/">actualidad federal</a>. Las fotografías se abren en la publicación de origen, donde conservan su contexto y autoría.</p>'
    if (PACKAGE/'theme/assets/montaje-campana.webp').exists():
        by_slug['fotos']['html'] += '<h2>Propuesta visual de campaña</h2><p>Montaje ilustrativo a partir de una fotografía de las jornadas de SPJ-USO Andalucía de septiembre de 2026. El escenario y la multitud se han generado; no representan la asistencia a un acto real.</p>[facuso_imagen file="montaje-campana.webp"]<p><a href="https://www.usoandalucia.es/44420-2/">Publicación de la fotografía original</a>.</p>'
    by_slug['fotos']['html'] += '<h2>Fotografías de la actividad sindical</h2><p>Cada imagen enlaza su noticia de origen en USO Andalucía.</p>[facuso_galeria]'
    by_slug['videos']['html'] = '<p>Los <a href="https://www.uso.es/videos-corporativos/">vídeos corporativos de USO</a> presentan el sindicato y su actividad. Consulta también los testimonios y noticias audiovisuales publicados por <a href="https://facuso.es/">FAC-USO</a>. Los vídeos se abren en la plataforma de origen.</p>'
    # Referencias internas portables: el instalador las resuelve con las URL de destino.
    for p in pages:
        def internal(match):
            raw = match.group(1)
            slug = raw.strip('/').split('/')[-1]
            return 'href="[[page:' + slug + ']]"' if slug in by_slug else match.group(0)
        p['html'] = re.sub(r'href="(/[^"#]*)"', internal, p['html'])
        p['parent'] = p.get('parent') or ''
    sectors = [p for p in pages if p['parent'] == 'sectores']
    provinces = [p for p in pages if p['parent'] == 'territorios' and p['slug'] != 'andalucia']
    province_slugs = {p['slug'] for p in provinces}
    for province in provinces:
        slug = province['slug']
        name = province['title']
        employment_slug = 'empleo-publico-' + slug
        # El acceso provincial abre nuestros anuncios, con el BOP seleccionado.
        province['html'] = province['html'].replace(
            '<a href="https://administracion.gob.es/empleopublico">Empleo público</a>',
            '<a href="[[page:' + employment_slug + ']]">Empleo público del BOP de ' + html.escape(name) + '</a>'
            '</li><li><a href="https://administracion.gob.es/empleopublico">Buscador estatal de empleo público (web externa)</a>')
        body = '<p>Bolsas de trabajo, convocatorias y ofertas de empleo público de ' + html.escape(name) + '. La selección inicial muestra los anuncios del boletín provincial incorporados a esta web.</p><p>Puedes filtrar por tipo de anuncio y cambiar la fuente para consultar también el BOE. Comprueba siempre las bases y sus rectificaciones; la fecha de una noticia no indica que el plazo siga abierto.</p>'
        if slug == 'malaga':
            body += '<p>La lectura automática del BOP de Málaga no está disponible desde este entorno. Selecciona BOE para ver las convocatorias que sí se han incorporado y consulta el boletín provincial para el resto de anuncios.</p>'
        pages.append(page(employment_slug, 'Empleo público de ' + name, body, parent=slug))
    home = '<section class="fac-hero"><p class="fac-eyebrow">FAC-USO Andalucía · Servicios públicos</p><h1>Tu trabajo al servicio de la ciudadanía.<br>Tus derechos, con USO.</h1><p>Información sindical para quienes trabajan en las administraciones, la sanidad y los servicios públicos de Andalucía.</p><div class="fac-actions"><a class="fac-button" href="[[page:servicios-a-la-afiliacion]]">Servicios a la afiliación</a><a class="fac-button secondary" href="[[page:contacto]]">Contacta con tu sindicato</a></div></section>'
    home=home.replace('</section>', '<img class="fac-hero-photo" width="1280" height="720" src="[[asset:foto-empleo.webp]]" alt="Mesa de trabajo y preparación de empleo público"><span class="fac-hero-photo-credit">Imagen de recurso · IA</span></section>',1)
    home += '<section class="fac-section"><div class="fac-section-head"><h2>Encuentra tu sector</h2></div><ul class="fac-sector-links">'
    home += ''.join(f'<li><a href="[[page:{p["slug"]}]]">{html.escape(p["title"])}</a></li>' for p in sectors)
    home += '</ul></section><section class="fac-section"><h2>Cerca de ti</h2><ul class="fac-territory-links">'
    home += ''.join(f'<li><a href="[[page:{p["slug"]}]]">{html.escape(p["title"])}</a></li>' for p in provinces)
    home += '</ul></section><p><a class="fac-button secondary" href="[[page:empleo-publico]]">Bolsas y oposiciones por provincia</a></p>[facuso_publicaciones excluir_empleo="1" limite="6"][facuso_publicaciones materia="empleo-publico" titulo="Bolsas y oposiciones" limite="6" filtros="0"]'
    pages.insert(0, page('inicio', 'Inicio', home))
    pages += [
        page('noticias', 'Noticias', '<p>Consulta la actividad sindical y los recursos publicados. Combina sector, materia y territorio para encontrar lo que te interesa.</p>[facuso_publicaciones]'),
        page('afiliacion', 'Afíliate a USO', '<p>La afiliación permite participar en el sindicato y acceder a sus servicios, con las condiciones que correspondan en cada caso.</p><p>Consulta la <a href="https://facuso.es/afiliate/">información y el formulario oficial de FAC-USO</a>. Si necesitas orientación antes de solicitar el alta, <a href="[[page:contacto]]">contacta con FAC-USO Andalucía</a>.</p>', sources=[{'url':'https://facuso.es/afiliate/','title':'Afiliación FAC-USO'}]),
        page('empleo-publico', 'Empleo público', '<p>Encuentra anuncios oficiales de empleo por provincia y tipo de proceso. Una oferta de empleo público anuncia plazas previstas; una convocatoria regula el proceso selectivo y su plazo. Una bolsa de trabajo sirve para cubrir necesidades temporales según sus propias bases.</p><p>Consulta el anuncio oficial y sus rectificaciones antes de presentar una solicitud. La fecha de una noticia no indica que el proceso siga abierto.</p>', parent='informacion'),
        page('bolsas-de-trabajo', 'Bolsas de trabajo', '<p>Anuncios sobre bolsas de empleo temporal de ayuntamientos, diputaciones y otras entidades. En cada noticia tienes el organismo y la publicación oficial para consultar requisitos, trámites y plazos.</p>', parent='empleo-publico'),
        page('oposiciones', 'Convocatorias de oposiciones', '<p>Convocatorias y bases de procesos de selección. Revisa en la publicación oficial las plazas, el sistema selectivo, la titulación, las tasas y la forma de presentar la solicitud.</p>', parent='empleo-publico'),
        page('ofertas-de-empleo-publico', 'Ofertas de empleo público', '<p>Las ofertas de empleo público recogen plazas previstas para su convocatoria. Su publicación no abre por sí sola el plazo de solicitudes. Consulta las convocatorias posteriores y las bases de cada proceso.</p>', parent='empleo-publico'),
        page('aviso-legal', 'Aviso legal y privacidad', '<p>Pendiente de completar y aprobar por la entidad responsable: identidad, NIF, domicilio, contacto, finalidades, bases jurídicas, conservación y ejercicio de derechos. Revisar también la configuración del alojamiento y de WordPress.</p>', status='draft'),
        page('creditos', 'Fuentes y créditos', '<p>Los textos informativos enlazan las fuentes de USO, FAC-USO y los organismos públicos que permiten ampliarlos. Las noticias se presentan como resúmenes y conservan su fecha original. La selección inicial se consultó el 18 de octubre de 2026.</p><h2>Identidad gráfica</h2><p>Los logotipos de FAC-USO y SPJ-USO pertenecen a sus respectivas organizaciones. Los escudos provinciales proceden de Wikimedia Commons, con las atribuciones que se indican a continuación.</p>' + ''.join('<p><a href="'+html.escape(a['url'])+'">'+html.escape(a['title'])+'</a> · '+html.escape(a['author'])+' · <a href="'+html.escape(a['license_url'] or a['url'])+'">'+html.escape(a['license'])+'</a>. '+html.escape(a['changes'])+'</p>' for a in read('assets.json'))),
    ]
    pages = ordered(pages)
    by_slug = {p['slug']: p for p in pages}
    categories = [dict(slug=s, title=t, parent='', description='') for s,t in [('sectores','Sectores'),('materias','Materias'),('territorios','Territorios')]]
    sector_slugs = {p['slug'] for p in pages if p['parent']=='sectores'}
    for p in pages:
        if p['parent'] == 'sectores' or p['parent'] in sector_slugs:
            categories.append(dict(slug=p['slug'],title=p['title'],parent=p['parent'],description=''))
    for slug,title in [('notas-de-prensa','Notas de prensa y comunicados'),('salud-laboral','Salud laboral y prevención de riesgos'),('formacion','Formación y competencias profesionales'),('campanas','Campañas'),('accion-sindical','Acción sindical'),('igualdad','Igualdad')]:
        categories.append(dict(slug=slug,title=title,parent='materias',description=''))
    categories.append(dict(slug='empleo-publico',title='Empleo público',parent='materias',description='Convocatorias, bolsas y ofertas publicadas por los organismos competentes.'))
    for slug,title in [('bolsas-de-trabajo','Bolsas de trabajo'),('oposiciones','Convocatorias de oposiciones'),('ofertas-de-empleo-publico','Ofertas de empleo público')]:
        categories.append(dict(slug=slug,title=title,parent='empleo-publico',description=''))
    for p in pages:
        if p['parent'] == 'territorios':
            categories.append(dict(slug=p['slug'],title=p['title'],parent='territorios',description=''))
    cat_map = {c['slug']:c for c in categories}
    for p in pages:
        children = [x for x in pages if x['parent']==p['slug'] and x['status']=='publish']
        if children and p['slug'] not in {'inicio', 'opaef'}:
            p['html'] += '\n[facuso_secciones]'
        slug=p['slug']
        if slug in province_slugs:
            p['html'] += f'\n[facuso_publicaciones materia="empleo-publico" territorio="{slug}" fuente="bop" titulo="Empleo del BOP de {html.escape(p["title"])}" limite="6" filtros="0"]'
            p['html'] += '<p><a class="fac-button secondary" href="[[page:empleo-publico-' + slug + ']]">Ver bolsas y empleo público de ' + html.escape(p['title']) + '</a></p>'
            p['html'] += f'\n[facuso_publicaciones territorio="{slug}" excluir_empleo="1" titulo="Actualidad sindical de {html.escape(p["title"])}"]'
        elif slug.startswith('empleo-publico-') and p['parent'] in province_slugs:
            p['html'] += f'\n[facuso_publicaciones materia="empleo-publico" territorio="{p["parent"]}" fuente="bop" titulo="Anuncios de empleo"]'
        elif slug in cat_map and cat_map[slug]['parent']:
            root=cat_map[slug]['parent']
            dimension = 'territorio' if root=='territorios' else 'materia' if root in ['materias','empleo-publico'] else 'sector'
            p['html'] += f'\n[facuso_publicaciones {dimension}="{slug}"]'
        elif slug=='diputacion-de-granada':
            p['html'] += '\n[facuso_publicaciones sector="diputaciones" territorio="granada"]'
        elif slug=='informacion':
            p['html'] += '\n[facuso_publicaciones]'
        section_photo = {'formacion':'formacion','sanidad':'sanidad','administracion-de-justicia':'justicia','asesoria-juridica':'justicia','salud-laboral':'sanidad','empleo-publico':'empleo','servicios-a-la-afiliacion':'formacion','conocenos':'formacion','sectores':'empleo','territorios':'empleo','enlaces':'empleo'}.get(slug)
        if section_photo:
            p['html'] = '[facuso_imagen file="foto-'+section_photo+'.webp"]\n'+p['html']
    employment=read('empleo-provincial.json')
    posts = copy.deepcopy(news['posts']+employment['posts'])
    if (ROOT/'data/bot-news-snapshot.json').exists():
        posts += copy.deepcopy(read('bot-news-snapshot.json')['posts'])
    for p in posts:
        if 'employment_type' in p:
            p['html'] += '<p><strong>Organismo:</strong> '+html.escape(p['employer'])+'.</p><p>Este anuncio forma parte del archivo de empleo público. La fecha de publicación no acredita que el plazo siga abierto. Comprueba las bases, las rectificaciones y los anuncios posteriores en la fuente oficial.</p>'
    # Preserva el contenido ya publicado como resúmenes, sin importar demos de las plantillas.
    summaries = {
        686: ('Preparación de oposiciones para la afiliación de USO', 'USO informa de cursos para preparar procesos de AGE, Seguridad Social y Correos dirigidos a afiliación al corriente de cuota A. La publicación explica el acceso a las clases, grabaciones y consultas. Para conocer las ediciones y las condiciones que siguen disponibles, revisa la información original antes de solicitar la inscripción.', ['administracion-general-del-estado','formacion']),
        683: ('Campaña de USO para participar en las elecciones sindicales', 'La campaña electoral de USO anima a formar candidaturas y participar en la representación de las plantillas. La publicación de FAC-USO Andalucía presenta los objetivos de crecimiento sindical y el papel de delegadas y delegados en la negociación colectiva. Incluye un enlace a los materiales confederales de la campaña.', ['campanas','accion-sindical','andalucia']),
        494: ('USO analiza las medidas de vivienda publicadas en octubre', 'La web de FAC-USO Andalucía recoge el análisis sindical de dos decretos sobre vivienda publicados en octubre de 2026. Expone medidas relativas a alquiler, compra y vivienda protegida, y señala la situación de su tramitación. Consulta la publicación y los textos oficiales enlazados para comprobar su vigencia y aplicación.', ['notas-de-prensa']),
        491: ('USO rechaza ampliar las altas médicas por mutuas', 'El sindicato expresa su oposición a que las mutuas decidan altas en procesos de enfermedad común. Su comunicado cuestiona el debate sobre absentismo y reclama mejorar la prevención en los puestos de trabajo, contar con estadísticas públicas y proteger a quienes están de baja. La publicación desarrolla sus argumentos y orientaciones para representantes.', ['salud-laboral','accion-sindical']),
        488: ('USO repasa las iniciativas laborales pendientes de tramitación', 'La publicación de FAC-USO Andalucía recoge un balance sindical de iniciativas laborales y sociales que estaban pendientes de aprobación. Entre los asuntos tratados figuran jornada, registro horario, prevención e igualdad. Se ofrece como información de contexto fechada; el estado de cada iniciativa debe comprobarse en sus fuentes parlamentarias y normativas.', ['notas-de-prensa','accion-sindical']),
        381: ('Información sobre la protección jurídica laboral USO–ARAG', 'FAC-USO presenta una póliza para determinados conflictos derivados de la actividad laboral o funcionarial. La información describe garantías de defensa y apoyo económico sujetas a requisitos, límites y exclusiones. Quien tenga interés debe consultar las condiciones contractuales y confirmar con su organización las modalidades de adhesión que estén vigentes.', ['accion-sindical']),
        231: ('Autorrefuerzo en órganos judiciales de Cádiz durante 2026', 'SPJ-USO Cádiz difunde una autorización de servicios extraordinarios en órganos judiciales de Jerez, Cádiz y Algeciras y en la Audiencia Provincial. La publicación sitúa el programa entre el 16 de septiembre y el 15 de noviembre de 2026 y explica la distribución de las prolongaciones de jornada. Los detalles deben contrastarse con la resolución aplicable.', ['administracion-de-justicia','cadiz','accion-sindical']),
        208: ('FAC-USO reclama más prevención y medios contra incendios', 'En una publicación sobre el incendio de Los Gallardos, FAC-USO traslada su apoyo a las personas afectadas y critica las carencias que atribuye al dispositivo de prevención y extinción. Reclama plantillas estables, medios suficientes y coordinación entre administraciones. El enlace original recoge la valoración sindical fechada y su contexto.', ['bomberos','almeria','salud-laboral']),
    }
    for original in read('web-existente.json'):
        if original['id'] not in summaries:
            continue
        title, text, cats=summaries[original['id']]
        posts.append(dict(slug=original['slug'],title=title,date=original['date'],status='publish',html='<p>'+html.escape(text)+'</p>',categories=cats,sources=[{'url':original['link'],'title':title}],notes=['Resumen de contenido ya publicado en FAC-USO Andalucía.']))
    for p in posts:
        p['type']='post'
        p['date']=p['date'].replace('T',' ')
        if not set(p['categories']) <= set(cat_map):
            raise ValueError('Categoría sin definir: '+str(p))
        if p['date']>'2026-10-18 23:59:59':
            raise ValueError('Noticia futura')
    pending = institutional['pending'] + territories['pending'] + [
        'Aportar los logotipos oficiales de Sanidad, Administración local, Administración autonómica y AGE. El tema permite configurarlos sin modificar código.',
        'Completar y aprobar aviso legal y privacidad antes de la publicación pública.',
        'Configurar credenciales propias de WordPress para el bot; la entrega no modifica el servidor de Diputación.',
    ]
    pending += employment.get('pending',[])
    # El paquete sí incluye los escudos, y tiene enlace secundario desde Diputaciones a Granada.
    pending=[x for x in pending if not x.startswith('Aportar logos sectoriales y escudos') and not x.startswith('Confirmar si la sección')]
    menus={'facuso-principal':[], 'facuso-pie':[]}
    for slug in ['inicio','conocenos','sectores','territorios','servicios-a-la-afiliacion','informacion','enlaces']:
        menus['facuso-principal'].append({'page':slug,'title': 'Provincias' if slug=='territorios' else 'Servicios' if slug=='servicios-a-la-afiliacion' else by_slug[slug]['title']})
        for child in [p for p in pages if p['parent']==slug and p['status']=='publish']:
            menus['facuso-principal'].append({'page':child['slug'],'parent':slug})
    for slug in ['contacto','sedes','afiliacion','noticias','creditos']:
        menus['facuso-pie'].append({'page':slug})
    def path(p):
        return (path(by_slug[p['parent']])+'/' if p['parent'] else '')+p['slug']
    for p in pages:
        p['path']=path(p)
        # Medianoche del día de referencia; evita programar las páginas para el futuro.
        p['date']='2026-10-18 00:00:00'
    assert len(pages)==len(set(p['slug'] for p in pages))
    assert len(posts)==len(set(p['slug'] for p in posts))
    return dict(version='1.0.0',date='2026-10-18',site={'title':'FAC-USO Andalucía','description':'Servicios públicos. Derechos laborales. Tu sindicato en Andalucía.'},pages=pages,posts=posts,categories=categories,menus=menus,pending=pending)

def wxr(data):
    ns={'excerpt':'http://wordpress.org/export/1.2/excerpt/','content':'http://purl.org/rss/1.0/modules/content/','wfw':'http://wellformedweb.org/CommentAPI/','dc':'http://purl.org/dc/elements/1.1/','wp':'http://wordpress.org/export/1.2/'}
    rss=ET.Element('rss',version='2.0',nsmap=ns); channel=ET.SubElement(rss,'channel')
    def add(parent,tag,value='',cdata=False):
        if ':' in tag:
            prefix,local=tag.split(':',1);tag='{'+ns[prefix]+'}'+local
        e=ET.SubElement(parent,tag);e.text=ET.CDATA(str(value)) if cdata else str(value);return e
    add(channel,'title',data['site']['title']);add(channel,'link','https://facusoandalucia.es');add(channel,'description',data['site']['description']);add(channel,'language','es-ES');add(channel,'wp:wxr_version','1.2');add(channel,'wp:base_site_url','https://facusoandalucia.es');add(channel,'wp:base_blog_url','https://facusoandalucia.es')
    author=add(channel,'wp:author');add(author,'wp:author_id',1);add(author,'wp:author_login','equipo-facuso',True);add(author,'wp:author_email','');add(author,'wp:author_display_name','Equipo FAC-USO',True)
    term_ids={c['slug']:i+1 for i,c in enumerate(data['categories'])}
    for c in data['categories']:
        e=add(channel,'wp:category');add(e,'wp:term_id',term_ids[c['slug']]);add(e,'wp:category_nicename',c['slug'],True);add(e,'wp:category_parent',c['parent'],True);add(e,'wp:cat_name',c['title'],True)
    menu_terms={name:len(term_ids)+i+1 for i,name in enumerate(data['menus'])}
    for name,tid in menu_terms.items():
        e=add(channel,'wp:term');add(e,'wp:term_id',tid);add(e,'wp:term_taxonomy','nav_menu');add(e,'wp:term_slug',name);add(e,'wp:term_name',name,True)
    ids={p['slug']:100+i for i,p in enumerate(data['pages']+data['posts'])}
    def meta(item,key,value):
        e=add(item,'wp:postmeta');add(e,'wp:meta_key',key,True);add(e,'wp:meta_value',value,True)
    used_import_dates=set()
    cat_parents={c['slug']:c['parent'] for c in data['categories']}
    employment_sources=read('fuentes-empleo.json')
    def in_category(post,slug):
        for category in post.get('categories',[]):
            while category:
                if category==slug:return True
                category=cat_parents.get(category,'')
        return False
    def static_publications(match):
        atts=dict(re.findall(r'([a-z_]+)="([^"]*)"',match[0]))
        matching=[]
        for post in data['posts']:
            if post['status']!='publish':continue
            if any(atts.get(key) and not in_category(post,atts[key]) for key in ['sector','materia','territorio']):continue
            if atts.get('excluir_empleo')=='1' and in_category(post,'empleo-publico'):continue
            if atts.get('fuente'):
                host=urlparse(post.get('sources',[{}])[0].get('url','')).hostname
                if not any(s['kind']==atts['fuente'] and host in s['hosts'] and (s['kind']!='bop' or not atts.get('territorio') or s['province']==atts['territorio']) for s in employment_sources):continue
            matching.append(post)
        matching.sort(key=lambda p:(p['date'],ids[p['slug']]),reverse=True)
        limit=min(18,max(3,int(atts.get('limite','9'))))
        heading=html.escape(atts.get('titulo','Actualidad sindical'))
        if not matching:return '<h2>'+heading+'</h2><p>No hay anuncios incorporados con esta selección.</p>'
        return '<h2>'+heading+'</h2><ul>'+''.join('<li><a href="/'+p['slug']+'/">'+html.escape(p['title'])+'</a></li>' for p in matching[:limit])+'</ul>'
    for p in data['pages']+data['posts']:
        item=add(channel,'item');add(item,'title',p['title'],True);add(item,'link','https://facusoandalucia.es/'+p.get('path',p['slug'])+'/');add(item,'dc:creator','equipo-facuso',True);add(item,'guid','https://facusoandalucia.es/?p='+str(ids[p['slug']]))
        body=re.sub(r'\[\[page:([a-z0-9-]+)\]\]',lambda m:'/'+next(q['path'] for q in data['pages'] if q['slug']==m[1])+'/',p['html'])
        body=re.sub(r'\[\[asset:([a-z0-9.\/-]+)\]\]',lambda m:'/wp-content/themes/facuso-andalucia/assets/'+m[1],body)
        images=read('imagenes-recurso.json') + (read('news-photos.json') if (ROOT/'data/news-photos.json').exists() else [])
        def static_photo(match):
            photo=next((q for q in images if q['file']==match[1]),None)
            if not photo:return ''
            return '<figure><img src="/wp-content/themes/facuso-andalucia/assets/'+html.escape(photo['file'])+'" alt="'+html.escape(photo['alt'])+'"><figcaption>'+html.escape(photo['credit'])+'</figcaption></figure>'
        body=re.sub(r'\[facuso_imagen file="([a-z0-9.\/-]+)"\]',static_photo,body)
        body=body.replace('[facuso_galeria]','')
        # El XML conserva enlaces y contenido aunque no se instale el complemento.
        body=body.replace('[facuso_secciones]','')
        body=re.sub(r'\[facuso_publicaciones[^\]]*\]',static_publications,body)
        children=[x for x in data['pages'] if x.get('parent')==p['slug'] and x['status']=='publish']
        if children:
            body+='<ul>'+''.join('<li><a href="/'+x['path']+'/">'+html.escape(x['title'])+'</a></li>' for x in children)+'</ul>'
        if p['sources']:
            body+='<h2>Fuentes</h2><ul>'+''.join('<li><a href="'+html.escape(s['url'])+'">'+html.escape(s['title'])+'</a></li>' for s in p['sources'])+'</ul>'
        # El XML conserva también las pestañas nuevas sin necesitar JavaScript.
        fragment=LH.fragment_fromstring(body,create_parent='div')
        for anchor in fragment.iter('a'):
            url=anchor.get('href','')
            if url.startswith(('https://','http://','//')):
                anchor.set('target','_blank')
                anchor.set('rel',' '.join(dict.fromkeys((anchor.get('rel','')+' noopener noreferrer').split())))
        body=(fragment.text or '')+''.join(LH.tostring(child,encoding='unicode',method='html') for child in fragment)
        pubdate=p.get('date','2026-10-18 00:00:00')
        normalized_title=''.join(c for c in unicodedata.normalize('NFKD',p['title']).casefold() if not unicodedata.combining(c))
        original_pubdate=pubdate
        # El importador oficial identifica duplicados por título/fecha/tipo en
        # vez de slug. Dos BOP distintos pueden publicar el mismo título ese día.
        # Solo en esas colisiones se usa otro segundo del mismo minuto; se
        # conserva el día y la fecha original queda también en un metadato.
        if (normalized_title,pubdate,p.get('type','page')) in used_import_dates:
            dt=datetime.fromisoformat(pubdate)
            for second in range(60):
                candidate=dt.replace(second=second).strftime('%Y-%m-%d %H:%M:%S')
                if (normalized_title,candidate,p.get('type','page')) not in used_import_dates:
                    pubdate=candidate;break
            else:raise ValueError('Demasiadas colisiones en la fecha de importación')
        used_import_dates.add((normalized_title,pubdate,p.get('type','page')))
        gmtd=datetime.fromisoformat(pubdate).replace(tzinfo=ZoneInfo('Europe/Madrid')).astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        add(item,'content:encoded',body,True);add(item,'excerpt:encoded','',True);add(item,'wp:post_id',ids[p['slug']]);add(item,'wp:post_date',pubdate);add(item,'wp:post_date_gmt',gmtd);add(item,'wp:comment_status','closed');add(item,'wp:ping_status','closed');add(item,'wp:post_name',p['slug'],True);add(item,'wp:status',p['status'],True);add(item,'wp:post_parent',ids.get(p.get('parent'),0));add(item,'wp:menu_order',0);add(item,'wp:post_type',p.get('type','page'),True);add(item,'wp:is_sticky',0);meta(item,'_facuso_key',p['slug'])
        if pubdate!=original_pubdate:meta(item,'_facuso_source_date',original_pubdate)
        if p['sources']:meta(item,'facuso_source_url',p['sources'][0]['url'])
        for cat in p.get('categories',[]):
            e=add(item,'category',next(c['title'] for c in data['categories'] if c['slug']==cat),True);e.set('domain','category');e.set('nicename',cat)
    mid=10000
    for menu,entries in data['menus'].items():
        menu_ids={}
        for entry in entries:
            mid+=1;menu_ids[entry['page']]=mid;p=next(p for p in data['pages'] if p['slug']==entry['page']);item=add(channel,'item');add(item,'title',entry.get('title',p['title']),True);add(item,'dc:creator','equipo-facuso',True);add(item,'wp:post_id',mid);add(item,'wp:post_name','menu-'+str(mid));add(item,'wp:status','publish');add(item,'wp:post_type','nav_menu_item');add(item,'wp:post_parent',0);add(item,'wp:menu_order',mid-10000)
            e=add(item,'category',menu,True);e.set('domain','nav_menu');e.set('nicename',menu)
            for k,v in {'_menu_item_type':'post_type','_menu_item_object':'page','_menu_item_object_id':ids[entry['page']],'_menu_item_menu_item_parent':menu_ids.get(entry.get('parent'),0),'_menu_item_target':'','_menu_item_classes':'a:0:{}','_menu_item_xfn':'','_menu_item_url':''}.items():meta(item,k,v)
    (DIST/'facuso-andalucia.xml').write_bytes(ET.tostring(rss,xml_declaration=True,encoding='UTF-8',pretty_print=True))

def main():
    data=build_content();DIST.mkdir(exist_ok=True)
    (PACKAGE/'content.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
    (PACKAGE/'employment-sources.json').write_text((ROOT/'data/fuentes-empleo.json').read_text())
    images=read('imagenes-recurso.json')
    if (ROOT/'data/imagenes-empleo-extra.json').exists():
        images += read('imagenes-empleo-extra.json')
    if (ROOT/'data/news-photos.json').exists():
        images += [dict(p,kind='original',description='Fotografía de la publicación original: '+p['source_url']) for p in read('news-photos.json')]
    (PACKAGE/'images.json').write_text(json.dumps(images,ensure_ascii=False,indent=2))
    source_hosts={urlparse(s['url']).hostname for p in data['pages']+data['posts'] for s in p['sources'] if s['url'].startswith('https://')}
    source_hosts.update(['boe.es','www.boe.es','uso.es','www.uso.es','facusoandalucia.es','www.facusoandalucia.es','www.usoandalucia.es','usoandalucia.es','bop.dipgra.es','bop.dipujaen.es','bopsevilla.dipusevilla.es','app.dipalme.org','www.bopcadiz.es','bopcadiz.es','bop.dipucordoba.es','bop.diphuelva.es','s2.diphuelva.es','www.bopmalaga.es','bopmalaga.es'])
    (PACKAGE/'allowed-source-hosts.json').write_text(json.dumps(sorted(source_hosts),ensure_ascii=False,indent=2))
    for folder in [PACKAGE/'languages',PACKAGE/'theme/languages']:
        folder.mkdir(exist_ok=True);(folder/'es.json').write_text((ROOT/'data/interfaz-es.json').read_text())
    (DIST/'contenido-fuentes.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
    wxr(data)
    for output,folder,prefix in [('facuso-arranque.zip',PACKAGE,'facuso-arranque'),('facuso-andalucia-tema.zip',PACKAGE/'theme','facuso-andalucia')]:
        with zipfile.ZipFile(DIST/output,'w',zipfile.ZIP_DEFLATED) as z:
            for p in sorted(folder.rglob('*')):
                if p.is_file() and 'vendor' not in p.parts:
                    entry=zipfile.ZipInfo(str(Path(prefix)/p.relative_to(folder)),date_time=(2026,10,18,0,0,0))
                    entry.compress_type=zipfile.ZIP_DEFLATED
                    entry.external_attr=0o100644 << 16
                    z.writestr(entry,p.read_bytes())
    print(json.dumps({k:len(data[k]) for k in ['pages','posts','categories','pending']},ensure_ascii=False))

if __name__=='__main__':main()
