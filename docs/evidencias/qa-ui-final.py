#!/usr/bin/env python3
"""Verifica imágenes y secciones de portada en el WordPress local."""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup
import requests

ROOT = Path(__file__).resolve().parents[2]
BASE = 'http://127.0.0.1:18086'
session = requests.Session()
errors: list[str] = []
checked_images: set[str] = set()


def soup_for(url: str) -> BeautifulSoup:
    response = session.get(url, timeout=15)
    if response.status_code != 200:
        errors.append(f'HTTP {response.status_code}: {url}')
    return BeautifulSoup(response.text, 'lxml')


def image_ok(src: str) -> None:
    if src in checked_images:
        return
    checked_images.add(src)
    response = session.get(src, timeout=15)
    if response.status_code != 200 or not response.headers.get('content-type', '').startswith('image/') or not response.content:
        errors.append(f'Imagen rota: {src}')


posts: list[dict] = []
page = 1
while True:
    response = session.get(f'{BASE}/wp-json/wp/v2/posts', params={
        'per_page': 100, 'page': page, '_fields': 'id,link,categories',
    }, timeout=15)
    response.raise_for_status()
    posts.extend(response.json())
    if page >= int(response.headers.get('X-WP-TotalPages', 1)):
        break
    page += 1
if len({post['id'] for post in posts}) != len(posts):
    errors.append('Hay ID de noticias duplicados en REST')
by_link = {post['link'].rstrip('/'): post for post in posts}
employment = session.get(f'{BASE}/wp-json/wp/v2/categories?slug=empleo-publico', timeout=15).json()[0]
employment_id = employment['id']

home = soup_for(BASE + '/')
sections = home.select('main .fac-news')
if len(sections) != 2:
    errors.append(f'Portada: {len(sections)} bloques de noticias, esperados 2')
section_results = []
for index, section in enumerate(sections):
    cards = section.select('.fac-card')
    links = [card.select_one('h3 a')['href'].rstrip('/') for card in cards]
    images = [card.select_one('img') for card in cards]
    title = section.select_one('h2').get_text(' ', strip=True)
    if len(cards) != 6 or len(set(links)) != 6:
        errors.append(f'{title}: esperadas seis noticias distintas')
    if any(image is None for image in images):
        errors.append(f'{title}: tarjeta sin imagen')
    for image in images:
        if image:
            image_ok(image['src'])
    expected_filters = 1 if index == 0 else 0
    if len(section.select('.fac-filters')) != expected_filters:
        errors.append(f'{title}: filtros visibles inesperados')
    if index == 1 and section.select_one('.fac-pagination'):
        errors.append('El bloque de empleo incluye paginación')
    for link in links:
        post = by_link.get(link)
        if not post:
            errors.append(f'Tarjeta sin entrada REST: {link}')
        elif (employment_id in post['categories']) != (index == 1):
            errors.append(f'Entrada en bloque temático incorrecto: {link}')
    section_results.append({'title': title, 'cards': len(cards), 'distinct_images': len({image['src'] for image in images if image})})
if len(sections) == 2:
    first = {a['href'].rstrip('/') for a in sections[0].select('.fac-card h3 a')}
    second = {a['href'].rstrip('/') for a in sections[1].select('.fac-card h3 a')}
    if first & second:
        errors.append('Portada: noticia repetida entre bloques')
    if section_results[1]['distinct_images'] < 4:
        errors.append('Portada: fotografías de empleo demasiado repetidas')

for post in posts:
    page_soup = soup_for(post['link'])
    image = page_soup.select_one('main .fac-article-photo img')
    if not image:
        errors.append(f'Noticia sin fotografía: {post["id"]}')
        continue
    if not image.get('alt', '').strip():
        errors.append(f'Noticia sin descripción de fotografía: {post["id"]}')
    caption = page_soup.select_one('main .fac-article-photo figcaption')
    if not caption or not caption.get_text(' ', strip=True):
        errors.append(f'Noticia sin etiqueta de fotografía: {post["id"]}')
    image_ok(image['src'])

gallery = soup_for(BASE + '/fotos/')
figures = gallery.select('.fac-photo-gallery figure')
if len(figures) != 25:
    errors.append(f'Galería: {len(figures)} fotografías, esperadas 25')
for figure in figures:
    image = figure.select_one('img')
    caption = figure.select_one('figcaption')
    link = figure.select_one('a[href]')
    if not image or not image.get('alt', '').strip() or not caption or not caption.get_text(' ', strip=True):
        errors.append('Galería: fotografía sin descripción o crédito visible')
        continue
    if not link or urlparse(link['href']).scheme != 'https':
        errors.append('Galería: fotografía sin enlace a fuente HTTPS')
    image_ok(image['src'])
montage = gallery.select_one('main .fac-section-photo')
montage_label = montage.select_one('figcaption').get_text(' ', strip=True) if montage and montage.select_one('figcaption') else ''
if 'IA' not in montage_label or 'No representa' not in montage_label:
    errors.append('Montaje de galería sin aviso visible de imagen generada')

result = {
    'published_news_checked': len(posts), 'post_ids_unique': len({post['id'] for post in posts}) == len(posts),
    'home_sections': section_results, 'gallery_photos': len(figures),
    'image_urls_checked': len(checked_images), 'montage_labeled': bool(montage_label), 'errors': errors,
}
path = ROOT / 'docs/evidencias/qa-ui-final.json'
path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(result, ensure_ascii=False))
raise SystemExit(1 if errors else 0)
