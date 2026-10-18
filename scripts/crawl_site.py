#!/usr/bin/env python3
"""Recorre el WordPress local entero y verifica enlaces, medios y filtros."""
from __future__ import annotations

import argparse
from collections import Counter, deque
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse
from xmlrpc.client import Fault, dumps, loads

from bs4 import BeautifulSoup
import requests

ROOT = Path(__file__).resolve().parents[1]
PROVINCES = ('almeria', 'cadiz', 'cordoba', 'granada', 'huelva', 'jaen', 'malaga', 'sevilla')
ERROR_TEXT = re.compile(r'Fatal error:|Uncaught (?:Error|Exception)|Warning:|Notice:|\[\[page:|\[facuso_(?:publicaciones|secciones)', re.I)
PHONE = re.compile(r'Tel[eé]fono:\s*([\d .]+)', re.I)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', default='http://127.0.0.1:18086')
    parser.add_argument('--out', default=str(ROOT / 'docs/evidencias/qa-crawl.json'))
    parser.add_argument('--max-pages', type=int, default=1000)
    parser.add_argument('--security', action='store_true', help='Prueba HTTP local; preparar antes el usuario QA con verify_wp.php --security-fixture')
    parser.add_argument('--security-bot', action='store_true', help='Prueba límites de la cuenta provincial de Granada con su contraseña de aplicación local')
    args = parser.parse_args()
    base = args.base.rstrip('/')
    host = urlparse(base).netloc
    session = requests.Session()
    session.headers['User-Agent'] = 'FAC-USO-QA-local/1.0'
    errors: list[str] = []
    warnings: list[str] = []
    seen: set[str] = set()
    resource_seen: set[str] = set()
    queue: deque[str] = deque([base + '/'])
    status_counts: Counter[int] = Counter()
    pages = posts = 0
    rest_posts: list[dict] = []
    expected = json.loads((ROOT / 'package/facuso-arranque/content.json').read_text())

    def normal(url: str) -> str:
        parsed = urlparse(url)
        pairs = sorted(parse_qsl(parsed.query, keep_blank_values=True))
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path or '/', '', urlencode(pairs), ''))

    def get(url: str) -> requests.Response | None:
        try:
            response = session.get(url, timeout=20, allow_redirects=True)
            status_counts[response.status_code] += 1
            return response
        except requests.RequestException as exc:
            errors.append(f'Error de conexión {url}: {type(exc).__name__}')
            return None

    for typ in ('pages', 'posts'):
        batch = 1
        found: list[dict] = []
        while True:
            response = get(f'{base}/wp-json/wp/v2/{typ}?per_page=100&page={batch}&_fields=id,slug,link,status,categories')
            if not response or response.status_code != 200:
                errors.append(f'API pública de {typ}: HTTP {response.status_code if response else "sin respuesta"}')
                break
            items = response.json()
            found.extend(items)
            if batch >= int(response.headers.get('X-WP-TotalPages', 1)):
                break
            batch += 1
        if typ == 'pages':
            pages = len(found)
        else:
            posts = len(found)
            rest_posts = found
        expected_slugs = {item['slug'] for item in expected[typ] if item['status'] == 'publish'}
        found_slugs = {item['slug'] for item in found}
        for slug in sorted(expected_slugs - found_slugs):
            errors.append(f'Falta {typ} publicado en REST: {slug}')
        for item in found:
            queue.append(normal(item['link']))

    def resource(url: str) -> None:
        url = normal(url)
        if url in resource_seen:
            return
        resource_seen.add(url)
        response = get(url)
        if not response or response.status_code != 200:
            errors.append(f'Recurso roto {url}: HTTP {response.status_code if response else "sin respuesta"}')
        elif not response.content:
            errors.append(f'Recurso vacío: {url}')

    while queue and len(seen) < args.max_pages:
        url = normal(queue.popleft())
        if url in seen:
            continue
        seen.add(url)
        response = get(url)
        if not response or response.status_code != 200:
            errors.append(f'Página rota {url}: HTTP {response.status_code if response else "sin respuesta"}')
            continue
        if 'text/html' not in response.headers.get('content-type', ''):
            warnings.append(f'Respuesta no HTML: {url}')
            continue
        soup = BeautifulSoup(response.text, 'lxml')
        if not soup.title or not soup.title.get_text(strip=True):
            errors.append(f'Sin título: {url}')
        if not soup.select_one('main'):
            errors.append(f'Sin contenido principal: {url}')
        if ERROR_TEXT.search(soup.get_text(' ', strip=True)):
            errors.append(f'Error PHP o marcador sin resolver: {url}')
        h1 = soup.select('main h1')
        if len(h1) != 1:
            errors.append(f'Se esperaba un H1, hallados {len(h1)}: {url}')
        for link in soup.select('a[href]'):
            raw = link['href'].strip()
            if not raw or raw.startswith('#') or raw.startswith(('mailto:', 'tel:')):
                continue
            parsed = urlparse(urljoin(url, raw))
            if parsed.scheme not in ('http', 'https'):
                errors.append(f'Esquema de enlace inadmisible: {url}: {raw[:80]}')
                continue
            if parsed.netloc == host:
                path = parsed.path
                if path.startswith(('/wp-admin', '/wp-login.php', '/wp-json/', '/feed')):
                    continue
                target = normal(parsed.geturl())
                if target not in seen:
                    queue.append(target)
            elif parsed.scheme != 'https':
                warnings.append(f'Enlace externo sin HTTPS: {url}: {raw[:120]}')
        for tag, attribute in (('img', 'src'), ('script', 'src'), ('link[rel="stylesheet"]', 'href')):
            for element in soup.select(f'{tag}[{attribute}]'):
                raw = element.get(attribute, '')
                target = urljoin(url, raw)
                if urlparse(target).netloc == host:
                    resource(target)
        for image in soup.select('img'):
            # alt="" declara una imagen decorativa; solo la ausencia del atributo es un fallo.
            if not image.has_attr('alt') and image.get('role') != 'presentation':
                errors.append(f'Imagen sin atributo alt: {url}: {image.get("src", "")[:120]}')

    if queue:
        errors.append(f'Límite de recorrido alcanzado ({args.max_pages}); quedan {len(queue)} URL')

    # Compara los filtros con la taxonomía real, incluidos anuncios futuros del bot.
    category_response = get(f'{base}/wp-json/wp/v2/categories?per_page=100&_fields=id,slug,parent')
    categories = category_response.json() if category_response and category_response.status_code == 200 else []
    if not categories:
        errors.append('No se pudo consultar la taxonomía pública')
    by_id = {term['id']: term for term in categories}

    def has_category(item: dict, wanted: str) -> bool:
        for term_id in item.get('categories', []):
            while term_id in by_id:
                term = by_id[term_id]
                if term['slug'] == wanted:
                    return True
                term_id = term['parent']
        return False

    filter_cases = [
        {'sector': 'sanidad', 'territorio': 'cadiz'},
        {'materia': 'empleo-publico', 'territorio': 'granada'},
        {'sector': 'administracion-local', 'materia': 'empleo-publico'},
    ]
    for case in filter_cases:
        query = urlencode({f'fac_{key}': value for key, value in case.items()})
        url = f'{base}/noticias/?{query}'
        response = get(url)
        if not response or response.status_code != 200:
            errors.append(f'Filtro roto {query}: HTTP {response.status_code if response else "sin respuesta"}')
            continue
        soup = BeautifulSoup(response.text, 'lxml')
        count = soup.select_one('.fac-news .fac-count')
        match = re.search(r'\d+', count.get_text(' ', strip=True)) if count else None
        expected_count = sum(all(has_category(post, slug) for slug in case.values()) for post in rest_posts)
        if not match or int(match.group()) != expected_count:
            errors.append(f'Filtro AND {query}: {match.group() if match else "sin cifra"} resultados, esperados {expected_count}')
        selected = {element.parent.get('name'): element.get('value') for element in soup.select('.fac-filters option[selected]')}
        for dimension, slug in case.items():
            if selected.get(f'fac_{dimension}') != slug:
                errors.append(f'Filtro no conserva selección {dimension}={slug}')
        shown = [element.get('href') for element in soup.select('.fac-news .fac-card h3 a')]
        if len(shown) != min(9, expected_count):
            errors.append(f'Filtro {query}: {len(shown)} tarjetas, esperadas {min(9, expected_count)}')

    for slug in PROVINCES:
        url = f'{base}/territorios/{slug}/'
        response = get(url)
        if not response or response.status_code != 200:
            errors.append(f'Provincia rota: {slug}')
            continue
        soup = BeautifulSoup(response.text, 'lxml')
        main = soup.select_one('main')
        if not main:
            continue
        if not main.select_one('a[href^="mailto:"]'):
            errors.append(f'Sin correo provincial: {slug}')
        phone = PHONE.search(main.get_text(' ', strip=True))
        if not phone or len(re.sub(r'\D', '', phone.group(1))) < 9:
            errors.append(f'Sin teléfono provincial: {slug}')
        if not soup.select_one('.fac-context img'):
            errors.append(f'Sin escudo provincial: {slug}')
        if not main.select_one('.fac-news .fac-card'):
            errors.append(f'Sin noticias provinciales: {slug}')

    response = get(f'{base}/noticias/?fac_pagina=999999')
    if not response or response.status_code != 200:
        errors.append('La paginación extrema falla')
    elif ERROR_TEXT.search(response.text):
        errors.append('La paginación extrema expone un error')

    security_results: dict[str, int | str] = {}
    if args.security:
        def login(username: str, password: str) -> requests.Session:
            client = requests.Session()
            client.get(f'{base}/wp-login.php', timeout=10).raise_for_status()
            result = client.post(f'{base}/wp-login.php', data={
                'log': username, 'pwd': password, 'wp-submit': 'Log In',
                'redirect_to': f'{base}/wp-admin/', 'testcookie': '1',
            }, timeout=15)
            result.raise_for_status()
            if not any('wordpress_logged_in' in cookie.name for cookie in client.cookies):
                errors.append(f'No se pudo abrir sesión local de {username}')
            return client

        before_pages = pages
        before_posts = posts
        anonymous = requests.Session()
        attempt = anonymous.post(f'{base}/wp-admin/admin-post.php',
                                 data={'action': 'facuso_import', 'design': '1'}, timeout=15)
        security_results['anonymous_import'] = attempt.status_code
        if attempt.status_code < 400:
            errors.append(f'Importación anónima no denegada: HTTP {attempt.status_code}')
        attempt = anonymous.post(f'{base}/wp-json/wp/v2/posts', json={'title': 'QA no autorizado'}, timeout=15)
        security_results['anonymous_rest_post'] = attempt.status_code
        if attempt.status_code not in (401, 403):
            errors.append(f'Escritura REST anónima no denegada: HTTP {attempt.status_code}')

        admin_password = (ROOT / 'docker/.secrets/admin_password').read_text().strip()
        admin = login('facuso-admin', admin_password)
        attempt = admin.post(f'{base}/wp-admin/admin-post.php',
                             data={'action': 'facuso_import', 'design': '1'}, timeout=15)
        security_results['admin_without_nonce'] = attempt.status_code
        if attempt.status_code != 403:
            errors.append(f'Importación sin nonce no denegada: HTTP {attempt.status_code}')

        subscriber = login('facuso-qa-subscriber', 'facuso-local-qa-dummy-only-2026')
        attempt = subscriber.post(f'{base}/wp-admin/admin-post.php',
                                  data={'action': 'facuso_import', 'design': '1'}, timeout=15)
        security_results['subscriber_import'] = attempt.status_code
        if attempt.status_code != 403:
            errors.append(f'Importación por suscriptor no denegada: HTTP {attempt.status_code}')
        attempt = subscriber.post(f'{base}/wp-json/wp/v2/posts', json={'title': 'QA no autorizado'}, timeout=15)
        security_results['subscriber_rest_post'] = attempt.status_code
        if attempt.status_code not in (401, 403):
            errors.append(f'Escritura REST por suscriptor no denegada: HTTP {attempt.status_code}')

        for typ, old in (('pages', before_pages), ('posts', before_posts)):
            result = anonymous.get(f'{base}/wp-json/wp/v2/{typ}?per_page=1', timeout=15)
            now = int(result.headers.get('X-WP-Total', -1))
            if now != old:
                errors.append(f'Las pruebas de permisos alteraron el número de {typ}: {old} -> {now}')

    if args.security_bot:
        from requests.auth import HTTPBasicAuth

        def xmlrpc_qa_count() -> int:
            result = subprocess.run([
                'docker', 'compose', '-f', 'docker/compose.yaml', 'exec', '-T', '--user', 'www-data',
                'wordpress', 'php', '/pruebas/verify_wp.php', '--xmlrpc-qa-count',
            ], cwd=ROOT, capture_output=True, text=True, timeout=20)
            match = re.fullmatch(r'XMLRPC_QA_POSTS (\d+)\s*', result.stdout)
            if result.returncode != 0 or not match:
                errors.append('No se pudo contar el contenido de prueba XML-RPC en WordPress local')
                return -1
            return int(match.group(1))

        password = (ROOT / 'docker/.secrets/bots/granada').read_text().strip()
        bot_auth = HTTPBasicAuth('facuso-bot-granada', password)
        before_xmlrpc = xmlrpc_qa_count()
        identity = requests.get(f'{base}/wp-json/wp/v2/users/me?_fields=id', auth=bot_auth, timeout=15)
        security_results['bot_identity'] = identity.status_code
        if identity.status_code != 200:
            errors.append(f'La cuenta bot local no se autentica: HTTP {identity.status_code}')
        term_ids = {term['slug']: term['id'] for term in categories}
        needed = ('granada', 'cadiz', 'empleo-publico')
        if not all(slug in term_ids for slug in needed):
            errors.append('Faltan categorías para las pruebas del bot')
        else:
            def bot_post(label: str, source: str, category_ids: list[int]) -> None:
                attempt = requests.post(f'{base}/wp-json/wp/v2/posts', auth=bot_auth, json={
                    'title': 'QA provincial denegada', 'status': 'draft', 'categories': category_ids,
                    'meta': {'facuso_source_url': source},
                }, timeout=15)
                security_results[label] = attempt.status_code
                if attempt.status_code != 403:
                    errors.append(f'Bot {label} no denegado: HTTP {attempt.status_code}')

            bot_post('foreign_province', 'https://www.uso.es/feed/', [term_ids['cadiz'], term_ids['empleo-publico']])
            bot_post('malicious_source', 'https://evil.example.test/feed/', [term_ids['granada'], term_ids['empleo-publico']])
            bot_post('source_with_userinfo', 'https://evil@www.uso.es/feed/', [term_ids['granada'], term_ids['empleo-publico']])

        denial_cases = [
            ('create_user', 'post', f'{base}/wp-json/wp/v2/users',
             {'json': {'username': 'facuso-qa-denied', 'email': 'qa@example.invalid', 'password': 'Dummy-only-not-secret-123'}}),
            ('upload_media', 'post', f'{base}/wp-json/wp/v2/media',
             {'data': b'invalid image', 'headers': {'Content-Disposition': 'attachment; filename="qa.png"', 'Content-Type': 'image/png'}}),
        ]
        sample_slug = expected['posts'][0]['slug']
        other = next((post for post in rest_posts if post['slug'] == sample_slug), None)
        if other:
            denial_cases.extend([
                ('edit_other_post', 'post', f"{base}/wp-json/wp/v2/posts/{other['id']}",
                 {'json': {'title': expected['posts'][0]['title']}}),
                ('delete_other_post', 'delete', f"{base}/wp-json/wp/v2/posts/{other['id']}", {}),
            ])
        else:
            errors.append('Falta noticia institucional para probar la edición entre usuarios')
        for label, method, url, kwargs in denial_cases:
            attempt = getattr(requests, method)(url, auth=bot_auth, timeout=15, **kwargs)
            security_results[label] = attempt.status_code
            if attempt.status_code not in (401, 403):
                errors.append(f'Bot {label} no denegado: HTTP {attempt.status_code}')
            if label == 'delete_other_post' and attempt.status_code == 200 and other:
                restored = subprocess.run([
                    'docker', 'compose', '-f', 'docker/compose.yaml', 'exec', '-T', '--user', 'www-data',
                    'wordpress', 'php', '/pruebas/verify_wp.php', f"--restore-post={other['id']}",
                ], cwd=ROOT, capture_output=True, text=True, timeout=20)
                if restored.returncode != 0:
                    errors.append('No se pudo restaurar la noticia local tras una eliminación indebida')

        for label, method, parameters in (
            ('xmlrpc_get_users_blogs', 'wp.getUsersBlogs', ['facuso-bot-granada', password]),
            ('xmlrpc_new_post', 'wp.newPost', [0, 'facuso-bot-granada', password, {
                'post_type': 'post', 'post_status': 'draft', 'post_title': 'FACUSO-QA-XMLRPC-DENIED',
                'post_content': 'Comprobación local de permisos',
            }]),
        ):
            attempt = requests.post(f'{base}/xmlrpc.php',
                                    data=dumps(tuple(parameters), methodname=method, allow_none=True).encode('utf-8'),
                                    headers={'Content-Type': 'text/xml'}, timeout=15)
            try:
                loads(attempt.content)
                outcome = 'accepted'
            except Fault as fault:
                outcome = f'fault:{fault.faultCode}'
            except Exception:
                outcome = f'http:{attempt.status_code}'
            security_results[label] = outcome
            if outcome not in ('fault:403', 'http:401', 'http:403'):
                errors.append(f'Bot {label} no denegado: {outcome}')
        after_xmlrpc = xmlrpc_qa_count()
        security_results['xmlrpc_qa_posts_after'] = after_xmlrpc
        if before_xmlrpc != 0 or after_xmlrpc != 0:
            errors.append(f'XML-RPC dejó contenido de prueba: antes={before_xmlrpc}, después={after_xmlrpc}')
            cleanup = subprocess.run([
                'docker', 'compose', '-f', 'docker/compose.yaml', 'exec', '-T', '--user', 'www-data',
                'wordpress', 'php', '/pruebas/verify_wp.php', '--xmlrpc-qa-cleanup',
            ], cwd=ROOT, capture_output=True, text=True, timeout=20)
            if cleanup.returncode != 0:
                errors.append('No se pudo eliminar contenido de prueba XML-RPC del entorno local')

    report = {
        'base': base, 'package': {'pages': len(expected['pages']), 'posts': len(expected['posts']), 'categories': len(expected['categories'])},
        'rest_published': {'pages': pages, 'posts': posts}, 'html_pages_visited': len(seen),
        'assets_checked': len(resource_seen), 'http_status_counts': dict(status_counts),
        'errors': errors, 'warnings': sorted(set(warnings)), 'security_http': security_results,
    }
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(f"Recorrido: {len(seen)} URL HTML, {len(resource_seen)} recursos, {len(errors)} errores, {len(set(warnings))} avisos. Informe: {path}")
    for error in errors[:30]:
        print(f'- {error}', file=sys.stderr)
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
