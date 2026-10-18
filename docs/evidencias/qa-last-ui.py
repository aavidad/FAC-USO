#!/usr/bin/env python3
"""Último ensayo acotado: búsqueda, archivo, favicon y anuncios BOE enriquecidos."""
import json
import hashlib
from pathlib import Path

from bs4 import BeautifulSoup
import requests

BASE = 'http://127.0.0.1:18086'
OUT = Path(__file__).with_suffix('.json')
ROOT = Path(__file__).resolve().parents[2]
errors = []
report = {}
session = requests.Session()

home = BeautifulSoup(session.get(BASE + '/', timeout=15).text, 'lxml')
home_sections = home.select('main .fac-news')
home_sequences = []
for _ in range(4):
    current = BeautifulSoup(session.get(BASE + '/', timeout=15).text, 'lxml')
    home_sequences.append([[link['href'] for link in section.select('.fac-card h3 a')]
                           for section in current.select('main .fac-news')])
report['home_order_stable'] = all(sequence == home_sequences[0] for sequence in home_sequences)
if not report['home_order_stable']:
    errors.append('El orden de las noticias en portada varía entre peticiones')
employment_photos = [image['src'] for image in home_sections[1].select('.fac-card-photo img')] if len(home_sections) == 2 else []
report['home_employment'] = {'cards': len(employment_photos), 'distinct_photos': len(set(employment_photos))}
if len(employment_photos) != 6 or len(set(employment_photos)) < 2:
    errors.append('La portada no conserva seis anuncios de empleo con fotografías variadas')
general_photos = [image['src'] for image in home_sections[0].select('.fac-card-photo img')] if len(home_sections) == 2 else []
report['home_general'] = {'cards': len(general_photos), 'distinct_photos': len(set(general_photos))}
if len(general_photos) != 6 or len(set(general_photos)) < 2:
    errors.append('La actualidad sindical no conserva seis anuncios con fotografías variadas')
same_photo = 0
for section in home_sections:
    for card in section.select('.fac-card'):
        link = card.select_one('h3 a')
        image = card.select_one('.fac-card-photo img')
        if not link or not image:
            errors.append('Tarjeta de portada sin enlace o fotografía')
            continue
        article = BeautifulSoup(session.get(link['href'], timeout=15).text, 'lxml')
        article_image = article.select_one('main .fac-article-photo img')
        if article_image and image['src'] == article_image['src']:
            same_photo += 1
        else:
            errors.append('La fotografía de una tarjeta cambia en su ficha')
report['home_list_detail_same_photo'] = same_photo
manifest = json.loads((ROOT / 'package/facuso-arranque/images.json').read_text())
generated = [row['file'] for row in manifest if row['kind'] == 'generated']
digests = [hashlib.sha256((ROOT / 'package/facuso-arranque/theme/assets' / name).read_bytes()).hexdigest()
           for name in generated]
report['generated_resources'] = {'files': len(generated), 'distinct_files': len(set(generated)),
                                 'distinct_images': len(set(digests))}
if len(generated) != 8 or len(set(generated)) != 8 or len(set(digests)) != 8:
    errors.append('Los ocho recursos ilustrativos no son distintos')

for name, path in [('search', '/?s=oposiciones'), ('granada_archive', '/category/territorios/granada/')]:
    response = session.get(BASE + path, timeout=15)
    soup = BeautifulSoup(response.text, 'lxml')
    cards = soup.select('main .fac-card')
    images = [card.select_one('.fac-card-photo img') for card in cards]
    report[name] = {'status': response.status_code, 'cards': len(cards), 'cards_with_photo': sum(image is not None for image in images)}
    if response.status_code != 200 or not cards or any(image is None for image in images):
        errors.append(f'{name}: tarjetas sin foto o página rota')
    for image in images:
        if image and session.get(image['src'], timeout=15).status_code != 200:
            errors.append(f'{name}: fotografía rota')

favicon = session.get(BASE + '/wp-content/themes/facuso-andalucia/assets/favicon.png', timeout=15)
report['favicon'] = {'status': favicon.status_code, 'type': favicon.headers.get('content-type'), 'bytes': len(favicon.content)}
if favicon.status_code != 200 or not favicon.headers.get('content-type', '').startswith('image/png'):
    errors.append('Favicon oficial no disponible')

boe_slugs = [
    'facuso-granada-786951a81428af8f1d57db00',
    'facuso-almeria-a49468b3fffa21bf3a307271',
]
report['boe_examples'] = []
for slug in boe_slugs:
    response = session.get(f'{BASE}/{slug}/', timeout=15)
    soup = BeautifulSoup(response.text, 'lxml')
    main = soup.select_one('main .fac-content')
    text = main.get_text(' ', strip=True) if main else ''
    words = len(text.split())
    source = soup.select_one('main .fac-sources a[href*="boe.es"]')
    report['boe_examples'].append({'slug': slug, 'status': response.status_code, 'words': words,
                                   'official_text': 'Texto del anuncio oficial (BOE)' in text, 'source_link': bool(source)})
    if response.status_code != 200 or words < 120 or 'Texto del anuncio oficial (BOE)' not in text or not source:
        errors.append(f'Anuncio BOE sin contenido enriquecido o fuente: {slug}')

categories = {row['slug']: row['id'] for row in session.get(
    BASE + '/wp-json/wp/v2/categories?per_page=100&_fields=id,slug', timeout=15).json()}
cadiz = session.get(BASE + '/wp-json/wp/v2/posts', params={
    'search': 'Universidad de Cádiz', 'per_page': 100, '_fields': 'id,slug,categories',
}, timeout=15).json()
matched = [row for row in cadiz if all(categories[slug] in row['categories'] for slug in
                                       ('cadiz', 'administracion-autonomica', 'universidades'))]
report['cadiz_university'] = {'found': len(cadiz), 'categorized': len(matched)}
if not cadiz or len(matched) != len(cadiz):
    errors.append('Universidad de Cádiz sin categorías autonómica y universidades')

report['errors'] = errors
OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(report, ensure_ascii=False))
raise SystemExit(1 if errors else 0)
