"""Descarga identidad publicada y documenta las licencias de los escudos."""
import json
from pathlib import Path
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'package/facuso-arranque/theme/assets'
SESSION = requests.Session()
SESSION.headers['User-Agent'] = 'FACUSOContentPreparation/1.0 (local research; facusoandalucia.es)'

def query(**params):
    r = SESSION.get('https://commons.wikimedia.org/w/api.php', params={
        'action': 'query', 'format': 'json', **params}, timeout=30)
    r.raise_for_status()
    return r.json()

if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    assets = []
    files = {
        'almeria': 'Coat of Arms of Almería Province.svg',
        'cadiz': 'Coat of Arms of Cádiz Province.svg',
        'cordoba': 'Coat of Arms of Córdoba Province (Spain).svg',
        'granada': 'Coat of Arms of Granada Province.svg',
        'huelva': 'Coat of Arms of Huelva Province.svg',
        'jaen': 'Coat of Arms of Jaén Province.svg',
        'malaga': 'Coat of Arms of Málaga Province.svg',
        'sevilla': 'Coat of Arms of Seville Province.svg',
        'bandera-andalucia': 'Flag of Andalusia.svg',
    }
    for slug, filename in files.items():
        result = query(titles='File:' + filename, prop='imageinfo',
                       iiprop='url|extmetadata', iiurlwidth=240)
        page = next(iter(result['query']['pages'].values()))
        info = page['imageinfo'][0]
        meta = info['extmetadata']
        image_url = info.get('thumburl', info['url'])
        r = SESSION.get(image_url, timeout=40)
        r.raise_for_status()
        if not r.headers.get('Content-Type', '').startswith('image/'):
            raise ValueError('Respuesta no gráfica')
        path = OUT / (slug + '.png')
        path.write_bytes(r.content)
        assets.append({'file': path.name, 'url': info['descriptionurl'],
                       'original_url': info['url'], 'download_url': image_url,
                       'title': filename,
                       'author': BeautifulSoup(meta.get('Artist', {}).get('value', ''), 'html.parser').get_text(' ', strip=True),
                       'license': meta.get('LicenseShortName', {}).get('value', ''),
                       'license_url': meta.get('LicenseUrl', {}).get('value', ''),
                       'date': '2026-10-18', 'changes': 'Miniatura PNG generada por Wikimedia; sin otros cambios.'})
        print(slug, assets[-1]['license'], flush=True)
    originals = {
        'logo-facuso-andalucia.png': 'https://facusoandalucia.es/wp-content/uploads/2026/10/logoFACUSO-Andalucia-.png',
        'justicia.jpg': 'https://facusoandalucia.es/wp-content/uploads/2026/07/logo-actual-SPJ-USO-alta-calidad-2-768x399-1.jpg',
    }
    for filename, url in originals.items():
        r = SESSION.get(url, timeout=30); r.raise_for_status()
        (OUT / filename).write_bytes(r.content)
        assets.append({'file': filename, 'url': url, 'title': filename,
                       'author': 'FAC-USO / SPJ-USO', 'license': 'Identidad corporativa; derechos de sus titulares.',
                       'license_url': '', 'date': '2026-10-18', 'changes': 'Sin cambios.'})
    (ROOT / 'data/assets.json').write_text(json.dumps(assets, ensure_ascii=False, indent=2))
