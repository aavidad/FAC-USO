"""Captura solo noticias públicas de los bots; nunca exporta usuarios ni secretos."""
from pathlib import Path
import json
import requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
base='http://127.0.0.1:18086/wp-json/wp/v2'
session=requests.Session()
categories={}
page=1
while True:
    response=session.get(base+'/categories',params={'per_page':100,'page':page},timeout=20)
    response.raise_for_status()
    categories.update({c['id']:c['slug'] for c in response.json()})
    if page>=int(response.headers['X-WP-TotalPages']):break
    page+=1
posts=[];page=1
while True:
    response=session.get(base+'/posts',params={'per_page':100,'page':page,'_fields':'slug,title,content,date,categories,meta'},timeout=20)
    response.raise_for_status()
    for post in response.json():
        if not post['slug'].startswith('facuso-'):continue
        source=post.get('meta',{}).get('facuso_source_url','')
        if not source.startswith('https://'):raise ValueError('Falta fuente HTTPS de una noticia del bot')
        title=BeautifulSoup(post['title']['rendered'],'html.parser').get_text(' ',strip=True)
        posts.append({'slug':post['slug'],'title':title,'date':post['date'],'status':'publish',
            'type':'post','html':post['content']['rendered'],
            'categories':[categories[c] for c in post['categories']],
            'sources':[{'url':source,'title':'Publicación oficial de origen'}],
            'external_id':post.get('meta',{}).get('facuso_external_id',''),
            'notes':['Captura de una noticia publicada por el bot provincial en el ensayo local del 18/10/2026.']})
    if page>=int(response.headers['X-WP-TotalPages']):break
    page+=1
(ROOT/'data/bot-news-snapshot.json').write_text(json.dumps({'date':'2026-10-18','posts':posts},ensure_ascii=False,indent=2))
print(f'{len(posts)} noticias públicas de bots capturadas; no se incluyen cuentas ni credenciales.')
